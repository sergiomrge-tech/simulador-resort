using UnrealBuildTool;
public class MareAltaEditorTarget : TargetRules {
 public MareAltaEditorTarget(TargetInfo Target) : base(Target) {
  Type=TargetType.Editor;DefaultBuildSettings=BuildSettingsVersion.Latest;IncludeOrderVersion=EngineIncludeOrderVersion.Latest;
  ExtraModuleNames.Add("MareAlta");
 }
}
