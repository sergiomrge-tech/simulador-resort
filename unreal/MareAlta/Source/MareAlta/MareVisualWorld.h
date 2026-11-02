#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareVisualWorld.generated.h"
class ALight;
class AExponentialHeightFog;
class ATextRenderActor;
class APostProcessVolume;
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
 UPROPERTY() TObjectPtr<APostProcessVolume> Exposure;
 /** Bounded volumes inside buildings (tag MareInterior): their own exposure, so the night setting that
  *  brightens the dark street does not blow the lit lobby, suite and bungalows out to white. */
 UPROPERTY() TArray<TObjectPtr<APostProcessVolume>> Interiors;
 UPROPERTY() TObjectPtr<ALight> Sun;
 UPROPERTY() TObjectPtr<ALight> Moon;
 UPROPERTY() TObjectPtr<AExponentialHeightFog> Fog;
 UPROPERTY() TArray<TObjectPtr<ALight>> Practical;
 UPROPERTY() TArray<TObjectPtr<ATextRenderActor>> Signs;
 /** Interaction point on the Grand Hotel reception desk, hidden until the hotel is bought. */
 UPROPERTY() TObjectPtr<class AMareServiceTarget> Reception;
 /** Grand Hotel elevators: the two lobby doors go up to the suite, the suite door comes back down. */
 UPROPERTY() TArray<TObjectPtr<class AMareServiceTarget>> Elevators;
 UPROPERTY() TObjectPtr<class UMaterialParameterCollection> TimeCollection;
 UPROPERTY() TObjectPtr<class ASkyLight> Sky;
 /** Night lamps: one shadowless point light per street-lamp globe, bulb, lantern and pool light. */
 struct FLamp{TWeakObjectPtr<class UPointLightComponent> Light;TWeakObjectPtr<AActor> Source;float Candela=0;};
 TArray<FLamp> Lamps;
 UPROPERTY() TObjectPtr<AActor> LampHolder;
 void BuildLamps();
public:
 int32 LampCount()const{return Lamps.Num();}
};
