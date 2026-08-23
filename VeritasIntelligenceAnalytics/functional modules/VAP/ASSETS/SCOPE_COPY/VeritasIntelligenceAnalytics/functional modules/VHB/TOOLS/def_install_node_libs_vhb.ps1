# def Install Node libs locally into VHB vendor
$ErrorActionPreference = 'Continue'
$Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VHB"
$NodeDir = Join-Path $Base "VENDOR\node"
New-Item -ItemType Directory -Path $NodeDir -Force | Out-Null
Set-Location $NodeDir
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Host "[WARN] npm not found"; return }
if (-not (Test-Path -LiteralPath "package.json")) { npm init -y }
npm install plotly.js-dist-min echarts chart.js d3 interactjs gridstack sortablejs moveable floating-ui lucide
Write-Host "[OK] Node local libs ready: $NodeDir"

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
