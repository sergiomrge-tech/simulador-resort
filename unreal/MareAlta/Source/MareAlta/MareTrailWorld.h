#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareTrailWorld.generated.h"
class AMarePerson;
class AMareServiceTarget;
class APlayerController;
class UStaticMeshComponent;

/** Lighthouse trail on foot (CHECKLIST_EXPANSOES 2.4): the group walks after the player from the beach to the
 *  lighthouse. Water and sunscreen at the start (E on each walker), walkers left behind complain, a group photo (P)
 *  and the lighthouse story (E) at the two viewpoints, and the sunset at the lighthouse if the group gets there in
 *  its window (MareSimulation::TrailScore + GuideTour). Values in tours.json "trail_tour". */
UCLASS()
class MAREALTA_API UMareTrailWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual TStatId GetStatId() const override;
 virtual void Deinitialize() override;
 bool IsActive()const{return Walkers.Num()>0;}
 /** Starts the trail now (boarding hour, tickets sold); false with the reason in LastMessage. */
 bool Start(APlayerController* Controller);
 FString Status()const;
 TArray<TPair<FVector,FString>> Bubbles()const;
 /** E on a walker at the start: water and sunscreen. */
 void GiveWater(int32 Walker);
 /** E on the viewpoint sign: the lighthouse story while the group rests. */
 void TellStory(int32 Viewpoint);
 /** The player took a photo (AMareController::TakePhoto): the group photo of the viewpoint they are at. */
 void OnPhoto();
 /** QA: "state", "water:i", "story:i", "photo", "goto:i" (viewpoint i, 9 = lighthouse, with the group), "finish". */
 FString QA(const FString& Cmd);
private:
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Walkers;
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> WaterTargets;
 UPROPERTY() TArray<TObjectPtr<AMareServiceTarget>> StoryTargets;
 UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Bottles;
 TWeakObjectPtr<APlayerController> PC;
 FString TourId;
 float Time=0,WaitMinutes=0,SunsetMinutes=0,FollowClock=0;
 int32 Complaints=0,Stories=0;
 bool bLeftStart=false,bArrived=false,bSunset=false,bLate=false,bFollowing=false;
 float FollowTime=0;
 FVector LastPos=FVector::ZeroVector,Heading2D=FVector::ZeroVector;
 TArray<bool> Watered,Photographed,Told;
 TArray<float> LagClock;
 TMap<int32,TPair<FString,float>> Says;
 /** Walkers of a finished tour: when they start back home (positive) or are removed (negative). */
 TMap<TWeakObjectPtr<AMarePerson>,double> Leaving;
 TSharedPtr<FJsonObject> Defs()const;
 FString Line(const FString& Key)const;
 FVector Viewpoint(int32 I)const;
 int32 ViewpointCount()const;
 int32 AtViewpoint()const;
 void Say(int32 Walker,const FString& Text,float Seconds=3.5f);
 void Finish();
 double Hour()const;
};
