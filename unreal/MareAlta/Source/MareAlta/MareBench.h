#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MareBench.generated.h"

// Frame-time benchmark of the packaged game per sector (PENDENCIAS P0 "FPS medido no executável").
// MareAlta.exe -MareBench -MareSaveRoot=D:/CodexTemp/<new folder> : everything unlocked, then for each sector
// (beach with bathers at 13h, kiosk, hotel lobby, village at 21h) 8 s warm-up and 20 s of frame times;
// writes bench.json (avg/median/p95/p99/worst ms, average fps, people rendered) plus one screenshot per sector and quits.
struct FSweepGroup{FString Mesh;int32 Instances=0;int32 Sections=0;TArray<TWeakObjectPtr<class UStaticMeshComponent>> Parts;};

UCLASS()
class AMareBench : public AActor
{
 GENERATED_BODY()
public:
 AMareBench();
 virtual void Tick(float DeltaSeconds) override;
private:
 FString Root;
 int32 Sector=-1;
 int32 Stage=0;
 double Next=0;
 TArray<float> Frames,Game,Render,Gpu,Presented;
 TArray<TSharedPtr<class FJsonValue>> Records;
 void Enter(class AMareController* PC);
 void Strip();
 void Sweep();
 TArray<FSweepGroup> Groups;
 int32 SweepIndex=-2;
 int32 SweepStage=0;
 void Write(bool bFinished);
 double Started=0;
 int32 Cycle=0;
};
