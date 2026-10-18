# Baixa os assets CC0 (Poly Haven) e gera as texturas procedurais. Windows PowerShell 5+/7.
# Uso:  powershell -ExecutionPolicy Bypass -File tools\fetch_assets.ps1 [--force]
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$py = $null
foreach ($c in @("py", "python", "python3")) { if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break } }
if (-not $py) { Write-Error "Python 3 nao encontrado (instale de python.org ou: winget install Python.Python.3.12)"; exit 1 }
& $py -c "import PIL, numpy" 2>$null
if ($LASTEXITCODE -ne 0) { & $py -m pip install --user pillow numpy }
& $py tools/fetch_assets.py @args
exit $LASTEXITCODE
