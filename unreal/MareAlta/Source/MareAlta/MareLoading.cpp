#include "MareLoading.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "MoviePlayer.h"
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
  /** A tip at random from Content/Data/tutorial.json (title and text, translated). */
  void Tip(FString& Title,FString& Text)
  {
   FString Json;TSharedPtr<FJsonObject> Doc;const TSharedPtr<FJsonObject>* Tips=nullptr;
   if(!FFileHelper::LoadFileToString(Json,*(FPaths::ProjectContentDir()/TEXT("Data/tutorial.json"))) ||
      !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Doc) || !Doc.IsValid() || !Doc->TryGetObjectField(TEXT("tips"),Tips))return;
   TArray<TSharedPtr<FJsonObject>> List;for(const auto& Pair:(*Tips)->Values)if(Pair.Value->Type==EJson::Object)List.Add(Pair.Value->AsObject());
   if(List.IsEmpty())return;
   const auto Pick=List[FMath::RandRange(0,List.Num()-1)];
   Title=MareLoc::Tr(Pick->GetStringField(TEXT("title")));Text=MareLoc::Tr(Pick->GetStringField(TEXT("text")));
  }
  TSharedRef<SWidget> Widget()
  {
   if(!Art().IsValid())if(UTexture2D* T=LoadObject<UTexture2D>(nullptr,TEXT("/Game/UI/Title/T_TitleArt.T_TitleArt")))Art().Reset(T);
   FSlateBrush& Brush=ArtBrush();
   if(Art().IsValid()){Brush.SetResourceObject(Art().Get());Brush.ImageSize=FVector2D(Art()->GetSizeX(),Art()->GetSizeY());Brush.DrawAs=ESlateBrushDrawType::Image;}
   FString Title,Text;Tip(Title,Text);
   const TSharedRef<SVerticalBox> Page=SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(MareLoc::Tr(TEXT("Dica")) + (Title.IsEmpty()?FString():TEXT(" · ")+Title)))
      .Font(MareNotebook::Hand(26)).ColorAndOpacity(MareNotebook::Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,10)[SNew(STextBlock).Text(FText::FromString(Text)).Font(MareNotebook::Body(15)).ColorAndOpacity(MareNotebook::Ink).AutoWrapText(true)]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)[SNew(STextBlock).Text(FText::FromString(MareLoc::Tr(TEXT("Carregando...")))).Font(MareNotebook::Hand(20)).ColorAndOpacity(MareNotebook::Tag)];
   return SNew(SOverlay)
    +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Hex(24,36,44))]
    +SOverlay::Slot()[SNew(SScaleBox).Stretch(EStretch::ScaleToFill)[SNew(SImage).Image(Art().IsValid()?&Brush:nullptr)]]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,48)
     [SNew(SBox).WidthOverride(640)[MareNotebook::Page(Page)]];
  }
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
