// Common to every village business (CHECKLIST_EXPANSOES 3.6): levels 1 to 3 (each dearer and with a harder hands-on
// task: business_games.json businesses.<id>.levels[], "set" overrides the game values and "price_mult" the prices),
// the optional clerk who serves the line by himself at clerk_share (60 %) of the price and no fame, while serving in
// person pays 100 % plus tip and fame, and the daily report of each business shown on the phone.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 TSharedPtr<FJsonObject> Kid(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  if(!Parent->HasTypedField<EJson::Object>(Key))Parent->SetObjectField(Key,MakeShared<FJsonObject>());
  return Parent->GetObjectField(Key);
 }
}

const TCHAR* UMareSimulation::BizGameKey(const FString& Id)
{
 if(Id==TEXT("sorveteria"))return TEXT("icecream");
 if(Id==TEXT("food_truck"))return TEXT("pastel");
 if(Id==TEXT("aluguel"))return TEXT("rental");
 if(Id==TEXT("souvenir"))return TEXT("shop");
 return nullptr;
}

TSharedPtr<FJsonObject> UMareSimulation::BizState(const FString& Id) const{return Object(Object(Object(State,TEXT("prog")),TEXT("biz")),Id);}
int32 UMareSimulation::BusinessLevel(const FString& Id) const{return FMath::Clamp(int32(Number(BizState(Id),TEXT("lvl"))),0,3);}

TSharedPtr<FJsonObject> UMareSimulation::BizLevelDef(const FString& Id,int32 Level) const
{
 const TArray<TSharedPtr<FJsonValue>>* Levels=nullptr;
 if(Level>=2 && Object(Object(BusinessGames(),TEXT("businesses")),Id)->TryGetArrayField(TEXT("levels"),Levels) && Levels->IsValidIndex(Level-2))return (*Levels)[Level-2]->AsObject();
 return nullptr;
}

TSharedPtr<FJsonObject> UMareSimulation::BizGameDefs(const FString& Id) const
{
 const TCHAR* Key=BizGameKey(Id);const auto Base=Object(Object(Object(BusinessGames(),TEXT("businesses")),Id),Key?Key:TEXT("-"));
 const int32 Level=BusinessLevel(Id);if(Level<2)return Base;
 // Level 2 and 3 copy the base values and lay each level's "set" over them (cached: the data never changes in play).
 static TMap<FString,TSharedPtr<FJsonObject>> Cache;const FString CacheKey=FString::Printf(TEXT("%s#%d"),*Id,Level);
 if(const auto* Found=Cache.Find(CacheKey))return *Found;
 auto Merged=MakeShared<FJsonObject>();Merged->Values=Base->Values;
 for(int32 L=2;L<=Level;++L){const auto Def=BizLevelDef(Id,L);if(!Def.IsValid())continue;for(const auto& Pair:Object(Def,TEXT("set"))->Values)Merged->Values.Add(Pair.Key,Pair.Value);}
 Cache.Add(CacheKey,Merged);return Merged;
}

double UMareSimulation::BizPriceMult(const FString& Id) const
{
 const auto Def=BizLevelDef(Id,BusinessLevel(Id));return Def.IsValid()?Number(Def,TEXT("price_mult"),1):1;
}

bool UMareSimulation::CanUpgradeBusiness(const FString& Id,FString& Reason,double* Cost) const
{
 if(!OwnsBusiness(Id)){Reason=TEXT("O negócio ainda não é seu.");return false;}
 const int32 Level=BusinessLevel(Id);if(Level>=3){Reason=TEXT("Nível máximo.");return false;}
 const auto Def=BizLevelDef(Id,Level+1);if(!Def.IsValid()){Reason=TEXT("Sem melhorias para este negócio.");return false;}
 const double Price=Number(Def,TEXT("cost"));if(Cost)*Cost=Price;
 if(FameLevel()<Number(Def,TEXT("fame"))){Reason=FString::Printf(TEXT("Precisa de fama nível %.0f."),Number(Def,TEXT("fame")));return false;}
 if(Money()<Price){Reason=FString::Printf(TEXT("Faltam R$ %.0f."),Price-Money());return false;}
 return true;
}

bool UMareSimulation::UpgradeBusiness(const FString& Id)
{
 FString Reason;double Cost=0;if(!CanUpgradeBusiness(Id,Reason,&Cost))return Fail(Reason);
 const int32 Level=BusinessLevel(Id)+1;const auto Def=BizLevelDef(Id,Level);
 BizState(Id)->SetNumberField(TEXT("lvl"),Level);
 const FString Name=String(Object(Object(Definitions,TEXT("businesses")),Id),TEXT("name"));
 Book(-Cost,FString::Printf(TEXT("%s: nível %d (%s)"),*Name,Level,*String(Def,TEXT("name"))));
 LastMessage=FString::Printf(TEXT("%s agora é nível %d: %s. Preços ×%.2f, e o serviço ficou mais exigente."),*Name,Level,*String(Def,TEXT("name")),BizPriceMult(Id));
 return Save();
}

double UMareSimulation::BizClerkShare() const{return Number(BusinessGames(),TEXT("clerk_share"),.6);}

bool UMareSimulation::HasBizClerk(const FString& Id) const
{
 // Saves from before 3.6 paid every business's clerk: a missing flag means hired.
 if(!OwnsBusiness(Id))return false;bool bHired=true;BizState(Id)->TryGetBoolField(TEXT("clerk"),bHired);return bHired;
}

bool UMareSimulation::SetBizClerk(const FString& Id,bool bHire)
{
 if(!OwnsBusiness(Id))return Fail(TEXT("O negócio ainda não é seu."));
 const auto Def=Object(Object(Definitions,TEXT("businesses")),Id);BizState(Id)->SetBoolField(TEXT("clerk"),bHire);
 LastMessage=bHire?FString::Printf(TEXT("Funcionário contratado em %s: atende sozinho quem você não atender, com %.0f%% da renda. Salário R$ %.0f por dia."),*String(Def,TEXT("name")),BizClerkShare()*100,Number(Def,TEXT("wage")))
  :FString::Printf(TEXT("Funcionário de %s dispensado: agora só vende quando você atende."),*String(Def,TEXT("name")));
 return Save();
}

TSharedPtr<FJsonObject> UMareSimulation::BizReport(const FString& Id)
{
 // Today's numbers; a new day keeps the closed one as "report_prev" (the phone shows both).
 auto Biz=BizState(Id);const double Day=Number(State,TEXT("day"),1);auto R=Kid(Biz,TEXT("report"));
 if(Number(R,TEXT("day"),-1)!=Day){if(R->HasField(TEXT("day")))Biz->SetObjectField(TEXT("report_prev"),R);R=MakeShared<FJsonObject>();R->SetNumberField(TEXT("day"),Day);Biz->SetObjectField(TEXT("report"),R);}
 return R;
}

void UMareSimulation::BizBookToday(const FString& Id,double Amount)
{
 // Same ledger the phone's "hoje R$" reads (OperateHour resets it each day).
 auto Ops=Kid(State,TEXT("ue_ops"));const double Day=Number(State,TEXT("day"),1);
 if(Number(Ops,TEXT("day"),-1)!=Day){Ops->SetNumberField(TEXT("day"),Day);Ops->SetObjectField(TEXT("today"),MakeShared<FJsonObject>());}
 auto Today=Kid(Ops,TEXT("today"));const FString Place=TEXT("biz_")+Id;Today->SetNumberField(Place,Number(Today,Place)+Amount);
}

void UMareSimulation::BizServed(const FString& Id,bool bClerk,double Paid,int32 Hits,int32 Fame)
{
 auto R=BizReport(Id);const FString P=bClerk?TEXT("clerk"):TEXT("you");
 R->SetNumberField(P+TEXT("_n"),Number(R,P+TEXT("_n"))+1);R->SetNumberField(P+TEXT("_money"),Number(R,P+TEXT("_money"))+Paid);
 if(!bClerk){R->SetNumberField(TEXT("hits"),Number(R,TEXT("hits"))+Hits);R->SetNumberField(TEXT("fame"),Number(R,TEXT("fame"))+Fame);if(Hits>=3)R->SetNumberField(TEXT("perfect"),Number(R,TEXT("perfect"))+1);}
 if(Paid>0)BizBookToday(Id,Paid);
}

void UMareSimulation::BizShelfSale(const FString& Id,double Paid)
{
 auto R=BizReport(Id);R->SetNumberField(TEXT("shelf_money"),Number(R,TEXT("shelf_money"))+Paid);if(Paid>0)BizBookToday(Id,Paid);
}

void UMareSimulation::BizLost(const FString& Id,int32 People)
{
 if(People<=0)return;auto R=BizReport(Id);R->SetNumberField(TEXT("lost"),Number(R,TEXT("lost"))+People);
}

FString UMareSimulation::BizReportLine(const FString& Id,bool bYesterday) const
{
 const auto Biz=BizState(Id);const double Day=Number(State,TEXT("day"),1);
 auto R=Object(Biz,TEXT("report"));
 // Yesterday is "report" itself while nothing was booked today yet, else the copy kept when today started.
 if(bYesterday){if(Number(R,TEXT("day"),-1)!=Day-1)R=Object(Biz,TEXT("report_prev"));if(Number(R,TEXT("day"),-1)!=Day-1)return TEXT("Ontem: sem movimento.");}
 else if(Number(R,TEXT("day"),-1)!=Day)return TEXT("Hoje: nenhum cliente ainda.");
 TArray<FString> Parts;const int32 You=int32(Number(R,TEXT("you_n"))),Clerk=int32(Number(R,TEXT("clerk_n"))),Lost=int32(Number(R,TEXT("lost")));
 if(You)Parts.Add(FString::Printf(TEXT("você atendeu %d (R$ %.0f, nota %.1f/3, %d perfeito(s), +%.0f fama)"),You,Number(R,TEXT("you_money")),Number(R,TEXT("hits"))/You,int32(Number(R,TEXT("perfect"))),Number(R,TEXT("fame"))));
 if(Clerk)Parts.Add(FString::Printf(TEXT("funcionário %d (R$ %.0f)"),Clerk,Number(R,TEXT("clerk_money"))));
 if(Number(R,TEXT("shelf_money"))>0)Parts.Add(FString::Printf(TEXT("prateleira R$ %.0f"),Number(R,TEXT("shelf_money"))));
 if(Lost)Parts.Add(FString::Printf(TEXT("%d desistiram da fila"),Lost));
 const double Total=Number(R,TEXT("you_money"))+Number(R,TEXT("clerk_money"))+Number(R,TEXT("shelf_money"));
 return FString(bYesterday?TEXT("Ontem: "):TEXT("Hoje: "))+(Parts.IsEmpty()?FString(TEXT("nenhum cliente")):FString::Join(Parts,TEXT(" · ")))+FString::Printf(TEXT(" · total R$ %.0f"),Total);
}
