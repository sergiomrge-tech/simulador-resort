#include "MareRestaurantWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "Engine/StaticMesh.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

TStatId UMareRestaurantWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareRestaurantWorld,STATGROUP_Tickables);}

void UMareRestaurantWorld::Deinitialize()
{
 if(IsValid(Pass))Pass->Destroy();if(IsValid(RoomService))RoomService->Destroy();
 for(auto& D:RoomDoors)if(IsValid(D))D->Destroy();RoomDoors.Empty();
 for(auto& Pair:Tables)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Diners)if(IsValid(Pair.Value))Pair.Value->Destroy();
 Tables.Empty();Diners.Empty();Super::Deinitialize();
}

void UMareRestaurantWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || !GetWorld()->GetGameInstance())return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!S)return;
 bool bHotel=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
 const auto Defs=S->RestaurantDefs();
 auto Place=[this](const TSharedPtr<FJsonObject>& D,const TCHAR* Key,FName Action,const TCHAR* Label)->AMareServiceTarget*{
  const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!D->TryGetArrayField(Key,At) || At->Num()!=4)return nullptr;
  auto T=GetWorld()->SpawnActor<AMareServiceTarget>(FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber()),FRotator(0,(*At)[3]->AsNumber(),0));
  if(T){T->Action=Action;T->Label=Label;T->Reach=260;T->OcclusionTolerance=90;}return T;};
 if(bHotel && !Pass)Pass=Place(Defs,TEXT("pass"),TEXT("RestaurantPass"),TEXT("Passe da cozinha · pegar pratos prontos"));
 // 08/11 (reference tip 11, C16): room service goes to the guest's door on the 3rd floor, no longer to the elevator.
 // The leaves of 302 and 303 (tools/ue58/gen_hotel_door.py) hang in the corridor wall (gen_hotel_rooms.py: wall at
 // y 6720, openings centred on x -1364 (0.90 m) and -1116 (0.95 m), floor 854); hinge on the west edge, opening into
 // the room.
 if(bHotel && RoomDoors.IsEmpty())if(UStaticMesh* Leaf=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Custom/HotelRooms/mare_hotel_door/mare_hotel_door.mare_hotel_door"))){   // i18n:skip
  const struct{float Centre,Width;int32 Room;}Doors[]={{-1364.f,90.f,302},{-1116.f,95.f,303}};
  for(const auto& D:Doors){FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   auto T=GetWorld()->SpawnActor<AMareServiceTarget>(FVector(D.Centre-D.Width*.5f,6720.f,854.f),FRotator(0,180,0),SP);if(!T)continue;
   T->Action=TEXT("RoomDoor");T->DataIndex=D.Room;T->Label=FString::Printf(TEXT("Quarto %d"),D.Room);T->Reach=240;T->OcclusionTolerance=80;
   T->DoorMesh->SetStaticMesh(Leaf);T->DoorMesh->SetRelativeScale3D(FVector(D.Width/90.f,1,1));T->RestoreDoorState(true);RoomDoors.Add(T);}}
 for(auto& D:RoomDoors)if(IsValid(D)){D->SetActorHiddenInGame(!bHotel);D->SetActorEnableCollision(bHotel);}
 if(bHotel && !RoomService)RoomService=Place(Defs,TEXT("room_service"),TEXT("RoomService"),TEXT("Serviço de quarto · entregar no elevador (outros andares)"));
 if(Pass)Pass->SetActorHiddenInGame(!bHotel);if(RoomService)RoomService->SetActorHiddenInGame(!bHotel);
 // Tables: target label follows the order's stage; the three tables without decorative diners get a seated guest.
 static const TSet<int32> Decorated={0,3,4};   // MareVillageWorld seats ambient hotel guests at these tables (seat 0, and 1 on 0/3)
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(!Defs->TryGetArrayField(TEXT("tables"),List))return;
 for(int32 I=0;I<List->Num();++I){const auto& V=(*List)[I]->AsArray();const FVector Table(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber());
  const auto Order=bHotel?S->TableOrder(I):nullptr;AMareServiceTarget* Target=Tables.FindRef(I);
  if(Order && !Target){Target=GetWorld()->SpawnActor<AMareServiceTarget>(Table+FVector(0,0,80),FRotator::ZeroRotator);
   if(Target){Target->Action=TEXT("RestaurantTable");Target->DataIndex=I;Target->Reach=230;Target->OcclusionTolerance=90;Tables.Add(I,Target);}}
  if(!Order && Target){Target->Destroy();Tables.Remove(I);Target=nullptr;}
  if(Target){const FString Stage=UMareSimulation::String(Order,TEXT("stage")),Name=UMareSimulation::String(Order,TEXT("name"));
   const FString Dish=UMareSimulation::String(S->MenuDish(UMareSimulation::String(Order,TEXT("dish"))),TEXT("name"));
   Target->Label=Stage==TEXT("order")?TEXT("Anotar o pedido · ")+Name:Stage==TEXT("tray")?TEXT("Servir ")+Dish+TEXT(" · ")+Name:TEXT("Na cozinha: ")+Dish;}
  AMarePerson* Diner=Diners.FindRef(I);
  if(Order && !Decorated.Contains(I) && !IsValid(Diner)){
   FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   // On the table's first real chair (hotel_seats.json), like the decorative diners; old offset only as a fallback.
   FVector Seat=Table+FVector(-11,52,39);float Yaw=-90;AMarePerson::HotelSeat(I,0,Seat,Yaw);
   Diner=GetWorld()->SpawnActor<AMarePerson>(Seat+FVector(0,0,60),FRotator(0,Yaw,0),Params);if(Diner)Diner->SitOn(Seat,Yaw);
   if(Diner){Diner->SaveId=FString::Printf(TEXT("restaurant_%d_%s"),I,*UMareSimulation::String(Order,TEXT("name")));Diner->PersonName=UMareSimulation::String(Order,TEXT("name"));
    Diner->Tags.Add(TEXT("MareHotelGuest"));Diner->bAmbient=true;Diner->bSeated=true;Diner->SetAppearance(I%4);
    Diner->GetCharacterMovement()->DisableMovement();Diner->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Diners.Add(I,Diner);}}
  else if(!Order && IsValid(Diner)){Diner->Destroy();Diners.Remove(I);}
 }
}
