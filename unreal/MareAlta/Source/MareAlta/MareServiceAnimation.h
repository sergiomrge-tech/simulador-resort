#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/ActorComponent.h"
#include "MareServiceAnimation.generated.h"

/** Authored locomotion/seated clips with arm IK; no replacement of the clothing rig. */
UCLASS(Transient)
class MAREALTA_API UMareServiceAnimInstance : public UAnimSingleNodeInstance
{
 GENERATED_BODY()
protected:
 virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
};

/** Update props after the current skeletal pose, with a measured grip and an upright vessel. */
UCLASS()
class MAREALTA_API UMareCarryPresentation : public UActorComponent
{
 GENERATED_BODY()
public:
 UMareCarryPresentation();
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
};
