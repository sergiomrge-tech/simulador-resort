#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareBarWorld.generated.h"
class AMareServiceTarget;
class AMarePerson;
class AStaticMeshActor;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;

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
 /** Guests seated before their stool had collision (right after buying the bar): placed again once the trace finds it. */
 TSet<FString> Untraced;
 bool StoolTop(int32 Stool,FVector& Top,float& Yaw,AActor* Ignore)const;
 /** Guests walking away with the time they are removed. */
 UPROPERTY() TMap<TObjectPtr<AMarePerson>,double> Leaving;
 AMarePerson* Seat(const FString& Order,const FString& Name,int32 Stool);
 // ---- Physical prep (CHECKLIST_EXPANSOES 1.1): the prep bench against the back panel with the ingredients and
 // tools (bar.json "bench"/"shelf"), one E target per ingredient, and the work glass whose layers show its contents.
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> PrepProps;
 UPROPERTY() TMap<FString,TObjectPtr<AMareServiceTarget>> Shelf;
 UPROPERTY() TObjectPtr<AMareServiceTarget> GlassTarget;
 UPROPERTY() TObjectPtr<AStaticMeshActor> GlassActor;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> LayerIce;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> LayerFruit;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> LayerLiquid;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> LayerFoam;
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> LiquidTint;
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> FruitTint;
 FString GlassShown;
 /** The ingredient just put in drops from above the glass into it (then disappears). */
 UPROPERTY() TObjectPtr<AStaticMeshActor> Falling;
 float FallTime=-1;
 FVector FallFrom=FVector::ZeroVector;
 int32 GlassCount=0;
 void BuildPrep(const TSharedPtr<FJsonObject>& Defs);
 void UpdatePrep(class UMareSimulation* S,bool bOwned,float DeltaSeconds);
public:
 /** Over each seated guest's head: where the bubble goes and what they ask for (MareSimulation::BarBubble). */
 TArray<TPair<FVector,FString>> Bubbles()const;
 /** QA: world position of a shelf item's E target, or of the glass ("glass"); false when not built. */
 bool PrepSpot(const FString& Id,FVector& At)const;
};
