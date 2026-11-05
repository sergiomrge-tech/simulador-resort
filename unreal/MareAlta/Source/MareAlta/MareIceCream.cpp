// Ice cream shop, hands-on (CHECKLIST_EXPANSOES 3.1): a queue of customers at the Gelato da Maré counter, each with a
// cone to build from memory (flavours, scoop size, topping), more of them on a hot day; the shop also fills the pool
// cooler with homemade popsicles. Values in Content/Data/business_games.json businesses.sorveteria.icecream.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 const TCHAR* IceNames[]={TEXT("Lia"),TEXT("Davi"),TEXT("Dona Cida"),TEXT("Caio"),TEXT("Bruna"),TEXT("Seu Tonho"),TEXT("Maya"),TEXT("Rafa"),TEXT("Júlia"),TEXT("Pedrinho"),TEXT("Nina"),TEXT("Téo")};
 TArray<TSharedPtr<FJsonValue>>& Arr(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  if(!O->HasTypedField<EJson::Array>(Key))O->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
  return const_cast<TArray<TSharedPtr<FJsonValue>>&>(O->GetArrayField(Key));
 }
 double Now(const TSharedPtr<FJsonObject>& State){return UMareSimulation::Number(State,TEXT("day"),1)*1440+UMareSimulation::Number(State,TEXT("minutes"));}
}

TSharedPtr<FJsonObject> UMareSimulation::IceDefs() const
{
 return Object(Object(Object(BusinessGames(),TEXT("businesses")),TEXT("sorveteria")),TEXT("icecream"));
}

TArray<TSharedPtr<FJsonObject>> UMareSimulation::IceQueue() const
{
 TArray<TSharedPtr<FJsonObject>> Out;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"))->TryGetArrayField(TEXT("queue"),List))for(const auto& V:*List)Out.Add(V->AsObject());
 return Out;
}

FString UMareSimulation::IceOrderLine(const TSharedPtr<FJsonObject>& Order) const
{
 const auto D=IceDefs();auto Name=[&](const FString& List,const FString& Id){const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
  if(D->TryGetArrayField(List,L))for(const auto& V:*L)if(String(V->AsObject(),TEXT("id"))==Id)return String(V->AsObject(),TEXT("name"));return Id;};
 TArray<FString> Flavors;const TArray<TSharedPtr<FJsonValue>>* F=nullptr;
 if(Order.IsValid() && Order->TryGetArrayField(TEXT("flavors"),F))for(const auto& V:*F)Flavors.Add(Name(TEXT("flavors"),V->AsString()));
 return FString::Printf(TEXT("%d %s: %s · %s"),Flavors.Num(),Flavors.Num()==1?TEXT("bola"):TEXT("bolas"),*FString::Join(Flavors,TEXT(" + ")),*Name(TEXT("toppings"),String(Order,TEXT("topping"))));
}

void UMareSimulation::AddIceCustomer()
{
 const auto D=IceDefs();auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"));auto& Queue=Arr(Biz,TEXT("queue"));
 if(Queue.Num()>=int32(Number(D,TEXT("queue_max"),6)))return;
 const TArray<TSharedPtr<FJsonValue>>* Flavors=nullptr;const TArray<TSharedPtr<FJsonValue>>* Toppings=nullptr;const TArray<TSharedPtr<FJsonValue>>* Range=nullptr;
 if(!D->TryGetArrayField(TEXT("flavors"),Flavors) || !D->TryGetArrayField(TEXT("toppings"),Toppings) || Flavors->IsEmpty() || Toppings->IsEmpty())return;
 int32 Lo=1,Hi=3;if(D->TryGetArrayField(TEXT("scoops"),Range) && Range->Num()==2){Lo=int32((*Range)[0]->AsNumber());Hi=int32((*Range)[1]->AsNumber());}
 auto O=MakeShared<FJsonObject>();const int32 N=FMath::RandRange(Lo,Hi);TArray<TSharedPtr<FJsonValue>> Pick;
 for(int32 I=0;I<N;++I)Pick.Add(MakeShared<FJsonValueString>(String((*Flavors)[FMath::RandRange(0,Flavors->Num()-1)]->AsObject(),TEXT("id"))));
 O->SetArrayField(TEXT("flavors"),Pick);O->SetStringField(TEXT("topping"),String((*Toppings)[FMath::RandRange(0,Toppings->Num()-1)]->AsObject(),TEXT("id")));
 const int32 Next=int32(Number(Biz,TEXT("next_customer")));Biz->SetNumberField(TEXT("next_customer"),Next+1);
 O->SetStringField(TEXT("name"),IceNames[(Next*7+int32(Number(State,TEXT("day"),1)))%UE_ARRAY_COUNT(IceNames)]);O->SetNumberField(TEXT("since"),Now(State));
 Queue.Add(MakeShared<FJsonValueObject>(O));
}

void UMareSimulation::IceCreamHour(int32 Hour)
{
 if(!OwnsBusiness(TEXT("sorveteria")))return;const auto D=IceDefs();auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"));
 // Whoever waited too long gives up; nobody stays after closing.
 auto& Queue=Arr(Biz,TEXT("queue"));const double Patience=Number(D,TEXT("patience_minutes"),45);int32 Gone=0;
 for(int32 I=Queue.Num()-1;I>=0;--I)if(!IsBusinessOpen(TEXT("sorveteria")) || Now(State)-Number(Queue[I]->AsObject(),TEXT("since"))>Patience){Queue.RemoveAt(I);++Gone;}
 if(Gone && IsBusinessOpen(TEXT("sorveteria")))LastMessage=FString::Printf(TEXT("Sorveteria: %d cliente(s) cansaram de esperar na fila."),Gone);
 if(!IsBusinessOpen(TEXT("sorveteria")))return;
 // New customers: a hot day doubles them, rain keeps most away.
 const TArray<TSharedPtr<FJsonValue>>* Range=nullptr;int32 Lo=1,Hi=2;if(D->TryGetArrayField(TEXT("arrivals"),Range) && Range->Num()==2){Lo=int32((*Range)[0]->AsNumber());Hi=int32((*Range)[1]->AsNumber());}
 double N=FMath::RandRange(Lo,Hi);if(TodayEvent()==TEXT("calor"))N*=Number(D,TEXT("hot_mult"),2);if(String(State,TEXT("weather"))==TEXT("rain"))N*=Number(D,TEXT("rain_mult"),.4);
 const int32 Arrive=FMath::FloorToInt(N)+(FMath::FRand()<FMath::Frac(N)?1:0);for(int32 I=0;I<Arrive;++I)AddIceCustomer();
 // Homemade popsicles for the pool cooler.
 auto P=Pool();const double Cap=Number(D,TEXT("popsicle_cap"),12),Have=Number(P,TEXT("popsicle_stock"));
 const int32 Made=int32(FMath::Min(Number(D,TEXT("popsicle_supply"),4),FMath::Max(0.,Cap-Have)));
 if(Made>0){P->SetNumberField(TEXT("popsicle_stock"),Have+Made);Book(-Made*Number(D,TEXT("popsicle_cost"),2),FString::Printf(TEXT("Sorveteria: %d picolé(s) para o cooler da piscina"),Made));}
}

FMareIceResult UMareSimulation::ServeIceCream(const TArray<FString>& Flavors,const TArray<float>& Sizes,const FString& Topping)
{
 FMareIceResult R;const auto D=IceDefs();auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("sorveteria"));auto& Queue=Arr(Biz,TEXT("queue"));
 if(Queue.IsEmpty()){Fail(TEXT("Ninguém na fila da sorveteria."));return R;}
 const auto O=Queue[0]->AsObject();TArray<FString> Want;const TArray<TSharedPtr<FJsonValue>>* F=nullptr;if(O->TryGetArrayField(TEXT("flavors"),F))for(const auto& V:*F)Want.Add(V->AsString());
 TArray<FString> A=Want,B=Flavors;A.Sort();B.Sort();const bool bFlavors=A==B;
 double Lo=.7,Hi=1;const TArray<TSharedPtr<FJsonValue>>* Right=nullptr;if(D->TryGetArrayField(TEXT("right"),Right) && Right->Num()==2){Lo=(*Right)[0]->AsNumber();Hi=(*Right)[1]->AsNumber();}
 int32 Small=0,Big=0;for(float S:Sizes){Small+=S<Lo;Big+=S>Hi;}
 const bool bSizes=Sizes.Num()==Want.Num() && Small+Big==0,bTopping=Topping==String(O,TEXT("topping"));
 R.Hits=int32(bFlavors)+int32(bSizes)+int32(bTopping);
 const TArray<TSharedPtr<FJsonValue>>* Pay=nullptr;const double Factor=D->TryGetArrayField(TEXT("pay"),Pay) && Pay->IsValidIndex(R.Hits)?(*Pay)[R.Hits]->AsNumber():.3+.3*R.Hits;
 const double Price=Want.Num()*Number(D,TEXT("price_per_scoop"),6)+(String(O,TEXT("topping"))!=TEXT("nenhuma")?Number(D,TEXT("topping_price"),2):0);
 R.Paid=FMath::RoundToDouble(Price*Factor)+(R.Hits==3?Number(D,TEXT("tip_perfect"),5):0);
 const FString Who=String(O,TEXT("name"));Book(R.Paid,FString::Printf(TEXT("Sorveteria: casquinha de %s (%d/3)"),*Who,R.Hits));
 AddFame(int32(Number(D,TEXT("fame_per_hit"),1))*R.Hits);Biz->SetNumberField(TEXT("games"),Number(Biz,TEXT("games"))+1);
 Queue.RemoveAt(0);R.bServed=true;
 TArray<FString> Notes;if(!bFlavors)Notes.Add(TEXT("sabor trocado"));if(Small)Notes.Add(TEXT("bola pequena"));if(Big)Notes.Add(TEXT("bola grande demais"));
 if(Sizes.Num()!=Want.Num())Notes.Add(FString::Printf(TEXT("pediu %d bola(s)"),Want.Num()));if(!bTopping)Notes.Add(TEXT("cobertura errada"));
 LastMessage=R.Hits==3?FString::Printf(TEXT("Perfeito! %s adorou: R$ %.0f com gorjeta."),*Who,R.Paid)
  :FString::Printf(TEXT("%s pagou R$ %.0f (%s)."),*Who,R.Paid,*FString::Join(Notes,TEXT(", ")));
 Save();return R;
}
