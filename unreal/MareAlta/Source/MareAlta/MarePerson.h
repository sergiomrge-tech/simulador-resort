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
 /** Beachwear worn over the swimwear (tank top, board shorts, cover-up), metahumans.json "beachwear". */
 UPROPERTY() TArray<TObjectPtr<USkeletalMeshComponent>> Overwear;
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
 /** A phone held up in front of the face (selfie): the right arm reaches for it and it faces the head. */
 UPROPERTY() TObjectPtr<UStaticMeshComponent> SelfiePhone;
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
 /** Name badge on the uniform's left chest (staff with a role), following the spine. */
 UPROPERTY() TObjectPtr<UStaticMeshComponent> Badge;
 /** Distance from spine_05 to the shirt surface in front (cm), per body. */
 float BadgeMaleAhead=13.f,BadgeFemaleAhead=15.f;
 void AttachBadge();
 /** Village walkers/residents never participate in the kiosk order state machine. */
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bAmbient=false;
 bool bConversing=false;
 /** Ambient guest placed on a chair (hotel restaurant); keeps the sitting pose. */
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bSeated=false;
 /** Where the pelvis must end up when seated (world cm: seat centre, ~11 cm above the seat top). Body sizes differ,
  *  so after the sitting clip runs the actor is shifted until the animated pelvis lands there (and again after a
  *  MetaHuman swap). Zero = no seat point (the actor transform is trusted as is). */
 FVector SeatPelvis=FVector::ZeroVector;
 float SeatAlignIn=-1;
 /** Seat i of restaurant table t from Content/Data/hotel_seats.json (mare_hud.chair_seats, the real chairs):
  *  seat top and the yaw facing the table. */
 static bool HotelSeat(int32 Table,int32 Index,FVector& SeatTop,float& Yaw);
 /** Places a seated person on a seat: rough actor transform now, exact pelvis alignment once the clip plays. */
 void SitOn(const FVector& SeatTop,float Yaw);
 /** Already placed on a seat (kiosk table points): find the seat top straight below the sitting pelvis (trace) and
  *  align on it, so taller and shorter bodies all sit on the stool instead of above or inside it. */
 void AlignToSeatBelow();
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
