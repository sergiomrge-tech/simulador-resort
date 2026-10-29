#include "MareHomeWorld.h"
#include "MareGame.h"
#include "MarePlayerPresentation.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MareAudioWorld.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TStatId UMareHomeWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareHomeWorld,STATGROUP_Tickables);}
AMareServiceTarget* UMareHomeWorld::Target(FName Action,const FString& Label,FVector Position,float Reach)
{
 auto T=GetWorld()->SpawnActor<AMareServiceTarget>(Position,FRotator::ZeroRotator);
 T->Action=Action;T->Label=Label;T->Reach=Reach;T->OcclusionTolerance=35;
 return T;
}
void UMareHomeWorld::Setup()
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 auto State=UMareSimulation::Object(Sim->State,TEXT("ue_home"));State->TryGetBoolField(TEXT("tv"),bTV);State->TryGetBoolField(TEXT("stereo"),bStereo);
 auto TVControl=Target(TEXT("HomeTV"),TEXT("TV · ligar/desligar"),FVector(4406,2119,121));
 Target(TEXT("HomeStereo"),TEXT("Som · ligar/desligar"),FVector(4475,2111,108));
 Target(TEXT("HomeSofa"),TEXT("Sofá · sentar e descansar"),FVector(4435,2342,65),220);
 Target(TEXT("HomeShower"),TEXT("Chuveiro · abrir/fechar água"),FVector(4919,1500,116));
 Target(TEXT("HomeSink"),TEXT("Pia · lavar as mãos"),FVector(4665,1638,95));
 FString Text;TSharedPtr<FJsonObject> Catalog;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/home_assets.json")));FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Catalog);
 const FString ScreenPath=UMareSimulation::String(Catalog,TEXT("tv_screen_mesh"));
 for(TActorIterator<AActor> It(GetWorld());It;++It){
  TArray<UInstancedStaticMeshComponent*> Components;It->GetComponents(Components);
  for(auto Source:Components)if(Source->GetInstanceCount()>0){
   if(!Source->GetStaticMesh() || Source->GetStaticMesh()->GetPathName()!=ScreenPath)continue;
   FTransform Transform;Source->GetInstanceTransform(0,Transform,true);
   if(FVector::Dist2D(Transform.GetLocation(),FVector(4406,2119,90))>100)continue;
   Transform.AddToTranslation(FVector(0,.08f,0));TVScreen=GetWorld()->SpawnActor<AStaticMeshActor>();
   auto Screen=TVScreen->GetStaticMeshComponent();Screen->SetMobility(EComponentMobility::Movable);TVScreen->SetActorTransform(Transform);
   Screen->SetStaticMesh(Source->GetStaticMesh());Screen->SetCollisionEnabled(ECollisionEnabled::NoCollision);Screen->SetCastShadow(false);
   Screen->UpdateBounds();TVControl->SetActorLocation(Screen->Bounds.Origin+FVector(0,2,0));
   if(auto Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_HomeTV_Coast.M_HomeTV_Coast")))Screen->SetMaterial(0,UMaterialInstanceDynamic::Create(Material,this));
   TVScreen->SetActorHiddenInGame(!bTV);
  }
 }
 auto Spray=GetWorld()->SpawnActor<AStaticMeshActor>();ShowerDrops=NewObject<UInstancedStaticMeshComponent>(Spray);Spray->AddInstanceComponent(ShowerDrops);
 ShowerDrops->SetupAttachment(Spray->GetRootComponent());ShowerDrops->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));
 ShowerDrops->SetCollisionEnabled(ECollisionEnabled::NoCollision);ShowerDrops->SetCastShadow(false);ShowerDrops->SetMobility(EComponentMobility::Movable);
 if(auto Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_ShowerWater.M_ShowerWater")))ShowerDrops->SetMaterial(0,Material);
 ShowerDrops->RegisterComponent();for(int32 I=0;I<128;++I)ShowerDrops->AddInstance(FTransform(FVector(4882,1500,100)));
 ShowerDrops->SetVisibility(false);bReady=true;
}
void UMareHomeWorld::Stand()
{
 if(!bSeated)return;auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!Hero)return;
 bSeated=false;Hero->SetActorTransform(Standing);Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Hero->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
}
void UMareHomeWorld::Use(FName Action)
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!Sim || !Hero)return;
 if(Action==TEXT("HomeTV")){bTV=!bTV;if(TVScreen)TVScreen->SetActorHiddenInGame(!bTV);Sim->LastMessage=bTV?TEXT("TV ligada · paisagens da costa"):TEXT("TV desligada");}
 if(Action==TEXT("HomeStereo")){bStereo=!bStereo;Sim->LastMessage=bStereo?TEXT("Som da casa ligado"):TEXT("Som da casa desligado");}
 if(Action==TEXT("HomeShower")){bShower=!bShower;Sim->LastMessage=bShower?TEXT("Chuveiro aberto"):TEXT("Chuveiro fechado");}
 if(Action==TEXT("HomeSink")){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("clean"),.24f);Sim->LastMessage=TEXT("Mãos limpas para um novo atendimento.");}
 if(Action==TEXT("HomeSofa")){
  if(bSeated){Stand();return;}Standing=Hero->GetActorTransform();bSeated=true;Hero->GetCharacterMovement()->DisableMovement();Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Hero->SetActorLocation(FVector(4435,2325,120));Hero->SetActorRotation(FRotator(0,-90,0));if(auto PC=Cast<APlayerController>(Hero->GetController()))PC->SetControlRotation(FRotator(0,-90,0));Sim->LastMessage=TEXT("Descansando no sofá · E ou movimento para levantar");
 }
 auto State=UMareSimulation::Object(Sim->State,TEXT("ue_home"));State->SetBoolField(TEXT("tv"),bTV);State->SetBoolField(TEXT("stereo"),bStereo);Sim->Save();
}
void UMareHomeWorld::Tick(float Dt)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()))return;if(!bReady)Setup();
 if(UGameplayStatics::IsGamePaused(this))return;
 auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!Hero)return;
 auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();Audio->SetHomeStereo(bStereo,FVector(4475,2111,108));
 if(bShower && FVector::DistSquared(Hero->GetActorLocation(),FVector(4800,1590,100))>FMath::Square(1000.f))bShower=false;
 if(ShowerDrops){ShowerDrops->SetVisibility(bShower);if(bShower)for(int32 I=0;I<128;++I){
  const float Phase=FMath::Fmod(GetWorld()->GetTimeSeconds()*1.2f+I/128.f,1.f),Angle=I*2.39996f;
  const FVector P(4882+FMath::Cos(Angle)*(5+Phase*13),1500+FMath::Sin(Angle)*(5+Phase*13),230-Phase*205);
  ShowerDrops->UpdateInstanceTransform(I,FTransform(FRotator::ZeroRotator,P,FVector(.012,.012,.09)),true,I==127,true);
 }}
 if(bSeated)if(auto P=Hero->FindComponentByClass<UMarePlayerPresentation>())if(auto Anim=Cast<UAnimSingleNodeInstance>(Hero->GetMesh()->GetAnimInstance()))if(Anim->GetCurrentAsset()==P->Clips.FindRef(TEXT("Sitting_Idle"))){
  const FVector Delta=FVector(4435,2325,56)-Hero->GetMesh()->GetSocketLocation(TEXT("pelvis"));Hero->AddActorWorldOffset(Delta*FMath::Min(1.f,Dt*8.f));
 }
}
