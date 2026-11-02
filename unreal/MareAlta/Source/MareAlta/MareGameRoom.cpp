#include "MareGameRoom.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "Camera/CameraActor.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
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
}

void UMareGameRoom::Shoot(double Angle,double Speed)
{
 if(Balls[0].bIn)return;
 Balls[0].V=FVector2D(FMath::Cos(Angle),FMath::Sin(Angle))*FMath::Clamp(Speed,.2,6.);PottedThisShot.Reset();bScratch=false;
}

bool UMareGameRoom::Moving() const{for(const auto& B:Balls)if(!B.bIn && !B.V.IsNearlyZero(StopSpeed))return true;return false;}

bool UMareGameRoom::Step(double Seconds)
{
 const double Dt=1./240;
 for(double T=0;T<Seconds;T+=Dt){
  for(int32 I=0;I<16;++I){auto& B=Balls[I];if(B.bIn)continue;
   const double Speed=B.V.Size();if(Speed<StopSpeed){B.V=FVector2D::ZeroVector;continue;}
   // Rolling resistance plus a little drag on the cloth.
   const double NewSpeed=FMath::Max(0.,Speed-(RollingDecel+LinearDrag*Speed)*Dt);B.V*=NewSpeed/Speed;B.P+=B.V*Dt;
   // Pockets: the ball centre inside the mouth drops.
   for(const auto& Pk:Pockets)if(FVector2D::Distance(B.P,Pk)<PocketR*.95){B.bIn=true;B.V=FVector2D::ZeroVector;PottedThisShot.Add(I);if(I==0)bScratch=true;break;}
   if(B.bIn)continue;
   // Cushions, open near the six pockets.
   const bool bNearCorner=FMath::Abs(B.P.X)>L/2-PocketR*1.6 && FMath::Abs(B.P.Y)>W/2-PocketR*1.6;
   const bool bNearMiddle=FMath::Abs(B.P.X)<PocketR*1.25;
   if(!bNearCorner && FMath::Abs(B.P.X)>L/2-R){B.P.X=FMath::Sign(B.P.X)*(L/2-R);B.V.X*=-CushionBounce;}
   if(!bNearCorner && !bNearMiddle && FMath::Abs(B.P.Y)>W/2-R){B.P.Y=FMath::Sign(B.P.Y)*(W/2-R);B.V.Y*=-CushionBounce;}
   // Never leave the table even through a pocket gap.
   B.P.X=FMath::Clamp(B.P.X,-L/2-.03,L/2+.03);B.P.Y=FMath::Clamp(B.P.Y,-W/2-.03,W/2+.03);
  }
  // Ball-ball: equal masses, exchange the normal components (with a little loss).
  for(int32 I=0;I<16;++I)for(int32 J=I+1;J<16;++J){auto& A=Balls[I];auto& B=Balls[J];if(A.bIn || B.bIn)continue;
   FVector2D D=B.P-A.P;const double Dist=D.Size();if(Dist>=2*R || Dist<1e-9)continue;
   const FVector2D N=D/Dist;const double Overlap=2*R-Dist;A.P-=N*Overlap/2;B.P+=N*Overlap/2;
   const double Rel=FVector2D::DotProduct(A.V-B.V,N);if(Rel<=0)continue;
   const double Impulse=Rel*(1+Restitution)/2;A.V-=N*Impulse;B.V+=N*Impulse;}
  if(!Moving())return false;
 }
 return Moving();
}

void UMareGameRoom::ResolveShot()
{
 int32 Scored=0;bool bEight=false;
 for(int32 I:PottedThisShot){if(I==8)bEight=true;else if(I!=0)++Scored;}
 Score[Turn]+=Scored;
 const bool bFoul=bScratch || PottedThisShot.Contains(0) || Balls[0].bIn;
 if(bEight)Winner=Score[Turn]>=3?Turn:1-Turn;       // the 8 only after three balls of your own
 else if(Score[Turn]>=4)Winner=Turn;
 if(bFoul){Balls[0]=FBall();Balls[0].P=FVector2D(-L/4,0);
  // Head spot taken: slide along the head string until free.
  for(int32 Try=0;Try<20;++Try){bool bFree=true;for(int32 I=1;I<16;++I)if(!Balls[I].bIn && FVector2D::Distance(Balls[I].P,Balls[0].P)<2*R+.002)bFree=false;
   if(bFree)break;Balls[0].P.Y+=(Try%2?-1:1)*(Try/2+1)*2.2*R;}}
 if(Winner<0 && (Scored==0 || bFoul))Turn=1-Turn;
 PottedThisShot.Reset();bScratch=false;
}

bool UMareGameRoom::PathClear(const FVector2D& A,const FVector2D& B,int32 IgnoreA,int32 IgnoreB) const
{
 const FVector2D D=B-A;const double Len=D.Size();if(Len<1e-6)return true;const FVector2D U=D/Len;
 for(int32 I=0;I<16;++I){if(I==IgnoreA || I==IgnoreB || Balls[I].bIn)continue;
  const double T=FMath::Clamp(FVector2D::DotProduct(Balls[I].P-A,U),0.,Len);
  if(FVector2D::Distance(A+U*T,Balls[I].P)<2*R)return false;}
 return true;
}

void UMareGameRoom::PlanGuestShot(double& Angle,double& Speed,uint32 Seed) const
{
 FRandomStream Rng(Seed);const FVector2D CueP=Balls[0].P;double Best=-1;Angle=0;Speed=2;
 for(int32 I=1;I<16;++I){if(Balls[I].bIn || (I==8 && Score[1]<3))continue;
  for(const auto& Pk:Pockets){
   const FVector2D ToPocket=(Pk-Balls[I].P).GetSafeNormal();const FVector2D Ghost=Balls[I].P-ToPocket*2*R;
   const FVector2D ToGhost=(Ghost-CueP);const double Cut=FVector2D::DotProduct(ToGhost.GetSafeNormal(),ToPocket);
   if(Cut<.25 || !PathClear(CueP,Ghost,0,I) || !PathClear(Balls[I].P,Pk,I,-1))continue;
   const double D1=ToGhost.Size(),D2=FVector2D::Distance(Balls[I].P,Pk);
   const double Value=Cut/(.3+D1+D2);
   if(Value>Best){Best=Value;Angle=FMath::Atan2(ToGhost.Y,ToGhost.X);Speed=FMath::Clamp(1.1+1.6*(D1+D2),1.4,4.5);}}}
 if(Best<0){// No clean pot: tap the nearest ball to keep the game going.
  double Near=1e9;for(int32 I=1;I<16;++I)if(!Balls[I].bIn){const double D=FVector2D::Distance(CueP,Balls[I].P);if(D<Near){Near=D;Angle=FMath::Atan2(Balls[I].P.Y-CueP.Y,Balls[I].P.X-CueP.X);}}
  Speed=1.6;}
 // A hotel guest is decent, not perfect: about 1.4 degrees of aim error.
 Angle+=FMath::DegreesToRadians(Rng.GetFraction()*2.8-1.4);Speed*=Rng.FRandRange(.92,1.08);
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

void UMareGameRoom::StartMatch(APlayerController* Controller,double InStake)
{
 if(bPlaying || !Controller)return;Player=Controller;Stake=InStake;Rack();bPlaying=true;bShotRunning=false;Charge=0;AimAngle=0;
 // The guest opponent stands at the foot of the table.
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
 Guest=GetWorld()->SpawnActor<AMarePerson>(Table.TransformPosition(FVector(L*50+70,40,90)),Table.Rotator()+FRotator(0,180,0),Params);
 if(Guest){Guest->SaveId=TEXT("pool_guest");Guest->PersonName=TEXT("Hóspede");Guest->SetAppearance(1);Guest->bAmbient=true;Guest->Tags.Add(TEXT("MareHotelGuest"));Guest->GetCharacterMovement()->DisableMovement();}
 Camera=GetWorld()->SpawnActor<ACameraActor>(World(FVector2D(-L/2-.6,0),.9),FRotator(-45,Table.Rotator().Yaw,0));
 Controller->SetViewTargetWithBlend(Camera,.5f);Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 // The player stands at the table: hide the body so it never sits between the match camera and the cloth.
 if(auto Pawn=Controller->GetPawn())Pawn->SetActorHiddenInGame(true);
 if(Cue)Cue->SetActorHiddenInGame(false);
 if(auto S=Sim(GetWorld()))S->LastMessage=Stake>0?FString::Printf(TEXT("Sinuca valendo R$ %.0f: quem encaçapar 4 primeiro vence."),Stake):TEXT("Sinuca: quem encaçapar 4 primeiro vence. Mouse mira, segure o clique para a força, Q sai.");
}

void UMareGameRoom::EndMatch(const FString& Message)
{
 if(!bPlaying)return;bPlaying=false;
 if(auto PC=Player.Get()){PC->SetViewTargetWithBlend(PC->GetPawn(),.5f);PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();if(auto Pawn=PC->GetPawn())Pawn->SetActorHiddenInGame(false);}
 if(IsValid(Guest))Guest->Destroy();Guest=nullptr;if(IsValid(Camera))Camera->Destroy();Camera=nullptr;if(Cue)Cue->SetActorHiddenInGame(true);
 if(auto S=Sim(GetWorld())){
  if(Winner>=0 && Stake>0)S->SettleBet(Winner==0?Stake:-Stake,Winner==0?TEXT("Sinuca: aposta ganha"):TEXT("Sinuca: aposta perdida"));
  if(Winner==0)S->AddFame(2);
  if(!Message.IsEmpty())S->LastMessage=Message;}
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
 return FString::Printf(TEXT("Sinuca · você %d × %d hóspede · %s"),Score[0],Score[1],bShotRunning?TEXT("bolas rolando"):Turn==0?TEXT("sua vez: mouse mira, segure e solte o clique"):TEXT("vez do hóspede"));
}

void UMareGameRoom::UpdateProps(float DeltaSeconds)
{
 for(int32 I=0;I<16 && I<BallActors.Num();++I)if(auto A=BallActors[I]){A->SetActorHiddenInGame(Balls[I].bIn);
  // Roll: rotate about the axis perpendicular to the velocity.
  const FVector Pos=World(Balls[I].P,-R);const FVector Delta=Pos-A->GetActorLocation();A->SetActorLocation(Pos);
  if(Delta.SizeSquared()>1e-4){const FVector Axis=FVector::CrossProduct(FVector::UpVector,Delta).GetSafeNormal();
   A->AddActorWorldRotation(FQuat(Axis,Delta.Size()/(R*100)));}}
 if(Cue){const bool bShow=bPlaying && Turn==0 && !bShotRunning && !Balls[0].bIn;Cue->SetActorHiddenInGame(!bShow);
  if(bShow){const FVector2D Dir(FMath::Cos(AimAngle),FMath::Sin(AimAngle));const double Back=.04+.25*Charge;
   // The cue (built along +X, tip at 1.48 m) lies behind the cue ball, slightly raised at the butt.
   const FVector Tip=World(Balls[0].P-Dir*Back,.004);const FRotator Rot=(World(Balls[0].P)-World(Balls[0].P-Dir,.12)).Rotation();
   Cue->SetActorLocationAndRotation(Tip-Rot.Vector()*148,Rot);}}
 if(Camera && bPlaying){const FVector2D Dir(FMath::Cos(AimAngle),FMath::Sin(AimAngle));
  const FVector Eye=World(Balls[0].P-Dir*.75,.55);const FVector Look=World(Balls[0].P+Dir*.6);
  Camera->SetActorLocationAndRotation(FMath::VInterpTo(Camera->GetActorLocation(),Eye,DeltaSeconds,4.f),FMath::RInterpTo(Camera->GetActorRotation(),(Look-Eye).Rotation(),DeltaSeconds,4.f));}
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
  if(PC->WasInputKeyJustPressed(EKeys::Q)){EndMatch(TEXT("Partida de sinuca encerrada."));return;}
  if(bShotRunning){
   if(!Step(DeltaSeconds)){bShotRunning=false;ResolveShot();
    if(Winner>=0){EndMatch(Winner==0?TEXT("Você venceu a partida de sinuca!"):TEXT("O hóspede venceu a partida de sinuca."));return;}
    GuestDelay=1.2f;}}
  else if(Turn==0){
   float DX=0,DY=0;PC->GetInputMouseDelta(DX,DY);AimAngle+=DX*.004;
   if(PC->IsInputKeyDown(EKeys::LeftMouseButton)){bCharging=true;Charge=FMath::Min(1.f,Charge+DeltaSeconds/1.2f);}
   else if(bCharging){bCharging=false;Shoot(AimAngle,.5+5.5*Charge);Charge=0;bShotRunning=true;
    if(auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>())Audio->PlayCue(TEXT("click"),.3f);}}
  else if((GuestDelay-=DeltaSeconds)<=0){double Angle=0,Speed=0;PlanGuestShot(Angle,Speed,FCrc::StrCrc32(*FString::Printf(TEXT("%d-%d"),Score[0],Score[1]))+GFrameNumber);
   AimAngle=Angle;Shoot(Angle,Speed);bShotRunning=true;}
 }
 UpdateProps(DeltaSeconds);
}
