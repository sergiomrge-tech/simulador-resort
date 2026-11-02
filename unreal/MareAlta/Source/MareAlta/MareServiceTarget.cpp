#include "MareServiceTarget.h"
#include "MareStaysWorld.h"
#include "MareGameRoom.h"
#include "MarePlayerPresentation.h"
#include "MareHomeWorld.h"
#include "MareVillageWorld.h"
#include "MareGame.h"
#include "MareIntro.h"
#include "MareAudioWorld.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MarePerson.h"
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
  if(Target->Action==TEXT("Door") && Target->DoorMesh->GetStaticMesh()){
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
 return !(P.X>-150 && P.X<40 && P.Y>-45 && P.Y<155);
}
void AMareServiceTarget::Use(APlayerController* Controller)
{
 auto PC=Cast<AMareController>(Controller);if(!PC)return;
 if(auto Presentation=PC->GetPawn()?PC->GetPawn()->FindComponentByClass<UMarePlayerPresentation>():nullptr)Presentation->ReachFor(GetActorTransform().TransformPosition(FocusOffset));
 auto Sim=PC->GetGameInstance()->GetSubsystem<UMareSimulation>();
 if(Action.ToString().StartsWith(TEXT("Home"))){GetWorld()->GetSubsystem<UMareHomeWorld>()->Use(Action);return;}
 if(Action==TEXT("IntroLetter")){if(auto Intro=Cast<AMareIntro>(GetOwner()))Intro->ReadLetter();return;}
 if(Action==TEXT("Resident")){GetWorld()->GetSubsystem<UMareVillageWorld>()->Speak(Cast<AMarePerson>(GetOwner()),Controller);return;}
 if(Action==TEXT("KioskSign")){bool Requested=false;UMareSimulation::Object(Sim->State,TEXT("company"))->TryGetBoolField(TEXT("kiosk_open"),Requested);Sim->SetOpen(!Requested);return;}
 if(Action==TEXT("Fridge") || Action==TEXT("Cupboard")){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("kiosk_fridge"),.3f);PC->OpenStation(Action);return;}
 if(Action==TEXT("Customer")){if(auto Person=Cast<AMarePerson>(GetOwner()))Person->Interact(PC);return;}
 if(Action==TEXT("Clean")){GetWorld()->GetSubsystem<UMareKioskWorld>()->CleanTable(DataIndex);GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("clean"),.3f);return;}
 if(Action==TEXT("Bed")){GetWorld()->GetSubsystem<UMareHomeWorld>()->StartSleep();return;}
 if(Action==TEXT("Elevator")){
  // Grand Hotel elevator between the lobby and the suite on the 3rd floor.
  if(auto Pawn=PC->GetPawn()){Pawn->SetActorLocation(TeleportTo,false,nullptr,ETeleportType::TeleportPhysics);PC->SetControlRotation(FRotator(0,TeleportYaw,0));}
  const FVector Spot=TeleportTo;GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("door"),.3f,&Spot);
  Sim->LastMessage=DataIndex==1?TEXT("Suíte do Grand Hotel · 3º andar"):TEXT("Lobby do Grand Hotel");return;}
 if(Action==TEXT("PousadaReception")){const FVector Bell=GetActorLocation();UMareAudioWorld::Action(this,TEXT("reception_bell"),&Bell);PC->OpenStation(TEXT("Reception"));return;}
 // Friendly match, or R$ 20 on the table once the cash allows it.
 if(Action==TEXT("PoolTable")){GetWorld()->GetSubsystem<UMareGameRoom>()->StartMatch(PC,Sim->Money()>=100?20:0);return;}
 if(Action==TEXT("RoomTask")){for(const FName& Tag:Tags){const FString T=Tag.ToString();
   if(T.StartsWith(TEXT("task:")))GetWorld()->GetSubsystem<UMareStaysWorld>()->UseTask(DataIndex,T.Mid(5));}return;}
 if(Action==TEXT("PoolLeaves")){if(Sim->ScoopPool())UMareAudioWorld::Action(this,TEXT("bar_pour"));return;}
 if(Action==TEXT("PoolTowel")){if(Sim->CollectPoolTowel(DataIndex))UMareAudioWorld::Action(this,TEXT("cleaning_towels"));return;}
 if(Action==TEXT("PoolCooler")){if(Sim->SellPopsicles())UMareAudioWorld::Action(this,TEXT("money_coins"));return;}
 if(Action==TEXT("BusinessCounter")){for(const FName& Tag:Tags){const FString T=Tag.ToString();if(T.StartsWith(TEXT("biz:")))PC->StartBusinessGame(T.Mid(4));}return;}
 if(Action==TEXT("BarCounter")){PC->OpenStation(TEXT("Bar"));return;}
 if(Action==TEXT("HotelReception")){const FVector Bell=GetActorLocation();UMareAudioWorld::Action(this,TEXT("reception_bell"),&Bell);PC->OpenStation(TEXT("ReceptionHotel"));return;}
 if(Action==TEXT("Door")){
  if(bOpened && !CanClose(PC->GetPawn()->GetActorLocation())){Sim->LastMessage=TEXT("Afaste-se do arco da porta para fechar.");return;}
  bOpened=!bOpened;
  const FVector Spot=GetActorLocation();GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("door"),.24f,&Spot);
 }
}
void AMareServiceTarget::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);if(Action!=TEXT("Door"))return;
 const float Target=bOpened?-90.f:0.f;
 const bool bMoving=!FMath::IsNearlyEqual(DoorAngle,Target,.1f);
 DoorMesh->SetCollisionEnabled(bMoving?ECollisionEnabled::NoCollision:ECollisionEnabled::QueryAndPhysics);
 DoorAngle=FMath::FInterpConstantTo(DoorAngle,Target,DeltaSeconds,200.f);DoorMesh->SetRelativeRotation(FRotator(0,DoorAngle,0));
 FocusOffset=FRotator(0,DoorAngle,0).RotateVector(FVector(-57.5,0,110));
 if(!bAutoClose)return;auto Player=UGameplayStatics::GetPlayerPawn(this,0);if(!Player)return;
 const FVector P=GetActorTransform().InverseTransformPosition(Player->GetActorLocation());
 if(P.X>-580 && P.X<120 && P.Y>-700 && P.Y<-40)bWasInside=true;
 if(bWasInside && bOpened && !bMoving && P.Y>155 && CanClose(Player->GetActorLocation())){bOpened=false;bWasInside=false;}
}
