#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareBarWorld.generated.h"
class AMareServiceTarget;
class AMarePerson;

/** Bar do Coqueiro in the world (gameplay plan M8): the E target inside the counter that opens the bar station,
 *  one guest per open order sitting on a stool facing the counter, and the bartender behind it once hired.
 *  Served guests leave with their drink in hand; impatient ones just leave. Positions come from Content/Data/bar.json;
 *  the simulation (MareBar.cpp) owns the orders, this only mirrors them every half second. */
UCLASS()
class MAREALTA_API UMareBarWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 /** Stool index of an order's guest, or INDEX_NONE (the station page lists orders in stool order). */
 int32 StoolOf(const FString& Order) const{const int32* S=Stools.Find(Order);return S?*S:INDEX_NONE;}
private:
 float Clock=0;
 int32 LastServed=-1;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Station;
 UPROPERTY() TObjectPtr<AMarePerson> Barman;
 UPROPERTY() TMap<FString,TObjectPtr<AMarePerson>> Guests;
 TMap<FString,int32> Stools;
 /** Guests walking away with the time they are removed. */
 UPROPERTY() TMap<TObjectPtr<AMarePerson>,double> Leaving;
 AMarePerson* Seat(const FString& Order,const FString& Name,int32 Stool);
};
