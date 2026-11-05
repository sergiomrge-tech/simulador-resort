#include "MareToursWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

TStatId UMareToursWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareToursWorld,STATGROUP_Tickables);}

void UMareToursWorld::Deinitialize()
{
 if(IsValid(Booth))Booth->Destroy();if(IsValid(BoothModel))BoothModel->Destroy();if(IsValid(Fishing))Fishing->Destroy();
 for(auto& P:Buyers)if(IsValid(P))P->Destroy();
 for(auto& Pair:Passengers)for(auto& P:Pair.Value)if(P.IsValid())P->Destroy();
 for(auto& Pair:Leaving)if(IsValid(Pair.Key))Pair.Key->Destroy();
 Buyers.Empty();Passengers.Empty();Leaving.Empty();Super::Deinitialize();
}

FVector UMareToursWorld::Ground(FVector At) const
{
 FHitResult Hit;if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,400),At-FVector(0,0,800),ECC_Visibility))At.Z=Hit.ImpactPoint.Z;return At;
}

AMarePerson* UMareToursWorld::Spawn(const FVector& At,float Yaw,const FString& Id)
{
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
 auto Person=GetWorld()->SpawnActor<AMarePerson>(Ground(At)+FVector(0,0,90),FRotator(0,Yaw,0),Params);if(!Person)return nullptr;
 Person->SaveId=Id;Person->PersonName=TEXT("Turista");Person->SetAppearance(FCrc::StrCrc32(*Id)%4);Person->bAmbient=true;
 Person->GetCharacterMovement()->DisableMovement();return Person;
}

TArray<TPair<FVector,FString>> UMareToursWorld::Bubbles()const
{
 TArray<TPair<FVector,FString>> Out;auto S=GetWorld() && GetWorld()->GetGameInstance()?GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;if(!S)return Out;
 int32 I=0;for(const FString& Id:S->TourIds())for(const auto& G:S->TourGroups(Id)){if(!Buyers.IsValidIndex(I) || !IsValid(Buyers[I]))return Out;
  Out.Add({Buyers[I]->GetActorLocation()+FVector(0,0,92),UMareSimulation::String(G,TEXT("name"))+TEXT(": ")+S->TourGroupLine(G)+TEXT(" · ")+UMareSimulation::String(S->TourDef(Id),TEXT("name"))});++I;}
 return Out;
}

void UMareToursWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || !GetWorld()->GetGameInstance())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("passeios"),bOwned);
 const auto Defs=S->ToursDefs();const double Now=GetWorld()->GetTimeSeconds();
 for(auto It=Leaving.CreateIterator();It;++It)if(!IsValid(It->Key) || Now>It->Value){if(IsValid(It->Key))It->Key->Destroy();It.RemoveCurrent();}
 const TArray<TSharedPtr<FJsonValue>>* B=nullptr;
 if(!Booth && bOwned && Defs->TryGetArrayField(TEXT("booth"),B) && B->Num()==4){
  const FVector At=Ground(FVector((*B)[0]->AsNumber(),(*B)[1]->AsNumber(),0));const FRotator Yaw(0,(*B)[3]->AsNumber(),0);
  // The rustic counter of the pousada reception doubles as the ticket booth (tools/ue58/gen_reception_desk.py).
  if(auto Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Custom/Reception/mare_reception_desk/mare_reception_desk.mare_reception_desk"))){
   BoothModel=GetWorld()->SpawnActor<AStaticMeshActor>(At,Yaw);BoothModel->SetMobility(EComponentMobility::Movable);BoothModel->GetStaticMeshComponent()->SetStaticMesh(Mesh);}
  Booth=GetWorld()->SpawnActor<AMareServiceTarget>(At+FVector(0,0,(*B)[2]->AsNumber()),Yaw);
  Booth->Action=TEXT("TourBooth");Booth->Label=TEXT("Bilheteria dos passeios");Booth->Reach=260;Booth->OcclusionTolerance=80;}
 // Fishing spot at the end of the pier, always there (Seu Severino's chapter asks for fish).
 const TArray<TSharedPtr<FJsonValue>>* F=nullptr;
 if(!Fishing && S->LeisureDefs()->TryGetArrayField(TEXT("fishing_spot"),F) && F->Num()==4){
  const FVector At=Ground(FVector((*F)[0]->AsNumber(),(*F)[1]->AsNumber(),0));
  Fishing=GetWorld()->SpawnActor<AMareServiceTarget>(At+FVector(0,0,90),FRotator(0,(*F)[3]->AsNumber(),0));
  if(Fishing){Fishing->Action=TEXT("Fishing");Fishing->Label=TEXT("Pescar na ponta do píer");Fishing->Reach=250;Fishing->OcclusionTolerance=90;}}
 if(Booth)Booth->SetActorHiddenInGame(!bOwned);
 if(BoothModel){BoothModel->SetActorHiddenInGame(!bOwned);BoothModel->SetActorEnableCollision(bOwned);}
 if(!bOwned)return;
 // Buyers in line: one figure per group waiting (or per person for an old count-only line), up to six.
 int32 Waiting=0;for(const FString& Id:S->TourIds()){if(!S->TourStatus(Id).IsEmpty())continue;const int32 G=S->TourGroups(Id).Num();Waiting+=G?G:S->TourCount(TEXT("queue"),Id);}Waiting=FMath::Min(Waiting,6);
 const TArray<TSharedPtr<FJsonValue>>* Q=nullptr;FVector First(7200,-2260,0);double Step=-85;
 if(Defs->TryGetArrayField(TEXT("queue"),Q) && Q->Num()==4){First=FVector((*Q)[0]->AsNumber(),(*Q)[1]->AsNumber(),0);Step=(*Q)[3]->AsNumber();}
 while(Buyers.Num()>Waiting){AMarePerson* P=Buyers.Pop();if(IsValid(P))P->Destroy();}
 while(Buyers.Num()<Waiting){const int32 I=Buyers.Num();
  if(auto P=Spawn(First+FVector(0,Step*I,0),90,FString::Printf(TEXT("tour_buyer_%d_%d"),int32(UMareSimulation::Number(S->State,TEXT("day"),1)),I)))Buyers.Add(P);else break;}
 // Passengers with a ticket wait further down the pier; they leave with the tour or go home when it is cancelled.
 int32 Slot=0;
 for(const FString& Id:S->TourIds()){auto& List=Passengers.FindOrAdd(Id);List.RemoveAll([](const TWeakObjectPtr<AMarePerson>& P){return !P.IsValid();});
  const FString Status=S->TourStatus(Id);
  if(!Status.IsEmpty()){
   FVector Goal=First+FVector(0,600,0);const TArray<TSharedPtr<FJsonValue>>* To=nullptr;
   if((Status==TEXT("guided") || Status==TEXT("guide")) && UMareSimulation::Object(Defs,TEXT("board"))->TryGetArrayField(Id,To) && To->Num()==3)
    Goal=FVector((*To)[0]->AsNumber(),(*To)[1]->AsNumber(),(*To)[2]->AsNumber());
   for(auto& P:List)if(P.IsValid()){P->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Leaving.Add(P.Get(),Now+(P->WalkTo(Goal)?40.:3.));}
   List.Empty();continue;}
  const int32 Sold=FMath::Min(S->TourCount(TEXT("sold"),Id),8);
  while(List.Num()<Sold){const FVector At=First+FVector(-60+120*(Slot%2),Step*(8+Slot/2),0);++Slot;
   if(auto P=Spawn(At,FMath::RandRange(0,360),FString::Printf(TEXT("tour_%s_%d"),*Id,List.Num())))List.Add(P);else break;}
  Slot+=List.Num();
 }
}
