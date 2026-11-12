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

int32 UMareSimulation::BaitCount(const FString& Bait) const
{
 if(Bait.IsEmpty() || Bait==TEXT("massa"))return 9999;   // bread dough: free and endless   // i18n:skip
 return int32(Number(Object(Object(State,TEXT("prog")),TEXT("bait")),Bait));   // i18n:skip
}

bool UMareSimulation::BuyBait(const FString& Bait)
{
 const TArray<TSharedPtr<FJsonValue>>* Baits=nullptr;if(!LeisureDefs()->TryGetArrayField(TEXT("baits"),Baits))return false;   // i18n:skip
 for(const auto& V:*Baits){const auto B=V->AsObject();if(String(B,TEXT("id"))!=Bait)continue;
  const double Cost=Number(B,TEXT("cost"));const int32 Pack=int32(Number(B,TEXT("pack")));   // i18n:skip
  if(Pack<=0){LastMessage=TEXT("Essa isca não precisa comprar.");return false;}
  if(Money()<Cost){LastMessage=FString::Printf(TEXT("Faltam R$ %.0f para a isca."),Cost-Money());return false;}
  Book(-Cost,TEXT("Isca de pesca"));
  auto Store=Object(Object(State,TEXT("prog")),TEXT("bait"));Store->SetNumberField(Bait,Number(Store,Bait)+Pack);   // i18n:skip
  LastMessage=FString::Printf(TEXT("Comprou %d iscas: %s."),Pack,*String(B,TEXT("name")));Save();return true;}
 return false;
}

TSharedPtr<FJsonObject> UMareSimulation::HookFish(const FString& InBait,bool& bOk)
{
 const FString Bait=InBait.IsEmpty()?FString(TEXT("massa")):InBait;bOk=false;   // i18n:skip
 const TArray<TSharedPtr<FJsonValue>>* Species=nullptr;if(!LeisureDefs()->TryGetArrayField(TEXT("species"),Species) || Species->IsEmpty())return nullptr;
 if(BaitCount(Bait)<=0){LastMessage=TEXT("Acabou essa isca.");return nullptr;}
 if(Bait!=TEXT("massa")){auto Store=Object(Object(State,TEXT("prog")),TEXT("bait"));Store->SetNumberField(Bait,FMath::Max(0.,Number(Store,Bait)-1));}   // i18n:skip
 const double Hour=FMath::Fmod(Number(State,TEXT("minutes")),1440.)/60.;
 auto Weight=[&](const TSharedPtr<FJsonObject>& F){
  const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;
  if(F->TryGetArrayField(TEXT("hours"),Hours) && Hours->Num()==2 && (Hour<(*Hours)[0]->AsNumber() || Hour>=(*Hours)[1]->AsNumber()))return 0.;
  const TSharedPtr<FJsonObject>* Mult=nullptr;double M=1;if(F->TryGetObjectField(TEXT("bait"),Mult))M=Number(*Mult,Bait,1);   // i18n:skip
  return Number(F,TEXT("weight"),1)*M;};
 double Total=0;for(const auto& V:*Species)Total+=Weight(V->AsObject());
 double Roll=FMath::FRand()*Total;TSharedPtr<FJsonObject> Fish=(*Species)[0]->AsObject();
 for(const auto& V:*Species){const double W=Weight(V->AsObject());if(W<=0)continue;Roll-=W;if(Roll<=0){Fish=V->AsObject();break;}}
 const TArray<TSharedPtr<FJsonValue>>* Size=nullptr;double Cm=30,Big=.5;
 if(Fish->TryGetArrayField(TEXT("cm"),Size) && Size->Num()==2){const double Lo=(*Size)[0]->AsNumber(),Hi=(*Size)[1]->AsNumber();
  Cm=FMath::RoundToDouble(FMath::FRandRange(Lo,Hi));Big=Hi>Lo?(Cm-Lo)/(Hi-Lo):.5;}
 auto Hooked=MakeShared<FJsonObject>();Hooked->SetStringField(TEXT("id"),String(Fish,TEXT("id")));Hooked->SetStringField(TEXT("name"),String(Fish,TEXT("name")));
 Hooked->SetNumberField(TEXT("cm"),Cm);Hooked->SetNumberField(TEXT("strength"),FMath::Clamp(Number(Fish,TEXT("strength"),.3)+.15*Big,0.,1.));   // i18n:skip
 bOk=true;return Hooked;
}

int32 UMareSimulation::SpeciesTotal() const
{
 const TArray<TSharedPtr<FJsonValue>>* Species=nullptr;return LeisureDefs()->TryGetArrayField(TEXT("species"),Species)?Species->Num():0;
}

int32 UMareSimulation::SpeciesCaught() const
{
 int32 N=0;const auto Log=Object(Object(State,TEXT("prog")),TEXT("fish"));const TArray<TSharedPtr<FJsonValue>>* Species=nullptr;
 if(LeisureDefs()->TryGetArrayField(TEXT("species"),Species))for(const auto& V:*Species)N+=Number(Log,String(V->AsObject(),TEXT("id")))>0;
 return N;
}

bool UMareSimulation::LandFish(const TSharedPtr<FJsonObject>& Fish)
{
 if(!Fish.IsValid())return false;
 // The catch goes to the stock as 'peixe' (the chapter delivers from there) and into the fishing log.
 auto Stock=Object(State,TEXT("stock"));Stock->SetNumberField(TEXT("peixe"),Number(Stock,TEXT("peixe"))+1);
 auto Log=Object(Object(State,TEXT("prog")),TEXT("fish"));const FString Id=String(Fish,TEXT("id"));const double Cm=Number(Fish,TEXT("cm"),30);
 const bool bNew=Number(Log,Id)<=0;const bool bRecord=!bNew && Cm>Number(Log,TEXT("best_")+Id);const int32 Before=SpeciesCaught();
 Log->SetNumberField(Id,Number(Log,Id)+1);Log->SetNumberField(TEXT("best_")+Id,FMath::Max(Number(Log,TEXT("best_")+Id),Cm));
 AddFame((Id==TEXT("garoupa")?10:2)+(bNew?int32(Number(LeisureDefs(),TEXT("first_fame"),5)):0));
 LastMessage=FString::Printf(TEXT("Pegou um(a) %s de %.0f cm! (peixes no estoque: %.0f)"),*String(Fish,TEXT("name")),Cm,Number(Stock,TEXT("peixe")));
 if(bNew)LastMessage+=TEXT(" Espécie nova no livro!");else if(bRecord)LastMessage+=TEXT(" Novo recorde!");
 // The whole book: a one-time prize from the fishermen.
 if(bNew && Before+1==SpeciesTotal() && SpeciesTotal()>0){const double Prize=Number(LeisureDefs(),TEXT("book_reward"),300);
  Book(Prize,TEXT("Livro de espécies completo"));LastMessage+=FString::Printf(TEXT(" Livro de espécies completo: os pescadores deram R$ %.0f!"),Prize);}
 Save();return bNew;
}

FString UMareSimulation::CatchFish()
{
 // The old one-step catch (tests, chapter QA): bread dough, no fight.
 bool bOk=false;const auto Fish=HookFish(TEXT("massa"),bOk);if(!bOk || !Fish.IsValid())return FString();   // i18n:skip
 LandFish(Fish);return String(Fish,TEXT("id"));
}

bool UMareSimulation::PhotoChallengeDone(const FString& Id) const
{
 bool bDone=false;Object(Object(State,TEXT("prog")),TEXT("photo_ch"))->TryGetBoolField(Id,bDone);return bDone;
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
 // 11/11 photo challenges: one-time goals met by a single photo (all the listed subjects, or `count` different ones).
 {const TArray<TSharedPtr<FJsonValue>>* Challenges=nullptr;auto Done=Object(Prog,TEXT("photo_ch"));
  if(LeisureDefs()->TryGetArrayField(TEXT("photo_challenges"),Challenges))for(const auto& V:*Challenges){const auto C=V->AsObject();const FString Id=String(C,TEXT("id"));
   bool bHad=false;Done->TryGetBoolField(Id,bHad);if(bHad)continue;
   bool bMet=true;const TArray<TSharedPtr<FJsonValue>>* All=nullptr;
   if(C->TryGetArrayField(TEXT("all"),All)){for(const auto& A:*All)bMet&=Subjects.Contains(A->AsString());bMet&=All->Num()>0;}   // i18n:skip
   else bMet=Subjects.Num()>=int32(Number(C,TEXT("count"),99));
   if(!bMet)continue;
   Done->SetBoolField(Id,true);const double Prize=Number(C,TEXT("money"));if(Prize>0)Book(Prize,TEXT("Desafio de foto"));AddFame(int32(Number(C,TEXT("fame"))));
   LastMessage+=FString::Printf(TEXT(" Desafio de foto cumprido: %s (+R$ %.0f)"),*String(C,TEXT("text")),Prize);}
  // The player learns the challenges by taking photos: every photo names the next one still open.
  if(Challenges)for(const auto& V:*Challenges){bool bHad=false;Done->TryGetBoolField(String(V->AsObject(),TEXT("id")),bHad);
   if(!bHad){LastMessage+=FString::Printf(TEXT(" Próximo desafio de foto: %s."),*String(V->AsObject(),TEXT("text")));break;}}}
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
