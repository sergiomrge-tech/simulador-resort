#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareStaffWorld.generated.h"
class AMarePerson;

/** Hired staff seen at work (pendências seção 3, refinamento dos funcionários): the receptionist behind the pousada
 *  counter, the maid going from bungalow to bungalow, the pool attendant with the net along the pool, the tour guide
 *  at the booth and the hotel waiter between the pass and the tables. Each role walks a route of stops from
 *  Content/Data/staff_world.json and holds a work pose at each one; it is on screen while the role is working
 *  (UMareSimulation::HasStaff) inside the role's hours. The kiosk attendant (UMareKioskWorld) and the bartender
 *  (UMareBarWorld) keep their own actors. Visual only: the simulation already applies each role's effect. */
UCLASS()
class MAREALTA_API UMareStaffWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 /** What the role's worker is doing now (stop label or "a caminho"), empty when nobody is on screen. */
 FString Activity(const FString& Role) const;
 /** The role's worker on screen, or null (QA and tests). */
 AMarePerson* Worker(const FString& Role) const;
private:
 struct FStop{FVector At=FVector::ZeroVector;float Yaw=0,Seconds=4;FString Pose,Label,Carry;bool bDrop=false;};
 struct FWorker
 {
  TWeakObjectPtr<AMarePerson> Person;
  TArray<FStop> Route;
  int32 Next=0;
  float Wait=0,Stuck=0;
  bool bMoving=false,bGlide=false;
  FVector LastPos=FVector::ZeroVector;
 };
 float Clock=0;
 TMap<FString,FWorker> Workers;
 TArray<FStop> RouteFor(const FString& Role,const TSharedPtr<class FJsonObject>& Def) const;
 FVector Ground(const FVector& At) const;
 void Spawn(const FString& Role,FWorker& W);
 void Step(FWorker& W,float DeltaSeconds);
};
