#include "MareBeachSports.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "Components/BoxComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

using ESport=UMareBeachSportsWorld::ESport;
using ETouch=UMareBeachSportsWorld::ETouch;
using EPhase=UMareBeachSportsWorld::EPhase;
namespace
{
 const float BallRadius[]={0.f,10.5f,3.f,11.f};   // by ESport
 const float NetTop=224.f;
 float Rnd(float A,float B){return FMath::FRandRange(A,B);}
 double Num(const TSharedPtr<FJsonObject>& O,const TCHAR* K,double Def=0){return UMareSimulation::Number(O,K,Def);}
 /** Where the ball is touched relative to the feet: cm ahead and cm up. */
 FVector2D TouchPoint(ETouch T)
 {
  switch(T){
  case ETouch::Bump:return FVector2D(55,92);case ETouch::Set:return FVector2D(22,208);case ETouch::Attack:return FVector2D(32,262);
  case ETouch::Serve:return FVector2D(36,215);case ETouch::Catch:return FVector2D(38,125);case ETouch::Palm:return FVector2D(45,140);
  default:return FVector2D(44,11);}   // foot: kick, trap, save
 }
 bool FootTouch(ETouch T){return T==ETouch::Kick || T==ETouch::Trap || T==ETouch::Save;}
 bool TwoHands(ETouch T){return T==ETouch::Bump || T==ETouch::Set || T==ETouch::Catch;}
}

TStatId UMareBeachSportsWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareBeachSportsWorld,STATGROUP_Tickables);}

TSharedPtr<FJsonObject> UMareBeachSportsWorld::Defs()
{
 static TSharedPtr<FJsonObject> Cached;
 if(!Cached.IsValid()){FString Text;Cached=MakeShared<FJsonObject>();
  if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/beach_sports.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Cached);   // i18n:skip
  if(!Cached.IsValid())Cached=MakeShared<FJsonObject>();}
 return Cached;
}

ESport UMareBeachSportsWorld::SportOfDay(int32 Day)
{
 // A chain from day 1: each day moves one or two steps round the three sports, so it is never yesterday's.
 Day=FMath::Clamp(Day,1,20000);int32 S=0;
 for(int32 D=1;D<=Day;++D){const uint32 H=FCrc::MemCrc32(&D,sizeof(D),0x5EA5u);S=D==1?int32(H%3u):(S+1+int32(H%2u))%3;}
 return ESport(S+1);
}
const TCHAR* UMareBeachSportsWorld::SportName(ESport InSport)
{
 switch(InSport){case ESport::Volley:return TEXT("volei");case ESport::Peteca:return TEXT("peteca");case ESport::Soccer:return TEXT("futebol");default:return TEXT("nenhum");}   // i18n:skip
}

void UMareBeachSportsWorld::Deinitialize(){ClearAll();Super::Deinitialize();}

void UMareBeachSportsWorld::ClearAll()
{
 for(auto& P:Players)if(P.Person.IsValid())P.Person->Destroy();
 Players.Empty();
 for(auto& A:Props)if(A.IsValid())A->Destroy();
 Props.Empty();Ball.Reset();
 Sport=ESport::None;Phase=EPhase::Rest;Receiver=Holder=LastHitter=-1;Rally=0;bGoal=bPicked=bRebound=false;Points[0]=Points[1]=0;
}

FVector UMareBeachSportsWorld::At(float Along,float Across,float Up)const
{
 const FRotator R(0,CourtYaw,0);
 FVector P=Centre+R.Vector()*Along+FRotationMatrix(R).GetScaledAxis(EAxis::Y)*Across;P.Z=Ground(P)+Up;return P;
}
float UMareBeachSportsWorld::AlongOf(const FVector& P)const{return FVector::DotProduct(P-Centre,FRotator(0,CourtYaw,0).Vector());}
float UMareBeachSportsWorld::AcrossOf(const FVector& P)const{return FVector::DotProduct(P-Centre,FRotationMatrix(FRotator(0,CourtYaw,0)).GetScaledAxis(EAxis::Y));}

float UMareBeachSportsWorld::Ground(const FVector& P)const
{
 FCollisionQueryParams Q(TEXT("MareSport"),true);   // i18n:skip
 for(const auto& Pl:Players)if(Pl.Person.IsValid())Q.AddIgnoredActor(Pl.Person.Get());
 for(const auto& A:Props)if(A.IsValid())Q.AddIgnoredActor(A.Get());
 if(auto Hero=UGameplayStatics::GetPlayerPawn(this,0))Q.AddIgnoredActor(Hero);
 FHitResult Hit;const FVector Top(P.X,P.Y,Centre.Z+350);
 return GetWorld()->LineTraceSingleByChannel(Hit,Top,Top-FVector(0,0,800),ECC_Visibility,Q)?Hit.ImpactPoint.Z:Centre.Z;
}

bool UMareBeachSportsWorld::HeroNear(float Radius)const
{
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);return Hero && FVector::Dist2D(Hero->GetActorLocation(),Centre)<Radius;
}
bool UMareBeachSportsWorld::HeroOnCourt()const
{
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);if(!Hero)return false;
 const FVector L=Hero->GetActorLocation();return FMath::Abs(AlongOf(L))<HalfL+150 && FMath::Abs(AcrossOf(L))<HalfW+150;
}

int32 UMareBeachSportsWorld::Nearest(const FVector& P,int32 Team,int32 Not)const
{
 int32 Best=-1;float BestD=1e12f;
 for(int32 I=0;I<Players.Num();++I){if(I==Not || (Team>=0 && Players[I].Team!=Team))continue;
  const float D=FVector::DistSquared2D(Players[I].Pos,P);if(D<BestD){BestD=D;Best=I;}}
 return Best;
}
int32 UMareBeachSportsWorld::Mate(int32 I)const{return I^1;}   // 0-1 and 2-3 are the pairs

FVector UMareBeachSportsWorld::HandPoint(int32 I)const
{
 const FPlayer& P=Players[I];const FVector F=FRotator(0,P.Yaw,0).Vector();
 if(P.Person.IsValid() && P.Person->GetMesh()->GetBoneIndex(TEXT("hand_r"))!=INDEX_NONE)return P.Person->GetMesh()->GetSocketLocation(TEXT("hand_r"))+F*7-FVector(0,0,9);   // i18n:skip
 return P.Pos+F*25+FVector(0,0,85);
}

FVector UMareBeachSportsWorld::Contact(const FVector& Stand,const FVector& Toward,ETouch Touch,float ExtraUp)const
{
 const FVector F=(Toward-Stand).GetSafeNormal2D();const FVector2D T=TouchPoint(Touch);
 return FVector(Stand.X,Stand.Y,Ground(Stand))+F*T.X+FVector(0,0,(FootTouch(Touch)?BallRadius[int32(Sport)]:T.Y)+ExtraUp);
}
void UMareBeachSportsWorld::Meet(int32 I,const FVector& Stand,float Seconds)
{
 if(!Players.IsValidIndex(I))return;
 Players[I].Target=Stand;Players[I].ArriveIn=FMath::Max(Seconds*.85f,.1f);
}

AStaticMeshActor* UMareBeachSportsWorld::Prop(const TCHAR* Slug,const FVector& Where,float Yaw,bool bMovable)
{
 static TSharedPtr<FJsonObject> Catalog;
 if(!Catalog.IsValid()){FString Text;Catalog=MakeShared<FJsonObject>();
  if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/custom_assets.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Catalog);   // i18n:skip
  if(!Catalog.IsValid())Catalog=MakeShared<FJsonObject>();}
 const FString Key=UMareSimulation::String(UMareSimulation::Object(Defs(),TEXT("props")),Slug);FString Path;   // i18n:skip
 if(Key.IsEmpty() || !Catalog->TryGetStringField(Key,Path))return nullptr;
 UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,*Path);if(!Mesh)return nullptr;
 FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto A=GetWorld()->SpawnActor<AStaticMeshActor>(Where,FRotator(0,Yaw,0),SP);if(!A)return nullptr;
 auto C=A->GetStaticMeshComponent();C->SetMobility(EComponentMobility::Movable);C->SetStaticMesh(Mesh);
 C->SetCollisionEnabled(ECollisionEnabled::NoCollision);(void)bMovable;
 A->Tags.Add(TEXT("MareSportProp"));Props.Add(A);return A;   // i18n:skip
}

bool UMareBeachSportsWorld::Begin(ESport Wanted)
{
 ClearAll();
 const auto D=Defs();const TArray<TSharedPtr<FJsonValue>>* C=nullptr;const TArray<TSharedPtr<FJsonValue>>* H=nullptr;
 if(!D->TryGetArrayField(TEXT("court"),C) || C->Num()<3)return false;   // i18n:skip
 Centre=FVector((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),(*C)[2]->AsNumber());CourtYaw=Num(D,TEXT("yaw"));   // i18n:skip
 if(D->TryGetArrayField(TEXT("half"),H) && H->Num()>=2){HalfL=(*H)[0]->AsNumber();HalfW=(*H)[1]->AsNumber();}   // i18n:skip
 Centre.Z=Ground(Centre);Sport=Wanted;
 TArray<FVector2D> Homes;const TCHAR* BallSlug=TEXT("volleyball");   // i18n:skip
 switch(Wanted){
 case ESport::Volley:{
  Homes={FVector2D(-330,-165),FVector2D(-330,165),FVector2D(330,165),FVector2D(330,-165)};
  // the net model runs along its own X: across the court
  if(AStaticMeshActor* Net=Prop(TEXT("net"),At(0,0),CourtYaw+90,false)){   // i18n:skip
   // nobody walks through the net (pawns only: aim traces pass)
   auto Box=NewObject<UBoxComponent>(Net);Box->SetupAttachment(Net->GetRootComponent());Box->SetBoxExtent(FVector(465,8,125));Box->SetRelativeLocation(FVector(0,0,125));
   Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Box->SetCollisionObjectType(ECC_WorldStatic);
   Box->SetCollisionResponseToAllChannels(ECR_Ignore);Box->SetCollisionResponseToChannel(ECC_Pawn,ECR_Block);Box->RegisterComponent();}
  break;}
 case ESport::Peteca:Homes={FVector2D(0,255),FVector2D(-225,-130),FVector2D(225,-130)};BallSlug=TEXT("peteca");break;   // i18n:skip
 case ESport::Soccer:
  Homes={FVector2D(-300,-140),FVector2D(-130,170),FVector2D(300,140),FVector2D(130,-170)};BallSlug=TEXT("soccer_ball");   // i18n:skip
  Prop(TEXT("goal"),At(-HalfL,0),CourtYaw,false);Prop(TEXT("goal"),At(HalfL,0),CourtYaw+180,false);   // i18n:skip
  break;
 default:Sport=ESport::None;return false;}
 BallPos=At(0,0,BallRadius[int32(Wanted)]);
 Ball=Prop(BallSlug,BallPos,0,true);
 if(Wanted==ESport::Peteca && Ball.IsValid())Ball->SetActorScale3D(FVector(1.4f));   // a little larger than life: it has to read from across the sand
 // Different people on the court (the automatic pick by id gave the same MetaHuman twice): the swimwear builds of the
 // beach roster, one per person, shuffled by the day.
 TArray<FString> Roster;
 {static TSharedPtr<FJsonObject> Meta;
  if(!Meta.IsValid()){FString Text;Meta=MakeShared<FJsonObject>();
   if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/metahumans.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Meta);   // i18n:skip
   if(!Meta.IsValid())Meta=MakeShared<FJsonObject>();}
  const TArray<TSharedPtr<FJsonValue>>* Beach=nullptr;TSet<FString> Seen;
  if(Meta->TryGetArrayField(TEXT("beach"),Beach))for(const auto& V:*Beach){const FString Name=V->AsString();   // i18n:skip
   if(!Name.EndsWith(TEXT("_Swim")) || Seen.Contains(Name))continue;Seen.Add(Name);Roster.Add(Name);}   // i18n:skip
  int32 Day=1;if(auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>())if(Sim->State.IsValid())Day=int32(UMareSimulation::Number(Sim->State,TEXT("day"),1));   // i18n:skip
  FRandomStream Mix(Day*31+int32(Wanted));for(int32 I=Roster.Num()-1;I>0;--I)Roster.Swap(I,Mix.RandRange(0,I));}
 for(int32 I=0;I<Homes.Num();++I){
  FPlayer P;P.Home=At(Homes[I].X,Homes[I].Y);P.Pos=P.Target=P.Home;P.GroundZ=P.Home.Z;
  P.Team=Wanted==ESport::Peteca?I:(I<2?0:1);P.Yaw=(Centre-P.Home).Rotation().Yaw;
  FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  AMarePerson* Person=GetWorld()->SpawnActor<AMarePerson>(P.Home+FVector(0,0,88),FRotator(0,P.Yaw,0),SP);if(!Person)continue;
  Person->SaveId=FString::Printf(TEXT("sport%d_%d"),int32(Wanted),I);Person->PersonName=TEXT("Banhista");Person->SetAppearance(I%4);   // i18n:skip
  Person->bAmbient=true;Person->Tags.Add(TEXT("MareBather"));Person->Tags.Add(TEXT("MareSportPlayer"));   // i18n:skip
  Person->GetCharacterMovement()->DisableMovement();Person->HoldPose=TEXT("Idle");Person->HandGoalSpeed=16.f;Person->bHandGoalsHeld=true;   // i18n:skip
  if(Roster.IsValidIndex(I)){Person->MetaRole=TEXT("beach");Person->SetMetaHuman(Roster[I]);}   // i18n:skip
  P.Person=Person;Players.Add(P);Drive(Person);}
 // The ball lies on the sand: once the MetaHumans are dressed somebody picks it up and the game starts.
 Phase=EPhase::Dead;Wait=4.f;
 Holder=Receiver=LastHitter=-1;Rally=0;Side=0;
 return Players.Num()>0;
}

void UMareBeachSportsWorld::Drive(AMarePerson* Person)
{
 TWeakObjectPtr<UMareBeachSportsWorld> Self(this);TWeakObjectPtr<AMarePerson> Who(Person);
 Person->PreTick=[Self,Who](float DeltaSeconds){
  if(!Self.IsValid() || !Who.IsValid())return;
  for(int32 I=0;I<Self->Players.Num();++I)if(Self->Players[I].Person==Who){Self->StepPlayer(I,FMath::Min(DeltaSeconds,.1f));return;}};
}

void UMareBeachSportsWorld::StepPlayer(int32 I,float Dt)
{
 FPlayer& P=Players[I];AMarePerson* Person=P.Person.Get();if(!Person)return;
 if((P.GroundIn-=Dt)<=0){P.GroundIn=.3f;P.GroundZ=Ground(P.Pos);}
 FVector Delta=P.Target-P.Pos;Delta.Z=0;const float Dist=Delta.Size();float Speed=0;
 if(P.Busy>0){P.Busy-=Dt;P.bMoving=false;if(P.Busy<=0)P.bCrouch=false;}
 else if(Dist>(P.bMoving?6.f:24.f)){
  // Fast enough to be there on time, between a walk and a run; each has its clip (no gliding in the idle pose).
  Speed=FMath::Clamp(P.ArriveIn>.05f?Dist/P.ArriveIn:230.f,130.f,440.f);
  P.Pos+=Delta/Dist*FMath::Min(Dist,Speed*Dt);P.bMoving=true;}
 else P.bMoving=false;
 if(P.ArriveIn>0)P.ArriveIn-=Dt;
 // Nobody runs into anybody: pushed apart below 80 cm.
 for(int32 J=0;J<Players.Num();++J){if(J==I)continue;FVector Away=P.Pos-Players[J].Pos;Away.Z=0;const float D=Away.Size();
  if(D<80.f)P.Pos+=(D>1.f?Away/D:FVector(I<J?1.f:-1.f,0,0))*FMath::Min(80.f-D,160.f*Dt);}
 P.Pos.Z=P.GroundZ;
 // Facing: where they run when it is far, else the ball; whoever holds it looks at the play.
 FVector Look=BallPos-P.Pos;
 if(P.bMoving && Dist>80)Look=Delta;
 else if(I==Holder && (Phase==EPhase::Hold || Phase==EPhase::Windup))Look=(Sport==ESport::Soccer?At((P.Team==0?1.f:-1.f)*HalfL,0):Centre)-P.Pos;
 Look.Z=0;
 if(Look.SizeSquared()>100)P.Yaw=FMath::RInterpTo(FRotator(0,P.Yaw,0),FRotator(0,Look.Rotation().Yaw,0),Dt,9.f).Yaw;
 // Jump of the attack: starts a little before the ball arrives.
 const float Left=Duration-FlightT;
 if(Phase==EPhase::Flight && I==Receiver && NextTouch==ETouch::Attack && Left<=.30f && Left>.08f && P.Hop<=0){P.Hop=P.HopTotal=.58f;}
 float Up=0;if(P.Hop>0){P.Hop-=Dt;const float S=FMath::Clamp(1-P.Hop/P.HopTotal,0.f,1.f);Up=4*46.f*S*(1-S);}
 Person->SetActorLocationAndRotation(P.Pos+FVector(0,0,88+Up),FRotator(0,P.Yaw,0),false,nullptr,ETeleportType::TeleportPhysics);
 if(P.Busy<=0)P.bCrouch=false;   // the deep crouch only to pick the ball up from the sand
 // Bump: a half squat with the torso forward, ready a moment before the ball and held through the touch.
 {const bool bBump=Sport==ESport::Volley && !P.bMoving && P.Hop<=0 && ((Phase==EPhase::Flight && I==Receiver && NextTouch==ETouch::Bump) || (P.Reach>0 && P.Touch==ETouch::Bump));
  const bool bLow=bBump && (Left<=.45f || P.Reach>0);
  Person->Squat=bLow?24.f:bBump?10.f:0.f;Person->Lean=bLow?26.f:bBump?10.f:0.f;}
 Person->HoldPose=P.Hop>0?TEXT("Jump"):P.bMoving?(Speed>240?TEXT("Jog_Fwd"):TEXT("Walk")):P.bCrouch?TEXT("Crouch_Idle"):TEXT("Idle");   // i18n:skip
 // Reaching for the ball: the last moments of its flight, a short follow-through, the wind-up of a serve or a kick.
 bool bReach=P.Reach>0;if(P.Reach>0)P.Reach-=Dt;
 if(Phase==EPhase::Flight && I==Receiver && Left<=.30f)bReach=true;
 if(Phase==EPhase::Windup && I==Holder)bReach=true;
 const FVector F=FRotator(0,P.Yaw,0).Vector(),Rt=FRotationMatrix(FRotator(0,P.Yaw,0)).GetScaledAxis(EAxis::Y);
 const bool bFoot=FootTouch(P.Touch);
 if(bReach && bFoot){Person->FootGoalWeight=1.f;Person->FootGoal=BallPos-F*7+FVector(0,0,-3);Person->KneeGoal=P.Pos+F*48+Rt*12+FVector(0,0,56);}
 else Person->FootGoalWeight=0.f;
 if(bReach && !bFoot){
  const bool bTwo=TwoHands(P.Touch);const float ElbowZ=FMath::Clamp(float(BallPos.Z-P.Pos.Z)-34.f,90.f,180.f);
  Person->bHandGoals=true;Person->HandGoalWeight[0]=1.f;Person->HandGoalWeight[1]=bTwo?1.f:0.f;
  for(int32 Hand=0;Hand<2;++Hand){const float S=Hand==0?1.f:-1.f;
   Person->HandGoal[Hand]=BallPos+Rt*S*(bTwo?7.f:0.f)-F*4-FVector(0,0,P.Touch==ETouch::Bump?6.f:0.f);
   Person->ElbowGoal[Hand]=P.Pos+Rt*S*30+F*14+FVector(0,0,ElbowZ);}
 }
 else{Person->bHandGoals=false;Person->HandGoalWeight[0]=Person->HandGoalWeight[1]=1.f;}
}

void UMareBeachSportsWorld::Launch(const FVector& Target,int32 ToPlayer,float Seconds,float Arc,ETouch Touch,bool bRoll)
{
 From=BallPos;To=Target;Duration=FMath::Max(Seconds,.25f);Apex=Arc;FlightT=0;bGround=bRoll;
 Receiver=ToPlayer;NextTouch=Touch;Phase=EPhase::Flight;Holder=-1;
 if(Players.IsValidIndex(ToPlayer))Players[ToPlayer].Touch=Touch;
}

void UMareBeachSportsWorld::StepBall(float Dt)
{
 const float R=BallRadius[int32(Sport)];const FVector Prev=BallPos;
 if(Phase==EPhase::Flight){
  FlightT+=Dt;const float S=FMath::Clamp(FlightT/Duration,0.f,1.f);
  if(bGround)BallPos=FMath::Lerp(From,To,1-FMath::Square(1-S));   // a rolling pass slows down
  else{BallPos=FMath::Lerp(From,To,S);BallPos.Z+=4*Apex*S*(1-S);}
  if(bQAFreeze && Players.IsValidIndex(Receiver) && Duration-FlightT<=.035f){bQAFreeze=false;const FPlayer& Q=Players[Receiver];
   UGameplayStatics::SetGlobalTimeDilation(this,.0001f);
   UE_LOG(LogTemp,Display,TEXT("MARE_SPORT_FREEZE touch=%d player=%d at=%.0f,%.0f,%.0f yaw=%.0f ball=%.0f,%.0f,%.0f"),int32(NextTouch),Receiver,Q.Pos.X,Q.Pos.Y,Q.Pos.Z,Q.Yaw,BallPos.X,BallPos.Y,BallPos.Z);}   // i18n:skip
  if(S>=1)Arrived();
 }
 else if((Phase==EPhase::Hold || Phase==EPhase::Windup) && Players.IsValidIndex(Holder)){
  const FPlayer& P=Players[Holder];const FVector F=FRotator(0,P.Yaw,0).Vector();
  if(Sport==ESport::Soccer)BallPos=P.Pos+F*44+FVector(0,0,R);                       // at the feet
  else if(Phase==EPhase::Windup){const float S=1-FMath::Clamp(Wait/.45f,0.f,1.f);   // tossed up in front and struck
   BallPos=P.Pos+F*36+FVector(0,0,(Sport==ESport::Peteca?105.f:120.f)+(Sport==ESport::Peteca?45.f:95.f)*FMath::Sin(S*UE_HALF_PI));}
  else BallPos=HandPoint(Holder);
 }
 if(AStaticMeshActor* B=Ball.Get()){
  const FVector Move=BallPos-Prev;FRotator Rot=B->GetActorRotation();
  if(Sport==ESport::Peteca){
   // the base leads, the feathers trail; upright in the hand, on its side on the sand
   if(Phase==EPhase::Flight && Move.SizeSquared()>.01f)Rot=FRotationMatrix::MakeFromZ(-Move.GetSafeNormal()).Rotator();
   else if(Phase==EPhase::Hold || Phase==EPhase::Windup)Rot=FRotator::ZeroRotator;
   else Rot=FRotator(-78,Rot.Yaw,0);}
  else if(Move.SizeSquared()>.01f){
   const FVector Axis=FVector::CrossProduct(FVector::UpVector,Move).GetSafeNormal();
   if(!Axis.IsNearlyZero())Rot=(FQuat(Axis,Move.Size()/FMath::Max(R,1.f))*Rot.Quaternion()).GetNormalized().Rotator();}
  B->SetActorLocationAndRotation(BallPos,Rot);
 }
}

void UMareBeachSportsWorld::Arrived()
{
 BallPos=To;
 if(!Players.IsValidIndex(Receiver)){   // on the sand, or in a goal
  if(bRebound){bRebound=false;Phase=EPhase::Dead;Wait=1.2f;return;}   // rolled back out of the net
  Phase=EPhase::Dead;Wait=1.5f;int32 Winner=-1;
  if(Sport==ESport::Volley){Winner=AlongOf(BallPos)<0?1:0;++Points[Winner];}
  else if(Sport==ESport::Soccer && bGoal && Players.IsValidIndex(LastHitter))Winner=Players[LastHitter].Team;
  if(Winner>=0)for(auto& P:Players)if(P.Team==Winner && P.Person.IsValid()){P.Person->PlayGesture(TEXT("Cheer"),2.6f);P.Busy=2.6f;P.Target=P.Pos;}   // i18n:skip
  if(Sport==ESport::Soccer && bGoal){
   // The goal is 1.1 m high: nobody walks into it for the ball. It hits the net and rolls back out in front of the line.
   const float GoalSide=AlongOf(BallPos)<0?-1.f:1.f;FVector Out=At(GoalSide*(HalfL-95),AcrossOf(BallPos)*.6f);Out.Z+=BallRadius[3];
   From=BallPos;To=Out;Duration=.9f;Apex=0;FlightT=0;bGround=true;Receiver=-1;Phase=EPhase::Flight;bRebound=true;}
  Rally=0;return;}
 const int32 R=Receiver;const ETouch T=NextTouch;Players[R].Reach=.16f;LastHitter=R;
 if(T==ETouch::Catch || T==ETouch::Trap || T==ETouch::Save || HeroOnCourt()){
  // kept: at the feet (soccer) or in the hands
  Holder=R;Receiver=-1;Phase=EPhase::Hold;Wait=Rnd(.5f,1.1f);
  if(Sport==ESport::Soccer){FPlayer& P=Players[R];const float Fwd=P.Team==0?1.f:-1.f;   // a few steps with the ball
   const FVector Go=At(FMath::Clamp(AlongOf(P.Pos)+Fwd*Rnd(60,150),-HalfL+110,HalfL-110),FMath::Clamp(AcrossOf(P.Pos)+Rnd(-130,130),-HalfW+40,HalfW-40));
   P.Target=Go;P.ArriveIn=FVector::Dist2D(P.Pos,Go)/200.f;Positions();}
  return;}
 ++Rally;
 if(Sport==ESport::Volley)VolleyNext(R);else if(Sport==ESport::Peteca)PetecaNext(R);else SoccerNext(R);
}

void UMareBeachSportsWorld::VolleyNext(int32 H)
{
 const FPlayer& P=Players[H];const int32 T=P.Team;const float Own=T==0?-1.f:1.f;const ETouch K=P.Touch;const int32 M=Mate(H);
 if(K==ETouch::Bump){   // first touch: up to the partner by the net
  const FVector Stand=At(Own*Rnd(120,190),Rnd(-110,110));
  Meet(M,Stand,1.25f);Launch(Contact(Stand,P.Pos,ETouch::Set),M,1.25f,170.f,ETouch::Set);}
 else if(K==ETouch::Set){   // second touch: lifted for the attack
  const FVector Stand=At(Own*Rnd(95,135),Rnd(-210,210));
  Meet(M,Stand,1.15f);Launch(Contact(Stand,At(0,AcrossOf(Stand)),ETouch::Attack),M,1.15f,150.f,ETouch::Attack);}
 else{   // serve or attack: over the net
  const bool bAttack=K==ETouch::Attack;
  FVector Land=At(-Own*Rnd(210,HalfL-70),Rnd(-240,240));
  float Seconds=FMath::Max(FVector::Dist2D(BallPos,Land)/(bAttack?1050.f:850.f),.75f);
  const bool bMiss=Rally>=2 && FMath::FRand()<(bAttack?.22f:.08f);
  int32 R=-1;FVector Target=Land+FVector(0,0,BallRadius[1]);
  if(!bMiss){R=Nearest(Land,1-T);
   // within the receiver's reach: a couple of steps, planted before the ball arrives (never still running at the touch)
   const FVector Off=Land-Players[R].Pos;const float Far=Off.Size2D(),Reach=FMath::Min(260.f,300.f*Seconds*.6f);
   if(Far>Reach)Land=At(AlongOf(Players[R].Pos+Off/Far*Reach),AcrossOf(Players[R].Pos+Off/Far*Reach));
   Seconds=FMath::Max(FVector::Dist2D(BallPos,Land)/(bAttack?1050.f:850.f),.75f);
   Meet(R,Land,Seconds*.7f);Target=Contact(Land,BallPos,ETouch::Bump);}
  // the arc must clear the net where the path crosses it
  float Arc=bAttack?Rnd(40,110):Rnd(150,230);
  const float A0=AlongOf(BallPos),A1=AlongOf(Target);
  if(A0*A1<0){const float S=A0/(A0-A1);const float Line=FMath::Lerp(BallPos.Z,Target.Z,S)-Centre.Z;const float Need=NetTop+38.f-Line;
   if(Need>0)Arc=FMath::Max(Arc,Need/FMath::Max(4*S*(1-S),.2f));}
  Launch(Target,R,Seconds,Arc,ETouch::Bump);Side=1-T;}
 Positions();
}

void UMareBeachSportsWorld::PetecaNext(int32 H)
{
 const int32 R=(H+1+FMath::RandRange(0,1))%Players.Num();const FPlayer& Q=Players[R];
 const FVector Stand=Q.Home+FVector(Rnd(-55,55),Rnd(-55,55),0);const float Seconds=Rnd(1.15f,1.5f);
 if(Rally>=3 && FMath::FRand()<.1f){   // falls short
  FVector Short=FMath::Lerp(BallPos,Stand,.62f);Short.Z=Ground(Short)+BallRadius[2];
  Launch(Short,-1,Seconds*.8f,Rnd(120,200),ETouch::Palm);}
 else{Meet(R,Stand,Seconds);Launch(Contact(Stand,Players[H].Pos,ETouch::Palm,Rnd(-25,12)),R,Seconds,Rnd(170,270),ETouch::Palm);}
 Positions();
}

void UMareBeachSportsWorld::SoccerNext(int32 H)
{
 const FPlayer& P=Players[H];const int32 T=P.Team;const float Fwd=T==0?1.f:-1.f;const float R=BallRadius[3];
 const float GoalAt=Fwd*HalfL;const float A=AlongOf(P.Pos);
 bGoal=false;
 if(FMath::Abs(GoalAt-A)<430 && FMath::FRand()<.6f){   // a shot
  const float Across=Rnd(-65,65);const int32 Keeper=Nearest(At(GoalAt,0),1-T);
  if(FMath::FRand()<.55f){   // saved with the foot
   const FVector Stand=At(GoalAt-Fwd*75,Across*.8f);const float Seconds=FMath::Max(FVector::Dist2D(BallPos,Stand)/1150.f,.45f);
   Meet(Keeper,Stand,Seconds*.8f);Launch(Contact(Stand,BallPos,ETouch::Save),Keeper,Seconds,0,ETouch::Save,true);}
  else{FVector In=At(GoalAt+Fwd*40,Across);In.Z+=R;bGoal=true;++Points[T];
   Launch(In,-1,FMath::Max(FVector::Dist2D(BallPos,In)/1250.f,.4f),Rnd(0,45),ETouch::Trap);}
 }
 else{   // a pass along the sand, sometimes cut by the other pair
  const int32 M=Mate(H);
  FVector Stand=Players[M].Pos+FVector(Rnd(-60,60),Rnd(-60,60),0);   // to where the partner already is: he ran free
  Stand=At(FMath::Clamp(AlongOf(Stand),-HalfL+120,HalfL-120),FMath::Clamp(AcrossOf(Stand),-HalfW+40,HalfW-40));
  int32 To2=M;
  if(FMath::FRand()<.22f){const FVector Mid=FMath::Lerp(P.Pos,Stand,.55f);To2=Nearest(Mid,1-T);Stand=FVector(Mid.X,Mid.Y,Ground(Mid));}
  const float Seconds=FMath::Max(FVector::Dist2D(BallPos,Stand)/720.f,.7f);
  Meet(To2,Stand,Seconds);Launch(Contact(Stand,BallPos,ETouch::Trap),To2,Seconds,0,ETouch::Trap,true);}
 Positions();
}

void UMareBeachSportsWorld::Positions()
{
 for(int32 I=0;I<Players.Num();++I){
  if(I==Receiver || I==Holder)continue;FPlayer& P=Players[I];if(P.Busy>0)continue;
  FVector Go=P.Home;float Speed=170.f;
  if(Sport==ESport::Volley){const float Own=P.Team==0?-1.f:1.f;
   if(Phase==EPhase::Flight && Side==P.Team){Speed=260.f;
    if(NextTouch==ETouch::Bump)Go=At(Own*170,AcrossOf(P.Home)*.4f);         // the partner gets ready to set
    else if(NextTouch==ETouch::Set)Go=At(Own*150,AcrossOf(P.Pos));          // the passer comes up for the attack
    else Go=At(Own*280,AcrossOf(P.Home));}                                  // cover behind the attacker
  }
  else if(Sport==ESport::Soccer){const int32 Has=Players.IsValidIndex(Holder)?Holder:Receiver;
   if(Players.IsValidIndex(Has)){const FPlayer& B=Players[Has];const float Fwd=B.Team==0?1.f:-1.f;Speed=300.f;
    if(P.Team==B.Team)Go=At(FMath::Clamp(AlongOf(B.Pos)+Fwd*Rnd(150,300),-HalfL+120,HalfL-120),FMath::Clamp((AcrossOf(B.Pos)>0?-1.f:1.f)*Rnd(140,260),-HalfW+40,HalfW-40));
    else if(I==Nearest(B.Pos,P.Team)){const FVector Goal=At(Fwd*HalfL,0);Go=B.Pos+(Goal-B.Pos).GetSafeNormal2D()*300.f;}   // marks, between the ball and the goal
    else Go=At(Fwd*(HalfL-110),AcrossOf(B.Pos)*.25f);}                       // guards the goal
  }
  // nobody stands inside somebody else
  for(int32 J=0;J<Players.Num();++J)if(J!=I && FVector::Dist2D(Players[J].Target,Go)<85){const FVector Away=(Go-Players[J].Target).GetSafeNormal2D();Go+=(Away.IsNearlyZero()?FVector(1,0,0):Away)*90.f;}
  P.Target=Go;P.ArriveIn=FVector::Dist2D(P.Pos,Go)/Speed;
 }
}

void UMareBeachSportsWorld::Decide(float Dt)
{
 if(Sport==ESport::Soccer && (Repos-=Dt)<=0){Repos=1.f;if(Phase==EPhase::Hold)Positions();}
 switch(Phase){
 case EPhase::Rest:
  if((Wait-=Dt)<=0 && Players.Num()){   // first serve / kick-off
   Holder=0;Phase=EPhase::Hold;Wait=1.2f;Touches=0;
   if(Sport==ESport::Volley){FPlayer& S=Players[0];S.Target=At(-HalfL+60,120);S.ArriveIn=FVector::Dist2D(S.Pos,S.Target)/170.f;}
   else if(Sport==ESport::Soccer){FPlayer& S=Players[0];S.Target=At(-40,0);S.ArriveIn=FVector::Dist2D(S.Pos,S.Target)/200.f;}}
  break;
 case EPhase::Hold:
  if(Players.IsValidIndex(Holder)){FPlayer& H=Players[Holder];
   if(HeroOnCourt()){H.Target=H.Pos;break;}                 // somebody walked in: wait
   if(H.bMoving && Sport!=ESport::Soccer)break;             // still carrying the ball back
   if((Wait-=Dt)<=0){Phase=EPhase::Windup;Wait=Sport==ESport::Soccer?.28f:.45f;H.Target=H.Pos;
    H.Touch=Sport==ESport::Soccer?ETouch::Kick:Sport==ESport::Peteca?ETouch::Palm:ETouch::Serve;}}
  break;
 case EPhase::Windup:
  if((Wait-=Dt)<=0 && Players.IsValidIndex(Holder)){const int32 H=Holder;Players[H].Reach=.16f;LastHitter=H;
   if(Sport==ESport::Volley)VolleyNext(H);else if(Sport==ESport::Peteca)PetecaNext(H);else SoccerNext(H);}
  break;
 case EPhase::Dead:
  if((Wait-=Dt)<=0){   // somebody goes for the ball
   int32 F=Nearest(BallPos);
   if(Sport==ESport::Volley)F=Nearest(BallPos,AlongOf(BallPos)<0?0:1);
   else if(Sport==ESport::Soccer && bGoal && Players.IsValidIndex(LastHitter))F=Nearest(BallPos,1-Players[LastHitter].Team);
   if(!Players.IsValidIndex(F))break;
   FPlayer& P=Players[F];const FVector Off=(BallPos-P.Pos).GetSafeNormal2D()*(Sport==ESport::Soccer?44.f:48.f);
   P.Target=FVector(BallPos.X-Off.X,BallPos.Y-Off.Y,P.Pos.Z);P.ArriveIn=FVector::Dist2D(P.Pos,P.Target)/300.f;P.Busy=0;
   Holder=F;Phase=EPhase::Fetch;bPicked=false;Positions();}
  break;
 case EPhase::Fetch:
  if(Players.IsValidIndex(Holder)){FPlayer& F=Players[Holder];
   if(F.bMoving || FVector::Dist2D(F.Pos,F.Target)>30)break;
   if(Sport==ESport::Soccer){Phase=EPhase::Hold;Wait=.5f;bGoal=false;Positions();break;}
   if(!bPicked){bPicked=true;F.Busy=.9f;F.bCrouch=true;F.Reach=.9f;F.Touch=ETouch::Catch;break;}   // crouches and takes it with both hands
   if(F.Busy>0)break;
   bPicked=false;Phase=EPhase::Hold;Wait=1.f;Touches=0;
   F.Target=Sport==ESport::Volley?At((F.Team==0?-1.f:1.f)*(HalfL-60),Rnd(-150,150)):F.Home;F.ArriveIn=FVector::Dist2D(F.Pos,F.Target)/170.f;
   F.bMoving=true;Positions();}
  break;
 default:break;}
}

void UMareBeachSportsWorld::Tick(float DeltaSeconds)
{
 UWorld* W=GetWorld();
 if(!W || !W->IsGameWorld() || !W->GetGameInstance() || !Cast<AMareGameMode>(W->GetAuthGameMode()) || UGameplayStatics::IsGamePaused(this))return;
 const float Dt=FMath::Min(DeltaSeconds,.1f);
 if(!bDefsRead){bDefsRead=true;const TArray<TSharedPtr<FJsonValue>>* C=nullptr;
  if(Defs()->TryGetArrayField(TEXT("court"),C) && C->Num()>=3)Centre=FVector((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),(*C)[2]->AsNumber());}   // i18n:skip
 if((Clock-=Dt)<=0){Clock=1.f;
  ESport Want=ESport::None;bool bLate=false;
  if(Forced>=0)Want=ESport(FMath::Clamp(Forced,0,3));
  else if(auto Sim=W->GetGameInstance()->GetSubsystem<UMareSimulation>()){
   const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;
   if(Sim->State.IsValid() && Defs()->TryGetArrayField(TEXT("hours"),Hours) && Hours->Num()==2){   // i18n:skip
    const double Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.;   // i18n:skip
    // Same weather rule as the sunbathers: the QA override first, then today's weather.
    const auto Weather=IConsoleManager::Get().FindConsoleVariable(TEXT("mare.Weather"));const int32 Sky=Weather?Weather->GetInt():0;   // i18n:skip
    const bool bRain=Sky==2 || Sky==3 || (Sky==0 && UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain"));   // i18n:skip
    const double Start=(*Hours)[0]->AsNumber(),End=(*Hours)[1]->AsNumber();
    if(!bRain && Hour>=Start && Hour<End)Want=SportOfDay(int32(UMareSimulation::Number(Sim->State,TEXT("day"),1)));   // i18n:skip
    bLate=bRain || Hour>=End+1 || Hour<Start-1;}}
  // Nobody pops in or out in front of the player: only far away, in the first seconds of the session, or an hour late.
  const bool bFree=Forced>=0 || W->GetTimeSeconds()<10 || !HeroNear(Num(Defs(),TEXT("unseen"),3500));   // i18n:skip
  if(Want!=Sport && (bFree || (Want==ESport::None && bLate))){if(Want==ESport::None)ClearAll();else Begin(Want);}
 }
 if(Sport==ESport::None)return;
 for(const auto& P:Players)if(!P.Person.IsValid()){ClearAll();return;}
 StepBall(Dt);Decide(Dt);
}

FString UMareBeachSportsWorld::Dump()const
{
 FString Out=FString::Printf(TEXT("sport=%s phase=%d rally=%d points=%d-%d holder=%d receiver=%d ball=(%.0f,%.0f,%.0f)"),SportName(Sport),int32(Phase),Rally,Points[0],Points[1],Holder,Receiver,BallPos.X,BallPos.Y,BallPos.Z);   // i18n:skip
 for(int32 I=0;I<Players.Num();++I){const FPlayer& P=Players[I];
  Out+=FString::Printf(TEXT(" p%d[t%d (%.0f,%.0f) %s%s]"),I,P.Team,P.Pos.X,P.Pos.Y,P.bMoving?TEXT("moving"):TEXT("still"),P.Person.IsValid()?*(TEXT(" ")+P.Person->MetaHuman):TEXT(" gone"));}   // i18n:skip
 return Out;
}

static FAutoConsoleCommandWithWorldAndArgs GMareSport(TEXT("mare.Sport"),TEXT("mare.Sport <volei|peteca|futebol|auto|clear|dump|hold|go>: QA of the beach sports (beach_sports.json)."),   // i18n:skip
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(!World)return;auto Sub=World->GetSubsystem<UMareBeachSportsWorld>();if(!Sub)return;const FString A=Args.Num()?Args[0]:TEXT("dump");   // i18n:skip
  if(A==TEXT("clear")){Sub->ClearAll();Sub->Forced=0;}   // i18n:skip
  else if(A==TEXT("auto"))Sub->Forced=-1;   // i18n:skip
  else if(A==TEXT("hold"))Sub->bQAFreeze=true;   // i18n:skip
  else if(A==TEXT("go")){Sub->bQAFreeze=false;UGameplayStatics::SetGlobalTimeDilation(World,1.f);}   // i18n:skip
  else if(A==TEXT("volei"))Sub->Forced=1;else if(A==TEXT("peteca"))Sub->Forced=2;else if(A==TEXT("futebol"))Sub->Forced=3;   // i18n:skip
  UE_LOG(LogTemp,Display,TEXT("MARE_SPORT forced=%d %s"),Sub->Forced,*Sub->Dump());}));   // i18n:skip
