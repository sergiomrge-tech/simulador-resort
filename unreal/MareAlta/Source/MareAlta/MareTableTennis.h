#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareTableTennis.generated.h"
class AStaticMeshActor;
class UPrimitiveComponent;
class ACameraActor;
class AMareServiceTarget;
class AMarePerson;
class APlayerController;

/** Table tennis dimensions (metres, tools/ue58/gen_table_tennis.py); table space: x along the length (the player's
 *  half is x<0), y across, z up from the playing surface. */
namespace MareTT{inline constexpr double L=2.74,W=1.525,NetH=.1525,R=.02,Top=.76,Reach=.24,Plane=.3;}

/** Grand Hotel game room: table tennis against a hotel guest (03/11, "tênis de mesa com gameplay completo").
 *  Real rules: the serve bounces once on the server's half, then on the receiver's (a net touch on a good serve is a
 *  let); in the rally each side returns after exactly one bounce on its half; bouncing twice, hitting your own half or
 *  missing the table loses the point. Games to 11 by two, the serve changes every 2 points (every point from 10-10),
 *  best of 3 games. The ball is a deterministic 3D simulation (gravity, air drag, topspin, table and net). */
UCLASS()
class MAREALTA_API UMareTableTennis : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 void StartMatch(APlayerController* Controller,const FString& Opponent,double Stake=0);
 void EndMatch(const FString& Message);
 bool IsPlaying() const{return bPlaying;}
 FString Status() const;
 // ---- Simulation (automation tests use it without a world).
 FVector Ball=FVector::ZeroVector,Vel=FVector::ZeroVector;
 double Spin=0;                 // topspin (+) / backspin (-), -1..1
 int32 Points[2]={0,0},Games[2]={0,0};
 int32 FirstServer=0,Server=0,MatchWinner=-1;
 bool bInPlay=false;           // ball travelling (false: waiting for the serve)
 bool bServing=false;          // the ball in flight is a serve
 int32 LastHitter=-1,ServeBounces=0,BouncesSinceHit=0,BounceSide=-1;
 bool bNetTouch=false;
 double PaddleY[2]={0,0};
 double Skill[2]={.12,.12};    // aiming error (m) of each side's shot AI: smaller is better
 double Speed[2]={2.2,2.2};    // how fast each side's paddle slides (m/s)
 FString Call;                 // umpire line of the last point
 int32 Rallies=0;
 void NewMatch(int32 First);
 /** Ball in the server's hand above its end of the table. */
 void ReadyServe();
 /** Serve aimed at TargetY on the receiver's half. */
 void Serve(int32 Side,double TargetY,uint32 Seed);
 /** Return the ball from its current position to (TargetX, TargetY) on the far half at a horizontal speed. */
 void Hit(int32 Side,double TargetX,double TargetY,double HSpeed,double Topspin);
 /** Advances the ball; returns true while the point goes on. */
 bool Step(double Seconds);
 /** Side whose paddle plane the ball is crossing now with a legal bounce behind it (-1 none). */
 int32 HitWindow() const;
 /** The shot AI for Side when the ball is in its window: true if it reached and returned the ball. */
 bool AIReturn(int32 Side,uint32 Seed);
 /** Where the ball will cross Side's paddle plane (y), simulating ahead. */
 double PredictY(int32 Side) const;
 void AwardPoint(int32 Side,const FString& Why);
private:
 bool Fly(FVector& P,FVector& V,double& S,double Dt) const;
 FVector World(const FVector& P) const;
 void SpawnProps();
 void UpdateProps(float DeltaSeconds);
 bool bPlaying=false,bSmash=false;
 float Delay=0,AimDrift=0;
 double Stake=0;
 FString Opponent;
 TArray<TWeakObjectPtr<UPrimitiveComponent>> HiddenParts;   // player body parts hidden during the match
 TArray<TWeakObjectPtr<AActor>> HiddenNearby;   // passers-by hidden while they stand in the match camera's way
 FTransform Table=FTransform::Identity;
 TWeakObjectPtr<APlayerController> Player;
 UPROPERTY() TObjectPtr<AStaticMeshActor> TableActor;
 UPROPERTY() TObjectPtr<AStaticMeshActor> BallActor;
 UPROPERTY() TObjectPtr<AStaticMeshActor> PlayerBat;
 UPROPERTY() TObjectPtr<AStaticMeshActor> GuestBat;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TObjectPtr<AMareServiceTarget> Target;
 UPROPERTY() TObjectPtr<AMarePerson> Guest;
};
