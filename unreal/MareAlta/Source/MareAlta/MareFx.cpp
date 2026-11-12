// Feedback pops drawn by the HUD (see MareFx.h).
#include "MareFx.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "UObject/StrongObjectPtr.h"

namespace
{
 struct FPop{TWeakObjectPtr<UWorld> World;FVector At;MareFx::EKind Kind;FString Text;double Born;int32 Seed;};
 TArray<FPop> GPops;
 UTexture2D* Tex(const TCHAR* Path)
 {
  static TMap<FString,TStrongObjectPtr<UTexture2D>> Cache;
  if(auto* Found=Cache.Find(Path))return Found->Get();
  UTexture2D* T=LoadObject<UTexture2D>(nullptr,Path);Cache.Add(Path,TStrongObjectPtr<UTexture2D>(T));return T;
 }
 float Life(MareFx::EKind K){return K==MareFx::EKind::Coin?1.4f:K==MareFx::EKind::Sparkle?1.0f:1.3f;}
 void Sprite(UCanvas* C,UTexture2D* T,const FVector2D& P,float Size,const FLinearColor& Color)
 {
  if(!T)return;FCanvasTileItem Item(P-FVector2D(Size*.5f),T->GetResource(),FVector2D(Size),Color);Item.BlendMode=SE_BLEND_Translucent;C->DrawItem(Item);
 }
}

namespace MareFx
{
 int32 Alive(){return GPops.Num();}
 void Spawn(UWorld* World,const FVector& At,EKind Kind,const FString& Text)
 {
  if(!World)return;
  if(GPops.Num()>24)GPops.RemoveAt(0);
  GPops.Add({World,At,Kind,Text,World->GetTimeSeconds(),FMath::Rand()});
 }
 void Draw(UCanvas* Canvas,APlayerController* Controller)
 {
  if(!Canvas || !Controller)return;UWorld* World=Controller->GetWorld();const double Now=World->GetTimeSeconds();
  UTexture2D* Coin=Tex(TEXT("/Game/UI/Icons/T_Fx_Coin.T_Fx_Coin"));   // i18n:skip
  UTexture2D* Soft=Tex(TEXT("/Game/UI/Icons/T_Fx_Soft.T_Fx_Soft"));   // i18n:skip
  UTexture2D* Star=Tex(TEXT("/Game/UI/Icons/T_Icon_Star.T_Icon_Star"));   // i18n:skip
  const float Scale=Canvas->ClipY/1080.f;
  for(int32 I=GPops.Num()-1;I>=0;--I){
   FPop& P=GPops[I];const float T=float(Now-P.Born)/Life(P.Kind);
   if(T>=1.f || P.World.Get()!=World){GPops.RemoveAt(I);continue;}
   FVector2D S;if(!Controller->ProjectWorldLocationToScreen(P.At,S))continue;
   const float Fade=1.f-FMath::Square(FMath::Max(0.f,T-.55f)/.45f);
   FRandomStream R(P.Seed);
   switch(P.Kind){
   case EKind::Coin:{
    // the coin pops up, spins (squashed width) and floats away with the amount next to it
    const FVector2D At=S+FVector2D(0,-90.f*Scale*T);const float Spin=.6f+.4f*FMath::Abs(FMath::Cos(T*6.f));
    const float Size=70.f*Scale*(T<.15f?T/.15f:1.f);
    if(Coin){FCanvasTileItem Item(At-FVector2D(Size*.5f*Spin,Size*.5f),Coin->GetResource(),FVector2D(Size*FMath::Max(.15f,Spin),Size),FLinearColor(1,1,1,Fade));Item.BlendMode=SE_BLEND_Translucent;Canvas->DrawItem(Item);}
    if(!P.Text.IsEmpty()){FCanvasTextItem Txt(At+FVector2D(42.f*Scale,-22.f*Scale),FText::FromString(P.Text),GEngine->GetLargeFont(),FLinearColor(1.f,.86f,.3f,Fade));
     Txt.Scale=FVector2D(2.0f*Scale);Txt.EnableShadow(FLinearColor(0,0,0,.6f*Fade),FVector2D(2,2));Canvas->DrawItem(Txt);}
    break;}
   case EKind::Sparkle:
    // a ring of little stars bursting out and twinkling
    for(int32 K=0;K<9;++K){const float A=K/9.f*UE_TWO_PI+R.FRandRange(-.3f,.3f),Dist=(45.f+R.FRandRange(0.f,60.f))*Scale*FMath::Sqrt(T);
     const float Tw=.6f+.4f*FMath::Sin(T*20.f+K);
     Sprite(Canvas,Star,S+FVector2D(FMath::Cos(A),FMath::Sin(A))*Dist,(26.f+R.FRandRange(0.f,16.f))*Scale*(1.f-T*.5f),FLinearColor(1.f,.95f,.6f,Fade*Tw));}
    Sprite(Canvas,Soft,S,110.f*Scale*(.5f+T),FLinearColor(1.f,1.f,.8f,.45f*(1.f-T)));
    break;
   case EKind::Foam:
    // soft white puffs swelling and drifting up
    for(int32 K=0;K<12;++K){const FVector2D Off(R.FRandRange(-80.f,80.f),R.FRandRange(-40.f,30.f));
     const float Size=(50.f+R.FRandRange(0.f,40.f))*Scale*(.5f+T);
     Sprite(Canvas,Soft,S+Off*Scale-FVector2D(0,40.f*Scale*T),Size,FLinearColor(.94f,.98f,1.f,Fade));
     Sprite(Canvas,Soft,S+Off*Scale-FVector2D(0,40.f*Scale*T),Size*.45f,FLinearColor(1,1,1,Fade));}
    break;}
  }
 }
}

static FAutoConsoleCommandWithWorldAndArgs MareFxQA(TEXT("mare.Fx"),TEXT("QA: pops a feedback effect 1.5 m in front of the camera: coin | sparkle | foam."),   // i18n:skip
 FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
  APlayerController* PC=World?World->GetFirstPlayerController():nullptr;if(!PC)return;FVector Eye;FRotator View;PC->GetPlayerViewPoint(Eye,View);
  const FString K=Args.Num()?Args[0]:FString(TEXT("coin"));   // i18n:skip
  MareFx::Spawn(World,Eye+View.Vector()*150.f,K==TEXT("sparkle")?MareFx::EKind::Sparkle:K==TEXT("foam")?MareFx::EKind::Foam:MareFx::EKind::Coin,K==TEXT("coin")?FString(TEXT("+R$ 12")):FString());}));   // i18n:skip
