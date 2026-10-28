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
 void PlayCue(FName Name,float Gain=.35f,const FVector* Position=nullptr,bool bAmbient=false);
 UFUNCTION(BlueprintCallable,Category="Audio") void SetVolume(FName Bus,float Value);
 UFUNCTION(BlueprintPure,Category="Audio") float GetVolume(FName Bus)const;
 UFUNCTION(BlueprintPure,Category="Audio") int32 LoadedSounds()const{return Sounds.Num();}
 UFUNCTION(BlueprintPure,Category="Audio") float LoopLevel(FName Name)const;
 UFUNCTION(BlueprintPure,Category="Audio") bool HasMasterMix()const{return MasterMix!=nullptr;}
 UFUNCTION(BlueprintCallable,Category="Audio") void SetRadioStation(FName Station);
 UFUNCTION(BlueprintPure,Category="Audio") FName GetRadioStation()const{return RadioStation;}
private:
 UPROPERTY() TMap<FName,TObjectPtr<USoundWave>> Sounds;
 UPROPERTY() TMap<FName,TObjectPtr<UAudioComponent>> Loops;
 UPROPERTY() TMap<TObjectPtr<UAudioComponent>,float> Voices;
 UPROPERTY() TObjectPtr<USoundAttenuation> Attenuation;
 UPROPERTY() TObjectPtr<USoundSubmix> MasterMix;
 TMap<FName,float> Volumes;
 FName RadioStation=TEXT("reggae_praia");
 TMap<FName,double> LastCue;
 float BirdClock=3,GullClock=8,DogClock=25,StepClock=0,ThunderClock=12,IndoorClock=0;
 bool bReady=false,bUnderwater=false,bIndoors=false,bWasPhone=false,bWasSwimming=false;
 double LastCash=0;FString LastCarry;int32 LastOrders=0,LastBell=-1;
 void StartSoundscape(UMareSimulation* Sim);
 void UpdateLayers(float DeltaSeconds,UMareSimulation* Sim,FVector Position,bool bRain,bool bNight);
 void UpdateEvents(float DeltaSeconds,UMareSimulation* Sim,FVector Position,bool bRain,bool bNight);
 float Gain(bool bAmbient)const;
};
