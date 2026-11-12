#pragma once
#include "CoreMinimal.h"
class APlayerController;

/**
 * Language page before the title menu (09/11, Sergio: "na tela inicial quero algo assim, antes de chegar no menu", with a
 * reference grid of flags): a dark title bar, one tile per translated language (flag and the language's own name), the
 * hint that it can be changed later in Options and a big Confirm button. The page speaks the selected language: picking
 * a tile switches its own texts. Confirm saves the choice (FMareOptions::Culture, "language_chosen") and applies it.
 * Shown once, on the first start of the packaged game; QA: "mare.ShowUI language".
 */
namespace MareLanguage
{
 /** First start of the game: no language confirmed yet, not in the editor, not a QA run, no -culture= on the command line. */
 MAREALTA_API bool ShouldAsk();
 /** Shows the page over the title menu; OnDone runs after Confirm (the menu then rebuilds its texts in the new language). */
 MAREALTA_API void Show(APlayerController* PC,TFunction<void()> OnDone);
 MAREALTA_API bool IsOpen();
 /** QA: selects a language on the open page (its texts switch to it), as a click would. */
 MAREALTA_API void QASelect(const FString& Culture);
 MAREALTA_API void Close();
 /** Text of the game in a given culture (the translation table of that file; Portuguese for pt-BR or when missing). */
 MAREALTA_API FString TrIn(const FString& Culture,const FString& Portuguese);
}
