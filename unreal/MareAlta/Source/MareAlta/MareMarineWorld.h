#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareMarineWorld.generated.h"
class AStaticMeshActor;
class AActor;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;

/** One slow daytime sailing ship, an anchored night cruise, and a breaching whale. */
UCLASS()
class MAREALTA_API UMareMarineWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 bool HasMarineModels() const;
 bool IsSailVisible() const;
 bool IsCruiseVisible() const;
 float WhalePhase() const{return CurrentPhase;}
 bool IsWhaleVisible() const;
 bool IsRippleVisible() const;
private:
 void SpawnModels();
 bool bInitialized=false;
 bool bPreviousImpact=false;
 float CurrentPhase=0.f;
 UPROPERTY() TObjectPtr<AStaticMeshActor> Sail;
 UPROPERTY() TObjectPtr<AStaticMeshActor> Cruise;
 UPROPERTY() TObjectPtr<AStaticMeshActor> Whale;
 UPROPERTY() TObjectPtr<AStaticMeshActor> Ripple;
 UPROPERTY() TObjectPtr<AActor> SprayActor;
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Spray;
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> RippleMaterial;
};
