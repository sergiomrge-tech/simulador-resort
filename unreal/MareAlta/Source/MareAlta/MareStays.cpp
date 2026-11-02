// Hands-on lodging for the pousada: reception queue, haggling, stays and cleaning (gameplay plan M2/M3).
// Kept in the simulation state so saves, tests and a future co-op mode share one source of truth.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 TSharedPtr<FJsonObject> Child(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  const TSharedPtr<FJsonObject>* Found=nullptr;if(Parent->TryGetObjectField(Key,Found))return *Found;
  auto Created=MakeShared<FJsonObject>();Parent->SetObjectField(Key,Created);return Created;
 }
 /** Mutable array field (created empty when missing). */
 TArray<TSharedPtr<FJsonValue>>& List(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  if(!Parent->HasTypedField<EJson::Array>(Key))Parent->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
  return const_cast<TArray<TSharedPtr<FJsonValue>>&>(Parent->GetArrayField(Key));
 }
 TSharedPtr<FJsonObject> Find(TArray<TSharedPtr<FJsonValue>>& Items,const FString& Id,int32* Index=nullptr)
 {
  for(int32 I=0;I<Items.Num();++I)if(UMareSimulation::String(Items[I]->AsObject(),TEXT("id"))==Id){if(Index)*Index=I;return Items[I]->AsObject();}
  return nullptr;
 }
 const TCHAR* GuestNames[]={TEXT("Ana"),TEXT("Bruno"),TEXT("Carla"),TEXT("Diego"),TEXT("Elisa"),TEXT("Fábio"),TEXT("Gabi"),TEXT("Heitor"),
  TEXT("Iara"),TEXT("João"),TEXT("Kátia"),TEXT("Lucas"),TEXT("Marina"),TEXT("Nina"),TEXT("Otávio"),TEXT("Paula")};
}

TSharedPtr<FJsonObject> UMareSimulation::Stays(){return Child(State,TEXT("stays"));}

/** Rooms of a place: the pousada's bungalows, or the Grand Hotel's suites once it is open. */
static int32 PlaceRooms(const UMareSimulation* Sim,const FString& Place)
{
 if(Place==TEXT("hotel")){bool bHotel=false;UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);return bHotel?32:0;}
 return Sim->PousadaRooms();
}
TSharedPtr<FJsonObject> UMareSimulation::StayOps(const FString& Place) const
{
 return Object(Object(CustomDefs(),TEXT("operations")),Place==TEXT("hotel")?TEXT("hotel_stays"):TEXT("pousada"));
}
double UMareSimulation::StayRate(const FString& Place) const
{
 return Place==TEXT("hotel")?FMath::RoundToDouble(220+SlotSum(TEXT("hotel_suites"),TEXT("rate"))+12*(Stars()-4)):PousadaRate();
}
void UMareSimulation::SyncRooms()
{
 auto& Rooms=List(Stays(),TEXT("rooms"));
 for(const TCHAR* Place:{TEXT("pousada"),TEXT("hotel")}){
  int32 Have=0;for(const auto& R:Rooms)Have+=String(R->AsObject(),TEXT("place"))==Place;
  for(int32 I=Have;I<PlaceRooms(this,Place);++I){auto R=MakeShared<FJsonObject>();R->SetStringField(TEXT("id"),FString::Printf(TEXT("%s_%d"),Place,I));
   R->SetStringField(TEXT("place"),Place);R->SetStringField(TEXT("state"),TEXT("free"));Rooms.Add(MakeShared<FJsonValueObject>(R));}}
}
int32 UMareSimulation::FreeCleanRooms(const FString& Place) const
{
 const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;int32 Free=0;
 if(Object(State,TEXT("stays"))->TryGetArrayField(TEXT("rooms"),Rooms))for(const auto& R:*Rooms){const auto O=R->AsObject();
  const FString P=String(O,TEXT("place"));Free+=(P==Place || (P.IsEmpty() && Place==TEXT("pousada"))) && String(O,TEXT("state"))==TEXT("free");}
 return Free;
}

FString UMareSimulation::AddArrival(const FString& Place)
{
 SyncRooms();auto& Queue=List(Stays(),TEXT("queue"));if(PlaceRooms(this,Place)<=0)return FString();
 int32 Waiting=0;for(const auto& V:Queue)Waiting+=String(V->AsObject(),TEXT("place"))==Place;if(Waiting>=3)return FString();
 auto Ops=StayOps(Place);
 const TArray<TSharedPtr<FJsonValue>>* Profiles=nullptr;if(!Ops->TryGetArrayField(TEXT("profiles"),Profiles) || Profiles->IsEmpty())return FString();
 auto Stay=Stays();const int32 Serial=Number(Stay,TEXT("serial"));Stay->SetNumberField(TEXT("serial"),Serial+1);
 FRandomStream Rng(int32(Number(State,TEXT("day"),1))*977+Serial*131+7);
 const auto Profile=(*Profiles)[Rng.RandRange(0,Profiles->Num()-1)]->AsObject();
 const double Reference=StayRate(Place);
 const double Limit=FMath::RoundToDouble(Reference*Rng.FRandRange(Number(Profile,TEXT("min"),.8),Number(Profile,TEXT("max"),1.1)));
 auto G=MakeShared<FJsonObject>();G->SetStringField(TEXT("id"),FString::Printf(TEXT("g%d"),Serial));
 G->SetStringField(TEXT("name"),GuestNames[Rng.RandRange(0,UE_ARRAY_COUNT(GuestNames)-1)]);
 G->SetStringField(TEXT("profile"),String(Profile,TEXT("id")));G->SetStringField(TEXT("label"),String(Profile,TEXT("label")));
 G->SetNumberField(TEXT("limit"),Limit);G->SetNumberField(TEXT("offer"),FMath::RoundToDouble(Limit*Rng.FRandRange(.75,.9)));
 G->SetNumberField(TEXT("round"),0);G->SetNumberField(TEXT("mood"),1);G->SetStringField(TEXT("place"),Place);
 G->SetNumberField(TEXT("since"),Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes")));
 G->SetNumberField(TEXT("nights"),Rng.RandRange(int32(Number(Profile,TEXT("nights_min"),1)),int32(Number(Profile,TEXT("nights_max"),3))));
 Queue.Add(MakeShared<FJsonValueObject>(G));return String(G,TEXT("id"));
}

UMareSimulation::EHaggle UMareSimulation::Haggle(const FString& Guest,double Price,double& OutOffer)
{
 auto& Queue=List(Stays(),TEXT("queue"));int32 Index=INDEX_NONE;auto G=Find(Queue,Guest,&Index);
 if(!G || Price<=0)return EHaggle::Invalid;
 const double Limit=Number(G,TEXT("limit")),Offer=Number(G,TEXT("offer"));const int32 Round=Number(G,TEXT("round"));
 Price=FMath::RoundToDouble(Price);
 auto CheckIn=[&](double Rate){
  SyncRooms();auto& Rooms=List(Stays(),TEXT("rooms"));TSharedPtr<FJsonObject> Room;
  const FString Place=String(G,TEXT("place")).IsEmpty()?FString(TEXT("pousada")):String(G,TEXT("place"));
  for(const auto& R:Rooms){const auto O=R->AsObject();const FString P=String(O,TEXT("place"));
   if((P==Place || (P.IsEmpty() && Place==TEXT("pousada"))) && String(O,TEXT("state"))==TEXT("free")){Room=O;break;}}
  if(!Room)return false;
  // Closing near the limit earns more but leaves the guest less happy (feeds the stay rating).
  const double Mood=FMath::Clamp(Number(G,TEXT("mood"))*(.55+.45*FMath::Clamp((Limit-Rate)/FMath::Max(1.,Limit*.25),0.,1.)),0.,1.);
  const int32 Nights=Number(G,TEXT("nights"),1);
  Room->SetStringField(TEXT("state"),TEXT("occupied"));Room->SetObjectField(TEXT("guest"),G);Room->SetNumberField(TEXT("nights"),Nights);
  Room->SetNumberField(TEXT("rate"),Rate);Room->SetNumberField(TEXT("mood"),Mood);
  Book(Rate*Nights,FString::Printf(TEXT("%s: %s, %d diária(s) de R$ %.0f"),Place==TEXT("hotel")?TEXT("Grand Hotel"):TEXT("Pousada"),*String(G,TEXT("name")),Nights,Rate));
  Queue.RemoveAt(Index);OutOffer=Rate;return true;
 };
 if(Price<=Offer)return CheckIn(Price)?EHaggle::Accepted:EHaggle::Invalid;
 if(Price<=Limit){
  // The first ask above the halfway point gets one meet-in-the-middle answer.
  if(Round==0 && Price>(Offer+Limit)/2){G->SetNumberField(TEXT("offer"),FMath::RoundToDouble((Offer+Price)/2));G->SetNumberField(TEXT("round"),1);
   OutOffer=Number(G,TEXT("offer"));return EHaggle::Countered;}
  return CheckIn(Price)?EHaggle::Accepted:EHaggle::Invalid;
 }
 // Over the limit: mood drops with how greedy the ask was; three refusals end the talk.
 const double Mood=Number(G,TEXT("mood"))-(.25+FMath::Clamp((Price-Limit)/Limit,0.,1.));G->SetNumberField(TEXT("mood"),Mood);
 G->SetNumberField(TEXT("round"),Round+1);
 if(Round+1>=3 || Mood<=0){const FString Name=String(G,TEXT("name"));Queue.RemoveAt(Index);OutOffer=0;
  LastMessage=FString::Printf(TEXT("%s foi embora da recepção: achou caro demais."),*Name);return EHaggle::Left;}
 G->SetNumberField(TEXT("offer"),FMath::RoundToDouble(Offer+(Limit-Offer)*.4));OutOffer=Number(G,TEXT("offer"));return EHaggle::Countered;
}
bool UMareSimulation::AcceptOffer(const FString& Guest)
{
 auto G=Find(List(Stays(),TEXT("queue")),Guest);if(!G)return false;double Out=0;
 return Haggle(Guest,Number(G,TEXT("offer")),Out)==EHaggle::Accepted;
}

bool UMareSimulation::CleanRoom(const FString& Room,const FString& Task)
{
 auto R=Find(List(Stays(),TEXT("rooms")),Room);if(!R || String(R,TEXT("state"))!=TEXT("dirty"))return false;
 auto& Tasks=List(R,TEXT("tasks"));const int32 Before=Tasks.Num();
 Tasks.RemoveAll([&](const TSharedPtr<FJsonValue>& V){return V->AsString()==Task;});if(Tasks.Num()==Before)return false;
 if(Tasks.IsEmpty()){R->SetStringField(TEXT("state"),TEXT("free"));R->RemoveField(TEXT("guest"));}
 return true;
}

void UMareSimulation::StaysNight()
{
 SyncRooms();auto Stay=Stays();auto& Rooms=List(Stay,TEXT("rooms"));const double Comfort=PlaceComfort(TEXT("pousada"));
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
 int32 Occupied=0,Left=0;double Revenue=0;
 // Hotel guests who check out tonight walk from the elevators out of the lobby next morning (UMareStaysWorld).
 TArray<TSharedPtr<FJsonValue>> Departures;
 for(const auto& V:Rooms){auto R=V->AsObject();if(String(R,TEXT("state"))!=TEXT("occupied"))continue;
  ++Occupied;Revenue+=Number(R,TEXT("rate"));const int32 Nights=Number(R,TEXT("nights"),1)-1;R->SetNumberField(TEXT("nights"),Nights);
  if(Nights>0)continue;
  // Check-out: comfort and decor, the check-in mood and a clean room decide the stars.
  const bool bHotel=String(R,TEXT("place"))==TEXT("hotel");
  const double Rating=FMath::Clamp((bHotel?3.9+HotelCustomBonus()*4:3.3+.025*Comfort)+1.2*(Number(R,TEXT("mood"))-.5)+(R->HasField(TEXT("was_dirty"))?-1.2:.3),1.,5.);
  Ratings.Add(MakeShared<FJsonValueNumber>(Rating));AddFame(bHotel?2:1);++Left;
  if(bHotel){const auto G=Object(R,TEXT("guest"));
   if(Departures.Num()<8 && !String(G,TEXT("id")).IsEmpty()){auto D=MakeShared<FJsonObject>();
    for(const TCHAR* Key:{TEXT("id"),TEXT("name"),TEXT("profile")})D->SetStringField(Key,String(G,Key));
    D->SetStringField(TEXT("place"),TEXT("hotel"));Departures.Add(MakeShared<FJsonValueObject>(D));}
   R->SetStringField(TEXT("state"),TEXT("free"));R->RemoveField(TEXT("guest"));continue;}   // hotel housekeeping
  R->SetStringField(TEXT("state"),TEXT("dirty"));R->RemoveField(TEXT("was_dirty"));
  TArray<TSharedPtr<FJsonValue>> Tasks;for(const TCHAR* T:{TEXT("bed"),TEXT("towels"),TEXT("trash")})Tasks.Add(MakeShared<FJsonValueString>(T));
  R->SetArrayField(TEXT("tasks"),Tasks);}
 while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);
 // Guests still waiting at the reception give up at night.
 Stay->SetArrayField(TEXT("queue"),TArray<TSharedPtr<FJsonValue>>());
 Stay->SetArrayField(TEXT("departures"),Departures);
 auto Last=MakeShared<FJsonObject>();Last->SetNumberField(TEXT("rooms"),Rooms.Num());Last->SetNumberField(TEXT("occupied"),Occupied);
 Last->SetNumberField(TEXT("rev"),Revenue);Last->SetNumberField(TEXT("checkouts"),Left);Child(State,TEXT("prog"))->SetObjectField(TEXT("pousada"),Last);
}

TSharedPtr<FJsonObject> UMareSimulation::TakeDeparture(const FString& Place)
{
 auto& Departures=List(Stays(),TEXT("departures"));
 for(int32 I=0;I<Departures.Num();++I){const auto D=Departures[I]->AsObject();
  if(D && String(D,TEXT("place"))==Place){Departures.RemoveAt(I);return D;}}
 return nullptr;
}

void UMareSimulation::StaysHour(int32 Hour)
{
 SyncRooms();
 // Check-outs leave in the morning; whoever was not seen walking out by 13:00 is already gone.
 if(Hour>=13)Stays()->SetArrayField(TEXT("departures"),TArray<TSharedPtr<FJsonValue>>());
 for(const TCHAR* Place:{TEXT("pousada"),TEXT("hotel")}){
  const FString P(Place);if(PlaceRooms(this,P)<=0)continue;auto Ops=StayOps(P);const bool bHotel=P==TEXT("hotel");
  // Arrivals 10:00-20:00; demand follows the occupancy models (fame, comfort, beauty, stars).
  if(Hour>=10 && Hour<20){FRandomStream Rng(int32(Number(State,TEXT("day"),1))*24+Hour+(bHotel?7919:0));
   const double Chance=FMath::Clamp((bHotel?HotelOccupancy():PousadaOccupancy())*Number(Ops,TEXT("arrivals_per_room_hour"),.25)*PlaceRooms(this,P),0.,.95);
   const int32 Count=bHotel?FMath::FloorToInt(Chance*3+Rng.FRand()):(Rng.FRand()<Chance?1:0);
   for(int32 I=0;I<Count;++I)AddArrival(P);}
  // Front desk staff: the pousada receptionist at once, the hotel desk after two hours of waiting.
  if((bHotel || HasStaff(String(Ops,TEXT("receptionist")))) && FreeCleanRooms(P)>0){const double Now=Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes"));
   TArray<FString> Ready;const TArray<TSharedPtr<FJsonValue>>* Queue=nullptr;
   if(Stays()->TryGetArrayField(TEXT("queue"),Queue))for(const auto& V:*Queue){const auto G=V->AsObject();
    const FString GP=String(G,TEXT("place")).IsEmpty()?FString(TEXT("pousada")):String(G,TEXT("place"));
    if(GP!=P || (bHotel && Now-Number(G,TEXT("since"),Now)<120))continue;Ready.Add(String(G,TEXT("id")));}
   for(const FString& Id:Ready)if(FreeCleanRooms(P)>0)AcceptOffer(Id);}
 }
 // Maid (pousada): a few cleaning tasks per hour on dirty bungalows.
 auto Ops=StayOps(TEXT("pousada"));
 if(HasStaff(String(Ops,TEXT("maid")))){int32 Budget=FMath::RoundToInt(Number(Ops,TEXT("maid_tasks_per_hour"),3)*StaffSkill(String(Ops,TEXT("maid"))));
  for(const auto& V:List(Stays(),TEXT("rooms"))){auto R=V->AsObject();
   while(Budget>0 && String(R,TEXT("state"))==TEXT("dirty")){const TArray<TSharedPtr<FJsonValue>>* Tasks=nullptr;
    if(!R->TryGetArrayField(TEXT("tasks"),Tasks) || Tasks->IsEmpty())break;
    CleanRoom(String(R,TEXT("id")),(*Tasks)[0]->AsString());--Budget;}}}
}
