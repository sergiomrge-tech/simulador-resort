// Food truck, hands-on (CHECKLIST_EXPANSOES 3.2): a queue at the Pastel truck, each pastel filled, sealed, fried to
// the golden point and sometimes a sugar-cane juice pressed at the mill; more customers on party days. Values in
// Content/Data/business_games.json businesses.food_truck.pastel.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 const TCHAR* PastelNames[]={TEXT("Seu Zé"),TEXT("Dona Lurdes"),TEXT("Kauã"),TEXT("Bia"),TEXT("Neném"),TEXT("Marcão"),TEXT("Carol"),TEXT("Tio Beto"),TEXT("Luana"),TEXT("Gui"),TEXT("Dona Fátima"),TEXT("Yuri")};
 TArray<TSharedPtr<FJsonValue>>& Arr(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  if(!O->HasTypedField<EJson::Array>(Key))O->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
  return const_cast<TArray<TSharedPtr<FJsonValue>>&>(O->GetArrayField(Key));
 }
 double Now(const TSharedPtr<FJsonObject>& State){return UMareSimulation::Number(State,TEXT("day"),1)*1440+UMareSimulation::Number(State,TEXT("minutes"));}
}

TSharedPtr<FJsonObject> UMareSimulation::PastelDefs() const
{
 return Object(Object(Object(BusinessGames(),TEXT("businesses")),TEXT("food_truck")),TEXT("pastel"));
}

TArray<TSharedPtr<FJsonObject>> UMareSimulation::PastelQueue() const
{
 TArray<TSharedPtr<FJsonObject>> Out;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("food_truck"))->TryGetArrayField(TEXT("queue"),List))for(const auto& V:*List)Out.Add(V->AsObject());
 return Out;
}

FString UMareSimulation::PastelOrderLine(const TSharedPtr<FJsonObject>& Order) const
{
 const auto D=PastelDefs();FString Filling=String(Order,TEXT("filling"));const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
 if(D->TryGetArrayField(TEXT("fillings"),L))for(const auto& V:*L)if(String(V->AsObject(),TEXT("id"))==Filling)Filling=String(V->AsObject(),TEXT("name"));
 bool bCana=false;if(Order.IsValid())Order->TryGetBoolField(TEXT("cana"),bCana);
 return TEXT("pastel de ")+Filling+(bCana?TEXT(" + caldo de cana"):TEXT(""));
}

void UMareSimulation::AddPastelCustomer()
{
 const auto D=PastelDefs();auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("food_truck"));auto& Queue=Arr(Biz,TEXT("queue"));
 if(Queue.Num()>=int32(Number(D,TEXT("queue_max"),6)))return;const TArray<TSharedPtr<FJsonValue>>* F=nullptr;
 if(!D->TryGetArrayField(TEXT("fillings"),F) || F->IsEmpty())return;
 auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("filling"),String((*F)[FMath::RandRange(0,F->Num()-1)]->AsObject(),TEXT("id")));
 O->SetBoolField(TEXT("cana"),FMath::FRand()<Number(D,TEXT("cana_chance"),.5));
 const int32 Next=int32(Number(Biz,TEXT("next_customer")));Biz->SetNumberField(TEXT("next_customer"),Next+1);
 O->SetStringField(TEXT("name"),PastelNames[(Next*5+int32(Number(State,TEXT("day"),1)))%UE_ARRAY_COUNT(PastelNames)]);O->SetNumberField(TEXT("since"),Now(State));
 Queue.Add(MakeShared<FJsonValueObject>(O));
}

void UMareSimulation::PastelHour(int32 Hour)
{
 if(!OwnsBusiness(TEXT("food_truck")))return;const auto D=PastelDefs();auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("food_truck"));
 auto& Queue=Arr(Biz,TEXT("queue"));const bool bOpen=IsBusinessOpen(TEXT("food_truck"));int32 Gone=0;
 for(int32 I=Queue.Num()-1;I>=0;--I)if(!bOpen || Now(State)-Number(Queue[I]->AsObject(),TEXT("since"))>Number(D,TEXT("patience_minutes"),40)){Queue.RemoveAt(I);++Gone;}
 if(Gone && bOpen)LastMessage=FString::Printf(TEXT("Food truck: %d cliente(s) cansaram de esperar o pastel."),Gone);
 if(!bOpen)return;
 // A party day (quermesse, festa junina, show) fills the street.
 const TArray<TSharedPtr<FJsonValue>>* Range=nullptr;int32 Lo=1,Hi=2;if(D->TryGetArrayField(TEXT("arrivals"),Range) && Range->Num()==2){Lo=int32((*Range)[0]->AsNumber());Hi=int32((*Range)[1]->AsNumber());}
 double N=FMath::RandRange(Lo,Hi);const TArray<TSharedPtr<FJsonValue>>* Parties=nullptr;
 if(D->TryGetArrayField(TEXT("party_events"),Parties) && Parties->ContainsByPredicate([this](const TSharedPtr<FJsonValue>& V){return V->AsString()==TodayEvent();}))N*=Number(D,TEXT("party_mult"),2);
 if(String(State,TEXT("weather"))==TEXT("rain"))N*=Number(D,TEXT("rain_mult"),.6);
 const int32 Arrive=FMath::FloorToInt(N)+(FMath::FRand()<FMath::Frac(N)?1:0);for(int32 I=0;I<Arrive;++I)AddPastelCustomer();
}

FMareIceResult UMareSimulation::ServePastel(const FString& Filling,bool bSealed,double FrySeconds,bool bCana)
{
 FMareIceResult R;const auto D=PastelDefs();auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("food_truck"));auto& Queue=Arr(Biz,TEXT("queue"));
 if(Queue.IsEmpty()){Fail(TEXT("Ninguém na fila do pastel."));return R;}
 const auto O=Queue[0]->AsObject();bool bWantsCana=false;O->TryGetBoolField(TEXT("cana"),bWantsCana);
 const double From=Number(D,TEXT("golden_from"),5.5),To=Number(D,TEXT("golden_to"),8.5),Burnt=Number(D,TEXT("burnt_s"),11.5);
 const bool bFilling=Filling==String(O,TEXT("filling")),bGolden=FrySeconds>=From && FrySeconds<=To;
 R.Hits=int32(bFilling)+int32(bSealed)+int32(bGolden);
 double Price=0;const TArray<TSharedPtr<FJsonValue>>* F=nullptr;
 if(D->TryGetArrayField(TEXT("fillings"),F))for(const auto& V:*F)if(String(V->AsObject(),TEXT("id"))==String(O,TEXT("filling")))Price=Number(V->AsObject(),TEXT("price"),9);
 const TArray<TSharedPtr<FJsonValue>>* Pay=nullptr;const double Factor=D->TryGetArrayField(TEXT("pay"),Pay) && Pay->IsValidIndex(R.Hits)?(*Pay)[R.Hits]->AsNumber():.3+.3*R.Hits;
 // A burnt pastel is not sold at all; the juice is paid when it was asked for and pressed.
 const bool bBurnt=FrySeconds>Burnt;const double Juice=bWantsCana && bCana?Number(D,TEXT("cana_price"),6):0;
 R.Paid=(bBurnt?0:FMath::RoundToDouble(Price*Factor))+Juice+(R.Hits==3 && (!bWantsCana || bCana)?Number(D,TEXT("tip_perfect"),4):0);
 const FString Who=String(O,TEXT("name"));if(R.Paid>0)Book(R.Paid,FString::Printf(TEXT("Food truck: pastel de %s (%d/3)"),*Who,R.Hits));
 AddFame(int32(Number(D,TEXT("fame_per_hit"),1))*R.Hits);Biz->SetNumberField(TEXT("games"),Number(Biz,TEXT("games"))+1);
 Queue.RemoveAt(0);R.bServed=true;
 TArray<FString> Notes;if(!bFilling)Notes.Add(TEXT("recheio errado"));if(!bSealed)Notes.Add(TEXT("abriu no óleo"));
 if(FrySeconds<From)Notes.Add(TEXT("ficou cru"));else if(bBurnt)Notes.Add(TEXT("queimou"));else if(!bGolden)Notes.Add(TEXT("passou do ponto"));
 if(bWantsCana && !bCana)Notes.Add(TEXT("faltou o caldo de cana"));
 LastMessage=R.Hits==3 && Notes.IsEmpty()?FString::Printf(TEXT("Pastel dourado e crocante! %s pagou R$ %.0f com gorjeta."),*Who,R.Paid)
  :FString::Printf(TEXT("%s pagou R$ %.0f (%s)."),*Who,R.Paid,*FString::Join(Notes,TEXT(", ")));
 Save();return R;
}
