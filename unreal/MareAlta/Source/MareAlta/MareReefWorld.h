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

/** Restores the original paired reef fish to safe depths and gentle motion. */
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
private:
 void IndexFish();
 bool bIndexed=false;
 float Clock=0;
 TArray<FMareReefFish> Fish;
};
