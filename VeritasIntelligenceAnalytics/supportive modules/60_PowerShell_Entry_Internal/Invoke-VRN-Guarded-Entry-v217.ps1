#requires -Version 7.0
param(
    [ValidateSet("PrecheckOnly","OpenInput","OpenOutput","OpenCommandIndex")]
    [string]$Mode = "PrecheckOnly",

    [switch]$Strict
)

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