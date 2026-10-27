using UnrealBuildTool;
public class MareAltaTarget : TargetRules {
 public MareAltaTarget(TargetInfo Target) : base(Target) {
  Type=TargetType.Game;DefaultBuildSettings=BuildSettingsVersion.Latest;IncludeOrderVersion=EngineIncludeOrderVersion.Latest;
  ExtraModuleNames.Add("MareAlta");
 }
}
