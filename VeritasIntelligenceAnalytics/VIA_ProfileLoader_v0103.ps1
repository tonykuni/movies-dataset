#Requires -Version 7.4
# ==============================================================================
# VIA_ProfileLoader_v0103.ps1  —  VIA 現代化雙引擎啟動外殼(薄層)· 作廢 v0100 / v0101 / v0102
# 全邏輯在 Python,PS 只負責:進環境 + 授權 + 呼叫各系統 Python 入口 + 現代化 TUI + 選擇題。
# v0103(工作站實錄:舊設定把 VIA_ROOT 指回 git 倉 → 找不到中樞;要常態掛 $PROFILE 且不能弄壞 PS):
#   ① 伴隨檔(中樞)先找 $PSScriptRoot,再找各根;不改動既有 $env:VIA_ROOT(舊工具照舊可用)
#   ② 入口搜尋兩棵樹:使用者層 VIA_ROOT(母系統)→ 本視窗 VIA_ROOT → $env:VIA_CODE_ROOT → $PSScriptRoot
#   ③ 只有互動式終端才自動開選單;-Command / -File / 非互動 / Claude Code 子行程 / VIA_NO_MENU 一律不開
#   ④ 舊短指令別名只在「沒有同名指令」時才設,不蓋掉原有功能
#   ⑤ via-setup:備份 $PROFILE → 寫標記區塊(try/catch 包住)→ 連續 3 次子行程載入檢查 + 剖析 + -NoProfile 逃生,任一失敗自動還原
#   ⑥ via-bak 先警告母系統很大、需確認
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
# 資料根 = 使用者層 VIA_ROOT(母系統)優先;不改動本視窗既有 $env:VIA_ROOT(舊工具照舊)
$ViaDataRoot = [Environment]::GetEnvironmentVariable('VIA_ROOT', 'User')
if ([string]::IsNullOrWhiteSpace($ViaDataRoot) -or -not (Test-Path $ViaDataRoot)) { $ViaDataRoot = $env:VIA_ROOT }
$ViaSearchRoots = @($ViaDataRoot, $env:VIA_ROOT, $env:VIA_CODE_ROOT, $PSScriptRoot) |
    Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

function Find-ViaTail {
    # 依序在各根找某家族尾版(排除退役 / 收容 / 副本 / 輸出夾);第一個有命中的根勝出;找不到回 $null
    param([Parameter(Mandatory)][string]$Pattern, [int]$Depth = 5, [string[]]$Roots = $ViaSearchRoots)
    $skip = 'RetiredEngines|intake|SCOPE_COPY|ASSETS|_archive|_superseded|references|backups|vcgc_hub'
    foreach ($r in $Roots) {
        $hit = Get-ChildItem -Path $r -Filter $Pattern -Recurse -Depth $Depth -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch $skip } | Sort-Object Name | Select-Object -Last 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

$ViaHubPy = Find-ViaTail 'VCGC_CommandHub_v*.py' 1 @($PSScriptRoot) 
if (-not $ViaHubPy) { $ViaHubPy = Find-ViaTail 'VCGC_CommandHub_v*.py' 1 }

function Invoke-ViaHub {
    # 中樞以資料根為 VIA_ROOT 執行(狀態寫在資料根),結束後還原本視窗原值
    $old = $env:VIA_ROOT
    try { $env:VIA_ROOT = $ViaDataRoot; & $PyCmd $ViaHubPy @args } finally { $env:VIA_ROOT = $old }
}

# --- 2. 自動掛載 via_* 虛擬環境(若存在) ---
foreach ($v in @(
        (Join-Path $env:VIA_ROOT '.venv\Scripts\Activate.ps1'),
        (Join-Path $env:USERPROFILE 'venvs\via_core\Scripts\Activate.ps1'))) {
    if (Test-Path $v) { . $v; break }
}

# --- 3. 核心短指令(薄層轉呼叫 Python) ---
function via-pano {
    param([switch]$Apply, [string]$Scope)
    $a = @('pano')
    if ($Apply) { $a += '--apply' }
    if (-not [string]::IsNullOrWhiteSpace($Scope)) { $a += @('--scope', $Scope) }
    Invoke-ViaHub @a
}
function via-bak {
    param([string]$Note = 'PS Active Checkpoint', [switch]$Yes)
    if (-not $Yes) {
        Write-Host ('[via-bak] 會把資料根(' + $ViaDataRoot + ')下所有 .py/.ps1/.json/.md/.toml 整份複製成快照;') -ForegroundColor DarkYellow
        Write-Host '          母系統很大又在 OneDrive,會吃空間與同步流量。' -ForegroundColor DarkYellow
        if ((Read-Host '確定執行?輸入 YES') -cne 'YES') { Write-Host '[取消] 未備份。' -ForegroundColor Yellow; return }
    }
    Invoke-ViaHub @('bak', '--note', $Note)
}
function via-ast {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Target,
        [string]$Symbol, [string]$CodeFile, [switch]$Clipboard, [string]$Code,
        [switch]$Rollback, [switch]$Yes
    )
    $a = @('ast', '--target', $Target)
    if ($Rollback) { $a += '--rollback' }
    if ($Yes) { $a += '--yes' }
    if (-not [string]::IsNullOrWhiteSpace($Symbol)) { $a += @('--symbol', $Symbol) }
    if (-not $Rollback) {
        if (-not [string]::IsNullOrWhiteSpace($CodeFile)) { $a += @('--code-file', $CodeFile) }
        elseif (-not [string]::IsNullOrWhiteSpace($Code)) { $a += @('--code', $Code) }
        else { $a += '--clipboard' }
    }
    Invoke-ViaHub @a
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
        [string]$VrnSource = (Join-Path $ViaDataRoot 'private\vrn_samples'),
        [string]$ViaDb = (Join-Path $ViaDataRoot 'via_database'),
        [switch]$Yes
    )
    $vdf = Find-ViaTail 'VDF_SystemManager_v*.py'
    $vrn = Find-ViaTail 'VRN_MDL260_SafeParallelLaunch_v*.py'
    Write-Host ''
    Write-Host '  全線啟動計畫' -ForegroundColor Cyan
    Write-Host ('  搜尋根   : ' + ($ViaSearchRoots -join ' | '))
    Write-Host ('  VDF 入口 : ' + $(if ($vdf) { $vdf } else { '找不到(VDF_SystemManager_v*.py)' }))
    Write-Host ('  VRN 入口 : ' + $(if ($vrn) { $vrn } else { '找不到(VRN_MDL260_SafeParallelLaunch_v*.py)' }))
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

# 向下相容:舊短指令導向新指令 —— 只在「沒有同名指令」時才設,不蓋掉原有功能
foreach ($pair in @(@('via-status', 'via'), @('via-six', 'via-pano'), @('via-panorama-all', 'via-pano'),
                    @('via-lanes', 'via-pano'), @('via-vdffetch', 'via-run'), @('via-vrnrun', 'via-run'))) {
    if (-not (Get-Command $pair[0] -ErrorAction SilentlyContinue)) {
        Set-Alias -Name $pair[0] -Value $pair[1] -Scope Global -ErrorAction SilentlyContinue
    }
}

# --- 5b. 常態設定:via-setup(備份 → 寫標記區塊 → 多次檢查 → 失敗自動還原) ---
$ViaProfileBegin = '# >>> VIA LOADER (managed by via-setup) >>>'
$ViaProfileEnd = '# <<< VIA LOADER <<<'
function Get-ViaProfileBlock {
    @"
$ViaProfileBegin
try {
    `$__viaRoot = [Environment]::GetEnvironmentVariable('VIA_ROOT', 'User')
    if (`$__viaRoot -and -not `$env:VIA_NO_LOADER -and (Test-Path `$__viaRoot)) {
        `$__viaL = Get-ChildItem -LiteralPath `$__viaRoot -Filter 'VIA_ProfileLoader_v*.ps1' -File -ErrorAction SilentlyContinue |
            Sort-Object Name | Select-Object -Last 1
        if (`$__viaL) { . `$__viaL.FullName }
    }
} catch {
    Write-Host "[VIA] loader 載入失敗,已略過(PS 照常可用):`$(`$_.Exception.Message)" -ForegroundColor DarkYellow
}
$ViaProfileEnd
"@
}
function Remove-ViaProfileBlock([string]$text) {
    $pat = '(?s)\r?\n?' + [regex]::Escape($ViaProfileBegin) + '.*?' + [regex]::Escape($ViaProfileEnd) + '\r?\n?'
    return [regex]::Replace($text, $pat, "`n")
}
function Test-ViaProfile {
    # 回傳 @{ ok = bool; lines = string[] };檢查 3 次子行程載入 + 剖析 + -NoProfile 逃生
    $lines = @(); $ok = $true
    $errs = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($PROFILE, [ref]$null, [ref]$errs)
    if ($errs.Count -eq 0) { $lines += '  [OK] ① $PROFILE 語法剖析 0 錯' } else { $ok = $false; $lines += "  [FAIL] ① 剖析錯 $($errs.Count):$($errs[0].Message)" }
    $pw = (Get-Process -Id $PID).Path
    foreach ($i in 1..3) {
        $t = [Diagnostics.Stopwatch]::StartNew()
        $out = & $pw -NoLogo -Command "if (Get-Command via-run -ErrorAction SilentlyContinue) { 'VIA_OK' } else { 'VIA_MISSING' }" 2>&1 | Out-String
        $ms = [int]$t.Elapsed.TotalMilliseconds
        if ($LASTEXITCODE -eq 0 -and $out -match 'VIA_OK') { $lines += "  [OK] ②-$i 新開 pwsh 載入 profile → via 指令就緒($ms ms,未跳選單)" }
        else { $ok = $false; $lines += "  [FAIL] ②-$i 新開 pwsh 載入失敗(rc $LASTEXITCODE):$($out.Trim() -replace '\s+',' ')" }
    }
    $np = & $pw -NoLogo -NoProfile -Command "'NOPROFILE_OK'" 2>&1 | Out-String
    if ($np -match 'NOPROFILE_OK') { $lines += '  [OK] ③ 逃生閥 pwsh -NoProfile 正常' } else { $ok = $false; $lines += '  [FAIL] ③ -NoProfile 異常' }
    return @{ ok = $ok; lines = $lines }
}
function via-setup {
    [CmdletBinding()]
    param([switch]$Uninstall, [switch]$Check)
    $userRoot = [Environment]::GetEnvironmentVariable('VIA_ROOT', 'User')
    if (-not $Uninstall -and -not $Check) {
        if (-not $userRoot -or -not (Get-ChildItem -LiteralPath $userRoot -Filter 'VIA_ProfileLoader_v*.ps1' -ErrorAction SilentlyContinue)) {
            Write-Host "[via-setup] 使用者層 VIA_ROOT($userRoot)下沒有 VIA_ProfileLoader_v*.ps1,先把 loader 放進去再設定。" -ForegroundColor Red
            return
        }
    }
    if ($Check) { (Test-ViaProfile).lines | ForEach-Object { Write-Host $_ }; return }
    $dir = Split-Path $PROFILE
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
    $bak = "$PROFILE.via_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item -LiteralPath $PROFILE -Destination $bak -Force
    $orig = Get-Content -LiteralPath $PROFILE -Raw -ErrorAction SilentlyContinue
    if ($null -eq $orig) { $orig = '' }
    $base = (Remove-ViaProfileBlock $orig).TrimEnd()
    $new = if ($Uninstall) { $base + "`n" } else { $base + "`n`n" + (Get-ViaProfileBlock) }
    $tmp = "$PROFILE.via_tmp"
    Set-Content -LiteralPath $tmp -Value $new -Encoding utf8BOM
    Move-Item -LiteralPath $tmp -Destination $PROFILE -Force
    Write-Host "[via-setup] 已備份原 profile → $bak" -ForegroundColor DarkCyan
    if ($Uninstall) { Write-Host '[via-setup] 已移除 VIA 區塊(其餘內容不動)。' -ForegroundColor Green; return }
    Write-Host '[via-setup] 寫入完成,開始多次檢查…' -ForegroundColor Cyan
    $r = Test-ViaProfile
    $r.lines | ForEach-Object { Write-Host $_ }
    if (-not $r.ok) {
        Copy-Item -LiteralPath $bak -Destination $PROFILE -Force
        Write-Host '[via-setup] 檢查未全過 → 已自動還原原 profile,PS 不受影響。請把上面 FAIL 行貼給 AI。' -ForegroundColor Red
        return
    }
    Write-Host '[via-setup] ✔ 全部通過。之後每次開 pwsh 會自動進 VIA;不想進:設 $env:VIA_NO_LOADER=1 或用 pwsh -NoProfile。' -ForegroundColor Green
}

# --- 6. 進入 PS 時的 VIA 主控台(頂部矩陣 + 選擇題 / 直接貼上雙軌) ---
function via {
    Clear-Host
    if (Get-Command Invoke-SpectreCommandWithStatus -ErrorAction SilentlyContinue) {
        Invoke-SpectreCommandWithStatus -Spinner 'Dots' -Title '喚醒 VIA 環境與載入前次備份...' -ScriptBlock {
            Start-Sleep -Milliseconds 250
        }
    }
    if ($ViaHubPy -and (Test-Path $ViaHubPy)) { Invoke-ViaHub boot }
    else { Write-Host "[WARN] 找不到 $ViaHubPy" -ForegroundColor Yellow }
    Write-Host '  另有:via-auth(授權)· via-run(全線)· via-setup(常態設定 / -Check 檢查 / -Uninstall 移除)' -ForegroundColor DarkCyan

    $choices = @(
        '1. 原生指令列 · 立即進入終端機(可直接貼上 / 輸入指令)',
        '2. via-pano · 全景檢視 GitHub + PC File,一輪 AST 修復(乾跑)',
        '3. via-bak · 主動備份 + Graphify + OmniRoute + agency-mem',
        '4. via-ast · AST 導入加速器(剪貼簿 / 檔案,diff 預覽後注入)',
        '5. via-auth · 授權:設定 FRED key / 查看授權狀態',
        '6. via-run · 全線啟動:開同意閘 → VDF 擷取 → VRN 解析(跑完自動關閘)',
        '7. via-setup · 常態設定:開 PS 自動進 VIA(備份 + 多次檢查 + 失敗自動還原)'
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
        '7.*' { via-setup }
    }
    Write-Host "`e[38;2;163;190;140m✔ VIA 已就緒｜可直接貼上/輸入指令(隨時輸入 via 重開選單)`e[0m`n"
}

# 進入 PowerShell 自動啟動 VIA 主控台 —— 只在互動式終端;腳本 / -Command / -File / 非互動 / Claude Code 子行程一律不開
$__viaArgs = [Environment]::GetCommandLineArgs() -join ' '
$__viaInteractive = [Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost' -and
    ($__viaArgs -notmatch '(?i)\s-(c|command|f|file|e|ec|encodedcommand|noni|noninteractive)\b') -and
    -not $env:CLAUDECODE -and -not $env:VIA_NO_MENU
if ($__viaInteractive) { via }
