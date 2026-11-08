// Kiosk payment (07/11, Sergio, pointing at the reference game: "sistema de pagamento assim"): after the player hands
// over the last item of an order, the customer pays in cash or by card. The price was already charged by Deliver; this
// is the skill on top: the change built from the drawer (notes and coins in reais) or the total typed on the terminal.
// Exact change earns a tip and five stars; wrong change costs stars (short) or money (too much). Esc lets the customer
// pay alone, without tip. Values in Content/Data/payment.json; all money in cents.
#include "MarePayment.h"
#include "MareSimulation.h"
#include "MareGame.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "MareAudioWorld.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "Kismet/GameplayStatics.h"

namespace
{
 int64 Cents(double Reais){return (int64)FMath::RoundToDouble(Reais*100.0);}
 FString Reais(int64 C){return FString::Printf(TEXT("R$ %lld,%02lld"),C/100,FMath::Abs(C%100));}
}

// ---------------------------------------------------------------------------------------------------------------------
// Rules (UMareSimulation)

TSharedPtr<FJsonObject> UMareSimulation::PaymentDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/payment.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

FMarePay UMareSimulation::MakePayment(const FString& Customer,double Total,FRandomStream& Rng) const
{
 FMarePay Pay;Pay.Customer=Customer;Pay.Total=Cents(Total);
 const auto D=PaymentDefs();
 if(Rng.FRand()>=Number(D,TEXT("cash_share"),.6)){Pay.bCard=true;return Pay;}
 // The smallest note that covers the total, sometimes a bigger one (a R$ 50 note for a R$ 18 coconut).
 TArray<int64> Notes;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
 if(D->TryGetArrayField(TEXT("given"),L))for(const auto& V:*L)Notes.Add(Cents(V->AsNumber()));
 if(Notes.IsEmpty())Notes={500,1000,2000,5000,10000};
 Notes.Sort();
 int32 First=Notes.IndexOfByPredicate([&](int64 N){return N>=Pay.Total;});
 if(First==INDEX_NONE){Pay.Given=((Pay.Total+9999)/10000)*10000;return Pay;}   // a big order: hundreds
 if(First+1<Notes.Num() && Rng.FRand()<Number(D,TEXT("given_bigger"),.45))++First;
 Pay.Given=Notes[First];
 return Pay;
}

double UMareSimulation::SettlePayment(const FMarePay& Pay,int64 Answer,bool bSkip)
{
 const auto D=PaymentDefs();double Stars=Number(D,TEXT("stars_skip"),3.5);
 if(bSkip){LastMessage=Pay.Customer+TEXT(" pagou sozinho, sem gorjeta.");}
 else if(Pay.bCard){
  if(Answer==Pay.Total){
   const int64 Tip=FMath::Max<int64>(0,(int64)FMath::RoundToDouble(Pay.Total*Number(D,TEXT("tip_card"),.05)));
   if(Tip>0)Book(Tip/100.0,TEXT("Gorjeta no cartão"));
   Stars=Number(D,TEXT("stars_exact"),5);LastMessage=FString::Printf(TEXT("Cartão aprovado! %s deixou %s de gorjeta."),*Pay.Customer,*Reais(Tip));}
  else{Stars=Number(D,TEXT("stars_short"),2);LastMessage=Pay.Customer+TEXT(" estranhou o valor na maquininha.");}}
 else{
  const int64 Diff=Answer-Pay.ChangeDue();
  if(Diff==0){
   const int64 Tip=FMath::Max<int64>(0,(int64)FMath::RoundToDouble(Pay.Total*Number(D,TEXT("tip_exact"),.1)));
   if(Tip>0)Book(Tip/100.0,TEXT("Gorjeta pelo troco certo"));
   Stars=Number(D,TEXT("stars_exact"),5);LastMessage=FString::Printf(TEXT("Troco certinho! %s deixou %s de gorjeta."),*Pay.Customer,*Reais(Tip));}
  else if(Diff<0){Stars=Number(D,TEXT("stars_short"),2);LastMessage=FString::Printf(TEXT("Faltou %s no troco de %s."),*Reais(-Diff),*Pay.Customer);}
  else{Book(-Diff/100.0,TEXT("Troco a mais"));Stars=Number(D,TEXT("stars_over"),4);
   LastMessage=FString::Printf(TEXT("Você deu %s a mais de troco para %s."),*Reais(Diff),*Pay.Customer);}}
 AddRating(Stars);Save();
 return Stars;
}

// ---------------------------------------------------------------------------------------------------------------------
// Screen

class SMarePayment;
static TWeakPtr<SMarePayment> GPayment;

class SMarePayment : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMarePayment){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_ARGUMENT(FMarePay,Pay) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  using namespace MareNotebook;Owner=Args._Owner;Pay=Args._Pay;auto S=Sim();
  const auto D=S?S->PaymentDefs():MakeShared<FJsonObject>();
  auto Screen=SNew(SVerticalBox);
  auto Line=[&](const FString& Label,TFunction<FString()> Value,const FLinearColor& C){Screen->AddSlot().AutoHeight().Padding(0,2)[SNew(SHorizontalBox)
   +SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Text(MareLoc::Text(Label)).Font(Body(15,true)).ColorAndOpacity(FLinearColor::White)]
   +SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Text_Lambda([Value](){return FText::FromString(Value());}).Font(Body(15,true)).ColorAndOpacity(C)]];};
  Line(TEXT("Total"),[this](){return Reais(Pay.Total);},FLinearColor::White);
  if(Pay.bCard)Line(TEXT("Cartão · digite o total"),[this](){return Typed.IsEmpty()?FString(TEXT("_")):Reais(FCString::Atoi64(*Typed));},Hex(255,236,150));
  else{Line(TEXT("Recebido"),[this](){return Reais(Pay.Given);},FLinearColor::White);
   Line(TEXT("Troco"),[this](){return Reais(Pay.ChangeDue());},Hex(150,235,170));
   Line(TEXT("Dando..."),[this](){return Reais(Giving());},Hex(255,236,150));}
  auto Pad=SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8,8));
  if(Pay.bCard){
   for(const TCHAR* K:{TEXT("1"),TEXT("2"),TEXT("3"),TEXT("4"),TEXT("5"),TEXT("6"),TEXT("7"),TEXT("8"),TEXT("9"),TEXT("00"),TEXT("0")}){const FString Key(K);
    Pad->AddSlot()[Key_(Key,[this,Key](){if(Typed.Len()<7)Typed+=Key;})];}
   Pad->AddSlot()[Key_(TEXT("apagar"),[this](){Typed.LeftChopInline(1);})];}
  else{
   TArray<double> Units;for(const TCHAR* F:{TEXT("notes"),TEXT("coins")}){const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(D->TryGetArrayField(F,L))for(const auto& V:*L)Units.Add(V->AsNumber());}
   if(Units.IsEmpty())Units={100,50,20,10,5,2,1,.5,.25,.1,.05};
   for(double U:Units){const int64 C=Cents(U);Pad->AddSlot()[Key_(U>=2?FString::Printf(TEXT("R$ %.0f"),U):Reais(C),[this,C](){Given.Add(C);},U>=2)];}
   Pad->AddSlot()[Key_(TEXT("desfazer"),[this](){if(Given.Num())Given.Pop();})];}
  ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Paper).Padding(FMargin(28,22))
   [SNew(SBox).WidthOverride(620)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[HandText(TEXT("Pagamento · ")+Pay.Customer,30,Brown)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,4,0,10)[BodyText(Pay.bCard?TEXT("Pagamento no cartão: digite o valor total na maquininha e confirme."):TEXT("Pagamento em dinheiro: monte o troco com as notas e moedas da gaveta e confirme."),12.5f,Faded)]
    +SVerticalBox::Slot().AutoHeight()[SNew(SBorder).BorderImage(&ScreenBrush()).Padding(FMargin(18,12))[Screen]]
    +SVerticalBox::Slot().AutoHeight().Padding(0,14,0,0)[Pad]
    +SVerticalBox::Slot().AutoHeight().Padding(0,16,0,0)[SNew(SHorizontalBox)
     +SHorizontalBox::Slot().AutoWidth()[Key_(Pay.bCard?TEXT("OK · cobrar"):TEXT("Confirmar troco"),[this](){Finish(false);},true,true)]
     +SHorizontalBox::Slot().AutoWidth().Padding(14,0,0,0).VAlign(VAlign_Center)[SNew(SButton).ButtonStyle(&Plain()).OnClicked_Lambda([this](){Finish(true);return FReply::Handled();})
      [HandText(TEXT("deixar o cliente pagar sozinho (Esc)"),16,Pencil)]]]]]];
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Finish(true);return FReply::Handled();}
  if(K==EKeys::Enter || K==EKeys::Gamepad_FaceButton_Bottom){Finish(false);return FReply::Handled();}
  if(K==EKeys::BackSpace){if(Pay.bCard)Typed.LeftChopInline(1);else if(Given.Num())Given.Pop();return FReply::Handled();}
  if(Pay.bCard){const FString N=K.GetDisplayName().ToString();if(N.Len()==1 && FChar::IsDigit(N[0]) && Typed.Len()<7){Typed+=N;return FReply::Handled();}}
  return FReply::Unhandled();
 }
 int64 Giving()const{int64 T=0;for(int64 C:Given)T+=C;return T;}
 FString QA(const FString& Cmd)
 {
  FString Verb,Arg;if(!Cmd.Split(TEXT(":"),&Verb,&Arg))Verb=Cmd;
  if(Verb==TEXT("give"))Given.Add(FCString::Atoi64(*Arg));
  else if(Verb==TEXT("undo") && Given.Num())Given.Pop();
  else if(Verb==TEXT("type"))Typed=Arg;
  else if(Verb==TEXT("ok")){Finish(false);return LastResult;}
  else if(Verb==TEXT("skip")){Finish(true);return LastResult;}
  return FString::Printf(TEXT("card=%d total=%lld given=%lld due=%lld giving=%lld typed=%s"),Pay.bCard?1:0,Pay.Total,Pay.Given,Pay.ChangeDue(),Giving(),*Typed);
 }
private:
 TWeakObjectPtr<AMareController> Owner;FMarePay Pay;TArray<int64> Given;FString Typed;FString LastResult;bool bDone=false;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetSimulation():nullptr;}
 static const FSlateRoundedBoxBrush& ScreenBrush(){static const FSlateRoundedBoxBrush B(MareNotebook::Hex(28,96,110),8.f);return B;}
 static const FButtonStyle& Plain(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateNoResource()).SetPressed(FSlateNoResource());return S;}
 TSharedRef<SWidget> Key_(const FString& Label,TFunction<void()> Action,bool bNote=false,bool bMain=false)
 {
  using namespace MareNotebook;
  static const FButtonStyle NoteStyle=FButtonStyle().SetNormal(FSlateRoundedBoxBrush(Hex(196,226,184),5.f,Hex(110,150,96),1.5f)).SetHovered(FSlateRoundedBoxBrush(Hex(214,238,202),5.f,Hex(110,150,96),1.5f)).SetPressed(FSlateRoundedBoxBrush(Hex(170,206,158),5.f));
  static const FButtonStyle CoinStyle=FButtonStyle().SetNormal(FSlateRoundedBoxBrush(Hex(240,214,140),16.f,Hex(176,140,60),1.5f)).SetHovered(FSlateRoundedBoxBrush(Hex(250,228,164),16.f,Hex(176,140,60),1.5f)).SetPressed(FSlateRoundedBoxBrush(Hex(220,190,110),16.f));
  const FButtonStyle* Style=bMain?&InkButton():bNote?&NoteStyle:&CoinStyle;
  return SNew(SBox).MinDesiredWidth(bMain?180:84).HeightOverride(bMain?44:40)[SNew(SButton).ButtonStyle(Style).HAlign(HAlign_Center).VAlign(VAlign_Center)
   .OnClicked_Lambda([this,Action](){Action();if(Owner.IsValid())UMareAudioWorld::Action(Owner.Get(),TEXT("kiosk_cash"),nullptr,.25f);return FReply::Handled();})
   [SNew(STextBlock).Text(MareLoc::Text(Label)).Font(bMain?Hand(20):Body(13,true)).ColorAndOpacity(bMain?MareNotebook::Tag:Ink)]];
 }
 void Finish(bool bSkip)
 {
  if(bDone)return;auto S=Sim();if(!S)return;
  if(!bSkip && Pay.bCard && FCString::Atoi64(*Typed)!=Pay.Total && !Typed.IsEmpty()){
   // Wrong amount on the terminal: the customer refuses it, try again (no penalty yet).
   S->LastMessage=Pay.Customer+TEXT(" recusou: o valor na maquininha não bate com o total.");Typed.Empty();LastResult=S->LastMessage;return;}
  bDone=true;
  S->SettlePayment(Pay,Pay.bCard?FCString::Atoi64(*Typed):Giving(),bSkip);LastResult=S->LastMessage;
  if(Owner.IsValid())Owner->CloseBusinessGame();
 }
};

namespace MarePayment
{
 TSharedRef<SWidget> Make(AMareController* Owner,const FMarePay& Pay)
 {
  const TSharedRef<SMarePayment> W=SNew(SMarePayment).Owner(Owner).Pay(Pay);GPayment=W;return W;
 }
 bool IsOpen(){return GPayment.IsValid();}
 FString QA(const FString& Cmd){const auto P=GPayment.Pin();return P.IsValid()?P->QA(Cmd):FString(TEXT("closed"));}
}

void AMareController::OpenPayment(const FString& Customer,double Total)
{
 auto S=GetSimulation();if(!S || !GEngine || !GEngine->GameViewport || GameWidget.IsValid() || IsMainMenuOpen())return;
 // Automated runs serve customers by themselves: no modal screen that would pause them.
 {const TCHAR* Cmd=FCommandLine::Get();if(GIsAutomationTesting || FParse::Param(Cmd,TEXT("MarePreviewQA")) || FParse::Param(Cmd,TEXT("MareGraphicsQA")) || FParse::Param(Cmd,TEXT("MareBench")) || bSkipPaymentForQA)return;}
 static FRandomStream Rng(int32(FDateTime::Now().GetTicks()%100000));
 const FMarePay Pay=S->MakePayment(Customer,Total,Rng);
 ClosePhone();SetPause(true);
 const TSharedRef<SWidget> W=MarePayment::Make(this,Pay);GameWidget=W;
 GEngine->GameViewport->AddViewportWidgetContent(W,40);bShowMouseCursor=true;
 SetInputMode(FInputModeUIOnly().SetWidgetToFocus(W));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
 S->ShowTip(TEXT("payment"));
}

static FAutoConsoleCommandWithWorldAndArgs MarePayQA(TEXT("mare.Pay"),TEXT("QA payment: 'open <total>' opens the screen, else give:<cents> | undo | type:<n> | ok | skip | state."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(!World || Args.IsEmpty())return;
  if(Args[0]==TEXT("open") && Args.Num()>1){if(auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(World,0)))PC->OpenPayment(TEXT("Cliente QA"),FCString::Atod(*Args[1]));}
  UE_LOG(LogTemp,Display,TEXT("MARE_PAY %s"),*MarePayment::QA(Args[0]));}));
