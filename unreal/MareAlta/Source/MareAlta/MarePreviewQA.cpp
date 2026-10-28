#include "MarePreviewQA.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareServiceAnimation.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "MareSimulation.h"
#include "MareAudioWorld.h"
#include "MareVisualWorld.h"
#include "EngineUtils.h"
#include "AudioMixerBlueprintLibrary.h"
#include "Misc/App.h"
#include "AudioDevice.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "InputKeyEventArgs.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PhysicsVolume.h"
#include "Components/BrushComponent.h"
#include "Components/CapsuleComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

AMarePreviewQA::AMarePreviewQA(){PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.bTickEvenWhenPaused=true;}
AMarePerson* AMarePreviewQA::SpawnInspectionPerson(UObject* WorldContextObject,FVector Location,int32 Variant,const FString& Dish)
{
 FString Profile;FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Profile);Profile.ReplaceInline(TEXT("\\"),TEXT("/"));
 auto World=GEngine->GetWorldFromContextObject(WorldContextObject,EGetWorldErrorMode::ReturnNull);
 if(!Profile.StartsWith(TEXT("D:/CodexTemp/")) || !World || !World->IsGameWorld())return nullptr;
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto Person=World->SpawnActor<AMarePerson>(Location,FRotator(0,-90,0),Params);if(!Person)return nullptr;
 Person->Tags.Add(TEXT("MareAuditFixture"));Person->SetAppearance(Variant);Person->HoldProduct(Dish);
 Person->Stage=EMarePersonStage::Eating;Person->Delivered.Add(Dish);Person->PlayPose(TEXT("Idle"));
 Person->GetCharacterMovement()->DisableMovement();Person->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 return Person;
}
void AMarePreviewQA::Check(const FString& Name,bool bPass)
{
 auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("name"),Name);Row->SetBoolField(TEXT("pass"),bPass);
 if(auto Hero=UGameplayStatics::GetPlayerCharacter(this,0)){
  auto P=Hero->GetActorLocation();Row->SetArrayField(TEXT("position"),{MakeShared<FJsonValueNumber>(P.X),MakeShared<FJsonValueNumber>(P.Y),MakeShared<FJsonValueNumber>(P.Z)});
  Row->SetStringField(TEXT("movement"),Hero->GetCharacterMovement()->GetMovementName());
  auto Volume=Hero->GetPhysicsVolume();Row->SetStringField(TEXT("volume"),Volume->GetName());
  if(auto Brush=Volume->GetBrushComponent())Row->SetStringField(TEXT("volume_collision"),Brush->GetCollisionProfileName().ToString());
  FHitResult Hit;
  FCollisionQueryParams Query;Query.AddIgnoredActor(Hero);
  if(GetWorld()->LineTraceSingleByChannel(Hit,P,P+FVector(0,0,180),ECC_Visibility,Query))Row->SetStringField(TEXT("overhead"),GetNameSafe(Hit.GetActor()));
 }
 Results.Add(MakeShared<FJsonValueObject>(Row));UE_LOG(LogTemp,Display,TEXT("MARE_PREVIEW_QA %s %s"),*Name,bPass?TEXT("PASS"):TEXT("FAIL"));
 auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("checks"),Results);Report->SetBoolField(TEXT("finished"),Name==TEXT("expansion_profile_restored"));
 FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*(Root/TEXT("preview-qa.json")));
}
void AMarePreviewQA::Capture(const FString& Name){FScreenshotRequest::RequestScreenshot(Root/(Name+TEXT(".png")),true,false);}
void AMarePreviewQA::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));auto Hero=PC?Cast<AMareCharacter>(PC->GetPawn()):nullptr;
 if(!Hero)return;
 if(Root.IsEmpty()){
  FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Root);Root.ReplaceInline(TEXT("\\"),TEXT("/"));
  if(!Root.StartsWith(TEXT("D:/CodexTemp/"))){Destroy();return;}
  FApp::SetUnfocusedVolumeMultiplier(1.f);Next=FPlatformTime::Seconds()+12;Phase=0;
 }
 if(FPlatformTime::Seconds()<Next || Phase>24)return;
 auto Move=Hero->GetCharacterMovement();auto Eyes=Hero->FindComponentByClass<UCameraComponent>();
 auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();auto Sim=PC->GetSimulation();
 auto Key=[&](FKey K,bool Down){PC->InputKey(FInputKeyEventArgs(GEngine->GameViewport->Viewport,INPUTDEVICEID_NONE,K,Down?IE_Pressed:IE_Released,FPlatformTime::Cycles64()));};
 switch(Phase++){
 case 0:{
  Check(TEXT("coast_and_dry_land"),GetWorld()->GetMapName().Contains(TEXT("Coast")) && !Move->IsSwimming());
  int32 Variant=0;for(const FString Dish:{TEXT("coco_gelado"),TEXT("suco"),TEXT("batata_frita"),TEXT("sorvete_morango")}){
   if(auto Person=SpawnInspectionPerson(this,FVector(3000+Variant*120,-2400,90),Variant,Dish))PresentationFixtures.Add(Person);++Variant;
  }
  Check(TEXT("customer_models_spawn"),PresentationFixtures.Num()==4);
  auto Visual=GetWorld()->GetSubsystem<UMareVisualWorld>();Visual->RefreshExpansions();
  auto Ownership=UMareSimulation::Object(Sim->State,TEXT("unlocked"));
  auto RegionMatches=[&](const FString& Region,bool bOwned){
   int32 Count=0;bool bCorrect=true;
   for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(FName(TEXT("Region_")+Region))){
    ++Count;bCorrect&=It->IsHidden()!=bOwned && It->GetActorEnableCollision()==bOwned;
   }
   return Count>0 && bCorrect;
  };
  for(const FString Region:{TEXT("pousada"),TEXT("bar"),TEXT("pool"),TEXT("neon"),TEXT("kiosk_tables"),TEXT("drinks"),TEXT("grand_hotel")}){
   bool bOwned=false;Ownership->TryGetBoolField(Region,bOwned);
   Check(TEXT("expansion_saved_visibility_")+Region,RegionMatches(Region,bOwned));
  }
  auto BusinessState=UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("biz"));
  for(const FString Id:{TEXT("sorveteria"),TEXT("aluguel"),TEXT("surfe"),TEXT("food_truck"),TEXT("souvenir")})
   Check(TEXT("business_saved_visibility_")+Id,RegionMatches(TEXT("Biz_")+Id,UMareSimulation::Number(UMareSimulation::Object(BusinessState,Id),TEXT("lvl"))>0));
  bool bPoolOwned=false;Ownership->TryGetBoolField(TEXT("pool"),bPoolOwned);int32 LotCount=0;bool bLotCorrect=true;
  for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("Lot_pool"))){++LotCount;bLotCorrect&=It->IsHidden()==bPoolOwned && It->GetActorEnableCollision()!=bPoolOwned;}
  Check(TEXT("pool_ground_cover_before_purchase"),LotCount==1 && bLotCorrect);
  const double OriginalCash=Sim->Money();const auto OriginalOwnership=MakeShared<FJsonObject>(*Ownership);
  Ownership->RemoveField(TEXT("kiosk_tables"));Visual->RefreshExpansions();
  Sim->State->SetNumberField(TEXT("money"),100000);
  Check(TEXT("expansion_purchase_reveals_geometry"),Sim->BuyExpansion(TEXT("kiosk_tables")) && RegionMatches(TEXT("kiosk_tables"),true));
  const double PurchasedCash=Sim->Money();
  Check(TEXT("expansion_duplicate_no_charge"),!Sim->BuyExpansion(TEXT("kiosk_tables")) && Sim->Money()==PurchasedCash);
  Sim->State->SetObjectField(TEXT("unlocked"),OriginalOwnership);Sim->State->SetNumberField(TEXT("money"),OriginalCash);
  Visual->RefreshExpansions();Sim->Save();
  FString Text;TSharedPtr<FJsonObject> Catalog;int32 Missing=0,Count=0;
  if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/actors.json"))) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Catalog)){
   for(const auto& Pair:Catalog->Values){auto Row=Pair.Value->AsObject();for(const FString Kind:{TEXT("static_meshes"),TEXT("skeletal_meshes")}){
    const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;if(Row->TryGetArrayField(Kind,Paths))for(const auto& Path:*Paths){++Count;if(!LoadObject<UObject>(nullptr,*Path->AsString()))++Missing;}}
    for(const auto& Clip:UMareSimulation::Object(Row,TEXT("animations"))->Values){++Count;if(!LoadObject<UObject>(nullptr,*Clip.Value->AsString()))++Missing;}
   }
  }
  Check(TEXT("runtime_actor_catalog"),Count>60 && Missing==0);
  Check(TEXT("audio_catalog"),Audio->LoadedSounds()==41);
  Check(TEXT("master_submix_routed"),Audio->HasMasterMix());
  if(auto Device=GetWorld()->GetAudioDevice()){UE_LOG(LogTemp,Display,TEXT("MARE_QA_AUDIO_DEVICE muted=%d primary=%f app=%f"),Device->IsAudioDeviceMuted(),Device->GetPrimaryVolume(),FApp::GetVolumeMultiplier());Device->SetDeviceMuted(false);Device->SetTransientPrimaryVolume(1.f);}
  FApp::SetVolumeMultiplier(1.f);
  InitialMaster=Audio->GetVolume(TEXT("Master"));InitialMinutes=UMareSimulation::Number(Sim->State,TEXT("minutes"));InitialWeather=UMareSimulation::String(Sim->State,TEXT("weather"));
  Audio->SetVolume(TEXT("Master"),.85f);UAudioMixerBlueprintLibrary::StartRecordingOutput(this,10);
  Hero->SetActorLocation(FVector(3800,-7200,-100));Move->StopMovementImmediately();PC->SetControlRotation(FRotator(0,-90,0));break;
 }
 case 1:{
  bool bAnimated=PresentationFixtures.Num()==4,bGripped=bAnimated;
  for(auto Person:PresentationFixtures){if(!IsValid(Person)){bAnimated=bGripped=false;continue;}
   auto Anim=Cast<UMareServiceAnimInstance>(Person->GetMesh()->GetAnimInstance());bAnimated&=Anim && Anim->GetCurrentAsset()!=nullptr;
   bGripped&=Person->CarriedMeshes.Num()==1;
   for(auto Part:Person->CarriedMeshes)if(IsValid(Part))bGripped&=FVector::Distance(Part->GetComponentLocation(),Person->GetMesh()->GetSocketLocation(Part->GetAttachSocketName()))<25.f;
   Person->Destroy();
  }
  PresentationFixtures.Empty();Check(TEXT("customer_authored_animation_active"),bAnimated);Check(TEXT("products_follow_animated_hands"),bGripped);
  UAudioMixerBlueprintLibrary::StopRecordingOutput(this,EAudioRecordingExportType::WavFile,TEXT("mix_audible"),Root);Audio->SetVolume(TEXT("Master"),0);UAudioMixerBlueprintLibrary::StartRecordingOutput(this,5);Check(TEXT("water_entry_and_float"),Move->IsSwimming() && Hero->GetActorLocation().Z>-90 && Hero->GetActorLocation().Z<-25);Check(TEXT("surface_camera_above_water"),Eyes && Eyes->GetComponentLocation().Z>-30);Before=Hero->GetActorLocation();Key(EKeys::LeftControl,true);Capture(TEXT("surface"));break;
 }
 case 2:UAudioMixerBlueprintLibrary::StopRecordingOutput(this,EAudioRecordingExportType::WavFile,TEXT("mix_muted"),Root);Audio->SetVolume(TEXT("Master"),.85f);Key(EKeys::LeftControl,false);Check(TEXT("ctrl_dives"),Hero->GetActorLocation().Z<Before.Z-70);Check(TEXT("underwater_camera"),Eyes && Eyes->PostProcessBlendWeight>.8);Capture(TEXT("underwater"));Key(EKeys::SpaceBar,true);break;
 case 3:Key(EKeys::SpaceBar,false);Check(TEXT("space_surfaces"),Hero->GetActorLocation().Z>-90 && Move->IsSwimming());Before=Hero->GetActorLocation();Key(EKeys::W,true);break;
 case 4:Key(EKeys::W,false);Check(TEXT("swimming_forward"),FVector::Dist2D(Before,Hero->GetActorLocation())>150);Hero->SetActorLocation(FVector(3800,-2900,180));Move->StopMovementImmediately();break;
 case 5:Check(TEXT("return_to_walking"),Move->IsMovingOnGround() && !Move->IsSwimming());Hero->SetActorLocation(FVector(3800,-2900,-6000));break;
 case 6:Check(TEXT("void_recovery"),Hero->GetActorLocation().Z>-500 && !Move->IsSwimming());PC->TogglePhone();Capture(TEXT("phone"));break;
 case 7:Check(TEXT("portable_phone"),PC->bPhoneOpen && PC->IsMoveInputIgnored());PC->ClosePhone();PC->TogglePauseMenu();PausedTime=GetWorld()->GetTimeSeconds();Capture(TEXT("pause"));UAudioMixerBlueprintLibrary::StartRecordingOutput(this,5);break;
 case 8:UAudioMixerBlueprintLibrary::StopRecordingOutput(this,EAudioRecordingExportType::WavFile,TEXT("mix_paused"),Root);Check(TEXT("pause_freezes_world"),UGameplayStatics::IsGamePaused(this) && FMath::IsNearlyEqual(PausedTime,double(GetWorld()->GetTimeSeconds()),.01));PC->TogglePhone();Check(TEXT("pause_blocks_duplicate_phone"),!PC->bPhoneOpen);PC->TogglePauseMenu();break;
 case 9:Check(TEXT("resume"),!UGameplayStatics::IsGamePaused(this) && !PC->IsMoveInputIgnored());Sim->CreateCompany(TEXT("Prévia QA"));Sim->AdvanceMinutes(390-UMareSimulation::Number(Sim->State,TEXT("minutes")));Sim->SetOpen(true);Check(TEXT("opening_respects_schedule"),!Sim->IsOpen());Sim->AdvanceMinutes(600-UMareSimulation::Number(Sim->State,TEXT("minutes")));Sim->SetOpen(true);break;
 case 10:Check(TEXT("kiosk_open"),PC->GetSimulation()->IsOpen());Hero->SetActorLocation(FVector(3800,-1200,100));PC->SetControlRotation(FRotator(-6,-90,0));PC->TogglePhone();Capture(TEXT("kiosk-phone"));break;
 case 11:PC->ClosePhone();Check(TEXT("save_succeeds"),PC->GetSimulation()->Save());break;
 case 12:Sim->AdvanceMinutes(1320-UMareSimulation::Number(Sim->State,TEXT("minutes")));break;
 case 13:Check(TEXT("night_crickets"),Audio->LoopLevel(TEXT("crickets_loop"))>.02f);Capture(TEXT("kiosk-night"));Sim->State->SetStringField(TEXT("weather"),TEXT("rain"));break;
 case 14:Check(TEXT("rain_mix"),Audio->LoopLevel(TEXT("rain_loop"))>.02f && Audio->LoopLevel(TEXT("crickets_loop"))<.005f);Capture(TEXT("kiosk-rain"));Sim->State->SetStringField(TEXT("weather"),InitialWeather);Sim->AdvanceMinutes(720-UMareSimulation::Number(Sim->State,TEXT("minutes")));break;
 case 15:Capture(TEXT("kiosk-day"));break;
 case 16:Hero->SetActorLocation(FVector(4520,2120,100));PC->SetControlRotation(FRotator(-8,25,0));break;
 case 17:Capture(TEXT("house-day"));break;
 case 18:Hero->SetActorLocation(FVector(3800,-1200,100));PC->SetControlRotation(FRotator(-6,-90,0));Sim->AdvanceMinutes(InitialMinutes-UMareSimulation::Number(Sim->State,TEXT("minutes")));Audio->SetVolume(TEXT("Master"),InitialMaster);Sim->Save();Check(TEXT("audio_settings_restored"),FMath::IsNearlyEqual(Audio->GetVolume(TEXT("Master")),InitialMaster));break;
 case 19:{
  ExpansionOwnership=MakeShared<FJsonObject>(*UMareSimulation::Object(Sim->State,TEXT("unlocked")));ExpansionCash=Sim->Money();
  FBox Bounds(ForceInit);for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("Region_pool")))Bounds+=It->GetComponentsBoundingBox(true);
  if(Bounds.IsValid){const FVector Center=Bounds.GetCenter();const FVector View=Center+FVector(1400,-1400,800);
   Move->SetMovementMode(MOVE_Flying);Move->StopMovementImmediately();Hero->SetActorLocation(View);PC->SetControlRotation((Center-View).Rotation());
  }
  break;
 }
 case 20:Capture(TEXT("expansion-pool-locked"));break;
 case 21:{
  Sim->State->SetNumberField(TEXT("money"),100000);bool bPurchased=true;
  for(const FString Id:{TEXT("kiosk_tables"),TEXT("drinks"),TEXT("grill"),TEXT("bar"),TEXT("pousada"),TEXT("pool")}){
   bool bOwned=false;UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(Id,bOwned);
   if(!bOwned)bPurchased&=Sim->BuyExpansion(Id);
  }
  Check(TEXT("expansion_pool_dependency_chain"),bPurchased);
  bool bCoverRemoved=false;for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("Lot_pool")))bCoverRemoved=It->IsHidden() && !It->GetActorEnableCollision();
  Check(TEXT("pool_ground_cover_removed_after_purchase"),bCoverRemoved);break;
 }
 case 22:Capture(TEXT("expansion-pool-purchased"));break;
 case 23:
  Sim->State->SetObjectField(TEXT("unlocked"),ExpansionOwnership);Sim->State->SetNumberField(TEXT("money"),ExpansionCash);
  GetWorld()->GetSubsystem<UMareVisualWorld>()->RefreshExpansions();
  Hero->SetActorLocation(FVector(3800,-1200,100));Move->SetMovementMode(MOVE_Walking);PC->SetControlRotation(FRotator(-6,-90,0));
  Check(TEXT("expansion_profile_restored"),Sim->Save());break;
 case 24:if(GetWorld()->WorldType!=EWorldType::PIE)GEngine->Exec(GetWorld(),TEXT("QUIT"));break;
 }
 Next=FPlatformTime::Seconds()+(Phase==13?10:Phase==1?7:Phase==3?4:Phase==4?5:3);
}
