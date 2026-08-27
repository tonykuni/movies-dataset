# VeritasNexusCore
# VERITAS INTELLIGENCE ANALYTICS
# Unified Supportive Tooling, Runtime Governance, Registry, HardGate, and System Control Gateway.
# Policy: This is the ONLY first-layer external interface file.
# Generated: 2026-06-08 20:15:46

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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
