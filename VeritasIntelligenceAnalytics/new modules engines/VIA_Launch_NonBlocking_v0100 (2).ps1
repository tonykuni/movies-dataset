#requires -Version 7.0
param(
    [ValidateSet('Controller', 'EnvManager', 'Repair', 'Priority', 'Console')]
    [string]$Target        = 'Controller',
    [string]$ToolsDir      = 'C:\VeritasIntelligenceAnalytics\CGE\tools',
    [string]$Root          = 'C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics',
    [string]$EnvRoot       = 'C:\Users\tonyk\envs',
    [string]$WorkRoot      = 'C:\VeritasIntelligenceAnalytics\CGE\Launch',
    [string[]]$ExtraArgs   = @(),
    [int]$TimeoutMinutes   = 30,
    [int]$StallSeconds     = 45,
    [switch]$NoBrowser,
    [switch]$NoLiveHtml
)

# ============================================================
# VIA Non-Blocking Launcher v0100
#
# 解決三件事：不關閉、不阻塞、不卡斷。
#
#   不阻塞  子行程以「檔案重導向」啟動，父行程不佔用管道 ——
#           管道 + ReadToEnd 會在子行程輸出量大時死鎖（LL#26 那個坑）。
#   不卡斷  父行程每 250ms 讀取新增位元組，即時換算進度與敘述。
#           以 FileShare::ReadWrite 開檔，否則 Windows 會因為子行程
#           仍持有寫入鎖而讀不到。
#   不關閉  停滯偵測 + 看門狗。超過 StallSeconds 沒有新輸出就顯示
#           「仍在執行（已 Xs 無輸出）」，不會讓人以為當掉；
#           超過 TimeoutMinutes 才強制終止並留下證據。
#
# 加速器一律「偵測到才算」。偵測不到就標 ABSENT，不自動安裝、
# 不假裝啟用 —— 宣稱啟用了不存在的加速器，比沒有加速器更危險。
#
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>" -Target Controller
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$Script:Start = Get-Date

function Write-Utf8NoBom {
    param([string]$TargetPath, [string]$Text)
    $dir = Split-Path -Path $TargetPath -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($TargetPath, $Text, [System.Text.UTF8Encoding]::new($false))
}

function ConvertTo-HtmlText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

foreach ($sub in @('logs', 'out')) {
    $dir = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
}
$StdOutPath  = Join-Path $WorkRoot ('logs\worker_' + $Script:Stamp + '.out')
$StdErrPath  = Join-Path $WorkRoot ('logs\worker_' + $Script:Stamp + '.err')
$LiveHtml    = Join-Path $WorkRoot 'out\VIA_Live_Progress.html'
$FinalJson   = Join-Path $WorkRoot ('out\launch_' + $Script:Stamp + '.json')

# ------------------------------------------------------------
# 1. 加速器偵測（偵測到才算，不安裝、不假裝）
# ------------------------------------------------------------

function Test-Tool {
    param([string]$Name)
    $found = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $found) { return '' }
    return $found.Source
}

function Test-PyModule {
    param([string]$PythonExe, [string]$Module)
    if (-not $PythonExe) { return $false }
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $PythonExe
        $psi.Arguments = ('-c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec(''' + $Module + ''') else 1)"')
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        if (-not $proc.WaitForExit(8000)) { $proc.Kill($true); return $false }
        return ($proc.ExitCode -eq 0)
    } catch { return $false }
}

Write-Host ''
Write-Host '  VIA NON-BLOCKING LAUNCHER v0100' -ForegroundColor Cyan
Write-Host '  ------------------------------------------------------------' -ForegroundColor DarkGray
Write-Host '  偵測加速器（偵測不到就是 ABSENT，不自動安裝）' -ForegroundColor DarkGray

$pythonExe = Test-Tool -Name 'python'
if (-not $pythonExe) { $pythonExe = Test-Tool -Name 'python3' }
$pwshExe = Test-Tool -Name 'pwsh'

$accelerators = [System.Collections.Generic.List[object]]::new()
function Add-Accel {
    param([string]$Id, [string]$Name, [string]$State, [string]$Detail, [string]$Kind)
    $accelerators.Add([pscustomobject]@{ id = $Id; name = $Name; state = $State; detail = $Detail; kind = $Kind })
}

# 真實外部工具
Add-Accel 'A01' 'Python 執行期'       $(if ($pythonExe) { 'READY' } else { 'ABSENT' }) $pythonExe 'RUNTIME'
Add-Accel 'A02' 'PowerShell 7'        $(if ($pwshExe) { 'READY' } else { 'ABSENT' })   $pwshExe   'RUNTIME'
$uvExe = Test-Tool -Name 'uv'
Add-Accel 'A03' 'uv 依賴解析器'        $(if ($uvExe) { 'READY' } else { 'ABSENT' })     $uvExe     'EXTERNAL'
$ruffExe = Test-Tool -Name 'ruff'
Add-Accel 'A04' 'ruff 語法修復'        $(if ($ruffExe) { 'READY' } else { 'ABSENT' })   $ruffExe   'EXTERNAL'
$hasPssa = $null -ne (Get-Module -ListAvailable -Name PSScriptAnalyzer -ErrorAction SilentlyContinue)
Add-Accel 'A05' 'PSScriptAnalyzer'    $(if ($hasPssa) { 'READY' } else { 'ABSENT' })   ''         'EXTERNAL'
foreach ($pair in @(
    @('A06', 'polars 欄式引擎', 'polars'), @('A07', 'pyarrow 零拷貝', 'pyarrow'),
    @('A08', 'duckdb 查詢引擎', 'duckdb'), @('A09', 'pydantic 契約驗證', 'pydantic'),
    @('A10', 'rapidfuzz 模糊比對', 'rapidfuzz'), @('A11', 'psutil 資源監測', 'psutil'))) {
    $ok = Test-PyModule -PythonExe $pythonExe -Module $pair[2]
    Add-Accel $pair[0] $pair[1] $(if ($ok) { 'READY' } else { 'ABSENT' }) $pair[2] 'PYLIB'
}

# 已由本專案自有程式實作的能力（不需外部套件）
foreach ($pair in @(
    @('A12', 'AST 精準解析（py + ps1）', 'VIA_CentralGovernanceConsole / Round1Repair'),
    @('A13', '依賴拓撲排序（DFS 三色）', 'DownwardController.topological_levels'),
    @('A14', '九頭龍爆炸半徑', 'TopologyGuard.blast_radius'),
    @('A15', 'PEP 508 標記求值', 'EnvManager v0110 Test-Marker'),
    @('A16', '介面契約比對 G15', 'ContractGovernor.verify'),
    @('A17', '指紋回滾（零脫落）', 'Round1CodeRepair 指紋驗證'),
    @('A18', '檔案優先序路由', 'FilePriorityRouter'),
    @('A19', '非阻塞執行與進度條', '本啟動器'),
    @('A20', 'Visual Lock HTML 矩陣', '各引擎共用渲染器'))) {
    Add-Accel $pair[0] $pair[1] 'BUILTIN' $pair[1 + 1] 'INTERNAL'
}

$ready   = @($accelerators | Where-Object { $_.state -eq 'READY' }).Count
$builtin = @($accelerators | Where-Object { $_.state -eq 'BUILTIN' }).Count
$absent  = @($accelerators | Where-Object { $_.state -eq 'ABSENT' }).Count
foreach ($accel in $accelerators) {
    $color = 'DarkGray'
    if ($accel.state -eq 'READY')   { $color = 'Green' }
    if ($accel.state -eq 'BUILTIN') { $color = 'Cyan' }
    if ($accel.state -eq 'ABSENT')  { $color = 'DarkYellow' }
    Write-Host ('    ' + $accel.id + ' ' + $accel.name.PadRight(28) + $accel.state) -ForegroundColor $color
}
Write-Host ('  加速器：外部就緒 ' + $ready + '／內建 ' + $builtin + '／缺席 ' + $absent) -ForegroundColor DarkGray
Write-Host ''

# ------------------------------------------------------------
# 2. 決定要跑什麼
# ------------------------------------------------------------

$targets = @{
    'Controller' = @{ script = 'VIA_DownwardController.py'; runtime = 'python'
                      args = @('--root', $Root, '--tools', $ToolsDir, '--env-root', $EnvRoot, '--no-open') }
    'EnvManager' = @{ script = 'VIA_EnvManager_UnifiedGovernance_v0110.ps1'; runtime = 'pwsh'
                      args = @('-EnvRoot', $EnvRoot, '-WorkRoot', (Join-Path $WorkRoot 'EnvManager'), '-NoBrowser') }
    'Repair'     = @{ script = 'VIA_Round1_CodeRepair_v0100.ps1'; runtime = 'pwsh'
                      args = @('-Path', $Root, '-WorkRoot', (Join-Path $WorkRoot 'Repair'), '-DryRun', '-NoBrowser') }
    'Priority'   = @{ script = 'VIA_FilePriorityRouter.py'; runtime = 'python'
                      args = @('--root', $Root, '--out', (Join-Path $WorkRoot 'Priority'), '--no-open') }
    'Console'    = @{ script = 'VIA_CentralGovernanceConsole.py'; runtime = 'python'
                      args = @('--root', $Root, '--no-open') }
}
$plan = $targets[$Target]
$scriptPath = Join-Path $ToolsDir $plan.script
if (-not (Test-Path -LiteralPath $scriptPath)) {
    $hit = @(Get-ChildItem -LiteralPath $ToolsDir -Recurse -Filter $plan.script -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($hit.Count -gt 0) { $scriptPath = $hit[0].FullName }
}
if (-not (Test-Path -LiteralPath $scriptPath)) {
    Write-Host ('  找不到目標腳本：' + $plan.script + '（於 ' + $ToolsDir + '）') -ForegroundColor Red
    return
}

$runner = $pwshExe
$argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptPath) + $plan.args + $ExtraArgs
if ($plan.runtime -eq 'python') {
    $runner = $pythonExe
    $argList = @($scriptPath) + $plan.args + $ExtraArgs
}
if (-not $runner) {
    Write-Host ('  缺少執行期：' + $plan.runtime) -ForegroundColor Red
    return
}

Write-Host ('  目標：' + $Target + '  ->  ' + $plan.script) -ForegroundColor White
Write-Host ('  逾時：' + $TimeoutMinutes + ' 分鐘  ｜  停滯提示：' + $StallSeconds + ' 秒') -ForegroundColor DarkGray
Write-Host ''

# ------------------------------------------------------------
# 3. 非阻塞啟動：重導向到檔案，不佔用管道
# ------------------------------------------------------------

Write-Utf8NoBom -TargetPath $StdOutPath -Text ''
Write-Utf8NoBom -TargetPath $StdErrPath -Text ''

# 用檔案重導向而不是管道：管道 + ReadToEnd 在輸出量大時會死鎖。
$proc = Start-Process -FilePath $runner -ArgumentList $argList `
    -RedirectStandardOutput $StdOutPath -RedirectStandardError $StdErrPath `
    -NoNewWindow -PassThru

# ------------------------------------------------------------
# 4. 即時追蹤：進度條 + 情境敘述 + 停滯偵測
# ------------------------------------------------------------

$offset = 0L
$percent = 0
$lastPercent = 0
$stage = '啟動中'
$lastLineAt = Get-Date
$lines = [System.Collections.Generic.List[string]]::new()
$errorLines = [System.Collections.Generic.List[string]]::new()
$stalled = $false
$stallReported = $false
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$killed = $false
$lastHtml = [DateTime]::MinValue

function Read-NewText {
    param([string]$Path, [ref]$Offset)
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    try {
        # FileShare::ReadWrite 是關鍵：子行程還握著寫入鎖，
        # 沒有這個旗標在 Windows 上會讀不到而誤判成沒有輸出。
        $stream = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    } catch { return '' }
    try {
        if ($stream.Length -le $Offset.Value) { return '' }
        $null = $stream.Seek($Offset.Value, [System.IO.SeekOrigin]::Begin)
        $count = [int]($stream.Length - $Offset.Value)
        $buffer = [byte[]]::new($count)
        $read = $stream.Read($buffer, 0, $count)
        $Offset.Value = $Offset.Value + $read
        return [System.Text.Encoding]::UTF8.GetString($buffer, 0, $read)
    } finally { $stream.Dispose() }
}

$spinner = @('|', '/', '-', '\')
$spin = 0

while (-not $proc.HasExited) {
    $chunk = Read-NewText -Path $StdOutPath -Offset ([ref]$offset)
    if ($chunk) {
        $lastLineAt = Get-Date
        $stalled = $false
        $stallReported = $false
        foreach ($line in ($chunk -split "`r?`n")) {
            if (-not $line.Trim()) { continue }
            $lines.Add($line)
            # 子引擎自報進度：PROGRESS|pct|msg
            $m = [regex]::Match($line, '^PROGRESS\|(\d+)\|(.*)$')
            if ($m.Success) {
                $percent = [int]$m.Groups[1].Value
                $stage = $m.Groups[2].Value
                continue
            }
            # 一般日誌：[時間][等級] 訊息
            $m2 = [regex]::Match($line, '^\[\d{2}:\d{2}:\d{2}\]\[(\w+)\]\s*(.+)$')
            if ($m2.Success) {
                $level = $m2.Groups[1].Value
                $stage = $m2.Groups[2].Value
                if ($percent -lt 95) { $percent = [math]::Min(95, $percent + 2) }
                $color = 'Gray'
                if ($level -eq 'OK')   { $color = 'Green' }
                if ($level -eq 'WARN') { $color = 'Yellow' }
                if ($level -eq 'FAIL') { $color = 'Red' }
                Write-Host ('    ' + $line) -ForegroundColor $color
                continue
            }
            Write-Host ('    ' + $line) -ForegroundColor DarkGray
        }
    }

    $silent = [int]((Get-Date) - $lastLineAt).TotalSeconds
    if ($silent -ge $StallSeconds) {
        $stalled = $true
        if (-not $stallReported) {
            Write-Host ('    [仍在執行] 已 ' + $silent + ' 秒沒有新輸出 —— 這通常是大量檔案雜湊或網路探測，不是當掉') -ForegroundColor DarkYellow
            $stallReported = $true
        }
    }

    $spin = ($spin + 1) % 4
    $elapsed = [int]((Get-Date) - $Script:Start).TotalSeconds
    $eta = ''
    if ($percent -gt 5 -and $percent -lt 100) {
        $estimate = [int](($elapsed / $percent) * (100 - $percent))
        $eta = '，預估剩餘 ' + $estimate + 's'
    }
    $status = $spinner[$spin] + ' ' + $stage
    if ($stalled) { $status = $status + ' （已 ' + $silent + 's 無輸出）' }
    Write-Progress -Activity ('VIA ' + $Target + ' 執行中  已 ' + $elapsed + 's' + $eta) `
        -Status $status -PercentComplete ([math]::Min(99, $percent))

    if (-not $NoLiveHtml -and ((Get-Date) - $lastHtml).TotalSeconds -ge 2) {
        $lastHtml = Get-Date
        $tail = @($lines | Select-Object -Last 60)
        $liveRows = ''
        foreach ($accel in $accelerators) {
            $cls = 'muted'
            if ($accel.state -eq 'READY') { $cls = 'ok' }
            if ($accel.state -eq 'BUILTIN') { $cls = 'built' }
            if ($accel.state -eq 'ABSENT') { $cls = 'warn' }
            $liveRows += '<tr><td>' + $accel.id + '</td><td>' + (ConvertTo-HtmlText -Text $accel.name) +
                         '</td><td class="' + $cls + '">' + $accel.state + '</td></tr>'
        }
        $live = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="2">
<title>VIA Live Progress</title><style>
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
body{margin:0;padding:20px 24px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px}
.seal{display:inline-flex;width:36px;height:36px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:20px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:15px;letter-spacing:.14em;text-transform:uppercase;margin:9px 0 3px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.bar{height:16px;background:var(--panel);border:1px solid var(--line);border-radius:3px;overflow:hidden;margin:10px 0}
.fill{height:100%;background:var(--green);width:${percent}%;transition:width .4s}
.fill.stall{background:var(--amber)}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed;margin-top:8px}
th,td{border-bottom:1px solid #ececed;padding:4px 7px;text-align:left;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}
.built{color:#3a5f8a;font-weight:600}.muted{color:#9a9c9e}
pre{background:var(--panel);border:1px solid var(--line);padding:10px;font-size:11px;white-space:pre-wrap;max-height:46vh;overflow:auto}
</style></head><body>
<div class="seal">動</div>
<h1>Live Progress — $Target</h1>
<p class="lede">$($Script:Stamp) · 已執行 ${elapsed}s · $(ConvertTo-HtmlText -Text $stage)$(if ($stalled) { '（已 ' + $silent + 's 無輸出，仍在執行）' })</p>
<div class="bar"><div class="fill$(if ($stalled) { ' stall' })"></div></div>
<table><colgroup><col style="width:10%"><col style="width:65%"><col style="width:25%"></colgroup>
<tr><th>ID</th><th>加速器</th><th>狀態</th></tr>$liveRows</table>
<h1 style="font-size:13px;margin-top:18px">即時輸出</h1>
<pre>$(ConvertTo-HtmlText -Text ($tail -join "`n"))</pre>
</body></html>
"@
        try { Write-Utf8NoBom -TargetPath $LiveHtml -Text $live } catch { }
        if ($elapsed -le 3 -and -not $NoBrowser) {
            try { Start-Process -FilePath $LiveHtml | Out-Null } catch { }
        }
    }

    if ((Get-Date) -gt $deadline) {
        Write-Host ('    [看門狗] 超過 ' + $TimeoutMinutes + ' 分鐘，終止子行程') -ForegroundColor Red
        try { $proc.Kill($true) } catch { }
        $killed = $true
        break
    }
    Start-Sleep -Milliseconds 250
}

# 收尾：把殘餘輸出讀乾淨
$chunk = Read-NewText -Path $StdOutPath -Offset ([ref]$offset)
foreach ($line in ($chunk -split "`r?`n")) {
    if ($line.Trim()) { $lines.Add($line); Write-Host ('    ' + $line) -ForegroundColor Gray }
}
if (Test-Path -LiteralPath $StdErrPath) {
    foreach ($line in (Get-Content -LiteralPath $StdErrPath -ErrorAction SilentlyContinue)) {
        if ($line.Trim()) { $errorLines.Add($line) }
    }
}

Write-Progress -Activity ('VIA ' + $Target) -Completed
$elapsed = [int]((Get-Date) - $Script:Start).TotalSeconds
$exitCode = -1
if (-not $killed) { try { $exitCode = $proc.ExitCode } catch { $exitCode = -1 } }

$verdict = 'UNKNOWN'
foreach ($line in $lines) {
    $m = [regex]::Match($line, '->\s+(GREEN|AMBER|RED)\s*$')
    if ($m.Success) { $verdict = $m.Groups[1].Value }
}
if ($killed) { $verdict = 'TIMEOUT' }
elseif ($verdict -eq 'UNKNOWN' -and $exitCode -eq 0) { $verdict = 'GREEN' }
elseif ($verdict -eq 'UNKNOWN') { $verdict = 'RED' }

$snapshot = [ordered]@{
    launcher = 'VIA_NonBlocking_Launcher'; version = 'v0100'; stamp = $Script:Stamp
    target = $Target; script = $scriptPath; runtime = $plan.runtime
    elapsed_seconds = $elapsed; exit_code = $exitCode; killed = $killed
    verdict = $verdict; stdout = $StdOutPath; stderr = $StdErrPath
    accelerators = @($accelerators)
    accelerator_summary = [ordered]@{ ready = $ready; builtin = $builtin; absent = $absent }
    error_tail = @($errorLines | Select-Object -Last 10)
}
Write-Utf8NoBom -TargetPath $FinalJson -Text ($snapshot | ConvertTo-Json -Depth 6)

$color = 'Green'
if ($verdict -eq 'AMBER') { $color = 'Yellow' }
if ($verdict -eq 'RED' -or $verdict -eq 'TIMEOUT') { $color = 'Red' }
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor DarkGray
Write-Host ('   ' + $Target + '  ->  ' + $verdict + '   （' + $elapsed + 's，exit ' + $exitCode + '）') -ForegroundColor $color
Write-Host ('   stdout : ' + $StdOutPath) -ForegroundColor DarkCyan
if ($errorLines.Count -gt 0) {
    Write-Host ('   stderr : ' + $StdErrPath + '（' + $errorLines.Count + ' 行）') -ForegroundColor DarkYellow
}
Write-Host ('   摘要   : ' + $FinalJson) -ForegroundColor DarkCyan
Write-Host ('   即時頁 : ' + $LiveHtml) -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkGray

# 子引擎自己產的報告：挑最新的一份開起來
if (-not $NoBrowser) {
    $reportDirs = @((Join-Path $WorkRoot 'EnvManager\out'), (Join-Path $WorkRoot 'Repair\out'),
                    (Join-Path $WorkRoot 'Priority'), (Join-Path $Root '_governance\out'),
                    (Join-Path $Root 'output\SYS'))
    $newest = $null
    foreach ($dir in $reportDirs) {
        if (-not (Test-Path -LiteralPath $dir)) { continue }
        $hit = @(Get-ChildItem -LiteralPath $dir -Filter '*.html' -ErrorAction SilentlyContinue |
            Sort-Object -Property @{ e = 'LastWriteTime'; desc = $true } | Select-Object -First 1)
        if ($hit.Count -eq 0) { continue }
        if ($null -eq $newest -or $hit[0].LastWriteTime -gt $newest.LastWriteTime) { $newest = $hit[0] }
    }
    if ($null -ne $newest) {
        try { Start-Process -FilePath $newest.FullName | Out-Null } catch { }
    }
}
