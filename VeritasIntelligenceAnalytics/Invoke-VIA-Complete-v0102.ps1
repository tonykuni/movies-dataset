# =====================================================================
# Invoke-VIA-Complete-v0102.ps1 — 一鍵完工鏈 啟動器/工人(批340;操作員實錄「via-complete run 卡斷」;批343 工人守護;批344 Ctrl-C 免疫)
# v0101→v0102(批344 .py.err 實錄兩輪 KeyboardInterrupt=工人被 Ctrl-C 波及):工人 env VIA_CTRLC_IMMUNE=1(MDL121 v0104
#   忽略 Ctrl-C+子程序新程序群);-Foreground=0(同窗除錯要能 Ctrl-C);啟動器印停止法(via-complete stop)
# v0100→v0101(批343 工作站實錄「[FAIL] 工人進程提前退出(退出碼 0)」於 backfill 539s 而 python 仍在跑):
#   ①工人印「[工人PID] python=<pid>」;啟動器解析後,pwsh 包裝殼退出而 python 仍活=不判 FAIL,改直讀 .py.out 續播
#   ②真死=印 log 尾 25 行+.py.err 尾 15 行(根因可見;零猜測)
#   ③工人 trap:終止性錯誤亦寫「=== 畢」+原話;③b 步內進度由 MDL121 v0103 供(主條連續推進)
# =====================================================================
# 律(批319 不卡斷):啟動器/工人分離——本窗只派工+直播尾讀 log;鏈體在分離進程
#   (關窗不斷;Ctrl-C 只離開觀看,背景照跑)。工人=python CGC_MDL121 尾版 run(v0101 每 5s 心跳)。
#   -Foreground = 同窗阻塞(除錯);-Worker/-LogPath = 內部派工參數;其餘參數原樣轉給 MDL121
#   (例:--only revenue,revenue_groups / --skip-net)。
#   log:VIA_Reports/completion/LAUNCH_<stamp>.log(工人 stdout 全文;結束印「=== 畢」)。
# =====================================================================
param(
    [switch]$Foreground,
    [switch]$Worker,
    [string]$LogPath = "",
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest = @()
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
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONWARNINGS = "ignore:Unverified HTTPS request"
$UTF8 = New-Object System.Text.UTF8Encoding($false)
$VIA = $PSScriptRoot
$REG = Join-Path $VIA "supportive modules\registry"
$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$LOGDIR = Join-Path $VIA "VIA_Reports\completion"
if (-not (Test-Path $LOGDIR)) { New-Item -ItemType Directory -Path $LOGDIR -Force | Out-Null }
$LOG = if ($LogPath) { $LogPath } else { Join-Path $LOGDIR ("LAUNCH_" + $STAMP + ".log") }
$PY = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }
$PSEXE = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }

function Newest([string]$dir, [string]$pat) {
    (Get-ChildItem -Path $dir -Filter $pat -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1).FullName
}
function Say([string]$msg, [string]$color = "Gray") {
    Write-Host $msg -ForegroundColor $color
    try { Add-Content -Path $LOG -Value $msg -Encoding UTF8 } catch { }
}
function Read-NewText([string]$path, [ref]$pos) {
    if (-not (Test-Path $path)) { return "" }
    try {
        $fs = New-Object System.IO.FileStream($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            if ($fs.Length -le $pos.Value) { return "" }
            $fs.Seek($pos.Value, [System.IO.SeekOrigin]::Begin) | Out-Null
            $buf = New-Object byte[] ($fs.Length - $pos.Value)
            $n = $fs.Read($buf, 0, $buf.Length)
            $pos.Value += $n
            return $UTF8.GetString($buf, 0, $n)
        } finally { $fs.Dispose() }
    } catch { return "" }
}
$ENGINE = Newest $REG "CGC_MDL121_CompletionAutomator_v*.py"
if (-not $ENGINE) { Say "  [FAIL] CGC_MDL121 尾版缺(先 via-reload)" "Red"; exit 2 }

function Invoke-Chain {
    # 工人本體:python MDL121 run(心跳逐行)→stdout 直接落本 log(啟動器直播尾讀)
    $al = @(('"' + $ENGINE + '"'), "run") + $Rest
    Say ("  [工人] {0} {1}" -f $PY, ($al -join " ")) "DarkGray"
    $t0 = Get-Date
    $p = Start-Process -FilePath $PY -ArgumentList $al -NoNewWindow -PassThru -RedirectStandardOutput ($LOG + ".py.out") -RedirectStandardError ($LOG + ".py.err")
    Say ("  [工人PID] python=" + $p.Id + " pwsh=" + $PID) "DarkGray"
    $pos = 0
    while (-not $p.HasExited) {
        $txt = Read-NewText ($LOG + ".py.out") ([ref]$pos)
        if ($txt) { Write-Host $txt -NoNewline; try { Add-Content -Path $LOG -Value $txt.TrimEnd() -Encoding UTF8 } catch { } }
        Start-Sleep -Milliseconds 800
    }
    $txt = Read-NewText ($LOG + ".py.out") ([ref]$pos)
    if ($txt) { Write-Host $txt -NoNewline; try { Add-Content -Path $LOG -Value $txt.TrimEnd() -Encoding UTF8 } catch { } }
    try { $err = Get-Content ($LOG + ".py.err") -Raw -Encoding UTF8 -ErrorAction SilentlyContinue; if ($err -and $err.Trim()) { Say ("  [stderr] " + $err.Trim()) "Yellow" } } catch { }
    $sec = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    Say ("=== 畢(退出碼 {0};{1}s)===" -f $p.ExitCode, $sec) "White"
    return $p.ExitCode
}

if ($Worker) {
    $env:VIA_CTRLC_IMMUNE = "1"
    trap { Say ("  [工人 trap] " + $_.Exception.Message) "Red"; Say "=== 畢(退出碼 1;工人終止性錯誤)===" "White"; exit 1 }
    try { $host.UI.RawUI.WindowTitle = "VIA 一鍵完工工人 · $STAMP" } catch { }
    Say "=== [工人] 完工鏈開跑 · 分離進程 PID $PID ===" "White"
    try { $code = Invoke-Chain } catch { Say ("  [FAIL] 工人例外:" + $_.Exception.Message) "Red"; Say "=== 畢(退出碼 1;工人例外)===" "White"; $code = 1 }
    exit $code
}
if ($Foreground) {
    $env:VIA_CTRLC_IMMUNE = "0"
    Say "--- [前景] -Foreground:同窗阻塞跑完工鏈(除錯用;Ctrl-C 可中止)" "Cyan"
    exit (Invoke-Chain)
}
# ---------- 分離派工+直播尾讀(不卡斷) ----------
$wargs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"' + $PSCommandPath + '"'), "-Worker", "-LogPath", ('"' + $LOG + '"')) + $Rest
Say ("  [派工命令列] {0} {1}" -f $PSEXE, ($wargs -join " ")) "DarkGray"
try {
    $wp = Start-Process -FilePath $PSEXE -ArgumentList $wargs -WindowStyle Minimized -PassThru
    Say ("--- [背景] 完工鏈已派工:分離進程 PID {0}(關窗不斷;Ctrl-C 只離開觀看;心跳每 5s)" -f $wp.Id) "Cyan"
} catch {
    Say ("  [FAIL] 派工敗:" + $_.Exception.Message + " → 退前景同窗跑") "Red"
    exit (Invoke-Chain)
}
Say "--- [直播] 尾讀 log(結束自動收;Ctrl-C 只離開觀看=工人 Ctrl-C 免疫照跑;再看:via-complete watch;停止:via-complete stop)" "Cyan"
$pos = 0; $done = $false; $tStart = Get-Date
try { if (Test-Path $LOG) { $pos = (Get-Item $LOG).Length } } catch { }
while (-not $done -and (((Get-Date) - $tStart).TotalHours -lt 12)) {
    $txt = Read-NewText $LOG ([ref]$pos)
    if ($txt) { Write-Host $txt -NoNewline; if ($txt -match "=== 畢") { $done = $true } }
    if (-not $done -and $wp.HasExited) {
        $txt = Read-NewText $LOG ([ref]$pos); if ($txt) { Write-Host $txt -NoNewline; if ($txt -match "=== 畢") { $done = $true } }
        if ($done) { break }
        # 批343:pwsh 包裝殼退出≠工人死;查 python PID(工人自報)仍活→直讀 .py.out 續播
        $pyPid = 0
        try { $m = [regex]::Match((Get-Content -Path $LOG -Raw -Encoding UTF8 -ErrorAction SilentlyContinue), "\[工人PID\] python=(\d+)"); if ($m.Success) { $pyPid = [int]$m.Groups[1].Value } } catch { }
        $pyAlive = $false
        if ($pyPid) { try { $pyAlive = [bool](Get-Process -Id $pyPid -ErrorAction SilentlyContinue) } catch { } }
        if ($pyAlive) {
            Write-Host ("  [注意] pwsh 包裝殼已退(退出碼 {0})但 python 工人 PID {1} 仍在跑=改直讀 {2}.py.out 續播(不判 FAIL)" -f $wp.ExitCode, $pyPid, (Split-Path $LOG -Leaf)) -ForegroundColor Yellow
            $pos2 = 0
            try { if (Test-Path ($LOG + ".py.out")) { $pos2 = (Get-Item ($LOG + ".py.out")).Length } } catch { }
            while ((((Get-Date) - $tStart).TotalHours -lt 12) -and (Get-Process -Id $pyPid -ErrorAction SilentlyContinue)) {
                $t2 = Read-NewText ($LOG + ".py.out") ([ref]$pos2); if ($t2) { Write-Host $t2 -NoNewline }
                Start-Sleep -Milliseconds 800
            }
            $t2 = Read-NewText ($LOG + ".py.out") ([ref]$pos2); if ($t2) { Write-Host $t2 -NoNewline }
            Write-Host "=== 畢(python 工人已結束;退出碼見 .py.out 終態行)===" -ForegroundColor White
            $done = $true; break
        }
        Write-Host "  [FAIL] 工人進程提前退出(退出碼 $($wp.ExitCode));python 工人亦不在;見 log $LOG" -ForegroundColor Red
        try { Write-Host "  --- log 尾 25 行 ---" -ForegroundColor DarkGray; Get-Content -Path $LOG -Tail 25 -Encoding UTF8 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host ("  | " + $_) -ForegroundColor DarkGray } } catch { }
        try { if (Test-Path ($LOG + ".py.err")) { Write-Host "  --- .py.err 尾 15 行 ---" -ForegroundColor DarkGray; Get-Content -Path ($LOG + ".py.err") -Tail 15 -Encoding UTF8 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host ("  | " + $_) -ForegroundColor Yellow } } } catch { }
        Write-Host ("  [重現] 同窗跑:{0} {1} -Foreground" -f $PSEXE, (($wargs | Where-Object { $_ -ne "-Worker" }) -join " ")) -ForegroundColor Yellow
        break
    }
    Start-Sleep -Milliseconds 700
}
if ($done) { exit $(if ($wp.HasExited) { $wp.ExitCode } else { 0 }) } else { exit 1 }
