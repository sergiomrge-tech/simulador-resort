#include "MareReefWorld.h"
#include "MareIsland.h"
#include "MareGame.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "MareSimulation.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

TStatId UMareReefWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareReefWorld,STATGROUP_Tickables);}
void UMareReefWorld::IndexFish()
{
 bIndexed=true;TMap<FString,UInstancedStaticMeshComponent*> Groups;
 const TArray<FString> Names={TEXT("World_0544"),TEXT("World_0545"),TEXT("World_0546"),TEXT("World_0547"),TEXT("World_0555"),TEXT("World_0556"),TEXT("World_0564"),TEXT("World_0565")};
 for(TActorIterator<AActor> It(GetWorld());It;++It){TArray<UInstancedStaticMeshComponent*> Components;It->GetComponents(Components);
  for(auto C:Components)if(C && C->GetStaticMesh() && Names.Contains(C->GetStaticMesh()->GetName()))Groups.Add(C->GetStaticMesh()->GetName(),C);
 }
 for(int32 G=0;G<Names.Num();G+=2){auto Body=Groups.FindRef(Names[G]);auto Tail=Groups.FindRef(Names[G+1]);
  if(!Body || !Tail || Body->GetInstanceCount()!=Tail->GetInstanceCount())continue;
  Body->SetMobility(EComponentMobility::Movable);Tail->SetMobility(EComponentMobility::Movable);
  Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);Tail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  for(int32 I=0;I<Body->GetInstanceCount();++I){FMareReefFish Row;Row.Body=Body;Row.Tail=Tail;Row.Index=I;
   if(!Body->GetInstanceTransform(I,Row.BodyTransform,true) || !Tail->GetInstanceTransform(I,Row.TailTransform,true))continue;
   const FVector Original=Row.BodyTransform.GetLocation();
   const float Offshore=FMath::Max(0.f,-Original.Y*.01f-24.f);
   const float Floor=-100.f*(.5f*FMath::Clamp(Offshore/14.f,0.f,1.f)+FMath::Max(0.f,Offshore-14.f)*.09f);
   const float Depth=FMath::Min(-82.f,FMath::Max(Floor+18.f,Original.Z));
   Row.TailOffset=(Row.TailTransform.GetLocation()-Original)*.22f;
   Row.BodyTransform.SetLocation(FVector(Original.X,Original.Y,Depth));
   Row.BodyTransform.SetScale3D(Row.BodyTransform.GetScale3D()*.22f);Row.TailTransform.SetScale3D(Row.TailTransform.GetScale3D()*.22f);
   Row.Seed=I*1.731f+G*3.1f;Fish.Add(Row);
   Row.TailTransform.SetLocation(Row.BodyTransform.GetLocation()+Row.TailOffset);
   Body->UpdateInstanceTransform(I,Row.BodyTransform,true,false,true);Tail->UpdateInstanceTransform(I,Row.TailTransform,true,false,true);
  }
  Body->MarkRenderStateDirty();Tail->MarkRenderStateDirty();
 }
 UE_LOG(LogTemp,Display,TEXT("Maré reef: %d fish pairs placed below the surface"),Fish.Num());
}
void UMareReefWorld::Tick(float DeltaSeconds)
{
 auto World=GetWorld();if(!World || !World->IsGameWorld() || !Cast<AMareGameMode>(World->GetAuthGameMode()))return;
 if(!bIndexed){IndexFish();Dress();}
 auto Pawn=UGameplayStatics::GetPlayerPawn(World,0);if(!Pawn)return;
 if(HoldTime>0 && Watch>=0 && SharkMesh && Watch<SharkMesh->GetInstanceCount()){FTransform T;SharkMesh->GetInstanceTransform(Watch,T,true);
  const FVector Side=T.GetRotation().RotateVector(FVector(1,0,0));HoldAt=T.GetLocation()+Side*380+FVector(0,0,40);HoldView=(T.GetLocation()-(HoldAt+FVector(0,0,60))).Rotation();}
 if(HoldTime<=0)Watch=-1;
 if(HoldTime>0){HoldTime-=DeltaSeconds;Pawn->SetActorLocation(HoldAt);if(auto C=Cast<ACharacter>(Pawn))C->GetCharacterMovement()->StopMovementImmediately();
  if(auto PC=Cast<APlayerController>(Pawn->GetController()))PC->SetControlRotation(HoldView);}
 UpdateSharks(DeltaSeconds,Pawn->GetActorLocation());
 Clock+=DeltaSeconds;if(Clock<.1f)return;Clock=0;
 const double Time=World->GetTimeSeconds();TSet<UInstancedStaticMeshComponent*> Changed;
 for(const auto& Row:Fish){auto Body=Row.Body.Get();auto Tail=Row.Tail.Get();if(!Body || !Tail)continue;
  const FVector Base=Row.BodyTransform.GetLocation();if(FVector::DistSquared2D(Base,Pawn->GetActorLocation())>FMath::Square(2400.f))continue;
  const float Phase=float(Time)*.8f+Row.Seed;const float Yaw=FMath::Sin(Phase)*4.f;
  const FVector Drift(FMath::Sin(Phase)*12.f,FMath::Cos(Phase*.8f)*8.f,FMath::Sin(Phase*.7f)*3.f);
  FTransform B=Row.BodyTransform;B.SetLocation(Base+Drift);B.SetRotation(FQuat(FVector::UpVector,FMath::DegreesToRadians(Yaw))*B.GetRotation());
  FTransform T=Row.TailTransform;T.SetLocation(Base+Drift+FRotator(0,Yaw,0).RotateVector(Row.TailOffset));T.SetRotation(FQuat(FVector::UpVector,FMath::DegreesToRadians(Yaw+FMath::Sin(float(Time)*8.f+Row.Seed)*18.f))*T.GetRotation());
  Body->UpdateInstanceTransform(Row.Index,B,true,false,true);Tail->UpdateInstanceTransform(Row.Index,T,true,false,true);Changed.Add(Body);Changed.Add(Tail);
 }
 for(auto Component:Changed)Component->MarkRenderStateDirty();
}

namespace
{
 TSharedPtr<FJsonObject> ReefDefs()
 {
  static TSharedPtr<FJsonObject> Defs;
  if(!Defs.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/reef.json")));
   FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Defs);if(!Defs.IsValid())Defs=MakeShared<FJsonObject>();}
  return Defs;
 }
 FVector2D Pair(const TSharedPtr<FJsonObject>& O,const FString& Key,const FVector2D& Default)
 {
  const TArray<TSharedPtr<FJsonValue>>* A=nullptr;return O.IsValid() && O->TryGetArrayField(Key,A) && A->Num()>=2?FVector2D((*A)[0]->AsNumber(),(*A)[1]->AsNumber()):Default;
 }
 // Models whose front is Blender +Y arrive facing UE -Y: this turns that front to F.
 FRotator FaceAlong(const FVector& F){return FRotationMatrix::MakeFromYZ(-F.GetSafeNormal(),FVector::UpVector).Rotator();}
}

void UMareReefWorld::Dress()
{
 // GPU first: one hierarchical instanced mesh per kind, static once placed, culled past a few tens of metres (the
 // reef is ~9 m down: nothing of it shows from the beach).
 const auto D=ReefDefs();UWorld* World=GetWorld();if(!World)return;
 FActorSpawnParameters P;P.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 Dressing=World->SpawnActor<AActor>(FVector::ZeroVector,FRotator::ZeroRotator,P);if(!Dressing)return;
 Dressing->SetRootComponent(NewObject<USceneComponent>(Dressing,TEXT("Root")));Dressing->GetRootComponent()->RegisterComponent();
 FRandomStream R(int32(UMareSimulation::Number(D,TEXT("seed"),5150)));
 const float Floor=UMareSimulation::Number(D,TEXT("floor_below"),-860),Cull=UMareSimulation::Number(D,TEXT("cull_cm"),6500);
 TArray<FVector2D> Clusters;const TArray<TSharedPtr<FJsonValue>>* CL=nullptr;
 if(D->TryGetArrayField(TEXT("clusters"),CL))for(const auto& V:*CL){const auto& A=V->AsArray();if(A.Num()>=2)Clusters.Add(FVector2D(A[0]->AsNumber(),A[1]->AsNumber()));}
 const FVector2D Spread=Pair(D,TEXT("spread"),FVector2D(700,420));
 const TArray<TSharedPtr<FJsonValue>>* StripA=nullptr;FBox2D Strip(FVector2D(1000,-13750),FVector2D(10600,-12850));
 if(D->TryGetArrayField(TEXT("strip"),StripA) && StripA->Num()==4)Strip=FBox2D(FVector2D((*StripA)[0]->AsNumber(),(*StripA)[1]->AsNumber()),FVector2D((*StripA)[2]->AsNumber(),(*StripA)[3]->AsNumber()));
 auto Make=[&](UStaticMesh* Mesh,bool bShadow,bool bTree)->UInstancedStaticMeshComponent*{
  UInstancedStaticMeshComponent* C=bTree?NewObject<UHierarchicalInstancedStaticMeshComponent>(Dressing):NewObject<UInstancedStaticMeshComponent>(Dressing);
  C->SetMobility(EComponentMobility::Movable);C->SetStaticMesh(Mesh);C->SetCollisionEnabled(ECollisionEnabled::NoCollision);C->SetCastShadow(bShadow);
  C->SetCullDistances(int32(Cull*.85f),int32(Cull));C->SetupAttachment(Dressing->GetRootComponent());C->RegisterComponent();Dressing->AddInstanceComponent(C);Parts.Add(C);return C;};
 TArray<FVector> Taken;   // x, y, radius of the bigger pieces already placed
 int32 Placed=0,Missing=0;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(D->TryGetArrayField(TEXT("dressing"),List))for(const auto& V:*List){const auto E=V->AsObject();
  auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(E,TEXT("mesh")));if(!Mesh){++Missing;UE_LOG(LogTemp,Warning,TEXT("REEF_MISSING %s"),*UMareSimulation::String(E,TEXT("mesh")));continue;}
  bool bShadow=false;E->TryGetBoolField(TEXT("shadow"),bShadow);auto C=Make(Mesh,bShadow,true);
  const FVector2D Scale=Pair(E,TEXT("scale"),FVector2D(1,1));const float Sink=UMareSimulation::Number(E,TEXT("sink")),Tilt=UMareSimulation::Number(E,TEXT("tilt")),Clear=UMareSimulation::Number(E,TEXT("clear"),30);
  const int32 Groups=int32(UMareSimulation::Number(E,TEXT("groups"),0));
  // Where each piece goes: around every cluster, plus extras over the whole strip; grouped kinds grow in patches.
  TArray<FVector2D> Wanted;
  auto Around=[&](const FVector2D& C0,const FVector2D& S){return C0+FVector2D(R.FRandRange(-S.X,S.X),R.FRandRange(-S.Y,S.Y));};
  for(const auto& C0:Clusters)for(int32 I=0;I<int32(UMareSimulation::Number(E,TEXT("count"),1));++I)Wanted.Add(Around(C0,Spread));
  const int32 Extra=int32(UMareSimulation::Number(E,TEXT("extra"),0));
  TArray<FVector2D> Patch;for(int32 G=0;G<Groups;++G)Patch.Add(FVector2D(R.FRandRange(Strip.Min.X,Strip.Max.X),R.FRandRange(Strip.Min.Y,Strip.Max.Y)));
  for(int32 I=0;I<Extra;++I)Wanted.Add(Patch.Num()?Around(Patch[I%Patch.Num()],FVector2D(160,160)):FVector2D(R.FRandRange(Strip.Min.X,Strip.Max.X),R.FRandRange(Strip.Min.Y,Strip.Max.Y)));
  for(FVector2D W:Wanted){
   for(int32 Try=0;Try<6;++Try){if(Try)W+=FVector2D(R.FRandRange(-150,150),R.FRandRange(-150,150));
    bool bFree=true;if(Clear>=35)for(const FVector& T:Taken)if(FVector2D::Distance(FVector2D(T.X,T.Y),W)<T.Z+Clear*.8f){bFree=false;break;}
    if(!bFree)continue;
    // Dropped from above: it must reach the sand (no coral underneath, nothing in the way).
    FHitResult Hit;FCollisionQueryParams Q(TEXT("MareReefDress"),false);
    if(!World->SweepSingleByChannel(Hit,FVector(W.X,W.Y,-300),FVector(W.X,W.Y,-1600),FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(Clear),Q))continue;
    if(Hit.ImpactPoint.Z>Floor)continue;
    const float S=R.FRandRange(Scale.X,Scale.Y);
    const FRotator Rot(R.FRandRange(-Tilt,Tilt),R.FRandRange(0.f,360.f),R.FRandRange(-Tilt,Tilt));
    C->AddInstance(FTransform(Rot,FVector(W.X,W.Y,Hit.ImpactPoint.Z-Sink*S),FVector(S)),true);++Placed;
    if(Clear>=35)Taken.Add(FVector(W.X,W.Y,Clear*S));break;}}
 }
 FillFloor(R,Strip);
 // Sharks: plain instances (moved every frame, no tree rebuild), one per listed cluster.
 const auto SD=UMareSimulation::Object(D,TEXT("sharks"));
 if(auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(SD,TEXT("mesh")))){SharkMesh=Make(Mesh,true,false);SharkMesh->SetCullDistances(0,int32(Cull*1.3f));
  const TArray<TSharedPtr<FJsonValue>>* Which=nullptr;SD->TryGetArrayField(TEXT("clusters"),Which);
  const FVector2D Rad=Pair(SD,TEXT("radius"),FVector2D(700,1100)),Dep=Pair(SD,TEXT("depth"),FVector2D(-720,-600));
  if(Which)for(const auto& V:*Which){const int32 I=int32(V->AsNumber());if(!Clusters.IsValidIndex(I))continue;FMareShark S;
   S.Centre=FVector(Clusters[I].X,Clusters[I].Y,0);S.Radius=R.FRandRange(Rad.X,Rad.Y);S.Depth=R.FRandRange(Dep.X,Dep.Y);S.Angle=R.FRandRange(0.f,2*PI);S.Dir=R.FRand()<.5f?-1.f:1.f;S.Seed=R.FRand()*10;
   Sharks.Add(S);SharkMesh->AddInstance(FTransform(FVector(S.Centre.X+S.Radius,S.Centre.Y,S.Depth)),true);}}
 else ++Missing;
 UE_LOG(LogTemp,Display,TEXT("Maré reef: %d seafloor pieces, %d sharks, %d missing meshes"),Placed,Sharks.Num(),Missing);
}

float UMareReefWorld::SeabedZ(float Y,float* Slope)
{
 // Piecewise linear along y (the beach runs along x); beyond the last point the floor stays flat.
 const TArray<TSharedPtr<FJsonValue>>* L=nullptr;TArray<FVector2D> Pts;
 if(UMareSimulation::Object(ReefDefs(),TEXT("floor_fill"))->TryGetArrayField(TEXT("profile"),L))for(const auto& V:*L){const auto& A=V->AsArray();if(A.Num()>=2)Pts.Add(FVector2D(A[0]->AsNumber(),A[1]->AsNumber()));}
 if(Slope)*Slope=0;if(Pts.IsEmpty())return -900;if(Y>=Pts[0].X)return Pts[0].Y;
 for(int32 I=1;I<Pts.Num();++I)if(Y>=Pts[I].X){const float A=(Y-Pts[I-1].X)/(Pts[I].X-Pts[I-1].X);if(Slope)*Slope=(Pts[I].Y-Pts[I-1].Y)/(Pts[I].X-Pts[I-1].X);return FMath::Lerp(Pts[I-1].Y,Pts[I].Y,A);}
 return Pts.Last().Y;
}

float UMareReefWorld::SeabedZ(float X,float Y,FVector* Normal)
{
 auto At=[](float PX,float PY){
  const float D=MareIsland::ShoreDistance(PX,PY);
  const float Near=SeabedZ(MareIsland::BayEquivalentY(2500.f));   // the profile at 25 m out
  if(D<2500.f)return FMath::Lerp(-30.f,Near,FMath::Clamp(D/2500.f,0.f,1.f));
  return SeabedZ(MareIsland::BayEquivalentY(D));};
 const float Z=At(X,Y);
 if(Normal){const float Dx=At(X+200.f,Y)-At(X-200.f,Y),Dy=At(X,Y+200.f)-At(X,Y-200.f);*Normal=FVector(-Dx/400.f,-Dy/400.f,1.f).GetSafeNormal();}
 return Z;
}

void UMareReefWorld::FillFloor(FRandomStream& R,const FBox2D& Reef)
{
 // 05/11 (Sergio: "faça um gerador com rochas, corais e algas marinhas, preencha todo fundo"): the whole sea floor,
 // from the shallows in front of the beach down the slope to the deep floor, gets rocks, corals and algae by depth
 // (reef.json floor_fill.kinds: density per 100 m2 inside a floor height range, patchy where 'patch' is set). Cell by
 // cell over the area; the shallows (still the beach terrain) are found by a trace, the rest follows the profile.
 // GPU: one HISM per kind built in one batch, culled by distance; no collision (swimming is unaffected).
 const auto F=UMareSimulation::Object(ReefDefs(),TEXT("floor_fill"));UWorld* World=GetWorld();if(!World || !F->HasField(TEXT("kinds")))return;
 const FVector2D XR=Pair(F,TEXT("x"),FVector2D(-19500,27500)),YR=Pair(F,TEXT("y"),FVector2D(-3300,-40000));
 const float Cell=UMareSimulation::Number(F,TEXT("cell"),500),ReefPad=UMareSimulation::Number(F,TEXT("reef_pad"),300);
 const FBox2D Skip(Reef.Min-FVector2D(ReefPad),Reef.Max+FVector2D(ReefPad));
 struct FKindRow{UHierarchicalInstancedStaticMeshComponent* C;float Dens,ZLo,ZHi,SLo,SHi,Sink,Tilt,Align,Patch,Cut,Seed;TArray<FTransform> Out;};
 TArray<FKindRow> Kinds;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;F->TryGetArrayField(TEXT("kinds"),List);
 for(const auto& V:*List){const auto E=V->AsObject();auto Mesh=LoadObject<UStaticMesh>(nullptr,*UMareSimulation::String(E,TEXT("mesh")));
  if(!Mesh){UE_LOG(LogTemp,Warning,TEXT("REEF_MISSING %s"),*UMareSimulation::String(E,TEXT("mesh")));continue;}
  auto C=NewObject<UHierarchicalInstancedStaticMeshComponent>(Dressing);C->SetMobility(EComponentMobility::Movable);C->SetStaticMesh(Mesh);
  C->SetCollisionEnabled(ECollisionEnabled::NoCollision);bool bShadow=false;E->TryGetBoolField(TEXT("shadow"),bShadow);C->SetCastShadow(bShadow);
  const float Cull=UMareSimulation::Number(E,TEXT("cull"),6000);C->SetCullDistances(int32(Cull*.8f),int32(Cull));
  C->SetupAttachment(Dressing->GetRootComponent());C->RegisterComponent();Dressing->AddInstanceComponent(C);Parts.Add(C);
  const FVector2D Z=Pair(E,TEXT("depth"),FVector2D(-12000,-100)),S=Pair(E,TEXT("scale"),FVector2D(1,1));
  Kinds.Add({C,float(UMareSimulation::Number(E,TEXT("per_100m2"),1)),float(Z.X),float(Z.Y),float(S.X),float(S.Y),float(UMareSimulation::Number(E,TEXT("sink"))),
   float(UMareSimulation::Number(E,TEXT("tilt"))),float(UMareSimulation::Number(E,TEXT("align"),.5)),float(UMareSimulation::Number(E,TEXT("patch"))),
   float(UMareSimulation::Number(E,TEXT("patch_cut"),.5)),float(R.FRandRange(0.f,1000.f)),{}});}
 const float CellArea=Cell*Cell/1e6f;   // in units of 100 m2
 for(float Y=YR.X;Y>YR.Y;Y-=Cell)for(float X=XR.X;X<XR.Y;X+=Cell){
  // the full island (08/11): whole cells on land or past the deep floor are skipped; past 120 m from the coast the
  // floor (seen from far above, through deep water) thins out to a quarter (27.6k -> 252k instances at full density)
  const float CellShore=MareIsland::ShoreDistance(X+Cell*.5f,Y-Cell*.5f);
  if(CellShore<-Cell || CellShore>30000.f+Cell)continue;
  const float Thin=FMath::Lerp(1.f,.25f,FMath::SmoothStep(12000.f,27000.f,CellShore));
  for(auto& K:Kinds){
   float N=K.Dens*CellArea*Thin;
   if(K.Patch>0){const float Noise=.5f+.5f*FMath::PerlinNoise2D(FVector2D(X,Y)/K.Patch+FVector2D(K.Seed));N*=FMath::SmoothStep(K.Cut-.08f,K.Cut+.08f,Noise)*2.f;}
   const int32 Count=FMath::FloorToInt(N)+(R.FRand()<FMath::Frac(N)?1:0);
   for(int32 I=0;I<Count;++I){const FVector2D W(X+R.FRandRange(0.f,Cell),Y-R.FRandRange(0.f,Cell));if(Skip.IsInside(W))continue;
    float Z;FVector Normal=FVector::UpVector;
    // 08/11 (the full island): all round the island by the distance to the coast; near a modelled beach (the bay) its
    // real ground under the water, elsewhere the radial profile. Land and the far deep floor (> 300 m out) are skipped.
    const float Shore=MareIsland::ShoreDistance(W.X,W.Y);
    if(Shore<=0.f || Shore>30000.f)continue;
    FHitResult Hit;FCollisionQueryParams Q(TEXT("MareFloorFill"),false);
    if(Shore<2500.f && World->LineTraceSingleByChannel(Hit,FVector(W.X,W.Y,200),FVector(W.X,W.Y,-1500),ECC_WorldStatic,Q) && Hit.ImpactNormal.Z>=.8f && Hit.ImpactPoint.Z<-30.f){
     Z=Hit.ImpactPoint.Z;Normal=Hit.ImpactNormal;}
    else Z=SeabedZ(W.X,W.Y,&Normal);
    if(Z<K.ZLo || Z>K.ZHi)continue;
    const float Sc=R.FRandRange(K.SLo,K.SHi);
    const FQuat Lean=FQuat::Slerp(FQuat::Identity,FQuat::FindBetweenNormals(FVector::UpVector,Normal),K.Align);
    const FQuat Rot=Lean*FRotator(R.FRandRange(-K.Tilt,K.Tilt),R.FRandRange(0.f,360.f),R.FRandRange(-K.Tilt,K.Tilt)).Quaternion();
    K.Out.Add(FTransform(Rot,FVector(W.X,W.Y,Z-K.Sink*Sc),FVector(Sc)));}}}
 for(auto& K:Kinds){K.C->AddInstances(K.Out,false,true);FloorFilled+=K.Out.Num();}
 UE_LOG(LogTemp,Display,TEXT("MARE_FLOOR_FILL instances=%d kinds=%d"),FloorFilled,Kinds.Num());
}

void UMareReefWorld::UpdateSharks(float Dt,const FVector& Swimmer)
{
 // Each shark circles its cluster, rising and dipping a little; a swimmer close by makes it swing wider (reef
 // sharks keep their distance) and it comes back in slowly.
 if(!SharkMesh || Sharks.IsEmpty())return;SharkTime+=Dt;const auto SD=UMareSimulation::Object(ReefDefs(),TEXT("sharks"));
 const float Speed=UMareSimulation::Number(SD,TEXT("speed"),130),ShyDist=UMareSimulation::Number(SD,TEXT("shy"),350);
 for(int32 I=0;I<Sharks.Num();++I){FMareShark& S=Sharks[I];const float Rad=S.Radius+S.Shy;
  S.Angle+=S.Dir*Speed/FMath::Max(200.f,Rad)*Dt;
  const FVector Pos(S.Centre.X+FMath::Cos(S.Angle)*Rad,S.Centre.Y+FMath::Sin(S.Angle)*Rad,S.Depth+FMath::Sin(SharkTime*.31f+S.Seed)*45.f);
  const bool bNear=FVector::Dist(Pos,Swimmer)<ShyDist;S.Shy=FMath::FInterpTo(S.Shy,bNear?ShyDist*1.6f:0.f,Dt,bNear?1.2f:.15f);
  const FVector Fwd=FVector(-FMath::Sin(S.Angle)*S.Dir,FMath::Cos(S.Angle)*S.Dir,FMath::Cos(SharkTime*.31f+S.Seed)*.06f);
  FRotator Rot=FaceAlong(Fwd);Rot.Roll+=8.f*S.Dir;   // banking into the turn
  SharkMesh->UpdateInstanceTransform(I,FTransform(Rot,Pos),true,I==Sharks.Num()-1,true);}
}

TArray<FVector> UMareReefWorld::InstancePositions(const FString& MeshName) const
{
 TArray<FVector> Out;for(auto C:Parts)if(C && C->GetStaticMesh() && C->GetStaticMesh()->GetName()==MeshName)
  for(int32 I=0;I<C->GetInstanceCount();++I){FTransform T;if(C->GetInstanceTransform(I,T,true))Out.Add(T.GetLocation()+FVector(0,0,C->GetStaticMesh()->GetBounds().BoxExtent.Z*T.GetScale3D().Z));}
 return Out;
}

int32 UMareReefWorld::SeafloorCount() const
{
 int32 N=0;for(auto C:Parts)if(C && C!=SharkMesh)N+=C->GetInstanceCount();return N;
}

FString UMareReefWorld::QA(const FString& Cmd)
{
 if(Cmd==TEXT("state")){FString Out;for(auto C:Parts)if(C && C->GetStaticMesh())Out+=FString::Printf(TEXT("%s=%d "),*C->GetStaticMesh()->GetName(),C->GetInstanceCount());return Out;}
 if(Cmd==TEXT("sharks")){FString Out;if(SharkMesh)for(int32 I=0;I<SharkMesh->GetInstanceCount();++I){FTransform T;SharkMesh->GetInstanceTransform(I,T,true);
   Out+=FString::Printf(TEXT("%.0f,%.0f,%.0f;"),T.GetLocation().X,T.GetLocation().Y,T.GetLocation().Z);}return Out;}
 if(Cmd.StartsWith(TEXT("hold:"))){TArray<FString> P;Cmd.Mid(5).ParseIntoArray(P,TEXT(","));if(P.Num()<6)return TEXT("x,y,z,pitch,yaw,seconds");
  HoldAt=FVector(FCString::Atof(*P[0]),FCString::Atof(*P[1]),FCString::Atof(*P[2]));HoldView=FRotator(FCString::Atof(*P[3]),FCString::Atof(*P[4]),0);HoldTime=FCString::Atof(*P[5]);return TEXT("ok");}
 if(Cmd.StartsWith(TEXT("watch:"))){// keep the player beside shark i, looking at it, for a few seconds
  const int32 I=FCString::Atoi(*Cmd.Mid(6));if(!SharkMesh || I>=SharkMesh->GetInstanceCount())return TEXT("none");Watch=I;HoldTime=8;return TEXT("ok");}
 return TEXT("state | sharks | hold:x,y,z,pitch,yaw,s | watch:i");
}

FVector UMareReefWorld::SamplePosition() const
{
 if(Fish.IsEmpty() || !Fish[0].Body.IsValid())return FVector::ZeroVector;FTransform T;return Fish[0].Body->GetInstanceTransform(Fish[0].Index,T,true)?T.GetLocation():FVector::ZeroVector;
}
TArray<FVector> UMareReefWorld::FishPositions(const FString& BodyMesh) const
{
 TArray<FVector> Out;for(const auto& Row:Fish){auto Body=Row.Body.Get();FTransform T;
  if(Body && Body->GetStaticMesh() && Body->GetStaticMesh()->GetName()==BodyMesh && Body->GetInstanceTransform(Row.Index,T,true))Out.Add(T.GetLocation());}
 return Out;
}
bool UMareReefWorld::AllFishUnderwater() const
{
 if(Fish.IsEmpty())return false;for(const auto& Row:Fish)for(auto Component:{Row.Body.Get(),Row.Tail.Get()}){
  if(!Component || !Component->GetStaticMesh())return false;FTransform Transform;if(!Component->GetInstanceTransform(Row.Index,Transform,true))return false;
  if(Component->GetStaticMesh()->GetBoundingBox().TransformBy(Transform.ToMatrixWithScale()).Max.Z>-60.f)return false;
 }return true;
}
