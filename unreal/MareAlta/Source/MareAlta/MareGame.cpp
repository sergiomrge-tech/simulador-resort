#include "MareGame.h"
#include "MarePreviewQA.h"
#include "MareAudioWorld.h"
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
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
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
  .SetNormal(FSlateRoundedBoxBrush(FLinearColor(.08f,.25f,.21f),8.f))
  .SetHovered(FSlateRoundedBoxBrush(FLinearColor(.12f,.36f,.31f),8.f))
  .SetPressed(FSlateRoundedBoxBrush(FLinearColor(.05f,.18f,.15f),8.f));
 TSharedRef<STextBlock> Text(const FString& Value,int32 Size=14,FLinearColor Color=FLinearColor(.08f,.12f,.11f))
 {
  return SNew(STextBlock).Text(FText::FromString(Value)).Font(FCoreStyle::GetDefaultFontStyle("Regular",Size)).ColorAndOpacity(Color).AutoWrapText(true);
 }
 TSharedRef<STextBlock> LiveText(TFunction<FString()> Value,int32 Size=14)
 {
  return SNew(STextBlock).Text_Lambda([Value](){return FText::FromString(Value());}).Font(FCoreStyle::GetDefaultFontStyle("Regular",Size)).ColorAndOpacity(FLinearColor(.08f,.12f,.11f)).AutoWrapText(true);
 }
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
 }
 void Rebuild()
 {
  if(!Sim())return;auto S=Sim();auto Tabs=SNew(SVerticalBox);
  FVector2D ViewSize(1280,720);if(GEngine && GEngine->GameViewport)GEngine->GameViewport->GetViewportSize(ViewSize);
  const float UIScale=FMath::Max(.1f,GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(FIntPoint(ViewSize.X,ViewSize.Y)));
  const float Height=FMath::Max(220.f,FMath::Min(Station.IsNone()?680.f:450.f,ViewSize.Y-40.f));
  const float Width=FMath::Max(240.f,FMath::Min(Station.IsNone()?FMath::Min(420.f,Height*.66f):420.f,ViewSize.X-40.f));
  const int32 Columns=Width<360.f?2:3;
  const TArray<FString> Titles={TEXT("Quiosque"),TEXT("Compras"),TEXT("Equipe"),TEXT("Finanças"),TEXT("Resort"),TEXT("Missões")};
  for(int32 R=0;R<6/Columns;++R){auto Row=SNew(SHorizontalBox);for(int32 C=0;C<Columns;++C){const int32 Index=R*Columns+C;
   Row->AddSlot().FillWidth(1).Padding(2)[Button(Titles[Index],[this,Index](){Tab=Index;})];}Tabs->AddSlot().AutoHeight()[Row];}
  SAssignNew(Body,SVerticalBox);
  auto Message=MareUI::Text(S->LastMessage,12);
  Message->SetVisibility(S->LastMessage.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible);
  ChildSlot.HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(20.f/UIScale)[SNew(SDPIScaler).DPIScale(1.f/UIScale)[SNew(SBox).WidthOverride(Width).HeightOverride(Height)[SNew(SBorder).BorderImage(&MareUI::Phone).Padding(10)[SNew(SBorder).BorderImage(&MareUI::Surface).Padding(14)[SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,8)[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().FillWidth(1)[MareUI::Text(TEXT("Maré Alta"),14)]
    +SHorizontalBox::Slot().AutoWidth()[MareUI::LiveText([S](){return FString::Printf(TEXT("R$ %.0f"),S->Money());},13)]]
   +SVerticalBox::Slot().AutoHeight()[Station.IsNone()?StaticCastSharedRef<SWidget>(Tabs):StaticCastSharedRef<SWidget>(MareUI::Text(Station==TEXT("Fridge")?TEXT("Geladeira"):TEXT("Porções prontas"),18))]
   +SVerticalBox::Slot().FillHeight(1).Padding(0,10)[SNew(SScrollBox)+SScrollBox::Slot()[Body.ToSharedRef()]]
   +SVerticalBox::Slot().AutoHeight()[Message]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left).Padding(0,8,0,0)[SNew(SButton).ButtonStyle(&MareUI::ActionButton).ContentPadding(FMargin(8,5)).OnClicked_Lambda([this](){if(Owner.IsValid())Owner->ClosePhone();return FReply::Handled();})[MareUI::Text(TEXT("Fechar · B / Esc"),12,FLinearColor::White)]]]]]]];
  if(!Station.IsNone()){Stock(true);if(!S->Carry().IsEmpty())Action(TEXT("Devolver produto"),[S](){S->ReturnCarry();});return;}
  if(Tab==0){auto Company=UMareSimulation::Object(S->State,TEXT("company"));bool bCreated=false;Company->TryGetBoolField(TEXT("created"),bCreated);
   if(!bCreated){Line(TEXT("Seu quiosque"),20);Body->AddSlot().AutoHeight()[SAssignNew(CompanyName,SEditableTextBox).Text(FText::FromString(TEXT("Maré Alta")))];Action(TEXT("Criar empresa"),[this,S](){S->CreateCompany(CompanyName->GetText().ToString());});}
   else{bool Requested=false;Company->TryGetBoolField(TEXT("kiosk_open"),Requested);auto Hours=UMareSimulation::Object(Company,TEXT("sim"));
    Body->AddSlot().AutoHeight().Padding(0,4)[MareUI::LiveText([S,Requested](){return S->IsOpen()?TEXT("Aberto · recebendo clientes"):Requested?TEXT("Abertura ativada · aguardando horário"):TEXT("Quiosque fechado");},18)];
    Line(FString::Printf(TEXT("Atendimento: %.0fh às %.0fh"),UMareSimulation::Number(Hours,TEXT("start"),8),UMareSimulation::Number(Hours,TEXT("end"),18)),12);
    Line(TEXT("Use a placa do balcão para abrir ou fechar."),12);}
   if(auto Audio=Owner->GetWorld()->GetSubsystem<UMareAudioWorld>()){
    const FName Radio=Audio->GetRadioStation();const FString Name=Radio==TEXT("off")?TEXT("Desligada"):Radio==TEXT("music_bossa")?TEXT("Bossa praiana"):Radio==TEXT("music_relax")?TEXT("Brisa instrumental"):TEXT("Reggae praiano");
    Action(TEXT("Rádio: ")+Name+TEXT(" · trocar"),[Audio,Radio](){Audio->SetRadioStation(Radio==TEXT("reggae_praia")?FName(TEXT("music_bossa")):Radio==TEXT("music_bossa")?FName(TEXT("music_relax")):Radio==TEXT("music_relax")?FName(TEXT("off")):FName(TEXT("reggae_praia")));});
   }
   if(!S->Carry().IsEmpty())Action(TEXT("Devolver produto"),[S](){S->ReturnCarry();});Line(TEXT("Retire os produtos prontos na geladeira e no armário do quiosque."),13);HomeSummary();
  }else if(Tab==1){Line(TEXT("Reposição imediata"),18);Stock(false);}
  else if(Tab==2){Line(TEXT("Um atendente para todo o quiosque"),18);Line(TEXT("Anota, retira os produtos, entrega e recolhe a louça."));Action(TEXT("Contratar atendente"),[S](){S->HireAttendant();});}
  else if(Tab==3){Line(FString::Printf(TEXT("Caixa · R$ %.0f"),S->Money()),20);const TArray<TSharedPtr<FJsonValue>>* Ledger=nullptr;if(S->State->TryGetArrayField(TEXT("ledger"),Ledger))for(int32 I=Ledger->Num()-1;I>=FMath::Max(0,Ledger->Num()-12);--I){auto Row=(*Ledger)[I]->AsObject();Line(UMareSimulation::String(Row,TEXT("label"))+FString::Printf(TEXT(" · R$ %.0f"),UMareSimulation::Number(Row,TEXT("amount"))),13);}}
  else if(Tab==4){
   Line(TEXT("Expansões do resort"),18);Line(TEXT("As áreas são liberadas após a compra."),12);
   auto Expansions=UMareSimulation::Object(S->Definitions,TEXT("expansions"));
   for(const auto& Pair:Expansions->Values){const FString Id(Pair.Key.ToView());auto Row=Pair.Value->AsObject();
    bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);
    if(bOwned)Line(UMareSimulation::String(Row,TEXT("name"))+TEXT(" · Comprada"),14);
    else Action(UMareSimulation::String(Row,TEXT("name"))+FString::Printf(TEXT(" · R$ %.0f"),UMareSimulation::Number(Row,TEXT("cost"))),[S,Id](){S->BuyExpansion(Id);});
   }
  }
  else Missions();
 }
};
AMareCharacter::AMareCharacter()
{
 PrimaryActorTick.bCanEverTick=true;
 GetCapsuleComponent()->InitCapsuleSize(32,88);
 Eyes=CreateDefaultSubobject<UCameraComponent>(TEXT("Eyes"));Eyes->SetupAttachment(GetCapsuleComponent());Eyes->SetRelativeLocation(FVector(0,0,64));Eyes->bUsePawnControlRotation=true;
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
void AMareCharacter::Forward(float Value){if(Controller){auto Rotation=Controller->GetControlRotation();if(!GetCharacterMovement()->IsSwimming())Rotation.Pitch=0;Rotation.Roll=0;AddMovementInput(Rotation.Vector(),Value);}}
void AMareCharacter::Right(float Value){if(Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),Value);}
void AMareCharacter::LookX(float Value){AddControllerYawInput(Value);}
void AMareCharacter::LookY(float Value){AddControllerPitchInput(Value);}
void AMareCharacter::Phone(){if(auto PC=Cast<AMareController>(Controller))PC->TogglePhone();}
void AMareCharacter::Interact(){if(auto PC=Cast<AMareController>(Controller))if(!PC->bPhoneOpen && !GetWorld()->IsPaused())if(auto Target=AMareServiceTarget::FindFocused(PC))Target->Use(PC);}
void AMareCharacter::SwimVertical(float Value){VerticalSwimInput=FMath::Clamp(Value,-1.f,1.f);}
void AMareCharacter::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto Movement=GetCharacterMovement();auto PC=Cast<APlayerController>(Controller);
 const bool bSwimming=Movement->IsSwimming();const float Vertical=PC && PC->IsMoveInputIgnored()?0.f:VerticalSwimInput;
 Movement->MaxWalkSpeed=bSprint?420:260;Movement->Buoyancy=Vertical<0?1.f:1.35f;
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
void AMareController::TogglePhone(){if(PauseWidget.IsValid())return;if(bPhoneOpen)ClosePhone();else OpenPhone();}
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
 PhoneWidget.Reset();bPhoneOpen=false;bShowMouseCursor=false;SetInputMode(FInputModeGameOnly());ResetIgnoreMoveInput();ResetIgnoreLookInput();
}
void AMareController::EndPlay(const EEndPlayReason::Type Reason){if(PauseWidget.IsValid() && GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(PauseWidget.ToSharedRef());PauseWidget.Reset();ClosePhone();Super::EndPlay(Reason);}
void AMareHUD::DrawHUD()
{
 Super::DrawHUD();if(!Canvas)return;auto S=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 auto Font=GEngine->GetSmallFont();float Y=24;
 const auto PC=Cast<AMareController>(GetOwningPlayerController());
 const float TextWidth=FMath::Clamp(Canvas->ClipX-44.f-(PC && PC->bPhoneOpen?460.f:0.f),180.f,540.f);
 auto Line=[&](const FString& Text,FLinearColor Color=FLinearColor::White){MareUI::HUDLine(Canvas,Font,Text,Color,Y,TextWidth);};
 Line(FString::Printf(TEXT("R$ %.0f   Dia %.0f   %02d:%02d"),S->Money(),UMareSimulation::Number(S->State,TEXT("day"),1),int32(UMareSimulation::Number(S->State,TEXT("minutes")))/60,int32(UMareSimulation::Number(S->State,TEXT("minutes")))%60));
 bool bCreated=false;auto Company=UMareSimulation::Object(S->State,TEXT("company"));Company->TryGetBoolField(TEXT("created"),bCreated);
 if(!bCreated)Line(TEXT("Comece aqui: B · Celular → Quiosque → Criar empresa"),FLinearColor(1.f,.88f,.56f));
 else if(!S->IsOpen())Line(TEXT("Aponte para a placa FECHADO e clique para abrir"),FLinearColor(1.f,.88f,.56f));
 auto Orders=UMareSimulation::Object(S->State,TEXT("ue_orders"));for(const auto& Pair:Orders->Values){auto Order=Pair.Value->AsObject();const TArray<TSharedPtr<FJsonValue>>* Items=nullptr;FString Text=UMareSimulation::String(Order,TEXT("name"))+TEXT(" · ");if(Order->TryGetArrayField(TEXT("remaining"),Items))for(const auto& Item:*Items)Text+=UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),Item->AsString()),TEXT("name"))+TEXT("  ");Line(Text);}
 const auto Campaign=UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("campaign"));
 const TArray<TSharedPtr<FJsonValue>>* Missions=nullptr;
 const int32 Stage=UMareSimulation::Number(Campaign,TEXT("stage"));
 if(S->Definitions->TryGetArrayField(TEXT("campaign"),Missions) && Missions->IsValidIndex(Stage)){
  const auto Mission=(*Missions)[Stage]->AsObject();const int32 Goal=UMareSimulation::Number(Mission,TEXT("qty"));
  const int32 Progress=FMath::Min(S->MissionAmount(Mission),Goal);
  Line(UMareSimulation::String(Mission,TEXT("title"))+FString::Printf(TEXT(" · %d/%d"),Progress,Goal)+(Progress>=Goal?TEXT(" · concluir no celular"):TEXT("")),FLinearColor(1.f,.88f,.56f));
 }
 if(S->Definitions->TryGetArrayField(TEXT("side_missions"),Missions)){
  const TArray<TSharedPtr<FJsonValue>>* Done=nullptr;Campaign->TryGetArrayField(TEXT("side_done"),Done);int32 Shown=0;
  for(const auto& Value:*Missions){const auto Mission=Value->AsObject();const FString Id=UMareSimulation::String(Mission,TEXT("id"));
   if(Done && Done->ContainsByPredicate([&](const auto& Item){return Item->AsString()==Id;}))continue;
   const int32 Goal=UMareSimulation::Number(Mission,TEXT("qty"));
   Line(UMareSimulation::String(Mission,TEXT("title"))+FString::Printf(TEXT(" · %d/%d"),FMath::Min(S->MissionAmount(Mission),Goal),Goal),FLinearColor(.85f,.92f,.82f));
   if(++Shown>=2)break;
  }
 }
 if(PC && !PC->bPhoneOpen && !GetWorld()->IsPaused()){
  const auto Target=AMareServiceTarget::FindFocused(GetOwningPlayerController());
  const FLinearColor FocusColor=Target?FLinearColor(1.f,.88f,.56f):FLinearColor(.9f,.9f,.9f,.8f);
  const float CX=Canvas->ClipX*.5f,CY=Canvas->ClipY*.5f;
  DrawLine(CX-3,CY,CX+3,CY,FocusColor,1.f);DrawLine(CX,CY-3,CX,CY+3,FocusColor,1.f);
  if(Target)Canvas->DrawText(Font,TEXT("E / Clique · ")+Target->Prompt(),22,Canvas->ClipY-62);
 }
 if(!S->Carry().IsEmpty())Line(TEXT("Na mão: ")+UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("dishes")),S->Carry()),TEXT("name")));
 if(auto Hero=Cast<AMareCharacter>(GetOwningPawn()))if(Hero->GetCharacterMovement()->IsSwimming())Line(TEXT("Nadando · Espaço sobe · Ctrl / Shift mergulha"));
 Canvas->DrawText(Font,TEXT("B · celular     E · interagir"),22,Canvas->ClipY-35);
}
AMareGameMode::AMareGameMode(){PrimaryActorTick.bCanEverTick=true;DefaultPawnClass=AMareCharacter::StaticClass();PlayerControllerClass=AMareController::StaticClass();HUDClass=AMareHUD::StaticClass();}
void AMareGameMode::BeginPlay(){Super::BeginPlay();if(FParse::Param(FCommandLine::Get(),TEXT("MarePreviewQA")))GetWorld()->SpawnActor<AMarePreviewQA>();}

void AMareGameMode::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 Sim->AdvanceMinutes(DeltaSeconds*2.0);SaveClock+=DeltaSeconds;if(SaveClock>=30){Sim->Save();SaveClock=0;}
}

UMareSimulation* AMareController::GetSimulation()const{return GetGameInstance()->GetSubsystem<UMareSimulation>();}
