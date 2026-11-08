#include "MareGame.h"
#include "MareTitle.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "MareStaffWorld.h"
#include "UnrealClient.h"
#include "Widgets/SCanvas.h"
#include "MareBarWorld.h"
#include "MareToursWorld.h"
#include "MareBoatTourWorld.h"
#include "MareSnorkelWorld.h"
#include "MareTrailWorld.h"
#include "MareRentalWorld.h"
#include "MareSouvenirGame.h"
#include "MareReefWorld.h"
#include "MarePlayerPresentation.h"
#include "MareHomeWorld.h"
#include "MareVillageWorld.h"
#include "MareIntro.h"
#include "MareIntroQA.h"
#include "MareGraphicsQA.h"
#include "EngineUtils.h"
#include "MarePreviewQA.h"
#include "MareBench.h"
#include "MareAudioWorld.h"
#include "MareCustomWorld.h"
#include "MareKioskWorld.h"
#include "Misc/CommandLine.h"
#include "CoreGlobals.h"
#include "Misc/Parse.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MareServiceTarget.h"
#include "MareOutline.h"
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
#include "Containers/Ticker.h"
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
#include "Widgets/Layout/SScaleBox.h"
#include "UObject/StrongObjectPtr.h"
#include "Misc/PackageName.h"
#include "Engine/Texture2D.h"
#if WITH_EDITOR
#include "TextureCompiler.h"
#endif
#include "MareGameRoom.h"
#include "MareTableTennis.h"
#include "MareFoosball.h"
#include "MareArcade.h"
#include "MareHotelEventsWorld.h"
#include "HAL/PlatformProcess.h"
#include "MareStaysWorld.h"
#include "MareOptions.h"
#include "MareGamepad.h"
#include "Engine/Texture2D.h"
#include "Framework/Application/SlateApplication.h"

namespace MareUI
{
 /** Wrap compact HUD text into the space left beside the portable phone. */
 void HUDLine(UCanvas* Canvas,UFont* Font,const FString& Value,FLinearColor Color,float& Y,float Width)
 {
  TArray<FString> Words;Value.ParseIntoArrayWS(Words);FString Current;
  auto Draw=[&](){
   FCanvasTextItem Item(FVector2D(22,Y),MareLoc::Text(Current),Font,Color);
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
 // Menus, pause and options use the notebook (03/11): titles and labels on ink buttons in handwriting, the rest in Nunito.
 static const FButtonStyle& ActionButton=MareNotebook::InkButton();
 inline FSlateFontInfo FontFor(int32 Size,bool bHand){return bHand?MareNotebook::Hand(Size+3):MareNotebook::Body(Size);}
 TSharedRef<STextBlock> Text(const FString& Value,int32 Size=14,FLinearColor Color=MareNotebook::Ink)
 {
  const bool bOnInk=Color.Equals(FLinearColor::White),bTitle=Size>=16 && Color.Equals(MareNotebook::Ink);
  return SNew(STextBlock).Text(MareLoc::Text(Value)).Font(FontFor(Size,bOnInk || bTitle)).ColorAndOpacity(bOnInk?MareNotebook::Tag:bTitle?MareNotebook::Brown:Color).AutoWrapText(true);
 }
 TSharedRef<STextBlock> LiveText(TFunction<FString()> Value,int32 Size=14)
 {
  return SNew(STextBlock).Text_Lambda([Value](){return MareLoc::Text(Value());}).Font(MareNotebook::Body(Size)).ColorAndOpacity(MareNotebook::Ink).AutoWrapText(true);
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
  return FMath::Clamp(View.Y/720.f,.75f,1.8f)/UIScale*FMareOptions::Get().TextScale;   // accessibility: interface size option
 }
 TSharedRef<STextBlock> Txt(const FString& V,int32 Size,FLinearColor C,bool bBold=false,float Wrap=0)
 {
  auto T=SNew(STextBlock).Text(MareLoc::Text(V)).Font(FCoreStyle::GetDefaultFontStyle(bBold?"Bold":"Regular",Size)).ColorAndOpacity(C);
  if(Wrap>0)T->SetWrapTextAt(Wrap);
  return T;
 }
 TSharedRef<SWidget> Key(const FString& K){return SNew(SBorder).BorderImage(&KeyCap()).Padding(FMargin(7,2))[Txt(K,12,Hex(90,58,30),true)];}
 FSlateRenderTransform Tilt(float Degrees){return FSlateRenderTransform(FQuat2D(FMath::DegreesToRadians(Degrees)));}
}
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
  // LB/RB turn the notebook tabs (phone only: a station has a single page).
  const bool bPrev=Event.GetKey()==EKeys::Gamepad_LeftShoulder,bNext=Event.GetKey()==EKeys::Gamepad_RightShoulder;
  if((bPrev || bNext) && Station.IsNone()){const int32 N=TabTitles().Num();Tab=(Tab+(bNext?1:N-1))%N;Rebuild();MareGamepad::FocusSoon(AsShared(),Tab,false);return FReply::Handled();}
  return SCompoundWidget::OnKeyDown(Geometry,Event);
 }
private:
 TWeakObjectPtr<AMareController> Owner;
 TSharedPtr<SVerticalBox> Body;
 int64 DebtPick=0;   // debt payment waiting for "Confirmar" (cents)
 TSharedPtr<SEditableTextBox> DebtAmount;
 TSharedPtr<SEditableTextBox> CompanyName;
 int32 Tab=0;
 FName Station;
 FString Place=TEXT("kiosk");
 /** Reception: the nightly price the player is about to ask each waiting guest (starts at the guest's offer). */
 TMap<FString,double> Ask;
 /** Tours booth: the tour being guided and the choice made at each stop (0 good, 1 ok, 2 bad). */
 FString GuideTourId;
 TArray<int32> GuideChoices;
 /** Booth: the extras the player is about to offer the first group (colete, foto, lanche). */
 TSet<FString> OfferExtras;
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
  return SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).IsEnabled(bEnabled).ContentPadding(FMargin(9,2)).OnClicked_Lambda([this,Action](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.3f);Action();Rebuild();return FReply::Handled();})
   [SNew(STextBlock).Text(MareLoc::Text(Label)).Font(MareNotebook::Hand(16)).ColorAndOpacity(MareNotebook::Tag)];
 }
 /** Underlined handwritten link ("espiar", "dispensar"). */
 TSharedRef<SWidget> Link(const FString& Label,TFunction<void()> Action)
 {
  return SNew(SMarePadButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(3,0)).OnClicked_Lambda([this,Action](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.3f);Action();Rebuild();return FReply::Handled();})
   [SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(Label,16,MareNotebook::Brown)]+SVerticalBox::Slot().AutoHeight()[SNew(SBox).HeightOverride(1.5f)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Brown)]]];
 }
 void Title(const FString& V,const FString& Note=FString())
 {
  auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom).Padding(0,0,14,0)[SNew(STextBlock).Text(MareLoc::Text(V)).Font(MareNotebook::Hand(30)).ColorAndOpacity(MareNotebook::Ink)];
  if(!Note.IsEmpty())Row->AddSlot().FillWidth(1).VAlign(VAlign_Bottom).Padding(0,0,0,4)[MareNotebook::HandText(Note,17,MareNotebook::Green)];
  Body->AddSlot().AutoHeight().Padding(0,0,0,4)[Row];
 }
 void Heading(const FString& V,const FString& Note=FString())
 {
  auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom).Padding(0,0,8,0)[SNew(STextBlock).Text(MareLoc::Text(V)).Font(MareNotebook::Hand(22)).ColorAndOpacity(MareNotebook::Brown)];
  if(!Note.IsEmpty())Row->AddSlot().FillWidth(1).VAlign(VAlign_Bottom).Padding(0,0,0,2)[MareNotebook::HandText(Note,16,MareNotebook::Pencil)];
  Body->AddSlot().AutoHeight().Padding(0,10,0,2)[Row];
 }
 void Line(const FString& V,float Size=12,const FLinearColor& C=MareNotebook::Ink){Body->AddSlot().AutoHeight().Padding(0,2)[MareNotebook::BodyText(V,Size,C)];}
 void Pencil(const FString& V){Body->AddSlot().AutoHeight().Padding(0,2)[MareNotebook::HandText(V,17,MareNotebook::Pencil)];}
 /** N price tags per row; each tag gets a small fixed tilt so the page looks hand-pinned. */
 /** A card grid laid out one line of cards per row of the page, so a page too tall for the phone turns leaves between
  *  lines of cards (SMareFit) instead of cutting them; a filler keeps the first line's column widths on the others. */
 struct FRowGrid
 {
  TSharedPtr<SVerticalBox> Body;TMap<int32,TSharedPtr<SUniformGridPanel>> Lines;int32 Columns=0;
  SUniformGridPanel::FScopedWidgetSlotArguments AddSlot(int32 Column,int32 Row)
  {
   Columns=FMath::Max(Columns,Column+1);TSharedPtr<SUniformGridPanel>& Line=Lines.FindOrAdd(Row);
   if(!Line.IsValid()){Line=SNew(SUniformGridPanel).SlotPadding(FMargin(4,2));
    if(Row>0 && Columns>1)Line->AddSlot(Columns-1,0)[SNullWidget::NullWidget];
    Body->AddSlot().AutoHeight().Padding(0,Row?0:4,0,Row?0:0)[Line.ToSharedRef()];}
   return Line->AddSlot(Column,0);
  }
 };
 TSharedRef<FRowGrid> Grid(){auto G=MakeShared<FRowGrid>();G->Body=Body;return G;}
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
   Body->AddSlot().AutoHeight().Padding(0,4)[SNew(SBox).WidthOverride(320)[SAssignNew(CompanyName,SEditableTextBox).Text(MareLoc::Text(TEXT("Maré Alta"))).Font(MareNotebook::Hand(20))]];
   Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6)[Button(TEXT("Criar empresa"),[this,S](){S->CreateCompany(CompanyName->GetText().ToString());})];return;}
  bool bRequested=false;Company->TryGetBoolField(TEXT("kiosk_open"),bRequested);auto Hours=UMareSimulation::Object(Company,TEXT("sim"));
  Title(UMareSimulation::String(Company,TEXT("name")).IsEmpty()?FString(TEXT("Quiosque")):UMareSimulation::String(Company,TEXT("name")),
   S->IsOpen()?TEXT("aberto · recebendo clientes"):bRequested?TEXT("abertura ativada · aguardando o horário"):TEXT("fechado · use a placa do balcão"));
  auto G=Grid();bool bHired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bHired);
  G->AddSlot(0,0)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(TEXT("Hoje"),15,MareNotebook::Faded)]
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(19)).ColorAndOpacity(MareNotebook::Green).Text_Lambda([S](){return MareLoc::Text(FString::Printf(TEXT("entrou R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_in"))));})]
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(19)).ColorAndOpacity(MareNotebook::Red).Text_Lambda([S](){return MareLoc::Text(FString::Printf(TEXT("saiu R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_out"))));})],TiltOf(0))];
  G->AddSlot(1,0)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(TEXT("Atendimento"),15,MareNotebook::Faded)]
   +SVerticalBox::Slot().AutoHeight()[MareNotebook::BodyText(FString::Printf(TEXT("%.0fh às %.0fh"),UMareSimulation::Number(Hours,TEXT("start"),8),S->KioskCloseHour()),12.5f,MareNotebook::Ink,true)]
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(17)).ColorAndOpacity(MareNotebook::Ink).Text_Lambda([S](){return MareLoc::Text(FString::Printf(TEXT("%d pedidos ativos"),UMareSimulation::Object(S->State,TEXT("ue_orders"))->Values.Num()));})]
   +SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(bHired?TEXT("com atendente"):TEXT("você atende sozinho"),17,MareNotebook::Pencil)],TiltOf(1))];
  if(auto Audio=Owner->GetWorld()->GetSubsystem<UMareAudioWorld>())
   G->AddSlot(2,0)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::HandText(TEXT("Rádio"),15,MareNotebook::Faded)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareAudioWorld::RadioName(Audio->GetRadioStation()),12.5f,MareNotebook::Ink,true)]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left)[SNew(SWrapBox).UseAllottedSize(true)
     +SWrapBox::Slot().Padding(0,0,4,4)[Button(TEXT("anterior"),[Audio](){Audio->PrevRadioStation();})]
     +SWrapBox::Slot().Padding(0,0,4,4)[Button(TEXT("próxima"),[Audio](){Audio->NextRadioStation();})]
     +SWrapBox::Slot().Padding(0,0,4,4)[Button(TEXT("desligar"),[Audio](){Audio->SetRadioStation(TEXT("off"));})]],TiltOf(2))];
  if(!S->Carry().IsEmpty())Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,4)[Button(TEXT("Devolver o produto que está na mão"),[S](){S->ReturnCarry();})];
  // Agenda: today's event and tomorrow's forecast with the paid preparations (events.json).
  {const auto Today=S->EventDef(S->TodayEvent()),Next=S->EventDef(S->TomorrowEvent());
   Heading(TEXT("Agenda"),Today->Values.Num()?TEXT("hoje: ")+UMareSimulation::String(Today,TEXT("name")):FString(TEXT("hoje: dia normal")));
   Line(TEXT("Temporada: ")+UMareSimulation::String(S->Season(),TEXT("name")),12,MareNotebook::Green);
   if(Today->Values.Num())Line(UMareSimulation::String(Today,TEXT("blurb"))+(S->IsPrepActive()?TEXT(" Preparativos feitos."):TEXT("")),12,MareNotebook::Faded);
   if(Next->Values.Num()){const FString Kind=UMareSimulation::String(Next,TEXT("prep"));
    Line(TEXT("Amanhã: ")+UMareSimulation::String(Next,TEXT("name"))+TEXT(". ")+UMareSimulation::String(Next,TEXT("blurb")),12.5f,MareNotebook::Ink);
    const bool bPaid=int32(UMareSimulation::Number(S->State,TEXT("prep_day"),-1))==int32(UMareSimulation::Number(S->State,TEXT("day"),1))+1;
    if(!Kind.IsEmpty())Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,2)[Button(bPaid?FString(TEXT("Preparativos pagos")):FString::Printf(TEXT("%s · R$ %.0f"),
     Kind==TEXT("storm")?TEXT("Proteger o estoque"):TEXT("Encomendar decoração"),UMareSimulation::Number(UMareSimulation::Object(S->EventDefs(),TEXT("prep_cost")),Kind)),[S](){S->BuyPrep();},!bPaid)];}
   else Line(TEXT("Amanhã: dia normal."),12.5f,MareNotebook::Ink);}
  Heading(TEXT("Estoque pronto"),TEXT("(pegue na geladeira e no armário do quiosque)"));
  auto Stock=Grid();int32 I=0;
  for(const auto& Id:Products()){auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);
   Stock->AddSlot(I%4,I/4)[MareNotebook::PriceTag(SNew(SVerticalBox)+SVerticalBox::Slot().AutoHeight()[MareNotebook::BodyText(UMareSimulation::String(Dish,TEXT("name")),12,MareNotebook::Ink,true)]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(MareNotebook::Hand(18)).ColorAndOpacity_Lambda([S,Id](){return FSlateColor(S->IsDishUnlocked(Id) && S->Available(Id)>0?MareNotebook::Green:MareNotebook::Red);})
     .Text_Lambda([S,Id](){if(!S->IsDishUnlocked(Id))return MareLoc::Text(TEXT("precisa de expansão"));const int32 N=S->Available(Id);return MareLoc::Text(N>0?FString::Printf(TEXT("%d prontos"),N):TEXT("acabou · repor"));})],TiltOf(I))];++I;}
 }
 /** Grand Hotel restaurant: tables, kitchen, the tray, room service and the events book (MareRestaurant.cpp). */
 void RestaurantPage()
 {
  auto S=Sim();using namespace MareNotebook;auto R=S->Restaurant();const double Now=S->RestaurantNow();
  Title(TEXT("Restaurante"),S->IsRestaurantOpen()?TEXT("em serviço"):TEXT("fechado"));
  Line(FString::Printf(TEXT("Almoço 12h–15h e jantar 19h–22h · %.0f pratos servidos"),UMareSimulation::Number(R,TEXT("served"))),12,Faded);
  // 5.3: the stars of the critic's guide, the pier's fish in the kitchen and the last reviews.
  {const int32 Stars=S->RestaurantStars();const auto C=UMareSimulation::Object(S->RestaurantDefs(),TEXT("critic"));FString Row;
   for(int32 I=0;I<int32(UMareSimulation::Number(C,TEXT("max_stars"),3));++I)Row+=I<Stars?TEXT("*"):TEXT("-");
   Line(FString::Printf(TEXT("%s: %s (%d de %.0f estrelas) · peixes do píer na cozinha: %.0f"),*UMareSimulation::String(C,TEXT("guide")),*Row,Stars,UMareSimulation::Number(C,TEXT("max_stars"),3),
    UMareSimulation::Number(UMareSimulation::Object(S->State,TEXT("stock")),TEXT("peixe"))),12.5f,Stars?Green:Ink);
   const TArray<TSharedPtr<FJsonValue>>* Reviews=nullptr;UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("restaurant"))->TryGetArrayField(TEXT("reviews"),Reviews);
   if(Reviews && Reviews->Num()){const auto Last=(*Reviews)[Reviews->Num()-1]->AsObject();
    Line(FString::Printf(TEXT("Última crítica: dia %.0f, nota %.1f%s."),UMareSimulation::Number(Last,TEXT("day")),UMareSimulation::Number(Last,TEXT("score")),
     UMareSimulation::Number(Last,TEXT("crew"))>0?TEXT(" (atendido pela equipe)"):TEXT("")),11.5f,Faded);}
   Line(TEXT("Um crítico disfarçado aparece de vez em quando numa mesa: quem anota tudo num caderninho. Atenda rápido e com peixe fresco do píer."),11.5f,Faded);}
  auto DishName=[S](const FString& Id){return UMareSimulation::String(S->MenuDish(Id),TEXT("name"));};
  Heading(TEXT("Mesas"),TEXT("E na mesa anota o pedido e serve o prato"));
  const TArray<TSharedPtr<FJsonValue>>* Tables=nullptr;R->TryGetArrayField(TEXT("tables"),Tables);
  if(!Tables || Tables->IsEmpty())Line(TEXT("Nenhuma mesa ocupada."),13,Faded);
  else for(const auto& V:*Tables){const auto O=V->AsObject();const FString Stage=UMareSimulation::String(O,TEXT("stage"));
   const double Left=UMareSimulation::Number(O,TEXT("ready"))-Now;
   const FString What=Stage==TEXT("order")?TEXT("esperando você anotar"):Stage==TEXT("tray")?TEXT("na bandeja: ")+DishName(UMareSimulation::String(O,TEXT("dish")))
    :Left>0?FString::Printf(TEXT("%s · pronto em %.0f min"),*DishName(UMareSimulation::String(O,TEXT("dish"))),Left):DishName(UMareSimulation::String(O,TEXT("dish")))+TEXT(" · pronto no passe");
   Line(FString::Printf(TEXT("Mesa %.0f · %s · %s"),UMareSimulation::Number(O,TEXT("table"))+1,*UMareSimulation::String(O,TEXT("name")),*What),12.5f,Stage==TEXT("tray")?Green:Ink);}
  Heading(TEXT("Serviço de quarto"),TEXT("entregue no elevador do saguão"));
  const TArray<TSharedPtr<FJsonValue>>* Room=nullptr;R->TryGetArrayField(TEXT("room"),Room);
  if(!Room || Room->IsEmpty())Line(TEXT("Nenhum pedido das suítes."),13,Faded);
  else for(const auto& V:*Room){const auto O=V->AsObject();const bool bTray=UMareSimulation::String(O,TEXT("stage"))==TEXT("tray");const double Left=UMareSimulation::Number(O,TEXT("ready"))-Now;
   Line(FString::Printf(TEXT("Suíte %.0f · %s · %s"),UMareSimulation::Number(O,TEXT("suite")),*DishName(UMareSimulation::String(O,TEXT("dish"))),
    bTray?TEXT("na bandeja"):Left>0?*FString::Printf(TEXT("pronto em %.0f min"),Left):TEXT("pronto no passe")),12.5f,bTray?Green:Ink);}
  Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6)[Button(TEXT("Pegar pratos prontos"),[this,S](){if(S->PickUpPass()>0)UMareAudioWorld::Action(Owner.Get(),TEXT("bar_ice_glass"));})];
  Heading(TEXT("Eventos"),TEXT("marque para amanhã à noite"));
  const auto Booked=UMareSimulation::Object(R,TEXT("event"));const TArray<TSharedPtr<FJsonValue>>* Events=nullptr;S->RestaurantDefs()->TryGetArrayField(TEXT("events"),Events);
  if(Booked->Values.Num()){FString Name;if(Events)for(const auto& V:*Events)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==UMareSimulation::String(Booked,TEXT("id")))Name=UMareSimulation::String(V->AsObject(),TEXT("name"));
   Line(FString::Printf(TEXT("%s marcado para o dia %.0f às %.0fh."),*Name,UMareSimulation::Number(Booked,TEXT("day")),UMareSimulation::Number(S->RestaurantDefs(),TEXT("event_hour"),20)),13,Green);}
  else if(Events)for(const auto& V:*Events){const auto E=V->AsObject();const FString Id=UMareSimulation::String(E,TEXT("id"));
   auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[BodyText(FString::Printf(TEXT("%s · %.0f convidados · custo R$ %.0f · rende ~R$ %.0f"),
    *UMareSimulation::String(E,TEXT("name")),UMareSimulation::Number(E,TEXT("guests")),UMareSimulation::Number(E,TEXT("cost")),UMareSimulation::Number(E,TEXT("income"))),12)]
    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("Marcar"),[S,Id](){S->BookEvent(Id);},S->Money()>=UMareSimulation::Number(E,TEXT("cost")))];
   Body->AddSlot().AutoHeight().Padding(0,2)[Row];}
 }
 /** Pier booth: today's tours with buyers to serve, and the guided tour (three stops) in the departure hour. */
 void ToursPage()
 {
  auto S=Sim();using namespace MareNotebook;
  if(!GuideTourId.IsEmpty()){
   const auto Tour=S->TourDef(GuideTourId);const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;
   UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(GuideTourId,Stops);
   Title(UMareSimulation::String(Tour,TEXT("name")),FString::Printf(TEXT("guiando · parada %d de 3"),FMath::Min(GuideChoices.Num()+1,3)));
   if(!Tour || !Stops || !S->IsTourBoarding(GuideTourId)){GuideTourId.Reset();GuideChoices.Reset();Line(TEXT("O passeio não pode mais sair."),13,Red);return;}
   const auto Stop=(*Stops)[GuideChoices.Num()]->AsObject();
   Pencil(UMareSimulation::String(Stop,TEXT("text")));Line(TEXT("O que você faz?"),13,Faded);
   // The three choices in a stable shuffled order, so the good one is not always first.
   int32 Order[3]={0,1,2};const uint32 Seed=FCrc::StrCrc32(*GuideTourId)+GuideChoices.Num()*7;
   for(int32 I=2;I>0;--I){const int32 J=int32((Seed>>(I*3))%uint32(I+1));Swap(Order[I],Order[J]);}
   for(int32 K:Order){const TCHAR* Key=K==0?TEXT("good"):K==1?TEXT("ok"):TEXT("bad");
    Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,3)[Button(UMareSimulation::String(Stop,Key),[this,S,K](){
     GuideChoices.Add(K);
     if(GuideChoices.Num()>=3){const double Rating=S->GuideTour(GuideTourId,GuideChoices);GuideTourId.Reset();GuideChoices.Reset();
      UMareAudioWorld::Action(Owner.Get(),Rating>=4?TEXT("deal_accept"):TEXT("deal_decline"));if(Rating>0)UMareAudioWorld::Action(Owner.Get(),TEXT("money_coins"));}})];}
   return;}
  Title(TEXT("Passeios"),S->HasStaff(TEXT("guia"))?TEXT("o guia vende e leva quem você não levar"):TEXT("sem guia: venda e guie você mesmo"));
  for(const FString& Id:S->TourIds()){const auto Tour=S->TourDef(Id);const FString Status=S->TourStatus(Id);
   const int32 Queue=S->TourCount(TEXT("queue"),Id),Sold=S->TourCount(TEXT("sold"),Id),Seats=S->TourSeats(Tour);
   FString Note;
   if(Status==TEXT("guided"))Note=FString::Printf(TEXT("já saiu com você · nota %.1f"),UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("tours")),TEXT("rating")),Id));
   else if(Status==TEXT("guide"))Note=TEXT("já saiu com o guia");else if(Status==TEXT("cancelled"))Note=TEXT("cancelado hoje");else if(Status==TEXT("empty"))Note=TEXT("saiu vazio");
   else if(Status==TEXT("rescheduled"))Note=TEXT("remarcado para amanhã");
   else if(Status==TEXT("storm"))Note=TEXT("mar bravo: decida antes da saída");
   else Note=FString::Printf(TEXT("sai às %.0fh · R$ %.0f · %d de %d lugares vendidos"),UMareSimulation::Number(Tour,TEXT("hour")),S->TicketPrice(Id),Sold,Seats);
   Heading(UMareSimulation::String(Tour,TEXT("name")),Note);
   // Rough sea with tickets sold: refund or reschedule (it changes the rating).
   if(Status==TEXT("storm")){auto Storm=SNew(SHorizontalBox);
    Storm->AddSlot().AutoWidth().Padding(0,0,8,0)[Button(TEXT("Devolver o dinheiro"),[this,S,Id](){if(S->RefundTour(Id))UMareAudioWorld::Action(Owner.Get(),TEXT("money_coins"));})];
    Storm->AddSlot().AutoWidth()[Button(TEXT("Remarcar para amanhã"),[this,S,Id](){if(S->RescheduleTour(Id))UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"));})];
    Body->AddSlot().AutoHeight().Padding(0,2,0,6)[Storm];continue;}
   if(!Status.IsEmpty())continue;
   // Seats as boxes: sold, free; and the waiting list.
   {Line(FString::Printf(TEXT("Lugares: %d de %d ocupados · %d livres"),Sold,Seats,FMath::Max(0,Seats-Sold))+(S->TourWaitlist(Id)?FString::Printf(TEXT(" · lista de espera: %d grupo(s)"),S->TourWaitlist(Id)):FString()),12,Ink);}
   const auto Groups=S->TourGroups(Id);
   if(Groups.Num()){Line(FString::Printf(TEXT("Na fila: %s (%s)"),*UMareSimulation::String(Groups[0],TEXT("name")),*S->TourGroupLine(Groups[0]))
     +(Groups.Num()>1?FString::Printf(TEXT(" · mais %d grupo(s)"),Groups.Num()-1):FString()),12.5f,Ink);
    auto Extras=SNew(SHorizontalBox);
    Extras->AddSlot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[BodyText(TEXT("Oferecer:"),12,Faded)];
    for(const auto& Pair:UMareSimulation::Object(S->ToursDefs(),TEXT("extras"))->Values){const FString E(Pair.Key.ToView());const bool bOn=OfferExtras.Contains(E);
     Extras->AddSlot().AutoWidth().Padding(0,2,6,2)[Button((bOn?TEXT("» "):TEXT(""))+UMareSimulation::String(Pair.Value->AsObject(),TEXT("short")),[this,E](){if(OfferExtras.Contains(E))OfferExtras.Remove(E);else OfferExtras.Add(E);})];}
    Body->AddSlot().AutoHeight()[Extras];}
   auto Row=SNew(SHorizontalBox);
   Row->AddSlot().AutoWidth().Padding(0,0,8,0)[Button(Groups.Num()?FString::Printf(TEXT("Vender para %s"),*UMareSimulation::String(Groups[0],TEXT("name"))):Queue>0?FString::Printf(TEXT("Vender %d bilhete(s)"),FMath::Min(Queue,Seats-Sold)):FString(TEXT("Ninguém na fila")),[this,S,Id](){
    const int32 N=S->TourGroups(Id).Num()?S->SellTourGroup(Id,OfferExtras.Array()):S->SellTickets(Id);OfferExtras.Reset();
    if(N>0)UMareAudioWorld::Action(Owner.Get(),TEXT("money_register"));},Queue>0)];
   const bool bPiloted=Id==UMareSimulation::String(UMareSimulation::Object(S->ToursDefs(),TEXT("boat_tour")),TEXT("tour"));
   const bool bSnorkel=Id==UMareSimulation::String(UMareSimulation::Object(S->ToursDefs(),TEXT("snorkel_tour")),TEXT("tour"));
   const bool bTrail=Id==UMareSimulation::String(UMareSimulation::Object(S->ToursDefs(),TEXT("trail_tour")),TEXT("tour"));
   if(S->IsTourBoarding(Id) && bTrail)Row->AddSlot().AutoWidth()[Button(TEXT("Guiar a trilha agora"),[this](){
    if(Owner.IsValid())if(auto Tour=Owner->GetWorld()->GetSubsystem<UMareTrailWorld>()){AMareController* C=Owner.Get();C->ClosePhone();Tour->Start(C);}},Sold>0)];
   else if(S->IsTourBoarding(Id) && bSnorkel)Row->AddSlot().AutoWidth()[Button(TEXT("Guiar o mergulho agora"),[this](){
    if(Owner.IsValid())if(auto Tour=Owner->GetWorld()->GetSubsystem<UMareSnorkelWorld>()){AMareController* C=Owner.Get();C->ClosePhone();Tour->Start(C);}},Sold>0)];
   else if(S->IsTourBoarding(Id) && bPiloted)Row->AddSlot().AutoWidth()[Button(TEXT("Pilotar o passeio agora"),[this](){
    if(Owner.IsValid())if(auto Tour=Owner->GetWorld()->GetSubsystem<UMareBoatTourWorld>()){AMareController* C=Owner.Get();C->ClosePhone();Tour->Start(C);}},Sold>0)];
   else if(S->IsTourBoarding(Id))Row->AddSlot().AutoWidth()[Button(TEXT("Guiar o passeio agora"),[this,Id](){GuideTourId=Id;GuideChoices.Reset();},Sold>0)];
   Body->AddSlot().AutoHeight().Padding(0,2,0,6)[Row];}
  Line(TEXT("Ofereça os extras que o grupo quer (criança pede colete, quem chega com fome quer lanche, primeira vez quer foto): rende mais e sobe a nota. Insistir no que não querem baixa a nota."),12,Faded);
  Line(TEXT("Na hora da saída, guie você mesmo: cada parada bem conduzida dá gorjeta e fama. Sem você e sem guia, o passeio é cancelado e os bilhetes devolvidos."),12,Faded);
 }
 /** Pool table (03/11, "sinuca como jogo completo"): pick an opponent, play a friendly or a betting match of
  *  eight-ball, or the Campeonato da Maré round of the day; bracket and record on the same page. */
 FString PoolPick;
 void PoolPage()
 {
  auto S=Sim();using namespace MareNotebook;auto Room=Owner.IsValid()?Owner->GetWorld()->GetSubsystem<UMareGameRoom>():nullptr;if(!Room)return;
  const TArray<FString> Players=S->PoolPlayers();if(PoolPick.IsEmpty() && Players.Num())PoolPick=Players[FMath::Min(2,Players.Num()-1)];
  auto B=UMareSimulation::Object(S->State,TEXT("billiards"));
  {const int32 Played=UMareSimulation::Number(B,TEXT("played")),Won=UMareSimulation::Number(B,TEXT("won")),Cups=UMareSimulation::Number(B,TEXT("cups"));
   Title(TEXT("Mesa de sinuca"),FString::Printf(TEXT("bola 8 · %d %s, %d %s, %d %s"),Played,Played==1?TEXT("partida"):TEXT("partidas"),Won,Won==1?TEXT("vitória"):TEXT("vitórias"),
    Cups,Cups==1?TEXT("campeonato ganho"):TEXT("campeonatos ganhos")));}
  auto Play=[this,Room](double Stake,const FString& Who,bool bCupRound){auto PC=Owner.Get();if(!PC)return;PC->ClosePhone();Room->StartMatch(PC,Stake,Who,bCupRound);};
  Heading(TEXT("Adversário"),TEXT("escolha com quem jogar"));
  auto Pick=SNew(SWrapBox).UseAllottedSize(true);
  for(const FString& Who:Players)Pick->AddSlot().Padding(0,2,6,2)[Button((Who==PoolPick?TEXT("» "):TEXT(""))+Who+TEXT(" · ")+S->PoolLevel(Who),[this,Who](){PoolPick=Who;Rebuild();})];
  Body->AddSlot().AutoHeight().Padding(0,2,0,6)[Pick];
  auto Row=SNew(SWrapBox).UseAllottedSize(true);
  Row->AddSlot().Padding(0,2,8,2)[Button(TEXT("Amistoso"),[Play,this](){Play(0,PoolPick,false);})];
  const TArray<TSharedPtr<FJsonValue>>* Stakes=nullptr;
  if(S->GameRoomDefs()->TryGetArrayField(TEXT("stakes"),Stakes))for(const auto& V:*Stakes){const double Bet=V->AsNumber();
   Row->AddSlot().Padding(0,2,8,2)[Button(FString::Printf(TEXT("Valendo R$ %.0f"),Bet),[Play,this,Bet](){Play(Bet,PoolPick,false);},S->Money()>=Bet)];}
  Body->AddSlot().AutoHeight().Padding(0,0,0,8)[Row];
  const auto Cup=UMareSimulation::Object(S->GameRoomDefs(),TEXT("cup"));const FString CupName=UMareSimulation::String(Cup,TEXT("name"));
  if(!S->PoolCupActive()){
   Heading(CupName,FString::Printf(TEXT("8 jogadores, mata-mata, uma rodada por dia · prêmio R$ %.0f, vice R$ %.0f"),UMareSimulation::Number(Cup,TEXT("prize")),UMareSimulation::Number(Cup,TEXT("runner_up"))));
   int32 NextDay=0;
   if(S->PoolCupSignupOpen(NextDay))Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,2,0,6)[Button(FString::Printf(TEXT("Inscrever-se · R$ %.0f"),UMareSimulation::Number(Cup,TEXT("fee"))),[S](){S->PoolCupJoin();},S->Money()>=UMareSimulation::Number(Cup,TEXT("fee")))];
   else Line(FString::Printf(TEXT("Campeonato semanal: as próximas inscrições abrem no dia %d."),NextDay),13,Faded);
   const FString Last=UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("billiards")),TEXT("cup")),TEXT("last_champion"));
   if(!Last.IsEmpty())Line(TEXT("Último campeão: ")+Last,13,Faded);}
  else{const TArray<FString> Alive=S->PoolCupAlive();FString Why;const bool bReady=S->PoolCupReady(Why);
   Heading(CupName,S->PoolCupRoundName());
   FString Bracket;for(int32 I=0;I+1<Alive.Num();I+=2)Bracket+=(Bracket.IsEmpty()?TEXT(""):TEXT("\n"))+Alive[I]+TEXT(" × ")+Alive[I+1];
   Pencil(Bracket);
   if(bReady){const FString Rival=S->PoolCupOpponent();
    Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,2,0,6)[Button(TEXT("Jogar a ")+S->PoolCupRoundName()+TEXT(" contra ")+Rival,[Play,Rival](){Play(0,Rival,true);})];}
   else Line(Why,13,Faded);}
  const TArray<TSharedPtr<FJsonValue>>* Log=nullptr;
  if(UMareSimulation::Object(B,TEXT("cup"))->TryGetArrayField(TEXT("log"),Log) && Log->Num()){FString Last;
   for(int32 I=FMath::Max(0,Log->Num()-4);I<Log->Num();++I)Last+=(Last.IsEmpty()?TEXT(""):TEXT("\n"))+(*Log)[I]->AsString();
   Line(Last,12,Faded);}
  Line(TEXT("Bola 8: depois da saída, quem encaçapar primeiro fica com lisas ou listradas. Acerte sempre uma bola sua primeiro; falta dá bola na mão ao adversário. A 8 só no fim."),12,Faded);
 }
 /** Table tennis (03/11): pick an opponent, a friendly or a betting match, best of 3 games of 11; the record. */
 void TableTennisPage()
 {
  auto S=Sim();using namespace MareNotebook;auto TT=Owner.IsValid()?Owner->GetWorld()->GetSubsystem<UMareTableTennis>():nullptr;if(!TT)return;
  const TArray<FString> Players=S->PoolPlayers();if(PoolPick.IsEmpty() && Players.Num())PoolPick=Players[FMath::Min(2,Players.Num()-1)];
  auto B=UMareSimulation::Object(S->State,TEXT("table_tennis"));
  {const int32 Played=UMareSimulation::Number(B,TEXT("played")),Won=UMareSimulation::Number(B,TEXT("won"));
   Title(TEXT("Tênis de mesa"),FString::Printf(TEXT("melhor de 3 games de 11 · %d %s, %d %s"),Played,Played==1?TEXT("partida"):TEXT("partidas"),Won,Won==1?TEXT("vitória"):TEXT("vitórias")));}
  auto Play=[this,TT](double Stake,const FString& Who){auto PC=Owner.Get();if(!PC)return;PC->ClosePhone();TT->StartMatch(PC,Who,Stake);};
  Heading(TEXT("Adversário"),TEXT("escolha com quem jogar"));
  auto Pick=SNew(SWrapBox).UseAllottedSize(true);
  for(const FString& Who:Players)Pick->AddSlot().Padding(0,2,6,2)[Button((Who==PoolPick?TEXT("» "):TEXT(""))+Who+TEXT(" · ")+S->PoolLevel(Who),[this,Who](){PoolPick=Who;Rebuild();})];
  Body->AddSlot().AutoHeight().Padding(0,2,0,6)[Pick];
  auto Row=SNew(SWrapBox).UseAllottedSize(true);
  Row->AddSlot().Padding(0,2,8,2)[Button(TEXT("Amistoso"),[Play,this](){Play(0,PoolPick);})];
  const TArray<TSharedPtr<FJsonValue>>* Stakes=nullptr;
  if(S->GameRoomDefs()->TryGetArrayField(TEXT("stakes"),Stakes))for(const auto& V:*Stakes){const double Bet=V->AsNumber();
   Row->AddSlot().Padding(0,2,8,2)[Button(FString::Printf(TEXT("Valendo R$ %.0f"),Bet),[Play,this,Bet](){Play(Bet,PoolPick);},S->Money()>=Bet)];}
  Body->AddSlot().AutoHeight().Padding(0,0,0,8)[Row];
  Line(TEXT("O saque quica primeiro do seu lado e depois do outro; rede no saque repete o ponto. Na troca de bola, devolva depois de um quique. Mova a raquete até a bola: o ponto onde ela bate e o movimento do mouse dão a direção; segurando o clique você corta, mais forte e mais arriscado."),12,Faded);
 }
 /** Phone tabs; "Drinks" (the bar's recipe book) only once the bar is bought. */
 TArray<FString> TabTitles()const
 {
  TArray<FString> T={TEXT("Quiosque"),TEXT("Compras"),TEXT("Equipe"),TEXT("Finanças"),TEXT("Resort"),TEXT("Missões"),TEXT("Personalizar")};
  bool bBar=false,bTours=false;if(auto S=Sim()){UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("bar"),bBar);
   UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("passeios"),bTours);}
  if(bBar)T.Add(TEXT("Drinks"));if(bTours)T.Add(TEXT("Passeios"));return T;
 }
 /** Recipe book of the Bar do Coqueiro (CHECKLIST_EXPANSOES 1.3): known drinks with ingredients, price and prep steps;
  *  unknown ones as "???" with the hint; the secret house drink; the "Mestre dos drinks" achievement. */
 void DrinksPage()
 {
  auto S=Sim();using namespace MareNotebook;auto Defs=S->BarDefs();
  auto IngredientName=[&Defs](const FString& Id){const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(Defs->TryGetArrayField(TEXT("ingredients"),L))
   for(const auto& V:*L)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==Id)return UMareSimulation::String(V->AsObject(),TEXT("name"));return Id;};
  int32 Known=0,Total=0;const TArray<TSharedPtr<FJsonValue>>* Recipes=nullptr;Defs->TryGetArrayField(TEXT("recipes"),Recipes);
  if(Recipes)for(const auto& V:*Recipes){if(!S->IsBarItemAvailable(V->AsObject()))continue;++Total;Known+=S->IsRecipeKnown(UMareSimulation::String(V->AsObject(),TEXT("id")));}
  Title(TEXT("Caderno de drinks"),FString::Printf(TEXT("%d de %d receitas"),Known,Total));
  Line(S->HasBarAchievement()?TEXT("Conquista: Mestre dos drinks! Todas as receitas descobertas."):TEXT("Misture no copo da bancada para descobrir receitas novas (cada uma dá fama)."),12,S->HasBarAchievement()?Green:Faded);
  const auto Lines=UMareSimulation::Object(Defs,TEXT("prep_lines"));
  if(Recipes)for(const auto& V:*Recipes){const auto R=V->AsObject();const FString Id=UMareSimulation::String(R,TEXT("id"));bool bSecret=false;R->TryGetBoolField(TEXT("secret"),bSecret);
   if(!S->IsBarItemAvailable(R))continue;
   if(S->IsRecipeKnown(Id)){TArray<FString> Parts,Mix;const TArray<TSharedPtr<FJsonValue>>* Needs=nullptr;
    if(R->TryGetArrayField(TEXT("needs"),Needs))for(const auto& N:*Needs){Parts.Add(IngredientName(N->AsString()));Mix.Add(N->AsString());}
    TArray<FString> Steps;for(const FString& St:S->BarPrepSteps(Mix))Steps.Add(UMareSimulation::String(Lines,St));
    Heading(UMareSimulation::String(R,TEXT("name"))+(bSecret?TEXT(" · receita secreta"):TEXT("")),FString::Printf(TEXT("R$ %.0f"),S->DrinkPrice(Id)));
    Line(FString::Join(Parts,TEXT(" + "))+TEXT("  ·  ")+FString::Join(Steps,TEXT(", ")),12,Ink);}
   else Line(FString(bSecret?TEXT("??? (receita secreta)"):TEXT("???"))+TEXT(" · dica: ")+UMareSimulation::String(R,TEXT("hint")),12.5f,Faded);}
 }
 /** Tour results (CHECKLIST_EXPANSOES 2.5): each tour that left with stars, tip, photos sold and the written reviews,
  *  word of mouth for today, and what the Personalizar upgrades do on the tours. */
 void TourResultsPage()
 {
  auto S=Sim();using namespace MareNotebook;const auto Results=S->TourResults();
  Title(TEXT("Passeios"),Results.Num()?FString::Printf(TEXT("%d passeio(s) avaliado(s)"),Results.Num()):FString(TEXT("nenhum passeio avaliado ainda")));
  for(const FString& Id:S->TourIds()){const int32 B=S->TourBuzz(Id);if(B==0)continue;
   const FString Name=UMareSimulation::String(S->TourDef(Id),TEXT("name"));
   Line(B>0?FString::Printf(TEXT("Boca a boca: +%d pessoa(s) hoje no %s (nota boa ontem)."),B,*Name):FString::Printf(TEXT("Boca a boca: %d pessoa(s) a menos hoje no %s (nota ruim ontem)."),-B,*Name),12,B>0?Green:Red);}
  if(Results.IsEmpty())Line(TEXT("Guie um passeio na hora da saída (ou contrate um guia): a nota, a gorjeta e o que os turistas escreveram aparecem aqui."),12,Faded);
  int32 Shown=0;for(const auto& R:Results){if(++Shown>5)break;bool bGuide=false;R->TryGetBoolField(TEXT("guide"),bGuide);
   const double Rating=UMareSimulation::Number(R,TEXT("rating"));
   Heading(UMareSimulation::String(R,TEXT("name"))+(bGuide?TEXT(" · com o guia"):TEXT(" · guiado por você")),FString::Printf(TEXT("dia %.0f · nota %.1f de 5"),UMareSimulation::Number(R,TEXT("day")),Rating).Replace(TEXT("."),TEXT(",")));
   FString Money=FString::Printf(TEXT("%.0f pessoa(s) · gorjeta R$ %.0f"),UMareSimulation::Number(R,TEXT("pax")),UMareSimulation::Number(R,TEXT("tip")));
   if(UMareSimulation::Number(R,TEXT("prints"))>0)Money+=FString::Printf(TEXT(" · %.0f foto(s) vendidas: R$ %.0f"),UMareSimulation::Number(R,TEXT("prints")),UMareSimulation::Number(R,TEXT("photos")));
   Line(Money,12,Ink);
   const TArray<TSharedPtr<FJsonValue>>* Reviews=nullptr;
   if(R->TryGetArrayField(TEXT("reviews"),Reviews))for(const auto& V:*Reviews){const auto Rv=V->AsObject();const int32 Stars=int32(UMareSimulation::Number(Rv,TEXT("stars"),3));
    Line(FString::Printf(TEXT("\"%s\" (%s, %d de 5)"),*UMareSimulation::String(Rv,TEXT("text")),*UMareSimulation::String(Rv,TEXT("who")),Stars),12.5f,Stars>=4?Green:Stars<=2?Red:Faded);}}
  Heading(TEXT("Melhorias dos passeios"),TEXT("em Personalizar · Passeios"));
  auto Tier=[S](const FString& Slot){const auto Def=S->CustomSlot(TEXT("passeios"),Slot);const int32 T=S->CustomTier(TEXT("passeios"),Slot);const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;
   return Def && Def->TryGetArrayField(TEXT("tiers"),Tiers) && Tiers->IsValidIndex(T-1)?UMareSimulation::String((*Tiers)[T-1]->AsObject(),TEXT("name")):FString();};
  Line(TEXT("Barco: ")+Tier(TEXT("barco"))+TEXT(" (no passeio de barco: mais rápido e o turista enjoa menos)"),12,Ink);
  Line(TEXT("Mergulho: ")+Tier(TEXT("mergulho"))+TEXT(" (no snorkel: enxerga mais longe e cada espécie vale mais)"),12,Ink);
  Line(TEXT("Fotos: ")+Tier(TEXT("fotos"))+TEXT(" (o fotógrafo vende fotos depois de cada passeio; mais com nota alta)"),12,Ink);
  Line(TEXT("Roteiros: ")+Tier(TEXT("roteiro"))+TEXT(" (no nível \"Pôr do sol no mar\" abre o passeio de jangada no fim da tarde)"),12,Ink);
  Line(TEXT("O guia contratado faz o passeio sozinho com nota 3, sem gorjeta. Indo junto, a nota, a gorjeta e a fama sobem."),12,Faded);
 }
 /** Bar do Coqueiro: guests' orders, the shaker and the ingredient shelf, the recipe book (MareBar.cpp). */
 void BarPage()
 {
  auto S=Sim();using namespace MareNotebook;auto B=S->Bar();auto Defs=S->BarDefs();
  auto IngredientName=[&Defs](const FString& Id){const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(Defs->TryGetArrayField(TEXT("ingredients"),L))
   for(const auto& V:*L)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==Id)return UMareSimulation::String(V->AsObject(),TEXT("name"));return Id;};
  const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;Defs->TryGetArrayField(TEXT("open"),Open);
  Title(TEXT("Bar do Coqueiro"),S->IsBarOpen()?FString::Printf(TEXT("aberto · %.0f drinks servidos"),UMareSimulation::Number(B,TEXT("served")))
   :FString::Printf(TEXT("fechado · abre das %.0fh às %.0fh"),Open && Open->Num()==2?(*Open)[0]->AsNumber():10.,Open && Open->Num()==2?(*Open)[1]->AsNumber():23.));
  const TArray<TSharedPtr<FJsonValue>>* Orders=nullptr;B->TryGetArrayField(TEXT("orders"),Orders);
  Heading(TEXT("Pedidos no balcão"),S->HasStaff(TEXT("bartender"))?TEXT("o bartender serve o que está no cardápio"):TEXT("escolha quem vai atender"));
  const FString Serving=S->BarServing();
  if(!Orders || Orders->IsEmpty())Line(TEXT("Ninguém no balcão agora."),13,Faded);
  else for(const auto& V:*Orders){const auto O=V->AsObject();const FString Id=UMareSimulation::String(O,TEXT("id")),Want=UMareSimulation::String(O,TEXT("want"));
   const double Waited=UMareSimulation::Number(S->State,TEXT("day"),1)*1440+UMareSimulation::Number(S->State,TEXT("minutes"))-UMareSimulation::Number(O,TEXT("since"));
   const FString What=S->BarBubble(O);
   auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,8,0)
    [Button(Serving==Id?TEXT("atendendo"):TEXT("atender"),[S,Id](){S->SetBarServing(Id);},true)]
    +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[BodyText(FString::Printf(TEXT("%s · %s · espera %.0f min"),*UMareSimulation::String(O,TEXT("name")),*What,Waited),12.5f,Serving==Id?Ink:Faded,Serving==Id)];
   Body->AddSlot().AutoHeight().Padding(0,2)[Row];}
  // Regulars and their usual (the player has to remember who drinks what).
  {TArray<FString> Regs;for(const auto& Pair:S->BarRegulars())if(auto R=S->BarRecipe(Pair.Value))Regs.Add(Pair.Key+TEXT(": ")+UMareSimulation::String(R,TEXT("name")));
   if(Regs.Num()){Heading(TEXT("Fregueses fiéis"),TEXT("pedem \"o de sempre\""));Line(FString::Join(Regs,TEXT(" · ")),12,Ink);}}
  if(S->IsBarRush())Line(TEXT("Bar lotado: happy hour ou noite de lua cheia!"),13,Green);
  // Physical prep: the bench at the back holds the ingredients; E on the work glass pours, mixes and serves.
  TArray<FString> Names;for(const FString& I:S->BarGlass())Names.Add(IngredientName(I));
  const FString Next=S->BarNextStep();const auto Lines=UMareSimulation::Object(Defs,TEXT("prep_lines"));
  Heading(TEXT("Copo de preparo"),Names.IsEmpty()?TEXT("vazio"):FString::Join(Names,TEXT(" + ")));
  Line(Names.IsEmpty()?TEXT("Pegue os ingredientes na bancada do fundo (E) e coloque no copo (E). Depois use o copo para socar, bater e servir.")
   :!Next.IsEmpty()?TEXT("Falta: ")+UMareSimulation::String(Lines,Next)+TEXT(" (E no copo)"):TEXT("Pronto! E no copo serve o cliente que você está atendendo."),12,Faded);
  Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,4)[Button(TEXT("Jogar fora"),[this,S](){
   if(S->BarDiscard()>0)UMareAudioWorld::Action(Owner.Get(),TEXT("cleaning_trash"),nullptr,.6f);},!Names.IsEmpty())];
  auto Stock=UMareSimulation::Object(B,TEXT("stock"));
  TArray<FString> Shelf;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
  if(Defs->TryGetArrayField(TEXT("ingredients"),List))for(const auto& V:*List){const FString Id=UMareSimulation::String(V->AsObject(),TEXT("id"));
   Shelf.Add(FString::Printf(TEXT("%s %d"),*UMareSimulation::String(V->AsObject(),TEXT("name")),int32(UMareSimulation::Number(Stock,Id))));}
  Heading(TEXT("Bancada"),FString::Printf(TEXT("até %d no copo"),int32(UMareSimulation::Number(Defs,TEXT("max_mix"),5))));
  Line(FString::Join(Shelf,TEXT(" · ")),12,Ink);
  const double Cost=S->BarRestockCost();
  Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6)[Button(Cost>0?FString::Printf(TEXT("Repor ingredientes · R$ %.0f"),Cost):FString(TEXT("Estoque cheio")),[S](){S->RestockBar();},Cost>0 && S->Money()>=Cost)];
  Heading(TEXT("Melhorias do bar"),TEXT("5 níveis cada"));
  for(const auto& Pair:UMareSimulation::Object(Defs,TEXT("upgrades"))->Values){const FString Id(Pair.Key.ToView());const auto U=Pair.Value->AsObject();
   const int32 Level=S->BarUpgrade(Id);const double UCost=S->BarUpgradeCost(Id);
   auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
    [BodyText(FString::Printf(TEXT("%s · nível %d/5 · %s"),*UMareSimulation::String(U,TEXT("name")),Level,*UMareSimulation::String(U,TEXT("desc"))),12,Level?Ink:Faded)]
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8,0,0,0)
    [Button(UCost>0?FString::Printf(TEXT("Melhorar · R$ %.0f"),UCost):FString(TEXT("Máximo")),[this,S,Id](){if(S->BuyBarUpgrade(Id))UMareAudioWorld::Action(Owner.Get(),TEXT("money_coins"));},UCost>0 && S->Money()>=UCost)];
   Body->AddSlot().AutoHeight().Padding(0,2)[Row];}
  if(S->HasStaff(TEXT("bartender"))){TArray<FString> Book;for(const FString& R:S->BarmanKnows())if(auto RR=S->BarRecipe(R))Book.Add(UMareSimulation::String(RR,TEXT("name")));
   Line(FString::Printf(TEXT("Bartender nível %d sabe: %s"),S->BarmanLevel(),*FString::Join(Book,TEXT(", "))),12,Faded);}
  int32 Known=0,Total=0;const TArray<TSharedPtr<FJsonValue>>* Recipes=nullptr;Defs->TryGetArrayField(TEXT("recipes"),Recipes);
  if(Recipes)for(const auto& V:*Recipes){++Total;Known+=S->IsRecipeKnown(UMareSimulation::String(V->AsObject(),TEXT("id")));}
  Heading(TEXT("Receitas"),FString::Printf(TEXT("%d de %d descobertas · cada descoberta dá fama"),Known,Total));
  if(Recipes)for(const auto& V:*Recipes){const auto R=V->AsObject();const FString Id=UMareSimulation::String(R,TEXT("id"));
   if(S->IsRecipeKnown(Id)){TArray<FString> Parts;const TArray<TSharedPtr<FJsonValue>>* Needs=nullptr;
    if(R->TryGetArrayField(TEXT("needs"),Needs))for(const auto& N:*Needs)Parts.Add(IngredientName(N->AsString()));
    Line(FString::Printf(TEXT("%s · R$ %.0f · %s"),*UMareSimulation::String(R,TEXT("name")),S->DrinkPrice(Id),*FString::Join(Parts,TEXT(", "))),12,Ink);}
   else Line(TEXT("??? · dica: ")+UMareSimulation::String(R,TEXT("hint")),12,Faded);}
 }
 /** Pousada reception: waiting guests with their offer, ask/counter buttons, and the room board. */
 void ReceptionPage(const FString& Where)
 {
  auto S=Sim();using namespace MareNotebook;S->SyncRooms();const bool bHotel=Where==TEXT("hotel");
  const int32 Free=S->FreeCleanRooms(Where);
  Title(bHotel?TEXT("Recepção do Grand Hotel"):TEXT("Recepção da pousada"));
  Line(FString::Printf(TEXT("%s livres: %d de %d · diária de referência R$ %.0f"),bHotel?TEXT("Quartos limpos"):TEXT("Quartos limpos"),Free,bHotel?32:S->PousadaRooms(),S->StayRate(Where)),13,Faded);
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
   // Name on its own line and the details below it: the narrow station page squeezed them side by side.
   Heading(FString::Printf(TEXT("%s · %s"),*UMareSimulation::String(G,TEXT("name")),*UMareSimulation::String(G,TEXT("label"))));
   Line(FString::Printf(TEXT("%.0f noite(s) · humor: %s · rodada %.0f de 3"),UMareSimulation::Number(G,TEXT("nights")),*Humor,UMareSimulation::Number(G,TEXT("round"))+1),12,Faded);
   Line(FString::Printf(TEXT("Oferece R$ %.0f por noite. Você pede R$ %.0f."),Offer,Price),14,Ink);
   auto Row=SNew(SHorizontalBox);auto Deal=SNew(SHorizontalBox);
   for(const int32 Step:{-10,-5,5,10})Row->AddSlot().AutoWidth().Padding(0,0,6,0)[Button(FString::Printf(TEXT("%+d%%"),Step),[this,Id,Step,Offer](){double& P=Ask.FindOrAdd(Id,Offer);P=FMath::Max(Offer,FMath::RoundToDouble(P*(1+Step/100.)));},true)];
   Deal->AddSlot().AutoWidth().Padding(0,0,6,0)[Button(FString::Printf(TEXT("Pedir R$ %.0f"),Price),[this,S,Id](){double Out=0;const double P=Ask.FindRef(Id);
    // The guest at the desk reacts on the face: a smile when the deal closes, annoyance at a counter-offer or leaving.
    auto Stays=Owner.IsValid() && Owner->GetWorld()?Owner->GetWorld()->GetSubsystem<UMareStaysWorld>():nullptr;
    switch(S->Haggle(Id,P,Out)){
     case UMareSimulation::EHaggle::Accepted:S->LastMessage=FString::Printf(TEXT("Fechado por R$ %.0f a noite. Chave entregue."),Out);Ask.Remove(Id);if(Stays)Stays->GuestExpress(Id,TEXT("smile"));
      UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"));UMareAudioWorld::Action(Owner.Get(),TEXT("reception_keys"));break;
     case UMareSimulation::EHaggle::Countered:S->LastMessage=FString::Printf(TEXT("Contraproposta: R$ %.0f por noite."),Out);Ask.Add(Id,Out);if(Stays)Stays->GuestExpress(Id,TEXT("annoyed"));UMareAudioWorld::Action(Owner.Get(),TEXT("reception_checkin"),nullptr,.6f);break;
     case UMareSimulation::EHaggle::Left:Ask.Remove(Id);if(Stays)Stays->GuestExpress(Id,TEXT("annoyed"),6.f);UMareAudioWorld::Action(Owner.Get(),TEXT("deal_decline"));break;
     default:S->LastMessage=TEXT("Sem quarto limpo livre.");}},Free>0)];
   Deal->AddSlot().AutoWidth()[Button(FString::Printf(TEXT("Aceitar R$ %.0f"),Offer),[this,S,Id,Offer](){if(S->AcceptOffer(Id)){S->LastMessage=FString::Printf(TEXT("Check-in por R$ %.0f a noite."),Offer);Ask.Remove(Id);
    if(auto W=Owner.IsValid()?Owner->GetWorld():nullptr)if(auto Stays=W->GetSubsystem<UMareStaysWorld>())Stays->GuestExpress(Id,TEXT("smile"));
    UMareAudioWorld::Action(Owner.Get(),TEXT("reception_checkin"));UMareAudioWorld::Action(Owner.Get(),TEXT("reception_keys"));}else S->LastMessage=TEXT("Sem quarto limpo livre.");},Free>0)];
   Body->AddSlot().AutoHeight().Padding(0,2,0,2)[Row];
   Body->AddSlot().AutoHeight().Padding(0,2,0,8)[Deal];
  }
  if(bHotel){HotelBoard(true);return;}   // 5.1: room counts, the visitable 3rd floor and the phone complaints
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
 /** 5.2: events on the beach (MareHotelEvents.cpp): the offer with Aceitar/Recusar, then the set-up progress. */
 void HotelEventBoard()
 {
  auto S=Sim();using namespace MareNotebook;const auto E=UMareSimulation::Object(S->State,TEXT("hotel_events"));
  const TSharedPtr<FJsonObject>* OfferP=nullptr;const auto B=S->BookedHotelEvent();
  if(E->TryGetObjectField(TEXT("offer"),OfferP)){const auto O=*OfferP;const auto Def=S->HotelEventKind(UMareSimulation::String(O,TEXT("kind")));
   Heading(TEXT("Pedido de evento"),UMareSimulation::String(Def,TEXT("name")));
   Line(FString::Printf(TEXT("%s · amanhã às %.0fh · R$ %.0f · %d peças para montar na praia"),*UMareSimulation::String(O,TEXT("client")),UMareSimulation::Number(Def,TEXT("hour"),16),
    UMareSimulation::Number(O,TEXT("fee")),Def->HasField(TEXT("pieces"))?Def->GetArrayField(TEXT("pieces")).Num():0),12.5f,Ink);
   auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(TEXT("Aceitar"),[this,S](){if(S->AcceptHotelEvent())UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"));})]
    +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("Recusar"),[S](){S->DeclineHotelEvent();})];
   Body->AddSlot().AutoHeight().Padding(0,2,0,4)[Row];
   Line(TEXT("Paga pelo que estiver montado quando os convidados chegarem; com menos da metade, fica só o sinal e a fama cai."),11.5f,Faded);}
  else if(B){const auto Def=S->HotelEventKind(UMareSimulation::String(B,TEXT("kind")));const FString St=UMareSimulation::String(B,TEXT("state"));
   const int32 Day=UMareSimulation::Number(S->State,TEXT("day"),1),EvDay=UMareSimulation::Number(B,TEXT("day"));
   Heading(TEXT("Evento marcado"),FString::Printf(TEXT("%s · %s às %.0fh"),*UMareSimulation::String(Def,TEXT("name")),EvDay>Day?TEXT("amanhã"):TEXT("hoje"),UMareSimulation::Number(B,TEXT("hour"))));
   if(St==TEXT("show"))Line(FString::Printf(TEXT("Os convidados chegaram · %s pagou R$ %.0f."),*UMareSimulation::String(B,TEXT("client")),UMareSimulation::Number(B,TEXT("paid"))),12.5f,Green);
   else{const int32 Placed=S->HotelEventCount(false,true),All=S->HotelEventCount(false,false);
    Line(FString::Printf(TEXT("Peças montadas: %d de %d · capricho: %d de %d"),Placed,All,S->HotelEventCount(true,true),S->HotelEventCount(true,false)),12.5f,Placed>=All?Green:Ink);
    Line(EvDay>Day?FString::Printf(TEXT("Amanhã, a partir das %.0fh, a planta aparece na praia a leste do hotel, perto do farol: E em cada peça transparente para montar."),UMareSimulation::Number(S->HotelEventDefs(),TEXT("setup_from"),6))
     :FString(TEXT("A planta está na praia a leste do hotel, perto do farol: E em cada peça transparente para montar antes dos convidados.")),11.5f,Faded);}}
 }
 /** 5.1: the Grand Hotel rooms (how many free, taken and being cleaned; the visitable 3rd floor with what is left to do)
  *  and the guests' complaints by phone, each with the technician button. bRooms false: only the complaints. */
 void HotelBoard(bool bRooms)
 {
  auto S=Sim();using namespace MareNotebook;S->SyncRooms();
  if(bRooms){
   Heading(TEXT("Quartos do hotel"),FString::Printf(TEXT("%d livres · %d ocupados · %d em arrumação"),S->HotelRoomsIn(TEXT("free")),S->HotelRoomsIn(TEXT("occupied")),S->HotelRoomsIn(TEXT("dirty"))));
   const TArray<TSharedPtr<FJsonValue>>* Visitable=nullptr;S->HotelRoomDefs()->TryGetArrayField(TEXT("visitable"),Visitable);
   for(int32 I=0;Visitable && I<Visitable->Num();++I){const auto R=S->HotelRoom(I);if(!R)continue;const FString St=UMareSimulation::String(R,TEXT("state"));FString Text;
    if(St==TEXT("occupied"))Text=FString::Printf(TEXT("%s · %s · mais %.0f noite(s)"),*S->HotelRoomName(I),*UMareSimulation::String(UMareSimulation::Object(R,TEXT("guest")),TEXT("name")),UMareSimulation::Number(R,TEXT("nights")));
    else if(St==TEXT("dirty")){TArray<FString> Left;const TArray<TSharedPtr<FJsonValue>>* T=nullptr;
     if(R->TryGetArrayField(TEXT("tasks"),T))for(const auto& V:*T)Left.Add(S->HotelTaskLabel(V->AsString()).ToLower());
     Text=FString::Printf(TEXT("%s · falta: %s"),*S->HotelRoomName(I),*FString::Join(Left,TEXT(", ")));}
    else Text=FString::Printf(TEXT("%s · limpo e livre"),*S->HotelRoomName(I));
    Line(Text,12.5f,St==TEXT("dirty")?Red:St==TEXT("occupied")?Ink:Green);}
   Line(TEXT("Os quartos 301, 302 e 303 ficam no 3º andar (elevador do saguão): arrumados só por você, o próximo hóspede dá nota melhor. A equipe de arrumação cuida dos outros e chega ao 3º andar depois das 11h."),11.5f,Faded);}
  if(bRooms)HotelEventBoard();
  const auto Complaints=S->HotelComplaints();
  Heading(TEXT("Telefone do hotel"),Complaints.Num()?FString::Printf(TEXT("%d reclamação(ões)"),Complaints.Num()):FString(TEXT("nenhuma reclamação")));
  for(const auto& C:Complaints){const FString Id=UMareSimulation::String(C,TEXT("id"));const auto Def=S->ComplaintKind(UMareSimulation::String(C,TEXT("kind")));
   const int32 Room=UMareSimulation::Number(C,TEXT("room"),-1);const double Cost=UMareSimulation::Number(Def,TEXT("cost"));const double Left=FMath::Max(0.,S->ComplaintMinutesLeft(C));
   auto Row=SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[BodyText(FString::Printf(TEXT("%s · %s · %.0f min"),*S->HotelRoomName(Room),*UMareSimulation::String(Def,TEXT("label")),Left),12,Left<20?Red:Ink)]
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8,0,0,0)[Button(Cost>0?FString::Printf(TEXT("Mandar técnico · R$ %.0f"),Cost):FString(TEXT("Mandar a equipe")),
     [this,S,Id](){if(S->SolveHotelComplaint(Id,false))UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"));},S->Money()>=Cost)];
   Body->AddSlot().AutoHeight().Padding(0,2)[Row];}
  if(Complaints.Num())Line(TEXT("Nos quartos 301, 302 e 303, resolver pessoalmente (E no quarto) é de graça e dá fama."),11.5f,Faded);
 }
 TArray<FString> Products(){return Sim()?Sim()->KioskMenu():TArray<FString>();}
 /** Restock cards; at a station also the "take it ready" button for what that station keeps. */
 void StockPage(bool bPickup)
 {
  auto S=Sim();auto G=Grid();int32 I=0;const int32 Columns=bPickup?2:4;
  for(const auto& Id:Products()){
   if(bPickup && Station==TEXT("Cupboard") && !S->IsHotDish(Id))continue;
   if(bPickup && Station==TEXT("Fridge") && S->IsHotDish(Id))continue;
   auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);auto Card=TagBody(FString::Printf(TEXT("%d disponíveis"),S->Available(Id)),UMareSimulation::String(Dish,TEXT("name")));
   if(!S->CanSupplyDish(Id))Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("libere em Resort"),16,MareNotebook::Pencil)];
   else{if(bPickup)Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,0,0,4)[Button(TEXT("Pegar pronto"),[S,Id](){S->Pickup(Id);})];
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("+10 · R$ %.0f"),S->RestockCost(Id)),[S,Id](){S->Restock(Id);})];}
   G->AddSlot(I%Columns,I/Columns)[MareNotebook::PriceTag(Card,TiltOf(I))];++I;}
 }
 void StaffPage()
 {
  auto S=Sim();Title(TEXT("Equipe"),TEXT("salários pagos quando você dorme"));auto Roles=UMareSimulation::Object(S->Definitions,TEXT("staff"));auto G=Grid();int32 I=0;
  for(const TCHAR* Role:{TEXT("atendente"),TEXT("recepcionista"),TEXT("camareira"),TEXT("bartender"),TEXT("guia"),TEXT("piscineiro"),TEXT("garcom_hotel")}){auto Def=UMareSimulation::Object(Roles,Role);const FString R=Role;
   bool bHired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(R,bHired);
   auto Card=TagBody(FString::Printf(TEXT("R$ %.0f por dia"),bHired?S->StaffWage(R):UMareSimulation::Number(Def,TEXT("wage"))),UMareSimulation::String(Def,TEXT("name")));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(R==TEXT("atendente")?TEXT("Anota, retira os produtos, entrega e recolhe a louça do quiosque."):UMareSimulation::String(Def,TEXT("blurb")),11,MareNotebook::Faded)];
   const FString Req=UMareSimulation::String(Def,TEXT("req"));bool bOwned=Req.IsEmpty();if(!bOwned)UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Req,bOwned);
   if(bHired){
    Card->AddSlot().AutoHeight()[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[MareNotebook::Stamp(TEXT("CONTRATADO"),MareNotebook::Green)]+SHorizontalBox::Slot().FillWidth(1).HAlign(HAlign_Right)[Link(TEXT("dispensar"),[S,R](){S->DismissStaff(R);})]];
    // Each person of the team: level and fatigue, shift and day off (links cycle them), and what they are doing now.
    const auto Team=S->StaffTeam(R);const auto Rules=UMareSimulation::Object(S->Definitions,TEXT("staff_rules"));
    const bool bShifts=R!=TEXT("atendente");const int32 Day=UMareSimulation::Number(S->State,TEXT("day"),1);
    auto World=Owner.IsValid()?Owner->GetWorld():nullptr;
    for(int32 W=0;W<Team.Num();++W){const auto P=Team[W];
     const double Fatigue=UMareSimulation::Number(P,TEXT("fatigue"));const bool bTired=Fatigue>=UMareSimulation::Number(Rules,TEXT("tired"),60);
     FString Line=FString::Printf(TEXT("%sNível %d · %.0f h hoje"),Team.Num()>1?*FString::Printf(TEXT("%dª pessoa · "),W+1):TEXT(""),int32(UMareSimulation::Number(P,TEXT("level"),1)),UMareSimulation::Number(P,TEXT("hours_today")));
     if(bShifts)Line+=FString::Printf(TEXT(" · cansaço %.0f%%%s"),Fatigue,bTired?TEXT(" (cansado)"):TEXT(""));
     Card->AddSlot().AutoHeight().Padding(0,4,0,0)[MareNotebook::BodyText(Line,11,bTired?MareNotebook::Red:MareNotebook::Ink)];
     if(bShifts)Card->AddSlot().AutoHeight()[SNew(SHorizontalBox)
      +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Link(TEXT("turno: ")+S->ShiftName(UMareSimulation::String(P,TEXT("shift"))).ToLower(),[S,R,W](){S->CycleStaffShift(R,W);})]
      +SHorizontalBox::Slot().AutoWidth()[Link(TEXT("folga: ")+UMareSimulation::WeekdayName(UMareSimulation::Number(P,TEXT("off"),-1)),[S,R,W](){S->CycleStaffDayOff(R,W);})]];
     FString Now;
     if(int32(UMareSimulation::Number(P,TEXT("absent_day"),-1))==Day)Now=TEXT("faltou hoje (exausto)");
     else if(int32(UMareSimulation::Number(P,TEXT("off"),-1))==UMareSimulation::Weekday(Day))Now=TEXT("de folga hoje");
     else if(!S->StaffOnDuty(R))Now=TEXT("fora do turno agora");
     else if(R==TEXT("atendente"))Now=TEXT("atendendo o quiosque");
     else if(R==TEXT("bartender"))Now=S->IsBarOpen()?TEXT("preparando drinks no bar"):TEXT("esperando o bar abrir");
     else if(auto Staff=World?World->GetSubsystem<UMareStaffWorld>():nullptr)Now=Staff->Activity(R).ToLower();
     if(!Now.IsEmpty())Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("agora: ")+Now,15,MareNotebook::Pencil)];}
    {const auto Done=S->StaffDoneToday(R);const TCHAR* Unit=R==TEXT("atendente")?TEXT("entregas"):R==TEXT("bartender")?TEXT("drinks"):R==TEXT("guia")?TEXT("bilhetes vendidos"):
      R==TEXT("garcom_hotel")?TEXT("mesas servidas"):R==TEXT("recepcionista")?TEXT("check-ins"):TEXT("tarefas");
     Card->AddSlot().AutoHeight().Padding(0,2,0,0)[MareNotebook::BodyText(Done.Value>0?FString::Printf(TEXT("Hoje: %d %s · R$ %.0f"),Done.Key,Unit,Done.Value):FString::Printf(TEXT("Hoje: %d %s"),Done.Key,Unit),11,MareNotebook::Green)];}
    if(bShifts && Team.Num()==1)Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,4,0,0)[Link(FString::Printf(TEXT("+ 2ª pessoa no outro turno · R$ %.0f"),UMareSimulation::Number(Def,TEXT("hire"))),[S,R](){S->HireSecondStaff(R);})];
    else if(Team.Num()>1)Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,4,0,0)[Link(TEXT("dispensar a 2ª pessoa"),[S,R](){S->DismissSecondStaff(R);})];}
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
  DebtCard();   // item 10: Dona Dilce's debt, before the ledger
  Heading(TEXT("Últimos lançamentos"));const TArray<TSharedPtr<FJsonValue>>* Ledger=nullptr;
  if(S->State->TryGetArrayField(TEXT("ledger"),Ledger))for(int32 I=Ledger->Num()-1;I>=FMath::Max(0,Ledger->Num()-14);--I){auto Row=(*Ledger)[I]->AsObject();const double Amount=UMareSimulation::Number(Row,TEXT("amount"));
   Body->AddSlot().AutoHeight().Padding(0,1)[SNew(SHorizontalBox)+SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[MareNotebook::BodyText(UMareSimulation::String(Row,TEXT("label")),11.5f)]
    +SHorizontalBox::Slot().AutoWidth().Padding(12,0,0,0)[MareNotebook::HandText(FString::Printf(TEXT("%sR$ %.0f"),Amount<0?TEXT("-"):TEXT("+"),FMath::Abs(Amount)),18,Amount<0?MareNotebook::Red:MareNotebook::Green)]];}
 }
 /** Dona Dilce's debt (MareDebt.cpp): balance, what was paid, a pencil progress line and the payment buttons.
  *  A value is picked first and only charged after "Confirmar" (debt.json phone.confirm shows the cash left). */
 void DebtCard()
 {
  auto S=Sim();bool bCreated=false;UMareSimulation::Object(S->State,TEXT("company"))->TryGetBoolField(TEXT("created"),bCreated);if(!bCreated)return;
  const auto Phone=UMareSimulation::Object(S->DebtDefs(),TEXT("phone"));   // i18n:skip
  auto R=[](int64 C){return FString::Printf(TEXT("%.0f"),C/100.0);};
  const int64 Principal=S->DebtPrincipalCents(),Paid=S->DebtPaidCents(),Left=S->DebtBalanceCents(),Max=S->DebtMaxPayCents();
  Heading(UMareSimulation::String(Phone,TEXT("title")));   // i18n:skip
  auto Card=SNew(SVerticalBox);
  if(Left<=0)Card->AddSlot().AutoHeight()[MareNotebook::Stamp(UMareSimulation::String(Phone,TEXT("settled")),MareNotebook::Green)];   // i18n:skip
  else Card->AddSlot().AutoHeight()[MareNotebook::HandText(UMareSimulation::String(Phone,TEXT("balance")).Replace(TEXT("{0}"),*R(Left)),24,MareNotebook::Brown)];   // i18n:skip
  Card->AddSlot().AutoHeight().Padding(0,2)[MareNotebook::BodyText(UMareSimulation::String(Phone,TEXT("paid")).Replace(TEXT("{0}"),*R(Paid)).Replace(TEXT("{1}"),*R(Principal)),11.5f,MareNotebook::Ink)];   // i18n:skip
  {const float F=Principal>0?float(double(Paid)/double(Principal)):0.f;   // pencil progress line (0..100 %)
   Card->AddSlot().AutoHeight().Padding(0,4).HAlign(HAlign_Left)[SNew(SBox).WidthOverride(360).HeightOverride(10)[SNew(SOverlay)
    +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Faded.CopyWithNewOpacity(.25f))]
    +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).WidthOverride(FMath::Max(2.f,360.f*F))[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Green)]]]];}
  if(Left>0 && S->IsDemo())Card->AddSlot().AutoHeight().Padding(0,2)[MareNotebook::BodyText(UMareSimulation::String(Phone,TEXT("demo_limit")).Replace(TEXT("{0}"),*R(S->DebtLimitCents())),10.5f,MareNotebook::Faded)];   // i18n:skip
  if(Left>0 && !S->IsDebtDemoCapped()){
   if(DebtPick>0 && DebtPick<=Max){
    Card->AddSlot().AutoHeight().Padding(0,6,0,2)[MareNotebook::HandText(UMareSimulation::String(Phone,TEXT("confirm")).Replace(TEXT("{0}"),*R(DebtPick)).Replace(TEXT("{1}"),*R(int64(FMath::RoundToDouble(S->Money()*100))-DebtPick)),17,MareNotebook::Ink)];   // i18n:skip
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("Confirmar"),[this,S](){const int64 V=DebtPick;DebtPick=0;S->PayDebt(V);})]
     +SHorizontalBox::Slot().AutoWidth().Padding(12,0,0,0).VAlign(VAlign_Center)[Link(TEXT("cancelar"),[this](){DebtPick=0;})]];}
   else{
    DebtPick=0;
    Card->AddSlot().AutoHeight().Padding(0,6,0,2)[MareNotebook::BodyText(UMareSimulation::String(Phone,TEXT("pay")),11.5f,MareNotebook::Faded)];   // i18n:skip
    auto Row=SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8,4));
    for(const int64 Amount:{int64(100000),int64(1000000),int64(5000000)})
     Row->AddSlot()[Button(TEXT("R$ ")+R(Amount),[this,Amount](){DebtPick=Amount;},Amount<=Max)];
    Row->AddSlot()[Button(TEXT("o máximo que der · R$ ")+R(Max),[this,Max](){DebtPick=Max;},Max>0)];
    Card->AddSlot().AutoHeight()[Row];
    // 07/11 (debt contract: "o botão abre valor livre"): any amount in reais, capped by what can be paid now.
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6,0,0)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[MareNotebook::BodyText(TEXT("outro valor: R$"),11.5f,MareNotebook::Faded)]
     +SHorizontalBox::Slot().AutoWidth().Padding(6,0)[SNew(SBox).WidthOverride(120)[SAssignNew(DebtAmount,SEditableTextBox).Font(MareNotebook::Hand(18)).HintText(MareLoc::Text(TEXT("ex.: 2500")))]]
     +SHorizontalBox::Slot().AutoWidth()[Button(TEXT("pagar este valor"),[this,Max](){const FString V=DebtAmount.IsValid()?DebtAmount->GetText().ToString().Replace(TEXT("."),TEXT("")).Replace(TEXT(","),TEXT(".")):FString();
      const int64 C=(int64)FMath::RoundToDouble(FCString::Atod(*V)*100.0);if(C>0)DebtPick=FMath::Min(C,Max);},Max>0)]];}}
  Body->AddSlot().AutoHeight().Padding(0,4)[MareNotebook::PriceTag(Card,TiltOf(3))];
 }
 void ResortPage()
 {
  auto S=Sim();bool bHotel=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
  TArray<FString> Today;for(const TCHAR* Id:{TEXT("bar"),TEXT("pool"),TEXT("passeios")})if(S->IsPlaceAvailable(Id))Today.Add(FString::Printf(TEXT("%s R$ %.0f"),*UMareSimulation::String(S->PlaceDef(Id),TEXT("name")),S->OpsToday(Id)));
  Title(TEXT("Resort"),Today.Num()?TEXT("hoje: ")+FString::Join(Today,TEXT(" · ")):FString(TEXT("compre expansões para o resort crescer")));
  if(bHotel){auto Last=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("hotel"));
   Pencil(FString::Printf(TEXT("Grand Hotel 5 estrelas · ocupação prevista %.0f%% · nota %.1f · fama %s"),S->HotelOccupancy()*100,S->Stars(),*S->FameName())+(Last->HasField(TEXT("rooms"))?FString::Printf(TEXT(" · última noite %.0f suítes, R$ %.0f"),UMareSimulation::Number(Last,TEXT("rooms")),UMareSimulation::Number(Last,TEXT("rev"))):FString()));}
  if(bHotel && S->HotelComplaints().Num())HotelBoard(false);   // 5.1: guests' complaints reach the phone anywhere
  if(bHotel && (UMareSimulation::Object(S->State,TEXT("hotel_events"))->HasField(TEXT("offer")) || S->BookedHotelEvent()))HotelEventBoard();   // 5.2: event offers and set-up anywhere
  auto Pousada=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("pousada"));
  if(S->PousadaRooms()>0 && Pousada->HasField(TEXT("rooms")))Pencil(FString::Printf(TEXT("Pousada, última noite: %.0f de %.0f quartos · R$ %.0f"),UMareSimulation::Number(Pousada,TEXT("occupied")),UMareSimulation::Number(Pousada,TEXT("rooms")),UMareSimulation::Number(Pousada,TEXT("rev"))));
  {const FString Next=S->NextUnlockText();if(!Next.IsEmpty())Pencil(Next);}   // 6.2: the next unlock and what it still needs
  Heading(TEXT("Expansões"),TEXT("(cada uma libera uma área nova)"));auto G=Grid();int32 I=0;auto Expansions=UMareSimulation::Object(S->Definitions,TEXT("expansions"));
  TArray<FString> Order;const TArray<TSharedPtr<FJsonValue>>* Listed=nullptr;if(S->Definitions->TryGetArrayField(TEXT("expansion_order"),Listed))for(const auto& V:*Listed)Order.Add(V->AsString());
  for(const auto& Pair:Expansions->Values)Order.AddUnique(FString(Pair.Key.ToView()));
  for(const FString& Id:Order){auto Row=UMareSimulation::Object(Expansions,Id);if(!Expansions->HasField(Id))continue;bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);
   auto Card=TagBody(FString::Printf(TEXT("R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),UMareSimulation::String(Row,TEXT("name")));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareSimulation::String(Row,TEXT("blurb")),10.5f,MareNotebook::Faded)];
   TArray<FString> Missing;const TArray<TSharedPtr<FJsonValue>>* Req=nullptr;if(Row->TryGetArrayField(TEXT("req"),Req))for(const auto& V:*Req){bool bHas=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(V->AsString(),bHas);if(!bHas)Missing.Add(UMareSimulation::String(UMareSimulation::Object(Expansions,V->AsString()),TEXT("name")));}
   {const FString Chapter=UMareSimulation::String(Row,TEXT("chapter"));if(!Chapter.IsEmpty() && !S->IsChapterDone(Chapter))Missing.Add(TEXT("história \"")+UMareSimulation::String(S->ChapterDefinition(Chapter),TEXT("title"))+TEXT("\""));
    const int32 Fame=UMareSimulation::Number(Row,TEXT("fame"));if(Fame>0 && S->FameLevel()<Fame)Missing.Add(FString::Printf(TEXT("fama nível %d"),Fame));}
   if(bOwned)Card->AddSlot().AutoHeight()[MareNotebook::Stamp(TEXT("COMPRADA"),MareNotebook::Green)];
   else if(S->IsFullGameOnly(Id))Card->AddSlot().AutoHeight()[MareNotebook::Stamp(TEXT("JOGO COMPLETO"),MareNotebook::Pencil)];   // Demo (06/11)
   else if(Missing.Num())Card->AddSlot().AutoHeight()[MareNotebook::HandText(TEXT("antes: ")+FString::Join(Missing,TEXT(", ")),15,MareNotebook::Pencil)];
   else Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Comprar · R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),[S,Id](){S->BuyExpansion(Id);})];
   G->AddSlot(I%3,I/3)[MareNotebook::PriceTag(Card,TiltOf(I))];++I;}
  Heading(TEXT("Negócios da vila"),FString::Printf(TEXT("(atender você mesmo rende 100%% e fama; o funcionário atende sozinho com %.0f%%)"),S->BizClerkShare()*100));auto B=Grid();I=0;
  for(const auto& Pair:UMareSimulation::Object(S->Definitions,TEXT("businesses"))->Values){const FString Id(Pair.Key.ToView());auto Def=Pair.Value->AsObject();
   const int32 Level=S->BusinessLevel(Id);const auto LevelDef=S->BizLevelDef(Id,Level);
   auto Card=TagBody(Level>0?FString::Printf(TEXT("nível %d/3 · funcionário R$ %.0f/dia"),Level,UMareSimulation::Number(Def,TEXT("wage")))
    :FString::Printf(TEXT("funcionário R$ %.0f/dia"),UMareSimulation::Number(Def,TEXT("wage"))),UMareSimulation::String(Def,TEXT("name"))+(LevelDef.IsValid()?TEXT(" · ")+UMareSimulation::String(LevelDef,TEXT("name")):FString()));
   Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareSimulation::String(Def,TEXT("blurb")),10.5f,MareNotebook::Faded)];FString Reason;
   if(S->OwnsBusiness(Id)){
    // 3.6: daily report, the next level and the clerk.
    Card->AddSlot().AutoHeight()[SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[MareNotebook::Stamp(TEXT("SEU"),MareNotebook::Green)]
     +SHorizontalBox::Slot().FillWidth(1)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(STextBlock).Text(MareLoc::Text(FString::Printf(TEXT("hoje R$ %.0f"),S->OpsToday(TEXT("biz_")+Id)))).Font(MareNotebook::Hand(16)).ColorAndOpacity(MareNotebook::Green)]];
    Card->AddSlot().AutoHeight().Padding(0,4,0,0)[MareNotebook::BodyText(S->BizReportLine(Id,false),10.f,MareNotebook::Ink)];
    Card->AddSlot().AutoHeight().Padding(0,2,0,4)[MareNotebook::BodyText(S->BizReportLine(Id,true),10.f,MareNotebook::Faded)];
    double Cost=0;const auto Next=S->BizLevelDef(Id,Level+1);
    if(Next.IsValid()){
     // 06/11: the level name in the button was cut ("R$ 1..."): the button only says level and price, the name leads the blurb.
     // The level's blurb (what gets harder) is the tooltip: in the card it made the row taller than the phone page.
     {auto Line=MareNotebook::BodyText(FString::Printf(TEXT("Próximo: nível %d, %s"),Level+1,*UMareSimulation::String(Next,TEXT("name"))),10.f,MareNotebook::Faded);
      Line->SetToolTipText(MareLoc::Text(UMareSimulation::String(Next,TEXT("blurb"))));Card->AddSlot().AutoHeight().Padding(0,2,0,0)[Line];}
     if(S->CanUpgradeBusiness(Id,Reason,&Cost))Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,2)[Button(FString::Printf(TEXT("Melhorar · R$ %.0f"),Cost),[S,Id](){S->UpgradeBusiness(Id);})];
     else Card->AddSlot().AutoHeight()[MareNotebook::HandText(Reason,14,MareNotebook::Pencil)];}
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,4,0,0)[S->HasBizClerk(Id)?Link(TEXT("dispensar o funcionário"),[S,Id](){S->SetBizClerk(Id,false);})
     :Button(FString::Printf(TEXT("Contratar funcionário · R$ %.0f/dia"),UMareSimulation::Number(Def,TEXT("wage"))),[S,Id](){S->SetBizClerk(Id,true);})];}
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
   for(int32 I=0;I<Rows->Num();++I){if(!bSide && (I!=Stage || S->IsCampaignAtFullGame()))continue;auto Q=(*Rows)[I]->AsObject();const FString Id=UMareSimulation::String(Q,TEXT("id"));
    const TArray<TSharedPtr<FJsonValue>>* Done=nullptr;if(bSide && Campaign->TryGetArrayField(TEXT("side_done"),Done) && Done->ContainsByPredicate([&](const auto& V){return V->AsString()==Id;}))continue;
    const int32 Have=S->MissionAmount(Q),Need=UMareSimulation::Number(Q,TEXT("qty"),1);
    auto Card=TagBody(FString::Printf(TEXT("%d de %d"),FMath::Min(Have,Need),Need),UMareSimulation::String(Q,TEXT("title")));
    Card->AddSlot().AutoHeight().Padding(0,0,0,6)[MareNotebook::BodyText(UMareSimulation::String(Q,TEXT("task")),11,MareNotebook::Faded)];
    Card->AddSlot().AutoHeight().HAlign(HAlign_Left)[Button(FString::Printf(TEXT("Concluir · R$ %.0f"),UMareSimulation::Number(Q,TEXT("reward"))),[S,Id,bSide](){S->ClaimMission(Id,bSide);},Have>=Need)];
    G->AddSlot(Shown%3,Shown/3)[MareNotebook::PriceTag(Card,TiltOf(Shown))];++Shown;}
   if(!Shown)Pencil(bSide?TEXT("Nenhum pedido aberto agora."):S->IsCampaignAtFullGame()?TEXT("Fim da demo: a história continua no jogo completo, com o Grand Hotel."):TEXT("Campanha concluída!"));
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
    List->AddSlot().AutoHeight()[SNew(SMarePadButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(0)).OnClicked_Lambda([this,Id](){Place=Id;Rebuild();return FReply::Handled();})
     [SNew(SBorder).BorderImage(bOn?static_cast<const FSlateBrush*>(&MareNotebook::MarkerBrush()):FCoreStyle::Get().GetBrush("NoBrush")).Padding(FMargin(5,0))[MareNotebook::HandText((bOn?TEXT("» "):TEXT(""))+Name,17,bOpen?MareNotebook::Ink:MareNotebook::Pencil)]]];}}
  return SNew(SMareFit).Name(TEXT("place index")).Rows(List)[List];
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
  const int32 PrevFocus=MareGamepad::FocusedIndex(AsShared());   // the same control keeps the gamepad focus after the rebuild
  const TArray<FString> Titles=TabTitles();if(!Titles.IsValidIndex(Tab))Tab=0;
  const bool bPhone=Station.IsNone();const bool bIndex=bPhone && Tab==6;
  SAssignNew(Body,SVerticalBox);
  // Status line in pencil: day, clock, weather and cash.
  // 07/11 (Sergio's photo: "Entregue ou devolva o pro..." cut at the station): the message gets its own wrapped line
  // under day and cash instead of an ellipsis between them.
  auto Status=SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Font(MareNotebook::Hand(16)).ColorAndOpacity(Faded).Text_Lambda([S](){const int32 M=UMareSimulation::Number(S->State,TEXT("minutes"));
     return MareLoc::Text(FString::Printf(TEXT("Dia %.0f · %02d:%02d · %s"),UMareSimulation::Number(S->State,TEXT("day"),1),M/60,M%60,UMareSimulation::String(S->State,TEXT("weather"))==TEXT("rain")?TEXT("Chuva"):TEXT("Sol")));})]
    +SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Font(MareNotebook::Hand(16)).ColorAndOpacity(Faded).Text_Lambda([S](){return MareLoc::Text(FString::Printf(TEXT("Caixa: R$ %.0f"),S->Money()));})]]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left).Padding(0,2,0,0)[SNew(SBox).Visibility(S->LastMessage.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible)[SNew(SBorder).BorderImage(&MarkerBrush()).Padding(FMargin(6,0))
    [SNew(STextBlock).Text(MareLoc::Text(S->LastMessage)).Font(MareNotebook::Hand(15)).ColorAndOpacity(Ink).AutoWrapText(true)]]];
  // Divider tabs: pastel paper, the open one is the white page itself; "fechar" sits at the end.
  auto Tabs=SNew(SHorizontalBox);
  if(bPhone)for(int32 I=0;I<Titles.Num();++I){const bool bOn=I==Tab;
   Tabs->AddSlot().AutoWidth().VAlign(VAlign_Bottom).Padding(0,0,3,0)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(0)).OnClicked_Lambda([this,I](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.3f);Tab=I;Rebuild();return FReply::Handled();})
    [SNew(SBorder).BorderImage(&TabBrush(bOn?Paper:TabColor(I))).Padding(bOn?FMargin(11,4,11,3):FMargin(8,2,8,2))[SNew(STextBlock).Text(MareLoc::Text(Titles[I])).Font(MareNotebook::Hand(bOn?17:15)).ColorAndOpacity(Ink)]]];}
  else Tabs->AddSlot().AutoWidth().VAlign(VAlign_Bottom)[SNew(SBorder).BorderImage(&TabBrush(Paper)).Padding(FMargin(16,6,16,5))[SNew(STextBlock).Text(MareLoc::Text(Station==TEXT("Fridge")?TEXT("Geladeira"):Station==TEXT("Reception") || Station==TEXT("ReceptionHotel")?TEXT("Recepção"):Station==TEXT("Bar")?TEXT("Bar"):Station==TEXT("PoolTable")?TEXT("Sinuca"):Station==TEXT("TableTennis")?TEXT("Tênis de mesa"):Station==TEXT("Tours")?TEXT("Píer"):Station==TEXT("Restaurant")?TEXT("Cozinha"):TEXT("Porções prontas"))).Font(MareNotebook::Hand(19)).ColorAndOpacity(Ink)]];
  Tabs->AddSlot().FillWidth(1)[SNullWidget::NullWidget];
  Tabs->AddSlot().AutoWidth().VAlign(VAlign_Bottom)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::Plain()).ContentPadding(FMargin(0)).OnClicked_Lambda([this](){if(Owner.IsValid())Owner->ClosePhone();return FReply::Handled();})
   [SNew(SBorder).BorderImage(&TabBrush(Hex(226,150,140))).Padding(FMargin(8,2,8,2))[SNew(STextBlock).Text(MareLoc::Text(TEXT("fechar"))).Font(MareNotebook::Hand(15)).ColorAndOpacity(Ink)]]];
  // The page: lined paper behind, place index on the left of Personalizar, scrolling content, a sticky note for messages.
  auto Page=SNew(SHorizontalBox);
  if(bIndex)Page->AddSlot().AutoWidth()[SNew(SBox).WidthOverride(150).Padding(FMargin(14,8,8,6))[PlaceIndex()]];
  Page->AddSlot().FillWidth(1).Padding(bIndex?FMargin(12,8,16,0):FMargin(24,8,18,0))[SNew(SMareFit).Name(Station.IsNone()?FString::Printf(TEXT("phone tab %d"),Tab):Station.ToString()).Rows(Body)[SNew(SBox).Padding(FMargin(0,0,0,10))[Body.ToSharedRef()]]];
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
  if(PrevFocus>=0)MareGamepad::FocusSoon(AsShared(),PrevFocus);
  if(Station==TEXT("Bar")){BarPage();return;}
  if(Station==TEXT("Tours")){ToursPage();return;}
  if(Station==TEXT("PoolTable")){PoolPage();return;}
  if(Station==TEXT("TableTennis")){TableTennisPage();return;}
  if(Station==TEXT("Restaurant")){RestaurantPage();return;}
  if(Station==TEXT("Reception") || Station==TEXT("ReceptionHotel")){ReceptionPage(Station==TEXT("ReceptionHotel")?TEXT("hotel"):TEXT("pousada"));return;}
  if(!bPhone){StockPage(true);if(!S->Carry().IsEmpty())Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,6)[Button(TEXT("Devolver produto"),[S](){S->ReturnCarry();})];return;}
  switch(Tab){
   case 0:KioskPage();break;
   case 1:Title(TEXT("Compras"),TEXT("reposição imediata · o produto chega pronto"));StockPage(false);break;
   case 2:StaffPage();break;
   case 3:FinancePage();break;
   case 4:ResortPage();break;
   case 5:MissionsPage();break;
   case 6:CustomizePage();break;
   default:if(Titles[Tab]==TEXT("Passeios"))TourResultsPage();else DrinksPage();
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
 // Under water the eye must not adapt up to the dark of the deep (it washed the -100 m floor back to daylight).
 Eyes->PostProcessSettings.bOverride_AutoExposureMinBrightness=Eyes->PostProcessSettings.bOverride_AutoExposureMaxBrightness=true;
 Eyes->PostProcessSettings.AutoExposureMinBrightness=4.f;Eyes->PostProcessSettings.AutoExposureMaxBrightness=10.f;
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
 Input->BindAxis(TEXT("LookPadX"),this,&AMareCharacter::LookPadX);Input->BindAxis(TEXT("LookPadY"),this,&AMareCharacter::LookPadY);
 Input->BindAction(TEXT("SprintToggle"),IE_Pressed,this,&AMareCharacter::SprintToggle);
}
void AMareCharacter::Forward(float Value){if(FMath::Abs(Value)>.1f)if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())Home->Stand();if(Controller){auto Rotation=Controller->GetControlRotation();if(!GetCharacterMovement()->IsSwimming())Rotation.Pitch=0;Rotation.Roll=0;AddMovementInput(Rotation.Vector(),Value);}}
void AMareCharacter::Right(float Value){if(FMath::Abs(Value)>.1f)if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())Home->Stand();if(Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),Value);}
void AMareCharacter::LookX(float Value){AddControllerYawInput(Value*FMareOptions::Get().MouseSensitivity);}
void AMareCharacter::LookY(float Value){const auto& Options=FMareOptions::Get();AddControllerPitchInput(Value*Options.MouseSensitivity*(Options.bInvertY?-1.f:1.f));}
// The stick value is already past the DeadZone of DefaultInput.ini: only the curve is applied here.
void AMareCharacter::LookPadX(float Value){if(Value!=0.f)AddControllerYawInput(MareGamepad::Curve(Value,0.f)*MareGamepad::LookUnitsPerSecond*FMareOptions::Get().GamepadSensitivity*GetWorld()->GetDeltaSeconds());}
void AMareCharacter::LookPadY(float Value)
{
 const auto& Options=FMareOptions::Get();
 if(Value!=0.f)AddControllerPitchInput(MareGamepad::Curve(Value,0.f)*MareGamepad::LookUnitsPerSecond*.8f*Options.GamepadSensitivity*(Options.bInvertY?-1.f:1.f)*GetWorld()->GetDeltaSeconds());
}
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
// 06/11 (CHECKLIST 0, red "Cached lighting in Lumen ... clipped" on the -100 m floor): the engine folds the luminance of
// SceneColorTint into the pre-exposure (PostProcessEyeAdaptation.cpp), so the old deep tint (luminance 0.013) pushed the
// exposure to EV ~15, past the safe range [-8, 12] of r.EyeAdaptation.CachedLightingPreExposure 4: Lumen's cached light was
// clipped. The tint now carries only the hue, at the surface luminance; the darkness is the ColorGain of the grading LUT,
// applied after the exposure. Test MareAlta.Visual.UnderwaterGrade.
void MareUnderwaterGrade(float EyeZ,FLinearColor& Tint,float& Gain)
{
 const float Blue=FMath::SmoothStep(300.f,2500.f,-EyeZ),Black=FMath::SmoothStep(2500.f,9000.f,-EyeZ);
 const FLinearColor Surface(.72f,.86f,.83f);
 const FLinearColor Hue=FMath::Lerp(FMath::Lerp(Surface,FLinearColor(.16f,.3f,.48f),Blue),FLinearColor(.006f,.014f,.03f),Black);
 Gain=FMath::Max(Hue.GetLuminance(),1e-4f)/Surface.GetLuminance();Tint=Hue*(1.f/Gain);
}
void AMareCharacter::SwimVertical(float Value){VerticalSwimInput=FMath::Clamp(Value,-1.f,1.f);}
void AMareCharacter::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto Movement=GetCharacterMovement();auto PC=Cast<APlayerController>(Controller);
 const bool bSwimming=Movement->IsSwimming();const float Vertical=PC && PC->IsMoveInputIgnored()?0.f:VerticalSwimInput;
 // A comfortable home leaves the player rested: walking and running get faster.
 const UMareSimulation* HomeSim=GetGameInstance()?GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;
 if(bSprintToggle && Movement->GetCurrentAcceleration().IsNearlyZero())bSprintToggle=false;   // L3 runs until the player stops
 Movement->MaxWalkSpeed=(bSprint || bSprintToggle?420:260)*(HomeSim?float(HomeSim->HomeSpeedFactor()):1.f);// 05/11 (Sergio: "o herói flutua na água (boia)": released 5 m down he shot up at 2.25 m/s): near the surface he
 // rests on it; under water he is close to neutral and drifts up slowly (~20 cm/s); Space swims up faster.
 Movement->Buoyancy=Vertical<0?1.f:Vertical>0 || GetActorLocation().Z>-110?1.35f:1.03f;
 if(bSwimming && (Vertical<=0 || GetActorLocation().Z<-78))AddMovementInput(FVector::UpVector,Vertical);
 const bool bUnderwater=bSwimming && Eyes->GetComponentLocation().Z<-38;
 Eyes->PostProcessBlendWeight=FMath::FInterpTo(Eyes->PostProcessBlendWeight,bUnderwater?1.f:0.f,DeltaSeconds,5);
 // 05/11 (Sergio: "conforme vai afundando vai ficando escuro, como no oceano de verdade, sem luz"): the sunlight dies
 // with depth: green-blue near the surface, deep blue by ~25 m, almost black on the -100 m floor.
 {FLinearColor Tint;float Gain=1.f;MareUnderwaterGrade(float(Eyes->GetComponentLocation().Z),Tint,Gain);
  Eyes->PostProcessSettings.SceneColorTint=Tint;Eyes->PostProcessSettings.bOverride_ColorGain=true;Eyes->PostProcessSettings.ColorGain=FVector4(1,1,1,Gain);}
 if(Movement->IsMovingOnGround() && !bSwimming && GetActorLocation().Z>-100)SafeLandLocation=GetActorLocation();
 // The sand planes offshore have no collision: the swimmer stops on the sea floor profile (reef.json floor_fill).
 if(bSwimming && GetActorLocation().Y<-5450){const float Floor=UMareReefWorld::SeabedZ(GetActorLocation().Y)+GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+15.f;
  if(GetActorLocation().Z<Floor){SetActorLocation(FVector(GetActorLocation().X,GetActorLocation().Y,Floor));if(Movement->Velocity.Z<0)Movement->Velocity.Z=0;}}
 // Fell through the world: back to the last safe ground. 07/11 (QA void_recovery): with the -100 m sea floor the old
 // -120 m line left someone who slipped under the beach falling for a long time; now anyone falling (not swimming) more
 // than 6 m below the ground profile under them (the beach/land is at about 0, the sea floor at SeabedZ) is brought back.
 {const float Ground=GetActorLocation().Y<-5450?UMareReefWorld::SeabedZ(GetActorLocation().Y):-100.f;
  if(GetActorLocation().Z<-12000 || (Movement->IsFalling() && !bSwimming && GetActorLocation().Z<Ground-600.f)){
   SetActorLocation(SafeLandLocation);Movement->StopMovementImmediately();VerticalSwimInput=0;}}
}

#define LOCTEXT_NAMESPACE "MareMenu"
/** Main menu: new game, continue, three load slots, options, credits, quit. */
/** Business counter task (port of the Godot minigame): three rounds of "stop the cursor in the green band",
 *  the band shrinks and the cursor speeds up each round. E, Space, Enter, click or A; Esc or B gives up. */
class SMareTimingGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareTimingGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_ARGUMENT(FString,Biz) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;Biz=Args._Biz;NewRound();
  auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;const auto Def=S?UMareSimulation::Object(UMareSimulation::Object(S->BusinessGames(),TEXT("businesses")),Biz):MakeShared<FJsonObject>();
  const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(Def->TryGetArrayField(TEXT("steps"),List))for(const auto& V:*List)Steps.Add(V->AsString());
  const FString Title=UMareSimulation::String(Def,TEXT("title"));
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,70)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,16))
   [SNew(SBox).WidthOverride(BarWidth+52)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[HandText(Title,30,Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4)[SNew(STextBlock).Font(Hand(22)).ColorAndOpacity(Ink).Text_Lambda([this](){
     return MareLoc::Text(Done>=0?Result:Steps.IsValidIndex(Round)?Steps[Round]:FString());})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SBox).WidthOverride(BarWidth).HeightOverride(46)[SNew(SOverlay)
     +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Kraft)]
     +SOverlay::Slot()[SNew(SBox).HAlign(HAlign_Left).Padding_Lambda([this](){return FMargin((Zone-ZoneW/2)*BarWidth,0,0,0);})
      [SNew(SBox).WidthOverride_Lambda([this](){return FOptionalSize(ZoneW*BarWidth);})[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Green)]]]
     +SOverlay::Slot()[SNew(SBox).HAlign(HAlign_Left).Padding_Lambda([this](){return FMargin(FMath::Max(0.f,Cursor()*BarWidth-4),0,0,0);})
      [SNew(SBox).WidthOverride(8)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Ink)]]]]]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(24)).ColorAndOpacity(Green).Text_Lambda([this](){
     FString Dots;for(int32 I=0;I<3;++I)Dots+=I<Marks.Num()?(Marks[I]?TEXT("O "):TEXT("X ")):TEXT("- ");return MareLoc::Text(Dots);})]
    +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("E, Espaço, clique ou A quando o cursor estiver no verde · Esc ou B desiste"),15,Faded)]]]];
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Finish(true);return FReply::Handled();}
  if(K==EKeys::E || K==EKeys::SpaceBar || K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom || K==EKeys::Gamepad_FaceButton_Left){Press();return FReply::Handled();}
  return FReply::Unhandled();
 }
 virtual FReply OnMouseButtonDown(const FGeometry&,const FPointerEvent&) override{Press();return FReply::Handled();}
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);
  if(Done>=0){if((Done-=Delta)<=0)Close();return;}
  if(Pause>0){if((Pause-=Delta)<=0)NewRound();return;}
  T+=Delta*Speed;
 }
private:
 static constexpr float BarWidth=560;
 TWeakObjectPtr<AMareController> Owner;FString Biz,Result;TArray<FString> Steps;TArray<bool> Marks;
 int32 Round=0;float T=0,Speed=.8f,Zone=.5f,ZoneW=.22f,Pause=0,Done=-1;
 float Cursor()const{return .5f-.5f*FMath::Cos(T*PI);}
 void NewRound(){Zone=FMath::FRandRange(.22f,.78f);ZoneW=.22f*FMath::Pow(.75f,float(Round));Speed=.8f+.3f*Round;T=FMath::FRand()*2;}
 void Press()
 {
  if(Done>=0 || Pause>0 || Round>2)return;
  const bool bHit=FMath::Abs(Cursor()-Zone)<=ZoneW/2;Marks.Add(bHit);
  if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),bHit?TEXT("deal_accept"):TEXT("deal_decline"));
  if(++Round>2){Finish(false);return;}Pause=.6f;
 }
 void Finish(bool bGaveUp)
 {
  auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;int32 Hits=0;for(bool B:Marks)Hits+=B;
  if(bGaveUp && Marks.Num()<3){Result=TEXT("Você saiu do balcão. O cliente espera.");Done=1.f;return;}
  if(S){S->PlayBusiness(Biz,Hits);Result=S->LastMessage;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("money_coins"));}
  Done=1.8f;
 }
 void Close(){if(Owner.IsValid())Owner->CloseBusinessGame();}
};
/** Ice cream shop (CHECKLIST_EXPANSOES 3.1, MareIceCream.cpp): the order shows for 3 s, then the cone is built from
 *  memory. Hold a tub (click, keys 1-6, or A on the selected tub) and the scoop grows; release in the green for the
 *  right size. Then the topping and "Entregar". One customer after another while the queue lasts. */
class SMareIceCreamGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareIceCreamGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;auto S=Sim();if(!S)return;const auto D=S->IceDefs();
  const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
  if(D->TryGetArrayField(TEXT("flavors"),L))for(const auto& V:*L)Flavors.Add({UMareSimulation::String(V->AsObject(),TEXT("id")),UMareSimulation::String(V->AsObject(),TEXT("name")),Color(V->AsObject())});
  if(D->TryGetArrayField(TEXT("toppings"),L))for(const auto& V:*L)Toppings.Add({UMareSimulation::String(V->AsObject(),TEXT("id")),UMareSimulation::String(V->AsObject(),TEXT("name")),Color(V->AsObject())});
  const TArray<TSharedPtr<FJsonValue>>* R=nullptr;if(D->TryGetArrayField(TEXT("right"),R) && R->Num()==2){RightLo=(*R)[0]->AsNumber();RightHi=(*R)[1]->AsNumber();}
  GrowTime=UMareSimulation::Number(D,TEXT("grow_seconds"),1.6);ShowTime=UMareSimulation::Number(D,TEXT("show_seconds"),3);
  // Level 2-3 cones take up to 4 scoops (businesses.sorveteria.levels, 3.6).
  {const TArray<TSharedPtr<FJsonValue>>* Sc=nullptr;if(D->TryGetArrayField(TEXT("scoops"),Sc) && Sc->Num()==2)MaxScoops=FMath::Clamp(int32((*Sc)[1]->AsNumber()),1,4);}
  auto Tubs=SNew(SHorizontalBox);
  for(int32 I=0;I<Flavors.Num();++I)Tubs->AddSlot().AutoWidth().Padding(4,0)[SNew(SButton).ButtonStyle(&Plain()).ContentPadding(0)
   .OnPressed_Lambda([this,I](){Begin(I);}).OnReleased_Lambda([this](){Commit();})
   [SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SBox).WidthOverride(96).HeightOverride(54)[SNew(SBorder).BorderImage(&Tub()).BorderBackgroundColor_Lambda([this,I](){
      return FSlateColor(Selected==I?Flavors[I].Color:Flavors[I].Color*.92f);}).Padding(0)[SNew(SBorder).BorderImage(&Rim()).BorderBackgroundColor(FLinearColor(1,1,1,0))
      .Visibility_Lambda([this,I](){return Selected==I?EVisibility::HitTestInvisible:EVisibility::Collapsed;})]]]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[BodyText(FString::Printf(TEXT("%d · %s"),I+1,*Flavors[I].Name),12,Ink)]]];
  auto Tops=SNew(SHorizontalBox);
  for(int32 I=0;I<Toppings.Num();++I)Tops->AddSlot().AutoWidth().Padding(3,0)[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(8,3))
   .OnClicked_Lambda([this,I](){if(Phase==EPhase::Build){Topping=I;Status=TEXT("Cobertura: ")+Toppings[I].Name+TEXT(". Aperte Entregar.");}return FReply::Handled();})
   [SNew(STextBlock).Font(Body(12,true)).ColorAndOpacity_Lambda([this,I](){return FSlateColor(Topping==I?Red:Ink);}).Text(MareLoc::Text(Toppings[I].Name))]];
  // The cone: three scoop places over a waffle cone drawn as narrowing strips.
  auto Cone=SNew(SVerticalBox);
  for(int32 K=MaxScoops-1;K>=0;--K)Cone->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0,-14,0,0)[SNew(SBox).WidthOverride_Lambda([this,K](){return FOptionalSize(ScoopPx(K));})
   .HeightOverride_Lambda([this,K](){return FOptionalSize(ScoopPx(K)*.82f);})[SNew(SBorder).BorderImage(&Ball()).BorderBackgroundColor_Lambda([this,K](){return FSlateColor(ScoopColor(K));})
    .Visibility_Lambda([this,K](){return ScoopPx(K)>1?EVisibility::Visible:EVisibility::Hidden;}).Padding(0).VAlign(VAlign_Top)
    // The topping drips over the top scoop.
    [SNew(SBox).HeightOverride_Lambda([this,K](){return FOptionalSize(ScoopPx(K)*.38f);})[SNew(SBorder).BorderImage(&Ball()).Padding(0).BorderBackgroundColor_Lambda([this,K](){
      return FSlateColor(K==TopScoop() && Topping>=0 && Toppings[Topping].Id!=TEXT("nenhuma")?Toppings[Topping].Color:FLinearColor(1,1,1,0));})]]]];
  for(int32 J=0;J<6;++J)Cone->AddSlot().AutoHeight().HAlign(HAlign_Center)[SNew(SBox).WidthOverride(70-J*11).HeightOverride(14)
   [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(J%2?Hex(196,140,74):Hex(214,160,90))]];
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,50)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,14))
   [SNew(SBox).WidthOverride(780)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().FillWidth(1)[HandText(TEXT("Gelato da Maré · montar a casquinha"),28,Brown)]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Faded).Text_Lambda([this](){
      auto S=Sim();return MareLoc::Text(S?FString::Printf(TEXT("na fila: %d"),S->IceQueue().Num()):FString());})]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,2)[SNew(STextBlock).Font(Hand(22)).ColorAndOpacity_Lambda([this](){return FSlateColor(Phase==EPhase::Show?Red:Ink);})
     .AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(Status);})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,6)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().Padding(0,0,24,0)[SNew(SBox).WidthOverride(150).HeightOverride(200).VAlign(VAlign_Bottom)[Cone]]
     +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[SNew(SVerticalBox)
      +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Freezer"),18,Faded)]
      +SVerticalBox::Slot().AutoHeight().Padding(0,2,0,8)[Tubs]
      // Size gauge: the scoop growing, the right size in green.
      +SVerticalBox::Slot().AutoHeight()[SNew(SBox).WidthOverride(GaugeW).HeightOverride(22)[SNew(SOverlay)
       +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Kraft)]
       +SOverlay::Slot()[SNew(SBox).HAlign(HAlign_Left).Padding(FMargin(RightLo/MaxSize*GaugeW,0,0,0))[SNew(SBox).WidthOverride((RightHi-RightLo)/MaxSize*GaugeW)
        [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Green)]]]
       +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).WidthOverride_Lambda([this](){return FOptionalSize(FMath::Min(Growing,MaxSize)/MaxSize*GaugeW);})
        [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(Ink.R,Ink.G,Ink.B,.5f))]]]]
      +SVerticalBox::Slot().AutoHeight().Padding(0,2)[HandText(TEXT("pequena · certa (verde) · grande"),14,Faded)]
      +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,2)[HandText(TEXT("Cobertura"),18,Faded)]
      +SVerticalBox::Slot().AutoHeight()[Tops]
      +SVerticalBox::Slot().AutoHeight().Padding(0,10,0,0)[SNew(SHorizontalBox)
       +SHorizontalBox::Slot().AutoWidth().Padding(0,0,10,0)[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Undo();return FReply::Handled();})[InkLabel(TEXT("Desfazer bola"),17)]]
       +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Deliver();return FReply::Handled();})[InkLabel(TEXT("Entregar"),17)]]]]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,0)[HandText(TEXT("Segure o sabor (clique, 1 a 6 ou A) e solte no verde · setas escolhem o pote · Enter entrega · Esc ou B sai"),14,Faded)]]]];
  NextCustomer();
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();if(Event.IsRepeat())return FReply::Handled();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Close();return FReply::Handled();}
  static const FKey Digits[]={EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six};
  for(int32 I=0;I<6;++I)if(K==Digits[I] && I<Flavors.Num()){Selected=I;Begin(I);return FReply::Handled();}
  if(K==EKeys::Left || K==EKeys::Gamepad_DPad_Left){Selected=(Selected+Flavors.Num()-1)%FMath::Max(1,Flavors.Num());return FReply::Handled();}
  if(K==EKeys::Right || K==EKeys::Gamepad_DPad_Right){Selected=(Selected+1)%FMath::Max(1,Flavors.Num());return FReply::Handled();}
  if(K==EKeys::Up || K==EKeys::Gamepad_DPad_Up){Topping=(Topping+1)%FMath::Max(1,Toppings.Num());return FReply::Handled();}
  if(K==EKeys::SpaceBar || K==EKeys::Gamepad_FaceButton_Bottom){Begin(Selected);return FReply::Handled();}
  if(K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Top){Deliver();return FReply::Handled();}
  if(K==EKeys::BackSpace || K==EKeys::Gamepad_FaceButton_Left){Undo();return FReply::Handled();}
  return FReply::Unhandled();
 }
 virtual FReply OnKeyUp(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::SpaceBar || K==EKeys::Gamepad_FaceButton_Bottom || K==EKeys::One || K==EKeys::Two || K==EKeys::Three || K==EKeys::Four || K==EKeys::Five || K==EKeys::Six){Commit();return FReply::Handled();}
  return FReply::Unhandled();
 }
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);
  if(Phase==EPhase::Show){if((Timer-=Delta)<=0){Phase=EPhase::Build;Status=TEXT("Agora de memória: monte a casquinha que foi pedida.");}return;}
  if(Phase==EPhase::Result){if((Timer-=Delta)<=0)NextCustomer();return;}
  if(Holding>=0)Growing=FMath::Min(MaxSize,Growing+Delta/GrowTime);
 }
 /** QA: builds the current order (bPerfect) or a wrong one and delivers it. */
 FString QABuild(bool bPerfect)
 {
  auto S=Sim();if(!S || S->IceQueue().IsEmpty())return TEXT("empty");const auto O=S->IceQueue()[0];Phase=EPhase::Build;Scoops.Reset();Sizes.Reset();
  const TArray<TSharedPtr<FJsonValue>>* F=nullptr;if(O->TryGetArrayField(TEXT("flavors"),F))for(const auto& V:*F){Scoops.Add(V->AsString());Sizes.Add(bPerfect?(RightLo+RightHi)*.5f:RightLo*.6f);}
  for(int32 I=0;I<Toppings.Num();++I)if(Toppings[I].Id==UMareSimulation::String(O,TEXT("topping")))Topping=I;
  return TEXT("ok");
 }
 void QADeliver(){Deliver();}
 void QAHold(int32 Flavor,float Seconds){Phase=EPhase::Build;Begin(Flavor);Growing=FMath::Min(MaxSize,Seconds/GrowTime);}
 void QARelease(){Commit();}
 void QAShowNow(){Phase=EPhase::Show;Timer=ShowTime;}
private:
 enum class EPhase{Show,Build,Result};
 struct FItem{FString Id,Name;FLinearColor Color;};
 static constexpr float GaugeW=520,MaxSize=1.3f;
 TWeakObjectPtr<AMareController> Owner;TArray<FItem> Flavors,Toppings;TArray<FString> Scoops;TArray<float> Sizes;FString Status;
 EPhase Phase=EPhase::Show;float Timer=0,Growing=0,RightLo=.7f,RightHi=1,GrowTime=1.6f,ShowTime=3;int32 Holding=-1,Selected=0,Topping=-1,MaxScoops=3;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetSimulation():nullptr;}
 static FLinearColor Color(const TSharedPtr<FJsonObject>& O){const TArray<TSharedPtr<FJsonValue>>* C=nullptr;
  return O->TryGetArrayField(TEXT("color"),C) && C->Num()==3?FLinearColor(FColor(uint8((*C)[0]->AsNumber()*255),uint8((*C)[1]->AsNumber()*255),uint8((*C)[2]->AsNumber()*255))):FLinearColor::White;}
 static const FSlateRoundedBoxBrush& Ball(){static const FSlateRoundedBoxBrush B(FLinearColor::White,60.f);return B;}
 static const FSlateRoundedBoxBrush& Tub(){static const FSlateRoundedBoxBrush B(FLinearColor::White,8.f,MareNotebook::Hex(150,150,160),2.f);return B;}
 static const FSlateRoundedBoxBrush& Rim(){static const FSlateRoundedBoxBrush B(FLinearColor(1,1,1,0),8.f,MareNotebook::Red,3.f);return B;}
 int32 TopScoop()const{return Scoops.Num()-1+(Holding>=0?1:0);}
 float ScoopPx(int32 K)const{const float S=K<Sizes.Num()?Sizes[K]:(K==Sizes.Num() && Holding>=0?Growing:0.f);return S>0?36+56*S:0.f;}
 FLinearColor ScoopColor(int32 K)const{const FString Id=K<Scoops.Num()?Scoops[K]:(Holding>=0 && Flavors.IsValidIndex(Holding)?Flavors[Holding].Id:FString());
  for(const auto& F:Flavors)if(F.Id==Id)return F.Color;return FLinearColor::White;}
 void NextCustomer()
 {
  auto S=Sim();Scoops.Reset();Sizes.Reset();Topping=-1;Holding=-1;Growing=0;
  if(!S || S->IceQueue().IsEmpty()){Close();return;}
  // The order, once, for a few seconds: then it is up to memory.
  const auto O=S->IceQueue()[0];Status=UMareSimulation::String(O,TEXT("name"))+TEXT(" pede: ")+S->IceOrderLine(O);Phase=EPhase::Show;Timer=ShowTime;
 }
 void Begin(int32 Flavor)
 {
  if(Phase!=EPhase::Build || Holding>=0 || Scoops.Num()>=MaxScoops || !Flavors.IsValidIndex(Flavor))return;Holding=Flavor;Selected=Flavor;Growing=0;
  if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("bar_ice_glass"),nullptr,.35f);
 }
 void Commit()
 {
  if(Holding<0)return;const float Size=Growing;Scoops.Add(Flavors[Holding].Id);Sizes.Add(Size);Holding=-1;Growing=0;
  Status=FString::Printf(TEXT("Bola de %s %s. %d de %d bolas."),*Flavors.FindByPredicate([this](const FItem& F){return F.Id==Scoops.Last();})->Name,
   Size<RightLo?TEXT("pequena"):Size>RightHi?TEXT("grande demais"):TEXT("no tamanho certo"),Scoops.Num(),MaxScoops);
 }
 void Undo(){if(Phase==EPhase::Build && Scoops.Num() && Holding<0){Scoops.Pop();Sizes.Pop();Status=TEXT("Bola desfeita.");}}
 void Deliver()
 {
  auto S=Sim();if(!S || Phase!=EPhase::Build || Holding>=0)return;
  if(Scoops.IsEmpty()){Status=TEXT("Ponha pelo menos uma bola na casquinha.");return;}
  const auto R=S->ServeIceCream(Scoops,Sizes,Topping>=0?Toppings[Topping].Id:TEXT("nenhuma"));Status=S->LastMessage;Phase=EPhase::Result;Timer=2.2f;
  if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),R.Hits==3?TEXT("money_coins"):R.Hits>0?TEXT("deal_accept"):TEXT("deal_decline"));
 }
 void Close(){if(Owner.IsValid())Owner->CloseBusinessGame();}
};

static TWeakPtr<SMareIceCreamGame> GIceGame;
/** Food truck (CHECKLIST_EXPANSOES 3.2, MarePastel.cpp): pick the filling, seal the edge by dragging along it (or
 *  left/right taps), dip it in the oil and take it out golden (the colour and a ding tell the point), then press the
 *  sugar-cane juice by turning the mill crank when it was asked for. One customer after another. */
class SMarePastelGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMarePastelGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;auto S=Sim();if(!S)return;const auto D=S->PastelDefs();const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
  if(D->TryGetArrayField(TEXT("fillings"),L))for(const auto& V:*L)Fillings.Add({UMareSimulation::String(V->AsObject(),TEXT("id")),UMareSimulation::String(V->AsObject(),TEXT("name")),Color(V->AsObject())});
  SealPx=UMareSimulation::Number(D,TEXT("seal_px"),1400);SealTaps=UMareSimulation::Number(D,TEXT("seal_taps"),14);Turns=UMareSimulation::Number(D,TEXT("crank_turns"),4);
  CrankTaps=UMareSimulation::Number(D,TEXT("crank_taps"),16);GoldenFrom=UMareSimulation::Number(D,TEXT("golden_from"),5.5);GoldenTo=UMareSimulation::Number(D,TEXT("golden_to"),8.5);
  BurntS=UMareSimulation::Number(D,TEXT("burnt_s"),11.5);
  auto Fill=SNew(SHorizontalBox);
  for(int32 I=0;I<Fillings.Num();++I)Fill->AddSlot().AutoWidth().Padding(3,0)[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(10,4))
   .OnClicked_Lambda([this,I](){Choose(I);return FReply::Handled();})
   [SNew(STextBlock).Font(Body(13,true)).ColorAndOpacity_Lambda([this,I](){return FSlateColor(Filling==I?Red:Ink);}).Text(MareLoc::Text(Fillings[I].Name))]];
  // The pastel: a half-moon of dough (raw, golden, browning, burnt), the filling showing until it is sealed, the
  // crimped edge marks; behind it the oil while frying.
  auto Crimps=SNew(SHorizontalBox);
  for(int32 K=0;K<10;++K)Crimps->AddSlot().AutoWidth().Padding(2,0)[SNew(SBox).WidthOverride(12).HeightOverride(10)[SNew(SBorder).BorderImage(&Crimp()).Padding(0)
   .BorderBackgroundColor_Lambda([this,K](){const FLinearColor C=DoughColor()*.55f;return FSlateColor(Seal>=(K+1)/10.f?FLinearColor(C.R,C.G,C.B,1):FLinearColor(1,1,1,0));})]];
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,50)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,14))
   [SNew(SBox).WidthOverride(780)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().FillWidth(1)[HandText(TEXT("Food truck do pastel"),28,Brown)]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Faded).Text_Lambda([this](){
      auto S=Sim();return MareLoc::Text(S?FString::Printf(TEXT("na fila: %d"),S->PastelQueue().Num()):FString());})]]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(22)).ColorAndOpacity(Red).Text_Lambda([this](){return MareLoc::Text(Order);})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,2)[SNew(STextBlock).Font(Hand(20)).ColorAndOpacity(Ink).AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(Status);})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,6)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().Padding(0,0,22,0)[SNew(SBox).WidthOverride(240).HeightOverride(150)[SNew(SOverlay)
      // Oil in the fryer, bubbling while the pastel is in it.
      +SOverlay::Slot()[SNew(SBorder).BorderImage(&Pan()).Padding(0).BorderBackgroundColor_Lambda([this](){
       return FSlateColor(Step==EStep::Fry?FLinearColor(.86f,.6f,.16f,.55f+.1f*FMath::Sin(Clock*14)):FLinearColor(.9f,.86f,.78f,.35f));})]
      +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(190).HeightOverride(96).Visibility_Lambda([this](){return Filling>=0?EVisibility::Visible:EVisibility::Hidden;})
       [SNew(SBorder).BorderImage(&HalfMoon()).Padding(0).BorderBackgroundColor_Lambda([this](){return FSlateColor(DoughColor());})
        [SNew(SOverlay)
         +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(0,10,0,0)[SNew(SBox).WidthOverride(120).HeightOverride(40)[SNew(SBorder).BorderImage(&Dot()).Padding(0)
          .BorderBackgroundColor_Lambda([this](){return FSlateColor(Fillings.IsValidIndex(Filling)?FLinearColor(Fillings[Filling].Color.R,Fillings[Filling].Color.G,Fillings[Filling].Color.B,1-Seal):FLinearColor(1,1,1,0));})]]
         +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,6)[Crimps]]]]]]
     +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Top)[SNew(SVerticalBox)
      +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("1. Recheio"),18,Faded)]
      +SVerticalBox::Slot().AutoHeight().Padding(0,2,0,6)[Fill]
      +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Faded).Text_Lambda([this](){
       return MareLoc::Text(FString::Printf(TEXT("2. Fechar a borda: %.0f%%"),Seal*100));})]
      +SVerticalBox::Slot().AutoHeight().Padding(0,2)[Gauge([this](){return Seal;},[](){return 1.f;},[](){return 1.f;})]
      +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,0)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Faded).Text_Lambda([this](){
       return MareLoc::Text(Step==EStep::Fry?FString::Printf(TEXT("3. Fritando: %.1f s"),FryT):TEXT("3. Fritar"));})]
      +SVerticalBox::Slot().AutoHeight().Padding(0,2)[Gauge([this](){return FryT/BurntS;},[this](){return GoldenFrom/BurntS;},[this](){return GoldenTo/BurntS;})]
      +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,0)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity_Lambda([this](){return FSlateColor(bWantsCana?Ink:Faded);}).Text_Lambda([this](){
       return MareLoc::Text(bWantsCana?FString::Printf(TEXT("4. Caldo de cana: girar a manivela (%.1f de %.0f voltas)"),Crank,Turns):TEXT("4. Caldo de cana: não pedido"));})]
      +SVerticalBox::Slot().AutoHeight().Padding(0,2)[SNew(SHorizontalBox)
       +SHorizontalBox::Slot().AutoWidth().Padding(0,0,10,0)[SNew(SBox).WidthOverride(44).HeightOverride(44)[SNew(SOverlay)
        +SOverlay::Slot()[SNew(SBorder).BorderImage(&Hub()).BorderBackgroundColor(Kraft)]
        +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(36).HeightOverride(6)
         .RenderTransform_Lambda([this](){return TransformCast<FSlateRenderTransform>(FQuat2D(Crank*2*PI));}).RenderTransformPivot(FVector2D(.5f,.5f))
         [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Brown)]]]]
       +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[Gauge([this](){return bWantsCana?Crank/FMath::Max(1.f,Turns):0.f;},[](){return 1.f;},[](){return 1.f;})]]
      +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,0)[SNew(SHorizontalBox)
       +SHorizontalBox::Slot().AutoWidth().Padding(0,0,10,0)[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Dip();return FReply::Handled();})[InkLabel(TEXT("Mergulhar no óleo"),17)]]
       +SHorizontalBox::Slot().AutoWidth().Padding(0,0,10,0)[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){TakeOut();return FReply::Handled();})[InkLabel(TEXT("Tirar do óleo"),17)]]
       +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Deliver();return FReply::Handled();})[InkLabel(TEXT("Entregar"),17)]]]]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,0)[HandText(TEXT("Arraste o mouse sobre o pastel para fechar a borda (ou setas esquerda e direita) · Espaço mergulha e tira · gire o mouse ou use as setas na manivela · Esc ou B sai"),14,Faded)]]]];
  NextCustomer();
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();if(Event.IsRepeat())return FReply::Handled();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Close();return FReply::Handled();}
  static const FKey Digits[]={EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four};
  for(int32 I=0;I<4;++I)if(K==Digits[I]){Choose(I);return FReply::Handled();}
  const bool bLeft=K==EKeys::Left || K==EKeys::Gamepad_DPad_Left,bRight=K==EKeys::Right || K==EKeys::Gamepad_DPad_Right;
  if(bLeft || bRight){if(LastTap!=(bLeft?1:2)){LastTap=bLeft?1:2;Work(-1);}return FReply::Handled();}
  if(K==EKeys::SpaceBar || K==EKeys::Gamepad_FaceButton_Bottom){if(Step==EStep::Fry)TakeOut();else Dip();return FReply::Handled();}
  if(K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Top){Deliver();return FReply::Handled();}
  return FReply::Unhandled();
 }
 virtual FReply OnMouseButtonDown(const FGeometry&,const FPointerEvent& Event) override
 {
  if(Event.GetEffectingButton()==EKeys::LeftMouseButton){bDragging=true;return FReply::Handled().CaptureMouse(SharedThis(this));}return FReply::Unhandled();
 }
 virtual FReply OnMouseButtonUp(const FGeometry&,const FPointerEvent& Event) override{bDragging=false;return FReply::Handled().ReleaseMouseCapture();}
 virtual FReply OnMouseMove(const FGeometry&,const FPointerEvent& Event) override
 {
  if(bDragging)Work(FMath::Abs(Event.GetCursorDelta().X)+FMath::Abs(Event.GetCursorDelta().Y));return FReply::Handled();
 }
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);Clock+=Delta;
  if(Step==EStep::Result){if((Timer-=Delta)<=0)NextCustomer();return;}
  if(Step==EStep::Fry){FryT+=Delta;SizzleClock-=Delta;
   if(SizzleClock<=0){SizzleClock=1.9f;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("pastel_fry"),nullptr,.6f);}
   // The golden point: a soft ding, and the dough turns golden.
   if(!bDinged && FryT>=GoldenFrom){bDinged=true;Status=TEXT("Dourado! Tire do óleo agora.");if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("pastel_ready"),nullptr,.7f);}
   if(FryT>GoldenTo && FryT-Delta<=GoldenTo)Status=TEXT("Está escurecendo... tire logo!");
   if(FryT>BurntS && FryT-Delta<=BurntS)Status=TEXT("Queimou!");}
 }
 // QA (AMareController::PastelQA).
 FString QAPerfect(bool bRight)
 {
  auto S=Sim();if(!S || S->PastelQueue().IsEmpty())return TEXT("empty");const auto O=S->PastelQueue()[0];
  for(int32 I=0;I<Fillings.Num();++I)if((Fillings[I].Id==UMareSimulation::String(O,TEXT("filling")))==bRight){Choose(I);break;}
  Seal=bRight?1.f:.4f;Dip();FryT=bRight?7.f:12.f;TakeOut();if(bWantsCana && bRight)Crank=Turns;Deliver();return S->LastMessage;
 }
 void QAStep(const FString& What,float V)
 {
  if(What==TEXT("fill")){auto S=Sim();if(S && S->PastelQueue().Num())for(int32 I=0;I<Fillings.Num();++I)if(Fillings[I].Id==UMareSimulation::String(S->PastelQueue()[0],TEXT("filling")))Choose(I);}
  else if(What==TEXT("seal"))Seal=FMath::Clamp(V,0.f,1.f);else if(What==TEXT("dip"))Dip();else if(What==TEXT("fry"))FryT=V;
  else if(What==TEXT("out"))TakeOut();else if(What==TEXT("crank"))Crank=V;else if(What==TEXT("deliver"))Deliver();
 }
private:
 enum class EStep{Fill,Seal,Fry,Cana,Ready,Result};
 struct FItem{FString Id,Name;FLinearColor Color;};
 TWeakObjectPtr<AMareController> Owner;TArray<FItem> Fillings;FString Order,Status;EStep Step=EStep::Fill;
 int32 Filling=-1,LastTap=0;float Seal=0,FryT=0,Crank=0,Timer=0,Clock=0,SizzleClock=0,SealPx=1400,SealTaps=14,Turns=4,CrankTaps=16,GoldenFrom=5.5f,GoldenTo=8.5f,BurntS=11.5f;
 bool bWantsCana=false,bDragging=false,bDinged=false,bFried=false;double FriedFor=0;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetSimulation():nullptr;}
 static FLinearColor Color(const TSharedPtr<FJsonObject>& O){const TArray<TSharedPtr<FJsonValue>>* C=nullptr;
  return O->TryGetArrayField(TEXT("color"),C) && C->Num()==3?FLinearColor(FColor(uint8((*C)[0]->AsNumber()*255),uint8((*C)[1]->AsNumber()*255),uint8((*C)[2]->AsNumber()*255))):FLinearColor::White;}
 static const FSlateRoundedBoxBrush& HalfMoon(){static const FSlateRoundedBoxBrush B(FLinearColor::White,FVector4(95,95,10,10));return B;}
 static const FSlateRoundedBoxBrush& Dot(){static const FSlateRoundedBoxBrush B(FLinearColor::White,20.f);return B;}
 // A rounded box only draws when its radius fits the box: one brush per size.
 static const FSlateRoundedBoxBrush& Crimp(){static const FSlateRoundedBoxBrush B(FLinearColor::White,4.f);return B;}
 static const FSlateRoundedBoxBrush& Hub(){static const FSlateRoundedBoxBrush B(FLinearColor::White,21.f);return B;}
 static const FSlateRoundedBoxBrush& Pan(){static const FSlateRoundedBoxBrush B(FLinearColor::White,16.f,MareNotebook::Hex(90,90,96),3.f);return B;}
 FLinearColor DoughColor()const
 {
  // Raw pale dough -> golden -> brown -> burnt, by the time in the oil.
  const float T=bFried||Step==EStep::Fry?FryT:0.f;const FLinearColor Raw(FColor(246,226,170)),Gold(FColor(232,165,62)),Brown(FColor(140,82,32)),Burnt(FColor(46,30,20));
  if(T<GoldenFrom)return FLinearColor::LerpUsingHSV(Raw,Gold,T/GoldenFrom);if(T<GoldenTo)return Gold;
  if(T<BurntS)return FLinearColor::LerpUsingHSV(Gold,Brown,(T-GoldenTo)/(BurntS-GoldenTo));return Burnt;
 }
 static TSharedRef<SWidget> Gauge(TFunction<float()> Value,TFunction<float()> Lo,TFunction<float()> Hi)
 {
  using namespace MareNotebook;const float W=440;
  return SNew(SBox).WidthOverride(W).HeightOverride(16)[SNew(SOverlay)
   +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Kraft)]
   +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).Padding_Lambda([Lo,Hi,W](){return FMargin(Hi()-Lo()>.001f?Lo()*W:0,0,0,0);})
    .WidthOverride_Lambda([Lo,Hi,W](){return FOptionalSize(Hi()-Lo()>.001f?Hi()*W:0.f);})
    [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Green)]]
   +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).WidthOverride_Lambda([Value,W](){return FOptionalSize(FMath::Clamp(Value(),0.f,1.f)*W);})
    [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(Ink.R,Ink.G,Ink.B,.55f))]]];
 }
 void NextCustomer()
 {
  auto S=Sim();Filling=-1;Seal=FryT=Crank=0;bDinged=bFried=false;Step=EStep::Fill;LastTap=0;
  if(!S || S->PastelQueue().IsEmpty()){Close();return;}
  const auto O=S->PastelQueue()[0];bWantsCana=false;O->TryGetBoolField(TEXT("cana"),bWantsCana);
  Order=UMareSimulation::String(O,TEXT("name"))+TEXT(" pede: ")+S->PastelOrderLine(O);Status=TEXT("Escolha o recheio.");
 }
 void Choose(int32 I){if(Step==EStep::Fill && Fillings.IsValidIndex(I)){Filling=I;Step=EStep::Seal;Status=TEXT("Recheio de ")+Fillings[I].Name+TEXT(". Agora arraste sobre o pastel para fechar a borda.");}}
 void Work(float Px)
 {
  // Px<0: one keyboard tap; otherwise mouse travel in pixels.
  if(Step==EStep::Seal && Seal<1){Seal=FMath::Min(1.f,Seal+(Px<0?1.f/SealTaps:Px/SealPx));if(Seal>=1)Status=TEXT("Borda fechada. Mergulhe no óleo.");}
  else if(Step==EStep::Cana && Crank<Turns){const float Before=Crank;Crank=FMath::Min(Turns,Crank+(Px<0?Turns/CrankTaps:Px/600.f));
   if(FMath::FloorToInt(Crank)>FMath::FloorToInt(Before) && Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("cana_crank"),nullptr,.6f);
   if(Crank>=Turns){Step=EStep::Ready;Status=TEXT("Caldo de cana no copo. Entregue!");}}
 }
 void Dip()
 {
  if(Step!=EStep::Seal)return;Step=EStep::Fry;FryT=0;SizzleClock=0;bDinged=false;
  Status=Seal>=1?TEXT("Fritando... espere o ponto dourado (e o ding)."):TEXT("A borda não estava fechada: o recheio está vazando!");
 }
 void TakeOut()
 {
  if(Step!=EStep::Fry)return;bFried=true;FriedFor=FryT;Step=bWantsCana?EStep::Cana:EStep::Ready;
  Status=(FryT<GoldenFrom?TEXT("Saiu cru... "):FryT<=GoldenTo?TEXT("Dourado no ponto! "):FryT<=BurntS?TEXT("Passou um pouco do ponto. "):TEXT("Queimado... "))
   +FString(bWantsCana?TEXT("Agora o caldo de cana: gire a manivela."):TEXT("Entregue."));
 }
 void Deliver()
 {
  auto S=Sim();if(!S || Step==EStep::Result || Step==EStep::Fill || Step==EStep::Fry || !bFried){if(Step==EStep::Seal)Status=TEXT("Frite o pastel antes de entregar.");return;}
  const auto R=S->ServePastel(Fillings.IsValidIndex(Filling)?Fillings[Filling].Id:FString(),Seal>=1,FriedFor,bWantsCana && Crank>=Turns);
  Status=S->LastMessage;Step=EStep::Result;Timer=2.4f;
  if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),R.Hits==3?TEXT("money_coins"):R.Hits>0?TEXT("deal_accept"):TEXT("deal_decline"));
 }
 void Close(){if(Owner.IsValid())Owner->CloseBusinessGame();}
};

static TWeakPtr<SMarePastelGame> GPastelGame;
/** Board and kayak rental (CHECKLIST_EXPANSOES 3.3, MareRental.cpp): returned boards are checked first (a dent drawn
 *  somewhere on the board: fine it or let it go), then the line: wax the board with circular strokes (mouse circles,
 *  or the arrows in turn) for a tip, and rent it for the time the customer asked. */
class SMareRentalGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareRentalGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;auto S=Sim();if(!S)return;WaxTurns=UMareSimulation::Number(S->RentalDefs(),TEXT("wax_turns"),5);
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,50)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,14))
   [SNew(SBox).WidthOverride(780)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().FillWidth(1)[HandText(TEXT("Aluguel de pranchas e caiaques"),28,Brown)]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Faded).Text_Lambda([this](){
      auto S=Sim();return MareLoc::Text(S?FString::Printf(TEXT("fila: %d · na água: %d · voltando: %d"),S->RentalQueue().Num(),S->RentalOut().Num(),S->RentalReturns().Num()):FString());})]]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(22)).ColorAndOpacity(Red).AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(Header);})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,2)[SNew(STextBlock).Font(Hand(19)).ColorAndOpacity(Ink).AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(Status);})]
    // The board (or kayak) seen from above: wax shine grows while waxing, the dent shows as a dark dimple.
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,8)[SNew(SBox).WidthOverride(BoardW).HeightOverride(BoardH)[SNew(SOverlay)
     +SOverlay::Slot()[SNew(SBorder).BorderImage(&Board()).Padding(0).BorderBackgroundColor_Lambda([this](){return FSlateColor(bKayak?FLinearColor(FColor(240,108,22)):FLinearColor(FColor(214,204,180)));})]
     +SOverlay::Slot().HAlign(HAlign_Center)[SNew(SBox).WidthOverride(8)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).Padding(0)
      .BorderBackgroundColor_Lambda([this](){return FSlateColor(bKayak?FLinearColor(0,0,0,0):FLinearColor(FColor(40,120,190)));})]]
     +SOverlay::Slot()[SNew(SBorder).BorderImage(&Board()).Padding(0).BorderBackgroundColor_Lambda([this](){return FSlateColor(FLinearColor(1,.97f,.82f,Mode==EMode::Rent?.85f*FMath::Min(1.f,Wax/WaxTurns)*(.8f+.2f*FMath::Sin(Wax*9)):0.f));})]
     +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top)[SNew(SBox).Padding_Lambda([this](){return FMargin(DentAt.X*(BoardW-30),DentAt.Y*(BoardH-22),0,0);})
      [SNew(SBox).WidthOverride(30).HeightOverride(22).Visibility_Lambda([this](){return Mode==EMode::Inspect && bDent?EVisibility::HitTestInvisible:EVisibility::Collapsed;})
       [SNew(SBorder).BorderImage(&Dimple()).Padding(0).BorderBackgroundColor(FLinearColor(.25f,.2f,.16f,.55f))]]]]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,2)[SNew(SBox).WidthOverride(BoardW).HeightOverride(14).Visibility_Lambda([this](){return Mode==EMode::Rent?EVisibility::Visible:EVisibility::Collapsed;})
     [SNew(SOverlay)+SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Kraft)]
      +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).WidthOverride_Lambda([this](){return FOptionalSize(FMath::Min(1.f,Wax/WaxTurns)*BoardW);})
       [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Green)]]]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,0)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().Padding(0,0,10,0)[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Left();return FReply::Handled();})
      [SNew(STextBlock).Font(Hand(17)).ColorAndOpacity(MareNotebook::Tag).Text_Lambda([this](){return MareLoc::Text(Mode==EMode::Inspect?TEXT("Tudo certo, sem multa"):TEXT("Alugar sem parafina"));})]]
     +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Right();return FReply::Handled();})
      [SNew(STextBlock).Font(Hand(17)).ColorAndOpacity(MareNotebook::Tag).Text_Lambda([this](){return MareLoc::Text(Mode==EMode::Inspect?TEXT("Cobrar multa (amassado)"):TEXT("Alugar"));})]]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,0)[HandText(TEXT("Confira a prancha que voltou: amassado é multa, multa sem amassado irrita. Antes de alugar, faça círculos com o mouse segurando o botão (ou as setas em sequência) para passar a parafina · Esc ou B sai"),14,Faded)]]]];
  Next();
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();if(Event.IsRepeat())return FReply::Handled();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Close();return FReply::Handled();}
  // Arrows in turn (up, right, down, left) are a quarter circle each.
  static const FKey Seq[]={EKeys::Up,EKeys::Right,EKeys::Down,EKeys::Left};static const FKey Pad[]={EKeys::Gamepad_DPad_Up,EKeys::Gamepad_DPad_Right,EKeys::Gamepad_DPad_Down,EKeys::Gamepad_DPad_Left};
  for(int32 I=0;I<4;++I)if(K==Seq[I] || K==Pad[I]){if(I==(LastArrow+1)%4)AddWax(.25f);LastArrow=I;return FReply::Handled();}
  if(K==EKeys::One)Left();else if(K==EKeys::Two || K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom)Right();else return FReply::Unhandled();
  return FReply::Handled();
 }
 virtual FReply OnMouseButtonDown(const FGeometry& G,const FPointerEvent& E) override
 {
  if(E.GetEffectingButton()!=EKeys::LeftMouseButton)return FReply::Unhandled();bWaxing=true;LastAngle=Angle(G,E);return FReply::Handled().CaptureMouse(SharedThis(this));
 }
 virtual FReply OnMouseButtonUp(const FGeometry&,const FPointerEvent&) override{bWaxing=false;return FReply::Handled().ReleaseMouseCapture();}
 virtual FReply OnMouseMove(const FGeometry& G,const FPointerEvent& E) override
 {
  // Waxing is circles: the turned angle around the panel centre, either way round.
  if(bWaxing && Mode==EMode::Rent){const float A=Angle(G,E);float D=FMath::FindDeltaAngleRadians(LastAngle,A);LastAngle=A;AddWax(FMath::Abs(D)/(2*PI));}
  return FReply::Handled();
 }
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override{SCompoundWidget::Tick(Geometry,Time,Delta);if(Pause>0 && (Pause-=Delta)<=0)Next();}
 // QA (AMareController::RentalQA).
 void QAWax(float Turns){Mode=EMode::Rent;AddWax(Turns);}
 void QALeft(){Left();}
 void QARight(){Right();}
 bool QADent()const{return bDent;}
 void QAShowDent(){Mode=EMode::Inspect;bDent=true;DentAt=FVector2D(.62f,.35f);}
private:
 enum class EMode{Inspect,Rent,Done};
 static constexpr float BoardW=520,BoardH=110;
 TWeakObjectPtr<AMareController> Owner;FString Header,Status;EMode Mode=EMode::Rent;bool bDent=false,bKayak=false,bWaxing=false;
 FVector2D DentAt=FVector2D(.5f,.5f);float Wax=0,WaxTurns=5,LastAngle=0,Pause=0;int32 LastArrow=3;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetSimulation():nullptr;}
 static const FSlateRoundedBoxBrush& Board(){static const FSlateRoundedBoxBrush B(FLinearColor::White,55.f);return B;}
 static const FSlateRoundedBoxBrush& Dimple(){static const FSlateRoundedBoxBrush B(FLinearColor::White,11.f);return B;}
 static float Angle(const FGeometry& G,const FPointerEvent& E){const FVector2D P=G.AbsoluteToLocal(E.GetScreenSpacePosition())-G.GetLocalSize()*.5f;return FMath::Atan2(P.Y,P.X);}
 void AddWax(float Turns)
 {
  if(Mode!=EMode::Rent)return;const bool bWas=Wax>=WaxTurns;Wax=FMath::Min(WaxTurns,Wax+Turns);
  if(!bWas && Wax>=WaxTurns){Status=TEXT("Parafina passada: a prancha brilha. Alugue!");if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"),nullptr,.4f);}
  else if(Wax<WaxTurns)Status=FString::Printf(TEXT("Passando parafina... %.0f%%"),Wax/WaxTurns*100);
 }
 void Next()
 {
  auto S=Sim();Wax=0;Pause=0;LastArrow=3;if(!S){Close();return;}
  // Returns first: the customer waits at the counter with the board.
  if(S->RentalReturns().Num()){const auto O=S->RentalReturns()[0];Mode=EMode::Inspect;O->TryGetBoolField(TEXT("dent"),bDent);bKayak=UMareSimulation::String(O,TEXT("item"))==TEXT("caiaque");
   const uint32 Seed=FCrc::StrCrc32(*UMareSimulation::String(O,TEXT("name")))+uint32(UMareSimulation::Number(O,TEXT("due")));
   DentAt=FVector2D(.18f+.64f*float(Seed%97)/97.f,.2f+.6f*float((Seed/97)%89)/89.f);
   Header=UMareSimulation::String(O,TEXT("name"))+TEXT(" devolveu ")+S->RentalItemName(UMareSimulation::String(O,TEXT("item")))+TEXT(".");Status=TEXT("Confira bem: tem algum amassado?");return;}
  if(S->RentalQueue().Num()){const auto O=S->RentalQueue()[0];Mode=EMode::Rent;bDent=false;bKayak=UMareSimulation::String(O,TEXT("item"))==TEXT("caiaque");
   Header=S->RentalRequestLine(O);Status=TEXT("Passe a parafina em círculos (gorjeta) ou alugue assim mesmo.");return;}
  Close();
 }
 void Left()
 {
  auto S=Sim();if(!S || Pause>0)return;
  if(Mode==EMode::Inspect){const int32 R=S->InspectReturn(false);Done(R>=2);}else if(Mode==EMode::Rent){S->RentItem(false);Done(true);}
 }
 void Right()
 {
  auto S=Sim();if(!S || Pause>0)return;
  if(Mode==EMode::Inspect){const int32 R=S->InspectReturn(true);Done(R>=2);}else if(Mode==EMode::Rent){S->RentItem(Wax>=WaxTurns);Done(true);}
 }
 void Done(bool bGood){auto S=Sim();Status=S?S->LastMessage:FString();Mode=EMode::Done;Pause=2.2f;
  if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),bGood?TEXT("money_coins"):TEXT("deal_decline"),nullptr,.6f);}
 void Close(){if(Owner.IsValid())Owner->CloseBusinessGame();}
};

static TWeakPtr<SMareRentalGame> GRentalGame;
/** Fishing at the pier: the line goes in, a random wait, then "Fisgou!" and a short window to strike
 *  (E, Space, Enter, click or A). Esc or B reels in. Several casts in a row; each catch goes to the stock. */
class SMareFishingGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareFishingGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;Cast();
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,70)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,16))
   [SNew(SBox).WidthOverride(560)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Pescaria no píer"),30,Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,6)[SNew(STextBlock).Font(Hand(26)).ColorAndOpacity_Lambda([this](){return FSlateColor(bBite?MareNotebook::Red:MareNotebook::Ink);})
     .Text_Lambda([this](){return MareLoc::Text(Status);})]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Green).Text_Lambda([this](){return MareLoc::Text(FString::Printf(TEXT("Peixes hoje: %d"),Caught));})]
    +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Espere o peixe fisgar e aperte E, Espaço, clique ou A na hora · Esc ou B recolhe a linha"),15,Faded)]]]];
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){if(Owner.IsValid())Owner->CloseBusinessGame();return FReply::Handled();}
  if(K==EKeys::E || K==EKeys::SpaceBar || K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom || K==EKeys::Gamepad_FaceButton_Left){Strike();return FReply::Handled();}
  return FReply::Unhandled();
 }
 virtual FReply OnMouseButtonDown(const FGeometry&,const FPointerEvent&) override{Strike();return FReply::Handled();}
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);Timer-=Delta;
  if(Timer>0)return;
  if(bBite){bBite=false;Status=TEXT("Escapou... a linha voltou vazia.");Timer=1.2f;bRecast=true;return;}
  if(bRecast){bRecast=false;Cast();return;}
  bBite=true;Status=TEXT("FISGOU! Puxe agora!");Timer=Window;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("pool_rail_bounce"));
 }
private:
 TWeakObjectPtr<AMareController> Owner;FString Status;float Timer=0,Window=1.1f;bool bBite=false,bRecast=false;int32 Caught=0;
 void Cast()
 {
  auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;float Low=2,High=6;
  if(S){const TArray<TSharedPtr<FJsonValue>>* Wait=nullptr;if(S->LeisureDefs()->TryGetArrayField(TEXT("bite_wait"),Wait) && Wait->Num()==2){Low=(*Wait)[0]->AsNumber();High=(*Wait)[1]->AsNumber();}
   Window=UMareSimulation::Number(S->LeisureDefs(),TEXT("bite_window"),1.1);}
  Timer=FMath::FRandRange(Low,High);Status=TEXT("Linha na água... espere.");bBite=false;
  if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("bar_pour"),nullptr,.5f);
 }
 void Strike()
 {
  if(bRecast)return;
  if(!bBite){Status=TEXT("Cedo demais! O peixe se assustou.");Timer=1.2f;bRecast=true;return;}
  bBite=false;auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;
  if(S && !S->CatchFish().IsEmpty()){++Caught;Status=S->LastMessage;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"));}
  Timer=2.2f;bRecast=true;
 }
};
/** Bar prep mini-actions (CHECKLIST_EXPANSOES 1.1). "socar": a pulse comes round four times, tap E on each beat.
 *  "bater": hold E, the shake bar fills; let go inside the green (past it the drink spills). "liquidificar": the
 *  blender speed swings, pulse E three times while it is in the zone. Esc or B gives up (the glass stays as it is). */
class SMareBarPrepGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareBarPrepGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_ARGUMENT(FString,Step) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;Step=Args._Step;
  auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;
  const FString Title=S?UMareSimulation::String(UMareSimulation::Object(S->BarDefs(),TEXT("prep_lines")),Step):Step;
  const FString Help=Step==TEXT("socar")?TEXT("Aperte E, Espaço, clique ou A quando o círculo acender · 4 batidas")
   :Step==TEXT("bater")?TEXT("Segure E, Espaço, clique ou A para bater e solte no verde · passou, derramou")
   :TEXT("Aperte E, Espaço, clique ou A quando o ponteiro estiver no verde · 3 pulsos");
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,70)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,16))
   [SNew(SBox).WidthOverride(BarWidth+52)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[HandText(Title.IsEmpty()?Step:Title,30,Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4)[SNew(STextBlock).Font(Hand(22)).ColorAndOpacity(Ink).Text_Lambda([this](){return MareLoc::Text(Status);})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,8)[SNew(SBox).WidthOverride(BarWidth).HeightOverride(46)[SNew(SOverlay)
     +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Kraft)]
     // Green zone (shake target / blender zone) or the beat flash (muddle).
     +SOverlay::Slot()[SNew(SBox).HAlign(HAlign_Left).Padding_Lambda([this](){return FMargin(ZoneLo()*BarWidth,0,0,0);})
      [SNew(SBox).WidthOverride_Lambda([this](){return FOptionalSize((ZoneHi()-ZoneLo())*BarWidth);})
       [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor_Lambda([this](){
        return FSlateColor(Step==TEXT("socar")?FLinearColor::LerpUsingHSV(MareNotebook::Kraft,MareNotebook::Green,BeatGlow()):MareNotebook::Green);})]]]
     // Fill (shake) or pointer (blender, muddle).
     +SOverlay::Slot()[SNew(SBox).HAlign(HAlign_Left).Padding_Lambda([this](){return FMargin(Step==TEXT("bater")?0.f:FMath::Max(0.f,Pointer()*BarWidth-4),0,0,0);})
      [SNew(SBox).WidthOverride_Lambda([this](){return FOptionalSize(Step==TEXT("bater")?FMath::Min(1.f,Fill)*BarWidth:8.f);})
       [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor_Lambda([this](){
        return FSlateColor(Step==TEXT("bater")?FLinearColor(MareNotebook::Ink.R,MareNotebook::Ink.G,MareNotebook::Ink.B,.55f):MareNotebook::Ink);})]]]]]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(24)).ColorAndOpacity(Green).Text_Lambda([this](){
     FString Dots;for(int32 I=0;I<Needed();++I)Dots+=I<Marks.Num()?(Marks[I]?TEXT("O "):TEXT("X ")):TEXT("- ");return MareLoc::Text(Dots);})]
    +SVerticalBox::Slot().AutoHeight()[HandText(Help+TEXT(" · Esc ou B desiste"),15,Faded)]]]];
  Status=Step==TEXT("bater")?TEXT("Segure para bater..."):TEXT("Atenção ao ritmo...");
  if(Step==TEXT("liquidificar") && Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("bar_blender"),nullptr,.6f);
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Close();return FReply::Handled();}
  if(IsAction(K)){if(!Event.IsRepeat())Press();return FReply::Handled();}
  return FReply::Unhandled();
 }
 virtual FReply OnKeyUp(const FGeometry&,const FKeyEvent& Event) override{if(IsAction(Event.GetKey())){Release();return FReply::Handled();}return FReply::Unhandled();}
 virtual FReply OnMouseButtonDown(const FGeometry&,const FPointerEvent&) override{Press();return FReply::Handled();}
 virtual FReply OnMouseButtonUp(const FGeometry&,const FPointerEvent&) override{Release();return FReply::Handled();}
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);
  if(Done>=0){if((Done-=Delta)<=0)Close();return;}
  T+=Delta;
  if(Step==TEXT("bater") && bHolding){Fill+=Delta/1.8f;
   if((ShakeSound-=Delta)<=0 && Owner.IsValid()){UMareAudioWorld::Action(Owner.Get(),TEXT("bar_shaker"),nullptr,.7f);ShakeSound=.55f;}
   if(Fill>1.f){bHolding=false;Score(.15,TEXT("Derramou! Bateu demais..."));}}
  // Muddle: a beat missed entirely counts as a miss.
  if(Step==TEXT("socar") && Marks.Num()<Needed() && T>Beat*(Marks.Num()+1)+Window){Marks.Add(false);if(Marks.Num()>=Needed())Finish();}
 }
private:
 static constexpr float BarWidth=560,Beat=.75f,Window=.16f;
 TWeakObjectPtr<AMareController> Owner;FString Step,Status;TArray<bool> Marks;
 float T=0,Fill=0,Done=-1,ShakeSound=0;bool bHolding=false;
 static bool IsAction(const FKey& K){return K==EKeys::E || K==EKeys::SpaceBar || K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom || K==EKeys::Gamepad_FaceButton_Left;}
 int32 Needed()const{return Step==TEXT("socar")?4:Step==TEXT("liquidificar")?3:1;}
 // Shake: green .72-.93 of the bar; blender zone moves a little after each pulse; muddle flashes the middle on the beat.
 float Blender()const{auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;
  return S?S->BarUpgrade(TEXT("liquidificador"))*float(UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->BarDefs(),TEXT("upgrades")),TEXT("liquidificador")),TEXT("blend_zone"),.03)):0.f;}
 float ZoneLo()const{return Step==TEXT("bater")?.72f:Step==TEXT("liquidificar")?.55f-.12f*Marks.Num()-Blender():.44f;}
 float ZoneHi()const{return Step==TEXT("bater")?.93f:Step==TEXT("liquidificar")?.72f-.12f*Marks.Num()+Blender():.56f;}
 float Pointer()const{return Step==TEXT("liquidificar")?.5f-.5f*FMath::Cos(T*PI*(.9f+.25f*Marks.Num())):FMath::Fmod(T/Beat+.5f,1.f);}
 float ToBeat()const{const float Phase=FMath::Fmod(T,Beat);return FMath::Min(Phase,Beat-Phase);}
 float BeatGlow()const{return FMath::Clamp(1-ToBeat()/(Window*1.5f),0.f,1.f);}
 void Press()
 {
  if(Done>=0)return;
  if(Step==TEXT("bater")){bHolding=true;return;}
  if(Marks.Num()>=Needed())return;
  bool bHit=false;
  if(Step==TEXT("socar")){bHit=ToBeat()<=Window && T>Beat*.5f;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("bar_ice_glass"),nullptr,bHit?.5f:.25f);}
  else{const float P=Pointer();bHit=P>=ZoneLo() && P<=ZoneHi();if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("bar_blender"),nullptr,.5f);}
  Marks.Add(bHit);Status=bHit?TEXT("Isso!"):TEXT("Quase...");
  if(Marks.Num()>=Needed())Finish();
 }
 void Release()
 {
  if(Step!=TEXT("bater") || !bHolding || Done>=0)return;bHolding=false;
  if(Fill>=.72f && Fill<=.93f){Marks.Add(true);Score(1,TEXT("No ponto! Gelado e bem batido."));}
  else{Marks.Add(false);Score(FMath::Clamp(Fill/.72f,0.f,1.f)*.6f,TEXT("Bateu pouco... ficou meio aguado."));}
 }
 void Finish(){int32 Hits=0;for(bool B:Marks)Hits+=B;Score(double(Hits)/Needed(),Hits==Needed()?TEXT("Perfeito!"):Hits>0?TEXT("Deu para o gasto."):TEXT("Saiu meio desajeitado..."));}
 void Score(double Value,const FString& Line)
 {
  auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;if(S)S->BarPrepStep(Step,Value);
  Status=Line;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),Value>=.7?TEXT("deal_accept"):TEXT("deal_decline"));Done=1.2f;
 }
 void Close(){if(Owner.IsValid())Owner->CloseBusinessGame();}
};
/** Demo end screen (events.json "end_of_content"): thanks, the save's numbers, what the full game brings, "keep playing" and the Steam wishlist. */
class SMareEndScreen : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareEndScreen){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_ARGUMENT(bool,Debt) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;auto S=Owner.IsValid()?Owner->GetSimulation():nullptr;if(!S){ChildSlot[SNullWidget::NullWidget];return;}
  const auto End=UMareSimulation::Object(S->EventDefs(),TEXT("end_of_content"));
  if(Args._Debt){
   // Item 10: the debt is paid (full game only). Dona Dilce's words, the credits and back to the same resort.
   const auto Fin=UMareSimulation::Object(S->DebtDefs(),TEXT("finale"));   // i18n:skip
   auto Buttons=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[SAssignNew(Continue,SMarePadButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,4))
     .OnClicked_Lambda([this](){if(Owner.IsValid())Owner->CloseBusinessGame();return FReply::Handled();})
     [SNew(STextBlock).Text(MareLoc::Text(UMareSimulation::String(Fin,TEXT("continue")))).Font(Hand(20)).ColorAndOpacity(MareNotebook::Tag)]]   // i18n:skip
    +SHorizontalBox::Slot().AutoWidth().Padding(12,0,0,0)[SNew(SMarePadButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,4))
     .OnClicked_Lambda([this](){if(Owner.IsValid()){auto O=Owner;O->CloseBusinessGame();O->OpenCredits();}return FReply::Handled();})
     [SNew(STextBlock).Text(MareLoc::Text(UMareSimulation::String(Fin,TEXT("credits")))).Font(Hand(20)).ColorAndOpacity(MareNotebook::Tag)]];   // i18n:skip
   ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(34,26))
    [SNew(SBox).WidthOverride(640)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight()[HandText(UMareSimulation::String(Fin,TEXT("title")),34,Brown)]   // i18n:skip
     +SVerticalBox::Slot().AutoHeight().Padding(0,10)[BodyText(UMareSimulation::String(Fin,TEXT("text")),14,Ink)]   // i18n:skip
     +SVerticalBox::Slot().AutoHeight().Padding(0,6)[HandText(UMareSimulation::String(Fin,TEXT("grandma")),20,Green)]   // i18n:skip
     +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left).Padding(0,14,0,0)[Buttons]]]];
   return;}
  const TArray<TSharedPtr<FJsonValue>>* Album=nullptr;UMareSimulation::Object(S->State,TEXT("prog"))->TryGetArrayField(TEXT("album"),Album);
  const int32 Days=int32(UMareSimulation::Number(S->State,TEXT("day"),1));
  const FString Stats=FString::Printf(TEXT("%d %s · R$ %.0f em caixa · fama: %s · %.1f estrelas · %d drinks descobertos · %d fotos no álbum"),
   Days,Days==1?TEXT("dia"):TEXT("dias"),S->Money(),*S->FameName(),S->Stars(),S->BarDiscoveries(),Album?Album->Num():0);
  // 6.5: what the full game brings (the Grand Hotel stays out of the demo, 06/11) and the Steam wishlist.
  auto Next=SNew(SVerticalBox);const TArray<TSharedPtr<FJsonValue>>* Coming=nullptr;
  if(End->TryGetArrayField(TEXT("next"),Coming) && Coming->Num()){Next->AddSlot().AutoHeight().Padding(0,8,0,2)[HandText(UMareSimulation::String(End,TEXT("next_title")),22,Brown)];
   for(const auto& V:*Coming)Next->AddSlot().AutoHeight().Padding(10,1)[BodyText(TEXT("- ")+V->AsString(),12.5f,Ink)];}
  const FString Review=UMareSimulation::String(End,TEXT("review_url"));
  auto Buttons=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth()[SAssignNew(Continue,SMarePadButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,4))
     .OnClicked_Lambda([this](){if(Owner.IsValid())Owner->CloseBusinessGame();return FReply::Handled();})
     [SNew(STextBlock).Text(MareLoc::Text(TEXT("Continuar jogando"))).Font(Hand(20)).ColorAndOpacity(MareNotebook::Tag)]];
  if(!Review.IsEmpty()){Next->AddSlot().AutoHeight().Padding(0,10,0,0)[BodyText(UMareSimulation::String(End,TEXT("review_text")),12.5f,Faded)];
   Buttons->AddSlot().AutoWidth().Padding(12,0,0,0)[SNew(SMarePadButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,4))
     .OnClicked_Lambda([Review](){FPlatformProcess::LaunchURL(*Review,nullptr,nullptr);return FReply::Handled();})
     [SNew(STextBlock).Text(MareLoc::Text(TEXT("Lista de desejos na Steam"))).Font(Hand(20)).ColorAndOpacity(MareNotebook::Tag)]];}
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(34,26))
   [SNew(SBox).WidthOverride(640)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[HandText(UMareSimulation::String(End,TEXT("title")),34,Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,10)[BodyText(UMareSimulation::String(End,TEXT("text")),14,Ink)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,6)[HandText(Stats,18,Green)]
    +SVerticalBox::Slot().AutoHeight()[Next]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left).Padding(0,14,0,0)[Buttons]]]];
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::Escape || K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom || K==EKeys::Gamepad_FaceButton_Right){if(Owner.IsValid())Owner->CloseBusinessGame();return FReply::Handled();}
  return FReply::Unhandled();
 }
private:
 TWeakObjectPtr<AMareController> Owner;TSharedPtr<SWidget> Continue;
};
// Title art (08/11): UI textures named in title.json, kept loaded with their brushes for the whole session.
static const FSlateBrush* TitleBrush(const FString& Path)
{
 static TMap<FString,TSharedPtr<FSlateBrush>> Brushes;static TArray<TStrongObjectPtr<UTexture2D>> Keep;
 if(Path.IsEmpty())return nullptr;
 if(const TSharedPtr<FSlateBrush>* Found=Brushes.Find(Path))return Found->Get();
 TSharedPtr<FSlateBrush> Brush;
 if(FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(Path)))if(UTexture2D* Tex=LoadObject<UTexture2D>(nullptr,*Path)){
#if WITH_EDITOR
  // In the editor a texture may still be compiling, and its size is then the square placeholder's (the logo came out
  // stretched into a square, 08/11): finish it first.
  FTextureCompilingManager::Get().FinishCompilation({Tex});
#endif
  Keep.Emplace(Tex);Brush=MakeShared<FSlateBrush>();Brush->SetResourceObject(Tex);Brush->ImageSize=FVector2D(Tex->GetSizeX(),Tex->GetSizeY());Brush->DrawAs=ESlateBrushDrawType::Image;}
 Brushes.Add(Path,Brush);return Brush.Get();
}
static bool MareTitleHasArt()
{
 FString Text,ArtPath;TSharedPtr<FJsonObject> T;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/title.json")));   // i18n:skip
 if(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),T) && T.IsValid())T->TryGetStringField(TEXT("art"),ArtPath);   // i18n:skip
 return TitleBrush(ArtPath)!=nullptr;
}
class SMareMainMenu : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareMainMenu){} SLATE_ARGUMENT(AMareController*,Controller) SLATE_END_ARGS()
 void Construct(const FArguments& Args){Controller=Args._Controller;Show(EPage::Main);}
 // OpenMainMenu focuses the menu (FInputModeUIOnly): a non-focusable widget logged an error in every PIE (04/11).
 virtual bool SupportsKeyboardFocus()const override{return true;}
 /** Gamepad B: the previous page (the main page stays). */
 void Back(){switch(Current){case EPage::Main:break;case EPage::Confirm:Show(EPage::New);break;default:Show(EPage::Main);}}
 void ShowCredits(){Show(EPage::Credits);}
private:
 enum class EPage:uint8{Main,Load,New,Confirm,Options,Credits};
 EPage Current=EPage::Main;
 TWeakObjectPtr<AMareController> Controller;
 int32 PendingSlot=0;
 FText Error;
 UMareSimulation* Sim()const{return Controller.IsValid()?Controller->GetSimulation():nullptr;}
 static FText SlotLabel(int32 Index,const FMareSlotInfo& Info)
 {
  if(!Info.bExists)return FText::Format(LOCTEXT("SlotEmpty","Slot {0} · vazio"),Index);
  const FDateTime Local=Info.SavedAt+(FDateTime::Now()-FDateTime::UtcNow());
  const FText Name=Info.Company.IsEmpty()?LOCTEXT("SlotNoCompany","sem empresa"):MareLoc::Text(Info.Company);
  return FText::Format(LOCTEXT("SlotFull","Slot {0} · Dia {1} · R$ {2}\n{3} · salvo em {4}"),Index,Info.Day,MareLoc::Text(FString::Printf(TEXT("%.0f"),Info.Money)),Name,MareLoc::Text(Local.ToString(TEXT("%d/%m/%Y %H:%M"))));
 }
 void Fail(){Error=Sim()?MareLoc::Text(Sim()->LastMessage):FText::GetEmpty();Show(EPage::Main);}
 void Show(EPage Page)
 {
  auto S=Sim();if(!S)return;
  Current=Page;
  auto Box=SNew(SVerticalBox);
  auto Button=[&Box](const FText& Label,TFunction<void()> Callback,bool bEnabled){Box->AddSlot().AutoHeight().Padding(0,5)[SNew(SMarePadButton).IsEnabled(bEnabled).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(14,8)).OnClicked_Lambda([Callback](){Callback();return FReply::Handled();})[MareUI::Text(Label.ToString(),14,FLinearColor::White)]];};
  auto Back=[this,&Button](){Button(LOCTEXT("Back","Voltar"),[this](){Show(EPage::Main);},true);};
  const bool bTitleMode=Controller.IsValid() && Controller->IsTitle();
  if(!bTitleMode)Box->AddSlot().AutoHeight().Padding(0,0,0,4)[MareUI::Text(TEXT("Maré Alta Resort"),24)];
  switch(Page){
  case EPage::Main:{
   Box->AddSlot().AutoHeight().Padding(0,0,0,12)[MareUI::Text(LOCTEXT("Subtitle","O quiosque da avó Dilce espera por você.").ToString(),12)];
   const int32 Last=S->LastSlot();const FMareSlotInfo LastInfo=S->SlotInfo(Last);
   Button(LOCTEXT("NewGame","Novo jogo"),[this](){Error=FText::GetEmpty();Show(EPage::New);},true);
   Button(LastInfo.bExists?FText::Format(LOCTEXT("ContinueSlot","Continuar · slot {0}, dia {1}"),Last,LastInfo.Day):LOCTEXT("Continue","Continuar"),[this,Last](){if(!Controller.IsValid() || !Controller->MenuLoadSlot(Last))Fail();},LastInfo.bExists);
   Button(LOCTEXT("Load","Carregar"),[this](){Error=FText::GetEmpty();Show(EPage::Load);},S->HasAnySave());
   Button(LOCTEXT("Options","Opções"),[this](){Show(EPage::Options);},true);
   Button(LOCTEXT("Credits","Créditos"),[this](){Show(EPage::Credits);},true);
   Button(LOCTEXT("Quit","Sair"),[this](){if(Controller.IsValid())UKismetSystemLibrary::QuitGame(Controller.Get(),Controller.Get(),EQuitPreference::Quit,false);},true);
   if(!Error.IsEmpty())Box->AddSlot().AutoHeight().Padding(0,10,0,0)[MareUI::Text(Error.ToString(),12,FLinearColor(.7f,.15f,.1f))];
   break;}
  case EPage::Load:case EPage::New:{
   const bool bNew=Page==EPage::New;
   Box->AddSlot().AutoHeight().Padding(0,0,0,10)[MareUI::Text((bNew?LOCTEXT("PickNew","Escolha o slot do novo jogo"):LOCTEXT("PickLoad","Escolha o save")).ToString(),14)];
   for(int32 Index=1;Index<=UMareSimulation::SlotCount;++Index){const FMareSlotInfo Info=S->SlotInfo(Index);
    Button(SlotLabel(Index,Info),[this,Index,bNew,bExists=Info.bExists](){
     if(!Controller.IsValid())return;
     if(!bNew){if(!Controller->MenuLoadSlot(Index))Fail();}
     else if(bExists){PendingSlot=Index;Show(EPage::Confirm);}
     else if(!Controller->MenuNewGame(Index))Fail();},bNew || Info.bExists);}
   Back();break;}
  case EPage::Confirm:
   Box->AddSlot().AutoHeight().Padding(0,0,0,10)[MareUI::Text(FText::Format(LOCTEXT("ConfirmText","Começar um novo jogo no slot {0}? O progresso atual desse slot fica guardado só como backup (.bak)."),PendingSlot).ToString(),13)];
   Button(LOCTEXT("ConfirmYes","Sim, começar do zero"),[this](){if(!Controller.IsValid() || !Controller->MenuNewGame(PendingSlot))Fail();},true);
   Button(LOCTEXT("ConfirmNo","Cancelar"),[this](){Show(EPage::New);},true);
   break;
  case EPage::Options:
   Box->AddSlot().AutoHeight().Padding(0,0,0,8)[MareUI::Text(LOCTEXT("OptionsTitle","Opções").ToString(),16)];
   if(Controller.IsValid())Box->AddSlot().AutoHeight()[Controller->MakeOptionsPanel()];
   Back();break;
  case EPage::Credits:
   Box->AddSlot().AutoHeight().Padding(0,0,0,8)[MareUI::Text(LOCTEXT("CreditsTitle","Créditos").ToString(),16)];
   Box->AddSlot().AutoHeight().Padding(0,0,0,8)[SNew(SBox).HeightOverride(320)[SNew(SMareFit).Name(TEXT("credits"))[MareUI::Text(LOCTEXT("CreditsText",
    "Maré Alta Resort — criado por Sergio.\n\n"
    "Feito na Unreal Engine 5.8.\n\n"
    "Modelos, texturas e sons de terceiros: quase tudo CC0 (domínio público) — Poly Haven, Quaternius, Kenney, ambientCG e outros. "
    "Fonte Nunito (SIL OFL 1.1). Ícones de game-icons.net (CC BY 3.0).\n\n"
    "A lista completa de fontes e licenças está no arquivo CREDITS.md que acompanha o jogo.\n\n"
    "Obrigado por jogar!").ToString(),12)]]];
   Back();break;
  }
  if(bTitleMode){
   // Title screen. 07/11: the logo and the menu in a column on the left, the living bay behind (AMareTitleCamera).
   // 08/11 (Sergio: "tela inicial em 2d", "use o canva para fazer algo bastante detalhado"): a detailed 2D painting of
   // the island fills the screen (title.json "art", cover-fitted) and the painted Canva logo ("logo_image") replaces the
   // text logo; while the art is up the 3D world is not drawn at all (AMareController::OpenMainMenu).
   FString Logo=TEXT("Coconut Simulator"),Sub=TEXT("Maré Alta Resort"),ArtPath,LogoPath;
   {FString Text;TSharedPtr<FJsonObject> T;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/title.json")));   // i18n:skip
    if(FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),T) && T.IsValid()){T->TryGetStringField(TEXT("logo"),Logo);T->TryGetStringField(TEXT("subtitle"),Sub);   // i18n:skip
     T->TryGetStringField(TEXT("art"),ArtPath);T->TryGetStringField(TEXT("logo_image"),LogoPath);}}   // i18n:skip
   const FSlateBrush* Art=TitleBrush(ArtPath);const FSlateBrush* LogoArt=TitleBrush(LogoPath);
   // red rubber stamp over the painted logo (the pale yellow one vanished against the sunset sky)
   const TSharedRef<SWidget> Stamp=S->IsDemo()?MareNotebook::Stamp(TEXT("DEMO"),LogoArt?MareNotebook::Hex(214,52,40):MareNotebook::Hex(255,236,150)):SNullWidget::NullWidget;
   auto Shadowed=[](const FString& V,float Size,const FLinearColor& C){return SNew(STextBlock).Text(FText::FromString(V)).Font(MareNotebook::Hand(Size)).ColorAndOpacity(C)
    .ShadowOffset(FVector2D(2.5f,2.5f)).ShadowColorAndOpacity(FLinearColor(0,0,0,.55f));};
   TSharedRef<SWidget> Head=SNullWidget::NullWidget;
   if(LogoArt){const FVector2D Size=LogoArt->ImageSize;const float W=520.f,H=W*Size.Y/FMath::Max(1.f,float(Size.X));
    Head=SNew(SOverlay)
     +SOverlay::Slot()[SNew(SBox).WidthOverride(W).HeightOverride(H)[SNew(SImage).Image(LogoArt)]]
     // the DEMO stamp pinned at the end of the logo's wooden sign
     +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom).Padding(0,0,-34,H*.05f)[SNew(SBox).RenderTransformPivot(FVector2D(.5f,.5f)).RenderTransform(FSlateRenderTransform(FQuat2D(FMath::DegreesToRadians(-8.f))))[Stamp]];}
   else Head=SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[Shadowed(Logo,78,MareNotebook::Hex(255,246,214))]
    +SVerticalBox::Slot().AutoHeight().Padding(6,-10,0,0)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Shadowed(Sub,30,MareNotebook::Hex(255,214,150))]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(18,0,0,0)[Stamp]];
   // a soft dark wash fading to the right (strips of falling opacity), so the column reads over the bright picture
   auto Wash=SNew(SHorizontalBox);
   // (fine strips: 12 wide ones showed as stripes over the painting)
   for(int32 K=0;K<56;++K)Wash->AddSlot().AutoWidth()[SNew(SBox).WidthOverride(15)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(0,0,0,(Art?.38f:.34f)*FMath::Square(1.f-K/56.f)))]];
   ChildSlot[SNew(SOverlay)
    +SOverlay::Slot()[Art?StaticCastSharedRef<SWidget>(SNew(SScaleBox).Stretch(EStretch::ScaleToFill)[SNew(SImage).Image(Art)]):SNullWidget::NullWidget]
    +SOverlay::Slot().HAlign(HAlign_Left)[Wash]
    +SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Fill).Padding(56,36,0,24)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight()[Head]
     +SVerticalBox::Slot().AutoHeight().Padding(LogoArt?60.f:24.f,LogoArt?4.f:40.f,0,0)[SNew(SBox).WidthOverride(Page==EPage::Options?560:400)[MareNotebook::Page(Box)]]]
    +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom).Padding(0,0,28,18)[Shadowed(LOCTEXT("TitleFoot","Demo · versão de teste").ToString(),18,FLinearColor(1,1,1,.85f))]];
  }
  else ChildSlot[SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.55f)).HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(Page==EPage::Options?540:440)[MareNotebook::Page(Box)]]];
  MareGamepad::FocusSoon(AsShared(),0);
 }
};
void AMareController::StartBusinessGame(const FString& Biz)
{
 auto S=GetSimulation();if(!GEngine || !GEngine->GameViewport || !S || GameWidget.IsValid())return;
 // 6.2: this business's own tip the first time, even when nobody is waiting yet; the generic one (the clerk at 60 %)
 // on a later visit.
 if(!S->ShowTip(TEXT("biz:")+Biz))S->ShowTip(TEXT("BusinessCounter"));
 FString Reason;if(!S->CanPlayBusiness(Biz,Reason)){S->LastMessage=Reason;return;}
 // Foosball (5.4): a real match on the table, rods turned by the mouse; it pays through PlayBusiness when it ends.
 if(Biz==TEXT("pebolim"))if(auto FB=GetWorld()->GetSubsystem<UMareFoosball>())if(FB->HasTable()){ClosePhone();
  const TArray<FString> Names=S->PoolPlayers();FB->StartMatch(this,Names.Num()?Names[FMath::RandRange(0,Names.Num()-1)]:FString());return;}
 // Arcades (5.4): the game is played on the cabinet's own screen; the token pays through PlayBusiness when it ends.
 if(Biz==TEXT("fliperama"))if(auto Arc=GetWorld()->GetSubsystem<UMareArcade>())if(Arc->Start(this)){ClosePhone();return;}
 ClosePhone();SetPause(true);
 // The ice cream shop has its own hands-on task (3.1): the cone built from memory, customer after customer.
 // The food truck too (3.2): fill, seal, fry and the sugar-cane juice.
 // The rental (3.3): check returned boards, wax and rent.
 if(Biz==TEXT("aluguel")){const TSharedRef<SMareRentalGame> Rent=SNew(SMareRentalGame).Owner(this);GameWidget=Rent;GRentalGame=Rent;
  GEngine->GameViewport->AddViewportWidgetContent(Rent,40);bShowMouseCursor=true;
  SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Rent));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);return;}
 // The souvenir shop (3.5): gift wrap, shelf and makers, postcards from the album.
 if(Biz==TEXT("souvenir")){const TSharedRef<SWidget> Shop=MareSouvenirGame::Make(this);GameWidget=Shop;
  GEngine->GameViewport->AddViewportWidgetContent(Shop,40);bShowMouseCursor=true;
  SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Shop));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);return;}
 if(Biz==TEXT("food_truck")){const TSharedRef<SMarePastelGame> Pastel=SNew(SMarePastelGame).Owner(this);GameWidget=Pastel;GPastelGame=Pastel;
  GEngine->GameViewport->AddViewportWidgetContent(Pastel,40);bShowMouseCursor=true;
  SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Pastel));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);return;}
 if(Biz==TEXT("sorveteria")){const TSharedRef<SMareIceCreamGame> Ice=SNew(SMareIceCreamGame).Owner(this);GameWidget=Ice;GIceGame=Ice;
  GEngine->GameViewport->AddViewportWidgetContent(Ice,40);bShowMouseCursor=true;
  SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Ice));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);return;}
 const TSharedRef<SMareTimingGame> Game=SNew(SMareTimingGame).Owner(this).Biz(Biz);GameWidget=Game;
 GEngine->GameViewport->AddViewportWidgetContent(Game,40);bShowMouseCursor=true;
 SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Game));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::CloseBusinessGame()
{
 if(GameWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(GameWidget.ToSharedRef());
 GameWidget.Reset();SetPause(false);bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
}
void AMareController::StartFishing()
{
 if(!GEngine || !GEngine->GameViewport || GameWidget.IsValid())return;
 ClosePhone();
 const TSharedRef<SMareFishingGame> Game=SNew(SMareFishingGame).Owner(this);GameWidget=Game;
 GEngine->GameViewport->AddViewportWidgetContent(Game,40);bShowMouseCursor=true;
 SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Game));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::StartBarPrep(const FString& Step)
{
 if(!GEngine || !GEngine->GameViewport || GameWidget.IsValid() || Step.IsEmpty())return;
 ClosePhone();
 const TSharedRef<SMareBarPrepGame> Game=SNew(SMareBarPrepGame).Owner(this).Step(Step);GameWidget=Game;
 GEngine->GameViewport->AddViewportWidgetContent(Game,40);bShowMouseCursor=true;
 SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Game));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
FString AMareController::RentalQA(const FString& Cmd)
{
 auto S=GetSimulation();auto W=GetWorld()->GetSubsystem<UMareRentalWorld>();if(!S || !W)return TEXT("none");
 if(Cmd==TEXT("own")){UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("biz")),TEXT("aluguel"))->SetNumberField(TEXT("lvl"),1);
  S->State->SetNumberField(TEXT("minutes"),10*60+10);return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("customers:"))){for(int32 I=0;I<FCString::Atoi(*Cmd.Mid(10));++I)S->AddRentalCustomer();return FString::Printf(TEXT("queue=%d"),S->RentalQueue().Num());}
 if(Cmd==TEXT("return:dent") || Cmd==TEXT("return:clean")){auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("name"),TEXT("Duda"));O->SetStringField(TEXT("item"),TEXT("prancha"));
  O->SetNumberField(TEXT("due"),1);O->SetBoolField(TEXT("dent"),Cmd==TEXT("return:dent"));auto R=S->RentalState();TArray<TSharedPtr<FJsonValue>> L;const TArray<TSharedPtr<FJsonValue>>* Old=nullptr;
  if(R->TryGetArrayField(TEXT("returns"),Old))L=*Old;L.Insert(MakeShared<FJsonValueObject>(O),0);R->SetArrayField(TEXT("returns"),L);return TEXT("ok");}
 if(Cmd==TEXT("open")){StartBusinessGame(TEXT("aluguel"));return GRentalGame.IsValid()?TEXT("open"):S->LastMessage;}
 if(Cmd==TEXT("adrift")){S->StartKayakAdrift();return TEXT("ok");}
 if(Cmd==TEXT("near") || Cmd==TEXT("tow") || Cmd==TEXT("home") || Cmd==TEXT("world"))return W->QA(Cmd);
 auto Game=GRentalGame.Pin();if(!Game.IsValid())return FString::Printf(TEXT("queue=%d returns=%d out=%d adrift=%d"),S->RentalQueue().Num(),S->RentalReturns().Num(),S->RentalOut().Num(),S->IsKayakAdrift());
 if(Cmd.StartsWith(TEXT("wax:"))){Game->QAWax(FCString::Atof(*Cmd.Mid(4)));return TEXT("ok");}
 if(Cmd==TEXT("left")){Game->QALeft();return S->LastMessage;}
 if(Cmd==TEXT("right")){Game->QARight();return S->LastMessage;}
 if(Cmd==TEXT("close")){CloseBusinessGame();return TEXT("ok");}
 return TEXT("?");
}
FString AMareController::SouvenirQA(const FString& Cmd)
{
 auto S=GetSimulation();if(!S)return TEXT("none");FString A,B;if(!Cmd.Split(TEXT(":"),&A,&B))A=Cmd;
 if(A==TEXT("own")){S->SouvenirState()->SetNumberField(TEXT("lvl"),1);S->State->SetNumberField(TEXT("minutes"),10*60+10);
  // The makers sell once their village story is done: the souvenir shop itself comes after the last one.
  for(const FString Id:{TEXT("pier"),TEXT("prainha"),TEXT("sabores"),TEXT("carnaval")})UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("ch"))->SetNumberField(Id,3);
  S->State->SetNumberField(TEXT("money"),FMath::Max(S->Money(),3000.));return TEXT("ok");}
 if(A==TEXT("gift")){const auto Crafts=S->SouvenirShelf();for(int32 I=0;I<FCString::Atoi(*B);++I)S->AddSouvenirGift(UMareSimulation::String(Crafts[I%2],TEXT("item")));return FString::Printf(TEXT("queue=%d"),S->SouvenirQueue().Num());}
 if(A==TEXT("open")){StartBusinessGame(TEXT("souvenir"));return MareSouvenirGame::IsOpen()?TEXT("open"):S->LastMessage;}
 if(A==TEXT("buy")){S->BuySouvenirCraft(B);return S->LastMessage;}
 if(A==TEXT("place")){FString Slot,Id;B.Split(TEXT(","),&Slot,&Id);S->PlaceSouvenir(FCString::Atoi(*Slot),Id);return S->LastMessage;}
 if(A==TEXT("hour")){const double Before=S->Money();const int32 H=FMath::FloorToInt(UMareSimulation::Number(S->State,TEXT("minutes"))/60)+1;
  for(int32 I=0;I<FMath::Max(1,FCString::Atoi(*B));++I)S->SouvenirHour(H);return FString::Printf(TEXT("sold=%.0f queue=%d"),S->Money()-Before,S->SouvenirQueue().Num());}
 if(A==TEXT("photo")){TakePhoto();return S->LastMessage;}
 if(A==TEXT("print")){const TArray<TSharedPtr<FJsonValue>>* Album=nullptr;UMareSimulation::Object(S->State,TEXT("prog"))->TryGetArrayField(TEXT("album"),Album);
  if(!Album || Album->IsEmpty())return TEXT("no photo");const auto P=Album->Last()->AsObject();const TArray<TSharedPtr<FJsonValue>>* Subs=nullptr;P->TryGetArrayField(TEXT("subjects"),Subs);
  S->PrintPostcards(UMareSimulation::String(P,TEXT("file")),Subs?Subs->Num():0);return S->LastMessage;}
 if(A==TEXT("state")){FString Out;for(const auto& Sl:S->SouvenirShelf())Out+=FString::Printf(TEXT("%s=%.0f "),*UMareSimulation::String(Sl,TEXT("item")),UMareSimulation::Number(Sl,TEXT("qty")));
  return Out+FString::Printf(TEXT("queue=%d cards=%d money=%.0f"),S->SouvenirQueue().Num(),S->SouvenirCards().Num(),S->Money());}
 if(A==TEXT("close")){CloseBusinessGame();return TEXT("ok");}
 return MareSouvenirGame::QA(Cmd);
}
FString AMareController::PastelQA(const FString& Cmd)
{
 auto S=GetSimulation();if(!S)return TEXT("none");
 if(Cmd==TEXT("own")){UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("biz")),TEXT("food_truck"))->SetNumberField(TEXT("lvl"),1);
  S->State->SetNumberField(TEXT("minutes"),14*60+10);return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("customers:"))){for(int32 I=0;I<FCString::Atoi(*Cmd.Mid(10));++I)S->AddPastelCustomer();return FString::Printf(TEXT("queue=%d"),S->PastelQueue().Num());}
 if(Cmd==TEXT("open")){StartBusinessGame(TEXT("food_truck"));return GPastelGame.IsValid()?TEXT("open"):S->LastMessage;}
 auto Game=GPastelGame.Pin();if(!Game.IsValid())return TEXT("no game");
 if(Cmd==TEXT("perfect") || Cmd==TEXT("wrong"))return Game->QAPerfect(Cmd==TEXT("perfect"));
 if(Cmd.Contains(TEXT(":"))){FString A,B;Cmd.Split(TEXT(":"),&A,&B);Game->QAStep(A,FCString::Atof(*B));return TEXT("ok");}
 if(Cmd==TEXT("close")){CloseBusinessGame();return TEXT("ok");}
 Game->QAStep(Cmd,0);return FString::Printf(TEXT("queue=%d"),S->PastelQueue().Num());
}
FString AMareController::IceCreamQA(const FString& Cmd)
{
 auto S=GetSimulation();if(!S)return TEXT("none");
 if(Cmd==TEXT("own")){UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"))->SetNumberField(TEXT("lvl"),1);
  S->State->SetNumberField(TEXT("minutes"),14*60+10);return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("customers:"))){for(int32 I=0;I<FCString::Atoi(*Cmd.Mid(10));++I)S->AddIceCustomer();return FString::Printf(TEXT("queue=%d"),S->IceQueue().Num());}
 if(Cmd==TEXT("open")){StartBusinessGame(TEXT("sorveteria"));return GIceGame.IsValid()?TEXT("open"):S->LastMessage;}
 auto Game=GIceGame.Pin();if(!Game.IsValid())return TEXT("no game");
 if(Cmd==TEXT("perfect") || Cmd==TEXT("wrong")){Game->QABuild(Cmd==TEXT("perfect"));Game->QADeliver();return S->LastMessage;}
 if(Cmd.StartsWith(TEXT("hold:"))){TArray<FString> P;Cmd.Mid(5).ParseIntoArray(P,TEXT(","));if(P.Num()==2)Game->QAHold(FCString::Atoi(*P[0]),FCString::Atof(*P[1]));return TEXT("ok");}
 if(Cmd==TEXT("release")){Game->QARelease();return TEXT("ok");}
 if(Cmd==TEXT("show")){Game->QAShowNow();return TEXT("ok");}
 if(Cmd==TEXT("close")){CloseBusinessGame();return TEXT("ok");}
 return FString::Printf(TEXT("queue=%d"),S->IceQueue().Num());
}
FString AMareController::ReefQA(const FString& Cmd){auto Reef=GetWorld()->GetSubsystem<UMareReefWorld>();return Reef?Reef->QA(Cmd):TEXT("none");}
FString AMareController::TrailQA(const FString& Cmd)
{
 auto S=GetSimulation();auto Tour=GetWorld()->GetSubsystem<UMareTrailWorld>();if(!S || !Tour)return TEXT("none");
 if(Cmd==TEXT("start")){const FString Id=UMareSimulation::String(UMareSimulation::Object(S->ToursDefs(),TEXT("trail_tour")),TEXT("tour"));
  const auto Def=S->TourDef(Id);if(!Def)return TEXT("no tour");
  S->State->SetNumberField(TEXT("minutes"),UMareSimulation::Number(Def,TEXT("hour"))*60+5);
  UMareSimulation::Object(S->Tours(),TEXT("done"))->RemoveField(Id);
  auto Sold=UMareSimulation::Object(S->Tours(),TEXT("sold"));if(UMareSimulation::Number(Sold,Id)<4)Sold->SetNumberField(Id,4);
  ClosePhone();return Tour->Start(this)?TEXT("started"):S->LastMessage;}
 return Tour->QA(Cmd);
}
FString AMareController::SnorkelQA(const FString& Cmd)
{
 auto S=GetSimulation();auto Tour=GetWorld()->GetSubsystem<UMareSnorkelWorld>();if(!S || !Tour)return TEXT("none");
 if(Cmd==TEXT("start")){const FString Id=UMareSimulation::String(UMareSimulation::Object(S->ToursDefs(),TEXT("snorkel_tour")),TEXT("tour"));
  const auto Def=S->TourDef(Id);if(!Def)return TEXT("no tour");
  S->State->SetNumberField(TEXT("minutes"),UMareSimulation::Number(Def,TEXT("hour"))*60+5);
  UMareSimulation::Object(S->Tours(),TEXT("done"))->RemoveField(Id);
  auto Sold=UMareSimulation::Object(S->Tours(),TEXT("sold"));if(UMareSimulation::Number(Sold,Id)<5)Sold->SetNumberField(Id,5);
  ClosePhone();return Tour->Start(this)?TEXT("started"):S->LastMessage;}
 return Tour->QA(Cmd);
}
FString AMareController::BoatTourQA(const FString& Cmd)
{
 auto S=GetSimulation();auto Tour=GetWorld()->GetSubsystem<UMareBoatTourWorld>();if(!S || !Tour)return TEXT("none");
 if(Cmd==TEXT("start")){const FString Id=UMareSimulation::String(UMareSimulation::Object(S->ToursDefs(),TEXT("boat_tour")),TEXT("tour"));
  const auto Def=S->TourDef(Id);if(!Def)return TEXT("no tour");
  S->State->SetNumberField(TEXT("minutes"),UMareSimulation::Number(Def,TEXT("hour"))*60+5);
  UMareSimulation::Object(S->Tours(),TEXT("done"))->RemoveField(Id);
  auto Sold=UMareSimulation::Object(S->Tours(),TEXT("sold"));if(UMareSimulation::Number(Sold,Id)<6)Sold->SetNumberField(Id,6);
  ClosePhone();return Tour->Start(this)?TEXT("started"):S->LastMessage;}
 return Tour->QA(Cmd);
}
void AMareController::UseBarGlass()
{
 auto S=GetSimulation();if(!S)return;
 if(!S->BarHand().IsEmpty()){const FString Hand=S->BarHand();
  if(S->BarPour())UMareAudioWorld::Action(this,Hand==TEXT("gelo")?TEXT("bar_ice_glass"):TEXT("bar_pour"),nullptr,.8f);return;}
 const FString Next=S->BarNextStep();
 if(!Next.IsEmpty()){StartBarPrep(Next);return;}
 if(S->BarGlass().IsEmpty()){S->LastMessage=TEXT("Pegue os ingredientes na bancada e coloque no copo.");return;}
 const auto Result=S->ServeGlass(S->BarServing());
 if(Result.bServed)UMareAudioWorld::Action(this,TEXT("money_coins"));
 if(Result.bDiscovered)UMareAudioWorld::Action(this,TEXT("deal_accept"));
 if(!Result.bServed && !Result.Recipe.IsEmpty())UMareAudioWorld::Action(this,TEXT("deal_decline"));
}
void AMareController::TakePhoto()
{
 // Photo mode: everything in frame (inside the view cone, close enough, not behind a wall) goes to the album.
 auto S=GetSimulation();if(!S || !PlayerCameraManager || IsPaused() || bPhoneOpen || GameWidget.IsValid() || IsMainMenuOpen())return;
 const FVector Eye=PlayerCameraManager->GetCameraLocation();const FVector Forward=PlayerCameraManager->GetCameraRotation().Vector();
 const float HalfFov=FMath::DegreesToRadians(PlayerCameraManager->GetFOVAngle()*.45f);
 TArray<FString> Subjects;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(S->LeisureDefs()->TryGetArrayField(TEXT("photo_subjects"),List))for(const auto& V:*List){const auto Sub=V->AsObject();const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
  // Sky subjects (the sunset): the low sun inside the frame, at the given hours (direction from the MareSun light).
  bool bSun=false;Sub->TryGetBoolField(TEXT("sun"),bSun);
  if(bSun){const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const double Hour=UMareSimulation::Number(S->State,TEXT("minutes"))/60;
   if(Sub->TryGetArrayField(TEXT("hours"),Hours) && Hours->Num()==2 && (Hour<(*Hours)[0]->AsNumber() || Hour>(*Hours)[1]->AsNumber()))continue;
   AActor* SunLight=nullptr;for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareSun"))){SunLight=*It;break;}
   if(!SunLight)continue;const FVector ToSun=-SunLight->GetActorForwardVector();
   if(FMath::RadiansToDegrees(FMath::Asin(ToSun.Z))>UMareSimulation::Number(Sub,TEXT("max_elevation"),18) ||
      FMath::RadiansToDegrees(FMath::Acos(FVector::DotProduct(ToSun,Forward)))>UMareSimulation::Number(Sub,TEXT("angle"),30))continue;
   Subjects.Add(UMareSimulation::String(Sub,TEXT("id")));continue;}
  if(!Sub->TryGetArrayField(TEXT("at"),At) || At->Num()!=3)continue;const FVector Point((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());
  const FVector To=Point-Eye;if(To.Size()>UMareSimulation::Number(Sub,TEXT("max"),5000) || FMath::Acos(FVector::DotProduct(To.GetSafeNormal(),Forward))>HalfFov)continue;
  FHitResult Hit;FCollisionQueryParams Query;Query.AddIgnoredActor(GetPawn());
  if(GetWorld()->LineTraceSingleByChannel(Hit,Eye,Point,ECC_Visibility,Query) && FVector::Dist(Hit.ImpactPoint,Point)>UMareSimulation::Number(Sub,TEXT("radius"),400))continue;
  Subjects.Add(UMareSimulation::String(Sub,TEXT("id")));}
 const FString File=FPaths::ProjectSavedDir()/TEXT("Album")/FString::Printf(TEXT("foto_dia%02d_%04.0f_%d.png"),int32(UMareSimulation::Number(S->State,TEXT("day"),1)),UMareSimulation::Number(S->State,TEXT("minutes")),int32(GFrameNumber%100000));
 FScreenshotRequest::RequestScreenshot(File,false,false);
 // The lighthouse trail: a photo at a viewpoint is the group photo of that stop.
 if(auto Trail=GetWorld()->GetSubsystem<UMareTrailWorld>())Trail->OnPhoto();
 S->RecordPhoto(Subjects,File);UMareAudioWorld::Action(this,TEXT("reception_checkin"),nullptr,.7f);S->ShowTip(TEXT("photo"));
}
void AMareController::ShowEndOfContent(bool bDebt)
{
 auto S=GetSimulation();if(!S || !GEngine || !GEngine->GameViewport || GameWidget.IsValid() || bPhoneOpen || IsMainMenuOpen())return;
 if(bDebt){if(!S->AckDebt())return;}else S->MarkEndOfContentShown();
 SetPause(true);
 const TSharedRef<SMareEndScreen> Screen=SNew(SMareEndScreen).Owner(this).Debt(bDebt);GameWidget=Screen;
 GEngine->GameViewport->AddViewportWidgetContent(Screen,45);bShowMouseCursor=true;
 SetInputMode(FInputModeUIOnly().SetWidgetToFocus(Screen));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
 UMareAudioWorld::Action(this,TEXT("deal_accept"));
}
void AMareController::OpenMainMenu()
{
 auto S=GetSimulation();if(!GEngine || !GEngine->GameViewport || !S || MainMenuWidget.IsValid())return;
 WorldSlot=S->ActiveSlot;bWorldFromFile=S->SlotInfo(WorldSlot).bExists;
 MareGamepad::Startup();
 // 07/11 (Sergio: "precisa ter uma tela inicial", "o menu inicial já é a tela do jogo"): at start-up (and back from the
 // pause menu) the menu is a title screen over a living bay at golden hour, seen by AMareTitleCamera; the clock and the
 // save stand still (AMareGameMode::Tick). In-game openings (credits after the debt finale) keep the pause.
 bTitle=!S->bMainMenuDone;
 if(bTitle){S->bTitleOpen=true;S->bHoldSaves=true;TitleSavedMinutes=UMareSimulation::Number(S->State,TEXT("minutes"));
  S->State->SetNumberField(TEXT("minutes"),AMareTitleCamera::TitleMinutes());
  FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  TitleCamera=GetWorld()->SpawnActor<AMareTitleCamera>(P);if(TitleCamera)SetViewTarget(TitleCamera);
  if(MareTitleHasArt())GEngine->GameViewport->bDisableWorldRendering=true;}   // the 2D title art covers the screen: draw nothing behind it
 else SetPause(true);
 {const TSharedRef<SMareMainMenu> Menu=SNew(SMareMainMenu).Controller(this);MainMenuWidget=Menu;const TWeakPtr<SMareMainMenu> Weak=Menu;
  MareGamepad::PushMenu(Menu,[Weak](){if(const auto Pinned=Weak.Pin())Pinned->Back();});}
 GEngine->GameViewport->AddViewportWidgetContent(MainMenuWidget.ToSharedRef(),50);bShowMouseCursor=true;
 SetInputMode(FInputModeUIOnly().SetWidgetToFocus(MainMenuWidget));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::OpenCredits()
{
 OpenMainMenu();if(MainMenuWidget.IsValid())StaticCastSharedPtr<SMareMainMenu>(MainMenuWidget)->ShowCredits();
}
void AMareController::CloseMainMenu()
{
 if(MainMenuWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(MainMenuWidget.ToSharedRef());
 MainMenuWidget.Reset();
 if(bTitle){bTitle=false;
  if(auto S=GetSimulation()){S->bTitleOpen=false;S->bHoldSaves=false;if(TitleSavedMinutes>=0)S->State->SetNumberField(TEXT("minutes"),TitleSavedMinutes);}
  TitleSavedMinutes=-1;
  if(IsValid(TitleCamera)){TitleCamera->Destroy();}TitleCamera=nullptr;
  if(GEngine && GEngine->GameViewport)GEngine->GameViewport->bDisableWorldRendering=false;
  if(GetPawn())SetViewTarget(GetPawn());}
}
void AMareController::ReloadWorld()
{
 // The old world must not write its actors into the newly selected state while it is torn down.
 if(auto S=GetSimulation()){S->bMainMenuDone=true;S->bHoldSaves=true;}
 CloseMainMenu();UGameplayStatics::OpenLevel(this,FName(*UGameplayStatics::GetCurrentLevelName(this,true)));
}
bool AMareController::MenuLoadSlot(int32 Slot)
{
 auto S=GetSimulation();if(!S)return false;
 if(Slot==WorldSlot && bWorldFromFile && S->ActiveSlot==Slot){
  S->bMainMenuDone=true;CloseMainMenu();SetPause(false);bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
  if(auto Mode=GetWorld()->GetAuthGameMode<AMareGameMode>())Mode->StartSession();
  return true;
 }
 if(!S->LoadSlot(Slot))return false;
 ReloadWorld();return true;
}
bool AMareController::MenuNewGame(int32 Slot)
{
 auto S=GetSimulation();if(!S)return false;
 // The world behind the menu already is a brand-new profile of this slot: just start the arrival.
 if(Slot==WorldSlot && !bWorldFromFile && !S->SlotInfo(Slot).bExists && S->ActiveSlot==Slot){
  S->bMainMenuDone=true;CloseMainMenu();SetPause(false);bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
  if(auto Mode=GetWorld()->GetAuthGameMode<AMareGameMode>())Mode->StartSession();
  return true;
 }
 if(!S->NewGame(Slot))return false;
 ReloadWorld();return true;
}
bool AMareController::ReloadActiveSlot()
{
 auto S=GetSimulation();if(!S || !S->LoadSlot(S->ActiveSlot))return false;
 ReloadWorld();return true;
}
void AMareController::ReturnToMainMenu()
{
 auto S=GetSimulation();if(!S)return;
 S->Save();S->bMainMenuDone=false;S->bHoldSaves=true;
 if(PauseWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();
 UGameplayStatics::OpenLevel(this,FName(*UGameplayStatics::GetCurrentLevelName(this,true)));
}
/** Options in tabs: edits a pending copy until "Aplicar" (audio sliders act at once). */
class SMareOptions : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareOptions){} SLATE_ARGUMENT(AMareController*,Controller) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  Controller=Args._Controller;Pending=FMareOptions::Get();
  TArray<FIntPoint> Supported;UKismetSystemLibrary::GetSupportedFullscreenResolutions(Supported);
  for(const FIntPoint& Size:Supported)if(Size.X>=1024 && Size.Y>=576)Resolutions.AddUnique(Size);
  if(Resolutions.IsEmpty())Resolutions={FIntPoint(1280,720),FIntPoint(1600,900),FIntPoint(1920,1080),FIntPoint(2560,1440),FIntPoint(3840,2160)};
  Resolutions.AddUnique(Pending.Resolution);
  Resolutions.Sort([](const FIntPoint& A,const FIntPoint& B){return A.X*A.Y!=B.X*B.Y?A.X*A.Y<B.X*B.Y:A.X<B.X;});
  Rebuild();
 }
 // Closing the menu while a new video mode is unconfirmed goes back to the previous one.
 virtual ~SMareOptions() override{if(RevertAt>0 && GEngine && !IsEngineExitRequested())Revert();}
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override
 {
  const FKey Pressed=Event.GetKey();
  // LB/RB change the tab; a gamepad button while waiting for a key cancels it (the gamepad layout is fixed).
  if(Listening.IsNone() && (Pressed==EKeys::Gamepad_LeftShoulder || Pressed==EKeys::Gamepad_RightShoulder)){
   Tab=(Tab+(Pressed==EKeys::Gamepad_RightShoulder?1:4))%5;Rebuild();MareGamepad::FocusSoon(AsShared(),Tab,false);return FReply::Handled();}
  if(Listening.IsNone())return FReply::Unhandled();
  if(Pressed.IsGamepadKey()){Listening=NAME_None;return FReply::Handled();}
  if(Pressed!=EKeys::Escape)Pending.Bind(Listening,Pressed);
  Listening=NAME_None;return FReply::Handled();
 }
 virtual FReply OnMouseButtonDown(const FGeometry& Geometry,const FPointerEvent& Event) override
 {
  if(Listening.IsNone())return FReply::Unhandled();
  if(Event.GetEffectingButton()!=EKeys::LeftMouseButton)Pending.Bind(Listening,Event.GetEffectingButton());
  Listening=NAME_None;return FReply::Handled();
 }
private:
 TWeakObjectPtr<AMareController> Controller;
 FMareOptions Pending;
 int32 Tab=0;
 FName Listening;
 double RevertAt=0;   // > 0 while a new resolution waits for confirmation
 TArray<FIntPoint> Resolutions;
 FText Status;
 static FLinearColor Ink(){return MareNotebook::Ink;}
 static const FButtonStyle& Light(){return MareNotebook::TagButton();}
 static FText Level(int32 Value)
 {
  static const FText Names[]={LOCTEXT("OptLow","Baixo"),LOCTEXT("OptMedium","Médio"),LOCTEXT("OptHigh","Alto"),LOCTEXT("OptEpic","Épico")};
  return Names[FMath::Clamp(Value,0,3)];
 }
 static FText OnOff(bool bOn){return bOn?LOCTEXT("OptOn","Ligado"):LOCTEXT("OptOff","Desligado");}
 UMareAudioWorld* Audio()const{return Controller.IsValid()?Controller->GetWorld()->GetSubsystem<UMareAudioWorld>():nullptr;}
 TSharedRef<SWidget> Button(const FText& Label,TFunction<void()> Callback,bool bMain=true)
 {
  return SNew(SMarePadButton).ButtonStyle(bMain?&MareUI::ActionButton:&Light()).ContentPadding(FMargin(12,6)).IsFocusable(true).OnClicked_Lambda([Callback](){Callback();return FReply::Handled();})
   [MareUI::Text(Label.ToString(),13,bMain?FLinearColor::White:Ink())];
 }
 /** Label, "<" value ">"; Step receives -1 or +1. */
 TSharedRef<SWidget> Row(const FText& Label,TFunction<FText()> Value,TFunction<void(int32)> Step)
 {
  auto Arrow=[Step](const TCHAR* Glyph,int32 Direction){return SNew(SMarePadButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(9,2)).IsFocusable(true)
   .OnClicked_Lambda([Step,Direction](){Step(Direction);return FReply::Handled();})[MareUI::Text(Glyph,13,FLinearColor::White)];};
  return SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(SBox).WidthOverride(180)[MareUI::Text(Label.ToString(),12)]]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Arrow(TEXT("<"),-1)]
   +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center).HAlign(HAlign_Center).Padding(6,0)
    [SNew(STextBlock).Text_Lambda([Value](){return Value();}).Font(MareNotebook::Body(12,true)).ColorAndOpacity(Ink())]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Arrow(TEXT(">"),1)];
 }
 void GraphicsPage(const TSharedRef<SVerticalBox>& Page)
 {
  auto Add=[&Page](TSharedRef<SWidget> Widget){Page->AddSlot().AutoHeight().Padding(0,3)[Widget];};
  Add(Row(LOCTEXT("OptPreset","Predefinição"),[this](){return Pending.IsCustomPreset()?FText::Format(LOCTEXT("OptCustom","Personalizado ({0})"),Level(Pending.Preset)):Level(Pending.Preset);},
   [this](int32 Step){Pending.SetPreset(FMath::Clamp(Pending.Preset+Step,0,3));}));
  const TPair<FText,int32 FMareOptions::*> Groups[]={{LOCTEXT("OptShadows","Sombras"),&FMareOptions::Shadows},{LOCTEXT("OptGI","Iluminação global (Lumen)"),&FMareOptions::GlobalIllumination},
   {LOCTEXT("OptReflections","Reflexos"),&FMareOptions::Reflections},{LOCTEXT("OptPost","Pós-processamento"),&FMareOptions::PostProcess},{LOCTEXT("OptTextures","Texturas"),&FMareOptions::Textures},
   {LOCTEXT("OptFoliage","Folhagem"),&FMareOptions::Foliage},{LOCTEXT("OptAA","Anti-serrilhado"),&FMareOptions::AntiAliasing},
   {LOCTEXT("OptViewDistance","Distância de visão"),&FMareOptions::ViewDistance},{LOCTEXT("OptModelDetail","Detalhe dos modelos"),&FMareOptions::ModelDetail},
   {LOCTEXT("OptEffects","Efeitos"),&FMareOptions::Effects},{LOCTEXT("OptShading","Sombreamento"),&FMareOptions::Shading}};
  for(const auto& Group:Groups){int32 FMareOptions::*Field=Group.Value;
   Add(Row(Group.Key,[this,Field](){return Level(Pending.*Field);},[this,Field](int32 Step){Pending.*Field=FMath::Clamp(Pending.*Field+Step,0,3);}));}
  Add(Row(LOCTEXT("OptCrowd","Pessoas nas cenas"),[this](){return Pending.Crowd==0?LOCTEXT("OptCrowdFew","Poucas"):Pending.Crowd==2?LOCTEXT("OptCrowdMany","Muitas"):LOCTEXT("OptCrowdNormal","Normal");},
   [this](int32 Step){Pending.Crowd=FMath::Clamp(Pending.Crowd+Step,0,2);}));
  Add(Row(LOCTEXT("OptScale","Escala 3D"),[this](){return MareLoc::Text(FString::Printf(TEXT("%.0f%%"),Pending.ResolutionScale));},
   [this](int32 Step){Pending.ResolutionScale=FMath::Clamp(Pending.ResolutionScale+5.f*Step,50.f,100.f);}));
  Add(Row(LOCTEXT("OptUpscaler","Upscaler"),[this](){return MareLoc::Text(Pending.Upscaler);},[this](int32 Step){const TArray<FString> List=FMareOptions::Upscalers();
   const int32 Index=FMath::Max(0,List.IndexOfByKey(Pending.Upscaler));Pending.Upscaler=List[(Index+Step+List.Num())%List.Num()];}));
  // NVIDIA DLSS Frame Generation: only offered on a card and driver that support it (RTX 40 and later).
  if(FMareOptions::FrameGenerationSupported())
   Add(Row(LOCTEXT("OptFrameGen","Geração de quadros (DLSS)"),[this](){return Pending.FrameGeneration==1?LOCTEXT("OptFrameGenOn","Ligada"):Pending.FrameGeneration==2?LOCTEXT("OptFrameGenAuto","Automática"):LOCTEXT("OptFrameGenOff","Desligada");},
    [this](int32 Step){Pending.FrameGeneration=(Pending.FrameGeneration+Step+3)%3;}));
 }
 void DisplayPage(const TSharedRef<SVerticalBox>& Page)
 {
  auto Add=[&Page](TSharedRef<SWidget> Widget){Page->AddSlot().AutoHeight().Padding(0,3)[Widget];};
  Add(Row(LOCTEXT("OptResolution","Resolução"),[this](){return Pending.WindowMode==1?LOCTEXT("OptDesktopRes","igual à área de trabalho"):MareLoc::Text(FString::Printf(TEXT("%d x %d"),Pending.Resolution.X,Pending.Resolution.Y));},
   [this](int32 Step){if(Pending.WindowMode==1)return;const int32 Index=Resolutions.IndexOfByKey(Pending.Resolution);Pending.Resolution=Resolutions[FMath::Clamp(Index<0?0:Index+Step,0,Resolutions.Num()-1)];}));
  Add(Row(LOCTEXT("OptWindow","Modo de exibição"),[this](){return Pending.WindowMode==0?LOCTEXT("OptFullscreen","Tela cheia"):Pending.WindowMode==1?LOCTEXT("OptBorderless","Tela cheia sem bordas"):LOCTEXT("OptWindowed","Janela");},
   [this](int32 Step){Pending.WindowMode=(Pending.WindowMode+Step+3)%3;}));
  Add(Row(LOCTEXT("OptVSync","VSync"),[this](){return OnOff(Pending.bVSync);},[this](int32){Pending.bVSync=!Pending.bVSync;}));
  Add(Row(LOCTEXT("OptFPS","Limite de FPS"),[this](){return Pending.FrameLimit>0?FText::AsNumber(Pending.FrameLimit):LOCTEXT("OptUnlimited","Ilimitado");},
   [this](int32 Step){const auto& List=FMareOptions::FrameLimits();const int32 Index=FMath::Max(0,List.IndexOfByKey(Pending.FrameLimit));Pending.FrameLimit=List[(Index+Step+List.Num())%List.Num()];}));
  Add(Row(LOCTEXT("OptFOV","Campo de visão"),[this](){return MareLoc::Text(FString::Printf(TEXT("%.0f°"),Pending.FieldOfView));},
   [this](int32 Step){Pending.FieldOfView=FMath::Clamp(Pending.FieldOfView+5.f*Step,70.f,110.f);}));
  Add(Row(LOCTEXT("OptTextScale","Tamanho da interface e do texto"),[this](){return MareLoc::Text(FString::Printf(TEXT("%.0f%%"),Pending.TextScale*100.f));},
   [this](int32 Step){Pending.TextScale=FMath::Clamp(FMath::RoundToFloat((Pending.TextScale+.05f*Step)*20.f)/20.f,.85f,1.5f);}));
  Add(Row(LOCTEXT("OptTips","Dicas do tutorial"),[this](){return OnOff(Pending.bTips);},[this](int32){Pending.bTips=!Pending.bTips;}));
  Add(Row(LOCTEXT("OptColorSafe","Modo para daltonismo (+/- nas variações)"),[this](){return OnOff(Pending.bColorSafe);},[this](int32){Pending.bColorSafe=!Pending.bColorSafe;}));
 }
 void AudioPage(const TSharedRef<SVerticalBox>& Page)
 {
  auto Sound=Audio();if(!Sound)return;
  const FName Buses[]={TEXT("Master"),TEXT("Music"),TEXT("Effects"),TEXT("Ambient")};
  const FText Labels[]={LOCTEXT("VolumeMaster","Volume geral"),LOCTEXT("VolumeMusic","Música"),LOCTEXT("VolumeEffects","Efeitos"),LOCTEXT("VolumeAmbient","Ambiente")};
  TWeakObjectPtr<UMareAudioWorld> Weak(Sound);
  for(int32 I=0;I<4;++I){const FName Bus=Buses[I];Page->AddSlot().AutoHeight().Padding(0,6)[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,12,0)[SNew(SBox).WidthOverride(130)[MareUI::Text(Labels[I].ToString(),12)]]
   +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[SNew(SSlider).IsFocusable(true).Value_Lambda([Weak,Bus](){return Weak.IsValid()?Weak->GetVolume(Bus):0.f;})
    .OnValueChanged_Lambda([Weak,Bus](float Value){if(Weak.IsValid())Weak->SetVolume(Bus,Value);})]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8,0,0,0)[SNew(SBox).WidthOverride(40)[SNew(STextBlock).ColorAndOpacity(Ink())
    .Text_Lambda([Weak,Bus](){return MareLoc::Text(FString::Printf(TEXT("%.0f%%"),Weak.IsValid()?Weak->GetVolume(Bus)*100.f:0.f));})]]];}
 }
 void ControlsPage(const TSharedRef<SVerticalBox>& Page)
 {
  auto Add=[&Page](TSharedRef<SWidget> Widget){Page->AddSlot().AutoHeight().Padding(0,3)[Widget];};
  Add(Row(LOCTEXT("OptSensitivity","Sensibilidade do mouse"),[this](){return MareLoc::Text(FString::Printf(TEXT("%.1f"),Pending.MouseSensitivity));},
   [this](int32 Step){Pending.MouseSensitivity=FMath::Clamp(FMath::RoundToFloat((Pending.MouseSensitivity+.1f*Step)*10.f)/10.f,.2f,3.f);}));
  Add(Row(LOCTEXT("OptInvertY","Inverter eixo Y"),[this](){return OnOff(Pending.bInvertY);},[this](int32){Pending.bInvertY=!Pending.bInvertY;}));
  Add(Row(LOCTEXT("OptPadSensitivity","Sensibilidade do controle"),[this](){return MareLoc::Text(FString::Printf(TEXT("%.1f"),Pending.GamepadSensitivity));},
   [this](int32 Step){Pending.GamepadSensitivity=FMath::Clamp(FMath::RoundToFloat((Pending.GamepadSensitivity+.1f*Step)*10.f)/10.f,.2f,3.f);}));
  Add(Row(LOCTEXT("OptPadGlyphs","Botões do controle"),[this](){return Pending.PadGlyphs==1?LOCTEXT("OptPadPlayStation","PlayStation"):LOCTEXT("OptPadXbox","Xbox");},
   [this](int32){Pending.PadGlyphs=1-Pending.PadGlyphs;}));
  Page->AddSlot().AutoHeight().Padding(0,10,0,4)[MareUI::Text(LOCTEXT("OptKeysHint","Clique numa ação e aperte a nova tecla (Esc cancela). Se a tecla já estiver em uso, as duas ações trocam.").ToString(),11)];
  for(const auto& Action:FMareOptions::Actions()){const FName Id=Action.Id;
   Page->AddSlot().AutoHeight().Padding(0,2)[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(SBox).WidthOverride(180)[MareUI::Text(Action.Label.ToString(),12)]]
    +SHorizontalBox::Slot().FillWidth(1)[SNew(SMarePadButton).ButtonStyle(&Light()).HAlign(HAlign_Center).ContentPadding(FMargin(8,4)).IsFocusable(true)
     .OnClicked_Lambda([this,Id](){Listening=Id;FSlateApplication::Get().SetKeyboardFocus(SharedThis(this),EFocusCause::SetDirectly);return FReply::Handled();})
     [SNew(STextBlock).Font(MareNotebook::Body(12,true)).ColorAndOpacity(Ink())
      .Text_Lambda([this,Id](){return Listening==Id?LOCTEXT("OptPressKey","aperte uma tecla..."):Pending.Key(Id).GetDisplayName();})]]];}
  // Fixed gamepad layout, named in the chosen style.
  const bool bPlayStation=Pending.PadGlyphs==1;
  auto Pad=[bPlayStation](const FKey& Key){return MareLoc::Text(MareGamepad::PadLabel(Key,bPlayStation));};
  FFormatNamedArguments Names;
  Names.Add(TEXT("Jump"),Pad(EKeys::Gamepad_FaceButton_Bottom));Names.Add(TEXT("Dive"),Pad(EKeys::Gamepad_FaceButton_Right));
  Names.Add(TEXT("Interact"),Pad(EKeys::Gamepad_FaceButton_Left));Names.Add(TEXT("Phone"),Pad(EKeys::Gamepad_FaceButton_Top));
  Names.Add(TEXT("View"),Pad(EKeys::Gamepad_Special_Left));Names.Add(TEXT("Start"),Pad(EKeys::Gamepad_Special_Right));
  Names.Add(TEXT("LT"),Pad(EKeys::Gamepad_LeftTrigger));Names.Add(TEXT("RT"),Pad(EKeys::Gamepad_RightTrigger));Names.Add(TEXT("L3"),Pad(EKeys::Gamepad_LeftThumbstick));
  Names.Add(TEXT("LB"),Pad(EKeys::Gamepad_LeftShoulder));Names.Add(TEXT("RB"),Pad(EKeys::Gamepad_RightShoulder));
  Page->AddSlot().AutoHeight().Padding(0,12,0,2)[MareUI::Text(LOCTEXT("OptPadTitle","Controle (Xbox / PlayStation)").ToString(),13)];
  Page->AddSlot().AutoHeight()[MareUI::Text(FText::Format(LOCTEXT("OptPadMap",
   "Analógico esquerdo: andar · analógico direito: olhar\n{Jump}: pular / subir nadando · {Dive}: mergulhar\n{Interact}: interagir · {Phone} ou {View}: celular · {Start}: pausa\n"
   "{LT} (segurar) ou {L3} (alternar): correr\nMenus: direcional ou analógico escolhe, {Jump} confirma, {Dive} volta, {LB}/{RB} trocam as abas\n"
   "Sinuca: analógico mira, segure {RT} para dar força e solte para tacar, {Dive} sai"),Names).ToString(),11)];
 }
 void LanguagePage(const TSharedRef<SVerticalBox>& Page)
 {
  Page->AddSlot().AutoHeight().Padding(0,3)[Row(LOCTEXT("OptLanguage","Idioma"),[this](){return FMareOptions::CultureName(Pending.Culture);},[this](int32 Step){const auto& List=FMareOptions::Cultures();
   const int32 Index=FMath::Max(0,List.IndexOfByKey(Pending.Culture));Pending.Culture=List[(Index+Step+List.Num())%List.Num()];})];
  Page->AddSlot().AutoHeight().Padding(0,10,0,0)[MareUI::Text(LOCTEXT("OptLanguageHint","A tradução para o inglês ainda está sendo feita: alguns textos podem continuar em português.").ToString(),11)];
 }
 void Rebuild()
 {
  const int32 PrevFocus=MareGamepad::FocusedIndex(AsShared());
  auto Body=SNew(SVerticalBox);auto Tabs=SNew(SHorizontalBox);
  const FText Names[]={LOCTEXT("OptTabGraphics","Gráficos"),LOCTEXT("OptTabDisplay","Tela"),LOCTEXT("OptTabAudio","Áudio"),LOCTEXT("OptTabControls","Controles"),LOCTEXT("OptTabLanguage","Idioma")};
  for(int32 I=0;I<5;++I)Tabs->AddSlot().FillWidth(1).Padding(I?3:0,0,0,0)[SNew(SMarePadButton).ButtonStyle(I==Tab?&MareUI::ActionButton:&Light()).HAlign(HAlign_Center).ContentPadding(FMargin(4,6)).IsFocusable(true)
   .OnClicked_Lambda([this,I](){Tab=I;Listening=NAME_None;Rebuild();return FReply::Handled();})[SNew(STextBlock).Text(Names[I]).Font(MareNotebook::Hand(16)).ColorAndOpacity(I==Tab?MareNotebook::Tag:Ink())]];
  Body->AddSlot().AutoHeight().Padding(0,0,0,10)[Tabs];
  auto Page=SNew(SVerticalBox);
  switch(Tab){case 0:GraphicsPage(Page);break;case 1:DisplayPage(Page);break;case 2:AudioPage(Page);break;case 3:ControlsPage(Page);break;default:LanguagePage(Page);}
  // Scrolls (wheel or bar): 04/11 the graphics page grew to 17 rows and the notebook leaf packing (SMareFit) left the
  // last six clipped below the box with no pager.
  Body->AddSlot().AutoHeight()[SNew(SBox).HeightOverride(380)[SNew(SScrollBox).ScrollBarAlwaysVisible(true)+SScrollBox::Slot().Padding(0,0,8,0)[Page]]];
  // Apply / defaults, or the 10 s confirmation after a resolution change.
  Body->AddSlot().AutoHeight().Padding(0,12,0,0)[SNew(SBox).Visibility_Lambda([this](){return RevertAt>0?EVisibility::Collapsed:EVisibility::Visible;})[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(LOCTEXT("OptApply","Aplicar"),[this](){Apply();})]
   +SHorizontalBox::Slot().AutoWidth()[Button(LOCTEXT("OptDefaults","Restaurar padrão"),[this](){RestoreDefaults();},false)]]];
  Body->AddSlot().AutoHeight().Padding(0,12,0,0)[SNew(SBox).Visibility_Lambda([this](){return RevertAt>0?EVisibility::Visible:EVisibility::Collapsed;})[SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[SNew(STextBlock).AutoWrapText(true).Font(MareNotebook::Body(12,true)).ColorAndOpacity(Ink())
    .Text_Lambda([this](){return FText::Format(LOCTEXT("OptKeepVideo","Manter este modo de tela? Volta ao anterior em {0} s."),FMath::Max(0,FMath::CeilToInt(RevertAt-FPlatformTime::Seconds())));})]
   +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().Padding(0,0,8,0)[Button(LOCTEXT("OptKeep","Manter"),[this](){Confirm();})]
    +SHorizontalBox::Slot().AutoWidth()[Button(LOCTEXT("OptRevert","Reverter"),[this](){Revert();},false)]]]];
  Body->AddSlot().AutoHeight().Padding(0,8,0,0)[SNew(STextBlock).AutoWrapText(true).Font(MareNotebook::Hand(15)).ColorAndOpacity(MareNotebook::Green).Text_Lambda([this](){return Status;})];
  ChildSlot[Body];
  if(PrevFocus>=0)MareGamepad::FocusSoon(AsShared(),PrevFocus);
 }
 void Apply()
 {
  if(RevertAt>0)return;
  Listening=NAME_None;Pending.Sanitize();FMareOptions::Set(Pending);
  Pending.ApplyGraphics();Pending.ApplyCulture();
  if(Controller.IsValid())for(auto It=Controller->GetWorld()->GetPlayerControllerIterator();It;++It)Pending.ApplyToPlayer(It->Get());
  if(Pending.ApplyDisplay()){RevertAt=FPlatformTime::Seconds()+10;Status=FText::GetEmpty();RegisterActiveTimer(.25f,FWidgetActiveTimerDelegate::CreateSP(this,&SMareOptions::Countdown));}
  else Status=LOCTEXT("OptApplied","Configurações aplicadas.");
 }
 EActiveTimerReturnType Countdown(double,float)
 {
  if(RevertAt<=0)return EActiveTimerReturnType::Stop;
  if(FPlatformTime::Seconds()<RevertAt)return EActiveTimerReturnType::Continue;
  Revert();return EActiveTimerReturnType::Stop;
 }
 void Confirm()
 {
  RevertAt=0;if(auto Settings=UGameUserSettings::GetGameUserSettings()){Settings->ConfirmVideoMode();Settings->SaveSettings();}
  Status=LOCTEXT("OptApplied","Configurações aplicadas.");
 }
 void Revert()
 {
  RevertAt=0;auto Settings=UGameUserSettings::GetGameUserSettings();if(!Settings)return;
  Settings->RevertVideoMode();Settings->ApplyResolutionSettings(false);Settings->SaveSettings();
  FMareOptions Live=FMareOptions::Get();Live.Resolution=Settings->GetScreenResolution();Live.WindowMode=Settings->GetFullscreenMode();FMareOptions::Set(Live);
  Pending.Resolution=FMareOptions::Get().Resolution;Pending.WindowMode=FMareOptions::Get().WindowMode;
  Status=LOCTEXT("OptReverted","O modo de tela anterior foi restaurado.");
 }
 void RestoreDefaults()
 {
  Listening=NAME_None;Pending=FMareOptions::Defaults();
  if(auto Sound=Audio())for(const FName Bus:{FName(TEXT("Master")),FName(TEXT("Music")),FName(TEXT("Effects")),FName(TEXT("Ambient"))})Sound->SetVolume(Bus,UMareAudioWorld::DefaultVolume(Bus));
  Status=LOCTEXT("OptDefaultsLoaded","Valores padrão carregados (o áudio já mudou). Clique em Aplicar para usar o resto.");
 }
};
TSharedRef<SWidget> AMareController::MakeOptionsPanel(){return SNew(SMareOptions).Controller(this);}
void AMareController::SetupInputComponent()
{
 Super::SetupInputComponent();InputComponent->BindAction(TEXT("Pause"),IE_Pressed,this,&AMareController::TogglePauseMenu).bExecuteWhenPaused=true;
 InputComponent->BindKey(EKeys::P,IE_Pressed,this,&AMareController::TakePhoto);InputComponent->BindKey(EKeys::Gamepad_DPad_Down,IE_Pressed,this,&AMareController::TakePhoto);
 MareGamepad::Startup();
 FMareOptions::Get().ApplyKeys(PlayerInput);
}
void AMareController::OnPossess(APawn* InPawn){Super::OnPossess(InPawn);FMareOptions::Get().ApplyToPlayer(this);}
void AMareController::TogglePauseMenu()
{
 if(MainMenuWidget.IsValid())return;
 if(auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>())if(Village->IsDialogueOpen()){Village->CloseDialogue();return;}
 for(TActorIterator<AMareIntro> It(GetWorld());It;++It)if(It->IsLetterOpen()){It->CloseLetter();return;}else if(It->IsArrival()){It->FinishArrival();return;}
 if(bPhoneOpen){ClosePhone();return;}
 if(!GEngine || !GEngine->GameViewport)return;
 if(PauseWidget.IsValid()){
  GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();SetPause(false);
  bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();return;
 }
 SetPause(true);BuildPauseMenu(false);bShowMouseCursor=true;
 SetInputMode(FInputModeGameAndUI());SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
// QA: opens a panel for the screenshot sweep of the UI ("mare.ShowUI pause|options|menu|letter").
struct FMareUIQA
{
 static void Show(UWorld* World,const FString& What)
 {
  auto PC=World?Cast<AMareController>(UGameplayStatics::GetPlayerController(World,0)):nullptr;if(!PC)return;
  if(What==TEXT("pause") || What==TEXT("options")){if(!PC->PauseWidget.IsValid())PC->TogglePauseMenu();PC->BuildPauseMenu(What==TEXT("options"));}
  else if(What==TEXT("menu"))PC->OpenMainMenu();
  else if(What.StartsWith(TEXT("phone")))PC->OpenPhone(FCString::Atoi(*What.RightChop(5)));   // "phone4" = Resort tab
  else if(What==TEXT("play")){   // QA gate in PIE: like Continue on the main menu (the paused menu kept the village from ever spawning)
   if(PC->IsMainMenuOpen() && !PC->MenuLoadSlot(PC->WorldSlot))PC->MenuNewGame(PC->WorldSlot);}
  else if(What==TEXT("close")){   // like E: ends the bus arrival, closes the letter, the pause menu
   for(TActorIterator<AMareIntro> It(World);It;++It){if(It->IsLetterOpen())It->CloseLetter();else if(It->IsArrival())It->FinishArrival();}
   // 06/11: the end-of-Early-Access screen (shows once everything is bought) pauses the game: every night photo of the
   // light audit came out identical, frozen at the house door. Close it (and any open minigame) like "Continuar jogando".
   if(PC->GameWidget.IsValid())PC->CloseBusinessGame();
   if(PC->PauseWidget.IsValid())PC->TogglePauseMenu();}
  else if(What==TEXT("letter")){AMareIntro* Intro=nullptr;for(TActorIterator<AMareIntro> It(World);It;++It){Intro=*It;break;}
   // Old QA saves have no intro stage and the intro actor removes itself: mark the letter as read (it stays readable).
   if(!Intro){if(auto Sim=PC->GetSimulation())if(!Sim->State->HasField(TEXT("ue_intro_stage")))Sim->State->SetNumberField(TEXT("ue_intro_stage"),2);Intro=World->SpawnActor<AMareIntro>();}
   if(Intro)Intro->ReadLetter();}
 }
};
// QA: screenshot with the UI after N real seconds (works while paused, e.g. "mare.ShowUI options, mare.ShotLater 4":
// a shot taken the same frame the menu opens comes before the notebook pages are laid out, 04/11).
// 06/11: "shot showui" wrote no file while the editor window was minimized: a shot with the UI is Slate grabbing the
// window's own back buffer, which is not drawn when minimized, and the request is dropped without a log line (HighResShot
// reads the scene and still worked). Restore the window first and ask for the shot a moment later.
static void MareShotWithUI(float Delay,const FString& File)
{
 if(FSlateApplication::IsInitialized() && GEngine && GEngine->GameViewport){
  const TSharedPtr<SWindow> Window=GEngine->GameViewport->GetWindow();
  if(Window.IsValid() && Window->IsWindowMinimized()){
   Window->Restore();Delay=FMath::Max(Delay,1.f);
   UE_LOG(LogTemp,Display,TEXT("mare.Shot: the window was minimized; restored it for the UI screenshot"));}
 }
 FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([File](float){
  FScreenshotRequest::RequestScreenshot(File,true,File.IsEmpty());return false;}),FMath::Max(Delay,.1f));
}
static FAutoConsoleCommand MareShotLaterCommand(TEXT("mare.ShotLater"),TEXT("QA: screenshot with the UI after N seconds (Saved/Screenshots)."),
 FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args){MareShotWithUI(Args.Num()?FCString::Atof(*Args[0]):3.f,FString());}));
// QA: screenshot with the UI that also works with the editor minimized ("mare.Shot [D:/path/file.png]"); use it instead of "shot showui".
static FAutoConsoleCommand MareShotCommand(TEXT("mare.Shot"),TEXT("QA: screenshot with the UI, restoring a minimized editor window first (optional file path)."),
 FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args){MareShotWithUI(.1f,Args.Num()?Args[0]:FString());}));
// QA (test profiles only): buys N of every stock item, so the kiosk cycle can be exercised from a drained save.
static FAutoConsoleCommandWithWorldAndArgs MareRestockCommand(TEXT("mare.Restock"),TEXT("QA: buys N of every stock item (QA save profile only)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  FString Profile;FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Profile);Profile.ReplaceInline(TEXT("\\"),TEXT("/"));
  auto PC=World?Cast<AMareController>(UGameplayStatics::GetPlayerController(World,0)):nullptr;auto S=PC?PC->GetSimulation():nullptr;
  if(!S || !Profile.StartsWith(TEXT("D:/CodexTemp/")))return;const int32 N=Args.Num()?FCString::Atoi(*Args[0]):20;
  TArray<FString> Items;for(const auto& Pair:UMareSimulation::Object(S->State,TEXT("stock"))->Values)Items.Add(FString(Pair.Key.ToView()));
  for(const FString& Item:Items)S->BuySupply(Item,N);
  UE_LOG(LogTemp,Display,TEXT("mare.Restock %d x %d items"),N,Items.Num());}));
// QA (test profiles only) for the full-game simulation: "mare.QA money <n> | buy <expansion> | biz <id> | step <chapter>".
// "step" meets the current chapter step's requirement (stock, counters, fame, photo, recipes, businesses) and advances it.
static FAutoConsoleCommandWithWorldAndArgs MareQACommand(TEXT("mare.QA"),TEXT("QA: money <n> | buy <expansion> | biz <id> | step <chapter> | fame <level> | dump <name> | hotelroom <i> | complaint <i>:<kind> (QA save profile only)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  FString Profile;FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Profile);Profile.ReplaceInline(TEXT("\\"),TEXT("/"));
  auto PC=World?Cast<AMareController>(UGameplayStatics::GetPlayerController(World,0)):nullptr;auto S=PC?PC->GetSimulation():nullptr;
  if(!S || Args.Num()<2 || !Profile.StartsWith(TEXT("D:/CodexTemp/")))return;const FString Verb=Args[0],Arg=Args[1];bool bOk=false;
  if(Verb==TEXT("money")){S->State->SetNumberField(TEXT("money"),FCString::Atod(*Arg));bOk=S->Save();}
  else if(Verb==TEXT("buy")){   // QA buys the full-game expansions too (the demo lock is for the player)
   bool bEA=false;S->Definitions->TryGetBoolField(TEXT("demo"),bEA);S->Definitions->SetBoolField(TEXT("demo"),false);
   bOk=S->BuyExpansion(Arg);S->Definitions->SetBoolField(TEXT("demo"),bEA);}
  else if(Verb==TEXT("biz"))bOk=S->BuyBusiness(Arg);
  else if(Verb==TEXT("vip")){   // the first open kiosk order becomes a VIP ("mare.QA vip <title index>")
   for(const auto& Pair:UMareSimulation::Object(S->State,TEXT("ue_orders"))->Values){bOk=S->MakeVip(FString(Pair.Key.ToView()),FCString::Atoi(*Arg),0);break;}}
  else if(Verb==TEXT("fame")){for(int32 I=0;I<600 && S->FameLevel()<FCString::Atoi(*Arg);++I)S->AddFame(50);bOk=S->FameLevel()>=FCString::Atoi(*Arg) && S->Save();}
  // 5.1: "mare.QA hotelroom <i>" checks hotel room i out now (dirty, minibar used; 0..2 = visitable 301..303);
  // "mare.QA complaint <i>:<kind>" puts a guest in room i and has them phone in a complaint (hotel_rooms.json kinds).
  else if(Verb==TEXT("hotelroom")){S->SyncRooms();if(auto R=S->HotelRoom(FCString::Atoi(*Arg))){R->SetStringField(TEXT("state"),TEXT("occupied"));
    R->SetObjectField(TEXT("guest"),MakeShared<FJsonObject>());S->HotelCheckOut(R);bOk=true;}}
  else if(Verb==TEXT("complaint")){FString Room,Kind;Arg.Split(TEXT(":"),&Room,&Kind);S->SyncRooms();const int32 I=FCString::Atoi(*Room);
   if(auto R=S->HotelRoom(I)){if(UMareSimulation::String(R,TEXT("state"))!=TEXT("occupied")){R->SetStringField(TEXT("state"),TEXT("occupied"));R->SetNumberField(TEXT("nights"),2);
     R->SetNumberField(TEXT("mood"),.7);auto G=MakeShared<FJsonObject>();G->SetStringField(TEXT("name"),TEXT("Hóspede"));R->SetObjectField(TEXT("guest"),G);}
    bOk=!S->AddHotelComplaint(I,Kind).IsEmpty();}}
  else if(Verb==TEXT("dump")){   // what a reload must keep: owned places, chapters, businesses, company, fame
   auto Out=MakeShared<FJsonObject>();Out->SetObjectField(TEXT("unlocked"),UMareSimulation::Object(S->State,TEXT("unlocked")));
   auto Prog=UMareSimulation::Object(S->State,TEXT("prog"));Out->SetObjectField(TEXT("chapters"),UMareSimulation::Object(Prog,TEXT("ch")));
   Out->SetObjectField(TEXT("biz"),UMareSimulation::Object(Prog,TEXT("biz")));Out->SetObjectField(TEXT("company"),UMareSimulation::Object(S->State,TEXT("company")));
   Out->SetNumberField(TEXT("fame_level"),S->FameLevel());FString Text;FJsonSerializer::Serialize(Out,TJsonWriterFactory<>::Create(&Text));
   bOk=FFileHelper::SaveStringToFile(Text,*(Profile/(Arg+TEXT(".json"))));}
  else if(Verb==TEXT("step") && S->IsChapterOpen(Arg) && !S->IsChapterDone(Arg)){
   auto Chapter=S->ChapterDefinition(Arg);const auto Step=Chapter->GetArrayField(TEXT("steps"))[S->ChapterStep(Arg)]->AsObject();
   const FString Kind=UMareSimulation::String(Step,TEXT("kind")),Item=UMareSimulation::String(Step,TEXT("item"));const int32 Qty=FMath::Max(1,int32(UMareSimulation::Number(Step,TEXT("qty"),1)));
   auto Prog=UMareSimulation::Object(S->State,TEXT("prog"));
   if(Kind==TEXT("deliver")){auto Stock=UMareSimulation::Object(S->State,TEXT("stock"));Stock->SetNumberField(Item,UMareSimulation::Number(Stock,Item)+Qty);}
   else if(Kind==TEXT("serve") || Kind==TEXT("sell"))UMareSimulation::Object(Prog,TEXT("ch"))->SetNumberField(Arg+TEXT("_")+Kind,Qty);
   else if(Kind==TEXT("pay"))S->State->SetNumberField(TEXT("money"),S->Money()+Qty);
   else if(Kind==TEXT("fame"))for(int32 I=0;I<400 && S->FameLevel()<Qty;++I)S->AddFame(50);
   else if(Kind==TEXT("photo"))UMareSimulation::Object(Prog,TEXT("chp"))->SetBoolField(Item,true);
   else if(Kind==TEXT("recipes")){int32 N=0;for(const auto& Pair:UMareSimulation::Object(S->Definitions,TEXT("dishes"))->Values)if(N++<Qty)UMareSimulation::Object(Prog,TEXT("disc"))->SetBoolField(FString(Pair.Key.ToView()),true);}
   else if(Kind==TEXT("biz"))for(const FString Biz:{TEXT("sorveteria"),TEXT("aluguel"),TEXT("food_truck"),TEXT("souvenir"),TEXT("surfe")})S->BuyBusiness(Biz);
   bOk=S->AdvanceChapter(Arg);}
  UE_LOG(LogTemp,Display,TEXT("mare.QA %s %s -> %s (%s)"),*Verb,*Arg,bOk?TEXT("ok"):TEXT("refused"),*S->LastMessage);}));
static FAutoConsoleCommandWithWorldAndArgs MareArcadeCommand(TEXT("mare.Arcade"),TEXT("QA: start:0|1, play:seconds, end, state (game room arcades, 5.4)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(!World)return;if(auto Arc=World->GetSubsystem<UMareArcade>())UE_LOG(LogTemp,Display,TEXT("mare.Arcade %s -> %s"),*FString::Join(Args,TEXT(" ")),*Arc->QA(FString::Join(Args,TEXT(" "))));}));
static FAutoConsoleCommandWithWorldAndArgs MareHotelEventCommand(TEXT("mare.HotelEvent"),TEXT("QA: offer[:kind], accept, today, decline, critic (5.3), state, placeall[:extras], place:i, start (Grand Hotel events, 5.2)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(!World || !World->GetGameInstance())return;auto S=World->GetGameInstance()->GetSubsystem<UMareSimulation>();auto W=World->GetSubsystem<UMareHotelEventsWorld>();if(!S || !W)return;
  const FString Cmd=FString::Join(Args,TEXT(" "));FString Verb,Arg;if(!Cmd.Split(TEXT(":"),&Verb,&Arg))Verb=Cmd;FString Out;
  if(Verb==TEXT("offer"))Out=S->OfferHotelEvent(Arg)+TEXT(" ")+S->LastMessage;
  else if(Verb==TEXT("accept"))Out=S->AcceptHotelEvent()?S->LastMessage:FString(TEXT("refused"));
  else if(Verb==TEXT("decline"))Out=S->DeclineHotelEvent()?FString(TEXT("ok")):FString(TEXT("refused"));
  else if(Verb==TEXT("start")){const double Paid=S->StartHotelEvent();Out=FString::Printf(TEXT("paid=%.0f %s"),Paid,*S->LastMessage);}
  else if(Verb==TEXT("critic"))Out=FString::Printf(TEXT("critic at table %d"),S->SeatCritic());   // 5.3
  else if(Verb==TEXT("today")){if(auto B=S->BookedHotelEvent()){B->SetNumberField(TEXT("day"),UMareSimulation::Number(S->State,TEXT("day"),1));S->Save();Out=TEXT("booked for today");}else Out=TEXT("nothing booked");}
  else Out=W->QA(Cmd);
  UE_LOG(LogTemp,Display,TEXT("mare.HotelEvent %s -> %s"),*Cmd,*Out);}));
static FAutoConsoleCommandWithWorldAndArgs MareShowUICommand(TEXT("mare.ShowUI"),TEXT("QA: opens a panel (pause, options, menu, letter) for UI screenshots."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){if(Args.Num())FMareUIQA::Show(World,Args[0]);}));
void AMareController::BuildPauseMenu(bool bOptions)
{
 if(!GEngine || !GEngine->GameViewport)return;
 if(PauseWidget.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());
 auto Menu=SNew(SVerticalBox);
 auto Add=[&](const FString& Label,TFunction<void()> Callback){Menu->AddSlot().AutoHeight().Padding(0,5)[SNew(SMarePadButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(14,8)).OnClicked_Lambda([Callback](){Callback();return FReply::Handled();})[MareUI::Text(Label,14,FLinearColor::White)]];};
 if(bOptions){
  Menu->AddSlot().AutoHeight().Padding(0,0,0,10)[MareUI::Text(LOCTEXT("OptionsTitle","Opções").ToString(),20)];
  Menu->AddSlot().AutoHeight()[MakeOptionsPanel()];
  Add(LOCTEXT("Back","Voltar").ToString(),[this](){BuildPauseMenu(false);});
 }else{
  Menu->AddSlot().AutoHeight().Padding(0,0,0,12)[MareUI::Text(LOCTEXT("PauseTitle","Maré Alta · pausa").ToString(),20)];
  Add(LOCTEXT("Resume","Retomar").ToString(),[this](){TogglePauseMenu();});
  const int32 SaveSlot=GetSimulation()->ActiveSlot;
  Add(FText::Format(LOCTEXT("SaveSlot","Salvar progresso (slot {0})"),SaveSlot).ToString(),[this](){GetSimulation()->Save();});
  Add(LOCTEXT("Options","Opções").ToString(),[this](){BuildPauseMenu(true);});
  Add(LOCTEXT("MainMenu","Voltar ao menu principal").ToString(),[this](){SetPause(false);ReturnToMainMenu();});
  Add(LOCTEXT("QuitDesktop","Sair para o desktop").ToString(),[this](){GetSimulation()->Save();UKismetSystemLibrary::QuitGame(this,this,EQuitPreference::Quit,false);});
 }
 PauseWidget=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.65f)).HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(bOptions?540:340)[MareNotebook::Page(Menu)]];
 GEngine->GameViewport->AddViewportWidgetContent(PauseWidget.ToSharedRef(),30);
 // Gamepad B: options -> pause page -> back to the game.
 const TWeakObjectPtr<AMareController> Weak(this);
 MareGamepad::PushMenu(PauseWidget.ToSharedRef(),[Weak,bOptions](){if(Weak.IsValid()){if(bOptions)Weak->BuildPauseMenu(false);else Weak->TogglePauseMenu();}});
}
void AMareController::TogglePhone(){if(MainMenuWidget.IsValid())return;if(auto Home=GetWorld()->GetSubsystem<UMareHomeWorld>())if(Home->IsSleeping())return;if(auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>())if(Village->IsDialogueOpen())return;for(TActorIterator<AMareIntro> It(GetWorld());It;++It)if(It->IsArrival() || It->IsLetterOpen())return;if(PauseWidget.IsValid())return;if(bPhoneOpen)ClosePhone();else OpenPhone();}
void AMareController::OpenPhone(int32 Tab)
{
 if(!GEngine || !GEngine->GameViewport)return;
 if(bPhoneOpen)ClosePhone();bPhoneOpen=true;
 if(auto Sim=GetSimulation())Sim->ShowTip(TEXT("phone"));
 if(auto Hero=Cast<AMareCharacter>(GetPawn()))Hero->SetPhoneVisible(true);
 SAssignNew(PhoneWidget,SMarePhone).Owner(this).Tab(Tab);GEngine->GameViewport->AddViewportWidgetContent(PhoneWidget.ToSharedRef(),20);
 {const TWeakObjectPtr<AMareController> Weak(this);MareGamepad::PushMenu(PhoneWidget.ToSharedRef(),[Weak](){if(Weak.IsValid())Weak->ClosePhone();});}
 bShowMouseCursor=true;SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(PhoneWidget).SetHideCursorDuringCapture(false));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
/** A station panel (fridge, cupboard, kitchen) is open: the phone frame, but the order tickets stay on screen. */
static bool GMareStationOpen=false;
void AMareController::OpenStation(FName Station)
{
 if(!GEngine || !GEngine->GameViewport)return;
 if(bPhoneOpen)ClosePhone();bPhoneOpen=true;
 GMareStationOpen=true;
 SAssignNew(PhoneWidget,SMarePhone).Owner(this).Tab(0).Station(Station);GEngine->GameViewport->AddViewportWidgetContent(PhoneWidget.ToSharedRef(),20);
 {const TWeakObjectPtr<AMareController> Weak(this);MareGamepad::PushMenu(PhoneWidget.ToSharedRef(),[Weak](){if(Weak.IsValid())Weak->ClosePhone();});}
 bShowMouseCursor=true;SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(PhoneWidget).SetHideCursorDuringCapture(false));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::ClosePhone()
{
 if(auto Hero=Cast<AMareCharacter>(GetPawn()))Hero->SetPhoneVisible(false);
 if(PhoneWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PhoneWidget.ToSharedRef());
 // A furniture preview ends with the phone: show what is really in use again.
 if(auto Custom=GetWorld()->GetSubsystem<UMareCustomWorld>())if(Custom->IsPreviewing())Custom->ApplyAll();
 PhoneWidget.Reset();bPhoneOpen=false;GMareStationOpen=false;bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
}
void AMareController::EndPlay(const EEndPlayReason::Type Reason){CloseMainMenu();if(PauseWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();ClosePhone();Super::EndPlay(Reason);}
/** Everything the tropical HUD shows; Signature() decides when Slate must rebuild. */
struct FMareHudModel
{
 FString Money,Day,Fame,Notice,Prompt,Carry,Hint,Stars,Rooms,Served,TipTitle,TipText;
 /** Compass: label and horizontal position 0..100 (50 = straight ahead) + 1000 x row, in steps of 1% so the HUD rebuilds rarely. */
 TArray<TPair<FString,int32>> Compass;
 FString InteractKey=TEXT("E"),PhoneKey=TEXT("B"),PauseKey=TEXT("Esc"); // remapped keys, or gamepad buttons after gamepad input
 FString PadHint; // gamepad help over the open phone
 int32 StarsFlash=0; // 1 up (green), -1 down (red)
 TArray<TPair<FString,FString>> Tickets;
 TArray<TPair<FString,int32>> Note; // text, style: 0 heading, 1 main goal, 2 secondary, 3 guidance
 bool bPhone=false;
 /** Pool scoreboard (5.4): balls still on the table (bit per ball, -1 no match), groups (you | opponent<<2), side to play. */
 int32 PoolTable=-1,PoolGroups=0,PoolTurn=0;FString PoolOpp;
 FString Signature()const
 {
  FString S=Money+Day+Fame+Notice+Prompt+Carry+Hint+Stars+Rooms+Served+TipTitle+TipText+FString::FromInt(Compass.Num())+InteractKey+PhoneKey+PauseKey+PadHint+FString::FromInt(StarsFlash)+(bPhone?TEXT("P"):TEXT(""));
  S+=FString::Printf(TEXT("|%d|%d|%d|"),PoolTable,PoolGroups,PoolTurn)+PoolOpp;
  for(const auto& T:Tickets)S+=T.Key+T.Value;
  for(const auto& C:Compass)S+=C.Key+FString::FromInt(C.Value);
  for(const auto& N:Note)S+=N.Key+FString::FromInt(N.Value);
  return S;
 }
};
/** Speech bubbles over the bar guests (CHECKLIST_EXPANSOES 1.2): handwritten paper notes projected over each head. The
 *  texts rebuild the canvas only when they change; positions (viewport pixels, converted with this widget's own
 *  geometry, which includes the DPI) are read every frame. */
class SMareBubbles : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareBubbles){} SLATE_END_ARGS()
 void Construct(const FArguments&){ChildSlot[SAssignNew(Canvas,SCanvas)];SetVisibility(EVisibility::HitTestInvisible);}
 struct FBubble{FString Text;FVector2D Pixel;float Alpha=1;};
 static const FSlateRoundedBoxBrush& BubbleBrush(){static const FSlateRoundedBoxBrush B(MareNotebook::Paper,10.f,MareNotebook::Pencil,1.5f);return B;}
 void Set(const TArray<FBubble>& In)
 {
  FString Sig;for(const auto& B:In)Sig+=B.Text+TEXT("|");Bubbles=In;if(Sig==Last)return;Last=Sig;
  using namespace MareNotebook;Canvas->ClearChildren();
  for(int32 I=0;I<In.Num();++I){
   Canvas->AddSlot().Position_Lambda([this,I](){return Bubbles.IsValidIndex(I)?Bubbles[I].Pixel*Units:FVector2D(-999);})
    .Size(FVector2D(260,80)).HAlign(HAlign_Center).VAlign(VAlign_Bottom)
    [SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Bottom)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(&BubbleBrush()).Padding(FMargin(10,4))
      .ColorAndOpacity_Lambda([this,I](){return FLinearColor(1,1,1,Bubbles.IsValidIndex(I)?Bubbles[I].Alpha:0);})
      .BorderBackgroundColor_Lambda([this,I](){return FSlateColor(FLinearColor(1,1,1,Bubbles.IsValidIndex(I)?Bubbles[I].Alpha:0));})
      [SNew(STextBlock).Text(MareLoc::Text(In[I].Text)).Font(Hand(17)).ColorAndOpacity(Ink).AutoWrapText(true).WrapTextAt(230)]]]];}
 }
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta)override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);FVector2D View(0);if(GEngine && GEngine->GameViewport)GEngine->GameViewport->GetViewportSize(View);
  if(View.X>0)Units=Geometry.GetLocalSize().X/View.X;
 }
private:
 TSharedPtr<SCanvas> Canvas;TArray<FBubble> Bubbles;FString Last;float Units=1;
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
  // Compass strip under the plank: cardinal letters and the resort's places by direction (map_markers.json).
  if(M.Compass.Num()){auto Strip=SNew(SCanvas);const float Width=560;
   for(const auto& C:M.Compass){const bool bCardinal=C.Key.StartsWith(TEXT("\t"));
    Strip->AddSlot().Position(FVector2D(C.Value%1000/100.f*Width,bCardinal?0:16+15*(C.Value/1000))).Size(FVector2D(130,18)).HAlign(HAlign_Center).VAlign(VAlign_Top)
     [Txt(bCardinal?C.Key.Mid(1):FString(TEXT("| "))+C.Key,bCardinal?14:11.5f,bCardinal?Hex(255,215,106):Paper,bCardinal)];}
   Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Center).Padding(FMargin(0,46,0,0))[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(0,0,0,.28f)).Padding(FMargin(4,2))
    [SNew(SBox).WidthOverride(Width).HeightOverride(48)[Strip]]];}
  // First-time tip card, bottom left above the key hints.
  if(!M.TipTitle.IsEmpty())Root->AddSlot().VAlign(VAlign_Bottom).HAlign(HAlign_Left).Padding(FMargin(24,0,0,96))[SNew(SBox).WidthOverride(400)
   [SNew(SBorder).BorderImage(&Ticket()).Padding(FMargin(14,10))[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[Txt(TEXT("Dica · ")+M.TipTitle,14,Accent,true)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,0)[Txt(M.TipText,12.5f,Ink,false,370)]]]];
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
    +SVerticalBox::Slot().AutoHeight().Padding(10,6,10,0)[Txt(M.Tickets[I].Key,13,Accent,true,130)]
    +SVerticalBox::Slot().AutoHeight().Padding(10,2,10,9)[Txt(M.Tickets[I].Value,12,Ink,false,130)]]]];
   Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Center).Padding(0,62,0,0)[Row];
  }
  // Pool scoreboard at the top centre: each side with its group's balls (potted ones faded) and the 8 once it is
  // their target; » marks the side to play.
  if(M.PoolTable>=0){
   static const FSlateRoundedBoxBrush Disc(FLinearColor::White,13.f),Dot(FLinearColor::White,7.f),DotS(FLinearColor::White,6.f);
   static const FLinearColor Colors[8]={Hex(20,20,20),Hex(242,190,30),Hex(30,70,170),Hex(200,40,35),Hex(105,50,140),Hex(235,110,25),Hex(25,120,60),Hex(120,30,35)};
   // Stripes: the colour inside a thick white ring (a band clipped by the disc does not exist in Slate brushes).
   static const TArray<FSlateRoundedBoxBrush> Ring=[]{TArray<FSlateRoundedBoxBrush> Out;for(const FLinearColor& C:Colors)Out.Emplace(C,13.f,FLinearColor(.96f,.95f,.9f),4.f);return Out;}();
   auto Ball=[&](int32 N)->TSharedRef<SWidget>{const bool bStripe=N>8;const FLinearColor C=Colors[N%8];
    auto Face=SNew(SOverlay)+SOverlay::Slot()[bStripe?SNew(SBorder).BorderImage(&Ring[N%8]):SNew(SBorder).BorderImage(&Disc).BorderBackgroundColor(C)];
    const float DotSize=bStripe?12.f:14.f;
    Face->AddSlot().HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(DotSize).HeightOverride(DotSize)[SNew(SBorder).BorderImage(bStripe?&DotS:&Dot).BorderBackgroundColor(FLinearColor(.97f,.96f,.92f)).Padding(0)
     .HAlign(HAlign_Center).VAlign(VAlign_Center)[Txt(FString::FromInt(N),8,Hex(20,20,20),true)]]];
    return SNew(SBox).WidthOverride(26).HeightOverride(26).Padding(0).RenderOpacity(M.PoolTable&(1<<N)?1.f:.22f)[Face];};
   const int32 Groups[2]={M.PoolGroups&3,(M.PoolGroups>>2)&3};const bool bOpen=Groups[0]==0;
   auto List=SNew(SVerticalBox);
   List->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0,0,0,4)[Txt(bOpen?TEXT("Sinuca bola 8 · mesa aberta"):TEXT("Sinuca bola 8"),12.5f,Accent,true)];
   for(int32 Row=0;Row<2;++Row){
    // Open table: one row of solids and one of stripes; then one row per side with its own group.
    const int32 Group=bOpen?Row+1:Groups[Row];const bool bMine=!bOpen && M.PoolTurn==Row;
    const FString Name=bOpen?FString(Row==0?TEXT("Lisas"):TEXT("Listradas")):(Row==0?FString(TEXT("Você")):M.PoolOpp)+(Group==1?TEXT(" · lisas"):TEXT(" · listradas"));
    auto Line=SNew(SHorizontalBox)+SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(SBox).WidthOverride(16)[Txt(bMine?TEXT("»"):TEXT(""),15,Accent,true)]]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,8,0)[SNew(SBox).WidthOverride(170)[Txt(Name,13,Ink,bMine)]];
    int32 Left=0;for(int32 K=0;K<7;++K){const int32 N=Group==1?K+1:K+9;Left+=(M.PoolTable>>N)&1;Line->AddSlot().AutoWidth().Padding(2,0)[Ball(N)];}
    Line->AddSlot().AutoWidth().Padding(8,0,0,0)[Left==0?Ball(8):SNew(SBox).WidthOverride(26)];
    List->AddSlot().AutoHeight().Padding(0,2)[Line];}
   if(bOpen)List->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0,3,0,0)[Txt(M.PoolTurn==0?TEXT("Vez: você"):TEXT("Vez: ")+M.PoolOpp,12,Ink,true)];
   // Top right, where the mission note sits outside a match (the notice card takes the top left).
   Root->AddSlot().VAlign(VAlign_Top).HAlign(HAlign_Right).Padding(0,66,22,0)[SNew(SBorder).BorderImage(&Ticket()).Padding(FMargin(14,8))[List]];}
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
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,10,0)[Key(M.InteractKey)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Txt(M.Prompt,15,Hex(90,58,30),true)]]];
  if(!M.PadHint.IsEmpty())Bottom->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0,6,0,0)[SNew(SBorder).BorderImage(&Toast()).Padding(FMargin(12,5))[Txt(M.PadHint,13,Hex(20,60,56),true)]];
  Root->AddSlot().VAlign(VAlign_Bottom).HAlign(HAlign_Center).Padding(0,0,0,58)[Bottom];
  if(!M.bPhone)Root->AddSlot().VAlign(VAlign_Bottom).HAlign(HAlign_Left).Padding(22,0,0,16)[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[Key(M.PhoneKey)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,16,0)[Txt(TEXT("Celular"),12,FLinearColor::White,true)]
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[Key(M.PauseKey)]
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
 if(Bubbles.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(Bubbles.ToSharedRef());
 Overlay.Reset();Bubbles.Reset();Super::EndPlay(Reason);
}
void AMareHUD::DrawHUD()
{
 Super::DrawHUD();if(!Canvas)return;auto S=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 if(!Overlay.IsValid() && GEngine && GEngine->GameViewport){SAssignNew(Overlay,SMareHud);GEngine->GameViewport->AddViewportWidgetContent(Overlay.ToSharedRef(),10);}
 const auto PC=Cast<AMareController>(GetOwningPlayerController());
 if(Overlay.IsValid())Overlay->SetVisibility(PC && PC->IsMainMenuOpen()?EVisibility::Collapsed:EVisibility::Visible);
 if(!Bubbles.IsValid() && GEngine && GEngine->GameViewport){SAssignNew(Bubbles,SMareBubbles);GEngine->GameViewport->AddViewportWidgetContent(Bubbles.ToSharedRef(),9);}
 if(Bubbles.IsValid()){TArray<SMareBubbles::FBubble> List;
  const bool bShow=PC && !PC->IsMainMenuOpen() && !PC->bPhoneOpen && !GetWorld()->IsPaused() && PC->PlayerCameraManager;
  if(bShow)if(auto BarWorld=GetWorld()->GetSubsystem<UMareBarWorld>()){
   const FVector Eye=PC->PlayerCameraManager->GetCameraLocation();const FVector Fwd=PC->PlayerCameraManager->GetCameraRotation().Vector();
   TArray<TPair<FVector,FString>> All=BarWorld->Bubbles();if(auto ToursWorld=GetWorld()->GetSubsystem<UMareToursWorld>())All.Append(ToursWorld->Bubbles());
   if(auto BoatTour=GetWorld()->GetSubsystem<UMareBoatTourWorld>())All.Append(BoatTour->Bubbles());
   if(auto Snorkel=GetWorld()->GetSubsystem<UMareSnorkelWorld>())All.Append(Snorkel->Bubbles());
   if(auto Trail=GetWorld()->GetSubsystem<UMareTrailWorld>())All.Append(Trail->Bubbles());
   if(auto Kiosk=GetWorld()->GetSubsystem<UMareKioskWorld>())All.Append(Kiosk->Bubbles());   // 07/11: who waits at the counter
   for(const auto& G:All){const FVector D=G.Key-Eye;const float Dist=D.Size();if(Dist>1400 || FVector::DotProduct(D,Fwd)<=0)continue;
    FHitResult Hit;FCollisionQueryParams Q(TEXT("MareBubble"),false,GetOwningPawn());
    if(GetWorld()->LineTraceSingleByChannel(Hit,Eye,G.Key,ECC_Visibility,Q) && Hit.Distance<Dist-60)continue;
    FVector2D Pixel;if(!PC->ProjectWorldLocationToScreen(G.Key,Pixel))continue;
    List.Add({G.Value,Pixel,FMath::Clamp((1400-Dist)/300.f,0.f,1.f)});}}
  Bubbles->Set(List);}
 if(PC && PC->IsMainMenuOpen())return;
 auto Dish=[&](const FString& Id){return UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id),TEXT("name"));};
 FMareHudModel M;M.bPhone=PC && PC->bPhoneOpen;
 auto KeyName=[](const TCHAR* Action){return MareGamepad::ActionLabel(Action);};
 M.InteractKey=KeyName(TEXT("Interact"));M.PhoneKey=KeyName(TEXT("Phone"));M.PauseKey=KeyName(TEXT("Pause"));
 const bool bPad=MareGamepad::UsingGamepad();
 if(M.bPhone && bPad){const bool bPlayStation=FMareOptions::Get().PadGlyphs==1;auto Pad=[bPlayStation](const FKey& Key){return MareLoc::Text(MareGamepad::PadLabel(Key,bPlayStation));};
  M.PadHint=FText::Format(LOCTEXT("PadPhoneHint","{0}/{1} abas · {2} escolhe · {3} fecha"),Pad(EKeys::Gamepad_LeftShoulder),Pad(EKeys::Gamepad_RightShoulder),
   Pad(EKeys::Gamepad_FaceButton_Bottom),Pad(EKeys::Gamepad_FaceButton_Right)).ToString();}
 const int32 Minutes=UMareSimulation::Number(S->State,TEXT("minutes"));
 M.Money=FString::Printf(TEXT("R$ %.0f"),S->Money());
 M.Day=FString::Printf(TEXT("Dia %.0f · %02d:%02d"),UMareSimulation::Number(S->State,TEXT("day"),1),Minutes/60,Minutes%60);
 M.Fame=TEXT("Fama: ")+S->FameName();
 const double Now=GetWorld()->GetRealTimeSeconds();
 const double Stars=FMath::RoundToDouble(S->Stars()*10)/10;
 if(ShownStars>=0 && Stars!=ShownStars){bStarsUp=Stars>ShownStars;StarsFlashUntil=Now+1.5;}
 ShownStars=Stars;if(Now<StarsFlashUntil)M.StarsFlash=bStarsUp?1:-1;
 M.Stars=FString::Printf(TEXT("%.1f"),Stars).Replace(TEXT("."),TEXT(","));
 if(M.StarsFlash && FMareOptions::Get().bColorSafe)M.Stars+=M.StarsFlash>0?TEXT(" +"):TEXT(" -");   // not only green/red
 if(const int32 Rooms=S->RoomsTotal())M.Rooms=FString::Printf(TEXT("%d/%d"),FMath::Min(S->RoomsOccupied(),Rooms),Rooms);
 M.Served=FString::Printf(TEXT("%d hoje"),S->ServedToday());
 if(S->LastMessage!=Notice){Notice=S->LastMessage;NoticeUntil=Notice.IsEmpty()?0:Now+7;}
 if(S->IsEndOfContentDue())if(auto EndPC=Cast<AMareController>(GetOwningPlayerController()))EndPC->ShowEndOfContent();
 // Compass: places by direction relative to where the player looks.
 if(auto View=GetOwningPlayerController()?GetOwningPlayerController()->PlayerCameraManager:nullptr){
  static TSharedPtr<FJsonObject> Markers;
  if(!Markers.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/map_markers.json")));
   FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Markers);if(!Markers.IsValid())Markers=MakeShared<FJsonObject>();}
  const FVector Eye=View->GetCameraLocation();const float Yaw=View->GetCameraRotation().Yaw;const float Half=UMareSimulation::Number(Markers,TEXT("field_of_view"),75);
  auto Slot=[&](float Bearing){const float Delta=FRotator::NormalizeAxis(Bearing-Yaw);return FMath::Abs(Delta)>Half?-1:FMath::RoundToInt(50.f+50.f*Delta/Half);};
  auto Place=[&](const FString& Label,float Bearing){const int32 X=Slot(Bearing);if(X>=0)M.Compass.Add({Label,X});};
  // UE yaw: 0 = +X (east on this map), 90 = +Y (south): letters for the four directions.
  // Cardinals in the current language (de: O = Ost, not the Portuguese Oeste); marked with a leading tab.
  Place(TEXT("\t")+MareLoc::Cardinal(1),0);Place(TEXT("\t")+MareLoc::Cardinal(2),90);Place(TEXT("\t")+MareLoc::Cardinal(3),180);Place(TEXT("\t")+MareLoc::Cardinal(0),-90);
  const TArray<TSharedPtr<FJsonValue>>* List=nullptr;const double Near=UMareSimulation::Number(Markers,TEXT("near"),900);
  TArray<TTuple<double,FString,int32>> Found;   // distance, name, position
  if(Markers->TryGetArrayField(TEXT("markers"),List))for(const auto& V:*List){const auto Mk=V->AsObject();const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
   if(!Mk->TryGetArrayField(TEXT("at"),At) || At->Num()<2)continue;
   const FString Req=UMareSimulation::String(Mk,TEXT("requires")),Biz=UMareSimulation::String(Mk,TEXT("biz"));bool bShow=true;
   if(!Req.IsEmpty()){bShow=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Req,bShow);}
   if(!Biz.IsEmpty())bShow=S->OwnsBusiness(Biz);
   const FVector To=FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),Eye.Z)-Eye;if(!bShow || To.Size2D()<Near)continue;
   const int32 X=Slot(To.Rotation().Yaw);if(X>=0)Found.Add({To.Size2D(),UMareSimulation::String(Mk,TEXT("name")),X});}
  // Places in the same direction would print over each other: nearest first, two rows, the farthest ones left out.
  Found.Sort([](const auto& A,const auto& B){return A.template Get<0>()<B.template Get<0>();});
  TArray<FVector2D> Used[2];
  for(const auto& F:Found){const FString& Name=F.template Get<1>();const int32 X=F.template Get<2>();
   // Label width measured with the font the strip draws it in ("| " + name, regular 11), in % of the 560-unit strip.
   const float Px=FSlateApplication::IsInitialized()?FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(TEXT("| ")+Name,FCoreStyle::GetDefaultFontStyle("Regular",11)).X:Name.Len()*8.5f;
   const float HalfWidth=(Px+10.f)/560.f*50.f;
   for(int32 Row=0;Row<2;Row++){bool bFree=true;for(const FVector2D& U:Used[Row])if(FMath::Abs(U.X-X)<U.Y+HalfWidth){bFree=false;break;}
    if(bFree){Used[Row].Add(FVector2D(X,HalfWidth));M.Compass.Add({Name,X+1000*Row});break;}}}
 }
 // Item 10, Dona Dilce's debt: her letter once the company exists, then each milestone (25/50/75 %) once, after the phone
 // closes and no other tip is on screen; the full-game finale uses the end screen.
 if(!M.bPhone && S->PendingTipTitle.IsEmpty() && Now>=TipUntil){
  if(!S->ShowDebtIntro()){const TArray<FString> Crossed=S->DebtPendingMilestones();
   if(Crossed.Num()){FString Text;const FString Title=S->DebtMilestoneTitle(Crossed.Last(),&Text);S->PendingTipTitle=Title;S->PendingTipText=Text;S->AckDebt();}}}
 if(!M.bPhone && S->IsDebtFinalePending())if(auto DebtPC=Cast<AMareController>(GetOwningPlayerController()))DebtPC->ShowEndOfContent(true);
 // First-time tips (tutorial.json): taken from the simulation and kept on screen for a while.
 if(!S->PendingTipTitle.IsEmpty()){TipTitle=S->PendingTipTitle;TipText=S->PendingTipText;S->PendingTipTitle.Reset();TipUntil=Now+14;}
 if(Now<TipUntil && !M.bPhone){M.TipTitle=TipTitle;M.TipText=TipText;}
 if(Now<NoticeUntil)M.Notice=Notice;
 const int32 IntroStage=UMareSimulation::Number(S->State,TEXT("ue_intro_stage"),2);
 if(IntroStage==0)M.Note={{TEXT("Chegada"),0},{TEXT("A vila parecia menor... e o mar, do tamanho das minhas lembranças."),2},{M.InteractKey+TEXT(" · avançar"),3}};
 else{
  M.Note.Add({TEXT("Missões"),0});
  if(IntroStage==1)M.Note.Add({TEXT("Entre na casa e leia a carta da avó Dilce"),3});
  bool bCreated=false;UMareSimulation::Object(S->State,TEXT("company"))->TryGetBoolField(TEXT("created"),bCreated);
  if(!bCreated && IntroStage>=2)M.Note.Add({TEXT("Comece aqui: ")+M.PhoneKey+TEXT(" · Celular → Quiosque → Criar empresa"),3});
  else if(bCreated && !S->IsOpen()){
   // 07/11 (Sergio: "tutorial precisa dizer como e onde abrir o quiosque"): where it is, which sign and which key; once
   // the opening is booked before 8h, say when it opens instead of asking again (pressing again would cancel it).
   bool bRequested=false;UMareSimulation::Object(S->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),bRequested);
   if(bRequested)M.Note.Add({FString::Printf(TEXT("Abertura marcada: o quiosque abre às %.0fh"),UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("company")),TEXT("sim")),TEXT("start"),8)),3});
   else M.Note.Add({FString::Printf(TEXT("Abra o quiosque: vá até a praia (siga \"Quiosque\" na bússola) e aperte %s na placa vermelha FECHADO do balcão"),*M.InteractKey),3});}
  const auto Campaign=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("campaign"));
  const TArray<TSharedPtr<FJsonValue>>* Missions=nullptr;const int32 Stage=UMareSimulation::Number(Campaign,TEXT("stage"));
  if(S->IsCampaignAtFullGame())M.Note.Add({TEXT("Uma nova maré · a história continua no jogo completo"),2});   // Demo (06/11)
  else if(S->Definitions->TryGetArrayField(TEXT("campaign"),Missions) && Missions->IsValidIndex(Stage)){
   const auto Mission=(*Missions)[Stage]->AsObject();const int32 Goal=UMareSimulation::Number(Mission,TEXT("qty"));const int32 Progress=FMath::Min(S->MissionAmount(Mission),Goal);
   // Objective always visible (Acesso Antecipado, 04/11): the title, what to do now and, for a purchase, how far the money
   // and the fame are from it (the Grand Hotel is a long save: "R$ 12.400 / 30.000 · fama 7/9").
   FString Extra;
   if(Progress<Goal && UMareSimulation::String(Mission,TEXT("kind"))==TEXT("expansion")){
    auto Exp=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("expansions")),UMareSimulation::String(Mission,TEXT("item")));
    const double Cost=UMareSimulation::Number(Exp,TEXT("cost"));const int32 Fame=UMareSimulation::Number(Exp,TEXT("fame"));
    if(Cost>0)Extra=FString::Printf(TEXT(" · R$ %.0f / %.0f"),FMath::Min(S->Money(),Cost),Cost);
    if(Fame>0)Extra+=FString::Printf(TEXT(" · fama %d/%d"),FMath::Min(S->FameLevel(),Fame),Fame);}
   M.Note.Add({UMareSimulation::String(Mission,TEXT("title"))+FString::Printf(TEXT(" — %d/%d"),Progress,Goal)+(Progress>=Goal?TEXT(" · concluir no celular"):TEXT("")),1});
   if(Progress<Goal)M.Note.Add({UMareSimulation::String(Mission,TEXT("task"))+Extra,2});
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
  // The next thing to save for, always visible.
  // 6.2: with the fame and the village story still missing, not only the money.
  {const FString Next=bCreated?S->NextUnlockText():FString();if(!Next.IsEmpty())M.Note.Add({Next,3});}
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
   // A famous customer: title on the ticket and the special request under the items.
   bool bVip=false;Order->TryGetBoolField(TEXT("vip"),bVip);
   if(bVip)Text+=TEXT("\n\"")+UMareSimulation::String(Order,TEXT("request"))+TEXT("\"");
   M.Tickets.Add({bVip?FString::Printf(TEXT("#%d VIP · %s%s"),Number,*UMareSimulation::String(Order,TEXT("vip_title")),Feel)
    :FString::Printf(TEXT("#%d %s%s"),Number,*UMareSimulation::String(Order,TEXT("name")),Feel),Text});
  }
 }
 if(!S->Carry().IsEmpty())M.Carry=Dish(S->Carry());
 if(auto Hero=Cast<AMareCharacter>(GetOwningPawn()))if(Hero->GetCharacterMovement()->IsSwimming())M.Hint=bPad?FText::Format(LOCTEXT("SwimPad","Nadando · {0} sobe · {1} mergulha"),MareLoc::Text(KeyName(TEXT("Jump"))),MareLoc::Text(KeyName(TEXT("Dive")))).ToString()
  :FString::Printf(TEXT("Nadando · %s sobe · %s/%s mergulha"),*KeyName(TEXT("Jump")),*KeyName(TEXT("Dive")),*KeyName(TEXT("Sprint")));
 if(auto BoatTour=GetWorld()->GetSubsystem<UMareBoatTourWorld>())if(BoatTour->IsActive())M.Hint=BoatTour->Status();
 if(auto Snorkel=GetWorld()->GetSubsystem<UMareSnorkelWorld>())if(Snorkel->IsActive())M.Hint=Snorkel->Status();
 if(auto Rental=GetWorld()->GetSubsystem<UMareRentalWorld>())if(Rental->IsActive())M.Hint=Rental->Status();
 if(auto Trail=GetWorld()->GetSubsystem<UMareTrailWorld>())if(Trail->IsActive())M.Hint=Trail->Status();
 // The mission note would sit on top of the held phone.
 // 07/11 (Sergio: "o pedido some da tela"): at a station the tickets stay (top centre, clear of the panel on the left).
 if(M.bPhone){M.Note.Empty();if(!GMareStationOpen)M.Tickets.Empty();}
 // Table tennis match: the score line instead of the crosshair and the mission note.
 if(auto TT=GetWorld()->GetSubsystem<UMareTableTennis>())if(TT->IsPlaying()){M.Note.Empty();M.Tickets.Empty();M.Hint=TT->Status();Overlay->Refresh(M);return;}
 // Arcade game: the controls instead of the crosshair and the mission note.
 if(auto Arc=GetWorld()->GetSubsystem<UMareArcade>())if(Arc->IsPlaying()){M.Note.Empty();M.Tickets.Empty();M.Compass.Empty();M.Hint=Arc->Status();Overlay->Refresh(M);return;}
 // Foosball match: the score line, and the active rod underlined from its grip to the wall.
 if(auto FB=GetWorld()->GetSubsystem<UMareFoosball>())if(FB->IsPlaying()){M.Note.Empty();M.Tickets.Empty();M.Compass.Empty();M.Hint=FB->Status();FVector From,To;FVector2D A,B;
  if(FB->ActiveRodLine(From,To) && PC && PC->ProjectWorldLocationToScreen(From,A) && PC->ProjectWorldLocationToScreen(To,B))DrawLine(A.X,A.Y,B.X,B.Y,FLinearColor(1,.85f,.2f,.85f),4.f);
  Overlay->Refresh(M);return;}
 // Pool match: aim guide, power bar and score instead of the crosshair and the mission note.
 if(auto Room=GetWorld()->GetSubsystem<UMareGameRoom>())if(Room->IsPlaying()){
  // The compass strip would run under the scoreboard (and means nothing at the table).
  M.Note.Empty();M.Tickets.Empty();M.Compass.Empty();M.Hint=Room->Status();FVector From,To;FVector2D A,B;
  if(Room->AimLine(From,To) && PC && PC->ProjectWorldLocationToScreen(From,A) && PC->ProjectWorldLocationToScreen(To,B))DrawLine(A.X,A.Y,B.X,B.Y,FLinearColor(1,1,1,.7f),1.5f);
  M.PoolTable=0;for(int32 I=0;I<16;++I)if(!Room->Balls[I].bIn)M.PoolTable|=1<<I;
  M.PoolGroups=Room->Group[0]|(Room->Group[1]<<2);M.PoolTurn=Room->Turn;M.PoolOpp=Room->OpponentName();
  // Called pocket for the 8: a yellow ring over the pocket mouth.
  FVector Called;FVector2D P;if(PC && Room->CalledPocketWorld(Called) && PC->ProjectWorldLocationToScreen(Called,P)){const float Rad=16;
   for(int32 K=0;K<16;++K){const float A0=K*UE_TWO_PI/16,A1=(K+1)*UE_TWO_PI/16;DrawLine(P.X+Rad*FMath::Cos(A0),P.Y+Rad*FMath::Sin(A0),P.X+Rad*FMath::Cos(A1),P.Y+Rad*FMath::Sin(A1),FLinearColor(1.f,.85f,.2f),2.5f);}}
  if(Room->Power()>0){const float X=Canvas->ClipX*.5f-120,Y=Canvas->ClipY-150;DrawRect(FLinearColor(0,0,0,.4f),X,Y,240,10);DrawRect(FLinearColor(1.f,.8f-.5f*Room->Power(),.3f),X,Y,240*Room->Power(),10);}
  Overlay->Refresh(M);return;}
 if(PC && !PC->bPhoneOpen && !GetWorld()->IsPaused()){
  const auto Target=AMareServiceTarget::FindFocused(GetOwningPlayerController());
  MareOutline::Update(GetOwningPlayerController(),Target);   // reference tip 1: outline what E would use
  const FLinearColor FocusColor=Target?FLinearColor(1.f,.88f,.56f):FLinearColor(.9f,.9f,.9f,.8f);
  const float CX=Canvas->ClipX*.5f,CY=Canvas->ClipY*.5f;
  DrawLine(CX-3,CY,CX+3,CY,FocusColor,1.f);DrawLine(CX,CY-3,CX,CY+3,FocusColor,1.f);
  if(Target)M.Prompt=Target->Prompt();
 }
 else MareOutline::Update(GetOwningPlayerController(),nullptr);
 Overlay->Refresh(M);
}
AMareGameMode::AMareGameMode(){PrimaryActorTick.bCanEverTick=true;DefaultPawnClass=AMareCharacter::StaticClass();PlayerControllerClass=AMareController::StaticClass();HUDClass=AMareHUD::StaticClass();}
void AMareGameMode::StartSession()
{
 // 07/11 (Sergio: "apresentação inicial do jogo"): a new game opens with the story postcards (MareTitle.cpp), then the
 // bus arrival. Loaded games and QA runs go straight on.
 auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();auto PC=Cast<AMareController>(GetWorld()->GetFirstPlayerController());
 const TCHAR* Cmd=FCommandLine::Get();
 // QA profiles (-MareSaveRoot under D:/CodexTemp, the gate checks the bus driver right away) skip it; mare.Story shows it.
 const bool bQA=GIsAutomationTesting || FParse::Param(Cmd,TEXT("MarePreviewQA")) || FParse::Param(Cmd,TEXT("MareIntroQA")) || FParse::Param(Cmd,TEXT("MareGraphicsQA")) || FParse::Param(Cmd,TEXT("MareBench")) || FParse::Param(Cmd,TEXT("MareSkipMenu"))
  || FString(Cmd).Contains(TEXT("MareSaveRoot=D:/CodexTemp/"));
 if(!bQA && Sim && PC && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)==0){
  const TWeakObjectPtr<AMareGameMode> Weak(this);
  if(MareStory::Show(PC,[Weak](){if(Weak.IsValid() && Weak->GetWorld())Weak->GetWorld()->SpawnActor<AMareIntro>();}))return;}
 GetWorld()->SpawnActor<AMareIntro>();
}
void AMareGameMode::BeginPlay()
{
 Super::BeginPlay();auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();if(Sim)Sim->bHoldSaves=false;
 FMareOptions::ApplyStartup();
 const TCHAR* Cmd=FCommandLine::Get();
 const bool bQA=FParse::Param(Cmd,TEXT("MareGraphicsQA")) || FParse::Param(Cmd,TEXT("MareIntroQA")) || FParse::Param(Cmd,TEXT("MarePreviewQA")) || FParse::Param(Cmd,TEXT("MareBench")) || FParse::Param(Cmd,TEXT("MareSkipMenu")) || GIsAutomationTesting;
 auto PC=Cast<AMareController>(GetWorld()->GetFirstPlayerController());
 if(Sim && !Sim->bMainMenuDone && !bQA && PC)PC->OpenMainMenu();
 if(!PC || !PC->IsMainMenuOpen()){if(Sim)Sim->bMainMenuDone=true;StartSession();}
 if(FParse::Param(FCommandLine::Get(),TEXT("MareGraphicsQA")))GetWorld()->SpawnActor<AMareGraphicsQA>();if(FParse::Param(FCommandLine::Get(),TEXT("MareIntroQA")))GetWorld()->SpawnActor<AMareIntroQA>();if(FParse::Param(FCommandLine::Get(),TEXT("MarePreviewQA")))GetWorld()->SpawnActor<AMarePreviewQA>();if(FParse::Param(FCommandLine::Get(),TEXT("MareBench")))GetWorld()->SpawnActor<AMareBench>();}

void AMareGameMode::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 if(Sim->bTitleOpen)return;   // title screen: the clock and the autosave wait (MareTitle.cpp)
 Sim->AdvanceMinutes(DeltaSeconds*1.0);SaveClock+=DeltaSeconds;if(SaveClock>=30){Sim->Save();SaveClock=0;}   // 1 game minute per real second: a day 08-24h lasts 16 min (balance_model.py, 04/11); autosave every 30 s (the comment used to swallow it, GPT report 06/11)
}

UMareSimulation* AMareController::GetSimulation()const{return GetGameInstance()->GetSubsystem<UMareSimulation>();}
#undef LOCTEXT_NAMESPACE
