#include "Misc/AutomationTest.h"
#include "MareComicEvents.h"
#include "MareSimulation.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareComicEventsTest,"MareAlta.Gameplay.ComicEvents",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareComicEventsTest::RunTest(const FString& Parameters)
{
 // Data: every event has lines, replies matching reactions, the same counts in English, sane hours and odds.
 FString Text;TSharedPtr<FJsonObject> Defs;
 TestTrue(TEXT("comic_events.json loads"),FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/comic_events.json"))) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs));
 if(!Defs.IsValid())return false;
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;TestTrue(TEXT("Has events"),Defs->TryGetArrayField(TEXT("events"),List) && List->Num()>0);
 TSet<FString> Ids;
 if(List)for(const auto& V:*List){auto E=V->AsObject();const FString Id=UMareSimulation::String(E,TEXT("id"));
  TestTrue(TEXT("Stable HUM id: ")+Id,Id.StartsWith(TEXT("HUM-")) && !Ids.Contains(Id));Ids.Add(Id);
  auto Count=[&](const TCHAR* F){const TArray<TSharedPtr<FJsonValue>>* L=nullptr;return E->TryGetArrayField(F,L)?L->Num():0;};
  TestTrue(Id+TEXT(" has lines"),Count(TEXT("asks"))>0);
  TestTrue(Id+TEXT(" replies match reactions"),Count(TEXT("replies"))>0 && Count(TEXT("replies"))==Count(TEXT("reactions")));
  TestEqual(Id+TEXT(" English lines"),Count(TEXT("asks_en")),Count(TEXT("asks")));
  TestEqual(Id+TEXT(" English replies"),Count(TEXT("replies_en")),Count(TEXT("replies")));
  TestEqual(Id+TEXT(" English reactions"),Count(TEXT("reactions_en")),Count(TEXT("reactions")));
  const double Odds=UMareSimulation::Number(E,TEXT("odds"));TestTrue(Id+TEXT(" odds in (0,1]"),Odds>0 && Odds<=1);
  TestTrue(Id+TEXT(" cooldown"),UMareSimulation::Number(E,TEXT("cooldown_minutes"))>=60);}
 TestTrue(TEXT("Lost tourist is in"),Ids.Contains(TEXT("HUM-005")));

 // Rules: own cooldown and the global gap, both in absolute game minutes.
 auto Comic=MakeShared<FJsonObject>();
 TestTrue(TEXT("Fresh save: due"),UMareComicEvents::IsDue(Comic,TEXT("HUM-005"),2000,360,90));
 UMareComicEvents::MarkStarted(Comic,TEXT("HUM-005"),2000);
 TestFalse(TEXT("Global gap blocks any event"),UMareComicEvents::IsDue(Comic,TEXT("HUM-007"),2050,600,90));
 TestTrue(TEXT("Other event due after the gap"),UMareComicEvents::IsDue(Comic,TEXT("HUM-007"),2091,600,90));
 TestFalse(TEXT("Own cooldown still blocks"),UMareComicEvents::IsDue(Comic,TEXT("HUM-005"),2200,360,90));
 TestTrue(TEXT("Own cooldown over"),UMareComicEvents::IsDue(Comic,TEXT("HUM-005"),2360,360,90));
 TestTrue(TEXT("Next day counts"),UMareComicEvents::IsDue(Comic,TEXT("HUM-005"),2000+1440,360,90));

 // Lines: sequences advance with the count of talks and stop at the punchline; others follow the roll.
 TestEqual(TEXT("Sequence starts at the first story"),UMareComicEvents::LineIndex(Comic,TEXT("HUM-008"),5,true,777),0);
 UMareSimulation::Object(Comic,TEXT("count"))->SetNumberField(TEXT("HUM-008"),3);
 TestEqual(TEXT("Fourth talk, fourth story"),UMareComicEvents::LineIndex(Comic,TEXT("HUM-008"),5,true,777),3);
 UMareSimulation::Object(Comic,TEXT("count"))->SetNumberField(TEXT("HUM-008"),12);
 TestEqual(TEXT("Stays at the punchline"),UMareComicEvents::LineIndex(Comic,TEXT("HUM-008"),5,true,0),4);
 TestEqual(TEXT("Random line from the roll"),UMareComicEvents::LineIndex(Comic,TEXT("HUM-005"),3,false,7),1);
 return true;
}
