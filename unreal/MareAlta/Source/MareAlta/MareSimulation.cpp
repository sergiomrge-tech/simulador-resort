#include "MareSimulation.h"
#include "MareKioskWorld.h"
#include "MareVisualWorld.h"
#include "Engine/World.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"

TSharedPtr<FJsonObject> UMareSimulation::Object(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
{
 const TSharedPtr<FJsonObject>* Found=nullptr;
 if(Parent.IsValid() && Parent->TryGetObjectField(Key,Found)) return *Found;
 auto Result=MakeShared<FJsonObject>();
 if(Parent.IsValid()) Parent->SetObjectField(Key,Result);
 return Result;
}
double UMareSimulation::Number(const TSharedPtr<FJsonObject>& Parent,const FString& Key,double Fallback)
{
 double Value=Fallback;
 if(Parent.IsValid()) Parent->TryGetNumberField(Key,Value);
 return Value;
}
FString UMareSimulation::String(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
{
 FString Value;
 if(Parent.IsValid()) Parent->TryGetStringField(Key,Value);
 return Value;
}
bool UMareSimulation::ReadJson(const FString& Path,TSharedPtr<FJsonObject>& Target) const
{
 FString Text;
 if(!FFileHelper::LoadFileToString(Text,*Path)) return false;
 return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Target) && Target.IsValid();
}
FString UMareSimulation::SavePath() const
{
 return (SaveDirectory.IsEmpty()?FPaths::ProjectSavedDir()/TEXT("SaveGames"):SaveDirectory)/TEXT("slot1.json");
}
void UMareSimulation::Initialize(FSubsystemCollectionBase& Collection)
{
 Super::Initialize(Collection);
 FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),SaveDirectory);
 ReadJson(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"),Definitions);
 const bool bExistingSave=IFileManager::Get().FileExists(*SavePath());
 if(!ReadJson(SavePath(),State)) ReadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),State);
 if(!bExistingSave && State.IsValid() && !FParse::Param(FCommandLine::Get(),TEXT("MarePreviewQA")) && !FParse::Param(FCommandLine::Get(),TEXT("MareGraphicsQA"))) State->SetNumberField(TEXT("ue_intro_stage"),0);
 if(!State.IsValid()) State=MakeShared<FJsonObject>();
 if(!Definitions.IsValid()) Definitions=MakeShared<FJsonObject>();
}
bool UMareSimulation::Fail(const FString& Message){LastMessage=Message;return false;}
double UMareSimulation::Money() const{return Number(State,TEXT("money"));}
FString UMareSimulation::Carry(bool bStaff) const{return String(Object(State,TEXT("company")),bStaff?TEXT("staff_carry"):TEXT("carry"));}
void UMareSimulation::Book(double Amount,const FString& Label)
{
 State->SetNumberField(TEXT("money"),Money()+Amount);
 const FString TotalKey=Amount>=0?TEXT("day_in"):TEXT("day_out");
 State->SetNumberField(TotalKey,Number(State,TotalKey)+FMath::Abs(Amount));
 auto Row=MakeShared<FJsonObject>(); Row->SetStringField(TEXT("label"),Label); Row->SetNumberField(TEXT("amount"),Amount);
 const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;
 TArray<TSharedPtr<FJsonValue>> Ledger;
 if(State->TryGetArrayField(TEXT("ledger"),Existing)) Ledger=*Existing;
 Ledger.Add(MakeShared<FJsonValueObject>(Row)); State->SetArrayField(TEXT("ledger"),Ledger);
}
bool UMareSimulation::CreateCompany(const FString& Name)
{
 const FString Clean=Name.TrimStartAndEnd().Left(32);
 if(Clean.IsEmpty()) return Fail(TEXT("Dê um nome ao quiosque."));
 auto Company=Object(State,TEXT("company")); Company->SetBoolField(TEXT("created"),true);
 Company->SetStringField(TEXT("name"),Clean); Company->SetBoolField(TEXT("physical"),true);
 LastMessage=TEXT("Empresa criada. Abra o quiosque para receber clientes."); return Save();
}
bool UMareSimulation::SetOpen(bool bOpen)
{
 auto Company=Object(State,TEXT("company")); bool bCreated=false;
 Company->TryGetBoolField(TEXT("created"),bCreated);
 if(bOpen && !bCreated) return Fail(TEXT("Crie sua empresa primeiro."));
 Company->SetBoolField(TEXT("kiosk_open"),bOpen);
 auto Hours=Object(Company,TEXT("sim"));
 LastMessage=bOpen?(IsOpen()?TEXT("Quiosque aberto. Recebendo clientes."):FString::Printf(TEXT("Abertura ativada. Atendimento das %.0fh às %.0fh."),Number(Hours,TEXT("start"),8),Number(Hours,TEXT("end"),18))):TEXT("Quiosque fechado.");
 return Save();
}
bool UMareSimulation::IsOpen() const
{
 auto Company=Object(State,TEXT("company")); bool bOpen=false,bCreated=false;
 Company->TryGetBoolField(TEXT("kiosk_open"),bOpen); Company->TryGetBoolField(TEXT("created"),bCreated);
 auto Sim=Object(Company,TEXT("sim")); const double Hour=Number(State,TEXT("minutes"),480)/60.;
 return bOpen && bCreated && Hour>=Number(Sim,TEXT("start"),8) && Hour<Number(Sim,TEXT("end"),18);
}
bool UMareSimulation::IsDishUnlocked(const FString& Dish) const
{
 if(!Object(Definitions,TEXT("dishes"))->HasField(Dish))return false;
 const FString Requirement=(Dish==TEXT("caipirinha") || Dish==TEXT("batida"))?TEXT("drinks"):Dish==TEXT("petiscos")?TEXT("grill"):TEXT("");
 if(Requirement.IsEmpty())return true;
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(Requirement,bOwned);return bOwned;
}
bool UMareSimulation::CanSupplyDish(const FString& Dish) const
{
 if(IsDishUnlocked(Dish))return true;
 if(!Object(Definitions,TEXT("dishes"))->HasField(Dish))return false;
 for(const auto& Pair:Object(State,TEXT("ue_orders"))->Values){
  const TArray<TSharedPtr<FJsonValue>>* Remaining=nullptr;
  if(Pair.Value->AsObject()->TryGetArrayField(TEXT("remaining"),Remaining))
   for(const auto& Item:*Remaining)if(Item->AsString()==Dish)return true;
 }
 return false;
}
int32 UMareSimulation::Available(const FString& Dish) const
{
 if(!CanSupplyDish(Dish))return 0;
 auto Dishes=Object(Definitions,TEXT("dishes")); if(!Dishes->HasField(Dish)) return 0;
 auto Uses=Object(Object(Dishes,Dish),TEXT("uses")); auto Stock=Object(State,TEXT("stock")); int32 Count=MAX_int32;
 for(const auto& Pair:Uses->Values) Count=FMath::Min(Count,FMath::FloorToInt(Number(Stock,FString(Pair.Key.ToView()))/FMath::Max(1.,Pair.Value->AsNumber())));
 return Count==MAX_int32?0:Count;
}
double UMareSimulation::RestockCost(const FString& Dish,int32 Quantity) const
{
 if(Quantity<1 || Quantity>48 || !CanSupplyDish(Dish)) return -1;
 auto Uses=Object(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("uses"));
 auto Stock=Object(State,TEXT("stock")); auto Supplies=Object(Definitions,TEXT("supplies")); double Cost=0;
 for(const auto& Pair:Uses->Values) Cost+=FMath::Max(0.,Quantity*Pair.Value->AsNumber()-Number(Stock,FString(Pair.Key.ToView())))*Number(Object(Supplies,FString(Pair.Key.ToView())),TEXT("cost"));
 return Cost;
}
bool UMareSimulation::Restock(const FString& Dish,int32 Quantity)
{
 const double Cost=RestockCost(Dish,Quantity);
 if(Cost<0) return Fail(TEXT("Produto ou quantidade inválida."));
 if(Money()<Cost) return Fail(TEXT("Saldo insuficiente. Nenhum insumo foi cobrado."));
 auto Uses=Object(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("uses")); auto Stock=Object(State,TEXT("stock"));
 for(const auto& Pair:Uses->Values) Stock->SetNumberField(FString(Pair.Key.ToView()),FMath::Max(Number(Stock,FString(Pair.Key.ToView())),Quantity*Pair.Value->AsNumber()));
 if(Cost>0) Book(-Cost,TEXT("Reposição: ")+Dish);
 LastMessage=TEXT("Estoque reposto."); return Save();
}
bool UMareSimulation::Pickup(const FString& Dish,bool bStaff)
{
 if(!CanSupplyDish(Dish))return Fail(TEXT("Compre a expansão que libera este produto no celular."));
 if(!Carry(bStaff).IsEmpty()) return Fail(TEXT("Entregue ou devolva o produto que está na mão."));
 if(Available(Dish)<1) return Fail(TEXT("Produto esgotado. Reponha nesta estação."));
 auto Uses=Object(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("uses")); auto Stock=Object(State,TEXT("stock"));
 for(const auto& Pair:Uses->Values) Stock->SetNumberField(FString(Pair.Key.ToView()),Number(Stock,FString(Pair.Key.ToView()))-Pair.Value->AsNumber());
 Object(State,TEXT("company"))->SetStringField(bStaff?TEXT("staff_carry"):TEXT("carry"),Dish); return Save();
}
bool UMareSimulation::ReturnCarry(bool bStaff)
{
 const FString Dish=Carry(bStaff); if(Dish.IsEmpty()) return false;
 auto Uses=Object(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("uses")); auto Stock=Object(State,TEXT("stock"));
 for(const auto& Pair:Uses->Values) Stock->SetNumberField(FString(Pair.Key.ToView()),Number(Stock,FString(Pair.Key.ToView()))+Pair.Value->AsNumber());
 Object(State,TEXT("company"))->SetStringField(bStaff?TEXT("staff_carry"):TEXT("carry"),TEXT("")); return Save();
}
FString UMareSimulation::AddOrder(const FString& Customer,const TArray<FString>& Dishes)
{
 if(!IsOpen() || Dishes.IsEmpty()) return TEXT("");
 auto Orders=Object(State,TEXT("ue_orders")); const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Order=MakeShared<FJsonObject>(); Order->SetStringField(TEXT("name"),Customer); TArray<TSharedPtr<FJsonValue>> Items;
 for(const auto& Dish:Dishes){if(!IsDishUnlocked(Dish)) return TEXT("");Items.Add(MakeShared<FJsonValueString>(Dish));}
 Order->SetArrayField(TEXT("remaining"),Items);Order->SetArrayField(TEXT("items"),Items); Orders->SetObjectField(Id,Order); Save(); return Id;
}
bool UMareSimulation::Deliver(const FString& OrderId,const FString& Dish,bool bStaff)
{
 auto Orders=Object(State,TEXT("ue_orders")); if(Carry(bStaff)!=Dish || !Orders->HasField(OrderId)) return false;
 auto Order=Object(Orders,OrderId); const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;
 if(!Order->TryGetArrayField(TEXT("remaining"),Existing)) return false;
 auto Items=*Existing; const int32 Index=Items.IndexOfByPredicate([&](const auto& V){return V->AsString()==Dish;});
 if(Index==INDEX_NONE) return false;
 Items.RemoveAt(Index); Order->SetArrayField(TEXT("remaining"),Items);
 Object(State,TEXT("company"))->SetStringField(bStaff?TEXT("staff_carry"):TEXT("carry"),TEXT(""));
 const double Price=Number(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("price")); Book(Price,TEXT("Venda: ")+Dish);
 State->SetNumberField(TEXT("kiosk_n"),Number(State,TEXT("kiosk_n"))+1); State->SetNumberField(TEXT("kiosk"),Number(State,TEXT("kiosk"))+Price);
 if(Dish.StartsWith(TEXT("sorvete_"))){auto Campaign=Object(Object(State,TEXT("prog")),TEXT("campaign"));Campaign->SetNumberField(TEXT("icecream"),Number(Campaign,TEXT("icecream"))+1);}
 AddFame(2);
 // Serve/sell steps count only sales made while that chapter step is active.
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;auto Progress=Object(Object(State,TEXT("prog")),TEXT("ch"));
 if(Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){const FString Chapter=String(Value->AsObject(),TEXT("id"));
  if(!IsChapterOpen(Chapter) || IsChapterDone(Chapter))continue;
  const auto Step=Value->AsObject()->GetArrayField(TEXT("steps"))[ChapterStep(Chapter)]->AsObject();const FString Kind=String(Step,TEXT("kind"));
  if(Kind==TEXT("serve") || (Kind==TEXT("sell") && String(Step,TEXT("item"))==Dish))Progress->SetNumberField(Chapter+TEXT("_")+Kind,Number(Progress,Chapter+TEXT("_")+Kind)+1);
 }
 if(Items.IsEmpty()) Orders->RemoveField(OrderId);
 return Save();
}
bool UMareSimulation::HireAttendant()
{
 auto Staff=Object(State,TEXT("staff")); bool bHired=false;Staff->TryGetBoolField(TEXT("atendente"),bHired);
 if(bHired) return Fail(TEXT("Seu atendente já cuida de todo o atendimento."));
 const double Cost=Number(Object(Object(Definitions,TEXT("staff")),TEXT("atendente")),TEXT("hire"));
 if(Money()<Cost) return Fail(TEXT("Saldo insuficiente."));
 Staff->SetBoolField(TEXT("atendente"),true); Book(-Cost,TEXT("Contratação do atendente"));return Save();
}
bool UMareSimulation::DismissAttendant()
{
 auto Staff=Object(State,TEXT("staff"));bool bHired=false;Staff->TryGetBoolField(TEXT("atendente"),bHired);
 if(!bHired)return Fail(TEXT("Não há atendente contratado."));
 ReturnCarry(true);Staff->SetBoolField(TEXT("atendente"),false);
 LastMessage=TEXT("Atendente dispensado. Você volta a atender o quiosque sozinho.");return Save();
}
bool UMareSimulation::BuyExpansion(const FString& Id)
{
 auto Expansions=Object(Definitions,TEXT("expansions")); if(!Expansions->HasField(Id)) return false;
 auto Unlocked=Object(State,TEXT("unlocked")); bool bOwned=false;Unlocked->TryGetBoolField(Id,bOwned);if(bOwned)return Fail(TEXT("Esta expansão já foi comprada."));
 auto Expansion=Object(Expansions,Id); const TArray<TSharedPtr<FJsonValue>>* Required=nullptr;
 if(Expansion->TryGetArrayField(TEXT("req"),Required)) for(const auto& Req:*Required){bool bHas=false;Unlocked->TryGetBoolField(Req->AsString(),bHas);if(!bHas)return Fail(TEXT("Compre as expansões anteriores."));}
 const double Cost=Number(Expansion,TEXT("cost")); if(Money()<Cost) return Fail(TEXT("Saldo insuficiente."));
 Unlocked->SetBoolField(Id,true);Book(-Cost,TEXT("Expansão: ")+Id);
 if(auto World=GetWorld())if(auto Visual=World->GetSubsystem<UMareVisualWorld>())Visual->RefreshExpansions();
 LastMessage=TEXT("Expansão desbloqueada: ")+String(Expansion,TEXT("name"));return Save();
}
int32 UMareSimulation::MissionAmount(const TSharedPtr<FJsonObject>& Mission) const
{
 const FString Kind=String(Mission,TEXT("kind")),Item=String(Mission,TEXT("item"));
 auto Company=Object(State,TEXT("company")); auto Prog=Object(State,TEXT("prog")); auto Campaign=Object(Prog,TEXT("campaign"));
 if(Kind==TEXT("sales")) return Number(State,TEXT("kiosk_n"));
 if(Kind==TEXT("icecream") || Kind==TEXT("fish")) return Number(Campaign,Kind);
 bool bValue=false;
 if(Kind==TEXT("company")) Company->TryGetBoolField(TEXT("created"),bValue);
 if(Kind==TEXT("open")) {Company->TryGetBoolField(TEXT("kiosk_open"),bValue);bValue|=Number(State,TEXT("kiosk_n"))>0;}
 if(Kind==TEXT("staff")) Object(State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bValue);
 if(Kind==TEXT("photo")) Object(Prog,TEXT("chapter_photo"))->TryGetBoolField(Item,bValue);
 if(Kind==TEXT("expansion"))Object(State,TEXT("unlocked"))->TryGetBoolField(Item,bValue);
 if(Kind==TEXT("chapter"))bValue=IsChapterDone(Item);
 return bValue?1:0;
}
TSharedPtr<FJsonObject> UMareSimulation::ChapterDefinition(const FString& Id) const
{
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;
 if(Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters)if(String(Value->AsObject(),TEXT("id"))==Id)return Value->AsObject();
 return nullptr;
}
int32 UMareSimulation::ChapterStep(const FString& Id) const{return Number(Object(Object(State,TEXT("prog")),TEXT("ch")),Id);}
bool UMareSimulation::IsChapterOpen(const FString& Id) const
{
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;if(!Definitions->TryGetArrayField(TEXT("chapters"),Chapters))return false;
 for(int32 I=0;I<Chapters->Num();++I)if(String((*Chapters)[I]->AsObject(),TEXT("id"))==Id)return I==0 || IsChapterDone(String((*Chapters)[I-1]->AsObject(),TEXT("id")));
 return false;
}
int32 UMareSimulation::ChapterStepProgress(const FString& Id,int32& Goal) const
{
 Goal=1;auto Chapter=ChapterDefinition(Id);if(!Chapter.IsValid() || IsChapterDone(Id))return 1;
 const auto Step=Chapter->GetArrayField(TEXT("steps"))[ChapterStep(Id)]->AsObject();const FString Kind=String(Step,TEXT("kind")),Item=String(Step,TEXT("item"));
 Goal=FMath::Max(1,int32(Number(Step,TEXT("qty"),1)));auto Prog=Object(State,TEXT("prog"));bool bValue=false;int32 Amount=0;
 if(Kind==TEXT("deliver"))Amount=Number(Object(State,TEXT("stock")),Item);
 else if(Kind==TEXT("pay"))Amount=FMath::Max(0.,Money());
 else if(Kind==TEXT("serve") || Kind==TEXT("sell"))Amount=Number(Object(Prog,TEXT("ch")),Id+TEXT("_")+Kind);
 else if(Kind==TEXT("fame"))Amount=FameLevel();
 else if(Kind==TEXT("recipes"))Amount=Object(Prog,TEXT("disc"))->Values.Num();
 else if(Kind==TEXT("biz"))Amount=Object(Prog,TEXT("biz"))->Values.Num();
 else if(Kind==TEXT("photo")){Object(Prog,TEXT("chp"))->TryGetBoolField(Item,bValue);Amount=bValue?1:0;}
 return FMath::Min(Amount,Goal);
}
bool UMareSimulation::AdvanceChapter(const FString& Id)
{
 auto Chapter=ChapterDefinition(Id);if(!Chapter.IsValid() || !IsChapterOpen(Id) || IsChapterDone(Id))return false;
 int32 Goal=1;if(ChapterStepProgress(Id,Goal)<Goal)return Fail(TEXT("Este passo da história ainda não foi cumprido."));
 const int32 StepIndex=ChapterStep(Id);const auto Step=Chapter->GetArrayField(TEXT("steps"))[StepIndex]->AsObject();const FString Kind=String(Step,TEXT("kind"));
 if(Kind==TEXT("deliver")){auto Stock=Object(State,TEXT("stock"));const FString Item=String(Step,TEXT("item"));Stock->SetNumberField(Item,Number(Stock,Item)-Goal);}
 if(Kind==TEXT("pay"))Book(-Goal,String(Chapter,TEXT("title"))+TEXT(": ")+String(Step,TEXT("text")));
 Object(Object(State,TEXT("prog")),TEXT("ch"))->SetNumberField(Id,StepIndex+1);
 LastMessage=TEXT("Passo concluído: ")+String(Step,TEXT("text"));
 if(IsChapterDone(Id)){Book(Number(Chapter,TEXT("reward")),TEXT("Capítulo concluído: ")+String(Chapter,TEXT("title")));AddFame(80);
  LastMessage=TEXT("Capítulo concluído! Liberado: ")+String(Chapter,TEXT("unlock"));}
 return Save();
}
double UMareSimulation::SupplyCost(const FString& Item,int32 Quantity) const
{
 auto Supplies=Object(Definitions,TEXT("supplies"));if(Quantity<1 || Quantity>48 || !Supplies->HasField(Item))return -1;
 return Quantity*Number(Object(Supplies,Item),TEXT("cost"));
}
bool UMareSimulation::BuySupply(const FString& Item,int32 Quantity)
{
 const double Cost=SupplyCost(Item,Quantity);if(Cost<0)return Fail(TEXT("Insumo ou quantidade inválida."));
 if(Money()<Cost)return Fail(TEXT("Saldo insuficiente. Nenhum insumo foi cobrado."));
 auto Stock=Object(State,TEXT("stock"));Stock->SetNumberField(Item,Number(Stock,Item)+Quantity);
 Book(-Cost,TEXT("Mercadinho: ")+String(Object(Object(Definitions,TEXT("supplies")),Item),TEXT("name")));
 LastMessage=TEXT("Compra feita no mercadinho.");return Save();
}
namespace{const int32 FameThresholds[]={0,100,250,450,700,1000,1400,1900,2500,3200};
 const TCHAR* FameNames[]={TEXT("Desconhecido"),TEXT("Falado na vila"),TEXT("Ponto da praia"),TEXT("Queridinho da cidade"),TEXT("Famoso na região"),
  TEXT("Roteiro turístico"),TEXT("Destaque na TV"),TEXT("Destino do verão"),TEXT("Paraíso famoso"),TEXT("Lenda da costa")};}
int32 UMareSimulation::FameLevel() const
{
 const double Xp=Number(Object(State,TEXT("prog")),TEXT("fame_xp"));int32 Level=1;
 for(int32 I=0;I<UE_ARRAY_COUNT(FameThresholds);++I)if(Xp>=FameThresholds[I])Level=I+1;
 return Level;
}
FString UMareSimulation::FameName() const{return FameNames[FMath::Clamp(FameLevel()-1,0,9)];}
double UMareSimulation::Stars() const
{
 const TArray<TSharedPtr<FJsonValue>>* Ratings=nullptr;if(!State->TryGetArrayField(TEXT("ratings"),Ratings) || Ratings->IsEmpty())return 3;
 double Sum=0;for(const auto& Value:*Ratings)Sum+=Value->AsNumber();return Sum/Ratings->Num();
}
double UMareSimulation::HotelOccupancy() const
{
 // Season, parties and upgrade tree are not ported yet; their terms stay neutral.
 return FMath::Clamp(.42+.12*(Stars()-4.)+.03*(FameLevel()-7),.15,.98);
}
void UMareSimulation::HotelNight()
{
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bOwned);if(!bOwned)return;
 constexpr int32 Rooms=32,Rate=220,Dining=35,StaffCost=900;
 const double Occupancy=HotelOccupancy();const int32 Occupied=FMath::RoundToInt(Rooms*Occupancy);
 const double Revenue=Occupied*Rate,Meals=FMath::RoundToDouble(Occupied*1.7*Dining);
 Book(Revenue,FString::Printf(TEXT("Grand Hotel: %d suítes ocupadas"),Occupied));
 Book(Meals,TEXT("Grand Hotel: restaurante e bar"));
 Book(-StaffCost,TEXT("Grand Hotel: equipe (recepção, cozinha, spa, limpeza)"));
 auto Last=MakeShared<FJsonObject>();Last->SetNumberField(TEXT("occ"),Occupancy);Last->SetNumberField(TEXT("rooms"),Occupied);
 Last->SetNumberField(TEXT("rev"),Revenue);Last->SetNumberField(TEXT("dining"),Meals);Last->SetNumberField(TEXT("staff"),StaffCost);
 Object(State,TEXT("prog"))->SetObjectField(TEXT("hotel"),Last);
 // Five-star guests rate their stay; keep the list bounded like the original rolling window.
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
 for(int32 I=0;I<FMath::Min(6,FMath::Max(1,Occupied/5));++I)Ratings.Add(MakeShared<FJsonValueNumber>(FMath::FRandRange(4.3,5.0)));
 while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);
 AddFame(Occupied/2);
}
void UMareSimulation::AddFame(int32 Xp)
{
 if(Xp<=0)return;const int32 Before=FameLevel();auto Prog=Object(State,TEXT("prog"));Prog->SetNumberField(TEXT("fame_xp"),Number(Prog,TEXT("fame_xp"))+Xp);
 if(FameLevel()>Before)LastMessage=TEXT("Sua fama subiu: ")+FameName()+TEXT("!");
}
bool UMareSimulation::ClaimMission(const FString& Id,bool bSide)
{
 const TArray<TSharedPtr<FJsonValue>>* Missions=nullptr;
 if(!Definitions->TryGetArrayField(bSide?TEXT("side_missions"):TEXT("campaign"),Missions)) return false;
 auto Campaign=Object(Object(State,TEXT("prog")),TEXT("campaign"));
 const int32 Stage=Number(Campaign,TEXT("stage")); TArray<TSharedPtr<FJsonValue>> Done;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;
 if(Campaign->TryGetArrayField(TEXT("side_done"),Existing)) Done=*Existing;
 for(int32 I=0;I<Missions->Num();++I){auto M=(*Missions)[I]->AsObject();if(String(M,TEXT("id"))!=Id) continue;
  if((!bSide && Stage!=I) || (bSide && Done.ContainsByPredicate([&](const auto& V){return V->AsString()==Id;}))) return false;
  if(MissionAmount(M)<Number(M,TEXT("qty"))) return Fail(TEXT("Objetivo ainda não concluído."));
  if(bSide){Done.Add(MakeShared<FJsonValueString>(Id));Campaign->SetArrayField(TEXT("side_done"),Done);}else Campaign->SetNumberField(TEXT("stage"),Stage+1);
  Book(Number(M,TEXT("reward")),TEXT("Missão: ")+String(M,TEXT("title"))); return Save();}
 return false;
}
void UMareSimulation::AdvanceMinutes(double Minutes){State->SetNumberField(TEXT("minutes"),FMath::Clamp(Number(State,TEXT("minutes"))+Minutes,0.,1440.));}
void UMareSimulation::Sleep()
{
 ReturnCarry();ReturnCarry(true);auto Company=Object(State,TEXT("company"));Company->SetBoolField(TEXT("kiosk_open"),false);
 const int32 Day=Number(State,TEXT("day"),1);auto Hours=Object(Company,TEXT("sim"));
 // wage_day guards against charging the same day twice after a reload, as in the Godot save.
 double Wages=0;
 if(Number(Hours,TEXT("wage_day"),-1)<Day){
  auto Staff=Object(State,TEXT("staff"));auto Roles=Object(Definitions,TEXT("staff"));
  for(const auto& Pair:Staff->Values){bool bHired=false;const FString Role(Pair.Key.ToView());
   // Legacy kiosk roles were merged into the single attendant; never charge them again.
   if(!Pair.Value->TryGetBool(bHired) || !bHired || !Roles->HasField(Role))continue;
   bool bLegacyKiosk=false;Object(Roles,Role)->TryGetBoolField(TEXT("company"),bLegacyKiosk);if(bLegacyKiosk)continue;
   const double Wage=Number(Object(Roles,Role),TEXT("wage"));Wages+=Wage;Book(-Wage,TEXT("Salário: ")+String(Object(Roles,Role),TEXT("name")));
  }
  Hours->SetNumberField(TEXT("wage_day"),Day);
  HotelNight();
 }
 auto Summary=MakeShared<FJsonObject>();const double In=Number(State,TEXT("day_in")),Out=Number(State,TEXT("day_out"));
 Summary->SetNumberField(TEXT("day"),Day);Summary->SetNumberField(TEXT("income"),In);Summary->SetNumberField(TEXT("expense"),Out);
 Summary->SetNumberField(TEXT("wages"),Wages);Summary->SetNumberField(TEXT("sales"),Number(State,TEXT("kiosk_n"))-Number(State,TEXT("ue_day_sales_start")));
 Summary->SetNumberField(TEXT("money"),Money());State->SetObjectField(TEXT("ue_last_day"),Summary);
 State->SetNumberField(TEXT("day_in"),0);State->SetNumberField(TEXT("day_out"),0);State->SetNumberField(TEXT("ue_day_sales_start"),Number(State,TEXT("kiosk_n")));
 LastMessage=FString::Printf(TEXT("Dia %d encerrado · vendas R$ %.0f · despesas R$ %.0f · saldo do dia R$ %.0f."),Day,In,Out,In-Out);
 if(Money()<0)LastMessage+=TEXT(" Caixa negativo: venda mais antes de repor estoque.");
 State->SetNumberField(TEXT("day"),Day+1);State->SetNumberField(TEXT("minutes"),480);
 State->SetObjectField(TEXT("ue_orders"),MakeShared<FJsonObject>());Save();
}
bool UMareSimulation::Save()
{
 if(GetWorld() && GetWorld()->IsGameWorld())if(auto Kiosk=GetWorld()->GetSubsystem<UMareKioskWorld>())Kiosk->CaptureState();
 FString Text;if(!FJsonSerializer::Serialize(State.ToSharedRef(),TJsonWriterFactory<>::Create(&Text))) return false;
 const FString Path=SavePath(),Temp=Path+TEXT(".tmp");IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
 if(!FFileHelper::SaveStringToFile(Text,*Temp,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) return Fail(TEXT("Falha ao salvar."));
 return IFileManager::Get().Move(*Path,*Temp,true,true);
}
bool UMareSimulation::ImportLegacySave(const FString& Path)
{
 TSharedPtr<FJsonObject> Imported;if(!ReadJson(Path,Imported) || !Imported->HasTypedField<EJson::Object>(TEXT("company")) || !Imported->HasTypedField<EJson::Number>(TEXT("money"))) return Fail(TEXT("Save incompatível."));
 if(FPaths::ConvertRelativePathToFull(Path)==FPaths::ConvertRelativePathToFull(SavePath())) return false;
 auto Previous=State;State=Imported;
 auto Kiosk=GetWorld() && GetWorld()->IsGameWorld()?GetWorld()->GetSubsystem<UMareKioskWorld>():nullptr;
 if(Kiosk)Kiosk->ResetPhysicalState();
 if(Save())return true;State=Previous;return false;
}
