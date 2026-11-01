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
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SNullWidget.h"
#include "Brushes/SlateRoundedBoxBrush.h"

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
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 TSharedRef<SWidget> Button(const FString& Label,TFunction<void()> Action)
 {
  return SNew(SButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(8,5)).OnClicked_Lambda([this,Action](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.16f);Action();Rebuild();return FReply::Handled();})[MareUI::Text(Label,12,FLinearColor::White)];
 }
 void Line(const FString& Value,int32 Size=14){Body->AddSlot().AutoHeight().Padding(0,4)[MareUI::Text(Value,Size)];}
 void Action(const FString& Label,TFunction<void()> Callback){Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,3)[Button(Label,Callback)];}
 void HomeSummary()
 {
  auto S=Sim();Line(TEXT("Seu turno"),15);
  Body->AddSlot().AutoHeight().Padding(0,3)[MareUI::LiveText([S](){return FString::Printf(TEXT("Pedidos ativos: %d"),UMareSimulation::Object(S->State,TEXT("ue_orders"))->Values.Num());},12)];
  Body->AddSlot().AutoHeight().Padding(0,3)[MareUI::LiveText([S](){bool Hired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),Hired);return Hired?TEXT("Equipe: 1 atendente contratado"):TEXT("Equipe: atendimento pelo jogador");},12)];
  Line(TEXT("Estoque pronto"),15);
  const TArray<FString> Products={TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};
  for(int32 I=0;I<Products.Num();I+=2){auto Row=SNew(SHorizontalBox);
   for(int32 J=0;J<2 && I+J<Products.Num();++J){const FString Id=Products[I+J];auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);
    Row->AddSlot().FillWidth(1).Padding(2)[SNew(SBorder).BorderImage(&MareUI::Card).Padding(8)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight()[MareUI::Text(UMareSimulation::String(Dish,TEXT("name")),11)]
     +SVerticalBox::Slot().AutoHeight().Padding(0,3,0,0)[MareUI::LiveText([S,Id](){if(!S->IsDishUnlocked(Id))return FString(TEXT("Expansão necessária"));const int32 Count=S->Available(Id);return Count>0?FString::Printf(TEXT("%d prontos"),Count):TEXT("Repor estoque");},12)]]];
   }Body->AddSlot().AutoHeight()[Row];
  }
 }
 void Stock(bool bPickup)
 {
  auto S=Sim();const TArray<FString> Products={TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};
  for(const auto& Id:Products){
   if(bPickup && Station==TEXT("Cupboard") && Id!=TEXT("batata_frita") && Id!=TEXT("porcao_peixe") && Id!=TEXT("petiscos"))continue;
   if(bPickup && Station==TEXT("Fridge") && (Id==TEXT("batata_frita") || Id==TEXT("porcao_peixe") || Id==TEXT("petiscos")))continue;
   auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);
   if(!S->CanSupplyDish(Id)){Line(UMareSimulation::String(Dish,TEXT("name"))+TEXT(" · desbloqueie em Resort"),12);continue;}
   Line(UMareSimulation::String(Dish,TEXT("name"))+FString::Printf(TEXT(" · %d disponíveis"),S->Available(Id)));
   auto Row=SNew(SHorizontalBox);
   if(bPickup)Row->AddSlot().AutoWidth().Padding(0,0,6,0)[Button(TEXT("Pegar pronto"),[S,Id](){S->Pickup(Id);})];
   Row->AddSlot().AutoWidth()[Button(FString::Printf(TEXT("Repor 10 · R$ %.0f"),S->RestockCost(Id)),[S,Id](){S->Restock(Id);})];
   Body->AddSlot().AutoHeight().Padding(0,0,0,10)[Row];
  }
 }
 void Missions()
 {
  auto S=Sim();auto Campaign=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("campaign"));
  const int32 Stage=UMareSimulation::Number(Campaign,TEXT("stage"));
  for(bool bSide:{false,true}){Line(bSide?TEXT("Secundárias"):TEXT("Uma nova maré"),17);const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;
   if(!S->Definitions->TryGetArrayField(bSide?TEXT("side_missions"):TEXT("campaign"),Rows))continue;
   for(int32 I=0;I<Rows->Num();++I){if(!bSide && I!=Stage)continue;auto Q=(*Rows)[I]->AsObject();const FString Id=UMareSimulation::String(Q,TEXT("id"));
    const TArray<TSharedPtr<FJsonValue>>* Done=nullptr;if(bSide && Campaign->TryGetArrayField(TEXT("side_done"),Done) && Done->ContainsByPredicate([&](const auto& V){return V->AsString()==Id;}))continue;
    Line(UMareSimulation::String(Q,TEXT("title")),15);Line(UMareSimulation::String(Q,TEXT("task"))+FString::Printf(TEXT(" · %d/%.0f"),S->MissionAmount(Q),UMareSimulation::Number(Q,TEXT("qty"))),12);
    Action(FString::Printf(TEXT("Concluir · R$ %.0f"),UMareSimulation::Number(Q,TEXT("reward"))),[S,Id,bSide](){S->ClaimMission(Id,bSide);});
   }
  }
  // Chapter steps are completed in person with the giver; the phone only tracks them.
  Line(TEXT("Histórias da vila"),17);const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;
  if(S->Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){auto C=Value->AsObject();const FString Id=UMareSimulation::String(C,TEXT("id"));
   if(!S->IsChapterOpen(Id))continue;Line(UMareSimulation::String(C,TEXT("title"))+TEXT(" · ")+UMareSimulation::String(C,TEXT("giver")),15);
   if(S->IsChapterDone(Id)){Line(TEXT("Concluída · ")+UMareSimulation::String(C,TEXT("unlock")),12);continue;}
   int32 Goal=1;const int32 Have=S->ChapterStepProgress(Id,Goal);const int32 Step=S->ChapterStep(Id);
   Line(FString::Printf(TEXT("Passo %d/3 · "),Step+1)+UMareSimulation::String(C->GetArrayField(TEXT("steps"))[Step]->AsObject(),TEXT("text"))+FString::Printf(TEXT(" · %d/%d"),Have,Goal),12);
   Line(TEXT("Converse com ")+UMareSimulation::String(C,TEXT("giver"))+TEXT(" para avançar."),12);
  }
 }
 /** Personalizar: every place of the resort (kiosk, expansions, hotel, businesses, home), each object in
  *  5 tiers (buy, use, free preview) and, at the kiosk, 5 recipe levels per dish. */
 void Customize()
 {
  auto S=Sim();auto World=Owner->GetWorld();auto Custom=World->GetSubsystem<UMareCustomWorld>();auto Kiosk=World->GetSubsystem<UMareKioskWorld>();
  const TArray<TSharedPtr<FJsonValue>>* TierNames=nullptr;S->CustomDefs()->TryGetArrayField(TEXT("tiers"),TierNames);
  static const TArray<FString> Order={TEXT("kiosk"),TEXT("bar"),TEXT("pool"),TEXT("pousada"),TEXT("passeios"),TEXT("hotel_restaurante"),TEXT("hotel_piscina"),TEXT("hotel_suites"),TEXT("hotel_lazer"),
   TEXT("biz_aluguel"),TEXT("biz_sorveteria"),TEXT("biz_food_truck"),TEXT("biz_souvenir"),TEXT("biz_surfe"),TEXT("home")};
  if(!Order.Contains(Place))Place=TEXT("kiosk");
  auto Picker=SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(4,4));
  for(const FString& Id:Order){const FString Name=UMareSimulation::String(S->PlaceDef(Id),TEXT("name"));const bool bOn=Id==Place;const bool bOpen=S->IsPlaceAvailable(Id);
   Picker->AddSlot()[SNew(SButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(7,4)).OnClicked_Lambda([this,Id](){Place=Id;Rebuild();return FReply::Handled();})
    [MareUI::Text((bOn?TEXT("● "):TEXT(""))+Name+(bOpen?TEXT(""):TEXT(" (bloqueado)")),11,bOpen?FLinearColor::White:FLinearColor(.82f,.86f,.84f))]];}
  Body->AddSlot().AutoHeight().Padding(0,2,0,8)[Picker];
  const FString PlaceName=UMareSimulation::String(S->PlaceDef(Place),TEXT("name"));
  Line(PlaceName,18);
  FString Locked;if(!S->IsPlaceAvailable(Place,&Locked)){Line(Locked,13);return;}
  Line(S->PlaceSummary(Place),12);
  FString Reason;const bool bCanChange=Place!=TEXT("kiosk") || !Kiosk || Kiosk->CanCustomize(Reason);
  if(!bCanChange)Line(Reason,12);
  const TArray<TSharedPtr<FJsonValue>>* Slots=nullptr;
  if(S->PlaceDef(Place)->TryGetArrayField(TEXT("slots"),Slots))for(const auto& Value:*Slots){
   auto Def=Value->AsObject();const FString Slot=UMareSimulation::String(Def,TEXT("id"));const int32 Current=S->CustomTier(Place,Slot);
   const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;if(!Def->TryGetArrayField(TEXT("tiers"),Tiers))continue;
   const FString Unlock=UMareSimulation::String(Def,TEXT("unlock"));bool bUnlocked=Unlock.IsEmpty();if(!bUnlocked)UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Unlock,bUnlocked);
   bool bVisual=true;Def->TryGetBoolField(TEXT("visual"),bVisual);
   Line(FString::Printf(TEXT("%s · %s"),*UMareSimulation::String(Def,TEXT("name")),*UMareSimulation::String((*Tiers)[Current-1]->AsObject(),TEXT("name"))),15);
   // Effect of each level above the first, in the words of the place.
   TArray<FString> Effects;const double C=UMareSimulation::Number(Def,TEXT("comfort")),B=UMareSimulation::Number(Def,TEXT("beauty"));
   if(C>0)Effects.Add(FString::Printf(TEXT("+%.0f conforto"),C));if(B>0)Effects.Add(FString::Printf(TEXT("+%.0f beleza"),B));
   if(Def->HasField(TEXT("speed")))Effects.Add(TEXT("atendente +10% rápido"));if(Def->HasField(TEXT("fame")))Effects.Add(TEXT("mais fama"));
   if(Def->HasField(TEXT("income")))Effects.Add(FString::Printf(TEXT("renda +%.0f%%"),UMareSimulation::Number(Def,TEXT("income"))*100));
   if(Def->HasField(TEXT("rate")))Effects.Add(FString::Printf(TEXT("diária +R$ %.0f"),UMareSimulation::Number(Def,TEXT("rate"))));
   if(Def->HasField(TEXT("seats")))Effects.Add(FString::Printf(TEXT("+%.0f vaga por passeio"),UMareSimulation::Number(Def,TEXT("seats"))));
   Line(TEXT("Cada nível acima do Simples: ")+FString::Join(Effects,TEXT(", ")),11);
   if(!bUnlocked){Line(TEXT("Disponível após comprar a expansão ")+UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("expansions")),Unlock),TEXT("name"))+TEXT(" (Resort)."),12);continue;}
   for(int32 Tier=1;Tier<=Tiers->Num();++Tier){auto TierDef=(*Tiers)[Tier-1]->AsObject();
    const FString Level=TierNames && TierNames->IsValidIndex(Tier-1)?(*TierNames)[Tier-1]->AsString():FString::FromInt(Tier);
    Body->AddSlot().AutoHeight().Padding(0,2)[SNew(SBorder).BorderImage(&MareUI::Card).Padding(8)[SNew(SVerticalBox)
     +SVerticalBox::Slot().AutoHeight()[MareUI::Text(FString::Printf(TEXT("%d · %s — %s"),Tier,*Level,*UMareSimulation::String(TierDef,TEXT("name"))),12)]
     +SVerticalBox::Slot().AutoHeight().Padding(0,2,0,0)[MareUI::Text(UMareSimulation::String(TierDef,TEXT("desc")),11,FLinearColor(.35f,.32f,.26f))]]];
    auto Row=SNew(SHorizontalBox);const bool bOwned=S->OwnsCustomTier(Place,Slot,Tier);const FString P=Place;
    if(Tier==Current)Row->AddSlot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,8,0)[MareUI::Text(TEXT("Em uso"),12,FLinearColor(.12f,.45f,.3f))];
    else if(bCanChange)Row->AddSlot().AutoWidth().Padding(0,0,6,0)[Button(bOwned?FString(TEXT("Usar")):FString::Printf(TEXT("Comprar · R$ %.0f"),S->CustomPrice(Place,Slot,Tier)),[S,Custom,P,Slot,Tier](){
      if(S->BuyCustom(P,Slot,Tier) && Custom)Custom->ApplyAll();})];
    if(Tier!=Current && Custom && bVisual)Row->AddSlot().AutoWidth()[Button(TEXT("Prévia"),[S,Custom,P,Slot,Tier,PlaceName](){Custom->Apply(P,Slot,Tier,true);
      S->LastMessage=TEXT("Prévia em ")+PlaceName+TEXT(". Feche o celular para voltar ao que está em uso.");})];
    Body->AddSlot().AutoHeight().Padding(0,0,0,6)[Row];
   }
  }
  if(Place!=TEXT("kiosk"))return;
  Line(TEXT("Receitas"),18);
  Line(TEXT("Receita melhor: preço maior, mais pedidos e, a partir de Gourmet, mais fama por venda."),12);
  const TArray<FString> Products={TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};
  const TArray<TSharedPtr<FJsonValue>>* Levels=nullptr;UMareSimulation::Object(S->CustomDefs(),TEXT("recipes"))->TryGetArrayField(TEXT("levels"),Levels);
  for(const auto& Id:Products){auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);const int32 Level=S->RecipeLevel(Id);
   const FString LevelName=Levels && Levels->IsValidIndex(Level-1)?(*Levels)[Level-1]->AsString():FString::FromInt(Level);
   Body->AddSlot().AutoHeight().Padding(0,2)[SNew(SBorder).BorderImage(&MareUI::Card).Padding(8)[SNew(SVerticalBox)
    +SVerticalBox::Slot().AutoHeight()[MareUI::Text(FString::Printf(TEXT("%s · nível %d (%s) · R$ %.0f"),*UMareSimulation::String(Dish,TEXT("name")),Level,*LevelName,S->DishPrice(Id)),12)]
    +SVerticalBox::Slot().AutoHeight().Padding(0,2,0,0)[MareUI::Text(S->RecipeTitle(Id),11,FLinearColor(.35f,.32f,.26f))]]];
   if(!S->IsDishUnlocked(Id)){Line(TEXT("Libere o produto em Resort para melhorar a receita."),11);continue;}
   if(Level>=5){Line(TEXT("Receita no nível máximo."),11);continue;}
   Action(FString::Printf(TEXT("Melhorar para \"%s\" · R$ %.0f"),*S->RecipeTitle(Id,Level+1),S->RecipeUpgradeCost(Id)),[S,Id](){S->UpgradeRecipe(Id);});
  }
 }
 /** Expansion roles: one row each with the wage and a hire / dismiss button. */
 void ExpansionStaff()
 {
  auto S=Sim();Line(TEXT("Equipe das expansões"),18);auto Roles=UMareSimulation::Object(S->Definitions,TEXT("staff"));
  for(const TCHAR* Role:{TEXT("bartender"),TEXT("camareira"),TEXT("guia")}){auto Def=UMareSimulation::Object(Roles,Role);const FString R=Role;
   Line(FString::Printf(TEXT("%s · salário R$ %.0f por dia"),*UMareSimulation::String(Def,TEXT("name")),UMareSimulation::Number(Def,TEXT("wage"))),14);
   Line(UMareSimulation::String(Def,TEXT("blurb")),11);
   if(S->HasStaff(R))Action(TEXT("Dispensar"),[S,R](){S->DismissStaff(R);});
   else Action(FString::Printf(TEXT("Contratar · R$ %.0f"),UMareSimulation::Number(Def,TEXT("hire"))),[S,R](){S->HireStaff(R);});
  }
 }
 /** Village businesses and what every place earned today. */
 void Businesses()
 {
  auto S=Sim();Line(TEXT("Hoje no resort"),18);
  for(const TCHAR* Id:{TEXT("bar"),TEXT("pool"),TEXT("passeios")})if(S->IsPlaceAvailable(Id))
   Line(FString::Printf(TEXT("%s · R$ %.0f"),*UMareSimulation::String(S->PlaceDef(Id),TEXT("name")),S->OpsToday(Id)),12);
  auto Pousada=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("pousada"));
  if(S->PousadaRooms()>0)Line(Pousada->HasField(TEXT("rooms"))?FString::Printf(TEXT("Pousada, última noite · %.0f de %.0f quartos · R$ %.0f"),UMareSimulation::Number(Pousada,TEXT("occupied")),
   UMareSimulation::Number(Pousada,TEXT("rooms")),UMareSimulation::Number(Pousada,TEXT("rev"))):FString(TEXT("Pousada · os primeiros hóspedes pagam quando você dormir.")),12);
  Line(TEXT("Negócios da vila"),18);Line(TEXT("Cada negócio rende sozinho no horário de funcionamento e paga um funcionário por dia."),12);
  for(const auto& Pair:UMareSimulation::Object(S->Definitions,TEXT("businesses"))->Values){const FString Id(Pair.Key.ToView());auto Def=Pair.Value->AsObject();
   const FString Title=UMareSimulation::String(Def,TEXT("name"));
   if(S->OwnsBusiness(Id)){Line(FString::Printf(TEXT("%s · seu · hoje R$ %.0f"),*Title,S->OpsToday(TEXT("biz_")+Id)),14);continue;}
   Line(FString::Printf(TEXT("%s · ~R$ %.0f/h · funcionário R$ %.0f/dia"),*Title,UMareSimulation::Number(Def,TEXT("hour")),UMareSimulation::Number(Def,TEXT("wage"))),14);
   Line(UMareSimulation::String(Def,TEXT("blurb")),11);FString Reason;
   if(S->CanBuyBusiness(Id,Reason))Action(FString::Printf(TEXT("Comprar · R$ %.0f"),UMareSimulation::Number(Def,TEXT("cost"))),[S,Id](){S->BuyBusiness(Id);});else Line(Reason,11);
  }
 }
 void Rebuild()
 {
  if(!Sim())return;auto S=Sim();using namespace MareTropical;
  const TArray<FString> Titles={TEXT("Quiosque"),TEXT("Compras"),TEXT("Equipe"),TEXT("Finanças"),TEXT("Resort"),TEXT("Missões"),TEXT("Personalizar")};
  auto Close=SNew(SButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(10,6)).OnClicked_Lambda([this](){if(Owner.IsValid())Owner->ClosePhone();return FReply::Handled();})[MareUI::Text(TEXT("Fechar · B / Esc"),12,FLinearColor::White)];
  // Side navigation like proposal C: company, balance and six coloured tabs.
  auto Nav=SNew(SVerticalBox);
  Nav->AddSlot().AutoHeight().Padding(8,6,8,0)[Txt(TEXT("Maré Alta"),16,Hex(255,246,230),true)];
  Nav->AddSlot().AutoHeight().Padding(8,2,8,14)[SNew(STextBlock).Text_Lambda([S](){return FText::FromString(FString::Printf(TEXT("R$ %.0f"),S->Money()));}).Font(FCoreStyle::GetDefaultFontStyle("Bold",14)).ColorAndOpacity(Hex(255,215,106))];
  for(int32 I=0;I<Titles.Num();++I){const bool bOn=I==Tab;
   Nav->AddSlot().AutoHeight().Padding(0,2)[SNew(SButton).ButtonStyle(bOn?&NavOn():&NavOff()).ContentPadding(FMargin(10,8)).OnClicked_Lambda([this,I](){if(Owner.IsValid())Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("click"),.16f);Tab=I;Rebuild();return FReply::Handled();})[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,9,0)[SNew(SBox).WidthOverride(11).HeightOverride(11)[SNew(SBorder).BorderImage(&Dot(bOn?FLinearColor::White:TabColor(I)))]]
    +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[Txt(Titles[I],14,bOn?FLinearColor::White:Hex(214,236,232),true)]]];}
  Nav->AddSlot().FillHeight(1)[SNullWidget::NullWidget];
  Nav->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(4,8,4,4)[Close];
  SAssignNew(Body,SVerticalBox);
  auto Message=MareUI::Text(S->LastMessage,12,Hex(162,76,43));
  Message->SetVisibility(S->LastMessage.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible);
  const FString Heading=Station.IsNone()?Titles[FMath::Clamp(Tab,0,Titles.Num()-1)]:Station==TEXT("Fridge")?TEXT("Geladeira"):TEXT("Porções prontas");
  auto Content=SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0,0,10,0)[SNew(SBox).WidthOverride(14).HeightOverride(14)[SNew(SBorder).BorderImage(&Dot(Station.IsNone()?TabColor(Tab):TabColor(1)))]]
    +SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)[Txt(Heading,20,Hex(74,58,28),true)]]
   +SVerticalBox::Slot().FillHeight(1).Padding(0,10)[SNew(SScrollBox)+SScrollBox::Slot()[Body.ToSharedRef()]]
   +SVerticalBox::Slot().AutoHeight()[Message];
  if(!Station.IsNone())Content->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,8,0,0)[Close];
  auto Shell=SNew(SHorizontalBox);
  if(Station.IsNone())Shell->AddSlot().AutoWidth().Padding(4,4,10,4)[SNew(SBox).WidthOverride(176)[Nav]];
  Shell->AddSlot().FillWidth(1)[SNew(SBorder).BorderImage(&Paper()).Padding(16)[Content]];
  ChildSlot.HAlign(HAlign_Left).VAlign(VAlign_Center)[SNew(SDPIScaler).DPIScale_Lambda([](){return MareTropical::Scale();})[SNew(SBox).Padding(FMargin(36,40,0,0)).WidthOverride(Station.IsNone()?700.f:460.f).HeightOverride(Station.IsNone()?460.f:430.f)[SNew(SBorder).BorderImage(&Frame()).Padding(10)[Shell]]]];
  if(!Station.IsNone()){Stock(true);if(!S->Carry().IsEmpty())Action(TEXT("Devolver produto"),[S](){S->ReturnCarry();});return;}
  if(Tab==0){auto Company=UMareSimulation::Object(S->State,TEXT("company"));bool bCreated=false;Company->TryGetBoolField(TEXT("created"),bCreated);
   if(!bCreated){Line(TEXT("Seu quiosque"),20);
    if(UMareSimulation::Number(S->State,TEXT("ue_intro_stage"),2)<2)Line(TEXT("Primeiro, entre na casa e leia a carta que seu avô deixou para você."),14);
    else{Body->AddSlot().AutoHeight()[SAssignNew(CompanyName,SEditableTextBox).Text(FText::FromString(TEXT("Maré Alta")))];Action(TEXT("Criar empresa"),[this,S](){S->CreateCompany(CompanyName->GetText().ToString());});}}
   else{bool Requested=false;Company->TryGetBoolField(TEXT("kiosk_open"),Requested);auto Hours=UMareSimulation::Object(Company,TEXT("sim"));
    Body->AddSlot().AutoHeight().Padding(0,4)[MareUI::LiveText([S,Requested](){return S->IsOpen()?TEXT("Aberto · recebendo clientes"):Requested?TEXT("Abertura ativada · aguardando horário"):TEXT("Quiosque fechado");},18)];
    Line(FString::Printf(TEXT("Atendimento: %.0fh às %.0fh"),UMareSimulation::Number(Hours,TEXT("start"),8),UMareSimulation::Number(Hours,TEXT("end"),18)),12);
    Line(TEXT("Use a placa do balcão para abrir ou fechar."),12);}
   if(auto Audio=Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()){
    Action(TEXT("Rádio: ")+UMareAudioWorld::RadioName(Audio->GetRadioStation())+TEXT(" · próxima"),[Audio](){Audio->NextRadioStation();});
   }
   if(!S->Carry().IsEmpty())Action(TEXT("Devolver produto"),[S](){S->ReturnCarry();});Line(TEXT("Retire os produtos prontos na geladeira e no armário do quiosque."),13);HomeSummary();
  }else if(Tab==1){Line(TEXT("Reposição imediata"),18);Stock(false);}
  else if(Tab==2){Line(TEXT("Um atendente para todo o quiosque"),18);Line(TEXT("Anota, retira os produtos, entrega e recolhe a louça."));
   Line(FString::Printf(TEXT("Contratação R$ %.0f · salário R$ %.0f por dia, pago ao dormir."),UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("staff")),TEXT("atendente")),TEXT("hire")),UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("staff")),TEXT("atendente")),TEXT("wage"))),12);bool bHired=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bHired);
   if(bHired)Action(TEXT("Dispensar atendente"),[S](){S->DismissAttendant();});else Action(TEXT("Contratar atendente"),[S](){S->HireAttendant();});ExpansionStaff();}
  else if(Tab==3){Line(FString::Printf(TEXT("Caixa · R$ %.0f"),S->Money()),20);
   Line(FString::Printf(TEXT("Hoje · entradas R$ %.0f · saídas R$ %.0f"),UMareSimulation::Number(S->State,TEXT("day_in")),UMareSimulation::Number(S->State,TEXT("day_out"))),13);
   if(S->State->HasTypedField<EJson::Object>(TEXT("ue_last_day"))){auto Last=UMareSimulation::Object(S->State,TEXT("ue_last_day"));
    Line(FString::Printf(TEXT("Dia %.0f · %.0f vendas · lucro R$ %.0f (salários R$ %.0f)"),UMareSimulation::Number(Last,TEXT("day")),UMareSimulation::Number(Last,TEXT("sales")),
     UMareSimulation::Number(Last,TEXT("income"))-UMareSimulation::Number(Last,TEXT("expense")),UMareSimulation::Number(Last,TEXT("wages"))),13);}
   Line(TEXT("Últimos lançamentos"),15);const TArray<TSharedPtr<FJsonValue>>* Ledger=nullptr;if(S->State->TryGetArrayField(TEXT("ledger"),Ledger))for(int32 I=Ledger->Num()-1;I>=FMath::Max(0,Ledger->Num()-12);--I){auto Row=(*Ledger)[I]->AsObject();Line(UMareSimulation::String(Row,TEXT("label"))+FString::Printf(TEXT(" · R$ %.0f"),UMareSimulation::Number(Row,TEXT("amount"))),13);}}
  else if(Tab==4){
   bool bHotel=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
   if(bHotel){Line(TEXT("Grand Hotel Maré Alta 5★"),18);
    Line(FString::Printf(TEXT("32 suítes · diária R$ 220 · ocupação prevista %.0f%% (nota %.1f★, fama %s)"),S->HotelOccupancy()*100,S->Stars(),*S->FameName()),12);
    auto Last=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("hotel"));
    if(Last->HasField(TEXT("rooms")))Line(FString::Printf(TEXT("Última noite: %.0f suítes · diárias R$ %.0f · restaurante R$ %.0f · equipe −R$ %.0f"),UMareSimulation::Number(Last,TEXT("rooms")),UMareSimulation::Number(Last,TEXT("rev")),UMareSimulation::Number(Last,TEXT("dining")),UMareSimulation::Number(Last,TEXT("staff"))),12);
    else Line(TEXT("Os hóspedes chegam esta noite; o resultado aparece depois que você dormir."),12);}
   Line(TEXT("Expansões do resort"),18);Line(TEXT("As áreas são liberadas após a compra."),12);
   auto Expansions=UMareSimulation::Object(S->Definitions,TEXT("expansions"));
   for(const auto& Pair:Expansions->Values){const FString Id(Pair.Key.ToView());auto Row=Pair.Value->AsObject();
    bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);
    if(bOwned)Line(UMareSimulation::String(Row,TEXT("name"))+TEXT(" · Comprada"),14);
    else Action(UMareSimulation::String(Row,TEXT("name"))+FString::Printf(TEXT(" · R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),[S,Id](){S->BuyExpansion(Id);});
   }
   Businesses();
  }
  else if(Tab==5)Missions();
  else Customize();
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
 if(PhoneWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PhoneWidget.ToSharedRef());
 // A furniture preview ends with the phone: show what is really in use again.
 if(auto Custom=GetWorld()->GetSubsystem<UMareCustomWorld>())if(Custom->IsPreviewing())Custom->ApplyAll();
 PhoneWidget.Reset();bPhoneOpen=false;bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
}
void AMareController::EndPlay(const EEndPlayReason::Type Reason){if(PauseWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();ClosePhone();Super::EndPlay(Reason);}
/** Everything the tropical HUD shows; Signature() decides when Slate must rebuild. */
struct FMareHudModel
{
 FString Money,Day,Fame,Notice,Prompt,Carry,Hint;
 TArray<TPair<FString,FString>> Tickets;
 TArray<TPair<FString,int32>> Note; // text, style: 0 heading, 1 main goal, 2 secondary, 3 guidance
 bool bPhone=false;
 FString Signature()const
 {
  FString S=Money+Day+Fame+Notice+Prompt+Carry+Hint+(bPhone?TEXT("P"):TEXT(""));
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
   +SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[Txt(M.Fame,15,Paper,true)]]];
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
 if(S->LastMessage!=Notice){Notice=S->LastMessage;NoticeUntil=Notice.IsEmpty()?0:Now+7;}
 if(Now<NoticeUntil)M.Notice=Notice;
 const int32 IntroStage=UMareSimulation::Number(S->State,TEXT("ue_intro_stage"),2);
 if(IntroStage==0)M.Note={{TEXT("Chegada"),0},{TEXT("A vila parecia menor... e o mar, do tamanho das minhas lembranças."),2},{TEXT("E · avançar"),3}};
 else{
  M.Note.Add({TEXT("Missões"),0});
  if(IntroStage==1)M.Note.Add({TEXT("Entre na casa e leia a carta do avô"),3});
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
   M.Tickets.Add({FString::Printf(TEXT("#%d %s"),Number,*UMareSimulation::String(Order,TEXT("name"))),Text});
  }
 }
 if(!S->Carry().IsEmpty())M.Carry=Dish(S->Carry());
 if(auto Hero=Cast<AMareCharacter>(GetOwningPawn()))if(Hero->GetCharacterMovement()->IsSwimming())M.Hint=TEXT("Nadando · Espaço sobe · Ctrl/Shift mergulha");
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
