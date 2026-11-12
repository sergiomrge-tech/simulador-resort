#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareBeachSports.generated.h"
class AMarePerson;
class AStaticMeshActor;
class FJsonObject;

/**
 * People playing on the beach (10/11, Sergio: "para deixar a praia mais viva faça pessoas jogando vôlei, peteca,
 * futebol de praia, mas em dias diferentes", "aleatória"). One sport a day, drawn from the day number (never the same
 * two days running), on dry days during the hours of Content/Data/beach_sports.json:
 *   - volleyball: 2 x 2 over a net, three touches a side (bump, set, jump attack), points, the ball fetched and served;
 *   - peteca: three people in a ring keeping the shuttlecock up with the palm;
 *   - beach soccer: 2 x 2 between two small goals, ground passes, interceptions, shots, saves and goals.
 * Life only (no management). Players are beach people (swimwear MetaHumans) moved by this system from their own tick
 * (AMarePerson::PreTick), with the UAL jog / crouch / jump clips and hands or the right foot reaching the ball by IK
 * at each touch. Players, net and goals appear and leave out of the player's sight.
 * QA: mare.Sport <volei|peteca|futebol|auto|clear|dump>.
 */
UCLASS()
class MAREALTA_API UMareBeachSportsWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 enum class ESport:uint8{None,Volley,Peteca,Soccer};
 /** The sport of a game day: random-looking, the same for the whole day, never yesterday's. */
 static ESport SportOfDay(int32 Day);
 static const TCHAR* SportName(ESport Sport);
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 static TSharedPtr<FJsonObject> Defs();
 /** QA: -1 follows the schedule; otherwise this sport is on now, whatever the hour, the weather or who is looking. */
 int32 Forced=-1;
 void ClearAll();
 FString Dump()const;

 enum class ETouch:uint8{Bump,Set,Attack,Serve,Catch,Palm,Kick,Trap,Save};
 enum class EPhase:uint8{Rest,Flight,Dead,Fetch,Hold,Windup};
 struct FPlayer
 {
  TWeakObjectPtr<AMarePerson> Person;int32 Team=0;
  FVector Home=FVector::ZeroVector,Pos=FVector::ZeroVector,Target=FVector::ZeroVector;
  float Yaw=0,GroundZ=0,GroundIn=0,ArriveIn=0;
  /** Seconds left of the reach for the ball (hands or foot follow it), of the hop of a jump attack, of a cheer. */
  float Reach=0,Hop=0,HopTotal=0,Busy=0;ETouch Touch=ETouch::Bump;bool bMoving=false,bCrouch=false;
 };
 TArray<FPlayer> Players;
 ESport Sport=ESport::None;
 EPhase Phase=EPhase::Rest;
 /** Ball: a flight is a straight line From -> To in Duration seconds plus an arc of Apex cm at mid flight (bGround: a
  *  rolling pass that slows down, no arc). Receiver touches it at To; -1 = nobody (it falls on the sand / into a goal). */
 FVector BallPos=FVector::ZeroVector,From=FVector::ZeroVector,To=FVector::ZeroVector,BallSpin=FVector::ZeroVector;
 float FlightT=0,Duration=1,Apex=0,Wait=0;bool bGround=false;
 int32 Receiver=-1,Holder=-1,LastHitter=-1,Touches=0,Side=0,Rally=0,Points[2]={0,0},Serving=0;ETouch NextTouch=ETouch::Bump;
 bool bGoal=false,bPicked=false,bRebound=false;
 /** QA (mare.Sport hold): freezes the game just before the next touch, to photograph the reach up close. */
 bool bQAFreeze=false;
 /** Hero inside the play area: the players hold the ball and wait. */
 bool HeroOnCourt()const;
private:
 TWeakObjectPtr<AStaticMeshActor> Ball;
 TArray<TWeakObjectPtr<AActor>> Props;
 FVector Centre=FVector::ZeroVector;float CourtYaw=0;bool bDefsRead=false;
 float Clock=0,Repos=0,HalfL=700,HalfW=340;
 /** Court frame: Along (the long axis, team 0 on the negative side) and Across, in world cm from the centre. */
 FVector At(float Along,float Across,float Up=0)const;
 float AlongOf(const FVector& P)const;
 float AcrossOf(const FVector& P)const;
 float Ground(const FVector& P)const;
 bool HeroNear(float Radius)const;
 bool Begin(ESport Wanted);
 AStaticMeshActor* Prop(const TCHAR* Slug,const FVector& Where,float Yaw,bool bMovable);
 void Drive(AMarePerson* Person);
 void StepPlayer(int32 I,float Dt);
 void StepBall(float Dt);
 /** Sends the ball from where it is to Target for player To (or nobody), reaching it in Seconds with an arc of Arc cm. */
 void Launch(const FVector& Target,int32 ToPlayer,float Seconds,float Arc,ETouch Touch,bool bRoll=false);
 void Arrived();
 void Decide(float Dt);
 void VolleyNext(int32 Hitter);
 void PetecaNext(int32 Hitter);
 void SoccerNext(int32 Hitter);
 void Positions();
 int32 Nearest(const FVector& P,int32 Team=-1,int32 Not=-1)const;
 int32 Mate(int32 I)const;
 FVector HandPoint(int32 I)const;
 /** Where player I touches the ball standing at Stand and facing Toward: ahead of the feet and up, by kind of touch. */
 FVector Contact(const FVector& Stand,const FVector& Toward,ETouch Touch,float ExtraUp=0)const;
 /** Sends player I to Stand, to be there in Seconds. */
 void Meet(int32 I,const FVector& Stand,float Seconds);
};
