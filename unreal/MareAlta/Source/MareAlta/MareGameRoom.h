#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareGameRoom.generated.h"
class AStaticMeshActor;
class ACameraActor;
class AMareServiceTarget;
class AMarePerson;
class APlayerController;

/** Pool table dimensions in metres (tools/ue58/gen_pool_table.py); outside the exported class (DLL interface rules). */
namespace MarePool{inline constexpr double L=1.98,W=.99,R=.028575,PocketR=.062,ClothZ=.78;}

/** Grand Hotel game room (gameplay plan M5): a real-size pool table played against a hotel guest.
 *  Short rules: first to pot 4 balls wins; the 8 before having 3 loses; potting the cue ball passes the turn.
 *  Physics is a deterministic 2D simulation in table space (metres, x along the length), substepped at 240 Hz,
 *  with the dimensions of tools/ue58/gen_pool_table.py. Unlocked by the expansion "salao_jogos". */
UCLASS()
class MAREALTA_API UMareGameRoom : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 /** E at the table: rack the balls and start a match (Stake is bet on the result, 0 for a friendly game). */
 void StartMatch(APlayerController* Controller,double Stake=0);
 void EndMatch(const FString& Message);
 bool IsPlaying() const{return bPlaying;}
 /** HUD helpers: the aim guide (world points), shot power 0..1 and a one-line score/turn status. */
 bool AimLine(FVector& From,FVector& To) const;
 float Power() const{return Charge;}
 FString Status() const;
 // ---- Simulation (also used by automation tests without a world).
 struct FBall{FVector2D P=FVector2D::ZeroVector,V=FVector2D::ZeroVector;bool bIn=false;};
 FBall Balls[16];
 int32 Score[2]={0,0};
 int32 Turn=0;            // 0 player, 1 guest
 int32 Winner=-1;
 void Rack();
 /** Cue ball shot: direction in radians (table space) and speed in m/s. */
 void Shoot(double Angle,double Speed);
 /** Advances the balls; returns true while anything moves. */
 bool Step(double Seconds);
 bool Moving() const;
 /** After the balls stop: score, fouls, turn and winner. */
 void ResolveShot();
 /** Shot AI for the side to play (the guest, or the player under mare.PoolAutoPlay): best pocketable ball (ghost-ball
  *  aim) with a small error; falls back to a safe tap. */
 void PlanGuestShot(double& Angle,double& Speed,uint32 Seed) const;
 TArray<int32> PottedThisShot;
 /** Sound events of the last Step (strongest ball-ball and cushion impact speeds, balls dropped). */
 double ClackSpeed=0,RailSpeed=0;int32 Drops=0;
private:
 bool PathClear(const FVector2D& A,const FVector2D& B,int32 IgnoreA,int32 IgnoreB) const;
 FVector World(const FVector2D& P,double Lift=0) const;
 void SpawnProps();
 void UpdateProps(float DeltaSeconds);
 bool bPlaying=false,bShotRunning=false,bCharging=false;
 float Charge=0.f,GuestDelay=0.f;
 double AimAngle=0,Stake=0;
 bool bScratch=false;
 int32 Shots=0;
 FTransform Table=FTransform::Identity;
 TWeakObjectPtr<APlayerController> Player;
 UPROPERTY() TObjectPtr<AStaticMeshActor> TableActor;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> BallActors;
 UPROPERTY() TObjectPtr<AStaticMeshActor> Cue;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Target;
 UPROPERTY() TObjectPtr<AMarePerson> Guest;
};
