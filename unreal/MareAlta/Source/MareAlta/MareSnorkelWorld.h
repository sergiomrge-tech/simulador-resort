#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareSnorkelWorld.generated.h"
class AStaticMeshActor;
class AMarePerson;
class AMareServiceTarget;
class APlayerController;
class UPrimitiveComponent;

/** Guided snorkel (CHECKLIST_EXPANSOES 2.3): the tour boat anchors off the reef and the group swims after the player.
 *  Aiming at a fish school or a coral kind and pressing E presents it to the group (each new species rates), touching
 *  coral costs rating, one swimmer drifts away and must be fetched, and back at the ladder the group is counted before
 *  the tour ends (MareSimulation::SnorkelScore + GuideTour). Values in tours.json "snorkel_tour". */
UCLASS()
class MAREALTA_API UMareSnorkelWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 bool IsActive()const;
 /** Starts the tour now (boarding hour, tickets sold); false with the reason in LastMessage. */
 bool Start(APlayerController* Controller);
 /** HUD line while snorkelling: species presented, coral touched, the lost swimmer's direction, the count. */
 FString Status()const;
 /** Swimmers' reactions over their heads. */
 TArray<TPair<FVector,FString>> Bubbles()const;
 /** E on a species target: presents it to the group. */
 void Present(int32 Species);
 /** QA: "state", "present:i", "aim:i", "lose", "fetch", "touch", "home", "group", "finish". */
 FString QA(const FString& Cmd);
private:
 UPROPERTY() TObjectPtr<AStaticMeshActor> Boat;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Swimmers;
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> Targets;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Masks;
 /** Coral components of each species (empty for fish), and all of them for the touch check. */
 TArray<TArray<TWeakObjectPtr<UPrimitiveComponent>>> SpeciesCorals;
 TArray<TWeakObjectPtr<UPrimitiveComponent>> Corals;
 TWeakObjectPtr<APlayerController> PC;
 FString TourId;
 float Heading=0,Time=0,CoralClock=0,LostClock=0,LadderClock=0,SayClock=0;
 int32 CoralTouches=0,Seen=0,Lost=-1;
 bool bLostDone=false,bCrewFetched=false,bSecondStop=false,bMasked=false;
 FVector LostAt=FVector::ZeroVector;
 TArray<bool> Presented;
 TArray<FVector> SwimPos;
 TMap<int32,TPair<FString,float>> Says;
 float QAHold=0,Frozen=0;FVector QAHoldAt=FVector::ZeroVector;
 TSharedPtr<FJsonObject> Defs()const;
 FString Line(const FString& Key)const;
 FVector Forward()const;
 void UpdateBoat();
 void UpdateTargets();
 void UpdateSwimmers(float Dt);
 void UpdateCoral(float Dt);
 void UpdateLostAndCount(float Dt);
 void BeginLost();
 void Found(bool bCrew);
 void Finish();
 void PutOnMasks();
 void Say(int32 Swimmer,const FString& Text,float Seconds=4);
 bool Candidates(int32 Species,TArray<FVector>& Out)const;
 bool DeepEnough(const FVector& P)const;
};
