#include "MareSimulation.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareHotelEventsTest,"MareAlta.Gameplay.HotelEvents",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareHotelEventsTest::RunTest(const FString& Parameters)
{
 // CHECKLIST 5.2: offer on the phone, booked for the next day, set-up window, pay by what was set, flop below half.
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/HotelEvents")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Result){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Result);};
 auto Done=[&](){Sim->RemoveFromRoot();Instance->RemoveFromRoot();};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Default save"),Load(TEXT("default_save.json"),Sim->State))){Done();return false;}
 // Every model of every kind exists and the chairs are where guests can sit.
 {TSharedPtr<FJsonObject> Assets;Load(TEXT("custom_assets.json"),Assets);
  for(const auto& Pair:UMareSimulation::Object(Sim->HotelEventDefs(),TEXT("kinds"))->Values){const auto K=Pair.Value->AsObject();const FString Kind(Pair.Key.ToView());
   TestTrue(Kind+TEXT(" has pieces"),K->HasTypedField<EJson::Array>(TEXT("pieces")));TestTrue(Kind+TEXT(" fee"),UMareSimulation::Number(K,TEXT("fee"))>0);
   int32 Chairs=0;for(const TCHAR* L:{TEXT("pieces"),TEXT("extras")}){const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(!K->TryGetArrayField(L,List))continue;
    for(const auto& V:*List){const FString Model=UMareSimulation::String(V->AsObject(),TEXT("model"));Chairs+=Model.Contains(TEXT("chair"));
     const FString Path=UMareSimulation::String(Assets,Model);TestFalse(Kind+TEXT(" model in the catalog: ")+Model,Path.IsEmpty());
     if(!Path.IsEmpty())TestNotNull(Kind+TEXT(" mesh loads: ")+Model,LoadObject<UStaticMesh>(nullptr,*Path));}}
   TestTrue(Kind+TEXT(" seats every guest"),Chairs>=UMareSimulation::Number(K,TEXT("guests"),8));}}
 // No hotel, no offer.
 Sim->State->SetNumberField(TEXT("day"),2);Sim->HotelEventsHour(9);
 TestFalse(TEXT("No offer without the hotel"),UMareSimulation::Object(Sim->State,TEXT("hotel_events"))->HasField(TEXT("offer")));
 Sim->Object(Sim->State,TEXT("unlocked"))->SetBoolField(TEXT("grand_hotel"),true);Sim->State->SetNumberField(TEXT("money"),1000);
 Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),300);
 Sim->HotelEventsHour(9);TestTrue(TEXT("Offer at 9h on an even day"),Sim->HotelEventState()->HasField(TEXT("offer")));
 Sim->HotelEventState()->RemoveField(TEXT("offer"));
 // The wedding: booked for tomorrow, nothing to set today.
 TestEqual(TEXT("Forced offer"),Sim->OfferHotelEvent(TEXT("casamento")),FString(TEXT("casamento")));
 TestEqual(TEXT("One offer at a time"),Sim->OfferHotelEvent(TEXT("congresso")),FString());
 TestTrue(TEXT("Accept"),Sim->AcceptHotelEvent());const auto B=Sim->BookedHotelEvent();
 if(!TestTrue(TEXT("Booked"),B.IsValid())){Done();return false;}
 TestEqual(TEXT("Next day"),int32(UMareSimulation::Number(B,TEXT("day"))),3);
 const int32 Pieces=Sim->HotelEventCount(false,false);TestEqual(TEXT("14 wedding pieces"),Pieces,14);TestEqual(TEXT("4 extras"),Sim->HotelEventCount(true,false),4);
 Sim->State->SetNumberField(TEXT("minutes"),10*60);TestFalse(TEXT("No set-up the day before"),Sim->PlaceHotelEventPiece(false,0));
 // Event day, 7h: set-up open; a piece is set once; at 17h it starts and pays by what was set.
 Sim->State->SetNumberField(TEXT("day"),3);Sim->State->SetNumberField(TEXT("minutes"),7*60);Sim->HotelEventsHour(7);
 TestTrue(TEXT("Set-up open"),Sim->HotelEventSetupOpen());
 TestTrue(TEXT("Set the arch"),Sim->PlaceHotelEventPiece(false,0));TestFalse(TEXT("Not twice"),Sim->PlaceHotelEventPiece(false,0));
 TestFalse(TEXT("Index outside"),Sim->PlaceHotelEventPiece(false,99));
 for(int32 I=1;I<Pieces;++I)Sim->PlaceHotelEventPiece(false,I);Sim->PlaceHotelEventPiece(true,0);Sim->PlaceHotelEventPiece(true,1);
 TestEqual(TEXT("All pieces set"),Sim->HotelEventCount(false,true),Pieces);
 const double Before=Sim->Money();const double Xp=UMareSimulation::Number(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));
 Sim->State->SetNumberField(TEXT("minutes"),17*60);Sim->HotelEventsHour(17);
 TestEqual(TEXT("Show"),UMareSimulation::String(Sim->BookedHotelEvent(),TEXT("state")),FString(TEXT("show")));
 TestFalse(TEXT("No set-up during the show"),Sim->HotelEventSetupOpen());
 TestEqual(TEXT("Fee with two extras"),Sim->Money()-Before,4800.);
 TestTrue(TEXT("Fame earned"),UMareSimulation::Number(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))>Xp);
 Sim->HotelEventsHour(19);TestFalse(TEXT("Cleared after the show"),Sim->BookedHotelEvent().IsValid());
 TestTrue(TEXT("Kept as last"),Sim->HotelEventState()->HasField(TEXT("last")));
 TestEqual(TEXT("Counted"),int32(UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("hotel_events")),TEXT("done"))),1);
 // A congress with 3 of 14 pieces is a flop: only the deposit, fame lost (but not below the level reached).
 Sim->OfferHotelEvent(TEXT("congresso"));Sim->AcceptHotelEvent();Sim->State->SetNumberField(TEXT("day"),4);Sim->State->SetNumberField(TEXT("minutes"),7*60);
 for(int32 I=0;I<3;++I)Sim->PlaceHotelEventPiece(false,I);
 {const double M=Sim->Money();const int32 Level=Sim->FameLevel();Sim->Object(Sim->State,TEXT("prog"))->SetNumberField(TEXT("fame_xp"),460);
  const double X=UMareSimulation::Number(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("fame_xp"));
  Sim->State->SetNumberField(TEXT("minutes"),10*60);Sim->HotelEventsHour(10);
  TestEqual(TEXT("Only the deposit"),Sim->Money()-M,500.);
  TestTrue(TEXT("Fame lost"),UMareSimulation::Number(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("fame_xp"))<X);
  TestTrue(TEXT("Level kept"),Sim->FameLevel()>=4);(void)Level;}
 // An offer not taken is gone the next day; declining clears it.
 Sim->HotelEventsHour(12);TestFalse(TEXT("Congress over"),Sim->BookedHotelEvent().IsValid());
 Sim->OfferHotelEvent(TEXT("aniversario"));Sim->State->SetNumberField(TEXT("day"),5);Sim->HotelEventsHour(8);
 TestFalse(TEXT("Old offer expired"),Sim->HotelEventState()->HasField(TEXT("offer")));
 Sim->OfferHotelEvent(TEXT("aniversario"));TestTrue(TEXT("Decline"),Sim->DeclineHotelEvent());TestFalse(TEXT("Declined"),Sim->HotelEventState()->HasField(TEXT("offer")));
 // A booked event the player never sets up (slept through) is a flop too.
 Sim->OfferHotelEvent(TEXT("aniversario"));Sim->AcceptHotelEvent();Sim->State->SetNumberField(TEXT("day"),7);Sim->HotelEventsHour(8);
 {const auto Last=UMareSimulation::Object(Sim->HotelEventState(),TEXT("last"));
  TestEqual(TEXT("Missed day ran"),UMareSimulation::String(Last,TEXT("kind")),FString(TEXT("aniversario")));
  TestEqual(TEXT("Missed: score 0"),UMareSimulation::Number(Last,TEXT("score"),-1),0.);}
 Done();return true;
}
#endif
