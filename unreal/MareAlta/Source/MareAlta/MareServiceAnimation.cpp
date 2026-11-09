#include "MareServiceAnimation.h"
#include "MarePerson.h"
#include "MareGame.h"
#include "MarePlayerPresentation.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Animation/AnimSingleNodeInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "TwoBoneIK.h"
#include "HAL/IConsoleManager.h"
#include "BonePose.h"
#include "AnimNodes/AnimNode_CopyPoseFromMesh.h"

// Sunbather on a towel, raised knee (degrees about the body's side axis; tuned by eye on the beach, 07/11).
static TAutoConsoleVariable<float> CVarLieThigh(TEXT("mare.LieThigh"),50.f,TEXT("Lying on a towel: thigh flexion of the raised knee (degrees)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarLieCalf(TEXT("mare.LieCalf"),-100.f,TEXT("Lying on a towel: shin fold of the raised knee (degrees)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarLieFoot(TEXT("mare.LieFoot"),50.f,TEXT("Lying on a towel: foot correction so the sole rests flat (degrees)."));   // i18n:skip
namespace MareServiceAnimation
{
bool IsVessel(UStaticMeshComponent* Part)
{
 return Part->ComponentHasTag(TEXT("MareVessel"));
}
// 08/11 (Sergio: "as pessoas na vila andam um pouco curvadas como idosos"): the walk clip bends the upper back and
// the neck forward (measured with mare_title_probe.posture: chest->head 25-30 deg forward walking, ~0 standing).
// While walking the upper back and the neck straighten by these degrees (blended in and out with the clip): 14/14 left
// walkers at ~7 deg overall lean (chest->head 12, neck->head 5, standing 12), measured and checked side-on (08/11).
static TAutoConsoleVariable<float> CVarMareWalkChest(TEXT("mare.WalkUprightChest"),14.f,TEXT("Degrees the upper back (spine_04) straightens while walking."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareWalkNeck(TEXT("mare.WalkUprightNeck"),14.f,TEXT("Degrees the neck (neck_01 + neck_02, split 60/40) straightens while walking."));   // i18n:skip
struct FServiceProxy : FAnimSingleNodeInstanceProxy
{
 explicit FServiceProxy(UAnimInstance* Instance):FAnimSingleNodeInstanceProxy(Instance){}
 FVector Targets[2],Elbows[2];float Strength[2]={0,0};
 TWeakObjectPtr<UAnimationAsset> PreviousAsset;
 TArray<FTransform> LastLocals,BlendFrom;
 float BlendTime=.2f;bool bNewClip=false;
 bool bOpenSwimmingHands=false;
 float Recline=0;
 float Upright=0;   // 0..1 while the walk clip plays
 /** Face up on a towel (not a lounger): which knee is raised, 0 none, 1 right, 2 left (07/11, Sergio: "deitado todo duro"). */
 bool bTowel=false,bProne=false;int32 LieKnee=0;
 virtual void PreUpdate(UAnimInstance* Instance,float DeltaSeconds) override
 {
  FAnimSingleNodeInstanceProxy::PreUpdate(Instance,DeltaSeconds);
  if(auto Owner=Cast<AMarePerson>(Instance->GetOwningActor())){Recline=Owner->bLying?Owner->Recline:0.f;
   bTowel=Owner->bLying && Owner->Recline<=0;bProne=bTowel && Owner->bProne;LieKnee=int32(FCrc::StrCrc32(*Owner->SaveId)%3u);}
  auto Single=Cast<UAnimSingleNodeInstance>(Instance);
  if(Single && Single->GetCurrentAsset()!=PreviousAsset.Get()){PreviousAsset=Single->GetCurrentAsset();BlendTime=0;bNewClip=true;}
  BlendTime+=DeltaSeconds;
  {const UAnimationAsset* Clip=Single?Single->GetCurrentAsset():nullptr;const bool bWalk=Clip && Clip->GetName()==TEXT("MH_Walk");   // i18n:skip
   Upright=FMath::FInterpTo(Upright,bWalk?1.f:0.f,DeltaSeconds,6.f);}
  auto Person=Cast<AMarePerson>(Instance->GetOwningActor());
  if(!Person){if(auto Hero=Cast<AMareCharacter>(Instance->GetOwningActor()))if(auto Presentation=Hero->FindComponentByClass<UMarePlayerPresentation>()){
   bOpenSwimmingHands=Hero->GetCharacterMovement()->IsSwimming() && Instance->GetSkelMeshComponent()==Presentation->ViewBody;
   const auto Inverse=Instance->GetSkelMeshComponent()->GetComponentTransform().Inverse();
   for(int32 Hand=0;Hand<2;++Hand){FVector Target=FVector::ZeroVector,Elbow=FVector::ZeroVector;float Weight=0;Presentation->HandTarget(Hand,Target,Elbow,Weight);
    Strength[Hand]=FMath::FInterpTo(Strength[Hand],Weight,DeltaSeconds,12.f);Targets[Hand]=Inverse.TransformPosition(Target);Elbows[Hand]=Inverse.TransformPosition(Elbow);}
  }return;}
  auto Mesh=Person->GetMesh();const auto ToComponent=Mesh->GetComponentTransform().Inverse();
  if(Person->bHandGoals){   // a tool held in both hands (pool skimmer): the hands follow it
   for(int32 Hand=0;Hand<2;++Hand){Strength[Hand]=FMath::FInterpTo(Strength[Hand],1.f,DeltaSeconds,6.f);
    Targets[Hand]=ToComponent.TransformPosition(Person->HandGoal[Hand]);Elbows[Hand]=ToComponent.TransformPosition(Person->ElbowGoal[Hand]);}
   return;}
  for(int32 Hand=0;Hand<2;++Hand){
   const FName Socket=Hand==0?TEXT("hand_r"):TEXT("hand_l");
   const bool bHolding=Person->CarriedMeshes.ContainsByPredicate([&](auto Part){return IsValid(Part) && Part->GetAttachSocketName()==Socket;});
   const bool bSelfie=Hand==0 && IsValid(Person->SelfiePhone);
   // Seated at a table with this hand free: forearm and hand rest on the top, a little past the near edge.
   const bool bRest=!bHolding && !bSelfie && Person->bTableAhead && !Person->SeatPelvis.IsZero();
   Strength[Hand]=FMath::FInterpTo(Strength[Hand],bHolding || bSelfie?1.f:bRest?.95f:0.f,DeltaSeconds,bSelfie || bRest?5.f:10.f);
   if(bRest){const float S=Hand==0?1.f:-1.f;const FVector F=Person->GetActorForwardVector(),R=Person->GetActorRightVector();
    const FVector Base(Person->SeatPelvis.X,Person->SeatPelvis.Y,Person->TableTopZ);
    Targets[Hand]=ToComponent.TransformPosition(Base+F*(Person->TableEdge+14)+R*S*17+FVector(0,0,3));
    Elbows[Hand]=ToComponent.TransformPosition(Base+F*(Person->TableEdge-6)+R*S*36+FVector(0,0,-2));
    continue;}
   const float Side=Hand==0?1.f:-1.f;
   FVector Grip=Person->GetActorLocation()+Person->GetActorForwardVector()*32+Person->GetActorRightVector()*Side*18+FVector(0,0,22);
   // 09/11 (C13): face down the hands stay folded under the chest as the pose has them (no IK into the towel).
   if(bProne && !bHolding && !bSelfie){Strength[Hand]=FMath::FInterpTo(Strength[Hand],0.f,DeltaSeconds,4.f);continue;}
   // 09/11 (C13): a reader's hands hold the open paperback by its covers (about 11 cm each side of the spine).
   if(bTowel && !bProne && !bHolding && !bSelfie && Person->ReadingBook){
    const FVector Sky=Person->GetActorForwardVector(),Head=Person->GetActorUpVector(),Out=Person->GetActorRightVector()*(Hand==0?1.f:-1.f);
    const FTransform B=Person->ReadingBook->GetComponentTransform();
    const FVector Pelvis=Mesh->GetSocketLocation(TEXT("pelvis"));
    Strength[Hand]=FMath::FInterpTo(Strength[Hand],1.f,DeltaSeconds,4.f);
    Targets[Hand]=ToComponent.TransformPosition(B.GetLocation()+Out*11.f-B.GetRotation().GetUpVector()*1.5f);
    Elbows[Hand]=ToComponent.TransformPosition(Pelvis+Head*36.f+Out*28.f+Sky*6.f);
    continue;}
   if(bTowel && !bHolding && !bSelfie){
    // Lying on the back: the free hand rests on the belly, the elbow out to the side on the towel. The actor's X axis
    // points at the sky and its Z axis runs from the feet to the head (AMarePerson::LieOn).
    const FVector Sky=Person->GetActorForwardVector(),Head=Person->GetActorUpVector(),Out=Person->GetActorRightVector()*(Hand==0?1.f:-1.f);
    const FVector Pelvis=Mesh->GetSocketLocation(TEXT("pelvis"));
    Strength[Hand]=FMath::FInterpTo(Strength[Hand],1.f,DeltaSeconds,4.f);
    Targets[Hand]=ToComponent.TransformPosition(Pelvis+Head*(Hand==0?24.f:16.f)+Sky*15+Out*7);
    Elbows[Hand]=ToComponent.TransformPosition(Pelvis+Head*30+Out*34-Sky*4);
    continue;}
   if(bSelfie){   // arm half stretched, the phone a little above the eyes and to the right
    Grip=Mesh->GetSocketLocation(TEXT("Head"))+Person->GetActorForwardVector()*40+Person->GetActorRightVector()*16+FVector(0,0,6);
    Targets[Hand]=ToComponent.TransformPosition(Grip);
    Elbows[Hand]=ToComponent.TransformPosition(Person->GetActorLocation()+Person->GetActorRightVector()*45+Person->GetActorForwardVector()*15+FVector(0,0,30));
    continue;}
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
  if(Upright>.01f){
   // Walking upright: the bends about the body's side axis (component X), each in its parent's frame (as the lounger).
   const auto& Bones=Output.Pose.GetBoneContainer();const auto& Ref=Bones.GetReferenceSkeleton();
   FCSPose<FCompactPose> Pose;Pose.InitPose(Output.Pose);
   const TPair<const TCHAR*,float> Fix[]={{TEXT("spine_04"),CVarMareWalkChest.GetValueOnAnyThread()},{TEXT("neck_01"),CVarMareWalkNeck.GetValueOnAnyThread()*.6f},{TEXT("neck_02"),CVarMareWalkNeck.GetValueOnAnyThread()*.4f}};   // i18n:skip
   for(const auto& F:Fix){const FCompactPoseBoneIndex Bone=Bones.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(F.Key));if(Bone==INDEX_NONE)continue;
    const FCompactPoseBoneIndex Parent=Bones.GetParentBoneIndex(Bone);if(Parent==INDEX_NONE)continue;
    const FQuat P=Pose.GetComponentSpaceTransform(Parent).GetRotation();const FQuat Bend(FVector(1,0,0),FMath::DegreesToRadians(F.Value*Upright));
    auto& Local=Output.Pose[Bone];Local.SetRotation((P.Inverse()*Bend*P*Local.GetRotation()).GetNormalized());}
  }
  if(Recline>0){
   // Lounger: bend the torso up at the waist (spine_01 flexes forward about the body's side axis, component X), the
   // rotation expressed in the pelvis frame so everything above follows.
   const auto& Bones=Output.Pose.GetBoneContainer();const auto& Ref=Bones.GetReferenceSkeleton();
   const FCompactPoseBoneIndex Spine=Bones.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(TEXT("spine_01")));
   const FCompactPoseBoneIndex Pelvis=Bones.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(TEXT("pelvis")));
   if(Spine!=INDEX_NONE && Pelvis!=INDEX_NONE){FCSPose<FCompactPose> Pose;Pose.InitPose(Output.Pose);
    const FQuat Parent=Pose.GetComponentSpaceTransform(Pelvis).GetRotation();
    const FQuat Bend(FVector(1,0,0),FMath::DegreesToRadians(-Recline));
    auto& Local=Output.Pose[Spine];Local.SetRotation((Parent.Inverse()*Bend*Parent*Local.GetRotation()).GetNormalized());}
  }
  if(bTowel && LieKnee>0 && !bProne){   // face down a knee 'to the sky' would go into the sand
   // One knee up, the sole flat on the towel: the thigh flexes toward the sky (component +Y is the face side, X the
   // body's side axis) and the shin folds back twice as much. Both bends are about the same axis, so each is expressed
   // in its parent's original frame.
   const auto& Bones=Output.Pose.GetBoneContainer();const auto& Ref=Bones.GetReferenceSkeleton();
   const TCHAR* Side=LieKnee==1?TEXT("_r"):TEXT("_l");
   const FCompactPoseBoneIndex Thigh=Bones.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(FName(FString(TEXT("thigh"))+Side)));   // i18n:skip
   const FCompactPoseBoneIndex Calf=Bones.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(FName(FString(TEXT("calf"))+Side)));   // i18n:skip
   const FCompactPoseBoneIndex Foot=Bones.GetCompactPoseIndexFromSkeletonIndex(Ref.FindBoneIndex(FName(FString(TEXT("foot"))+Side)));   // i18n:skip
   if(Thigh!=INDEX_NONE && Calf!=INDEX_NONE){FCSPose<FCompactPose> Pose;Pose.InitPose(Output.Pose);
    auto Bend=[&](FCompactPoseBoneIndex Bone,float Degrees){const FCompactPoseBoneIndex Parent=Bones.GetParentBoneIndex(Bone);if(Parent==INDEX_NONE)return;
     const FQuat P=Pose.GetComponentSpaceTransform(Parent).GetRotation();auto& Local=Output.Pose[Bone];
     Local.SetRotation((P.Inverse()*FQuat(FVector(1,0,0),FMath::DegreesToRadians(Degrees))*P*Local.GetRotation()).GetNormalized());};
    Bend(Thigh,CVarLieThigh.GetValueOnAnyThread());Bend(Calf,CVarLieCalf.GetValueOnAnyThread());if(Foot!=INDEX_NONE)Bend(Foot,CVarLieFoot.GetValueOnAnyThread());}
  }
  if(bOpenSwimmingHands){
   const auto& Bones=Output.Pose.GetBoneContainer();const auto& Ref=Bones.GetReferenceSkeleton();
   for(int32 I=0;I<Count;++I){const FCompactPoseBoneIndex Index(I);const int32 SkeletonIndex=Bones.GetSkeletonIndex(Index);
    if(SkeletonIndex==INDEX_NONE)continue;const FString Name=Ref.GetBoneName(SkeletonIndex).ToString();
    if(Name.StartsWith(TEXT("index_")) || Name.StartsWith(TEXT("middle_")) || Name.StartsWith(TEXT("ring_")) || Name.StartsWith(TEXT("pinky_")) || Name.StartsWith(TEXT("thumb_")))Output.Pose[Index].SetRotation(Ref.GetRefBonePose()[SkeletonIndex].GetRotation());
   }
  }
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
namespace MareServiceAnimation
{
/** The face is a component of the MetaHuman blueprint, a child actor of the person. */
AMarePerson* FaceOwner(const UAnimInstance* Instance)
{
 AActor* Actor=Instance->GetOwningActor();if(!Actor)return nullptr;
 if(auto Person=Cast<AMarePerson>(Actor))return Person;
 return Cast<AMarePerson>(Actor->GetParentActor());
}
struct FFaceProxy : FAnimInstanceProxy
{
 explicit FFaceProxy(UAnimInstance* Instance):FAnimInstanceProxy(Instance){}
 FAnimNode_CopyPoseFromMesh Copy;
 TArray<TPair<FName,float>> Curves;
 virtual void Initialize(UAnimInstance* Instance) override
 {
  FAnimInstanceProxy::Initialize(Instance);
  Copy.bUseAttachedParent=false;Copy.bCopyCurves=false;
  if(auto Person=FaceOwner(Instance))Copy.SourceMeshComponent=Person->GetMesh();
  FAnimationInitializeContext Context(this);Copy.Initialize_AnyThread(Context);
 }
 virtual void PreUpdate(UAnimInstance* Instance,float DeltaSeconds) override
 {
  FAnimInstanceProxy::PreUpdate(Instance,DeltaSeconds);
  auto Person=FaceOwner(Instance);
  if(Person && !Copy.SourceMeshComponent.IsValid())Copy.SourceMeshComponent=Person->GetMesh();
  Copy.PreUpdate(Instance);
  Curves.Reset();if(Person)Person->FaceCurves(Curves);
 }
 virtual void CacheBones() override
 {
  FAnimInstanceProxy::CacheBones();
  FAnimationCacheBonesContext Context(this);Copy.CacheBones_AnyThread(Context);
 }
 virtual void UpdateAnimationNode(const FAnimationUpdateContext& Context) override{Copy.Update_AnyThread(Context);}
 virtual bool Evaluate(FPoseContext& Output) override
 {
  Copy.Evaluate_AnyThread(Output);
  for(const auto& Curve:Curves)Output.Curve.Set(Curve.Key,Curve.Value);
  return true;
 }
};
}
FAnimInstanceProxy* UMareFaceAnimInstance::CreateAnimInstanceProxy(){return MakeUnique<MareServiceAnimation::FFaceProxy>(this).Release();}
FAnimInstanceProxy* UMareServiceAnimInstance::CreateAnimInstanceProxy(){return MakeUnique<MareServiceAnimation::FServiceProxy>(this).Release();}
UMareCarryPresentation::UMareCarryPresentation(){PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickGroup=TG_PostPhysics;}
void UMareCarryPresentation::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
 Super::TickComponent(DeltaTime,TickType,ThisTickFunction);auto Person=Cast<AMarePerson>(GetOwner());if(!Person)return;
 if(UStaticMeshComponent* Phone=Person->SelfiePhone){   // the model's screen normal is its Y axis, its long side Z
  const FVector Hand=Person->GetMesh()->GetSocketLocation(TEXT("hand_r")),Head=Person->GetMesh()->GetSocketLocation(TEXT("Head"));
  const FVector ToFace=(Head-Hand).GetSafeNormal();const FRotator Facing=FRotationMatrix::MakeFromYZ(ToFace,FVector::UpVector).Rotator();
  const FVector Centre=Phone->GetStaticMesh()?Phone->GetStaticMesh()->GetBounds().Origin:FVector::ZeroVector;
  Phone->SetWorldLocationAndRotation(Hand+ToFace*4.f-Facing.RotateVector(Centre),Facing);}
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
