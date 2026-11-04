#include "MareGameRoom.h"
#include "MareLoc.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "MareGamepad.h"
#include "MareOptions.h"
#include "Camera/CameraActor.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/ChildActorComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

using namespace MarePool;
namespace
{
 constexpr double Restitution=.95,CushionBounce=.78,RollingDecel=.22,LinearDrag=.18,StopSpeed=.008;
 const FVector2D Pockets[6]={{-MarePool::L/2,-MarePool::W/2},{0,-MarePool::W/2-.01},{MarePool::L/2,-MarePool::W/2},
  {-MarePool::L/2,MarePool::W/2},{0,MarePool::W/2+.01},{MarePool::L/2,MarePool::W/2}};
 UMareSimulation* Sim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
}

static TAutoConsoleVariable<int32> CVarPoolAutoPlay(TEXT("mare.PoolAutoPlay"),0,TEXT("QA: the shot AI also plays the player's turns at the pool table."));
// QA: "mare.PoolQA" starts a friendly match for the first player at the pool table (with mare.PoolAutoPlay 1 it plays itself).
static FAutoConsoleCommandWithWorld PoolQACommand(TEXT("mare.PoolQA"),TEXT("Starts a pool match for player 0 (QA)."),
 FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World){if(auto Room=World?World->GetSubsystem<UMareGameRoom>():nullptr)Room->StartMatch(World->GetFirstPlayerController(),0,TEXT("Seu Bené"));}));

TStatId UMareGameRoom::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareGameRoom,STATGROUP_Tickables);}

void UMareGameRoom::Deinitialize()
{
 if(bPlaying)EndMatch(FString());
 for(auto A:BallActors)if(IsValid(A))A->Destroy();
 for(AActor* A:TArray<AActor*>{TableActor,Cue,Camera,Target,Guest})if(IsValid(A))A->Destroy();
 Super::Deinitialize();
}

// ---------------------------------------------------------------- simulation
void UMareGameRoom::Rack()
{
 for(auto& B:Balls)B=FBall();
 // Triangle on the foot spot with the 8 in the middle; cue ball on the head spot.
 static const int32 Order[15]={1,9,2,10,8,3,11,4,12,5,13,6,14,7,15};
 int32 K=0;const double Gap=2*R+.0005;
 for(int32 Row=0;Row<5;++Row)for(int32 I=0;I<=Row;++I)Balls[Order[K++]].P=FVector2D(L/4+Row*Gap*.866,(I-Row/2.)*Gap);
 Balls[0].P=FVector2D(-L/4,0);
 Score[0]=Score[1]=0;Turn=0;Winner=-1;PottedThisShot.Reset();bScratch=false;
 Group[0]=Group[1]=0;FirstHit=-1;bBreakShot=true;bBallInHand=false;LastCall.Reset();
}

int32 UMareGameRoom::Remaining(int32 InGroup) const{int32 N=0;for(int32 I=1;I<16;++I)if(!Balls[I].bIn && GroupOf(I)==InGroup)++N;return N;}

bool UMareGameRoom::IsTarget(int32 Side,int32 Ball) const
{
 if(Ball<=0 || Ball>15 || Balls[Ball].bIn)return false;
 if(Group[Side]==0)return Ball!=8;
 return Remaining(Group[Side])==0?Ball==8:GroupOf(Ball)==Group[Side];
}

bool UMareGameRoom::PlaceCueBall(const FVector2D& P)
{
 if(FMath::Abs(P.X)>L/2-R-.005 || FMath::Abs(P.Y)>W/2-R-.005)return false;
 for(int32 I=1;I<16;++I)if(!Balls[I].bIn && FVector2D::Distance(Balls[I].P,P)<2*R+.003)return false;
 for(const auto& Pk:Pockets)if(FVector2D::Distance(Pk,P)<PocketR*1.6)return false;
 Balls[0]=FBall();Balls[0].P=P;return true;
}

void UMareGameRoom::PlaceCueBallForAI()
{
 double BestValue=-2;FVector2D Best=FVector2D(-L/4,0);const FBall Saved=Balls[0];
 for(int32 X=0;X<11;++X)for(int32 Y=0;Y<5;++Y){const FVector2D P(-L/2+L*(X+.5)/11,-W/2+W*(Y+.5)/5);
  if(!PlaceCueBall(P))continue;double A=0,S=0;const double V=BestPot(A,S);if(V>BestValue){BestValue=V;Best=P;}}
 Balls[0]=Saved;if(!PlaceCueBall(Best))PlaceCueBall(FVector2D(-L/4,0));
}

void UMareGameRoom::SpotEight()
{
 // On the foot spot, or the nearest free point behind it along the long axis.
 FVector2D P(L/4,0);for(int32 Try=0;Try<30;++Try){bool bFree=true;
  for(int32 I=0;I<16;++I)if(I!=8 && !Balls[I].bIn && FVector2D::Distance(Balls[I].P,P)<2*R+.002)bFree=false;
  if(bFree)break;P.X+=2.1*R;}
 Balls[8]=FBall();Balls[8].P=P;
}

void UMareGameRoom::Shoot(double Angle,double Speed)
{
 if(Balls[0].bIn)return;
 Balls[0].V=FVector2D(FMath::Cos(Angle),FMath::Sin(Angle))*FMath::Clamp(Speed,.2,6.);PottedThisShot.Reset();bScratch=false;FirstHit=-1;bBallInHand=false;
}

bool UMareGameRoom::Moving() const{for(const auto& B:Balls)if(!B.bIn && !B.V.IsNearlyZero(StopSpeed))return true;return false;}

bool UMareGameRoom::Step(double Seconds)
{
 const double Dt=1./240;ClackSpeed=RailSpeed=0;Drops=0;
 for(double T=0;T<Seconds;T+=Dt){
  for(int32 I=0;I<16;++I){auto& B=Balls[I];if(B.bIn)continue;
   const double Speed=B.V.Size();if(Speed<StopSpeed){B.V=FVector2D::ZeroVector;continue;}
   // Rolling resistance plus a little drag on the cloth.
   const double NewSpeed=FMath::Max(0.,Speed-(RollingDecel+LinearDrag*Speed)*Dt);B.V*=NewSpeed/Speed;B.P+=B.V*Dt;
   // Pockets: the ball centre inside the mouth drops.
   for(const auto& Pk:Pockets)if(FVector2D::Distance(B.P,Pk)<PocketR*.95){B.bIn=true;B.V=FVector2D::ZeroVector;PottedThisShot.Add(I);++Drops;if(I==0)bScratch=true;break;}
   if(B.bIn)continue;
   // Cushions, open near the six pockets.
   const bool bNearCorner=FMath::Abs(B.P.X)>L/2-PocketR*1.6 && FMath::Abs(B.P.Y)>W/2-PocketR*1.6;
   const bool bNearMiddle=FMath::Abs(B.P.X)<PocketR*1.25;
   if(!bNearCorner && FMath::Abs(B.P.X)>L/2-R){B.P.X=FMath::Sign(B.P.X)*(L/2-R);RailSpeed=FMath::Max(RailSpeed,FMath::Abs(B.V.X));B.V.X*=-CushionBounce;}
   if(!bNearCorner && !bNearMiddle && FMath::Abs(B.P.Y)>W/2-R){B.P.Y=FMath::Sign(B.P.Y)*(W/2-R);RailSpeed=FMath::Max(RailSpeed,FMath::Abs(B.V.Y));B.V.Y*=-CushionBounce;}
   // Never leave the table even through a pocket gap.
   B.P.X=FMath::Clamp(B.P.X,-L/2-.03,L/2+.03);B.P.Y=FMath::Clamp(B.P.Y,-W/2-.03,W/2+.03);
  }
  // Ball-ball: equal masses, exchange the normal components (with a little loss).
  for(int32 I=0;I<16;++I)for(int32 J=I+1;J<16;++J){auto& A=Balls[I];auto& B=Balls[J];if(A.bIn || B.bIn)continue;
   FVector2D D=B.P-A.P;const double Dist=D.Size();if(Dist>=2*R || Dist<1e-9)continue;
   const FVector2D N=D/Dist;const double Overlap=2*R-Dist;A.P-=N*Overlap/2;B.P+=N*Overlap/2;
   const double Rel=FVector2D::DotProduct(A.V-B.V,N);if(Rel<=0)continue;
   const double Impulse=Rel*(1+Restitution)/2;ClackSpeed=FMath::Max(ClackSpeed,Rel);A.V-=N*Impulse;B.V+=N*Impulse;
   if(FirstHit<0 && I==0)FirstHit=J;}
  if(!Moving())return false;
 }
 return Moving();
}

void UMareGameRoom::ResolveShot()
{
 const int32 Me=Turn,Opp=1-Turn;
 bool bFoul=bScratch || Balls[0].bIn;const TCHAR* Why=bFoul?TEXT("branca na caçapa"):nullptr;
 // Own group cleared before this shot (balls potted now still count as on the table for the 8 rule).
 auto LeftBefore=[&](int32 Side){if(Group[Side]==0)return 99;int32 N=Remaining(Group[Side]);for(int32 I:PottedThisShot)if(GroupOf(I)==Group[Side])++N;return N;};
 const bool bClearedBefore=Group[Me]!=0 && LeftBefore(Me)==0;
 if(FirstHit<0){bFoul=true;Why=TEXT("a branca não tocou em nenhuma bola");}
 else if(!bBreakShot){
  const bool bRightFirst=Group[Me]==0?FirstHit!=8:bClearedBefore?FirstHit==8:GroupOf(FirstHit)==Group[Me];
  if(!bRightFirst && !bFoul){bFoul=true;Why=TEXT("tocou primeiro na bola errada");}}
 TArray<int32> Potted;bool bEight=false;
 for(int32 I:PottedThisShot){if(I==8)bEight=true;else if(I!=0)Potted.Add(I);}
 LastCall.Reset();
 if(bEight){
  if(bBreakShot && !bFoul){SpotEight();bEight=false;LastCall=TEXT("A 8 caiu na saída e voltou para a mesa.");}
  else{Winner=!bFoul && bClearedBefore?Me:Opp;
   LastCall=Winner==Me?TEXT("Encaçapou a 8 no fim: vitória!"):bFoul?TEXT("A 8 caiu junto com uma falta: derrota."):TEXT("A 8 caiu antes da hora: derrota.");}}
 // The first legal pot after the break gives the groups.
 if(Winner<0 && !bFoul && !bBreakShot && Group[Me]==0 && Potted.Num()){Group[Me]=GroupOf(Potted[0]);Group[Opp]=3-Group[Me];
  LastCall=Group[Me]==1?TEXT("Lisas para quem encaçapou."):TEXT("Listradas para quem encaçapou.");}
 for(int32 Side=0;Side<2;++Side)Score[Side]=Group[Side]==0?0:7-Remaining(Group[Side]);
 if(Winner<0){
  const bool bOwnPot=Potted.ContainsByPredicate([&](int32 I){return Group[Me]==0 || GroupOf(I)==Group[Me];});
  if(bFoul){Turn=Opp;bBallInHand=true;if(!PlaceCueBall(FVector2D(-L/4,0)))PlaceCueBallForAI();
   LastCall=FString(TEXT("Falta: "))+Why+TEXT(". Bola na mão para ")+(Opp==0?TEXT("você."):TEXT("o adversário."));}
  else if(!bOwnPot)Turn=Opp;}
 bBreakShot=false;PottedThisShot.Reset();bScratch=false;FirstHit=-1;
}

bool UMareGameRoom::PathClear(const FVector2D& A,const FVector2D& B,int32 IgnoreA,int32 IgnoreB) const
{
 const FVector2D D=B-A;const double Len=D.Size();if(Len<1e-6)return true;const FVector2D U=D/Len;
 for(int32 I=0;I<16;++I){if(I==IgnoreA || I==IgnoreB || Balls[I].bIn)continue;
  const double T=FMath::Clamp(FVector2D::DotProduct(Balls[I].P-A,U),0.,Len);
  if(FVector2D::Distance(A+U*T,Balls[I].P)<2*R)return false;}
 return true;
}

double UMareGameRoom::BestPot(double& Angle,double& Speed) const
{
 const FVector2D CueP=Balls[0].P;double Best=-1;Angle=0;Speed=2;
 for(int32 I=1;I<16;++I){if(!IsTarget(Turn,I))continue;
  for(const auto& Pk:Pockets){
   const FVector2D ToPocket=(Pk-Balls[I].P).GetSafeNormal();const FVector2D Ghost=Balls[I].P-ToPocket*2*R;
   const FVector2D ToGhost=(Ghost-CueP);const double Cut=FVector2D::DotProduct(ToGhost.GetSafeNormal(),ToPocket);
   if(Cut<.25 || !PathClear(CueP,Ghost,0,I) || !PathClear(Balls[I].P,Pk,I,-1))continue;
   const double D1=ToGhost.Size(),D2=FVector2D::Distance(Balls[I].P,Pk);
   const double Value=Cut/(.3+D1+D2);
   if(Value>Best){Best=Value;Angle=FMath::Atan2(ToGhost.Y,ToGhost.X);Speed=FMath::Clamp(1.1+1.6*(D1+D2),1.4,4.5);}}}
 return Best;
}

void UMareGameRoom::PlanGuestShot(double& Angle,double& Speed,uint32 Seed) const
{
 FRandomStream Rng(Seed);const FVector2D CueP=Balls[0].P;
 if(bBreakShot){// Break: hard, straight into the head ball of the rack.
  Angle=FMath::Atan2(Balls[1].P.Y-CueP.Y,Balls[1].P.X-CueP.X)+FMath::DegreesToRadians(Rng.FRandRange(-1.,1.));Speed=5.5;return;}
 if(BestPot(Angle,Speed)<0){// No clean pot: a legal touch on the nearest reachable target ball (safety).
  double Near=1e9;for(int32 I=1;I<16;++I)if(IsTarget(Turn,I)){const double D=FVector2D::Distance(CueP,Balls[I].P);
   if(D<Near && PathClear(CueP,Balls[I].P,0,I)){Near=D;Angle=FMath::Atan2(Balls[I].P.Y-CueP.Y,Balls[I].P.X-CueP.X);}}
  if(Near>1e8)for(int32 I=1;I<16;++I)if(IsTarget(Turn,I)){const double D=FVector2D::Distance(CueP,Balls[I].P);if(D<Near){Near=D;Angle=FMath::Atan2(Balls[I].P.Y-CueP.Y,Balls[I].P.X-CueP.X);}}
  Speed=1.6;}
 // Opponent skill: a few tenths of a degree for a champion, a few degrees for a beginner.
 const double Err=AimError[Turn];Angle+=FMath::DegreesToRadians(Rng.GetFraction()*2*Err-Err);Speed*=Rng.FRandRange(.92,1.08);
}

// ---------------------------------------------------------------- world
FVector UMareGameRoom::World(const FVector2D& P,double Lift) const{return Table.TransformPosition(FVector(P.X*100,P.Y*100,(ClothZ+R+Lift)*100));}

void UMareGameRoom::SpawnProps()
{
 // Table placement lives in data (Content/Data/game_room.json: table [x, y, z, yaw]) so it moves without a build.
 FString Text;TSharedPtr<FJsonObject> Data;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/game_room.json")));
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Data) || !Data.IsValid())return;
 const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!Data->TryGetArrayField(TEXT("table"),At) || At->Num()!=4)return;
 Table=FTransform(FRotator(0,(*At)[3]->AsNumber(),0),FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber()));
 auto Spawn=[this](const TCHAR* Path,const FTransform& T){auto Mesh=LoadObject<UStaticMesh>(nullptr,Path);if(!Mesh)return (AStaticMeshActor*)nullptr;
  auto A=GetWorld()->SpawnActor<AStaticMeshActor>(T.GetLocation(),T.Rotator());A->SetMobility(EComponentMobility::Movable);A->GetStaticMeshComponent()->SetStaticMesh(Mesh);
  A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);return A;};
 TableActor=Spawn(TEXT("/Game/Custom/GameRoom/pool_table/pool_table.pool_table"),Table);
 if(TableActor)TableActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
 Rack();
 for(int32 I=0;I<16;++I)BallActors.Add(Spawn(*FString::Printf(TEXT("/Game/Custom/GameRoom/pool_ball_%02d/pool_ball_%02d.pool_ball_%02d"),I,I,I),FTransform(World(Balls[I].P,-R))));
 Cue=Spawn(TEXT("/Game/Custom/GameRoom/pool_cue/pool_cue.pool_cue"),Table);if(Cue)Cue->SetActorHiddenInGame(true);
 Target=GetWorld()->SpawnActor<AMareServiceTarget>(Table.TransformPosition(FVector(-L*50-25,0,ClothZ*100+10)),FRotator::ZeroRotator);
 Target->Action=TEXT("PoolTable");Target->Label=TEXT("Mesa de sinuca · jogar contra um hóspede");Target->Reach=260;Target->OcclusionTolerance=80;
}

void UMareGameRoom::StartMatch(APlayerController* Controller,double InStake,const FString& InOpponent,bool bInCup)
{
 if(bPlaying || !Controller)return;Player=Controller;Stake=InStake;bCup=bInCup;
 Opponent=InOpponent.IsEmpty()?FString(TEXT("Hóspede")):InOpponent;int32 Look=1;AimError[0]=AimError[1]=1.4;
 if(auto S=Sim(GetWorld())){const auto Row=S->PoolPlayer(Opponent);AimError[1]=UMareSimulation::Number(Row,TEXT("skill"),1.4);Look=int32(UMareSimulation::Number(Row,TEXT("appearance"),1));}Rack();bPlaying=true;Shots=0;bShotRunning=false;bPlacing=false;Charge=0;AimAngle=0;
 // The guest opponent stands at the foot of the table.
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
 Guest=GetWorld()->SpawnActor<AMarePerson>(Table.TransformPosition(FVector(L*50+70,40,90)),Table.Rotator()+FRotator(0,180,0),Params);
 if(Guest){Guest->SaveId=TEXT("pool_guest");Guest->PersonName=Opponent;Guest->SetAppearance(Look);Guest->bAmbient=true;Guest->Tags.Add(TEXT("MareHotelGuest"));Guest->GetCharacterMovement()->DisableMovement();}
 Camera=GetWorld()->SpawnActor<ACameraActor>(World(FVector2D(-L/2-.6,0),.9),FRotator(-45,Table.Rotator().Yaw,0));
 Controller->SetViewTargetWithBlend(Camera,.5f);Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 // The player stands at the table: hide the body so it never sits between the match camera and the cloth.
 // Only the table, the balls and the cue/bats on screen (Sergio, 03/11): no arms or hands of the player at all.
 if(auto Pawn=Controller->GetPawn()){Pawn->SetActorHiddenInGame(true);TArray<UPrimitiveComponent*> Parts;Pawn->GetComponents(Parts);HiddenParts.Reset();
  for(auto C:Parts)if(C->IsVisible()){HiddenParts.Add(C);C->SetVisibility(false);}}
 if(Cue)Cue->SetActorHiddenInGame(false);
 if(auto S=Sim(GetWorld()))S->LastMessage=Stake>0?FString::Printf(TEXT("Sinuca bola 8 valendo R$ %.0f: lisas ou listradas, a 8 por último."),Stake):TEXT("Sinuca bola 8: lisas ou listradas, a 8 por último. Mouse mira, segure o clique para a força, Q sai.");
}

void UMareGameRoom::EndMatch(const FString& Message)
{
 if(!bPlaying)return;bPlaying=false;
 UE_LOG(LogTemp,Display,TEXT("MARE_POOL match end winner=%d score=%d-%d shots=%d"),Winner,Score[0],Score[1],Shots);
 if(auto PC=Player.Get()){PC->SetViewTargetWithBlend(PC->GetPawn(),.5f);PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();if(auto Pawn=PC->GetPawn()){Pawn->SetActorHiddenInGame(false);for(auto& C:HiddenParts)if(C.IsValid())C->SetVisibility(true);HiddenParts.Reset();}}
 if(IsValid(Guest))Guest->Destroy();Guest=nullptr;if(IsValid(Camera))Camera->Destroy();Camera=nullptr;if(Cue)Cue->SetActorHiddenInGame(true);
 if(auto S=Sim(GetWorld())){
  // Quitting a bet or a cup round counts as a loss (W.O.); a friendly match left halfway is just not recorded.
  const int32 Result=Winner>=0?Winner:(Stake>0 || bCup)?1:-1;
  if(Result>=0 && Stake>0)S->SettleBet(Result==0?Stake:-Stake,Result==0?TEXT("Sinuca: aposta ganha"):TEXT("Sinuca: aposta perdida"));
  if(Result==0)S->AddFame(2);
  if(Result>=0)S->PoolRecord(Result==0);
  if(!Message.IsEmpty())S->LastMessage=Message;
  if(bCup && Result>=0){const FString Said=S->LastMessage;S->PoolCupResult(Result==0);S->LastMessage=Said+TEXT(" ")+S->LastMessage;}}
 bCup=false;
 Rack();
}

bool UMareGameRoom::AimLine(FVector& From,FVector& To) const
{
 if(!bPlaying || Turn!=0 || bShotRunning || Balls[0].bIn)return false;
 const FVector2D Dir(FMath::Cos(AimAngle),FMath::Sin(AimAngle));
 // Guide to the first ball or cushion in the aim direction, like a short laser line.
 double Len=.6;for(int32 I=1;I<16;++I)if(!Balls[I].bIn){const FVector2D D=Balls[I].P-Balls[0].P;const double T=FVector2D::DotProduct(D,Dir);
  const double Miss=FVector2D::Distance(Balls[0].P+Dir*T,Balls[I].P);
  if(T>0 && Miss<2*R)Len=FMath::Min(Len,T-FMath::Sqrt(FMath::Max(0.,4*R*R-Miss*Miss)));}
 From=World(Balls[0].P);To=World(Balls[0].P+Dir*FMath::Max(.05,Len));return true;
}

FString UMareGameRoom::Status() const
{
 if(!bPlaying)return FString();
 const bool bPad=MareGamepad::UsingGamepad();const bool bPlayStation=FMareOptions::Get().PadGlyphs==1;
 FString Yours=TEXT("sua vez: mouse mira, segure e solte o clique · Q sai");
 if(bPad)Yours=FText::Format(NSLOCTEXT("MareGameRoom","PoolPadTurn","sua vez: analógico mira, segure {0} e solte · {1} sai"),
  MareLoc::Text(MareGamepad::PadLabel(EKeys::Gamepad_RightTrigger,bPlayStation)),MareLoc::Text(MareGamepad::PadLabel(EKeys::Gamepad_FaceButton_Right,bPlayStation))).ToString();
 if(bPlacing)Yours=bPad?FText::Format(NSLOCTEXT("MareGameRoom","PoolPadPlace","bola na mão: analógico move a branca, {0} confirma"),
  MareLoc::Text(MareGamepad::PadLabel(EKeys::Gamepad_RightTrigger,bPlayStation))).ToString():TEXT("bola na mão: mova o mouse para posicionar a branca e clique");
 auto Side=[this](int32 S){return Group[S]==1?TEXT(" (lisas)"):Group[S]==2?TEXT(" (listradas)"):TEXT("");};
 FString Line=FString::Printf(TEXT("Sinuca · você%s %d × %d %s%s · %s"),Side(0),Score[0],Score[1],*Opponent,Side(1),
  bShotRunning?TEXT("bolas rolando"):Turn==0?*Yours:*(TEXT("vez de ")+Opponent));
 if(!LastCall.IsEmpty() && !bShotRunning)Line+=TEXT("\n")+LastCall;
 return Line;
}

void UMareGameRoom::UpdateProps(float DeltaSeconds)
{
 for(int32 I=0;I<16 && I<BallActors.Num();++I)if(auto A=BallActors[I]){A->SetActorHiddenInGame(Balls[I].bIn);
  // Roll: rotate about the axis perpendicular to the velocity.
  const FVector Pos=World(Balls[I].P,-R);const FVector Delta=Pos-A->GetActorLocation();A->SetActorLocation(Pos);
  if(Delta.SizeSquared()>1e-4){const FVector Axis=FVector::CrossProduct(FVector::UpVector,Delta).GetSafeNormal();
   A->AddActorWorldRotation(FQuat(Axis,Delta.Size()/(R*100)));}}
 if(Cue){const bool bShow=bPlaying && Turn==0 && !bShotRunning && !bPlacing && !Balls[0].bIn;Cue->SetActorHiddenInGame(!bShow);
  if(bShow){const FVector2D Dir(FMath::Cos(AimAngle),FMath::Sin(AimAngle));const double Back=.04+.25*Charge;
   // The cue (built along +X, tip at 1.48 m) lies behind the cue ball, slightly raised at the butt.
   const FVector Tip=World(Balls[0].P-Dir*Back,.004);const FRotator Rot=(World(Balls[0].P)-World(Balls[0].P-Dir,.12)).Rotation();
   Cue->SetActorLocationAndRotation(Tip-Rot.Vector()*148,Rot);}}
 if(Camera && bPlaying){const FVector2D Dir(FMath::Cos(AimAngle),FMath::Sin(AimAngle));
  const FVector Eye=World(Balls[0].P-Dir*.75,.55);const FVector Look=World(Balls[0].P+Dir*.6);
  Camera->SetActorLocationAndRotation(FMath::VInterpTo(Camera->GetActorLocation(),Eye,DeltaSeconds,4.f),FMath::RInterpTo(Camera->GetActorRotation(),(Look-Eye).Rotation(),DeltaSeconds,4.f));
  // The opponent stands at the foot of the table: when the shot camera comes round to that end he would fill the
  // frame, so he steps out of the picture until the camera moves away.
  if(IsValid(Guest)){const FVector Cam=Camera->GetActorLocation(),G=Guest->GetActorLocation()+FVector(0,0,40);
   const FVector View=(World(Balls[0].P)-Cam).GetSafeNormal();const double Ahead=FVector::DotProduct(G-Cam,View);
   const bool bInFrame=Ahead>0 && FVector::CrossProduct(View,G-Cam).Size()<Ahead*.75;
   const bool bHide=FVector::Dist(Cam,G)<220 || (bInFrame && Ahead<FVector::Dist(Cam,World(Balls[0].P))+60);
   // A MetaHuman body is its own child actor and is hidden with the person.
   Guest->SetActorHiddenInGame(bHide);if(Guest->MetaHumanBody && Guest->MetaHumanBody->GetChildActor())Guest->MetaHumanBody->GetChildActor()->SetActorHiddenInGame(bHide);}}
}

void UMareGameRoom::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 auto S=Sim(GetWorld());if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("salao_jogos"),bOwned);
 if(bOwned && !TableActor)SpawnProps();
 if(TableActor){TableActor->SetActorHiddenInGame(!bOwned);if(Target)Target->SetActorHiddenInGame(!bOwned);}
 if(!bOwned)return;
 if(bPlaying){
  auto PC=Player.Get();if(!PC){EndMatch(FString());return;}
  if(PC->WasInputKeyJustPressed(EKeys::Q) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right)){EndMatch(TEXT("Partida de sinuca encerrada."));return;}
  if(bShotRunning){
   const bool bStill=!Step(DeltaSeconds);
   {const FVector At=Table.GetLocation()+FVector(0,0,80);
    if(ClackSpeed>.05)UMareAudioWorld::Action(this,TEXT("pool_ball_clack"),&At,FMath::Clamp(float(ClackSpeed)/3.f,.25f,1.f));
    if(RailSpeed>.15)UMareAudioWorld::Action(this,TEXT("pool_rail_bounce"),&At,FMath::Clamp(float(RailSpeed)/3.f,.3f,1.f));
    if(Drops)UMareAudioWorld::Action(this,TEXT("pool_pocket"),&At);}
   if(bStill){bShotRunning=false;ResolveShot();
    if(Winner>=0){EndMatch(Winner==0?TEXT("Você venceu a partida de sinuca! ")+LastCall:Opponent+TEXT(" venceu a partida de sinuca. ")+LastCall);return;}
    bPlacing=Turn==0 && bBallInHand && !CVarPoolAutoPlay.GetValueOnGameThread();GuestDelay=1.2f;}}
  else if(Turn==0 && CVarPoolAutoPlay.GetValueOnGameThread()){
   // QA: the AI plays the player's turns too, so a whole match runs to the end on its own.
   if((GuestDelay-=DeltaSeconds)<=0){if(bBallInHand)PlaceCueBallForAI();double Angle=0,Speed=0;PlanGuestShot(Angle,Speed,GFrameNumber*7919);AimAngle=Angle;Shoot(Angle,Speed);bShotRunning=true;++Shots;}}
  else if(Turn==0 && bPlacing){
   // Ball in hand: the mouse (or a stick) slides the cue ball over the cloth in the camera's frame; click confirms.
   float DX=0,DY=0;PC->GetInputMouseDelta(DX,DY);
   DX+=(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX)+PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX))*DeltaSeconds*60;
   DY+=(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY)+PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY))*DeltaSeconds*60;
   const FVector2D Dir(FMath::Cos(AimAngle),FMath::Sin(AimAngle)),Side(-Dir.Y,Dir.X);
   PlaceCueBall(Balls[0].P+(Dir*DY+Side*DX)*.004);
   if(PC->WasInputKeyJustReleased(EKeys::LeftMouseButton) || PC->WasInputKeyJustReleased(EKeys::Gamepad_RightTrigger) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Bottom))bPlacing=false;}
  else if(Turn==0){
   float DX=0,DY=0;PC->GetInputMouseDelta(DX,DY);AimAngle+=DX*.004;
   // Gamepad: either stick aims (squared curve for fine shots), RT held charges like the mouse button.
   const float Stick=FMath::Clamp(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX)+PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX),-1.f,1.f);
   AimAngle+=MareGamepad::Curve(Stick,0.f)*MareGamepad::AimRadiansPerSecond*DeltaSeconds;
   if(PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_RightTrigger) || PC->GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis)>.3f){bCharging=true;Charge=FMath::Min(1.f,Charge+DeltaSeconds/1.2f);}
   else if(bCharging){bCharging=false;const FVector At=Table.GetLocation()+FVector(0,0,80);UMareAudioWorld::Action(this,TEXT("pool_cue_hit"),&At,.4f+.6f*Charge);
    Shoot(AimAngle,.5+5.5*Charge);Charge=0;bShotRunning=true;++Shots;}}
  else if((GuestDelay-=DeltaSeconds)<=0){if(bBallInHand)PlaceCueBallForAI();double Angle=0,Speed=0;PlanGuestShot(Angle,Speed,FCrc::StrCrc32(*FString::Printf(TEXT("%d-%d"),Score[0],Score[1]))+GFrameNumber);
   AimAngle=Angle;{const FVector At=Table.GetLocation()+FVector(0,0,80);UMareAudioWorld::Action(this,TEXT("pool_cue_hit"),&At,FMath::Clamp(float(Speed)/6.f,.4f,1.f));}
   Shoot(Angle,Speed);bShotRunning=true;++Shots;}
 }
 UpdateProps(DeltaSeconds);
}
