#requires -Version 7.0
# ============================================================================
#  VMT  Read-Only Launcher  v1.0   --  AI Outlook 郵箱 × 工作管理系統啟動器
# ----------------------------------------------------------------------------
#  目的: 在 Windows / PowerShell 環境下啟動 VMT 引擎管線, 免去 python3 與
#        路徑寫法的差異。預設 dry-run, 只讀不寫。
#  治理: 唯讀啟動器 -- 不寫任何 DB; 不呼叫 Stop-Process; 不做破壞性刪除;
#        來源信箱全程唯讀。落帳需明確加 -Commit, 寄信需再加 -Draft / -Send。
#  隔離: 優先使用專屬 venv  vmt_pm (Py3.11) @ C:\Users\tonyk\envs\vmt_pm;
#        找不到就退回系統 Python。引擎本身零套件相依, 兩者皆可執行。
#  慣例: param 首列; 無別名; 無 Read-Host; 無 exit / Stop-Process;
#        ProcessStartInfo 管子程序; UTF8 no-BOM 寫檔; Start-Process 僅開報告。
#
#  用法:
#    .\Start-VMT.ps1 -Demo                     內建範例, dry-run (什麼都不寫)
#    .\Start-VMT.ps1 -Demo -Commit             內建範例, 實際落帳
#    .\Start-VMT.ps1                           讀真實 Outlook, dry-run
#    .\Start-VMT.ps1 -Commit                   讀真實 Outlook, 落帳 + 寫信稿
#    .\Start-VMT.ps1 -Commit -Draft            另外在 Outlook 建草稿 (不寄出)
#    .\Start-VMT.ps1 -Transcript meeting.json  加上會議逐字稿
#    .\Start-VMT.ps1 -Test                     跑 35 項單元測試
# ============================================================================
param(
    [string]$Root           = "",
    [string]$EnvRoot        = "C:\Users\tonyk\envs",
    [string]$EnvName        = "vmt_pm",
    [string]$PyLauncher     = "",
    [ValidateSet('auto','outlook','folder','sample')]
    [string]$Source         = "auto",
    [string]$Transcript     = "",
    [string]$MeetingConfig  = "",
    [string]$Me             = "",
    [string]$AsOf           = "",
    [switch]$Demo,
    [switch]$Commit,
    [switch]$Draft,
    [switch]$Send,
    [switch]$Llm,
    [switch]$Test,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$script:T0 = Get-Date
$script:Here = $PSScriptRoot

function Write-Step {
    param([string]$Tag, [string]$Msg, [string]$Color = 'Cyan')
    Write-Host ("[{0}] [{1}] {2}" -f (Get-Date).ToString('HH:mm:ss'), $Tag, $Msg) -ForegroundColor $Color
}

# ----- ProcessStartInfo 子程序執行 (等程序結束, 非等使用者輸入) -------------
function Invoke-Native {
    param([string]$FilePath, [string[]]$Arguments)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    foreach ($a in $Arguments) { [void]$psi.ArgumentList.Add($a) }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding  = [System.Text.Encoding]::UTF8
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    $started = $false
    try { $started = $proc.Start() } catch { return @{ code = -999; out = ''; err = $_.Exception.Message } }
    if (-not $started) { return @{ code = -998; out = ''; err = 'process did not start' } }
    $out = $proc.StandardOutput.ReadToEnd()
    $err = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    return @{ code = $proc.ExitCode; out = $out; err = $err }
}

# ----- Python 啟動器偵測 (專屬 venv 優先, 再 py -3.11, 最後系統 python) -----
function Resolve-PyLauncher {
    param([string]$Preferred, [string]$VenvPython)
    $cands = @()
    if ($Preferred)  { $cands += ,@($Preferred,   @()) }
    if ($VenvPython -and (Test-Path -LiteralPath $VenvPython)) { $cands += ,@($VenvPython, @()) }
    $cands += ,@('py',         @('-3.11'))
    $cands += ,@('py',         @('-3'))
    $cands += ,@('python3.11', @())
    $cands += ,@('python',     @())
    $cands += ,@('python3',    @())
    foreach ($c in $cands) {
        $r = Invoke-Native -FilePath $c[0] -Arguments (@($c[1]) + @('--version'))
        $txt = ($r.out + $r.err).Trim()
        if ($r.code -eq 0 -and ($txt -match 'Python\s+3\.(\d+)')) {
            $minor = [int]$Matches[1]
            if ($minor -ge 11) {
                return @{ file = $c[0]; pre = $c[1]; ver = $txt }
            }
        }
    }
    return $null
}

Write-Host ''
Write-Host '=============================================================' -ForegroundColor DarkCyan
Write-Host '  VMT  |  AI 高智慧自動 Outlook 郵箱及工作管理系統  v1.0' -ForegroundColor Cyan
Write-Host '  唯讀啟動器 · 預設 dry-run · 不寫 DB · 不 Stop-Process' -ForegroundColor DarkGray
Write-Host '=============================================================' -ForegroundColor DarkCyan

# ----- 前置檢查 --------------------------------------------------------------
$engineDir = Join-Path $script:Here 'engines'
$pipeline  = Join-Path $engineDir  'vmt_pipeline.py'
$testFile  = Join-Path $script:Here 'tests\test_vmt_engines.py'

if (-not (Test-Path -LiteralPath $pipeline)) {
    Write-Step 'ERR' "找不到引擎: $pipeline" 'Red'
    Write-Step 'ERR' '請確認目前分支含 VMT 引擎組 (PR #5 的分支)。' 'Red'
    Write-Host ''
    Write-Host '  git fetch origin claude/auto-meeting-notes-workflow-x4ow5i' -ForegroundColor Yellow
    Write-Host '  git checkout claude/auto-meeting-notes-workflow-x4ow5i' -ForegroundColor Yellow
    Write-Host ''
    return
}

if ($Send -and -not $Commit) {
    Write-Step 'GATE' '-Send 必須搭配 -Commit。已中止, 未執行任何動作。' 'Red'
    return
}
if ($Draft -and -not $Commit) {
    Write-Step 'GATE' '-Draft 必須搭配 -Commit。已中止, 未執行任何動作。' 'Red'
    return
}

$venvPy = Join-Path (Join-Path $EnvRoot $EnvName) 'Scripts\python.exe'
$py = Resolve-PyLauncher -Preferred $PyLauncher -VenvPython $venvPy
if ($null -eq $py) {
    Write-Step 'ERR' '找不到 Python 3.11 以上。請安裝 Python 或指定 -PyLauncher。' 'Red'
    Write-Step 'ERR' '(Windows 上沒有 python3 這個指令, 一般是 py 或 python)' 'DarkGray'
    return
}
$whichPy = if ($py.file -eq $venvPy) { "專屬 venv $EnvName" } else { "系統 $($py.file)" }
Write-Step 'PY'   "$($py.ver)  ←  $whichPy"

# ----- 工作區 ----------------------------------------------------------------
if ($Root) {
    $env:VMT_ROOT = $Root
} elseif (-not $env:VMT_ROOT) {
    $env:VMT_ROOT = 'C:\VIA\VeritasMailTracker'
}
Write-Step 'ROOT' $env:VMT_ROOT
if (-not (Test-Path -LiteralPath $env:VMT_ROOT)) {
    if ($Commit) {
        # 只在落帳模式建立目錄; dry-run 連目錄都不碰
        [void][System.IO.Directory]::CreateDirectory($env:VMT_ROOT)
        Write-Step 'ROOT' '工作區不存在, 已建立 (僅 -Commit 模式會建立)' 'DarkYellow'
    } else {
        Write-Step 'ROOT' '工作區尚未建立 — dry-run 不需要它, 加 -Commit 時才會建立' 'DarkGray'
    }
}

# ----- 測試模式 --------------------------------------------------------------
if ($Test) {
    Write-Step 'TEST' '執行單元測試 (不碰任何工作區資料)...'
    $r = Invoke-Native -FilePath $py.file -Arguments (@($py.pre) + @($testFile))
    Write-Host $r.out
    if ($r.err) { Write-Host $r.err -ForegroundColor DarkGray }
    if ($r.code -eq 0) { Write-Step 'TEST' '全部通過' 'Green' }
    else { Write-Step 'TEST' "有失敗 (exit $($r.code))" 'Red' }
    return
}

# ----- 組引擎參數 ------------------------------------------------------------
$engineArgs = @($pipeline)
if ($Demo) { $engineArgs += '--demo' }
else       { $engineArgs += @('--source', $Source) }
if ($Commit) { $engineArgs += '--commit' }
if ($Draft) { $engineArgs += '--draft' }
if ($Send) { $engineArgs += '--send' }
if ($Llm)  { $engineArgs += '--llm' }
if ($Me)   { $engineArgs += @('--me', $Me) }
if ($AsOf) { $engineArgs += @('--as-of', $AsOf) }
if ($Transcript)    { $engineArgs += @('--transcript', $Transcript) }
if ($MeetingConfig) { $engineArgs += @('--meeting-config', $MeetingConfig) }
$engineArgs += '--no-open'        # 報告由本啟動器統一開啟, 引擎端不自行開窗

$mode = 'DRY-RUN (只產報告, 不寫任何東西)'
if ($Send) { $mode = 'COMMIT + 直接寄出 (不可逆)' }
elseif ($Draft) { $mode = 'COMMIT + 建 Outlook 草稿 (不寄出)' }
elseif ($Commit) { $mode = 'COMMIT (落帳 + 寫 .txt 信稿, 不寄出)' }

$modeColor = 'Green'
if ($Commit) { $modeColor = 'Yellow' }
Write-Step 'MODE' $mode $modeColor
if ($Send) {
    Write-Step 'WARN' '信件將直接寄出, 無法撤回。' 'Red'
}

# ----- 執行 ------------------------------------------------------------------
Write-Step 'RUN' '啟動引擎管線...'
$r = Invoke-Native -FilePath $py.file -Arguments (@($py.pre) + $engineArgs)
Write-Host ''
Write-Host $r.out
if ($r.err) { Write-Host $r.err -ForegroundColor DarkGray }

if ($r.code -ne 0) {
    Write-Step 'ERR' "引擎回傳非零離開碼: $($r.code)" 'Red'
    return
}

# ----- 開啟報告 (Start-Process 僅用於開啟報告) -------------------------------
$dash = Join-Path (Join-Path $env:VMT_ROOT 'reports') 'VMT_Dashboard.html'
if ((Test-Path -LiteralPath $dash) -and (-not $NoOpen)) {
    Write-Step 'OPEN' $dash
    Start-Process -FilePath $dash
} elseif (-not (Test-Path -LiteralPath $dash)) {
    Write-Step 'OPEN' '尚無戰情總覽 (dry-run 亦會產出報告, 若無請檢查工作區路徑)' 'DarkGray'
}

$elapsed = ((Get-Date) - $script:T0).TotalSeconds
Write-Host ''
Write-Host '===== VMT DONE =====' -ForegroundColor DarkCyan
Write-Host ("模式     : {0}" -f $mode)
Write-Host ("工作區   : {0}" -f $env:VMT_ROOT)
Write-Host ("報告     : {0}" -f (Join-Path $env:VMT_ROOT 'reports'))
Write-Host ("Python   : {0}  ({1})" -f $py.ver, $whichPy)
Write-Host ("耗時     : {0:N1} 秒" -f $elapsed)
if (-not $Commit) {
    Write-Host ''
    Write-Host '※ 這是 dry-run。以上全部只是計畫，未寫入任何帳本、未產生任何信件。' -ForegroundColor Yellow
    Write-Host '  確認無誤後加上 -Commit 重跑。' -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
