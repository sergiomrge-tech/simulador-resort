#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareHotelEventsWorld.generated.h"
class AStaticMeshActor;
class AMareServiceTarget;
class AMarePerson;
class UMaterialInterface;

/** The Grand Hotel event on the beach (CHECKLIST 5.2, MareHotelEvents.cpp): on the event day the plan shows as ghost
 *  pieces on the event area (hotel_events.json area); E on a ghost sets the real piece (PlaceHotelEventPiece). When the
 *  event starts the guests arrive and sit on the chairs that were set; when it ends everything is cleared. */
UCLASS()
class MAREALTA_API UMareHotelEventsWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 /** A ghost was used (DataIndex: piece i, or 1000 + i for the extras). */
 void Place(int32 DataIndex);
 /** QA: "state", "placeall", "place:i". */
 FString QA(const FString& Cmd);
 int32 GuestCount() const{return Guests.Num();}
private:
 struct FPiece{TObjectPtr<AStaticMeshActor> Actor=nullptr;TObjectPtr<AMareServiceTarget> Target=nullptr;bool bExtra=false;int32 Index=0;bool bShown=false;FString Model;};
 void Clear();
 void Build(const TSharedPtr<class FJsonObject>& Booked);
 void Refresh(const TSharedPtr<class FJsonObject>& Booked);
 void SeatGuests(const TSharedPtr<class FJsonObject>& Booked);
 FVector Ground(const FVector& At) const;
 TArray<FPiece> Pieces;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Actors;
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> Targets;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Guests;
 UPROPERTY() TObjectPtr<UMaterialInterface> Ghost;
 FString BuiltFor;
 float Clock=0;
};
