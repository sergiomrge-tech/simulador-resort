#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareEventsWorld.generated.h"
class AStaticMeshActor;
class APointLight;

/** The party of the day on the beach (events.json party_spot): quermesse stalls and bunting, the junina bonfire with
 *  a flickering light, the DJ booth with its banner, the carnaval mix; paid decoration adds more bunting and a banner.
 *  Rebuilt whenever today's event or the preparations change. */
UCLASS()
class MAREALTA_API UMareEventsWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 /** Props currently placed (QA). */
 int32 PropCount() const{return Props.Num();}
private:
 float Clock=0;
 FString Shown;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Props;
 UPROPERTY() TObjectPtr<APointLight> Fire;
 /** Simulated flames of the junina bonfire (Niagara Fluids smoke-fire template). */
 UPROPERTY() TObjectPtr<class UNiagaraComponent> Flames;
 /** Second sheet of the 2D gas fire, turned 90 degrees, so the column of fire reads from every side (10/11). */
 UPROPERTY() TObjectPtr<class UNiagaraComponent> Flames2;
 /** Villagers and walkers standing near the party dance (mocap clips); released when they leave or it ends. */
 TArray<TWeakObjectPtr<class AMarePerson>> Dancers;
 FVector PartyCentre=FVector::ZeroVector;
 void UpdateDancers();
 void Clear();
};
