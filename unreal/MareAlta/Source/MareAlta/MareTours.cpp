// Tours, hands-on: buyers at the pier booth before each departure, tickets sold by the player (or the guide),
// and the tour guided in its departure hour through three stops whose choices make the rating and the tip.
// Without the player or a guide the tour is cancelled and refunded. State "tours" lives in the save.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 TSharedPtr<FJsonObject> Child(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  const TSharedPtr<FJsonObject>* Found=nullptr;if(Parent->TryGetObjectField(Key,Found))return *Found;
  auto Created=MakeShared<FJsonObject>();Parent->SetObjectField(Key,Created);return Created;
 }
}

TSharedPtr<FJsonObject> UMareSimulation::ToursDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/tours.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

TSharedPtr<FJsonObject> UMareSimulation::Tours()
{
 // A new day starts with empty booths.
 auto T=Child(State,TEXT("tours"));const int32 Day=int32(Number(State,TEXT("day"),1));
 if(int32(Number(T,TEXT("day")))!=Day){T->Values.Empty();T->SetNumberField(TEXT("day"),Day);}
 return T;
}

TSharedPtr<FJsonObject> UMareSimulation::TourDef(const FString& Id) const
{
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Object(CustomDefs(),TEXT("operations"))->TryGetArrayField(TEXT("tours"),List))
  for(const auto& V:*List)if(String(V->AsObject(),TEXT("id"))==Id)return V->AsObject();
 return nullptr;
}

TArray<FString> UMareSimulation::TourIds() const
{
 TArray<FString> Ids;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Object(CustomDefs(),TEXT("operations"))->TryGetArrayField(TEXT("tours"),List))for(const auto& V:*List)Ids.Add(String(V->AsObject(),TEXT("id")));
 return Ids;
}

int32 UMareSimulation::TourCount(const FString& Field,const FString& Id) const
{
 const auto T=Object(State,TEXT("tours"));if(int32(Number(T,TEXT("day")))!=int32(Number(State,TEXT("day"),1)))return 0;
 return int32(Number(Object(T,Field),Id));
}

FString UMareSimulation::TourStatus(const FString& Id) const
{
 const auto T=Object(State,TEXT("tours"));if(int32(Number(T,TEXT("day")))!=int32(Number(State,TEXT("day"),1)))return FString();
 return String(Object(T,TEXT("done")),Id);
}

bool UMareSimulation::IsTourBoarding(const FString& Id) const
{
 const auto Tour=TourDef(Id);if(!Tour || !TourStatus(Id).IsEmpty())return false;
 const double Hour=Number(State,TEXT("minutes"))/60;return Hour>=Number(Tour,TEXT("hour")) && Hour<Number(Tour,TEXT("hour"))+1;
}

double UMareSimulation::TicketPrice(const FString& Id) const
{
 const auto Tour=TourDef(Id);return Tour?FMath::RoundToDouble(Number(Tour,TEXT("price"))*PlaceIncomeFactor(TEXT("passeios"))):0;
}

static void AddToday(const TSharedPtr<FJsonObject>& State,double Amount)
{
 auto Today=Child(Child(State,TEXT("ue_ops")),TEXT("today"));Today->SetNumberField(TEXT("passeios"),UMareSimulation::Number(Today,TEXT("passeios"))+Amount);
}

int32 UMareSimulation::SellTickets(const FString& Id)
{
 const auto Tour=TourDef(Id);if(!Tour || !TourStatus(Id).IsEmpty()){Fail(TEXT("Esse passeio já saiu hoje."));return 0;}
 auto T=Tours();auto Queue=Child(T,TEXT("queue"));auto Sold=Child(T,TEXT("sold"));
 const int32 Free=TourSeats(Tour)-int32(Number(Sold,Id));const int32 N=FMath::Min(int32(Number(Queue,Id)),Free);
 if(N<=0){Fail(Free<=0?TEXT("Passeio lotado."):TEXT("Ninguém na fila deste passeio."));return 0;}
 Queue->SetNumberField(Id,Number(Queue,Id)-N);Sold->SetNumberField(Id,Number(Sold,Id)+N);
 const double Paid=N*TicketPrice(Id);Book(Paid,FString::Printf(TEXT("%s: %d bilhete(s)"),*String(Tour,TEXT("name")),N));AddToday(State,Paid);
 LastMessage=FString::Printf(TEXT("%d bilhete(s) vendido(s) para %s: R$ %.0f."),N,*String(Tour,TEXT("name")),Paid);Save();return N;
}

static void RateTour(UMareSimulation* Sim,double Rating)
{
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(Sim->State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
 Ratings.Add(MakeShared<FJsonValueNumber>(Rating));while(Ratings.Num()>40)Ratings.RemoveAt(0);Sim->State->SetArrayField(TEXT("ratings"),Ratings);
}

double UMareSimulation::GuideTour(const FString& Id,const TArray<int32>& Choices)
{
 const auto Tour=TourDef(Id);
 if(!Tour || !IsTourBoarding(Id)){Fail(TEXT("Só dá para guiar na hora da saída."));return 0;}
 auto T=Tours();const int32 Pax=int32(Number(Object(T,TEXT("sold")),Id));if(Pax<=0){Fail(TEXT("Nenhum bilhete vendido para este passeio."));return 0;}
 int32 Good=0,Ok=0;for(int32 C:Choices){Good+=C==0;Ok+=C==1;}
 const double Rating=FMath::Min(5.,2+Good+.5*Ok);
 const double Tip=FMath::RoundToDouble(Pax*TicketPrice(Id)*.1*Good);const double Cost=Number(Tour,TEXT("cost"));
 Book(Tip-Cost,FString::Printf(TEXT("%s guiado por você (gorjeta R$ %.0f, custo R$ %.0f)"),*String(Tour,TEXT("name")),Tip,Cost));AddToday(State,Tip-Cost);
 Child(T,TEXT("done"))->SetStringField(Id,TEXT("guided"));Child(T,TEXT("rating"))->SetNumberField(Id,Rating);
 RateTour(this,Rating);AddFame(Pax/2+Good*2);
 LastMessage=FString::Printf(TEXT("%s: nota %.1f, gorjeta R$ %.0f."),*String(Tour,TEXT("name")),Rating,Tip);Save();return Rating;
}

void UMareSimulation::ToursHour(int32 Hour)
{
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("passeios"),bOwned);if(!bOwned)return;
 auto T=Tours();auto Queue=Child(T,TEXT("queue"));auto Sold=Child(T,TEXT("sold"));auto Done=Child(T,TEXT("done"));
 const int32 Started=Hour-1;const bool bGuide=HasStaff(String(Object(CustomDefs(),TEXT("operations")),TEXT("tour_guide")));
 for(const FString& Id:TourIds()){const auto Tour=TourDef(Id);if(!String(Done,Id).IsEmpty())continue;
  const int32 Departs=int32(Number(Tour,TEXT("hour")));
  // High tide or a storm keeps the boats in: sea tours are called off for the day (the lighthouse trail still goes).
  if(IsSeaRough() && Id!=TEXT("farol")){if(Number(Sold,Id)>0){const double Refund=Number(Sold,Id)*TicketPrice(Id);Book(-Refund,String(Tour,TEXT("name"))+TEXT(": mar bravo, bilhetes devolvidos"));}
   Queue->SetNumberField(Id,0);Done->SetStringField(Id,TEXT("cancelled"));continue;}
  // Buyers walk up to the booth during the three hours before the departure (sea tours need calm sea).
  if(Started>=Departs-3 && Started<Departs){const int32 Wanted=TourPassengers(Tour);
   const int32 Room=TourSeats(Tour)-int32(Number(Sold,Id))-int32(Number(Queue,Id));
   Queue->SetNumberField(Id,Number(Queue,Id)+FMath::Clamp(FMath::CeilToInt(Wanted/3.)+FMath::RandRange(-1,1),0,FMath::Max(0,Room)));
   if(bGuide && Number(Queue,Id)>0){const FString Before=LastMessage;SellTickets(Id);LastMessage=Before;}}
  // End of the departure hour: whoever was not guided by the player goes with the guide, or is refunded.
  if(Started==Departs){const int32 Pax=int32(Number(Sold,Id));Queue->SetNumberField(Id,0);
   if(Pax<=0){Done->SetStringField(Id,TEXT("empty"));continue;}
   if(bGuide){Book(-Number(Tour,TEXT("cost")),String(Tour,TEXT("name"))+TEXT(": custo da saída"));AddToday(State,-Number(Tour,TEXT("cost")));
    Done->SetStringField(Id,TEXT("guide"));RateTour(this,3.5);AddFame(Pax/2);}
   else{const double Refund=Pax*TicketPrice(Id);Book(-Refund,String(Tour,TEXT("name"))+TEXT(": cancelado, bilhetes devolvidos"));AddToday(State,-Refund);
    Done->SetStringField(Id,TEXT("cancelled"));LastMessage=String(Tour,TEXT("name"))+TEXT(" cancelado: ninguém guiou. Contrate um guia ou vá ao píer na hora.");}}
 }
}
