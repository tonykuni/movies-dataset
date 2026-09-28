# VeritasNexusCore
# VERITAS INTELLIGENCE ANALYTICS
# Unified Supportive Tooling, Runtime Governance, Registry, HardGate, and System Control Gateway.
# Policy: This is the ONLY first-layer external interface file.
# Generated: 2026-06-08 20:15:46

# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
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

$def_INTERFACE_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

function def_FindLatestFreezeReport {
    $reportRoot = Join-Path $def_INTERFACE_ROOT "_freeze_reports"

    if (-not (Test-Path -LiteralPath $reportRoot)) {
        return $null
    }

    return Get-ChildItem -LiteralPath $reportRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function def_Show_VeritasNexusCore {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VeritasNexusCore" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "VERITAS INTELLIGENCE ANALYTICS"
    Write-Host "Unified Supportive Tooling, Runtime Governance, Registry, HardGate, and System Control Gateway."
    Write-Host ""
    Write-Host "Root: $def_INTERFACE_ROOT"
    Write-Host ""
    Write-Host "Groups:"
    Get-ChildItem -LiteralPath $def_INTERFACE_ROOT -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d{2}_' } |
        Sort-Object Name |
        ForEach-Object { Write-Host "  def $($_.Name)" -ForegroundColor Green }

    $latest = def_FindLatestFreezeReport

    if ($null -ne $latest) {
        $htmlCandidates = Get-ChildItem -LiteralPath $latest.FullName -File -Filter "*.html" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        $jsonCandidates = Get-ChildItem -LiteralPath $latest.FullName -File -Filter "*.json" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        Write-Host ""
        Write-Host "Latest Report Folder:"
        Write-Host "  $($latest.FullName)"

        if ($null -ne $htmlCandidates) {
            Write-Host "  HTML: $($htmlCandidates.FullName)"
            Start-Process -FilePath $htmlCandidates.FullName | Out-Null
        }

        if ($null -ne $jsonCandidates) {
            Write-Host "  JSON: $($jsonCandidates.FullName)"
        }
    }

    Write-Host ""
    Write-Host "PowerShell remains open. No exit. No Stop-Process." -ForegroundColor Cyan
}

try {
    def_Show_VeritasNexusCore
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "PowerShell remains open." -ForegroundColor Yellow
}
finally {
    Write-Host "def Interface session remains open." -ForegroundColor Cyan
}

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
