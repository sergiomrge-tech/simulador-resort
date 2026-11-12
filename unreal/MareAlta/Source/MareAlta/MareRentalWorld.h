#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareRentalWorld.generated.h"
class AStaticMeshActor;
class AMareServiceTarget;

/** The rental's kayak adrift (CHECKLIST_EXPANSOES 3.3): while MareSimulation::IsKayakAdrift, a kayak bobs on the sea
 *  off the beach, drifting slowly away; swimming up and pressing E takes it in tow (it follows the swimmer), and
 *  bringing it to the beach in front of the rental returns it (MareSimulation::RescueKayak). */
UCLASS()
class MAREALTA_API UMareRentalWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 bool IsActive()const;
 FString Status()const;
 void Tow();
 /** QA: "near" (puts the player beside the kayak), "home" (the towed kayak and the player at the beach), "state". */
 FString QA(const FString& Cmd);
private:
 UPROPERTY() TObjectPtr<AStaticMeshActor> Kayak;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Target;
 FVector Pos=FVector::ZeroVector;float Yaw=0,Time=0;bool bTowed=false;
};
