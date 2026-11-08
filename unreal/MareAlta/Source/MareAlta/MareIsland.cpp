// The full island: coast distance field (see MareIsland.h).
#include "MareIsland.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 struct FIslandField
 {
  bool bTried=false,bLoaded=false;
  FVector2D Origin=FVector2D::ZeroVector;float Cell=500;int32 W=0,H=0;float BayWaterline=-2950;
  TArray<float> Metres;
  void Load()
  {
   bTried=true;FString Text;TSharedPtr<FJsonObject> Root;
   const FString Dir=FPaths::ProjectContentDir()/TEXT("Data");   // i18n:skip
   if(!FFileHelper::LoadFileToString(Text,*(Dir/TEXT("island.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root) || !Root.IsValid())return;   // i18n:skip
   const TSharedPtr<FJsonObject>* Sdf=nullptr;if(!Root->TryGetObjectField(TEXT("sdf"),Sdf))return;   // i18n:skip
   const TArray<TSharedPtr<FJsonValue>>* O=nullptr;const TArray<TSharedPtr<FJsonValue>>* S=nullptr;
   if(!(*Sdf)->TryGetArrayField(TEXT("origin"),O) || !(*Sdf)->TryGetArrayField(TEXT("size"),S) || O->Num()<2 || S->Num()<2)return;   // i18n:skip
   Origin=FVector2D((*O)[0]->AsNumber(),(*O)[1]->AsNumber());W=int32((*S)[0]->AsNumber());H=int32((*S)[1]->AsNumber());
   double C=500;(*Sdf)->TryGetNumberField(TEXT("cell"),C);Cell=float(C);   // i18n:skip
   double Bay=-2950;Root->TryGetNumberField(TEXT("bay_waterline_y"),Bay);BayWaterline=float(Bay);   // i18n:skip
   TArray<uint8> Bytes;FString File=TEXT("island_sdf.bin");(*Sdf)->TryGetStringField(TEXT("file"),File);   // i18n:skip
   if(!FFileHelper::LoadFileToArray(Bytes,*(Dir/File)) || Bytes.Num()!=W*H*2){UE_LOG(LogTemp,Warning,TEXT("MARE_ISLAND sdf missing or wrong size"));return;}   // i18n:skip
   Metres.SetNumUninitialized(W*H);const FFloat16* Half=reinterpret_cast<const FFloat16*>(Bytes.GetData());
   for(int32 I=0;I<W*H;++I)Metres[I]=Half[I].GetFloat();
   bLoaded=true;
  }
  float At(int32 X,int32 Y)const{return Metres[FMath::Clamp(Y,0,H-1)*W+FMath::Clamp(X,0,W-1)];}
 };
 FIslandField& Field(){static FIslandField F;if(!F.bTried)F.Load();return F;}
}

namespace MareIsland
{
 bool IsLoaded(){return Field().bLoaded;}
 float ShoreDistance(float X,float Y)
 {
  const FIslandField& F=Field();if(!F.bLoaded)return 1e6f;
  const float FX=(X-F.Origin.X)/F.Cell,FY=(Y-F.Origin.Y)/F.Cell;
  const float CX=FMath::Clamp(FX,0.f,float(F.W-1)),CY=FMath::Clamp(FY,0.f,float(F.H-1));
  const int32 X0=FMath::FloorToInt(CX),Y0=FMath::FloorToInt(CY);const float A=CX-X0,B=CY-Y0;
  const float M=FMath::Lerp(FMath::Lerp(F.At(X0,Y0),F.At(X0+1,Y0),A),FMath::Lerp(F.At(X0,Y0+1),F.At(X0+1,Y0+1),A),B);
  // Past the edge of the field (open sea, far away): add the way still to go.
  const float Outside=FVector2D(FX-CX,FY-CY).Size()*F.Cell;
  return M*100.f+Outside;
 }
 float BayEquivalentY(float Distance){return Field().BayWaterline-Distance;}
 float CoastY(float X,float Y){return BayEquivalentY(FMath::Clamp(ShoreDistance(X,Y),-40000.f,40000.f));}
}

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareIslandFieldTest,"MareAlta.World.IslandField",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareIslandFieldTest::RunTest(const FString&)
{
 if(!TestTrue(TEXT("island_sdf.bin loads"),MareIsland::IsLoaded()))return false;
 // The bay keeps its old straight beach: the waterline near y -29.5 m, the old shore band 25 m out at y -54.5 m,
 // the reef shelf 100 m out (y -130 m); the village, the kiosk and the summit are on land; open sea all round.
 TestTrue(TEXT("bay waterline"),FMath::Abs(MareIsland::ShoreDistance(0,-2950))<500.f);
 TestTrue(TEXT("old shore line 25 m out"),FMath::Abs(MareIsland::ShoreDistance(0,-5450)-2500.f)<300.f);
 TestTrue(TEXT("reef 100 m out"),FMath::Abs(MareIsland::ShoreDistance(0,-13000)-10000.f)<400.f);
 TestTrue(TEXT("kiosk on land"),MareIsland::ShoreDistance(3600,-1500)<0.f);
 TestTrue(TEXT("village on land"),MareIsland::ShoreDistance(4000,2500)<-3000.f);
 TestTrue(TEXT("summit on land"),MareIsland::ShoreDistance(4000,38900)<-10000.f);
 TestTrue(TEXT("sea to the north"),MareIsland::ShoreDistance(0,125000)>0.f);
 TestTrue(TEXT("sea to the west"),MareIsland::ShoreDistance(-60000,30000)>0.f);
 TestTrue(TEXT("sea to the east"),MareIsland::ShoreDistance(65000,30000)>0.f);
 TestTrue(TEXT("far sea keeps growing"),MareIsland::ShoreDistance(0,-900000)>MareIsland::ShoreDistance(0,-100000));
 TestTrue(TEXT("coast y in the bay"),FMath::Abs(MareIsland::CoastY(3600,-5000)+5000.f)<400.f);   // i18n:skip
 {float North=60000.f;while(North<200000.f && MareIsland::ShoreDistance(0,North)<0.f)North+=500.f;   // the north waterline
  TestTrue(TEXT("north shore found"),North<200000.f);   // i18n:skip
  TestTrue(TEXT("10 m off the north shore reads like 10 m off the bay"),FMath::Abs(MareIsland::CoastY(0,North+1000.f)-MareIsland::BayEquivalentY(1000.f))<600.f);}   // i18n:skip
 TestTrue(TEXT("bay-equivalent y"),FMath::IsNearlyEqual(MareIsland::BayEquivalentY(2500.f),-5450.f,1.f));
 return true;
}
#endif
