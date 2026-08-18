#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-All v0103 — ONE POWERSHELL TO HANDLE ALL(WorkOps 總指揮·v0102 版本前送)
------------------------------------------------------------------------------------------
 v0103(操作員 ONE POWERSHELL 再令 2026/08/08):
   [2b] WOP 歸戶段升級:out\wop_confirm.csv 在位先自動吸收(apply;吸收後改名歸檔)
        再融合歸戶(propose)— 佇列點選→下載→重跑 all 即完成閉環,免記分段動詞;
        段序整理:2 深鏈 → 2b WOP → 2c 決策(執行序=編號序)
------------------------------------------------------------------------------------------
 v0102(操作員 M365 規劃書令 2026/08/08:補強註冊/整合所有工具/建立 U/I):
   [2c] WOP 專案歸戶(ENG-028:M1 多訊號融合→AUTO/ASK/QUARANTINE→M2 賦號;
        分歧件產 out\WopConfirmQueue.html mouse-only 確認佇列;學習記憶手動遞減)
   產物清單增列 WopConfirmQueue.html / wop_registry.json
------------------------------------------------------------------------------------------
 v0101(操作員再令 2026/08/08:one powershell…and the following processes):
   [0d] OCR 十段探測快照(ENG-026,落 out\ocr_probe.json)
   [2b] 決策 KPI 快照(ENG-027:decisions report + export;帳本空則誠實略過)
   產物清單增列 naming_review.csv / decision_log.csv / ocr_probe.json
 操作員原令(2026/08/08):one powershell to handle all above and the following processes.
 一支到底(每段誠實 OK/FAIL,失敗不中斷其餘;不卡斷;全程動態解析最新版):
   [0] 環境自癒:venv 缺→pmsetup(EnvManager 中央治理);dot 缺→dotsetup install
       (官方可攜版+sha256;user-scope);envmgr 健檢落 out\envmanager\
   [1] 指揮板一支到底:掃描→對帳→PLM 編號→追蹤佇列→六頁板+週報+通知+KPI(靜默建板)
   [2] 深度鏈:時段唯讀逐封(含內文)→語料橋→超級引擎→NLP/DM/PM 分析(含 DFG 圖)
   [3] 總結與開啟:指揮板 + analytics 報告(-NoOpen 全不開);逐段結果與產物清單
 治理:Outlook 唯讀、原件/分類零觸碰、絕不代寄、基底零觸碰 — 全由被呼叫引擎守持。
 回退:刪本檔,各分段動詞(pmsetup/dotsetup/envmgr/板/deep)照常單獨可跑。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [int]$BodyChars = 1200,
    [switch]$NoOpen,
    [switch]$SkipDeep
)
$ErrorActionPreference = "Continue"
$WorkOps = $PSScriptRoot
$Engines = Join-Path $WorkOps "engines"
$Stages  = [System.Collections.Generic.List[object]]::new()

function Get-NewestScript { param([string]$Dir, [string]$Pattern)
    Get-ChildItem -Path $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
}
function Invoke-Stage { param([string]$Name, [scriptblock]$Body)
    Write-Host ""
    Write-Host ("──── {0} ────" -f $Name) -ForegroundColor Cyan
    $t = [Diagnostics.Stopwatch]::StartNew()
    $global:LASTEXITCODE = 0
    try {
        & $Body
        $ok = ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
    } catch {
        Write-Host ("  [FAIL] {0}" -f $_.Exception.Message) -ForegroundColor Red
        $ok = $false
    }
    $t.Stop()
    $Stages.Add([pscustomobject]@{ 段 = $Name; 結果 = $(if ($ok) { "OK" } else { "FAIL" }); 秒 = [math]::Round($t.Elapsed.TotalSeconds, 1) })
    $global:LASTEXITCODE = 0
}

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host ("  VIA WorkOps ALL v0103  |  環境自癒→板→深鏈→WOP歸戶(自動吸收確認)→決策KPI · {0} 天窗" -f $Days) -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---------- [0] 環境自癒 ----------
Invoke-Stage "0a 隔離 venv(EnvManager 中央治理)" {
    if (Test-Path -LiteralPath (Join-Path $Engines ".venv_pm\Scripts\python.exe")) {
        Write-Host "  venv 已在位 — 免安裝(via-workops pmsetup -Recreate 可重建)" -ForegroundColor Green
    } else {
        $pms = Get-NewestScript $Engines "Invoke-VIA-WorkOps-PmSetup-v0*.ps1"
        if ($pms) { & $pms.FullName } else { Write-Host "  [FAIL] PmSetup 不在位" -ForegroundColor Red; throw "PmSetup missing" }
    }
}
Invoke-Stage "0b graphviz 可攜版(DFG 圖)" {
    $dotP = Get-ChildItem -Path (Join-Path $Engines ".graphviz") -Filter "dot.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($dotP -or (Get-Command dot -ErrorAction SilentlyContinue)) {
        Write-Host "  dot 已就位 — 免下載" -ForegroundColor Green
    } else {
        & py (Join-Path $Engines "VIA_ENG070_WorkopsGraphvizSetup.py") install
    }
}
Invoke-Stage "0c EnvManager 健檢(落 out\envmanager\)" {
    & py (Join-Path $Engines "VIA_ENG069_WorkopsEnvmanagerBridge.py") health
}
Invoke-Stage "0d OCR 十段探測快照(ENG-026)" {
    $router = Join-Path (Split-Path (Split-Path $WorkOps -Parent) -Parent) "supportive modules\VIA_OCR_Router\SUP_MDL146_OcrRouter.py"
    $probeOut = Join-Path $WorkOps "out\ocr_probe.json"
    & py $router probe | Tee-Object -Variable probeLines | Select-Object -Last 1 | Write-Host
    ($probeLines | Select-Object -SkipLast 1) -join "`n" | Set-Content -LiteralPath $probeOut -Encoding UTF8
}

# ---------- [1] 指揮板 ----------
Invoke-Stage "1 指揮板一支到底(掃描→對帳→編號→六頁板+週報+KPI)" {
    $board = Get-NewestScript $WorkOps "Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"
    if (-not $board) { throw "CommandBoard 不在位" }
    & $board.FullName -Silent
}

# ---------- [2] 深度鏈 ----------
if ($SkipDeep) {
    Write-Host "`n──── 2 深度鏈:-SkipDeep 指定略過 ────" -ForegroundColor DarkYellow
    $Stages.Add([pscustomobject]@{ 段 = "2 深度鏈"; 結果 = "SKIP"; 秒 = 0 })
} else {
    Invoke-Stage "2 深度鏈(唯讀掃描→語料橋→引擎→分析+DFG)" {
        $deep = Get-NewestScript $Engines "Invoke-VIA-WorkOps-Deep-v0*.ps1"
        if (-not $deep) { throw "Deep 不在位" }
        & $deep.FullName -Days $Days -BodyChars $BodyChars -NoOpen
    }
}

# ---------- [2b] WOP 專案歸戶(ENG-028)----------
Invoke-Stage "2b WOP 專案歸戶(確認檔自動吸收→融合→賦號)" {
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\wop_confirm.csv")) {
        & py (Join-Path $Engines "VIA_ENG087_WorkopsWopIdentifier.py") apply
    }
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\mails.csv")) {
        & py (Join-Path $Engines "VIA_ENG087_WorkopsWopIdentifier.py") propose
    } else {
        Write-Host "  掃描語料尚缺(out\mails.csv)— 板段成功後下次跑即歸戶" -ForegroundColor DarkYellow
    }
}

# ---------- [2c] 決策 KPI ----------
Invoke-Stage "2c 決策 KPI 快照(ENG-027)" {
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\decision_log.db")) {
        & py (Join-Path $Engines "VIA_ENG068_WorkopsDecisionLog.py") report
        & py (Join-Path $Engines "VIA_ENG068_WorkopsDecisionLog.py") export
    } else {
        Write-Host "  決策帳本尚空 — via-workops decisions add 開始記錄(會議範本:docs\Meeting_Minutes_Template.md)" -ForegroundColor DarkYellow
    }
}

# ---------- [3] 總結與開啟 ----------
Write-Host ""
Write-Host "──── 3 總結 ────" -ForegroundColor Cyan
$Stages | Format-Table -AutoSize | Out-String | Write-Host
$ViaRoot   = Split-Path (Split-Path $WorkOps -Parent) -Parent   # 與指揮板同式:WorkOps→functional modules→VIA 根
$boardHtml = Join-Path $ViaRoot "VIA_Reports\workops_run\VIA_WorkOps_CommandBoard.html"
$aReport   = Join-Path $WorkOps "out\deep\engine_out\analytics_report.html"
$eReport   = Join-Path $WorkOps "out\deep\engine_out\engine_report.html"
Write-Host "[產物]" -ForegroundColor Yellow
$naming  = Join-Path $WorkOps "out\naming_review.csv"
$decCsv  = Join-Path $WorkOps "out\decision_log.csv"
$ocrJson = Join-Path $WorkOps "out\ocr_probe.json"
$wopQ    = Join-Path $WorkOps "out\WopConfirmQueue.html"
$wopReg  = Join-Path $WorkOps "out\wop_registry.json"
foreach ($p in @($boardHtml, $eReport, $aReport, $naming, $decCsv, $ocrJson, $wopQ, $wopReg)) {
    if (Test-Path -LiteralPath $p) { Write-Host ("  在位  {0}" -f $p) -ForegroundColor Green }
    else { Write-Host ("  缺席  {0}" -f $p) -ForegroundColor DarkYellow }
}
if (-not $NoOpen) {
    if (Test-Path -LiteralPath $boardHtml) { Start-Process $boardHtml | Out-Null }
    if (Test-Path -LiteralPath $aReport)   { Start-Process $aReport   | Out-Null }
}
$bad = @($Stages | Where-Object { $_.結果 -eq "FAIL" })
if ($bad.Count) { Write-Host ("[誠實清單] 未成段:{0}" -f (($bad | ForEach-Object { $_.段 }) -join "、")) -ForegroundColor Yellow }
Write-Host "[總結] WorkOps ALL 完成(Outlook 唯讀 · 原件零觸碰 · 絕不代寄 · 基底零觸碰)" -ForegroundColor Green
