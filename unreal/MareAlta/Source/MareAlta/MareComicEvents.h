#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Dom/JsonObject.h"
#include "MareComicEvents.generated.h"
class AMarePerson;
class AMareServiceTarget;
class APlayerController;

/** Light manager of the comic events (docs/ue58/HUMOR_EVENTOS_COMICOS.md, data Content/Data/comic_events.json):
 *  stable ids HUM-00x, one active at a time, per-event cooldown and a global gap in game minutes, a seedable roll.
 *  An event borrows a pedestrian near the player, who stops, faces the player and calls; E opens a short exchange
 *  (UMareVillageWorld::Quip). Ignored, it ends by itself. Cooldowns and the line counters live in the save
 *  ("comic"); nothing touches money, stock or orders. QA: mare.Comic <id> starts one now, mare.ComicSeed <n>. */
UCLASS()
class MAREALTA_API UMareComicEvents : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId()const override;
 virtual void Deinitialize() override;
 /** Player pressed E on the caller. */
 void Interact(APlayerController* Controller);
 /** Starts an event now (QA), ignoring hours, odds and cooldowns; false if none can start here. */
 bool Force(const FString& Id);
 FString ActiveId()const{return Active;}
 enum class EState:uint8{Idle,Active,Resolved};
 EState State()const{return Active.IsEmpty()?(LastResolved.IsEmpty()?EState::Idle:EState::Resolved):EState::Active;}

 /** Pure rules, used by the game and the automation test. Now and the stored times are absolute game minutes
  *  (day * 1440 + minutes). Due: the event's own cooldown and the global gap have both passed. */
 static bool IsDue(const TSharedPtr<FJsonObject>& Comic,const FString& Id,double Now,double Cooldown,double GlobalGap);
 static void MarkStarted(const TSharedPtr<FJsonObject>& Comic,const FString& Id,double Now);
 /** Which line an event says next: in order for sequences (the fisherman's fish grows), otherwise by the roll. */
 static int32 LineIndex(const TSharedPtr<FJsonObject>& Comic,const FString& Id,int32 Lines,bool bSequence,int32 Roll);
private:
 TSharedPtr<FJsonObject> Defs;
 FRandomStream Rng;
 float Clock=0,Waited=0;
 FString Active,LastResolved,Line,SpeakerName;
 TArray<FString> Replies,Reactions;
 FString SavedName;
 TWeakObjectPtr<AMarePerson> Caller;
 UPROPERTY() TObjectPtr<AMareServiceTarget> CallTarget;
 bool bTalking=false;
 /** HUM-001: the seagull swooping on a customer's food (Approach -> Hover -> Away, seconds since start). */
 UPROPERTY() TObjectPtr<class AStaticMeshActor> Gull;
 UPROPERTY() TObjectPtr<class UStaticMeshComponent> Bite;
 TWeakObjectPtr<AMarePerson> Victim;
 FVector GullFrom,GullAway;float GullTime=0;bool bBitten=false;
 bool StartGull(const TSharedPtr<FJsonObject>& Def,bool bForced);
 void UpdateGull(float DeltaSeconds);
 /** Optional prop in the caller's hand while the event lasts (HUM-002: the influencer's phone, up for a selfie). */
 UPROPERTY() TObjectPtr<class UStaticMeshComponent> Prop;
 /** HUM-004: a beach umbrella the wind knocks over. Its parts (pole, disc, canopy: the meshes sharing the pole's XY)
  *  step aside while a movable copy tumbles downwind and lies on the sand; E puts it back, or it is put back unseen. */
 struct FUmbrellaPart{TWeakObjectPtr<class UStaticMeshComponent> Component;int32 Instance=-1;FTransform Original;uint8 Collision=0;};
 TArray<FUmbrellaPart> UmbrellaParts;
 UPROPERTY() TObjectPtr<AActor> Umbrella;
 FTransform UmbrellaHome,UmbrellaFrom;FVector UmbrellaRest,UmbrellaWind;float UmbrellaTime=0;int32 UmbrellaPhase=0;
 bool InHotelEventArea(const FVector& At) const;
 bool StartUmbrella(const TSharedPtr<FJsonObject>& Def,bool bForced);
 void UpdateUmbrella(float DeltaSeconds);
 void RestoreUmbrella();
 /** HUM-006: the attendant almost drops the tray (a brief stop and wobble); nothing is lost, rarer at each level. */
 TWeakObjectPtr<AMarePerson> Clumsy;float ClumsyTime=0,ClumsySpeed=0;FRotator ClumsyMesh;
 TArray<TPair<TWeakObjectPtr<class USceneComponent>,FTransform>> ClumsyTray;
 bool StartClumsy(const TSharedPtr<FJsonObject>& Def,bool bForced);
 void UpdateClumsy(float DeltaSeconds);
 void RestoreClumsy();
 /** The event line as a HUD notice, "Speaker: line". */
 void Notice()const;
 bool Load();
 TSharedPtr<FJsonObject> EventDef(const FString& Id)const;
 bool Start(const TSharedPtr<FJsonObject>& Def,bool bForced);
 void Finish(bool bTalked);
};
