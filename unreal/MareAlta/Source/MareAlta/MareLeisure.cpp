// Fishing at the pier and the photo album: the player's own leisure, feeding the village chapters
// (Seu Severino's fish, Padre Robson's lighthouse photo). Content/Data/leisure.json.
#include "MareSimulation.h"
#include "MareOptions.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TSharedPtr<FJsonObject> UMareSimulation::LeisureDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/leisure.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

FString UMareSimulation::CatchFish()
{
 const TArray<TSharedPtr<FJsonValue>>* Species=nullptr;if(!LeisureDefs()->TryGetArrayField(TEXT("species"),Species) || Species->IsEmpty())return FString();
 double Total=0;for(const auto& V:*Species)Total+=Number(V->AsObject(),TEXT("weight"),1);
 double Roll=FMath::FRand()*Total;TSharedPtr<FJsonObject> Fish=(*Species)[0]->AsObject();
 for(const auto& V:*Species){Roll-=Number(V->AsObject(),TEXT("weight"),1);if(Roll<=0){Fish=V->AsObject();break;}}
 const TArray<TSharedPtr<FJsonValue>>* Size=nullptr;double Cm=30;
 if(Fish->TryGetArrayField(TEXT("cm"),Size) && Size->Num()==2)Cm=FMath::RoundToDouble(FMath::FRandRange((*Size)[0]->AsNumber(),(*Size)[1]->AsNumber()));
 // The catch goes to the stock as 'peixe' (the chapter delivers from there) and into the fishing log.
 auto Stock=Object(State,TEXT("stock"));Stock->SetNumberField(TEXT("peixe"),Number(Stock,TEXT("peixe"))+1);
 auto Log=Object(Object(State,TEXT("prog")),TEXT("fish"));const FString Id=String(Fish,TEXT("id"));
 Log->SetNumberField(Id,Number(Log,Id)+1);Log->SetNumberField(TEXT("best_")+Id,FMath::Max(Number(Log,TEXT("best_")+Id),Cm));
 AddFame(Id==TEXT("garoupa")?10:2);
 LastMessage=FString::Printf(TEXT("Pegou um(a) %s de %.0f cm! (peixes no estoque: %.0f)"),*String(Fish,TEXT("name")),Cm,Number(Stock,TEXT("peixe")));
 Save();return Id;
}

int32 UMareSimulation::RecordPhoto(const TArray<FString>& Subjects,const FString& File)
{
 auto Prog=Object(State,TEXT("prog"));auto Flags=Object(Prog,TEXT("chp"));
 TArray<TSharedPtr<FJsonValue>> Album;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(Prog->TryGetArrayField(TEXT("album"),Existing))Album=*Existing;
 int32 New=0;TArray<FString> Names;
 for(const FString& Id:Subjects){bool bHad=false;Flags->TryGetBoolField(Id,bHad);if(!bHad){Flags->SetBoolField(Id,true);++New;}
  const TArray<TSharedPtr<FJsonValue>>* List=nullptr;if(LeisureDefs()->TryGetArrayField(TEXT("photo_subjects"),List))
   for(const auto& V:*List)if(String(V->AsObject(),TEXT("id"))==Id)Names.Add(String(V->AsObject(),TEXT("name")));}
 auto Photo=MakeShared<FJsonObject>();Photo->SetStringField(TEXT("file"),File);Photo->SetNumberField(TEXT("day"),Number(State,TEXT("day"),1));
 Photo->SetNumberField(TEXT("minutes"),Number(State,TEXT("minutes")));
 TArray<TSharedPtr<FJsonValue>> Tags;for(const FString& Id:Subjects)Tags.Add(MakeShared<FJsonValueString>(Id));Photo->SetArrayField(TEXT("subjects"),Tags);
 Album.Add(MakeShared<FJsonValueObject>(Photo));while(Album.Num()>200)Album.RemoveAt(0);Prog->SetArrayField(TEXT("album"),Album);
 if(New)AddFame(3*New);
 LastMessage=Names.Num()?TEXT("Foto salva no álbum: ")+FString::Join(Names,TEXT(", "))+(New?TEXT(" (novo!)"):TEXT("")):TEXT("Foto salva no álbum.");
 Save();return New;
}

int32 UMareSimulation::BarDiscoveries() const
{
 // Recipes found by mixing (not on the starting menu) count for the "sabores" chapter.
 int32 N=0;const TArray<TSharedPtr<FJsonValue>>* Known=nullptr;
 if(Object(State,TEXT("bar"))->TryGetArrayField(TEXT("known"),Known))for(const auto& V:*Known){bool bStart=false;if(auto R=BarRecipe(V->AsString()))R->TryGetBoolField(TEXT("known"),bStart);N+=!bStart;}
 return N;
}

bool UMareSimulation::ShowTip(const FString& Key)
{
 static TSharedPtr<FJsonObject> Tips;
 if(!Tips.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/tutorial.json")));
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Tips);if(!Tips.IsValid())Tips=MakeShared<FJsonObject>();}
 const auto Tip=Object(Object(Tips,TEXT("tips")),Key);if(!Tip->Values.Num())return false;
 if(!FMareOptions::Get().bTips)return false;   // tips switched off in the options (not marked as seen)
 auto Seen=Object(Object(State,TEXT("prog")),TEXT("tips"));bool bSeen=false;Seen->TryGetBoolField(Key,bSeen);if(bSeen)return false;
 Seen->SetBoolField(Key,true);PendingTipTitle=String(Tip,TEXT("title"));PendingTipText=String(Tip,TEXT("text"));return true;
}

FString UMareSimulation::NextUnlockText() const
{
 // The cheapest expansion whose prerequisites are owned (as NextGoal), with what is still missing for it.
 auto Unlocked=Object(State,TEXT("unlocked"));TSharedPtr<FJsonObject> Best;double BestCost=0;
 for(const auto& Pair:Object(Definitions,TEXT("expansions"))->Values){const auto E=Pair.Value->AsObject();const FString Id(Pair.Key.ToView());
  bool bOwned=false;Unlocked->TryGetBoolField(Id,bOwned);if(bOwned || IsFullGameOnly(Id))continue;bool bReady=true;const TArray<TSharedPtr<FJsonValue>>* Req=nullptr;
  if(E->TryGetArrayField(TEXT("req"),Req))for(const auto& R:*Req){bool b=false;Unlocked->TryGetBoolField(R->AsString(),b);bReady&=b;}
  if(!bReady)continue;const double Price=Number(E,TEXT("cost"));if(!Best.IsValid() || Price<BestCost){Best=E;BestCost=Price;}}
 if(!Best.IsValid())return FString();
 TArray<FString> Missing;
 if(Money()<BestCost)Missing.Add(FString::Printf(TEXT("R$ %.0f"),FMath::CeilToDouble(BestCost-Money())));
 const int32 Fame=int32(Number(Best,TEXT("fame")));if(Fame>0 && FameLevel()<Fame)Missing.Add(FString::Printf(TEXT("fama %d"),Fame));
 FString Story;const FString Chapter=String(Best,TEXT("chapter"));
 if(!Chapter.IsEmpty() && !IsChapterDone(Chapter))Story=TEXT("a história \"")+String(ChapterDefinition(Chapter),TEXT("title"))+TEXT("\"");
 const FString Head=TEXT("Próximo desbloqueio: ")+String(Best,TEXT("name"));
 if(Missing.IsEmpty() && Story.IsEmpty())return Head+TEXT(" · já dá para comprar no celular");
 FString Line=Head+TEXT(" · ");
 if(Missing.Num())Line+=TEXT("faltam ")+FString::Join(Missing,TEXT(" e "));
 if(!Story.IsEmpty())Line+=(Missing.Num()?TEXT(" e "):TEXT(""))+FString(TEXT("conclua "))+Story;
 return Line;
}

bool UMareSimulation::NextGoal(FString& Name,double& Cost) const
{
 // The cheapest expansion whose prerequisites are owned: the next thing worth saving for.
 auto Unlocked=Object(State,TEXT("unlocked"));Cost=0;Name.Reset();
 for(const auto& Pair:Object(Definitions,TEXT("expansions"))->Values){const auto E=Pair.Value->AsObject();const FString Id(Pair.Key.ToView());
  bool bOwned=false;Unlocked->TryGetBoolField(Id,bOwned);if(bOwned || IsFullGameOnly(Id))continue;bool bReady=true;const TArray<TSharedPtr<FJsonValue>>* Req=nullptr;
  if(E->TryGetArrayField(TEXT("req"),Req))for(const auto& R:*Req){bool b=false;Unlocked->TryGetBoolField(R->AsString(),b);bReady&=b;}
  if(!bReady)continue;const double Price=Number(E,TEXT("cost"));if(Name.IsEmpty() || Price<Cost){Name=String(E,TEXT("name"));Cost=Price;}}
 return !Name.IsEmpty();
}
