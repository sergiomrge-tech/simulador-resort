// Board and kayak rental, hands-on (CHECKLIST_EXPANSOES 3.3): customers rent for 30 or 60 game minutes and come back;
// the returned board is checked (a dent is fined, a fine without a dent annoys); waxing before renting adds a tip; a
// rented kayak can drift off and the player tows it back. Values in business_games.json businesses.aluguel.rental.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 const TCHAR* RentalNames[]={TEXT("Duda"),TEXT("Léo"),TEXT("Iara"),TEXT("Tavinho"),TEXT("Mel"),TEXT("Caio"),TEXT("Soninha"),TEXT("Breno"),TEXT("Lara"),TEXT("Joca")};
 TArray<TSharedPtr<FJsonValue>>& Arr(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  if(!O->HasTypedField<EJson::Array>(Key))O->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
  return const_cast<TArray<TSharedPtr<FJsonValue>>&>(O->GetArrayField(Key));
 }
 double Now(const TSharedPtr<FJsonObject>& State){return UMareSimulation::Number(State,TEXT("day"),1)*1440+UMareSimulation::Number(State,TEXT("minutes"));}
 TArray<TSharedPtr<FJsonObject>> Objects(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  TArray<TSharedPtr<FJsonObject>> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(O->TryGetArrayField(Key,L))for(const auto& V:*L)Out.Add(V->AsObject());return Out;
 }
}

TSharedPtr<FJsonObject> UMareSimulation::RentalDefs() const{return BizGameDefs(TEXT("aluguel"));}
TSharedPtr<FJsonObject> UMareSimulation::RentalState() const{return Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("aluguel"));}
TArray<TSharedPtr<FJsonObject>> UMareSimulation::RentalQueue() const{return Objects(RentalState(),TEXT("queue"));}
TArray<TSharedPtr<FJsonObject>> UMareSimulation::RentalReturns() const{return Objects(RentalState(),TEXT("returns"));}
TArray<TSharedPtr<FJsonObject>> UMareSimulation::RentalOut() const{return Objects(RentalState(),TEXT("rented"));}

FString UMareSimulation::RentalItemName(const FString& Item) const
{
 return String(Object(Object(RentalDefs(),TEXT("items")),Item),TEXT("name"));
}

double UMareSimulation::RentalPrice(const FString& Item,int32 Minutes) const
{
 return FMath::RoundToDouble(Number(Object(Object(RentalDefs(),TEXT("items")),Item),TEXT("price30"),10)*FMath::Max(1,Minutes/30)*BizSaleMult(TEXT("aluguel")));
}

void UMareSimulation::AddRentalCustomer()
{
 const auto D=RentalDefs();auto R=RentalState();auto& Queue=Arr(R,TEXT("queue"));if(Queue.Num()>=int32(Number(D,TEXT("queue_max"),5)))return;
 TArray<FString> Items;for(const auto& Pair:Object(D,TEXT("items"))->Values)Items.Add(FString(Pair.Key.ToView()));if(Items.IsEmpty())return;
 auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("item"),Items[FMath::RandRange(0,Items.Num()-1)]);O->SetNumberField(TEXT("minutes"),FMath::RandBool()?30:60);
 const int32 Next=int32(Number(R,TEXT("next_customer")));R->SetNumberField(TEXT("next_customer"),Next+1);
 O->SetStringField(TEXT("name"),RentalNames[(Next*3+int32(Number(State,TEXT("day"),1)))%UE_ARRAY_COUNT(RentalNames)]);O->SetNumberField(TEXT("since"),Now(State));
 Queue.Add(MakeShared<FJsonValueObject>(O));
}

FString UMareSimulation::RentalRequestLine(const TSharedPtr<FJsonObject>& O) const
{
 return FString::Printf(TEXT("%s quer %s por %.0f min (R$ %.0f)"),*String(O,TEXT("name")),*RentalItemName(String(O,TEXT("item"))),Number(O,TEXT("minutes")),RentalPrice(String(O,TEXT("item")),int32(Number(O,TEXT("minutes")))));
}

void UMareSimulation::RentalHour(int32 Hour)
{
 if(!OwnsBusiness(TEXT("aluguel")))return;const auto D=RentalDefs();auto R=RentalState();const bool bOpen=IsBusinessOpen(TEXT("aluguel"));
 // Whoever waited too long leaves the line; at closing the line goes home.
 auto& Queue=Arr(R,TEXT("queue"));auto& Out=Arr(R,TEXT("rented"));auto& Returns=Arr(R,TEXT("returns"));
 // The clerk (3.6) rents to whoever the player left in line (no wax, clerk_share of the price) and checks the returns
 // (a dent pays clerk_share of the fine), without fame.
 if(HasBizClerk(TEXT("aluguel")) && (Queue.Num() || Returns.Num())){double Sum=0;const int32 N=Queue.Num()+Returns.Num();
  for(const auto& V:Queue){const auto O=V->AsObject();const FString Item=String(O,TEXT("item"));const int32 Minutes=int32(Number(O,TEXT("minutes"),30));
   const double Paid=FMath::RoundToDouble(RentalPrice(Item,Minutes)*BizClerkShare());Sum+=Paid;BizServed(TEXT("aluguel"),true,Paid,0,0);
   auto Rent=MakeShared<FJsonObject>();Rent->SetStringField(TEXT("name"),String(O,TEXT("name")));Rent->SetStringField(TEXT("item"),Item);
   Rent->SetNumberField(TEXT("due"),Now(State)+Minutes);Rent->SetBoolField(TEXT("waxed"),false);Out.Add(MakeShared<FJsonValueObject>(Rent));}
  for(const auto& V:Returns){bool bDent=false;V->AsObject()->TryGetBoolField(TEXT("dent"),bDent);
   const double Paid=bDent?FMath::RoundToDouble(Number(D,TEXT("fine"),20)*BizClerkShare()):0;Sum+=Paid;BizServed(TEXT("aluguel"),true,Paid,0,0);}
  Queue.Empty();Returns.Empty();if(Sum>0)Book(Sum,FString::Printf(TEXT("Aluguel: funcionário atendeu %d cliente(s)"),N));}
 int32 Gone=0;for(int32 I=Queue.Num()-1;I>=0;--I)if(!bOpen || Now(State)-Number(Queue[I]->AsObject(),TEXT("since"))>Number(D,TEXT("patience_minutes"),40)){Queue.RemoveAt(I);++Gone;}
 BizLost(TEXT("aluguel"),Gone);
 // Rentals that ran out come back to be checked (some with a dent); at closing everybody returns.
 for(int32 I=Out.Num()-1;I>=0;--I){const auto O=Out[I]->AsObject();if(bOpen && Now(State)<Number(O,TEXT("due")))continue;
  O->SetBoolField(TEXT("dent"),FMath::FRand()<Number(D,TEXT("dent_chance"),.3));Returns.Add(Out[I]);Out.RemoveAt(I);}
 if(!bOpen)return;
 const TArray<TSharedPtr<FJsonValue>>* Range=nullptr;int32 Lo=1,Hi=2;if(D->TryGetArrayField(TEXT("arrivals"),Range) && Range->Num()==2){Lo=int32((*Range)[0]->AsNumber());Hi=int32((*Range)[1]->AsNumber());}
 double N=FMath::RandRange(Lo,Hi);if(TodayEvent()==TEXT("calor"))N*=Number(D,TEXT("hot_mult"),1.5);if(TodayEvent()==TEXT("mare"))N*=Number(D,TEXT("tide_mult"),1.4);if(String(State,TEXT("weather"))==TEXT("rain"))N*=Number(D,TEXT("rain_mult"),.3);
 const int32 Arrive=FMath::FloorToInt(N)+(FMath::FRand()<FMath::Frac(N)?1:0);for(int32 I=0;I<Arrive;++I)AddRentalCustomer();
 // A rented kayak sometimes drifts off and has to be fetched.
 const bool bKayakOut=Out.ContainsByPredicate([](const TSharedPtr<FJsonValue>& V){return UMareSimulation::String(V->AsObject(),TEXT("item"))==TEXT("caiaque");});
 if(bKayakOut && !IsKayakAdrift() && FMath::FRand()<Number(D,TEXT("adrift_chance"),.25))StartKayakAdrift();
}

bool UMareSimulation::RentItem(bool bWaxed)
{
 auto R=RentalState();auto& Queue=Arr(R,TEXT("queue"));if(Queue.IsEmpty())return Fail(TEXT("Ninguém na fila do aluguel."));
 const auto O=Queue[0]->AsObject();const FString Item=String(O,TEXT("item"));const int32 Minutes=int32(Number(O,TEXT("minutes"),30));
 const double Price=RentalPrice(Item,Minutes),Tip=bWaxed?FMath::RoundToDouble(Price*Number(RentalDefs(),TEXT("wax_tip"),.3)):0;
 Book(Price+Tip,FString::Printf(TEXT("Aluguel: %s por %d min%s"),*RentalItemName(Item),Minutes,bWaxed?TEXT(" (encerada)"):TEXT("")));AddFame(bWaxed?2:1);
 BizServed(TEXT("aluguel"),false,Price+Tip,bWaxed?3:2,bWaxed?2:1);
 auto Rent=MakeShared<FJsonObject>();Rent->SetStringField(TEXT("name"),String(O,TEXT("name")));Rent->SetStringField(TEXT("item"),Item);
 Rent->SetNumberField(TEXT("due"),Now(State)+Minutes);Rent->SetBoolField(TEXT("waxed"),bWaxed);Arr(R,TEXT("rented")).Add(MakeShared<FJsonValueObject>(Rent));
 Queue.RemoveAt(0);R->SetNumberField(TEXT("games"),Number(R,TEXT("games"))+1);
 LastMessage=FString::Printf(TEXT("%s levou %s por %d min: R$ %.0f"),*String(O,TEXT("name")),*RentalItemName(Item),Minutes,Price+Tip)
  +(bWaxed?FString::Printf(TEXT(" (gorjeta R$ %.0f pela parafina)."),Tip):FString(TEXT(".")));
 return Save();
}

int32 UMareSimulation::InspectReturn(bool bFine)
{
 // 3 = right call on a dent (fine paid), 2 = right call on a clean board, 1 = dent let go, 0 = clean board fined.
 auto R=RentalState();auto& Returns=Arr(R,TEXT("returns"));if(Returns.IsEmpty()){Fail(TEXT("Nada para conferir."));return -1;}
 const auto O=Returns[0]->AsObject();bool bDent=false;O->TryGetBoolField(TEXT("dent"),bDent);Returns.RemoveAt(0);
 const FString Who=String(O,TEXT("name")),What=RentalItemName(String(O,TEXT("item")));const double Fine=Number(RentalDefs(),TEXT("fine"),20);int32 Result=0;
 if(bDent && bFine){Book(Fine,FString::Printf(TEXT("Aluguel: multa por %s amassado(a)"),*What));LastMessage=FString::Printf(TEXT("%s pagou R$ %.0f de multa pelo amassado."),*Who,Fine);Result=3;}
 else if(!bDent && !bFine){AddFame(1);LastMessage=FString::Printf(TEXT("%s devolveu %s inteiro(a). Tudo certo!"),*Who,*What);Result=2;}
 else if(bDent){LastMessage=FString::Printf(TEXT("Deixou passar: %s voltou amassado(a) e ficou por isso mesmo."),*What);Result=1;}
 else{AddFame(-int32(Number(RentalDefs(),TEXT("unfair_fame"),2)));LastMessage=FString::Printf(TEXT("%s reclamou: multa sem amassado nenhum! A fama caiu."),*Who);Result=0;}
 BizServed(TEXT("aluguel"),false,Result==3?Fine:0,Result,Result==2?1:Result==0?-int32(Number(RentalDefs(),TEXT("unfair_fame"),2)):0);
 Save();return Result;
}

bool UMareSimulation::IsKayakAdrift() const{bool b=false;Object(RentalState(),TEXT("adrift"))->TryGetBoolField(TEXT("active"),b);return b;}
void UMareSimulation::StartKayakAdrift()
{
 auto A=Object(RentalState(),TEXT("adrift"));A->SetBoolField(TEXT("active"),true);A->SetNumberField(TEXT("since"),Now(State));
 LastMessage=TEXT("Um caiaque alugado está à deriva no mar! Nade até ele e reboque de volta (E).");
}
double UMareSimulation::RescueKayak()
{
 if(!IsKayakAdrift()){Fail(TEXT("Nenhum caiaque à deriva."));return 0;}
 Object(RentalState(),TEXT("adrift"))->SetBoolField(TEXT("active"),false);const double Reward=Number(RentalDefs(),TEXT("rescue_reward"),30);
 Book(Reward,TEXT("Aluguel: caiaque resgatado"));AddFame(3);LastMessage=FString::Printf(TEXT("Caiaque de volta à praia! O cliente agradeceu: R$ %.0f."),Reward);Save();return Reward;
}
