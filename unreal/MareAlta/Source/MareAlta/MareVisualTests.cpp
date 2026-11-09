#include "Misc/AutomationTest.h"
#include "MareGame.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareUnderwaterGradeTest,"MareAlta.Visual.UnderwaterGrade",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareUnderwaterGradeTest::RunTest(const FString& Parameters)
{
 // 06/11 (CHECKLIST 0): the luminance of SceneColorTint goes into the pre-exposure. With the under-water eye at most EV100 10
 // the exposure must stay inside the safe range of r.EyeAdaptation.CachedLightingPreExposure 4 ([-8, 12]): the tint keeps a
 // luminance near 0.8 at every depth (the old deep tint of 0.013 meant EV ~15 and Lumen's cached light clipped on the floor).
 float LastGain=2.f;
 for(float Z=-40.f;Z>=-10000.f;Z-=40.f){FLinearColor Tint;float Gain=1.f;MareUnderwaterGrade(Z,Tint,Gain);
  // 09/11: the cap rises to 15 in the shallows (MareUnderwaterMaxEV); r.EyeAdaptation.CachedLightingPreExposure is 8 now,
  // so the safe range is [-4, 16].
  const float ExposureEV=MareUnderwaterMaxEV(Z)-1.f-FMath::Log2(Tint.GetLuminance());
  if(!TestTrue(FString::Printf(TEXT("Exposure EV %.1f inside [-4, 16] at z %.0f"),ExposureEV,Z),ExposureEV<=16.f))break;
  if(!TestTrue(FString::Printf(TEXT("Darker or equal going down at z %.0f"),Z),Gain<=LastGain+1e-4f))break;
  LastGain=Gain;}
 // Still nearly black on the -100 m floor and untouched just under the surface (Sergio, 05/11: "como no oceano de verdade").
 FLinearColor Tint;float Gain=1.f;
 MareUnderwaterGrade(-9800.f,Tint,Gain);TestTrue(TEXT("Deep floor nearly black (gain < 0.03)"),Gain<.03f);
 MareUnderwaterGrade(-60.f,Tint,Gain);TestTrue(TEXT("Surface water at full light"),Gain>.98f);
 // The sunlit sand bank 3 m down averages EV100 ~15.5 at noon: the cap there may not hold it 5 stops over (white sand).
 TestTrue(TEXT("Shallow cap lets the eye follow the sun"),MareUnderwaterMaxEV(-280.f)>=14.5f);
 TestTrue(TEXT("Deep cap keeps the floor dark"),MareUnderwaterMaxEV(-9800.f)<=10.f);
 return true;
}
