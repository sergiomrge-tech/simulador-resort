#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MareIntro.generated.h"
class AStaticMeshActor;
class ACameraActor;
class AMareServiceTarget;

/** Arrival is enabled only for a genuinely new save; existing profiles are never relocated. */
UCLASS()
class MAREALTA_API AMareIntro : public AActor
{
 GENERATED_BODY()
public:
 AMareIntro();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 void FinishArrival();
 void ReadLetter();
 void CloseLetter();
 bool IsArrival() const { return bArrival; }
 bool IsLetterOpen() const { return LetterWidget.IsValid(); }
private:
 UPROPERTY() TObjectPtr<AStaticMeshActor> Bus;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TObjectPtr<AMareServiceTarget> LetterTarget;
 UPROPERTY() TObjectPtr<AActor> LetterPaper;
 TSharedPtr<SWidget> LetterWidget;
 bool bArrival=false;
 bool bDisembarking=false;
 float DisembarkTime=0;
 bool bBusDeparting=false;
 float DepartureTime=0;
 float ArrivalTime=0;
};
