#include "MareAudioWorld.h"
#include "MareSummitWorld.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareIsland.h"
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
static TSharedPtr<FJsonObject> RadioDefs()
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/radio.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);   // i18n:skip
  if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}
const TArray<FName>& UMareAudioWorld::RadioStations()
{
 // The dial (Content/Data/radio.json): Aloha FM opens it, the CC0 Open Lo-Fi tracks follow, 'off' closes it.
 static TArray<FName> Stations;
 if(Stations.IsEmpty()){const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
  if(RadioDefs()->TryGetArrayField(TEXT("stations"),List))for(const auto& V:*List)Stations.Add(FName(UMareSimulation::String(V->AsObject(),TEXT("id"))));   // i18n:skip
  if(Stations.IsEmpty())Stations={TEXT("radio_havaiana"),TEXT("music_relax"),TEXT("off")};}
 return Stations;
}
int32 UMareAudioWorld::AlwaysLoadedStations(){return int32(UMareSimulation::Number(RadioDefs(),TEXT("always_loaded"),10));}   // i18n:skip
FString UMareAudioWorld::RadioName(FName Station)
{
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(RadioDefs()->TryGetArrayField(TEXT("stations"),List))for(const auto& V:*List)   // i18n:skip
  if(FName(UMareSimulation::String(V->AsObject(),TEXT("id")))==Station)return UMareSimulation::String(V->AsObject(),TEXT("name"));   // i18n:skip
 return TEXT("Desligada");
}
void UMareAudioWorld::PrevRadioStation()
{
 const int32 Index=RadioStations().IndexOfByKey(RadioStation);
 SetRadioStation(RadioStations()[(Index-1+RadioStations().Num())%RadioStations().Num()]);
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
float UMareAudioWorld::LoopLevel(FName Name)const
{
 const UAudioComponent* Component=Name==TEXT("home_stereo")?Stereos.FindRef(TEXT("home")).Get():Loops.FindRef(Name).Get();   // i18n:skip
 return IsValid(Component)?Component->VolumeMultiplier:0.f;
}
void UMareAudioWorld::SetHomeStereo(bool bEnabled,FVector Position){SetStereo(TEXT("home"),bEnabled?FName(TEXT("music_relax")):NAME_None,Position);}
void UMareAudioWorld::SetStereo(FName Id,FName Track,FVector Position)
{
 if(!bReady)return;
 UAudioComponent* Set=Stereos.FindRef(Id).Get();
 // Another track (or off): the old one stops; the new one starts on the set, heard within a few metres.
 if(StereoTracks.FindRef(Id)!=Track){if(IsValid(Set))Set->Stop();Set=nullptr;Stereos.Remove(Id);StereoTracks.Add(Id,Track);
  if(!Track.IsNone())if(auto Wave=Sounds.FindRef(Track)){
   auto Local=NewObject<USoundAttenuation>(this);Local->Attenuation.bAttenuate=true;Local->Attenuation.bSpatialize=true;
   Local->Attenuation.AttenuationShapeExtents=FVector(150);Local->Attenuation.FalloffDistance=650;
   Set=UGameplayStatics::SpawnSoundAtLocation(this,Wave,Position,FRotator::ZeroRotator,.001f,1,0,Local,nullptr,false);
   if(Set){Set->SetUISound(false);Stereos.Add(Id,Set);}}}
 if(Set){Set->SetWorldLocation(Position);Set->SetVolumeMultiplier(!Track.IsNone() && GetVolume(TEXT("Master"))>0?MusicBus()*.24f:0.f);}
}
float UMareAudioWorld::Gain(bool bAmbient)const{return (MasterMix?1.f:GetVolume(TEXT("Master")))*GetVolume(TEXT("Effects"))*(bAmbient?GetVolume(TEXT("Ambient")):1.f);}
void UMareAudioWorld::SetVolume(FName Bus,float Value)
{
 if(!Volumes.Contains(Bus))return;Value=FMath::Clamp(Value,0.f,1.f);Volumes[Bus]=Value;
 GConfig->SetFloat(TEXT("MareAudio"),*Bus.ToString(),Value,GGameUserSettingsIni);GConfig->Flush(false,GGameUserSettingsIni);
 if(Bus==TEXT("Master") && MasterMix)MasterMix->SetSubmixOutputVolume(this,Value);
 ApplyVolumes();
}
// 08/11 (Sergio, demo: the background music could not be changed nor turned off): the sliders live in the options of
// the pause menu, and the loops only followed the buses in Tick, which stops while paused, so nothing changed until
// the game resumed (only an exact zero muted). Now every playing sound is set from its last level right away.
float UMareAudioWorld::MusicBus()const{return (MasterMix?1.f:GetVolume(TEXT("Master")))*GetVolume(TEXT("Music"));}
void UMareAudioWorld::ApplyVolumes()
{
 const bool bMuted=GetVolume(TEXT("Master"))==0;
 for(auto Pair:Stereos)if(IsValid(Pair.Value))Pair.Value->SetVolumeMultiplier(bMuted || StereoTracks.FindRef(Pair.Key).IsNone()?0.f:MusicBus()*.24f);
 for(auto& Voice:Voices)if(IsValid(Voice.Key))Voice.Key->SetVolumeMultiplier(bMuted?0:Voice.Value*Gain(Voice.Key->ComponentHasTag(TEXT("Ambient"))));
 for(auto Pair:Loops)if(IsValid(Pair.Value)){const float* Base=LoopBase.Find(Pair.Key);
  Pair.Value->SetVolumeMultiplier(bMuted || !Base?0.f:*Base*(MusicLoops.Contains(Pair.Key)?MusicBus():Gain(true)));}
}
void UMareAudioWorld::StartSoundscape(UMareSimulation* Sim)
{
 MasterMix=Cast<USoundSubmix>(GetDefault<UAudioSettings>()->MasterSubmix.TryLoad());
 if(MasterMix)MasterMix->SetSubmixOutputVolume(this,GetVolume(TEXT("Master")));
 FString Text;TArray<TSharedPtr<FJsonValue>> Catalog;
 if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/audio.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Catalog);
 for(auto Item:Catalog){auto Row=Item->AsObject();const FString Name=UMareSimulation::String(Row,TEXT("id"));if(auto Wave=LoadObject<USoundWave>(nullptr,*UMareSimulation::String(Row,TEXT("path")))){Sounds.Add(FName(Name),Wave);
  const FString Group=UMareSimulation::String(Row,TEXT("group"));if(!Group.IsEmpty()){Groups.FindOrAdd(Group).Add(FName(Name));GroupVolume.Add(Group,UMareSimulation::Number(Row,TEXT("volume")));}}}
 // The always-loaded stations play silently from the start (no gap when switching); the rest stream only while tuned.
 TArray<FName> LoopNames;for(int32 I=0;I<RadioStations().Num() && I<AlwaysLoadedStations();++I)LoopNames.Add(RadioStations()[I]);LoopNames.Remove(TEXT("off"));
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
 // 08/11 (island all round): distances to the nearest coast, read as the old bay's y (MareIsland::CoastY).
 const float CoastY=MareIsland::CoastY(Position.X,Position.Y);
 const float Beach=FMath::Clamp(1.f-(CoastY+3200.f)/7000.f,.08f,1.f);
 // The forest: north of the village as before, and now everywhere inland outside the village (mare_island.forest).
 const bool InVillage=Position.X>-15000.f && Position.X<20000.f && Position.Y<12000.f;
 // 08/11: only by the distance inland (the old "north of y 84 m" rule made the new north beaches woods: no sea there).
 const float Woods=InVillage?0.f:FMath::Clamp((-MareIsland::ShoreDistance(Position.X,Position.Y)-4500.f)/2500.f,0.f,1.f);
 // 08/11 (Sergio: "somente ambiente noturno na trilha à noite, como grilos"): in the island forest at night the music
 // and the sea step back and the night takes over (crickets up, the day birds of the forest loop silent).
 const float NightWoods=bNight?Woods:0.f;
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
 // Near a radio set that is playing, the background radio steps back.
 float StereoDuck=1.f;for(auto Pair:Stereos)if(IsValid(Pair.Value) && !StereoTracks.FindRef(Pair.Key).IsNone())StereoDuck=FMath::Min(StereoDuck,FMath::Clamp(FVector::Dist(Position,Pair.Value->GetComponentLocation())/800.f,.12f,1.f));
 // A station past the always-loaded ones: start it when tuned, drop it once faded out after another is chosen.
 if(IsRadioStation(RadioStation) && !Loops.Contains(RadioStation))if(auto Wave=Sounds.FindRef(RadioStation))
  if(auto Component=UGameplayStatics::SpawnSound2D(this,Wave,.001f,1,0,nullptr,false,false)){Component->SetUISound(false);Loops.Add(RadioStation,Component);}
 {TArray<FName> Drop;const int32 Kept=AlwaysLoadedStations();
  for(auto Pair:Loops){const int32 Index=RadioStations().IndexOfByKey(Pair.Key);
   if(Index>=Kept && Pair.Key!=RadioStation && IsValid(Pair.Value) && Pair.Value->VolumeMultiplier<=.002f){Pair.Value->Stop();Drop.Add(Pair.Key);}}
  for(FName Name:Drop)Loops.Remove(Name);}
 for(auto Pair:Loops){const FName Name=Pair.Key;float Target=0;bool bMusic=false;
  // Base level without the bus volumes (kept in LoopBase so the options can apply a new volume while paused).
  if(Name==ZoneTrack){bMusic=true;Target=ZoneLevel*(bIndoors?.8f:1.f)*(1.f-NightWoods);}
  // Per-station trim so every track plays at the same loudness (reggae_praia is mastered 3.6 dB softer).
  else if(Name==RadioStation && IsRadioStation(Name)){bMusic=true;Target=(Name==TEXT("reggae_praia")?1.5f:1.f)*Duck*(bNight?.22f:.32f)*(bIndoors?.65f:1.f)*StereoDuck*(1.f-NightWoods);}
  else if(IsRadioStation(Name))bMusic=true;
  if(Name==TEXT("ocean_loop"))Target=Beach*(bIndoors?.1f:.4f)*(1.f-.7f*NightWoods);
  // Mix 03/11 (tools/ue58/measure_mix.py): the rain sat 18 dB over the sea and over the music; now ~3 dB above the sea.
  if(Name==TEXT("rain_loop"))Target=(bRain?(bIndoors?.025f:.08f):0.f);
  if(Name==TEXT("wind_loop"))Target=(bRain?.16f:.055f)*(bIndoors?.15f:1.f);
  if(Name==TEXT("crickets_loop"))Target=(bNight && !bRain?.22f+.12f*NightWoods:0.f)*(bIndoors?.25f:1.f);
  if(Name==TEXT("leaves_soft"))Target=(!bRain && CoastY>-1100?.2f:0.f)*(bIndoors?.2f:1.f);
  if(Name==TEXT("underwater_loop"))Target=(bUnderwater?.28f:0.f);
  // 04/11 (Sergio: "som de mata fechada na trilha"): the forest past the back of the village and on the summit trail
  // (OpenGameArt CC0 birds + forest ambience), softer at night when the crickets take over, almost gone in the rain.
  if(Name==TEXT("forest_loop"))Target=.24f*Woods*(bNight?.08f:1.f)*(bRain?.25f:1.f)*(bIndoors?.2f:1.f);
  auto Component=Pair.Value;if(!IsValid(Component))continue;
  // The silence before the tsunami (UMareSummitWorld): every ambience and the radio fall silent.
  if(auto Summit=GetWorld()->GetSubsystem<UMareSummitWorld>())if(Summit->IsWaveRunning())Target=0;
  LoopBase.Add(Name,Target);if(bMusic)MusicLoops.Add(Name);else MusicLoops.Remove(Name);
  Target*=bMusic?MusicBus():Gain(true);
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
  const FString Surface=Wood?TEXT("wood"):(Position.Y>900 && Position.Y<12000 && Position.X>-15000 && Position.X<20000)?TEXT("concrete"):TEXT("carpet");   // village streets; the island ground is soft
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
 if(GullClock<=0){GullClock=FMath::FRandRange(28.f,55.f);FVector Spot=Position+FVector(700,-1200,800);if(!bNight && !bRain && MareIsland::CoastY(Position.X,Position.Y)<-500){const bool bFirst=FMath::RandBool();PlayCue(bFirst?TEXT("seagull1"):TEXT("seagull2"),bFirst?.3f:.75f,&Spot,true);}}   // seagull2 is recorded 8 dB softer
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
 // 08/11: the tsunami omen is a dry storm (no rain on screen), so no rain sound either; the thunder stays.
 const auto Summit=GetWorld()->GetSubsystem<UMareSummitWorld>();
 const bool Rain=UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain") && !(Summit && Summit->GloomTarget()>0.f);
 UpdateLayers(DeltaSeconds,Sim,Hero->GetActorLocation(),Rain,Night);UpdateEvents(DeltaSeconds,Sim,Hero->GetActorLocation(),Rain,Night);
 for(auto It=Voices.CreateIterator();It;++It){if(!IsValid(It.Key()) || !It.Key()->IsPlaying())It.RemoveCurrent();else{It.Key()->SetVolumeMultiplier(GetVolume(TEXT("Master"))==0?0:It.Value()*Gain(It.Key()->ComponentHasTag(TEXT("Ambient"))));It.Key()->SetLowPassFilterEnabled(bUnderwater);It.Key()->SetLowPassFilterFrequency(bUnderwater?900:18000);if((Rain || Night) && It.Key()->ComponentHasTag(TEXT("Ambient")) && It.Key()->Sound && It.Key()->Sound->GetName().StartsWith(TEXT("bird")))It.Key()->Stop();}}
}
void UMareAudioWorld::Deinitialize(){for(auto Pair:Stereos)if(IsValid(Pair.Value))Pair.Value->Stop();Stereos.Empty();for(auto Pair:Loops)if(IsValid(Pair.Value))Pair.Value->Stop();for(auto Pair:Voices)if(IsValid(Pair.Key))Pair.Key->Stop();Loops.Empty();Voices.Empty();Sounds.Empty();Super::Deinitialize();}
