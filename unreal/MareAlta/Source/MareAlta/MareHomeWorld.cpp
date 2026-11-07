#include "MareHomeWorld.h"
#include "MareLoc.h"
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
 SetupStereos(State);
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
 for(FStereoSet& Set:StereoSets)if(Action==Set.Action || (Action==TEXT("HomeStereoOff") && Set.Id==TEXT("home"))){
  // Next track on this set; past the last one it switches off (E is the only button on a set).
  TArray<FName> Tracks=UMareAudioWorld::RadioStations();Tracks.Remove(TEXT("off"));
  if(Action==TEXT("HomeStereoOff"))Set.Track=NAME_None;
  else if(Set.Track.IsNone())Set.Track=Tracks.Contains(Set.Default)?Set.Default:(Tracks.Num()?Tracks[0]:NAME_None);
  else{const int32 I=Tracks.IndexOfByKey(Set.Track);Set.Track=Tracks.IsValidIndex(I+1)?Tracks[I+1]:NAME_None;}
  Sim->LastMessage=Set.Track.IsNone()?TEXT("Rádio desligado"):TEXT("Tocando: ")+UMareAudioWorld::RadioName(Set.Track);
  if(Set.Id==TEXT("home"))bStereo=!Set.Track.IsNone();
  UMareSimulation::Object(Sim->State,TEXT("ue_home"))->SetStringField(TEXT("stereo_")+Set.Id,Set.Track.IsNone()?FString():Set.Track.ToString());}   // i18n:skip
 if(Action==TEXT("HomeShower")){bShower=!bShower;Sim->LastMessage=bShower?TEXT("Chuveiro aberto"):TEXT("Chuveiro fechado");}
 if(Action==TEXT("HomeSink")){GetWorld()->GetSubsystem<UMareAudioWorld>()->PlayCue(TEXT("clean"),.24f);Sim->LastMessage=TEXT("Mãos limpas para um novo atendimento.");}
 if(Action==TEXT("HomeSofa")){
  if(bSeated){Stand();return;}Standing=Hero->GetActorTransform();bSeated=true;Hero->GetCharacterMovement()->DisableMovement();Hero->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Hero->SetActorLocation(FVector(4435,2325,120));Hero->SetActorRotation(FRotator(0,-90,0));if(auto PC=Cast<APlayerController>(Hero->GetController()))PC->SetControlRotation(FRotator(0,-90,0));Sim->LastMessage=FText::Format(NSLOCTEXT("MareHome","SofaRest","Descansando no sofá · {0} ou movimento para levantar"),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Interact")))).ToString();
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
 UpdateStereos();
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

void UMareHomeWorld::SetupStereos(const TSharedPtr<FJsonObject>& HomeState)
{
 FString Text;TSharedPtr<FJsonObject> Defs;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/radio.json")));FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);   // i18n:skip
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(!Defs.IsValid() || !Defs->TryGetArrayField(TEXT("stereos"),List))return;   // i18n:skip
 for(const auto& V:*List){const auto D=V->AsObject();FStereoSet Set;
  Set.Id=UMareSimulation::String(D,TEXT("id"));Set.Action=FName(UMareSimulation::String(D,TEXT("action")));Set.Unlock=UMareSimulation::String(D,TEXT("unlock"));   // i18n:skip
  Set.Default=FName(UMareSimulation::String(D,TEXT("default")));D->TryGetBoolField(TEXT("boombox"),Set.bModel);Set.Yaw=UMareSimulation::Number(D,TEXT("yaw"));Set.Probe=UMareSimulation::Number(D,TEXT("probe"),220);   // i18n:skip
  const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(D->TryGetArrayField(TEXT("at"),At) && At->Num()>=3)Set.At=FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());   // i18n:skip
  // Saved track (empty = off); the house's old on/off switch meant its relaxing track.
  FString Saved;if(HomeState->TryGetStringField(TEXT("stereo_")+Set.Id,Saved))Set.Track=Saved.IsEmpty()?NAME_None:FName(Saved);   // i18n:skip
  else if(Set.Id==TEXT("home") && bStereo)Set.Track=Set.Default;
  StereoSets.Add(Set);}
}
void UMareHomeWorld::UpdateStereos()
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();if(!Sim || !Audio)return;
 static UStaticMesh* Boombox=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/World/Models/World_1165/World_1165/StaticMeshes/World_1165.World_1165"));
 for(FStereoSet& Set:StereoSets){
  bool bOwned=Set.Unlock.IsEmpty();if(!bOwned)UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(Set.Unlock,bOwned);
  if(bOwned && !Set.bPlaced){Set.bPlaced=true;
   // On the counter below (z 0 in radio.json): the first surface a trace finds from probe cm down (above the counter,
   // under the roof: from 12 m it landed on the kiosk roof and the lobby ceiling).
   if(Set.At.Z==0){FHitResult Hit;FCollisionQueryParams Params;Params.bTraceComplex=true;
    if(GetWorld()->LineTraceSingleByChannel(Hit,FVector(Set.At.X,Set.At.Y,Set.Probe),FVector(Set.At.X,Set.At.Y,-200),ECC_Visibility,Params))Set.At.Z=Hit.ImpactPoint.Z;}
   if(Set.bModel && Boombox){auto Model=GetWorld()->SpawnActor<AStaticMeshActor>(Set.At,FRotator(0,Set.Yaw,0));
    if(Model){Model->SetMobility(EComponentMobility::Movable);Model->GetStaticMeshComponent()->SetStaticMesh(Boombox);Model->SetActorScale3D(FVector(.66f));
     Model->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Set.Model=Model;}}
   Set.Target=Target(Set.Action,FString(),Set.At+FVector(0,0,Set.bModel?20.f:0.f));}
  if(Set.Model.IsValid())Set.Model->SetActorHiddenInGame(!bOwned);
  if(Set.Target.IsValid()){Set.Target->SetActorHiddenInGame(!bOwned);Set.Target->SetActorEnableCollision(bOwned);
   Set.Target->Label=Set.Track.IsNone()?FString(TEXT("Rádio · ligar")):TEXT("Rádio · ")+UMareAudioWorld::RadioName(Set.Track)+TEXT(" · próxima música");}
  Audio->SetStereo(FName(Set.Id),bOwned?Set.Track:NAME_None,Set.At+FVector(0,0,15));}
}
