#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MareIntro.generated.h"
class AStaticMeshActor;
class ACameraActor;
class AMareServiceTarget;
class UStaticMeshComponent;
class UAudioComponent;
class AMarePerson;

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
 bool HasRefinedBus()const{return BusDoor!=nullptr && BusWheels.Num()==4;}
 float DoorFraction()const{return DoorOpen;}
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
 UPROPERTY() TObjectPtr<UStaticMeshComponent> BusDoor;
 UPROPERTY() TObjectPtr<UAudioComponent> BusSound;
 UPROPERTY() TObjectPtr<AMarePerson> BusDriver;
 UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> BusWheels;
 FVector StopPosition=FVector(5355,3000,12);
 FVector StartPosition=FVector(6755,3000,12);
 FVector InteriorCamera,FrontLook;
 TArray<FVector> ExitSteps;
 float DoorOpen=0,DoorYaw=-85,WheelAngle=0,StepClock=0;
 bool LoadBus();
 FVector BusPoint(const FVector& Local)const;
 void AnimateBus(float Distance);
 void AdvanceArrival(float Dt);
};
