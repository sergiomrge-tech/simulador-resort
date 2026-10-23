param([string[]]$Checks=@('terminal','counter-first','company','counter','practical','phone-layout'),[switch]$Exported)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$engine='C:/Users/sergi/Documents/ChatGPT/Gestao Facil/Ilha Selvagem/tools/Godot_v4.5.1-stable_win64.exe'
$anyFailed=$false
foreach($check in $Checks) {
    $kind=if($Exported){'pack'}else{'source'}
    $env:APPDATA=Join-Path $taskRoot "build/qa/counter-batch-$check-$kind"
    New-Item -ItemType Directory -Force $env:APPDATA | Out-Null
    $log=Join-Path $taskRoot "build/logs/counter-batch-$check-$kind.log"
    $argsList=@('--resolution','1280x720','--audio-driver','Dummy','--log-file',('"'+$log+'"'),'--','--loop-test',('--'+$check+'-test'),'--quality=1')
    $work=$taskRoot
    if($Exported) {
        $exe=Join-Path $taskRoot 'build/rc2-playable/MareAltaResort.exe'
        $work=Join-Path $taskRoot 'build/rc2-playable'
    } else {
        $exe=$engine
        $argsList=@('--path',('"'+$taskRoot+'"'))+$argsList
    }
    $process=Start-Process -FilePath $exe -WorkingDirectory $work -ArgumentList $argsList -WindowStyle Hidden -PassThru
    $process.WaitForExit()
    $errorsFound=Select-String -Path $log -Pattern 'SCRIPT ERROR|Parse Error|REAL_MISSING|TEST FAIL|FAIL '
    $passFound=Select-String -Path $log -Pattern 'TEST PASS|TEST.*PASS'
    Write-Output "$check $kind exit=$($process.ExitCode)"
    $errorsFound | ForEach-Object {Write-Output $_.Line}
    $passFound | ForEach-Object {Write-Output $_.Line}
    if($process.ExitCode -ne 0 -or $errorsFound -or -not $passFound){$anyFailed=$true}
}
if($anyFailed){exit 1}
