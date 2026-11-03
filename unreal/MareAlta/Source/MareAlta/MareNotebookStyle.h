#pragma once
// "Caderno do Quiosque": the UI style of the whole game (phone, menus, dialogues, letter). Moved out of
// MareGame.cpp on 03/11 so every panel uses it; old flat cards (MareUI) were converted.
#include "CoreMinimal.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Fonts/CompositeFont.h"
#include "Styling/SlateTypes.h"
#include "Styling/CoreStyle.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Rendering/DrawElements.h"
#include "Misc/Paths.h"

/** "Caderno do Quiosque" (phone option 3, chosen by the user on 01/11): kraft cover, notebook divider tabs,
 *  lined paper, handwriting, price tags and an EM USO stamp. Fonts are OFL files in Content/UI/Fonts. */
namespace MareNotebook
{
 inline FLinearColor Hex(uint8 R,uint8 G,uint8 B,float A=1.f){FLinearColor C(FColor(R,G,B));C.A=A;return C;}
 inline FSlateRenderTransform Tilt(float Degrees){return FSlateRenderTransform(FQuat2D(FMath::DegreesToRadians(Degrees)));}
 const FLinearColor Kraft=Hex(227,207,166),Paper=Hex(255,251,240),Rule=Hex(222,233,240),Margin=Hex(233,166,160),Ink=Hex(46,32,20),
  Brown=Hex(122,59,28),Faded=Hex(107,78,46),Pencil=Hex(128,104,76),Green=Hex(70,104,48),Red=Hex(178,58,40),Tag=Hex(255,243,201),
  TagEdge=Hex(201,168,106),Marker=Hex(255,229,138);
 inline const FLinearColor& TabColor(int32 I){static const FLinearColor C[]={Hex(246,185,168),Hex(191,224,196),Hex(188,215,238),Hex(247,220,142),Hex(216,195,238),Hex(243,199,156),Hex(206,226,170)};return C[FMath::Clamp(I,0,6)];}
 inline FSlateFontInfo Font(const TCHAR* File,float Size,const char* Fallback)
 {
  static TMap<FString,TSharedPtr<const FCompositeFont>> Cache;
  if(!Cache.Contains(File)){const FString Path=FPaths::ProjectContentDir()/TEXT("UI/Fonts")/File;
   TSharedPtr<const FCompositeFont> Loaded;if(FPaths::FileExists(Path))Loaded=MakeShared<FStandaloneCompositeFont>(NAME_None,Path,EFontHinting::Default,EFontLoadingPolicy::LazyLoad);Cache.Add(File,Loaded);}
  const auto& Composite=Cache[File];return Composite.IsValid()?FSlateFontInfo(Composite,Size):FCoreStyle::GetDefaultFontStyle(Fallback,Size);
 }
 inline FSlateFontInfo Hand(float Size){return Font(TEXT("PatrickHand-Regular.ttf"),Size,"Regular");}
 inline FSlateFontInfo Body(float Size,bool bBold=false){return Font(bBold?TEXT("Nunito-ExtraBold.ttf"):TEXT("Nunito-SemiBold.ttf"),Size,bBold?"Bold":"Regular");}
 inline const FSlateRoundedBoxBrush& Cover(){static const FSlateRoundedBoxBrush B(Kraft,18.f);return B;}
 inline const FSlateRoundedBoxBrush& Sheet(){static const FSlateRoundedBoxBrush B(Paper,FVector4(0,12,0,0));return B;}
 inline const FSlateRoundedBoxBrush& TabBrush(const FLinearColor& C){static TMap<uint32,TSharedPtr<FSlateRoundedBoxBrush>> Cache;auto& B=Cache.FindOrAdd(C.ToFColor(false).ToPackedARGB());if(!B.IsValid())B=MakeShared<FSlateRoundedBoxBrush>(C,FVector4(10,10,0,0));return *B;}
 inline const FSlateRoundedBoxBrush& TagBrush(){static const FSlateRoundedBoxBrush B(Tag,FVector4(6,22,6,6),TagEdge,1.5f);return B;}
 inline const FSlateRoundedBoxBrush& TagShadow(){static const FSlateRoundedBoxBrush B(Hex(217,195,151),FVector4(6,22,6,6));return B;}
 inline const FSlateRoundedBoxBrush& Hole(){static const FSlateRoundedBoxBrush B(Kraft,5.f,Hex(168,134,84),1.5f);return B;}
 inline const FSlateRoundedBoxBrush& StampBrush(const FLinearColor& C){static TMap<uint32,TSharedPtr<FSlateRoundedBoxBrush>> Cache;auto& B=Cache.FindOrAdd(C.ToFColor(false).ToPackedARGB());if(!B.IsValid())B=MakeShared<FSlateRoundedBoxBrush>(FLinearColor::Transparent,6.f,C,2.5f);return *B;}
 inline const FSlateRoundedBoxBrush& MarkerBrush(){static const FSlateRoundedBoxBrush B(Marker,3.f);return B;}
 inline const FSlateRoundedBoxBrush& Note(){static const FSlateRoundedBoxBrush B(Hex(255,236,150),4.f,Hex(214,190,120),1.f);return B;}
 inline const FButtonStyle& InkButton(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateRoundedBoxBrush(Brown,5.f)).SetHovered(FSlateRoundedBoxBrush(Hex(146,76,40),5.f)).SetPressed(FSlateRoundedBoxBrush(Hex(92,42,18),5.f)).SetDisabled(FSlateRoundedBoxBrush(Hex(190,170,140),5.f));return S;}
 inline const FButtonStyle& Plain(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateNoResource()).SetHovered(FSlateRoundedBoxBrush(Hex(255,229,138,.55f),3.f)).SetPressed(FSlateRoundedBoxBrush(Marker,3.f));return S;}
 inline TSharedRef<STextBlock> HandText(const FString& V,float Size,const FLinearColor& C=Ink){return SNew(STextBlock).Text(FText::FromString(V)).Font(Hand(Size)).ColorAndOpacity(C).AutoWrapText(true);}
 inline TSharedRef<STextBlock> BodyText(const FString& V,float Size=12,const FLinearColor& C=Ink,bool bBold=false){return SNew(STextBlock).Text(FText::FromString(V)).Font(Body(Size,bBold)).ColorAndOpacity(C).AutoWrapText(true);}
 /** Rubber stamp (EM USO, CONTRATADO, SEU): red or green ink, slightly crooked. */
 inline TSharedRef<SWidget> Stamp(const FString& V,const FLinearColor& C=Red)
 {
  return SNew(SBox).HAlign(HAlign_Left)[SNew(SBorder).BorderImage(&StampBrush(C)).Padding(FMargin(8,0)).RenderTransform(Tilt(-7)).RenderTransformPivot(FVector2D(.5f))[HandText(V,18,C)]];
 }
 /** Paper price tag with the string hole and a solid shadow; tilt in degrees. */
 inline TSharedRef<SWidget> PriceTag(TSharedRef<SWidget> Content,float Tilt=0,const FString& Tooltip=FString())
 {
  return SNew(SBox).Padding(FMargin(2,4,6,8)).ToolTipText(Tooltip.IsEmpty()?FText::GetEmpty():FText::FromString(Tooltip))[SNew(SOverlay).RenderTransform(MareNotebook::Tilt(Tilt)).RenderTransformPivot(FVector2D(.5f))
   +SOverlay::Slot().Padding(FMargin(3,4,-3,-4))[SNew(SBorder).BorderImage(&TagShadow())]
   +SOverlay::Slot()[SNew(SBorder).BorderImage(&TagBrush()).Padding(FMargin(12,14,10,10))[Content]]
   +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(FMargin(0,7,10,0))[SNew(SBox).WidthOverride(10).HeightOverride(10)[SNew(SBorder).BorderImage(&Hole())]]];
 }
}
/** Lined notebook paper with the red margin; drawn behind the scrolling page. */
class SPaperLines : public SLeafWidget
{
public:
 SLATE_BEGIN_ARGS(SPaperLines):_MarginX(0){} SLATE_ATTRIBUTE(float,MarginX) SLATE_END_ARGS()
 inline void Construct(const FArguments& Args){MarginX=Args._MarginX;}
 virtual FVector2D ComputeDesiredSize(float)const override{return FVector2D(10,10);}
 virtual int32 OnPaint(const FPaintArgs&,const FGeometry& Geometry,const FSlateRect&,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle&,bool)const override
 {
  const FVector2f Size=FVector2f(Geometry.GetLocalSize());
  FSlateDrawElement::MakeBox(Out,Layer,Geometry.ToPaintGeometry(),&MareNotebook::Sheet());
  for(float Y=34;Y<Size.Y;Y+=28)FSlateDrawElement::MakeLines(Out,Layer+1,Geometry.ToPaintGeometry(),TArray<FVector2f>{FVector2f(0,Y),FVector2f(Size.X,Y)},ESlateDrawEffect::None,MareNotebook::Rule,true,1.f);
  const float X=MarginX.Get();if(X>0)FSlateDrawElement::MakeLines(Out,Layer+1,Geometry.ToPaintGeometry(),TArray<FVector2f>{FVector2f(X,0),FVector2f(X,Size.Y)},ESlateDrawEffect::None,MareNotebook::Margin,true,2.f);
  return Layer+1;
 }
private:
 TAttribute<float> MarginX;
};

namespace MareNotebook
{
 inline const FSlateRoundedBoxBrush& PinBrush(){static const FSlateRoundedBoxBrush B(Hex(226,85,63),8.f,Hex(150,40,30),1.5f);return B;}
 inline const FSlateRoundedBoxBrush& ShadowBrush(){static const FSlateRoundedBoxBrush B(Hex(60,40,20,.28f),FVector4(0,12,0,0));return B;}
 /** Secondary button: a paper tag with a kraft edge (the ink button is the main one). */
 inline const FButtonStyle& TagButton(){static const FButtonStyle S=FButtonStyle().SetNormal(FSlateRoundedBoxBrush(Tag,5.f,TagEdge,1.5f))
  .SetHovered(FSlateRoundedBoxBrush(Marker,5.f,TagEdge,1.5f)).SetPressed(FSlateRoundedBoxBrush(Hex(240,210,120),5.f,TagEdge,1.5f));return S;}
 /** A sheet of the notebook for any panel: lined paper with the red margin, a pin on top and a soft shadow.
  *  Content starts right of the margin. */
 inline TSharedRef<SWidget> Page(TSharedRef<SWidget> Content,FMargin Padding=FMargin(58,24,24,22),float MarginX=44)
 {
  return SNew(SOverlay)
   +SOverlay::Slot().Padding(FMargin(5,7,-5,-7))[SNew(SBorder).BorderImage(&ShadowBrush())]
   +SOverlay::Slot()[SNew(SPaperLines).MarginX(MarginX)]
   +SOverlay::Slot().Padding(Padding)[Content]
   +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Top).Padding(0,-7,0,0)[SNew(SBox).WidthOverride(16).HeightOverride(16)[SNew(SBorder).BorderImage(&PinBrush())]];
 }
 /** Main action: ink button with the handwriting label. */
 inline TSharedRef<STextBlock> InkLabel(const FString& V,float Size=17){return SNew(STextBlock).Text(FText::FromString(V)).Font(Hand(Size)).ColorAndOpacity(Tag);}
}
