#include "MareLoc.h"
#include "Internationalization/Culture.h"
#include "Internationalization/Internationalization.h"
#include "Internationalization/PolyglotTextData.h"
#include "Internationalization/TextLocalizationManager.h"
#include "HAL/FileManager.h"
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
  // 09/11: translation values with placeholders ("Resting on the sofa · {0} or move to get up"): a LOCTEXT formatted
  // in English and passed through Tr again is already translated (the audit listed it as missing).
  TArray<FTemplate> TranslatedTemplates;
 };
 FTable& Table(){static FTable T;return T;}
 TSet<FString> Registered;          // polyglot keys already registered (all languages loaded once)

 /** Translation file of the current culture: "pt" (native), or the Content/Localization/Mare/<name>.json that matches the
  * culture best ("zh-Hans-CN" -> zh-Hans, "de-AT" -> de, "pt-PT"). */
 FString CurrentLanguage()
 {
  const FString Name=FInternationalization::Get().GetCurrentCulture()->GetName();
  if(Name.IsEmpty() || Name==TEXT("pt") || Name.StartsWith(TEXT("pt-BR")))return TEXT("pt");
  static TMap<FString,FString> Resolved;
  if(const FString* Hit=Resolved.Find(Name))return *Hit;
  auto Exists=[](const FString& Key){return FPaths::FileExists(FPaths::ProjectContentDir()/TEXT("Localization/Mare")/(Key+TEXT(".json")));};
  FString Key=TEXT("pt");
  TArray<FString> Candidates={Name};
  if(Name.StartsWith(TEXT("zh")))Candidates.Add(TEXT("zh-Hans"));
  int32 Dash;if(Name.FindChar(TEXT('-'),Dash))Candidates.Add(Name.Left(Dash));
  for(const FString& C:Candidates)if(C!=TEXT("source") && Exists(C)){Key=C;break;}
  Resolved.Add(Name,Key);
  return Key;
 }
 /** Languages with a translation file (for the polyglot LOCTEXT registration). */
 TArray<FString> Languages()
 {
  TArray<FString> Files,Out;IFileManager::Get().FindFiles(Files,*(FPaths::ProjectContentDir()/TEXT("Localization/Mare/*.json")),true,false);
  for(const FString& F:Files){const FString Base=FPaths::GetBaseFilename(F);if(Base!=TEXT("source") && !Base.StartsWith(TEXT("todo_")))Out.Add(Base);}
  return Out;
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
   const FString Value=Text.Mid(Pos,Next-Pos);
   // 09/11: a value is a number or a name, never more sentences (the day summary with "Jogo salvo no slot 1. O
   // quiosque..." after it was matched by the summary template, the rest left in Portuguese inside {3}).
   if(Value.Contains(TEXT(". ")) || Value.Contains(TEXT("! ")) || Value.Contains(TEXT("? ")) || Value.Contains(TEXT("\n")))return false;
   Values.Add(Value);Pos=Next+Part.Len();}
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
  for(const FString& Language:Languages()){
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

FString MareLoc::Cardinal(int32 Index)
{
 // North, east, south, west in each language's own compass letters.
 static const TMap<FString,TArray<FString>> Letters={
  {TEXT("pt"),{TEXT("N"),TEXT("L"),TEXT("S"),TEXT("O")}},{TEXT("pt-PT"),{TEXT("N"),TEXT("E"),TEXT("S"),TEXT("O")}},
  {TEXT("en"),{TEXT("N"),TEXT("E"),TEXT("S"),TEXT("W")}},{TEXT("es"),{TEXT("N"),TEXT("E"),TEXT("S"),TEXT("O")}},
  {TEXT("fr"),{TEXT("N"),TEXT("E"),TEXT("S"),TEXT("O")}},{TEXT("it"),{TEXT("N"),TEXT("E"),TEXT("S"),TEXT("O")}},
  {TEXT("de"),{TEXT("N"),TEXT("O"),TEXT("S"),TEXT("W")}},{TEXT("nl"),{TEXT("N"),TEXT("O"),TEXT("Z"),TEXT("W")}},
  {TEXT("ru"),{TEXT("С"),TEXT("В"),TEXT("Ю"),TEXT("З")}},{TEXT("pl"),{TEXT("N"),TEXT("W"),TEXT("S"),TEXT("Z")}},
  {TEXT("cs"),{TEXT("S"),TEXT("V"),TEXT("J"),TEXT("Z")}},{TEXT("hu"),{TEXT("É"),TEXT("K"),TEXT("D"),TEXT("Ny")}},
  {TEXT("ro"),{TEXT("N"),TEXT("E"),TEXT("S"),TEXT("V")}},{TEXT("da"),{TEXT("N"),TEXT("Ø"),TEXT("S"),TEXT("V")}},
  {TEXT("fi"),{TEXT("P"),TEXT("I"),TEXT("E"),TEXT("L")}},{TEXT("ja"),{TEXT("北"),TEXT("東"),TEXT("南"),TEXT("西")}},
  {TEXT("ko"),{TEXT("북"),TEXT("동"),TEXT("남"),TEXT("서")}},{TEXT("zh-Hans"),{TEXT("北"),TEXT("东"),TEXT("南"),TEXT("西")}}};
 const TArray<FString>* List=Letters.Find(Language());if(!List)List=Letters.Find(TEXT("en"));
 return (*List)[FMath::Clamp(Index,0,3)];
}

bool MareLoc::LatinOnly(const FString& Text){for(TCHAR C:Text)if(C>0x024F && C!=0x2014 && C!=0x2022 && C!=0x00B7 && C!=0x2026 && C!=0x2605 && (C<0x2000 || C>0x206F))return false;return true;}

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
 {auto AddTranslated=[&T](const FString& Value){FTemplate Tpl;int32 Literal=0;if(!SplitTemplate(Value,Tpl.Parts))return;for(const FString& P:Tpl.Parts)Literal+=P.Len();
   if(Literal>=6){Tpl.Key=Value;T.TranslatedTemplates.Add(MoveTemp(Tpl));}};
  for(const auto& Pair:ReadSection(T.Language,TEXT("strings")))if(!Pair.Value.IsEmpty())AddTranslated(Pair.Value);
  const TSharedPtr<FJsonObject>* LocValues=nullptr;if(Json->TryGetObjectField(TEXT("loctext"),LocValues))
   for(const auto& Pair:(*LocValues)->Values){FString Value;if(Pair.Value->TryGetString(Value))AddTranslated(Value);}}
 auto Literal=[](const FTemplate& X){int32 N=0;for(const FString& P:X.Parts)N+=P.Len();return N;};
 T.Templates.Sort([&](const FTemplate& A,const FTemplate& B){return Literal(A)>Literal(B);});
 UE_LOG(LogTemp,Display,TEXT("MARE_LOC %s exact=%d templates=%d"),*T.Language,T.Exact.Num(),T.Templates.Num());
}

namespace MareLocData
{
 /** Numbers, prices, keys and symbols ("0/12", "R$ 14", "Esc", "80%") have nothing to translate. */
 bool NothingToTranslate(const FString& Text)
 {
  // 09/11: an order number and a first name ("#1 Thiago") are shown as they are.
  if(Text.StartsWith(TEXT("#"))){int32 I=1;while(I<Text.Len() && FChar::IsDigit(Text[I]))++I;
   if(I>1 && I<Text.Len() && Text[I]==TEXT(' ') && !Text.Mid(I+1).Contains(TEXT(" ")))return true;}
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
  // Already translated (a formatted English LOCTEXT passed through Tr again).
  for(const FTemplate& Tpl:T.TranslatedTemplates)if(MatchTemplate(Tpl,Portuguese,Values))return Portuguese;
  // 09/11: a counter at the end of a mission step ("Levar 4 peixes para o almoço dos pescadores (0/4)").
  if(Portuguese.EndsWith(TEXT(")"))){const int32 Open=Portuguese.Find(TEXT(" ("),ESearchCase::CaseSensitive,ESearchDir::FromEnd);
   if(Open>0){const FString Inner=Portuguese.Mid(Open+2,Portuguese.Len()-Open-3);FString A,B;
    if(Inner.Split(TEXT("/"),&A,&B) && A.IsNumeric() && B.IsNumeric())return Translate(T,Portuguese.Left(Open),bFound)+Portuguese.Mid(Open);}}
  // Composed texts ("Uma nova maré — 0/1", "Coco gelado<br>12 prontos", "Fama: Desconhecido", "| Quiosque", menus with
  // several lines): split at the first separator the HUD uses and translate each side; a piece may be listed together
  // with its separator ("Fama: ").
  static const TCHAR* Seps[]={TEXT("\n"),TEXT("<br>"),TEXT(" — "),TEXT(" · "),TEXT("   "),TEXT(": "),TEXT("| ")};
  for(int32 S=0;S<UE_ARRAY_COUNT(Seps);++S){const TCHAR* Sep=Seps[S];
   // 09/11: after the line breaks, several sentences ("Bom dia! Dia 1 encerrado ... Jogo salvo no slot 1. O quiosque
   // está fechado; ..."): each sentence on its own, before the HUD separators (the summary's own " · " would split it
   // in the wrong place).
   if(S==2)for(int32 I=3;I+2<Portuguese.Len();++I){const TCHAR C=Portuguese[I];
    if((C==TEXT('.') || C==TEXT('!') || C==TEXT('?')) && Portuguese[I+1]==TEXT(' ') && FChar::IsUpper(Portuguese[I+2])){
     bool bLeft=true,bRight=true;const FString Joined=Translate(T,Portuguese.Left(I+1),bLeft)+TEXT(" ")+Translate(T,Portuguese.Mid(I+2),bRight);
     bFound=bLeft && bRight;return Joined;}}
   const int32 At=Portuguese.Find(Sep,ESearchCase::CaseSensitive);if(At==INDEX_NONE)continue;
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
