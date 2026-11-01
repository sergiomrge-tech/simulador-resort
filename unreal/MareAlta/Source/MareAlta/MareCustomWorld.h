#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareCustomWorld.generated.h"
class UInstancedStaticMeshComponent;
class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInterface;

/** Shows the selected customization tier of every object (Data/customization.json): swaps furniture
 *  meshes inside each place area, recolours materials, and previews tiers without buying them. */
UCLASS()
class MAREALTA_API UMareCustomWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 virtual void Deinitialize() override;
 /** Re-applies every saved tier (also ends a preview). */
 void ApplyAll();
 /** Shows a tier of one slot; with bPreview the save is untouched (ApplyAll restores it). */
 void Apply(const FString& Place,const FString& Slot,int32 Tier,bool bPreview=false);
 bool IsPreviewing()const{return bPreview;}
 /** QA: replacement instances currently shown for a slot, and whether its tier visual exists. */
 int32 PartInstances(const FString& Place,const FString& Slot)const;
 bool HasVisual(const FString& Place,const FString& Slot,int32 Tier)const;
 /** QA/tools: preview every slot of a place at one tier (0 = back to the saved tiers). */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void PreviewPlace(const FString& Place,int32 Tier);
private:
 struct FHidden{TWeakObjectPtr<UInstancedStaticMeshComponent> Component;int32 Index=0;FTransform Original;};
 struct FSlotState{
  TArray<FTransform> Anchors;                       // world transforms the parts are placed on
  TWeakObjectPtr<AActor> AnchorActor;               // region visibility follows this actor
  TArray<FHidden> HideTargets;                       // original instances replaced by tiers 2..5
  TArray<TWeakObjectPtr<UInstancedStaticMeshComponent>> MaterialTargets;
  TMap<TWeakObjectPtr<UInstancedStaticMeshComponent>,TArray<TObjectPtr<UMaterialInterface>>> Originals;
  TArray<TWeakObjectPtr<UHierarchicalInstancedStaticMeshComponent>> Parts;
  int32 Shown=0;
 };
 TMap<FString,FSlotState> Slots;
 UPROPERTY() TObjectPtr<AActor> Holder;
 UPROPERTY() TArray<TObjectPtr<UMaterialInterface>> KeepMaterials;
 TSharedPtr<class FJsonObject> Assets;
 bool bIndexed=false,bPreview=false;float Clock=0;
 void Index();
 class UMareSimulation* Sim()const;
 class UStaticMesh* PartMesh(const FString& Slug)const;
 static FString Key(const FString& Place,const FString& Slot){return Place+TEXT("/")+Slot;}
};
