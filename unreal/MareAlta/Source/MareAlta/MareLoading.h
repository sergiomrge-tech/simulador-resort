#pragma once
#include "CoreMinimal.h"

/** Loading screen of the packaged game (title art + a tip from tutorial.json), MareLoading.cpp. */
namespace MareLoading
{
 /** Registers the PreLoadMap hook (game module startup). */
 void Register();
 /** Shader warm-up (09/11): while the PSO precaching of the loaded world runs, boosts it and, when bOverlay, holds a
  *  "preparing the graphics" page with a progress bar over the title; logs MARE_PSO lines (warm-up and, every minute,
  *  the PSOs the game still had to create while playing). Packaged game only. */
 void ShaderWarmup(bool bOverlay);
 /** The title closed: drops the page (the warm-up keeps running in the background until it ends). */
 void EndWarmup();
 /** QA ("mare.ShowUI loading" / "mare.ShowUI warmup"): shows or hides that page over the viewport, also in the editor. */
 void QAShow(bool bWarmup);
}
