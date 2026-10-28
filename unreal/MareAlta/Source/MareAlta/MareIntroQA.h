#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Dom/JsonObject.h"
#include "MareIntroQA.generated.h"
/** Opt-in test only for a disposable D:/CodexTemp save. */
UCLASS()
class AMareIntroQA : public AActor
{
 GENERATED_BODY()
public:
 AMareIntroQA();
 virtual void Tick(float DeltaSeconds) override;
private:
 int32 Phase=0;double Next=0;FString Root;
 TArray<TSharedPtr<FJsonValue>> Checks;
 void Check(const FString& Name,bool Passed);
};
