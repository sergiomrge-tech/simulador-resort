#include "MareSimulation.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "MareGameRoom.h"
#include "MareStaysWorld.h"
#include "Engine/GameInstance.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
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
 // Suites are paid at the reception (MareStays); the night books the restaurant of real stays and the crew.
 TestEqual(TEXT("No guests checked in yet"),Rooms,0);
 TestEqual(TEXT("Hotel night booked once with wage"),Sim->Money(),double(BeforeNight+FMath::RoundToDouble(Rooms*1.7*35)-900.-Wage));
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareExpansionOpsTest,"MareAlta.Migration.ExpansionOperations",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareExpansionOpsTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/ExpansionOps")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 Load(TEXT("definitions.json"),Sim->Definitions);Load(TEXT("default_save.json"),Sim->State);
 // Every place: five tiers per object.
 int32 Slots=0,Places=0;for(const auto& Pair:Sim->Object(Sim->CustomDefs(),TEXT("places"))->Values){++Places;const TArray<TSharedPtr<FJsonValue>>* Defs=nullptr;
  if(Pair.Value->AsObject()->TryGetArrayField(TEXT("slots"),Defs))for(const auto& V:*Defs){const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;
   TestTrue(TEXT("Five tiers"),V->AsObject()->TryGetArrayField(TEXT("tiers"),Tiers) && Tiers->Num()==5);++Slots;}}
 TestTrue(TEXT("All resort places customizable"),Places>=15 && Slots>=70);
 TestFalse(TEXT("Bar decor waits for the bar"),Sim->IsPlaceAvailable(TEXT("bar")));
 Sim->State->SetNumberField(TEXT("money"),100000);Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));
 TestFalse(TEXT("Locked place refuses purchase"),Sim->BuyCustom(TEXT("bar"),TEXT("carta"),2));
 for(const TCHAR* Id:{TEXT("bar"),TEXT("pousada"),TEXT("pool"),TEXT("passeios")})Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(Id,true);
 TestTrue(TEXT("Bar decor available"),Sim->IsPlaceAvailable(TEXT("bar")));
 // Hourly income: bar and pool book once per game hour, only while open.
 Sim->State->SetNumberField(TEXT("minutes"),600);double Before=Sim->Money();Sim->AdvanceMinutes(60);
 TestTrue(TEXT("Bar earns while open"),Sim->OpsToday(TEXT("bar"))>0 && Sim->OpsToday(TEXT("pool"))>0);
 TestEqual(TEXT("Hour booked into cash"),Sim->Money(),Before+Sim->OpsToday(TEXT("bar"))+Sim->OpsToday(TEXT("pool")));
 const double BarHour=Sim->OpsToday(TEXT("bar"));Sim->State->SetNumberField(TEXT("minutes"),600);Sim->AdvanceMinutes(60);
 TestEqual(TEXT("Same hour never booked twice"),Sim->OpsToday(TEXT("bar")),BarHour);
 const double Plain=Sim->HourlyIncome(TEXT("bar"));
 TestTrue(TEXT("Drinks menu upgrade"),Sim->BuyCustom(TEXT("bar"),TEXT("carta"),5));
 TestTrue(TEXT("Better bar earns more"),Sim->HourlyIncome(TEXT("bar"))>Plain*1.3);
 // Tours need the guide.
 Sim->State->SetNumberField(TEXT("minutes"),780);Sim->AdvanceMinutes(60);
 TestEqual(TEXT("No guide, no tour"),Sim->OpsToday(TEXT("passeios")),0.);
 TestTrue(TEXT("Hire guide"),Sim->HireStaff(TEXT("guia")));TestTrue(TEXT("Guide is hired"),Sim->HasStaff(TEXT("guia")));
 const int32 Seats=Sim->TourSeats(Sim->Object(Sim->State,TEXT("none")));TestTrue(TEXT("Boat upgrade"),Sim->BuyCustom(TEXT("passeios"),TEXT("barco"),5));
 TestEqual(TEXT("Bigger boat, more seats"),Sim->TourSeats(Sim->Object(Sim->State,TEXT("none"))),Seats+4);
 Sim->State->SetNumberField(TEXT("minutes"),840);Sim->AdvanceMinutes(60);
 TestTrue(TEXT("Boat tour departs at 14h"),Sim->OpsToday(TEXT("passeios"))>0);
 // Businesses: bought once, earn in their hours.
 TestFalse(TEXT("Business needs fame"),Sim->BuyBusiness(TEXT("sorveteria")));
 Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),100000);
 Before=Sim->Money();TestTrue(TEXT("Buy ice cream shop"),Sim->BuyBusiness(TEXT("sorveteria")));
 TestEqual(TEXT("Business charged once"),Sim->Money(),Before-900.);TestFalse(TEXT("Not twice"),Sim->BuyBusiness(TEXT("sorveteria")));
 Sim->State->SetNumberField(TEXT("minutes"),900);Sim->AdvanceMinutes(60);
 TestTrue(TEXT("Business earns"),Sim->OpsToday(TEXT("biz_sorveteria"))>0);
 // Pousada: rooms from expansions, rate from room upgrades, night booked at sleep.
 TestEqual(TEXT("Bungalow plus two pool rooms"),Sim->PousadaRooms(),3);
 const double Rate=Sim->PousadaRate();TestTrue(TEXT("Better beds"),Sim->BuyCustom(TEXT("pousada"),TEXT("cama"),3));
 TestEqual(TEXT("Beds raise the nightly rate"),Sim->PousadaRate(),Rate+60);
 Sim->Sleep();auto Night=Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("pousada"));
 TestEqual(TEXT("Pousada night recorded"),int32(Sim->Number(Night,TEXT("rooms"))),3);
 // Home: comfort makes the player faster.
 TestEqual(TEXT("Plain home"),Sim->HomeSpeedFactor(),1.);TestTrue(TEXT("New bed"),Sim->BuyCustom(TEXT("home"),TEXT("cama"),5));
 TestTrue(TEXT("Rested player walks faster"),Sim->HomeSpeedFactor()>1.05);
 // Grand Hotel areas raise the hotel occupancy and suite rate.
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);const double Occ=Sim->HotelOccupancy();
 TestTrue(TEXT("Spa upgrade"),Sim->BuyCustom(TEXT("hotel_lazer"),TEXT("spa"),5));
 TestTrue(TEXT("Hotel decor fills rooms"),Sim->HotelOccupancy()>Occ || Occ>=.98);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareReputationHudTest,"MareAlta.Gameplay.ReputationHud",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareReputationHudTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/ReputationHud")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 // New game: no rooms yet, nothing sold, neutral 3-star average.
 TestEqual(TEXT("No rooms before the pousada"),Sim->RoomsTotal(),0);
 TestEqual(TEXT("Nothing sold yet"),Sim->ServedToday(),0);
 TestEqual(TEXT("Neutral stars"),Sim->Stars(),3.);
 // Sales today count from the day's starting mark, and the mark moves at the day close.
 Sim->State->SetNumberField(TEXT("ue_day_sales_start"),10);Sim->State->SetNumberField(TEXT("kiosk_n"),17);
 TestEqual(TEXT("Seven sold today"),Sim->ServedToday(),7);
 // Rooms occupied come from last night's pousada and hotel results.
 // Rooms occupied: live pousada stays plus last night's hotel suites.
 auto Room=MakeShared<FJsonObject>();Room->SetStringField(TEXT("id"),TEXT("pousada_0"));Room->SetStringField(TEXT("state"),TEXT("occupied"));
 Sim->Stays()->SetArrayField(TEXT("rooms"),{MakeShared<FJsonValueObject>(Room)});
 TestEqual(TEXT("Occupied rooms are the live stays"),Sim->RoomsOccupied(),1);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);
 TestEqual(TEXT("Hotel suites count"),Sim->RoomsTotal(),Sim->PousadaRooms()+32);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePousadaStaysTest,"MareAlta.Gameplay.PousadaStays",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePousadaStaysTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/PousadaStays")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("pousada"),true);
 Sim->SyncRooms();const int32 Rooms=Sim->PousadaRooms();
 TestTrue(TEXT("Pousada has rooms"),Rooms>=1);TestEqual(TEXT("All rooms start clean"),Sim->FreeCleanRooms(),Rooms);
 auto Queue=[&](){const TArray<TSharedPtr<FJsonValue>>* Q=nullptr;Sim->Stays()->TryGetArrayField(TEXT("queue"),Q);return Q?Q->Num():0;};
 auto Guest=[&](const FString& Id){const TArray<TSharedPtr<FJsonValue>>* Q=nullptr;Sim->Stays()->TryGetArrayField(TEXT("queue"),Q);
  if(Q)for(const auto& V:*Q)if(Sim->String(V->AsObject(),TEXT("id"))==Id)return V->AsObject();return TSharedPtr<FJsonObject>();};
 // A greedy price is refused twice and the guest leaves; nothing is charged.
 const FString First=Sim->AddArrival();TestFalse(TEXT("Guest arrived"),First.IsEmpty());TestEqual(TEXT("Queue has one"),Queue(),1);
 const double Limit=Sim->Number(Guest(First),TEXT("limit"));double Offer=0;const double Before=Sim->Money();
 TestTrue(TEXT("Greedy ask countered"),Sim->Haggle(First,Limit*1.5,Offer)==UMareSimulation::EHaggle::Countered);
 TestTrue(TEXT("Counter offer stays under the limit"),Offer<=Limit);
 TestTrue(TEXT("Second greedy ask: guest leaves"),Sim->Haggle(First,Limit*1.5,Offer)==UMareSimulation::EHaggle::Left);
 TestEqual(TEXT("Queue empty after leaving"),Queue(),0);TestEqual(TEXT("Nothing charged"),Sim->Money(),Before);
 // Taking the offer checks in and charges every night once.
 const FString Second=Sim->AddArrival();auto G=Guest(Second);const double Rate=Sim->Number(G,TEXT("offer"));const int32 Nights=Sim->Number(G,TEXT("nights"));
 TestTrue(TEXT("Accept the offer"),Sim->AcceptOffer(Second));
 TestEqual(TEXT("All nights charged at check-in"),Sim->Money(),Before+Rate*Nights);
 TestEqual(TEXT("Room taken"),Sim->FreeCleanRooms(),Rooms-1);TestEqual(TEXT("Occupied count"),Sim->RoomsOccupied(),1);
 // Nights pass; the check-out leaves a rating and a dirty room with three tasks; no extra charge.
 const TArray<TSharedPtr<FJsonValue>>* Ratings=nullptr;Sim->State->TryGetArrayField(TEXT("ratings"),Ratings);const int32 RatingsBefore=Ratings?Ratings->Num():0;
 const double Paid=Sim->Money();for(int32 I=0;I<Nights;++I)Sim->StaysNight();
 TestEqual(TEXT("Nights do not charge again"),Sim->Money(),Paid);
 Sim->State->TryGetArrayField(TEXT("ratings"),Ratings);TestEqual(TEXT("Check-out rated"),Ratings?Ratings->Num():0,FMath::Min(40,RatingsBefore+1));
 TestEqual(TEXT("Room dirty"),Sim->FreeCleanRooms(),Rooms-1);
 TestFalse(TEXT("Unknown task"),Sim->CleanRoom(TEXT("pousada_0"),TEXT("window")));
 TestTrue(TEXT("Make the bed"),Sim->CleanRoom(TEXT("pousada_0"),TEXT("bed")));TestFalse(TEXT("Bed only once"),Sim->CleanRoom(TEXT("pousada_0"),TEXT("bed")));
 TestTrue(TEXT("Towels"),Sim->CleanRoom(TEXT("pousada_0"),TEXT("towels")));TestTrue(TEXT("Trash"),Sim->CleanRoom(TEXT("pousada_0"),TEXT("trash")));
 TestEqual(TEXT("Room free again"),Sim->FreeCleanRooms(),Rooms);
 // The maid cleans dirty rooms by the hour.
 const FString Third=Sim->AddArrival();Sim->AcceptOffer(Third);
 for(int32 I=0;I<6;++I)Sim->StaysNight();
 TestEqual(TEXT("Dirty again"),Sim->FreeCleanRooms(),Rooms-1);
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("camareira"),true);Sim->StaysHour(9);
 TestEqual(TEXT("Maid cleaned the room"),Sim->FreeCleanRooms(),Rooms);
 // Grand Hotel: 32 suites, five-star rates, the hotel desk checks guests in after two hours, housekeeping cleans.
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);Sim->SyncRooms();
 TestEqual(TEXT("Hotel suites"),Sim->FreeCleanRooms(TEXT("hotel")),32);TestEqual(TEXT("Pousada untouched"),Sim->FreeCleanRooms(),Rooms);
 TestTrue(TEXT("Hotel rate above the pousada"),Sim->StayRate(TEXT("hotel"))>Sim->StayRate(TEXT("pousada")));
 const FString Vip=Sim->AddArrival(TEXT("hotel"));TestFalse(TEXT("VIP arrived"),Vip.IsEmpty());
 Sim->StaysHour(9);TestEqual(TEXT("Desk waits two hours"),Sim->FreeCleanRooms(TEXT("hotel")),32);
 Sim->State->SetNumberField(TEXT("minutes"),Sim->Number(Sim->State,TEXT("minutes"))+130);Sim->StaysHour(9);
 TestEqual(TEXT("Hotel desk checked the VIP in"),Sim->FreeCleanRooms(TEXT("hotel")),31);
 for(int32 I=0;I<8;++I)Sim->StaysNight();
 TestEqual(TEXT("Housekeeping freed the suite"),Sim->FreeCleanRooms(TEXT("hotel")),32);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareHotelReceptionLineTest,"MareAlta.Gameplay.HotelReceptionLine",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareHotelReceptionLineTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/HotelReceptionLine")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 // Lobby layout (tools/ue58/hotel_lobby_shell.py, Content/Data/hotel_lobby.json): desk around (-1390,6470), furniture
 // inside x -3570..-630, y 5840..6840, main door to the south (-Y) at x -2100, lifts on the north wall.
 FMareStayLine Line;
 if(!TestTrue(TEXT("Hotel reception line in the data"),UMareStaysWorld::LineFor(Sim,TEXT("hotel"),Line))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 TestTrue(TEXT("Line at the lobby desk"),FVector::Dist2D(Line.Desk,FVector(-1390,6470,0))<200);
 TestTrue(TEXT("Line grows towards the entrance"),Line.Front.Y<-.99);
 const FVector Staff[]={FVector(-1390,6565,0),FVector(-1390,6330,0)};   // receptionist and the chatting guest (MareVillageWorld)
 for(int32 I=0;I<3;++I){const FVector Spot=Line.Spot(I);
  TestTrue(FString::Printf(TEXT("Spot %d inside the lobby"),I),Spot.X>-3570 && Spot.X<-630 && Spot.Y>5840 && Spot.Y<6840);
  TestTrue(FString::Printf(TEXT("Spot %d in front of the counter"),I),Spot.Y<Line.Desk.Y-100);
  for(const FVector& Other:Staff)TestTrue(FString::Printf(TEXT("Spot %d clear of the ambient people"),I),FVector::Dist2D(Spot,Other)>80);}
 TestTrue(TEXT("Exit outside the main door"),Line.Exit.Y<5600 && FMath::Abs(Line.Exit.X+2100)<150);
 TestEqual(TEXT("Two elevator doors"),Line.Elevators.Num(),2);
 for(const FVector& Lift:Line.Elevators)TestTrue(TEXT("Elevator behind the desk wall"),Lift.Y>6600 && Lift.X<-2400);
 FMareStayLine Pousada;TestTrue(TEXT("Pousada line still in the data"),UMareStaysWorld::LineFor(Sim,TEXT("pousada"),Pousada));
 TestEqual(TEXT("Pousada has no elevators"),Pousada.Elevators.Num(),0);
 // Hotel closed: no VIP shows up at the lobby.
 TestTrue(TEXT("No hotel arrival before the purchase"),Sim->AddArrival(TEXT("hotel")).IsEmpty());
 TestEqual(TEXT("Empty hotel line"),UMareStaysWorld::QueueOf(Sim,TEXT("hotel")).Num(),0);
 // Hotel open: a line of three, separate from the pousada one.
 Sim->State->SetNumberField(TEXT("money"),1000);Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("pousada"),true);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);Sim->SyncRooms();
 // Arrivals respect the opening hours (10:00-20:00): none at night or early morning.
 for(int32 Hour:{0,6,9,20,23})Sim->StaysHour(Hour);
 TestEqual(TEXT("No arrivals outside the reception hours"),UMareStaysWorld::QueueOf(Sim,TEXT("hotel")).Num(),0);
 TArray<FString> Vips;for(int32 I=0;I<3;++I)Vips.Add(Sim->AddArrival(TEXT("hotel")));
 TestFalse(TEXT("Third VIP in line"),Vips[2].IsEmpty());
 TestTrue(TEXT("Hotel line holds three"),Sim->AddArrival(TEXT("hotel")).IsEmpty());
 const auto HotelLine=UMareStaysWorld::QueueOf(Sim,TEXT("hotel"));TestEqual(TEXT("Hotel queue"),HotelLine.Num(),3);
 TestEqual(TEXT("Queue order kept"),Sim->String(HotelLine[0],TEXT("id")),Vips[0]);
 TestEqual(TEXT("Pousada line apart"),UMareStaysWorld::QueueOf(Sim,TEXT("pousada")).Num(),0);
 const FString Backpacker=Sim->AddArrival(TEXT("pousada"));TestFalse(TEXT("Pousada still receives"),Backpacker.IsEmpty());
 TestEqual(TEXT("Pousada guest not in the lobby"),UMareStaysWorld::QueueOf(Sim,TEXT("hotel")).Num(),3);
 // Check-in: the first VIP leaves the line (walks to the elevators) and owns a suite.
 const int32 Nights=Sim->Number(HotelLine[0],TEXT("nights"),1);
 TestTrue(TEXT("Check-in at the hotel desk"),Sim->AcceptOffer(Vips[0]));
 TestEqual(TEXT("Line moved up"),UMareStaysWorld::QueueOf(Sim,TEXT("hotel")).Num(),2);
 TestEqual(TEXT("Suite taken"),Sim->FreeCleanRooms(TEXT("hotel")),31);
 // Night: the reception line empties; the stay counts down and the check-out leaves through the lobby next morning.
 bool bLeft=false;
 for(int32 I=0;I<Nights;++I){Sim->StaysNight();
  TestEqual(TEXT("Line empty at night"),UMareStaysWorld::QueueOf(Sim,TEXT("hotel")).Num(),0);
  const TArray<TSharedPtr<FJsonValue>>* Out=nullptr;
  if(Sim->Stays()->TryGetArrayField(TEXT("departures"),Out))for(const auto& V:*Out)bLeft|=Sim->String(V->AsObject(),TEXT("id"))==Vips[0];
  TestEqual(TEXT("Still a guest before the last night"),bLeft,I==Nights-1);}
 TestEqual(TEXT("Suite free after the check-out"),Sim->FreeCleanRooms(TEXT("hotel")),32);
 TestFalse(TEXT("No pousada departures"),Sim->TakeDeparture(TEXT("pousada")).IsValid());
 const auto Leaving=Sim->TakeDeparture(TEXT("hotel"));
 TestTrue(TEXT("The VIP walks out"),Leaving.IsValid() && Sim->String(Leaving,TEXT("id"))==Vips[0] && Sim->String(Leaving,TEXT("place"))==TEXT("hotel"));
 TestFalse(TEXT("Only once"),Sim->TakeDeparture(TEXT("hotel")).IsValid());
 // Whoever is still upstairs at 13:00 has already gone.
 Sim->Stays()->SetArrayField(TEXT("departures"),{MakeShared<FJsonValueObject>(Leaving)});Sim->StaysHour(13);
 TestFalse(TEXT("Departures cleared after the morning"),Sim->TakeDeparture(TEXT("hotel")).IsValid());
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePricesTest,"MareAlta.Gameplay.PricesAndFame",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePricesTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/PricesAndFame")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 const FString Coco=TEXT("coco_gelado");const double Fair=Sim->DishPrice(Coco),FairDemand=Sim->DishDemand(Coco);
 TestEqual(TEXT("Sale price starts fair"),Sim->SalePrice(Coco),Fair);TestEqual(TEXT("Fair ratio"),Sim->PriceRatio(Coco),1.);
 TestTrue(TEXT("Set a higher price"),Sim->SetSalePrice(Coco,Fair*1.3));TestTrue(TEXT("Expensive sells less"),Sim->DishDemand(Coco)<FairDemand*.6);
 Sim->SetSalePrice(Coco,Fair*.8);TestTrue(TEXT("Cheap sells more"),Sim->DishDemand(Coco)>FairDemand*1.4);
 Sim->SetSalePrice(Coco,Fair*10);TestEqual(TEXT("Clamped at double"),Sim->SalePrice(Coco),FMath::RoundToDouble(Fair*2));
 Sim->SetSalePrice(Coco,1);TestEqual(TEXT("Clamped at half"),Sim->SalePrice(Coco),FMath::RoundToDouble(Fair*.5));
 const double Start=Sim->KioskArrivalFactor();
 Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),1e6);
 TestTrue(TEXT("Fame brings more customers"),Sim->KioskArrivalFactor()>Start*1.2);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePoolPhysicsTest,"MareAlta.Gameplay.PoolPhysics",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePoolPhysicsTest::RunTest(const FString& Parameters)
{
 auto Room=NewObject<UMareGameRoom>();Room->AddToRoot();namespace R=MarePool;
 // Break: everything stops within 20 s and stays on the table.
 Room->Rack();Room->Shoot(0,5.5);double T=0;while(Room->Step(1./30) && T<20)T+=1./30;
 TestFalse(TEXT("Balls stop after the break"),Room->Moving());TestTrue(TEXT("Break settles in time"),T<20);
 bool bInside=true;for(const auto& B:Room->Balls)if(!B.bIn)bInside&=FMath::Abs(B.P.X)<=R::L/2+.001 && FMath::Abs(B.P.Y)<=R::W/2+.001;
 TestTrue(TEXT("Every ball on the cloth"),bInside);
 // A straight shot pockets a ball sitting in front of the corner pocket; the shooter keeps the turn.
 Room->Rack();for(int32 I=1;I<16;++I)Room->Balls[I].bIn=true;
 Room->Balls[3].bIn=false;Room->Balls[3].P=FVector2D(R::L/2-.15,R::W/2-.15);
 const FVector2D ToPocket=(FVector2D(R::L/2,R::W/2)-Room->Balls[3].P).GetSafeNormal();Room->Balls[0].P=Room->Balls[3].P-ToPocket*.5;
 Room->Shoot(FMath::Atan2(ToPocket.Y,ToPocket.X),2.5);
 while(Room->Step(1./30)){}
 TestTrue(TEXT("Ball 3 potted"),Room->Balls[3].bIn);Room->ResolveShot();
 TestEqual(TEXT("Player scored"),Room->Score[0],1);TestEqual(TEXT("Player keeps the turn"),Room->Turn,0);
 // The 8 before three balls loses; the cue ball in a pocket passes the turn and is respotted.
 Room->Rack();Room->PottedThisShot={8};Room->ResolveShot();TestEqual(TEXT("Early 8 loses"),Room->Winner,1);
 Room->Rack();Room->Balls[0].bIn=true;Room->PottedThisShot={0};Room->ResolveShot();TestEqual(TEXT("Scratch passes the turn"),Room->Turn,1);TestFalse(TEXT("Cue ball back"),Room->Balls[0].bIn);
 Room->Rack();Room->Score[0]=3;Room->PottedThisShot={5};Room->ResolveShot();TestEqual(TEXT("Fourth ball wins"),Room->Winner,0);
 // The guest finds a clean pot when one exists.
 Room->Rack();for(int32 I=1;I<16;++I)Room->Balls[I].bIn=true;Room->Balls[2].bIn=false;Room->Balls[2].P=FVector2D(.6,.1);Room->Balls[0].P=FVector2D(-.2,.05);Room->Turn=1;
 double Angle=0,Speed=0;Room->PlanGuestShot(Angle,Speed,7);Room->Shoot(Angle,Speed);while(Room->Step(1./30)){}
 TestTrue(TEXT("Guest hits a ball"),Room->Balls[2].P!=FVector2D(.6,.1) || Room->Balls[2].bIn);
 Room->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareSaveSlotsTest,"MareAlta.Saves.Slots",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareSaveSlotsTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 const FString Dir=FPaths::ProjectSavedDir()/TEXT("Automation/SaveSlots")/FGuid::NewGuid().ToString(EGuidFormats::Digits);Sim->SaveDirectory=Dir;
 auto ReadFile=[](const FString& Path){TSharedPtr<FJsonObject> Result;FString Text;FFileHelper::LoadFileToString(Text,*Path);FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);return Result;};
 auto Legacy=ReadFile(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"));Sim->Definitions=ReadFile(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"));
 if(!TestTrue(TEXT("Default save available"),Legacy.IsValid() && Sim->Definitions.IsValid())){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 // A profile from before the slots: only slot1.json, no index.
 Legacy->SetNumberField(TEXT("day"),7);Legacy->SetNumberField(TEXT("money"),1234);FString LegacyText;
 FJsonSerializer::Serialize(Legacy.ToSharedRef(),TJsonWriterFactory<>::Create(&LegacyText));IFileManager::Get().MakeDirectory(*Dir,true);
 FFileHelper::SaveStringToFile(LegacyText,*(Dir/TEXT("slot1.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
 TestEqual(TEXT("Legacy save becomes slot 1"),Sim->LastSlot(),1);
 TestTrue(TEXT("Slot index created by the migration"),FPaths::FileExists(Dir/TEXT("slots.json")));
 const FMareSlotInfo First=Sim->SlotInfo(1);
 TestTrue(TEXT("Slot 1 listed"),First.bExists);TestEqual(TEXT("Slot 1 day"),First.Day,7);TestEqual(TEXT("Slot 1 money"),First.Money,1234.0);
 TestFalse(TEXT("Slot 2 empty"),Sim->SlotInfo(2).bExists);TestFalse(TEXT("Empty slot cannot load"),Sim->LoadSlot(3));
 TestTrue(TEXT("Load legacy slot"),Sim->LoadSlot(1));TestEqual(TEXT("Legacy state loaded"),UMareSimulation::Number(Sim->State,TEXT("day")),7.0);
 // New game in slot 2, then two saves: the second keeps the first one as .bak.
 TestTrue(TEXT("New game in slot 2"),Sim->NewGame(2));
 TestEqual(TEXT("Slot 2 active"),Sim->ActiveSlot,2);TestEqual(TEXT("Index points to slot 2"),Sim->LastSlot(),2);
 TestEqual(TEXT("New game starts with the arrival"),UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),-1),0.0);
 Sim->State->SetNumberField(TEXT("day"),3);Sim->State->SetNumberField(TEXT("money"),500);TestTrue(TEXT("Save slot 2"),Sim->Save());
 Sim->State->SetNumberField(TEXT("money"),600);TestTrue(TEXT("Save slot 2 again"),Sim->Save());
 TestTrue(TEXT("Backup created"),FPaths::FileExists(Dir/TEXT("slot2.json.bak")));
 TestEqual(TEXT("Backup holds the previous save"),UMareSimulation::Number(ReadFile(Dir/TEXT("slot2.json.bak")),TEXT("money")),500.0);
 TestEqual(TEXT("Slot 1 untouched"),UMareSimulation::Number(ReadFile(Dir/TEXT("slot1.json")),TEXT("day")),7.0);
 Sim->Sleep();TestEqual(TEXT("Day close autosaves the active slot"),UMareSimulation::Number(ReadFile(Dir/TEXT("slot2.json")),TEXT("day")),4.0);
 // Another session reads the slot; a damaged file falls back to its backup.
 auto Other=NewObject<UMareSimulation>(Instance);Other->AddToRoot();Other->SaveDirectory=Dir;Other->Definitions=Sim->Definitions;
 TestEqual(TEXT("Last slot remembered"),Other->LastSlot(),2);
 TestTrue(TEXT("Load slot 2"),Other->LoadSlot(2));TestEqual(TEXT("Slot 2 day"),UMareSimulation::Number(Other->State,TEXT("day")),4.0);
 FFileHelper::SaveStringToFile(FString(TEXT("{broken")),*(Dir/TEXT("slot2.json")));
 TestTrue(TEXT("Damaged slot loads its backup"),Other->LoadSlot(2));TestEqual(TEXT("Backup state"),UMareSimulation::Number(Other->State,TEXT("money")),600.0);
 // Starting over in an occupied slot keeps the old profile as .bak.
 TestTrue(TEXT("New game over slot 1"),Other->NewGame(1));
 TestEqual(TEXT("Old slot 1 kept as backup"),UMareSimulation::Number(ReadFile(Dir/TEXT("slot1.json.bak")),TEXT("day")),7.0);
 Other->RemoveFromRoot();Sim->RemoveFromRoot();Instance->RemoveFromRoot();
 IFileManager::Get().DeleteDirectory(*Dir,false,true);return true;
}
#endif

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBarDrinksTest,"MareAlta.Gameplay.BarDrinks",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBarDrinksTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/BarDrinks")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);Sim->State->SetNumberField(TEXT("minutes"),600);
 auto Orders=[&](){const TArray<TSharedPtr<FJsonValue>>* O=nullptr;Sim->Bar()->TryGetArrayField(TEXT("orders"),O);return O?O->Num():0;};
 // Mixing is by the set of ingredients: order is free, repeats and extras are no recipe.
 TestEqual(TEXT("Caipirinha in any order"),Sim->MixRecipe({TEXT("gelo"),TEXT("acucar"),TEXT("cachaca"),TEXT("limao")}),FString(TEXT("caipirinha")));
 TestTrue(TEXT("Extra ingredient is nothing"),Sim->MixRecipe({TEXT("gelo"),TEXT("acucar"),TEXT("cachaca"),TEXT("limao"),TEXT("morango")}).IsEmpty());
 TestTrue(TEXT("Repeated ingredient is nothing"),Sim->MixRecipe({TEXT("gelo"),TEXT("gelo"),TEXT("cachaca"),TEXT("limao")}).IsEmpty());
 // Closed until bought.
 TestTrue(TEXT("No orders before the bar is bought"),Sim->AddBarOrder().IsEmpty());
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("bar"),true);
 TestTrue(TEXT("Starting menu"),Sim->IsRecipeKnown(TEXT("caipirinha")) && !Sim->IsRecipeKnown(TEXT("mojito")));
 const double Lime=Sim->Number(Sim->Object(Sim->Bar(),TEXT("stock")),TEXT("limao"));TestTrue(TEXT("Shelf starts with stock"),Lime>0);
 // Right drink: paid with a tip, ingredients used, guest gone.
 const FString A=Sim->AddBarOrder(TEXT("caipirinha"));TestFalse(TEXT("Guest sits down"),A.IsEmpty());
 double Before=Sim->Money();
 auto R=Sim->ServeBar(A,{TEXT("cachaca"),TEXT("limao"),TEXT("acucar"),TEXT("gelo")});
 TestTrue(TEXT("Caipirinha served"),R.bServed && !R.bDiscovered);TestTrue(TEXT("Paid at least the price"),Sim->Money()-Before>=Sim->DrinkPrice(TEXT("caipirinha")));
 TestEqual(TEXT("Lime used"),Sim->Number(Sim->Object(Sim->Bar(),TEXT("stock")),TEXT("limao")),Lime-1);TestEqual(TEXT("Order closed"),Orders(),0);
 // Wrong drink: discovered anyway (fame), but not paid and the guest keeps waiting.
 const FString B=Sim->AddBarOrder(TEXT("caipirinha"));Before=Sim->Money();
 const double FameBefore=Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));
 R=Sim->ServeBar(B,{TEXT("rum"),TEXT("limao"),TEXT("hortela"),TEXT("acucar"),TEXT("agua_gas")});
 TestTrue(TEXT("Mojito discovered"),R.bDiscovered && R.Recipe==TEXT("mojito") && Sim->IsRecipeKnown(TEXT("mojito")));
 TestFalse(TEXT("Wrong drink not served"),R.bServed);TestEqual(TEXT("Wrong drink not paid"),Sim->Money(),Before);TestEqual(TEXT("Guest still waiting"),Orders(),1);
 TestTrue(TEXT("Discovery gives fame"),Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))>FameBefore);
 // Nonsense mix is used up and pays nothing.
 R=Sim->ServeBar(B,{TEXT("leite_condensado"),TEXT("agua_gas")});TestTrue(TEXT("Nonsense is no drink"),R.Recipe.IsEmpty() && !R.bServed);
 // A surprise accepts any recipe.
 const FString C=Sim->AddBarOrder(TEXT("surpresa"));
 R=Sim->ServeBar(C,{TEXT("limao"),TEXT("acucar"),TEXT("agua_gas"),TEXT("gelo")});TestTrue(TEXT("Surprise accepts limonada"),R.bServed);
 // Restock costs money and fills the shelf; with no money it is refused.
 const double Cost=Sim->BarRestockCost();TestTrue(TEXT("Restock has a cost"),Cost>0);Before=Sim->Money();
 TestTrue(TEXT("Restock bought"),Sim->RestockBar());TestEqual(TEXT("Restock charged"),Sim->Money(),Before-Cost);
 TestEqual(TEXT("Shelf full"),Sim->BarRestockCost(),0.);
 // Out of an ingredient: nothing is used and the guest waits.
 Sim->Object(Sim->Bar(),TEXT("stock"))->SetNumberField(TEXT("cachaca"),0);
 R=Sim->ServeBar(B,{TEXT("cachaca"),TEXT("limao"),TEXT("acucar"),TEXT("gelo")});TestFalse(TEXT("No cachaça, no drink"),R.bServed || !R.Recipe.IsEmpty());
 TestEqual(TEXT("Lime kept when the mix is refused"),Sim->Number(Sim->Object(Sim->Bar(),TEXT("stock")),TEXT("limao")),10.);
 Sim->Object(Sim->Bar(),TEXT("stock"))->SetNumberField(TEXT("cachaca"),10);
 // Hourly: the bartender serves known drinks; the waiting guest was a caipirinha.
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("bartender"),true);Before=Sim->Money();
 Sim->BarHour(11);TestTrue(TEXT("Bartender served and was paid"),Sim->Money()>Before);
 // Impatient guests leave; nobody stays after closing.
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("bartender"),false);
 Sim->State->SetNumberField(TEXT("minutes"),1400);Sim->BarHour(23);TestEqual(TEXT("Bar empty after closing"),Orders(),0);
 TestTrue(TEXT("No orders while closed"),Sim->AddBarOrder().IsEmpty());
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
