#include "MareOptions.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMareOptionsFileTest,"MareAlta.Options.SaveAndReload",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FMareOptionsFileTest::RunTest(const FString& Parameters)
{
 const FString Dir=FPaths::ProjectSavedDir()/TEXT("Automation/Options")/FGuid::NewGuid().ToString(EGuidFormats::Digits);
 const FString Path=Dir/TEXT("MareOptions.json");
 // Defaults survive a round trip untouched.
 const FMareOptions Defaults=FMareOptions::Defaults();
 TestTrue(TEXT("Defaults saved"),Defaults.SaveFile(Path));
 FMareOptions Reloaded;Reloaded.Keys.Reset();
 TestTrue(TEXT("Defaults reloaded"),Reloaded.LoadFile(Path));
 TestTrue(TEXT("Defaults round trip"),Reloaded.Equals(Defaults));
 TestEqual(TEXT("Default interact key"),Reloaded.Key(TEXT("Interact")),EKeys::E);
 // Every field changed away from its default.
 FMareOptions Custom=Defaults;
 Custom.SetPreset(1);Custom.Shadows=3;Custom.GlobalIllumination=0;Custom.Reflections=2;Custom.PostProcess=3;Custom.Textures=0;Custom.Foliage=2;Custom.AntiAliasing=3;
 Custom.ResolutionScale=65.f;Custom.Upscaler=TEXT("DLSS");Custom.Resolution=FIntPoint(1920,1080);Custom.WindowMode=1;Custom.bVSync=true;Custom.FrameLimit=144;Custom.FieldOfView=100.f;
 Custom.MouseSensitivity=1.7f;Custom.bInvertY=true;Custom.Culture=TEXT("en");
 Custom.Bind(TEXT("Phone"),EKeys::Tab);
 Custom.Bind(TEXT("Interact"),EKeys::SpaceBar);   // Jump had SpaceBar: it takes E
 TestEqual(TEXT("Rebound interact"),Custom.Key(TEXT("Interact")),EKeys::SpaceBar);
 TestEqual(TEXT("Conflicting action swapped"),Custom.Key(TEXT("Jump")),EKeys::E);
 TestTrue(TEXT("Mixed groups are a custom preset"),Custom.IsCustomPreset());
 TestFalse(TEXT("Custom differs from defaults"),Custom.Equals(Defaults));
 TestTrue(TEXT("Custom saved"),Custom.SaveFile(Path));
 TestFalse(TEXT("No temporary file left"),FPaths::FileExists(Path+TEXT(".tmp")));
 FMareOptions Read=FMareOptions::Defaults();
 TestTrue(TEXT("Custom reloaded"),Read.LoadFile(Path));
 TestTrue(TEXT("Custom round trip"),Read.Equals(Custom));
 TestEqual(TEXT("Resolution kept"),Read.Resolution,FIntPoint(1920,1080));
 TestEqual(TEXT("Borderless kept"),Read.WindowMode,1);
 TestEqual(TEXT("FPS cap kept"),Read.FrameLimit,144);
 TestEqual(TEXT("FOV kept"),Read.FieldOfView,100.f);
 TestTrue(TEXT("Sensitivity kept"),FMath::IsNearlyEqual(Read.MouseSensitivity,1.7f,1e-4f));
 TestTrue(TEXT("Invert Y kept"),Read.bInvertY);
 TestEqual(TEXT("Culture kept"),Read.Culture,FString(TEXT("en")));
 TestEqual(TEXT("Upscaler name kept even without the plugin"),Read.Upscaler,FString(TEXT("DLSS")));
 TestEqual(TEXT("Phone key kept"),Read.Key(TEXT("Phone")),EKeys::Tab);
 // Presets set every group; out-of-range or broken files are sanitized.
 Read.SetPreset(3);TestFalse(TEXT("Uniform groups are not custom"),Read.IsCustomPreset());TestEqual(TEXT("Preset sets shadows"),Read.Shadows,3);
 TestTrue(TEXT("Broken file written"),FFileHelper::SaveStringToFile(TEXT("{\"preset\":9,\"shadows\":-4,\"resolution_scale\":3,\"field_of_view\":300,\"frame_limit\":75,\"window_mode\":7,")
  TEXT("\"mouse_sensitivity\":0,\"upscaler\":\"XeSS9\",\"culture\":\"xx\",\"keys\":{\"Interact\":\"NotAKey\",\"Phone\":\"W\"}}"),*Path));
 FMareOptions Clamped=FMareOptions::Defaults();
 TestTrue(TEXT("Broken file still loads"),Clamped.LoadFile(Path));
 TestEqual(TEXT("Preset clamped"),Clamped.Preset,3);TestEqual(TEXT("Group clamped"),Clamped.Shadows,0);
 TestEqual(TEXT("3D scale clamped"),Clamped.ResolutionScale,25.f);TestEqual(TEXT("FOV clamped"),Clamped.FieldOfView,110.f);
 TestEqual(TEXT("FPS cap snapped"),Clamped.FrameLimit,60);TestEqual(TEXT("Window mode clamped"),Clamped.WindowMode,2);
 TestTrue(TEXT("Sensitivity clamped"),Clamped.MouseSensitivity>=.1f);
 TestEqual(TEXT("Unknown upscaler falls back to TSR"),Clamped.Upscaler,FString(TEXT("TSR")));
 TestEqual(TEXT("Unknown culture falls back"),Clamped.Culture,FString(TEXT("pt-BR")));
 // Phone on W collides with MoveForward: the whole map goes back to defaults.
 TestEqual(TEXT("Duplicate key resets interact"),Clamped.Key(TEXT("Interact")),EKeys::E);
 TestEqual(TEXT("Duplicate key resets phone"),Clamped.Key(TEXT("Phone")),EKeys::B);
 FMareOptions Missing=FMareOptions::Defaults();
 TestFalse(TEXT("Missing file reports failure"),Missing.LoadFile(Dir/TEXT("none.json")));
 TestTrue(TEXT("Missing file keeps defaults"),Missing.Equals(Defaults));
 IFileManager::Get().DeleteDirectory(*Dir,false,true);
 return true;
}
#endif
