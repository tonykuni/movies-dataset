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
$ErrorActionPreference = "Stop"
$ReadinessCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114T_final_release_package_validation_only\RUN_20260623_021149_VIA_v0114T_FINAL_RELEASE_PACKAGE_VALIDATION_ONLY\output\VIA_v0114T_ReadinessGate.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114U Precheck after v0114T" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114U)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "Rows       : $($r.def_release_package_validation_rows)" -ForegroundColor Cyan
Write-Host "Execution  : $($r.def_execution_enabled)" -ForegroundColor Yellow
Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114U -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114U." }
if ($r.def_execution_enabled -ne "false" -or $r.def_apply_enabled -ne "false") { throw "BLOCKED_EXECUTION_OR_APPLY_SHOULD_BE_DISABLED." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114U_FINAL_RELEASE_FREEZE_SEAL_ONLY" -ForegroundColor Green

