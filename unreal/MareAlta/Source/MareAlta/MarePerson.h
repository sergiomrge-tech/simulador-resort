#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "MarePerson.generated.h"
class UAnimSequence;
class UStaticMeshComponent;
class AMareServiceTarget;
class APlayerController;

UENUM(BlueprintType)
enum class EMarePersonStage:uint8 {Approaching,Order,Products,ToTable,Eating,Leaving};
/** Physical customer/attendant using the preserved rig, clothing and authored animation clips. */
UCLASS()
class MAREALTA_API AMarePerson : public ACharacter
{
 GENERATED_BODY()
public:
 AMarePerson();
 virtual void Tick(float DeltaSeconds) override;
 bool SetAppearance(int32 AppearanceVariant);
 void PlayPose(const FString& Name,bool bLoop=true);
 bool WalkTo(const FVector& Goal);
 bool AtGoal()const;
 void HoldProduct(const FString& Dish);
 void ClearProducts();
 void Interact(APlayerController* Player);
 UPROPERTY() TObjectPtr<AMareServiceTarget> Interaction;
 UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> CarriedMeshes;
 UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> HairMeshes;
 UPROPERTY() TMap<FString,TObjectPtr<UAnimSequence>> Clips;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 FString PersonName;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") FString SaveId;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bConsumed=false;
 /** Keep future save fields when rewriting this customer's known state. */
 TSharedPtr<class FJsonObject> SaveMetadata;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 FString OrderId;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 TArray<FString> Plan;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 TArray<FString> Delivered;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 EMarePersonStage Stage=EMarePersonStage::Approaching;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 int32 Variant=0;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 int32 CounterIndex=-1;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 int32 TableIndex=-1;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 bool bEmployee=false;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 float Elapsed=0;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 FVector Destination=FVector::ZeroVector;
 static class UStaticMesh* ProductMesh(const FString& Dish,bool bUsed=false);
 static TSharedPtr<class FJsonObject> AssetCatalog();
private:
 FString Playing;
 FTransform ReferenceBoneTransform(FName Bone)const;
};
