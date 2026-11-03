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
 *  Eight-ball rules (03/11, "sinuca como jogo completo"): the table is open after the break until a legal pot gives the
 *  shooter solids (1-7) or stripes (9-15); the cue ball must hit one of your own group first (open table: anything but
 *  the 8); a foul (cue ball potted, nothing hit, wrong ball first) gives the opponent the ball in hand; potting your own
 *  ball keeps the turn; the 8 wins only after your group is cleared and without a foul, otherwise it loses. The 8 potted
 *  on the break is spotted again.
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
 /** Start a match from the table page: Stake is bet on the result (0 friendly), Opponent one of game_room.json
  *  "players" (their skill sets the shot AI's aim error), bCup a Campeonato da Maré round (quitting forfeits). */
 void StartMatch(APlayerController* Controller,double Stake=0,const FString& InOpponent=FString(),bool bInCup=false);
 void EndMatch(const FString& Message);
 bool IsPlaying() const{return bPlaying;}
 /** HUD helpers: the aim guide (world points), shot power 0..1 and a one-line score/turn status. */
 bool AimLine(FVector& From,FVector& To) const;
 float Power() const{return Charge;}
 FString Status() const;
 // ---- Simulation (also used by automation tests without a world).
 struct FBall{FVector2D P=FVector2D::ZeroVector,V=FVector2D::ZeroVector;bool bIn=false;};
 FBall Balls[16];
 int32 Score[2]={0,0};    // balls of each side's group already potted
 int32 Turn=0;            // 0 player, 1 guest
 int32 Winner=-1;
 int32 Group[2]={0,0};    // 0 open table, 1 solids, 2 stripes
 int32 FirstHit=-1;       // first ball the cue ball touched in the running shot
 bool bBreakShot=true;    // the next shot is the break
 bool bBallInHand=false;  // after a foul the side to play places the cue ball anywhere free
 double AimError[2]={1.4,1.4}; // degrees of aim error of each side's shot AI (opponent skill)
 FString LastCall;        // short referee line of the last shot ("Falta: branca na caçapa")
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
 /** Ball in hand for the AI: the free spot with the best pot on the table for the side to play. */
 void PlaceCueBallForAI();
 /** Ball in hand: puts the cue ball at P if it is on the cloth and clear of the other balls. */
 bool PlaceCueBall(const FVector2D& P);
 /** Group of a ball (1 solids, 2 stripes, 0 cue/8) and balls of a group still on the table. */
 static int32 GroupOf(int32 Ball){return Ball>=1 && Ball<=7?1:Ball>=9 && Ball<=15?2:0;}
 int32 Remaining(int32 InGroup) const;
 /** Balls the side to play may aim at now (own group, the 8 once cleared, anything but the 8 on an open table). */
 bool IsTarget(int32 Side,int32 Ball) const;
 TArray<int32> PottedThisShot;
 /** Sound events of the last Step (strongest ball-ball and cushion impact speeds, balls dropped). */
 double ClackSpeed=0,RailSpeed=0;int32 Drops=0;
private:
 bool PathClear(const FVector2D& A,const FVector2D& B,int32 IgnoreA,int32 IgnoreB) const;
 /** Best pot for the side to play from the current cue ball: value (<0 none), angle and speed. */
 double BestPot(double& Angle,double& Speed) const;
 void SpotEight();
 FVector World(const FVector2D& P,double Lift=0) const;
 void SpawnProps();
 void UpdateProps(float DeltaSeconds);
 bool bPlaying=false,bShotRunning=false,bCharging=false,bPlacing=false;
 FString Opponent=TEXT("Hóspede");
 bool bCup=false;
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
