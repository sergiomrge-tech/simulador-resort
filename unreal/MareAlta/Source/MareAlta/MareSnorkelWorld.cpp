// Guided snorkel (CHECKLIST_EXPANSOES 2.3). Values in Content/Data/tours.json "snorkel_tour"; the rating goes through
// MareSimulation::SnorkelScore (the three stop choices and the bonus) and GuideTour, like the other guided tours.
#include "MareSnorkelWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareReefWorld.h"
#include "MareAudioWorld.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

namespace
{
 UMareSimulation* SimOf(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 AStaticMeshActor* Prop(UWorld* World,const FString& Name,const FVector& At,const FRotator& Rot)
 {
  auto Mesh=LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Custom/TourBoat/%s/%s.%s"),*Name,*Name,*Name));if(!Mesh)return nullptr;
  FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto A=World->SpawnActor<AStaticMeshActor>(At,Rot,P);if(!A)return nullptr;A->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
  A->GetStaticMeshComponent()->SetStaticMesh(Mesh);A->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);return A;
 }
 FVector Vec(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;if(!O.IsValid() || !O->TryGetArrayField(Key,A) || A->Num()<2)return FVector::ZeroVector;
  return FVector((*A)[0]->AsNumber(),(*A)[1]->AsNumber(),A->Num()>2?(*A)[2]->AsNumber():0);
 }
 // A model whose front is Blender +Y arrives with its front on UE -Y: this turns that front to the direction F.
 FRotator FaceAlong(const FVector& F){return FRotationMatrix::MakeFromYZ(-F.GetSafeNormal(),FVector::UpVector).Rotator();}
 UMaterialParameterCollection* TimeMPC(){static UMaterialParameterCollection* M=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/World/Materials/MPC_MareTime.MPC_MareTime"));return M;}
 TArray<TSharedPtr<FJsonValue>> SpeciesList(const TSharedPtr<FJsonObject>& D)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;return D.IsValid() && D->TryGetArrayField(TEXT("species"),A)?*A:TArray<TSharedPtr<FJsonValue>>();
 }
}

TStatId UMareSnorkelWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareSnorkelWorld,STATGROUP_Tickables);}
TSharedPtr<FJsonObject> UMareSnorkelWorld::Defs()const
{
 auto S=SimOf(GetWorld());return S?UMareSimulation::Object(S->ToursDefs(),TEXT("snorkel_tour")):MakeShared<FJsonObject>();
}
FString UMareSnorkelWorld::Line(const FString& Key)const{return UMareSimulation::String(UMareSimulation::Object(Defs(),TEXT("lines")),Key);}
FVector UMareSnorkelWorld::Forward()const{return FRotator(0,Heading,0).Vector();}
bool UMareSnorkelWorld::IsActive()const{return IsValid(Boat);}

void UMareSnorkelWorld::Deinitialize()
{
 auto Kill=[](auto& List){for(auto& A:List)if(IsValid(A))A->Destroy();List.Empty();};
 Kill(Swimmers);Kill(Targets);Kill(Masks);if(IsValid(Boat))Boat->Destroy();Boat=nullptr;
 Super::Deinitialize();
}

bool UMareSnorkelWorld::DeepEnough(const FVector& P)const
{
 // Swimmers stay where the sea is at least chest deep (rocks, sand banks and the pier are left alone).
 FHitResult Hit;FCollisionQueryParams Q(TEXT("MareSnorkelDepth"),false);for(auto& Sw:Swimmers)if(IsValid(Sw))Q.AddIgnoredActor(Sw);
 for(const auto& C:Corals)if(C.IsValid())Q.AddIgnoredComponent(C.Get());
 if(IsValid(Boat))Q.AddIgnoredActor(Boat);if(PC.IsValid() && PC->GetPawn())Q.AddIgnoredActor(PC->GetPawn());
 if(!GetWorld()->LineTraceSingleByChannel(Hit,FVector(P.X,P.Y,300),FVector(P.X,P.Y,-1500),ECC_Visibility,Q))return true;
 return Hit.ImpactPoint.Z<UMareSimulation::Number(Defs(),TEXT("sea_z"),-30)-80;
}

bool UMareSnorkelWorld::Start(APlayerController* Controller)
{
 auto S=SimOf(GetWorld());if(!S || IsActive() || !Controller || !Controller->GetPawn())return false;
 const auto D=Defs();TourId=UMareSimulation::String(D,TEXT("tour"));
 if(!UMareSimulation::String(UMareSimulation::Object(S->State,TEXT("tours")),TEXT("active")).IsEmpty()){S->LastMessage=TEXT("Já tem um passeio em andamento.");return false;}
 if(!S->IsTourBoarding(TourId)){S->LastMessage=TEXT("Só dá para guiar na hora da saída.");return false;}
 const int32 Sold=S->TourCount(TEXT("sold"),TourId);
 if(Sold<=0){S->LastMessage=TEXT("Nenhum bilhete vendido para este passeio.");return false;}
 const FVector Anchor=Vec(D,TEXT("anchor"));Heading=Anchor.Z;const float SeaZ=UMareSimulation::Number(D,TEXT("sea_z"),-30);
 Boat=Prop(GetWorld(),UMareSimulation::String(D,TEXT("mesh")),FVector(Anchor.X,Anchor.Y,SeaZ+UMareSimulation::Number(D,TEXT("freeboard"),22)),FaceAlong(Forward()));
 if(!Boat)return false;
 PC=Controller;Time=CoralClock=LostClock=LadderClock=SayClock=0;CoralTouches=Seen=0;Lost=-1;bLostDone=bCrewFetched=bSecondStop=bMasked=false;Says.Reset();
 // Species: fish schools come from the reef (MareReefWorld), corals are the reef's coral meshes, one target each.
 const auto List=SpeciesList(D);Presented.Init(false,List.Num());SpeciesCorals.SetNum(List.Num());Corals.Reset();
 TMap<FString,int32> CoralKind;
 for(int32 I=0;I<List.Num();++I){const TArray<TSharedPtr<FJsonValue>>* Names=nullptr;
  if(List[I]->AsObject()->TryGetArrayField(TEXT("coral"),Names))for(const auto& N:*Names)CoralKind.Add(N->AsString(),I);}
 for(TActorIterator<AActor> It(GetWorld());It;++It){TArray<UStaticMeshComponent*> Parts;It->GetComponents(Parts);
  for(auto C:Parts)if(C && C->GetStaticMesh())if(const int32* K=CoralKind.Find(C->GetStaticMesh()->GetName())){SpeciesCorals[*K].Add(C);Corals.Add(C);}}
 for(int32 I=0;I<List.Num();++I){auto T=GetWorld()->SpawnActor<AMareServiceTarget>(FVector(0,0,-100000),FRotator::ZeroRotator);if(!T)continue;
  T->Action=TEXT("TourSpecies");T->DataIndex=I;T->Reach=UMareSimulation::Number(D,TEXT("look_range"),900);T->OcclusionTolerance=70;
  T->Label=TEXT("Apresentar: ")+UMareSimulation::String(List[I]->AsObject(),TEXT("name"));Targets.Add(T);}
 // The group jumps in at the ladder, one swimmer per ticket.
 const FVector Start=Vec(D,TEXT("hero_start")),Ladder=Vec(D,TEXT("ladder"));const int32 N=FMath::Min(Sold,6);
 for(int32 I=0;I<N;++I){// In a line between the ladder and the guide.
  FVector P=(Start+Ladder)*.5f+FVector(((I%2)?1:-1)*(70.f+65.f*(I/2)),(I%3)*30.f-30.f,0);P.Z=SeaZ;
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto Person=GetWorld()->SpawnActor<AMarePerson>(P+FVector(0,0,90),FRotator(0,(Start-Ladder).Rotation().Yaw,0),Params);if(!Person)continue;
  Person->SaveId=FString::Printf(TEXT("snorkel_%d"),I);Person->PersonName=TEXT("Turista");Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);
  Person->bAmbient=true;Person->Tags.Add(TEXT("MareBather"));Person->TreadWater(P,true);Swimmers.Add(Person);SwimPos.Add(P);}
 SwimPos.SetNum(Swimmers.Num());
 // The player jumps in first, facing the reef.
 if(auto Hero=Cast<ACharacter>(Controller->GetPawn())){Hero->SetActorLocation(Start);Hero->GetCharacterMovement()->StopMovementImmediately();
  Controller->SetControlRotation(FRotator(-12,(Start-Ladder).Rotation().Yaw,0));}
 UMareSimulation::Object(S->State,TEXT("tours"))->SetStringField(TEXT("active"),TourId);
 const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;FString First;
 if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->Num())First=UMareSimulation::String((*Stops)[0]->AsObject(),TEXT("text"))+TEXT(" ");
 S->LastMessage=First+Line(TEXT("start"));
 UMareAudioWorld::Action(this,TEXT("swim_splash"));
 return true;
}

void UMareSnorkelWorld::Say(int32 Swimmer,const FString& Text,float Seconds){if(Swimmers.IsValidIndex(Swimmer))Says.Add(Swimmer,TPair<FString,float>(Text,Time+Seconds));}

void UMareSnorkelWorld::PutOnMasks()
{
 // The mask over the eyes (the face rig's eye bones when the MetaHuman has them), following the head.
 bMasked=true;
 for(auto& P:Swimmers){if(!IsValid(P))continue;USkeletalMeshComponent* Head=P->GetMesh();FVector Eyes=Head->GetBoneIndex(TEXT("head"))!=INDEX_NONE?Head->GetSocketLocation(TEXT("head"))+FVector(0,0,9)+P->GetActorForwardVector()*9:P->GetActorLocation()+FVector(0,0,70);
  TArray<USkeletalMeshComponent*> Parts;P->GetComponents(Parts);
  for(auto C:Parts)if(C->GetBoneIndex(TEXT("FACIAL_L_Eye"))!=INDEX_NONE && C->GetBoneIndex(TEXT("FACIAL_R_Eye"))!=INDEX_NONE){
   Eyes=(C->GetSocketLocation(TEXT("FACIAL_L_Eye"))+C->GetSocketLocation(TEXT("FACIAL_R_Eye")))*.5f;Head=C;break;}
  const FName Bone=Head->GetBoneIndex(TEXT("head"))!=INDEX_NONE?FName(TEXT("head")):NAME_None;
  if(auto M=Prop(GetWorld(),TEXT("TourBoat_snorkel"),Eyes+P->GetActorForwardVector()*1.5f,FaceAlong(P->GetActorForwardVector()))){
   M->AttachToComponent(Head,FAttachmentTransformRules::KeepWorldTransform,Bone);Masks.Add(M);}}
}

bool UMareSnorkelWorld::Candidates(int32 Species,TArray<FVector>& Out)const
{
 Out.Reset();const auto List=SpeciesList(Defs());if(!List.IsValidIndex(Species))return false;
 const FString Fish=UMareSimulation::String(List[Species]->AsObject(),TEXT("fish")),Floor=UMareSimulation::String(List[Species]->AsObject(),TEXT("reef"));
 if(!Fish.IsEmpty()){if(auto Reef=GetWorld()->GetSubsystem<UMareReefWorld>())Out=Reef->FishPositions(Fish);}
 else if(!Floor.IsEmpty()){if(auto Reef=GetWorld()->GetSubsystem<UMareReefWorld>())Out=Reef->InstancePositions(Floor);}
 else if(SpeciesCorals.IsValidIndex(Species))for(const auto& C:SpeciesCorals[Species])if(C.IsValid())Out.Add(C->Bounds.Origin+FVector(0,0,C->Bounds.BoxExtent.Z*.4f));
 return Out.Num()>0;
}

void UMareSnorkelWorld::UpdateTargets()
{
 // Each species' target sits on the school or coral that best matches the aim, so the usual E prompt picks it.
 auto Controller=PC.Get();if(!Controller)return;FVector Eye;FRotator View;Controller->GetPlayerViewPoint(Eye,View);const FVector Aim=View.Vector();
 const auto List=SpeciesList(Defs());TArray<FVector> Points;
 for(int32 I=0;I<Targets.Num();++I){auto T=Targets[I];if(!IsValid(T))continue;FVector Best(0,0,-100000);float Score=FLT_MAX;
  if(Candidates(I,Points))for(const FVector& P:Points){const FVector Delta=P-Eye;const float Dist=Delta.Size();if(Dist>T->Reach || Dist<1)continue;
   const float Along=FVector::DotProduct(Delta,Aim);if(Along<=0)continue;const float Rank=(Delta-Aim*Along).Size()+Dist*.035f;if(Rank<Score){Score=Rank;Best=P;}}
  T->SetActorLocation(Best);
  const FString Name=UMareSimulation::String(List.IsValidIndex(I)?List[I]->AsObject():nullptr,TEXT("name"));
  T->Label=Presented.IsValidIndex(I) && Presented[I]?Name+TEXT(" (o grupo já viu)"):TEXT("Apresentar: ")+Name;}
}

void UMareSnorkelWorld::Present(int32 Species)
{
 auto S=SimOf(GetWorld());const auto D=Defs();const auto List=SpeciesList(D);if(!S || !IsActive() || !List.IsValidIndex(Species))return;
 const auto Sp=List[Species]->AsObject();const FString Name=UMareSimulation::String(Sp,TEXT("name"));
 if(Presented[Species]){Say(FMath::RandRange(0,FMath::Max(0,Swimmers.Num()-1)),Line(TEXT("seen")),2.5f);S->LastMessage=TEXT("O grupo já viu o ")+Name+TEXT(".");return;}
 Presented[Species]=true;++Seen;
 for(int32 I=Species%2;I<Swimmers.Num();I+=2)if(I!=Lost)Say(I,Line(TEXT("present")),3);
 FString Text=Name+TEXT(": ")+UMareSimulation::String(Sp,TEXT("fact"))+TEXT(".");
 // The sergeant majors are the tour's second stop.
 if(int32(UMareSimulation::Number(Sp,TEXT("stop"),0))==1 && !bSecondStop){bSecondStop=true;const TArray<TSharedPtr<FJsonValue>>* Stops=nullptr;
  if(UMareSimulation::Object(S->ToursDefs(),TEXT("stops"))->TryGetArrayField(TourId,Stops) && Stops->IsValidIndex(1))Text=UMareSimulation::String((*Stops)[1]->AsObject(),TEXT("text"))+TEXT(" ")+Text;}
 S->LastMessage=Text+FString::Printf(TEXT(" (%d de %d espécies)"),Seen,List.Num());
 UMareAudioWorld::Action(this,TEXT("deal_accept"),nullptr,.5f);
 if(Seen>=int32(UMareSimulation::Number(D,TEXT("lost_after"),2)) && Lost<0 && !bLostDone)BeginLost();
}

void UMareSnorkelWorld::BeginLost()
{
 if(Swimmers.IsEmpty() || Lost>=0 || bLostDone)return;auto Controller=PC.Get();if(!Controller || !Controller->GetPawn())return;
 const auto D=Defs();Lost=Swimmers.Num()-1;LostClock=0;
 // Drifts away from the player, toward deep enough water (tries several directions).
 const FVector Hero=Controller->GetPawn()->GetActorLocation();const FVector Away=(SwimPos[Lost]-Hero).GetSafeNormal2D();
 const float Dist=UMareSimulation::Number(D,TEXT("lost_distance"),1150);LostAt=SwimPos[Lost];
 for(const float Turn:{0.f,40.f,-40.f,80.f,-80.f,120.f,-120.f,180.f}){const FVector P=Hero+(Away.IsNearlyZero()?Forward():Away).RotateAngleAxis(Turn,FVector::UpVector)*Dist;
  if(DeepEnough(P)){LostAt=FVector(P.X,P.Y,SwimPos[Lost].Z);break;}}
 Say(Lost,Line(TEXT("lost")),6);
 if(auto S=SimOf(GetWorld()))S->LastMessage=TEXT("Um turista se perdeu do grupo! Procure o balão e vá buscá-lo.");
}

void UMareSnorkelWorld::Found(bool bCrew)
{
 if(Lost<0)return;const int32 Who=Lost;Lost=-1;bLostDone=true;bCrewFetched=bCrew;auto S=SimOf(GetWorld());
 if(bCrew){SwimPos[Who]=Vec(Defs(),TEXT("ladder"));SwimPos[Who].Z=UMareSimulation::Number(Defs(),TEXT("sea_z"),-30);if(S)S->LastMessage=Line(TEXT("crew"));}
 else{Say(Who,Line(TEXT("found")),3.5f);if(S)S->LastMessage=TEXT("Você trouxe o turista de volta para o grupo.");UMareAudioWorld::Action(this,TEXT("deal_accept"),nullptr,.4f);}
}

void UMareSnorkelWorld::UpdateSwimmers(float Dt)
{
 auto Controller=PC.Get();auto Hero=Controller?Controller->GetPawn():nullptr;if(!Hero)return;const auto D=Defs();
 const float SeaZ=UMareSimulation::Number(D,TEXT("sea_z"),-30),Speed=UMareSimulation::Number(D,TEXT("follow_speed"),175),Gap=UMareSimulation::Number(D,TEXT("spacing"),120);
 const FVector H=Hero->GetActorLocation();FVector F=Controller->GetControlRotation().Vector().GetSafeNormal2D();if(F.IsNearlyZero())F=Forward();const FVector R(-F.Y,F.X,0);
 int32 Slot=0;
 for(int32 I=0;I<Swimmers.Num();++I){auto P=Swimmers[I];if(!IsValid(P))continue;FVector Goal;float V=Speed;
  if(I==Lost){Goal=LostAt;V=UMareSimulation::Number(D,TEXT("lost_drift"),55);}
  else{// Two by two behind the guide, a little to each side.
   const int32 Row=Slot/2,Side=Slot%2?1:-1;++Slot;Goal=H-F*(Gap*1.4f+Gap*Row)+R*Side*Gap*.55f;}
  FVector Pos=SwimPos[I];FVector To=FVector(Goal.X-Pos.X,Goal.Y-Pos.Y,0);const float Dist=To.Size();
  if(Dist>35){const FVector Step=To/Dist*FMath::Min(Dist,V*FMath::Clamp(Dist/180.f,.35f,1.f)*Dt);const FVector Next=Pos+Step;
   if(DeepEnough(Next) || !DeepEnough(Pos))Pos=Next;}
  // Never inside the hull: pushed out to the nearer side of the boat.
  {const FVector Rel=Pos-Vec(D,TEXT("anchor"))*FVector(1,1,0);const FVector BF=Forward(),BR(-BF.Y,BF.X,0);const float Along=FVector::DotProduct(Rel,BF),Across=FVector::DotProduct(Rel,BR);
   if(Along>-60 && Along<UMareSimulation::Number(D,TEXT("centre"),430)*2+60 && FMath::Abs(Across)<175)Pos+=BR*((Across>=0?175.f:-175.f)-Across);}
  // Keep a body's width from each other.
  for(int32 J=0;J<I;++J){const FVector Gp=FVector(Pos.X-SwimPos[J].X,Pos.Y-SwimPos[J].Y,0);const float L=Gp.Size();if(L<85 && L>1)Pos+=Gp/L*(85-L)*.5f;}
  Pos.Z=SeaZ;const FVector Move=Pos-SwimPos[I];SwimPos[I]=Pos;P->SwimAt=Pos;
  const float Yaw=Move.SizeSquared2D()>.01f?Move.Rotation().Yaw:(H-Pos).Rotation().Yaw;
  P->SetActorRotation(FRotator(0,FMath::FixedTurn(P->GetActorRotation().Yaw,Yaw,120.f*Dt),0));}
}

void UMareSnorkelWorld::UpdateCoral(float Dt)
{
 // Touching coral: the guide's body (centre and chest) within the margin of a coral's bounds.
 CoralClock=FMath::Max(0.f,CoralClock-Dt);auto Hero=PC.IsValid()?PC->GetPawn():nullptr;if(!Hero || CoralClock>0)return;
 const float Margin=UMareSimulation::Number(Defs(),TEXT("coral_margin"),22);const FVector H=Hero->GetActorLocation();
 for(const auto& C:Corals){if(!C.IsValid() || FVector::DistSquared2D(C->Bounds.Origin,H)>FMath::Square(400.f))continue;const FBox Box=C->Bounds.GetBox();
  if(Box.ComputeSquaredDistanceToPoint(H)<Margin*Margin || Box.ComputeSquaredDistanceToPoint(H-FVector(0,0,35))<Margin*Margin){
   ++CoralTouches;CoralClock=UMareSimulation::Number(Defs(),TEXT("coral_cooldown"),4);
   int32 Near=-1;float Best=FLT_MAX;for(int32 I=0;I<Swimmers.Num();++I)if(I!=Lost){const float L=FVector::DistSquared2D(SwimPos[I],H);if(L<Best){Best=L;Near=I;}}
   Say(Near,Line(TEXT("coral")),3);
   if(auto S=SimOf(GetWorld()))S->LastMessage=TEXT("Você encostou no coral! O grupo viu, e a nota do passeio cai.");
   UMareAudioWorld::Action(this,TEXT("deal_decline"),nullptr,.5f);return;}}
}

void UMareSnorkelWorld::UpdateLostAndCount(float Dt)
{
 auto Controller=PC.Get();auto Hero=Controller?Controller->GetPawn():nullptr;if(!Hero)return;const auto D=Defs();auto S=SimOf(GetWorld());
 const FVector H=Hero->GetActorLocation();
 if(Lost<0 && !bLostDone && Time>UMareSimulation::Number(D,TEXT("lost_seconds"),70))BeginLost();
 if(Lost>=0){LostClock+=Dt;SayClock-=Dt;if(SayClock<=0){SayClock=5;Say(Lost,Line(TEXT("lost")),5.5f);}
  if(FVector::Dist2D(H,SwimPos[Lost])<UMareSimulation::Number(D,TEXT("fetch_radius"),320))Found(false);}
 // The count at the ladder: everyone present ends the tour; a lost swimmer is fetched by the crew after a while.
 const FVector Ladder=Vec(D,TEXT("ladder"));const float Radius=UMareSimulation::Number(D,TEXT("count_radius"),520);
 if(Seen<1 || FVector::Dist2D(H,Ladder)>Radius){LadderClock=0;
  // Swimming far off ends the tour: the crew brings everybody back.
  if(Time>5 && FVector::Dist2D(H,Ladder)>6500){if(Lost>=0)Found(true);else bCrewFetched=true;Finish();}
  return;}
 LadderClock+=Dt;
 if(Lost>=0){if(LadderClock>UMareSimulation::Number(D,TEXT("crew_fetch_seconds"),45))Found(true);
  else if(S && FMath::Fmod(LadderClock,6.f)<Dt)S->LastMessage=FText::Format(FText::FromString(Line(TEXT("missing"))),Swimmers.Num()-1,Swimmers.Num()).ToString();
  return;}
 int32 Here=0;for(const FVector& P:SwimPos)Here+=FVector::Dist2D(P,Ladder)<Radius*1.8f;
 if(Here>=Swimmers.Num())Finish();
}

void UMareSnorkelWorld::UpdateBoat()
{
 // The anchored boat rides the swell (heave, pitch, roll); the sea goes flat inside its hull (MPC Boat*).
 const auto D=Defs();const FVector Anchor=Vec(D,TEXT("anchor"));const float SeaZ=UMareSimulation::Number(D,TEXT("sea_z"),-30),T=GetWorld()->GetTimeSeconds();
 const float Storm=TimeMPC()?UKismetMaterialLibrary::GetScalarParameterValue(this,TimeMPC(),TEXT("Storm")):0.f;
 const FVector F=Forward(),Rgt(-F.Y,F.X,0),Mid=FVector(Anchor.X,Anchor.Y,0)+F*UMareSimulation::Number(D,TEXT("centre"),430);
 auto Hs=[&](const FVector& P){return AMarePerson::SeaHeight(FVector2D(P.X,P.Y),T,Storm);};
 const float Bow=Hs(Mid+F*380),Stern=Hs(Mid-F*380),Port=Hs(Mid-Rgt*120),Star=Hs(Mid+Rgt*120);
 const FRotator Base=FaceAlong(F);
 Boat->SetActorLocationAndRotation(FVector(Anchor.X,Anchor.Y,SeaZ+(Bow+Stern+Port+Star)*.25f+UMareSimulation::Number(D,TEXT("freeboard"),22)),
  FRotator(FMath::RadiansToDegrees(FMath::Atan2(Star-Port,240.f))*.7f,Base.Yaw,FMath::RadiansToDegrees(FMath::Atan2(Bow-Stern,760.f))));
 if(TimeMPC()){UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC(),TEXT("BoatX"),Mid.X);UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC(),TEXT("BoatY"),Mid.Y);
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC(),TEXT("BoatYaw"),Heading);UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC(),TEXT("BoatOn"),1);
  const float BowDeck=Boat->GetActorTransform().TransformPosition(FVector(0,-780,12)).Z,SternDeck=Boat->GetActorTransform().TransformPosition(FVector(0,-40,12)).Z;
  UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC(),TEXT("BoatH"),FMath::Min(BowDeck,SternDeck)-SeaZ-30);}
}

void UMareSnorkelWorld::Finish()
{
 if(!IsActive())return;auto S=SimOf(GetWorld());auto Controller=PC.Get();const auto D=Defs();
 if(S){TArray<int32> Choices;double Bonus=0;S->SnorkelScore(CoralTouches,Seen,bCrewFetched,Choices,Bonus);S->GuideTour(TourId,Choices,Bonus);
  UMareSimulation::Object(S->State,TEXT("tours"))->RemoveField(TEXT("active"));
  if(!bCrewFetched)S->LastMessage=Line(TEXT("done"))+TEXT(" ")+S->LastMessage;}
 // Back on the pier with the group.
 if(Controller)if(auto Hero=Cast<ACharacter>(Controller->GetPawn())){Hero->SetActorLocation(Vec(D,TEXT("hero_return")));Hero->GetCharacterMovement()->StopMovementImmediately();}
 auto Kill=[](auto& List){for(auto& A:List)if(IsValid(A))A->Destroy();List.Empty();};
 Kill(Swimmers);Kill(Targets);Kill(Masks);SwimPos.Reset();Says.Reset();Corals.Reset();SpeciesCorals.Reset();
 if(IsValid(Boat))Boat->Destroy();Boat=nullptr;
 if(TimeMPC())UKismetMaterialLibrary::SetScalarParameterValue(this,TimeMPC(),TEXT("BoatOn"),0);
 UMareAudioWorld::Action(this,TEXT("money_coins"));
}

void UMareSnorkelWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld() || GetWorld()->IsPaused())return;
 // A save made in the water comes back with the tour marked active but nobody swimming: clear it.
 if(!IsActive()){if(auto S=SimOf(GetWorld())){auto T=UMareSimulation::Object(S->State,TEXT("tours"));
   if(!UMareSimulation::String(T,TEXT("active")).IsEmpty() && UMareSimulation::String(T,TEXT("active"))==UMareSimulation::String(Defs(),TEXT("tour")))T->RemoveField(TEXT("active"));}return;}
 Time+=DeltaSeconds;UpdateBoat();
 if(QAHold>0){QAHold-=DeltaSeconds;if(auto Hero=PC.IsValid()?Cast<ACharacter>(PC->GetPawn()):nullptr){Hero->SetActorLocation(QAHoldAt);Hero->GetCharacterMovement()->StopMovementImmediately();}}
 // Masks go on once the swimmers' heads are posed (the tread clip plays from the first frames).
 if(!bMasked && Time>1.2f)PutOnMasks();
 if(Frozen>0)Frozen-=DeltaSeconds;else UpdateSwimmers(DeltaSeconds);
 UpdateTargets();UpdateCoral(DeltaSeconds);UpdateLostAndCount(DeltaSeconds);
}

FString UMareSnorkelWorld::Status()const
{
 if(!IsActive())return FString();const auto D=Defs();const int32 Total=SpeciesList(D).Num();
 FString Goal;
 if(Lost>=0 && PC.IsValid() && PC->GetPawn() && SwimPos.IsValidIndex(Lost)){const FVector To=SwimPos[Lost]-PC->GetPawn()->GetActorLocation();
  const FVector Aim=PC->GetControlRotation().Vector().GetSafeNormal2D(),R(-Aim.Y,Aim.X,0);const float Ahead=FVector::DotProduct(To.GetSafeNormal2D(),Aim),Side=FVector::DotProduct(To.GetSafeNormal2D(),R);
  const TCHAR* Dir=Ahead>.7f?TEXT("à frente"):Ahead<-.7f?TEXT("atrás de você"):Side>0?TEXT("à direita"):TEXT("à esquerda");
  Goal=FString::Printf(TEXT("Falta um turista! Ele está a %.0f m, %s: vá buscar"),To.Size2D()/100.f,Dir);}
 else if(Seen>=int32(UMareSimulation::Number(D,TEXT("ok_species"),2)))Goal=Line(TEXT("count"));
 else Goal=Line(TEXT("start"));
 return FString::Printf(TEXT("Snorkel · espécies %d de %d · coral tocado %d · %s"),Seen,Total,CoralTouches,*Goal);
}

TArray<TPair<FVector,FString>> UMareSnorkelWorld::Bubbles()const
{
 TArray<TPair<FVector,FString>> Out;const float SeaZ=UMareSimulation::Number(Defs(),TEXT("sea_z"),-30);
 for(const auto& Pair:Says)if(Pair.Value.Value>Time && SwimPos.IsValidIndex(Pair.Key))Out.Add({FVector(SwimPos[Pair.Key].X,SwimPos[Pair.Key].Y,SeaZ+95),Pair.Value.Key});
 return Out;
}

FString UMareSnorkelWorld::QA(const FString& Cmd)
{
 auto Controller=PC.Get();auto Hero=Controller?Cast<ACharacter>(Controller->GetPawn()):nullptr;const auto D=Defs();
 auto Put=[&](const FVector& At,const FVector& Look){if(!Hero)return;Hero->SetActorLocation(At);Hero->GetCharacterMovement()->StopMovementImmediately();
  if(Controller && !Look.IsZero())Controller->SetControlRotation((Look-(At+FVector(0,0,60))).Rotation());};
 if(Cmd.StartsWith(TEXT("present:"))){Present(FCString::Atoi(*Cmd.Mid(8)));return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("aim:")) && Hero){TArray<FVector> Points;const int32 I=FCString::Atoi(*Cmd.Mid(4));if(!Candidates(I,Points))return TEXT("none");
  // The nearest school or coral to the ladder, seen from 2.6 m off at the surface.
  const FVector Ladder=Vec(D,TEXT("ladder"));Points.Sort([&](const FVector& A,const FVector& B){return FVector::DistSquared2D(A,Ladder)<FVector::DistSquared2D(B,Ladder);});
  // Neutral buoyancy while posing for the capture (restored when the tour ends).
  // Held in place for a few seconds while posing for the capture (the hero floats up otherwise).
  const FVector P=Points[0];const FVector From=FVector(P.X,P.Y+330,P.Z+230);Put(From,P);QAHold=6;QAHoldAt=From;
  return FString::Printf(TEXT("aim %.0f,%.0f,%.0f"),P.X,P.Y,P.Z);}
 if(Cmd==TEXT("lose")){if(Lost<0 && bLostDone)bLostDone=false;BeginLost();return FString::Printf(TEXT("lost=%d at %.0f,%.0f"),Lost,LostAt.X,LostAt.Y);}
 if(Cmd==TEXT("fetch") && Lost>=0){Put(SwimPos[Lost]+FVector(-250,0,-30),SwimPos[Lost]);return TEXT("ok");}
 if(Cmd==TEXT("touch") && Hero){const FVector H=Hero->GetActorLocation();UPrimitiveComponent* Best=nullptr;float L=FLT_MAX;
  for(const auto& C:Corals)if(C.IsValid()){const float X=FVector::DistSquared2D(C->Bounds.Origin,H);if(X<L){L=X;Best=C.Get();}}
  if(!Best)return TEXT("none");Put(Best->Bounds.Origin+FVector(0,0,Best->Bounds.BoxExtent.Z+10),FVector::ZeroVector);return TEXT("ok");}
 if(Cmd==TEXT("home")){const FVector L=Vec(D,TEXT("ladder"));Put(FVector(L.X,L.Y+120,-60),FVector(L.X,L.Y-400,0));return TEXT("ok");}
 if(Cmd==TEXT("group") && Hero){const FVector H=Hero->GetActorLocation();FVector F=Controller->GetControlRotation().Vector().GetSafeNormal2D();const FVector R(-F.Y,F.X,0);
  for(int32 I=0;I<SwimPos.Num();++I)if(I!=Lost){SwimPos[I]=H+F*(260+90*(I/3))+R*((I%3)-1)*110.f;SwimPos[I].Z=UMareSimulation::Number(D,TEXT("sea_z"),-30);}return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("freeze:"))){Frozen=FCString::Atof(*Cmd.Mid(7));return TEXT("ok");}
 if(Cmd==TEXT("finish")){Finish();return TEXT("ok");}
 int32 Masked=0;for(auto& M:Masks)Masked+=IsValid(M);int32 Valid=0;for(auto& T:Targets)Valid+=IsValid(T) && T->GetActorLocation().Z>-50000;
 return FString::Printf(TEXT("active=%d seen=%d coral=%d lost=%d lostdone=%d crew=%d swimmers=%d masks=%d targets_in_range=%d corals=%d t=%.0f"),
  IsActive(),Seen,CoralTouches,Lost,bLostDone,bCrewFetched,Swimmers.Num(),Masked,Valid,Corals.Num(),Time);
}
