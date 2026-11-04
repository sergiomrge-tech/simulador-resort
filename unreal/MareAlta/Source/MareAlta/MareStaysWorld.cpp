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
  {TEXT("bed"),TEXT("/Game/Custom/RoomMess/mess_towel/mess_towel.mess_towel"),FVector(10,-40,108),25,10,TEXT("Arrumar a cama"),2.8f},
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
 Tasks.Empty();Mess.Empty();Guests.Empty();GuestPlace.Empty();Leaving.Empty();Super::Deinitialize();
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
 if(bPousada)SyncTasks();
 // Reception lines: the pousada counter (spawned above) and the Grand Hotel lobby desk (UMareVisualWorld spawns its
 // E target; the line only needs the data point). Guests leaving any line walk away and are removed on arrival.
 FMareStayLine Line;
 if(Desk && LineFor(S,TEXT("pousada"),Line)){
  // The pousada keeps its counter actor as reference; without an "exit" entry its guests go back down the path.
  if(!S->StayOps(TEXT("pousada"))->HasField(TEXT("exit")))Line.Exit=Desk->GetActorLocation()+Desk->GetActorForwardVector()*900;
  Line.Desk=Desk->GetActorLocation();Line.Front=Desk->GetActorForwardVector();SyncGuests(Line,bPousada);}
 bool bHotel=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
 if(LineFor(S,TEXT("hotel"),Line)){SyncGuests(Line,bHotel);if(bHotel)SyncDepartures(Line);}
 for(auto It=Leaving.CreateIterator();It;++It){AMarePerson* Person=It.Key();
  if(!IsValid(Person) || Person->AtGoal() || GetWorld()->GetTimeSeconds()>It.Value()){if(IsValid(Person))Person->Destroy();It.RemoveCurrent();}}
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
  UMareAudioWorld::Action(this,Task==TEXT("bed")?TEXT("cleaning_bed"):Task==TEXT("towels")?TEXT("cleaning_towels"):TEXT("cleaning_trash"));
  S->LastMessage=FString::Printf(TEXT("Bangalô %d: %s."),Room+1,Task==TEXT("bed")?TEXT("cama arrumada"):Task==TEXT("towels")?TEXT("toalhas recolhidas"):TEXT("lixo retirado"));
  SyncTasks();}
}

bool UMareStaysWorld::LineFor(const UMareSimulation* Simulation,const FString& Place,FMareStayLine& Out)
{
 if(!Simulation)return false;
 const auto Ops=Simulation->StayOps(Place);const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
 if(!Ops.IsValid() || !Ops->TryGetArrayField(TEXT("reception"),At) || At->Num()!=4)return false;
 auto Point=[](const TArray<TSharedPtr<FJsonValue>>& V){return FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber());};
 Out=FMareStayLine();Out.Place=Place;Out.Desk=Point(*At);Out.Front=FRotator(0,(*At)[3]->AsNumber(),0).Vector();
 const TArray<TSharedPtr<FJsonValue>>* Exit=nullptr;
 Out.Exit=Ops->TryGetArrayField(TEXT("exit"),Exit) && Exit->Num()==3?Point(*Exit):Out.Desk+Out.Front*900;
 const TArray<TSharedPtr<FJsonValue>>* Lifts=nullptr;
 if(Ops->TryGetArrayField(TEXT("elevators"),Lifts))for(const auto& V:*Lifts){const TArray<TSharedPtr<FJsonValue>>* P=nullptr;
  if(V->TryGetArray(P) && P->Num()==3)Out.Elevators.Add(Point(*P));}
 return true;
}

TArray<TSharedPtr<FJsonObject>> UMareStaysWorld::QueueOf(UMareSimulation* Simulation,const FString& Place)
{
 TArray<TSharedPtr<FJsonObject>> Line;const TArray<TSharedPtr<FJsonValue>>* Queue=nullptr;
 if(Simulation && Simulation->Stays()->TryGetArrayField(TEXT("queue"),Queue))for(const auto& V:*Queue){const FString P=UMareSimulation::String(V->AsObject(),TEXT("place"));
  if(P==Place || (P.IsEmpty() && Place==TEXT("pousada")))Line.Add(V->AsObject());}
 return Line;
}

void UMareStaysWorld::GuestExpress(const FString& Id,const FString& Mood,float Seconds)
{
 if(AMarePerson* Person=Guests.FindRef(Id))Person->Express(Mood,Seconds);
}

int32 UMareStaysWorld::LineCount(const FString& Place) const
{
 int32 Count=0;for(const auto& Pair:GuestPlace)Count+=Pair.Value==Place && IsValid(Guests.FindRef(Pair.Key));return Count;
}

FVector UMareStaysWorld::Ground(const FVector& At,const AActor* Ignore) const
{
 // Start only 1.5 m up: the hotel lobby ceiling is 4 m above its floor and must not be taken for the ground.
 FCollisionQueryParams Params(SCENE_QUERY_STAT(MareStaysGround),false,Ignore);
 for(const auto& Pair:Guests)if(IsValid(Pair.Value))Params.AddIgnoredActor(Pair.Value);
 FHitResult Hit;
 if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,150),At-FVector(0,0,600),ECC_Visibility,Params))return Hit.ImpactPoint;
 return At;
}

AMarePerson* UMareStaysWorld::SpawnGuest(const FString& Place,const FString& Id,const FString& Name,const FVector& Floor,const FRotator& Facing)
{
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
 auto Person=GetWorld()->SpawnActor<AMarePerson>(Floor+FVector(0,0,90),Facing,Params);if(!Person)return nullptr;
 Person->SaveId=Place+TEXT("_")+Id;Person->PersonName=Name;
 Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);Person->bAmbient=true;
 // The tag picks the MetaHuman cast (MarePerson: "hotel" / "pousada" rosters) before the first outfit tick.
 Person->Tags.Add(Place==TEXT("hotel")?TEXT("MareHotelGuest"):TEXT("MarePousadaGuest"));
 Person->GetCharacterMovement()->DisableMovement();return Person;
}

void UMareStaysWorld::Walk(AMarePerson* Person,const FVector& Goal,float Timeout)
{
 // WalkTo follows the navmesh, so guests go around the lobby furniture; without a path they vanish shortly.
 Person->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
 const bool bPath=Person->WalkTo(Goal);Leaving.Add(Person,GetWorld()->GetTimeSeconds()+(bPath?Timeout:3.f));
}

void UMareStaysWorld::SyncGuests(const FMareStayLine& Line,bool bOpen)
{
 auto S=Sim(GetWorld());if(!S)return;
 const TArray<TSharedPtr<FJsonObject>> Waiting=bOpen?QueueOf(S,Line.Place):TArray<TSharedPtr<FJsonObject>>();
 const bool bHotel=Line.Place==TEXT("hotel");
 // Guests who left the line walk away: after a check-in to their bungalow deck (pousada) or to the elevators (hotel),
 // otherwise out (pousada path, hotel main door). A locked place loses its people at once.
 for(auto It=Guests.CreateIterator();It;++It){const FString Id=It.Key();if(GuestPlace.FindRef(Id)!=Line.Place)continue;
  if(Waiting.ContainsByPredicate([&](const TSharedPtr<FJsonObject>& G){return UMareSimulation::String(G,TEXT("id"))==Id;}))continue;
  AMarePerson* Person=It.Value();It.RemoveCurrent();GuestPlace.Remove(Id);if(!IsValid(Person))continue;
  if(!bOpen){Person->Destroy();continue;}
  FVector Goal=Line.Exit;
  const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;int32 Bungalow=0;
  if(S->Stays()->TryGetArrayField(TEXT("rooms"),Rooms))for(const auto& V:*Rooms){const auto R=V->AsObject();
   const FString P=UMareSimulation::String(R,TEXT("place"));const bool bMine=P==Line.Place || (P.IsEmpty() && !bHotel);
   if(bMine && UMareSimulation::String(UMareSimulation::Object(R,TEXT("guest")),TEXT("id"))==Id){
    if(bHotel){if(Line.Elevators.Num())Goal=Line.Elevators[FCrc::StrCrc32(*Id)%uint32(Line.Elevators.Num())];}
    else RoomPoint(Bungalow,FVector(0,260,49),Goal);   // the bungalow deck
    break;}
   Bungalow+=bMine;}
  Walk(Person,Goal,bHotel?60.f:45.f);}
 // The line forms in front of the desk, one metre apart, everyone facing the counter, feet on the traced floor.
 const FRotator Facing=(-Line.Front).Rotation();
 for(int32 I=0;I<Waiting.Num();++I){
  const FString Id=UMareSimulation::String(Waiting[I],TEXT("id"));
  TObjectPtr<AMarePerson>& Person=Guests.FindOrAdd(Id);GuestPlace.Add(Id,Line.Place);
  if(!IsValid(Person)){Person=SpawnGuest(Line.Place,Id,UMareSimulation::String(Waiting[I],TEXT("name")),Ground(Line.Spot(I)),Facing);
   if(!Person){Guests.Remove(Id);GuestPlace.Remove(Id);}continue;}
  if(FVector::Dist2D(Person->GetActorLocation(),Line.Spot(I))>30){Person->SetActorLocation(Ground(Line.Spot(I),Person)+FVector(0,0,90));Person->SetActorRotation(Facing);}
 }
}

void UMareStaysWorld::SyncDepartures(const FMareStayLine& Line)
{
 // Check-outs walk out between 7:00 and 13:00, one every four seconds, from a lift door to the main door.
 auto S=Sim(GetWorld());if(!S || Line.Elevators.IsEmpty())return;
 const double Minutes=UMareSimulation::Number(S->State,TEXT("minutes"));
 if(Minutes<7*60 || Minutes>=13*60 || GetWorld()->GetTimeSeconds()<NextDeparture)return;
 const auto D=S->TakeDeparture(Line.Place);if(!D)return;
 NextDeparture=GetWorld()->GetTimeSeconds()+4;
 const FString Id=UMareSimulation::String(D,TEXT("id"));
 const FVector From=Line.Elevators[FCrc::StrCrc32(*Id)%uint32(Line.Elevators.Num())];
 if(auto Person=SpawnGuest(Line.Place,TEXT("out_")+Id,UMareSimulation::String(D,TEXT("name")),Ground(From),FRotator(0,(Line.Exit-From).Rotation().Yaw,0)))
  Walk(Person,Line.Exit,60.f);
}
