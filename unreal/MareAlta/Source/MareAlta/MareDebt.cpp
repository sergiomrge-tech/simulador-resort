// Grandma's debt (CHECKLIST_EXPANSOES item 10, docs/ue58/DIVIDA_DA_AVO.md, Content/Data/debt.json).
// Dona Dilce left the kiosk and a R$ 1.000.000 debt. No interest, no instalments: the player pays when they want on the
// phone (Finanças). Everything in prog.debt is kept in cents; the principal is frozen in the save when it is created.
// The demo can pay up to demo_payment_cap and never reaches the finale.
#include "MareSimulation.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 int64 Cents(double Reais){return (int64)FMath::RoundToDouble(Reais*100.0);}
 int64 Int(const TSharedPtr<FJsonObject>& O,const TCHAR* Key){double V=0;O->TryGetNumberField(Key,V);return (int64)V;}
}

TSharedPtr<FJsonObject> UMareSimulation::DebtDefs() const
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/debt.json")));   // i18n:skip
  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 return Defs;
}

bool UMareSimulation::IsDemo() const{bool bDemo=false;if(Definitions.IsValid())Definitions->TryGetBoolField(TEXT("demo"),bDemo);return bDemo;}

bool UMareSimulation::HasDebt() const
{
 return State.IsValid() && Object(State,TEXT("prog"))->HasTypedField<EJson::Object>(TEXT("debt"));   // i18n:skip
}

bool UMareSimulation::EnsureDebt()
{
 auto Prog=Object(State,TEXT("prog"));
 const int32 Day=FMath::Max(1,int32(Number(State,TEXT("day"),1)));
 if(Prog->HasTypedField<EJson::Object>(TEXT("debt"))){   // i18n:skip
  // An existing debt is never recreated: the principal stays frozen even if debt.json changes. Only repair broken fields.
  auto D=Prog->GetObjectField(TEXT("debt"));bool bFixed=false;   // i18n:skip
  if(Int(D,TEXT("principal_cents"))<=0){D->SetNumberField(TEXT("principal_cents"),double(Cents(Number(DebtDefs(),TEXT("principal"),1000000))));bFixed=true;}   // i18n:skip
  const int64 Paid=Int(D,TEXT("paid_cents"));
  if(Paid<0 || Paid>Int(D,TEXT("principal_cents"))){D->SetNumberField(TEXT("paid_cents"),double(FMath::Clamp<int64>(Paid,0,Int(D,TEXT("principal_cents")))));bFixed=true;}
  if(!D->HasTypedField<EJson::Array>(TEXT("milestones_seen"))){D->SetArrayField(TEXT("milestones_seen"),{});bFixed=true;}
  return bFixed?Save():true;
 }
 auto D=MakeShared<FJsonObject>();
 D->SetNumberField(TEXT("version"),1);
 D->SetNumberField(TEXT("principal_cents"),double(Cents(Number(DebtDefs(),TEXT("principal"),1000000))));   // i18n:skip
 D->SetNumberField(TEXT("paid_cents"),0);
 D->SetNumberField(TEXT("created_day"),Day);D->SetNumberField(TEXT("last_payment_day"),Day);D->SetNumberField(TEXT("last_reminder_day"),0);
 D->SetBoolField(TEXT("intro_seen"),false);D->SetBoolField(TEXT("finale_seen"),false);D->SetArrayField(TEXT("milestones_seen"),{});
 Prog->SetObjectField(TEXT("debt"),D);   // i18n:skip
 return Save();
}

int64 UMareSimulation::DebtPrincipalCents() const{return HasDebt()?Int(Object(Object(State,TEXT("prog")),TEXT("debt")),TEXT("principal_cents")):Cents(Number(DebtDefs(),TEXT("principal"),1000000));}   // i18n:skip
int64 UMareSimulation::DebtPaidCents() const{return HasDebt()?Int(Object(Object(State,TEXT("prog")),TEXT("debt")),TEXT("paid_cents")):0;}   // i18n:skip
int64 UMareSimulation::DebtBalanceCents() const{return FMath::Max<int64>(0,DebtPrincipalCents()-DebtPaidCents());}
int64 UMareSimulation::DebtLimitCents() const
{
 const int64 Principal=DebtPrincipalCents();
 return IsDemo()?FMath::Min(Principal,Cents(Number(DebtDefs(),TEXT("demo_payment_cap"),250000))):Principal;
}
bool UMareSimulation::IsDebtDemoCapped() const{return IsDemo() && DebtPaidCents()>=DebtLimitCents() && DebtBalanceCents()>0;}

int64 UMareSimulation::DebtMaxPayCents() const
{
 if(!HasDebt())return 0;
 return FMath::Max<int64>(0,FMath::Min3(DebtBalanceCents(),DebtLimitCents()-DebtPaidCents(),Cents(Money())));
}

bool UMareSimulation::DebtCentsFromJson(const TSharedPtr<FJsonValue>& Value,int64& Out)
{
 // Only a JSON number holding whole cents is a payment: no bool, text, null, NaN/Infinity or fractions of a cent.
 if(!Value.IsValid() || Value->Type!=EJson::Number)return false;
 const double V=Value->AsNumber();
 if(!FMath::IsFinite(V) || V!=FMath::FloorToDouble(V) || FMath::Abs(V)>9.0e15)return false;
 Out=(int64)V;return true;
}

bool UMareSimulation::PayDebt(int64 PayCents)
{
 if(bPayingDebt)return false;   // a second click while the first payment is still being saved
 if(!HasDebt()){bool bCreated=false;Object(State,TEXT("company"))->TryGetBoolField(TEXT("created"),bCreated);
  if(!bCreated || !EnsureDebt())return Fail(TEXT("Crie sua empresa primeiro."));}   // old save: the debt arrives now
 const auto Phone=Object(DebtDefs(),TEXT("phone"));   // i18n:skip
 if(PayCents<=0 || PayCents>Cents(Money()) || PayCents>DebtBalanceCents())return Fail(String(Phone,TEXT("invalid")));   // i18n:skip
 if(PayCents>DebtLimitCents()-DebtPaidCents())
  return Fail(String(Phone,TEXT("demo_limit")).Replace(TEXT("{0}"),*FString::Printf(TEXT("%.0f"),DebtLimitCents()/100.0)));   // i18n:skip
 bPayingDebt=true;
 // Everything the payment changes, to undo it if the save fails (no money leaves without a saved receipt).
 auto Prog=Object(State,TEXT("prog"));auto D=Prog->GetObjectField(TEXT("debt"));   // i18n:skip
 const auto DebtCopy=MakeShared<FJsonObject>(*D);
 const double OldMoney=Number(State,TEXT("money")),OldOut=Number(State,TEXT("day_out"));
 TArray<TSharedPtr<FJsonValue>> OldLedger;{const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(State->TryGetArrayField(TEXT("ledger"),L))OldLedger=*L;}
 const bool bHadLedger=State->HasField(TEXT("ledger")),bHadOut=State->HasField(TEXT("day_out"));
 Book(-PayCents/100.0,String(Phone,TEXT("pay")));   // i18n:skip
 D->SetNumberField(TEXT("paid_cents"),double(DebtPaidCents()+PayCents));
 D->SetNumberField(TEXT("last_payment_day"),Number(State,TEXT("day"),1));
 bool bSaved=Save();
 if(!bSaved){
  State->SetNumberField(TEXT("money"),OldMoney);
  if(bHadOut)State->SetNumberField(TEXT("day_out"),OldOut);else State->RemoveField(TEXT("day_out"));
  if(bHadLedger)State->SetArrayField(TEXT("ledger"),OldLedger);else State->RemoveField(TEXT("ledger"));
  Prog->SetObjectField(TEXT("debt"),DebtCopy);   // i18n:skip
  bPayingDebt=false;return Fail(TEXT("Falha ao salvar: o pagamento não foi feito."));
 }
 bPayingDebt=false;
 // 11/11 (seen in the exe: "Pagamento de R$ 740000 recebido"): thousands grouped with a space, like the finale's
 // "R$ 1 000 000" (a space reads the same in the twelve languages; a dot or a comma would not).
 auto Grouped=[](double Reais){FString Whole=FString::Printf(TEXT("%.0f"),FMath::FloorToDouble(Reais));
  for(int32 I=Whole.Len()-3;I>0;I-=3)Whole.InsertAt(I,TEXT(" "));   // i18n:skip
  const int32 Cents=FMath::RoundToInt32((Reais-FMath::FloorToDouble(Reais))*100);return Cents?Whole+FString::Printf(TEXT(",%02d"),Cents):Whole;};   // i18n:skip
 LastMessage=String(Phone,TEXT("receipt")).Replace(TEXT("{0}"),*Grouped(PayCents/100.0))   // i18n:skip
  .Replace(TEXT("{1}"),*Grouped(DebtBalanceCents()/100.0));
 return true;
}

TArray<FString> UMareSimulation::DebtPendingMilestones() const
{
 TArray<FString> Pending;if(!HasDebt())return Pending;
 const auto D=Object(Object(State,TEXT("prog")),TEXT("debt"));   // i18n:skip
 TSet<FString> Seen;{const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(D->TryGetArrayField(TEXT("milestones_seen"),L))for(const auto& V:*L)Seen.Add(V->AsString());}
 const int64 Principal=DebtPrincipalCents(),Paid=DebtPaidCents();
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(DebtDefs()->TryGetArrayField(TEXT("milestones"),List))for(const auto& V:*List){const auto M=V->AsObject();const FString Id=String(M,TEXT("id"));   // i18n:skip
  if(!Seen.Contains(Id) && Paid>=(int64)FMath::RoundToDouble(Principal*Number(M,TEXT("fraction"))))Pending.Add(Id);}   // i18n:skip
 return Pending;
}

bool UMareSimulation::IsDebtFinalePending() const
{
 if(!HasDebt() || IsDemo() || DebtBalanceCents()>0)return false;
 bool bSeen=false;Object(Object(State,TEXT("prog")),TEXT("debt"))->TryGetBoolField(TEXT("finale_seen"),bSeen);return !bSeen;   // i18n:skip
}

bool UMareSimulation::DebtMilestoneTipDue() const{return DebtPendingMilestones().Num()>0 && !IsDebtFinalePending();}

bool UMareSimulation::AckDebt()
{
 if(!HasDebt())return false;
 auto D=Object(Object(State,TEXT("prog")),TEXT("debt"));   // i18n:skip
 const TArray<FString> Pending=DebtPendingMilestones();const bool bFinale=IsDebtFinalePending();
 if(!Pending.Num() && !bFinale)return true;
 const auto Previous=MakeShared<FJsonObject>(*D);
 TArray<TSharedPtr<FJsonValue>> Seen;{const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(D->TryGetArrayField(TEXT("milestones_seen"),L))Seen=*L;}
 for(const FString& Id:Pending)Seen.Add(MakeShared<FJsonValueString>(Id));
 D->SetArrayField(TEXT("milestones_seen"),Seen);if(bFinale)D->SetBoolField(TEXT("finale_seen"),true);
 if(Save())return true;
 Object(State,TEXT("prog"))->SetObjectField(TEXT("debt"),Previous);return false;   // shown again next time   // i18n:skip
}

bool UMareSimulation::DebtReminder(int32 Day)
{
 if(!HasDebt() || DebtBalanceCents()<=0 || (IsDemo() && DebtPaidCents()>=DebtLimitCents()))return false;
 auto D=Object(Object(State,TEXT("prog")),TEXT("debt"));   // i18n:skip
 const int32 Since=FMath::Max3(int32(Int(D,TEXT("created_day"))),int32(Int(D,TEXT("last_payment_day"))),int32(Int(D,TEXT("last_reminder_day"))));
 if(Day-Since<int32(Number(DebtDefs(),TEXT("reminder_every_days"),7)))return false;
 D->SetNumberField(TEXT("last_reminder_day"),Day);
 const auto R=Object(DebtDefs(),TEXT("reminder"));PendingTipTitle=String(R,TEXT("title"));PendingTipText=String(R,TEXT("text"));   // i18n:skip
 Save();return true;
}

bool UMareSimulation::ShowDebtIntro()
{
 // The letter that reveals the million: once, after the company exists (the arrival letter in the house stays as it is).
 bool bCreated=false;Object(State,TEXT("company"))->TryGetBoolField(TEXT("created"),bCreated);if(!bCreated)return false;
 if(!HasDebt())EnsureDebt();if(!HasDebt())return false;
 auto D=Object(Object(State,TEXT("prog")),TEXT("debt"));bool bSeen=false;D->TryGetBoolField(TEXT("intro_seen"),bSeen);if(bSeen)return false;   // i18n:skip
 const auto I=Object(DebtDefs(),TEXT("intro"));   // i18n:skip
 PendingTipTitle=String(I,TEXT("title"));   // i18n:skip
 PendingTipText=String(I,TEXT("letter"))+TEXT("\n")+String(I,TEXT("comfort"))+TEXT("\n")+String(I,TEXT("signature"));   // i18n:skip
 D->SetBoolField(TEXT("intro_seen"),true);Save();return true;
}

FString UMareSimulation::DebtMilestoneTitle(const FString& Id,FString* Text) const
{
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(DebtDefs()->TryGetArrayField(TEXT("milestones"),List))for(const auto& V:*List){const auto M=V->AsObject();   // i18n:skip
  if(String(M,TEXT("id"))==Id){if(Text)*Text=String(M,TEXT("text"));return String(M,TEXT("title"));}}   // i18n:skip
 return FString();
}
