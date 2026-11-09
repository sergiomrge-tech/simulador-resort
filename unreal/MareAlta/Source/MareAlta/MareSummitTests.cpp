#include "Misc/AutomationTest.h"
#include "MareSummitWorld.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareSummitRulesTest,"MareAlta.Gameplay.SummitOffering",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareSummitRulesTest::RunTest(const FString& Parameters)
{
 // Before meeting Seu Tibúrcio nothing is owed; afterwards one offering per game day.
 TestTrue(TEXT("Not met: nothing owed"),UMareSummitWorld::OfferingDone(false,0,7));
 TestTrue(TEXT("Met, offered today"),UMareSummitWorld::OfferingDone(true,5,5));
 TestFalse(TEXT("Met, offered yesterday"),UMareSummitWorld::OfferingDone(true,4,5));
 // Phases of a forgotten day (08/11, by day): calm, reminders from 12h, omen from 14h, the wave at 16h.
 TestEqual(TEXT("Morning calm"),UMareSummitWorld::PhaseAt(9*60),0);
 TestEqual(TEXT("12h reminder"),UMareSummitWorld::PhaseAt(12*60),1);
 TestEqual(TEXT("13h59 still reminder"),UMareSummitWorld::PhaseAt(14*60-1),1);
 TestEqual(TEXT("14h omen"),UMareSummitWorld::PhaseAt(14*60),2);
 TestEqual(TEXT("16h wave"),UMareSummitWorld::PhaseAt(16*60),3);
 return true;
}
