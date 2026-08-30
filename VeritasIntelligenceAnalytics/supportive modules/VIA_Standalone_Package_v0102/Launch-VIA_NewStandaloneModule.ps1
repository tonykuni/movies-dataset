#requires -Version 7.0
param(
    [switch]$ReviewOnly,
    [switch]$RuntimeProbeOnly,
    [switch]$ExecuteEntry
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
$ErrorActionPreference = "Stop"

# =============================================================================
# def PARAMETERS
# =============================================================================
$def_PARAM_PackageDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$def_PARAM_AppDir = Join-Path $def_PARAM_PackageDir "app"
$def_PARAM_SupportPyDir = Join-Path $def_PARAM_PackageDir "_supportive_bundle\python"
$def_PARAM_LogDir = Join-Path $def_PARAM_PackageDir "_logs"
$def_PARAM_EntryFile = Join-Path $def_PARAM_AppDir "Invoke-VeritasCodexNexus.ps1"

# =============================================================================
# def ENV
# =============================================================================
$env:VIA_OFFLINE_MODE = "1"
$env:VIA_NETWORK_DISABLED = "1"
$env:VIA_STANDALONE_PACKAGE_DIR = $def_PARAM_PackageDir
$env:PYTHONPATH = "$def_PARAM_SupportPyDir;$def_PARAM_AppDir;$env:PYTHONPATH"

# =============================================================================
# def HELPERS
# =============================================================================
function def_FindPython {
    $candidates = @(
        "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe",
        "python",
        "py"
    )

    foreach ($candidate in $candidates) {
        try {
            if ($candidate -match "\\python\.exe$") {
                if (Test-Path -LiteralPath $candidate) { return $candidate }
            } else {
                $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
                if ($null -ne $cmd) { return $candidate }
            }
        } catch {}
    }

    return ""
}

function def_InvokeRuntimeProbe {
    $python = def_FindPython
    $bootstrap = Join-Path $def_PARAM_SupportPyDir "SUP_MDL160_StandaloneBootstrap.py"

    if ([string]::IsNullOrWhiteSpace($python)) {
        Write-Host "[WARN] Python not found." -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path -LiteralPath $bootstrap)) {
        Write-Host "[FAIL] Bootstrap missing: $bootstrap" -ForegroundColor Red
        return
    }

    Write-Host "[RUN] Runtime Probe" -ForegroundColor Cyan
    & $python $bootstrap
}

function def_InvokeEntryReview {
    if (-not (Test-Path -LiteralPath $def_PARAM_EntryFile)) {
        Write-Host "[FAIL] Entry file missing: $def_PARAM_EntryFile" -ForegroundColor Red
        return
    }

    Write-Host "[OK] Entry file exists: $def_PARAM_EntryFile" -ForegroundColor Green

    if ($ExecuteEntry) {
        Write-Host "[RUN] Execute Entry" -ForegroundColor Cyan
        & $def_PARAM_EntryFile
    } else {
        Write-Host "[REVIEW] Entry execution skipped. Use -ExecuteEntry to run." -ForegroundColor Yellow
    }
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · STANDALONE PACKAGE LAUNCHER · VIA_NewStandaloneModule v0105" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_InvokeRuntimeProbe

    if ($RuntimeProbeOnly) {
        Write-Host "PowerShell remains open." -ForegroundColor Cyan
        return
    }

    def_InvokeEntryReview

    Write-Host ""
    Write-Host "PowerShell remains open." -ForegroundColor Cyan
} catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host "PowerShell remains open." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
