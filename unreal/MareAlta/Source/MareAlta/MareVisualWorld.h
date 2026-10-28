#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareVisualWorld.generated.h"
class ALight;
class AExponentialHeightFog;
class ATextRenderActor;
/** Natural daylight and practical interior light linked to the saved game clock. */
UCLASS()
class MAREALTA_API UMareVisualWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 /** Apply saved ownership to region geometry without changing the player's save. */
 void RefreshExpansions();
private:
 float Clock=0;
 bool bRegionsIndexed=false;
 TMap<FName,TArray<TWeakObjectPtr<AActor>>> ExpansionRegions;
 TMap<FName,bool> RegionVisibility;
 UPROPERTY() TObjectPtr<ALight> Sun;
 UPROPERTY() TObjectPtr<ALight> Moon;
 UPROPERTY() TObjectPtr<AExponentialHeightFog> Fog;
 UPROPERTY() TArray<TObjectPtr<ALight>> Practical;
 UPROPERTY() TArray<TObjectPtr<ATextRenderActor>> Signs;
};
