#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareHomeWorld.generated.h"
class AMareServiceTarget;
class AStaticMeshActor;
class UInstancedStaticMeshComponent;

/** House interactions use the furnished house already in the migrated map. */
UCLASS()
class MAREALTA_API UMareHomeWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 /** Toggle appliances or sit using a physical target, never through a duplicate menu. */
 void Use(FName Action);
 /** Restore the free standing location before leaving a seat. */
 void Stand();
 /** Fade out, advance one day and wake on the free bedside floor. */
 void StartSleep();
 bool IsSleeping()const{return SleepTime>=0;}
 bool IsSeated()const{return bSeated;}
 bool IsTVOn()const{return bTV;}
 bool IsStereoOn()const{return bStereo;}
 bool IsShowerOn()const{return bShower;}
 /** Saves resume on free floor rather than inside the sofa collision. */
 FTransform StandingPose(const FTransform& Current)const{return bSeated?Standing:Current;}
private:
 bool bReady=false,bTV=false,bStereo=false,bShower=false,bSeated=false;
 float SleepTime=-1;
 bool bDayAdvanced=false;
 FTransform Standing;
 UPROPERTY() TObjectPtr<AStaticMeshActor> TVScreen;
 /** Coast-landscape picture shown on the TV (the old CRT's screen actor, or the "mare_tv_screen" slot of a new set). */
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> TVPicture;
 TWeakObjectPtr<UMeshComponent> LitSet;bool bLitShown=false;
 /** Switches the picture of whichever TV the house has now (customization home/tv; tier 1 = the old CRT). */
 void UpdateTV();
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> ShowerDrops;
 void Setup();
 AMareServiceTarget* Target(FName Action,const FString& Label,FVector Position,float Reach=170);
};
