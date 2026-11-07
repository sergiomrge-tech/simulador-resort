// Grand Hotel events with set-up (CHECKLIST_EXPANSOES 5.2): beach wedding, birthday party and congress. An offer reaches
// the phone, the player books it for the next day, sets the pieces up from the plan on the beach (UMareHotelEventsWorld)
// and is paid by how much of it was ready when the guests arrive. Values in Content/Data/hotel_events.json.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 TSharedPtr<FJsonObject> EvChild(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  const TSharedPtr<FJsonObject>* Found=nullptr;if(Parent->TryGetObjectField(Key,Found))return *Found;
  auto Created=MakeShared<FJsonObject>();Parent->SetObjectField(Key,Created);return Created;
 }
 TArray<TSharedPtr<FJsonValue>> Bools(int32 N){TArray<TSharedPtr<FJsonValue>> L;for(int32 I=0;I<N;++I)L.Add(MakeShared<FJsonValueBoolean>(false));return L;}
}

TSharedPtr<FJsonObject> UMareSimulation::HotelEventDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/hotel_events.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

TSharedPtr<FJsonObject> UMareSimulation::HotelEventState(){return EvChild(State,TEXT("hotel_events"));}
TSharedPtr<FJsonObject> UMareSimulation::HotelEventKind(const FString& Kind) const{return Object(Object(HotelEventDefs(),TEXT("kinds")),Kind);}

FString UMareSimulation::OfferHotelEvent(const FString& Force)
{
 auto E=HotelEventState();if(E->HasField(TEXT("offer")) || E->HasField(TEXT("booked")))return FString();
 TArray<FString> Kinds;for(const auto& Pair:Object(HotelEventDefs(),TEXT("kinds"))->Values)Kinds.Add(FString(Pair.Key.ToView()));if(Kinds.IsEmpty())return FString();
 const FString Kind=Force.IsEmpty()?Kinds[FMath::RandRange(0,Kinds.Num()-1)]:Force;const auto Def=HotelEventKind(Kind);if(!Def->HasField(TEXT("name")))return FString();
 const TArray<TSharedPtr<FJsonValue>>* Clients=nullptr;FString Client=String(Def,TEXT("name"));
 if(Def->TryGetArrayField(TEXT("client"),Clients) && Clients->Num())Client=(*Clients)[FMath::RandRange(0,Clients->Num()-1)]->AsString();
 auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("kind"),Kind);O->SetStringField(TEXT("client"),Client);
 O->SetNumberField(TEXT("fee"),Number(Def,TEXT("fee")));O->SetNumberField(TEXT("day"),Number(State,TEXT("day"),1));
 E->SetObjectField(TEXT("offer"),O);
 LastMessage=FString::Printf(TEXT("Pedido de evento no Grand Hotel: %s (%s), amanhã às %.0fh, R$ %.0f. Aceite no celular (Resort) ou na recepção do hotel."),
  *String(Def,TEXT("name")),*Client,Number(Def,TEXT("hour"),16),Number(Def,TEXT("fee")));
 return Kind;
}

bool UMareSimulation::AcceptHotelEvent()
{
 auto E=HotelEventState();const TSharedPtr<FJsonObject>* Offer=nullptr;if(!E->TryGetObjectField(TEXT("offer"),Offer))return Fail(TEXT("Nenhum pedido de evento."));
 const auto O=*Offer;const FString Kind=String(O,TEXT("kind"));const auto Def=HotelEventKind(Kind);
 auto B=MakeShared<FJsonObject>();for(const auto& Pair:O->Values)B->SetField(FString(Pair.Key.ToView()),Pair.Value);
 B->SetNumberField(TEXT("day"),Number(State,TEXT("day"),1)+1);B->SetNumberField(TEXT("hour"),Number(Def,TEXT("hour"),16));B->SetStringField(TEXT("state"),TEXT("booked"));
 B->SetArrayField(TEXT("placed"),Bools(Def->GetArrayField(TEXT("pieces")).Num()));B->SetArrayField(TEXT("extras"),Bools(Def->HasField(TEXT("extras"))?Def->GetArrayField(TEXT("extras")).Num():0));
 E->SetObjectField(TEXT("booked"),B);E->RemoveField(TEXT("offer"));
 LastMessage=FString::Printf(TEXT("%s marcado para amanhã às %.0fh. A partir das %.0fh a planta aparece na praia a leste do hotel, perto do farol: monte cada peça com E."),
  *String(Def,TEXT("name")),Number(Def,TEXT("hour"),16),Number(HotelEventDefs(),TEXT("setup_from"),6));
 return Save();
}

bool UMareSimulation::DeclineHotelEvent(){auto E=HotelEventState();if(!E->HasField(TEXT("offer")))return false;E->RemoveField(TEXT("offer"));LastMessage=TEXT("Pedido de evento recusado.");return Save();}

TSharedPtr<FJsonObject> UMareSimulation::BookedHotelEvent() const
{
 const TSharedPtr<FJsonObject>* B=nullptr;return Object(State,TEXT("hotel_events"))->TryGetObjectField(TEXT("booked"),B)?*B:nullptr;
}

bool UMareSimulation::HotelEventSetupOpen() const
{
 const auto B=BookedHotelEvent();if(!B || String(B,TEXT("state"))!=TEXT("booked"))return false;
 const double Now=Number(State,TEXT("minutes"));
 return int32(Number(State,TEXT("day"),1))==int32(Number(B,TEXT("day"))) && Now>=Number(HotelEventDefs(),TEXT("setup_from"),6)*60 && Now<Number(B,TEXT("hour"))*60;
}

int32 UMareSimulation::HotelEventCount(bool bExtra,bool bPlacedOnly) const
{
 const auto B=BookedHotelEvent();if(!B)return 0;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(!B->TryGetArrayField(bExtra?TEXT("extras"):TEXT("placed"),L))return 0;
 int32 N=0;for(const auto& V:*L)N+=!bPlacedOnly || V->AsBool();return N;
}

bool UMareSimulation::PlaceHotelEventPiece(bool bExtra,int32 Index)
{
 auto B=BookedHotelEvent();if(!B)return Fail(TEXT("Nenhum evento marcado."));
 if(!HotelEventSetupOpen())return Fail(TEXT("A montagem é no dia do evento, antes dos convidados chegarem."));
 TArray<TSharedPtr<FJsonValue>> L=B->GetArrayField(bExtra?TEXT("extras"):TEXT("placed"));if(!L.IsValidIndex(Index) || L[Index]->AsBool())return false;
 L[Index]=MakeShared<FJsonValueBoolean>(true);B->SetArrayField(bExtra?TEXT("extras"):TEXT("placed"),L);
 const auto Def=HotelEventKind(String(B,TEXT("kind")));const auto Piece=Def->GetArrayField(bExtra?TEXT("extras"):TEXT("pieces"))[Index]->AsObject();
 LastMessage=FString::Printf(TEXT("Montado: %s. Peças: %d de %d%s."),*String(Piece,TEXT("label")),HotelEventCount(false,true),HotelEventCount(false,false),
  HotelEventCount(true,false)?*FString::Printf(TEXT(" · capricho: %d de %d"),HotelEventCount(true,true),HotelEventCount(true,false)):TEXT(""));
 return Save();
}

double UMareSimulation::StartHotelEvent()
{
 auto B=BookedHotelEvent();if(!B || String(B,TEXT("state"))!=TEXT("booked"))return 0;const auto D=HotelEventDefs();const auto Def=HotelEventKind(String(B,TEXT("kind")));
 const int32 Pieces=FMath::Max(1,HotelEventCount(false,false)),Placed=HotelEventCount(false,true),Extras=HotelEventCount(true,true);
 const double Score=double(Placed)/Pieces;const double Bonus=Number(D,TEXT("extra_bonus"),.1)*Extras;double Paid=0;
 if(Score>=Number(D,TEXT("min_score"),.5)){Paid=FMath::RoundToDouble(Number(B,TEXT("fee"))*Score*(1+Bonus));AddFame(FMath::RoundToInt(Number(Def,TEXT("fame"),6)*Score*(1+Bonus)));
  Book(Paid,FString::Printf(TEXT("Grand Hotel: %s"),*String(Def,TEXT("name"))));
  LastMessage=Score>=1?FString::Printf(TEXT("%s: tudo pronto quando os convidados chegaram! R$ %.0f%s."),*String(B,TEXT("client")),Paid,Extras?TEXT(" (e elogiaram o capricho)"):TEXT(""))
   :FString::Printf(TEXT("%s começou com %d de %d peças: R$ %.0f."),*String(Def,TEXT("name")),Placed,Pieces,Paid);}
 else{Paid=FMath::RoundToDouble(Number(B,TEXT("fee"))*.2);Book(Paid,FString::Printf(TEXT("Grand Hotel: sinal do %s"),*String(Def,TEXT("name"))));
  AddFame(-int32(Number(D,TEXT("flop_fame"),4)));
  LastMessage=FString::Printf(TEXT("%s: os convidados chegaram e quase nada estava montado (%d de %d). Ficou só o sinal, R$ %.0f, e a fama caiu."),*String(Def,TEXT("name")),Placed,Pieces,Paid);}
 B->SetStringField(TEXT("state"),TEXT("show"));B->SetNumberField(TEXT("score"),Score);B->SetNumberField(TEXT("paid"),Paid);
 auto Prog=EvChild(EvChild(State,TEXT("prog")),TEXT("hotel_events"));Prog->SetNumberField(TEXT("done"),Number(Prog,TEXT("done"))+1);
 Prog->SetNumberField(TEXT("earned"),Number(Prog,TEXT("earned"))+Paid);
 Save();return Paid;
}

void UMareSimulation::HotelEventsHour(int32 Hour)
{
 bool bHotel=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);if(!bHotel)return;
 auto E=HotelEventState();const auto D=HotelEventDefs();const int32 Day=int32(Number(State,TEXT("day"),1));
 // An offer not taken is gone the next day.
 const TSharedPtr<FJsonObject>* Offer=nullptr;if(E->TryGetObjectField(TEXT("offer"),Offer) && int32(Number(*Offer,TEXT("day")))<Day)E->RemoveField(TEXT("offer"));
 if(Hour==int32(Number(D,TEXT("offer_hour"),9)) && Day%FMath::Max(1,int32(Number(D,TEXT("offer_every_days"),2)))==0)OfferHotelEvent();
 auto B=BookedHotelEvent();if(!B)return;const int32 EvDay=int32(Number(B,TEXT("day"))),EvHour=int32(Number(B,TEXT("hour")));
 if(String(B,TEXT("state"))==TEXT("booked") && (Day>EvDay || (Day==EvDay && Hour>=EvHour)))StartHotelEvent();
 // The party ends: the area is cleared (UMareHotelEventsWorld removes the pieces and the guests).
 if(String(B,TEXT("state"))==TEXT("show") && (Day>EvDay || Hour>=EvHour+int32(Number(D,TEXT("show_hours"),2)))){E->SetObjectField(TEXT("last"),B);E->RemoveField(TEXT("booked"));Save();}
}
