#pragma once
#include "CoreMinimal.h"

/** Loading screen of the packaged game (title art + a tip from tutorial.json), MareLoading.cpp. */
namespace MareLoading
{
 /** Registers the PreLoadMap hook (game module startup). */
 void Register();
}
