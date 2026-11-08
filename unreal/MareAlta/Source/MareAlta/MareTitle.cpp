// Title screen camera (07/11): a smooth loop through the points of Content/Data/title.json (Catmull-Rom positions,
// eased rotations), on its own while the main menu is up. AMareController::OpenMainMenu spawns it in title mode.
#include "MareTitle.h"
#include "HAL/IConsoleManager.h"
#include "Camera/CameraComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

static TSharedPtr<FJsonObject> TitleDefs()
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/title.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

double AMareTitleCamera::TitleMinutes(){double H=17.3;TitleDefs()->TryGetNumberField(TEXT("hour"),H);return H*60.0;}

AMareTitleCamera::AMareTitleCamera()
{
 PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.bTickEvenWhenPaused=true;
 GetCameraComponent()->SetConstraintAspectRatio(false);   // no black bars in a non-16:9 window (lesson of 06/11)
 GetCameraComponent()->SetFieldOfView(70.f);
}

void AMareTitleCamera::BeginPlay()
{
 Super::BeginPlay();
 const auto D=TitleDefs();double Seconds=80;D->TryGetNumberField(TEXT("loop_seconds"),Seconds);Loop=FMath::Max(10.f,float(Seconds));
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(D->TryGetArrayField(TEXT("points"),List))for(const auto& V:*List){const auto& A=V->AsArray();if(A.Num()<5)continue;
  Points.Add(FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber()));Angles.Add(FRotator(A[3]->AsNumber(),A[4]->AsNumber(),0));}
 if(Points.Num()<2){Points={FVector(3000,-3600,500),FVector(5000,-3400,500)};Angles={FRotator(-6,60,0),FRotator(-6,120,0)};}
 Place(0);
}

void AMareTitleCamera::Place(float T)
{
 const int32 N=Points.Num();const float U=FMath::Fmod(T/Loop,1.f)*N;const int32 I=FMath::FloorToInt(U)%N;const float F=U-FMath::FloorToFloat(U);
 auto P=[&](int32 K){return Points[(K%N+N)%N];};
 const FVector P0=P(I-1),P1=P(I),P2=P(I+1),P3=P(I+2);
 // Catmull-Rom through the points: a continuous, unhurried glide with no stops at the corners.
 const float F2=F*F,F3=F2*F;
 const FVector Pos=.5f*((2.f*P1)+(-P0+P2)*F+(2.f*P0-5.f*P1+4.f*P2-P3)*F2+(-P0+3.f*P1-3.f*P2+P3)*F3);
 const float E=F*F*(3.f-2.f*F);
 const FQuat Q=FQuat::Slerp(Angles[I].Quaternion(),Angles[(I+1)%N].Quaternion(),E);
 SetActorLocationAndRotation(Pos,Q);
}

void AMareTitleCamera::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);Time+=DeltaSeconds;Place(Time);
}

// ---------------------------------------------------------------------------------------------------------------------
// Story opening (new game only, before the bus arrival).
#include "MareGame.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "Engine/Texture2D.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Engine.h"
#include "Slate/SlateBrushAsset.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "UObject/StrongObjectPtr.h"

class SMareStory : public SCompoundWidget
{
public:
 SLATE_BEGIN_ARGS(SMareStory){} SLATE_ARGUMENT(TFunction<void()>,OnDone) SLATE_END_ARGS()
 struct FPanel{TStrongObjectPtr<UTexture2D> Tex;FSlateBrush Brush;FString Text;};
 TArray<TSharedPtr<FPanel>> Panels;int32 Index=0;double Shown=0;TFunction<void()> Done;bool bClosed=false;
 void Construct(const FArguments& Args)
 {
  Done=Args._OnDone;
  const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
  if(TitleDefs()->TryGetArrayField(TEXT("story"),List))for(const auto& V:*List){const auto O=V->AsObject();auto P=MakeShared<FPanel>();
   P->Text=O->GetStringField(TEXT("text"));
   if(UTexture2D* T=LoadObject<UTexture2D>(nullptr,*O->GetStringField(TEXT("image")))){P->Tex.Reset(T);P->Brush.SetResourceObject(T);P->Brush.ImageSize=FVector2D(1920,1080);}
   Panels.Add(P);}
  Shown=FPlatformTime::Seconds();
  ChildSlot[SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(.02f,.02f,.03f,1)).Padding(0)
   [SNew(SOverlay)
    // the postcard: the capture inside a cream border, slowly zooming (render transform from the panel's age)
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)[SNew(SBox).WidthOverride(1280).HeightOverride(720)
     [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(MareNotebook::Paper).Padding(16)
      [SNew(SBox).Clipping(EWidgetClipping::ClipToBounds)[SNew(SImage).Image_Lambda([this](){return Panels.IsValidIndex(Index)?&Panels[Index]->Brush:nullptr;})
       .RenderTransformPivot(FVector2D(.5f,.5f)).RenderTransform_Lambda([this](){const float A=FMath::Min(1.f,float(FPlatformTime::Seconds()-Shown)/9.f);
        return TOptional<FSlateRenderTransform>(FSlateRenderTransform(1.f+.06f*A,FVector2D(-12.f*A,-6.f*A)));})
       .ColorAndOpacity_Lambda([this](){const float A=FMath::Clamp(float(FPlatformTime::Seconds()-Shown)/.8f,0.f,1.f);return FLinearColor(1,1,1,A);})]]]]
    +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,40)[SNew(SBox).WidthOverride(1100)
     [SNew(STextBlock).Text_Lambda([this](){return Panels.IsValidIndex(Index)?MareLoc::Text(Panels[Index]->Text):FText::GetEmpty();}).Font(MareNotebook::Hand(34))
      .ColorAndOpacity(MareNotebook::Hex(255,246,214)).Justification(ETextJustify::Center).AutoWrapText(true).ShadowOffset(FVector2D(2,2)).ShadowColorAndOpacity(FLinearColor(0,0,0,.7f))]]
    +SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom).Padding(0,0,30,14)[SNew(STextBlock).Text(MareLoc::Text(TEXT("Espaço · continuar      Esc · pular"))).Font(MareNotebook::Body(12)).ColorAndOpacity(FLinearColor(1,1,1,.6f))]]];
  if(Panels.IsEmpty())Close();
 }
 virtual bool SupportsKeyboardFocus()const override{return true;}
 virtual FReply OnKeyDown(const FGeometry&,const FKeyEvent& Event) override
 {
  const FKey K=Event.GetKey();
  if(K==EKeys::Escape || K==EKeys::Gamepad_FaceButton_Right){Close();return FReply::Handled();}
  Next();return FReply::Handled();
 }
 virtual FReply OnMouseButtonDown(const FGeometry&,const FPointerEvent&) override{Next();return FReply::Handled();}
 virtual void Tick(const FGeometry& G,const double Time,const float Dt) override
 {
  SCompoundWidget::Tick(G,Time,Dt);
  if(FPlatformTime::Seconds()-Shown>9.0)Next();   // each card stays nine seconds unless advanced
 }
 void Next(){if(++Index>=Panels.Num())Close();else Shown=FPlatformTime::Seconds();}
 void Close(){if(bClosed)return;bClosed=true;if(Done){auto F=Done;Done=nullptr;F();}}
};

static TWeakPtr<SMareStory> GStory;
namespace MareStory
{
 bool IsOpen(){return GStory.IsValid();}
 bool Show(AMareController* Owner,TFunction<void()> OnDone)
 {
  if(!Owner || !GEngine || !GEngine->GameViewport || !TitleDefs()->HasField(TEXT("story")))return false;
  TWeakObjectPtr<AMareController> Weak(Owner);
  TSharedPtr<SMareStory> Holder;
  const TSharedRef<SMareStory> W=SNew(SMareStory).OnDone([Weak,OnDone](){
   if(Weak.IsValid() && GEngine && GEngine->GameViewport){if(auto Pinned=GStory.Pin())GEngine->GameViewport->RemoveViewportWidgetContent(Pinned.ToSharedRef());
    Weak->bShowMouseCursor=false;Weak->SetInputMode(FInputModeGameOnly());Weak->ResetIgnoreMoveInput();Weak->ResetIgnoreLookInput();}
   GStory.Reset();if(OnDone)OnDone();});
  GStory=W;
  GEngine->GameViewport->AddViewportWidgetContent(W,60);
  Owner->SetInputMode(FInputModeUIOnly().SetWidgetToFocus(W));Owner->SetIgnoreMoveInput(true);Owner->SetIgnoreLookInput(true);
  return true;
 }
}

static FAutoConsoleCommandWithWorldAndArgs MareStoryQA(TEXT("mare.Story"),TEXT("QA: shows the new-game story postcards now."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&,UWorld* World){
  if(auto PC=Cast<AMareController>(World?World->GetFirstPlayerController():nullptr))MareStory::Show(PC,nullptr);}));
