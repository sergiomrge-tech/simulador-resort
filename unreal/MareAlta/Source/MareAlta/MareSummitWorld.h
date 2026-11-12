#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareSummitWorld.generated.h"
class AMarePerson;
class APlayerController;
class AStaticMeshActor;
class UAudioComponent;
class SWidget;

/** The old man on the summit and the tsunami (04/11, Sergio): Seu Tibúrcio sits on a bench in front of his wooden house
 *  on top of the mountain behind the village (trail: mare_tsunami.trail). Once the player has met him, every day an
 *  offering must reach his basket (any kiosk product carried up the trail; a hug while there is no kiosk yet).
 *  Forgotten (08/11, by day): reminders at 12h and 13h30, at 14h the omen (the sky darkens slowly into a grey storm,
 *  rain, very rough sea), at 16h the wave: the sea draws back from every beach, the wall rises far out, grows as it
 *  shoals, breaks near the shore (its crest pitches forward and collapses into white water) and runs in; when it
 *  reaches the hero the screen goes black and a big GAME OVER offers to restart the day (the morning snapshot) or go
 *  to the main menu. The map is never shown devastated.
 *  Save: State.summit {met, last_day}. QA: mare.Tsunami 0 disables it, mare.TsunamiNow 1 = omen now, 2 = wave now,
 *  mare.ElderMet 1 marks him met. */
UCLASS()
class MAREALTA_API UMareSummitWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 virtual void Deinitialize() override;
 /** E on Seu Tibúrcio. */
 void Talk(APlayerController* Controller);
 /** 0..1: the omen's storm (rain, storm clouds, sea far rougher than a stormy day); MareVisualWorld reads it. */
 float OmenLevel()const{return Omen;}
 bool IsWaveRunning()const{return bWave;}
 /** 0..1, eased slowly by MareVisualWorld: the grey storm sky of the omen and the wave (daylight stays). */
 float GloomTarget()const{return bOmenOn||bWave?1.f:0.f;}
 /** QA/film: the wave's state (time, front distance to the coast in cm, height in cm, break 0..1, drawback cm). */
 FString WaveReport()const;
 bool IsGameOver()const{return bOver;}
 /** Pure rule for the automation test: has today's offering been made (or is the rule not active yet)? */
 static bool OfferingDone(bool bMet,int32 LastDay,int32 Day){return !bMet || LastDay>=Day;}
 /** Which phase a day is in at Minutes when the offering is missing: 0 calm, 1 reminder, 2 omen, 3 wave. */
 // 08/11 (Sergio: "o dia virou noite de repente... pode continuar de dia"): the whole event happens by day.
 static int32 PhaseAt(double Minutes){return Minutes>=16*60?3:Minutes>=14*60?2:Minutes>=12*60?1:0;}
private:
 UPROPERTY() TObjectPtr<AMarePerson> Elder;
 UPROPERTY() TObjectPtr<AStaticMeshActor> Wave;
 UPROPERTY() TObjectPtr<UAudioComponent> Roar;
 /** Lightning: a cold directional light that flashes twice with each thunder clap during the omen and the wave. */
 UPROPERTY() TObjectPtr<class ADirectionalLight> Lightning;
 float FlashTime=-10.f;
 void Thunder(float Gain);
 void UpdateLightning(float DeltaSeconds);
 TSharedPtr<SWidget> OverWidget;
 bool bReady=false,bWave=false,bOver=false,bOmenOn=false,bForcedOmen=false;
 float Omen=0,WaveTime=0,OverTime=0,ThunderClock=0;
 /** The wave (08/11): its origin y, height in cm (the mesh is 100 m tall at scale 1), how far it has broken (0..1),
  *  the distance of its front foot to the coast and the sea's draw-back in cm (MPC_MareTime.Drawback). */
 float WaveY=0,WaveHeight=0,WaveBreak=0,FrontShore=0,Drawback=0;
 UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> WaveWater;
 UPROPERTY() TObjectPtr<class UMaterialInstanceDynamic> WaveSpray;
 UPROPERTY() TObjectPtr<class UMaterialParameterCollection> TimeCollection;
 void SetDrawback(float Cm);
 int32 SeenDay=-1,Reminded=-1,Hinted=-1;
 FString PrevWeather,MorningState;
 void Setup();
 void Offer(const FString& Gift,bool bCount=true);
 /** Campaign finale "A Festa da Maré Alta": the night party on the beach, Seu Tibúrcio comes down, the volcano's
  *  fireworks, then THE END with credits (prog.campaign.finale). */
 UPROPERTY() TObjectPtr<AMarePerson> PartyElder;
 TSharedPtr<SWidget> CreditsWidget;
 bool bFinale=false;float FinaleTime=0;int32 FinaleLine=-1;
 void UpdateFinale(float DeltaSeconds,class UMareSimulation* Sim,double Minutes);
 void ShowCredits();
 void CloseCredits();
 void StartOmen();
 void EndOmen();
 void StartWave();
 void UpdateWave(float DeltaSeconds);
 void ShowGameOver();
 void RestoreMorning(bool bRestart);
};
