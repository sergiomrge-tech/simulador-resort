// Item 10: grandma's debt against the fixed contract vectors (tools/ue58/balance/debt_vectors.json, cents).
#include "MareSimulation.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareDebtVectorsTest,"MareAlta.Gameplay.DebtVectors",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareDebtVectorsTest::RunTest(const FString& Parameters)
{
 auto LoadJson=[](const FString& Path,TSharedPtr<FJsonObject>& Out){FString Text;return FFileHelper::LoadFileToString(Text,*Path) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Out) && Out.IsValid();};
 TSharedPtr<FJsonObject> Vectors;
 if(!TestTrue(TEXT("Contract vectors"),LoadJson(FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../../tools/ue58/balance/debt_vectors.json")),Vectors)))return false;
 const TArray<TSharedPtr<FJsonValue>>* Cases=nullptr;if(!TestTrue(TEXT("Cases"),Vectors->TryGetArrayField(TEXT("cases"),Cases)))return false;
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 int32 Actions=0;
 for(const auto& CaseValue:*Cases){
  const auto Case=CaseValue->AsObject();const FString Id=Case->GetStringField(TEXT("id"));
  auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
  Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Debt")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
  if(!LoadJson(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"),Sim->Definitions) || !LoadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),Sim->State)){
   AddError(TEXT("definitions/default_save"));Sim->RemoveFromRoot();break;}
  bool bDemo=false;Case->TryGetBoolField(TEXT("demo"),bDemo);Sim->Definitions->SetBoolField(TEXT("demo"),bDemo);
  const auto Initial=Case->GetObjectField(TEXT("initial"));
  for(const auto& Pair:Initial->Values){const FString Key(Pair.Key.ToView());
   if(Key==TEXT("money_cents"))Sim->State->SetNumberField(TEXT("money"),Pair.Value->AsNumber()/100.0);
   else if(Key==TEXT("prog")){auto Prog=UMareSimulation::Object(Sim->State,TEXT("prog"));for(const auto& P:Pair.Value->AsObject()->Values)Prog->SetField(FString(P.Key.ToView()),P.Value);}
   else Sim->State->SetField(Key,Pair.Value);}
  Sim->State->SetNumberField(TEXT("day"),Case->GetNumberField(TEXT("created_day")));
  TestTrue(Id+TEXT(": debt created/kept"),Sim->EnsureDebt());
  auto Check=[&](const FString& Where,const TSharedPtr<FJsonObject>& E){
   const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
   if(E->HasField(TEXT("paid_cents")))TestEqual(Where+TEXT(" paid"),Sim->DebtPaidCents(),int64(E->GetNumberField(TEXT("paid_cents"))));
   if(E->HasField(TEXT("balance_cents")))TestEqual(Where+TEXT(" balance"),Sim->DebtBalanceCents(),int64(E->GetNumberField(TEXT("balance_cents"))));
   if(E->HasField(TEXT("money_cents")))TestEqual(Where+TEXT(" money"),int64(FMath::RoundToDouble(Sim->Money()*100)),int64(E->GetNumberField(TEXT("money_cents"))));
   if(E->TryGetArrayField(TEXT("pending"),List)){TArray<FString> Want;for(const auto& V:*List)Want.Add(V->AsString());
    TestEqual(Where+TEXT(" pending"),FString::Join(Sim->DebtPendingMilestones(),TEXT(",")),FString::Join(Want,TEXT(",")));}
   bool bFinale=false;if(E->TryGetBoolField(TEXT("finale"),bFinale))TestEqual(Where+TEXT(" finale"),Sim->IsDebtFinalePending(),bFinale);};
  const TArray<TSharedPtr<FJsonValue>>* List=nullptr;Case->TryGetArrayField(TEXT("actions"),List);
  for(int32 I=0;List && I<List->Num();++I){const auto A=(*List)[I]->AsObject();const FString Where=FString::Printf(TEXT("%s #%d"),*Id,I);++Actions;
   if(A->HasField(TEXT("migrate")))TestTrue(Where+TEXT(" migrate"),Sim->EnsureDebt());
   else if(A->HasField(TEXT("pay"))){
    Sim->State->SetNumberField(TEXT("day"),A->GetNumberField(TEXT("day")));
    bool bSaveOk=true;A->TryGetBoolField(TEXT("save_ok"),bSaveOk);Sim->bFailNextSaveForTest=!bSaveOk;
    int64 Cents=0;const bool bValid=UMareSimulation::DebtCentsFromJson(A->TryGetField(TEXT("pay")),Cents);
    const bool bOk=bValid && Sim->PayDebt(Cents);Sim->bFailNextSaveForTest=false;
    const auto E=A->GetObjectField(TEXT("expect"));TestEqual(Where+TEXT(" ok"),bOk,E->GetBoolField(TEXT("ok")));Check(Where,E);}
   else if(A->HasField(TEXT("remind"))){bool bWant=false;A->TryGetBoolField(TEXT("expect_reminder"),bWant);
    TestEqual(Where+TEXT(" reminder"),Sim->DebtReminder(int32(A->GetNumberField(TEXT("remind")))),bWant);}
   else if(A->HasField(TEXT("ack")))TestTrue(Where+TEXT(" ack"),Sim->AckDebt());
   else Check(Where,A);}
  if(Id==TEXT("save_antigo_preserva_desconhecidos")){
   TestEqual(TEXT("Unknown prog field kept"),UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("custom_future")),TEXT("keep")),42.0);
   TestEqual(TEXT("Unknown root field kept"),UMareSimulation::String(Sim->State,TEXT("future")),FString(TEXT("preservar")));
   TestEqual(TEXT("Created on the migration day"),UMareSimulation::Number(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("debt")),TEXT("created_day")),20.0);}
  Sim->RemoveFromRoot();}
 TestTrue(TEXT("Every vector action ran"),Actions>=45);
 // The letter shows once after the company exists; the phone card needs nothing else.
 {auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
  Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Debt")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
  LoadJson(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"),Sim->Definitions);LoadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),Sim->State);
  TestFalse(TEXT("No letter before the company"),Sim->ShowDebtIntro());
  TestTrue(TEXT("Company"),Sim->CreateCompany(TEXT("Teste")));TestTrue(TEXT("Debt comes with the company"),Sim->HasDebt());
  TestEqual(TEXT("Principal R$ 1.000.000"),Sim->DebtPrincipalCents(),int64(100000000));
  TestTrue(TEXT("Letter once"),Sim->ShowDebtIntro());TestFalse(TEXT("Letter title"),Sim->PendingTipTitle.IsEmpty());TestFalse(TEXT("Not twice"),Sim->ShowDebtIntro());
  Sim->RemoveFromRoot();}
 Instance->RemoveFromRoot();
 return true;
}

// 11/11: the whole debt paid in one go (a milestone crossed and the balance cleared by the same payment).
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareDebtOnePaymentTest,"MareAlta.Gameplay.DebtOnePayment",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareDebtOnePaymentTest::RunTest(const FString& Parameters)
{
 auto LoadJson=[](const FString& Path,TSharedPtr<FJsonObject>& Out){FString Text;return FFileHelper::LoadFileToString(Text,*Path) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Out) && Out.IsValid();};
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/DebtOnePayment")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 if(!LoadJson(FPaths::ProjectContentDir()/TEXT("Data/definitions.json"),Sim->Definitions) || !LoadJson(FPaths::ProjectContentDir()/TEXT("Data/default_save.json"),Sim->State)){
  AddError(TEXT("definitions/default_save"));Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->Definitions->SetBoolField(TEXT("demo"),false);   // the finale only exists in the full game
 TestTrue(TEXT("Company"),Sim->CreateCompany(TEXT("Teste")));
 const int64 Balance=Sim->DebtBalanceCents();TestTrue(TEXT("There is a debt"),Balance>0);
 Sim->State->SetNumberField(TEXT("money"),Balance/100.0+10);
 TestTrue(TEXT("Paid in one go"),Sim->PayDebt(Balance));TestEqual(TEXT("Nothing left"),Sim->DebtBalanceCents(),int64(0));
 TestTrue(TEXT("Milestones were crossed"),Sim->DebtPendingMilestones().Num()>0);
 TestTrue(TEXT("The finale is pending"),Sim->IsDebtFinalePending());
 TestFalse(TEXT("No milestone tip in front of the finale"),Sim->DebtMilestoneTipDue());
 TestTrue(TEXT("The end screen acknowledges"),Sim->AckDebt());
 TestFalse(TEXT("Finale seen"),Sim->IsDebtFinalePending());TestEqual(TEXT("No milestone left"),Sim->DebtPendingMilestones().Num(),0);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();
 return true;
}
#endif
