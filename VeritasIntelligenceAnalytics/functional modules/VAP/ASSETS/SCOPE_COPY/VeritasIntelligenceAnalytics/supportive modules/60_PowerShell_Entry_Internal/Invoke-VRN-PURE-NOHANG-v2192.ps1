#requires -Version 7.0
param(
    [ValidateSet("PrecheckOnly","OpenInput","OpenOutput","OpenHtml")]
    [string]$Mode = "OpenHtml"
)
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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$VIA_ROOT        = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
$MODULE_ROOT     = Join-Path $VIA_ROOT "module"
$VRN_ROOT        = Join-Path $MODULE_ROOT "VRN"
$SUPPORTIVE_DIR  = Join-Path $MODULE_ROOT "supportive_module"
$PRECHECK_RUNNER = Join-Path $SUPPORTIVE_DIR "Invoke-VRN-SafePrecheck-v216.ps1"
$HTML_UI         = Join-Path $SUPPORTIVE_DIR "VRN_Resonance_Command_Center_v2192_PURE_NOHANG.html"
$INPUT_DIR       = Join-Path $VRN_ROOT "input"
$OUTPUT_DIR      = Join-Path $VRN_ROOT "output"

function def_OpenPath {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        Start-Process $Path
    } else {
        Write-Host "[WARN] Missing: $Path" -ForegroundColor Yellow
    }
}

Write-Host "==================================================================================================" -ForegroundColor Cyan
Write-Host "def VRN PURE NOHANG Command Center v2.1.9.2" -ForegroundColor Cyan
Write-Host "==================================================================================================" -ForegroundColor Cyan
Write-Host "[MODE] $Mode" -ForegroundColor Yellow

if (Test-Path -LiteralPath $PRECHECK_RUNNER -PathType Leaf) {
    & $PRECHECK_RUNNER -Strict
} else {
    Write-Host "[FAIL] Precheck runner missing: $PRECHECK_RUNNER" -ForegroundColor Red
}

switch ($Mode) {
    "PrecheckOnly" { Write-Host "[OK] Precheck only completed." -ForegroundColor Green }
    "OpenInput"    { def_OpenPath $INPUT_DIR }
    "OpenOutput"   { def_OpenPath $OUTPUT_DIR }
    "OpenHtml"     { def_OpenPath $HTML_UI }
}

Write-Host ""
Write-Host "PowerShell session remains open." -ForegroundColor Cyan

