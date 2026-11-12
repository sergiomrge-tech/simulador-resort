#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareToursWorld.generated.h"
class AMareServiceTarget;
class AStaticMeshActor;
class AMarePerson;

/** Tours at the pier: the ticket booth (E opens the tours page), buyers in line in front of it, passengers with a
 *  ticket waiting on the pier, who walk out to the boat (or the trail) when the tour leaves and back to the beach
 *  when it is cancelled. Places come from Content/Data/tours.json; MareTours.cpp owns the state. */
UCLASS()
class MAREALTA_API UMareToursWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 /** Over the head of each group's figure in the booth line: who they are and what they want (2.1). */
 TArray<TPair<FVector,FString>> Bubbles()const;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
private:
 float Clock=0;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Booth;
 UPROPERTY() TObjectPtr<AStaticMeshActor> BoothModel;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Fishing;
 UPROPERTY() TObjectPtr<AStaticMeshActor> FishingModel;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Buyers;
 /** Passengers with a ticket, per tour. */
 TMap<FString,TArray<TWeakObjectPtr<AMarePerson>>> Passengers;
 UPROPERTY() TMap<TObjectPtr<AMarePerson>,double> Leaving;
 AMarePerson* Spawn(const FVector& At,float Yaw,const FString& Id);
 FVector Ground(FVector At) const;
};
