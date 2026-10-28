#include "MareKioskWorld.h"
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
 const TArray<FString> Names=Person->Variant==3?TArray<FString>{TEXT("Ana"),TEXT("Maria"),TEXT("Luiza"),TEXT("Camila")}:TArray<FString>{TEXT("João"),TEXT("Pedro"),TEXT("Rafael"),TEXT("Bruno")};
 Person->PersonName=Names[FMath::RandRange(0,Names.Num()-1)];Person->CounterIndex=Counter;Person->TableIndex=Table;
 if(Table!=INDEX_NONE)ReservedTables.Add(Table);
 Guests.Add(Person);Person->WalkTo(CounterPoints[Counter]);
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
  TArray<FString> Menu={TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};
  Menu.RemoveAll([S](const FString& Id){return !S->IsDishUnlocked(Id);});if(Menu.IsEmpty())return false;
  Person->Plan={Menu[FMath::RandRange(0,Menu.Num()-1)]};if(FMath::RandRange(0,3)==0)Person->Plan.Add(Menu[FMath::RandRange(0,Menu.Num()-1)]);
  Person->OrderId=S->AddOrder(Person->PersonName,Person->Plan);if(Person->OrderId.IsEmpty())return false;
  Person->Stage=EMarePersonStage::Products;Person->Elapsed=0;return true;
 }
 if(Person->Stage!=EMarePersonStage::Products)return false;
 const FString Dish=S->Carry(bStaff);if(Dish.IsEmpty())return false;
 if(!S->Deliver(Person->OrderId,Dish,bStaff))return false;
 Person->Delivered.Add(Dish);Person->HoldProduct(Dish);Person->Elapsed=0;
 if(!UMareSimulation::Object(S->State,TEXT("ue_orders"))->HasField(Person->OrderId))FinishCounter(Person);
 return true;
}
void UMareKioskWorld::FinishCounter(AMarePerson* Person)
{
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
 Person->WalkTo(Person->GetActorLocation()+FVector(850,-60,0));
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
void UMareKioskWorld::UpdateCustomer(AMarePerson* P)
{
 if(P->Stage==EMarePersonStage::Approaching && P->Elapsed>45){Leave(P);return;}
 if(P->Stage==EMarePersonStage::Approaching && P->AtGoal()){
  P->Stage=P->OrderId.IsEmpty()?EMarePersonStage::Order:EMarePersonStage::Products;P->Elapsed=0;
  if(CounterStaffPoints.IsValidIndex(P->CounterIndex))
   P->SetActorRotation(FRotator(0,(CounterStaffPoints[P->CounterIndex]-P->GetActorLocation()).Rotation().Yaw,0));
 }
 else if((P->Stage==EMarePersonStage::Order || P->Stage==EMarePersonStage::Products) && P->Elapsed>120)Leave(P);
 else if(P->Stage==EMarePersonStage::ToTable && (P->AtGoal() || P->Elapsed>35)){
  if(!P->AtGoal()){Leave(P);return;}
  if(P->TableIndex!=INDEX_NONE){if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();P->GetCharacterMovement()->DisableMovement();P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);P->SetActorLocation(TablePoints[P->TableIndex]);P->SetActorRotation(FRotator(0,TableYaw[P->TableIndex],0));P->PlayPose(TEXT("Sitting_Idle"));}
  else P->PlayPose(TEXT("Idle"));
  P->Stage=EMarePersonStage::Eating;P->Elapsed=0;
 }
 else if(P->Stage==EMarePersonStage::Eating){if(P->Elapsed>8 && !P->bConsumed){P->bConsumed=true;P->ClearProducts();MakeDirty(P);}if(P->Elapsed>18)Leave(P);}
 else if(P->Stage==EMarePersonStage::Leaving && (P->Elapsed>25 || P->AtGoal()))P->Destroy();
}
void UMareKioskWorld::UpdateAttendant(float DeltaSeconds)
{
 auto S=Sim();bool bHired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bHired);
 if(!bHired){if(IsValid(Attendant)){Attendant->Destroy();Attendant=nullptr;}return;}
 if(!IsValid(Attendant)){Attendant=GetWorld()->SpawnActor<AMarePerson>(FVector(3700,-1230,98),FRotator::ZeroRotator);Attendant->bEmployee=true;Attendant->Variant=3;Attendant->SetAppearance(3);Attendant->PersonName=TEXT("Atendente");}
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
   if(S->Pickup(Dish,true)){Attendant->ClearProducts();Attendant->HoldProduct(Dish);}return;
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
 if(S->IsOpen()){Arrival-=DeltaSeconds;if(Arrival<=0){SpawnCustomer();Arrival=FMath::FRandRange(18.f,30.f);}}
 for(auto P:Guests){
  if(!S->IsOpen() && P->OrderId.IsEmpty() && (P->Stage==EMarePersonStage::Approaching || P->Stage==EMarePersonStage::Order))Leave(P);
  UpdateCustomer(P);
 }
 UpdateAttendant(DeltaSeconds);
}
