#Requires -Version 7.4
# ==============================================================================
# VIA_ProfileLoader_v0102.ps1  —  VIA 現代化雙引擎啟動外殼(薄層)· 作廢 v0100 / v0101
# 全邏輯在 Python,PS 只負責:進環境 + 授權 + 呼叫各系統 Python 入口 + 現代化 TUI + 選擇題。
# v0102:選單選項去掉方括號 —— PwshSpectreConsole 會把選項裡的方括號當顏色標記解析而報
#        「Could not find color or style」(工作站 2026-11-23 實錄 · Spectre 2.3.0);其餘與 v0101 一致。
# v0101 新增(操作員 2026-11-23「PS 也一起授權寫進去 TO HANDLE ALL」):
#   via-auth  授權:FRED key 以遮罩輸入存「Windows 使用者層」環境變數(不寫檔、不入 git、不顯示明碼)
#   via-run   全線:由你當場輸入 YES 開本次同意閘(只在本行程,跑完即關)→ VDF launch --run → VRN MDL260 run
# 路徑一律用 $PSScriptRoot / $env:VIA_ROOT,入口以檔名找尾版(桌機與倉兩種目錄結構都可用),不寫死本機路徑。
# 交給操作員的 PS 只有這一支。寫入 $PROFILE 前請先照 UAT 測過。緊急逃生:pwsh -NoProfile
# ==============================================================================
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
Import-Module PwshSpectreConsole -ErrorAction SilentlyContinue

# --- 1. VIA 根目錄與 Python ---
if ([string]::IsNullOrWhiteSpace($env:VIA_ROOT)) { $env:VIA_ROOT = $PSScriptRoot }
$PyCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }

function Find-ViaTail {
    # 以檔名找某家族尾版(排除退役 / 收容 / 副本 / 輸出夾);找不到回 $null
    param([Parameter(Mandatory)][string]$Pattern, [int]$Depth = 5)
    $skip = 'RetiredEngines|intake|SCOPE_COPY|ASSETS|_archive|_superseded|references|backups|vcgc_hub'
    Get-ChildItem -Path $env:VIA_ROOT -Filter $Pattern -Recurse -Depth $Depth -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch $skip } |
        Sort-Object Name | Select-Object -Last 1 | ForEach-Object { $_.FullName }
}

$ViaHubPy = Find-ViaTail 'VCGC_CommandHub_v*.py' 1
if (-not $ViaHubPy) { $ViaHubPy = Join-Path $PSScriptRoot 'VCGC_CommandHub_v0100.py' }

# --- 2. 自動掛載 via_* 虛擬環境(若存在) ---
foreach ($v in @(
        (Join-Path $env:VIA_ROOT '.venv\Scripts\Activate.ps1'),
        (Join-Path $env:USERPROFILE 'venvs\via_core\Scripts\Activate.ps1'))) {
    if (Test-Path $v) { . $v; break }
}

# --- 3. 核心短指令(薄層轉呼叫 Python) ---
function via-pano {
    param([switch]$Apply, [string]$Scope)
    $a = @($ViaHubPy, 'pano')
    if ($Apply) { $a += '--apply' }
    if (-not [string]::IsNullOrWhiteSpace($Scope)) { $a += @('--scope', $Scope) }
    & $PyCmd @a
}
function via-bak {
    param([string]$Note = 'PS Active Checkpoint')
    & $PyCmd $ViaHubPy bak --note $Note
}
function via-ast {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Target,
        [string]$Symbol, [string]$CodeFile, [switch]$Clipboard, [string]$Code,
        [switch]$Rollback, [switch]$Yes
    )
    $a = @($ViaHubPy, 'ast', '--target', $Target)
    if ($Rollback) { $a += '--rollback' }
    if ($Yes) { $a += '--yes' }
    if (-not [string]::IsNullOrWhiteSpace($Symbol)) { $a += @('--symbol', $Symbol) }
    if (-not $Rollback) {
        if (-not [string]::IsNullOrWhiteSpace($CodeFile)) { $a += @('--code-file', $CodeFile) }
        elseif (-not [string]::IsNullOrWhiteSpace($Code)) { $a += @('--code', $Code) }
        else { $a += '--clipboard' }
    }
    & $PyCmd @a
}

# --- 4. 授權:via-auth(FRED key 只進使用者層環境變數;不寫檔、不顯示明碼) ---
function Get-ViaMask([string]$s) {
    if ([string]::IsNullOrEmpty($s)) { return '未設定' }
    return ('已設定(…' + $s.Substring([Math]::Max(0, $s.Length - 4)) + ',長度 ' + $s.Length + ')')
}
function via-auth {
    [CmdletBinding()]
    param([switch]$Fred, [switch]$Clear)
    if ($Clear) {
        [Environment]::SetEnvironmentVariable('FRED_API_KEY', $null, 'User')
        Remove-Item Env:FRED_API_KEY -ErrorAction SilentlyContinue
        Write-Host '[授權] FRED_API_KEY 已自使用者層移除。' -ForegroundColor Yellow
    }
    if ($Fred) {
        $sec = Read-Host -AsSecureString '貼上 FRED API key(輸入不顯示)'
        $plain = (ConvertFrom-SecureString -SecureString $sec -AsPlainText).Trim()
        if ($plain -notmatch '^[0-9a-f]{32}$') {
            Write-Host '[授權] 格式不符(FRED key 應為 32 位小寫十六進位),未儲存。' -ForegroundColor Red
            return
        }
        [Environment]::SetEnvironmentVariable('FRED_API_KEY', $plain, 'User')
        $env:FRED_API_KEY = $plain
        $plain = $null
        Write-Host '[授權] FRED_API_KEY 已存入 Windows 使用者層(本視窗立即生效;已開的其他程式需重開才讀得到)。' -ForegroundColor Green
        Write-Host '        ⚠ 若有 claude remote-control 正在跑,請 Ctrl+C 後重開,工作站 session 才吃得到。' -ForegroundColor DarkYellow
    }
    $userFred = [Environment]::GetEnvironmentVariable('FRED_API_KEY', 'User')
    Write-Host ''
    Write-Host '  授權狀態' -ForegroundColor Cyan
    Write-Host ('  FRED_API_KEY(使用者層) : ' + (Get-ViaMask $userFred))
    Write-Host ('  FRED_API_KEY(本視窗)   : ' + (Get-ViaMask $env:FRED_API_KEY))
    Write-Host ('  VIA_NET_CONSENT         : ' + $(if ($env:VIA_NET_CONSENT -eq 'YES') { '開(本視窗)' } else { '關(via-run 時由你當場開)' }))
    Write-Host ''
}

# --- 5. 全線:via-run(同意閘每次由你當場開,只在本行程,跑完即關) ---
function via-run {
    [CmdletBinding()]
    param(
        [switch]$VdfOnly, [switch]$VrnOnly,
        [string]$VrnSource = (Join-Path $env:VIA_ROOT 'private\vrn_samples'),
        [string]$ViaDb = (Join-Path $env:VIA_ROOT 'via_database'),
        [switch]$Yes
    )
    $vdf = Find-ViaTail 'VDF_SystemManager_v*.py'
    $vrn = Find-ViaTail 'VRN_MDL260_SafeParallelLaunch_v*.py'
    Write-Host ''
    Write-Host '  全線啟動計畫' -ForegroundColor Cyan
    Write-Host ('  VDF 入口 : ' + $(if ($vdf) { Split-Path $vdf -Leaf } else { '找不到(VDF_SystemManager_v*.py)' }))
    Write-Host ('  VRN 入口 : ' + $(if ($vrn) { Split-Path $vrn -Leaf } else { '找不到(VRN_MDL260_SafeParallelLaunch_v*.py)' }))
    Write-Host ('  VRN 報告 : ' + $VrnSource + $(if (Test-Path $VrnSource) { '' } else { '(不存在)' }))
    Write-Host ('  資料庫   : ' + $ViaDb + $(if (Test-Path $ViaDb) { '' } else { '(不存在)' }))
    Write-Host ('  FRED key : ' + (Get-ViaMask $env:FRED_API_KEY) + '(沒有也能跑,FRED 序列會照實標黃)')
    Write-Host ''
    if (-not $Yes) {
        $ans = Read-Host '本次要開網路同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)並開始擷取?輸入 YES 繼續'
        if ($ans -cne 'YES') { Write-Host '[取消] 同意閘未開,未擷取。' -ForegroundColor Yellow; return }
    }
    $env:VIA_NET_CONSENT = 'YES'
    $env:VIA_SCRAPE_CONSENT = 'YES'
    $sum = [ordered]@{}
    try {
        if (-not $VrnOnly) {
            if ($vdf) {
                $t = [Diagnostics.Stopwatch]::StartNew()
                & $PyCmd $vdf launch --run
                $sum['VDF launch --run'] = "rc $LASTEXITCODE · $([Math]::Round($t.Elapsed.TotalMinutes,1)) 分"
            } else { $sum['VDF'] = '入口找不到,略過' }
        }
        if (-not $VdfOnly) {
            if ($vrn -and (Test-Path $VrnSource)) {
                $t = [Diagnostics.Stopwatch]::StartNew()
                & $PyCmd $vrn run --source $VrnSource --via-db $ViaDb
                $sum['VRN MDL260 run'] = "rc $LASTEXITCODE · $([Math]::Round($t.Elapsed.TotalMinutes,1)) 分"
            } else { $sum['VRN'] = '入口或報告夾不在,略過' }
        }
    } finally {
        Remove-Item Env:VIA_NET_CONSENT, Env:VIA_SCRAPE_CONSENT -ErrorAction SilentlyContinue
        Write-Host ''
        Write-Host '  全線結果(同意閘已關)' -ForegroundColor Cyan
        foreach ($k in $sum.Keys) { Write-Host ("  {0,-18} {1}" -f $k, $sum[$k]) }
        Write-Host ''
    }
}

# 向下相容:舊短指令導向新指令(避免肌肉記憶報錯)
Set-Alias -Name via-status       -Value via        -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-six          -Value via-pano   -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-panorama-all -Value via-pano   -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-lanes        -Value via-pano   -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-vdffetch     -Value via-run    -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-vrnrun       -Value via-run    -Scope Global -ErrorAction SilentlyContinue

# --- 6. 進入 PS 時的 VIA 主控台(頂部矩陣 + 選擇題 / 直接貼上雙軌) ---
function via {
    Clear-Host
    if (Get-Command Invoke-SpectreCommandWithStatus -ErrorAction SilentlyContinue) {
        Invoke-SpectreCommandWithStatus -Spinner 'Dots' -Title '喚醒 VIA 環境與載入前次備份...' -ScriptBlock {
            Start-Sleep -Milliseconds 250
        }
    }
    if (Test-Path $ViaHubPy) { & $PyCmd $ViaHubPy boot }
    else { Write-Host "[WARN] 找不到 $ViaHubPy" -ForegroundColor Yellow }
    Write-Host '  另有:via-auth(授權 FRED key / 看授權狀態)· via-run(開同意閘 → VDF → VRN 全線)' -ForegroundColor DarkCyan

    $choices = @(
        '1. 原生指令列 · 立即進入終端機(可直接貼上 / 輸入指令)',
        '2. via-pano · 全景檢視 GitHub + PC File,一輪 AST 修復(乾跑)',
        '3. via-bak · 主動備份 + Graphify + OmniRoute + agency-mem',
        '4. via-ast · AST 導入加速器(剪貼簿 / 檔案,diff 預覽後注入)',
        '5. via-auth · 授權:設定 FRED key / 查看授權狀態',
        '6. via-run · 全線啟動:開同意閘 → VDF 擷取 → VRN 解析(跑完自動關閘)'
    )
    if (Get-Command Read-SpectreSelection -ErrorAction SilentlyContinue) {
        $choice = Read-SpectreSelection -Title "`n[bold #88C0D0]請選擇操作模式(直接按 Enter 進入指令列供貼上/輸入):[/]" -Choices $choices
    } else {
        $choices | ForEach-Object { Write-Host "  $_" }
        $n = Read-Host '輸入編號(直接 Enter = 1)'
        $choice = if ([string]::IsNullOrWhiteSpace($n)) { '1.' } else { "$n." }
    }
    switch -Wildcard ($choice) {
        '2.*' { via-pano }
        '3.*' {
            $note = Read-Host '輸入備份焦點備註(直接 Enter 用預設)'
            if ([string]::IsNullOrWhiteSpace($note)) { via-bak } else { via-bak -Note $note }
        }
        '4.*' {
            $t = Read-Host '目標 Python 檔案路徑'
            $s = Read-Host '指定單一符號(直接 Enter 自動偵測全部函式/類別)'
            $cf = Read-Host '來源 .py 檔路徑(直接 Enter = 讀剪貼簿)'
            $p = @{ Target = $t }
            if (-not [string]::IsNullOrWhiteSpace($s)) { $p.Symbol = $s }
            if ([string]::IsNullOrWhiteSpace($cf)) { $p.Clipboard = $true } else { $p.CodeFile = $cf }
            via-ast @p
        }
        '5.*' {
            $f = Read-Host '要設定 / 更新 FRED key 嗎?(y/N)'
            if ($f -match '^[yY]') { via-auth -Fred } else { via-auth }
        }
        '6.*' { via-run }
    }
    Write-Host "`e[38;2;163;190;140m✔ VIA 已就緒｜可直接貼上/輸入指令(隨時輸入 via 重開選單)`e[0m`n"
}

# 進入 PowerShell 自動啟動 VIA 主控台
via
