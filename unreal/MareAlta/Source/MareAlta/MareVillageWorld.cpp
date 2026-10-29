#include "MareVillageWorld.h"
#include "MareGame.h"
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
 Person->GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
 Person->Tags.Add(TEXT("MareVillagePerson"));return Person;
}
void UMareVillageWorld::Setup()
{
 FString Text;TSharedPtr<FJsonObject> Data;
 if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/village_routes.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Data))return;
 const auto Vector=[](const TArray<TSharedPtr<FJsonValue>>& A){return FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());};
 for(const auto& Item:Data->GetArrayField(TEXT("routes"))){TArray<FVector> Points;for(const auto& P:Item->AsObject()->GetArrayField(TEXT("points")))Points.Add(Vector(P->AsArray()));if(Points.Num()>1)Routes.Add(Points);}
 int32 Variant=0;
 for(const auto& Item:Data->GetArrayField(TEXT("residents"))){auto Row=Item->AsObject();auto Person=SpawnPerson(Vector(Row->GetArrayField(TEXT("position"))),Variant++%4,UMareSimulation::String(Row,TEXT("name")));if(!Person)continue;
  Person->SetActorRotation(FRotator(0,UMareSimulation::Number(Row,TEXT("yaw")),0));Residents.Add(Person);
  auto Target=GetWorld()->SpawnActor<AMareServiceTarget>();Target->Action=TEXT("Resident");Target->Label=Person->PersonName+TEXT(" · conversar");Target->Reach=260;Target->OcclusionTolerance=40;Target->SetOwner(Person);
  Target->AttachToActor(Person,FAttachmentTransformRules::SnapToTargetNotIncludingScale);Target->SetActorRelativeLocation(FVector(0,0,38));Person->Interaction=Target;
 }
 bReady=Routes.Num()>0;UE_LOG(LogTemp,Display,TEXT("MARE_VILLAGE_READY residents=%d routes=%d"),Residents.Num(),Routes.Num());
}
void UMareVillageWorld::UpdateWalkers(float Dt)
{
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);if(!Hero)return;
 const bool Low=UGameUserSettings::GetGameUserSettings()->GetOverallScalabilityLevel()<=1;int32 Budget=Low?5:12;
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
   if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();P->PlayPose(TEXT("Idle"));W.Stuck=0;
  }else if(P->GetVelocity().Size2D()<8)W.Stuck+=Dt;else W.Stuck=0;
  if(W.Stuck>5){if(!P->WalkTo(Points[W.Point])){W.Direction=-W.Direction;W.Point=FMath::Clamp(W.Point+W.Direction,0,Points.Num()-1);P->WalkTo(Points[W.Point]);}W.Stuck=0;}
  W.Previous=P->GetActorLocation();
 }
}
void UMareVillageWorld::Tick(float Dt)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()) || UGameplayStatics::IsGamePaused(this))return;
 Clock-=Dt;if(Clock>0)return;Clock=.25f;if(!bReady){Setup();if(!bReady)return;}
 UpdateWalkers(.25f);
}
void UMareVillageWorld::Speak(AMarePerson* Person,APlayerController* Controller)
{
 if(!IsValid(Person) || !Controller || Dialogue.IsValid() || !GEngine || !GEngine->GameViewport)return;
 auto PC=Cast<AMareController>(Controller);if(!PC || PC->bPhoneOpen)return;
 Speaker=Person;DialogController=Controller;Person->bConversing=true;
 const FString Greeting=Person->PersonName==TEXT("Dona Rita")?TEXT("Seu avô sempre disse que você voltaria. O quiosque guardou muitas histórias — agora vai ganhar as suas. Se precisar de ajuda, a vila está por perto."):
  Person->PersonName==TEXT("Seu Zé")?TEXT("Eu conheci seu avô quando aquele píer ainda era novo. Venha conversar comigo para ajudar os pescadores e fazer o negócio da família crescer."):
  Person->PersonName==TEXT("Dona Lourdes")?TEXT("Bem-vindo de volta! As melhores receitas da vila carregam lembranças. Seu avô nunca deixava ninguém sair do quiosque sem um sorriso."):
  Person->PersonName==TEXT("Padre Tomé")?TEXT("A vila fica melhor quando cuidamos uns dos outros. Seu avô fez isso por muitos anos. Fico feliz em ver você por aqui."):
  TEXT("Bem-vindo à vila! É bom ver o quiosque da família ganhando vida outra vez.");
 static const FSlateRoundedBoxBrush Card(FLinearColor(.95f,.94f,.88f),12.f);
 Dialogue=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.25f)).HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(20)
 [SNew(SBox).MaxDesiredWidth(580)[SNew(SBorder).BorderImage(&Card).Padding(18)[SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(Person->PersonName)).Font(FCoreStyle::GetDefaultFontStyle("Bold",19)).ColorAndOpacity(FLinearColor(.08f,.16f,.14f))]
  +SVerticalBox::Slot().AutoHeight().Padding(0,9)[SNew(STextBlock).Text(FText::FromString(Greeting)).AutoWrapText(true).Font(FCoreStyle::GetDefaultFontStyle("Regular",15)).ColorAndOpacity(FLinearColor(.12f,.13f,.12f))]
  +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left)[SNew(SButton).ContentPadding(FMargin(12,6)).OnClicked_Lambda([this](){CloseDialogue();return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(TEXT("Até logo · E / Esc")))]]]]];
 GEngine->GameViewport->AddViewportWidgetContent(Dialogue.ToSharedRef(),35);Controller->bShowMouseCursor=true;Controller->SetInputMode(FInputModeGameAndUI());Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("experience")),TEXT("greeted"))->SetBoolField(Person->PersonName,true);Sim->Save();
}
void UMareVillageWorld::CloseDialogue()
{
 if(GEngine && GEngine->GameViewport && Dialogue.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(Dialogue.ToSharedRef());Dialogue.Reset();
 if(auto Person=Speaker.Get())Person->bConversing=false;Speaker.Reset();
 if(auto PC=DialogController.Get()){PC->bShowMouseCursor=false;PC->SetInputMode(FInputModeGameOnly());PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}DialogController.Reset();
}
void UMareVillageWorld::Deinitialize(){CloseDialogue();Residents.Empty();Pedestrians.Empty();Super::Deinitialize();}
