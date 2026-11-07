#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareBusinessWorld.generated.h"
class AMareServiceTarget;
class AMarePerson;

/** Village businesses in the world: an E target at each owned business counter (opens the three-round counter
 *  task) and a customer waiting in front of it while a task is available this hour. Positions come from
 *  Content/Data/business_games.json; the simulation (MareBusiness.cpp) decides when a customer is due. */
UCLASS()
class MAREALTA_API UMareBusinessWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
private:
 float Clock=0;
 UPROPERTY() TMap<FString,TObjectPtr<AMareServiceTarget>> Counters;
 UPROPERTY() TMap<FString,TObjectPtr<AMarePerson>> Waiting;
 /** The ice cream queue behind the first customer (3.1): up to three more people in line. */
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> IceLine;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> PastelLine;
 /** Game-room machines (foosball, arcades) and the guests playing them at night. */
 UPROPERTY() TArray<TObjectPtr<class AStaticMeshActor>> Machines;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> NightPlayers;
 void SyncGameRoom(class UMareSimulation* S);
};
