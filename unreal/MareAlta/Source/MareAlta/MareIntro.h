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
class FJsonObject;

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
 /** QA: the arrival boat and its boatman are there; how far the boat has settled at the pier (0..1). */
 bool HasArrivalBoat()const{return Boat!=nullptr && Boatman!=nullptr;}
 float DockFraction()const{return Docked;}
private:
 UPROPERTY() TObjectPtr<AStaticMeshActor> Boat;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TObjectPtr<AMareServiceTarget> LetterTarget;
 UPROPERTY() TObjectPtr<AActor> LetterPaper;
 UPROPERTY() TObjectPtr<UAudioComponent> BoatSound;
 UPROPERTY() TObjectPtr<AMarePerson> Boatman;
 TSharedPtr<SWidget> LetterWidget;
 TSharedPtr<FJsonObject> BoatDefs;
 bool bArrival=false;
 bool bDisembarking=false;
 bool bBoatLeaving=false;
 float DisembarkTime=0,ArrivalTime=0,LeaveTime=0,LeaveSpeed=0,StepClock=0,Docked=0,Heading=90;
 FVector LeavePos=FVector::ZeroVector;
 // The pier (x of its centre line; the end and deck height are measured on load) and the run in from the sea.
 float PierX=7200,PierEndY=0,PierZ=30;
 FVector Dock=FVector::ZeroVector,PathA=FVector::ZeroVector,PathB=FVector::ZeroVector;
 float BoatLength=820.f,SailSeconds=16.f,DisembarkSeconds=5.f;
 bool LoadBoat();
 FVector BoatPoint(const FVector& Local)const;
 void SailTo(float Travel);
 void RideWaves(const FVector& At2D,float NewHeading);
 void RemoveBoat();
 void AdvanceArrival(float Dt);
 static FVector Vec3(const TSharedPtr<FJsonObject>& O,const FString& Key,const FVector& Fallback);
};
