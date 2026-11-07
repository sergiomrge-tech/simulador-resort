#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareBoatTourWorld.generated.h"
class AStaticMeshActor;
class AMarePerson;
class AMareServiceTarget;
class APlayerController;

/** Playable boat tour (CHECKLIST_EXPANSOES 2.2): the player pilots the tour boat with the passengers seated aboard
 *  through the buoys of tours.json "boat_tour" to three stops, each an action (vests on every passenger, dolphins
 *  watched with the engine off, the story of the deserted beach), and back to the pier, where it is rated like a
 *  guided tour (MareSimulation::GuideTourScored). Waves rock the boat; full speed makes passengers seasick. */
UCLASS()
class MAREALTA_API UMareBoatTourWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 bool IsActive()const;
 /** Starts the tour now (the tour must be boarding with tickets sold); false with the reason in LastMessage. */
 bool Start(APlayerController* Controller);
 /** HUD line while touring: controls, next buoy or the stop's instruction, speed. */
 FString Status()const;
 /** Passenger reactions over their heads (cheers, seasick, thanks). */
 TArray<TPair<FVector,FString>> Bubbles()const;
 /** E on a passenger: puts the vest on (vests stop). */
 void GiveVest(int32 Seat);
 /** E on the deserted beach: tells its story (story stop). */
 void TellStory();
 /** QA: "drive:throttle,steer,seconds" overrides the controls; "goto:i" places the boat at route point i; "state". */
 FString QA(const FString& Cmd);
private:
 UPROPERTY() TObjectPtr<AStaticMeshActor> Boat;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Passengers;
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> VestTargets;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Vests;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Buoys;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Dolphins;
 UPROPERTY() TObjectPtr<AMareServiceTarget> StoryTarget;
 TWeakObjectPtr<APlayerController> PC;
 FString TourId;
 float Heading=0,Speed=0,Throttle=0,Time=0,RoughTime=0,DolphinWatch=0,DolphinTime=0,ShallowTimer=0;
 int32 Next=0,StopIndex=-1,Sick=0;
 bool bStopActive=false,bDolphinsHere=false,bDolphinBad=false,bStory=false,bCheered=false;
 double Bonus=0;
 TArray<int32> Choices;
 TArray<bool> Vested;
 /** Each passenger's place in the boat's frame, taken once they settled on the bench and reapplied every frame. */
 TArray<FTransform> SeatRel;
 TMap<int32,TPair<FString,float>> Says;
 float QAThrottle=0,QASteer=0,QATime=0;
 TSharedPtr<FJsonObject> Defs()const;
 FVector RoutePoint(int32 I)const;
 FString StopKind(int32 Stop)const;
 void UpdateBoat(float Dt);
 void UpdateRoute(float Dt);
 void BeginStop(int32 Stop);
 void EndStop(int32 Choice);
 void Finish();
 void Say(int32 Seat,const FString& Line,float Seconds=4);
 FVector Forward()const;
};
