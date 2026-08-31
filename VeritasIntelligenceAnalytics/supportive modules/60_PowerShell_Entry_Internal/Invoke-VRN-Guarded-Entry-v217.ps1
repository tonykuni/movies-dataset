#requires -Version 7.0
param(
    [ValidateSet("PrecheckOnly","OpenInput","OpenOutput","OpenCommandIndex")]
    [string]$Mode = "PrecheckOnly",

    [switch]$Strict
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
$COMMAND_INDEX   = Join-Path $SUPPORTIVE_DIR "VRN_Guarded_Command_Index_v217.html"

$INPUT_DIR       = Join-Path $VRN_ROOT "input"
$OUTPUT_DIR      = Join-Path $VRN_ROOT "output"

function def_OpenPath {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        try { Start-Process $Path } catch {
            Write-Host "[WARN] Cannot open: $Path :: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] Path missing: $Path" -ForegroundColor Yellow
    }
}

if (-not (Test-Path -LiteralPath $PRECHECK_RUNNER -PathType Leaf)) {
    Write-Host "[FAIL] SafePrecheck runner missing: $PRECHECK_RUNNER" -ForegroundColor Red
    throw "SafePrecheck runner missing."
}

Write-Host "==================================================================================================" -ForegroundColor Cyan
Write-Host "def VRN Guarded Entry v2.1.7" -ForegroundColor Cyan
Write-Host "==================================================================================================" -ForegroundColor Cyan
Write-Host "[MODE] $Mode" -ForegroundColor Yellow

if ($Strict) {
    & $PRECHECK_RUNNER -Strict
} else {
    & $PRECHECK_RUNNER
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] LastExitCode from precheck: $LASTEXITCODE" -ForegroundColor Yellow
}

switch ($Mode) {
    "PrecheckOnly" {
        Write-Host "[OK] Precheck completed. No launcher executed." -ForegroundColor Green
    }
    "OpenInput" {
        def_OpenPath -Path $INPUT_DIR
    }
    "OpenOutput" {
        def_OpenPath -Path $OUTPUT_DIR
    }
    "OpenCommandIndex" {
        def_OpenPath -Path $COMMAND_INDEX
    }
}

Write-Host ""
Write-Host "PowerShell session remains open." -ForegroundColor Cyan

