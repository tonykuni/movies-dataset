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
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114D_sandbox_review_seal\RUN_20260622_211832_VIA_v0114D_SANDBOX_REVIEW_SEAL\output\VIA_v0114D_ReadinessGate.csv
"
$DecisionCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114D_sandbox_review_seal\RUN_20260622_211832_VIA_v0114D_SANDBOX_REVIEW_SEAL\_manual_release_gate_draft\VIA_v0114D_USER_EDIT_ManualReleaseDecision.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
if (-not (Test-Path -LiteralPath $DecisionCsv)) { throw "Missing decision csv: $DecisionCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
$d = @(Import-Csv -LiteralPath $DecisionCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114E Precheck after v0114D" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114E)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "User Accept: $($d.def_user_release_accept)" -ForegroundColor Yellow
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114E -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114E." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114E_MANUAL_RELEASE_APPROVAL_GATE_ONLY" -ForegroundColor Green

