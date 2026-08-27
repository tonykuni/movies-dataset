#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "VAP Next Optimization Actions" -ForegroundColor Cyan
Write-Host "1) Open V6 script and set EnableNetworkFetch = `$true" -ForegroundColor Yellow
Write-Host "2) Re-run V6 to fetch live data" -ForegroundColor Yellow
Write-Host "3) Re-run V7 to calculate quant tables" -ForegroundColor Yellow
Write-Host "4) Re-run maturity optimizer to confirm score improvement" -ForegroundColor Yellow
Write-Host ""
Write-Host "Commands are guidance only. This file intentionally does not auto-edit your scripts." -ForegroundColor DarkGray

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
