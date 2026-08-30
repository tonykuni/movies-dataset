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
<#
.SYNOPSIS
  Invoke-VRN-Activate-And-Validate.ps1
  VRN 系統一鍵啟動 + 健檢 + 雙組交叉驗證

.DESCRIPTION
  在 VRN 生產資料夾單擊執行：
    1. HardGate 7-tool BOOT_PRECHECK
    2. VRN_ENG008_HealthCheck.py — 25 檔完整性 + 跨模組規則一致性
    3. VRN_ENG001_ACTIVATEANDCROSSVALIDATE.py — 雙組獨立資料集交叉驗證
    4. 自動開啟 HTML 報告

.PARAMETER VrnDir
  VRN 生產資料夾（預設：腳本所在目錄）

.PARAMETER Python
  Python 執行檔（預設：py -3.12，遵循 LL#16）

.PARAMETER SkipHealthCheck
  跳過健檢，只跑 cross-validation

.PARAMETER SkipActivate
  只跑健檢，不跑 cross-validation

.PARAMETER OpenReports
  完成後自動開啟 HTML 報告（預設 $true）

.EXAMPLE
  .\Invoke-VRN-Activate-And-Validate.ps1
  # 一鍵全跑

.EXAMPLE
  .\Invoke-VRN-Activate-And-Validate.ps1 -SkipActivate
  # 只健檢

.NOTES
  Lesson Learned 對照：
    LL#10  block comment 不含 <# #>
    LL#12  Start-Process 開 HTML 不等待
    LL#15  block comment 不含 + - < >  → 用 # 行註解
    LL#16  Python 3.13 numba/ortools 不支援 → py -3.12
    LL#27-33 PS7 event-driven stdout/stderr handling
#>

#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$VrnDir = $PSScriptRoot,
    [string]$Python = "py",
    [string]$PythonArgs = "-3.12",
    [switch]$SkipHealthCheck,
    [switch]$SkipActivate,
    [switch]$NoOpenReports
)

# VIA Visual Lock console palette (ANSI)
$global:VIA_PALETTE = @{
    Header   = "`e[38;2;76;120;168m"     # #4c78a8
    Success  = "`e[38;2;67;154;154m"     # #439a9a
    Warning  = "`e[38;2;224;176;32m"     # #e0b020
    Error    = "`e[38;2;200;48;48m"      # #c83030
    Mono     = "`e[38;2;200;224;200m"    # #c8e0c8
    Reset    = "`e[0m"
    Bold     = "`e[1m"
    Dim      = "`e[2m"
}

function Write-VIAHeader {
    param([string]$Text)
    $bar = "═" * 76
    $p = $global:VIA_PALETTE
    Write-Host ""
    Write-Host "$($p.Header)$($p.Bold)$bar$($p.Reset)"
    Write-Host "$($p.Header)$($p.Bold)  $Text$($p.Reset)"
    Write-Host "$($p.Header)$($p.Bold)$bar$($p.Reset)"
}

function Write-VIASection {
    param([string]$Text)
    $p = $global:VIA_PALETTE
    Write-Host ""
    Write-Host "$($p.Header)─── $Text$($p.Reset)"
}

function Write-VIAStatus {
    param([string]$Status, [string]$Text)
    $p = $global:VIA_PALETTE
    $color = switch ($Status) {
        "READY"      { $p.Success }
        "OK"         { $p.Success }
        "PASS"       { $p.Success }
        "✓"          { $p.Success }
        "WARN"       { $p.Warning }
        "⚠"          { $p.Warning }
        "FAIL"       { $p.Error }
        "ERROR"      { $p.Error }
        "✗"          { $p.Error }
        "NEAR-READY" { $p.Warning }
        "NOT-READY"  { $p.Error }
        default      { $p.Mono }
    }
    Write-Host "$color  [$Status]$($p.Reset) $Text"
}

# ── BANNER ────────────────────────────────────────────────────────────────────

Write-VIAHeader "VRN System Activation + Cross-Validation"
$p = $global:VIA_PALETTE
Write-Host "$($p.Mono)  Script:    $($MyInvocation.MyCommand.Path)$($p.Reset)"
Write-Host "$($p.Mono)  VrnDir:    $VrnDir$($p.Reset)"
Write-Host "$($p.Mono)  Python:    $Python $PythonArgs$($p.Reset)"
Write-Host "$($p.Mono)  Started:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')$($p.Reset)"

# ── PRE-CHECKS ────────────────────────────────────────────────────────────────

Write-VIASection "Pre-flight Checks"

# Check VrnDir exists
if (-not (Test-Path -Path $VrnDir -PathType Container)) {
    Write-VIAStatus "ERROR" "VrnDir not found: $VrnDir"
    exit 2
}
Write-VIAStatus "OK" "VrnDir exists"

# Check Python available
$pyCheck = $null
try {
    $pyCheck = & $Python $PythonArgs --version 2>&1
} catch {
    Write-VIAStatus "ERROR" "Python launcher failed: $_"
    exit 2
}
if (-not $pyCheck -or $LASTEXITCODE -ne 0) {
    Write-VIAStatus "ERROR" "Python not available via '$Python $PythonArgs'"
    Write-Host "$($p.Mono)    Try: $Python --list  # to see installed versions$($p.Reset)"
    exit 2
}
Write-VIAStatus "OK" "Python: $pyCheck"

# Check core scripts present
$REQUIRED_SCRIPTS = @(
    "VRN_ENG008_HealthCheck.py",
    "VRN_ENG001_ACTIVATEANDCROSSVALIDATE.py",
    "VIA_HardGate_BootPrecheck.py"
)
$missingScripts = @()
foreach ($s in $REQUIRED_SCRIPTS) {
    $p2 = Join-Path $VrnDir $s
    if (-not (Test-Path $p2)) {
        $missingScripts += $s
    }
}
if ($missingScripts.Count -gt 0) {
    Write-VIAStatus "ERROR" "Missing required scripts: $($missingScripts -join ', ')"
    exit 2
}
Write-VIAStatus "OK" "All $($REQUIRED_SCRIPTS.Count) required scripts present"

# ── PHASE 1: HEALTHCHECK ──────────────────────────────────────────────────────

$healthCheckOK = $true
if (-not $SkipHealthCheck) {
    Write-VIASection "Phase 1: VRN_ENG008_HealthCheck.py"

    $hcScript = Join-Path $VrnDir "VRN_ENG008_HealthCheck.py"
    $t0 = Get-Date
    & $Python $PythonArgs $hcScript --vrn-dir $VrnDir
    $t1 = Get-Date
    $hcExit = $LASTEXITCODE
    $hcElapsed = ($t1 - $t0).TotalSeconds

    if ($hcExit -eq 0) {
        Write-VIAStatus "READY" ("HealthCheck completed in {0:F2}s" -f $hcElapsed)
        $healthCheckOK = $true
    } else {
        Write-VIAStatus "NEAR-READY" ("HealthCheck non-zero exit (code=$hcExit) in {0:F2}s" -f $hcElapsed)
        $healthCheckOK = $false
    }

    # Show summary stats from JSON
    $hcSumPath = Join-Path $VrnDir "VRN_HealthCheck_Summary.json"
    if (Test-Path $hcSumPath) {
        try {
            $hcSum = Get-Content $hcSumPath -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Host "$($p.Mono)    pass / warn / fail : $($hcSum.n_pass) / $($hcSum.n_warn) / $($hcSum.n_fail)$($p.Reset)"
            Write-Host "$($p.Mono)    classification     : $($hcSum.classification)$($p.Reset)"
            Write-Host "$($p.Mono)    files found        : $($hcSum.manifest_totals.found)/$($hcSum.manifest_totals.expected)$($p.Reset)"
        } catch {
            Write-VIAStatus "WARN" "Could not parse HealthCheck JSON: $_"
        }
    }
} else {
    Write-VIASection "Phase 1: HealthCheck (SKIPPED)"
}

# ── PHASE 2: ACTIVATE + CROSS-VALIDATE ────────────────────────────────────────

$activateOK = $true
if (-not $SkipActivate) {
    Write-VIASection "Phase 2: VRN_ENG001_ACTIVATEANDCROSSVALIDATE.py"

    $cvScript = Join-Path $VrnDir "VRN_ENG001_ACTIVATEANDCROSSVALIDATE.py"
    $t0 = Get-Date
    Push-Location $VrnDir
    try {
        & $Python $PythonArgs $cvScript
    } finally {
        Pop-Location
    }
    $t1 = Get-Date
    $cvExit = $LASTEXITCODE
    $cvElapsed = ($t1 - $t0).TotalSeconds

    if ($cvExit -eq 0) {
        Write-VIAStatus "READY" ("Activation completed in {0:F2}s" -f $cvElapsed)
        $activateOK = $true
    } else {
        Write-VIAStatus "NEAR-READY" ("Activation non-zero exit (code=$cvExit) in {0:F2}s" -f $cvElapsed)
        $activateOK = $false
    }

    # Show cross-validation summary
    $cvSumPath = Join-Path $VrnDir "cross_validation_summary.json"
    if (Test-Path $cvSumPath) {
        try {
            $cvSum = Get-Content $cvSumPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $cv = $cvSum.cross_validation
            Write-Host "$($p.Mono)    cross-validation : $($cv.n_pass)/$($cv.n_total) pass · $($cv.classification)$($p.Reset)"
            Write-Host "$($p.Mono)    activation_ok    : $($cvSum.activation_ok)$($p.Reset)"
            Write-Host "$($p.Mono)    Set A elapsed    : $($cvSum.set_A.elapsed)s$($p.Reset)"
            Write-Host "$($p.Mono)    Set B elapsed    : $($cvSum.set_B.elapsed)s$($p.Reset)"
        } catch {
            Write-VIAStatus "WARN" "Could not parse Cross-Validation JSON: $_"
        }
    }
} else {
    Write-VIASection "Phase 2: ACTIVATE (SKIPPED)"
}

# ── PHASE 3: REPORT OPENING ───────────────────────────────────────────────────

if (-not $NoOpenReports) {
    Write-VIASection "Phase 3: Open Reports"

    $reports = @(
        "VRN_HealthCheck_Report.html",
        "cross_validation_report.html"
    )
    foreach ($r in $reports) {
        $p2 = Join-Path $VrnDir $r
        if (Test-Path $p2) {
            try {
                # LL#12: Start-Process to open HTML, don't wait
                Start-Process $p2
                Write-VIAStatus "OK" "Opened: $r"
            } catch {
                Write-VIAStatus "WARN" "Could not open: $r ($_)"
            }
        } else {
            Write-VIAStatus "WARN" "Report not found: $r"
        }
    }
}

# ── FINAL VERDICT ─────────────────────────────────────────────────────────────

Write-VIAHeader "Final Verdict"

$overallOK = $healthCheckOK -and $activateOK
$verdict = if ($overallOK) { "READY" } else { "NEAR-READY" }
Write-VIAStatus $verdict "Overall System Status"

Write-Host ""
Write-Host "$($p.Mono)  HealthCheck      : $(if ($SkipHealthCheck) { 'SKIPPED' } elseif ($healthCheckOK) { '✓ READY' } else { '⚠ NEAR-READY' })$($p.Reset)"
Write-Host "$($p.Mono)  CrossValidation  : $(if ($SkipActivate) { 'SKIPPED' } elseif ($activateOK) { '✓ READY' } else { '⚠ NEAR-READY' })$($p.Reset)"
Write-Host "$($p.Mono)  Completed        : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')$($p.Reset)"
Write-Host ""

# Output reports paths
Write-Host "$($p.Header)  Reports in: $VrnDir$($p.Reset)"
Write-Host "$($p.Mono)    VRN_HealthCheck_Report.html$($p.Reset)"
Write-Host "$($p.Mono)    cross_validation_report.html$($p.Reset)"
Write-Host "$($p.Mono)    VRN_Production_Manifest.json$($p.Reset)"
Write-Host ""

exit $(if ($overallOK) { 0 } else { 1 })

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
