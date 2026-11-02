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
 /** Real smartphone (Data/custom_assets.json "realistic_smartphone") held in front of the eyes while the phone is open. */
 void SetPhoneVisible(bool bVisible);
 /** The held phone, or null while it is put away (hand IK grips its short edges). */
 class UStaticMeshComponent* GetHeldPhone()const;
 /** Glass of the held phone projected to the viewport, in pixels: the phone UI is drawn exactly there. */
 bool PhoneScreenRect(FVector2D& Min,FVector2D& Max)const;
private:
 UPROPERTY() TObjectPtr<UCameraComponent> Eyes;
 UPROPERTY() TObjectPtr<class UStaticMeshComponent> PhoneModel;
 float VerticalSwimInput=0.f;
 bool bSprint=false;
 /** L3 on the gamepad: run until the player stops. */
 bool bSprintToggle=false;
 FVector SafeLandLocation=FVector(3800,-1200,100);
 void SprintPressed(){bSprint=true;}
 void SprintReleased(){bSprint=false;}
 void SprintToggle(){bSprintToggle=!bSprintToggle;}
 void Forward(float Value);
 void Right(float Value);
 void LookX(float Value);
 void LookY(float Value);
 /** Right stick: a rate (per second), unlike the mouse deltas of LookX/LookY. */
 void LookPadX(float Value);
 void LookPadY(float Value);
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
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void OpenPhone(int32 Tab=0);
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void ClosePhone();
 UFUNCTION(BlueprintPure,Category="Maré Alta") UMareSimulation* GetSimulation()const;
 void OpenStation(FName Station);
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bPhoneOpen=false;
 /** Main menu over the paused world at start-up; the session (intro) only starts after a choice. */
 /** Business counter task (three timing rounds) over the paused world; the result pays through PlayBusiness. */
 void StartBusinessGame(const FString& Biz);
 void CloseBusinessGame();
 void OpenMainMenu();
 bool IsMainMenuOpen()const{return MainMenuWidget.IsValid();}
 /** Continue/Load: the slot already behind the menu just resumes, another slot reloads the level. */
 bool MenuLoadSlot(int32 Slot);
 /** New game in a slot (an occupied slot keeps its old file as .bak), then the arrival intro. */
 bool MenuNewGame(int32 Slot);
 /** Saves and reloads the level with the main menu open again. */
 void ReturnToMainMenu();
 /** Full options (graphics, display, audio, controls, language) shared by the pause menu and the main menu. */
 TSharedRef<SWidget> MakeOptionsPanel();
 virtual void OnPossess(APawn* InPawn) override;
private:
 void BuildPauseMenu(bool bOptions);
 TSharedPtr<SMarePhone> PhoneWidget;
 TSharedPtr<SWidget> PauseWidget;
 TSharedPtr<SWidget> MainMenuWidget;
 TSharedPtr<SWidget> GameWidget;
 /** Slot whose state the current world was built from, and whether that state came from a file. */
 int32 WorldSlot=1;
 bool bWorldFromFile=false;
 void CloseMainMenu();
 void ReloadWorld();
};

UCLASS()
class MAREALTA_API AMareHUD : public AHUD
{
 GENERATED_BODY()
public:
 virtual void DrawHUD() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 /** "Maré Tropical" overlay (wood plank, order tickets, mission note, prompt); rebuilt only on change. */
 TSharedPtr<class SMareHud> Overlay;
 /** Short-lived notice for messages produced outside the phone (sleep, chapters, fame). */
 FString Notice;
 double NoticeUntil=0;
 /** Star average shown last frame; a change flashes the value green/red for a moment. */
 double ShownStars=-1,StarsFlashUntil=0;
 bool bStarsUp=true;
};

UCLASS()
class MAREALTA_API AMareGameMode : public AGameModeBase
{
 GENERATED_BODY()
public:
 AMareGameMode();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 /** Starts play after the main menu (or directly in QA runs): arrival intro and the letter. */
 void StartSession();
private:
 float SaveClock=0.f;
};
