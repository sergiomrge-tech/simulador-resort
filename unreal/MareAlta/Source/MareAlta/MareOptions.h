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
 // GI and reflections default to Medium: UE 5.8's Lumen Lite (irradiance fields), about twice as fast as High.
 int32 Preset=2,Shadows=2,GlobalIllumination=1,Reflections=1,PostProcess=2,Textures=2,Foliage=2,AntiAliasing=2;
 int32 ViewDistance=2,Effects=2,Shading=2;
 /** Mesh detail (0 low .. 3 epic): how soon models switch to their simpler LODs (r.StaticMeshLODDistanceScale, r.SkeletalMeshLODBias). */
 int32 ModelDetail=2;
 /** People in the scenes: 0 few, 1 normal, 2 many (walkers on the streets and how far away people are still drawn). */
 int32 Crowd=1;
 /** Walkers on the village streets and draw distance of people (cm) for the Crowd option. */
 int32 CrowdWalkers()const;
 float CrowdDrawDistance()const;
 float ResolutionScale=80.f;
 FString Upscaler=TEXT("TSR");
 /** NVIDIA DLSS Frame Generation (Streamline plugin, RTX 40+): 0 off, 1 on (one generated frame per rendered one), 2 auto. */
 int32 FrameGeneration=0;
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
 // Accessibility.
 /** Size of the whole interface (HUD, phone, menus): 0.85 .. 1.5. */
 float TextScale=1.f;
 /** First-time tutorial tips (Content/Data/tutorial.json). */
 bool bTips=true;
 /** Changes are also told by sign (+ / -), not only by green and red. */
 bool bColorSafe=false;
 TMap<FName,FKey> Keys;
 // Language (culture name).
 FString Culture=TEXT("pt-BR");
 /** The language page before the title menu (MareLanguage.cpp) was confirmed once: it is not asked again. */
 bool bLanguageChosen=false;

 struct FAction{FName Id;FText Label;FKey Default;};
 /** Remappable actions, in menu order. */
 static const TArray<FAction>& Actions();
 static const TArray<int32>& FrameLimits();
 static const TArray<FString>& Cultures();
 static FText CultureName(const FString& Name);
 /** TSR always; DLSS/FSR only when their plugin registered its console variables. */
 static TArray<FString> Upscalers();
 /** The NVIDIA plugins are optional (Plugins/NVIDIA, tools/ue58/install_dlss.ps1): their Blueprint libraries are called by
  *  reflection, so the game builds and runs without them. True only on a GPU and driver that support the feature. */
 /** Set at PostEngineInit (MareAlta.cpp): the NVIDIA support queries are only valid after it (never in commandlets such as the cooker). */
 static bool bEngineReady;
 /** Applies the live options' upscaler and frame generation; called again at PostEngineInit. */
 static void ApplyNvidia();
 static bool DLSSSupported();
 static bool FrameGenerationSupported();
 /** Frames per second actually shown, generated ones included (0 when frame generation is not running). */
 static float PresentedFrameRate();

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
 /** Model detail (LOD distances) and the people draw distance of the Crowd option. */
 void ApplyDetail()const;
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
