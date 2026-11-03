#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareMarineWorld.generated.h"
class AStaticMeshActor;
class AActor;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;

/** One slow daytime sailing ship, an anchored night cruise, a breaching whale, a fishing boat and a jangada
 *  sailing past along the coast by day, and the seagulls gliding in circles over the beach. */
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
 /** Boats passing along the coast (tools/ue58/gen_boats.py models): a fishing boat eastwards, a jangada westwards. */
 UPROPERTY() TObjectPtr<AStaticMeshActor> PassingBoat;
 UPROPERTY() TObjectPtr<AStaticMeshActor> PassingRaft;
 /** Exported seagull_fly instances (World_0536): each glides around the spot it was placed at. */
 struct FGull{TWeakObjectPtr<UInstancedStaticMeshComponent> Component;int32 Index=0;FVector Centre=FVector::ZeroVector;FVector Scale=FVector::OneVector;float Radius=700,Speed=.25f,Phase=0;};
 TArray<FGull> Gulls;
 bool bGullsIndexed=false;
 void UpdateLife(float Time,bool bDay);
public:
 int32 GullCount()const{return Gulls.Num();}
 bool IsPassingBoatVisible()const;
};
