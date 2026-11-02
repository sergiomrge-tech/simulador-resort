#include "MareGame.h"
#include "MarePlayerPresentation.h"
#include "MareHomeWorld.h"
#include "MareVillageWorld.h"
#include "MareIntro.h"
#include "MareIntroQA.h"
#include "MareGraphicsQA.h"
#include "EngineUtils.h"
#include "MarePreviewQA.h"
#include "MareAudioWorld.h"
#include "MareCustomWorld.h"
#include "MareKioskWorld.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MareServiceTarget.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Canvas.h"
#include "CanvasItem.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/UserInterfaceSettings.h"
#include "GameFramework/GameUserSettings.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/SLeafWidget.h"
#include "Fonts/CompositeFont.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SNullWidget.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Widgets/Images/SImage.h"
#include "MareGameRoom.h"
#include "Engine/Texture2D.h"

namespace MareUI
{
 /** Wrap compact HUD text into the space left beside the portable phone. */
 void HUDLine(UCanvas* Canvas,UFont* Font,const FString& Value,FLinearColor Color,float& Y,float Width)
 {
  TArray<FString> Words;Value.ParseIntoArrayWS(Words);FString Current;
  auto Draw=[&](){
   FCanvasTextItem Item(FVector2D(22,Y),FText::FromString(Current),Font,Color);
   Item.EnableShadow(FLinearColor::Black);Canvas->DrawItem(Item);Y+=22;Current.Empty();
  };
  for(const auto& Word:Words){
   const FString Candidate=Current.IsEmpty()?Word:Current+TEXT(" ")+Word;float XSize,YSize;
   Canvas->StrLen(Font,Candidate,XSize,YSize);
   if(!Current.IsEmpty() && XSize>Width)Draw();
   Current=Current.IsEmpty()?Word:Current+TEXT(" ")+Word;
  }
  if(!Current.IsEmpty())Draw();
 }
 static const FSlateRoundedBoxBrush Phone(FLinearColor(.035f,.055f,.05f),24.f);
 static const FSlateRoundedBoxBrush Surface(FLinearColor(.94f,.94f,.90f),18.f);
 static const FSlateRoundedBoxBrush Card(FLinearColor(.99f,.99f,.97f),10.f);
 static const FButtonStyle ActionButton=FButtonStyle()
  .SetNormal(FSlateRoundedBoxBrush(FLinearColor(FColor(47,158,143)),8.f))
  .SetHovered(FSlateRoundedBoxBrush(FLinearColor(FColor(62,178,163)),8.f))
  .SetPressed(FSlateRoundedBoxBrush(FLinearColor(FColor(35,125,113)),8.f));
 TSharedRef<STextBlock> Text(const FString& Value,int32 Size=14,FLinearColor Color=FLinearColor(.08f,.12f,.11f))
 {
  return SNew(STextBlock).Text(FText::FromString(Value)).Font(FCoreStyle::GetDefaultFontStyle("Regular",Size)).ColorAndOpacity(Color).AutoWrapText(true);
 }
 TSharedRef<STextBlock> LiveText(TFunction<FString()> Value,int32 Size=14)
 {
  return SNew(STextBlock).Text_Lambda([Value](){return FText::FromString(Value());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",Size)).ColorAndOpacity(FLinearColor(.08f,.12f,.11f)).AutoWrapText(true);
 }
}
namespace MareTropical
{
 /** "Maré Tropical" palette chosen by the user (proposal B) with C-style side tabs on the phone. */
 FLinearColor Hex(uint8 R,uint8 G,uint8 B,float A=1.f){FLinearColor C(FColor(R,G,B));C.A=A;return C;}
 const FSlateRoundedBoxBrush& Plank(){static const FSlateRoundedBoxBrush B(Hex(116,74,43),0.f,Hex(78,47,26),3.f);return B;}
 /** White HUD icons (tools/ue58/gen_hud_icons.py -> /Game/UI/Icons), tinted by the widget; the fonts have no ★ or bed glyph. */
 const FSlateBrush& Icon(const TCHAR* Name)
 {
  static TMap<FString,TSharedPtr<FSlateBrush>> Cache;auto& B=Cache.FindOrAdd(Name);
  if(!B.IsValid()){B=MakeShared<FSlateBrush>();B->ImageSize=FVector2D(18,18);
   if(auto T=LoadObject<UTexture2D>(nullptr,*FString::Printf(TEXT("/Game/UI/Icons/T_Icon_%s.T_Icon_%s"),Name,Name))){T->AddToRoot();B->SetResourceObject(T);}}   // rooted: the brush cache outlives levels
  return *B;
 }
 const FSlateRoundedBoxBrush& Coin(){static const FSlateRoundedBoxBrush B(Hex(255,207,92),9.f,Hex(176,124,31),2.f);return B;}
 const FSlateRoundedBoxBrush& Ticket(){static const FSlateRoundedBoxBrush B(Hex(255,250,238),5.f,Hex(222,196,160),1.f);return B;}
 const FSlateRoundedBoxBrush& TicketStrip(){static const FSlateRoundedBoxBrush B(Hex(233,199,155),2.f);return B;}
 const FSlateRoundedBoxBrush& Note(){static const FSlateRoundedBoxBrush B(Hex(255,243,196),4.f,Hex(214,190,120),1.f);return B;}
 const FSlateRoundedBoxBrush& Pin(){static const FSlateRoundedBoxBrush B(Hex(226,85,63),8.f,Hex(150,40,30),1.5f);return B;}
 const FSlateRoundedBoxBrush& Sign(){static const FSlateRoundedBoxBrush B(Hex(255,250,238),12.f,Hex(199,154,91),4.f);return B;}
 const FSlateRoundedBoxBrush& Toast(){static const FSlateRoundedBoxBrush B(Hex(233,247,243,.96f),10.f,Hex(47,158,143),2.f);return B;}
 const FSlateRoundedBoxBrush& KeyCap(){static const FSlateRoundedBoxBrush B(Hex(255,255,255,.92f),5.f,Hex(90,58,30),1.5f);return B;}
 const FSlateRoundedBoxBrush& Frame(){static const FSlateRoundedBoxBrush B(Hex(27,94,99),22.f,Hex(18,64,68),2.f);return B;}
 const FSlateRoundedBoxBrush& Paper(){static const FSlateRoundedBoxBrush B(Hex(253,246,234),16.f);return B;}
 const FSlateRoundedBoxBrush& Dot(FLinearColor C){static TMap<uint32,TSharedPtr<FSlateRoundedBoxBrush>> Cache;auto& B=Cache.FindOrAdd(C.ToFColor(false).ToPackedARGB());if(!B.IsValid())B=MakeShared<FSlateRoundedBoxBrush>(C,6.f);return *B;}
 const FButtonStyle& NavOn(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateRoundedBoxBrush(Hex(232,121,79),9.f)).SetHovered(FSlateRoundedBoxBrush(Hex(240,138,98),9.f)).SetPressed(FSlateRoundedBoxBrush(Hex(205,100,62),9.f));return S;}
 const FButtonStyle& NavOff(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateRoundedBoxBrush(Hex(255,255,255,.14f),9.f)).SetPressed(FSlateRoundedBoxBrush(Hex(255,255,255,.22f),9.f));return S;}
 FLinearColor TabColor(int32 I){static const FColor C[]={FColor(232,121,79),FColor(47,158,143),FColor(90,123,214),FColor(217,164,59),FColor(201,91,124),FColor(59,143,178),FColor(150,105,190)};return FLinearColor(C[FMath::Clamp(I,0,6)]);}
 float Scale()
 {
  FVector2D View(1280,720);if(GEngine && GEngine->GameViewport)GEngine->GameViewport->GetViewportSize(View);
  const float UIScale=FMath::Max(.1f,GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(FIntPoint(View.X,View.Y)));
  return FMath::Clamp(View.Y/720.f,.75f,1.8f)/UIScale;
 }
 TSharedRef<STextBlock> Txt(const FString& V,int32 Size,FLinearColor C,bool bBold=false,float Wrap=0)
 {
  auto T=SNew(STextBlock).Text(FText::FromString(V)).Font(FCoreStyle::GetDefaultFontStyle(bBold?"Bold":"Regular",Size)).ColorAndOpacity(C);
  if(Wrap>0)T->SetWrapTextAt(Wrap);
  return T;
 }
 TSharedRef<SWidget> Key(const FString& K){return SNew(SBorder).BorderImage(&KeyCap()).Padding(FMargin(7,2))[Txt(K,12,Hex(90,58,30),true)];}
 FSlateRenderTransform Tilt(float Degrees){return FSlateRenderTransform(FQuat2D(FMath::DegreesToRadians(Degrees)));}
}
/** "Caderno do Quiosque" (phone option 3, chosen by the user on 01/11): kraft cover, notebook divider tabs,
 *  lined paper, handwriting, price tags and an EM USO stamp. Fonts are OFL files in Content/UI/Fonts. */
namespace MareNotebook
{
 using MareTropical::Hex;
 const FLinearColor Kraft=Hex(227,207,166),Paper=Hex(255,251,240),Rule=Hex(222,233,240),Margin=Hex(233,166,160),Ink=Hex(46,32,20),
  Brown=Hex(122,59,28),Faded=Hex(107,78,46),Pencil=Hex(128,104,76),Green=Hex(70,104,48),Red=Hex(178,58,40),Tag=Hex(255,243,201),
  TagEdge=Hex(201,168,106),Marker=Hex(255,229,138);
 const FLinearColor& TabColor(int32 I){static const FLinearColor C[]={Hex(246,185,168),Hex(191,224,196),Hex(188,215,238),Hex(247,220,142),Hex(216,195,238),Hex(243,199,156),Hex(206,226,170)};return C[FMath::Clamp(I,0,6)];}
 FSlateFontInfo Font(const TCHAR* File,float Size,const char* Fallback)
 {
  static TMap<FString,TSharedPtr<const FCompositeFont>> Cache;
  if(!Cache.Contains(File)){const FString Path=FPaths::ProjectContentDir()/TEXT("UI/Fonts")/File;
   TSharedPtr<const FCompositeFont> Loaded;if(FPaths::FileExists(Path))Loaded=MakeShared<FStandaloneCompositeFont>(NAME_None,Path,EFontHinting::Default,EFontLoadingPolicy::LazyLoad);Cache.Add(File,Loaded);}
  const auto& Composite=Cache[File];return Composite.IsValid()?FSlateFontInfo(Composite,Size):FCoreStyle::GetDefaultFontStyle(Fallback,Size);
 }
 FSlateFontInfo Hand(float Size){return Font(TEXT("PatrickHand-Regular.ttf"),Size,"Regular");}
 FSlateFontInfo Body(float Size,bool bBold=false){return Font(bBold?TEXT("Nunito-ExtraBold.ttf"):TEXT("Nunito-SemiBold.ttf"),Size,bBold?"Bold":"Regular");}
 const FSlateRoundedBoxBrush& Cover(){static const FSlateRoundedBoxBrush B(Kraft,18.f);return B;}
 const FSlateRoundedBoxBrush& Sheet(){static const FSlateRoundedBoxBrush B(Paper,FVector4(0,12,0,0));return B;}
 const FSlateRoundedBoxBrush& TabBrush(const FLinearColor& C){static TMap<uint32,TSharedPtr<FSlateRoundedBoxBrush>> Cache;auto& B=Cache.FindOrAdd(C.ToFColor(false).ToPackedARGB());if(!B.IsValid())B=MakeShared<FSlateRoundedBoxBrush>(C,FVector4(10,10,0,0));return *B;}
 const FSlateRoundedBoxBrush& TagBrush(){static const FSlateRoundedBoxBrush B(Tag,FVector4(6,22,6,6),TagEdge,1.5f);return B;}
 const FSlateRoundedBoxBrush& TagShadow(){static const FSlateRoundedBoxBrush B(Hex(217,195,151),FVector4(6,22,6,6));return B;}
 const FSlateRoundedBoxBrush& Hole(){static const FSlateRoundedBoxBrush B(Kraft,5.f,Hex(168,134,84),1.5f);return B;}
 const FSlateRoundedBoxBrush& StampBrush(const FLinearColor& C){static TMap<uint32,TSharedPtr<FSlateRoundedBoxBrush>> Cache;auto& B=Cache.FindOrAdd(C.ToFColor(false).ToPackedARGB());if(!B.IsValid())B=MakeShared<FSlateRoundedBoxBrush>(FLinearColor::Transparent,6.f,C,2.5f);return *B;}
 const FSlateRoundedBoxBrush& MarkerBrush(){static const FSlateRoundedBoxBrush B(Marker,3.f);return B;}
 const FSlateRoundedBoxBrush& Note(){static const FSlateRoundedBoxBrush B(Hex(255,236,150),4.f,Hex(214,190,120),1.f);return B;}
 const FButtonStyle& InkButton(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateRoundedBoxBrush(Brown,5.f)).SetHovered(FSlateRoundedBoxBrush(Hex(146,76,40),5.f)).SetPressed(FSlateRoundedBoxBrush(Hex(92,42,18),5.f)).SetDisabled(FSlateRoundedBoxBrush(Hex(190,170,140),5.f));return S;}
 const FButtonStyle& Plain(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateRoundedBoxBrush(Hex(255,229,138,.55f),3.f)).SetPressed(FSlateRoundedBoxBrush(Marker,3.f));return S;}
 TSharedRef<STextBlock> HandText(const FString& V,float Size,const FLinearColor& C=Ink){return SNew(STextBlock).Text(FText::FromString(V)).Font(Hand(Size)).ColorAndOpacity(C).AutoWrapText(true);}
 TSharedRef<STextBlock> BodyText(const FString& V,float Size=12,const FLinearColor& C=Ink,bool bBold=false){return SNew(STextBlock).Text(FText::FromString(V)).Font(Body(Size,bBold)).ColorAndOpacity(C).AutoWrapText(true);}
 /** Rubber stamp (EM USO, CONTRATADO, SEU): red or green ink, slightly crooked. */
 TSharedRef<SWidget> Stamp(const FString& V,const FLinearColor& C=Red)
 {
  return SNew(SBox).HAlign(HAlign_Left)[SNew(SBorder).BorderImage(&StampBrush(C)).Padding(FMargin(8,0)).RenderTransform(MareTropical::Tilt(-7)).RenderTransformPivot(FVector2D(.5f))[HandText(V,18,C)]];
 }
 /** Paper price tag with the string hole and a solid shadow; tilt in degrees. */
 TSharedRef<SWidget> PriceTag(TSharedRef<SWidget> Content,float Tilt=0,const FString& Tooltip=FString())
 {
  return SNew(SBox).Padding(FMargin(2,4,6,8)).ToolTipText(Tooltip.IsEmpty()?FText::GetEmpty():FText::FromString(Tooltip))[SNew(SOverlay).RenderTransform(MareTropical::Tilt(Tilt)).RenderTransformPivot(FVector2D(.5f))
   +SOverlay::Slot().Padding(FMargin(3,4,-3,-4))[SNew(SBorder).BorderImage(&TagShadow())]
   +SOverlay::Slot()[SNew(SBorder).BorderImage(&TagBrush()).Padding(FMargin(12,14,10,10))[Content]]
   +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(FMargin(0,7,10,0))[SNew(SBox).WidthOverride(10).HeightOverride(10)[SNew(SBorder).BorderImage(&Hole())]]];
 }
}
/** Lined notebook paper with the red margin; drawn behind the scrolling page. */
class SPaperLines : public SLeafWidget
{
public:
 SLATE_BEGIN_ARGS(SPaperLines):_MarginX(0){} SLATE_ATTRIBUTE(float,MarginX) SLATE_END_ARGS()
 void Construct(const FArguments& Args){MarginX=Args._MarginX;}
 virtual FVector2D ComputeDesiredSize(float)const override{return FVector2D(10,10);}
 virtual int32 OnPaint(const FPaintArgs&,const FGeometry& Geometry,const FSlateRect&,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle&,bool)const override
 {
  const FVector2f Size=FVector2f(Geometry.GetLocalSize());
  FSlateDrawElement::MakeBox(Out,Layer,Geometry.ToPaintGeometry(),&MareNotebook::Sheet());
  for(float Y=34;Y<Size.Y;Y+=28)FSlateDrawElement::MakeLines(Out,Layer+1,Geometry.ToPaintGeometry(),TArray<FVector2f>{FVector2f(0,Y),FVector2f(Size.X,Y)},ESlateDrawEffect::None,MareNotebook::Rule,true,1.f);
  const float X=MarginX.Get();if(X>0)FSlateDrawElement::MakeLines(Out,Layer+1,Geometry.ToPaintGeometry(),TArray<FVector2f>{FVector2f(X,0),FVector2f(X,Size.Y)},ESlateDrawEffect::None,MareNotebook::Margin,true,2.f);
  return Layer+1;
 }
private:
 TAttribute<float> MarginX;
};
class SMarePhone : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMarePhone){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_ARGUMENT(int32,Tab) SLATE_ARGUMENT(FName,Station) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  Owner=Args._Owner;Tab=Args._Tab;Station=Args._Station; Rebuild();
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)override
 {
  if(Event.GetKey()==EKeys::Escape && Owner.IsValid()){Owner->ClosePhone();return FReply::Handled();}
  return SCompoundWidget::OnKeyDown(Geometry,Event);
 }
private:
 TWeakObjectPtr<AMareController> Owner;
 TSharedPtr<SVerticalBox> Body;
 TSharedPtr<SEditableTextBox> CompanyName;
 int32 Tab=0;
 FName Station;
 FString Place=TEXT("kiosk");
 /** Reception: the nightly price the player is about to ask each waiting guest (starts at the guest's offer). */
 TMap<FString,double> Ask;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 // ---- Where the page goes: exactly over the glass of the 3D phone, else a fixed sheet.
 // Viewport pixels -> units inside the DPI scaler: measured from this widget, so monitor DPI is included.
 float UnitsPerPixel=1.f;
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta)override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);FVector2D View(0);if(GEngine && GEngine->GameViewport)GEngine->GameViewport->GetViewportSize(View);
  if(View.X>0)UnitsPerPixel=Geometry.GetLocalSize().X/View.X/MareTropical::Scale();
 }
 FSlateRect ScreenRect()const
 {
  FVector2D Min,Max;auto Hero=Owner.IsValid()?Cast<AMareCharacter>(Owner->GetPawn()):nullptr;
  if(Station.IsNone() && Hero && Hero->PhoneScreenRect(Min,Max)){const float U=UnitsPerPixel;return FSlateRect(Min.X*U,Min.Y*U,Max.X*U,Max.Y*U);}
  return Station.IsNone()?FSlateRect(40,90,1000,500):FSlateRect(36,110,516,560);
 }
 // ---- Building blocks of the page.
 TSharedRef<SWidget> Button(const FString& Label,TFunction<void()> Action,bool bEnabled=true)
 {
  return SNew(SButton).ButtonStyle(&MareNotebook::InkButton()).IsEnabled(bEnabled).ContentPadding(FMargin(9,2)).OnClicked_Lambda([this,Action](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.16f);Action();Rebuild();return FReply::Handled();})
   [SNew(STextBlock).Text(FText::FromString(Label)).Font(MareNotebook::Hand(16)).ColorAndOpacity(MareNotebook::Tag)];
 }
 /** Underlined handwritten link ("espiar", "dispensar"). */
 TSharedRef<SWidget> Link(const FString& Label,TFunction<void()> Action)
 {
  return SNew(SButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(3,0)).OnClicked_Lambda([this,Action](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.16f);Action();Rebuild();return FReply::Handled();})
   [SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(Label,16,MareNotebook::Brown)]+SVerticalBox::Slot().AutoHeight()[SNew(SBox).HeightOverride(1.5f)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Brown)]]];
 }
 void Title(const FString& V,const FString& Note=FString())
 {
  auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom).Padding(0,0,14,0)[SNew(STextBlock).Text(FText::FromString(V)).Font(MareNotebook::Hand(30)).ColorAndOpacity(MareNotebook::Ink)];
  if(!Note.IsEmpty())Row->AddSlot().FillWidth(1).VAlign(VAlign_Bottom).Padding(0,0,0,4)[MareNotebook::HandText(Note,17,MareNotebook::Green)];
  Body->AddSlot().AutoHeight().Padding(0,0,0,4)[Row];
 }
 void Heading(const FString& V,const FString& Note=FString())
 {
  auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom).Padding(0,0,8,0)[SNew(STextBlock).Text(FText::FromString(V)).Font(MareNotebook::Hand(22)).ColorAndOpacity(MareNotebook::Brown)];
  if(!Note.IsEmpty())Row->AddSlot().FillWidth(1).VAlign(VAlign_Bottom).Padding(0,0,0,2)[MareNotebook::HandText(Note,16,MareNotebook::Pencil)];
  Body->AddSlot().AutoHeight().Padding(0,10,0,2)[Row];
 }
 void Line(const FString& V,float Size=12,const FLinearColor& C=MareNotebook::Ink){Body->AddSlot().AutoHeight().Padding(0,2)[MareNotebook::BodyText(V,Size,C)];}
 void Pencil(const FString& V){Body->AddSlot().AutoHeight().Padding(0,2)[MareNotebook::HandText(V,17,MareNotebook::Pencil)];}
 /** N price tags per row; each tag gets a small fixed tilt so the page looks hand-pinned. */
 TSharedRef<SUniformGridPanel> Grid(){auto G=SNew(SUniformGridPanel).SlotPadding(FMargin(4,2));Body->AddSlot().AutoHeight().Padding(0,4)[G];return G;}
 static float TiltOf(int32 I){static const float T[]={-1.2f,.8f,-.5f,1.f,-.8f,.6f};return T[I%6];}
 TSharedRef<SVerticalBox> TagBody(const FString& Top,const FString& Name)
 {
  return SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(Top,15,MareNotebook::Faded)]
   +SVerticalBox::Slot().AutoHeight().Padding(0,1,0,6)[MareNotebook::BodyText(Name,12.5f,MareNotebook::Ink,true)];
 }
 // ---- Pages.
 void KioskPage()
 {
  auto S=Sim();auto Company=UMareSimulation::Object(S->State,TEXT("company"));bool bCreated=false;Company->TryGetBoolField(TEXT("created"),bCreated);
  if(!bCreated){Title(TEXT("Seu quiosque"));
   if(UMareSimulation::Number(S->State,TEXT("ue_intro_stage"),2)<2){Pencil(TEXT("Primeiro, entre na casa e leia a carta que sua avó Dilce deixou para você."));return;}
   Pencil(TEXT("Dê um nome ao quiosque da família:"));
   Body->AddSlot().AutoHeight().Padding(0,4)[SNew(SBox).WidthOverride(320)[SAssignNew(CompanyName,SEditableTextBox).Text(FText::FromString(TEXT("Maré Alta"))).Font(MareNotebook::Hand(20))]];
   Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6)[Button(TEXT("Criar empresa"),[this,S](){S->CreateCompany(CompanyName->GetText().ToString());})];return;}
  bool bRequested=false;Company->TryGetBoolField(TEXT("kiosk_open"),bRequested);auto Hours=UMareSimulation::Object(Company,TEXT("sim"));
  Title(UMareSimulation::String(Company,TEXT("name")).IsEmpty()?FString(TEXT("Quiosque")):UMareSimulation::String(Company,TEXT("name")),
   S->IsOpen()?TEXT("aberto · recebendo clientes"):bRequested?TEXT("abertura ativada · aguardando o horário"):TEXT("fechado · use a placa do balcão"));
  auto G=Grid();bool bHired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bHired);
  G->AddSlot(0,0)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(TEXT("Hoje"),15,MareNotebook::Faded)]
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(19)).ColorAndOpacity(MareNotebook::Green).Text_Lambda([S](){return FText::FromString(FString::Printf(TEXT("entrou R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_in"))));})]
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(19)).ColorAndOpacity(MareNotebook::Red).Text_Lambda([S](){return FText::FromString(FString::Printf(TEXT("saiu R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_out"))));})],TiltOf(0))];
  G->AddSlot(1,0)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(TEXT("Atendimento"),15,MareNotebook::Faded)]
   +SVerticalBox::Slot().AutoHeight()[MareNotebook::BodyText(FString::Printf(TEXT("%.0fh às %.0fh"),UMareSimulation::Number(Hours,TEXT("start"),8),UMareSimulation::Number(Hours,TEXT("end"),18)),12.5f,MareNotebook::Ink,true)]
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(17)).ColorAndOpacity(MareNotebook::Ink).Text_Lambda([S](){return FText::FromString(FString::Printf(TEXT("%d pedidos ativos"),UMareSimulation::Object(S->State,TEXT("ue_orders"))->Values.Num()));})]
   +SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(bHired?TEXT("com atendente"):TEXT("você atende sozinho"),17,MareNotebook::Pencil)],TiltOf(1))];
  if(auto Audio=Owner->GetWorld()->GetSubsystem<UMareAudioWorld>())
   G->AddSlot(2,0)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(TEXT("Rádio"),15,MareNotebook::Faded)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareAudioWorld::RadioName(Audio->GetRadioStation()),12.5f,MareNotebook::Ink,true)]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left)[Button(TEXT("próxima"),[Audio](){Audio->NextRadioStation();})],TiltOf(2))];
  if(!S->Carry().IsEmpty())Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,4)[Button(TEXT("Devolver o produto que está na mão"),[S](){S->ReturnCarry();})];
  Heading(TEXT("Estoque pronto"),TEXT("(pegue na geladeira e no armário do quiosque)"));
  auto Stock=Grid();int32 I=0;
  for(const auto& Id:Products()){auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);
   Stock->AddSlot(I%4,I/4)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::BodyText(UMareSimulation::String(Dish,TEXT("name")),12,MareNotebook::Ink,true)]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(18)).ColorAndOpacity_Lambda([S,Id](){return FSlateColor(S->IsDishUnlocked(Id) && S->Available(Id)>0?MareNotebook::Green:MareNotebook::Red);})
     .Text_Lambda([S,Id](){if(!S->IsDishUnlocked(Id))return FText::FromString(TEXT("precisa de expansão"));const int32 N=S->Available(Id);return FText::FromString(N>0?FString::Printf(TEXT("%d prontos"),N):TEXT("acabou · repor"));})],TiltOf(I))];++I;}
 }
 /** Pousada reception: waiting guests with their offer, ask/counter buttons, and the room board. */
 void ReceptionPage(const FString& Where)
 {
  auto S=Sim();using namespace MareNotebook;S->SyncRooms();const bool bHotel=Where==TEXT("hotel");
  const int32 Free=S->FreeCleanRooms(Where);
  Title(bHotel?TEXT("Recepção do Grand Hotel"):TEXT("Recepção da pousada"));
  Line(FString::Printf(TEXT("%s livres: %d de %d · diária de referência R$ %.0f"),bHotel?TEXT("Suítes"):TEXT("Quartos limpos"),Free,bHotel?32:S->PousadaRooms(),S->StayRate(Where)),13,Faded);
  if(bHotel)Line(TEXT("Quem você não atender em 2 horas, a equipe do hotel recebe pela oferta do hóspede."),12,Faded);
  const TArray<TSharedPtr<FJsonValue>>* All=nullptr;S->Stays()->TryGetArrayField(TEXT("queue"),All);
  TArray<TSharedPtr<FJsonValue>> Mine;if(All)for(const auto& V:*All){const FString P=UMareSimulation::String(V->AsObject(),TEXT("place"));if(P==Where || (P.IsEmpty() && !bHotel))Mine.Add(V);}
  const TArray<TSharedPtr<FJsonValue>>* Queue=&Mine;
  if(Queue->IsEmpty())Line(TEXT("Ninguém esperando agora. Hóspedes chegam entre 10h e 20h."),13,Faded);
  else if(!Free)Line(bHotel?TEXT("Hotel lotado esta noite."):TEXT("Sem quarto limpo: arrume um bangalô para fazer o check-in."),13,Red);
  for(const auto& Value:*Queue){
   const auto G=Value->AsObject();const FString Id=UMareSimulation::String(G,TEXT("id"));
   const double Offer=UMareSimulation::Number(G,TEXT("offer")),Mood=UMareSimulation::Number(G,TEXT("mood"));
   double& Price=Ask.FindOrAdd(Id,Offer);if(Price<Offer)Price=Offer;
   const FString Humor=Mood>.7?TEXT("animado"):Mood>.35?TEXT("hesitante"):TEXT("irritado");
   Heading(FString::Printf(TEXT("%s · %s"),*UMareSimulation::String(G,TEXT("name")),*UMareSimulation::String(G,TEXT("label"))),
    FString::Printf(TEXT("%.0f noite(s) · humor: %s · rodada %.0f de 3"),UMareSimulation::Number(G,TEXT("nights")),*Humor,UMareSimulation::Number(G,TEXT("round"))+1));
   Line(FString::Printf(TEXT("Oferece R$ %.0f por noite. Você pede R$ %.0f."),Offer,Price),14,Ink);
   auto Row=SNew(SHorizontalBox);
   for(const int32 Step:{-10,-5,5,10})Row->AddSlot().AutoWidth().Padding(0,0,6,0)[Button(FString::Printf(TEXT("%+d%%"),Step),[this,Id,Step,Offer](){double& P=Ask.FindOrAdd(Id,Offer);P=FMath::Max(Offer,FMath::RoundToDouble(P*(1+Step/100.)));},true)];
   Row->AddSlot().AutoWidth().Padding(10,0,6,0)[Button(FString::Printf(TEXT("Pedir R$ %.0f"),Price),[this,S,Id](){double Out=0;const double P=Ask.FindRef(Id);
    switch(S->Haggle(Id,P,Out)){
     case UMareSimulation::EHaggle::Accepted:S->LastMessage=FString::Printf(TEXT("Fechado por R$ %.0f a noite. Chave entregue."),Out);Ask.Remove(Id);break;
     case UMareSimulation::EHaggle::Countered:S->LastMessage=FString::Printf(TEXT("Contraproposta: R$ %.0f por noite."),Out);Ask.Add(Id,Out);break;
     case UMareSimulation::EHaggle::Left:Ask.Remove(Id);break;
     default:S->LastMessage=TEXT("Sem quarto limpo livre.");}},Free>0)];
   Row->AddSlot().AutoWidth()[Button(FString::Printf(TEXT("Aceitar R$ %.0f"),Offer),[this,S,Id,Offer](){if(S->AcceptOffer(Id)){S->LastMessage=FString::Printf(TEXT("Check-in por R$ %.0f a noite."),Offer);Ask.Remove(Id);}else S->LastMessage=TEXT("Sem quarto limpo livre.");},Free>0)];
   Body->AddSlot().AutoHeight().Padding(0,2,0,8)[Row];
  }
  if(bHotel)return;   // 32 suites: the hotel crew keeps them; only the pousada shows the room board
  Heading(TEXT("Quartos"));
  const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;S->Stays()->TryGetArrayField(TEXT("rooms"),Rooms);
  if(Rooms)for(int32 I=0;I<Rooms->Num();++I){const auto R=(*Rooms)[I]->AsObject();if(UMareSimulation::String(R,TEXT("place"))==TEXT("hotel"))continue;
   const FString State=UMareSimulation::String(R,TEXT("state"));FString Text;
   if(State==TEXT("occupied"))Text=FString::Printf(TEXT("Bangalô %d · %s · mais %.0f noite(s) · R$ %.0f"),I+1,*UMareSimulation::String(UMareSimulation::Object(R,TEXT("guest")),TEXT("name")),UMareSimulation::Number(R,TEXT("nights")),UMareSimulation::Number(R,TEXT("rate")));
   else if(State==TEXT("dirty")){TArray<FString> Tasks;const TArray<TSharedPtr<FJsonValue>>* T=nullptr;
    if(R->TryGetArrayField(TEXT("tasks"),T))for(const auto& V:*T)Tasks.Add(V->AsString()==TEXT("bed")?TEXT("arrumar a cama"):V->AsString()==TEXT("towels")?TEXT("recolher toalhas"):TEXT("tirar o lixo"));
    Text=FString::Printf(TEXT("Bangalô %d · sujo: %s"),I+1,*FString::Join(Tasks,TEXT(", ")));}
   else Text=FString::Printf(TEXT("Bangalô %d · limpo e livre"),I+1);
   Line(Text,13,State==TEXT("dirty")?Red:State==TEXT("occupied")?Ink:Green);}
 }
 static const TArray<FString>& Products(){static const TArray<FString> P={TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};return P;}
 /** Restock cards; at a station also the "take it ready" button for what that station keeps. */
 void StockPage(bool bPickup)
 {
  auto S=Sim();auto G=Grid();int32 I=0;const int32 Columns=bPickup?2:4;
  for(const auto& Id:Products()){
   if(bPickup && Station==TEXT("Cupboard") && Id!=TEXT("batata_frita") && Id!=TEXT("porcao_peixe") && Id!=TEXT("petiscos"))continue;
   if(bPickup && Station==TEXT("Fridge") && (Id==TEXT("batata_frita") || Id==TEXT("porcao_peixe") || Id==TEXT("petiscos")))continue;
   auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);auto Card=TagBody(FString::Printf(TEXT("%d disponíveis"),S->Available(Id)),UMareSimulation::String(Dish,TEXT("name")));
   if(!S->CanSupplyDish(Id))Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("libere em Resort"),16,MareNotebook::Pencil)];
   else{if(bPickup)Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,0,0,4)[Button(TEXT("Pegar pronto"),[S,Id](){S->Pickup(Id);})];
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("+10 · R$ %.0f"),S->RestockCost(Id)),[S,Id](){S->Restock(Id);})];}
   G->AddSlot(I%Columns,I/Columns)[MareNotebook::PriceTag(Card,TiltOf(I))];++I;}
 }
 void StaffPage()
 {
  auto S=Sim();Title(TEXT("Equipe"),TEXT("salários pagos quando você dorme"));auto Roles=UMareSimulation::Object(S->Definitions,TEXT("staff"));auto G=Grid();int32 I=0;
  for(const TCHAR* Role:{TEXT("atendente"),TEXT("bartender"),TEXT("camareira"),TEXT("guia")}){auto Def=UMareSimulation::Object(Roles,Role);const FString R=Role;
   auto Card=TagBody(FString::Printf(TEXT("R$ %.0f por dia"),UMareSimulation::Number(Def,TEXT("wage"))),UMareSimulation::String(Def,TEXT("name")));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(R==TEXT("atendente")?TEXT("Anota, retira os produtos, entrega e recolhe a louça do quiosque."):UMareSimulation::String(Def,TEXT("blurb")),11,MareNotebook::Faded)];
   const FString Req=UMareSimulation::String(Def,TEXT("req"));bool bOwned=Req.IsEmpty();if(!bOwned)UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Req,bOwned);
   if(S->HasStaff(R))Card->AddSlot().AutoHeight()[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[MareNotebook::Stamp(TEXT("CONTRATADO"),MareNotebook::Green)]+SHorizontalBox::Slot().FillWidth(1).HAlign(HAlign_Right)[Link(TEXT("dispensar"),[S,R](){S->DismissStaff(R);})]];
   else if(!bOwned)Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("precisa: ")+UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("expansions")),Req),TEXT("name")),16,MareNotebook::Pencil)];
   else Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Contratar · R$ %.0f"),UMareSimulation::Number(Def,TEXT("hire"))),[S,R](){if(R==TEXT("atendente"))S->HireAttendant();else S->HireStaff(R);})];
   G->AddSlot(I%2,I/2)[MareNotebook::PriceTag(Card,TiltOf(I))];++I;}
 }
 void FinancePage()
 {
  auto S=Sim();Title(TEXT("Finanças"));auto G=Grid();
  auto Big=[](const FString& Top,const FString& Value,const FLinearColor& C,const FString& Note){return SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(Top,15,MareNotebook::Faded)]
   +SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(Value,28,C)]+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(Note,15,MareNotebook::Pencil)];};
  G->AddSlot(0,0)[MareNotebook::PriceTag(Big(TEXT("Caixa"),FString::Printf(TEXT("R$ %.0f"),S->Money()),S->Money()<0?MareNotebook::Red:MareNotebook::Ink,TEXT("dinheiro do quiosque")),TiltOf(0))];
  G->AddSlot(1,0)[MareNotebook::PriceTag(Big(TEXT("Hoje"),FString::Printf(TEXT("+R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_in"))),MareNotebook::Green,FString::Printf(TEXT("saídas R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_out")))),TiltOf(1))];
  if(S->State->HasTypedField<EJson::Object>(TEXT("ue_last_day"))){auto Last=UMareSimulation::Object(S->State,TEXT("ue_last_day"));const double Profit=UMareSimulation::Number(Last,TEXT("income"))-UMareSimulation::Number(Last,TEXT("expense"));
   G->AddSlot(2,0)[MareNotebook::PriceTag(Big(FString::Printf(TEXT("Dia %.0f"),UMareSimulation::Number(Last,TEXT("day"))),FString::Printf(TEXT("R$ %.0f"),Profit),Profit<0?MareNotebook::Red:MareNotebook::Green,
    FString::Printf(TEXT("%.0f vendas · salários R$ %.0f"),UMareSimulation::Number(Last,TEXT("sales")),UMareSimulation::Number(Last,TEXT("wages")))),TiltOf(2))];}
  Heading(TEXT("Últimos lançamentos"));const TArray<TSharedPtr<FJsonValue>>* Ledger=nullptr;
  if(S->State->TryGetArrayField(TEXT("ledger"),Ledger))for(int32 I=Ledger->Num()-1;I>=FMath::Max(0,Ledger->Num()-14);--I){auto Row=(*Ledger)[I]->AsObject();const double Amount=UMareSimulation::Number(Row,TEXT("amount"));
   Body->AddSlot().AutoHeight().Padding(0,1)[SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[MareNotebook::BodyText(UMareSimulation::String(Row,TEXT("label")),11.5f)]
    +SHorizontalBox::Slot().AutoWidth().Padding(12,0,0,0)[MareNotebook::HandText(FString::Printf(TEXT("%sR$ %.0f"),Amount<0?TEXT("-"):TEXT("+"),FMath::Abs(Amount)),18,Amount<0?MareNotebook::Red:MareNotebook::Green)]];}
 }
 void ResortPage()
 {
  auto S=Sim();bool bHotel=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
  TArray<FString> Today;for(const TCHAR* Id:{TEXT("bar"),TEXT("pool"),TEXT("passeios")})if(S->IsPlaceAvailable(Id))Today.Add(FString::Printf(TEXT("%s R$ %.0f"),*UMareSimulation::String(S->PlaceDef(Id),TEXT("name")),S->OpsToday(Id)));
  Title(TEXT("Resort"),Today.Num()?TEXT("hoje: ")+FString::Join(Today,TEXT(" · ")):FString(TEXT("compre expansões para o resort crescer")));
  if(bHotel){auto Last=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("hotel"));
   Pencil(FString::Printf(TEXT("Grand Hotel 5 estrelas · ocupação prevista %.0f%% · nota %.1f · fama %s"),S->HotelOccupancy()*100,S->Stars(),*S->FameName())+(Last->HasField(TEXT("rooms"))?FString::Printf(TEXT(" · última noite %.0f suítes, R$ %.0f"),UMareSimulation::Number(Last,TEXT("rooms")),UMareSimulation::Number(Last,TEXT("rev"))):FString()));}
  auto Pousada=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("pousada"));
  if(S->PousadaRooms()>0 && Pousada->HasField(TEXT("rooms")))Pencil(FString::Printf(TEXT("Pousada, última noite: %.0f de %.0f quartos · R$ %.0f"),UMareSimulation::Number(Pousada,TEXT("occupied")),UMareSimulation::Number(Pousada,TEXT("rooms")),UMareSimulation::Number(Pousada,TEXT("rev"))));
  Heading(TEXT("Expansões"),TEXT("(cada uma libera uma área nova)"));auto G=Grid();int32 I=0;auto Expansions=UMareSimulation::Object(S->Definitions,TEXT("expansions"));
  TArray<FString> Order;const TArray<TSharedPtr<FJsonValue>>* Listed=nullptr;if(S->Definitions->TryGetArrayField(TEXT("expansion_order"),Listed))for(const auto& V:*Listed)Order.Add(V->AsString());
  for(const auto& Pair:Expansions->Values)Order.AddUnique(FString(Pair.Key.ToView()));
  for(const FString& Id:Order){auto Row=UMareSimulation::Object(Expansions,Id);if(!Expansions->HasField(Id))continue;bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);
   auto Card=TagBody(FString::Printf(TEXT("R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),UMareSimulation::String(Row,TEXT("name")));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareSimulation::String(Row,TEXT("blurb")),10.5f,MareNotebook::Faded)];
   TArray<FString> Missing;const TArray<TSharedPtr<FJsonValue>>* Req=nullptr;if(Row->TryGetArrayField(TEXT("req"),Req))for(const auto& V:*Req){bool bHas=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(V->AsString(),bHas);if(!bHas)Missing.Add(UMareSimulation::String(UMareSimulation::Object(Expansions,V->AsString()),TEXT("name")));}
   if(bOwned)Card->AddSlot().AutoHeight()[MareNotebook::Stamp(TEXT("COMPRADA"),MareNotebook::Green)];
   else if(Missing.Num())Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("antes: ")+FString::Join(Missing,TEXT(", ")),15,MareNotebook::Pencil)];
   else Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Comprar · R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),[S,Id](){S->BuyExpansion(Id);})];
   G->AddSlot(I%3,I/3)[MareNotebook::PriceTag(Card,TiltOf(I))];++I;}
  Heading(TEXT("Negócios da vila"),TEXT("(rendem sozinhos e pagam um funcionário por dia)"));auto B=Grid();I=0;
  for(const auto& Pair:UMareSimulation::Object(S->Definitions,TEXT("businesses"))->Values){const FString Id(Pair.Key.ToView());auto Def=Pair.Value->AsObject();
   auto Card=TagBody(FString::Printf(TEXT("~R$ %.0f/h · funcionário R$ %.0f"),UMareSimulation::Number(Def,TEXT("hour")),UMareSimulation::Number(Def,TEXT("wage"))),UMareSimulation::String(Def,TEXT("name")));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareSimulation::String(Def,TEXT("blurb")),10.5f,MareNotebook::Faded)];FString Reason;
   if(S->OwnsBusiness(Id))Card->AddSlot().AutoHeight()[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[MareNotebook::Stamp(TEXT("SEU"),MareNotebook::Green)]
    +SHorizontalBox::Slot().FillWidth(1).HAlign(HAlign_Right).VAlign(VAlign_Center)[MareNotebook::HandText(FString::Printf(TEXT("hoje R$ %.0f"),S->OpsToday(TEXT("biz_")+Id)),16,MareNotebook::Green)]];
   else if(S->CanBuyBusiness(Id,Reason))Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Comprar · R$ %.0f"),UMareSimulation::Number(Def,TEXT("cost"))),[S,Id](){S->BuyBusiness(Id);})];
   else Card->AddSlot().AutoHeight()[MareNotebook::HandText(Reason,15,MareNotebook::Pencil)];
   B->AddSlot(I%3,I/3)[MareNotebook::PriceTag(Card,TiltOf(I+1))];++I;}
 }
 void MissionsPage()
 {
  auto S=Sim();auto Campaign=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("campaign"));const int32 Stage=UMareSimulation::Number(Campaign,TEXT("stage"));
  Title(TEXT("Missões"));
  for(bool bSide:{false,true}){const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;if(!S->Definitions->TryGetArrayField(bSide?TEXT("side_missions"):TEXT("campaign"),Rows))continue;
   Heading(bSide?TEXT("Pedidos da vila"):TEXT("Uma nova maré"));auto G=Grid();int32 Shown=0;
   for(int32 I=0;I<Rows->Num();++I){if(!bSide && I!=Stage)continue;auto Q=(*Rows)[I]->AsObject();const FString Id=UMareSimulation::String(Q,TEXT("id"));
    const TArray<TSharedPtr<FJsonValue>>* Done=nullptr;if(bSide && Campaign->TryGetArrayField(TEXT("side_done"),Done) && Done->ContainsByPredicate([&](const auto& V){return V->AsString()==Id;}))continue;
    const int32 Have=S->MissionAmount(Q),Need=UMareSimulation::Number(Q,TEXT("qty"),1);
    auto Card=TagBody(FString::Printf(TEXT("%d de %d"),FMath::Min(Have,Need),Need),UMareSimulation::String(Q,TEXT("title")));
    Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareSimulation::String(Q,TEXT("task")),11,MareNotebook::Faded)];
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Concluir · R$ %.0f"),UMareSimulation::Number(Q,TEXT("reward"))),[S,Id,bSide](){S->ClaimMission(Id,bSide);},Have>=Need)];
    G->AddSlot(Shown%3,Shown/3)[MareNotebook::PriceTag(Card,TiltOf(Shown))];++Shown;}
   if(!Shown)Pencil(bSide?TEXT("Nenhum pedido aberto agora."):TEXT("Campanha concluída!"));
  }
  // Chapter steps are completed in person with the giver; the notebook only tracks them.
  Heading(TEXT("Histórias da vila"),TEXT("(converse com quem pediu para avançar)"));auto G=Grid();int32 Shown=0;const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;
  if(S->Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){auto C=Value->AsObject();const FString Id=UMareSimulation::String(C,TEXT("id"));if(!S->IsChapterOpen(Id))continue;
   auto Card=TagBody(UMareSimulation::String(C,TEXT("giver")),UMareSimulation::String(C,TEXT("title")));
   if(S->IsChapterDone(Id))Card->AddSlot().AutoHeight()[MareNotebook::Stamp(TEXT("CONCLUÍDA"),MareNotebook::Green)];
   else{int32 Goal=1;const int32 Have=S->ChapterStepProgress(Id,Goal);const int32 Step=S->ChapterStep(Id);
    Card->AddSlot().AutoHeight()[MareNotebook::BodyText(FString::Printf(TEXT("Passo %d de 3 · "),Step+1)+UMareSimulation::String(C->GetArrayField(TEXT("steps"))[Step]->AsObject(),TEXT("text")),11,MareNotebook::Faded)];
    Card->AddSlot().AutoHeight()[MareNotebook::HandText(FString::Printf(TEXT("%d de %d"),Have,Goal),17,MareNotebook::Green)];}
   G->AddSlot(Shown%3,Shown/3)[MareNotebook::PriceTag(Card,TiltOf(Shown+2))];++Shown;}
 }
 /** Personalizar: every place (kiosk, expansions, hotel, businesses, home), 5 tiers per object, and recipes. */
 TSharedRef<SWidget> PlaceIndex()
 {
  auto S=Sim();auto List=SNew(SVerticalBox);
  static const TArray<FString> GroupNames={TEXT("Quiosque"),TEXT("Expansões"),TEXT("Hotel"),TEXT("Negócios"),TEXT("Casa")};
  static const TArray<TArray<FString>> GroupPlaces={{TEXT("kiosk")},{TEXT("bar"),TEXT("pool"),TEXT("pousada"),TEXT("passeios")},
   {TEXT("hotel_restaurante"),TEXT("hotel_piscina"),TEXT("hotel_suites"),TEXT("hotel_lazer")},{TEXT("biz_aluguel"),TEXT("biz_sorveteria"),TEXT("biz_food_truck"),TEXT("biz_souvenir"),TEXT("biz_surfe")},{TEXT("home")}};
  List->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("Onde?"),16,MareNotebook::Pencil)];
  for(int32 G=0;G<GroupNames.Num();++G){List->AddSlot().AutoHeight().Padding(0,6,0,0)[MareNotebook::HandText(GroupNames[G],14,MareNotebook::Faded)];
   for(const FString& Id:GroupPlaces[G]){FString Name=UMareSimulation::String(S->PlaceDef(Id),TEXT("name"));Name.RemoveFromStart(TEXT("Grand Hotel · "));const bool bOn=Id==Place,bOpen=S->IsPlaceAvailable(Id);
    List->AddSlot().AutoHeight()[SNew(SButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(0)).OnClicked_Lambda([this,Id](){Place=Id;Rebuild();return FReply::Handled();})
     [SNew(SBorder).BorderImage(bOn?static_cast<const FSlateBrush*>(&MareNotebook::MarkerBrush()):FCoreStyle::Get().GetBrush("NoBrush")).Padding(FMargin(5,0))[MareNotebook::HandText((bOn?TEXT("» "):TEXT(""))+Name,17,bOpen?MareNotebook::Ink:MareNotebook::Pencil)]]];}}
  return SNew(SScrollBox)+SScrollBox::Slot()[List];
 }
 void CustomizePage()
 {
  auto S=Sim();auto World=Owner->GetWorld();auto Custom=World->GetSubsystem<UMareCustomWorld>();auto Kiosk=World->GetSubsystem<UMareKioskWorld>();
  const TArray<TSharedPtr<FJsonValue>>* TierNames=nullptr;S->CustomDefs()->TryGetArrayField(TEXT("tiers"),TierNames);
  if(!S->PlaceDef(Place)->HasField(TEXT("slots")))Place=TEXT("kiosk");
  const FString PlaceName=UMareSimulation::String(S->PlaceDef(Place),TEXT("name"));
  FString Summary=S->PlaceSummary(Place);Summary.ReplaceInline(TEXT("Conforto"),TEXT("conforto"));Summary.ReplaceInline(TEXT("Beleza"),TEXT("beleza"));
  Title(PlaceName);
  FString Locked;if(!S->IsPlaceAvailable(Place,&Locked)){Pencil(Locked);return;}
  Body->AddSlot().AutoHeight().Padding(0,0,0,4)[MareNotebook::HandText(Summary,16,MareNotebook::Green)];
  FString Reason;const bool bCanChange=Place!=TEXT("kiosk") || !Kiosk || Kiosk->CanCustomize(Reason);if(!bCanChange)Pencil(Reason);
  const TArray<TSharedPtr<FJsonValue>>* Slots=nullptr;
  if(S->PlaceDef(Place)->TryGetArrayField(TEXT("slots"),Slots))for(const auto& Value:*Slots){
   auto Def=Value->AsObject();const FString Slot=UMareSimulation::String(Def,TEXT("id"));const int32 Current=S->CustomTier(Place,Slot);
   const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;if(!Def->TryGetArrayField(TEXT("tiers"),Tiers))continue;
   TArray<FString> Effects;const double C=UMareSimulation::Number(Def,TEXT("comfort")),B=UMareSimulation::Number(Def,TEXT("beauty"));
   if(C>0)Effects.Add(FString::Printf(TEXT("+%.0f conforto"),C));if(B>0)Effects.Add(FString::Printf(TEXT("+%.0f beleza"),B));
   if(Def->HasField(TEXT("speed")))Effects.Add(TEXT("atendente +10% rápido"));if(Def->HasField(TEXT("fame")))Effects.Add(TEXT("mais fama"));
   if(Def->HasField(TEXT("income")))Effects.Add(FString::Printf(TEXT("renda +%.0f%%"),UMareSimulation::Number(Def,TEXT("income"))*100));
   if(Def->HasField(TEXT("rate")))Effects.Add(FString::Printf(TEXT("diária +R$ %.0f"),UMareSimulation::Number(Def,TEXT("rate"))));
   if(Def->HasField(TEXT("seats")))Effects.Add(FString::Printf(TEXT("+%.0f vaga"),UMareSimulation::Number(Def,TEXT("seats"))));
   Heading(UMareSimulation::String(Def,TEXT("name")),TEXT("(")+FString::Join(Effects,TEXT(", "))+TEXT(" por nível)"));
   const FString Unlock=UMareSimulation::String(Def,TEXT("unlock"));bool bUnlocked=Unlock.IsEmpty();if(!bUnlocked)UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Unlock,bUnlocked);
   if(!bUnlocked){Pencil(TEXT("Disponível depois de comprar ")+UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("expansions")),Unlock),TEXT("name"))+TEXT(" (Resort)."));continue;}
   bool bVisual=true;Def->TryGetBoolField(TEXT("visual"),bVisual);auto G=Grid();
   for(int32 Tier=1;Tier<=Tiers->Num();++Tier){auto TierDef=(*Tiers)[Tier-1]->AsObject();const FString P=Place;
    const FString Level=TierNames && TierNames->IsValidIndex(Tier-1)?(*TierNames)[Tier-1]->AsString():FString::FromInt(Tier);
    auto Card=TagBody(FString::Printf(TEXT("nº %d · %s"),Tier,*Level),UMareSimulation::String(TierDef,TEXT("name")));
    Card->AddSlot().FillHeight(1)[SNullWidget::NullWidget];
    if(Tier==Current)Card->AddSlot().AutoHeight()[MareNotebook::Stamp(TEXT("EM USO"))];
    else{auto Row=SNew(SHorizontalBox);const bool bOwned=S->OwnsCustomTier(Place,Slot,Tier);
     if(bCanChange)Row->AddSlot().AutoWidth()[Button(bOwned?FString(TEXT("usar")):FString::Printf(TEXT("R$ %.0f"),S->CustomPrice(Place,Slot,Tier)),[S,Custom,P,Slot,Tier](){if(S->BuyCustom(P,Slot,Tier) && Custom)Custom->ApplyAll();})];
     if(Custom && bVisual)Row->AddSlot().FillWidth(1).HAlign(HAlign_Right).VAlign(VAlign_Center)[Link(TEXT("espiar"),[S,Custom,P,Slot,Tier,PlaceName](){Custom->Apply(P,Slot,Tier,true);
      S->LastMessage=TEXT("Espiando em ")+PlaceName+TEXT(". Feche o celular para voltar ao que está em uso.");})];
     Card->AddSlot().AutoHeight()[Row];}
    G->AddSlot(Tier-1,0)[MareNotebook::PriceTag(Card,TiltOf(Tier-1),UMareSimulation::String(TierDef,TEXT("desc")))];}
  }
  if(Place!=TEXT("kiosk"))return;
  Heading(TEXT("Receitas e preços"),TEXT("(receita melhor: preço de referência maior, mais pedidos e fama · seu preço muda a procura)"));
  const TArray<TSharedPtr<FJsonValue>>* Levels=nullptr;UMareSimulation::Object(S->CustomDefs(),TEXT("recipes"))->TryGetArrayField(TEXT("levels"),Levels);auto G=Grid();int32 I=0;
  for(const auto& Id:Products()){auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);const int32 Level=S->RecipeLevel(Id);
   const FString LevelName=Levels && Levels->IsValidIndex(Level-1)?(*Levels)[Level-1]->AsString():FString::FromInt(Level);
   auto Card=TagBody(FString::Printf(TEXT("nível %d · %s · R$ %.0f"),Level,*LevelName,S->DishPrice(Id)),UMareSimulation::String(Dish,TEXT("name")));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(S->RecipeTitle(Id),11,MareNotebook::Faded)];
   if(!S->IsDishUnlocked(Id))Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("libere o produto em Resort"),15,MareNotebook::Pencil)];
   else if(Level>=5)Card->AddSlot().AutoHeight()[MareNotebook::Stamp(TEXT("NO MÁXIMO"),MareNotebook::Green)];
   else Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Melhorar · R$ %.0f"),S->RecipeUpgradeCost(Id)),[S,Id](){S->UpgradeRecipe(Id);})];
   // Your price (50%-200% of the recipe price): cheap sells more, expensive sells less and earns smaller tips.
   if(S->IsDishUnlocked(Id)){const double R=S->PriceRatio(Id);
    Card->AddSlot().AutoHeight().Padding(0,6,0,0)[MareNotebook::BodyText(FString::Printf(TEXT("Seu preço: R$ %.0f · %s"),S->SalePrice(Id),R>1.15?TEXT("caro"):R<.9?TEXT("barato"):TEXT("justo")),12.5f,R>1.15?MareNotebook::Red:R<.9?MareNotebook::Green:MareNotebook::Ink,true)];
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().Padding(0,0,6,0)[Button(TEXT("-R$ 1"),[S,Id](){S->SetSalePrice(Id,S->SalePrice(Id)-1);})]
     +SHorizontalBox::Slot().AutoWidth().Padding(0,0,6,0)[Button(TEXT("+R$ 1"),[S,Id](){S->SetSalePrice(Id,S->SalePrice(Id)+1);})]
     +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("justo"),[S,Id](){S->SetSalePrice(Id,S->DishPrice(Id));})]];}
   G->AddSlot(I%4,I/4)[MareNotebook::PriceTag(Card,TiltOf(I),TEXT("Próxima: ")+S->RecipeTitle(Id,FMath::Min(Level+1,5)))];++I;}
 }
 void Rebuild()
 {
  if(!Sim())return;auto S=Sim();using namespace MareNotebook;
  static const TArray<FString> Titles={TEXT("Quiosque"),TEXT("Compras"),TEXT("Equipe"),TEXT("Finanças"),TEXT("Resort"),TEXT("Missões"),TEXT("Personalizar")};
  const bool bPhone=Station.IsNone();const bool bIndex=bPhone && Tab==6;
  SAssignNew(Body,SVerticalBox);
  // Status line in pencil: day, clock, weather and cash.
  auto Status=SNew(SHorizontalBox)
   +SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Font(MareNotebook::Hand(16)).ColorAndOpacity(Faded).Text_Lambda([S](){const int32 M=UMareSimulation::Number(S->State,TEXT("minutes"));
    return FText::FromString(FString::Printf(TEXT("Dia %.0f · %02d:%02d · %s"),UMareSimulation::Number(S->State,TEXT("day"),1),M/60,M%60,UMareSimulation::String(S->State,TEXT("weather"))==TEXT("rain")?TEXT("Chuva"):TEXT("Sol")));})]
   +SHorizontalBox::Slot().FillWidth(2).HAlign(HAlign_Center).Padding(8,0)[SNew(SBox).Visibility(S->LastMessage.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible)[SNew(SBorder).BorderImage(&MarkerBrush()).Padding(FMargin(6,0))
    [SNew(STextBlock).Text(FText::FromString(S->LastMessage)).Font(MareNotebook::Hand(15)).ColorAndOpacity(Ink).OverflowPolicy(ETextOverflowPolicy::Ellipsis).ToolTipText(FText::FromString(S->LastMessage))]]]
   +SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Font(MareNotebook::Hand(16)).ColorAndOpacity(Faded).Text_Lambda([S](){return FText::FromString(FString::Printf(TEXT("Caixa: R$ %.0f"),S->Money()));})];
  // Divider tabs: pastel paper, the open one is the white page itself; "fechar" sits at the end.
  auto Tabs=SNew(SHorizontalBox);
  if(bPhone)for(int32 I=0;I<Titles.Num();++I){const bool bOn=I==Tab;
   Tabs->AddSlot().AutoWidth().VAlign(VAlign_Bottom).Padding(0,0,3,0)[SNew(SButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(0)).OnClicked_Lambda([this,I](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.16f);Tab=I;Rebuild();return FReply::Handled();})
    [SNew(SBorder).BorderImage(&TabBrush(bOn?Paper:TabColor(I))).Padding(bOn?FMargin(11,4,11,3):FMargin(8,2,8,2))[SNew(STextBlock).Text(FText::FromString(Titles[I])).Font(MareNotebook::Hand(bOn?17:15)).ColorAndOpacity(Ink)]]];}
  else Tabs->AddSlot().AutoWidth().VAlign(VAlign_Bottom)[SNew(SBorder).BorderImage(&TabBrush(Paper)).Padding(FMargin(16,6,16,5))[SNew(STextBlock).Text(FText::FromString(Station==TEXT("Fridge")?TEXT("Geladeira"):Station==TEXT("Reception") || Station==TEXT("ReceptionHotel")?TEXT("Recepção"):TEXT("Porções prontas"))).Font(MareNotebook::Hand(19)).ColorAndOpacity(Ink)]];
  Tabs->AddSlot().FillWidth(1)[SNullWidget::NullWidget];
  Tabs->AddSlot().AutoWidth().VAlign(VAlign_Bottom)[SNew(SButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(0)).OnClicked_Lambda([this](){if(Owner.IsValid())Owner->ClosePhone();return FReply::Handled();})
   [SNew(SBorder).BorderImage(&TabBrush(Hex(226,150,140))).Padding(FMargin(8,2,8,2))[SNew(STextBlock).Text(FText::FromString(TEXT("fechar"))).Font(MareNotebook::Hand(15)).ColorAndOpacity(Ink)]]];
  // The page: lined paper behind, place index on the left of Personalizar, scrolling content, a sticky note for messages.
  auto Page=SNew(SHorizontalBox);
  if(bIndex)Page->AddSlot().AutoWidth()[SNew(SBox).WidthOverride(150).Padding(FMargin(14,8,8,6))[PlaceIndex()]];
  Page->AddSlot().FillWidth(1).Padding(bIndex?FMargin(12,8,16,0):FMargin(24,8,18,0))[SNew(SScrollBox)+SScrollBox::Slot().Padding(0,0,0,10)[Body.ToSharedRef()]];
  auto Sheet=SNew(SOverlay)+SOverlay::Slot()[SNew(SPaperLines).MarginX(bIndex?150.f:12.f)]+SOverlay::Slot()[Page];
  auto Screen=SNew(SBorder).BorderImage(&Cover()).Padding(FMargin(16,5,16,0))[SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().Padding(4,0,4,2)[Status]
   +SVerticalBox::Slot().AutoHeight()[Tabs]
   +SVerticalBox::Slot().FillHeight(1)[Sheet]];
  // Placed over the 3D phone's glass every frame (Slate units); the box size includes its offset padding.
  ChildSlot.HAlign(HAlign_Left).VAlign(VAlign_Top)[SNew(SDPIScaler).DPIScale_Lambda([](){return MareTropical::Scale();})[SNew(SBox)
   .Padding_Lambda([this](){const FSlateRect R=ScreenRect();return FMargin(R.Left,R.Top,0,0);})
   .WidthOverride_Lambda([this](){return FOptionalSize(ScreenRect().Right);})
   .HeightOverride_Lambda([this](){return FOptionalSize(ScreenRect().Bottom);})[Screen]]];
  if(Station==TEXT("Reception") || Station==TEXT("ReceptionHotel")){ReceptionPage(Station==TEXT("ReceptionHotel")?TEXT("hotel"):TEXT("pousada"));return;}
  if(!bPhone){StockPage(true);if(!S->Carry().IsEmpty())Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6)[Button(TEXT("Devolver produto"),[S](){S->ReturnCarry();})];return;}
  switch(Tab){
   case 0:KioskPage();break;
   case 1:Title(TEXT("Compras"),TEXT("reposição imediata · o produto chega pronto"));StockPage(false);break;
   case 2:StaffPage();break;
   case 3:FinancePage();break;
   case 4:ResortPage();break;
   case 5:MissionsPage();break;
   default:CustomizePage();
  }
 }
};
AMareCharacter::AMareCharacter()
{
 CreateDefaultSubobject<UMarePlayerPresentation>(TEXT("PlayerPresentation"));
 bUseControllerRotationYaw=true;
 PrimaryActorTick.bCanEverTick=true;
 GetCapsuleComponent()->InitCapsuleSize(32,88);
 Eyes=CreateDefaultSubobject<UCameraComponent>(TEXT("Eyes"));Eyes->SetupAttachment(GetCapsuleComponent());Eyes->SetRelativeLocation(FVector(12,0,74));Eyes->bUsePawnControlRotation=true;
 Eyes->PostProcessSettings.bOverride_SceneColorTint=true;Eyes->PostProcessSettings.SceneColorTint=FLinearColor(.72f,.86f,.83f);
 PhoneModel=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PhoneModel"));PhoneModel->SetupAttachment(Eyes);
 PhoneModel->SetCollisionEnabled(ECollisionEnabled::NoCollision);PhoneModel->SetCastShadow(false);PhoneModel->SetVisibility(false);
 Eyes->PostProcessSettings.bOverride_VignetteIntensity=true;Eyes->PostProcessSettings.VignetteIntensity=.28f;Eyes->PostProcessBlendWeight=0;
 GetCharacterMovement()->MaxWalkSpeed=260;GetCharacterMovement()->JumpZVelocity=360;GetCharacterMovement()->MaxStepHeight=35;
 GetCharacterMovement()->GetNavAgentPropertiesRef().bCanSwim=true;
 GetCharacterMovement()->MaxSwimSpeed=210;GetCharacterMovement()->Buoyancy=1.35f;GetCharacterMovement()->BrakingDecelerationSwimming=180;
}
void AMareCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
 Super::SetupPlayerInputComponent(Input);Input->BindAxis(TEXT("Forward"),this,&AMareCharacter::Forward);Input->BindAxis(TEXT("Right"),this,&AMareCharacter::Right);
 Input->BindAxis(TEXT("LookX"),this,&AMareCharacter::LookX);Input->BindAxis(TEXT("LookY"),this,&AMareCharacter::LookY);
 Input->BindAction(TEXT("Phone"),IE_Pressed,this,&AMareCharacter::Phone);Input->BindAction(TEXT("Interact"),IE_Pressed,this,&AMareCharacter::Interact);Input->BindAction(TEXT("Jump"),IE_Pressed,this,&ACharacter::Jump);
 Input->BindAction(TEXT("Jump"),IE_Released,this,&ACharacter::StopJumping);
 Input->BindAxis(TEXT("SwimVertical"),this,&AMareCharacter::SwimVertical);
 Input->BindAction(TEXT("Sprint"),IE_Pressed,this,&AMareCharacter::SprintPressed);Input->BindAction(TEXT("Sprint"),IE_Released,this,&AMareCharacter::SprintReleased);
}
void AMareCharacter::Forward(float Value){if(FMath::Abs(Value)>.1f)if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())Home->Stand();if(Controller){auto Rotation=Controller->GetControlRotation();if(!GetCharacterMovement()->IsSwimming())Rotation.Pitch=0;Rotation.Roll=0;AddMovementInput(Rotation.Vector(),Value);}}
void AMareCharacter::Right(float Value){if(FMath::Abs(Value)>.1f)if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())Home->Stand();if(Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),Value);}
void AMareCharacter::LookX(float Value){AddControllerYawInput(Value);}
void AMareCharacter::LookY(float Value){AddControllerPitchInput(Value);}
void AMareCharacter::Phone(){if(auto PC=Cast<AMareController>(Controller))PC->TogglePhone();}
void AMareCharacter::Interact()
{
 if(auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>())if(Village->IsDialogueOpen()){Village->CloseDialogue();return;}
 for(TActorIterator<AMareIntro> It(GetWorld());It;++It)if(It->IsArrival()){It->FinishArrival();return;}
 auto PC=Cast<AMareController>(Controller);if(!PC || PC->bPhoneOpen || GetWorld()->IsPaused())return;
 if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())if(Home->IsSeated()){Home->Stand();return;}
 if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())if(Home->IsSleeping())return;
 if(auto Target=AMareServiceTarget::FindFocused(PC))Target->Use(PC);
}
// The phone is a real model scaled x2 at 19.5 cm (the camera near plane is 10 cm), which looks like a
// phone held at arm's length; its glass (inset from the body) is where the Slate phone UI is drawn.
namespace MarePhoneHold{constexpr double Scale=2.0,Distance=19.5,Drop=1.0,GlassX=3.25,GlassZ=7.75;}
void AMareCharacter::SetPhoneVisible(bool bVisible)
{
 if(bVisible && !PhoneModel->GetStaticMesh()){FString Text;TSharedPtr<FJsonObject> Assets;
  if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/custom_assets.json"))) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Assets) && Assets.IsValid())
   if(auto PhoneMesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(Assets,TEXT("realistic_smartphone")))){
    // Imported upright (width X, thickness Y, length Z): lay it on its side with the glass (+Y) facing the eyes.
    const FRotator Rotation=FRotationMatrix::MakeFromYZ(FVector(-1,0,0),FVector(0,1,0)).Rotator();const FBoxSphereBounds B=PhoneMesh->GetBounds();
    PhoneModel->SetStaticMesh(PhoneMesh);PhoneModel->SetRelativeScale3D(FVector(MarePhoneHold::Scale));PhoneModel->SetRelativeRotation(Rotation);
    PhoneModel->SetRelativeLocation(FVector(MarePhoneHold::Distance,0,-MarePhoneHold::Drop)-Rotation.RotateVector(B.Origin*MarePhoneHold::Scale));}}
 PhoneModel->SetVisibility(bVisible && PhoneModel->GetStaticMesh());
}
UStaticMeshComponent* AMareCharacter::GetHeldPhone()const{return PhoneModel && PhoneModel->IsVisible()?PhoneModel.Get():nullptr;}
bool AMareCharacter::PhoneScreenRect(FVector2D& Min,FVector2D& Max)const
{
 auto PC=Cast<APlayerController>(Controller);if(!PC || !GetHeldPhone())return false;
 const FBoxSphereBounds B=PhoneModel->GetStaticMesh()->GetBounds();Min=FVector2D(1e9);Max=FVector2D(-1e9);
 for(int32 I=0;I<4;++I){const FVector Local=B.Origin+FVector((I&1?1:-1)*MarePhoneHold::GlassX,B.BoxExtent.Y,(I&2?1:-1)*MarePhoneHold::GlassZ);FVector2D Screen;
  if(!PC->ProjectWorldLocationToScreen(PhoneModel->GetComponentTransform().TransformPosition(Local),Screen))return false;Min=FVector2D::Min(Min,Screen);Max=FVector2D::Max(Max,Screen);}
 return Max.X-Min.X>50 && Max.Y-Min.Y>30;
}
void AMareCharacter::SwimVertical(float Value){VerticalSwimInput=FMath::Clamp(Value,-1.f,1.f);}
void AMareCharacter::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto Movement=GetCharacterMovement();auto PC=Cast<APlayerController>(Controller);
 const bool bSwimming=Movement->IsSwimming();const float Vertical=PC && PC->IsMoveInputIgnored()?0.f:VerticalSwimInput;
 // A comfortable home leaves the player rested: walking and running get faster.
 const UMareSimulation* HomeSim=GetGameInstance()?GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;
 Movement->MaxWalkSpeed=(bSprint?420:260)*(HomeSim?float(HomeSim->HomeSpeedFactor()):1.f);Movement->Buoyancy=Vertical<0?1.f:1.35f;
 if(bSwimming && (Vertical<=0 || GetActorLocation().Z<-78))AddMovementInput(FVector::UpVector,Vertical);
 const bool bUnderwater=bSwimming && Eyes->GetComponentLocation().Z<-38;
 Eyes->PostProcessBlendWeight=FMath::FInterpTo(Eyes->PostProcessBlendWeight,bUnderwater?1.f:0.f,DeltaSeconds,5);
 if(Movement->IsMovingOnGround() && !bSwimming && GetActorLocation().Z>-100)SafeLandLocation=GetActorLocation();
 if(GetActorLocation().Z<-5000){SetActorLocation(SafeLandLocation);Movement->StopMovementImmediately();VerticalSwimInput=0;}
}

void AMareController::SetupInputComponent()
{
 Super::SetupInputComponent();InputComponent->BindAction(TEXT("Pause"),IE_Pressed,this,&AMareController::TogglePauseMenu).bExecuteWhenPaused=true;
}
void AMareController::TogglePauseMenu()
{
 if(auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>())if(Village->IsDialogueOpen()){Village->CloseDialogue();return;}
 for(TActorIterator<AMareIntro> It(GetWorld());It;++It)if(It->IsLetterOpen()){It->CloseLetter();return;}else if(It->IsArrival()){It->FinishArrival();return;}
 if(bPhoneOpen){ClosePhone();return;}
 if(!GEngine || !GEngine->GameViewport)return;
 if(PauseWidget.IsValid()){
  GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();SetPause(false);
  bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();return;
 }
 SetPause(true);auto Menu=SNew(SVerticalBox);
 auto Add=[&](const FString& Label,TFunction<void()> Callback){Menu->AddSlot().AutoHeight().Padding(0,5)[SNew(SButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(14,8)).OnClicked_Lambda([Callback](){Callback();return FReply::Handled();})[MareUI::Text(Label,14,FLinearColor::White)]];};
 Menu->AddSlot().AutoHeight().Padding(0,0,0,12)[MareUI::Text(TEXT("Maré Alta · pausa"),20)];
 Add(TEXT("Retomar"),[this](){TogglePauseMenu();});
 Add(TEXT("Salvar progresso"),[this](){GetSimulation()->Save();});
 Add(TEXT("Qualidade: média"),[](){auto Settings=UGameUserSettings::GetGameUserSettings();Settings->SetOverallScalabilityLevel(1);Settings->ApplyNonResolutionSettings();Settings->SaveSettings();});
 Add(TEXT("Qualidade: alta"),[](){auto Settings=UGameUserSettings::GetGameUserSettings();Settings->SetOverallScalabilityLevel(2);Settings->ApplyNonResolutionSettings();Settings->SaveSettings();});
 auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();
 const TArray<FName> Buses={TEXT("Master"),TEXT("Music"),TEXT("Effects"),TEXT("Ambient")};
 const TArray<FString> Labels={TEXT("Volume geral"),TEXT("Música"),TEXT("Efeitos"),TEXT("Ambiente")};
 for(int32 I=0;I<Buses.Num();++I){const FName Bus=Buses[I];Menu->AddSlot().AutoHeight().Padding(0,5)[SNew(SHorizontalBox)
  +SHorizontalBox::Slot().AutoWidth().Padding(0,0,12,0)[SNew(SBox).WidthOverride(110)[MareUI::Text(Labels[I],12)]]
  +SHorizontalBox::Slot().FillWidth(1)[SNew(SSlider).Value(Audio->GetVolume(Bus)).OnValueChanged_Lambda([Audio,Bus](float Value){Audio->SetVolume(Bus,Value);})]];}
 Add(TEXT("Sair para o desktop"),[this](){GetSimulation()->Save();UKismetSystemLibrary::QuitGame(this,this,EQuitPreference::Quit,false);});
 PauseWidget=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.65f)).HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(340)[SNew(SBorder).BorderImage(&MareUI::Surface).Padding(20)[Menu]]];
 GEngine->GameViewport->AddViewportWidgetContent(PauseWidget.ToSharedRef(),30);bShowMouseCursor=true;
 SetInputMode(FInputModeGameAndUI());SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::TogglePhone(){if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())if(Home->IsSleeping())return;if(auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>())if(Village->IsDialogueOpen())return;for(TActorIterator<AMareIntro> It(GetWorld());It;++It)if(It->IsArrival() || It->IsLetterOpen())return;if(PauseWidget.IsValid())return;if(bPhoneOpen)ClosePhone();else OpenPhone();}
void AMareController::OpenPhone(int32 Tab)
{
 if(!GEngine || !GEngine->GameViewport)return;
 if(bPhoneOpen)ClosePhone();bPhoneOpen=true;
 if(auto Hero=Cast<AMareCharacter>(GetPawn()))Hero->SetPhoneVisible(true);
 SAssignNew(PhoneWidget,SMarePhone).Owner(this).Tab(Tab);GEngine->GameViewport->AddViewportWidgetContent(PhoneWidget.ToSharedRef(),20);
 bShowMouseCursor=true;SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(PhoneWidget).SetHideCursorDuringCapture(false));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::OpenStation(FName Station)
{
 if(!GEngine || !GEngine->GameViewport)return;
 if(bPhoneOpen)ClosePhone();bPhoneOpen=true;
 SAssignNew(PhoneWidget,SMarePhone).Owner(this).Tab(0).Station(Station);GEngine->GameViewport->AddViewportWidgetContent(PhoneWidget.ToSharedRef(),20);
 bShowMouseCursor=true;SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(PhoneWidget).SetHideCursorDuringCapture(false));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::ClosePhone()
{
 if(auto Hero=Cast<AMareCharacter>(GetPawn()))Hero->SetPhoneVisible(false);
 if(PhoneWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PhoneWidget.ToSharedRef());
 // A furniture preview ends with the phone: show what is really in use again.
 if(auto Custom=GetWorld()->GetSubsystem<UMareCustomWorld>())if(Custom->IsPreviewing())Custom->ApplyAll();
 PhoneWidget.Reset();bPhoneOpen=false;bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
}
void AMareController::EndPlay(const EEndPlayReason::Type Reason){if(PauseWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();ClosePhone();Super::EndPlay(Reason);}
/** Everything the tropical HUD shows; Signature() decides when Slate must rebuild. */
struct FMareHudModel
{
 FString Money,Day,Fame,Notice,Prompt,Carry,Hint,Stars,Rooms,Served;
 int32 StarsFlash=0; // 1 up (green), -1 down (red)
 TArray<TPair<FString,FString>> Tickets;
 TArray<TPair<FString,int32>> Note; // text, style: 0 heading, 1 main goal, 2 secondary, 3 guidance
 bool bPhone=false;
 FString Signature()const
 {
  FString S=Money+Day+Fame+Notice+Prompt+Carry+Hint+Stars+Rooms+Served+FString::FromInt(StarsFlash)+(bPhone?TEXT("P"):TEXT(""));
  for(const auto& T:Tickets)S+=T.Key+T.Value;
  for(const auto& N:Note)S+=N.Key+FString::FromInt(N.Value);
  return S;
 }
};
class SMareHud : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareHud){} SLATE_END_ARGS()
 void Construct(const FArguments&){ChildSlot[SNullWidget::NullWidget];}
 void Refresh(const FMareHudModel& M)
 {
  const FString Sig=M.Signature();if(Sig==Last)return;Last=Sig;using namespace MareTropical;
  const FLinearColor Ink=Hex(74,58,28),Paper=Hex(255,246,230),Accent=Hex(162,76,43);
  auto Root=SNew(SOverlay);
  // Wood plank: coin + money, day/time, fame.
  Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Fill)[SNew(SBorder).BorderImage(&Plank()).Padding(FMargin(22,9))[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,8,0)[SNew(SBox).WidthOverride(18).HeightOverride(18)[SNew(SBorder).BorderImage(&Coin())]]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,34,0)[Txt(M.Money,17,Hex(255,215,106),true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,34,0)[Txt(M.Day,15,Paper,true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,34,0)[Txt(M.Fame,15,Paper,true)]
   // Reputation, always visible: star average, rooms occupied (when there are rooms) and sales today.
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[SNew(SImage).Image(&Icon(TEXT("Star"))).ColorAndOpacity(Hex(255,207,92))]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,24,0)[Txt(M.Stars,15,M.StarsFlash>0?Hex(140,230,140):M.StarsFlash<0?Hex(255,130,110):Paper,true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[M.Rooms.IsEmpty()?SNullWidget::NullWidget:SNew(SImage).Image(&Icon(TEXT("Bed"))).ColorAndOpacity(Paper)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,M.Rooms.IsEmpty()?0:24,0)[Txt(M.Rooms,15,Paper,true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[SNew(SImage).Image(&Icon(TEXT("Person"))).ColorAndOpacity(Paper)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Txt(M.Served,15,Paper,true)]]];
  // Order tickets, slightly tilted like paper slips.
  if(M.Tickets.Num()){
   auto Row=SNew(SHorizontalBox);
   for(int32 I=0;I<M.Tickets.Num();++I)Row->AddSlot().AutoWidth().Padding(7,0)[SNew(SBox).WidthOverride(150).RenderTransform(Tilt(I%2?1.6f:-1.6f)).RenderTransformPivot(FVector2D(.5f,.5f))[SNew(SBorder).BorderImage(&Ticket()).Padding(0)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SBox).HeightOverride(5)[SNew(SBorder).BorderImage(&TicketStrip())]]
    +SVerticalBox::Slot().AutoHeight().Padding(10,6,10,0)[Txt(M.Tickets[I].Key,13,Accent,true)]
    +SVerticalBox::Slot().AutoHeight().Padding(10,2,10,9)[Txt(M.Tickets[I].Value,12,Ink,false,130)]]]];
   Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Center).Padding(0,62,0,0)[Row];
  }
  // Mission note pinned on the right; the side-tab phone covers the centre-left instead.
  if(M.Note.Num()){
   auto List=SNew(SVerticalBox);
   for(const auto& N:M.Note)List->AddSlot().AutoHeight().Padding(0,N.Value==0?0:4,0,0)[Txt(N.Key,N.Value==0?15:N.Value==1?13:12,N.Value==3?Accent:Ink,N.Value<=1,250)];
   Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Right).Padding(0,70,26,0)[SNew(SBox).WidthOverride(280).RenderTransform(Tilt(1.f)).RenderTransformPivot(FVector2D(.5f,0))[SNew(SOverlay)
    +SOverlay::Slot()[SNew(SBorder).BorderImage(&Note()).Padding(FMargin(16,18,16,16))[List]]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Top).Padding(0,-7,0,0)[SNew(SBox).WidthOverride(16).HeightOverride(16)[SNew(SBorder).BorderImage(&Pin())]]]];
  }
  // Temporary notice (sleep summary, chapter, fame) as a light card under the plank.
  if(!M.Notice.IsEmpty() && !M.bPhone)Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Left).Padding(22,62,0,0)[SNew(SBox).MaxDesiredWidth(380)[SNew(SBorder).BorderImage(&Toast()).Padding(FMargin(14,9))[Txt(M.Notice,13,Hex(20,60,56),false,350)]]];
  // Interaction sign and carried product at the bottom centre.
  auto Bottom=SNew(SVerticalBox);
  if(!M.Carry.IsEmpty())Bottom->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0,0,0,6)[SNew(SBorder).BorderImage(&Toast()).Padding(FMargin(12,5))[Txt(TEXT("Na mão: ")+M.Carry,13,Hex(20,60,56),true)]];
  if(!M.Prompt.IsEmpty())Bottom->AddSlot().AutoHeight().HAlign(HAlign_Center)[SNew(SBorder).BorderImage(&Sign()).Padding(FMargin(16,8))[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,10,0)[Key(TEXT("E"))]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Txt(M.Prompt,15,Hex(90,58,30),true)]]];
  Root->AddSlot().VAlign(VAlign_Bottom).HAlign(HAlign_Center).Padding(0,0,0,58)[Bottom];
  if(!M.bPhone)Root->AddSlot().VAlign(VAlign_Bottom).HAlign(HAlign_Left).Padding(22,0,0,16)[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[Key(TEXT("B"))]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,16,0)[Txt(TEXT("Celular"),12,FLinearColor::White,true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[Key(TEXT("Esc"))]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,16,0)[Txt(TEXT("Pausa"),12,FLinearColor::White,true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Txt(M.Hint,12,FLinearColor::White,true)]];
  ChildSlot[SNew(SDPIScaler).DPIScale_Lambda([](){return MareTropical::Scale();})[Root]];
 }
private:
 FString Last;
};
void AMareHUD::EndPlay(const EEndPlayReason::Type Reason)
{
 if(Overlay.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(Overlay.ToSharedRef());
 Overlay.Reset();Super::EndPlay(Reason);
}
void AMareHUD::DrawHUD()
{
 Super::DrawHUD();if(!Canvas)return;auto S=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 if(!Overlay.IsValid() && GEngine && GEngine->GameViewport){SAssignNew(Overlay,SMareHud);GEngine->GameViewport->AddViewportWidgetContent(Overlay.ToSharedRef(),10);}
 const auto PC=Cast<AMareController>(GetOwningPlayerController());
 auto Dish=[&](const FString& Id){return UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id),TEXT("name"));};
 FMareHudModel M;M.bPhone=PC && PC->bPhoneOpen;
 const int32 Minutes=UMareSimulation::Number(S->State,TEXT("minutes"));
 M.Money=FString::Printf(TEXT("R$ %.0f"),S->Money());
 M.Day=FString::Printf(TEXT("Dia %.0f · %02d:%02d"),UMareSimulation::Number(S->State,TEXT("day"),1),Minutes/60,Minutes%60);
 M.Fame=TEXT("Fama: ")+S->FameName();
 const double Now=GetWorld()->GetRealTimeSeconds();
 const double Stars=FMath::RoundToDouble(S->Stars()*10)/10;
 if(ShownStars>=0 && Stars!=ShownStars){bStarsUp=Stars>ShownStars;StarsFlashUntil=Now+1.5;}
 ShownStars=Stars;if(Now<StarsFlashUntil)M.StarsFlash=bStarsUp?1:-1;
 M.Stars=FString::Printf(TEXT("%.1f"),Stars).Replace(TEXT("."),TEXT(","));
 if(const int32 Rooms=S->RoomsTotal())M.Rooms=FString::Printf(TEXT("%d/%d"),FMath::Min(S->RoomsOccupied(),Rooms),Rooms);
 M.Served=FString::Printf(TEXT("%d hoje"),S->ServedToday());
 if(S->LastMessage!=Notice){Notice=S->LastMessage;NoticeUntil=Notice.IsEmpty()?0:Now+7;}
 if(Now<NoticeUntil)M.Notice=Notice;
 const int32 IntroStage=UMareSimulation::Number(S->State,TEXT("ue_intro_stage"),2);
 if(IntroStage==0)M.Note={{TEXT("Chegada"),0},{TEXT("A vila parecia menor... e o mar, do tamanho das minhas lembranças."),2},{TEXT("E · avançar"),3}};
 else{
  M.Note.Add({TEXT("Missões"),0});
  if(IntroStage==1)M.Note.Add({TEXT("Entre na casa e leia a carta da avó Dilce"),3});
  bool bCreated=false;UMareSimulation::Object(S->State,TEXT("company"))->TryGetBoolField(TEXT("created"),bCreated);
  if(!bCreated && IntroStage>=2)M.Note.Add({TEXT("Comece aqui: B · Celular → Quiosque → Criar empresa"),3});
  else if(bCreated && !S->IsOpen())M.Note.Add({TEXT("Clique na placa FECHADO do balcão para abrir"),3});
  const auto Campaign=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("campaign"));
  const TArray<TSharedPtr<FJsonValue>>* Missions=nullptr;const int32 Stage=UMareSimulation::Number(Campaign,TEXT("stage"));
  if(S->Definitions->TryGetArrayField(TEXT("campaign"),Missions) && Missions->IsValidIndex(Stage)){
   const auto Mission=(*Missions)[Stage]->AsObject();const int32 Goal=UMareSimulation::Number(Mission,TEXT("qty"));const int32 Progress=FMath::Min(S->MissionAmount(Mission),Goal);
   M.Note.Add({UMareSimulation::String(Mission,TEXT("title"))+FString::Printf(TEXT(" — %d/%d"),Progress,Goal)+(Progress>=Goal?TEXT(" · concluir no celular"):TEXT("")),1});
  }
  if(S->Definitions->TryGetArrayField(TEXT("side_missions"),Missions)){
   const TArray<TSharedPtr<FJsonValue>>* Done=nullptr;Campaign->TryGetArrayField(TEXT("side_done"),Done);int32 Shown=0;
   for(const auto& Value:*Missions){
    const auto Mission=Value->AsObject();const FString Id=UMareSimulation::String(Mission,TEXT("id"));
    if(Done && Done->ContainsByPredicate([&](const auto& Item){return Item->AsString()==Id;}))continue;
    const int32 Goal=UMareSimulation::Number(Mission,TEXT("qty"));
    M.Note.Add({UMareSimulation::String(Mission,TEXT("title"))+FString::Printf(TEXT(" — %d/%d"),FMath::Min(S->MissionAmount(Mission),Goal),Goal),2});
    if(++Shown>=2)break;
   }
  }
  // Village story step currently open (talk to its giver to advance).
  const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;
  if(S->Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){
   auto C=Value->AsObject();const FString Id=UMareSimulation::String(C,TEXT("id"));
   if(!S->IsChapterOpen(Id) || S->IsChapterDone(Id))continue;
   int32 Goal=1;const int32 Have=S->ChapterStepProgress(Id,Goal);
   M.Note.Add({UMareSimulation::String(C,TEXT("giver"))+TEXT(": ")+UMareSimulation::String(C->GetArrayField(TEXT("steps"))[S->ChapterStep(Id)]->AsObject(),TEXT("text"))+FString::Printf(TEXT(" — %d/%d"),Have,Goal),2});
   break;
  }
  auto Orders=UMareSimulation::Object(S->State,TEXT("ue_orders"));int32 Number=0;
  for(const auto& Pair:Orders->Values){
   if(++Number>5)break;auto Order=Pair.Value->AsObject();const TArray<TSharedPtr<FJsonValue>>* Items=nullptr;FString Text;
   if(Order->TryGetArrayField(TEXT("remaining"),Items))for(const auto& Item:*Items)Text+=(Text.IsEmpty()?TEXT(""):TEXT("\n"))+Dish(Item->AsString());
   // How the customer felt about your prices when ordering.
   double High=0,Low=9;const TArray<TSharedPtr<FJsonValue>>* All=nullptr;
   if(Order->TryGetArrayField(TEXT("items"),All) || Order->TryGetArrayField(TEXT("remaining"),All))for(const auto& Item:*All){const double R=S->PriceRatio(Item->AsString());High=FMath::Max(High,R);Low=FMath::Min(Low,R);}
   const TCHAR* Feel=High>1.25?TEXT(" · achou caro"):Low<.85?TEXT(" · que barato!"):TEXT("");
   M.Tickets.Add({FString::Printf(TEXT("#%d %s%s"),Number,*UMareSimulation::String(Order,TEXT("name")),Feel),Text});
  }
 }
 if(!S->Carry().IsEmpty())M.Carry=Dish(S->Carry());
 if(auto Hero=Cast<AMareCharacter>(GetOwningPawn()))if(Hero->GetCharacterMovement()->IsSwimming())M.Hint=TEXT("Nadando · Espaço sobe · Ctrl/Shift mergulha");
 // The mission note would sit on top of the held phone.
 if(M.bPhone){M.Note.Empty();M.Tickets.Empty();}
 // Pool match: aim guide, power bar and score instead of the crosshair and the mission note.
 if(auto Room=GetWorld()->GetSubsystem<UMareGameRoom>())if(Room->IsPlaying()){
  M.Note.Empty();M.Tickets.Empty();M.Hint=Room->Status();FVector From,To;FVector2D A,B;
  if(Room->AimLine(From,To) && PC && PC->ProjectWorldLocationToScreen(From,A) && PC->ProjectWorldLocationToScreen(To,B))DrawLine(A.X,A.Y,B.X,B.Y,FLinearColor(1,1,1,.7f),1.5f);
  if(Room->Power()>0){const float X=Canvas->ClipX*.5f-120,Y=Canvas->ClipY-150;DrawRect(FLinearColor(0,0,0,.4f),X,Y,240,10);DrawRect(FLinearColor(1.f,.8f-.5f*Room->Power(),.3f),X,Y,240*Room->Power(),10);}
  Overlay->Refresh(M);return;}
 if(PC && !PC->bPhoneOpen && !GetWorld()->IsPaused()){
  const auto Target=AMareServiceTarget::FindFocused(GetOwningPlayerController());
  const FLinearColor FocusColor=Target?FLinearColor(1.f,.88f,.56f):FLinearColor(.9f,.9f,.9f,.8f);
  const float CX=Canvas->ClipX*.5f,CY=Canvas->ClipY*.5f;
  DrawLine(CX-3,CY,CX+3,CY,FocusColor,1.f);DrawLine(CX,CY-3,CX,CY+3,FocusColor,1.f);
  if(Target)M.Prompt=Target->Prompt();
 }
 Overlay->Refresh(M);
}
AMareGameMode::AMareGameMode(){PrimaryActorTick.bCanEverTick=true;DefaultPawnClass=AMareCharacter::StaticClass();PlayerControllerClass=AMareController::StaticClass();HUDClass=AMareHUD::StaticClass();}
void AMareGameMode::BeginPlay(){Super::BeginPlay();GetWorld()->SpawnActor<AMareIntro>();if(FParse::Param(FCommandLine::Get(),TEXT("MareGraphicsQA")))GetWorld()->SpawnActor<AMareGraphicsQA>();if(FParse::Param(FCommandLine::Get(),TEXT("MareIntroQA")))GetWorld()->SpawnActor<AMareIntroQA>();if(FParse::Param(FCommandLine::Get(),TEXT("MarePreviewQA")))GetWorld()->SpawnActor<AMarePreviewQA>();}

void AMareGameMode::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 Sim->AdvanceMinutes(DeltaSeconds*2.0);SaveClock+=DeltaSeconds;if(SaveClock>=30){Sim->Save();SaveClock=0;}
}

UMareSimulation* AMareController::GetSimulation()const{return GetGameInstance()->GetSubsystem<UMareSimulation>();}
