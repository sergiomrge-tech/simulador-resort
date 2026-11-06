#include "MareSimulation.h"
#include "Algo/Reverse.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "MareGameRoom.h"
#include "MareTableTennis.h"
#include "MareFoosball.h"
#include "Engine/StaticMesh.h"
#include "MareStaysWorld.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "MareArcade.h"
#include "Dom/JsonValue.h"
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
 const double BeforeNight=Sim->Money();const double Upkeep=Sim->DailyUpkeep();const int32 DayBefore=Sim->Number(Sim->State,TEXT("day"));Sim->Sleep();
 TestTrue(TEXT("Upkeep charged for the owned expansions (the hotel alone is R$ 150)"),Upkeep>=150);
 auto Hotel=Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("hotel"));const int32 Rooms=Sim->Number(Hotel,TEXT("rooms"));
 // Suites are paid at the reception (MareStays); the night books the restaurant of real stays and the crew.
 TestEqual(TEXT("No guests checked in yet"),Rooms,0);
 TestEqual(TEXT("Hotel night booked once with wage"),Sim->Money(),double(BeforeNight+FMath::RoundToDouble(Rooms*1.7*35)-900.-Wage-Upkeep));
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
 TestEqual(TEXT("Decor starts neutral"),Sim->KioskArrivalFactor()/(Sim->EventDemand()*Sim->WordOfMouth()),1.0);   // season, event demand and stars apart
 // Stars move the traffic: a run of quick 5-star services brings more people, customers giving up bring fewer.
 {const double Neutral=Sim->WordOfMouth();for(int32 I=0;I<40;++I)Sim->AddRating(5);TestTrue(TEXT("Five stars bring more customers"),Sim->WordOfMouth()>Neutral && Sim->WordOfMouth()<=1.25);
  for(int32 I=0;I<40;++I)Sim->AddRating(1);TestEqual(TEXT("Angry customers cut the traffic"),Sim->WordOfMouth(),.7);Sim->State->RemoveField(TEXT("ratings"));}
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
 // 3.6: no flat rate any more; the clerk serves the line the hour after the customers arrive.
 Sim->State->SetNumberField(TEXT("minutes"),900);Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));Sim->AdvanceMinutes(120);
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
 // 5.1: the check-out leaves the room dirty until the housekeeping crew (8:00-18:00) cleans it.
 TestEqual(TEXT("Checked-out hotel room dirty"),Sim->FreeCleanRooms(TEXT("hotel")),31);
 for(int32 H=8;H<18;++H)Sim->StaysHour(H);
 TestEqual(TEXT("Housekeeping freed the suite"),Sim->FreeCleanRooms(TEXT("hotel")),32);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareHotelRoomsTest,"MareAlta.Gameplay.HotelRooms",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareHotelRoomsTest::RunTest(const FString& Parameters)
{
 // CHECKLIST 5.1: three kinds of room, check-out with the minibar bill, housekeeping by hand or by the crew, phone complaints.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/HotelRooms")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);Sim->SyncRooms();Sim->State->SetNumberField(TEXT("money"),5000);
 // Kinds: the visitable 3rd floor first, 32 rooms in all.
 TestEqual(TEXT("301 is the suite"),Sim->HotelRoomKind(0),FString(TEXT("suite")));TestEqual(TEXT("302 standard"),Sim->HotelRoomKind(1),FString(TEXT("standard")));
 TestEqual(TEXT("303 luxury"),Sim->HotelRoomKind(2),FString(TEXT("luxo")));
 {TMap<FString,int32> Count;for(int32 I=0;I<32;++I)Count.FindOrAdd(Sim->HotelRoomKind(I))++;
  TestEqual(TEXT("2 suites"),Count.FindRef(TEXT("suite")),2);TestEqual(TEXT("10 luxury"),Count.FindRef(TEXT("luxo")),10);TestEqual(TEXT("20 standard"),Count.FindRef(TEXT("standard")),20);}
 TestEqual(TEXT("Room number 301"),UMareSimulation::HotelRoomNumber(0),301);TestEqual(TEXT("Room number 401"),UMareSimulation::HotelRoomNumber(8),401);
 TestEqual(TEXT("Room name"),Sim->HotelRoomName(2),FString(TEXT("Luxo 303")));
 // Every visitable room has a spot for each task and each complaint kind (UMareStaysWorld places them in the world).
 {const TArray<TSharedPtr<FJsonValue>>* Spots=nullptr;const TArray<TSharedPtr<FJsonValue>>* Visitable=nullptr;
  TestTrue(TEXT("Spots in the data"),Sim->HotelRoomDefs()->TryGetArrayField(TEXT("spots"),Spots));Sim->HotelRoomDefs()->TryGetArrayField(TEXT("visitable"),Visitable);
  if(Spots && Visitable && TestEqual(TEXT("One spot set per visitable room"),Spots->Num(),Visitable->Num()))for(int32 I=0;I<Spots->Num();++I){const auto O=(*Spots)[I]->AsObject();
   for(const TCHAR* T:{TEXT("bed"),TEXT("towels"),TEXT("trash"),TEXT("minibar")})TestTrue(FString::Printf(TEXT("Room %d spot %s"),I,T),O->HasTypedField<EJson::Array>(T));
   const TArray<TSharedPtr<FJsonValue>>* Kinds=nullptr;UMareSimulation::Object(Sim->HotelRoomDefs(),TEXT("complaints"))->TryGetArrayField(TEXT("kinds"),Kinds);
   if(Kinds)for(const auto& K:*Kinds){const FString Id=UMareSimulation::String(K->AsObject(),TEXT("id"));
    TestTrue(FString::Printf(TEXT("Room %d fix spot %s"),I,*Id),UMareSimulation::Object(O,TEXT("fix"))->HasTypedField<EJson::Array>(Id));}}}
 // A guest asking for a luxury room gets one.
 {const FString Id=Sim->AddArrival(TEXT("hotel"));const TArray<TSharedPtr<FJsonValue>>* Queue=nullptr;Sim->Stays()->TryGetArrayField(TEXT("queue"),Queue);
  if(TestFalse(TEXT("Hotel guest arrived"),Id.IsEmpty()) && Queue){for(const auto& V:*Queue)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==Id)V->AsObject()->SetStringField(TEXT("kind"),TEXT("luxo"));
   TestTrue(TEXT("Luxury guest checked in"),Sim->AcceptOffer(Id));
   bool bLux=false;for(int32 I=0;I<32;++I){auto R=Sim->HotelRoom(I);if(R && UMareSimulation::String(UMareSimulation::Object(R,TEXT("guest")),TEXT("id"))==Id)bLux=Sim->HotelRoomKind(I)==TEXT("luxo");}
   TestTrue(TEXT("Room of the kind asked for"),bLux);}}
 // Check-out of 302: dirty with bed, towels and trash; the minibar bill matches what was taken.
 auto R=Sim->HotelRoom(1);if(!TestTrue(TEXT("Room 302 exists"),R.IsValid())){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 R->SetStringField(TEXT("state"),TEXT("occupied"));R->SetNumberField(TEXT("nights"),1);R->SetNumberField(TEXT("mood"),.6);
 {auto G=MakeShared<FJsonObject>();G->SetStringField(TEXT("id"),TEXT("t1"));G->SetStringField(TEXT("name"),TEXT("Ana"));R->SetObjectField(TEXT("guest"),G);}
 const double BeforeOut=Sim->Money();const double Bill=Sim->HotelCheckOut(R);
 TestEqual(TEXT("Dirty after check-out"),UMareSimulation::String(R,TEXT("state")),FString(TEXT("dirty")));
 TestEqual(TEXT("Minibar bill booked"),Sim->Money(),BeforeOut+Bill);
 {double Sum=0;const TArray<TSharedPtr<FJsonValue>>* Taken=nullptr;R->TryGetArrayField(TEXT("minibar_taken"),Taken);const TArray<TSharedPtr<FJsonValue>>* Items=nullptr;Sim->HotelRoomDefs()->TryGetArrayField(TEXT("minibar"),Items);
  if(Taken && Items)for(const auto& T:*Taken)for(const auto& V:*Items)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==T->AsString())Sum+=UMareSimulation::Number(V->AsObject(),TEXT("price"));
  TestEqual(TEXT("Bill = prices of what was taken"),Bill,Sum);
  const TArray<TSharedPtr<FJsonValue>>* Tasks=nullptr;R->TryGetArrayField(TEXT("tasks"),Tasks);
  TestEqual(TEXT("Minibar task only if something was taken"),Tasks && Tasks->ContainsByPredicate([](const TSharedPtr<FJsonValue>& V){return V->AsString()==TEXT("minibar");}),Taken && Taken->Num()>0);}
 // Force a known minibar: the espumante costs 30 to restock.
 R->SetArrayField(TEXT("minibar_taken"),{MakeShared<FJsonValueString>(TEXT("espumante"))});
 R->SetArrayField(TEXT("tasks"),{MakeShared<FJsonValueString>(TEXT("bed")),MakeShared<FJsonValueString>(TEXT("towels")),MakeShared<FJsonValueString>(TEXT("trash")),MakeShared<FJsonValueString>(TEXT("minibar"))});
 TestEqual(TEXT("Restock cost"),Sim->HotelMinibarCost(R),30.);
 TestFalse(TEXT("Unknown task"),Sim->CleanHotelRoom(1,TEXT("window"),true));
 // The crew does not touch the visitable floor before 11:00.
 Sim->State->SetNumberField(TEXT("minutes"),9*60);Sim->HotelRoomsHour(9);
 TestEqual(TEXT("Crew leaves 302 for the player in the morning"),UMareSimulation::String(R,TEXT("state")),FString(TEXT("dirty")));
 {const double M=Sim->Money();TestTrue(TEXT("Restock the minibar"),Sim->CleanHotelRoom(1,TEXT("minibar"),true));TestEqual(TEXT("Restock paid"),Sim->Money(),M-30);}
 for(const TCHAR* T:{TEXT("bed"),TEXT("towels"),TEXT("trash")})TestTrue(FString(TEXT("By hand: "))+T,Sim->CleanHotelRoom(1,T,true));
 TestEqual(TEXT("Room free"),UMareSimulation::String(R,TEXT("state")),FString(TEXT("free")));
 TestTrue(TEXT("Done alone: polished"),R->HasField(TEXT("polished")));
 // A non-visitable room is cleaned by the crew in the morning; the visitable one only after 11:00.
 auto Far=Sim->HotelRoom(9);Far->SetStringField(TEXT("state"),TEXT("occupied"));Far->SetObjectField(TEXT("guest"),MakeShared<FJsonObject>());Sim->HotelCheckOut(Far);
 R->SetStringField(TEXT("state"),TEXT("occupied"));Sim->HotelCheckOut(R);
 Sim->HotelRoomsHour(9);TestEqual(TEXT("Crew cleaned room 402"),UMareSimulation::String(Far,TEXT("state")),FString(TEXT("free")));
 TestEqual(TEXT("302 still dirty at 9:00"),UMareSimulation::String(R,TEXT("state")),FString(TEXT("dirty")));
 Sim->HotelRoomsHour(12);TestEqual(TEXT("Crew reaches 302 after 11:00"),UMareSimulation::String(R,TEXT("state")),FString(TEXT("free")));
 TestFalse(TEXT("Crew work is not polished"),R->HasField(TEXT("polished")));
 // Complaints: one per room, solved by the technician (paid) or in person (free, fame), or expired (mood drops).
 auto Lux=Sim->HotelRoom(2);Lux->SetStringField(TEXT("state"),TEXT("occupied"));Lux->SetNumberField(TEXT("mood"),.7);
 TestTrue(TEXT("No complaint from a free room"),Sim->AddHotelComplaint(1,TEXT("ac")).IsEmpty());
 const FString Ac=Sim->AddHotelComplaint(2,TEXT("ac"));TestFalse(TEXT("Complaint by phone"),Ac.IsEmpty());
 TestTrue(TEXT("One open complaint per room"),Sim->AddHotelComplaint(2,TEXT("tv")).IsEmpty());
 TestEqual(TEXT("90 minutes to solve"),Sim->ComplaintMinutesLeft(Sim->HotelComplaints()[0]),90.);
 {const double M=Sim->Money();TestTrue(TEXT("Technician sent"),Sim->SolveHotelComplaint(Ac,false));TestEqual(TEXT("Technician paid"),Sim->Money(),M-80);}
 const FString Tv=Sim->AddHotelComplaint(2,TEXT("tv"));const double Fame=Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));
 TestTrue(TEXT("Solved in person"),Sim->SolveHotelComplaint(Tv,true));TestTrue(TEXT("In person gives fame"),Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))>Fame);
 const FString Shower=Sim->AddHotelComplaint(2,TEXT("shower"));const double Mood=Sim->Number(Lux,TEXT("mood"));
 Sim->State->SetNumberField(TEXT("minutes"),9*60+95);
 TestEqual(TEXT("Expired after the deadline"),Sim->ExpireHotelComplaints(),1);
 TestTrue(TEXT("Guest mood dropped"),Sim->Number(Lux,TEXT("mood"))<Mood);TestTrue(TEXT("Room marked complained"),Lux->HasField(TEXT("complained")));
 TestEqual(TEXT("No complaints left"),Sim->HotelComplaints().Num(),0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
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
 // 5.1: the room is dirty after the check-out until housekeeping is done; the guest still walks out next morning.
 TestEqual(TEXT("Suite being cleaned after the check-out"),Sim->FreeCleanRooms(TEXT("hotel")),31);
 TestEqual(TEXT("One hotel room dirty"),Sim->HotelRoomsIn(TEXT("dirty")),1);
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
 // (an experienced one: a level-1 bartender botches 15% of the drinks, which made this check fail at random)
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("bartender"),true);Sim->BarmanLevel();
 {const TArray<TSharedPtr<FJsonValue>>* Team=nullptr;if(Sim->Object(Sim->State,TEXT("staff_team"))->TryGetArrayField(TEXT("bartender"),Team))for(const auto& V:*Team)V->AsObject()->SetNumberField(TEXT("level"),5);}
 TestEqual(TEXT("Experienced bartender"),Sim->BarmanLevel(),5);
 Before=Sim->Money();Sim->BarHour(11);TestTrue(TEXT("Bartender served and was paid"),Sim->Money()>Before);
 // Impatient guests leave; nobody stays after closing.
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("bartender"),false);
 Sim->State->SetNumberField(TEXT("minutes"),1400);Sim->BarHour(23);TestEqual(TEXT("Bar empty after closing"),Orders(),0);
 TestTrue(TEXT("No orders while closed"),Sim->AddBarOrder().IsEmpty());
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBarPrepTest,"MareAlta.Gameplay.BarPrep",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBarPrepTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 1.1: every recipe made by hand (pick, pour, mini-actions, serve) is the right drink in any
 // order; a wrong mix never charges the guest; throwing away loses the ingredients; a careful prep pays more.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/BarPrep")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),5000);Sim->State->SetNumberField(TEXT("minutes"),600);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("bar"),true);
 // The bar world reads bar.stock before anything calls Bar(): the starting shelf must still be filled.
 Sim->Object(Sim->Object(Sim->State,TEXT("bar")),TEXT("stock"));
 auto Stock=[&](const FString& I){return Sim->Number(Sim->Object(Sim->Bar(),TEXT("stock")),I);};
 TestTrue(TEXT("Starting shelf filled after an early read"),Stock(TEXT("gelo"))>0);
 auto Make=[&](const TArray<FString>& Mix,double Score){
  for(const FString& I:Mix){if(!Sim->BarPick(I) || Sim->BarHand()!=I || !Sim->BarPour())return false;}
  for(int32 Guard=0;Guard<4 && !Sim->BarNextStep().IsEmpty();++Guard)if(!Sim->BarPrepStep(Sim->BarNextStep(),Score))return false;
  return Sim->BarNextStep().IsEmpty();};
 TestTrue(TEXT("Empty hand cannot pour"),!Sim->BarPour());
 // Pick, put back, pick again; pouring uses the stock at once.
 const double Ice=Stock(TEXT("gelo"));
 TestTrue(TEXT("Pick ice"),Sim->BarPick(TEXT("gelo")) && Sim->BarHand()==TEXT("gelo"));
 TestTrue(TEXT("Same item puts it back"),Sim->BarPick(TEXT("gelo")) && Sim->BarHand().IsEmpty());
 Sim->BarPick(TEXT("gelo"));TestTrue(TEXT("Pour"),Sim->BarPour());TestEqual(TEXT("Stock used on pouring"),Stock(TEXT("gelo")),Ice-1);
 Sim->BarPick(TEXT("gelo"));TestFalse(TEXT("No doubles in the glass"),Sim->BarPour());Sim->BarPick(TEXT("gelo"));
 TestEqual(TEXT("Ice only needs shaking"),Sim->BarNextStep(),FString(TEXT("bater")));
 const double Lost=Sim->BarDiscard();TestTrue(TEXT("Throwing away costs the ingredients"),Lost>0 && Sim->BarGlass().IsEmpty());
 TestEqual(TEXT("Thrown ice not refunded"),Stock(TEXT("gelo")),Ice-1);
 // Steps per kind of drink.
 TestEqual(TEXT("Caipirinha: muddle then shake"),FString::Join(Sim->BarPrepSteps({TEXT("cachaca"),TEXT("limao"),TEXT("acucar"),TEXT("gelo")}),TEXT(",")),FString(TEXT("socar,bater")));
 TestEqual(TEXT("Batida: blender"),FString::Join(Sim->BarPrepSteps({TEXT("cachaca"),TEXT("coco"),TEXT("leite_condensado"),TEXT("gelo")}),TEXT(",")),FString(TEXT("liquidificar")));
 TestEqual(TEXT("Mojito: muddle then shake"),FString::Join(Sim->BarPrepSteps({TEXT("rum"),TEXT("limao"),TEXT("hortela"),TEXT("acucar"),TEXT("agua_gas")}),TEXT(",")),FString(TEXT("socar,bater")));
 TestFalse(TEXT("Steps in order only"),Sim->BarPrepStep(TEXT("bater"),1));
 // The house drink is secret: mixing it does nothing until a VIP tells it (MareAlta.Gameplay.BarGuests); open it here.
 TestTrue(TEXT("Secret recipe closed"),Sim->MixRecipe({TEXT("rum"),TEXT("maracuja"),TEXT("coco"),TEXT("hortela"),TEXT("gelo")}).IsEmpty());
 Sim->Object(Sim->Bar(),TEXT("secrets"))->SetBoolField(TEXT("coqueiro"),true);
 TestFalse(TEXT("No chope without the chopeira"),Sim->BarPick(TEXT("chope")));
 Sim->Object(Sim->Bar(),TEXT("upgrades"))->SetNumberField(TEXT("chopeira"),1);
 TestEqual(TEXT("Chope needs no prep"),Sim->BarPrepSteps({TEXT("chope")}).Num(),0);
 // Every recipe, in its order and reversed, served to a guest who asked for it.
 const TArray<TSharedPtr<FJsonValue>>* Recipes=nullptr;Sim->BarDefs()->TryGetArrayField(TEXT("recipes"),Recipes);
 int32 Made=0;
 for(int32 Pass=0;Pass<2;++Pass)for(const auto& V:*Recipes){const auto R=V->AsObject();const FString Id=Sim->String(R,TEXT("id"));
  TArray<FString> Mix;for(const auto& N:R->GetArrayField(TEXT("needs")))Mix.Add(N->AsString());if(Pass)Algo::Reverse(Mix);
  Sim->RestockBar();const FString Order=Sim->AddBarOrder(Id);if(!TestFalse(TEXT("Guest for ")+Id,Order.IsEmpty()))continue;
  Sim->SetBarServing(Order);
  TestTrue(TEXT("Made by hand: ")+Id,Make(Mix,1));
  const double Before=Sim->Money();const auto Out=Sim->ServeGlass(Order);
  TestTrue(TEXT("Served: ")+Id,Out.bServed && Out.Recipe==Id);TestTrue(TEXT("Paid: ")+Id,Sim->Money()>Before);
  TestTrue(TEXT("Glass empty after serving: ")+Id,Sim->BarGlass().IsEmpty());Made+=Out.bServed;}
 TestEqual(TEXT("Every recipe both ways"),Made,2*Recipes->Num());
 // A wrong mix: the guest makes a face and pays nothing; a near miss (another recipe) does not pay either.
 Sim->RestockBar();FString Order=Sim->AddBarOrder(TEXT("caipirinha"));Sim->SetBarServing(Order);
 TestTrue(TEXT("Nonsense mixed"),Make({TEXT("leite_condensado"),TEXT("agua_gas")},1));
 double Before=Sim->Money();auto Out=Sim->ServeGlass(Order);
 TestTrue(TEXT("Nonsense is no drink"),!Out.bServed && Out.Recipe.IsEmpty());TestEqual(TEXT("Nonsense not charged"),Sim->Money(),Before);
 TestTrue(TEXT("Made a caipiroska"),Make({TEXT("vodka"),TEXT("limao"),TEXT("acucar"),TEXT("gelo")},1));
 Out=Sim->ServeGlass(Order);TestTrue(TEXT("Other recipe not served"),!Out.bServed && Out.Recipe==TEXT("caipiroska"));TestEqual(TEXT("Other recipe not charged"),Sim->Money(),Before);
 // Not ready: serving before the steps is refused and keeps the glass.
 Sim->BarPick(TEXT("cachaca"));Sim->BarPour();TestFalse(TEXT("Steps first"),Sim->ServeGlass(Order).bServed);TestEqual(TEXT("Glass kept"),Sim->BarGlass().Num(),1);Sim->BarDiscard();
 // Careful prep pays more than a clumsy one (same wait).
 TestTrue(TEXT("Perfect caipirinha"),Make({TEXT("cachaca"),TEXT("limao"),TEXT("acucar"),TEXT("gelo")},1));
 Before=Sim->Money();Sim->ServeGlass(Order);const double Good=Sim->Money()-Before;
 Order=Sim->AddBarOrder(TEXT("caipirinha"));Sim->SetBarServing(Order);
 TestTrue(TEXT("Clumsy caipirinha"),Make({TEXT("cachaca"),TEXT("limao"),TEXT("acucar"),TEXT("gelo")},0));
 Before=Sim->Money();Sim->ServeGlass(Order);const double Bad=Sim->Money()-Before;
 TestTrue(TEXT("Careful prep pays more"),Good>Bad && Bad>0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBarGuestsTest,"MareAlta.Gameplay.BarGuests",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBarGuestsTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 1.2: bubbles, taste profiles rating a surprise, happy hour / full moon, regulars and "o de sempre".
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/BarGuests")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),5000);Sim->State->SetNumberField(TEXT("minutes"),600);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("bar"),true);
 const double Chance=Sim->Number(Sim->BarDefs(),TEXT("regular_chance"),.3);Sim->BarDefs()->SetNumberField(TEXT("regular_chance"),0);
 auto OrderOf=[&](const FString& Id){for(const auto& V:Sim->Bar()->GetArrayField(TEXT("orders")))if(Sim->String(V->AsObject(),TEXT("id"))==Id)return V->AsObject();return TSharedPtr<FJsonObject>();};
 auto Serve=[&](const FString& Order,const FString& Recipe){TArray<FString> Mix;
  for(const auto& N:Sim->BarRecipe(Recipe)->GetArrayField(TEXT("needs")))Mix.Add(N->AsString());return Sim->ServeBar(Order,Mix);};
 // Every guest has a taste; the bubble says what they want.
 const FString A=Sim->AddBarOrder(TEXT("caipirinha"));TestFalse(TEXT("Taste profile"),Sim->String(OrderOf(A),TEXT("taste")).IsEmpty());
 TestTrue(TEXT("Bubble names a known drink"),Sim->BarBubble(OrderOf(A)).Contains(TEXT("Caipirinha")));
 const FString H=Sim->AddBarOrder(TEXT("mojito"));TestTrue(TEXT("Bubble gives the hint of an unknown drink"),Sim->BarBubble(OrderOf(H)).Contains(TEXT("hortelã")));
 const FString B=Sim->AddBarOrder(TEXT("surpresa"));OrderOf(B)->SetStringField(TEXT("taste"),TEXT("doce"));
 TestTrue(TEXT("Surprise bubble with the taste"),Sim->BarBubble(OrderOf(B)).Contains(TEXT("docinho")));
 // Surprise rated by taste: a sweet guest loves a batida de coco (3) and not a limonada... (1 for a strong one).
 TestEqual(TEXT("Sweet guest, batida de coco"),Sim->SurpriseStars(TEXT("batida_coco"),TEXT("doce")),3);
 TestEqual(TEXT("Strong guest, limonada"),Sim->SurpriseStars(TEXT("limonada"),TEXT("forte")),1);
 Sim->RestockBar();double Before=Sim->Money();auto R=Serve(B,TEXT("batida_coco"));
 TestTrue(TEXT("Surprise served with 3 stars"),R.bServed && R.Stars==3);const double Three=Sim->Money()-Before;
 const FString C=Sim->AddBarOrder(TEXT("surpresa"));OrderOf(C)->SetStringField(TEXT("taste"),TEXT("forte"));
 Sim->RestockBar();Before=Sim->Money();R=Serve(C,TEXT("batida_coco"));TestTrue(TEXT("Surprise to the wrong taste: fewer stars"),R.bServed && R.Stars==2);
 TestTrue(TEXT("Three stars pay more than two"),Three>Sim->Money()-Before);
 // Served right and fast: a regular, who comes back for "o de sempre".
 Sim->RestockBar();R=Serve(A,TEXT("caipirinha"));TestTrue(TEXT("Caipirinha served"),R.bServed);
 TMap<FString,FString> Regs=Sim->BarRegulars();TestTrue(TEXT("Regulars remembered"),Regs.Num()>=1);
 FString Regular;for(const auto& Pair:Regs)if(Pair.Value==TEXT("caipirinha"))Regular=Pair.Key;TestFalse(TEXT("The caipirinha guest is a regular"),Regular.IsEmpty());
 Sim->BarDefs()->SetNumberField(TEXT("regular_chance"),1);
 const FString D=Sim->AddBarOrder();auto O=OrderOf(D);bool bUsual=false;if(O)O->TryGetBoolField(TEXT("usual"),bUsual);
 const FString Usual=O?Sim->BarRegulars().FindRef(Sim->String(O,TEXT("name"))):FString();
 TestTrue(TEXT("A regular comes back for the usual"),bUsual && !Usual.IsEmpty() && Sim->String(O,TEXT("want"))==Usual);
 TestEqual(TEXT("Usual bubble"),Sim->BarBubble(O),FString(TEXT("O de sempre!")));
 Sim->RestockBar();const double Fame=Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));R=Serve(D,Usual.IsEmpty()?FString(TEXT("caipirinha")):Usual);
 TestTrue(TEXT("Usual served"),R.bServed && R.bUsual);TestTrue(TEXT("Usual gives extra fame"),Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))>=Fame+2);
 // (regulars stay away while the VIP is tested: a regular's return would take that arrival)
 Sim->BarDefs()->SetNumberField(TEXT("regular_chance"),0);
 // A VIP tells the secret house drink to whoever serves them well; knowing every recipe is the achievement.
 TestFalse(TEXT("Secret closed at first"),Sim->IsBarSecretOpen(TEXT("coqueiro")));
 Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),100000);
 const double Vip=Sim->Number(Sim->BarDefs(),TEXT("vip_chance"),.12);Sim->BarDefs()->SetNumberField(TEXT("vip_chance"),1);
 const FString V=Sim->AddBarOrder();bool bVip=false;if(auto VO=OrderOf(V))VO->TryGetBoolField(TEXT("vip"),bVip);
 Sim->BarDefs()->SetNumberField(TEXT("vip_chance"),Vip);
 TestTrue(TEXT("VIP at the counter"),bVip);TestTrue(TEXT("VIP bubble"),Sim->BarBubble(OrderOf(V)).StartsWith(TEXT("VIP")));
 Sim->RestockBar();R=Serve(V,TEXT("caipirinha"));
 TestTrue(TEXT("VIP served opens the secret"),R.bServed && Sim->IsBarSecretOpen(TEXT("coqueiro")) && Sim->IsRecipeKnown(TEXT("coqueiro")));
 TestEqual(TEXT("Secret mixable"),Sim->MixRecipe({TEXT("rum"),TEXT("maracuja"),TEXT("coco"),TEXT("hortela"),TEXT("gelo")}),FString(TEXT("coqueiro")));
 TestFalse(TEXT("No achievement yet"),Sim->HasBarAchievement());
 for(const auto& RV:Sim->BarDefs()->GetArrayField(TEXT("recipes"))){const FString Id=Sim->String(RV->AsObject(),TEXT("id"));
  if(Sim->IsRecipeKnown(Id) || Id==TEXT("mojito"))continue;
  auto Known=Sim->Bar()->GetArrayField(TEXT("known"));Known.Add(MakeShared<FJsonValueString>(Id));Sim->Bar()->SetArrayField(TEXT("known"),Known);}
 const FString M=Sim->AddBarOrder(TEXT("mojito"));Sim->RestockBar();R=Serve(M,TEXT("mojito"));
 TestTrue(TEXT("Last recipe gives the achievement"),R.bServed && Sim->HasBarAchievement());
 Sim->BarDefs()->SetNumberField(TEXT("regular_chance"),Chance);
 // Rush: happy hour and full-moon nights; more stools taken.
 TestFalse(TEXT("No rush at 10h"),Sim->IsBarRush());
 Sim->State->SetNumberField(TEXT("minutes"),17*60+10);TestTrue(TEXT("Happy hour"),Sim->IsBarRush());
 Sim->State->SetNumberField(TEXT("minutes"),20*60);TestFalse(TEXT("No rush at 20h on a normal day"),Sim->IsBarRush());
 Sim->State->SetStringField(TEXT("day_event"),TEXT("lua"));TestTrue(TEXT("Full moon night"),Sim->IsBarRush());
 Sim->Bar()->SetArrayField(TEXT("orders"),TArray<TSharedPtr<FJsonValue>>());int32 Seated=0;
 for(int32 I=0;I<10;++I)Seated+=!Sim->AddBarOrder(TEXT("caipirinha")).IsEmpty();
 TestEqual(TEXT("Rush fills more stools"),Seated,int32(Sim->Number(Sim->BarDefs(),TEXT("max_orders_rush"),6)));
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBarUpgradesTest,"MareAlta.Gameplay.BarUpgrades",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBarUpgradesTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 1.4: five-level upgrades (blender, freezer, banquetas, neon, chopeira), ice melting faster on a
 // hot day, and a bartender who only makes what he learned and botches drinks at a low level.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/BarUpgrades")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),50000);Sim->State->SetNumberField(TEXT("minutes"),600);
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("bar"),true);
 auto Stock=[&](const FString& I){return Sim->Number(Sim->Object(Sim->Bar(),TEXT("stock")),I);};
 // Buying: the price of each level, five levels at most.
 const double Cost=Sim->BarUpgradeCost(TEXT("freezer"));double Before=Sim->Money();
 TestTrue(TEXT("Freezer bought"),Sim->BuyBarUpgrade(TEXT("freezer")));TestEqual(TEXT("Freezer charged"),Sim->Money(),Before-Cost);
 TestEqual(TEXT("Freezer level 1"),Sim->BarUpgrade(TEXT("freezer")),1);
 for(int32 I=0;I<6;++I)Sim->BuyBarUpgrade(TEXT("banquetas"));TestEqual(TEXT("Five levels at most"),Sim->BarUpgrade(TEXT("banquetas")),5);
 TestEqual(TEXT("Maxed costs nothing"),Sim->BarUpgradeCost(TEXT("banquetas")),0.);
 TestFalse(TEXT("Unknown upgrade"),Sim->BuyBarUpgrade(TEXT("helicoptero")));
 // Banquetas: more guests at once (never more than the stools).
 TestTrue(TEXT("More seats"),Sim->BarSeats()>int32(Sim->Number(Sim->BarDefs(),TEXT("max_orders"),4)));
 TestTrue(TEXT("Seats capped by the stools"),Sim->BarSeats()<=Sim->BarDefs()->GetArrayField(TEXT("stools")).Num());
 // Freezer: more ice on restock; ice melts, much faster on a hot day, slower with the freezer.
 Sim->RestockBar();TestTrue(TEXT("Freezer holds more ice"),Stock(TEXT("gelo"))>Sim->Number(Sim->BarDefs(),TEXT("restock_qty"),10));
 const double Ice=Stock(TEXT("gelo"));Sim->BarHour(10);const double Normal=Ice-Stock(TEXT("gelo"));TestTrue(TEXT("Ice melts"),Normal>0);
 Sim->State->SetStringField(TEXT("day_event"),TEXT("calor"));const double Ice2=Stock(TEXT("gelo"));Sim->BarHour(11);
 TestTrue(TEXT("Hot day melts faster"),Ice2-Stock(TEXT("gelo"))>Normal*2);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 Sim->Bar()->SetArrayField(TEXT("orders"),TArray<TSharedPtr<FJsonValue>>());
 // Chopeira: the chope only once bought, pour only, dearer per level.
 TestFalse(TEXT("No chope at first"),Sim->BarPick(TEXT("chope")));
 TestTrue(TEXT("Chopeira bought"),Sim->BuyBarUpgrade(TEXT("chopeira")));Sim->RestockBar();
 const double Chope1=Sim->DrinkPrice(TEXT("chope"));Sim->BuyBarUpgrade(TEXT("chopeira"));TestTrue(TEXT("Chope dearer with the level"),Sim->DrinkPrice(TEXT("chope"))>Chope1);
 const FString C=Sim->AddBarOrder(TEXT("chope"));Sim->SetBarServing(C);
 TestTrue(TEXT("Pour the chope"),Sim->BarPick(TEXT("chope")) && Sim->BarPour());TestTrue(TEXT("Chope ready at once"),Sim->BarNextStep().IsEmpty());
 Before=Sim->Money();TestTrue(TEXT("Chope served"),Sim->ServeGlass(C).bServed && Sim->Money()>Before);
 // Blender: the blended drink pays more with a better blender.
 auto Batida=[&](){Sim->RestockBar();const FString O=Sim->AddBarOrder(TEXT("batida_coco"));Sim->SetBarServing(O);
  for(const FString& I:{TEXT("cachaca"),TEXT("coco"),TEXT("leite_condensado"),TEXT("gelo")}){Sim->BarPick(I);Sim->BarPour();}
  Sim->BarPrepStep(TEXT("liquidificar"),1);const double M=Sim->Money();Sim->ServeGlass(O);return Sim->Money()-M;};
 Sim->Object(Sim->Bar(),TEXT("known"));const double Plain=Batida();
 for(int32 I=0;I<5;++I)Sim->BuyBarUpgrade(TEXT("liquidificador"));const double Strong=Batida();
 TestTrue(TEXT("Better blender pays more"),Strong>Plain);
 // Bartender: knows the starting menu only, learns the player's recipes over the days, botches drinks at level 1.
 Sim->Object(Sim->State,TEXT("staff"))->SetBoolField(TEXT("bartender"),true);
 TestTrue(TEXT("Bartender knows the menu"),Sim->BarmanKnows().Contains(TEXT("caipirinha")));
 TestFalse(TEXT("Bartender does not know a discovered drink yet"),Sim->BarmanKnows().Contains(TEXT("batida_coco")));
 Sim->Bar()->SetNumberField(TEXT("barman_day"),Sim->Number(Sim->State,TEXT("day"),1)-5);Sim->BarHour(12);
 TestTrue(TEXT("Bartender learned the batida"),Sim->BarmanKnows().Contains(TEXT("batida_coco")));
 auto Errors=Sim->BarDefs()->GetArrayField(TEXT("barman_error"));auto Saved=Errors;Errors[0]=MakeShared<FJsonValueNumber>(1.);Sim->BarDefs()->SetArrayField(TEXT("barman_error"),Errors);
 Sim->Bar()->SetArrayField(TEXT("orders"),TArray<TSharedPtr<FJsonValue>>());Sim->RestockBar();Sim->AddBarOrder(TEXT("caipirinha"));
 const double Errs=Sim->Number(Sim->Bar(),TEXT("barman_errors"));Before=Sim->Money();Sim->BarHour(13);
 TestTrue(TEXT("Green bartender botches a drink"),Sim->Number(Sim->Bar(),TEXT("barman_errors"))>Errs);
 Sim->BarDefs()->SetArrayField(TEXT("barman_error"),Saved);
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
 // The hourly counter task (ice cream, pastel and rental have their own queues: 3.1-3.3).
 // (the surf school keeps the generic task: its own lessons were dropped from the plan, 06/11)
 FString Reason;TestFalse(TEXT("Not owned: no counter task"),Sim->CanPlayBusiness(TEXT("surfe"),Reason));
 Sim->Object(Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("biz")),TEXT("surfe"))->SetNumberField(TEXT("lvl"),1);
 TestTrue(TEXT("Owned and open: task available"),Sim->CanPlayBusiness(TEXT("surfe"),Reason));
 double Before=Sim->Money();const double Perfect=Sim->PlayBusiness(TEXT("surfe"),3);
 TestTrue(TEXT("Perfect task pays"),Perfect>0);TestEqual(TEXT("Booked"),Sim->Money(),Before+Perfect);
 TestFalse(TEXT("Once per hour"),Sim->CanPlayBusiness(TEXT("surfe"),Reason));TestEqual(TEXT("Second try pays nothing"),Sim->PlayBusiness(TEXT("surfe"),3),0.);
 Sim->State->SetNumberField(TEXT("minutes"),13*60);
 const double Miss=Sim->PlayBusiness(TEXT("surfe"),0);TestTrue(TEXT("Next hour available, fewer hits pay less"),Miss>0 && Miss<Perfect);
 Sim->State->SetNumberField(TEXT("minutes"),22*60);TestFalse(TEXT("Closed at night"),Sim->CanPlayBusiness(TEXT("surfe"),Reason));
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareTourBoothTest,"MareAlta.Gameplay.TourBooth",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareTourBoothTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 2.1: groups with a bubble, extras that please or annoy, seats and waiting list, rough-sea choice.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/TourBooth")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),2000);Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("passeios"),true);
 Sim->State->SetNumberField(TEXT("minutes"),11*60);
 const FString Boat=TEXT("barco");const double Price=Sim->TicketPrice(Boat);
 // A family with a kid, hungry: colete and lanche are wanted.
 Sim->AddTourGroup(Boat,2,1,TEXT("hungry"));const auto G=Sim->TourGroups(Boat);
 TestEqual(TEXT("Group in line"),G.Num(),1);TestTrue(TEXT("Bubble line"),Sim->TourGroupLine(G[0]).Contains(TEXT("2 adultos e 1 criança")) && Sim->TourGroupLine(G[0]).Contains(TEXT("fome")));
 double Before=Sim->Money();TestEqual(TEXT("Three board"),Sim->SellTourGroup(Boat,{TEXT("colete"),TEXT("lanche")}),3);
 const auto X=Sim->Object(Sim->ToursDefs(),TEXT("extras"));
 TestEqual(TEXT("Tickets and wanted extras paid"),Sim->Money()-Before,3*Price+3*Sim->Number(Sim->Object(X,TEXT("colete")),TEXT("price"))+3*Sim->Number(Sim->Object(X,TEXT("lanche")),TEXT("price")));
 const double Pleased=Sim->Number(Sim->Object(Sim->Tours(),TEXT("extra_rating")),Boat);TestTrue(TEXT("Wanted extras raise the rating"),Pleased>0);
 // Pushing an extra nobody wants: refused, rating down.
 Sim->AddTourGroup(Boat,2,0,TEXT("calm"));Before=Sim->Money();Sim->SellTourGroup(Boat,{TEXT("foto")});
 TestEqual(TEXT("Unwanted extra not paid"),Sim->Money()-Before,2*Price);
 TestTrue(TEXT("Pushy seller loses rating"),Sim->Number(Sim->Object(Sim->Tours(),TEXT("extra_rating")),Boat)<Pleased);
 // Seats: a group that does not fit goes to the waiting list and comes first tomorrow.
 const int32 Seats=Sim->TourSeats(Sim->TourDef(Boat));Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Boat,Seats-1);
 Sim->AddTourGroup(Boat,3,0,TEXT(""));TestEqual(TEXT("Full: nobody boards"),Sim->SellTourGroup(Boat,{}),0);TestEqual(TEXT("Waiting list"),Sim->TourWaitlist(Boat),1);
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->State->SetNumberField(TEXT("minutes"),11*60);
 Sim->Tours();Sim->ToursHour(12);
 TestTrue(TEXT("Waiting group first in line tomorrow"),Sim->TourGroups(Boat).Num()>=1 && Sim->Number(Sim->TourGroups(Boat)[0],TEXT("adults"))==3);
 TestEqual(TEXT("Waiting list emptied"),Sim->TourWaitlist(Boat),0);
 // Rough sea with tickets sold: the player chooses; refund gives the money back.
 Sim->SellTourGroup(Boat,{});const int32 Pax=Sim->TourCount(TEXT("sold"),Boat);TestTrue(TEXT("Sold before the storm"),Pax>0);
 Sim->State->SetStringField(TEXT("day_event"),TEXT("tempestade"));Sim->ToursHour(13);
 TestTrue(TEXT("Storm waits for a choice"),Sim->IsTourStormPending(Boat));
 Before=Sim->Money();TestTrue(TEXT("Refund"),Sim->RefundTour(Boat));TestEqual(TEXT("Refunded"),Sim->Money(),Before-Pax*Price);
 TestEqual(TEXT("Cancelled after refund"),Sim->TourStatus(Boat),FString(TEXT("cancelled")));
 // Next day, rough again: reschedule keeps most seats for tomorrow, already paid.
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));Sim->Tours();
 Sim->AddTourGroup(Boat,4,0,TEXT(""));Sim->SellTourGroup(Boat,{});Sim->State->SetStringField(TEXT("day_event"),TEXT("tempestade"));Sim->ToursHour(13);
 Before=Sim->Money();TestTrue(TEXT("Reschedule"),Sim->RescheduleTour(Boat));TestTrue(TEXT("Part refunded at most"),Sim->Money()>=Before-4*Price && Sim->Money()<=Before);
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));Sim->Tours();Sim->ToursHour(12);
 TestTrue(TEXT("Rescheduled seats already sold tomorrow"),Sim->TourCount(TEXT("sold"),Boat)>=3);
 // Playable boat tour (2.2): the trip's bonus (dolphins +, seasick -) moves the guided rating.
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));Sim->Tours();
 Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Boat,4);Sim->State->SetNumberField(TEXT("minutes"),14*60+5);
 TestEqual(TEXT("Seasick passengers lower the rating"),Sim->GuideTour(Boat,{0,0,0},-.6),4.4);
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->Tours();Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Boat,4);
 TestEqual(TEXT("Dolphins raise the rating"),Sim->GuideTour(Boat,{0,1,0},.5),5.);
 // Guided snorkel (2.3): coral touched, species presented and the group count decide the three stops; each new species
 // adds to the bonus and each coral touch takes from it.
 {const FString Snorkel=TEXT("snorkel");TArray<int32> C;double B=0;
  Sim->SnorkelScore(0,6,false,C,B);TestTrue(TEXT("Careful snorkel, many species, everyone counted: all good"),C==TArray<int32>({0,0,0}));TestTrue(TEXT("Species bonus"),B>.5);
  Sim->SnorkelScore(1,3,false,C,B);TestTrue(TEXT("One coral touch and three species: ok, ok, good"),C==TArray<int32>({1,1,0}));
  Sim->SnorkelScore(3,1,true,C,B);TestTrue(TEXT("Coral trampled, one species, crew fetched the lost one: all bad"),C==TArray<int32>({2,2,2}));TestTrue(TEXT("Coral lowers the bonus"),B<0);
  Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->Tours();
  Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Snorkel,4);Sim->State->SetNumberField(TEXT("minutes"),10*60+5);
  TestEqual(TEXT("A bad snorkel rates low"),Sim->GuideTour(Snorkel,C,B),2+B);
  Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->Tours();
  Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Snorkel,4);Sim->State->SetNumberField(TEXT("minutes"),10*60+5);
  Sim->SnorkelScore(0,8,false,C,B);TestEqual(TEXT("A careful snorkel rates top"),Sim->GuideTour(Snorkel,C,B),5.);}
 // Lighthouse trail (2.4): water and sunscreen, photos at the viewpoints and the sunset decide the stops; walkers left
 // behind complain and cost rating, the sunset and a story add to it.
 {const FString Trail=TEXT("farol");TArray<int32> C;double B=0;
  Sim->TrailScore(4,4,2,2,true,1,0,C,B);TestTrue(TEXT("Water for all, both photos, sunset: all good"),C==TArray<int32>({0,0,0}));TestEqual(TEXT("Sunset and story bonus"),B,.65,1e-6);
  Sim->TrailScore(2,4,1,2,false,0,2,C,B);TestTrue(TEXT("Half watered, one photo, sunset missed: ok, ok, ok"),C==TArray<int32>({1,1,1}));TestTrue(TEXT("Complaints lower the bonus"),B<0);
  Sim->TrailScore(0,4,0,2,false,0,9,C,B);TestTrue(TEXT("No water, no photos: bad, bad, ok"),C==TArray<int32>({2,2,1}));TestEqual(TEXT("Bonus floor"),B,-1.,1e-6);
  Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->Tours();
  Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Trail,4);Sim->State->SetNumberField(TEXT("minutes"),16*60+5);
  Sim->TrailScore(4,4,2,2,true,0,0,C,B);TestEqual(TEXT("A trail at sunset rates top"),Sim->GuideTour(Trail,C,B),5.);
  // Results (2.5): the tour that left is written down with stars, tip and reviews; tomorrow more people come.
  const auto Results=Sim->TourResults();TestTrue(TEXT("Result recorded"),Results.Num()>0 && Sim->String(Results[0],TEXT("id"))==Trail);
  const TArray<TSharedPtr<FJsonValue>>* Rv=nullptr;TestTrue(TEXT("Written reviews"),Results.Num() && Results[0]->TryGetArrayField(TEXT("reviews"),Rv) && Rv->Num()>=2);
  TestTrue(TEXT("Sunset highlight first"),Rv && Rv->Num() && Sim->String((*Rv)[0]->AsObject(),TEXT("text")).Contains(TEXT("pôr do sol")));
  const int32 PaxBefore=Sim->TourPassengers(Sim->TourDef(Trail));
  Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->Tours();
  TestEqual(TEXT("Word of mouth: +2 tomorrow"),Sim->TourBuzz(Trail),2);TestTrue(TEXT("More passengers tomorrow"),Sim->TourPassengers(Sim->TourDef(Trail))>=FMath::Min(PaxBefore+1,Sim->TourSeats(Sim->TourDef(Trail))));
  // The photographer (Personalizar "fotos" tier 3) sells prints after the tour.
  Sim->Object(Sim->Object(Sim->Object(Sim->State,TEXT("custom")),TEXT("passeios")),TEXT("fotos"))->SetNumberField(TEXT("tier"),3);
  Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Trail,5);Sim->State->SetNumberField(TEXT("minutes"),16*60+5);
  const double Cash=Sim->Money();Sim->GuideTour(Trail,{0,0,0},.5);TestTrue(TEXT("Photos sold"),Sim->Number(Sim->TourResults()[0],TEXT("photos"))>0);
  TestTrue(TEXT("Photo money booked"),Sim->Money()>Cash);
  // A playable tour still underway after its departure hour ends normally (the trail reaches the lighthouse at sunset).
  Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);Sim->Tours();Sim->Object(Sim->Tours(),TEXT("sold"))->SetNumberField(Trail,3);
  Sim->State->SetNumberField(TEXT("minutes"),17*60+40);TestEqual(TEXT("Too late without a tour underway"),Sim->GuideTour(Trail,{0,0,0},0),0.);
  Sim->Tours()->SetStringField(TEXT("active"),Trail);TestTrue(TEXT("Underway tour rated after its hour"),Sim->GuideTour(Trail,{0,0,0},0)>0);
  // The sunset raft only exists with the "Pôr do sol no mar" route.
  TestFalse(TEXT("Raft locked"),Sim->TourIds().Contains(TEXT("jangada")));
  Sim->Object(Sim->Object(Sim->Object(Sim->State,TEXT("custom")),TEXT("passeios")),TEXT("roteiro"))->SetNumberField(TEXT("tier"),3);
  TestTrue(TEXT("Raft unlocked"),Sim->TourIds().Contains(TEXT("jangada")));}
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareIceCreamTest,"MareAlta.Gameplay.IceCream",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareIceCreamTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 3.1: queue at the counter (hot day x2), the cone built from memory scored on flavours, scoop
 // size and topping, patience, and homemade popsicles for the pool cooler.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/IceCream")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),2000);Sim->State->SetNumberField(TEXT("minutes"),14*60+10);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 auto Biz=Sim->Object(Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"));Biz->SetNumberField(TEXT("lvl"),1);
 FString Reason;TestFalse(TEXT("Nobody in line yet"),Sim->CanPlayBusiness(TEXT("sorveteria"),Reason));
 Sim->IceCreamHour(15);const int32 Calm=Sim->IceQueue().Num();TestTrue(TEXT("Customers arrive"),Calm>=1);
 TestTrue(TEXT("A customer in line can be served"),Sim->CanPlayBusiness(TEXT("sorveteria"),Reason));
 Biz->SetArrayField(TEXT("queue"),{});Sim->State->SetStringField(TEXT("day_event"),TEXT("calor"));Sim->IceCreamHour(15);
 TestTrue(TEXT("Hot day: twice the customers"),Sim->IceQueue().Num()>=2);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 TestFalse(TEXT("Order line"),Sim->IceOrderLine(Sim->IceQueue()[0]).IsEmpty());
 // The right cone: every flavour, the right size, the right topping.
 auto Build=[&](const TSharedPtr<FJsonObject>& O,TArray<FString>& F,TArray<float>& Sz,float Size){F.Reset();Sz.Reset();const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
  if(O->TryGetArrayField(TEXT("flavors"),L))for(const auto& V:*L){F.Add(V->AsString());Sz.Add(Size);}};
 TArray<FString> F;TArray<float> Sz;const int32 Before=Sim->IceQueue().Num();
 auto O=Sim->IceQueue()[0];Build(O,F,Sz,.85f);double Cash=Sim->Money();
 const auto Good=Sim->ServeIceCream(F,Sz,Sim->String(O,TEXT("topping")));
 TestEqual(TEXT("Perfect cone: 3/3"),Good.Hits,3);TestTrue(TEXT("Paid with the tip"),Sim->Money()-Cash>=Good.Paid-1e-6 && Good.Paid>0);
 TestEqual(TEXT("Served customer leaves the line"),Sim->IceQueue().Num(),Before-1);
 // A wrong cone: another flavour, small scoops, no topping asked for.
 Sim->AddIceCustomer();Sim->AddIceCustomer();O=Sim->IceQueue()[0];Build(O,F,Sz,.3f);F[0]=F[0]==TEXT("coco")?TEXT("acai"):TEXT("coco");
 const FString WrongTop=Sim->String(O,TEXT("topping"))==TEXT("granulado")?TEXT("caramelo"):TEXT("granulado");
 const auto Bad=Sim->ServeIceCream(F,Sz,WrongTop);
 TestTrue(TEXT("Wrong flavour, small scoops, wrong topping: 0 or 1 hit"),Bad.Hits<=1 || (F.Num()>1 && Bad.Hits<=1));TestTrue(TEXT("Pays less"),Bad.Paid<Good.Paid+20);
 TestTrue(TEXT("Message tells what went wrong"),Sim->LastMessage.Contains(TEXT("pequena")));
 // Too big a scoop is a miss too.
 O=Sim->IceQueue()[0];Build(O,F,Sz,1.25f);TestTrue(TEXT("Too big: sizes miss"),Sim->ServeIceCream(F,Sz,Sim->String(O,TEXT("topping"))).Hits==2);
 // Patience: whoever waited too long gives up.
 Sim->AddIceCustomer();Sim->IceQueue().Last()->SetNumberField(TEXT("since"),0);const int32 Waiting=Sim->IceQueue().Num();Sim->IceCreamHour(16);
 TestTrue(TEXT("The one who waited all day gave up"),!Sim->IceQueue().ContainsByPredicate([](const TSharedPtr<FJsonObject>& Q){return UMareSimulation::Number(Q,TEXT("since"))==0;}));
 TestTrue(TEXT("Queue capped"),Sim->IceQueue().Num()<=int32(Sim->Number(Sim->IceDefs(),TEXT("queue_max"),6)) && Waiting>=1);
 // Homemade popsicles: the shop fills the pool cooler; the cooler sells only what it holds.
 auto Pool=Sim->Pool();Pool->SetNumberField(TEXT("popsicle_stock"),0);Sim->IceCreamHour(17);
 const int32 Stock=int32(Sim->Number(Pool,TEXT("popsicle_stock")));TestTrue(TEXT("Cooler filled by the shop"),Stock>0);
 Pool->SetNumberField(TEXT("popsicles"),Stock+2);Cash=Sim->Money();TestTrue(TEXT("Homemade popsicles sold"),Sim->SellPopsicles());
 TestEqual(TEXT("Cooler empty"),Sim->Number(Pool,TEXT("popsicle_stock")),0.);TestTrue(TEXT("Short of popsicles told"),Sim->LastMessage.Contains(TEXT("Faltou")));
 TestTrue(TEXT("Homemade price"),Sim->Money()-Cash>=Stock*Sim->Number(Sim->PoolDefs(),TEXT("popsicle_price"),7)*1.39);
 TestFalse(TEXT("Nothing left to sell"),Sim->SellPopsicles());
 // Closing: the line goes home.
 Sim->AddIceCustomer();Sim->State->SetNumberField(TEXT("minutes"),19*60+5);Sim->IceCreamHour(20);TestEqual(TEXT("Closed: empty line"),Sim->IceQueue().Num(),0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePastelTest,"MareAlta.Gameplay.Pastel",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePastelTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 3.2: queue at the truck (party days x2), filling + seal + golden fry scored, burnt not sold,
 // the sugar-cane juice paid only when pressed, patience and closing.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Pastel")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),2000);Sim->State->SetNumberField(TEXT("minutes"),14*60+10);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 auto Biz=Sim->Object(Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("biz")),TEXT("food_truck"));Biz->SetNumberField(TEXT("lvl"),1);
 FString Reason;TestFalse(TEXT("Nobody at the truck yet"),Sim->CanPlayBusiness(TEXT("food_truck"),Reason));
 Sim->PastelHour(15);TestTrue(TEXT("Customers arrive"),Sim->PastelQueue().Num()>=1);TestTrue(TEXT("Can serve"),Sim->CanPlayBusiness(TEXT("food_truck"),Reason));
 Biz->SetArrayField(TEXT("queue"),{});Sim->State->SetStringField(TEXT("day_event"),TEXT("quermesse"));Sim->PastelHour(15);
 TestTrue(TEXT("Party day: twice the customers"),Sim->PastelQueue().Num()>=2);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 TestTrue(TEXT("Order line"),Sim->PastelOrderLine(Sim->PastelQueue()[0]).StartsWith(TEXT("pastel de ")));
 // Perfect: right filling, sealed, golden; the juice pressed when asked.
 auto O=Sim->PastelQueue()[0];bool bCana=false;O->TryGetBoolField(TEXT("cana"),bCana);double Cash=Sim->Money();
 const auto Good=Sim->ServePastel(Sim->String(O,TEXT("filling")),true,7,bCana);
 TestEqual(TEXT("Perfect pastel: 3/3"),Good.Hits,3);TestTrue(TEXT("Paid"),Good.Paid>0 && Sim->Money()>Cash);
 // Juice asked but not pressed: not paid, and said.
 Sim->AddPastelCustomer();O=Sim->PastelQueue()[0];O->SetBoolField(TEXT("cana"),true);
 const auto NoJuice=Sim->ServePastel(Sim->String(O,TEXT("filling")),true,7,false);
 TestTrue(TEXT("Juice missing told"),Sim->LastMessage.Contains(TEXT("caldo de cana")));TestTrue(TEXT("Juice not paid"),NoJuice.Paid<Good.Paid+1e-6 || !bCana);
 // Open in the oil and raw: few hits.
 Sim->AddPastelCustomer();O=Sim->PastelQueue()[0];const auto Raw=Sim->ServePastel(Sim->String(O,TEXT("filling")),false,2,false);
 TestEqual(TEXT("Open and raw: 1 hit"),Raw.Hits,1);TestTrue(TEXT("Raw and leaking told"),Sim->LastMessage.Contains(TEXT("cru")) && Sim->LastMessage.Contains(TEXT("abriu")));
 // Burnt: not sold.
 Sim->AddPastelCustomer();O=Sim->PastelQueue()[0];O->SetBoolField(TEXT("cana"),false);
 const auto Burnt=Sim->ServePastel(Sim->String(O,TEXT("filling")),true,15,false);TestEqual(TEXT("Burnt pastel not paid"),Burnt.Paid,0.);
 TestTrue(TEXT("Burnt told"),Sim->LastMessage.Contains(TEXT("queimou")));
 // Wrong filling.
 Sim->AddPastelCustomer();O=Sim->PastelQueue()[0];O->SetBoolField(TEXT("cana"),false);
 const FString Other=Sim->String(O,TEXT("filling"))==TEXT("queijo")?TEXT("carne"):TEXT("queijo");
 TestEqual(TEXT("Wrong filling: 2/3"),Sim->ServePastel(Other,true,7,false).Hits,2);
 // Patience and closing.
 Sim->AddPastelCustomer();Sim->PastelQueue().Last()->SetNumberField(TEXT("since"),0);Sim->PastelHour(16);
 TestFalse(TEXT("Waited too long, gave up"),Sim->PastelQueue().ContainsByPredicate([](const TSharedPtr<FJsonObject>& Q){return UMareSimulation::Number(Q,TEXT("since"))==0;}));
 Sim->AddPastelCustomer();Sim->State->SetNumberField(TEXT("minutes"),23*60+10);Sim->PastelHour(24);TestEqual(TEXT("Closed: empty line"),Sim->PastelQueue().Num(),0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareRentalTest,"MareAlta.Gameplay.Rental",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareRentalTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 3.3: rent for 30/60 min (wax tip), returns checked (dent fined, unfair fine costs fame), the kayak adrift.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Rental")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),2000);Sim->State->SetNumberField(TEXT("minutes"),10*60+10);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 Sim->RentalState()->SetNumberField(TEXT("lvl"),1);FString Reason;
 TestFalse(TEXT("Nobody yet"),Sim->CanPlayBusiness(TEXT("aluguel"),Reason));
 Sim->RentalHour(11);TestTrue(TEXT("Customers arrive"),Sim->RentalQueue().Num()>=1);
 // Rent waxed: price + tip; rent plain: price only.
 Sim->RentalState()->SetArrayField(TEXT("queue"),{});Sim->AddRentalCustomer();auto O=Sim->RentalQueue()[0];O->SetStringField(TEXT("item"),TEXT("prancha"));O->SetNumberField(TEXT("minutes"),60);
 double Cash=Sim->Money();TestTrue(TEXT("Rented waxed"),Sim->RentItem(true));const double Waxed=Sim->Money()-Cash;
 Sim->AddRentalCustomer();O=Sim->RentalQueue()[0];O->SetStringField(TEXT("item"),TEXT("prancha"));O->SetNumberField(TEXT("minutes"),60);
 Cash=Sim->Money();Sim->RentItem(false);const double Plain=Sim->Money()-Cash;
 TestEqual(TEXT("60 min board price"),Plain,Sim->RentalPrice(TEXT("prancha"),60));TestTrue(TEXT("Wax adds a tip"),Waxed>Plain);
 TestEqual(TEXT("Two out on the water"),Sim->RentalOut().Num(),2);
 // Time runs out: they come back to be checked.
 Sim->State->SetNumberField(TEXT("minutes"),11*60+20);Sim->RentalHour(12);TestEqual(TEXT("Both back"),Sim->RentalReturns().Num(),2);
 TestTrue(TEXT("Returns can be checked"),Sim->CanPlayBusiness(TEXT("aluguel"),Reason));
 auto SetDent=[&](bool b){Sim->RentalReturns()[0]->SetBoolField(TEXT("dent"),b);};
 SetDent(true);Cash=Sim->Money();TestEqual(TEXT("Dent fined"),Sim->InspectReturn(true),3);TestEqual(TEXT("Fine paid"),Sim->Money()-Cash,Sim->Number(Sim->RentalDefs(),TEXT("fine"),20));
 SetDent(false);const double Fame=Sim->Number(Sim->State,TEXT("fame_xp"));TestEqual(TEXT("Clean board fined: unfair"),Sim->InspectReturn(true),0);
 TestTrue(TEXT("Unfair fine told"),Sim->LastMessage.Contains(TEXT("reclamou")));
 Sim->AddRentalCustomer();Sim->RentItem(false);Sim->State->SetNumberField(TEXT("minutes"),12*60+40);Sim->RentalHour(13);SetDent(false);
 TestEqual(TEXT("Clean board let go"),Sim->InspectReturn(false),2);TestEqual(TEXT("Nothing left to check"),Sim->InspectReturn(false),-1);
 // The kayak adrift: rescued for a reward.
 // 06/11: the hour above can set a rented kayak adrift by chance (adrift_chance, FRand): the gate failed 1 run in 3.
 // The random drift is not what is checked here: start from a calm sea.
 Sim->Object(Sim->RentalState(),TEXT("adrift"))->SetBoolField(TEXT("active"),false);
 TestFalse(TEXT("No kayak adrift"),Sim->IsKayakAdrift());Sim->StartKayakAdrift();TestTrue(TEXT("Kayak adrift"),Sim->IsKayakAdrift());
 Cash=Sim->Money();TestTrue(TEXT("Rescue pays"),Sim->RescueKayak()>0 && Sim->Money()>Cash);TestFalse(TEXT("Back on the beach"),Sim->IsKayakAdrift());
 // Closing: whoever is out comes back, the line goes home.
 Sim->AddRentalCustomer();Sim->RentItem(false);Sim->AddRentalCustomer();Sim->State->SetNumberField(TEXT("minutes"),17*60+5);Sim->RentalHour(18);
 TestEqual(TEXT("Closed: empty line"),Sim->RentalQueue().Num(),0);TestEqual(TEXT("Closed: everything back"),Sim->RentalOut().Num(),0);
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareSouvenirTest,"MareAlta.Gameplay.Souvenir",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareSouvenirTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 3.5: crafts from the makers (chapter, daily pieces), the shelf (window sells most), the gift wrap
 // (folds in order, ribbon, speed), postcards from album photos, closing, saved.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Souvenir")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),2000);Sim->State->SetNumberField(TEXT("minutes"),10*60+10);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));
 Sim->SouvenirState()->SetNumberField(TEXT("lvl"),1);FString Reason;
 TestTrue(TEXT("Shop opens to manage"),Sim->CanPlayBusiness(TEXT("souvenir"),Reason));
 TestEqual(TEXT("Starts with Dona Rita's magnets on the window"),Sim->String(Sim->SouvenirShelf()[0],TEXT("item")),FString(TEXT("ima")));
 // Makers: Seu Severino carves only after the pier story; each maker has a few pieces a day.
 TestFalse(TEXT("Jangada waits for the pier chapter"),Sim->BuySouvenirCraft(TEXT("jangada")));
 Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("ch"))->SetNumberField(TEXT("pier"),3);
 double Cash=Sim->Money();TestTrue(TEXT("Bought jangadas"),Sim->BuySouvenirCraft(TEXT("jangada")));
 const double JangadaCost=Sim->Number(Sim->SouvenirCraft(TEXT("jangada")),TEXT("cost"));const int32 Daily=int32(Sim->Number(Sim->SouvenirCraft(TEXT("jangada")),TEXT("daily")));
 TestEqual(TEXT("Paid the maker"),Cash-Sim->Money(),JangadaCost*FMath::Min(Daily,4));TestEqual(TEXT("In the back room"),Sim->SouvenirBackStock(TEXT("jangada")),FMath::Min(Daily,4));
 while(Sim->SouvenirMakerLeft(TEXT("jangada"))>0)Sim->BuySouvenirCraft(TEXT("jangada"));
 TestFalse(TEXT("Sold out for today"),Sim->BuySouvenirCraft(TEXT("jangada")));
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);TestEqual(TEXT("New pieces next day"),Sim->SouvenirMakerLeft(TEXT("jangada")),Daily);
 // Shelf: placing moves the back-room stock; the window sells far more than the back shelf.
 TestTrue(TEXT("Jangadas on the back shelf"),Sim->PlaceSouvenir(3,TEXT("jangada")));TestEqual(TEXT("Back room emptied"),Sim->SouvenirBackStock(TEXT("jangada")),0);
 TestFalse(TEXT("Nothing to place"),Sim->PlaceSouvenir(2,TEXT("cocada")));
 auto Fill=[&](int32 Slot,const FString& Id,int32 Qty){auto S=Sim->SouvenirShelf()[Slot];S->SetStringField(TEXT("item"),Id);S->SetNumberField(TEXT("qty"),Qty);};
 Sim->SouvenirState()->SetObjectField(TEXT("back"),MakeShared<FJsonObject>());Sim->SouvenirState()->SetArrayField(TEXT("cards"),{});
 int32 SoldWindow=0,SoldBack=0;FMath::RandInit(7);
 for(int32 Round=0;Round<40;++Round){Fill(0,TEXT("colar"),99);Fill(1,TEXT(""),0);Fill(2,TEXT(""),0);Fill(3,TEXT(""),0);Sim->SouvenirHour(11);SoldWindow+=99-int32(Sim->Number(Sim->SouvenirShelf()[0],TEXT("qty")));
  Fill(0,TEXT(""),0);Fill(3,TEXT("colar"),99);Sim->SouvenirHour(11);SoldBack+=99-int32(Sim->Number(Sim->SouvenirShelf()[3],TEXT("qty")));}
 TestTrue(FString::Printf(TEXT("Window sells more than the back shelf (%d vs %d)"),SoldWindow,SoldBack),SoldWindow>SoldBack*2);
 Fill(0,TEXT(""),0);Fill(3,TEXT(""),0);Sim->SouvenirState()->SetArrayField(TEXT("queue"),{});
 Cash=Sim->Money();Sim->SouvenirHour(11);TestEqual(TEXT("Empty shelf sells nothing"),Sim->Money(),Cash);
 // Gift wrap: right order + ribbon + quick = fee x 1.0 + tip; wrong order and ribbon pays less; slow loses the third hit.
 TArray<FString> Right={TEXT("laterais"),TEXT("fundo"),TEXT("topo")},Wrong={TEXT("topo"),TEXT("laterais"),TEXT("fundo")};
 Sim->AddSouvenirGift(TEXT("colar"));TestTrue(TEXT("Gift in line"),Sim->SouvenirQueue().Num()==1);const FString Asked=Sim->String(Sim->SouvenirQueue()[0],TEXT("ribbon"));
 TestTrue(TEXT("Gift line names the ribbon"),Sim->SouvenirGiftLine(Sim->SouvenirQueue()[0]).Contains(TEXT("fita")));
 Cash=Sim->Money();auto R=Sim->WrapGift(Right,Asked,8);const auto D=Sim->SouvenirDefs();
 TestEqual(TEXT("Perfect wrap: 3 hits"),R.Hits,3);TestEqual(TEXT("Perfect wrap pays fee + tip"),Sim->Money()-Cash,Sim->Number(D,TEXT("wrap_fee"))+Sim->Number(D,TEXT("tip_perfect")));
 Sim->AddSouvenirGift(TEXT("colar"));const FString Other=Sim->String(Sim->SouvenirQueue()[0],TEXT("ribbon"))==TEXT("azul")?TEXT("verde"):TEXT("azul");
 Cash=Sim->Money();R=Sim->WrapGift(Wrong,Other,8);TestEqual(TEXT("Crumpled and wrong ribbon: 1 hit"),R.Hits,1);TestTrue(TEXT("Pays less"),Sim->Money()-Cash<Sim->Number(D,TEXT("wrap_fee")));
 TestTrue(TEXT("Tells what went wrong"),Sim->LastMessage.Contains(TEXT("fita da cor errada")) && Sim->LastMessage.Contains(TEXT("amassado")));
 Sim->AddSouvenirGift(TEXT("colar"));R=Sim->WrapGift(Right,Sim->String(Sim->SouvenirQueue()[0],TEXT("ribbon")),40);TestEqual(TEXT("Slow: 2 hits"),R.Hits,2);
 TestEqual(TEXT("Nobody waiting"),Sim->WrapGift(Right,Asked,5).bServed,false);
 // Postcards: printed from an album photo (dearer with subjects), sold to tourists.
 Cash=Sim->Money();TestTrue(TEXT("Postcards printed"),Sim->PrintPostcards(TEXT("C:/album/foto_farol.png"),2));
 TestEqual(TEXT("Print cost"),Cash-Sim->Money(),Sim->Number(D,TEXT("card_cost"))*Sim->Number(D,TEXT("card_batch")));
 TestEqual(TEXT("Lighthouse + whale card price"),Sim->Number(Sim->SouvenirCards()[0],TEXT("price")),Sim->Number(D,TEXT("card_price"))+2*Sim->Number(D,TEXT("subject_bonus")));
 int32 Before=int32(Sim->Number(Sim->SouvenirCards()[0],TEXT("qty")));for(int32 I=0;I<20 && Sim->SouvenirCards().Num() && Sim->Number(Sim->SouvenirCards()[0],TEXT("qty"))==Before;++I)Sim->SouvenirHour(12);
 TestTrue(TEXT("Tourists buy postcards"),Sim->SouvenirCards().IsEmpty() || Sim->Number(Sim->SouvenirCards()[0],TEXT("qty"))<Before);
 // Closing: the gift line goes home; the shelf and the back room are kept in the save.
 Sim->AddSouvenirGift(TEXT("colar"));Fill(1,TEXT("mascara"),3);Sim->State->SetNumberField(TEXT("minutes"),20*60+5);Sim->SouvenirHour(21);
 TestEqual(TEXT("Closed: empty line"),Sim->SouvenirQueue().Num(),0);
 TestTrue(TEXT("Saved"),Sim->Save());FString Text;TArray<FString> Files;IFileManager::Get().FindFilesRecursive(Files,*Sim->SaveDirectory,TEXT("slot*.json"),true,false);
 if(Files.Num())FFileHelper::LoadFileToString(Text,*Files[0]);
 TestTrue(TEXT("Shelf in the save file"),Text.Contains(TEXT("mascara")) && Text.Contains(TEXT("foto_farol")));
 IFileManager::Get().DeleteDirectory(*Sim->SaveDirectory,false,true);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBusinessCommonTest,"MareAlta.Gameplay.BusinessCommon",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBusinessCommonTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 3.6, for every village business: a perfect, a middling and a wrong service pay what the data
 // says and are kept in the save (daily report); the clerk serves alone at 60 % with no fame, without him the line gives
 // up; level 2 costs money and fame, raises the prices and makes the task harder.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/BusinessCommon")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),20000);Sim->State->SetNumberField(TEXT("minutes"),14*60+10);Sim->State->SetStringField(TEXT("day_event"),TEXT(""));Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));
 const TArray<FString> Ids={TEXT("sorveteria"),TEXT("food_truck"),TEXT("aluguel"),TEXT("souvenir")};
 for(const FString& Id:Ids)Sim->BizState(Id)->SetNumberField(TEXT("lvl"),1);
 auto Pay=[&](const TSharedPtr<FJsonObject>& D,int32 Hits){return D->GetArrayField(TEXT("pay"))[Hits]->AsNumber();};
 auto Fame=[&](){return Sim->Number(Sim->Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));};
 auto Paid=[&](TFunction<void()> Do){const double Cash=Sim->Money();Do();return Sim->Money()-Cash;};
 // --- Ice cream: two coconut scoops with sprinkles.
 auto IceOrder=[&](){Sim->BizState(TEXT("sorveteria"))->SetArrayField(TEXT("queue"),{});Sim->AddIceCustomer();auto O=Sim->IceQueue()[0];
  O->SetArrayField(TEXT("flavors"),{MakeShared<FJsonValueString>(TEXT("coco")),MakeShared<FJsonValueString>(TEXT("coco"))});O->SetStringField(TEXT("topping"),TEXT("granulado"));return O;};
 {const auto D=Sim->IceDefs();const double Price=2*Sim->Number(D,TEXT("price_per_scoop"))+Sim->Number(D,TEXT("topping_price"));
  IceOrder();TestEqual(TEXT("Ice perfect pays price x pay[3] + tip"),Paid([&](){Sim->ServeIceCream({TEXT("coco"),TEXT("coco")},{.85f,.85f},TEXT("granulado"));}),FMath::RoundToDouble(Price*Pay(D,3))+Sim->Number(D,TEXT("tip_perfect")));
  IceOrder();TestEqual(TEXT("Ice middling (scoops too big) pays x pay[2]"),Paid([&](){Sim->ServeIceCream({TEXT("coco"),TEXT("coco")},{1.25f,1.25f},TEXT("granulado"));}),FMath::RoundToDouble(Price*Pay(D,2)));
  IceOrder();const double F0=Fame();TestEqual(TEXT("Ice wrong pays x pay[0]"),Paid([&](){Sim->ServeIceCream({TEXT("acai")},{.2f},TEXT("caramelo"));}),FMath::RoundToDouble(Price*Pay(D,0)));
  TestEqual(TEXT("Ice wrong: no fame"),Fame(),F0);}
 // --- Pastel: a cheese pastel, no juice.
 auto PastelOrder=[&](){Sim->BizState(TEXT("food_truck"))->SetArrayField(TEXT("queue"),{});Sim->AddPastelCustomer();auto O=Sim->PastelQueue()[0];
  O->SetStringField(TEXT("filling"),TEXT("queijo"));O->SetBoolField(TEXT("cana"),false);return O;};
 {const auto D=Sim->PastelDefs();PastelOrder();const double Price=Sim->PastelOrderPrice(Sim->PastelQueue()[0]);TestTrue(TEXT("Cheese pastel has a price"),Price>0);
  TestEqual(TEXT("Pastel perfect pays price x pay[3] + tip"),Paid([&](){Sim->ServePastel(TEXT("queijo"),true,7,false);}),FMath::RoundToDouble(Price*Pay(D,3))+Sim->Number(D,TEXT("tip_perfect")));
  PastelOrder();TestEqual(TEXT("Pastel middling (opened in the oil, raw) pays x pay[1]"),Paid([&](){Sim->ServePastel(TEXT("queijo"),false,2,false);}),FMath::RoundToDouble(Price*Pay(D,1)));
  PastelOrder();TestEqual(TEXT("Pastel wrong pays x pay[0]"),Paid([&](){Sim->ServePastel(TEXT("carne"),false,2,false);}),FMath::RoundToDouble(Price*Pay(D,0)));}
 // --- Rental: a board for 60 min waxed (perfect), plain (middling), a clean board fined (wrong).
 auto RentOrder=[&](){Sim->RentalState()->SetArrayField(TEXT("queue"),{});Sim->AddRentalCustomer();auto O=Sim->RentalQueue()[0];O->SetStringField(TEXT("item"),TEXT("prancha"));O->SetNumberField(TEXT("minutes"),60);};
 {const double Price=Sim->RentalPrice(TEXT("prancha"),60);
  RentOrder();TestEqual(TEXT("Rental perfect (waxed) pays price + wax tip"),Paid([&](){Sim->RentItem(true);}),Price+FMath::RoundToDouble(Price*Sim->Number(Sim->RentalDefs(),TEXT("wax_tip"))));
  RentOrder();TestEqual(TEXT("Rental middling (plain) pays the price"),Paid([&](){Sim->RentItem(false);}),Price);
  auto Back=MakeShared<FJsonObject>();Back->SetStringField(TEXT("name"),TEXT("Ana"));Back->SetStringField(TEXT("item"),TEXT("prancha"));Back->SetBoolField(TEXT("dent"),false);
  Sim->RentalState()->SetArrayField(TEXT("returns"),{MakeShared<FJsonValueObject>(Back)});const double F0=Fame();
  TestEqual(TEXT("Rental wrong (clean board fined) pays nothing"),Paid([&](){Sim->InspectReturn(true);}),0.);TestTrue(TEXT("and costs fame"),Fame()<=F0);}
 // --- Souvenir: gift wrap in order with the asked ribbon, quick (perfect) / slow (middling) / all wrong.
 {const auto D=Sim->SouvenirDefs();const TArray<FString> Right={TEXT("laterais"),TEXT("fundo"),TEXT("topo")},Wrong={TEXT("topo"),TEXT("fundo"),TEXT("laterais")};
  auto Gift=[&](){Sim->SouvenirState()->SetArrayField(TEXT("queue"),{});Sim->AddSouvenirGift(TEXT("ima"));Sim->SouvenirQueue()[0]->SetStringField(TEXT("ribbon"),TEXT("azul"));};
  Gift();TestEqual(TEXT("Wrap perfect pays fee x pay[3] + tip"),Paid([&](){Sim->WrapGift(Right,TEXT("azul"),5);}),FMath::RoundToDouble(Sim->WrapFee()*Pay(D,3))+Sim->Number(D,TEXT("tip_perfect")));
  Gift();TestEqual(TEXT("Wrap middling (slow) pays x pay[2]"),Paid([&](){Sim->WrapGift(Right,TEXT("azul"),60);}),FMath::RoundToDouble(Sim->WrapFee()*Pay(D,2)));
  Gift();TestEqual(TEXT("Wrap wrong pays x pay[0]"),Paid([&](){Sim->WrapGift(Wrong,TEXT("verde"),60);}),FMath::RoundToDouble(Sim->WrapFee()*Pay(D,0)));}
 // Daily report: 3 services each, with the grades; the phone line says it; all of it is in the save file.
 for(const FString& Id:Ids){const auto R=Sim->BizReport(Id);TestEqual(Id+TEXT(": 3 served by the player"),int32(Sim->Number(R,TEXT("you_n"))),3);
  TestTrue(Id+TEXT(": report line"),Sim->BizReportLine(Id,false).Contains(TEXT("você atendeu 3")));}
 TestEqual(TEXT("Ice: one perfect"),int32(Sim->Number(Sim->BizReport(TEXT("sorveteria")),TEXT("perfect"))),1);
 TestEqual(TEXT("Ice: grades 3+2+0"),int32(Sim->Number(Sim->BizReport(TEXT("sorveteria")),TEXT("hits"))),5);
 TestTrue(TEXT("Saved"),Sim->Save());
 {TArray<FString> Files;IFileManager::Get().FindFilesRecursive(Files,*Sim->SaveDirectory,TEXT("slot*.json"),true,false);FString Text;if(Files.Num())FFileHelper::LoadFileToString(Text,*Files[0]);
  TSharedPtr<FJsonObject> Saved;TestTrue(TEXT("Save file read"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Saved) && Saved.IsValid());
  for(const FString& Id:Ids){const auto R=Sim->Object(Sim->Object(Sim->Object(Sim->Object(Saved,TEXT("prog")),TEXT("biz")),Id),TEXT("report"));
   TestEqual(Id+TEXT(": report saved"),int32(Sim->Number(R,TEXT("you_n"))),3);TestEqual(Id+TEXT(": money saved"),Sim->Number(R,TEXT("you_money")),Sim->Number(Sim->BizReport(Id),TEXT("you_money")));}
  TestEqual(TEXT("Money saved"),Sim->Number(Saved,TEXT("money")),Sim->Money());}
 // Next day: today's report becomes yesterday's.
 Sim->State->SetNumberField(TEXT("day"),Sim->Number(Sim->State,TEXT("day"),1)+1);
 TestTrue(TEXT("Yesterday kept"),Sim->BizReportLine(TEXT("sorveteria"),true).Contains(TEXT("você atendeu 3")));TestTrue(TEXT("Today empty"),Sim->BizReportLine(TEXT("sorveteria"),false).Contains(TEXT("nenhum")));
 // Clerk: on by default, serves the line alone at 60 % of the full price, no fame.
 Sim->Pool()->SetNumberField(TEXT("popsicle_stock"),99);   // the cooler full: no popsicle cost booked in the hour
 {TestTrue(TEXT("Clerk hired by default"),Sim->HasBizClerk(TEXT("sorveteria")));const auto O=IceOrder();const double Price=Sim->IceOrderPrice(O);const double F0=Fame();
  TestEqual(TEXT("Clerk serves at 60%"),Paid([&](){Sim->IceCreamHour(15);}),FMath::RoundToDouble(Price*.6));TestEqual(TEXT("Clerk: no fame"),Fame(),F0);
  TestEqual(TEXT("Clerk in the report"),int32(Sim->Number(Sim->BizReport(TEXT("sorveteria")),TEXT("clerk_n"))),1);
  TestTrue(TEXT("Dismissed"),Sim->SetBizClerk(TEXT("sorveteria"),false));TestFalse(TEXT("No clerk"),Sim->HasBizClerk(TEXT("sorveteria")));
  IceOrder()->SetNumberField(TEXT("since"),0);Sim->State->SetStringField(TEXT("weather"),TEXT("rain"));Sim->BizState(TEXT("sorveteria"))->SetNumberField(TEXT("next_customer"),0);
  const double Cash=Sim->Money();Sim->IceCreamHour(15);
  TestTrue(TEXT("Without the clerk nobody is paid for the line"),Sim->Money()<=Cash);TestEqual(TEXT("The one who waited gave up"),int32(Sim->Number(Sim->BizReport(TEXT("sorveteria")),TEXT("lost"))),1);
  Sim->State->SetStringField(TEXT("weather"),TEXT("sun"));Sim->SetBizClerk(TEXT("sorveteria"),true);}
 // Level 2: needs fame and money; dearer and harder.
 {FString Reason;Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),0);TestFalse(TEXT("Level 2 needs fame"),Sim->CanUpgradeBusiness(TEXT("sorveteria"),Reason));
  Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),100000);const auto Base=Sim->IceDefs();const double ShowBase=Sim->Number(Base,TEXT("show_seconds"));
  IceOrder();const double Price1=Sim->IceOrderPrice(Sim->IceQueue()[0]);const double Cost=Sim->Number(Sim->BizLevelDef(TEXT("sorveteria"),2),TEXT("cost"));
  TestEqual(TEXT("Level 2 charged"),Paid([&](){TestTrue(TEXT("Upgraded"),Sim->UpgradeBusiness(TEXT("sorveteria")));}),-Cost);
  TestEqual(TEXT("Level 2"),Sim->BusinessLevel(TEXT("sorveteria")),2);
  TestTrue(TEXT("Dearer"),Sim->IceOrderPrice(Sim->IceQueue()[0])>Price1);TestTrue(TEXT("Harder: the order shows for less time"),Sim->Number(Sim->IceDefs(),TEXT("show_seconds"))<ShowBase);
  TestEqual(TEXT("Base values untouched"),Sim->Number(Base,TEXT("show_seconds")),ShowBase);
  for(const FString& Id:Ids){Sim->BizState(Id)->SetNumberField(TEXT("lvl"),3);TestTrue(Id+TEXT(": level 3 dearer"),Sim->BizPriceMult(Id)>1.4);}
  TestTrue(TEXT("Pastel level 3: tighter golden window"),Sim->Number(Sim->PastelDefs(),TEXT("golden_to"))-Sim->Number(Sim->PastelDefs(),TEXT("golden_from"))<2);
  TestTrue(TEXT("Rental level 3: more wax turns"),Sim->Number(Sim->RentalDefs(),TEXT("wax_turns"))>5);
  TestTrue(TEXT("Souvenir level 3: ribbon shown shorter"),Sim->Number(Sim->SouvenirDefs(),TEXT("memo_s"))<3);
  TestFalse(TEXT("No level 4"),Sim->CanUpgradeBusiness(TEXT("sorveteria"),Reason));}
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
 // Fishing: each catch adds a 'peixe' to the stock (Seu Severino's chapter delivers from there).
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
 // 6.2: every player-facing E target (AMareServiceTarget::Action) and every business counter has its own tip.
 for(const TCHAR* Key:{TEXT("Fridge"),TEXT("Cupboard"),TEXT("Customer"),TEXT("KioskSign"),TEXT("Clean"),TEXT("PousadaReception"),TEXT("RoomTask"),TEXT("HotelReception"),
  TEXT("BusinessCounter"),TEXT("TourBooth"),TEXT("TourVest"),TEXT("TourStory"),TEXT("TourSpecies"),TEXT("TrailWater"),TEXT("TrailStory"),TEXT("RentalTow"),
  TEXT("BarCounter"),TEXT("BarIngredient"),TEXT("BarGlass"),TEXT("Fishing"),TEXT("RestaurantTable"),TEXT("RestaurantPass"),TEXT("RoomService"),TEXT("Elevator"),
  TEXT("HotelTask"),TEXT("HotelFix"),TEXT("PoolLeaves"),TEXT("PoolTowel"),TEXT("PoolCooler"),TEXT("PoolTable"),TEXT("TableTennis"),TEXT("Resident"),TEXT("Elder"),TEXT("Comic"),TEXT("Bed"),TEXT("phone"),TEXT("photo")})
  if(FCString::Strcmp(Key,TEXT("BarCounter")))TestTrue(FString(TEXT("Tip exists: "))+Key,Sim->ShowTip(Key));
 for(const auto& Pair:UMareSimulation::Object(Sim->Definitions,TEXT("businesses"))->Values)TestTrue(TEXT("Business tip: ")+FString(Pair.Key.ToView()),Sim->ShowTip(TEXT("biz:")+FString(Pair.Key.ToView())));
 // Next goal: the cheapest expansion with its prerequisites owned.
 FString Goal;double Cost=0;TestTrue(TEXT("A goal at the start"),Sim->NextGoal(Goal,Cost));TestTrue(TEXT("Goal costs something"),Cost>0);
 // 6.2: the next unlock says what is missing (money, fame, village story) and when it can be bought.
 Sim->State->SetNumberField(TEXT("money"),0);
 {const FString Line=Sim->NextUnlockText();TestTrue(TEXT("Next unlock named: ")+Line,Line.StartsWith(TEXT("Próximo desbloqueio: ")+Goal));TestTrue(TEXT("Money missing: ")+Line,Line.Contains(FString::Printf(TEXT("faltam R$ %.0f"),Cost)));}
 Sim->State->SetNumberField(TEXT("money"),Cost);
 {const FString Line=Sim->NextUnlockText();TestTrue(TEXT("Affordable: ")+Line,Line.Contains(TEXT("já dá para comprar")));}
 // An expansion that also needs fame: owned prerequisites, enough money, fame 0.
 {auto Unlocked=UMareSimulation::Object(Sim->State,TEXT("unlocked"));FString FameId;int32 Fame=0;
  for(const auto& Pair:UMareSimulation::Object(Sim->Definitions,TEXT("expansions"))->Values){const int32 F=UMareSimulation::Number(Pair.Value->AsObject(),TEXT("fame"));if(F>0){FameId=FString(Pair.Key.ToView());Fame=F;break;}}
  if(TestFalse(TEXT("Some expansion needs fame"),FameId.IsEmpty())){
   for(const auto& Pair:UMareSimulation::Object(Sim->Definitions,TEXT("expansions"))->Values)if(FString(Pair.Key.ToView())!=FameId)Unlocked->SetBoolField(FString(Pair.Key.ToView()),true);
   UMareSimulation::Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),0);Sim->State->SetNumberField(TEXT("money"),1e7);
   const FString Line=Sim->NextUnlockText();TestTrue(TEXT("Fame missing: ")+Line,Line.Contains(FString::Printf(TEXT("fama %d"),Fame)));
   Unlocked->SetBoolField(FameId,true);TestTrue(TEXT("All bought: no line"),Sim->NextUnlockText().IsEmpty());}}
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
 {// Complete rules (5.4): weak break, no cushion after the contact, the called 8.
  Room->Rack();Room->Shoot(0,.9);while(Room->Step(1./30)){}
  const int32 Rails=Room->RailBalls();const int32 Potted=Room->PottedThisShot.Num();Room->ResolveShot();
  if(Potted==0 && Rails<4)TestTrue(TEXT("A soft break is a foul with ball in hand"),Room->Turn==1 && Room->bBallInHand && Room->LastCall.Contains(TEXT("saída fraca")));
  else AddError(FString::Printf(TEXT("Soft break test setup: %d balls potted, %d at the cushion"),Potted,Rails));
  Room->Rack();Room->Shoot(0,5.5);while(Room->Step(1./30)){}
  TestTrue(TEXT("A hard break reaches 4 cushions or pots"),Room->RailBalls()>=4 || Room->PottedThisShot.Num()>0);
  auto Lone=[&](int32 Ball,const FVector2D& At,const FVector2D& Cue){Room->Rack();Room->bBreakShot=false;Room->Group[0]=1;Room->Group[1]=2;Room->Turn=0;
   for(int32 I=1;I<16;++I)Room->Balls[I].bIn=true;Room->Balls[10].bIn=false;Room->Balls[10].P=FVector2D(-.8,-.4);
   Room->Balls[Ball].bIn=false;Room->Balls[Ball].P=At;Room->Balls[0]=UMareGameRoom::FBall();Room->Balls[0].P=Cue;};
  Lone(3,FVector2D(.1,0),FVector2D(0,0));for(int32 I=4;I<=7;++I)Room->Balls[I].bIn=false,Room->Balls[I].P=FVector2D(-.7,-.35+I*.08);
  Room->Shoot(0,.4);while(Room->Step(1./30)){}Room->ResolveShot();
  TestTrue(TEXT("Touching a ball that never reaches a cushion is a foul"),Room->Turn==1 && Room->bBallInHand && Room->LastCall.Contains(TEXT("tabela")));
  const FVector2D Corner(R::L/2,R::W/2),EightAt=Corner-FVector2D(.15,.15),CueAt=Corner-FVector2D(.5,.5);
  Lone(8,EightAt,CueAt);TestTrue(TEXT("On the 8 after clearing"),Room->OnTheEight(0));TestEqual(TEXT("Aim calls the corner"),Room->AimPocket(UE_DOUBLE_PI/4),5);
  Room->Shoot(UE_DOUBLE_PI/4,2.5);while(Room->Step(1./30)){}TestEqual(TEXT("The 8 drops in the corner"),Room->EightPocket,5);Room->ResolveShot();
  TestEqual(TEXT("The 8 in the called pocket wins"),Room->Winner,0);
  Lone(8,EightAt,CueAt);Room->CalledPocket=0;Room->bCallLocked=true;Room->Shoot(UE_DOUBLE_PI/4,2.5);while(Room->Step(1./30)){}Room->ResolveShot();
  TestEqual(TEXT("The 8 in another pocket loses"),Room->Winner,1);TestTrue(TEXT("Referee says why"),Room->LastCall.Contains(TEXT("cantada")));}
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
 // Weekly (5.4): no second sign-up the same week; the next edition opens 7 days later.
 int32 NextDay=0;TestFalse(TEXT("Weekly: closed mid-week"),Sim->PoolCupJoin());TestFalse(TEXT("Weekly: sign-up closed"),Sim->PoolCupSignupOpen(NextDay));
 TestEqual(TEXT("Weekly: next sign-up a week after the first"),NextDay,8);
 Sim->State->SetNumberField(TEXT("day"),8);TestTrue(TEXT("Weekly: open again"),Sim->PoolCupSignupOpen(NextDay));
 TestTrue(TEXT("Join again"),Sim->PoolCupJoin());Sim->PoolCupResult(false);
 TestFalse(TEXT("Elimination ends the cup"),Sim->PoolCupActive());
 // Without the player the guests play their own cup on the last sign-up night; cup nights draw spectators.
 Sim->State->SetNumberField(TEXT("day"),16);Sim->State->SetNumberField(TEXT("minutes"),22*60);
 UMareSimulation::Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("salao_jogos"),true);
 Sim->GameRoomHour(22);
 TestFalse(TEXT("Guests' cup: a champion"),UMareSimulation::String(UMareSimulation::Object(B,TEXT("cup")),TEXT("last_champion")).IsEmpty());
 TestTrue(TEXT("Guests' cup: tonight is a cup night"),Sim->PoolCupNight());
 TestFalse(TEXT("Guests' cup: sign-up closed until next week"),Sim->PoolCupSignupOpen(NextDay));TestEqual(TEXT("Guests' cup: next in a week"),NextDay,22);
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareFoosballTest,"MareAlta.Gameplay.FoosballMatch",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareFoosballTest::RunTest(const FString& Parameters)
{
 // 5.4 foosball with real rods: the ball rolls into the goal mouth, bounces off the walls and the end wall beside the
 // goal, a hanging man blocks it and a lifted one lets it pass, turning the rod kicks it, and AI-against-AI matches
 // always end 5 to something with real play.
 auto FB=NewObject<UMareFoosball>();FB->AddToRoot();namespace F=MareFB;
 auto LiftAll=[FB](){for(int32 I=0;I<F::Rods;++I){FB->RodA[I]=1.5;FB->RodW[I]=0;FB->RodVY[I]=0;FB->RodY[I]=0;}};
 auto Run=[FB](double Seconds){for(double T=0;T<Seconds && FB->bLive;T+=1./60)FB->Step(1./60);};
 FB->NewMatch();LiftAll();FB->bLive=true;FB->Ball=FVector2D(.4,0);FB->Vel=FVector2D(3,0);Run(1);
 TestEqual(TEXT("Rolling into the guest's goal scores for the player"),FB->Goals[0],1);
 FB->NewMatch();LiftAll();FB->bLive=true;FB->Ball=FVector2D(.3,.2);FB->Vel=FVector2D(0,2);Run(.3);
 TestTrue(TEXT("Side wall bounces the ball back"),FB->Vel.Y<0 && FMath::Abs(FB->Ball.Y)<=F::HY-F::R+1e-6);
 FB->NewMatch();LiftAll();FB->bLive=true;FB->Ball=FVector2D(.45,.25);FB->Vel=FVector2D(3,0);Run(.4);
 TestTrue(TEXT("End wall beside the goal: no goal, back into play"),FB->Goals[0]==0 && FB->Vel.X<0);
 FB->NewMatch();LiftAll();FB->RodA[5]=0;FB->bLive=true;FB->Ball=FVector2D(.12,0);FB->Vel=FVector2D(2,0);Run(.4);
 TestTrue(TEXT("A hanging man blocks the ball"),FB->Vel.X<0 && FB->Ball.X<F::RodX(5));
 FB->NewMatch();LiftAll();FB->bLive=true;FB->Ball=FVector2D(.12,0);FB->Vel=FVector2D(2,0);FB->Step(.3);
 TestTrue(TEXT("Lifted men let it pass"),FB->Ball.X>F::RodX(5)+.05 || FB->Goals[0]==1);
 FB->NewMatch();LiftAll();FB->RodA[3]=0;FB->bLive=true;FB->Ball=FVector2D(F::RodX(3)+.04,0);FB->Vel=FVector2D::ZeroVector;
 for(int32 I=0;I<6;++I){FB->TurnRod(3,FB->RodA[3]+30./60,1./60);FB->Step(1./60);}
 TestTrue(TEXT("Turning the rod kicks the ball forward"),FB->Vel.X>1.5 && FB->LastTouch==0);
 AddInfo(FString::Printf(TEXT("Kick speed %.2f m/s"),FB->Vel.X));
 int32 Wins[2]={0,0},Touches=0,Serves=0,Goals=0,Restarts=0;double Time=0;bool bEnded=true;
 for(int32 M=0;M<8;++M){FB->NewMatch();FB->Skill[0]=FB->Skill[1]=1.1;double T=0;
  while(FB->Winner<0 && T<1200){if(!FB->bLive)FB->Serve(M*7919+int32(T*60));
   FB->AI(0,1./60,M*131+int32(T*600));FB->AI(1,1./60,M*733+int32(T*600)+1);FB->Step(1./60);T+=1./60;}
  if(FB->Winner<0){bEnded=false;AddError(FString::Printf(TEXT("Match %d did not end: %d-%d ball %s vel %s touches %d serves %d call '%s' rods %.3f/%.2f %.3f/%.2f"),M,FB->Goals[0],FB->Goals[1],*FB->Ball.ToString(),*FB->Vel.ToString(),
   FB->Touches,FB->Serves,*FB->Call,FB->RodY[3],FB->RodA[3],FB->RodY[4],FB->RodA[4]));continue;}
  ++Wins[FB->Winner];Touches+=FB->Touches;Serves+=FB->Serves;Time+=T;Goals+=FB->Goals[0]+FB->Goals[1];Restarts+=FB->Restarts;
  TestEqual(TEXT("Winner has 5 goals"),FB->Goals[FB->Winner],UMareFoosball::WinGoals);}
 AddInfo(FString::Printf(TEXT("Foosball: 8 matches, wins %d/%d, %.0f s each, %d touches, %d serves for %d goals, %d goalie restarts"),Wins[0],Wins[1],Time/8,Touches,Serves,Goals,Restarts));
 TestTrue(TEXT("Every match ends"),bEnded);TestTrue(TEXT("Both sides win sometimes"),Wins[0]>0 && Wins[1]>0);
 TestTrue(TEXT("Real play: the men touch the ball many times"),Touches>8*20);
 TestTrue(TEXT("Few dead balls: serves are mostly after goals"),Serves<=Goals+8*2);
 TestTrue(TEXT("A match lasts a few minutes, not seven"),Time/8<240);
 // The heel tap: a ball stopped just behind a rod is played backward instead of dying there.
 FB->NewMatch();LiftAll();for(int32 I=0;I<F::Rods;++I)FB->RodA[I]=0;FB->bLive=true;FB->Ball=FVector2D(F::RodX(3)-.04,0);FB->Vel=FVector2D::ZeroVector;
 for(int32 I=0;I<60 && FB->Vel.X>-.3;++I){FB->AI(0,1./60,I);FB->Step(1./60);}
 TestTrue(TEXT("Heel tap plays a ball stopped behind the rod"),FB->Vel.X<-.3);
 // A ball dead beside the goalie, out of his reach, goes back to his feet.
 FB->NewMatch();LiftAll();FB->bLive=true;FB->Ball=FVector2D(-.64,.22);FB->Vel=FVector2D::ZeroVector;Run(4);
 TestTrue(TEXT("Goalie puts a dead ball near his goal back into play"),FB->bLive && FB->Restarts==1 && FMath::IsNearlyEqual(FB->Ball.X,F::RodX(0)+.045,.01));
 // The player's hands (PlayerControl, what the mouse and the gamepad feed): forward slides the active rod away from the
 // player, sideways turns its feet toward the guest's goal, a click kicks a ball in front of the men toward that goal
 // and the right button lifts them over the ball.
 {using FIn=UMareFoosball::FInput;
  FB->NewMatch();for(int32 I=0;I<F::Rods;++I)FB->RodA[I]=0;FB->bLive=true;FB->Ball=FVector2D(F::RodX(3)+.08,0);FB->Vel=FVector2D::ZeroVector;
  FIn Fwd;Fwd.DY=10;for(int32 I=0;I<10;++I){FB->PlayerControl(Fwd,1./60);FB->Step(1./60);}
  TestTrue(FString::Printf(TEXT("Mouse forward slides the active 5-bar away from the player (active %d, y %.3f)"),FB->Active,FB->RodY[3]),FB->Active==3 && FB->RodY[3]>.02);
  FIn Side;Side.DX=20;FB->PlayerControl(Side,1./60);FB->Step(1./60);
  TestTrue(FString::Printf(TEXT("Mouse right turns the feet forward (%.2f rad)"),FB->RodA[3]),FB->RodA[3]>.2);
  FIn Lift;Lift.bLift=true;for(int32 I=0;I<20;++I){FB->PlayerControl(Lift,1./60);FB->Step(1./60);}
  TestTrue(FString::Printf(TEXT("Right button lifts the men (%.2f rad)"),FB->RodA[3]),FMath::Cos(FB->RodA[3])<F::Lift);
  FB->NewMatch();LiftAll();FB->RodA[3]=0;FB->bLive=true;FB->Ball=FVector2D(F::RodX(3)+.04,0);FB->Vel=FVector2D::ZeroVector;
  FIn Shot;Shot.bShot=true;FB->PlayerControl(Shot,1./60);FB->Step(1./60);
  for(int32 I=0;I<40;++I){FB->PlayerControl(FIn(),1./60);FB->Step(1./60);}
  TestTrue(FString::Printf(TEXT("A click kicks the ball toward the guest's goal (%.2f m/s)"),FB->Vel.X),(FB->Vel.X>1.5 || FB->Goals[0]==1) && FB->LastTouch==0);}
 TestEqual(TEXT("Hits: 5x1 = 3"),UMareFoosball::Hits(5,1),3);TestEqual(TEXT("Hits: 5x4 = 2"),UMareFoosball::Hits(5,4),2);
 TestEqual(TEXT("Hits: 3x5 = 1"),UMareFoosball::Hits(3,5),1);TestEqual(TEXT("Hits: 0x5 = 0"),UMareFoosball::Hits(0,5),0);
 FB->RemoveFromRoot();
 // World data (defects seen in the photos of 06/11): every mesh the table spawns resolves through custom_assets.json (the
 // rods had hard-coded names without the importer's suffix and never appeared), and the guests waiting at the foosball
 // and arcade counters stand clear of the cabinet and of the night players (they stood 15-20 cm inside each other).
 auto Json=[](const TCHAR* Name){FString Text;TSharedPtr<FJsonObject> O;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),O);return O.IsValid()?O:MakeShared<FJsonObject>();};
 const auto Assets=Json(TEXT("custom_assets.json"));
 TArray<FString> Slugs={TEXT("mare_foosball_body"),TEXT("mare_foosball_ball")};
 for(const TCHAR* R:{TEXT("1_coral"),TEXT("2_coral"),TEXT("3_coral"),TEXT("5_coral"),TEXT("1_mar"),TEXT("2_mar"),TEXT("3_mar"),TEXT("5_mar")})Slugs.Add(FString(TEXT("mare_foosball_rod_"))+R);
 for(const FString& Slug:Slugs){FString Path;TestTrue(FString::Printf(TEXT("%s loads"),*Slug),Assets->TryGetStringField(Slug,Path) && LoadObject<UStaticMesh>(nullptr,*Path)!=nullptr);}
 const auto Games=Json(TEXT("business_games.json"));const auto Room=Games->GetObjectField(TEXT("game_room"));
 auto Vec=[](const TSharedPtr<FJsonObject>& O,const TCHAR* F){const TArray<TSharedPtr<FJsonValue>>* A=nullptr;
  return O.IsValid() && O->TryGetArrayField(F,A) && A->Num()==4?FTransform(FRotator(0,(*A)[3]->AsNumber(),0),FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),0)):FTransform::Identity;};
 const FTransform Table=Vec(Room,TEXT("foosball"));TArray<FVector> Night;
 for(const float Side:{-1.f,1.f})Night.Add(Table.TransformPosition(FVector(0,Side*70,0)));
 const TArray<TSharedPtr<FJsonValue>>* Arcades=nullptr;
 if(Room->TryGetArrayField(TEXT("arcades"),Arcades))for(const auto& V:*Arcades){const auto& A=V->AsArray();
  Night.Add(FTransform(FRotator(0,A[3]->AsNumber(),0),FVector(A[0]->AsNumber(),A[1]->AsNumber(),0)).TransformPosition(FVector(0,75,0)));}
 const auto Biz=Games->GetObjectField(TEXT("businesses"));
 for(const TCHAR* Id:{TEXT("pebolim"),TEXT("fliperama")}){const FVector G=Vec(Biz->GetObjectField(Id),TEXT("guest")).GetLocation();
  const FVector L=Table.InverseTransformPosition(G);
  TestTrue(FString::Printf(TEXT("%s guest outside the foosball cabinet and its grips"),Id),FMath::Abs(L.X)>81+30 || FMath::Abs(L.Y)>62+30);
  for(const FVector& N:Night)TestTrue(FString::Printf(TEXT("%s guest 60 cm or more from a night player (%.0f cm)"),Id,FVector::Dist2D(G,N)),FVector::Dist2D(G,N)>=60);}
 return true;
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
 // 6. Seu Severino's pier chapter: 4 fish caught at the pier, 15 customers served during the step, R$ 150.
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareArcadeTest,"MareAlta.Gameplay.Arcade",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareArcadeTest::RunTest(const FString& Parameters)
{
 // CHECKLIST_EXPANSOES 5.4: the two playable arcades. Corrida de Jangada: a rock in the raft's path costs a life (once,
 // with a moment of grace), a fish is netted, three hits end the game, the river speeds up. Pinball: launch, bumpers,
 // bumpers kick and score, the flippers turn up, a ball between the flippers drains, the third drain ends the game.
 FRandomStream R(7);
 FMareJangada J;J.Reset();
 FMareJangada::FThing Rock;Rock.Kind=0;Rock.W=26;Rock.H=24;Rock.X=J.X;Rock.Y=FMareJangada::RaftY-40;J.Things.Add(Rock);J.Spawn=99;
 int32 Ev=0;for(int32 I=0;I<30;++I)Ev|=J.Step(1/30.f,0,R);
 TestTrue(TEXT("jangada: hit by the rock"),(Ev&1)!=0);TestEqual(TEXT("jangada: one life lost"),J.Lives,2);
 FMareJangada::FThing Fish;Fish.Kind=2;Fish.W=18;Fish.H=12;Fish.X=J.X;Fish.Y=FMareJangada::RaftY-30;J.Things.Add(Fish);
 for(int32 I=0;I<30;++I)J.Step(1/30.f,0,R);TestEqual(TEXT("jangada: fish netted"),J.Fish,1);
 const float Before=J.Speed;J.Spawn=99;J.Things.Reset();for(int32 I=0;I<300;++I)J.Step(1/30.f,0,R);
 TestTrue(TEXT("jangada: the river speeds up"),J.Speed>Before);
 for(int32 Hit=0;Hit<3 && !J.bOver;++Hit){J.Hurt=0;FMareJangada::FThing B=Rock;B.X=J.X;B.Y=FMareJangada::RaftY;J.Things.Add(B);J.Step(1/30.f,0,R);}
 TestTrue(TEXT("jangada: game over after the third hit"),J.bOver);
 TestTrue(TEXT("jangada: points count distance and fish"),J.Points()>=10);
 const float SteerFrom=0;FMareJangada K;K.Reset();K.Spawn=99;for(int32 I=0;I<120;++I)K.Step(1/30.f,1,R);
 TestTrue(TEXT("jangada: the raft stays on the river"),K.X<=MareArc::VW-FMareJangada::Bank-FMareJangada::RaftW*.5f+.01f && K.X>SteerFrom);
 // Pinball do Farol: the launch sends the ball up the plunger lane, a bumper kicks it away and scores, a held flipper
 // turns up, a ball between the flippers drains (one ball fewer), the third drain ends the game.
 FMarePinball P;P.Reset();
 TestTrue(TEXT("pinball: the ball waits in the lane"),P.bInLane);
 P.Step(1/60.f,false,false,true);TestTrue(TEXT("pinball: launched up the lane"),P.Vel.Y<-300);
 for(int32 I=0;I<30;++I)P.Step(1/60.f,false,false,false);TestTrue(TEXT("pinball: the ball leaves the lane"),P.Ball.Y<150);
 P.Reset();P.Ball=FMarePinball::BumperPos(2)+FVector2D(0,-18);P.Vel=FVector2D(0,120);
 Ev=0;for(int32 I=0;I<20;++I)Ev|=P.Step(1/60.f,false,false,false);
 TestTrue(TEXT("pinball: bumper hit scores 100"),(Ev&1)!=0 && P.Score>=100);TestTrue(TEXT("pinball: kicked away"),P.Vel.Y<0 || P.Ball.Y<FMarePinball::BumperPos(2).Y);
 P.Reset();P.Step(1/60.f,true,false,false);TestTrue(TEXT("pinball: left flipper turns up"),P.Flip[0]<FMarePinball::FlipRest);
 for(int32 I=0;I<10;++I)P.Step(1/60.f,true,false,false);TestEqual(TEXT("pinball: up to its stop"),P.Flip[0],FMarePinball::FlipUp);
 P.Reset();P.Ball=FVector2D(152,215);P.Vel=FVector2D(0,80);
 for(int32 I=0;I<60 && P.Balls==3;++I)P.Step(1/60.f,false,false,false);
 TestEqual(TEXT("pinball: drained between the flippers"),P.Balls,2);TestTrue(TEXT("pinball: next ball in the lane"),P.bInLane);
 for(int32 Lost=0;Lost<2;++Lost){P.Ball=FVector2D(152,215);P.Vel=FVector2D(0,80);for(int32 I=0;I<60 && !P.bOver && P.Balls==2-Lost;++I)P.Step(1/60.f,false,false,false);}
 TestTrue(TEXT("pinball: game over after the third ball"),P.bOver);
 P.Reset();P.Ball=FVector2D(FMarePinball::LaneX(1),26);P.Vel=FVector2D(0,40);P.Step(1/60.f,false,false,false);
 TestTrue(TEXT("pinball: rollover lane lit"),P.bLanes[1] && P.Score==250);
 // Business hits from the points thresholds of business_games.json.
 auto Defs=MakeShared<FJsonObject>();auto Jd=MakeShared<FJsonObject>();TArray<TSharedPtr<FJsonValue>> At;for(double V:{250.0,600.0,1100.0})At.Add(MakeShared<FJsonValueNumber>(V));
 Jd->SetArrayField(TEXT("hits_at"),At);Defs->SetObjectField(TEXT("jangada"),Jd);
 TestEqual(TEXT("hits: 0 below the first mark"),UMareArcade::HitsFor(0,100,Defs),0);
 TestEqual(TEXT("hits: 2 between marks"),UMareArcade::HitsFor(0,700,Defs),2);
 TestEqual(TEXT("hits: 3 at most"),UMareArcade::HitsFor(0,5000,Defs),3);
 return true;
}
