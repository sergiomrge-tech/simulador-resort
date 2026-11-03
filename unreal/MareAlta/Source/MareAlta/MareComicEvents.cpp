#include "MareComicEvents.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MareVillageWorld.h"
#include "MarePreviewQA.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

static TAutoConsoleVariable<float> CVarGullAt(TEXT("mare.GullAt"),-1.f,TEXT("QA: holds the HUM-001 seagull at this many seconds of its flight (-1 = normal)."));
static TAutoConsoleVariable<int32> CVarComicSeed(TEXT("mare.ComicSeed"),0,TEXT("QA: seed of the comic-event roll (0 = time)."));
static FAutoConsoleCommandWithWorldAndArgs ComicQACommand(TEXT("mare.Comic"),TEXT("QA: starts a comic event now (comic_events.json id, e.g. HUM-005)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(World && Args.Num())if(auto Comic=World->GetSubsystem<UMareComicEvents>())Comic->Force(Args[0]);}));

// QA (QA profile only): a customer eating fries 2.5 m in front of the player, for HUM-001 without waiting for the kiosk.
// "mare.ComicDiner seated [dish]" hands the food to the seated person nearest the player instead (a customer at a table).
static FAutoConsoleCommandWithWorldAndArgs ComicDinerCommand(TEXT("mare.ComicDiner"),TEXT("QA: a customer eating fries near the player ('seated [dish]': the nearest seated person)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  APawn* Hero=World?UGameplayStatics::GetPlayerPawn(World,0):nullptr;if(!Hero)return;
  FString Profile;FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),Profile);Profile.ReplaceInline(TEXT("\\"),TEXT("/"));
  if(!Profile.StartsWith(TEXT("D:/CodexTemp/")))return;
  if(Args.Num() && Args[0]==TEXT("seated")){
   const FString Dish=Args.Num()>1?Args[1]:FString(TEXT("batata_frita"));AMarePerson* Best=nullptr;
   for(TActorIterator<AMarePerson> It(World);It;++It)if(It->bSeated && It->StaffRole.IsEmpty() && (!Best || FVector::Dist(It->GetActorLocation(),Hero->GetActorLocation())<FVector::Dist(Best->GetActorLocation(),Hero->GetActorLocation())))Best=*It;
   if(Best){Best->ClearProducts();Best->HoldProduct(Dish);Best->Stage=EMarePersonStage::Eating;Best->bConsumed=false;Best->Delivered.Add(Dish);
    UE_LOG(LogTemp,Display,TEXT("Maré ComicDiner seated %s at %s"),*Best->GetName(),*Best->GetActorLocation().ToString());}
   return;}
  AMarePreviewQA::SpawnInspectionPerson(World,Hero->GetActorLocation()+Hero->GetActorForwardVector()*250.f,1,Args.Num()?Args[0]:FString(TEXT("batata_frita")));}));

TStatId UMareComicEvents::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareComicEvents,STATGROUP_Tickables);}

bool UMareComicEvents::IsDue(const TSharedPtr<FJsonObject>& Comic,const FString& Id,double Now,double Cooldown,double GlobalGap)
{
 if(!Comic.IsValid())return true;
 double Any=-1e9,Last=-1e9;Comic->TryGetNumberField(TEXT("last_any"),Any);
 const TSharedPtr<FJsonObject>* LastOf=nullptr;if(Comic->TryGetObjectField(TEXT("last"),LastOf))(*LastOf)->TryGetNumberField(Id,Last);
 return Now-Any>=GlobalGap && Now-Last>=Cooldown;
}
void UMareComicEvents::MarkStarted(const TSharedPtr<FJsonObject>& Comic,const FString& Id,double Now)
{
 if(!Comic.IsValid())return;Comic->SetNumberField(TEXT("last_any"),Now);
 UMareSimulation::Object(Comic,TEXT("last"))->SetNumberField(Id,Now);
}
int32 UMareComicEvents::LineIndex(const TSharedPtr<FJsonObject>& Comic,const FString& Id,int32 Lines,bool bSequence,int32 Roll)
{
 if(Lines<=0)return 0;
 if(!bSequence)return FMath::Abs(Roll)%Lines;
 double Seen=0;const TSharedPtr<FJsonObject>* Count=nullptr;if(Comic.IsValid() && Comic->TryGetObjectField(TEXT("count"),Count))(*Count)->TryGetNumberField(Id,Seen);
 return FMath::Min(int32(Seen),Lines-1);   // the last story stays the punchline once they run out
}

bool UMareComicEvents::Load()
{
 if(Defs.IsValid())return true;
 FString Text;if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/comic_events.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs))return false;
 const int32 Seed=CVarComicSeed.GetValueOnGameThread();Rng.Initialize(Seed?Seed:int32(FDateTime::Now().GetTicks()%INT32_MAX));
 return Defs.IsValid();
}
TSharedPtr<FJsonObject> UMareComicEvents::EventDef(const FString& Id)const
{
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(!Defs.IsValid() || !Defs->TryGetArrayField(TEXT("events"),List))return nullptr;
 for(const auto& V:*List)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==Id)return V->AsObject();
 return nullptr;
}

void UMareComicEvents::Tick(float DeltaSeconds)
{
 UWorld* World=GetWorld();if(!World || !World->IsGameWorld() || !Cast<AMareGameMode>(World->GetAuthGameMode()) || !Load())return;
 auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);if(!Hero)return;
 if(!Active.IsEmpty() && IsValid(Gull)){UpdateGull(DeltaSeconds);return;}
 if(!Active.IsEmpty() && IsValid(Umbrella)){UpdateUmbrella(DeltaSeconds);return;}
 if(!Active.IsEmpty() && Clumsy.IsValid()){UpdateClumsy(DeltaSeconds);return;}
 if(!Active.IsEmpty()){
  AMarePerson* P=Caller.Get();if(!P){Finish(false);return;}
  if(!bTalking){   // keep facing the player and calling; ignored for long enough, the caller moves on
   FVector To=Hero->GetActorLocation()-P->GetActorLocation();To.Z=0;if(!To.IsNearlyZero())P->SetActorRotation(To.Rotation());
   Waited+=DeltaSeconds;if(Waited>UMareSimulation::Number(EventDef(Active),TEXT("wait_seconds"),40) || FVector::Dist2D(P->GetActorLocation(),Hero->GetActorLocation())>2500)Finish(false);}
  return;}
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=UMareSimulation::Number(Defs,TEXT("check_seconds"),10);
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(World,0));if(!PC || PC->bPhoneOpen)return;
 if(auto Village=World->GetSubsystem<UMareVillageWorld>())if(Village->IsDialogueOpen())return;
 if(auto C=Cast<ACharacter>(Hero))if(C->GetCharacterMovement() && C->GetCharacterMovement()->IsSwimming())return;
 const double Minutes=UMareSimulation::Number(Sim->State,TEXT("minutes")),Now=UMareSimulation::Number(Sim->State,TEXT("day"),1)*1440+Minutes;
 auto Comic=UMareSimulation::Object(Sim->State,TEXT("comic"));
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(!Defs->TryGetArrayField(TEXT("events"),List))return;
 for(const auto& V:*List){auto Def=V->AsObject();const FString Id=UMareSimulation::String(Def,TEXT("id"));
  const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;if(Def->TryGetArrayField(TEXT("hours"),Hours) && Hours->Num()==2 && (Minutes<(*Hours)[0]->AsNumber()*60 || Minutes>=(*Hours)[1]->AsNumber()*60))continue;
  double MaxY=0;if(Def->TryGetNumberField(TEXT("max_y"),MaxY) && Hero->GetActorLocation().Y>MaxY)continue;   // e.g. the lost tourist: on the beach side only
  if(!IsDue(Comic,Id,Now,UMareSimulation::Number(Def,TEXT("cooldown_minutes"),360),UMareSimulation::Number(Defs,TEXT("global_gap_minutes"),90)))continue;
  if(Rng.FRand()>UMareSimulation::Number(Def,TEXT("odds"),.1))continue;
  if(Start(Def,false))return;}
}

bool UMareComicEvents::Force(const FString& Id)
{
 if(!Load() || !Active.IsEmpty())return false;
 auto Def=EventDef(Id);return Def.IsValid() && Start(Def,true);
}

bool UMareComicEvents::Start(const TSharedPtr<FJsonObject>& Def,bool bForced)
{
 const FString Kind=UMareSimulation::String(Def,TEXT("kind"));
 if(Kind==TEXT("gull"))return StartGull(Def,bForced);
 if(Kind==TEXT("umbrella"))return StartUmbrella(Def,bForced);
 if(Kind==TEXT("clumsy"))return StartClumsy(Def,bForced);
 UWorld* World=GetWorld();APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);auto Village=World->GetSubsystem<UMareVillageWorld>();
 auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Hero || !Village || !Sim)return false;
 const float Wait=UMareSimulation::Number(Def,TEXT("wait_seconds"),40);
 AMarePerson* P=Village->HoldPedestrianNear(Hero->GetActorLocation(),UMareSimulation::Number(Defs,TEXT("near_min"),250),bForced?2000.f:UMareSimulation::Number(Defs,TEXT("near_max"),900),Wait+5);
 if(!P)return false;
 const FString Id=UMareSimulation::String(Def,TEXT("id"));auto Comic=UMareSimulation::Object(Sim->State,TEXT("comic"));
 auto Strings=[&](const TCHAR* Field){TArray<FString> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(Def->TryGetArrayField(Field,L))for(const auto& V:*L)Out.Add(V->AsString());return Out;};
 const TArray<FString> Asks=Strings(TEXT("asks"));Replies=Strings(TEXT("replies"));Reactions=Strings(TEXT("reactions"));
 bool bSequence=false;Def->TryGetBoolField(TEXT("sequence"),bSequence);
 Line=Asks.IsValidIndex(0)?Asks[LineIndex(Comic,Id,Asks.Num(),bSequence,Rng.RandHelper(1000))]:FString();
 SpeakerName=UMareSimulation::String(Def,TEXT("speaker"));SavedName=P->PersonName;P->PersonName=SpeakerName;
 const double Now=UMareSimulation::Number(Sim->State,TEXT("day"),1)*1440+UMareSimulation::Number(Sim->State,TEXT("minutes"));MarkStarted(Comic,Id,Now);
 // A floating call to action on the caller, like the residents' "conversar".
 CallTarget=World->SpawnActor<AMareServiceTarget>();
 if(CallTarget){CallTarget->Action=TEXT("Comic");CallTarget->Label=SpeakerName+TEXT(" · está chamando você");CallTarget->Reach=300;CallTarget->OcclusionTolerance=40;CallTarget->SetOwner(P);
  CallTarget->AttachToActor(P,FAttachmentTransformRules::SnapToTargetNotIncludingScale);CallTarget->SetActorRelativeLocation(FVector(0,0,38));}
 // A prop in hand while calling (the influencer's phone held up for a selfie): mesh, socket, location, rotation, scale.
 const TSharedPtr<FJsonObject>* PropDef=nullptr;
 if(Def->TryGetObjectField(TEXT("prop"),PropDef))if(UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(*PropDef,TEXT("mesh")))){
  auto V3=[&](const TCHAR* F){const TArray<TSharedPtr<FJsonValue>>* A=nullptr;return (*PropDef)->TryGetArrayField(F,A) && A->Num()==3?FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),(*A)[2]->AsNumber()):FVector::ZeroVector;};
  const FVector R=V3(TEXT("rotation"));
  Prop=NewObject<UStaticMeshComponent>(P);Prop->SetStaticMesh(Mesh);Prop->SetCollisionEnabled(ECollisionEnabled::NoCollision);Prop->SetMobility(EComponentMobility::Movable);
  Prop->SetupAttachment(P->GetMesh(),FName(*UMareSimulation::String(*PropDef,TEXT("socket"))));
  Prop->SetRelativeTransform(FTransform(FRotator(R.X,R.Y,R.Z),V3(TEXT("location")),FVector(UMareSimulation::Number(*PropDef,TEXT("scale"),1))));Prop->RegisterComponent();
  bool bSelfie=false;(*PropDef)->TryGetBoolField(TEXT("selfie"),bSelfie);if(bSelfie)P->SelfiePhone=Prop;}
 Active=Id;Caller=P;Waited=0;bTalking=false;
 UE_LOG(LogTemp,Display,TEXT("Maré comic event %s started (%s)"),*Id,bForced?TEXT("forced"):TEXT("roll"));
 return true;
}

void UMareComicEvents::Interact(APlayerController* Controller)
{
 if(IsValid(Umbrella)){if(UmbrellaPhase==1){UmbrellaPhase=2;UmbrellaTime=0;UmbrellaFrom=Umbrella->GetActorTransform();
   if(IsValid(CallTarget))CallTarget->Destroy();CallTarget=nullptr;}return;}
 AMarePerson* P=Caller.Get();auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>();if(!P || !Village || bTalking || Active.IsEmpty())return;
 bTalking=true;const TWeakObjectPtr<UMareComicEvents> Weak(this);const TArray<FString> R=Reactions;
 Village->Quip(P,Controller,SpeakerName,Line,Replies,[R](int32 I){return R.IsValidIndex(I)?R[I]:FString();},[Weak](){if(Weak.IsValid())Weak->Finish(true);});
}

void UMareComicEvents::Finish(bool bTalked)
{
 UWorld* World=GetWorld();
 if(IsValid(Gull))Gull->Destroy();Gull=nullptr;Bite=nullptr;Victim.Reset();
 if(AMarePerson* P=Caller.Get())P->SelfiePhone=nullptr;
 if(IsValid(Prop))Prop->DestroyComponent();Prop=nullptr;
 RestoreUmbrella();RestoreClumsy();
 if(AMarePerson* P=Caller.Get()){P->PersonName=SavedName;if(World)if(auto Village=World->GetSubsystem<UMareVillageWorld>())Village->ReleasePedestrian(P);}
 if(IsValid(CallTarget))CallTarget->Destroy();CallTarget=nullptr;
 if(bTalked && World)if(auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>()){
  auto Count=UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("comic")),TEXT("count"));Count->SetNumberField(Active,UMareSimulation::Number(Count,Active)+1);}
 UE_LOG(LogTemp,Display,TEXT("Maré comic event %s resolved (%s)"),*Active,bTalked?TEXT("talked"):TEXT("ignored"));
 LastResolved=Active;Active.Empty();Caller.Reset();bTalking=false;
}

void UMareComicEvents::Deinitialize(){if(!Active.IsEmpty())Finish(false);Super::Deinitialize();}

// The swoop: ease in along a curve that dips under the straight line (approach), straight and accelerating (away).
static FVector GullArc(const FVector& A,const FVector& B,float U){const float E=FMath::InterpEaseInOut(0.f,1.f,FMath::Clamp(U,0.f,1.f),2.f);FVector X=FMath::Lerp(A,B,E);X.Z-=FMath::Sin(E*PI)*250.f;return X;}
static FVector GullOut(const FVector& A,const FVector& B,float U){return FMath::Lerp(A,B,FMath::InterpEaseIn(0.f,1.f,FMath::Clamp(U,0.f,1.f),2.f));}
// Where the food is and where the gull hovers: beside it on the side away from the customer. The model's body sits 24 cm above
// its origin and the beak 33 cm ahead (local +Y), so the origin goes a little below the food and the beak dips onto it.
static bool GullHover(AMarePerson* V,FVector& Food,FVector& Side,FVector& Hover)
{
 if(!V || V->CarriedMeshes.IsEmpty() || !IsValid(V->CarriedMeshes[0]))return false;
 Food=V->CarriedMeshes[0]->GetComponentLocation();Side=(Food-V->GetActorLocation()).GetSafeNormal2D();if(Side.IsNearlyZero())Side=FVector(0,-1,0);
 Hover=Food+Side*40.f+FVector(0,0,-6);return true;
}

bool UMareComicEvents::StartGull(const TSharedPtr<FJsonObject>& Def,bool bForced)
{
 // Customers eating one of the listed foods (any food when forced, for QA), closest to the player first, so the player sees it.
 UWorld* World=GetWorld();APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Hero || !Sim)return false;
 TArray<FString> Foods;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(Def->TryGetArrayField(TEXT("foods"),L))for(const auto& V:*L)Foods.Add(V->AsString());
 TArray<AMarePerson*> Candidates;
 for(TActorIterator<AMarePerson> It(World);It;++It){AMarePerson* P=*It;
  if(P->Stage!=EMarePersonStage::Eating || P->bConsumed || !P->StaffRole.IsEmpty() || P->CarriedMeshes.IsEmpty() || !IsValid(P->CarriedMeshes[0]))continue;
  if(FVector::Dist2D(P->GetActorLocation(),Hero->GetActorLocation())>3000)continue;
  bool bFood=bForced;for(const FString& D:P->Delivered)if(Foods.Contains(D))bFood=true;
  if(bFood)Candidates.Add(P);}
 Candidates.Sort([&](const AMarePerson& A,const AMarePerson& B){return FVector::DistSquared2D(A.GetActorLocation(),Hero->GetActorLocation())<FVector::DistSquared2D(B.GetActorLocation(),Hero->GetActorLocation());});
 // Open sky only: the whole flight (curved approach and the way out) must be clear of roofs, umbrellas and walls,
 // so a customer under the kiosk roof or a parasol is safe. Approach headings from the sea side (-Y) first.
 AMarePerson* Target=nullptr;FVector From=FVector::ZeroVector,Away=FVector::ZeroVector;
 for(AMarePerson* P:Candidates){FVector Food,Side,Hover;if(!GullHover(P,Food,Side,Hover))continue;
  FCollisionQueryParams Query(TEXT("MareGull"),false);Query.AddIgnoredActor(Hero);Query.AddIgnoredActor(P);
  // A 40 cm sphere (the wings) along the flight; a thin line only within 1.1 m of the food.
  auto Clear=[&](TFunctionRef<FVector(float)> Path){FVector Prev=Path(0);for(int32 S=1;S<=14;++S){const FVector X=Path(S/14.f);
    const bool bClose=FMath::Min(FVector::Dist(Prev,Hover),FVector::Dist(X,Hover))<110.f;
    if(bClose?World->LineTraceTestByChannel(Prev,X,ECC_Visibility,Query):World->SweepTestByChannel(Prev,X,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(40.f),Query))return false;Prev=X;}return true;};
  for(int32 K=0;K<8 && !Target;++K){
   const float A=FMath::DegreesToRadians(-90.f+(K%2?1:-1)*((K+1)/2)*45.f);const FVector In(FMath::Cos(A),FMath::Sin(A),0);
   // leave away from the customer, not over their head
   const float First=In.RotateAngleAxis(110.f,FVector::UpVector).Dot(Side)>=In.RotateAngleAxis(-110.f,FVector::UpVector).Dot(Side)?110.f:-110.f;
   for(const float Turn:{First,-First}){
    const FVector F=Hover+In*1800.f+FVector(0,0,900),W=Hover+In.RotateAngleAxis(Turn,FVector::UpVector)*2400.f+FVector(0,0,1100);
    if(Clear([&](float U){return GullArc(F,Hover,U);}) && Clear([&](float U){return GullOut(Hover,W,U);})){Target=P;From=F;Away=W;break;}}}
  if(Target)break;}
 if(!Target)return false;
 UStaticMesh* GullMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/World/Models/World_0536/World_0536/StaticMeshes/World_0536.World_0536"));if(!GullMesh)return false;
 FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 Gull=World->SpawnActor<AStaticMeshActor>(From,FRotator::ZeroRotator,P);if(!Gull)return false;
 Gull->SetMobility(EComponentMobility::Movable);Gull->GetStaticMeshComponent()->SetStaticMesh(GullMesh);Gull->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 Gull->SetActorScale3D(FVector(1.15f));   // the model is a real-size gull (1.1 m span); 1.15 = herring gull
 GullFrom=From;GullAway=Away;GullTime=0;bBitten=false;Victim=Target;
 auto Strings=[&](const TCHAR* Field){TArray<FString> Out;const TArray<TSharedPtr<FJsonValue>>* S=nullptr;if(Def->TryGetArrayField(Field,S))for(const auto& V:*S)Out.Add(V->AsString());return Out;};
 const TArray<FString> Asks=Strings(TEXT("asks"));const FString Id=UMareSimulation::String(Def,TEXT("id"));auto Comic=UMareSimulation::Object(Sim->State,TEXT("comic"));
 SpeakerName=UMareSimulation::String(Def,TEXT("speaker"));Line=Asks.IsValidIndex(0)?Asks[LineIndex(Comic,Id,Asks.Num(),false,Rng.RandHelper(1000))]:FString();
 MarkStarted(Comic,Id,UMareSimulation::Number(Sim->State,TEXT("day"),1)*1440+UMareSimulation::Number(Sim->State,TEXT("minutes")));
 Active=Id;Waited=0;
 UE_LOG(LogTemp,Display,TEXT("Maré comic event %s started (%s) on %s"),*Id,bForced?TEXT("forced"):TEXT("roll"),*Target->GetName());
 return true;
}

void UMareComicEvents::UpdateGull(float DeltaSeconds)
{
 GullTime+=DeltaSeconds;AMarePerson* V=Victim.Get();
 const float Held=CVarGullAt.GetValueOnGameThread();if(Held>=0.f)GullTime=FMath::Min(Held,6.8f);   // QA: frozen frame of the flight
 FVector Food,Side,Hover;if(!GullHover(V,Food,Side,Hover)){Food=Gull->GetActorLocation();Side=FVector(0,-1,0);Hover=Food;}
 static const float In=3.f,Stay=.9f,Out=3.f;
 FVector Pos,Next;
 if(GullTime<In){Pos=GullArc(GullFrom,Hover,GullTime/In);Next=GullArc(GullFrom,Hover,(GullTime+.05f)/In);}
 else if(GullTime<In+Stay){const float W=GullTime-In;Pos=Hover+FVector(0,0,8.f*FMath::Sin(W*18.f));Next=Pos-Side;
  if(!bBitten && W>Stay*.5f && V && V->CarriedMeshes.Num()){bBitten=true;   // the bite: a small piece of the food, nothing taken from the plate or the stock
   Bite=NewObject<UStaticMeshComponent>(Gull);Bite->SetStaticMesh(V->CarriedMeshes[0]->GetStaticMesh());Bite->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   Bite->SetupAttachment(Gull->GetRootComponent());Bite->SetUsingAbsoluteScale(true);Bite->SetWorldScale3D(FVector(.22f));Bite->SetRelativeLocation(FVector(0,31,24));Bite->RegisterComponent();
   Notice();
   V->bConversing=true;}}
 else if(GullTime<In+Stay+Out){const float U=(GullTime-In-Stay)/Out;Pos=GullOut(Hover,GullAway,U);Next=GullOut(Hover,GullAway,FMath::Min(U+.02f,1.f))+(GullAway-Hover).GetSafeNormal()*.01f;}
 else{if(V)V->bConversing=false;Finish(true);return;}
 FVector Dir=Next-Pos;if(Dir.IsNearlyZero())Dir=FVector(1,0,0);
 // The gull model faces local +Y: heading is the travel direction minus 90 degrees; pitch follows the climb or dive.
 const float Heading=FMath::RadiansToDegrees(FMath::Atan2(Dir.Y,Dir.X))-90.f;float Climb=FMath::RadiansToDegrees(FMath::Atan2(Dir.Z,Dir.Size2D()));
 if(GullTime>=In && GullTime<In+Stay)Climb=-18.f;   // nose down onto the food while hovering
 Gull->SetActorLocationAndRotation(Pos,FRotator(0,Heading,FMath::Clamp(-Climb,-25.f,25.f)));
}

void UMareComicEvents::Notice()const
{
 if(UWorld* World=GetWorld())if(auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>())
  Sim->LastMessage=SpeakerName.IsEmpty()?Line:FString::Printf(TEXT("%s: %s"),*SpeakerName,*Line);
}

static TArray<FString> DefStrings(const TSharedPtr<FJsonObject>& Def,const TCHAR* Field)
{
 TArray<FString> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(Def->TryGetArrayField(Field,L))for(const auto& V:*L)Out.Add(V->AsString());return Out;
}

// ---- HUM-004: beach umbrella blown over ------------------------------------------------------------------------

bool UMareComicEvents::StartUmbrella(const TSharedPtr<FJsonObject>& Def,bool bForced)
{
 UWorld* World=GetWorld();APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Hero || !Sim)return false;
 // Not in the rain (the beach empties and umbrellas close); the breeze is enough otherwise.
 if(UMaterialParameterCollection* Time=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime")))
  if(!bForced && UKismetMaterialLibrary::GetScalarParameterValue(World,Time,TEXT("Rain"))>.3f)return false;
 const FString PoleName=UMareSimulation::String(Def,TEXT("pole_mesh"));
 // Every visible pole of a beach umbrella 4-25 m from the player, nearest first.
 struct FPole{UStaticMeshComponent* C;int32 I;FVector Base;float Dist;};TArray<FPole> Poles;
 for(TActorIterator<AActor> It(World);It;++It){if(It->IsHidden())continue;
  for(UActorComponent* AC:It->GetComponents())if(auto SM=Cast<UStaticMeshComponent>(AC))if(SM->GetStaticMesh() && SM->IsVisible() && SM->GetStaticMesh()->GetName()==PoleName){
   const float Low=SM->GetStaticMesh()->GetBoundingBox().Min.Z;
   auto Add=[&](const FTransform& T,int32 I){if(T.GetScale3D().Z<.01f)return;const FVector B=T.TransformPosition(FVector(0,0,Low));const float D=FVector::Dist2D(B,Hero->GetActorLocation());
    if(D>=(bForced?150.f:400.f) && D<=2500.f)Poles.Add({SM,I,B,D});};
   if(auto ISM=Cast<UInstancedStaticMeshComponent>(SM)){for(int32 I=0;I<ISM->GetInstanceCount();++I){FTransform T;ISM->GetInstanceTransform(I,T,true);Add(T,I);}}
   else Add(SM->GetComponentTransform(),-1);}}
 Poles.Sort([](const FPole& A,const FPole& B){return A.Dist<B.Dist;});
 const float Run=UMareSimulation::Number(Def,TEXT("distance"),650);
 for(const FPole& Pole:Poles){
  // Downwind along the beach (the sea breeze turns along the shore): a clear run and open sand where it stops.
  FCollisionQueryParams Query(TEXT("MareUmbrella"),false,Pole.C->GetOwner());Query.AddIgnoredActor(Hero);
  for(const float Angle:{0.f,180.f,25.f,-25.f,155.f,205.f}){
   const FVector Wind=FVector(1,0,0).RotateAngleAxis(Angle,FVector::UpVector);FVector Rest=Pole.Base+Wind*Run;FHitResult Floor;
   if(!World->LineTraceSingleByChannel(Floor,Rest+FVector(0,0,150),Rest-FVector(0,0,200),ECC_Visibility,Query) || !Floor.GetComponent())continue;
   UMaterialInterface* Under=Floor.GetComponent()->GetMaterial(0);
   if(!Under || !Under->GetName().Contains(TEXT("CoastGround")) || Floor.ImpactPoint.Y>-1050.f || FMath::Abs(Floor.ImpactPoint.Z-Pole.Base.Z)>60.f)continue;
   Rest=Floor.ImpactPoint;
   const FVector From=Pole.Base+Wind*170.f;
   if(World->SweepTestByChannel(From+FVector(0,0,125),Rest+FVector(0,0,125),FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(95.f),Query)
    || World->SweepTestByChannel(From+FVector(0,0,35),Rest+FVector(0,0,35),FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(30.f),Query))continue;
   // The umbrella: every mesh sharing the pole's XY, from the sand to the top of the canopy.
   UmbrellaParts.Reset();
   for(TActorIterator<AActor> It(World);It;++It)for(UActorComponent* AC:It->GetComponents())if(auto SM=Cast<UStaticMeshComponent>(AC))if(SM->GetStaticMesh() && SM->IsVisible()){
    auto Take=[&](const FTransform& T,int32 I){const FVector L=T.GetLocation();
     if(FVector::Dist2D(L,Pole.Base)<4.f && L.Z>Pole.Base.Z-10.f && L.Z<Pole.Base.Z+300.f && SM->GetStaticMesh()->GetBounds().BoxExtent.Size2D()*T.GetScale3D().X<260.f){
      FUmbrellaPart Part;Part.Component=SM;Part.Instance=I;Part.Original=T;Part.Collision=uint8(SM->GetCollisionEnabled());UmbrellaParts.Add(Part);}};
    if(auto ISM=Cast<UInstancedStaticMeshComponent>(SM)){for(int32 I=0;I<ISM->GetInstanceCount();++I){FTransform T;ISM->GetInstanceTransform(I,T,true);if(T.GetScale3D().Z>.01f)Take(T,I);}}
    else Take(SM->GetComponentTransform(),-1);}
   if(UmbrellaParts.Num()<2){UmbrellaParts.Reset();continue;}
   // A movable copy, pivot at the foot of the pole; the originals step aside (epsilon scale keeps ISM bounds sane).
   UmbrellaHome=FTransform(FRotator::ZeroRotator,Pole.Base);
   Umbrella=World->SpawnActor<AActor>(AActor::StaticClass(),UmbrellaHome);if(!Umbrella){UmbrellaParts.Reset();return false;}
   auto Root=NewObject<USceneComponent>(Umbrella,TEXT("Root"));Root->SetMobility(EComponentMobility::Movable);Umbrella->SetRootComponent(Root);Root->RegisterComponent();Umbrella->SetActorTransform(UmbrellaHome);
   for(const FUmbrellaPart& Part:UmbrellaParts){UStaticMeshComponent* Src=Part.Component.Get();
    // Instanced parts stay instanced: their colour is per-instance custom data (the canopy tint).
    auto SrcISM=Cast<UInstancedStaticMeshComponent>(Src);
    UStaticMeshComponent* Copy=SrcISM?NewObject<UInstancedStaticMeshComponent>(Umbrella):NewObject<UStaticMeshComponent>(Umbrella);
    Copy->SetMobility(EComponentMobility::Movable);Copy->SetStaticMesh(Src->GetStaticMesh());
    for(int32 M=0;M<Src->GetNumMaterials();++M)Copy->SetMaterial(M,Src->GetMaterial(M));
    Copy->SetCollisionEnabled(ECollisionEnabled::NoCollision);Copy->SetupAttachment(Root);Copy->RegisterComponent();
    if(auto CopyISM=Cast<UInstancedStaticMeshComponent>(Copy)){const int32 N=SrcISM->NumCustomDataFloats;CopyISM->SetNumCustomDataFloats(N);CopyISM->AddInstance(Part.Original,true);
     if(N>0 && SrcISM->PerInstanceSMCustomData.Num()>=(Part.Instance+1)*N){TArray<float> Data;for(int32 K=0;K<N;++K)Data.Add(SrcISM->PerInstanceSMCustomData[Part.Instance*N+K]);CopyISM->SetCustomData(0,Data,true);}}
    else Copy->SetWorldTransform(Part.Original);
    if(auto ISM=Cast<UInstancedStaticMeshComponent>(Src)){FTransform T=Part.Original;T.SetScale3D(FVector(.001f));ISM->UpdateInstanceTransform(Part.Instance,T,true,true,true);}
    else{Src->SetVisibility(false);Src->SetCollisionEnabled(ECollisionEnabled::NoCollision);}}
   UmbrellaWind=Wind;UmbrellaRest=Rest;UmbrellaTime=0;UmbrellaPhase=0;
   const TArray<FString> Asks=DefStrings(Def,TEXT("asks"));const FString Id=UMareSimulation::String(Def,TEXT("id"));auto Comic=UMareSimulation::Object(Sim->State,TEXT("comic"));
   SpeakerName=UMareSimulation::String(Def,TEXT("speaker"));Line=Asks.IsValidIndex(0)?Asks[LineIndex(Comic,Id,Asks.Num(),false,Rng.RandHelper(1000))]:FString();
   MarkStarted(Comic,Id,UMareSimulation::Number(Sim->State,TEXT("day"),1)*1440+UMareSimulation::Number(Sim->State,TEXT("minutes")));
   Active=Id;Waited=0;bTalking=false;Notice();
   // Its owner runs after it (a pedestrian nearby, if any).
   if(auto Village=World->GetSubsystem<UMareVillageWorld>())if(AMarePerson* P=Village->HoldPedestrianNear(Pole.Base,0,1800,UMareSimulation::Number(Def,TEXT("wait_seconds"),60)+20)){
    Caller=P;SavedName=P->PersonName;P->WalkTo(Rest-Wind*160.f+FVector::CrossProduct(Wind,FVector::UpVector)*90.f);}
   UE_LOG(LogTemp,Display,TEXT("Maré comic event %s started (%s), umbrella of %d parts at %s rolls to %s"),*Id,bForced?TEXT("forced"):TEXT("roll"),UmbrellaParts.Num(),*Pole.Base.ToString(),*Rest.ToString());
   return true;}}
 return false;
}

void UMareComicEvents::UpdateUmbrella(float DeltaSeconds)
{
 UmbrellaTime+=DeltaSeconds;UWorld* World=GetWorld();
 const FVector Up=FVector::UpVector,Axis=FVector::CrossProduct(Up,UmbrellaWind).GetSafeNormal();
 // Lying: foot and canopy rim on the sand (tan = canopy height / canopy radius, 210/107: about 63 degrees).
 static const float Lying=63.f,Tumble=3.4f;
 auto Pose=[&](const FVector& Foot,float Tilt,float Spin){return FTransform(FQuat(Axis,FMath::DegreesToRadians(Tilt))*FQuat(Up,FMath::DegreesToRadians(Spin)),Foot);};
 if(UmbrellaPhase==0){
  const float T=UmbrellaTime;FVector Foot;float Tilt,Spin;
  if(T<.5f){const float U=T/.5f;   // a gust pulls it out of the sand and leans it over
   Foot=UmbrellaHome.GetLocation()+UmbrellaWind*40.f*U+Up*28.f*FMath::Sin(U*PI*.5f);Tilt=35.f*U*U;Spin=20.f*U;}
  else{const float U=FMath::Clamp((T-.5f)/(Tumble-.5f),0.f,1.f),E=1.f-FMath::Square(1.f-U);   // rolls on the canopy rim, slowing down
   const FVector A=UmbrellaHome.GetLocation()+UmbrellaWind*40.f+Up*28.f;Foot=FMath::Lerp(A,UmbrellaRest,E);
   Foot.Z=FMath::Lerp(A.Z,UmbrellaRest.Z,FMath::Min(U*2.f,1.f))+22.f*FMath::Abs(FMath::Sin(U*PI*3.f))*(1.f-U);
   Tilt=FMath::Lerp(35.f,Lying,FMath::Min(U*2.5f,1.f))+7.f*FMath::Sin(U*PI*5.f)*(1.f-U);Spin=20.f+300.f*E;}
  Umbrella->SetActorTransform(Pose(Foot,Tilt,Spin));
  if(T>=Tumble){UmbrellaPhase=1;Waited=0;
   // Optional: E on the umbrella puts it back.
   CallTarget=World->SpawnActor<AMareServiceTarget>();
   if(CallTarget){CallTarget->Action=TEXT("Comic");CallTarget->Label=TEXT("Guarda-sol · recolocar");CallTarget->Reach=320;CallTarget->OcclusionTolerance=60;CallTarget->SetOwner(Umbrella);
    CallTarget->AttachToActor(Umbrella,FAttachmentTransformRules::KeepRelativeTransform);CallTarget->SetActorRelativeLocation(FVector(0,0,110));}}
  return;}
 if(UmbrellaPhase==1){
  // Left alone: someone puts it back while the player is not looking (or is far away).
  Waited+=DeltaSeconds;APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);
  const bool bUnseen=!Umbrella->WasRecentlyRendered(.5f) || !Hero || FVector::Dist2D(Hero->GetActorLocation(),UmbrellaRest)>3500.f;
  if((Waited>UMareSimulation::Number(EventDef(Active),TEXT("wait_seconds"),60) && bUnseen) || Waited>300.f)Finish(false);
  return;}
 // Being put back: lifted, carried over and planted again.
 const float U=FMath::Clamp(UmbrellaTime/1.1f,0.f,1.f),E=FMath::InterpEaseInOut(0.f,1.f,U,2.f);
 const FVector Foot=FMath::Lerp(UmbrellaFrom.GetLocation(),UmbrellaHome.GetLocation(),E)+Up*60.f*FMath::Sin(U*PI);
 Umbrella->SetActorTransform(FTransform(FQuat::Slerp(UmbrellaFrom.GetRotation(),UmbrellaHome.GetRotation(),E),Foot));
 if(U>=1.f)Finish(true);
}

void UMareComicEvents::RestoreUmbrella()
{
 for(const FUmbrellaPart& Part:UmbrellaParts)if(UStaticMeshComponent* Src=Part.Component.Get()){
  if(auto ISM=Cast<UInstancedStaticMeshComponent>(Src))ISM->UpdateInstanceTransform(Part.Instance,Part.Original,true,true,true);
  else{Src->SetVisibility(true);Src->SetCollisionEnabled(ECollisionEnabled::Type(Part.Collision));}}
 UmbrellaParts.Reset();
 if(IsValid(Umbrella))Umbrella->Destroy();Umbrella=nullptr;UmbrellaPhase=0;
}

// ---- HUM-006: the clumsy attendant -------------------------------------------------------------------------------

bool UMareComicEvents::StartClumsy(const TSharedPtr<FJsonObject>& Def,bool bForced)
{
 UWorld* World=GetWorld();APawn* Hero=UGameplayStatics::GetPlayerPawn(World,0);auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Hero || !Sim)return false;
 const FString Role=UMareSimulation::String(Def,TEXT("role"));AMarePerson* Target=nullptr;
 for(TActorIterator<AMarePerson> It(World);It;++It)
  if(It->StaffRole==Role && !It->CarriedMeshes.IsEmpty() && IsValid(It->CarriedMeshes[0]) && (bForced || It->GetVelocity().Size2D()>40.f)
   && FVector::Dist2D(It->GetActorLocation(),Hero->GetActorLocation())<2500.f){Target=*It;break;}
 if(!Target)return false;
 // Training: level 1 trips at the full odds, each level up makes it rarer (level 5: a fifth).
 double Level=1;const TArray<TSharedPtr<FJsonValue>>* Team=nullptr;
 if(UMareSimulation::Object(Sim->State,TEXT("staff_team"))->TryGetArrayField(Role,Team) && Team->Num())Level=UMareSimulation::Number((*Team)[0]->AsObject(),TEXT("level"),1);
 if(!bForced && Rng.FRand()>(6.0-FMath::Clamp(Level,1.0,5.0))/5.0)return false;
 Clumsy=Target;ClumsyTime=0;ClumsySpeed=Target->GetCharacterMovement()->MaxWalkSpeed;ClumsyMesh=Target->GetMesh()->GetRelativeRotation();
 Target->GetCharacterMovement()->MaxWalkSpeed=0;Target->GetCharacterMovement()->StopMovementImmediately();Target->bConversing=true;ClumsyTray.Reset();
 for(auto Part:Target->CarriedMeshes)if(IsValid(Part))ClumsyTray.Add({Part,Part->GetRelativeTransform()});
 const TArray<FString> Asks=DefStrings(Def,TEXT("asks"));const FString Id=UMareSimulation::String(Def,TEXT("id"));auto Comic=UMareSimulation::Object(Sim->State,TEXT("comic"));
 SpeakerName=UMareSimulation::String(Def,TEXT("speaker"));Line=Asks.IsValidIndex(0)?Asks[LineIndex(Comic,Id,Asks.Num(),false,Rng.RandHelper(1000))]:FString();
 MarkStarted(Comic,Id,UMareSimulation::Number(Sim->State,TEXT("day"),1)*1440+UMareSimulation::Number(Sim->State,TEXT("minutes")));
 Active=Id;Waited=0;bTalking=false;
 UE_LOG(LogTemp,Display,TEXT("Maré comic event %s started (%s) on %s, level %d"),*Id,bForced?TEXT("forced"):TEXT("roll"),*Target->GetName(),int32(Level));
 return true;
}

void UMareComicEvents::UpdateClumsy(float DeltaSeconds)
{
 AMarePerson* P=Clumsy.Get();ClumsyTime+=DeltaSeconds;
 static const float Length=1.6f;
 if(!P || ClumsyTime>=Length){Finish(true);return;}
 const float U=ClumsyTime/Length;
 // A trip: lean forward, a side-to-side wobble that settles, the tray dipping and tilting before it is caught.
 const float Lean=9.f*FMath::Sin(PI*FMath::Clamp(U*2.2f,0.f,1.f)),Settle=1.f-U;
 const float Sway=7.f*FMath::Sin(ClumsyTime*12.f)*Settle*FMath::Min(U*4.f,1.f);
 P->GetMesh()->SetRelativeRotation((FRotator(-Lean,0,Sway).Quaternion()*ClumsyMesh.Quaternion()).Rotator());
 const float Dip=FMath::Sin(PI*FMath::Clamp((U-.08f)/.5f,0.f,1.f));
 for(const auto& Part:ClumsyTray)if(USceneComponent* C=Part.Key.Get())
  C->SetRelativeTransform(FTransform(FRotator(14.f*Dip*FMath::Sin(ClumsyTime*15.f),0,24.f*Dip),FVector(0,0,-7.f*Dip))*Part.Value);
 if(U>.35f && Line.Len() && !bTalking){bTalking=true;Notice();}   // the "phew" once the tray is caught
}

void UMareComicEvents::RestoreClumsy()
{
 if(AMarePerson* P=Clumsy.Get()){P->bConversing=false;P->GetMesh()->SetRelativeRotation(ClumsyMesh);if(ClumsySpeed>0)P->GetCharacterMovement()->MaxWalkSpeed=ClumsySpeed;
  for(const auto& Part:ClumsyTray)if(USceneComponent* C=Part.Key.Get())C->SetRelativeTransform(Part.Value);}
 Clumsy.Reset();ClumsyTray.Reset();
}
