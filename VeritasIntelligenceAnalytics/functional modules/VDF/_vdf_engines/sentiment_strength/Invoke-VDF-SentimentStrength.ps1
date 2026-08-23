#requires -Version 7.0

$def_PARAM_PYTHON = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_vdf_envs\sentiment_strength\Scripts\python.exe"
$def_PARAM_ROUTER = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_vdf_engines\sentiment_strength\VDF_SentimentStrength_Router.py"
$def_PARAM_INPUT_JSON = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_vdf_inputs\VDF_SentimentStrength_Input.json"
$def_PARAM_OUTPUT_DIR = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_vdf_outputs\sentiment_strength"

if (-not (Test-Path -LiteralPath $def_PARAM_PYTHON)) {
    $def_PARAM_PYTHON = "python"
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "def VDF SentimentStrength Launcher" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

& $def_PARAM_PYTHON $def_PARAM_ROUTER --input-json $def_PARAM_INPUT_JSON

Write-Host ""
Write-Host "Output Dir: $def_PARAM_OUTPUT_DIR" -ForegroundColor Green
Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
