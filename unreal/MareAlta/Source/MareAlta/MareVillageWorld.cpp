#include "MareVillageWorld.h"
#include "MareLoc.h"
#include "MareOptions.h"
#include "MareNotebookStyle.h"
#include "Widgets/Layout/SWrapBox.h"
#include "MareGame.h"
#include "MareGamepad.h"
#include "MarePerson.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/GameUserSettings.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "NavigationSystem.h"
#include "AIController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/ConfigCacheIni.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"

TStatId UMareVillageWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareVillageWorld,STATGROUP_Tickables);}
AMarePerson* UMareVillageWorld::SpawnPerson(FVector Position,int32 Variant,const FString& Name)
{
 auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());FNavLocation Ground;
 if(!Nav || !Nav->ProjectPointToNavigation(Position,Ground,FVector(90,90,180)))return nullptr;
 // 10/11: nudged out of a prop standing on the point (a potted plant on a route start blocked the spawn for good).
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding;
 auto Person=GetWorld()->SpawnActor<AMarePerson>(Ground.Location+FVector(0,0,88),FRotator::ZeroRotator,Params);
 if(!Person)return nullptr;if(!Person->SetAppearance(Variant)){Person->Destroy();return nullptr;}
 Person->PersonName=Name;Person->bAmbient=true;Person->GetCharacterMovement()->MaxWalkSpeed=105+Variant*7;
 Person->GetCapsuleComponent()->SetCapsuleRadius(34);
 Person->GetCharacterMovement()->AvoidanceConsiderationRadius=300;Person->GetCharacterMovement()->SetAvoidanceEnabled(true);
 // Off-screen people skip their pose; not a MetaHuman, whose hidden rig drives the visible body (AMarePerson::SetMetaHuman).
 if(Person->MetaHuman.IsEmpty())Person->GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
 Person->Tags.Add(TEXT("MareVillagePerson"));return Person;
}
void UMareVillageWorld::Setup()
{
 // Retry on a later tick while navigation is loading/building; do not mark an empty population ready.
 auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());FNavLocation ReadyPoint;
 if(!Nav || Nav->IsNavigationBuildInProgress() || !Nav->ProjectPointToNavigation(FVector(3700,-1230,98),ReadyPoint,FVector(80,80,150)))return;
 FString Text;TSharedPtr<FJsonObject> Data;
 if(!FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/village_routes.json"))) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Data))return;
 const auto Vector=[](const TArray<TSharedPtr<FJsonValue>>& A){return FVector(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());};
 for(const auto& Item:Data->GetArrayField(TEXT("routes"))){TArray<FVector> Points;for(const auto& P:Item->AsObject()->GetArrayField(TEXT("points")))Points.Add(Vector(P->AsArray()));if(Points.Num()>1)Routes.Add(Points);}
 if(Routes.IsEmpty())return;
 for(const auto& Item:Data->GetArrayField(TEXT("residents"))){auto Row=Item->AsObject();const FString Name=UMareSimulation::String(Row,TEXT("name"));
  // Verified against the exported GLB roots: Human_2 is the female rig; 0/1/3 are male.
  const int32 Look=Name==TEXT("Dona Roberta") || Name==TEXT("Dona Cecília") || Name==TEXT("Alana")?2:Name==TEXT("Seu Severino") || Name==TEXT("Padre Robson")?1:3;
  auto Person=SpawnPerson(Vector(Row->GetArrayField(TEXT("position"))),Look,Name);if(!Person)continue;
  Person->SetActorRotation(FRotator(0,UMareSimulation::Number(Row,TEXT("yaw")),0));Residents.Add(Person);
  auto Target=GetWorld()->SpawnActor<AMareServiceTarget>();Target->Action=TEXT("Resident");Target->Label=Person->PersonName+TEXT(" · conversar");Target->Reach=260;Target->OcclusionTolerance=40;Target->SetOwner(Person);
  Target->AttachToActor(Person,FAttachmentTransformRules::SnapToTargetNotIncludingScale);Target->SetActorRelativeLocation(FVector(0,0,38));Person->Interaction=Target;
 }
 bReady=Routes.Num()>0;UE_LOG(LogTemp,Display,TEXT("MARE_VILLAGE_READY residents=%d routes=%d"),Residents.Num(),Routes.Num());
}
void UMareVillageWorld::UpdateWalkers(float Dt)
{
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);if(!Hero)return;
 // "Pessoas" graphics option: 3 / 6 / 12 walkers (04/11: halved from 12 for 60 FPS, every MetaHuman costs render-thread time).
 const int32 Budget=FMareOptions::Get().CrowdWalkers();
 if(Pedestrians.Num()<Budget && Routes.Num()){
  const int32 Index=Pedestrians.Num();
  // Groups (reference tip 9): in every five, a pair (leader + 1) and a trio (leader + 2). Followers spawn beside the
  // last leader and walk with it.
  const int32 Slot=Index%5;const bool bFollower=Slot==1 || Slot==3 || Slot==4;
  AMarePerson* Lead=nullptr;for(int32 K=Pedestrians.Num()-1;K>=0 && bFollower;--K)if(Pedestrians[K].Side==0){Lead=Pedestrians[K].Person.Get();break;}
  // A follower that cannot be placed beside its leader (a leader standing still by a prop) becomes a walker on its own
  // route on every third try, instead of trying the same blocked spot for the whole session (10/11).
  if(bFollower && Lead && SpawnMisses%3!=2){const float Side=Slot==4?-80.f:80.f;
   auto Person=SpawnPerson(Lead->GetActorLocation()+Lead->GetActorRightVector()*Side,Index%4,TEXT("Morador"));if(!Person)++SpawnMisses;
   if(Person){FWalker Walker;Walker.Person=Person;Walker.Leader=Lead;Walker.Side=Side;Walker.Previous=Person->GetActorLocation();Pedestrians.Add(Walker);}}
  else{int32 Leaders=0;for(const auto& Other:Pedestrians)if(Other.Side==0)++Leaders;const int32 Route=Leaders%Routes.Num();const auto& Points=Routes[Route];const int32 Start=(Index/Routes.Num()+SpawnMisses)%Points.Num();
   auto Person=SpawnPerson(Points[Start],Index%4,TEXT("Morador"));if(!Person)++SpawnMisses;
   if(Person){FWalker Walker;Walker.Person=Person;Walker.Route=Route;Walker.Point=FMath::Min(Start+1,Points.Num()-1);Walker.Previous=Person->GetActorLocation();
    Person->WalkTo(Points[Walker.Point]);Pedestrians.Add(Walker);}}
 }
 for(int32 I=Pedestrians.Num()-1;I>=0;--I){auto& W=Pedestrians[I];auto P=W.Person.Get();if(!P){Pedestrians.RemoveAt(I);continue;}
  if(I>=Budget){P->Destroy();Pedestrians.RemoveAt(I);continue;}
  P->GetMesh()->SetComponentTickInterval(FVector::DistSquared(P->GetActorLocation(),Hero->GetActorLocation())>FMath::Square(3000.f)?.15f:0.f);
  if(P->bHiddenByDistance){W.Stuck=0;continue;}   // out of the scene: paused where it is (AMarePerson::SetDistanceHidden)
  if(W.Leader.IsValid() || W.Side!=0){
   // A follower: beside its leader, a little behind; stops and chats when the leader stops; alone it just idles.
   AMarePerson* L=W.Leader.Get();if(!L){P->bConversing=false;continue;}
   const bool bStill=L->GetVelocity().Size2D()<10;
   FVector Goal=L->GetActorLocation()+L->GetActorRightVector()*W.Side-L->GetActorForwardVector()*(bStill?0.f:45.f);
   // on walkable ground (not inside a planter or a bench beside the path); else right behind the leader
   if(auto Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld())){FNavLocation On;
    if(Nav->ProjectPointToNavigation(Goal,On,FVector(40,40,200)))Goal=FVector(On.Location.X,On.Location.Y,Goal.Z);
    else Goal=L->GetActorLocation()-L->GetActorForwardVector()*90.f;}
   const float Far=FVector::Dist2D(P->GetActorLocation(),Goal);
   if(Far>650.f){P->SetActorLocation(Goal,false,nullptr,ETeleportType::TeleportPhysics);W.LastGoal=Goal;continue;}   // fell far behind (blocked): rejoin
   if(Far>110.f && FVector::Dist2D(Goal,W.LastGoal)>90.f){P->WalkTo(Goal);W.LastGoal=Goal;P->bConversing=false;}
   else if(Far<=110.f && bStill){if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();
    P->SetActorRotation(FRotator(0,(L->GetActorLocation()-P->GetActorLocation()).Rotation().Yaw,0));P->bConversing=true;}
   continue;}
  if(W.Wait>0){W.Wait-=Dt;P->bConversing=W.Wait>1;if(W.Wait<=0)P->WalkTo(Routes[W.Route][W.Point]);continue;}P->bConversing=false;
  const auto& Points=Routes[W.Route];
  if(P->AtGoal()){
   if(W.Point==Points.Num()-1)W.Direction=-1;else if(W.Point==0)W.Direction=1;W.Point+=W.Direction;W.Wait=2.f+(I%4);
   if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();P->PlayPose(TEXT("Idle"));W.Stuck=0;W.BlockedAttempts=0;
  }else if(P->GetVelocity().Size2D()<8)W.Stuck+=Dt;else{W.Stuck=0;W.BlockedAttempts=0;}
  if(W.Stuck>5){
   // A valid path request can still hit a physical obstruction. Do not retry it forever.
   if(++W.BlockedAttempts>=2){W.Direction=-W.Direction;W.Point=FMath::Clamp(W.Point+W.Direction,0,Points.Num()-1);W.BlockedAttempts=0;}
   if(!P->WalkTo(Points[W.Point])){W.Direction=-W.Direction;W.Point=FMath::Clamp(W.Point+W.Direction,0,Points.Num()-1);P->WalkTo(Points[W.Point]);}W.Stuck=0;
  }
  W.Previous=P->GetActorLocation();
 }
}
void UMareVillageWorld::UpdateHotelGuests()
{
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();bool bHotel=false;
 UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(TEXT("grand_hotel"),bHotel);
 if(!bHotel){for(auto P:HotelGuests)if(IsValid(P))P->Destroy();HotelGuests.Empty();return;}
 if(HotelGuests.Num())return;
 // Lobby floor is 45 cm above the terrace; capsule half-height 88 (tools/ue58/hotel_lobby_shell.py layout).
 // Terrace venues follow the Godot hotel_world.gd layout: restaurant floor 155, gym floor 148, pool bar 120.
 struct FSpot{FVector At;float Yaw;int32 Look;bool bTalk,bSeat;const TCHAR* Name;};
 TArray<FSpot> Spots={{FVector(-1390,6565,133),-90,2,true,false,TEXT("Recepcionista")},{FVector(-1390,6330,133),90,0,true,false,TEXT("Hóspede")},
  // 10/11 (Sergio's photo: "homem falando com parede"): this pair stood at y 5760 and 5880 with the tower's glass front
  // at y 5773 between them, one outside with his nose on the glass. Both inside now (traced: 1.1 m clear around each).
  {FVector(-1560,5940,133),90,3,true,false,TEXT("Hóspede")},{FVector(-1560,6060,133),-90,2,true,false,TEXT("Hóspede")},
  {FVector(-2660,4520,208),90,3,true,false,TEXT("Hóspede")},{FVector(-2530,4510,208),110,2,true,false,TEXT("Hóspede")},{FVector(-2600,4760,208),-90,0,false,false,TEXT("Barman")}};
 // Restaurant diners sit on the real chairs (Content/Data/hotel_seats.json, measured from the chair meshes by
 // mare_hud.chair_seats): the old fixed offsets from the table left them in the air or on the backrest. For seats
 // At is the seat top; AMarePerson::SitOn then aligns the animated pelvis on it.
 const struct{int32 Table;bool bBoth;int32 Look;}Tables[]={{0,true,0},{4,false,1}};   // 04/11: fewer people for FPS   // restaurant.json indices
 for(const auto& T:Tables)for(int32 Side=0;Side<(T.bBoth?2:1);++Side){FVector Seat;float Yaw;
  if(AMarePerson::HotelSeat(T.Table,Side,Seat,Yaw))Spots.Add({Seat,Yaw,Side?(T.Look+3)%4:T.Look,true,true,TEXT("Hóspede")});}
 for(const auto& S:Spots){FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto P=GetWorld()->SpawnActor<AMarePerson>(S.At+FVector(0,0,S.bSeat?60:0),FRotator(0,S.Yaw,0),Params);if(!P)continue;
  if(S.bSeat)P->SitOn(S.At,S.Yaw);
  if(!P->SetAppearance(S.Look)){P->Destroy();continue;}
  P->PersonName=S.Name;P->bAmbient=true;P->bConversing=S.bTalk;P->bSeated=S.bSeat;P->GetCharacterMovement()->DisableMovement();
  if(S.bSeat)P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);else P->GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn,ECR_Block);
  P->RosterIndex=HotelGuests.Num();   // neighbours take different people of the roster in turn
  P->Tags.Add(TEXT("MareHotelGuest"));HotelGuests.Add(P);}
}
// 11/11 church interior: at mass time (Content/Data/church.json) a few villagers sit in the pews, facing the altar.
void UMareVillageWorld::UpdateChurch()
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/church.json")));
  if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs) || !Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const double Hour=FMath::Fmod(UMareSimulation::Number(Sim->State,TEXT("minutes")),1440.0)/60.;
 const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const TArray<TSharedPtr<FJsonValue>>* Seats=nullptr;
 if(!Defs->TryGetArrayField(TEXT("masses"),Hours) || !Defs->TryGetArrayField(TEXT("seats"),Seats))return;   // i18n:skip
 bool bMass=false;for(const auto& H:*Hours){const auto& R=H->AsArray();if(R.Num()==2 && Hour>=R[0]->AsNumber() && Hour<R[1]->AsNumber())bMass=true;}
 if(!bMass){for(auto P:Faithful)if(IsValid(P))P->Destroy();Faithful.Empty();return;}
 if(Faithful.Num())return;
 int32 I=0;
 for(const auto& V:*Seats){const auto& A=V->AsArray();if(A.Num()!=4)continue;
  const FVector Top(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());const float Yaw=A[3]->AsNumber();
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto P=GetWorld()->SpawnActor<AMarePerson>(Top+FVector(0,0,60),FRotator(0,Yaw,0),Params);if(!P)continue;
  P->SaveId=FString::Printf(TEXT("church_%d"),I);P->SitOn(Top,Yaw);
  if(!P->SetAppearance(I%4)){P->Destroy();continue;}
  P->PersonName=TEXT("Morador");P->bAmbient=true;P->bSeated=true;P->GetCharacterMovement()->DisableMovement();
  P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);Faithful.Add(P);++I;}
}
void UMareVillageWorld::UpdatePier()
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/pier_people.json")));
  if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs) || !Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const double Hour=FMath::Fmod(UMareSimulation::Number(Sim->State,TEXT("minutes")),1440.0)/60.;
 const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const TArray<TSharedPtr<FJsonValue>>* Spots=nullptr;
 if(!Defs->TryGetArrayField(TEXT("hours"),Hours) || Hours->Num()!=2 || !Defs->TryGetArrayField(TEXT("spots"),Spots))return;   // i18n:skip
 const auto Weather=IConsoleManager::Get().FindConsoleVariable(TEXT("mare.Weather"));const int32 Forced=Weather?Weather->GetInt():0;
 const bool bRain=Forced==2 || Forced==3 || (Forced==0 && UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain"));
 const bool bOut=!bRain && Hour>=(*Hours)[0]->AsNumber() && Hour<(*Hours)[1]->AsNumber();
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);const bool bLoading=GetWorld()->GetTimeSeconds()<10;
 PierPeople.SetNum(Spots->Num());
 for(int32 I=0;I<Spots->Num();++I){const auto& A=(*Spots)[I]->AsArray();if(A.Num()!=5)continue;
  const FVector At(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber());
  // Nobody pops in or out in front of the player (same rule as the sunbathers).
  const bool bFar=bLoading || !Hero || FVector::Dist2D(Hero->GetActorLocation(),At)>2500;
  AMarePerson* Present=PierPeople[I];
  if(!bOut){if(IsValid(Present) && bFar){Present->Destroy();PierPeople[I]=nullptr;}continue;}
  if(IsValid(Present) || !bFar)continue;
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto P=GetWorld()->SpawnActor<AMarePerson>(At+FVector(0,0,90),FRotator(0,A[3]->AsNumber(),0),Params);if(!P)continue;
  if(!P->SetAppearance((I+2)%4)){P->Destroy();continue;}
  P->SaveId=FString::Printf(TEXT("pier_%d"),I);P->PersonName=TEXT("Morador");P->bAmbient=true;P->Tags.Add(TEXT("MarePierPerson"));
  P->GetCharacterMovement()->DisableMovement();P->HoldPose=A[4]->AsString();
  PierPeople[I]=P;}
}
int32 UMareVillageWorld::SunbatherCount()const{int32 N=0;for(const auto& P:Sunbathers)N+=IsValid(P.Get());return N;}
void UMareVillageWorld::UpdateSunbathers()
{
 static TSharedPtr<FJsonObject> Defs;
 if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/sunbathers.json")));
  if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs) || !Defs.IsValid())Defs=MakeShared<FJsonObject>();}
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();if(!Sim)return;
 const double Hour=UMareSimulation::Number(Sim->State,TEXT("minutes"))/60.;
 const TArray<TSharedPtr<FJsonValue>>* Hours=nullptr;const TArray<TSharedPtr<FJsonValue>>* Towels=nullptr;
 if(!Defs->TryGetArrayField(TEXT("hours"),Hours) || Hours->Num()!=2 || !Defs->TryGetArrayField(TEXT("towels"),Towels))return;
 // Same weather rule as the sky (UMareVisualWorld): the QA override first, then today's weather.
 const auto Weather=IConsoleManager::Get().FindConsoleVariable(TEXT("mare.Weather"));const int32 Forced=Weather?Weather->GetInt():0;
 const bool bRain=Forced==2 || Forced==3 || (Forced==0 && UMareSimulation::String(Sim->State,TEXT("weather"))==TEXT("rain"));
 const double Start=(*Hours)[0]->AsNumber(),End=(*Hours)[1]->AsNumber();
 const bool bOut=!bRain && Hour>=Start && Hour<End;
 // Nobody pops in or out in front of the player: after the first seconds of the session (still the loading fade),
 // arrivals and departures wait until the towel is 25 m away; an hour outside the window they leave regardless.
 auto Hero=UGameplayStatics::GetPlayerPawn(this,0);const bool bLoading=GetWorld()->GetTimeSeconds()<10;
 // Spots: beach towels (lying flat, head inland) and, with the pool day use bought, the pool loungers (torso up on
 // the backrest, pelvis just in front of its hinge, head away from the pool).
 struct FSpot{FVector Centre;float Yaw,Recline;int32 Water=0;};TArray<FSpot> Spots;   // Water: 0 lying, 1 pool, 2 sea
 const int32 Count=FMath::Min(int32(UMareSimulation::Number(Defs,TEXT("count"),5)),Towels->Num());
 for(int32 I=0;I<Count;++I){const auto& V=(*Towels)[I]->AsArray();if(V.Num()!=4)continue;
  // Long side of the towel = its local Y; the head goes inland (+Y, away from the sea).
  FVector Axis=FRotator(0,V[3]->AsNumber()+90,0).Vector();if(Axis.Y<0)Axis=-Axis;
  Spots.Add({FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber()),float(Axis.Rotation().Yaw),0.f});}
 bool bPool=false;UMareSimulation::Object(Sim->State,TEXT("unlocked"))->TryGetBoolField(TEXT("pool"),bPool);
 const TArray<TSharedPtr<FJsonValue>>* Loungers=nullptr;
 if(bPool && Defs->TryGetArrayField(TEXT("loungers"),Loungers)){const float Bend=UMareSimulation::Number(Defs,TEXT("recline"),40);
  const int32 Use=FMath::Min(int32(UMareSimulation::Number(Defs,TEXT("lounger_count"),3)),Loungers->Num());
  for(int32 I=0;I<Use;++I){const auto& V=(*Loungers)[I]->AsArray();if(V.Num()==4)Spots.Add({FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber()),float(V[3]->AsNumber()),Bend});}}
 // Swimmers treading water: in the sea off the beach, and in the pool once it is bought.
 const TArray<TSharedPtr<FJsonValue>>* Swimmers=nullptr;
 if(Defs->TryGetArrayField(TEXT("swimmers"),Swimmers))for(const auto& Value:*Swimmers){const auto& V=Value->AsArray();if(V.Num()!=5)continue;
  const int32 Water=V[4]->AsString()==TEXT("pool")?1:2;if(Water==1 && !bPool)continue;
  Spots.Add({FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber()),float(V[3]->AsNumber()),0.f,Water});}
 for(int32 I=Spots.Num();I<Sunbathers.Num();++I)if(IsValid(Sunbathers[I].Get()))Sunbathers[I]->Destroy();
 Sunbathers.SetNum(Spots.Num());
 for(int32 I=0;I<Spots.Num();++I){const FSpot& Spot=Spots[I];
  const bool bFar=bLoading || !Hero || FVector::Dist2D(Hero->GetActorLocation(),Spot.Centre)>2500;
  AMarePerson* Present=Sunbathers[I];
  if(!bOut){if(IsValid(Present) && (bFar || Hour>=End+1 || Hour<Start-1)){Present->Destroy();Sunbathers[I]=nullptr;}
   // 11/11: with the player near, whoever lies face up on a towel gets up and walks inland (a few seconds apart);
   // they are removed like before, once the towel is 25 m away or an hour later.
   else if(IsValid(Present) && Present->bLying && FMath::FRand()<.05f)Present->GetUpFromTowel(Spot.Centre+FVector(0,1800,0));
   continue;}
  if(IsValid(Present) || !bFar)continue;
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto P=GetWorld()->SpawnActor<AMarePerson>(Spot.Centre+FVector(0,0,90),FRotator(0,Spot.Yaw,0),Params);if(!P)continue;
  if(!P->SetAppearance(I%4)){P->Destroy();continue;}
  P->SaveId=FString::Printf(TEXT("bather%d"),I);P->PersonName=TEXT("Banhista");P->bAmbient=true;P->Tags.Add(TEXT("MareBather"));
  // The pool is 1.32 m deep: people stand on its floor chatting with the water at the chest; at sea they tread water.
  if(Spot.Water==1){P->bConversing=true;P->GetCharacterMovement()->DisableMovement();P->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   P->SetActorLocation(Spot.Centre+FVector(0,0,88));}
  else if(Spot.Water==2)P->TreadWater(Spot.Centre,true);else{P->LieOn(Spot.Centre,Spot.Yaw,Spot.Recline,I%3==1);P->bReading=I%3==2 && Spot.Recline<=0;}   // 09/11 (C13): face down / reading
  Sunbathers[I]=P;}
}
void UMareVillageWorld::Tick(float Dt)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()) || UGameplayStatics::IsGamePaused(this))return;
 Clock-=Dt;if(Clock>0)return;Clock=.25f;if(!bReady){Setup();if(!bReady)return;}
 UpdateWalkers(.25f);UpdateHotelGuests();UpdateSunbathers();UpdateChurch();UpdatePier();
}
void UMareVillageWorld::Speak(AMarePerson* Person,APlayerController* Controller)
{
 if(!IsValid(Person) || !Controller || Dialogue.IsValid() || !GEngine || !GEngine->GameViewport)return;
 auto PC=Cast<AMareController>(Controller);if(!PC || PC->bPhoneOpen)return;
 Speaker=Person;DialogController=Controller;Person->bConversing=true;
 const FString Greeting=Person->PersonName==TEXT("Dona Roberta")?TEXT("Sua avó Dilce sempre disse que você voltaria. O quiosque guardou muitas histórias — agora vai ganhar as suas. Se precisar de ajuda, a vila está por perto."):
  Person->PersonName==TEXT("Seu Severino")?TEXT("Eu conheci sua avó Dilce quando aquele píer ainda era novo. Venha conversar comigo para ajudar os pescadores e fazer o negócio da família crescer."):
  Person->PersonName==TEXT("Dona Cecília")?TEXT("Bem-vindo de volta! As melhores receitas da vila carregam lembranças. Sua avó Dilce nunca deixava ninguém sair do quiosque sem um sorriso."):
  Person->PersonName==TEXT("Padre Robson")?TEXT("A vila fica melhor quando cuidamos uns dos outros. Sua avó Dilce fez isso por muitos anos. Fico feliz em ver você por aqui."):
  TEXT("Bem-vindo à vila! É bom ver o quiosque da família ganhando vida outra vez.");
 auto Sim=GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>();
 // The giver of the open chapter offers its current step in person.
 FString Story;auto Actions=SNew(SWrapBox).UseAllottedSize(true);TWeakObjectPtr<AMarePerson> WeakPerson(Person);TWeakObjectPtr<APlayerController> WeakController(Controller);
 const FString Result=ActionResult;ActionResult.Empty();
 const auto AddAction=[&](const FString& Label,TFunction<void()> Callback){Actions->AddSlot().Padding(0,0,8,6)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(10,2)).OnClicked_Lambda([this,Sim,Callback,WeakPerson,WeakController](){
  Sim->LastMessage.Empty();Callback();const FString Message=Sim->LastMessage;CloseDialogue();ActionResult=Message;
  if(WeakPerson.IsValid() && WeakController.IsValid())Speak(WeakPerson.Get(),WeakController.Get());return FReply::Handled();})[MareNotebook::InkLabel(Label,16)]];};
 const TArray<TSharedPtr<FJsonValue>>* Chapters=nullptr;
 if(Sim->Definitions->TryGetArrayField(TEXT("chapters"),Chapters))for(const auto& Value:*Chapters){auto C=Value->AsObject();const FString Id=UMareSimulation::String(C,TEXT("id"));
  if(UMareSimulation::String(C,TEXT("giver"))!=Person->PersonName || !Sim->IsChapterOpen(Id))continue;
  if(Sim->IsChapterDone(Id)){Story=TEXT("Obrigado pela ajuda com \"")+UMareSimulation::String(C,TEXT("title"))+TEXT("\". A vila não vai esquecer.");break;}
  const int32 StepIndex=Sim->ChapterStep(Id);const auto Step=C->GetArrayField(TEXT("steps"))[StepIndex]->AsObject();const FString Kind=UMareSimulation::String(Step,TEXT("kind")),Item=UMareSimulation::String(Step,TEXT("item"));
  int32 Goal=1;const int32 Have=Sim->ChapterStepProgress(Id,Goal);
  Story=(StepIndex==0?UMareSimulation::String(C,TEXT("story"))+TEXT("\n\n"):FString())+FString::Printf(TEXT("%s · passo %d/3: "),*UMareSimulation::String(C,TEXT("title")),StepIndex+1)+UMareSimulation::String(Step,TEXT("text"))+FString::Printf(TEXT(" (%d/%d)"),Have,Goal);
  if(Kind==TEXT("deliver") && Have<Goal){const int32 Missing=Goal-Have;
   AddAction(FString::Printf(TEXT("Comprar %d no mercadinho · R$ %.0f"),Missing,Sim->SupplyCost(Item,Missing)),[Sim,Item,Missing](){Sim->BuySupply(Item,Missing);});}
  else if(Have>=Goal)AddAction(Kind==TEXT("deliver")?FString::Printf(TEXT("Entregar %d do estoque"),Goal):Kind==TEXT("pay")?FString::Printf(TEXT("Doar R$ %d"),Goal):FString(TEXT("Concluir passo")),[Sim,Id](){Sim->AdvanceChapter(Id);});
  break;
 }
 Actions->AddSlot().Padding(0,0,0,6)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(10,2)).OnClicked_Lambda([this](){CloseDialogue();return FReply::Handled();})
  [SNew(STextBlock).Font(MareNotebook::Hand(16)).ColorAndOpacity(MareNotebook::Tag).Text(MareGamepad::UsingGamepad()?FText::Format(NSLOCTEXT("MareVillage","ByePad","Até logo · {0}"),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Dive"))))
   :FText::Format(NSLOCTEXT("MareVillage","ByeKeys","Até logo · {0} / {1}"),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Interact"))),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Pause")))))]];
 Dialogue=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.25f)).HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(20)
 [SNew(SBox).WidthOverride(620)[MareNotebook::Page(SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(MareLoc::Text(Person->PersonName)).Font(MareNotebook::Hand(26)).ColorAndOpacity(MareNotebook::Brown)]
  +SVerticalBox::Slot().AutoHeight().Padding(0,9)[SNew(STextBlock).Text(MareLoc::Text(Story.IsEmpty()?Greeting:Story)).WrapTextAt(530).Font(MareNotebook::Body(14)).ColorAndOpacity(MareNotebook::Ink)]
  +SVerticalBox::Slot().AutoHeight().Padding(0,0,0,6)[SNew(STextBlock).Text(MareLoc::Text(Result)).Visibility(Result.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible).WrapTextAt(530).Font(MareNotebook::Hand(17)).ColorAndOpacity(MareNotebook::Green)]
  +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[Actions])]];
 GEngine->GameViewport->AddViewportWidgetContent(Dialogue.ToSharedRef(),35);
 {const TWeakObjectPtr<UMareVillageWorld> Weak(this);MareGamepad::PushMenu(Dialogue.ToSharedRef(),[Weak](){if(Weak.IsValid())Weak->CloseDialogue();});}
 Controller->bShowMouseCursor=true;Controller->SetInputMode(FInputModeGameAndUI());Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(Sim->State,TEXT("prog")),TEXT("experience")),TEXT("greeted"))->SetBoolField(Person->PersonName,true);Sim->Save();
}
void UMareVillageWorld::CloseDialogue()
{
 if(GEngine && GEngine->GameViewport && Dialogue.IsValid())GEngine->GameViewport->RemoveViewportWidgetContent(Dialogue.ToSharedRef());Dialogue.Reset();
 if(auto Person=Speaker.Get())Person->bConversing=false;Speaker.Reset();
 if(auto PC=DialogController.Get()){PC->bShowMouseCursor=false;PC->SetInputMode(FInputModeGameOnly());PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}DialogController.Reset();
}
void UMareVillageWorld::Quip(AMarePerson* Person,APlayerController* Controller,const FString& Name,const FString& Line,const TArray<FString>& Replies,
 TFunction<FString(int32)> OnReply,TFunction<void()> OnClosed)
{
 if(!IsValid(Person) || !Controller || Dialogue.IsValid() || !GEngine || !GEngine->GameViewport){if(OnClosed)OnClosed();return;}
 auto PC=Cast<AMareController>(Controller);if(!PC || PC->bPhoneOpen){if(OnClosed)OnClosed();return;}
 Speaker=Person;DialogController=Controller;Person->bConversing=true;QuipClosed=OnClosed;
 auto Actions=SNew(SWrapBox).UseAllottedSize(true);TWeakObjectPtr<AMarePerson> WeakPerson(Person);TWeakObjectPtr<APlayerController> WeakController(Controller);
 for(int32 I=0;I<Replies.Num();++I)
  Actions->AddSlot().Padding(0,0,8,6)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(10,2)).OnClicked_Lambda([this,I,Name,OnReply,WeakPerson,WeakController](){
   // The reaction page keeps the same "closed" callback: take it before closing the question page.
   auto Closed=MoveTemp(QuipClosed);QuipClosed=nullptr;const FString Reaction=OnReply?OnReply(I):FString();CloseDialogue();
   if(WeakPerson.IsValid() && WeakController.IsValid() && !Reaction.IsEmpty())Quip(WeakPerson.Get(),WeakController.Get(),Name,Reaction,{},nullptr,Closed);else if(Closed)Closed();
   return FReply::Handled();})[MareNotebook::InkLabel(Replies[I],16)]];
 Actions->AddSlot().Padding(0,0,0,6)[SNew(SMarePadButton).ButtonStyle(&MareNotebook::InkButton()).ContentPadding(FMargin(10,2)).OnClicked_Lambda([this](){CloseDialogue();return FReply::Handled();})
  [SNew(STextBlock).Font(MareNotebook::Hand(16)).ColorAndOpacity(MareNotebook::Tag).Text(MareGamepad::UsingGamepad()?FText::Format(NSLOCTEXT("MareVillage","ByePad","Até logo · {0}"),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Dive"))))
   :FText::Format(NSLOCTEXT("MareVillage","ByeKeys","Até logo · {0} / {1}"),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Interact"))),MareLoc::Text(MareGamepad::ActionLabel(TEXT("Pause")))))]];
 Dialogue=SNew(SBorder).BorderBackgroundColor(FLinearColor(0,0,0,.25f)).HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(20)
 [SNew(SBox).WidthOverride(620)[MareNotebook::Page(SNew(SVerticalBox)
  +SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(MareLoc::Text(Name)).Font(MareNotebook::Hand(26)).ColorAndOpacity(MareNotebook::Brown)]
  +SVerticalBox::Slot().AutoHeight().Padding(0,9)[SNew(STextBlock).Text(MareLoc::Text(Line)).WrapTextAt(530).Font(MareNotebook::Body(14)).ColorAndOpacity(MareNotebook::Ink)]
  +SVerticalBox::Slot().AutoHeight().Padding(0,6,0,0)[Actions])]];
 GEngine->GameViewport->AddViewportWidgetContent(Dialogue.ToSharedRef(),35);
 {const TWeakObjectPtr<UMareVillageWorld> Weak(this);MareGamepad::PushMenu(Dialogue.ToSharedRef(),[Weak](){if(Weak.IsValid())Weak->CloseDialogue();});}
 Controller->bShowMouseCursor=true;Controller->SetInputMode(FInputModeGameAndUI());Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
}
AMarePerson* UMareVillageWorld::HoldPedestrianNear(FVector At,float MinDist,float MaxDist,float Seconds)
{
 for(auto& W:Pedestrians){auto P=W.Person.Get();if(!P || P->bConversing || W.Wait>0)continue;const float D=FVector::Dist2D(P->GetActorLocation(),At);if(D<MinDist || D>MaxDist)continue;
  if(auto AI=Cast<AAIController>(P->GetController()))AI->StopMovement();W.Wait=Seconds;P->bConversing=true;return P;}
 return nullptr;
}
void UMareVillageWorld::ReleasePedestrian(AMarePerson* Person){for(auto& W:Pedestrians)if(W.Person.Get()==Person)W.Wait=FMath::Min(W.Wait,.5f);}
void UMareVillageWorld::Deinitialize(){CloseDialogue();Residents.Empty();HotelGuests.Empty();Sunbathers.Empty();Faithful.Empty();Pedestrians.Empty();Super::Deinitialize();}
