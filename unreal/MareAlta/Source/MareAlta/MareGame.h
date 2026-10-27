#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "MareGame.generated.h"
class SMarePhone;
class UMareSimulation;

UCLASS()
class MAREALTA_API AMareCharacter : public ACharacter
{
 GENERATED_BODY()
public:
 AMareCharacter();
 virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
private:
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
 void OpenPhone(int32 Tab=0);
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void ClosePhone();
 UFUNCTION(BlueprintPure,Category="Maré Alta") UMareSimulation* GetSimulation()const;
 void OpenStation(FName Station);
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bPhoneOpen=false;
private:
 TSharedPtr<SMarePhone> PhoneWidget;
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
 virtual void Tick(float DeltaSeconds) override;
private:
 float SaveClock=0.f;
};
