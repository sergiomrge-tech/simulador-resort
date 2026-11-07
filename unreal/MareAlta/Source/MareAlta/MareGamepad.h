#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Widgets/Input/SButton.h"

/** Device of the last real input: decides whether the HUD shows keys or gamepad buttons. */
enum class EMareInputDevice : uint8 { KeyboardMouse, Gamepad };

/**
 * Gamepad support (Xbox / PlayStation through XInput or Steam Input).
 *
 * Fixed layout (not remappable; the keyboard keys stay remappable in the options):
 *  left stick walk, right stick look (options: controller sensitivity, invert Y),
 *  A/Cross jump and swim up, X/Square interact, Y/Triangle or View/Create phone, Start/Options pause,
 *  LT/L2 hold or L3 toggle run, B/Circle dive (and back in menus),
 *  LB/RB (L1/R1) change tabs in the phone and in the options.
 *  Pool: either stick aims, hold RT/R2 for power and release to shoot, B/Circle leaves the match.
 * Interact is X (not A) because A is jump/swim up and the game is mostly walking around: pressing
 * A to talk/serve would also jump. In menus A always confirms (Slate "accept").
 *
 * Menus (main menu, pause, options, phone, stations, village dialogue, the letter) register here while
 * open: the first control gets focus when the menu opens with the gamepad, the D-pad / left stick move
 * the focus (Slate navigation), A presses and B goes back or closes. The mouse keeps working as before.
 */
namespace MareGamepad
{
 /** Gamepad key of a gameplay action (the remappable FMareOptions ids plus "Pause"); Invalid when none. */
 MAREALTA_API FKey PadKey(FName Action);
 /** Short button name: Xbox ("A", "LB", "Start") or PlayStation ("Cruz", "L1", "Options"). */
 MAREALTA_API FString PadLabel(const FKey& Key,bool bPlayStation);
 /** Label of an action for a device: the remapped keyboard key ("Esc" for pause) or the gamepad button. */
 MAREALTA_API FString ActionLabelFor(FName Action,EMareInputDevice Device,bool bPlayStation);
 /** Same for the device used last, with the button style chosen in the options. */
 MAREALTA_API FString ActionLabel(FName Action);

 MAREALTA_API EMareInputDevice LastDevice();
 MAREALTA_API void SetLastDevice(EMareInputDevice Device);
 MAREALTA_API bool UsingGamepad();

 /** Stick response: deadzone, then a squared curve for fine aim. Axis -1..1 -> -1..1. */
 MAREALTA_API float Curve(float Axis,float DeadZone=.12f);
 /** Look rate in controller input units per second at full deflection (x2.5 legacy scale ~ 140 deg/s). */
 inline constexpr float LookUnitsPerSecond=56.f;
 /** Pool aim rate in radians per second at full deflection. */
 inline constexpr float AimRadiansPerSecond=1.1f;

 /** Legacy mappings this module expects in Config/DefaultInput.ini; returns the missing ones (empty = all present). */
 MAREALTA_API TArray<FString> MissingDefaultMappings();

 /** Registers the Slate input pre-processor once (device tracking, menu back and first focus). */
 MAREALTA_API void Startup();

 /** A menu became visible: B/Circle calls OnBack while it is the topmost one. */
 MAREALTA_API void PushMenu(const TSharedRef<SWidget>& Root,TFunction<void()> OnBack);
 MAREALTA_API void PopMenu(const TSharedPtr<SWidget>& Root);
 MAREALTA_API TSharedPtr<SWidget> TopMenu();
 /** Calls the topmost menu's back action; false when no menu is open. */
 MAREALTA_API bool Back();

 /** Visible, enabled buttons/sliders/check boxes under Root in layout order (the root itself excluded). */
 MAREALTA_API void CollectFocusable(const TSharedRef<SWidget>& Root,TArray<TSharedRef<SWidget>>& Out);
 /** Index of the focused control inside Root, or -1. */
 MAREALTA_API int32 FocusedIndex(const TSharedRef<SWidget>& Root);
 /** Focuses control Index (clamped) of Root now; false when Root has no control. */
 MAREALTA_API bool FocusIndex(const TSharedRef<SWidget>& Root,int32 Index);
 /** Same on the next paint (after a rebuild); by default only while the gamepad is in use. */
 MAREALTA_API void FocusSoon(const TSharedRef<SWidget>& Root,int32 Index=0,bool bOnlyWithGamepad=true);
}

/** SButton that draws a thick outline while it has focus and the gamepad is in use. */
class SMarePadButton : public SButton
{
public:
 virtual int32 OnPaint(const FPaintArgs& Args,const FGeometry& AllottedGeometry,const FSlateRect& MyCullingRect,FSlateWindowElementList& OutDrawElements,
  int32 LayerId,const FWidgetStyle& InWidgetStyle,bool bParentEnabled)const override;
};
