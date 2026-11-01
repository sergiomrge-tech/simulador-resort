#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Dom/JsonObject.h"
#include "MareSimulation.generated.h"

/** Native economy and progression. JSON retains fields from the original save format. */
UCLASS()
class MAREALTA_API UMareSimulation : public UGameInstanceSubsystem
{
 GENERATED_BODY()
public:
 virtual void Initialize(FSubsystemCollectionBase& Collection) override;
 TSharedPtr<FJsonObject> State;
 TSharedPtr<FJsonObject> Definitions;
 FString LastMessage;
 /** Separate test/import destination; blank uses this UE project Saved folder. */
 FString SaveDirectory;
 /** Creates the company without changing existing inventory or personal saves. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool CreateCompany(const FString& Name);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool SetOpen(bool bOpen);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool IsOpen() const;
 /** Expansion licences gate sale/pickup while keeping display props visible. */
 UFUNCTION(BlueprintPure,Category="Maré Alta")
 bool IsDishUnlocked(const FString& Dish) const;
 /** Previously accepted orders remain fulfillable after the licence migration. */
 UFUNCTION(BlueprintPure,Category="Maré Alta")
 bool CanSupplyDish(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 int32 Available(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 double RestockCost(const FString& Dish, int32 Quantity=10) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Restock(const FString& Dish, int32 Quantity=10);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Pickup(const FString& Dish,bool bStaff=false);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool ReturnCarry(bool bStaff=false);
 /** Checks customer demand, consumes carry and records payment once per delivered item. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Deliver(const FString& OrderId, const FString& Dish,bool bStaff=false);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 FString AddOrder(const FString& Customer, const TArray<FString>& Dishes);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool HireAttendant();
 /** Lets the attendant go: carried product returns to stock, no refund, no wage from the next night. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool DismissAttendant();
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool BuyExpansion(const FString& Id);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool ClaimMission(const FString& Id, bool bSide=false);
 int32 MissionAmount(const TSharedPtr<FJsonObject>& Mission) const;
 /** Village chapters open in sequence and keep their step in prog.ch, as in the approved save. */
 TSharedPtr<FJsonObject> ChapterDefinition(const FString& Id) const;
 int32 ChapterStep(const FString& Id) const;
 bool IsChapterOpen(const FString& Id) const;
 bool IsChapterDone(const FString& Id) const{return ChapterStep(Id)>=3;}
 /** Current/required amount of the active step; deliver/pay consume only in AdvanceChapter. */
 int32 ChapterStepProgress(const FString& Id,int32& Goal) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool AdvanceChapter(const FString& Id);
 /** Market purchase of raw supplies, charged once and only when the full amount is affordable. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool BuySupply(const FString& Item,int32 Quantity);
 double SupplyCost(const FString& Item,int32 Quantity) const;
 /** Fame level 1..10 from prog.fame_xp using the original thresholds. */
 int32 FameLevel() const;
 FString FameName() const;
 void AddFame(int32 Xp);
 /** Average guest rating (1..5) over the saved ratings list. */
 double Stars() const;
 /** Grand Hotel occupancy 0.15..0.98 from rating and fame, as in the approved version. */
 double HotelOccupancy() const;
 /** Books one night of the Grand Hotel (suites, dining, staff) and stores prog.hotel. */
 void HotelNight();
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 void AdvanceMinutes(double Minutes);
 /** Closes the day: wages once per day, summary in ue_last_day, ledger totals reset. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 void Sleep();
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Save();
 /** Read-only legacy import; destination always belongs to the Unreal project. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool ImportLegacySave(const FString& Path);
 // ---- Customization (Content/Data/customization.json): 5 tiers per object, tier 1 is the starting look.
 /** Catalogue loaded on first use (also works in automation tests that skip Initialize). */
 TSharedPtr<FJsonObject> CustomDefs() const;
 TSharedPtr<FJsonObject> CustomSlot(const FString& Place,const FString& Slot) const;
 /** Selected tier 1..5 (state custom.<place>.<slot>.tier). */
 UFUNCTION(BlueprintPure,Category="Maré Alta") int32 CustomTier(const FString& Place,const FString& Slot) const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool OwnsCustomTier(const FString& Place,const FString& Slot,int32 Tier) const;
 /** Price of a tier: slot base_price x price_mult[tier-1]; tier 1 is free. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double CustomPrice(const FString& Place,const FString& Slot,int32 Tier) const;
 /** Buys the tier when not owned (charged once), then selects it. Owned tiers switch for free. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool BuyCustom(const FString& Place,const FString& Slot,int32 Tier);
 /** Comfort / beauty points of a place: sum over slots of weight x (tier-1). */
 double PlaceComfort(const FString& Place) const;
 double PlaceBeauty(const FString& Place) const;
 double CustomEffect(const FString& Key,double Fallback=0) const;
 /** Kiosk gameplay from the decor: customer arrival rate x, tip share, patience x, attendant speed x. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskArrivalFactor() const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskTipRate() const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskPatienceFactor() const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskServiceSpeed() const;
 /** Recipe level 1..5 per dish (state recipes.<dish>): raises the sale price and the demand. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") int32 RecipeLevel(const FString& Dish) const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double DishPrice(const FString& Dish) const;
 /** Cost of the next recipe level (0 when maxed). */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double RecipeUpgradeCost(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool UpgradeRecipe(const FString& Dish);
 FString RecipeTitle(const FString& Dish,int32 Level=0) const;
 /** Relative chance a customer orders this dish (recipe level makes it more popular). */
 double DishDemand(const FString& Dish) const;
 // ---- Places beyond the kiosk (customization.json "places" + "operations").
 TSharedPtr<FJsonObject> PlaceDef(const FString& Place) const;
 /** Bought expansion / business behind a place (the home and the kiosk are always available). */
 bool IsPlaceAvailable(const FString& Place,FString* Reason=nullptr) const;
 double PlaceEffect(const FString& Place,const FString& Key,double Fallback=0) const;
 /** Sum over slots of Key x (tier-1), e.g. "rate", "income", "seats". */
 double SlotSum(const FString& Place,const FString& Key) const;
 /** Income multiplier of a place: 1 + income_per_point x (comfort+beauty) + service upgrades. */
 double PlaceIncomeFactor(const FString& Place) const;
 /** Extra occupancy from the pool (pousada and hotel) and from the four hotel areas. */
 double StayBonus() const;
 double HotelCustomBonus() const;
 int32 PousadaRooms() const;
 double PousadaRate() const;
 double PousadaOccupancy() const;
 /** Books one night of the pousada (rooms x rate x occupancy, plus tips); stores prog.pousada. */
 void PousadaNight();
 int32 TourSeats(const TSharedPtr<FJsonObject>& Tour) const;
 int32 TourPassengers(const TSharedPtr<FJsonObject>& Tour) const;
 /** Expected income of an hourly operation (bar, pool) or business for one open hour, before chance. */
 double HourlyIncome(const FString& Id) const;
 double BusinessRate(const FString& Id) const;
 /** Books the hour that just ended [Hour-1, Hour): bar, pool, tours and businesses. Once per game hour. */
 void OperateHour(int32 Hour);
 /** Income booked today by a place (bar, pool, passeios, biz_<id>). */
 double OpsToday(const FString& Place) const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool HasStaff(const FString& Role) const;
 /** Hires an expansion role (bartender, camareira, guia): needs its expansion; wage charged at night. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool HireStaff(const FString& Role);
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool DismissStaff(const FString& Role);
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool OwnsBusiness(const FString& Id) const;
 /** Buys a village business (definitions.businesses): needs its chapter and fame level. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool BuyBusiness(const FString& Id);
 bool CanBuyBusiness(const FString& Id,FString& Reason) const;
 /** Home comfort makes the player walk faster; home beauty brings fame every night. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double HomeSpeedFactor() const;
 /** One line with the current effect of a place's decor, for the phone. */
 FString PlaceSummary(const FString& Place) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 double Money() const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 FString Carry(bool bStaff=false) const;
 static TSharedPtr<FJsonObject> Object(const TSharedPtr<FJsonObject>& Parent, const FString& Key);
 static double Number(const TSharedPtr<FJsonObject>& Parent, const FString& Key, double Fallback=0);
 static FString String(const TSharedPtr<FJsonObject>& Parent, const FString& Key);
private:
 bool ReadJson(const FString& Path,TSharedPtr<FJsonObject>& Target) const;
 void Book(double Amount,const FString& Label);
 bool Fail(const FString& Message);
 FString SavePath() const;
 mutable TSharedPtr<FJsonObject> CustomCatalog;
};
