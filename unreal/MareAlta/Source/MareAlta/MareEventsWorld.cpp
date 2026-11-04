#include "MareEventsWorld.h"
#include "MareSimulation.h"
#include "MarePerson.h"
#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/PointLight.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"

// QA: "mare.Event junina" makes today's event a party (events.json id; empty = none) to check the decoration and dancers.
static FAutoConsoleCommandWithWorldAndArgs EventQACommand(TEXT("mare.Event"),TEXT("QA: sets today's event (events.json id)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(World && World->GetGameInstance())if(auto S=World->GetGameInstance()->GetSubsystem<UMareSimulation>())
   S->State->SetStringField(TEXT("day_event"),Args.Num()?Args[0]:FString());}));

TStatId UMareEventsWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareEventsWorld,STATGROUP_Tickables);}

void UMareEventsWorld::Clear()
{
 for(auto& P:Props)if(IsValid(P))P->Destroy();Props.Empty();
 if(IsValid(Fire))Fire->Destroy();Fire=nullptr;
 if(IsValid(Flames))Flames->DestroyComponent();Flames=nullptr;
 for(auto& D:Dancers)if(D.IsValid())D->WorkPose.Reset();
 Dancers.Empty();PartyCentre=FVector::ZeroVector;
}

void UMareEventsWorld::UpdateDancers()
{
 // Within 9 m of the party: guests and villagers who are not seated, working or eating dance while they stand there
 // (AMarePerson plays WorkPose when not walking). The clip is fixed per person; junina and quermesse cheer more.
 if(PartyCentre.IsZero())return;
 const bool bFolk=Shown.StartsWith(TEXT("junina")) || Shown.StartsWith(TEXT("quermesse"));
 for(int32 I=Dancers.Num()-1;I>=0;--I){AMarePerson* P=Dancers[I].Get();
  if(!P || FVector::Dist2D(P->GetActorLocation(),PartyCentre)>1100 || P->bSeated){if(P)P->WorkPose.Reset();Dancers.RemoveAt(I);}}
 for(TActorIterator<AMarePerson> It(GetWorld());It;++It){AMarePerson* P=*It;
  // Only villagers and walkers (bAmbient): kiosk customers waiting in line or at a table keep their own poses.
  if(!P->bAmbient || P->bEmployee || P->bSeated || P->bLying || !P->WorkPose.IsEmpty())continue;
  if(FVector::Dist2D(P->GetActorLocation(),PartyCentre)>900)continue;
  // MH_Dance stays out: the capture bends 50 cm forward with the arms hanging, which reads as broken in the game.
  static const TCHAR* Dance[]={TEXT("DanceHip"),TEXT("Cheer"),TEXT("DanceHip")};
  static const TCHAR* Folk[]={TEXT("Cheer"),TEXT("DanceHip"),TEXT("Cheer")};
  P->WorkPose=(bFolk?Folk:Dance)[FCrc::StrCrc32(*(P->SaveId+P->PersonName))%3];Dancers.Add(P);}
}

void UMareEventsWorld::Deinitialize(){Clear();Super::Deinitialize();}

void UMareEventsWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || !GetWorld()->GetGameInstance())return;
 auto S=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 // The bonfire flickers every frame; the layout is checked twice a second.
 if(IsValid(Fire))Fire->PointLightComponent->SetIntensity(9000.f*(.8f+.2f*FMath::Sin(GetWorld()->GetTimeSeconds()*11.f)*FMath::Sin(GetWorld()->GetTimeSeconds()*4.3f)));
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 UpdateDancers();
 const FString Event=S->TodayEvent();bool bParty=false;S->EventDef(Event)->TryGetBoolField(TEXT("party"),bParty);
 const FString Want=bParty?Event+(S->IsPrepActive()?TEXT("+deco"):TEXT("")):FString();
 if(Want==Shown)return;Shown=Want;Clear();if(Want.IsEmpty())return;
 const TArray<TSharedPtr<FJsonValue>>* Spot=nullptr;if(!S->EventDefs()->TryGetArrayField(TEXT("party_spot"),Spot) || Spot->Num()!=3)return;
 const FVector Centre((*Spot)[0]->AsNumber(),(*Spot)[1]->AsNumber(),(*Spot)[2]->AsNumber());PartyCentre=Centre;
 auto Ground=[this](FVector At){FHitResult Hit;if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,600),At-FVector(0,0,800),ECC_Visibility))At.Z=Hit.ImpactPoint.Z;return At;};
 // Local layout in metres around the centre (x east, y north), yaw in degrees.
 auto Put=[&](const TCHAR* Name,float X,float Y,float Yaw,float Lift=0,float Scale=1){
  // A model from Fab (<name>_fab, tools/ue58/prep_fab_food.py) replaces the generated one when it exists.
  auto Load=[](const FString& N){return LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Custom/Festival/%s/%s.%s"),*N,*N,*N));};
  UStaticMesh* Found=Load(FString(Name)+TEXT("_fab"));if(!Found)Found=Load(Name);
  if(auto Mesh=Found){
   auto A=GetWorld()->SpawnActor<AStaticMeshActor>(Ground(Centre+FVector(X*100,Y*100,0))+FVector(0,0,Lift),FRotator(0,Yaw,0));
   A->SetMobility(EComponentMobility::Movable);A->SetActorScale3D(FVector(Scale));A->GetStaticMeshComponent()->SetStaticMesh(Mesh);A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Props.Add(A);}};
 const bool bDeco=Want.EndsWith(TEXT("+deco"));
 if(Event==TEXT("quermesse")){Put(TEXT("festa_stall"),-3,0,90);Put(TEXT("festa_stall"),0,2,0);Put(TEXT("festa_stall"),3,0,-90);
  Put(TEXT("festa_bunting"),-1.5,-1.5,0);Put(TEXT("festa_bunting"),1.5,-1.5,0);}
 else if(Event==TEXT("junina")){
  // Bonfire: the scanned Quixel campfire (logs, ashes, stones; tools/ue58/prep_fab_food.py campfire) with simulated
  // flames and smoke (Niagara Fluids template); the old generated logs and mesh flame remain only as a fallback.
  static UStaticMesh* Scan=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Custom/Festival/festa_campfire_scan/festa_campfire_scan.festa_campfire_scan"));
  static UNiagaraSystem* FireFx=LoadObject<UNiagaraSystem>(nullptr,TEXT("/NiagaraFluids/Templates/Gas/2D/Systems/Grid2D_Gas_SmokeFire.Grid2D_Gas_SmokeFire"));
  if(Scan)Put(TEXT("festa_campfire_scan"),0,0,0,0,2.0f);else Put(TEXT("festa_campfire_logs"),0,0,0,0,2.4f);
  if(FireFx)Flames=UNiagaraFunctionLibrary::SpawnSystemAtLocation(GetWorld(),FireFx,Ground(Centre)+FVector(0,0,10),FRotator::ZeroRotator,FVector(1.1f),false,true);
  else Put(TEXT("festa_fire"),0,0,0,5,1.5f);
  Put(TEXT("festa_stall"),0,4,0);
  Put(TEXT("festa_bunting"),-3.5,0,90);Put(TEXT("festa_bunting"),3.5,0,90);
  Fire=GetWorld()->SpawnActor<APointLight>(Ground(Centre)+FVector(0,0,120),FRotator::ZeroRotator);
  if(Fire){Fire->PointLightComponent->SetLightColor(FLinearColor(1.f,.55f,.2f));Fire->PointLightComponent->SetAttenuationRadius(1400);Fire->PointLightComponent->SetMobility(EComponentMobility::Movable);}}
 else if(Event==TEXT("show_dj")){Put(TEXT("festa_dj_booth"),0,2,0);Put(TEXT("festa_bunting"),0,-1,0);}
 else if(Event==TEXT("carnaval")){Put(TEXT("festa_dj_booth"),0,2,0);Put(TEXT("festa_bunting"),-3,-1,0);Put(TEXT("festa_bunting"),3,-1,0);Put(TEXT("festa_stall"),-5,1,90);}
 // Paid decoration: the party banner at the entrance and an extra row of bunting.
 if(bDeco){Put(TEXT("festa_banner"),0,-8,0);Put(TEXT("festa_bunting"),0,-5.5f,0);}
}
