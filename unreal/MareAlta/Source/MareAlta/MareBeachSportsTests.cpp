#include "Misc/AutomationTest.h"
#include "MareBeachSports.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareBeachSportsDayTest,"MareAlta.Gameplay.BeachSportsDay",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareBeachSportsDayTest::RunTest(const FString& Parameters)
{
 using ESport=UMareBeachSportsWorld::ESport;
 int32 Count[4]={0,0,0,0};bool bRepeat=false,bStable=true;
 for(int32 Day=1;Day<=60;++Day){const ESport S=UMareBeachSportsWorld::SportOfDay(Day);
  ++Count[int32(S)];
  bStable&=S==UMareBeachSportsWorld::SportOfDay(Day);
  if(Day>1 && S==UMareBeachSportsWorld::SportOfDay(Day-1))bRepeat=true;}
 TestEqual(TEXT("Every day has a sport"),Count[0],0);   // i18n:skip
 TestFalse(TEXT("Never the same sport two days running"),bRepeat);   // i18n:skip
 TestTrue(TEXT("The same day always gives the same sport"),bStable);   // i18n:skip
 for(int32 S=1;S<=3;++S)TestTrue(FString::Printf(TEXT("Sport %d shows up often in 60 days"),S),Count[S]>=12);   // i18n:skip
 return true;
}
#endif
