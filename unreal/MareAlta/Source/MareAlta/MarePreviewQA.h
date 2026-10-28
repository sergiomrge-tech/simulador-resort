#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Dom/JsonObject.h"
#include "MarePreviewQA.generated.h"

/** Opt-in runtime regression, restricted to a disposable D:/CodexTemp profile. */
UCLASS()
class AMarePreviewQA : public AActor
{
 GENERATED_BODY()
public:
 AMarePreviewQA();
 virtual void Tick(float DeltaSeconds) override;
private:
 int32 Phase=0;
 double Next=0;
 FVector Before;
 double PausedTime=0;
 FString Root;
 float InitialMaster=.85f;
 double InitialMinutes=420;
 FString InitialWeather;
 TArray<TSharedPtr<FJsonValue>> Results;
 void Check(const FString& Name,bool bPass);
 void Capture(const FString& Name);
};
