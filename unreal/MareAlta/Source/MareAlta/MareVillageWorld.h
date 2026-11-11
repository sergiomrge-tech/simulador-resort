#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MareVillageWorld.generated.h"
class AMarePerson;
class APlayerController;

/** Ambient residents and pedestrians are separate from paying kiosk customers. */
UCLASS()
class MAREALTA_API UMareVillageWorld : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaSeconds) override;
 virtual void Deinitialize() override;
 virtual TStatId GetStatId()const override;
 /** Interactions belong to physically present residents, never invisible phone targets. */
 void Speak(AMarePerson* Person,APlayerController* Controller);
 void CloseDialogue();
 bool IsDialogueOpen()const{return Dialogue.IsValid();}
 /** Short exchange (comic events): the line, the player's replies (each opens its reaction page) and a goodbye.
  *  OnReply returns the reaction for the chosen reply; OnClosed runs once when the exchange ends, however it ends. */
 void Quip(AMarePerson* Person,APlayerController* Controller,const FString& Name,const FString& Line,const TArray<FString>& Replies,
  TFunction<FString(int32)> OnReply,TFunction<void()> OnClosed);
 /** A walking pedestrian between MinDist and MaxDist cm of At stops for Seconds (null if none); Release lets it walk on. */
 AMarePerson* HoldPedestrianNear(FVector At,float MinDist,float MaxDist,float Seconds);
 void ReleasePedestrian(AMarePerson* Person);
 int32 ResidentCount()const{return Residents.Num();}
 int32 PedestrianCount()const{return Pedestrians.Num();}
 int32 HotelGuestCount()const{return HotelGuests.Num();}
 int32 SunbatherCount()const;
private:
 struct FWalker{TWeakObjectPtr<AMarePerson> Person;int32 Route=0,Point=0,Direction=1,BlockedAttempts=0;float Wait=0,Stuck=0;FVector Previous;
  /** Reference tip 9 (08/11): walking in company. A follower keeps beside its leader (Side cm to the right, a little
   *  behind) and stops and chats when the leader stops. */
  TWeakObjectPtr<AMarePerson> Leader;float Side=0;FVector LastGoal=FVector::ZeroVector;};
 TArray<TArray<FVector>> Routes;
 TArray<FWalker> Pedestrians;
 /** 10/11: failed walker spawns so far; each one moves the next try to another point of the route (a potted plant stood on
  *  a route's first point and the same spawn failed 3 times a second for the whole session). */
 int32 SpawnMisses=0;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Residents;
 /** Receptionist, lobby guests, restaurant diners, gym and pool-bar regulars of the Grand Hotel, present only once it is owned. */
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> HotelGuests;
 void UpdateHotelGuests();
 /** People seated in the church's pews at mass time (Content/Data/church.json). */
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Faithful;
 void UpdateChurch();
 /** People passing time on the pier (Data/pier_people.json): leaning on a post of the rope rail, on the phone. */
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> PierPeople;
 void UpdatePier();
 /** Sunbathers lying on the beach towels by day when it is dry (Content/Data/sunbathers.json). */
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Sunbathers;
 void UpdateSunbathers();
 TWeakObjectPtr<AMarePerson> Speaker;
 TWeakObjectPtr<APlayerController> DialogController;
 TSharedPtr<SWidget> Dialogue;
 /** Result of a chapter action, shown once when the conversation reopens. */
 FString ActionResult;
 TFunction<void()> QuipClosed;
 bool bReady=false;float Clock=0;
 void Setup();
 void UpdateWalkers(float Dt);
 AMarePerson* SpawnPerson(FVector Position,int32 Variant,const FString& Name);
};
