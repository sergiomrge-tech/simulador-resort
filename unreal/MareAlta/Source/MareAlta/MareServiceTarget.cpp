#include "MareServiceTarget.h"
#include "MareFx.h"
#include "MareBoatTourWorld.h"
#include "MareSnorkelWorld.h"
#include "MareTrailWorld.h"
#include "MareRentalWorld.h"
#include "MareSummitWorld.h"
#include "MareComicEvents.h"
#include "MareStaysWorld.h"
#include "MareGameRoom.h"
#include "MareHotelEventsWorld.h"
#include "MarePlayerPresentation.h"
#include "MareHomeWorld.h"
#include "MareVillageWorld.h"
#include "MareGame.h"
#include "MareIntro.h"
#include "MareAudioWorld.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MarePerson.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "MareKioskWorld.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "EngineUtils.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

AMareServiceTarget::AMareServiceTarget()
{
 PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=.025f;
 RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("InteractionOrigin"));
 DoorMesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorLeaf"));DoorMesh->SetupAttachment(RootComponent);
 DoorMesh->SetMobility(EComponentMobility::Movable);
}
void AMareServiceTarget::BeginPlay()
{
 Super::BeginPlay();
 // The leaf is 220 cm high; the lintel starts at 247 cm and the pivot is 12 cm above ground.
 if(Action==TEXT("Door"))DoorMesh->SetRelativeScale3D(FVector(bAutoClose?1.04f:1.f,1.f,1.065f));
}
AMareServiceTarget* AMareServiceTarget::FindFocused(APlayerController* Controller)
{
 if(!Controller || !Controller->GetPawn())return nullptr;
 FVector Eye;FRotator View;Controller->GetPlayerViewPoint(Eye,View);const FVector Aim=View.Vector();
 AMareServiceTarget* Best=nullptr;float Score=FLT_MAX;
 for(TActorIterator<AMareServiceTarget> It(Controller->GetWorld());It;++It){auto Target=*It;
  if(Target->IsHidden() || (Target->GetOwner() && Target->GetOwner()->IsHidden()))continue;
  FVector Focus=Target->GetActorTransform().TransformPosition(Target->FocusOffset);
  // Select the visible leaf/mattress surface, not a single point hidden inside it.
  if((Target->Action==TEXT("Door") || Target->Action==TEXT("RoomDoor")) && Target->DoorMesh->GetStaticMesh()){
   const FTransform Frame=Target->DoorMesh->GetComponentTransform();
   const FBox Box=Target->DoorMesh->GetStaticMesh()->GetBoundingBox();
   const FVector Center=Frame.TransformPosition(Box.GetCenter());
   const FVector RayPoint=Eye+Aim*FMath::Max(0.f,FVector::DotProduct(Center-Eye,Aim));
   Focus=Frame.TransformPosition(Box.GetClosestPointTo(Frame.InverseTransformPosition(RayPoint)));
  }else if(Target->Action==TEXT("Bed")){
   const FBox Mattress(FVector(4330,1875,58),FVector(4465,2050,82));
   Focus=Mattress.GetClosestPointTo(Eye+Aim*FMath::Max(0.f,FVector::DotProduct(Mattress.GetCenter()-Eye,Aim)));
  }
  const FVector Delta=Focus-Eye;const float Distance=Delta.Size();if(Distance>Target->Reach || Distance<1)continue;
  const float Along=FVector::DotProduct(Delta,Aim);if(Along<=0)continue;
  const float Miss=(Delta-Aim*Along).Size();if(Miss>FMath::Max(25.f,Distance*.19f))continue;
  FHitResult Hit;FCollisionQueryParams Params;Params.AddIgnoredActor(Controller->GetPawn());Params.AddIgnoredActor(Target);
  if(Controller->GetWorld()->LineTraceSingleByChannel(Hit,Eye,Focus,ECC_Visibility,Params) && FVector::Distance(Hit.ImpactPoint,Focus)>Target->OcclusionTolerance)continue;
  const float Rank=Miss+Distance*.035f;if(Rank<Score){Score=Rank;Best=Target;}
 }
 return Best;
}
FString AMareServiceTarget::Prompt()const
{
 if(Action==TEXT("Door"))return Label+(bOpened?TEXT(" · fechar"):TEXT(" · abrir"));
 if(Action==TEXT("RoomDoor")){auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();
  if(!bOpened && Sim && Sim->HasRoomServiceTray(DataIndex))return Label+TEXT(" · bater e entregar o serviço de quarto");
  return Label+(bOpened?TEXT(" · fechar"):TEXT(" · abrir"));}
 if(Action==TEXT("KioskSign")){auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();bool Requested=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),Requested);return Requested?(Sim->IsOpen()?TEXT("Fechar quiosque"):TEXT("Abertura programada · cancelar")):TEXT("Abrir quiosque");}
 return Label;
}
void AMareServiceTarget::RestoreDoorState(bool bOpen)
{
 bOpened=bOpen;bWasInside=false;DoorAngle=bOpen?-90.f:0.f;
 DoorMesh->SetRelativeRotation(FRotator(0,DoorAngle,0));
 FocusOffset=FRotator(0,DoorAngle,0).RotateVector(FVector(-57.5,0,110));
}
bool AMareServiceTarget::CanClose(const FVector& PlayerLocation)const
{
 const FVector P=GetActorTransform().InverseTransformPosition(PlayerLocation);
 if(Action==TEXT("RoomDoor"))return !(P.X>-100 && P.X<15 && P.Y>-20 && P.Y<105);   // the hotel leaf sweeps 0.9 m into the room
 return !(P.X>-150 && P.X<40 && P.Y>-45 && P.Y<155);
}
void AMareServiceTarget::Use(APlayerController* Controller)
{
 // Reference tip 4 (08/11): a sparkle where something is cleaned, foam where a room or towel is tidied.
 {const FVector Focus=GetActorTransform().TransformPosition(FocusOffset);
  if(Action==TEXT("Clean") || Action==TEXT("PoolLeaves"))MareFx::Spawn(GetWorld(),Focus,MareFx::EKind::Sparkle);
  else if(Action==TEXT("RoomTask") || Action==TEXT("HotelTask") || Action==TEXT("PoolTowel") || Action==TEXT("HotelFix"))MareFx::Spawn(GetWorld(),Focus,MareFx::EKind::Foam);}
 auto PC=Cast<AMareController>(Controller);if(!PC)return;
 if(auto Presentation=PC->GetPawn()?PC->GetPawn()->FindComponentByClass<UMarePlayerPresentation>():nullptr)Presentation->ReachFor(GetActorTransform().TransformPosition(FocusOffset));
 auto Sim=PC->GetGameInstance()->GetSubsystem<UMareSimulation>();
 if(Action.ToString().StartsWith(TEXT("Home"))){GetWorld()->GetSubsystem<UMareHomeWorld>()->Use(Action);return;}
 // First-time tip of this kind of target (Content/Data/tutorial.json). The business counter's tips (one per business, 6.2) are shown by AMareController::StartBusinessGame (it also opens from QA).
 if(Sim && Action!=TEXT("BusinessCounter"))Sim->ShowTip(Action.ToString());
 if(Action==TEXT("IntroLetter")){if(auto Intro=Cast<AMareIntro>(GetOwner()))Intro->ReadLetter();return;}
 if(Action==TEXT("Resident")){GetWorld()->GetSubsystem<UMareVillageWorld>()->Speak(Cast<AMarePerson>(GetOwner()),Controller);return;}
 if(Action==TEXT("Elder")){if(auto Summit=GetWorld()->GetSubsystem<UMareSummitWorld>())Summit->Talk(Controller);return;}
 if(Action==TEXT("Comic")){if(auto Comic=GetWorld()->GetSubsystem<UMareComicEvents>())Comic->Interact(Controller);return;}
 if(Action==TEXT("KioskSign")){bool Requested=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),Requested);Sim->SetOpen(!Requested);return;}
 if(Action==TEXT("Fridge") || Action==TEXT("Cupboard")){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("kiosk_fridge"),.3f);
  // A restock box in hand: each E stores one unit (reference tip 7); otherwise the station opens.
  if(!Sim->RestockBoxDish().IsEmpty()){if(Sim->StoreFromBox(Action))MareFx::Spawn(GetWorld(),GetActorTransform().TransformPosition(FocusOffset),MareFx::EKind::Sparkle);return;}
  PC->OpenStation(Action);return;}
 if(Action==TEXT("Customer")){if(auto Person=Cast<AMarePerson>(GetOwner()))Person->Interact(PC);return;}
 if(Action==TEXT("Clean")){GetWorld()->GetSubsystem<UMareKioskWorld>()->CleanTable(DataIndex);GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("clean"),.3f);return;}
 if(Action==TEXT("Bed")){GetWorld()->GetSubsystem<UMareHomeWorld>()->StartSleep();return;}
 if(Action==TEXT("Elevator")){
  // Grand Hotel elevator between the lobby and the suite on the 3rd floor.
  if(auto Pawn=PC->GetPawn()){Pawn->SetActorLocation(TeleportTo,false,nullptr,ETeleportType::TeleportPhysics);PC->SetControlRotation(FRotator(0,TeleportYaw,0));}
  const FVector Spot=TeleportTo;GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("door"),.3f,&Spot);
  Sim->LastMessage=DataIndex==1?TEXT("Suíte do Grand Hotel · 3º andar"):DataIndex==2?TEXT("Andar dos quartos 302 e 303 · 3º andar"):TEXT("Lobby do Grand Hotel");return;}
 if(Action==TEXT("PousadaReception")){const FVector Bell=GetActorLocation();UMareAudioWorld::Action(this,TEXT("reception_bell"),&Bell);PC->OpenStation(TEXT("Reception"));return;}
 // The table page: opponents, friendly or betting match, the Campeonato da Maré and the record (MareGame.cpp PoolPage).
 if(Action==TEXT("PoolTable")){PC->OpenStation(TEXT("PoolTable"));return;}
 if(Action==TEXT("TableTennis")){PC->OpenStation(TEXT("TableTennis"));return;}
 if(Action==TEXT("RoomTask")){for(const FName& Tag:Tags){const FString T=Tag.ToString();
   if(T.StartsWith(TEXT("task:")))GetWorld()->GetSubsystem<UMareStaysWorld>()->UseTask(DataIndex,T.Mid(5));}return;}
 if(Action==TEXT("HotelTask") || Action==TEXT("HotelFix")){auto Stays=GetWorld()->GetSubsystem<UMareStaysWorld>();
  for(const FName& Tag:Tags){const FString T=Tag.ToString();
   if(T.StartsWith(TEXT("task:")))Stays->UseHotelTask(DataIndex,T.Mid(5));else if(T.StartsWith(TEXT("fix:")))Stays->UseHotelFix(T.Mid(4));}return;}
 if(Action==TEXT("PoolLeaves")){if(Sim->ScoopPool())UMareAudioWorld::Action(this,TEXT("bar_pour"));return;}
 if(Action==TEXT("PoolTowel")){if(Sim->CollectPoolTowel(DataIndex))UMareAudioWorld::Action(this,TEXT("cleaning_towels"));return;}
 if(Action==TEXT("PoolCooler")){if(Sim->SellPopsicles())UMareAudioWorld::Action(this,TEXT("money_coins"));return;}
 if(Action==TEXT("EventPiece")){GetWorld()->GetSubsystem<UMareHotelEventsWorld>()->Place(DataIndex);return;}
 if(Action==TEXT("BusinessCounter")){for(const FName& Tag:Tags){const FString T=Tag.ToString();if(T.StartsWith(TEXT("biz:")))PC->StartBusinessGame(T.Mid(4));}return;}
 if(Action==TEXT("TourBooth")){const FVector Bell=GetActorLocation();UMareAudioWorld::Action(this,TEXT("reception_bell"),&Bell);PC->OpenStation(TEXT("Tours"));return;}
 if(Action==TEXT("RestaurantTable")){if(Sim->UseTable(DataIndex))UMareAudioWorld::Action(this,TEXT("reception_checkin"));return;}
 if(Action==TEXT("RestaurantPass")){if(Sim->PickUpPass()>0)UMareAudioWorld::Action(this,TEXT("bar_ice_glass"));PC->OpenStation(TEXT("Restaurant"));return;}
 if(Action==TEXT("RoomService")){if(Sim->DeliverRoomService(-1)>0)UMareAudioWorld::Action(this,TEXT("money_coins"));return;}
 if(Action==TEXT("Fishing")){PC->StartFishing();return;}
 if(Action==TEXT("BarCounter")){PC->OpenStation(TEXT("Bar"));return;}
 if(Action==TEXT("BarIngredient")){for(const FName& Tag:Tags){const FString T=Tag.ToString();
   // No hands (Sergio, 04/11): E on the shelf item drops it straight into the work glass.
   if(T.StartsWith(TEXT("ing:")) && Sim->BarPick(T.Mid(4)) && Sim->BarPour()){const FVector Spot=GetActorLocation();
    UMareAudioWorld::Action(this,T.Mid(4)==TEXT("gelo")?TEXT("bar_ice_glass"):TEXT("bar_pour"),&Spot,.7f);}}return;}
 if(Action==TEXT("BarGlass")){PC->UseBarGlass();return;}
 if(Action==TEXT("TourVest")){if(auto Tour=GetWorld()->GetSubsystem<UMareBoatTourWorld>())Tour->GiveVest(DataIndex);return;}
 if(Action==TEXT("RentalTow")){if(auto W=GetWorld()->GetSubsystem<UMareRentalWorld>())W->Tow();return;}
 if(Action==TEXT("TrailWater")){if(auto Tour=GetWorld()->GetSubsystem<UMareTrailWorld>())Tour->GiveWater(DataIndex);return;}
 if(Action==TEXT("TrailStory")){if(auto Tour=GetWorld()->GetSubsystem<UMareTrailWorld>())Tour->TellStory(DataIndex);return;}
 if(Action==TEXT("TourSpecies")){if(auto Tour=GetWorld()->GetSubsystem<UMareSnorkelWorld>())Tour->Present(DataIndex);return;}
 if(Action==TEXT("TourStory")){if(auto Tour=GetWorld()->GetSubsystem<UMareBoatTourWorld>())Tour->TellStory();return;}
 if(Action==TEXT("HotelReception")){const FVector Bell=GetActorLocation();UMareAudioWorld::Action(this,TEXT("reception_bell"),&Bell);PC->OpenStation(TEXT("ReceptionHotel"));return;}
 // C16 (reference tip 11): with a room-service tray ready, knocking on 302 brings the guest to the door: it opens,
 // the guest steps into the doorway, takes the tray (gesture) and pays; then goes back in, the door stays open.
 if(Action==TEXT("RoomDoor") && !bOpened && Sim->HasRoomServiceTray(DataIndex)){
  bOpened=true;const FVector Spot=GetActorLocation();GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("door"),.24f,&Spot);
  const FVector Doorway=GetActorTransform().TransformPosition(FVector(-45.f*DoorMesh->GetRelativeScale3D().X,0,0))-GetActorRightVector()*0.f;
  FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  const FVector Inside=Doorway+FVector(0,-55,90);   // just inside the room (the room is to the south, -Y)
  if(auto Guest=GetWorld()->SpawnActor<AMarePerson>(Inside,FRotator(0,90,0),SP)){Guest->PersonName=FString::Printf(TEXT("Hóspede do %d"),DataIndex);Guest->SaveId=FString::Printf(TEXT("room%d_guest"),DataIndex);
   Guest->Tags.Add(TEXT("MareHotelGuest"));Guest->bAmbient=true;Guest->SetAppearance(2);Guest->GetCharacterMovement()->DisableMovement();
   Guest->PlayGesture(TEXT("Interact"),2.4f);DoorGuest=Guest;GuestLeft=5.f;}
  if(Sim->DeliverRoomService(DataIndex)>0)UMareAudioWorld::Action(this,TEXT("money_coins"));
  return;}
 if(Action==TEXT("Door") || Action==TEXT("RoomDoor")){
  if(bOpened && !CanClose(PC->GetPawn()->GetActorLocation())){Sim->LastMessage=TEXT("Afaste-se do arco da porta para fechar.");return;}
  bOpened=!bOpened;
  const FVector Spot=GetActorLocation();GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("door"),.24f,&Spot);
 }
}
void AMareServiceTarget::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);if(Action!=TEXT("Door") && Action!=TEXT("RoomDoor"))return;
 if(Action==TEXT("RoomDoor")){
  // the guest of 302 waits behind a closed door while a room-service dish is on its way; after the hand-over they go in
  if(GuestLeft>0 && (GuestLeft-=DeltaSeconds)<=0 && DoorGuest.IsValid())DoorGuest->Destroy();
  auto Sim=GetGameInstance()->GetSubsystem<UMareSimulation>();auto Player=UGameplayStatics::GetPlayerPawn(this,0);
  if(bOpened && GuestLeft<=0 && Sim && Sim->HasRoomServiceTray(DataIndex) && Player && CanClose(Player->GetActorLocation()))bOpened=false;}
 const float Target=bOpened?-90.f:0.f;
 const bool bMoving=!FMath::IsNearlyEqual(DoorAngle,Target,.1f);
 DoorMesh->SetCollisionEnabled(bMoving?ECollisionEnabled::NoCollision:ECollisionEnabled::QueryAndPhysics);
 DoorAngle=FMath::FInterpConstantTo(DoorAngle,Target,DeltaSeconds,200.f);DoorMesh->SetRelativeRotation(FRotator(0,DoorAngle,0));
 FocusOffset=FRotator(0,DoorAngle,0).RotateVector(FVector(Action==TEXT("RoomDoor")?-45.f*DoorMesh->GetRelativeScale3D().X:-57.5f,0,110));
 if(!bAutoClose)return;auto Player=UGameplayStatics::GetPlayerPawn(this,0);if(!Player)return;
 const FVector P=GetActorTransform().InverseTransformPosition(Player->GetActorLocation());
 if(P.X>-580 && P.X<120 && P.Y>-700 && P.Y<-40)bWasInside=true;
 if(bWasInside && bOpened && !bMoving && P.Y>155 && CanClose(Player->GetActorLocation())){bOpened=false;bWasInside=false;}
}
