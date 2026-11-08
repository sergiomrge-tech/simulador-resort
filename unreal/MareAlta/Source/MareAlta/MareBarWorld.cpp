#include "MareBarWorld.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MarePerson.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
 UMareSimulation* Sim(const UWorld* World){return World && World->GetGameInstance()?World->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 FVector Point(const TSharedPtr<FJsonObject>& Defs,const FString& Key,double* Yaw=nullptr)
 {
  const TArray<TSharedPtr<FJsonValue>>* At=nullptr;if(!Defs->TryGetArrayField(Key,At) || At->Num()<3)return FVector::ZeroVector;
  if(Yaw)*Yaw=At->Num()>3?(*At)[3]->AsNumber():0;
  return FVector((*At)[0]->AsNumber(),(*At)[1]->AsNumber(),(*At)[2]->AsNumber());
 }
}

TStatId UMareBarWorld::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareBarWorld,STATGROUP_Tickables);}

void UMareBarWorld::Deinitialize()
{
 if(IsValid(Station))Station->Destroy();if(IsValid(Barman))Barman->Destroy();
 for(auto& Pair:Guests)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:Leaving)if(IsValid(Pair.Key))Pair.Key->Destroy();
 for(auto& Prop:PrepProps)if(IsValid(Prop))Prop->Destroy();
 for(auto& Pair:Shelf)if(IsValid(Pair.Value))Pair.Value->Destroy();
 for(auto& Pair:UpgradeProps)if(IsValid(Pair.Value))Pair.Value->Destroy();
 if(IsValid(GlassTarget))GlassTarget->Destroy();if(IsValid(GlassActor))GlassActor->Destroy();if(IsValid(Falling))Falling->Destroy();
 Guests.Empty();Leaving.Empty();PrepProps.Empty();Shelf.Empty();Super::Deinitialize();
}

bool UMareBarWorld::StoolTop(int32 Stool,FVector& Top,float& Yaw,AActor* Ignore)const
{
 // The real stool top under the seat point (bar.json "seat" height is only the fallback); false when nothing is hit.
 auto Defs=Sim(GetWorld())->BarDefs();const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(!Defs->TryGetArrayField(TEXT("stools"),List) || !List->IsValidIndex(Stool))return false;
 const auto& S=(*List)[Stool]->AsArray();Yaw=S[2]->AsNumber();
 const TArray<TSharedPtr<FJsonValue>>* SeatFit=nullptr;double SeatTop=82;
 if(Defs->TryGetArrayField(TEXT("seat"),SeatFit) && SeatFit->Num()==2)SeatTop=(*SeatFit)[0]->AsNumber();
 Top=FVector(S[0]->AsNumber(),S[1]->AsNumber(),SeatTop);FHitResult Hit;FCollisionQueryParams Q(TEXT("MareStool"),true,Ignore);
 if(!GetWorld()->LineTraceSingleByChannel(Hit,Top+FVector(0,0,60),Top-FVector(0,0,100),ECC_Visibility,Q))return false;
 Top.Z=Hit.ImpactPoint.Z;return true;
}

AMarePerson* UMareBarWorld::Seat(const FString& Order,const FString& Name,int32 Stool)
{
 auto Defs=Sim(GetWorld())->BarDefs();const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(!Defs->TryGetArrayField(TEXT("stools"),List) || !List->IsValidIndex(Stool))return nullptr;
 const auto& S=(*List)[Stool]->AsArray();const FRotator Facing(0,S[2]->AsNumber(),0);
 // Sitting_Idle puts the hips 46 cm over the root and 33 cm behind it: the root goes in front of the stool seat.
 const TArray<TSharedPtr<FJsonValue>>* SeatFit=nullptr;double SeatTop=82,Ahead=30;
 if(Defs->TryGetArrayField(TEXT("seat"),SeatFit) && SeatFit->Num()==2){SeatTop=(*SeatFit)[0]->AsNumber();Ahead=(*SeatFit)[1]->AsNumber();}
 const FVector At=FVector(S[0]->AsNumber(),S[1]->AsNumber(),SeatTop-46+88)+Facing.Vector()*Ahead;
 FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 auto Person=GetWorld()->SpawnActor<AMarePerson>(At,Facing,Params);if(!Person)return nullptr;
 Person->SaveId=TEXT("bar_")+Order;Person->PersonName=Name;Person->SetAppearance(FCrc::StrCrc32(*Person->SaveId)%4);
 Person->bAmbient=true;Person->bSeated=true;Person->GetCharacterMovement()->DisableMovement();
 Person->SetActorEnableCollision(false);
 // The real stool top (trace; bar.json "seat" is only the fallback) and the pelvis aligned on it per body: with the
 // fixed height the shorter and taller patrons sat inside the stool or up to 20 cm above it (mare_hud.seat_audit).
 FVector Top;float Yaw=Facing.Yaw;if(!StoolTop(Stool,Top,Yaw,Person))Untraced.Add(Order);
 Person->SitOn(Top,Yaw);return Person;
}

namespace
{
 UStaticMesh* PrepMesh(const FString& Name)
 {
  const FString N=TEXT("BarPrep_")+Name;
  return LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Custom/BarPrep/%s/%s.%s"),*N,*N,*N));
 }
 AStaticMeshActor* SpawnProp(UWorld* World,UStaticMesh* Mesh,const FVector& At,float Yaw,bool bCollide)
 {
  if(!Mesh)return nullptr;FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  auto Actor=World->SpawnActor<AStaticMeshActor>(At,FRotator(0,Yaw,0),Params);if(!Actor)return nullptr;
  Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);Actor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
  if(!bCollide)Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  return Actor;
 }
 FLinearColor JsonColor(const TSharedPtr<FJsonObject>& O)
 {
  const TArray<TSharedPtr<FJsonValue>>* C=nullptr;if(!O->TryGetArrayField(TEXT("color"),C) || C->Num()<3)return FLinearColor::White;
  return FLinearColor((*C)[0]->AsNumber(),(*C)[1]->AsNumber(),(*C)[2]->AsNumber());
 }
}

void UMareBarWorld::BuildPrep(const TSharedPtr<FJsonObject>& Defs)
{
 const TArray<TSharedPtr<FJsonValue>>* Bench=nullptr;if(!Defs->TryGetArrayField(TEXT("bench"),Bench) || Bench->Num()<4)return;
 const double Top=(*Bench)[2]->AsNumber();
 // The bench model's top is 95 cm over its base; it blocks like the counter (complex collision).
 if(auto B=SpawnProp(GetWorld(),PrepMesh(TEXT("bench")),FVector((*Bench)[0]->AsNumber(),(*Bench)[1]->AsNumber(),Top-95),(*Bench)[3]->AsNumber(),true))PrepProps.Add(B);
 TMap<FString,FString> Names;TSet<FString> Tapped;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Defs->TryGetArrayField(TEXT("ingredients"),List))for(const auto& V:*List){const FString Id=UMareSimulation::String(V->AsObject(),TEXT("id"));
  Names.Add(Id,UMareSimulation::String(V->AsObject(),TEXT("name")));if(!UMareSimulation::String(V->AsObject(),TEXT("requires")).IsEmpty())Tapped.Add(Id);}
 // Upgrade models, hidden until the level is bought.
 for(const auto& Pair:UMareSimulation::Object(Defs,TEXT("upgrade_props"))->Values){const FString Id(Pair.Key.ToView());const auto& P=Pair.Value->AsArray();if(P.Num()<4)continue;
  if(auto Prop=SpawnProp(GetWorld(),PrepMesh(Id),FVector(P[0]->AsNumber(),P[1]->AsNumber(),P[2]->AsNumber()),P[3]->AsNumber(),Id==TEXT("freezer"))){Prop->SetActorHiddenInGame(true);UpgradeProps.Add(Id,Prop);}}
 for(const auto& Pair:UMareSimulation::Object(Defs,TEXT("shelf"))->Values){
  const FString Id(Pair.Key.ToView());const auto& P=Pair.Value->AsArray();if(P.Num()<3)continue;
  const FVector At(P[0]->AsNumber(),P[1]->AsNumber(),P.Num()>3?P[3]->AsNumber():Top);
  // A tapped ingredient (the chope) has its upgrade model instead of a shelf prop; its target is the tap.
  FVector Focus=At+FVector(0,0,30);
  if(!Tapped.Contains(Id)){auto Prop=SpawnProp(GetWorld(),PrepMesh(Id),At,P[2]->AsNumber(),false);if(!Prop)continue;PrepProps.Add(Prop);Focus=Prop->GetComponentsBoundingBox().GetCenter();}
  if(!Names.Contains(Id))continue;
  // One E target per ingredient, at the middle of the visible prop.
  auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(Focus,FRotator::ZeroRotator);if(!Target)continue;
  Target->Action=TEXT("BarIngredient");Target->Label=Names[Id];Target->Reach=220;Target->OcclusionTolerance=35;
  Target->Tags.Add(FName(*(TEXT("ing:")+Id)));Shelf.Add(Id,Target);}
 const TArray<TSharedPtr<FJsonValue>>* G=nullptr;if(!Defs->TryGetArrayField(TEXT("glass"),G) || G->Num()<2)return;
 const FVector At((*G)[0]->AsNumber(),(*G)[1]->AsNumber(),Top);
 GlassActor=SpawnProp(GetWorld(),PrepMesh(TEXT("glass")),At,0,false);if(!GlassActor)return;
 if(G->Num()>2)GlassActor->SetActorScale3D(FVector((*G)[2]->AsNumber()));
 auto Layer=[this](const TCHAR* Name){auto C=NewObject<UStaticMeshComponent>(GlassActor);C->SetMobility(EComponentMobility::Movable);
  C->SetStaticMesh(PrepMesh(Name));C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  C->SetupAttachment(GlassActor->GetRootComponent());C->RegisterComponent();C->SetVisibility(false);return C;};
 LayerIce=Layer(TEXT("layer_ice"));LayerFruit=Layer(TEXT("layer_fruit"));LayerLiquid=Layer(TEXT("layer_liquid"));LayerFoam=Layer(TEXT("layer_foam"));
 if(LayerLiquid->GetMaterial(0)){LiquidTint=UMaterialInstanceDynamic::Create(LayerLiquid->GetMaterial(0),this);LayerLiquid->SetMaterial(0,LiquidTint);}
 if(LayerFruit->GetMaterial(0)){FruitTint=UMaterialInstanceDynamic::Create(LayerFruit->GetMaterial(0),this);LayerFruit->SetMaterial(0,FruitTint);}
 GlassTarget=GetWorld()->SpawnActor<AMareServiceTarget>(At+FVector(0,0,12),FRotator::ZeroRotator);
 if(GlassTarget){GlassTarget->Action=TEXT("BarGlass");GlassTarget->Label=TEXT("Copo de preparo");GlassTarget->Reach=220;GlassTarget->OcclusionTolerance=35;}
}

TArray<TPair<FVector,FString>> UMareBarWorld::Bubbles()const
{
 TArray<TPair<FVector,FString>> Out;auto S=Sim(GetWorld());if(!S)return Out;const TArray<TSharedPtr<FJsonValue>>* Orders=nullptr;
 if(!UMareSimulation::Object(S->State,TEXT("bar"))->TryGetArrayField(TEXT("orders"),Orders))return Out;
 for(const auto& V:*Orders){const auto O=V->AsObject();const AMarePerson* Person=Guests.FindRef(UMareSimulation::String(O,TEXT("id"))).Get();
  if(!IsValid(Person) || !Person->bSeated)continue;
  // Seated: the bubble floats just over the head (measured in the bar capture: +95 cm floated a metre above it).
  Out.Add({Person->GetActorLocation()+FVector(0,0,58),S->BarBubble(O)});}
 return Out;
}

bool UMareBarWorld::PrepSpot(const FString& Id,FVector& At)const
{
 const AMareServiceTarget* T=Id==TEXT("glass")?GlassTarget.Get():Shelf.FindRef(Id).Get();if(!T)return false;
 At=T->GetActorLocation();return true;
}

void UMareBarWorld::UpdatePrep(UMareSimulation* S,bool bOwned,float DeltaSeconds)
{
 if(Falling){FallTime+=DeltaSeconds;const float A=FMath::Clamp(FallTime/.45f,0.f,1.f);
  // An arc from the shelf item over the glass and down into it.
  const FVector End=GlassActor->GetActorLocation()+FVector(0,0,6);
  Falling->SetActorLocation(FMath::Lerp(FallFrom,End,A)+FVector(0,0,28*FMath::Sin(PI*A)));
  if(A>=1){Falling->Destroy();Falling=nullptr;}}
 if(bOwned && PrepProps.IsEmpty())BuildPrep(S->BarDefs());
 for(auto& Prop:PrepProps)if(IsValid(Prop))Prop->SetActorHiddenInGame(!bOwned);
 for(auto& Pair:UpgradeProps)if(IsValid(Pair.Value))Pair.Value->SetActorHiddenInGame(!bOwned || S->BarUpgrade(Pair.Key)<1);
 {TMap<FString,bool> Avail;const TArray<TSharedPtr<FJsonValue>>* L=nullptr;
  if(S->BarDefs()->TryGetArrayField(TEXT("ingredients"),L))for(const auto& V:*L)Avail.Add(UMareSimulation::String(V->AsObject(),TEXT("id")),S->IsBarItemAvailable(V->AsObject()));
  for(auto& Pair:Shelf)if(IsValid(Pair.Value))Pair.Value->SetActorHiddenInGame(!bOwned || !Avail.FindRef(Pair.Key));}
 if(GlassActor)GlassActor->SetActorHiddenInGame(!bOwned);
 if(GlassTarget)GlassTarget->SetActorHiddenInGame(!bOwned);
 if(!bOwned || !GlassActor)return;
 S->Bar();   // fills the starting shelf before anything below reads (and so creates) bar.stock
 const auto Defs=S->BarDefs();const FString Hand=S->BarHand();const TArray<FString> Glass=S->BarGlass();
 if(Glass.Num()>GlassCount && !Falling){
  const FString N=TEXT("BarPrep_hand_")+Glass.Last();
  if(auto Mesh=LoadObject<UStaticMesh>(nullptr,*FString::Printf(TEXT("/Game/Custom/BarPrep/%s/%s.%s"),*N,*N,*N))){
   const AMareServiceTarget* From=Shelf.FindRef(Glass.Last()).Get();
   FallFrom=From?From->GetActorLocation():GlassActor->GetActorLocation()+FVector(0,0,30);
   Falling=SpawnProp(GetWorld(),Mesh,FallFrom,FMath::FRandRange(0.f,360.f),false);
   if(Falling){Falling->SetActorScale3D(FVector(.6f));Falling->SetActorRotation(FRotator(25,FMath::FRandRange(0.f,360.f),0));FallTime=0;}}}
 GlassCount=Glass.Num();
 auto BarState=UMareSimulation::Object(S->State,TEXT("bar"));auto Stock=UMareSimulation::Object(BarState,TEXT("stock"));
 TMap<FString,TSharedPtr<FJsonObject>> Ing;const TArray<TSharedPtr<FJsonValue>>* List=nullptr;
 if(Defs->TryGetArrayField(TEXT("ingredients"),List))for(const auto& V:*List)Ing.Add(UMareSimulation::String(V->AsObject(),TEXT("id")),V->AsObject());
 for(auto& Pair:Shelf){if(!IsValid(Pair.Value) || !Ing.Contains(Pair.Key))continue;
  const FString Name=UMareSimulation::String(Ing[Pair.Key],TEXT("name"));const int32 Left=int32(UMareSimulation::Number(Stock,Pair.Key));
  Pair.Value->Label=Hand==Pair.Key?Name+TEXT(" · devolver"):Left>0?FString::Printf(TEXT("%s · pegar (%d)"),*Name,Left):Name+TEXT(" · acabou, reponha no balcão");}
 // The glass prompt says what E does next.
 const FString Next=S->BarNextStep();const auto Lines=UMareSimulation::Object(Defs,TEXT("prep_lines"));
 if(GlassTarget){
  if(!Hand.IsEmpty())GlassTarget->Label=TEXT("Copo · colocar ")+(Ing.Contains(Hand)?UMareSimulation::String(Ing[Hand],TEXT("name")):Hand);
  else if(Glass.IsEmpty())GlassTarget->Label=TEXT("Copo de preparo · pegue os ingredientes na bancada");
  else if(!Next.IsEmpty())GlassTarget->Label=TEXT("Copo · ")+UMareSimulation::String(Lines,Next);
  else{FString Guest;const FString Serving=S->BarServing();const TArray<TSharedPtr<FJsonValue>>* Orders=nullptr;
   if(BarState->TryGetArrayField(TEXT("orders"),Orders))
    for(const auto& V:*Orders)if(UMareSimulation::String(V->AsObject(),TEXT("id"))==Serving)Guest=UMareSimulation::String(V->AsObject(),TEXT("name"));
   GlassTarget->Label=Guest.IsEmpty()?FString(TEXT("Copo pronto · ninguém esperando")):TEXT("Copo pronto · servir ")+Guest;}}
 // Layers: ice; muddled fruit tinted by the fruit; the liquid filled by how many liquids and tinted by the mix (a
 // blended drink takes the fruit into it); the foam once shaken or blended.
 auto Prep=UMareSimulation::Object(BarState,TEXT("prep"));TArray<FString> Done;
 for(const auto& Pair:Prep->Values)Done.Add(FString(Pair.Key.ToView()));
 const FString Shown=FString::Join(Glass,TEXT(","))+TEXT("|")+FString::Join(Done,TEXT(","));if(Shown==GlassShown)return;GlassShown=Shown;
 const bool bBlended=Done.Contains(TEXT("liquidificar"));int32 Liquids=0,Fruits=0;bool bIce=false;
 FLinearColor Liquid=FLinearColor::Black,Fruit=FLinearColor::Black;
 for(const FString& I:Glass){if(!Ing.Contains(I))continue;const FString L=UMareSimulation::String(Ing[I],TEXT("layer"));const FLinearColor C=JsonColor(Ing[I]);
  if(L==TEXT("ice"))bIce=true;
  else if(L==TEXT("fruit")){Fruit+=C;++Fruits;if(bBlended){Liquid+=C;++Liquids;}}
  else if(L==TEXT("liquid")){Liquid+=C;++Liquids;}}
 LayerIce->SetVisibility(bIce);
 LayerFruit->SetVisibility(Fruits>0 && !bBlended);if(FruitTint && Fruits)FruitTint->SetVectorParameterValue(TEXT("Tint"),Fruit/float(Fruits));
 LayerLiquid->SetVisibility(Liquids>0);
 if(Liquids){LayerLiquid->SetRelativeScale3D(FVector(1,1,FMath::Clamp(.3f+.22f*Liquids,.3f,1.f)));
  if(LiquidTint)LiquidTint->SetVectorParameterValue(TEXT("Tint"),Liquid/float(Liquids));}
 LayerFoam->SetVisibility(Done.Contains(TEXT("bater")) || bBlended);
}

void UMareBarWorld::Tick(float DeltaSeconds)
{
 if(!GetWorld() || !GetWorld()->IsGameWorld())return;
 auto S=Sim(GetWorld());if(!S)return;
 bool bOwned=false;UMareSimulation::Object(S->State,TEXT("unlocked"))->TryGetBoolField(TEXT("bar"),bOwned);
 UpdatePrep(S,bOwned,DeltaSeconds);
 Clock-=DeltaSeconds;if(Clock>0)return;Clock=.5f;
 const auto Defs=S->BarDefs();
 if(!Station && bOwned){
  Station=GetWorld()->SpawnActor<AMareServiceTarget>(Point(Defs,TEXT("station")),FRotator::ZeroRotator);
  Station->Action=TEXT("BarCounter");Station->Label=TEXT("Bar do Coqueiro · preparar drinks");Station->Reach=230;Station->OcclusionTolerance=70;}
 if(Station)Station->SetActorHiddenInGame(!bOwned);
 const double Now=GetWorld()->GetTimeSeconds();
 for(auto It=Leaving.CreateIterator();It;++It)if(!IsValid(It->Key) || Now>It->Value){if(IsValid(It->Key))It->Key->Destroy();It.RemoveCurrent();}
 // Bartender behind the counter while one is hired and the bar is open.
 const bool bBarman=bOwned && S->HasStaff(TEXT("bartender")) && S->IsBarOpen();
 if(bBarman && !Barman){double Yaw=0;const FVector At=Point(Defs,TEXT("barman"),&Yaw);
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  Barman=GetWorld()->SpawnActor<AMarePerson>(At+FVector(0,0,88),FRotator(0,Yaw,0),Params);
  if(Barman){Barman->SaveId=TEXT("bar_bartender");Barman->PersonName=TEXT("Bartender");Barman->bEmployee=true;Barman->StaffRole=TEXT("bartender");Barman->bAmbient=true;
   Barman->GetCharacterMovement()->DisableMovement();Barman->SetActorEnableCollision(false);}}
 else if(!bBarman && Barman){Barman->Destroy();Barman=nullptr;}
 // One guest per open order on a free stool; a guest whose order is gone stands up and walks off.
 TArray<FString> Open;const TArray<TSharedPtr<FJsonValue>>* Orders=nullptr;
 if(bOwned && UMareSimulation::Object(S->State,TEXT("bar"))->TryGetArrayField(TEXT("orders"),Orders))
  for(const auto& V:*Orders)Open.Add(UMareSimulation::String(V->AsObject(),TEXT("id")));
 const int32 Served=int32(UMareSimulation::Number(UMareSimulation::Object(S->State,TEXT("bar")),TEXT("served")));
 const bool bJustServed=LastServed>=0 && Served>LastServed;LastServed=Served;
 for(auto It=Untraced.CreateIterator();It;++It){AMarePerson* Person=Guests.FindRef(*It);const int32 Stool=StoolOf(*It);FVector Top;float Yaw=0;
  if(!IsValid(Person) || Stool==INDEX_NONE){It.RemoveCurrent();continue;}
  if(StoolTop(Stool,Top,Yaw,Person)){Person->SitOn(Top,Yaw);It.RemoveCurrent();}}
 if(IsValid(Barman) && BarmanGestureUntil>0 && Now>BarmanGestureUntil){BarmanGestureUntil=0;Barman->PlayPose(TEXT("Idle"));}
 struct FDrinker{FString Key;AMarePerson* Person;int32 Stool;};TArray<FDrinker> Drinkers;
 for(auto It=Guests.CreateIterator();It;++It){if(Open.Contains(It->Key))continue;AMarePerson* Person=It->Value;
  if(IsValid(Person)){
   if(bJustServed && !It->Key.StartsWith(TEXT("d:"))){const FString Last=UMareSimulation::String(UMareSimulation::Object(S->State,TEXT("bar")),TEXT("last"));
    Person->HoldProduct(UMareSimulation::String(S->BarRecipe(Last),TEXT("mesh")));
    // 07/11 (reference game: "bar assim"): the guest stays on the stool with the drink, sipping, then leaves; the
    // bartender turns to them and hands it over.
    const FString Key=TEXT("d:")+It->Key;const int32 Stool=Stools.FindRef(It->Key);
    Drinkers.Add({Key,Person,Stool});DrinkUntil.Add(Key,Now+FMath::FRandRange(25.f,40.f));
    if(IsValid(Barman)){const FVector To=Person->GetActorLocation()-Barman->GetActorLocation();Barman->SetActorRotation(FRotator(0,To.Rotation().Yaw,0));
     Barman->PlayPose(TEXT("Interact"),false);BarmanGestureUntil=Now+1.6;}
    Stools.Remove(It->Key);It.RemoveCurrent();continue;}
   if(It->Key.StartsWith(TEXT("d:"))){if(Now<DrinkUntil.FindRef(It->Key))continue;DrinkUntil.Remove(It->Key);}
   Person->bSeated=false;Person->SetActorEnableCollision(true);Person->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
   const FVector Away=Person->GetActorLocation()+Person->GetActorForwardVector()*-900+FVector(0,-600,0);
   Leaving.Add(Person,Now+(Person->WalkTo(Away)?25.:4.));}
  Stools.Remove(It->Key);It.RemoveCurrent();}
 for(const FDrinker& D:Drinkers){Guests.Add(D.Key,D.Person);Stools.Add(D.Key,D.Stool);}   // after the loop: no map edits while iterating
 const TArray<TSharedPtr<FJsonValue>>* Seats=nullptr;const int32 Count=Defs->TryGetArrayField(TEXT("stools"),Seats)?Seats->Num():0;
 for(const auto& V:Orders?*Orders:TArray<TSharedPtr<FJsonValue>>()){const auto O=V->AsObject();const FString Id=UMareSimulation::String(O,TEXT("id"));
  if(Guests.Contains(Id))continue;
  TSet<int32> Used;for(const auto& Pair:Stools)Used.Add(Pair.Value);
  int32 Free=INDEX_NONE;for(int32 I=0;I<Count && Free==INDEX_NONE;++I)if(!Used.Contains(I))Free=I;if(Free==INDEX_NONE)break;
  if(auto Person=Seat(Id,UMareSimulation::String(O,TEXT("name")),Free)){Guests.Add(Id,Person);Stools.Add(Id,Free);}}
}
