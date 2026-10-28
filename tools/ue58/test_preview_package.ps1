param([string]$Package='D:/Builds/MareAltaUE58_AudioVisual_2026-10-28/Windows')
$ErrorActionPreference='Stop'
$exe=Join-Path $Package 'MareAlta.exe'
if(-not (Test-Path -LiteralPath $exe)){throw "Executável ausente: $exe"}
if(-not (Test-Path -LiteralPath (Join-Path $Package 'MareAlta/Content/Paks'))){throw 'Pacote sem Paks/IoStore'}
$qa='D:/CodexTemp/ue58-package-qa-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
New-Item -ItemType Directory -Path $qa -Force | Out-Null
$env:TEMP='D:/CodexTemp/ue58-temp'
$env:TMP=$env:TEMP
$start=Get-Date
$process=Start-Process -FilePath $exe -WorkingDirectory $Package -ArgumentList @('-MarePreviewQA',"-MareSaveRoot=$qa","-UserDir=$qa/Unreal", "-abslog=$qa/runtime.log",'-RenderOffscreen','-unattended','-nosplash','-windowed','-ResX=1280','-ResY=720') -WindowStyle Hidden -PassThru
while(-not $process.HasExited){
 if(((Get-Date)-$start).TotalSeconds -gt 240){Stop-Process -Id $process.Id -ErrorAction SilentlyContinue;throw "Timeout: $qa"}
 Start-Sleep -Seconds 2
 $process.Refresh()
}
$reportPath=Join-Path $qa 'preview-qa.json'
if(-not (Test-Path -LiteralPath $reportPath)){throw "Jogo encerrou sem relatório: $qa"}
$report=Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if(-not $report.finished -or $report.checks.Count -lt 20 -or @($report.checks | Where-Object {-not $_.pass}).Count){$report | ConvertTo-Json -Depth 8;throw "Regressão reprovada: $qa"}
$issues=@(Select-String -LiteralPath "$qa/runtime.log" -Pattern 'Error:|Fatal error|Assertion failed|Ensure condition failed' | ForEach-Object {$_.Line})
if($issues.Count){$issues;throw "Erros no log: $qa"}
foreach($picture in @('surface.png','underwater.png','phone.png','pause.png','kiosk-phone.png','kiosk-day.png','kiosk-night.png','house-day.png','expansion-pool-locked.png','expansion-pool-purchased.png')){if(-not (Test-Path -LiteralPath "$qa/$picture")){throw "Captura ausente: $picture"}}
foreach($recording in @('mix_audible.wav','mix_muted.wav','mix_paused.wav')){if(-not (Test-Path -LiteralPath "$qa/$recording")){throw "Gravação ausente: $recording"}}
$result=[ordered]@{qa_root=$qa;executable=$exe;checks=$report.checks.Count;passed=$true;exit_code=$process.ExitCode;tested_at=(Get-Date -Format o);visual_review_required=$true}
$result | ConvertTo-Json | Set-Content -LiteralPath "$qa/package-result.json" -Encoding utf8
$result | ConvertTo-Json
