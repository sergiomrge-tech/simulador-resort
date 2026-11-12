param([string]$Label='after-high',[int]$Preset=2,[switch]$Exported,[switch]$Original,[switch]$Paired,[switch]$Reverse)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$env:APPDATA="D:/CodexTemp/resort-perf/$Label"
New-Item -ItemType Directory -Force $env:APPDATA | Out-Null
$log="D:/CodexTemp/resort-perf/$Label.log"
$exe='C:/Users/sergi/Documents/ChatGPT/Gestao Facil/Ilha Selvagem/tools/Godot_v4.5.1-stable_win64.exe'
$arguments=@('--resolution','1920x1080','--audio-driver','Dummy','--log-file',('"'+$log+'"'),'--','--loop-test','--perf-test','--perf-shots',("--quality=$Preset"))
if($Paired){$arguments+='--perf-paired'}
if($Reverse){$arguments+='--perf-reverse'}
if($Original){$arguments+='--perf-original'}
if($Exported){$exe=Join-Path $root 'build/rc2-playable/MareAltaResort.exe'}
else{$arguments=@('--path',('"'+$root+'"'))+$arguments}
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
$end=(Get-Date).AddMinutes(4)
while(-not $p.WaitForExit(1000)){
    if((Test-Path $log) -and (Select-String -LiteralPath $log -Pattern 'Parse Error|Failed to load script' -Quiet)){Stop-Process -Id $p.Id;throw "Script error: $log"}
    if((Get-Date) -gt $end){Stop-Process -Id $p.Id;throw 'Benchmark timeout'}
}
Get-Content -LiteralPath $log | Select-String 'BENCH_SCENE|BENCH_PAIRED|PERFORMANCE_TEST|ERROR:' | ForEach-Object {$_.Line}
if($p.ExitCode -ne 0 -or (Select-String -LiteralPath $log -Pattern 'ERROR:|REAL_MISSING|TEST FAIL' -Quiet)){throw "Benchmark failed: $log"}
