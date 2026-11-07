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
 *  Forgotten: reminders at 15h and 18h, at 19h the omen (heavy rain, extremely rough sea), at 22h the wave rises far
 *  out to 100 m and runs in; when it reaches the hero the screen goes black and a big GAME OVER offers to restart the
 *  day (the morning snapshot) or go to the main menu. The map is never shown devastated.
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
 bool IsGameOver()const{return bOver;}
 /** Pure rule for the automation test: has today's offering been made (or is the rule not active yet)? */
 static bool OfferingDone(bool bMet,int32 LastDay,int32 Day){return !bMet || LastDay>=Day;}
 /** Which phase a day is in at Minutes when the offering is missing: 0 calm, 1 reminder, 2 omen, 3 wave. */
 static int32 PhaseAt(double Minutes){return Minutes>=22*60?3:Minutes>=19*60?2:Minutes>=15*60?1:0;}
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
 bool bReady=false,bWave=false,bOver=false,bOmenOn=false;
 float Omen=0,WaveTime=0,OverTime=0,ThunderClock=0;
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
