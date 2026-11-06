// Souvenir shop, hands-on (CHECKLIST_EXPANSOES 3.5): crafts bought from the village makers go to the back room and
// onto the shelf (the window sells most), tourists buy every open hour and some want the gift wrapped at the counter
// (fold the paper in the right order, the ribbon in the colour asked), and postcards printed from the player's own
// album photos sell too. Values in Content/Data/business_games.json businesses.souvenir.shop.
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 const TCHAR* TouristNames[]={TEXT("Giovanna"),TEXT("Mr. Peter"),TEXT("Rafa"),TEXT("Dona Neide"),TEXT("Hiroshi"),TEXT("Bruna"),TEXT("Seu Osvaldo"),TEXT("Ingrid"),TEXT("Thiago"),TEXT("Lucía"),TEXT("Pietra"),TEXT("Klaus")};
 TArray<TSharedPtr<FJsonValue>>& Arr(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  if(!O->HasTypedField<EJson::Array>(Key))O->SetArrayField(Key,TArray<TSharedPtr<FJsonValue>>());
  return const_cast<TArray<TSharedPtr<FJsonValue>>&>(O->GetArrayField(Key));
 }
 double Now(const TSharedPtr<FJsonObject>& State){return UMareSimulation::Number(State,TEXT("day"),1)*1440+UMareSimulation::Number(State,TEXT("minutes"));}
 TArray<TSharedPtr<FJsonObject>> Objects(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  TArray<TSharedPtr<FJsonObject>> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(O->TryGetArrayField(Key,L))for(const auto& V:*L)Out.Add(V->AsObject());return Out;
 }
}

TSharedPtr<FJsonObject> UMareSimulation::SouvenirDefs() const{return BizGameDefs(TEXT("souvenir"));}
double UMareSimulation::WrapFee() const{return Number(SouvenirDefs(),TEXT("wrap_fee"),6)*BizSaleMult(TEXT("souvenir"));}
double UMareSimulation::SouvenirPrice(const TSharedPtr<FJsonObject>& Craft) const{return FMath::RoundToDouble(Number(Craft,TEXT("price"),10)*BizSaleMult(TEXT("souvenir")));}
TSharedPtr<FJsonObject> UMareSimulation::SouvenirState() const{return Object(Object(Object(State,TEXT("prog")),TEXT("biz")),TEXT("souvenir"));}
TArray<TSharedPtr<FJsonObject>> UMareSimulation::SouvenirQueue() const{return Objects(SouvenirState(),TEXT("queue"));}
TArray<TSharedPtr<FJsonObject>> UMareSimulation::SouvenirCards() const{return Objects(SouvenirState(),TEXT("cards"));}

TSharedPtr<FJsonObject> UMareSimulation::SouvenirCraft(const FString& Id) const
{
 for(const auto& C:Objects(SouvenirDefs(),TEXT("crafts")))if(String(C,TEXT("id"))==Id)return C;
 return nullptr;
}

TArray<TSharedPtr<FJsonObject>> UMareSimulation::SouvenirShelf() const
{
 // The shelf starts with the first crafts from Dona Rita (start_shelf) the first time it is looked at.
 auto R=SouvenirState();const int32 Slots=Objects(SouvenirDefs(),TEXT("slots")).Num();auto& Shelf=Arr(R,TEXT("shelf"));
 if(Shelf.IsEmpty()){const TArray<TSharedPtr<FJsonValue>>* Start=nullptr;SouvenirDefs()->TryGetArrayField(TEXT("start_shelf"),Start);
  for(int32 I=0;I<Slots;++I){auto O=MakeShared<FJsonObject>();
   if(Start && Start->IsValidIndex(I) && (*Start)[I]->AsArray().Num()==2){O->SetStringField(TEXT("item"),(*Start)[I]->AsArray()[0]->AsString());O->SetNumberField(TEXT("qty"),(*Start)[I]->AsArray()[1]->AsNumber());}
   else{O->SetStringField(TEXT("item"),TEXT(""));O->SetNumberField(TEXT("qty"),0);}
   Shelf.Add(MakeShared<FJsonValueObject>(O));}}
 return Objects(R,TEXT("shelf"));
}

int32 UMareSimulation::SouvenirBackStock(const FString& Id) const{return int32(Number(Object(SouvenirState(),TEXT("back")),Id));}

int32 UMareSimulation::SouvenirMakerLeft(const FString& Id) const
{
 // Each maker turns out a few pieces a day, and only once their village chapter is done.
 const auto C=SouvenirCraft(Id);if(!C.IsValid())return 0;const FString Chapter=String(C,TEXT("chapter"));
 if(!Chapter.IsEmpty() && !IsChapterDone(Chapter))return 0;
 const auto R=SouvenirState();const bool bToday=Number(R,TEXT("made_day"),-1)==Number(State,TEXT("day"),1);
 return FMath::Max(0,int32(Number(C,TEXT("daily"),6))-(bToday?int32(Number(Object(R,TEXT("made")),Id)):0));
}

bool UMareSimulation::BuySouvenirCraft(const FString& Id)
{
 const auto C=SouvenirCraft(Id);if(!C.IsValid())return Fail(TEXT("Artesanato desconhecido."));
 const FString Chapter=String(C,TEXT("chapter"));
 if(!Chapter.IsEmpty() && !IsChapterDone(Chapter))return Fail(FString::Printf(TEXT("%s ainda não faz %s: termine a história dele(a) na vila."),*String(C,TEXT("maker")),*String(C,TEXT("name"))));
 const int32 Left=SouvenirMakerLeft(Id);if(Left<=0)return Fail(FString::Printf(TEXT("%s já vendeu tudo o que fez hoje. Volte amanhã."),*String(C,TEXT("maker"))));
 const int32 N=FMath::Min(Left,int32(Number(SouvenirDefs(),TEXT("buy_batch"),4)));const double Cost=Number(C,TEXT("cost"),5)*N;
 if(Money()<Cost)return Fail(FString::Printf(TEXT("Faltam R$ %.0f para comprar %d peça(s)."),Cost-Money(),N));
 auto R=SouvenirState();const double Day=Number(State,TEXT("day"),1);
 if(Number(R,TEXT("made_day"),-1)!=Day){R->SetNumberField(TEXT("made_day"),Day);R->SetObjectField(TEXT("made"),MakeShared<FJsonObject>());}
 auto Made=Object(R,TEXT("made"));Made->SetNumberField(Id,Number(Made,Id)+N);
 auto Back=Object(R,TEXT("back"));Back->SetNumberField(Id,Number(Back,Id)+N);
 Book(-Cost,FString::Printf(TEXT("Lojinha: %d %s (%s)"),N,*String(C,TEXT("name")),*String(C,TEXT("maker"))));
 LastMessage=FString::Printf(TEXT("%s vendeu %d peça(s) de %s por R$ %.0f. Ponha na prateleira!"),*String(C,TEXT("maker")),N,*String(C,TEXT("name")),Cost);
 return Save();
}

bool UMareSimulation::PlaceSouvenir(int32 Slot,const FString& Id)
{
 // Everything of this craft in the back room goes to the slot (up to slot_cap); what was there goes back.
 auto Shelf=SouvenirShelf();if(!Shelf.IsValidIndex(Slot))return Fail(TEXT("Lugar da prateleira inválido."));
 auto Back=Object(SouvenirState(),TEXT("back"));const auto S=Shelf[Slot];const FString Old=String(S,TEXT("item"));const int32 Cap=int32(Number(SouvenirDefs(),TEXT("slot_cap"),10));
 if(Id.IsEmpty() || Id==Old){if(Id.IsEmpty() && !Old.IsEmpty()){Back->SetNumberField(Old,Number(Back,Old)+Number(S,TEXT("qty")));S->SetStringField(TEXT("item"),TEXT(""));S->SetNumberField(TEXT("qty"),0);return Save();}
  if(Id.IsEmpty())return true;}
 if(!SouvenirCraft(Id).IsValid())return Fail(TEXT("Artesanato desconhecido."));
 if(Id!=Old){
  // The same craft on two slots would split it: move it from wherever it already stands.
  for(int32 I=0;I<Shelf.Num();++I)if(I!=Slot && String(Shelf[I],TEXT("item"))==Id){Back->SetNumberField(Id,Number(Back,Id)+Number(Shelf[I],TEXT("qty")));Shelf[I]->SetStringField(TEXT("item"),TEXT(""));Shelf[I]->SetNumberField(TEXT("qty"),0);}
  if(!Old.IsEmpty())Back->SetNumberField(Old,Number(Back,Old)+Number(S,TEXT("qty")));
  S->SetStringField(TEXT("item"),Id);S->SetNumberField(TEXT("qty"),0);}
 const int32 Move=FMath::Min(int32(Number(Back,Id)),Cap-int32(Number(S,TEXT("qty"))));
 if(Move<=0 && Number(S,TEXT("qty"))<=0){S->SetStringField(TEXT("item"),TEXT(""));return Fail(TEXT("Nada disso no estoque dos fundos: compre dos artesãos primeiro."));}
 S->SetNumberField(TEXT("qty"),Number(S,TEXT("qty"))+Move);Back->SetNumberField(Id,Number(Back,Id)-Move);
 const auto Slots=Objects(SouvenirDefs(),TEXT("slots"));
 LastMessage=FString::Printf(TEXT("%s: %s, %.0f peça(s)."),*String(Slots[Slot],TEXT("name")),*String(SouvenirCraft(Id),TEXT("name")),Number(S,TEXT("qty")));
 return Save();
}

double UMareSimulation::SouvenirCardPrice(int32 Subjects) const
{
 return FMath::RoundToDouble((Number(SouvenirDefs(),TEXT("card_price"),5)+Number(SouvenirDefs(),TEXT("subject_bonus"),2)*FMath::Clamp(Subjects,0,2))*BizSaleMult(TEXT("souvenir")));
}

bool UMareSimulation::PrintPostcards(const FString& File,int32 Subjects)
{
 const auto D=SouvenirDefs();const int32 Batch=int32(Number(D,TEXT("card_batch"),5));const double Cost=Number(D,TEXT("card_cost"),1.5)*Batch;
 if(File.IsEmpty())return Fail(TEXT("Escolha uma foto do álbum."));
 auto R=SouvenirState();auto& Cards=Arr(R,TEXT("cards"));int32 Total=0;for(const auto& V:Cards)Total+=int32(Number(V->AsObject(),TEXT("qty")));
 if(Total+Batch>int32(Number(D,TEXT("card_max"),30)))return Fail(TEXT("O expositor de cartões-postais está cheio."));
 if(Money()<Cost)return Fail(FString::Printf(TEXT("Faltam R$ %.0f para imprimir."),Cost-Money()));
 TSharedPtr<FJsonObject> Card;for(const auto& V:Cards)if(String(V->AsObject(),TEXT("file"))==File)Card=V->AsObject();
 if(!Card.IsValid()){Card=MakeShared<FJsonObject>();Card->SetStringField(TEXT("file"),File);Card->SetNumberField(TEXT("qty"),0);Cards.Add(MakeShared<FJsonValueObject>(Card));}
 Card->SetNumberField(TEXT("subjects"),Subjects);Card->SetNumberField(TEXT("price"),SouvenirCardPrice(Subjects));Card->SetNumberField(TEXT("qty"),Number(Card,TEXT("qty"))+Batch);
 Book(-Cost,FString::Printf(TEXT("Lojinha: impressão de %d cartões-postais"),Batch));
 LastMessage=FString::Printf(TEXT("%d cartões-postais impressos com a sua foto (R$ %.0f cada)."),Batch,SouvenirCardPrice(Subjects));
 return Save();
}

void UMareSimulation::AddSouvenirGift(const FString& Item)
{
 const auto D=SouvenirDefs();auto R=SouvenirState();auto& Queue=Arr(R,TEXT("queue"));if(Queue.Num()>=int32(Number(D,TEXT("queue_max"),4)))return;
 const auto Ribbons=Objects(D,TEXT("ribbons"));if(Ribbons.IsEmpty())return;
 auto O=MakeShared<FJsonObject>();O->SetStringField(TEXT("item"),Item);O->SetStringField(TEXT("ribbon"),String(Ribbons[FMath::RandRange(0,Ribbons.Num()-1)],TEXT("id")));
 const int32 Next=int32(Number(R,TEXT("next_customer")));R->SetNumberField(TEXT("next_customer"),Next+1);
 O->SetStringField(TEXT("name"),TouristNames[(Next*7+int32(Number(State,TEXT("day"),1)))%UE_ARRAY_COUNT(TouristNames)]);O->SetNumberField(TEXT("since"),Now(State));
 Queue.Add(MakeShared<FJsonValueObject>(O));
}

FString UMareSimulation::SouvenirGiftLine(const TSharedPtr<FJsonObject>& O) const
{
 FString Ribbon=String(O,TEXT("ribbon"));for(const auto& Rb:Objects(SouvenirDefs(),TEXT("ribbons")))if(String(Rb,TEXT("id"))==Ribbon)Ribbon=String(Rb,TEXT("name"));
 const auto C=SouvenirCraft(String(O,TEXT("item")));
 return FString::Printf(TEXT("%s levou %s e quer embrulho para presente com fita %s"),*String(O,TEXT("name")),C.IsValid()?*String(C,TEXT("name")):TEXT("uma lembrança"),*Ribbon);
}

void UMareSimulation::SouvenirHour(int32 Hour)
{
 if(!OwnsBusiness(TEXT("souvenir")))return;const auto D=SouvenirDefs();auto R=SouvenirState();const bool bOpen=IsBusinessOpen(TEXT("souvenir"));
 auto& Queue=Arr(R,TEXT("queue"));int32 Gone=0;
 // The clerk (3.6) wraps the gifts the player left waiting: a plain wrap, clerk_share of the fee, no fame.
 if(HasBizClerk(TEXT("souvenir")) && Queue.Num()){double Sum=0;const int32 N=Queue.Num();
  for(int32 I=0;I<N;++I){const double Paid=FMath::RoundToDouble(WrapFee()*BizClerkShare());Sum+=Paid;BizServed(TEXT("souvenir"),true,Paid,0,0);}
  Queue.Empty();if(Sum>0)Book(Sum,FString::Printf(TEXT("Lojinha: funcionário embrulhou %d presente(s)"),N));}
 for(int32 I=Queue.Num()-1;I>=0;--I)if(!bOpen || Now(State)-Number(Queue[I]->AsObject(),TEXT("since"))>Number(D,TEXT("patience_minutes"),45)){Queue.RemoveAt(I);++Gone;}
 BizLost(TEXT("souvenir"),Gone);
 if(Gone && bOpen)LastMessage=FString::Printf(TEXT("Lojinha: %d turista(s) cansaram de esperar o embrulho."),Gone);
 if(!bOpen)return;
 // Tourists: more with fame, many more on carnaval; the shop is indoors (rain does not stop them).
 const TArray<TSharedPtr<FJsonValue>>* Range=nullptr;int32 Lo=1,Hi=3;if(D->TryGetArrayField(TEXT("browsers"),Range) && Range->Num()==2){Lo=int32((*Range)[0]->AsNumber());Hi=int32((*Range)[1]->AsNumber());}
 double N=FMath::RandRange(Lo,Hi)*(1+Number(D,TEXT("fame_browsers"),.15)*(FameLevel()-1));
 const auto Events=Object(D,TEXT("event_mult"));if(Events->HasField(TodayEvent()))N*=Number(Events,TodayEvent(),1);
 const int32 Browsers=FMath::FloorToInt(N)+(FMath::FRand()<FMath::Frac(N)?1:0);
 auto Shelf=SouvenirShelf();const auto Slots=Objects(D,TEXT("slots"));double Sales=0;int32 Pieces=0,Cards=0;
 for(int32 B=0;B<Browsers;++B){
  // From the window inwards: each slot catches the eye with its own chance (the back shelf is hardly seen).
  for(int32 I=0;I<Shelf.Num() && I<Slots.Num();++I){const auto C=SouvenirCraft(String(Shelf[I],TEXT("item")));if(!C.IsValid() || Number(Shelf[I],TEXT("qty"))<1)continue;
   if(FMath::FRand()>=Number(D,TEXT("buy_chance"),.3)*Number(Slots[I],TEXT("mult"),1)*Number(C,TEXT("appeal"),1))continue;
   Shelf[I]->SetNumberField(TEXT("qty"),Number(Shelf[I],TEXT("qty"))-1);Sales+=SouvenirPrice(C);++Pieces;
   if(FMath::FRand()<Number(D,TEXT("gift_chance"),.45))AddSouvenirGift(String(C,TEXT("id")));
   break;}
  // A postcard on the way out (the dearer ones show the lighthouse, the whales...).
  auto& CardList=Arr(R,TEXT("cards"));
  if(CardList.Num() && FMath::FRand()<Number(D,TEXT("card_chance"),.35)){const int32 K=FMath::RandRange(0,CardList.Num()-1);const auto Card=CardList[K]->AsObject();
   Sales+=Number(Card,TEXT("price"),5);++Cards;Card->SetNumberField(TEXT("qty"),Number(Card,TEXT("qty"))-1);if(Number(Card,TEXT("qty"))<1)CardList.RemoveAt(K);}
 }
 for(auto& S:Shelf)if(Number(S,TEXT("qty"))<1){S->SetNumberField(TEXT("qty"),0);}
 R->SetNumberField(TEXT("sold_pieces"),Number(R,TEXT("sold_pieces"))+Pieces);R->SetNumberField(TEXT("sold_cards"),Number(R,TEXT("sold_cards"))+Cards);
 if(Sales>0){Book(Sales,FString::Printf(TEXT("Lojinha: %d lembrança(s) e %d cartão(ões)-postal(is)"),Pieces,Cards));BizShelfSale(TEXT("souvenir"),Sales);}
 int32 Empty=0;for(const auto& S:Shelf)Empty+=Number(S,TEXT("qty"))<1;
 if(Empty==Shelf.Num() && Browsers>0)LastMessage=TEXT("Lojinha: a prateleira está vazia! Compre artesanato e arrume a vitrine.");
}

FMareIceResult UMareSimulation::WrapGift(const TArray<FString>& Folds,const FString& Ribbon,double Seconds)
{
 FMareIceResult Out;const auto D=SouvenirDefs();auto R=SouvenirState();auto& Queue=Arr(R,TEXT("queue"));
 if(Queue.IsEmpty()){Fail(TEXT("Ninguém esperando embrulho."));return Out;}
 const auto O=Queue[0]->AsObject();TArray<FString> Order;for(const auto& F:Objects(D,TEXT("folds")))Order.Add(String(F,TEXT("id")));
 const bool bFolds=Folds==Order,bRibbon=Ribbon==String(O,TEXT("ribbon")),bFast=Seconds<=Number(D,TEXT("fast_s"),15);
 Out.Hits=int32(bFolds)+int32(bRibbon)+int32(bFast);
 const TArray<TSharedPtr<FJsonValue>>* Pay=nullptr;const double Factor=D->TryGetArrayField(TEXT("pay"),Pay) && Pay->IsValidIndex(Out.Hits)?(*Pay)[Out.Hits]->AsNumber():.33*Out.Hits;
 Out.Paid=FMath::RoundToDouble(WrapFee()*Factor)+(Out.Hits==3?Number(D,TEXT("tip_perfect"),5):0);
 const FString Who=String(O,TEXT("name"));if(Out.Paid>0)Book(Out.Paid,FString::Printf(TEXT("Lojinha: embrulho para %s (%d/3)"),*Who,Out.Hits));
 AddFame(int32(Number(D,TEXT("fame_per_hit"),1))*Out.Hits);R->SetNumberField(TEXT("games"),Number(R,TEXT("games"))+1);
 BizServed(TEXT("souvenir"),false,Out.Paid,Out.Hits,int32(Number(D,TEXT("fame_per_hit"),1))*Out.Hits);
 Queue.RemoveAt(0);Out.bServed=true;
 TArray<FString> Notes;if(!bFolds)Notes.Add(TEXT("papel amassado (dobras fora de ordem)"));if(!bRibbon)Notes.Add(TEXT("fita da cor errada"));if(!bFast)Notes.Add(TEXT("demorou"));
 LastMessage=Notes.IsEmpty()?FString::Printf(TEXT("Que presente lindo! %s pagou R$ %.0f com gorjeta."),*Who,Out.Paid)
  :FString::Printf(TEXT("%s pagou R$ %.0f (%s)."),*Who,Out.Paid,*FString::Join(Notes,TEXT(", ")));
 Save();return Out;
}
