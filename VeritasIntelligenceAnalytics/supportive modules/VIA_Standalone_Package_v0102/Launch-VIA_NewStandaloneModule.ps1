#requires -Version 7.0
param(
    [switch]$ReviewOnly,
    [switch]$RuntimeProbeOnly,
    [switch]$ExecuteEntry
)

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
