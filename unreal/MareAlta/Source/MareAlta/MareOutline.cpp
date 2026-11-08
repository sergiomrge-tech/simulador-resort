// Outline of the focused interaction target (see MareOutline.h).
#include "MareOutline.h"
#include "MareServiceTarget.h"
#include "Engine/PostProcessVolume.h"
#include "EngineUtils.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/MeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/OverlapResult.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"

namespace
{
 TWeakObjectPtr<AMareServiceTarget> GLast;
 TArray<TWeakObjectPtr<UPrimitiveComponent>> GLit;
 const TCHAR* OutlinePath=TEXT("/Game/World/Materials/M_PP_Outline.M_PP_Outline");   // i18n:skip

 // The hero camera keeps its own post-process at weight 0 (exposure lives in the level's volumes), so the outline goes
 // into the level's unbound post-process volume, once per world.
 TWeakObjectPtr<UWorld> GWorldWithOutline;
 void EnsureBlendable(APlayerController* Controller)
 {
  UWorld* World=Controller?Controller->GetWorld():nullptr;if(!World || GWorldWithOutline.Get()==World)return;
  GWorldWithOutline=World;
  if(!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(FString(OutlinePath))))return;
  UMaterialInterface* Mat=LoadObject<UMaterialInterface>(nullptr,OutlinePath);if(!Mat)return;
  for(TActorIterator<APostProcessVolume> It(World);It;++It)if(It->bUnbound && It->bEnabled){It->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f,Mat));return;}
 }
 // A mesh worth outlining: visible, not a whole building or a floor, not a batch of many instances (the outline would
 // run around every chair of the batch).
 bool Suitable(UPrimitiveComponent* C,const APawn* Player,const FVector& Focus)
 {
  if(!C || !C->IsVisible() || !C->IsA<UMeshComponent>() || C->GetOwner()==Player)return false;
  // A batch of instances lights up as a whole: fine when the other copies are far away (the three Gothic beds of the
  // map, one per room), not when they stand next to it (a row of chairs).
  if(auto Ism=Cast<UInstancedStaticMeshComponent>(C))if(Ism->GetInstanceCount()>1){
   const float Size=Ism->GetStaticMesh()?Ism->GetStaticMesh()->GetBounds().SphereRadius:100.f;if(Size>260.f)return false;
   int32 Near=0;for(int32 I=0;I<Ism->GetInstanceCount();++I){FTransform T;Ism->GetInstanceTransform(I,T,true);if(FVector::Dist(T.GetLocation(),Focus)<1500.f)++Near;}
   return Near<=1;}
  return C->Bounds.SphereRadius<260.f;
 }
 void AddActorMeshes(AActor* Actor,TArray<UPrimitiveComponent*>& Out,const APawn* Player)
 {
  TArray<UMeshComponent*> Meshes;Actor->GetComponents<UMeshComponent>(Meshes);
  for(UMeshComponent* M:Meshes)if(M->IsVisible() && (M->IsA<USkeletalMeshComponent>() || M->IsA<UStaticMeshComponent>()) && M->GetOwner()!=Player)Out.AddUnique(M);
 }
 void Pick(const APawn* Player,const FVector& Eye,AMareServiceTarget* Target,TArray<UPrimitiveComponent*>& Out)
 {
  UWorld* World=Target->GetWorld();
  if(Target->Action==TEXT("Door") && Target->DoorMesh && Target->DoorMesh->GetStaticMesh()){Out.Add(Target->DoorMesh);return;}   // i18n:skip
  // A target owned by a person (a customer, a guest): the person.
  if(AActor* Owner=Target->GetOwner())if(Owner->IsA<ACharacter>()){AddActorMeshes(Owner,Out,Player);return;}
  const FVector Focus=Target->GetActorTransform().TransformPosition(Target->FocusOffset);
  FCollisionQueryParams Params(TEXT("MareOutline"),true);Params.AddIgnoredActor(Player);Params.AddIgnoredActor(Target);   // i18n:skip
  auto Take=[&](UPrimitiveComponent* C){
   if(!C)return;AActor* Owner=C->GetOwner();
   if(Owner && Owner->IsA<ACharacter>() && Owner!=Player){AddActorMeshes(Owner,Out,Player);return;}
   if(Suitable(C,Player,Focus))Out.AddUnique(C);};
  FHitResult Hit;
  if(World->LineTraceSingleByChannel(Hit,Eye,Focus+(Focus-Eye).GetSafeNormal()*40.f,ECC_Visibility,Params) && FVector::Dist(Hit.ImpactPoint,Focus)<FMath::Max(Target->OcclusionTolerance,80.f))Take(Hit.GetComponent());
  TArray<FOverlapResult> Near;
  World->OverlapMultiByChannel(Near,Focus,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(28.f),Params);
  for(const FOverlapResult& R:Near)Take(R.GetComponent());
  if(Out.Num())return;
  // 08/11 (Sergio: "tudo que for clicável precisa ter essa borda"): decorations without collision are missed by the
  // trace and the overlap; take the smallest mesh whose box holds the focus point.
  UPrimitiveComponent* Best=nullptr;float BestSize=FLT_MAX;
  for(TActorIterator<AActor> It(World);It;++It){if(*It==Player || *It==Target)continue;
   if(FVector::DistSquared(It->GetActorLocation(),Focus)>FMath::Square(4000.f) && !It->GetRootComponent())continue;
   TArray<UMeshComponent*> Meshes;It->GetComponents<UMeshComponent>(Meshes);
   for(UMeshComponent* M:Meshes){if(!Suitable(M,Player,Focus))continue;FBox Box=M->Bounds.GetBox().ExpandBy(12.f);
    // an instance batch: the box of the copy nearest the focus
    if(auto Ism=Cast<UInstancedStaticMeshComponent>(M))if(Ism->GetInstanceCount()>1 && Ism->GetStaticMesh()){float BestD=FLT_MAX;
     for(int32 I=0;I<Ism->GetInstanceCount();++I){FTransform T;Ism->GetInstanceTransform(I,T,true);const float D=FVector::Dist(T.GetLocation(),Focus);if(D<BestD){BestD=D;Box=Ism->GetStaticMesh()->GetBoundingBox().TransformBy(T).ExpandBy(12.f);}}}
    if(!Box.IsInside(Focus))continue;const float Size=M->Bounds.SphereRadius;if(Size<BestSize){BestSize=Size;Best=M;}}}
  if(Best)Out.Add(Best);
 }
}

namespace MareOutline
{
 int32 Count(){int32 N=0;for(const auto& W:GLit)if(W.IsValid())++N;return N;}
 void Update(APlayerController* Controller,AMareServiceTarget* Target)
 {
  if(!Controller)return;
  EnsureBlendable(Controller);
  if(GLast.Get()==Target && (Target==nullptr || Count()>0))return;
  for(const auto& W:GLit)if(UPrimitiveComponent* C=W.Get())C->SetRenderCustomDepth(false);
  GLit.Reset();GLast=Target;
  if(!Target)return;
  FVector Eye;FRotator View;Controller->GetPlayerViewPoint(Eye,View);
  TArray<UPrimitiveComponent*> Picked;Pick(Controller->GetPawn(),Eye,Target,Picked);
  for(UPrimitiveComponent* C:Picked){C->SetRenderCustomDepth(true);GLit.Add(C);}
 }
}

#include "HAL/IConsoleManager.h"
static FAutoConsoleCommandWithWorldAndArgs MareOutlineQA(TEXT("mare.OutlineQA"),TEXT("QA: logs the outlined target and its meshes."),   // i18n:skip
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&,UWorld*){
  FString Names;for(const auto& W:GLit)if(W.IsValid())Names+=W->GetOwner()->GetName()+TEXT("/")+W->GetName()+TEXT(" ");   // i18n:skip
  UE_LOG(LogTemp,Display,TEXT("MARE_OUTLINE target=%s meshes=%d %s"),GLast.IsValid()?*GLast->Label:TEXT("none"),MareOutline::Count(),*Names);}));   // i18n:skip

static FAutoConsoleCommandWithWorldAndArgs MareOutlineAudit(TEXT("mare.OutlineAudit"),TEXT("QA: every visible interaction target and how many meshes its outline would take."),   // i18n:skip
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&,UWorld* World){
  if(!World)return;APawn* Player=World->GetFirstPlayerController()?World->GetFirstPlayerController()->GetPawn():nullptr;
  int32 Total=0,Empty=0;FString Missing;
  for(TActorIterator<AMareServiceTarget> It(World);It;++It){AMareServiceTarget* T=*It;if(T->IsHidden() || (T->GetOwner() && T->GetOwner()->IsHidden()))continue;++Total;
   const FVector Focus=T->GetActorTransform().TransformPosition(T->FocusOffset);
   TArray<UPrimitiveComponent*> Out;Pick(Player,Focus+FVector(-120,0,40),T,Out);
   if(Out.IsEmpty()){++Empty;Missing+=FString::Printf(TEXT("%s[%s @%.0f,%.0f,%.0f] "),*T->Label,*T->Action.ToString(),Focus.X,Focus.Y,Focus.Z);}}   // i18n:skip
  UE_LOG(LogTemp,Display,TEXT("MARE_OUTLINE_AUDIT targets=%d without_mesh=%d %s"),Total,Empty,*Missing);}));   // i18n:skip
