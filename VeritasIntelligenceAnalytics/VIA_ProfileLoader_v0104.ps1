#Requires -Version 7.4
# ==============================================================================
# VIA_ProfileLoader_v0104.ps1 — VIA 唯一一支 PS(薄殼)· 作廢 v0100 / v0101 / v0102 / v0103
# 操作員 2026-11-23:「所有指令用 PY 寫導入加速器」「ONE PS TO SET UP AND HANDLE ALL」「啟動被動更新」
# 本版 PS 不再有任何邏輯:每個 via-* 只把參數轉給 VCGC_CommandHub 尾版(Python,帶加速器橋)。
#   via            主控台(前次備份 / 前次 doctor / 選單)
#   via-update     架構快照(被動:啟動才更新)→ 視覺鎖定 HTML:系統卡 · SSOT/SDD/註冊/regex/同義字矩陣 · 燈號
#   via-doctor     VCGC 工具外掛並行查環境:衝突 · 遺漏 · 加速器 · Graphify/OmniRoute/Agency-mem → 安裝計畫
#   via-install    照 doctor 計畫走 VCGC 安裝閘(你輸入 YES 才開同意閘,只在子行程)
#   via-bak        增量備份(只備變動檔)+ Graphify / OmniRoute 收據 + agency-mem 交接記憶
#   via-pano / via-ast   照前版
#   via-auth       FRED key 遮罩輸入 → Windows 使用者層(不顯示任何字元)
#   via-run        全線:YES → VDF launch --run → VRN MDL260 run(同意閘只在子行程)
#   via-setup      常態掛 $PROFILE(Python 做備份 + 標記區塊 + 3 次檢查,失敗自動還原)
# 不寫死本機路徑:資料根 = 使用者層 VIA_ROOT;中樞 = 本檔同夾的 VCGC_CommandHub 尾版。緊急逃生:pwsh -NoProfile
# ==============================================================================
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
Import-Module PwshSpectreConsole -ErrorAction SilentlyContinue

# --- 1. 根與 Python(不改動本視窗既有 $env:VIA_ROOT,舊工具照舊) ---
if ([string]::IsNullOrWhiteSpace($env:VIA_ROOT)) { $env:VIA_ROOT = $PSScriptRoot }
$PyCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
$ViaDataRoot = [Environment]::GetEnvironmentVariable('VIA_ROOT', 'User')
if ([string]::IsNullOrWhiteSpace($ViaDataRoot) -or -not (Test-Path $ViaDataRoot)) { $ViaDataRoot = $env:VIA_ROOT }
$ViaHubPy = Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'VCGC_CommandHub_v*.py' -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1 -ExpandProperty FullName

function Invoke-ViaHub {
    # 中樞以資料根為 VIA_ROOT、本檔夾為 VIA_CODE_ROOT 執行;結束後還原本視窗原值
    if (-not $ViaHubPy) { Write-Host "[VIA] $PSScriptRoot 下找不到 VCGC_CommandHub_v*.py" -ForegroundColor Yellow; return }
    $old = $env:VIA_ROOT; $oldCode = $env:VIA_CODE_ROOT
    try { $env:VIA_ROOT = $ViaDataRoot; $env:VIA_CODE_ROOT = $PSScriptRoot; & $PyCmd $ViaHubPy @args }
    finally { $env:VIA_ROOT = $old; $env:VIA_CODE_ROOT = $oldCode }
}

# --- 2. 自動掛載 via_* 虛擬環境(若存在) ---
foreach ($v in @((Join-Path $env:VIA_ROOT '.venv\Scripts\Activate.ps1'),
                 (Join-Path $env:USERPROFILE 'venvs\via_core\Scripts\Activate.ps1'))) {
    if ($v -and (Test-Path $v)) { . $v; break }
}

# --- 3. 短指令:全部轉給 Python(參數原樣傳) ---
function via-update  { Invoke-ViaHub update @args }
function via-doctor  { Invoke-ViaHub doctor @args }
function via-install { Invoke-ViaHub install @args }
function via-bak     { Invoke-ViaHub bak @args }
function via-plug    { Invoke-ViaHub plug @args }
function via-run     { Invoke-ViaHub run @args }
function via-setup   { Invoke-ViaHub setup @args }
function via-pano    { Invoke-ViaHub pano @args }
function via-ast     { Invoke-ViaHub ast @args }
function via-auth {
    Invoke-ViaHub auth @args
    # 讓本視窗也吃到剛存的使用者層值(只在記憶體,不顯示)
    $u = [Environment]::GetEnvironmentVariable('FRED_API_KEY', 'User')
    if ($u) { $env:FRED_API_KEY = $u } else { Remove-Item Env:FRED_API_KEY -ErrorAction SilentlyContinue }
}

# 向下相容:舊短指令只在「沒有同名指令」時才設,不蓋掉原有功能
foreach ($pair in @(@('via-status', 'via'), @('via-six', 'via-pano'), @('via-panorama-all', 'via-update'),
                    @('via-lanes', 'via-update'), @('via-vdffetch', 'via-run'), @('via-vrnrun', 'via-run'),
                    @('via-env', 'via-doctor'))) {
    if (-not (Get-Command $pair[0] -ErrorAction SilentlyContinue)) {
        Set-Alias -Name $pair[0] -Value $pair[1] -Scope Global -ErrorAction SilentlyContinue
    }
}

# --- 4. 主控台(選項不用方括號:Spectre 會當顏色標記) ---
function via {
    Clear-Host
    Invoke-ViaHub boot
    $choices = @(
        '1. 原生指令列 · 直接貼上 / 輸入指令',
        '2. via-update · 架構快照(被動更新)→ 視覺鎖定 HTML',
        '3. via-doctor · 環境醫生:衝突 · 遺漏 · 加速器 · 工具',
        '4. via-install · 照 doctor 計畫走安裝閘(YES 才裝)',
        '5. via-bak · 增量備份 + Graphify + OmniRoute + agency-mem',
        '6. via-run · 全線啟動 VDF → VRN(YES 才開同意閘)',
        '7. via-auth · FRED key 授權 / 查看',
        '8. via-setup · 常態掛 PS(失敗自動還原)',
        '9. via-pano · 全景 AST 檢視(乾跑)'
    )
    if (Get-Command Read-SpectreSelection -ErrorAction SilentlyContinue) {
        $choice = Read-SpectreSelection -Title "`n[bold #88C0D0]請選擇(直接 Enter 進指令列):[/]" -Choices $choices
    } else {
        $choices | ForEach-Object { Write-Host "  $_" }
        $n = Read-Host '輸入編號(直接 Enter = 1)'
        $choice = if ([string]::IsNullOrWhiteSpace($n)) { '1.' } else { "$n." }
    }
    switch -Wildcard ($choice) {
        '2.*' { via-update }
        '3.*' { via-doctor }
        '4.*' { via-install }
        '5.*' {
            $note = Read-Host '備份焦點備註(直接 Enter 用預設)'
            if ([string]::IsNullOrWhiteSpace($note)) { via-bak } else { via-bak --note $note }
        }
        '6.*' { via-run }
        '7.*' {
            $f = Read-Host '要設定 / 更新 FRED key 嗎?(y/N)'
            if ($f -match '^[yY]') { via-auth --fred } else { via-auth }
        }
        '8.*' { via-setup }
        '9.*' { via-pano }
    }
    Write-Host "`e[38;2;163;190;140m✔ VIA 已就緒｜可直接貼上/輸入指令(隨時輸入 via 重開選單)`e[0m`n"
}

# 進 PowerShell 自動開主控台 —— 只在互動式終端;-Command / -File / 非互動 / Claude Code 子行程 / VIA_NO_MENU 一律不開
$__viaArgs = [Environment]::GetCommandLineArgs() -join ' '
$__viaInteractive = [Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost' -and
    ($__viaArgs -notmatch '(?i)\s-(c|command|f|file|e|ec|encodedcommand|noni|noninteractive)\b') -and
    -not $env:CLAUDECODE -and -not $env:VIA_NO_MENU
if ($__viaInteractive) { via }
