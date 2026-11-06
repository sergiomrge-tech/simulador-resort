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
FString UMareSimulation::SaveFolder() const{return SaveDirectory.IsEmpty()?FPaths::ProjectSavedDir()/TEXT("SaveGames"):SaveDirectory;}
FString UMareSimulation::SlotPath(int32 Slot) const{return SaveFolder()/FString::Printf(TEXT("slot%d.json"),FMath::Clamp(Slot,1,SlotCount));}
FString UMareSimulation::SavePath() const{return SlotPath(ActiveSlot);}
bool UMareSimulation::ReadSave(const FString& Path,TSharedPtr<FJsonObject>& Target) const
{
 return ReadJson(Path,Target) || ReadJson(Path+TEXT(".bak"),Target);
}
FMareSlotInfo UMareSimulation::SlotInfo(int32 Slot) const
{
 FMareSlotInfo Info;TSharedPtr<FJsonObject> Saved;const FString Path=SlotPath(Slot);
 if(!ReadSave(Path,Saved))return Info;
 Info.bExists=true;Info.Day=Number(Saved,TEXT("day"),1);Info.Money=Number(Saved,TEXT("money"));
 Info.Company=String(Object(Saved,TEXT("company")),TEXT("name"));
 Info.SavedAt=IFileManager::Get().GetTimeStamp(*(IFileManager::Get().FileExists(*Path)?Path:Path+TEXT(".bak")));
 return Info;
}
bool UMareSimulation::HasAnySave() const
{
 for(int32 Slot=1;Slot<=SlotCount;++Slot)if(IFileManager::Get().FileExists(*SlotPath(Slot)) || IFileManager::Get().FileExists(*(SlotPath(Slot)+TEXT(".bak"))))return true;
 return false;
}
void UMareSimulation::WriteSlotIndex(int32 Slot) const
{
 auto Index=MakeShared<FJsonObject>();Index->SetNumberField(TEXT("last"),Slot);FString Text;
 IFileManager::Get().MakeDirectory(*SaveFolder(),true);
 if(FJsonSerializer::Serialize(Index,TJsonWriterFactory<>::Create(&Text)))FFileHelper::SaveStringToFile(Text,*(SaveFolder()/TEXT("slots.json")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}
int32 UMareSimulation::LastSlot() const
{
 TSharedPtr<FJsonObject> Index;
 if(ReadJson(SaveFolder()/TEXT("slots.json"),Index)){const int32 Slot=Number(Index,TEXT("last"),1);if(Slot>=1 && Slot<=SlotCount)return Slot;}
 // Profiles from before the slots only have slot1.json: it is slot 1 and the index is created now.
 if(IFileManager::Get().FileExists(*SlotPath(1)))WriteSlotIndex(1);
 return 1;
}
bool UMareSimulation::LoadSlot(int32 Slot)
{
 if(Slot<1 || Slot>SlotCount)return Fail(TEXT("Slot inválido."));
 TSharedPtr<FJsonObject> Loaded;if(!ReadSave(SlotPath(Slot),Loaded))return Fail(TEXT("Slot vazio ou danificado."));
 State=Loaded;ActiveSlot=Slot;WriteSlotIndex(Slot);LastMessage.Empty();return true;
}
bool UMareSimulation::NewGame(int32 Slot)
{
 if(Slot<1 || Slot>SlotCount)return Fail(TEXT("Slot inválido."));
 TSharedPtr<FJsonObject> Fresh;if(!ReadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),Fresh))return Fail(TEXT("Perfil inicial não encontrado."));
 Fresh->SetNumberField(TEXT("ue_intro_stage"),0);
 auto Previous=State;const int32 PreviousSlot=ActiveSlot;State=Fresh;ActiveSlot=Slot;
 if(!WriteState()){State=Previous;ActiveSlot=PreviousSlot;return false;}
 WriteSlotIndex(Slot);LastMessage.Empty();return true;
}
void UMareSimulation::Initialize(FSubsystemCollectionBase& Collection)
{
 Super::Initialize(Collection);
 FParse::Value(FCommandLine::Get(),TEXT("MareSaveRoot="),SaveDirectory);
 int32 Slot=0;ActiveSlot=FParse::Value(FCommandLine::Get(),TEXT("MareSlot="),Slot)?FMath::Clamp(Slot,1,SlotCount):LastSlot();
 ReadJson(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"),Definitions);
 const bool bExistingSave=IFileManager::Get().FileExists(*SavePath()) || IFileManager::Get().FileExists(*(SavePath()+TEXT(".bak")));
 if(!ReadSave(SavePath(),State)) ReadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),State);
 if(!bExistingSave && State.IsValid() && !FParse::Param(FCommandLine::Get(),TEXT("MarePreviewQA")) && !FParse::Param(FCommandLine::Get(),TEXT("MareGraphicsQA")) && !FParse::Param(FCommandLine::Get(),TEXT("MareBench"))) State->SetNumberField(TEXT("ue_intro_stage"),0);
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
TArray<FString> UMareSimulation::KioskMenu() const
{
 TArray<FString> Menu;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Definitions->TryGetArrayField(TEXT("kiosk_menu"),List))for(const auto& V:*List)if(Object(Definitions,TEXT("dishes"))->HasField(V->AsString()))Menu.Add(V->AsString());
 if(Menu.IsEmpty())Menu={TEXT("coco_gelado"),TEXT("suco"),TEXT("caipirinha"),TEXT("petiscos"),TEXT("sorvete_morango"),TEXT("sorvete_chocolate"),TEXT("batata_frita"),TEXT("porcao_peixe")};
 return Menu;
}
bool UMareSimulation::IsHotDish(const FString& Dish) const{bool bHot=false;Object(Object(Definitions,TEXT("dishes")),Dish)->TryGetBoolField(TEXT("hot"),bHot);return bHot;}
bool UMareSimulation::IsDishUnlocked(const FString& Dish) const
{
 if(!Object(Definitions,TEXT("dishes"))->HasField(Dish))return false;
 const FString Requirement=String(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("requires"));   // e.g. grill, drinks
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
bool UMareSimulation::RollVip(const FString& OrderId)
{
 auto Vip=Object(Definitions,TEXT("kiosk_vip"));if(FameLevel()<Number(Vip,TEXT("min_fame"),2) || FMath::FRand()>=Number(Vip,TEXT("odds"),0))return false;
 const TArray<TSharedPtr<FJsonValue>>* Titles=nullptr;const TArray<TSharedPtr<FJsonValue>>* Requests=nullptr;
 if(!Vip->TryGetArrayField(TEXT("titles"),Titles) || !Vip->TryGetArrayField(TEXT("requests"),Requests) || Titles->IsEmpty() || Requests->IsEmpty())return false;
 return MakeVip(OrderId,FMath::RandRange(0,Titles->Num()-1),FMath::RandRange(0,Requests->Num()-1));
}
bool UMareSimulation::MakeVip(const FString& OrderId,int32 Title,int32 Request)
{
 auto Orders=Object(State,TEXT("ue_orders"));if(!Orders->HasField(OrderId))return false;auto Vip=Object(Definitions,TEXT("kiosk_vip"));
 const TArray<TSharedPtr<FJsonValue>>* Titles=nullptr;const TArray<TSharedPtr<FJsonValue>>* Requests=nullptr;
 if(!Vip->TryGetArrayField(TEXT("titles"),Titles) || !Vip->TryGetArrayField(TEXT("requests"),Requests) || !Titles->IsValidIndex(Title) || !Requests->IsValidIndex(Request))return false;
 auto Order=Object(Orders,OrderId);Order->SetBoolField(TEXT("vip"),true);Order->SetStringField(TEXT("vip_title"),(*Titles)[Title]->AsString());
 Order->SetStringField(TEXT("request"),(*Requests)[Request]->AsString());
 LastMessage=TEXT("Cliente VIP no balcão: ")+(*Titles)[Title]->AsString()+TEXT("!");return Save();
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
 // The player's price is charged; the comfort of the kiosk decor adds a tip, smaller when the price feels high.
 const double Price=SalePrice(Dish); Book(Price,TEXT("Venda: ")+Dish);if(bStaff)StaffDid(TEXT("atendente"),1,Price);
 const double Tip=FMath::RoundToDouble(Price*KioskTipRate()*FMath::Clamp(2-PriceRatio(Dish),0.,1.)*100)/100; if(Tip>=.01) Book(Tip,TEXT("Gorjeta"));
 State->SetNumberField(TEXT("kiosk_n"),Number(State,TEXT("kiosk_n"))+1); State->SetNumberField(TEXT("kiosk"),Number(State,TEXT("kiosk"))+Price+Tip);
 if(Dish.StartsWith(TEXT("sorvete_"))){auto Campaign=Object(Object(State,TEXT("prog")),TEXT("campaign"));Campaign->SetNumberField(TEXT("icecream"),Number(Campaign,TEXT("icecream"))+1);}
 // Signature recipes and a beautiful kiosk spread the word faster.
 AddFame(2+(RecipeLevel(Dish)>=Number(Object(CustomDefs(),TEXT("recipes")),TEXT("fame_from_level"),4)?1:0)+(PlaceBeauty(TEXT("kiosk"))>=CustomEffect(TEXT("fame_beauty_threshold"),20)?1:0));
 // Serve/sell steps count only sales made while that chapter step is active.
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;auto Progress=Object(Object(State,TEXT("prog")),TEXT("ch"));
 if(Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){const FString Chapter=String(Value->AsObject(),TEXT("id"));
  if(!IsChapterOpen(Chapter) || IsChapterDone(Chapter))continue;
  const auto Step=Value->AsObject()->GetArrayField(TEXT("steps"))[ChapterStep(Chapter)]->AsObject();const FString Kind=String(Step,TEXT("kind"));
  if(Kind==TEXT("serve") || (Kind==TEXT("sell") && String(Step,TEXT("item"))==Dish))Progress->SetNumberField(Chapter+TEXT("_")+Kind,Number(Progress,Chapter+TEXT("_")+Kind)+1);
 }
 // A famous customer pays an extra tip per item and spreads the word once the whole order is served.
 bool bVip=false;Order->TryGetBoolField(TEXT("vip"),bVip);
 if(bVip){auto Vip=Object(Definitions,TEXT("kiosk_vip"));const double Extra=FMath::RoundToDouble(Price*Number(Vip,TEXT("tip"),.8)*100)/100;
  if(Extra>=.01){Book(Extra,TEXT("Gorjeta VIP"));State->SetNumberField(TEXT("kiosk"),Number(State,TEXT("kiosk"))+Extra);}
  if(Items.IsEmpty()){AddFame(int32(Number(Vip,TEXT("fame"),6)));LastMessage=String(Order,TEXT("vip_title"))+TEXT(" adorou o atendimento e postou sobre o quiosque!");}}
 if(Items.IsEmpty()) Orders->RemoveField(OrderId);
 return Save();
}
bool UMareSimulation::HireAttendant()
{
 auto Staff=Object(State,TEXT("staff")); bool bHired=false;Staff->TryGetBoolField(TEXT("atendente"),bHired);
 if(bHired) return Fail(TEXT("Seu atendente já cuida de todo o atendimento."));
 const double Cost=Number(Object(Object(Definitions,TEXT("staff")),TEXT("atendente")),TEXT("hire"));
 if(Money()<Cost) return Fail(FString::Printf(TEXT("Saldo insuficiente: o atendente custa R$ %.0f. Atenda sozinho e volte depois."),Cost));
 Staff->SetBoolField(TEXT("atendente"),true);Object(State,TEXT("staff_team"))->RemoveField(TEXT("atendente"));TeamList(TEXT("atendente")); Book(-Cost,TEXT("Contratação do atendente"));return Save();
}
bool UMareSimulation::DismissAttendant()
{
 auto Staff=Object(State,TEXT("staff"));bool bHired=false;Staff->TryGetBoolField(TEXT("atendente"),bHired);
 if(!bHired)return Fail(TEXT("Não há atendente contratado."));
 ReturnCarry(true);Staff->SetBoolField(TEXT("atendente"),false);Object(State,TEXT("staff_team"))->RemoveField(TEXT("atendente"));
 LastMessage=TEXT("Atendente dispensado. Você volta a atender o quiosque sozinho.");return Save();
}
bool UMareSimulation::BuyExpansion(const FString& Id)
{
 auto Expansions=Object(Definitions,TEXT("expansions")); if(!Expansions->HasField(Id)) return false;
 auto Unlocked=Object(State,TEXT("unlocked")); bool bOwned=false;Unlocked->TryGetBoolField(Id,bOwned);if(bOwned)return Fail(TEXT("Esta expansão já foi comprada."));
 auto Expansion=Object(Expansions,Id); const TArray<TSharedPtr<FJsonValue>>* Required=nullptr;
 if(Expansion->TryGetArrayField(TEXT("req"),Required)) for(const auto& Req:*Required){bool bHas=false;Unlocked->TryGetBoolField(Req->AsString(),bHas);if(!bHas)return Fail(TEXT("Compre as expansões anteriores."));}
 // Story and fame gates from the data (the Grand Hotel needs the carnaval chapter and fame level 8, as in the Godot game).
 const FString Chapter=String(Expansion,TEXT("chapter"));
 if(!Chapter.IsEmpty() && !IsChapterDone(Chapter))return Fail(TEXT("Conclua antes a história \"")+String(ChapterDefinition(Chapter),TEXT("title"))+TEXT("\" em Histórias da vila."));
 const int32 Fame=Number(Expansion,TEXT("fame"));if(Fame>0 && FameLevel()<Fame)return Fail(FString::Printf(TEXT("Precisa de mais fama (nível %d)."),Fame));
 const double Cost=Number(Expansion,TEXT("cost")); if(Money()<Cost) return Fail(FString::Printf(TEXT("Saldo insuficiente: %s custa R$ %.0f."),*String(Expansion,TEXT("name")),Cost));
 Unlocked->SetBoolField(Id,true);Book(-Cost,TEXT("Expansão: ")+Id);
 if(auto World=GetWorld())if(auto Visual=World->GetSubsystem<UMareVisualWorld>())Visual->RefreshExpansions();
 LastMessage=TEXT("Expansão desbloqueada: ")+String(Expansion,TEXT("name"));return Save();
}
int32 UMareSimulation::MissionAmount(const TSharedPtr<FJsonObject>& Mission) const
{
 const FString Kind=String(Mission,TEXT("kind")),Item=String(Mission,TEXT("item"));
 auto Company=Object(State,TEXT("company")); auto Prog=Object(State,TEXT("prog")); auto Campaign=Object(Prog,TEXT("campaign"));
 if(Kind==TEXT("sales")) return Number(State,TEXT("kiosk_n"));
 if(Kind==TEXT("icecream")) return Number(Campaign,Kind);
 // Fish: every catch is logged per species in prog.fish (MareLeisure.cpp CatchFish); best_<id> keys are sizes.
 if(Kind==TEXT("fish")){int32 Caught=0;for(const auto& Pair:Object(Prog,TEXT("fish"))->Values)if(!FString(Pair.Key.ToView()).StartsWith(TEXT("best_")))Caught+=int32(Pair.Value->AsNumber());
  return FMath::Max(Caught,int32(Number(Campaign,Kind)));}
 bool bValue=false;
 if(Kind==TEXT("company")) Company->TryGetBoolField(TEXT("created"),bValue);
 if(Kind==TEXT("open")) {Company->TryGetBoolField(TEXT("kiosk_open"),bValue);bValue|=Number(State,TEXT("kiosk_n"))>0;}
 if(Kind==TEXT("staff")) Object(State,TEXT("staff"))->TryGetBoolField(TEXT("atendente"),bValue);
 // Photos flag prog.chp (RecordPhoto); chapter_photo is the old name, still read for older saves.
 if(Kind==TEXT("photo")){Object(Prog,TEXT("chp"))->TryGetBoolField(Item,bValue);if(!bValue)Object(Prog,TEXT("chapter_photo"))->TryGetBoolField(Item,bValue);}
 if(Kind==TEXT("expansion"))Object(State,TEXT("unlocked"))->TryGetBoolField(Item,bValue);
 if(Kind==TEXT("chapter"))bValue=IsChapterDone(Item);
 // Story beats of the summit (UMareSummitWorld): met Seu Tibúrcio, offerings left in his basket, the final party.
 if(Kind==TEXT("elder"))Object(State,TEXT("summit"))->TryGetBoolField(TEXT("met"),bValue);
 if(Kind==TEXT("offerings"))return Number(Object(State,TEXT("summit")),TEXT("count"));
 if(Kind==TEXT("finale"))Campaign->TryGetBoolField(TEXT("finale"),bValue);
 // Act 5 (04/11, "campanha 12 h no mínimo"): fame level, recipe levels gained, customization upgrades made.
 if(Kind==TEXT("fame"))return FameLevel();
 if(Kind==TEXT("recipes")){int32 Levels=0;for(const auto& Pair:Object(Definitions,TEXT("dishes"))->Values)Levels+=RecipeLevel(FString(Pair.Key.ToView()))-1;return Levels;}
 if(Kind==TEXT("custom")){int32 Upgrades=0;for(const auto& Place:Object(State,TEXT("custom"))->Values){const TSharedPtr<FJsonObject>* Slots=nullptr;
  if(Place.Value->TryGetObject(Slots))for(const auto& Slot:(*Slots)->Values){const TSharedPtr<FJsonObject>* Row=nullptr;
   if(Slot.Value->TryGetObject(Row))Upgrades+=FMath::Max(0,int32(Number(*Row,TEXT("tier"),1))-1);}}return Upgrades;}
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
 else if(Kind==TEXT("recipes"))Amount=Object(Prog,TEXT("disc"))->Values.Num()+BarDiscoveries();
 else if(Kind==TEXT("biz")){for(const auto& Pair:Object(Prog,TEXT("biz"))->Values)Amount+=OwnsBusiness(FString(Pair.Key.ToView()));}   // bought ones only
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
void UMareSimulation::AddRating(double Value)
{
 TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
 Ratings.Add(MakeShared<FJsonValueNumber>(FMath::Clamp(Value,1.,5.)));while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);
}
double UMareSimulation::HotelOccupancy() const
{
 // Season, parties and upgrade tree are not ported yet; their terms stay neutral.
 // Decor of the four hotel areas and the resort pool add their own occupancy bonus.
 return FMath::Clamp(.42+.12*(Stars()-4.)+.03*(FameLevel()-7)+HotelCustomBonus()+StayBonus(),.15,.98);
}
static constexpr int32 HotelSuites=32;
void UMareSimulation::HotelNight()
{
 bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bOwned);if(!bOwned)return;
 // Suites are paid at check-in at the reception (MareStays.cpp); the night books the restaurant of the
 // guests staying and the hotel crew. Ratings come from the real check-outs.
 constexpr int32 Dining=35,StaffCost=900;int32 Occupied=0;const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;
 if(Object(State,TEXT("stays"))->TryGetArrayField(TEXT("rooms"),Rooms))for(const auto& R:*Rooms)
  Occupied+=String(R->AsObject(),TEXT("place"))==TEXT("hotel") && String(R->AsObject(),TEXT("state"))==TEXT("occupied");
 const double Meals=FMath::RoundToDouble(Occupied*1.7*Dining*PlaceIncomeFactor(TEXT("hotel_restaurante"))*PlaceIncomeFactor(TEXT("hotel_piscina")));
 if(Meals>0)Book(Meals,TEXT("Grand Hotel: restaurante e bar"));
 Book(-StaffCost,TEXT("Grand Hotel: equipe (recepção, cozinha, spa, limpeza)"));
 auto Last=MakeShared<FJsonObject>();Last->SetNumberField(TEXT("occ"),Occupied/double(HotelSuites));Last->SetNumberField(TEXT("rooms"),Occupied);
 Last->SetNumberField(TEXT("dining"),Meals);Last->SetNumberField(TEXT("staff"),StaffCost);
 Object(State,TEXT("prog"))->SetObjectField(TEXT("hotel"),Last);
}
void UMareSimulation::AddFame(int32 Xp)
{
 // A loss (a flop, a missed VIP, an unfair fine) takes xp back, but never below the level already reached.
 if(Xp<0){auto Prog=Object(State,TEXT("prog"));const double Now=Number(Prog,TEXT("fame_xp"));const int32 L=FameLevel();
  const double Floor=L>=2?FameThresholds[FMath::Min(L-1,int32(UE_ARRAY_COUNT(FameThresholds))-1)]:0;Prog->SetNumberField(TEXT("fame_xp"),FMath::Max(Floor,Now+Xp));return;}
 if(Xp==0)return;const int32 Before=FameLevel();auto Prog=Object(State,TEXT("prog"));Prog->SetNumberField(TEXT("fame_xp"),Number(Prog,TEXT("fame_xp"))+Xp);
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
void UMareSimulation::AdvanceMinutes(double Minutes)
{
 const double Before=Number(State,TEXT("minutes")),After=FMath::Clamp(Before+Minutes,0.,1440.);State->SetNumberField(TEXT("minutes"),After);
 // Expansions and businesses earn by the hour: book every full hour the clock has just crossed.
 for(int32 Hour=FMath::FloorToInt(Before/60)+1;Hour<=FMath::FloorToInt(After/60);++Hour)OperateHour(Hour);
}
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
   const double Wage=StaffWage(Role);Wages+=Wage;Book(-Wage,TEXT("Salário: ")+String(Object(Roles,Role),TEXT("name")));
  }
  // Businesses pay their own clerk once per day, like the staff wages above.
  for(const auto& Pair:Object(Definitions,TEXT("businesses"))->Values)if(HasBizClerk(FString(Pair.Key.ToView()))){
   const double Wage=Number(Pair.Value->AsObject(),TEXT("wage"));Wages+=Wage;Book(-Wage,TEXT("Funcionário: ")+String(Pair.Value->AsObject(),TEXT("name")));}
  Hours->SetNumberField(TEXT("wage_day"),Day);
  // Upkeep: 0.5 % a day of what the resort's expansions cost (the Grand Hotel alone is R$ 150): money needs some care.
  const double Upkeep=DailyUpkeep();if(Upkeep>0){Wages+=Upkeep;Book(-Upkeep,TEXT("Manutenção do resort"));}
  // Hands-on stays replace the old sorted pousada occupancy (MareStays.cpp).
  StaysNight();
  HotelNight();
  // A beautiful home brings visitors and talk in the village.
  AddFame(FMath::FloorToInt(PlaceBeauty(TEXT("home"))*PlaceEffect(TEXT("home"),TEXT("fame_per_beauty_night"))));
 }
 auto Summary=MakeShared<FJsonObject>();const double In=Number(State,TEXT("day_in")),Out=Number(State,TEXT("day_out"));
 Summary->SetNumberField(TEXT("day"),Day);Summary->SetNumberField(TEXT("income"),In);Summary->SetNumberField(TEXT("expense"),Out);
 Summary->SetNumberField(TEXT("wages"),Wages);Summary->SetNumberField(TEXT("sales"),Number(State,TEXT("kiosk_n"))-Number(State,TEXT("ue_day_sales_start")));
 Summary->SetNumberField(TEXT("money"),Money());State->SetObjectField(TEXT("ue_last_day"),Summary);
 StaffNight();   // fatigue, rest and absences (MareStaff.cpp); writes ue_last_day.staff_note
 State->SetNumberField(TEXT("day_in"),0);State->SetNumberField(TEXT("day_out"),0);State->SetNumberField(TEXT("ue_day_sales_start"),Number(State,TEXT("kiosk_n")));
 LastMessage=FString::Printf(TEXT("Dia %d encerrado · vendas R$ %.0f · despesas R$ %.0f · saldo do dia R$ %.0f."),Day,In,Out,In-Out);
 {const auto P=Object(Object(State,TEXT("prog")),TEXT("pousada"));const int32 Checkouts=Number(P,TEXT("checkouts"));
  if(Number(P,TEXT("rooms"))>0)LastMessage+=FString::Printf(TEXT(" Hospedagem: %d quarto(s) ocupado(s), %d check-out(s), nota média %.1f."),int32(Number(P,TEXT("occupied"))),Checkouts,Stars());}
 if(Money()<0)LastMessage+=TEXT(" Caixa negativo: venda mais antes de repor estoque.");
 {const FString Note=String(Object(State,TEXT("ue_last_day")),TEXT("staff_note"));if(!Note.IsEmpty())LastMessage+=TEXT(" Equipe: ")+Note;}
 State->SetNumberField(TEXT("day"),Day+1);State->SetNumberField(TEXT("minutes"),480);StartDayEvent();
 State->SetObjectField(TEXT("ue_orders"),MakeShared<FJsonObject>());
 // End of day autosave in the active slot.
 if(Save())LastMessage+=FString::Printf(TEXT(" Jogo salvo no slot %d."),ActiveSlot);
}
bool UMareSimulation::Save()
{
 if(bHoldSaves)return true;
 if(GetWorld() && GetWorld()->IsGameWorld())if(auto Kiosk=GetWorld()->GetSubsystem<UMareKioskWorld>())Kiosk->CaptureState();
 return WriteState();
}
bool UMareSimulation::WriteState()
{
 FString Text;if(!State.IsValid() || !FJsonSerializer::Serialize(State.ToSharedRef(),TJsonWriterFactory<>::Create(&Text))) return false;
 const FString Path=SavePath(),Temp=Path+TEXT(".tmp");IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
 if(!FFileHelper::SaveStringToFile(Text,*Temp,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) return Fail(TEXT("Falha ao salvar."));
 // The previous good file survives as .bak until the next save.
 if(IFileManager::Get().FileExists(*Path) && IFileManager::Get().Copy(*(Path+TEXT(".bak")),*Path,true,true)!=COPY_OK) return Fail(TEXT("Falha ao criar o backup do save."));
 if(!IFileManager::Get().Move(*Path,*Temp,true,true)) return Fail(TEXT("Falha ao salvar."));
 if(!IFileManager::Get().FileExists(*(SaveFolder()/TEXT("slots.json"))))WriteSlotIndex(ActiveSlot);
 return true;
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

// ---------------------------------------------------------------------------------------------
// Customization: tiers of every object and recipe levels (catalogue in Data/customization.json).
TSharedPtr<FJsonObject> UMareSimulation::CustomDefs() const
{
 if(!CustomCatalog.IsValid()){if(!ReadJson(FPaths::ProjectContentDir()/TEXT("Data/customization.json"),CustomCatalog))CustomCatalog=MakeShared<FJsonObject>();}
 return CustomCatalog;
}
TSharedPtr<FJsonObject> UMareSimulation::CustomSlot(const FString& Place,const FString& Slot) const
{
 const TArray<TSharedPtr<FJsonValue>>* Slots=nullptr;
 if(Object(Object(CustomDefs(),TEXT("places")),Place)->TryGetArrayField(TEXT("slots"),Slots))
  for(const auto& Value:*Slots)if(String(Value->AsObject(),TEXT("id"))==Slot)return Value->AsObject();
 return nullptr;
}
int32 UMareSimulation::CustomTier(const FString& Place,const FString& Slot) const
{
 return FMath::Clamp(int32(Number(Object(Object(Object(State,TEXT("custom")),Place),Slot),TEXT("tier"),1)),1,5);
}
bool UMareSimulation::OwnsCustomTier(const FString& Place,const FString& Slot,int32 Tier) const
{
 if(Tier<=1)return true;const TArray<TSharedPtr<FJsonValue>>* Owned=nullptr;
 return Object(Object(Object(State,TEXT("custom")),Place),Slot)->TryGetArrayField(TEXT("owned"),Owned) && Owned->ContainsByPredicate([Tier](const TSharedPtr<FJsonValue>& V){return int32(V->AsNumber())==Tier;});
}
double UMareSimulation::CustomPrice(const FString& Place,const FString& Slot,int32 Tier) const
{
 auto Def=CustomSlot(Place,Slot);if(!Def.IsValid() || Tier<1 || Tier>5)return 0;
 const TArray<TSharedPtr<FJsonValue>>* Mult=nullptr;if(!CustomDefs()->TryGetArrayField(TEXT("price_mult"),Mult) || !Mult->IsValidIndex(Tier-1))return 0;
 return FMath::RoundToDouble(Number(Def,TEXT("base_price"))*(*Mult)[Tier-1]->AsNumber());
}
bool UMareSimulation::BuyCustom(const FString& Place,const FString& Slot,int32 Tier)
{
 auto Def=CustomSlot(Place,Slot);if(!Def.IsValid() || Tier<1 || Tier>5)return Fail(TEXT("Item de personalização desconhecido."));
 const FString Unlock=String(Def,TEXT("unlock"));bool bUnlocked=Unlock.IsEmpty();if(!bUnlocked)Object(State,TEXT("unlocked"))->TryGetBoolField(Unlock,bUnlocked);
 if(!bUnlocked)return Fail(TEXT("Compre antes a expansão ")+String(Object(Object(Definitions,TEXT("expansions")),Unlock),TEXT("name"))+TEXT("."));
 FString Reason;if(!IsPlaceAvailable(Place,&Reason))return Fail(Reason);
 bool bRequiresClosed=false;Object(Object(CustomDefs(),TEXT("places")),Place)->TryGetBoolField(TEXT("requires_closed"),bRequiresClosed);
 if(bRequiresClosed && IsOpen())return Fail(TEXT("Feche o quiosque para trocar a decoração."));
 const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;
 const FString Name=Def->TryGetArrayField(TEXT("tiers"),Tiers) && Tiers->IsValidIndex(Tier-1)?String((*Tiers)[Tier-1]->AsObject(),TEXT("name")):String(Def,TEXT("name"));
 const bool bOwned=OwnsCustomTier(Place,Slot,Tier);
 if(!bOwned){const double Price=CustomPrice(Place,Slot,Tier);if(Money()<Price)return Fail(FString::Printf(TEXT("Saldo insuficiente: %s custa R$ %.0f."),*Name,Price));}
 // Object() hands back a detached object for missing keys: attach the chain before writing.
 auto Custom=Object(State,TEXT("custom"));if(!State->HasField(TEXT("custom")))State->SetObjectField(TEXT("custom"),Custom);
 auto PlaceState=Object(Custom,Place);if(!Custom->HasField(Place))Custom->SetObjectField(Place,PlaceState);
 auto Entry=Object(PlaceState,Slot);if(!PlaceState->HasField(Slot))PlaceState->SetObjectField(Slot,Entry);
 if(!bOwned){const double Price=CustomPrice(Place,Slot,Tier);Book(-Price,String(Def,TEXT("name"))+TEXT(": ")+Name);
  TArray<TSharedPtr<FJsonValue>> Owned;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;
  if(Entry->TryGetArrayField(TEXT("owned"),Existing))Owned=*Existing;Owned.Add(MakeShared<FJsonValueNumber>(Tier));Entry->SetArrayField(TEXT("owned"),Owned);
  LastMessage=FString::Printf(TEXT("Comprado: %s (%s)."),*Name,*String(Def,TEXT("name")));}
 else LastMessage=FString::Printf(TEXT("Em uso: %s."),*Name);
 Entry->SetNumberField(TEXT("tier"),Tier);
 return Save();
}
static double SlotPoints(const UMareSimulation* Sim,const FString& Place,const TCHAR* Key)
{
 double Points=0;const TArray<TSharedPtr<FJsonValue>>* Slots=nullptr;
 if(UMareSimulation::Object(UMareSimulation::Object(Sim->CustomDefs(),TEXT("places")),Place)->TryGetArrayField(TEXT("slots"),Slots))
  for(const auto& V:*Slots){auto Def=V->AsObject();Points+=UMareSimulation::Number(Def,Key)*(Sim->CustomTier(Place,UMareSimulation::String(Def,TEXT("id")))-1);}
 return Points;
}
double UMareSimulation::PlaceComfort(const FString& Place) const{return SlotPoints(this,Place,TEXT("comfort"));}
double UMareSimulation::PlaceBeauty(const FString& Place) const{return SlotPoints(this,Place,TEXT("beauty"));}
double UMareSimulation::CustomEffect(const FString& Key,double Fallback) const{return Number(Object(CustomDefs(),TEXT("effects")),Key,Fallback);}
// Fame brings people to the beach (+4% per level, as in the Godot version); decor adds its own points.
double UMareSimulation::WordOfMouth() const{return FMath::Clamp(1.+(Stars()-3.5)*.17,.7,1.25);}
double UMareSimulation::DailyUpkeep() const
{
 double Upkeep=0;for(const auto& Pair:Object(Definitions,TEXT("expansions"))->Values){bool bOwned=false;Object(State,TEXT("unlocked"))->TryGetBoolField(FString(Pair.Key.ToView()),bOwned);
  if(bOwned)Upkeep+=Number(Pair.Value->AsObject(),TEXT("cost"))*.005;}
 return FMath::RoundToDouble(Upkeep);
}
double UMareSimulation::KioskArrivalFactor() const
{
 // Word of mouth: 3.5 stars keep the traffic, 5 stars bring a quarter more customers, 2 stars a quarter fewer.
 const double Mouth=WordOfMouth();
 return (1+CustomEffect(TEXT("arrival_per_point"),.035)*(PlaceComfort(TEXT("kiosk"))+PlaceBeauty(TEXT("kiosk"))))*(1+.04*(FameLevel()-1))*EventDemand()*Mouth;
}
double UMareSimulation::KioskTipRate() const{return CustomEffect(TEXT("tip_per_comfort"),.015)*PlaceComfort(TEXT("kiosk"));}
double UMareSimulation::KioskPatienceFactor() const{return 1+CustomEffect(TEXT("patience_per_comfort"),.03)*PlaceComfort(TEXT("kiosk"));}
double UMareSimulation::KioskServiceSpeed() const{return 1+CustomEffect(TEXT("speed_per_counter_tier"),.1)*(CustomTier(TEXT("kiosk"),TEXT("balcao"))-1);}
int32 UMareSimulation::RecipeLevel(const FString& Dish) const{return FMath::Clamp(int32(Number(Object(State,TEXT("recipes")),Dish,1)),1,5);}
double UMareSimulation::DishPrice(const FString& Dish) const
{
 const double Base=Number(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("price"));const TArray<TSharedPtr<FJsonValue>>* Mult=nullptr;
 const int32 Level=RecipeLevel(Dish);
 return Object(CustomDefs(),TEXT("recipes"))->TryGetArrayField(TEXT("price_mult"),Mult) && Mult->IsValidIndex(Level-1)?FMath::RoundToDouble(Base*(*Mult)[Level-1]->AsNumber()):Base;
}
double UMareSimulation::SalePrice(const FString& Dish) const
{
 const double Reference=DishPrice(Dish),Set=Number(Object(State,TEXT("prices")),Dish);
 return Set>0?FMath::Clamp(Set,FMath::RoundToDouble(Reference*.5),FMath::RoundToDouble(Reference*2)):Reference;
}
bool UMareSimulation::SetSalePrice(const FString& Dish,double Price)
{
 const double Reference=DishPrice(Dish);if(Reference<=0)return false;
 Price=FMath::Clamp(FMath::RoundToDouble(Price),FMath::RoundToDouble(Reference*.5),FMath::RoundToDouble(Reference*2));
 if(!State->HasTypedField<EJson::Object>(TEXT("prices")))State->SetObjectField(TEXT("prices"),MakeShared<FJsonObject>());
 State->GetObjectField(TEXT("prices"))->SetNumberField(Dish,Price);return true;
}
double UMareSimulation::PriceRatio(const FString& Dish) const{const double Reference=DishPrice(Dish);return Reference>0?SalePrice(Dish)/Reference:1;}
double UMareSimulation::RecipeUpgradeCost(const FString& Dish) const
{
 const int32 Level=RecipeLevel(Dish);if(Level>=5)return 0;const TArray<TSharedPtr<FJsonValue>>* Mult=nullptr;
 if(!Object(CustomDefs(),TEXT("recipes"))->TryGetArrayField(TEXT("cost_mult"),Mult) || !Mult->IsValidIndex(Level))return 0;
 return FMath::RoundToDouble(Number(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("price"))*(*Mult)[Level]->AsNumber());
}
FString UMareSimulation::RecipeTitle(const FString& Dish,int32 Level) const
{
 if(Level<=0)Level=RecipeLevel(Dish);const TArray<TSharedPtr<FJsonValue>>* Notes=nullptr;
 if(Object(Object(CustomDefs(),TEXT("recipes")),TEXT("notes"))->TryGetArrayField(Dish,Notes) && Notes->IsValidIndex(Level-1))return (*Notes)[Level-1]->AsString();
 return String(Object(Object(Definitions,TEXT("dishes")),Dish),TEXT("name"));
}
bool UMareSimulation::UpgradeRecipe(const FString& Dish)
{
 if(!Object(Definitions,TEXT("dishes"))->HasField(Dish))return Fail(TEXT("Prato desconhecido."));
 if(!IsDishUnlocked(Dish))return Fail(TEXT("Libere este produto antes de melhorar a receita."));
 const int32 Level=RecipeLevel(Dish);if(Level>=5)return Fail(TEXT("Esta receita já está no nível máximo."));
 const double Cost=RecipeUpgradeCost(Dish);if(Money()<Cost)return Fail(FString::Printf(TEXT("Saldo insuficiente: a receita custa R$ %.0f."),Cost));
 auto Recipes=Object(State,TEXT("recipes"));if(!State->HasField(TEXT("recipes")))State->SetObjectField(TEXT("recipes"),Recipes);
 Book(-Cost,TEXT("Receita: ")+RecipeTitle(Dish,Level+1));Recipes->SetNumberField(Dish,Level+1);
 LastMessage=FString::Printf(TEXT("Nova receita: %s · agora R$ %.0f."),*RecipeTitle(Dish),DishPrice(Dish));
 return Save();
}
double UMareSimulation::DishDemand(const FString& Dish) const
{
 // Price elasticity: fair price x1, +30% about x0.5, -20% about x1.55 (never below x0.15 or above x1.6).
 const double Elastic=FMath::Clamp(FMath::Exp(-2.2*(PriceRatio(Dish)-1)),.15,1.6);
 return (1+Number(Object(CustomDefs(),TEXT("recipes")),TEXT("demand_per_level"),.5)*(RecipeLevel(Dish)-1))*Elastic;
}
// Places beyond the kiosk: decor effects and the operations of the expansions (customization.json).
static TSharedPtr<FJsonObject> Child(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
{
 if(!Parent->HasTypedField<EJson::Object>(Key))Parent->SetObjectField(Key,MakeShared<FJsonObject>());
 return Parent->GetObjectField(Key);
}
static bool Owns(const TSharedPtr<FJsonObject>& State,const FString& Expansion)
{
 bool bOwned=false;UMareSimulation::Object(State,TEXT("unlocked"))->TryGetBoolField(Expansion,bOwned);return bOwned;
}
TSharedPtr<FJsonObject> UMareSimulation::PlaceDef(const FString& Place) const{return Object(Object(CustomDefs(),TEXT("places")),Place);}
bool UMareSimulation::IsPlaceAvailable(const FString& Place,FString* Reason) const
{
 auto Def=PlaceDef(Place);const FString Unlock=String(Def,TEXT("unlock")),Business=String(Def,TEXT("business"));
 if(!Unlock.IsEmpty() && !Owns(State,Unlock)){if(Reason)*Reason=TEXT("Compre antes a expansão ")+String(Object(Object(Definitions,TEXT("expansions")),Unlock),TEXT("name"))+TEXT(" (Resort).");return false;}
 if(!Business.IsEmpty() && !OwnsBusiness(Business)){if(Reason)*Reason=TEXT("Compre antes o negócio ")+String(Object(Object(Definitions,TEXT("businesses")),Business),TEXT("name"))+TEXT(" (Resort).");return false;}
 return true;
}
double UMareSimulation::PlaceEffect(const FString& Place,const FString& Key,double Fallback) const{return Number(Object(PlaceDef(Place),TEXT("effects")),Key,Fallback);}
double UMareSimulation::SlotSum(const FString& Place,const FString& Key) const
{
 double Sum=0;const TArray<TSharedPtr<FJsonValue>>* Slots=nullptr;
 if(PlaceDef(Place)->TryGetArrayField(TEXT("slots"),Slots))for(const auto& V:*Slots){auto Def=V->AsObject();Sum+=Number(Def,Key)*(CustomTier(Place,String(Def,TEXT("id")))-1);}
 return Sum;
}
double UMareSimulation::PlaceIncomeFactor(const FString& Place) const
{
 return 1+PlaceEffect(Place,TEXT("income_per_point"))*(PlaceComfort(Place)+PlaceBeauty(Place))+SlotSum(Place,TEXT("income"));
}
double UMareSimulation::StayBonus() const
{
 return Owns(State,TEXT("pool"))?PlaceEffect(TEXT("pool"),TEXT("stay_per_point"))*(PlaceComfort(TEXT("pool"))+PlaceBeauty(TEXT("pool"))):0;
}
double UMareSimulation::HotelCustomBonus() const
{
 double Bonus=0;for(const TCHAR* Place:{TEXT("hotel_restaurante"),TEXT("hotel_piscina"),TEXT("hotel_suites"),TEXT("hotel_lazer")})
  Bonus+=PlaceEffect(Place,TEXT("hotel_per_point"))*(PlaceComfort(Place)+PlaceBeauty(Place));
 return Bonus;
}
// Pousada: one bungalow, two more rooms with the pool expansion ("rooms" in definitions), as in the original.
int32 UMareSimulation::RoomsTotal() const
{
 bool bHotel=false;Object(State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
 return PousadaRooms()+(bHotel?HotelSuites:0);
}
int32 UMareSimulation::RoomsOccupied() const
{
 int32 Occupied=0;const TArray<TSharedPtr<FJsonValue>>* Rooms=nullptr;
 if(Object(State,TEXT("stays"))->TryGetArrayField(TEXT("rooms"),Rooms))for(const auto& R:*Rooms)Occupied+=String(R->AsObject(),TEXT("state"))==TEXT("occupied");
 return Occupied;
}
int32 UMareSimulation::ServedToday() const{return FMath::Max(0,int32(Number(State,TEXT("kiosk_n"))-Number(State,TEXT("ue_day_sales_start"))));}
int32 UMareSimulation::PousadaRooms() const
{
 if(!Owns(State,TEXT("pousada")))return 0;auto Ops=Object(Object(CustomDefs(),TEXT("operations")),TEXT("pousada"));
 int32 Rooms=Number(Ops,TEXT("rooms_base"),1);for(const auto& Pair:Object(Definitions,TEXT("expansions"))->Values)
  if(Owns(State,FString(Pair.Key.ToView())))Rooms+=Number(Pair.Value->AsObject(),TEXT("rooms"));
 return Rooms;
}
double UMareSimulation::PousadaRate() const
{
 auto Ops=Object(Object(CustomDefs(),TEXT("operations")),TEXT("pousada"));
 return FMath::RoundToDouble(Number(Ops,TEXT("rate_base"),100)+Number(Ops,TEXT("star_bonus"),12)*Stars()+SlotSum(TEXT("pousada"),TEXT("rate")));
}
double UMareSimulation::PousadaOccupancy() const
{
 auto Ops=Object(Object(CustomDefs(),TEXT("operations")),TEXT("pousada"));
 const double Maid=HasStaff(String(Ops,TEXT("maid")))?Number(Ops,TEXT("maid_bonus"),.1):0;
 return FMath::Clamp(Number(Ops,TEXT("occupancy"),.45)+Number(Ops,TEXT("fame_occupancy"),.03)*(FameLevel()-1)+PlaceEffect(TEXT("pousada"),TEXT("occupancy_per_comfort"))*PlaceComfort(TEXT("pousada"))
  +PlaceEffect(TEXT("pousada"),TEXT("occupancy_per_beauty"))*PlaceBeauty(TEXT("pousada"))+StayBonus()+Maid,.15,1.);
}
void UMareSimulation::PousadaNight()
{
 const int32 Rooms=PousadaRooms();if(Rooms<=0)return;
 // Expected occupancy, rounded with chance so a single bungalow is not always full or always empty.
 const double Expected=Rooms*PousadaOccupancy();const int32 Occupied=FMath::Clamp(int32(Expected)+(FMath::FRand()<FMath::Frac(Expected)?1:0),0,Rooms);
 const double Rate=PousadaRate(),Revenue=Occupied*Rate;
 const double Tips=FMath::RoundToDouble(Revenue*Number(Object(Object(CustomDefs(),TEXT("operations")),TEXT("pousada")),TEXT("tip"),.04)*PlaceIncomeFactor(TEXT("pousada")));
 if(Revenue>0)Book(Revenue,FString::Printf(TEXT("Pousada: %d de %d quartos ocupados"),Occupied,Rooms));
 if(Tips>0)Book(Tips,TEXT("Pousada: gorjetas"));
 auto Last=MakeShared<FJsonObject>();Last->SetNumberField(TEXT("rooms"),Rooms);Last->SetNumberField(TEXT("occupied"),Occupied);
 Last->SetNumberField(TEXT("rate"),Rate);Last->SetNumberField(TEXT("rev"),Revenue+Tips);Child(State,TEXT("prog"))->SetObjectField(TEXT("pousada"),Last);
 if(Occupied>0){TArray<TSharedPtr<FJsonValue>> Ratings;const TArray<TSharedPtr<FJsonValue>>* Existing=nullptr;if(State->TryGetArrayField(TEXT("ratings"),Existing))Ratings=*Existing;
  const double Comfort=PlaceComfort(TEXT("pousada"));
  for(int32 I=0;I<Occupied;++I)Ratings.Add(MakeShared<FJsonValueNumber>(FMath::Clamp(FMath::FRandRange(3.4,4.4)+.025*Comfort,1.,5.)));
  while(Ratings.Num()>40)Ratings.RemoveAt(0);State->SetArrayField(TEXT("ratings"),Ratings);AddFame(Occupied);}
}
int32 UMareSimulation::TourSeats(const TSharedPtr<FJsonObject>& Tour) const
{
 return Number(Tour,TEXT("seats"),6)+FMath::RoundToInt(SlotSum(TEXT("passeios"),TEXT("seats")))+(FameLevel()>=8?2:0);
}
int32 UMareSimulation::TourPassengers(const TSharedPtr<FJsonObject>& Tour) const
{
 const double Guests=Number(Object(Object(State,TEXT("prog")),TEXT("pousada")),TEXT("occupied"));
 const double Pax=1+Stars()*1.2+Guests*1.5+.3*(FameLevel()-1)+.08*(PlaceComfort(TEXT("passeios"))+PlaceBeauty(TEXT("passeios")));
 // Word of mouth (2.5): yesterday's rating of this tour brings more (or fewer) people today.
 return FMath::Clamp(FMath::RoundToInt(Pax*(String(State,TEXT("weather"))==TEXT("rain")?.6:1.))+TourBuzz(String(Tour,TEXT("id"))),1,TourSeats(Tour));
}
double UMareSimulation::HourlyIncome(const FString& Id) const
{
 auto Op=Object(Object(Object(CustomDefs(),TEXT("operations")),TEXT("hourly")),Id);
 const FString Role=String(Op,TEXT("staff"));const double Staff=!Role.IsEmpty() && HasStaff(Role)?1+Number(Op,TEXT("staff_bonus"))*StaffSkill(Role):1;
 const double Weather=String(State,TEXT("weather"))==TEXT("rain")?.6:1;
 const double Clean=Id==TEXT("pool")?PoolCleanliness():1;   // leaves and towels at the pool cost customers
 return Number(Op,TEXT("guests"),2)*Number(Op,TEXT("spend"),10)*PlaceIncomeFactor(Id)*(1+.04*(FameLevel()-1))*Staff*Weather*Clean;
}
double UMareSimulation::BusinessRate(const FString& Id) const
{
 auto Ops=Object(CustomDefs(),TEXT("operations"));auto Def=Object(Object(Definitions,TEXT("businesses")),Id);
 const bool bRainProof=Id==TEXT("food_truck") || Id==TEXT("souvenir");
 const double Weather=!bRainProof && String(State,TEXT("weather"))==TEXT("rain")?Number(Ops,TEXT("business_rain"),.4):1;
 return Number(Def,TEXT("hour"))*BizPriceMult(Id)*(1+Number(Ops,TEXT("business_fame"),.06)*(FameLevel()-1))*PlaceIncomeFactor(TEXT("biz_")+Id)*Weather;
}
void UMareSimulation::OperateHour(int32 Hour)
{
 // The hour index guards against booking twice when tests or the day close move the clock back.
 const int32 Day=Number(State,TEXT("day"),1);auto Ops=Child(State,TEXT("ue_ops"));const int32 Index=Day*24+Hour;
 if(Number(Ops,TEXT("hour"),-1)>=Index)return;Ops->SetNumberField(TEXT("hour"),Index);
 // Staff shifts are checked against the hour being operated, not the clock (Advance may cross several hours).
 TGuardValue<int32> Duty(DutyHour,Hour-1);StaffHour(Hour);
 if(Number(Ops,TEXT("day"),-1)!=Day){Ops->SetNumberField(TEXT("day"),Day);Ops->SetObjectField(TEXT("today"),MakeShared<FJsonObject>());}
 auto Today=Child(Ops,TEXT("today"));const int32 Started=Hour-1;double Total=0;TArray<FString> Parts;
 auto Add=[&](const FString& Place,const FString& Label,double Amount){Amount=FMath::RoundToDouble(Amount);if(Amount<=0)return;
  Today->SetNumberField(Place,Number(Today,Place)+Amount);Total+=Amount;Parts.Add(FString::Printf(TEXT("%s R$ %.0f"),*Label,Amount));};
 StaysHour(Hour);BarHour(Hour);IceCreamHour(Hour);PastelHour(Hour);RentalHour(Hour);SouvenirHour(Hour);PoolHour(Hour);RestaurantHour(Hour);GameRoomHour(Hour);HotelEventsHour(Hour);
 auto Defs=Object(CustomDefs(),TEXT("operations"));
 for(const auto& Pair:Object(Defs,TEXT("hourly"))->Values){const FString Id(Pair.Key.ToView());auto Op=Pair.Value->AsObject();
  const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;if(!Owns(State,String(Op,TEXT("unlock"))) || !Op->TryGetArrayField(TEXT("open"),Open) || Open->Num()!=2)continue;
  if(Started>=(*Open)[0]->AsNumber() && Started<(*Open)[1]->AsNumber())Add(Id,String(Op,TEXT("name")),HourlyIncome(Id)*FMath::FRandRange(.85,1.15));}
 // Tours sell tickets at the pier and leave guided by the player or the guide (MareTours.cpp).
 ToursHour(Hour);
 for(const auto& Pair:Object(Definitions,TEXT("businesses"))->Values){const FString Id(Pair.Key.ToView());if(!OwnsBusiness(Id))continue;
  // Businesses with a line earn per customer (served by the player or the clerk, 3.6); the others pay a flat rate
  // per open hour only with the clerk hired, at his share.
  if(BizGameKey(Id) || !HasBizClerk(Id))continue;
  const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;if(!Pair.Value->AsObject()->TryGetArrayField(TEXT("open"),Open) || Open->Num()!=2)continue;
  if(Started>=(*Open)[0]->AsNumber() && Started<(*Open)[1]->AsNumber()){const double Paid=FMath::RoundToDouble(BusinessRate(Id)*BizClerkShare()*FMath::FRandRange(.85,1.15));
   BizServed(Id,true,Paid,0,0);BizBookToday(Id,-Paid);Add(TEXT("biz_")+Id,String(Pair.Value->AsObject(),TEXT("name")),Paid);}}
 // One ledger line per hour keeps the statement readable; the phone shows the split per place.
 if(Total>0)Book(Total,FString::Printf(TEXT("Resort %02dh–%02dh: "),Started,Hour)+FString::Join(Parts,TEXT(" · ")));
}
double UMareSimulation::OpsToday(const FString& Place) const
{
 auto Ops=Object(State,TEXT("ue_ops"));return Number(Ops,TEXT("day"),-1)==Number(State,TEXT("day"),1)?Number(Object(Ops,TEXT("today")),Place):0;
}
bool UMareSimulation::HasStaff(const FString& Role) const{return StaffOnDuty(Role);}   // hired and on duty now (MareStaff.cpp)
bool UMareSimulation::HireStaff(const FString& Role)
{
 auto Def=Object(Object(Definitions,TEXT("staff")),Role);bool bLegacy=false;Def->TryGetBoolField(TEXT("company"),bLegacy);
 if(!Object(Definitions,TEXT("staff"))->HasField(Role) || bLegacy)return Fail(TEXT("Cargo desconhecido."));
 bool bHired=false;Object(State,TEXT("staff"))->TryGetBoolField(Role,bHired);if(bHired)return Fail(String(Def,TEXT("name"))+TEXT(" já foi contratado."));
 const FString Req=String(Def,TEXT("req"));if(!Req.IsEmpty() && !Owns(State,Req))return Fail(TEXT("Compre antes a expansão ")+String(Object(Object(Definitions,TEXT("expansions")),Req),TEXT("name"))+TEXT("."));
 const double Cost=Number(Def,TEXT("hire"));if(Money()<Cost)return Fail(FString::Printf(TEXT("Saldo insuficiente: a contratação custa R$ %.0f."),Cost));
 Child(State,TEXT("staff"))->SetBoolField(Role,true);Child(State,TEXT("staff_team"))->RemoveField(Role);TeamList(Role);
 Book(-Cost,TEXT("Contratação: ")+String(Def,TEXT("name")));
 LastMessage=String(Def,TEXT("name"))+TEXT(" contratado. Salário pago ao dormir.");return Save();
}
bool UMareSimulation::DismissStaff(const FString& Role)
{
 if(Role==TEXT("atendente"))return DismissAttendant();bool bHired=false;Object(State,TEXT("staff"))->TryGetBoolField(Role,bHired);
 if(!bHired)return Fail(TEXT("Ninguém contratado neste cargo."));
 Child(State,TEXT("staff"))->SetBoolField(Role,false);Child(State,TEXT("staff_team"))->RemoveField(Role);LastMessage=String(Object(Object(Definitions,TEXT("staff")),Role),TEXT("name"))+TEXT(" dispensado.");return Save();
}
bool UMareSimulation::OwnsBusiness(const FString& Id) const{return Number(Object(Object(Object(State,TEXT("prog")),TEXT("biz")),Id),TEXT("lvl"))>0;}
bool UMareSimulation::CanBuyBusiness(const FString& Id,FString& Reason) const
{
 auto Def=Object(Object(Definitions,TEXT("businesses")),Id);if(!Object(Definitions,TEXT("businesses"))->HasField(Id)){Reason=TEXT("Negócio desconhecido.");return false;}
 if(OwnsBusiness(Id)){Reason=TEXT("Você já é dono deste negócio.");return false;}
 const FString Chapter=String(Def,TEXT("chapter"));
 if(!Chapter.IsEmpty() && !IsChapterDone(Chapter)){Reason=TEXT("Conclua a história \"")+String(ChapterDefinition(Chapter),TEXT("title"))+TEXT("\" da vila.");return false;}
 if(FameLevel()<Number(Def,TEXT("fame"))){Reason=FString::Printf(TEXT("Precisa de fama nível %.0f."),Number(Def,TEXT("fame")));return false;}
 return true;
}
bool UMareSimulation::BuyBusiness(const FString& Id)
{
 FString Reason;if(!CanBuyBusiness(Id,Reason))return Fail(Reason);auto Def=Object(Object(Definitions,TEXT("businesses")),Id);
 const double Cost=Number(Def,TEXT("cost"));if(Money()<Cost)return Fail(FString::Printf(TEXT("Saldo insuficiente: o negócio custa R$ %.0f."),Cost));
 auto Business=MakeShared<FJsonObject>();Business->SetNumberField(TEXT("lvl"),1);Child(Child(State,TEXT("prog")),TEXT("biz"))->SetObjectField(Id,Business);
 Book(-Cost,TEXT("Negócio: ")+String(Def,TEXT("name")));
 if(auto World=GetWorld())if(auto Visual=World->GetSubsystem<UMareVisualWorld>())Visual->RefreshExpansions();
 LastMessage=TEXT("Negócio comprado: ")+String(Def,TEXT("name"))+FString::Printf(TEXT(". O funcionário atende sozinho com %.0f%% da renda; atendendo você mesmo rende 100%% e fama."),BizClerkShare()*100);return Save();
}
double UMareSimulation::HomeSpeedFactor() const{return 1+PlaceEffect(TEXT("home"),TEXT("speed_per_comfort"))*PlaceComfort(TEXT("home"));}
FString UMareSimulation::PlaceSummary(const FString& Place) const
{
 const double Comfort=PlaceComfort(Place),Beauty=PlaceBeauty(Place);FString Head=FString::Printf(TEXT("Conforto %.0f · Beleza %.0f"),Comfort,Beauty);
 if(Place==TEXT("kiosk"))return Head+FString::Printf(TEXT(" · movimento ×%.2f · gorjeta %.0f%% · paciência ×%.2f"),KioskArrivalFactor(),KioskTipRate()*100,KioskPatienceFactor());
 if(Place==TEXT("bar") || Place==TEXT("pool")){FString Line=Head+FString::Printf(TEXT(" · renda ×%.2f · ~R$ %.0f por hora aberta · hoje R$ %.0f"),PlaceIncomeFactor(Place),HourlyIncome(Place),OpsToday(Place));
  if(Place==TEXT("bar"))Line+=HasStaff(TEXT("bartender"))?TEXT(" · bartender +15%"):TEXT(" · contrate um bartender (+15%)");
  if(Place==TEXT("pool"))Line+=FString::Printf(TEXT(" · hóspedes +%.0f%% de ocupação"),StayBonus()*100);return Line;}
 if(Place==TEXT("pousada"))return Head+FString::Printf(TEXT(" · %d quarto(s) · diária R$ %.0f · ocupação prevista %.0f%%%s"),PousadaRooms(),PousadaRate(),PousadaOccupancy()*100,HasStaff(TEXT("camareira"))?TEXT(""):TEXT(" · contrate uma camareira (+10%)"));
 if(Place==TEXT("passeios")){FString Line=Head+FString::Printf(TEXT(" · preço ×%.2f · hoje R$ %.0f"),PlaceIncomeFactor(Place),OpsToday(Place));const TArray<TSharedPtr<FJsonValue>>* Tours=nullptr;
  if(Object(CustomDefs(),TEXT("operations"))->TryGetArrayField(TEXT("tours"),Tours))for(const auto& V:*Tours){auto Tour=V->AsObject();Line+=FString::Printf(TEXT(" · %s %.0fh %d/%d vagas"),*String(Tour,TEXT("name")),Number(Tour,TEXT("hour")),TourPassengers(Tour),TourSeats(Tour));}
  return Line+(HasStaff(TEXT("guia"))?TEXT(""):TEXT(" · sem guia contratado os passeios não saem"));}
 if(Place.StartsWith(TEXT("hotel_")))return Head+FString::Printf(TEXT(" · ocupação do hotel %.0f%% · diária R$ %.0f · decoração do hotel +%.0f%%"),HotelOccupancy()*100,220+SlotSum(TEXT("hotel_suites"),TEXT("rate")),HotelCustomBonus()*100);
 if(Place.StartsWith(TEXT("biz_"))){const FString Id=Place.RightChop(4);const TArray<TSharedPtr<FJsonValue>>* Open=nullptr;FString Hours;
  if(Object(Object(Definitions,TEXT("businesses")),Id)->TryGetArrayField(TEXT("open"),Open) && Open->Num()==2)Hours=FString::Printf(TEXT(" · aberto %.0fh–%.0fh"),(*Open)[0]->AsNumber(),(*Open)[1]->AsNumber());
  return Head+FString::Printf(TEXT(" · ~R$ %.0f por hora%s · hoje R$ %.0f"),BusinessRate(Id),*Hours,OpsToday(Place));}
 if(Place==TEXT("home"))return Head+FString::Printf(TEXT(" · você anda %.0f%% mais rápido · +%.0f de fama por noite"),(HomeSpeedFactor()-1)*100,FMath::FloorToDouble(Beauty*PlaceEffect(Place,TEXT("fame_per_beauty_night"))));
 return Head;
}
