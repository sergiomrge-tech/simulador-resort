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
 if(((Get-Date)-$start).TotalSeconds -gt 300){Stop-Process -Id $process.Id -ErrorAction SilentlyContinue;throw "Timeout: $qa"}
 Start-Sleep -Seconds 2
 $process.Refresh()
}
$reportPath=Join-Path $qa 'preview-qa.json'
if(-not (Test-Path -LiteralPath $reportPath)){throw "Jogo encerrou sem relatório: $qa"}
$report=Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if(-not $report.finished -or $report.checks.Count -lt 20 -or @($report.checks | Where-Object {-not $_.pass}).Count){$report | ConvertTo-Json -Depth 8;throw "Regressão reprovada: $qa"}
$required=@('home_door_fits_frame','home_door_opens_after_fit','home_door_closes_after_fit','reef_pairs_present','reef_below_wave_surface','reef_motion','marine_models_loaded','day_sail_only','night_cruise_only','whale_breaches','marine_splash','marine_night_visible')
$required+=@('grass_coverage_cooked','grass_nonblocking_culled','grass_cycle_captured')
$required+=@('swim_hands_in_front_separated')
$required+=@('player_rig_loaded','player_pickup_ready','player_carry_hands','player_returns_product','player_body_visible','home_tv_focus','home_tv_on','home_stereo_plays','home_stereo_music_volume','home_sofa_focus','home_sofa_sits','home_sofa_stands','home_shower_focus','home_shower_on','home_appliances_cycle')
foreach($picture in @('player-carry.png','player-body.png','home-tv-off.png','home-tv-on.png','home-sofa.png','home-shower.png')){if(-not (Test-Path -LiteralPath "$qa/$picture")){throw "Captura de corpo/casa ausente: $picture"}}
foreach($picture in @('grass-day.png','grass-rain.png','grass-night.png')){if(-not (Test-Path -LiteralPath "$qa/$picture")){throw "Captura de gramado ausente: $picture"}}
foreach($name in $required){if(-not @($report.checks | Where-Object {$_.name -eq $name -and $_.pass}).Count){throw "Verificação ausente: $name em $qa"}}
$issues=@(Select-String -LiteralPath "$qa/runtime.log" -Pattern 'Error:|Fatal error|Assertion failed|Ensure condition failed|missing usage flag|Default Material will be used|Failed to compile Material|Failed to find object|SkipPackage:' | ForEach-Object {$_.Line})
if($issues.Count){$issues;throw "Erros no log: $qa"}
foreach($picture in @('surface.png','underwater.png','phone.png','pause.png','kiosk-phone.png','kiosk-day.png','kiosk-night.png','house-day.png','expansion-pool-locked.png','expansion-pool-purchased.png','reef-underwater.png','shore-waves.png','whale-breach.png','whale-splash.png','cruise-night.png')){if(-not (Test-Path -LiteralPath "$qa/$picture")){throw "Captura ausente: $picture"}}
foreach($recording in @('mix_audible.wav','mix_muted.wav','mix_paused.wav')){if(-not (Test-Path -LiteralPath "$qa/$recording")){throw "Gravação ausente: $recording"}}
$result=[ordered]@{qa_root=$qa;executable=$exe;checks=$report.checks.Count;passed=$true;exit_code=$process.ExitCode;tested_at=(Get-Date -Format o);visual_review_required=$true}
$result | ConvertTo-Json | Set-Content -LiteralPath "$qa/package-result.json" -Encoding utf8
$result | ConvertTo-Json
