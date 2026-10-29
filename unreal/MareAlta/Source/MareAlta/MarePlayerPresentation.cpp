#include "MarePlayerPresentation.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareServiceAnimation.h"
#include "MareHomeWorld.h"
#include "Animation/AnimSequence.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"

UMarePlayerPresentation::UMarePlayerPresentation()
{
 PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickGroup=TG_PostPhysics;
}
void UMarePlayerPresentation::BeginPlay()
{
 Super::BeginPlay();auto Hero=Cast<AMareCharacter>(GetOwner());if(!Hero)return;
 auto Row=UMareSimulation::Object(AMarePerson::AssetCatalog(),TEXT("Human_0"));
 const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;
 if(!Row->TryGetArrayField(TEXT("skeletal_meshes"),Paths) || Paths->IsEmpty())return;
 auto Asset=LoadObject<USkeletalMesh>(nullptr,*(*Paths)[0]->AsString());if(!Asset)return;
 auto Body=Hero->GetMesh();Body->SetSkeletalMeshAsset(Asset);
 Body->SetRelativeLocationAndRotation(FVector(0,0,-88),FRotator(0,-90,0));
 Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);Body->SetOwnerNoSee(true);Body->SetCastHiddenShadow(true);
 Body->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 Body->SetAnimInstanceClass(UMareServiceAnimInstance::StaticClass());
 ViewBody=NewObject<USkeletalMeshComponent>(Hero,TEXT("FirstPersonBody"));Hero->AddInstanceComponent(ViewBody);
 ViewBody->SetupAttachment(Hero->GetRootComponent());ViewBody->SetSkeletalMeshAsset(Asset);
 ViewBody->SetRelativeTransform(Body->GetRelativeTransform());ViewBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 ViewBody->SetOnlyOwnerSee(true);ViewBody->SetCastShadow(false);
 ViewBody->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 ViewBody->RegisterComponent();ViewBody->SetAnimInstanceClass(UMareServiceAnimInstance::StaticClass());
 ViewBody->HideBoneByName(TEXT("Head"),EPhysBodyOp::PBO_None);ViewBody->HideBoneByName(TEXT("neck_01"),EPhysBodyOp::PBO_None);
 for(const FString Name:{TEXT("Idle"),TEXT("Walk"),TEXT("Interact"),TEXT("Swim_Idle"),TEXT("Sitting_Idle")}){
  const FString Path=UMareSimulation::String(UMareSimulation::Object(Row,TEXT("animations")),TEXT("Human_0")+Name);
  if(auto Clip=LoadObject<UAnimSequence>(nullptr,*Path))Clips.Add(Name,Clip);
 }
 BuildHair(Row);AddTickPrerequisiteComponent(ViewBody);AddTickPrerequisiteComponent(Body);UpdateAnimation();
}
void UMarePlayerPresentation::BuildHair(const TSharedPtr<FJsonObject>& Row)
{
 auto Hero=Cast<AMareCharacter>(GetOwner());const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;
 if(!Hero || !Row->TryGetArrayField(TEXT("static_meshes"),Paths))return;
 const auto& Ref=Hero->GetMesh()->GetSkeletalMeshAsset()->GetRefSkeleton();
 for(const auto& Path:*Paths)if(auto Asset=LoadObject<UStaticMesh>(nullptr,*Path->AsString())){
  const FName Bone=Asset->GetName().StartsWith(TEXT("Camera_"))?TEXT("neck_01"):TEXT("Head");
  int32 Index=Ref.FindBoneIndex(Bone);FTransform Reference=FTransform::Identity;
  while(Index!=INDEX_NONE){Reference=Reference*Ref.GetRefBonePose()[Index];Index=Ref.GetParentIndex(Index);}
  auto Hair=NewObject<UStaticMeshComponent>(Hero);Hero->AddInstanceComponent(Hair);
  Hair->SetStaticMesh(Asset);Hair->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Hair->AttachToComponent(Hero->GetMesh(),FAttachmentTransformRules::KeepRelativeTransform,Bone);
  Hair->SetRelativeTransform(Reference.Inverse());Hair->SetOwnerNoSee(true);Hair->SetCastHiddenShadow(true);Hair->RegisterComponent();
 }
}
void UMarePlayerPresentation::ReachFor(const FVector& Position){ReachPosition=Position;ReachRemaining=.65f;}
bool UMarePlayerPresentation::HandTarget(int32 Hand,FVector& Target,FVector& Elbow,float& Weight)const
{
 auto Hero=Cast<AMareCharacter>(GetOwner());if(!Hero)return false;
 auto Eyes=Hero->FindComponentByClass<UCameraComponent>();if(!Eyes)return false;
 const bool bCarrying=!HeldDish.IsEmpty();const bool bReaching=ReachRemaining>0 && Hand==0;
 const bool bSupport=bCarrying && HeldProduct && HeldProduct->GetStaticMesh()->GetBounds().BoxExtent.Size2D()>23;
 Weight=(Hand==0 && bCarrying) || (Hand==1 && bSupport)?1.f:0.f;
 const float Side=Hand==0?1.f:-1.f;
 const FVector Forward=Hero->GetActorForwardVector(),Right=Hero->GetActorRightVector();
 Target=Eyes->GetComponentLocation()+Forward*43+Right*Side*17-FVector(0,0,28);
 Elbow=Hero->GetActorLocation()+Right*Side*40+Forward*6+FVector(0,0,20);
 if(Hero->GetCharacterMovement()->IsSwimming() && !bCarrying){
  const float Phase=GetWorld()->GetTimeSeconds()*(Hero->GetVelocity().Size2D()>30?2.3f:1.4f);
  Target=Eyes->GetComponentLocation()+Forward*(40+12*FMath::Cos(Phase))+Right*Side*(24+13*FMath::Sin(Phase))-FVector(0,0,23+8*FMath::Sin(Phase));
  Elbow=Eyes->GetComponentLocation()+Right*Side*44+Forward*8-FVector(0,0,18);Weight=1.f;
 }
 if(bReaching){const float Alpha=FMath::Sin(FMath::Clamp(1-ReachRemaining/.65f,0.f,1.f)*PI);
  const FVector Delta=ReachPosition-Eyes->GetComponentLocation();
  const FVector Reach=Eyes->GetComponentLocation()+Delta.GetClampedToMaxSize(65);
  Target=FMath::Lerp(Target,Reach,Alpha);Weight=FMath::Max(Weight,Alpha);}
 return Weight>0;
}
void UMarePlayerPresentation::UpdateAnimation()
{
 auto Hero=Cast<AMareCharacter>(GetOwner());if(!Hero || !ViewBody)return;
 const bool bSwimming=Hero->GetCharacterMovement()->IsSwimming();
 const bool bSeated=GetWorld()->GetSubsystem<UMareHomeWorld>()->IsSeated();
 const FString Clip=bSeated?TEXT("Sitting_Idle"):bSwimming?TEXT("Swim_Idle"):ReachRemaining>0?TEXT("Interact"):Hero->GetVelocity().SizeSquared2D()>25?TEXT("Walk"):TEXT("Idle");
 if(Playing!=Clip && Clips.Contains(Clip)){
  Playing=Clip;for(auto Body:{Hero->GetMesh(),ViewBody.Get()})if(auto Instance=Cast<UMareServiceAnimInstance>(Body->GetAnimInstance())){
   Instance->SetAnimationAsset(Clips[Clip],Clip!=TEXT("Interact"));Instance->SetPlaying(true);}
 }
 for(auto Body:{Hero->GetMesh(),ViewBody.Get()})if(auto Instance=Cast<UMareServiceAnimInstance>(Body->GetAnimInstance()))Instance->SetPlayRate(bSwimming?1.25f:Clip==TEXT("Walk")?FMath::Clamp(Hero->GetVelocity().Size2D()/160.f,.65f,2.6f):1.f);
 // Changing the single-node animation can reinitialize bone visibility.
 ViewBody->HideBoneByName(TEXT("neck_01"),EPhysBodyOp::PBO_None);
 ViewBody->HideBoneByName(TEXT("Head"),EPhysBodyOp::PBO_None);
 const FVector Position=bSwimming?FVector(-10,0,62):FVector(0,0,-88);
 const FRotator Rotation=bSwimming?FRotator(0,90,-85):FRotator(0,-90,0);
 Hero->GetMesh()->SetRelativeLocationAndRotation(Position,Rotation);ViewBody->SetRelativeLocationAndRotation(Position,Rotation);
}
void UMarePlayerPresentation::UpdateCarry()
{
 auto Hero=Cast<AMareCharacter>(GetOwner());if(!Hero || !ViewBody)return;
 auto Sim=Hero->GetGameInstance()->GetSubsystem<UMareSimulation>();const FString Dish=Sim?Sim->Carry():TEXT("");
 if(Dish!=HeldDish){if(HeldProduct){HeldProduct->DestroyComponent();HeldProduct=nullptr;}HeldDish=Dish;
  if(!Dish.IsEmpty())if(auto Asset=AMarePerson::ProductMesh(Dish)){
   HeldProduct=NewObject<UStaticMeshComponent>(Hero);Hero->AddInstanceComponent(HeldProduct);
   HeldProduct->SetStaticMesh(Asset);HeldProduct->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   HeldProduct->AttachToComponent(ViewBody,FAttachmentTransformRules::SnapToTargetNotIncludingScale,TEXT("hand_r"));
   HeldProduct->SetUsingAbsoluteRotation(true);HeldProduct->SetUsingAbsoluteScale(true);HeldProduct->RegisterComponent();
  }
 }
 if(HeldProduct && HeldProduct->GetStaticMesh()){
  const auto B=HeldProduct->GetStaticMesh()->GetBounds();const FRotator Rotation(0,Hero->GetActorRotation().Yaw,0);
  const bool Vessel=HeldDish==TEXT("suco") || HeldDish==TEXT("coco_gelado") || HeldDish==TEXT("caipirinha") || HeldDish==TEXT("batida");
  const FVector Grip(B.Origin.X,Vessel?B.BoxExtent.Y*.65f:0,Vessel?B.Origin.Z*.75f:B.Origin.Z-B.BoxExtent.Z);
  HeldProduct->SetWorldLocationAndRotation(ViewBody->GetSocketLocation(TEXT("hand_r"))-Rotation.RotateVector(Grip),Rotation);
 }
}
void UMarePlayerPresentation::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Function)
{
 Super::TickComponent(Dt,Type,Function);ReachRemaining=FMath::Max(0.f,ReachRemaining-Dt);UpdateAnimation();UpdateCarry();
}
