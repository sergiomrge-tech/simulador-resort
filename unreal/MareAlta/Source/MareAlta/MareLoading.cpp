#include "MareLoading.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "MareOptions.h"
#include "Internationalization/Culture.h"
#include "Internationalization/Internationalization.h"
#include "MoviePlayer.h"
#include "PipelineStateCache.h"
#include "Containers/Ticker.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "HAL/PlatformTime.h"
#include "Styling/SlateBrush.h"
#include "Engine/Texture2D.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"

/** Loading screen (09/11, C7): every map load of the packaged game (the first one at boot, Carregar, Novo jogo in
 *  another slot, back to the main menu) shows the title art with a notebook page holding a tip from tutorial.json, in
 *  the player's language, instead of a frozen frame. The movie player draws it on its own thread while the map loads. */
namespace MareLoading
{
 namespace
 {
  TStrongObjectPtr<UTexture2D>& Art(){static TStrongObjectPtr<UTexture2D> T;return T;}
  FSlateBrush& ArtBrush(){static FSlateBrush B;return B;}
  /** The title art as a brush (null when the texture is missing). */
  const FSlateBrush* TitleArt()
  {
   if(!Art().IsValid())if(UTexture2D* T=LoadObject<UTexture2D>(nullptr,TEXT("/Game/UI/Title/T_TitleArt.T_TitleArt")))Art().Reset(T);
   if(!Art().IsValid())return nullptr;
   FSlateBrush& Brush=ArtBrush();
   Brush.SetResourceObject(Art().Get());Brush.ImageSize=FVector2D(Art()->GetSizeX(),Art()->GetSizeY());Brush.DrawAs=ESlateBrushDrawType::Image;
   return &Brush;
  }
  /** A tip at random from Content/Data/tutorial.json (title and text, translated). */
  void Tip(FString& Title,FString& Text)
  {
   FString Json;TSharedPtr<FJsonObject> Doc;const TSharedPtr<FJsonObject>* Tips=nullptr;
   if(!FFileHelper::LoadFileToString(Json,*(FPaths::ProjectContentDir()/TEXT("Data/tutorial.json"))) ||
      !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Doc) || !Doc.IsValid() || !Doc->TryGetObjectField(TEXT("tips"),Tips))return;
   // Only tips about what the demo has (09/11: the first boot drew the Grand Hotel's elevator).
   static const TCHAR* Skip[]={TEXT("Hotel"),TEXT("Elevator"),TEXT("Restaurant"),TEXT("Room"),TEXT("Pool"),TEXT("TableTennis"),TEXT("Rental")};   // i18n:skip
   TArray<TSharedPtr<FJsonObject>> List;
   for(const auto& Pair:(*Tips)->Values){const FString Id(Pair.Key.ToView());bool bOut=false;for(const TCHAR* S:Skip)bOut|=Id.Contains(S);
    if(!bOut && Pair.Value->Type==EJson::Object)List.Add(Pair.Value->AsObject());}
   if(List.IsEmpty())return;
   const auto Pick=List[FMath::RandRange(0,List.Num()-1)];
   Title=MareLoc::Tr(Pick->GetStringField(TEXT("title")));Text=MareLoc::Tr(Pick->GetStringField(TEXT("text")));
  }
  TSharedRef<SWidget> Widget()
  {
   // The player's language before any text (09/11: on the first boot the tip came out in the system's language).
   {const FMareOptions& O=FMareOptions::Get();if(!GIsEditor && FInternationalization::Get().GetCurrentCulture()->GetName()!=O.Culture)O.ApplyCulture();}
   const FSlateBrush* Brush=TitleArt();
   FString Title,Text;Tip(Title,Text);
   const TSharedRef<SVerticalBox> Page=SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(MareLoc::Tr(TEXT("Dica")) + (Title.IsEmpty()?FString():TEXT(" · ")+Title)))
      .Font(MareNotebook::Hand(26)).ColorAndOpacity(MareNotebook::Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,10)[SNew(STextBlock).Text(FText::FromString(Text)).Font(MareNotebook::Body(15)).ColorAndOpacity(MareNotebook::Ink).AutoWrapText(true)]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)[SNew(STextBlock).Text(FText::FromString(MareLoc::Tr(TEXT("Carregando...")))).Font(MareNotebook::Hand(20)).ColorAndOpacity(MareNotebook::Brown)];
   return SNew(SOverlay)
    +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Hex(24,36,44))]
    +SOverlay::Slot()[SNew(SScaleBox).Stretch(EStretch::ScaleToFill)[SNew(SImage).Image(Brush)]]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,48)
     [SNew(SBox).WidthOverride(640)[MareNotebook::Page(Page)]];
  }

  /** Shader warm-up state (09/11). Modern games compile their pipeline states (PSOs) before the menu: the first time
   *  a material is drawn the driver compiles it, and a fresh PC (or a new driver) showed the world with objects popping
   *  in late (r.PSOPrecache.ProxyCreationStrategy 1 holds a mesh back until its PSOs are ready) and hitches the first
   *  time each thing showed up. UE 5.8 already precaches the PSOs of every loaded component in the background; this
   *  waits for it, at the highest priority, before letting the player in, and draws the world behind the page so the
   *  first frames compile there. With the driver cache warm (every later start) it ends in about a second, unseen. */
  struct FWarm{TSharedPtr<SWidget> Page;FTSTicker::FDelegateHandle Tick;double Start=0,QuietSince=-1;uint32 Peak=0;float Progress=0;
   bool bOverlay=false,bWorldOff=false,bTitleGone=false;};
  FWarm& Warm(){static FWarm W;return W;}
  constexpr float BarWidth=520.f;
  void LogRuntime(const TCHAR* When)
  {
   const FPSORuntimeCreationStats S=PipelineStateCache::GetPSORuntimeCreationStats();
   UE_LOG(LogTemp,Display,TEXT("MARE_PSO %s created=%u hitches_gfx=%u hitches_cs=%u precached_hitches=%u driver_cache_misses=%u driver_cache_unhealthy=%d active=%u"),   // i18n:skip
    When,S.TotalPSOCreations,S.GraphicsPSOHitches,S.ComputePSOHitches,S.PreviouslyPrecachedPSOHitches,S.SuspectedUnhealthyDriverCachePSOHitches,
    S.bDriverCacheSuspectedUnhealthy?1:0,PipelineStateCache::NumActivePrecacheRequests());
  }
  void DropPage()
  {
   FWarm& W=Warm();
   if(W.Page.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(W.Page.ToSharedRef());
   W.Page.Reset();
  }
  void FinishWarmup()
  {
   FWarm& W=Warm();
   PipelineStateCache::PrecachePSOsBoostToHighestPriority(false);
   DropPage();
   if(!W.bTitleGone && GEngine && GEngine->GameViewport)GEngine->GameViewport->bDisableWorldRendering=W.bWorldOff;
   UE_LOG(LogTemp,Display,TEXT("MARE_PSO warmup %.1fs peak=%u left=%u title_gone=%d"),FPlatformTime::Seconds()-W.Start,W.Peak,   // i18n:skip
    PipelineStateCache::NumActivePrecacheRequests(),W.bTitleGone?1:0);
   LogRuntime(TEXT("after_warmup"));   // i18n:skip
  }
  TSharedRef<SWidget> WarmWidget()
  {
   static const FSlateRoundedBoxBrush Back(MareNotebook::Hex(217,195,151),8.f);
   static const FSlateRoundedBoxBrush Fill(MareNotebook::Brown,8.f);
   const TSharedRef<SVerticalBox> Page=SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(MareLoc::Tr(TEXT("Preparando os gráficos"))))
      .Font(MareNotebook::Hand(26)).ColorAndOpacity(MareNotebook::Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,14)[SNew(STextBlock)
      .Text(FText::FromString(MareLoc::Tr(TEXT("Na primeira vez o jogo prepara os efeitos visuais para a sua placa de vídeo. Nas próximas vezes isso é rápido."))))
      .Font(MareNotebook::Body(15)).ColorAndOpacity(MareNotebook::Ink).AutoWrapText(true)]
    +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(SBox).WidthOverride(BarWidth).HeightOverride(16)[SNew(SOverlay)
      +SOverlay::Slot()[SNew(SBorder).BorderImage(&Back)]
      +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).WidthOverride_Lambda([](){return FOptionalSize(FMath::Max(16.f,BarWidth*Warm().Progress));})
       [SNew(SBorder).BorderImage(&Fill)]]]]
     +SHorizontalBox::Slot().FillWidth(1).HAlign(HAlign_Right).VAlign(VAlign_Center)[SNew(STextBlock)
      .Text_Lambda([](){return FText::FromString(FString::Printf(TEXT("%d%%"),FMath::RoundToInt(Warm().Progress*100.f)));})   // i18n:skip
      .Font(MareNotebook::Hand(20)).ColorAndOpacity(MareNotebook::Brown)]];
   return SNew(SOverlay)
    +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Hex(24,36,44))]
    +SOverlay::Slot()[SNew(SScaleBox).Stretch(EStretch::ScaleToFill)[SNew(SImage).Image(TitleArt())]]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,48)
     [SNew(SBox).WidthOverride(640)[MareNotebook::Page(Page)]];
  }
 }

 void ShaderWarmup(bool bOverlay)
 {
  if(GIsEditor)return;
  FWarm& W=Warm();if(W.Tick.IsValid())return;
  W=FWarm();W.Start=FPlatformTime::Seconds();W.bOverlay=bOverlay;W.Peak=PipelineStateCache::NumActivePrecacheRequests();
  PipelineStateCache::PrecachePSOsBoostToHighestPriority(true);
  if(GEngine && GEngine->GameViewport){W.bWorldOff=GEngine->GameViewport->bDisableWorldRendering;GEngine->GameViewport->bDisableWorldRendering=false;}
  static bool bRuntimeLog=false;
  if(!bRuntimeLog){bRuntimeLog=true;FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float){LogRuntime(TEXT("runtime"));return true;}),60.f);}   // i18n:skip
  UE_LOG(LogTemp,Display,TEXT("MARE_PSO warmup_start active=%u overlay=%d"),W.Peak,bOverlay?1:0);   // i18n:skip
  W.Tick=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float){
   FWarm& W=Warm();const uint32 N=PipelineStateCache::NumActivePrecacheRequests();const double Now=FPlatformTime::Seconds(),T=Now-W.Start;
   W.Peak=FMath::Max(W.Peak,N);
   if(W.Peak>0)W.Progress=FMath::Max(W.Progress,1.f-float(N)/float(W.Peak));
   W.QuietSince=N>0?-1.0:(W.QuietSince<0?Now:W.QuietSince);
   // The page only when it is worth it: half a second in and still compiling (a warm driver cache never shows it).
   if(W.bOverlay && !W.bTitleGone && !W.Page.IsValid() && N>0 && T>.5 && GEngine && GEngine->GameViewport)
   {W.Page=WarmWidget();GEngine->GameViewport->AddViewportWidgetContent(W.Page.ToSharedRef(),60);}
   if((T>1.0 && W.QuietSince>=0 && Now-W.QuietSince>=.75) || T>150.0){W.Progress=1.f;W.Tick.Reset();FinishWarmup();return false;}
   return true;}),.1f);
 }

 void EndWarmup()
 {
  FWarm& W=Warm();W.bTitleGone=true;DropPage();
 }

 void Register()
 {
  FCoreUObjectDelegates::PreLoadMap.AddLambda([](const FString&){
   if(GIsEditor || IsRunningDedicatedServer() || !IsMoviePlayerEnabled() || !GetMoviePlayer())return;
   FLoadingScreenAttributes A;A.bAutoCompleteWhenLoadingCompletes=true;A.MinimumLoadingScreenDisplayTime=1.5f;A.bMoviesAreSkippable=false;
   A.WidgetLoadingScreen=Widget();
   GetMoviePlayer()->SetupLoadingScreen(A);});
 }
}
