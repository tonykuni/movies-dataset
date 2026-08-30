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

$VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$VDF_DIR  = Join-Path $VIA_ROOT "functional modules\VDF"

$TargetJ = Join-Path $VDF_DIR "Invoke-VIA-v0114J-ExplicitFinalUserApprovalGate-NoStall-NoClose.ps1"
$ApprovalPhrase = "YES_I_ACCEPT_FINAL_APPLY_REVIEW_NEXT_ONLY_NO_APPLY_IN_v0114J"

function Step {
    param([int]$Now,[int]$Total,[string]$Msg)
    $pct = [int](($Now / $Total) * 100)
    Write-Progress -Activity "VIA v0114J OneClick Approval Launcher" -Status $Msg -PercentComplete $pct
    Write-Host "[$Now/$Total] $Msg" -ForegroundColor Cyan
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114J ONE-CLICK APPROVAL LAUNCHER · NO APPLY" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: No apply · No source mutation · No canonical merge · No DB write · No close" -ForegroundColor Yellow

    Step 1 6 "Check v0114J target script"
    if (-not (Test-Path -LiteralPath $TargetJ)) {
        throw "Missing target script: $TargetJ"
    }

    Step 2 6 "AST syntax check target"
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($TargetJ, [ref]$tokens, [ref]$errors) | Out-Null

    if ($errors -and @($errors).Count -gt 0) {
        Write-Host "[FAIL] AST parser found errors in v0114J target." -ForegroundColor Red
        $errors | Select-Object Message, Extent | Format-List
        throw "Target script AST failed."
    }

    Write-Host "[OK] AST clean." -ForegroundColor Green

    Step 3 6 "Run v0114J with exact approval phrase"
    & $TargetJ `
        -def_PARAM_FINAL_USER_APPLY_ACCEPT $ApprovalPhrase `
        -def_PARAM_OPEN_REPORT $true

    Step 4 6 "Find latest v0114J run"
    $RootJ = Join-Path $VDF_DIR "_integration_v0114J_explicit_final_user_approval_gate"

    if (-not (Test-Path -LiteralPath $RootJ)) {
        throw "v0114J output root not found: $RootJ"
    }

    $LatestJ = Get-ChildItem -LiteralPath $RootJ -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0114J_ExplicitFinalUserApprovalGate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $LatestJ) {
        throw "No v0114J summary found."
    }

    $SummaryPath = Join-Path $LatestJ.FullName "output\VIA_v0114J_ExplicitFinalUserApprovalGate_Summary.json"
    $ReadinessPath = Join-Path $LatestJ.FullName "output\VIA_v0114J_ReadinessGate.csv"
    $ValidationPath = Join-Path $LatestJ.FullName "output\VIA_v0114J_ValidationMatrix.csv"

    Step 5 6 "Validate v0114J output"
    $Summary = Get-Content -LiteralPath $SummaryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $Ready = @(Import-Csv -LiteralPath $ReadinessPath)[0]
    $Validation = @(Import-Csv -LiteralPath $ValidationPath)

    $FailRows = @($Validation | Where-Object { $_.def_status -ne "PASS" }).Count

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114J ONE-CLICK RESULT" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "LatestJ           : $($LatestJ.FullName)" -ForegroundColor Cyan
    Write-Host "Gate              : $($Ready.def_gate_status)" -ForegroundColor Yellow
    Write-Host "Allow v0114K      : $($Ready.def_allow_v0114K)" -ForegroundColor Yellow
    Write-Host "Validation Fail   : $($Ready.def_validation_fail)" -ForegroundColor Yellow
    Write-Host "Technical Fail    : $($Ready.def_technical_fail)" -ForegroundColor Yellow
    Write-Host "Approval Fail     : $($Ready.def_approval_fail)" -ForegroundColor Yellow
    Write-Host "Final User Accept : $($Ready.def_final_user_apply_accept)" -ForegroundColor Yellow
    Write-Host "Apply             : $($Ready.def_apply_enabled)" -ForegroundColor Yellow
    Write-Host "Mutation          : $($Ready.def_source_mutation)" -ForegroundColor Yellow
    Write-Host "Canonical         : $($Ready.def_canonical_merge)" -ForegroundColor Yellow
    Write-Host "DB Write          : $($Ready.def_db_write)" -ForegroundColor Yellow

    if (
        $Ready.def_allow_v0114K -eq "true" -and
        $Ready.def_final_user_apply_accept -eq "YES" -and
        $Ready.def_apply_enabled -eq "false" -and
        $Ready.def_source_mutation -eq "false" -and
        $Ready.def_canonical_merge -eq "false" -and
        $Ready.def_db_write -eq "false"
    ) {
        Write-Host ""
        Write-Host "[PASS] v0114J approved. READY_FOR_v0114K_FINAL_APPLY_EXECUTION_CANDIDATE_REVIEW_ONLY." -ForegroundColor Green
        Write-Host "[SAFE] v0114J did NOT apply anything." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[BLOCKED] v0114J did not reach v0114K readiness. Review report." -ForegroundColor Red
    }

    Step 6 6 "Open output folders"
    try { Start-Process -FilePath $LatestJ.FullName } catch {}
    try { Start-Process -FilePath (Join-Path $LatestJ.FullName "report") } catch {}
    try { Start-Process -FilePath (Join-Path $LatestJ.FullName "output") } catch {}

    Write-Progress -Activity "VIA v0114J OneClick Approval Launcher" -Completed

} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow
    return
} finally {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · PowerShell remains open" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
