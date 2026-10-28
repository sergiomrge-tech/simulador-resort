#include "MareServiceTarget.h"
#include "MareGame.h"
#include "MareAudioWorld.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MarePerson.h"
#include "MareKioskWorld.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

AMareServiceTarget::AMareServiceTarget()
{
 PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=.025f;
 RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("InteractionOrigin"));
 DoorMesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorLeaf"));DoorMesh->SetupAttachment(RootComponent);
 DoorMesh->SetMobility(EComponentMobility::Movable);
}
AMareServiceTarget* AMareServiceTarget::FindFocused(APlayerController* Controller)
{
 if(!Controller || !Controller->GetPawn())return nullptr;
 FVector Eye;FRotator View;Controller->GetPlayerViewPoint(Eye,View);const FVector Aim=View.Vector();
 AMareServiceTarget* Best=nullptr;float Score=FLT_MAX;
 for(TActorIterator<AMareServiceTarget> It(Controller->GetWorld());It;++It){auto Target=*It;
  if(Target->IsHidden() || (Target->GetOwner() && Target->GetOwner()->IsHidden()))continue;
  const FVector Focus=Target->GetActorTransform().TransformPosition(Target->FocusOffset);
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
 auto Sim=PC->GetGameInstance()->GetSubsystem<UMareSimulation>();
 if(Action==TEXT("Fridge") || Action==TEXT("Cupboard")){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("kiosk_fridge"),.3f);PC->OpenStation(Action);return;}
 if(Action==TEXT("Customer")){if(auto Person=Cast<AMarePerson>(GetOwner()))Person->Interact(PC);return;}
 if(Action==TEXT("Clean")){GetWorld()->GetSubsystem<UMareKioskWorld>()->CleanTable(DataIndex);GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("clean"),.3f);return;}
 if(Action==TEXT("Bed")){Sim->Sleep();return;}
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
