#pragma once
#include "CoreMinimal.h"

/** The full island (08/11/2026, docs/ue58/ILHA_PLANO.md): signed distance to the coast, made by tools/ue58/gen_island.py
 *  (Content/Data/island.json "sdf" + island_sdf.bin). The single source for everything that used to assume a straight
 *  beach along y = -54.5 m: the sea floor profile, the swimming floor, the sea's waves and foam. */
namespace MareIsland
{
 /** Distance to the coast in cm: negative on land, positive at sea (bilinear, 5 m grid). Far outside the field it
  *  keeps growing with the distance to the field's edge. Returns +1e6 when the field could not be loaded. */
 MAREALTA_API float ShoreDistance(float X,float Y);
 MAREALTA_API bool IsLoaded();
 /** The old straight-beach y that matches a distance from the coast in the bay (waterline at y -29.5 m): lets formulas
  *  written along y (the sea floor profile, the sea material) follow the coast all round the island. */
 MAREALTA_API float BayEquivalentY(float Distance);
 /** BayEquivalentY of the point's own coast distance (clamped to +-400 m): "how far up the beach", the way the old
  *  code read Position.Y (beach sounds, gulls, sand footprints, the beach umbrella), now on every shore. */
 MAREALTA_API float CoastY(float X,float Y);
}
