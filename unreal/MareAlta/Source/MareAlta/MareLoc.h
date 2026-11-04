#pragma once
#include "CoreMinimal.h"

/**
 * Game translations (English, Spanish; Portuguese is the source language), Content/Localization/Mare/<culture>.json:
 *  - "loctext": {"Namespace,Key": "translation"} -> registered as UE polyglot text data, so every LOCTEXT follows the
 *    current culture like a compiled .locres would;
 *  - "strings": {"texto em português": "translation"} for text that reaches the screen as FString (code literals and
 *    Content/Data/*.json names, descriptions, dialogues). Keys may hold {0} {1} ... placeholders: a formatted string
 *    ("Repor o bar custa R$ 120.") matches the template "Repor o bar custa R$ {0}." and the values move into the
 *    translation's placeholders.
 * tools/ue58/i18n_extract.py lists the source texts and what is missing; -MareLocAudit logs every untranslated text
 * shown on screen (MARE_LOC_MISSING).
 */
namespace MareLoc
{
 /** Translation of a Portuguese text for the current culture (the text itself in Portuguese or when unknown). */
 MAREALTA_API FString Tr(const FString& Portuguese);
 MAREALTA_API FText Text(const FString& Portuguese);
 /** Loads the tables of the current culture and registers the LOCTEXT translations (call after a culture change). */
 MAREALTA_API void Reload();
 /** Short culture code in use: "pt", "en" or "es". */
 MAREALTA_API FString Language();
}
