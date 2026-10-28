#include "MareSimulation.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareEconomyTest,"MareAlta.Migration.NativeEconomy",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareEconomyTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/NativeEconomy")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 TestTrue(TEXT("Definitions exported from approved source"),Load(TEXT("definitions.json"),Sim->Definitions));
 TestTrue(TEXT("Default save exported without personal data"),Load(TEXT("default_save.json"),Sim->State));
 if(!Sim->Definitions.IsValid() || !Sim->State.IsValid()){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 TestFalse(TEXT("Kiosk starts closed"),Sim->IsOpen());
 TestTrue(TEXT("New profile has no purchased expansions"),Sim->Object(Sim->State,TEXT("unlocked"))->Values.IsEmpty());
 const double StartingMoney=Sim->Money();
 TestFalse(TEXT("Cannot buy pool before required expansions"),Sim->BuyExpansion(TEXT("pool")));
 TestEqual(TEXT("Rejected purchase preserves money"),Sim->Money(),StartingMoney);
 TestFalse(TEXT("Drinks need purchased licence"),Sim->IsDishUnlocked(TEXT("caipirinha")));
 TestFalse(TEXT("Locked drink cannot be picked"),Sim->Pickup(TEXT("caipirinha")));
 TestFalse(TEXT("Locked petiscos cannot be replenished"),Sim->Restock(TEXT("petiscos"),10));
 Sim->State->SetNumberField(TEXT("money"),100000);
 const double TablesPrice=Sim->Number(Sim->Object(Sim->Object(Sim->Definitions,TEXT("expansions")),TEXT("kiosk_tables")),TEXT("cost"));
 TestTrue(TEXT("Buy first expansion"),Sim->BuyExpansion(TEXT("kiosk_tables")));
 TestEqual(TEXT("Expansion charged once"),Sim->Money(),100000-TablesPrice);
 TestFalse(TEXT("Owned expansion cannot be purchased twice"),Sim->BuyExpansion(TEXT("kiosk_tables")));
 TestEqual(TEXT("Duplicate purchase preserves money"),Sim->Money(),100000-TablesPrice);
 TSharedPtr<FJsonObject> SavedExpansion;FString SavedText;
 FFileHelper::LoadFileToString(SavedText,*(Sim->SaveDirectory/TEXT("slot1.json")));
 FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(SavedText),SavedExpansion);
 bool bSavedOwned=false;Sim->Object(SavedExpansion,TEXT("unlocked"))->TryGetBoolField(TEXT("kiosk_tables"),bSavedOwned);
 TestTrue(TEXT("Purchased expansion persists"),bSavedOwned);
 TestTrue(TEXT("Buy drinks licence"),Sim->BuyExpansion(TEXT("drinks")));
 TestTrue(TEXT("Purchased drinks licence releases product"),Sim->IsDishUnlocked(TEXT("caipirinha")));
 TestTrue(TEXT("Restock newly licensed product"),Sim->Restock(TEXT("caipirinha"),10));
 TestTrue(TEXT("Licensed product can be picked"),Sim->Pickup(TEXT("caipirinha")));
 Sim->ReturnCarry();
 Sim->State->SetNumberField(TEXT("money"),StartingMoney);
 Sim->Object(Sim->State,TEXT("unlocked"))->RemoveField(TEXT("kiosk_tables"));
 Sim->Object(Sim->State,TEXT("unlocked"))->RemoveField(TEXT("drinks"));
 auto LegacyOrder=MakeShared<FJsonObject>();
 LegacyOrder->SetArrayField(TEXT("remaining"),{MakeShared<FJsonValueString>(TEXT("caipirinha"))});
 Sim->Object(Sim->State,TEXT("ue_orders"))->SetObjectField(TEXT("legacy-license-order"),LegacyOrder);
 TestFalse(TEXT("Old order does not grant licence"),Sim->IsDishUnlocked(TEXT("caipirinha")));
 TestTrue(TEXT("Old saved order remains fulfillable"),Sim->CanSupplyDish(TEXT("caipirinha")));
 TestTrue(TEXT("Can pick drink for old saved order"),Sim->Pickup(TEXT("caipirinha")));
 Sim->ReturnCarry();Sim->Object(Sim->State,TEXT("ue_orders"))->RemoveField(TEXT("legacy-license-order"));
 TestFalse(TEXT("Old order exception ends when order ends"),Sim->CanSupplyDish(TEXT("caipirinha")));
 TestTrue(TEXT("Closed kiosk refuses arrivals"),Sim->AddOrder(TEXT("Ana"),{TEXT("suco")}).IsEmpty());
 TestFalse(TEXT("Cannot open before creating company"),Sim->SetOpen(true));
 TestTrue(TEXT("Create company"),Sim->CreateCompany(TEXT("Maré de teste")));
 TestTrue(TEXT("Opening can be requested before hours"),Sim->SetOpen(true));
 TestFalse(TEXT("Requested opening still respects working hours"),Sim->IsOpen());
 TestTrue(TEXT("Queued opening can be cancelled"),Sim->SetOpen(false));
 Sim->State->SetNumberField(TEXT("minutes"),600);
 TestTrue(TEXT("Open explicitly"),Sim->SetOpen(true));
 const FString Id=Sim->AddOrder(TEXT("Ana"),{TEXT("suco"),TEXT("coco_gelado")});
 TestFalse(TEXT("Counter customer has order"),Id.IsEmpty());
 const double Before=Sim->Money();const int32 Cups=Sim->Available(TEXT("suco"));
 TestTrue(TEXT("Ready product pickup"),Sim->Pickup(TEXT("suco")));
 TestEqual(TEXT("Pickup consumes exactly once"),Sim->Available(TEXT("suco")),Cups-1);
 TestFalse(TEXT("Cannot pick second product into occupied hand"),Sim->Pickup(TEXT("suco")));
 TestTrue(TEXT("Return restores inventory"),Sim->ReturnCarry());
 TestEqual(TEXT("Return exact amount"),Sim->Available(TEXT("suco")),Cups);
 TestFalse(TEXT("Second return cannot duplicate inventory"),Sim->ReturnCarry());
 Sim->Pickup(TEXT("suco"));TestTrue(TEXT("Delivery pays immediately"),Sim->Deliver(Id,TEXT("suco")));
 TestEqual(TEXT("Correct automatic price"),Sim->Money(),Before+14);
 TestFalse(TEXT("Delivery cannot pay twice"),Sim->Deliver(Id,TEXT("suco")));
 TestTrue(TEXT("Partial order remains visible"),Sim->Object(Sim->State,TEXT("ue_orders"))->HasField(Id));
 Sim->Pickup(TEXT("coco_gelado"));Sim->Deliver(Id,TEXT("coco_gelado"));
 TestFalse(TEXT("Completed order removed"),Sim->Object(Sim->State,TEXT("ue_orders"))->HasField(Id));
 const double Cost=Sim->RestockCost(TEXT("suco"),10);const double Cash=Sim->Money();
 TestTrue(TEXT("Direct restock"),Sim->Restock(TEXT("suco"),10));
 TestEqual(TEXT("Only missing inputs charged"),Sim->Money(),Cash-Cost);
 TestEqual(TEXT("Ten ready juices"),Sim->Available(TEXT("suco")),10);
 Sim->State->SetNumberField(TEXT("money"),0);const int32 Fish=Sim->Available(TEXT("porcao_peixe"));
 TestFalse(TEXT("Atomic restock refuses insufficient cash"),Sim->Restock(TEXT("porcao_peixe"),48));
 TestEqual(TEXT("No partial replenishment"),Sim->Available(TEXT("porcao_peixe")),Fish);
 Sim->State->SetNumberField(TEXT("money"),1000);
 TestTrue(TEXT("Single attendant hire"),Sim->HireAttendant());TestFalse(TEXT("No duplicate attendant"),Sim->HireAttendant());
 TestTrue(TEXT("Campaign reward"),Sim->ClaimMission(TEXT("chegada")));const double Rewarded=Sim->Money();
 TestFalse(TEXT("Campaign reward idempotent"),Sim->ClaimMission(TEXT("chegada")));TestEqual(TEXT("No repeated reward"),Sim->Money(),Rewarded);
 TestTrue(TEXT("Native save created in isolated directory"),FPaths::FileExists(Sim->SaveDirectory/TEXT("slot1.json")));
 Sim->ReturnCarry();const int32 StockBefore=Sim->Available(TEXT("coco_gelado"));
 TestTrue(TEXT("Player picks a product"),Sim->Pickup(TEXT("coco_gelado")));
 TestTrue(TEXT("Attendant has independent carry"),Sim->Pickup(TEXT("coco_gelado"),true));
 TestEqual(TEXT("Two inventories consume two products"),Sim->Available(TEXT("coco_gelado")),StockBefore-2);
 TestEqual(TEXT("Player item preserved"),Sim->Carry(),FString(TEXT("coco_gelado")));
 TestTrue(TEXT("Attendant return independent"),Sim->ReturnCarry(true));
 TestEqual(TEXT("Attendant return does not clear player hand"),Sim->Carry(),FString(TEXT("coco_gelado")));
 Sim->ReturnCarry();TestEqual(TEXT("Both returns restore exact inventory"),Sim->Available(TEXT("coco_gelado")),StockBefore);
 Sim->Sleep();TestFalse(TEXT("Sleeping closes business"),Sim->IsOpen());
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
#endif
