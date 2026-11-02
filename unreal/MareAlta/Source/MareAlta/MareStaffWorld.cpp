#include "MareStaffWorld.h"
#include "MareSimulation.h"
#include "MarePerson.h"
#include "AIController.h"
#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 UMareSimulation* Sim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 TSharedPtr<FJsonObject> StaffDefs()
 {
  static TSharedPtr<FJsonObject> Defs;
  if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/staff_world.json")));
   FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
  return Defs;
 }
 constexpr float GlideSpeed=120.f;
}

TStatId UMareStaffWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareStaffWorld,STATGROUP_Tickables);}

void UMareStaffWorld::Deinitialize()
{
 for(auto& Pair:Workers)if(Pair.Value.Person.IsValid())Pair.Value.Person->Destroy();
 Workers.Empty();Super::Deinitialize();
}

AMarePerson* UMareStaffWorld::Worker(const FString& Role) const{const FWorker* W=Workers.Find(Role);return W?W->Person.Get():nullptr;}

FString UMareStaffWorld::Activity(const FString& Role) const
{
 const FWorker* W=Workers.Find(Role);if(!W || !W->Person.IsValid() || W->Route.IsEmpty())return FString();
 if(W->bMoving)return W->Route[W->Next].Label.IsEmpty()?TEXT("a caminho"):TEXT("a caminho: ")+W->Route[W->Next].Label.ToLower();
 const int32 At=(W->Next+W->Route.Num()-1)%W->Route.Num();return W->Route[At].Label;
}

FVector UMareStaffWorld::Ground(const FVector& At) const
{
 FHitResult Hit;FCollisionQueryParams Params(TEXT("MareStaffGround"),false);
 FCollisionObjectQueryParams Static(ECC_WorldStatic);
 if(GetWorld()->LineTraceSingleByObjectType(Hit,At+FVector(0,0,150),At-FVector(0,0,1200),Static,Params))return Hit.ImpactPoint;
 return At;
}

TArray<UMareStaffWorld::FStop> UMareStaffWorld::RouteFor(const FString& Role,const TSharedPtr<FJsonObject>& Def) const
{
 TArray<FStop> Route;auto S=Sim(GetWorld());
 auto Read=[&](const TSharedPtr<FJsonObject>& O,FStop& Out){
  Out.Pose=UMareSimulation::String(O,TEXT("pose"));Out.Label=UMareSimulation::String(O,TEXT("label"));
  Out.Carry=UMareSimulation::String(O,TEXT("carry"));O->TryGetBoolField(TEXT("drop"),Out.bDrop);
  Out.Seconds=UMareSimulation::Number(O,TEXT("seconds"),4);Out.Yaw=UMareSimulation::Number(O,TEXT("yaw"));};
 const FString Kind=UMareSimulation::String(Def,TEXT("route"));
 if(Kind==TEXT("bungalows")){
  // The maid goes along the rented bungalows (room i is the i-th from the east, as in UMareStaysWorld).
  TArray<AActor*> Bungalows;for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareBungalow")))Bungalows.Add(*It);
  Bungalows.Sort([](const AActor& A,const AActor& B){return A.GetActorLocation().X>B.GetActorLocation().X;});
  const int32 Rooms=S?FMath::Min(S->PousadaRooms(),Bungalows.Num()):0;
  const TArray<TSharedPtr<FJsonValue>>* Deck=nullptr;FVector Local(0,260,49);
  if(Def->TryGetArrayField(TEXT("deck"),Deck) && Deck->Num()==3)Local=FVector((*Deck)[0]->AsNumber(),(*Deck)[1]->AsNumber(),(*Deck)[2]->AsNumber());
  for(int32 I=0;I<Rooms;++I){FStop Stop;Read(Def,Stop);
   Stop.At=Ground(Bungalows[I]->GetActorTransform().TransformPosition(Local));
   Stop.Yaw=Bungalows[I]->GetActorRotation().Yaw-90;Stop.Label=FString::Printf(TEXT("Arrumando o bangalô %d"),I+1);Route.Add(Stop);}
  return Route;}
 if(Kind==TEXT("reception")){
  // Behind a counter given as [x, y, z, yaw] (the yaw faces the guests), e.g. customization.json operations.pousada.reception.
  const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
  auto Ops=UMareSimulation::Object(UMareSimulation::Object(S?S->CustomDefs():MakeShared<FJsonObject>(),TEXT("operations")),UMareSimulation::String(Def,TEXT("place")));
  if(Ops->TryGetArrayField(TEXT("reception"),At) && At->Num()==4){FStop Stop;Read(Def,Stop);
   const FRotator Face(0,(*At)[3]->AsNumber(),0);
   Stop.At=Ground(FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber())-Face.Vector()*UMareSimulation::Number(Def,TEXT("behind"),90));
   Stop.Yaw=Face.Yaw;Route.Add(Stop);}
  return Route;}
 const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;
 if(Def->TryGetArrayField(TEXT("stops"),Stops))for(const auto& V:*Stops){const auto O=V->AsObject();const TArray<TSharedPtr<FJsonValue>>* At=nullptr;
  if(!O.IsValid() || !O->TryGetArrayField(TEXT("at"),At) || At->Num()<2)continue;
  FStop Stop;Read(O,Stop);Stop.At=Ground(FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),At->Num()>2?(*At)[2]->AsNumber():0));Route.Add(Stop);}
 return Route;
}

void UMareStaffWorld::Spawn(const FString& Role,FWorker& W)
{
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 const FStop& First=W.Route[0];
 auto Person=GetWorld()->SpawnActor<AMarePerson>(First.At+FVector(0,0,90),FRotator(0,First.Yaw,0),Params);if(!Person)return;
 auto S=Sim(GetWorld());
 Person->SaveId=TEXT("staff_")+Role;Person->bEmployee=true;Person->bAmbient=true;Person->StaffRole=Role;
 Person->PersonName=S?UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(S->Definitions,TEXT("staff")),Role),TEXT("name")):Role;
 Person->Tags.Add(TEXT("MareStaff"));
 W.Person=Person;W.Next=W.Route.Num()>1?1:0;W.Wait=First.Seconds;W.bMoving=false;Person->WorkPose=First.Pose;
}

void UMareStaffWorld::Step(FWorker& W,float DeltaSeconds)
{
 AMarePerson* P=W.Person.Get();if(!P || W.Route.IsEmpty())return;
 const FStop& Goal=W.Route[W.Next];
 if(!W.bMoving){
  W.Wait-=DeltaSeconds;if(W.Wait>0 || W.Route.Num()<2)return;
  // Leave the stop: pick up what this leg carries, then walk on the navmesh or glide in a straight line.
  const FStop& Here=W.Route[(W.Next+W.Route.Num()-1)%W.Route.Num()];
  if(!Here.Carry.IsEmpty()){P->ClearProducts();P->HoldProduct(Here.Carry);}
  W.bMoving=true;W.Stuck=0;W.LastPos=P->GetActorLocation();P->WorkPose.Reset();
  W.bGlide=!P->WalkTo(Goal.At+FVector(0,0,90));
  if(W.bGlide){P->GetCharacterMovement()->DisableMovement();P->SetActorEnableCollision(false);P->WorkPose=TEXT("Walk");}
  return;}
 FVector Pos=P->GetActorLocation();const FVector Target=Goal.At+FVector(0,0,90);
 bool bArrived=false;
 if(W.bGlide){const FVector To=Target-Pos;const float Dist=To.Size2D();
  if(Dist<15){bArrived=true;}
  else{const FVector Dir=FVector(To.X,To.Y,0).GetSafeNormal();
   Pos+=Dir*FMath::Min(Dist,GlideSpeed*DeltaSeconds);
   // Ground under the feet, traced from knee height: tracing from above the head climbed onto roofs and canopies.
   FHitResult Hit;FCollisionObjectQueryParams Static(ECC_WorldStatic);
   if(GetWorld()->LineTraceSingleByObjectType(Hit,Pos-FVector(0,0,40),Pos-FVector(0,0,400),Static))Pos.Z=FMath::FInterpTo(Pos.Z,Hit.ImpactPoint.Z+90,DeltaSeconds,6);
   P->SetActorLocation(Pos);P->SetActorRotation(FMath::RInterpTo(P->GetActorRotation(),Dir.Rotation(),DeltaSeconds,6));}}
 else{
  bArrived=P->AtGoal();
  // Path blocked or the navmesh does not reach (raised floors): finish this leg gliding.
  W.Stuck=FVector::Dist2D(Pos,W.LastPos)<2?W.Stuck+DeltaSeconds:0;W.LastPos=Pos;
  if(!bArrived && W.Stuck>3){if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();
   P->GetCharacterMovement()->DisableMovement();P->SetActorEnableCollision(false);W.bGlide=true;P->WorkPose=TEXT("Walk");}}
 if(!bArrived)return;
 if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();
 P->SetActorRotation(FRotator(0,Goal.Yaw,0));P->WorkPose=Goal.Pose;
 if(Goal.bDrop)P->ClearProducts();
 W.bMoving=false;W.Wait=Goal.Seconds;W.Next=(W.Next+1)%W.Route.Num();
}

void UMareStaffWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 for(auto& Pair:Workers)Step(Pair.Value,DeltaSeconds);
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=1.f;
 auto S=Sim(GetWorld());if(!S)return;
 const double Hour=UMareSimulation::Number(S->State,TEXT("minutes"))/60;
 const auto Roles=UMareSimulation::Object(StaffDefs(),TEXT("roles"));
 for(const auto& Pair:Roles->Values){const FString Role(Pair.Key.ToView());const auto Def=Pair.Value->AsObject();if(!Def.IsValid())continue;
  const FString Place=UMareSimulation::String(Def,TEXT("requires"));bool bOpen=Place.IsEmpty();
  if(!bOpen)UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(Place,bOpen);
  const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;bool bHours=true;
  if(Def->TryGetArrayField(TEXT("hours"),Hours) && Hours->Num()==2)bHours=Hour>=(*Hours)[0]->AsNumber() && Hour<(*Hours)[1]->AsNumber();
  const bool bWant=bOpen && bHours && S->HasStaff(Role);
  FWorker& W=Workers.FindOrAdd(Role);
  if(bWant && !W.Person.IsValid()){W.Route=RouteFor(Role,Def);if(W.Route.Num())Spawn(Role,W);}
  else if(!bWant && W.Person.IsValid()){W.Person->Destroy();W=FWorker();}}
}
