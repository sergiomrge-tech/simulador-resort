#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareKioskWorld.generated.h"
class AMarePerson;
class UMareSimulation;
class AMareServiceTarget;

/** Two counter places, reserved tables and one physical attendant. No preparation/payment phase. */
UCLASS()
class MAREALTA_API UMareKioskWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Initialize(FSubsystemCollectionBase& Collection) override;
 virtual void Deinitialize() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 bool Serve(AMarePerson* Person,bool bStaff);
 void CleanTable(int32 Index);
 /** Capture physical state in the same atomic save as its economy. Never writes a file. */
 void CaptureState();
 /** Clear only this subsystem's transient actors before loading another save. */
 void ResetPhysicalState();
 /** Availability includes a seated guest even after their used dishes are collected. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool IsTableReserved(int32 Index)const{return ReservedTables.Contains(Index);}
private:
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Guests;
 UPROPERTY() TObjectPtr<AMarePerson> Attendant;
 UPROPERTY() TArray<TObjectPtr<AActor>> DirtyObjects;
 TArray<FVector> CounterPoints;
 TArray<FVector> CounterStaffPoints;
 TArray<FVector> TablePoints;
 TArray<FVector> TableApproaches;
 TArray<FVector> TableSurfaces;
 TArray<float> TableYaw;
 TSet<int32> ReservedTables;
 TSet<int32> DirtyTables;
 float Arrival=15;
 float StaffClock=0;
 int32 LastDay=-1;
 bool bRestored=false;
 bool bRestoring=false;
 FDelegateHandle TearDownHandle;
 void BeforeTearDown(UWorld* World);
 UMareSimulation* Sim()const;
 void SpawnCustomer();
 void UpdateCustomer(AMarePerson* Person);
 void UpdateAttendant(float DeltaSeconds);
 void FinishCounter(AMarePerson* Person);
 void Leave(AMarePerson* Person);
 void MakeDirty(AMarePerson* Person);
 void CreateInteraction(AMarePerson* Person);
 void SpawnDirtyTable(int32 Table,const TArray<FString>& Items);
 void RestoreWorld();
 void RestoreGuest(const TSharedPtr<class FJsonObject>& Row);
 void ResumeGuest(AMarePerson* Person);
 void RecoverOrders();
 TSharedPtr<class FJsonObject> CaptureGuest(AMarePerson* Person,TSet<FString>& Claimed)const;
 static FVector FromGodot(const TArray<TSharedPtr<class FJsonValue>>& Values,float Height=0);
};
