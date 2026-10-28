param([Parameter(Mandatory=$true)][string]$Package,[int]$Width=1920,[int]$Height=1080)
$ErrorActionPreference='Stop'
$qa='D:/CodexTemp/ue58-render-profile-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
New-Item -ItemType Directory -Path $qa -Force | Out-Null
$state=Get-Content -LiteralPath 'unreal/MareAlta/Content/Data/default_save.json' -Raw | ConvertFrom-Json
$state | Add-Member -NotePropertyName ue_intro_stage -NotePropertyValue 2 -Force
$state | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath "$qa/slot1.json" -Encoding utf8
$env:TEMP='D:/CodexTemp/ue58-temp';$env:TMP=$env:TEMP
nvidia-smi --query-gpu=name,memory.total,driver_version,temperature.gpu --format=csv | Set-Content -LiteralPath "$qa/gpu.csv"
$exe=Join-Path $Package 'MareAlta.exe'
$p=Start-Process -FilePath $exe -WorkingDirectory $Package -ArgumentList @('-MareGraphicsQA','-MareNativeResolution','-csvGpuStats',"-MareSaveRoot=$qa","-UserDir=$qa/UE","-abslog=$qa/runtime.log",'-RenderOffscreen','-unattended','-nosplash','-windowed','-ForceRes',"-ResX=$Width","-ResY=$Height") -WindowStyle Hidden -PassThru
$start=Get-Date
while(-not $p.HasExited){if(((Get-Date)-$start).TotalSeconds -gt 300){Stop-Process -Id $p.Id;throw "Profiling timeout: $qa"};Start-Sleep -Seconds 2;$p.Refresh()}
if($p.ExitCode -ne 0){throw "Exit $($p.ExitCode): $qa"}
$report=Get-Content -LiteralPath "$qa/graphics-qa.json" -Raw | ConvertFrom-Json
if(-not $report.finished -or $report.captures.Count -ne 4){throw "Incomplete: $qa"}
foreach($c in $report.captures){if(-not (Test-Path -LiteralPath $c.csv)){throw "CSV missing: $($c.csv)"};if($c.pcg_instances -ne 60){throw "Missing cooked PCG: $($c.pcg_instances)"};if($c.viewport_x -ne $Width -or $c.viewport_y -ne $Height){throw "Unexpected viewport: $($c.viewport_x)x$($c.viewport_y)"}}
$issues=@(Select-String -LiteralPath "$qa/runtime.log" -Pattern 'Error:|Fatal error|Assertion failed|Ensure condition failed|Invalid material.*Nanite')
if($issues.Count){$issues;throw "Render issues: $qa"}
Write-Output $qa

