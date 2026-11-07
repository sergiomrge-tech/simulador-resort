#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareFoosball.generated.h"
class AStaticMeshActor;
class UPrimitiveComponent;
class ACameraActor;
class AMarePerson;
class APlayerController;

/** Foosball table (metres, tools/ue58/gen_foosball.py). Field space: X along the table toward the guest's goal (the
 *  player's goal is at X=-HX), Y across (the player's handles at Y<0), the playfield at z=0. Rod i is at RodX(i); its
 *  men hang from the axis RodH above the playfield, the foot block FootR below the axis. */
namespace MareFB
{
 inline constexpr double HX=.675,HY=.35,R=.0175,GoalHalf=.11,Field=.76,RodH=.105,FootR=.095,FootHX=.017,FootHY=.015,Lift=.68;
 inline constexpr int32 Rods=8;
 inline constexpr int32 Count[Rods]={1,2,3,5,5,3,2,1};
 inline constexpr int32 Team[Rods]={0,0,1,0,1,0,1,1};
 inline double RodX(int32 I){return -.6125+I*.175;}
 double Travel(int32 Men);
 double Man(int32 Men,int32 K);
}

/** Grand Hotel game room: foosball against a hotel guest with real rod control (5.4, "Pebolim com controle real (girar
 *  as barras)"). The mouse slides the active rod (the player's rod nearest behind the ball) up and down and turns it
 *  left and right: the men's feet swing with the rod and kick the ball with the speed of the turn; a click is a quick
 *  shot, the right button lifts the men so the ball passes. The other rods of the player's team keep in line with the
 *  ball. The ball is a deterministic 2D simulation (rolling friction, walls, corner ramps, goal mouths, the foot blocks
 *  as moving boxes). First to 5 goals. At night (game_room token hours) two guests play AI against AI. */
UCLASS()
class MAREALTA_API UMareFoosball : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 bool HasTable() const{return TableActor!=nullptr;}
 void StartMatch(APlayerController* Controller,const FString& Opponent);
 void EndMatch(const FString& Message);
 bool IsPlaying() const{return bPlaying;}
 FString Status() const;
 /** HUD: the active rod from its grip to the near wall (world). */
 bool ActiveRodLine(FVector& From,FVector& To) const;
 // ---- Simulation (automation tests use it without a world).
 FVector2D Ball=FVector2D::ZeroVector,Vel=FVector2D::ZeroVector;
 double RodY[MareFB::Rods]={},RodA[MareFB::Rods]={},RodW[MareFB::Rods]={},RodVY[MareFB::Rods]={};
 int32 Goals[2]={0,0},Winner=-1,LastTouch=-1,Active=3,Serves=0,Touches=0,Restarts=0;
 bool bLive=false;
 double Still=0,Sideways=0,Skill[2]={1.1,1.1};
 FString Call;
 static constexpr int32 WinGoals=5;
 void NewMatch();
 /** Ball dropped in at midfield from a side wall, rolling in. */
 void Serve(uint32 Seed);
 /** Advances the ball; returns false when a goal or a dead ball stopped play this step. */
 bool Step(double Seconds);
 /** Rod control of a team by the AI (also the player's other rods when Assist): track the ball, kick when it is in
  *  front of a man, lift the rods the team's own shot must pass. */
 void AI(int32 Side,double Dt,uint32 Seed,bool bAssistOnly=false,int32 Skip=-1);
 /** Sets a rod's angle for this step, keeping its angular speed for the kick. */
 void TurnRod(int32 I,double Angle,double Dt);
 void SlideRod(int32 I,double Y,double Dt);
 /** Man of rod I nearest to the field Y (-1 none in reach). */
 int32 NearestMan(int32 I,double Y,double& Gap) const;
 int32 PickActive(int32 Current) const;
 /** The player's hands for one step: mouse deltas (DY forward slides the active rod away from the player, DX turns the
  *  feet toward the guest's goal), a click kicks, the right button lifts; the gamepad sticks/triggers the same. */
 struct FInput{float DX=0,DY=0,PadX=0,PadY=0;bool bShot=false,bLift=false;};
 void PlayerControl(const FInput& In,double Dt);
 /** Business result: 3 = won by 3 or more, 2 won, 1 lost by 1-2, 0 lost by more. */
 static int32 Hits(int32 Mine,int32 Theirs);
private:
 struct FKick{int32 Phase=0;double T=0,Cool=0,Dir=1;};
 FKick Kick[MareFB::Rods];
 double AimY[MareFB::Rods]={};
 FVector Local(double X,double Y,double Z) const;
 void SpawnProps();
 void UpdateProps(float DeltaSeconds);
 void Score(int32 Side);
 bool NightDemo() const;
 bool bPlaying=false,bDemo=false;
 float Delay=0;
 double PlayerA=0;
 float Idle=0;
 FQuat BallSpin=FQuat::Identity;
 FString Opponent;
 TArray<TWeakObjectPtr<UPrimitiveComponent>> HiddenParts;
 TArray<TWeakObjectPtr<AActor>> HiddenNearby;
 FTransform Table=FTransform::Identity;
 TWeakObjectPtr<APlayerController> Player;
 UPROPERTY() TObjectPtr<AStaticMeshActor> TableActor;
 UPROPERTY() TObjectPtr<AStaticMeshActor> BallActor;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> RodActors;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TObjectPtr<AMarePerson> Guest;
};
