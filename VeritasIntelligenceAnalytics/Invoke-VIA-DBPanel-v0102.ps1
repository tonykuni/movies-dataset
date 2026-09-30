# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-DBPanel-v0102.ps1 — VIA 資料庫面板 · 一支全包(操作員令 2026-09-28「one powershell code to handle all」)
#   v0102(v0101 留作版史 L04):工作站實錄——報告表格被貼回 PowerShell 當指令跑、剪貼簿一份蓋一份。所以:
#     ⓐ 預設先 git pull --ff-only(-NoPull 關);倉根另有啟動器 VIA-DBPanel.ps1,站在倉根打 .\VIA-DBPanel.ps1 就好。
#     ⓑ 跑完自動把「要貼回的東西」(黃色塊 + ① 總判 + ③ 行尾 + ⑨ mega 日期)組成一份,寫 DBM_PASTE_latest.txt 並放進剪貼簿;
#        操作員只要回 Claude 對話框按一次 Ctrl+V。-NoClipboard 關。
#   以下沿用 v0101:
#     ① 在哪個資料夾跑都行:路徑全從本檔位置算,不再因為站在倉根 / VIA 夾而「找不到路徑」。
#     ② 加速器(Celeritas PS7):Start-CeleritasPS7 起、Get-CeleritasRegex 編譯進度協定、Invoke-CeleritasParallel 並行算鎖定檔雜湊、
#        Read/Write-CeleritasText 讀寫 JSON、Get-CeleritasStatus 進報告、Write-CeleritasReport 存加速器頁、結束 Restore-CeleritasPS7。
#     ③ 鎖定檔行尾(Z231):律冊 + VRN_ENG112 v0100 + VRN_ENG110 v0114 三支逐支比「工作複本 / 換 LF 後 / 倉裡 blob」。
#        只差行尾 → 先備份到 VIA_Reports\dbmanager\restore\<時間>\ 再寫回倉裡原位元(寫入的位元組先證明 git blob = HEAD;內容一字不變);
#        內容真的不同 → 不碰、列 RED 請 via 審核。-NoEolFix = 只檢查不修。
#     ④ 資料家目錄(可 -SkipCatalog)→ ⑤ VCGC dbm panel(只認這次新寫的 JSON)→ ⑥ VCGC dbm report:rich 十二張矩陣
#        (總判 · 加速器 · 行尾 · 步驟 · 資料庫 · 核對 · 兩張清單 · 清單檢查 · mega 日期診斷 · 錯誤矩陣 · AST 檔 · AST 問題),
#        存 DBM_REPORT_latest.html / .txt;rich 缺 = 純文字同十二張。→ ⑦ (選)主控台重建 → ⑧ 黃色貼回塊。
# 紀律(政策附冊 VIA_Policy_DBPanel_v0100.json):不寫庫、不抓網、不代開同意閘;python 只走 Invoke-VIAPython(缺 = 停);
#   再生件只落 VIA_Reports\dbmanager\(永不 commit);修行尾只換回倉裡位元且先備份,不刪檔。
# 用法(一行一條;站在哪個資料夾都可以,給對本檔路徑即可):
#   .\VIA-DBPanel.ps1                     (站在倉根;啟動器找最新版)
#   & "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\Invoke-VIA-DBPanel-v0102.ps1"
#   ... -SkipCatalog     用現有目錄頁(快)
#   ... -NoEolFix        行尾只檢查不修
#   ... -NoPull          不先拉最新碼
#   ... -NoClipboard     不自動放進剪貼簿(貼回檔照寫)
#   ... -BuildUi         最後重建主控台藍圖頁
#   ... -PlainReport     不用 rich,純文字十二張
#   ... -Rows 60         長表(核對 · 錯誤 · AST 問題 · mega)每張最多幾列(預設 25;全表在面板 JSON)
# 結束碼:0 = GREEN/AMBER · 1 = RED · 2 = NODATA/ABSENT · 3 = 面板沒跑出來(看 log)
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$NoPull,
    [switch]$NoClipboard,
    [switch]$SkipCatalog,
    [switch]$NoEolFix,
    [switch]$BuildUi,
    [switch]$PlainReport,
    [ValidateRange(5, 500)][int]$Rows = 25
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$StartDir = (Get-Location).Path
Set-Location -LiteralPath $VIA
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
# 點源時 Celeritas 已自己 Start-CeleritasPS7(本行程減壓 + 快照);這裡只確認函式在,不重複起
$script:HasCeleritas = [bool](Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) -and [bool](Get-Command Invoke-CeleritasParallel -ErrorAction SilentlyContinue)
$verdict = "NODATA"

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
    }
    return $Default
}

function Get-DBPRegex {
    # 加速器:編譯過的 regex 快取(Get-CeleritasRegex);缺席退回一般 regex
    param([string]$Pattern)
    if ($script:HasCeleritas) { return (Get-CeleritasRegex -Pattern $Pattern) }
    return [regex]::new($Pattern)
}

function Read-DBPText {
    param([string]$Path)
    if ($script:HasCeleritas) { return (Read-CeleritasText -Path $Path) }
    return [IO.File]::ReadAllText($Path)
}

function Write-DBPText {
    param([string]$Path, [string]$Text)
    if ($script:HasCeleritas) { Write-CeleritasText -Path $Path -Text $Text; return }
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Get-DBPColor {
    param([string]$State)
    switch -Regex ("" + $State) {
        '^(GREEN|OK|FIXED)$' { return "Green" }
        '^(AMBER|MED|BAD|EOL_ONLY)$' { return "Yellow" }
        '^(RED|HIGH|ABSENT|UNREADABLE|CONTENT_DIFF)$' { return "Red" }
        '^(NODATA)$' { return "DarkYellow" }
        default { return "Gray" }
    }
}

# ---------------------------------------------------------------- 中央 python 入口(禁止繞過)
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
    if (Test-Path -LiteralPath $pyMod) { . $pyMod }
}
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Host "  [DB 面板] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
    Set-Location -LiteralPath $StartDir
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
$steps = [System.Collections.Generic.List[object]]::new()
$rxProg = Get-DBPRegex '^@@PROGRESS\|([\d.]+)\|(.*)$'
if (-not $console) { Write-Host "  [DB 面板] VCGC 主控台尾版不在" -ForegroundColor Red; Set-Location -LiteralPath $StartDir; exit 3 }

function Add-DBPStep {
    param([string]$Step, [int]$Rc, [double]$Sec, [string]$Note = "")
    $steps.Add([ordered]@{ step = $Step; rc = $Rc; sec = [Math]::Round($Sec, 1); note = $Note })
}

function Invoke-DBPStep {
    # 跑一步:整段輸出進 log;@@PROGRESS|pct|msg → Write-Progress;-Show 時其餘行直接上畫面(rich 報告用)
    param([string]$Title, [string]$Family, [string]$Script, [string[]]$ArgList, [switch]$Show)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $lines = [System.Collections.Generic.List[string]]::new()
    $global:LASTEXITCODE = 0
    Invoke-VIAPython -Family $Family $Script @ArgList 2>&1 | ForEach-Object {
        $ln = "" + $_
        $m = $rxProg.Match($ln)
        if ($m.Success) {
            $pct = [int][double]$m.Groups[1].Value
            Write-Progress -Id 21 -Activity ("VIA 資料庫面板 · " + $Title) -Status $m.Groups[2].Value -PercentComplete ([Math]::Min(100, [Math]::Max(0, $pct)))
        } else {
            $lines.Add($ln)
            if ($Show) { Write-Host $ln }
        }
    }
    $rc = $global:LASTEXITCODE
    Write-Progress -Id 21 -Activity ("VIA 資料庫面板 · " + $Title) -Completed
    $plain = $lines | ForEach-Object { $_ -replace "`e\[[0-9;]*m", "" }
    Add-Content -LiteralPath $logPath -Value (@("===== " + $Title + " · rc=" + $rc + " =====") + @($plain)) -Encoding utf8
    Add-DBPStep $Title $rc $sw.Elapsed.TotalSeconds ""
    return [pscustomobject]@{ Lines = $lines; Rc = $rc }
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  VIA 資料庫面板 v0102 · 一支全包 · 唯讀 · VCGC → dbm         ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ("  [位置] 本檔 " + $VIA + "(你站在 " + $StartDir + " 也沒關係)") -ForegroundColor DarkGray
Write-Host ("  [log]  " + $logPath) -ForegroundColor DarkGray

try {
    # ① 拉最新碼(選)
    if (-not $NoPull) {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        Write-Host "  [1/7] git pull --ff-only" -ForegroundColor Cyan
        $g = @(git -C $Repo pull --ff-only 2>&1 | ForEach-Object { "" + $_ })
        $grc = $LASTEXITCODE
        Add-Content -LiteralPath $logPath -Value (@("===== git pull · rc=" + $grc + " =====") + $g) -Encoding utf8
        if ($g.Count -gt 0) { Write-Host ("        " + $g[$g.Count - 1]) -ForegroundColor DarkGray }
        if ($grc -ne 0) { Write-Host "        git pull 沒成功(本機有改動或分叉);照現有碼繼續" -ForegroundColor Yellow }
        Add-DBPStep "git pull" $grc $sw.Elapsed.TotalSeconds ""
    } else {
        Write-Host "  [1/7] 略過 git pull(-NoPull)" -ForegroundColor DarkGray
    }

    # ② 鎖定檔行尾(Z231):加速器並行算三支的雜湊,再逐支判
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Write-Host "  [2/7] 鎖定檔行尾檢查(Z231)" -ForegroundColor Cyan
    $locked = @(
        "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json",
        "VeritasIntelligenceAnalytics/functional modules/VRN/VRN_ENG112_FinancialRead_v0100.py",
        "VeritasIntelligenceAnalytics/functional modules/VRN/VRN_ENG110_TabReport_v0114.py"
    )
    $items = foreach ($rel in $locked) {
        $headId = ("" + (git -C $Repo rev-parse ("HEAD:" + $rel) 2>$null)).Trim()
        [pscustomobject]@{ Rel = $rel; Full = (Join-Path $Repo ($rel -replace '/', '\')); Head = $headId }
    }
    $hashBlock = {
        # 並行 runspace 裡只用 .NET:sha256 前 16 碼(原位元 / 換 LF)+ git blob sha1(原位元 / 換 LF)
        $it = $_
        $o = [ordered]@{ Rel = $it.Rel; Full = $it.Full; Head = $it.Head; Exists = (Test-Path -LiteralPath $it.Full); Raw16 = ""; Lf16 = ""; RawBlob = ""; LfBlob = "" }
        if ($o.Exists) {
            $raw = [IO.File]::ReadAllBytes($it.Full)
            # Latin1 是位元組 1:1 對映:CRLF → LF 只動這兩個位元組,其餘一個不變
            $lf = [Text.Encoding]::Latin1.GetBytes([Text.Encoding]::Latin1.GetString($raw).Replace("`r`n", "`n"))
            $sha = [Security.Cryptography.SHA256]::Create()
            $o.Raw16 = ([BitConverter]::ToString($sha.ComputeHash($raw)) -replace '-', '').Substring(0, 16).ToLower()
            $o.Lf16 = ([BitConverter]::ToString($sha.ComputeHash($lf)) -replace '-', '').Substring(0, 16).ToLower()
            foreach ($pair in @(@("RawBlob", $raw), @("LfBlob", $lf))) {
                $hdr = [Text.Encoding]::ASCII.GetBytes("blob " + $pair[1].Length + [char]0)
                $s1 = [Security.Cryptography.SHA1]::Create()
                $buf = [byte[]]::new($hdr.Length + $pair[1].Length)
                [Array]::Copy($hdr, $buf, $hdr.Length)
                [Array]::Copy($pair[1], 0, $buf, $hdr.Length, $pair[1].Length)
                $o[$pair[0]] = ([BitConverter]::ToString($s1.ComputeHash($buf)) -replace '-', '').ToLower()
            }
        }
        [pscustomobject]$o
    }
    $hashed = if ($script:HasCeleritas) { @($items | Invoke-CeleritasParallel -Process $hashBlock) } else { @($items | ForEach-Object $hashBlock) }
    $eolRows = [System.Collections.Generic.List[object]]::new()
    $restoreDir = Join-Path $outDir ("restore\" + $stamp)
    foreach ($h in $hashed) {
        $name = Split-Path $h.Rel -Leaf
        $state = ""; $action = ""
        if (-not $h.Exists) { $state = "ABSENT"; $action = "檔不在(git pull 後再跑)" }
        elseif (-not $h.Head) { $state = "ABSENT"; $action = "倉裡 HEAD 沒有這支" }
        elseif ($h.RawBlob -eq $h.Head) { $state = "OK"; $action = "與倉裡原位元相同" }
        elseif ($h.LfBlob -eq $h.Head) {
            $state = "EOL_ONLY"; $action = "只差行尾(CRLF),內容與倉裡相同"
            if (-not $NoEolFix) {
                New-Item -ItemType Directory -Force -Path $restoreDir | Out-Null
                Copy-Item -LiteralPath $h.Full -Destination (Join-Path $restoreDir $name) -Force
                # 工作站實錄(R15):git checkout-index -f 看索引 stat 沒變就不寫 → 三支都「換回失敗」。
                # 改成直接寫 LF 位元組:上面已證明它的 git blob = HEAD blob,寫進去的就是倉裡原位元,不靠 git 的 stat 快取
                $lfBytes = [Text.Encoding]::Latin1.GetBytes([Text.Encoding]::Latin1.GetString([IO.File]::ReadAllBytes($h.Full)).Replace("`r`n", "`n"))
                [IO.File]::WriteAllBytes($h.Full, $lfBytes)
                git -C $Repo update-index -q --refresh 2>&1 | Out-Null
                $after = [IO.File]::ReadAllBytes($h.Full)
                $afterSha = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($after)) -replace '-', '').Substring(0, 16).ToLower()
                if ($afterSha -eq $h.Lf16) { $state = "FIXED"; $action = "已換回倉裡原位元 " + $afterSha + "(原檔備份:" + $restoreDir + ")" }
                else { $state = "EOL_ONLY"; $action = "換回失敗(現在 " + $afterSha + ");原檔備份在 " + $restoreDir }
            } else { $action += ";-NoEolFix:只檢查不修" }
        } else { $state = "CONTENT_DIFF"; $action = "內容與倉裡不同(不是行尾):不碰,請 via 審核" }
        $eolRows.Add([ordered]@{ file = $name; state = $state; raw16 = $h.Raw16; lf16 = $h.Lf16; head16 = ("" + $h.Head).Substring(0, [Math]::Min(16, ("" + $h.Head).Length)); action = $action })
        Write-Host ("        {0,-12} {1}  {2}" -f $state, $name, $action) -ForegroundColor (Get-DBPColor $state)
    }
    Add-DBPStep "行尾檢查" 0 $sw.Elapsed.TotalSeconds ("{0} 支" -f $eolRows.Count)

    # ③ 資料家目錄
    if (-not $SkipCatalog -and $datahome) {
        Write-Host "  [3/7] 資料家目錄 catalog --tables(逐表;輸出進 log)" -ForegroundColor Cyan
        $cat = Invoke-DBPStep "目錄" "vrn" $datahome @("catalog", "--tables")
        $okLine = @($cat.Lines | Where-Object { $_ -match '\[目錄\]' })
        if ($okLine.Count -gt 0) { Write-Host ("        " + $okLine[$okLine.Count - 1]) -ForegroundColor DarkGray }
        if ($cat.Rc -ne 0) { Write-Host ("        目錄 rc={0}(看 log);面板照跑,會照實標目錄狀態" -f $cat.Rc) -ForegroundColor Yellow }
    } elseif (-not $datahome) {
        Write-Host "  [3/7] 資料家 CGC_MDL123 尾版不在;面板照跑(目錄 = ABSENT)" -ForegroundColor Yellow
    } else {
        Write-Host "  [3/7] 略過目錄重掃(-SkipCatalog)" -ForegroundColor DarkGray
    }

    # ④ 面板(只認這次新寫的 JSON)
    Write-Host "  [4/7] VCGC dbm panel" -ForegroundColor Cyan
    $jsonPath = Join-Path $outDir "DBM_PANEL_latest.json"
    $panStart = [DateTime]::UtcNow.AddSeconds(-1)
    $pan = Invoke-DBPStep "面板" "vrn" $console @("dbm", "panel", "--quiet")
    $fresh = (Test-Path -LiteralPath $jsonPath) -and ((Get-Item -LiteralPath $jsonPath).LastWriteTimeUtc -ge $panStart)
    $rcOk = @(0, 1, 2) -contains [int]$pan.Rc
    $hasPaste = @($pan.Lines | Where-Object { $_ -eq "END_PASTE" }).Count -gt 0
    if (-not ($fresh -and $rcOk -and $hasPaste)) {
        $why = if (-not $fresh) { "這次沒有寫出新的面板 JSON" } elseif (-not $rcOk) { "面板 rc 不是 0/1/2" } else { "面板沒印完(沒有 END_PASTE)" }
        Write-Host ("  [DB 面板] 面板沒跑成(rc={0}):{1};最後幾行:" -f $pan.Rc, $why) -ForegroundColor Red
        $pl = @($pan.Lines)
        $k = [Math]::Min(12, $pl.Count)
        if ($k -gt 0) { $pl[($pl.Count - $k)..($pl.Count - 1)] | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor DarkGray } }
        Write-Host ("  完整輸出:" + $logPath) -ForegroundColor DarkGray
        exit 3
    }
    $J = (Read-DBPText $jsonPath) | ConvertFrom-Json -AsHashtable
    $verdict = "" + (Get-DBPValue $J "verdict" "NODATA")

    # ⑤ 側車:加速器狀態 + 行尾 + 步驟 → rich 報告一起畫
    $accel = [ordered]@{ "加速器" = $script:VIAAccelPairNote }
    if ($script:HasCeleritas) { try { $st = Get-CeleritasStatus; foreach ($k2 in $st.Keys) { $accel[$k2] = "" + $st[$k2] } } catch { $accel["狀態"] = "讀不到:" + $_.Exception.Message } }
    $accel["PowerShell"] = "" + $PSVersionTable.PSVersion
    $width = 160
    try { $width = [Math]::Max(100, [Math]::Min(220, $Host.UI.RawUI.WindowSize.Width - 2)) } catch { $width = 160 }
    $sidePath = Join-Path $outDir "DBM_PS_SIDE_latest.json"
    $side = [ordered]@{ schema = "VIA.DBM.PSSide.v1"; script = (Split-Path $PSCommandPath -Leaf); ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                        accel = $accel; eol = @($eolRows); steps = @($steps) }
    Write-DBPText $sidePath ($side | ConvertTo-Json -Depth 6)

    # ⑥ rich 詳細摘要矩陣(十二張)
    Write-Host "  [5/7] VCGC dbm report(rich 詳細摘要矩陣;缺 rich = 純文字同十二張)" -ForegroundColor Cyan
    Write-Host ""
    $env:COLUMNS = "" + $width
    $repArgs = @("dbm", "report", "--side", $sidePath, "--width", ("" + $width), "--rows", ("" + $Rows))
    if ($PlainReport) { $repArgs += "--plain" }
    $rep = Invoke-DBPStep "報告" "vrn" $console $repArgs -Show
    if ($rep.Rc -ne 0) { Write-Host ("  [報告] rc={0}:報告沒畫出來(面板 JSON 仍在;看 log)" -f $rep.Rc) -ForegroundColor Yellow }

    # ⑦ 主控台藍圖頁(選)
    if ($BuildUi) {
        Write-Host "  [6/7] 重建主控台藍圖頁(dbm ui)" -ForegroundColor Cyan
        $ui = Invoke-DBPStep "主控台" "vrn" $console @("dbm", "ui")
        $ul = @($ui.Lines | Where-Object { $_ -match '\[DBM ui\]' })
        if ($ul.Count -gt 0) { Write-Host ("        " + $ul[$ul.Count - 1]) -ForegroundColor DarkGray }
    } else {
        Write-Host "  [6/7] 略過主控台重建(要重建加 -BuildUi)" -ForegroundColor DarkGray
    }

    # 加速器頁
    $accelPage = Join-Path $outDir "DBM_ACCEL_latest.html"
    if ($script:HasCeleritas) { try { [void](Write-CeleritasReport -Path $accelPage) } catch { $accelPage = "(加速器頁沒寫成:" + $_.Exception.Message + ")" } }

    Write-Host ""
    Write-Host "  [7/7] 檔案" -ForegroundColor Cyan
    Write-Host ("        報告 HTML  " + (Join-Path $outDir "DBM_REPORT_latest.html")) -ForegroundColor DarkCyan
    Write-Host ("        報告 TXT   " + (Join-Path $outDir "DBM_REPORT_latest.txt")) -ForegroundColor DarkCyan
    Write-Host ("        面板 JSON  " + $jsonPath) -ForegroundColor DarkCyan
    Write-Host ("        加速器頁   " + $accelPage) -ForegroundColor DarkCyan
    Write-Host ("        log        " + $logPath) -ForegroundColor DarkCyan

    # ⑧ 黃色貼回塊(面板印的那段 + 行尾一行)
    $paste = [System.Collections.Generic.List[string]]::new()
    $on = $false
    foreach ($ln in $pan.Lines) {
        if ($ln -eq "BEGIN_PASTE") { $on = $true; continue }
        if ($ln -eq "END_PASTE") { $on = $false; continue }
        if ($on) { $paste.Add($ln) }
    }
    $paste.Insert([Math]::Min(1, $paste.Count), ("  行尾 " + (($eolRows | ForEach-Object { $_.state + " " + $_.file }) -join " · ")))
    Write-Host ""
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    foreach ($ln in $paste) { Write-Host $ln -ForegroundColor Yellow }
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow

    # 貼回包:黃色塊 + 報告 ① 總判 · ③ 行尾 · ⑨ mega 日期(從 DBM_REPORT_latest.txt 依區塊標題切出)→ 檔 + 剪貼簿
    $digest = [System.Collections.Generic.List[string]]::new()
    $digest.Add("### VIA 資料庫面板貼回包 · " + (Split-Path $PSCommandPath -Leaf) + " · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
    $digest.Add("")
    foreach ($ln in $paste) { $digest.Add($ln) }
    $txtPath = Join-Path $outDir "DBM_REPORT_latest.txt"
    if (Test-Path -LiteralPath $txtPath) {
        $all = (Read-DBPText $txtPath) -split "`r?`n"
        $rxHead = Get-DBPRegex '^━━ (.)'
        $keep = $false
        foreach ($ln in $all) {
            $m2 = $rxHead.Match($ln)
            if ($m2.Success) { $keep = @("①", "③", "⑨") -contains $m2.Groups[1].Value; if ($keep) { $digest.Add("") } }
            if ($keep) { $digest.Add($ln.TrimEnd()) }
        }
    }
    $pastePath = Join-Path $outDir "DBM_PASTE_latest.txt"
    Write-DBPText $pastePath (($digest -join "`n") + "`n")
    $clipOk = $false
    if (-not $NoClipboard -and (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
        try { Set-Clipboard -Value ($digest -join "`n"); $clipOk = $true } catch { $clipOk = $false }
    }
    Write-Host ""
    if ($clipOk) {
        Write-Host ("  ✅ 貼回包已放進剪貼簿(黃色塊 + ① 總判 + ③ 行尾 + ⑨ mega 日期,共 " + $digest.Count + " 行)") -ForegroundColor Green
        Write-Host "     → 回到 Claude 對話框按 Ctrl+V 送出就好。不要貼回 PowerShell。" -ForegroundColor Green
    } else {
        Write-Host ("  貼回包:" + $pastePath + "(剪貼簿沒放:-NoClipboard 或本機沒有 Set-Clipboard)") -ForegroundColor Yellow
    }
} finally {
    if ($script:HasCeleritas) { try { Restore-CeleritasPS7 } catch { } }
    Set-Location -LiteralPath $StartDir
}

switch ($verdict) {
    "GREEN" { exit 0 }
    "AMBER" { exit 0 }
    "RED" { exit 1 }
    default { exit 2 }
}
