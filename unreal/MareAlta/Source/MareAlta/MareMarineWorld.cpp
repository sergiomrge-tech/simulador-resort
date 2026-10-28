#include "MareMarineWorld.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareAudioWorld.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/GameInstance.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TStatId UMareMarineWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareMarineWorld,STATGROUP_Tickables);}
bool UMareMarineWorld::HasMarineModels() const{return IsValid(Sail) && IsValid(Cruise) && IsValid(Whale) && IsValid(Ripple) && IsValid(Spray);}
bool UMareMarineWorld::IsSailVisible() const{return IsValid(Sail) && !Sail->IsHidden();}
bool UMareMarineWorld::IsCruiseVisible() const{return IsValid(Cruise) && !Cruise->IsHidden();}
bool UMareMarineWorld::IsWhaleVisible() const{return IsValid(Whale) && !Whale->IsHidden();}
bool UMareMarineWorld::IsRippleVisible() const{return IsValid(Ripple) && !Ripple->IsHidden();}
void UMareMarineWorld::SpawnModels()
{
 bInitialized=true;FString Text;TSharedPtr<FJsonObject> Catalog;
 if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/marine_assets.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Catalog))return;
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto Make=[&](const FString& Id){auto Data=UMareSimulation::Object(Catalog,Id);auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(Data,TEXT("path")));if(!Mesh)return (AStaticMeshActor*)nullptr;
  auto Actor=GetWorld()->SpawnActor<AStaticMeshActor>(FVector::ZeroVector,FRotator::ZeroRotator,Params);if(!Actor)return (AStaticMeshActor*)nullptr;
  auto Component=Actor->GetStaticMeshComponent();Component->SetMobility(EComponentMobility::Movable);Component->SetStaticMesh(Mesh);Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);Actor->SetActorHiddenInGame(true);return Actor;};
 Sail=Make(TEXT("pirate_sailship"));Cruise=Make(TEXT("coastal_cruise"));Whale=Make(TEXT("humpback_whale"));
 Ripple=GetWorld()->SpawnActor<AStaticMeshActor>(FVector(-600,-13900,-12),FRotator::ZeroRotator,Params);
 if(Ripple){auto C=Ripple->GetStaticMeshComponent();C->SetMobility(EComponentMobility::Movable);C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));C->SetCollisionEnabled(ECollisionEnabled::NoCollision);C->SetCastShadow(false);
  if(auto Mat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_WhaleRipple.M_WhaleRipple"))){RippleMaterial=UMaterialInstanceDynamic::Create(Mat,this);C->SetMaterial(0,RippleMaterial);}
  Ripple->SetActorScale3D(FVector(28,28,1));Ripple->SetActorHiddenInGame(true);}
 SprayActor=GetWorld()->SpawnActor<AActor>(FVector(-600,-13900,-20),FRotator::ZeroRotator,Params);
 if(SprayActor){Spray=NewObject<UInstancedStaticMeshComponent>(SprayActor);SprayActor->SetRootComponent(Spray);SprayActor->AddInstanceComponent(Spray);Spray->SetMobility(EComponentMobility::Movable);
  Spray->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));Spray->SetCollisionEnabled(ECollisionEnabled::NoCollision);Spray->SetCastShadow(false);Spray->RegisterComponent();SprayActor->SetActorLocation(FVector(-600,-13900,-20));
  for(int32 I=0;I<40;++I)Spray->AddInstance(FTransform(FRotator::ZeroRotator,FVector::ZeroVector,FVector(.18f)));SprayActor->SetActorHiddenInGame(true);}
 if(Sail)Sail->SetActorScale3D(FVector(1));if(Cruise)Cruise->SetActorScale3D(FVector(1.6));if(Whale)Whale->SetActorScale3D(FVector(1.4));
 UE_LOG(LogTemp,Display,TEXT("Maré marine assets: %s"),HasMarineModels()?TEXT("ready"):TEXT("incomplete"));
}
void UMareMarineWorld::Tick(float DeltaSeconds)
{
 auto World=GetWorld();if(!World || !World->IsGameWorld() || !Cast<AMareGameMode>(World->GetAuthGameMode()))return;
 if(!bInitialized)SpawnModels();if(!HasMarineModels())return;
 auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const double Time=World->GetTimeSeconds();const double Minutes=UMareSimulation::Number(Sim->State,TEXT("minutes"));const bool Day=Minutes>=360 && Minutes<1140;
 Sail->SetActorHiddenInGame(!Day);Cruise->SetActorHiddenInGame(Day);
 const float X=-12000.f+FMath::Fmod(16000.f+float(Time)*50.f,36000.f);
 const FRotator SailRot(0,90,.46f*FMath::Sin(float(Time)*.8f));Sail->SetActorRotation(SailRot);
 const auto Bounds=Sail->GetStaticMeshComponent()->GetStaticMesh()->GetBounds();const FVector Offset(-Bounds.Origin.X,-Bounds.Origin.Y,-(Bounds.Origin.Z-Bounds.BoxExtent.Z));
 Sail->SetActorLocation(FVector(X,-22000.f,-270.f+3.5f*FMath::Sin(float(Time)*1.2f))+SailRot.RotateVector(Offset));
 Cruise->SetActorLocation(FVector(4000,-21000,-30));Cruise->SetActorRotation(FRotator(0,6.8f,0));
 CurrentPhase=FMath::Fmod(float(Time),32.f);const bool Airborne=CurrentPhase<4.f;Whale->SetActorHiddenInGame(!Airborne);
 if(Airborne){const float U=CurrentPhase/4.f;const auto W=Whale->GetStaticMeshComponent()->GetStaticMesh()->GetBounds();const float Lift=-(W.Origin.Z-W.BoxExtent.Z)*1.4f;
  Whale->SetActorLocation(FVector(-1200+FMath::Lerp(-600.f,600.f,U),-13900,-530.f+1400.f*FMath::Sin(PI*U)+Lift));Whale->SetActorRotation(FRotator(FMath::Lerp(63.f,-13.f,U),15,0));}
 const float Impact=CurrentPhase-4.f;const bool Waves=Impact>=0 && Impact<6.f;const bool Droplets=Impact>=0 && Impact<2.4f;
 Ripple->SetActorHiddenInGame(!Waves);SprayActor->SetActorHiddenInGame(!Droplets);
 if(Waves && RippleMaterial)RippleMaterial->SetScalarParameterValue(TEXT("Strength"),FMath::Clamp(1.f-Impact/6.f,0.f,1.f));
 if(Droplets){for(int32 I=0;I<40;++I){const float T=FMath::Max(0.f,Impact-(I%7)*.022f),Angle=I*2.39996f,Speed=200.f+(I%9)*42.f;
   const FVector P(FMath::Cos(Angle)*Speed*T,FMath::Sin(Angle)*Speed*T,FMath::Max(0.f,(800.f+(I%5)*100.f)*T-490.f*T*T));
   const float Scale=.18f*FMath::Max(.15f,1.f-T/2.4f);Spray->UpdateInstanceTransform(I,FTransform(FRotator::ZeroRotator,P,FVector(Scale,Scale,Scale*2.5f)),false,false,true);}
  Spray->MarkRenderStateDirty();}
 const bool Hit=Impact>=0 && Impact<.3f;
 if(Hit && !bPreviousImpact){if(auto Pawn=UGameplayStatics::GetPlayerPawn(World,0)){const float Distance=FVector::Dist2D(Pawn->GetActorLocation(),FVector(-600,-13900,0));const float Gain=.16f*FMath::Clamp(1.f-Distance/22000.f,0.f,1.f);if(auto Audio=World->GetSubsystem<UMareAudioWorld>())Audio->PlayCue(TEXT("whale_splash"),Gain,nullptr,true);}}
 bPreviousImpact=Hit;
}
