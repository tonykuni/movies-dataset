<#
.SYNOPSIS
  VIA 桌機一支全包 v0101(2026-11-12)— ① 取這輪檔 ② 唯讀驗證 VCGC · VDF · VRN 產出(VIA_DesktopValidate v0100)
  ③ 實測 OneShot v0101(-WithOneShot 才跑)④ Claude 桌面版 / Claude Code 命令列缺就裝 ⑤ 遠端連線永遠開(開機自動 · 斷線自動重開)⑥ 總表 + 剪貼簿。

.DESCRIPTION
  操作員 2026-11-12「ONE PS TO HANDLE ALL ABOVE」「REAL-TEST AND VALIDATE OUTPUT OF VRN VDF VCGC AUTOMATICALLY」「永遠啟動遠端連線手機連線」。
  v0101:加唯讀驗證;remote-control 改成「開機登入自動啟動 + 斷線 30 秒後自動重開」(使用者層 Startup 捷徑 · 不需系統管理員);v0100 不動。
  - 不論從哪個資料夾執行,先自己找到 movies-dataset 倉再做事(上次在 C:\Users\tonyk 跑 → not a git repository)。
  - 安裝一律先問 Y/N(-Yes 才自動);只用官方來源:winget Anthropic.Claude · https://claude.ai/install.ps1。
  - 不設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)· 不碰 TA-Lib · 不推 · 不改 VRN-1 遠端。
  - Desktop Commander 要在 Claude 桌面版裡由你登入 / 啟用,本支只把桌面版裝好並開起來,不代設帳號。

.EXAMPLE
  Set-Location "$env:USERPROFILE\OneDrive\Documents\movies-dataset"
  git fetch origin claude/optimistic-goodall-yhalc5
  git checkout origin/claude/optimistic-goodall-yhalc5 -- "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopAllInOne_v0101.ps1"
  pwsh -NoProfile -ExecutionPolicy Bypass -File "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopAllInOne_v0101.ps1"
#>
[CmdletBinding()]
param(
    [string]$Repo = '',
    [string]$Branch = 'claude/optimistic-goodall-yhalc5',
    [switch]$Yes,
    [switch]$WithOneShot,
    [switch]$NoValidate,
    [switch]$NoAlwaysOn,
    [switch]$SkipInstall,
    [switch]$NoRemote
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$Stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$Log   = Join-Path $env:TEMP "VIA_DesktopAllInOne_v0101_$Stamp.log"
$Paste = Join-Path $env:TEMP "VIA_DesktopAllInOne_v0101_${Stamp}_paste.txt"
$Rows  = [System.Collections.Generic.List[object]]::new()

function Say([string]$m, [string]$c = 'Gray') { Write-Host $m -ForegroundColor $c; Add-Content -Path $Log -Value $m -Encoding utf8 }
function Note([string]$step, [string]$lamp, [string]$key) { $Rows.Add([pscustomobject]@{ Step = $step; Lamp = $lamp; Key = $key }) }
function Ask([string]$q) {
    if ($Yes) { return $true }
    $a = Read-Host "$q [Y/N]"
    return ($a -match '^(y|yes|是)$')
}

# ── ① 找倉(不論從哪個資料夾執行)───────────────────────────────────────
function Find-Repo {
    $cands = @()
    if ($Repo) { $cands += $Repo }
    if ($PSScriptRoot) { $cands += (git -C $PSScriptRoot rev-parse --show-toplevel 2>$null) }
    $cands += (git rev-parse --show-toplevel 2>$null)
    $cands += @(
        (Join-Path $env:USERPROFILE 'OneDrive\Documents\movies-dataset'),
        (Join-Path $env:USERPROFILE 'Documents\movies-dataset'),
        (Join-Path $env:USERPROFILE 'movies-dataset')
    )
    foreach ($c in $cands) {
        if ($c -and (Test-Path (Join-Path $c '.git')) -and (Test-Path (Join-Path $c 'VeritasIntelligenceAnalytics'))) { return (Resolve-Path $c).Path }
    }
    $hit = Get-ChildItem -Path $env:USERPROFILE -Directory -Filter 'movies-dataset' -Recurse -Depth 4 -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName '.git') } | Select-Object -First 1
    if ($hit) { return $hit.FullName }
    return $null
}

$RepoPath = Find-Repo
if (-not $RepoPath) {
    Say '[RED] 找不到 movies-dataset 倉(要有 .git 與 VeritasIntelligenceAnalytics 夾)· 用 -Repo "<倉路徑>" 指定' 'Red'
    exit 1
}
Set-Location $RepoPath
Say "[GREEN] 倉:$RepoPath" 'Green'
Note '找倉' 'GREEN' $RepoPath

# ── ② 取這輪檔(只取這些 · 其他本機改動不動)────────────────────────────────
$AI = 'VeritasIntelligenceAnalytics/docs/handoff/ai'
$Round = @(
    "$AI/VIA_DesktopValidate_v0100.py",
    "$AI/VIA_DesktopOneShot_v0101.ps1",
    'VeritasIntelligenceAnalytics/functional modules/VDF/VDF_SystemManager_v0170.py',
    'VeritasIntelligenceAnalytics/functional modules/VRN/VRN_SystemManager_v0264.py'
)
git fetch origin $Branch 2>&1 | ForEach-Object { Say "  $_" }
$got = @($Round | Where-Object { git cat-file -e "origin/${Branch}:$_" 2>$null; $LASTEXITCODE -eq 0 })
if ($got.Count) { git checkout "origin/$Branch" -- @got 2>&1 | ForEach-Object { Say "  $_" } }
Note '取這輪檔' ($(if ($got.Count -eq $Round.Count) { 'GREEN' } else { 'YELLOW' })) "$($got.Count)/$($Round.Count) 支"

# ── ③ 唯讀驗證 VCGC · VDF · VRN 產出 ─────────────────────────────────────
if (-not $NoValidate) {
    $Val = "$AI/VIA_DesktopValidate_v0100.py"
    if (Test-Path $Val) {
        Say '▶ 唯讀驗證 VIA_DesktopValidate v0100' 'Cyan'
        $vout = & python $Val --root $RepoPath 2>&1 | ForEach-Object { $l = "$_"; Say $l; $l }
        $vrc = $LASTEXITCODE
        $vlast = @($vout | Where-Object { $_ -match '總燈' }) | Select-Object -Last 1
        $vlamp = if ($vlast -match '^\[(\w+)\]') { $Matches[1] } else { "rc $vrc" }
        Note '唯讀驗證' $vlamp ($(if ($vlast) { $vlast } else { "rc $vrc" }))
        $global:ValidateLines = @($vout | Where-Object { $_ -match '^\s+\[' })
    } else { Note '唯讀驗證' 'RED' "取不到 $Val" }
} else { Note '唯讀驗證' 'SKIP' '-NoValidate' }

# ── ④ 實測 OneShot v0101(選用:-WithOneShot)───────────────────────────────
if ($WithOneShot) {
    $One = "$AI/VIA_DesktopOneShot_v0101.ps1"
    if (Test-Path $One) {
        Say '▶ 實測 VIA_DesktopOneShot v0101' 'Cyan'
        $before = Get-Date
        & pwsh -NoProfile -ExecutionPolicy Bypass -File $One -Branch $Branch
        $rc = $LASTEXITCODE
        $sum = Get-ChildItem -Path $env:TEMP -Filter 'VIA_DesktopOneShot_v0101_*_paste.txt' -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $before } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($sum) { Note '實測 OneShot v0101' 'DONE' "摘要 $($sum.FullName)" } else { Note '實測 OneShot v0101' 'YELLOW' "rc $rc · 沒找到本輪摘要檔" }
    } else { Note '實測 OneShot v0101' 'RED' "取不到 $One" }
} else { Note '實測 OneShot v0101' 'SKIP' '要跑加 -WithOneShot' }

# ── ⑤a Claude 桌面版(Desktop Commander · Remote Control 都靠它)────────────────────
function Find-ClaudeDesktop {
    $paths = @(
        (Join-Path $env:LOCALAPPDATA 'AnthropicClaude\claude.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Claude\Claude.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\claude\Claude.exe')
    )
    foreach ($p in $paths) { if (Test-Path $p) { return $p } }
    return $null
}
$hasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
$desk = Find-ClaudeDesktop
if (-not $desk -and $hasWinget) {
    $listed = winget list --id Anthropic.Claude -e --accept-source-agreements 2>$null | Out-String
    if ($listed -match 'Anthropic\.Claude') { $desk = '(winget 已安裝)' }
}
if ($desk) {
    Note 'Claude 桌面版' 'GREEN' "已安裝 · $desk"
} elseif ($SkipInstall) {
    Note 'Claude 桌面版' 'YELLOW' '未安裝 · -SkipInstall'
} elseif (-not $hasWinget) {
    Note 'Claude 桌面版' 'YELLOW' '未安裝 · 這台沒有 winget → 請到 https://claude.ai/download 下載'
} elseif (Ask '要安裝 Claude 桌面版嗎?(winget · Anthropic.Claude)') {
    Say '▶ winget install Anthropic.Claude' 'Cyan'
    winget install --id Anthropic.Claude -e --accept-package-agreements --accept-source-agreements 2>&1 | ForEach-Object { Say "  $_" }
    $desk = Find-ClaudeDesktop
    Note 'Claude 桌面版' ($(if ($LASTEXITCODE -eq 0 -or $desk) { 'GREEN' } else { 'RED' })) "winget rc $LASTEXITCODE · $desk"
} else {
    Note 'Claude 桌面版' 'YELLOW' '你選不裝'
}
$deskExe = Find-ClaudeDesktop
if ($deskExe) {
    Start-Process -FilePath $deskExe
    Say '[INFO] 已開 Claude 桌面版:請登入 → 設定 → Claude Code → Remote Control 開啟並加入倉夾;Desktop Commander 在桌面版裡啟用。' 'Yellow'
}

# ── ⑤b Claude Code 命令列(claude remote-control 要它)──────────────────────────
function Add-LocalBin { $lb = Join-Path $env:USERPROFILE '.local\bin'; if ((Test-Path $lb) -and ($env:Path -notlike "*$lb*")) { $env:Path = "$lb;$env:Path" } }
Add-LocalBin
$cli = Get-Command claude -ErrorAction SilentlyContinue
if ($cli) {
    $ver = (& claude --version 2>$null | Select-Object -First 1)
    Note 'Claude Code 命令列' 'GREEN' "已安裝 · $ver · $($cli.Source)"
} elseif ($SkipInstall) {
    Note 'Claude Code 命令列' 'YELLOW' '未安裝 · -SkipInstall'
} elseif (Ask '要安裝 Claude Code 命令列嗎?(官方 https://claude.ai/install.ps1 · 裝在使用者層級)') {
    Say '▶ irm https://claude.ai/install.ps1 | iex' 'Cyan'
    try { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression } catch { Say "  [RED] 安裝失敗:$($_.Exception.Message)" 'Red' }
    Add-LocalBin
    $cli = Get-Command claude -ErrorAction SilentlyContinue
    Note 'Claude Code 命令列' ($(if ($cli) { 'GREEN' } else { 'RED' })) ($(if ($cli) { "裝好 · $($cli.Source)" } else { '裝完仍找不到 claude(重開終端機再試)' }))
} else {
    Note 'Claude Code 命令列' 'YELLOW' '你選不裝'
}

# ── ⑥ 遠端連線永遠開(開機登入自動 · 斷線 30 秒後自動重開 · 使用者層 · 不需系統管理員)──────────
$RcDir    = Join-Path $env:LOCALAPPDATA 'VIA'
$RcScript = Join-Path $RcDir 'VIA_RemoteControl_AlwaysOn_v0100.ps1'
$RcLnk    = Join-Path ([Environment]::GetFolderPath('Startup')) 'VIA Claude Remote Control.lnk'
function Test-RcRunning {
    [bool](Get-CimInstance Win32_Process -Filter "Name='pwsh.exe' OR Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*VIA_RemoteControl_AlwaysOn_v0100*' })
}
if ($NoAlwaysOn) {
    Note '遠端連線永遠開' 'SKIP' '-NoAlwaysOn'
} elseif (-not $cli) {
    Note '遠端連線永遠開' 'YELLOW' '沒有 claude 命令列 → 未設定'
} else {
    New-Item -ItemType Directory -Force -Path $RcDir | Out-Null
    @"
# VIA 遠端連線常駐(由 VIA_DesktopAllInOne v0101 產生)· 倉:$RepoPath
`$host.UI.RawUI.WindowTitle = 'VIA Claude Remote Control(常駐 · 不要關)'
`$lb = Join-Path `$env:USERPROFILE '.local\bin'; if (`$env:Path -notlike "*`$lb*") { `$env:Path = "`$lb;`$env:Path" }
Set-Location -LiteralPath '$RepoPath'
while (`$true) {
    Write-Host "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 啟動 claude remote-control" -ForegroundColor Cyan
    claude remote-control
    Write-Host "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] remote-control 結束(rc `$LASTEXITCODE)· 30 秒後重開(要停:關這個視窗)" -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}
"@ | Set-Content -Path $RcScript -Encoding utf8
    $pw = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
    if (-not $pw) { $pw = (Get-Command powershell).Source }
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut($RcLnk)
    $sc.TargetPath = $pw
    $sc.Arguments = "-NoExit -NoProfile -ExecutionPolicy Bypass -File `"$RcScript`""
    $sc.WorkingDirectory = $RepoPath
    $sc.WindowStyle = 7
    $sc.Description = 'VIA Claude Remote Control 常駐(手機 / 網頁版連線)'
    $sc.Save()
    if (Test-RcRunning) {
        Note '遠端連線永遠開' 'GREEN' "已在跑 · 開機捷徑 $RcLnk"
    } else {
        Start-Process -FilePath $pw -ArgumentList @('-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $RcScript) -WindowStyle Minimized
        Note '遠端連線永遠開' 'STARTED' "已啟動(最小化視窗)· 開機自動 · 斷線 30 秒重開 · 捷徑 $RcLnk"
    }
    Say '[INFO] 電腦睡眠時連線會斷;要手機隨時連得到,請在 Windows 設定把「插電時睡眠」改成「永不」。' 'Yellow'
}

# ── 總表 + 剪貼簿 ──────────────────────────────────────────────────
$Rows | Format-Table -AutoSize -Wrap | Out-String -Width 200 | ForEach-Object { Write-Host $_; Add-Content -Path $Log -Value $_ -Encoding utf8 }
$out = @("VIA_DesktopAllInOne v0101 · $Stamp · 倉 $RepoPath") + ($Rows | ForEach-Object { "{0} | {1} | {2}" -f $_.Step, $_.Lamp, $_.Key })
$oneShotSum = $Rows | Where-Object { $_.Step -eq '實測 OneShot v0101' -and $_.Key -like '摘要 *' } | Select-Object -First 1
if ($global:ValidateLines) { $out += '── 唯讀驗證 ──'; $out += $global:ValidateLines }
if ($oneShotSum) { $out += '── 實測摘要 ──'; $out += Get-Content -LiteralPath ($oneShotSum.Key -replace '^摘要 ', '') -Encoding utf8 }
$out | Set-Content -Path $Paste -Encoding utf8
try { $out -join "`n" | Set-Clipboard; $clip = '(已複製到剪貼簿)' } catch { $clip = '' }
Say "日誌:$Log"
Say "貼回摘要:$Paste $clip"
