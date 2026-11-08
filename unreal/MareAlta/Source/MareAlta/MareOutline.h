#pragma once
#include "CoreMinimal.h"
class AMareServiceTarget;
class APlayerController;

/** Coloured outline around what the E key would use (08/11, Resort Simulator reference tip 1). The visible meshes of the
 *  focused target are drawn into custom depth and the post-process material M_PP_Outline (mare_outline.py) draws a
 *  warm edge around them. Called every frame by the HUD with the focused target (or null). */
namespace MareOutline
{
 MAREALTA_API void Update(APlayerController* Controller,AMareServiceTarget* Target);
 /** QA: how many mesh components are outlined now. */
 MAREALTA_API int32 Count();
}
