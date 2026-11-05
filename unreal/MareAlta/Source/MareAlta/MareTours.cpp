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

static TArray<TSharedPtr<FJsonValue>>& ListOf(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
{
 if(!Parent->HasTypedField<EJson::Array>(Key))Parent->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
 return const_cast<TArray<TSharedPtr<FJsonValue>>&>(Parent->GetArrayField(Key));
}

static const TCHAR* TourNames[]={TEXT("Família Souza"),TEXT("Casal Lima"),TEXT("Turma da Bia"),TEXT("Família Oliveira"),TEXT("Dona Marta e netos"),
 TEXT("Casal Ribeiro"),TEXT("Galera de Recife"),TEXT("Família Costa"),TEXT("Seu Jair e filhos"),TEXT("Amigas de BH"),TEXT("Família Nunes"),TEXT("Casal Teixeira")};

TArray<TSharedPtr<FJsonObject>> UMareSimulation::TourGroups(const FString& Id) const
{
 TArray<TSharedPtr<FJsonObject>> Out;const auto T=Object(State,TEXT("tours"));if(int32(Number(T,TEXT("day")))!=int32(Number(State,TEXT("day"),1)))return Out;
 // Gone, cancelled or waiting for the storm decision: nobody stays in line for it.
 if(!String(Object(T,TEXT("done")),Id).IsEmpty())return Out;
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(Object(T,TEXT("groups"))->TryGetArrayField(Id,List))for(const auto& V:*List)Out.Add(V->AsObject());
 return Out;
}

FString UMareSimulation::TourGroupLine(const TSharedPtr<FJsonObject>& G) const
{
 const int32 A=int32(Number(G,TEXT("adults"),1)),K=int32(Number(G,TEXT("kids")));
 FString Line=FString::Printf(TEXT("%d %s"),A,A==1?TEXT("adulto"):TEXT("adultos"));
 if(K)Line+=FString::Printf(TEXT(" e %d %s"),K,K==1?TEXT("criança"):TEXT("crianças"));
 const FString Trait=String(Object(ToursDefs(),TEXT("traits")),String(G,TEXT("trait")));if(!Trait.IsEmpty())Line+=TEXT(" · ")+Trait;
 return Line;
}

void UMareSimulation::AddTourGroup(const FString& Id,int32 Adults,int32 Kids,const FString& Trait)
{
 auto T=Tours();auto Groups=Child(T,TEXT("groups"));auto& List=ListOf(Groups,Id);const int32 Next=int32(Number(T,TEXT("next_group")));
 auto G=MakeShared<FJsonObject>();G->SetStringField(TEXT("id"),FString::Printf(TEXT("g%d"),Next));T->SetNumberField(TEXT("next_group"),Next+1);
 G->SetStringField(TEXT("name"),TourNames[(Next*5+int32(Number(State,TEXT("day"),1)))%UE_ARRAY_COUNT(TourNames)]);
 G->SetNumberField(TEXT("adults"),FMath::Max(1,Adults));G->SetNumberField(TEXT("kids"),FMath::Max(0,Kids));if(!Trait.IsEmpty())G->SetStringField(TEXT("trait"),Trait);
 List.Add(MakeShared<FJsonValueObject>(G));
 auto Queue=Child(T,TEXT("queue"));Queue->SetNumberField(Id,Number(Queue,Id)+FMath::Max(1,Adults)+FMath::Max(0,Kids));
}

int32 UMareSimulation::TourWaitlist(const FString& Id) const
{
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;return Object(Object(State,TEXT("tour_wait")),TEXT("groups"))->TryGetArrayField(Id,List)?List->Num():0;
}

bool UMareSimulation::IsTourStormPending(const FString& Id) const{return TourStatus(Id)==TEXT("storm");}

static void AddToday(const TSharedPtr<FJsonObject>& State,double Amount)
{
 auto Today=Child(Child(State,TEXT("ue_ops")),TEXT("today"));Today->SetNumberField(TEXT("passeios"),UMareSimulation::Number(Today,TEXT("passeios"))+Amount);
}

int32 UMareSimulation::SellTickets(const FString& Id)
{
 // With groups in line (2.1) the guide sells group by group, without offering extras.
 if(TourGroups(Id).Num()){int32 Total=0;FString Msg;while(TourGroups(Id).Num()){const int32 N=SellTourGroup(Id,{});if(N<=0 && TourGroups(Id).IsEmpty())break;Total+=N;Msg=LastMessage;}
  LastMessage=Msg;return Total;}
 const auto Tour=TourDef(Id);if(!Tour || !TourStatus(Id).IsEmpty()){Fail(TEXT("Esse passeio já saiu hoje."));return 0;}
 auto T=Tours();auto Queue=Child(T,TEXT("queue"));auto Sold=Child(T,TEXT("sold"));
 const int32 Free=TourSeats(Tour)-int32(Number(Sold,Id));const int32 N=FMath::Min(int32(Number(Queue,Id)),Free);
 if(N<=0){Fail(Free<=0?TEXT("Passeio lotado."):TEXT("Ninguém na fila deste passeio."));return 0;}
 Queue->SetNumberField(Id,Number(Queue,Id)-N);Sold->SetNumberField(Id,Number(Sold,Id)+N);
 const double Paid=N*TicketPrice(Id);Book(Paid,FString::Printf(TEXT("%s: %d bilhete(s)"),*String(Tour,TEXT("name")),N));AddToday(State,Paid);
 LastMessage=FString::Printf(TEXT("%d bilhete(s) vendido(s) para %s: R$ %.0f."),N,*String(Tour,TEXT("name")),Paid);Save();return N;
}

int32 UMareSimulation::SellTourGroup(const FString& Id,const TArray<FString>& Extras)
{
 const auto Tour=TourDef(Id);if(!Tour || !TourStatus(Id).IsEmpty()){Fail(TEXT("Esse passeio já saiu hoje."));return 0;}
 auto T=Tours();auto& List=ListOf(Child(T,TEXT("groups")),Id);if(List.IsEmpty()){Fail(TEXT("Ninguém na fila deste passeio."));return 0;}
 const auto G=List[0]->AsObject();List.RemoveAt(0);
 const int32 A=int32(Number(G,TEXT("adults"),1)),K=int32(Number(G,TEXT("kids"))),N=A+K;
 auto Queue=Child(T,TEXT("queue"));Queue->SetNumberField(Id,FMath::Max(0.,Number(Queue,Id)-N));
 auto Sold=Child(T,TEXT("sold"));const FString Name=String(G,TEXT("name"));
 // Does not fit: the waiting list, first in line tomorrow.
 if(Number(Sold,Id)+N>TourSeats(Tour)){auto& Wait=ListOf(Child(Child(State,TEXT("tour_wait")),TEXT("groups")),Id);Wait.Add(MakeShared<FJsonValueObject>(G));
  LastMessage=FString::Printf(TEXT("%s: %s lotado. Ficaram na lista de espera para amanhã."),*Name,*String(Tour,TEXT("name")));Save();return 0;}
 Sold->SetNumberField(Id,Number(Sold,Id)+N);
 double Paid=N*TicketPrice(Id),ExtraRating=0;TArray<FString> Bought,Refused;
 const FString Trait=String(G,TEXT("trait"));
 for(const FString& E:Extras){const auto X=Object(Object(ToursDefs(),TEXT("extras")),E);if(!X->Values.Num())continue;
  const FString By=String(X,TEXT("wanted_by"));const bool bWanted=(By==TEXT("kids") && K>0) || By==Trait;
  if(bWanted){Paid+=Number(X,TEXT("price"))*(String(X,TEXT("per"))==TEXT("person")?N:1);ExtraRating+=Number(X,TEXT("rating"));Bought.Add(String(X,TEXT("name")).ToLower());}
  else{ExtraRating-=Number(ToursDefs(),TEXT("pushy_rating"),.15);Refused.Add(String(X,TEXT("name")).ToLower());}}
 auto Ex=Child(T,TEXT("extra_rating"));Ex->SetNumberField(Id,Number(Ex,Id)+ExtraRating);
 auto Gs=Child(T,TEXT("groups_sold"));Gs->SetNumberField(Id,Number(Gs,Id)+1);
 Book(Paid,FString::Printf(TEXT("%s: %d bilhete(s)"),*String(Tour,TEXT("name")),N));AddToday(State,Paid);
 LastMessage=FString::Printf(TEXT("%s: %d bilhete(s), R$ %.0f."),*Name,N,Paid);
 if(Bought.Num())LastMessage+=TEXT(" Levaram ")+FString::Join(Bought,TEXT(", "))+TEXT(".");
 if(Refused.Num())LastMessage+=TEXT(" Recusaram ")+FString::Join(Refused,TEXT(", "))+TEXT(" (insistiu demais).");
 Save();return N;
}

bool UMareSimulation::RefundTour(const FString& Id)
{
 if(!IsTourStormPending(Id))return Fail(TEXT("Não há passeio para devolver."));
 auto T=Tours();const auto Tour=TourDef(Id);const double Refund=Number(Object(T,TEXT("sold")),Id)*TicketPrice(Id);
 Book(-Refund,String(Tour,TEXT("name"))+TEXT(": mar bravo, bilhetes devolvidos"));AddToday(State,-Refund);
 Child(T,TEXT("done"))->SetStringField(Id,TEXT("cancelled"));
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Old=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Old))Ratings=*Old;
 Ratings.Add(MakeShared<FJsonValueNumber>(Number(ToursDefs(),TEXT("refund_rating"),3)));while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);
 LastMessage=FString::Printf(TEXT("%s: dinheiro devolvido (R$ %.0f)."),*String(Tour,TEXT("name")),Refund);return Save();
}

bool UMareSimulation::RescheduleTour(const FString& Id)
{
 if(!IsTourStormPending(Id))return Fail(TEXT("Não há passeio para remarcar."));
 auto T=Tours();const auto Tour=TourDef(Id);const int32 Pax=int32(Number(Object(T,TEXT("sold")),Id));
 // Most groups keep the date for tomorrow (first in line, already paid); the rest take their money back.
 const int32 Keep=FMath::RoundToInt(Pax*Number(ToursDefs(),TEXT("reschedule_keep"),.7));const double Refund=(Pax-Keep)*TicketPrice(Id);
 if(Refund>0){Book(-Refund,String(Tour,TEXT("name"))+TEXT(": remarcado, parte devolvida"));AddToday(State,-Refund);}
 auto Wait=Child(State,TEXT("tour_wait"));auto Paid=Child(Wait,TEXT("paid"));Paid->SetNumberField(Id,Number(Paid,Id)+Keep);
 Child(T,TEXT("done"))->SetStringField(Id,TEXT("rescheduled"));
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Old=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Old))Ratings=*Old;
 Ratings.Add(MakeShared<FJsonValueNumber>(Number(ToursDefs(),TEXT("reschedule_rating"),4)));while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);
 LastMessage=FString::Printf(TEXT("%s remarcado para amanhã: %d pessoa(s) mantiveram a reserva."),*String(Tour,TEXT("name")),Keep);return Save();
}

static void RateTour(UMareSimulation* Sim,double Rating)
{
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(Sim->State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
 Ratings.Add(MakeShared<FJsonValueNumber>(Rating));while(Ratings.Num()>40)Ratings.RemoveAt(0);Sim->State->SetArrayField(TEXT("ratings"),Ratings);
}

double UMareSimulation::GuideTour(const FString& Id,const TArray<int32>& Choices,double Bonus)
{
 const auto Tour=TourDef(Id);
 if(!Tour || !IsTourBoarding(Id)){Fail(TEXT("Só dá para guiar na hora da saída."));return 0;}
 auto T=Tours();const int32 Pax=int32(Number(Object(T,TEXT("sold")),Id));if(Pax<=0){Fail(TEXT("Nenhum bilhete vendido para este passeio."));return 0;}
 int32 Good=0,Ok=0;for(int32 C:Choices){Good+=C==0;Ok+=C==1;}
 const double Groups=FMath::Max(1.,Number(Object(T,TEXT("groups_sold")),Id));
 // Bonus: what happened on a playable tour (dolphins seen, passengers seasick; MareBoatTourWorld).
 const double Rating=FMath::Clamp(2+Good+.5*Ok+Number(Object(T,TEXT("extra_rating")),Id)/Groups+Bonus,1.,5.);
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
 for(const FString& Id:TourIds()){const auto Tour=TourDef(Id);if(!String(Done,Id).IsEmpty() && String(Done,Id)!=TEXT("storm"))continue;
  // Out at sea with the player (playable boat tour): it ends at the pier, not with the clock.
  if(String(T,TEXT("active"))==Id)continue;
  const int32 Departs=int32(Number(Tour,TEXT("hour")));
  // High tide or a storm keeps the boats in: sea tours are called off for the day (the lighthouse trail still goes).
  if(String(Done,Id)==TEXT("storm")){if(Started>=Departs){RefundTour(Id);}continue;}
  if(IsSeaRough() && Id!=TEXT("farol")){
   // With tickets sold the player decides (refund or tomorrow); otherwise it is simply off for the day.
   Queue->SetNumberField(Id,0);Child(T,TEXT("groups"))->SetArrayField(Id,TArray<TSharedPtr<FJsonValue>>());
   if(Number(Sold,Id)>0){Done->SetStringField(Id,TEXT("storm"));LastMessage=String(Tour,TEXT("name"))+TEXT(": mar bravo! Na bilheteria, devolva o dinheiro ou remarque para amanhã.");}
   else Done->SetStringField(Id,TEXT("cancelled"));continue;}
  // Buyers walk up to the booth during the three hours before the departure (sea tours need calm sea).
  if(Started>=Departs-3 && Started<Departs){const int32 Wanted=TourPassengers(Tour);
   // First hour: yesterday's rescheduled (paid) seats and the waiting list come first.
   if(Started==Departs-3){auto Wait=Child(State,TEXT("tour_wait"));auto PaidSeats=Child(Wait,TEXT("paid"));
    if(Number(PaidSeats,Id)>0){Sold->SetNumberField(Id,Number(Sold,Id)+Number(PaidSeats,Id));PaidSeats->RemoveField(Id);}
    auto WaitGroups=Child(Wait,TEXT("groups"));const TArray<TSharedPtr<FJsonValue>>* Waiting=nullptr;
    if(WaitGroups->TryGetArrayField(Id,Waiting)){auto& Line=ListOf(Child(T,TEXT("groups")),Id);
     for(const auto& W:*Waiting){Line.Add(W);Queue->SetNumberField(Id,Number(Queue,Id)+Number(W->AsObject(),TEXT("adults"),1)+Number(W->AsObject(),TEXT("kids")));}
     WaitGroups->RemoveField(Id);}}
   const int32 Room=TourSeats(Tour)-int32(Number(Sold,Id))-int32(Number(Queue,Id));
   int32 People=FMath::Clamp(FMath::CeilToInt(Wanted/3.)+FMath::RandRange(-1,1),0,FMath::Max(0,Room+2));
   // People arrive in groups: adults, maybe kids, a trait the extras can please.
   const auto TraitObj=Object(ToursDefs(),TEXT("traits"));TArray<FString> Traits;for(const auto& Pair:TraitObj->Values)Traits.Add(FString(Pair.Key.ToView()));
   while(People>0){const int32 A=FMath::Clamp(FMath::RandRange(1,int32(Number(ToursDefs(),TEXT("max_adults"),3))),1,People);
    const int32 K=People-A>0 && FMath::FRand()<Number(ToursDefs(),TEXT("kid_chance"),.4)?FMath::Min(People-A,FMath::RandRange(1,int32(Number(ToursDefs(),TEXT("max_kids"),2)))):0;
    AddTourGroup(Id,A,K,Traits.Num() && FMath::FRand()<.7?Traits[FMath::RandRange(0,Traits.Num()-1)]:FString());People-=A+K;}
   if(bGuide && Number(Queue,Id)>0){const FString Before=LastMessage;const int32 N=SellTickets(Id);LastMessage=Before;
    if(N>0)StaffDid(String(Object(CustomDefs(),TEXT("operations")),TEXT("tour_guide")),N,N*TicketPrice(Id));}}
  // End of the departure hour: whoever was not guided by the player goes with the guide, or is refunded.
  if(Started==Departs){const int32 Pax=int32(Number(Sold,Id));Queue->SetNumberField(Id,0);Child(T,TEXT("groups"))->SetArrayField(Id,TArray<TSharedPtr<FJsonValue>>());
   if(Pax<=0){Done->SetStringField(Id,TEXT("empty"));continue;}
   if(bGuide){Book(-Number(Tour,TEXT("cost")),String(Tour,TEXT("name"))+TEXT(": custo da saída"));AddToday(State,-Number(Tour,TEXT("cost")));
    Done->SetStringField(Id,TEXT("guide"));RateTour(this,FMath::Clamp(3.5+Number(Object(T,TEXT("extra_rating")),Id)/FMath::Max(1.,Number(Object(T,TEXT("groups_sold")),Id)),1.,5.));AddFame(Pax/2);}
   else{const double Refund=Pax*TicketPrice(Id);Book(-Refund,String(Tour,TEXT("name"))+TEXT(": cancelado, bilhetes devolvidos"));AddToday(State,-Refund);
    Done->SetStringField(Id,TEXT("cancelled"));LastMessage=String(Tour,TEXT("name"))+TEXT(" cancelado: ninguém guiou. Contrate um guia ou vá ao píer na hora.");}}
 }
}
