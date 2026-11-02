#include "MarePerson.h"
#include "MareServiceAnimation.h"
#include "MareServiceTarget.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MareKioskWorld.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "NavigationSystem.h"
#include "Animation/AnimSequence.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/Texture2D.h"
#include "Components/CapsuleComponent.h"
#include "Components/ChildActorComponent.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

static TAutoConsoleVariable<int32> CVarMareMetaHumans(TEXT("mare.MetaHumans"),1,TEXT("People wear the built MetaHumans of Content/Data/metahumans.json (0 = original rig people)."));
static TAutoConsoleVariable<FString> CVarMareMetaHuman(TEXT("mare.MetaHuman"),TEXT(""),TEXT("QA: force this built MetaHuman on every new person (empty = roster choice)."));

/** Content/Data/metahumans.json: built MetaHumans per role (staff, hotel, village, beach) and swimwear colours. */
static TSharedPtr<FJsonObject> MetaHumanRoster()
{
 static TSharedPtr<FJsonObject> Roster;
 if(!Roster.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/metahumans.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Roster);if(!Roster.IsValid())Roster=MakeShared<FJsonObject>();}
 return Roster;
}

TSharedPtr<FJsonObject> AMarePerson::AssetCatalog()
{
 FString Text;TSharedPtr<FJsonObject> Result;
 FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/actors.json")));
 FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);return Result.IsValid()?Result:MakeShared<FJsonObject>();
}
UStaticMesh* AMarePerson::ProductMesh(const FString& Dish,bool bUsed)
{
 auto Entry=UMareSimulation::Object(AssetCatalog(),(bUsed?TEXT("Used_"):TEXT("Dish_"))+Dish);
 const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;
 if(!Entry->TryGetArrayField(TEXT("static_meshes"),Paths) || Paths->IsEmpty())return nullptr;
 return LoadObject<UStaticMesh>(nullptr,*(*Paths)[0]->AsString());
}
AMarePerson::AMarePerson()
{
 PrimaryActorTick.bCanEverTick=true;GetCapsuleComponent()->InitCapsuleSize(28,88);
 GetMesh()->SetRelativeLocation(FVector(0,0,-88));GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
 GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 GetCharacterMovement()->MaxWalkSpeed=125;GetCharacterMovement()->bOrientRotationToMovement=true;
 GetCharacterMovement()->RotationRate=FRotator(0,180,0);GetCharacterMovement()->MaxStepHeight=32;
 AIControllerClass=AAIController::StaticClass();AutoPossessAI=EAutoPossessAI::PlacedInWorldOrSpawned;
 bUseControllerRotationYaw=false;
 auto Carry=CreateDefaultSubobject<UMareCarryPresentation>(TEXT("CarryPresentation"));Carry->AddTickPrerequisiteComponent(GetMesh());
}
FTransform AMarePerson::ReferenceBoneTransform(FName Bone)const
{
 auto MeshAsset=GetMesh()->GetSkeletalMeshAsset();if(!MeshAsset)return FTransform::Identity;
 const auto& Ref=MeshAsset->GetRefSkeleton();int32 Index=Ref.FindBoneIndex(Bone);FTransform Result=FTransform::Identity;
 while(Index!=INDEX_NONE){Result=Result*Ref.GetRefBonePose()[Index];Index=Ref.GetParentIndex(Index);}return Result;
}
bool AMarePerson::SetAppearance(int32 AppearanceVariant)
{
 if(SaveId.IsEmpty())SaveId=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 const int32 Selected=(AppearanceVariant%4+4)%4;
 const FString Key=FString::Printf(TEXT("Human_%d"),Selected);auto Row=UMareSimulation::Object(AssetCatalog(),Key);
 const TArray<TSharedPtr<FJsonValue>>* Paths=nullptr;if(!Row->TryGetArrayField(TEXT("skeletal_meshes"),Paths) || Paths->IsEmpty())return false;
 auto MeshAsset=LoadObject<USkeletalMesh>(nullptr,*(*Paths)[0]->AsString());if(!MeshAsset)return false;
 Variant=Selected;
 // Reapplying a look must not stack hair or leave the new anim instance without a clip.
 for(auto Part:HairMeshes)if(IsValid(Part))Part->DestroyComponent();HairMeshes.Empty();
 Clips.Empty();Playing.Reset();bOutfitApplied=false;   // a new mesh brings its default materials back
 GetMesh()->SetSkeletalMeshAsset(MeshAsset);GetMesh()->SetAnimInstanceClass(UMareServiceAnimInstance::StaticClass());
 for(const FString& Name:{TEXT("Idle"),TEXT("Idle_Talking"),TEXT("Walk"),TEXT("Sitting_Idle"),TEXT("Interact")}){
  const FString Path=UMareSimulation::String(UMareSimulation::Object(Row,TEXT("animations")),Key+Name);
  if(auto Clip=LoadObject<UAnimSequence>(nullptr,*Path))Clips.Add(Name,Clip);
 }
 if(Row->TryGetArrayField(TEXT("static_meshes"),Paths))for(const auto& Path:*Paths){auto Part=LoadObject<UStaticMesh>(nullptr,*Path->AsString());if(!Part)continue;
  const FName Bone=Part->GetName().StartsWith(TEXT("Camera_"))?TEXT("neck_01"):TEXT("Head");
  auto Hair=NewObject<UStaticMeshComponent>(this);AddInstanceComponent(Hair);Hair->SetMobility(EComponentMobility::Movable);Hair->SetStaticMesh(Part);Hair->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Hair->AttachToComponent(GetMesh(),FAttachmentTransformRules::KeepRelativeTransform,Bone);Hair->SetRelativeTransform(ReferenceBoneTransform(Bone).Inverse());Hair->RegisterComponent();HairMeshes.Add(Hair);
 }
 PlayPose(TEXT("Idle"));return true;
}
bool AMarePerson::SetMetaHuman(const FString& Name)
{
 const FString Root=FString::Printf(TEXT("/Game/People/MetaHumans/%s/MH_%s/"),*Name,*Name);
 auto Body=LoadObject<USkeletalMesh>(nullptr,*FString::Printf(TEXT("%sBody/SKM_MH_%s_BodyMesh.SKM_MH_%s_BodyMesh"),*Root,*Name,*Name));
 UClass* Look=LoadClass<AActor>(nullptr,*FString::Printf(TEXT("%sBP_MH_%s.BP_MH_%s_C"),*Root,*Name,*Name));
 if(!Body || !Look)return false;
 for(auto Part:HairMeshes)if(IsValid(Part))Part->DestroyComponent();HairMeshes.Empty();
 Clips.Empty();Playing.Reset();bOutfitApplied=true;MetaHuman=Name;
 // The rig mesh becomes the MetaHuman body skeleton and keeps driving the pose (clips retargeted from UAL
 // by mare_metahuman.retarget_clips); it stays hidden while the blueprint's body, face, clothes and grooms follow it.
 GetMesh()->SetSkeletalMeshAsset(Body);GetMesh()->SetAnimInstanceClass(UMareServiceAnimInstance::StaticClass());
 for(const FString& Clip:{TEXT("Idle"),TEXT("Idle_Talking"),TEXT("Walk"),TEXT("Sitting_Idle"),TEXT("Interact")})
  if(auto Anim=LoadObject<UAnimSequence>(nullptr,*FString::Printf(TEXT("/Game/People/Animations/MH_%s.MH_%s"),*Clip,*Clip)))Clips.Add(Clip,Anim);
 GetMesh()->SetVisibility(false,false);
 if(MetaHumanBody)MetaHumanBody->DestroyComponent();
 MetaHumanBody=NewObject<UChildActorComponent>(this);AddInstanceComponent(MetaHumanBody);
 MetaHumanBody->SetupAttachment(GetMesh());MetaHumanBody->SetChildActorClass(Look);MetaHumanBody->RegisterComponent();
 if(AActor* Child=MetaHumanBody->GetChildActor()){TArray<USkeletalMeshComponent*> Parts;Child->GetComponents(Parts);
  for(auto Part:Parts){Part->SetLeaderPoseComponent(GetMesh());Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);}}
 // Swim builds (<Name>_Swim, whole body) wear the bikini/trunks made for that body (tools/ue58/gen_mh_swimwear.py).
 if(Swimwear){Swimwear->DestroyComponent();Swimwear=nullptr;}
 if(Name.EndsWith(TEXT("_Swim"))){const FString Base=Name.LeftChop(5);USkeletalMesh* Garment=nullptr;
  for(const TCHAR* Kind:{TEXT("Bikini"),TEXT("Trunks")})
   if(!Garment)Garment=LoadObject<USkeletalMesh>(nullptr,*FString::Printf(TEXT("/Game/People/Swimwear/SKM_%s_%s.SKM_%s_%s"),Kind,*Base,Kind,*Base));
  if(Garment){Swimwear=NewObject<USkeletalMeshComponent>(this);AddInstanceComponent(Swimwear);Swimwear->SetupAttachment(GetMesh());
   Swimwear->SetSkeletalMeshAsset(Garment);Swimwear->SetCollisionEnabled(ECollisionEnabled::NoCollision);Swimwear->RegisterComponent();
   Swimwear->SetLeaderPoseComponent(GetMesh());
   const TArray<TSharedPtr<FJsonValue>>* Colours=nullptr;
   if(MetaHumanRoster()->TryGetArrayField(TEXT("swim_colours"),Colours) && Colours->Num()){
    const FColor C=FColor::FromHex((*Colours)[int32(FCrc::StrCrc32(*SaveId)%uint32(Colours->Num()))]->AsString());
    for(int32 I=0;I<Swimwear->GetNumMaterials();++I)if(auto M=Swimwear->CreateDynamicMaterialInstance(I))M->SetVectorParameterValue(TEXT("Tint"),FLinearColor(C));}}}
 PlayPose(TEXT("Idle"));return true;
}
void AMarePerson::PlayPose(const FString& Name,bool bLoop)
{
 if(Playing==Name || !Clips.Contains(Name))return;Playing=Name;
 if(auto Instance=Cast<UMareServiceAnimInstance>(GetMesh()->GetAnimInstance())){Instance->SetAnimationAsset(Clips[Name],bLoop);Instance->SetPlaying(true);}
}
bool AMarePerson::WalkTo(const FVector& Goal)
{
 Destination=Goal;
 if(auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld())){
  FNavLocation Projected;
  if(!Nav->ProjectPointToNavigation(Goal,Projected,FVector(80,80,150)))return false;
  Destination=Projected.Location;
 }
 GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
 GetCharacterMovement()->SetMovementMode(MOVE_Walking);SpawnDefaultController();
 auto AI=Cast<AAIController>(GetController());if(!AI)return false;
 // Stop-on-overlap adds the capsule radius to acceptance, leaving customers
 // outside the arrival threshold even after a successful path completion.
 const auto Result=AI->MoveToLocation(Destination,20,false,true,false,true,nullptr,false);
 if(Result==EPathFollowingRequestResult::Failed)return false;
 PlayPose(TEXT("Walk"));return true;
}
bool AMarePerson::AtGoal()const{return FVector::DistSquared2D(GetActorLocation(),Destination)<FMath::Square(35.f);}
void AMarePerson::HoldProduct(const FString& Dish)
{
 auto MeshAsset=ProductMesh(Dish);if(!MeshAsset)return;
 const FName Hand=CarriedMeshes.Num()%2==0?TEXT("hand_r"):TEXT("hand_l");
 if(!GetMesh()->DoesSocketExist(Hand))return;
 auto Product=NewObject<UStaticMeshComponent>(this);AddInstanceComponent(Product);Product->SetMobility(EComponentMobility::Movable);Product->SetStaticMesh(MeshAsset);
 Product->SetCollisionEnabled(ECollisionEnabled::NoCollision);Product->AttachToComponent(GetMesh(),FAttachmentTransformRules::SnapToTargetNotIncludingScale,Hand);
 Product->SetUsingAbsoluteRotation(true);
 Product->SetUsingAbsoluteScale(true);Product->SetWorldScale3D(FVector::OneVector);
 if(Dish==TEXT("suco") || Dish==TEXT("coco_gelado") || Dish==TEXT("caipirinha") || Dish==TEXT("batida"))Product->ComponentTags.Add(TEXT("MareVessel"));
 Product->RegisterComponent();CarriedMeshes.Add(Product);
}
void AMarePerson::ClearProducts(){for(auto Part:CarriedMeshes)if(Part)Part->DestroyComponent();CarriedMeshes.Empty();}
float AMarePerson::DrinkGesture()const
{
 if(Stage!=EMarePersonStage::Eating || bConsumed || Elapsed>=7.f)return 0;
 const float Phase=FMath::Fmod(Elapsed,3.2f)/3.2f;
 return FMath::SmoothStep(.1f,.4f,Phase)*(1-FMath::SmoothStep(.65f,.95f,Phase));
}
void AMarePerson::Interact(APlayerController* Player)
{
 if(auto Kiosk=GetWorld()->GetSubsystem<UMareKioskWorld>())Kiosk->Serve(this,false);
}
void AMarePerson::ApplyOutfit(EOutfit Style)
{
 Outfit=Style;bOutfitApplied=true;if(Style==EOutfit::Uniform || Style==EOutfit::Auto)return;
 auto Body=GetMesh();if(!Body || !Body->GetSkeletalMeshAsset())return;
 static UMaterialInterface* Cloth=nullptr;static UMaterialInterface* Skin=nullptr;static UMaterialInterface* Hidden=nullptr;
 if(!Cloth)Cloth=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Actors/Combined/Shared/M_PersonOutfit.M_PersonOutfit"));
 if(!Skin)Skin=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Actors/Combined/Shared/M_PersonBody.M_PersonBody"));
 if(!Hidden)Hidden=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Actors/Combined/Shared/M_PersonHidden.M_PersonHidden"));
 if(!Cloth || !Skin || !Hidden)return;
 FRandomStream Rng(int32(FCrc::StrCrc32(*SaveId)));
 auto Pick=[&](std::initializer_list<FLinearColor> List){TArray<FLinearColor> A(List);return A[Rng.RandRange(0,A.Num()-1)];};
 // Slots of the UBC rig: 2 body, 3 shirt, 4 sleeves, 5 shoes, 6 trousers/shorts.
 auto Slot=[&](int32 Part){return Body->GetMaterialIndex(*FString::Printf(TEXT("Human_%d_material_%d"),Variant,Part));};
 auto Tex=[&](int32 Part){return LoadObject<UTexture2D>(nullptr,*FString::Printf(TEXT("/Game/Actors/Combined/Human_%d/Human_%d_texture_%d.Human_%d_texture_%d"),Variant,Variant,Part,Variant,Part));};
 auto Dye=[&](int32 Part,const FLinearColor& Color){const int32 I=Slot(Part);if(I==INDEX_NONE)return;auto M=UMaterialInstanceDynamic::Create(Cloth,this);
  if(auto T=Tex(Part))M->SetTextureParameterValue(TEXT("Atlas"),T);M->SetVectorParameterValue(TEXT("Tint"),Color);Body->SetMaterial(I,M);};
 auto Hide=[&](int32 Part){const int32 I=Slot(Part);if(I!=INDEX_NONE)Body->SetMaterial(I,Hidden);};
 const FLinearColor Bright[]={{.85f,.28f,.22f},{.95f,.74f,.18f},{.92f,.92f,.88f},{.08f,.58f,.62f},{.86f,.34f,.55f},{.52f,.74f,.24f},{.98f,.55f,.25f}};
 const FLinearColor Shorts[]={{.66f,.56f,.38f},{.12f,.16f,.32f},{.86f,.86f,.80f},{.24f,.36f,.58f},{.85f,.40f,.18f}};
 const FLinearColor Swim[]={{.86f,.12f,.22f},{.05f,.45f,.75f},{.98f,.80f,.10f},{.08f,.08f,.10f},{.92f,.42f,.62f},{.12f,.62f,.42f},{.96f,.94f,.90f}};
 switch(Style){
 case EOutfit::Swim:{
  // The garments were generated from the body mesh and keep its UVs, while the body itself has no skin
  // under them: painting every piece with the body atlas shows bare skin, and the underwear painted on
  // that atlas becomes the bikini / swim trunks in one colour (M_PersonBody).
  auto M=UMaterialInstanceDynamic::Create(Skin,this);if(auto T=Tex(2))M->SetTextureParameterValue(TEXT("Atlas"),T);
  M->SetVectorParameterValue(TEXT("SwimTint"),Swim[Rng.RandRange(0,6)]);
  for(int32 Part:{2,3,4,5,6}){const int32 I=Slot(Part);if(I!=INDEX_NONE)Body->SetMaterial(I,M);}break;}
 case EOutfit::Beach:{const FLinearColor Top=Bright[Rng.RandRange(0,6)];Dye(3,Top);Dye(4,Top);
  Dye(6,Shorts[Rng.RandRange(0,4)]);Dye(5,Pick({{.70f,.55f,.35f},{.90f,.88f,.84f},{.20f,.45f,.60f}}));break;}
 case EOutfit::Social:{const FLinearColor Top=Pick({{.93f,.93f,.91f},{.66f,.76f,.90f},{.90f,.86f,.74f},{.93f,.93f,.91f}});Dye(3,Top);Dye(4,Top);
  Dye(6,Pick({{.10f,.10f,.11f},{.08f,.10f,.20f},{.58f,.54f,.44f}}));Dye(5,Pick({{.04f,.04f,.04f},{.20f,.11f,.06f}}));break;}
 default:{const FLinearColor Top=Pick({{.55f,.62f,.70f},{.80f,.78f,.70f},{.62f,.30f,.25f},{.30f,.42f,.30f},{.85f,.84f,.80f},{.25f,.30f,.45f}});Dye(3,Top);Dye(4,Top);
  Dye(6,Shorts[Rng.RandRange(0,4)]);Dye(5,Pick({{.85f,.85f,.82f},{.35f,.25f,.18f},{.10f,.10f,.12f}}));break;}
 }
}
void AMarePerson::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);Elapsed+=DeltaSeconds;
 // Choose the outfit once the spawner has set the role: staff in uniform, hotel staff and diners in
 // social clothes, beach-goers in beach or swimwear, villagers casual.
 // MetaHumans replace the rig people once the role is known: a stable pick (save id) from the role's roster;
 // the dyed rig outfits below remain the fallback when a MetaHuman is missing or mare.MetaHumans is 0.
 if(!bOutfitApplied && Elapsed>.05f && MetaHuman.IsEmpty() && CVarMareMetaHumans.GetValueOnGameThread()){
  FString Wanted=CVarMareMetaHuman.GetValueOnGameThread();
  if(Wanted.IsEmpty()){
   const TCHAR* RoleKey=bEmployee?TEXT("staff"):Tags.Contains(TEXT("MareHotelGuest"))?TEXT("hotel"):Tags.Contains(TEXT("MarePousadaGuest"))?TEXT("pousada"):bAmbient?TEXT("village"):TEXT("beach");
   const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
   if(MetaHumanRoster()->TryGetArrayField(RoleKey,List) && List->Num())
    Wanted=(*List)[int32(FCrc::StrCrc32(*(SaveId+PersonName))%uint32(List->Num()))]->AsString();
  }
  if(!Wanted.IsEmpty())SetMetaHuman(Wanted);
 }
 if(!bOutfitApplied && Elapsed>.05f){EOutfit Style=Outfit;
  if(Style==EOutfit::Auto){FRandomStream R(int32(FCrc::StrCrc32(*SaveId))+7);
   if(bEmployee)Style=EOutfit::Uniform;
   else if(Tags.Contains(TEXT("MareHotelGuest")))Style=(PersonName==TEXT("Recepcionista") || PersonName==TEXT("Barman") || bSeated || GetActorLocation().Y>5600)?EOutfit::Social:EOutfit::Beach;
   else if(bAmbient)Style=R.FRand()<.3f?EOutfit::Beach:EOutfit::Casual;
   // Swimwear (EOutfit::Swim) stays off until the people get real garments (MetaHuman outfits):
   // painting the generated clothes with the body atlas works but looks like underwear.
   else Style=EOutfit::Beach;}
  ApplyOutfit(Style);}
 if(GetVelocity().SizeSquared2D()>25)PlayPose(TEXT("Walk"));else if(bAmbient)PlayPose(bSeated?TEXT("Sitting_Idle"):bConversing?TEXT("Idle_Talking"):TEXT("Idle"));else if(Stage!=EMarePersonStage::Eating)PlayPose(TEXT("Idle"));
}
