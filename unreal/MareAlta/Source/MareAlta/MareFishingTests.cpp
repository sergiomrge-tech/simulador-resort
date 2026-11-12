// Fase 3 (11/11): fishing with bait, the fight with the fish, the species book and the photo challenges.
#include "MareSimulation.h"
#include "MareFishing.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 /** A fight played by a rule: 0 = sensible angler (gives line while the fish pulls or the line is tight, reels otherwise),
  *  1 = holds the whole time, 2 = never reels. Fixed pull pattern (Rand01 = .5). */
 int32 PlayFight(float Strength,int32 Style,float* Seconds=nullptr)
 {
  FMareFishFight F;F.Strength=Strength;float T=0;
  while(F.Result==0 && T<180.f){
   const bool bReel=Style==1?true:Style==2?false:(!F.IsPulling() && F.Tension<.8f) || F.Tension<.12f;
   F.Step(1.f/60.f,bReel,.5f);T+=1.f/60.f;}
  if(Seconds)*Seconds=T;return F.Result;
 }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareFishingFightTest,"MareAlta.Gameplay.FishingFight",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareFishingFightTest::RunTest(const FString& Parameters)
{
 // The sensible angler lands every fish, the big ones take longer; nobody wins by holding the button on a strong
 // fish, and nobody lands anything without reeling.
 float Small=0,Big=0;
 TestEqual(TEXT("Sardine landed"),PlayFight(.1f,0,&Small),1);
 TestEqual(TEXT("Snook landed"),PlayFight(.6f,0),1);
 TestEqual(TEXT("Grouper landed"),PlayFight(1.f,0,&Big),1);
 TestTrue(TEXT("A big fish takes longer"),Big>Small*1.5f);
 TestTrue(TEXT("A sardine comes in within 8 s"),Small<8.f);
 TestTrue(TEXT("The grouper comes in within 60 s"),Big<60.f);
 TestEqual(TEXT("Holding on a strong fish snaps the line"),PlayFight(.7f,1),-1);
 TestEqual(TEXT("Holding on a grouper snaps the line"),PlayFight(1.f,1),-1);
 TestEqual(TEXT("Never reeling loses the fish"),PlayFight(.3f,2),-2);
 return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareFishingBookTest,"MareAlta.Gameplay.FishingBook",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareFishingBookTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/FishingBook")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 auto Count=[&](const FString& Bait,double Minutes,const FString& Species,int32 Casts){Sim->State->SetNumberField(TEXT("minutes"),Minutes);
  Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("bait"))->SetNumberField(Bait,Casts+1);int32 N=0;   // i18n:skip
  for(int32 I=0;I<Casts;++I){bool bOk=false;const auto F=Sim->HookFish(Bait,bOk);if(bOk && F.IsValid() && Sim->String(F,TEXT("id"))==Species)++N;}return N;};
 // Bait: bread dough is free and endless; the paid baits come in packs and are used up one per cast.
 TestTrue(TEXT("Dough is endless"),Sim->BaitCount(TEXT("massa"))>1000);TestEqual(TEXT("No squid at the start"),Sim->BaitCount(TEXT("lula")),0);   // i18n:skip
 bool bOk=true;Sim->HookFish(TEXT("lula"),bOk);TestFalse(TEXT("No cast without the bait"),bOk);
 Sim->State->SetNumberField(TEXT("money"),10);TestFalse(TEXT("Bait refused without money"),Sim->BuyBait(TEXT("lula")));
 Sim->State->SetNumberField(TEXT("money"),500);TestTrue(TEXT("Squid bought"),Sim->BuyBait(TEXT("lula")));
 TestEqual(TEXT("A pack of five"),Sim->BaitCount(TEXT("lula")),5);TestEqual(TEXT("Paid"),Sim->Money(),455.);
 Sim->HookFish(TEXT("lula"),bOk);TestTrue(TEXT("Cast with squid"),bOk);TestEqual(TEXT("One bait used"),Sim->BaitCount(TEXT("lula")),4);
 // Species follow the bait and the hour: squid brings the grouper far more often than dough; the cutlassfish only bites at night.
 const int32 GrouperSquid=Count(TEXT("lula"),600,TEXT("garoupa"),600),GrouperDough=Count(TEXT("massa"),600,TEXT("garoupa"),600);   // i18n:skip
 TestTrue(TEXT("Squid brings the grouper"),GrouperSquid>GrouperDough*3 && GrouperSquid>30);
 TestEqual(TEXT("No cutlassfish by day"),Count(TEXT("lula"),600,TEXT("peixe_espada"),400),0);
 TestTrue(TEXT("Cutlassfish at night"),Count(TEXT("lula"),1260,TEXT("peixe_espada"),400)>40);
 TestEqual(TEXT("No jack in the morning"),Count(TEXT("lula"),600,TEXT("xareu"),400),0);
 TestTrue(TEXT("Jack late in the afternoon"),Count(TEXT("lula"),990,TEXT("xareu"),400)>20);
 // The book: a first catch is new and pays more fame; a bigger one is a record; the last species pays the prize.
 Sim->Object(Sim->State,TEXT("prog"))->SetObjectField(TEXT("fish"),MakeShared<FJsonObject>());
 const TArray<TSharedPtr<FJsonValue>>* Species=nullptr;Sim->LeisureDefs()->TryGetArrayField(TEXT("species"),Species);
 if(!TestTrue(TEXT("Eight species"),Species && Species->Num()==8)){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 TestEqual(TEXT("Empty book"),Sim->SpeciesCaught(),0);
 const double Money=Sim->Money();
 for(int32 I=0;I<Species->Num();++I){auto F=MakeShared<FJsonObject>();F->SetStringField(TEXT("id"),Sim->String((*Species)[I]->AsObject(),TEXT("id")));
  F->SetStringField(TEXT("name"),Sim->String((*Species)[I]->AsObject(),TEXT("name")));F->SetNumberField(TEXT("cm"),30);
  TestTrue(TEXT("New species"),Sim->LandFish(F));
  if(I==0){F->SetNumberField(TEXT("cm"),44);TestFalse(TEXT("Not new the second time"),Sim->LandFish(F));TestTrue(TEXT("Record noted"),Sim->LastMessage.Contains(TEXT("recorde")));}
  if(I<Species->Num()-1)TestEqual(TEXT("No prize before the last"),Sim->Money(),Money);}
 TestEqual(TEXT("Full book"),Sim->SpeciesCaught(),8);TestEqual(TEXT("Book prize"),Sim->Money(),Money+Sim->Number(Sim->LeisureDefs(),TEXT("book_reward")));
 TestEqual(TEXT("Record size kept"),Sim->Number(Sim->Object(Sim->Object(Sim->State,TEXT("prog")),TEXT("fish")),TEXT("best_sardinha")),44.);
 // Photo challenges: one photo with all the subjects, once.
 const double Before=Sim->Money();
 Sim->RecordPhoto({TEXT("farol")},TEXT("a.png"));TestFalse(TEXT("One subject is not the postcard"),Sim->PhotoChallengeDone(TEXT("cartao_postal")));
 Sim->RecordPhoto({TEXT("farol"),TEXT("pier")},TEXT("b.png"));TestTrue(TEXT("Postcard challenge"),Sim->PhotoChallengeDone(TEXT("cartao_postal")));
 TestEqual(TEXT("Challenge paid"),Sim->Money(),Before+60.);
 Sim->RecordPhoto({TEXT("farol"),TEXT("pier")},TEXT("c.png"));TestEqual(TEXT("Paid once"),Sim->Money(),Before+60.);
 Sim->RecordPhoto({TEXT("farol"),TEXT("pier"),TEXT("quiosque")},TEXT("d.png"));TestTrue(TEXT("Panorama with three subjects"),Sim->PhotoChallengeDone(TEXT("panorama")));   // i18n:skip
 TestFalse(TEXT("Sunset not done"),Sim->PhotoChallengeDone(TEXT("fim_de_tarde")));
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();
 return true;
}
#endif
