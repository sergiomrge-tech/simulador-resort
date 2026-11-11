param(
 [string]$Package='D:/Builds/MareAltaUE58_Shipping_2026-11-11a/Windows',
 [Parameter(Mandatory=$true)][string]$Script,
 [int]$Timeout=1200,
 [int]$ResX=1280,
 [int]$ResY=720
)
# Scripted photo run of the packaged game (AMareScriptQA): poses, clock, console commands and screenshots listed in a
# text file under D:/CodexTemp. Prints the folder with the PNGs and script-qa.json.
$ErrorActionPreference='Stop'
$env:TEMP='D:/CodexTemp/ue58-temp'
$env:TMP=$env:TEMP
$qa='D:/CodexTemp/ue58-script-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
New-Item -ItemType Directory -Force $qa | Out-Null
$a=@("-MareScriptQA=$Script",'-MareSkipMenu',"-MareSaveRoot=$qa","-UserDir=$qa/Unreal","-abslog=$qa/runtime.log",'-unattended','-nosplash','-windowed',"-ResX=$ResX","-ResY=$ResY")
$p=Start-Process -FilePath "$Package/MareAlta.exe" -WorkingDirectory $Package -ArgumentList $a -PassThru
$start=Get-Date
while(-not $p.HasExited){if(((Get-Date)-$start).TotalSeconds -gt $Timeout){Get-Process MareAlta* -ErrorAction SilentlyContinue | Stop-Process -Force;Write-Output "TIMEOUT";break};Start-Sleep 3;$p.Refresh()}
Start-Sleep 2
$done=$false;if(Test-Path "$qa/script-qa.json"){$done=(Get-Content "$qa/script-qa.json" -Raw | ConvertFrom-Json).finished}
Write-Output "pasta: $qa  terminou: $done  fotos: $((Get-ChildItem $qa -Filter *.png).Count)"
