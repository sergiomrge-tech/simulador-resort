#include "MareServiceAnimation.h"
#include "MarePerson.h"
#include "Animation/AnimSingleNodeInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "TwoBoneIK.h"
#include "BonePose.h"

namespace MareServiceAnimation
{
bool IsVessel(UStaticMeshComponent* Part)
{
 return Part->ComponentHasTag(TEXT("MareVessel"));
}
struct FServiceProxy : FAnimSingleNodeInstanceProxy
{
 explicit FServiceProxy(UAnimInstance* Instance):FAnimSingleNodeInstanceProxy(Instance){}
 FVector Targets[2],Elbows[2];float Strength[2]={0,0};
 TWeakObjectPtr<UAnimationAsset> PreviousAsset;
 TArray<FTransform> LastLocals,BlendFrom;
 float BlendTime=.2f;bool bNewClip=false;
 virtual void PreUpdate(UAnimInstance* Instance,float DeltaSeconds) override
 {
  FAnimSingleNodeInstanceProxy::PreUpdate(Instance,DeltaSeconds);
  auto Single=Cast<UAnimSingleNodeInstance>(Instance);
  if(Single && Single->GetCurrentAsset()!=PreviousAsset.Get()){PreviousAsset=Single->GetCurrentAsset();BlendTime=0;bNewClip=true;}
  BlendTime+=DeltaSeconds;
  auto Person=Cast<AMarePerson>(Instance->GetOwningActor());if(!Person)return;
  auto Mesh=Person->GetMesh();const auto ToComponent=Mesh->GetComponentTransform().Inverse();
  for(int32 Hand=0;Hand<2;++Hand){
   const FName Socket=Hand==0?TEXT("hand_r"):TEXT("hand_l");
   const bool bHolding=Person->CarriedMeshes.ContainsByPredicate([&](auto Part){return IsValid(Part) && Part->GetAttachSocketName()==Socket;});
   Strength[Hand]=FMath::FInterpTo(Strength[Hand],bHolding?1.f:0.f,DeltaSeconds,10.f);
   const float Side=Hand==0?1.f:-1.f;
   FVector Grip=Person->GetActorLocation()+Person->GetActorForwardVector()*32+Person->GetActorRightVector()*Side*18+FVector(0,0,22);
   if(bHolding && Hand==0){
    const bool bDrink=Person->CarriedMeshes.ContainsByPredicate([&](auto Part){return IsValid(Part) && Part->GetAttachSocketName()==Socket && IsVessel(Part);});
    if(bDrink){const FVector Mouth=Mesh->GetSocketLocation(TEXT("Head"))+Person->GetActorForwardVector()*12-FVector(0,0,23);
     Grip=FMath::Lerp(Grip,Mouth,Person->DrinkGesture());}
   }
   Targets[Hand]=ToComponent.TransformPosition(Grip);
   Elbows[Hand]=ToComponent.TransformPosition(Person->GetActorLocation()+Person->GetActorRightVector()*Side*42+Person->GetActorForwardVector()*5+FVector(0,0,3));
  }
 }
 virtual bool Evaluate(FPoseContext& Output) override
 {
  const bool bEvaluated=FAnimSingleNodeInstanceProxy::Evaluate(Output);
  if(!bEvaluated)return false;
  const int32 Count=Output.Pose.GetNumBones();
  if(bNewClip){BlendFrom=LastLocals;bNewClip=false;}
  if(BlendFrom.Num()==Count && BlendTime<.2f){
   float Alpha=FMath::Clamp(BlendTime/.2f,0.f,1.f);Alpha=Alpha*Alpha*(3-2*Alpha);
   for(int32 I=0;I<Count;++I){auto& Local=Output.Pose[FCompactPoseBoneIndex(I)];const auto Target=Local;Local.Blend(BlendFrom[I],Target,Alpha);}
  }
  LastLocals.SetNumUninitialized(Count);for(int32 I=0;I<Count;++I)LastLocals[I]=Output.Pose[FCompactPoseBoneIndex(I)];
  if(Strength[0]<.001f && Strength[1]<.001f)return true;
  FCSPose<FCompactPose> Pose;Pose.InitPose(Output.Pose);const auto& Bones=Output.Pose.GetBoneContainer();
  for(int32 Hand=0;Hand<2;++Hand){if(Strength[Hand]<.001f)continue;
   const FName Names[3]={Hand==0?TEXT("upperarm_r"):TEXT("upperarm_l"),Hand==0?TEXT("lowerarm_r"):TEXT("lowerarm_l"),Hand==0?TEXT("hand_r"):TEXT("hand_l")};
   FCompactPoseBoneIndex Indices[3];bool bValid=true;
   for(int32 I=0;I<3;++I){Indices[I]=Bones.GetCompactPoseIndexFromSkeletonIndex(Bones.GetReferenceSkeleton().FindBoneIndex(Names[I]));bValid&=Indices[I]!=INDEX_NONE;}
   if(!bValid)continue;
   FTransform Upper=Pose.GetComponentSpaceTransform(Indices[0]),Lower=Pose.GetComponentSpaceTransform(Indices[1]),End=Pose.GetComponentSpaceTransform(Indices[2]);
   FTransform Original[3]={Upper,Lower,End};
   AnimationCore::SolveTwoBoneIK(Upper,Lower,End,Elbows[Hand],Targets[Hand],false,1.,1.);
   FTransform Solved[3]={Upper,Lower,End};
   for(int32 I=0;I<3;++I){FTransform Blended;Blended.Blend(Original[I],Solved[I],Strength[Hand]);Blended.NormalizeRotation();Pose.SetComponentSpaceTransform(Indices[I],Blended);}
  }
  FCSPose<FCompactPose>::ConvertComponentPosesToLocalPosesSafe(Pose,Output.Pose);return true;
 }
};
}
FAnimInstanceProxy* UMareServiceAnimInstance::CreateAnimInstanceProxy(){return MakeUnique<MareServiceAnimation::FServiceProxy>(this).Release();}
UMareCarryPresentation::UMareCarryPresentation(){PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickGroup=TG_PostPhysics;}
void UMareCarryPresentation::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
 Super::TickComponent(DeltaTime,TickType,ThisTickFunction);auto Person=Cast<AMarePerson>(GetOwner());if(!Person)return;
 for(auto Part:Person->CarriedMeshes){if(!IsValid(Part) || !Part->GetStaticMesh())continue;
  const auto Bounds=Part->GetStaticMesh()->GetBounds();const bool bVessel=MareServiceAnimation::IsVessel(Part);
  const float Side=Part->GetAttachSocketName()==TEXT("hand_r")?1.f:-1.f;
  const float Tilt=bVessel && Side>0?Person->DrinkGesture()*18.f:0.f;
  const FRotator Upright(Tilt,Person->GetActorRotation().Yaw,0);
  const FVector Grip(Bounds.Origin.X,bVessel?Side*Bounds.BoxExtent.Y*.65f:0.f,bVessel?Bounds.Origin.Z*.75f:Bounds.Origin.Z-Bounds.BoxExtent.Z);
  const FVector Hand=Person->GetMesh()->GetSocketLocation(Part->GetAttachSocketName());
  Part->SetWorldLocationAndRotation(Hand-Upright.RotateVector(Grip),Upright);
 }
}
