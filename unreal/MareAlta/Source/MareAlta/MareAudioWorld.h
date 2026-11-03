#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareAudioWorld.generated.h"
class UAudioComponent;
class USoundWave;
class USoundAttenuation;
class USoundSubmix;
class UMareSimulation;

/** Quiet layered soundscape; original instrumental music, no crowd voices. */
UCLASS()
class MAREALTA_API UMareAudioWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Initialize(FSubsystemCollectionBase& Collection) override;
 virtual void Deinitialize() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 /** Playback uses the effects bus; positional cues use distance attenuation. */
 UAudioComponent* PlayCue(FName Name,float Gain=.35f,const FVector* Position=nullptr,bool bAmbient=false);
 /** Action sound (Content/Data/audio.json "group"): one of its variations at the catalog volume times Scale. */
 UAudioComponent* PlayAction(const FString& Group,const FVector* Position=nullptr,float Scale=1.f);
 static void Action(const UObject* Context,const FString& Group,const FVector* Position=nullptr,float Scale=1.f);
 UFUNCTION(BlueprintCallable,Category="Audio") void SetVolume(FName Bus,float Value);
 UFUNCTION(BlueprintPure,Category="Audio") float GetVolume(FName Bus)const;
 /** Factory volume of a bus (Master, Music, Effects, Ambient), used by "Restaurar padrão". */
 static float DefaultVolume(FName Bus);
 UFUNCTION(BlueprintPure,Category="Audio") int32 LoadedSounds()const{return Sounds.Num();}
 UFUNCTION(BlueprintPure,Category="Audio") float LoopLevel(FName Name)const;
 UFUNCTION(BlueprintPure,Category="Audio") bool HasMasterMix()const{return MasterMix!=nullptr;}
 UFUNCTION(BlueprintCallable,Category="Audio") void SetRadioStation(FName Station);
 UFUNCTION(BlueprintPure,Category="Audio") FName GetRadioStation()const{return RadioStation;}
 /** Ordered radio stations (original instrumental music) followed by "off". */
 static const TArray<FName>& RadioStations();
 static bool IsRadioStation(FName Name){return Name!=TEXT("off") && RadioStations().Contains(Name);}
 static FString RadioName(FName Station);
 /** Cycle to the next station, ending with the radio switched off. */
 UFUNCTION(BlueprintCallable,Category="Audio") void NextRadioStation();
 /** Physical home stereo is spatial, uses Music volume and ducks the portable radio nearby. */
 void SetHomeStereo(bool bEnabled,FVector Position);
private:
 UPROPERTY() TMap<FName,TObjectPtr<USoundWave>> Sounds;
 TMap<FString,TArray<FName>> Groups;
 TMap<FString,float> GroupVolume;
 UPROPERTY() TMap<FName,TObjectPtr<UAudioComponent>> Loops;
 UPROPERTY() TMap<TObjectPtr<UAudioComponent>,float> Voices;
 UPROPERTY() TObjectPtr<USoundAttenuation> Attenuation;
 UPROPERTY() TObjectPtr<USoundSubmix> MasterMix;
 UPROPERTY() TObjectPtr<UAudioComponent> HomeStereo;
 bool bHomeStereo=false;
 TMap<FName,float> Volumes;
 FName RadioStation=TEXT("reggae_praia");
 TMap<FName,double> LastCue;
 float BirdClock=3,GullClock=8,StepClock=0,ThunderClock=12,IndoorClock=0;
 bool bReady=false,bUnderwater=false,bIndoors=false,bWasPhone=false,bWasSwimming=false;
 double LastCash=0;FString LastCarry;int32 LastOrders=0,LastBell=-1;
 void StartSoundscape(UMareSimulation* Sim);
 void UpdateLayers(float DeltaSeconds,UMareSimulation* Sim,FVector Position,bool bRain,bool bNight);
 void UpdateEvents(float DeltaSeconds,UMareSimulation* Sim,FVector Position,bool bRain,bool bNight);
 float Gain(bool bAmbient)const;
};
