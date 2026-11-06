// Grand Hotel rooms (CHECKLIST 5.1): three kinds of room, check-out leaves the room dirty with the minibar to restock
// (the minibar bill is charged at check-out), the housekeeping crew cleans by the hour, and guests phone in complaints
// with a deadline. Values in Content/Data/hotel_rooms.json; the room list itself lives in the save (state "stays").
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
 const TArray<TSharedPtr<FJsonValue>>& Array(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  static const TArray<TSharedPtr<FJsonValue>> Empty;const TArray<TSharedPtr<FJsonValue>>* Found=nullptr;
  return O.IsValid() && O->TryGetArrayField(Key,Found)?*Found:Empty;
 }
}

TSharedPtr<FJsonObject> UMareSimulation::HotelRoomDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/hotel_rooms.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

FString UMareSimulation::HotelRoomKind(int32 Index) const
{
 // The visitable 3rd floor comes first (301 suite, 302 standard, 303 luxury); the rest fills the kinds in order.
 const auto& Visitable=Array(HotelRoomDefs(),TEXT("visitable"));
 if(Visitable.IsValidIndex(Index))return Visitable[Index]->AsString();
 int32 Left=Index-Visitable.Num();
 for(const auto& V:Array(HotelRoomDefs(),TEXT("kinds"))){const auto K=V->AsObject();const FString Id=String(K,TEXT("id"));
  int32 Count=Number(K,TEXT("count"));for(const auto& Seen:Visitable)Count-=Seen->AsString()==Id;
  if(Left<Count)return Id;Left-=FMath::Max(0,Count);}
 return TEXT("standard");
}
TSharedPtr<FJsonObject> UMareSimulation::HotelKindDef(const FString& Kind) const
{
 for(const auto& V:Array(HotelRoomDefs(),TEXT("kinds")))if(String(V->AsObject(),TEXT("id"))==Kind)return V->AsObject();
 return MakeShared<FJsonObject>();
}
int32 UMareSimulation::HotelRoomNumber(int32 Index){return (3+Index/8)*100+Index%8+1;}
TSharedPtr<FJsonObject> UMareSimulation::HotelRoom(int32 Index)
{
 const FString Id=FString::Printf(TEXT("hotel_%d"),Index);
 for(const auto& V:List(Stays(),TEXT("rooms")))if(String(V->AsObject(),TEXT("id"))==Id)return V->AsObject();
 return nullptr;
}
int32 UMareSimulation::HotelRoomIndex(const TSharedPtr<FJsonObject>& Room)
{
 FString Id=String(Room,TEXT("id"));return Id.RemoveFromStart(TEXT("hotel_"))?FCString::Atoi(*Id):INDEX_NONE;
}
FString UMareSimulation::HotelRoomName(int32 Index) const
{
 return FString::Printf(TEXT("%s %d"),*String(HotelKindDef(HotelRoomKind(Index)),TEXT("label")),HotelRoomNumber(Index));
}
int32 UMareSimulation::HotelRoomsIn(const FString& RoomState) const
{
 int32 Count=0;const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;
 if(Object(State,TEXT("stays"))->TryGetArrayField(TEXT("rooms"),Rooms))for(const auto& V:*Rooms)
  Count+=String(V->AsObject(),TEXT("place"))==TEXT("hotel") && String(V->AsObject(),TEXT("state"))==RoomState;
 return Count;
}
FString UMareSimulation::HotelTaskLabel(const FString& Task) const
{
 const FString Label=String(Object(HotelRoomDefs(),TEXT("task_labels")),Task);return Label.IsEmpty()?Task:Label;
}
FString UMareSimulation::HotelTaskDone(const FString& Task) const
{
 const FString Done=String(Object(HotelRoomDefs(),TEXT("task_done")),Task);return Done.IsEmpty()?Task:Done;
}
FString UMareSimulation::HotelProfileKind(const FString& Profile) const
{
 const FString Kind=String(Object(HotelRoomDefs(),TEXT("profile_kind")),Profile);return Kind.IsEmpty()?FString(TEXT("standard")):Kind;
}

double UMareSimulation::HotelCheckOut(const TSharedPtr<FJsonObject>& Room)
{
 // The minibar: what the guest took is on the bill (only if it was stocked), and has to be restocked by housekeeping.
 const int32 Index=HotelRoomIndex(Room);const auto Defs=HotelRoomDefs();double Bill=0;
 TArray<TSharedPtr<FJsonValue>> Taken;
 if(!Room->HasField(TEXT("minibar_empty"))){
  FRandomStream Rng(int32(Number(State,TEXT("day"),1))*613+Index*37+11);const auto& Items=Array(Defs,TEXT("minibar"));
  const int32 Count=Items.Num()?Rng.RandRange(0,int32(Number(Defs,TEXT("minibar_take_max"),4))):0;
  for(int32 I=0;I<Count;++I){const auto Item=Items[Rng.RandRange(0,Items.Num()-1)]->AsObject();Bill+=Number(Item,TEXT("price"));
   Taken.Add(MakeShared<FJsonValueString>(String(Item,TEXT("id"))));}}
 if(Bill>0)Book(Bill,FString::Printf(TEXT("Grand Hotel: frigobar do quarto %d"),HotelRoomNumber(Index)));
 Room->SetStringField(TEXT("state"),TEXT("dirty"));Room->RemoveField(TEXT("guest"));Room->RemoveField(TEXT("polished"));
 Room->RemoveField(TEXT("minibar_empty"));Room->SetArrayField(TEXT("minibar_taken"),Taken);
 TArray<TSharedPtr<FJsonValue>> Tasks;
 for(const auto& T:Array(Defs,TEXT("tasks")))if(T->AsString()!=TEXT("minibar") || Taken.Num())Tasks.Add(T);
 Room->SetArrayField(TEXT("tasks"),Tasks);
 // A complaint still open leaves with the guest.
 List(Stays(),TEXT("complaints")).RemoveAll([&](const TSharedPtr<FJsonValue>& V){return int32(Number(V->AsObject(),TEXT("room"),-1))==Index;});
 auto Prog=Child(Child(State,TEXT("prog")),TEXT("hotel_rooms"));Prog->SetNumberField(TEXT("minibar"),Number(Prog,TEXT("minibar"))+Bill);
 return Bill;
}

double UMareSimulation::HotelMinibarCost(const TSharedPtr<FJsonObject>& Room) const
{
 double Cost=0;
 for(const auto& T:Array(Room,TEXT("minibar_taken")))for(const auto& V:Array(HotelRoomDefs(),TEXT("minibar")))
  if(String(V->AsObject(),TEXT("id"))==T->AsString()){Cost+=Number(V->AsObject(),TEXT("cost"));break;}
 return Cost;
}

bool UMareSimulation::CleanHotelRoom(int32 Index,const FString& Task,bool bByHand)
{
 auto R=HotelRoom(Index);if(!R || String(R,TEXT("state"))!=TEXT("dirty"))return false;
 const auto& Tasks=Array(R,TEXT("tasks"));if(!Tasks.ContainsByPredicate([&](const TSharedPtr<FJsonValue>& V){return V->AsString()==Task;}))return false;
 // Restocking pays the supplier for what the last guest took.
 if(Task==TEXT("minibar")){const double Cost=HotelMinibarCost(R);if(Cost>0){if(Money()<Cost){LastMessage=FString::Printf(TEXT("Sem caixa para repor o frigobar (R$ %.0f)."),Cost);return false;}
   Book(-Cost,FString::Printf(TEXT("Grand Hotel: reposição do frigobar do %d"),HotelRoomNumber(Index)));}
  R->RemoveField(TEXT("minibar_taken"));}
 // Count the hand-made tasks: a room the player finishes alone (no crew help) is "polished".
 if(bByHand)R->SetNumberField(TEXT("hand_tasks"),Number(R,TEXT("hand_tasks"))+1);else R->SetBoolField(TEXT("crew_helped"),true);
 const bool bLast=Tasks.Num()==1;
 if(!CleanRoom(R->GetStringField(TEXT("id")),Task))return false;
 if(bLast){bool bHelped=false;R->TryGetBoolField(TEXT("crew_helped"),bHelped);
  if(!bHelped && Number(R,TEXT("hand_tasks"))>0)R->SetBoolField(TEXT("polished"),true);
  R->RemoveField(TEXT("hand_tasks"));R->RemoveField(TEXT("crew_helped"));}
 return true;
}

TArray<TSharedPtr<FJsonObject>> UMareSimulation::HotelComplaints()
{
 TArray<TSharedPtr<FJsonObject>> Out;for(const auto& V:List(Stays(),TEXT("complaints")))Out.Add(V->AsObject());return Out;
}
TSharedPtr<FJsonObject> UMareSimulation::ComplaintKind(const FString& Kind) const
{
 for(const auto& V:Array(Object(HotelRoomDefs(),TEXT("complaints")),TEXT("kinds")))if(String(V->AsObject(),TEXT("id"))==Kind)return V->AsObject();
 return MakeShared<FJsonObject>();
}
double UMareSimulation::ComplaintMinutesLeft(const TSharedPtr<FJsonObject>& Complaint) const
{
 return Number(Complaint,TEXT("due"))-(Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes")));
}
FString UMareSimulation::AddHotelComplaint(int32 Index,const FString& Kind)
{
 auto R=HotelRoom(Index);if(!R || String(R,TEXT("state"))!=TEXT("occupied"))return FString();
 auto& Open=List(Stays(),TEXT("complaints"));
 for(const auto& V:Open)if(int32(Number(V->AsObject(),TEXT("room"),-1))==Index)return FString();
 const auto Def=ComplaintKind(Kind);if(!Def->HasField(TEXT("id")))return FString();
 auto Stay=Stays();const int32 Serial=Number(Stay,TEXT("complaint_serial"));Stay->SetNumberField(TEXT("complaint_serial"),Serial+1);
 const double Now=Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes"));
 auto C=MakeShared<FJsonObject>();C->SetStringField(TEXT("id"),FString::Printf(TEXT("c%d"),Serial));C->SetNumberField(TEXT("room"),Index);
 C->SetStringField(TEXT("kind"),Kind);C->SetNumberField(TEXT("since"),Now);C->SetNumberField(TEXT("due"),Now+Number(Def,TEXT("minutes"),60));
 Open.Add(MakeShared<FJsonValueObject>(C));
 LastMessage=FString::Printf(TEXT("Telefone: %s, %s (%.0f min para resolver)."),*HotelRoomName(Index),*String(Def,TEXT("label")),Number(Def,TEXT("minutes"),60));
 return String(C,TEXT("id"));
}
bool UMareSimulation::SolveHotelComplaint(const FString& Id,bool bInPerson)
{
 auto& Open=List(Stays(),TEXT("complaints"));int32 At=INDEX_NONE;
 for(int32 I=0;I<Open.Num();++I)if(String(Open[I]->AsObject(),TEXT("id"))==Id)At=I;
 if(At==INDEX_NONE)return false;const auto C=Open[At]->AsObject();const auto Def=ComplaintKind(String(C,TEXT("kind")));
 const int32 Index=Number(C,TEXT("room"),-1);
 if(!bInPerson){const double Cost=Number(Def,TEXT("cost"));if(Money()<Cost){LastMessage=TEXT("Sem caixa para mandar o técnico.");return false;}
  if(Cost>0)Book(-Cost,FString::Printf(TEXT("Grand Hotel: técnico no quarto %d"),HotelRoomNumber(Index)));}
 if(auto R=HotelRoom(Index))R->SetNumberField(TEXT("mood"),FMath::Clamp(Number(R,TEXT("mood"),.5)+Number(Object(HotelRoomDefs(),TEXT("complaints")),TEXT("solved_mood"),.08),0.,1.));
 if(bInPerson)AddFame(1);
 auto Prog=Child(Child(State,TEXT("prog")),TEXT("hotel_rooms"));Prog->SetNumberField(TEXT("solved"),Number(Prog,TEXT("solved"))+1);
 LastMessage=FString::Printf(TEXT("%s: %s resolvido%s."),*HotelRoomName(Index),*String(Def,TEXT("label")).ToLower(),bInPerson?TEXT(" por você"):TEXT(" pelo técnico"));
 Open.RemoveAt(At);return true;
}
int32 UMareSimulation::ExpireHotelComplaints()
{
 auto& Open=List(Stays(),TEXT("complaints"));int32 Failed=0;const double Penalty=Number(Object(HotelRoomDefs(),TEXT("complaints")),TEXT("failed_mood"),.4);
 for(int32 I=Open.Num()-1;I>=0;--I){const auto C=Open[I]->AsObject();if(ComplaintMinutesLeft(C)>0)continue;
  const int32 Index=Number(C,TEXT("room"),-1);
  if(auto R=HotelRoom(Index)){R->SetNumberField(TEXT("mood"),FMath::Clamp(Number(R,TEXT("mood"),.5)-Penalty,0.,1.));R->SetBoolField(TEXT("complained"),true);}
  LastMessage=FString::Printf(TEXT("%s cansou de esperar: \"%s\" vai para a avaliação."),*HotelRoomName(Index),*String(ComplaintKind(String(C,TEXT("kind"))),TEXT("label")));
  auto Prog=Child(Child(State,TEXT("prog")),TEXT("hotel_rooms"));Prog->SetNumberField(TEXT("failed"),Number(Prog,TEXT("failed"))+1);
  Open.RemoveAt(I);++Failed;}
 return Failed;
}

void UMareSimulation::HotelRoomsHour(int32 Hour)
{
 bool bHotel=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);if(!bHotel)return;
 const auto Defs=HotelRoomDefs();const auto Crew=Object(Defs,TEXT("crew"));const int32 Visitable=Array(Defs,TEXT("visitable")).Num();
 ExpireHotelComplaints();
 // Housekeeping crew (paid in the hotel's nightly staff cost): the rooms nobody sees first, the visitable floor late
 // in the morning so the player can do those by hand.
 if(Hour>=Number(Crew,TEXT("from"),8) && Hour<Number(Crew,TEXT("to"),18)){int32 Budget=Number(Crew,TEXT("tasks_per_hour"),8);
  const bool bVisitable=Hour>=Number(Crew,TEXT("visitable_after"),11);
  TArray<int32> Order;for(int32 I=Visitable;I<32;++I)Order.Add(I);if(bVisitable)for(int32 I=0;I<Visitable;++I)Order.Add(I);
  for(const int32 I:Order){auto R=HotelRoom(I);
   while(Budget>0 && R && String(R,TEXT("state"))==TEXT("dirty")){const auto& Tasks=Array(R,TEXT("tasks"));if(Tasks.IsEmpty())break;
    const FString Task=Tasks[0]->AsString();if(!CleanHotelRoom(I,Task,false)){break;}--Budget;}}}
 // New complaints by phone: one per hour at most, only from occupied rooms.
 const auto Rules=Object(Defs,TEXT("complaints"));
 if(Hour>=Number(Rules,TEXT("from"),8) && Hour<Number(Rules,TEXT("to"),22) && List(Stays(),TEXT("complaints")).Num()<Number(Rules,TEXT("max_open"),3)){
  FRandomStream Rng(int32(Number(State,TEXT("day"),1))*24+Hour+31337);const auto& Kinds=Array(Rules,TEXT("kinds"));
  for(int32 I=0;I<32 && Kinds.Num();++I){auto R=HotelRoom(I);if(!R || String(R,TEXT("state"))!=TEXT("occupied"))continue;
   if(Rng.FRand()<Number(Rules,TEXT("chance_per_room_hour"),.012)){
    if(!AddHotelComplaint(I,String(Kinds[Rng.RandRange(0,Kinds.Num()-1)]->AsObject(),TEXT("id"))).IsEmpty())break;}}}
}
