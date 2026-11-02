// Day events and the party calendar (port of the Godot Economy.DAY_EVENTS / Core.forecast_next / buy_prep):
// tomorrow's event is decided tonight, the phone forecasts it, paid preparations decorate a party or protect the
// stock from a storm. Content/Data/events.json.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TSharedPtr<FJsonObject> UMareSimulation::EventDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/events.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

TSharedPtr<FJsonObject> UMareSimulation::EventDef(const FString& Id) const{return Object(Object(EventDefs(),TEXT("events")),Id);}

FString UMareSimulation::RollEvent(int32 Day) const
{
 // Parties follow the weekly calendar; the carnaval only after the mayor's chapter.
 if(Day>=Number(EventDefs(),TEXT("party_from_day"),8)){const FString Party=String(Object(EventDefs(),TEXT("party_calendar")),FString::FromInt(Day%7));
  if(!Party.IsEmpty() && (Party!=TEXT("carnaval") || IsChapterDone(String(EventDefs(),TEXT("carnaval_chapter")))))return Party;}
 const TArray<TSharedPtr<FJsonValue>>* Odds=nullptr;float Roll=FMath::FRand();
 if(EventDefs()->TryGetArrayField(TEXT("odds"),Odds))for(const auto& V:*Odds){const auto& Pair=V->AsArray();if(Pair.Num()!=2)continue;
  Roll-=Pair[1]->AsNumber();if(Roll<0)return Pair[0]->AsString();}
 return FString();
}

FString UMareSimulation::TodayEvent() const{return String(State,TEXT("day_event"));}
FString UMareSimulation::TomorrowEvent() const{return String(State,TEXT("forecast"));}
bool UMareSimulation::IsPrepActive() const{return int32(Number(State,TEXT("prep_day"),-1))==int32(Number(State,TEXT("day"),1));}
bool UMareSimulation::IsSeaRough() const{bool b=false;EventDef(TodayEvent())->TryGetBoolField(TEXT("rough_sea"),b);return b;}

double UMareSimulation::EventDemand() const
{
 const auto E=EventDef(TodayEvent());if(!E->Values.Num())return 1;
 return IsPrepActive() && E->HasField(TEXT("deco_demand"))?Number(E,TEXT("deco_demand")):Number(E,TEXT("demand"),1);
}

void UMareSimulation::StartDayEvent()
{
 // Today's event is yesterday's forecast; tomorrow gets a new one.
 const int32 Day=int32(Number(State,TEXT("day"),1));
 FString Today=int32(Number(State,TEXT("forecast_day"),-1))==Day?String(State,TEXT("forecast")):RollEvent(Day);
 State->SetStringField(TEXT("day_event"),Today);
 State->SetStringField(TEXT("forecast"),RollEvent(Day+1));State->SetNumberField(TEXT("forecast_day"),Day+1);
 bool bRain=false;EventDef(Today)->TryGetBoolField(TEXT("rain"),bRain);
 State->SetStringField(TEXT("weather"),bRain || FMath::FRand()<Number(EventDefs(),TEXT("rain_odds"),.12)?TEXT("rain"):TEXT("sun"));
 // A storm without preparations ruins part of the supplies left outside.
 if(Today==TEXT("tempestade") && !IsPrepActive()){const double Loss=Number(EventDefs(),TEXT("storm_loss"),.35);auto Stock=Object(State,TEXT("stock"));int32 Lost=0;
  for(auto& Pair:Stock->Values){double N=0;if(!Pair.Value->TryGetNumber(N) || N<=0)continue;const int32 Gone=FMath::FloorToInt(N*Loss);Lost+=Gone;Pair.Value=MakeShared<FJsonValueNumber>(N-Gone);}
  if(Lost)LastMessage=FString::Printf(TEXT("A tempestade estragou %d itens do estoque. Da próxima vez, faça os preparativos."),Lost);}
}

bool UMareSimulation::BuyPrep()
{
 const auto E=EventDef(TomorrowEvent());const FString Kind=String(E,TEXT("prep"));
 if(Kind.IsEmpty())return Fail(TEXT("Amanhã não precisa de preparativos."));
 const int32 Tomorrow=int32(Number(State,TEXT("day"),1))+1;if(int32(Number(State,TEXT("prep_day"),-1))==Tomorrow)return Fail(TEXT("Os preparativos já estão pagos."));
 const double Cost=Number(Object(EventDefs(),TEXT("prep_cost")),Kind);if(Money()<Cost)return Fail(FString::Printf(TEXT("Os preparativos custam R$ %.0f."),Cost));
 Book(-Cost,TEXT("Preparativos: ")+String(E,TEXT("name")));State->SetNumberField(TEXT("prep_day"),Tomorrow);
 LastMessage=Kind==TEXT("storm")?TEXT("Estoque protegido para a tempestade de amanhã."):TEXT("Decoração encomendada para a festa de amanhã!");return Save();
}
