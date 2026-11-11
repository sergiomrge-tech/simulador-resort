#include "MareKioskWorld.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "MarePerson.h"
#include "MareServiceTarget.h"
#include "MareSimulation.h"
#include "MareGame.h"
#include "Engine/GameInstance.h"
#include "AIController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "NavigationSystem.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

UMareSimulation* UMareKioskWorld::Sim()const{return GetWorld() && GetWorld()->GetGameInstance()?GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
TStatId UMareKioskWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareKioskWorld,STATGROUP_Tickables);}
FVector UMareKioskWorld::FromGodot(const TArray<TSharedPtr<FJsonValue>>& V,float Height){return V.Num()==3?FVector(V[0]->AsNumber()*100,V[2]->AsNumber()*100,V[1]->AsNumber()*100+Height):FVector::ZeroVector;}
void UMareKioskWorld::Initialize(FSubsystemCollectionBase& Collection)
{
 Super::Initialize(Collection);TearDownHandle=FWorldDelegates::OnWorldBeginTearDown.AddUObject(this,&UMareKioskWorld::BeforeTearDown);FString Text;TSharedPtr<FJsonObject> World;
 FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/world.json")));
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),World))return;
 const TArray<TSharedPtr<FJsonValue>>* Spots=nullptr;if(!World->TryGetArrayField(TEXT("tables"),Spots))return;
 for(int32 I=0;I<Spots->Num();++I){auto Row=(*Spots)[I]->AsObject();const auto& Pos=Row->GetArrayField(TEXT("pos"));
  if(I<2){CounterPoints.Add(FromGodot(Row->GetArrayField(TEXT("approach")),88));CounterStaffPoints.Add(FromGodot(Row->GetArrayField(TEXT("staff_approach")),88));}
  else{TablePoints.Add(FromGodot(Pos,88));TableApproaches.Add(FromGodot(Row->GetArrayField(TEXT("approach")),88));TableYaw.Add(90-FMath::RadiansToDegrees(UMareSimulation::Number(Row,TEXT("rot"))));TableSurfaces.Add(FromGodot(Row->GetArrayField(TEXT("serve_pos"))));}
 }
}
void UMareKioskWorld::SpawnCustomer()
{
 auto S=Sim();if(!S || CounterPoints.Num()<2)return;int32 Counter=INDEX_NONE;
 for(int32 I=0;I<2;++I){if(!Guests.ContainsByPredicate([&](auto P){return IsValid(P) && P->CounterIndex==I && P->Stage<=EMarePersonStage::Products;})){Counter=I;break;}}
 if(Counter==INDEX_NONE)return;
 int32 Table=INDEX_NONE;bool bTables=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("kiosk_tables"),bTables);
 if(bTables){for(int32 I=0;I<TablePoints.Num();++I)if(!ReservedTables.Contains(I) && !DirtyTables.Contains(I)){Table=I;break;}if(Table==INDEX_NONE)return;}
 const FVector Start=CounterPoints[Counter]+FVector(FMath::RandBool()?650:-650,-180,0);
 auto Person=GetWorld()->SpawnActor<AMarePerson>(Start,FRotator::ZeroRotator);if(!Person)return;
 Person->Variant=FMath::RandRange(0,3);if(!Person->SetAppearance(Person->Variant)){Person->Destroy();return;}
 // 07/11 (Sergio: a man called "Luiza"): the MetaHuman picked for the look decides, not the old Godot variant number.
 const TArray<FString> Names=Person->IsWoman()?TArray<FString>{TEXT("Charbele"),TEXT("Yasmin"),TEXT("Ayla"),TEXT("Luiza"),TEXT("Ana Clara"),TEXT("Jéssica"),TEXT("Thaís"),TEXT("Dona Neide"),TEXT("Kelly"),TEXT("Raíssa"),TEXT("Fernanda"),TEXT("Tia Socorro")}
  :TArray<FString>{TEXT("João"),TEXT("Pedro"),TEXT("Rafael"),TEXT("Bruno"),TEXT("Thiago"),TEXT("Wesley"),TEXT("Seu Raimundo"),TEXT("Juninho"),TEXT("Cleber"),TEXT("Marcão"),TEXT("Davi"),TEXT("Tio Zeca")};   // Brazilian names only (Sergio, 04/11)
 Person->PersonName=Names[FMath::RandRange(0,Names.Num()-1)];Person->CounterIndex=Counter;Person->TableIndex=Table;
 // No path to the counter from this side (07/11, stuck customers): never leave someone frozen in the walk pose.
 if(!Person->WalkTo(CounterPoints[Counter])){Person->Destroy();return;}
 if(Table!=INDEX_NONE)ReservedTables.Add(Table);
 Guests.Add(Person);
 CreateInteraction(Person);
}
void UMareKioskWorld::CreateInteraction(AMarePerson* Person)
{
 auto Target=GetWorld()->SpawnActor<AMareServiceTarget>();Target->Action=TEXT("Customer");Target->Label=Person->PersonName;Target->SetOwner(Person);
 Target->AttachToActor(Person,FAttachmentTransformRules::SnapToTargetNotIncludingScale);Target->SetActorRelativeLocation(FVector(0,0,45));Target->Reach=350;Target->OcclusionTolerance=90;Person->Interaction=Target;
}
bool UMareKioskWorld::Serve(AMarePerson* Person,bool bStaff)
{
 auto S=Sim();if(!S || !IsValid(Person))return false;
 if(Person->Stage==EMarePersonStage::Order){
  TArray<FString> Menu=S->KioskMenu();
  Menu.RemoveAll([S](const FString& Id){return !S->IsDishUnlocked(Id);});if(Menu.IsEmpty())return false;
  // Better recipes are ordered more often (weight 1 + 0.5 per recipe level above the first).
  auto PickDish=[S,&Menu](){double Total=0;for(const auto& Id:Menu)Total+=S->DishDemand(Id);double R=FMath::FRandRange(0.,Total);
   for(const auto& Id:Menu){R-=S->DishDemand(Id);if(R<=0)return Id;}return Menu.Last();};
  Person->Plan={PickDish()};if(FMath::RandRange(0,3)==0)Person->Plan.Add(PickDish());
  Person->OrderId=S->AddOrder(Person->PersonName,Person->Plan);if(Person->OrderId.IsEmpty())return false;
  S->RollVip(Person->OrderId);Person->Express(TEXT("hmm"),1.6f);   // choosing from the menu: a thinking "hmm"
  // 10/11 (reference tip 9): while the order is being prepared, about half of the customers wait with their arms
  // folded (the same person always the same way). The UAL 2 "Yes" clip is a raised arm, not a nod: not used here.
  if(FCrc::StrCrc32(*(Person->SaveId+Person->PersonName))%2==0)Person->WaitPose=TEXT("Idle_FoldArms");   // i18n:skip
  Person->Stage=EMarePersonStage::Products;Person->Elapsed=0;return true;
 }
 if(Person->Stage!=EMarePersonStage::Products)return false;
 const FString Dish=S->Carry(bStaff);if(Dish.IsEmpty())return false;
 if(!S->Deliver(Person->OrderId,Dish,bStaff))return false;
 Person->Delivered.Add(Dish);Person->HoldProduct(Dish);Person->Elapsed=0;Person->Express(TEXT("smile"),4.f);   // served: a smile
 Person->PlayGesture(TEXT("PickUp_Table"),1.1f);   // takes it from the counter (UAL clip, MarePerson::PlayGesture)
 if(!UMareSimulation::Object(S->State,TEXT("ue_orders"))->HasField(Person->OrderId)){
  FinishCounter(Person);
  // 07/11 (reference game: "sistema de pagamento assim"): the player who served the whole order takes the payment.
  if(!bStaff){double Total=0;for(const FString& Id:Person->Delivered)Total+=S->SalePrice(Id);
   if(auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(GetWorld(),0)))PC->OpenPayment(Person->PersonName,Total);}}
 return true;
}
void UMareKioskWorld::FinishCounter(AMarePerson* Person)
{
 // The order is complete: the faster it was, the better the stars (5 right away, 2.5 at the end of the patience).
 if(auto S=Sim())S->AddRating(5.-2.5*FMath::Clamp(Person->Elapsed/(80.f*float(S->KioskPatienceFactor())),0.f,1.f));
 Person->CounterIndex=-1;if(Person->Interaction){Person->Interaction->Destroy();Person->Interaction=nullptr;}
 Person->Stage=EMarePersonStage::ToTable;Person->Elapsed=0;
 const FVector Goal=Person->TableIndex!=INDEX_NONE?TableApproaches[Person->TableIndex]:Person->GetActorLocation()+FVector(160,-170,0);
 Person->WalkTo(Goal);
}
void UMareKioskWorld::Leave(AMarePerson* Person)
{
 if(Person->Interaction){Person->Interaction->Destroy();Person->Interaction=nullptr;}
 if(Person->TableIndex!=INDEX_NONE && !DirtyTables.Contains(Person->TableIndex))ReservedTables.Remove(Person->TableIndex);
 if(auto S=Sim())UMareSimulation::Object(S->State,TEXT("ue_orders"))->RemoveField(Person->OrderId);
 // A seated capsule overlaps its chair. Stand in the authored clear approach
 // before enabling walking collision, rather than trapping the guest in furniture.
 if(Person->Stage==EMarePersonStage::Eating && TableApproaches.IsValidIndex(Person->TableIndex)){
  FNavLocation Standing;
  if(auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld()))
   if(Nav->ProjectPointToNavigation(TableApproaches[Person->TableIndex],Standing,FVector(150,150,150)))
    Person->SetActorLocation(Standing.Location+FVector(0,0,Person->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
 }
 Person->CounterIndex=-1;Person->Stage=EMarePersonStage::Leaving;Person->Elapsed=0;
 WalkAway(Person);
}
/** 07/11 (Sergio: "clientes travados"): the exit used to be one fixed point 8.5 m east; when it fell off the navmesh
 *  (the deck, the water) WalkTo failed silently and the guest stood in the walk pose until vanishing in sight. Try the
 *  beach both ways and inland; with no path at all, stand idle (removed once out of the player's view). */
bool UMareKioskWorld::WalkAway(AMarePerson* Person)
{
 const FVector At=Person->GetActorLocation();
 const FVector Tries[]={FVector(850,-60,0),FVector(-850,-60,0),FVector(700,500,0),FVector(-700,500,0),FVector(450,-350,0),FVector(-450,-350,0)};
 const int32 Start=FMath::RandRange(0,1);   // half go east, half west: not a parade in one direction
 for(int32 I=0;I<UE_ARRAY_COUNT(Tries);++I){const FVector Off=Tries[(I+Start)%UE_ARRAY_COUNT(Tries)];if(Person->WalkTo(At+Off))return true;}
 if(auto AI=Cast<AAIController>(Person->GetController()))AI->StopMovement();
 Person->PlayPose(TEXT("Idle"));return false;
}
/** Somebody the player is looking at, close enough to notice a pop. */
static bool SeenByPlayer(UWorld* World,const FVector& At)
{
 APlayerController* PC=UGameplayStatics::GetPlayerController(World,0);if(!PC || !PC->PlayerCameraManager)return false;
 const FVector Eye=PC->PlayerCameraManager->GetCameraLocation(),To=At-Eye;
 return To.Size()<3500.f && FVector::DotProduct(To.GetSafeNormal(),PC->PlayerCameraManager->GetCameraRotation().Vector())>.35f;
}
void UMareKioskWorld::MakeDirty(AMarePerson* Person)
{
 const int32 Table=Person->TableIndex;if(Table==INDEX_NONE || DirtyTables.Contains(Table))return;
 SpawnDirtyTable(Table,Person->Delivered);TArray<TSharedPtr<FJsonValue>> Items;
 for(const auto& Dish:Person->Delivered)Items.Add(MakeShared<FJsonValueString>(Dish));
 if(auto S=Sim())UMareSimulation::Object(S->State,TEXT("ue_dirty_tables"))->SetArrayField(FString::FromInt(Table),Items);
}
void UMareKioskWorld::SpawnDirtyTable(int32 Table,const TArray<FString>& Items)
{
 if(!TableSurfaces.IsValidIndex(Table) || DirtyTables.Contains(Table))return;
 DirtyTables.Add(Table);ReservedTables.Add(Table);
 for(int32 I=0;I<Items.Num();++I){const FString& Dish=Items[I];
  auto Mesh=AMarePerson::ProductMesh(Dish,true);if(!Mesh)continue;
  const FRotator Orientation(0,TableYaw[Table],0);
  const FVector Offset=Orientation.RotateVector(FVector((I/2)*16.f,Items.Num()>1?(I%2==0?-8.f:8.f):0.f,1));
  auto Object=GetWorld()->SpawnActor<AStaticMeshActor>(TableSurfaces[Table]+Offset,FRotator::ZeroRotator);
  Object->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);Object->GetStaticMeshComponent()->SetStaticMesh(Mesh);Object->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Object->Tags.Add(FName(*FString::Printf(TEXT("Table_%d"),Table)));DirtyObjects.Add(Object);
 }
 auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(TableSurfaces[Table],FRotator::ZeroRotator);Target->Action=TEXT("Clean");Target->Label=TEXT("Recolher louça");Target->DataIndex=Table;Target->Tags.Add(FName(*FString::Printf(TEXT("Table_%d"),Table)));DirtyObjects.Add(Target);
}
void UMareKioskWorld::CleanTable(int32 Index)
{
 const FName Tag(*FString::Printf(TEXT("Table_%d"),Index));
 for(int32 I=DirtyObjects.Num()-1;I>=0;--I)if(!IsValid(DirtyObjects[I]) || DirtyObjects[I]->Tags.Contains(Tag)){if(IsValid(DirtyObjects[I]))DirtyObjects[I]->Destroy();DirtyObjects.RemoveAt(I);}
 DirtyTables.Remove(Index);
 if(!Guests.ContainsByPredicate([&](auto P){return IsValid(P) && P->TableIndex==Index && P->Stage!=EMarePersonStage::Leaving;}))ReservedTables.Remove(Index);
 if(auto S=Sim()){UMareSimulation::Object(S->State,TEXT("ue_dirty_tables"))->RemoveField(FString::FromInt(Index));S->Save();}
}
bool UMareKioskWorld::CanCustomize(FString& Reason)const
{
 auto S=GetWorld() && GetWorld()->GetGameInstance()?GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;
 if(S && S->IsOpen()){Reason=TEXT("Feche o quiosque pela placa do balcão para trocar a decoração.");return false;}
 if(Guests.ContainsByPredicate([](const auto& P){return IsValid(P);})){Reason=TEXT("Espere os clientes saírem para trocar a decoração.");return false;}
 if(!DirtyTables.IsEmpty()){Reason=TEXT("Recolha a louça das mesas antes de trocar a decoração.");return false;}
 Reason.Empty();return true;
}
void UMareKioskWorld::UpdateCustomer(AMarePerson* P)
{
 auto S=Sim();if(!S)return;
 if(P->Stage==EMarePersonStage::Approaching && P->Elapsed>45){Leave(P);return;}
 if(P->Stage==EMarePersonStage::Approaching && P->AtGoal()){
  P->Stage=P->OrderId.IsEmpty()?EMarePersonStage::Order:EMarePersonStage::Products;P->Elapsed=0;
  if(CounterStaffPoints.IsValidIndex(P->CounterIndex))
   P->SetActorRotation(FRotator(0,(CounterStaffPoints[P->CounterIndex]-P->GetActorLocation()).Rotation().Yaw,0));
 }
 else if((P->Stage==EMarePersonStage::Order || P->Stage==EMarePersonStage::Products) && P->Elapsed>80*S->KioskPatienceFactor()){
  // Gave up waiting: one star and a grumble (the stars move tomorrow's traffic, UMareSimulation::KioskArrivalFactor).
  S->AddRating(1.);P->Express(TEXT("annoyed"),3.f);S->LastMessage=P->PersonName+TEXT(" cansou de esperar e foi embora resmungando. Uma estrela.");Leave(P);}
 else if(P->Stage==EMarePersonStage::ToTable && P->TableIndex!=INDEX_NONE && !P->AtGoal() && P->Elapsed<35 && P->GetVelocity().SizeSquared2D()<100
  && (FMath::IsNearlyEqual(P->Elapsed,12.f,.6f) || FMath::IsNearlyEqual(P->Elapsed,24.f,.6f))){
  // Stuck behind a chair or another guest: ask for the path again, the goal nudged a little around the approach.
  P->WalkTo(TableApproaches[P->TableIndex]+FVector(FMath::FRandRange(-40.f,40.f),FMath::FRandRange(-40.f,40.f),0));P->Elapsed+=1.2f;}
 else if(P->Stage==EMarePersonStage::ToTable && (P->AtGoal() || P->Elapsed>35)){
  // Close enough after the retries: take the seat (the guest is placed on it either way); far away: give up.
  const bool bNear=P->TableIndex!=INDEX_NONE && FVector::Dist2D(P->GetActorLocation(),TableApproaches[P->TableIndex])<300.f;
  if(!P->AtGoal() && !bNear){
   UE_LOG(LogTemp,Warning,TEXT("Maré kiosk: %s gave up reaching table %d: at %s, goal %s, %.0f cm away, velocity %.0f"),*P->PersonName,P->TableIndex,
    *P->GetActorLocation().ToString(),*P->Destination.ToString(),FVector::Dist2D(P->GetActorLocation(),P->Destination),P->GetVelocity().Size2D());
   Leave(P);return;}
  if(P->TableIndex!=INDEX_NONE){if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();P->GetCharacterMovement()->DisableMovement();P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);P->SetActorLocation(TablePoints[P->TableIndex]);P->SetActorRotation(FRotator(0,TableYaw[P->TableIndex],0));P->PlayPose(TEXT("Sitting_Idle"));P->AlignToSeatBelow();}
  else P->PlayPose(TEXT("Idle"));
  P->Stage=EMarePersonStage::Eating;P->Elapsed=0;
 }
 else if(P->Stage==EMarePersonStage::Eating){if(P->Elapsed>8 && !P->bConsumed){P->bConsumed=true;P->ClearProducts();MakeDirty(P);}if(P->Elapsed>18)Leave(P);}
 else if(P->Stage==EMarePersonStage::Leaving){
  // Keep walking while the player watches (a new leg further on); vanish only out of sight, or after a minute anyway.
  const bool bStill=P->GetVelocity().SizeSquared2D()<100.f && P->Elapsed>3.f;
  if(P->Elapsed>60.f || ((P->AtGoal() || bStill || P->Elapsed>25.f) && !SeenByPlayer(GetWorld(),P->GetActorLocation()+FVector(0,0,80))))P->Destroy();
  else if(P->AtGoal() || (bStill && FMath::Fmod(P->Elapsed,4.f)<.05f))WalkAway(P);}
}
void UMareKioskWorld::UpdateAttendant(float DeltaSeconds)
{
 auto S=Sim();bool bHired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bHired);
 if(!bHired){if(IsValid(Attendant)){Attendant->Destroy();Attendant=nullptr;}return;}
 if(!IsValid(Attendant)){Attendant=GetWorld()->SpawnActor<AMarePerson>(FVector(3700,-1230,98),FRotator::ZeroRotator);Attendant->bEmployee=true;Attendant->Variant=3;Attendant->SetAppearance(3);Attendant->PersonName=TEXT("Atendente");Attendant->StaffRole=TEXT("atendente");}
 StaffClock+=DeltaSeconds;if(StaffClock<1.5)return;StaffClock=0;
 for(auto P:Guests){if(!IsValid(P) || P->CounterIndex<0)continue;
  const FVector Goal=CounterStaffPoints[P->CounterIndex];
  if((P->Stage==EMarePersonStage::Order || !S->Carry(true).IsEmpty()) && FVector::DistSquared2D(Attendant->GetActorLocation(),Goal)>FMath::Square(80.f)){if(FVector::DistSquared2D(Attendant->Destination,Goal)>100)Attendant->WalkTo(Goal);return;}
  if(P->Stage==EMarePersonStage::Order){Serve(P,true);return;}
  if(P->Stage!=EMarePersonStage::Products)continue;
  auto Order=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("ue_orders")),P->OrderId);const TArray<TSharedPtr<FJsonValue>>* Items=nullptr;
  if(!Order->TryGetArrayField(TEXT("remaining"),Items) || Items->IsEmpty())continue;
  const FString Dish=(*Items)[0]->AsString();
  const FString Held=S->Carry(true);
  if(!Held.IsEmpty() && !Items->ContainsByPredicate([&](const auto& Item){return Item->AsString()==Held;})){
   S->ReturnCarry(true);Attendant->ClearProducts();return;
  }
  if(S->Carry(true).IsEmpty()){
   const FVector Storage=Dish==TEXT("batata_frita") || Dish==TEXT("porcao_peixe")?FVector(3800,-1240,98):FVector(3920,-1240,98);
   if(FVector::DistSquared2D(Attendant->GetActorLocation(),Storage)>FMath::Square(95.f)){Attendant->WalkTo(Storage);return;}
   if(S->Pickup(Dish,true)){Attendant->ClearProducts();Attendant->HoldProduct(Dish);Attendant->PlayGesture(TEXT("PickUp_Table"),1.1f);}return;
  }
  if(Serve(P,true))Attendant->ClearProducts();return;
 }
 if(!S->Carry(true).IsEmpty()){S->ReturnCarry(true);Attendant->ClearProducts();}
 if(!DirtyTables.IsEmpty()){const int32 Table=*DirtyTables.CreateConstIterator();
  if(FVector::DistSquared2D(Attendant->GetActorLocation(),TableApproaches[Table])>FMath::Square(100.f)){Attendant->WalkTo(TableApproaches[Table]);return;}
  CleanTable(Table);
 }
}
void UMareKioskWorld::Tick(float DeltaSeconds)
{
 auto S=Sim();if(!S || !GetWorld()->IsGameWorld() || !GetWorld()->GetAuthGameMode<AMareGameMode>() || GetWorld()->IsPaused())return;
 if(!bRestored){RestoreWorld();bRestored=true;}
 const int32 Day=UMareSimulation::Number(S->State,TEXT("day"),1);
 if(LastDay!=INDEX_NONE && LastDay!=Day){for(auto P:Guests)if(IsValid(P)){if(P->Interaction)P->Interaction->Destroy();P->Destroy();}Guests.Empty();ReservedTables=DirtyTables;if(IsValid(Attendant))Attendant->ClearProducts();}
 LastDay=Day;
 Guests.RemoveAll([](auto P){return !IsValid(P);});
 RecoverOrders();
 // Decor comfort + beauty bring customers more often (KioskArrivalFactor, 1 .. ~3.4).
 // Rush hours: lunch (12-14h) and the sunset (17-18h30) bring 60 % more people at once.
 const double Clock=UMareSimulation::Number(S->State,TEXT("minutes"))/60.;const float Rush=(Clock>=12 && Clock<14) || (Clock>=17 && Clock<18.5)?1.6f:1.f;
 if(S->IsOpen()){Arrival-=DeltaSeconds;if(Arrival<=0){SpawnCustomer();Arrival=FMath::FRandRange(18.f,30.f)/(float(S->KioskArrivalFactor())*Rush);}}
 // Not while busy with something else (a comic event stops him for a moment: HUM-006).
 if(IsValid(Attendant) && !Attendant->bConversing)Attendant->GetCharacterMovement()->MaxWalkSpeed=125.f*float(S->KioskServiceSpeed());
 for(auto P:Guests){
  if(!S->IsOpen() && P->OrderId.IsEmpty() && (P->Stage==EMarePersonStage::Approaching || P->Stage==EMarePersonStage::Order))Leave(P);
  UpdateCustomer(P);
 }
 UpdateAttendant(DeltaSeconds);
}

TArray<TPair<FVector,FString>> UMareKioskWorld::Bubbles()const
{
 TArray<TPair<FVector,FString>> Out;auto S=const_cast<UMareKioskWorld*>(this)->Sim();if(!S)return Out;
 auto Dishes=UMareSimulation::Object(S->Definitions,TEXT("dishes"));   // i18n:skip
 for(const auto& P:Guests){if(!IsValid(P) || P->CounterIndex<0)continue;
  FString Line;
  if(P->Stage==EMarePersonStage::Order)Line=TEXT("Quero pedir!");
  else if(P->Stage==EMarePersonStage::Products){TArray<FString> Missing=P->Plan;for(const FString& D:P->Delivered)Missing.RemoveSingle(D);
   if(Missing.Num())Line=UMareSimulation::String(UMareSimulation::Object(Dishes,Missing[0]),TEXT("name"))+(Missing.Num()>1?FString::Printf(TEXT(" +%d"),Missing.Num()-1):FString());}   // i18n:skip
  if(!Line.IsEmpty())Out.Add({P->GetActorLocation()+FVector(0,0,112),Line});}
 return Out;
}
