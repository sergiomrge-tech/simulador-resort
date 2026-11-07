#include "MareIntro.h"
#include "MareLoc.h"
#include "MareGame.h"
#include "MareGamepad.h"
#include "MareNotebookStyle.h"
#include "MareSimulation.h"
#include "MarePlayerPresentation.h"
#include "MareAudioWorld.h"
#include "MarePerson.h"
#include "Components/CapsuleComponent.h"
#include "Components/AudioComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
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
  auto Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Intro/Refined/Letter_Home/Letter_Home.Letter_Home"));auto C=Paper->GetStaticMeshComponent();
  C->SetMobility(EComponentMobility::Movable);C->SetStaticMesh(Mesh);C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 }
 LetterTarget=GetWorld()->SpawnActor<AMareServiceTarget>(FVector(4435,2237,58),FRotator::ZeroRotator,Params);
 if(LetterTarget){LetterTarget->Action=TEXT("IntroLetter");LetterTarget->Label=TEXT("Carta da avó Dilce");LetterTarget->Reach=275;LetterTarget->OcclusionTolerance=100;LetterTarget->SetOwner(this);}
 if(UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)!=0)return;
 if(!LoadBus()){FinishArrival();return;}
 Camera=GetWorld()->SpawnActor<ACameraActor>(FVector(5950,2580,235),FRotator::ZeroRotator,Params);
 if(!Camera){FinishArrival();return;}
 Camera->SetActorRotation((BusPoint(FVector(100,0,120))-Camera->GetActorLocation()).Rotation());
 Hero->GetCharacterMovement()->StopMovementImmediately();Hero->GetCharacterMovement()->DisableMovement();
 Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 PC->SetViewTarget(Camera);PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);bArrival=true;
}
bool AMareIntro::LoadBus()
{
 FString Text;TSharedPtr<FJsonObject> Data;
 if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/intro_refined_bus.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Data))return false;
 const auto Vector=[](const TSharedPtr<FJsonObject>& Row,const FString& Key){const auto& A=Row->GetArrayField(Key);return FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());};
 auto Parts=UMareSimulation::Object(Data,TEXT("parts"));
 auto Cabin=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(UMareSimulation::Object(Parts,TEXT("Bus_Cabin")),TEXT("mesh")));
 if(!Cabin)return false;
 Bus=GetWorld()->SpawnActor<AStaticMeshActor>();auto Root=Bus->GetStaticMeshComponent();Root->SetMobility(EComponentMobility::Movable);
 Root->SetStaticMesh(Cabin);Root->SetCollisionEnabled(ECollisionEnabled::NoCollision);Bus->SetActorLocationAndRotation(StartPosition,FRotator(0,180,0));
 for(const FString Name:{TEXT("Bus_Door"),TEXT("wheelFL"),TEXT("wheelFR"),TEXT("wheelLR"),TEXT("wheelRR")}){
  auto Row=UMareSimulation::Object(Parts,Name);auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(Row,TEXT("mesh")));if(!Mesh){Bus->Destroy();Bus=nullptr;return false;}
  auto Part=NewObject<UStaticMeshComponent>(Bus);Bus->AddInstanceComponent(Part);Part->SetupAttachment(Root);Part->SetMobility(EComponentMobility::Movable);
  Part->SetStaticMesh(Mesh);Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);Part->SetRelativeLocation(Vector(Row,TEXT("position")));Part->RegisterComponent();
  if(Name==TEXT("Bus_Door"))BusDoor=Part;else BusWheels.Add(Part);
 }
 InteriorCamera=Vector(Data,TEXT("interior_camera"));FrontLook=Vector(Data,TEXT("front_look"));DoorYaw=UMareSimulation::Number(Data,TEXT("door_swing_yaw"),-85);
 for(const auto& Item:Data->GetArrayField(TEXT("steps"))){const auto& A=Item->AsArray();ExitSteps.Add(FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber()));}
 BusDriver=GetWorld()->SpawnActor<AMarePerson>(BusPoint(FVector(390,-53,150)),Bus->GetActorRotation());
 if(BusDriver){BusDriver->SetAppearance(2);BusDriver->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);BusDriver->GetCharacterMovement()->DisableMovement();
  // 06/11 (CHECKLIST 0, photo of the seated driver): with no role he took the beach roster and drove the bus in a bikini.
  // A seated villager (village roster, casual clothes); seated keeps the events from making him dance.
  BusDriver->PersonName=TEXT("Motorista");BusDriver->bAmbient=true;BusDriver->bSeated=true;
  BusDriver->Stage=EMarePersonStage::Eating;BusDriver->bConsumed=true;BusDriver->HoldPose=TEXT("Sitting_Idle");BusDriver->PlayPose(TEXT("Sitting_Idle"));BusDriver->AttachToActor(Bus,FAttachmentTransformRules::KeepWorldTransform);}
 return ExitSteps.Num()>=5;
}
FVector AMareIntro::BusPoint(const FVector& Local)const{return Bus?Bus->GetActorTransform().TransformPosition(Local):StopPosition+FRotator(0,180,0).RotateVector(Local);}
void AMareIntro::AnimateBus(float Distance)
{
 WheelAngle+=FMath::RadiansToDegrees(Distance/35.6f);
 for(auto Wheel:BusWheels)if(IsValid(Wheel))Wheel->SetRelativeRotation(FRotator(WheelAngle,0,0));
 if(IsValid(BusDoor))BusDoor->SetRelativeRotation(FRotator(0,DoorYaw*DoorOpen,0));
 if(IsValid(BusDriver))BusDriver->AddActorWorldOffset(BusPoint(FVector(390,-53,106))-BusDriver->GetMesh()->GetSocketLocation(TEXT("pelvis")));
}
void AMareIntro::AdvanceArrival(float Dt)
{
 auto PC=UGameplayStatics::GetPlayerController(this,0);auto Hero=PC?PC->GetCharacter():nullptr;if(!Hero){FinishArrival();return;}
 const float PreviousTime=ArrivalTime;ArrivalTime+=Dt;
 auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();
 if(ArrivalTime>.25f && !BusSound){const FVector Position=Bus->GetActorLocation();BusSound=Audio->PlayCue(TEXT("bus_engine"),.20f,&Position);}
 if(BusSound)BusSound->SetWorldLocation(Bus->GetActorLocation());
 if(PreviousTime<7.6f && ArrivalTime>=7.6f)Audio->PlayCue(TEXT("bus_brake"),.17f);
 if(ArrivalTime<=8.f){
  const float T=FMath::Clamp(ArrivalTime/8.f,0.f,1.f),Travel=1-FMath::Square(1-T);
  const FVector Before=Bus->GetActorLocation();Bus->SetActorLocation(FMath::Lerp(StartPosition,StopPosition,Travel));AnimateBus(FVector::Dist(Before,Bus->GetActorLocation()));
  if(ArrivalTime>2.f){Camera->SetActorLocation(BusPoint(InteriorCamera));Camera->SetActorRotation((BusPoint(FrontLook)-Camera->GetActorLocation()).Rotation());}
  else Camera->SetActorRotation((BusPoint(FVector(100,0,120))-Camera->GetActorLocation()).Rotation());
  return;
 }
 Bus->SetActorLocation(StopPosition);DoorOpen=FMath::Clamp((ArrivalTime-8.f)/1.2f,0.f,1.f);AnimateBus(0);
 if(ArrivalTime<9.2f)return;
 if(!bDisembarking){bDisembarking=true;PC->SetViewTarget(Hero);if(auto Body=Hero->FindComponentByClass<UMarePlayerPresentation>())Body->SetScriptedWalking(true);}
 DisembarkTime+=Dt;const float Progress=FMath::Clamp(DisembarkTime/4.5f,0.f,1.f)*(ExitSteps.Num()-1);
 const int32 Index=FMath::Min(FMath::FloorToInt(Progress),ExitSteps.Num()-2);const float T=Progress-Index;
 const FVector Foot=BusPoint(FMath::Lerp(ExitSteps[Index],ExitSteps[Index+1],T));
 Hero->SetActorLocation(Foot+FVector(0,0,88),false,nullptr,ETeleportType::TeleportPhysics);
 Hero->SetActorRotation(FRotator(0,-90,0));PC->SetControlRotation(FRotator(-12,-90,0));
 StepClock-=Dt;if(StepClock<=0){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("footstep_concrete_002"),.15f);StepClock=.55f;}
 if(DisembarkTime>=4.5f)FinishArrival();
}
void AMareIntro::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 if(bBusDeparting && Bus){
  DepartureTime+=DeltaSeconds;DoorOpen=FMath::Max(0.f,1.f-DepartureTime/1.2f);const float Distance=FMath::Max(0.f,DepartureTime-1.2f)*42.f*DeltaSeconds;
  Bus->AddActorWorldOffset(Bus->GetActorForwardVector()*Distance);AnimateBus(Distance);
  if(BusSound)BusSound->SetWorldLocation(Bus->GetActorLocation());
  if(DepartureTime>13.f){if(BusSound)BusSound->Stop();if(BusDriver)BusDriver->Destroy();Bus->Destroy();Bus=nullptr;bBusDeparting=false;}return;
 }
 if(bArrival && Bus)AdvanceArrival(DeltaSeconds);
}
void AMareIntro::FinishArrival()
{
 auto PC=UGameplayStatics::GetPlayerController(this,0);auto Hero=PC?PC->GetCharacter():nullptr;
 if(PC && Hero){
  PC->SetViewTarget(Hero);Hero->SetActorLocation(FVector(5000,2775,100),false,nullptr,ETeleportType::TeleportPhysics);
  Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Hero->GetCharacterMovement()->StopMovementImmediately();Hero->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
  if(auto Body=Hero->FindComponentByClass<UMarePlayerPresentation>())Body->SetScriptedWalking(false);
  PC->SetControlRotation(FRotator(0,-150,0));PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();
 }
 bArrival=false;bDisembarking=false;
 if(Bus){if(ArrivalTime<9.f){if(BusSound)BusSound->Stop();if(BusDriver)BusDriver->Destroy();Bus->Destroy();Bus=nullptr;}else bBusDeparting=true;}
 if(Camera){Camera->Destroy();Camera=nullptr;}
 if(auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>()){Sim->State->SetNumberField(TEXT("ue_intro_stage"),1);Sim->Save();}
}
void AMareIntro::ReadLetter()
{
 if(LetterWidget.IsValid() || !GEngine || !GEngine->GameViewport)return;
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));if(!PC || PC->bPhoneOpen || GetWorld()->IsPaused())return;
 const FString Letter=TEXT("Meu neto,\n\nSe você está lendo esta carta, chegou à nossa vila. Ainda me lembro de você pequeno, correndo pela areia enquanto eu abria o quiosque. Você dizia que o mar tinha cheiro de aventura. Eu respondia que também tinha cheiro de casa.\n\nNosso negócio começou com um balcão, alguns cocos e a vontade de acolher quem chegava. Nem todos os dias foram fáceis. Quando o vento virou, foram as pessoas da vila que nos ajudaram a continuar. Cada cadeira guarda uma conversa; cada freguês deixou um pedacinho de sua história conosco.\n\nHoje minhas mãos precisam descansar um pouco mais, mas o sonho da família ainda tem muito caminho pela frente. Quero passar o quiosque para você. Abra as portas, conheça nossos vizinhos e faça deste lugar também o seu lugar.\n\nSe puder, ajude o negócio a crescer. Mas lembre-se de que o que construímos de mais valioso nunca coube em uma caixa registradora: foi o carinho com que recebemos cada pessoa.\n\nNão tenha pressa. Mesmo de longe, vou torcer por você a cada nova maré.\n\nCom todo meu amor,\nVó Dilce");
 auto Text=SNew(STextBlock).Text(MareLoc::Text(Letter)).Font(MareNotebook::Hand(20)).ColorAndOpacity(MareNotebook::Ink).AutoWrapText(true);
 LetterWidget=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.75)).HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(720).MaxDesiredHeight(860)[MareNotebook::Page(SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,12)[SNew(STextBlock).Text(MareLoc::Text(TEXT("Uma carta para você"))).Font(MareNotebook::Hand(30)).ColorAndOpacity(MareNotebook::Brown)]
  +SVerticalBox::Slot().FillHeight(1)[SNew(SMareFit).Name(TEXT("letter")).MinScale(.55f)[Text]]
  +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Left).Padding(0,16,0,0)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(12,3)).OnClicked_Lambda([this](){CloseLetter();return FReply::Handled();})[MareNotebook::InkLabel(TEXT("Guardar a carta"),18)]])]];
 GEngine->GameViewport->AddViewportWidgetContent(LetterWidget.ToSharedRef(),40);
 {const TWeakObjectPtr<AMareIntro> Weak(this);MareGamepad::PushMenu(LetterWidget.ToSharedRef(),[Weak](){if(Weak.IsValid())Weak->CloseLetter();});}
 PC->bShowMouseCursor=true;PC->SetInputMode(FInputModeGameAndUI());PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);
}
void AMareIntro::CloseLetter()
{
 if(!LetterWidget.IsValid())return;
 if(GEngine && GEngine->GameViewport)GEngine->GameViewport->RemoveViewportWidgetContent(LetterWidget.ToSharedRef());LetterWidget.Reset();
 if(auto PC=UGameplayStatics::GetPlayerController(this,0)){PC->bShowMouseCursor=false;PC->SetInputMode(FInputModeGameOnly());PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}
 if(auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>()){Sim->State->SetNumberField(TEXT("ue_intro_stage"),2);Sim->Save();}
}
