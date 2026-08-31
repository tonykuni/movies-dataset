#requires -Version 7.0
# =============================================================================
# Invoke-VIA-OnePaste-Pipeline.ps1  v1.1
# VIA · One-Paste Apply Pipeline (SSOT v22 + VRN v2.2)
#
# v1.1 fix:
#   - Replace array splatting (@args) with hashtable splatting (@ssotParams /
#     @vrnParams). Array splat collided with PS automatic $args variable,
#     causing -PatchFile to be consumed as $VIA_ROOT positional arg in wrapper.
#
# 功能(append-only,功能只增不減):
#   1. 自動定位 3 個交付檔(Downloads / OneDrive Desktop / Desktop / CWD)
#   2. Unblock-File(解除 MOTW)
#   3. Process-scope ExecutionPolicy Bypass(不改 system policy)
#   4. 跑 SSOT v22 同義字 auto-append wrapper(idempotent · skip 若已 append)
#   5. py_compile + 13/13 lookup self-test 驗證 SSOT
#   6. 跑 VRN v2.2 stock-only visual full extractor
#   7. 收集 KPI(input file count / stock / reject / strong_reject hit counts)
#   8. 產生 pipeline summary HTML 報告(VIA Visual Lock 樣式)
#   9. 自動開啟 summary HTML + VRN HTML
#  10. 永遠不關 PS7 session(失敗也是)
#
# LL 規範:
#   - param() at very top, only #requires & #-comments before
#   - 無 <# #> block comments
#   - $script: scope discipline
#   - Sort-Object hashtable syntax
#   - [System.IO.File]::WriteAllText 收斂在 Write-TextAtomic
#   - 中文 console output
# =============================================================================

param(
    [string]$VIA_ROOT      = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics",
    [string]$DownloadsDir  = "",
    [string]$DesktopDir    = "",
    [switch]$SkipSSOT,
    [switch]$SkipVRN,
    [switch]$NoOpenHtml,
    [switch]$VerifyOnly
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
$ErrorActionPreference = "Continue"
$ProgressPreference    = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# =============================================================================
# def CONSTANTS
# =============================================================================
$script:VIA_ROOT      = $VIA_ROOT
$script:SUPPORT_DIR   = Join-Path $VIA_ROOT "module\supportive_module"
$script:SSOT_FILE     = Join-Path $script:SUPPORT_DIR "VIA_SSOT_Unified.py"
$script:VRN_DIR       = Join-Path $VIA_ROOT "module\VRN"
$script:INPUT_DIR     = Join-Path $script:VRN_DIR "input"
$script:TIMESTAMP     = Get-Date -Format "yyyyMMdd_HHmmss"
$script:PIPELINE_ROOT = Join-Path $script:VRN_DIR "_pipeline_runs\Pipeline_$($script:TIMESTAMP)"

if (-not $DownloadsDir) { $DownloadsDir = "$env:USERPROFILE\Downloads" }
if (-not $DesktopDir)   { $DesktopDir   = "$env:USERPROFILE\OneDrive\Desktop" }

$script:DELIVERY_FILES = @(
    @{
        Name        = "Invoke-VIA-SSOT-v22-Append-v2.ps1"
        Role        = "ssot_wrapper"
        Required    = $true
        Description = "SSOT v22 同義字 auto-append PS7 wrapper"
    },
    @{
        Name        = "SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py"
        Role        = "ssot_patch"
        Required    = $true
        Description = "SSOT 同義字 patch(55 keys / 361 synonyms)"
    },
    @{
        Name        = "VRN_StockOnlyVisualFull_v2.2.ps1"
        Role        = "vrn_extractor"
        Required    = $true
        Description = "VRN v2.2 stock-only visual full extractor"
    }
)

$script:SEARCH_DIRS = @($DownloadsDir, $DesktopDir, "$env:USERPROFILE\Desktop", (Get-Location).Path)

$script:PIPELINE_STATE = [ordered]@{
    pipeline_started_at = (Get-Date).ToString("s")
    timestamp           = $script:TIMESTAMP
    via_root            = $script:VIA_ROOT
    pipeline_dir        = $script:PIPELINE_ROOT
    found_files         = @{}
    missing_files       = @()
    ssot_state          = "PENDING"
    ssot_output         = ""
    ssot_exit_code      = -1
    ssot_already        = $false
    ssot_canonical_keys = 0
    ssot_synonyms       = 0
    ssot_tests_pass     = 0
    ssot_tests_total    = 0
    vrn_state           = "PENDING"
    vrn_output          = ""
    vrn_exit_code       = -1
    vrn_html            = ""
    vrn_input_count     = 0
    vrn_stock_count     = 0
    vrn_reject_count    = 0
    vrn_strong_reject   = 0
    vrn_ssot_loaded     = $false
    overall             = "PENDING"
    fatal_message       = ""
    pipeline_ended_at   = ""
}

# =============================================================================
# def UTILITIES
# =============================================================================
function Save-Log {
    param([string]$Line, [string]$Color = "Gray")
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Line) -ForegroundColor $Color
}

function Write-Banner {
    param([string]$Text, [string]$Color = "Cyan")
    $bar = "═" * 75
    Write-Host ""
    Write-Host $bar -ForegroundColor $Color
    Write-Host ("  " + $Text) -ForegroundColor $Color
    Write-Host $bar -ForegroundColor $Color
}

function Write-Section {
    param([string]$Text)
    $bar = "─" * 75
    Write-Host ""
    Write-Host $bar -ForegroundColor DarkGray
    Write-Host ("  " + $Text) -ForegroundColor Cyan
    Write-Host $bar -ForegroundColor DarkGray
}

function Write-TextAtomic {
    param([string]$Path, [string]$Content)
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Content)
    $tmp = $Path + ".tmp_pipe_" + $script:TIMESTAMP
    [System.IO.File]::WriteAllBytes($tmp, $bytes)
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

function Test-FileExists {
    param([string]$Path)
    if ([string]::IsNullOrEmpty($Path)) { return $false }
    return (Test-Path -LiteralPath $Path -PathType Leaf)
}

function Html-Esc {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

# =============================================================================
# def FILE LOCATION
# =============================================================================
function Find-DeliveryFiles {
    Save-Log "Locating delivery files..." "DarkCyan"
    foreach ($entry in $script:DELIVERY_FILES) {
        $found = ""
        foreach ($dir in $script:SEARCH_DIRS) {
            if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
            $candidate = Join-Path $dir $entry.Name
            if (Test-FileExists $candidate) { $found = $candidate; break }
        }
        if ($found) {
            $script:PIPELINE_STATE.found_files[$entry.Name] = $found
            Save-Log ("  OK    " + $entry.Name.PadRight(50) + "  ←  " + (Split-Path $found -Parent)) "DarkGray"
        } elseif ($entry.Required) {
            $script:PIPELINE_STATE.missing_files += $entry.Name
            Save-Log ("  MISS  " + $entry.Name) "Red"
        }
    }
    if ($script:PIPELINE_STATE.missing_files.Count -gt 0) {
        Write-Host ""
        Write-Host "[FATAL] 以下檔案找不到。請從 Claude 對話下載到 Downloads/Desktop:" -ForegroundColor Red
        foreach ($miss in $script:PIPELINE_STATE.missing_files) {
            Write-Host ("    - " + $miss) -ForegroundColor Red
        }
        Write-Host "搜尋過的目錄:" -ForegroundColor Yellow
        foreach ($d in $script:SEARCH_DIRS) {
            Write-Host ("    - " + $d) -ForegroundColor Yellow
        }
        throw "Missing required delivery files"
    }
}

# =============================================================================
# def UNBLOCK + EXECUTION POLICY
# =============================================================================
function Initialize-Environment {
    Save-Log "Setting ExecutionPolicy = Bypass (Process scope only)..." "DarkCyan"
    try {
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue
    } catch {}

    Save-Log "Unblock-File on all delivery files..." "DarkCyan"
    foreach ($path in $script:PIPELINE_STATE.found_files.Values) {
        try {
            Unblock-File -LiteralPath $path -ErrorAction SilentlyContinue
        } catch {}
    }
    Save-Log "Environment ready." "Green"
}

# =============================================================================
# def SSOT STEP
# =============================================================================
function Invoke-SSOTStep {
    if ($SkipSSOT) {
        Save-Log "SSOT step skipped (-SkipSSOT)" "Yellow"
        $script:PIPELINE_STATE.ssot_state = "SKIPPED"
        return
    }

    $wrapper = $script:PIPELINE_STATE.found_files["Invoke-VIA-SSOT-v22-Append-v2.ps1"]
    $patch   = $script:PIPELINE_STATE.found_files["SUP_MDL655_SSOTUnifiedV22SynonymsPatch.py"]

    Write-Section "STEP 1/2 · Applying SSOT v22 Synonyms"

    $ssotParams = @{
        PatchFile = $patch
    }
    if ($VerifyOnly) { $ssotParams.VerifyOnly = $true }

    $captured = [System.Collections.Generic.List[string]]::new()
    try {
        $output = & $wrapper @ssotParams 2>&1
        $rc = $LASTEXITCODE
        foreach ($line in $output) {
            $s = [string]$line
            $captured.Add($s)
            $color = "Gray"
            if ($s -match "FATAL|FAIL") { $color = "Red" }
            elseif ($s -match "OK|PASS|DONE|Append complete") { $color = "Green" }
            elseif ($s -match "WARN|Skip|Marker") { $color = "Yellow" }
            elseif ($s -match "^\[\d{2}:") { $color = "DarkCyan" }
            Write-Host $s -ForegroundColor $color
        }
    } catch {
        $rc = -1
        $captured.Add("[CAUGHT] " + $_.Exception.Message)
        Write-Host ("[CAUGHT] " + $_.Exception.Message) -ForegroundColor Red
    }

    $joined = ($captured -join "`n")
    $script:PIPELINE_STATE.ssot_output    = $joined
    $script:PIPELINE_STATE.ssot_exit_code = $rc

    $mKeys     = [regex]::Match($joined, 'canonical_keys\s*=\s*(\d+)')
    $mSyn      = [regex]::Match($joined, 'total_synonyms\s*=\s*(\d+)')
    $mTests    = [regex]::Match($joined, '\[RESULT\]\s+(\d+)/(\d+)\s+lookup tests passed')
    if ($mKeys.Success)  { $script:PIPELINE_STATE.ssot_canonical_keys = [int]$mKeys.Groups[1].Value }
    if ($mSyn.Success)   { $script:PIPELINE_STATE.ssot_synonyms       = [int]$mSyn.Groups[1].Value }
    if ($mTests.Success) {
        $script:PIPELINE_STATE.ssot_tests_pass  = [int]$mTests.Groups[1].Value
        $script:PIPELINE_STATE.ssot_tests_total = [int]$mTests.Groups[2].Value
    }
    if ($joined -match "already exists in SSOT") {
        $script:PIPELINE_STATE.ssot_already = $true
    }

    if ($joined -match "DONE · VIA SSOT v22 Synonyms APPENDED & VERIFIED" -or
        $script:PIPELINE_STATE.ssot_tests_pass -eq $script:PIPELINE_STATE.ssot_tests_total -and $script:PIPELINE_STATE.ssot_tests_total -gt 0) {
        $script:PIPELINE_STATE.ssot_state = "PASS"
        Save-Log "SSOT v22 verified." "Green"
    } else {
        $script:PIPELINE_STATE.ssot_state = "FAIL"
        Save-Log "SSOT v22 step did NOT confirm PASS — check log above" "Red"
    }
}

# =============================================================================
# def VRN STEP
# =============================================================================
function Invoke-VRNStep {
    if ($SkipVRN) {
        Save-Log "VRN step skipped (-SkipVRN)" "Yellow"
        $script:PIPELINE_STATE.vrn_state = "SKIPPED"
        return
    }
    if ($VerifyOnly) {
        Save-Log "VerifyOnly — skipping VRN run." "Yellow"
        $script:PIPELINE_STATE.vrn_state = "SKIPPED_VERIFY_ONLY"
        return
    }
    if ($script:PIPELINE_STATE.ssot_state -eq "FAIL") {
        Save-Log "SSOT FAIL — abort VRN step (no point running)" "Red"
        $script:PIPELINE_STATE.vrn_state = "ABORTED_DUE_TO_SSOT_FAIL"
        return
    }

    $extractor = $script:PIPELINE_STATE.found_files["VRN_StockOnlyVisualFull_v2.2.ps1"]

    Write-Section "STEP 2/2 · Running VRN v2.2 Stock-Only Extractor"

    $captured = [System.Collections.Generic.List[string]]::new()
    try {
        $vrnParams = @{}
        if ($NoOpenHtml) { $vrnParams.NoOpenHtml = $true }
        $output = & $extractor @vrnParams 2>&1
        $rc = $LASTEXITCODE
        foreach ($line in $output) {
            $s = [string]$line
            $captured.Add($s)
            $color = "Gray"
            if ($s -match "FATAL|FAIL|Error") { $color = "Red" }
            elseif ($s -match "OK|PASS|DONE|SUCCESS") { $color = "Green" }
            elseif ($s -match "WARN|Skip") { $color = "Yellow" }
            elseif ($s -match "^\[OK\]|^\[RUN\]") { $color = "Cyan" }
            Write-Host $s -ForegroundColor $color
        }
    } catch {
        $rc = -1
        $captured.Add("[CAUGHT] " + $_.Exception.Message)
        Write-Host ("[CAUGHT] " + $_.Exception.Message) -ForegroundColor Red
    }

    $joined = ($captured -join "`n")
    $script:PIPELINE_STATE.vrn_output    = $joined
    $script:PIPELINE_STATE.vrn_exit_code = $rc

    $mInputs = [regex]::Match($joined, 'INPUT[_\s]+FILES?\D+(\d+)', 'IgnoreCase')
    $mHtml   = [regex]::Match($joined, '\[HTML\]\s+(.+?\.html)', 'IgnoreCase')
    if ($mInputs.Success) { $script:PIPELINE_STATE.vrn_input_count = [int]$mInputs.Groups[1].Value }
    if ($mHtml.Success)   { $script:PIPELINE_STATE.vrn_html = $mHtml.Groups[1].Value.Trim() }

    if (-not $script:PIPELINE_STATE.vrn_html) {
        $latest = Get-ChildItem -LiteralPath (Join-Path $script:VRN_DIR "_full_extract_runs") -Recurse -Filter "*.html" -ErrorAction SilentlyContinue |
                  Sort-Object -Property @{e="LastWriteTime"; desc=$true} |
                  Select-Object -First 1
        if ($latest) { $script:PIPELINE_STATE.vrn_html = $latest.FullName }
    }

    if (Test-FileExists $script:PIPELINE_STATE.vrn_html) {
        try {
            $htmlText = Get-Content -LiteralPath $script:PIPELINE_STATE.vrn_html -Raw -Encoding UTF8
            $mStock  = [regex]::Match($htmlText, 'Stock Reports[^<]*<[^>]*>\s*(\d+)', 'IgnoreCase')
            $mRej    = [regex]::Match($htmlText, 'Rejected[^<]*<[^>]*>\s*(\d+)', 'IgnoreCase')
            $mIn2    = [regex]::Match($htmlText, 'Input Files[^<]*<[^>]*>\s*(\d+)', 'IgnoreCase')
            $mStrong = [regex]::Matches($htmlText, 'STRONG[\s_]?REJECT', 'IgnoreCase')
            if ($mStock.Success) { $script:PIPELINE_STATE.vrn_stock_count = [int]$mStock.Groups[1].Value }
            if ($mRej.Success)   { $script:PIPELINE_STATE.vrn_reject_count = [int]$mRej.Groups[1].Value }
            if ($mIn2.Success -and $script:PIPELINE_STATE.vrn_input_count -eq 0) {
                $script:PIPELINE_STATE.vrn_input_count = [int]$mIn2.Groups[1].Value
            }
            $script:PIPELINE_STATE.vrn_strong_reject = $mStrong.Count
            if ($htmlText -match 'SSOT loaded') { $script:PIPELINE_STATE.vrn_ssot_loaded = $true }
        } catch {
            Save-Log ("HTML parse warning: " + $_.Exception.Message) "Yellow"
        }
    }

    if ($rc -eq 0 -and $script:PIPELINE_STATE.vrn_input_count -gt 0) {
        $script:PIPELINE_STATE.vrn_state = "PASS"
        Save-Log "VRN v2.2 extractor completed." "Green"
    } else {
        $script:PIPELINE_STATE.vrn_state = "FAIL"
        Save-Log "VRN v2.2 extractor did not confirm PASS" "Red"
    }
}

# =============================================================================
# def SUMMARY HTML REPORT
# =============================================================================
function Write-SummaryHtml {
    $st = $script:PIPELINE_STATE

    $ssotBadge = switch ($st.ssot_state) {
        "PASS"    { "<span class='b ok'>PASS</span>" }
        "SKIPPED" { "<span class='b skip'>SKIPPED</span>" }
        "FAIL"    { "<span class='b bad'>FAIL</span>" }
        default   { "<span class='b warn'>PENDING</span>" }
    }
    $vrnBadge = switch ($st.vrn_state) {
        "PASS"    { "<span class='b ok'>PASS</span>" }
        "SKIPPED" { "<span class='b skip'>SKIPPED</span>" }
        "SKIPPED_VERIFY_ONLY" { "<span class='b skip'>VERIFY_ONLY</span>" }
        "ABORTED_DUE_TO_SSOT_FAIL" { "<span class='b bad'>ABORTED</span>" }
        "FAIL"    { "<span class='b bad'>FAIL</span>" }
        default   { "<span class='b warn'>PENDING</span>" }
    }
    $overallBadge = switch ($st.overall) {
        "PASS"    { "<span class='b ok'>PIPELINE PASS</span>" }
        "PARTIAL" { "<span class='b warn'>PIPELINE PARTIAL</span>" }
        "FAIL"    { "<span class='b bad'>PIPELINE FAIL</span>" }
        default   { "<span class='b warn'>UNKNOWN</span>" }
    }

    $filesHtml = ""
    foreach ($entry in $script:DELIVERY_FILES) {
        $name = $entry.Name
        $path = if ($st.found_files.ContainsKey($name)) { $st.found_files[$name] } else { "(NOT FOUND)" }
        $cls  = if ($st.found_files.ContainsKey($name)) { "ok" } else { "bad" }
        $filesHtml += "<tr><td class='mono'>" + (Html-Esc $name) + "</td><td class='" + $cls + "'>" + (if ($cls -eq "ok") {"FOUND"} else {"MISSING"}) + "</td><td class='path'>" + (Html-Esc $path) + "</td><td>" + (Html-Esc $entry.Description) + "</td></tr>"
    }

    $ssotOutEsc = Html-Esc $st.ssot_output
    $vrnOutEsc  = Html-Esc $st.vrn_output

    $ssotLoadedCls = if ($st.vrn_ssot_loaded) { "ok" } else { "warn" }
    $ssotLoadedTxt = if ($st.vrn_ssot_loaded) { "YES" } else { "NO / unknown" }

    $cssVarsHeader = "Generated " + $st.timestamp + " · pipeline_dir " + $st.pipeline_dir

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Pipeline Summary · $($st.timestamp)</title>
<style>
:root{--bg:#f5f4f0;--ink:#1a1a1a;--mute:#6b6b6b;--line:#e8e6df;--blue:#4c78a8;--teal:#439a9a;--ok:#2f7d32;--warn:#9a6a00;--bad:#b42318;--card:#ffffff}
*{box-sizing:border-box}
body{font-family:'Syne','DM Sans','Microsoft JhengHei',sans-serif;background:var(--bg);color:var(--ink);margin:0;font-size:11px;line-height:1.55}
.rb{height:6px;background:linear-gradient(90deg,#e63946,#f4a261,#e9c46a,#2a9d8f,#264653,#9b5de5)}
header{padding:28px 36px 18px;border-bottom:1px solid var(--line)}
header h1{font-family:'Syne',sans-serif;font-size:28px;font-weight:700;margin:0 0 6px;letter-spacing:.5px}
header .sub{color:var(--mute);font-size:11px}
.wrap{padding:24px 36px}
.kpi{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:18px}
.cd{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px 16px}
.cd-h{font-size:10px;color:var(--mute);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px}
.cd-b{font-family:'DM Mono',monospace;font-size:22px;font-weight:700}
.cd-i{font-size:10px;color:var(--mute);margin-top:4px}
.b{display:inline-block;padding:3px 8px;border-radius:3px;font-family:'DM Mono',monospace;font-size:10px;font-weight:700;letter-spacing:.5px}
.b.ok{background:#dcecdc;color:var(--ok)}
.b.warn{background:#fdf0d0;color:var(--warn)}
.b.bad{background:#fde2de;color:var(--bad)}
.b.skip{background:#e8e6df;color:var(--mute)}
.section{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:18px 20px;margin-bottom:14px}
.section h2{font-family:'Syne',sans-serif;font-size:14px;font-weight:600;margin:0 0 12px;letter-spacing:.3px}
table{width:100%;border-collapse:collapse;font-size:10px}
th{font-weight:600;text-align:left;border-bottom:1px solid var(--line);padding:8px 6px;text-transform:uppercase;font-size:9px;letter-spacing:.5px;color:var(--mute)}
td{padding:7px 6px;border-bottom:1px solid var(--line);vertical-align:top}
td.mono,td.path{font-family:'DM Mono',monospace;font-size:9px}
td.path{color:var(--mute);word-break:break-all}
td.ok{color:var(--ok);font-weight:700}
td.bad{color:var(--bad);font-weight:700}
td.warn{color:var(--warn);font-weight:700}
.tm{background:#0d0d0d;color:#d1d5db;border-radius:6px;padding:14px 16px;font-family:'DM Mono',monospace;font-size:9.5px;white-space:pre-wrap;word-break:break-all;max-height:380px;overflow:auto;position:relative}
.tm::before{content:'';position:absolute;top:8px;left:12px;width:8px;height:8px;border-radius:50%;background:#ff5f56;box-shadow:14px 0 #ffbd2e,28px 0 #27c93f}
.tm{padding-top:30px}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
.muted{color:var(--mute)}
.tag{display:inline-block;padding:1px 6px;background:var(--line);border-radius:2px;font-size:9px;font-family:'DM Mono',monospace;color:var(--mute)}
</style>
</head>
<body>
<div class="rb"></div>
<header>
<h1>VIA Pipeline Summary</h1>
<div class="sub">$cssVarsHeader</div>
</header>
<div class="wrap">

<div class="kpi">
<div class="cd"><div class="cd-h">OVERALL</div><div class="cd-b">$overallBadge</div></div>
<div class="cd"><div class="cd-h">SSOT v22</div><div class="cd-b">$ssotBadge</div><div class="cd-i">$($st.ssot_tests_pass)/$($st.ssot_tests_total) lookup tests</div></div>
<div class="cd"><div class="cd-h">VRN v2.2</div><div class="cd-b">$vrnBadge</div><div class="cd-i">exit=$($st.vrn_exit_code)</div></div>
<div class="cd"><div class="cd-h">SSOT Keys</div><div class="cd-b">$($st.ssot_canonical_keys)</div><div class="cd-i">$($st.ssot_synonyms) synonyms</div></div>
<div class="cd"><div class="cd-h">VRN Stock</div><div class="cd-b">$($st.vrn_stock_count)</div><div class="cd-i">/$($st.vrn_input_count) input</div></div>
<div class="cd"><div class="cd-h">VRN Reject</div><div class="cd-b">$($st.vrn_reject_count)</div><div class="cd-i">STRONG hits: $($st.vrn_strong_reject)</div></div>
</div>

<div class="section">
<h2>01 · Delivery Files</h2>
<table>
<thead><tr><th>Filename</th><th>Status</th><th>Path</th><th>Description</th></tr></thead>
<tbody>$filesHtml</tbody>
</table>
</div>

<div class="section">
<h2>02 · SSOT v22 Result</h2>
<p>
<span class="tag">state</span> $ssotBadge &nbsp;
<span class="tag">exit</span> <span class="mono">$($st.ssot_exit_code)</span> &nbsp;
<span class="tag">already_applied</span> <span class="mono">$($st.ssot_already)</span> &nbsp;
<span class="tag">canonical_keys</span> <span class="mono">$($st.ssot_canonical_keys)</span> &nbsp;
<span class="tag">total_synonyms</span> <span class="mono">$($st.ssot_synonyms)</span> &nbsp;
<span class="tag">lookup</span> <span class="mono">$($st.ssot_tests_pass)/$($st.ssot_tests_total)</span>
</p>
<div class="tm">$ssotOutEsc</div>
</div>

<div class="section">
<h2>03 · VRN v2.2 Result</h2>
<p>
<span class="tag">state</span> $vrnBadge &nbsp;
<span class="tag">exit</span> <span class="mono">$($st.vrn_exit_code)</span> &nbsp;
<span class="tag">input</span> <span class="mono">$($st.vrn_input_count)</span> &nbsp;
<span class="tag">stock</span> <span class="mono">$($st.vrn_stock_count)</span> &nbsp;
<span class="tag">reject</span> <span class="mono">$($st.vrn_reject_count)</span> &nbsp;
<span class="tag">strong_reject_hits</span> <span class="mono">$($st.vrn_strong_reject)</span> &nbsp;
<span class="tag">SSOT_loaded</span> <span class="$ssotLoadedCls"><b>$ssotLoadedTxt</b></span>
</p>
<p class="path">VRN HTML: $(Html-Esc $st.vrn_html)</p>
<div class="tm">$vrnOutEsc</div>
</div>

<div class="section">
<h2>04 · Pipeline Metadata</h2>
<table>
<tbody>
<tr><td>started_at</td><td class="mono">$($st.pipeline_started_at)</td></tr>
<tr><td>ended_at</td><td class="mono">$($st.pipeline_ended_at)</td></tr>
<tr><td>timestamp</td><td class="mono">$($st.timestamp)</td></tr>
<tr><td>via_root</td><td class="path">$($st.via_root)</td></tr>
<tr><td>ssot_file</td><td class="path">$($script:SSOT_FILE)</td></tr>
<tr><td>vrn_input_dir</td><td class="path">$($script:INPUT_DIR)</td></tr>
<tr><td>pipeline_dir</td><td class="path">$($st.pipeline_dir)</td></tr>
</tbody>
</table>
</div>

</div>
</body>
</html>
"@

    $summaryHtml = Join-Path $script:PIPELINE_ROOT ("VIA_Pipeline_Summary_" + $script:TIMESTAMP + ".html")
    Write-TextAtomic -Path $summaryHtml -Content $html

    $summaryJson = Join-Path $script:PIPELINE_ROOT ("VIA_Pipeline_Summary_" + $script:TIMESTAMP + ".json")
    $jsonText = $st | ConvertTo-Json -Depth 6
    Write-TextAtomic -Path $summaryJson -Content $jsonText

    return @{ Html = $summaryHtml; Json = $summaryJson }
}

# =============================================================================
# def MAIN
# =============================================================================
function Invoke-Main {
    Write-Banner "VIA · One-Paste Apply Pipeline (SSOT v22 + VRN v2.2)"

    if (-not (Test-Path -LiteralPath $script:PIPELINE_ROOT)) {
        New-Item -ItemType Directory -Path $script:PIPELINE_ROOT -Force | Out-Null
    }
    Save-Log ("Pipeline workdir: " + $script:PIPELINE_ROOT) "DarkCyan"
    Save-Log ("VIA_ROOT       : " + $script:VIA_ROOT) "DarkCyan"
    Save-Log ("SSOT file      : " + $script:SSOT_FILE) "DarkCyan"
    Save-Log ("VRN input dir  : " + $script:INPUT_DIR) "DarkCyan"

    Write-Section "STEP 0/2 · Environment Setup"
    Find-DeliveryFiles
    Initialize-Environment

    Invoke-SSOTStep
    Invoke-VRNStep

    # Determine overall state
    if ($script:PIPELINE_STATE.ssot_state -eq "PASS" -and $script:PIPELINE_STATE.vrn_state -eq "PASS") {
        $script:PIPELINE_STATE.overall = "PASS"
    } elseif ($script:PIPELINE_STATE.ssot_state -eq "FAIL" -or $script:PIPELINE_STATE.vrn_state -eq "FAIL") {
        $script:PIPELINE_STATE.overall = "FAIL"
    } else {
        $script:PIPELINE_STATE.overall = "PARTIAL"
    }
    $script:PIPELINE_STATE.pipeline_ended_at = (Get-Date).ToString("s")

    Write-Section "Generating Pipeline Summary HTML + JSON"
    $reports = Write-SummaryHtml
    Save-Log ("Summary HTML: " + $reports.Html) "Green"
    Save-Log ("Summary JSON: " + $reports.Json) "Green"

    if (-not $NoOpenHtml -and (Test-FileExists $reports.Html)) {
        try { Start-Process $reports.Html } catch {}
    }
    if (-not $NoOpenHtml -and (Test-FileExists $script:PIPELINE_STATE.vrn_html)) {
        try { Start-Process $script:PIPELINE_STATE.vrn_html } catch {}
    }

    # Final banner
    $color = switch ($script:PIPELINE_STATE.overall) {
        "PASS"    { "Green" }
        "PARTIAL" { "Yellow" }
        "FAIL"    { "Red" }
        default   { "Yellow" }
    }
    Write-Banner ("PIPELINE " + $script:PIPELINE_STATE.overall) $color

    Write-Host ("  SSOT v22         : " + $script:PIPELINE_STATE.ssot_state) -ForegroundColor $color
    Write-Host ("  · canonical_keys : " + $script:PIPELINE_STATE.ssot_canonical_keys) -ForegroundColor DarkGray
    Write-Host ("  · synonyms       : " + $script:PIPELINE_STATE.ssot_synonyms) -ForegroundColor DarkGray
    Write-Host ("  · lookup_tests   : " + $script:PIPELINE_STATE.ssot_tests_pass + "/" + $script:PIPELINE_STATE.ssot_tests_total) -ForegroundColor DarkGray
    Write-Host ("  · already_done   : " + $script:PIPELINE_STATE.ssot_already) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host ("  VRN v2.2         : " + $script:PIPELINE_STATE.vrn_state) -ForegroundColor $color
    Write-Host ("  · input          : " + $script:PIPELINE_STATE.vrn_input_count) -ForegroundColor DarkGray
    Write-Host ("  · stock_reports  : " + $script:PIPELINE_STATE.vrn_stock_count) -ForegroundColor DarkGray
    Write-Host ("  · rejected       : " + $script:PIPELINE_STATE.vrn_reject_count) -ForegroundColor DarkGray
    Write-Host ("  · strong_reject  : " + $script:PIPELINE_STATE.vrn_strong_reject) -ForegroundColor DarkGray
    Write-Host ("  · ssot_loaded    : " + $script:PIPELINE_STATE.vrn_ssot_loaded) -ForegroundColor DarkGray
    Write-Host ("  · html           : " + $script:PIPELINE_STATE.vrn_html) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host ("  Summary HTML     : " + $reports.Html) -ForegroundColor Green
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# =============================================================================
# def RUN
# =============================================================================
try {
    Invoke-Main
} catch {
    $script:PIPELINE_STATE.overall          = "FAIL"
    $script:PIPELINE_STATE.fatal_message    = $_.Exception.Message
    $script:PIPELINE_STATE.pipeline_ended_at = (Get-Date).ToString("s")
    Write-Host ""
    Write-Host ("[FATAL] " + $_.Exception.Message) -ForegroundColor Red
    if ($_.ScriptStackTrace) {
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    }
    try {
        if (-not (Test-Path -LiteralPath $script:PIPELINE_ROOT)) {
            New-Item -ItemType Directory -Path $script:PIPELINE_ROOT -Force | Out-Null
        }
        $reports = Write-SummaryHtml
        Write-Host ("[INFO] Partial summary written: " + $reports.Html) -ForegroundColor Yellow
        if (-not $NoOpenHtml -and (Test-FileExists $reports.Html)) {
            try { Start-Process $reports.Html } catch {}
        }
    } catch {}
    Write-Host "PowerShell session remains open." -ForegroundColor Yellow
}

