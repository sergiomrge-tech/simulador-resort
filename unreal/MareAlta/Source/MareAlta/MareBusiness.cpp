// Village businesses, hands-on: once per hour of opening, the owner can serve at the counter in a three-round
// timing task (port of the Godot minigame). Reward and fame grow with the hits; the passive hourly income stays.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TSharedPtr<FJsonObject> UMareSimulation::BusinessGames() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/business_games.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

bool UMareSimulation::IsBusinessOpen(const FString& Id) const
{
 const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;const double Hour=Number(State,TEXT("minutes"))/60;
 if(!Object(Object(Definitions,TEXT("businesses")),Id)->TryGetArrayField(TEXT("open"),Open) || Open->Num()!=2)return false;
 return Hour>=(*Open)[0]->AsNumber() && Hour<(*Open)[1]->AsNumber();
}

bool UMareSimulation::CanPlayBusiness(const FString& Id,FString& Reason) const
{
 if(!OwnsBusiness(Id)){Reason=TEXT("O negócio ainda não é seu.");return false;}
 if(!IsBusinessOpen(Id)){const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;Object(Object(Definitions,TEXT("businesses")),Id)->TryGetArrayField(TEXT("open"),Open);
  Reason=Open && Open->Num()==2?FString::Printf(TEXT("Fechado agora (abre das %.0fh às %.0fh)."),(*Open)[0]->AsNumber(),(*Open)[1]->AsNumber()):TEXT("Fechado agora.");return false;}
 const int32 Hour=int32(Number(State,TEXT("day"),1))*24+FMath::FloorToInt(Number(State,TEXT("minutes"))/60);
 if(Number(Object(Object(Object(State,TEXT("prog")),TEXT("biz")),Id),TEXT("games_hour"),-1)>=Hour){Reason=TEXT("Cliente atendido. O próximo chega na próxima hora.");return false;}
 return true;
}

double UMareSimulation::PlayBusiness(const FString& Id,int32 Hits)
{
 FString Reason;if(!CanPlayBusiness(Id,Reason)){Fail(Reason);return 0;}
 auto Biz=Object(Object(Object(State,TEXT("prog")),TEXT("biz")),Id);
 Biz->SetNumberField(TEXT("games_hour"),int32(Number(State,TEXT("day"),1))*24+FMath::FloorToInt(Number(State,TEXT("minutes"))/60));
 Biz->SetNumberField(TEXT("games"),Number(Biz,TEXT("games"))+1);
 const auto Def=Object(Object(Definitions,TEXT("businesses")),Id);
 const TArray<TSharedPtr<FJsonValue>>* Rewards=nullptr;Hits=FMath::Clamp(Hits,0,3);
 const double Factor=BusinessGames()->TryGetArrayField(TEXT("rewards"),Rewards) && Rewards->IsValidIndex(Hits)?(*Rewards)[Hits]->AsNumber():.3+.6*Hits;
 const double Reward=FMath::RoundToDouble(FMath::Max(BusinessRate(Id),Number(Def,TEXT("hour")))*Factor);
 Book(Reward,FString::Printf(TEXT("%s: atendimento (%d/3)"),*String(Def,TEXT("name")),Hits));
 AddFame(int32(Number(BusinessGames(),TEXT("fame_per_hit"),2))*Hits);
 LastMessage=Hits==3?FString::Printf(TEXT("Perfeito! Cliente encantado: R$ %.0f."),Reward):Hits>0?FString::Printf(TEXT("Cliente atendido: R$ %.0f."),Reward)
  :FString::Printf(TEXT("Saiu meio torto... R$ %.0f."),Reward);
 Save();return Reward;
}
