#include "MarePerson.h"
#include "MareServiceAnimation.h"
#include "MareServiceTarget.h"
#include "MareSimulation.h"
#include "Engine/GameInstance.h"
#include "MareKioskWorld.h"
#include "MareAudioWorld.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "NavigationSystem.h"
#include "Animation/AnimSequence.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/Texture2D.h"
#include "Components/CapsuleComponent.h"
#include "Components/ChildActorComponent.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/IConsoleManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/Skeleton.h"
#include "Materials/MaterialInterface.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

static TAutoConsoleVariable<int32> CVarMareMetaHumans(TEXT("mare.MetaHumans"),1,TEXT("People wear the built MetaHumans of Content/Data/metahumans.json (0 = original rig people)."));
static TAutoConsoleVariable<int32> CVarMareBeachwear(TEXT("mare.Beachwear"),-1,TEXT("QA: beachwear option index for new beach people (-1 = picked per person)."));
static TAutoConsoleVariable<int32> CVarMareFaces(TEXT("mare.Faces"),1,TEXT("MetaHuman faces blink and change expression (own face pose with rig curves); 0 = faces follow the body, neutral."));
static TAutoConsoleVariable<int32> CVarMareMocap(TEXT("mare.Mocap"),1,TEXT("Use the free Fab mocap clips (seated/standing talk, party dances); 0 = base clips only."));
static TAutoConsoleVariable<FString> CVarMareMetaHuman(TEXT("mare.MetaHuman"),TEXT(""),TEXT("QA: force this built MetaHuman on every new person (empty = roster choice)."));

/** Content/Data/metahumans.json: built MetaHumans per role (staff, hotel, village, beach) and swimwear colours. */
static TSharedPtr<FJsonObject> MetaHumanRoster()
{
 static TSharedPtr<FJsonObject> Roster;
 if(!Roster.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/metahumans.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Roster);if(!Roster.IsValid())Roster=MakeShared<FJsonObject>();}
 return Roster;
}

bool AMarePerson::HotelSeat(int32 Table,int32 Index,FVector& SeatTop,float& Yaw)
{
 static TSharedPtr<FJsonObject> Doc;
 if(!Doc.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/hotel_seats.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Doc);if(!Doc.IsValid())Doc=MakeShared<FJsonObject>();}
 const TArray<TSharedPtr<FJsonValue>>* Seats=nullptr;if(!Doc->TryGetArrayField(TEXT("seats"),Seats))return false;
 int32 Found=0;
 for(const auto& V:*Seats){const auto O=V->AsObject();if(!O.IsValid() || int32(O->GetNumberField(TEXT("table")))!=Table)continue;
  if(Found++!=Index)continue;
  const auto& A=O->GetArrayField(TEXT("seat"));if(A.Num()!=4)return false;
  SeatTop=FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());Yaw=A[3]->AsNumber();return true;}
 return false;
}

void AMarePerson::SitOn(const FVector& SeatTop,float Yaw)
{
 // The pelvis bone rides ~11 cm above the seat surface (kiosk diners measure 8-17 with mare_hud.seat_audit), centred
 // on the seat. Rough start: Sitting_Idle has the pelvis 30 cm behind the root and ~50 cm above it, capsule half 88.
 const FVector Forward=FRotator(0,Yaw,0).Vector();
 SeatPelvis=SeatTop+FVector(0,0,11);
 SetActorLocationAndRotation(SeatPelvis+Forward*30+FVector(0,0,-50+88),FRotator(0,Yaw,0));
 SeatAlignIn=.6f;
}

void AMarePerson::LieOn(const FVector& TowelCentre,float AxisYaw)
{
 // Face up on the towel (03/11, Sergio: "deitadas de barriga para cima"): the calm standing idle laid on its back,
 // the actor's forward (the face) pointing at the sky and its up axis (feet to head) along the towel.
 LieCentre=TowelCentre;LieYaw=AxisYaw;bLying=true;LieAlignIn=.8f;
 GetCharacterMovement()->DisableMovement();GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 SetActorLocationAndRotation(TowelCentre+FVector(0,0,12),FRotationMatrix::MakeFromXZ(FVector::UpVector,FRotator(0,AxisYaw,0).Vector()).Rotator());
}

void AMarePerson::UpdateLying(float DeltaSeconds)
{
 // The standing idles stand with one foot 37 cm behind the other, which laid down sinks a heel into the sand. The
 // first 0.17 s of the Cheer capture stands square with the hands on the chest: played slowly back and forth it is a
 // person resting on the back with the hands on the belly, breathing. Without the mocap clips, the idle.
 if(!Clips.Contains(TEXT("Cheer")))PlayPose(TEXT("Idle"));
 else{PlayPose(TEXT("Cheer"),false);
  if(auto Instance=Cast<UMareServiceAnimInstance>(GetMesh()->GetAnimInstance())){Instance->SetPlaying(false);
   Instance->SetPosition(.085f+.085f*FMath::Sin(Elapsed*.9f+FCrc::StrCrc32(*SaveId)%7),false);}}
 if(LieAlignIn>0 && (LieAlignIn-=DeltaSeconds)<=0 && GetMesh()->GetBoneIndex(TEXT("head"))!=INDEX_NONE){
  // Centre the body (head to mid-feet) on the towel and rest the pelvis 11 cm above it (the back of the hips on the cloth).
  const FVector Mid=(GetMesh()->GetSocketLocation(TEXT("foot_l"))+GetMesh()->GetSocketLocation(TEXT("foot_r")))/2;
  const FVector Centre=(GetMesh()->GetSocketLocation(TEXT("head"))+Mid)/2;
  AddActorWorldOffset(FVector(LieCentre.X-Centre.X,LieCentre.Y-Centre.Y,LieCentre.Z+11-GetMesh()->GetSocketLocation(TEXT("pelvis")).Z));}
}

// QA: "mare.Express smile|annoyed [seconds] [metres]" puts a mood on everyone near the player (face captures).
static FAutoConsoleCommandWithWorldAndArgs GMareExpress(TEXT("mare.Express"),TEXT("mare.Express <smile|annoyed> [seconds=6] [radius m=8]"),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(!World || Args.IsEmpty())return;APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);if(!Hero)return;
  const float Seconds=Args.Num()>1?FCString::Atof(*Args[1]):6.f,Radius=(Args.Num()>2?FCString::Atof(*Args[2]):8.f)*100.f;int32 Count=0;
  for(TActorIterator<AMarePerson> It(World);It;++It)if(FVector::Dist(It->GetActorLocation(),Hero->GetActorLocation())<Radius){It->Express(Args[0],Seconds);++Count;}
  UE_LOG(LogTemp,Display,TEXT("MARE_EXPRESS %s people=%d"),*Args[0],Count);}));

bool AMarePerson::IsWoman()const
{
 if(!MetaHuman.IsEmpty()){FString Base=MetaHuman;MetaHuman.Split(TEXT("_"),&Base,nullptr);
  const TArray<TSharedPtr<FJsonValue>>* Men=nullptr;
  if(MetaHumanRoster()->TryGetArrayField(TEXT("men"),Men))for(const auto& V:*Men)if(V->AsString()==Base)return false;
  return true;}
 const USkeletalMesh* Body=GetMesh()->GetSkeletalMeshAsset();
 return Body && Body->GetSkeleton() && Body->GetSkeleton()->GetPathName().Contains(TEXT("/Female/"));
}

void AMarePerson::Express(const FString& InMood,float Seconds)
{
 Mood=InMood;MoodTotal=MoodLeft=FMath::Max(Seconds,.5f);
 // A short wordless voice goes with the face (tools/ue58/fetch_murmurs.py: a little laugh, a grumble or a sigh,
 // a "hmm"), soft and from the head; nothing is ever spoken.
 const TCHAR* Kind=InMood==TEXT("smile")?TEXT("happy"):InMood==TEXT("annoyed")?TEXT("annoyed"):InMood==TEXT("hmm")?TEXT("hmm"):nullptr;
 if(!Kind)return;
 const bool bFemale=IsWoman();
 const FVector Head=GetMesh()->GetBoneIndex(TEXT("head"))!=INDEX_NONE?GetMesh()->GetSocketLocation(TEXT("head")):GetActorLocation()+FVector(0,0,70);
 UMareAudioWorld::Action(this,FString::Printf(TEXT("voice_%s_%s"),Kind,bFemale?TEXT("f"):TEXT("m")),&Head);
}

void AMarePerson::FaceCurves(TArray<TPair<FName,float>>& Out)const
{
 // Blink about every 3-6 s: 0.16 s closing and opening (BlinkAt/NextBlink advance in Tick).
 const float Since=Elapsed-BlinkAt;const float Blink=Since<.16f?FMath::Sin(Since/.16f*PI):0.f;
 if(Blink>0){Out.Add({TEXT("CTRL_expressions_eyeBlinkL"),Blink});Out.Add({TEXT("CTRL_expressions_eyeBlinkR"),Blink});}
 if(MoodLeft<=0 || Mood.IsEmpty())return;
 // Ease in over 0.4 s and out over the last 0.8 s.
 const float Gone=MoodTotal-MoodLeft;const float W=FMath::Min(FMath::SmoothStep(0.f,.4f,Gone),FMath::SmoothStep(0.f,.8f,MoodLeft));
 auto Both=[&Out,W](const TCHAR* Control,float Value){for(const TCHAR* Side:{TEXT("L"),TEXT("R")})Out.Add({FName(FString(TEXT("CTRL_expressions_"))+Control+Side),Value*W});};
 if(Mood==TEXT("smile")){Both(TEXT("mouthCornerPull"),.75f);Both(TEXT("mouthCornerWiden"),.25f);Both(TEXT("eyeCheekRaise"),.45f);Both(TEXT("eyeSquintInner"),.2f);}
 else if(Mood==TEXT("annoyed")){Both(TEXT("browDown"),.7f);Both(TEXT("browLateral"),.5f);Both(TEXT("mouthCornerDepress"),.45f);Both(TEXT("eyeSquintInner"),.35f);Both(TEXT("noseWrinkle"),.25f);}
 else if(Mood==TEXT("hmm")){Both(TEXT("browRaiseIn"),.35f);Both(TEXT("eyeSquintInner"),.15f);Both(TEXT("mouthCornerDepress"),.12f);}
}

void AMarePerson::AlignToSeatBelow()
{
 // Sitting_Idle: pelvis 30 cm behind the root, ~50 cm above it.
 const FVector Pelvis=GetActorLocation()-GetActorForwardVector()*30+FVector(0,0,-88+50);
 FHitResult Hit;FCollisionQueryParams Q(TEXT("MareSeat"),true,this);
 if(GetWorld()->LineTraceSingleByChannel(Hit,Pelvis+FVector(0,0,40),Pelvis-FVector(0,0,80),ECC_Visibility,Q)){
  SeatPelvis=FVector(Pelvis.X,Pelvis.Y,Hit.ImpactPoint.Z+11);SeatAlignIn=.6f;}
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
 if(!SeatPelvis.IsZero())SeatAlignIn=.6f;
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
/** Which roster colour a clothing material takes: the default Epic garment ("shirt"/"short") or a Fab outfit piece
 *  built into the MetaHuman (Clothing/MI_WI_*: tops and dresses = "shirt", bottoms = "short"); shoes and complete
 *  designer outfits keep their own colours (nullptr). */
static const TCHAR* FabGarmentPart(const FString& Path)
{
 if(Path.Contains(TEXT("DefaultGarment")))return Path.Contains(TEXT("_Short"))?TEXT("short"):TEXT("shirt");
 const bool bOutfit=Path.Contains(TEXT("/Clothing/MI_WI_"))|| Path.Contains(TEXT("/MetaOutfits/"))|| Path.Contains(TEXT("_Casual_"));
 if(!bOutfit)return nullptr;
 for(const TCHAR* Word:{TEXT("_shs_"),TEXT("Flipflops"),TEXT("Flats"),TEXT("Loafers"),TEXT("Slipper"),TEXT("Shoe"),TEXT("Sneaker")})if(Path.Contains(Word))return nullptr;
 if(Path.Contains(TEXT("_btm"))|| Path.Contains(TEXT("Shorts"))|| Path.Contains(TEXT("Pant")))return TEXT("short");
 return TEXT("shirt");   // tops, t-shirts, dresses, casual shirts, swimsuits
}
bool AMarePerson::SetMetaHuman(const FString& Name)
{
 const FString Root=FString::Printf(TEXT("/Game/People/MetaHumans/%s/MH_%s/"),*Name,*Name);
 auto Body=LoadObject<USkeletalMesh>(nullptr,*FString::Printf(TEXT("%sBody/SKM_MH_%s_BodyMesh.SKM_MH_%s_BodyMesh"),*Root,*Name,*Name));
 UClass* Look=LoadClass<AActor>(nullptr,*FString::Printf(TEXT("%sBP_MH_%s.BP_MH_%s_C"),*Root,*Name,*Name));
 if(!Body || !Look)return false;
 for(auto Part:HairMeshes)if(IsValid(Part))Part->DestroyComponent();HairMeshes.Empty();
 Clips.Empty();Playing.Reset();bOutfitApplied=true;MetaHuman=Name;
 if(!SeatPelvis.IsZero())SeatAlignIn=.6f;   // another body: the pelvis moves, align again
 // The rig mesh becomes the MetaHuman body skeleton and keeps driving the pose (clips retargeted from UAL
 // by mare_metahuman.retarget_clips); it stays hidden while the blueprint's body, face, clothes and grooms follow it.
 GetMesh()->SetSkeletalMeshAsset(Body);GetMesh()->SetAnimInstanceClass(UMareServiceAnimInstance::StaticClass());
 // The last three are free Fab mocap clips (mare_metahuman.import_mocap; local only, like the outfits; mare.Mocap 0
 // turns them off); missing ones fall back to the base clips.
 TArray<FString> Wanted={TEXT("Idle"),TEXT("Idle_Talking"),TEXT("Walk"),TEXT("Sitting_Idle"),TEXT("Interact")};
 if(CVarMareMocap.GetValueOnGameThread())Wanted.Append({TEXT("SitTalk"),TEXT("DanceHip"),TEXT("Cheer")});
 for(const FString& Clip:Wanted)
  if(auto Anim=LoadObject<UAnimSequence>(nullptr,*FString::Printf(TEXT("/Game/People/Animations/MH_%s.MH_%s"),*Clip,*Clip)))Clips.Add(Clip,Anim);
 GetMesh()->SetVisibility(false,false);
 // The hidden rig is never rendered itself: it must tick and refresh its bones always, or the visible body that
 // follows it freezes and the person glides along without moving legs or arms.
 GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 if(MetaHumanBody)MetaHumanBody->DestroyComponent();
 MetaHumanBody=NewObject<UChildActorComponent>(this);AddInstanceComponent(MetaHumanBody);
 MetaHumanBody->SetupAttachment(GetMesh());MetaHumanBody->SetChildActorClass(Look);MetaHumanBody->RegisterComponent();
 if(AActor* Child=MetaHumanBody->GetChildActor()){TArray<USkeletalMeshComponent*> Parts;Child->GetComponents(Parts);
  for(auto Part:Parts){Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   // Garments at full detail (mare_metahuman.hi_garments): the Medium build decimates the Fab clothes into jagged
   // necklines; the same garment from a High build is worn instead, the rest of the person stays Medium.
   if(const USkeletalMesh* Worn=Part->GetSkeletalMeshAsset())if(Worn->GetName().StartsWith(TEXT("MH_")+Name+TEXT("_Outfits"))){
    const FString Hi=FString::Printf(TEXT("/Game/People/MetaHumans/_HiGarments/%s/MH_%s/Clothing/%s.%s"),*Name,*Name,*Worn->GetName(),*Worn->GetName());
    if(auto Detailed=LoadObject<USkeletalMesh>(nullptr,*Hi))Part->SetSkeletalMeshAsset(Detailed);}
   // The face evaluates its own pose (copy of the body + blink/mood curves for RigLogic); the rest follow the body.
   if(Part->GetFName()==TEXT("Face") && CVarMareFaces.GetValueOnGameThread()){Part->SetLeaderPoseComponent(nullptr);
    Part->SetAnimInstanceClass(UMareFaceAnimInstance::StaticClass());Part->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;}
   else Part->SetLeaderPoseComponent(GetMesh());}}
 // Swim builds (<Name>_Swim, whole body) wear the bikini/trunks made for that body (tools/ue58/gen_mh_swimwear.py).
 if(Swimwear){Swimwear->DestroyComponent();Swimwear=nullptr;}
 for(auto Part:Overwear)if(IsValid(Part))Part->DestroyComponent();Overwear.Empty();
 if(Name.EndsWith(TEXT("_Swim"))){const FString Base=Name.LeftChop(5);USkeletalMesh* Garment=nullptr;
  for(const TCHAR* Kind:{TEXT("Bikini"),TEXT("Trunks")})
   if(!Garment)Garment=LoadObject<USkeletalMesh>(nullptr,*FString::Printf(TEXT("/Game/People/Swimwear/SKM_%s_%s.SKM_%s_%s"),Kind,*Base,Kind,*Base));
  if(Garment){Swimwear=NewObject<USkeletalMeshComponent>(this);AddInstanceComponent(Swimwear);Swimwear->SetupAttachment(GetMesh());
   Swimwear->SetSkeletalMeshAsset(Garment);Swimwear->SetCollisionEnabled(ECollisionEnabled::NoCollision);Swimwear->RegisterComponent();
   Swimwear->SetLeaderPoseComponent(GetMesh());
   const TArray<TSharedPtr<FJsonValue>>* Colours=nullptr;
   if(MetaHumanRoster()->TryGetArrayField(TEXT("swim_colours"),Colours) && Colours->Num()){
    const FColor C=FColor::FromHex((*Colours)[int32(FCrc::StrCrc32(*SaveId)%uint32(Colours->Num()))]->AsString());
    for(int32 I=0;I<Swimwear->GetNumMaterials();++I)if(auto M=Swimwear->CreateDynamicMaterialInstance(I))M->SetVectorParameterValue(TEXT("Tint"),FLinearColor(C));}}
  // Beachwear over the swimwear (tools/ue58/gen_mh_swimwear.py tank|boardshorts|coverup, fitted to this body): one of
  // the person's options in metahumans.json "beachwear" ("" = swimwear only, "tank+boardshorts" = both), each piece in
  // a colour of "beachwear_colours". Board shorts replace the trunks.
  for(auto Part:Overwear)if(IsValid(Part))Part->DestroyComponent();Overwear.Empty();
  const TSharedPtr<FJsonObject>* Wear=nullptr;const TArray<TSharedPtr<FJsonValue>>* Options=nullptr;
  if(MetaHumanRoster()->TryGetObjectField(TEXT("beachwear"),Wear) && (*Wear)->TryGetArrayField(Base,Options) && Options->Num()){
   const int32 Forced=CVarMareBeachwear.GetValueOnGameThread();
   const int32 Pick=Forced>=0?Forced%Options->Num():int32(FCrc::StrCrc32(*(SaveId+TEXT("wear")))%uint32(Options->Num()));
   TArray<FString> Kinds;(*Options)[Pick]->AsString().ParseIntoArray(Kinds,TEXT("+"));
   const TArray<TSharedPtr<FJsonValue>>* Colours=nullptr;MetaHumanRoster()->TryGetArrayField(TEXT("beachwear_colours"),Colours);
   for(const FString& Kind:Kinds){const FString Asset=Kind.Left(1).ToUpper()+Kind.Mid(1);
    auto Piece=LoadObject<USkeletalMesh>(nullptr,*FString::Printf(TEXT("/Game/People/Swimwear/SKM_%s_%s.SKM_%s_%s"),*Asset,*Base,*Asset,*Base));if(!Piece)continue;
    auto Part=NewObject<USkeletalMeshComponent>(this);AddInstanceComponent(Part);Part->SetupAttachment(GetMesh());Part->SetSkeletalMeshAsset(Piece);
    Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);Part->RegisterComponent();Part->SetLeaderPoseComponent(GetMesh());
    if(Colours && Colours->Num()){const FColor C=FColor::FromHex((*Colours)[int32(FCrc::StrCrc32(*(SaveId+Kind))%uint32(Colours->Num()))]->AsString());
     for(int32 I=0;I<Part->GetNumMaterials();++I)if(auto M=Part->CreateDynamicMaterialInstance(I))M->SetVectorParameterValue(TEXT("Tint"),FLinearColor(C));}
    if(Kind==TEXT("boardshorts") && Swimwear && Swimwear->GetSkeletalMeshAsset() && Swimwear->GetSkeletalMeshAsset()->GetName().Contains(TEXT("Trunks")))Swimwear->SetVisibility(false);
    Overwear.Add(Part);}}}
 const bool bSwim=Name.EndsWith(TEXT("_Swim"));const FString RoleKey=bSwim?TEXT("swim"):MetaRole.IsEmpty()?TEXT("village"):MetaRole;
 auto Pick=[this](const TArray<TSharedPtr<FJsonValue>>& List,const TCHAR* Salt,int32 First=0){
  return FLinearColor(FColor::FromHex(List[First+int32(FCrc::StrCrc32(*(SaveId+Salt))%uint32(List.Num()-First))]->AsString()));};
 // Default Epic garment (white shirt/shorts): colours per role from the roster (uniform for staff).
 const TSharedPtr<FJsonObject>* Clothes=nullptr;const TSharedPtr<FJsonObject>* Palette=nullptr;
 if(!bSwim && MetaHumanRoster()->TryGetObjectField(TEXT("clothes"),Clothes) && (*Clothes)->TryGetObjectField(RoleKey,Palette))
  if(AActor* Child=MetaHumanBody->GetChildActor()){TArray<UMeshComponent*> Garments;Child->GetComponents(Garments);
   for(UMeshComponent* Garment:Garments)for(int32 I=0;I<Garment->GetNumMaterials();++I){const UMaterialInterface* Mat=Garment->GetMaterial(I);
    if(!Mat)continue;const TCHAR* Part=FabGarmentPart(Mat->GetPathName());if(!Part)continue;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
    if(!(*Palette)->TryGetArrayField(Part,List) || !List->Num())continue;
    if(auto M=Garment->CreateDynamicMaterialInstance(I)){const FLinearColor C=Pick(*List,Part);
     // Parameter names differ per outfit: Epic garments (diffuse_color_*), the mini dress (Color1/2, sleeves) and the
     // casual sets (Color_Base); unknown names are ignored by the material.
     for(const TCHAR* P:{TEXT("diffuse_color_1"),TEXT("diffuse_color_2"),TEXT("B_diffuse_color_1"),TEXT("Color1"),TEXT("Color2"),
      TEXT("Color1Sleeve"),TEXT("Color2Sleeve"),TEXT("Color_Base")})M->SetVectorParameterValue(P,C);}}}
 // Footwear fitted in Blender to a woman's or a man's MetaHuman foot (tools/ue58/gen_mh_shoes.py): nobody barefoot.
 // Builds dressed with Fab outfits (Content/Data/outfits_fab.json) bring their own shoes: no generated pair then.
 if(Shoes){Shoes->DestroyComponent();Shoes=nullptr;}
 bool bOutfitShoes=false;
 if(AActor* Child=MetaHumanBody?MetaHumanBody->GetChildActor():nullptr){TArray<UMeshComponent*> Parts;Child->GetComponents(Parts);
  for(UMeshComponent* Part:Parts)for(int32 I=0;I<Part->GetNumMaterials();++I)if(const UMaterialInterface* Mat=Part->GetMaterial(I)){
   const FString Path=Mat->GetPathName();
   for(const TCHAR* Word:{TEXT("_shs_"),TEXT("Flipflops"),TEXT("Flats"),TEXT("Loafers"),TEXT("Sneaker"),TEXT("Shoe"),TEXT("Slipper"),TEXT("Casual_")})if(Path.Contains(Word))bOutfitShoes=true;}}
 if(bOutfitShoes){PlayPose(TEXT("Idle"));return true;}
 const TSharedPtr<FJsonObject>* ShoeKinds=nullptr;FString Kind;
 const TArray<TSharedPtr<FJsonValue>>* KindList=nullptr;
 if(MetaHumanRoster()->TryGetObjectField(TEXT("shoes"),ShoeKinds) && (*ShoeKinds)->TryGetArrayField(RoleKey,KindList) && KindList->Num())
  Kind=(*KindList)[int32(FCrc::StrCrc32(*(SaveId+TEXT("feet")))%uint32(KindList->Num()))]->AsString();
 if(!Kind.IsEmpty()){
  const TCHAR* Foot=IsWoman()?TEXT("Ada"):TEXT("Mateo");
  if(auto Pair=LoadObject<USkeletalMesh>(nullptr,*FString::Printf(TEXT("/Game/People/Swimwear/SKM_%s_%s.SKM_%s_%s"),*Kind,Foot,*Kind,Foot))){
   Shoes=NewObject<USkeletalMeshComponent>(this);AddInstanceComponent(Shoes);Shoes->SetupAttachment(GetMesh());
   Shoes->SetSkeletalMeshAsset(Pair);Shoes->SetCollisionEnabled(ECollisionEnabled::NoCollision);Shoes->RegisterComponent();
   Shoes->SetLeaderPoseComponent(GetMesh());
   const TSharedPtr<FJsonObject>* Colours=nullptr;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
   if(MetaHumanRoster()->TryGetObjectField(TEXT("shoe_colours"),Colours) && (*Colours)->TryGetArrayField(Kind,List) && List->Num()>1){
    // Slot 0 = upper or strap, slot 1 = sole (first colour of the list).
    if(auto M=Shoes->CreateDynamicMaterialInstance(0))M->SetVectorParameterValue(TEXT("Tint"),Pick(*List,TEXT("shoe"),1));
    if(auto M=Shoes->CreateDynamicMaterialInstance(1))M->SetVectorParameterValue(TEXT("Tint"),FLinearColor(FColor::FromHex((*List)[0]->AsString())));}}}
 PlayPose(TEXT("Idle"));return true;
}
void AMarePerson::PlayPose(const FString& Name,bool bLoop)
{
 if(Playing==Name || !Clips.Contains(Name))return;Playing=Name;
 // Variety: half of the guests (fixed per person) talk with their hands while seated. Staff and anyone riding
 // something (the bus driver) keep the calm base clip.
 FString Clip=Name;
 const bool bVaried=!bEmployee && !GetAttachParentActor() && FCrc::StrCrc32(*(SaveId+PersonName))%2;
 if(bVaried && Name==TEXT("Sitting_Idle") && Clips.Contains(TEXT("SitTalk")))Clip=TEXT("SitTalk");
 if(auto Instance=Cast<UMareServiceAnimInstance>(GetMesh()->GetAnimInstance())){Instance->SetAnimationAsset(Clips[Clip],bLoop);Instance->SetPlaying(true);}
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
 if(MoodLeft>0)MoodLeft-=DeltaSeconds;
 if(Elapsed>=NextBlink){BlinkAt=Elapsed;NextBlink=Elapsed+FMath::FRandRange(2.8f,6.f);}
 if(SeatAlignIn>0 && (SeatAlignIn-=DeltaSeconds)<=0 && Playing==TEXT("Sitting_Idle") && GetMesh()->GetBoneIndex(TEXT("pelvis"))!=INDEX_NONE){
  // Shift the whole actor so the animated pelvis sits on the seat point (heights and proportions differ per body).
  AddActorWorldOffset(SeatPelvis-GetMesh()->GetSocketLocation(TEXT("pelvis")));}
 else if(SeatAlignIn<=0 && !SeatPelvis.IsZero() && !Playing.IsEmpty() && Playing!=TEXT("Sitting_Idle"))SeatPelvis=FVector::ZeroVector;   // stood up
 if(SeatPelvis.IsZero())bTableAhead=false;
 else if(SeatAlignIn<=0 && !SeatPelvis.Equals(TableSeat,1.f)){
  // Once per seat: walk a vertical probe forward from the pelvis; the first surface 8-45 cm above the pelvis is the
  // table (or counter) top, and that distance is its near edge. The chair itself is below the pelvis and ignored.
  TableSeat=SeatPelvis;bTableAhead=false;const FVector Forward=GetActorForwardVector();FCollisionQueryParams Q(TEXT("MareTable"),true,this);
  for(float Ahead=15;Ahead<=75 && !bTableAhead;Ahead+=5){FHitResult Hit;const FVector At=SeatPelvis+Forward*Ahead;
   if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,60),At-FVector(0,0,5),ECC_Visibility,Q)){const float Rise=Hit.ImpactPoint.Z-SeatPelvis.Z;
    if(Rise>8 && Rise<45){bTableAhead=true;TableTopZ=Hit.ImpactPoint.Z;TableEdge=Ahead;}}}}
 // Choose the outfit once the spawner has set the role: staff in uniform, hotel staff and diners in
 // social clothes, beach-goers in beach or swimwear, villagers casual.
 // MetaHumans replace the rig people once the role is known: a stable pick (save id) from the role's roster;
 // the dyed rig outfits below remain the fallback when a MetaHuman is missing or mare.MetaHumans is 0.
 if(!bOutfitApplied && Elapsed>.05f && MetaHuman.IsEmpty() && CVarMareMetaHumans.GetValueOnGameThread()){
  FString Wanted=CVarMareMetaHuman.GetValueOnGameThread();
  if(Wanted.IsEmpty()){
   FString RoleKey=bEmployee?TEXT("staff"):Tags.Contains(TEXT("MareBather"))?TEXT("beach"):Tags.Contains(TEXT("MareHotelGuest"))?TEXT("hotel"):Tags.Contains(TEXT("MarePousadaGuest"))?TEXT("pousada"):bAmbient?TEXT("village"):TEXT("beach");
   if(bEmployee && !StaffRole.IsEmpty() && MetaHumanRoster()->HasField(TEXT("staff_")+StaffRole))RoleKey=TEXT("staff_")+StaffRole;
   const TArray<TSharedPtr<FJsonValue>>* List=nullptr;TArray<TSharedPtr<FJsonValue>> Swimmers;
   // Sunbathers lie on their towels in swimwear: only the whole-body swim builds of the beach roster.
   if(Tags.Contains(TEXT("MareBather")) && MetaHumanRoster()->TryGetArrayField(RoleKey,List)){
    for(const auto& V:*List)if(V->AsString().Contains(TEXT("_Swim")))Swimmers.Add(V);if(Swimmers.Num())List=&Swimmers;}
   if((List || MetaHumanRoster()->TryGetArrayField(RoleKey,List)) && List->Num())
    Wanted=(*List)[int32(FCrc::StrCrc32(*(SaveId+PersonName))%uint32(List->Num()))]->AsString();
   MetaRole=RoleKey;
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
 if(bEmployee && !StaffRole.IsEmpty() && !Badge && !MetaHuman.IsEmpty() && Elapsed>.6f)AttachBadge();
 if(bLying)UpdateLying(DeltaSeconds);
 else if(GetVelocity().SizeSquared2D()>25)PlayPose(TEXT("Walk"));else if(!WorkPose.IsEmpty())PlayPose(WorkPose);else if(bAmbient)PlayPose(bSeated?TEXT("Sitting_Idle"):bConversing?TEXT("Idle_Talking"):TEXT("Idle"));else if(Stage!=EMarePersonStage::Eating)PlayPose(TEXT("Idle"));
}
void AMarePerson::AttachBadge()
{
 // Model: tools/ue58/gen_staff_badge.py (front +Y, origin at the back). Placed once in the actor's frame on the left
 // chest, then kept relative to spine_05 so it follows breathing and walking.
 static UStaticMesh* BadgeMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Custom/Staff/mare_staff_badge/mare_staff_badge.mare_staff_badge"));
 const FName Bone=TEXT("spine_05");
 if(!BadgeMesh || !GetMesh()->GetSkeletalMeshAsset() || GetMesh()->GetBoneIndex(Bone)==INDEX_NONE){Badge=NewObject<UStaticMeshComponent>(this);return;}   // no retry every tick
 const bool bFemale=IsWoman();
 Badge=NewObject<UStaticMeshComponent>(this);AddInstanceComponent(Badge);Badge->SetStaticMesh(BadgeMesh);
 Badge->SetCollisionEnabled(ECollisionEnabled::NoCollision);Badge->SetCastShadow(false);
 Badge->SetupAttachment(GetMesh(),Bone);Badge->RegisterComponent();
 const FVector Chest=GetMesh()->GetSocketLocation(Bone);
 const FVector At=Chest+GetActorForwardVector()*(bFemale?BadgeFemaleAhead:BadgeMaleAhead)-GetActorRightVector()*9.f+FVector(0,0,bFemale?-6.f:-3.f);
 Badge->SetWorldLocationAndRotation(At,FRotator(0,GetActorRotation().Yaw-90,0));
}

