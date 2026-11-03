// Pool (sinuca) beyond a single match (03/11, "sinuca como jogo completo"): the opponents of the game room, the
// player's record and the Campeonato da Maré, an 8-player knockout with one round per game day. The player's matches
// are real games at the table (UMareGameRoom); the other matches of each round are decided by the players' skill.
// Data in Content/Data/game_room.json (players, stakes, cup); state in the save under "billiards".
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
 TArray<FString> Strings(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  TArray<FString> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(Parent->TryGetArrayField(Key,L))for(const auto& V:*L)Out.Add(V->AsString());return Out;
 }
 void SetStrings(const TSharedPtr<FJsonObject>& Parent,const FString& Key,const TArray<FString>& Values)
 {
  TArray<TSharedPtr<FJsonValue>> L;for(const auto& V:Values)L.Add(MakeShared<FJsonValueString>(V));Parent->SetArrayField(Key,L);
 }
}

const FString UMareSimulation::PoolYou=TEXT("Você");

TSharedPtr<FJsonObject> UMareSimulation::GameRoomDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/game_room.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

TArray<FString> UMareSimulation::PoolPlayers() const
{
 TArray<FString> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
 if(GameRoomDefs()->TryGetArrayField(TEXT("players"),L))for(const auto& V:*L)Out.Add(String(V->AsObject(),TEXT("name")));
 return Out;
}

TSharedPtr<FJsonObject> UMareSimulation::PoolPlayer(const FString& Name) const
{
 const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
 if(GameRoomDefs()->TryGetArrayField(TEXT("players"),L))for(const auto& V:*L)if(String(V->AsObject(),TEXT("name"))==Name)return V->AsObject();
 return MakeShared<FJsonObject>();
}

FString UMareSimulation::PoolLevel(const FString& Name) const
{
 const double Skill=Number(PoolPlayer(Name),TEXT("skill"),2);
 return Skill>=2.5?TEXT("iniciante"):Skill>=1.7?TEXT("médio"):Skill>=1.0?TEXT("bom"):TEXT("craque");
}

TSharedPtr<FJsonObject> UMareSimulation::Billiards(){return Child(State,TEXT("billiards"));}

void UMareSimulation::PoolRecord(bool bWon)
{
 auto B=Billiards();B->SetNumberField(TEXT("played"),Number(B,TEXT("played"))+1);if(bWon)B->SetNumberField(TEXT("won"),Number(B,TEXT("won"))+1);Save();
}

void UMareSimulation::RecordGame(const FString& Key,bool bWon)
{
 auto B=Child(State,Key);B->SetNumberField(TEXT("played"),Number(B,TEXT("played"))+1);if(bWon)B->SetNumberField(TEXT("won"),Number(B,TEXT("won"))+1);Save();
}

bool UMareSimulation::PoolCupActive() const
{
 bool bActive=false;Object(Object(State,TEXT("billiards")),TEXT("cup"))->TryGetBoolField(TEXT("active"),bActive);return bActive;
}

TArray<FString> UMareSimulation::PoolCupAlive() const{return Strings(Object(Object(State,TEXT("billiards")),TEXT("cup")),TEXT("alive"));}

FString UMareSimulation::PoolCupRoundName() const
{
 const int32 N=PoolCupAlive().Num();return N>=8?TEXT("quartas de final"):N>=4?TEXT("semifinal"):TEXT("final");
}

bool UMareSimulation::PoolCupJoin()
{
 if(PoolCupActive())return Fail(TEXT("O campeonato já está em andamento."));
 const auto Cup=Object(GameRoomDefs(),TEXT("cup"));const double Fee=Number(Cup,TEXT("fee"),50);
 if(Money()<Fee)return Fail(FString::Printf(TEXT("Saldo insuficiente: a inscrição custa R$ %.0f."),Fee));
 TArray<FString> Field=PoolPlayers();
 for(int32 I=Field.Num()-1;I>0;--I)Field.Swap(I,FMath::RandRange(0,I));
 Field.SetNum(FMath::Min(Field.Num(),7));
 // The player gets a random slot in the bracket.
 Field.Insert(PoolYou,FMath::RandRange(0,Field.Num()));
 auto C=Child(Billiards(),TEXT("cup"));C->SetBoolField(TEXT("active"),true);SetStrings(C,TEXT("alive"),Field);
 C->SetNumberField(TEXT("played_day"),-1);SetStrings(C,TEXT("log"),{});
 Book(-Fee,TEXT("Inscrição: ")+String(Cup,TEXT("name")));
 LastMessage=String(Cup,TEXT("name"))+TEXT(": inscrição feita! Uma rodada por dia, aqui na mesa.");return Save();
}

FString UMareSimulation::PoolCupOpponent() const
{
 const TArray<FString> Alive=PoolCupAlive();const int32 Me=Alive.IndexOfByKey(PoolYou);
 if(!PoolCupActive() || Me==INDEX_NONE)return FString();
 const int32 Other=Me%2==0?Me+1:Me-1;return Alive.IsValidIndex(Other)?Alive[Other]:FString();
}

bool UMareSimulation::PoolCupReady(FString& Why) const
{
 if(!PoolCupActive()){Why=TEXT("Sem campeonato em andamento.");return false;}
 if(PoolCupOpponent().IsEmpty()){Why=TEXT("Você foi eliminado.");return false;}
 if(int32(Number(Object(Object(State,TEXT("billiards")),TEXT("cup")),TEXT("played_day"),-1))==int32(Number(State,TEXT("day"),1))){
  Why=TEXT("A próxima rodada é amanhã.");return false;}
 return true;
}

void UMareSimulation::PoolCupResult(bool bWon)
{
 if(!PoolCupActive())return;
 auto C=Child(Billiards(),TEXT("cup"));const auto Cup=Object(GameRoomDefs(),TEXT("cup"));
 TArray<FString> Alive=PoolCupAlive(),Next,Log=Strings(C,TEXT("log"));const FString Round=PoolCupRoundName();
 for(int32 I=0;I+1<Alive.Num();I+=2){const FString& A=Alive[I];const FString& B=Alive[I+1];FString Winner;
  if(A==PoolYou || B==PoolYou)Winner=bWon?PoolYou:(A==PoolYou?B:A);
  else{// Other matches: the better player (smaller aim error) wins more often, never always.
   const double Ea=Number(PoolPlayer(A),TEXT("skill"),2),Eb=Number(PoolPlayer(B),TEXT("skill"),2);
   Winner=FMath::FRand()<1/(1+FMath::Exp((Ea-Eb)*1.6))?A:B;}
  Next.Add(Winner);Log.Add(Round+TEXT(": ")+A+TEXT(" × ")+B+TEXT(" → ")+Winner);}
 SetStrings(C,TEXT("log"),Log);C->SetNumberField(TEXT("played_day"),Number(State,TEXT("day"),1));
 const FString Name=String(Cup,TEXT("name"));
 if(Next.Num()<=1){// Final played: the cup ends.
  C->SetBoolField(TEXT("active"),false);SetStrings(C,TEXT("alive"),Next);
  if(bWon){const double Prize=Number(Cup,TEXT("prize"),600);Book(Prize,TEXT("Prêmio: ")+Name);AddFame(int32(Number(Cup,TEXT("fame"),10)));
   auto B=Billiards();B->SetNumberField(TEXT("cups"),Number(B,TEXT("cups"))+1);
   LastMessage=FString::Printf(TEXT("Campeão do %s! Troféu na estante e R$ %.0f de prêmio."),*Name,Prize);}
  else{const double Second=Number(Cup,TEXT("runner_up"),150);Book(Second,TEXT("Vice: ")+Name);
   LastMessage=FString::Printf(TEXT("Vice-campeão do %s: R$ %.0f. Campeão: %s."),*Name,Second,Next.Num()?*Next[0]:TEXT("?"));}}
 else{SetStrings(C,TEXT("alive"),Next);
  if(!Next.Contains(PoolYou)){C->SetBoolField(TEXT("active"),false);LastMessage=TEXT("Eliminado do ")+Name+TEXT(" na ")+Round+TEXT(". Inscreva-se de novo quando quiser.");}
  else LastMessage=TEXT("Você passou de fase! Próxima: ")+PoolCupRoundName()+TEXT(", amanhã.");}
 Save();
}
