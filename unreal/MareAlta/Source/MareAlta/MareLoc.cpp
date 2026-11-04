#include "MareLoc.h"
#include "Internationalization/Culture.h"
#include "Internationalization/Internationalization.h"
#include "Internationalization/PolyglotTextData.h"
#include "Internationalization/TextLocalizationManager.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace MareLocData
{
 // FString compares case-insensitively, so a default TMap mixed "options" (identifier) with "Options" and "farol" with
 // "Farol": English labels came out in lowercase. Keys here are case-sensitive.
 struct FCaseKeyFuncs:TDefaultMapKeyFuncs<FString,FString,false>
 {
  static bool Matches(const FString& A,const FString& B){return A.Equals(B,ESearchCase::CaseSensitive);}
  static uint32 GetKeyHash(const FString& K){return FCrc::StrCrc32(*K);}
 };
 using FCaseMap=TMap<FString,FString,FDefaultSetAllocator,FCaseKeyFuncs>;
 struct FCaseSetFuncs:DefaultKeyFuncs<FString>
 {
  static bool Matches(const FString& A,const FString& B){return A.Equals(B,ESearchCase::CaseSensitive);}
  static uint32 GetKeyHash(const FString& K){return FCrc::StrCrc32(*K);}
 };
 struct FTemplate{FString Key;TArray<FString> Parts;FString Translation;};
 struct FTable
 {
  FString Language;
  FCaseMap Exact;
  TArray<FTemplate> Templates;     // keys with {n} placeholders, longest literal text first
  FCaseMap Cache;     // resolved results (formatted strings repeat every frame)
  TSet<FString,FCaseSetFuncs> Logged;
  TSet<FString,FCaseSetFuncs> Translated; // translation values: a text already translated passes through unchanged
 };
 FTable& Table(){static FTable T;return T;}
 TSet<FString> Registered;          // polyglot keys already registered (all languages loaded once)

 FString CurrentLanguage()
 {
  const FString Name=FInternationalization::Get().GetCurrentCulture()->GetName();
  return Name.StartsWith(TEXT("es"))?TEXT("es"):Name.StartsWith(TEXT("en"))?TEXT("en"):TEXT("pt");
 }
 TSharedPtr<FJsonObject> LoadFile(const FString& Language)
 {
  FString Text;TSharedPtr<FJsonObject> Json;
  const FString Path=FPaths::ProjectContentDir()/TEXT("Localization/Mare")/(Language+TEXT(".json"));
  if(FFileHelper::LoadFileToString(Text,*Path))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json);
  return Json;
 }
 /** "Repor o bar custa R$ {0}." -> literal parts between placeholders: ["Repor o bar custa R$ ", "."] */
 bool SplitTemplate(const FString& Key,TArray<FString>& Parts)
 {
  Parts.Reset();FString Rest=Key;int32 Count=0;
  for(;;){int32 Open=Rest.Find(TEXT("{"));if(Open==INDEX_NONE)break;int32 Close=Rest.Find(TEXT("}"),ESearchCase::CaseSensitive,ESearchDir::FromStart,Open);
   if(Close==INDEX_NONE || Close-Open>3 || !Rest.Mid(Open+1,Close-Open-1).IsNumeric())break;
   Parts.Add(Rest.Left(Open));Rest.RightChopInline(Close+1);++Count;}
  Parts.Add(Rest);return Count>0;
 }
 /** Pairs of one top-level object ("strings"), read token by token: FJsonObject keys ignore case, so "Farol" and "farol"
  * collapsed into one entry on load (04/11) and English signs stayed in Portuguese or came out in lowercase. */
 TArray<TPair<FString,FString>> ReadSection(const FString& Language,const TCHAR* Section)
 {
  TArray<TPair<FString,FString>> Out;FString Text;
  const FString Path=FPaths::ProjectContentDir()/TEXT("Localization/Mare")/(Language+TEXT(".json"));
  if(!FFileHelper::LoadFileToString(Text,*Path))return Out;
  const TSharedRef<TJsonReader<>> Reader=TJsonReaderFactory<>::Create(Text);
  EJsonNotation Notation;int32 Depth=0;bool bInside=false;
  while(Reader->ReadNext(Notation)){
   switch(Notation){
    case EJsonNotation::ObjectStart:case EJsonNotation::ArrayStart:
     if(Depth==1 && Notation==EJsonNotation::ObjectStart && Reader->GetIdentifier()==Section)bInside=true;++Depth;break;
    case EJsonNotation::ObjectEnd:case EJsonNotation::ArrayEnd:--Depth;if(Depth==1)bInside=false;break;
    case EJsonNotation::String:if(bInside && Depth==2)Out.Emplace(Reader->GetIdentifier(),Reader->GetValueAsString());break;
    case EJsonNotation::Error:return Out;
    default:break;}
  }
  return Out;
 }
 bool MatchTemplate(const FTemplate& T,const FString& Text,TArray<FString>& Values)
 {
  // FString::StartsWith("") is false in UE: a template that begins with {0} ("{0} hoje") has an empty first part.
  Values.Reset();if(!T.Parts[0].IsEmpty() && !Text.StartsWith(T.Parts[0],ESearchCase::CaseSensitive))return false;
  int32 Pos=T.Parts[0].Len();
  for(int32 I=1;I<T.Parts.Num();++I){const FString& Part=T.Parts[I];
   int32 Next;
   if(I==T.Parts.Num()-1){if(Part.IsEmpty())Next=Text.Len();else{if(!Text.EndsWith(Part,ESearchCase::CaseSensitive))return false;Next=Text.Len()-Part.Len();}}
   else{if(Part.IsEmpty())return false;Next=Text.Find(Part,ESearchCase::CaseSensitive,ESearchDir::FromStart,Pos);}
   if(Next==INDEX_NONE || Next<Pos)return false;
   Values.Add(Text.Mid(Pos,Next-Pos));Pos=Next+Part.Len();}
  return Pos==Text.Len();
 }
 void RegisterLocText()
 {
  // One entry per LOCTEXT holding every language, registered once (04/11: registering en and es separately made the
  // Spanish entry replace the English one, and English menus stayed in Portuguese). UE picks the current culture itself.
  static bool bDone=false;if(bDone)return;bDone=true;
  const TSharedPtr<FJsonObject> Native=LoadFile(TEXT("source"));const TSharedPtr<FJsonObject>* Source=nullptr;
  if(!Native.IsValid() || !Native->TryGetObjectField(TEXT("loctext"),Source))return;
  TMap<FString,FPolyglotTextData> Data;
  for(const TCHAR* Language:{TEXT("en"),TEXT("es")}){
   const TSharedPtr<FJsonObject> Json=LoadFile(Language);const TSharedPtr<FJsonObject>* Loc=nullptr;
   if(!Json.IsValid() || !Json->TryGetObjectField(TEXT("loctext"),Loc))continue;
   for(const auto& Pair:(*Loc)->Values){const FString Id(Pair.Key.ToView());FString Translation;if(!Pair.Value->TryGetString(Translation) || Translation.IsEmpty())continue;
    FString NativeText;if(!(*Source)->TryGetStringField(Id,NativeText))continue;FString Namespace,Key;if(!Id.Split(TEXT(","),&Namespace,&Key))continue;
    FPolyglotTextData* Entry=Data.Find(Id);
    if(!Entry)Entry=&Data.Add(Id,FPolyglotTextData(ELocalizedTextSourceCategory::Game,Namespace,Key,NativeText,TEXT("pt-BR")));
    Entry->AddLocalizedString(Language,Translation);}
  }
  for(auto& Pair:Data)FTextLocalizationManager::Get().RegisterPolyglotTextData(Pair.Value);
 }
}

FString MareLoc::Language(){return MareLocData::CurrentLanguage();}

void MareLoc::Reload()
{
 using namespace MareLocData;
 FTable& T=Table();T=FTable();T.Language=CurrentLanguage();
 RegisterLocText();
 if(T.Language==TEXT("pt"))return;
 const TSharedPtr<FJsonObject> Json=LoadFile(T.Language);
 if(!Json.IsValid())return;
 // A LOCTEXT that reaches a widget as FString (ToString of a Portuguese text) is translated too.
 const TSharedPtr<FJsonObject> Native=LoadFile(TEXT("source"));const TSharedPtr<FJsonObject>* Source=nullptr;const TSharedPtr<FJsonObject>* Loc=nullptr;
 if(Native.IsValid() && Native->TryGetObjectField(TEXT("loctext"),Source) && Json->TryGetObjectField(TEXT("loctext"),Loc))
  for(const auto& Pair:(*Loc)->Values){FString Value,From;if(Pair.Value->TryGetString(Value) && !Value.IsEmpty() && (*Source)->TryGetStringField(FString(Pair.Key.ToView()),From))T.Exact.Add(From,Value);}
 for(const auto& Pair:ReadSection(T.Language,TEXT("strings"))){const FString& Key=Pair.Key;const FString& Value=Pair.Value;if(Value.IsEmpty())continue;
  FTemplate Tpl;if(SplitTemplate(Key,Tpl.Parts)){Tpl.Key=Key;Tpl.Translation=Value;T.Templates.Add(MoveTemp(Tpl));}else T.Exact.Add(Key,Value);}
 for(const auto& Pair:T.Exact)T.Translated.Add(Pair.Value);
 auto Literal=[](const FTemplate& X){int32 N=0;for(const FString& P:X.Parts)N+=P.Len();return N;};
 T.Templates.Sort([&](const FTemplate& A,const FTemplate& B){return Literal(A)>Literal(B);});
 UE_LOG(LogTemp,Display,TEXT("MARE_LOC %s exact=%d templates=%d"),*T.Language,T.Exact.Num(),T.Templates.Num());
}

namespace MareLocData
{
 /** Numbers, prices, keys and symbols ("0/12", "R$ 14", "Esc", "80%") have nothing to translate. */
 bool NothingToTranslate(const FString& Text)
 {
  int32 Run=0,Longest=0;
  for(TCHAR C:Text.Replace(TEXT("R$"),TEXT(""))){if(FChar::IsAlpha(C))Longest=FMath::Max(Longest,++Run);else Run=0;}
  return Longest<2 || Text.Len()<=3;
 }
 FString Translate(FTable& T,const FString& Portuguese,bool& bFound)
 {
  bFound=true;
  if(Portuguese.IsEmpty())return Portuguese;
  if(const FString* Hit=T.Exact.Find(Portuguese))return *Hit;
  if(T.Translated.Contains(Portuguese) || NothingToTranslate(Portuguese))return Portuguese;
  TArray<FString> Values;
  for(const FTemplate& Tpl:T.Templates)if(MatchTemplate(Tpl,Portuguese,Values)){
   FString Result=Tpl.Translation;
   // A value can itself be translatable (a dish or place name inside a sentence).
   for(int32 I=0;I<Values.Num();++I){const FString* Inner=T.Exact.Find(Values[I]);Result.ReplaceInline(*FString::Printf(TEXT("{%d}"),I),Inner?**Inner:*Values[I],ESearchCase::CaseSensitive);}
   return Result;}
  // Composed texts ("Uma nova maré — 0/1", "Coco gelado<br>12 prontos", "Fama: Desconhecido", "| Quiosque", menus with
  // several lines): split at the first separator the HUD uses and translate each side; a piece may be listed together
  // with its separator ("Fama: ").
  static const TCHAR* Seps[]={TEXT("\n"),TEXT("<br>"),TEXT(" — "),TEXT(" · "),TEXT("   "),TEXT(": "),TEXT("| ")};
  for(const TCHAR* Sep:Seps){const int32 At=Portuguese.Find(Sep,ESearchCase::CaseSensitive);if(At==INDEX_NONE)continue;
   const FString Left=Portuguese.Left(At),Right=Portuguese.Mid(At+FCString::Strlen(Sep));
   bool bLeft=true,bRight=true;
   const FString* WithSep=T.Exact.Find(Left+Sep);
   const FString Joined=(WithSep?*WithSep:Translate(T,Left,bLeft)+Sep)+Translate(T,Right,bRight);
   bFound=bLeft && bRight;
   return Joined;}
  bFound=false;
  return Portuguese;
 }
}

FString MareLoc::Tr(const FString& Portuguese)
{
 using namespace MareLocData;
 FTable& T=Table();
 if(T.Language.IsEmpty() || T.Language!=CurrentLanguage())Reload();
 if(T.Language==TEXT("pt") || Portuguese.IsEmpty())return Portuguese;
 if(const FString* Hit=T.Cache.Find(Portuguese))return *Hit;
 bool bFound=true;const FString Result=Translate(T,Portuguese,bFound);
 if(!bFound && !T.Logged.Contains(Portuguese) && FParse::Param(FCommandLine::Get(),TEXT("MareLocAudit"))){T.Logged.Add(Portuguese);UE_LOG(LogTemp,Display,TEXT("MARE_LOC_MISSING %s"),*Portuguese.ReplaceCharWithEscapedChar());}
 if(T.Cache.Num()>4096)T.Cache.Reset();
 T.Cache.Add(Portuguese,Result);
 return Result;
}

FText MareLoc::Text(const FString& Portuguese){return FText::FromString(Tr(Portuguese));}
