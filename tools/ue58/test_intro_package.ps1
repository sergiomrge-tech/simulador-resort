param([Parameter(Mandatory=$true)][string]$Package)
$ErrorActionPreference='Stop'
$exe=Join-Path $Package 'MareAlta.exe'
if(-not (Test-Path -LiteralPath $exe)){throw "Executável ausente: $exe"}
$root='D:/CodexTemp/ue58-intro-package-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
$env:TEMP='D:/CodexTemp/ue58-temp';$env:TMP=$env:TEMP
foreach($mode in @('natural','skip')){
 $qa=Join-Path $root $mode
 New-Item -ItemType Directory -Path $qa -Force | Out-Null
 $argsList=@('-MareIntroQA',"-MareSaveRoot=$qa","-UserDir=$qa/Unreal","-abslog=$qa/runtime.log",'-RenderOffscreen','-unattended','-nosplash','-windowed','-ResX=1280','-ResY=720')
 if($mode -eq 'natural'){$argsList+='-MareIntroNaturalQA'}
 $process=Start-Process -FilePath $exe -WorkingDirectory $Package -ArgumentList $argsList -WindowStyle Hidden -PassThru
 if(-not $process.WaitForExit(180000)){Stop-Process -Id $process.Id -ErrorAction SilentlyContinue;throw "Tempo esgotado: $qa"}
 if($process.ExitCode -ne 0){throw "Jogo terminou com código $($process.ExitCode): $qa"}
 $report=Get-Content -LiteralPath "$qa/intro-qa.json" -Raw | ConvertFrom-Json
 if(-not $report.finished -or $report.checks.Count -lt 6 -or @($report.checks | Where-Object {-not $_.pass}).Count){$report | ConvertTo-Json -Depth 8;throw "Falha na abertura: $qa"}
 $issues=@(Select-String -LiteralPath "$qa/runtime.log" -Pattern 'Error:|Fatal error|Assertion failed|Ensure condition failed|missing usage flag|Default Material will be used|Failed to compile Material')
 if($issues.Count){$issues;throw "Erros no log: $qa"}
 foreach($file in @('intro-bus.png','intro-after-arrival.png','intro-letter.png','slot1.json')){if(-not (Test-Path -LiteralPath "$qa/$file")){throw "Evidência ausente: $qa/$file"}}
 $save=Get-Content -LiteralPath "$qa/slot1.json" -Raw | ConvertFrom-Json
 if($save.ue_intro_stage -ne 2){throw "Conclusão não persistida: $qa"}
 [pscustomobject]@{Mode=$mode;Checks=$report.checks.Count;Profile=$qa;Result='PASS'}
}
Write-Output "Imagens e logs para revisão: $root"
