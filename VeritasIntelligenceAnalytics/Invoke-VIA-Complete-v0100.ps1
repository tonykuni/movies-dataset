# =====================================================================
# Invoke-VIA-Complete-v0100.ps1 — 一鍵完工鏈 啟動器/工人(批340;操作員實錄「via-complete run 卡斷」)
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
    $host.UI.RawUI.WindowTitle = "VIA 一鍵完工工人 · $STAMP"
    Say "=== [工人] 完工鏈開跑 · 分離進程 PID $PID ===" "White"
    try { $code = Invoke-Chain } catch { Say ("  [FAIL] 工人例外:" + $_.Exception.Message) "Red"; Say "=== 畢(退出碼 1;工人例外)===" "White"; $code = 1 }
    exit $code
}
if ($Foreground) {
    Say "--- [前景] -Foreground:同窗阻塞跑完工鏈(除錯用)" "Cyan"
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
Say "--- [直播] 尾讀 log(結束自動收;隨時 Ctrl-C 離開,再看:Get-Content -Wait '$LOG')" "Cyan"
$pos = 0; $done = $false; $tStart = Get-Date
try { if (Test-Path $LOG) { $pos = (Get-Item $LOG).Length } } catch { }
while (-not $done -and (((Get-Date) - $tStart).TotalHours -lt 12)) {
    $txt = Read-NewText $LOG ([ref]$pos)
    if ($txt) { Write-Host $txt -NoNewline; if ($txt -match "=== 畢") { $done = $true } }
    if (-not $done -and $wp.HasExited) {
        $txt = Read-NewText $LOG ([ref]$pos); if ($txt) { Write-Host $txt -NoNewline }
        if (-not ($txt -match "=== 畢")) {
            Write-Host "  [FAIL] 工人進程提前退出(退出碼 $($wp.ExitCode));見 log $LOG" -ForegroundColor Red
            Write-Host ("  [重現] 同窗跑:{0} {1} -Foreground" -f $PSEXE, (($wargs | Where-Object { $_ -ne "-Worker" }) -join " ")) -ForegroundColor Yellow
        }
        break
    }
    Start-Sleep -Milliseconds 700
}
if ($done) { exit $(if ($wp.HasExited) { $wp.ExitCode } else { 0 }) } else { exit 1 }
