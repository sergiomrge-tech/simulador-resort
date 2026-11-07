// The Grand Hotel event on the beach (CHECKLIST_EXPANSOES 5.2): ghost plan, set-up with E, seated guests.
#include "MareHotelEventsWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "MareAudioWorld.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInterface.h"
#include "MaterialShared.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 UMareSimulation* EvSim(const UWorld* W){return W && W->GetGameInstance()?W->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 FString AssetPath(const FString& Model)
 {
  static TSharedPtr<FJsonObject> Assets;
  if(!Assets.IsValid()){FString Text;FFileHelper::LoadFileToString(Text,*(FPaths::ProjectContentDir()/TEXT("Data/custom_assets.json")));
   FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Assets);if(!Assets.IsValid())Assets=MakeShared<FJsonObject>();}
  return UMareSimulation::String(Assets,Model);
 }
 TArray<TSharedPtr<FJsonObject>> Objects(const TSharedPtr<FJsonObject>& O,const FString& Key)
 {
  TArray<TSharedPtr<FJsonObject>> Out;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;if(O.IsValid() && O->TryGetArrayField(Key,L))for(const auto& V:*L)Out.Add(V->AsObject());return Out;
 }
 bool Flag(const TSharedPtr<FJsonObject>& B,bool bExtra,int32 I)
 {
  const TArray<TSharedPtr<FJsonValue>>* L=nullptr;return B->TryGetArrayField(bExtra?TEXT("extras"):TEXT("placed"),L) && L->IsValidIndex(I) && (*L)[I]->AsBool();
 }
}

TStatId UMareHotelEventsWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareHotelEventsWorld,STATGROUP_Tickables);}
void UMareHotelEventsWorld::Deinitialize(){Clear();Super::Deinitialize();}

void UMareHotelEventsWorld::Clear()
{
 for(auto& A:Actors)if(IsValid(A))A->Destroy();for(auto& T:Targets)if(IsValid(T))T->Destroy();for(auto& G:Guests)if(IsValid(G))G->Destroy();
 Actors.Reset();Targets.Reset();Guests.Reset();Pieces.Reset();BuiltFor.Reset();
}

FVector UMareHotelEventsWorld::Ground(const FVector& At) const
{
 FHitResult Hit;FCollisionQueryParams Q(TEXT("MareEventGround"),false);
 for(const auto& A:Actors)if(IsValid(A))Q.AddIgnoredActor(A);
 if(GetWorld()->LineTraceSingleByChannel(Hit,At+FVector(0,0,400),At-FVector(0,0,600),ECC_WorldStatic,Q))return Hit.ImpactPoint;
 return At;
}

void UMareHotelEventsWorld::Build(const TSharedPtr<FJsonObject>& Booked)
{
 Clear();auto S=EvSim(GetWorld());if(!S)return;const auto D=S->HotelEventDefs();const auto Def=S->HotelEventKind(UMareSimulation::String(Booked,TEXT("kind")));
 const TArray<TSharedPtr<FJsonValue>>* AreaA=nullptr;FVector2D Area(10600,-1900);
 if(D->TryGetArrayField(TEXT("area"),AreaA) && AreaA->Num()==2)Area=FVector2D((*AreaA)[0]->AsNumber(),(*AreaA)[1]->AsNumber());
 if(!Ghost)Ghost=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Custom/HotelEvents/M_EventGhost.M_EventGhost"));
 for(int32 Pass=0;Pass<2;++Pass){const auto List=Objects(Def,Pass?TEXT("extras"):TEXT("pieces"));
  for(int32 I=0;I<List.Num();++I){const auto P=List[I];const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!P->TryGetArrayField(TEXT("at"),At) || At->Num()<2)continue;
   const FString Model=UMareSimulation::String(P,TEXT("model"));auto Mesh=LoadObject<UStaticMesh>(nullptr,*AssetPath(Model));if(!Mesh){UE_LOG(LogTemp,Warning,TEXT("MARE_EVENT_MISSING %s"),*Model);continue;}
   const FVector Spot=Ground(FVector(Area.X+(*At)[0]->AsNumber(),Area.Y+(*At)[1]->AsNumber(),0));
   FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   auto A=GetWorld()->SpawnActor<AStaticMeshActor>(Spot,FRotator(0,UMareSimulation::Number(P,TEXT("yaw")),0),SP);if(!A)continue;
   A->SetMobility(EComponentMobility::Movable);A->GetStaticMeshComponent()->SetStaticMesh(Mesh);Actors.Add(A);
   auto T=GetWorld()->SpawnActor<AMareServiceTarget>(Spot+FVector(0,0,60),FRotator::ZeroRotator,SP);
   if(T){T->Action=TEXT("EventPiece");T->DataIndex=Pass*1000+I;T->Reach=260;T->OcclusionTolerance=120;
    T->Label=FString::Printf(TEXT("Montar: %s"),*UMareSimulation::String(P,TEXT("label")));Targets.Add(T);}
   Pieces.Add({A,T,Pass==1,I,false,Model});}}
 BuiltFor=UMareSimulation::String(Booked,TEXT("kind"))+FString::Printf(TEXT("@%.0f"),UMareSimulation::Number(Booked,TEXT("day")));
 UE_LOG(LogTemp,Display,TEXT("MARE_EVENT plan %s pieces=%d"),*BuiltFor,Pieces.Num());
}

void UMareHotelEventsWorld::Refresh(const TSharedPtr<FJsonObject>& Booked)
{
 // A piece not set yet is a see-through ghost without collision; set, it is the real thing.
 const bool bSetup=UMareSimulation::String(Booked,TEXT("state"))==TEXT("booked");
 for(auto& P:Pieces){if(!IsValid(P.Actor))continue;const bool bPlaced=Flag(Booked,P.bExtra,P.Index);auto C=P.Actor->GetStaticMeshComponent();
  const bool bWantShown=bPlaced;
  if(P.bShown!=bWantShown || (!bPlaced && C->GetNumOverrideMaterials()==0)){
   // Nanite draws only opaque/masked: the ghost and a piece with its own glass (the lantern) render without it.
   if(bPlaced){C->EmptyOverrideMaterials();C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);bool bGlass=false;
    for(int32 M=0;M<C->GetNumMaterials();++M)if(auto Mat=C->GetMaterial(M))bGlass|=IsTranslucentBlendMode(Mat->GetBlendMode());C->SetForceDisableNanite(bGlass);}
   else{C->SetForceDisableNanite(true);for(int32 M=0;M<C->GetNumMaterials();++M)if(Ghost)C->SetMaterial(M,Ghost);C->SetCollisionEnabled(ECollisionEnabled::NoCollision);}
   P.bShown=bWantShown;}
  // After the guests arrive the unset ghosts disappear (the chance to set them is gone).
  P.Actor->SetActorHiddenInGame(!bPlaced && !bSetup);
  if(IsValid(P.Target))P.Target->SetActorHiddenInGame(bPlaced || !bSetup);}
}

void UMareHotelEventsWorld::SeatGuests(const TSharedPtr<FJsonObject>& Booked)
{
 auto S=EvSim(GetWorld());if(!S || Guests.Num())return;const auto Def=S->HotelEventKind(UMareSimulation::String(Booked,TEXT("kind")));
 int32 Want=int32(UMareSimulation::Number(Def,TEXT("guests"),8));bool bChatty=false;Def->TryGetBoolField(TEXT("chatty"),bChatty);/* a party talks; a ceremony or a talk listens */const float SeatZ=UMareSimulation::Number(S->HotelEventDefs(),TEXT("chair_seat_z"),46);
 const float Front=UMareSimulation::Number(S->HotelEventDefs(),TEXT("chair_front_yaw"),0);int32 N=0;
 for(const auto& P:Pieces){if(Want<=0)break;if(!IsValid(P.Actor) || P.bExtra || !Flag(Booked,false,P.Index) || !P.Model.Contains(TEXT("chair")))continue;
  FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  const FVector Seat=P.Actor->GetActorLocation()+FVector(0,0,SeatZ);const float Yaw=P.Actor->GetActorRotation().Yaw+Front;
  auto G=GetWorld()->SpawnActor<AMarePerson>(Seat+FVector(0,0,90),FRotator(0,Yaw,0),SP);if(!G)continue;
  G->SaveId=FString::Printf(TEXT("hotel_event_%d"),N);G->PersonName=TEXT("Convidado");G->Tags.Add(TEXT("MareHotelGuest"));G->bAmbient=true;G->bSeated=true;G->bConversing=bChatty;
  G->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);G->GetCharacterMovement()->DisableMovement();G->SetAppearance(N%4);G->SitOn(Seat,Yaw);
  Guests.Add(G);++N;--Want;}
 // Who the party is for stands at the front facing the guests (the couple under the arch, the speaker at the lectern).
 {const TArray<TSharedPtr<FJsonValue>>* AreaA=nullptr;FVector2D Area(10600,-1900);
  if(S->HotelEventDefs()->TryGetArrayField(TEXT("area"),AreaA) && AreaA->Num()==2)Area=FVector2D((*AreaA)[0]->AsNumber(),(*AreaA)[1]->AsNumber());
  const auto Hosts=Objects(Def,TEXT("hosts"));
  for(int32 H=0;H<Hosts.Num();++H){const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!Hosts[H]->TryGetArrayField(TEXT("at"),At) || At->Num()<2)continue;
   FActorSpawnParameters SP;SP.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
   const FVector Foot=Ground(FVector(Area.X+(*At)[0]->AsNumber(),Area.Y+(*At)[1]->AsNumber(),0));
   auto G=GetWorld()->SpawnActor<AMarePerson>(Foot+FVector(0,0,92),FRotator(0,UMareSimulation::Number(Hosts[H],TEXT("yaw")),0),SP);if(!G)continue;
   G->SaveId=FString::Printf(TEXT("hotel_event_host_%d"),H);G->PersonName=UMareSimulation::String(Hosts[H],TEXT("label"));G->Tags.Add(TEXT("MareHotelGuest"));G->bAmbient=true;
   G->GetCharacterMovement()->DisableMovement();G->SetAppearance((N+H)%4);Guests.Add(G);}}
 UE_LOG(LogTemp,Display,TEXT("MARE_EVENT guests seated=%d"),N);
}

void UMareHotelEventsWorld::Tick(float DeltaSeconds)
{
 UWorld* World=GetWorld();if(!World || !World->IsGameWorld())return;Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 auto S=EvSim(World);if(!S)return;const auto B=S->BookedHotelEvent();
 if(!B){if(Pieces.Num() || Guests.Num())Clear();return;}
 const FString State=UMareSimulation::String(B,TEXT("state"));
 const bool bToday=int32(UMareSimulation::Number(S->State,TEXT("day"),1))==int32(UMareSimulation::Number(B,TEXT("day")));
 const bool bVisible=bToday && (State==TEXT("show") || UMareSimulation::Number(S->State,TEXT("minutes"))>=UMareSimulation::Number(S->HotelEventDefs(),TEXT("setup_from"),6)*60);
 if(!bVisible){if(Pieces.Num())Clear();return;}
 const FString Key=UMareSimulation::String(B,TEXT("kind"))+FString::Printf(TEXT("@%.0f"),UMareSimulation::Number(B,TEXT("day")));
 if(BuiltFor!=Key)Build(B);
 Refresh(B);
 if(State==TEXT("show"))SeatGuests(B);
}

void UMareHotelEventsWorld::Place(int32 DataIndex)
{
 auto S=EvSim(GetWorld());if(!S)return;const bool bExtra=DataIndex>=1000;
 if(S->PlaceHotelEventPiece(bExtra,bExtra?DataIndex-1000:DataIndex)){UMareAudioWorld::Action(this,TEXT("click"));if(const auto B=S->BookedHotelEvent())Refresh(B);}
}

FString UMareHotelEventsWorld::QA(const FString& Cmd)
{
 auto S=EvSim(GetWorld());if(!S)return TEXT("no sim");FString A,Arg;if(!Cmd.Split(TEXT(":"),&A,&Arg))A=Cmd;
 if(A==TEXT("placeall")){int32 N=0;for(const auto& P:Pieces)if(!P.bExtra || Arg==TEXT("extras")){if(S->PlaceHotelEventPiece(P.bExtra,P.Index))++N;}
  if(const auto B=S->BookedHotelEvent())Refresh(B);return FString::Printf(TEXT("placed=%d"),N);}
 if(A==TEXT("place")){Place(FCString::Atoi(*Arg));return S->LastMessage;}
 const auto B=S->BookedHotelEvent();
 return FString::Printf(TEXT("booked=%s state=%s pieces=%d actors=%d guests=%d placed=%d/%d extras=%d/%d"),B?*UMareSimulation::String(B,TEXT("kind")):TEXT("-"),
  B?*UMareSimulation::String(B,TEXT("state")):TEXT("-"),Pieces.Num(),Actors.Num(),Guests.Num(),S->HotelEventCount(false,true),S->HotelEventCount(false,false),
  S->HotelEventCount(true,true),S->HotelEventCount(true,false));
}
