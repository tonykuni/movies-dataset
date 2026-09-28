#requires -Version 7.0
param(
    [switch]$ReviewOnly,
    [switch]$RuntimeProbeOnly,
    [switch]$ExecuteEntry
)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====

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

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
