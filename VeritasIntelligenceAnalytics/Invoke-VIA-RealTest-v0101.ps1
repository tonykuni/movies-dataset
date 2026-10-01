# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-RealTest-v0101.ps1 — 短指令 via-realtest(R43 · v0100 的下一版;via-realtest 自動取最新版號)
#   R43(2026-10-02 工作站實跑):操作員「他卡住了嗎」「en manager怎麼丟了」。量到的兩件事:
#   (a) ENV MANAGER(CGC_MDL240 v0100)依序委派 8 支正主、全跑完才一次印 → 畫面 780 秒沒字,進度條是「約 95%」假估;
#       而且它的 ⑨「鏈上缺件」讀 VDF / VRN 鏈的最新 JSON —— 和兩條鏈並行時讀到的是上一輪,不是本輪。
#   (b) 只在結尾輸出的工具(衝突 · 覆蓋)被「240 秒沒新輸出」嚇成像卡住。
#   本版:ENV 改成等 VDF / VRN 兩條鏈跑完才起跑(⑨ 讀本輪結果),用 CGC_MDL240 v0101 的逐委派進度行算真百分比(k/8);
#   結尾才輸出的工具,狀態寫「等結果 · 這支結尾才一次輸出」、停滯提示寫明「沒新輸出 ≠ 卡住」。其餘全照 v0100。
# ---- 以下為 v0100 原說明 ----
# Invoke-VIA-RealTest-v0100.ps1 — 短指令 via-realtest(R42 · 一支 PS 全包 · 不卡斷實測)
#   操作員(R42 2026-10-01):「要加入25個ps加速器 所有py擋要加入加速器 ps標準模板自動跳出html 三合一矩陣報告及結果驗證報告
#   請寫成短指令via_realtest … 太慢了還是卡斷 25個加速器 動態進度條 動態百分比 自動跳出報告」
#   「不要被vs code開啟 走環境流程也要自動檢查上下全部有無缺漏lib 現況有無衝突 依照他的邏輯補強環境工具無衝突
#    整個結果報告可透過via panorama結合更完整包含所有vcgc的控管項目」
#   「all into one ps code to handle all 所有加速模組及跳出html報告全部合一不卡斷實測 所有結果聚在最後 紅字為錯誤 黃字要貼給ai詳細且明確足夠」
#   工作站實錄:`run --family vdf CGC_MDL170_VDFChainRunner run` 印完「起始日 2023-07-01」就沒下文——鏈跑器逐站靜靜跑、全跑完才印總表。
#   本支(L70 這一次的許可;新檔,不動任何舊版)—— 從頭跑到尾不停,任何一步出事都照實記下、繼續下一步,所有結果聚在最後:
#   ① 加速模組:Celeritas PS7 模板(-RestoreOnly + Start-CeleritasPS7)+ 25 個 PS 加速器(Get-VIAAccelRoster 25/25)。不齊照實記紅,照跑。
#   ② VCGC 閘(status):照實記(沒過記紅、附 [同步] 原因),**不擋**;-StrictGate 才在閘沒過時停。
#   ③ 並行五條(各自子行程,經 VCGC):VCGC→VDF 鏈 · VCGC→VRN 鏈(鏈跑器 v0105 / v0108 起每站印進度)·
#      工具覆蓋(CGC_MDL230:所有 PY 加速器橋 · VDF 網路工具 · PS 加速器與模板)·
#      ENV MANAGER(CGC_MDL240:上下全部 LIB 缺漏 · 執行檔 · 輔助工具;只查不裝)· 現況衝突(CGC_MDL135 eight-hub:八路衝突 + uv)。
#      -FixEnv:照環境工具自己的邏輯補(既有 via-envtools -Apply -Approve:裝前 freeze · 順序安裝 · 同名獨立境;同意閘不代設),補完再驗。
#   ④ 動態進度條 + 百分比:每條一條 Write-Progress(k/N · 現在跑哪站 · 已幾秒)+ 總進度;-StallSec 秒沒新輸出印一次提示;
#      超過 -MaxMin 分鐘用看門狗停掉那條、照實記 TIMEOUT。
#   ⑤ 總報告:VIA Panorama monitor(VCGC 全部控管項目)→ 同步器三合一矩陣頁 → 自動跳出(全景 · 三合一 · VDF 鏈 · VRN 鏈 · 工具覆蓋);
#      **只走瀏覽器 exe**(Edge / Chrome),找不到就只印網址 —— 絕不交給 .html 預設程式(工作站是 VS Code)。-NoOpen 不開。
#   ⑥ 最後聚合:紅字 = 錯誤清單(閘 · 加速器 · 紅燈站 · 超時 · 衝突);黃字 = 「貼給 AI」整段(環境 · 版本 · 每個非綠項目的
#      站 / 燈 / 細節 / 補法 / 證據 · 缺件與補法 · 衝突 · 失敗 log 尾段 · 頁面路徑),同時寫 VIA_Reports\realtest\PASTE_TO_AI_latest.txt
#      並放進剪貼簿(Set-Clipboard 在就放)。只採本輪新寫的結果檔;舊檔不冒充(標「本輪沒產出」)。
#   不代開網路同意閘;不用 TA-Lib;不刪檔;本行程設的環境變數跑完全部還原。
# 用法:via-realtest [-Resume] [-FixEnv] [-NoOpen] [-StrictGate] [-StallSec 240] [-MaxMin 60]
#   或:pwsh -File .\VeritasIntelligenceAnalytics\Invoke-VIA-RealTest-v0101.ps1 [同上參數]
# 結束碼:0 = 全綠 · 2 = 有發現(黃 / GATED / NODATA / ABSENT / AMBER)· 1 = 有紅 · 124 = 有一條超時被停
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Resume,
    [switch]$FixEnv,
    [switch]$NoOpen,
    [switch]$StrictGate,
    [int]$StallSec = 240,
    [int]$MaxMin = 60
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
$Reg = Join-Path $VIA "supportive modules\registry"
$Rep = Join-Path $VIA "VIA_Reports"
$LogDir = Join-Path $Rep "realtest"
$clock = [Diagnostics.Stopwatch]::StartNew()
$runStart = Get-Date
$envKeys = @("VIA_FROM_VCGC", "VIA_VCGC_PUSH", "PYTHONUNBUFFERED", "PYTHONIOENCODING", "PYTHONWARNINGS", "VIA_NO_OPEN")
$envSaved = @{}
foreach ($k in $envKeys) { $envSaved[$k] = [Environment]::GetEnvironmentVariable($k, "Process") }
$Errs = New-Object System.Collections.Generic.List[string]     # 紅:錯誤
$Ai = New-Object System.Collections.Generic.List[string]       # 黃:貼給 AI
$exitCode = 0

function Get-RtNewest([string]$Dir, [string]$Pattern) {
    Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
}
function Get-RtPython {
    foreach ($c in @($env:VIA_PY, "python", "python3", "py")) {
        if (-not $c) { continue }
        $cmd = Get-Command $c -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
    }
    return $null
}
function Read-RtLog([string]$Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return @() }
    try {
        $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try { $sr = New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8); $t = $sr.ReadToEnd() } finally { $fs.Dispose() }
        return @($t -split "`r?`n")
    } catch { return @() }
}
function Read-RtJson([string]$Path) {
    # 只採本輪新寫的結果檔;舊檔回 $null(不冒充)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    if ((Get-Item -LiteralPath $Path).LastWriteTime -lt $runStart.AddSeconds(-2)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json -Depth 30 } catch { return $null }
}
function Get-P([object]$o, [string]$n) {
    # 安全取欄位:結果 JSON 各家欄位不一(VDF 站 id · VRN 站 layer),嚴格模式下取不存在的欄位會丟例外
    if ($null -eq $o) { return $null }
    $p = $o.PSObject.Properties[$n]
    if ($p) { return $p.Value }
    return $null
}
function Cut([object]$s, [int]$n = 260) { $t = ("" + $s) -replace "\s+", " "; if ($t.Length -gt $n) { $t.Substring(0, $n) + "…" } else { $t } }
function To-FileUri([string]$path) {
    $full = [IO.Path]::GetFullPath($path) -replace '\\', '/'
    if (-not $full.StartsWith('/')) { $full = '/' + $full }
    return 'file://' + (($full -split '/' | ForEach-Object { [Uri]::EscapeDataString($_) -replace '%3A', ':' }) -join '/')
}
function Open-RtPages([string[]]$Pages) {
    $p = @($Pages | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($p.Count -eq 0) { return }
    if (Get-Command Open-VIAPagesInBrowser -ErrorAction SilentlyContinue) { Open-VIAPagesInBrowser -Paths $p -Tag "via-realtest"; return }
    $bx = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
            "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
            "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if ($bx) { Start-Process -FilePath $bx -ArgumentList ($p | ForEach-Object { '"' + (To-FileUri $_) + '"' }) | Out-Null; return }
    # 找不到瀏覽器:只印網址,絕不交給 .html 預設程式(工作站是 VS Code)
    Write-Host "  [頁] 找不到 Edge / Chrome;請用瀏覽器開下列網址(不交給 .html 預設程式):" -ForegroundColor Yellow
    $p | ForEach-Object { Write-Host ("     " + (To-FileUri $_)) -ForegroundColor DarkGray }
}

try {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  via-realtest · 加速模組 → VCGC → VDF ∥ VRN ∥ 覆蓋 ∥ 環境 ∥ 衝突 → 全景 · 跳出  ║" -ForegroundColor Cyan
    Write-Host "  ╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

    # ① 加速模組
    $ps7 = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    $ps7State = "不在"
    if (Test-Path -LiteralPath $ps7) {
        try { . $ps7 -RestoreOnly; if (Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) { [void](Start-CeleritasPS7); $ps7State = "已套" } else { $ps7State = "載入(無 Start)" } }
        catch { $ps7State = "載入失敗:" + (Cut $_.Exception.Message 120) }
    }
    $roster = $null
    try { $roster = Get-VIAAccelRoster } catch { $roster = $null }
    $nAcc = if ($roster) { $roster.Count } else { 0 }
    if ($nAcc -eq 25) {
        Write-Host ("  ① PS 加速器 25/25 掛上 · Celeritas PS7 模板 " + $ps7State) -ForegroundColor Green
        Write-Host ("     " + (@($roster.Keys) -join " · ")) -ForegroundColor DarkGray
    } else {
        Write-Host ("  ① PS 加速器 " + $nAcc + "/25(不齊,照跑)") -ForegroundColor Red
        $Errs.Add("PS 加速器只有 " + $nAcc + "/25(VIA_PS_Accel_Module.ps1 / VIA_PS_Accelerators_25_Roster_v0100.ps1 沒載到)")
    }

    $py = Get-RtPython
    $V = Get-RtNewest $Reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    if (-not $py -or -not $V) {
        $Errs.Add("找不到 python(" + $py + ")或 VCGC 主控台尾版(" + $(if ($V) { $V.Name } else { "無" }) + ");先 git pull、確認 python 在 PATH")
        throw "no-python-or-console"
    }
    $env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"; $env:PYTHONUNBUFFERED = "1"; $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONWARNINGS = "ignore::SyntaxWarning"; $env:VIA_NO_OPEN = "1"

    # ② VCGC 閘(照實記,不擋)
    Write-Progress -Id 0 -Activity "via-realtest" -Status "② VCGC 閘(status)…" -PercentComplete 2
    $gate = @(& $py $V.FullName status 2>&1 | ForEach-Object { "" + $_ })
    $grc = $LASTEXITCODE
    $gateWhy = @($gate | Where-Object { $_ -match '\[同步\]' } | ForEach-Object { $_.Trim() })
    if ($grc -eq 0) { Write-Host "  ② VCGC 閘 · 過(rc 0)" -ForegroundColor Green }
    else {
        Write-Host ("  ② VCGC 閘 · 沒過(rc " + $grc + ")· 照實記下,實測照跑") -ForegroundColor Red
        $Errs.Add("VCGC 閘 status rc " + $grc + ":" + $(if ($gateWhy.Count) { Cut ($gateWhy -join " | ") 300 } else { "看 log" }))
        if ($StrictGate) { throw "gate" }
    }

    # ③ 並行五條
    $mode = if ($Resume) { @("run", "--resume") } else { @("run") }
    $lanes = @(
        [ordered]@{ id = "VDF"; title = "VCGC → VDF 鏈"; args = @($V.FullName, "run", "--family", "vdf", "CGC_MDL170_VDFChainRunner") + $mode; progress = $true; json = "vdf_chain\VDFCHAIN_latest.json" },
        [ordered]@{ id = "VRN"; title = "VCGC → VRN 鏈"; args = @($V.FullName, "run", "--family", "vrn", "CGC_MDL172_VRNChainRunner") + $mode; progress = $true; json = "vrn_chain\VRNCHAIN_latest.json" },
        [ordered]@{ id = "COV"; title = "工具覆蓋(PY 加速器 · VDF 網路 · PS 模板)"; args = @($V.FullName, "run", "--family", "core", "CGC_MDL230_ToolCoverageProbe", "matrix", "--no-open", "--ledger"); progress = $false; expect = 90; json = "toolprobe\COVERAGE_MATRIX_latest.json" },
        [ordered]@{ id = "ENV"; title = "環境 · 上下 LIB 缺漏(ENV MANAGER)"; args = @($V.FullName, "run", "--family", "core", "CGC_MDL240_EnvManager", "check"); progress = $true; after = @("VDF", "VRN"); json = "env_manager\ENVMGR_latest.json" },
        [ordered]@{ id = "CFL"; title = "環境 · 現況衝突(八路 + uv)"; args = @($V.FullName, "run", "--family", "core", "CGC_MDL135_EnvGovernance", "eight-hub"); progress = $false; expect = 20; json = "" }
    )
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $startLane = {
        param($ln)
        $argStr = ($ln.args | ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } }) -join " "
        try {
            $ln.proc = Start-Process -FilePath $py -ArgumentList $argStr -WorkingDirectory $VIA -NoNewWindow -PassThru `
                -RedirectStandardOutput $ln.log -RedirectStandardError $ln.err
        } catch {
            $ln.proc = $null
            $Errs.Add($ln.title + " 啟動失敗:" + (Cut $_.Exception.Message 200))
        }
        $ln.pending = $false
        $ln.t0 = Get-Date; $ln.lastSize = 0; $ln.lastChange = Get-Date; $ln.warned = $false; $ln.pct = 0; $ln.timeout = $false; $ln.now = "起步中"
        Write-Host ("  ③ 啟動 " + $ln.title) -ForegroundColor DarkGray
    }
    foreach ($ln in $lanes) {
        $ln.log = Join-Path $LogDir ($ln.id + "_" + $stamp + ".log")
        $ln.err = Join-Path $LogDir ($ln.id + "_" + $stamp + ".err.log")
        $ln.timeout = $false; $ln.pct = 0
        if ($ln.after) {
            # 等前置的鏈跑完才起跑(ENV ⑨ 鏈上缺件要讀本輪鏈結果)
            $ln.pending = $true; $ln.proc = $null; $ln.now = "排隊:等 " + ($ln.after -join " / ") + " 鏈跑完(⑨ 要讀本輪鏈結果)"
            Write-Host ("  ③ 排隊 " + $ln.title + " · " + $ln.now) -ForegroundColor DarkGray
            continue
        }
        & $startLane $ln
    }

    # ④ 動態進度 · 停滯提示 · 看門狗
    $ids = @{ VDF = 1; VRN = 2; COV = 3; ENV = 4; CFL = 5 }
    $alive = { @($lanes | Where-Object { $_.pending -or ($_.proc -and -not $_.proc.HasExited) }).Count }
    while ((& $alive) -gt 0) {
        foreach ($ln in $lanes) {
            if ($ln.pending) {
                $deps = @($lanes | Where-Object { $_.id -in $ln.after })
                if (@($deps | Where-Object { $_.pending -or ($_.proc -and -not $_.proc.HasExited) }).Count -eq 0) { & $startLane $ln }
                else { Write-Progress -Id $ids[$ln.id] -ParentId 0 -Activity $ln.title -Status $ln.now -PercentComplete 0; continue }
            }
            if (-not $ln.proc) { continue }
            $el = [int]((Get-Date) - $ln.t0).TotalSeconds
            if ($ln.proc.HasExited) {
                $ln.pct = 100
                Write-Progress -Id $ids[$ln.id] -ParentId 0 -Activity $ln.title -Status ("完成 · " + $el + "s") -PercentComplete 100
                continue
            }
            $size = if (Test-Path -LiteralPath $ln.log) { (Get-Item -LiteralPath $ln.log).Length } else { 0 }
            if ($size -ne $ln.lastSize) { $ln.lastSize = $size; $ln.lastChange = Get-Date; $ln.warned = $false }
            if ($ln.progress) {
                $lines = Read-RtLog $ln.log
                $done = @($lines | Where-Object { $_ -match '^\[進度\] \w+ \d+/(\d+|\?) 完成 ' })
                $started = @($lines | Where-Object { $_ -match '^\[進度\] \w+ (?:\d+/(?:\d+|\?) )?開始 ' })
                $k = 0; $n = 0
                if ($done.Count -and $done[-1] -match '(\d+)/(\d+|\?) 完成') { $k = [int]$Matches[1]; if ($Matches[2] -ne '?') { $n = [int]$Matches[2] } }
                if (-not $n -and $started.Count -and $started[-1] -match '(\d+)/(\d+) 開始') { $n = [int]$Matches[2] }
                if ($started.Count -and $started[-1] -match '開始 (.+)$') { $ln.now = $Matches[1] }
                $ln.pct = if ($n -gt 0) { [Math]::Min(99, [int](100 * $k / $n)) } else { [Math]::Min(95, $el) }
                $status = ("{0}/{1} 站 · {2}% · 現在:{3} · 已 {4}s" -f $k, $(if ($n) { $n } else { "?" }), $ln.pct, $ln.now, $el)
            } else {
                $ln.pct = [Math]::Min(90, [int](100 * $el / [Math]::Max(1, $ln.expect)))
                $ln.now = "等結果(這支結尾才一次輸出;沒新輸出 ≠ 卡住)"
                $status = ("等結果 · 這支結尾才一次輸出 · 已 {0}s(平常約 {1}s)" -f $el, $ln.expect)
            }
            Write-Progress -Id $ids[$ln.id] -ParentId 0 -Activity $ln.title -Status $status -PercentComplete $ln.pct
            $idle = [int]((Get-Date) - $ln.lastChange).TotalSeconds
            if ($idle -ge $StallSec -and -not $ln.warned) {
                $why = if ($ln.progress) { "這一站跑比較久;站有自己的逾時,超時照實記 NODATA" } else { "這支工具只在結尾才一次輸出,沒新輸出 ≠ 卡住" }
                Write-Host ("  ⚠ " + $ln.title + " 已 " + $idle + " 秒沒有新輸出 · 目前在:" + $ln.now + "(" + $why + ";看門狗 " + $MaxMin + " 分鐘會兜底,別按 Ctrl+C)") -ForegroundColor Yellow
                $ln.warned = $true
            }
            if ($el -ge ($MaxMin * 60)) {
                Write-Host ("  ⛔ " + $ln.title + " 超過 " + $MaxMin + " 分鐘 · 看門狗停掉(TIMEOUT)") -ForegroundColor Red
                try { $ln.proc.Kill($true) } catch { }
                $ln.timeout = $true
            }
        }
        $all = [int](($lanes | ForEach-Object { $_.pct } | Measure-Object -Average).Average)
        Write-Progress -Id 0 -Activity "via-realtest" -Status ("總進度 {0}% · 已 {1}s" -f $all, [int]$clock.Elapsed.TotalSeconds) -PercentComplete $all
        Start-Sleep -Milliseconds 700
    }
    foreach ($ln in $lanes) { if ($ln.proc) { $ln.proc.WaitForExit() }; Write-Progress -Id $ids[$ln.id] -Activity $ln.title -Completed }
    Write-Progress -Id 0 -Activity "via-realtest" -Completed

    # 環境補強(只在 -FixEnv;照環境工具自己的邏輯)
    $envLane = $lanes | Where-Object { $_.id -eq "ENV" } | Select-Object -First 1
    $fixNote = "沒帶 -FixEnv:只查不裝"
    if ($FixEnv) {
        if ($env:VIA_NET_CONSENT -ne "YES") { $fixNote = "-FixEnv 但同意閘沒開(`$env:VIA_NET_CONSENT='YES' 要你自己設):本輪只查不裝" }
        elseif (Get-Command via-envtools -ErrorAction SilentlyContinue) {
            Write-Host "  ⓔ -FixEnv:via-envtools -Apply -Approve(裝前 freeze · 順序安裝 · 同名獨立境)…" -ForegroundColor Cyan
            try { via-envtools -Apply -Approve; $fixNote = "-FixEnv:via-envtools -Apply -Approve 已跑(下方 ENV 為補完後再驗)" }
            catch { $fixNote = "-FixEnv:via-envtools 失敗:" + (Cut $_.Exception.Message 200); $Errs.Add($fixNote) }
            $null = & $py $V.FullName run --family core CGC_MDL240_EnvManager check 2>&1
        } else { $fixNote = "-FixEnv:via-envtools 沒註冊(先 . Register-VIA-Commands 尾版):本輪只查不裝" }
    }

    # ⑤ 全景 + 三合一 + 跳出
    $pano = Get-RtNewest $Reg "VIA_Panorama_v*.py"
    if ($pano) { $null = & $py $V.FullName run --family core $pano.FullName monitor 2>&1 }
    $adapter = Get-RtNewest $Reg "CGC_MDL241_TemplateAdapter_v*.py"
    $tplIn = Join-Path $VIA "VIA_HTML_UI\legacy\reference-templates\VIAHTMLUniversalUI-Standalone.html"
    $tri = Join-Path $Rep "template_adapter\synced\VIAHTMLUniversalUI_Standalone\VIA_UI_VIAHTMLUniversalUI_Standalone_latest.html"
    $triLine = ""
    if ($adapter -and (Test-Path -LiteralPath $tplIn)) {
        $s = @(& $py $V.FullName run --family vrn $adapter.FullName sync --in $tplIn 2>&1 | ForEach-Object { "" + $_ })
        $triLine = (@($s | Where-Object { $_ -match '\[模板同步\]' }) | Select-Object -Last 1)
    }
    $pages = @((Join-Path $Rep "panorama\monitor_latest.html"), $tri, (Join-Path $Rep "vdf_chain\VIA_VDF_Chain_Matrix_v0100.html"),
               (Join-Path $Rep "vrn_chain\VIA_VRN_Chain_Evidence_v0100.html"), (Join-Path $Rep "toolprobe\COVERAGE_MATRIX_latest.html")) |
             Where-Object { (Test-Path -LiteralPath $_) -and (Get-Item -LiteralPath $_).LastWriteTime -ge $runStart.AddSeconds(-2) }
    if (-not $NoOpen) { Open-RtPages $pages }

    # ⑥ 聚合:結果總表 → 紅字錯誤 → 黃字貼給 AI
    $head = (& git -C $Repo rev-parse --short HEAD 2>$null); $branch = (& git -C $Repo rev-parse --abbrev-ref HEAD 2>$null)
    & git -C $Repo fetch -q origin main 2>$null
    $ab = (& git -C $Repo rev-list --left-right --count "origin/main...HEAD" 2>$null)
    $dirty = @(& git -C $Repo status --porcelain 2>$null).Count
    $pyVer = (& $py --version 2>&1) -join ""
    $Ai.Add("===== 貼給 AI · via-realtest " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "(從這行到「貼給 AI 結束」整段複製)=====")
    $Ai.Add("[環境] 倉 " + $Repo + " · 分支 " + $branch + " · HEAD " + $head + " · 落後/領先 origin/main " + ($ab -replace "\s+", "/") + " · 未提交 " + $dirty + " 檔")
    $Ai.Add("[環境] " + $pyVer + " · pwsh " + $PSVersionTable.PSVersion + " · VCGC " + $V.Name + " · PS 加速器 " + $nAcc + "/25 · Celeritas PS7 " + $ps7State)
    $Ai.Add("[環境] VIA_NET_CONSENT=" + $env:VIA_NET_CONSENT + " · VIA_SCRAPE_CONSENT=" + $env:VIA_SCRAPE_CONSENT + " · VIA_DATA_HOME=" + $env:VIA_DATA_HOME + " · " + $fixNote)
    $Ai.Add("[VCGC 閘] status rc " + $grc + $(if ($gateWhy.Count) { " · " + (Cut ($gateWhy -join " | ") 600) } else { "" }))

    Write-Host ""
    Write-Host "  ═══════════════════ 結果總表 ═══════════════════" -ForegroundColor Cyan
    $worst = if ($Errs.Count) { 1 } else { 0 }
    foreach ($ln in $lanes) {
        $rc = if ($ln.timeout) { 124 } elseif ($ln.proc) { $ln.proc.ExitCode } else { -1 }
        $secs = if ($ln.t0) { [int]((Get-Date) - $ln.t0).TotalSeconds } else { 0 }
        $lines = Read-RtLog $ln.log
        $tally = @($lines | Where-Object { $_ -match '\[計\] GREEN|\[ENV MANAGER\] 總判|\[八路衝突|覆蓋矩陣|總判|verdict' } | Select-Object -Last 1)
        $color = if ($rc -eq 0) { "Green" } elseif ($rc -in 2, 3, 4) { "Yellow" } else { "Red" }
        Write-Host ("  " + $ln.title.PadRight(30) + " rc " + ("" + $rc).PadLeft(3) + " · " + ("" + $secs).PadLeft(4) + "s · " + $(if ($tally.Count) { Cut $tally[0] 120 } else { "(看 log)" })) -ForegroundColor $color
        if ($rc -eq 124) { $Errs.Add($ln.title + " 超過 " + $MaxMin + " 分鐘被看門狗停掉;停前最後在:" + $ln.now) }
        elseif ($rc -eq 1 -or $rc -lt 0) { $Errs.Add($ln.title + " rc " + $rc + "(" + $(if ($tally.Count) { Cut $tally[0] 160 } else { "看 log" }) + ")") }
        $sev = if ($rc -eq 0) { 0 } elseif ($rc -eq 124) { 124 } elseif ($rc -in 2, 3, 4) { 2 } else { 1 }
        if ($sev -eq 124 -or ($sev -eq 1 -and $worst -ne 124) -or ($sev -eq 2 -and $worst -eq 0)) { $worst = $sev }

        $Ai.Add("")
        $Ai.Add("[" + $ln.id + "] " + $ln.title + " · rc " + $rc + " · " + $secs + "s · " + $(if ($tally.Count) { Cut $tally[0] 200 } else { "無總結行" }) + " · log " + $ln.log)
        $j = if ($ln.json) { Read-RtJson (Join-Path $Rep $ln.json) } else { $null }
        if ($ln.json -and -not $j) { $Ai.Add("  (本輪沒產出 " + $ln.json + ";舊檔不採用)") }
        if ($j) {
            if ((Get-P $j 'stages')) {
                foreach ($st in @((Get-P $j 'stages') | Where-Object { (Get-P $_ 'state') -ne "GREEN" -and (Get-P $_ 'state') -ne "SKIP" })) {
                    $sid = if ((Get-P $st 'id')) { (Get-P $st 'id') } else { (Get-P $st 'layer') }
                    $Ai.Add("  - " + $sid + " " + (Get-P $st 'name') + " · " + (Get-P $st 'state') + " · 細節:" + (Cut (Get-P $st 'detail') 420) + $(if ((Get-P $st 'fix')) { " · 補法:" + (Cut (Get-P $st 'fix') 200) } else { "" }) + $(if ((Get-P $st 'evidence')) { " · 證據:" + (Get-P $st 'evidence') } else { "" }))
                    if ((Get-P $st 'state') -eq "RED") { $Errs.Add($ln.id + " 紅燈:" + $sid + " " + (Get-P $st 'name') + " · " + (Cut (Get-P $st 'detail') 220)) }
                }
            } elseif ($ln.id -eq "COV") {
                $Ai.Add("  總判 " + (Get-P $j 'verdict'))
                foreach ($r in @((Get-P $j 'rows') | Where-Object { (Get-P $_ 'lamp') -ne "GREEN" })) {
                    $Ai.Add("  - " + (Get-P $r 'title') + " [" + (Get-P $r 'group') + "] · " + (Get-P $r 'lamp') + " · " + (Get-P $r 'have') + "/" + (Get-P $r 'elig') + $(if ((Get-P $r 'miss')) { " · 缺:" + (Cut (@((Get-P $r 'miss')) -join ", ") 300) } else { "" }) + $(if ((Get-P $r 'perr')) { " · 剖析錯:" + (Cut (@((Get-P $r 'perr')) -join ", ") 200) } else { "" }))
                    if ((Get-P $r 'lamp') -eq "RED") { $Errs.Add("工具覆蓋紅:" + (Get-P $r 'title') + " [" + (Get-P $r 'group') + "] 缺 " + (Cut (@((Get-P $r 'miss')) -join ", ") 160)) }
                }
            } elseif ($ln.id -eq "ENV") {
                $Ai.Add("  總判 " + (Get-P $j 'verdict') + " · " + (((Get-P $j 'tally').PSObject.Properties | ForEach-Object { $_.Name + " " + $_.Value }) -join " · "))
                foreach ($r in @((Get-P $j 'rows') | Where-Object { (Get-P $_ 'state') -ne "GREEN" })) {
                    $Ai.Add("  - " + (Get-P $r 'group') + " " + (Get-P $r 'item') + " · " + (Get-P $r 'state') + " · " + (Cut (Get-P $r 'note') 220) + $(if ((Get-P $r 'fix')) { " · 補法:" + (Cut (Get-P $r 'fix') 220) } else { "" }))
                    if ((Get-P $r 'state') -eq "RED") { $Errs.Add("環境紅:" + (Get-P $r 'item') + " · " + (Cut (Get-P $r 'note') 160) + " · 補法:" + (Cut (Get-P $r 'fix') 160)) }
                }
                $Ai.Add("  補法一貼即用:" + (Join-Path $Rep "env_governance\TOOLS_PLAN_latest.ps1") + "(裝件是操作員的手;-FixEnv 走 via-envtools -Apply -Approve)")
            }
        }
        if ($ln.id -eq "CFL") {
            $cf = @($lines | Where-Object { $_ -match '\[八路衝突|BLOCK|forbidden|mismatch' -and $_ -notmatch '^\s*\[(政策|分群|不衝突|靜態|位階|加速|環境計畫|回覆|衝突|還原)\]|^\[第一步' } | Select-Object -First 12)
            $cf | ForEach-Object { $Ai.Add("  " + (Cut $_ 400)) }
            if ($rc -ne 0 -and $cf.Count) { $Errs.Add("現況衝突:" + (Cut $cf[0] 200)) }
        }
        if ($rc -ne 0) {
            $tail = @((Read-RtLog $ln.err) + $lines | Where-Object { $_ -and $_ -notmatch '^\s*\[(政策|分群|不衝突|靜態|位階|加速|環境計畫|回覆|衝突|還原)\]|^\[第一步|^\[政策\]' } | Select-Object -Last 8)
            if ($tail.Count) { $Ai.Add("  log 尾段:"); $tail | ForEach-Object { $Ai.Add("    " + (Cut $_ 300)) } }
        }
    }
    $pj = Read-RtJson (Join-Path $Rep "panorama\monitor_latest.json")
    $Ai.Add("")
    if ($pj) {
        $Ai.Add("[全景 VCGC 控管] 總判 " + (Get-P $pj 'verdict'))
        foreach ($r in @((Get-P $pj 'rows') | Where-Object { (Get-P $_ 'lamp') -ne "GREEN" })) {
            $Ai.Add("  - " + (Get-P $r 'track') + " · " + (Get-P $r 'lamp') + " · " + (Cut (Get-P $r 'value') 260) + $(if ((Get-P $r 'note')) { " · " + (Cut (Get-P $r 'note') 200) } else { "" }))
        }
    } else { $Ai.Add("[全景 VCGC 控管] 本輪沒產出 monitor_latest.json") }
    $Ai.Add("[三合一] " + $(if ($triLine) { Cut $triLine 240 } else { "本輪沒產出" }))
    $Ai.Add("[頁] " + (@($pages | ForEach-Object { (To-FileUri $_) }) -join " · "))
    $Ai.Add("[時間] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $worst)
    $Ai.Add("===== 貼給 AI 結束 =====")
    $exitCode = $worst

    Write-Host ""
    if ($Errs.Count) {
        Write-Host ("  ═══════════════════ 錯誤(紅)· " + $Errs.Count + " 項 ═══════════════════") -ForegroundColor Red
        $i = 0; foreach ($e in $Errs) { $i++; Write-Host ("  " + $i + ". " + $e) -ForegroundColor Red }
    } else {
        Write-Host "  ═══════════════════ 錯誤(紅)· 0 項 ═══════════════════" -ForegroundColor Green
    }
    Write-Host ""
    foreach ($a in $Ai) { Write-Host $a -ForegroundColor Yellow }
    $out = Join-Path $LogDir "PASTE_TO_AI_latest.txt"
    $Ai | Set-Content -LiteralPath $out -Encoding utf8
    Copy-Item -LiteralPath $out -Destination (Join-Path $LogDir ("PASTE_TO_AI_" + $stamp + ".txt")) -Force
    $clip = $false
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { try { ($Ai -join [Environment]::NewLine) | Set-Clipboard; $clip = $true } catch { } }
    Write-Host ""
    Write-Host ("  [via-realtest] 黃字整段已存 " + $out + $(if ($clip) { " · 也已放進剪貼簿(直接 Ctrl+V 貼給 AI)" } else { "" })) -ForegroundColor Cyan
    Write-Host ("  [via-realtest] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $exitCode + "(0 全綠 · 2 有發現 · 1 有紅 · 124 超時)") -ForegroundColor Cyan
} catch {
    if ("$_" -notin @("gate", "no-python-or-console")) { $Errs.Add("via-realtest 自身例外:" + (Cut $_.Exception.Message 300) + " @ 行 " + $_.InvocationInfo.ScriptLineNumber) }
    Write-Host ""
    Write-Host ("  ═══════════════════ 錯誤(紅)· " + $Errs.Count + " 項 ═══════════════════") -ForegroundColor Red
    $i = 0; foreach ($e in $Errs) { $i++; Write-Host ("  " + $i + ". " + $e) -ForegroundColor Red }
    Write-Host "===== 貼給 AI(提前停止)=====" -ForegroundColor Yellow
    foreach ($e in $Errs) { Write-Host ("  " + $e) -ForegroundColor Yellow }
    Write-Host ("  pwsh " + $PSVersionTable.PSVersion + " · 倉 " + $Repo) -ForegroundColor Yellow
    Write-Host "===== 貼給 AI 結束 =====" -ForegroundColor Yellow
    $exitCode = 1
} finally {
    foreach ($k in $envKeys) { [Environment]::SetEnvironmentVariable($k, $envSaved[$k], "Process") }
}
exit $exitCode
