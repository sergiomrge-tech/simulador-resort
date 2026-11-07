#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MareGraphicsQA.generated.h"
/** Opt-in fixed-view render profiling, restricted to a disposable profile. */
UCLASS()
class AMareGraphicsQA : public AActor
{
 GENERATED_BODY()
public:
 AMareGraphicsQA();
 virtual void Tick(float DeltaSeconds) override;
private:
 FString Root;
 bool bHotelScene=false;
 int32 VariantCount=4;
 int32 RenderPercentage=80;
 int32 Variant=0;
 int32 Stage=0;
 double Next=0;
 TSharedFuture<FString> Capture;
 TArray<TSharedPtr<class FJsonValue>> Records;
 void Configure();
};
