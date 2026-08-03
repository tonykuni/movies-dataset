#requires -Version 7.0

param(
    [string]$UnifiedInputSSOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json",
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

function def_ReadJson {
    param([string]$Path)
    if (-not [System.IO.File]::Exists($Path)) {
        throw "UnifiedInputSSOT missing: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

try {
    $cfg = def_ReadJson $UnifiedInputSSOT

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA UNIFIED INPUT GATEWAY" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Action        : $Action"
    Write-Host "SSOT          : $UnifiedInputSSOT"
    Write-Host "Freeze Status : $($cfg.freeze_status)"
    Write-Host "Root          : $($cfg.paths.root)"
    Write-Host "NexusCore     : $($cfg.paths.nexuscore_entry)"
    Write-Host "VDF Root      : $($cfg.paths.vdf_root)"
    Write-Host "VRN SSOT Root : $($cfg.paths.vrn_ssot_root)"

    if ($Action -eq "status") {
        Write-Host ""
        Write-Host "Locked Files:"
        foreach ($f in $cfg.locked_files) {
            Write-Host ("  [{0}] {1}" -f $f.Status, $f.Path)
        }
    }
    elseif ($Action -eq "open-report") {
        $html = $cfg.outputs.html_report
        if ([System.IO.File]::Exists($html)) {
            Start-Process -FilePath $html | Out-Null
            Write-Host "Opened report: $html" -ForegroundColor Green
        }
        else {
            Write-Host "Report missing: $html" -ForegroundColor Yellow
        }
    }
    elseif ($Action -eq "open-nexus") {
        $nexus = $cfg.paths.nexuscore_entry
        if ([System.IO.File]::Exists($nexus)) {
            Write-Host "NexusCore exists: $nexus" -ForegroundColor Green
        }
        else {
            Write-Host "NexusCore missing: $nexus" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Unknown action. Supported: status, open-report, open-nexus" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}