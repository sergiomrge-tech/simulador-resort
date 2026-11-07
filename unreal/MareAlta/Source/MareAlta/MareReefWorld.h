#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareReefWorld.generated.h"
class UInstancedStaticMeshComponent;

struct FMareReefFish
{
 TWeakObjectPtr<UInstancedStaticMeshComponent> Body;
 TWeakObjectPtr<UInstancedStaticMeshComponent> Tail;
 int32 Index=0;
 FTransform BodyTransform;
 FTransform TailTransform;
 FVector TailOffset=FVector::ZeroVector;
 float Seed=0;
};

struct FMareShark
{
 FVector Centre=FVector::ZeroVector;
 float Radius=900,Shy=0,Depth=-650,Angle=0,Dir=1,Seed=0;
};

/** Restores the original paired reef fish to safe depths and gentle motion, and dresses the seafloor around the
 *  offshore reef (Content/Data/reef.json, 05/11): rocks, kelp, seagrass, sponges, anemones, urchins, starfish and
 *  shells as one HISM per mesh (GPU), and blacktip reef sharks circling their clusters. */
UCLASS()
class MAREALTA_API UMareReefWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 int32 FishCount() const{return Fish.Num();}
 bool AllFishUnderwater() const;
 FVector SamplePosition() const;
 /** Where the fish of one species (its body mesh name, e.g. World_0544) swim now (guided snorkel). */
 TArray<FVector> FishPositions(const FString& BodyMesh) const;
 /** Where the instances of a seafloor mesh (e.g. Sea_anemone, Sea_shark) are now (guided snorkel species). */
 TArray<FVector> InstancePositions(const FString& MeshName) const;
 int32 SeafloorCount() const;
 int32 SharkCount() const{return Sharks.Num();}
 /** Sea floor height (cm) offshore of the modelled beach, from reef.json floor_fill.profile (the sand planes of
  *  mare_water.ensure_seabed follow the same profile). */
 static float SeabedZ(float Y,float* Slope=nullptr);
 int32 FloorFillCount() const{return FloorFilled;}
 /** QA: "state" (instances per mesh), "sharks", "hold:x,y,z,pitch,yaw,seconds" (keeps the player there), "watch:i". */
 FString QA(const FString& Cmd);
private:
 void IndexFish();
 void Dress();
 void FillFloor(FRandomStream& R,const FBox2D& Reef);
 int32 FloorFilled=0;
 void UpdateSharks(float Dt,const FVector& Swimmer);
 bool bIndexed=false;
 float Clock=0;
 TArray<FMareReefFish> Fish;
 UPROPERTY() TObjectPtr<AActor> Dressing;
 UPROPERTY() TArray<TObjectPtr<UInstancedStaticMeshComponent>> Parts;
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> SharkMesh;
 TArray<FMareShark> Sharks;
 float SharkTime=0,HoldTime=0;
 int32 Watch=-1;
 FVector HoldAt=FVector::ZeroVector;
 FRotator HoldView=FRotator::ZeroRotator;
};
