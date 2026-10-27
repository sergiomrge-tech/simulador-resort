#include "MareGame.h"
#include "MareSimulation.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"

namespace MareUI
{
 static const FSlateRoundedBoxBrush Phone(FLinearColor(.035f,.055f,.05f),24.f);
 static const FSlateRoundedBoxBrush Surface(FLinearColor(.94f,.94f,.90f),18.f);
 static const FSlateRoundedBoxBrush Card(FLinearColor(.99f,.99f,.97f),10.f);
 TSharedRef<STextBlock> Text(const FString& Value,int32 Size=14)
 {
  return SNew(STextBlock).Text(FText::FromString(Value)).Font(FCoreStyle::GetDefaultFontStyle("Regular",Size)).ColorAndOpacity(FLinearColor(.08f,.12f,.11f)).AutoWrapText(true);
 }
}
class SMarePhone : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMarePhone){} SLATE_ARGUMENT(TWeakObjectPtr<AMareController>,Owner) SLATE_ARGUMENT(int32,Tab) SLATE_END_ARGS()
 void Construct(const FArguments& Args)
 {
  Owner=Args._Owner;Tab=Args._Tab; Rebuild();
 }
private:
 TWeakObjectPtr<AMareController> Owner;
 TSharedPtr<SVerticalBox> Body;
 TSharedPtr<SEditableTextBox> CompanyName;
 int32 Tab=0;
 UMareSimulation* Sim()const{return Owner.IsValid()?Owner->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 TSharedRef<SWidget> Button(const FString& Label,TFunction<void()> Action)
 {
  return SNew(SButton).ContentPadding(FMargin(10,6)).OnClicked_Lambda([this,Action](){Action();Rebuild();return FReply::Handled();})[MareUI::Text(Label,13)];
 }
 void Line(const FString& Value,int32 Size=14){Body->AddSlot().AutoHeight().Padding(0,4)[MareUI::Text(Value,Size)];}
 void Action(const FString& Label,TFunction<void()> Callback){Body->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0,3)[Button(Label,Callback)];}
 void Stock(bool bPickup)
 {
  auto S=Sim();const TArray<FString> Products={TEXT("coco_gelado"),TEXT("suco"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};
  for(const auto& Id:Products){auto Dish=UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Id);
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
 }
 void Rebuild()
 {
  if(!Sim())return;auto S=Sim();auto Tabs=SNew(SVerticalBox);
  const TArray<FString> Titles={TEXT("Quiosque"),TEXT("Compras"),TEXT("Equipe"),TEXT("Finanças"),TEXT("Resort"),TEXT("Missões")};
  for(int32 R=0;R<2;++R){auto Row=SNew(SHorizontalBox);for(int32 C=0;C<3;++C){const int32 Index=R*3+C;
   Row->AddSlot().FillWidth(1).Padding(2)[Button(Titles[Index],[this,Index](){Tab=Index;})];}Tabs->AddSlot().AutoHeight()[Row];}
  SAssignNew(Body,SVerticalBox);
  ChildSlot.HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(20)[SNew(SBox).WidthOverride(420).HeightOverride(680)[SNew(SBorder).BorderImage(&MareUI::Phone).Padding(10)[SNew(SBorder).BorderImage(&MareUI::Surface).Padding(14)[SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,10)[MareUI::Text(FString::Printf(TEXT("Maré Alta       R$ %.0f"),S->Money()),17)]
   +SVerticalBox::Slot().AutoHeight()[Tabs]
   +SVerticalBox::Slot().FillHeight(1).Padding(0,10)[SNew(SScrollBox)+SScrollBox::Slot()[Body.ToSharedRef()]]
   +SVerticalBox::Slot().AutoHeight()[MareUI::Text(S->LastMessage,12)]
   +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,0)[SNew(SButton).OnClicked_Lambda([this](){if(Owner.IsValid())Owner->ClosePhone();return FReply::Handled();})[MareUI::Text(TEXT("Fechar · B / Esc"),13)]]]]]];
  if(Tab==0){auto Company=UMareSimulation::Object(S->State,TEXT("company"));bool bCreated=false;Company->TryGetBoolField(TEXT("created"),bCreated);
   if(!bCreated){Line(TEXT("Seu quiosque"),20);Body->AddSlot().AutoHeight()[SAssignNew(CompanyName,SEditableTextBox).Text(FText::FromString(TEXT("Maré Alta")))];Action(TEXT("Criar empresa"),[this,S](){S->CreateCompany(CompanyName->GetText().ToString());});}
   else{Line(S->IsOpen()?TEXT("Aberto · recebendo clientes"):TEXT("Quiosque fechado"),18);Action(S->IsOpen()?TEXT("Fechar quiosque"):TEXT("Abrir quiosque"),[S](){S->SetOpen(!S->IsOpen());});}
   if(!S->Carry().IsEmpty())Action(TEXT("Devolver produto"),[S](){S->ReturnCarry();});Stock(true);
  }else if(Tab==1){Line(TEXT("Reposição imediata"),18);Stock(false);}
  else if(Tab==2){Line(TEXT("Um atendente para todo o quiosque"),18);Line(TEXT("Anota, retira os produtos, entrega e recolhe a louça."));Action(TEXT("Contratar atendente"),[S](){S->HireAttendant();});}
  else if(Tab==3){Line(FString::Printf(TEXT("Caixa · R$ %.0f"),S->Money()),20);const TArray<TSharedPtr<FJsonValue>>* Ledger=nullptr;if(S->State->TryGetArrayField(TEXT("ledger"),Ledger))for(int32 I=Ledger->Num()-1;I>=FMath::Max(0,Ledger->Num()-12);--I){auto Row=(*Ledger)[I]->AsObject();Line(UMareSimulation::String(Row,TEXT("label"))+FString::Printf(TEXT(" · R$ %.0f"),UMareSimulation::Number(Row,TEXT("amount"))),13);}}
  else if(Tab==4){Line(TEXT("Expansões do resort"),18);auto Expansions=UMareSimulation::Object(S->Definitions,TEXT("expansions"));for(const auto& Pair:Expansions->Values){const FString Id(Pair.Key.ToView());auto Row=Pair.Value->AsObject();Action(UMareSimulation::String(Row,TEXT("name"))+FString::Printf(TEXT(" · R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),[S,Id](){S->BuyExpansion(Id);});}}
  else Missions();
 }
};
AMareCharacter::AMareCharacter()
{
 GetCapsuleComponent()->InitCapsuleSize(32,88);
 auto Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Eyes"));Camera->SetupAttachment(GetCapsuleComponent());Camera->SetRelativeLocation(FVector(0,0,64));Camera->bUsePawnControlRotation=true;
 GetCharacterMovement()->MaxWalkSpeed=260;GetCharacterMovement()->JumpZVelocity=360;GetCharacterMovement()->MaxStepHeight=35;
}
void AMareCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
 Super::SetupPlayerInputComponent(Input);Input->BindAxis(TEXT("Forward"),this,&AMareCharacter::Forward);Input->BindAxis(TEXT("Right"),this,&AMareCharacter::Right);
 Input->BindAxis(TEXT("LookX"),this,&AMareCharacter::LookX);Input->BindAxis(TEXT("LookY"),this,&AMareCharacter::LookY);
 Input->BindAction(TEXT("Phone"),IE_Pressed,this,&AMareCharacter::Phone);Input->BindAction(TEXT("Interact"),IE_Pressed,this,&AMareCharacter::Interact);Input->BindAction(TEXT("Jump"),IE_Pressed,this,&ACharacter::Jump);
}
void AMareCharacter::Forward(float Value){if(Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),Value);}
void AMareCharacter::Right(float Value){if(Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),Value);}
void AMareCharacter::LookX(float Value){AddControllerYawInput(Value);}
void AMareCharacter::LookY(float Value){AddControllerPitchInput(Value);}
void AMareCharacter::Phone(){if(auto PC=Cast<AMareController>(Controller))PC->TogglePhone();}
void AMareCharacter::Interact(){}
void AMareController::TogglePhone(){if(bPhoneOpen)ClosePhone();else OpenPhone();}
void AMareController::OpenPhone(int32 Tab)
{
 if(!GEngine || !GEngine->GameViewport)return;
 if(bPhoneOpen)ClosePhone();bPhoneOpen=true;
 SAssignNew(PhoneWidget,SMarePhone).Owner(this).Tab(Tab);GEngine->GameViewport->AddViewportWidgetContent(PhoneWidget.ToSharedRef(),20);
 bShowMouseCursor=true;SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(PhoneWidget).SetHideCursorDuringCapture(false));SetIgnoreMoveInput(true);SetIgnoreLookInput(true);
}
void AMareController::ClosePhone()
{
 if(PhoneWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PhoneWidget.ToSharedRef());
 PhoneWidget.Reset();bPhoneOpen=false;bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
}
void AMareController::EndPlay(const EEndPlayReason::Type Reason){ClosePhone();Super::EndPlay(Reason);}
void AMareHUD::DrawHUD()
{
 Super::DrawHUD();if(!Canvas)return;auto S=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 auto Font=GEngine->GetSmallFont();float Y=24;
 auto Line=[&](const FString& Text,FLinearColor Color=FLinearColor::White){Canvas->SetDrawColor(Color.ToFColor(true));Canvas->DrawText(Font,Text,22,Y);Y+=22;};
 Line(FString::Printf(TEXT("R$ %.0f   Dia %.0f   %02d:%02d"),S->Money(),UMareSimulation::Number(S->State,TEXT("day"),1),int32(UMareSimulation::Number(S->State,TEXT("minutes")))/60,int32(UMareSimulation::Number(S->State,TEXT("minutes")))%60));
 auto Orders=UMareSimulation::Object(S->State,TEXT("ue_orders"));for(const auto& Pair:Orders->Values){auto Order=Pair.Value->AsObject();const TArray<TSharedPtr<FJsonValue>>* Items=nullptr;FString Text=UMareSimulation::String(Order,TEXT("name"))+TEXT(" · ");if(Order->TryGetArrayField(TEXT("remaining"),Items))for(const auto& Item:*Items)Text+=UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Item->AsString()),TEXT("name"))+TEXT("  ");Line(Text);}
 Canvas->DrawText(Font,TEXT("B · celular     E · interagir"),22,Canvas->ClipY-35);
}
AMareGameMode::AMareGameMode(){DefaultPawnClass=AMareCharacter::StaticClass();PlayerControllerClass=AMareController::StaticClass();HUDClass=AMareHUD::StaticClass();}


