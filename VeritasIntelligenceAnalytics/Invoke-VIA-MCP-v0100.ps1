# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# Invoke-VIA-MCP-v0100.ps1 — VIA MCP Engine 一支 PS 整合指令(操作員 2026-11-05:「INTEGRATE INTO ONE PS CODE TO HANDLE ALL ABOVE … APPLY THIS INTO VCGC AND ACTIVATE IT」)
#   一支搞定:① 找到倉 → git pull(--ff-only)② 找 python 與 VCGC 主控台尾版 ③ VIA_FROM_VCGC=YES via-vcgc mcp …(doctor · 預設五個 MCP · probe 真啟動 · apply 先乾跑 · Token 檢查 / 唯讀驗證)
#   ④ 開滑鼠操作頁(mcp serve)⑤ 結尾一張矩陣 + 機讀判決行;日誌落 VIA_Reports\mcp\。PS 只做啟動與連結 U/I,業務邏輯全在 VIA_MCP_Engine 尾版(L117)。
#   用法(任何資料夾都可以打;本檔自己找倉):
#     .\Invoke-VIA-MCP-v0100.ps1                                  # all:pull → doctor → (空平台就加預設五個) → probe → apply 乾跑 → token(有就測) → serve 開頁
#     .\Invoke-VIA-MCP-v0100.ps1 -Action serve                    # 只開頁
#     .\Invoke-VIA-MCP-v0100.ps1 -Action setup -Platform claude-desktop -Preset basic   # 加 Filesystem(Documents)· Memory · Fetch · Sequential Thinking · GitHub
#     .\Invoke-VIA-MCP-v0100.ps1 -Action probe -Platform claude-desktop                 # 真啟動每一個 MCP(initialize → tools/list)
#     .\Invoke-VIA-MCP-v0100.ps1 -Action apply -Platform claude-desktop -Apply          # 真寫設定檔(先備份);沒 -Apply 只乾跑
#     .\Invoke-VIA-MCP-v0100.ps1 -Action token -TokenSource store -TokenRepo owner/repo  # 憑證管理員 GITHUB_PAT_READONLY → 讀 5 ✓ 寫 3 ✗ 驗證(寫入意外成功自動清理)
#     .\Invoke-VIA-MCP-v0100.ps1 -InstallShortcut                 # 把 via-mcp 短令寫進你自己的 $PROFILE(操作員的手;L70:本檔不改任何既有 .ps1)
#   加速 / 進度:點載 supportive modules\VIA_PS_PyProgress_Module.ps1 → Invoke-VIAPython(25 加速器 · 心跳 · 逾時);Invoke-VIACeleritasScoped 有就套;都缺就直呼 python 照實說。
#   不碰 TA-Lib;不改其他 .ps1(L70);不裝套件;不代設同意閘;Token 永不寫進檔案(只在憑證庫 / 環境變數)。
[CmdletBinding()]
param(
    [ValidateSet('all', 'card', 'doctor', 'selftest', 'setup', 'probe', 'apply', 'token', 'serve', 'pull')][string]$Action = 'all',
    [string]$Platform = 'claude-desktop',
    [ValidateSet('', 'basic', 'research')][string]$Preset = '',
    [string]$Repo = '',
    [string]$Python = '',
    [int]$Port = 8765,
    [switch]$Apply,
    [switch]$NoPull,
    [switch]$NoOpen,
    [switch]$NoProbe,
    [ValidateSet('env', 'store')][string]$TokenSource = 'env',
    [string]$TokenRepo = '',
    [switch]$InstallShortcut,
    [int]$TimeoutSec = 1800,
    [int]$ProbeTimeoutSec = 180
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

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$script:Stamp = Get-Date -Format yyyyMMdd_HHmmss
$script:Rows = [System.Collections.Generic.List[object]]::new()
$script:Fails = 0

function Write-Lamp([string]$Step, [string]$Lamp, [string]$Detail) {
    $script:Rows.Add([pscustomobject]@{ step = $Step; lamp = $Lamp; detail = $Detail; at = (Get-Date -Format HH:mm:ss) })
    $color = switch ($Lamp) { 'GREEN' { 'Green' } 'YELLOW' { 'Yellow' } 'RED' { 'Red' } default { 'DarkGray' } }
    if ($Lamp -eq 'RED') { $script:Fails++ }
    Write-Host ("  [{0,-6}] {1,-10} {2}" -f $Lamp, $Step, $Detail) -ForegroundColor $color
}

# ---------- ① 找倉(本檔所在往上找 VIA_MCP_Engine;再退到 -Repo / 預設路徑) ----------
function Find-VIARepo([string]$Hint) {
    $cands = [System.Collections.Generic.List[string]]::new()
    if ($Hint) { $cands.Add($Hint) }
    $p = $PSScriptRoot
    while ($p -and (Split-Path $p -Parent)) { $cands.Add($p); $p = Split-Path $p -Parent }
    $cands.Add('C:\Users\tonyk\OneDrive\Documents\movies-dataset')
    $cands.Add((Join-Path $HOME 'OneDrive\Documents\movies-dataset'))
    $cands.Add((Join-Path $HOME 'Downloads\movies-dataset'))
    $cands.Add((Get-Location).Path)
    foreach ($c in $cands) {
        if ($c -and (Test-Path (Join-Path $c 'VIA_MCP_Engine')) -and (Test-Path (Join-Path $c 'VeritasIntelligenceAnalytics'))) { return (Resolve-Path $c).Path }
    }
    return $null
}
$RepoRoot = Find-VIARepo $Repo
if (-not $RepoRoot) {
    Write-Host "[VIA MCP] 找不到倉(要同時有 VIA_MCP_Engine\ 與 VeritasIntelligenceAnalytics\)。給 -Repo <倉根>,或把本檔放回 VeritasIntelligenceAnalytics\ 再跑。" -ForegroundColor Red
    Write-Host "          你剛才在 C:\Users\tonyk 打 git pull 會 fatal:那不是倉;倉在 OneDrive\Documents\movies-dataset 這類位置。" -ForegroundColor Yellow
    exit 3
}
$VIA = Join-Path $RepoRoot 'VeritasIntelligenceAnalytics'
Set-Location -LiteralPath $VIA
$LogDir = Join-Path $VIA 'VIA_Reports\mcp'; New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("mcp_" + $script:Stamp + ".log")
Write-Host ("[VIA MCP] 倉 {0} · 日誌 {1}" -f $RepoRoot, $LogFile) -ForegroundColor Cyan

# ---------- ② 加速 / 進度模組(有就用;缺就直呼 python,照實說) ----------
$PyProg = Join-Path $VIA 'supportive modules\VIA_PS_PyProgress_Module.ps1'
if (Test-Path $PyProg) { try { . $PyProg } catch { Write-Host "  [模組] VIA_PS_PyProgress_Module 點載失敗:$($_.Exception.Message)" -ForegroundColor Yellow } }
$script:HasPyProg = [bool](Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)
$script:HasScoped = [bool](Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue)
Write-Lamp '模組' $(if ($script:HasPyProg) { 'GREEN' } else { 'YELLOW' }) ("Invoke-VIAPython " + $(if ($script:HasPyProg) { '在(25 加速器 · 心跳 · 逾時)' } else { '缺 → 直呼 python' }) + " · Celeritas scoped " + $(if ($script:HasScoped) { '在' } else { '缺' }))

# ---------- ③ python 與尾版 ----------
function Find-Python([string]$Hint) {
    if ($Hint) { return $Hint }
    foreach ($n in @('python', 'python3')) { $c = Get-Command $n -ErrorAction SilentlyContinue; if ($c) { return $c.Source } }
    $py = Get-Command py -ErrorAction SilentlyContinue; if ($py) { return 'py' }
    return $null
}
$Py = Find-Python $Python
if (-not $Py) { Write-Lamp 'python' 'RED' '找不到 python / py(裝 Python 3.11+ 後再跑;本檔不代裝)'; exit 3 }
$PyArgs0 = @(); if ($Py -eq 'py') { $PyArgs0 = @('-3') }
$Console = Get-ChildItem -LiteralPath (Join-Path $VIA 'supportive modules\registry') -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File | Sort-Object { [int]([regex]::Match($_.Name, '_v(\d+)\.py$').Groups[1].Value) } | Select-Object -Last 1
$Engine = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'VIA_MCP_Engine') -Filter 'VIA_MCP_Engine_v*.py' -File | Sort-Object { [int]([regex]::Match($_.Name, '_v(\d+)\.py$').Groups[1].Value) } | Select-Object -Last 1

# ---------- 一步:VIA_FROM_VCGC=YES python <主控台尾版> mcp <子指令…>(有加速模組就經 Invoke-VIAPython;全文進日誌;回 rc) ----------
function Invoke-VIAMcp([string]$Step, [string[]]$McpArgs, [int]$Sec = 0, [switch]$Interactive) {
    $keep = @{ VIA_FROM_VCGC = $env:VIA_FROM_VCGC; PYTHONUTF8 = $env:PYTHONUTF8; PYTHONWARNINGS = $env:PYTHONWARNINGS; VIA_PANORAMA_AUTO = $env:VIA_PANORAMA_AUTO }
    $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'; $env:PYTHONWARNINGS = 'ignore'; $env:VIA_PANORAMA_AUTO = '0'
    $argv = @($Console.FullName, 'mcp') + $McpArgs
    $t0 = Get-Date
    Add-Content -LiteralPath $LogFile -Value ("=== [{0}] {1} · {2}" -f (Get-Date -Format HH:mm:ss), $Step, ($argv -join ' ')) -Encoding UTF8
    $rc = 0
    try {
        if ($Interactive) {
            # serve 要留在前景(Ctrl+C 結束)且要能開瀏覽器:直呼,不經心跳包裝
            & $Py @PyArgs0 @argv
            $rc = $LASTEXITCODE
        } elseif ($script:HasPyProg) {
            $body = { Invoke-VIAPython -Family core -Python $Py -TimeoutSec $Sec -Rest $argv }
            $out = if ($script:HasScoped) { Invoke-VIACeleritasScoped -Body $body } else { & $body }
            $rc = $global:LASTEXITCODE
            if ($out) { $out | Out-String | Add-Content -LiteralPath $LogFile -Encoding UTF8 }
        } else {
            $out = & $Py @PyArgs0 @argv 2>&1
            $rc = $LASTEXITCODE
            if ($out) { $out | Out-String | Add-Content -LiteralPath $LogFile -Encoding UTF8; $out | ForEach-Object { Write-Host ("    " + $_) } }
        }
    } catch {
        $rc = 1; Add-Content -LiteralPath $LogFile -Value ("[例外] " + $_.Exception.Message) -Encoding UTF8; Write-Host ("    [例外] " + $_.Exception.Message) -ForegroundColor Red
    } finally {
        foreach ($k in $keep.Keys) { $v = $keep[$k]; if ($null -eq $v -or $v -eq '') { Remove-Item "Env:$k" -ErrorAction SilentlyContinue } else { Set-Item "Env:$k" $v } }
    }
    $sec = [Math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    Add-Content -LiteralPath $LogFile -Value ("--- rc {0} · {1}s" -f $rc, $sec) -Encoding UTF8
    return [pscustomobject]@{ rc = $rc; sec = $sec }
}

# ---------- 短令(只寫自己的 $PROFILE;L70:不碰 Register / Override / Launch) ----------
function Install-VIAMcpShortcut {
    $marker = '# [VIA-MCP-SHORTCUT v0100]'
    $line = "$marker function via-mcp { & pwsh -ExecutionPolicy Bypass -File '" + $PSCommandPath + "' @args }"
    $prof = $PROFILE
    if (-not (Test-Path $prof)) { New-Item -ItemType File -Force -Path $prof | Out-Null }
    $cur = Get-Content -LiteralPath $prof -Raw -ErrorAction SilentlyContinue
    if ($cur -and $cur.Contains($marker)) {
        $cur = ($cur -split "`r?`n" | Where-Object { -not $_.StartsWith($marker) }) -join [Environment]::NewLine
        Set-Content -LiteralPath $prof -Value $cur -Encoding UTF8
    }
    Add-Content -LiteralPath $prof -Value $line -Encoding UTF8
    Write-Lamp '短令' 'GREEN' ("via-mcp 已寫進 " + $prof + "(新視窗生效;或現在打 . `$PROFILE)。移除:刪掉那一行即可")
    Write-Host ("    之後任何資料夾都可以打:via-mcp · via-mcp -Action serve · via-mcp -Action token -TokenSource store -TokenRepo owner/repo") -ForegroundColor Cyan
}

# ---------- 預設五個 MCP(每平台上限 5;已有的名稱不重加) ----------
function Get-VIAMcpAssigned([string]$Plat) {
    # list 很快且只讀:直呼 python 抓輸出(不經心跳包裝,保證拿得到文字),一併記進日誌
    $keep = $env:VIA_FROM_VCGC; $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'
    try { $txt = (& $Py @PyArgs0 $Console.FullName 'mcp' 'list' 2>&1 | Out-String) } catch { $txt = '' }
    finally { if ($null -eq $keep -or $keep -eq '') { Remove-Item Env:VIA_FROM_VCGC -ErrorAction SilentlyContinue } else { $env:VIA_FROM_VCGC = $keep } }
    Add-Content -LiteralPath $LogFile -Value ("=== list`n" + $txt) -Encoding UTF8
    $m = [regex]::Match($txt, [regex]::Escape($Plat) + '\((\d+)/\d+\):([^\r\n]*)', 'RightToLeft')
    if ($m.Success) { return @(($m.Groups[2].Value -split ',\s*') | Where-Object { $_ }) }
    return @()
}
function Invoke-VIAMcpSetup([string]$Plat, [string]$Kind) {
    $docs = [Environment]::GetFolderPath('MyDocuments')
    $research = Join-Path $HOME 'Research'
    $root = if ($Kind -eq 'research' -and (Test-Path $research)) { $research } else { $docs }
    $plan = @(
        @{ id = 'filesystem'; args = @("paths=$root") },
        @{ id = 'memory'; args = @() },
        @{ id = 'fetch'; args = @() },
        @{ id = 'sequential-thinking'; args = @() },
        @{ id = 'github'; args = @() }
    )
    if ($Kind -eq 'research') { $plan[3] = @{ id = 'git'; args = @("repository=$RepoRoot") } }
    $have = Get-VIAMcpAssigned $Plat
    $added = 0; $skipped = 0
    foreach ($p in $plan) {
        if ($have -contains $p.id) { $skipped++; continue }
        if (($have.Count + $added) -ge 5) { Write-Lamp 'setup' 'YELLOW' ("已滿 5 個,略過 " + $p.id); continue }
        $r = Invoke-VIAMcp ('add ' + $p.id) (@('add', $Plat, $p.id) + $p.args) 120
        if ($r.rc -eq 0) { $added++ } else { Write-Lamp 'setup' 'RED' ("add " + $p.id + " rc " + $r.rc + "(看日誌)") }
    }
    Write-Lamp 'setup' $(if ($added -or $skipped) { 'GREEN' } else { 'YELLOW' }) ("{0}:新加 {1} · 已有 {2} · 資料夾 {3}" -f $Plat, $added, $skipped, $root)
}

# ---------- 主體 ----------
Write-Host ""
Write-Host ("VIA MCP Engine 一鍵(v0100)· Action={0} · Platform={1}" -f $Action, $Platform) -ForegroundColor Cyan
if (-not $Console) { Write-Lamp '尾版' 'RED' '找不到 CGC_MDL149_VeritasCentralGovernanceConsole_v*.py(先 git pull)'; exit 3 }
if (-not $Engine) { Write-Lamp '尾版' 'RED' '找不到 VIA_MCP_Engine\VIA_MCP_Engine_v*.py(先 git pull;需要 main 已含 PR #593)' }
else { Write-Lamp '尾版' 'GREEN' ("主控台 " + $Console.Name + " · 引擎 " + $Engine.Name + " · python " + $Py) }

if ($InstallShortcut) { Install-VIAMcpShortcut }

# ① git pull(--ff-only;在倉根;不是倉就照實說)
if ($Action -in @('all', 'pull') -and -not $NoPull) {
    if (Test-Path (Join-Path $RepoRoot '.git')) {
        $git = Get-Command git -ErrorAction SilentlyContinue
        if ($git) {
            $before = (& git -C $RepoRoot rev-parse --short HEAD 2>$null)
            $pull = & git -C $RepoRoot pull --ff-only 2>&1
            $after = (& git -C $RepoRoot rev-parse --short HEAD 2>$null)
            $pull | Out-String | Add-Content -LiteralPath $LogFile -Encoding UTF8
            if ($LASTEXITCODE -eq 0) { Write-Lamp 'pull' 'GREEN' ("{0} → {1}" -f $before, $after) }
            else { Write-Lamp 'pull' 'YELLOW' ("git pull 回 rc {0}(本機有改動或非 ff;看日誌;照舊版繼續)" -f $LASTEXITCODE) }
            # pull 後尾版可能換了,重取
            $Console = Get-ChildItem -LiteralPath (Join-Path $VIA 'supportive modules\registry') -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File | Sort-Object { [int]([regex]::Match($_.Name, '_v(\d+)\.py$').Groups[1].Value) } | Select-Object -Last 1
            $Engine = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'VIA_MCP_Engine') -Filter 'VIA_MCP_Engine_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object { [int]([regex]::Match($_.Name, '_v(\d+)\.py$').Groups[1].Value) } | Select-Object -Last 1
        } else { Write-Lamp 'pull' 'YELLOW' '沒有 git 指令(照本機現況繼續)' }
    } else { Write-Lamp 'pull' 'YELLOW' ($RepoRoot + ' 不是 git 倉(.git 不在;OneDrive 同步夾?)照現況繼續') }
}
if (-not $Engine) { Write-Host "[VIA MCP] 引擎不在,後面做不了。先在倉根 git pull。" -ForegroundColor Red; exit 3 }
if ($Action -eq 'pull') { exit $(if ($script:Fails) { 1 } else { 0 }) }

# ② 短卡 / doctor / selftest
if ($Action -in @('all', 'card')) { $r = Invoke-VIAMcp 'card' @() 120; Write-Lamp 'card' $(if ($r.rc -eq 0) { 'GREEN' } else { 'RED' }) ("mcp 短卡 rc {0} · {1}s" -f $r.rc, $r.sec) }
if ($Action -in @('all', 'doctor')) { $r = Invoke-VIAMcp 'doctor' @('doctor') 300; Write-Lamp 'doctor' $(if ($r.rc -eq 0) { 'GREEN' } else { 'RED' }) ("環境偵測 rc {0} · {1}s(詳見日誌:node / npx / uvx / docker / 憑證管理員 / 各平台設定檔)" -f $r.rc, $r.sec) }
if ($Action -eq 'selftest') { $r = Invoke-VIAMcp 'selftest' @('selftest') 600; Write-Lamp 'selftest' $(if ($r.rc -eq 0) { 'GREEN' } else { 'RED' }) ("引擎離線自測 rc {0} · {1}s" -f $r.rc, $r.sec) }

# ③ 預設五個(setup;all 時只在平台還是空的、或有 -Preset 才加)
if ($Action -eq 'setup' -or ($Action -eq 'all' -and $Preset)) { Invoke-VIAMcpSetup $Platform $(if ($Preset) { $Preset } else { 'basic' }) }
elseif ($Action -eq 'all') {
    $have = Get-VIAMcpAssigned $Platform
    if ($have.Count -eq 0) { Invoke-VIAMcpSetup $Platform 'basic' } else { Write-Lamp 'setup' 'GREEN' ("{0} 已有 {1} 個:{2}(要重設用 -Action setup -Preset basic)" -f $Platform, $have.Count, ($have -join ', ')) }
}

# ④ probe 真啟動(第一次 npx / uvx 會先下載套件)
if ($Action -in @('all', 'probe') -and -not $NoProbe) {
    $r = Invoke-VIAMcp 'probe' @('probe', $Platform, '--timeout', "$ProbeTimeoutSec") ($ProbeTimeoutSec * 6)
    Write-Lamp 'probe' $(if ($r.rc -eq 0) { 'GREEN' } elseif ($r.rc -eq 2) { 'YELLOW' } else { 'RED' }) ("真啟動 {0} 的每一個 MCP rc {1} · {2}s(rc 1 = 有 MCP 啟不來,日誌有 stderr;rc 2 = 平台沒有 MCP)" -f $Platform, $r.rc, $r.sec)
}

# ⑤ apply:先乾跑;-Apply 才真寫(先備份)
if ($Action -in @('all', 'apply')) {
    $r = Invoke-VIAMcp 'apply --dry-run' @('apply', $Platform, '--dry-run') 300
    Write-Lamp 'apply' $(if ($r.rc -eq 0) { 'GREEN' } else { 'RED' }) ("乾跑 rc {0}(合併預覽在日誌)" -f $r.rc)
    if ($Apply -and $r.rc -eq 0) {
        $r2 = Invoke-VIAMcp 'apply' @('apply', $Platform) 300
        Write-Lamp 'apply' $(if ($r2.rc -eq 0) { 'GREEN' } else { 'RED' }) ("真寫 rc {0}(舊檔備份在 ~\.via_mcp_engine\backups;重啟該 AI 應用後生效)" -f $r2.rc)
    } elseif (-not $Apply) { Write-Lamp 'apply' 'YELLOW' '只乾跑;要真寫加 -Apply(或在頁面按「套用」)' }
}

# ⑥ token:檢查 + 唯讀驗證(Token 只從環境變數 / 憑證管理員;本檔不收、不印、不寫)
if ($Action -in @('all', 'token')) {
    $haveTok = ($TokenSource -eq 'store') -or [bool]$env:GITHUB_PERSONAL_ACCESS_TOKEN
    if (-not $haveTok -and $Action -eq 'all') { Write-Lamp 'token' 'YELLOW' '沒有 GITHUB_PERSONAL_ACCESS_TOKEN,也沒指定 -TokenSource store;略過(要測:cmdkey /generic:GITHUB_PAT_READONLY /user:via /pass:<Token> 再 -TokenSource store)' }
    else {
        $r = Invoke-VIAMcp 'token check' @('token', 'check', '--source', $TokenSource) 120
        Write-Lamp 'token' $(if ($r.rc -eq 0) { 'GREEN' } else { 'RED' }) ("Token 類型 / scope / 到期 rc {0}" -f $r.rc)
        if ($TokenRepo) {
            $r2 = Invoke-VIAMcp 'token readonly-test' @('token', 'readonly-test', '--source', $TokenSource, '--repo', $TokenRepo) 300
            Write-Lamp 'token' $(if ($r2.rc -eq 0) { 'GREEN' } else { 'RED' }) ("唯讀驗證 {0}:rc {1}(0 = READONLY_OK;1 = 可寫或讀失敗,寫入痕跡已自動清理;證據在 ~\.via_mcp_engine\evidence)" -f $TokenRepo, $r2.rc)
        } elseif ($Action -eq 'token') { Write-Lamp 'token' 'YELLOW' '沒給 -TokenRepo owner/repo,只做檢查沒做唯讀驗證' }
    }
}

# ---------- 結尾矩陣 + 判決行 ----------
Write-Host ""
Write-Host ("  {0,-8} {1,-10} {2}" -f '燈', '步', '細節') -ForegroundColor DarkGray
foreach ($row in $script:Rows) { Write-Host ("  {0,-8} {1,-10} {2}" -f $row.lamp, $row.step, $row.detail) -ForegroundColor $(switch ($row.lamp) { 'GREEN' { 'Green' } 'YELLOW' { 'Yellow' } 'RED' { 'Red' } default { 'DarkGray' } }) }
$lamp = if ($script:Fails) { 'RED' } elseif (($script:Rows | Where-Object { $_.lamp -eq 'YELLOW' }).Count) { 'YELLOW' } else { 'GREEN' }
Write-Host ("[計] Invoke-VIA-MCP v0100 · {0} · 步 {1} · 紅 {2} · 日誌 {3}" -f $lamp, $script:Rows.Count, $script:Fails, $LogFile) -ForegroundColor $(if ($lamp -eq 'GREEN') { 'Green' } elseif ($lamp -eq 'YELLOW') { 'Yellow' } else { 'Red' })
$script:Rows | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $LogDir ("mcp_" + $script:Stamp + ".json")) -Encoding UTF8

# ⑦ serve:滑鼠操作頁(前景;Ctrl+C 結束;引擎自己開瀏覽器)
if ($Action -in @('all', 'serve') -and -not $NoOpen) {
    Write-Host ""
    Write-Host ("[VIA MCP] 開頁 http://127.0.0.1:{0}/ … 點平台 → 按 + → ▶ 測試啟動 → 套用;Ctrl+C 結束" -f $Port) -ForegroundColor Cyan
    $r = Invoke-VIAMcp 'serve' @('serve', '--port', "$Port") 0 -Interactive
    exit $r.rc
}
exit $(if ($script:Fails) { 1 } else { 0 })
