#include "MareIntro.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/TextRenderActor.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"

AMareIntro::AMareIntro(){PrimaryActorTick.bCanEverTick=true;}
void AMareIntro::BeginPlay()
{
 Super::BeginPlay();auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();
 if(!Sim || !Sim->State->HasField(TEXT("ue_intro_stage"))) {Destroy();return;}
 auto PC=UGameplayStatics::GetPlayerController(this,0);auto Hero=PC?PC->GetCharacter():nullptr;if(!Hero){Destroy();return;}
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 // The note sits on the small table in the accessible living room. It remains available after reading.
 LetterPaper=GetWorld()->SpawnActor<AStaticMeshActor>(FVector(4435,2237,58),FRotator::ZeroRotator,Params);
 if(auto Paper=Cast<AStaticMeshActor>(LetterPaper)){
  auto Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane"));auto C=Paper->GetStaticMeshComponent();
  C->SetMobility(EComponentMobility::Movable);C->SetStaticMesh(Mesh);C->SetWorldScale3D(FVector(.23,.16,1));C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 }
 LetterTarget=GetWorld()->SpawnActor<AMareServiceTarget>(FVector(4435,2237,58),FRotator::ZeroRotator,Params);
 if(LetterTarget){LetterTarget->Action=TEXT("IntroLetter");LetterTarget->Label=TEXT("Carta do avô");LetterTarget->Reach=220;LetterTarget->OcclusionTolerance=100;LetterTarget->SetOwner(this);}
 if(UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)!=0)return;
 Bus=GetWorld()->SpawnActor<AStaticMeshActor>(FVector(6500,3000,170),FRotator(0,180,0),Params);
 auto BusMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Intro/Bus/bus.bus"));
 if(!Bus || !BusMesh){if(Bus)Bus->Destroy();FinishArrival();return;}
 auto Comp=Bus->GetStaticMeshComponent();Comp->SetMobility(EComponentMobility::Movable);Comp->SetStaticMesh(BusMesh);Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 // Imported mesh has an offset origin; compensate so its lower bounds remain on the road.
 const FBoxSphereBounds Bounds=BusMesh->GetBounds();
 const FVector RotatedOrigin=Bus->GetActorRotation().RotateVector(Bounds.Origin);
 Bus->SetActorLocation(FVector(6500-RotatedOrigin.X,3000-RotatedOrigin.Y,12-Bounds.Origin.Z+Bounds.BoxExtent.Z));
 const int32 GlassSlot=BusMesh->GetMaterialIndex(TEXT("Windows"));
 if(GlassSlot!=INDEX_NONE)if(auto Neutral=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Intro/Bus/Metal.Metal")))Comp->SetMaterial(GlassSlot,Neutral);
 Camera=GetWorld()->SpawnActor<ACameraActor>(FVector(4700,2900,190),FRotator::ZeroRotator,Params);
 if(!Camera){FinishArrival();return;}
 Camera->SetActorRotation((FVector(6000,3000,130)-Camera->GetActorLocation()).Rotation());
 PC->SetViewTarget(Camera);PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);bArrival=true;
}
void AMareIntro::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);if(bBusDeparting && Bus){DepartureTime+=DeltaSeconds;Bus->AddActorWorldOffset(FVector(-190.f*DeltaSeconds,0,0));if(DepartureTime>9.f){Bus->Destroy();bBusDeparting=false;}return;}
 if(!bArrival || !Bus)return;
 if(bDisembarking){DisembarkTime+=DeltaSeconds;auto PC=UGameplayStatics::GetPlayerController(this,0);if(auto Hero=PC?PC->GetCharacter():nullptr)Hero->SetActorLocation(FMath::Lerp(FVector(5330,2850,145),FVector(5200,2700,100),FMath::Clamp(DisembarkTime/2.f,0.f,1.f)),false,nullptr,ETeleportType::TeleportPhysics);if(DisembarkTime>=2.f)FinishArrival();return;}
 ArrivalTime+=DeltaSeconds;
 FVector Position=Bus->GetActorLocation();Position.X-=130.f*DeltaSeconds;Bus->SetActorLocation(Position);
 if(ArrivalTime>=9.f){bDisembarking=true;auto PC=UGameplayStatics::GetPlayerController(this,0);if(auto Hero=PC?PC->GetCharacter():nullptr){Hero->GetCharacterMovement()->StopMovementImmediately();Hero->SetActorLocation(FVector(5330,2850,145),false,nullptr,ETeleportType::TeleportPhysics);PC->SetControlRotation(FRotator(0,-150,0));PC->SetViewTarget(Hero);}else FinishArrival();}
}
void AMareIntro::FinishArrival()
{
 auto PC=UGameplayStatics::GetPlayerController(this,0);auto Hero=PC?PC->GetCharacter():nullptr;
 if(PC && Hero){PC->SetViewTarget(Hero);Hero->SetActorLocation(FVector(5200,2700,100),false,nullptr,ETeleportType::TeleportPhysics);Hero->GetCharacterMovement()->StopMovementImmediately();PC->SetControlRotation(FRotator(0,-150,0));PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}
 bArrival=false;bDisembarking=false;if(Bus){if(ArrivalTime<8.f)Bus->Destroy();else bBusDeparting=true;}if(Camera)Camera->Destroy();
 if(auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>()){Sim->State->SetNumberField(TEXT("ue_intro_stage"),1);Sim->Save();}
}
void AMareIntro::ReadLetter()
{
 if(LetterWidget.IsValid() || !GEngine || !GEngine->GameViewport)return;
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));if(!PC || PC->bPhoneOpen || GetWorld()->IsPaused())return;
 static const FSlateRoundedBoxBrush Card(FLinearColor(.95f,.91f,.81f),12.f);
 const FString Letter=TEXT("Meu neto,\n\nSe você está lendo esta carta, chegou à nossa vila. Ainda me lembro de você pequeno, correndo pela areia enquanto eu abria o quiosque. Você dizia que o mar tinha cheiro de aventura. Eu respondia que também tinha cheiro de casa.\n\nNosso negócio começou com um balcão, alguns cocos e a vontade de acolher quem chegava. Nem todos os dias foram fáceis. Quando o vento virou, foram as pessoas da vila que nos ajudaram a continuar. Cada cadeira guarda uma conversa; cada freguês deixou um pedacinho de sua história conosco.\n\nHoje minhas mãos precisam descansar um pouco mais, mas o sonho da família ainda tem muito caminho pela frente. Quero passar o quiosque para você. Abra as portas, conheça nossos vizinhos e faça deste lugar também o seu lugar.\n\nSe puder, ajude o negócio a crescer. Mas lembre-se de que o que construímos de mais valioso nunca coube em uma caixa registradora: foi o carinho com que recebemos cada pessoa.\n\nNão tenha pressa. Mesmo de longe, vou torcer por você a cada nova maré.\n\nCom todo meu amor,\nVô");
 auto Text=SNew(STextBlock).Text(FText::FromString(Letter)).Font(FCoreStyle::GetDefaultFontStyle("Regular",16)).ColorAndOpacity(FLinearColor(.15f,.13f,.1f)).AutoWrapText(true);
 LetterWidget=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.75)).HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(570).MaxDesiredHeight(620)[SNew(SBorder).BorderImage(&Card).Padding(24)[SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,12)[SNew(STextBlock).Text(FText::FromString(TEXT("Uma carta para você"))).Font(FCoreStyle::GetDefaultFontStyle("Bold",22)).ColorAndOpacity(FLinearColor(.18f,.15f,.1f))]
  +SVerticalBox::Slot().FillHeight(1)[SNew(SScrollBox)+SScrollBox::Slot()[Text]]
  +SVerticalBox::Slot().AutoHeight().Padding(0,8,0,0)[SNew(STextBlock).Text(FText::FromString(TEXT("Role para ler toda a carta"))).Font(FCoreStyle::GetDefaultFontStyle("Regular",11)).ColorAndOpacity(FLinearColor(.25f,.22f,.18f))]
  +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left).Padding(0,16,0,0)[SNew(SButton).ContentPadding(FMargin(14,8)).OnClicked_Lambda([this](){CloseLetter();return FReply::Handled();})[SNew(STextBlock).Text(FText::FromString(TEXT("Guardar a carta")))]]]]];
 GEngine->GameViewport->AddViewportWidgetContent(LetterWidget.ToSharedRef(),40);PC->bShowMouseCursor=true;PC->SetInputMode(FInputModeGameAndUI());PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);
}
void AMareIntro::CloseLetter()
{
 if(!LetterWidget.IsValid())return;
 if(GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(LetterWidget.ToSharedRef());LetterWidget.Reset();
 if(auto PC=UGameplayStatics::GetPlayerController(this,0)){PC->bShowMouseCursor=false;PC->SetInputMode(FInputModeGameOnly());PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}
 if(auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>()){Sim->State->SetNumberField(TEXT("ue_intro_stage"),2);Sim->Save();}
}
