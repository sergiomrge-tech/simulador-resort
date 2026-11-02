#include "MareBarWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

namespace
{
 UMareSimulation* Sim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 FVector Point(const TSharedPtr<FJsonObject>& Defs,const FString& Key,double* Yaw=nullptr)
 {
  const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!Defs->TryGetArrayField(Key,At) || At->Num()<3)return FVector::ZeroVector;
  if(Yaw)*Yaw=At->Num()>3?(*At)[3]->AsNumber():0;
  return FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());
 }
}

TStatId UMareBarWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareBarWorld,STATGROUP_Tickables);}

void UMareBarWorld::Deinitialize()
{
 if(IsValid(Station))Station->Destroy();if(IsValid(Barman))Barman->Destroy();
 for(auto& Pair:Guests)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Leaving)if(IsValid(Pair.Key))Pair.Key->Destroy();
 Guests.Empty();Leaving.Empty();Super::Deinitialize();
}

AMarePerson* UMareBarWorld::Seat(const FString& Order,const FString& Name,int32 Stool)
{
 auto Defs=Sim(GetWorld())->BarDefs();const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(!Defs->TryGetArrayField(TEXT("stools"),List) || !List->IsValidIndex(Stool))return nullptr;
 const auto& S=(*List)[Stool]->AsArray();const FRotator Facing(0,S[2]->AsNumber(),0);
 // Sitting_Idle puts the hips 46 cm over the root and 33 cm behind it: the root goes in front of the stool seat.
 const TArray<TSharedPtr<FJsonValue>>* SeatFit=nullptr;double SeatTop=82,Ahead=30;
 if(Defs->TryGetArrayField(TEXT("seat"),SeatFit) && SeatFit->Num()==2){SeatTop=(*SeatFit)[0]->AsNumber();Ahead=(*SeatFit)[1]->AsNumber();}
 const FVector At=FVector(S[0]->AsNumber(),S[1]->AsNumber(),SeatTop-46+88)+Facing.Vector()*Ahead;
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto Person=GetWorld()->SpawnActor<AMarePerson>(At,Facing,Params);if(!Person)return nullptr;
 Person->SaveId=TEXT("bar_")+Order;Person->PersonName=Name;Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);
 Person->bAmbient=true;Person->bSeated=true;Person->GetCharacterMovement()->DisableMovement();
 Person->SetActorEnableCollision(false);return Person;
}

void UMareBarWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=Sim(GetWorld());if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("bar"),bOwned);
 const auto Defs=S->BarDefs();
 if(!Station && bOwned){
  Station=GetWorld()->SpawnActor<AMareServiceTarget>(Point(Defs,TEXT("station")),FRotator::ZeroRotator);
  Station->Action=TEXT("BarCounter");Station->Label=TEXT("Bar do Coqueiro · preparar drinks");Station->Reach=230;Station->OcclusionTolerance=70;}
 if(Station)Station->SetActorHiddenInGame(!bOwned);
 const double Now=GetWorld()->GetTimeSeconds();
 for(auto It=Leaving.CreateIterator();It;++It)if(!IsValid(It->Key) || Now>It->Value){if(IsValid(It->Key))It->Key->Destroy();It.RemoveCurrent();}
 // Bartender behind the counter while one is hired and the bar is open.
 const bool bBarman=bOwned && S->HasStaff(TEXT("bartender")) && S->IsBarOpen();
 if(bBarman && !Barman){double Yaw=0;const FVector At=Point(Defs,TEXT("barman"),&Yaw);
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  Barman=GetWorld()->SpawnActor<AMarePerson>(At+FVector(0,0,88),FRotator(0,Yaw,0),Params);
  if(Barman){Barman->SaveId=TEXT("bar_bartender");Barman->PersonName=TEXT("Bartender");Barman->bEmployee=true;Barman->StaffRole=TEXT("bartender");Barman->bAmbient=true;
   Barman->GetCharacterMovement()->DisableMovement();Barman->SetActorEnableCollision(false);}}
 else if(!bBarman && Barman){Barman->Destroy();Barman=nullptr;}
 // One guest per open order on a free stool; a guest whose order is gone stands up and walks off.
 TArray<FString> Open;const TArray<TSharedPtr<FJsonValue>>* Orders=nullptr;
 if(bOwned && UMareSimulation::Object(S->State,TEXT("bar"))->TryGetArrayField(TEXT("orders"),Orders))
  for(const auto& V:*Orders)Open.Add(UMareSimulation::String(V->AsObject(),TEXT("id")));
 const int32 Served=int32(UMareSimulation::Number(UMareSimulation::Object(S->State,TEXT("bar")),TEXT("served")));
 const bool bJustServed=LastServed>=0 && Served>LastServed;LastServed=Served;
 for(auto It=Guests.CreateIterator();It;++It){if(Open.Contains(It->Key))continue;AMarePerson* Person=It->Value;
  if(IsValid(Person)){
   if(bJustServed){const FString Last=UMareSimulation::String(UMareSimulation::Object(S->State,TEXT("bar")),TEXT("last"));
    Person->HoldProduct(UMareSimulation::String(S->BarRecipe(Last),TEXT("mesh")));}
   Person->bSeated=false;Person->SetActorEnableCollision(true);Person->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
   const FVector Away=Person->GetActorLocation()+Person->GetActorForwardVector()*-900+FVector(0,-600,0);
   Leaving.Add(Person,Now+(Person->WalkTo(Away)?25.:4.));}
  Stools.Remove(It->Key);It.RemoveCurrent();}
 const TArray<TSharedPtr<FJsonValue>>* Seats=nullptr;const int32 Count=Defs->TryGetArrayField(TEXT("stools"),Seats)?Seats->Num():0;
 for(const auto& V:Orders?*Orders:TArray<TSharedPtr<FJsonValue>>()){const auto O=V->AsObject();const FString Id=UMareSimulation::String(O,TEXT("id"));
  if(Guests.Contains(Id))continue;
  TSet<int32> Used;for(const auto& Pair:Stools)Used.Add(Pair.Value);
  int32 Free=INDEX_NONE;for(int32 I=0;I<Count && Free==INDEX_NONE;++I)if(!Used.Contains(I))Free=I;if(Free==INDEX_NONE)break;
  if(auto Person=Seat(Id,UMareSimulation::String(O,TEXT("name")),Free)){Guests.Add(Id,Person);Stools.Add(Id,Free);}}
}
