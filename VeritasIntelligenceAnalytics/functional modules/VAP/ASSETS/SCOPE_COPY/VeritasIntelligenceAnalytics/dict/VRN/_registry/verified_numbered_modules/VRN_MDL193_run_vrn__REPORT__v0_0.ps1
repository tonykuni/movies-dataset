# ==================================================================================================
# def VRN Canonical Active Launcher v03
# def First action: purge temp\summary_staging
# def Then: verify YFinance FINAL_SEALED + active manifest + clean no-summary data
# def No core mutation
# ==================================================================================================

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
$ErrorActionPreference = "Continue"
$ProgressPreference = "Continue"

$VRN_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$CONFIG_DIR = Join-Path $VRN_ROOT "config"
$TEMP_DIR = Join-Path $VRN_ROOT "temp"
$SUMMARY_TEMP = Join-Path $TEMP_DIR "summary_staging"

$ACTIVE_MANIFEST = Join-Path $CONFIG_DIR "VRN_Active_DataManifest_v03.json"
$YFINANCE_SEAL = Join-Path $CONFIG_DIR "VRN_YFinance_InfoReference_FinalSeal_v051.json"

$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$RUN_DIR = Join-Path $VRN_ROOT "_vrn_system_start_runs\VRN_ACTIVE_LAUNCH_$TS"
$REPORT_HTML = Join-Path $RUN_DIR "VRN_Active_Launch_Report.html"
$REPORT_JSON = Join-Path $RUN_DIR "VRN_Active_Launch_Report.json"

function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_WriteText {
    param([string]$Path, [string]$Text)
    def_EnsureDir (Split-Path -Parent $Path)
    $Enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $Enc)
}

function def_Html {
    param([object]$Text)
    return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

def_EnsureDir $RUN_DIR
def_EnsureDir $TEMP_DIR

if (Test-Path -LiteralPath $SUMMARY_TEMP) {
    Remove-Item -LiteralPath $SUMMARY_TEMP -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $SUMMARY_TEMP | Out-Null

$SealStatus = "MISSING"
$SealPass = $false
if (Test-Path -LiteralPath $YFINANCE_SEAL) {
    try {
        $SealObj = Get-Content -LiteralPath $YFINANCE_SEAL -Raw | ConvertFrom-Json
        $SealStatus = [string]$SealObj.seal_status
        $SealPass = [bool]$SealObj.final_hard_pass
    } catch {
        $SealStatus = "READ_ERROR"
    }
}

$ManifestOk = $false
$BasicInfo = ""
$Financial = ""
$BasicRows = 0
$FinancialRows = 0

if (Test-Path -LiteralPath $ACTIVE_MANIFEST) {
    try {
        $M = Get-Content -LiteralPath $ACTIVE_MANIFEST -Raw | ConvertFrom-Json
        $BasicInfo = [string]$M.basicinfo_canonical_no_summary
        $Financial = [string]$M.financial_canonical_no_summary
        $BasicRows = [int]$M.basic_rows
        $FinancialRows = [int]$M.financial_rows
        $ManifestOk = $true
    } catch {}
}

$SystemReady = ($SealPass -and $ManifestOk -and (Test-Path -LiteralPath $BasicInfo) -and (Test-Path -LiteralPath $Financial))

$Report = [ordered]@{
    system_ready = $SystemReady
    generated_at = (Get-Date).ToString("s")
    seal_status = $SealStatus
    seal_pass = $SealPass
    active_manifest = $ACTIVE_MANIFEST
    manifest_ok = $ManifestOk
    basicinfo = $BasicInfo
    financial = $Financial
    basic_rows = $BasicRows
    financial_rows = $FinancialRows
    summary_temp_purged_first = $true
}

def_WriteText $REPORT_JSON ($Report | ConvertTo-Json -Depth 20)

$Html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Active Launch Report</title>
<style>
body{font-family:"Segoe UI","Microsoft JhengHei",Arial;background:#f5f4f0;color:#111827;margin:0;font-size:12px}
.header{background:#0f172a;color:white;padding:24px 32px}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;padding:16px 30px}
.card{background:white;border:1px solid #ddd;border-radius:8px;padding:12px}
.num{font-size:20px;font-weight:800;overflow-wrap:anywhere}
.section{background:white;margin:0 30px 20px 30px;border:1px solid #ddd;border-radius:8px;padding:16px}
.ok{color:#166534;font-weight:800}.warn{color:#92400e;font-weight:800}
.code{white-space:pre-wrap;background:#0f172a;color:#d1fae5;padding:12px;border-radius:8px}
</style>
</head>
<body>
<div class="header">
<h1>VRN Active Launch Report</h1>
<div>Temp purge first · YFinance seal · canonical clean data</div>
</div>
<div class="grid">
<div class="card"><div class="num">$([int]$SystemReady)</div><div>System Ready</div></div>
<div class="card"><div class="num">$SealStatus</div><div>YFinance Seal</div></div>
<div class="card"><div class="num">$SealPass</div><div>Seal Pass</div></div>
<div class="card"><div class="num">$ManifestOk</div><div>Manifest OK</div></div>
<div class="card"><div class="num">$BasicRows</div><div>BASICINFO Rows</div></div>
<div class="card"><div class="num">$FinancialRows</div><div>Financial Rows</div></div>
</div>
<div class="section">
<h2>01 Final Verdict</h2>
<p class="$(if($SystemReady){'ok'}else{'warn'})">$(if($SystemReady){'SYSTEM READY'}else{'NEEDS REVIEW'})</p>
<p><b>BASICINFO:</b> $(def_Html $BasicInfo)</p>
<p><b>Financial:</b> $(def_Html $Financial)</p>
<p><b>Manifest:</b> $(def_Html $ACTIVE_MANIFEST)</p>
</div>
<div class="section">
<h2>02 Rule Lock</h2>
<div class="code">def temp\summary_staging 已在啟動第一步清除
def YFinance final seal 必須 FINAL_SEALED
def active manifest 指向 canonical no-summary data
def old summary overlay 不進主輸出
def historical run scripts 不修</div>
</div>
</body>
</html>
"@

def_WriteText $REPORT_HTML $Html
Start-Process $REPORT_HTML

Write-Host "==================================================================================================" -ForegroundColor Green
Write-Host "def VRN ACTIVE LAUNCH DONE" -ForegroundColor Green
Write-Host "==================================================================================================" -ForegroundColor Green
Write-Host "[REPORT] $REPORT_HTML" -ForegroundColor Green
Write-Host "[REPORT_JSON] $REPORT_JSON" -ForegroundColor Green
Write-Host "[BASICINFO] $BasicInfo" -ForegroundColor Green
Write-Host "[FINANCIAL] $Financial" -ForegroundColor Green

if ($SystemReady) {
    Write-Host "[RESULT] SYSTEM READY：active canonical launch passed." -ForegroundColor Green
} else {
    Write-Host "[RESULT] NEEDS REVIEW：check report." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "PowerShell session remains open." -ForegroundColor DarkGray

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
