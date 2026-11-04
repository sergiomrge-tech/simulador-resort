#include "MareMarineWorld.h"
#include "MareGame.h"
#include "MareSimulation.h"
#include "MareAudioWorld.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "HAL/IConsoleManager.h"
#include "Engine/GameInstance.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

// Volcano ash (Sergio, 04/11): the plume rises only on some days, drawn from the day number (same day = same answer).
static TAutoConsoleVariable<int32> CVarMareVolcanoSmoke(TEXT("mare.VolcanoSmoke"),-1,TEXT("Volcano ash plume: -1 = random days (about 35%), 0 = never, 1 = always (QA)."));
bool UMareMarineWorld::VolcanoSmokesOnDay(int32 Day){return (uint32(HashCombine(GetTypeHash(Day),0x9E3779B9u))%100u)<35u;}
// Night eruption (Sergio, 04/11): lava glowing down the ravines facing the beach, crater fire and a lit plume, on random nights.
static TAutoConsoleVariable<int32> CVarMareVolcanoErupt(TEXT("mare.VolcanoErupt"),-1,TEXT("Volcano night eruption: -1 = random nights (about 20%), 0 = never, 1 = every night (QA)."));
bool UMareMarineWorld::VolcanoEruptsOnNight(int32 Day){return (uint32(HashCombine(GetTypeHash(Day),0x7F4A7C15u))%100u)<20u;}
TStatId UMareMarineWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareMarineWorld,STATGROUP_Tickables);}
// The cruise, the whale and the daytime galleon were all removed (Sergio, 04/11); the coast boats, gulls and the
// volcano remain.
bool UMareMarineWorld::HasMarineModels() const{return bInitialized;}
bool UMareMarineWorld::IsSailVisible() const{return IsValid(Sail) && !Sail->IsHidden();}
// The night cruise was removed from the game (Sergio, 04/11); kept as a query for the QA checks.
bool UMareMarineWorld::IsCruiseVisible() const{return IsValid(Cruise) && !Cruise->IsHidden();}
bool UMareMarineWorld::IsWhaleVisible() const{return IsValid(Whale) && !Whale->IsHidden();}
bool UMareMarineWorld::IsRippleVisible() const{return IsValid(Ripple) && !Ripple->IsHidden();}
bool UMareMarineWorld::IsPassingBoatVisible() const{return IsValid(PassingBoat) && !PassingBoat->IsHidden();}
void UMareMarineWorld::SpawnModels()
{
 bInitialized=true;
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto MakeBoat=[&](const TCHAR* Path){auto Mesh=LoadObject<UStaticMesh>(nullptr,Path);if(!Mesh)return (AStaticMeshActor*)nullptr;
  auto Actor=GetWorld()->SpawnActor<AStaticMeshActor>(FVector::ZeroVector,FRotator::ZeroRotator,Params);if(!Actor)return (AStaticMeshActor*)nullptr;
  auto Component=Actor->GetStaticMeshComponent();Component->SetMobility(EComponentMobility::Movable);Component->SetStaticMesh(Mesh);Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);Actor->SetActorHiddenInGame(true);return Actor;};
 PassingBoat=MakeBoat(TEXT("/Game/Custom/Boats/mare_bote/mare_bote.mare_bote"));PassingRaft=MakeBoat(TEXT("/Game/Custom/Boats/mare_jangada/mare_jangada.mare_jangada"));

 UE_LOG(LogTemp,Display,TEXT("Maré marine assets: %s"),HasMarineModels()?TEXT("ready"):TEXT("incomplete"));
}
void UMareMarineWorld::Tick(float DeltaSeconds)
{
 auto World=GetWorld();if(!World || !World->IsGameWorld() || !Cast<AMareGameMode>(World->GetAuthGameMode()))return;
 if(!bInitialized)SpawnModels();if(!HasMarineModels())return;
 auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const double Time=World->GetTimeSeconds();const double Minutes=UMareSimulation::Number(Sim->State,TEXT("minutes"));const bool Day=Minutes>=360 && Minutes<1140;
 // Plume tagged MareVolcanoPlume by Content/Python/mare_volcano.py (level actor), found once.
 if(!bVolcanoSearched){bVolcanoSearched=true;for(TActorIterator<AStaticMeshActor> It(World);It;++It)if(It->ActorHasTag(TEXT("MareVolcanoPlume"))){VolcanoPlume=*It;break;}}
 {const int32 GameDay=int32(UMareSimulation::Number(Sim->State,TEXT("day"),1));
  // A night belongs to the day it started on: after midnight it is still the previous evening's eruption.
  const int32 NightDay=Minutes<360?GameDay-1:GameDay;
  const int32 EruptMode=CVarMareVolcanoErupt.GetValueOnGameThread();
  const bool bErupt=!Day && (EruptMode==1 || (EruptMode<0 && VolcanoEruptsOnNight(NightDay)));
  const float Target=bErupt?1.f:0.f;VolcanoGlow=FMath::FInterpTo(VolcanoGlow,Target,DeltaSeconds,.5f);
  if(!VolcanoCollection)VolcanoCollection=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
  if(VolcanoCollection)UKismetMaterialLibrary::SetScalarParameterValue(World,VolcanoCollection,TEXT("Volcano"),VolcanoGlow);
  if(VolcanoPlume){const int32 Mode=CVarMareVolcanoSmoke.GetValueOnGameThread();
   const bool bSmoke=bErupt || Mode==1 || (Mode<0 && Day && VolcanoSmokesOnDay(GameDay));
   if(VolcanoPlume->IsHidden()==bSmoke)VolcanoPlume->SetActorHiddenInGame(!bSmoke);}}
 UpdateLife(float(Time),Day);
}

void UMareMarineWorld::UpdateLife(float Time,bool bDay)
{
 // Boats along the coast: models float at their waterline (z = 0 in the model), the sea plane is at z -30; they
 // pitch and roll with the swell. The models face local -Y: yaw 90 heads +X, -90 heads -X.
 auto Pass=[&](AStaticMeshActor* Boat,float Y,float Speed,float Offset,float Yaw){if(!IsValid(Boat))return;Boat->SetActorHiddenInGame(!bDay);if(!bDay)return;
  const float Span=26000.f;const float U=FMath::Fmod(Offset+Time*FMath::Abs(Speed),Span);
  Boat->SetActorLocation(FVector(Speed>0?-9000.f+U:17000.f-U,Y,-30.f+12.f*FMath::Sin(Time*1.1f+Offset)));
  Boat->SetActorRotation(FRotator(2.2f*FMath::Sin(Time*.9f+Offset),Yaw,3.5f*FMath::Sin(Time*.7f+Offset*.5f)));};
 Pass(PassingBoat,-5200.f,320.f,0.f,90.f);
 Pass(PassingRaft,-7500.f,-260.f,9000.f,-90.f);
 // Seagulls: the exported gliding gulls circle around where they were placed, rising and dipping, banking into
 // the turn. Their model faces local +Y (Blender front -Y), so the heading is the tangent minus 90 degrees.
 if(!bGullsIndexed){bGullsIndexed=true;int32 N=0;
  for(TObjectIterator<UInstancedStaticMeshComponent> It;It;++It){UInstancedStaticMeshComponent* C=*It;
   if(C->GetWorld()!=GetWorld() || !C->GetStaticMesh() || C->GetStaticMesh()->GetName()!=TEXT("World_0536"))continue;
   C->SetMobility(EComponentMobility::Movable);
   for(int32 I=0;I<C->GetInstanceCount();++I){FTransform T;C->GetInstanceTransform(I,T,true);FGull G;G.Component=C;G.Index=I;G.Scale=T.GetScale3D();
    G.Radius=600.f+(N%3)*250.f;G.Speed=(N%2?1.f:-1.f)*(.2f+.03f*(N%4));G.Phase=N*1.7f;G.Centre=T.GetLocation()-FVector(FMath::Cos(G.Phase),FMath::Sin(G.Phase),0)*G.Radius;Gulls.Add(G);++N;}}}
 TSet<UInstancedStaticMeshComponent*> Dirty;
 for(int32 K=0;K<Gulls.Num();++K){const FGull& G=Gulls[K];auto C=G.Component.Get();if(!C)continue;
  const float A=G.Phase+Time*G.Speed;const FVector P=G.Centre+FVector(FMath::Cos(A)*G.Radius,FMath::Sin(A)*G.Radius,90.f*FMath::Sin(Time*.6f+K));
  const FVector Dir=FVector(-FMath::Sin(A),FMath::Cos(A),0)*FMath::Sign(G.Speed);const float Heading=FMath::RadiansToDegrees(FMath::Atan2(Dir.Y,Dir.X))-90.f;
  C->UpdateInstanceTransform(G.Index,FTransform(FRotator(0,Heading,-16.f*FMath::Sign(G.Speed)),P,G.Scale),true,false,true);Dirty.Add(C);}
 for(auto C:Dirty)C->MarkRenderStateDirty();
}
