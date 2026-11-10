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
/** Under-water colour by eye height: Tint = hue at the surface luminance (SceneColorTint feeds the pre-exposure), Gain = darkness
 *  for ColorGain.W (grading LUT, after the exposure). */
void MareUnderwaterGrade(float EyeZ,FLinearColor& Tint,float& Gain);
/** Under-water eye cap (EV100): 15 in the sunlit shallows, 10 from ~25 m down (09/11). */
float MareUnderwaterMaxEV(float EyeZ);

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
 /** C19 (09/11): sun rays under water, long additive planes along the sun direction around the eyes. */
 UPROPERTY() TArray<TObjectPtr<class UStaticMeshComponent>> SunShafts;
 void UpdateSunShafts(bool bUnderwater,float DeltaSeconds);
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
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void OpenStation(FName Station);
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UPROPERTY(BlueprintReadOnly,Category="Maré Alta") bool bPhoneOpen=false;
 /** Main menu over the paused world at start-up; the session (intro) only starts after a choice. */
 /** Business counter task (three timing rounds) over the paused world; the result pays through PlayBusiness. */
 void StartBusinessGame(const FString& Biz);
 /** Fishing at the pier (cast, wait, strike) over the running world. */
 void StartFishing();
 /** Bar work glass (E): pour the ingredient in hand, else run the next prep step's mini-action, else serve. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void UseBarGlass();
 /** QA of the playable boat tour: "start" (forces the boarding hour and tickets), else MareBoatTourWorld::QA. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString BoatTourQA(const FString& Cmd);
 /** QA of the guided snorkel: "start" (forces the boarding hour and tickets), else MareSnorkelWorld::QA. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString SnorkelQA(const FString& Cmd);
 /** QA of the reef seafloor and sharks (MareReefWorld::QA). */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString ReefQA(const FString& Cmd);
 /** QA of the ice cream shop: "own", "customers:n", "open", "perfect", "wrong", "hold:flavor,seconds", "release", "show", "close". */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString IceCreamQA(const FString& Cmd);
 /** QA of the food truck: "own", "customers:n", "open", "perfect", "wrong", "fill", "seal:f", "dip", "fry:s", "out", "crank:t", "deliver", "close". */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString PastelQA(const FString& Cmd);
 /** QA of the rental: "own", "customers:n", "return:dent|clean", "open", "wax:t", "left", "right", "adrift", "near", "tow", "home", "close". */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString RentalQA(const FString& Cmd);
 /** QA of the souvenir shop: "own", "gift:n", "open", "buy:id", "place:slot,id", "hour:n", "photo", "print", "state", "close"; else the open screen (MareSouvenirGame::QA). */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString SouvenirQA(const FString& Cmd);
 /** QA of the lighthouse trail: "start" (forces the departure hour and tickets), else MareTrailWorld::QA. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") FString TrailQA(const FString& Cmd);
 /** Bar prep mini-action over the running world: "socar" (taps on the beat), "bater" (hold and let go in the
  *  green), "liquidificar" (pulses in the zone). The score goes to UMareSimulation::BarPrepStep. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void StartBarPrep(const FString& Step);
 /** Early Access end screen (once per save, when everything is bought and the village stories are done). */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void ShowEndOfContent(bool bDebt=false);
 /** Main menu straight on its credits page (debt finale). */
 void OpenCredits();
 /** Photo mode (P / D-pad down): screenshot to Saved/Album and the subjects in frame to the album. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") void TakePhoto();
 void CloseBusinessGame();
 /** Kiosk payment screen (MarePayment.cpp): cash change or card after the player completes an order. */
 void OpenPayment(const FString& Customer,double Total);
 /** QA scripts that drive the kiosk themselves (mare.Pay off). */
 bool bSkipPaymentForQA=false;
 void OpenMainMenu();
 /** Language page over the title menu (first start; QA "mare.ShowUI language"); the menu rebuilds its texts after Confirm. */
 void ShowLanguagePage();
 bool IsMainMenuOpen()const{return MainMenuWidget.IsValid();}
 bool IsTitle()const{return bTitle;}
 /** Continue/Load: the slot already behind the menu just resumes, another slot reloads the level. */
 bool MenuLoadSlot(int32 Slot);
 /** New game in a slot (an occupied slot keeps its old file as .bak), then the arrival intro. */
 bool MenuNewGame(int32 Slot);
 /** Saves and reloads the level with the main menu open again. */
 void ReturnToMainMenu();
 /** Reloads the active slot from disk and rebuilds the world (tsunami game over: "restart the day"). */
 bool ReloadActiveSlot();
 /** Full options (graphics, display, audio, controls, language) shared by the pause menu and the main menu. */
 TSharedRef<SWidget> MakeOptionsPanel();
 virtual void OnPossess(APawn* InPawn) override;
private:
 void BuildPauseMenu(bool bOptions);
 friend struct FMareUIQA;
 TSharedPtr<SMarePhone> PhoneWidget;
 TSharedPtr<SWidget> PauseWidget;
 TSharedPtr<SWidget> MainMenuWidget;
 /** Title screen state (MareTitle.cpp): the menu at start-up flies over the bay instead of pausing. */
 bool bTitle=false;double TitleSavedMinutes=-1;UPROPERTY() TObjectPtr<class AMareTitleCamera> TitleCamera=nullptr;
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
 /** Speech bubbles over the bar guests (their order). */
 TSharedPtr<class SMareBubbles> Bubbles;
 /** Short-lived notice for messages produced outside the phone (sleep, chapters, fame). */
 FString Notice;
 double NoticeUntil=0;
 /** First-time tip on screen (MareSimulation::ShowTip) and until when. */
 FString TipTitle,TipText;double TipUntil=0;
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
