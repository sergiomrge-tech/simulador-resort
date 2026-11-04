#include "MareSummitWorld.h"
#include "MareGame.h"
#include "MareGamepad.h"
#include "MareLoc.h"
#include "MareNotebookStyle.h"
#include "MarePerson.h"
#include "MareServiceTarget.h"
#include "MareSimulation.h"
#include "MareVillageWorld.h"
#include "MareAudioWorld.h"
#include "Components/AudioComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Serialization/JsonSerializer.h"
#include "Sound/SoundWave.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"

#define LOCTEXT_NAMESPACE "MareSummit"

static TAutoConsoleVariable<int32> CVarMareTsunami(TEXT("mare.Tsunami"),1,TEXT("Daily offering / tsunami rule: 1 on, 0 off."));
static TAutoConsoleVariable<int32> CVarMareTsunamiNow(TEXT("mare.TsunamiNow"),0,TEXT("QA: 1 starts the omen now, 2 starts the wave now (resets to 0)."));
static TAutoConsoleVariable<int32> CVarMareElderMet(TEXT("mare.ElderMet"),0,TEXT("QA: 1 marks Seu Tibúrcio as met (the rule becomes active)."));

static const TCHAR* ElderName=TEXT("Seu Tibúrcio");

TStatId UMareSummitWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareSummitWorld,STATGROUP_Tickables);}

static TSharedPtr<FJsonObject> ChildOf(const TSharedPtr<FJsonObject>& Parent,const FString& Key)
{
 const TSharedPtr<FJsonObject>* Found=nullptr;if(Parent->TryGetObjectField(Key,Found) && Found && Found->IsValid())return *Found;
 auto Made=MakeShared<FJsonObject>();Parent->SetObjectField(Key,Made);return Made;
}
static TSharedPtr<FJsonObject> SummitState(UMareSimulation* Sim){return ChildOf(Sim->State,TEXT("summit"));}

void UMareSummitWorld::Setup()
{
 // The bench is a level actor tagged MareSummit (mare_tsunami.summit_props); the old man sits on it facing the sea.
 AActor* Bench=nullptr;
 for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("MareSummit"))){auto Mesh=It->GetStaticMeshComponent()->GetStaticMesh();
  if(Mesh && Mesh->GetName().Contains(TEXT("bench")))Bench=*It;}
 if(!Bench)return;
 const float Yaw=Bench->GetActorRotation().Yaw+90.f;   // painted_wooden_bench: the seat faces local +Y (bench at yaw 180 -> the sea)
 const FVector Forward=FRotator(0,Yaw,0).Vector();
 FVector SeatTop=Bench->GetActorLocation()+FVector(0,0,45);
 {FHitResult Hit;FCollisionQueryParams Q(TEXT("MareElderSeat"),true);const FVector At=Bench->GetActorLocation()+Forward*8;
  if(Bench->ActorLineTraceSingle(Hit,At+FVector(0,0,70),At-FVector(0,0,5),ECC_Visibility,Q))SeatTop=Hit.ImpactPoint;
  UE_LOG(LogTemp,Display,TEXT("MARE_SUMMIT_SEAT hit=%d top=%s bench=%s yaw=%.0f"),Hit.bBlockingHit?1:0,*SeatTop.ToString(),*Bench->GetActorLocation().ToString(),Yaw);}
 // Seated like the bar patrons (MareBarWorld): no movement, no capsule collision, the pelvis aligned on the seat.
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 Elder=GetWorld()->SpawnActor<AMarePerson>(SeatTop+Forward*30+FVector(0,0,42),FRotator(0,Yaw,0),Params);
 if(!Elder)return;
 Elder->Tags.Add(TEXT("MareElder"));Elder->PersonName=ElderName;Elder->bAmbient=true;Elder->SaveId=TEXT("summit_elder");
 if(!Elder->SetAppearance(1)){Elder->Destroy();Elder=nullptr;return;}
 Elder->bSeated=true;Elder->GetCharacterMovement()->DisableMovement();Elder->SetActorEnableCollision(false);
 Elder->SitOn(SeatTop,Yaw);
 auto Target=GetWorld()->SpawnActor<AMareServiceTarget>();Target->Action=TEXT("Elder");Target->Label=FString(ElderName)+TEXT(" · conversar");
 Target->Reach=280;Target->OcclusionTolerance=60;Target->SetOwner(Elder);
 Target->AttachToActor(Elder,FAttachmentTransformRules::SnapToTargetNotIncludingScale);Target->SetActorRelativeLocation(FVector(0,0,20));Elder->Interaction=Target;
 bReady=true;
}

void UMareSummitWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()))return;
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim || !Sim->bMainMenuDone)return;
 if(!bReady){Setup();if(!bReady)return;}
 if(bOver){OverTime+=DeltaSeconds;return;}
 auto Summit=SummitState(Sim);
 if(CVarMareElderMet.GetValueOnGameThread()){Summit->SetBoolField(TEXT("met"),true);CVarMareElderMet->Set(0,ECVF_SetByCode);}
 const int32 Day=int32(UMareSimulation::Number(Sim->State,TEXT("day"),1));
 const double Minutes=UMareSimulation::Number(Sim->State,TEXT("minutes"));
 bool bMet=false;Summit->TryGetBoolField(TEXT("met"),bMet);
 const int32 Last=int32(UMareSimulation::Number(Summit,TEXT("last_day"),0));
 // Morning snapshot: "restart the day" after a game over goes back to the state of this morning.
 if(Day!=SeenDay && !bWave){SeenDay=Day;FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(Sim->State.ToSharedRef(),Writer);MorningState=Text;}
 if(bWave){UpdateWave(DeltaSeconds);return;}
 UpdateFinale(DeltaSeconds,Sim,Minutes);
 if(bFinale){Summit->SetNumberField(TEXT("last_day"),Day);return;}   // the whole village brings tonight's offering
 const int32 Forced=CVarMareTsunamiNow.GetValueOnGameThread();
 if(Forced){CVarMareTsunamiNow->Set(0,ECVF_SetByCode);if(Forced==1)StartOmen();else{StartOmen();StartWave();}return;}
 // Before the first meeting the residents point the way (from day 2, once a day in the morning).
 if(!bMet && Day>=2 && Hinted!=Day && Minutes>=9*60 && Minutes<18*60){Hinted=Day;
  Sim->LastMessage=TEXT("Dizem que um velho lá no alto do morro, atrás da vila, quer muito falar com você. Tem uma trilha.");}
 const bool bActive=bMet && CVarMareTsunami.GetValueOnGameThread()!=0;
 const bool bDone=OfferingDone(bMet,Last,Day);
 const int32 Phase=bActive && !bDone?PhaseAt(Minutes):0;
 if(Phase==1 && Reminded!=Day*10+1 && Minutes<18*60){Reminded=Day*10+1;Sim->LastMessage=TEXT("Hoje ainda falta a oferenda do Seu Tibúrcio. O vulcão anda resmungando.");}
 if(Phase==1 && Minutes>=18*60 && Reminded!=Day*10+2){Reminded=Day*10+2;Sim->LastMessage=TEXT("O céu está ficando esquisito... a oferenda do Seu Tibúrcio!");}
 if(Phase>=2 && !bOmenOn)StartOmen();
 if(Phase<2 && bOmenOn)EndOmen();
 Omen=FMath::FInterpTo(Omen,bOmenOn?1.f:0.f,DeltaSeconds,.35f);
 if(bOmenOn){ThunderClock-=DeltaSeconds;if(ThunderClock<=0){ThunderClock=FMath::FRandRange(6.f,14.f);Thunder(.35f);}}
 UpdateLightning(DeltaSeconds);
 if(Phase==3)StartWave();
}

void UMareSummitWorld::StartOmen()
{
 if(bOmenOn)return;auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 bOmenOn=true;PrevWeather=UMareSimulation::String(Sim->State,TEXT("weather"));Sim->State->SetStringField(TEXT("weather"),TEXT("rain"));
 Sim->LastMessage=TEXT("O mar ficou bravo de repente. Seu Tibúrcio avisou: sem oferenda, a Onda vem!");
}

void UMareSummitWorld::EndOmen()
{
 if(!bOmenOn)return;auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 bOmenOn=false;Sim->State->SetStringField(TEXT("weather"),PrevWeather.IsEmpty()?TEXT("sun"):PrevWeather);
}

void UMareSummitWorld::Offer(const FString& Gift,bool bCount)
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 auto Summit=SummitState(Sim);Summit->SetBoolField(TEXT("met"),true);
 Summit->SetNumberField(TEXT("last_day"),UMareSimulation::Number(Sim->State,TEXT("day"),1));
 if(bCount)Summit->SetNumberField(TEXT("count"),UMareSimulation::Number(Summit,TEXT("count"))+1);
 if(!Gift.IsEmpty())ChildOf(Sim->State,TEXT("company"))->SetStringField(TEXT("carry"),FString());   // the product stays in the basket
 if(bOmenOn){EndOmen();Sim->LastMessage=TEXT("O mar foi se acalmando. Ufa! Seu Tibúrcio sorriu (acho).");}
 if(Elder)Elder->Express(TEXT("smile"),5.f);
 Sim->Save();
}

void UMareSummitWorld::Talk(APlayerController* Controller)
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>();
 UE_LOG(LogTemp,Display,TEXT("MARE_SUMMIT_TALK sim=%d village=%d elder=%d wave=%d dialog=%d"),Sim?1:0,Village?1:0,Elder?1:0,bWave?1:0,Village&&Village->IsDialogueOpen()?1:0);
 if(!Sim || !Village || !Elder || bWave)return;
 auto Summit=SummitState(Sim);bool bMet=false;Summit->TryGetBoolField(TEXT("met"),bMet);
 const int32 Day=int32(UMareSimulation::Number(Sim->State,TEXT("day"),1));
 const bool bDone=OfferingDone(bMet,int32(UMareSimulation::Number(Summit,TEXT("last_day"),0)),Day);
 const FString Gift=Sim->Carry();
 const bool bKiosk=Sim->State->HasField(TEXT("company")) && !UMareSimulation::String(UMareSimulation::Object(Sim->State,TEXT("company")),TEXT("name")).IsEmpty();
 const TWeakObjectPtr<UMareSummitWorld> Weak(this);
 if(!bMet){
  Village->Quip(Elder,Controller,ElderName,
   TEXT("Finalmente alguém subiu! Faz três semanas que eu grito daqui de cima e só o eco responde. Escuta: aquele vulcão lá no mar é temperamental. Todo santo dia alguém precisa deixar uma oferenda neste cesto, senão ele se zanga e manda a Onda. A grande. A de cem metros."),
   {TEXT("Cem metros?!"),TEXT("Que tipo de oferenda?"),TEXT("Isso é sério?")},
   [](int32 I)->FString{
    if(I==0)return TEXT("Cem. Contei com a régua do meu avô, que media tudo em palmos. Deu muitos palmos.");
    if(I==1)return TEXT("Qualquer coisa gostosa do seu quiosque: uma água de coco, um petisco... O vulcão é guloso, igual a mim. Traz aqui em cima, nas mãos, e deixa no cesto. Todo dia, antes das dez da noite.");
    return TEXT("Seríssimo. Em 1987 esqueceram uma vez e a Onda levou a praia, o bar e o meu bigode. O bigode nunca mais cresceu igual.");},
   [Weak](){if(Weak.IsValid()){Weak->Offer(FString(),false);
    if(auto S=Weak->GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>())S->LastMessage=TEXT("Hoje Seu Tibúrcio já deu um coco dele, por conta da casa. A partir de amanhã, a oferenda é com você: todo dia, antes das 22h.");}});
  return;
 }
 if(bDone){
  static const TCHAR* Lines[]={TEXT("O vulcão está de barriga cheia hoje. Pode descer tranquilo. Devagar, que a trilha é traiçoeira."),
   TEXT("Volta amanhã. E traz coco gelado, que o de ontem chegou morno. O vulcão reclamou. Eu também."),
   TEXT("Sabia que eu já fui surfista? Peguei a Onda uma vez. Ela que me pegou, na verdade."),
   TEXT("Daqui de cima dá pra ver tudo: o mar, o vulcão, e você esquecendo a oferenda amanhã. Brincadeira. Ou não.")};
  Village->Quip(Elder,Controller,ElderName,Lines[(Day+int32(FPlatformTime::Seconds()))%4],{},nullptr,nullptr);return;
 }
 if(!Gift.IsEmpty() || !bKiosk){
  const FString Line=!Gift.IsEmpty()?FString::Printf(TEXT("Opa! Trouxe %s? O vulcão vai adorar. Pode deixar no cesto, com carinho."),*UMareSimulation::String(UMareSimulation::Object(UMareSimulation::Object(Sim->Definitions,TEXT("dishes")),Gift),TEXT("name")).ToLower())
   :FString(TEXT("Sem quiosque ainda, né? Tá bom, hoje vale um abraço. No vulcão não dá, então vai em mim mesmo."));
  Village->Quip(Elder,Controller,ElderName,Line,{!Gift.IsEmpty()?TEXT("Deixar no cesto"):TEXT("Dar um abraço")},
   [Weak,Gift](int32)->FString{if(Weak.IsValid())Weak->Offer(Gift);
    return TEXT("Pronto! O vulcão agradece. Ouviu esse arroto lá longe? Foi ele. Até amanhã!");},nullptr);
  return;
 }
 Village->Quip(Elder,Controller,ElderName,
  bOmenOn?TEXT("Tá vendo esse mar?! CORRE no quiosque, pega qualquer coisa e traz aqui! A Onda está acordando!")
   :TEXT("Veio de mão abanando? O vulcão não aceita visita, aceita petisco! Pega qualquer coisa no quiosque e traz aqui em cima."),
  {TEXT("Vou buscar"),TEXT("E se eu cantar pra ele?")},
  [](int32 I)->FString{return I==0?TEXT("Vai! E não demora, que hoje ele está com fome."):TEXT("Já tentei. Ele odeia pagode. Odeia mais ainda o meu pagode.");},nullptr);
}

void UMareSummitWorld::Thunder(float Gain)
{
 if(auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>())Audio->PlayCue(TEXT("thunder"),Gain,nullptr,true);
 FlashTime=0.f;
}

void UMareSummitWorld::UpdateLightning(float DeltaSeconds)
{
 FlashTime+=DeltaSeconds;
 if(!Lightning && (bOmenOn || bWave)){
  // From the sky over the sea towards the island: it lights the wave's face and the beach.
  Lightning=GetWorld()->SpawnActor<ADirectionalLight>(FVector::ZeroVector,FRotator(-42,90,0));
  if(Lightning){auto L=Cast<UDirectionalLightComponent>(Lightning->GetLightComponent());Lightning->SetMobility(EComponentMobility::Movable);
   L->SetLightColor(FLinearColor(.72f,.8f,1.f));L->SetCastShadows(false);L->SetIntensity(0);L->SetAtmosphereSunLight(false);}
 }
 if(!Lightning)return;
 // Two quick strokes: 0-0.12 s and 0.2-0.45 s, decaying.
 const float T=FlashTime;
 const float Flash=T<.12f?1.f-T/.12f*.5f:T<.2f?.15f:T<.45f?.9f*(1.f-(T-.2f)/.25f):0.f;
 Lightning->GetLightComponent()->SetIntensity(FMath::Max(Flash,0.f)*(bOmenOn||bWave?3.f:0.f));
}

void UMareSummitWorld::StartWave()
{
 if(bWave)return;auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 bWave=true;WaveTime=0;Sim->bHoldSaves=true;   // the doomed evening is never written to the slot
 // Sergio 04/11: "quando começa o tsunami as ondas param... silêncio antes do fim": the sea draws back flat, the rain,
 // thunder and lightning stop and the ambience falls silent (MareVisualWorld/MareAudioWorld read IsWaveRunning).
 EndOmen();
 if(auto Village=GetWorld()->GetSubsystem<UMareVillageWorld>())Village->CloseDialogue();
 Sim->LastMessage=TEXT("De repente, silêncio. O mar recuou... e lá longe, no horizonte, ele está subindo.");
 auto Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Summit/TsunamiWave/TsunamiWave.TsunamiWave"));
 auto Hero=UGameplayStatics::GetPlayerCharacter(this,0);const float X=Hero?Hero->GetActorLocation().X:4000.f;
 Wave=GetWorld()->SpawnActor<AStaticMeshActor>(FVector(X,-80000,-400),FRotator::ZeroRotator);
 if(Wave){Wave->SetMobility(EComponentMobility::Movable);Wave->GetStaticMeshComponent()->SetStaticMesh(Mesh);
  Wave->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Wave->GetStaticMeshComponent()->SetCastShadow(true);
  Wave->SetActorScale3D(FVector(1,.15f,.15f));}
 if(auto Sound=LoadObject<USoundWave>(nullptr,TEXT("/Game/Audio/ocean_loop.ocean_loop"))){auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();
  const float Gain=Audio?Audio->GetVolume(TEXT("Master"))*Audio->GetVolume(TEXT("Effects")):.6f;
  Roar=UGameplayStatics::SpawnSound2D(this,Sound,.001f*Gain,.42f,0,nullptr,false,false);}
}

void UMareSummitWorld::UpdateWave(float DeltaSeconds)
{
 WaveTime+=DeltaSeconds;auto Hero=UGameplayStatics::GetPlayerCharacter(this,0);
 // 0-35 s: grows from 15 m to 100 m far out while closing in at ~18 m/s; then runs in at 30 m/s over the beach and
 // up the hill. Its front reaching the hero ends the game (the island is never shown devastated).
 const float Grow=FMath::Clamp(WaveTime/35.f,0.f,1.f);const float Scale=FMath::Lerp(.15f,1.f,FMath::SmoothStep(0.f,1.f,Grow));
 const float Y=-80000.f+FMath::Min(WaveTime,35.f)*1800.f+FMath::Max(WaveTime-35.f,0.f)*3000.f;
 if(Wave){Wave->SetActorLocation(FVector(Wave->GetActorLocation().X,Y,-400));Wave->SetActorScale3D(FVector(1,Scale,Scale));}
 Omen=FMath::FInterpTo(Omen,0.f,DeltaSeconds,1.5f);
 // Silence; only in the last seconds the low roar of the wall arrives.
 if(Roar){auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>();const float Gain=Audio?Audio->GetVolume(TEXT("Master"))*Audio->GetVolume(TEXT("Effects")):.6f;
  Roar->SetVolumeMultiplier(FMath::Lerp(.001f,1.3f,FMath::Clamp((WaveTime-28.f)/10.f,0.f,1.f))*Gain);}
 FlashTime=10.f;UpdateLightning(DeltaSeconds);
 const float Front=Y+3000.f*Scale;   // the lip reaches ~30 m ahead of the actor origin at full size
 if(Hero && Front>=Hero->GetActorLocation().Y)ShowGameOver();
 if(WaveTime>140.f)ShowGameOver();
}

void UMareSummitWorld::ShowGameOver()
{
 if(bOver || !GEngine || !GEngine->GameViewport)return;
 bOver=true;OverTime=0;
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));
 const TWeakObjectPtr<UMareSummitWorld> Weak(this);
 auto Button=[Weak](const FText& Label,bool bRestart){return SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(18,6))
   .OnClicked_Lambda([Weak,bRestart](){if(Weak.IsValid())Weak->RestoreMorning(bRestart);return FReply::Handled();})
   [SNew(STextBlock).Text(Label).Font(MareNotebook::Hand(26)).ColorAndOpacity(FLinearColor(.95f,.93f,.88f))];};
 OverWidget=SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
  .BorderBackgroundColor_Lambda([Weak](){const float T=Weak.IsValid()?Weak->OverTime:2.f;return FLinearColor(0,0,0,FMath::Clamp(T/1.4f,0.f,1.f));})
  .HAlign(HAlign_Center).VAlign(VAlign_Center)
  [SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(STextBlock).Text(LOCTEXT("GameOver","GAME OVER")).Font(MareNotebook::Hand(150))
    .ColorAndOpacity_Lambda([Weak](){const float T=Weak.IsValid()?Weak->OverTime:3.f;return FSlateColor(FLinearColor(.92f,.12f,.08f,FMath::Clamp((T-1.2f)/1.f,0.f,1.f)));})]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,6,0,30)[SNew(STextBlock).Text(MareLoc::Text(TEXT("A Onda levou tudo. Seu Tibúrcio bem que avisou.")))
    .Font(MareNotebook::Body(22)).ColorAndOpacity_Lambda([Weak](){const float T=Weak.IsValid()?Weak->OverTime:3.f;return FSlateColor(FLinearColor(.9f,.88f,.84f,FMath::Clamp((T-1.8f)/1.f,0.f,1.f)));})]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(SHorizontalBox)
    +SHorizontalBox::Slot().AutoWidth().Padding(12,0)[Button(MareLoc::Text(TEXT("Recomeçar o dia")),true)]
    +SHorizontalBox::Slot().AutoWidth().Padding(12,0)[Button(MareLoc::Text(TEXT("Menu principal")),false)]]];
 GEngine->GameViewport->AddViewportWidgetContent(OverWidget.ToSharedRef(),80);
 if(PC){PC->bShowMouseCursor=true;PC->SetInputMode(FInputModeUIOnly().SetWidgetToFocus(OverWidget));PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);}
 if(auto Hero=UGameplayStatics::GetPlayerCharacter(this,0))Hero->GetCharacterMovement()->DisableMovement();
 if(Roar)Roar->FadeOut(3.f,0.f);
 UE_LOG(LogTemp,Display,TEXT("MARE_TSUNAMI_GAME_OVER t=%.1f"),WaveTime);
}

void UMareSummitWorld::RestoreMorning(bool bRestart)
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));
 if(!Sim || !PC)return;
 TSharedPtr<FJsonObject> Morning;
 if(!MorningState.IsEmpty() && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(MorningState),Morning) && Morning.IsValid())Sim->State=Morning;
 Sim->bHoldSaves=false;Sim->Save();
 if(GEngine && GEngine->GameViewport && OverWidget.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(OverWidget.ToSharedRef());OverWidget.Reset();
 if(bRestart)PC->ReloadActiveSlot();else PC->ReturnToMainMenu();
}

static TAutoConsoleVariable<int32> CVarMareFinaleNow(TEXT("mare.FinaleNow"),0,TEXT("QA: 1 starts the campaign finale party now."));

void UMareSummitWorld::UpdateFinale(float DeltaSeconds,UMareSimulation* Sim,double Minutes)
{
 auto Campaign=ChildOf(ChildOf(Sim->State,TEXT("prog")),TEXT("campaign"));
 bool bDone=false;Campaign->TryGetBoolField(TEXT("finale"),bDone);
 if(!bFinale){
  const TArray<TSharedPtr<FJsonValue>>* Missions=nullptr;FString Current;
  if(Sim->Definitions->TryGetArrayField(TEXT("campaign"),Missions)){const int32 Stage=int32(UMareSimulation::Number(Campaign,TEXT("stage")));
   if(Missions->IsValidIndex(Stage))Current=UMareSimulation::String((*Missions)[Stage]->AsObject(),TEXT("id"));}
  auto Hero=UGameplayStatics::GetPlayerCharacter(this,0);
  const bool bForced=CVarMareFinaleNow.GetValueOnGameThread()!=0;if(bForced)CVarMareFinaleNow->Set(0,ECVF_SetByCode);
  const bool bTime=Current==TEXT("festa") && !bDone && Minutes>=20*60 && Minutes<23.5*60 && Hero && Hero->GetActorLocation().Y<2500.f && !bWave;
  if(!bTime && !bForced)return;
  bFinale=true;FinaleTime=0;FinaleLine=-1;EndOmen();
  // The village comes down to the beach; Seu Tibúrcio too, for the first time in thirty years, right in front of the hero.
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
  const FVector At=Hero?Hero->GetActorLocation()+Hero->GetActorForwardVector()*260.f:FVector(3700,-2400,120);
  PartyElder=GetWorld()->SpawnActor<AMarePerson>(At,FRotator(0,Hero?Hero->GetActorRotation().Yaw+180.f:90.f,0),Params);
  if(PartyElder){PartyElder->Tags.Add(TEXT("MareElder"));PartyElder->PersonName=ElderName;PartyElder->bAmbient=true;PartyElder->SaveId=TEXT("summit_elder");
   if(!PartyElder->SetAppearance(1)){PartyElder->Destroy();PartyElder=nullptr;}else PartyElder->Express(TEXT("smile"),40.f);}
  if(auto Erupt=IConsoleManager::Get().FindConsoleVariable(TEXT("mare.VolcanoErupt")))Erupt->Set(1,ECVF_SetByCode);   // the volcano's "fireworks"
  UE_LOG(LogTemp,Display,TEXT("MARE_FINALE_START"));
 }
 FinaleTime+=DeltaSeconds;
 static const TCHAR* Lines[]={
  TEXT("A vila inteira desceu para a praia. E olha quem veio junto: Seu Tibúrcio, de chinelo novo!"),
  TEXT("Seu Tibúrcio: \"Trinta anos sem descer esse morro. A trilha encolheu ou fui eu que cresci?\""),
  TEXT("Prefeita Tuanny anuncia a Festa da Maré Alta. Seu Gregory chora. Diz que é cebola. Não tem cebola."),
  TEXT("E o vulcão... está soltando fogos? Seu Tibúrcio: \"Ele adora festa. Quem não adora?\""),
  TEXT("Vovó Dilce mandou um áudio de sete minutos. Resumo: está muito orgulhosa e quer o quarto com vista.")};
 const int32 Line=FMath::Min(int32(FinaleTime/7.f),4);
 if(Line!=FinaleLine && FinaleTime<35.f){FinaleLine=Line;Sim->LastMessage=Lines[Line];}
 if(FinaleTime>=36.f && !CreditsWidget.IsValid() && !bDone)ShowCredits();
}

void UMareSummitWorld::ShowCredits()
{
 if(!GEngine || !GEngine->GameViewport)return;
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 ChildOf(ChildOf(Sim->State,TEXT("prog")),TEXT("campaign"))->SetBoolField(TEXT("finale"),true);Sim->Save();
 auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0));
 const TWeakObjectPtr<UMareSummitWorld> Weak(this);
 auto Line=[](const FString& Text,int32 Size,FLinearColor Color){return SNew(STextBlock).Text(MareLoc::Text(Text)).Font(MareNotebook::Body(Size)).ColorAndOpacity(Color).Justification(ETextJustify::Center);};
 const FLinearColor Cream(.95f,.92f,.84f),Soft(.8f,.78f,.72f);
 CreditsWidget=SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(0,0,0,.82f)).HAlign(HAlign_Center).VAlign(VAlign_Center)
  [SNew(SVerticalBox)
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(STextBlock).Text(LOCTEXT("TheEnd","FIM")).Font(MareNotebook::Hand(140)).ColorAndOpacity(FLinearColor(.98f,.78f,.35f))]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,0,0,26)[Line(TEXT("...ou quase. A maré continua, o quiosque também, e amanhã tem oferenda."),20,Cream)]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,2)[Line(TEXT("Maré Alta Resort"),26,Cream)]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,2)[Line(TEXT("Ideia, direção e muita paciência: Sergio"),17,Soft)]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,2)[Line(TEXT("Modelos e texturas: Poly Haven, Quaternius, Fab e colaboradores (veja CREDITS.md)"),17,Soft)]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,2)[Line(TEXT("Elenco: Vovó Dilce, Seu Gregory, Padre Robson, Dona Cecília, Prefeita Tuanny e Seu Tibúrcio"),17,Soft)]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0,2,0,30)[Line(TEXT("E o vulcão, no papel de si mesmo."),17,Soft)]
   +SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(18,6))
    .OnClicked_Lambda([Weak](){if(Weak.IsValid())Weak->CloseCredits();return FReply::Handled();})
    [SNew(STextBlock).Text(MareLoc::Text(TEXT("Continuar na praia"))).Font(MareNotebook::Hand(26)).ColorAndOpacity(Cream)]]];
 GEngine->GameViewport->AddViewportWidgetContent(CreditsWidget.ToSharedRef(),80);
 if(PC){PC->bShowMouseCursor=true;PC->SetInputMode(FInputModeUIOnly().SetWidgetToFocus(CreditsWidget));PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);}
 UE_LOG(LogTemp,Display,TEXT("MARE_FINALE_CREDITS"));
}

void UMareSummitWorld::CloseCredits()
{
 if(GEngine && GEngine->GameViewport && CreditsWidget.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(CreditsWidget.ToSharedRef());CreditsWidget.Reset();
 if(auto PC=Cast<AMareController>(UGameplayStatics::GetPlayerController(this,0))){PC->bShowMouseCursor=false;PC->SetInputMode(FInputModeGameOnly());PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 Sim->LastMessage=TEXT("Missão concluída: A Festa da Maré Alta. Resgate a recompensa no celular. E boa festa!");
}

void UMareSummitWorld::Deinitialize()
{
 if(GEngine && GEngine->GameViewport && OverWidget.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(OverWidget.ToSharedRef());OverWidget.Reset();
 if(GEngine && GEngine->GameViewport && CreditsWidget.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(CreditsWidget.ToSharedRef());CreditsWidget.Reset();
 if(bFinale)if(auto Erupt=IConsoleManager::Get().FindConsoleVariable(TEXT("mare.VolcanoErupt")))Erupt->Set(-1,ECVF_SetByCode);
 if(Roar)Roar->Stop();Super::Deinitialize();
}

#undef LOCTEXT_NAMESPACE
