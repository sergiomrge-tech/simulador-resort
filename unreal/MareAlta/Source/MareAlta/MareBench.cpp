#include "MareBench.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareOptions.h"
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
#include "HAL/IConsoleManager.h"
#include "GameFramework/GameModeBase.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "UObject/UObjectIterator.h"
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
 Frames.Reset();Game.Reset();Render.Reset();Gpu.Reset();Presented.Reset();Stage=0;Next=FPlatformTime::Seconds()+8;
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
   // A console variable is set with code priority, like the game's own options: a console-priority Exec is silently
   // refused once FMareOptions set the variable (04/11: r.Streamline.DLSSG.Enable 1 never reached frame generation).
   for(const FString& C:Commands){FString Name,Value;const FString Line=C.TrimStartAndEnd();
    if(Line.Split(TEXT(" "),&Name,&Value))if(auto Var=IConsoleManager::Get().FindConsoleVariable(*Name)){Var->Set(*Value.TrimStartAndEnd(),ECVF_SetByCode);continue;}
    GEngine->Exec(GetWorld(),*Line);}}
  // Everything a late game has: all expansions and the Grand Hotel (fame and the carnaval chapter played through state).
  auto Sim=PC->GetSimulation();Sim->State->SetNumberField(TEXT("money"),500000);Sim->Definitions->SetBoolField(TEXT("demo"),false);   // the bench measures the full game
  UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("ch"))->SetNumberField(TEXT("carnaval"),3);Sim->AddFame(100000);
  for(const TCHAR* Id:{TEXT("kiosk_tables"),TEXT("drinks"),TEXT("grill"),TEXT("bar"),TEXT("pousada"),TEXT("pool"),TEXT("passeios"),TEXT("grand_hotel")}){
   bool bOwned=false;UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);if(!bOwned)Sim->BuyExpansion(Id);}
  // -MareBenchNoShadow=<mesh name part>: those meshes stop casting shadows (cost split between their shadows and their pixels).
  FString NoShadow;if(FParse::Value(FCommandLine::Get(),TEXT("MareBenchNoShadow="),NoShadow))
   for(TObjectIterator<UStaticMeshComponent> It;It;++It)if(It->GetWorld()==GetWorld() && It->GetStaticMesh() && It->GetStaticMesh()->GetName().Contains(NoShadow))It->SetCastShadow(false);
  Hero->GetCharacterMovement()->SetMovementMode(MOVE_Flying);Started=FPlatformTime::Seconds();Sector=0;Enter(PC);return;
 }
 if(FParse::Param(FCommandLine::Get(),TEXT("MareBenchSweep"))){Sweep();return;}
 if(Stage==0){if(FPlatformTime::Seconds()<Next)return;Stage=1;Next=FPlatformTime::Seconds()+20;
  // Per-scope timings of the same 20 s (CSV profiler: animation, skinning, shadows...), csv/<sector>.csv.
  FCsvProfiler::Get()->BeginCapture(-1,Root/TEXT("csv"),FString(Sectors[Sector].Name)+TEXT(".csv"));return;}
 if(Stage==0 || Stage==1)Strip();
 if(Stage==1){
  Frames.Add(FApp::GetDeltaTime()*1000.f);Game.Add(FPlatformTime::ToMilliseconds(GGameThreadTime));Render.Add(FPlatformTime::ToMilliseconds(GRenderThreadTime));
  Gpu.Add(FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0)));
  // With DLSS frame generation the engine's frame time counts only rendered frames; Streamline reports what reached the screen.
  Presented.Add(FMareOptions::PresentedFrameRate());
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
  Row->SetNumberField(TEXT("game_ms"),Avg(Game));Row->SetNumberField(TEXT("render_ms"),Avg(Render));Row->SetNumberField(TEXT("gpu_ms"),Avg(Gpu));Row->SetNumberField(TEXT("presented_fps"),Avg(Presented));
  if(auto FG=IConsoleManager::Get().FindConsoleVariable(TEXT("r.Streamline.DLSSG.Enable")))Row->SetNumberField(TEXT("frame_generation_cvar"),FG->GetInt());
  Row->SetBoolField(TEXT("frame_generation_supported"),FMareOptions::FrameGenerationSupported());Row->SetBoolField(TEXT("focus"),FApp::HasFocus());
  Row->SetNumberField(TEXT("clock"),UMareSimulation::Number(PC->GetSimulation()->State,TEXT("minutes")));
  {FString Extra;FParse::Value(FCommandLine::Get(),TEXT("MareBenchExec="),Extra,false);Row->SetStringField(TEXT("exec"),Extra);
   FString NoShadow;FParse::Value(FCommandLine::Get(),TEXT("MareBenchNoShadow="),NoShadow);Row->SetStringField(TEXT("no_shadow"),NoShadow);}
  Row->SetStringField(TEXT("variant"),FParse::Param(FCommandLine::Get(),TEXT("MareBenchNoPeople"))?TEXT("sem_pessoas"):FParse::Param(FCommandLine::Get(),TEXT("MareBenchNoGroom"))?TEXT("sem_cabelo"):TEXT("completo"));
  Row->SetNumberField(TEXT("people"),People);Row->SetNumberField(TEXT("people_rendered"),Seen);Row->SetNumberField(TEXT("viewport_x"),Size.X);Row->SetNumberField(TEXT("viewport_y"),Size.Y);
  Row->SetNumberField(TEXT("ram_mb"),double(FPlatformMemory::GetStats().UsedPhysical)/(1024.0*1024.0));
  Row->SetNumberField(TEXT("elapsed_s"),FPlatformTime::Seconds()-Started);Row->SetNumberField(TEXT("cycle"),Cycle);
  Records.Add(MakeShared<FJsonValueObject>(Row));Stage=2;Next=FPlatformTime::Seconds()+2;
  Write(false);return;
 }
 if(FPlatformTime::Seconds()<Next)return;
 if(++Sector<int32(UE_ARRAY_COUNT(Sectors))){Enter(PC);return;}
 // Soak (PENDENCIAS P0 "sessões de 2 h"): -MareBenchSoak=<seconds> sleeps to the next morning and runs the sectors
 // again until that long has passed; bench.json is rewritten after every sector, so a crash still leaves the record.
 double Soak=0;FParse::Value(FCommandLine::Get(),TEXT("MareBenchSoak="),Soak);
 if(FPlatformTime::Seconds()-Started<Soak){PC->GetSimulation()->Sleep();++Cycle;Sector=0;Enter(PC);return;}
 Write(true);GEngine->Exec(GetWorld(),TEXT("QUIT"));
}

void AMareBench::Write(bool bFinished)
{
 auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("sectors"),Records);Report->SetBoolField(TEXT("finished"),bFinished);
 Report->SetNumberField(TEXT("cycles"),Cycle+1);Report->SetNumberField(TEXT("elapsed_s"),FPlatformTime::Seconds()-Started);
 FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*(Root/TEXT("bench.json")));
}

// -MareBenchSweep (60 FPS work): at the beach sector, the static/instanced meshes grouped by mesh; the 20 biggest groups
// (instances x sections) are hidden one at a time, 2 s to settle and 4 s measured, then shown again. sweep.json lists
// render/GPU/game ms per hidden group next to the baseline, so the costly meshes show up in one run.
void AMareBench::Sweep()
{
 const double Now=FPlatformTime::Seconds();
 if(SweepIndex==-2){
  if(Now<Next)return;   // the sector's 8 s warm-up
  GetWorld()->GetAuthGameMode()->SetActorTickEnabled(false);   // clock frozen: the same sun for every measurement
  TMap<FString,int32> Index;
  for(TObjectIterator<UStaticMeshComponent> It;It;++It){UStaticMeshComponent* C=*It;
   if(C->GetWorld()!=GetWorld() || !C->IsVisible() || !C->GetStaticMesh() || C->GetOwner()==nullptr || C->GetOwner()->IsHidden())continue;
   if(Cast<USkeletalMeshComponent>(C))continue;
   const FString Mesh=C->GetStaticMesh()->GetName();int32* At=Index.Find(Mesh);
   if(!At){At=&Index.Add(Mesh,Groups.Num());Groups.AddDefaulted();Groups.Last().Mesh=Mesh;Groups.Last().Sections=C->GetStaticMesh()->GetNumSections(0);}
   FSweepGroup& G=Groups[*At];G.Parts.Add(C);auto ISM=Cast<UInstancedStaticMeshComponent>(C);G.Instances+=ISM?ISM->GetInstanceCount():1;}
  Groups.Sort([](const FSweepGroup& A,const FSweepGroup& B){return A.Instances*FMath::Max(1,A.Sections)>B.Instances*FMath::Max(1,B.Sections);});
  if(Groups.Num()>20)Groups.SetNum(20);
  SweepIndex=-1;SweepStage=0;Next=Now+2;Frames.Reset();Render.Reset();Gpu.Reset();Game.Reset();return;}
 if(SweepStage==0){if(Now<Next)return;SweepStage=1;Next=Now+4;Frames.Reset();Render.Reset();Gpu.Reset();Game.Reset();return;}
 if(SweepStage==1){
  Frames.Add(FApp::GetDeltaTime()*1000.f);Game.Add(FPlatformTime::ToMilliseconds(GGameThreadTime));Render.Add(FPlatformTime::ToMilliseconds(GRenderThreadTime));
  Gpu.Add(FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0)));if(Now<Next)return;
  auto Avg=[](const TArray<float>& A){double S=0;for(float V:A)S+=V;return A.Num()?S/A.Num():0.0;};
  auto Row=MakeShared<FJsonObject>();
  if(SweepIndex<0)Row->SetStringField(TEXT("hidden"),TEXT("(nada)"));
  else{const FSweepGroup& G=Groups[SweepIndex];Row->SetStringField(TEXT("hidden"),G.Mesh);Row->SetNumberField(TEXT("instances"),G.Instances);
   Row->SetNumberField(TEXT("sections"),G.Sections);Row->SetNumberField(TEXT("components"),G.Parts.Num());
   for(auto& P:G.Parts)if(P.IsValid())P->SetVisibility(true);}
  Row->SetNumberField(TEXT("frame_ms"),Avg(Frames));Row->SetNumberField(TEXT("render_ms"),Avg(Render));Row->SetNumberField(TEXT("gpu_ms"),Avg(Gpu));Row->SetNumberField(TEXT("presented_fps"),Avg(Presented));Row->SetNumberField(TEXT("game_ms"),Avg(Game));
  Records.Add(MakeShared<FJsonValueObject>(Row));
  if(++SweepIndex>=Groups.Num()){auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("sweep"),Records);Report->SetBoolField(TEXT("finished"),true);
   FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*(Root/TEXT("sweep.json")));
   GEngine->Exec(GetWorld(),TEXT("QUIT"));SweepStage=2;return;}
  for(auto& P:Groups[SweepIndex].Parts)if(P.IsValid())P->SetVisibility(false);
  SweepStage=0;Next=Now+2;return;}
}
