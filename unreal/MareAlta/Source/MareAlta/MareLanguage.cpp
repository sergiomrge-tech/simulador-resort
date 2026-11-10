#include "MareLanguage.h"
#include "MareGamepad.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "MareOptions.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Texture2D.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "ImageUtils.h"
#include "Internationalization/Culture.h"
#include "Internationalization/Internationalization.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace MareLanguage
{
 FString TrIn(const FString& Culture,const FString& Portuguese)
 {
  if(Culture==TEXT("pt-BR"))return Portuguese;   // i18n:skip
  static TMap<FString,TSharedPtr<FJsonObject>> Tables;
  TSharedPtr<FJsonObject>& Table=Tables.FindOrAdd(Culture);
  if(!Table.IsValid()){
   FString Json;TSharedPtr<FJsonObject> Doc;const TSharedPtr<FJsonObject>* Strings=nullptr;
   const FString Path=FPaths::ProjectContentDir()/TEXT("Localization/Mare")/(Culture+TEXT(".json"));   // i18n:skip
   if(FFileHelper::LoadFileToString(Json,*Path) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Doc) && Doc.IsValid()
      && Doc->TryGetObjectField(TEXT("strings"),Strings))Table=*Strings;   // i18n:skip
   else Table=MakeShared<FJsonObject>();
  }
  FString Out;return Table->TryGetStringField(Portuguese,Out) && !Out.IsEmpty()?Out:Portuguese;
 }

 namespace
 {
  /** Flag of a culture: Content/UI/Flags/<culture>.png (flagcdn.com, public domain; CREDITS.md), staged as a plain file. */
  const FSlateBrush* Flag(const FString& Culture)
  {
   static TMap<FString,TSharedPtr<FSlateBrush>> Brushes;static TArray<TStrongObjectPtr<UTexture2D>> Keep;
   if(const TSharedPtr<FSlateBrush>* Found=Brushes.Find(Culture))return Found->Get();
   TSharedPtr<FSlateBrush> Brush;
   if(UTexture2D* Tex=FImageUtils::ImportFileAsTexture2D(FPaths::ProjectContentDir()/TEXT("UI/Flags")/(Culture+TEXT(".png")))){   // i18n:skip
    Keep.Emplace(Tex);Brush=MakeShared<FSlateBrush>();Brush->SetResourceObject(Tex);Brush->ImageSize=FVector2D(120,80);Brush->DrawAs=ESlateBrushDrawType::Image;}
   Brushes.Add(Culture,Brush);return Brush.Get();
  }
  /** The title painting behind the page (the menu under it stays hidden). */
  const FSlateBrush* Art()
  {
   static TStrongObjectPtr<UTexture2D> Tex;static FSlateBrush Brush;
   if(!Tex.IsValid())if(UTexture2D* T=LoadObject<UTexture2D>(nullptr,TEXT("/Game/UI/Title/T_TitleArt.T_TitleArt")))Tex.Reset(T);   // i18n:skip
   if(!Tex.IsValid())return nullptr;
   Brush.SetResourceObject(Tex.Get());Brush.ImageSize=FVector2D(Tex->GetSizeX(),Tex->GetSizeY());Brush.DrawAs=ESlateBrushDrawType::Image;
   return &Brush;
  }
  /** The player's system language when the game has it (en-US -> en, zh-CN -> zh-Hans, pt -> pt-BR), else the saved one. */
  FString Guess()
  {
   const FMareOptions& Options=FMareOptions::Get();const TArray<FString>& List=FMareOptions::Cultures();
   if(FPaths::FileExists(FMareOptions::DefaultPath()) && Options.Culture!=TEXT("pt-BR"))return Options.Culture;   // i18n:skip
   const FString Os=FInternationalization::Get().GetDefaultLanguage()->GetName();
   for(const FString& C:List)if(Os.Equals(C,ESearchCase::IgnoreCase))return C;
   if(Os.StartsWith(TEXT("zh")) && List.Contains(TEXT("zh-Hans")))return TEXT("zh-Hans");   // i18n:skip
   if(Os.StartsWith(TEXT("pt-PT")) && List.Contains(TEXT("pt-PT")))return TEXT("pt-PT");   // i18n:skip
   if(Os.StartsWith(TEXT("pt")))return TEXT("pt-BR");   // i18n:skip
   for(const FString& C:List)if(Os.StartsWith(C+TEXT("-"),ESearchCase::IgnoreCase))return C;
   return Options.Culture;
  }
 }

 class SMareLanguagePage : public SCompoundWidget
 {
 public:
  SLATE_BEGIN_ARGS(SMareLanguagePage){} SLATE_ARGUMENT(TFunction<void(const FString&)>,OnConfirm) SLATE_END_ARGS()
  virtual bool SupportsKeyboardFocus()const override{return true;}
  TSharedPtr<SWidget> FocusTarget()const{const TWeakPtr<SButton>* B=Buttons.Find(Selected);if(B && B->IsValid())return B->Pin();return ConfirmButton;}
  FString Selected;
  void Construct(const FArguments& Args)
  {
   using namespace MareNotebook;
   OnConfirm=Args._OnConfirm;Selected=Guess();
   static const FSlateRoundedBoxBrush TileBrush(Hex(252,245,228),10.f,Hex(170,140,96,.7f),1.5f);
   static const FSlateRoundedBoxBrush TileHover(Hex(255,250,236),10.f,Hex(214,150,80),2.5f);
   static const FSlateRoundedBoxBrush TileOn(Hex(255,240,214),10.f,Hex(238,124,30),4.f);
   static const FSlateRoundedBoxBrush BarBrush(Hex(66,36,20,.97f),FVector4(16,16,0,0));
   static const FSlateRoundedBoxBrush SheetBrush(Hex(250,241,220,.98f),FVector4(0,0,16,16));
   static const FSlateRoundedBoxBrush FlagEdge(Hex(60,40,25,.55f),3.f);
   static const FButtonStyle TileStyle=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateNoResource()).SetPressed(FSlateNoResource())
    .SetNormalPadding(FMargin(0)).SetPressedPadding(FMargin(0));
   static const FButtonStyle ConfirmStyle=FButtonStyle()
    .SetNormal(FSlateRoundedBoxBrush(Hex(196,96,28),14.f,Hex(255,226,170,.9f),2.5f))
    .SetHovered(FSlateRoundedBoxBrush(Hex(226,124,44),14.f,Hex(255,246,214),3.5f))
    .SetPressed(FSlateRoundedBoxBrush(Hex(150,70,20),14.f,Hex(255,246,214),3.5f));
   const int32 Columns=7;
   TSharedRef<SUniformGridPanel> Grid=SNew(SUniformGridPanel).SlotPadding(FMargin(7.f));
   const TArray<FString>& List=FMareOptions::Cultures();
   for(int32 I=0;I<List.Num();++I){
    const FString Culture=List[I];
    TSharedPtr<SButton> Button;
    Grid->AddSlot(I%Columns,I/Columns)[SAssignNew(Button,SMarePadButton).ButtonStyle(&TileStyle).ContentPadding(FMargin(0))
     .OnClicked_Lambda([this,Culture](){
      // A second click on the selected tile confirms (like a double click); the first one only selects.
      if(Selected==Culture && FPlatformTime::Seconds()-LastClick<.45)Confirm();
      Selected=Culture;LastClick=FPlatformTime::Seconds();return FReply::Handled();})
     [SNew(SBox).WidthOverride(134).HeightOverride(146)
      [SNew(SBorder).Padding(FMargin(7,10,7,6)).BorderImage_Lambda([this,Culture]()->const FSlateBrush*{
        if(Selected==Culture)return &TileOn;const TWeakPtr<SButton>* B=Buttons.Find(Culture);
        return B && B->IsValid() && (B->Pin()->IsHovered() || B->Pin()->HasKeyboardFocus())?&TileHover:&TileBrush;})
       [SNew(SVerticalBox)
        +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(SBorder).BorderImage(&FlagEdge).Padding(1.5f)
         [SNew(SBox).WidthOverride(102).HeightOverride(68)[SNew(SImage).Image(Flag(Culture))]]]
        // Names break only before "(" (Português / (Brasil)): automatic wrapping split 日本語 inside the word.
        +SVerticalBox::Slot().FillHeight(1).HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(0,6,0,0)[SNew(STextBlock)
         .Text(FText::AsCultureInvariant(FMareOptions::CultureName(Culture).ToString().Replace(TEXT(" ("),TEXT("\n("))))   // i18n:skip
         .Font(Body(14.f,true)).ColorAndOpacity(Ink).Justification(ETextJustify::Center)]]]]];
    Buttons.Add(Culture,Button);
   }
   auto Say=[this](const TCHAR* Portuguese,bool bUpper){const FString Pt(Portuguese);
    return TAttribute<FText>::CreateLambda([this,Pt,bUpper](){const FText T=FText::FromString(TrIn(Selected,Pt));return bUpper?T.ToUpper():T;});};
   ChildSlot[SNew(SOverlay)
    +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Hex(24,36,44))]
    +SOverlay::Slot()[Art()?StaticCastSharedRef<SWidget>(SNew(SScaleBox).Stretch(EStretch::ScaleToFill)[SNew(SImage).Image(Art())]):SNullWidget::NullWidget]
    +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(0,0,0,.42f))]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(16)
    [SNew(SScaleBox).Stretch(EStretch::ScaleToFit).StretchDirection(EStretchDirection::DownOnly)
     [SNew(SVerticalBox)
      +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(&BarBrush).Padding(FMargin(24,12)).HAlign(HAlign_Center)
       [SNew(STextBlock).Text(Say(TEXT("Escolha seu idioma"),true)).Font(Hand(40)).ColorAndOpacity(Hex(255,240,206))]]
      +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(&SheetBrush).Padding(FMargin(26,20,26,24))
       [SNew(SVerticalBox)
        +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[Grid]
        +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,16,0,0)[SNew(STextBlock)
         .Text(Say(TEXT("Você pode mudar depois em Opções."),false)).Font(Body(17)).ColorAndOpacity(Ink)]
        +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,14,0,0)[SNew(SBox).MinDesiredWidth(380).HeightOverride(72)
         [SAssignNew(ConfirmButton,SMarePadButton).ButtonStyle(&ConfirmStyle).HAlign(HAlign_Center).VAlign(VAlign_Center).ContentPadding(FMargin(34,6))
          .OnClicked_Lambda([this](){Confirm();return FReply::Handled();})
          [SNew(STextBlock).Text(Say(TEXT("Confirmar"),true)).Font(Hand(34)).ColorAndOpacity(Hex(255,246,214))
           .ShadowOffset(FVector2D(1.5f,1.5f)).ShadowColorAndOpacity(FLinearColor(0,0,0,.4f))]]]]]]]];
  }
  virtual FReply OnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override
  {
   if(Event.GetKey()==EKeys::Enter || Event.GetKey()==EKeys::Gamepad_Special_Right){Confirm();return FReply::Handled();}
   return SCompoundWidget::OnKeyDown(Geometry,Event);
  }
 private:
  TFunction<void(const FString&)> OnConfirm;
  TMap<FString,TWeakPtr<SButton>> Buttons;
  TSharedPtr<SButton> ConfirmButton;
  double LastClick=0;
  bool bDone=false;
  void Confirm(){if(bDone)return;bDone=true;if(OnConfirm)OnConfirm(Selected);}
 public:
  /** QA: selects a tile as a click would ("mare.ShowUI language:en"). */
  void Select(const FString& Culture){if(FMareOptions::Cultures().Contains(Culture))Selected=Culture;}
 };

 namespace
 {
  TSharedPtr<SMareLanguagePage>& Page(){static TSharedPtr<SMareLanguagePage> P;return P;}
 }

 bool ShouldAsk()
 {
  const TCHAR* Cmd=FCommandLine::Get();FString Arg;
  return !GIsEditor && !FMareOptions::IsQARun() && !FMareOptions::Get().bLanguageChosen && !FParse::Param(Cmd,TEXT("MareSkipMenu"))
   && !FParse::Value(Cmd,TEXT("culture="),Arg) && FMareOptions::Cultures().Num()>1;
 }
 bool IsOpen(){return Page().IsValid();}
 void QASelect(const FString& Culture){if(Page().IsValid())Page()->Select(Culture);}
 void Close()
 {
  if(!Page().IsValid())return;
  const TSharedPtr<SWidget> Root=Page();Page().Reset();
  MareGamepad::PopMenu(Root);
  if(GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(Root.ToSharedRef());
 }
 void Show(APlayerController* PC,TFunction<void()> OnDone)
 {
  if(!PC || !GEngine || !GEngine->GameViewport || Page().IsValid())return;
  const TSharedRef<SMareLanguagePage> W=SNew(SMareLanguagePage).OnConfirm([OnDone](const FString& Culture){
   FMareOptions Options=FMareOptions::Get();Options.Culture=Culture;Options.bLanguageChosen=true;FMareOptions::Set(Options);
   FMareOptions::Get().ApplyCulture();
   UE_LOG(LogTemp,Display,TEXT("MARE_LANGUAGE chosen=%s now=%s"),*Culture,*FInternationalization::Get().GetCurrentCulture()->GetName());   // i18n:skip
   const TFunction<void()> Done=OnDone;   // the page (and this lambda) goes away in Close
   Close();if(Done)Done();});
  Page()=W;
  GEngine->GameViewport->AddViewportWidgetContent(W,55);
  MareGamepad::PushMenu(W,[](){});   // there is no going back from the first page: a language has to be chosen
  const TSharedPtr<SWidget> Focus=W->FocusTarget();
  PC->SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Focus.IsValid()?Focus:StaticCastSharedRef<SWidget>(W)));
  PC->bShowMouseCursor=true;
  UE_LOG(LogTemp,Display,TEXT("MARE_LANGUAGE page selected=%s os=%s"),*W->Selected,*FInternationalization::Get().GetDefaultLanguage()->GetName());   // i18n:skip
 }
}
