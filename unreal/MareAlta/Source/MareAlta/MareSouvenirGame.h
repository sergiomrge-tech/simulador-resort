#pragma once
#include "CoreMinimal.h"
class AMareController;
class SWidget;

/** Souvenir shop screen (CHECKLIST_EXPANSOES 3.5, SMareSouvenirGame in MareSouvenirGame.cpp): gift wrap at the counter,
 *  shelf and village makers, postcards from the album. The logic lives in MareSouvenir.cpp (UMareSimulation). */
namespace MareSouvenirGame
{
 TSharedRef<SWidget> Make(AMareController* Owner);
 bool IsOpen();
 /** QA over the open screen: "tab:n", "fold:id", "ribbon:id", "deliver", "perfect", "wrong", "restart", "state". */
 FString QA(const FString& Cmd);
}
