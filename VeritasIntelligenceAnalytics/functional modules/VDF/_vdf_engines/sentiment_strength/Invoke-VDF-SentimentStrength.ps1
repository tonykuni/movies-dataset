#requires -Version 7.0

# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
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

