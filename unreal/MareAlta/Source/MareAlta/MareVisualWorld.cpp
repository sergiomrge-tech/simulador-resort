#include "MareVisualWorld.h"
#include "MareSimulation.h"
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

TStatId UMareVisualWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareVisualWorld,STATGROUP_Tickables);}
void UMareVisualWorld::BuildLamps()
{
 // Light sources exported from Godot (their glow materials were lost): mesh, glass centre above the
 // pivot (cm), candela at full night, reach (cm), colour temperature (K).
 struct FKind{const TCHAR* Mesh;float Up,Candela,Radius,Kelvin;};
 static const FKind Kinds[]={{TEXT("World_1392"),40,150,1900,2900},{TEXT("World_2205"),40,150,1900,2900},{TEXT("World_0687"),9,32,800,2700},
  {TEXT("World_0515"),9,32,800,2700},{TEXT("World_0199"),19,12,550,2200},{TEXT("World_0138"),2,30,700,9000}};
 LampHolder=GetWorld()->SpawnActor<AActor>();if(!LampHolder)return;
 LampHolder->SetRootComponent(NewObject<USceneComponent>(LampHolder,TEXT("LampRoot")));LampHolder->GetRootComponent()->RegisterComponent();
 for(TActorIterator<AActor> It(GetWorld());It;++It){if(*It==LampHolder)continue;
  TArray<UInstancedStaticMeshComponent*> Parts;It->GetComponents(Parts);
  for(auto Part:Parts){if(!Part->GetStaticMesh())continue;const FString Mesh=Part->GetStaticMesh()->GetName();
   const FKind* Kind=nullptr;for(const auto& K:Kinds)if(Mesh==K.Mesh)Kind=&K;if(!Kind)continue;
   for(int32 I=0;I<Part->GetInstanceCount();++I){FTransform T;Part->GetInstanceTransform(I,T,true);
    auto Light=NewObject<UPointLightComponent>(LampHolder);Light->SetupAttachment(LampHolder->GetRootComponent());Light->RegisterComponent();
    Light->SetWorldLocation(T.TransformPosition(FVector(0,0,Kind->Up)));Light->SetIntensityUnits(ELightUnits::Candelas);Light->SetIntensity(0);
    Light->SetAttenuationRadius(Kind->Radius);Light->SetUseTemperature(true);Light->SetTemperature(Kind->Kelvin);Light->SetCastShadows(false);
    Light->SetSourceRadius(4);Light->SetVisibility(false);Lamps.Add({Light,*It,Kind->Candela});}
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
void UMareVisualWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()))return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=2.f;
 RefreshExpansions();
 if(!Sun){for(TActorIterator<ALight> It(GetWorld());It;++It){if(It->ActorHasTag(TEXT("MareSun")))Sun=*It;if(It->ActorHasTag(TEXT("MareMoon")))Moon=*It;if(It->ActorHasTag(TEXT("MarePractical")))Practical.AddUnique(*It);}
  for(TActorIterator<AExponentialHeightFog> It(GetWorld());It;++It)Fog=*It;
  for(TActorIterator<APostProcessVolume> It(GetWorld());It;++It)if(It->bUnbound){Exposure=*It;break;}
  for(TActorIterator<ASkyLight> It(GetWorld());It;++It){Sky=*It;break;}
  BuildLamps();
  for(TActorIterator<ATextRenderActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareText"))){Signs.Add(*It);
   if(It->ActorHasTag(TEXT("MareStatusSign"))){auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(It->GetActorLocation(),FRotator::ZeroRotator);
    Target->Action=TEXT("KioskSign");Target->Label=TEXT("Placa do quiosque");Target->Reach=330;Target->OcclusionTolerance=100;Target->SetOwner(*It);}
  }
  // Grand Hotel reception desk inside the opened ground floor (tools/ue58/hotel_lobby_shell.py).
  if(!Reception){Reception=GetWorld()->SpawnActor<AMareServiceTarget>(FVector(-1390,6470,160),FRotator::ZeroRotator);
   Reception->Action=TEXT("HotelReception");Reception->Label=TEXT("Recepção do Grand Hotel");Reception->Reach=280;Reception->OcclusionTolerance=60;}}
 if(Reception){bool bHotel=false;UMareSimulation::Object(GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>()->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);Reception->SetActorHiddenInGame(!bHotel);}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const float Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.f;
 const float Solar=FMath::Sin((Hour-6.f)/12.f*PI);const float Day=FMath::SmoothStep(-.04f,.18f,Solar);
 const bool Rain=UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain");
 // Night: the eye must not adapt up to daylight brightness (that washed the scene out white); keep a
 // narrow dark EV100 window so moonlight reads blue-dim and lamps/windows carry the image.
 if(Exposure){Exposure->Settings.bOverride_AutoExposureMinBrightness=true;Exposure->Settings.bOverride_AutoExposureMaxBrightness=true;Exposure->Settings.AutoExposureMinBrightness=FMath::Lerp(-1.9f,5.f,Day);Exposure->Settings.AutoExposureMaxBrightness=FMath::Lerp(-.9f,14.f,Day);}
 if(Sky)Sky->GetLightComponent()->SetIntensity(FMath::Lerp(.035f,1.f,Day));
 if(Sun){Sun->SetActorRotation(FRotator(-Solar*58.f,-65.f+(Hour-12.f)*12.f,0));Sun->GetLightComponent()->SetIntensity(FMath::Max(0.f,Solar)*65000.f*(Rain?.2f:1.f));
  Sun->GetLightComponent()->SetLightColor(FLinearColor(1.f,FMath::Lerp(.95f,.99f,Day),FMath::Lerp(.88f,.975f,Day)),false);}
 if(Moon){Moon->GetLightComponent()->SetIntensity((1-Day)*.45f);Moon->GetLightComponent()->SetLightColor(FLinearColor(.62f,.72f,1.f),false);}
 // Lamps switch on at dusk and only where the area is built (region actors hidden until bought).
 const float Dark=FMath::SmoothStep(.55f,.05f,Day);
 for(const auto& Lamp:Lamps)if(auto Light=Lamp.Light.Get()){const bool bOn=Dark>.01f && Lamp.Source.IsValid() && !Lamp.Source->IsHidden();
  Light->SetVisibility(bOn);Light->SetIntensity(bOn?Lamp.Candela*Dark:0.f);}
 // Facade windows glow at night through MPC_MareTime.Night (M_WindowPane_PBR).
 if(!TimeCollection)TimeCollection=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
 if(TimeCollection)UKismetMaterialLibrary::SetScalarParameterValue(this,TimeCollection,TEXT("Night"),FMath::Clamp(1.f-Day,0.f,1.f)*(Rain?.8f:1.f));
 for(auto Light:Practical)if(IsValid(Light))Light->GetLightComponent()->SetIntensity(Light->ActorHasTag(TEXT("MareHomeLight"))?FMath::Lerp(1000.f,180.f,Day):Light->ActorHasTag(TEXT("MareBounce"))?FMath::Lerp(400.f,6500.f,Day):FMath::Lerp(2200.f,10000.f,Day));
 if(Fog)Fog->GetComponent()->SetFogDensity(Rain?.0018f:.00065f);
 auto Dishes=UMareSimulation::Object(Sim->Definitions,TEXT("dishes"));
 auto Price=[&](const FString& Id){return UMareSimulation::String(UMareSimulation::Object(Dishes,Id),TEXT("name"))+FString::Printf(TEXT("   R$ %.0f"),Sim->DishPrice(Id));};
 for(auto Sign:Signs){if(!IsValid(Sign))continue;FString Text;
  if(Sign->ActorHasTag(TEXT("MareCompanySign")))Text=UMareSimulation::String(UMareSimulation::Object(Sim->State,TEXT("company")),TEXT("name"));
  if(Sign->ActorHasTag(TEXT("MareStatusSign"))){bool Requested=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),Requested);Text=Sim->IsOpen()?TEXT("ABERTO"):Requested?TEXT("AGUARDE O HORÁRIO"):TEXT("FECHADO");Sign->GetTextRender()->SetTextRenderColor(Sim->IsOpen()?FColor(24,135,64):Requested?FColor(145,96,18):FColor(186,35,35));}
  if(Sign->ActorHasTag(TEXT("MarePromoSign")))Text=FString::Printf(TEXT("PROMOÇÕES<br>Coco gelado<br>R$ %.0f<br>Suco da fruta<br>R$ %.0f"),Sim->DishPrice(TEXT("coco_gelado")),Sim->DishPrice(TEXT("suco")));
  if(Sign->ActorHasTag(TEXT("MareMenuSign")))for(FString Id:{TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")})if(Sim->IsDishUnlocked(Id))Text+=Price(Id)+TEXT("<br>");
  for(FName Tag:Sign->Tags)if(Tag.ToString().StartsWith(TEXT("MareStock_"))){FString Id=Tag.ToString().RightChop(10);Text=UMareSimulation::String(UMareSimulation::Object(Dishes,Id),TEXT("name"))+FString::Printf(TEXT("<br>%d prontos"),Sim->Available(Id));}
  if(!Text.IsEmpty() && Sign->GetTextRender()->Text.ToString()!=Text)Sign->GetTextRender()->SetText(FText::FromString(Text));
 }
}
