#include "MareIntroQA.h"
#include "MareIntro.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"

AMareIntroQA::AMareIntroQA(){PrimaryActorTick.bCanEverTick=true;}
void AMareIntroQA::Check(const FString& Name,bool Passed){auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("name"),Name);Row->SetBoolField(TEXT("pass"),Passed);Checks.Add(MakeShared<FJsonValueObject>(Row));UE_LOG(LogTemp,Display,TEXT("INTRO QA %s %s"),*Name,Passed?TEXT("PASS"):TEXT("FAIL"));}
void AMareIntroQA::WalkTo(const FVector& Position){WalkTarget=Position;bWalking=true;WalkDeadline=FPlatformTime::Seconds()+35;Next=0;}
void AMareIntroQA::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 if(Root.IsEmpty()){FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Root);Root.ReplaceInline(TEXT("\\"),TEXT("/"));if(!Root.StartsWith(TEXT("D:/CodexTemp/"))){Destroy();return;}Next=FPlatformTime::Seconds()+.9;}
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));auto Hero=PC?Cast<AMareCharacter>(PC->GetPawn()):nullptr;if(!Hero)return;
 auto Sim=PC->GetSimulation();auto Eyes=Hero->FindComponentByClass<UCameraComponent>();AMareIntro* Intro=nullptr;AMareServiceTarget* Door=nullptr;
 for(TActorIterator<AMareIntro> It(GetWorld());It;++It){Intro=*It;break;}
 for(TActorIterator<AMareServiceTarget> It(GetWorld());It;++It)if(It->Action==TEXT("Door") && It->bAutoClose){Door=*It;break;}
 if(bWalking){
  const FVector Delta=WalkTarget-Hero->GetActorLocation();
  if(Delta.Size2D()>28 && FPlatformTime::Seconds()<WalkDeadline){Hero->AddMovementInput(Delta.GetSafeNormal2D());PC->SetControlRotation(FRotator(0,Delta.Rotation().Yaw,0));return;}
  Check(FString::Printf(TEXT("home_walk_segment_%d"),Phase),Delta.Size2D()<=28);bWalking=false;Hero->GetCharacterMovement()->StopMovementImmediately();
 }
 if(FPlatformTime::Seconds()<Next)return;
 const bool Natural=FParse::Param(FCommandLine::Get(),TEXT("MareIntroNaturalQA"));
 auto Capture=[this](const FString& Name){FScreenshotRequest::RequestScreenshot(Root/(Name+TEXT(".png")),true,false);};
 switch(Phase++){
 case 0:Check(TEXT("new_save_arrival_active"),Intro && Intro->IsArrival() && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)==0);Check(TEXT("refined_bus_loaded"),Intro && Intro->HasRefinedBus());Capture(TEXT("intro-bus"));Next=FPlatformTime::Seconds()+3.2;break;
 case 1:Capture(TEXT("intro-interior"));if(!Natural){if(Intro)Intro->FinishArrival();Phase=4;}Next=FPlatformTime::Seconds()+(Natural?4.4:1);break;
 case 2:Check(TEXT("bus_door_opens"),Intro && Intro->DoorFraction()>.1f);Capture(TEXT("intro-door"));Next=FPlatformTime::Seconds()+2;break;
 case 3:Capture(TEXT("intro-stairs"));Next=FPlatformTime::Seconds()+4;break;
 case 4:
  Check(Natural?TEXT("arrival_finishes_naturally"):TEXT("arrival_can_be_skipped"),Intro && !Intro->IsArrival() && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)==1 && !PC->IsMoveInputIgnored());Capture(TEXT("intro-after-arrival"));
  Hero->GetCharacterMovement()->MaxWalkSpeed=170;if(Door)WalkTo(Door->GetActorTransform().TransformPosition(FVector(-57.5,210,90)));else{Check(TEXT("home_door_exists"),false);Phase=8;}break;
 case 5:{
  const FVector Focus=Door?Door->GetActorTransform().TransformPosition(Door->FocusOffset):FVector::ZeroVector;PC->SetControlRotation((Focus-Eyes->GetComponentLocation()).Rotation());Next=FPlatformTime::Seconds()+.5;break;}
 case 6:{auto Focus=AMareServiceTarget::FindFocused(PC);Check(TEXT("arrival_home_door_focus"),Focus==Door && Door);if(Focus==Door && Door && !Door->IsOpen())Door->Use(PC);Next=FPlatformTime::Seconds()+1;break;}
 case 7:if(Door)WalkTo(Door->GetActorTransform().TransformPosition(FVector(-57.5,-180,90)));break;
 case 8:WalkTo(FVector(4610,2280,100));break;
 case 9:PC->SetControlRotation((FVector(4435,2237,58)-Eyes->GetComponentLocation()).Rotation());Capture(TEXT("intro-letter-table"));Next=FPlatformTime::Seconds()+.5;break;
 case 10:{
  auto Target=AMareServiceTarget::FindFocused(PC);Check(TEXT("letter_can_be_aimed"),Target && Target->Action==TEXT("IntroLetter"));if(Target && Target->Action==TEXT("IntroLetter"))Target->Use(PC);Check(TEXT("letter_opens"),Intro && Intro->IsLetterOpen() && PC->IsMoveInputIgnored());Capture(TEXT("intro-letter"));Next=FPlatformTime::Seconds()+2;break;}
 case 11:
  if(Intro)Intro->CloseLetter();Check(TEXT("letter_closes_and_saves"),Intro && !Intro->IsLetterOpen() && !PC->IsMoveInputIgnored() && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),0)==2 && Sim->Save());
  if(Intro)Intro->ReadLetter();Check(TEXT("letter_can_be_read_again"),Intro && Intro->IsLetterOpen());if(Intro)Intro->CloseLetter();
  {auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("checks"),Checks);Report->SetBoolField(TEXT("finished"),true);FString Out;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Out));FFileHelper::SaveStringToFile(Out,*(Root/TEXT("intro-qa.json")));}
  UKismetSystemLibrary::QuitGame(this,PC,EQuitPreference::Quit,false);break;
 default:break;
 }
}
