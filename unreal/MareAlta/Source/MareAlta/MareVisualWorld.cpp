#include "MareVisualWorld.h"
#include "Components/RectLightComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Engine/PointLight.h"
#include "Engine/StaticMesh.h"
#include "Dom/JsonObject.h"
#include "Misc/Paths.h"
#include "MareSummitWorld.h"
#include "MareMarineWorld.h"
#include "MareLoc.h"
#include "MareSimulation.h"
#include "MareIsland.h"
#include "MareGame.h"
#include "MareServiceTarget.h"
#include "Engine/GameInstance.h"
#include "Engine/Light.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/LightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "EngineUtils.h"
#include "Engine/TextRenderActor.h"
#include "Components/TextRenderComponent.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Components/PointLightComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/CollisionProfile.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "HAL/IConsoleManager.h"
#include "Components/LocalLightComponent.h"
#include "UObject/UObjectIterator.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
// 04/11 (Sergio: "precisa ficar mais escuro a noite"): extra stops taken off the night exposure.
// 06/11 (CHECKLIST 0, the house at night "clara e alaranjada demais" while the suite and lobby were black): the house had no
// interior volume, so it took the outdoor night eye (EV100 -1.9..-0.9, made for moonlight), which blew 38 cd lamps up to
// daylight; the interiors with a volume used EV 4.4..5.2 and were nearly black. One night eye for every room (house included).
static TAutoConsoleVariable<float> CVarMareInteriorNightEV(TEXT("mare.InteriorNightEV"),2.6f,TEXT("Night EV100 floor of the eye inside the MareInterior volumes (the ceiling is +0.8); lower = brighter rooms."));
// 08/11: in the island forest at night (no lamp in view) the eye opened to the -1.9 floor and the woods looked like day;
// the village keeps its lamps in view and sits near the -0.9 top of the night range.
static TAutoConsoleVariable<float> CVarMareNightMinEV(TEXT("mare.NightMinEV"),-1.9f,TEXT("Lowest outdoor exposure (EV100) at night: how far the eye may open where no light is in view (the night top stays -0.9)."));
static TAutoConsoleVariable<float> CVarMareNightDarken(TEXT("mare.NightDarken"),1.3f,TEXT("Stops of exposure removed at night (0 = old night)"));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomSun(TEXT("mare.GloomSun"),.45f,TEXT("Tsunami storm sky: sun intensity kept (0..1)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomEV(TEXT("mare.GloomEV"),-.45f,TEXT("Tsunami storm sky: exposure bias."));   // i18n:skip
// 10/11 (Sergio on the trail: "muito claras", "sem sombras"): under the canopy the eye opened as wide as on the beach
// (daylight EV100 5..14) and the shaded woods came out as bright as a clearing. Measured on the trail: -0.7 stop reads
// as shade with the sun spots kept; -1.2 lost the floor in the dark.
static TAutoConsoleVariable<float> CVarMareForestEV(TEXT("mare.ForestEV"),-.7f,TEXT("Exposure bias by day under a dense forest canopy (0 = same as in the open)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomCover(TEXT("mare.GloomCover"),.6f,TEXT("Tsunami storm sky: cloud coverage."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomDensity(TEXT("mare.GloomDensity"),.03f,TEXT("Tsunami storm sky: cloud density."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomRayleigh(TEXT("mare.GloomRayleigh"),.006f,TEXT("Tsunami storm sky: Rayleigh scattering (less = less blue)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomMie(TEXT("mare.GloomMie"),.12f,TEXT("Tsunami storm sky: Mie scattering (grey haze)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareGloomStorm(TEXT("mare.GloomStorm"),0.f,TEXT("Tsunami storm sky: StormClouds of the volumetric clouds."));   // i18n:skip

static TAutoConsoleVariable<float> CVarMareBounceLightReach(TEXT("mare.BounceLightReach"),1.f,TEXT("Draw distance of the bounce (fill) lights, times mare.LightDrawDistance (04/11: x2.5 cost the beach 4 FPS)."));
static TAutoConsoleVariable<float> CVarMareLightShadowMinRadius(TEXT("mare.LightShadowMinRadius"),1000.f,TEXT("Local lights with a smaller attenuation radius (cm) cast no shadow (04/11: 99 of 134 lights cast shadows; under 10 m off = kiosk 56 -> 61 FPS); 0 = keep the authored shadows."));
// 08/11 (bench, village at night: 19 lights lit, 1124 shadow draw calls, lights 2.6 ms + shadows 1.1 ms of GPU; all
// local lights off = 58 -> 66 FPS): only the nearest few lamps cast shadows, the others light without one.
static TAutoConsoleVariable<int32> CVarMareLightShadowBudget(TEXT("mare.LightShadowBudget"),4,TEXT("At most this many local lights cast shadows, the nearest to the camera within mare.LightShadowReach (0 = no budget: every eligible light keeps its shadow)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareLightShadowReach(TEXT("mare.LightShadowReach"),2500.f,TEXT("Local lights farther than this from the camera (cm) cast no shadow (with mare.LightShadowBudget)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareLightDrawDistance(TEXT("mare.LightDrawDistance"),3000.f,TEXT("Local lights (interiors, bounce, lamps, shops) fade out beyond this distance from the camera (cm), with a 15 m fade (04/11 EXE: with all local lights off the beach went 46 -> 56 FPS and the kiosk 49 -> 63: about 150 lights of the whole map were drawn every frame, day included; 50 m gave beach 53, 30 m 59). 0 = never culled; set on lights that have no distance of their own."));

static TAutoConsoleVariable<int32> CVarMareWalkTest(TEXT("mare.WalkTest"),0,TEXT("QA: the player walks straight ahead (footprint capture)."));
static TAutoConsoleVariable<int32> CVarMareWeather(TEXT("mare.Weather"),0,TEXT("QA weather override: 0 = today's weather, 1 = clear, 2 = rain, 3 = storm, 4 = rough sea without rain."));

TStatId UMareVisualWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareVisualWorld,STATGROUP_Tickables);}
bool UMareVisualWorld::UnlockMatches(const TSharedPtr<FJsonObject>& Owned,const FString& Spec)
{
 TArray<FString> Terms;Spec.ParseIntoArray(Terms,TEXT(","));
 for(FString Term:Terms){Term.TrimStartAndEndInline();const bool bNot=Term.StartsWith(TEXT("!"));if(bNot)Term.RightChopInline(1);
  bool bOwned=false;if(Owned.IsValid())Owned->TryGetBoolField(Term,bOwned);if(bOwned==bNot)return false;}
 return true;
}
static TAutoConsoleVariable<float> CVarMareKioskDayLight(TEXT("mare.KioskDayLight"),25.f,TEXT("Kiosk work lights by day: multiple of their night candela (they must read against the daylight exposure)."));   // i18n:skip
void UMareVisualWorld::BuildLamps()
{
 // Light sources exported from Godot (their glow materials were lost): mesh, glass centre above the
 // pivot (cm), candela at full night, reach (cm), colour temperature (K).
 struct FKind{const TCHAR* Mesh;float Up,Candela,Radius,Kelvin;bool bDown=false;};
 static const FKind Kinds[]={{TEXT("World_1392"),40,150,1900,2900},{TEXT("World_2205"),40,150,1900,2900},{TEXT("World_0687"),9,32,800,2700},
  {TEXT("World_0515"),9,32,800,2700},{TEXT("World_0138"),2,30,700,9000},
  // 05/11 (Sergio: "a luz precisa vir das lâmpadas", the kiosk and the house looked lit by the furniture): the light
  // of a room comes from its fixtures, with shadows. Kiosk lantern (was 12 cd, no shadow), the kiosk's rattan
  // pendants, the house's oil lamp on the nightstand.
  {TEXT("World_0199"),19,90,950,2500},{TEXT("World_1211"),-15,70,900,2600,true},{TEXT("World_1229"),-15,45,800,2600,true},{TEXT("World_0937"),12,22,520,1900},
  // The house ceiling fan has the room's light under it. 06/11 (Sergio: the house at night was "clara e alaranjada
  // demais"): neutral warm-white 4000 K like a home LED, a little dimmer.
  {TEXT("World_0960"),-45,32,750,4000,true},
  // 06/11 (CHECKLIST 0: "luz sem luminária" in the Grand Hotel lobby): the ten ceiling lamps of the lobby light it (the six
  // bare 2500 cd lights of mare_hotel_lobby.py were removed). Plain static mesh actors, matched below like the instances.
  {TEXT("modern_ceiling_lamp_011"),40,250,1100,3500,true},
  // 10/11 (demo simulation: the kiosk's tiki torches stood dark at night): the flame mesh of each torch (kiosk, hotel
  // pool terrace) lights the sand around it, fire-coloured; the flame itself glows through M_TorchFlame (mare_torch.py).
  {TEXT("World_1273"),20,38,620,1900}};
 LampHolder=GetWorld()->SpawnActor<AActor>();if(!LampHolder)return;
 LampHolder->SetRootComponent(NewObject<USceneComponent>(LampHolder,TEXT("LampRoot")));LampHolder->GetRootComponent()->RegisterComponent();
 // Fixtures added where a room had light but no lamp (Content/Data/lighting.json).
 TSet<AActor*> Fixtures;
 {FString Text;TSharedPtr<FJsonObject> Defs;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/lighting.json")));
  if(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs) && Defs.IsValid()){const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
   if(Defs->TryGetArrayField(TEXT("fixtures"),List))for(const auto& V:*List){const auto F=V->AsObject();const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
    auto Mesh=LoadObject<UStaticMesh>(nullptr,*F->GetStringField(TEXT("mesh")));if(!Mesh || !F->TryGetArrayField(TEXT("at"),At) || At->Num()!=3)continue;
    const FVector P((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto Fix=GetWorld()->SpawnActor<AStaticMeshActor>(P,FRotator(0,F->GetNumberField(TEXT("yaw")),0),SP);if(!Fix)continue;Fixtures.Add(Fix);
    Fix->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);Fix->GetStaticMeshComponent()->SetStaticMesh(Mesh);Fix->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // The bulb sits inside the shade: a shade casting shadows kept almost all of its own light in (the suite was dark).
    Fix->GetStaticMeshComponent()->SetCastShadow(false);
    // 05/11 (Sergio: "a lâmpada precisa estar virada para baixo"): a ceiling lamp throws its light down (a spot under
    // the shade); a faint point light keeps a little glow on the ceiling around it (added below at 15%).
    auto Light=NewObject<USpotLightComponent>(LampHolder);Light->SetupAttachment(LampHolder->GetRootComponent());Light->RegisterComponent();
    Light->SetInnerConeAngle(38.f);Light->SetOuterConeAngle(68.f);Light->SetWorldRotation(FRotator(-90,0,0));
    Light->SetWorldLocation(P+FVector(0,0,F->GetNumberField(TEXT("light_up"))));Light->SetIntensityUnits(ELightUnits::Candelas);Light->SetIntensity(0);
    Light->SetAttenuationRadius(F->GetNumberField(TEXT("radius")));Light->SetUseTemperature(true);Light->SetTemperature(F->GetNumberField(TEXT("kelvin")));
    Light->SetCastShadows(true);Light->ContactShadowLength=.08f;Light->SetSourceRadius(6);Light->SetVisibility(false);
    FString Unlock;F->TryGetStringField(TEXT("unlock"),Unlock);if(!Unlock.IsEmpty())Fix->SetActorHiddenInGame(true);
    bool bWorkFix=false;F->TryGetBoolField(TEXT("work"),bWorkFix);   // i18n:skip
    Lamps.Add({Light,Fix,float(F->GetNumberField(TEXT("candela"))),Unlock,bWorkFix});
    auto Glow=NewObject<UPointLightComponent>(LampHolder);Glow->SetupAttachment(LampHolder->GetRootComponent());Glow->RegisterComponent();
    Glow->SetWorldLocation(Light->GetComponentLocation()+FVector(0,0,20));Glow->SetIntensityUnits(ELightUnits::Candelas);Glow->SetIntensity(0);
    Glow->SetAttenuationRadius(F->GetNumberField(TEXT("radius"))*.6f);Glow->SetUseTemperature(true);Glow->SetTemperature(F->GetNumberField(TEXT("kelvin")));
    Glow->SetCastShadows(false);Glow->SetVisibility(false);double GlowShare=.15;F->TryGetNumberField(TEXT("glow"),GlowShare);Lamps.Add({Glow,Fix,float(F->GetNumberField(TEXT("candela"))*GlowShare),Unlock,bWorkFix});}}}   // i18n:skip
 for(TActorIterator<AActor> It(GetWorld());It;++It){if(*It==LampHolder || Fixtures.Contains(*It))continue;
  TArray<UStaticMeshComponent*> Parts;It->GetComponents(Parts);
  for(auto Part:Parts){if(!Part->GetStaticMesh())continue;const FString Mesh=Part->GetStaticMesh()->GetName();
   const FKind* Kind=nullptr;for(const auto& K:Kinds)if(Mesh==K.Mesh)Kind=&K;if(!Kind)continue;
   auto Instanced=Cast<UInstancedStaticMeshComponent>(Part);
   for(int32 I=0;I<(Instanced?Instanced->GetInstanceCount():1);++I){FTransform T=Part->GetComponentTransform();if(Instanced)Instanced->GetInstanceTransform(I,T,true);
    UPointLightComponent* Light=Kind->bDown?NewObject<USpotLightComponent>(LampHolder):NewObject<UPointLightComponent>(LampHolder);
    Light->SetupAttachment(LampHolder->GetRootComponent());Light->RegisterComponent();
    if(auto Spot=Cast<USpotLightComponent>(Light)){Spot->SetInnerConeAngle(40.f);Spot->SetOuterConeAngle(70.f);Spot->SetWorldRotation(FRotator(-90,0,0));}
    Light->SetWorldLocation(T.TransformPosition(FVector(0,0,Kind->Up)));Light->SetIntensityUnits(ELightUnits::Candelas);Light->SetIntensity(0);
    Light->SetAttenuationRadius(Kind->Radius);Light->SetUseTemperature(true);Light->SetTemperature(Kind->Kelvin);
    // 09/11 (night photo tour: the water round the pier glowed neon green): the sea's blue-green scattering under the warm
    // 2900 K posts turned green; the pier and the beach posts over the water burn a cooler 4300 K.
    {const FVector At=T.GetLocation();if(At.Y<-2400 && At.X>5600 && Kind->Radius>=1500)Light->SetTemperature(4300);}
    // Street lamps and lanterns cast shadows at night (03/11, Sergio: "nada tem sombra"); the small lamps only a contact shadow.
    Light->SetCastShadows(Kind->Radius>=500);Light->ContactShadowLength=.08f;
    // 07/11 (Sergio: "escuro, precisa ter lâmpada de luz dentro do quiosque"): the kiosk's pendants and lantern are work
    // lights, on during the opening hours by day too.
    const bool bWork=Mesh==TEXT("World_1211") || Mesh==TEXT("World_1229") || Mesh==TEXT("World_0199");
    Light->SetSourceRadius(4);Light->SetVisibility(false);Lamps.Add({Light,*It,Kind->Candela,FString(),bWork});
    // A hanging ceiling lamp also lights the ceiling around it a little (like the lighting.json fixtures).
    if(Kind->bDown && Kind->Up>0){auto Glow=NewObject<UPointLightComponent>(LampHolder);Glow->SetupAttachment(LampHolder->GetRootComponent());Glow->RegisterComponent();
     Glow->SetWorldLocation(Light->GetComponentLocation()+FVector(0,0,20));Glow->SetIntensityUnits(ELightUnits::Candelas);Glow->SetIntensity(0);
     Glow->SetAttenuationRadius(Kind->Radius*.6f);Glow->SetUseTemperature(true);Glow->SetTemperature(Kind->Kelvin);Glow->SetCastShadows(false);Glow->SetVisibility(false);
     Lamps.Add({Glow,*It,Kind->Candela*.15f,FString(),bWork});}}
  }
 }
}
void UMareVisualWorld::RefreshExpansions()
{
 auto World=GetWorld();
 if(!World || !World->IsGameWorld() || !World->GetGameInstance())return;
 auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const auto Definitions=UMareSimulation::Object(Sim->Definitions,TEXT("expansions"));
 const auto Businesses=UMareSimulation::Object(Sim->Definitions,TEXT("businesses"));
 if(!bRegionsIndexed){
  for(TActorIterator<AActor> It(World);It;++It)for(FName Tag:It->Tags){
   const FString Name=Tag.ToString();
   const FString Id=Name.StartsWith(TEXT("Region_"))?Name.RightChop(7):Name.StartsWith(TEXT("Lot_"))?Name.RightChop(4):TEXT("");
   if(Definitions->HasField(Id) || (Id.StartsWith(TEXT("Biz_")) && Businesses->HasField(Id.RightChop(4))))ExpansionRegions.FindOrAdd(Tag).Add(*It);
  }
  bRegionsIndexed=true;
 }
 const auto Unlocked=UMareSimulation::Object(Sim->State,TEXT("unlocked"));
 for(const auto& Region:ExpansionRegions){
  const FString Tag=Region.Key.ToString();const bool bLot=Tag.StartsWith(TEXT("Lot_"));const FString Id=Tag.RightChop(bLot?4:7);
  bool bOwned=false;
  if(Id.StartsWith(TEXT("Biz_")))bOwned=UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("biz")),Id.RightChop(4)),TEXT("lvl"))>0;
  else Unlocked->TryGetBoolField(Id,bOwned);
  const bool bVisible=bLot?!bOwned:bOwned;
  const bool* Previous=RegionVisibility.Find(Region.Key);if(Previous && *Previous==bVisible)continue;
  for(const auto& Entry:Region.Value)if(auto Actor=Entry.Get()){
   Actor->SetActorHiddenInGame(!bVisible);Actor->SetActorEnableCollision(bVisible);
  }
  RegionVisibility.Add(Region.Key,bVisible);
 }
}
static TAutoConsoleVariable<float> CVarMareMoonLux(TEXT("mare.MoonLux"),1.1f,TEXT("Full moon light at night (lux)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareStars(TEXT("mare.Stars"),1.f,TEXT("Brightness of the night sky (stars, Milky Way, aurora)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareAurora(TEXT("mare.Aurora"),1.f,TEXT("Aurora strength in the night sky (0 = none)."));   // i18n:skip
static TAutoConsoleVariable<float> CVarMareMoonGlow(TEXT("mare.MoonGlow"),1.f,TEXT("Brightness of the moon disc in the sky."));   // i18n:skip
/** 10/11 (event photos: "Noite de lua cheia" looked like any night, the moon is full every night since 09/11): on the
 *  "lua" event day the moon is a super moon, larger, brighter and lighting the beach more. 0..1. */
static float MareSuperMoon(const UMareSimulation* Sim){return Sim && UMareSimulation::String(Sim->State,TEXT("day_event"))==TEXT("lua")?1.f:0.f;}   // i18n:skip
/** The full moon's light direction at a game hour: opposite the sun (same arc, half a day apart). */
static FRotator MareMoonRotation(float Hour){const float Solar=FMath::Sin((Hour-6.f)/12.f*PI);return FRotator(Solar*58.f,-65.f+(Hour-12.f)*12.f+180.f,0);}
void UMareVisualWorld::UpdateMoonDisc()
{
 // Every frame, so the disc stays put in the sky while the camera moves: far along the moon's direction (30 km, beyond
 // the island and the sea, inside the infinite far plane), facing the camera, ~2 degrees wide (3.5 with the halo).
 if(!MoonDisc){for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareMoonDisc"))){MoonDisc=*It;break;}
  if(!MoonDisc)return;
  MoonDisc->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
  // No collision at all: the dome is a sphere round the camera, and with the engine sphere's collision it swallowed
  // every aim trace (TV, sofa, bed, people) in the packaged QA (09/11).
  auto NoCollision=[](AStaticMeshActor* A){A->SetActorEnableCollision(false);A->GetStaticMeshComponent()->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
   A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);A->GetStaticMeshComponent()->SetGenerateOverlapEvents(false);};
  NoCollision(MoonDisc);
  MoonMaterial=MoonDisc->GetStaticMeshComponent()->CreateDynamicMaterialInstance(0);
  for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareStarDome"))){StarDome=*It;break;}
  if(StarDome){NoCollision(StarDome);StarDome->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);StarMaterial=StarDome->GetStaticMeshComponent()->CreateDynamicMaterialInstance(0);}}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();APlayerCameraManager* Cam=UGameplayStatics::GetPlayerCameraManager(this,0);
 if(!Sim || !Cam)return;
 const float Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.f;
 const float Solar=FMath::Sin((Hour-6.f)/12.f*PI);const float Day=FMath::SmoothStep(-.04f,.18f,Solar);
 // 09/11 (Sergio: "coloque nuvens de estrela no céu a noite, tipo aurora boreal"): the night sky dome around the camera
 // (28 km, inside the moon's 30 km): stars, the Milky Way and an aurora over the sea, fading in at dusk, gone in rain.
 if(StarDome){const float Night=FMath::Clamp((1.f-FMath::SmoothStep(-.1f,.12f,Solar))*(1.f-.95f*RainNow)*(1.f-GloomNow),0.f,1.f);
  const bool bOff=Night<.01f;if(StarDome->IsHidden()!=bOff)StarDome->SetActorHiddenInGame(bOff);
  if(!bOff){StarDome->SetActorLocation(Cam->GetCameraLocation());StarDome->SetActorScale3D(FVector(2800000.0/50.0));
   if(StarMaterial){StarMaterial->SetScalarParameterValue(TEXT("Night"),Night*CVarMareStars.GetValueOnGameThread());StarMaterial->SetScalarParameterValue(TEXT("Aurora"),CVarMareAurora.GetValueOnGameThread());}}}   // i18n:skip
 const FVector Up=-MareMoonRotation(Hour).Vector();
 const float Show=FMath::Clamp((1.f-Day)*FMath::SmoothStep(-.03f,.04f,float(Up.Z))*(1.f-.9f*RainNow)*(1.f-GloomNow),0.f,1.f);
 const bool bHide=Show<.01f;if(MoonDisc->IsHidden()!=bHide)MoonDisc->SetActorHiddenInGame(bHide);
 if(bHide)return;
 constexpr double Distance=3000000.0;
 MoonDisc->SetActorLocationAndRotation(Cam->GetCameraLocation()+Up*Distance,FRotationMatrix::MakeFromZY(-Up,FVector::UpVector).Rotator());
 const float Super=MareSuperMoon(Sim);
 MoonDisc->SetActorScale3D(FVector(Distance*.0611*2.2*(1.f+.5f*Super)/100.0));   // 1 degree read too small next to the trees: ~2.2
 if(MoonMaterial)MoonMaterial->SetScalarParameterValue(TEXT("Bright"),Show*CVarMareMoonGlow.GetValueOnGameThread()*(1.f+.7f*Super));   // i18n:skip
}
void UMareVisualWorld::UpdateCanopy(float DeltaSeconds)
{
 // The trees of the woods (mare_mountains.TREES: no palms, rocks or shrubs) in the island forest and the mountain woods.
 if(!bCanopyIndexed){bCanopyIndexed=true;
  static const TCHAR* TreeMeshes[]={TEXT("World_0504"),TEXT("World_0505"),TEXT("World_1206"),TEXT("tree_small_02"),TEXT("jacaranda_tree")};
  for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareIslandForest")) || It->ActorHasTag(TEXT("MareMountainVegetation"))){
   TArray<UInstancedStaticMeshComponent*> Comps;It->GetComponents(Comps);
   for(auto C:Comps)if(C && C->GetStaticMesh()){const FString Name=C->GetStaticMesh()->GetName();
    for(const TCHAR* Tree:TreeMeshes)if(Name.StartsWith(Tree)){CanopyTrees.Add(C);break;}}}
  UE_LOG(LogTemp,Display,TEXT("MARE_CANOPY tree_components=%d"),CanopyTrees.Num());}
 CanopyClock-=DeltaSeconds;
 if(CanopyClock<=0.f){CanopyClock=.5f;
  const APlayerCameraManager* Cam=UGameplayStatics::GetPlayerCameraManager(GetWorld(),0);
  int32 Count=0;
  if(Cam){const FVector At=Cam->GetCameraLocation();
   for(const auto& C:CanopyTrees)if(C.IsValid())Count+=C->GetInstancesOverlappingSphere(At,1200.f,true).Num();}
  // Woods are ~1 tree per 40 m2 (step 6.2 m): ~10 inside 12 m; clearings, trail edges and the open slopes fewer.
  const float Before=CanopyTarget;CanopyTarget=FMath::SmoothStep(2.f,8.f,float(Count));
  if((Before>=.5f)!=(CanopyTarget>=.5f))UE_LOG(LogTemp,Display,TEXT("MARE_CANOPY under=%d trees=%d"),CanopyTarget>=.5f?1:0,Count);}
 CanopyNow=FMath::FInterpTo(CanopyNow,CanopyTarget,DeltaSeconds,.8f);
}

void UMareVisualWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()))return;
 // Every frame: the weather easing, the rain curtains following the camera and the footprints; the rest of the
 // scene (sun, lamps, signs) refreshes every 2 s below.
 if(auto WeatherSim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>())UpdateWeather(DeltaSeconds,WeatherSim);
 UpdateFootprints();
 UpdateCanopy(DeltaSeconds);
 UpdateMoonDisc();
 ShadowClock-=DeltaSeconds;if(ShadowClock<=0){ShadowClock=.5f;BudgetLightShadows();}
 // While the tsunami sky changes the light refreshes every 0.25 s, so the darkening is smooth, not in 2 s steps.
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=GloomNow>.001f && GloomNow<.99f?.25f:2.f;
 RefreshExpansions();
 AddGlassCompanions();
 CullLocalLights();
 if(!Sun){for(TActorIterator<ALight> It(GetWorld());It;++It){if(It->ActorHasTag(TEXT("MareSun")))Sun=*It;if(It->ActorHasTag(TEXT("MareMoon")))Moon=*It;if(It->ActorHasTag(TEXT("MarePractical")))Practical.AddUnique(*It);
   if(It->ActorHasTag(TEXT("MareSuitePart")))if(auto Bare=Cast<APointLight>(*It))BareLights.Add(Bare);}
  for(TActorIterator<AExponentialHeightFog> It(GetWorld());It;++It)Fog=*It;
  for(TActorIterator<APostProcessVolume> It(GetWorld());It;++It)if(It->bUnbound){Exposure=*It;break;}
  for(TActorIterator<APostProcessVolume> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareInterior")))Interiors.Add(*It);
  for(TActorIterator<ASkyLight> It(GetWorld());It;++It){Sky=*It;break;}
  BuildLamps();
  for(TActorIterator<ATextRenderActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareText"))){Signs.Add(*It);SignSource.Add(*It,It->GetTextRender()->Text.ToString());
   if(It->ActorHasTag(TEXT("MareStatusSign"))){auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(It->GetActorLocation(),FRotator::ZeroRotator);
    Target->Action=TEXT("KioskSign");Target->Label=TEXT("Placa do quiosque");Target->Reach=330;Target->OcclusionTolerance=100;Target->SetOwner(*It);}
  }
  // Grand Hotel reception desk inside the opened ground floor (tools/ue58/hotel_lobby_shell.py).
  if(!Reception){Reception=GetWorld()->SpawnActor<AMareServiceTarget>(FVector(-1390,6470,160),FRotator::ZeroRotator);
   Reception->Action=TEXT("HotelReception");Reception->Label=TEXT("Recepção do Grand Hotel");Reception->Reach=280;Reception->OcclusionTolerance=60;}}
 if(Reception){bool bHotel=false;UMareSimulation::Object(GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>()->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);Reception->SetActorHiddenInGame(!bHotel);
  // Suite on the 3rd floor (tools/ue58/gen_suite.py, origin -2800,6342,851): arrival points face into the room.
  if(Elevators.IsEmpty()){auto Make=[this](FVector At,FVector To,float Yaw,int32 Index,const TCHAR* Label){auto T=GetWorld()->SpawnActor<AMareServiceTarget>(At,FRotator::ZeroRotator);
    T->Action=TEXT("Elevator");T->Label=Label;T->Reach=260;T->OcclusionTolerance=60;T->TeleportTo=To;T->TeleportYaw=Yaw;T->DataIndex=Index;Elevators.Add(T);};
   Make(FVector(-2600,6862,195),FVector(-1736,6800,943),-90,2,TEXT("Elevador · subir aos quartos 302 e 303"));
   Make(FVector(-2900,6862,195),FVector(-2800,6690,943),-90,1,TEXT("Elevador · subir para a suíte 301"));
   Make(FVector(-2800,6895,1001),FVector(-2750,6640,137),-90,0,TEXT("Elevador · descer ao lobby"));
   // 5.1: the guest floor corridor (tools/ue58/gen_hotel_rooms.py: elevator door at x -1736 on the north wall).
   Make(FVector(-1736,6880,1001),FVector(-2600,6640,137),-90,0,TEXT("Elevador · descer ao lobby"));}
  for(auto T:Elevators)if(T)T->SetActorHiddenInGame(!bHotel);}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const float Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.f;
 const float Solar=FMath::Sin((Hour-6.f)/12.f*PI);const float Day=FMath::SmoothStep(-.04f,.18f,Solar);
 const int32 ForcedWeather=CVarMareWeather.GetValueOnGameThread();
 const bool Rain=ForcedWeather==2 || ForcedWeather==3 || ((ForcedWeather==0) && UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain"));
 // Night: the eye must not adapt up to daylight brightness (that washed the scene out white); keep a
 // narrow dark EV100 window so moonlight reads blue-dim and lamps/windows carry the image.
 for(auto Volume:Interiors)if(Volume){auto& S=Volume->Settings;S.bOverride_AutoExposureMinBrightness=S.bOverride_AutoExposureMaxBrightness=true;
  const float NightEV=CVarMareInteriorNightEV.GetValueOnGameThread();
  S.AutoExposureMinBrightness=FMath::Lerp(NightEV,5.f,Day);S.AutoExposureMaxBrightness=FMath::Lerp(NightEV+.8f,9.f,Day);}
 if(Exposure){Exposure->Settings.bOverride_AutoExposureMinBrightness=true;Exposure->Settings.bOverride_AutoExposureMaxBrightness=true;Exposure->Settings.AutoExposureMinBrightness=FMath::Lerp(FMath::Min(CVarMareNightMinEV.GetValueOnGameThread(),-.9f),5.f,Day);Exposure->Settings.AutoExposureMaxBrightness=FMath::Lerp(-.9f,14.f,Day);}
 // 08/11 (Sergio: "o tempo ficou escuro, muito de repente. O dia virou noite"): the tsunami's storm sky builds up over
 // ~15 s and stays a grey day: a dim veiled sun, heavy dark clouds, haze (GloomNow eases every frame in UpdateWeather).
 // Overcast light: the sun fades out with the rain (no hard shadows) and the diffuse sky light doubles.
 if(Sky)Sky->GetLightComponent()->SetIntensity(FMath::Lerp(.035f,1.f,Day)*(1.f+2.5f*RainNow+1.2f*GloomNow*(1.f-RainNow)));
 if(Sun){Sun->SetActorRotation(FRotator(-Solar*58.f,-65.f+(Hour-12.f)*12.f,0));Sun->GetLightComponent()->SetIntensity(FMath::Max(0.f,Solar)*65000.f*FMath::Lerp(1.f-.998f*RainNow,CVarMareGloomSun.GetValueOnGameThread(),GloomNow));
  Sun->GetLightComponent()->SetLightColor(FLinearColor(1.f,FMath::Lerp(.95f,.99f,Day),FMath::Lerp(.88f,.975f,Day)),false);}
 // 09/11 (Sergio: "coloque uma lua cheia nas noites", "lua que gera luz noturna"): a full moon rises opposite the sun and
 // lights the night (it was a faint fixed light of .45 lux); no light while it is under the horizon.
 if(Moon){const FRotator MoonRot=MareMoonRotation(Hour);Moon->SetActorRotation(MoonRot);
  // the sky atmosphere drew its own small white disc for this light in the middle of the textured moon
  if(auto Directional=Cast<UDirectionalLightComponent>(Moon->GetLightComponent()))if(Directional->GetAtmosphereSunDiskColorScale()!=FLinearColor::Black)Directional->SetAtmosphereSunDiskColorScale(FLinearColor::Black);
  const float Above=FMath::SmoothStep(-.03f,.08f,float(-MoonRot.Vector().Z));
  Moon->GetLightComponent()->SetIntensity((1-Day)*Above*CVarMareMoonLux.GetValueOnGameThread()*(1.f+.8f*MareSuperMoon(Sim))*(1.f-.85f*RainNow));Moon->GetLightComponent()->SetLightColor(FLinearColor(.62f,.72f,1.f),false);}
 // Lamps switch on at dusk and only where the area is built (region actors hidden until bought).
 // FMath::SmoothStep needs A<B (with .55,.05 the lamps were lit by day and off at night).
 const float Dark=1.f-FMath::SmoothStep(.05f,.55f,Day);
 // Fixtures of an expansion show once it is bought (lighting.json "unlock"). 06/11 (5.4 game room): a comma list with
 // "!" for "not bought yet" ("grand_hotel,!salao_jogos": the lobby ceiling lamp that the billiard lamp replaces).
 const auto Owned=UMareSimulation::Object(Sim->State,TEXT("unlocked"));
 for(const auto& Lamp:Lamps)if(!Lamp.Unlock.IsEmpty() && Lamp.Source.IsValid()){const bool b=UnlockMatches(Owned,Lamp.Unlock);if(Lamp.Source->IsHidden()==b)Lamp.Source->SetActorHiddenInGame(!b);}
 // Bare lights without a fixture (the suite's): a soft fill by day, off at night, the ceiling lamps take over.
 for(auto Bare:BareLights)if(IsValid(Bare))Bare->GetLightComponent()->SetIntensity(FMath::Lerp(0.f,700.f,FMath::Square(Day)));
 // Kiosk work lights: from 7h to the closing hour; by day several times brighter so they read
 // against the daylight exposure under the roof (CVar mare.KioskDayLight).
 bool bCompany=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("created"),bCompany);
 const float HourNow=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.f;
 // 08/11 (Sergio: "quiosque continua escuro"): on from 7h even before the company exists (the kiosk is there all along).
 (void)bCompany;
 const float Work=HourNow>=7.f && HourNow<Sim->KioskCloseHour()+.5f?FMath::Lerp(1.f,CVarMareKioskDayLight.GetValueOnGameThread(),1.f-Dark):0.f;
 for(const auto& Lamp:Lamps)if(auto Light=Lamp.Light.Get()){const float Level=Lamp.bWork?FMath::Max(Dark,Work):Dark;const bool bOn=Level>.01f && Lamp.Source.IsValid() && !Lamp.Source->IsHidden();
  Light->SetVisibility(bOn);Light->SetIntensity(bOn?Lamp.Candela*Level:0.f);}
 if(Dark>.5f && !bLampsLogged){bLampsLogged=true;int32 On=0,Hidden=0,Gone=0;for(const auto& Lamp:Lamps){if(!Lamp.Source.IsValid())++Gone;else if(Lamp.Source->IsHidden())++Hidden;else ++On;}
  UE_LOG(LogTemp,Display,TEXT("MARE_LAMPS total=%d on=%d hidden_source=%d lost_source=%d"),Lamps.Num(),On,Hidden,Gone);}
 // Facade windows glow at night through MPC_MareTime.Night (M_WindowPane_PBR).
 if(!TimeCollection)TimeCollection=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
 if(TimeCollection)UKismetMaterialLibrary::SetScalarParameterValue(this,TimeCollection,TEXT("Night"),FMath::Clamp(1.f-Day,0.f,1.f)*(Rain?.8f:1.f));
 // A grey storm day needs the interior lights up (no sun through the windows).
 const float Overcast=1.f+1.6f*RainNow;
 // 05/11 (Sergio: "com a lâmpada funcionando tira a luz das paredes"): rectangular panels have no fixture (the generated
 // room fills "luz Sala/Cozinha/Banheiro", the kiosk fill and the kiosk lantern panel): off at night, the lamps light the
 // rooms; by day a soft fill. Point lights at a fixture (MareHomeLight: the pousada lamps) stay modest.
 // 06/11: point lights with no fixture at all (tag MareBareLight: the bungalow ceilings, the pousada reception door) are a
 // day fill only, off at night (the bedside lamps and the chandelier light the rooms).
 for(auto Light:Practical)if(IsValid(Light)){const bool bPanel=Light->GetLightComponent()->IsA<URectLightComponent>() || Light->ActorHasTag(TEXT("MareVisualExtra"));
  if(Light->ActorHasTag(TEXT("MareBareLight"))){Light->GetLightComponent()->SetIntensity(Overcast*FMath::Lerp(0.f,180.f,FMath::Square(Day)));continue;}
  Light->GetLightComponent()->SetIntensity(Overcast*(bPanel?FMath::Lerp(0.f,Light->ActorHasTag(TEXT("MareVisualExtra"))?600.f:2600.f,FMath::Square(Day))
  :Light->ActorHasTag(TEXT("MareHomeLight"))?FMath::Lerp(90.f,180.f,Day):Light->ActorHasTag(TEXT("MareBounce"))?FMath::Lerp(120.f,6500.f,Day):FMath::Lerp(350.f,2600.f,Day)));}
 // Overcast: denser fog with the rain (greys the horizon and the sky), a little darker exposure.
 if(Fog)Fog->GetComponent()->SetFogDensity(FMath::Lerp(.00065f,.0042f,FMath::Max(RainNow,.35f*GloomNow)));
 if(Exposure){Exposure->Settings.bOverride_AutoExposureBias=true;Exposure->Settings.AutoExposureBias=-.3f*RainNow*(1.f-GloomNow)+CVarMareGloomEV.GetValueOnGameThread()*GloomNow-CVarMareNightDarken.GetValueOnGameThread()*FMath::Clamp(1.f-Day,0.f,1.f)+CVarMareForestEV.GetValueOnGameThread()*CanopyNow*FMath::Clamp(Day,0.f,1.f);}
 auto Dishes=UMareSimulation::Object(Sim->Definitions,TEXT("dishes"));
 auto Price=[&](const FString& Id){return UMareSimulation::String(UMareSimulation::Object(Dishes,Id),TEXT("name"))+FString::Printf(TEXT("   R$ %.0f"),Sim->SalePrice(Id));};
 for(auto Sign:Signs){if(!IsValid(Sign))continue;FString Text;
  if(Sign->ActorHasTag(TEXT("MareCompanySign")))Text=UMareSimulation::String(UMareSimulation::Object(Sim->State,TEXT("company")),TEXT("name"));
  if(Sign->ActorHasTag(TEXT("MareStatusSign"))){bool Requested=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),Requested);Text=Sim->IsOpen()?TEXT("ABERTO"):Requested?TEXT("AGUARDE O HORÁRIO"):TEXT("FECHADO");Sign->GetTextRender()->SetTextRenderColor(Sim->IsOpen()?FColor(24,135,64):Requested?FColor(145,96,18):FColor(186,35,35));}
  if(Sign->ActorHasTag(TEXT("MarePromoSign")))Text=FString::Printf(TEXT("PROMOÇÕES<br>Coco gelado<br>R$ %.0f<br>Suco da fruta<br>R$ %.0f"),Sim->SalePrice(TEXT("coco_gelado")),Sim->SalePrice(TEXT("suco")));
  if(Sign->ActorHasTag(TEXT("MareMenuSign")))for(const FString& Id:Sim->KioskMenu())if(Sim->IsDishUnlocked(Id))Text+=Price(Id)+TEXT("<br>");
  for(FName Tag:Sign->Tags)if(Tag.ToString().StartsWith(TEXT("MareStock_"))){FString Id=Tag.ToString().RightChop(10);Text=UMareSimulation::String(UMareSimulation::Object(Dishes,Id),TEXT("name"))+FString::Printf(TEXT("<br>%d prontos"),Sim->Available(Id));}
  // Fixed signs saved in the level ("Casa", street names) keep their Portuguese text as the source for the translation.
  if(Text.IsEmpty())if(const FString* Source=SignSource.Find(Sign))Text=*Source;
  // The sign font is Latin only: a Cyrillic or CJK translation would draw empty boxes, so those keep the Portuguese.
  // 07/11 (the kiosk sign read "QUIOSQUE ▯ SABORES DA PRAIA"): the sign font has no bullet; draw a dash instead.
  if(!Text.IsEmpty()){FText Shown=MareLoc::Text(Text);if(!MareLoc::LatinOnly(Shown.ToString()))Shown=FText::FromString(Text);
   FString Drawn=Shown.ToString();if(Drawn.Contains(TEXT("•"))){Drawn.ReplaceInline(TEXT("•"),TEXT("-"));Shown=FText::FromString(Drawn);}
   if(!Sign->GetTextRender()->Text.EqualTo(Shown))Sign->GetTextRender()->SetText(Shown);}
 }
}

// 08/11 (Sergio: "diminua as ondas; ondas fortes só quando estiver chovendo"): on fair days the sea's Storm sits below
// zero (heights scale with 1+Storm*k in M_CoastalWater and AMarePerson::SeaHeight: about half of the old everyday sea);
// rain lifts it to .8, a storm to 1.
// 08/11 (Sergio: "deixe as ondas mais calmas"): -.45 -> -.75 (swell x.48, mid waves x.18).
static TAutoConsoleVariable<float> CVarMareSeaCalm(TEXT("mare.SeaCalm"),-.75f,TEXT("Sea roughness on fair days (MPC_MareTime.Storm, below 0 = calmer)."));   // i18n:skip
void UMareVisualWorld::UpdateWeather(float DeltaSeconds,UMareSimulation* Sim)
{
 // The tsunami's storm sky, eased every frame (08/11: inside the 2 s refresh it only advanced one frame's time per
 // refresh, and in slow motion the sky never darkened).
 {auto Summit=GetWorld()->GetSubsystem<UMareSummitWorld>();const float Target=Summit?Summit->GloomTarget():0.f;
  GloomNow=FMath::Lerp(GloomNow,Target,1.f-FMath::Exp(-DeltaSeconds*.07f));if(GloomNow<.001f && Target==0.f)GloomNow=0.f;}
 // Today's weather: rain from the save; storm = the "tempestade" event; rough sea (maré alta) also lifts the waves.
 bool bRain=UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain");
 bool bStorm=UMareSimulation::String(Sim->State,TEXT("day_event"))==TEXT("tempestade");
 bool bRough=Sim->IsSeaRough();
 switch(CVarMareWeather.GetValueOnGameThread()){case 1:bRain=bStorm=bRough=false;break;case 2:bRain=true;bStorm=bRough=false;break;
  case 3:bRain=bStorm=bRough=true;break;case 4:bRain=bStorm=false;bRough=true;break;default:break;}
 // Tsunami omen (UMareSummitWorld): the whole storm, and a sea far rougher than any stormy day.
 const float SummitOmen=GetWorld()->GetSubsystem<UMareSummitWorld>()?GetWorld()->GetSubsystem<UMareSummitWorld>()->OmenLevel():0.f;
 if(SummitOmen>.05f)bRain=bStorm=bRough=true;
 const bool bTsunami=GetWorld()->GetSubsystem<UMareSummitWorld>() && GetWorld()->GetSubsystem<UMareSummitWorld>()->IsWaveRunning();
 if(bTsunami)bRain=bStorm=bRough=false;   // the silence before the end: no rain, the sea draws back flat
 // About 4 s to settle; a QA override applies at once (PIE in the background ticks a few times a second).
 const float Ease=CVarMareWeather.GetValueOnGameThread()!=0?1.f:1.f-FMath::Exp(-DeltaSeconds*.25f);
 RainNow=FMath::Lerp(RainNow,bRain?(bStorm?1.f:.7f):0.f,Ease);
 if(SummitOmen>.05f)RainNow=0.f;   // 08/11: a dry storm (Sergio's reference; the rain drew streaks)
 WindNow=FMath::Lerp(WindNow,bStorm?1.f:bRain?.5f:.2f,Ease);
 // Volcano eruption nights (Sergio, 04/11): the sea gets very rough while the lava glows.
 const float Erupt=GetWorld()->GetSubsystem<UMareMarineWorld>()?GetWorld()->GetSubsystem<UMareMarineWorld>()->VolcanoGlowValue():0.f;
 StormNow=FMath::Lerp(StormNow,bStorm?1.f:bRough?.45f:0.f,Ease);
 // Only the sea follows the eruption; the clouds (StormClouds) keep the weather, or the night sky filled with flakes.
 const float Rough=FMath::Max3(StormNow,.85f*Erupt,1.1f*SummitOmen);   // 08/11: 1.9 drew a regular grid of crests (Sergio: linhas)
 const float Weather=FMath::Lerp(CVarMareSeaCalm.GetValueOnGameThread(),.8f,FMath::Clamp(RainNow/.7f,0.f,1.f));
 float SeaStorm=Weather+FMath::Max(0.f,Rough-Weather)*FMath::SmoothStep(0.f,.2f,Rough);
 // Tsunami: Storm below zero flattens M_CoastalWater's swell (its heights scale with 1+Storm*k) - the sea goes still.
 TsunamiCalm=FMath::FInterpTo(TsunamiCalm,bTsunami?1.f:0.f,DeltaSeconds,.6f);SeaStorm=FMath::Lerp(SeaStorm,-.9f,TsunamiCalm);
 if(TimeCollection){UKismetMaterialLibrary::SetScalarParameterValue(this,TimeCollection,TEXT("Rain"),RainNow);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeCollection,TEXT("Wind"),WindNow);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeCollection,TEXT("Storm"),SeaStorm);}
 // Overcast: thicker, fuller clouds (engine m_SimpleVolumetricCloud parameters) and a greyer, hazier atmosphere.
 if(!bSkyLooked){bSkyLooked=true;
  for(TActorIterator<AActor> It(GetWorld());It;++It){
   if(auto Cloud=It->FindComponentByClass<UVolumetricCloudComponent>())if(UMaterialInterface* CloudBase=Cloud->Material.LoadSynchronous()){CloudMaterial=UMaterialInstanceDynamic::Create(CloudBase,this);Cloud->SetMaterial(CloudMaterial);}
   if(auto SkyAtmo=It->FindComponentByClass<USkyAtmosphereComponent>())Atmosphere=SkyAtmo;}}
 if(CloudMaterial){CloudMaterial->SetScalarParameterValue(TEXT("Cloud_GlobalCoverage"),FMath::Lerp(FMath::Lerp(-.2f,.35f,RainNow),CVarMareGloomCover.GetValueOnGameThread(),GloomNow));
  CloudMaterial->SetScalarParameterValue(TEXT("Cloud_GlobalDensity"),FMath::Lerp(FMath::Lerp(.008f,.02f,RainNow),CVarMareGloomDensity.GetValueOnGameThread(),GloomNow));
  CloudMaterial->SetScalarParameterValue(TEXT("StormClouds"),FMath::Lerp(StormNow,CVarMareGloomStorm.GetValueOnGameThread(),GloomNow));}
 // The tsunami's grey storm day: far less blue scattering and a grey haze (the volumetric clouds alone left a navy sky).
 if(Atmosphere){Atmosphere->SetRayleighScatteringScale(FMath::Lerp(FMath::Lerp(.0331f,.024f,RainNow),CVarMareGloomRayleigh.GetValueOnGameThread(),GloomNow));
  Atmosphere->SetMieScatteringScale(FMath::Lerp(FMath::Lerp(.004f,.05f,RainNow),CVarMareGloomMie.GetValueOnGameThread(),GloomNow));}
 // Rain curtains: two open cylinders (3.5 m and 9 m) centred on the camera, hidden under a roof.
 if(RainCurtains.IsEmpty()){
  UStaticMesh* Cylinder=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
  UMaterialInterface* Mat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_RainCurtain.M_RainCurtain"));
  if(!Cylinder || !Mat)return;
  for(float Radius:{350.f,900.f}){FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   auto A=GetWorld()->SpawnActor<AStaticMeshActor>(FVector::ZeroVector,FRotator::ZeroRotator,P);if(!A)continue;
   A->SetMobility(EComponentMobility::Movable);auto M=A->GetStaticMeshComponent();M->SetStaticMesh(Cylinder);M->SetMaterial(0,Mat);
   M->SetCollisionEnabled(ECollisionEnabled::NoCollision);M->SetCastShadow(false);M->bVisibleInReflectionCaptures=false;
   A->SetActorScale3D(FVector(Radius/50.f,Radius/50.f,16.f));A->SetActorHiddenInGame(true);A->Tags.Add(TEXT("MareRain"));RainCurtains.Add(A);}}
 APlayerCameraManager* Cam=UGameplayStatics::GetPlayerCameraManager(GetWorld(),0);if(!Cam)return;
 const FVector Eye=Cam->GetCameraLocation();
 FHitResult Roof;FCollisionQueryParams Q(TEXT("MareRainRoof"),false);if(APawn* Pawn=UGameplayStatics::GetPlayerPawn(GetWorld(),0))Q.AddIgnoredActor(Pawn);
 const bool bCovered=GetWorld()->LineTraceSingleByChannel(Roof,Eye,Eye+FVector(0,0,2500),ECC_Visibility,Q);
 for(auto A:RainCurtains)if(IsValid(A)){A->SetActorLocation(FVector(Eye.X,Eye.Y,Eye.Z+250));A->SetActorHiddenInGame(RainNow<.02f || bCovered || GloomNow>.05f);}   // 08/11: the tsunami sky is a dry storm (the curtains drew streaks over the whole view)
}

int32 UMareVisualWorld::FootprintCount()const{return Footprints?Footprints->GetInstanceCount():0;}
void UMareVisualWorld::UpdateFootprints()
{
 static const int32 MaxPrints=240;static const float Life=180.f;
 UWorld* World=GetWorld();if(!World || !World->IsGameWorld())return;
 if(!Footprints){
  UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Custom/Beach/beach_footprint/beach_footprint1.beach_footprint1"));
  UMaterialInterface* Mat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_SandFootprint.M_SandFootprint"));
  if(!Mesh || !Mat)return;
  FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  FootprintActor=World->SpawnActor<AActor>(FVector::ZeroVector,FRotator::ZeroRotator,P);if(!FootprintActor)return;
  Footprints=NewObject<UInstancedStaticMeshComponent>(FootprintActor,TEXT("Footprints"));FootprintActor->SetRootComponent(Footprints);
  Footprints->SetMobility(EComponentMobility::Movable);Footprints->SetStaticMesh(Mesh);Footprints->SetMaterial(0,Mat);
  Footprints->SetCollisionEnabled(ECollisionEnabled::NoCollision);Footprints->SetCastShadow(false);Footprints->NumCustomDataFloats=1;
  Footprints->RegisterComponent();}
 const float Now=World->GetTimeSeconds();
 // Fade: custom data 0 = age (0 fresh .. 1 gone).
 for(int32 I=0;I<FootprintBorn.Num();++I)Footprints->SetCustomDataValue(I,0,FMath::Clamp((Now-FootprintBorn[I])/Life,0.f,1.f),false);
 if(FootprintBorn.Num())Footprints->MarkRenderStateDirty();
 ACharacter* Hero=Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(World,0));if(!Hero)return;
 UCharacterMovementComponent* Move=Hero->GetCharacterMovement();if(!Move || !Move->IsMovingOnGround())return;
 // QA walk: the hero zeroes outside input, so push it along its facing (swept) and step that way.
 FVector Velocity=Hero->GetVelocity();Velocity.Z=0;
 if(CVarMareWalkTest.GetValueOnGameThread()){
  // step along the facing and set the capsule on the floor below (a swept move stalls on the sand ripples)
  const float Half=Hero->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();const FVector Next=Hero->GetActorLocation()+Hero->GetActorForwardVector()*200.f*FMath::Min(World->GetDeltaSeconds(),.1f);
  FHitResult Floor;FCollisionQueryParams FQ(TEXT("MareWalkTest"),false,Hero);
  if(World->LineTraceSingleByChannel(Floor,Next+FVector(0,0,Half),Next-FVector(0,0,Half*3),ECC_Visibility,FQ))Hero->SetActorLocation(Floor.ImpactPoint+FVector(0,0,Half+2.f));
  Velocity=Hero->GetActorForwardVector()*200.f;}
 if(Velocity.Size()<60.f)return;
 const FVector Feet=Hero->GetActorLocation()-FVector(0,0,Hero->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
 if(FVector::Dist2D(Feet,LastStep)<72.f)return;
 LastStep=Feet;bLeftFoot=!bLeftFoot;
 const FVector Dir=Velocity.GetSafeNormal();const FVector Right(-Dir.Y,Dir.X,0);const float Side=bLeftFoot?-1.f:1.f;
 const FVector At=Feet+Right*Side*11.f;
 FHitResult Hit;FCollisionQueryParams Q(TEXT("MareFootprint"),true,Hero);
 if(!World->LineTraceSingleByChannel(Hit,At+FVector(0,0,60),At-FVector(0,0,90),ECC_Visibility,Q) || !Hit.GetComponent())return;
 // Sand only: the coast ground materials (the bay and the island's new land) on the beach side of the lawn (grass starts
 // around the old bay's y -1050, measured all round the island as the distance to the coast).
 UMaterialInterface* Under=Hit.GetComponent()->GetMaterial(0);
 if(!Under || !(Under->GetName().Contains(TEXT("CoastGround")) || Under->GetName().Contains(TEXT("IslandGround"))) || MareIsland::CoastY(Hit.ImpactPoint.X,Hit.ImpactPoint.Y)>-1050.f)return;
 const FTransform T(FRotationMatrix::MakeFromZX(Hit.ImpactNormal,Dir).Rotator(),Hit.ImpactPoint+Hit.ImpactNormal*.6f,FVector(1,Side,1));   // the mesh is a right foot
 if(Footprints->GetInstanceCount()<MaxPrints){NextFootprint=Footprints->AddInstance(T,true);FootprintBorn.Add(Now);}
 else{Footprints->UpdateInstanceTransform(NextFootprint,T,true,true,true);FootprintBorn[NextFootprint]=Now;}
 Footprints->SetCustomDataValue(NextFootprint,0,0.f,true);
 NextFootprint=(NextFootprint+1)%MaxPrints;
}

void UMareVisualWorld::CullLocalLights()
{
 // Every local light of the world gets a draw distance (mare.LightDrawDistance; kiosk/house bounce lights x
 // mare.BounceLightReach) unless its author gave it one, and lights smaller than mare.LightShadowMinRadius stop casting
 // shadows (04/11: 99 of 134 lights were shadowed, each one redrawing its shadow pages). Lights spawned later
 // (expansions, lamps, businesses) are picked up on the next 2 s refresh; a cvar change reapplies to all of them.
 const float Reach=CVarMareLightDrawDistance.GetValueOnGameThread(),Bounce=CVarMareBounceLightReach.GetValueOnGameThread(),MinShadow=CVarMareLightShadowMinRadius.GetValueOnGameThread();
 const FVector Key(Reach,Bounce,MinShadow);const bool bChanged=!Key.Equals(LightCullKey);LightCullKey=Key;
 int32 Set=0,Shadowed=0;
 for(TObjectIterator<ULocalLightComponent> It;It;++It){ULocalLightComponent* Light=*It;
  if(Light->GetWorld()!=GetWorld())continue;
  FLightCullState* State=LightCull.Find(Light);
  if(!State){if(Light->MaxDrawDistance>0)continue;State=&LightCull.Add(Light,{Light->CastShadows!=0});}
  else if(!bChanged)continue;
  const AActor* Owner=Light->GetOwner();const bool bBounce=Owner && Owner->ActorHasTag(TEXT("MareBounce"));
  const float D=Reach<=0?0.f:(bBounce?Reach*Bounce:Reach);
  Light->MaxDrawDistance=D;Light->MaxDistanceFadeRange=FMath::Min(1500.f,D*.3f);
  // A fill light needs no shadow; small lights (lanterns, interiors) keep at most a contact shadow.
  const bool bShadow=State->bShadow && !bBounce && Light->AttenuationRadius>=MinShadow;
  State->bEligible=bShadow;   // whether it casts one now is BudgetLightShadows' call (the nearest few)
  if(CVarMareLightShadowBudget.GetValueOnGameThread()<=0 && Light->CastShadows!=bShadow)Light->SetCastShadows(bShadow);
  Shadowed+=bShadow;++Set;Light->MarkRenderStateDirty();}
 if(Set)UE_LOG(LogTemp,Display,TEXT("MARE_LIGHT_CULL lights=%d shadowed=%d reach=%.0f bounce=x%.1f min_shadow_radius=%.0f"),Set,Shadowed,Reach,Bounce,MinShadow);
}

void UMareVisualWorld::BudgetLightShadows()
{
 const int32 Budget=CVarMareLightShadowBudget.GetValueOnGameThread();if(Budget<=0)return;
 const float Reach=CVarMareLightShadowReach.GetValueOnGameThread();
 auto PC=GetWorld()->GetFirstPlayerController();if(!PC || !PC->PlayerCameraManager)return;
 const FVector Eye=PC->PlayerCameraManager->GetCameraLocation();
 struct FCand{ULocalLightComponent* L;float D;};TArray<FCand> Cands;
 for(auto It=LightCull.CreateIterator();It;++It){ULocalLightComponent* L=It.Key().Get();if(!L){It.RemoveCurrent();continue;}
  float D=FVector::Dist(L->GetComponentLocation(),Eye);
  if(!It.Value().bEligible || !L->IsVisible() || L->Intensity<=0.f || D>Reach){if(L->CastShadows)L->SetCastShadows(false);continue;}
  if(L->CastShadows)D-=300.f;   // hysteresis: a lamp already shadowed keeps it until another is clearly nearer
  Cands.Add({L,D});}
 Cands.Sort([](const FCand& A,const FCand& B){return A.D<B.D;});
 for(int32 I=0;I<Cands.Num();++I){const bool b=I<Budget;if(Cands[I].L->CastShadows!=b)Cands[I].L->SetCastShadows(b);}
}

void UMareVisualWorld::AddGlassCompanions()
{
 // Content/Data/glass_split.json (mare_hud splitglass, 04/11): meshes whose see-through triangles moved to a separate
 // non-Nanite <mesh>_Glass so the opaque body could use Nanite (GPU-first rule). Every component drawing a body gets
 // the glass on top, same instances and transforms; the body's own translucent overrides go to the glass.
 if(bGlassDone)return;bGlassDone=true;
 FString Text;TSharedPtr<FJsonObject> Map;
 if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/glass_split.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Map) || !Map.IsValid())return;
 TMap<UStaticMesh*,UStaticMesh*> Glass;
 for(const auto& Pair:Map->Values){const FString Key(Pair.Key.ToView());if(Key.StartsWith(TEXT("_")))continue;FString GlassPath;if(!Pair.Value->TryGetString(GlassPath))continue;
  UStaticMesh* Body=FindObject<UStaticMesh>(nullptr,*Key);if(!Body)Body=LoadObject<UStaticMesh>(nullptr,*Key);
  UStaticMesh* G=LoadObject<UStaticMesh>(nullptr,*GlassPath);if(Body && G)Glass.Add(Body,G);}
 if(Glass.IsEmpty())return;
 TArray<UStaticMeshComponent*> Sources;
 for(TObjectIterator<UStaticMeshComponent> It;It;++It)if(It->GetWorld()==GetWorld() && It->GetStaticMesh() && Glass.Contains(It->GetStaticMesh()) && !It->ComponentHasTag(TEXT("MareGlass")))Sources.Add(*It);
 int32 Made=0;
 for(UStaticMeshComponent* Src:Sources){AActor* Owner=Src->GetOwner();if(!Owner)continue;UStaticMesh* G=Glass[Src->GetStaticMesh()];
  UStaticMeshComponent* Comp=NewObject<UStaticMeshComponent>(Owner,Src->GetClass());Comp->ComponentTags.Add(TEXT("MareGlass"));
  Comp->SetMobility(Src->Mobility);Comp->SetupAttachment(Src);Comp->SetStaticMesh(G);Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Comp->SetCastShadow(Src->CastShadow);Comp->SetVisibility(Src->IsVisible());Comp->SetHiddenInGame(Src->bHiddenInGame);
  Comp->LDMaxDrawDistance=Src->LDMaxDrawDistance;
  // Translucent overrides of the body move to the glass (where those triangles now are); the body falls back to its
  // opaque placeholder slot, which has no triangles.
  for(int32 I=0;I<Src->OverrideMaterials.Num();++I)if(UMaterialInterface* M=Src->OverrideMaterials[I]){Comp->SetMaterial(I,M);
   if(IsTranslucentBlendMode(M->GetBlendMode()))Src->SetMaterial(I,nullptr);}
  if(auto SrcISM=Cast<UInstancedStaticMeshComponent>(Src)){auto ISM=CastChecked<UInstancedStaticMeshComponent>(Comp);
   ISM->InstanceStartCullDistance=SrcISM->InstanceStartCullDistance;ISM->InstanceEndCullDistance=SrcISM->InstanceEndCullDistance;
   Comp->RegisterComponent();
   TArray<FTransform> Instances;for(int32 I=0;I<SrcISM->GetInstanceCount();++I){FTransform T;SrcISM->GetInstanceTransform(I,T,false);Instances.Add(T);}
   ISM->AddInstances(Instances,false,false);}
  else Comp->RegisterComponent();
  Owner->AddInstanceComponent(Comp);++Made;}
 UE_LOG(LogTemp,Display,TEXT("MARE_GLASS_SPLIT meshes=%d components=%d"),Glass.Num(),Made);
}

