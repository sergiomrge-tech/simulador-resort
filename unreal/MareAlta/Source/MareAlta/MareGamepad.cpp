#include "MareGamepad.h"
#include "MareOptions.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/InputSettings.h"
#include "Layout/WidgetPath.h"
#include "Rendering/DrawElements.h"
#include "Widgets/Layout/SScrollBox.h"

namespace MareGamepadData
{
 EMareInputDevice Device=EMareInputDevice::KeyboardMouse;
 float ScrollAxis=0.f;   // right stick Y while a menu is open
 struct FMenu{TWeakPtr<SWidget> Root;TFunction<void()> OnBack;};
 TArray<FMenu>& Menus(){static TArray<FMenu> List;return List;}
 void Prune(){Menus().RemoveAll([](const FMenu& Menu){return !Menu.Root.IsValid();});}
 bool IsMenuKey(const FKey& Key)
 {
  return Key==EKeys::Gamepad_DPad_Up || Key==EKeys::Gamepad_DPad_Down || Key==EKeys::Gamepad_DPad_Left || Key==EKeys::Gamepad_DPad_Right
   || Key==EKeys::Gamepad_LeftStick_Up || Key==EKeys::Gamepad_LeftStick_Down || Key==EKeys::Gamepad_LeftStick_Left || Key==EKeys::Gamepad_LeftStick_Right
   || Key==EKeys::Gamepad_FaceButton_Bottom;
 }
 /** Topmost menu without any of its controls focused (the player clicked the world, a rebuild dropped the focus...). */
 TSharedPtr<SWidget> MenuWithoutFocus()
 {
  const TSharedPtr<SWidget> Top=MareGamepad::TopMenu();
  if(!Top.IsValid())return nullptr;
  TArray<TSharedRef<SWidget>> Controls;MareGamepad::CollectFocusable(Top.ToSharedRef(),Controls);
  return Controls.Num() && MareGamepad::FocusedIndex(Top.ToSharedRef())<0?Top:nullptr;
 }
 void FindScrollBoxes(const TSharedRef<SWidget>& Widget,TArray<TSharedRef<SScrollBox>>& Out);
 bool Contains(const TSharedRef<SWidget>& Widget,const SWidget* Wanted);
 /** Watches every Slate input before routing; consumes only B and the first press that gives a menu its focus. */
 class FProcessor : public IInputProcessor
 {
 public:
  /** Right stick scrolls the open menu: the scroll box around the focused control, else the first one that can scroll. */
  virtual void Tick(const float DeltaTime,FSlateApplication& App,TSharedRef<ICursor>)override
  {
   if(ScrollAxis==0.f)return;
   const TSharedPtr<SWidget> Top=MareGamepad::TopMenu();if(!Top.IsValid())return;
   TArray<TSharedRef<SScrollBox>> Boxes;FindScrollBoxes(Top.ToSharedRef(),Boxes);
   const TSharedPtr<SWidget> Focused=App.GetUserFocusedWidget(0);TSharedPtr<SScrollBox> Target;
   for(const auto& Box:Boxes)if(Box->GetScrollOffsetOfEnd()>0){if(!Target.IsValid())Target=Box;if(Focused.IsValid() && Contains(Box,Focused.Get()))Target=Box;}
   if(Target.IsValid())Target->SetScrollOffset(FMath::Clamp(Target->GetScrollOffset()-ScrollAxis*900.f*DeltaTime,0.f,Target->GetScrollOffsetOfEnd()));
  }
  virtual const TCHAR* GetDebugName()const override{return TEXT("MareGamepad");}
  virtual bool HandleKeyDownEvent(FSlateApplication&,const FKeyEvent& Event)override
  {
   const FKey Key=Event.GetKey();
   if(!Key.IsGamepadKey()){MareGamepad::SetLastDevice(EMareInputDevice::KeyboardMouse);return false;}
   MareGamepad::SetLastDevice(EMareInputDevice::Gamepad);
   if(Key==EKeys::Gamepad_FaceButton_Right)return !Event.IsRepeat() && MareGamepad::Back();
   if(IsMenuKey(Key))if(const TSharedPtr<SWidget> Menu=MenuWithoutFocus())return MareGamepad::FocusIndex(Menu.ToSharedRef(),0);
   return false;
  }
  virtual bool HandleAnalogInputEvent(FSlateApplication&,const FAnalogInputEvent& Event)override
  {
   const FKey Key=Event.GetKey();
   if(Key==EKeys::Gamepad_RightY)ScrollAxis=MareGamepad::Curve(Event.GetAnalogValue(),.2f);
   if(!Key.IsGamepadKey() || FMath::Abs(Event.GetAnalogValue())<.35f)return false;
   MareGamepad::SetLastDevice(EMareInputDevice::Gamepad);
   if(Key==EKeys::Gamepad_LeftX || Key==EKeys::Gamepad_LeftY)if(const TSharedPtr<SWidget> Menu=MenuWithoutFocus())return MareGamepad::FocusIndex(Menu.ToSharedRef(),0);
   return false;
  }
  virtual bool HandleMouseMoveEvent(FSlateApplication&,const FPointerEvent& Event)override
  {
   if(Event.GetCursorDelta().SizeSquared()>9.f)MareGamepad::SetLastDevice(EMareInputDevice::KeyboardMouse);
   return false;
  }
  virtual bool HandleMouseButtonDownEvent(FSlateApplication&,const FPointerEvent&)override{MareGamepad::SetLastDevice(EMareInputDevice::KeyboardMouse);return false;}
  virtual bool HandleMouseWheelOrGestureEvent(FSlateApplication&,const FPointerEvent&,const FPointerEvent*)override{MareGamepad::SetLastDevice(EMareInputDevice::KeyboardMouse);return false;}
 };
 void FindScrollBoxes(const TSharedRef<SWidget>& Widget,TArray<TSharedRef<SScrollBox>>& Out)
 {
  if(!Widget->GetVisibility().IsVisible())return;
  if(Widget->GetType()==TEXT("SScrollBox"))Out.Add(StaticCastSharedRef<SScrollBox>(Widget));
  if(FChildren* Children=Widget->GetChildren())for(int32 I=0;I<Children->Num();++I)FindScrollBoxes(Children->GetChildAt(I),Out);
 }
 bool Contains(const TSharedRef<SWidget>& Widget,const SWidget* Wanted)
 {
  if(&Widget.Get()==Wanted)return true;
  if(FChildren* Children=Widget->GetChildren())for(int32 I=0;I<Children->Num();++I)if(Contains(Children->GetChildAt(I),Wanted))return true;
  return false;
 }
 void Collect(const TSharedRef<SWidget>& Widget,TArray<TSharedRef<SWidget>>& Out,bool bRoot)
 {
  if(!Widget->GetVisibility().IsVisible())return;   // collapsed or hidden subtree
  if(!bRoot && Widget->SupportsKeyboardFocus()){const FName Type=Widget->GetType();
   if(Type==TEXT("SButton") || Type==TEXT("SMarePadButton") || Type==TEXT("SSlider") || Type==TEXT("SCheckBox")){if(Widget->IsEnabled())Out.Add(Widget);return;}}
  if(FChildren* Children=Widget->GetChildren())for(int32 I=0;I<Children->Num();++I)Collect(Children->GetChildAt(I),Out,false);
 }
 struct FPad{FName Action;FKey Key;};
 const TArray<FPad>& Pads()
 {
  static const TArray<FPad> List={{TEXT("Jump"),EKeys::Gamepad_FaceButton_Bottom},{TEXT("Interact"),EKeys::Gamepad_FaceButton_Left},
   {TEXT("Phone"),EKeys::Gamepad_FaceButton_Top},{TEXT("Dive"),EKeys::Gamepad_FaceButton_Right},{TEXT("Sprint"),EKeys::Gamepad_LeftTrigger},
   {TEXT("Pause"),EKeys::Gamepad_Special_Right},{TEXT("MoveForward"),EKeys::Gamepad_Left2D},{TEXT("MoveBack"),EKeys::Gamepad_Left2D},
   {TEXT("MoveLeft"),EKeys::Gamepad_Left2D},{TEXT("MoveRight"),EKeys::Gamepad_Left2D}};
  return List;
 }
}

FKey MareGamepad::PadKey(FName Action)
{
 const auto* Found=MareGamepadData::Pads().FindByPredicate([Action](const MareGamepadData::FPad& Pad){return Pad.Action==Action;});
 return Found?Found->Key:EKeys::Invalid;
}
FString MareGamepad::PadLabel(const FKey& Key,bool bPlayStation)
{
 struct FName2{FKey Key;const TCHAR* Xbox;const TCHAR* PlayStation;};
 static const FName2 Names[]={
  {EKeys::Gamepad_FaceButton_Bottom,TEXT("A"),TEXT("Cruz")},{EKeys::Gamepad_FaceButton_Right,TEXT("B"),TEXT("Círculo")},
  {EKeys::Gamepad_FaceButton_Left,TEXT("X"),TEXT("Quadrado")},{EKeys::Gamepad_FaceButton_Top,TEXT("Y"),TEXT("Triângulo")},
  {EKeys::Gamepad_LeftShoulder,TEXT("LB"),TEXT("L1")},{EKeys::Gamepad_RightShoulder,TEXT("RB"),TEXT("R1")},
  {EKeys::Gamepad_LeftTrigger,TEXT("LT"),TEXT("L2")},{EKeys::Gamepad_RightTrigger,TEXT("RT"),TEXT("R2")},
  {EKeys::Gamepad_LeftThumbstick,TEXT("L3"),TEXT("L3")},{EKeys::Gamepad_RightThumbstick,TEXT("R3"),TEXT("R3")},
  {EKeys::Gamepad_Special_Left,TEXT("View"),TEXT("Create")},{EKeys::Gamepad_Special_Right,TEXT("Start"),TEXT("Options")},
  {EKeys::Gamepad_Left2D,TEXT("Analógico esq."),TEXT("Analógico esq.")},{EKeys::Gamepad_Right2D,TEXT("Analógico dir."),TEXT("Analógico dir.")},
  {EKeys::Gamepad_DPad_Up,TEXT("Direcional cima"),TEXT("Direcional cima")},{EKeys::Gamepad_DPad_Down,TEXT("Direcional baixo"),TEXT("Direcional baixo")}};
 for(const auto& Name:Names)if(Name.Key==Key)return bPlayStation?Name.PlayStation:Name.Xbox;
 return Key.IsValid()?Key.GetDisplayName(false).ToString():FString();
}
FString MareGamepad::ActionLabelFor(FName Action,EMareInputDevice Device,bool bPlayStation)
{
 if(Device==EMareInputDevice::Gamepad){const FKey Pad=PadKey(Action);if(Pad.IsValid())return PadLabel(Pad,bPlayStation);}
 if(Action==TEXT("Pause"))return TEXT("Esc");
 const FKey Key=FMareOptions::Get().Key(Action);
 return Key.IsValid()?Key.GetDisplayName(false).ToString():FString();
}
FString MareGamepad::ActionLabel(FName Action){return ActionLabelFor(Action,LastDevice(),FMareOptions::Get().PadGlyphs==1);}
EMareInputDevice MareGamepad::LastDevice(){return MareGamepadData::Device;}
void MareGamepad::SetLastDevice(EMareInputDevice Device){MareGamepadData::Device=Device;}
bool MareGamepad::UsingGamepad(){return MareGamepadData::Device==EMareInputDevice::Gamepad;}
float MareGamepad::Curve(float Axis,float DeadZone)
{
 const float Size=FMath::Abs(Axis);if(Size<=DeadZone)return 0.f;
 const float T=FMath::Min(1.f,(Size-DeadZone)/FMath::Max(.01f,1.f-DeadZone));
 return FMath::Sign(Axis)*T*T;
}
TArray<FString> MareGamepad::MissingDefaultMappings()
{
 struct FAction{const TCHAR* Name;FKey Key;};
 struct FAxis{const TCHAR* Name;FKey Key;float Scale;};
 static const FAction Actions[]={{TEXT("Jump"),EKeys::Gamepad_FaceButton_Bottom},{TEXT("Interact"),EKeys::Gamepad_FaceButton_Left},
  {TEXT("Phone"),EKeys::Gamepad_FaceButton_Top},{TEXT("Phone"),EKeys::Gamepad_Special_Left},{TEXT("Pause"),EKeys::Gamepad_Special_Right},
  {TEXT("Sprint"),EKeys::Gamepad_LeftTrigger},{TEXT("SprintToggle"),EKeys::Gamepad_LeftThumbstick}};
 static const FAxis Axes[]={{TEXT("Forward"),EKeys::Gamepad_LeftY,1.f},{TEXT("Right"),EKeys::Gamepad_LeftX,1.f},
  {TEXT("LookPadX"),EKeys::Gamepad_RightX,1.f},{TEXT("LookPadY"),EKeys::Gamepad_RightY,-1.f},
  {TEXT("SwimVertical"),EKeys::Gamepad_FaceButton_Bottom,1.f},{TEXT("SwimVertical"),EKeys::Gamepad_FaceButton_Right,-1.f}};
 TArray<FString> Missing;const UInputSettings* Settings=GetDefault<UInputSettings>();
 for(const auto& Action:Actions){TArray<FInputActionKeyMapping> Found;Settings->GetActionMappingByName(Action.Name,Found);
  if(!Found.ContainsByPredicate([&](const FInputActionKeyMapping& M){return M.Key==Action.Key;}))Missing.Add(FString::Printf(TEXT("%s=%s"),Action.Name,*Action.Key.ToString()));}
 for(const auto& Axis:Axes){TArray<FInputAxisKeyMapping> Found;Settings->GetAxisMappingByName(Axis.Name,Found);
  if(!Found.ContainsByPredicate([&](const FInputAxisKeyMapping& M){return M.Key==Axis.Key && FMath::IsNearlyEqual(M.Scale,Axis.Scale);}))Missing.Add(FString::Printf(TEXT("%s=%s(%.0f)"),Axis.Name,*Axis.Key.ToString(),Axis.Scale));}
 return Missing;
}
void MareGamepad::Startup()
{
 static bool bDone=false;
 if(bDone || !FSlateApplication::IsInitialized())return;
 bDone=FSlateApplication::Get().RegisterInputPreProcessor(MakeShared<MareGamepadData::FProcessor>());
 for(const FString& Missing:MissingDefaultMappings())UE_LOG(LogTemp,Warning,TEXT("MareGamepad: mapping missing in DefaultInput.ini: %s"),*Missing);
}
void MareGamepad::PushMenu(const TSharedRef<SWidget>& Root,TFunction<void()> OnBack)
{
 using namespace MareGamepadData;Prune();
 Menus().RemoveAll([&Root](const FMenu& Menu){return Menu.Root.Pin().Get()==&Root.Get();});
 Menus().Add({Root,MoveTemp(OnBack)});
 FocusSoon(Root,0);
}
void MareGamepad::PopMenu(const TSharedPtr<SWidget>& Root)
{
 using namespace MareGamepadData;Menus().RemoveAll([&Root](const FMenu& Menu){return !Menu.Root.IsValid() || Menu.Root.Pin()==Root;});
}
TSharedPtr<SWidget> MareGamepad::TopMenu(){MareGamepadData::Prune();return MareGamepadData::Menus().Num()?MareGamepadData::Menus().Last().Root.Pin():nullptr;}
bool MareGamepad::Back()
{
 MareGamepadData::Prune();if(MareGamepadData::Menus().IsEmpty())return false;
 // Copy first: the callback usually closes the menu and changes the list.
 const TFunction<void()> OnBack=MareGamepadData::Menus().Last().OnBack;
 if(OnBack)OnBack();
 return true;
}
void MareGamepad::CollectFocusable(const TSharedRef<SWidget>& Root,TArray<TSharedRef<SWidget>>& Out){MareGamepadData::Collect(Root,Out,true);}
int32 MareGamepad::FocusedIndex(const TSharedRef<SWidget>& Root)
{
 if(!FSlateApplication::IsInitialized())return -1;
 const TSharedPtr<SWidget> Focused=FSlateApplication::Get().GetUserFocusedWidget(0);if(!Focused.IsValid())return -1;
 TArray<TSharedRef<SWidget>> Controls;CollectFocusable(Root,Controls);
 return Controls.IndexOfByPredicate([&Focused](const TSharedRef<SWidget>& Control){return &Control.Get()==Focused.Get();});
}
bool MareGamepad::FocusIndex(const TSharedRef<SWidget>& Root,int32 Index)
{
 if(!FSlateApplication::IsInitialized())return false;
 TArray<TSharedRef<SWidget>> Controls;CollectFocusable(Root,Controls);if(Controls.IsEmpty())return false;
 FSlateApplication::Get().SetAllUserFocus(Controls[FMath::Clamp(Index,0,Controls.Num()-1)],EFocusCause::Navigation);
 return true;
}
void MareGamepad::FocusSoon(const TSharedRef<SWidget>& Root,int32 Index,bool bOnlyWithGamepad)
{
 if(bOnlyWithGamepad && !UsingGamepad())return;
 const TWeakPtr<SWidget> Weak=Root;
 Root->RegisterActiveTimer(0.f,FWidgetActiveTimerDelegate::CreateLambda([Weak,Index,bOnlyWithGamepad](double,float){
  if(const TSharedPtr<SWidget> Pinned=Weak.Pin())if(!bOnlyWithGamepad || UsingGamepad())FocusIndex(Pinned.ToSharedRef(),Index);
  return EActiveTimerReturnType::Stop;}));
}

int32 SMarePadButton::OnPaint(const FPaintArgs& Args,const FGeometry& AllottedGeometry,const FSlateRect& MyCullingRect,FSlateWindowElementList& OutDrawElements,
 int32 LayerId,const FWidgetStyle& InWidgetStyle,bool bParentEnabled)const
{
 const int32 Layer=SButton::OnPaint(Args,AllottedGeometry,MyCullingRect,OutDrawElements,LayerId,InWidgetStyle,bParentEnabled);
 if(!MareGamepad::UsingGamepad() || !HasAnyUserFocus().IsSet())return Layer;
 static const FSlateRoundedBoxBrush Outline(FLinearColor::Transparent,9.f,FLinearColor(1.f,.74f,.18f),3.f);
 FSlateDrawElement::MakeBox(OutDrawElements,Layer+1,AllottedGeometry.ToInflatedPaintGeometry(FVector2D(4,4)),&Outline);
 return Layer+1;
}
