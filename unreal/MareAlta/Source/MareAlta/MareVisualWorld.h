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
 /** Weather eased towards today's state (MPC_MareTime Rain/Wind/Storm) and the rain curtains around the camera. */
 float RainNow=0,WindNow=.2f,StormNow=0;
 UPROPERTY() TArray<TObjectPtr<class AStaticMeshActor>> RainCurtains;
 /** Overcast sky: the volumetric cloud material (dynamic copy) and the atmosphere follow the rain/storm. */
 UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> CloudMaterial;
 UPROPERTY() TObjectPtr<class USkyAtmosphereComponent> Atmosphere;
 bool bSkyLooked=false;
 void UpdateWeather(float DeltaSeconds,class UMareSimulation* Sim);
 /** Footprints the player leaves on the beach sand: a ring of instanced imprints (M_SandFootprint), alternating
  *  feet along the walking direction, fading out over three minutes. */
 UPROPERTY() TObjectPtr<AActor> FootprintActor;
 UPROPERTY() TObjectPtr<class UInstancedStaticMeshComponent> Footprints;
 TArray<float> FootprintBorn;
 FVector LastStep=FVector(1e9);
 int32 NextFootprint=0;
 bool bLeftFoot=false;
 void UpdateFootprints();
public:
 int32 FootprintCount()const;
public:
 int32 LampCount()const{return Lamps.Num();}
 /** Gives every local light of the world a draw distance (mare.LightDrawDistance) unless it has one. */
 void CullLocalLights();
 struct FLightCullState{bool bShadow=true;};
 TMap<TWeakObjectPtr<class ULocalLightComponent>,FLightCullState> LightCull;
 FVector LightCullKey=FVector(-1);
};
