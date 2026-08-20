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
