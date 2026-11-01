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
 TestTrue(TEXT("Dismiss attendant"),Sim->DismissAttendant());TestFalse(TEXT("Cannot dismiss twice"),Sim->DismissAttendant());TestTrue(TEXT("Rehire attendant"),Sim->HireAttendant());
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareProgressionTest,"MareAlta.Migration.DayCloseAndChapters",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareProgressionTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/DayCloseAndChapters")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);Sim->CreateCompany(TEXT("Teste"));
 const double Wage=Sim->Number(Sim->Object(Sim->Object(Sim->Definitions,TEXT("staff")),TEXT("atendente")),TEXT("wage"));
 // Legacy kiosk roles from old saves must not be billed after the single-attendant merge.
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("garcom"),true);
 TestTrue(TEXT("Hire attendant"),Sim->HireAttendant());const double AfterHire=Sim->Money();
 Sim->Sleep();
 TestEqual(TEXT("Only the attendant wage is charged"),Sim->Money(),AfterHire-Wage);
 TestEqual(TEXT("Day advanced"),int32(Sim->Number(Sim->State,TEXT("day"))),2);
 auto Last=Sim->Object(Sim->State,TEXT("ue_last_day"));
 TestEqual(TEXT("Summary keeps wages"),Sim->Number(Last,TEXT("wages")),Wage);
 TestEqual(TEXT("Daily totals reset"),Sim->Number(Sim->State,TEXT("day_out")),0.);
 Sim->State->SetNumberField(TEXT("day"),1);const double BeforeRepeat=Sim->Money();Sim->Sleep();
 TestEqual(TEXT("Reloaded day is not paid twice"),Sim->Money(),BeforeRepeat);
 TestEqual(TEXT("Fame starts unknown"),Sim->FameLevel(),1);
 TestTrue(TEXT("First chapter open"),Sim->IsChapterOpen(TEXT("pier")));TestFalse(TEXT("Second chapter waits"),Sim->IsChapterOpen(TEXT("prainha")));
 // Step 1: deliver four fish bought at the market, consumed exactly once.
 Sim->Object(Sim->State,TEXT("stock"))->SetNumberField(TEXT("peixe"),0);
 TestFalse(TEXT("Cannot deliver without fish"),Sim->AdvanceChapter(TEXT("pier")));
 const double Market=Sim->Money();TestTrue(TEXT("Buy fish"),Sim->BuySupply(TEXT("peixe"),4));
 TestEqual(TEXT("Market charged once"),Sim->Money(),Market-Sim->SupplyCost(TEXT("peixe"),4));
 TestTrue(TEXT("Deliver fish"),Sim->AdvanceChapter(TEXT("pier")));
 TestEqual(TEXT("Fish consumed"),Sim->Number(Sim->Object(Sim->State,TEXT("stock")),TEXT("peixe")),0.);
 TestEqual(TEXT("Step 2 active"),Sim->ChapterStep(TEXT("pier")),1);
 // Step 2: serve counts only deliveries after the step starts.
 Sim->State->SetNumberField(TEXT("minutes"),600);Sim->SetOpen(true);Sim->Restock(TEXT("coco_gelado"),20);
 for(int32 I=0;I<15;++I){const FString Id=Sim->AddOrder(TEXT("Cliente"),{TEXT("coco_gelado")});Sim->Pickup(TEXT("coco_gelado"));Sim->Deliver(Id,TEXT("coco_gelado"));}
 int32 Goal=0;TestEqual(TEXT("Fifteen served"),Sim->ChapterStepProgress(TEXT("pier"),Goal),15);
 TestTrue(TEXT("Serve step"),Sim->AdvanceChapter(TEXT("pier")));
 TestTrue(TEXT("Sales add fame"),Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))>=30);
 // Step 3: pay once, then reward once.
 const double BeforePay=Sim->Money();const double Reward=Sim->Number(Sim->ChapterDefinition(TEXT("pier")),TEXT("reward"));
 TestTrue(TEXT("Pay step completes chapter"),Sim->AdvanceChapter(TEXT("pier")));
 TestEqual(TEXT("Donation and reward booked once"),Sim->Money(),BeforePay-150+Reward);
 TestFalse(TEXT("Completed chapter cannot repeat"),Sim->AdvanceChapter(TEXT("pier")));
 TestEqual(TEXT("No repeated reward"),Sim->Money(),BeforePay-150+Reward);
 TestTrue(TEXT("Next chapter opens"),Sim->IsChapterOpen(TEXT("prainha")));
 auto Comunidade=MakeShared<FJsonObject>();Comunidade->SetStringField(TEXT("kind"),TEXT("chapter"));Comunidade->SetStringField(TEXT("item"),TEXT("pier"));
 TestEqual(TEXT("Campaign chapter mission is reachable"),Sim->MissionAmount(Comunidade),1);
 TSharedPtr<FJsonObject> Saved;FString Text;FFileHelper::LoadFileToString(Text,*(Sim->SaveDirectory/TEXT("slot1.json")));FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Saved);
 TestEqual(TEXT("Chapter step persisted"),int32(Sim->Number(Sim->Object(Sim->Object(Saved,TEXT("prog")),TEXT("ch")),TEXT("pier"))),3);
 // Grand Hotel night: only when owned, booked once with the original rates.
 TestFalse(TEXT("No hotel night before purchase"),Sim->Object(Sim->State,TEXT("prog"))->HasField(TEXT("hotel")) && Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("hotel"))->HasField(TEXT("rooms")));
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);
 const double Occupancy=Sim->HotelOccupancy();TestTrue(TEXT("Occupancy clamped"),Occupancy>=.15 && Occupancy<=.98);
 const double BeforeNight=Sim->Money();const int32 DayBefore=Sim->Number(Sim->State,TEXT("day"));Sim->Sleep();
 auto Hotel=Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("hotel"));const int32 Rooms=Sim->Number(Hotel,TEXT("rooms"));
 TestEqual(TEXT("Rooms from occupancy"),Rooms,int32(FMath::RoundToInt(32*Occupancy)));
 TestEqual(TEXT("Hotel night booked once with wage"),Sim->Money(),double(BeforeNight+Rooms*220.+FMath::RoundToDouble(Rooms*1.7*35)-900.-Wage));
 TestEqual(TEXT("Day advanced with hotel"),int32(Sim->Number(Sim->State,TEXT("day"))),DayBefore+1);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareCustomizationTest,"MareAlta.Migration.Customization",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareCustomizationTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Customization")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 Load(TEXT("definitions.json"),Sim->Definitions);Load(TEXT("default_save.json"),Sim->State);
 TestTrue(TEXT("Catalogue loads"),Sim->CustomSlot(TEXT("kiosk"),TEXT("banquetas")).IsValid());
 // Every slot of every place has exactly five tiers.
 const TArray<TSharedPtr<FJsonValue>>* Slots=nullptr;int32 SlotCount=0;
 if(Sim->Object(Sim->Object(Sim->CustomDefs(),TEXT("places")),TEXT("kiosk"))->TryGetArrayField(TEXT("slots"),Slots))for(const auto& V:*Slots){
  const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;TestTrue(TEXT("Slot has tiers"),V->AsObject()->TryGetArrayField(TEXT("tiers"),Tiers) && Tiers->Num()==5);++SlotCount;}
 TestTrue(TEXT("Kiosk has at least eight customizable objects"),SlotCount>=8);
 TestEqual(TEXT("Starting tier is Simples"),Sim->CustomTier(TEXT("kiosk"),TEXT("banquetas")),1);
 TestEqual(TEXT("Decor starts neutral"),Sim->KioskArrivalFactor(),1.0);
 TestEqual(TEXT("Tier prices grow"),Sim->CustomPrice(TEXT("kiosk"),TEXT("banquetas"),2),75.0);
 TestTrue(TEXT("Higher tier costs more"),Sim->CustomPrice(TEXT("kiosk"),TEXT("banquetas"),5)>Sim->CustomPrice(TEXT("kiosk"),TEXT("banquetas"),4));
 Sim->State->SetNumberField(TEXT("money"),50);
 TestFalse(TEXT("Cannot buy without money"),Sim->BuyCustom(TEXT("kiosk"),TEXT("banquetas"),2));
 TestEqual(TEXT("Refused purchase keeps tier"),Sim->CustomTier(TEXT("kiosk"),TEXT("banquetas")),1);
 Sim->State->SetNumberField(TEXT("money"),10000);
 TestFalse(TEXT("Table decor needs the tables expansion"),Sim->BuyCustom(TEXT("kiosk"),TEXT("mesas"),2));
 TestTrue(TEXT("Buy stools tier 3"),Sim->BuyCustom(TEXT("kiosk"),TEXT("banquetas"),3));
 TestEqual(TEXT("Charged once"),Sim->Money(),10000-180.0);
 TestEqual(TEXT("Tier selected"),Sim->CustomTier(TEXT("kiosk"),TEXT("banquetas")),3);
 TestTrue(TEXT("Back to Simples is free"),Sim->BuyCustom(TEXT("kiosk"),TEXT("banquetas"),1));
 TestTrue(TEXT("Re-using an owned tier is free"),Sim->BuyCustom(TEXT("kiosk"),TEXT("banquetas"),3));
 TestEqual(TEXT("No double charge"),Sim->Money(),10000-180.0);
 TestEqual(TEXT("Comfort from stools"),Sim->PlaceComfort(TEXT("kiosk")),2.0);
 TestTrue(TEXT("Decor brings more customers"),Sim->KioskArrivalFactor()>1.0);
 TestTrue(TEXT("Counter tier speeds the attendant"),Sim->BuyCustom(TEXT("kiosk"),TEXT("balcao"),5) && FMath::IsNearlyEqual(Sim->KioskServiceSpeed(),1.4,1e-6));
 // Saved and reloaded.
 TSharedPtr<FJsonObject> Saved;FString Text;FFileHelper::LoadFileToString(Text,*(Sim->SaveDirectory/TEXT("slot1.json")));FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Saved);
 TestEqual(TEXT("Tier persists"),int32(Sim->Number(Sim->Object(Sim->Object(Sim->Object(Saved,TEXT("custom")),TEXT("kiosk")),TEXT("banquetas")),TEXT("tier"))),3);
 // Kiosk must be closed to change furniture.
 Sim->CreateCompany(TEXT("Teste"));Sim->State->SetNumberField(TEXT("minutes"),600);Sim->SetOpen(true);
 TestFalse(TEXT("Open kiosk refuses decor change"),Sim->BuyCustom(TEXT("kiosk"),TEXT("iluminacao"),2));
 // Recipes: price and demand grow, upgrade charged once, max level.
 const double Base=Sim->DishPrice(TEXT("coco_gelado"));TestEqual(TEXT("Base coconut price"),Base,12.0);
 const double Cost=Sim->RecipeUpgradeCost(TEXT("coco_gelado"));TestEqual(TEXT("First recipe upgrade cost"),Cost,144.0);
 const double Money=Sim->Money();TestTrue(TEXT("Upgrade recipe"),Sim->UpgradeRecipe(TEXT("coco_gelado")));
 TestEqual(TEXT("Recipe charged"),Sim->Money(),Money-Cost);
 TestEqual(TEXT("Recipe raises the price"),Sim->DishPrice(TEXT("coco_gelado")),15.0);
 TestTrue(TEXT("Better recipe sells more"),Sim->DishDemand(TEXT("coco_gelado"))>Sim->DishDemand(TEXT("suco")));
 for(int32 I=0;I<3;++I)Sim->UpgradeRecipe(TEXT("coco_gelado"));
 TestEqual(TEXT("Max recipe level"),Sim->RecipeLevel(TEXT("coco_gelado")),5);
 TestFalse(TEXT("No upgrade past level 5"),Sim->UpgradeRecipe(TEXT("coco_gelado")));
 TestFalse(TEXT("Locked product recipe refused"),Sim->UpgradeRecipe(TEXT("caipirinha")));
 // A sale pays the recipe price plus the comfort tip.
 const FString Order=Sim->AddOrder(TEXT("Ana"),{TEXT("coco_gelado")});
 const double BeforeSale=Sim->Money();Sim->Pickup(TEXT("coco_gelado"));
 TestTrue(TEXT("Deliver upgraded coconut"),Sim->Deliver(Order,TEXT("coco_gelado")));
 const double Price=Sim->DishPrice(TEXT("coco_gelado"));
 TestEqual(TEXT("Sale = recipe price + tip"),Sim->Money(),BeforeSale+Price+FMath::RoundToDouble(Price*Sim->KioskTipRate()*100)/100);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
#endif
