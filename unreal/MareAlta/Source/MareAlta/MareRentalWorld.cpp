// The rental's kayak adrift (CHECKLIST_EXPANSOES 3.3). Values in business_games.json businesses.aluguel.rental.
#include "MareRentalWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

namespace
{
 UMareSimulation* SimOf(const UWorld* W){return W && W->GetGameInstance()?W->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 FVector Vec(const TSharedPtr<FJsonObject>& O,const FString& Key,const FVector& Default=FVector::ZeroVector)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O.IsValid() || !O->TryGetArrayField(Key,A) || A->Num()<2)return Default;
  return FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),A->Num()>2?(*A)[2]->AsNumber():0);
 }
 FRotator FaceAlong(const FVector& F){return FRotationMatrix::MakeFromYZ(-F.GetSafeNormal(),FVector::UpVector).Rotator();}
}

TStatId UMareRentalWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareRentalWorld,STATGROUP_Tickables);}
bool UMareRentalWorld::IsActive()const{return IsValid(Kayak);}
void UMareRentalWorld::Deinitialize(){if(IsValid(Kayak))Kayak->Destroy();if(IsValid(Target))Target->Destroy();Super::Deinitialize();}

void UMareRentalWorld::Tow()
{
 if(!IsActive() || bTowed)return;bTowed=true;if(IsValid(Target))Target->SetActorHiddenInGame(true);
 if(auto S=SimOf(GetWorld()))S->LastMessage=TEXT("Rebocando o caiaque: nade até a areia em frente ao aluguel.");
 UMareAudioWorld::Action(this,TEXT("swim_splash"),nullptr,.6f);
}

void UMareRentalWorld::Tick(float DeltaSeconds)
{
 UWorld* World=GetWorld();if(!World || !World->IsGameWorld() || World->IsPaused())return;auto S=SimOf(World);if(!S)return;
 const auto D=S->RentalDefs();
 if(!S->IsKayakAdrift()){if(IsValid(Kayak))Kayak->Destroy();if(IsValid(Target))Target->Destroy();Kayak=nullptr;Target=nullptr;bTowed=false;return;}
 auto Pawn=UGameplayStatics::GetPlayerPawn(World,0);if(!Pawn)return;Time+=DeltaSeconds;
 if(!IsValid(Kayak)){
  // Off the beach in front of the rental, somewhere in the drift area (kept in the save while adrift).
  auto A=UMareSimulation::Object(S->RentalState(),TEXT("adrift"));const FVector Lo=Vec(D,TEXT("adrift_from"),FVector(5600,-6000,0)),Hi=Vec(D,TEXT("adrift_to"),FVector(6600,-5000,0));
  if(!A->HasField(TEXT("x"))){A->SetNumberField(TEXT("x"),FMath::FRandRange(Lo.X,Hi.X));A->SetNumberField(TEXT("y"),FMath::FRandRange(Lo.Y,Hi.Y));}
  Pos=FVector(UMareSimulation::Number(A,TEXT("x")),UMareSimulation::Number(A,TEXT("y")),0);Yaw=FMath::FRandRange(0.f,360.f);bTowed=false;
  auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(D,TEXT("kayak_mesh")));if(!Mesh)return;
  FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  Kayak=World->SpawnActor<AStaticMeshActor>(Pos,FRotator::ZeroRotator,P);if(!Kayak)return;Kayak->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
  Kayak->GetStaticMeshComponent()->SetStaticMesh(Mesh);Kayak->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Target=World->SpawnActor<AMareServiceTarget>(Pos,FRotator::ZeroRotator);
  if(Target){Target->Action=TEXT("RentalTow");Target->Label=TEXT("Rebocar o caiaque");Target->Reach=380;Target->OcclusionTolerance=120;}}
 // Simple physics: it rides the swell and slowly drifts offshore; in tow it follows the swimmer on a short line.
 const FVector H=Pawn->GetActorLocation();FVector Dir=FRotator(0,Yaw,0).Vector();
 if(bTowed){const FVector Want=H-Pawn->GetActorForwardVector().GetSafeNormal2D()*220.f;
  const FVector To=FVector(Want.X-Pos.X,Want.Y-Pos.Y,0);if(To.Size()>40){Pos+=To.GetClampedToMaxSize(FMath::Min(To.Size(),260.f*DeltaSeconds*FMath::Clamp(To.Size()/150.f,.3f,1.5f)));Dir=To.GetSafeNormal();
   Yaw=FMath::FixedTurn(Yaw,Dir.Rotation().Yaw,60.f*DeltaSeconds);}}
 else{Pos.Y-=UMareSimulation::Number(D,TEXT("drift_speed"),8)*DeltaSeconds;Yaw+=4.f*FMath::Sin(Time*.3f)*DeltaSeconds;}
 static UMaterialParameterCollection* MPC=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
 const float Storm=MPC?UKismetMaterialLibrary::GetScalarParameterValue(this,MPC,TEXT("Storm")):0.f;const float T=World->GetTimeSeconds();const FVector F=FRotator(0,Yaw,0).Vector(),R(-F.Y,F.X,0);
 // The model's origin is the stern: sample the swell along the hull.
 const FVector Mid=Pos+F*150;auto Sea=[&](const FVector& P){return AMarePerson::SeaHeight(FVector2D(P.X,P.Y),T,Storm);};
 const float Bow=Sea(Mid+F*140),Stern=Sea(Mid-F*140),Port=Sea(Mid-R*35),Star=Sea(Mid+R*35);
 const FRotator Base=FaceAlong(F);const float Z=UMareSimulation::Number(D,TEXT("sea_z"),-30)+(Bow+Stern+Port+Star)*.25f-12;
 Kayak->SetActorLocationAndRotation(FVector(Pos.X,Pos.Y,Z),FRotator(FMath::RadiansToDegrees(FMath::Atan2(Star-Port,70.f))*.6f,Base.Yaw,FMath::RadiansToDegrees(FMath::Atan2(Bow-Stern,280.f))));
 if(IsValid(Target))Target->SetActorLocation(FVector(Mid.X,Mid.Y,Z+40));
 // Brought to the beach in front of the rental: returned.
 const FVector Shore=Vec(D,TEXT("shore"),FVector(6650,-3300,0));
 if(bTowed && FVector::Dist2D(Mid,Shore)<UMareSimulation::Number(D,TEXT("shore_radius"),900)){S->RescueKayak();UMareAudioWorld::Action(this,TEXT("money_coins"));
  Kayak->Destroy();Kayak=nullptr;if(IsValid(Target))Target->Destroy();Target=nullptr;bTowed=false;}
}

FString UMareRentalWorld::Status()const
{
 if(!IsActive())return FString();auto Pawn=UGameplayStatics::GetPlayerPawn(GetWorld(),0);if(!Pawn)return FString();
 if(bTowed)return FString::Printf(TEXT("Rebocando o caiaque · leve até a areia do aluguel (%.0f m)"),FVector::Dist2D(Pos,Vec(SimOf(GetWorld())->RentalDefs(),TEXT("shore"),FVector(6650,-3300,0)))/100);
 return FString::Printf(TEXT("Caiaque à deriva a %.0f m · nade até ele e aperte E"),FVector::Dist2D(Pos,Pawn->GetActorLocation())/100);
}

FString UMareRentalWorld::QA(const FString& Cmd)
{
 auto Hero=Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(GetWorld(),0));
 if(Cmd==TEXT("near") && Hero && IsActive()){Hero->SetActorLocation(Pos+FVector(250,-150,-60));Hero->GetCharacterMovement()->StopMovementImmediately();
  if(auto PC=Cast<APlayerController>(Hero->GetController()))PC->SetControlRotation((Pos+FVector(0,0,-40)-Hero->GetActorLocation()).Rotation());return TEXT("ok");}
 if(Cmd==TEXT("tow")){Tow();return TEXT("ok");}
 if(Cmd==TEXT("home") && Hero){const FVector Shore=Vec(SimOf(GetWorld())->RentalDefs(),TEXT("shore"),FVector(6650,-3300,0));Hero->SetActorLocation(Shore+FVector(0,-300,-40));Pos=Shore+FVector(0,-500,0);return TEXT("ok");}
 return FString::Printf(TEXT("active=%d towed=%d pos=%.0f,%.0f"),IsActive(),bTowed,Pos.X,Pos.Y);
}
