param(
 [string]$Package='D:/Builds/MareAltaUE58_Pessoas_2026-11-04/Windows',
 [string[]]$Variants=@(''),
 [string]$Exec='',
 [int]$Soak=0,
 [int]$ResX=1920,
 [int]$ResY=1080
)
# Frame-time benchmark of the packaged game (PENDENCIAS P0 "FPS medido no executável"): runs MareAlta.exe -MareBench
# once per variant ('' = full game, 'MareBenchNoPeople', 'MareBenchNoGroom') and prints one row per sector.
# -Soak 7200 = 2-hour session (PENDENCIAS P0): the sectors repeat, sleeping to the next day between rounds.
$ErrorActionPreference='Stop'
$env:TEMP='D:/CodexTemp/ue58-temp'
$env:TMP=$env:TEMP
foreach($variant in $Variants){
 $qa='D:/CodexTemp/ue58-bench-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
 New-Item -ItemType Directory -Force $qa | Out-Null
 $args=@('-MareBench',"-MareSaveRoot=$qa","-UserDir=$qa/Unreal","-abslog=$qa/runtime.log",'-unattended','-nosplash','-windowed',"-ResX=$ResX","-ResY=$ResY")
 if($variant){$args+="-$variant"}
 if($Exec){$args+="-MareBenchExec=`"$Exec`""}
 if($Soak){$args+="-MareBenchSoak=$Soak"}
 $p=Start-Process -FilePath "$Package/MareAlta.exe" -WorkingDirectory $Package -ArgumentList $args -PassThru
 $start=Get-Date
 while(-not $p.HasExited){if(((Get-Date)-$start).TotalSeconds -gt (420+$Soak*1.2)){Stop-Process -Id $p.Id;throw "Timeout: $qa"};Start-Sleep 3;$p.Refresh()}
 if(-not (Test-Path "$qa/bench.json")){throw "Sem bench.json: $qa"}
 Write-Output "== $(if($variant){$variant}else{'completo'}) $Exec  ($qa)"
 (Get-Content "$qa/bench.json" -Raw | ConvertFrom-Json).sectors | ForEach-Object {
  "{0,-13} fps {1,5:N1}  p99 {2,5:N1} | jogo {3,5:N1} render {4,5:N1} gpu {5,5:N1} | pessoas {6}/{7}" -f $_.sector,$_.avg_fps,$_.p99_ms,$_.game_ms,$_.render_ms,$_.gpu_ms,$_.people_rendered,$_.people }
 $bad=@(Select-String -LiteralPath "$qa/runtime.log" -Pattern 'Failed to find object|Nanite static mesh|overflow|Error:|Fatal')
 if($bad.Count){Write-Output "  avisos no log: $($bad.Count)"}
}
