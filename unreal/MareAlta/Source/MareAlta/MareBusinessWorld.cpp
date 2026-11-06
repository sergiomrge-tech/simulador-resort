#include "MareBusinessWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"

TStatId UMareBusinessWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareBusinessWorld,STATGROUP_Tickables);}

void UMareBusinessWorld::Deinitialize()
{
 for(auto& Pair:Counters)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Waiting)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& P:IceLine)if(IsValid(P))P->Destroy();IceLine.Empty();for(auto& P:PastelLine)if(IsValid(P))P->Destroy();PastelLine.Empty();
 for(auto& M:Machines)if(IsValid(M))M->Destroy();for(auto& P:NightPlayers)if(IsValid(P))P->Destroy();
 Counters.Empty();Waiting.Empty();Machines.Empty();NightPlayers.Empty();Super::Deinitialize();
}

void UMareBusinessWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || !GetWorld()->GetGameInstance())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 SyncGameRoom(S);
 auto Ground=[this](FVector At){FHitResult Hit;
  if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,300),At-FVector(0,0,600),ECC_Visibility))At.Z=Hit.ImpactPoint.Z;return At;};
 for(const auto& Pair:UMareSimulation::Object(S->BusinessGames(),TEXT("businesses"))->Values){
  const FString Id(Pair.Key.ToView());const auto Def=Pair.Value->AsObject();const FString Requires=UMareSimulation::String(Def,TEXT("requires"));
  bool bOwned=false;if(Requires.IsEmpty())bOwned=S->OwnsBusiness(Id);else UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Requires,bOwned);
  const TArray<TSharedPtr<FJsonValue>>* C=nullptr;const TArray<TSharedPtr<FJsonValue>>* G=nullptr;
  if(!Def->TryGetArrayField(TEXT("counter"),C) || C->Num()!=4 || !Def->TryGetArrayField(TEXT("guest"),G) || G->Num()!=4)continue;
  AMareServiceTarget* Counter=Counters.FindRef(Id);
  if(!Counter && bOwned){
   const FVector At=Ground(FVector((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),0))+FVector(0,0,(*C)[2]->AsNumber());
   Counter=GetWorld()->SpawnActor<AMareServiceTarget>(At,FRotator(0,(*C)[3]->AsNumber(),0));
   Counter->Action=TEXT("BusinessCounter");Counter->Tags.Add(*(TEXT("biz:")+Id));Counter->Reach=260;Counter->OcclusionTolerance=90;
   Counter->Label=Requires.IsEmpty()?UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("businesses")),Id),TEXT("name"))
    :UMareSimulation::String(Def,TEXT("title"));
   Counters.Add(Id,Counter);}
  if(Counter)Counter->SetActorHiddenInGame(!bOwned);
  // A customer waits at the counter while this hour's task is available.
  // The souvenir shop always opens for managing; a tourist waits at its counter only while someone wants a gift wrapped.
  FString Reason;const bool bDue=bOwned && S->CanPlayBusiness(Id,Reason) && (Id!=TEXT("souvenir") || S->SouvenirQueue().Num()>0);AMarePerson* Guest=Waiting.FindRef(Id);
  if(bDue && !IsValid(Guest)){
   FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
   const FVector At=Ground(FVector((*G)[0]->AsNumber(),(*G)[1]->AsNumber(),0))+FVector(0,0,90);
   Guest=GetWorld()->SpawnActor<AMarePerson>(At,FRotator(0,(*G)[3]->AsNumber(),0),Params);
   if(Guest){const int32 Hour=int32(UMareSimulation::Number(S->State,TEXT("day"),1))*24+FMath::FloorToInt(UMareSimulation::Number(S->State,TEXT("minutes"))/60);
    Guest->SaveId=FString::Printf(TEXT("biz_%s_%d"),*Id,Hour);Guest->PersonName=TEXT("Cliente");Guest->SetAppearance(FCrc::StrCrc32(*Guest->SaveId)%4);
    Guest->bAmbient=true;Guest->GetCharacterMovement()->DisableMovement();Waiting.Add(Id,Guest);}}
  else if(!bDue && IsValid(Guest)){Guest->Destroy();Waiting.Remove(Id);}
  // The ice cream queue: the rest of the line stands behind the first customer, one step apart.
  if(Id==TEXT("sorveteria") || Id==TEXT("food_truck")){auto& Line=Id==TEXT("sorveteria")?IceLine:PastelLine;
   const int32 Want=bDue?FMath::Clamp((Id==TEXT("sorveteria")?S->IceQueue().Num():S->PastelQueue().Num())-1,0,3):0;
   while(Line.Num()>Want){if(IsValid(Line.Last()))Line.Last()->Destroy();Line.Pop();}
   // The line goes behind the first customer, or to a side when a wall or a drop is there (the pastel truck stands
   // with a facade right behind its customer): every place must be on the same ground and reachable at chest height.
   const FRotator Face(0,(*G)[3]->AsNumber(),0);const FVector First=Ground(FVector((*G)[0]->AsNumber(),(*G)[1]->AsNumber(),0));
   FVector Dir=-Face.Vector();
   for(const FVector& Try:{-Face.Vector(),FRotationMatrix(Face).GetUnitAxis(EAxis::Y),-FRotationMatrix(Face).GetUnitAxis(EAxis::Y)}){bool bFree=true;
    for(int32 K=1;K<=3 && bFree;++K){const FVector P=Ground(First+Try*95.f*K);FHitResult Hit;
     bFree=FMath::Abs(P.Z-First.Z)<40 && !GetWorld()->SweepSingleByChannel(Hit,First+FVector(0,0,120),P+FVector(0,0,120),FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(25));}
    if(bFree){Dir=Try;break;}}
   for(int32 I=Line.Num();I<Want;++I){
    const FVector At=Ground(First+Dir*(95.f*(I+1)))+FVector(0,0,90);
    FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
    if(auto P=GetWorld()->SpawnActor<AMarePerson>(At,Face,Params)){P->SaveId=FString::Printf(TEXT("%s_line_%d_%d"),*Id,I,int32(UMareSimulation::Number(S->State,TEXT("day"),1)));
     P->PersonName=TEXT("Cliente");P->SetAppearance(FCrc::StrCrc32(*P->SaveId)%4);P->bAmbient=true;P->GetCharacterMovement()->DisableMovement();Line.Add(P);}}}
 }
}

void UMareBusinessWorld::SyncGameRoom(UMareSimulation* S)
{
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("salao_jogos"),bOwned);
 const auto Room=UMareSimulation::Object(S->BusinessGames(),TEXT("game_room"));
 auto Read=[](const TArray<TSharedPtr<FJsonValue>>& V){return FTransform(FRotator(0,V[3]->AsNumber(),0),FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber()));};
 TArray<FTransform> Arcades;FTransform Foosball;bool bFoosball=false;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Room->TryGetArrayField(TEXT("foosball"),List) && List->Num()==4){Foosball=Read(*List);bFoosball=true;}
 if(Room->TryGetArrayField(TEXT("arcades"),List))for(const auto& V:*List)if(V->AsArray().Num()==4)Arcades.Add(Read(V->AsArray()));
 if(bOwned && Machines.IsEmpty()){
  auto Place=[this](const TCHAR* Path,const FTransform& T){if(auto Mesh=LoadObject<UStaticMesh>(nullptr,Path)){
   auto A=GetWorld()->SpawnActor<AStaticMeshActor>(T.GetLocation(),T.Rotator());A->SetMobility(EComponentMobility::Movable);A->GetStaticMeshComponent()->SetStaticMesh(Mesh);Machines.Add(A);}};
  if(bFoosball)Place(TEXT("/Game/Custom/GameRoom/foosball_table/foosball_table.foosball_table"),Foosball);
  for(const FTransform& T:Arcades)Place(TEXT("/Game/Custom/GameRoom/arcade_cabinet/arcade_cabinet.arcade_cabinet"),T);}
 for(auto& M:Machines)if(IsValid(M)){M->SetActorHiddenInGame(!bOwned);M->SetActorEnableCollision(bOwned);}
 // Night: guests on both sides of the foosball and in front of each arcade during the token hours.
 const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const double Hour=UMareSimulation::Number(S->State,TEXT("minutes"))/60;
 const bool bNight=bOwned && Room->TryGetArrayField(TEXT("token_hours"),Hours) && Hours->Num()==2 && Hour>=(*Hours)[0]->AsNumber() && Hour<(*Hours)[1]->AsNumber();
 if(bNight && NightPlayers.IsEmpty()){
  TArray<FTransform> Spots;
  if(bFoosball)for(const float Side:{-1.f,1.f})Spots.Add(FTransform(FRotator(0,Foosball.Rotator().Yaw+(Side<0?90:-90),0),Foosball.TransformPosition(FVector(0,Side*70,88))));
  for(const FTransform& T:Arcades)Spots.Add(FTransform(T.Rotator(),T.TransformPosition(FVector(0,75,88))));
  for(int32 I=0;I<Spots.Num();++I){FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   // Arcade players face the screen: the cabinet front is +Y in the model, so they look back along -Y.
   const FRotator Face=I>=2 || !bFoosball?Spots[I].Rotator()+FRotator(0,-90,0):Spots[I].Rotator();
   if(auto P=GetWorld()->SpawnActor<AMarePerson>(Spots[I].GetLocation(),Face,Params)){P->SaveId=FString::Printf(TEXT("gameroom_night_%d"),I);P->PersonName=TEXT("Hóspede");
    P->Tags.Add(TEXT("MareHotelGuest"));P->bAmbient=true;P->bConversing=true;P->SetAppearance(I%4);P->GetCharacterMovement()->DisableMovement();NightPlayers.Add(P);}}}
 else if(!bNight && NightPlayers.Num()){for(auto& P:NightPlayers)if(IsValid(P))P->Destroy();NightPlayers.Empty();}
}
