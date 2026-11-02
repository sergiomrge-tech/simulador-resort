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
 UFUNCTION(BlueprintCallable,Category="Presentation") bool SetAppearance(int32 AppearanceVariant);
 /** MetaHuman built in /Game/People/MetaHumans/<Name>: its blueprint follows this rig mesh, animated with the retargeted clips. */
 UFUNCTION(BlueprintCallable,Category="Presentation") bool SetMetaHuman(const FString& Name);
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") FString MetaHuman;
 UPROPERTY() TObjectPtr<class UChildActorComponent> MetaHumanBody;
 UPROPERTY() TObjectPtr<USkeletalMeshComponent> Swimwear;
 UPROPERTY() TObjectPtr<USkeletalMeshComponent> Shoes;
 /** Roster role (staff, hotel, pousada, village, beach) picking clothes colours and footwear. */
 FString MetaRole;
 UFUNCTION(BlueprintCallable,Category="Presentation") void PlayPose(const FString& Name,bool bLoop=true);
 UFUNCTION(BlueprintCallable,Category="Presentation") bool WalkTo(const FVector& Goal);
 bool AtGoal()const;
 UFUNCTION(BlueprintCallable,Category="Presentation") void HoldProduct(const FString& Dish);
 void ClearProducts();
 /** Smooth drinking gesture during consumption; zero while walking or after disposal. */
 float DrinkGesture()const;
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
 /** Staff role (definitions.json staff key): picks the MetaHuman and uniform from metahumans.json "staff_<role>"
  *  (falls back to "staff"). */
 FString StaffRole;
 /** Pose held while standing still at work (UMareStaffWorld), e.g. Interact while cleaning; Walk while gliding. */
 FString WorkPose;
 /** Village walkers/residents never participate in the kiosk order state machine. */
 bool bAmbient=false,bConversing=false;
 /** Ambient guest placed on a chair (hotel restaurant); keeps the sitting pose. */
 bool bSeated=false;
 /** Clothing style, applied on the first tick once role flags are set (employees keep the uniform). */
 enum class EOutfit:uint8{Auto,Uniform,Casual,Beach,Swim,Social};
 EOutfit Outfit=EOutfit::Auto;
 void ApplyOutfit(EOutfit Style);
 /** QA/tools: 1 uniform, 2 casual, 3 beach, 4 swim (bikini/trunks), 5 social. */
 UFUNCTION(BlueprintCallable,Category="Presentation") void SetOutfitStyle(int32 Style){ApplyOutfit(EOutfit(FMath::Clamp(Style,1,5)));}
private:
 bool bOutfitApplied=false;
public:
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
