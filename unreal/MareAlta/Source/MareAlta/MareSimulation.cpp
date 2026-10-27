#include "MareSimulation.h"
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
 if(!ReadJson(SavePath(),State)) ReadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),State);
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
 Company->SetBoolField(TEXT("kiosk_open"),bOpen); return Save();
}
bool UMareSimulation::IsOpen() const
{
 auto Company=Object(State,TEXT("company")); bool bOpen=false,bCreated=false;
 Company->TryGetBoolField(TEXT("kiosk_open"),bOpen); Company->TryGetBoolField(TEXT("created"),bCreated);
 auto Sim=Object(Company,TEXT("sim")); const double Hour=Number(State,TEXT("minutes"),480)/60.;
 return bOpen && bCreated && Hour>=Number(Sim,TEXT("start"),8) && Hour<Number(Sim,TEXT("end"),18);
}
int32 UMareSimulation::Available(const FString& Dish) const
{
 auto Dishes=Object(Definitions,TEXT("dishes")); if(!Dishes->HasField(Dish)) return 0;
 auto Uses=Object(Object(Dishes,Dish),TEXT("uses")); auto Stock=Object(State,TEXT("stock")); int32 Count=MAX_int32;
 for(const auto& Pair:Uses->Values) Count=FMath::Min(Count,FMath::FloorToInt(Number(Stock,FString(Pair.Key.ToView()))/FMath::Max(1.,Pair.Value->AsNumber())));
 return Count==MAX_int32?0:Count;
}
double UMareSimulation::RestockCost(const FString& Dish,int32 Quantity) const
{
 if(Quantity<1 || Quantity>48 || !Object(Definitions,TEXT("dishes"))->HasField(Dish)) return -1;
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
 for(const auto& Dish:Dishes){if(!Object(Definitions,TEXT("dishes"))->HasField(Dish)) return TEXT("");Items.Add(MakeShared<FJsonValueString>(Dish));}
 Order->SetArrayField(TEXT("remaining"),Items); Orders->SetObjectField(Id,Order); Save(); return Id;
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
bool UMareSimulation::BuyExpansion(const FString& Id)
{
 auto Expansions=Object(Definitions,TEXT("expansions")); if(!Expansions->HasField(Id)) return false;
 auto Unlocked=Object(State,TEXT("unlocked")); bool bOwned=false;Unlocked->TryGetBoolField(Id,bOwned);if(bOwned)return false;
 auto Expansion=Object(Expansions,Id); const TArray<TSharedPtr<FJsonValue>>* Required=nullptr;
 if(Expansion->TryGetArrayField(TEXT("req"),Required)) for(const auto& Req:*Required){bool bHas=false;Unlocked->TryGetBoolField(Req->AsString(),bHas);if(!bHas)return Fail(TEXT("Compre as expansões anteriores."));}
 const double Cost=Number(Expansion,TEXT("cost")); if(Money()<Cost) return Fail(TEXT("Saldo insuficiente."));
 Unlocked->SetBoolField(Id,true);Book(-Cost,TEXT("Expansão: ")+Id);return Save();
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
 return bValue?1:0;
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
 ReturnCarry();ReturnCarry(true);Object(State,TEXT("company"))->SetBoolField(TEXT("kiosk_open"),false);
 State->SetNumberField(TEXT("day"),Number(State,TEXT("day"),1)+1);State->SetNumberField(TEXT("minutes"),480);
 State->SetObjectField(TEXT("ue_orders"),MakeShared<FJsonObject>());Save();
}
bool UMareSimulation::Save()
{
 FString Text;if(!FJsonSerializer::Serialize(State.ToSharedRef(),TJsonWriterFactory<>::Create(&Text))) return false;
 const FString Path=SavePath(),Temp=Path+TEXT(".tmp");IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
 if(!FFileHelper::SaveStringToFile(Text,*Temp,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) return Fail(TEXT("Falha ao salvar."));
 return IFileManager::Get().Move(*Path,*Temp,true,true);
}
bool UMareSimulation::ImportLegacySave(const FString& Path)
{
 TSharedPtr<FJsonObject> Imported;if(!ReadJson(Path,Imported) || !Imported->HasTypedField<EJson::Object>(TEXT("company")) || !Imported->HasTypedField<EJson::Number>(TEXT("money"))) return Fail(TEXT("Save incompatível."));
 if(FPaths::ConvertRelativePathToFull(Path)==FPaths::ConvertRelativePathToFull(SavePath())) return false;
 auto Previous=State;State=Imported;if(Save()) return true;State=Previous;return false;
}
