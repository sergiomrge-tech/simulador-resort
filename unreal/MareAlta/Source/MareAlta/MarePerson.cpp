#include "MarePerson.h"
#include "MareServiceTarget.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MareKioskWorld.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "NavigationSystem.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TSharedPtr<FJsonObject> AMarePerson::AssetCatalog()
{
 FString Text;TSharedPtr<FJsonObject> Result;
 FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/actors.json")));
 FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);return Result.IsValid()?Result:MakeShared<FJsonObject>();
}
UStaticMesh* AMarePerson::ProductMesh(const FString& Dish,bool bUsed)
{
 auto Entry=UMareSimulation::Object(AssetCatalog(),(bUsed?TEXT("Used_"):TEXT("Dish_"))+Dish);
 const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;
 if(!Entry->TryGetArrayField(TEXT("static_meshes"),Paths) || Paths->IsEmpty())return nullptr;
 return LoadObject<UStaticMesh>(nullptr,*(*Paths)[0]->AsString());
}
AMarePerson::AMarePerson()
{
 PrimaryActorTick.bCanEverTick=true;GetCapsuleComponent()->InitCapsuleSize(28,88);
 GetMesh()->SetRelativeLocation(FVector(0,0,-88));GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
 GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 GetCharacterMovement()->MaxWalkSpeed=125;GetCharacterMovement()->bOrientRotationToMovement=true;
 GetCharacterMovement()->RotationRate=FRotator(0,180,0);GetCharacterMovement()->MaxStepHeight=32;
 AIControllerClass=AAIController::StaticClass();AutoPossessAI=EAutoPossessAI::PlacedInWorldOrSpawned;
 bUseControllerRotationYaw=false;
}
FTransform AMarePerson::ReferenceBoneTransform(FName Bone)const
{
 auto MeshAsset=GetMesh()->GetSkeletalMeshAsset();if(!MeshAsset)return FTransform::Identity;
 const auto& Ref=MeshAsset->GetRefSkeleton();int32 Index=Ref.FindBoneIndex(Bone);FTransform Result=FTransform::Identity;
 while(Index!=INDEX_NONE){Result=Result*Ref.GetRefBonePose()[Index];Index=Ref.GetParentIndex(Index);}return Result;
}
bool AMarePerson::SetAppearance(int32 AppearanceVariant)
{
 const FString Key=FString::Printf(TEXT("Human_%d"),AppearanceVariant%4);auto Row=UMareSimulation::Object(AssetCatalog(),Key);
 const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;if(!Row->TryGetArrayField(TEXT("skeletal_meshes"),Paths) || Paths->IsEmpty())return false;
 auto MeshAsset=LoadObject<USkeletalMesh>(nullptr,*(*Paths)[0]->AsString());if(!MeshAsset)return false;
 GetMesh()->SetSkeletalMeshAsset(MeshAsset);GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
 for(const FString& Name:{TEXT("Idle"),TEXT("Idle_Talking"),TEXT("Walk"),TEXT("Sitting_Idle"),TEXT("Interact")}){
  const FString Path=UMareSimulation::String(UMareSimulation::Object(Row,TEXT("animations")),Key+Name);
  if(auto Clip=LoadObject<UAnimSequence>(nullptr,*Path))Clips.Add(Name,Clip);
 }
 if(Row->TryGetArrayField(TEXT("static_meshes"),Paths))for(const auto& Path:*Paths){auto Part=LoadObject<UStaticMesh>(nullptr,*Path->AsString());if(!Part)continue;
  const FName Bone=Part->GetName().StartsWith(TEXT("Camera_"))?TEXT("neck_01"):TEXT("Head");
  auto Hair=NewObject<UStaticMeshComponent>(this);AddInstanceComponent(Hair);Hair->SetStaticMesh(Part);Hair->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Hair->AttachToComponent(GetMesh(),FAttachmentTransformRules::KeepRelativeTransform,Bone);Hair->SetRelativeTransform(ReferenceBoneTransform(Bone).Inverse());Hair->RegisterComponent();HairMeshes.Add(Hair);
 }
 PlayPose(TEXT("Idle"));return true;
}
void AMarePerson::PlayPose(const FString& Name,bool bLoop)
{
 if(Playing==Name || !Clips.Contains(Name))return;Playing=Name;GetMesh()->PlayAnimation(Clips[Name],bLoop);
}
bool AMarePerson::WalkTo(const FVector& Goal)
{
 Destination=Goal;
 if(auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld())){
  FNavLocation Projected;
  if(!Nav->ProjectPointToNavigation(Goal,Projected,FVector(80,80,150)))return false;
  Destination=Projected.Location;
 }
 GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
 GetCharacterMovement()->SetMovementMode(MOVE_Walking);SpawnDefaultController();
 auto AI=Cast<AAIController>(GetController());if(!AI)return false;
 // Stop-on-overlap adds the capsule radius to acceptance, leaving customers
 // outside the arrival threshold even after a successful path completion.
 const auto Result=AI->MoveToLocation(Destination,20,false,true,false,true,nullptr,false);
 if(Result==EPathFollowingRequestResult::Failed)return false;
 PlayPose(TEXT("Walk"));return true;
}
bool AMarePerson::AtGoal()const{return FVector::DistSquared2D(GetActorLocation(),Destination)<FMath::Square(35.f);}
void AMarePerson::HoldProduct(const FString& Dish)
{
 auto MeshAsset=ProductMesh(Dish);if(!MeshAsset)return;
 const FName Hand=CarriedMeshes.Num()%2==0?TEXT("hand_r"):TEXT("hand_l");
 if(!GetMesh()->DoesSocketExist(Hand))return;
 auto Product=NewObject<UStaticMeshComponent>(this);AddInstanceComponent(Product);Product->SetStaticMesh(MeshAsset);
 Product->SetCollisionEnabled(ECollisionEnabled::NoCollision);Product->AttachToComponent(GetMesh(),FAttachmentTransformRules::SnapToTargetNotIncludingScale,Hand);
 Product->SetRelativeLocation(FVector(3,0,-2));Product->SetRelativeRotation(FRotator(0,0,90));Product->RegisterComponent();CarriedMeshes.Add(Product);
}
void AMarePerson::ClearProducts(){for(auto Part:CarriedMeshes)if(Part)Part->DestroyComponent();CarriedMeshes.Empty();}
void AMarePerson::Interact(APlayerController* Player)
{
 if(auto Kiosk=GetWorld()->GetSubsystem<UMareKioskWorld>())Kiosk->Serve(this,false);
}
void AMarePerson::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);Elapsed+=DeltaSeconds;
 if(GetVelocity().SizeSquared2D()>25)PlayPose(TEXT("Walk"));else if(Stage!=EMarePersonStage::Eating)PlayPose(TEXT("Idle"));
}
