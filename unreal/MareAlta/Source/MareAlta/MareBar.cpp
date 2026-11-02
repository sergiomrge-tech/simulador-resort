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
 if(!B->HasField(TEXT("stock"))){auto Stock=Child(B,TEXT("stock"));const int32 Half=int32(Number(BarDefs(),TEXT("restock_qty"),10))/2;
  for(const auto& V:Items(BarDefs(),TEXT("ingredients")))Stock->SetNumberField(String(V->AsObject(),TEXT("id")),Half);}
 if(!B->HasField(TEXT("known"))){auto& Known=List(B,TEXT("known"));
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
  if(Needs.Num()!=Mix.Num())continue;bool bAll=true;for(const auto& N:Needs)bAll&=Mix.Contains(N->AsString());
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
 auto B=Bar();auto& Orders=List(B,TEXT("orders"));if(Orders.Num()>=Number(BarDefs(),TEXT("max_orders"),4))return FString();
 FString Drink=Want;FString Hint;
 if(Drink.IsEmpty()){
  TArray<FString> Known,Unknown;for(const auto& V:Items(BarDefs(),TEXT("recipes"))){const FString Id=String(V->AsObject(),TEXT("id"));(IsRecipeKnown(Id)?Known:Unknown).Add(Id);}
  const float Roll=FMath::FRand();
  // Most guests order from the menu; some leave it to the bartender; some ask for a drink you do not know yet.
  if(Roll<.2f)Drink=TEXT("surpresa");
  else if(Roll<.42f && Unknown.Num())Drink=Unknown[FMath::RandRange(0,Unknown.Num()-1)];
  else Drink=Known.Num()?Known[FMath::RandRange(0,Known.Num()-1)]:TEXT("surpresa");
 }
 if(auto R=BarRecipe(Drink))if(!IsRecipeKnown(Drink))Hint=String(R,TEXT("hint"));
 const int32 Next=Number(B,TEXT("next"));B->SetNumberField(TEXT("next"),Next+1);
 auto O=MakeShared<FJsonObject>();const FString Id=FString::Printf(TEXT("b%d"),Next);
 O->SetStringField(TEXT("id"),Id);O->SetStringField(TEXT("name"),BarNames[(Next*7+3)%UE_ARRAY_COUNT(BarNames)]);
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
 FBarResult Out;auto B=Bar();auto& Orders=List(B,TEXT("orders"));auto Stock=Child(B,TEXT("stock"));
 int32 Index=INDEX_NONE;for(int32 I=0;I<Orders.Num();++I)if(String(Orders[I]->AsObject(),TEXT("id"))==OrderId)Index=I;
 if(Index==INDEX_NONE){Fail(TEXT("Esse cliente já foi embora."));return Out;}
 if(Ingredients.IsEmpty()){Fail(TEXT("A coqueteleira está vazia."));return Out;}
 for(const FString& I:Ingredients)if(Number(Stock,I)<1){Fail(TEXT("Acabou um ingrediente: reponha o bar."));return Out;}
 for(const FString& I:Ingredients)Stock->SetNumberField(I,Number(Stock,I)-1);
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
 Out.Paid=FMath::RoundToDouble(DrinkPrice(Out.Recipe)*(1+.15*FMath::Clamp(1-Waited/30.,0.,1.)));Out.bServed=true;
 Book(Out.Paid,TEXT("Bar: ")+Name);AddFame(1);
 B->SetNumberField(TEXT("served"),Number(B,TEXT("served"))+1);B->SetStringField(TEXT("last"),Out.Recipe);Orders.RemoveAt(Index);
 LastMessage=(Out.bDiscovered?FString::Printf(TEXT("Receita nova descoberta: %s! "),*Name):FString())+FString::Printf(TEXT("%s adorou o drink: R$ %.0f."),*Guest,Out.Paid);
 Save();return Out;
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
   B->SetNumberField(TEXT("served"),Number(B,TEXT("served"))+1);B->SetStringField(TEXT("last"),Want);Orders.RemoveAt(I);++Served;}}
 const int32 Arrivals=FMath::RandRange(1,2+FameLevel()/4);for(int32 I=0;I<Arrivals;++I)AddBarOrder();
}
