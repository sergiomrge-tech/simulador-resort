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
 int32 ResidentCount()const{return Residents.Num();}
 int32 PedestrianCount()const{return Pedestrians.Num();}
private:
 struct FWalker{TWeakObjectPtr<AMarePerson> Person;int32 Route=0,Point=0,Direction=1,BlockedAttempts=0;float Wait=0,Stuck=0;FVector Previous;};
 TArray<TArray<FVector>> Routes;
 TArray<FWalker> Pedestrians;
 UPROPERTY() TArray<TObjectPtr<AMarePerson>> Residents;
 TWeakObjectPtr<AMarePerson> Speaker;
 TWeakObjectPtr<APlayerController> DialogController;
 TSharedPtr<SWidget> Dialogue;
 bool bReady=false;float Clock=0;
 void Setup();
 void UpdateWalkers(float Dt);
 AMarePerson* SpawnPerson(FVector Position,int32 Variant,const FString& Name);
};
