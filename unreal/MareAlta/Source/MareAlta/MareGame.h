#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "MareGame.generated.h"
class SMarePhone;
class UMareSimulation;
class UCameraComponent;

UCLASS()
class MAREALTA_API AMareCharacter : public ACharacter
{
 GENERATED_BODY()
public:
 AMareCharacter();
 virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
 virtual void Tick(float DeltaSeconds) override;
 /** Shared vertical swim control for keyboard, gamepad and QA. Positive rises, negative dives. */
 UFUNCTION(BlueprintCallable,Category="Movement") void SwimVertical(float Value);
private:
 UPROPERTY() TObjectPtr<UCameraComponent> Eyes;
 float VerticalSwimInput=0.f;
 bool bSprint=false;
 FVector SafeLandLocation=FVector(3800,-1200,100);
 void SprintPressed(){bSprint=true;}
 void SprintReleased(){bSprint=false;}
 void Forward(float Value);
 void Right(float Value);
 void LookX(float Value);
 void LookY(float Value);
 void Phone();
 void Interact();
};

UCLASS()
class MAREALTA_API AMareController : public APlayerController
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void TogglePhone();
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void TogglePauseMenu();
 virtual void SetupInputComponent() override;
 void OpenPhone(int32 Tab=0);
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void ClosePhone();
 UFUNCTION(BlueprintPure,Category="Maré Alta") UMareSimulation* GetSimulation()const;
 void OpenStation(FName Station);
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bPhoneOpen=false;
private:
 TSharedPtr<SMarePhone> PhoneWidget;
 TSharedPtr<SWidget> PauseWidget;
};

UCLASS()
class MAREALTA_API AMareHUD : public AHUD
{
 GENERATED_BODY()
public:
 virtual void DrawHUD() override;
};

UCLASS()
class MAREALTA_API AMareGameMode : public AGameModeBase
{
 GENERATED_BODY()
public:
 AMareGameMode();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
private:
 float SaveClock=0.f;
};
