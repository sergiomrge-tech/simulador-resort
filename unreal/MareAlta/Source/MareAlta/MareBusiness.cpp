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
 const auto Def=Object(Object(Definitions,TEXT("businesses")),Id);const auto Game=Object(Object(BusinessGames(),TEXT("businesses")),Id);
 if(!(Def->HasField(TEXT("open"))?Def:Game)->TryGetArrayField(TEXT("open"),Open) || Open->Num()!=2)return false;
 return Hour>=(*Open)[0]->AsNumber() && Hour<(*Open)[1]->AsNumber();
}

bool UMareSimulation::CanPlayBusiness(const FString& Id,FString& Reason) const
{
 const auto Game=Object(Object(BusinessGames(),TEXT("businesses")),Id);const FString Requires=String(Game,TEXT("requires"));
 if(!Requires.IsEmpty()){bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(Requires,bOwned);if(!bOwned){Reason=TEXT("Compre o salão de jogos do hotel.");return false;}}
 else if(!OwnsBusiness(Id)){Reason=TEXT("O negócio ainda não é seu.");return false;}
 if(!IsBusinessOpen(Id)){const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;(Requires.IsEmpty()?Object(Object(Definitions,TEXT("businesses")),Id):Game)->TryGetArrayField(TEXT("open"),Open);
  Reason=Open && Open->Num()==2?FString::Printf(TEXT("Fechado agora (abre das %.0fh às %.0fh)."),(*Open)[0]->AsNumber(),(*Open)[1]->AsNumber()):TEXT("Fechado agora.");return false;}
 // The ice cream shop works by its queue (3.1): one cone per customer in line, not one task per hour.
 if(Id==TEXT("sorveteria")){if(IceQueue().IsEmpty()){Reason=TEXT("Ninguém na fila da sorveteria agora.");return false;}return true;}
 if(Id==TEXT("aluguel")){if(RentalQueue().IsEmpty() && RentalReturns().IsEmpty()){Reason=TEXT("Ninguém para alugar nem devolver agora.");return false;}return true;}
 if(Id==TEXT("food_truck")){if(PastelQueue().IsEmpty()){Reason=TEXT("Ninguém na fila do pastel agora.");return false;}return true;}
 // The souvenir shop is always open to manage (shelf, makers, postcards); the gift line is served inside it (3.5).
 if(Id==TEXT("souvenir"))return true;
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
 const auto Game=Object(Object(BusinessGames(),TEXT("businesses")),Id);const bool bMachine=!String(Game,TEXT("requires")).IsEmpty();
 const auto Def=bMachine?Game:Object(Object(Definitions,TEXT("businesses")),Id);
 const TArray<TSharedPtr<FJsonValue>>* Rewards=nullptr;Hits=FMath::Clamp(Hits,0,3);
 const double Factor=BusinessGames()->TryGetArrayField(TEXT("rewards"),Rewards) && Rewards->IsValidIndex(Hits)?(*Rewards)[Hits]->AsNumber():.3+.6*Hits;
 // Game-room machines pay their own base (a bet won against a guest, tokens of the players watching).
 const double Reward=FMath::RoundToDouble((bMachine?Number(Game,TEXT("base")):FMath::Max(BusinessRate(Id),Number(Def,TEXT("hour"))))*Factor);
 Book(Reward,FString::Printf(TEXT("%s: atendimento (%d/3)"),*String(Def,TEXT("name")),Hits));
 AddFame(int32(Number(BusinessGames(),TEXT("fame_per_hit"),2))*Hits);
 LastMessage=Hits==3?FString::Printf(TEXT("Perfeito! Cliente encantado: R$ %.0f."),Reward):Hits>0?FString::Printf(TEXT("Cliente atendido: R$ %.0f."),Reward)
  :FString::Printf(TEXT("Saiu meio torto... R$ %.0f."),Reward);
 Save();return Reward;
}

void UMareSimulation::GameRoomHour(int32 Hour)
{
 // Night tokens: guests play foosball and the arcades between the token hours, more when the hotel is full.
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("salao_jogos"),bOwned);if(!bOwned)return;
 const auto Room=Object(BusinessGames(),TEXT("game_room"));const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const TArray<TSharedPtr<FJsonValue>>* Players=nullptr;
 if(!Room->TryGetArrayField(TEXT("token_hours"),Hours) || Hours->Num()!=2)return;
 const int32 Started=Hour-1;if(Started<(*Hours)[0]->AsNumber() || Started>=(*Hours)[1]->AsNumber())return;
 int32 Low=2,High=6;if(Room->TryGetArrayField(TEXT("night_players"),Players) && Players->Num()==2){Low=int32((*Players)[0]->AsNumber());High=int32((*Players)[1]->AsNumber());}
 const int32 Guests=FMath::RoundToInt(FMath::Lerp(double(Low),double(High),FMath::Clamp(double(RoomsOccupied())/FMath::Max(1,RoomsTotal()),0.,1.)));
 const double Tokens=Guests*Number(Room,TEXT("token_price"),5)*FMath::FRandRange(.8,1.2);
 if(Tokens>=1){Book(FMath::RoundToDouble(Tokens),FString::Printf(TEXT("Salão de jogos: fichas (%d jogadores)"),Guests));
  auto Today=Object(Object(State,TEXT("ue_ops")),TEXT("today"));Today->SetNumberField(TEXT("salao_jogos"),Number(Today,TEXT("salao_jogos"))+FMath::RoundToDouble(Tokens));}
}
