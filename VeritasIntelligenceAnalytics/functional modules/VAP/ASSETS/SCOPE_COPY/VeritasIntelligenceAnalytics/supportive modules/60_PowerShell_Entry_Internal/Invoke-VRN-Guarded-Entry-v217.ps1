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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
