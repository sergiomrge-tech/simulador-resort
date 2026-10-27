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
 bool CreateCompany(const FString& Name);
 bool SetOpen(bool bOpen);
 bool IsOpen() const;
 int32 Available(const FString& Dish) const;
 double RestockCost(const FString& Dish, int32 Quantity=10) const;
 bool Restock(const FString& Dish, int32 Quantity=10);
 bool Pickup(const FString& Dish);
 bool ReturnCarry();
 /** Checks customer demand, consumes carry and records payment once per delivered item. */
 bool Deliver(const FString& OrderId, const FString& Dish);
 FString AddOrder(const FString& Customer, const TArray<FString>& Dishes);
 bool HireAttendant();
 bool BuyExpansion(const FString& Id);
 bool ClaimMission(const FString& Id, bool bSide=false);
 int32 MissionAmount(const TSharedPtr<FJsonObject>& Mission) const;
 void AdvanceMinutes(double Minutes);
 void Sleep();
 bool Save();
 /** Read-only legacy import; destination always belongs to the Unreal project. */
 bool ImportLegacySave(const FString& Path);
 double Money() const;
 FString Carry() const;
 static TSharedPtr<FJsonObject> Object(const TSharedPtr<FJsonObject>& Parent, const FString& Key);
 static double Number(const TSharedPtr<FJsonObject>& Parent, const FString& Key, double Fallback=0);
 static FString String(const TSharedPtr<FJsonObject>& Parent, const FString& Key);
private:
 bool ReadJson(const FString& Path,TSharedPtr<FJsonObject>& Target) const;
 void Book(double Amount,const FString& Label);
 bool Fail(const FString& Message);
 FString SavePath() const;
};
