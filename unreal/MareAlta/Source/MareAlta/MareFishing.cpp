// Fishing at the pier with bait, a fight and the species book (11/11, Fase 3). The rules live in the simulation
// (MareLeisure.cpp: HookFish, LandFish, BuyBait) and in FMareFishFight below; this file is the panel.
#include "MareFishing.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareAudioWorld.h"
#include "MareNotebookStyle.h"
#include "MareLoc.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Images/SImage.h"
#include "Engine/Texture2D.h"
#include "UObject/StrongObjectPtr.h"
#include "Misc/PackageName.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"

void FMareFishFight::Step(float Dt,bool bReel,float Rand01)
{
 if(Result!=0 || Dt<=0)return;
 // The fish pulls in bursts: longer and closer together the stronger it is.
 if(PullLeft>0)PullLeft-=Dt;
 else if((NextPull-=Dt)<=0){PullLeft=.6f+1.f*Strength;NextPull=FMath::Lerp(1.9f,1.1f,Strength)*(.6f+.8f*Rand01);}
 const bool bPull=PullLeft>0;
 Tension+=Dt*(bReel?(.55f+(bPull?.35f+.9f*Strength:0.f)):(-.6f+(bPull?.25f*Strength:0.f)));
 // Tuned so that giving line during the pulls and reeling between them lands a sardine in ~5 s and the biggest
 // grouper in ~40 s (MareFishingTests); reeling against a pull gains almost nothing.
 Progress+=Dt*(bReel?(bPull?.04f:.30f-.12f*Strength):-(bPull?.04f+.05f*Strength:.03f));
 Tension=FMath::Clamp(Tension,0.f,1.2f);
 if(Tension>=1.f)Over+=Dt;else Over=FMath::Max(0.f,Over-Dt*2.f);
 if(Tension<=.02f && !bReel)Slack+=Dt;else Slack=0;
 if(Over>.45f)Result=-1;
 else if(Slack>2.5f || Progress<=0.f)Result=-2;
 else if(Progress>=1.f)Result=1;
}

namespace
{
 const float BarWidth=520.f;
 /** Profile picture of a species (rendered from the bpy model, 2:1). The texture is held for as long as the game runs:
  *  a brush that only points at it would not keep it from the garbage collector. */
 const FSlateBrush* FishBrush(const FString& Id)
 {
  struct FPicture{TStrongObjectPtr<UTexture2D> Texture;FSlateBrush Brush;};
  static TMap<FString,TSharedPtr<FPicture>> Pictures;
  if(const auto Found=Pictures.Find(Id))return (*Found)->Texture.IsValid()?&(*Found)->Brush:nullptr;
  auto Picture=MakeShared<FPicture>();const FString Path=FString::Printf(TEXT("/Game/UI/Fish/T_Fish_%s"),*Id);
  if(FPackageName::DoesPackageExist(Path))if(auto Texture=LoadObject<UTexture2D>(nullptr,*(Path+TEXT(".T_Fish_")+Id))){
   Picture->Texture.Reset(Texture);Picture->Brush.SetResourceObject(Texture);Picture->Brush.ImageSize=FVector2D(256,128);Picture->Brush.DrawAs=ESlateBrushDrawType::Image;}
  Pictures.Add(Id,Picture);return Picture->Texture.IsValid()?&Picture->Brush:nullptr;
 }
 class SMareFishingGame;
 TWeakPtr<SMareFishingGame> GFishing;

 class SMareFishingGame : public SCompoundWidget
 {
 public:
  SLATE_BEGIN_ARGS(SMareFishingGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_END_ARGS()
  void Construct(const FArguments& Args)
  {
   using namespace MareNotebook;Owner=Args._Owner;Last=FPlatformTime::Seconds();
   if(auto S=Sim()){const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
    if(S->LeisureDefs()->TryGetArrayField(TEXT("baits"),List))for(const auto& V:*List)Baits.Add(V->AsObject());}   // i18n:skip
   Cast();
   auto Bar=[this](TAttribute<FOptionalSize> Width,TAttribute<FSlateColor> Colour,TAttribute<FMargin> Mark){
    return SNew(SBox).WidthOverride(BarWidth).HeightOverride(26)[SNew(SOverlay)
     +SOverlay::Slot()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Kraft)]
     +SOverlay::Slot().HAlign(HAlign_Left)[SNew(SBox).WidthOverride(Width)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Colour)]]
     +SOverlay::Slot().HAlign(HAlign_Left).Padding(Mark)[SNew(SBox).WidthOverride(3)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Ink)]]];};
   TSharedRef<SVerticalBox> Book=SNew(SVerticalBox);
   if(auto S=Sim()){const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
    if(S->LeisureDefs()->TryGetArrayField(TEXT("species"),List))for(const auto& V:*List){const auto F=V->AsObject();
     const FSlateBrush* Picture=FishBrush(UMareSimulation::String(F,TEXT("id")));
     Book->AddSlot().AutoHeight().Padding(0,1)[SNew(SHorizontalBox)
      +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,10,0)[SNew(SBox).WidthOverride(84).HeightOverride(42)
       [Picture?StaticCastSharedRef<SWidget>(SNew(SImage).Image(Picture).ColorAndOpacity_Lambda([this,F](){return FSlateColor(Count(F)>0?FLinearColor::White:FLinearColor(.03f,.03f,.03f,.5f));})):StaticCastSharedRef<SWidget>(SNew(SBox))]]
      +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[SNew(STextBlock).Font(Hand(19)).AutoWrapText(true)
       .ColorAndOpacity_Lambda([this,F](){return FSlateColor(Count(F)>0?MareNotebook::Ink:MareNotebook::Pencil);})
       .Text_Lambda([this,F](){return FText::FromString(BookLine(F));})]];}}
   ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,70)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,16))
    [SNew(SBox).WidthOverride(BarWidth+40)[SNew(SWidgetSwitcher).WidgetIndex_Lambda([this](){return bBook?1:0;})
     +SWidgetSwitcher::Slot()[SNew(SVerticalBox)
      +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Pescaria no píer"),30,Brown)]
      +SVerticalBox::Slot().AutoHeight().Padding(0,4)[SNew(STextBlock).Font(Hand(24)).AutoWrapText(true).ColorAndOpacity_Lambda([this](){return FSlateColor(bBite || (bFight && Fight.IsPulling())?MareNotebook::Red:MareNotebook::Ink);})
       .Text_Lambda([this](){return MareLoc::Text(Status);})]
      +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,2)[SNew(SBox).WidthOverride(256).HeightOverride(128)
       .Visibility_Lambda([this](){return !bFight && !LandedId.IsEmpty() && FishBrush(LandedId)?EVisibility::Visible:EVisibility::Collapsed;})
       [SNew(SImage).Image_Lambda([this](){return FishBrush(LandedId);})]]
      // The fight: tension (keep it under the mark) and the line already reeled in.
      +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[SNew(SVerticalBox).Visibility_Lambda([this](){return bFight?EVisibility::Visible:EVisibility::Collapsed;})
       +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Tensão da linha"),16,Faded)]
       +SVerticalBox::Slot().AutoHeight()[Bar(TAttribute<FOptionalSize>::CreateLambda([this](){return FOptionalSize(FMath::Clamp(Fight.Tension,0.f,1.f)*BarWidth);}),
         TAttribute<FSlateColor>::CreateLambda([this](){return FSlateColor(Fight.Tension>.9f?MareNotebook::Red:Fight.Tension>.72f?MareNotebook::Hex(214,150,40):MareNotebook::Green);}),
         FMargin(.9f*BarWidth,0,0,0))]
       +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[HandText(TEXT("Linha recolhida"),16,Faded)]
       +SVerticalBox::Slot().AutoHeight()[Bar(TAttribute<FOptionalSize>::CreateLambda([this](){return FOptionalSize(FMath::Clamp(Fight.Progress,0.f,1.f)*BarWidth);}),
         FSlateColor(MareNotebook::Brown),FMargin(BarWidth-3,0,0,0))]]
      +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Brown).AutoWrapText(true).Text_Lambda([this](){return FText::FromString(BaitLine());})]
      +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Green).Text_Lambda([this](){
        auto S=Sim();return MareLoc::Text(FString::Printf(TEXT("Peixes hoje: %d · Livro: %d de %d espécies"),Caught,S?S->SpeciesCaught():0,S?S->SpeciesTotal():0));})]
      +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(15)).ColorAndOpacity(Faded).AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(bFight
        ?FString(TEXT("Segure E, Espaço, clique ou A para recolher · solte quando o peixe puxar · a linha arrebenta no vermelho"))
        :FString(TEXT("Espere fisgar e aperte E, Espaço, clique ou A · 1, 2, 3 trocam a isca · L abre o livro · Esc ou B recolhe a linha")));})]]
     +SWidgetSwitcher::Slot()[SNew(SVerticalBox)
      +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Livro de espécies"),30,Brown)]
      +SVerticalBox::Slot().AutoHeight().Padding(0,4)[Book]
      +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[HandText(TEXT("L, Esc ou B volta para a pescaria"),15,Faded)]]]]];
  }
  virtual bool SupportsKeyboardFocus()const override{return true;}
  virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
  {
   const FKey K=Event.GetKey();
   if(K==EKeys::L || K==EKeys::Tab || K==EKeys::Gamepad_FaceButton_Top){if(!bFight)bBook=!bBook;return FReply::Handled();}
   if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){if(bBook)bBook=false;else if(Owner.IsValid())Owner->CloseBusinessGame();return FReply::Handled();}
   if(bBook)return FReply::Handled();
   if(K==EKeys::One || K==EKeys::Two || K==EKeys::Three){PickBait(K==EKeys::One?0:K==EKeys::Two?1:2);return FReply::Handled();}
   if(K==EKeys::Gamepad_DPad_Left || K==EKeys::Gamepad_DPad_Right){PickBait((Bait+(K==EKeys::Gamepad_DPad_Right?1:Baits.Num()-1))%FMath::Max(1,Baits.Num()));return FReply::Handled();}
   if(IsAction(K)){if(!Event.IsRepeat())Press();return FReply::Handled();}
   return FReply::Unhandled();
  }
  virtual FReply OnKeyUp(const FGeometry&,const FKeyEvent& Event) override{if(IsAction(Event.GetKey())){bHeld=false;return FReply::Handled();}return FReply::Unhandled();}
  virtual FReply OnMouseButtonDown(const FGeometry&,const FPointerEvent&) override{if(!bBook)Press();return FReply::Handled();}
  virtual FReply OnMouseButtonUp(const FGeometry&,const FPointerEvent&) override{bHeld=false;return FReply::Handled();}
  virtual void Tick(const FGeometry& Geometry,const double Time,const float) override
  {
   SCompoundWidget::Tick(Geometry,Time,0);
   // Real time: the Slate tick is slow while the editor is in the background.
   const double Now=FPlatformTime::Seconds();Advance(float(FMath::Clamp(Now-Last,0.,.1)));Last=Now;
  }
  void Advance(float Delta)
  {
   if(bBook)return;
   if(bFight){if(bAuto)bHeld=(!Fight.IsPulling() && Fight.Tension<.8f) || Fight.Tension<.12f;   // QA: the sensible angler of the tests
    Fight.Step(Delta,bHeld,FMath::FRand());
    if(Fight.IsPulling()!=bWasPulling){bWasPulling=Fight.IsPulling();Status=bWasPulling?FString::Printf(TEXT("%s está puxando! Dê linha!"),*FishName()):FString(TEXT("Agora! Recolha a linha!"));}
    if(Fight.Result!=0)EndFight();
    return;}
   Timer-=Delta;if(Timer>0)return;
   if(bBite){bBite=false;Hooked.Reset();Status=TEXT("Escapou... a linha voltou vazia.");Timer=1.2f;bRecast=true;return;}
   if(bRecast){bRecast=false;Cast();return;}
   bBite=true;Status=TEXT("FISGOU! Puxe agora!");Timer=Window;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("pool_rail_bounce"));
  }
  // QA entry points.
  void QABite(){if(bFight)return;bBook=false;bRecast=false;bBite=false;Timer=0;Advance(.01f);}   // a bite right now, whatever the panel was doing
  void QAHold(bool bDown){bHeld=bDown;}
  FString State()
  {
   auto S=Sim();
   return FString::Printf(TEXT("open=%d bait=%s bite=%d fight=%d tension=%.2f progress=%.2f pulling=%d result=%d caught=%d book=%d/%d status=%s"),bBook?1:0,*BaitId(),bBite?1:0,bFight?1:0,   // i18n:skip
    Fight.Tension,Fight.Progress,Fight.IsPulling()?1:0,Fight.Result,Caught,S?S->SpeciesCaught():0,S?S->SpeciesTotal():0,*Status);
  }
  void Press()
  {
   if(bFight){bHeld=true;return;}
   if(bRecast)return;
   if(!bBite){Status=TEXT("Cedo demais! O peixe se assustou.");Timer=1.2f;bRecast=true;return;}
   // Strike: the fish that took this bait is on; now it has to be brought in.
   bBite=false;auto S=Sim();bool bOk=false;Hooked=S?S->HookFish(BaitId(),bOk):nullptr;
   if(!bOk || !Hooked.IsValid()){Status=S?S->LastMessage:FString();if(Bait!=0)Bait=0;Timer=1.6f;bRecast=true;return;}
   Fight=FMareFishFight();Fight.Strength=float(UMareSimulation::Number(Hooked,TEXT("strength"),.3));bFight=true;bHeld=true;bWasPulling=false;   // i18n:skip
   Status=TEXT("Fisgado! Recolha a linha!");
  }
  void PickBait(int32 Index)
  {
   if(bFight || !Baits.IsValidIndex(Index))return;auto S=Sim();if(!S)return;
   const FString Id=UMareSimulation::String(Baits[Index],TEXT("id"));
   // No units of a paid bait: the same key buys a pack at the pier.
   if(S->BaitCount(Id)<=0){const bool bBought=S->BuyBait(Id);Status=S->LastMessage;if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),bBought?TEXT("money_coins"):TEXT("deal_decline"),nullptr,.6f);if(!bBought)return;}
   Bait=Index;
  }
  bool bBook=false,bAuto=false;
 private:
  TWeakObjectPtr<AMareController> Owner;TArray<TSharedPtr<FJsonObject>> Baits;TSharedPtr<FJsonObject> Hooked;FMareFishFight Fight;
  FString Status,LandedId;double Last=0;float Timer=0,Window=1.1f;bool bBite=false,bRecast=false,bFight=false,bHeld=false,bWasPulling=false;int32 Caught=0,Bait=0;
  UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetSimulation():nullptr;}
  static bool IsAction(const FKey& K){return K==EKeys::E || K==EKeys::SpaceBar || K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom || K==EKeys::Gamepad_FaceButton_Left;}
  FString BaitId()const{return Baits.IsValidIndex(Bait)?UMareSimulation::String(Baits[Bait],TEXT("id")):FString(TEXT("massa"));}   // i18n:skip
  FString FishName()const{return Hooked.IsValid()?UMareSimulation::String(Hooked,TEXT("name")):FString();}
  int32 Count(const TSharedPtr<FJsonObject>& F)const{auto S=Sim();return S?int32(UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("fish")),UMareSimulation::String(F,TEXT("id")))):0;}
  FString BookLine(const TSharedPtr<FJsonObject>& F)const
  {
   auto S=Sim();const int32 N=Count(F);
   if(N<=0)return FString::Printf(TEXT("??? · %s"),*MareLoc::Text(UMareSimulation::String(F,TEXT("hint"))).ToString());
   const double Best=S?UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("fish")),TEXT("best_")+UMareSimulation::String(F,TEXT("id"))):0;
   return MareLoc::Text(FString::Printf(TEXT("%s · pescados: %d · recorde: %.0f cm"),*UMareSimulation::String(F,TEXT("name")),N,Best)).ToString();
  }
  FString BaitLine()const
  {
   auto S=Sim();FString Line=MareLoc::Text(TEXT("Isca: ")).ToString();
   for(int32 I=0;I<Baits.Num();++I){const FString Id=UMareSimulation::String(Baits[I],TEXT("id"));const FString Name=MareLoc::Text(UMareSimulation::String(Baits[I],TEXT("name"))).ToString();
    const int32 Pack=int32(UMareSimulation::Number(Baits[I],TEXT("pack")));const int32 Have=S?S->BaitCount(Id):0;   // i18n:skip
    FString Part=Pack<=0?FString::Printf(TEXT("%d %s"),I+1,*Name):Have>0?FString::Printf(TEXT("%d %s x%d"),I+1,*Name,Have)
     :MareLoc::Text(FString::Printf(TEXT("%d %s (R$ %.0f por %d)"),I+1,*Name,UMareSimulation::Number(Baits[I],TEXT("cost")),Pack)).ToString();
    if(I==Bait)Part=TEXT("[")+Part+TEXT("]");
    Line+=(I?TEXT("  ·  "):TEXT(""))+Part;}
   return Line;
  }
  void Cast()
  {
   auto S=Sim();float Low=2,High=6;
   if(S){const TArray<TSharedPtr<FJsonValue>>* Wait=nullptr;if(S->LeisureDefs()->TryGetArrayField(TEXT("bite_wait"),Wait) && Wait->Num()==2){Low=(*Wait)[0]->AsNumber();High=(*Wait)[1]->AsNumber();}
    Window=UMareSimulation::Number(S->LeisureDefs(),TEXT("bite_window"),1.1);
    if(S->BaitCount(BaitId())<=0)Bait=0;}   // the paid bait ran out: back to bread dough
   Timer=FMath::FRandRange(Low,High);Status=TEXT("Linha na água... espere.");bBite=false;LandedId.Reset();
   if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("bar_pour"),nullptr,.5f);
  }
  void EndFight()
  {
   bFight=false;bHeld=false;auto S=Sim();
   if(Fight.Result==1 && S){S->LandFish(Hooked);++Caught;Status=S->LastMessage;LandedId=UMareSimulation::String(Hooked,TEXT("id"));if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("deal_accept"));}
   else{Status=Fight.Result==-1?FString::Printf(TEXT("A linha arrebentou! %s foi embora com a isca."),*FishName()):FString::Printf(TEXT("%s se soltou do anzol."),*FishName());
    if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("deal_decline"),nullptr,.6f);}
   Hooked.Reset();Timer=Fight.Result==1?4.2f:2.4f;bRecast=true;   // a catch stays on show a little longer (its picture)
  }
 };
}

TSharedRef<SWidget> MareFishing::Create(AMareController* Owner)
{
 const TSharedRef<SMareFishingGame> Game=SNew(SMareFishingGame).Owner(Owner);GFishing=Game;return Game;
}

FString MareFishing::QA(const FString& Cmd)
{
 auto Game=GFishing.Pin();if(!Game.IsValid())return TEXT("no game");   // i18n:skip
 FString A,B;if(!Cmd.Split(TEXT(":"),&A,&B))A=Cmd;
 if(A==TEXT("bait"))Game->PickBait(FCString::Atoi(*B));   // i18n:skip
 else if(A==TEXT("bite"))Game->QABite();   // i18n:skip
 else if(A==TEXT("strike"))Game->Press();   // i18n:skip
 else if(A==TEXT("hold"))Game->QAHold(B!=TEXT("0"));   // i18n:skip
 else if(A==TEXT("step"))Game->Advance(FCString::Atof(*B));   // i18n:skip
 else if(A==TEXT("book"))Game->bBook=!Game->bBook;   // i18n:skip
 else if(A==TEXT("auto"))Game->bAuto=B!=TEXT("0");   // i18n:skip
 return Game->State();
}

// QA: "mare.Fish start | bait:1 | bite | strike | hold:1 | hold:0 | step:0.5 | book | state" on the open fishing panel.
static FAutoConsoleCommandWithWorldAndArgs MareFishCommand(TEXT("mare.Fish"),TEXT("QA: drives the pier fishing panel (bait:<i>, bite, strike, hold:<0|1>, step:<s>, book, state)."),   // i18n:skip
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(Args.Num() && Args[0]==TEXT("start"))if(auto PC=World?Cast<AMareController>(UGameplayStatics::GetPlayerController(World,0)):nullptr)PC->StartFishing();   // i18n:skip
  // The call stays outside UE_LOG: Shipping compiles the log line away together with whatever its arguments would do
  // (11/11: in the packaged game only "start" had any effect).
  const FString Result=MareFishing::QA(Args.Num()?Args[0]:FString(TEXT("state")));
  UE_LOG(LogTemp,Display,TEXT("MARE_FISH %s"),*Result);}));
