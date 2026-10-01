# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-RealTest-v0100.ps1 — 短指令 via-realtest(R42 · VCGC-REQ098)
#   操作員(R42 2026-10-01):「要加入25個ps加速器 所有py擋要加入加速器 ps標準模板自動跳出html 三合一矩陣報告及結果驗證報告
#   請寫成短指令via_realtest … 太慢了還是卡斷 25個加速器 動態進度條 動態百分比 自動跳出報告」。
#   工作站實錄:`run --family vdf CGC_MDL170_VDFChainRunner run` 印完「起始日 2023-07-01」就沒下文——鏈跑器逐站靜靜跑、全跑完才印總表。
#   本支(L70 這一次的許可;新檔,不動任何舊版):
#   ① 加速器:Celeritas PS7 模板(VeritasCeleritas.PS7 -RestoreOnly + Start-CeleritasPS7)+ 25 個 PS 加速器(Get-VIAAccelRoster 必須 25/25)。
#   ② 閘:VCGC status 必須 rc 0(沒過就停,印出 [同步] 那一行;-SkipGate 跳過)。
#   ③ 並行五條(各自子行程,經 VCGC):VCGC→VDF 鏈(CGC_MDL170 v0105 起每站印進度)· VCGC→VRN 鏈(CGC_MDL172 v0108 起每節點印進度)·
#      工具覆蓋矩陣(CGC_MDL230:所有 PY 加速器橋 / VDF 網路工具 / PS 加速器與模板 —— 「所有 py 檔要加入加速器」的實測)·
#      環境流程(操作員同日追加「走環境流程也要自動檢查上下全部有無缺漏 lib 現況有無衝突 依照他的邏輯補強環境工具無衝突」):
#      ENV MANAGER(CGC_MDL240 check:輔助工具 · 各家族 python 必備 LIB · 鏈上報過的缺件 · 執行檔 · PS 端;只查不裝)·
#      八路衝突 + uv 計畫(CGC_MDL135 eight-hub:現況有無衝突)。
#      -FixEnv:照環境工具自己的邏輯補 —— 走既有 via-envtools -Apply -Approve(裝前 freeze 存證 · L24 順序安裝 · 同名獨立境;
#      同意閘 VIA_NET_CONSENT 不代設,沒開就只印補法),補完再跑一次 ENV MANAGER 驗。沒帶 -FixEnv = 只查不裝。
#   ④ 動態進度條 + 動態百分比:每條鏈一條 Write-Progress(k/N · 現在跑哪站 · 已幾秒),總進度一條;
#      某條 -StallSec(預設 240)秒沒有新輸出 → 印一次「在跑哪一站、多久沒動」(站有自己的逾時,超時照實記 NODATA,不是卡死);
#      整體超過 -MaxMin(預設 60)分鐘 → 用加速器模組同款看門狗停掉那條並照實報 TIMEOUT(不假綠)。
#   ⑤ 跑完自動跳出:VIA Panorama monitor(VCGC 全部控管項目:實跑事件 · VDF / VRN 鏈 · SDD · 串測 · 交接 · TA-Lib)重產全景頁 →
#      同步器 CGC_MDL241 重產三合一矩陣頁(VCGC + VDF 鏈 + VRN 鏈 + 工具覆蓋 · 燈號 + 實測結果驗證)
#      + VDF 鏈矩陣頁 + VRN 鏈證據頁 + 工具覆蓋矩陣頁 + ENV MANAGER 頁;**只走瀏覽器 exe**(Edge / Chrome),
#      找不到瀏覽器就只印路徑 —— 絕不交給 .html 預設程式(工作站預設是 VS Code);-NoOpen 不開。
#   ⑥ -Resume:兩條鏈只重跑上一回不綠的站(鏈跑器 run --resume)。
#   不代開網路同意閘(VIA_NET_CONSENT 照你的視窗設定;沒開 = VDF 0b GATED,照實);不用 TA-Lib;不刪檔、不改機器環境變數(本行程設的全部還原)。
# 用法(站在倉根或任何地方):via-realtest [-Resume] [-FixEnv] [-NoOpen] [-SkipGate] [-StallSec 240] [-MaxMin 60]
#   或直接:pwsh -File .\VeritasIntelligenceAnalytics\Invoke-VIA-RealTest-v0100.ps1 [同上參數]
# 結束碼:0 = 三條全綠 · 2 = 有 GATED / NODATA / ABSENT / YELLOW(有發現)· 1 = 有紅 · 3 = 閘沒過 / 加速器不齊 · 124 = 有一條超時被停
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Resume,
    [switch]$FixEnv,
    [switch]$NoOpen,
    [switch]$SkipGate,
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
$Reg = Join-Path $VIA "supportive modules\registry"
$Rep = Join-Path $VIA "VIA_Reports"
$LogDir = Join-Path $Rep "realtest"
$clock = [Diagnostics.Stopwatch]::StartNew()
$exitCode = 0
$envKeys = @("VIA_FROM_VCGC", "VIA_VCGC_PUSH", "PYTHONUNBUFFERED", "PYTHONIOENCODING", "PYTHONWARNINGS", "VIA_NO_OPEN")
$envSaved = @{}
foreach ($k in $envKeys) { $envSaved[$k] = [Environment]::GetEnvironmentVariable($k, "Process") }

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

function Open-RtPages([string[]]$Pages) {
    $p = @($Pages | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($p.Count -eq 0) { return }
    if (Get-Command Open-VIAPagesInBrowser -ErrorAction SilentlyContinue) { Open-VIAPagesInBrowser -Paths $p -Tag "via-realtest"; return }
    $bx = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
            "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
            "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if ($bx) { Start-Process -FilePath $bx -ArgumentList ($p | ForEach-Object { '"' + ([Uri]$_).AbsoluteUri + '"' }) | Out-Null; return }
    # 找不到瀏覽器:只印路徑,絕不 Invoke-Item(.html 預設程式在工作站是 VS Code)
    Write-Host "  [頁] 找不到 Edge / Chrome;請用瀏覽器手動開(不交給 .html 預設程式):" -ForegroundColor Yellow
    $p | ForEach-Object { Write-Host ("     " + ([Uri]$_).AbsoluteUri) -ForegroundColor DarkGray }
}

function Read-RtLog([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    try {
        $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try { $sr = New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8); $t = $sr.ReadToEnd() } finally { $fs.Dispose() }
        return @($t -split "`r?`n")
    } catch { return @() }
}

try {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  via-realtest · VCGC → VDF ∥ VRN ∥ 覆蓋 ∥ 環境 · 動態進度 · 自動跳出 ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

    # ① 加速器:Celeritas PS7 模板 + 25 個 PS 加速器
    $ps7 = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
    if (Test-Path -LiteralPath $ps7) {
        try { . $ps7 -RestoreOnly; if (Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) { [void](Start-CeleritasPS7) } } catch { }
    }
    $roster = $null
    try { $roster = Get-VIAAccelRoster } catch { $roster = $null }
    if (-not $roster -or $roster.Count -ne 25) {
        Write-Host ("  ① PS 加速器 · 不齊(" + $(if ($roster) { $roster.Count } else { 0 }) + "/25)· 先 git pull 讓 VIA_PS_Accel_Module 與 25 名冊在位") -ForegroundColor Red
        $exitCode = 3
        return
    }
    Write-Host ("  ① PS 加速器 25/25 掛上 · Celeritas PS7 模板" + $(if (Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) { " 已套" } else { " 不在(照跑)" })) -ForegroundColor Green
    Write-Host ("     " + (@($roster.Keys) -join " · ")) -ForegroundColor DarkGray

    $py = Get-RtPython
    $V = Get-RtNewest $Reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    if (-not $py -or -not $V) { Write-Host "  [via-realtest] 找不到 python 或 VCGC 主控台尾版(先 git pull)" -ForegroundColor Red; $exitCode = 3; return }
    $env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"; $env:PYTHONUNBUFFERED = "1"; $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONWARNINGS = "ignore::SyntaxWarning"; $env:VIA_NO_OPEN = "1"
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

    # ② 閘
    if (-not $SkipGate) {
        Write-Progress -Id 0 -Activity "via-realtest" -Status "② VCGC 閘(status)…" -PercentComplete 2
        $g = @(& $py $V.FullName status 2>&1 | ForEach-Object { "" + $_ })
        $grc = $LASTEXITCODE
        if ($grc -ne 0) {
            Write-Host ("  ② VCGC 閘 · 沒過(rc " + $grc + ")· 一步都不跑") -ForegroundColor Red
            $g | Where-Object { $_ -match '\[同步\]|\[子系統\]' } | ForEach-Object { Write-Host ("     " + $_.Trim()) -ForegroundColor Yellow }
            Write-Host "     先 python `$V run --family core CGC_MDL143_MergeMedic sync --apply(拉齊)或 registry-sync,再跑一次" -ForegroundColor DarkGray
            $exitCode = 3
            return
        }
        Write-Host "  ② VCGC 閘 · 過(rc 0)" -ForegroundColor Green
    }

    # ③ 並行三條
    $mode = if ($Resume) { @("run", "--resume") } else { @("run") }
    $adapter = Get-RtNewest $Reg "CGC_MDL241_TemplateAdapter_v*.py"
    $lanes = @(
        [ordered]@{ id = "VDF"; title = "VCGC → VDF 鏈"; args = @($V.FullName, "run", "--family", "vdf", "CGC_MDL170_VDFChainRunner") + $mode; progress = $true },
        [ordered]@{ id = "VRN"; title = "VCGC → VRN 鏈"; args = @($V.FullName, "run", "--family", "vrn", "CGC_MDL172_VRNChainRunner") + $mode; progress = $true },
        [ordered]@{ id = "COV"; title = "工具覆蓋(PY 加速器 · VDF 網路 · PS 模板)"; args = @($V.FullName, "run", "--family", "core", "CGC_MDL230_ToolCoverageProbe", "matrix", "--no-open", "--ledger"); progress = $false; expect = 90 },
        [ordered]@{ id = "ENV"; title = "環境 · 上下 LIB 缺漏(ENV MANAGER)"; args = @($V.FullName, "run", "--family", "core", "CGC_MDL240_EnvManager", "check"); progress = $false; expect = 90 },
        [ordered]@{ id = "CFL"; title = "環境 · 現況衝突(八路 + uv)"; args = @($V.FullName, "run", "--family", "core", "CGC_MDL135_EnvGovernance", "eight-hub"); progress = $false; expect = 20 }
    )
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    foreach ($ln in $lanes) {
        $ln.log = Join-Path $LogDir ($ln.id + "_" + $stamp + ".log")
        $ln.err = Join-Path $LogDir ($ln.id + "_" + $stamp + ".err.log")
        $argStr = ($ln.args | ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } }) -join " "
        $ln.proc = Start-Process -FilePath $py -ArgumentList $argStr -WorkingDirectory $VIA -NoNewWindow -PassThru `
            -RedirectStandardOutput $ln.log -RedirectStandardError $ln.err
        $ln.t0 = Get-Date; $ln.lastSize = 0; $ln.lastChange = Get-Date; $ln.warned = $false; $ln.pct = 0; $ln.timeout = $false
        Write-Host ("  ③ 啟動 " + $ln.title + " · log " + (Split-Path $ln.log -Leaf)) -ForegroundColor DarkGray
    }

    # ④ 動態進度條 + 百分比 + 停滯提示 + 整體上限
    $ids = @{ VDF = 1; VRN = 2; COV = 3; ENV = 4; CFL = 5 }
    while (@($lanes | Where-Object { -not $_.proc.HasExited }).Count -gt 0) {
        foreach ($ln in $lanes) {
            $el = [int]((Get-Date) - $ln.t0).TotalSeconds
            if ($ln.proc.HasExited) {
                $ln.pct = 100
                Write-Progress -Id $ids[$ln.id] -ParentId 0 -Activity $ln.title -Status ("完成 · " + $el + "s") -PercentComplete 100
                continue
            }
            $size = if (Test-Path -LiteralPath $ln.log) { (Get-Item -LiteralPath $ln.log).Length } else { 0 }
            if ($size -ne $ln.lastSize) { $ln.lastSize = $size; $ln.lastChange = Get-Date; $ln.warned = $false }
            $now = "起步中"
            if ($ln.progress) {
                $lines = Read-RtLog $ln.log
                $done = @($lines | Where-Object { $_ -match '^\[進度\] \w+ (\d+)/(\d+|\?) 完成 (.+)$' })
                $started = @($lines | Where-Object { $_ -match '^\[進度\] \w+ (?:\d+/(?:\d+|\?) )?開始 (.+)$' })
                $k = 0; $n = 0
                if ($done.Count) { if ($done[-1] -match '(\d+)/(\d+|\?) 完成') { $k = [int]$Matches[1]; if ($Matches[2] -ne '?') { $n = [int]$Matches[2] } } }
                if (-not $n -and $started.Count -and $started[-1] -match '(\d+)/(\d+) 開始') { $n = [int]$Matches[2] }
                if ($started.Count -and $started[-1] -match '開始 (.+)$') { $now = $Matches[1] }
                $ln.pct = if ($n -gt 0) { [Math]::Min(99, [int](100 * $k / $n)) } else { [Math]::Min(95, $el) }
                $status = ("{0}/{1} 站 · {2}% · 現在:{3} · 已 {4}s" -f $k, $(if ($n) { $n } else { "?" }), $ln.pct, $now, $el)
            } else {
                $ln.pct = [Math]::Min(95, [int](100 * $el / [Math]::Max(1, $ln.expect)))
                $status = ("{0} · 約 {1}% · 已 {2}s" -f $(if ($ln.id -eq "COV") { "掃描全樹(AST 第二讀法)" } elseif ($ln.id -eq "ENV") { "逐項委派正主檢查" } else { "八路衝突 + uv 計畫" }), $ln.pct, $el)
            }
            Write-Progress -Id $ids[$ln.id] -ParentId 0 -Activity $ln.title -Status $status -PercentComplete $ln.pct
            $idle = [int]((Get-Date) - $ln.lastChange).TotalSeconds
            if ($idle -ge $StallSec -and -not $ln.warned) {
                Write-Host ("  ⚠ " + $ln.title + " 已 " + $idle + " 秒沒有新輸出 · 目前在:" + $now + "(這站有自己的逾時,超時照實記 NODATA;不是當掉就別按 Ctrl+C)") -ForegroundColor Yellow
                $ln.warned = $true
            }
            if ($el -ge ($MaxMin * 60)) {
                Write-Host ("  ⛔ " + $ln.title + " 超過 " + $MaxMin + " 分鐘 · 看門狗停掉(TIMEOUT,不假綠)· 已收到的輸出在 " + $ln.log) -ForegroundColor Red
                try { $ln.proc.Kill($true) } catch { }
                $ln.timeout = $true
            }
        }
        $all = [int](($lanes | ForEach-Object { $_.pct } | Measure-Object -Average).Average)
        Write-Progress -Id 0 -Activity "via-realtest" -Status ("總進度 {0}% · 已 {1}s" -f $all, [int]$clock.Elapsed.TotalSeconds) -PercentComplete $all
        Start-Sleep -Milliseconds 700
    }
    foreach ($ln in $lanes) { $ln.proc.WaitForExit(); Write-Progress -Id $ids[$ln.id] -Activity $ln.title -Completed }
    Write-Progress -Id 0 -Activity "via-realtest" -Completed

    # 結果
    Write-Host ""
    Write-Host "  ═══ 結果 ═══" -ForegroundColor Cyan
    $worst = 0
    foreach ($ln in $lanes) {
        $rc = if ($ln.timeout) { 124 } else { $ln.proc.ExitCode }
        $lines = Read-RtLog $ln.log
        $tally = @($lines | Where-Object { $_ -match '\[計\] GREEN|\[工具覆蓋|覆蓋矩陣\]|\[ENV MANAGER\] 總判|\[八路衝突|總判|verdict' } | Select-Object -Last 1)
        $color = if ($rc -eq 0) { "Green" } elseif ($rc -in 2, 3, 4) { "Yellow" } else { "Red" }
        Write-Host ("  " + $ln.title.PadRight(28) + " rc " + $rc + " · " + [int]((Get-Date) - $ln.t0).TotalSeconds + "s · " + $(if ($tally.Count) { $tally[0].Trim() } else { "(看 log)" })) -ForegroundColor $color
        $bad = @($lines | Where-Object { $_ -match '^\s+\[(RED|ABSENT|GATED|NODATA)\s*\]|^\s+(RED|AMBER)\s+│|^\s+(BASE|FAMILY|DUP|PIN)\s+BLOCK' } | Select-Object -First 8)
        $bad | ForEach-Object { Write-Host ("      " + $_.Trim().Substring(0, [Math]::Min(150, $_.Trim().Length))) -ForegroundColor DarkGray }
        $sev = if ($rc -eq 0) { 0 } elseif ($rc -eq 124) { 124 } elseif ($rc -in 2, 3, 4) { 2 } else { 1 }
        if ($sev -eq 124 -or ($sev -eq 1 -and $worst -ne 124) -or ($sev -eq 2 -and $worst -eq 0)) { $worst = $sev }
    }
    $exitCode = $worst

    # 環境補強(只在 -FixEnv;照環境工具自己的邏輯,不另立一套)
    $envLane = $lanes | Where-Object { $_.id -eq "ENV" } | Select-Object -First 1
    $plan = Join-Path $Rep "env_governance\TOOLS_PLAN_latest.ps1"
    if ($envLane -and $envLane.proc.ExitCode -ne 0) {
        Write-Host ("  ⓔ 環境有缺(補法一貼即用:" + $plan + ";裝件是你的手)") -ForegroundColor Yellow
        if ($FixEnv) {
            if ($env:VIA_NET_CONSENT -ne "YES") {
                Write-Host "  ⓔ -FixEnv:要裝先在你的視窗打 `$env:VIA_NET_CONSENT='YES'(同意閘不代設)· 本輪只查不裝" -ForegroundColor Yellow
            } elseif (Get-Command via-envtools -ErrorAction SilentlyContinue) {
                Write-Host "  ⓔ -FixEnv:via-envtools -Apply -Approve(裝前 freeze 存證 · 順序安裝 · 同名獨立境)…" -ForegroundColor Cyan
                via-envtools -Apply -Approve
                $re = @(& $py $V.FullName run --family core CGC_MDL240_EnvManager check 2>&1 | ForEach-Object { "" + $_ })
                $re | Where-Object { $_ -match '\[ENV MANAGER\] 總判' } | ForEach-Object { Write-Host ("  ⓔ 補完再驗:" + $_.Trim()) -ForegroundColor Cyan }
            } else {
                Write-Host "  ⓔ -FixEnv:via-envtools 沒註冊(先 . .\VeritasIntelligenceAnalytics\Register-VIA-Commands-v*.ps1 尾版)· 本輪只查不裝" -ForegroundColor Yellow
            }
        }
    }

    # 總報告:VIA Panorama monitor(VCGC 全部控管項目)
    $pano = Get-RtNewest $Reg "VIA_Panorama_v*.py"
    if ($pano) {
        $pm = @(& $py $V.FullName run --family core $pano.FullName monitor 2>&1 | ForEach-Object { "" + $_ })
        $pm | Where-Object { $_ -match '^\[VIA_Panorama|^\s+(RED|YELLOW|GREEN|STALE|NODATA)\s' } | Select-Object -First 12 |
            ForEach-Object { Write-Host ("  ⓟ " + $_.Trim()) -ForegroundColor DarkGray }
    }

    # ⑤ 三合一矩陣頁 + 結果驗證頁
    $pages = @()
    $tplIn = Join-Path $VIA "VIA_HTML_UI\legacy\reference-templates\VIAHTMLUniversalUI-Standalone.html"
    $tri = Join-Path $Rep "template_adapter\synced\VIAHTMLUniversalUI_Standalone\VIA_UI_VIAHTMLUniversalUI_Standalone_latest.html"
    if ($adapter -and (Test-Path -LiteralPath $tplIn)) {
        $t1 = Get-Date
        $s = @(& $py $V.FullName run --family vrn $adapter.FullName sync --in $tplIn 2>&1 | ForEach-Object { "" + $_ })
        $s | Where-Object { $_ -match '\[模板同步\]' } | Select-Object -Last 1 | ForEach-Object { Write-Host ("  ⑤ " + $_.Trim()) -ForegroundColor DarkGray }
        if ((Test-Path -LiteralPath $tri) -and (Get-Item -LiteralPath $tri).LastWriteTime -ge $t1.AddSeconds(-1)) { $pages += $tri }
    }
    $pages = @((Join-Path $Rep "panorama\monitor_latest.html")) + $pages
    $pages += @((Join-Path $Rep "vdf_chain\VIA_VDF_Chain_Matrix_v0100.html"), (Join-Path $Rep "vrn_chain\VIA_VRN_Chain_Evidence_v0100.html"),
                (Join-Path $Rep "toolprobe\COVERAGE_MATRIX_latest.html"), (Join-Path $Rep "env_manager\ENVMGR_latest.html"))
    $pages = @($pages | Where-Object { Test-Path -LiteralPath $_ })
    Write-Host ("  ⑤ 報告頁 " + $pages.Count + " 張:全景監控(VCGC 控管)· 三合一矩陣 · VDF 鏈矩陣 · VRN 鏈證據 · 工具覆蓋 · 環境") -ForegroundColor Cyan
    $pages | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    if (-not $NoOpen) { Open-RtPages $pages }
    Write-Host ("  [via-realtest] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $exitCode + "(0 全綠 · 2 有發現 · 1 有紅 · 124 超時)") -ForegroundColor Cyan
} finally {
    foreach ($k in $envKeys) { [Environment]::SetEnvironmentVariable($k, $envSaved[$k], "Process") }
}
exit $exitCode
