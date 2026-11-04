#include "MareHomeWorld.h"
#include "MareGame.h"
#include "MareGamepad.h"
#include "Camera/PlayerCameraManager.h"
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
#include "MareCustomWorld.h"
#include "HAL/IConsoleManager.h"
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
   if(auto Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_HomeTV_Coast.M_HomeTV_Coast"))){TVPicture=UMaterialInstanceDynamic::Create(Material,this);Screen->SetMaterial(0,TVPicture);}
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
void UMareHomeWorld::StartSleep()
{
 if(IsSleeping())return;
 auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));
 auto PC=Hero?Cast<APlayerController>(Hero->GetController()):nullptr;if(!PC)return;
 Stand();Hero->GetCharacterMovement()->StopMovementImmediately();
 PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);
 PC->PlayerCameraManager->StartCameraFade(0,1,.65f,FLinearColor::Black,false,true);
 SleepTime=0;bDayAdvanced=false;
}
void UMareHomeWorld::Stand()
{
 if(!bSeated)return;auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!Hero)return;
 bSeated=false;Hero->SetActorTransform(Standing);Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Hero->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
}
void UMareHomeWorld::Use(FName Action)
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!Sim || !Hero)return;
 if(Action==TEXT("HomeTV")){bTV=!bTV;UpdateTV();Sim->LastMessage=bTV?TEXT("TV ligada · paisagens da costa"):TEXT("TV desligada");}
 if(Action==TEXT("HomeStereo")){bStereo=!bStereo;Sim->LastMessage=bStereo?TEXT("Som da casa ligado"):TEXT("Som da casa desligado");}
 if(Action==TEXT("HomeShower")){bShower=!bShower;Sim->LastMessage=bShower?TEXT("Chuveiro aberto"):TEXT("Chuveiro fechado");}
 if(Action==TEXT("HomeSink")){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("clean"),.24f);Sim->LastMessage=TEXT("Mãos limpas para um novo atendimento.");}
 if(Action==TEXT("HomeSofa")){
  if(bSeated){Stand();return;}Standing=Hero->GetActorTransform();bSeated=true;Hero->GetCharacterMovement()->DisableMovement();Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Hero->SetActorLocation(FVector(4435,2325,120));Hero->SetActorRotation(FRotator(0,-90,0));if(auto PC=Cast<APlayerController>(Hero->GetController()))PC->SetControlRotation(FRotator(0,-90,0));Sim->LastMessage=FText::Format(NSLOCTEXT("MareHome","SofaRest","Descansando no sofá · {0} ou movimento para levantar"),FText::FromString(MareGamepad::ActionLabel(TEXT("Interact")))).ToString();
 }
 auto State=UMareSimulation::Object(Sim->State,TEXT("ue_home"));State->SetBoolField(TEXT("tv"),bTV);State->SetBoolField(TEXT("stereo"),bStereo);Sim->Save();
}
// QA: "mare.HomeTV" switches the house TV like E on it (captures of every TV option lit).
static FAutoConsoleCommandWithWorld GMareHomeTV(TEXT("mare.HomeTV"),TEXT("Switch the house TV on/off (QA)."),
 FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World){if(World)if(auto Home=World->GetSubsystem<UMareHomeWorld>())Home->Use(TEXT("HomeTV"));}));

void UMareHomeWorld::UpdateTV()
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 // Whatever set is shown now (bought or previewed in the phone): its parts exist only for tiers 2..5.
 TArray<UMeshComponent*> Sets;if(auto Custom=GetWorld()->GetSubsystem<UMareCustomWorld>())Custom->SlotParts(TEXT("home"),TEXT("tv"),Sets);
 UMeshComponent* Set=Sets.Num()?Sets[0]:nullptr;
 // The old CRT keeps its separate glass screen; a new set lights its own picture slot. Rebuilt parts (a tier change)
 // come back with the mesh's dark screen, so the picture is reapplied whenever the set or the switch changes.
 if(TVScreen)TVScreen->SetActorHiddenInGame(!bTV || Set!=nullptr);
 if(Set==LitSet.Get() && bLitShown==bTV)return;
 LitSet=Set;bLitShown=bTV;if(!Set)return;
 for(int32 I=0;I<Set->GetNumMaterials();++I){const UStaticMeshComponent* Mesh=Cast<UStaticMeshComponent>(Set);
  const UMaterialInterface* Default=Mesh && Mesh->GetStaticMesh()?Mesh->GetStaticMesh()->GetMaterial(I):nullptr;
  if(Default && Default->GetName().Contains(TEXT("mare_tv_screen"))){
   static UMaterialInterface* Flat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/World/Materials/M_HomeTV_Flat.M_HomeTV_Flat"));
   Set->SetMaterial(I,bTV && Flat?Flat:nullptr);}}
}
void UMareHomeWorld::Tick(float Dt)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()))return;if(!bReady)Setup();
 if(UGameplayStatics::IsGamePaused(this))return;
 auto Hero=Cast<AMareCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!Hero)return;
 auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();Audio->SetHomeStereo(bStereo,FVector(4475,2111,108));
 UpdateTV();
 if(IsSleeping()){
  SleepTime+=Dt;auto PC=Cast<APlayerController>(Hero->GetController());
  if(SleepTime>=.75f && !bDayAdvanced){
   auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
   bDayAdvanced=true;bShower=false;Hero->SetActorLocation(FVector(4540,2000,110));
   Hero->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Sim->Sleep();
   Sim->LastMessage=TEXT("Bom dia! ")+Sim->LastMessage+TEXT(" O quiosque está fechado; abra a placa quando estiver pronto.");
   if(PC)PC->PlayerCameraManager->StartCameraFade(1,0,.8f,FLinearColor::Black,false,false);
  }
  if(SleepTime>=1.65f){SleepTime=-1;if(PC){PC->SetIgnoreMoveInput(false);PC->SetIgnoreLookInput(false);}}
 }
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
