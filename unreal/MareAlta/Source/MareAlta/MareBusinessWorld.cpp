#include "MareBusinessWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

TStatId UMareBusinessWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareBusinessWorld,STATGROUP_Tickables);}

void UMareBusinessWorld::Deinitialize()
{
 for(auto& Pair:Counters)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Waiting)if(IsValid(Pair.Value))Pair.Value->Destroy();
 Counters.Empty();Waiting.Empty();Super::Deinitialize();
}

void UMareBusinessWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || !GetWorld()->GetGameInstance())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 auto Ground=[this](FVector At){FHitResult Hit;
  if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,300),At-FVector(0,0,600),ECC_Visibility))At.Z=Hit.ImpactPoint.Z;return At;};
 for(const auto& Pair:UMareSimulation::Object(S->BusinessGames(),TEXT("businesses"))->Values){
  const FString Id(Pair.Key.ToView());const auto Def=Pair.Value->AsObject();const bool bOwned=S->OwnsBusiness(Id);
  const TArray<TSharedPtr<FJsonValue>>* C=nullptr;const TArray<TSharedPtr<FJsonValue>>* G=nullptr;
  if(!Def->TryGetArrayField(TEXT("counter"),C) || C->Num()!=4 || !Def->TryGetArrayField(TEXT("guest"),G) || G->Num()!=4)continue;
  AMareServiceTarget* Counter=Counters.FindRef(Id);
  if(!Counter && bOwned){
   const FVector At=Ground(FVector((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),0))+FVector(0,0,(*C)[2]->AsNumber());
   Counter=GetWorld()->SpawnActor<AMareServiceTarget>(At,FRotator(0,(*C)[3]->AsNumber(),0));
   Counter->Action=TEXT("BusinessCounter");Counter->Tags.Add(*(TEXT("biz:")+Id));Counter->Reach=260;Counter->OcclusionTolerance=90;
   Counter->Label=UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("businesses")),Id),TEXT("name"));
   Counters.Add(Id,Counter);}
  if(Counter)Counter->SetActorHiddenInGame(!bOwned);
  // A customer waits at the counter while this hour's task is available.
  FString Reason;const bool bDue=bOwned && S->CanPlayBusiness(Id,Reason);AMarePerson* Guest=Waiting.FindRef(Id);
  if(bDue && !IsValid(Guest)){
   FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
   const FVector At=Ground(FVector((*G)[0]->AsNumber(),(*G)[1]->AsNumber(),0))+FVector(0,0,90);
   Guest=GetWorld()->SpawnActor<AMarePerson>(At,FRotator(0,(*G)[3]->AsNumber(),0),Params);
   if(Guest){const int32 Hour=int32(UMareSimulation::Number(S->State,TEXT("day"),1))*24+FMath::FloorToInt(UMareSimulation::Number(S->State,TEXT("minutes"))/60);
    Guest->SaveId=FString::Printf(TEXT("biz_%s_%d"),*Id,Hour);Guest->PersonName=TEXT("Cliente");Guest->SetAppearance(FCrc::StrCrc32(*Guest->SaveId)%4);
    Guest->bAmbient=true;Guest->GetCharacterMovement()->DisableMovement();Waiting.Add(Id,Guest);}}
  else if(!bDue && IsValid(Guest)){Guest->Destroy();Waiting.Remove(Id);}
 }
}
