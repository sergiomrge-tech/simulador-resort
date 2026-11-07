#include "Modules/ModuleManager.h"
#include "Misc/CoreDelegates.h"
#include "Containers/Ticker.h"
#include "MareOptions.h"

/** Game module: once the engine is up, the DLSS / frame generation choice is applied again with the real support
 *  answer. The NVIDIA Blueprint libraries initialize in their own PostEngineInit step, so the query waits one more
 *  frame (04/11: asked inside the broadcast they logged "should not be called before PostEngineInit" and said no). */
class FMareAltaModule : public FDefaultGameModuleImpl
{
public:
 virtual void StartupModule() override
 {
  FCoreDelegates::OnPostEngineInit.AddLambda([](){
   FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float){FMareOptions::bEngineReady=true;FMareOptions::ApplyNvidia();return false;}));});
 }
};
IMPLEMENT_PRIMARY_GAME_MODULE(FMareAltaModule, MareAlta, "MareAlta");
