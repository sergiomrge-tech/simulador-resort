#include "MareAudioWorld.h"
#include "MareSummitWorld.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundWave.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundSubmix.h"
#include "Sound/AudioSettings.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Camera/CameraComponent.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TStatId UMareAudioWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareAudioWorld,STATGROUP_Tickables);}
const TArray<FName>& UMareAudioWorld::RadioStations()
{
 // Aloha FM (original Hawaiian ukulele, asked by Sergio on 03/11) opens the dial; the Mare Alta theme has its own station.
 static const TArray<FName> Stations={TEXT("radio_havaiana"),TEXT("radio_havaiana_onda"),TEXT("radio_havaiana_lua"),TEXT("music_tema"),TEXT("reggae_praia"),TEXT("radio_reggae_roots"),TEXT("radio_calypso"),TEXT("radio_beach_pop"),TEXT("music_bossa"),TEXT("music_relax"),TEXT("off")};
 return Stations;
}
FString UMareAudioWorld::RadioName(FName Station)
{
 if(Station==TEXT("radio_havaiana"))return TEXT("Aloha FM · havaiana");
 if(Station==TEXT("radio_havaiana_onda"))return TEXT("Aloha FM · onda alegre");
 if(Station==TEXT("radio_havaiana_lua"))return TEXT("Aloha FM · luar");
 if(Station==TEXT("music_tema"))return TEXT("Tema Maré Alta");
 if(Station==TEXT("reggae_praia"))return TEXT("Reggae da Praia");
 if(Station==TEXT("radio_reggae_roots"))return TEXT("Reggae Roots");
 if(Station==TEXT("radio_calypso"))return TEXT("Calipso Caribe");
 if(Station==TEXT("radio_beach_pop"))return TEXT("Praia Pop · ukulele");
 if(Station==TEXT("music_bossa"))return TEXT("Bossa praiana");
 if(Station==TEXT("music_relax"))return TEXT("Brisa instrumental");
 return TEXT("Desligada");
}
void UMareAudioWorld::NextRadioStation()
{
 const int32 Index=RadioStations().IndexOfByKey(RadioStation);
 SetRadioStation(RadioStations()[(Index+1)%RadioStations().Num()]);
}
void UMareAudioWorld::Initialize(FSubsystemCollectionBase& Collection)
{
 Super::Initialize(Collection);
 FString Station;GConfig->GetString(TEXT("MareAudio"),TEXT("Radio"),Station,GGameUserSettingsIni);
 if(RadioStations().Contains(FName(Station)))RadioStation=FName(Station);
 for(const FName Bus:{FName(TEXT("Master")),FName(TEXT("Music")),FName(TEXT("Effects")),FName(TEXT("Ambient"))}){
  float Value=DefaultVolume(Bus);GConfig->GetFloat(TEXT("MareAudio"),*Bus.ToString(),Value,GGameUserSettingsIni);Volumes.Add(Bus,FMath::Clamp(Value,0.f,1.f));
 }
}
float UMareAudioWorld::DefaultVolume(FName Bus){return Bus==TEXT("Master")?.85f:Bus==TEXT("Music")?.3f:Bus==TEXT("Effects")?.75f:Bus==TEXT("Ambient")?.7f:1.f;}
float UMareAudioWorld::GetVolume(FName Bus)const{const float* Value=Volumes.Find(Bus);return Value?*Value:1.f;}
void UMareAudioWorld::SetRadioStation(FName Station)
{
 if(!RadioStations().Contains(Station))return;
 RadioStation=Station;GConfig->SetString(TEXT("MareAudio"),TEXT("Radio"),*Station.ToString(),GGameUserSettingsIni);GConfig->Flush(false,GGameUserSettingsIni);
}
float UMareAudioWorld::LoopLevel(FName Name)const{UAudioComponent* Component=Name==TEXT("home_stereo")?HomeStereo.Get():Loops.FindRef(Name).Get();return IsValid(Component)?Component->VolumeMultiplier:0.f;}
void UMareAudioWorld::SetHomeStereo(bool bEnabled,FVector Position)
{
 bHomeStereo=bEnabled;if(!bReady)return;
 if(bEnabled && !HomeStereo)if(auto Wave=Sounds.FindRef(TEXT("music_relax"))){
  auto Local=NewObject<USoundAttenuation>(this);Local->Attenuation.bAttenuate=true;Local->Attenuation.bSpatialize=true;
  Local->Attenuation.AttenuationShapeExtents=FVector(150);Local->Attenuation.FalloffDistance=650;
  HomeStereo=UGameplayStatics::SpawnSoundAtLocation(this,Wave,Position,FRotator::ZeroRotator,.001f,1,0,Local,nullptr,false);
  if(HomeStereo)HomeStereo->SetUISound(false);
 }
 if(HomeStereo){HomeStereo->SetWorldLocation(Position);HomeStereo->SetVolumeMultiplier(bEnabled && GetVolume(TEXT("Master"))>0?GetVolume(TEXT("Music"))*.24f*(MasterMix?1.f:GetVolume(TEXT("Master"))):0.f);}
}
float UMareAudioWorld::Gain(bool bAmbient)const{return (MasterMix?1.f:GetVolume(TEXT("Master")))*GetVolume(TEXT("Effects"))*(bAmbient?GetVolume(TEXT("Ambient")):1.f);}
void UMareAudioWorld::SetVolume(FName Bus,float Value)
{
 if(!Volumes.Contains(Bus))return;Value=FMath::Clamp(Value,0.f,1.f);Volumes[Bus]=Value;
 GConfig->SetFloat(TEXT("MareAudio"),*Bus.ToString(),Value,GGameUserSettingsIni);GConfig->Flush(false,GGameUserSettingsIni);
 if(Bus==TEXT("Master") && MasterMix)MasterMix->SetSubmixOutputVolume(this,Value);
 if(HomeStereo && (GetVolume(TEXT("Master"))==0 || GetVolume(TEXT("Music"))==0))HomeStereo->SetVolumeMultiplier(0);
 for(auto& Voice:Voices)if(IsValid(Voice.Key))Voice.Key->SetVolumeMultiplier(GetVolume(TEXT("Master"))==0?0:Voice.Value*Gain(Voice.Key->ComponentHasTag(TEXT("Ambient"))));
 for(auto Pair:Loops)if(IsValid(Pair.Value) && (GetVolume(TEXT("Master"))==0 || (IsRadioStation(Pair.Key)?GetVolume(TEXT("Music"))==0:GetVolume(TEXT("Effects"))*GetVolume(TEXT("Ambient"))==0)))Pair.Value->SetVolumeMultiplier(0);
}
void UMareAudioWorld::StartSoundscape(UMareSimulation* Sim)
{
 MasterMix=Cast<USoundSubmix>(GetDefault<UAudioSettings>()->MasterSubmix.TryLoad());
 if(MasterMix)MasterMix->SetSubmixOutputVolume(this,GetVolume(TEXT("Master")));
 FString Text;TArray<TSharedPtr<FJsonValue>> Catalog;
 if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/audio.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Catalog);
 for(auto Item:Catalog){auto Row=Item->AsObject();const FString Name=UMareSimulation::String(Row,TEXT("id"));if(auto Wave=LoadObject<USoundWave>(nullptr,*UMareSimulation::String(Row,TEXT("path")))){Sounds.Add(FName(Name),Wave);
  const FString Group=UMareSimulation::String(Row,TEXT("group"));if(!Group.IsEmpty()){Groups.FindOrAdd(Group).Add(FName(Name));GroupVolume.Add(Group,UMareSimulation::Number(Row,TEXT("volume")));}}}
 TArray<FName> LoopNames=RadioStations();LoopNames.Remove(TEXT("off"));
 LoopNames.Append({TEXT("ocean_loop"),TEXT("wind_loop"),TEXT("rain_loop"),TEXT("crickets_loop"),TEXT("leaves_soft"),TEXT("underwater_loop"),TEXT("forest_loop")});
 for(FName Name:LoopNames){
  if(auto Wave=Sounds.FindRef(Name)){auto Component=UGameplayStatics::SpawnSound2D(this,Wave,.001f,1,0,nullptr,false,false);if(Component){Component->SetUISound(false);Loops.Add(Name,Component);}}
 }
 Attenuation=NewObject<USoundAttenuation>(this);Attenuation->Attenuation.bAttenuate=true;Attenuation->Attenuation.bSpatialize=true;
 Attenuation->Attenuation.AttenuationShapeExtents=FVector(150);Attenuation->Attenuation.FalloffDistance=3200;
 LastCash=Sim->Money();LastCarry=Sim->Carry();LastOrders=UMareSimulation::Object(Sim->State,TEXT("ue_orders"))->Values.Num();bReady=true;
 UE_LOG(LogTemp,Display,TEXT("MARE_AUDIO_READY %d sounds"),Sounds.Num());
}
UAudioComponent* UMareAudioWorld::PlayAction(const FString& Group,const FVector* Position,float Scale)
{
 const TArray<FName>* Names=Groups.Find(Group);if(!Names || !Names->Num())return nullptr;
 return PlayCue((*Names)[FMath::RandRange(0,Names->Num()-1)],GroupVolume.FindRef(Group)*Scale,Position);
}
void UMareAudioWorld::Action(const UObject* Context,const FString& Group,const FVector* Position,float Scale)
{
 if(UWorld* World=Context?Context->GetWorld():nullptr)if(auto Audio=World->GetSubsystem<UMareAudioWorld>())Audio->PlayAction(Group,Position,Scale);
}
UAudioComponent* UMareAudioWorld::PlayCue(FName Name,float Volume,const FVector* Position,bool bAmbient)
{
 auto Wave=Sounds.FindRef(Name);if(!Wave || GetVolume(TEXT("Master"))<=.001 || Gain(bAmbient)<=.001 || UGameplayStatics::IsGamePaused(this))return nullptr;
 const double Now=GetWorld()->GetTimeSeconds();if(Voices.Num()>=16 || (LastCue.Contains(Name) && Now-LastCue[Name]<.12))return nullptr;LastCue.Add(Name,Now);
 auto Component=Position?UGameplayStatics::SpawnSoundAtLocation(this,Wave,*Position,FRotator::ZeroRotator,Volume*Gain(bAmbient),FMath::FRandRange(.97f,1.03f),0,Attenuation):UGameplayStatics::SpawnSound2D(this,Wave,Volume*Gain(bAmbient));
 if(Component){Component->SetUISound(false);if(bAmbient)Component->ComponentTags.Add(TEXT("Ambient"));Voices.Add(Component,Volume);}
 return Component;
}
void UMareAudioWorld::UpdateLayers(float DeltaSeconds,UMareSimulation* Sim,FVector Position,bool bRain,bool bNight)
{
 auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));auto Eyes=Hero?Hero->FindComponentByClass<UCameraComponent>():nullptr;
 bUnderwater=Hero && Hero->GetCharacterMovement()->IsSwimming() && Eyes && Eyes->GetComponentLocation().Z<-38;
 IndoorClock-=DeltaSeconds;if(IndoorClock<=0 && Eyes){IndoorClock=.5f;FHitResult Hit;FCollisionQueryParams Query;Query.AddIgnoredActor(Hero);bIndoors=GetWorld()->LineTraceSingleByChannel(Hit,Eyes->GetComponentLocation(),Eyes->GetComponentLocation()+FVector(0,0,350),ECC_Visibility,Query);}
 const float Beach=FMath::Clamp(1.f-(Position.Y+3200.f)/7000.f,.08f,1.f);
 // Music by place and time (Content/Data/audio_zones.json): the zone's track rises inside it and the radio ducks.
 static TSharedPtr<FJsonObject> Zones;
 if(!Zones.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/audio_zones.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Zones);if(!Zones.IsValid())Zones=MakeShared<FJsonObject>();}
 FName ZoneTrack;float ZoneLevel=0;const double Hour=Sim?UMareSimulation::Number(Sim->State,TEXT("minutes"))/60:12;
 const TArray<TSharedPtr<FJsonValue>>* ZoneList=nullptr;const double Fade=FMath::Max(1.,UMareSimulation::Number(Zones,TEXT("fade"),300));
 if(Sim && Zones->TryGetArrayField(TEXT("zones"),ZoneList))for(const auto& V:*ZoneList){const auto Z=V->AsObject();
  const FString Requires=UMareSimulation::String(Z,TEXT("requires"));bool bOwned=Requires.IsEmpty();if(!bOwned)UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(Requires,bOwned);
  const TArray<TSharedPtr<FJsonValue>>* C=nullptr;const TArray<TSharedPtr<FJsonValue>>* H=nullptr;
  if(!bOwned || !Z->TryGetArrayField(TEXT("centre"),C) || C->Num()<2 || !Z->TryGetArrayField(TEXT("hours"),H) || H->Num()!=2)continue;
  if(Hour<(*H)[0]->AsNumber() || Hour>=(*H)[1]->AsNumber())continue;
  const double Dist=FVector::Dist2D(Position,FVector((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),0)),Radius=UMareSimulation::Number(Z,TEXT("radius"));
  if(Dist>=Radius)continue;
  ZoneTrack=FName(UMareSimulation::String(Z,TEXT("track")));ZoneLevel=float(UMareSimulation::Number(Z,TEXT("volume"),.25)*FMath::Clamp((Radius-Dist)/Fade,0.,1.));break;}
 const float Duck=ZoneTrack.IsNone()?1.f:FMath::Lerp(1.f,float(UMareSimulation::Number(Zones,TEXT("radio_duck"),.2)),FMath::Clamp(ZoneLevel/.15f,0.f,1.f));
 for(auto Pair:Loops){const FName Name=Pair.Key;float Target=0;
  if(Name==ZoneTrack)Target=(MasterMix?1.f:GetVolume(TEXT("Master")))*GetVolume(TEXT("Music"))*ZoneLevel*(bIndoors?.8f:1.f);
  // Per-station trim so every track plays at the same loudness (reggae_praia is mastered 3.6 dB softer).
  else if(Name==RadioStation && IsRadioStation(Name))Target=(Name==TEXT("reggae_praia")?1.5f:1.f)*Duck*(MasterMix?1.f:GetVolume(TEXT("Master")))*GetVolume(TEXT("Music"))*(bNight?.22f:.32f)*(bIndoors?.65f:1.f)*(bHomeStereo && HomeStereo?FMath::Clamp(FVector::Dist(Position,HomeStereo->GetComponentLocation())/800.f,.12f,1.f):1.f);
  if(Name==TEXT("ocean_loop"))Target=Gain(true)*Beach*(bIndoors?.1f:.4f);
  // Mix 03/11 (tools/ue58/measure_mix.py): the rain sat 18 dB over the sea and over the music; now ~3 dB above the sea.
  if(Name==TEXT("rain_loop"))Target=Gain(true)*(bRain?(bIndoors?.025f:.08f):0.f);
  if(Name==TEXT("wind_loop"))Target=Gain(true)*(bRain?.16f:.055f)*(bIndoors?.15f:1.f);
  if(Name==TEXT("crickets_loop"))Target=Gain(true)*(bNight && !bRain?.22f:0.f)*(bIndoors?.25f:1.f);
  if(Name==TEXT("leaves_soft"))Target=Gain(true)*(!bRain && Position.Y>-1100?.2f:0.f)*(bIndoors?.2f:1.f);
  if(Name==TEXT("underwater_loop"))Target=Gain(true)*(bUnderwater?.28f:0.f);
  // 04/11 (Sergio: "som de mata fechada na trilha"): the forest past the back of the village and on the summit trail
  // (OpenGameArt CC0 birds + forest ambience), softer at night when the crickets take over, almost gone in the rain.
  if(Name==TEXT("forest_loop"))Target=Gain(true)*.24f*FMath::Clamp((Position.Y-8400.f)/1600.f,0.f,1.f)*(bNight?.35f:1.f)*(bRain?.25f:1.f)*(bIndoors?.2f:1.f);
  auto Component=Pair.Value;if(!IsValid(Component))continue;
  // The silence before the tsunami (UMareSummitWorld): every ambience and the radio fall silent.
  if(auto Summit=GetWorld()->GetSubsystem<UMareSummitWorld>())if(Summit->IsWaveRunning())Target=0;
  if(GetVolume(TEXT("Master"))==0)Target=0;
  Component->SetVolumeMultiplier(FMath::FInterpTo(Component->VolumeMultiplier,Target,DeltaSeconds,3));
  Component->SetLowPassFilterEnabled(bUnderwater);Component->SetLowPassFilterFrequency(bUnderwater?650:18000);
 }
}
void UMareAudioWorld::UpdateEvents(float DeltaSeconds,UMareSimulation* Sim,FVector Position,bool bRain,bool bNight)
{
 auto Hero=UGameplayStatics::GetPlayerCharacter(this,0);auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));
 if(!Hero)return;StepClock-=DeltaSeconds;
 const bool Swimming=Hero->GetCharacterMovement()->IsSwimming();
 if(Swimming!=bWasSwimming){PlayCue(TEXT("swim_splash"),.22f);bWasSwimming=Swimming;}
 if(Swimming && Hero->GetVelocity().Size()>35 && StepClock<=0){PlayCue(TEXT("swim_stroke"),.18f);StepClock=1.1f;}
 if(Hero->GetCharacterMovement()->IsMovingOnGround() && Hero->GetVelocity().Size2D()>45 && StepClock<=0){
  const bool Wood=(Position.X>3500 && Position.X<4150 && Position.Y>-1650 && Position.Y<-900);
  const FString Surface=Wood?TEXT("wood"):Position.Y>900?TEXT("concrete"):TEXT("carpet");
  // The concrete steps were recorded 8 dB softer than the carpet ones (measure_mix.py): even them out per surface.
  const float Trim=Surface==TEXT("concrete")?2.f:Surface==TEXT("wood")?1.25f:1.f;
  PlayCue(FName(FString::Printf(TEXT("footstep_%s_%03d"),*Surface,FMath::RandRange(0,4))),.18f*Trim);StepClock=Hero->GetVelocity().Size2D()>300?.3f:.46f;
 }
 if(Sim->Carry()!=LastCarry){if(!Sim->Carry().IsEmpty())PlayCue(TEXT("kiosk_pickup"),.6f);LastCarry=Sim->Carry();}
 if(Sim->Money()>LastCash+.01)PlayCue(TEXT("kiosk_cash"),.8f);LastCash=Sim->Money();
 const int32 Orders=UMareSimulation::Object(Sim->State,TEXT("ue_orders"))->Values.Num();if(Orders>LastOrders)PlayCue(TEXT("glass"),.15f);LastOrders=Orders;
 if(PC && PC->bPhoneOpen!=bWasPhone){PlayCue(TEXT("swoosh"),.14f);bWasPhone=PC->bPhoneOpen;}
 GullClock-=DeltaSeconds;BirdClock-=DeltaSeconds;ThunderClock-=DeltaSeconds;
 // A calm background (Sergio, 03/11: soft and relaxing, not crowded): birds and gulls now and then over the sea and wind.
 if(!bRain && !bNight && BirdClock<=0){BirdClock=FMath::FRandRange(10.f,22.f);const FVector Trees[]={FVector(4200,1700,500),FVector(5300,3600,500),FVector(3300,-1000,500),FVector(900,-900,500),FVector(-1500,700,500),FVector(6900,3700,600),FVector(8300,1800,600)};
  FVector Nearest=Trees[0];for(auto Tree:Trees)if(FVector::Dist(Position,Tree)<FVector::Dist(Position,Nearest))Nearest=Tree;
  if(FVector::Dist(Position,Nearest)<3500)PlayCue(FMath::RandBool()?TEXT("bird1"):TEXT("bird2"),.035f,&Nearest,true);   // the bird clips are ~25 dB hotter than the gulls'
 }
 if(GullClock<=0){GullClock=FMath::FRandRange(28.f,55.f);FVector Spot=Position+FVector(700,-1200,800);if(!bNight && !bRain && Position.Y<-500){const bool bFirst=FMath::RandBool();PlayCue(bFirst?TEXT("seagull1"):TEXT("seagull2"),bFirst?.3f:.75f,&Spot,true);}}   // seagull2 is recorded 8 dB softer
 if(ThunderClock<=0){ThunderClock=FMath::FRandRange(22.f,45.f);if(bRain && UMareSimulation::String(Sim->State,TEXT("day_event"))==TEXT("tempestade"))PlayCue(TEXT("thunder"),.25f,nullptr,true);}
 const int32 Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60;
 if(LastBell<0)LastBell=Hour;if(Hour!=LastBell){LastBell=Hour;FVector Church(7000,3000,700);if(Hour>=7 && Hour<=21)PlayCue(TEXT("bell"),.2f,&Church,true);}
}
void UMareAudioWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()) || UGameplayStatics::IsGamePaused(this))return;
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;if(!bReady)StartSoundscape(Sim);
 auto Hero=UGameplayStatics::GetPlayerCharacter(this,0);if(!Hero)return;
 const double Minutes=UMareSimulation::Number(Sim->State,TEXT("minutes"));const bool Night=Minutes<360 || Minutes>=1110;
 const bool Rain=UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain");
 UpdateLayers(DeltaSeconds,Sim,Hero->GetActorLocation(),Rain,Night);UpdateEvents(DeltaSeconds,Sim,Hero->GetActorLocation(),Rain,Night);
 for(auto It=Voices.CreateIterator();It;++It){if(!IsValid(It.Key()) || !It.Key()->IsPlaying())It.RemoveCurrent();else{It.Key()->SetVolumeMultiplier(GetVolume(TEXT("Master"))==0?0:It.Value()*Gain(It.Key()->ComponentHasTag(TEXT("Ambient"))));It.Key()->SetLowPassFilterEnabled(bUnderwater);It.Key()->SetLowPassFilterFrequency(bUnderwater?900:18000);if((Rain || Night) && It.Key()->ComponentHasTag(TEXT("Ambient")) && It.Key()->Sound && It.Key()->Sound->GetName().StartsWith(TEXT("bird")))It.Key()->Stop();}}
}
void UMareAudioWorld::Deinitialize(){if(HomeStereo)HomeStereo->Stop();for(auto Pair:Loops)if(IsValid(Pair.Value))Pair.Value->Stop();for(auto Pair:Voices)if(IsValid(Pair.Key))Pair.Key->Stop();Loops.Empty();Voices.Empty();Sounds.Empty();Super::Deinitialize();}
