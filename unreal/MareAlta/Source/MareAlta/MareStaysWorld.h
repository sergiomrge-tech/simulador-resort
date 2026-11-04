#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareStaysWorld.generated.h"
class AMareServiceTarget;
class AStaticMeshActor;
class AMarePerson;
class UMareSimulation;
class FJsonObject;

/** Where a place's reception line forms and where its guests go (customization.json operations.pousada /
 *  hotel_stays: "reception" [x,y,z,yaw] in cm/degrees, optional "exit" [x,y,z] and "elevators" [[x,y,z],...]). */
struct FMareStayLine
{
 FString Place;
 /** Counter point the line faces, and the direction the line grows (out of the counter). */
 FVector Desk=FVector::ZeroVector,Front=FVector::ForwardVector;
 /** Where guests who leave without a room (or check out) walk to before disappearing. */
 FVector Exit=FVector::ZeroVector;
 /** Hotel: elevator doors where checked-in guests go up (and check-outs come down). Empty for the pousada. */
 TArray<FVector> Elevators;
 /** Spot of the I-th guest in line (one metre apart, first 1.1 m from the counter), at the counter height. */
 FVector Spot(int32 Index) const{return Desk+Front*(110+Index*100);}
};

/** The pousada and the Grand Hotel in the world (gameplay plan M2/M3): reception desk target, guests waiting in line
 *  at each reception (pousada counter, hotel lobby), and the mess of dirty bungalows (crumpled towels, tied trash bag,
 *  unmade bed) as E targets that clean the room in the simulation. Hotel guests who check in walk to the elevators,
 *  check-outs come down from them and leave through the main door. The simulation (MareStays.cpp) owns the state;
 *  this only mirrors it every half second. */
UCLASS()
class MAREALTA_API UMareStaysWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 /** E on a mess target: DataIndex is the room, Label carries the task id after "task:". */
 void UseTask(int32 Room,const FString& Task);
 /** World location of a bungalow-local point (cm), for QA and placement. */
 bool RoomPoint(int32 Room,const FVector& Local,FVector& Out) const;
 int32 TaskTargetCount() const{return Tasks.Num();}
 /** Reception line of a place from the data; false when the place has no "reception" entry. */
 static bool LineFor(const UMareSimulation* Simulation,const FString& Place,FMareStayLine& Out);
 /** Guests of Place waiting at its reception, in queue order (old saves without "place" are pousada guests). */
 static TArray<TSharedPtr<FJsonObject>> QueueOf(UMareSimulation* Simulation,const FString& Place);
 /** People currently standing in Place's line (QA). */
 int32 LineCount(const FString& Place) const;
 /** The guest of queue entry Id shows a mood on the face (AMarePerson::Express): a deal closed, a counter-offer. */
 void GuestExpress(const FString& Id,const FString& Mood,float Seconds=4.f);
private:
 void FindBungalows();
 void SyncTasks();
 /** Mirrors Place's queue as people in line; bOpen false (place locked) removes them at once. */
 void SyncGuests(const FMareStayLine& Line,bool bOpen);
 /** Morning check-outs of Place come down the elevators and walk out of the main door, one every few seconds. */
 void SyncDepartures(const FMareStayLine& Line);
 /** Floor under a point (traced from just above it, below the lobby ceiling), or the point itself. */
 FVector Ground(const FVector& At,const AActor* Ignore=nullptr) const;
 AMarePerson* SpawnGuest(const FString& Place,const FString& Id,const FString& Name,const FVector& Floor,const FRotator& Facing);
 void Walk(AMarePerson* Person,const FVector& Goal,float Timeout);
 float Clock=0.f;
 double NextDeparture=0;
 UPROPERTY() TArray<TObjectPtr<AActor>> Bungalows;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Desk;
 UPROPERTY() TObjectPtr<AStaticMeshActor> DeskModel;
 /** Key "room:task" -> target and its visible mess. */
 UPROPERTY() TMap<FString,TObjectPtr<AMareServiceTarget>> Tasks;
 UPROPERTY() TMap<FString,TObjectPtr<AStaticMeshActor>> Mess;
 /** Guest id -> person standing in a reception line (ids are unique across places), and the place of each. */
 UPROPERTY() TMap<FString,TObjectPtr<AMarePerson>> Guests;
 TMap<FString,FString> GuestPlace;
 /** Guests walking away from the desk, with the time they are removed even if the path fails. */
 UPROPERTY() TMap<TObjectPtr<AMarePerson>,double> Leaving;
};
