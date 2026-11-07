// The two playable arcades of the Grand Hotel game room (CHECKLIST_EXPANSOES 5.4): "Corrida de Jangada" and "Pinball do Farol",
// drawn on the cabinet's own screen. Values in business_games.json businesses.fliperama.arcade.
#include "MareArcade.h"
#include "MareSimulation.h"
#include "MareServiceTarget.h"
#include "MareGamepad.h"
#include "MareAudioWorld.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Canvas.h"
#include "Engine/CanvasRenderTarget2D.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "InputCoreTypes.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
 UMareSimulation* ArcSim(const UWorld* W){return W && W->GetGameInstance()?W->GetGameInstance()->GetSubsystem<UMareSimulation>():nullptr;}
 TSharedPtr<FJsonObject> ArcDefs(UMareSimulation* S)
 {
  return S?UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(S->BusinessGames(),TEXT("businesses")),TEXT("fliperama")),TEXT("arcade")):MakeShared<FJsonObject>();
 }
 TSharedPtr<FJsonObject> Records(UMareSimulation* S)
 {
  return UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(UMareSimulation::Object(S->State,TEXT("prog")),TEXT("biz")),TEXT("fliperama")),TEXT("records"));
 }
 bool Overlap(float AX,float AY,float AW,float AH,float BX,float BY,float BW,float BH)
 {
  return FMath::Abs(AX-BX)*2<AW+BW && FMath::Abs(AY-BY)*2<AH+BH;
 }
}

// ------------------------------------------------------------------ Corrida de Jangada
void FMareJangada::Reset(){*this=FMareJangada();}

int32 FMareJangada::Step(float Dt,float Steer,FRandomStream& R)
{
 if(bOver)return 0;int32 Ev=0;Time+=Dt;
 Speed=FMath::Min(170.f,60.f+Time*2.2f);Dist+=Speed*Dt;Scroll=FMath::Fmod(Scroll+Speed*Dt,128.f);
 X=FMath::Clamp(X+FMath::Clamp(Steer,-1.f,1.f)*150.f*Dt,Bank+RaftW*.5f,MareArc::VW-Bank-RaftW*.5f);
 Hurt=FMath::Max(0.f,Hurt-Dt);
 // New things at the top of the river, more often as it speeds up; never two on the same spot.
 Spawn-=Dt*(Speed/60.f);
 if(Spawn<=0){Spawn=R.FRandRange(.75f,1.25f);
  const float Roll=R.FRand();FThing T;T.Kind=Roll<.48f?0:Roll<.63f?1:Roll<.95f?2:3;
  T.W=T.Kind==0?26:T.Kind==1?44:18;T.H=T.Kind==0?24:T.Kind==1?22:12;
  T.X=R.FRandRange(Bank+T.W*.5f,MareArc::VW-Bank-T.W*.5f);T.Y=-T.H;T.VX=T.Kind==1?(R.FRand()<.5f?-28.f:28.f):0.f;
  bool bFree=true;for(const FThing& O:Things)if(O.Y<40 && FMath::Abs(O.X-T.X)<(O.W+T.W)*.5f+6)bFree=false;
  if(bFree)Things.Add(T);}
 for(FThing& T:Things){if(T.bDone)continue;T.Y+=Speed*Dt;T.X+=T.VX*Dt;
  if(T.X<Bank+T.W*.5f || T.X>MareArc::VW-Bank-T.W*.5f)T.VX=-T.VX;
  if(!Overlap(X,RaftY,RaftW,RaftH,T.X,T.Y,T.W*.8f,T.H*.8f))continue;
  if(T.Kind>=2){T.bDone=true;Score+=T.Kind==3?50:10;++Fish;Ev|=T.Kind==3?4:2;}
  else if(Hurt<=0){T.bDone=true;--Lives;++Hits;Hurt=1.5f;Ev|=1;if(Lives<=0){bOver=true;Ev|=8;}}}
 Things.RemoveAll([](const FThing& T){return T.bDone || T.Y>MareArc::VH+30;});
 return Ev;
}

// ------------------------------------------------------------------ Pinball do Farol
namespace
{
 // Chrome walls (tools/ue58/gen_arcade_art.py PB_WALLS): outer frame, the plunger lane wall and floor, the two slopes.
 const FVector2D PBWalls[][2]={{{84,232},{84,40}},{{84,40},{116,8}},{{116,8},{204,8}},{{204,8},{236,40}},{{236,40},{236,232}},
  {{220,232},{220,64}},{{220,232},{236,232}},{{84,170},{124,204}},{{220,170},{180,204}}};
 FVector2D Closest(const FVector2D& P,const FVector2D& A,const FVector2D& B)
 {
  const FVector2D AB=B-A;const float T=FMath::Clamp(float(FVector2D::DotProduct(P-A,AB)/FMath::Max(AB.SizeSquared(),1e-4)),0.f,1.f);return A+AB*T;
 }
 // Pushes the ball out of a capsule (segment + radius) and bounces it against the surface moving at SurfaceVel.
 bool Collide(FVector2D& P,FVector2D& V,const FVector2D& A,const FVector2D& B,float Radius,float Bounce,const FVector2D& SurfaceVel=FVector2D::ZeroVector)
 {
  const FVector2D Q=Closest(P,A,B);const FVector2D D=P-Q;const float Dist=float(D.Size());if(Dist>=Radius)return false;
  const FVector2D N=Dist>1e-4f?D/Dist:FVector2D(0,-1);P=Q+N*Radius;
  const FVector2D Rel=V-SurfaceVel;const float VN=float(FVector2D::DotProduct(Rel,N));if(VN<0)V-=N*(1+Bounce)*VN;
  return true;
 }
}

void FMarePinball::Reset(){*this=FMarePinball();}

FVector2D FMarePinball::Tip(int32 Side,float Angle) const
{
 const float R=FMath::DegreesToRadians(Angle);
 return Pivot(Side)+FVector2D(Side==0?FMath::Cos(R):-FMath::Cos(R),FMath::Sin(R))*FlipLen;
}

int32 FMarePinball::Step(float Dt,bool bLeft,bool bRight,bool bLaunch)
{
 if(bOver)return 0;int32 Ev=0;Time+=Dt;
 for(float& F:Flash)F=FMath::Max(0.f,F-Dt);
 // In the plunger lane, resting on its floor: the launch sends it up the lane.
 bInLane=Ball.X>221 && Ball.Y>150;
 if(bInLane && bLaunch && Vel.Size()<40)Vel=FVector2D(0,-430);
 const int32 Sub=8;const float H=Dt/Sub;
 for(int32 K=0;K<Sub;++K){
  for(int32 Side=0;Side<2;++Side){FlipPrev[Side]=Flip[Side];const bool bHeld=Side==0?bLeft:bRight;
   Flip[Side]=bHeld?FMath::Max(FlipUp,Flip[Side]-1500*H):FMath::Min(FlipRest,Flip[Side]+800*H);}
  Vel.Y+=Gravity*H;if(Vel.Size()>620)Vel=Vel.GetSafeNormal()*620;
  Ball+=Vel*H;
  for(const auto& W:PBWalls)Collide(Ball,Vel,W[0],W[1],BallR+1.5f,.5f);
  for(int32 I=0;I<3;++I){const FVector2D C=BumperPos(I);const FVector2D D=Ball-C;const float Dist=float(D.Size());
   if(Dist<BallR+BumperR && Dist>1e-3f){const FVector2D N=D/Dist;Ball=C+N*(BallR+BumperR);
    const float VN=float(FVector2D::DotProduct(Vel,N));Vel-=N*2*FMath::Min(VN,0.f);Vel+=N*170;Score+=100;++Bumps;Flash[I]=.2f;Ev|=1;}}
  for(int32 Side=0;Side<2;++Side){
   // The flipper surface moves with the turn: the ball takes that speed (the shot).
   const FVector2D P=Pivot(Side),T=Tip(Side,Flip[Side]);const FVector2D Q=Closest(Ball,P,T),R=Q-P;
   const float W=FMath::DegreesToRadians(Flip[Side]-FlipPrev[Side])/H;
   const FVector2D Surface=Side==0?FVector2D(-R.Y,R.X)*W:FVector2D(R.Y,-R.X)*W;
   if(Collide(Ball,Vel,P,T,BallR+3,.25f,Surface) && FMath::Abs(W)>1)Ev|=32;}}
 // Rollover lanes at the top.
 if(Ball.Y>22 && Ball.Y<40)for(int32 I=0;I<3;++I)if(!bLanes[I] && FMath::Abs(Ball.X-LaneX(I))<7){bLanes[I]=true;Score+=250;Ev|=2;
  if(bLanes[0] && bLanes[1] && bLanes[2]){Score+=1000;Ev|=4;bLanes[0]=bLanes[1]=bLanes[2]=false;}}
 // A ball resting off the lane (on a slope corner) gets a nudge.
 Still=(!bInLane && Vel.Size()<6)?Still+Dt:0;if(Still>2.5f){Vel=FVector2D(Ball.X<152?60:-60,-140);Still=0;}
 if(Ball.Y>248){--Balls;Ev|=16;if(Balls<=0){bOver=true;Ev|=8;}else{Ball=FVector2D(228,224);Vel=FVector2D::ZeroVector;bInLane=true;}}
 return Ev;
}

// ------------------------------------------------------------------ the cabinets
TStatId UMareArcade::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UMareArcade,STATGROUP_Tickables);}

void UMareArcade::Deinitialize()
{
 if(IsPlaying())Stop(FString());
 for(auto& T:Targets)if(IsValid(T))T->Destroy();Targets.Reset();
 Super::Deinitialize();
}

int32 UMareArcade::HitsFor(int32 GameIndex,int32 Points,const TSharedPtr<FJsonObject>& Defs)
{
 const TArray<TSharedPtr<FJsonValue>>* L=nullptr;int32 Hits=0;
 if(UMareSimulation::Object(Defs,GameId(GameIndex))->TryGetArrayField(TEXT("hits_at"),L))for(const auto& V:*L)if(Points>=V->AsNumber())++Hits;
 return FMath::Min(Hits,3);
}

void UMareArcade::FindCabinets()
{
 // The cabinets are placed by UMareBusinessWorld at game_room.arcades (index 0 Jangada, 1 Pinball; the second cabinet model kept its file name mare_arcade_siri).
 Cabinets.SetNum(2);
 for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It){auto Mesh=It->GetStaticMeshComponent()->GetStaticMesh();if(!Mesh)continue;
  const FString N=Mesh->GetName();if(N==TEXT("mare_arcade_jangada"))Cabinets[0]=*It;else if(N==TEXT("mare_arcade_siri"))Cabinets[1]=*It;}
 for(int32 I=0;I<2;++I)if(IsValid(Cabinets[I]) && (!Targets.IsValidIndex(I) || !IsValid(Targets[I]))){
  if(Targets.Num()<=I)Targets.SetNum(I+1);
  const FTransform T=Cabinets[I]->GetActorTransform();
  auto Target=GetWorld()->SpawnActor<AMareServiceTarget>(T.TransformPosition(FVector(0,45,110)),FRotator::ZeroRotator);
  if(Target){Target->Action=TEXT("BusinessCounter");Target->Tags.Add(TEXT("biz:fliperama"));Target->DataIndex=I;Target->Reach=230;Target->OcclusionTolerance=80;
   Target->Label=I==0?TEXT("Jogar \"Corrida de Jangada\""):TEXT("Jogar \"Pinball do Farol\"");}
  Targets[I]=Target;}
 for(int32 I=0;I<Targets.Num();++I)if(IsValid(Targets[I]))Targets[I]->SetActorHiddenInGame(!IsValid(Cabinets[I]) || Cabinets[I]->IsHidden());
}

UTexture2D* UMareArcade::Tex(const TCHAR* Name)
{
 if(auto Found=Textures.Find(Name))return Found->Get();
 UTexture2D* T=LoadObject<UTexture2D>(nullptr,*FString::Printf(TEXT("/Game/UI/Arcade/%s.%s"),Name,Name));
 Textures.Add(Name,T);
 if(!T)UE_LOG(LogTemp,Warning,TEXT("MARE_ARCADE_MISSING %s"),Name);
 return T;
}

bool UMareArcade::Start(APlayerController* Controller,int32 Force)
{
 if(IsPlaying() || !Controller)return false;FindCabinets();
 int32 Pick=Force;
 if(Pick<0){float Best=1e9;const FVector At=Controller->GetPawn()?Controller->GetPawn()->GetActorLocation():FVector::ZeroVector;
  for(int32 I=0;I<Cabinets.Num();++I)if(IsValid(Cabinets[I])){const float D=FVector::Dist2D(At,Cabinets[I]->GetActorLocation());if(D<Best){Best=D;Pick=I;}}}
 if(!Cabinets.IsValidIndex(Pick) || !IsValid(Cabinets[Pick]))return false;
 auto S=ArcSim(GetWorld());if(!S)return false;
 Game=Pick;Cabinet=Pick;Player=Controller;Over=0;Idle=0;bPaid=false;bRecord=false;Final=0;
 Rng.Initialize(int32(FPlatformTime::Cycles()&0x7fffffff));
 if(Game==0)Jangada.Reset();else Pinball.Reset();
 Record=int32(UMareSimulation::Number(Records(S),GameId(Game)));
 // Every sprite loaded (and resident) before the first frame: a texture still compiling drew as a white square.
 for(const TCHAR* Name:{TEXT("T_Arc_Font"),TEXT("T_Arc_J_Water"),TEXT("T_Arc_J_Sand"),TEXT("T_Arc_J_Rock1"),TEXT("T_Arc_J_Boat"),TEXT("T_Arc_J_Fish"),
  TEXT("T_Arc_J_FishGold"),TEXT("T_Arc_J_Raft"),TEXT("T_Arc_P_Table"),TEXT("T_Arc_P_Bumper"),TEXT("T_Arc_P_Ball"),TEXT("T_Arc_P_Flipper")})if(UTexture2D* T=Tex(Name)){T->SetForceMipLevelsToBeResident(30.f);T->WaitForStreaming();}
 // The game on the cabinet's screen: a canvas render target replaces the screen slot while it is played.
 if(!Screen){Screen=UCanvasRenderTarget2D::CreateCanvasRenderTarget2D(this,UCanvasRenderTarget2D::StaticClass(),MareArc::VW*2,MareArc::VH*2);
  if(Screen){Screen->ClearColor=FLinearColor::Black;Screen->OnCanvasRenderTargetUpdate.AddDynamic(this,&UMareArcade::DrawScreen);}}
 auto Comp=Cabinets[Pick]->GetStaticMeshComponent();ScreenSlot=-1;
 for(int32 I=0;I<Comp->GetNumMaterials();++I)if(auto M=Comp->GetMaterial(I))if(M->GetName().Contains(TEXT("screen"))){ScreenSlot=I;break;}
 if(ScreenSlot>=0 && Screen){SavedMaterial=Comp->GetMaterial(ScreenSlot);
  if(auto Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/UI/Arcade/M_ArcadeScreen.M_ArcadeScreen"))){
   ScreenMID=UMaterialInstanceDynamic::Create(Base,this);ScreenMID->SetTextureParameterValue(TEXT("Screen"),Screen);Comp->SetMaterial(ScreenSlot,ScreenMID);}}
 // Close in front of the screen, square to it: the 40 x 30 cm picture fills most of the view.
 const FTransform T=Cabinets[Pick]->GetActorTransform();
 const FVector Centre=T.TransformPosition(MareArc::ScreenLocal),Normal=T.TransformVectorNoScale(MareArc::ScreenNormal);
 const FVector Eye=Centre+Normal*60.f;
 Camera=GetWorld()->SpawnActor<ACameraActor>(Eye,(Centre-Eye).Rotation());
 if(Camera){Camera->GetCameraComponent()->SetConstraintAspectRatio(false);Camera->GetCameraComponent()->SetFieldOfView(57.f);}
 Controller->SetViewTargetWithBlend(Camera,.4f);Controller->SetIgnoreMoveInput(true);Controller->SetIgnoreLookInput(true);
 // No arms or hands of the player on screen (Sergio, 03/11).
 if(auto Pawn=Controller->GetPawn()){TArray<UPrimitiveComponent*> Parts;Pawn->GetComponents(Parts);HiddenParts.Reset();
  for(auto C:Parts)if(C->IsVisible()){HiddenParts.Add(C);C->SetVisibility(false);}}
 S->LastMessage=Game==0?TEXT("Corrida de Jangada: desvie das pedras e dos barcos e pesque os peixes."):TEXT("Pinball do Farol: Espaço lança a bola, A e D (ou Shift esquerdo e direito) batem os flippers.");
 UMareAudioWorld::Action(this,TEXT("coin"));
 return true;
}

void UMareArcade::Finish()
{
 // The token is paid when the game ends (the business pays by points); a new best score gives fame.
 auto S=ArcSim(GetWorld());if(!S || bPaid)return;bPaid=true;
 Final=Game==0?Jangada.Points():Pinball.Points();const auto D=ArcDefs(S);
 const int32 Hits=HitsFor(Game,Final,D);const double Paid=S->PlayBusiness(TEXT("fliperama"),Hits);
 FString Msg=FString::Printf(TEXT("%s: %d pontos."),Game==0?TEXT("Corrida de Jangada"):TEXT("Pinball do Farol"),Final);
 if(Final>Record){bRecord=true;Records(S)->SetNumberField(GameId(Game),Final);
  const int32 Fame=int32(UMareSimulation::Number(D,TEXT("record_fame"),2));if(Record>0)S->AddFame(Fame);
  Msg+=Record>0?FString::Printf(TEXT(" Novo recorde! (antes: %d)"),Record):FString(TEXT(" Primeiro recorde da máquina!"));Record=Final;}
 if(Paid>0)Msg+=FString::Printf(TEXT(" Fichas: R$ %.0f."),Paid);
 S->LastMessage=Msg;S->Save();
 UE_LOG(LogTemp,Display,TEXT("MARE_ARCADE end game=%s points=%d hits=%d record=%d paid=%.0f"),GameId(Game),Final,Hits,Record,Paid);
 UMareAudioWorld::Action(this,bRecord?TEXT("money_register"):TEXT("money_coins"));
}

void UMareArcade::Stop(const FString& Message)
{
 if(!IsPlaying())return;
 if(Cabinets.IsValidIndex(Cabinet) && IsValid(Cabinets[Cabinet]) && ScreenSlot>=0 && SavedMaterial)Cabinets[Cabinet]->GetStaticMeshComponent()->SetMaterial(ScreenSlot,SavedMaterial);
 SavedMaterial=nullptr;ScreenMID=nullptr;ScreenSlot=-1;
 if(auto PC=Player.Get()){PC->SetViewTargetWithBlend(PC->GetPawn(),.4f);PC->ResetIgnoreMoveInput();PC->ResetIgnoreLookInput();}
 for(auto& C:HiddenParts)if(C.IsValid())C->SetVisibility(true);HiddenParts.Reset();
 if(IsValid(Camera))Camera->Destroy();Camera=nullptr;
 if(!Message.IsEmpty())if(auto S=ArcSim(GetWorld()))S->LastMessage=Message;
 Game=-1;Cabinet=-1;
}

void UMareArcade::Tick(float DeltaSeconds)
{
 UWorld* World=GetWorld();if(!World || !World->IsGameWorld())return;
 Clock-=DeltaSeconds;if(Clock<=0){Clock=2.f;FindCabinets();}
 if(!IsPlaying())return;
 auto PC=Player.Get();if(!PC || World->IsPaused())return;
 const float Dt=FMath::Min(DeltaSeconds,.05f);
 if(PC->WasInputKeyJustPressed(EKeys::Q) || PC->WasInputKeyJustPressed(EKeys::Escape) || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right)){
  if(!bPaid && ((Game==0 && Jangada.Time>3) || (Game==1 && Pinball.Time>3)))Finish();
  Stop(bPaid?FString():FString(TEXT("Você saiu do fliperama.")));return;}
 const bool bAct=PC->WasInputKeyJustPressed(EKeys::SpaceBar) || PC->WasInputKeyJustPressed(EKeys::E) || PC->WasInputKeyJustPressed(EKeys::Enter)
  || PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Bottom) || PC->WasInputKeyJustPressed(EKeys::LeftMouseButton);
 if(Over>0){Over-=Dt;if(Over<=0 || (Over<2.2f && bAct)){
   // Space on the result screen plays again (one more token), anything else leaves.
   if(bAct && Over>0){const int32 Again=Game;Stop(FString());Start(PC,Again);}else Stop(FString());}
  if(Screen)Screen->UpdateResource();return;}
 if(Game==0){
  float Steer=PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
  if(PC->IsInputKeyDown(EKeys::A) || PC->IsInputKeyDown(EKeys::Left))Steer-=1;if(PC->IsInputKeyDown(EKeys::D) || PC->IsInputKeyDown(EKeys::Right))Steer+=1;
  const int32 Ev=Jangada.Step(Dt,Steer,Rng);
  if(Ev&1)UMareAudioWorld::Action(this,TEXT("pool_rail_bounce"));if(Ev&6)UMareAudioWorld::Action(this,TEXT("coin"));
  if(Ev&8){Finish();Over=4.f;}}
 else{
  const bool bLeft=PC->IsInputKeyDown(EKeys::A) || PC->IsInputKeyDown(EKeys::Left) || PC->IsInputKeyDown(EKeys::LeftShift) || PC->IsInputKeyDown(EKeys::Gamepad_LeftShoulder)
   || PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis)>.3f;
  const bool bRight=PC->IsInputKeyDown(EKeys::D) || PC->IsInputKeyDown(EKeys::Right) || PC->IsInputKeyDown(EKeys::RightShift) || PC->IsInputKeyDown(EKeys::Gamepad_RightShoulder)
   || PC->GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis)>.3f;
  const bool bLaunch=PC->IsInputKeyDown(EKeys::SpaceBar) || PC->IsInputKeyDown(EKeys::Down) || PC->IsInputKeyDown(EKeys::S) || PC->IsInputKeyDown(EKeys::Gamepad_FaceButton_Bottom);
  const int32 Ev=Pinball.Step(Dt,bLeft,bRight,bLaunch);
  if(Ev&1)UMareAudioWorld::Action(this,TEXT("pool_ball_clack"));if(Ev&6)UMareAudioWorld::Action(this,TEXT("coin"));if(Ev&16)UMareAudioWorld::Action(this,TEXT("voice_annoyed_m"));
  if(Ev&32)UMareAudioWorld::Action(this,TEXT("pool_rail_bounce"));
  if(Ev&8){Finish();Over=4.f;}}
 if(Screen)Screen->UpdateResource();
}

FString UMareArcade::Status() const
{
 if(!IsPlaying())return FString();const bool bPad=MareGamepad::UsingGamepad();
 if(Game==0)return FString::Printf(TEXT("Corrida de Jangada · %s/%s rema · %s sai"),bPad?TEXT("analógico"):TEXT("A"),bPad?TEXT("D-pad"):TEXT("D"),bPad?TEXT("B"):TEXT("Q"));
 return FString::Printf(TEXT("Pinball do Farol · %s lança · %s flippers · %s sai"),bPad?TEXT("A"):TEXT("Espaço"),bPad?TEXT("LB/RB"):TEXT("A/D"),bPad?TEXT("B"):TEXT("Q"));
}

// ------------------------------------------------------------------ drawing (virtual 320 x 240, x Scale)
void UMareArcade::DrawSprite(UCanvas* C,UTexture2D* T,float X,float Y,float W,float H,FLinearColor Tint,FVector2D UV0,FVector2D UVS,float Rotation,FVector2D Pivot) const
{
 C->K2_DrawTexture(T,FVector2D(X*Scale,Y*Scale),FVector2D(W*Scale,H*Scale),UV0,UVS,Tint,BLEND_Translucent,Rotation,Pivot);
}

void UMareArcade::DrawText(UCanvas* C,const FString& Text,float X,float Y,float Size,FLinearColor Color,bool bCentre) const
{
 // Press Start 2P atlas (T_Arc_Font): ASCII 32..127, 16 x 6 cells of 16 px. Accents fall back to the plain letter.
 auto Font=const_cast<UMareArcade*>(this)->Tex(TEXT("T_Arc_Font"));if(!Font)return;
 FString Plain=Text;
 for(const auto& P:{TPair<const TCHAR*,const TCHAR*>(TEXT("ÁÀÂÃ"),TEXT("A")),TPair<const TCHAR*,const TCHAR*>(TEXT("áàâã"),TEXT("a")),TPair<const TCHAR*,const TCHAR*>(TEXT("ÉÊ"),TEXT("E")),
  TPair<const TCHAR*,const TCHAR*>(TEXT("éê"),TEXT("e")),TPair<const TCHAR*,const TCHAR*>(TEXT("Í"),TEXT("I")),TPair<const TCHAR*,const TCHAR*>(TEXT("í"),TEXT("i")),
  TPair<const TCHAR*,const TCHAR*>(TEXT("ÓÔÕ"),TEXT("O")),TPair<const TCHAR*,const TCHAR*>(TEXT("óôõ"),TEXT("o")),TPair<const TCHAR*,const TCHAR*>(TEXT("Ú"),TEXT("U")),
  TPair<const TCHAR*,const TCHAR*>(TEXT("ú"),TEXT("u")),TPair<const TCHAR*,const TCHAR*>(TEXT("Ç"),TEXT("C")),TPair<const TCHAR*,const TCHAR*>(TEXT("ç"),TEXT("c"))})
  for(const TCHAR* Ch=P.Key;*Ch;++Ch)Plain.ReplaceCharInline(*Ch,P.Value[0]);
 float X0=bCentre?X-Plain.Len()*Size*.5f:X;
 for(int32 I=0;I<Plain.Len();++I){const int32 Code=FMath::Clamp(int32(Plain[I]),32,127)-32;
  // Drop shadow, then the letter.
  for(int32 Pass=0;Pass<2;++Pass){const float O=Pass?0:Size*.12f;
   DrawSprite(C,Font,X0+I*Size+O,Y+O,Size,Size,Pass?Color:FLinearColor(0,0,0,.7f),FVector2D((Code%16)/16.f,(Code/16)/8.f),FVector2D(1/16.f,1/8.f));}}
}

void UMareArcade::DrawScreen(UCanvas* C,int32 Width,int32 Height)
{
 if(!C || Game<0)return;Scale=float(Width)/MareArc::VW;
 const FLinearColor White(1,1,1),Yellow(1,.85f,.2f),Red(1,.3f,.25f),Cyan(.5f,.95f,1);
 if(Game==0){const FMareJangada& J=Jangada;
  // River scrolling down between sand banks.
  for(int32 TY=-1;TY<3;++TY)for(int32 TX=0;TX<3;++TX)DrawSprite(C,Tex(TEXT("T_Arc_J_Water")),TX*128.f,TY*128.f+J.Scroll,128,128);
  for(int32 TY=-1;TY<3;++TY){DrawSprite(C,Tex(TEXT("T_Arc_J_Sand")),-100,TY*128.f+J.Scroll,128,128);DrawSprite(C,Tex(TEXT("T_Arc_J_Sand")),MareArc::VW-28,TY*128.f+J.Scroll,128,128);}
  for(const auto& T:J.Things){const TCHAR* Name=T.Kind==0?TEXT("T_Arc_J_Rock1"):T.Kind==1?TEXT("T_Arc_J_Boat"):T.Kind==2?TEXT("T_Arc_J_Fish"):TEXT("T_Arc_J_FishGold");
   const float S=T.Kind==0?34:T.Kind==1?58:26;const float H=T.Kind==0?S:S*.5f;
   DrawSprite(C,Tex(Name),T.X-S*.5f,T.Y-H*.5f,S,H);}
  if(J.Hurt<=0 || FMath::Fmod(J.Hurt,.2f)<.1f)DrawSprite(C,Tex(TEXT("T_Arc_J_Raft")),J.X-14,FMareJangada::RaftY-28,28,56);
  DrawText(C,FString::Printf(TEXT("PONTOS %05d"),J.Points()),8,6,8,White);
  DrawText(C,FString::Printf(TEXT("RECORDE %05d"),FMath::Max(Record,J.Points())),MareArc::VW-8-13*8,6,8,Yellow);
  FString Hearts;for(int32 I=0;I<J.Lives;++I)Hearts+=TEXT("* ");DrawText(C,Hearts,8,18,8,Red);
  if(J.Time<2.5f)DrawText(C,TEXT("A / D REMA"),MareArc::VW*.5f,110,10,Cyan,true);}
 else{const FMarePinball& P=Pinball;
  // Table: 640x480 drawn into a 1024x512 texture (pow2 padding, centred).
  DrawSprite(C,Tex(TEXT("T_Arc_P_Table")),0,0,MareArc::VW,MareArc::VH,FLinearColor::White,FVector2D(192/1024.f,16/512.f),FVector2D(640/1024.f,480/512.f));
  for(int32 I=0;I<3;++I){const float X=FMarePinball::LaneX(I);
   C->K2_DrawTexture(nullptr,FVector2D((X-3)*Scale,31*Scale),FVector2D(6*Scale,6*Scale),FVector2D(0,0),FVector2D(1,1),P.bLanes[I]?FLinearColor(1,.85f,.2f):FLinearColor(.25f,.2f,.1f),BLEND_Translucent);}
  for(int32 I=0;I<3;++I){const FVector2D B=FMarePinball::BumperPos(I);const float R=FMarePinball::BumperR+(P.Flash[I]>0?1.5f:0);
   DrawSprite(C,Tex(TEXT("T_Arc_P_Bumper")),B.X-R,B.Y-R,R*2,R*2,P.Flash[I]>0?FLinearColor(1.6f,1.6f,1.6f):FLinearColor::White);}
  // Flippers: the sprite's pivot (x 16 of 128) on the pivot point; the right one mirrored.
  const float FW=FMarePinball::FlipLen*128.f/104.f,FH=FW*.42f;
  for(int32 Side=0;Side<2;++Side){const FVector2D Pv=FMarePinball::Pivot(Side);
   if(Side==0)DrawSprite(C,Tex(TEXT("T_Arc_P_Flipper")),Pv.X-FW*16/128.f,Pv.Y-FH*.5f,FW,FH,FLinearColor::White,FVector2D(0,0),FVector2D(1,1),P.Flip[0],FVector2D(16/128.f,.5f));
   else DrawSprite(C,Tex(TEXT("T_Arc_P_Flipper")),Pv.X-FW*112/128.f,Pv.Y-FH*.5f,FW,FH,FLinearColor::White,FVector2D(1,0),FVector2D(-1,1),-P.Flip[1],FVector2D(112/128.f,.5f));}
  DrawSprite(C,Tex(TEXT("T_Arc_P_Ball")),P.Ball.X-FMarePinball::BallR-1,P.Ball.Y-FMarePinball::BallR-1,FMarePinball::BallR*2+2,FMarePinball::BallR*2+2);
  // Score panel on the right of the table.
  DrawText(C,TEXT("PONTOS"),246,40,8,Cyan);DrawText(C,FString::Printf(TEXT("%06d"),P.Points()),246,54,8,White);
  DrawText(C,TEXT("BOLAS"),246,84,8,Cyan);DrawText(C,FString::Printf(TEXT("%d"),FMath::Max(P.Balls,0)),246,98,8,Red);
  DrawText(C,TEXT("RECORDE"),246,128,8,Cyan);DrawText(C,FString::Printf(TEXT("%06d"),FMath::Max(Record,P.Points())),246,142,8,Yellow);
  DrawText(C,TEXT("PINBALL"),8,40,8,Yellow);DrawText(C,TEXT("DO FAROL"),8,54,8,Yellow);
  if(P.bInLane && P.Vel.Size()<40){DrawText(C,TEXT("ESPACO"),8,180,8,White);DrawText(C,TEXT("LANCA"),8,194,8,White);}}
 if(Over>0){C->K2_DrawTexture(nullptr,FVector2D(0,0),FVector2D(Width,Height),FVector2D(0,0),FVector2D(1,1),FLinearColor(0,0,0,.6f),BLEND_Translucent);
  DrawText(C,TEXT("FIM DE JOGO"),MareArc::VW*.5f,70,16,Yellow,true);
  DrawText(C,FString::Printf(TEXT("%d PONTOS"),Final),MareArc::VW*.5f,104,12,White,true);
  if(bRecord)DrawText(C,TEXT("NOVO RECORDE!"),MareArc::VW*.5f,132,12,Red,true);
  DrawText(C,TEXT("ESPACO: DE NOVO   Q: SAIR"),MareArc::VW*.5f,180,8,Cyan,true);}
}

FString UMareArcade::QA(const FString& Cmd)
{
 FString A,B;if(!Cmd.Split(TEXT(":"),&A,&B))A=Cmd;
 if(A==TEXT("start")){auto PC=GetWorld()->GetFirstPlayerController();return Start(PC,B.IsEmpty()?-1:FCString::Atoi(*B))?TEXT("ok"):TEXT("refused");}
 if(A==TEXT("end")){if(IsPlaying()){Finish();Stop(FString());}return ArcSim(GetWorld())?ArcSim(GetWorld())->LastMessage:FString();}
 if(A==TEXT("play")){   // a quick scripted game for photos: steer away from rocks / swing at whatever peeks out
  const float Seconds=B.IsEmpty()?6:FCString::Atof(*B);
  for(float T=0;T<Seconds && IsPlaying() && Over<=0;T+=1/30.f){
   if(Game==0){float Steer=0;for(const auto& Th:Jangada.Things)if(Th.Kind<2 && Th.Y>120 && Th.Y<200 && FMath::Abs(Th.X-Jangada.X)<30)Steer=Th.X>Jangada.X?-1:1;
    if(Jangada.Step(1/30.f,Steer,Rng)&8){Finish();Over=4;}}
   else{const FMarePinball& P=Pinball;const bool bNear=P.Vel.Y>0 && P.Ball.Y>182 && P.Ball.Y<212;
    if(Pinball.Step(1/30.f,bNear && P.Ball.X<152,bNear && P.Ball.X>=152,P.bInLane)&8){Finish();Over=4;}}}
  if(Screen)Screen->UpdateResource();return QA(TEXT("state"));}
 if(A==TEXT("state"))return FString::Printf(TEXT("playing=%d game=%d jangada=%d/%d lives=%d pinball=%d balls=%d bumps=%d over=%.1f record=%d cabinets=%d"),IsPlaying(),Game,
  Jangada.Points(),Jangada.Fish,Jangada.Lives,Pinball.Points(),Pinball.Balls,Pinball.Bumps,Over,Record,(Cabinets.Num()>0 && IsValid(Cabinets[0]))+(Cabinets.Num()>1 && IsValid(Cabinets[1])));
 return TEXT("start:0|1, play:seconds, end, state");
}
