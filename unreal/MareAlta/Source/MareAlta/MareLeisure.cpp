// Fishing at the pier and the photo album: the player's own leisure, feeding the village chapters
// (Seu Gregory's fish, Padre Robson's lighthouse photo). Content/Data/leisure.json.
#include "MareSimulation.h"
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
