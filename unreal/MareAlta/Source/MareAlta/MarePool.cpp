// Pool day use, hands-on: leaves to scoop, towels to collect, popsicles to sell (gameplay plan, P1 "Piscina").
// Cleanliness scales the pool's hourly income and, at closing, adds a guest rating (stars). State lives in the save.
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
}

TSharedPtr<FJsonObject> UMareSimulation::PoolDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/pool.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}
TSharedPtr<FJsonObject> UMareSimulation::Pool(){return Child(State,TEXT("pool"));}

int32 UMareSimulation::PoolTowels() const
{
 const TArray<TSharedPtr<FJsonValue>>* T=nullptr;return Object(State,TEXT("pool"))->TryGetArrayField(TEXT("towels"),T)?T->Num():0;
}

double UMareSimulation::PoolCleanliness() const
{
 const auto P=Object(State,TEXT("pool"));
 return FMath::Clamp(1-Number(P,TEXT("dirt"))/100*Number(PoolDefs(),TEXT("dirt_penalty"),.5)-PoolTowels()*Number(PoolDefs(),TEXT("towel_penalty"),.03),.3,1.);
}

bool UMareSimulation::ScoopPool()
{
 auto P=Pool();const double Dirt=Number(P,TEXT("dirt"));if(Dirt<=0)return Fail(TEXT("A água já está limpa."));
 P->SetNumberField(TEXT("dirt"),FMath::Max(0.,Dirt-Number(PoolDefs(),TEXT("scoop"),25)));
 LastMessage=Number(P,TEXT("dirt"))<=0?TEXT("Piscina limpinha!"):TEXT("Folhas retiradas com a peneira.");return Save();
}

bool UMareSimulation::CollectPoolTowel(int32 Lounger)
{
 auto& Towels=List(Pool(),TEXT("towels"));
 const int32 Index=Towels.IndexOfByPredicate([Lounger](const TSharedPtr<FJsonValue>& V){return int32(V->AsNumber())==Lounger;});
 if(Index==INDEX_NONE)return Fail(TEXT("Nada para recolher aqui."));
 Towels.RemoveAt(Index);LastMessage=TEXT("Toalha recolhida.");return Save();
}

bool UMareSimulation::SellPopsicles()
{
 auto P=Pool();const int32 Want=int32(Number(P,TEXT("popsicles")));if(Want<=0)return Fail(TEXT("Ninguém pediu picolé agora."));
 const double Paid=FMath::RoundToDouble(Want*Number(PoolDefs(),TEXT("popsicle_price"),7)*FMath::Max(1.,PlaceIncomeFactor(TEXT("pool"))));
 P->SetNumberField(TEXT("popsicles"),0);Book(Paid,FString::Printf(TEXT("Piscina: %d picolé(s)"),Want));AddFame(1);
 LastMessage=FString::Printf(TEXT("%d picolé(s) vendido(s): R$ %.0f."),Want,Paid);return Save();
}

void UMareSimulation::PoolHour(int32 Hour)
{
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("pool"),bOwned);if(!bOwned)return;
 const auto Op=Object(Object(Object(CustomDefs(),TEXT("operations")),TEXT("hourly")),TEXT("pool"));
 const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;if(!Op->TryGetArrayField(TEXT("open"),Open) || Open->Num()!=2)return;
 const int32 Started=Hour-1;if(Started<(*Open)[0]->AsNumber() || Started>=(*Open)[1]->AsNumber())return;
 auto P=Pool();const bool bRain=String(State,TEXT("weather"))==TEXT("rain");
 const TArray<TSharedPtr<FJsonValue>>* Range=nullptr;double Add=8;
 if(PoolDefs()->TryGetArrayField(TEXT("dirt_per_hour"),Range) && Range->Num()==2)Add=FMath::FRandRange((*Range)[0]->AsNumber(),(*Range)[1]->AsNumber());
 P->SetNumberField(TEXT("dirt"),FMath::Min(100.,Number(P,TEXT("dirt"))+Add+(bRain?Number(PoolDefs(),TEXT("rain_extra"),6):0)));
 if(!bRain){
  // Bathers leave a towel on a free lounger now and then and ask for popsicles in the heat.
  const TArray<TSharedPtr<FJsonValue>>* Loungers=nullptr;auto& Towels=List(P,TEXT("towels"));
  if(PoolDefs()->TryGetArrayField(TEXT("loungers"),Loungers) && FMath::FRand()<.6f){
   TArray<int32> Free;
   for(int32 I=0;I<Loungers->Num();++I)if(!Towels.ContainsByPredicate([I](const TSharedPtr<FJsonValue>& V){return int32(V->AsNumber())==I;}))Free.Add(I);
   if(Free.Num())Towels.Add(MakeShared<FJsonValueNumber>(Free[FMath::RandRange(0,Free.Num()-1)]));}
  P->SetNumberField(TEXT("popsicles"),FMath::Min(Number(PoolDefs(),TEXT("max_popsicles"),6),Number(P,TEXT("popsicles"))+FMath::RandRange(0,2)));}
 // Closing hour: the day's bathers rate the pool by how clean it is (feeds the resort stars).
 if(Started==int32((*Open)[1]->AsNumber())-1){
  TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
  Ratings.Add(MakeShared<FJsonValueNumber>(FMath::RoundToDouble((2+3*PoolCleanliness())*2)/2));
  while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);
  P->SetNumberField(TEXT("popsicles"),0);}
}
