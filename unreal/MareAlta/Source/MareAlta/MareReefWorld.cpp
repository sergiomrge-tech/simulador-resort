#include "MareReefWorld.h"
#include "MareGame.h"
#include "Components/InstancedStaticMeshComponent.h"
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
 if(!bIndexed)IndexFish();Clock+=DeltaSeconds;if(Clock<.1f)return;Clock=0;
 auto Pawn=UGameplayStatics::GetPlayerPawn(World,0);if(!Pawn)return;
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

FVector UMareReefWorld::SamplePosition() const
{
 if(Fish.IsEmpty() || !Fish[0].Body.IsValid())return FVector::ZeroVector;FTransform T;return Fish[0].Body->GetInstanceTransform(Fish[0].Index,T,true)?T.GetLocation():FVector::ZeroVector;
}
bool UMareReefWorld::AllFishUnderwater() const
{
 if(Fish.IsEmpty())return false;for(const auto& Row:Fish)for(auto Component:{Row.Body.Get(),Row.Tail.Get()}){
  if(!Component || !Component->GetStaticMesh())return false;FTransform Transform;if(!Component->GetInstanceTransform(Row.Index,Transform,true))return false;
  if(Component->GetStaticMesh()->GetBoundingBox().TransformBy(Transform.ToMatrixWithScale()).Max.Z>-60.f)return false;
 }return true;
}
