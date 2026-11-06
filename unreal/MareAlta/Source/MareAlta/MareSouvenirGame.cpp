// Souvenir shop screen (CHECKLIST_EXPANSOES 3.5): three pages in the notebook style - wrap the gift of the tourist at
// the counter (three folds in the right order, the ribbon in the colour asked, quickly), arrange the shelf with crafts
// bought from the village makers, and print postcards from the player's own album photos.
#include "MareSouvenirGame.h"
#include "MareGame.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "MareSimulation.h"
#include "MareAudioWorld.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Dom/JsonValue.h"
#include "Engine/Texture2D.h"
#include "HAL/PlatformTime.h"
#include "ImageUtils.h"
#include "Misc/Paths.h"
#include "UObject/StrongObjectPtr.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
 FLinearColor JsonColor(const TSharedPtr<FJsonObject>& O)
 {
  const TArray<TSharedPtr<FJsonValue>>* C=nullptr;
  return O.IsValid() && O->TryGetArrayField(TEXT("color"),C) && C->Num()==3?FLinearColor(FColor(uint8((*C)[0]->AsNumber()*255),uint8((*C)[1]->AsNumber()*255),uint8((*C)[2]->AsNumber()*255))):FLinearColor::White;
 }
 TArray<TSharedPtr<FJsonObject>> List(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  TArray<TSharedPtr<FJsonObject>> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(O.IsValid() && O->TryGetArrayField(Key,L))for(const auto& V:*L)Out.Add(V->AsObject());return Out;
 }
 // A rounded box only draws when its radius fits the box: one brush per size.
 const FSlateRoundedBoxBrush& Round4(){static const FSlateRoundedBoxBrush B(FLinearColor::White,4.f);return B;}
 const FSlateRoundedBoxBrush& Round8(){static const FSlateRoundedBoxBrush B(FLinearColor::White,8.f);return B;}
 const FSlateRoundedBoxBrush& Swatch(){static const FSlateRoundedBoxBrush B(FLinearColor::White,8.f,MareNotebook::Hex(90,70,50),1.5f);return B;}
 const FSlateRoundedBoxBrush& FlapBrush(){static const FSlateRoundedBoxBrush B(FLinearColor::White,4.f,MareNotebook::Hex(46,112,108),2.f);return B;}
 const FSlateRoundedBoxBrush& SwatchOn(){static const FSlateRoundedBoxBrush B(FLinearColor::White,8.f,MareNotebook::Ink,3.f);return B;}
}

class SMareSouvenirGame : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareSouvenirGame){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;auto S=Sim();if(!S)return;const auto D=S->SouvenirDefs();
  for(const auto& F:List(D,TEXT("folds")))Folds.Add({UMareSimulation::String(F,TEXT("id")),UMareSimulation::String(F,TEXT("name")),FLinearColor::White});
  for(const auto& R:List(D,TEXT("ribbons")))Ribbons.Add({UMareSimulation::String(R,TEXT("id")),UMareSimulation::String(R,TEXT("name")),JsonColor(R)});
  MemoS=UMareSimulation::Number(D,TEXT("memo_s"),3);FastS=UMareSimulation::Number(D,TEXT("fast_s"),15);
  Switcher=SNew(SWidgetSwitcher)+SWidgetSwitcher::Slot()[WrapPage()]+SWidgetSwitcher::Slot()[ShelfPage()]+SWidgetSwitcher::Slot()[CardsPage()];
  auto Tabs=SNew(SHorizontalBox);
  const TCHAR* Names[]={TEXT("1. Embrulhar presente"),TEXT("2. Prateleira e artesãos"),TEXT("3. Cartões-postais")};
  for(int32 I=0;I<3;++I)Tabs->AddSlot().AutoWidth().Padding(0,0,8,0)[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(12,4)).OnClicked_Lambda([this,I](){SetTab(I);return FReply::Handled();})
   [SNew(STextBlock).Font(Hand(18)).ColorAndOpacity_Lambda([this,I](){return FSlateColor(Tab==I?Red:Ink);}).Text(MareLoc::Text(Names[I]))]];
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,40)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(26,14))
   [SNew(SBox).WidthOverride(860)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().FillWidth(1)[HandText(TEXT("Lojinha de souvenires"),28,Brown)]
     +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(Faded).Text_Lambda([this](){auto S=Sim();if(!S)return FText();
      int32 Cards=0;for(const auto& C:S->SouvenirCards())Cards+=int32(UMareSimulation::Number(C,TEXT("qty")));
      return MareLoc::Text(FString::Printf(TEXT("embrulhos na fila: %d · cartões no expositor: %d"),S->SouvenirQueue().Num(),Cards));})]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4)[Tabs]
    +SVerticalBox::Slot().AutoHeight().Padding(0,2)[SNew(STextBlock).Font(Hand(19)).ColorAndOpacity(Ink).AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(Status);})]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4)[Switcher.ToSharedRef()]
    +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[HandText(TEXT("Tab troca de página · Esc ou B sai"),14,Faded)]]]];
  SetTab(S->SouvenirQueue().Num()?0:1);
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();if(Event.IsRepeat())return FReply::Handled();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Close();return FReply::Handled();}
  if(K==EKeys::Tab || K==EKeys::Gamepad_RightShoulder){SetTab((Tab+1)%3);return FReply::Handled();}
  if(K==EKeys::Gamepad_LeftShoulder){SetTab((Tab+2)%3);return FReply::Handled();}
  if(Tab==0){
   static const FKey Digits[]={EKeys::One,EKeys::Two,EKeys::Three};
   for(int32 I=0;I<3;++I)if(K==Digits[I]){if(ButtonOrder.IsValidIndex(I))Fold(ButtonOrder[I]);return FReply::Handled();}
   static const FKey Letters[]={EKeys::Q,EKeys::W,EKeys::E,EKeys::R,EKeys::T};
   for(int32 I=0;I<5;++I)if(K==Letters[I]){PickRibbon(I);return FReply::Handled();}
   if(K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom){Deliver();return FReply::Handled();}
   if(K==EKeys::BackSpace || K==EKeys::Gamepad_FaceButton_Left){Restart();return FReply::Handled();}
  }
  return FReply::Unhandled();
 }
 virtual void Tick(const FGeometry& Geometry,const double Time,const float Delta) override
 {
  SCompoundWidget::Tick(Geometry,Time,Delta);
  if(bResult && FPlatformTime::Seconds()>=ResultUntil){bResult=false;NextGift();}
 }
 // QA (MareSouvenirGame::QA).
 FString QA(const FString& Cmd)
 {
  auto S=Sim();if(!S)return TEXT("none");FString A,B;const bool bArg=Cmd.Split(TEXT(":"),&A,&B);if(!bArg)A=Cmd;
  if(A==TEXT("tab")){SetTab(FCString::Atoi(*B));return TEXT("ok");}
  if(A==TEXT("fold")){for(int32 I=0;I<Folds.Num();++I)if(Folds[I].Id==B)Fold(I);return FString::Join(Done,TEXT(","));}
  if(A==TEXT("ribbon")){for(int32 I=0;I<Ribbons.Num();++I)if(Ribbons[I].Id==B)PickRibbon(I);return Ribbon>=0?Ribbons[Ribbon].Id:TEXT("-");}
  if(A==TEXT("restart")){Restart();return TEXT("ok");}
  if(A==TEXT("deliver")){Deliver();return S->LastMessage;}
  if(A==TEXT("asked"))return S->SouvenirQueue().Num()?UMareSimulation::String(S->SouvenirQueue()[0],TEXT("ribbon")):TEXT("-");
  if(A==TEXT("perfect") || A==TEXT("wrong")){
   if(S->SouvenirQueue().IsEmpty())return TEXT("empty");const bool bRight=A==TEXT("perfect");Restart();
   for(int32 I=0;I<Folds.Num();++I)Fold(bRight?I:Folds.Num()-1-I);
   const FString Asked=UMareSimulation::String(S->SouvenirQueue()[0],TEXT("ribbon"));
   for(int32 I=0;I<Ribbons.Num();++I)if((Ribbons[I].Id==Asked)==bRight){PickRibbon(I);break;}
   Deliver();return S->LastMessage;}
  if(A==TEXT("memo"))return FString::Printf(TEXT("%d"),MemoVisible()?1:0);
  if(A==TEXT("hidememo")){ShownAt=FPlatformTime::Seconds()-MemoS-1;return TEXT("ok");}
  return TEXT("?");
 }
private:
 struct FItem{FString Id,Name;FLinearColor Color;};
 TWeakObjectPtr<AMareController> Owner;TSharedPtr<SWidgetSwitcher> Switcher;TSharedPtr<SVerticalBox> ShelfBox,CardBox;
 TArray<FItem> Folds,Ribbons;TArray<int32> ButtonOrder;TArray<FString> Done;FString Status;
 int32 Tab=0,Ribbon=-1,SelectedSlot=0;bool bCrumpled=false,bResult=false,bHasGift=false;double ShownAt=0,ResultUntil=0,MemoS=3,FastS=15;
 FLinearColor GiftColor=FLinearColor::White;
 TArray<TStrongObjectPtr<UTexture2D>> Thumbs;TArray<TSharedPtr<FSlateBrush>> ThumbBrushes;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetSimulation():nullptr;}
 bool MemoVisible()const{return bHasGift && FPlatformTime::Seconds()-ShownAt<MemoS;}
 bool HasFold(const FString& Id)const{return Done.Contains(Id);}
 void Close(){if(Owner.IsValid())Owner->CloseBusinessGame();}
 void Sound(const TCHAR* Cue,float Volume=.6f){if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),Cue,nullptr,Volume);}

 void SetTab(int32 I)
 {
  Tab=FMath::Clamp(I,0,2);Switcher->SetActiveWidgetIndex(Tab);
  if(Tab==0)NextGift();else if(Tab==1){RebuildShelf();Status=TEXT("Escolha um lugar da prateleira e ponha nele o artesanato dos fundos. A vitrine da frente vende muito mais que o fundo da loja.");}
  else{RebuildCards();Status=TEXT("As fotos do seu álbum (tecla P) viram cartões-postais: com o farol, a baleia ou o pôr do sol vendem mais caro.");}
 }

 // ---------- Page 1: wrap the gift ----------
 TSharedRef<SWidget> WrapPage()
 {
  using namespace MareNotebook;
  const FLinearColor GiftPaper=Hex(120,196,190);   // teal gift paper
  auto Flap=[this,GiftPaper](EHorizontalAlignment H,EVerticalAlignment V,float W,float Ht,const FString& Id){
   return SNew(SBox).HAlign(H).VAlign(V)[SNew(SBox).WidthOverride(W).HeightOverride(Ht).Visibility_Lambda([this,Id](){return HasFold(Id)?EVisibility::HitTestInvisible:EVisibility::Hidden;})
    [SNew(SBorder).BorderImage(&FlapBrush()).Padding(0).BorderBackgroundColor_Lambda([this,GiftPaper](){
     // The folded flap shows the paper's lighter back; a crumpled one is darker and greyer.
     return FSlateColor(bCrumpled?FLinearColor::LerpUsingHSV(GiftPaper,FLinearColor(.45f,.45f,.42f),.45f):FLinearColor::LerpUsingHSV(GiftPaper,FLinearColor::White,.45f));})]];};
  auto RibbonColor=[this](){return Ribbon>=0?Ribbons[Ribbon].Color:FLinearColor(0,0,0,0);};
  auto FoldButtons=SNew(SHorizontalBox);
  for(int32 P=0;P<3;++P)FoldButtons->AddSlot().AutoWidth().Padding(0,0,8,0)[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(12,5))
   .OnClicked_Lambda([this,P](){if(ButtonOrder.IsValidIndex(P))Fold(ButtonOrder[P]);return FReply::Handled();})
   [SNew(STextBlock).Font(Hand(17)).ColorAndOpacity(MareNotebook::Tag).Text_Lambda([this,P](){return MareLoc::Text(ButtonOrder.IsValidIndex(P) && Folds.IsValidIndex(ButtonOrder[P])?
    FString::Printf(TEXT("%d. %s"),P+1,*Folds[ButtonOrder[P]].Name):FString());})]];
  auto Swatches=SNew(SHorizontalBox);const TCHAR* Keys[]={TEXT("Q"),TEXT("W"),TEXT("E"),TEXT("R"),TEXT("T")};
  for(int32 I=0;I<Ribbons.Num() && I<5;++I)Swatches->AddSlot().AutoWidth().Padding(0,0,8,0)[SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(SButton).ButtonStyle(&Plain()).ContentPadding(0).OnClicked_Lambda([this,I](){PickRibbon(I);return FReply::Handled();})
    [SNew(SBox).WidthOverride(46).HeightOverride(30)[SNew(SBorder).Padding(0).BorderImage_Lambda([this,I]()->const FSlateBrush*{return Ribbon==I?&SwatchOn():&Swatch();}).BorderBackgroundColor(Ribbons[I].Color)]]]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(STextBlock).Font(Hand(14)).ColorAndOpacity(Faded).Text(MareLoc::Text(FString::Printf(TEXT("%s %s"),Keys[I],*Ribbons[I].Name)))]];
  return SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(22)).ColorAndOpacity(Red).AutoWrapText(true).Text_Lambda([this](){return MareLoc::Text(OrderLine());})]
   +SVerticalBox::Slot().AutoHeight().Padding(0,6)[SNew(SHorizontalBox)
    // The gift seen from above: the craft in its box on the paper, the flaps folding over it, then the ribbon and bow.
    +SHorizontalBox::Slot().AutoWidth().Padding(0,0,22,0)[SNew(SBox).WidthOverride(280).HeightOverride(180)[SNew(SOverlay)
     +SOverlay::Slot()[SNew(SBorder).BorderImage(&Round8()).Padding(0).BorderBackgroundColor_Lambda([this,GiftPaper](){return FSlateColor(bHasGift?(bCrumpled?GiftPaper*.8f:GiftPaper):Kraft);})]
     +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(150).HeightOverride(96).Visibility_Lambda([this](){return bHasGift?EVisibility::HitTestInvisible:EVisibility::Hidden;})
      [SNew(SBorder).BorderImage(&Round4()).Padding(0).BorderBackgroundColor_Lambda([this](){return FSlateColor(GiftColor);})]]
     +SOverlay::Slot()[Flap(HAlign_Left,VAlign_Fill,92,180,TEXT("laterais"))]
     +SOverlay::Slot()[Flap(HAlign_Right,VAlign_Fill,92,180,TEXT("laterais"))]
     +SOverlay::Slot()[Flap(HAlign_Fill,VAlign_Bottom,280,62,TEXT("fundo"))]
     +SOverlay::Slot()[Flap(HAlign_Fill,VAlign_Top,280,62,TEXT("topo"))]
     +SOverlay::Slot().HAlign(HAlign_Center)[SNew(SBox).WidthOverride(16)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).Padding(0).BorderBackgroundColor_Lambda([RibbonColor](){return FSlateColor(RibbonColor());})]]
     +SOverlay::Slot().VAlign(VAlign_Center)[SNew(SBox).HeightOverride(16)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).Padding(0).BorderBackgroundColor_Lambda([RibbonColor](){return FSlateColor(RibbonColor());})]]
     +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(44).HeightOverride(28)[SNew(SBorder).BorderImage(&Round8()).Padding(0)
      .BorderBackgroundColor_Lambda([RibbonColor](){const FLinearColor C=RibbonColor();return FSlateColor(C.A>0?C*.82f:C);})]]]]
    +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Top)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[SNew(SBorder).BorderImage(&Note()).Padding(FMargin(10,4))
      [HandText(TEXT("Embrulho bem feito: primeiro as laterais, depois o fundo e por último o topo."),16,Ink)]]
     +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Dobras do papel"),17,Faded)]
     +SVerticalBox::Slot().AutoHeight().Padding(0,2,0,8)[FoldButtons]
     +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Fita"),17,Faded)]
     +SVerticalBox::Slot().AutoHeight().Padding(0,2,0,6)[Swatches]
     +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(17)).ColorAndOpacity(Faded).Text_Lambda([this](){
      return MareLoc::Text(bHasGift?FString::Printf(TEXT("Tempo: %.0f s (capricho rápido até %.0f s)"),FPlatformTime::Seconds()-ShownAt,FastS):FString());})]
     +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[SNew(SHorizontalBox)
      +SHorizontalBox::Slot().AutoWidth().Padding(0,0,10,0)[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Restart();return FReply::Handled();})[InkLabel(TEXT("Papel novo (Backspace)"),16)]]
      +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).ButtonStyle(&InkButton()).ContentPadding(FMargin(14,5)).OnClicked_Lambda([this](){Deliver();return FReply::Handled();})[InkLabel(TEXT("Entregar (Enter)"),16)]]]]];
 }
 FString OrderLine()const
 {
  auto S=Sim();if(!S || !bHasGift || S->SouvenirQueue().IsEmpty())return TEXT("Ninguém esperando embrulho agora.");
  const auto O=S->SouvenirQueue()[0];
  // The ribbon colour is said once (memo_s seconds): then the player has to remember it.
  if(MemoVisible())return S->SouvenirGiftLine(O);
  const auto C=S->SouvenirCraft(UMareSimulation::String(O,TEXT("item")));
  return FString::Printf(TEXT("%s espera o embrulho de %s (qual era a cor da fita?)"),*UMareSimulation::String(O,TEXT("name")),C.IsValid()?*UMareSimulation::String(C,TEXT("name")):TEXT("uma lembrança"));
 }
 void NextGift()
 {
  auto S=Sim();Done.Empty();Ribbon=-1;bCrumpled=false;bResult=false;ShownAt=FPlatformTime::Seconds();
  bHasGift=S && S->SouvenirQueue().Num()>0;
  if(!bHasGift){if(Tab==0)Status=TEXT("Quando um turista comprar e pedir embrulho, ele espera aqui no balcão.");return;}
  const auto O=S->SouvenirQueue()[0];GiftColor=JsonColor(S->SouvenirCraft(UMareSimulation::String(O,TEXT("item"))));
  // The fold buttons change places with every customer: the order has to be known, not the position.
  ButtonOrder={0,1,2};const uint32 Seed=FCrc::StrCrc32(*UMareSimulation::String(O,TEXT("name")))+uint32(UMareSimulation::Number(O,TEXT("since")));
  for(int32 I=2;I>0;--I)ButtonOrder.Swap(I,int32((Seed>>(I*5))%uint32(I+1)));
  Status=TEXT("Dobre o papel na ordem certa e escolha a fita que o cliente pediu.");
 }
 void Restart(){if(!bHasGift || bResult)return;Done.Empty();Ribbon=-1;bCrumpled=false;Status=TEXT("Papel novo na mesa.");}
 void Fold(int32 I)
 {
  if(!bHasGift || bResult || !Folds.IsValidIndex(I) || HasFold(Folds[I].Id))return;
  if(Done.Num()!=I)bCrumpled=true;   // folds out of order crumple the paper
  Done.Add(Folds[I].Id);Sound(TEXT("deal_accept"),.25f);
  Status=bCrumpled?TEXT("Ops, essa dobra fora de ordem amassou o papel. Pode seguir ou pegar papel novo."):Done.Num()==Folds.Num()?TEXT("Papel dobrado certinho. Agora a fita!"):TEXT("Boa dobra.");
 }
 void PickRibbon(int32 I){if(!bHasGift || bResult || !Ribbons.IsValidIndex(I))return;if(Done.Num()<Folds.Num()){Status=TEXT("Termine as dobras antes da fita.");return;}Ribbon=I;Status=TEXT("Fita ")+Ribbons[I].Name+TEXT(". Entregue!");}
 void Deliver()
 {
  auto S=Sim();if(!S || !bHasGift || bResult)return;
  if(Done.Num()<Folds.Num() || Ribbon<0){Status=TEXT("Falta terminar: dobre o papel e escolha a fita.");return;}
  const auto R=S->WrapGift(Done,Ribbons[Ribbon].Id,FPlatformTime::Seconds()-ShownAt);
  Status=S->LastMessage;bResult=true;ResultUntil=FPlatformTime::Seconds()+2.4;
  Sound(R.Hits==3?TEXT("money_coins"):R.Hits>0?TEXT("deal_accept"):TEXT("deal_decline"));
 }

 // ---------- Page 2: shelf and village makers ----------
 TSharedRef<SWidget> ShelfPage(){return SAssignNew(ShelfBox,SVerticalBox);}
 void RebuildShelf()
 {
  using namespace MareNotebook;auto S=Sim();if(!S || !ShelfBox.IsValid())return;ShelfBox->ClearChildren();
  const auto D=S->SouvenirDefs();const auto Slots=List(D,TEXT("slots"));const auto Shelf=S->SouvenirShelf();
  ShelfBox->AddSlot().AutoHeight()[HandText(TEXT("Prateleira (clique para escolher o lugar)"),17,Faded)];
  for(int32 I=0;I<Slots.Num() && I<Shelf.Num();++I){
   const auto C=S->SouvenirCraft(UMareSimulation::String(Shelf[I],TEXT("item")));const int32 Qty=int32(UMareSimulation::Number(Shelf[I],TEXT("qty")));
   const FString What=C.IsValid() && Qty>0?FString::Printf(TEXT("%s · %d peça(s) · R$ %.0f"),*UMareSimulation::String(C,TEXT("name")),Qty,S->SouvenirPrice(C)):FString(TEXT("vazio"));
   ShelfBox->AddSlot().AutoHeight().Padding(0,1)[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[SNew(SBox).WidthOverride(14).HeightOverride(14)[SNew(SBorder).BorderImage(&Round4()).Padding(0)
     .BorderBackgroundColor(C.IsValid() && Qty>0?JsonColor(C):FLinearColor(0,0,0,.1f))]]
    +SHorizontalBox::Slot().FillWidth(1)[SNew(SButton).ButtonStyle(&Plain()).ContentPadding(FMargin(4,1)).OnClicked_Lambda([this,I](){SelectedSlot=I;RebuildShelf();return FReply::Handled();})
     [SNew(STextBlock).Font(Hand(18)).ColorAndOpacity(SelectedSlot==I?Red:Ink).Text(MareLoc::Text(FString::Printf(TEXT("%s%s (vende x%.1f): %s"),SelectedSlot==I?TEXT("» "):TEXT(""),
      *UMareSimulation::String(Slots[I],TEXT("name")),UMareSimulation::Number(Slots[I],TEXT("mult"),1),*What)))]]
    +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(8,1)).Visibility(C.IsValid() && Qty>0?EVisibility::Visible:EVisibility::Collapsed)
     .OnClicked_Lambda([this,I](){if(auto S=Sim()){S->PlaceSouvenir(I,FString());Status=S->LastMessage.IsEmpty()?TEXT("Lugar esvaziado: as peças voltaram para os fundos."):S->LastMessage;}RebuildShelf();return FReply::Handled();})
     [SNew(STextBlock).Font(Hand(15)).ColorAndOpacity(Ink).Text(MareLoc::Text(TEXT("tirar")))]]];}
  ShelfBox->AddSlot().AutoHeight().Padding(0,8,0,0)[HandText(TEXT("Artesãos da vila (compre para os fundos e ponha na prateleira)"),17,Faded)];
  const FString SlotName=Slots.IsValidIndex(SelectedSlot)?UMareSimulation::String(Slots[SelectedSlot],TEXT("where")):FString();
  const int32 Batch=int32(UMareSimulation::Number(D,TEXT("buy_batch"),4));
  for(const auto& C:List(D,TEXT("crafts"))){
   const FString Id=UMareSimulation::String(C,TEXT("id")),Chapter=UMareSimulation::String(C,TEXT("chapter"));const bool bLocked=!Chapter.IsEmpty() && !S->IsChapterDone(Chapter);
   const int32 Left=S->SouvenirMakerLeft(Id),Back=S->SouvenirBackStock(Id);
   const FString Line=bLocked?FString::Printf(TEXT("%s · %s (termine a história na vila)"),*UMareSimulation::String(C,TEXT("name")),*UMareSimulation::String(C,TEXT("maker")))
    :FString::Printf(TEXT("%s · %s · paga R$ %.0f, vende R$ %.0f · hoje ainda: %d · nos fundos: %d"),*UMareSimulation::String(C,TEXT("name")),*UMareSimulation::String(C,TEXT("maker")),
     UMareSimulation::Number(C,TEXT("cost")),S->SouvenirPrice(C),Left,Back);
   ShelfBox->AddSlot().AutoHeight().Padding(0,1)[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,6,0)[SNew(SBox).WidthOverride(14).HeightOverride(14)[SNew(SBorder).BorderImage(&Round4()).Padding(0).BorderBackgroundColor(JsonColor(C))]]
    +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[SNew(STextBlock).Font(Hand(16)).ColorAndOpacity(bLocked?Faded:Ink).AutoWrapText(true).Text(MareLoc::Text(Line))]
    +SHorizontalBox::Slot().AutoWidth().Padding(4,0)[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(8,1)).IsEnabled(!bLocked && Left>0)
     .OnClicked_Lambda([this,Id](){if(auto S=Sim()){S->BuySouvenirCraft(Id);Status=S->LastMessage;Sound(TEXT("deal_accept"),.4f);}RebuildShelf();return FReply::Handled();})
     [SNew(STextBlock).Font(Hand(15)).ColorAndOpacity(Ink).Text(MareLoc::Text(bLocked?FString(TEXT("bloqueado")):Left>0?FString::Printf(TEXT("comprar %d"),FMath::Min(Batch,Left)):FString(TEXT("esgotado hoje"))))]]
    +SHorizontalBox::Slot().AutoWidth()[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(8,1)).IsEnabled(Back>0)
     .OnClicked_Lambda([this,Id](){if(auto S=Sim()){S->PlaceSouvenir(SelectedSlot,Id);Status=S->LastMessage;}RebuildShelf();return FReply::Handled();})
     [SNew(STextBlock).Font(Hand(15)).ColorAndOpacity(Ink).Text(MareLoc::Text(TEXT("pôr ")+SlotName))]]];}
 }

 // ---------- Page 3: postcards from the album ----------
 TSharedRef<SWidget> CardsPage(){return SAssignNew(CardBox,SVerticalBox);}
 void RebuildCards()
 {
  using namespace MareNotebook;auto S=Sim();if(!S || !CardBox.IsValid())return;CardBox->ClearChildren();
  const TArray<TSharedPtr<FJsonValue>>* Album=nullptr;UMareSimulation::Object(S->State,TEXT("prog"))->TryGetArrayField(TEXT("album"),Album);
  TArray<TSharedPtr<FJsonObject>> Photos;
  if(Album)for(int32 I=Album->Num()-1;I>=0 && Photos.Num()<4;--I){const auto P=(*Album)[I]->AsObject();if(FPaths::FileExists(UMareSimulation::String(P,TEXT("file"))))Photos.Add(P);}
  if(Photos.IsEmpty()){CardBox->AddSlot().AutoHeight().Padding(0,10)[HandText(TEXT("O álbum está vazio. Tire fotos pelo resort com a tecla P: o farol aceso, as baleias, o pôr do sol..."),18,Faded)];}
  Thumbs.Reset();ThumbBrushes.Reset();auto Row=SNew(SHorizontalBox);
  const auto D=S->SouvenirDefs();const int32 Batch=int32(UMareSimulation::Number(D,TEXT("card_batch"),5));const double Cost=UMareSimulation::Number(D,TEXT("card_cost"),1.5)*Batch;
  for(const auto& P:Photos){
   const FString File=UMareSimulation::String(P,TEXT("file"));const TArray<TSharedPtr<FJsonValue>>* Subs=nullptr;P->TryGetArrayField(TEXT("subjects"),Subs);const int32 N=Subs?Subs->Num():0;
   TSharedPtr<FSlateBrush> Brush=MakeShared<FSlateBrush>();
   if(UTexture2D* Tex=FImageUtils::ImportFileAsTexture2D(File)){Thumbs.Emplace(Tex);Brush->SetResourceObject(Tex);Brush->ImageSize=FVector2D(184,104);}
   ThumbBrushes.Add(Brush);
   int32 Stock=0;for(const auto& C:S->SouvenirCards())if(UMareSimulation::String(C,TEXT("file"))==File)Stock=int32(UMareSimulation::Number(C,TEXT("qty")));
   Row->AddSlot().AutoWidth().Padding(0,0,10,0)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor::White).Padding(4)
     [SNew(SBox).WidthOverride(184).HeightOverride(104)[SNew(SImage).Image(Brush.Get())]]]
    +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Font(Hand(15)).ColorAndOpacity(Faded).Text(MareLoc::Text(FString::Printf(TEXT("dia %.0f · %d atração(ões) · R$ %.0f cada · no expositor: %d"),
     UMareSimulation::Number(P,TEXT("day"),1),N,S->SouvenirCardPrice(N),Stock)))]
    +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left)[SNew(SButton).ButtonStyle(&TagButton()).ContentPadding(FMargin(8,1))
     .OnClicked_Lambda([this,File,N](){if(auto S=Sim()){S->PrintPostcards(File,N);Status=S->LastMessage;Sound(TEXT("deal_accept"),.4f);}RebuildCards();return FReply::Handled();})
     [SNew(STextBlock).Font(Hand(15)).ColorAndOpacity(Ink).Text(MareLoc::Text(FString::Printf(TEXT("imprimir %d (R$ %.1f)"),Batch,Cost)))]]];}
  CardBox->AddSlot().AutoHeight().Padding(0,4)[Row];
 }
};

namespace
{
 TWeakPtr<SMareSouvenirGame> GSouvenir;
}
TSharedRef<SWidget> MareSouvenirGame::Make(AMareController* Owner)
{
 const TSharedRef<SMareSouvenirGame> W=SNew(SMareSouvenirGame).Owner(Owner);GSouvenir=W;return W;
}
bool MareSouvenirGame::IsOpen(){return GSouvenir.IsValid();}
FString MareSouvenirGame::QA(const FString& Cmd){const auto W=GSouvenir.Pin();return W.IsValid()?W->QA(Cmd):TEXT("no game");}
