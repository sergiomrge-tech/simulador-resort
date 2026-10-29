#include "MareGraphicsQA.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/GameViewportClient.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Serialization/JsonSerializer.h"

AMareGraphicsQA::AMareGraphicsQA(){PrimaryActorTick.bCanEverTick=true;}
void AMareGraphicsQA::Configure()
{
 const TCHAR* Commands[]={TEXT("r.Nanite 1"),TEXT("r.DynamicGlobalIlluminationMethod 1"),TEXT("r.ReflectionMethod 1")};
 for(const TCHAR* Command:Commands)GEngine->Exec(GetWorld(),Command);
 if(Variant==2)GEngine->Exec(GetWorld(),TEXT("r.Nanite 0"));
 if(Variant==3){GEngine->Exec(GetWorld(),TEXT("r.DynamicGlobalIlluminationMethod 0"));GEngine->Exec(GetWorld(),TEXT("r.ReflectionMethod 2"));}
 for(TActorIterator<AActor> It(GetWorld());It;++It){if(It->ActorHasTag(TEXT("MareGraphicsPCG")) || It->ActorHasTag(TEXT("MareGrassPCG")))It->SetActorHiddenInGame(Variant==1);
  if(bHotelScene){TArray<UInstancedStaticMeshComponent*> Cs;It->GetComponents(Cs);for(auto C:Cs){if(C->GetStaticMesh() && C->GetStaticMesh()->GetName()==TEXT("World_2365")){C->SetVisibility(Variant==4);C->SetCastShadow(Variant==4);}
   for(auto Tag:C->ComponentTags)if(Tag.ToString().StartsWith(TEXT("HotelTower_")))C->SetVisibility(Variant!=4);}}
 }
}
void AMareGraphicsQA::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));auto Hero=PC?Cast<AMareCharacter>(PC->GetPawn()):nullptr;if(!Hero)return;
 if(Root.IsEmpty()){
  FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Root);Root.ReplaceInline(TEXT("\\"),TEXT("/"));
  if(!Root.StartsWith(TEXT("D:/CodexTemp/"))){Destroy();return;}
  auto Sim=PC->GetSimulation();Sim->AdvanceMinutes(720-UMareSimulation::Number(Sim->State,TEXT("minutes")));GetWorld()->GetAuthGameMode()->SetActorTickEnabled(false);
  bHotelScene=FParse::Param(FCommandLine::Get(),TEXT("MareProfileHotel"));VariantCount=bHotelScene?5:4;
  Hero->GetCharacterMovement()->SetMovementMode(MOVE_Flying);Hero->SetActorLocation(bHotelScene?FVector(-2100,3500,450):FVector(2800,-750,100));PC->SetControlRotation(bHotelScene?FRotator(10,90,0):FRotator(-4,145,0));
  RenderPercentage=FParse::Param(FCommandLine::Get(),TEXT("MareNativeResolution"))?100:80;GEngine->Exec(GetWorld(),*FString::Printf(TEXT("r.ScreenPercentage %d"),RenderPercentage));
  for(const TCHAR* C:{TEXT("t.MaxFPS 0"),TEXT("r.VSync 0"),TEXT("sg.GlobalIlluminationQuality 2"),TEXT("sg.ReflectionQuality 2"),TEXT("sg.ShadowQuality 2"),TEXT("sg.ViewDistanceQuality 2")})GEngine->Exec(GetWorld(),C);
  Configure();Next=FPlatformTime::Seconds()+15;Stage=0;
 }
 if(FPlatformTime::Seconds()<Next)return;
 static const TCHAR* Names[]={TEXT("all-enabled"),TEXT("without-pcg"),TEXT("nanite-off"),TEXT("lumen-off"),TEXT("hotel-legacy")};
 if(Stage==0){FCsvProfiler::Get()->BeginCapture(-1,Root,Names[Variant]);Stage=1;Next=FPlatformTime::Seconds()+12;return;}
 if(Stage==1){Capture=FCsvProfiler::Get()->EndCapture();FScreenshotRequest::RequestScreenshot(Root/(FString(Names[Variant])+TEXT(".png")),true,false);Stage=2;Next=FPlatformTime::Seconds()+3;return;}
 if(!Capture.IsReady()){Next=FPlatformTime::Seconds()+1;return;}
 auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("variant"),Names[Variant]);Row->SetStringField(TEXT("csv"),Capture.Get());FVector2D Size;GEngine->GameViewport->GetViewportSize(Size);
 Row->SetNumberField(TEXT("viewport_x"),Size.X);Row->SetNumberField(TEXT("viewport_y"),Size.Y);Row->SetNumberField(TEXT("screen_percentage"),RenderPercentage);
 int32 Instances=0;for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareGraphicsPCG"))){TArray<UInstancedStaticMeshComponent*> Cs;It->GetComponents(Cs);for(auto C:Cs)Instances+=C->GetInstanceCount();}
 Row->SetNumberField(TEXT("pcg_instances"),Instances);
 int32 GrassInstances=0;for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareGrassPCG"))){TArray<UInstancedStaticMeshComponent*> Cs;It->GetComponents(Cs);for(auto C:Cs)GrassInstances+=C->GetInstanceCount();}
 Row->SetNumberField(TEXT("grass_instances"),GrassInstances);Records.Add(MakeShared<FJsonValueObject>(Row));
 if(++Variant<VariantCount){Configure();Stage=0;Next=FPlatformTime::Seconds()+10;return;}
 Variant=0;Configure();auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("captures"),Records);Report->SetBoolField(TEXT("finished"),true);FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*(Root/TEXT("graphics-qa.json")));GEngine->Exec(GetWorld(),TEXT("QUIT"));
}
