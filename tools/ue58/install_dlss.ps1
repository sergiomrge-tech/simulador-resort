param(
 [string]$Zip='D:/Downloads/dlss58/dlss58.zip',
 [string]$Url='https://developer.nvidia.com/downloads/assets/gameworks/downloads/secure/dlss/ue-dlss-5.8/8.9.0/2026.10.16_ue5.8_dlss4.5plugin_v8.9.0.zip'
)
# Installs the NVIDIA DLSS 4.5 plugins for UE 5.8 (plugin v8.9.0: DLSS Super Resolution, Frame Generation, Reflex) into
# unreal/MareAlta/Plugins/NVIDIA. They are not in git (about 3.5 GB, NVIDIA RTX SDK EULA). REQUIRED before opening or
# building the project: the .uproject enables them (not "Optional": in a monolithic game UE silently drops an optional
# plugin whose modules are not all compiled, e.g. DLSS's Vulkan/D3D11 ones, 04/11). On GPUs without DLSS the game hides
# the options.
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$dest=Join-Path $repo 'unreal/MareAlta/Plugins/NVIDIA'
$keep=@('DLSS','StreamlineCore','StreamlineDLSSG','StreamlineReflex','StreamlineNGXCommon')
if(-not (Test-Path $Zip)){
 New-Item -ItemType Directory -Force (Split-Path $Zip) | Out-Null
 Write-Output "Baixando $Url"
 & curl.exe -sSL -A 'Mozilla/5.0' -o $Zip $Url
 if($LASTEXITCODE -ne 0){throw "Download falhou: $LASTEXITCODE"}
}
$tmp=Join-Path (Split-Path $Zip) 'x'
if(-not (Test-Path (Join-Path $tmp 'Plugins/DLSS/DLSS.uplugin'))){
 Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
 Expand-Archive -LiteralPath $Zip -DestinationPath $tmp
}
New-Item -ItemType Directory -Force $dest | Out-Null
foreach($p in $keep){
 $target=Join-Path $dest $p
 if(Test-Path $target){Remove-Item -Recurse -Force $target}
 Copy-Item -Recurse (Join-Path $tmp "Plugins/$p") $target
 # Prebuilt modules of NVIDIA's own build (UE 5.8.0): this C++ project compiles the plugins itself against the installed
 # engine. Binaries/ThirdParty (the NGX and Streamline runtime DLLs) stays.
 Remove-Item -Recurse -Force (Join-Path $target 'Intermediate'),(Join-Path $target 'Binaries/Win64'),(Join-Path $target 'Binaries/WinArm64') -ErrorAction SilentlyContinue
}
Write-Output "Plugins NVIDIA instalados em $dest : $($keep -join ', ')"
