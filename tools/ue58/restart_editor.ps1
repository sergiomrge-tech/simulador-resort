# Restart the UE 5.8 editor with the MCP server and a NEW save folder (qa rule: fresh profile per gate run).
# Usage: powershell -File tools/ue58/restart_editor.ps1 [-Build]  (-Build compiles MareAltaEditor with the editor closed)
param([switch]$Build, [string]$Tag = 'claude')
$ErrorActionPreference = 'Continue'
$proj = 'D:\Projetos\MareAltaUE58\unreal\MareAlta\MareAlta.uproject'
Get-Process UnrealEditor -ErrorAction SilentlyContinue | ForEach-Object { taskkill /PID $_.Id /F | Out-Null }
Start-Sleep 4
Remove-Item 'D:\Projetos\MareAltaUE58\unreal\MareAlta\Saved\Autosaves\PackageRestoreData.json' -ErrorAction SilentlyContinue
if ($Build) {
    & 'D:/UE_5.8/Engine/Build/BatchFiles/Build.bat' MareAltaEditor Win64 Development "-Project=$proj" -WaitMutex 2>&1 |
        Select-String -Pattern 'error|warning C|Total time|Result:|Succeeded|Failed' | Select-Object -Last 40
    if ($LASTEXITCODE -ne 0) { Write-Output "BUILD FAILED $LASTEXITCODE"; exit 1 }
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$save = "D:/CodexTemp/$Tag-qa-$stamp"
Start-Process 'D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList "`"$proj`" -ModelContextProtocolStartServer -MareSaveRoot=$save"
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 600) {
    Start-Sleep 5
    try { Invoke-WebRequest -Uri 'http://127.0.0.1:8000/mcp' -Method Get -TimeoutSec 3 -UseBasicParsing | Out-Null; $code = 200 }
    catch { $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 } }
    if ($code -eq 405) { Start-Sleep 25; Write-Output "EDITOR READY save=$save after $([int]((Get-Date)-$t0).TotalSeconds)s"; exit 0 }
}
Write-Output 'EDITOR NOT READY after 600 s'; exit 2
