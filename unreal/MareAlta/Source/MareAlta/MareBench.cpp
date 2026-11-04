#include "MareBench.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#include "RHI.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Components/SkeletalMeshComponent.h"
#include "RenderCore.h"

namespace
{
 struct FBenchSector{const TCHAR* Name;int32 Minutes;FVector At;FRotator Look;};
 // Pawn positions (flying) and clock of each sector, in rising order (the day ends at 24:00 until the player sleeps,
 // so the clock only moves forward); the same views the QA gate photographs.
 const FBenchSector Sectors[]={
  {TEXT("praia"),780,FVector(3000,-3600,260),FRotator(-8,90,0)},
  {TEXT("quiosque"),860,FVector(3750,-2600,200),FRotator(-6,90,0)},
  {TEXT("saguao_hotel"),940,FVector(-2100,5800,170),FRotator(-2,90,0)},
  {TEXT("vila_noite"),1260,FVector(4300,2900,100),FRotator(-4,180,0)},
 };
}

AMareBench::AMareBench(){PrimaryActorTick.bCanEverTick=true;}

// Cost split: -MareBenchNoPeople hides every person (and stops their animation), -MareBenchNoGroom only the hair
// strands; the same sectors measured with and without show what the people cost.
void AMareBench::Strip()
{
 const bool bNoPeople=FParse::Param(FCommandLine::Get(),TEXT("MareBenchNoPeople")),bNoGroom=FParse::Param(FCommandLine::Get(),TEXT("MareBenchNoGroom"));
 if(!bNoPeople && !bNoGroom)return;
 for(TActorIterator<AMarePerson> It(GetWorld());It;++It){
  if(bNoPeople){if(!It->IsHidden()){It->SetActorHiddenInGame(true);TArray<USkeletalMeshComponent*> Parts;It->GetComponents(Parts);for(auto Part:Parts)Part->SetComponentTickEnabled(false);}continue;}
  TArray<UPrimitiveComponent*> Parts;It->GetComponents(Parts);
  for(auto Part:Parts)if(Part->GetClass()->GetName().Contains(TEXT("Groom")) && Part->IsVisible())Part->SetVisibility(false);}
}

void AMareBench::Enter(AMareController* PC)
{
 const FBenchSector& S=Sectors[Sector];auto Sim=PC->GetSimulation();auto Hero=Cast<AMareCharacter>(PC->GetPawn());
 const double Now=UMareSimulation::Number(Sim->State,TEXT("minutes"));
 if(S.Minutes>Now)Sim->AdvanceMinutes(S.Minutes-Now);
 Hero->SetActorLocation(S.At);PC->SetControlRotation(S.Look);
 Frames.Reset();Game.Reset();Render.Reset();Gpu.Reset();Stage=0;Next=FPlatformTime::Seconds()+8;
}

void AMareBench::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));auto Hero=PC?Cast<AMareCharacter>(PC->GetPawn()):nullptr;if(!Hero || !PC->GetSimulation())return;
 if(Sector<0){
  FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Root);Root.ReplaceInline(TEXT("\\"),TEXT("/"));
  if(!Root.StartsWith(TEXT("D:/CodexTemp/"))){Destroy();return;}
  for(const TCHAR* C:{TEXT("t.MaxFPS 0"),TEXT("r.VSync 0")})GEngine->Exec(GetWorld(),C);
  // Experiments without a new package: -MareBenchExec="cvar value;cvar value" runs those console commands first.
  FString Extra;if(FParse::Value(FCommandLine::Get(),TEXT("MareBenchExec="),Extra,false)){TArray<FString> Commands;Extra.TrimQuotes().ParseIntoArray(Commands,TEXT(";"));
   for(const FString& C:Commands)GEngine->Exec(GetWorld(),*C.TrimStartAndEnd());}
  // Everything a late game has: all expansions and the Grand Hotel (fame and the carnaval chapter played through state).
  auto Sim=PC->GetSimulation();Sim->State->SetNumberField(TEXT("money"),500000);
  UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("ch"))->SetNumberField(TEXT("carnaval"),3);Sim->AddFame(100000);
  for(const TCHAR* Id:{TEXT("kiosk_tables"),TEXT("drinks"),TEXT("grill"),TEXT("bar"),TEXT("pousada"),TEXT("pool"),TEXT("passeios"),TEXT("grand_hotel")}){
   bool bOwned=false;UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);if(!bOwned)Sim->BuyExpansion(Id);}
  Hero->GetCharacterMovement()->SetMovementMode(MOVE_Flying);Sector=0;Enter(PC);return;
 }
 if(Stage==0){if(FPlatformTime::Seconds()<Next)return;Stage=1;Next=FPlatformTime::Seconds()+20;
  // Per-scope timings of the same 20 s (CSV profiler: animation, skinning, shadows...), csv/<sector>.csv.
  FCsvProfiler::Get()->BeginCapture(-1,Root/TEXT("csv"),FString(Sectors[Sector].Name)+TEXT(".csv"));return;}
 if(Stage==0 || Stage==1)Strip();
 if(Stage==1){
  Frames.Add(FApp::GetDeltaTime()*1000.f);Game.Add(FPlatformTime::ToMilliseconds(GGameThreadTime));Render.Add(FPlatformTime::ToMilliseconds(GRenderThreadTime));
  Gpu.Add(FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0)));
  if(FPlatformTime::Seconds()<Next)return;
  FCsvProfiler::Get()->EndCapture();
  FScreenshotRequest::RequestScreenshot(Root/(FString(TEXT("bench-"))+Sectors[Sector].Name+TEXT(".png")),true,false);
  TArray<float> Sorted=Frames;Sorted.Sort();double Sum=0;for(float F:Frames)Sum+=F;
  auto Pct=[&Sorted](double P){return Sorted.Num()?Sorted[FMath::Clamp(int32(P*(Sorted.Num()-1)),0,Sorted.Num()-1)]:0.f;};
  // A MetaHuman's animated rig is hidden; the visible parts are other components: count a person when any of them drew.
  int32 People=0,Seen=0;for(TActorIterator<AMarePerson> It(GetWorld());It;++It){++People;TArray<UPrimitiveComponent*> Parts;It->GetComponents(Parts);
   for(auto Part:Parts)if(Part->IsVisible() && Part->WasRecentlyRendered(.5f)){++Seen;break;}}
  auto Avg=[](const TArray<float>& A){double S=0;for(float V:A)S+=V;return A.Num()?S/A.Num():0.0;};
  FVector2D Size;GEngine->GameViewport->GetViewportSize(Size);
  auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("sector"),Sectors[Sector].Name);Row->SetNumberField(TEXT("frames"),Frames.Num());
  Row->SetNumberField(TEXT("avg_ms"),Frames.Num()?Sum/Frames.Num():0);Row->SetNumberField(TEXT("avg_fps"),Sum>0?1000.0*Frames.Num()/Sum:0);
  Row->SetNumberField(TEXT("p50_ms"),Pct(.5));Row->SetNumberField(TEXT("p95_ms"),Pct(.95));Row->SetNumberField(TEXT("p99_ms"),Pct(.99));Row->SetNumberField(TEXT("worst_ms"),Sorted.Num()?Sorted.Last():0);
  Row->SetNumberField(TEXT("game_ms"),Avg(Game));Row->SetNumberField(TEXT("render_ms"),Avg(Render));Row->SetNumberField(TEXT("gpu_ms"),Avg(Gpu));
  Row->SetNumberField(TEXT("clock"),UMareSimulation::Number(PC->GetSimulation()->State,TEXT("minutes")));
  {FString Extra;FParse::Value(FCommandLine::Get(),TEXT("MareBenchExec="),Extra,false);Row->SetStringField(TEXT("exec"),Extra);}
  Row->SetStringField(TEXT("variant"),FParse::Param(FCommandLine::Get(),TEXT("MareBenchNoPeople"))?TEXT("sem_pessoas"):FParse::Param(FCommandLine::Get(),TEXT("MareBenchNoGroom"))?TEXT("sem_cabelo"):TEXT("completo"));
  Row->SetNumberField(TEXT("people"),People);Row->SetNumberField(TEXT("people_rendered"),Seen);Row->SetNumberField(TEXT("viewport_x"),Size.X);Row->SetNumberField(TEXT("viewport_y"),Size.Y);
  Records.Add(MakeShared<FJsonValueObject>(Row));Stage=2;Next=FPlatformTime::Seconds()+2;return;
 }
 if(FPlatformTime::Seconds()<Next)return;
 if(++Sector<int32(UE_ARRAY_COUNT(Sectors))){Enter(PC);return;}
 auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("sectors"),Records);Report->SetBoolField(TEXT("finished"),true);
 FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*(Root/TEXT("bench.json")));
 GEngine->Exec(GetWorld(),TEXT("QUIT"));
}
