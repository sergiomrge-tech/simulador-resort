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
};
