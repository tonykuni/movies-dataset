#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-Deep v0101 — 深度郵件智能一支到底(時間起迄可設定+命名核對)
------------------------------------------------------------------------------------------
 v0101(操作員裁決 2026/08/08):
   1) 讀取時間「起迄可設定」:-StartDate/-EndDate(如 2026-07-01)優先於 -Days 天窗
   2) 鏈尾自動跑命名提議(workops_namer propose)— 編號不變,系統提議人話名稱
      供使用者核對(out\naming_review.csv;核對後報表顯示「編號·名稱」)
 鏈:scanrange(唯讀逐封,含內文)→ 語料橋 → 超級引擎 → 分析層(NLP/DM/PM+DFG)
     → 命名提議。治理:Outlook 唯讀;輸出落 out\deep\;不卡斷;動態解析最新版。
 回退:刪本檔即回 v0100(固定 -Days 天窗,無命名步)。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [string]$StartDate = "",
    [string]$EndDate = "",
    [int]$BodyChars = 1200,
    [switch]$NoOpen
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
$ErrorActionPreference = "Continue"
$Here   = $PSScriptRoot                       # engines/
$WorkOps = Split-Path $Here -Parent
$Deep   = Join-Path $WorkOps "out\deep"
New-Item -ItemType Directory -Force -Path $Deep | Out-Null

$St = if ($StartDate) { Get-Date $StartDate } else { (Get-Date).Date.AddDays(-1 * [math]::Abs($Days)) }
$En = if ($EndDate)   { Get-Date $EndDate }   else { Get-Date }

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host ("  VIA WorkOps DEEP v0101  |  {0:yyyy-MM-dd} → {1:yyyy-MM-dd HH:mm} · 掃描→橋→引擎→分析→命名" -f $St, $En) -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

Write-Host "[1/5] 時段唯讀逐封匯出(含內文片段)..." -ForegroundColor Yellow
$scan = Join-Path $Here "Invoke-VIA-Outlook-TimeRange-ReadOnly.ps1"
& $scan -StartTime $St -EndTime $En `
        -OutputRoot (Join-Path $Deep "scanrange") -IncludeBodySnippet $true -BodySnippetLength $BodyChars

Write-Host "[2/5] 語料橋(schema 統一)..." -ForegroundColor Yellow
& py (Join-Path $Here "VIA_ENG066_WorkopsCorpusBridge.py") --inputs (Join-Path $Deep "scanrange") (Join-Path $WorkOps "out") --outdir (Join-Path $Deep "corpus")

Write-Host "[3/5] 郵件智能超級引擎..." -ForegroundColor Yellow
& py (Join-Path $Here "VIA_ENG056_EmailSuperEngine.py") --input (Join-Path $Deep "corpus") --outdir (Join-Path $Deep "engine_out")

Write-Host "[4/5] NLP/DM/PM 分析層..." -ForegroundColor Yellow
$VPy = Join-Path $Here ".venv_pm\Scripts\python.exe"
$PyCmd = if (Test-Path -LiteralPath $VPy) { $VPy } else { "py" }
Push-Location $Deep
try { & $PyCmd (Join-Path $Here "VIA_ENG057_EngineAnalytics.py") --outdir (Join-Path $Deep "engine_out") } finally { Pop-Location }

Write-Host "[5/5] 命名提議(編號不變;核對表 out\naming_review.csv)..." -ForegroundColor Yellow
& py (Join-Path $Here "VIA_ENG076_WorkopsNamer.py") propose

$report = Join-Path $Deep "engine_out\engine_report.html"
$aReport = Join-Path $Deep "engine_out\analytics_report.html"
if (-not $NoOpen) {
    if (Test-Path -LiteralPath $report)  { Start-Process $report  | Out-Null }
    if (Test-Path -LiteralPath $aReport) { Start-Process $aReport | Out-Null }
}
Write-Host ("[總結] 深度鏈完成 · 產物:{0}(Outlook 唯讀,原件零觸碰)· 名稱核對:via-workops names" -f $Deep) -ForegroundColor Green

