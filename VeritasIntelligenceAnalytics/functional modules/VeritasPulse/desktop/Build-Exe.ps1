# Build-Exe.ps1 — package VeritasPulse as a single Windows .exe
# Run from the desktop\ folder after build_all.py has produced output\VeritasPulse_App.html
# Honors Tony's LL: py -3.11 launcher, no VS Code, no input waits.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "[1/3] installing build deps (pywebview + pyinstaller)" -ForegroundColor Cyan
py -3.11 -m pip install --upgrade pywebview pyinstaller | Out-Null

$app = Join-Path $here "..\output\VeritasPulse_App.html"
if (-not (Test-Path $app)) { throw "build first: python build_all.py  (missing $app)" }

Write-Host "[2/3] building VeritasPulse.exe (onefile, windowed)" -ForegroundColor Cyan
py -3.11 -m PyInstaller --noconfirm --onefile --windowed `
  --name VeritasPulse `
  --add-data "$app;." `
  "vpl_desktop.py"

Write-Host "[3/3] done -> dist\VeritasPulse.exe" -ForegroundColor Green
Start-Process (Join-Path $here "dist")
