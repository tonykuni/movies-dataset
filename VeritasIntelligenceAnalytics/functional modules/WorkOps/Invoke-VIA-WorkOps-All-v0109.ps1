#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-All v0109 — ONE POWERSHELL TO HANDLE ALL(WorkOps 總指揮·v0108 版本前送)
------------------------------------------------------------------------------------------
 v0109(操作員 ONE POWERSHELL TO HANDLE ALL ABOVE 令 2026/08/11):
   [0s] Git 同步段(最先跑):git pull --ff-only origin main — 安全快轉,分岔/離線
        誠實示警不中斷;偵測 ALL 自身有新版入庫時提示「本輪以現版跑完,下輪自動採新版」
        (動態解析鐵律使然)。從此 via-sync 免先打,一句 via-workops all 含同步到底。
------------------------------------------------------------------------------------------
 v0108(操作員「一個 powershell code to handle all」令 2026/08/11):
   [0f] 人工回件收割:自動從 Downloads / repo 根撿最新 wop_confirm*.csv、gold_set*.csv、
        lexicon_review*.csv、control_sheet*.csv 歸位(既有檔先 .bak;sha 帳 harvest_ledger
        防重複吸收;Downloads 原檔零觸碰)— 佇列頁下載後直接重跑 all 即閉環,免手搬
   [2e3] ML 迴圈(選配;無 sklearn 誠實略過):lexicon_review 在位→ml adopt(冪等)
        →ml train→ml suggest;絕不自動跑 cluster(避免覆蓋操作員填寫中之核對表)
   -HarvestOnly 開關:只跑收割段即離開(= via-workops harvest)
------------------------------------------------------------------------------------------
 v0107(操作員總覽升級令 2026/08/11:步驟性/順序性/自動化一頁呈現):
   [3] 逐段結果落 out\all_run_summary.json(段名/OK-FAIL/秒)— 板 v0128 總覽頁
       「自動化流程帶」自動吸收,每輪步驟成果一頁可視
------------------------------------------------------------------------------------------
 v0106(操作員 APPLY ALL 令 2026/08/11:外部套件 ENG-051..054 升籍接線):
   [2e2] 治理鏈:承諾候選(ENG-051 candidates,絕不自動納管)→ 統一登記簿(ENG-054)
        → 一致性守衛(ENG-052 唯讀矛盾報告)→ 健康分(ENG-053 可解釋扣分)
        守衛報 FAIL=誠實示警不改資料;板末刷同輪吸收四產物
------------------------------------------------------------------------------------------
 v0105(操作員 ONE POWERSHELL 三令 2026/08/10:handle all above & the following automatically):
   [0e] 全鏈自測(ENG-032 沙箱六段;-SkipSelftest 可略)— 先測後串,FinalGate 紅=誠實示警不中斷
   [2e] Gold Set 準確度:每輪自動刷新核對樣板;out\gold_set.csv 在位即自動實測計分
        (核對→另存→重跑 all 即閉環,免記分段動詞 — 同 wop_confirm 模式)
   [2f] 側車備份+驗證(ENG-031:20 項正本 zip+sha256;每輪自動,篡改即示警)
   [2g] 板末刷:本輪歸戶/解析/準確度全吸收後靜默重生指揮板(00-09 十面資料同輪)
------------------------------------------------------------------------------------------
 v0104(操作員 NEXT 令:M3 回覆解析入編):[2b] 回覆解析(ENG-029 三層 fallback
   投票/token/關鍵詞→事實流+狀態;未解析誠實列出)→ [2c] WOP 歸戶 → [2d] 決策 KPI
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
    [switch]$SkipDeep,
    [switch]$SkipSelftest,
    [switch]$HarvestOnly
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
Write-Host ("  VIA WorkOps ALL v0109  |  同步→回件收割→自測→自癒→板→深鏈→解析→歸戶→決策→準確度→治理鏈→ML→備份→板末刷 · {0} 天窗" -f $Days) -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---------- [0s] Git 同步(v0109:pull --ff-only;離線/分岔誠實示警不中斷)----------
Invoke-Stage "0s Git 同步(pull --ff-only origin main)" {
    $repoRoot = Split-Path (Split-Path (Split-Path $WorkOps -Parent) -Parent) -Parent
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
        Write-Host "  非 git 檢出 — 略過同步" -ForegroundColor DarkYellow
        return
    }
    $before = (Get-NewestScript $WorkOps "Invoke-VIA-WorkOps-All-v0*.ps1").Name
    git -C $repoRoot pull --ff-only origin main 2>&1 | Select-Object -Last 4 | ForEach-Object { Write-Host ("  " + $_) }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [WARN] 同步未成(離線或分岔)— 以現有版本續跑;稍後 via-sync 補" -ForegroundColor DarkYellow
        $global:LASTEXITCODE = 0
        return
    }
    $after = (Get-NewestScript $WorkOps "Invoke-VIA-WorkOps-All-v0*.ps1").Name
    if ($after -ne $before) {
        Write-Host ("  [注意] ALL 新版已入庫({0})— 本輪以 {1} 跑完,下輪自動採新版" -f $after, $before) -ForegroundColor Yellow
    }
}

# ---------- [0f] 人工回件收割(v0108:Downloads/repo 根 → 自動歸位)----------
Invoke-Stage "0f 回件收割(wop_confirm/gold_set/lexicon_review/control_sheet 自動歸位)" {
    $outDir = Join-Path $WorkOps "out"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $ledgerP = Join-Path $outDir "harvest_ledger.json"
    $ledger = @{}
    if (Test-Path -LiteralPath $ledgerP) {
        try { (Get-Content -LiteralPath $ledgerP -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties |
              ForEach-Object { $ledger[$_.Name] = $_.Value } } catch { }
    }
    $repoRoot = Split-Path (Split-Path (Split-Path $WorkOps -Parent) -Parent) -Parent
    $srcDirs = @((Join-Path $env:USERPROFILE "Downloads"), $repoRoot,
                 (Split-Path (Split-Path $WorkOps -Parent) -Parent)) | Where-Object { Test-Path -LiteralPath $_ }
    $targets = @(
        @{ Pattern = "wop_confirm*.csv";    Dest = (Join-Path $outDir "wop_confirm.csv");    Label = "WOP 確認檔(2c 段自動吸收)" },
        @{ Pattern = "gold_set*.csv";       Dest = (Join-Path $outDir "gold_set.csv");       Label = "Gold Set(2e 段自動實測)"; Exclude = "gold_set_template*" },
        @{ Pattern = "lexicon_review*.csv"; Dest = (Join-Path $outDir "lexicon_review.csv"); Label = "詞庫核對表(2e3 段 ml adopt)" },
        @{ Pattern = "control_sheet*.csv";  Dest = (Join-Path $WorkOps "control_sheet.csv"); Label = "控管表(板段對帳)" }
    )
    $nAbs = 0
    foreach ($tg in $targets) {
        $cands = foreach ($sd in $srcDirs) {
            Get-ChildItem -Path $sd -Filter $tg.Pattern -File -ErrorAction SilentlyContinue |
                Where-Object { -not $tg.Exclude -or $_.Name -notlike $tg.Exclude } |
                Where-Object { $_.FullName -ne $tg.Dest }
        }
        $newest = $cands | Sort-Object LastWriteTime | Select-Object -Last 1
        if (-not $newest) { continue }
        $sha = (Get-FileHash -LiteralPath $newest.FullName -Algorithm SHA256).Hash
        if ($ledger.ContainsKey($sha)) {
            Write-Host ("  [略] {0}:{1} 已吸收過(sha 帳)" -f $tg.Label, $newest.Name) -ForegroundColor DarkGray
            continue
        }
        if (Test-Path -LiteralPath $tg.Dest) {
            $bak = "$($tg.Dest).bak_$(Get-Date -Format yyyyMMdd_HHmmss)"
            Copy-Item -LiteralPath $tg.Dest -Destination $bak
        }
        Copy-Item -LiteralPath $newest.FullName -Destination $tg.Dest
        $ledger[$sha] = @{ file = $newest.Name; from = $newest.DirectoryName; ts = (Get-Date).ToString("s") }
        $nAbs++
        Write-Host ("  [收] {0} ← {1}({2};原檔零觸碰)" -f $tg.Label, $newest.Name, $newest.DirectoryName) -ForegroundColor Green
    }
    ($ledger | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $ledgerP -Encoding UTF8
    if ($nAbs -eq 0) { Write-Host "  無新回件 — Downloads/repo 根皆淨(佇列頁下載後重跑即自動歸位)" -ForegroundColor DarkGray }
}
if ($HarvestOnly) {
    Write-Host "`n[收割模式] 只跑回件歸位 — 接著跑 via-workops all 讓各段吸收" -ForegroundColor Cyan
    return
}

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

# ---------- [0e] 全鏈自測(先測後串)----------
if ($SkipSelftest) {
    Write-Host "`n──── 0e 全鏈自測:-SkipSelftest 指定略過 ────" -ForegroundColor DarkYellow
    $Stages.Add([pscustomobject]@{ 段 = "0e 全鏈自測"; 結果 = "SKIP"; 秒 = 0 })
} else {
    Invoke-Stage "0e 全鏈自測(ENG-032 沙箱六段;正本零觸碰)" {
        & py (Join-Path $Engines "VIA_ENG081_WorkopsSelftest.py")
    }
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

# ---------- [2b] 回覆解析(ENG-029 · M3)----------
Invoke-Stage "2b 回覆解析(投票/token/關鍵詞三層;未中誠實)" {
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\mails.csv")) {
        & py (Join-Path $Engines "workops_reply_parser.py") parse
    } else {
        Write-Host "  掃描語料尚缺 — 板段成功後下次跑即解析" -ForegroundColor DarkYellow
    }
}

# ---------- [2c] WOP 專案歸戶(ENG-028)----------
Invoke-Stage "2c WOP 專案歸戶(確認檔自動吸收→融合→賦號)" {
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\wop_confirm.csv")) {
        & py (Join-Path $Engines "VIA_ENG087_WorkopsWopIdentifier.py") apply
    }
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\mails.csv")) {
        & py (Join-Path $Engines "VIA_ENG087_WorkopsWopIdentifier.py") propose
    } else {
        Write-Host "  掃描語料尚缺(out\mails.csv)— 板段成功後下次跑即歸戶" -ForegroundColor DarkYellow
    }
}

# ---------- [2d] 決策 KPI ----------
Invoke-Stage "2d 決策 KPI 快照(ENG-027)" {
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\decision_log.db")) {
        & py (Join-Path $Engines "VIA_ENG068_WorkopsDecisionLog.py") report
        & py (Join-Path $Engines "VIA_ENG068_WorkopsDecisionLog.py") export
    } else {
        Write-Host "  決策帳本尚空 — via-workops decisions add 開始記錄(會議範本:docs\Meeting_Minutes_Template.md)" -ForegroundColor DarkYellow
    }
}

# ---------- [2e] Gold Set 準確度(ENG-030)----------
Invoke-Stage "2e Gold Set 準確度(樣板刷新;gold_set.csv 在位即實測)" {
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\wop_registry.json")) {
        & py (Join-Path $Engines "workops_accuracy_benchmark.py") template
        if (Test-Path -LiteralPath (Join-Path $WorkOps "out\gold_set.csv")) {
            & py (Join-Path $Engines "workops_accuracy_benchmark.py") run
        } else {
            Write-Host "  gold_set.csv 未在位 — Excel 核對 gold_set_template.csv 後另存,下輪自動計分(板 05 面三步引導)" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "  尚無歸戶 registry — 歸戶段成功後下輪自動出樣板" -ForegroundColor DarkYellow
    }
}

# ---------- [2e2] 治理鏈(ENG-051/054/052/053)----------
Invoke-Stage "2e2 治理鏈:承諾候選→統一登記簿→一致性守衛→健康分" {
    & py (Join-Path $Engines "workops_commitment_intelligence.py") candidates
    & py (Join-Path $Engines "workops_unified_work_register.py")
    & py (Join-Path $Engines "workops_consistency_guard.py")
    & py (Join-Path $Engines "workops_project_health.py")
}

# ---------- [2e3] ML 迴圈(v0108;選配 — 無 sklearn 誠實略過)----------
Invoke-Stage "2e3 ML 迴圈:adopt(冪等)→train→suggest(絕不自動 cluster)" {
    & py -c "import sklearn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  scikit-learn 未在位 — 誠實略過(via-workops ml setup 一鍵裝)" -ForegroundColor DarkYellow
        $global:LASTEXITCODE = 0
        return
    }
    if (Test-Path -LiteralPath (Join-Path $WorkOps "out\lexicon_review.csv")) {
        & py (Join-Path $Engines "VIA_ENG075_WorkopsMlLab.py") adopt
    }
    & py (Join-Path $Engines "VIA_ENG075_WorkopsMlLab.py") train
    & py (Join-Path $Engines "VIA_ENG075_WorkopsMlLab.py") suggest
}

# ---------- [2f] 側車備份+驗證(ENG-031)----------
Invoke-Stage "2f 側車備份+驗證(20 項正本 zip+sha256)" {
    & py (Join-Path $Engines "VIA_ENG061_WorkopsBackup.py") backup
    $bkDir = Join-Path $WorkOps "out\backups"
    $newest = Get-ChildItem -Path $bkDir -Filter "*.zip" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($newest) { & py (Join-Path $Engines "VIA_ENG061_WorkopsBackup.py") verify $newest.FullName }
    else { Write-Host "  [FAIL] 備份 zip 未產生" -ForegroundColor Red; $global:LASTEXITCODE = 1 }
}

# ---------- [2g] 板末刷(本輪全成果同板)----------
Invoke-Stage "2g 板末刷(歸戶/解析/準確度吸收後重生十面板)" {
    $board = Get-NewestScript $WorkOps "Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"
    if (-not $board) { throw "CommandBoard 不在位" }
    & $board.FullName -Silent
}

# ---------- [3] 總結與開啟 ----------
Write-Host ""
Write-Host "──── 3 總結 ────" -ForegroundColor Cyan
$Stages | Format-Table -AutoSize | Out-String | Write-Host
# v0107:逐段結果落側車 — 板總覽頁「自動化流程帶」自動吸收
try {
    $runSum = [ordered]@{ ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss"); version = "v0107"
                          stages = @($Stages | ForEach-Object { [ordered]@{ stage = $_.段; gate = $_.結果; sec = $_.秒 } }) }
    ($runSum | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath (Join-Path $WorkOps "out\all_run_summary.json") -Encoding UTF8
} catch { Write-Host ("  [WARN] all_run_summary 未落:{0}" -f $_.Exception.Message) -ForegroundColor DarkYellow }
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
$goldTpl = Join-Path $WorkOps "out\gold_set_template.csv"
$accRep  = Join-Path $WorkOps "out\accuracy_report.json"
$stRep   = Join-Path $WorkOps "out\selftest_report.json"
$uwrCsv  = Join-Path $WorkOps "out\unified_work_register.csv"
$consH   = Join-Path $WorkOps "out\Consistency_Report.html"
$healthJ = Join-Path $WorkOps "out\project_health.json"
$bkNew   = Get-ChildItem -Path (Join-Path $WorkOps "out\backups") -Filter "*.zip" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$bkPath  = $(if ($bkNew) { $bkNew.FullName } else { Join-Path $WorkOps "out\backups\(尚無)" })
foreach ($p in @($boardHtml, $eReport, $aReport, $naming, $decCsv, $ocrJson, $wopQ, $wopReg, $goldTpl, $accRep, $stRep, $uwrCsv, $consH, $healthJ, $bkPath)) {
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
