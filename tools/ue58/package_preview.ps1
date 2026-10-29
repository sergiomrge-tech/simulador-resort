param(
 [string]$Engine='D:/UE_5.8',
 [string]$Output='D:/Builds/MareAltaUE58_AudioVisual_2026-10-28'
)
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project=Join-Path $repo 'unreal/MareAlta/MareAlta.uproject'
$projectMatch=[regex]::Escape([IO.Path]::GetFullPath($project).Replace('\','/'))
$openEditors=@(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'" | Where-Object {$_.CommandLine -and $_.CommandLine.Replace('\','/') -match $projectMatch})
if($openEditors.Count){throw 'Feche o Unreal Editor deste projeto antes de exportar: a DLL em uso impede o link.'}
if(-not [IO.Path]::GetFullPath($Output).StartsWith('D:\',[StringComparison]::OrdinalIgnoreCase)){throw 'Build deve ficar no drive D.'}
$env:TEMP='D:/CodexTemp/ue58-temp'
$env:TMP=$env:TEMP
Set-Item Env:UE-LocalDataCachePath 'D:/CodexTemp/ue58-ddc'
New-Item -ItemType Directory -Path $env:TEMP,$Output -Force | Out-Null
$buildLog='D:/CodexTemp/ue58-package-audiovisual-20261028.log'
& "$Engine/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun "-project=$project" -noP4 -platform=Win64 -clientconfig=Development -build -cook -iterativecooking -map=Coast -stage -pak -iostore -archive "-archivedirectory=$Output" -utf8output 2>&1 | Tee-Object -FilePath $buildLog | Out-Null
if($LASTEXITCODE -ne 0){throw "Empacotamento falhou: $LASTEXITCODE"}
Write-Output "Empacotamento concluído: $Output. Log: $buildLog"
