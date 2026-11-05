// Bar do Coqueiro: drinks mixed at the counter from bought ingredients, recipes discovered by mixing
// (gameplay plan M8). State lives in the save ("bar") like the stays, so tests and a future co-op share it.
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
 TArray<TSharedPtr<FJsonValue>> Items(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  const TArray<TSharedPtr<FJsonValue>>* Found=nullptr;return Parent->TryGetArrayField(Key,Found)?*Found:TArray<TSharedPtr<FJsonValue>>();
 }
 const TCHAR* BarNames[]={TEXT("Rafa"),TEXT("Bia"),TEXT("Caio"),TEXT("Duda"),TEXT("Léo"),TEXT("Malu"),TEXT("Téo"),TEXT("Lia"),
  TEXT("Guto"),TEXT("Nanda"),TEXT("Vini"),TEXT("Babi"),TEXT("Juca"),TEXT("Mel"),TEXT("Tati"),TEXT("Beto")};
}

TSharedPtr<FJsonObject> UMareSimulation::BarDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/bar.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

TSharedPtr<FJsonObject> UMareSimulation::Bar()
{
 auto B=Child(State,TEXT("bar"));
 // First visit: the starting menu and half a restock of every ingredient (the bar comes with its shelf filled).
 // An empty {} counts as never filled: Object() creates fields on read (the bar world reads the stock every frame).
 if(!B->HasField(TEXT("stock")) || Object(B,TEXT("stock"))->Values.IsEmpty()){auto Stock=Child(B,TEXT("stock"));const int32 Half=int32(Number(BarDefs(),TEXT("restock_qty"),10))/2;
  for(const auto& V:Items(BarDefs(),TEXT("ingredients")))Stock->SetNumberField(String(V->AsObject(),TEXT("id")),Half);}
 if(!B->HasField(TEXT("known")) || Items(B,TEXT("known")).IsEmpty()){auto& Known=List(B,TEXT("known"));
  for(const auto& V:Items(BarDefs(),TEXT("recipes"))){bool bKnown=false;V->AsObject()->TryGetBoolField(TEXT("known"),bKnown);
   if(bKnown)Known.Add(MakeShared<FJsonValueString>(String(V->AsObject(),TEXT("id"))));}}
 return B;
}

TSharedPtr<FJsonObject> UMareSimulation::BarRecipe(const FString& Recipe) const
{
 for(const auto& V:Items(BarDefs(),TEXT("recipes")))if(String(V->AsObject(),TEXT("id"))==Recipe)return V->AsObject();
 return nullptr;
}

FString UMareSimulation::MixRecipe(const TArray<FString>& Ingredients) const
{
 TSet<FString> Mix(Ingredients);if(Mix.Num()!=Ingredients.Num())return FString();     // a doubled ingredient is never a recipe
 for(const auto& V:Items(BarDefs(),TEXT("recipes"))){auto R=V->AsObject();const auto Needs=Items(R,TEXT("needs"));
  if(Needs.Num()!=Mix.Num() || !IsBarSecretOpen(String(R,TEXT("id"))))continue;bool bAll=true;for(const auto& N:Needs)bAll&=Mix.Contains(N->AsString());
  if(bAll)return String(R,TEXT("id"));}
 return FString();
}

bool UMareSimulation::IsRecipeKnown(const FString& Recipe) const
{
 for(const auto& V:Items(Object(State,TEXT("bar")),TEXT("known")))if(V->AsString()==Recipe)return true;
 bool bKnown=false;if(auto R=BarRecipe(Recipe))R->TryGetBoolField(TEXT("known"),bKnown);return bKnown;
}

bool UMareSimulation::IsBarOpen() const
{
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("bar"),bOwned);if(!bOwned)return false;
 const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;const double Hour=Number(State,TEXT("minutes"))/60;
 return !BarDefs()->TryGetArrayField(TEXT("open"),Open) || Open->Num()!=2 || (Hour>=(*Open)[0]->AsNumber() && Hour<(*Open)[1]->AsNumber());
}

double UMareSimulation::DrinkPrice(const FString& Recipe) const
{
 auto R=BarRecipe(Recipe);if(!R)return 0;
 return FMath::RoundToDouble(Number(R,TEXT("price"))*FMath::Max(1.,PlaceIncomeFactor(TEXT("bar")))*(1+.03*(FameLevel()-1)));
}

FString UMareSimulation::AddBarOrder(const FString& Want)
{
 if(!IsBarOpen())return FString();
 auto B=Bar();auto& Orders=List(B,TEXT("orders"));
 if(Orders.Num()>=Number(BarDefs(),IsBarRush()?TEXT("max_orders_rush"):TEXT("max_orders"),4))return FString();
 FString Drink=Want;FString Hint;FString Guest;bool bUsual=false;
 const int32 Next0=int32(Number(B,TEXT("next")));
 if(Drink.IsEmpty() && FMath::FRand()<Number(BarDefs(),TEXT("regular_chance"),.3)){
  // A regular not already at the counter comes back for "o de sempre".
  TSet<FString> Seated;for(const auto& V:Items(B,TEXT("orders")))Seated.Add(String(V->AsObject(),TEXT("name")));
  TArray<FString> Free;for(const auto& Pair:BarRegulars())if(!Seated.Contains(Pair.Key) && BarRecipe(Pair.Value))Free.Add(Pair.Key);
  if(Free.Num()){Guest=Free[FMath::RandRange(0,Free.Num()-1)];Drink=BarRegulars()[Guest];bUsual=true;}}
 bool bVip=false;
 if(Drink.IsEmpty() && Guest.IsEmpty() && FameLevel()>=Number(BarDefs(),TEXT("vip_fame"),4) && FMath::FRand()<Number(BarDefs(),TEXT("vip_chance"),.12)){
  // A VIP (once per visit) who knows the house's secret drink and tells it to whoever serves them well.
  bool bOpen=true;for(const auto& V:Items(BarDefs(),TEXT("recipes"))){bool bSecret=false;V->AsObject()->TryGetBoolField(TEXT("secret"),bSecret);if(bSecret)bOpen&=IsBarSecretOpen(String(V->AsObject(),TEXT("id")));}
  bool bSeated=false;for(const auto& V:Items(B,TEXT("orders"))){bool bV=false;V->AsObject()->TryGetBoolField(TEXT("vip"),bV);bSeated|=bV;}
  if(!bOpen && !bSeated){bVip=true;Guest=String(BarDefs(),TEXT("vip_name"));Drink=TEXT("surpresa");}}
 if(Drink.IsEmpty()){
  TArray<FString> Known,Unknown;for(const auto& V:Items(BarDefs(),TEXT("recipes"))){const FString Id=String(V->AsObject(),TEXT("id"));
   if(!IsBarSecretOpen(Id))continue;(IsRecipeKnown(Id)?Known:Unknown).Add(Id);}
  const float Roll=FMath::FRand();
  // Most guests order from the menu; some leave it to the bartender; some ask for a drink you do not know yet.
  if(Roll<.2f)Drink=TEXT("surpresa");
  else if(Roll<.42f && Unknown.Num())Drink=Unknown[FMath::RandRange(0,Unknown.Num()-1)];
  else Drink=Known.Num()?Known[FMath::RandRange(0,Known.Num()-1)]:TEXT("surpresa");
 }
 if(auto R=BarRecipe(Drink))if(!IsRecipeKnown(Drink))Hint=String(R,TEXT("hint"));
 const int32 Next=Number(B,TEXT("next"));B->SetNumberField(TEXT("next"),Next+1);
 auto O=MakeShared<FJsonObject>();const FString Id=FString::Printf(TEXT("b%d"),Next);
 O->SetStringField(TEXT("id"),Id);O->SetStringField(TEXT("name"),Guest.IsEmpty()?FString(BarNames[(Next*7+3)%UE_ARRAY_COUNT(BarNames)]):Guest);
 // Taste profile (doce/forte/azedo) shown with a surprise and used to rate it.
 {TArray<FString> Tastes;for(const auto& Pair:Object(BarDefs(),TEXT("tastes"))->Values)Tastes.Add(FString(Pair.Key.ToView()));
  if(Tastes.Num())O->SetStringField(TEXT("taste"),Tastes[(Next0*5+1)%Tastes.Num()]);}
 if(bUsual)O->SetBoolField(TEXT("usual"),true);
 if(bVip)O->SetBoolField(TEXT("vip"),true);
 O->SetStringField(TEXT("want"),Drink);if(!Hint.IsEmpty())O->SetStringField(TEXT("hint"),Hint);
 O->SetNumberField(TEXT("since"),Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes")));
 Orders.Add(MakeShared<FJsonValueObject>(O));return Id;
}

double UMareSimulation::BarRestockCost() const
{
 double Cost=0;const double Qty=Number(BarDefs(),TEXT("restock_qty"),10);auto Stock=Object(Object(State,TEXT("bar")),TEXT("stock"));
 for(const auto& V:Items(BarDefs(),TEXT("ingredients"))){auto I=V->AsObject();Cost+=FMath::Max(0.,Qty-Number(Stock,String(I,TEXT("id"))))*Number(I,TEXT("cost"));}
 return FMath::RoundToDouble(Cost);
}

bool UMareSimulation::RestockBar()
{
 auto Stock=Child(Bar(),TEXT("stock"));const double Cost=BarRestockCost();
 if(Cost<=0)return Fail(TEXT("O estoque do bar já está cheio."));
 if(Money()<Cost)return Fail(FString::Printf(TEXT("Repor o bar custa R$ %.0f."),Cost));
 const double Qty=Number(BarDefs(),TEXT("restock_qty"),10);
 for(const auto& V:Items(BarDefs(),TEXT("ingredients"))){const FString Id=String(V->AsObject(),TEXT("id"));Stock->SetNumberField(Id,FMath::Max(Qty,Number(Stock,Id)));}
 Book(-Cost,TEXT("Bar: ingredientes"));LastMessage=FString::Printf(TEXT("Bar reabastecido por R$ %.0f."),Cost);return Save();
}

UMareSimulation::FBarResult UMareSimulation::ServeBar(const FString& OrderId,const TArray<FString>& Ingredients)
{
 return ServeMix(OrderId,Ingredients,true,-1);
}

UMareSimulation::FBarResult UMareSimulation::ServeMix(const FString& OrderId,const TArray<FString>& Ingredients,bool bUseStock,double PrepScore)
{
 FBarResult Out;auto B=Bar();auto& Orders=List(B,TEXT("orders"));auto Stock=Child(B,TEXT("stock"));
 int32 Index=INDEX_NONE;for(int32 I=0;I<Orders.Num();++I)if(String(Orders[I]->AsObject(),TEXT("id"))==OrderId)Index=I;
 if(Index==INDEX_NONE){Fail(TEXT("Esse cliente já foi embora."));return Out;}
 if(Ingredients.IsEmpty()){Fail(TEXT("A coqueteleira está vazia."));return Out;}
 if(bUseStock){
  for(const FString& I:Ingredients)if(Number(Stock,I)<1){Fail(TEXT("Acabou um ingrediente: reponha o bar."));return Out;}
  for(const FString& I:Ingredients)Stock->SetNumberField(I,Number(Stock,I)-1);}
 const auto Order=Orders[Index]->AsObject();const FString Want=String(Order,TEXT("want")),Guest=String(Order,TEXT("name"));
 Out.Recipe=MixRecipe(Ingredients);
 if(Out.Recipe.IsEmpty()){LastMessage=FString::Printf(TEXT("%s provou e fez careta: essa mistura não é drink nenhum."),*Guest);Save();return Out;}
 const auto R=BarRecipe(Out.Recipe);const FString Name=String(R,TEXT("name"));
 if(!IsRecipeKnown(Out.Recipe)){Out.bDiscovered=true;List(B,TEXT("known")).Add(MakeShared<FJsonValueString>(Out.Recipe));AddFame(int32(Number(BarDefs(),TEXT("discovery_fame"),6)));}
 if(Want!=Out.Recipe && Want!=TEXT("surpresa")){
  const auto Asked=BarRecipe(Want);
  LastMessage=(Out.bDiscovered?FString::Printf(TEXT("Receita nova: %s! "),*Name):FString())+FString::Printf(TEXT("Mas %s pediu %s."),*Guest,
   *(Asked && IsRecipeKnown(Want)?String(Asked,TEXT("name")):FString(TEXT("outra coisa"))));
  Save();return Out;}
 // Served: price plus a tip that shrinks with the wait (up to 15% within half an hour).
 const double Waited=Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes"))-Number(Order,TEXT("since"));
 // A careful prep (the mini-actions' average score) moves the price up to ±prep_tip.
 const double Prep=PrepScore<0?1.:1+Number(BarDefs(),TEXT("prep_tip"),.1)*(2*FMath::Clamp(PrepScore,0.,1.)-1);
 double Extra=1;
 if(Want==TEXT("surpresa")){Out.Stars=SurpriseStars(Out.Recipe,String(Order,TEXT("taste")));
  const auto Prices=Items(BarDefs(),TEXT("stars_price"));if(Prices.IsValidIndex(Out.Stars-1))Extra=Prices[Out.Stars-1]->AsNumber();}
 bool bUsualOrder=false;Order->TryGetBoolField(TEXT("usual"),bUsualOrder);
 if(bUsualOrder){Out.bUsual=true;Extra*=1+Number(BarDefs(),TEXT("regular_tip"),.15);AddFame(int32(Number(BarDefs(),TEXT("regular_fame"),1)));}
 Out.Paid=FMath::RoundToDouble(DrinkPrice(Out.Recipe)*(1+.15*FMath::Clamp(1-Waited/30.,0.,1.))*Prep*Extra);Out.bServed=true;
 bool bVipOrder=false;Order->TryGetBoolField(TEXT("vip"),bVipOrder);FString Secret;
 if(bVipOrder)for(const auto& V:Items(BarDefs(),TEXT("recipes"))){const auto SR=V->AsObject();bool bSecret=false;SR->TryGetBoolField(TEXT("secret"),bSecret);
  const FString Id=String(SR,TEXT("id"));if(!bSecret || IsBarSecretOpen(Id))continue;
  Child(B,TEXT("secrets"))->SetBoolField(Id,true);if(!IsRecipeKnown(Id)){List(B,TEXT("known")).Add(MakeShared<FJsonValueString>(Id));AddFame(int32(Number(BarDefs(),TEXT("discovery_fame"),6)));}
  TArray<FString> Parts;for(const auto& N:Items(SR,TEXT("needs")))for(const auto& I:Items(BarDefs(),TEXT("ingredients")))if(String(I->AsObject(),TEXT("id"))==N->AsString())Parts.Add(String(I->AsObject(),TEXT("name")));
  Secret=FString::Printf(TEXT(" %s cochichou o segredo da casa: %s = %s!"),*Guest,*String(SR,TEXT("name")),*FString::Join(Parts,TEXT(" + ")));}
 // Served right and fast: the guest becomes a regular and will ask for "o de sempre" (this drink).
 if(Waited<=Number(BarDefs(),TEXT("regular_wait"),20)){auto Regs=Child(B,TEXT("regulars"));
  if(!Regs->HasField(Guest) && Regs->Values.Num()<Number(BarDefs(),TEXT("max_regulars"),8))Regs->SetStringField(Guest,Out.Recipe);}
 Book(Out.Paid,TEXT("Bar: ")+Name);AddFame(1);
 B->SetNumberField(TEXT("served"),Number(B,TEXT("served"))+1);B->SetStringField(TEXT("last"),Out.Recipe);Orders.RemoveAt(Index);
 LastMessage=(Out.bDiscovered?FString::Printf(TEXT("Receita nova descoberta: %s! "),*Name):FString())+FString::Printf(TEXT("%s adorou o drink: R$ %.0f."),*Guest,Out.Paid);
 if(Out.Stars>0)LastMessage+=FString::Printf(TEXT(" Surpresa: %s"),*FString::ChrN(Out.Stars,TEXT('★')));
 if(Out.bUsual)LastMessage+=TEXT(" \"Isso! O de sempre.\"");
 LastMessage+=Secret;
 if(!HasBarAchievement()){bool bAll=true;for(const auto& V:Items(BarDefs(),TEXT("recipes")))bAll&=IsRecipeKnown(String(V->AsObject(),TEXT("id")));
  if(bAll){Child(Object(State,TEXT("prog")),TEXT("achievements"))->SetBoolField(TEXT("mestre_drinks"),true);AddFame(int32(Number(BarDefs(),TEXT("achievement_fame"),10)));
   LastMessage+=TEXT(" Conquista: Mestre dos drinks! Todas as receitas do bar descobertas.");}}
 Save();return Out;
}

// ---- Physical prep (CHECKLIST_EXPANSOES 1.1) -------------------------------------------------------------------------
namespace
{
 bool InList(const TSharedPtr<FJsonObject>& Defs,const FString& Key,const FString& Id)
 {
  for(const auto& V:Items(Defs,Key))if(V->AsString()==Id)return true;return false;
 }
}

FString UMareSimulation::BarHand() const{return String(Object(State,TEXT("bar")),TEXT("hand"));}

TArray<FString> UMareSimulation::BarGlass() const
{
 TArray<FString> Out;for(const auto& V:Items(Object(State,TEXT("bar")),TEXT("glass")))Out.Add(V->AsString());return Out;
}

bool UMareSimulation::BarPick(const FString& Ingredient)
{
 auto B=Bar();
 if(String(B,TEXT("hand"))==Ingredient){B->RemoveField(TEXT("hand"));LastMessage=TEXT("Devolvido à bancada.");return true;}
 bool bKnown=false;for(const auto& V:Items(BarDefs(),TEXT("ingredients")))bKnown|=String(V->AsObject(),TEXT("id"))==Ingredient;
 if(!bKnown)return Fail(TEXT("Isso não é ingrediente."));
 if(Number(Object(B,TEXT("stock")),Ingredient)<1)return Fail(TEXT("Acabou: reponha o bar no balcão."));
 B->SetStringField(TEXT("hand"),Ingredient);LastMessage=FString();return true;
}

bool UMareSimulation::BarPour()
{
 auto B=Bar();const FString Hand=String(B,TEXT("hand"));if(Hand.IsEmpty())return Fail(TEXT("Pegue um ingrediente na bancada."));
 auto& Glass=List(B,TEXT("glass"));auto Stock=Child(B,TEXT("stock"));
 for(const auto& V:Glass)if(V->AsString()==Hand)return Fail(TEXT("Isso já está no copo."));
 if(Glass.Num()>=Number(BarDefs(),TEXT("max_mix"),5))return Fail(TEXT("O copo está cheio."));
 if(Number(Stock,Hand)<1){B->RemoveField(TEXT("hand"));return Fail(TEXT("Acabou: reponha o bar no balcão."));}
 Stock->SetNumberField(Hand,Number(Stock,Hand)-1);Glass.Add(MakeShared<FJsonValueString>(Hand));
 // Anything added after shaking has to be mixed again.
 B->RemoveField(TEXT("hand"));B->RemoveField(TEXT("prep"));LastMessage=FString();return Save();
}

TArray<FString> UMareSimulation::BarPrepSteps(const TArray<FString>& Mix) const
{
 TArray<FString> Steps;if(Mix.IsEmpty())return Steps;auto Defs=BarDefs();bool bMuddle=false,bBlend=false;
 for(const FString& I:Mix){bMuddle|=InList(Defs,TEXT("muddle"),I);bBlend|=InList(Defs,TEXT("blend"),I);}
 if(bMuddle)Steps.Add(TEXT("socar"));Steps.Add(bBlend?TEXT("liquidificar"):TEXT("bater"));return Steps;
}

FString UMareSimulation::BarNextStep() const
{
 auto Prep=Object(Object(State,TEXT("bar")),TEXT("prep"));
 for(const FString& S:BarPrepSteps(BarGlass()))if(!Prep->HasField(S))return S;return FString();
}

bool UMareSimulation::BarPrepStep(const FString& Step,double Score)
{
 if(Step.IsEmpty() || BarNextStep()!=Step)return false;
 Child(Bar(),TEXT("prep"))->SetNumberField(Step,FMath::Clamp(Score,0.,1.));return Save();
}

double UMareSimulation::BarDiscard()
{
 auto B=Bar();double Lost=0;const TArray<FString> Glass=BarGlass();if(Glass.IsEmpty())return 0;
 for(const auto& V:Items(BarDefs(),TEXT("ingredients")))if(Glass.Contains(String(V->AsObject(),TEXT("id"))))Lost+=Number(V->AsObject(),TEXT("cost"));
 B->SetArrayField(TEXT("glass"),TArray<TSharedPtr<FJsonValue>>());B->RemoveField(TEXT("prep"));
 // The guest at the counter has an opinion about it.
 const auto Lines=Items(BarDefs(),TEXT("discard_reactions"));FString Guest;const FString Serving=BarServing();
 for(const auto& V:Items(B,TEXT("orders")))if(String(V->AsObject(),TEXT("id"))==Serving)Guest=String(V->AsObject(),TEXT("name"));
 const int32 Pick=int32(Number(B,TEXT("discarded")))%FMath::Max(1,Lines.Num());B->SetNumberField(TEXT("discarded"),Number(B,TEXT("discarded"))+1);
 LastMessage=FString::Printf(TEXT("Copo jogado fora: R$ %.2f perdidos."),Lost);
 if(!Guest.IsEmpty() && Lines.IsValidIndex(Pick))LastMessage+=FString::Printf(TEXT(" %s: \"%s\""),*Guest,*Lines[Pick]->AsString());
 Save();return Lost;
}

FString UMareSimulation::BarServing()
{
 auto B=Bar();const FString Chosen=String(B,TEXT("serving"));FString Oldest;double Since=TNumericLimits<double>::Max();
 for(const auto& V:Items(B,TEXT("orders"))){const auto O=V->AsObject();if(String(O,TEXT("id"))==Chosen)return Chosen;
  if(Number(O,TEXT("since"))<Since){Since=Number(O,TEXT("since"));Oldest=String(O,TEXT("id"));}}
 return Oldest;
}

void UMareSimulation::SetBarServing(const FString& Order){Bar()->SetStringField(TEXT("serving"),Order);}

UMareSimulation::FBarResult UMareSimulation::ServeGlass(const FString& Order)
{
 FBarResult Out;const TArray<FString> Glass=BarGlass();
 if(Glass.IsEmpty()){Fail(TEXT("O copo está vazio."));return Out;}
 const FString Next=BarNextStep();
 if(!Next.IsEmpty()){Fail(FString::Printf(TEXT("Falta %s antes de servir."),*Next));return Out;}
 if(Order.IsEmpty()){Fail(TEXT("Ninguém esperando no balcão."));return Out;}
 double Score=0;int32 N=0;for(const auto& Pair:Object(Bar(),TEXT("prep"))->Values){Score+=Pair.Value->AsNumber();++N;}
 Out=ServeMix(Order,Glass,false,N?Score/N:1);
 // Served or tasted, the glass is empty again unless the guest was already gone (then it stays for the next one).
 if(Out.bServed || !Out.Recipe.IsEmpty() || LastMessage.Contains(TEXT("careta"))){auto B=Bar();
  B->SetArrayField(TEXT("glass"),TArray<TSharedPtr<FJsonValue>>());B->RemoveField(TEXT("prep"));B->RemoveField(TEXT("serving"));Save();}
 return Out;
}

FString UMareSimulation::BarBubble(const TSharedPtr<FJsonObject>& Order) const
{
 bool bUsual=false;Order->TryGetBoolField(TEXT("usual"),bUsual);if(bUsual)return TEXT("O de sempre!");
 bool bVip=false;Order->TryGetBoolField(TEXT("vip"),bVip);
 if(bVip){const FString Word=String(Object(BarDefs(),TEXT("tastes")),String(Order,TEXT("taste")));
  return TEXT("VIP · Me surpreenda")+(Word.IsEmpty()?FString():TEXT(": ")+Word)+TEXT(". Se gostar, conto um segredo...");}
 const FString Want=String(Order,TEXT("want"));
 if(Want==TEXT("surpresa")){const FString Word=String(Object(BarDefs(),TEXT("tastes")),String(Order,TEXT("taste")));
  return Word.IsEmpty()?FString(TEXT("Me surpreenda!")):TEXT("Me surpreenda: ")+Word+TEXT("!");}
 if(IsRecipeKnown(Want))return String(BarRecipe(Want),TEXT("name"))+TEXT(", por favor!");
 const FString Hint=String(Order,TEXT("hint"));return Hint.IsEmpty()?FString(TEXT("Hmm... o que tem de bom?")):TEXT("Quero ")+Hint+TEXT("...");
}

int32 UMareSimulation::SurpriseStars(const FString& Recipe,const FString& Taste) const
{
 auto R=BarRecipe(Recipe);if(!R)return 1;const double Score=Number(Object(R,TEXT("taste")),Taste,.5);
 return FMath::Clamp(1+int32(FMath::RoundToDouble(2*Score)),1,3);
}

bool UMareSimulation::IsBarRush() const
{
 const double Hour=Number(State,TEXT("minutes"))/60;const TArray<TSharedPtr<FJsonValue>>* Happy=nullptr;
 if(BarDefs()->TryGetArrayField(TEXT("happy_hour"),Happy) && Happy->Num()==2 && Hour>=(*Happy)[0]->AsNumber() && Hour<(*Happy)[1]->AsNumber())return true;
 return TodayEvent()==TEXT("lua") && Hour>=Number(BarDefs(),TEXT("full_moon_from"),19);
}

bool UMareSimulation::IsBarSecretOpen(const FString& Recipe) const
{
 auto R=BarRecipe(Recipe);bool bSecret=false;if(R)R->TryGetBoolField(TEXT("secret"),bSecret);if(!bSecret)return true;
 // Saves that already found it by mixing (before it became secret) keep it.
 for(const auto& V:Items(Object(State,TEXT("bar")),TEXT("known")))if(V->AsString()==Recipe)return true;
 bool bOpen=false;Object(Object(State,TEXT("bar")),TEXT("secrets"))->TryGetBoolField(Recipe,bOpen);return bOpen;
}

bool UMareSimulation::HasBarAchievement() const
{
 bool bHas=false;Object(Object(State,TEXT("prog")),TEXT("achievements"))->TryGetBoolField(TEXT("mestre_drinks"),bHas);return bHas;
}

TMap<FString,FString> UMareSimulation::BarRegulars() const
{
 TMap<FString,FString> Out;for(const auto& Pair:Object(Object(State,TEXT("bar")),TEXT("regulars"))->Values)Out.Add(FString(Pair.Key.ToView()),Pair.Value->AsString());return Out;
}

void UMareSimulation::BarHour(int32 Hour)
{
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("bar"),bOwned);if(!bOwned)return;
 auto B=Bar();auto& Orders=List(B,TEXT("orders"));auto Stock=Child(B,TEXT("stock"));
 const double Now=Number(State,TEXT("day"),1)*1440+Number(State,TEXT("minutes"));const double Patience=Number(BarDefs(),TEXT("patience_hours"),2)*60;
 Orders.RemoveAll([&](const TSharedPtr<FJsonValue>& V){return Now-Number(V->AsObject(),TEXT("since"))>Patience || !IsBarOpen();});
 if(!IsBarOpen())return;
 // The bartender serves what is on the menu (a surprise becomes a known drink) at a share of the price, no tip.
 if(HasStaff(TEXT("bartender"))){int32 Served=0;
  for(int32 I=Orders.Num()-1;I>=0 && Served<3;--I){const auto O=Orders[I]->AsObject();FString Want=String(O,TEXT("want"));
   if(Want==TEXT("surpresa"))Want=TEXT("caipirinha");if(!IsRecipeKnown(Want))continue;
   const auto Needs=Items(BarRecipe(Want),TEXT("needs"));bool bStock=true;for(const auto& N:Needs)bStock&=Number(Stock,N->AsString())>=1;if(!bStock)continue;
   for(const auto& N:Needs)Stock->SetNumberField(N->AsString(),Number(Stock,N->AsString())-1);
   Book(FMath::RoundToDouble(DrinkPrice(Want)*Number(BarDefs(),TEXT("bartender_share"),.85)),TEXT("Bar (bartender): ")+String(BarRecipe(Want),TEXT("name")));
   StaffDid(TEXT("bartender"),1,FMath::RoundToDouble(DrinkPrice(Want)*Number(BarDefs(),TEXT("bartender_share"),.85)));
   B->SetNumberField(TEXT("served"),Number(B,TEXT("served"))+1);B->SetStringField(TEXT("last"),Want);Orders.RemoveAt(I);++Served;}}
 const int32 Arrivals=FMath::RandRange(1,2+FameLevel()/4)*(IsBarRush()?int32(Number(BarDefs(),TEXT("rush_mult"),2)):1);
 for(int32 I=0;I<Arrivals;++I)AddBarOrder();
}
