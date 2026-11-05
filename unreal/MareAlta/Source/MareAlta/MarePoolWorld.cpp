#include "MarePoolWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"

TStatId UMarePoolWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMarePoolWorld,STATGROUP_Tickables);}

void UMarePoolWorld::Deinitialize()
{
 if(IsValid(Cooler))Cooler->Destroy();if(IsValid(CoolerModel))CoolerModel->Destroy();
 for(auto& Pair:Props)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Targets)if(IsValid(Pair.Value))Pair.Value->Destroy();
 Props.Empty();Targets.Empty();Super::Deinitialize();
}

void UMarePoolWorld::Show(const FString& Key,bool bWanted,const TCHAR* Mesh,const FVector& At,float Yaw,FName Action,const FString& Label,int32 Data,float Focus)
{
 AStaticMeshActor* Prop=Props.FindRef(Key);AMareServiceTarget* Target=Targets.FindRef(Key);
 if(!bWanted){if(IsValid(Prop))Prop->Destroy();if(IsValid(Target))Target->Destroy();Props.Remove(Key);Targets.Remove(Key);return;}
 if(IsValid(Prop))return;
 if(auto Model=LoadObject<UStaticMesh>(nullptr,Mesh)){
  Prop=GetWorld()->SpawnActor<AStaticMeshActor>(At,FRotator(0,Yaw,0));Prop->SetMobility(EComponentMobility::Movable);
  Prop->GetStaticMeshComponent()->SetStaticMesh(Model);Prop->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Props.Add(Key,Prop);}
 Target=GetWorld()->SpawnActor<AMareServiceTarget>(At,FRotator(0,Yaw,0));
 Target->Action=Action;Target->Label=Label;Target->DataIndex=Data;Target->FocusOffset=FVector(0,0,Focus);Target->Reach=260;Target->OcclusionTolerance=80;
 Targets.Add(Key,Target);
}

void UMarePoolWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || !GetWorld()->GetGameInstance())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("pool"),bOwned);
 const auto Defs=S->PoolDefs();const auto P=UMareSimulation::Object(S->State,TEXT("pool"));
 // Leaves: one floating cluster per started quarter of dirt, on the first spots.
 const int32 Clusters=bOwned?FMath::CeilToInt(UMareSimulation::Number(P,TEXT("dirt"))/UMareSimulation::Number(Defs,TEXT("scoop"),25)):0;
 const double WaterZ=UMareSimulation::Number(Defs,TEXT("water_z"),-8);
 const TArray<TSharedPtr<FJsonValue>>* Spots=nullptr;
 if(Defs->TryGetArrayField(TEXT("leaf_spots"),Spots))for(int32 I=0;I<Spots->Num();++I){const auto& V=(*Spots)[I]->AsArray();
  Show(FString::Printf(TEXT("leaf:%d"),I),I<Clusters,TEXT("/Game/Custom/PoolMess/pool_leaves/pool_leaves.pool_leaves"),
   FVector(V[0]->AsNumber(),V[1]->AsNumber(),WaterZ),I*67.f,TEXT("PoolLeaves"),TEXT("Peneirar as folhas"),I,6);}
 // Towels left on loungers.
 TSet<int32> Towels;const TArray<TSharedPtr<FJsonValue>>* T=nullptr;if(P->TryGetArrayField(TEXT("towels"),T))for(const auto& V:*T)Towels.Add(int32(V->AsNumber()));
 const TArray<TSharedPtr<FJsonValue>>* Loungers=nullptr;
 if(Defs->TryGetArrayField(TEXT("loungers"),Loungers))for(int32 I=0;I<Loungers->Num();++I){const auto& V=(*Loungers)[I]->AsArray();
  Show(FString::Printf(TEXT("towel:%d"),I),bOwned && Towels.Contains(I),TEXT("/Game/Custom/RoomMess/mess_towel/mess_towel.mess_towel"),
   FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber()),I*41.f,TEXT("PoolTowel"),TEXT("Recolher a toalha"),I,8);}
 // Popsicle cooler on the deck; its label says how many were asked for.
 const TArray<TSharedPtr<FJsonValue>>* C=nullptr;
 if(!Cooler && bOwned && Defs->TryGetArrayField(TEXT("cooler"),C) && C->Num()==4){
  const FVector At((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),(*C)[2]->AsNumber());const FRotator Yaw(0,(*C)[3]->AsNumber(),0);
  if(auto Model=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/World/Models/World_0345/World_0345/StaticMeshes/World_0345.World_0345"))){
   CoolerModel=GetWorld()->SpawnActor<AStaticMeshActor>(At,Yaw);CoolerModel->SetMobility(EComponentMobility::Movable);CoolerModel->GetStaticMeshComponent()->SetStaticMesh(Model);}
  Cooler=GetWorld()->SpawnActor<AMareServiceTarget>(At,Yaw);Cooler->Action=TEXT("PoolCooler");Cooler->FocusOffset=FVector(0,0,45);Cooler->Reach=240;Cooler->OcclusionTolerance=80;}
 if(Cooler){const int32 Want=int32(UMareSimulation::Number(P,TEXT("popsicles")));
  Cooler->Label=Want>0?FString::Printf(TEXT("Vender picolés (%d pedidos)"),Want):TEXT("Cooler de picolés · ninguém pediu");
  // Homemade by the ice cream shop (3.1): the label tells what is left inside.
  if(S->OwnsBusiness(TEXT("sorveteria")))Cooler->Label+=FString::Printf(TEXT(" · %d caseiro(s) no cooler"),int32(UMareSimulation::Number(P,TEXT("popsicle_stock"))));
  Cooler->SetActorHiddenInGame(!bOwned);if(CoolerModel){CoolerModel->SetActorHiddenInGame(!bOwned);CoolerModel->SetActorEnableCollision(bOwned);}}
}
