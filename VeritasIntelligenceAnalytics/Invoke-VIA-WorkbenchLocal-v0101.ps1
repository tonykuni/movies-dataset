#Requires -Version 7.0
<#
.SYNOPSIS
    VIA WorkbenchLocal v0101 — 一支 PS 搞定:進專案環境 → 加速器 → 取碼 → 網路工具 → 自測 → 出頁 → Playwright → Graphify → DuckDB → VCGC → MCP(不卡段 · 動態進度)

.DESCRIPTION
    操作員 2026-11-10:「INTEGRATE ALL OF ABOVE INTO ONE PS CODE TO HANDLE ALL · 第一行先進入專案環境 · PS/PY 都要導入加速器 ·
    抓資料檔案都要導入網路工具 · 現在的 PS/PY 檔也是一樣 · 不卡段 · 動態進度條 · 不動就是指令壞了」。v0100 留作版史(L04)。

    ① 第一個動作 = 進專案環境:找本機倉(-Repo → $env:VIA_REPO → $env:VRN2_ROOT 的上層 → OneDrive\Documents\movies-dataset →
       Documents\movies-dataset → $HOME\movies-dataset),Set-Location 進去並設 VIA_FROM_VCGC · PYTHONUTF8 · PYTHONUNBUFFERED;
       專案 .venv 在就用它的 python,否則 py -3。本機倉**只讀**:不切分支、不 stash、不 pull,你的工作樹一根不碰。
    ② 加速器:PS = L103 標準模板 [VIA:PS-TEMPLATE](腳本單獨放時改從專案倉載同一支 Celeritas PS7)+ PS-ACCEL 橋;
       PY = 每支子程式自帶 [VIA:ACCEL-BRIDGE](上傳整合器 v0102 起補上)。
    ③ 取碼:本分支的新件放在 $HOME\VIA_Workbench_Local\movies-dataset(專用稀疏副本,~1 MB;git 自帶傳輸 · 重試 2/4/8 s)。
    ④ 網路工具:先跑 SUP_MDL740_NetUnified 尾版自測;-FetchUrl 的資料檔一律經 VIA_NetFetch → NetUnified.http_bytes
       (AegisNexus · 雙閘由網路工具判,本腳本永不代設 VIA_NET_CONSENT)。
    ⑤ 自測 → 出頁(上傳整合 · 鎖定 U/I)→ Playwright 實測出好的頁 → Graphify 車道 → DuckDB 湖矩陣 → VCGC 唯讀(token · tools)→ MCP。

    不卡段:每一步都是子行程,非同步讀輸出;逾時只殺那一步(含子孫行程),其餘照跑。
    動態進度:總條 + 本步條(Write-Progress)+ 同一行即時重畫(轉輪 · 已跑秒 · 距上次輸出秒 · 內層 %)。內層 % 來源:
       @@PROGRESS|<pct>|<msg>(PY 端協定)· git 的「NN%」;都沒有就標「估」(依逾時粗估,封頂 95%)。
       導向成逐字稿時改成每 10 秒一行。超過 -StallWarnSec 沒有任何輸出 → 黃字點名(還活著 · PID · 等到逾時才殺)。
       轉輪不轉 = 腳本本身卡住;轉輪在轉但「距上次輸出」一直漲 = 子程式沒在吐東西(看黃字)。

.NOTES
    紅線:不代設網路同意閘 · 不代裝套件 · 不改 .ps1 以外的他系統檔 · 不碰 VRN-1(tonykuni/VIA-VDF-VRN)· 不發號(L125)。
    結束碼:0 綠 · 1 紅 · 2 黃(黃不是綠)。逐步 log 與收據在 <Out>\_runs\<時間>\。
#>
[CmdletBinding()]
param(
    [string]$Repo = '',
    [string]$KitRoot = (Join-Path $HOME 'VIA_Workbench_Local'),
    [string]$RepoUrl = 'https://github.com/tonykuni/movies-dataset.git',
    [string]$Branch = 'claude/practical-pasteur-p67i78',
    [string]$Downloads = (Join-Path $HOME 'Downloads'),
    [string]$Out = (Join-Path (Join-Path $HOME 'Downloads') 'VIA_Uploads_Workbench'),
    [string[]]$FetchUrl = @(),
    [string[]]$FetchSha = @(),
    [string]$Only = '',
    [ValidateRange(10, 3600)][int]$StallWarnSec = 60,
    [switch]$Serve,
    [ValidateRange(1024, 65535)][int]$Port = 8765,
    [switch]$ActivateMcp,
    [switch]$NoOpen,
    [switch]$ProgressLines
)
# ===== [第一行 · 進入專案環境] 找本機倉 → Set-Location → 專案變數(只讀;不切分支 · 不 stash · 不 pull) =====
$StartDir = (Get-Location).Path
$RepoCand = @($Repo, $env:VIA_REPO, $(if ($env:VRN2_ROOT) { Split-Path $env:VRN2_ROOT -Parent }),
    (Join-Path $HOME 'OneDrive\Documents\movies-dataset'), (Join-Path $HOME 'Documents\movies-dataset'), (Join-Path $HOME 'movies-dataset'))
$Repo = $RepoCand | Where-Object { $_ -and (Test-Path -LiteralPath (Join-Path $_ 'VeritasIntelligenceAnalytics')) } | Select-Object -First 1
$RepoVIA = if ($Repo) { Join-Path $Repo 'VeritasIntelligenceAnalytics' } else { $null }
New-Item -ItemType Directory -Path $KitRoot -Force | Out-Null
Set-Location -LiteralPath $(if ($Repo) { $Repo } else { $KitRoot })
$env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUNBUFFERED = '1'
if ($RepoVIA) { $env:VIA_ROOT = $RepoVIA }
# ===== [第一行 · END] =====
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        # v0101:腳本單獨放(例:下載夾)時,改從剛進入的專案倉載同一支正主
        if (-not $VIACelTplFile -and $RepoVIA) {
            $VIACelTplTry = Join-Path $RepoVIA 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry }
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
$VIAPSAccelLoaded = $false
try {
    foreach ($VIAPSAccelProbe in @($PSScriptRoot, $RepoVIA)) {
        while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
            $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
            if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; $VIAPSAccelLoaded = $true; break }
            $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
        }
        if ($VIAPSAccelLoaded) { break }
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = 'Stop'
$SelfVer = 'v0101'
$RunStamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$RunDir = Join-Path (Join-Path $Out '_runs') $RunStamp
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
$Rows = [System.Collections.Generic.List[object]]::new()
$script:Tty = (-not [Console]::IsOutputRedirected) -and (-not $ProgressLines)
$script:TotalSteps = 20
$script:Spin = @('|', '/', '-', '\')

function Write-Line([string]$Text, [string]$Colour = 'Gray') { Write-Host $Text -ForegroundColor $Colour }
function Add-Row([string]$Step, [string]$State, [string]$Why, [double]$Sec = 0, [string]$Log = '') {
    $Rows.Add([pscustomobject]@{ 步驟 = $Step; 燈 = $State; 秒 = [math]::Round($Sec, 1); 說明 = $Why; Log = $Log })
    $c = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; SKIP = 'DarkGray' }[$State]; if (-not $c) { $c = 'Gray' }
    Write-Line ("  [{0}] {1} · {2}" -f $State, $Step, $Why) $c
}
function Test-Want([string]$Name) {
    if (-not $Only) { return $true }
    $keys = @($Only.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
    return [bool]($keys | Where-Object { $Name.ToLower().Contains($_) })
}
function Get-Newest([string]$Folder, [string]$Pattern) {
    if (-not $Folder -or -not (Test-Path -LiteralPath $Folder)) { return $null }
    $hit = Get-ChildItem -LiteralPath $Folder -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($hit) { return $hit.FullName } else { return $null }
}
function Clear-ProgLine { if ($script:Tty) { try { Write-Host ("`r" + (' ' * ([Console]::WindowWidth - 1)) + "`r") -NoNewline } catch { } } }

function Invoke-Step {
    # 一步 = 一個子行程:非同步讀 stdout/stderr · 解析進度 · 轉輪 · 沉默警告 · 逾時只殺本步
    param([string]$Name, [string]$Exe, [string[]]$ArgList = @(), [int]$TimeoutSec = 300, [string]$Cwd = '', [switch]$Git, [switch]$RcOnly)
    if (-not (Test-Want $Name)) { Add-Row $Name 'SKIP' "-Only $Only"; return $null }
    $log = Join-Path $RunDir (($Name -replace '[^\w\-]', '_') + '.log')
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $lines = [System.Collections.Generic.List[string]]::new()
    $inner = $null; $innerMsg = ''; $lastOut = Get-Date; $lastBeat = [datetime]::MinValue; $stallWarned = 0
    $shown = 0; $hidden = 0; $killed = $false; $code = $null
    Write-Line ("`n=== {0} === (逾時 {1}s)" -f $Name, $TimeoutSec) 'Cyan'
    try {
        $info = [System.Diagnostics.ProcessStartInfo]::new()
        $info.FileName = $Exe
        $info.WorkingDirectory = $(if ($Cwd) { $Cwd } else { (Get-Location).Path })
        $info.UseShellExecute = $false
        $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
        $info.StandardOutputEncoding = [Text.Encoding]::UTF8; $info.StandardErrorEncoding = [Text.Encoding]::UTF8
        foreach ($a in $ArgList) { $info.ArgumentList.Add([string]$a) }
        $proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $info
        if (-not $proc.Start()) { throw '子行程啟動失敗' }
        $streams = @($proc.StandardOutput, $proc.StandardError)
        $tasks = @($streams[0].ReadLineAsync(), $streams[1].ReadLineAsync())
        $tick = 0
        while (-not $proc.HasExited -or $null -ne $tasks[0] -or $null -ne $tasks[1]) {
            $got = $false
            for ($i = 0; $i -lt 2; $i++) {
                if ($null -ne $tasks[$i] -and $tasks[$i].IsCompleted) {
                    $line = $tasks[$i].GetAwaiter().GetResult()
                    if ($null -eq $line) { $tasks[$i] = $null; continue }
                    $got = $true; $lastOut = Get-Date; $stallWarned = 0
                    $lines.Add($line); Add-Content -LiteralPath $log -Value $line -Encoding utf8
                    if ($line -match '^\s*@@PROGRESS\|([0-9.]+)\|(.*)$') { $inner = [double]$Matches[1]; $innerMsg = $Matches[2].Trim() }
                    elseif ($Git -and $line -match '(\d{1,3})%') { $inner = [double]$Matches[1]; $innerMsg = ($line -replace '\s+', ' ').Trim() }
                    elseif ($line.Trim()) {
                        $loud = $line -match '(?i)\b(RED|FAIL|ERROR|Traceback|Exception|TIMEOUT|DENY)\b'
                        if ($shown -lt 12 -or $loud) { Clear-ProgLine; Write-Host ("    " + $line); $shown++ } else { $hidden++ }
                    }
                    $tasks[$i] = $streams[$i].ReadLineAsync()
                }
            }
            $el = $timer.Elapsed.TotalSeconds
            if (-not $killed -and $el -gt $TimeoutSec) {
                $killed = $true; try { $proc.Kill($true) } catch { }
                Clear-ProgLine; Write-Line ("    [TIMEOUT] 超過 {0}s,殺掉本步子行程(含子孫),繼續下一步" -f $TimeoutSec) 'Red'
            }
            $quiet = ((Get-Date) - $lastOut).TotalSeconds
            if ($quiet -ge $StallWarnSec * ($stallWarned + 1)) {
                $stallWarned++
                Clear-ProgLine
                Write-Line ("    [沉默] {0:N0}s 沒有任何輸出 · 子行程還活著(PID {1})· 到 {2}s 逾時才殺" -f $quiet, $proc.Id, $TimeoutSec) 'Yellow'
            }
            $pct = if ($null -ne $inner) { [math]::Min(100, $inner) } else { [math]::Min(95, 100.0 * $el / [math]::Max(1, $TimeoutSec)) }
            $est = if ($null -ne $inner) { '' } else { '估' }
            $overall = [math]::Min(100, [int](100.0 * ($Rows.Count + $pct / 100.0) / $script:TotalSteps))
            $tick++
            $sp = $script:Spin[$tick % 4]
            $msg = if ($innerMsg) { $innerMsg } elseif ($lines.Count) { $lines[$lines.Count - 1] } else { '啟動中' }
            Write-Progress -Id 1 -Activity "VIA WorkbenchLocal $SelfVer" -Status ("總進度 {0}% · 已完成 {1}/{2} 步" -f $overall, $Rows.Count, $script:TotalSteps) -PercentComplete $overall
            Write-Progress -Id 2 -ParentId 1 -Activity $Name -Status ("{0} {1:N0}s · 距上次輸出 {2:N0}s · {3}" -f $sp, $el, $quiet, ($msg -replace '\s+', ' ')) -PercentComplete ([int]$pct)
            if ($script:Tty) {
                $txt = ("  {0} {1} {2,5:N1}%{3} · {4:N0}s · 距上次輸出 {5:N0}s · {6}" -f $sp, $Name, $pct, $est, $el, $quiet, ($msg -replace '\s+', ' '))
                try { $w = [Console]::WindowWidth - 1 } catch { $w = 120 }
                if ($txt.Length -gt $w) { $txt = $txt.Substring(0, [math]::Max(10, $w)) }
                Write-Host ("`r" + $txt.PadRight($w)) -NoNewline -ForegroundColor DarkCyan
            }
            elseif (((Get-Date) - $lastBeat).TotalSeconds -ge 10) {
                $lastBeat = Get-Date
                Write-Line ("    [進度] {0} {1:N1}%{2} · {3:N0}s · 距上次輸出 {4:N0}s · {5}" -f $Name, $pct, $est, $el, $quiet, ($msg -replace '\s+', ' ')) 'DarkCyan'
            }
            if (-not $got) { Start-Sleep -Milliseconds 200 }
        }
        $proc.WaitForExit(); $code = $proc.ExitCode
    }
    catch { $lines.Add("例外:" + $_.Exception.Message); Write-Line ("    例外:" + $_.Exception.Message) 'Red' }
    Clear-ProgLine
    Write-Progress -Id 2 -Activity $Name -Completed
    $sec = $timer.Elapsed.TotalSeconds
    $lamp = $null
    for ($k = $lines.Count - 1; $k -ge 0 -and -not $RcOnly; $k--) {
        if ($lines[$k] -match '"lamp":\s*"(GREEN|YELLOW|RED|NODATA)"') { $lamp = $Matches[1]; break }
    }
    if ($lamp -eq 'NODATA') { $lamp = 'YELLOW' }
    if ($killed) { $state = 'RED'; $why = "TIMEOUT {0}s" -f $TimeoutSec }
    elseif ($null -eq $code) { $state = 'RED'; $why = '沒跑起來' }
    elseif ($lamp) { $state = $lamp; $why = "rc $code · 燈 $lamp" }
    else { $state = $(if ($code -eq 0) { 'GREEN' } else { 'RED' }); $why = "rc $code" }
    $tail = ($lines | Where-Object { $_ -and $_ -notmatch '^\s*@@PROGRESS' } | Select-Object -Last 1)
    if ($tail) { $why += " · " + (($tail -replace '\s+', ' ').Trim()) }
    if ($hidden) { $why += " · 另 $hidden 行在 log" }
    if ($why.Length -gt 220) { $why = $why.Substring(0, 220) + '…' }
    Add-Row $Name $state $why $sec $log
    return [pscustomobject]@{ State = $state; Code = $code; Lines = $lines }
}
function Invoke-Py([string]$Name, [string]$File, [string[]]$ArgList = @(), [int]$TimeoutSec = 300, [string]$Cwd = '', [switch]$RcOnly) {
    if (-not (Test-Want $Name)) { Add-Row $Name 'SKIP' "-Only $Only"; return $null }
    if (-not $File -or -not (Test-Path -LiteralPath $File)) { Add-Row $Name 'YELLOW' ("ABSENT:檔不在(" + $File + ")"); return $null }
    return Invoke-Step -Name $Name -Exe $script:PyExe -ArgList (@($script:PyPre) + @('-u', $File) + $ArgList) -TimeoutSec $TimeoutSec -Cwd $Cwd -RcOnly:$RcOnly
}

$rc = 0
try {
    Write-Line ("VIA WorkbenchLocal {0} · PS {1} · {2}" -f $SelfVer, $PSVersionTable.PSVersion, (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) 'White'

    # S01 進入專案環境(第一行已做,這裡記錄 + 選 Python)
    $venvPy = if ($Repo) { @((Join-Path $Repo '.venv\Scripts\python.exe'), (Join-Path $RepoVIA '.venv\Scripts\python.exe')) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1 }
    if ($venvPy) { $script:PyExe = $venvPy; $script:PyPre = @('-B') }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $script:PyExe = (Get-Command py).Source; $script:PyPre = @('-3', '-B') }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $script:PyExe = (Get-Command python).Source; $script:PyPre = @('-B') }
    else { Add-Row 'S01 進入專案環境' 'RED' '找不到 Python(py / python / .venv)'; $rc = 1; throw [OperationCanceledException]::new('stop') }
    Add-Row 'S01 進入專案環境' $(if ($Repo) { 'GREEN' } else { 'YELLOW' }) ($(if ($Repo) { "專案倉 $Repo(只讀)" } else { "沒找到本機倉 → 只用稀疏套件($KitRoot);DuckDB / VCGC 唯讀步會略過" }) + " · Python " + $script:PyExe)

    # S02 加速器
    $accel = @()
    $accel += $(if ($VIACelTplOwn) { 'PS 模板 Celeritas PS7 已啟動' } elseif (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore) { 'Celeritas PS7 已在跑(沿用)' } else { 'Celeritas PS7 正主缺' })
    $accel += $(if ($VIAPSAccelLoaded) { 'PS-ACCEL 橋已載' } else { 'PS-ACCEL 橋缺' })
    $accel += 'PY 子程式各自帶 ACCEL-BRIDGE'
    Add-Row 'S02 加速器(PS+PY)' $(if ($VIACelTplOwn -or (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore)) { 'GREEN' } else { 'YELLOW' }) ($accel -join ' · ')

    # S03 取碼:專用稀疏副本(git 自帶傳輸;重試 2/4/8 s)
    $git = (Get-Command git -ErrorAction SilentlyContinue).Source
    $Kit = Join-Path $KitRoot 'movies-dataset'
    $KitVIA = Join-Path $Kit 'VeritasIntelligenceAnalytics'
    $Sparse = @(
        '/.mcp.json', '/VeritasIntelligenceAnalytics/Invoke-VIA-WorkbenchLocal-v*.ps1', '/VeritasIntelligenceAnalytics/Invoke-VIA-UploadsWorkbench-v*.ps1',
        '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_UploadsWorkbench_v*.py', '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_WorkbenchLock_v*.py',
        '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_NetFetch_v*.py', '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_PlaywrightProbe_v*.py',
        '/VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_GraphifyLane_v*.py', '/VeritasIntelligenceAnalytics/review/VIA_Workbench_LockSite_v0106_4/',
        '/VeritasIntelligenceAnalytics/supportive modules/VIA_PS_Accel_Module.ps1', '/VeritasIntelligenceAnalytics/supportive modules/VIA_SuperAccel_Module.py',
        '/VeritasIntelligenceAnalytics/supportive modules/VeritasCeleritas_v*.py', '/VeritasIntelligenceAnalytics/supportive modules/ps7/',
        '/VeritasIntelligenceAnalytics/supportive modules/network/SUP_MDL740_NetUnified_v*.py', '/VeritasIntelligenceAnalytics/supportive modules/network/SUP_MDL756_SmartDecode_v*.py',
        '/VeritasIntelligenceAnalytics/supportive modules/network/VeritasAegisNexus_v*.py',
        '/VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL279_MCPServer_v*.py',
        # 網路工具經 VCGC 啟用器讀鎖冊選 AegisNexus 版本 → 啟用器鏈 · 鎖冊 · 引擎版本冊 · 名冊 · 同意閘(稀疏副本內實測 NetUnified 自測 9/9)
        '/VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL233_ToolActivate_v*.py', '/VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL224_ScrapeGate_v*.py',
        '/VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v*.json', '/VeritasIntelligenceAnalytics/supportive modules/registry/VIA_EngineVersion_Register_v*.json',
        '/VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolRoster_SSOT_v*.json'
    )
    if (-not $git) { Add-Row 'S03 取碼(稀疏套件)' 'RED' '找不到 git'; $rc = 1 }
    elseif (Test-Want 'S03 取碼') {
        if (-not (Test-Path -LiteralPath (Join-Path $Kit '.git'))) {
            $r = Invoke-Step -Name 'S03a git clone(稀疏 · 無檔)' -Exe $git -ArgList @('clone', '--progress', '--filter=blob:none', '--no-checkout', '--depth', '1', '--branch', $Branch, $RepoUrl, $Kit) -TimeoutSec 600 -Git
        }
        & $git -C $Kit sparse-checkout set --no-cone @Sparse 2>&1 | Out-Null
        $ok = $false
        foreach ($wait in 0, 2, 4, 8) {
            if ($wait) { Write-Line ("    重試前等 {0}s" -f $wait) 'DarkYellow'; Start-Sleep -Seconds $wait; $null = $Rows.RemoveAt($Rows.Count - 1) }
            $r = Invoke-Step -Name 'S03b git fetch(本分支尾)' -Exe $git -ArgList @('-C', $Kit, 'fetch', '--progress', '--depth', '1', 'origin', $Branch) -TimeoutSec 600 -Git
            if ($r -and $r.Code -eq 0) { $ok = $true; break }
        }
        if ($ok) {
            $r = Invoke-Step -Name 'S03c git checkout(專用副本對齊)' -Exe $git -ArgList @('-C', $Kit, '-c', 'advice.detachedHead=false', 'checkout', '--force', 'FETCH_HEAD') -TimeoutSec 300 -Git
            Write-Line ("    套件 @ " + ((& $git -C $Kit rev-parse --short HEAD) -join '')) 'DarkGray'
        }
        else { $rc = 1 }
    }
    else { Add-Row 'S03 取碼(稀疏套件)' 'SKIP' "-Only $Only" }
    $script:TotalSteps = [math]::Max($script:TotalSteps, $Rows.Count + 13)

    # 尾版挑法:套件優先(本分支新件),專案倉有就用專案倉的(他系統 / 大件)
    $AI = Join-Path $KitVIA 'docs\handoff\ai'
    $RepoAI = if ($RepoVIA) { Join-Path $RepoVIA 'docs\handoff\ai' } else { $null }
    $NetDir = if ($RepoVIA -and (Get-Newest (Join-Path $RepoVIA 'supportive modules\network') 'SUP_MDL740_NetUnified_v*.py')) { Join-Path $RepoVIA 'supportive modules\network' } else { Join-Path $KitVIA 'supportive modules\network' }

    # S04 網路工具體檢 · S05 資料檔下載(只經網路工具)
    Invoke-Py 'S04 網路工具 NetUnified 自測' (Get-Newest $NetDir 'SUP_MDL740_NetUnified_v*.py') @('--selftest') 300 -RcOnly | Out-Null
    if ($FetchUrl.Count) {
        $fa = @(); foreach ($u in $FetchUrl) { $fa += @('--url', $u) }; foreach ($h in $FetchSha) { $fa += @('--sha', $h) }
        Invoke-Py 'S05 資料檔下載(經網路工具)' (Get-Newest $AI 'VIA_NetFetch_v*.py') ($fa + @('--out', (Join-Path $Out 'fetched'))) 1800 | Out-Null
    }
    else { Add-Row 'S05 資料檔下載(經網路工具)' 'SKIP' '沒給 -FetchUrl(本跑不下載任何資料檔)' }

    # S06–S10 自測
    Invoke-Py 'S06 自測 上傳整合器' (Get-Newest $AI 'VIA_UploadsWorkbench_v*.py') @('--selftest') 300 -RcOnly | Out-Null
    Invoke-Py 'S07 自測 NetFetch' (Get-Newest $AI 'VIA_NetFetch_v*.py') @('--selftest') 300 -RcOnly | Out-Null
    Invoke-Py 'S08 自測 PlaywrightProbe' (Get-Newest $AI 'VIA_PlaywrightProbe_v*.py') @('--selftest') 300 -RcOnly | Out-Null
    Invoke-Py 'S09 自測 GraphifyLane' (Get-Newest $AI 'VIA_GraphifyLane_v*.py') @('--selftest') 300 -RcOnly | Out-Null
    Invoke-Py 'S10 自測 VCGC MCP' (Get-Newest (Join-Path $KitVIA 'supportive modules\registry') 'CGC_MDL279_MCPServer_v*.py') @('--selftest') 300 -RcOnly | Out-Null

    # S11 出頁:挑 20 份正本(含「 (n)」複本)→ 暫存 → 上傳整合器(鎖定 U/I)
    $hub = Join-Path $Out 'index.html'
    if (Test-Want 'S11 出頁') {
        $Wanted = @('VIA v0105 實際ZIP完整矩陣與欄位燈號稽核 v0105.2.md', 'VIA_Matrix_Audit_v0105_1_20261106.xlsx', 'VIA VCGC · AI handover · v0106.4.md',
            'subsystem_v0106_4_final_actual_zip_receipt.json', 'VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip.sha256',
            'VIA 六系統獨立工作台與 AI 交接指南 v0106.4.md', 'viaatlas.zip', 'VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip',
            'VIA_Workbench_Hub_latest.html', 'VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip.sha256', 'VIA Matrix Governance v0105 — 現況與安全接入.md',
            'VIA Governance MCP v0105 — Windows 手動接入.md', 'mcp_stdio_smoke_v0105_2.py', 'VIA_Matrix_Audit_v0105_1_20261106.json',
            'VIA 五系統 RED 阻礙與安全修復計畫 v0105.2.md', 'matrix_detail_v0105_2_final_receipt.json', 'VIA_Matrix_Governance_Full_Model_v0105_1_20261106.json.gz',
            'VIA_MatrixGovernance_AllInOne_v0100.py', 'VIA_MatrixGovernance_QA_v0100.html', 'VIA_MatrixGovernance_README_v0100.md')
        $rx = foreach ($w in $Wanted) { $e = [IO.Path]::GetExtension($w); '^' + [regex]::Escape($w.Substring(0, $w.Length - $e.Length)) + '( \(\d+\))?' + [regex]::Escape($e) + '$' }
        $Stage = Join-Path ([IO.Path]::GetTempPath()) ("VIA_UploadsStage_" + $RunStamp + "_" + $PID)
        New-Item -ItemType Directory -Path $Stage -Force | Out-Null
        $files = @(Get-ChildItem -LiteralPath $Downloads -File -ErrorAction SilentlyContinue)
        $n = 0; $picked = 0
        foreach ($f in $files) {
            $n++
            if ($n % 25 -eq 0 -or $n -eq $files.Count) { Write-Progress -Id 2 -ParentId 1 -Activity 'S11a 挑檔' -Status ("{0}/{1} · 已挑 {2}" -f $n, $files.Count, $picked) -PercentComplete ([int](100.0 * $n / [math]::Max(1, $files.Count))) }
            foreach ($r1 in $rx) { if ($f.Name -match $r1) { Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $Stage $f.Name); $picked++; break } }
        }
        Write-Progress -Id 2 -Activity 'S11a 挑檔' -Completed
        Add-Row 'S11a 挑檔(下載夾不動)' $(if ($picked) { 'GREEN' } else { 'RED' }) ("掃 {0} 檔 · 挑 {1} 個 → {2}" -f $files.Count, $picked, $Stage)
        if ($picked) {
            Invoke-Py 'S11b 出頁(鎖定 U/I · 0 token)' (Get-Newest $AI 'VIA_UploadsWorkbench_v*.py') @('--in', $Stage, '--out', $Out) 1800 | Out-Null
        }
        Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue
    }
    else { Add-Row 'S11 出頁' 'SKIP' "-Only $Only" }

    # S12 Playwright 實測出好的頁 · S13 Graphify 車道 · S14 DuckDB 湖矩陣
    if (Test-Path -LiteralPath $hub) { Invoke-Py 'S12 Playwright 實測工作台頁' (Get-Newest $AI 'VIA_PlaywrightProbe_v*.py') @('--pages', $Out, '--out', (Join-Path $RunDir 'shots')) 1800 | Out-Null }
    else { Add-Row 'S12 Playwright 實測工作台頁' 'YELLOW' '沒有頁可測(S11 沒出頁)' }
    $gl = if ($RepoAI -and (Get-Newest $RepoAI 'VIA_GraphifyLane_v*.py')) { Get-Newest $RepoAI 'VIA_GraphifyLane_v*.py' } else { Get-Newest $AI 'VIA_GraphifyLane_v*.py' }
    Invoke-Py 'S13 Graphify 車道' $gl @() 300 | Out-Null
    if ($RepoAI) { Invoke-Py 'S14 DuckDB 湖矩陣(VCGC 自己的湖)' (Get-Newest $RepoAI 'VIA_LakeMatrix_v*.py') @() 1800 $RepoVIA | Out-Null }
    else { Add-Row 'S14 DuckDB 湖矩陣(VCGC 自己的湖)' 'YELLOW' '沒有本機倉:湖在專案倉裡,本跑略過' }

    # S15 VCGC 唯讀(專案倉的主控台:省 Token 卡 · 工具席位)
    $V = if ($RepoVIA) { Get-Newest (Join-Path $RepoVIA 'supportive modules\registry') 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' } else { $null }
    if ($V) {
        Invoke-Py 'S15a VCGC token(省 Token 卡)' $V @('token') 600 $Repo -RcOnly | Out-Null
        Invoke-Py 'S15b VCGC tools(工具席位)' $V @('tools') 600 $Repo -RcOnly | Out-Null
    }
    else { Add-Row 'S15 VCGC 唯讀' 'YELLOW' '沒有本機倉 / 主控台:略過' }

    # S16 MCP:收據給 VCGC MCP(via://uploads/latest)· 印 / 寫用戶端設定
    $mcpSrv = Get-Newest (Join-Path $KitVIA 'supportive modules\registry') 'CGC_MDL279_MCPServer_v*.py'
    $mcpRoot = if ($RepoVIA) { $RepoVIA } else { $KitVIA }
    if ((Test-Path -LiteralPath (Join-Path $Out 'uploads_receipt.json')) -and $mcpSrv) {
        $md = Join-Path $mcpRoot 'VIA_Reports\uploads'; New-Item -ItemType Directory -Path $md -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $Out 'uploads_receipt.json') -Destination (Join-Path $md 'UPLOADS_latest.json') -Force
        $pp = $script:PyPre
        $cfg = ((& $script:PyExe @pp $mcpSrv --client-config --root $mcpRoot) -join "`n") | ConvertFrom-Json -AsHashtable
        $srv = $cfg['mcpServers']['vcgc']; $srv['command'] = $script:PyExe; $srv['args'] = @($script:PyPre) + @($srv['args'])
        $note = "收據 → $md\UPLOADS_latest.json · 伺服器 $(Split-Path $mcpSrv -Leaf) · root $mcpRoot"
        if ($ActivateMcp) {
            $desk = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
            New-Item -ItemType Directory -Path (Split-Path $desk -Parent) -Force | Out-Null
            $conf = @{}
            if (Test-Path -LiteralPath $desk) {
                Copy-Item -LiteralPath $desk -Destination ($desk + '.bak_' + $RunStamp)
                $t = Get-Content -LiteralPath $desk -Raw -Encoding utf8; if ($t.Trim()) { $conf = $t | ConvertFrom-Json -AsHashtable }
            }
            if (-not $conf.ContainsKey('mcpServers')) { $conf['mcpServers'] = @{} }
            $conf['mcpServers']['vcgc'] = $srv
            Set-Content -LiteralPath $desk -Value ($conf | ConvertTo-Json -Depth 20) -Encoding utf8NoBOM
            Add-Row 'S16 VCGC MCP' 'GREEN' ("$note · 已寫入 Claude Desktop(原檔備份 .bak_$RunStamp)· 重開 Claude Desktop 生效")
        }
        else {
            Write-Line (@{ mcpServers = @{ vcgc = $srv } } | ConvertTo-Json -Depth 10) 'DarkGray'
            Add-Row 'S16 VCGC MCP' 'YELLOW' "$note · 只印設定(要寫入加 -ActivateMcp)"
        }
    }
    else { Add-Row 'S16 VCGC MCP' 'YELLOW' '沒有整合收據或 MCP 伺服器:略過' }

    # 前端伺服器(只綁 127.0.0.1)/ 開頁
    $url = $null
    if ($Serve -and (Test-Path -LiteralPath $hub)) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { Write-Line "  port $Port 已被占用,沒另開(換 -Port)" 'Yellow' }
        else {
            $p = Start-Process -FilePath $script:PyExe -ArgumentList (@($script:PyPre) + @('-m', 'http.server', "$Port", '--bind', '127.0.0.1', '--directory', $Out)) -WindowStyle Minimized -PassThru
            $url = "http://127.0.0.1:$Port/index.html"; Write-Line "  前端伺服器 PID $($p.Id) · $url · 停止:Stop-Process -Id $($p.Id)" 'Green'
        }
    }
    if (-not $NoOpen -and (Test-Path -LiteralPath $hub)) { if ($url) { Start-Process $url } else { Invoke-Item -LiteralPath $hub } }
}
catch {
    if ($_.Exception -isnot [OperationCanceledException]) { Add-Row '例外' 'RED' $_.Exception.Message }
}
finally {
    Write-Progress -Id 1 -Activity "VIA WorkbenchLocal $SelfVer" -Completed
    Set-Location -LiteralPath $StartDir
    $nRed = @($Rows | Where-Object { $_.燈 -eq 'RED' }).Count
    $nYel = @($Rows | Where-Object { $_.燈 -eq 'YELLOW' }).Count
    $rc = if ($nRed) { 1 } elseif ($nYel) { 2 } else { 0 }
    Write-Host ""
    $Rows | Select-Object 步驟, 燈, 秒, 說明 | Format-Table -AutoSize -Wrap
    $verdict = @{ 0 = 'GREEN 全綠'; 1 = "RED 紅 $nRed 步"; 2 = "YELLOW 黃 $nYel 步(黃不是綠)" }[$rc]
    Write-Line ("總判:{0} · log 與收據:{1}" -f $verdict, $RunDir) $(@{ 0 = 'Green'; 1 = 'Red'; 2 = 'Yellow' }[$rc])
    try {
        @{ engine = "Invoke-VIA-WorkbenchLocal_$SelfVer"; at_utc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'); rc = $rc; repo = $Repo; kit = $KitRoot; steps = $Rows } |
            ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $RunDir 'workbenchlocal_receipt.json') -Encoding utf8NoBOM
    } catch { }
}
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
exit $rc
