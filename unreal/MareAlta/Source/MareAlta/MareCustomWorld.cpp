#include "MareCustomWorld.h"
#include "MareSimulation.h"
#include "MareGame.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

TStatId UMareCustomWorld::GetStatId()const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareCustomWorld,STATGROUP_Tickables);}
UMareSimulation* UMareCustomWorld::Sim()const{return GetWorld() && GetWorld()->GetGameInstance()?GetWorld()->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
void UMareCustomWorld::Deinitialize(){Slots.Empty();Super::Deinitialize();}

UStaticMesh* UMareCustomWorld::PartMesh(const FString& Slug)const
{
 // Data/custom_assets.json maps a Poly Haven / Fab slug to its imported asset (tools: mare_custom.py).
 const FString Path=UMareSimulation::String(Assets,Slug);
 return Path.IsEmpty()?nullptr:LoadObject<UStaticMesh>(nullptr,*Path);
}

void UMareCustomWorld::Index()
{
 auto S=Sim();if(!S)return;
 FString Text;Assets=MakeShared<FJsonObject>();
 if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/custom_assets.json"))))FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Assets);
 if(!Assets.IsValid())Assets=MakeShared<FJsonObject>();
 Holder=GetWorld()->SpawnActor<AActor>();
 Holder->SetRootComponent(NewObject<USceneComponent>(Holder,TEXT("CustomRoot")));Holder->GetRootComponent()->RegisterComponent();
 auto Places=UMareSimulation::Object(S->CustomDefs(),TEXT("places"));
 for(const auto& PlacePair:Places->Values){const FString Place(PlacePair.Key.ToView());auto PlaceDef=PlacePair.Value->AsObject();
  const TArray<TSharedPtr<FJsonValue>>* Area=nullptr;FBox2D Box(FVector2D(-1e9),FVector2D(1e9));
  if(PlaceDef->TryGetArrayField(TEXT("area"),Area) && Area->Num()==4)Box=FBox2D(FVector2D((*Area)[0]->AsNumber(),(*Area)[2]->AsNumber()),FVector2D((*Area)[1]->AsNumber(),(*Area)[3]->AsNumber()));
  const TArray<TSharedPtr<FJsonValue>>* Defs=nullptr;if(!PlaceDef->TryGetArrayField(TEXT("slots"),Defs))continue;
  for(const auto& Value:*Defs){auto Def=Value->AsObject();FSlotState& State=Slots.Add(Key(Place,UMareSimulation::String(Def,TEXT("id"))));
   TArray<FString> AnchorMeshes;if(Def->HasField(TEXT("anchor")))AnchorMeshes.Add(UMareSimulation::String(Def,TEXT("anchor")));
   const TArray<TSharedPtr<FJsonValue>>* Also=nullptr;if(Def->TryGetArrayField(TEXT("also"),Also))for(const auto& A:*Also)AnchorMeshes.Add(A->AsString());
   TArray<FString> HideMeshes;const TArray<TSharedPtr<FJsonValue>>* Hide=nullptr;if(Def->TryGetArrayField(TEXT("hide"),Hide))for(const auto& H:*Hide)HideMeshes.Add(H->AsString());
   const bool bMaterialSlot=[&](){const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;if(!Def->TryGetArrayField(TEXT("tiers"),Tiers))return false;
    for(const auto& T:*Tiers)if(T->AsObject()->HasField(TEXT("material")))return true;return false;}();
   for(TActorIterator<AActor> It(GetWorld());It;++It){if(*It==Holder)continue;TArray<UInstancedStaticMeshComponent*> Parts;It->GetComponents(Parts);
    for(auto Part:Parts){if(!Part->GetStaticMesh())continue;const FString Mesh=Part->GetStaticMesh()->GetName();
     const bool bAnchor=AnchorMeshes.Contains(Mesh),bHide=HideMeshes.Contains(Mesh);if(!bAnchor && !bHide)continue;
     bool bInside=false;
     for(int32 I=0;I<Part->GetInstanceCount();++I){FTransform T;Part->GetInstanceTransform(I,T,true);
      if(!Box.IsInside(FVector2D(T.GetLocation())))continue;bInside=true;
      if(bAnchor && !bMaterialSlot){State.Anchors.Add(T);State.AnchorActor=*It;}
      if(bHide)State.HideTargets.Add({Part,I,T});}
     // Material tiers recolour the whole component: only when it lives entirely inside the place.
     if(bAnchor && bMaterialSlot && bInside){bool bAll=true;for(int32 I=0;I<Part->GetInstanceCount();++I){FTransform T;Part->GetInstanceTransform(I,T,true);bAll&=Box.IsInside(FVector2D(T.GetLocation()));}
      if(bAll){State.MaterialTargets.Add(Part);State.AnchorActor=*It;auto& Saved=State.Originals.Add(Part);for(int32 M=0;M<Part->GetNumMaterials();++M)Saved.Add(Part->GetMaterial(M));}
      else UE_LOG(LogTemp,Warning,TEXT("MARE_CUSTOM %s/%s: %s is shared outside the place, not recoloured"),*Place,*UMareSimulation::String(Def,TEXT("id")),*Mesh);}
    }
   }
   // Free spots (plants): ground-traced points with a fixed, varied heading.
   const TArray<TSharedPtr<FJsonValue>>* Spots=nullptr;
   if(Def->TryGetArrayField(TEXT("spots"),Spots))for(int32 I=0;I<Spots->Num();++I){const auto& P=(*Spots)[I]->AsArray();if(P.Num()<2)continue;
    const FVector Top(P[0]->AsNumber(),P[1]->AsNumber(),3000);FHitResult Hit;FCollisionQueryParams Query(TEXT("MareCustomSpot"),true);
    const float Z=GetWorld()->LineTraceSingleByChannel(Hit,Top,Top-FVector(0,0,6000),ECC_Visibility,Query)?Hit.ImpactPoint.Z:0.f;
    State.Anchors.Add(FTransform(FRotator(0,37.f*I,0),FVector(Top.X,Top.Y,Z)));}
   UE_LOG(LogTemp,Display,TEXT("MARE_CUSTOM %s/%s anchors=%d hide=%d materials=%d"),*Place,*UMareSimulation::String(Def,TEXT("id")),State.Anchors.Num(),State.HideTargets.Num(),State.MaterialTargets.Num());
  }
 }
 bIndexed=true;
}

void UMareCustomWorld::Apply(const FString& Place,const FString& Slot,int32 Tier,bool bPreviewTier)
{
 auto S=Sim();FSlotState* State=Slots.Find(Key(Place,Slot));auto Def=S?S->CustomSlot(Place,Slot):nullptr;if(!State || !Def.IsValid())return;
 if(bPreviewTier)bPreview=true;
 const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;if(!Def->TryGetArrayField(TEXT("tiers"),Tiers) || !Tiers->IsValidIndex(Tier-1))return;
 auto TierDef=(*Tiers)[Tier-1]->AsObject();
 for(auto Part:State->Parts)if(Part.IsValid())Part->DestroyComponent();State->Parts.Empty();
 // Materials: tier material when present, otherwise the original look.
 const FString MaterialName=UMareSimulation::String(TierDef,TEXT("material"));
 UMaterialInterface* Material=MaterialName.IsEmpty()?nullptr:LoadObject<UMaterialInterface>(nullptr,*FString::Printf(TEXT("/Game/Custom/Materials/%s.%s"),*MaterialName,*MaterialName));
 if(Material)KeepMaterials.AddUnique(Material);
 for(const auto& Target:State->MaterialTargets)if(auto Component=Target.Get()){const auto* Saved=State->Originals.Find(Target);
  for(int32 M=0;M<Component->GetNumMaterials();++M)Component->SetMaterial(M,Material?Material:(Saved && Saved->IsValidIndex(M)?(*Saved)[M].Get():nullptr));}
 // Meshes: build every part; if a tier asset is missing keep the original furniture visible.
 const TArray<TSharedPtr<FJsonValue>>* PartDefs=nullptr;TierDef->TryGetArrayField(TEXT("parts"),PartDefs);
 const int32 Count=TierDef->HasField(TEXT("count"))?FMath::Min(int32(UMareSimulation::Number(TierDef,TEXT("count"))),State->Anchors.Num()):State->Anchors.Num();
 bool bBuilt=false;
 if(PartDefs && Count>0)for(const auto& PartValue:*PartDefs){auto PartDef=PartValue->AsObject();UStaticMesh* Mesh=PartMesh(UMareSimulation::String(PartDef,TEXT("model")));
  if(!Mesh){UE_LOG(LogTemp,Warning,TEXT("MARE_CUSTOM missing asset %s"),*UMareSimulation::String(PartDef,TEXT("model")));continue;}
  // Fit: height h (cm), optional footprint w; bottom-centre of the mesh lands on the local point 'at'.
  const FBoxSphereBounds B=Mesh->GetBounds();const double Height=FMath::Max(1.,B.BoxExtent.Z*2),Width=FMath::Max(1.,2*FMath::Max(B.BoxExtent.X,B.BoxExtent.Y));
  const double Sz=UMareSimulation::Number(PartDef,TEXT("h"),Height)/Height;const double Sxy=PartDef->HasField(TEXT("w"))?UMareSimulation::Number(PartDef,TEXT("w"))/Width:Sz;
  const TArray<TSharedPtr<FJsonValue>>* At=nullptr;FVector Local(0);if(PartDef->TryGetArrayField(TEXT("at"),At) && At->Num()==3)Local=FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());
  const FRotator Yaw(0,UMareSimulation::Number(PartDef,TEXT("yaw")),0);
  const FVector Centre=FVector(B.Origin.X,B.Origin.Y,B.Origin.Z-B.BoxExtent.Z)*FVector(Sxy,Sxy,Sz);
  const FTransform Fit=FTransform(FRotator::ZeroRotator,-Centre,FVector(Sxy,Sxy,Sz))*FTransform(Yaw,Local);
  auto Component=NewObject<UHierarchicalInstancedStaticMeshComponent>(Holder);Component->SetupAttachment(Holder->GetRootComponent());Component->SetStaticMesh(Mesh);
  Component->SetMobility(EComponentMobility::Movable);Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Component->RegisterComponent();
  for(int32 I=0;I<Count;++I)Component->AddInstance(Fit*FTransform(State->Anchors[I].GetRotation(),State->Anchors[I].GetLocation()),true);
  State->Parts.Add(Component);bBuilt=true;}
 // Original instances step aside (epsilon scale keeps their bounds valid) only when a replacement exists.
 const bool bReplace=bBuilt && State->HideTargets.Num()>0;
 for(const auto& Hidden:State->HideTargets)if(auto Component=Hidden.Component.Get()){
  FTransform T=Hidden.Original;if(bReplace)T.SetScale3D(FVector(.001));Component->UpdateInstanceTransform(Hidden.Index,T,true,true,true);}
 State->Shown=Tier;
}

void UMareCustomWorld::ApplyAll()
{
 auto S=Sim();if(!S)return;bPreview=false;
 auto Places=UMareSimulation::Object(S->CustomDefs(),TEXT("places"));
 for(const auto& PlacePair:Places->Values){const FString Place(PlacePair.Key.ToView());const TArray<TSharedPtr<FJsonValue>>* Defs=nullptr;
  if(PlacePair.Value->AsObject()->TryGetArrayField(TEXT("slots"),Defs))for(const auto& V:*Defs){const FString Slot=UMareSimulation::String(V->AsObject(),TEXT("id"));Apply(Place,Slot,S->CustomTier(Place,Slot));}}
}

int32 UMareCustomWorld::PartInstances(const FString& Place,const FString& Slot)const
{
 int32 Total=0;if(const FSlotState* State=Slots.Find(Key(Place,Slot)))for(const auto& Part:State->Parts)if(Part.IsValid())Total+=Part->GetInstanceCount();return Total;
}
bool UMareCustomWorld::HasVisual(const FString& Place,const FString& Slot,int32 Tier)const
{
 auto S=Sim();auto Def=S?S->CustomSlot(Place,Slot):nullptr;const TArray<TSharedPtr<FJsonValue>>* Tiers=nullptr;
 if(!Def.IsValid() || !Def->TryGetArrayField(TEXT("tiers"),Tiers) || !Tiers->IsValidIndex(Tier-1))return false;
 auto TierDef=(*Tiers)[Tier-1]->AsObject();const FString Material=UMareSimulation::String(TierDef,TEXT("material"));
 if(!Material.IsEmpty())return LoadObject<UMaterialInterface>(nullptr,*FString::Printf(TEXT("/Game/Custom/Materials/%s.%s"),*Material,*Material))!=nullptr;
 const TArray<TSharedPtr<FJsonValue>>* PartDefs=nullptr;if(!TierDef->TryGetArrayField(TEXT("parts"),PartDefs))return Tier==1;
 for(const auto& P:*PartDefs)if(!PartMesh(UMareSimulation::String(P->AsObject(),TEXT("model"))))return false;return true;
}

void UMareCustomWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld()->IsGameWorld() || !Cast<AMareGameMode>(GetWorld()->GetAuthGameMode()))return;
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=1.f;
 if(!bIndexed){Index();ApplyAll();}
 // Replacement furniture follows region visibility (kiosk tables appear only once bought).
 for(auto& Pair:Slots){const bool bHidden=Pair.Value.AnchorActor.IsValid() && Pair.Value.AnchorActor->IsHidden();
  for(const auto& Part:Pair.Value.Parts)if(Part.IsValid() && Part->IsVisible()==bHidden){Part->SetVisibility(!bHidden);Part->SetCollisionEnabled(bHidden?ECollisionEnabled::NoCollision:ECollisionEnabled::QueryAndPhysics);}}
}
