#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
class UPlayerInput;
class APlayerController;

/**
 * Player options outside the audio buses: graphics, display, controls and language.
 * Stored in Saved/MareOptions.json; graphics/display are mirrored into UGameUserSettings so the
 * engine starts with them. Audio volumes stay in UMareAudioWorld ([MareAudio] in GameUserSettings.ini).
 */
struct MAREALTA_API FMareOptions
{
 // Graphics: Preset is the base scalability level (0 low .. 3 epic); the groups below override it.
 int32 Preset=2,Shadows=2,GlobalIllumination=2,Reflections=2,PostProcess=2,Textures=2,Foliage=2,AntiAliasing=2;
 float ResolutionScale=80.f;
 FString Upscaler=TEXT("TSR");
 // Display. WindowMode follows EWindowMode: 0 fullscreen, 1 borderless, 2 windowed.
 FIntPoint Resolution=FIntPoint(1280,720);
 int32 WindowMode=2;
 bool bVSync=false;
 int32 FrameLimit=60; // 0 = unlimited
 float FieldOfView=90.f;
 // Controls.
 float MouseSensitivity=1.f;
 /** Right-stick look speed (1 = about 140 degrees per second at full deflection); invert Y applies to both. */
 float GamepadSensitivity=1.f;
 bool bInvertY=false;
 /** Button names shown for the gamepad: 0 Xbox (A, B, X, Y), 1 PlayStation (Cruz, Círculo...). */
 int32 PadGlyphs=0;
 TMap<FName,FKey> Keys;
 // Language (culture name).
 FString Culture=TEXT("pt-BR");

 struct FAction{FName Id;FText Label;FKey Default;};
 /** Remappable actions, in menu order. */
 static const TArray<FAction>& Actions();
 static const TArray<int32>& FrameLimits();
 static const TArray<FString>& Cultures();
 static FText CultureName(const FString& Name);
 /** TSR always; DLSS/FSR only when their plugin registered its console variables. */
 static TArray<FString> Upscalers();

 static FMareOptions Defaults();
 /** Current engine state (first run, before any file exists). */
 static FMareOptions FromEngine();
 static FString DefaultPath();
 bool LoadFile(const FString& Path);
 bool SaveFile(const FString& Path)const;
 void Sanitize();
 bool Equals(const FMareOptions& Other)const;

 bool IsCustomPreset()const;
 void SetPreset(int32 Level);
 FKey Key(FName Action)const;
 /** Assigns NewKey to Action; another action already on that key takes the old one (swap). */
 void Bind(FName Action,FKey NewKey);

 /** Options in effect (defaults in QA/automation runs, so scripted keys and cameras stay stable). */
 static const FMareOptions& Get();
 /** Replaces the options in effect and saves them (nothing is applied here). */
 static void Set(const FMareOptions& Options);
 static bool IsQARun();

 /** Scalability, 3D scale, upscaler, VSync and FPS cap; also saves UGameUserSettings. */
 void ApplyGraphics()const;
 /** Resolution and window mode, left unconfirmed; true when the video mode changed. */
 bool ApplyDisplay()const;
 void ApplyCulture()const;
 /** Key remaps on the player's input and FOV on the pawn's camera. */
 void ApplyToPlayer(APlayerController* Player)const;
 void ApplyKeys(UPlayerInput* Input)const;
 /** Once per process: upscaler, culture and the Lumen safety setting. */
 static void ApplyStartup();
 /** r.Lumen.AsyncCompute must stay 0 (GPU fault mitigation, see DefaultEngine.ini). */
 static void KeepLumenSafe();
};
