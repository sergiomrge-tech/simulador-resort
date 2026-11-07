#include "MareGamepad.h"
#include "MareOptions.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

/** Gamepad layout in DefaultInput.ini, HUD labels per input device, stick curve and options round trip. */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareGamepadMappingTest,"MareAlta.Gamepad.MappingsAndLabels",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareGamepadMappingTest::RunTest(const FString& Parameters)
{
 // Every gamepad mapping the character, controller and menus rely on is present.
 const TArray<FString> Missing=MareGamepad::MissingDefaultMappings();
 TestEqual(TEXT("No gamepad mapping missing"),Missing.Num(),0);
 for(const FString& Name:Missing)AddError(TEXT("Missing mapping: ")+Name);

 // The HUD shows the keyboard key or the gamepad button depending on the last input.
 const FString InteractKey=FMareOptions::Get().Key(TEXT("Interact")).GetDisplayName(false).ToString();
 TestEqual(TEXT("Keyboard interact = remapped key"),MareGamepad::ActionLabelFor(TEXT("Interact"),EMareInputDevice::KeyboardMouse,false),InteractKey);
 TestEqual(TEXT("Keyboard pause = Esc"),MareGamepad::ActionLabelFor(TEXT("Pause"),EMareInputDevice::KeyboardMouse,false),FString(TEXT("Esc")));
 TestEqual(TEXT("Xbox interact = X"),MareGamepad::ActionLabelFor(TEXT("Interact"),EMareInputDevice::Gamepad,false),FString(TEXT("X")));
 TestEqual(TEXT("Xbox jump = A"),MareGamepad::ActionLabelFor(TEXT("Jump"),EMareInputDevice::Gamepad,false),FString(TEXT("A")));
 TestEqual(TEXT("Xbox phone = Y"),MareGamepad::ActionLabelFor(TEXT("Phone"),EMareInputDevice::Gamepad,false),FString(TEXT("Y")));
 TestEqual(TEXT("Xbox dive = B"),MareGamepad::ActionLabelFor(TEXT("Dive"),EMareInputDevice::Gamepad,false),FString(TEXT("B")));
 TestEqual(TEXT("Xbox run = LT"),MareGamepad::ActionLabelFor(TEXT("Sprint"),EMareInputDevice::Gamepad,false),FString(TEXT("LT")));
 TestEqual(TEXT("Xbox pause = Start"),MareGamepad::ActionLabelFor(TEXT("Pause"),EMareInputDevice::Gamepad,false),FString(TEXT("Start")));
 TestEqual(TEXT("PlayStation interact = Quadrado"),MareGamepad::ActionLabelFor(TEXT("Interact"),EMareInputDevice::Gamepad,true),FString(TEXT("Quadrado")));
 TestEqual(TEXT("PlayStation pause = Options"),MareGamepad::ActionLabelFor(TEXT("Pause"),EMareInputDevice::Gamepad,true),FString(TEXT("Options")));
 TestEqual(TEXT("PlayStation R2"),MareGamepad::PadLabel(EKeys::Gamepad_RightTrigger,true),FString(TEXT("R2")));

 // Device tracking drives ActionLabel.
 const EMareInputDevice Before=MareGamepad::LastDevice();
 MareGamepad::SetLastDevice(EMareInputDevice::Gamepad);
 TestTrue(TEXT("Gamepad in use"),MareGamepad::UsingGamepad());
 TestEqual(TEXT("Label follows the gamepad"),MareGamepad::ActionLabel(TEXT("Jump")),MareGamepad::PadLabel(EKeys::Gamepad_FaceButton_Bottom,FMareOptions::Get().PadGlyphs==1));
 MareGamepad::SetLastDevice(EMareInputDevice::KeyboardMouse);
 TestFalse(TEXT("Keyboard in use"),MareGamepad::UsingGamepad());
 TestEqual(TEXT("Label follows the keyboard"),MareGamepad::ActionLabel(TEXT("Interact")),InteractKey);
 MareGamepad::SetLastDevice(Before);

 // Stick curve: deadzone, full deflection, sign and the squared middle.
 TestEqual(TEXT("Inside the deadzone"),MareGamepad::Curve(.1f),0.f);
 TestTrue(TEXT("Full right"),FMath::IsNearlyEqual(MareGamepad::Curve(1.f),1.f));
 TestTrue(TEXT("Full left"),FMath::IsNearlyEqual(MareGamepad::Curve(-1.f),-1.f));
 TestTrue(TEXT("Squared middle"),FMath::IsNearlyEqual(MareGamepad::Curve(.56f,.12f),.25f,1e-3f));

 // Controller options survive a save/load and are clamped.
 const FString Path=FPaths::ProjectSavedDir()/TEXT("Automation/Gamepad")/FGuid::NewGuid().ToString(EGuidFormats::Digits)/TEXT("MareOptions.json");
 FMareOptions Custom=FMareOptions::Defaults();Custom.GamepadSensitivity=1.8f;Custom.PadGlyphs=1;
 TestTrue(TEXT("Saved"),Custom.SaveFile(Path));
 FMareOptions Read=FMareOptions::Defaults();TestTrue(TEXT("Loaded"),Read.LoadFile(Path));
 TestTrue(TEXT("Gamepad sensitivity kept"),FMath::IsNearlyEqual(Read.GamepadSensitivity,1.8f,1e-4f));
 TestEqual(TEXT("PlayStation buttons kept"),Read.PadGlyphs,1);
 TestTrue(TEXT("Round trip"),Read.Equals(Custom));
 Read.GamepadSensitivity=50.f;Read.PadGlyphs=7;Read.Sanitize();
 TestEqual(TEXT("Gamepad sensitivity clamped"),Read.GamepadSensitivity,3.f);TestEqual(TEXT("Button style clamped"),Read.PadGlyphs,1);
 TestTrue(TEXT("Gamepad keys are never keyboard remaps"),[&](){FMareOptions O=FMareOptions::Defaults();O.Keys.Add(TEXT("Jump"),EKeys::Gamepad_FaceButton_Bottom);O.Sanitize();return O.Key(TEXT("Jump"))==EKeys::SpaceBar;}());
 return true;
}

/** Menu navigation pieces that need no window: which controls take the focus, the menu stack and B. */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareGamepadMenuTest,"MareAlta.Gamepad.MenuFocusAndBack",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareGamepadMenuTest::RunTest(const FString& Parameters)
{
 const EMareInputDevice Before=MareGamepad::LastDevice();
 MareGamepad::SetLastDevice(EMareInputDevice::KeyboardMouse);   // no deferred focus while testing
 TSharedPtr<SWidget> First,Disabled,Hidden,Slider,Text;
 const TSharedRef<SVerticalBox> Root=SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(FText::FromString(TEXT("Título")))]
  +SVerticalBox::Slot().AutoHeight()[SAssignNew(First,SMarePadButton)]
  +SVerticalBox::Slot().AutoHeight()[SAssignNew(Disabled,SMarePadButton).IsEnabled(false)]
  +SVerticalBox::Slot().AutoHeight()[SNew(SBox).Visibility(EVisibility::Collapsed)[SAssignNew(Hidden,SButton)]]
  +SVerticalBox::Slot().AutoHeight()[SAssignNew(Text,SEditableTextBox)]
  +SVerticalBox::Slot().AutoHeight()[SAssignNew(Slider,SSlider).IsFocusable(true)];
 TArray<TSharedRef<SWidget>> Controls;MareGamepad::CollectFocusable(Root,Controls);
 auto Has=[&Controls](const TSharedPtr<SWidget>& W){return Controls.ContainsByPredicate([&W](const TSharedRef<SWidget>& C){return &C.Get()==W.Get();});};
 TestTrue(TEXT("Enabled button focusable"),Has(First));
 TestTrue(TEXT("Slider focusable"),Has(Slider));
 TestFalse(TEXT("Disabled button skipped"),Has(Disabled));
 TestFalse(TEXT("Collapsed button skipped"),Has(Hidden));
 TestFalse(TEXT("Text box skipped"),Has(Text));
 TestTrue(TEXT("First control is the first button"),Controls.Num()>0 && &Controls[0].Get()==First.Get());

 int32 Backs=0;
 MareGamepad::PushMenu(Root,[&Backs](){++Backs;});
 TestTrue(TEXT("Pushed menu is on top"),MareGamepad::TopMenu()==TSharedPtr<SWidget>(Root));
 TestTrue(TEXT("B is taken by the menu"),MareGamepad::Back());
 TestEqual(TEXT("Back callback ran"),Backs,1);
 {
  const TSharedRef<SWidget> Inner=SNew(SVerticalBox)+SVerticalBox::Slot()[SNew(SMarePadButton)];
  MareGamepad::PushMenu(Inner,[&Backs](){Backs+=10;});
  TestTrue(TEXT("Newest menu on top"),MareGamepad::TopMenu()==TSharedPtr<SWidget>(Inner));
  MareGamepad::Back();TestEqual(TEXT("Only the top menu goes back"),Backs,11);
 }
 TestTrue(TEXT("Destroyed menu leaves the stack"),MareGamepad::TopMenu()==TSharedPtr<SWidget>(Root));
 MareGamepad::PopMenu(Root);
 TestFalse(TEXT("Popped menu is gone"),MareGamepad::TopMenu()==TSharedPtr<SWidget>(Root));
 MareGamepad::SetLastDevice(Before);
 return true;
}
#endif
