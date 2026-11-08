#pragma once
#include "CoreMinimal.h"
class UCanvas;
class APlayerController;
class UWorld;

/** Feedback pops (08/11, Resort Simulator reference tip 4): a coin with "+R$ x" rising when money comes in, a burst of
 *  sparkles where a table is cleaned, soft foam puffs where a room or towel is tidied. Drawn by the HUD on the Canvas
 *  at the projected world point (no Niagara asset needed; cheap: a few sprites for about a second). */
namespace MareFx
{
 enum class EKind:uint8{Coin,Sparkle,Foam};
 MAREALTA_API void Spawn(UWorld* World,const FVector& At,EKind Kind,const FString& Text=FString());
 MAREALTA_API void Draw(UCanvas* Canvas,APlayerController* Controller);
 /** QA: pops alive now. */
 MAREALTA_API int32 Alive();
}
