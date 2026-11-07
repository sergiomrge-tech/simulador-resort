#include "MarePoolSwimWorld.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareAudioWorld.h"
#include "Animation/AnimSequence.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

static bool bReloadDefs=false;
TStatId UMarePoolSwimWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMarePoolSwimWorld,STATGROUP_Tickables);}

TSharedPtr<FJsonObject> UMarePoolSwimWorld::Defs()
{
 static TSharedPtr<FJsonObject> Cached;
 if(bReloadDefs){Cached.Reset();bReloadDefs=false;}
 if(!Cached.IsValid()){FString Text;Cached=MakeShared<FJsonObject>();
  if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/pool_swim.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Cached);}
 return Cached;
}

static double Num(const TSharedPtr<FJsonObject>& O,const TCHAR* K,double Def=0){return UMareSimulation::Number(O,K,Def);}
static FVector2D Pair(const TSharedPtr<FJsonObject>& O,const TCHAR* K,double A,double B)
{
 const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(O.IsValid() && O->TryGetArrayField(K,L) && L->Num()>=2)return FVector2D((*L)[0]->AsNumber(),(*L)[1]->AsNumber());
 return FVector2D(A,B);
}
static FBox2D Rect(const TSharedPtr<FJsonObject>& P)
{
 const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(!P->TryGetArrayField(TEXT("swim_rect"),L) || L->Num()<4)return FBox2D(FVector2D(-100,-100),FVector2D(100,100));
 return FBox2D(FVector2D((*L)[0]->AsNumber(),(*L)[1]->AsNumber()),FVector2D((*L)[2]->AsNumber(),(*L)[3]->AsNumber()));
}
static TArray<TSharedPtr<FJsonValue>> Pools()
{
 const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(UMarePoolSwimWorld::Defs()->TryGetArrayField(TEXT("pools"),L))return *L;return {};   // i18n:skip
}

void UMarePoolSwimWorld::Deinitialize(){ClearAll();Super::Deinitialize();}

void UMarePoolSwimWorld::ClearAll()
{
 for(auto& S:Swimmers)if(S.Person.IsValid())S.Person->Destroy();
 Swimmers.Empty();
}

int32 UMarePoolSwimWorld::Wanted(int32 Pool,const TSharedPtr<FJsonObject>& P)const
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim || !Sim->State.IsValid())return 0;
 bool bOwned=false;UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(UMareSimulation::String(P,TEXT("unlock")),bOwned);
 if(!bOwned)return 0;
 if(Forced>=0)return Forced;
 const FVector2D Hours=Pair(Defs(),TEXT("hours"),9,18);const double Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.;
 if(Hour<Hours.X || Hour>=Hours.Y)return 0;
 if(UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain"))return 0;
 const FVector2D Count=Pair(P,TEXT("count"),3,5);
 return int32(UMareSimulation::String(Sim->State,TEXT("day_event"))==TEXT("calor")?Count.Y:Count.X);
}

bool UMarePoolSwimWorld::Seen(const FVector& At)const
{
 // Conservative: anywhere in front of the camera within 60 m counts as seen (walls are ignored), and anything close.
 APlayerCameraManager* Cam=UGameplayStatics::GetPlayerCameraManager(GetWorld(),0);if(!Cam)return false;
 const FVector Eye=Cam->GetCameraLocation(),To=At-Eye;const float Dist=To.Size();
 if(Dist<700)return true;if(Dist>6000)return false;
 const float Half=FMath::DegreesToRadians(Cam->GetFOVAngle()*.5f+12.f);
 return FVector::DotProduct(To/Dist,Cam->GetCameraRotation().Vector())>FMath::Cos(Half);
}

// A swimmer's body seen from above: lying along its heading (head ~90 cm ahead of the root, feet ~85 cm behind, the
// Swim_Fwd clip measured on the MetaHumans), or a point when treading water upright.
static void Body(const FVector& At,float Yaw,bool bLong,FVector& A,FVector& B)
{
 const FVector F=FRotator(0,Yaw,0).Vector();const FVector P(At.X,At.Y,0);
 if(bLong){A=P-F*85.f;B=P+F*90.f;}else{A=P;B=P+F*.1f;}
}
static bool Lies(UMarePoolSwimWorld::EState St,const FVector& Pos,const FVector& Target)
{
 using E=UMarePoolSwimWorld::EState;
 return St==E::Swim || St==E::Jump || St==E::Float || (St==E::Chat && FVector::Dist2D(Pos,Target)>70);
}

bool UMarePoolSwimWorld::Clear(int32 Self,const FVector& At,float Yaw,bool bLong,float Gap,const TSharedPtr<FJsonObject>& P)const
{
 FVector A,B;Body(At,Yaw,bLong,A,B);
 for(int32 J=0;J<Swimmers.Num();++J){const FSwimmer& O=Swimmers[J];
  if(J==Self || !O.Person.IsValid() || O.State==EState::Edge || (Swimmers.IsValidIndex(Self) && (Swimmers[Self].Partner==J || O.Pool!=Swimmers[Self].Pool)))continue;
  FVector C,D,X,Y;Body(O.Pos,O.Yaw,Lies(O.State,O.Pos,O.Target),C,D);
  FMath::SegmentDistToSegmentSafe(A,B,C,D,X,Y);if(FVector::Dist(X,Y)<Gap)return false;
  // Someone on the way to a chat spot keeps it free too.
  if(O.State==EState::Chat){FMath::SegmentDistToSegmentSafe(A,B,FVector(O.Target.X,O.Target.Y,0),FVector(O.Target.X,O.Target.Y,0)+FVector(.1f,0,0),X,Y);if(FVector::Dist(X,Y)<Gap)return false;}}
 // Floats and balls on the water ([x, y, radius]).
 const TArray<TSharedPtr<FJsonValue>>* Obs=nullptr;
 if(P.IsValid() && P->TryGetArrayField(TEXT("obstacles"),Obs))for(const auto& V:*Obs){const auto& O=V->AsArray();if(O.Num()<3)continue;   // i18n:skip
  const FVector C(O[0]->AsNumber(),O[1]->AsNumber(),0);if(FMath::PointDistToSegment(C,A,B)<O[2]->AsNumber()+Gap*.5f)return false;}
 return true;
}

FVector UMarePoolSwimWorld::RandomPoint(const TSharedPtr<FJsonObject>& P,const FVector& Away)const
{
 const FBox2D R=Rect(P);const float Z=Num(P,TEXT("water_z"));FVector Best(R.GetCenter().X,R.GetCenter().Y,Z);float BestScore=-1;
 for(int32 T=0;T<16;++T){const FVector C(FMath::FRandRange(R.Min.X,R.Max.X),FMath::FRandRange(R.Min.Y,R.Max.Y),Z);
  float Score=FVector::Dist2D(C,Away);
  const TArray<TSharedPtr<FJsonValue>>* Obs=nullptr;
  if(P->TryGetArrayField(TEXT("obstacles"),Obs))for(const auto& V:*Obs){const auto& O=V->AsArray();if(O.Num()>=3)Score=FMath::Min(Score,(FVector::Dist2D(C,FVector(O[0]->AsNumber(),O[1]->AsNumber(),0))-float(O[2]->AsNumber()))*2.f);}   // i18n:skip
  for(const auto& S:Swimmers)if(S.Person.IsValid())Score=FMath::Min(Score,FVector::Dist2D(S.Pos,C)*1.5f);
  if(Score>BestScore){BestScore=Score;Best=C;}}
 return Best;
}

void UMarePoolSwimWorld::Place(FSwimmer& S,const TSharedPtr<FJsonObject>& P,const TCHAR* Pose,float Z)
{
 AMarePerson* Person=S.Person.Get();if(!Person)return;
 Person->HoldPose=Pose;
 Person->SetActorLocationAndRotation(FVector(S.Pos.X,S.Pos.Y,Num(P,TEXT("water_z"))+Z),FRotator(0,S.Yaw,0));
}

bool UMarePoolSwimWorld::Spawn(int32 Pool,const TSharedPtr<FJsonObject>& P)
{
 const TArray<TSharedPtr<FJsonValue>>* Entries=nullptr;if(!P->TryGetArrayField(TEXT("entries"),Entries) || !Entries->Num())return false;   // i18n:skip
 const int32 Pick=FMath::RandRange(0,Entries->Num()-1);const auto& E=(*Entries)[Pick]->AsArray();if(E.Num()<3)return false;
 const FVector At(E[0]->AsNumber(),E[1]->AsNumber(),Num(P,TEXT("edge_z")));
 if(Seen(At)){LastSpawnFail=FString::Printf(TEXT("seen %.0f,%.0f"),At.X,At.Y);return false;}   // i18n:skip
 for(const auto& S:Swimmers)if(S.Person.IsValid() && S.State==EState::Edge && FVector::Dist2D(S.Pos,At)<120){LastSpawnFail=TEXT("entry busy");return false;}   // i18n:skip
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 AMarePerson* Person=GetWorld()->SpawnActor<AMarePerson>(At+FVector(0,0,88),FRotator(0,E[2]->AsNumber(),0),Params);if(!Person){LastSpawnFail=TEXT("spawn failed");return false;}   // i18n:skip
 Person->SaveId=FString::Printf(TEXT("poolswim_%d"),++Serial);Person->PersonName=TEXT("Hóspede");Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);
 Person->bAmbient=true;Person->Tags.Add(TEXT("MareBather"));Person->Tags.Add(TEXT("MarePoolSwimmer"));
 Person->GetCharacterMovement()->DisableMovement();Person->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 Person->HoldPose=TEXT("Idle");
 FSwimmer S;S.Person=Person;S.Pool=Pool;S.State=EState::Edge;S.Pos=At;S.JumpFrom=At;S.Yaw=E[2]->AsNumber();
 S.Timer=FMath::FRandRange(2.f,4.f);S.Total=0;   // a look at the water first (the MetaHuman also needs a moment to dress)
 S.Speed=FMath::FRandRange(Pair(Defs(),TEXT("speed"),45,70).X,Pair(Defs(),TEXT("speed"),45,70).Y);
 const FVector2D Legs=Pair(Defs(),TEXT("legs"),2,4);S.Legs=FMath::RandRange(int32(Legs.X),int32(Legs.Y));   // i18n:skip
 Swimmers.Add(S);return true;
}

void UMarePoolSwimWorld::Step(int32 I,float Dt)
{
 FSwimmer& S=Swimmers[I];AMarePerson* Person=S.Person.Get();if(!Person)return;
 const TArray<TSharedPtr<FJsonValue>> All=Pools();if(!All.IsValidIndex(S.Pool))return;const auto P=All[S.Pool]->AsObject();
 const auto D=Defs();const float WaterZ=Num(P,TEXT("water_z")),SwimZ=Num(D,TEXT("swim_z"),52),TreadZ=Num(D,TEXT("tread_z"),56);
 S.Timer-=Dt;
 auto TurnTo=[&](float Goal,float Rate){S.Yaw=FMath::FixedTurn(S.Yaw,Goal,Rate*Dt);};
 auto StartSwim=[&](){S.State=EState::Swim;S.Partner=-1;S.Target=RandomPoint(P,S.Pos);};
 switch(S.State){
 case EState::Edge:
  Person->SetActorLocationAndRotation(S.Pos+FVector(0,0,88),FRotator(0,S.Yaw,0));
  if(S.Timer<=0 && Person->Clips.Contains(TEXT("Jump_Start"))){
   // Jump in where the water in front is free.
   const FVector Land=S.Pos+FRotator(0,S.Yaw,0).Vector()*Num(D,TEXT("jump_in"),140);
   // Where the swimmer lands must be free (the body then swims off and avoids the rest).
   // After 10 s of waiting only people count (a float or the ball drifting there would keep them on the edge forever).
   if(!Clear(I,Land,S.Yaw,false,Num(D,TEXT("spacing"),60)*2,S.Total>10?nullptr:P)){S.Timer=1.f;S.Total+=1.f;break;}
   S.State=EState::Jump;S.JumpFrom=S.Pos;S.Target=FVector(Land.X,Land.Y,WaterZ);
   S.Total=Person->Clips[TEXT("Jump_Start")]->GetPlayLength()*.6f;S.Timer=S.Total+Num(D,TEXT("jump_time"),.8);
   Person->PlayPose(TEXT("Jump_Start"),false);Person->HoldPose=TEXT("Jump_Start");}
  break;
 case EState::Jump:{
  // Push-off (first part of Jump_Start in place), then a short arc into the water.
  const float Flight=Num(D,TEXT("jump_time"),.8);const float Gone=Flight-(S.Timer);
  if(Gone<0){Person->SetActorLocationAndRotation(S.JumpFrom+FVector(0,0,88),FRotator(0,S.Yaw,0));break;}
  if(Person->HoldPose!=TEXT("Jump"))Person->HoldPose=TEXT("Jump");
  const float A=FMath::Clamp(Gone/Flight,0.f,1.f);
  const FVector From=S.JumpFrom+FVector(0,0,88),To=S.Target+FVector(0,0,SwimZ);
  S.Pos=FMath::Lerp(S.JumpFrom,S.Target,A);
  Person->SetActorLocationAndRotation(FMath::Lerp(From,To,A)+FVector(0,0,Num(D,TEXT("jump_height"),70)*4*A*(1-A)),FRotator(0,S.Yaw,0));
  if(A>=1){const FVector Splash=S.Target;UMareAudioWorld::Action(this,TEXT("swim_splash"),&Splash,.7f);StartSwim();}
  break;}
 case EState::Swim:{
  if(S.bLeaving && !Seen(S.Pos)){Person->Destroy();break;}
  const FVector To=S.Target-S.Pos;const float Dist=To.Size2D();
  if(Dist<60){
   if(--S.Legs>0){S.Target=RandomPoint(P,S.Pos);break;}
   const FVector2D Legs=Pair(D,TEXT("legs"),2,4);S.Legs=FMath::RandRange(int32(Legs.X),int32(Legs.Y));   // i18n:skip
   // Something else for a while: chat with a free swimmer of this pool, or float on the back.
   int32 Mate=-1;for(int32 J=0;J<Swimmers.Num();++J)if(J!=I && Swimmers[J].Person.IsValid() && Swimmers[J].Pool==S.Pool && Swimmers[J].State==EState::Swim && Swimmers[J].Partner<0 && !Swimmers[J].bLeaving){Mate=J;break;}
   if(Mate>=0 && FMath::FRand()<.6f){
    FSwimmer& M=Swimmers[Mate];const FVector2D Secs=Pair(D,TEXT("chat_seconds"),20,40);const float Talk=FMath::FRandRange(Secs.X,Secs.Y);
    // The mate stops where it is; this one swims up to chat_gap in front of it.
    const FVector Dir=(S.Pos-M.Pos).GetSafeNormal2D();const FVector Spot=M.Pos+(Dir.IsNearlyZero()?FVector(1,0,0):Dir)*Num(D,TEXT("chat_gap"),110);
    const FBox2D R=Rect(P);
    if(R.IsInside(FVector2D(Spot)) && Clear(I,Spot,0,false,Num(D,TEXT("spacing"),60),P)){
     S.State=EState::Chat;S.Partner=Mate;S.Target=FVector(Spot.X,Spot.Y,WaterZ);S.Timer=Talk+8;
     M.State=EState::Chat;M.Partner=I;M.Target=M.Pos;M.Timer=Talk+8;break;}}
   const FVector2D Secs=Pair(D,TEXT("float_seconds"),18,35);
   S.State=EState::Float;S.Timer=FMath::FRandRange(Secs.X,Secs.Y);
   Person->LieOn(FVector(S.Pos.X,S.Pos.Y,WaterZ-Num(D,TEXT("float_drop"),15)),S.Yaw);break;}
  // Forward along the heading, turning toward the target; slow down and pick elsewhere when someone is ahead.
  TurnTo(To.Rotation().Yaw,Num(D,TEXT("turn_rate"),70));
  const FVector Fwd=FRotator(0,S.Yaw,0).Vector();float Speed=S.Speed;
  if(!Clear(I,S.Pos+Fwd*Num(D,TEXT("look_ahead"),70),S.Yaw,true,Num(D,TEXT("spacing"),60),P)){Speed=0;if(S.Timer<=0){S.Target=RandomPoint(P,S.Pos-Fwd*200);S.Timer=1.5f;}}
  // Facing away from the target: turn in place first (no wide loops into the walls).
  if(FMath::Abs(FMath::FindDeltaAngleDegrees(S.Yaw,To.Rotation().Yaw))>60)Speed*=.2f;
  FVector Next=S.Pos+Fwd*Speed*Dt;const FBox2D R=Rect(P);
  Next.X=FMath::Clamp(Next.X,R.Min.X,R.Max.X);Next.Y=FMath::Clamp(Next.Y,R.Min.Y,R.Max.Y);S.Pos=Next;
  Place(S,P,TEXT("Swim_Fwd"),SwimZ);break;}
 case EState::Float:
  if(S.Timer<=0 || (S.bLeaving && !Seen(S.Pos))){Person->bLying=false;Person->SetActorRotation(FRotator(0,S.Yaw,0));
   if(S.bLeaving && !Seen(S.Pos)){Person->Destroy();break;}
   StartSwim();}
  break;
 case EState::Chat:{
  FSwimmer* M=Swimmers.IsValidIndex(S.Partner)?&Swimmers[S.Partner]:nullptr;
  if(!M || !M->Person.IsValid() || M->Partner!=I || S.Timer<=0){StartSwim();break;}
  const FVector To=S.Target-S.Pos;
  if(To.Size2D()>70){TurnTo(To.Rotation().Yaw,Num(D,TEXT("turn_rate"),70));
   const FVector Fwd=FRotator(0,S.Yaw,0).Vector();float Speed=S.Speed*(FMath::Abs(FMath::FindDeltaAngleDegrees(S.Yaw,To.Rotation().Yaw))>60?.2f:1.f);
   if(!Clear(I,S.Pos+Fwd*Num(D,TEXT("look_ahead"),70),S.Yaw,true,Num(D,TEXT("spacing"),60),P))Speed=0;
   S.Pos+=Fwd*FMath::Min(Speed*Dt,To.Size2D());Place(S,P,TEXT("Swim_Fwd"),SwimZ);break;}
  // The last stretch upright, drifting in slowly (the stroke would reach the partner with the hands).
  if(To.Size2D()>5)S.Pos+=To.GetSafeNormal2D()*FMath::Min(25.f*Dt,To.Size2D());
  // Facing each other, treading water; now and then a smile.
  TurnTo((M->Pos-S.Pos).Rotation().Yaw,60);Place(S,P,TEXT("Swim_Idle"),TreadZ);
  if(FMath::FRand()<Dt*.06f)Person->Express(TEXT("smile"),3.f);
  break;}
 }
}

void UMarePoolSwimWorld::Tick(float DeltaSeconds)
{
 UWorld* W=GetWorld();if(!W || !W->IsGameWorld() || !W->GetGameInstance())return;
 const float Dt=FMath::Min(DeltaSeconds,.1f);
 for(int32 I=0;I<Swimmers.Num();++I)if(Swimmers[I].Person.IsValid())Step(I,Dt);
 // Drop the destroyed ones (partners point by index: fix them up).
 for(int32 I=Swimmers.Num()-1;I>=0;--I)if(!Swimmers[I].Person.IsValid()){Swimmers.RemoveAt(I);
  for(auto& S:Swimmers){if(S.Partner==I)S.Partner=-1;else if(S.Partner>I)--S.Partner;}}
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=1.f;
 const TArray<TSharedPtr<FJsonValue>> All=Pools();
 LastWanted.SetNum(All.Num());
 for(int32 Pool=0;Pool<All.Num();++Pool){const auto P=All[Pool]->AsObject();const int32 Want=Wanted(Pool,P);LastWanted[Pool]=Want;
  int32 Have=0;for(auto& S:Swimmers)if(S.Pool==Pool && !S.bLeaving)++Have;
  // Too many (evening, rain, fewer guests): the extra ones leave once nobody is looking.
  for(int32 I=Swimmers.Num()-1;I>=0 && Have>Want;--I)if(Swimmers[I].Pool==Pool && !Swimmers[I].bLeaving){Swimmers[I].bLeaving=true;--Have;
   if(Swimmers[I].State==EState::Edge && !Seen(Swimmers[I].Pos))Swimmers[I].Person->Destroy();}
  // One newcomer at a time, a few seconds apart.
  Spawned-=1.f;if(Have<Want && Spawned<=0 && Spawn(Pool,P))Spawned=Forced>=0?0.f:FMath::FRandRange(3.f,7.f);}   // QA: no wait between newcomers
}

FString UMarePoolSwimWorld::Dump()const
{
 static const TCHAR* Names[]={TEXT("edge"),TEXT("jump"),TEXT("swim"),TEXT("float"),TEXT("chat")};
 FString Out=FString::Printf(TEXT("want=%s fail=%s | "),*FString::JoinBy(LastWanted,TEXT(","),[](int32 V){return FString::FromInt(V);}),*LastSpawnFail);   // i18n:skip   // i18n:skip
 for(int32 I=0;I<Swimmers.Num();++I){const auto& S=Swimmers[I];if(!S.Person.IsValid())continue;const FVector L=S.Person->GetActorLocation();
  Out+=FString::Printf(TEXT("%d %s %s pos=(%.0f,%.0f,%.0f) yaw=%.0f partner=%d%s; "),I,*S.Person->MetaHuman,Names[uint8(S.State)],L.X,L.Y,L.Z,S.Yaw,S.Partner,S.bLeaving?TEXT(" leaving"):TEXT(""));}   // i18n:skip
 return Out;
}

static FAutoConsoleCommandWithWorldAndArgs GMarePoolSwim(TEXT("mare.PoolSwim"),TEXT("mare.PoolSwim <n|auto|clear|reload|dump>: QA of the pool swimmers (pool_swim.json)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(!World)return;auto Sub=World->GetSubsystem<UMarePoolSwimWorld>();if(!Sub)return;const FString A=Args.Num()?Args[0]:TEXT("dump");
  if(A==TEXT("clear")){Sub->ClearAll();Sub->Forced=0;}
  else if(A==TEXT("reload")){bReloadDefs=true;UMarePoolSwimWorld::Defs();}   // i18n:skip
  else if(A==TEXT("auto"))Sub->Forced=-1;   // i18n:skip
  else if(A!=TEXT("dump"))Sub->Forced=FCString::Atoi(*A);
  UE_LOG(LogTemp,Display,TEXT("MARE_POOLSWIM forced=%d %s"),Sub->Forced,*Sub->Dump());}));
