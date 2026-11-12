// Lighthouse trail on foot (CHECKLIST_EXPANSOES 2.4). Values in Content/Data/tours.json "trail_tour"; the rating
// goes through MareSimulation::TrailScore (stop choices and bonus) and GuideTour, like the other guided tours.
#include "MareTrailWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "AIController.h"
#include "NavigationSystem.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"

namespace
{
 UMareSimulation* SimOf(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 FVector Vec(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O.IsValid() || !O->TryGetArrayField(Key,A) || A->Num()<2)return FVector::ZeroVector;
  return FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),A->Num()>2?(*A)[2]->AsNumber():0);
 }
 TArray<TSharedPtr<FJsonValue>> Views(const TSharedPtr<FJsonObject>& D)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;return D.IsValid() && D->TryGetArrayField(TEXT("mirantes"),A)?*A:TArray<TSharedPtr<FJsonValue>>();
 }
}

TStatId UMareTrailWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareTrailWorld,STATGROUP_Tickables);}
TSharedPtr<FJsonObject> UMareTrailWorld::Defs()const
{
 auto S=SimOf(GetWorld());return S?UMareSimulation::Object(S->ToursDefs(),TEXT("trail_tour")):MakeShared<FJsonObject>();
}
FString UMareTrailWorld::Line(const FString& Key)const{return UMareSimulation::String(UMareSimulation::Object(Defs(),TEXT("lines")),Key);}
FVector UMareTrailWorld::Viewpoint(int32 I)const{const auto V=Views(Defs());return V.IsValidIndex(I)?Vec(V[I]->AsObject(),TEXT("at")):Vec(Defs(),TEXT("lighthouse"));}
int32 UMareTrailWorld::ViewpointCount()const{return Views(Defs()).Num();}
double UMareTrailWorld::Hour()const{auto S=SimOf(GetWorld());return S?UMareSimulation::Number(S->State,TEXT("minutes"))/60.:12.;}
int32 UMareTrailWorld::AtViewpoint()const
{
 auto Hero=PC.IsValid()?PC->GetPawn():nullptr;if(!Hero)return -1;const float R=UMareSimulation::Number(Defs(),TEXT("radius"),450);
 for(int32 I=0;I<ViewpointCount();++I)if(FVector::Dist2D(Hero->GetActorLocation(),Viewpoint(I))<R)return I;
 return -1;
}

void UMareTrailWorld::Deinitialize()
{
 auto Kill=[](auto& List){for(auto& A:List)if(IsValid(A))A->Destroy();List.Empty();};
 Kill(Walkers);Kill(WaterTargets);Kill(StoryTargets);Bottles.Empty();
 for(auto& Pair:Leaving)if(Pair.Key.IsValid())Pair.Key->Destroy();Leaving.Empty();
 Super::Deinitialize();
}

bool UMareTrailWorld::Start(APlayerController* Controller)
{
 auto S=SimOf(GetWorld());if(!S || IsActive() || !Controller || !Controller->GetPawn())return false;
 const auto D=Defs();TourId=UMareSimulation::String(D,TEXT("tour"));
 if(!UMareSimulation::String(UMareSimulation::Object(S->State,TEXT("tours")),TEXT("active")).IsEmpty()){S->LastMessage=TEXT("Já tem um passeio em andamento.");return false;}
 if(!S->IsTourBoarding(TourId)){S->LastMessage=TEXT("Só dá para guiar na hora da saída.");return false;}
 const int32 Sold=S->TourCount(TEXT("sold"),TourId);
 if(Sold<=0){S->LastMessage=TEXT("Nenhum bilhete vendido para este passeio.");return false;}
 PC=Controller;Time=WaitMinutes=SunsetMinutes=FollowClock=0;Complaints=Stories=0;bLeftStart=bArrived=bSunset=bLate=bFollowing=false;FollowTime=0;Says.Reset();LastPos=Heading2D=FVector::ZeroVector;
 const FVector Start=Vec(D,TEXT("start"));const int32 N=FMath::Min(Sold,5);
 Watered.Init(false,N);LagClock.Init(0,N);Photographed.Init(false,ViewpointCount());Told.Init(false,ViewpointCount());
 // The group waits in a half circle at the start of the trail, facing the guide.
 const FVector Hero=Controller->GetPawn()->GetActorLocation();const FVector Face=(Hero-Start).GetSafeNormal2D().IsNearlyZero()?FVector(1,0,0):(Hero-Start).GetSafeNormal2D();
 auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
 for(int32 I=0;I<N;++I){FVector At=Start+Face.RotateAngleAxis(-60.f+30.f*I,FVector::UpVector)*-120.f;
  // On the walkable sand (never on the pier deck or a boat): the navmesh point nearest to the slot.
  FNavLocation OnNav;if(Nav && Nav->ProjectPointToNavigation(At,OnNav,FVector(300,300,400)))At=OnNav.Location;
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
  auto P=GetWorld()->SpawnActor<AMarePerson>(At+FVector(0,0,90),Face.Rotation(),Params);if(!P)continue;
  P->SaveId=FString::Printf(TEXT("trail_%d"),I);P->PersonName=TEXT("Turista");P->SetAppearance(FCrc::StrCrc32(*P->SaveId)%4);P->bAmbient=true;
  P->GetCharacterMovement()->MaxWalkSpeed=UMareSimulation::Number(D,TEXT("speed"),240);Walkers.Add(P);
  auto T=GetWorld()->SpawnActor<AMareServiceTarget>(At+FVector(0,0,60),FRotator::ZeroRotator);
  if(T){T->Action=TEXT("TrailWater");T->DataIndex=Walkers.Num()-1;T->Label=TEXT("Entregar água e protetor solar");T->Reach=300;T->OcclusionTolerance=60;
   T->AttachToActor(P,FAttachmentTransformRules::KeepWorldTransform);}
  WaterTargets.Add(T);}
 Watered.SetNum(Walkers.Num());LagClock.SetNum(Walkers.Num());
 // A sign at each viewpoint: E tells the lighthouse story there.
 for(int32 I=0;I<ViewpointCount();++I){auto T=GetWorld()->SpawnActor<AMareServiceTarget>(Viewpoint(I)+FVector(0,0,110),FRotator::ZeroRotator);
  if(T){T->Action=TEXT("TrailStory");T->DataIndex=I;T->Label=TEXT("Contar a história do farol");T->Reach=500;T->OcclusionTolerance=200;}StoryTargets.Add(T);}
 UMareSimulation::Object(S->State,TEXT("tours"))->SetStringField(TEXT("active"),TourId);
 const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;FString First;
 if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->Num())First=UMareSimulation::String((*Stops)[0]->AsObject(),TEXT("text"))+TEXT(" ");
 S->LastMessage=First+Line(TEXT("start"));
 UMareAudioWorld::Action(this,TEXT("reception_bell"));
 return true;
}

void UMareTrailWorld::Say(int32 Walker,const FString& Text,float Seconds){if(Walkers.IsValidIndex(Walker))Says.Add(Walker,TPair<FString,float>(Text,Time+Seconds));}

void UMareTrailWorld::GiveWater(int32 W)
{
 if(!Watered.IsValidIndex(W) || Watered[W] || bLeftStart)return;Watered[W]=true;
 if(WaterTargets.IsValidIndex(W) && IsValid(WaterTargets[W]))WaterTargets[W]->SetActorHiddenInGame(true);
 // The bottle in the walker's hand (no hands for the hero: it goes straight to them).
 if(auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(Defs(),TEXT("bottle"))))if(Walkers.IsValidIndex(W) && IsValid(Walkers[W]) && Walkers[W]->GetMesh()->DoesSocketExist(TEXT("hand_r"))){
  auto B=NewObject<UStaticMeshComponent>(Walkers[W]);Walkers[W]->AddInstanceComponent(B);B->SetStaticMesh(Mesh);B->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  B->SetupAttachment(Walkers[W]->GetMesh(),TEXT("hand_r"));B->SetRelativeLocation(FVector(0,3,-4));B->SetRelativeRotation(FRotator(0,0,90));B->RegisterComponent();Bottles.Add(B);}
 Say(W,Line(TEXT("thanks")),2.5f);UMareAudioWorld::Action(this,TEXT("cleaning_towels"),nullptr,.4f);
}

void UMareTrailWorld::TellStory(int32 I)
{
 auto S=SimOf(GetWorld());if(!S || !Told.IsValidIndex(I) || Told[I] || bArrived)return;
 auto Hero=PC.IsValid()?PC->GetPawn():nullptr;if(!Hero || FVector::Dist2D(Hero->GetActorLocation(),Viewpoint(I))>UMareSimulation::Number(Defs(),TEXT("radius"),450)*1.5f)return;
 Told[I]=true;++Stories;S->AdvanceMinutes(UMareSimulation::Number(Defs(),TEXT("story_minutes"),12));
 if(StoryTargets.IsValidIndex(I) && IsValid(StoryTargets[I]))StoryTargets[I]->SetActorHiddenInGame(true);
 const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;FString Tale;
 if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->IsValidIndex(1))Tale=TEXT(" (")+UMareSimulation::String((*Stops)[1]->AsObject(),TEXT("good"))+TEXT(")");
 S->LastMessage=Line(TEXT("story"))+Tale+FString::Printf(TEXT(" Agora são %02d:%02d."),int32(Hour()),int32(FMath::Fmod(Hour()*60,60.)));
 for(int32 K=0;K<Walkers.Num();K+=2)Say(K,TEXT("Que história!"),3);UMareAudioWorld::Action(this,TEXT("deal_accept"),nullptr,.4f);
}

void UMareTrailWorld::OnPhoto()
{
 if(!IsActive())return;const int32 I=AtViewpoint();if(I<0 || Photographed[I])return;
 // The group must be there for the group photo.
 int32 Near=0;for(auto& W:Walkers)if(IsValid(W) && FVector::Dist2D(W->GetActorLocation(),Viewpoint(I))<UMareSimulation::Number(Defs(),TEXT("gather_radius"),900))++Near;
 auto S=SimOf(GetWorld());if(Near*2<Walkers.Num()){if(S)S->LastMessage=TEXT("Espere o grupo chegar para a foto.");return;}
 Photographed[I]=true;for(int32 K=1;K<Walkers.Num();K+=2)Say(K,Line(TEXT("photo")),3);
 if(S)S->LastMessage=FString::Printf(TEXT("Foto do grupo no %s!"),*UMareSimulation::String(Views(Defs())[I]->AsObject(),TEXT("name")));
}

void UMareTrailWorld::Finish()
{
 auto S=SimOf(GetWorld());if(!IsActive())return;
 if(S){TArray<int32> Choices;double Bonus=0;int32 Given=0,Shots=0;for(bool B:Watered)Given+=B;for(bool B:Photographed)Shots+=B;
  S->TrailScore(Given,Walkers.Num(),Shots,ViewpointCount(),bSunset,Stories,Complaints,Choices,Bonus);S->GuideTour(TourId,Choices,Bonus);
  UMareSimulation::Object(S->State,TEXT("tours"))->RemoveField(TEXT("active"));if(bSunset)S->LastMessage=Line(TEXT("done"))+TEXT(" ")+S->LastMessage;}
 // The group stays a little longer, then walks back to the beach and goes home.
 const double Now=GetWorld()->GetTimeSeconds();
 for(auto& W:Walkers)if(IsValid(W))Leaving.Add(W.Get(),Now+UMareSimulation::Number(Defs(),TEXT("linger_seconds"),20));Walkers.Empty();
 auto Kill=[](auto& List){for(auto& A:List)if(IsValid(A))A->Destroy();List.Empty();};
 Kill(WaterTargets);Kill(StoryTargets);Bottles.Empty();Says.Reset();
 UMareAudioWorld::Action(this,TEXT("money_coins"));
}

void UMareTrailWorld::Tick(float DeltaSeconds)
{
 auto World=GetWorld();if(!World || !World->IsGameWorld() || World->IsPaused())return;
 auto S=SimOf(World);
 // After the tour: walking home, gone once out of the way.
 {const double Now=World->GetTimeSeconds();for(auto It=Leaving.CreateIterator();It;++It){AMarePerson* P=It.Key().Get();if(!P){It.RemoveCurrent();continue;}
   if(It.Value()>0 && Now>It.Value()){It.Value()=-(Now+40);P->WalkTo(Vec(Defs(),TEXT("start")));}
   else if(It.Value()<0 && Now>-It.Value()){P->Destroy();It.RemoveCurrent();}}}
 // A save made on the trail comes back marked active with nobody walking: clear it.
 if(!IsActive()){if(S){auto T=UMareSimulation::Object(S->State,TEXT("tours"));
   if(!UMareSimulation::String(T,TEXT("active")).IsEmpty() && UMareSimulation::String(T,TEXT("active"))==UMareSimulation::String(Defs(),TEXT("tour")))T->RemoveField(TEXT("active"));}return;}
 Time+=DeltaSeconds;auto Hero=PC.IsValid()?PC->GetPawn():nullptr;if(!Hero || !S)return;const auto D=Defs();
 const FVector H=Hero->GetActorLocation(),Start=Vec(D,TEXT("start")),Light=Vec(D,TEXT("lighthouse"));
 if(!bLeftStart && FVector::Dist2D(H,Start)>UMareSimulation::Number(D,TEXT("start_radius"),1500)){bLeftStart=true;
  for(auto& T:WaterTargets)if(IsValid(T))T->SetActorHiddenInGame(true);}
 // They set off as soon as the guide does; complaints only once they have been walking a while.
 if(!bFollowing && FVector::Dist2D(H,Start)>UMareSimulation::Number(D,TEXT("follow_radius"),350)){bFollowing=true;FollowTime=0;}
 if(bFollowing)FollowTime+=DeltaSeconds;
 // Walking after the guide, two by two (path finding on the navmesh, re-aimed twice a second).
 FollowClock-=DeltaSeconds;const bool bRoute=FollowClock<=0;if(bRoute)FollowClock=.5f;
 // "Behind" is where the guide came from (the trail so far), not where the camera looks: turning round to see the
 // group must not pull it in front of the guide.
 if(LastPos.IsZero())LastPos=Start;if(FVector::Dist2D(H,LastPos)>150){Heading2D=(H-LastPos).GetSafeNormal2D();LastPos=H;}
 const FVector Back=Heading2D.IsNearlyZero()?(Start-H).GetSafeNormal2D():-Heading2D;
 const FVector Side(-Back.Y,Back.X,0);const float Gap=UMareSimulation::Number(D,TEXT("spacing"),130),Lag=UMareSimulation::Number(D,TEXT("lag_distance"),1000);
 for(int32 I=0;I<Walkers.Num();++I){auto P=Walkers[I];if(!IsValid(P))continue;
  // On the trail: two by two behind the guide. At the lighthouse: side by side on the rocks, facing the sunset (west).
  const FVector View=Vec(D,TEXT("sunset_view"));
  const FVector Goal=bArrived?View+FVector(0,(I-(Walkers.Num()-1)*.5f)*Gap,0):H+Back*(Gap*(1.3f+I/2))+Side*((I%2)?1.f:-1.f)*Gap*.5f;
  const float Dist=FVector::Dist2D(P->GetActorLocation(),H);
  if(bRoute && (bFollowing || bArrived)){if(FVector::Dist2D(P->GetActorLocation(),Goal)>90){if(!P->WalkTo(Goal))P->WalkTo(H);}
   else if(auto AI=Cast<AAIController>(P->GetController())){AI->StopMovement();P->SetActorRotation(FRotator(0,bArrived?180.f:(H-P->GetActorLocation()).Rotation().Yaw,0));}}
  // Left behind: a complaint (once in a while each).
  LagClock[I]=FMath::Max(0.f,LagClock[I]-DeltaSeconds);
  if(bFollowing && FollowTime>6 && !bArrived && Dist>Lag && LagClock[I]<=0){LagClock[I]=UMareSimulation::Number(D,TEXT("lag_cooldown"),25);++Complaints;Say(I,Line(TEXT("lag")),3.5f);
   S->LastMessage=TEXT("Um turista ficou para trás: ande mais devagar (sem correr) para o grupo acompanhar.");UMareAudioWorld::Action(this,TEXT("deal_decline"),nullptr,.4f);}}
 // At the lighthouse: the group gathers, then the sunset (or the wait for it, or the miss).
 const float Gather=UMareSimulation::Number(D,TEXT("gather_radius"),900);
 if(!bArrived && FVector::Dist2D(H,Light)<UMareSimulation::Number(D,TEXT("radius"),450)){int32 Near=0;for(auto& W:Walkers)if(IsValid(W) && FVector::Dist2D(W->GetActorLocation(),Light)<Gather*1.5f)++Near;
  if(Near>=Walkers.Num()){bArrived=true;for(auto& T:StoryTargets)if(IsValid(T))T->SetActorHiddenInGame(true);
   const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->IsValidIndex(2))
    S->LastMessage=UMareSimulation::String((*Stops)[2]->AsObject(),TEXT("text"));}}
 if(bArrived){const TArray<TSharedPtr<FJsonValue>>* Win=nullptr;double From=17.25,To=17.95;
  if(D->TryGetArrayField(TEXT("sunset"),Win) && Win->Num()==2){From=(*Win)[0]->AsNumber();To=(*Win)[1]->AsNumber();}
  const double Now=Hour();const float Minutes=DeltaSeconds;   // 1 game minute per real second
  if(Now>To && !bSunset){bLate=true;S->LastMessage=Line(TEXT("late"));Say(0,Line(TEXT("late")),4);Finish();return;}
  if(Now<From){WaitMinutes+=Minutes;if(WaitMinutes>=UMareSimulation::Number(D,TEXT("patience_minutes"),15)){WaitMinutes=0;++Complaints;
    Say(FMath::RandRange(0,Walkers.Num()-1),Line(TEXT("early")),4);S->LastMessage=Line(TEXT("early"))+TEXT(" (o grupo está ficando impaciente)");}}
  else{if(!bSunset){bSunset=true;for(int32 K=0;K<Walkers.Num();++K)Say(K,Line(TEXT("sunset")),5);UMareAudioWorld::Action(this,TEXT("deal_accept"));}
   SunsetMinutes+=Minutes;if(SunsetMinutes>=UMareSimulation::Number(D,TEXT("sunset_watch_minutes"),12)){Finish();return;}}}
 // The guide wandering off for good ends the walk.
 if(FVector::Dist2D(H,Light)>12000 && FVector::Dist2D(H,Start)>12000)Finish();
}

FString UMareTrailWorld::Status()const
{
 if(!IsActive())return FString();const auto D=Defs();int32 Given=0,Shots=0;for(bool B:Watered)Given+=B;for(bool B:Photographed)Shots+=B;
 FString Goal;
 if(!bLeftStart && Given<Walkers.Num())Goal=FString::Printf(TEXT("Água e protetor: %d de %d (E em cada turista)"),Given,Walkers.Num());
 else if(bArrived)Goal=bSunset?Line(TEXT("sunset")):Line(TEXT("early"));
 else{const int32 V=AtViewpoint();if(V>=0 && !Photographed[V])Goal=Line(TEXT("mirante"));
  else{int32 Next=-1;for(int32 I=0;I<Photographed.Num();++I)if(!Photographed[I]){Next=I;break;}
   Goal=Next>=0?TEXT("Siga para o ")+UMareSimulation::String(Views(D)[Next]->AsObject(),TEXT("name")):Line(TEXT("go_lighthouse"));}}
 return FString::Printf(TEXT("Trilha do farol · %02d:%02d · fotos %d de %d · reclamações %d · %s"),int32(Hour()),int32(FMath::Fmod(Hour()*60,60.)),Shots,Photographed.Num(),Complaints,*Goal);
}

TArray<TPair<FVector,FString>> UMareTrailWorld::Bubbles()const
{
 TArray<TPair<FVector,FString>> Out;
 for(const auto& Pair:Says)if(Pair.Value.Value>Time && Walkers.IsValidIndex(Pair.Key) && IsValid(Walkers[Pair.Key]))Out.Add({Walkers[Pair.Key]->GetActorLocation()+FVector(0,0,120),Pair.Value.Key});
 return Out;
}

FString UMareTrailWorld::QA(const FString& Cmd)
{
 auto Hero=PC.IsValid()?Cast<ACharacter>(PC->GetPawn()):nullptr;
 if(Cmd.StartsWith(TEXT("water:"))){GiveWater(FCString::Atoi(*Cmd.Mid(6)));return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("story:"))){TellStory(FCString::Atoi(*Cmd.Mid(6)));return TEXT("ok");}
 if(Cmd==TEXT("photo")){OnPhoto();return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("goto:")) && Hero){const int32 I=FCString::Atoi(*Cmd.Mid(5));const FVector At=I==9?Vec(Defs(),TEXT("lighthouse")):Viewpoint(I);
  bLeftStart=bFollowing=true;FollowTime=0;Hero->SetActorLocation(At+FVector(0,0,100));Hero->GetCharacterMovement()->StopMovementImmediately();
  for(int32 K=0;K<Walkers.Num();++K)if(IsValid(Walkers[K])){if(auto AI=Cast<AAIController>(Walkers[K]->GetController()))AI->StopMovement();
   Walkers[K]->SetActorLocation(At+FVector(-160-60*(K/2),((K%2)?1:-1)*80.f,100),false,nullptr,ETeleportType::TeleportPhysics);}
  return TEXT("ok");}
 if(Cmd==TEXT("finish")){Finish();return TEXT("ok");}
 int32 Given=0,Shots=0;for(bool B:Watered)Given+=B;for(bool B:Photographed)Shots+=B;
 return FString::Printf(TEXT("active=%d walkers=%d water=%d photos=%d stories=%d complaints=%d left=%d arrived=%d sunset=%d late=%d hour=%.2f"),
  IsActive(),Walkers.Num(),Given,Shots,Stories,Complaints,bLeftStart,bArrived,bSunset,bLate,Hour());
}
