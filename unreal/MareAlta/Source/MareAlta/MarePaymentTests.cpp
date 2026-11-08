// Kiosk payment rules (MarePayment.cpp): what the customer hands over, and exact / short / extra change and the card.
#include "MareSimulation.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMarePaymentTest,"MareAlta.Gameplay.KioskPayment",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMarePaymentTest::RunTest(const FString& Parameters)
{
 auto Instance=NewObject<UGameInstance>();Instance->AddToRoot();
 auto Sim=NewObject<UMareSimulation>(Instance);Sim->AddToRoot();
 Sim->SaveDirectory=FPaths::ProjectSavedDir()/TEXT("Automation/Payment")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto Load=[&](const FString& Name,TSharedPtr<FJsonObject>& Out){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data")/Name));return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Out);};
 if(!TestTrue(TEXT("Definitions"),Load(TEXT("definitions.json"),Sim->Definitions)) || !TestTrue(TEXT("Save"),Load(TEXT("default_save.json"),Sim->State))){Sim->RemoveFromRoot();Instance->RemoveFromRoot();return false;}
 Sim->State->SetNumberField(TEXT("money"),1000);
 // Customers hand over a note that covers the total; cards carry no cash.
 FRandomStream Rng(7);int32 Cards=0;
 for(int32 I=0;I<200;++I){const FMarePay P=Sim->MakePayment(TEXT("A"),18.5,Rng);if(P.bCard){++Cards;TestEqual(TEXT("Card has no cash"),P.Given,int64(0));}
  else{TestTrue(TEXT("Note covers the total"),P.Given>=P.Total);TestTrue(TEXT("A real note"),P.Given==2000 || P.Given==5000);}}
 TestTrue(TEXT("Both ways happen"),Cards>30 && Cards<170);
 FMarePay Cash;Cash.Customer=TEXT("Ana");Cash.Total=1850;Cash.Given=2000;
 TestEqual(TEXT("Change due"),Cash.ChangeDue(),int64(150));
 const double M0=Sim->Money();
 TestEqual(TEXT("Exact change: five stars"),Sim->SettlePayment(Cash,150,false),5.0);
 TestEqual(TEXT("Exact change tips 10 %"),Sim->Money(),M0+1.85,.001);
 const double M1=Sim->Money();
 TestEqual(TEXT("Short change: two stars"),Sim->SettlePayment(Cash,100,false),2.0);
 TestEqual(TEXT("Short change costs no money"),Sim->Money(),M1,.001);
 TestEqual(TEXT("Too much change: four stars"),Sim->SettlePayment(Cash,250,false),4.0);
 TestEqual(TEXT("The extra change leaves the cash"),Sim->Money(),M1-1.0,.001);
 FMarePay Card;Card.Customer=TEXT("Bia");Card.Total=1850;Card.bCard=true;
 const double M2=Sim->Money();
 TestEqual(TEXT("Card typed right: five stars"),Sim->SettlePayment(Card,1850,false),5.0);
 TestTrue(TEXT("Card tip"),Sim->Money()>M2);
 const double M3=Sim->Money();
 TestEqual(TEXT("Skipped: no tip"),Sim->SettlePayment(Cash,0,true),3.5);
 TestEqual(TEXT("Skipped: money unchanged"),Sim->Money(),M3,.001);
 Sim->RemoveFromRoot();Instance->RemoveFromRoot();
 return true;
}
#endif
