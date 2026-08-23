#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_DualProjectDailyHealth\Invoke-VIA-DualProjectDailyHealth.ps1"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA DUAL PROJECT DAILY HEALTH · MANUAL LAUNCHER" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if(Test-Path -LiteralPath $ScriptPath -PathType Leaf){
    pwsh -NoProfile -ExecutionPolicy Bypass -File $ScriptPath -OpenHtmlReport
} else {
    Write-Host "[BLOCK] Daily health script missing: $ScriptPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "PowerShell remains open. No exit. No Stop-Process." -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
