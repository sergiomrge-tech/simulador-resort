param([string]$EngineRoot='D:/UE_5.8',[int]$Port=8000)
$ErrorActionPreference='Stop'
$projectFile=Join-Path $PSScriptRoot 'MareAlta.uproject'
$editorFile=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
if(!(Test-Path -LiteralPath $editorFile)){throw "UnrealEditor não encontrado em $EngineRoot"}
$cacheRoot='D:/CodexTemp/ue58-ddc'
New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
Set-Item Env:UE-LocalDataCachePath $cacheRoot
Start-Process -FilePath $editorFile -ArgumentList @(('"'+$projectFile+'"'),'-ModelContextProtocolStartServer',"-ModelContextProtocolPort=$Port") -WindowStyle Hidden
Write-Output "MCP local: http://127.0.0.1:$Port/mcp"
