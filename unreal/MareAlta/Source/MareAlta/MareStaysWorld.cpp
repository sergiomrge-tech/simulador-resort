#include "MareStaysWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

namespace
{
 /** Where each mess sits inside a bungalow (actor-local cm; floor is 49 cm above the actor origin, bed origin at
  *  (0,-82,45) from customization_places.py). The mesh, its yaw, the E focus height and the mesh scale
  *  (the bed's towel is spread wider so it reads from the door). */
 struct FMessSpot{const TCHAR* Task;const TCHAR* Mesh;FVector Local;float Yaw;float Focus;const TCHAR* Label;float Scale=1.f;};
 const FMessSpot Spots[]={
  {TEXT("bed"),TEXT("/Game/Custom/RoomMess/mess_towel/mess_towel.mess_towel"),FVector(10,-40,108),25,10,TEXT("Arrumar a cama"),1.8f},
  {TEXT("towels"),TEXT("/Game/Custom/RoomMess/mess_towel/mess_towel.mess_towel"),FVector(-95,70,49),-40,8,TEXT("Recolher as toalhas")},
  {TEXT("trash"),TEXT("/Game/Custom/RoomMess/mess_trash_bag/mess_trash_bag.mess_trash_bag"),FVector(120,115,49),0,20,TEXT("Tirar o lixo")}};
 UMareSimulation* Sim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
}

TStatId UMareStaysWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareStaysWorld,STATGROUP_Tickables);}

void UMareStaysWorld::Deinitialize()
{
 if(IsValid(DeskModel))DeskModel->Destroy();
 for(auto& Pair:Tasks)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Mess)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Guests)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Leaving)if(IsValid(Pair.Key))Pair.Key->Destroy();
 Tasks.Empty();Mess.Empty();Guests.Empty();Leaving.Empty();Super::Deinitialize();
}

void UMareStaysWorld::FindBungalows()
{
 // Bungalows are level actors tagged MareBungalow (mare_beach.place_bungalows); room i is the i-th from the east.
 for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareBungalow")))Bungalows.Add(*It);
 Bungalows.Sort([](const AActor& A,const AActor& B){return A.GetActorLocation().X>B.GetActorLocation().X;});
}

bool UMareStaysWorld::RoomPoint(int32 Room,const FVector& Local,FVector& Out) const
{
 if(!Bungalows.IsValidIndex(Room) || !IsValid(Bungalows[Room]))return false;
 Out=Bungalows[Room]->GetActorTransform().TransformPosition(Local);return true;
}

void UMareStaysWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=Sim(GetWorld());if(!S)return;
 bool bPousada=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("pousada"),bPousada);
 if(Bungalows.IsEmpty())FindBungalows();
 // Reception desk position comes from data (customization.json operations.pousada.reception) so it can move without a build.
 if(!Desk){const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
  auto Ops=UMareSimulation::Object(UMareSimulation::Object(S->CustomDefs(),TEXT("operations")),TEXT("pousada"));
  if(Ops->TryGetArrayField(TEXT("reception"),At) && At->Num()==4){
   // Ground under the given point, then the counter model (tools/ue58/gen_reception_desk.py) and its E target.
   FVector At3((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());FHitResult Hit;
   if(GetWorld()->LineTraceSingleByChannel(Hit,At3+FVector(0,0,500),At3-FVector(0,0,800),ECC_Visibility))At3.Z=Hit.ImpactPoint.Z;
   const FRotator Yaw(0,(*At)[3]->AsNumber(),0);
   if(auto Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Custom/Reception/mare_reception_desk/mare_reception_desk.mare_reception_desk"))){
    DeskModel=GetWorld()->SpawnActor<AStaticMeshActor>(At3,Yaw+FRotator(0,UMareSimulation::Number(Ops,TEXT("reception_mesh_yaw")),0));
    DeskModel->SetMobility(EComponentMobility::Movable);DeskModel->GetStaticMeshComponent()->SetStaticMesh(Mesh);}
   Desk=GetWorld()->SpawnActor<AMareServiceTarget>(At3+FVector(0,0,105),Yaw);
   Desk->Action=TEXT("PousadaReception");Desk->Label=TEXT("Recepção da pousada");Desk->Reach=260;Desk->OcclusionTolerance=60;}}
 if(Desk)Desk->SetActorHiddenInGame(!bPousada);
 if(DeskModel){DeskModel->SetActorHiddenInGame(!bPousada);DeskModel->SetActorEnableCollision(bPousada);}
 if(!bPousada)return;
 SyncTasks();SyncGuests();
}

void UMareStaysWorld::SyncTasks()
{
 auto S=Sim(GetWorld());TSet<FString> Want;
 const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;
 if(S->Stays()->TryGetArrayField(TEXT("rooms"),Rooms))for(int32 Room=0;Room<Rooms->Num();++Room){
  const auto R=(*Rooms)[Room]->AsObject();if(UMareSimulation::String(R,TEXT("state"))!=TEXT("dirty") || UMareSimulation::String(R,TEXT("place"))==TEXT("hotel"))continue;
  const TArray<TSharedPtr<FJsonValue>>* Left=nullptr;if(!R->TryGetArrayField(TEXT("tasks"),Left))continue;
  for(const auto& V:*Left)Want.Add(FString::Printf(TEXT("%d:%s"),Room,*V->AsString()));}
 // Remove what was cleaned (by the player, the maid or a new day) and spawn what is newly dirty.
 for(auto It=Tasks.CreateIterator();It;++It)if(!Want.Contains(It.Key())){
  if(IsValid(It.Value()))It.Value()->Destroy();if(auto M=Mess.FindRef(It.Key()))M->Destroy();Mess.Remove(It.Key());It.RemoveCurrent();}
 for(const FString& Key:Want){if(Tasks.Contains(Key))continue;
  FString RoomText,Task;Key.Split(TEXT(":"),&RoomText,&Task);const int32 Room=FCString::Atoi(*RoomText);
  const FMessSpot* Spot=nullptr;for(const auto& Candidate:Spots)if(Task==Candidate.Task)Spot=&Candidate;
  FVector At;if(!Spot || !RoomPoint(Room,Spot->Local,At))continue;
  const FRotator Yaw(0,Bungalows[Room]->GetActorRotation().Yaw+Spot->Yaw,0);
  if(auto Mesh=LoadObject<UStaticMesh>(nullptr,Spot->Mesh)){
   auto Prop=GetWorld()->SpawnActor<AStaticMeshActor>(At,Yaw);Prop->SetMobility(EComponentMobility::Movable);
   Prop->GetStaticMeshComponent()->SetStaticMesh(Mesh);Prop->SetActorScale3D(FVector(Spot->Scale,Spot->Scale,1.f));Prop->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Mess.Add(Key,Prop);}
  auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(At,Yaw);
  Target->Action=TEXT("RoomTask");Target->Label=FString(Spot->Label)+TEXT(" · bangalô ")+FString::FromInt(Room+1);
  Target->DataIndex=Room;Target->Tags.Add(*(TEXT("task:")+Task));Target->FocusOffset=FVector(0,0,Spot->Focus);Target->Reach=220;Target->OcclusionTolerance=60;
  Tasks.Add(Key,Target);}
}

void UMareStaysWorld::UseTask(int32 Room,const FString& Task)
{
 auto S=Sim(GetWorld());if(!S)return;
 if(S->CleanRoom(FString::Printf(TEXT("pousada_%d"),Room),Task)){
  if(auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>())Audio->PlayCue(TEXT("clean"),.3f);
  S->LastMessage=FString::Printf(TEXT("Bangalô %d: %s."),Room+1,Task==TEXT("bed")?TEXT("cama arrumada"):Task==TEXT("towels")?TEXT("toalhas recolhidas"):TEXT("lixo retirado"));
  SyncTasks();}
}

void UMareStaysWorld::SyncGuests()
{
 auto S=Sim(GetWorld());if(!Desk)return;
 const TArray<TSharedPtr<FJsonValue>>* Queue=nullptr;S->Stays()->TryGetArrayField(TEXT("queue"),Queue);
 TArray<TSharedPtr<FJsonObject>> Line;if(Queue)for(const auto& V:*Queue){const FString P=UMareSimulation::String(V->AsObject(),TEXT("place"));
  if(P.IsEmpty() || P==TEXT("pousada"))Line.Add(V->AsObject());}
 // Guests who left the line walk away: to their bungalow after a check-in, otherwise back down the path.
 for(auto It=Guests.CreateIterator();It;++It){if(Line.ContainsByPredicate([&](const auto& G){return UMareSimulation::String(G,TEXT("id"))==It.Key();}))continue;
  AMarePerson* Person=It.Value();It.RemoveCurrent();if(!IsValid(Person))continue;
  FVector Goal=Desk->GetActorLocation()+Desk->GetActorForwardVector()*900;
  const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;
  if(S->Stays()->TryGetArrayField(TEXT("rooms"),Rooms))for(int32 I=0;I<Rooms->Num();++I){const auto G=UMareSimulation::Object((*Rooms)[I]->AsObject(),TEXT("guest"));
   if(UMareSimulation::String(G,TEXT("id"))==Person->SaveId.Mid(8)){RoomPoint(I,FVector(0,260,49),Goal);break;}}   // the bungalow deck
  Person->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Person->WalkTo(Goal);Leaving.Add(Person,GetWorld()->GetTimeSeconds()+45);}
 for(auto It=Leaving.CreateIterator();It;++It){AMarePerson* Person=It.Key();
  if(!IsValid(Person) || Person->AtGoal() || GetWorld()->GetTimeSeconds()>It.Value()){if(IsValid(Person))Person->Destroy();It.RemoveCurrent();}}
 // The line forms in front of the desk, one metre apart, everyone facing the counter.
 const FVector Front=Desk->GetActorForwardVector();
 for(int32 I=0;I<Line.Num();++I){
  const FString Id=UMareSimulation::String(Line[I],TEXT("id"));const FVector Spot=Desk->GetActorLocation()+Front*(110+I*100)+FVector(0,0,90);
  auto& Person=Guests.FindOrAdd(Id);
  if(!IsValid(Person)){FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
   Person=GetWorld()->SpawnActor<AMarePerson>(Spot,(-Front).Rotation(),Params);if(!Person)continue;
   Person->SaveId=TEXT("pousada_")+Id;Person->PersonName=UMareSimulation::String(Line[I],TEXT("name"));
   Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);Person->bAmbient=true;Person->Tags.Add(TEXT("MarePousadaGuest"));
   Person->GetCharacterMovement()->DisableMovement();}
  else if(FVector::Dist2D(Person->GetActorLocation(),Spot)>30)Person->SetActorLocation(Spot);
 }
}
