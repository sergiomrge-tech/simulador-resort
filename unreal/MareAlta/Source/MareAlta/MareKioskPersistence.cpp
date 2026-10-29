#include "MareKioskWorld.h"
#include "MarePerson.h"
#include "MareServiceTarget.h"
#include "MareHomeWorld.h"
#include "MareSimulation.h"
#include "AIController.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"

namespace MarePersistence
{
 using FObject=TSharedPtr<FJsonObject>;
 TArray<TSharedPtr<FJsonValue>> Vector(const FVector& V)
 {
  return {MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)};
 }
 FVector Vector(const FObject& Row,const FString& Key,const FVector& Fallback)
 {
  const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
  if(!Row->TryGetArrayField(Key,Values) || Values->Num()!=3)return Fallback;
  for(const auto& Value:*Values)if(!Value.IsValid() || Value->Type!=EJson::Number || !FMath::IsFinite(Value->AsNumber()))return Fallback;
  return FVector((*Values)[0]->AsNumber(),(*Values)[1]->AsNumber(),(*Values)[2]->AsNumber());
 }
 TArray<FString> Strings(const FObject& Row,const FString& Key)
 {
  TArray<FString> Result;const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
  if(Row->TryGetArrayField(Key,Values))for(const auto& Value:*Values)if(Value.IsValid() && Value->Type==EJson::String)Result.Add(Value->AsString());
  return Result;
 }
 void Strings(const FObject& Row,const FString& Key,const TArray<FString>& Values)
 {
  TArray<TSharedPtr<FJsonValue>> Result;for(const auto& Value:Values)Result.Add(MakeShared<FJsonValueString>(Value));Row->SetArrayField(Key,Result);
 }
 FObject Pose(const AActor* Actor,const FObject& Previous=nullptr)
 {
  auto Row=Previous.IsValid()?MakeShared<FJsonObject>(*Previous):MakeShared<FJsonObject>();Row->SetArrayField(TEXT("position"),Vector(Actor->GetActorLocation()));Row->SetNumberField(TEXT("yaw"),Actor->GetActorRotation().Yaw);return Row;
 }
}

void UMareKioskWorld::BeforeTearDown(UWorld* World)
{
 if(World==GetWorld() && bRestored && Sim())Sim()->Save();
}
void UMareKioskWorld::Deinitialize()
{
 FWorldDelegates::OnWorldBeginTearDown.Remove(TearDownHandle);Super::Deinitialize();
}

TSharedPtr<FJsonObject> UMareKioskWorld::CaptureGuest(AMarePerson* P,TSet<FString>& Claimed)const
{
 using namespace MarePersistence;
 auto Row=Pose(P,P->SaveMetadata);auto S=Sim();auto Orders=UMareSimulation::Object(S->State,TEXT("ue_orders"));
 FString OrderId=P->OrderId;auto Stage=P->Stage;TArray<FString> Delivered=P->Delivered;
 // AddOrder saves before its caller receives the id. Bind that new transaction
 // using the unclaimed order rather than writing a customer-less order to disk.
 if(OrderId.IsEmpty() && Stage==EMarePersonStage::Order && !P->Plan.IsEmpty())
  for(const auto& Pair:Orders->Values){const FString Id(Pair.Key.ToView());auto Order=Pair.Value->AsObject();
   if(!Claimed.Contains(Id) && UMareSimulation::String(Order,TEXT("name"))==P->PersonName && Strings(Order,TEXT("remaining"))==P->Plan){OrderId=Id;Claimed.Add(Id);break;}
  }
 if(!OrderId.IsEmpty() && Stage<=EMarePersonStage::Products){
  Delivered=P->Plan;
  if(Orders->HasTypedField<EJson::Object>(OrderId)){
   for(const auto& Dish:Strings(UMareSimulation::Object(Orders,OrderId),TEXT("remaining")))Delivered.RemoveSingle(Dish);
   if(Stage==EMarePersonStage::Order)Stage=EMarePersonStage::Products;
  }else Stage=EMarePersonStage::ToTable;
 }
 Row->SetStringField(TEXT("id"),P->SaveId);Row->SetStringField(TEXT("name"),P->PersonName);Row->SetStringField(TEXT("order"),OrderId);
 Row->SetNumberField(TEXT("variant"),P->Variant);Row->SetNumberField(TEXT("stage"),int32(Stage));
 Row->SetNumberField(TEXT("counter"),Stage<=EMarePersonStage::Products?P->CounterIndex:-1);Row->SetNumberField(TEXT("table"),P->TableIndex);
 Row->SetNumberField(TEXT("elapsed"),Stage==P->Stage?P->Elapsed:0);Row->SetBoolField(TEXT("consumed"),P->bConsumed);
 Row->SetArrayField(TEXT("destination"),Vector(P->Destination));Strings(Row,TEXT("plan"),P->Plan);Strings(Row,TEXT("delivered"),Delivered);
 return Row;
}

void UMareKioskWorld::CaptureState()
{
 using namespace MarePersistence;
 if(!bRestored || bRestoring || !Sim())return;auto S=Sim();auto Snapshot=UMareSimulation::Object(S->State,TEXT("ue_kiosk"));
 const int32 Day=UMareSimulation::Number(S->State,TEXT("day"),1);TArray<TSharedPtr<FJsonValue>> Rows;TSet<FString> Claimed;
 for(auto P:Guests)if(IsValid(P) && !P->OrderId.IsEmpty())Claimed.Add(P->OrderId);
 if(LastDay==Day)for(auto P:Guests)if(IsValid(P))Rows.Add(MakeShared<FJsonValueObject>(CaptureGuest(P,Claimed)));
 Snapshot->SetNumberField(TEXT("version"),1);Snapshot->SetNumberField(TEXT("day"),Day);Snapshot->SetArrayField(TEXT("guests"),Rows);
 Snapshot->SetNumberField(TEXT("arrival"),LastDay==Day?Arrival:15);
 if(IsValid(Attendant))Snapshot->SetObjectField(TEXT("attendant"),Pose(Attendant,UMareSimulation::Object(Snapshot,TEXT("attendant"))));
 if(auto Player=UGameplayStatics::GetPlayerPawn(this,0)){
  auto Saved=Pose(Player,UMareSimulation::Object(Snapshot,TEXT("player")));
  if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())Saved->SetArrayField(TEXT("position"),Vector(Home->StandingPose(Player->GetActorTransform()).GetLocation()));
  if(auto PC=UGameplayStatics::GetPlayerController(this,0))Saved->SetArrayField(TEXT("view"),Vector(PC->GetControlRotation().Euler()));
  Snapshot->SetObjectField(TEXT("player"),Saved);
 }
 auto Doors=UMareSimulation::Object(Snapshot,TEXT("doors"));
 for(TActorIterator<AMareServiceTarget> It(GetWorld());It;++It)if(It->Action==TEXT("Door"))Doors->SetBoolField(It->Label,It->IsOpen());
}

void UMareKioskWorld::ResetPhysicalState()
{
 for(auto P:Guests)if(IsValid(P)){if(P->Interaction)P->Interaction->Destroy();P->Destroy();}
 for(auto Object:DirtyObjects)if(IsValid(Object))Object->Destroy();
 if(IsValid(Attendant))Attendant->Destroy();
 Guests.Empty();DirtyObjects.Empty();Attendant=nullptr;DirtyTables.Empty();ReservedTables.Empty();
 bRestored=false;bRestoring=false;LastDay=-1;Arrival=15;StaffClock=0;
}

void UMareKioskWorld::RestoreWorld()
{
 using namespace MarePersistence;
 bRestoring=true;auto S=Sim();auto Snapshot=UMareSimulation::Object(S->State,TEXT("ue_kiosk"));
 const int32 Day=UMareSimulation::Number(S->State,TEXT("day"),1);LastDay=Day;
 auto Dirty=UMareSimulation::Object(S->State,TEXT("ue_dirty_tables"));
 for(const auto& Pair:Dirty->Values){const FString Key(Pair.Key.ToView());int32 Index;
  if(LexTryParseString(Index,*Key) && TableSurfaces.IsValidIndex(Index))SpawnDirtyTable(Index,Strings(Dirty,Key));
 }
 const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;
 if(UMareSimulation::Number(Snapshot,TEXT("day"),Day)==Day && Snapshot->TryGetArrayField(TEXT("guests"),Rows))
  for(const auto& Value:*Rows)if(Value.IsValid() && Value->Type==EJson::Object)RestoreGuest(Value->AsObject());
 Arrival=FMath::Clamp(float(UMareSimulation::Number(Snapshot,TEXT("arrival"),15)),1.f,30.f);
 UpdateAttendant(0);
 if(IsValid(Attendant) && Snapshot->HasTypedField<EJson::Object>(TEXT("attendant")))
  Attendant->SetActorLocation(Vector(UMareSimulation::Object(Snapshot,TEXT("attendant")),TEXT("position"),Attendant->GetActorLocation()));
 if(IsValid(Attendant) && !S->Carry(true).IsEmpty())Attendant->HoldProduct(S->Carry(true));
 auto Doors=UMareSimulation::Object(Snapshot,TEXT("doors"));
 for(TActorIterator<AMareServiceTarget> It(GetWorld());It;++It){bool bOpen=false;if(It->Action==TEXT("Door") && Doors->TryGetBoolField(It->Label,bOpen))It->RestoreDoorState(bOpen);}
 if(Snapshot->HasTypedField<EJson::Object>(TEXT("player")))if(auto Player=UGameplayStatics::GetPlayerPawn(this,0)){
  auto Saved=UMareSimulation::Object(Snapshot,TEXT("player"));Player->SetActorLocation(Vector(Saved,TEXT("position"),Player->GetActorLocation()));
  if(auto PC=UGameplayStatics::GetPlayerController(this,0))PC->SetControlRotation(FRotator::MakeFromEuler(Vector(Saved,TEXT("view"),PC->GetControlRotation().Euler())));
 }
 bRestoring=false;
}

void UMareKioskWorld::RestoreGuest(const TSharedPtr<FJsonObject>& Row)
{
 using namespace MarePersistence;
 const int32 Stage=UMareSimulation::Number(Row,TEXT("stage"));if(Stage<0 || Stage>int32(EMarePersonStage::Leaving))return;
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto P=GetWorld()->SpawnActor<AMarePerson>(Vector(Row,TEXT("position"),CounterPoints[0]),FRotator(0,UMareSimulation::Number(Row,TEXT("yaw")),0),Params);
 if(!P)return;P->SaveMetadata=MakeShared<FJsonObject>(*Row);P->SaveId=UMareSimulation::String(Row,TEXT("id"));P->Variant=FMath::Clamp(int32(UMareSimulation::Number(Row,TEXT("variant"))),0,3);
 if(!P->SetAppearance(P->Variant)){P->Destroy();return;}
 P->PersonName=UMareSimulation::String(Row,TEXT("name"));P->OrderId=UMareSimulation::String(Row,TEXT("order"));P->Stage=EMarePersonStage(Stage);
 P->CounterIndex=UMareSimulation::Number(Row,TEXT("counter"),-1);P->TableIndex=UMareSimulation::Number(Row,TEXT("table"),-1);
 if(!CounterPoints.IsValidIndex(P->CounterIndex))P->CounterIndex=-1;
 if(!TablePoints.IsValidIndex(P->TableIndex))P->TableIndex=-1;
 P->Plan=Strings(Row,TEXT("plan"));P->Delivered=Strings(Row,TEXT("delivered"));P->Elapsed=FMath::Max(0.f,float(UMareSimulation::Number(Row,TEXT("elapsed"))));
 Row->TryGetBoolField(TEXT("consumed"),P->bConsumed);P->Destination=Vector(Row,TEXT("destination"),P->GetActorLocation());
 if(P->TableIndex>=0 && P->Stage!=EMarePersonStage::Leaving)ReservedTables.Add(P->TableIndex);
 Guests.Add(P);ResumeGuest(P);
}

void UMareKioskWorld::ResumeGuest(AMarePerson* P)
{
 if(!P->bConsumed)for(const auto& Dish:P->Delivered)P->HoldProduct(Dish);
 if(P->Stage<=EMarePersonStage::Products){
  if(P->CounterIndex<0){Leave(P);return;}CreateInteraction(P);
  if(P->Stage==EMarePersonStage::Approaching)P->WalkTo(CounterPoints[P->CounterIndex]);
 }else if(P->Stage==EMarePersonStage::ToTable)FinishCounter(P);
 else if(P->Stage==EMarePersonStage::Eating){
  if(P->TableIndex>=0){P->GetCharacterMovement()->DisableMovement();P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);P->SetActorLocation(TablePoints[P->TableIndex]);P->SetActorRotation(FRotator(0,TableYaw[P->TableIndex],0));P->PlayPose(TEXT("Sitting_Idle"));}
  else P->PlayPose(TEXT("Idle"));
 }else if(P->Stage==EMarePersonStage::Leaving)P->WalkTo(P->Destination);
}

void UMareKioskWorld::RecoverOrders()
{
 using namespace MarePersistence;
 auto S=Sim();auto Orders=UMareSimulation::Object(S->State,TEXT("ue_orders"));
 for(const auto& Pair:Orders->Values){const FString Id(Pair.Key.ToView());
  if(Guests.ContainsByPredicate([&](auto P){return IsValid(P) && P->OrderId==Id;}))continue;
  int32 Counter=-1;for(int32 I=0;I<CounterPoints.Num();++I)
   if(!Guests.ContainsByPredicate([&](auto P){return IsValid(P) && P->CounterIndex==I;})){Counter=I;break;}
  if(Counter<0)return;auto Order=Pair.Value->AsObject();auto Remaining=Strings(Order,TEXT("remaining"));if(Remaining.IsEmpty())continue;
  auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("name"),UMareSimulation::String(Order,TEXT("name")));Row->SetStringField(TEXT("order"),Id);
  int32 Table=-1;bool bTables=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("kiosk_tables"),bTables);
  if(bTables){for(int32 I=0;I<TablePoints.Num();++I)if(!ReservedTables.Contains(I)){Table=I;break;}if(Table<0)return;}
  Row->SetNumberField(TEXT("counter"),Counter);Row->SetNumberField(TEXT("table"),Table);Row->SetNumberField(TEXT("stage"),int32(EMarePersonStage::Approaching));
  Row->SetArrayField(TEXT("position"),Vector(CounterPoints[Counter]+FVector(-650,-180,0)));
  auto Plan=Strings(Order,TEXT("items"));if(Plan.IsEmpty())Plan=Remaining;auto Delivered=Plan;for(const auto& Dish:Remaining)Delivered.RemoveSingle(Dish);
  Strings(Row,TEXT("plan"),Plan);Strings(Row,TEXT("delivered"),Delivered);RestoreGuest(Row);
 }
}
