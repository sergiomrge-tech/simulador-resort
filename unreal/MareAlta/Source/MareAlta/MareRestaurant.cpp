// Grand Hotel restaurant, hands-on: table orders, the kitchen pass, room service and events booked a day ahead
// (gameplay plan, P1 "Restaurante do hotel"). State "restaurant" lives in the save like the other places.
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
 TArray<TSharedPtr<FJsonValue>>& List(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  if(!Parent->HasTypedField<EJson::Array>(Key))Parent->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
  return const_cast<TArray<TSharedPtr<FJsonValue>>&>(Parent->GetArrayField(Key));
 }
 const TCHAR* DinerNames[]={TEXT("Sra. Helena"),TEXT("Sr. Augusto"),TEXT("Casal Lima"),TEXT("Família Souza"),TEXT("Dr. Paulo"),TEXT("Sra. Íris"),
  TEXT("Sr. Mauro"),TEXT("Casal Prado"),TEXT("Sra. Vera"),TEXT("Sr. Ciro")};
}

TSharedPtr<FJsonObject> UMareSimulation::RestaurantDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/restaurant.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}
TSharedPtr<FJsonObject> UMareSimulation::Restaurant(){return Child(State,TEXT("restaurant"));}

double UMareSimulation::RestaurantNow() const{return Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes"));}

bool UMareSimulation::IsRestaurantOpen() const
{
 bool bHotel=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);if(!bHotel)return false;
 const double Hour=Number(State,TEXT("minutes"))/60;const TArray<TSharedPtr<FJsonValue>>* Services=nullptr;
 if(RestaurantDefs()->TryGetArrayField(TEXT("services"),Services))for(const auto& V:*Services){const auto& S=V->AsArray();
  if(S.Num()==2 && Hour>=S[0]->AsNumber() && Hour<S[1]->AsNumber())return true;}
 return false;
}

TSharedPtr<FJsonObject> UMareSimulation::MenuDish(const FString& Id) const
{
 const TArray<TSharedPtr<FJsonValue>>* Menu=nullptr;
 if(RestaurantDefs()->TryGetArrayField(TEXT("menu"),Menu))for(const auto& V:*Menu)if(String(V->AsObject(),TEXT("id"))==Id)return V->AsObject();
 return nullptr;
}

double UMareSimulation::MenuPrice(const FString& Id) const
{
 // 5.3: each star of the critic's guide makes the whole menu dearer.
 const double Stars=1+Number(Object(RestaurantDefs(),TEXT("critic")),TEXT("star_price"),.12)*RestaurantStars();
 const auto Dish=MenuDish(Id);return Dish?FMath::RoundToDouble(Number(Dish,TEXT("price"))*FMath::Max(1.,PlaceIncomeFactor(TEXT("hotel_restaurante")))*Stars):0;
}

TSharedPtr<FJsonObject> UMareSimulation::TableOrder(int32 Table) const
{
 const TArray<TSharedPtr<FJsonValue>>* Tables=nullptr;
 if(Object(State,TEXT("restaurant"))->TryGetArrayField(TEXT("tables"),Tables))for(const auto& V:*Tables)if(int32(Number(V->AsObject(),TEXT("table")))==Table)return V->AsObject();
 return nullptr;
}

static FString RandomDish(const UMareSimulation* Sim)
{
 const TArray<TSharedPtr<FJsonValue>>* Menu=nullptr;if(!Sim->RestaurantDefs()->TryGetArrayField(TEXT("menu"),Menu) || Menu->IsEmpty())return FString();
 return UMareSimulation::String((*Menu)[FMath::RandRange(0,Menu->Num()-1)]->AsObject(),TEXT("id"));
}

FString UMareSimulation::SeatDiners(int32 Table)
{
 if(!IsRestaurantOpen() || TableOrder(Table))return FString();
 const TArray<TSharedPtr<FJsonValue>>* Tables=nullptr;if(!RestaurantDefs()->TryGetArrayField(TEXT("tables"),Tables) || !Tables->IsValidIndex(Table))return FString();
 auto R=Restaurant();const int32 Next=int32(Number(R,TEXT("next")));R->SetNumberField(TEXT("next"),Next+1);
 auto O=MakeShared<FJsonObject>();O->SetNumberField(TEXT("table"),Table);O->SetStringField(TEXT("stage"),TEXT("order"));
 O->SetStringField(TEXT("name"),DinerNames[(Next*3+1)%UE_ARRAY_COUNT(DinerNames)]);O->SetNumberField(TEXT("since"),RestaurantNow());
 List(R,TEXT("tables")).Add(MakeShared<FJsonValueObject>(O));return String(O,TEXT("name"));
}

bool UMareSimulation::UseTable(int32 Table)
{
 auto O=TableOrder(Table);if(!O)return Fail(TEXT("Mesa livre."));const FString Stage=String(O,TEXT("stage"));
 if(Stage==TEXT("order")){const FString Dish=RandomDish(this);O->SetStringField(TEXT("dish"),Dish);O->SetStringField(TEXT("stage"),TEXT("cooking"));
  O->SetNumberField(TEXT("ready"),RestaurantNow()+Number(RestaurantDefs(),TEXT("cook_minutes"),20));
  // 5.3: a fish dish takes a fish of the pier from the stock (fresh, dearer); with none the kitchen buys one.
  const FString Fish=TakeKitchenFish(O);
  bool bCritic=false;O->TryGetBoolField(TEXT("critic"),bCritic);
  if(bCritic)LastMessage=FString::Printf(TEXT("%s pediu %s e anotou algo num caderninho...%s"),*String(O,TEXT("name")),*String(MenuDish(Dish),TEXT("name")),*Fish);
  else LastMessage=FString::Printf(TEXT("%s pediu %s. Na cozinha!%s"),*String(O,TEXT("name")),*String(MenuDish(Dish),TEXT("name")),*Fish);
  return Save();}
 if(Stage==TEXT("tray")){
  const double Waited=RestaurantNow()-Number(O,TEXT("since"));const FString Dish=String(O,TEXT("dish"));
  bool bFresh=false;O->TryGetBoolField(TEXT("fresh"),bFresh);const auto F=Object(RestaurantDefs(),TEXT("fresh_fish"));
  const double Paid=FMath::RoundToDouble(MenuPrice(Dish)*(1+.15*FMath::Clamp(1-Waited/40.,0.,1.))*(bFresh?1+Number(F,TEXT("bonus"),.25):1.));
  Book(Paid,TEXT("Restaurante: ")+String(MenuDish(Dish),TEXT("name")));AddFame(1+(bFresh?int32(Number(F,TEXT("fame"),1)):0));
  bool bCritic=false;O->TryGetBoolField(TEXT("critic"),bCritic);
  if(bCritic){ReviewCritic(O,false);const FString Review=LastMessage;
   auto& Tables=List(Restaurant(),TEXT("tables"));Tables.RemoveAll([Table](const TSharedPtr<FJsonValue>& V){return int32(UMareSimulation::Number(V->AsObject(),TEXT("table")))==Table;});
   Restaurant()->SetNumberField(TEXT("served"),Number(Restaurant(),TEXT("served"))+1);
   LastMessage=FString::Printf(TEXT("Prato servido: R$ %.0f. "),Paid)+Review;return Save();}
  auto& Tables=List(Restaurant(),TEXT("tables"));Tables.RemoveAll([Table](const TSharedPtr<FJsonValue>& V){return int32(UMareSimulation::Number(V->AsObject(),TEXT("table")))==Table;});
  Restaurant()->SetNumberField(TEXT("served"),Number(Restaurant(),TEXT("served"))+1);
  LastMessage=FString::Printf(TEXT("Prato servido: R$ %.0f."),Paid);return Save();}
 return Fail(Stage==TEXT("cooking")?TEXT("O prato ainda está na cozinha."):TEXT("Nada a fazer nesta mesa."));
}

int32 UMareSimulation::PickUpPass()
{
 int32 Got=0;const double Now=RestaurantNow();auto R=Restaurant();
 for(const TCHAR* Key:{TEXT("tables"),TEXT("room")})for(const auto& V:List(R,Key)){auto O=V->AsObject();
  if(String(O,TEXT("stage"))==TEXT("cooking") && Number(O,TEXT("ready"))<=Now){O->SetStringField(TEXT("stage"),TEXT("tray"));++Got;}}
 if(!Got){Fail(TEXT("Nenhum prato pronto no passe."));return 0;}
 LastMessage=FString::Printf(TEXT("%d prato(s) na bandeja."),Got);Save();return Got;
}

int32 UMareSimulation::DeliverRoomService()
{
 auto& Room=List(Restaurant(),TEXT("room"));int32 N=0;double Paid=0;
 for(int32 I=Room.Num()-1;I>=0;--I){auto O=Room[I]->AsObject();if(String(O,TEXT("stage"))!=TEXT("tray"))continue;
  Paid+=FMath::RoundToDouble(MenuPrice(String(O,TEXT("dish")))*(1+Number(RestaurantDefs(),TEXT("room_fee"),.15)));Room.RemoveAt(I);++N;}
 if(!N){Fail(TEXT("Nenhum serviço de quarto na bandeja."));return 0;}
 Book(Paid,FString::Printf(TEXT("Serviço de quarto: %d entrega(s)"),N));AddFame(N);
 LastMessage=FString::Printf(TEXT("Serviço de quarto entregue: R$ %.0f."),Paid);Save();return N;
}

bool UMareSimulation::BookEvent(const FString& Id)
{
 const TArray<TSharedPtr<FJsonValue>>* Events=nullptr;TSharedPtr<FJsonObject> Event;
 if(RestaurantDefs()->TryGetArrayField(TEXT("events"),Events))for(const auto& V:*Events)if(String(V->AsObject(),TEXT("id"))==Id)Event=V->AsObject();
 bool bHotel=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
 if(!Event || !bHotel)return Fail(TEXT("Evento indisponível."));
 auto R=Restaurant();if(Object(R,TEXT("event"))->Values.Num())return Fail(TEXT("Já há um evento marcado."));
 if(Money()<Number(Event,TEXT("cost")))return Fail(FString::Printf(TEXT("Preparar o evento custa R$ %.0f."),Number(Event,TEXT("cost"))));
 Book(-Number(Event,TEXT("cost")),TEXT("Preparativos: ")+String(Event,TEXT("name")));
 auto Booked=MakeShared<FJsonObject>();Booked->SetStringField(TEXT("id"),Id);Booked->SetNumberField(TEXT("day"),Number(State,TEXT("day"),1)+1);
 R->SetObjectField(TEXT("event"),Booked);
 LastMessage=FString::Printf(TEXT("%s marcado para amanhã às %.0fh."),*String(Event,TEXT("name")),Number(RestaurantDefs(),TEXT("event_hour"),20));return Save();
}

void UMareSimulation::RestaurantHour(int32 Hour)
{
 bool bHotel=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);if(!bHotel)return;
 auto R=Restaurant();const double Now=RestaurantNow();const int32 Started=Hour-1;
 // Event of the day: guests, income and fame at the event hour.
 const auto Event=Object(R,TEXT("event"));
 // An event whose night was slept through still happens (the crew runs it): it used to vanish with the preparation paid.
 const bool bPast=Event->Values.Num() && int32(Number(Event,TEXT("day")))<int32(Number(State,TEXT("day"),1));
 if(Event->Values.Num() && (bPast || (int32(Number(Event,TEXT("day")))==int32(Number(State,TEXT("day"),1)) && Started==int32(Number(RestaurantDefs(),TEXT("event_hour"),20))))){
  const TArray<TSharedPtr<FJsonValue>>* Events=nullptr;
  if(RestaurantDefs()->TryGetArrayField(TEXT("events"),Events))for(const auto& V:*Events){const auto E=V->AsObject();if(String(E,TEXT("id"))!=String(Event,TEXT("id")))continue;
   const double Income=FMath::RoundToDouble(Number(E,TEXT("income"))*FMath::Max(1.,PlaceIncomeFactor(TEXT("hotel_restaurante"))));
   Book(Income,String(E,TEXT("name"))+FString::Printf(TEXT(" (%.0f convidados)"),Number(E,TEXT("guests"))));AddFame(int32(Number(E,TEXT("fame"))));
   LastMessage=String(E,TEXT("name"))+TEXT(" foi um sucesso!");}
  R->RemoveField(TEXT("event"));}
 else if(!Event->Values.Num() || Number(Event,TEXT("day"))<Number(State,TEXT("day"),1))R->RemoveField(TEXT("event"));
 // The hotel crew serves whoever waited too long, at a share of the price and without tip.
 // The restaurant waiter takes over after 15 minutes at 90%; without him the hotel crew helps after 45 at 70%.
 const bool bWaiter=HasStaff(TEXT("garcom_hotel"));
 const double CrewAfter=bWaiter?15:Number(RestaurantDefs(),TEXT("crew_minutes"),45),Share=bWaiter?.9:Number(RestaurantDefs(),TEXT("crew_share"),.7);double Crew=0;
 for(const TCHAR* Key:{TEXT("tables"),TEXT("room")}){auto& Items=List(R,Key);
  for(int32 I=Items.Num()-1;I>=0;--I){const auto O=Items[I]->AsObject();if(Now-Number(O,TEXT("since"))<CrewAfter)continue;
   FString Dish=String(O,TEXT("dish"));if(Dish.IsEmpty())Dish=RandomDish(this);
   bool bCritic=false;O->TryGetBoolField(TEXT("critic"),bCritic);if(bCritic){O->SetStringField(TEXT("dish"),Dish);ReviewCritic(O,true);}Crew+=FMath::RoundToDouble(MenuPrice(Dish)*Share);Items.RemoveAt(I);if(bWaiter)StaffDid(TEXT("garcom_hotel"),1,FMath::RoundToDouble(MenuPrice(Dish)*Share));}}
 if(Crew>0)Book(Crew,bWaiter?TEXT("Restaurante (garçom)"):TEXT("Restaurante (equipe do hotel)"));
 if(!IsRestaurantOpen())return;
 // New diners at about half of the free tables, and room service from the suites.
 const TArray<TSharedPtr<FJsonValue>>* Tables=nullptr;
 // 5.3: on his day the critic comes to one of the services, disguised as any diner.
 {const auto C=Object(RestaurantDefs(),TEXT("critic"));const int32 Day=int32(Number(State,TEXT("day"),1));
  const int32 Due=int32(Number(R,TEXT("critic_next"),Number(C,TEXT("from_day"),3)));
  if(Day>=Due && int32(Number(R,TEXT("critic_day"),-1))!=Day && FMath::FRand()<Number(C,TEXT("chance_per_hour"),.4))SeatCritic();}
 if(RestaurantDefs()->TryGetArrayField(TEXT("tables"),Tables))for(int32 I=0;I<Tables->Num();++I)if(FMath::FRand()<.5f)SeatDiners(I);
 if(FMath::FRand()<.7f){auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("dish"),RandomDish(this));O->SetStringField(TEXT("stage"),TEXT("cooking"));
  O->SetNumberField(TEXT("suite"),FMath::RandRange(301,332));O->SetNumberField(TEXT("since"),Now);O->SetNumberField(TEXT("ready"),Now+Number(RestaurantDefs(),TEXT("cook_minutes"),20));
  List(R,TEXT("room")).Add(MakeShared<FJsonValueObject>(O));}
}

FString UMareSimulation::TakeKitchenFish(const TSharedPtr<FJsonObject>& O)
{
 bool bFish=false;if(auto D=MenuDish(String(O,TEXT("dish"))))D->TryGetBoolField(TEXT("fish"),bFish);if(!bFish)return FString();
 auto Stock=Object(State,TEXT("stock"));const auto F=Object(RestaurantDefs(),TEXT("fresh_fish"));
 if(Number(Stock,TEXT("peixe"))>=1){Stock->SetNumberField(TEXT("peixe"),Number(Stock,TEXT("peixe"))-1);O->SetBoolField(TEXT("fresh"),true);
  return FString::Printf(TEXT(" Peixe fresco do píer (sobram %.0f)."),Number(Stock,TEXT("peixe")));}
 const double Cost=Number(F,TEXT("buy_cost"),22);Book(-Cost,TEXT("Restaurante: peixe do fornecedor"));
 return FString::Printf(TEXT(" Sem peixe pescado: o fornecedor cobrou R$ %.0f."),Cost);
}

int32 UMareSimulation::RestaurantStars() const{return int32(Number(Object(Object(State,TEXT("prog")),TEXT("restaurant")),TEXT("stars")));}

int32 UMareSimulation::SeatCritic()
{
 if(!IsRestaurantOpen())return -1;const TArray<TSharedPtr<FJsonValue>>* Tables=nullptr;if(!RestaurantDefs()->TryGetArrayField(TEXT("tables"),Tables))return -1;
 for(const auto& V:List(Restaurant(),TEXT("tables"))){bool b=false;V->AsObject()->TryGetBoolField(TEXT("critic"),b);if(b)return -1;}
 TArray<int32> Free;for(int32 I=0;I<Tables->Num();++I)if(!TableOrder(I))Free.Add(I);if(Free.IsEmpty())return -1;
 const int32 Table=Free[FMath::RandRange(0,Free.Num()-1)];if(SeatDiners(Table).IsEmpty())return -1;
 TableOrder(Table)->SetBoolField(TEXT("critic"),true);
 const auto C=Object(RestaurantDefs(),TEXT("critic"));auto R=Restaurant();const int32 Day=int32(Number(State,TEXT("day"),1));
 const TArray<TSharedPtr<FJsonValue>>* Every=nullptr;int32 Gap=4;
 if(C->TryGetArrayField(TEXT("every_days"),Every) && Every->Num()==2)Gap=FMath::RandRange(int32((*Every)[0]->AsNumber()),int32((*Every)[1]->AsNumber()));
 R->SetNumberField(TEXT("critic_day"),Day);R->SetNumberField(TEXT("critic_next"),Day+Gap);Save();return Table;
}

void UMareSimulation::ReviewCritic(const TSharedPtr<FJsonObject>& O,bool bByCrew)
{
 // 5.3: the critic's score: 5 served by the player, -1 per 10 min over 20 of waiting, -0.5 for fish that is not fresh.
 const auto C=Object(RestaurantDefs(),TEXT("critic"));double Score=0;
 if(bByCrew)Score=HasStaff(TEXT("garcom_hotel"))?Number(C,TEXT("waiter_score"),3):Number(C,TEXT("crew_score"),2.5);
 else{const double Waited=RestaurantNow()-Number(O,TEXT("since"));Score=5-FMath::Max(0.,(Waited-20)/10);
  bool bFish=false,bFresh=false;if(auto D=MenuDish(String(O,TEXT("dish"))))D->TryGetBoolField(TEXT("fish"),bFish);O->TryGetBoolField(TEXT("fresh"),bFresh);
  if(bFish && !bFresh)Score-=.5;}
 Score=FMath::Clamp(FMath::RoundToDouble(Score*2)/2,1.,5.);AddRating(Score);
 auto Prog=Object(State,TEXT("prog"));if(!Prog->HasTypedField<EJson::Object>(TEXT("restaurant")))Prog->SetObjectField(TEXT("restaurant"),MakeShared<FJsonObject>());
 auto P=Object(Prog,TEXT("restaurant"));const int32 Stars=RestaurantStars();const int32 Max=int32(Number(C,TEXT("max_stars"),3));FString Result;
 if(Score>=Number(C,TEXT("star_score"),4.5) && Stars<Max){P->SetNumberField(TEXT("stars"),Stars+1);AddFame(int32(Number(C,TEXT("star_fame"),15)));
  Result=FString::Printf(TEXT("O restaurante ganhou a %dª estrela (cardápio +%.0f%%)!"),Stars+1,Number(C,TEXT("star_price"),.12)*100);}
 else if(Score<=Number(C,TEXT("bad_score"),2.5)){AddFame(-int32(Number(C,TEXT("bad_fame"),6)));Result=TEXT("Crítica ruim: a fama caiu.");}
 else{AddFame(int32(Number(C,TEXT("good_fame"),4)));Result=Stars>=Max?FString(TEXT("O restaurante manteve as estrelas.")):FString(TEXT("Boa crítica, mas ainda sem estrela nova."));}
 TArray<TSharedPtr<FJsonValue>> Reviews;const TArray<TSharedPtr<FJsonValue>>* Old=nullptr;if(P->TryGetArrayField(TEXT("reviews"),Old))Reviews=*Old;
 auto Rv=MakeShared<FJsonObject>();Rv->SetNumberField(TEXT("day"),Number(State,TEXT("day"),1));Rv->SetNumberField(TEXT("score"),Score);Rv->SetNumberField(TEXT("crew"),bByCrew?1:0);
 Reviews.Add(MakeShared<FJsonValueObject>(Rv));while(Reviews.Num()>5)Reviews.RemoveAt(0);P->SetArrayField(TEXT("reviews"),Reviews);
 const FString Guide=String(C,TEXT("guide"));const FString Who=String(O,TEXT("name"));
 if(bByCrew)LastMessage=FString::Printf(TEXT("%s era o crítico do %s (atendido pela equipe)! Nota %.1f. %s"),*Who,*Guide,Score,*Result);
 else LastMessage=FString::Printf(TEXT("%s era o crítico do %s! Nota %.1f. %s"),*Who,*Guide,Score,*Result);
}
