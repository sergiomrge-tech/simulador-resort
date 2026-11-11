#include "MareOptions.h"
#include "MareLoc.h"
#include "Camera/CameraComponent.h"
#include "CoreGlobals.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "Internationalization/Culture.h"
#include "Internationalization/Internationalization.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

#define LOCTEXT_NAMESPACE "MareOptions"
namespace MareOptionsData
{
 const TPair<const TCHAR*,int32 FMareOptions::*> Ints[]={{TEXT("preset"),&FMareOptions::Preset},{TEXT("shadows"),&FMareOptions::Shadows},
  {TEXT("global_illumination"),&FMareOptions::GlobalIllumination},{TEXT("reflections"),&FMareOptions::Reflections},{TEXT("post_process"),&FMareOptions::PostProcess},
  {TEXT("textures"),&FMareOptions::Textures},{TEXT("foliage"),&FMareOptions::Foliage},{TEXT("anti_aliasing"),&FMareOptions::AntiAliasing},
  {TEXT("window_mode"),&FMareOptions::WindowMode},{TEXT("frame_limit"),&FMareOptions::FrameLimit},{TEXT("pad_glyphs"),&FMareOptions::PadGlyphs},
  {TEXT("frame_generation"),&FMareOptions::FrameGeneration},{TEXT("view_distance"),&FMareOptions::ViewDistance},{TEXT("effects"),&FMareOptions::Effects},
  {TEXT("shading"),&FMareOptions::Shading},{TEXT("model_detail"),&FMareOptions::ModelDetail},{TEXT("crowd"),&FMareOptions::Crowd}};
 const TPair<const TCHAR*,float FMareOptions::*> Floats[]={{TEXT("resolution_scale"),&FMareOptions::ResolutionScale},{TEXT("field_of_view"),&FMareOptions::FieldOfView},{TEXT("mouse_sensitivity"),&FMareOptions::MouseSensitivity},{TEXT("gamepad_sensitivity"),&FMareOptions::GamepadSensitivity},{TEXT("text_scale"),&FMareOptions::TextScale}};
 const TPair<const TCHAR*,bool FMareOptions::*> Bools[]={{TEXT("vsync"),&FMareOptions::bVSync},{TEXT("invert_y"),&FMareOptions::bInvertY},{TEXT("tips"),&FMareOptions::bTips},{TEXT("color_safe"),&FMareOptions::bColorSafe},{TEXT("language_chosen"),&FMareOptions::bLanguageChosen}};
 /** Legacy mappings (DefaultInput.ini) driven by each remappable action; axes carry their scale. */
 struct FBinding{FName Name;bool bAxis;float Scale;};
 TArray<FBinding> Bindings(FName Action)
 {
  static const TMap<FName,TArray<FBinding>> Map={
   {TEXT("MoveForward"),{{TEXT("Forward"),true,1.f}}},{TEXT("MoveBack"),{{TEXT("Forward"),true,-1.f}}},
   {TEXT("MoveLeft"),{{TEXT("Right"),true,-1.f}}},{TEXT("MoveRight"),{{TEXT("Right"),true,1.f}}},
   {TEXT("Jump"),{{TEXT("Jump"),false,0.f},{TEXT("SwimVertical"),true,1.f}}},
   {TEXT("Sprint"),{{TEXT("Sprint"),false,0.f},{TEXT("SwimVertical"),true,-1.f}}},
   {TEXT("Dive"),{{TEXT("SwimVertical"),true,-1.f}}},
   {TEXT("Interact"),{{TEXT("Interact"),false,0.f}}},{TEXT("Phone"),{{TEXT("Phone"),false,0.f}}}};
  const auto* Found=Map.Find(Action);return Found?*Found:TArray<FBinding>();
 }
 // Plugin upscalers are only offered when their console variables exist.
 const TCHAR* DLSSVar=TEXT("r.NGX.DLSS.Enable");
 const TCHAR* FSRVars[]={TEXT("r.FidelityFX.FSR4.Enabled"),TEXT("r.FidelityFX.FSR3.Enabled"),TEXT("r.FidelityFX.FSR.Enabled")};
 const TCHAR* FrameGenVar=TEXT("r.Streamline.DLSSG.Enable");
 void SetVar(const TCHAR* Name,int32 Value){if(auto Var=IConsoleManager::Get().FindConsoleVariable(Name))if(Var->GetInt()!=Value)Var->Set(Value,ECVF_SetByCode);}
 void SetFloat(const TCHAR* Name,float Value){if(auto Var=IConsoleManager::Get().FindConsoleVariable(Name))if(!FMath::IsNearlyEqual(Var->GetFloat(),Value))Var->Set(Value,ECVF_SetByCode);}
 /** Calls a static UFUNCTION of an optional plugin's Blueprint library; Read gets the parameter block afterwards. */
 bool CallLibrary(const TCHAR* ClassPath,const TCHAR* Function,TFunctionRef<void(UFunction*,uint8*)> Read)
 {
  UClass* Library=FindObject<UClass>(nullptr,ClassPath);UFunction* Func=Library?Library->FindFunctionByName(Function):nullptr;
  if(!Func || Func->NumParms>2 || !Func->HasAnyFunctionFlags(FUNC_Static))return false;
  TArray<uint8,TInlineAllocator<64>> Params;Params.SetNumZeroed(FMath::Max<int32>(Func->ParmsSize,1));
  for(TFieldIterator<FProperty> It(Func);It && It->HasAnyPropertyFlags(CPF_Parm);++It)It->InitializeValue_InContainer(Params.GetData());
  Library->GetDefaultObject()->ProcessEvent(Func,Params.GetData());Read(Func,Params.GetData());
  for(TFieldIterator<FProperty> It(Func);It && It->HasAnyPropertyFlags(CPF_Parm);++It)It->DestroyValue_InContainer(Params.GetData());
  return true;
 }
 bool CallBool(const TCHAR* ClassPath,const TCHAR* Function)
 {
  bool bResult=false;
  CallLibrary(ClassPath,Function,[&bResult](UFunction* Func,uint8* Params){if(auto Ret=CastField<FBoolProperty>(Func->GetReturnProperty()))bResult=Ret->GetPropertyValue_InContainer(Params);});
  return bResult;
 }
 void ApplyUpscaler(const FString& Wanted,int32 FrameGeneration)
 {
  const FString Use=FMareOptions::Upscalers().Contains(Wanted)?Wanted:FString(TEXT("TSR"));
  SetVar(DLSSVar,Use==TEXT("DLSS"));for(const TCHAR* Name:FSRVars)SetVar(Name,Use==TEXT("FSR"));
  // Reflex comes on with it by itself (t.Streamline.Reflex.Auto).
  SetVar(FrameGenVar,FMareOptions::FrameGenerationSupported()?FMath::Clamp(FrameGeneration,0,2):0);
 }
 FMareOptions& Live()
 {
  static FMareOptions Options=[](){
   if(FMareOptions::IsQARun())return FMareOptions::Defaults();
   FMareOptions Result=FMareOptions::FromEngine();Result.LoadFile(FMareOptions::DefaultPath());return Result;}();
  // -culture=en / -culture=zh-Hans on the command line (QA captures of the translations) wins over the saved choice.
  static bool bCultureArg=[](){FString Arg;if(FParse::Value(FCommandLine::Get(),TEXT("culture="),Arg) && FMareOptions::Cultures().Contains(Arg))Options.Culture=Arg;return true;}();
  return Options;
 }
}

const TArray<FMareOptions::FAction>& FMareOptions::Actions()
{
 static const TArray<FAction> List={
  {TEXT("MoveForward"),LOCTEXT("MoveForward","Andar para frente"),EKeys::W},{TEXT("MoveBack"),LOCTEXT("MoveBack","Andar para trás"),EKeys::S},
  {TEXT("MoveLeft"),LOCTEXT("MoveLeft","Andar para a esquerda"),EKeys::A},{TEXT("MoveRight"),LOCTEXT("MoveRight","Andar para a direita"),EKeys::D},
  {TEXT("Jump"),LOCTEXT("Jump","Pular / subir nadando"),EKeys::SpaceBar},{TEXT("Sprint"),LOCTEXT("Sprint","Correr"),EKeys::LeftShift},
  {TEXT("Dive"),LOCTEXT("Dive","Mergulhar"),EKeys::LeftControl},{TEXT("Interact"),LOCTEXT("Interact","Interagir"),EKeys::E},
  {TEXT("Phone"),LOCTEXT("Phone","Celular"),EKeys::B}};
 return List;
}
const TArray<int32>& FMareOptions::FrameLimits(){static const TArray<int32> List={30,60,120,144,0};return List;}
namespace MareOptionsData
{
 /** Every culture the game can offer, with its own name; one is listed only when Content/Localization/Mare/<culture>.json
  * exists, so a new language is a new file (tools/ue58/i18n_extract.py). Order: Steam's most played languages. */
 const TPair<const TCHAR*,const TCHAR*> KnownCultures[]={
  {TEXT("pt-BR"),TEXT("Português (Brasil)")},{TEXT("en"),TEXT("English")},{TEXT("es"),TEXT("Español")},
  {TEXT("zh-Hans"),TEXT("简体中文")},{TEXT("ru"),TEXT("Русский")},{TEXT("de"),TEXT("Deutsch")},{TEXT("fr"),TEXT("Français")},
  {TEXT("ja"),TEXT("日本語")},{TEXT("ko"),TEXT("한국어")},{TEXT("it"),TEXT("Italiano")},{TEXT("pl"),TEXT("Polski")},
  {TEXT("nl"),TEXT("Nederlands")},{TEXT("pt-PT"),TEXT("Português (Portugal)")},
  {TEXT("cs"),TEXT("Čeština")},{TEXT("hu"),TEXT("Magyar")},{TEXT("ro"),TEXT("Română")},{TEXT("da"),TEXT("Dansk")},
  {TEXT("fi"),TEXT("Suomi")}};
}
const TArray<FString>& FMareOptions::Cultures()
{
 static const TArray<FString> List=[](){TArray<FString> Out;
  for(const auto& Pair:MareOptionsData::KnownCultures)
   if(FCString::Strcmp(Pair.Key,TEXT("pt-BR"))==0 || FPaths::FileExists(FPaths::ProjectContentDir()/TEXT("Localization/Mare")/(FString(Pair.Key)+TEXT(".json"))))Out.Add(Pair.Key);
  return Out;}();
 return List;
}
FText FMareOptions::CultureName(const FString& Name)
{
 for(const auto& Pair:MareOptionsData::KnownCultures)if(Name==Pair.Key)return FText::AsCultureInvariant(Pair.Value);
 return FText::AsCultureInvariant(Name);
}
TArray<FString> FMareOptions::Upscalers()
{
 TArray<FString> List={TEXT("TSR")};auto& Console=IConsoleManager::Get();
 if(Console.FindConsoleVariable(MareOptionsData::DLSSVar) && DLSSSupported())List.Add(TEXT("DLSS"));
 for(const TCHAR* Name:MareOptionsData::FSRVars)if(Console.FindConsoleVariable(Name)){List.Add(TEXT("FSR"));break;}
 return List;
}
bool FMareOptions::bEngineReady=false;
bool FMareOptions::DLSSSupported(){return bEngineReady && !IsRunningCommandlet() && MareOptionsData::CallBool(TEXT("/Script/DLSSBlueprint.DLSSLibrary"),TEXT("IsDLSSSupported"));}
void FMareOptions::ApplyNvidia()
{
 FMareOptions& Options=MareOptionsData::Live();
 // First run on an NVIDIA RTX card (no options file yet, not a QA run): DLSS upscaling and, on RTX 40+, frame generation in auto mode.
 if(!IsQARun() && !FPaths::FileExists(DefaultPath())){if(DLSSSupported())Options.Upscaler=TEXT("DLSS");if(FrameGenerationSupported())Options.FrameGeneration=2;}
 MareOptionsData::ApplyUpscaler(Options.Upscaler,Options.FrameGeneration);
}
bool FMareOptions::FrameGenerationSupported()
{
 return bEngineReady && !IsRunningCommandlet() && IConsoleManager::Get().FindConsoleVariable(MareOptionsData::FrameGenVar)
  && MareOptionsData::CallBool(TEXT("/Script/StreamlineDLSSGBlueprint.StreamlineLibraryDLSSG"),TEXT("IsDLSSGSupported"));
}
float FMareOptions::PresentedFrameRate()
{
 float Rate=0.f;
 MareOptionsData::CallLibrary(TEXT("/Script/StreamlineDLSSGBlueprint.StreamlineLibraryDLSSG"),TEXT("GetDLSSGFrameTiming"),[&Rate](UFunction* Func,uint8* Params){
  if(auto Prop=CastField<FFloatProperty>(Func->FindPropertyByName(TEXT("FrameRateInHertz"))))Rate=Prop->GetPropertyValue_InContainer(Params);});
 return Rate;
}
FMareOptions FMareOptions::Defaults()
{
 // Same values as Config/DefaultGameUserSettings.ini.
 FMareOptions Options;for(const auto& Action:Actions())Options.Keys.Add(Action.Id,Action.Default);
 return Options;
}
FMareOptions FMareOptions::FromEngine()
{
 FMareOptions Options=Defaults();
 if(auto Settings=GEngine?UGameUserSettings::GetGameUserSettings():nullptr){
  const int32 Overall=Settings->GetOverallScalabilityLevel();
  Options.Preset=Overall>=0?Overall:Settings->GetViewDistanceQuality();
  Options.Shadows=Settings->GetShadowQuality();Options.GlobalIllumination=Settings->GetGlobalIlluminationQuality();Options.Reflections=Settings->GetReflectionQuality();
  Options.PostProcess=Settings->GetPostProcessingQuality();Options.Textures=Settings->GetTextureQuality();Options.Foliage=Settings->GetFoliageQuality();Options.AntiAliasing=Settings->GetAntiAliasingQuality();
  Options.ViewDistance=Settings->GetViewDistanceQuality();Options.Effects=Settings->GetVisualEffectQuality();Options.Shading=Settings->GetShadingQuality();
  float Normalized,Value,Min,Max;Settings->GetResolutionScaleInformationEx(Normalized,Value,Min,Max);Options.ResolutionScale=Value;
  Options.Resolution=Settings->GetScreenResolution();Options.WindowMode=Settings->GetFullscreenMode();
  Options.bVSync=Settings->IsVSyncEnabled();Options.FrameLimit=FMath::RoundToInt(Settings->GetFrameRateLimit());
 }
 Options.Sanitize();return Options;
}
FString FMareOptions::DefaultPath(){return FPaths::ProjectSavedDir()/TEXT("MareOptions.json");}
bool FMareOptions::LoadFile(const FString& Path)
{
 FString Text;TSharedPtr<FJsonObject> Json;
 if(!FFileHelper::LoadFileToString(Text,*Path) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json) || !Json.IsValid())return false;
 using namespace MareOptionsData;double Number;
 for(const auto& Field:Ints)if(Json->TryGetNumberField(Field.Key,Number))this->*Field.Value=FMath::RoundToInt(FMath::Clamp(Number,-1e6,1e6));
 for(const auto& Field:Floats)if(Json->TryGetNumberField(Field.Key,Number))this->*Field.Value=float(FMath::Clamp(Number,-1e6,1e6));
 for(const auto& Field:Bools)Json->TryGetBoolField(Field.Key,this->*Field.Value);
 if(Json->TryGetNumberField(TEXT("resolution_x"),Number))Resolution.X=FMath::RoundToInt(FMath::Clamp(Number,0.,1e5));
 if(Json->TryGetNumberField(TEXT("resolution_y"),Number))Resolution.Y=FMath::RoundToInt(FMath::Clamp(Number,0.,1e5));
 Json->TryGetStringField(TEXT("upscaler"),Upscaler);Json->TryGetStringField(TEXT("culture"),Culture);
 const TSharedPtr<FJsonObject>* KeyObject=nullptr;
 if(Json->TryGetObjectField(TEXT("keys"),KeyObject))for(const auto& Action:Actions()){FString Name;
  if((*KeyObject)->TryGetStringField(Action.Id.ToString(),Name)){const FKey Loaded(*Name);if(Loaded.IsValid())Keys.Add(Action.Id,Loaded);}}
 Sanitize();return true;
}
bool FMareOptions::SaveFile(const FString& Path)const
{
 using namespace MareOptionsData;auto Json=MakeShared<FJsonObject>();
 Json->SetNumberField(TEXT("version"),1);
 for(const auto& Field:Ints)Json->SetNumberField(Field.Key,this->*Field.Value);
 for(const auto& Field:Floats)Json->SetNumberField(Field.Key,this->*Field.Value);
 for(const auto& Field:Bools)Json->SetBoolField(Field.Key,this->*Field.Value);
 Json->SetNumberField(TEXT("resolution_x"),Resolution.X);Json->SetNumberField(TEXT("resolution_y"),Resolution.Y);
 Json->SetStringField(TEXT("upscaler"),Upscaler);Json->SetStringField(TEXT("culture"),Culture);
 auto KeyObject=MakeShared<FJsonObject>();for(const auto& Action:Actions())KeyObject->SetStringField(Action.Id.ToString(),Key(Action.Id).GetFName().ToString());
 Json->SetObjectField(TEXT("keys"),KeyObject);
 FString Text;if(!FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text)))return false;
 const FString Temp=Path+TEXT(".tmp");
 return FFileHelper::SaveStringToFile(Text,*Temp,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM) && IFileManager::Get().Move(*Path,*Temp,true);
}
void FMareOptions::Sanitize()
{
 for(int32* Level:{&Preset,&Shadows,&GlobalIllumination,&Reflections,&PostProcess,&Textures,&Foliage,&AntiAliasing,&ViewDistance,&Effects,&Shading,&ModelDetail})*Level=FMath::Clamp(*Level,0,3);
 Crowd=FMath::Clamp(Crowd,0,2);
 ResolutionScale=FMath::Clamp(FMath::RoundToFloat(ResolutionScale),25.f,100.f);
 if(Upscaler!=TEXT("TSR") && Upscaler!=TEXT("DLSS") && Upscaler!=TEXT("FSR"))Upscaler=TEXT("TSR");
 FrameGeneration=FMath::Clamp(FrameGeneration,0,2);
 Resolution=FIntPoint(FMath::Clamp(Resolution.X,640,16384),FMath::Clamp(Resolution.Y,480,16384));
 WindowMode=FMath::Clamp(WindowMode,0,2);
 if(!FrameLimits().Contains(FrameLimit)){
  // Unknown caps snap to the nearest listed one; very high or non-positive means unlimited.
  int32 Best=0;if(FrameLimit>0 && FrameLimit<=200)for(int32 Limit:FrameLimits())if(Limit>0 && (Best==0 || FMath::Abs(Limit-FrameLimit)<FMath::Abs(Best-FrameLimit)))Best=Limit;
  FrameLimit=Best;
 }
 FieldOfView=FMath::Clamp(FMath::RoundToFloat(FieldOfView),70.f,110.f);
 TextScale=FMath::Clamp(FMath::RoundToFloat(TextScale*20.f)/20.f,.85f,1.5f);
 MouseSensitivity=FMath::Clamp(MouseSensitivity,.1f,5.f);
 GamepadSensitivity=FMath::Clamp(GamepadSensitivity,.2f,3.f);
 PadGlyphs=FMath::Clamp(PadGlyphs,0,1);
 if(!Cultures().Contains(Culture))Culture=TEXT("pt-BR");
 // Missing or invalid keys go back to their default; a duplicated key resets the whole map.
 TMap<FName,FKey> Clean;TSet<FKey> Used;bool bDuplicate=false;
 for(const auto& Action:Actions()){const FKey* Found=Keys.Find(Action.Id);const FKey Value=Found && Found->IsValid() && !Found->IsGamepadKey()?*Found:Action.Default;
  bDuplicate|=Used.Contains(Value);Used.Add(Value);Clean.Add(Action.Id,Value);}
 if(bDuplicate){Clean.Reset();for(const auto& Action:Actions())Clean.Add(Action.Id,Action.Default);}
 Keys=MoveTemp(Clean);
}
bool FMareOptions::Equals(const FMareOptions& Other)const
{
 using namespace MareOptionsData;
 for(const auto& Field:Ints)if(this->*Field.Value!=Other.*Field.Value)return false;
 for(const auto& Field:Floats)if(!FMath::IsNearlyEqual(this->*Field.Value,Other.*Field.Value,1e-4f))return false;
 for(const auto& Field:Bools)if(this->*Field.Value!=Other.*Field.Value)return false;
 for(const auto& Action:Actions())if(Key(Action.Id)!=Other.Key(Action.Id))return false;
 return Resolution==Other.Resolution && Upscaler==Other.Upscaler && Culture==Other.Culture;
}
bool FMareOptions::IsCustomPreset()const
{
 for(int32 Level:{Shadows,GlobalIllumination,Reflections,PostProcess,Textures,Foliage,AntiAliasing,ViewDistance,Effects,Shading,ModelDetail})if(Level!=Preset)return true;
 return false;
}
void FMareOptions::SetPreset(int32 Level){Preset=Shadows=GlobalIllumination=Reflections=PostProcess=Textures=Foliage=AntiAliasing=ViewDistance=Effects=Shading=ModelDetail=FMath::Clamp(Level,0,3);}
// 08/11 (reference tip 13, busier streets): 4 / 8 / 16 in pairs and trios (was 3 / 6 / 12); distant ones still hide.
int32 FMareOptions::CrowdWalkers()const{static const int32 Walkers[]={4,8,16};return Walkers[FMath::Clamp(Crowd,0,2)];}
float FMareOptions::CrowdDrawDistance()const{static const float Reach[]={3500.f,5000.f,8000.f};return Reach[FMath::Clamp(Crowd,0,2)];}
FKey FMareOptions::Key(FName Action)const
{
 if(const FKey* Found=Keys.Find(Action))return *Found;
 const FAction* Default=Actions().FindByPredicate([Action](const FAction& Item){return Item.Id==Action;});
 return Default?Default->Default:EKeys::Invalid;
}
void FMareOptions::Bind(FName Action,FKey NewKey)
{
 if(!NewKey.IsValid() || !Actions().ContainsByPredicate([Action](const FAction& Item){return Item.Id==Action;}))return;
 const FKey Old=Key(Action);
 for(const auto& Item:Actions())if(Item.Id!=Action && Key(Item.Id)==NewKey)Keys.Add(Item.Id,Old);
 Keys.Add(Action,NewKey);
}
bool FMareOptions::IsQARun()
{
 const TCHAR* Cmd=FCommandLine::Get();
 return GIsAutomationTesting || FParse::Param(Cmd,TEXT("MareGraphicsQA")) || FParse::Param(Cmd,TEXT("MareIntroQA")) || FParse::Param(Cmd,TEXT("MarePreviewQA")) || FParse::Param(Cmd,TEXT("MareBench")) || FString(Cmd).Contains(TEXT("MareScriptQA="));
}
const FMareOptions& FMareOptions::Get(){return MareOptionsData::Live();}
void FMareOptions::Set(const FMareOptions& Options)
{
 auto& Live=MareOptionsData::Live();Live=Options;Live.Sanitize();
 if(!IsQARun() && !Live.SaveFile(DefaultPath()))UE_LOG(LogTemp,Warning,TEXT("MareOptions: could not save %s"),*DefaultPath());
}
void FMareOptions::KeepLumenSafe(){MareOptionsData::SetVar(TEXT("r.Lumen.AsyncCompute"),0);}
void FMareOptions::ApplyGraphics()const
{
 auto Settings=GEngine?UGameUserSettings::GetGameUserSettings():nullptr;if(!Settings)return;
 Settings->SetOverallScalabilityLevel(Preset);
 Settings->SetShadowQuality(Shadows);Settings->SetGlobalIlluminationQuality(GlobalIllumination);Settings->SetReflectionQuality(Reflections);
 Settings->SetPostProcessingQuality(PostProcess);Settings->SetTextureQuality(Textures);Settings->SetFoliageQuality(Foliage);Settings->SetAntiAliasingQuality(AntiAliasing);
 Settings->SetViewDistanceQuality(ViewDistance);Settings->SetVisualEffectQuality(Effects);Settings->SetShadingQuality(Shading);
 Settings->SetResolutionScaleValueEx(ResolutionScale);   // after the overall level, which also sets the 3D scale
 Settings->SetVSyncEnabled(bVSync);Settings->SetFrameRateLimit(float(FrameLimit));
 Settings->ApplyNonResolutionSettings();Settings->SaveSettings();
 MareOptionsData::ApplyUpscaler(Upscaler,FrameGeneration);ApplyDetail();KeepLumenSafe();
}
void FMareOptions::ApplyDetail()const
{
 // Lower detail switches models to their simpler LODs closer to the camera.
 static const float MeshScale[]={2.f,1.5f,1.f,.8f};static const int32 SkinBias[]={2,1,0,0};
 MareOptionsData::SetFloat(TEXT("r.StaticMeshLODDistanceScale"),MeshScale[FMath::Clamp(ModelDetail,0,3)]);
 MareOptionsData::SetVar(TEXT("r.SkeletalMeshLODBias"),SkinBias[FMath::Clamp(ModelDetail,0,3)]);
 // MetaHuman hair physics (Niagara strand solver) only on Epic effects: 04/11 EXE, off = beach 59 -> 62, kiosk 56 -> 61 FPS.
 MareOptionsData::SetVar(TEXT("r.HairStrands.Simulation"),Effects>=3?1:0);
}
bool FMareOptions::ApplyDisplay()const
{
 auto Settings=GEngine?UGameUserSettings::GetGameUserSettings():nullptr;if(!Settings)return false;
 const EWindowMode::Type Mode=static_cast<EWindowMode::Type>(WindowMode);
 const bool bChanged=Settings->GetScreenResolution()!=Resolution || Settings->GetFullscreenMode()!=Mode;
 if(!bChanged)return false;
 Settings->SetScreenResolution(Resolution);Settings->SetFullscreenMode(Mode);Settings->ApplyResolutionSettings(false);
 return true;
}
void FMareOptions::ApplyCulture()const
{
 // In the editor this would switch the editor's own language: only the game applies it.
 if(GIsEditor){UE_LOG(LogTemp,Log,TEXT("MareOptions: culture %s saved, applied only outside the editor."),*Culture);return;}
 if(FInternationalization::Get().GetCurrentCulture()->GetName()!=Culture)FInternationalization::Get().SetCurrentCulture(Culture);
 GConfig->SetString(TEXT("Internationalization"),TEXT("Culture"),*Culture,GGameUserSettingsIni);GConfig->Flush(false,GGameUserSettingsIni);
 MareLoc::Reload();
}
void FMareOptions::ApplyKeys(UPlayerInput* Input)const
{
 if(!Input)return;
 Input->ForceRebuildingKeyMaps(true);   // project mappings, then the remaps relative to them
 for(const auto& Action:Actions()){const FKey Wanted=Key(Action.Id);if(Wanted==Action.Default)continue;
  for(const auto& Binding:MareOptionsData::Bindings(Action.Id)){
   if(Binding.bAxis){Input->RemoveAxisMapping(FInputAxisKeyMapping(Binding.Name,Action.Default,Binding.Scale));Input->AddAxisMapping(FInputAxisKeyMapping(Binding.Name,Wanted,Binding.Scale));}
   else{Input->RemoveActionMapping(FInputActionKeyMapping(Binding.Name,Action.Default));Input->AddActionMapping(FInputActionKeyMapping(Binding.Name,Wanted));}}}
 Input->ForceRebuildingKeyMaps(false);
}
void FMareOptions::ApplyToPlayer(APlayerController* Player)const
{
 if(!Player)return;ApplyKeys(Player->PlayerInput);
 if(auto Pawn=Player->GetPawn())if(auto Camera=Pawn->FindComponentByClass<UCameraComponent>())Camera->SetFieldOfView(FieldOfView);
}
void FMareOptions::ApplyStartup()
{
 static bool bDone=false;KeepLumenSafe();if(bDone)return;bDone=true;
 const FMareOptions& Options=Get();
 // The packaged game re-applies its saved graphics (the editor keeps its own viewport settings).
 if(!GIsEditor && !IsQARun() && FPaths::FileExists(DefaultPath()))Options.ApplyGraphics();
 else{MareOptionsData::ApplyUpscaler(Options.Upscaler,Options.FrameGeneration);Options.ApplyDetail();}
 Options.ApplyCulture();KeepLumenSafe();
}
#undef LOCTEXT_NAMESPACE
