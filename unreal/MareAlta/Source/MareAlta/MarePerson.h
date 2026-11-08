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
 /** A short one-shot gesture (07/11, reference game: people that visibly take and hand things): the clip plays once for
  *  Seconds while the automatic pose choice waits; ignored when the clip is not loaded. */
 void PlayGesture(const FString& Name,float Seconds);
 float GestureLeft=0;
 UFUNCTION(BlueprintCallable,Category="Presentation") bool WalkTo(const FVector& Goal);
 bool AtGoal()const;
 UFUNCTION(BlueprintCallable,Category="Presentation") void HoldProduct(const FString& Dish);
 void ClearProducts();
 /** Facial expression for a few seconds with a short wordless voice: "smile" (served, a deal closed), "hmm"
  *  (choosing from the menu) or "annoyed" (a counter-offer, leaving the reception); it eases in and out. */
 UFUNCTION(BlueprintCallable,Category="Presentation") void Express(const FString& Mood,float Seconds=4.f);
 /** Face rig control curves for this frame (blinks + mood), read by UMareFaceAnimInstance on the game thread. */
 void FaceCurves(TArray<TPair<FName,float>>& Out)const;
 /** Woman or man: MetaHumans by their preset name (metahumans.json "men"; every MetaHuman body shares one skeleton
  *  stored under Common/Female, so its path says nothing), the old rig people by their skeleton. */
 bool IsWoman()const;
 FString Mood;float MoodLeft=0,MoodTotal=1,NextBlink=0,BlinkAt=-10;
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
 /** A table or counter in front of the seat (found by tracing ahead of the pelvis once seated): the arms rest on its
  *  top instead of the sitting clip's pose, which put forearms through the tabletop (mare_hud armaudit). */
 bool bTableAhead=false;
 float TableTopZ=0,TableEdge=0;
 FVector TableSeat=FVector::ZeroVector;
 /** Seat i of restaurant table t from Content/Data/hotel_seats.json (mare_hud.chair_seats, the real chairs):
  *  seat top and the yaw facing the table. */
 static bool HotelSeat(int32 Table,int32 Index,FVector& SeatTop,float& Yaw);
 /** Places a seated person on a seat: rough actor transform now, exact pelvis alignment once the clip plays. */
 void SitOn(const FVector& SeatTop,float Yaw);
 /** A pose kept whatever the person does (the bus driver riding the bus): survives the MetaHuman swap. */
 FString HoldPose;
 /** Already placed on a seat (kiosk table points): find the seat top straight below the sitting pelvis (trace) and
  *  align on it, so taller and shorter bodies all sit on the stool instead of above or inside it. */
 void AlignToSeatBelow();
 /** Sunbather lying face up on a beach towel (03/11, "deitar na canga, de barriga para cima"): the start of the
  *  Cheer capture (standing square, hands on the chest) laid on its back along the towel axis (AxisYaw, head first); once the pose plays the body is centred on the towel,
  *  pelvis 11 cm above it. (The Fab LieDown capture lies curled on its side, rejected for the beach.) */
 void LieOn(const FVector& TowelCentre,float AxisYaw,float InRecline=0.f);
 bool bLying=false;
 /** Degrees the torso bends up at the hips while lying (a lounger backrest); 0 = flat on a towel. The pelvis is
  *  then anchored at the given point (just in front of the backrest hinge) instead of centring the body. */
 float Recline=0;
 /** Treading water (03/11, PENDENCIAS "nadar no mar e na piscina"): the UAL Swim_Idle retargeted to the MetaHuman, the
  *  root 32 cm under the water surface (Surface z: water at the shoulders), riding the sea waves when bSea (SeaHeight replicates the ocean material's
  *  vertex offset) and turning the head side to side slowly. */
 void TreadWater(const FVector& Surface,bool bInSea);
 /** Work poses with a tool in both hands, the hands following it by IK (HandGoal/ElbowGoal, read by the service
  *  anim): "Skim" (pool attendant) a pool skimmer net (tools/ue58/gen_pool_skimmer.py) swept across the water in a
  *  slow arc; "Sweep" (housekeeper) the Poly Haven plastic broom brushing the floor in short strokes. */
 UPROPERTY() TObjectPtr<UStaticMeshComponent> Tool;
 bool bHandGoals=false;FVector HandGoal[2],ElbowGoal[2];   // [0] right hand, [1] left hand (world)
 void UpdateTool(float DeltaSeconds);
 bool bTreading=false,bSeaSwim=false;FVector SwimAt=FVector::ZeroVector;
 /** Vertical offset of the sea surface at a point (cm) at world time Seconds, as M_Ocean's world position offset
  *  (mare_materials.build_water); Storm 0..1 is MPC_MareTime.Storm. */
 static float SeaHeight(const FVector2D& P,float Seconds,float Storm);
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
 float SeenCheck=0;
 bool bCastsShadow=true;
 /** Hidden and not animating because the camera is beyond mare.PeopleDrawDistance (see SetDistanceHidden). */
 bool bHiddenByDistance=false;
 float OutOfView=0;
 void SetDistanceHidden(bool bHide);
 /** Restart the hair strands simulation (groom): after a jump in position the strands would trail metres behind. */
 void ResetHair();
 /** Hair strands physics on/off (groom SetEnableSimulation): off while riding something fast (the water slide), where
  *  the simulated strands stayed metres behind and the head looked bald. */
 void SetHairSimulation(bool bOn);
 /** Riding a water slide lying back, feet first (07/11, Sergio: legs went through the chute with the chair pose): the
  *  lying pose with the torso raised Recline degrees, head pointing HeadYaw, the pelvis placed on PelvisAt every frame. */
 void RideReclined(const FVector& PelvisAt,float HeadYaw,float InRecline);
 /** Moved by a world system (pool swimmers, slide riders): called at the start of this person's own tick, before the
  *  pose and the hair are updated, so they all render at the same place (moved later in the frame, the hair strands
  *  trailed one frame behind: 70 cm down the slide at 3 fps). */
 TFunction<void(float)> PreTick;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta")
 FVector Destination=FVector::ZeroVector;
 static class UStaticMesh* ProductMesh(const FString& Dish,bool bUsed=false);
 static TSharedPtr<class FJsonObject> AssetCatalog();
private:
 FString Playing;
 FTransform ReferenceBoneTransform(FName Bone)const;
 FVector LieCentre=FVector::ZeroVector;float LieYaw=0,LieAlignIn=0;
 void UpdateLying(float DeltaSeconds);
};
