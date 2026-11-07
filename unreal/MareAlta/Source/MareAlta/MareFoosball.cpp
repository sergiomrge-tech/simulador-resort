#include "MareFoosball.h"
#include "MareSimulation.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "MareGamepad.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
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

namespace F=MareFB;
namespace
{
 constexpr double FBSub=1./600,FBWall=.7,FBFoot=.55,FBMaxSpeed=8.;
 UMareSimulation* FBSim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 double FBFwd(int32 Side){return Side==0?1.:-1.;}
 // The imported mesh names carry the importer's suffix (mare_foosball_rod_5_mar4, ...): look them up in
 // Data/custom_assets.json (written by mare_custom.py) instead of guessing the asset path.
 FString FBAsset(const FString& Slug)
 {
  static TSharedPtr<FJsonObject> Assets;
  if(!Assets.IsValid()){FString Text;Assets=MakeShared<FJsonObject>();
   if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/custom_assets.json")))){TSharedPtr<FJsonObject> Read;
    if(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Read) && Read.IsValid())Assets=Read;}}
  FString Path;if(!Assets->TryGetStringField(Slug,Path))UE_LOG(LogTemp,Warning,TEXT("MARE_FB no custom asset '%s'"),*Slug);
  return Path;
 }
 FString FBRodSlug(int32 I)
 {
  static const TCHAR* P[F::Rods]={TEXT("1_coral"),TEXT("2_coral"),TEXT("3_mar"),TEXT("5_coral"),TEXT("5_mar"),TEXT("3_coral"),TEXT("2_mar"),TEXT("1_mar")};
  return FString(TEXT("mare_foosball_rod_"))+P[I];
 }
}

double MareFB::Travel(int32 Men){return Men==1?.10:Men==2?.20:Men==3?.125:.08;}
double MareFB::Man(int32 Men,int32 K)
{
 static const double M2[2]={-.12,.12},M3[3]={-.185,0,.185},M5[5]={-.24,-.12,0,.12,.24};
 return Men==1?0.:Men==2?M2[K]:Men==3?M3[K]:M5[K];
}

static TAutoConsoleVariable<int32> CVarFBAutoPlay(TEXT("mare.FBAutoPlay"),0,TEXT("QA: the foosball AI also plays the player's rods."));
// QA: "mare.FBQA" starts a foosball match for player 0 against Seu Bené (with mare.FBAutoPlay 1 it plays itself).
static FAutoConsoleCommandWithWorld FBQACommand(TEXT("mare.FBQA"),TEXT("Starts a foosball match for player 0 (QA)."),
 FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World){if(auto FB=World?World->GetSubsystem<UMareFoosball>():nullptr)FB->StartMatch(World->GetFirstPlayerController(),TEXT("Seu Bené"));}));

TStatId UMareFoosball::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareFoosball,STATGROUP_Tickables);}

void UMareFoosball::Deinitialize()
{
 if(bPlaying)EndMatch(FString());
 for(AActor* A:TArray<AActor*>{TableActor,BallActor,Camera,Guest})if(IsValid(A))A->Destroy();
 for(auto& A:RodActors)if(IsValid(A))A->Destroy();RodActors.Empty();
 Super::Deinitialize();
}

// ---------------------------------------------------------------- simulation
int32 UMareFoosball::Hits(int32 Mine,int32 Theirs){return Mine>Theirs?(Mine-Theirs>=3?3:2):(Theirs-Mine<=2?1:0);}

void UMareFoosball::NewMatch()
{
 Goals[0]=Goals[1]=0;Winner=-1;LastTouch=-1;Serves=0;Touches=0;Restarts=0;bLive=false;Still=0;Call.Reset();Ball=FVector2D::ZeroVector;Vel=FVector2D::ZeroVector;
 for(int32 I=0;I<F::Rods;++I){RodY[I]=RodA[I]=RodW[I]=RodVY[I]=AimY[I]=0;Kick[I]=FKick();}
}

void UMareFoosball::Serve(uint32 Seed)
{
 // The referee's drop: from the side wall at midfield, rolling in across the two midfield rods.
 FRandomStream Rng(Seed);const double S=(Serves++%2)?1.:-1.;
 Ball=FVector2D(Rng.FRandRange(-.02,.02),S*(F::HY-F::R-.01));Vel=FVector2D(Rng.FRandRange(-.25,.25),-S*Rng.FRandRange(.55,.85));
 bLive=true;Still=0;Sideways=0;LastTouch=-1;
}

void UMareFoosball::TurnRod(int32 I,double Angle,double Dt){RodW[I]=FMath::UnwindRadians(Angle-RodA[I])/FMath::Max(Dt,1e-4);}
void UMareFoosball::SlideRod(int32 I,double Y,double Dt){const double T=F::Travel(F::Count[I]);RodVY[I]=(FMath::Clamp(Y,-T,T)-RodY[I])/FMath::Max(Dt,1e-4);}

int32 UMareFoosball::NearestMan(int32 I,double Y,double& Gap) const
{
 int32 Best=-1;Gap=1e9;
 for(int32 K=0;K<F::Count[I];++K){const double D=FMath::Abs(Y-(RodY[I]+F::Man(F::Count[I],K)));if(D<Gap){Gap=D;Best=K;}}
 return Best;
}

int32 UMareFoosball::PickActive(int32 Current) const
{
 // The player's rod nearest behind the ball (a rod just past the ball still counts: its feet reach 7 cm forward).
 auto Cost=[this](int32 I){const double D=Ball.X-F::RodX(I);return FMath::Abs(D)+(D< -.05?.15:0.);};
 int32 Best=Current;double BestCost=F::Team[Current]==0?Cost(Current)-.03:1e9;
 for(int32 I=0;I<F::Rods;++I)if(F::Team[I]==0 && Cost(I)<BestCost){BestCost=Cost(I);Best=I;}
 return Best;
}

void UMareFoosball::Score(int32 Side)
{
 ++Goals[Side];bLive=false;Vel=FVector2D::ZeroVector;
 if(GetWorld())UE_LOG(LogTemp,Display,TEXT("MARE_FB goal side=%d %d-%d touches=%d serves=%d restarts=%d"),Side,Goals[0]+(Side==0?0:0),Goals[1],Touches,Serves,Restarts);
 Call=FString::Printf(TEXT("Gol %s! %d × %d."),Side==0?TEXT("seu"):*(TEXT("de ")+(Opponent.IsEmpty()?FString(TEXT("Hóspede")):Opponent)),Goals[0],Goals[1]);
 if(Goals[Side]>=WinGoals)Winner=Side;
}

bool UMareFoosball::Step(double Seconds)
{
 for(double T=0;T<Seconds-1e-9;T+=FBSub){
  const double Dt=FMath::Min(FBSub,Seconds-T);
  for(int32 I=0;I<F::Rods;++I){RodA[I]=FMath::UnwindRadians(RodA[I]+RodW[I]*Dt);const double Tr=F::Travel(F::Count[I]);RodY[I]=FMath::Clamp(RodY[I]+RodVY[I]*Dt,-Tr,Tr);}
  if(!bLive)continue;
  // Rolling: the cork ball on the laminated field slows a little with speed and stops by itself.
  const double Speed=Vel.Size();
  if(Speed>0){const double S2=FMath::Max(0.,Speed-(.05+.3*Speed)*Dt);Vel*=S2/Speed;}
  // Corner ramps push the ball back out.
  const double U=F::HX-FMath::Abs(Ball.X),V=F::HY-FMath::Abs(Ball.Y);
  if(U+V<.06 && FMath::Abs(Ball.Y)>F::GoalHalf)Vel+=FVector2D(-FMath::Sign(Ball.X),-FMath::Sign(Ball.Y))*1.4*Dt;
  Ball+=Vel*Dt;
  if(FMath::Abs(Ball.Y)>F::HY-F::R){Ball.Y=FMath::Sign(Ball.Y)*(F::HY-F::R);if(Vel.Y*Ball.Y>0)Vel.Y=-Vel.Y*FBWall;}
  if(FMath::Abs(Ball.X)>F::HX-F::R){const double Sx=FMath::Sign(Ball.X);
   if(FMath::Abs(Ball.Y)<F::GoalHalf-F::R*.5){
    // Inside the goal mouth: the box walls keep it in line; past the line it is a goal.
    if(FMath::Abs(Ball.X)>F::HX+F::R){Score(Sx>0?0:1);return false;}}
   else{Ball.X=Sx*(F::HX-F::R);if(Vel.X*Sx>0)Vel.X=-Vel.X*FBWall;}}
  for(const double Sx:{-1.,1.})for(const double Sy:{-1.,1.}){const FVector2D Post(Sx*F::HX,Sy*F::GoalHalf);const FVector2D D=Ball-Post;const double L=D.Size();
   if(L<F::R && L>1e-6){const FVector2D N=D/L;Ball=Post+N*F::R;const double Vn=FVector2D::DotProduct(Vel,N);if(Vn<0)Vel-=(1+FBWall)*Vn*N;}}
  if(FMath::Abs(Ball.X)>F::HX && FMath::Abs(Ball.Y)>F::GoalHalf-F::R){Ball.Y=FMath::Sign(Ball.Y)*(F::GoalHalf-F::R);Vel.Y=-Vel.Y*FBWall;}
  // The men's foot blocks: boxes that move with the rod's slide and swing; they reach the ball while the rod is turned
  // less than ~47 degrees (higher, the feet pass over it).
  for(int32 I=0;I<F::Rods;++I){const double C=FMath::Cos(RodA[I]);if(C<F::Lift)continue;
   const double Fx=F::RodX(I)+F::FootR*FMath::Sin(RodA[I]);const FVector2D Vf(F::FootR*C*RodW[I],RodVY[I]);
   for(int32 K=0;K<F::Count[I];++K){const double Fy=RodY[I]+F::Man(F::Count[I],K);
    const FVector2D Cl(FMath::Clamp(Ball.X,Fx-F::FootHX,Fx+F::FootHX),FMath::Clamp(Ball.Y,Fy-F::FootHY,Fy+F::FootHY));FVector2D D=Ball-Cl;double L=D.Size();
    if(L>=F::R)continue;
    FVector2D N=L>1e-6?D/L:FVector2D(Ball.X>=Fx?1.:-1.,0);
    Ball=Cl+N*F::R;const FVector2D Vr=Vel-Vf;const double Vn=FVector2D::DotProduct(Vr,N);
    if(Vn<0){Vel-=(1+FBFoot)*Vn*N;const FVector2D Vt=Vr-Vn*N;Vel-=Vt*.15;
     // The boot's rounded side: a sideways push also rolls the ball a little off the foot along X.
     if(FMath::Abs(N.Y)>.9)Vel.X+=(Ball.X>=Fx?1.:-1.)*FMath::Min(.25,-Vn*.12);}
    if(LastTouch!=F::Team[I] || Vn< -.3)++Touches;LastTouch=F::Team[I];}}
  if(Vel.Size()>FBMaxSpeed)Vel=Vel.GetSafeNormal()*FBMaxSpeed;
  // Dead ball: stopped where no man reaches it (between two rods) for 3 s, or stuck anywhere for 8 s.
  // A ball only pushed sideways along one rod (no progress along the table) for 7 s is a stuck ball too.
  if(FMath::Abs(Vel.X)<.06){Sideways+=Dt;if(Sideways>7){bLive=false;Call=TEXT("Bola presa: nova saída.");return false;}}else Sideways=0;
  if(Vel.Size()<.03){Still+=Dt;
   if(Still>3){bool bReach=false;
    for(int32 I=0;I<F::Rods && !bReach;++I){const double Tr=F::Travel(F::Count[I]);
     if(FMath::Abs(Ball.X-F::RodX(I))>F::FootR*.73+F::FootHX+F::R*.8)continue;
     for(int32 K=0;K<F::Count[I];++K){const double M=F::Man(F::Count[I],K);if(Ball.Y>=M-Tr-F::FootHY-F::R && Ball.Y<=M+Tr+F::FootHY+F::R){bReach=true;break;}}}
    // Out of every man's reach near an end (between the goal and the 2-bar, beside the goalie): the goalie of that
    // end puts it back into play at his feet, as in the table rules. Elsewhere it is a new drop at midfield.
    if(!bReach && FMath::Abs(Ball.X)>.45){const int32 G=Ball.X<0?0:F::Rods-1;Ball=FVector2D(F::RodX(G)+(G==0?.045:-.045),0);Vel=FVector2D::ZeroVector;
     Still=0;Sideways=0;++Restarts;Call=TEXT("Bola parada no gol: o goleiro repõe.");continue;}
    if(!bReach || Still>8){bLive=false;Call=TEXT("Bola parada: nova saída.");return false;}}}
  else Still=0;
 }
 return bLive;
}

void UMareFoosball::AI(int32 Side,double Dt,uint32 Seed,bool bAssistOnly,int32 Skip)
{
 FRandomStream Rng(Seed);const double Fw=FBFwd(Side);
 for(int32 I=0;I<F::Rods;++I){if(F::Team[I]!=Side || I==Skip)continue;
  FKick& K=Kick[I];K.Cool-=Dt;
  // Where the ball will cross this rod (folded off the side walls), or where it is when it is not coming.
  double Y=Ball.Y;
  if(bLive && FMath::Abs(Vel.X)>.05 && (F::RodX(I)-Ball.X)*Vel.X>0){const double Tt=FMath::Min((F::RodX(I)-Ball.X)/Vel.X,1.2);
   const double Span=2*(F::HY-F::R);double P=Ball.Y+Vel.Y*Tt+(F::HY-F::R);P=FMath::Fmod(P,2*Span);if(P<0)P+=2*Span;Y=(P>Span?2*Span-P:P)-(F::HY-F::R);}
  if(!bLive)Y=0;
  // The man that gets there with the least travel.
  const double Tr=F::Travel(F::Count[I]);double Want=RodY[I],Best=1e9;
  for(int32 M=0;M<F::Count[I];++M){const double Need=FMath::Clamp(Y-F::Man(F::Count[I],M),-Tr,Tr);const double Miss=FMath::Abs(Y-(Need+F::Man(F::Count[I],M)));
   const double Cost=Miss*4+FMath::Abs(Need-RodY[I]);if(Cost<Best){Best=Cost;Want=Need;}}
  if(K.Phase==1)Want+=AimY[I];
  // Close to the ball the hands slow down (a full-speed slide would bat it along the rod).
  const double Near=FMath::Abs(Ball.X-F::RodX(I))<.06 && bLive?.45:1.;
  const double Sp=(bAssistOnly?1.2:Skill[Side])*Near;
  SlideRod(I,RodY[I]+FMath::Clamp(Want-RodY[I],-Sp*Dt,Sp*Dt),Dt);
  // Lift the rods the team's own shot has to pass.
  const bool bOwnShot=bLive && LastTouch==Side && Vel.X*Fw>1.2 && (F::RodX(I)-Ball.X)*Fw>.03;
  if(bOwnShot && K.Phase==0){TurnRod(I,RodA[I]+FMath::Clamp(-Fw*1.5-RodA[I],-20*Dt,20*Dt),Dt);continue;}
  double Gap=0;NearestMan(I,Ball.Y,Gap);const double Dx=(Ball.X-F::RodX(I))*Fw,Speed=Vel.Size();
  const bool bInFront=bLive && Dx>-.005 && Dx<.075 && Gap<F::FootHY+F::R*.8 && Speed<3.5;
  // A slow ball just behind the rod (between two rods facing away from each other) gets a soft heel tap backward,
  // otherwise nobody could ever play it (it was 4 of every 5 dead balls).
  const bool bBehind=bLive && Dx<=-.005 && Dx>-.075 && Gap<F::FootHY+F::R*.8 && Speed<.4;
  if(!bAssistOnly && K.Phase==0 && K.Cool<=0 && (bInFront || bBehind)){K.Phase=1;K.T=0;AimY[I]=Rng.FRandRange(-.012,.012);K.Dir=bInFront?Fw:-Fw;}
  const double D=K.Dir;
  if(K.Phase==1){K.T+=Dt;
   // Wind up (feet back), then swing through.
   TurnRod(I,RodA[I]+FMath::Clamp(-D*.6-RodA[I],-14*Dt,14*Dt),Dt);
   if(FMath::Abs(RodA[I]+D*.6)<.05 || K.T>.25){K.Phase=2;K.T=D==Fw?Rng.FRandRange(24.,34.):Rng.FRandRange(8.,12.);}
   if(!(D==Fw?bInFront:bBehind) && K.T>.08){K.Phase=3;}}
  else if(K.Phase==2){TurnRod(I,RodA[I]+D*K.T*Dt,Dt);if(RodA[I]*D>1.25){K.Phase=3;K.Cool=.35;}}
  else{TurnRod(I,RodA[I]+FMath::Clamp(-RodA[I],-8*Dt,8*Dt),Dt);if(K.Phase==3 && FMath::Abs(RodA[I])<.05)K.Phase=0;}
 }
}

void UMareFoosball::PlayerControl(const FInput& In,double Dt)
{
 const int32 Was=Active;Active=PickActive(Active);if(Active!=Was){PlayerA=RodA[Active];Idle=1;}
 // The active rod: the mouse (or the left stick) slides it, sideways mouse (or the right stick) turns it; a click is a
 // quick shot (the kick of the AI's hands), the right button lifts the men. The other rods keep in line with the ball.
 SlideRod(Active,RodY[Active]+In.DY*.0035+In.PadY*1.3*Dt,Dt);
 FKick& K=Kick[Active];
 if(In.bShot && K.Phase==0){K.Phase=1;K.T=0;K.Dir=1;}
 if(K.Phase==1){K.T+=Dt;TurnRod(Active,RodA[Active]+FMath::Clamp(-.6-RodA[Active],-16*Dt,16*Dt),Dt);if(FMath::Abs(RodA[Active]+.6)<.05 || K.T>.2){K.Phase=2;K.T=30;}}
 else if(K.Phase==2){TurnRod(Active,RodA[Active]+K.T*Dt,Dt);if(RodA[Active]>1.25)K.Phase=3;}
 else if(In.bLift){TurnRod(Active,RodA[Active]+FMath::Clamp(-1.5-RodA[Active],-20*Dt,20*Dt),Dt);PlayerA=RodA[Active];K.Phase=0;}
 else{
  if(FMath::Abs(In.DX)>.01f){PlayerA+=FMath::Clamp(In.DX*.02,-.9,.9);Idle=0;}else Idle+=Dt;
  if(FMath::Abs(In.PadX)>.15f){PlayerA=In.PadX*1.4;Idle=0;}   // the stick sets the angle directly
  // Left alone, the men drop back to hanging (ready to block).
  if(Idle>.45f)PlayerA=PlayerA+FMath::Clamp(-FMath::UnwindRadians(PlayerA),-6*Dt,6*Dt);
  PlayerA=FMath::UnwindRadians(PlayerA);TurnRod(Active,PlayerA,Dt);if(K.Phase==3)K.Phase=0;}
 if(K.Phase!=0)PlayerA=RodA[Active];
 AI(0,Dt,GFrameNumber*17,true,Active);
}

// ---------------------------------------------------------------- world
FVector UMareFoosball::Local(double X,double Y,double Z) const{return Table.TransformPosition(FVector(-X*100,Y*100,(F::Field+Z)*100));}

void UMareFoosball::SpawnProps()
{
 auto S=FBSim(GetWorld());if(!S)return;
 const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
 if(!UMareSimulation::Object(S->BusinessGames(),TEXT("game_room"))->TryGetArrayField(TEXT("foosball"),At) || At->Num()!=4)return;
 Table=FTransform(FRotator(0,(*At)[3]->AsNumber(),0),FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber()));
 auto Spawn=[this](const FString& Slug,const FTransform& T){const FString Path=FBAsset(Slug);auto Mesh=Path.IsEmpty()?nullptr:LoadObject<UStaticMesh>(nullptr,*Path);if(!Mesh)return (AStaticMeshActor*)nullptr;
  auto A=GetWorld()->SpawnActor<AStaticMeshActor>(T.GetLocation(),T.Rotator());A->SetMobility(EComponentMobility::Movable);A->GetStaticMeshComponent()->SetStaticMesh(Mesh);
  A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);A->GetStaticMeshComponent()->SetCanEverAffectNavigation(false);return A;};
 TableActor=Spawn(TEXT("mare_foosball_body"),Table);
 if(!TableActor)return;
 TableActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
 BallActor=Spawn(TEXT("mare_foosball_ball"),Table);
 RodActors.Reset();for(int32 I=0;I<F::Rods;++I)RodActors.Add(Spawn(FBRodSlug(I),Table));
 NewMatch();
}

void UMareFoosball::StartMatch(APlayerController* Controller,const FString& InOpponent)
{
 if(bPlaying || !Controller || !TableActor)return;
 Player=Controller;Opponent=InOpponent.IsEmpty()?FString(TEXT("Hóspede")):InOpponent;bPlaying=true;bDemo=false;Delay=1.2f;Idle=0;PlayerA=0;
 int32 Look=1;Skill[0]=1.2;
 if(auto S=FBSim(GetWorld())){const auto Row=S->PoolPlayer(Opponent);
  // The pool roster's aim error (degrees) sets how fast the guest's hands are: a craque reaches everything.
  const double E=UMareSimulation::Number(Row,TEXT("skill"),2);Skill[1]=FMath::Clamp(1.75-.3*E,.75,1.6);Look=int32(UMareSimulation::Number(Row,TEXT("appearance"),1));}
 NewMatch();Active=3;
 // Always exactly at his grips: "adjust if possible" pushed him 50 cm into the cabinet when the guest waiting at
 // the counter stood on the spot (photo 06/11: shorts and hands over the far rods).
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 Guest=GetWorld()->SpawnActor<AMarePerson>(Local(0,F::HY+.5,-F::Field)+FVector(0,0,90),Table.Rotator()+FRotator(0,-90,0),Params);
 if(Guest){Guest->SaveId=TEXT("fb_guest");Guest->PersonName=Opponent;Guest->SetAppearance(Look);Guest->bAmbient=true;Guest->Tags.Add(TEXT("MareHotelGuest"));Guest->GetCharacterMovement()->DisableMovement();}
 // High over the player's side, looking down the field: both goals and every rod in view, the player's grips at the
 // bottom of the frame.
 // Steep enough that the near wall hides none of the field (from y -0.8, z 1.2 the ball vanished along the player's wall).
 const FVector Eye=Local(0,-.58,1.38),Look2=Local(0,.03,0);
 Camera=GetWorld()->SpawnActor<ACameraActor>(Eye,(Look2-Eye).Rotation());
 if(Camera){Camera->GetCameraComponent()->SetConstraintAspectRatio(false);Camera->GetCameraComponent()->SetFieldOfView(64.f);}   // no letterbox (MareGameRoom.cpp)
 Controller->SetViewTargetWithBlend(Camera,.5f);Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 // No arms or hands of the player on screen (Sergio, 03/11).
 if(auto Pawn=Controller->GetPawn()){Pawn->SetActorHiddenInGame(true);TArray<UPrimitiveComponent*> Parts;Pawn->GetComponents(Parts);HiddenParts.Reset();
  for(auto C:Parts)if(C->IsVisible()){HiddenParts.Add(C);C->SetVisibility(false);}}
 if(auto S=FBSim(GetWorld()))S->LastMessage=FString::Printf(TEXT("Pebolim contra %s: quem fizer %d gols primeiro vence."),*Opponent,WinGoals);
}

void UMareFoosball::EndMatch(const FString& Message)
{
 if(!bPlaying)return;bPlaying=false;
 UE_LOG(LogTemp,Display,TEXT("MARE_FB match end winner=%d goals=%d-%d touches=%d serves=%d"),Winner,Goals[0],Goals[1],Touches,Serves);
 if(auto PC=Player.Get()){PC->SetViewTargetWithBlend(PC->GetPawn(),.5f);PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();
  if(auto Pawn=PC->GetPawn()){Pawn->SetActorHiddenInGame(false);for(auto& C:HiddenParts)if(C.IsValid())C->SetVisibility(true);HiddenParts.Reset();}}
 for(auto& A:HiddenNearby)if(auto P=Cast<AMarePerson>(A.Get())){
  // The guest who waited at the counter leaves with the result (UMareBusinessWorld removes him): keep him hidden.
  if(P->SaveId.StartsWith(TEXT("biz_pebolim")))continue;
  P->SetActorHiddenInGame(false);if(P->MetaHumanBody && P->MetaHumanBody->GetChildActor())P->MetaHumanBody->GetChildActor()->SetActorHiddenInGame(false);}
 HiddenNearby.Reset();
 if(IsValid(Guest))Guest->Destroy();Guest=nullptr;if(IsValid(Camera))Camera->Destroy();Camera=nullptr;
 if(auto S=FBSim(GetWorld())){
  if(Winner>=0){S->RecordGame(TEXT("foosball"),Winner==0);const double Paid=S->PlayBusiness(TEXT("pebolim"),Hits(Goals[0],Goals[1]));
   S->LastMessage=(Winner==0?FString::Printf(TEXT("Você venceu %s no pebolim por %d × %d!"),*Opponent,Goals[0],Goals[1])
    :FString::Printf(TEXT("%s venceu no pebolim por %d × %d."),*Opponent,Goals[1],Goals[0]))+(Paid>0?FString::Printf(TEXT(" Fichas: R$ %.0f."),Paid):FString());}
  else if(!Message.IsEmpty())S->LastMessage=Message;}
 NewMatch();
}

FString UMareFoosball::Status() const
{
 if(!bPlaying)return FString();
 const bool bPad=MareGamepad::UsingGamepad();
 // Two short lines: the full sentence ran off the right edge of a 16:9 screen.
 FString Line=FString::Printf(TEXT("Pebolim · você %d × %d %s · %s sai\n%s"),Goals[0],Goals[1],*Opponent,bPad?TEXT("B"):TEXT("Q"),
  bPad?TEXT("analógico esq. desliza · dir. gira · RT chuta · LT levanta")
  :TEXT("mouse: frente/trás desliza, lados gira · clique chuta · direito levanta"));
 if(!Call.IsEmpty())Line+=TEXT("\n")+Call;
 return Line;
}

bool UMareFoosball::ActiveRodLine(FVector& From,FVector& To) const
{
 if(!bPlaying || !TableActor)return false;
 // Only the stretch from the bearing outward: the grip runs under the hint text at the bottom of the screen.
 From=Local(F::RodX(Active),-F::HY-.07,F::RodH);To=Local(F::RodX(Active),-F::HY-.02,F::RodH);return true;
}

bool UMareFoosball::NightDemo() const
{
 auto S=FBSim(GetWorld());if(!S)return false;
 const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const double Hour=UMareSimulation::Number(S->State,TEXT("minutes"))/60;
 return UMareSimulation::Object(S->BusinessGames(),TEXT("game_room"))->TryGetArrayField(TEXT("token_hours"),Hours) && Hours->Num()==2
  && Hour>=(*Hours)[0]->AsNumber() && Hour<(*Hours)[1]->AsNumber();
}

void UMareFoosball::UpdateProps(float DeltaSeconds)
{
 for(int32 I=0;I<RodActors.Num();++I)if(AStaticMeshActor* A=RodActors[I]){
  // The rod meshes have the grip on UE -Y (the player's side); the guest's rods are turned 180 degrees. Field X runs
  // along local -X, so the player's rods pitch by -angle and the guest's by +angle (feet forward = toward the goal).
  const FQuat Q=Table.GetRotation()*FRotator(F::Team[I]==0?-FMath::RadiansToDegrees(RodA[I]):FMath::RadiansToDegrees(RodA[I]),F::Team[I]==0?0.f:180.f,0).Quaternion();
  A->SetActorLocationAndRotation(Local(F::RodX(I),RodY[I],F::RodH),Q);}
 if(BallActor){
  const FVector2D Moved=Vel*DeltaSeconds;
  if(bLive && Moved.Size()>1e-5){const FVector Dir=Table.TransformVectorNoScale(FVector(-Moved.X,Moved.Y,0)).GetSafeNormal();
   // Renormalised every frame: the product drifted off unit length within a minute and the ball shrank out of sight.
   BallSpin=FQuat(FVector::CrossProduct(FVector::UpVector,Dir).GetSafeNormal(),Moved.Size()/F::R)*BallSpin;BallSpin.Normalize();}
  BallActor->SetActorLocationAndRotation(Local(Ball.X,Ball.Y,F::R),BallSpin);}
 // People: whoever stands at the table or in front of the match camera steps out of the picture until it ends.
 if(bPlaying && Camera){const FVector Cam=Camera->GetActorLocation(),Mid=Local(0,0,0);
  for(TActorIterator<AMarePerson> It(GetWorld());It;++It){AMarePerson* P=*It;if(P==Guest || HiddenNearby.Contains(P))continue;
   if(FVector::Dist2D(P->GetActorLocation(),Cam)<200 || FVector::Dist2D(P->GetActorLocation(),Mid)<170){HiddenNearby.Add(P);P->SetActorHiddenInGame(true);
    if(P->MetaHumanBody && P->MetaHumanBody->GetChildActor())P->MetaHumanBody->GetChildActor()->SetActorHiddenInGame(true);}}}
}

void UMareFoosball::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 auto S=FBSim(GetWorld());if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("salao_jogos"),bOwned);
 if(bOwned && !TableActor)SpawnProps();
 if(TableActor)TableActor->SetActorHiddenInGame(!bOwned);if(BallActor)BallActor->SetActorHiddenInGame(!bOwned);
 for(auto& A:RodActors)if(IsValid(A))A->SetActorHiddenInGame(!bOwned);
 if(!bOwned || !TableActor)return;
 const double Dt=FMath::Min(DeltaSeconds,.05f);
 if(!bPlaying){
  // Night: two hotel guests (UMareBusinessWorld's night players) play each other.
  const bool bNight=NightDemo();
  if(bNight && !bDemo){NewMatch();bDemo=true;Skill[0]=Skill[1]=1.;Opponent=TEXT("Hóspede");Delay=1.f;}
  else if(!bNight && bDemo){bDemo=false;NewMatch();}
  if(bDemo){
   if(Winner>=0 || !bLive){if((Delay-=Dt)<=0){if(Winner>=0)NewMatch();Serve(GFrameNumber);Delay=1.5f;}}
   AI(0,Dt,GFrameNumber*13);AI(1,Dt,GFrameNumber*29+7);const int32 Before=Touches;Step(Dt);
   if(Touches>Before && TableActor){const FVector At=Local(Ball.X,Ball.Y,F::R);UMareAudioWorld::Action(this,TEXT("tt_paddle"),&At,.35f);}}
  UpdateProps(DeltaSeconds);return;}
 auto PC=Player.Get();if(!PC){EndMatch(FString());return;}
 if(PC->WasInputKeyJustPressed(EKeys::Q) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right)){EndMatch(TEXT("Partida de pebolim encerrada."));return;}
 if(Winner>=0){if((Delay-=Dt)<=0)EndMatch(FString());else{Step(Dt);UpdateProps(DeltaSeconds);}return;}
 if(!bLive && (Delay-=Dt)<=0){Serve(GFrameNumber);Delay=1.4f;Call.Reset();}
 const bool bAuto=CVarFBAutoPlay.GetValueOnGameThread()!=0;
 if(bAuto)AI(0,Dt,GFrameNumber*17);
 else{
  FInput In;PC->GetInputMouseDelta(In.DX,In.DY);
  In.PadY=PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);In.PadX=PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX);
  In.bShot=PC->WasInputKeyJustPressed(EKeys::LeftMouseButton) || PC->WasInputKeyJustPressed(EKeys::Gamepad_RightTrigger);
  In.bLift=PC->IsInputKeyDown(EKeys::RightMouseButton) || PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis)>.3f;
  PlayerControl(In,Dt);}
 AI(1,Dt,GFrameNumber*31+3);
 const int32 Before=Touches;const int32 Was=Goals[0]+Goals[1];
 Step(Dt);
 const FVector At=Local(Ball.X,Ball.Y,F::R);
 if(Touches>Before)UMareAudioWorld::Action(this,TEXT("tt_paddle"),&At,FMath::Clamp(float(Vel.Size()/4),.3f,1.f));
 if(Goals[0]+Goals[1]!=Was){UMareAudioWorld::Action(this,TEXT("money_coins"),&At,.6f);Delay=2.f;}
 else if(!bLive && Delay<=0){UE_LOG(LogTemp,Display,TEXT("MARE_FB dead ball: %s"),*Call);Delay=1.4f;}
 UpdateProps(DeltaSeconds);
}
