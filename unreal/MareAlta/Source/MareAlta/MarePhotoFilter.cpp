// Photo filters (11/11, the last open item of "pesca e foto"): O / D-pad up cycles the look of the next photos (natural,
// summer, sepia, black and white, faded). The look is an unbound post-process volume owned by the controller: it shows
// for a few seconds as a preview when the player changes it and again on the frame the photo is taken, so the game is
// never played through a filter. Grading only (saturation, contrast, gain, vignette, grain): no SceneColorTint, whose
// luminance goes into the pre-exposure and clips Lumen's cached light (lesson of 06/11).
#include "MareGame.h"
#include "MareSimulation.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "HAL/IConsoleManager.h"

namespace
{
 struct FMarePhotoLook{const TCHAR* Message;float Saturation,Contrast;FVector Gain;float Vignette,Grain;};
 // Whole sentences (one translation key each): a glued "prefix + name" would not match any translation template.
 const FMarePhotoLook Looks[]={
  {TEXT("Filtro da foto: natural."),1.f,1.f,FVector(1,1,1),0.f,0.f},
  {TEXT("Filtro da foto: verão (cores vivas)."),1.28f,1.08f,FVector(1.05,1.,.94),.25f,0.f},
  {TEXT("Filtro da foto: sépia."),.12f,1.05f,FVector(1.13,1.,.76),.5f,.25f},
  {TEXT("Filtro da foto: preto e branco."),0.f,1.15f,FVector(1,1,1),.4f,.3f},
  {TEXT("Filtro da foto: desbotado, de máquina antiga."),.62f,.88f,FVector(1.02,1.,1.05),.35f,.2f}};
}

int32 AMareController::PhotoFilterCount(){return UE_ARRAY_COUNT(Looks);}

void AMareController::ShowPhotoFilter(float Seconds)
{
 auto World=GetWorld();if(!World)return;
 World->GetTimerManager().ClearTimer(PhotoFilterTimer);
 if(PhotoFilter<=0 || Seconds<=0){if(PhotoFilterVolume)PhotoFilterVolume->bEnabled=false;return;}
 if(!PhotoFilterVolume){FActorSpawnParameters P;P.Owner=this;P.ObjectFlags|=RF_Transient;
  PhotoFilterVolume=World->SpawnActor<APostProcessVolume>(FVector::ZeroVector,FRotator::ZeroRotator,P);if(!PhotoFilterVolume)return;
  PhotoFilterVolume->bUnbound=true;PhotoFilterVolume->Priority=80;PhotoFilterVolume->BlendWeight=1;}
 const FMarePhotoLook& L=Looks[FMath::Clamp(PhotoFilter,0,PhotoFilterCount()-1)];
 FPostProcessSettings& S=PhotoFilterVolume->Settings;S=FPostProcessSettings();
 S.bOverride_ColorSaturation=true;S.ColorSaturation=FVector4(L.Saturation,L.Saturation,L.Saturation,1);
 S.bOverride_ColorContrast=true;S.ColorContrast=FVector4(L.Contrast,L.Contrast,L.Contrast,1);
 S.bOverride_ColorGain=true;S.ColorGain=FVector4(L.Gain.X,L.Gain.Y,L.Gain.Z,1);
 S.bOverride_VignetteIntensity=true;S.VignetteIntensity=L.Vignette;
 S.bOverride_FilmGrainIntensity=true;S.FilmGrainIntensity=L.Grain;
 PhotoFilterVolume->bEnabled=true;
 World->GetTimerManager().SetTimer(PhotoFilterTimer,FTimerDelegate::CreateWeakLambda(this,[this](){if(PhotoFilterVolume)PhotoFilterVolume->bEnabled=false;}),Seconds,false);
}

void AMareController::SetPhotoFilter(int32 Index,float PreviewSeconds)
{
 PhotoFilter=FMath::Clamp(Index,0,PhotoFilterCount()-1);
 if(auto S=GetSimulation())S->LastMessage=Looks[PhotoFilter].Message;
 ShowPhotoFilter(PreviewSeconds);
}

void AMareController::CyclePhotoFilter()
{
 if(IsPaused() || bPhoneOpen || GameWidget.IsValid() || IsMainMenuOpen())return;
 SetPhotoFilter((PhotoFilter+1)%PhotoFilterCount(),4.f);
}

// QA: "mare.PhotoFilter <index> [seconds]" picks the look and holds it on screen (default 4 s; 0 = only on photos).
static FAutoConsoleCommandWithWorldAndArgs GMarePhotoFilterCmd(TEXT("mare.PhotoFilter"),TEXT("Photo filter: <index 0-4> [preview seconds]"),   // i18n:skip
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  auto PC=World?Cast<AMareController>(World->GetFirstPlayerController()):nullptr;if(!PC || Args.IsEmpty())return;
  const int32 Index=FCString::Atoi(*Args[0]);const float Seconds=Args.Num()>1?FCString::Atof(*Args[1]):4.f;
  PC->SetPhotoFilter(Index,Seconds);
  UE_LOG(LogTemp,Display,TEXT("MARE_PHOTO_FILTER index=%d of %d seconds=%.1f"),PC->PhotoFilter,AMareController::PhotoFilterCount(),Seconds);}));
