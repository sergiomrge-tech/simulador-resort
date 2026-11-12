#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareRestaurantWorld.generated.h"
class AMareServiceTarget;
class AMarePerson;

/** Grand Hotel restaurant in the world: an E target on every table with diners (take the order / serve), the kitchen
 *  pass (pick up what is ready, opens the restaurant page) and the room-service point by the lifts. Tables that have
 *  no decorative diner get a seated guest while they have an order. Places come from Content/Data/restaurant.json. */
UCLASS()
class MAREALTA_API UMareRestaurantWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
private:
 float Clock=0;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Pass;
 UPROPERTY() TObjectPtr<AMareServiceTarget> RoomService;
 /** Guest-room doors of 302 and 303 (C16): room service is handed over there, the guest opens. */
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> RoomDoors;
 UPROPERTY() TMap<int32,TObjectPtr<AMareServiceTarget>> Tables;
 UPROPERTY() TMap<int32,TObjectPtr<AMarePerson>> Diners;
};
