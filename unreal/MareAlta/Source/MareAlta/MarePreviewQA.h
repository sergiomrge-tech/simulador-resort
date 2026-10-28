#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Dom/JsonObject.h"
#include "MarePreviewQA.generated.h"
class AMarePerson;

/** Opt-in runtime regression, restricted to a disposable D:/CodexTemp profile. */
UCLASS()
class AMarePreviewQA : public AActor
{
 GENERATED_BODY()
public:
 AMarePreviewQA();
 virtual void Tick(float DeltaSeconds) override;
 /** Runtime fixture spawning is restricted to an explicit disposable D:/CodexTemp profile. */
 UFUNCTION(BlueprintCallable,meta=(WorldContext="WorldContextObject"),Category="QA")
 static AMarePerson* SpawnInspectionPerson(UObject* WorldContextObject,FVector Location,int32 Variant,const FString& Dish);
private:
 int32 Phase=0;
 double Next=0;
 FVector Before;
 double PausedTime=0;
 FString Root;
 float InitialMaster=.85f;
 double InitialMinutes=420;
 FString InitialWeather;
 FName InitialRadio;
 TSharedPtr<FJsonObject> ExpansionOwnership;
 double ExpansionCash=0;
 TArray<TSharedPtr<FJsonValue>> Results;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> PresentationFixtures;
 void Check(const FString& Name,bool bPass);
 void Capture(const FString& Name);
};
