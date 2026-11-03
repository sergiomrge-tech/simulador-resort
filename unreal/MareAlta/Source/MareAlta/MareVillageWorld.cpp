#include "MareVillageWorld.h"
#include "MareGame.h"
#include "MareGamepad.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/GameUserSettings.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "NavigationSystem.h"
#include "AIController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"

TStatId UMareVillageWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareVillageWorld,STATGROUP_Tickables);}
AMarePerson* UMareVillageWorld::SpawnPerson(FVector Position,int32 Variant,const FString& Name)
{
 auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());FNavLocation Ground;
 if(!Nav || !Nav->ProjectPointToNavigation(Position,Ground,FVector(90,90,180)))return nullptr;
 auto Person=GetWorld()->SpawnActor<AMarePerson>(Ground.Location+FVector(0,0,88),FRotator::ZeroRotator);
 if(!Person)return nullptr;if(!Person->SetAppearance(Variant)){Person->Destroy();return nullptr;}
 Person->PersonName=Name;Person->bAmbient=true;Person->GetCharacterMovement()->MaxWalkSpeed=105+Variant*7;
 Person->GetCapsuleComponent()->SetCapsuleRadius(34);
 Person->GetCharacterMovement()->AvoidanceConsiderationRadius=300;Person->GetCharacterMovement()->SetAvoidanceEnabled(true);
 Person->GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
 Person->Tags.Add(TEXT("MareVillagePerson"));return Person;
}
void UMareVillageWorld::Setup()
{
 // Retry on a later tick while navigation is loading/building; do not mark an empty population ready.
 auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());FNavLocation ReadyPoint;
 if(!Nav || Nav->IsNavigationBuildInProgress() || !Nav->ProjectPointToNavigation(FVector(3700,-1230,98),ReadyPoint,FVector(80,80,150)))return;
 FString Text;TSharedPtr<FJsonObject> Data;
 if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/village_routes.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Data))return;
 const auto Vector=[](const TArray<TSharedPtr<FJsonValue>>& A){return FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());};
 for(const auto& Item:Data->GetArrayField(TEXT("routes"))){TArray<FVector> Points;for(const auto& P:Item->AsObject()->GetArrayField(TEXT("points")))Points.Add(Vector(P->AsArray()));if(Points.Num()>1)Routes.Add(Points);}
 if(Routes.IsEmpty())return;
 for(const auto& Item:Data->GetArrayField(TEXT("residents"))){auto Row=Item->AsObject();const FString Name=UMareSimulation::String(Row,TEXT("name"));
  // Verified against the exported GLB roots: Human_2 is the female rig; 0/1/3 are male.
  const int32 Look=Name==TEXT("Dona Roberta") || Name==TEXT("Dona Cecília") || Name==TEXT("Alana")?2:Name==TEXT("Seu Gregory") || Name==TEXT("Padre Robson")?1:3;
  auto Person=SpawnPerson(Vector(Row->GetArrayField(TEXT("position"))),Look,Name);if(!Person)continue;
  Person->SetActorRotation(FRotator(0,UMareSimulation::Number(Row,TEXT("yaw")),0));Residents.Add(Person);
  auto Target=GetWorld()->SpawnActor<AMareServiceTarget>();Target->Action=TEXT("Resident");Target->Label=Person->PersonName+TEXT(" · conversar");Target->Reach=260;Target->OcclusionTolerance=40;Target->SetOwner(Person);
  Target->AttachToActor(Person,FAttachmentTransformRules::SnapToTargetNotIncludingScale);Target->SetActorRelativeLocation(FVector(0,0,38));Person->Interaction=Target;
 }
 bReady=Routes.Num()>0;UE_LOG(LogTemp,Display,TEXT("MARE_VILLAGE_READY residents=%d routes=%d"),Residents.Num(),Routes.Num());
}
void UMareVillageWorld::UpdateWalkers(float Dt)
{
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);if(!Hero)return;
 // Mixed/custom presets report overall quality -1; use the actual distance setting.
 const bool Low=UGameUserSettings::GetGameUserSettings()->GetViewDistanceQuality()<=1;int32 Budget=Low?5:12;
 GConfig->GetInt(TEXT("MareCrowd"),Low?TEXT("LowBudget"):TEXT("HighBudget"),Budget,GGameUserSettingsIni);Budget=FMath::Clamp(Budget,0,24);
 if(Pedestrians.Num()<Budget && Routes.Num()){
  const int32 Index=Pedestrians.Num(),Route=Index%Routes.Num();const auto& Points=Routes[Route];const int32 Start=(Index/Routes.Num())%Points.Num();
  if(auto Person=SpawnPerson(Points[Start],Index%4,TEXT("Morador"))){FWalker Walker;Walker.Person=Person;Walker.Route=Route;Walker.Point=FMath::Min(Start+1,Points.Num()-1);Walker.Previous=Person->GetActorLocation();
   Person->WalkTo(Points[Walker.Point]);Pedestrians.Add(Walker);}
 }
 for(int32 I=Pedestrians.Num()-1;I>=0;--I){auto& W=Pedestrians[I];auto P=W.Person.Get();if(!P){Pedestrians.RemoveAt(I);continue;}
  if(I>=Budget){P->Destroy();Pedestrians.RemoveAt(I);continue;}
  P->GetMesh()->SetComponentTickInterval(FVector::DistSquared(P->GetActorLocation(),Hero->GetActorLocation())>FMath::Square(3000.f)?.15f:0.f);
  if(W.Wait>0){W.Wait-=Dt;P->bConversing=W.Wait>1;if(W.Wait<=0)P->WalkTo(Routes[W.Route][W.Point]);continue;}P->bConversing=false;
  const auto& Points=Routes[W.Route];
  if(P->AtGoal()){
   if(W.Point==Points.Num()-1)W.Direction=-1;else if(W.Point==0)W.Direction=1;W.Point+=W.Direction;W.Wait=2.f+(I%4);
   if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();P->PlayPose(TEXT("Idle"));W.Stuck=0;W.BlockedAttempts=0;
  }else if(P->GetVelocity().Size2D()<8)W.Stuck+=Dt;else{W.Stuck=0;W.BlockedAttempts=0;}
  if(W.Stuck>5){
   // A valid path request can still hit a physical obstruction. Do not retry it forever.
   if(++W.BlockedAttempts>=2){W.Direction=-W.Direction;W.Point=FMath::Clamp(W.Point+W.Direction,0,Points.Num()-1);W.BlockedAttempts=0;}
   if(!P->WalkTo(Points[W.Point])){W.Direction=-W.Direction;W.Point=FMath::Clamp(W.Point+W.Direction,0,Points.Num()-1);P->WalkTo(Points[W.Point]);}W.Stuck=0;
  }
  W.Previous=P->GetActorLocation();
 }
}
void UMareVillageWorld::UpdateHotelGuests()
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();bool bHotel=false;
 UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
 if(!bHotel){for(auto P:HotelGuests)if(IsValid(P))P->Destroy();HotelGuests.Empty();return;}
 if(HotelGuests.Num())return;
 // Lobby floor is 45 cm above the terrace; capsule half-height 88 (tools/ue58/hotel_lobby_shell.py layout).
 // Terrace venues follow the Godot hotel_world.gd layout: restaurant floor 155, gym floor 148, pool bar 120.
 struct FSpot{FVector At;float Yaw;int32 Look;bool bTalk,bSeat;const TCHAR* Name;};
 TArray<FSpot> Spots={{FVector(-1390,6565,133),-90,2,true,false,TEXT("Recepcionista")},{FVector(-1390,6330,133),90,0,true,false,TEXT("Hóspede")},
  {FVector(-1560,5760,133),90,3,true,false,TEXT("Hóspede")},{FVector(-1560,5880,133),-90,2,true,false,TEXT("Hóspede")},{FVector(-2600,6690,133),90,1,false,false,TEXT("Hóspede")},
  {FVector(-1290,3000,236),0,1,true,false,TEXT("Hóspede")},{FVector(-1180,3000,236),180,0,true,false,TEXT("Hóspede")},
  {FVector(-2660,4520,208),90,3,true,false,TEXT("Hóspede")},{FVector(-2530,4510,208),110,2,true,false,TEXT("Hóspede")},{FVector(-2600,4760,208),-90,0,false,false,TEXT("Barman")}};
 // Restaurant diners sit on the real chairs (Content/Data/hotel_seats.json, measured from the chair meshes by
 // mare_hud.chair_seats): the old fixed offsets from the table left them in the air or on the backrest. For seats
 // At is the seat top; AMarePerson::SitOn then aligns the animated pelvis on it.
 const struct{int32 Table;bool bBoth;int32 Look;}Tables[]={{0,true,0},{3,true,2},{4,false,1}};   // restaurant.json indices
 for(const auto& T:Tables)for(int32 Side=0;Side<(T.bBoth?2:1);++Side){FVector Seat;float Yaw;
  if(AMarePerson::HotelSeat(T.Table,Side,Seat,Yaw))Spots.Add({Seat,Yaw,Side?(T.Look+3)%4:T.Look,true,true,TEXT("Hóspede")});}
 for(const auto& S:Spots){FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto P=GetWorld()->SpawnActor<AMarePerson>(S.At+FVector(0,0,S.bSeat?60:0),FRotator(0,S.Yaw,0),Params);if(!P)continue;
  if(S.bSeat)P->SitOn(S.At,S.Yaw);
  if(!P->SetAppearance(S.Look)){P->Destroy();continue;}
  P->PersonName=S.Name;P->bAmbient=true;P->bConversing=S.bTalk;P->bSeated=S.bSeat;P->GetCharacterMovement()->DisableMovement();
  if(S.bSeat)P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);else P->GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn,ECR_Block);
  P->Tags.Add(TEXT("MareHotelGuest"));HotelGuests.Add(P);}
}
void UMareVillageWorld::Tick(float Dt)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()) || UGameplayStatics::IsGamePaused(this))return;
 Clock-=Dt;if(Clock>0)return;Clock=.25f;if(!bReady){Setup();if(!bReady)return;}
 UpdateWalkers(.25f);UpdateHotelGuests();
}
void UMareVillageWorld::Speak(AMarePerson* Person,APlayerController* Controller)
{
 if(!IsValid(Person) || !Controller || Dialogue.IsValid() || !GEngine || !GEngine->GameViewport)return;
 auto PC=Cast<AMareController>(Controller);if(!PC || PC->bPhoneOpen)return;
 Speaker=Person;DialogController=Controller;Person->bConversing=true;
 const FString Greeting=Person->PersonName==TEXT("Dona Roberta")?TEXT("Sua avó Dilce sempre disse que você voltaria. O quiosque guardou muitas histórias — agora vai ganhar as suas. Se precisar de ajuda, a vila está por perto."):
  Person->PersonName==TEXT("Seu Gregory")?TEXT("Eu conheci sua avó Dilce quando aquele píer ainda era novo. Venha conversar comigo para ajudar os pescadores e fazer o negócio da família crescer."):
  Person->PersonName==TEXT("Dona Cecília")?TEXT("Bem-vindo de volta! As melhores receitas da vila carregam lembranças. Sua avó Dilce nunca deixava ninguém sair do quiosque sem um sorriso."):
  Person->PersonName==TEXT("Padre Robson")?TEXT("A vila fica melhor quando cuidamos uns dos outros. Sua avó Dilce fez isso por muitos anos. Fico feliz em ver você por aqui."):
  TEXT("Bem-vindo à vila! É bom ver o quiosque da família ganhando vida outra vez.");
 static const FSlateRoundedBoxBrush Card(FLinearColor(.95f,.94f,.88f),12.f);
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 // The giver of the open chapter offers its current step in person.
 FString Story;auto Actions=SNew(SHorizontalBox);TWeakObjectPtr<AMarePerson> WeakPerson(Person);TWeakObjectPtr<APlayerController> WeakController(Controller);
 const FString Result=ActionResult;ActionResult.Empty();
 const auto AddAction=[&](const FString& Label,TFunction<void()> Callback){Actions->AddSlot().AutoWidth().Padding(0,0,8,0)[SNew(SMarePadButton).ContentPadding(FMargin(12,6)).OnClicked_Lambda([this,Sim,Callback,WeakPerson,WeakController](){
  Sim->LastMessage.Empty();Callback();const FString Message=Sim->LastMessage;CloseDialogue();ActionResult=Message;
  if(WeakPerson.IsValid() && WeakController.IsValid())Speak(WeakPerson.Get(),WeakController.Get());return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(Label))]];};
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;
 if(Sim->Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){auto C=Value->AsObject();const FString Id=UMareSimulation::String(C,TEXT("id"));
  if(UMareSimulation::String(C,TEXT("giver"))!=Person->PersonName || !Sim->IsChapterOpen(Id))continue;
  if(Sim->IsChapterDone(Id)){Story=TEXT("Obrigado pela ajuda com \"")+UMareSimulation::String(C,TEXT("title"))+TEXT("\". A vila não vai esquecer.");break;}
  const int32 StepIndex=Sim->ChapterStep(Id);const auto Step=C->GetArrayField(TEXT("steps"))[StepIndex]->AsObject();const FString Kind=UMareSimulation::String(Step,TEXT("kind")),Item=UMareSimulation::String(Step,TEXT("item"));
  int32 Goal=1;const int32 Have=Sim->ChapterStepProgress(Id,Goal);
  Story=(StepIndex==0?UMareSimulation::String(C,TEXT("story"))+TEXT("\n\n"):FString())+FString::Printf(TEXT("%s · passo %d/3: "),*UMareSimulation::String(C,TEXT("title")),StepIndex+1)+UMareSimulation::String(Step,TEXT("text"))+FString::Printf(TEXT(" (%d/%d)"),Have,Goal);
  if(Kind==TEXT("deliver") && Have<Goal){const int32 Missing=Goal-Have;
   AddAction(FString::Printf(TEXT("Comprar %d no mercadinho · R$ %.0f"),Missing,Sim->SupplyCost(Item,Missing)),[Sim,Item,Missing](){Sim->BuySupply(Item,Missing);});}
  else if(Have>=Goal)AddAction(Kind==TEXT("deliver")?FString::Printf(TEXT("Entregar %d do estoque"),Goal):Kind==TEXT("pay")?FString::Printf(TEXT("Doar R$ %d"),Goal):FString(TEXT("Concluir passo")),[Sim,Id](){Sim->AdvanceChapter(Id);});
  break;
 }
 Actions->AddSlot().AutoWidth()[SNew(SMarePadButton).ContentPadding(FMargin(12,6)).OnClicked_Lambda([this](){CloseDialogue();return FReply::Handled();})
  [SNew(STextBlock).Text(MareGamepad::UsingGamepad()?FText::Format(NSLOCTEXT("MareVillage","ByePad","Até logo · {0}"),FText::FromString(MareGamepad::ActionLabel(TEXT("Dive"))))
   :FText::Format(NSLOCTEXT("MareVillage","ByeKeys","Até logo · {0} / {1}"),FText::FromString(MareGamepad::ActionLabel(TEXT("Interact"))),FText::FromString(MareGamepad::ActionLabel(TEXT("Pause")))))]];
 Dialogue=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.25f)).HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(20)
 [SNew(SBox).WidthOverride(580)[SNew(SBorder).BorderImage(&Card).Padding(18)[SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(Person->PersonName)).Font(FCoreStyle::GetDefaultFontStyle("Bold",19)).ColorAndOpacity(FLinearColor(.08f,.16f,.14f))]
  +SVerticalBox::Slot().AutoHeight().Padding(0,9)[SNew(STextBlock).Text(FText::FromString(Story.IsEmpty()?Greeting:Story)).WrapTextAt(544).Font(FCoreStyle::GetDefaultFontStyle("Regular",15)).ColorAndOpacity(FLinearColor(.12f,.13f,.12f))]
  +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[SNew(STextBlock).Text(FText::FromString(Result)).Visibility(Result.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible).WrapTextAt(544).Font(FCoreStyle::GetDefaultFontStyle("Italic",12)).ColorAndOpacity(FLinearColor(.2f,.3f,.27f))]
  +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left)[Actions]]]];
 GEngine->GameViewport->AddViewportWidgetContent(Dialogue.ToSharedRef(),35);
 {const TWeakObjectPtr<UMareVillageWorld> Weak(this);MareGamepad::PushMenu(Dialogue.ToSharedRef(),[Weak](){if(Weak.IsValid())Weak->CloseDialogue();});}
 Controller->bShowMouseCursor=true;Controller->SetInputMode(FInputModeGameAndUI());Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("experience")),TEXT("greeted"))->SetBoolField(Person->PersonName,true);Sim->Save();
}
void UMareVillageWorld::CloseDialogue()
{
 if(GEngine && GEngine->GameViewport && Dialogue.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(Dialogue.ToSharedRef());Dialogue.Reset();
 if(auto Person=Speaker.Get())Person->bConversing=false;Speaker.Reset();
 if(auto PC=DialogController.Get()){PC->bShowMouseCursor=false;PC->SetInputMode(FInputModeGameOnly());PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}DialogController.Reset();
}
void UMareVillageWorld::Deinitialize(){CloseDialogue();Residents.Empty();HotelGuests.Empty();Pedestrians.Empty();Super::Deinitialize();}
