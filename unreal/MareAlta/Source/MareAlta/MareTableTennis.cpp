#include "MareTableTennis.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "MareGamepad.h"
#include "MareOptions.h"
#include "Camera/CameraActor.h"
#include "Components/ChildActorComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "InputCoreTypes.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

using namespace MareTT;
namespace
{
 constexpr double G=9.81,Drag=.14,SpinAccel=3.0,TableBounce=.88,Sub=1./600;
 UMareSimulation* Sim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 double Sgn(int32 Side){return Side==0?-1.:1.;}
 bool OnTable(const FVector& P){return FMath::Abs(P.X)<=L/2 && FMath::Abs(P.Y)<=W/2;}
}

static TAutoConsoleVariable<int32> CVarTTAutoPlay(TEXT("mare.TTAutoPlay"),0,TEXT("QA: the table tennis AI also plays the player's side."));
// QA: "mare.TTQA" starts a match for player 0 against Seu Bené (with mare.TTAutoPlay 1 it plays itself).
static FAutoConsoleCommandWithWorld TTQACommand(TEXT("mare.TTQA"),TEXT("Starts a table tennis match for player 0 (QA)."),
 FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World){if(auto TT=World?World->GetSubsystem<UMareTableTennis>():nullptr)TT->StartMatch(World->GetFirstPlayerController(),TEXT("Seu Bené"));}));

TStatId UMareTableTennis::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareTableTennis,STATGROUP_Tickables);}

void UMareTableTennis::Deinitialize()
{
 if(bPlaying)EndMatch(FString());
 for(AActor* A:TArray<AActor*>{TableActor,BallActor,PlayerBat,GuestBat,Camera,Target,Guest})if(IsValid(A))A->Destroy();
 Super::Deinitialize();
}

// ---------------------------------------------------------------- simulation
bool UMareTableTennis::Fly(FVector& P,FVector& V,double& S,double Dt) const
{
 // Gravity plus the Magnus push of the spin (topspin dives), and air drag growing with the square of the speed.
 V.Z-=(G+SpinAccel*S)*Dt;V-=V*V.Size()*Drag*Dt;P+=V*Dt;
 if(P.Z<=R && P.Z-V.Z*Dt>R && OnTable(P)){P.Z=R;V.Z=-V.Z*TableBounce;V.X*=.9+.08*S;V.Y*=.92;S*=.5;return true;}
 return false;
}

void UMareTableTennis::NewMatch(int32 First)
{
 Points[0]=Points[1]=Games[0]=Games[1]=0;FirstServer=Server=First;MatchWinner=-1;Rallies=0;Call.Reset();ReadyServe();
}

void UMareTableTennis::ReadyServe()
{
 bInPlay=bServing=bNetTouch=false;LastHitter=-1;ServeBounces=BouncesSinceHit=0;BounceSide=-1;Spin=0;Vel=FVector::ZeroVector;
 Ball=FVector(Sgn(Server)*(L/2+.12),FMath::Clamp(PaddleY[Server],-W/2+.1,W/2-.1),.22);
}

void UMareTableTennis::Serve(int32 Side,double TargetY,uint32 Seed)
{
 if(bInPlay || MatchWinner>=0 || Side!=Server)return;
 FRandomStream Rng(Seed);const double S=Sgn(Side);
 TargetY=FMath::Clamp(TargetY+Rng.FRandRange(-1.,1.)*Skill[Side]*.6,-W/2+.08,W/2-.08);
 // A real serve is fast and low: search speed and downward angle so the ball bounces on the server's half, clears
 // the net and lands on the receiver's half nearest the target (tools/ue58 replica: about 6 m/s, -1.2 to -1.6 m/s).
 const double Want=-S*(L/2-.5);double BestErr=1e9;FVector Best(-S*5,0,-1.2);
 const FVector2D Dir=FVector2D(-S,(TargetY-Ball.Y)*.5).GetSafeNormal();
 for(double H=3.;H<=7.01;H+=.2)for(double Vz=-4.;Vz<=1.01;Vz+=.2){
  FVector P=Ball,V(Dir.X*H,Dir.Y*H,Vz);double Sp=.1;int32 Bounces=0;bool bOk=true;double LandX=0,LandY=0;
  for(double Tt=0;Tt<2.;Tt+=Sub*2){const FVector Prev=P;
   if(Fly(P,V,Sp,Sub*2)){++Bounces;const bool bOwn=(P.X<0)==(S<0);if((Bounces==1)!=bOwn){bOk=false;break;}if(Bounces==2){LandX=P.X;LandY=P.Y;break;}}
   if((Prev.X<0)!=(P.X<0) && P.Z<NetH+R+.01){bOk=false;break;}if(P.Z<-Top){bOk=false;break;}}
  if(!bOk || Bounces<2)continue;
  const double Err=FMath::Abs(LandX-Want)+FMath::Abs(LandY-TargetY);
  if(Err<BestErr){BestErr=Err;Best=FVector(Dir.X*H,Dir.Y*H,Vz);}}
 Vel=Best;Spin=.1;bInPlay=bServing=true;ServeBounces=0;BouncesSinceHit=0;LastHitter=Side;bNetTouch=false;Call.Reset();++Rallies;
}

void UMareTableTennis::Hit(int32 Side,double TargetX,double TargetY,double HSpeed,double Topspin)
{
 // For a horizontal speed, bisect the upward speed so the real model (drag, spin) lands on the target; if that arc
 // would not clear the net, slow down (a higher arc) and solve again.
 const FVector2D D=FVector2D(TargetX,TargetY)-FVector2D(Ball.X,Ball.Y);const double Dist=D.Size();const FVector2D U=D/FMath::Max(Dist,1e-6);
 double H=HSpeed,Vz=0;
 for(int32 Try=0;Try<10;++Try){double Lo=-4,Hi=8;bool bClear=true;
  for(int32 It=0;It<22;++It){Vz=(Lo+Hi)/2;FVector P=Ball,V(U.X*H,U.Y*H,Vz);double S=Topspin;double Landed=-1;bClear=true;
   for(double Tt=0;Tt<3;Tt+=Sub*2){const FVector Prev=P;V.Z-=(G+SpinAccel*S)*Sub*2;V-=V*V.Size()*Drag*Sub*2;P+=V*Sub*2;
    if((Prev.X<0)!=(P.X<0) && P.Z<NetH+R+.03)bClear=false;
    if(P.Z<=R && V.Z<0){Landed=FVector2D::Distance(FVector2D(P.X,P.Y),FVector2D(Ball.X,Ball.Y));break;}}
   if(Landed<0 || Landed>Dist)Hi=Vz;else Lo=Vz;}
  Vz=(Lo+Hi)/2;if(bClear)break;H*=.9;}
 Vel=FVector(U.X*H,U.Y*H,Vz);Spin=Topspin;LastHitter=Side;BouncesSinceHit=0;BounceSide=-1;bServing=false;bNetTouch=false;++Rallies;
}

int32 UMareTableTennis::HitWindow() const
{
 if(!bInPlay || bServing || LastHitter<0 || BouncesSinceHit!=1 || BounceSide==LastHitter)return -1;
 const int32 Side=1-LastHitter;const double Edge=Sgn(Side)*(L/2+Plane);
 const bool bComing=Sgn(Side)*Vel.X>0;const bool bAt=Side==0?Ball.X<=Edge && Ball.X>=Edge-.6:Ball.X>=Edge && Ball.X<=Edge+.6;
 return bComing && bAt && Ball.Z>-.05 && Ball.Z<1.1?Side:-1;
}

double UMareTableTennis::PredictY(int32 Side) const
{
 FVector P=Ball,V=Vel;double S=Spin;const double Edge=Sgn(Side)*(L/2+Plane);
 for(double T=0;T<2.5;T+=Sub*4){Fly(P,V,S,Sub*4);if(Side==0?P.X<=Edge:P.X>=Edge)return P.Y;if(P.Z<-Top)break;}
 return P.Y;
}

bool UMareTableTennis::Step(double Seconds)
{
 if(!bInPlay)return false;
 const int32 Window=HitWindow();
 for(double T=0;T<Seconds;T+=Sub){
  const FVector Prev=Ball;const bool bBounce=Fly(Ball,Vel,Spin,Sub);
  // Net: the band stops a low ball (it drops back), a ball skimming the cord slows and rolls over.
  if((Prev.X<0)!=(Ball.X<0) && FMath::Abs(Ball.Y)<W/2+.1525 && Ball.Z<NetH+R){bNetTouch=true;
   if(Ball.Z<NetH-R*.5){Ball.X=Prev.X;Vel.X*=-.12;Vel.Z*=.25;Vel.Y*=.4;}else{Vel*=.6;Vel.Z=FMath::Abs(Vel.Z)*.4;}}
  if(bBounce){const int32 Side=Ball.X<0?0:1;BounceSide=Side;
   if(bServing){++ServeBounces;
    if(ServeBounces==1 && Side!=Server){AwardPoint(1-Server,TEXT("Saque sem quicar no próprio lado."));return false;}
    if(ServeBounces==2){if(Side==Server){AwardPoint(1-Server,TEXT("O saque não passou para o outro lado."));return false;}
     if(bNetTouch){Call=TEXT("Let: o saque raspou a rede. Repete o ponto.");ReadyServe();return false;}
     bServing=false;BouncesSinceHit=1;LastHitter=Server;}}
   else{if(Side==LastHitter){AwardPoint(1-LastHitter,TEXT("A bola quicou do próprio lado."));return false;}
    if(++BouncesSinceHit>=2){AwardPoint(LastHitter,TEXT("Dois quiques: não devolveu."));return false;}}}
  if(Ball.Z<-Top+R || FMath::Abs(Ball.X)>L/2+4 || FMath::Abs(Ball.Y)>4){
   if(bServing)AwardPoint(1-Server,TEXT("Saque fora."));
   else if(BouncesSinceHit==0)AwardPoint(1-LastHitter,TEXT("Bola fora da mesa."));
   else AwardPoint(LastHitter,TEXT("Não alcançou a bola."));
   return false;}
  // Stop as the ball reaches a paddle plane so the side can return it this frame.
  if(Window<0 && HitWindow()>=0)return true;
 }
 return bInPlay;
}

bool UMareTableTennis::AIReturn(int32 Side,uint32 Seed)
{
 if(HitWindow()!=Side || FMath::Abs(PaddleY[Side]-Ball.Y)>Reach)return false;
 FRandomStream Rng(Seed);const double S=-Sgn(Side);
 double TX=S*(L/2-Rng.FRandRange(.25,.85))+Rng.FRandRange(-1.,1.)*Skill[Side]*1.6;
 double TY=Rng.FRandRange(-W/2+.15,W/2-.15)+Rng.FRandRange(-1.,1.)*Skill[Side];double HS=Rng.FRandRange(5.5,7.5);
 // Unforced errors, more for weaker players and against fast balls: long, wide or into the net.
 const double Incoming=FVector2D(Vel.X,Vel.Y).Size();
 // About 5-6 shots a point, like a casual game.
 if(Rng.FRand()<FMath::Clamp(.1+Skill[Side]+(Incoming-6)*.02,.08,.4)){const int32 Kind=Rng.RandRange(0,2);
  if(Kind==0)TX=S*(L/2+Rng.FRandRange(.05,.4));else if(Kind==1)TY=FMath::Sign(TY+.001)*(W/2+Rng.FRandRange(.05,.3));
  else{Hit(Side,TX,TY,HS,.6);Vel.Z-=Rng.FRandRange(1.2,2.);return true;}}   // too flat: into the net
 Hit(Side,TX,TY,HS,Rng.FRandRange(.2,.6));return true;
}

void UMareTableTennis::AwardPoint(int32 Side,const FString& Why)
{
 bInPlay=false;++Points[Side];Call=Why;
 if(Points[Side]>=11 && Points[Side]-Points[1-Side]>=2){++Games[Side];
  Call+=FString::Printf(TEXT(" Game para %s (%d × %d)."),Side==0?TEXT("você"):*Opponent,Points[0],Points[1]);
  if(Games[Side]>=2){MatchWinner=Side;return;}
  Points[0]=Points[1]=0;FirstServer=1-FirstServer;}
 const int32 Total=Points[0]+Points[1];
 Server=Total<20?(FirstServer+Total/2)%2:(FirstServer+Total)%2;
 ReadyServe();
}

// ---------------------------------------------------------------- world
FVector UMareTableTennis::World(const FVector& P) const{return Table.TransformPosition(FVector(P.X*100,P.Y*100,(Top+P.Z)*100));}

void UMareTableTennis::SpawnProps()
{
 FString Text;TSharedPtr<FJsonObject> Data;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/game_room.json")));
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Data) || !Data.IsValid())return;
 const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!Data->TryGetArrayField(TEXT("tt_table"),At) || At->Num()!=4)return;
 Table=FTransform(FRotator(0,(*At)[3]->AsNumber(),0),FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber()));
 auto Spawn=[this](const TCHAR* Path,const FTransform& T){auto Mesh=LoadObject<UStaticMesh>(nullptr,Path);if(!Mesh)return (AStaticMeshActor*)nullptr;
  auto A=GetWorld()->SpawnActor<AStaticMeshActor>(T.GetLocation(),T.Rotator());A->SetMobility(EComponentMobility::Movable);A->GetStaticMeshComponent()->SetStaticMesh(Mesh);
  A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);return A;};
 TableActor=Spawn(TEXT("/Game/Custom/GameRoom/tt_table/tt_table.tt_table"),Table);
 if(TableActor)TableActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
 BallActor=Spawn(TEXT("/Game/Custom/GameRoom/tt_ball/tt_ball.tt_ball"),Table);
 PlayerBat=Spawn(TEXT("/Game/Custom/GameRoom/tt_bat_red/tt_bat_red.tt_bat_red"),Table);
 GuestBat=Spawn(TEXT("/Game/Custom/GameRoom/tt_bat_black/tt_bat_black.tt_bat_black"),Table);
 // At rest: both bats lie on the table beside the net and the ball sits next to them.
 if(PlayerBat)PlayerBat->SetActorLocationAndRotation(World(FVector(-.35,.45,.004)),Table.Rotator()+FRotator(0,20,-90));
 if(GuestBat)GuestBat->SetActorLocationAndRotation(World(FVector(.35,-.45,.004)),Table.Rotator()+FRotator(0,200,-90));
 if(BallActor)BallActor->SetActorLocation(World(FVector(-.2,.3,0)));
 Target=GetWorld()->SpawnActor<AMareServiceTarget>(World(FVector(-L/2-.25,0,.05)),FRotator::ZeroRotator);
 Target->Action=TEXT("TableTennis");Target->Label=TEXT("Mesa de tênis de mesa · jogar contra um hóspede");Target->Reach=260;Target->OcclusionTolerance=80;
}

void UMareTableTennis::StartMatch(APlayerController* Controller,const FString& InOpponent,double InStake)
{
 if(bPlaying || !Controller || !TableActor)return;
 Player=Controller;Stake=InStake;Opponent=InOpponent.IsEmpty()?FString(TEXT("Hóspede")):InOpponent;bPlaying=true;Delay=1.5f;AimDrift=0;
 int32 Look=1;Skill[0]=.05;Speed[0]=3.;
 if(auto S=Sim(GetWorld())){const auto Row=S->PoolPlayer(Opponent);
  // The pool roster's aim error (degrees) maps to the table: a craque misses by centimetres, a beginner by a hand.
  const double E=UMareSimulation::Number(Row,TEXT("skill"),2);Skill[1]=FMath::Clamp(.04+.05*E,.05,.22);Speed[1]=FMath::Clamp(3.2-.45*E,1.6,3.);
  Look=int32(UMareSimulation::Number(Row,TEXT("appearance"),1));}
 PaddleY[0]=PaddleY[1]=0;NewMatch(FMath::RandBool()?0:1);
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
 Guest=GetWorld()->SpawnActor<AMarePerson>(World(FVector(L/2+.75,0,-Top))+FVector(0,0,90),Table.Rotator()+FRotator(0,180,0),Params);
 if(Guest){Guest->SaveId=TEXT("tt_guest");Guest->PersonName=Opponent;Guest->SetAppearance(Look);Guest->bAmbient=true;Guest->Tags.Add(TEXT("MareHotelGuest"));Guest->GetCharacterMovement()->DisableMovement();}
 // High behind the player's end, looking down the table: the bat sits low in the frame and never hides the far half.
 Camera=GetWorld()->SpawnActor<ACameraActor>(World(FVector(-L/2-1.9,0,1.1)),(World(FVector(L/6,0,-.15))-World(FVector(-L/2-1.9,0,1.1))).Rotation());
 Controller->SetViewTargetWithBlend(Camera,.5f);Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 // Only the table, the balls and the cue/bats on screen (Sergio, 03/11): no arms or hands of the player at all.
 if(auto Pawn=Controller->GetPawn()){Pawn->SetActorHiddenInGame(true);TArray<UPrimitiveComponent*> Parts;Pawn->GetComponents(Parts);HiddenParts.Reset();
  for(auto C:Parts)if(C->IsVisible()){HiddenParts.Add(C);C->SetVisibility(false);}}
 if(auto S=Sim(GetWorld()))S->LastMessage=FString::Printf(TEXT("Tênis de mesa contra %s: melhor de 3 games de 11. Mouse move a raquete, segure o clique para cortar, Q sai."),*Opponent);
}

void UMareTableTennis::EndMatch(const FString& Message)
{
 if(!bPlaying)return;bPlaying=false;
 UE_LOG(LogTemp,Display,TEXT("MARE_TT match end winner=%d games=%d-%d points=%d-%d rallies=%d"),MatchWinner,Games[0],Games[1],Points[0],Points[1],Rallies);
 if(auto PC=Player.Get()){PC->SetViewTargetWithBlend(PC->GetPawn(),.5f);PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();if(auto Pawn=PC->GetPawn()){Pawn->SetActorHiddenInGame(false);for(auto& C:HiddenParts)if(C.IsValid())C->SetVisibility(true);HiddenParts.Reset();}}
 for(auto& A:HiddenNearby)if(auto P=Cast<AMarePerson>(A.Get())){P->SetActorHiddenInGame(false);if(P->MetaHumanBody && P->MetaHumanBody->GetChildActor())P->MetaHumanBody->GetChildActor()->SetActorHiddenInGame(false);}
 HiddenNearby.Reset();
 if(IsValid(Guest))Guest->Destroy();Guest=nullptr;if(IsValid(Camera))Camera->Destroy();Camera=nullptr;
 if(auto S=Sim(GetWorld())){const int32 Result=MatchWinner>=0?MatchWinner:Stake>0?1:-1;
  if(Result>=0 && Stake>0)S->SettleBet(Result==0?Stake:-Stake,Result==0?TEXT("Tênis de mesa: aposta ganha"):TEXT("Tênis de mesa: aposta perdida"));
  if(Result==0)S->AddFame(2);
  if(Result>=0)S->RecordGame(TEXT("table_tennis"),Result==0);
  if(!Message.IsEmpty())S->LastMessage=Message;}
 bInPlay=false;
 if(PlayerBat)PlayerBat->SetActorLocationAndRotation(World(FVector(-.35,.45,.004)),Table.Rotator()+FRotator(0,20,-90));
 if(GuestBat)GuestBat->SetActorLocationAndRotation(World(FVector(.35,-.45,.004)),Table.Rotator()+FRotator(0,200,-90));
 if(BallActor)BallActor->SetActorLocation(World(FVector(-.2,.3,0)));
}

FString UMareTableTennis::Status() const
{
 if(!bPlaying)return FString();
 const bool bPad=MareGamepad::UsingGamepad();
 FString Doing;
 if(MatchWinner>=0)Doing=TEXT("fim de jogo");
 else if(!bInPlay)Doing=Server==0?(bPad?TEXT("seu saque: analógico posiciona, gatilho saca"):TEXT("seu saque: mova o mouse e clique")):*(TEXT("saque de ")+Opponent);
 else Doing=bPad?TEXT("analógico move a raquete · segure o gatilho para cortar"):TEXT("mouse move a raquete · segure o clique para cortar");
 FString Line=FString::Printf(TEXT("Tênis de mesa · você %d × %d %s · games %d × %d · %s · Q sai"),Points[0],Points[1],*Opponent,Games[0],Games[1],*Doing);
 if(!Call.IsEmpty())Line+=TEXT("\n")+Call;
 return Line;
}

void UMareTableTennis::UpdateProps(float DeltaSeconds)
{
 if(!bPlaying)return;
 if(BallActor)BallActor->SetActorLocation(World(Ball)-FVector(0,0,R*100));
 // The player's bat on its plane, following the ball's height while a rally comes in; tilted forward for topspin.
 const double PZ=FMath::Clamp(bInPlay?Ball.Z:.15,.02,.6);
 // Held a little low and to the right of the ball, as a forehand: the ball and the far half stay in view.
 if(PlayerBat)PlayerBat->SetActorLocationAndRotation(World(FVector(-L/2-Plane-.05,PaddleY[0]+.12,PZ-.27)),Table.Rotator()+FRotator(0,90,bSmash?-25:-10));
 // Hotel guests walking by: whoever stands close to the match camera steps out of the picture until the match ends.
 if(Camera){const FVector Cam=Camera->GetActorLocation();
  for(TActorIterator<AMarePerson> It(GetWorld());It;++It){AMarePerson* P=*It;if(P==Guest)continue;
   if(FVector::Dist2D(P->GetActorLocation(),Cam)<260 && !HiddenNearby.Contains(P)){HiddenNearby.Add(P);P->SetActorHiddenInGame(true);
    if(P->MetaHumanBody && P->MetaHumanBody->GetChildActor())P->MetaHumanBody->GetChildActor()->SetActorHiddenInGame(true);}}}
 const double GZ=FMath::Clamp(bInPlay?Ball.Z:.15,.02,.6);
 if(GuestBat)GuestBat->SetActorLocationAndRotation(World(FVector(L/2+Plane+.05,PaddleY[1],GZ-.17)),Table.Rotator()+FRotator(0,-90,-10));
 // The opponent stands behind his bat with the bat at his right hand (his right is -y facing the player).
 if(IsValid(Guest)){const FVector Want=World(FVector(L/2+.75,PaddleY[1]+.32,-Top))+FVector(0,0,90);
  Guest->SetActorLocation(FMath::VInterpTo(Guest->GetActorLocation(),Want,DeltaSeconds,8.f));}
}

void UMareTableTennis::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 auto S=Sim(GetWorld());if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("salao_jogos"),bOwned);
 if(bOwned && !TableActor)SpawnProps();
 for(AActor* A:TArray<AActor*>{TableActor,BallActor,PlayerBat,GuestBat,Target})if(IsValid(A))A->SetActorHiddenInGame(!bOwned);
 if(!bOwned || !bPlaying)return;
 auto PC=Player.Get();if(!PC){EndMatch(FString());return;}
 if(PC->WasInputKeyJustPressed(EKeys::Q) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right)){EndMatch(TEXT("Partida de tênis de mesa encerrada."));return;}
 const bool bAuto=CVarTTAutoPlay.GetValueOnGameThread()!=0;
 const FVector At=World(Ball);
 // Player paddle: the mouse (or a stick) slides it; its lateral speed is the aim of the next return.
 float DX=0,DY=0;PC->GetInputMouseDelta(DX,DY);
 DX+=(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX)+PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX))*DeltaSeconds*90;
 bSmash=PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis)>.3f;
 if(!bAuto){PaddleY[0]=FMath::Clamp(PaddleY[0]+DX*.0045,-W/2-.5,W/2+.5);AimDrift=FMath::FInterpTo(AimDrift,DX*.02f,DeltaSeconds,6.f);}
 // AI paddles (the guest, and the player under mare.TTAutoPlay) slide toward where the ball will cross their plane.
 for(int32 Side=bAuto?0:1;Side<2;++Side){
  const bool bComing=bInPlay && Sgn(Side)*Vel.X>0 && (bServing || LastHitter!=Side);
  const double Want=bComing?PredictY(Side):Side==Server && !bInPlay?PaddleY[Side]:0;
  PaddleY[Side]+=FMath::Clamp(Want-PaddleY[Side],-Speed[Side]*DeltaSeconds,Speed[Side]*DeltaSeconds);}
 if(MatchWinner>=0){
  if((Delay-=DeltaSeconds)<=0)EndMatch(MatchWinner==0?FString::Printf(TEXT("Você venceu %s no tênis de mesa por %d × %d em games!"),*Opponent,Games[0],Games[1])
   :FString::Printf(TEXT("%s venceu no tênis de mesa por %d × %d em games."),*Opponent,Games[1],Games[0]));
  UpdateProps(DeltaSeconds);return;}
 if(!bInPlay){
  if(Server==0 && !bAuto){Ball.Y=FMath::Clamp(PaddleY[0],-W/2+.1,W/2-.1);
   if(PC->WasInputKeyJustReleased(EKeys::LeftMouseButton) || PC->WasInputKeyJustReleased(EKeys::Gamepad_RightTrigger) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Bottom)){
    Serve(0,FMath::Clamp(-Ball.Y*.5+AimDrift*4,-W/2+.1,W/2-.1),GFrameNumber);UMareAudioWorld::Action(this,TEXT("tt_paddle"),&At,.7f);}}
  else if((Delay-=DeltaSeconds)<=0){Serve(Server,FMath::FRandRange(-W/2+.2,W/2-.2),GFrameNumber*31);UMareAudioWorld::Action(this,TEXT("tt_paddle"),&At,.7f);Delay=1.4f;}}
 else{const int32 Before=BouncesSinceHit+ServeBounces;
  const bool bLive=Step(DeltaSeconds);
  if(BouncesSinceHit+ServeBounces>Before && bInPlay)UMareAudioWorld::Action(this,TEXT("tt_bounce"),&At,.6f);
  if(!bLive){Delay=1.4f;UMareAudioWorld::Action(this,TEXT("tt_bounce"),&At,.35f);}
  const int32 Window=HitWindow();
  if(Window==1 || (Window==0 && bAuto)){if(AIReturn(Window,GFrameNumber*7+Rallies))UMareAudioWorld::Action(this,TEXT("tt_paddle"),&At,.8f);}
  else if(Window==0 && FMath::Abs(PaddleY[0]-Ball.Y)<=Reach){
   // The player's return: where the ball meets the bat and how the mouse moved aim it; holding the click smashes.
   const double Offset=(Ball.Y-PaddleY[0])/Reach;
   const double TY=FMath::Clamp(Offset*.45+AimDrift*3.,-W/2+.06,W/2-.06)+FMath::FRandRange(-1.,1.)*(bSmash?.12:.05);
   const double TX=L/2-(bSmash?.35:.6)+FMath::FRandRange(-1.,1.)*(bSmash?.25:.08);
   Hit(0,TX,TY,bSmash?9.5:6.8,bSmash?.8:.4);UMareAudioWorld::Action(this,TEXT("tt_paddle"),&At,bSmash?1.f:.8f);}}
 UpdateProps(DeltaSeconds);
}
