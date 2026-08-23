#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_BASE_HOME_IO_20260506_210324\vap_base_home_io_builder.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_BASE_HOME_IO_20260506_210324\VAP_Base_Home_WindowsIO_TemplateLibrary.html"

Write-Host ""
Write-Host "Refreshing VAP Base Home..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
} else {
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
