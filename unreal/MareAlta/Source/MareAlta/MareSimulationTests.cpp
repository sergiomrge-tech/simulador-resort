#include "MareSimulation.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "MareGameRoom.h"
#include "MareTableTennis.h"
#include "MareStaysWorld.h"
#include "MarePerson.h"
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
 {// VIP: extra tip on each item, fame once the whole order is served, ticket fields saved with the order.
  const FString Vip=Sim->AddOrder(TEXT("Teste"),{TEXT("suco")});TestTrue(TEXT("VIP order"),Sim->MakeVip(Vip,0,1));
  auto Order=UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("ue_orders")),Vip);
  TestFalse(TEXT("VIP title and request"),UMareSimulation::String(Order,TEXT("vip_title")).IsEmpty() || UMareSimulation::String(Order,TEXT("request")).IsEmpty());
  const double VipCash=Sim->Money();const double Xp=UMareSimulation::Number(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));
  UMareSimulation::Object(Sim->State,TEXT("company"))->SetStringField(TEXT("carry"),TEXT("suco"));TestTrue(TEXT("VIP served"),Sim->Deliver(Vip,TEXT("suco")));
  TestTrue(TEXT("VIP pays more than the price"),Sim->Money()-VipCash>=Sim->SalePrice(TEXT("suco"))*1.5);
  TestTrue(TEXT("VIP adds fame"),UMareSimulation::Number(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))-Xp>=8);}
 Sim->State->SetNumberField(TEXT("money"),150);
 TestFalse(TEXT("Starting cash cannot hire"),Sim->HireAttendant());TestTrue(TEXT("Hire refusal names the cost"),Sim->LastMessage.Contains(TEXT("R$ 240")));
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
 TestEqual(TEXT("Decor starts neutral"),Sim->KioskArrivalFactor()/Sim->EventDemand(),1.0);   // season and event demand apart
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
 // With the guide, buyers of the 14h boat come from 11h on and he sells the tickets; the boat leaves at 14h.
 Sim->State->SetNumberField(TEXT("minutes"),660);for(int32 I=0;I<4;++I)Sim->AdvanceMinutes(60);
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
 Room->bBreakShot=false;Room->Balls[3].bIn=false;Room->Balls[3].P=FVector2D(R::L/2-.15,R::W/2-.15);
 const FVector2D ToPocket=(FVector2D(R::L/2,R::W/2)-Room->Balls[3].P).GetSafeNormal();Room->Balls[0].P=Room->Balls[3].P-ToPocket*.5;
 Room->Shoot(FMath::Atan2(ToPocket.Y,ToPocket.X),2.5);
 while(Room->Step(1./30)){}
 TestTrue(TEXT("Ball 3 potted"),Room->Balls[3].bIn);Room->ResolveShot();
 TestEqual(TEXT("Open table: the pot gives solids"),Room->Group[0],1);TestEqual(TEXT("Player keeps the turn"),Room->Turn,0);
 // Eight-ball: the 8 before clearing loses; the cue ball in a pocket passes the turn with ball in hand; the 8 after
 // the group is cleared wins.
 Room->Rack();Room->bBreakShot=false;Room->Balls[8].bIn=true;Room->FirstHit=8;Room->PottedThisShot={8};Room->ResolveShot();TestEqual(TEXT("Early 8 loses"),Room->Winner,1);
 Room->Rack();Room->bBreakShot=false;Room->Balls[0].bIn=true;Room->FirstHit=3;Room->PottedThisShot={0};Room->ResolveShot();
 TestEqual(TEXT("Scratch passes the turn"),Room->Turn,1);TestFalse(TEXT("Cue ball back"),Room->Balls[0].bIn);TestTrue(TEXT("Ball in hand after a scratch"),Room->bBallInHand);
 Room->Rack();Room->bBreakShot=false;Room->Group[0]=1;Room->Group[1]=2;for(int32 I=1;I<=8;++I)Room->Balls[I].bIn=true;
 Room->FirstHit=8;Room->PottedThisShot={8};Room->ResolveShot();TestEqual(TEXT("The 8 after clearing wins"),Room->Winner,0);
 // The guest finds a clean pot when one exists.
 Room->Rack();for(int32 I=1;I<16;++I)Room->Balls[I].bIn=true;Room->Balls[2].bIn=false;Room->Balls[2].P=FVector2D(.6,.1);Room->Balls[0].P=FVector2D(-.2,.05);Room->Turn=1;Room->bBreakShot=false;
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBusinessShiftTest,"MareAlta.Gameplay.BusinessCounter",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBusinessShiftTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/BusinessCounter")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),5000);Sim->State->SetNumberField(TEXT("minutes"),12*60);
 // Every business in the counter data exists in the definitions and has three steps.
 for(const auto& Pair:Sim->Object(Sim->BusinessGames(),TEXT("businesses"))->Values){const FString Id(Pair.Key.ToView());
  if(!Sim->String(Pair.Value->AsObject(),TEXT("requires")).IsEmpty())continue;   // game-room machines need the expansion, not a business
  TestTrue(TEXT("Counter business defined: ")+Id,Sim->Object(Sim->Definitions,TEXT("businesses"))->HasField(Id));
  const TArray<TSharedPtr<FJsonValue>>* Steps=nullptr;TestTrue(TEXT("Three steps: ")+Id,Pair.Value->AsObject()->TryGetArrayField(TEXT("steps"),Steps) && Steps->Num()==3);}
 FString Reason;TestFalse(TEXT("Not owned: no counter task"),Sim->CanPlayBusiness(TEXT("sorveteria"),Reason));
 Sim->Object(Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"))->SetNumberField(TEXT("lvl"),1);
 TestTrue(TEXT("Owned and open: task available"),Sim->CanPlayBusiness(TEXT("sorveteria"),Reason));
 double Before=Sim->Money();const double Perfect=Sim->PlayBusiness(TEXT("sorveteria"),3);
 TestTrue(TEXT("Perfect task pays"),Perfect>0);TestEqual(TEXT("Booked"),Sim->Money(),Before+Perfect);
 TestFalse(TEXT("Once per hour"),Sim->CanPlayBusiness(TEXT("sorveteria"),Reason));TestEqual(TEXT("Second try pays nothing"),Sim->PlayBusiness(TEXT("sorveteria"),3),0.);
 Sim->State->SetNumberField(TEXT("minutes"),13*60);
 const double Miss=Sim->PlayBusiness(TEXT("sorveteria"),0);TestTrue(TEXT("Next hour available, fewer hits pay less"),Miss>0 && Miss<Perfect);
 Sim->State->SetNumberField(TEXT("minutes"),22*60);TestFalse(TEXT("Closed at night"),Sim->CanPlayBusiness(TEXT("sorveteria"),Reason));
 // Game-room machines: need the game room; pay their own base; night tokens between the token hours.
 TestFalse(TEXT("Foosball needs the game room"),Sim->CanPlayBusiness(TEXT("pebolim"),Reason));
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("salao_jogos"),true);Sim->State->SetNumberField(TEXT("minutes"),20*60);
 TestTrue(TEXT("Foosball open at night"),Sim->CanPlayBusiness(TEXT("pebolim"),Reason));
 Before=Sim->Money();const double Won=Sim->PlayBusiness(TEXT("pebolim"),3);TestTrue(TEXT("Foosball win pays the base x 2.2"),FMath::IsNearlyEqual(Won,FMath::RoundToDouble(30*2.2)));
 Before=Sim->Money();Sim->GameRoomHour(21);TestTrue(TEXT("Night tokens"),Sim->Money()>Before);
 Before=Sim->Money();Sim->State->SetNumberField(TEXT("minutes"),12*60);Sim->GameRoomHour(13);TestEqual(TEXT("No tokens at noon"),Sim->Money(),Before);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePoolDayUseTest,"MareAlta.Gameplay.PoolDayUse",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePoolDayUseTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/PoolDayUse")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));
 Sim->PoolHour(11);TestEqual(TEXT("Nothing before the pool is bought"),Sim->Number(Sim->Pool(),TEXT("dirt")),0.);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("pool"),true);
 const double CleanIncome=Sim->HourlyIncome(TEXT("pool"));TestEqual(TEXT("Clean pool"),Sim->PoolCleanliness(),1.);
 for(int32 Hour=11;Hour<=15;++Hour)Sim->PoolHour(Hour);
 TestTrue(TEXT("Leaves fall while open"),Sim->Number(Sim->Pool(),TEXT("dirt"))>=30);
 TestTrue(TEXT("Dirty pool earns less"),Sim->HourlyIncome(TEXT("pool"))<CleanIncome);
 while(Sim->Number(Sim->Pool(),TEXT("dirt"))>0)Sim->ScoopPool();
 TestFalse(TEXT("Nothing left to scoop"),Sim->ScoopPool());
 // Towels: put one on lounger 2 and collect it; a free lounger has nothing.
 Sim->Pool()->SetArrayField(TEXT("towels"),{MakeShared<FJsonValueNumber>(2)});
 TestTrue(TEXT("Towel lowers cleanliness"),Sim->PoolCleanliness()<1);
 TestFalse(TEXT("No towel on lounger 0"),Sim->CollectPoolTowel(0));TestTrue(TEXT("Towel collected"),Sim->CollectPoolTowel(2));
 TestEqual(TEXT("Clean again"),Sim->PoolCleanliness(),1.);
 // Popsicles: sold at once for the price each.
 Sim->Pool()->SetNumberField(TEXT("popsicles"),3);const double Before=Sim->Money();
 TestTrue(TEXT("Popsicles sold"),Sim->SellPopsicles());TestTrue(TEXT("Paid for three"),Sim->Money()-Before>=3*Sim->Number(Sim->PoolDefs(),TEXT("popsicle_price")));
 TestFalse(TEXT("Nobody asking now"),Sim->SellPopsicles());
 // Closing hour rates the pool: a dirty one gets a low mark.
 Sim->Pool()->SetNumberField(TEXT("dirt"),100);Sim->State->SetArrayField(TEXT("ratings"),{});
 Sim->PoolHour(18);const TArray<TSharedPtr<FJsonValue>>* Ratings=nullptr;Sim->State->TryGetArrayField(TEXT("ratings"),Ratings);
 TestTrue(TEXT("Dirty pool rated low at closing"),Ratings && Ratings->Num()==1 && (*Ratings)[0]->AsNumber()<=3.5);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareToursHandsOnTest,"MareAlta.Gameplay.ToursHandsOn",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareToursHandsOnTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/ToursHandsOn")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("passeios"),true);
 // Every tour has three guided stops.
 for(const FString& Id:Sim->TourIds()){const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;
  TestTrue(TEXT("Three stops: ")+Id,Sim->Object(Sim->ToursDefs(),TEXT("stops"))->TryGetArrayField(Id,Stops) && Stops->Num()==3);}
 // Buyers for the 14h boat arrive from 11h; the player sells at the booth.
 Sim->State->SetNumberField(TEXT("minutes"),660);Sim->AdvanceMinutes(60);
 TestTrue(TEXT("Buyers at the booth"),Sim->TourCount(TEXT("queue"),TEXT("barco"))>0);
 double Before=Sim->Money();const double StartCash=Before;const int32 Sold=Sim->SellTickets(TEXT("barco"));
 TestTrue(TEXT("Tickets sold"),Sold>0);TestEqual(TEXT("Tickets paid"),Sim->Money(),Before+Sold*Sim->TicketPrice(TEXT("barco")));
 TestEqual(TEXT("Queue empty after selling"),Sim->TourCount(TEXT("queue"),TEXT("barco")),0);
 TestEqual(TEXT("Cannot guide before departure"),Sim->GuideTour(TEXT("barco"),{0,0,0}),0.);
 // Departure hour: a perfect guided tour rates 5 and tips.
 Sim->State->SetNumberField(TEXT("minutes"),14*60+10);TestTrue(TEXT("Boarding at 14h"),Sim->IsTourBoarding(TEXT("barco")));
 Before=Sim->Money();TestEqual(TEXT("Perfect rating"),Sim->GuideTour(TEXT("barco"),{0,0,0}),5.);
 TestTrue(TEXT("Guided tour pays tip"),Sim->Money()>Before-Sim->Number(Sim->TourDef(TEXT("barco")),TEXT("cost")));
 TestTrue(TEXT("Tour profitable overall"),Sim->Money()>StartCash);TestEqual(TEXT("Guided"),Sim->TourStatus(TEXT("barco")),FString(TEXT("guided")));
 TestEqual(TEXT("Not twice"),Sim->GuideTour(TEXT("barco"),{0,0,0}),0.);
 // Nobody guides the 16h trail without a guide: cancelled and refunded.
 Sim->State->SetNumberField(TEXT("minutes"),780);for(int32 I=0;I<3;++I)Sim->AdvanceMinutes(60);
 const int32 TrailSold=Sim->SellTickets(TEXT("farol"));Before=Sim->Money();
 Sim->State->SetNumberField(TEXT("minutes"),16*60);Sim->AdvanceMinutes(60);
 if(TrailSold>0){TestEqual(TEXT("Trail cancelled"),Sim->TourStatus(TEXT("farol")),FString(TEXT("cancelled")));
  TestEqual(TEXT("Trail refunded"),Sim->Money(),Before-TrailSold*Sim->TicketPrice(TEXT("farol")));}
 // A bad guide rates low.
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->State->SetNumberField(TEXT("minutes"),9*60);
 Sim->Tours();Sim->AdvanceMinutes(60);Sim->SellTickets(TEXT("snorkel"));Sim->State->SetNumberField(TEXT("minutes"),10*60+5);
 if(Sim->TourCount(TEXT("sold"),TEXT("snorkel"))>0)TestEqual(TEXT("Careless guide rates 2"),Sim->GuideTour(TEXT("snorkel"),{2,2,2}),2.);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareRestaurantTest,"MareAlta.Gameplay.HotelRestaurant",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareRestaurantTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/HotelRestaurant")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),5000);Sim->State->SetNumberField(TEXT("minutes"),12*60+5);
 TestTrue(TEXT("No restaurant before the hotel"),Sim->SeatDiners(0).IsEmpty());
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);
 TestTrue(TEXT("Lunch service open"),Sim->IsRestaurantOpen());
 TestFalse(TEXT("Diners seated"),Sim->SeatDiners(1).IsEmpty());TestTrue(TEXT("Table taken once"),Sim->SeatDiners(1).IsEmpty());
 TestTrue(TEXT("Order taken"),Sim->UseTable(1));TestEqual(TEXT("Cooking"),Sim->String(Sim->TableOrder(1),TEXT("stage")),FString(TEXT("cooking")));
 TestFalse(TEXT("Cannot serve while cooking"),Sim->UseTable(1));TestEqual(TEXT("Nothing ready yet"),Sim->PickUpPass(),0);
 Sim->State->SetNumberField(TEXT("minutes"),12*60+30);TestEqual(TEXT("Dish on the tray"),Sim->PickUpPass(),1);
 double Before=Sim->Money();const double Price=Sim->MenuPrice(Sim->String(Sim->TableOrder(1),TEXT("dish")));
 TestTrue(TEXT("Served"),Sim->UseTable(1));TestTrue(TEXT("Paid at least the menu price"),Sim->Money()-Before>=Price);TestFalse(TEXT("Table free"),Sim->TableOrder(1).IsValid());
 // Room service: cooked, picked up and delivered at the lift with the room fee.
 auto Room=MakeShared<FJsonObject>();Room->SetStringField(TEXT("dish"),TEXT("salada"));Room->SetStringField(TEXT("stage"),TEXT("cooking"));Room->SetNumberField(TEXT("suite"),305);
 Room->SetNumberField(TEXT("since"),Sim->RestaurantNow());Room->SetNumberField(TEXT("ready"),Sim->RestaurantNow());
 Sim->Restaurant()->SetArrayField(TEXT("room"),{MakeShared<FJsonValueObject>(Room)});
 TestEqual(TEXT("Nothing to deliver before the pass"),Sim->DeliverRoomService(),0);TestEqual(TEXT("Room dish picked up"),Sim->PickUpPass(),1);
 Before=Sim->Money();TestEqual(TEXT("Room service delivered"),Sim->DeliverRoomService(),1);TestTrue(TEXT("Room fee"),Sim->Money()-Before>Sim->MenuPrice(TEXT("salada")));
 // A party left waiting is served by the crew at a share of the price.
 Sim->SeatDiners(2);Sim->State->SetNumberField(TEXT("minutes"),13*60+30);Before=Sim->Money();Sim->RestaurantHour(14);
 TestTrue(TEXT("Crew served the long wait"),Sim->Money()>Before);
 // Event: paid now, earns tomorrow at the event hour.
 Before=Sim->Money();TestTrue(TEXT("Event booked"),Sim->BookEvent(TEXT("aniversario")));TestEqual(TEXT("Preparation paid"),Sim->Money(),Before-600.);
 TestFalse(TEXT("One event at a time"),Sim->BookEvent(TEXT("casamento")));
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->State->SetNumberField(TEXT("minutes"),21*60);Before=Sim->Money();
 Sim->RestaurantHour(21);TestTrue(TEXT("Event income"),Sim->Money()-Before>=1600);TestEqual(TEXT("Event done"),Sim->Object(Sim->Restaurant(),TEXT("event"))->Values.Num(),0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareLeisureChaptersTest,"MareAlta.Gameplay.FishingPhotoChapters",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareLeisureChaptersTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/FishingPhoto")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 // Fishing: each catch adds a 'peixe' to the stock (Seu Gregory's chapter delivers from there).
 const double Fish=Sim->Number(Sim->Object(Sim->State,TEXT("stock")),TEXT("peixe"));
 for(int32 I=0;I<4;++I)TestFalse(TEXT("Caught a fish"),Sim->CatchFish().IsEmpty());
 TestEqual(TEXT("Four fish in the stock"),Sim->Number(Sim->Object(Sim->State,TEXT("stock")),TEXT("peixe")),Fish+4);
 // Photo of the lighthouse flags Padre Robson's step; a repeated subject gives no new fame.
 TestEqual(TEXT("New subject"),Sim->RecordPhoto({TEXT("farol")},TEXT("a.png")),1);TestEqual(TEXT("Already photographed"),Sim->RecordPhoto({TEXT("farol")},TEXT("b.png")),0);
 bool bFlag=false;Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("chp"))->TryGetBoolField(TEXT("farol"),bFlag);TestTrue(TEXT("Lighthouse flag"),bFlag);
 const TArray<TSharedPtr<FJsonValue>>* Album=nullptr;TestTrue(TEXT("Album has two photos"),Sim->Object(Sim->State,TEXT("prog"))->TryGetArrayField(TEXT("album"),Album) && Album->Num()==2);
 // Bar discoveries count as recipes; only bought businesses count.
 Sim->Bar();TestEqual(TEXT("No discoveries yet"),Sim->BarDiscoveries(),0);
 Sim->Object(Sim->State,TEXT("bar"))->SetArrayField(TEXT("known"),{MakeShared<FJsonValueString>(TEXT("caipirinha")),MakeShared<FJsonValueString>(TEXT("mojito")),MakeShared<FJsonValueString>(TEXT("pina_colada"))});
 TestEqual(TEXT("Two drinks discovered"),Sim->BarDiscoveries(),2);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareDayEventsTest,"MareAlta.Gameplay.DayEventsParties",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareDayEventsTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/DayEvents")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);
 // Weekly calendar from day 8: quermesse (day%7==2), junina (4), DJ (6); the carnaval waits for the mayor's chapter.
 TestEqual(TEXT("Quermesse on day 9"),Sim->RollEvent(9),FString(TEXT("quermesse")));TestEqual(TEXT("Junina on day 11"),Sim->RollEvent(11),FString(TEXT("junina")));
 TestEqual(TEXT("DJ on day 13"),Sim->RollEvent(13),FString(TEXT("show_dj")));TestNotEqual(TEXT("No carnaval before the chapter"),Sim->RollEvent(14),FString(TEXT("carnaval")));
 TestNotEqual(TEXT("No party before day 8"),Sim->RollEvent(2),FString(TEXT("quermesse")));
 // Forecast becomes today's event at the next day; a decorated party draws more than a plain one.
 Sim->State->SetNumberField(TEXT("day"),8);Sim->State->SetStringField(TEXT("forecast"),TEXT("quermesse"));Sim->State->SetNumberField(TEXT("forecast_day"),9);
 const double Plain=Sim->KioskArrivalFactor();double Before=Sim->Money();
 TestTrue(TEXT("Decoration bought"),Sim->BuyPrep());TestEqual(TEXT("Decoration paid"),Sim->Money(),Before-120.);TestFalse(TEXT("Not twice"),Sim->BuyPrep());
 Sim->State->SetNumberField(TEXT("day"),9);Sim->StartDayEvent();
 TestEqual(TEXT("Today is the forecast"),Sim->TodayEvent(),FString(TEXT("quermesse")));TestTrue(TEXT("Preparations active"),Sim->IsPrepActive());
 TestTrue(TEXT("Decorated party draws more"),Sim->KioskArrivalFactor()>Plain*1.6);
 // A storm without preparations ruins part of the stock and keeps the boats in.
 Sim->Object(Sim->State,TEXT("stock"))->SetNumberField(TEXT("coco"),20);
 Sim->State->SetStringField(TEXT("forecast"),TEXT("tempestade"));Sim->State->SetNumberField(TEXT("day"),10);Sim->State->SetNumberField(TEXT("forecast_day"),10);Sim->StartDayEvent();
 TestEqual(TEXT("Storm day"),Sim->TodayEvent(),FString(TEXT("tempestade")));TestEqual(TEXT("Rain with the storm"),Sim->String(Sim->State,TEXT("weather")),FString(TEXT("rain")));
 TestEqual(TEXT("Storm loss"),Sim->Number(Sim->Object(Sim->State,TEXT("stock")),TEXT("coco")),13.);TestTrue(TEXT("Rough sea"),Sim->IsSeaRough());
 TestTrue(TEXT("Storm keeps the customers away"),Sim->KioskArrivalFactor()<Plain*.5);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("passeios"),true);Sim->State->SetNumberField(TEXT("minutes"),660);Sim->AdvanceMinutes(60);
 TestEqual(TEXT("Boat tour cancelled"),Sim->TourStatus(TEXT("barco")),FString(TEXT("cancelled")));
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareNewStaffTest,"MareAlta.Gameplay.NewStaffRoles",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareNewStaffTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/NewStaff")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),5000);Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));
 TestFalse(TEXT("Pool attendant needs the pool"),Sim->HireStaff(TEXT("piscineiro")));
 for(const TCHAR* Id:{TEXT("pool"),TEXT("grand_hotel")})Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(Id,true);
 TestTrue(TEXT("Hire pool attendant"),Sim->HireStaff(TEXT("piscineiro")));TestTrue(TEXT("Hire restaurant waiter"),Sim->HireStaff(TEXT("garcom_hotel")));
 // The attendant keeps the pool clean through an open day.
 Sim->Pool()->SetArrayField(TEXT("towels"),{MakeShared<FJsonValueNumber>(1)});
 for(int32 Hour=11;Hour<=16;++Hour)Sim->PoolHour(Hour);
 TestTrue(TEXT("Pool stays clean"),Sim->Number(Sim->Pool(),TEXT("dirt"))<20);TestEqual(TEXT("Towels collected"),Sim->PoolTowels(),0);
 // The waiter serves a waiting table after 15 minutes at 90%.
 Sim->State->SetNumberField(TEXT("minutes"),12*60+5);Sim->SeatDiners(0);Sim->State->SetNumberField(TEXT("minutes"),12*60+30);
 const double Since=Sim->Number(Sim->TableOrder(0),TEXT("since"));const double Before=Sim->Money();Sim->RestaurantHour(13);
 // New diners may sit at the freed table in the same hour: the original party must be gone.
 TestTrue(TEXT("Waiter served"),Sim->Money()>Before && (!Sim->TableOrder(0).IsValid() || Sim->Number(Sim->TableOrder(0),TEXT("since"))!=Since));
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareTutorialTest,"MareAlta.Gameplay.TutorialTips",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareTutorialTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Tutorial")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 // Each tip once per save; unknown keys show nothing.
 TestTrue(TEXT("First bar visit shows the tip"),Sim->ShowTip(TEXT("BarCounter")));TestFalse(TEXT("Tip title set"),Sim->PendingTipTitle.IsEmpty());
 TestFalse(TEXT("Not twice"),Sim->ShowTip(TEXT("BarCounter")));TestFalse(TEXT("Unknown key"),Sim->ShowTip(TEXT("Nothing")));
 // Every E target action used in the game has a tip.
 for(const TCHAR* Key:{TEXT("Fridge"),TEXT("Customer"),TEXT("PousadaReception"),TEXT("RoomTask"),TEXT("BusinessCounter"),TEXT("TourBooth"),TEXT("Fishing"),TEXT("RestaurantTable"),TEXT("PoolLeaves"),TEXT("phone"),TEXT("photo")})
  TestTrue(FString(TEXT("Tip exists: "))+Key,Sim->ShowTip(Key));
 // Next goal: the cheapest expansion with its prerequisites owned.
 FString Goal;double Cost=0;TestTrue(TEXT("A goal at the start"),Sim->NextGoal(Goal,Cost));TestTrue(TEXT("Goal costs something"),Cost>0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareSeasonsEndTest,"MareAlta.Gameplay.SeasonsAndEndOfContent",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareSeasonsEndTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Seasons")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 // Seasons: 14 days each, cycling; summer draws more than winter.
 Sim->State->SetNumberField(TEXT("day"),1);TestEqual(TEXT("Day 1 is summer"),Sim->String(Sim->Season(),TEXT("id")),FString(TEXT("verao")));const double Summer=Sim->EventDemand();
 Sim->State->SetNumberField(TEXT("day"),30);TestEqual(TEXT("Day 30 is winter"),Sim->String(Sim->Season(),TEXT("id")),FString(TEXT("inverno")));
 TestTrue(TEXT("Winter quieter than summer"),Sim->EventDemand()<Summer);
 Sim->State->SetNumberField(TEXT("day"),57);TestEqual(TEXT("Cycle restarts"),Sim->String(Sim->Season(),TEXT("id")),FString(TEXT("verao")));
 // End of content: only with every expansion and every chapter, and only once.
 TestFalse(TEXT("Not at the start"),Sim->IsEndOfContentDue());
 for(const auto& Pair:Sim->Object(Sim->Definitions,TEXT("expansions"))->Values)Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(FString(Pair.Key.ToView()),true);
 TestFalse(TEXT("Chapters still open"),Sim->IsEndOfContentDue());
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;Sim->Definitions->TryGetArrayField(TEXT("chapters"),Chapters);
 for(const auto& V:*Chapters){const auto C=V->AsObject();Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("ch"))->SetNumberField(Sim->String(C,TEXT("id")),C->GetArrayField(TEXT("steps")).Num());}
 TestTrue(TEXT("Everything done"),Sim->IsEndOfContentDue());Sim->MarkEndOfContentShown();TestFalse(TEXT("Shown once"),Sim->IsEndOfContentDue());
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareStaffShiftsTest,"MareAlta.Gameplay.StaffShiftsAndLevels",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareStaffShiftsTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/StaffShifts")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),5000);Sim->State->SetNumberField(TEXT("day"),2);Sim->State->SetNumberField(TEXT("minutes"),600);
 auto Hour=[&](double H){Sim->State->SetNumberField(TEXT("minutes"),H*60);};
 // An old save: a hired role without a team works full time at the base wage.
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("garcom_hotel"),true);
 Hour(3);TestTrue(TEXT("Old save: on duty at any hour"),Sim->StaffOnDuty(TEXT("garcom_hotel")));
 TestEqual(TEXT("Old save: base wage"),Sim->StaffWage(TEXT("garcom_hotel")),48.);
 // Hire, then a second person: each covers half of the day and the wage follows the shift shares.
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("bar"),true);
 TestTrue(TEXT("Hire bartender"),Sim->HireStaff(TEXT("bartender")));TestEqual(TEXT("One person"),Sim->StaffTeam(TEXT("bartender")).Num(),1);
 const double Before=Sim->Money();
 TestTrue(TEXT("Hire a second bartender"),Sim->HireSecondStaff(TEXT("bartender")));
 TestEqual(TEXT("Second hire paid"),Sim->Money(),Before-260);
 TestFalse(TEXT("No third person"),Sim->HireSecondStaff(TEXT("bartender")));
 const auto Team=Sim->StaffTeam(TEXT("bartender"));
 TestTrue(TEXT("Morning and afternoon"),Team.Num()==2 && Sim->String(Team[0],TEXT("shift"))==TEXT("manha") && Sim->String(Team[1],TEXT("shift"))==TEXT("tarde"));
 TestEqual(TEXT("Half-shift wages"),Sim->StaffWage(TEXT("bartender")),25.+27.);
 Hour(10);TestTrue(TEXT("Morning on duty"),Sim->HasStaff(TEXT("bartender")));
 Hour(22);TestTrue(TEXT("Evening on duty"),Sim->HasStaff(TEXT("bartender")));
 Hour(4);TestFalse(TEXT("Nobody at 4h"),Sim->HasStaff(TEXT("bartender")));
 TestTrue(TEXT("Hired flag kept"),Sim->Object(Sim->State,TEXT("staff"))->HasField(TEXT("bartender")));
 // Days off: both on Monday (day 1, 8, 15...) leaves the bar without a bartender that day only.
 Sim->CycleStaffDayOff(TEXT("bartender"),0);Sim->CycleStaffDayOff(TEXT("bartender"),1);
 Hour(10);Sim->State->SetNumberField(TEXT("day"),8);TestFalse(TEXT("Monday off"),Sim->HasStaff(TEXT("bartender")));
 Sim->State->SetNumberField(TEXT("day"),9);TestTrue(TEXT("Back on Tuesday"),Sim->HasStaff(TEXT("bartender")));
 // Shift swap keeps the pair complementary.
 TestTrue(TEXT("Cycle shift"),Sim->CycleStaffShift(TEXT("bartender"),0));
 const auto Swapped=Sim->StaffTeam(TEXT("bartender"));
 TestTrue(TEXT("Still complementary"),Sim->String(Swapped[0],TEXT("shift"))!=Sim->String(Swapped[1],TEXT("shift")) && Sim->String(Swapped[0],TEXT("shift"))!=TEXT("integral"));
 TestTrue(TEXT("Back to one person"),Sim->DismissSecondStaff(TEXT("bartender")));
 auto Solo=Sim->StaffTeam(TEXT("bartender"))[0];Solo->SetNumberField(TEXT("off"),-1);
 TestEqual(TEXT("One full-time again"),Sim->String(Solo,TEXT("shift")),FString(TEXT("integral")));
 // Experience: 30 worked hours make level 2, a better effect and a raise.
 for(int32 I=0;I<30;++I)Sim->StaffHour(12);
 TestEqual(TEXT("Level 2"),Sim->Number(Solo,TEXT("level")),2.);
 TestTrue(TEXT("Better effect"),FMath::IsNearlyEqual(Sim->StaffSkill(TEXT("bartender")),1.06,1e-6));
 TestEqual(TEXT("Raise"),Sim->StaffWage(TEXT("bartender")),45.);
 // Fatigue without days off: tired (weaker), then exhausted and absent the next day.
 int32 Absent=-1;bool bWasTired=false;
 for(int32 Night=0;Night<30 && Absent<0;++Night){Sim->StaffNight();
  if(Sim->Number(Solo,TEXT("fatigue"))>=60 && !bWasTired){bWasTired=true;TestTrue(TEXT("Tired works worse"),Sim->StaffSkill(TEXT("bartender"))<1.);}
  if(Sim->Number(Solo,TEXT("absent_day"),-1)>0)Absent=Sim->Number(Solo,TEXT("absent_day"));
  else Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"))+1);}
 TestTrue(TEXT("Got tired"),bWasTired);TestTrue(TEXT("Missed a day"),Absent>0);
 Sim->State->SetNumberField(TEXT("day"),Absent);TestFalse(TEXT("Absent that day"),Sim->HasStaff(TEXT("bartender")));
 Sim->StaffNight();TestTrue(TEXT("Rested after the absence"),Sim->Number(Solo,TEXT("fatigue"))<60);
 // What each role did today (staff page): counted per day.
 Sim->StaffDid(TEXT("bartender"),2,30);TestEqual(TEXT("Tasks today"),Sim->StaffDoneToday(TEXT("bartender")).Key,2);
 TestEqual(TEXT("Money today"),Sim->StaffDoneToday(TEXT("bartender")).Value,30.);
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"))+1);TestEqual(TEXT("New day resets"),Sim->StaffDoneToday(TEXT("bartender")).Key,0);
 // The kiosk attendant has no shifts or fatigue.
 TestTrue(TEXT("Hire attendant"),Sim->HireAttendant());Hour(3);TestTrue(TEXT("Attendant exempt"),Sim->StaffOnDuty(TEXT("atendente")));
 TestFalse(TEXT("Attendant has no shifts"),Sim->CycleStaffShift(TEXT("atendente"),0));
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePoolFullMatchTest,"MareAlta.Gameplay.PoolFullMatch",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePoolFullMatchTest::RunTest(const FString& Parameters)
{
 // Whole matches with the real physics and rules, both sides played by the shot AI: every match must end with a
 // winner in a reasonable number of shots, the balls never leave the table, and both sides can win.
 auto Room=NewObject<UMareGameRoom>();Room->AddToRoot();namespace R=MarePool;
 int32 Wins[2]={0,0},MaxShots=0,TotalShots=0;bool bInside=true,bEnded=true,bGroups=true;const int32 Matches=40;TSet<FString> Calls;
 for(int32 M=0;M<Matches;++M){Room->Rack();int32 Shots=0;
  while(Room->Winner<0 && Shots<300){if(Room->bBallInHand)Room->PlaceCueBallForAI();
   double Angle=0,Speed=0;Room->PlanGuestShot(Angle,Speed,uint32(M*1000+Shots));Room->Shoot(Angle,Speed);++Shots;
   double T=0;while(Room->Step(1./30) && T<40)T+=1./30;
   for(const auto& B:Room->Balls)if(!B.bIn)bInside&=FMath::Abs(B.P.X)<=R::L/2+.031 && FMath::Abs(B.P.Y)<=R::W/2+.031;
   Room->ResolveShot();}
  if(Room->Winner<0){bEnded=false;AddError(FString::Printf(TEXT("Match %d did not end after %d shots (%d-%d)"),M,Shots,Room->Score[0],Room->Score[1]));}
  else{// Eight-ball: the winner either cleared the group and potted the 8, or the loser potted the 8 early / with a foul.
   bGroups&=Room->Group[0]+Room->Group[1]==3 || Room->Group[0]+Room->Group[1]==0;Calls.Add(Room->LastCall);++Wins[Room->Winner];}
  MaxShots=FMath::Max(MaxShots,Shots);TotalShots+=Shots;}
 AddInfo(FString::Printf(TEXT("Pool: %d matches, wins %d/%d, average %.1f shots, longest %d"),Matches,Wins[0],Wins[1],TotalShots/double(Matches),MaxShots));
 TestTrue(TEXT("Every match ends"),bEnded);TestTrue(TEXT("Balls stay on the table"),bInside);
 TestTrue(TEXT("Both sides win sometimes"),Wins[0]>0 && Wins[1]>0);TestTrue(TEXT("Matches are not endless"),TotalShots/double(Matches)<90);
 TestTrue(TEXT("Groups are always one solids, one stripes"),bGroups);
 AddInfo(TEXT("Endings: ")+FString::Join(Calls.Array(),TEXT(" | ")));
 {// Rules on a hand-made table: wrong ball first is a foul with ball in hand; the 8 before clearing loses.
  Room->Rack();Room->bBreakShot=false;Room->Group[0]=1;Room->Group[1]=2;Room->Turn=0;
  for(int32 I=1;I<16;++I)Room->Balls[I].bIn=true;
  Room->Balls[9].bIn=false;Room->Balls[9].P=FVector2D(.2,0);Room->Balls[3].bIn=false;Room->Balls[3].P=FVector2D(.6,.3);
  Room->Balls[0]=UMareGameRoom::FBall();Room->Balls[0].P=FVector2D(-.3,0);
  Room->Shoot(0,1.5);while(Room->Step(1./30)){}Room->ResolveShot();
  TestTrue(TEXT("Hitting the opponent's ball first is a foul"),Room->Turn==1 && Room->bBallInHand);
  Room->Rack();Room->bBreakShot=false;Room->Group[0]=1;Room->Group[1]=2;Room->Turn=0;
  for(int32 I=1;I<16;++I)Room->Balls[I].bIn=true;
  Room->Balls[8].bIn=false;Room->Balls[8].P=FVector2D(R::L/2-.1,R::W/2-.1);Room->Balls[2].bIn=false;Room->Balls[2].P=FVector2D(-.6,.3);
  Room->Balls[0]=UMareGameRoom::FBall();Room->Balls[0].P=FVector2D(R::L/2-.4,R::W/2-.4);
  Room->Shoot(UE_DOUBLE_PI/4,2.5);while(Room->Step(1./30)){}Room->ResolveShot();
  TestEqual(TEXT("The 8 before your group is cleared loses"),Room->Winner,1);}
 Room->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePoolCupTest,"MareAlta.Gameplay.PoolCup",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePoolCupTest::RunTest(const FString& Parameters)
{
 // Campeonato da Maré: fee, 8-player bracket with the player in it, one round per day, champion paid and counted;
 // an elimination ends the cup; the record counts every match.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/PoolCup")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!Load(TEXT("definitions.json"),Sim->Definitions) || !Load(TEXT("default_save.json"),Sim->State)){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);
 TestTrue(TEXT("Join the cup"),Sim->PoolCupJoin());TestEqual(TEXT("Fee paid"),Sim->Money(),950.);
 TestEqual(TEXT("Eight players"),Sim->PoolCupAlive().Num(),8);TestTrue(TEXT("Player in the bracket"),Sim->PoolCupAlive().Contains(UMareSimulation::PoolYou));
 TestFalse(TEXT("Cannot join twice"),Sim->PoolCupJoin());
 FString Why;
 for(int32 Round=0;Round<3;++Round){
  TestTrue(TEXT("Round ready"),Sim->PoolCupReady(Why));TestFalse(TEXT("Has an opponent"),Sim->PoolCupOpponent().IsEmpty());
  Sim->PoolRecord(true);Sim->PoolCupResult(true);
  if(Round<2){TestFalse(TEXT("One round per day"),Sim->PoolCupReady(Why));Sim->State->SetNumberField(TEXT("day"),UMareSimulation::Number(Sim->State,TEXT("day"),1)+1);}}
 TestFalse(TEXT("Cup over after the final"),Sim->PoolCupActive());TestEqual(TEXT("Prize paid"),Sim->Money(),950.+600.);
 auto B=UMareSimulation::Object(Sim->State,TEXT("billiards"));
 TestEqual(TEXT("Cup counted"),UMareSimulation::Number(B,TEXT("cups")),1.);TestEqual(TEXT("Matches counted"),UMareSimulation::Number(B,TEXT("played")),3.);
 Sim->State->SetNumberField(TEXT("day"),UMareSimulation::Number(Sim->State,TEXT("day"),1)+1);
 TestTrue(TEXT("Join again"),Sim->PoolCupJoin());Sim->PoolCupResult(false);
 TestFalse(TEXT("Elimination ends the cup"),Sim->PoolCupActive());
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareTableTennisTest,"MareAlta.Gameplay.TableTennisMatch",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareTableTennisTest::RunTest(const FString& Parameters)
{
 // The ball model and the rules: a normal return clears the net and lands on the far half; a serve bounces on both
 // halves; whole best-of-3 matches between two shot AIs end with a legal score and real rallies.
 auto TT=NewObject<UMareTableTennis>();TT->AddToRoot();namespace T=MareTT;
 TT->NewMatch(0);TT->Ball=FVector(-T::L/2-.3,0,.15);TT->bInPlay=true;TT->bServing=false;TT->Hit(0,T::L/4,.2,6.8,.4);
 for(int32 I=0;I<240 && TT->BounceSide<0 && TT->bInPlay;++I)TT->Step(1./60);
 TestEqual(TEXT("Return lands on the far half"),TT->BounceSide,1);TestFalse(TEXT("Return clears the net"),TT->bNetTouch);
 TT->NewMatch(0);TT->Serve(0,.3,11);for(int32 I=0;I<240 && TT->bServing && TT->bInPlay;++I)TT->Step(1./60);
 TestTrue(TEXT("Serve is legal (own half, then far half)"),!TT->bServing && TT->bInPlay && TT->BounceSide==1);
 int32 Wins[2]={0,0},Points=0,Shots=0;bool bEnded=true,bScores=true;
 for(int32 M=0;M<16;++M){TT->NewMatch(M%2);TT->Skill[0]=TT->Skill[1]=.09;int32 Guard=0;
  while(TT->MatchWinner<0 && ++Guard<150000){
   if(!TT->bInPlay){TT->Serve(TT->Server,FMath::FRandRange(-.6,.6),M*977+Guard);if(!TT->bInPlay)TT->ReadyServe();continue;}
   for(int32 Side=0;Side<2;++Side){const double Sg=Side==0?-1.:1.;
    if(Sg*TT->Vel.X>0){const double Want=TT->PredictY(Side);TT->PaddleY[Side]+=FMath::Clamp(Want-TT->PaddleY[Side],-2.4/60,2.4/60);}}
   const int32 Before=TT->Points[0]+TT->Points[1]+10*(TT->Games[0]+TT->Games[1]);
   TT->Step(1./60);const int32 Win=TT->HitWindow();if(Win>=0)TT->AIReturn(Win,M*131+Guard);
   if(TT->Points[0]+TT->Points[1]+10*(TT->Games[0]+TT->Games[1])!=Before)++Points;}
  Shots+=TT->Rallies;
  if(TT->MatchWinner<0){bEnded=false;AddError(FString::Printf(TEXT("Match %d did not end: games %d-%d points %d-%d, inplay %d serving %d ball %s vel %s hitter %d bounces %d/%d side %d window %d"),M,TT->Games[0],TT->Games[1],TT->Points[0],TT->Points[1],
   TT->bInPlay,TT->bServing,*TT->Ball.ToString(),*TT->Vel.ToString(),TT->LastHitter,TT->ServeBounces,TT->BouncesSinceHit,TT->BounceSide,TT->HitWindow()));continue;}
  const int32 W=TT->MatchWinner;++Wins[W];
  bScores&=TT->Games[W]==2 && TT->Games[1-W]<=1 && TT->Points[W]>=11 && TT->Points[W]-TT->Points[1-W]>=2;}
 AddInfo(FString::Printf(TEXT("Table tennis: 16 matches, wins %d/%d, %.2f shots per point"),Wins[0],Wins[1],Shots/double(FMath::Max(Points,1))));
 TestTrue(TEXT("Every match ends"),bEnded);TestTrue(TEXT("Legal final scores"),bScores);TestTrue(TEXT("Both sides win sometimes"),Wins[0]>0 && Wins[1]>0);
 const double PerPoint=Shots/double(FMath::Max(Points,1));TestTrue(TEXT("Real rallies, not endless (3 to 9 shots per point)"),PerPoint>3 && PerPoint<9);
 TT->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareCampaignAuditTest,"MareAlta.Gameplay.CampaignAudit",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareCampaignAuditTest::RunTest(const FString& Parameters)
{
 // The whole main campaign and every side mission, played through the real actions: counters move with the action,
 // missions are claimed in order and only once, rewards are paid exactly, chapters gate businesses and the Grand Hotel.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/CampaignAudit")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),200000);Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));Sim->State->SetNumberField(TEXT("minutes"),600);
 auto Sell=[&](const FString& Dish,int32 Count){int32 Sold=0;
  for(int32 I=0;I<Count;++I){if(Sim->Available(Dish)<1)Sim->Restock(Dish,10);const FString Id=Sim->AddOrder(TEXT("Teste"),{Dish});
   if(Sim->Pickup(Dish) && Sim->Deliver(Id,Dish))++Sold;}
  return Sold;};
 auto Stage=[&](){return int32(Sim->Number(Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("campaign")),TEXT("stage")));};
 TMap<FString,double> Rewards;for(const TCHAR* Key:{TEXT("campaign"),TEXT("side_missions")})for(const auto& V:Sim->Definitions->GetArrayField(Key))
  Rewards.Add(Sim->String(V->AsObject(),TEXT("id")),Sim->Number(V->AsObject(),TEXT("reward")));
 auto Claim=[&](const FString& Id,bool bSide=false){const double Before=Sim->Money();const bool bOk=Sim->ClaimMission(Id,bSide);
  TestTrue(TEXT("Claim ")+Id,bOk);TestEqual(TEXT("Reward ")+Id,Sim->Money()-Before,Rewards.FindRef(Id));
  const double After=Sim->Money();TestFalse(TEXT("Claim once ")+Id,Sim->ClaimMission(Id,bSide));TestEqual(TEXT("No second reward ")+Id,Sim->Money(),After);};
 auto Advance=[&](const FString& Chapter,int32 Steps){for(int32 I=0;I<Steps;++I)TestTrue(FString::Printf(TEXT("%s step %d"),*Chapter,Sim->ChapterStep(Chapter)+1),Sim->AdvanceChapter(Chapter));};
 auto Stock=[&](const FString& Item,double Qty){auto S=Sim->Object(Sim->State,TEXT("stock"));S->SetNumberField(Item,Sim->Number(S,Item)+Qty);};

 // 1-2. Company and opening; claims are refused before the goal and out of order.
 TestFalse(TEXT("Out of order"),Sim->ClaimMission(TEXT("portas")));TestFalse(TEXT("Goal first"),Sim->ClaimMission(TEXT("chegada")));
 TestTrue(TEXT("Create company"),Sim->CreateCompany(TEXT("Quiosque Teste")));Claim(TEXT("chegada"));
 TestTrue(TEXT("Open"),Sim->SetOpen(true));Claim(TEXT("portas"));
 // 3. Eight kiosk sales.
 TestEqual(TEXT("Eight sales"),Sell(TEXT("coco_gelado"),8),8);Claim(TEXT("primeiros"));
 // 4-5. Tables and the attendant.
 TestTrue(TEXT("Tables"),Sim->BuyExpansion(TEXT("kiosk_tables")));Claim(TEXT("mesas"));
 TestTrue(TEXT("Attendant"),Sim->HireAttendant());Claim(TEXT("equipe"));
 // Act 2: Seu Tibúrcio on the summit (UMareSummitWorld writes State.summit): met, then three offerings.
 TestFalse(TEXT("Elder before meeting"),Sim->ClaimMission(TEXT("morro")));
 {auto Summit=MakeShared<FJsonObject>();Summit->SetBoolField(TEXT("met"),true);Sim->State->SetObjectField(TEXT("summit"),Summit);}Claim(TEXT("morro"));
 Sim->Object(Sim->State,TEXT("summit"))->SetNumberField(TEXT("count"),2);TestFalse(TEXT("Two offerings are not three"),Sim->ClaimMission(TEXT("oferendas")));
 Sim->Object(Sim->State,TEXT("summit"))->SetNumberField(TEXT("count"),3);Claim(TEXT("oferendas"));
 // 6. Seu Gregory's pier chapter: 4 fish caught at the pier, 15 customers served during the step, R$ 150.
 TestFalse(TEXT("Chapter before its step"),Sim->AdvanceChapter(TEXT("pier")));
 for(int32 I=0;I<4;++I)Sim->CatchFish();Advance(TEXT("pier"),1);
 Sell(TEXT("coco_gelado"),15);Advance(TEXT("pier"),2);TestTrue(TEXT("Pier chapter done"),Sim->IsChapterDone(TEXT("pier")));
 Claim(TEXT("comunidade"));
 // 7-9. Bar, pousada, pool.
 for(const TCHAR* Id:{TEXT("drinks"),TEXT("grill"),TEXT("bar")})TestTrue(FString(TEXT("Buy "))+Id,Sim->BuyExpansion(Id));Claim(TEXT("encontro"));
 TestTrue(TEXT("Pousada"),Sim->BuyExpansion(TEXT("pousada")));Claim(TEXT("hospedar"));
 TestTrue(TEXT("Pool"),Sim->BuyExpansion(TEXT("pool")));Claim(TEXT("verao"));
 TestTrue(TEXT("Tours"),Sim->BuyExpansion(TEXT("passeios")));
 // 10. The Grand Hotel waits for the carnaval story and fame 8.
 TestFalse(TEXT("Hotel needs the story"),Sim->BuyExpansion(TEXT("grand_hotel")));
 // prainha: fame 3, photo of the lighthouse, 6 coconuts.
 Sim->AddFame(400);Advance(TEXT("prainha"),1);Sim->RecordPhoto({TEXT("farol")},TEXT("teste.png"));Advance(TEXT("prainha"),1);Stock(TEXT("coco"),6);Advance(TEXT("prainha"),1);
 Claim(TEXT("prainha_m"));
 // sabores: two drinks discovered, 10 petiscos sold during the step, R$ 250.
 {auto Disc=Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("disc"));Disc->SetBoolField(TEXT("batida"),true);Disc->SetBoolField(TEXT("caipirinha"),true);}
 Advance(TEXT("sabores"),1);TestEqual(TEXT("Petiscos"),Sell(TEXT("petiscos"),10),10);Advance(TEXT("sabores"),2);
 Claim(TEXT("sabores_m"));
 // carnaval: fame 5, two businesses (the surf school needs prainha, the snack truck needs sabores), R$ 400.
 TestFalse(TEXT("Souvenir shop waits for the carnaval story"),Sim->BuyBusiness(TEXT("souvenir")));
 Sim->AddFame(3000);Advance(TEXT("carnaval"),1);
 TestTrue(TEXT("Sorveteria"),Sim->BuyBusiness(TEXT("sorveteria")));TestTrue(TEXT("Aluguel"),Sim->BuyBusiness(TEXT("aluguel")));Advance(TEXT("carnaval"),2);
 Claim(TEXT("carnaval_m"));
 if(Sim->FameLevel()<8)TestFalse(TEXT("Hotel needs fame 8"),Sim->BuyExpansion(TEXT("grand_hotel")));
 Sim->AddFame(100000);TestTrue(TEXT("Grand Hotel"),Sim->BuyExpansion(TEXT("grand_hotel")));Claim(TEXT("marealta"));
 // Act 5: the game room, recipes, customization, fame 10 and 3,400 kiosk sales.
 TestTrue(TEXT("Game room"),Sim->BuyExpansion(TEXT("salao_jogos")));Claim(TEXT("salao"));
 TestFalse(TEXT("Recipes first"),Sim->ClaimMission(TEXT("chef")));
 {auto Recipes=MakeShared<FJsonObject>();int32 Given=0;for(const auto& Pair:Sim->Object(Sim->Definitions,TEXT("dishes"))->Values){if(Given>=20)break;Recipes->SetNumberField(FString(Pair.Key.ToView()),FMath::Min(5,1+20-Given));Given+=FMath::Min(4,20-Given);}
  Sim->State->SetObjectField(TEXT("recipes"),Recipes);}Claim(TEXT("chef"));
 {auto Custom=MakeShared<FJsonObject>();auto Place=MakeShared<FJsonObject>();for(int32 I=0;I<10;++I){auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("tier"),5);Place->SetObjectField(FString::Printf(TEXT("s%d"),I),Row);}
  Custom->SetObjectField(TEXT("kiosk"),Place);Sim->State->SetObjectField(TEXT("custom"),Custom);}Claim(TEXT("postal"));
 Claim(TEXT("lenda"));
 TestFalse(TEXT("Sales first"),Sim->ClaimMission(TEXT("fregueses")));Sim->State->SetNumberField(TEXT("kiosk_n"),4000);Claim(TEXT("fregueses"));
 // Finale: the beach party sets prog.campaign.finale (UMareSummitWorld::ShowCredits).
 TestFalse(TEXT("Party before it happens"),Sim->ClaimMission(TEXT("festa")));
 Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("campaign"))->SetBoolField(TEXT("finale"),true);Claim(TEXT("festa"));
 TestEqual(TEXT("Campaign finished"),Stage(),Sim->Definitions->GetArrayField(TEXT("campaign")).Num());
 // Side missions: 5 fish, 12 ice creams, lighthouse and sunset photos.
 Sim->CatchFish();TestTrue(TEXT("Fish counted from the fishing log"),Sim->ClaimMission(TEXT("pescador"),true));
 TestEqual(TEXT("Ice creams"),Sell(TEXT("sorvete_morango"),12),12);Claim(TEXT("gelados"),true);
 Claim(TEXT("faroleiro"),true);
 TestFalse(TEXT("Sunset needs its photo"),Sim->ClaimMission(TEXT("entardecer"),true));
 Sim->RecordPhoto({TEXT("por_do_sol")},TEXT("teste.png"));Claim(TEXT("entardecer"),true);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareFaceCurvesTest,"MareAlta.People.FaceCurves",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareFaceCurvesTest::RunTest(const FString& Parameters)
{
 // The face rig curves of a person (UMareFaceAnimInstance reads them): a blink peaks mid-way through its 0.16 s, a
 // smile pulls both mouth corners, annoyance lowers both brows, and nothing is left once the mood has faded.
 AMarePerson* P=GetMutableDefault<AMarePerson>();
 const FString OldMood=P->Mood;const float Old[5]={P->Elapsed,P->BlinkAt,P->MoodLeft,P->MoodTotal,P->NextBlink};
 auto Value=[P](const TCHAR* Name){TArray<TPair<FName,float>> C;P->FaceCurves(C);for(const auto& V:C)if(V.Key==FName(Name))return V.Value;return 0.f;};
 P->Elapsed=10.f;P->BlinkAt=10.f-.08f;P->Mood.Reset();P->MoodLeft=0;
 TestTrue(TEXT("Blink closes both eyes mid-way"),Value(TEXT("CTRL_expressions_eyeBlinkL"))>.95f && Value(TEXT("CTRL_expressions_eyeBlinkR"))>.95f);
 P->BlinkAt=0;
 TestEqual(TEXT("Eyes open between blinks"),Value(TEXT("CTRL_expressions_eyeBlinkL")),0.f);
 P->Mood=TEXT("smile");P->MoodTotal=4;P->MoodLeft=2;
 TestTrue(TEXT("Smile pulls the mouth corners"),FMath::IsNearlyEqual(Value(TEXT("CTRL_expressions_mouthCornerPullL")),.75f,.01f) && Value(TEXT("CTRL_expressions_mouthCornerPullR"))>.7f);
 TestEqual(TEXT("Smile does not lower the brows"),Value(TEXT("CTRL_expressions_browDownL")),0.f);
 P->Mood=TEXT("annoyed");
 TestTrue(TEXT("Annoyance lowers both brows"),Value(TEXT("CTRL_expressions_browDownL"))>.6f && Value(TEXT("CTRL_expressions_browDownR"))>.6f);
 P->MoodLeft=.1f;
 TestTrue(TEXT("The mood eases out at the end"),Value(TEXT("CTRL_expressions_browDownL"))<.2f);
 P->MoodLeft=0;
 TestEqual(TEXT("No mood after it ends"),Value(TEXT("CTRL_expressions_browDownL")),0.f);
 P->Mood=OldMood;P->Elapsed=Old[0];P->BlinkAt=Old[1];P->MoodLeft=Old[2];P->MoodTotal=Old[3];P->NextBlink=Old[4];
 return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareHundredCyclesTest,"MareAlta.Acceptance.HundredCycles",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareHundredCyclesTest::RunTest(const FString& Parameters)
{
 // Acceptance criterion (PENDENCIAS sec. 14): 100 kiosk cycles (order, pick-up, delivery) with a save and a reload in
 // another session every 10 cycles: money rises by exactly the sale booked (price + decor tip), each pick-up takes exactly
 // one unit, nothing is charged or delivered twice after a reload, and an order served halfway resumes where it was.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 const FString Dir=FPaths::ProjectSavedDir()/TEXT("Automation/HundredCycles")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto ReadFile=[](const FString& Path){TSharedPtr<FJsonObject> Result;FString Text;FFileHelper::LoadFileToString(Text,*Path);FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);return Result;};
 auto Defs=ReadFile(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"));
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();Sim->SaveDirectory=Dir;Sim->Definitions=Defs;
 Sim->State=ReadFile(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"));
 if(!TestTrue(TEXT("Data available"),Defs.IsValid() && Sim->State.IsValid())){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),100000);
 TestTrue(TEXT("Company"),Sim->CreateCompany(TEXT("Aceite")));Sim->State->SetNumberField(TEXT("minutes"),600);TestTrue(TEXT("Open"),Sim->SetOpen(true));
 const TArray<FString> Menu={TEXT("suco"),TEXT("coco_gelado")};
 int32 Served=0,Reloads=0;bool bExact=true,bOnce=true,bResume=true;FRandomStream Rng(2026);
 for(int32 Cycle=0;Cycle<100;++Cycle){
  for(const auto& D:Menu)if(Sim->Available(D)<4)Sim->Restock(D,20);
  TArray<FString> Plan={Menu[Rng.RandRange(0,1)]};if(Rng.FRand()<.3f)Plan.Add(Menu[Rng.RandRange(0,1)]);
  const FString Id=Sim->AddOrder(FString::Printf(TEXT("Cliente %d"),Cycle),Plan);
  if(!TestFalse(TEXT("Order accepted"),Id.IsEmpty()))break;
  for(int32 I=0;I<Plan.Num();++I){
   // Suco and coco gelado share the ice: count the picked product only (one pick-up takes one of it).
   const double Cash=Sim->Money();const int32 Units=Sim->Available(Plan[I]);
   if(!Sim->Pickup(Plan[I])){if(bExact)AddInfo(FString::Printf(TEXT("cycle %d: pickup %s refused (%s)"),Cycle,*Plan[I],*Sim->LastMessage));bExact=false;break;}
   if(Sim->Available(Plan[I])!=Units-1 && bExact){AddInfo(FString::Printf(TEXT("cycle %d: %s stock %d -> %d"),Cycle,*Plan[I],Units,Sim->Available(Plan[I])));bExact=false;}
   if(I==0 && Plan.Num()>1 && Cycle%10==9){
    // Save with the product in hand and the order half served; another session loads it.
    Sim->Save();auto Other=NewObject<UMareSimulation>(Instance);Other->AddToRoot();Other->SaveDirectory=Dir;Other->Definitions=Defs;
    const bool bLoaded=Other->LoadSlot(1);++Reloads;
    bResume&=bLoaded && Other->Carry()==Plan[0] && UMareSimulation::Object(Other->State,TEXT("ue_orders"))->HasField(Id) && Other->Money()==Cash && Other->Available(Plan[0])==Sim->Available(Plan[0]);
    Sim->RemoveFromRoot();Sim=Other;}
   const double Price=Sim->SalePrice(Plan[I]);const double Revenue=UMareSimulation::Number(Sim->State,TEXT("kiosk")),Sales=UMareSimulation::Number(Sim->State,TEXT("kiosk_n"));
   if(!Sim->Deliver(Id,Plan[I])){if(bExact)AddInfo(FString::Printf(TEXT("cycle %d: deliver %s refused (%s)"),Cycle,*Plan[I],*Sim->LastMessage));bExact=false;break;}
   // The sale pays the price plus the decor tip, booked once: the cash rises exactly as much as the kiosk revenue,
   // never less than the price, and the sale counter by one.
   const double Gain=Sim->Money()-Cash,Booked=UMareSimulation::Number(Sim->State,TEXT("kiosk"))-Revenue;
   if((!FMath::IsNearlyEqual(Gain,Booked,.01) || Gain<Price-.01 || UMareSimulation::Number(Sim->State,TEXT("kiosk_n"))!=Sales+1) && bExact){
    AddInfo(FString::Printf(TEXT("cycle %d item %d %s: cash +%.2f, revenue +%.2f, price %.2f"),Cycle,I,*Plan[I],Gain,Booked,Price));bExact=false;}
   ++Served;
  }
  // The finished order is gone; delivering it again pays nothing.
  const double After=Sim->Money();
  bOnce&=!UMareSimulation::Object(Sim->State,TEXT("ue_orders"))->HasField(Id) && !Sim->Deliver(Id,Plan[0]) && Sim->Money()==After;
  if(Cycle%10==4){
   // A plain reload between orders keeps money, stock and the (empty) order list exactly.
   Sim->Save();auto Other=NewObject<UMareSimulation>(Instance);Other->AddToRoot();Other->SaveDirectory=Dir;Other->Definitions=Defs;
   const bool bLoaded=Other->LoadSlot(1);++Reloads;
   bResume&=bLoaded && Other->Money()==Sim->Money() && Other->Available(TEXT("suco"))==Sim->Available(TEXT("suco"))
    && Other->Available(TEXT("coco_gelado"))==Sim->Available(TEXT("coco_gelado")) && UMareSimulation::Object(Other->State,TEXT("ue_orders"))->Values.IsEmpty();
   Sim->RemoveFromRoot();Sim=Other;}
 }
 TestTrue(TEXT("Money and stock change by exactly one sale each"),bExact);
 TestTrue(TEXT("Nothing charged or delivered twice"),bOnce);
 TestTrue(TEXT("Reloads keep the state and resume half-served orders"),bResume);
 TestTrue(TEXT("At least 100 items served"),Served>=100);TestTrue(TEXT("Reloads exercised"),Reloads>=10);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();IFileManager::Get().DeleteDirectory(*Dir,false,true);return true;
}
