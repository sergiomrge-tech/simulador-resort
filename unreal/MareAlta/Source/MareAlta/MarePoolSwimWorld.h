#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MarePoolSwimWorld.generated.h"
class AMarePerson;
class FJsonObject;

/** Guests enjoying the pools (Content/Data/pool_swim.json): by day they jump in from the edge, swim between points,
 *  float on the back and tread water chatting in pairs; never through the walls or each other. Life only, no
 *  management. People appear and leave out of the player's sight. QA: mare.PoolSwim [n|clear|dump]. */
UCLASS()
class MAREALTA_API UMarePoolSwimWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 static TSharedPtr<FJsonObject> Defs();
 enum class EState:uint8{Edge,Jump,Swim,Float,Chat,Climb,Ride,Fly};
 struct FSwimmer
 {
  TWeakObjectPtr<AMarePerson> Person;int32 Pool=0;EState State=EState::Edge;
  FVector Pos=FVector::ZeroVector,Target=FVector::ZeroVector,JumpFrom=FVector::ZeroVector;
  float Yaw=0,Speed=60,Timer=0,Total=1;int32 Legs=0,Partner=-1;bool bLeaving=false;
  /** Water slide: progress along the climb (cm) or the chute (0..1), and the flight velocity off its end. */
  float Along=0;FVector Vel=FVector::ZeroVector;
 };
 TArray<FSwimmer> Swimmers;
 /** QA: force this many swimmers in the nearest pool now (-1 = back to the schedule). */
 int32 Forced=-1;
 /** QA: why the last newcomer could not appear (seen, no entry, spawn failed) and the wanted count per pool. */
 FString LastSpawnFail;TArray<int32> LastWanted;
 FString Dump()const;
 void ClearAll();
private:
 float Clock=0,Spawned=0;int32 Serial=0;
 int32 Wanted(int32 Pool,const TSharedPtr<FJsonObject>& P)const;
 bool Seen(const FVector& At)const;
 bool Spawn(int32 Pool,const TSharedPtr<FJsonObject>& P);
 FVector RandomPoint(const TSharedPtr<FJsonObject>& P,const FVector& Away)const;
 /** Whether a body at At (lying along Yaw when bLong) keeps Gap cm from every other swimmer's body and the floats. */
 bool Clear(int32 Self,const FVector& At,float Yaw,bool bLong,float Gap,const TSharedPtr<FJsonObject>& P)const;
 void Place(FSwimmer& S,const TSharedPtr<FJsonObject>& P,const TCHAR* Pose,float Z);
 void Step(int32 I,float Dt);
 /** Water slide (pool "slide"): the climb (stair foot -> top -> chute start, feet height) and the chute floor at
  *  t 0..1, both in world cm from the generator's shape (tools/gen_hotel.py water_slide). */
 static TArray<FVector> SlideClimb(const TSharedPtr<FJsonObject>& Slide);
 static FVector SlideChute(const TSharedPtr<FJsonObject>& Slide,float T);
 bool SpawnRider(int32 Pool,const TSharedPtr<FJsonObject>& P);
 /** Hooks the swimmer's stepping into its own tick (AMarePerson::PreTick). */
 void Drive(AMarePerson* Person);
};
