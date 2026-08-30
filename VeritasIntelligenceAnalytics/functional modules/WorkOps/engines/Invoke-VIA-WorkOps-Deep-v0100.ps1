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
<#
==========================================================================================
 Invoke-VIA-WorkOps-Deep v0100 — 深度郵件智能一支到底
------------------------------------------------------------------------------------------
 鏈:scanrange(時段唯讀逐封匯出,含內文片段)→ 語料橋 → 超級引擎(修復/五維分類/
     E01-E07 庫/PMBOK 匯出)→ 分析層(NLP/DM/PM)→ 開啟報告
 背景:操作員實跑發現 engine --input out 讀 0 封(schema 不合)— 本鏈以語料橋補齊。
 治理:Outlook 唯讀;輸出落 WorkOps\out\deep\(可重生);不卡斷;各引擎動態解析最新版。
 回退:刪本檔,五個分段動詞(scanrange/bridge/engine/analytics)仍可手動逐步跑。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [int]$BodyChars = 1200,
    [switch]$NoOpen
)
$ErrorActionPreference = "Continue"
$Here   = $PSScriptRoot                       # engines/
$WorkOps = Split-Path $Here -Parent
$Deep   = Join-Path $WorkOps "out\deep"
New-Item -ItemType Directory -Force -Path $Deep | Out-Null

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host ("  VIA WorkOps DEEP v0100  |  掃描→語料橋→超級引擎→分析 · {0} 天窗" -f $Days) -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

Write-Host "[1/4] 時段唯讀逐封匯出(含內文片段)..." -ForegroundColor Yellow
$scan = Join-Path $Here "Invoke-VIA-Outlook-TimeRange-ReadOnly.ps1"
& $scan -StartTime (Get-Date).Date.AddDays(-1 * [math]::Abs($Days)) -EndTime (Get-Date) `
        -OutputRoot (Join-Path $Deep "scanrange") -IncludeBodySnippet $true -BodySnippetLength $BodyChars

Write-Host "[2/4] 語料橋(schema 統一)..." -ForegroundColor Yellow
& py (Join-Path $Here "VIA_ENG066_WorkopsCorpusBridge.py") --inputs (Join-Path $Deep "scanrange") (Join-Path $WorkOps "out") --outdir (Join-Path $Deep "corpus")

Write-Host "[3/4] 郵件智能超級引擎..." -ForegroundColor Yellow
& py (Join-Path $Here "VIA_ENG056_EmailSuperEngine.py") --input (Join-Path $Deep "corpus") --outdir (Join-Path $Deep "engine_out")

Write-Host "[4/4] NLP/DM/PM 分析層..." -ForegroundColor Yellow
$VPy = Join-Path $Here ".venv_pm\Scripts\python.exe"
$PyCmd = if (Test-Path -LiteralPath $VPy) { $VPy } else { "py" }
Push-Location $Deep
try { & $PyCmd (Join-Path $Here "VIA_ENG057_EngineAnalytics.py") --outdir (Join-Path $Deep "engine_out") } finally { Pop-Location }

$report = Join-Path $Deep "engine_out\engine_report.html"
$aReport = Join-Path $Deep "engine_out\analytics_report.html"
if (-not $NoOpen) {
    if (Test-Path -LiteralPath $report)  { Start-Process $report  | Out-Null }
    if (Test-Path -LiteralPath $aReport) { Start-Process $aReport | Out-Null }
}
Write-Host ("[總結] 深度鏈完成 · 產物:{0}(Outlook 唯讀,原件零觸碰)" -f $Deep) -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
