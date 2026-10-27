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
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 bool Serve(AMarePerson* Person,bool bStaff);
 void CleanTable(int32 Index);
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
 UMareSimulation* Sim()const;
 void SpawnCustomer();
 void UpdateCustomer(AMarePerson* Person);
 void UpdateAttendant(float DeltaSeconds);
 void FinishCounter(AMarePerson* Person);
 void Leave(AMarePerson* Person);
 void MakeDirty(AMarePerson* Person);
 static FVector FromGodot(const TArray<TSharedPtr<class FJsonValue>>& Values,float Height=0);
};
