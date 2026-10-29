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
 bool IsSeated()const{return bSeated;}
 bool IsTVOn()const{return bTV;}
 bool IsStereoOn()const{return bStereo;}
 bool IsShowerOn()const{return bShower;}
 /** Saves resume on free floor rather than inside the sofa collision. */
 FTransform StandingPose(const FTransform& Current)const{return bSeated?Standing:Current;}
private:
 bool bReady=false,bTV=false,bStereo=false,bShower=false,bSeated=false;
 FTransform Standing;
 UPROPERTY() TObjectPtr<AStaticMeshActor> TVScreen;
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> ShowerDrops;
 void Setup();
 AMareServiceTarget* Target(FName Action,const FString& Label,FVector Position,float Reach=170);
};
