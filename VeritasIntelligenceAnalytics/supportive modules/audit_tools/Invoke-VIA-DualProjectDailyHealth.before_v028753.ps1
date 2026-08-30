#requires -Version 7.0
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

param(
    [switch]$OpenHtmlReport
)

$ProjectRoot = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
$ActiveRoot = Join-Path $ProjectRoot 'dict\VDF\_active'
$FreezeRoot = Join-Path $ProjectRoot 'dict\VDF\_freeze'
$ToolRoot = Join-Path $ProjectRoot 'tools\VIA_DualProjectDailyHealth'
$DailyRoot = Join-Path $ToolRoot 'daily_runs'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$RunRoot = Join-Path $DailyRoot "RUN_$Stamp"
$ReportDir = Join-Path $RunRoot 'report'
$RuntimeDir = Join-Path $RunRoot 'runtime'

foreach($d in @($DailyRoot,$RunRoot,$ReportDir,$RuntimeDir)){
    [System.IO.Directory]::CreateDirectory($d) | Out-Null
}

function ReadJson($Path){
    try {
        if(Test-Path -LiteralPath $Path){
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {}
    return $null
}

function Prop($Obj,$Name,$Default=''){
    if($null -eq $Obj){ return $Default }
    try {
        $p = $Obj.PSObject.Properties[$Name]
        if($null -ne $p -and $null -ne $p.Value){ return $p.Value }
    } catch {}
    return $Default
}

function H($v){
    if($null -eq $v){ return '' }
    return [System.Net.WebUtility]::HtmlEncode([string]$v)
}

function FindLatest($Filter){
    Get-ChildItem -LiteralPath $ActiveRoot -Recurse -File -Filter $Filter -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

$ActivePointer = Join-Path $ActiveRoot 'VDF_ACTIVE_POINTER.json'
$FrozenPointer = Join-Path $FreezeRoot 'VDF_FINAL_ACTIVATION_SEAL_POINTER_v02868.json'

$Active = ReadJson $ActivePointer
$Frozen = ReadJson $FrozenPointer
$SmokeFile = FindLatest 'VIA_ReadOnlyLaneSmoke_Runtime_v02874.json'
$ConsoleFile = FindLatest 'VIA_DualProjectUserTestConsoleHotfix_Runtime_v028731.json'

$Smoke = if($SmokeFile){ ReadJson $SmokeFile.FullName } else { $null }

$ActiveStatus = [string](Prop $Active 'status' '')
$FrozenStatus = [string](Prop $Frozen 'status' '')
$SmokeStatus = [string](Prop $Smoke 'status' '')
$SmokeOk = [int](Prop $Smoke 'smoke_ok' 0)
$SmokeBlock = [int](Prop $Smoke 'smoke_block' 0)

$Issues = @()
if($ActiveStatus -ne 'FINAL_PROMOTED_ACTIVE_POINTER_LOCKED'){ $Issues += "Active pointer review: $ActiveStatus" }
if($FrozenStatus -ne 'FINAL_PROMOTED_ACTIVE_POINTER_LOCKED'){ $Issues += "Frozen pointer review: $FrozenStatus" }
if($SmokeStatus -ne 'READONLY_LANE_SMOKE_READY'){ $Issues += "Smoke review: $SmokeStatus" }
if($SmokeOk -lt 6){ $Issues += "Smoke OK less than 6: $SmokeOk" }
if($SmokeBlock -gt 0){ $Issues += "Smoke block greater than 0: $SmokeBlock" }

$Status = if($Issues.Count -eq 0){ 'DAILY_HEALTH_READY' } else { 'DAILY_HEALTH_REVIEW_REQUIRED' }
$Risk = if($Issues.Count -eq 0){ 'LOW' } else { 'MEDIUM' }

$RuntimePath = Join-Path $RuntimeDir 'VIA_DualProjectDailyHealth_Runtime.json'
$HtmlPath = Join-Path $ReportDir 'VIA_DualProjectDailyHealth_Report.html'

$Runtime = [pscustomobject]@{
    generated_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffK')
    status = $Status
    risk = $Risk
    active_status = $ActiveStatus
    frozen_status = $FrozenStatus
    smoke_status = $SmokeStatus
    smoke_ok = $SmokeOk
    smoke_block = $SmokeBlock
    latest_smoke_runtime = if($SmokeFile){$SmokeFile.FullName}else{''}
    latest_console_runtime = if($ConsoleFile){$ConsoleFile.FullName}else{''}
    issues = $Issues
    policy = [pscustomobject]@{
        db_write = $false
        source_repair = $false
        pointer_rewrite = $false
        destructive_delete = $false
        stop_process = $false
        vrn_extraction = $false
        vdf_db_write = $false
    }
}

$Runtime | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $RuntimePath -Encoding UTF8

if($Issues.Count -eq 0){
    $issueRows = '<tr><td>OK</td><td>No current issue.</td></tr>'
} else {
    $issueRows = ($Issues | ForEach-Object { '<tr><td>REVIEW</td><td>' + (H $_) + '</td></tr>' }) -join "`n"
}

$latestSmokeText = H $Runtime.latest_smoke_runtime
$latestConsoleText = H $Runtime.latest_console_runtime

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Dual Project Daily Health</title>
<style>
body{font-family:'Microsoft JhengHei','Segoe UI',Arial,sans-serif;background:#f8fbfa;color:#1d3438;margin:0;font-size:12px}
header{padding:16px 24px;border-bottom:1px solid rgba(38,70,75,.18);background:white;position:sticky;top:0}
h1{margin:0;text-align:center;font-size:18px}
.wrap{padding:16px 24px}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:14px}
.card{background:white;border:1px solid rgba(38,70,75,.16);border-radius:10px;padding:10px}
.k{font-size:10px;color:#657f82}.v{font-size:16px;font-weight:700}
table{width:100%;border-collapse:collapse;background:white;border:1px solid rgba(38,70,75,.16)}
th,td{border-bottom:1px solid rgba(38,70,75,.12);padding:7px;text-align:left;vertical-align:top}
th{background:#edf8f6}
code{font-family:Consolas,monospace;word-break:break-word}
</style>
</head>
<body>
<header><h1>def VIA Dual Project Daily Health</h1></header>
<div class="wrap">
<div class="grid">
<div class="card"><div class="k">Status</div><div class="v">$Status</div></div>
<div class="card"><div class="k">Risk</div><div class="v">$Risk</div></div>
<div class="card"><div class="k">Active</div><div class="v">$ActiveStatus</div></div>
<div class="card"><div class="k">Frozen</div><div class="v">$FrozenStatus</div></div>
<div class="card"><div class="k">Smoke</div><div class="v">$SmokeStatus</div></div>
<div class="card"><div class="k">Smoke OK</div><div class="v">$SmokeOk</div></div>
</div>
<h2>Issues</h2>
<table><thead><tr><th>Status</th><th>Message</th></tr></thead><tbody>$issueRows</tbody></table>
<h2>Paths</h2>
<table>
<tr><th>Runtime</th><td><code>$RuntimePath</code></td></tr>
<tr><th>Latest Smoke</th><td><code>$latestSmokeText</code></td></tr>
<tr><th>Latest Console</th><td><code>$latestConsoleText</code></td></tr>
</table>
</div>
</body>
</html>
"@

[System.IO.File]::WriteAllText($HtmlPath,$html,[System.Text.UTF8Encoding]::new($false))

Write-Host ''
Write-Host '================================================================================' -ForegroundColor Cyan
Write-Host 'VIA DUAL PROJECT DAILY HEALTH' -ForegroundColor Cyan
Write-Host '================================================================================' -ForegroundColor Cyan
Write-Host "Status : $Status"
Write-Host "Risk   : $Risk"
Write-Host "HTML   : $HtmlPath"
Write-Host "Runtime: $RuntimePath"

if($OpenHtmlReport -and (Test-Path -LiteralPath $HtmlPath)){
    Start-Process $HtmlPath
}

Write-Host 'Read-only daily health complete. No DB write. No Stop-Process.' -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
