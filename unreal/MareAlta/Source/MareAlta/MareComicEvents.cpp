#include "MareComicEvents.h"
#include "MareGame.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MareVillageWorld.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

static TAutoConsoleVariable<int32> CVarComicSeed(TEXT("mare.ComicSeed"),0,TEXT("QA: seed of the comic-event roll (0 = time)."));
static FAutoConsoleCommandWithWorldAndArgs ComicQACommand(TEXT("mare.Comic"),TEXT("QA: starts a comic event now (comic_events.json id, e.g. HUM-005)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  if(World && Args.Num())if(auto Comic=World->GetSubsystem<UMareComicEvents>())Comic->Force(Args[0]);}));

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
 Active=Id;Caller=P;Waited=0;bTalking=false;
 UE_LOG(LogTemp,Display,TEXT("Maré comic event %s started (%s)"),*Id,bForced?TEXT("forced"):TEXT("roll"));
 return true;
}

void UMareComicEvents::Interact(APlayerController* Controller)
{
 AMarePerson* P=Caller.Get();auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>();if(!P || !Village || bTalking || Active.IsEmpty())return;
 bTalking=true;const TWeakObjectPtr<UMareComicEvents> Weak(this);const TArray<FString> R=Reactions;
 Village->Quip(P,Controller,SpeakerName,Line,Replies,[R](int32 I){return R.IsValidIndex(I)?R[I]:FString();},[Weak](){if(Weak.IsValid())Weak->Finish(true);});
}

void UMareComicEvents::Finish(bool bTalked)
{
 UWorld* World=GetWorld();
 if(AMarePerson* P=Caller.Get()){P->PersonName=SavedName;if(World)if(auto Village=World->GetSubsystem<UMareVillageWorld>())Village->ReleasePedestrian(P);}
 if(IsValid(CallTarget))CallTarget->Destroy();CallTarget=nullptr;
 if(bTalked && World)if(auto Sim=World->GetGameInstance()->GetSubsystem<UMareSimulation>()){
  auto Count=UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("comic")),TEXT("count"));Count->SetNumberField(Active,UMareSimulation::Number(Count,Active)+1);}
 UE_LOG(LogTemp,Display,TEXT("Maré comic event %s resolved (%s)"),*Active,bTalked?TEXT("talked"):TEXT("ignored"));
 LastResolved=Active;Active.Empty();Caller.Reset();bTalking=false;
}

void UMareComicEvents::Deinitialize(){if(!Active.IsEmpty())Finish(false);Super::Deinitialize();}
