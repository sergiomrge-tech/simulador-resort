// Staff refinement: shifts, days off, two people per role, levels and fatigue (pendências seção 3).
// Rules in definitions.json staff_rules; state in staff_team. The hire flag stays in State.staff (old saves, kiosk).
#include "MareSimulation.h"
#include "Dom/JsonValue.h"

namespace
{
 TSharedPtr<FJsonObject> Child(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
 {
  const TSharedPtr<FJsonObject>* Found=nullptr;if(Parent->TryGetObjectField(Key,Found))return *Found;
  auto Created=MakeShared<FJsonObject>();Parent->SetObjectField(Key,Created);return Created;
 }
 TSharedPtr<FJsonObject> NewWorker(const FString& Shift)
 {
  auto W=MakeShared<FJsonObject>();W->SetStringField(TEXT("shift"),Shift);W->SetNumberField(TEXT("off"),-1);
  W->SetNumberField(TEXT("level"),1);W->SetNumberField(TEXT("xp"),0);W->SetNumberField(TEXT("fatigue"),0);
  W->SetNumberField(TEXT("absent_day"),-1);W->SetNumberField(TEXT("hours_today"),0);return W;
 }
}

static TSharedPtr<FJsonObject> Rules(const UMareSimulation* S){return UMareSimulation::Object(S->Definitions,TEXT("staff_rules"));}
static bool Hired(const UMareSimulation* S,const FString& Role){bool b=false;UMareSimulation::Object(S->State,TEXT("staff"))->TryGetBoolField(Role,b);return b;}
static bool Exempt(const UMareSimulation* S,const FString& Role)
{
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Rules(S)->TryGetArrayField(TEXT("exempt"),List))for(const auto& V:*List)if(V->AsString()==Role)return true;
 return false;
}

TArray<TSharedPtr<FJsonValue>>& UMareSimulation::TeamList(const FString& Role)
{
 auto Team=Child(State,TEXT("staff_team"));
 if(!Team->HasTypedField<EJson::Array>(Role)){TArray<TSharedPtr<FJsonValue>> One;
  if(Hired(this,Role))One.Add(MakeShared<FJsonValueObject>(NewWorker(TEXT("integral"))));Team->SetArrayField(Role,One);}
 return const_cast<TArray<TSharedPtr<FJsonValue>>&>(Team->GetArrayField(Role));
}

TArray<TSharedPtr<FJsonObject>> UMareSimulation::StaffTeam(const FString& Role) const
{
 TArray<TSharedPtr<FJsonObject>> Out;if(!Hired(this,Role))return Out;
 const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Object(State,TEXT("staff_team"))->TryGetArrayField(Role,List))for(const auto& V:*List)if(V->AsObject().IsValid())Out.Add(V->AsObject());
 if(Out.IsEmpty())Out.Add(NewWorker(TEXT("integral")));
 return Out;
}

TArray<FString> UMareSimulation::StaffShifts() const
{
 TArray<FString> Out;for(const auto& Pair:Object(Rules(this),TEXT("shifts"))->Values)Out.Add(FString(Pair.Key.ToView()));
 if(Out.IsEmpty())Out.Add(TEXT("integral"));return Out;
}
FString UMareSimulation::ShiftName(const FString& Shift) const{const FString N=String(Object(Object(Rules(this),TEXT("shifts")),Shift),TEXT("name"));return N.IsEmpty()?Shift:N;}
FString UMareSimulation::WeekdayName(int32 Weekday)
{
 static const TCHAR* Names[]={TEXT("segunda"),TEXT("terça"),TEXT("quarta"),TEXT("quinta"),TEXT("sexta"),TEXT("sábado"),TEXT("domingo")};
 return Weekday>=0 && Weekday<7?Names[Weekday]:TEXT("sem folga");
}

static bool WorkerOnDuty(const UMareSimulation* S,const TSharedPtr<FJsonObject>& W,int32 Day,double Hour)
{
 if(int32(UMareSimulation::Number(W,TEXT("off"),-1))==UMareSimulation::Weekday(Day))return false;
 if(int32(UMareSimulation::Number(W,TEXT("absent_day"),-1))==Day)return false;
 const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;
 if(!UMareSimulation::Object(UMareSimulation::Object(Rules(S),TEXT("shifts")),UMareSimulation::String(W,TEXT("shift")))->TryGetArrayField(TEXT("hours"),Hours) || Hours->Num()!=2)return true;
 return Hour>=(*Hours)[0]->AsNumber() && Hour<(*Hours)[1]->AsNumber();
}

bool UMareSimulation::StaffOnDuty(const FString& Role) const
{
 if(!Hired(this,Role))return false;if(Exempt(this,Role))return true;
 const int32 Day=Number(State,TEXT("day"),1);const double Hour=DutyHour>=0?DutyHour+.5:Number(State,TEXT("minutes"))/60;
 for(const auto& W:StaffTeam(Role))if(WorkerOnDuty(this,W,Day,Hour))return true;
 return false;
}

double UMareSimulation::StaffSkill(const FString& Role) const
{
 if(!Hired(this,Role))return 0;const auto R=Rules(this);
 const int32 Day=Number(State,TEXT("day"),1);const double Hour=DutyHour>=0?DutyHour+.5:Number(State,TEXT("minutes"))/60;double Best=0;
 for(const auto& W:StaffTeam(Role)){if(!Exempt(this,Role) && !WorkerOnDuty(this,W,Day,Hour))continue;
  double Skill=1+Number(R,TEXT("level_bonus"),.06)*(Number(W,TEXT("level"),1)-1);
  if(Number(W,TEXT("fatigue"))>=Number(R,TEXT("tired"),60))Skill*=1-Number(R,TEXT("tired_penalty"),.35);
  Best=FMath::Max(Best,Skill);}
 return Best;
}

double UMareSimulation::StaffWage(const FString& Role) const
{
 const auto R=Rules(this);const double Base=Number(Object(Object(Definitions,TEXT("staff")),Role),TEXT("wage"));double Total=0;
 for(const auto& W:StaffTeam(Role)){const double Share=Number(Object(Object(R,TEXT("shifts")),String(W,TEXT("shift"))),TEXT("wage"),1);
  Total+=FMath::RoundToDouble(Base*Share*(1+Number(R,TEXT("raise"),.08)*(Number(W,TEXT("level"),1)-1)));}
 return Total;
}

bool UMareSimulation::CycleStaffShift(const FString& Role,int32 Index)
{
 if(!Hired(this,Role) || Exempt(this,Role))return Fail(TEXT("Este cargo não tem turnos."));
 auto& Team=TeamList(Role);if(!Team.IsValidIndex(Index))return false;
 const TArray<FString> Shifts=StaffShifts();auto W=Team[Index]->AsObject();
 FString Next=Shifts[(Shifts.IndexOfByKey(String(W,TEXT("shift")))+1)%Shifts.Num()];
 if(Team.Num()>1){
  // Two people always split the day: swapping one half swaps the other.
  if(Next==TEXT("integral"))Next=Shifts[(Shifts.IndexOfByKey(Next)+1)%Shifts.Num()];
  auto Other=Team[1-Index]->AsObject();Other->SetStringField(TEXT("shift"),Next==TEXT("manha")?TEXT("tarde"):TEXT("manha"));}
 W->SetStringField(TEXT("shift"),Next);
 LastMessage=FString::Printf(TEXT("%s: turno %s."),*String(Object(Object(Definitions,TEXT("staff")),Role),TEXT("name")),*ShiftName(Next).ToLower());
 return Save();
}

bool UMareSimulation::CycleStaffDayOff(const FString& Role,int32 Index)
{
 if(!Hired(this,Role) || Exempt(this,Role))return Fail(TEXT("Este cargo não tem folgas."));
 auto& Team=TeamList(Role);if(!Team.IsValidIndex(Index))return false;
 auto W=Team[Index]->AsObject();const int32 Off=int32(Number(W,TEXT("off"),-1))+1;W->SetNumberField(TEXT("off"),Off>6?-1:Off);
 LastMessage=Off>6?TEXT("Sem dia de folga: o cansaço vai acumular."):TEXT("Folga às ")+WeekdayName(Off)+TEXT("s.");
 return Save();
}

bool UMareSimulation::HireSecondStaff(const FString& Role)
{
 if(!Hired(this,Role) || Exempt(this,Role))return Fail(TEXT("Contrate primeiro uma pessoa para o cargo."));
 auto& Team=TeamList(Role);if(Team.Num()>=Number(Rules(this),TEXT("max_team"),2))return Fail(TEXT("A equipe deste cargo já está completa."));
 auto Def=Object(Object(Definitions,TEXT("staff")),Role);const double Cost=Number(Def,TEXT("hire"));
 if(Money()<Cost)return Fail(FString::Printf(TEXT("Saldo insuficiente: a contratação custa R$ %.0f."),Cost));
 // The first person moves to the morning (unless already on a half shift) and the new one covers the other half.
 auto First=Team[0]->AsObject();if(String(First,TEXT("shift"))==TEXT("integral"))First->SetStringField(TEXT("shift"),TEXT("manha"));
 Team.Add(MakeShared<FJsonValueObject>(NewWorker(String(First,TEXT("shift"))==TEXT("manha")?TEXT("tarde"):TEXT("manha"))));
 Book(-Cost,TEXT("Contratação: ")+String(Def,TEXT("name"))+TEXT(" (2º turno)"));
 LastMessage=String(Def,TEXT("name"))+TEXT(": segunda pessoa contratada, cada uma num turno.");return Save();
}

bool UMareSimulation::DismissSecondStaff(const FString& Role)
{
 auto& Team=TeamList(Role);if(Team.Num()<2)return Fail(TEXT("Só há uma pessoa neste cargo."));
 Team.RemoveAt(1);Team[0]->AsObject()->SetStringField(TEXT("shift"),TEXT("integral"));
 LastMessage=String(Object(Object(Definitions,TEXT("staff")),Role),TEXT("name"))+TEXT(": volta a uma pessoa em turno integral.");return Save();
}

void UMareSimulation::StaffHour(int32 Hour)
{
 const auto R=Rules(this);const int32 Day=Number(State,TEXT("day"),1);
 const TArray<TSharedPtr<FJsonValue>>* Levels=nullptr;R->TryGetArrayField(TEXT("xp_levels"),Levels);
 for(const auto& Pair:Object(State,TEXT("staff"))->Values){const FString Role(Pair.Key.ToView());bool bHired=false;
  if(!Pair.Value->TryGetBool(bHired) || !bHired || !Object(Definitions,TEXT("staff"))->HasField(Role))continue;
  bool bLegacy=false;Object(Object(Definitions,TEXT("staff")),Role)->TryGetBoolField(TEXT("company"),bLegacy);if(bLegacy)continue;
  for(const auto& V:TeamList(Role)){auto W=V->AsObject();if(!Exempt(this,Role) && !WorkerOnDuty(this,W,Day,Hour-.5))continue;
   W->SetNumberField(TEXT("hours_today"),Number(W,TEXT("hours_today"))+1);
   const double Xp=Number(W,TEXT("xp"))+Number(R,TEXT("xp_per_hour"),1);W->SetNumberField(TEXT("xp"),Xp);
   int32 Level=1;if(Levels)for(int32 I=1;I<Levels->Num();++I)if(Xp>=(*Levels)[I]->AsNumber())Level=I+1;
   if(Level>Number(W,TEXT("level"),1)){W->SetNumberField(TEXT("level"),Level);
    LastMessage=FString::Printf(TEXT("%s subiu para o nível %d: trabalha melhor e o salário sobe %.0f%%."),
     *String(Object(Object(Definitions,TEXT("staff")),Role),TEXT("name")),Level,Number(R,TEXT("raise"),.08)*100);}}}
}

void UMareSimulation::StaffNight()
{
 const auto R=Rules(this);const int32 Day=Number(State,TEXT("day"),1);TArray<FString> Notes;
 for(const auto& Pair:Object(State,TEXT("staff"))->Values){const FString Role(Pair.Key.ToView());bool bHired=false;
  if(!Pair.Value->TryGetBool(bHired) || !bHired || Exempt(this,Role) || !Object(Definitions,TEXT("staff"))->HasField(Role))continue;
  bool bLegacy=false;Object(Object(Definitions,TEXT("staff")),Role)->TryGetBoolField(TEXT("company"),bLegacy);if(bLegacy)continue;
  const FString Name=String(Object(Object(Definitions,TEXT("staff")),Role),TEXT("name"));
  for(const auto& V:TeamList(Role)){auto W=V->AsObject();
   const bool bOff=int32(Number(W,TEXT("off"),-1))==Weekday(Day) || int32(Number(W,TEXT("absent_day"),-1))==Day;
   double Fatigue=Number(W,TEXT("fatigue"))-Number(R,TEXT("recover"),4);
   Fatigue+=bOff?-Number(R,TEXT("rest"),35):Number(Object(Object(R,TEXT("shifts")),String(W,TEXT("shift"))),TEXT("fatigue"),9);
   Fatigue=FMath::Clamp(Fatigue,0.,100.);
   if(Fatigue>=Number(R,TEXT("absent"),90)){W->SetNumberField(TEXT("absent_day"),Day+1);Notes.Add(Name+TEXT(" está exausto(a) e falta amanhã"));}
   else if(Fatigue>=Number(R,TEXT("tired"),60) && Number(W,TEXT("fatigue"))<Number(R,TEXT("tired"),60))Notes.Add(Name+TEXT(" está cansado(a): dê um dia de folga"));
   W->SetNumberField(TEXT("fatigue"),Fatigue);W->SetNumberField(TEXT("hours_today"),0);}}
 if(Notes.Num())Child(State,TEXT("ue_last_day"))->SetStringField(TEXT("staff_note"),FString::Join(Notes,TEXT("; "))+TEXT("."));
 else Child(State,TEXT("ue_last_day"))->RemoveField(TEXT("staff_note"));
}

void UMareSimulation::StaffDid(const FString& Role,int32 Tasks,double Money)
{
 if(Role.IsEmpty() || (Tasks<=0 && Money<=0))return;
 auto Done=Child(State,TEXT("staff_done"));const int32 Day=Number(State,TEXT("day"),1);
 if(Number(Done,TEXT("day"),-1)!=Day){Done->SetNumberField(TEXT("day"),Day);Done->SetObjectField(TEXT("roles"),MakeShared<FJsonObject>());}
 auto R=Child(Child(Done,TEXT("roles")),Role);
 R->SetNumberField(TEXT("tasks"),Number(R,TEXT("tasks"))+Tasks);R->SetNumberField(TEXT("money"),Number(R,TEXT("money"))+Money);
}

TPair<int32,double> UMareSimulation::StaffDoneToday(const FString& Role) const
{
 const auto Done=Object(State,TEXT("staff_done"));if(Number(Done,TEXT("day"),-1)!=Number(State,TEXT("day"),1))return {0,0.};
 const auto R=Object(Object(Done,TEXT("roles")),Role);return {int32(Number(R,TEXT("tasks"))),Number(R,TEXT("money"))};
}
