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
  "VIA_ENG151_VplDesktop.py"

Write-Host "[3/3] done -> dist\VeritasPulse.exe" -ForegroundColor Green
Start-Process (Join-Path $here "dist")

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
