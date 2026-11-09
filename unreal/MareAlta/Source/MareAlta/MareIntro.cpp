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
#include "Camera/CameraComponent.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
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
 if(!LoadBoat()){FinishArrival();return;}
 // The opening shot from the pier: the boat coming in from the open sea, then the view from the passenger bench.
 Camera=GetWorld()->SpawnActor<ACameraActor>(FVector(PierX+280,PierEndY+650,PierZ+260),FRotator::ZeroRotator,Params);   // clear of the fisherman
 if(!Camera){FinishArrival();return;}
 Camera->GetCameraComponent()->SetConstraintAspectRatio(false);   // no letterbox in a non-16:9 window (lesson 06/11)
 Camera->SetActorRotation((BoatPoint(FVector(0,-430,120))-Camera->GetActorLocation()).Rotation());
 Hero->GetCharacterMovement()->StopMovementImmediately();Hero->GetCharacterMovement()->DisableMovement();
 Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 PC->SetViewTarget(Camera);PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);bArrival=true;
 Hero->SetActorHiddenInGame(true);   // the hero's body waits out of sight (it stood on the pier in the shots) until going ashore
}
// 08/11 (Sergio: "herói chega de barco, não de ônibus, na ilha"): the hero arrives by sea, on the tour boat (the lancha of
// Content/Data/tours.json boat_tour, which also gives the waterline, freeboard, helm and benches), docking bow-on at the far
// end of the pier; the boatman stays at the helm and takes the boat back out once the hero is ashore.
bool AMareIntro::LoadBoat()
{
 auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return false;
 BoatDefs=UMareSimulation::Object(Sim->ToursDefs(),TEXT("boat_tour"));
 auto Mesh=LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Custom/TourBoat/%s/%s.%s"),*UMareSimulation::String(BoatDefs,TEXT("mesh")),*UMareSimulation::String(BoatDefs,TEXT("mesh")),*UMareSimulation::String(BoatDefs,TEXT("mesh"))));
 if(!Mesh)return false;
 // The pier, measured: its far end and deck height along x = PierX (the sea itself has no collision).
 FCollisionQueryParams Q(TEXT("MareIntroPier"),true);FHitResult Hit;PierEndY=0;
 for(float Y=-4600.f;Y>-9000.f;Y-=50.f){
  if(GetWorld()->LineTraceSingleByChannel(Hit,FVector(PierX,Y,500),FVector(PierX,Y,-300),ECC_Visibility,Q) && Hit.ImpactPoint.Z>-5.f){PierEndY=Y;PierZ=Hit.ImpactPoint.Z;}
  else if(PierEndY!=0)break;}
 if(PierEndY==0)return false;
 // Transom (the model's origin) 80 cm plus a hull length short of the pier, bow to the island; the run in curves from the open sea.
 Dock=FVector(PierX,PierEndY-80.f-BoatLength,0);
 PathA=Dock+FVector(3600,-15000,0);PathB=Dock+FVector(0,-7000,0);
 FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 Boat=GetWorld()->SpawnActor<AStaticMeshActor>(PathA,FRotator::ZeroRotator,P);if(!Boat)return false;
 auto Root=Boat->GetStaticMeshComponent();Root->SetMobility(EComponentMobility::Movable);Root->SetStaticMesh(Mesh);Root->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 SailTo(0.f);
 const FVector Helm=Vec3(BoatDefs,TEXT("helm"),FVector(45,-30,100));
 Boatman=GetWorld()->SpawnActor<AMarePerson>(BoatPoint(Helm),Boat->GetActorRotation(),P);
 if(Boatman){Boatman->SetAppearance(1);Boatman->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Boatman->GetCharacterMovement()->DisableMovement();
  // A villager with a role (lesson 06/11: no role = beach roster in swimwear), standing at the helm facing the bow.
  Boatman->PersonName=TEXT("Barqueiro");Boatman->bAmbient=true;Boatman->bSeated=true;Boatman->Stage=EMarePersonStage::Eating;Boatman->bConsumed=true;
  Boatman->HoldPose=TEXT("Idle");Boatman->PlayPose(Boatman->HoldPose);   // i18n:skip
  const float Half=Boatman->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
  Boatman->SetActorLocationAndRotation(BoatPoint(FVector(Helm.X,Helm.Y,12))+FVector(0,0,Half),FRotator(0,Heading,0));
  Boatman->AttachToActor(Boat,FAttachmentTransformRules::KeepWorldTransform);}
 return true;
}
FVector AMareIntro::Vec3(const TSharedPtr<FJsonObject>& O,const FString& Key,const FVector& Fallback)
{
 const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O.IsValid() || !O->TryGetArrayField(Key,A) || A->Num()<3)return Fallback;
 return FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),(*A)[2]->AsNumber());
}
FVector AMareIntro::BoatPoint(const FVector& Local)const{return Boat?Boat->GetActorTransform().TransformPosition(Local):Dock;}
void AMareIntro::SailTo(float Travel)
{
 // Quadratic curve from the open sea to the dock; the heading follows the curve.
 const float T=FMath::Clamp(Travel,0.f,1.f);
 const FVector At=(1-T)*(1-T)*PathA+2*(1-T)*T*PathB+T*T*Dock;
 const FVector Tangent=2*(1-T)*(PathB-PathA)+2*T*(Dock-PathB);
 RideWaves(At,Tangent.Rotation().Yaw);
}
void AMareIntro::RideWaves(const FVector& At2D,float NewHeading)
{
 if(!Boat)return;Heading=NewHeading;
 // Like the playable tour (MareBoatTourWorld): heave, pitch and roll from the real sea surface (AMarePerson::SeaHeight),
 // and the sea goes flat inside the hull (ocean material, MPC Boat*).
 static UMaterialParameterCollection* TimeMPC=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
 const float Storm=TimeMPC?UKismetMaterialLibrary::GetScalarParameterValue(this,TimeMPC,TEXT("Storm")):0.f;const float Time=GetWorld()->GetTimeSeconds();
 const FVector F=FRotator(0,Heading,0).Vector(),Rgt(-F.Y,F.X,0);
 auto H=[&](const FVector& P){return AMarePerson::SeaHeight(FVector2D(P.X,P.Y),Time,Storm);};
 const float HBow=H(At2D+F*760),HStern=H(At2D),HPort=H(At2D+F*380-Rgt*120),HStar=H(At2D+F*380+Rgt*120);
 const float SeaZ=UMareSimulation::Number(BoatDefs,TEXT("sea_z"),-30);
 const FVector At(At2D.X,At2D.Y,SeaZ+(HBow+HStern+HPort+HStar)*.25f+UMareSimulation::Number(BoatDefs,TEXT("freeboard"),10));
 const float Pitch=FMath::RadiansToDegrees(FMath::Atan2(HBow-HStern,760.f)),Roll=FMath::RadiansToDegrees(FMath::Atan2(HStar-HPort,240.f))*.7f;
 const FRotator Base=FRotationMatrix::MakeFromYZ(-F,FVector::UpVector).Rotator();   // the model's front is its -Y
 Boat->SetActorLocationAndRotation(At,FRotator(Roll,Base.Yaw,Pitch));
 if(TimeMPC){const FVector Mid=At+F*UMareSimulation::Number(BoatDefs,TEXT("centre"),430);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatX"),Mid.X);UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatY"),Mid.Y);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatYaw"),Heading);UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatOn"),1);
  const float BowDeck=BoatPoint(FVector(0,-780,12)).Z,SternDeck=BoatPoint(FVector(0,-40,12)).Z;
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatH"),FMath::Min(BowDeck,SternDeck)-SeaZ-30);}
}
void AMareIntro::RemoveBoat()
{
 if(BoatSound)BoatSound->Stop();BoatSound=nullptr;
 if(Boatman)Boatman->Destroy();Boatman=nullptr;
 if(Boat)Boat->Destroy();Boat=nullptr;bBoatLeaving=false;
 if(auto MPC=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime")))UKismetMaterialLibrary::SetScalarParameterValue(this,MPC,TEXT("BoatOn"),0);
}
void AMareIntro::AdvanceArrival(float Dt)
{
 auto PC=UGameplayStatics::GetPlayerController(this,0);auto Hero=PC?PC->GetCharacter():nullptr;if(!Hero){FinishArrival();return;}
 ArrivalTime+=Dt;
 auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();
 // No outboard recording yet: the bus diesel, lower and softer, reads as the boat's engine.
 if(ArrivalTime>.25f && !BoatSound){const FVector Position=Boat->GetActorLocation();BoatSound=Audio->PlayCue(TEXT("boat_engine"),.2f,&Position);}   // 09/11: a real boat engine (was the bus engine pitched down)
 if(BoatSound){BoatSound->SetWorldLocation(Boat->GetActorLocation());if(ArrivalTime>SailSeconds)BoatSound->SetVolumeMultiplier(FMath::Max(.06f,.2f*(1.f-(ArrivalTime-SailSeconds)/2.f)));}
 const float T=FMath::Clamp(ArrivalTime/SailSeconds,0.f,1.f);SailTo(1-FMath::Square(1-T));
 Docked=FMath::Clamp((ArrivalTime-SailSeconds)/1.f,0.f,1.f);
 if(ArrivalTime<SailSeconds+1.f){
  if(ArrivalTime>3.f){   // aboard: standing in the bow, ahead of the canopy (from the bench it filled the view), looking at the island
   Camera->SetActorLocation(BoatPoint(FVector(0,-690,150)));
   const FRotator Ahead(-3.f,Heading,Boat->GetActorRotation().Roll*.5f);   // level: the boat's own roll only in part
   Camera->SetActorRotation(ArrivalTime<3.2f?Ahead:FMath::RInterpTo(Camera->GetActorRotation(),Ahead,Dt,5.f));}
  else Camera->SetActorRotation((BoatPoint(FVector(0,-430,120))-Camera->GetActorLocation()).Rotation());
  return;
 }
 if(!bDisembarking){bDisembarking=true;Hero->SetActorHiddenInGame(false);PC->SetViewTarget(Hero);if(auto Body=Hero->FindComponentByClass<UMarePlayerPresentation>())Body->SetScriptedWalking(true);}
 // From the bow (ahead of the canopy, which filled the view from the bench) up onto the pier and along it.
 const FVector Steps[5]={BoatPoint(FVector(0,-640,14)),BoatPoint(FVector(0,-760,20)),FVector(PierX,PierEndY-40,PierZ),
  FVector(PierX,PierEndY-10,PierZ),FVector(PierX,PierEndY+450,PierZ)};
 DisembarkTime+=Dt;const float Progress=FMath::Clamp(DisembarkTime/DisembarkSeconds,0.f,1.f)*4.f;
 const int32 Index=FMath::Min(FMath::FloorToInt(Progress),3);const float S=Progress-Index;
 Hero->SetActorLocation(FMath::Lerp(Steps[Index],Steps[Index+1],S)+FVector(0,0,Hero->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),false,nullptr,ETeleportType::TeleportPhysics);
 Hero->SetActorRotation(FRotator(0,90,0));PC->SetControlRotation(FRotator(-8,90,0));
 StepClock-=Dt;if(StepClock<=0){Audio->PlayCue(*FString::Printf(TEXT("footstep_wood_%03d"),FMath::RandRange(0,4)),.15f);StepClock=.55f;}
 if(DisembarkTime>=DisembarkSeconds)FinishArrival();
}
void AMareIntro::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 if(bBoatLeaving && Boat){
  // Back out from the pier, then turn round and head out to sea.
  LeaveTime+=DeltaSeconds;
  if(LeaveTime<4.f)SailTo(1.f-.12f*FMath::SmoothStep(0.f,1.f,LeaveTime/4.f));
  else{if(LeavePos.IsZero()){LeavePos=Boat->GetActorLocation();LeavePos.Z=0;}
   const float NewHeading=FMath::FixedTurn(Heading,-90.f,22.f*DeltaSeconds);LeaveSpeed=FMath::Min(700.f,LeaveSpeed+160.f*DeltaSeconds);
   LeavePos+=FRotator(0,NewHeading,0).Vector()*LeaveSpeed*DeltaSeconds;RideWaves(LeavePos,NewHeading);}
  if(BoatSound)BoatSound->SetWorldLocation(Boat->GetActorLocation());
  if(LeaveTime>20.f)RemoveBoat();
  return;
 }
 if(bArrival && Boat)AdvanceArrival(DeltaSeconds);
}
void AMareIntro::FinishArrival()
{
 auto PC=UGameplayStatics::GetPlayerController(this,0);auto Hero=PC?PC->GetCharacter():nullptr;
 if(PC && Hero){
  // Ashore at the pier, facing the village (skipping the scene lands there too).
  PC->SetViewTarget(Hero);Hero->SetActorHiddenInGame(false);
  const FVector Ashore=PierEndY!=0?FVector(PierX,PierEndY+450,PierZ):FVector(7200,-4700,32);
  Hero->SetActorLocation(Ashore+FVector(0,0,Hero->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+2),false,nullptr,ETeleportType::TeleportPhysics);
  Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Hero->GetCharacterMovement()->StopMovementImmediately();Hero->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
  if(auto Body=Hero->FindComponentByClass<UMarePlayerPresentation>())Body->SetScriptedWalking(false);
  PC->SetControlRotation(FRotator(0,90,0));PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();
 }
 bArrival=false;bDisembarking=false;
 if(Boat){if(ArrivalTime<SailSeconds)RemoveBoat();else{bBoatLeaving=true;LeaveTime=0;LeaveSpeed=0;LeavePos=FVector::ZeroVector;}}
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
