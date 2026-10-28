using UnrealBuildTool;
public class MareAlta : ModuleRules {
 public MareAlta(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
  PublicDependencyModuleNames.AddRange(new[]{"Core","CoreUObject","Engine","InputCore","Json","JsonUtilities","Slate","SlateCore","NavigationSystem","AIModule","AudioMixer","AnimationCore"});
 }
}
