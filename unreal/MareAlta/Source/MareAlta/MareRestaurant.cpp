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
 const auto Dish=MenuDish(Id);return Dish?FMath::RoundToDouble(Number(Dish,TEXT("price"))*FMath::Max(1.,PlaceIncomeFactor(TEXT("hotel_restaurante")))):0;
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
  LastMessage=FString::Printf(TEXT("%s pediu %s. Na cozinha!"),*String(O,TEXT("name")),*String(MenuDish(Dish),TEXT("name")));return Save();}
 if(Stage==TEXT("tray")){
  const double Waited=RestaurantNow()-Number(O,TEXT("since"));const FString Dish=String(O,TEXT("dish"));
  const double Paid=FMath::RoundToDouble(MenuPrice(Dish)*(1+.15*FMath::Clamp(1-Waited/40.,0.,1.)));
  Book(Paid,TEXT("Restaurante: ")+String(MenuDish(Dish),TEXT("name")));AddFame(1);
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
 if(Event->Values.Num() && int32(Number(Event,TEXT("day")))==int32(Number(State,TEXT("day"),1)) && Started==int32(Number(RestaurantDefs(),TEXT("event_hour"),20))){
  const TArray<TSharedPtr<FJsonValue>>* Events=nullptr;
  if(RestaurantDefs()->TryGetArrayField(TEXT("events"),Events))for(const auto& V:*Events){const auto E=V->AsObject();if(String(E,TEXT("id"))!=String(Event,TEXT("id")))continue;
   const double Income=FMath::RoundToDouble(Number(E,TEXT("income"))*FMath::Max(1.,PlaceIncomeFactor(TEXT("hotel_restaurante"))));
   Book(Income,String(E,TEXT("name"))+FString::Printf(TEXT(" (%.0f convidados)"),Number(E,TEXT("guests"))));AddFame(int32(Number(E,TEXT("fame"))));
   LastMessage=String(E,TEXT("name"))+TEXT(" foi um sucesso!");}
  R->RemoveField(TEXT("event"));}
 else if(!Event->Values.Num() || Number(Event,TEXT("day"))<Number(State,TEXT("day"),1))R->RemoveField(TEXT("event"));
 // The hotel crew serves whoever waited too long, at a share of the price and without tip.
 const double CrewAfter=Number(RestaurantDefs(),TEXT("crew_minutes"),45),Share=Number(RestaurantDefs(),TEXT("crew_share"),.7);double Crew=0;
 for(const TCHAR* Key:{TEXT("tables"),TEXT("room")}){auto& Items=List(R,Key);
  for(int32 I=Items.Num()-1;I>=0;--I){const auto O=Items[I]->AsObject();if(Now-Number(O,TEXT("since"))<CrewAfter)continue;
   FString Dish=String(O,TEXT("dish"));if(Dish.IsEmpty())Dish=RandomDish(this);Crew+=FMath::RoundToDouble(MenuPrice(Dish)*Share);Items.RemoveAt(I);}}
 if(Crew>0)Book(Crew,TEXT("Restaurante (equipe do hotel)"));
 if(!IsRestaurantOpen())return;
 // New diners at about half of the free tables, and room service from the suites.
 const TArray<TSharedPtr<FJsonValue>>* Tables=nullptr;
 if(RestaurantDefs()->TryGetArrayField(TEXT("tables"),Tables))for(int32 I=0;I<Tables->Num();++I)if(FMath::FRand()<.5f)SeatDiners(I);
 if(FMath::FRand()<.7f){auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("dish"),RandomDish(this));O->SetStringField(TEXT("stage"),TEXT("cooking"));
  O->SetNumberField(TEXT("suite"),FMath::RandRange(301,332));O->SetNumberField(TEXT("since"),Now);O->SetNumberField(TEXT("ready"),Now+Number(RestaurantDefs(),TEXT("cook_minutes"),20));
  List(R,TEXT("room")).Add(MakeShared<FJsonValueObject>(O));}
}
