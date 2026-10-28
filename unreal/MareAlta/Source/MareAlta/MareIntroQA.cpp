#include "MareIntroQA.h"
#include "MareIntro.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
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
void AMareIntroQA::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 if(Root.IsEmpty()){FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Root);Root.ReplaceInline(TEXT("\\"),TEXT("/"));if(!Root.StartsWith(TEXT("D:/CodexTemp/"))){Destroy();return;}Next=FPlatformTime::Seconds()+3;}
 if(FPlatformTime::Seconds()<Next)return;
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));if(!PC || !PC->GetPawn())return;
 auto Sim=PC->GetSimulation();AMareIntro* Intro=nullptr;for(TActorIterator<AMareIntro> It(GetWorld());It;++It){Intro=*It;break;}
 switch(Phase++){
 case 0:
  Check(TEXT("new_save_arrival_active"),Intro && Intro->IsArrival() && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)==0);
  FScreenshotRequest::RequestScreenshot(Root/TEXT("intro-bus.png"),true,false);Next=FPlatformTime::Seconds()+(FParse::Param(FCommandLine::Get(),TEXT("MareIntroNaturalQA"))?10:3);break;
 case 1:
  if(Intro && !FParse::Param(FCommandLine::Get(),TEXT("MareIntroNaturalQA")))Intro->FinishArrival();Check(FParse::Param(FCommandLine::Get(),TEXT("MareIntroNaturalQA"))?TEXT("arrival_finishes_naturally"):TEXT("arrival_can_be_skipped"),Intro && !Intro->IsArrival() && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),2)==1 && !PC->IsMoveInputIgnored());
  FScreenshotRequest::RequestScreenshot(Root/TEXT("intro-after-arrival.png"),true,false);
  Next=FPlatformTime::Seconds()+2;break;
 case 2:{
  PC->GetPawn()->SetActorLocation(FVector(4480,2320,100));PC->SetControlRotation((FVector(4435,2237,58)-FVector(4480,2320,164)).Rotation());
  Next=FPlatformTime::Seconds()+2;break;}
 case 3:{
  auto Target=AMareServiceTarget::FindFocused(PC);Check(TEXT("letter_can_be_aimed"),Target && Target->Action==TEXT("IntroLetter"));if(Target && Target->Action==TEXT("IntroLetter"))Target->Use(PC);Check(TEXT("letter_opens"),Intro && Intro->IsLetterOpen() && PC->IsMoveInputIgnored());
  FScreenshotRequest::RequestScreenshot(Root/TEXT("intro-letter.png"),true,false);Next=FPlatformTime::Seconds()+3;break;}
 case 4:
  if(Intro)Intro->CloseLetter();Check(TEXT("letter_closes_and_saves"),Intro && !Intro->IsLetterOpen() && !PC->IsMoveInputIgnored() && UMareSimulation::Number(Sim->State,TEXT("ue_intro_stage"),0)==2 && Sim->Save());
  if(Intro)Intro->ReadLetter();Check(TEXT("letter_can_be_read_again"),Intro && Intro->IsLetterOpen());if(Intro)Intro->CloseLetter();
  {auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("checks"),Checks);Report->SetBoolField(TEXT("finished"),true);FString Out;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Out));FFileHelper::SaveStringToFile(Out,*(Root/TEXT("intro-qa.json")));}
  UKismetSystemLibrary::QuitGame(this,PC,EQuitPreference::Quit,false);break;
 default:break;
 }
}
