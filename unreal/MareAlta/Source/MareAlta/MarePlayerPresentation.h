#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MarePlayerPresentation.generated.h"
class UAnimSequence;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/** Reuses the authored clothed rig for first-person body, grips and swim poses. */
UCLASS()
class MAREALTA_API UMarePlayerPresentation : public UActorComponent
{
 GENERATED_BODY()
public:
 UMarePlayerPresentation();
 virtual void BeginPlay() override;
 virtual void TickComponent(float DeltaSeconds,ELevelTick TickType,FActorComponentTickFunction* Function) override;
 /** A brief reaching gesture, shared by E and mouse interactions. */
 void ReachFor(const FVector& Position);
 /** Controlled opening traversal still plays locomotion while character movement is locked. */
 void SetScriptedWalking(bool bWalking){bScriptedWalking=bWalking;}
 /** Snapshot used by the animation proxy before worker-thread pose evaluation. */
 bool HandTarget(int32 Hand,FVector& Target,FVector& Elbow,float& Weight)const;
 UPROPERTY() TObjectPtr<USkeletalMeshComponent> ViewBody;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> HeldProduct;
 UPROPERTY() TMap<FString,TObjectPtr<UAnimSequence>> Clips;
 FString HeldDish;
private:
 FString Playing;
 bool bScriptedWalking=false;
 float ReachRemaining=0;
 FVector ReachPosition=FVector::ZeroVector;
 void UpdateAnimation();
 void UpdateCarry();
 void BuildHair(const TSharedPtr<class FJsonObject>& Row);
};
