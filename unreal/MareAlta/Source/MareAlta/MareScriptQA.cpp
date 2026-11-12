#include "MareScriptQA.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/OutputDeviceNull.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"

AMareScriptQA::AMareScriptQA(){PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.bTickEvenWhenPaused=true;}

void AMareScriptQA::Write(bool bFinished)
{
 auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("steps"),Records);Report->SetBoolField(TEXT("finished"),bFinished);
 FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*(Root/TEXT("script-qa.json")));
}

void AMareScriptQA::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));auto Hero=PC?Cast<AMareCharacter>(PC->GetPawn()):nullptr;if(!Hero || !PC->GetSimulation())return;
 if(Line<0){
  FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Root);Root.ReplaceInline(TEXT("\\"),TEXT("/"));
  FString File;FParse::Value(FCommandLine::Get(),TEXT("MareScriptQA="),File);File.ReplaceInline(TEXT("\\"),TEXT("/"));
  if(!Root.StartsWith(TEXT("D:/CodexTemp/")) || !File.StartsWith(TEXT("D:/CodexTemp/")) || !FFileHelper::LoadFileToStringArray(Lines,*File)){Destroy();return;}
  Line=0;Next=FPlatformTime::Seconds()+12;return;
 }
 // Several steps a frame until one asks to wait (a screenshot is taken at the end of the frame: one frame per shot).
 while(FPlatformTime::Seconds()>=Next){
  if(Line>=Lines.Num()){Write(true);FPlatformMisc::RequestExit(false);Next=FPlatformTime::Seconds()+60;return;}
  const FString Step=Lines[Line++].TrimStartAndEnd();if(Step.IsEmpty() || Step.StartsWith(TEXT("#")))continue;
  FString Verb,Arg;if(!Step.Split(TEXT(" "),&Verb,&Arg))Verb=Step;Arg.TrimStartAndEndInline();
  auto Sim=PC->GetSimulation();auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("step"),Step);
  Row->SetNumberField(TEXT("clock"),UMareSimulation::Number(Sim->State,TEXT("minutes")));
  if(Verb==TEXT("wait"))Next=FPlatformTime::Seconds()+FCString::Atod(*Arg);   // i18n:skip
  else if(Verb==TEXT("clock")){   // i18n:skip
   const double Now=FMath::Fmod(UMareSimulation::Number(Sim->State,TEXT("minutes")),1440.0);double Ahead=FCString::Atod(*Arg)-Now;if(Ahead<0)Ahead+=1440;Sim->AdvanceMinutes(Ahead);}
  else if(Verb==TEXT("pose")){TArray<FString> V;Arg.ParseIntoArray(V,TEXT(","));   // i18n:skip
   if(V.Num()>=5){Hero->GetCharacterMovement()->SetMovementMode(MOVE_Flying);Hero->GetCharacterMovement()->StopMovementImmediately();
    Hero->SetActorLocation(FVector(FCString::Atod(*V[0]),FCString::Atod(*V[1]),FCString::Atod(*V[2])));PC->SetControlRotation(FRotator(FCString::Atod(*V[3]),FCString::Atod(*V[4]),0));}}
  else if(Verb==TEXT("speed"))UGameplayStatics::SetGlobalTimeDilation(this,FMath::Clamp(FCString::Atof(*Arg),.05f,20.f));   // i18n:skip
  else if(Verb==TEXT("hire"))Row->SetBoolField(TEXT("ok"),Sim->HireAttendant());   // i18n:skip
  else if(Verb==TEXT("pastel"))Row->SetStringField(TEXT("result"),PC->PastelQA(Arg));   // i18n:skip
  else if(Verb==TEXT("shot")){FScreenshotRequest::RequestScreenshot(Root/(Arg+TEXT(".png")),true,false);Next=FPlatformTime::Seconds()+.35;}   // i18n:skip
  else if(Verb==TEXT("people")){TArray<TSharedPtr<FJsonValue>> List;const FVector At=Hero->GetActorLocation();   // i18n:skip
   for(TActorIterator<AMarePerson> It(GetWorld());It;++It){const FVector P=It->GetActorLocation();if(FVector::Dist2D(P,At)>2500)continue;
    auto One=MakeShared<FJsonObject>();One->SetStringField(TEXT("name"),It->PersonName);One->SetNumberField(TEXT("stage"),int32(It->Stage));One->SetBoolField(TEXT("employee"),It->bEmployee);
    One->SetBoolField(TEXT("seated"),It->bSeated);One->SetBoolField(TEXT("hidden"),It->IsHidden());One->SetStringField(TEXT("at"),P.ToCompactString());One->SetNumberField(TEXT("yaw"),It->GetActorRotation().Yaw);
    List.Add(MakeShared<FJsonValueObject>(One));}
   Row->SetArrayField(TEXT("people"),List);}
  else{FOutputDeviceNull Null;Row->SetBoolField(TEXT("ok"),IConsoleManager::Get().ProcessUserConsoleInput(*Step,Null,GetWorld()));}
  Row->SetStringField(TEXT("message"),Sim->LastMessage);Row->SetNumberField(TEXT("money"),UMareSimulation::Number(Sim->State,TEXT("money")));
  Records.Add(MakeShared<FJsonValueObject>(Row));Write(false);
 }
}
