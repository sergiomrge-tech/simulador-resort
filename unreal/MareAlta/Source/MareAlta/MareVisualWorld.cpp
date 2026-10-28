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

TStatId UMareVisualWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareVisualWorld,STATGROUP_Tickables);}
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
  for(TActorIterator<ATextRenderActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareText"))){Signs.Add(*It);
   if(It->ActorHasTag(TEXT("MareStatusSign"))){auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(It->GetActorLocation(),FRotator::ZeroRotator);
    Target->Action=TEXT("KioskSign");Target->Label=TEXT("Placa do quiosque");Target->Reach=330;Target->OcclusionTolerance=100;Target->SetOwner(*It);}
  }}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const float Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.f;
 const float Solar=FMath::Sin((Hour-6.f)/12.f*PI);const float Day=FMath::SmoothStep(-.04f,.18f,Solar);
 const bool Rain=UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain");
 if(Exposure){Exposure->Settings.bOverride_AutoExposureMinBrightness=true;Exposure->Settings.bOverride_AutoExposureMaxBrightness=true;Exposure->Settings.AutoExposureMinBrightness=FMath::Lerp(0.f,5.f,Day);Exposure->Settings.AutoExposureMaxBrightness=FMath::Lerp(8.f,14.f,Day);}
 if(Sun){Sun->SetActorRotation(FRotator(-Solar*58.f,-65.f+(Hour-12.f)*12.f,0));Sun->GetLightComponent()->SetIntensity(FMath::Max(0.f,Solar)*65000.f*(Rain?.2f:1.f));
  Sun->GetLightComponent()->SetLightColor(FLinearColor(1.f,FMath::Lerp(.95f,.99f,Day),FMath::Lerp(.88f,.975f,Day)),false);}
 if(Moon)Moon->GetLightComponent()->SetIntensity((1-Day)*.8f);
 for(auto Light:Practical)if(IsValid(Light))Light->GetLightComponent()->SetIntensity(Light->ActorHasTag(TEXT("MareHomeLight"))?FMath::Lerp(1000.f,180.f,Day):Light->ActorHasTag(TEXT("MareBounce"))?FMath::Lerp(400.f,6500.f,Day):FMath::Lerp(2200.f,10000.f,Day));
 if(Fog)Fog->GetComponent()->SetFogDensity(Rain?.0018f:.00065f);
 auto Dishes=UMareSimulation::Object(Sim->Definitions,TEXT("dishes"));
 auto Price=[&](const FString& Id){auto Dish=UMareSimulation::Object(Dishes,Id);return UMareSimulation::String(Dish,TEXT("name"))+FString::Printf(TEXT("   R$ %.0f"),UMareSimulation::Number(Dish,TEXT("price")));};
 for(auto Sign:Signs){if(!IsValid(Sign))continue;FString Text;
  if(Sign->ActorHasTag(TEXT("MareCompanySign")))Text=UMareSimulation::String(UMareSimulation::Object(Sim->State,TEXT("company")),TEXT("name"));
  if(Sign->ActorHasTag(TEXT("MareStatusSign"))){bool Requested=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),Requested);Text=Sim->IsOpen()?TEXT("ABERTO"):Requested?TEXT("AGUARDE O HORÁRIO"):TEXT("FECHADO");Sign->GetTextRender()->SetTextRenderColor(Sim->IsOpen()?FColor(24,135,64):Requested?FColor(145,96,18):FColor(186,35,35));}
  if(Sign->ActorHasTag(TEXT("MarePromoSign")))Text=FString::Printf(TEXT("PROMOÇÕES<br>Coco gelado<br>R$ %.0f<br>Suco da fruta<br>R$ %.0f"),UMareSimulation::Number(UMareSimulation::Object(Dishes,TEXT("coco_gelado")),TEXT("price")),UMareSimulation::Number(UMareSimulation::Object(Dishes,TEXT("suco")),TEXT("price")));
  if(Sign->ActorHasTag(TEXT("MareMenuSign")))for(FString Id:{TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")})if(Sim->IsDishUnlocked(Id))Text+=Price(Id)+TEXT("<br>");
  for(FName Tag:Sign->Tags)if(Tag.ToString().StartsWith(TEXT("MareStock_"))){FString Id=Tag.ToString().RightChop(10);Text=UMareSimulation::String(UMareSimulation::Object(Dishes,Id),TEXT("name"))+FString::Printf(TEXT("<br>%d prontos"),Sim->Available(Id));}
  if(!Text.IsEmpty() && Sign->GetTextRender()->Text.ToString()!=Text)Sign->GetTextRender()->SetText(FText::FromString(Text));
 }
}
