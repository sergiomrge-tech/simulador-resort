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
    # Não interpretar uma falha antiga antes que a nova engine abra o log.
    [System.IO.File]::WriteAllText($log, "")
    $process=Start-Process -FilePath $exe -WorkingDirectory $work -ArgumentList $argsList -WindowStyle Hidden -PassThru
    $deadline=(Get-Date).AddMinutes(5)
    while(-not $process.WaitForExit(1000)) {
        $parseFailure=Test-Path -LiteralPath $log
        if($parseFailure){$parseFailure=Select-String -Path $log -Pattern 'Parse Error|Failed to load script' -Quiet}
        if($parseFailure -or (Get-Date) -gt $deadline) {
            Stop-Process -Id $process.Id
            $process.WaitForExit()
            Write-Output "$check interrompido por falha de script ou timeout; veja $log"
            break
        }
    }
    $errorsFound=Select-String -Path $log -Pattern 'ERROR:|REAL_MISSING|TEST FAIL|FAIL '
    $passFound=Select-String -Path $log -Pattern 'TEST PASS|TEST.*PASS'
    Write-Output "$check $kind exit=$($process.ExitCode)"
    $errorsFound | Select-Object -First 12 | ForEach-Object {Write-Output $_.Line}
    $passFound | ForEach-Object {Write-Output $_.Line}
    if($process.ExitCode -ne 0 -or $errorsFound -or -not $passFound){$anyFailed=$true}
}
if($anyFailed){exit 1}
