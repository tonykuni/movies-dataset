# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-DBPanel-v0100.ps1 — VIA 資料庫面板(唯讀;操作員令 2026-09-28)
#   從 VCGC 往下:① (選)git pull --ff-only → ② DataHome 目錄(CGC_MDL123 catalog --tables)
#   → ③ 主控台 dbm panel(CGC_MDL149 尾版路由 → CGC_MDL228 v0102+)→ ④ 讀 DBM_PANEL_latest.json 分區上色:
#      [1] 摘要  [2] 資料庫  [3] 數量核對  [4] 兩張清單(全部台股 · 主動式台股 ETF)  [5] 三項計畫
#      [6] 錯誤矩陣(嚴重度 · 來源 · 項目 · 說明 · 建議處置)  [7] AST 矩陣(檔 · 類別 · 說明 · 處置)  [8] 黃色貼回塊
#   → ⑤ (選)重建主控台藍圖頁(dbm ui)。
# 紀律(政策附冊 VIA_Policy_DBPanel_v0100.json):
#   · 唯讀:不寫庫、不動檔、不抓網、不代開同意閘;只寫 VIA_Reports\dbmanager\(再生件,永不 commit)。
#   · python 一律走中央 Invoke-VIAPython(禁止繞過直呼 python;helper 缺 = fail-closed 停)。
#   · 長輸出(政策前言、目錄逐表)寫進 VIA_Reports\dbmanager\logs\,畫面只留面板;貼回只貼黃色那段。
# 用法(一行一條,不要把多條貼成一行):
#   .\Invoke-VIA-DBPanel-v0100.ps1                   # 重掃目錄 + 面板
#   .\Invoke-VIA-DBPanel-v0100.ps1 -SkipCatalog      # 用現有目錄頁(快)
#   .\Invoke-VIA-DBPanel-v0100.ps1 -Pull -BuildUi    # 先拉最新碼,最後重建主控台藍圖頁
#   .\Invoke-VIA-DBPanel-v0100.ps1 -Rows 60          # 錯誤矩陣 / AST 矩陣 / 核對各顯示幾列(預設 25)
# 結束碼:0 = GREEN/AMBER · 1 = RED · 2 = NODATA/ABSENT · 3 = 面板沒跑出來(看 log)
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Pull,
    [switch]$SkipCatalog,
    [switch]$BuildUi,
    [ValidateRange(5, 500)][int]$Rows = 25
)

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
Set-Location -LiteralPath $Repo
$script:VIAAccelPairNote = "正主缺,略過"
try {
    $join = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $join) {
        . $join
        $script:VIAAccelPairNote = "套對 $($script:CeleritasPS7.Version) · 已套"
    }
} catch {
    $script:VIAAccelPairNote = "正主載入失敗,略過"
}
Write-Host ("  [加速器] " + $script:VIAAccelPairNote)
$env:VIA_FROM_VCGC = "YES"
$env:VIA_VCGC_PUSH = "NO"
$env:GIT_EDITOR = "true"
$env:GIT_TERMINAL_PROMPT = "0"

# ---------------------------------------------------------------- 共用小工具(StrictMode 安全)
function Get-DBPNewest {
    param([string]$Dir, [string]$Pattern)
    $hit = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $hit) { return $null }
    return $hit.FullName
}

function Get-DBPValue {
    # 讀 -AsHashtable 的 JSON:缺鍵回預設,不在 StrictMode 下炸
    param($Obj, [string]$Key, $Default = $null)
    if ($null -eq $Obj) { return $Default }
    if ($Obj -is [System.Collections.IDictionary]) {
        if ($Obj.Contains($Key) -and $null -ne $Obj[$Key]) { return $Obj[$Key] }
        return $Default
    }
    return $Default
}

function Get-DBPWidth {
    # 顯示寬度:中日韓全形字算 2 格
    param([string]$Text)
    if (-not $Text) { return 0 }
    $w = 0
    foreach ($ch in $Text.ToCharArray()) {
        $c = [int]$ch
        if (($c -ge 0x1100 -and $c -le 0x115F) -or ($c -ge 0x2E80 -and $c -le 0xA4CF) -or ($c -ge 0xAC00 -and $c -le 0xD7A3) -or
            ($c -ge 0xF900 -and $c -le 0xFAFF) -or ($c -ge 0xFE30 -and $c -le 0xFE4F) -or ($c -ge 0xFF00 -and $c -le 0xFF60) -or
            ($c -ge 0xFFE0 -and $c -le 0xFFE6)) { $w += 2 } else { $w += 1 }
    }
    return $w
}

function Format-DBPCell {
    # 截到指定顯示寬度(超過補 …),不足補空白
    param($Value, [int]$Width)
    $s = if ($null -eq $Value) { "—" } else { ("" + $Value) -replace "[\r\n]+", " " }
    if ((Get-DBPWidth $s) -gt $Width) {
        $sb = [System.Text.StringBuilder]::new()
        foreach ($ch in $s.ToCharArray()) {
            if ((Get-DBPWidth ($sb.ToString() + $ch)) -gt ($Width - 1)) { break }
            [void]$sb.Append($ch)
        }
        $s = $sb.ToString() + "…"
    }
    $pad = $Width - (Get-DBPWidth $s)
    if ($pad -gt 0) { $s = $s + (" " * $pad) }
    return $s
}

function Get-DBPColor {
    param([string]$State)
    switch -Regex ("" + $State) {
        '^(GREEN|OK)$' { return "Green" }
        '^(AMBER|MED|BAD)$' { return "Yellow" }
        '^(RED|HIGH|ABSENT|UNREADABLE)$' { return "Red" }
        '^(NODATA)$' { return "DarkYellow" }
        '^(LOW|INFO)$' { return "DarkGray" }
        default { return "Gray" }
    }
}

function Write-DBPSection {
    param([string]$Title)
    Write-Host ""
    Write-Host ("━━━━ " + $Title + " " + ("━" * [Math]::Max(4, 60 - (Get-DBPWidth $Title)))) -ForegroundColor Cyan
}

function Write-DBPTable {
    # Columns = @(@{k='鍵'; h='表頭'; w=寬}, ...);ColorKey 那一欄的值決定整列顏色
    param([object[]]$Items, [object[]]$Columns, [string]$ColorKey = "", [int]$Max = 25)
    $head = ($Columns | ForEach-Object { Format-DBPCell $_.h $_.w }) -join " │ "
    Write-Host ("  " + $head) -ForegroundColor White
    Write-Host ("  " + (($Columns | ForEach-Object { "─" * $_.w }) -join "─┼─")) -ForegroundColor DarkGray
    $n = 0
    foreach ($it in @($Items)) {
        if ($null -eq $it) { continue }
        if ($n -ge $Max) { break }
        $cells = foreach ($c in $Columns) { Format-DBPCell (Get-DBPValue $it $c.k "—") $c.w }
        $color = if ($ColorKey) { Get-DBPColor (Get-DBPValue $it $ColorKey "") } else { "Gray" }
        Write-Host ("  " + ($cells -join " │ ")) -ForegroundColor $color
        $n++
    }
    $total = @($Items | Where-Object { $null -ne $_ }).Count
    if ($total -gt $Max) { Write-Host ("  … 另 {0} 列(全表在 JSON / MD;-Rows 可加大)" -f ($total - $Max)) -ForegroundColor DarkGray }
    if ($total -eq 0) { Write-Host "  (無)" -ForegroundColor DarkGray }
}

function ConvertTo-DBPText {
    # 小字典 → "k v · k v"
    param($Map)
    if ($null -eq $Map -or -not ($Map -is [System.Collections.IDictionary]) -or $Map.Count -eq 0) { return "—" }
    return (($Map.GetEnumerator() | Sort-Object Name | ForEach-Object { "{0} {1}" -f $_.Name, $_.Value }) -join " · ")
}

# ---------------------------------------------------------------- 中央 python 入口(禁止繞過)
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
    if (Test-Path -LiteralPath $pyMod) { . $pyMod }
}
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Host "  [DB 面板] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
    exit 3
}

$reg = Join-Path $VIA "supportive modules\registry"
$outDir = Join-Path $VIA "VIA_Reports\dbmanager"
$logDir = Join-Path $outDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir ("DBPanel_" + $stamp + ".log")
$console = Get-DBPNewest $reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
$datahome = Get-DBPNewest $reg "CGC_MDL123_DataHome_v*.py"
if (-not $console) { Write-Host "  [DB 面板] VCGC 主控台尾版不在" -ForegroundColor Red; exit 3 }

function Invoke-DBPStep {
    # 跑一步:整段輸出進 log;@@PROGRESS|pct|msg → Write-Progress;回傳所有行 + rc
    param([string]$Title, [string]$Family, [string]$Script, [string[]]$ArgList)
    Add-Content -LiteralPath $logPath -Value ("===== " + $Title + " · " + (Get-Date -Format "HH:mm:ss") + " =====") -Encoding utf8
    $lines = [System.Collections.Generic.List[string]]::new()
    $global:LASTEXITCODE = 0
    Invoke-VIAPython -Family $Family $Script @ArgList 2>&1 | ForEach-Object {
        $ln = "" + $_
        if ($ln -match '^@@PROGRESS\|([\d.]+)\|(.*)$') {
            $pct = [int][double]$Matches[1]
            Write-Progress -Id 21 -Activity ("VIA 資料庫面板 · " + $Title) -Status $Matches[2] -PercentComplete ([Math]::Min(100, [Math]::Max(0, $pct)))
        } else {
            $lines.Add($ln)
        }
    }
    $rc = $global:LASTEXITCODE
    if ($lines.Count -gt 0) { Add-Content -LiteralPath $logPath -Value $lines -Encoding utf8 }
    Write-Progress -Id 21 -Activity ("VIA 資料庫面板 · " + $Title) -Completed
    return [pscustomobject]@{ Lines = $lines; Rc = $rc }
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  VIA 資料庫面板 · 唯讀 · VCGC → dbm panel                     ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ("  [log] " + $logPath) -ForegroundColor DarkGray

# ① 拉最新碼(選)
if ($Pull) {
    Write-Host "  [1/4] git pull --ff-only" -ForegroundColor Cyan
    $g = git -C $Repo pull --ff-only 2>&1
    $g | ForEach-Object { Add-Content -LiteralPath $logPath -Value ("" + $_) -Encoding utf8 }
    $gl = @($g)
    if ($gl.Count -gt 0) { Write-Host ("        " + $gl[$gl.Count - 1]) -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ne 0) { Write-Host "        git pull 沒成功(本機有改動或分叉);照現有碼繼續" -ForegroundColor Yellow }
} else {
    Write-Host "  [1/4] 略過 git pull(要拉最新碼加 -Pull)" -ForegroundColor DarkGray
}

# ② 資料家目錄
if (-not $SkipCatalog) {
    if ($datahome) {
        Write-Host "  [2/4] 資料家目錄 catalog --tables(逐表;輸出進 log)" -ForegroundColor Cyan
        $cat = Invoke-DBPStep "目錄" "vrn" $datahome @("catalog", "--tables")
        $cl = @($cat.Lines | Where-Object { $_ -match '\S' })
        $showN = [Math]::Min(3, $cl.Count)
        if ($showN -gt 0) { $cl[($cl.Count - $showN)..($cl.Count - 1)] | ForEach-Object { Write-Host ("        " + $_) -ForegroundColor DarkGray } }
        if ($cat.Rc -ne 0) { Write-Host ("        目錄 rc={0}(看 log);面板照跑,會照實標目錄狀態" -f $cat.Rc) -ForegroundColor Yellow }
    } else {
        Write-Host "  [2/4] 資料家 CGC_MDL123 尾版不在;面板照跑(目錄 = ABSENT)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [2/4] 略過目錄重掃(-SkipCatalog;用現有 DATAHOME_CATALOG_latest.json)" -ForegroundColor DarkGray
}

# ③ 面板
Write-Host "  [3/4] VCGC dbm panel(總覽 · 核對 · 計畫 · 兩張清單 · AST · 錯誤矩陣)" -ForegroundColor Cyan
$pan = Invoke-DBPStep "面板" "vrn" $console @("dbm", "panel")
$jsonPath = Join-Path $outDir "DBM_PANEL_latest.json"
$mdPath = Join-Path $outDir "DBM_PANEL_latest.md"
if (-not (Test-Path -LiteralPath $jsonPath)) {
    Write-Host ("  [DB 面板] 面板 JSON 沒產出(rc={0});最後幾行:" -f $pan.Rc) -ForegroundColor Red
    $pl = @($pan.Lines)
    $k = [Math]::Min(12, $pl.Count)
    if ($k -gt 0) { $pl[($pl.Count - $k)..($pl.Count - 1)] | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor DarkGray } }
    Write-Host ("  完整輸出:" + $logPath) -ForegroundColor DarkGray
    exit 3
}
$J = Get-Content -LiteralPath $jsonPath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
$ov = Get-DBPValue $J "overview" @{}
$kpi = Get-DBPValue $ov "kpi" @{}
$verdict = "" + (Get-DBPValue $J "verdict" "NODATA")

# [1] 摘要
Write-DBPSection ("[1] 摘要 · 判定 " + $verdict + " · " + (Get-DBPValue $J "engine" "") + " · " + (Get-DBPValue $J "ts" ""))
Write-DBPTable -Items @(Get-DBPValue $J "summary" @()) -ColorKey "state" -Max 40 -Columns @(
    @{ k = "section"; h = "區"; w = 22 }, @{ k = "state"; h = "狀態"; w = 7 }, @{ k = "headline"; h = "重點"; w = 90 })

# [2] 資料庫
Write-DBPSection ("[2] 資料庫 · 目錄 " + (Get-DBPValue $ov "catalog_ts" "—") + " · " + (Get-DBPValue $ov "catalog_state" "—"))
Write-Host ("  正庫 {0} · 對帳副本 {1} · {2} 表 · {3:N0} 列 · 最新 {4} · 湖 {5} 夾 {6} 檔 · 壞檔 {7}" -f `
    (Get-DBPValue $kpi "dbs" 0), (Get-DBPValue $kpi "replicas" 0), (Get-DBPValue $kpi "tables" 0), [long](Get-DBPValue $kpi "rows" 0),
    (Get-DBPValue $kpi "latest" "—"), (Get-DBPValue $kpi "lakes" 0), (Get-DBPValue $kpi "lake_files" 0), (Get-DBPValue $kpi "bad_files" 0))
$dbRows = foreach ($d in @(Get-DBPValue $ov "dbs" @())) {
    @{ role = (Get-DBPValue $d "role" ""); name = (Get-DBPValue $d "name" ""); tables = (Get-DBPValue $d "tables" 0)
       rows = ("{0:N0}" -f [long](Get-DBPValue $d "rows" 0)); latest = (Get-DBPValue $d "latest" "—")
       counts = (ConvertTo-DBPText (Get-DBPValue $d "counts" @{})); state = ("" + (Get-DBPValue $d "state" "OK")).ToUpper() }
}
Write-DBPTable -Items @($dbRows) -ColorKey "state" -Max 40 -Columns @(
    @{ k = "role"; h = "角色"; w = 8 }, @{ k = "name"; h = "庫"; w = 38 }, @{ k = "tables"; h = "表"; w = 4 },
    @{ k = "rows"; h = "列"; w = 13 }, @{ k = "latest"; h = "最新"; w = 10 }, @{ k = "counts"; h = "三態"; w = 36 })

# [3] 數量核對
$rec = Get-DBPValue $J "reconcile" @{}
Write-DBPSection ("[3] 數量核對 · " + (ConvertTo-DBPText (Get-DBPValue $rec "counts" @{})))
Write-DBPTable -Items @(Get-DBPValue $rec "rows" @()) -ColorKey "state" -Max $Rows -Columns @(
    @{ k = "state"; h = "狀態"; w = 6 }, @{ k = "db"; h = "庫"; w = 30 }, @{ k = "table"; h = "表"; w = 28 },
    @{ k = "rows_now"; h = "現在"; w = 11 }, @{ k = "why"; h = "原因"; w = 56 })

# [4] 兩張清單
$lst = Get-DBPValue $J "lists" @{}
Write-DBPSection ("[4] 兩張清單 · " + (Get-DBPValue $lst "state" "—") + " · 規則 股票 " + (Get-DBPValue (Get-DBPValue $lst "rules" @{}) "stock_code" "—") +
    " · 主動ETF " + (Get-DBPValue (Get-DBPValue $lst "rules" @{}) "active_etf_code" "—"))
$ls = @(Get-DBPValue $lst "summary" @())
if ($ls.Count -eq 0) { Write-Host ("  " + (Get-DBPValue $lst "why" "清單區塊沒有內容")) -ForegroundColor (Get-DBPColor (Get-DBPValue $lst "state" "")) }
foreach ($it in $ls) {
    $st = "" + (Get-DBPValue $it "state" "")
    Write-Host ("  ■ {0,-14} {1,-7} {2}" -f (Get-DBPValue $it "list" ""), $st, (Get-DBPValue $it "why" "")) -ForegroundColor (Get-DBPColor $st)
    Write-Host ("      表 {0} · 數 {1} · 剔除 {2}" -f (Get-DBPValue $it "table" "—"), (ConvertTo-DBPText (Get-DBPValue $it "counts" @{})),
        (ConvertTo-DBPText (Get-DBPValue $it "dropped" @{}))) -ForegroundColor DarkGray
    foreach ($c in @(Get-DBPValue $it "checks" @())) {
        $ok = [bool](Get-DBPValue $c "ok" $false)
        Write-Host ("      {0} {1}:{2}" -f $(if ($ok) { "OK" } else { "NG" }), (Get-DBPValue $c "check" ""), (Get-DBPValue $c "detail" "")) -ForegroundColor $(if ($ok) { "Green" } else { "Yellow" })
    }
}
$cross = Get-DBPValue $lst "crosscheck" @{}
if (@(Get-DBPValue $cross "listed_not_in_registry" @()).Count -gt 0) {
    Write-Host ("  交叉:" + (Get-DBPValue $cross "note" "") + ":" + (@(Get-DBPValue $cross "listed_not_in_registry" @()) -join ", ")) -ForegroundColor Yellow
}
if ((Get-DBPValue $lst "state" "") -ne "GREEN") {
    Write-Host "  更新順序(只列指令,本面板不代跑;要網路的步驟由操作員親開閘,見 via-gates):" -ForegroundColor Cyan
    foreach ($s in @(Get-DBPValue $lst "plan" @())) {
        Write-Host ("    {0}. {1}" -f (Get-DBPValue $s "step" ""), (Get-DBPValue $s "what" "")) -ForegroundColor Gray
        Write-Host ("         " + (Get-DBPValue $s "cmd" "")) -ForegroundColor White
    }
}

# [5] 三項計畫
Write-DBPSection "[5] 三項計畫(只出計畫;刪與搬是操作員的手 L10)"
$pls = @(Get-DBPValue $J "plan_lines" @())
if ($pls.Count -eq 0) { Write-Host "  (目錄不在,沒有計畫可算)" -ForegroundColor DarkGray }
foreach ($ln in $pls) { Write-Host ("  " + $ln) -ForegroundColor Gray }

# [6] 錯誤矩陣
$errs = @(Get-DBPValue $J "errors" @())
$sevCount = [ordered]@{ HIGH = 0; MED = 0; LOW = 0 }
foreach ($e in $errs) { $sv = "" + (Get-DBPValue $e "sev" ""); if ($sevCount.Contains($sv)) { $sevCount[$sv]++ } }
Write-DBPSection ("[6] 錯誤矩陣 · HIGH {0} · MED {1} · LOW {2}" -f $sevCount.HIGH, $sevCount.MED, $sevCount.LOW)
Write-DBPTable -Items $errs -ColorKey "sev" -Max $Rows -Columns @(
    @{ k = "sev"; h = "嚴重度"; w = 6 }, @{ k = "source"; h = "來源"; w = 6 }, @{ k = "item"; h = "項目"; w = 40 },
    @{ k = "desc"; h = "說明"; w = 52 }, @{ k = "action"; h = "建議處置"; w = 44 })

# [7] AST 矩陣
$ast = Get-DBPValue $J "ast" @{}
Write-DBPSection ("[7] AST 矩陣 · " + (ConvertTo-DBPText (Get-DBPValue $ast "by_class" @{})) + " · 嚴重度 " + (ConvertTo-DBPText (Get-DBPValue $ast "by_sev" @{})))
Write-DBPTable -Items @(Get-DBPValue $ast "files" @()) -ColorKey "state" -Max 40 -Columns @(
    @{ k = "file"; h = "檔"; w = 52 }, @{ k = "lang"; h = "語言"; w = 4 }, @{ k = "lines"; h = "行數"; w = 6 },
    @{ k = "defs"; h = "定義"; w = 5 }, @{ k = "issues"; h = "問題"; w = 5 }, @{ k = "high"; h = "HIGH"; w = 5 }, @{ k = "state"; h = "狀態"; w = 6 })
Write-Host ""
$astRows = foreach ($i in @(Get-DBPValue $ast "issues" @())) {
    @{ sev = (Get-DBPValue $i "sev" ""); cls = (Get-DBPValue $i "cls" "")
       at = ("{0}:{1}" -f (Get-DBPValue $i "file" ""), (Get-DBPValue $i "line" 0)); desc = (Get-DBPValue $i "desc" "")
       detail = (Get-DBPValue $i "detail" ""); action = (Get-DBPValue $i "action" "") }
}
Write-DBPTable -Items @($astRows) -ColorKey "sev" -Max $Rows -Columns @(
    @{ k = "sev"; h = "嚴重度"; w = 6 }, @{ k = "cls"; h = "類別"; w = 8 }, @{ k = "at"; h = "檔:行"; w = 44 },
    @{ k = "desc"; h = "類別說明"; w = 44 }, @{ k = "action"; h = "建議處置"; w = 40 })
$seen = @{}
foreach ($i in @(Get-DBPValue $ast "issues" @())) { $seen["" + (Get-DBPValue $i "cls" "")] = $true }
$legend = Get-DBPValue $ast "legend" @{}
if ($seen.Count -gt 0) {
    Write-Host "  類別說明(本次出現的):" -ForegroundColor DarkCyan
    foreach ($c in ($seen.Keys | Sort-Object)) { Write-Host ("    {0,-9} {1}" -f $c, (Get-DBPValue $legend $c "")) -ForegroundColor DarkGray }
}

# ④ 主控台藍圖頁(選)
if ($BuildUi) {
    Write-Host ""
    Write-Host "  [4/4] 重建主控台藍圖頁(dbm ui)" -ForegroundColor Cyan
    $ui = Invoke-DBPStep "主控台" "vrn" $console @("dbm", "ui")
    $ul = @($ui.Lines | Where-Object { $_ -match '\[DBM ui\]' })
    if ($ul.Count -gt 0) { Write-Host ("        " + $ul[$ul.Count - 1]) -ForegroundColor DarkGray } else { Write-Host ("        rc={0}(看 log)" -f $ui.Rc) -ForegroundColor Yellow }
} else {
    Write-Host ""
    Write-Host "  [4/4] 略過主控台重建(要重建加 -BuildUi)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host ("  [全表] JSON " + $jsonPath) -ForegroundColor DarkCyan
Write-Host ("  [全表] MD   " + $mdPath) -ForegroundColor DarkCyan
Write-Host ("  [log]  " + $logPath) -ForegroundColor DarkCyan

# [8] 黃色貼回塊:面板印在 BEGIN_PASTE / END_PASTE 之間的那段(沒有就用 JSON 的 paste)
$paste = [System.Collections.Generic.List[string]]::new()
$on = $false
foreach ($ln in $pan.Lines) {
    if ($ln -eq "BEGIN_PASTE") { $on = $true; continue }
    if ($ln -eq "END_PASTE") { $on = $false; continue }
    if ($on) { $paste.Add($ln) }
}
if ($paste.Count -eq 0) { foreach ($ln in @(Get-DBPValue $J "paste" @())) { $paste.Add("" + $ln) } }
Write-Host ""
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
foreach ($ln in $paste) { Write-Host $ln -ForegroundColor Yellow }
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow

switch ($verdict) {
    "GREEN" { exit 0 }
    "AMBER" { exit 0 }
    "RED" { exit 1 }
    default { exit 2 }
}
