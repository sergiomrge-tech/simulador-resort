#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareArcade.generated.h"
class AStaticMeshActor;
class ACameraActor;
class APlayerController;
class UCanvas;
class UCanvasRenderTarget2D;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UTexture2D;
class UPrimitiveComponent;
class AMareServiceTarget;

/** The arcade screen and cabinet geometry (tools/ue58/gen_arcade_cabinet.py, tools/ue58/gen_arcade_art.py). */
namespace MareArc
{
 inline constexpr int32 VW=320,VH=240;                     // virtual screen of both games
 inline const FVector ScreenLocal(0,20.97,129.05);          // screen centre, cabinet local cm
 inline const FVector ScreenNormal(0,.9749,.2225);          // outward normal, cabinet local
 inline constexpr float ScreenW=40.f,ScreenH=30.f;           // cm
}

/** "Corrida de Jangada": the raft goes up a river between sand banks; steer left/right, dodge rocks and fishing
 *  boats, net the fish (gold fish worth more). Three lives; the river speeds up. Pure simulation (tested). */
struct FMareJangada
{
 struct FThing{int32 Kind=0;float X=0,Y=0,W=0,H=0,VX=0;bool bDone=false;};   // Kind 0 rock, 1 boat, 2 fish, 3 gold fish
 static constexpr float RaftY=196,RaftW=18,RaftH=30,Bank=28;
 float X=MareArc::VW*.5f,Speed=60,Dist=0,Spawn=1,Hurt=0,Time=0,Scroll=0;
 int32 Lives=3,Score=0,Fish=0,Hits=0;bool bOver=false;
 TArray<FThing> Things;
 void Reset();
 /** Steer -1..1; returns the events of the step (bit 1 hit, 2 fish, 4 gold, 8 game over). */
 int32 Step(float Dt,float Steer,FRandomStream& R);
 int32 Points() const{return Score+int32(Dist/10);}
};

/** "Pinball do Farol": a video pinball on the arcade screen. The ball is launched from the plunger lane, rolls down the
 *  tilted table (gravity), bounces off the chrome walls and the three bumpers (+100, kicked away), lights the three
 *  rollover lanes at the top (+250 each, all three = +1000), and is kept in play by the two flippers; it drains between
 *  them. Three balls. Geometry in virtual px, the same numbers as tools/ue58/gen_arcade_art.py (PB_*). Pure simulation. */
struct FMarePinball
{
 static constexpr float BallR=4,Gravity=230,BumperR=11,FlipLen=22,FlipRest=30,FlipUp=-28;   // degrees (screen y down)
 FVector2D Ball=FVector2D(228,224),Vel=FVector2D::ZeroVector;
 float Flip[2]={FlipRest,FlipRest},FlipPrev[2]={FlipRest,FlipRest},Flash[3]={0,0,0},Still=0,Time=0;
 bool bLanes[3]={false,false,false},bInLane=true,bOver=false;
 int32 Balls=3,Score=0,Bumps=0,Saves=0;
 void Reset();
 /** Flippers held (left, right) and the launch; returns events (1 bumper, 2 lane, 4 all lanes, 8 game over, 16 ball lost, 32 flipper hit). */
 int32 Step(float Dt,bool bLeft,bool bRight,bool bLaunch);
 int32 Points() const{return Score;}
 static FVector2D Pivot(int32 Side){return Side==0?FVector2D(126,206):FVector2D(178,206);}
 FVector2D Tip(int32 Side,float Angle) const;
 static FVector2D BumperPos(int32 I){return I==0?FVector2D(130,80):I==1?FVector2D(176,80):FVector2D(153,118);}
 static float LaneX(int32 I){return 128+25*I;}
};

/** The two playable arcade cabinets of the Grand Hotel game room (CHECKLIST 5.4 "2 fliperamas jogáveis em tela";
 *  06/11, Sergio: "fliperama de pinball e corrida": Corrida de Jangada and Pinball do Farol).
 *  The game is drawn on a canvas render target put on the cabinet's own screen (M_ArcadeScreen), the camera moves in
 *  front of it; A/D or the arrows (stick) steer, Space/E (A button) acts, Q/Esc (B) leaves. A token per game pays the
 *  business (PlayBusiness "fliperama", 0-3 by points); the best score of each game is saved (prog.biz.fliperama.records)
 *  and beating it gives fame. Values in business_games.json businesses.fliperama.arcade. */
UCLASS()
class MAREALTA_API UMareArcade : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 bool IsPlaying() const{return Game>=0;}
 /** Plays the cabinet nearest the player (0 Jangada, 1 Pinball; Force >= 0 picks it). */
 bool Start(APlayerController* Controller,int32 Force=-1);
 void Stop(const FString& Message);
 FString Status() const;
 /** QA: "start:0|1", "steer:-1..1", "swing", "step:seconds", "end", "state". */
 FString QA(const FString& Cmd);
 UFUNCTION() void DrawScreen(UCanvas* Canvas,int32 Width,int32 Height);
 /** Business result of a game: 0..3 by the points thresholds of business_games.json. */
 static int32 HitsFor(int32 GameIndex,int32 Points,const TSharedPtr<class FJsonObject>& Defs);
 static const TCHAR* GameId(int32 I){return I==0?TEXT("jangada"):TEXT("pinball");}
 FMareJangada Jangada;
 FMarePinball Pinball;
private:
 void FindCabinets();
 void Finish();
 UTexture2D* Tex(const TCHAR* Name);
 void DrawSprite(UCanvas* C,UTexture2D* T,float X,float Y,float W,float H,FLinearColor Tint=FLinearColor::White,FVector2D UV0=FVector2D(0,0),FVector2D UVS=FVector2D(1,1),float Rotation=0,FVector2D Pivot=FVector2D(.5f,.5f)) const;
 void DrawText(UCanvas* C,const FString& Text,float X,float Y,float Size,FLinearColor Color,bool bCentre=false) const;
 int32 Game=-1,Cabinet=-1;float Scale=2,Over=0,Idle=0;bool bPaid=false,bRecord=false;int32 Record=0,Final=0;
 FRandomStream Rng;
 TWeakObjectPtr<APlayerController> Player;
 UPROPERTY() TArray<TObjectPtr<AStaticMeshActor>> Cabinets;
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> Targets;
 UPROPERTY() TObjectPtr<UCanvasRenderTarget2D> Screen;
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> ScreenMID;
 UPROPERTY() TObjectPtr<UMaterialInterface> SavedMaterial;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TMap<FString,TObjectPtr<UTexture2D>> Textures;
 int32 ScreenSlot=-1;
 TArray<TWeakObjectPtr<UPrimitiveComponent>> HiddenParts;
 float Clock=0;
};
