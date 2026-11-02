#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MarePoolWorld.generated.h"
class AMareServiceTarget;
class AStaticMeshActor;

/** Pool day use in the world: floating leaf clusters on the water (one per quarter of dirt, E scoops), used towels
 *  crumpled on the loungers (E collects) and the popsicle cooler by the deck (E sells what the bathers asked for).
 *  Positions come from Content/Data/pool.json; the simulation (MarePool.cpp) owns the state. */
UCLASS()
class MAREALTA_API UMarePoolWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
private:
 float Clock=0;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Cooler;
 UPROPERTY() TObjectPtr<AStaticMeshActor> CoolerModel;
 /** Key "leaf:<spot>" or "towel:<lounger>": the prop and its E target. */
 UPROPERTY() TMap<FString,TObjectPtr<AStaticMeshActor>> Props;
 UPROPERTY() TMap<FString,TObjectPtr<AMareServiceTarget>> Targets;
 void Show(const FString& Key,bool bWanted,const TCHAR* Mesh,const FVector& At,float Yaw,FName Action,const FString& Label,int32 Data,float Focus);
};
