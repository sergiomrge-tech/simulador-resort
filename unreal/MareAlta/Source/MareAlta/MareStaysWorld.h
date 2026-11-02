#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareStaysWorld.generated.h"
class AMareServiceTarget;
class AStaticMeshActor;
class AMarePerson;

/** The pousada in the world (gameplay plan M2/M3): reception desk target, guests waiting in line, and the
 *  mess of dirty bungalows (crumpled towels, tied trash bag, unmade bed) as E targets that clean the room in
 *  the simulation. The simulation (MareStays.cpp) owns the state; this only mirrors it every half second. */
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
private:
 void FindBungalows();
 void SyncTasks();
 void SyncGuests();
 float Clock=0.f;
 UPROPERTY() TArray<TObjectPtr<AActor>> Bungalows;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Desk;
 UPROPERTY() TObjectPtr<AStaticMeshActor> DeskModel;
 /** Key "room:task" -> target and its visible mess. */
 UPROPERTY() TMap<FString,TObjectPtr<AMareServiceTarget>> Tasks;
 UPROPERTY() TMap<FString,TObjectPtr<AStaticMeshActor>> Mess;
 /** Guest id -> person standing in the reception line. */
 UPROPERTY() TMap<FString,TObjectPtr<AMarePerson>> Guests;
 /** Guests walking away from the desk, with the time they are removed even if the path fails. */
 UPROPERTY() TMap<TObjectPtr<AMarePerson>,double> Leaving;
};
