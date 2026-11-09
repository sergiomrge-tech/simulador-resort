// Playable boat tour (CHECKLIST_EXPANSOES 2.2). Values in Content/Data/tours.json "boat_tour"; the rating goes through
// MareSimulation::GuideTour like the dialogue tours (choices 0 good, 1 ok, 2 bad per stop) plus the bonus of the trip
// (dolphins seen, passengers seasick).
#include "MareBoatTourWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "MareGame.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Components/AudioComponent.h"

namespace
{
 UMareSimulation* SimOf(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 UStaticMesh* TourMesh(const FString& Name)
 {
  return LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Custom/TourBoat/%s/%s.%s"),*Name,*Name,*Name));
 }
 AStaticMeshActor* Prop(UWorld* World,const FString& Name,const FVector& At,const FRotator& Rot)
 {
  auto Mesh=TourMesh(Name);if(!Mesh)return nullptr;FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto A=World->SpawnActor<AStaticMeshActor>(At,Rot,P);if(!A)return nullptr;A->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
  A->GetStaticMeshComponent()->SetStaticMesh(Mesh);A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);return A;
 }
 FVector Vec(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O.IsValid() || !O->TryGetArrayField(Key,A) || A->Num()<2)return FVector::ZeroVector;
  return FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),A->Num()>2?(*A)[2]->AsNumber():0);
 }
 // A model whose front is Blender -Y arrives with its front on UE -Y: this turns that front to the direction F.
 FRotator FaceAlong(const FVector& F){return FRotationMatrix::MakeFromYZ(-F.GetSafeNormal(),FVector::UpVector).Rotator();}
}

TStatId UMareBoatTourWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareBoatTourWorld,STATGROUP_Tickables);}

TSharedPtr<FJsonObject> UMareBoatTourWorld::Defs()const
{
 auto S=SimOf(GetWorld());return S?UMareSimulation::Object(S->ToursDefs(),TEXT("boat_tour")):MakeShared<FJsonObject>();
}

FVector UMareBoatTourWorld::RoutePoint(int32 I)const
{
 const TArray<TSharedPtr<FJsonValue>>* Route=nullptr;if(!Defs()->TryGetArrayField(TEXT("route"),Route) || !Route->IsValidIndex(I))return Vec(Defs(),TEXT("dock"));
 const auto R=(*Route)[I]->AsObject();return R->HasField(TEXT("buoy"))?Vec(R,TEXT("buoy")):Vec(R,TEXT("at"));
}

FString UMareBoatTourWorld::StopKind(int32 Stop)const{return Stop==0?TEXT("vests"):Stop==1?TEXT("dolphins"):TEXT("story");}

FVector UMareBoatTourWorld::Forward()const{return FRotator(0,Heading,0).Vector();}

bool UMareBoatTourWorld::IsActive()const{return IsValid(Boat);}

void UMareBoatTourWorld::Deinitialize()
{
 auto Kill=[](auto& List){for(auto& A:List)if(IsValid(A))A->Destroy();List.Empty();};
 Kill(Passengers);Kill(VestTargets);Kill(Vests);Kill(Buoys);Kill(Dolphins);
 if(IsValid(StoryTarget))StoryTarget->Destroy();if(IsValid(Boat))Boat->Destroy();Boat=nullptr;
 if(IsValid(EngineSound))EngineSound->Stop();EngineSound=nullptr;
 Super::Deinitialize();
}

bool UMareBoatTourWorld::Start(APlayerController* Controller)
{
 auto S=SimOf(GetWorld());if(!S || IsActive() || !Controller || !Controller->GetPawn())return false;
 const auto D=Defs();TourId=UMareSimulation::String(D,TEXT("tour"));
 const int32 Sold=S->TourCount(TEXT("sold"),TourId);
 if(!S->IsTourBoarding(TourId)){S->LastMessage=TEXT("Só dá para guiar na hora da saída.");return false;}
 if(Sold<=0){S->LastMessage=TEXT("Nenhum bilhete vendido para este passeio.");return false;}
 const FVector Spawn=Vec(D,TEXT("spawn"));Heading=Spawn.Z;
 const float SeaZ=UMareSimulation::Number(D,TEXT("sea_z"),-30);
 // Born on the wave where it is, so nothing jumps when it starts riding the swell.
 static UMaterialParameterCollection* TimeMPC=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
 const float Storm0=TimeMPC?UKismetMaterialLibrary::GetScalarParameterValue(this,TimeMPC,TEXT("Storm")):0.f;
 const float Z0=SeaZ+AMarePerson::SeaHeight(FVector2D(Spawn.X,Spawn.Y),GetWorld()->GetTimeSeconds(),Storm0)+UMareSimulation::Number(D,TEXT("freeboard"),10);
 Boat=Prop(GetWorld(),UMareSimulation::String(D,TEXT("mesh")),FVector(Spawn.X,Spawn.Y,Z0),FaceAlong(Forward()));if(!Boat)return false;
 PC=Controller;SeatRel.Reset();Speed=Throttle=Time=RoughTime=DolphinWatch=DolphinTime=0;Next=0;StopIndex=-1;Sick=0;Bonus=0;Choices.Reset();Says.Reset();
 bStopActive=bDolphinsHere=bDolphinBad=bStory=bCheered=false;
 // Passengers sit on the benches facing the centre line; each has a vest target for the first stop.
 const TArray<TSharedPtr<FJsonValue>>* Seats=nullptr;D->TryGetArrayField(TEXT("seats"),Seats);
 const int32 N=Seats?FMath::Min(Sold,Seats->Num()):0;Vested.Init(false,N);
 for(int32 I=0;I<N;++I){const auto& P=(*Seats)[I]->AsArray();const FVector Local(P[0]->AsNumber(),P[1]->AsNumber(),P[2]->AsNumber());
  const FVector At=Boat->GetActorTransform().TransformPosition(Local);
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto Person=GetWorld()->SpawnActor<AMarePerson>(At+FVector(0,0,60),Boat->GetActorRotation(),Params);if(!Person)continue;
  Person->SaveId=FString::Printf(TEXT("boat_%s_%d"),*TourId,I);Person->PersonName=TEXT("Turista");Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);
  Person->bAmbient=true;Person->bSeated=true;Person->GetCharacterMovement()->DisableMovement();Person->SetActorEnableCollision(false);
  const float Yaw=Boat->GetActorRotation().Yaw+(Local.X>0?180.f:0.f);
  Person->SitOn(At,Yaw);Passengers.Add(Person);
  auto T=GetWorld()->SpawnActor<AMareServiceTarget>(At+FVector(0,0,45),FRotator::ZeroRotator);
  if(T){T->Action=TEXT("TourVest");T->DataIndex=I;T->Label=TEXT("Entregar o colete");T->Reach=320;T->OcclusionTolerance=80;T->SetActorHiddenInGame(true);
   T->AttachToActor(Boat,FAttachmentTransformRules::KeepWorldTransform);}
  VestTargets.Add(T);}
 // Buoys of the route.
 const TArray<TSharedPtr<FJsonValue>>* Route=nullptr;
 if(D->TryGetArrayField(TEXT("route"),Route))for(int32 I=0;I<Route->Num();++I){const bool bStop=(*Route)[I]->AsObject()->HasField(TEXT("stop"));
  if(auto B=Prop(GetWorld(),bStop?TEXT("TourBoat_stop"):TEXT("TourBoat_buoy"),RoutePoint(I)+FVector(0,0,SeaZ),FRotator(0,FMath::FRandRange(0.f,360.f),0)))Buoys.Add(B);}
 // The pilot at the helm: no walking, the view moves with the boat.
 auto Hero=Cast<ACharacter>(Controller->GetPawn());
 if(Hero){Hero->GetCharacterMovement()->DisableMovement();Hero->GetCharacterMovement()->SetComponentTickEnabled(false);Hero->SetActorEnableCollision(false);
  Hero->SetActorLocation(Boat->GetActorTransform().TransformPosition(Vec(D,TEXT("helm"))));Hero->AttachToActor(Boat,FAttachmentTransformRules::KeepWorldTransform);}
 Controller->SetIgnoreMoveInput(true);
 UMareSimulation::Object(S->State,TEXT("tours"))->SetStringField(TEXT("active"),TourId);
 S->LastMessage=TEXT("Passeio de barco: siga as boias. W/S acelera, A/D vira.");
 UMareAudioWorld::Action(this,TEXT("reception_bell"));
 return true;
}

void UMareBoatTourWorld::Say(int32 Seat,const FString& Line,float Seconds){Says.Add(Seat,TPair<FString,float>(Line,Time+Seconds));}

void UMareBoatTourWorld::GiveVest(int32 Seat)
{
 if(!bStopActive || StopKind(StopIndex)!=TEXT("vests") || !Vested.IsValidIndex(Seat) || Vested[Seat])return;
 Vested[Seat]=true;if(VestTargets.IsValidIndex(Seat) && IsValid(VestTargets[Seat]))VestTargets[Seat]->SetActorHiddenInGame(true);
 // The vest on the passenger's chest, following the body.
 if(Passengers.IsValidIndex(Seat) && IsValid(Passengers[Seat])){AMarePerson* P=Passengers[Seat];USkeletalMeshComponent* Body=P->GetMesh();
  const FName Bone=Body->GetBoneIndex(TEXT("spine_04"))!=INDEX_NONE?FName(TEXT("spine_04")):FName(TEXT("spine_03"));
  const FVector Chest=Body->GetBoneIndex(Bone)!=INDEX_NONE?Body->GetSocketLocation(Bone):P->GetActorLocation()+FVector(0,0,40);
  if(auto V=Prop(GetWorld(),TEXT("TourBoat_vest"),Chest+P->GetActorForwardVector()*3-FVector(0,0,8),FaceAlong(P->GetActorForwardVector()))){
   V->AttachToComponent(Body,FAttachmentTransformRules::KeepWorldTransform,Bone);Vests.Add(V);}}
 Say(Seat,UMareSimulation::String(UMareSimulation::Object(Defs(),TEXT("lines")),TEXT("vest_thanks")),2.5f);
 UMareAudioWorld::Action(this,TEXT("cleaning_towels"),nullptr,.5f);
}

void UMareBoatTourWorld::TellStory()
{
 if(!bStopActive || StopKind(StopIndex)!=TEXT("story") || bStory)return;bStory=true;
 if(auto S=SimOf(GetWorld())){const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;
  if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->IsValidIndex(2))
   S->LastMessage=TEXT("Você contou: ")+UMareSimulation::String((*Stops)[2]->AsObject(),TEXT("good"))+TEXT(". A turma adorou!");}
 for(int32 I=0;I<Passengers.Num();I+=2)Say(I,TEXT("Que lugar lindo!"),3);
}

void UMareBoatTourWorld::BeginStop(int32 Stop)
{
 bStopActive=true;StopIndex=Stop;DolphinWatch=DolphinTime=0;bDolphinBad=false;bStory=false;bCheered=false;
 const auto D=Defs();auto S=SimOf(GetWorld());const auto Lines=UMareSimulation::Object(D,TEXT("lines"));const FString Kind=StopKind(Stop);
 const TArray<TSharedPtr<FJsonValue>>* Route=nullptr;D->TryGetArrayField(TEXT("route"),Route);
 const FVector Look=Route && Route->IsValidIndex(Next)?Vec((*Route)[Next]->AsObject(),TEXT("look")):FVector::ZeroVector;
 if(Kind==TEXT("vests"))for(int32 I=0;I<VestTargets.Num();++I)if(IsValid(VestTargets[I]))VestTargets[I]->SetActorHiddenInGame(Vested[I]);
 if(Kind==TEXT("dolphins")){bDolphinsHere=FMath::FRand()<UMareSimulation::Number(D,TEXT("dolphin_chance"),.75);
  if(bDolphinsHere)for(int32 I=0;I<int32(UMareSimulation::Number(D,TEXT("dolphin_count"),3));++I)
   if(auto Dl=Prop(GetWorld(),TEXT("TourBoat_dolphin"),Look,FRotator::ZeroRotator))Dolphins.Add(Dl);}
 if(Kind==TEXT("story")){
  if(!StoryTarget){StoryTarget=GetWorld()->SpawnActor<AMareServiceTarget>(Look,FRotator::ZeroRotator);
   if(StoryTarget){StoryTarget->Action=TEXT("TourStory");StoryTarget->Label=TEXT("Contar a história da praia deserta");StoryTarget->Reach=6000;StoryTarget->OcclusionTolerance=800;}}
  if(StoryTarget){StoryTarget->SetActorLocation(Look);StoryTarget->SetActorHiddenInGame(false);}}
 if(S){const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;
  if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->IsValidIndex(Stop))
   S->LastMessage=UMareSimulation::String((*Stops)[Stop]->AsObject(),TEXT("text"))+TEXT(" ")+UMareSimulation::String(Lines,Kind==TEXT("dolphins") && !bDolphinsHere?TEXT("no_dolphins"):Kind);}
 UMareAudioWorld::Action(this,TEXT("reception_bell"),nullptr,.6f);
}

void UMareBoatTourWorld::EndStop(int32 Choice)
{
 Choices.Add(Choice);bStopActive=false;
 for(auto& T:VestTargets)if(IsValid(T))T->SetActorHiddenInGame(true);if(StoryTarget)StoryTarget->SetActorHiddenInGame(true);
 StopIndex=-1;++Next;
 UMareAudioWorld::Action(this,Choice==0?TEXT("deal_accept"):TEXT("deal_decline"),nullptr,.5f);
}

void UMareBoatTourWorld::UpdateBoat(float Dt)
{
 const auto D=Defs();auto Controller=PC.Get();if(!Controller)return;
 float Thr=0,Steer=0;
 if(QATime>0){QATime-=Dt;Thr=QAThrottle;Steer=QASteer;}
 else{Thr=(Controller->IsInputKeyDown(EKeys::W) || Controller->IsInputKeyDown(EKeys::Up)?1.f:0.f)-(Controller->IsInputKeyDown(EKeys::S) || Controller->IsInputKeyDown(EKeys::Down)?1.f:0.f)
   +Controller->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
  Steer=(Controller->IsInputKeyDown(EKeys::D) || Controller->IsInputKeyDown(EKeys::Right)?1.f:0.f)-(Controller->IsInputKeyDown(EKeys::A) || Controller->IsInputKeyDown(EKeys::Left)?1.f:0.f)
   +Controller->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);}
 Thr=FMath::Clamp(Thr,-1.f,1.f);Steer=FMath::Clamp(Steer,-1.f,1.f);Throttle=Thr;
 // A better boat (Personalizar "barco") is faster and steadier.
 const auto Up=UMareSimulation::Object(SimOf(GetWorld())->ToursDefs(),TEXT("upgrades"));const int32 BoatTier=SimOf(GetWorld())->CustomTier(TEXT("passeios"),TEXT("barco"))-1;
 const float Max=UMareSimulation::Number(D,TEXT("max_speed"),950)*(1+UMareSimulation::Number(Up,TEXT("boat_speed_per_tier"),.07)*BoatTier),Rev=UMareSimulation::Number(D,TEXT("reverse_speed"),250),Acc=UMareSimulation::Number(D,TEXT("accel"),260);
 const float Target=Thr>=0?Thr*Max:Thr*Rev;
 Speed+=FMath::Clamp(Target-Speed,-Acc*1.6f*Dt,Acc*Dt);
 Heading+=Steer*UMareSimulation::Number(D,TEXT("turn"),42)*Dt*FMath::Clamp(FMath::Abs(Speed)/300.f,.25f,1.f)*(Speed<-5?-1.f:1.f);
 FVector At=Boat->GetActorLocation()+Forward()*Speed*Dt;
 // Shallows and the shore stop the boat (deep sea has no collision; sand, rocks and the pier do).
 if(FMath::Abs(Speed)>5){FHitResult Hit;FCollisionQueryParams Q(TEXT("MareBoatShallow"),false,Boat);Q.AddIgnoredActor(Controller->GetPawn());
  const FVector Probe=At+Forward()*(Speed>0?420.f:-120.f);
  if(GetWorld()->LineTraceSingleByChannel(Hit,Probe+FVector(0,0,400),Probe-FVector(0,0,160),ECC_Visibility,Q) && Hit.ImpactPoint.Z>UMareSimulation::Number(D,TEXT("sea_z"),-30)-70){
   Speed=-Speed*.2f;At=Boat->GetActorLocation();ShallowTimer=2.f;}}
 ShallowTimer=FMath::Max(0.f,ShallowTimer-Dt);
 // Waves: the boat rides the real sea surface (AMarePerson::SeaHeight replicates the ocean material's offset), sampled
 // at the bow, the stern and both sides for heave, pitch and roll; turning heels it and speed lifts the bow.
 auto S=SimOf(GetWorld());const float SpeedFrac=FMath::Abs(Speed)/Max;
 static UMaterialParameterCollection* TimeMPC=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));
 const float Storm=TimeMPC?UKismetMaterialLibrary::GetScalarParameterValue(this,TimeMPC,TEXT("Storm")):0.f;const float T=GetWorld()->GetTimeSeconds();
 const FVector F=Forward(),Rgt(-F.Y,F.X,0);
 auto H=[&](const FVector& P){return AMarePerson::SeaHeight(FVector2D(P.X,P.Y),T,Storm);};
 const float HBow=H(At+F*380),HStern=H(At-F*380),HPort=H(At-Rgt*120),HStar=H(At+Rgt*120);
 At.Z=UMareSimulation::Number(D,TEXT("sea_z"),-30)+(HBow+HStern+HPort+HStar)*.25f+UMareSimulation::Number(D,TEXT("freeboard"),10)+4.f*SpeedFrac;
 const float BowPitch=FMath::RadiansToDegrees(FMath::Atan2(HBow-HStern,760.f))+3.5f*SpeedFrac+(Target>Speed+50?1.5f:0.f);
 const float SideRoll=FMath::RadiansToDegrees(FMath::Atan2(HStar-HPort,240.f))*.7f+Steer*5.f*SpeedFrac;
 const float Swell=1.f+Storm;
 const FRotator Base=FaceAlong(Forward());
 Boat->SetActorLocationAndRotation(At,FRotator(SideRoll,Base.Yaw,BowPitch));
 // The sea goes flat inside the hull (ocean material, MPC Boat*): a level a little under the deck.
 if(TimeMPC){const FVector Mid=At+F*UMareSimulation::Number(D,TEXT("centre"),430);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatX"),Mid.X);UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatY"),Mid.Y);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatYaw"),Heading);UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatOn"),1);
  // The lowest deck point (the bow dips when pitching): the flat water stays under it everywhere in the hull.
  const float BowDeck=Boat->GetActorTransform().TransformPosition(FVector(0,-780,12)).Z,SternDeck=Boat->GetActorTransform().TransformPosition(FVector(0,-40,12)).Z;
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC,TEXT("BoatH"),FMath::Min(BowDeck,SternDeck)-UMareSimulation::Number(D,TEXT("sea_z"),-30)-30);}
 // Full speed for too long makes a passenger seasick.
 if(SpeedFrac>UMareSimulation::Number(D,TEXT("seasick_speed"),.85)){RoughTime+=Dt*Swell;
  if(RoughTime>=UMareSimulation::Number(D,TEXT("seasick_seconds"),6)+UMareSimulation::Number(Up,TEXT("seasick_seconds_per_tier"),1.5)*BoatTier && Sick<Passengers.Num()){RoughTime=0;
   const double Penalty=UMareSimulation::Number(D,TEXT("seasick_rating"),.3);if(Bonus>-1+Penalty-1e-6)Bonus-=Penalty;
   Say(Sick,UMareSimulation::String(UMareSimulation::Object(D,TEXT("lines")),TEXT("seasick")),6);++Sick;
   if(S)S->LastMessage=TEXT("Um turista ficou enjoado: devagar com o acelerador!");}}
 else RoughTime=FMath::Max(0.f,RoughTime-Dt*.5f);
 // 09/11: the boat's own engine (boat_engine, a real hot-bulb boat engine recording, CC BY 4.0); the tour was silent.
 if(!IsValid(EngineSound))if(auto Audio=GetWorld()->GetSubsystem<UMareAudioWorld>())EngineSound=Audio->PlayCue(TEXT("boat_engine"),.22f,&At);
 if(IsValid(EngineSound)){EngineSound->SetWorldLocation(At);EngineSound->SetPitchMultiplier(.82f+.42f*SpeedFrac);EngineSound->SetVolumeMultiplier(.13f+.14f*SpeedFrac);}
 // Buoys bob on the swell and are nudged aside by the hull (never inside the boat).
 const FVector Mid=At+F*UMareSimulation::Number(D,TEXT("centre"),430);
 for(int32 I=0;I<Buoys.Num();++I)if(IsValid(Buoys[I])){FVector B=Buoys[I]->GetActorLocation();
  {const FVector Rel=B-Mid;const float Along=FVector::DotProduct(Rel,F),Across=FVector::DotProduct(Rel,Rgt);
   if(FMath::Abs(Along)<500 && FMath::Abs(Across)<200)B+=Rgt*((Across>=0?200.f:-200.f)-Across);}
  B.Z=UMareSimulation::Number(D,TEXT("sea_z"),-30)+H(B)-20.f;Buoys[I]->SetActorLocationAndRotation(B,FRotator(4.f*FMath::Sin(Time+I),Buoys[I]->GetActorRotation().Yaw,3.f*FMath::Sin(Time*.8f+I)));}
}

void UMareBoatTourWorld::UpdateRoute(float Dt)
{
 const auto D=Defs();auto Controller=PC.Get();
 // The model's origin is the transom: distances are measured from the middle of the hull.
 const FVector Here=Boat->GetActorLocation()+Forward()*UMareSimulation::Number(D,TEXT("centre"),430);
 const TArray<TSharedPtr<FJsonValue>>* Route=nullptr;D->TryGetArrayField(TEXT("route"),Route);const int32 Count=Route?Route->Num():0;
 // Dolphins: three jumping around the stop's look point, each on its own circle and timing.
 for(int32 I=0;I<Dolphins.Num();++I)if(IsValid(Dolphins[I])){
  const FVector Look=Route && Route->IsValidIndex(Next)?Vec((*Route)[Next]->AsObject(),TEXT("look")):Dolphins[I]->GetActorLocation();
  const float A=Time*.35f+I*2.1f,R=300.f+100.f*I;const FVector Centre(Look.X,Look.Y,0);
  const FVector Pos=Centre+FVector(FMath::Cos(A)*R,FMath::Sin(A)*R,0);const FVector Dir(-FMath::Sin(A),FMath::Cos(A),0);
  const float Phase=FMath::Fmod(Time*.45f+I*.33f,1.f);const float Jump=Phase<.35f?FMath::Sin(Phase/.35f*PI):-.4f;
  const float SeaZ=UMareSimulation::Number(D,TEXT("sea_z"),-30);
  const float Z=SeaZ-60+Jump*240.f,Slope=Phase<.35f?FMath::Cos(Phase/.35f*PI)*1.4f:0.f;
  Dolphins[I]->SetActorLocationAndRotation(FVector(Pos.X,Pos.Y,Z),FaceAlong(Dir+FVector(0,0,Slope)));
  if(Phase<.05f && !bCheered && bStopActive){bCheered=true;for(int32 K=0;K<Passengers.Num();K+=2)Say(K,UMareSimulation::String(UMareSimulation::Object(D,TEXT("lines")),TEXT("cheer")),3);
   UMareAudioWorld::Action(this,TEXT("whale_splash"),&Pos,.4f);}}
 if(!bStopActive){
  if(Next>=Count){// Back to the pier.
   if(FVector::Dist2D(Here,Vec(D,TEXT("dock")))<UMareSimulation::Number(D,TEXT("dock_radius"),900) && FMath::Abs(Speed)<UMareSimulation::Number(D,TEXT("stop_speed"),140))Finish();
   return;}
  const auto R=(*Route)[Next]->AsObject();const float Dist=FVector::Dist2D(Here,RoutePoint(Next));
  if(R->HasField(TEXT("buoy"))){if(Dist<UMareSimulation::Number(D,TEXT("buoy_radius"),800)){++Next;UMareAudioWorld::Action(this,TEXT("bell"),nullptr,.3f);}}
  else if(Dist<UMareSimulation::Number(D,TEXT("stop_radius"),900) && FMath::Abs(Speed)<UMareSimulation::Number(D,TEXT("stop_speed"),140))BeginStop(int32(UMareSimulation::Number(R,TEXT("stop"))));
  return;}
 const FString Kind=StopKind(StopIndex);const float Away=FVector::Dist2D(Here,RoutePoint(Next));const bool bLeft=Away>UMareSimulation::Number(D,TEXT("stop_radius"),900)*1.8f;
 if(Kind==TEXT("vests")){int32 Done=0;for(bool B:Vested)Done+=B;
  if(Done>=Vested.Num())EndStop(0);else if(bLeft)EndStop(Done*2>=Vested.Num()?1:2);}
 else if(Kind==TEXT("dolphins")){
  if(!bDolphinsHere){DolphinTime+=Dt;if(DolphinTime>5 || bLeft)EndStop(1);return;}
  const FVector Look=Vec((*Route)[Next]->AsObject(),TEXT("look"));const float Max=UMareSimulation::Number(D,TEXT("max_speed"),950);
  // Speeding toward the dolphins is the bad choice; engine off and looking at them is the good one.
  if(FVector::Dist2D(Here,Look)<1500 && FMath::Abs(Speed)>.6f*Max)bDolphinBad=true;
  bool bLooking=false;
  if(Controller && Controller->PlayerCameraManager){const FVector Eye=Controller->PlayerCameraManager->GetCameraLocation();
   const FVector To=(FVector(Look.X,Look.Y,Look.Z)-Eye).GetSafeNormal();
   bLooking=FVector::DotProduct(To,Controller->PlayerCameraManager->GetCameraRotation().Vector())>FMath::Cos(FMath::DegreesToRadians(UMareSimulation::Number(D,TEXT("dolphin_look_deg"),35)));}
  if(bLooking && FMath::Abs(Speed)<40)DolphinWatch+=Dt;
  if(DolphinWatch>=UMareSimulation::Number(D,TEXT("dolphin_watch_seconds"),4)){if(!bDolphinBad)Bonus+=UMareSimulation::Number(D,TEXT("dolphin_bonus"),.5);EndStop(bDolphinBad?2:0);}
  else if(bLeft)EndStop(bDolphinBad?2:1);}
 else{if(bStory)EndStop(0);else if(bLeft)EndStop(1);}
}

void UMareBoatTourWorld::Finish()
{
 auto S=SimOf(GetWorld());auto Controller=PC.Get();const auto D=Defs();
 while(Choices.Num()<3)Choices.Add(2);
 if(S){S->GuideTour(TourId,Choices,Bonus);UMareSimulation::Object(S->State,TEXT("tours"))->RemoveField(TEXT("active"));}
 if(Controller){if(auto Hero=Cast<ACharacter>(Controller->GetPawn())){Hero->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
   Hero->SetActorLocation(Vec(D,TEXT("hero_return")));Hero->SetActorRotation(FRotator(0,Hero->GetActorRotation().Yaw,0));
   Hero->SetActorEnableCollision(true);Hero->GetCharacterMovement()->SetComponentTickEnabled(true);Hero->GetCharacterMovement()->SetMovementMode(MOVE_Walking);}
  Controller->SetIgnoreMoveInput(false);}
 auto Kill=[](auto& List){for(auto& A:List)if(IsValid(A))A->Destroy();List.Empty();};
 Kill(Passengers);Kill(VestTargets);Kill(Vests);Kill(Buoys);Kill(Dolphins);
 if(IsValid(StoryTarget))StoryTarget->Destroy();StoryTarget=nullptr;
 if(IsValid(Boat))Boat->Destroy();Boat=nullptr;Says.Reset();
 if(IsValid(EngineSound))EngineSound->Stop();EngineSound=nullptr;
 if(auto MPC=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime")))UKismetMaterialLibrary::SetScalarParameterValue(this,MPC,TEXT("BoatOn"),0);
 UMareAudioWorld::Action(this,TEXT("money_coins"));
}

void UMareBoatTourWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || GetWorld()->IsPaused())return;
 // A save made at sea comes back with the tour marked active but no boat: clear it.
 if(!IsActive()){if(auto S=SimOf(GetWorld())){auto T=UMareSimulation::Object(S->State,TEXT("tours"));
   if(!UMareSimulation::String(T,TEXT("active")).IsEmpty() && UMareSimulation::String(T,TEXT("active"))==UMareSimulation::String(Defs(),TEXT("tour")))T->RemoveField(TEXT("active"));}return;}
 Time+=DeltaSeconds;
 // The pilot never swims: a wave crest over the helm must not switch the character to swimming.
 if(auto Hero=PC.IsValid()?Cast<ACharacter>(PC->GetPawn()):nullptr)if(Hero->GetCharacterMovement()->MovementMode!=MOVE_None)Hero->GetCharacterMovement()->DisableMovement();
 // The first moment the boat holds still: the passengers settle their pelvis on the benches (AMarePerson::SitOn
 // aligns once against a world point), then everyone rides the waves attached to the boat.
 if(Time<1.2f)return;
 if(SeatRel.Num()!=Passengers.Num()){SeatRel.Reset();for(auto& P:Passengers)SeatRel.Add(IsValid(P)?P->GetActorTransform().GetRelativeTransform(Boat->GetActorTransform()):FTransform::Identity);}
 UpdateBoat(DeltaSeconds);if(!IsActive())return;
 // Passengers ride rigidly with the boat (their own seated logic must not drift them off the benches).
 for(int32 I=0;I<Passengers.Num();++I)if(IsValid(Passengers[I]))Passengers[I]->SetActorTransform(SeatRel[I]*Boat->GetActorTransform(),false,nullptr,ETeleportType::TeleportPhysics);
 UpdateRoute(DeltaSeconds);
 // Dolphins left behind once the stop is over and the boat is far.
 if(!bStopActive && Dolphins.Num() && IsActive()){bool bFar=true;for(auto& Dl:Dolphins)if(IsValid(Dl) && FVector::Dist2D(Dl->GetActorLocation(),Boat->GetActorLocation())<6000)bFar=false;
  if(bFar){for(auto& Dl:Dolphins)if(IsValid(Dl))Dl->Destroy();Dolphins.Empty();}}
}

FString UMareBoatTourWorld::Status()const
{
 if(!IsActive())return FString();const auto D=Defs();const auto Lines=UMareSimulation::Object(D,TEXT("lines"));
 const TArray<TSharedPtr<FJsonValue>>* Route=nullptr;D->TryGetArrayField(TEXT("route"),Route);const int32 Count=Route?Route->Num():0;
 FString Goal;
 if(ShallowTimer>0)Goal=UMareSimulation::String(Lines,TEXT("shallow"));
 else if(bStopActive){const FString Kind=StopKind(StopIndex);
  if(Kind==TEXT("vests")){int32 Done=0;for(bool B:Vested)Done+=B;Goal=UMareSimulation::String(Lines,TEXT("vests"))+FString::Printf(TEXT(" (%d/%d)"),Done,Vested.Num());}
  else if(Kind==TEXT("dolphins"))Goal=UMareSimulation::String(Lines,bDolphinsHere?TEXT("dolphins"):TEXT("no_dolphins"));
  else Goal=UMareSimulation::String(Lines,TEXT("story"));}
 else if(Next>=Count)Goal=UMareSimulation::String(Lines,TEXT("return"));
 else{int32 Stops=0;for(int32 I=0;I<=Next && I<Count;++I)Stops+=(*Route)[I]->AsObject()->HasField(TEXT("stop"));
  Goal=(*Route)[Next]->AsObject()->HasField(TEXT("stop"))?FString::Printf(TEXT("Parada %d de 3: chegue devagar na boia amarela"),Stops):FString::Printf(TEXT("Siga para a próxima boia (%d de %d)"),Next+1,Count);}
 return FString::Printf(TEXT("W/S acelera · A/D vira · %.0f nós · %s"),FMath::Abs(Speed)*0.0194384f,*Goal);
}

TArray<TPair<FVector,FString>> UMareBoatTourWorld::Bubbles()const
{
 TArray<TPair<FVector,FString>> Out;
 for(const auto& Pair:Says)if(Pair.Value.Value>Time && Passengers.IsValidIndex(Pair.Key) && IsValid(Passengers[Pair.Key]))
  Out.Add({Passengers[Pair.Key]->GetActorLocation()+FVector(0,0,70),Pair.Value.Key});
 return Out;
}

FString UMareBoatTourWorld::QA(const FString& Cmd)
{
 if(Cmd.StartsWith(TEXT("drive:"))){TArray<FString> P;Cmd.Mid(6).ParseIntoArray(P,TEXT(","));
  if(P.Num()==3){QAThrottle=FCString::Atof(*P[0]);QASteer=FCString::Atof(*P[1]);QATime=FCString::Atof(*P[2]);}return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("goto:")) && IsActive()){const int32 I=FCString::Atoi(*Cmd.Mid(5));bStopActive=false;StopIndex=-1;const FVector P=RoutePoint(I);
  const FVector From=I>0?RoutePoint(I-1):Boat->GetActorLocation();Heading=(P-From).GetSafeNormal2D().Rotation().Yaw;
  Boat->SetActorLocation(FVector(P.X,P.Y,Boat->GetActorLocation().Z)-Forward()*(UMareSimulation::Number(Defs(),TEXT("centre"),430)+350));Speed=0;Next=I;return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("vest:"))){GiveVest(FCString::Atoi(*Cmd.Mid(5)));return TEXT("ok");}
 if(Cmd==TEXT("story")){TellStory();return TEXT("ok");}
 if(Cmd==TEXT("look") && PC.IsValid() && IsActive()){const TArray<TSharedPtr<FJsonValue>>* Route=nullptr;Defs()->TryGetArrayField(TEXT("route"),Route);
  if(Route && Route->IsValidIndex(Next)){const FVector Look=Vec((*Route)[Next]->AsObject(),TEXT("look"));
   if(!Look.IsZero() && PC->PlayerCameraManager)PC->SetControlRotation((Look-PC->PlayerCameraManager->GetCameraLocation()).Rotation());}return TEXT("ok");}
 if(Cmd==TEXT("finish") && IsActive()){Finish();return TEXT("ok");}
 return FString::Printf(TEXT("active=%d next=%d stop=%d speed=%.0f choices=%d bonus=%.2f sick=%d"),IsActive(),Next,StopIndex,Speed,Choices.Num(),Bonus,Sick);
}
