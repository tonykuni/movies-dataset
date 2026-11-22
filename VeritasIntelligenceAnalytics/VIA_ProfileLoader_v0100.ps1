#Requires -Version 7.4
# ==============================================================================
# VIA_ProfileLoader_v0100.ps1  —  VIA 現代化雙引擎啟動外殼(薄層)
# 全邏輯在 Python(VCGC_CommandHub),PS 只負責:進環境 + 現代化 TUI + 選擇題。
# 路徑一律用 $PSScriptRoot,不寫死任何本機路徑;交給操作員的 PS 只有這一支。
# 寫入 $PROFILE 前請先照 UAT 四階段測過(見倉內 docs 的測試規劃)。
# 緊急逃生:pwsh -NoProfile  即可跳過本外殼進純淨終端機。
# ==============================================================================
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
Import-Module PwshSpectreConsole -ErrorAction SilentlyContinue

# --- 1. VIA 根目錄與 Python 入口(以本檔所在為 VIA_ROOT,可被既有 $env:VIA_ROOT 覆蓋) ---
if ([string]::IsNullOrWhiteSpace($env:VIA_ROOT)) { $env:VIA_ROOT = $PSScriptRoot }
$ViaHubPy = Get-ChildItem -Path $PSScriptRoot -Filter 'VCGC_CommandHub_v*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1 | ForEach-Object { $_.FullName }
if (-not $ViaHubPy) { $ViaHubPy = Join-Path $PSScriptRoot 'VCGC_CommandHub_v0100.py' }
$PyCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }

# --- 2. 自動掛載 via_* 虛擬環境(若存在) ---
foreach ($v in @(
        (Join-Path $env:VIA_ROOT '.venv\Scripts\Activate.ps1'),
        (Join-Path $env:USERPROFILE 'venvs\via_core\Scripts\Activate.ps1'))) {
    if (Test-Path $v) { . $v; break }
}

# --- 3. 四個核心短指令(薄層轉呼叫 Python;向下相容舊 9 支別名) ---
function via-pano {
    param([switch]$Apply)
    if ($Apply) { & $PyCmd $ViaHubPy pano --apply } else { & $PyCmd $ViaHubPy pano }
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
        else { $a += '--clipboard' }   # 預設:直接吃剪貼簿
    }
    & $PyCmd @a
}
# 向下相容:舊 9 支短指令一律導向新 4 支(避免肌肉記憶報錯)
Set-Alias -Name via-status       -Value via        -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-six          -Value via-pano   -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-panorama-all -Value via-pano   -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-lanes        -Value via-pano   -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-vdffetch     -Value via-bak    -Scope Global -ErrorAction SilentlyContinue
Set-Alias -Name via-vrnrun       -Value via-bak    -Scope Global -ErrorAction SilentlyContinue

# --- 4. 進入 PS 時的 VIA 主控台(頂部矩陣 + 選擇題 / 直接貼上雙軌) ---
function via {
    Clear-Host
    if (Get-Command Invoke-SpectreCommandWithStatus -ErrorAction SilentlyContinue) {
        Invoke-SpectreCommandWithStatus -Spinner 'Dots' -Title '喚醒 VIA 環境與載入前次備份...' -ScriptBlock {
            Start-Sleep -Milliseconds 250
        }
    }
    # 最上方:短指令速查矩陣 + 晨間前次備份摘要(全由 Python Rich 印出,調整格式)
    if (Test-Path $ViaHubPy) { & $PyCmd $ViaHubPy boot }
    else { Write-Host "[WARN] 找不到 $ViaHubPy" -ForegroundColor Yellow }

    # 下方:方向鍵選擇題(第 1 項 = 直接進原生指令列,按 Enter 即可貼上/輸入)
    if (Get-Command Read-SpectreSelection -ErrorAction SilentlyContinue) {
        $choice = Read-SpectreSelection -Title "`n[bold #88C0D0]請選擇操作模式(直接按 Enter 進入指令列供貼上/輸入):[/]" -Choices @(
            '1. [原生指令列] 立即進入終端機(可直接貼上 / 輸入指令)',
            '2. [via-pano]   全景檢視 GitHub + PC File,一輪 AST 修復(乾跑)',
            '3. [via-bak]    主動備份 + Graphify + OmniRoute + agency-mem',
            '4. [via-ast]    AST 導入加速器(剪貼簿 / 檔案,diff 預覽後注入)'
        )
        switch -Wildcard ($choice) {
            '2.*' { via-pano }
            '3.*' {
                $note = Read-Host '輸入備份焦點備註(直接 Enter 用預設)'
                if ([string]::IsNullOrWhiteSpace($note)) { via-bak } else { via-bak -Note $note }
            }
            '4.*' {
                $t = Read-Host '目標 Python 檔案路徑'
                $s = Read-Host '指定單一符號(直接 Enter 自動偵測全部函式/類別)'
                $srcMode = Read-SpectreSelection -Title '程式碼來源:' -Choices @(
                    '1. [剪貼簿] 讀取目前已複製的 Python 程式碼',
                    '2. [檔案]   指定來源 .py 檔路徑')
                if ($srcMode -like '2.*') {
                    $cf = Read-Host '來源 .py 檔路徑'
                    if ([string]::IsNullOrWhiteSpace($s)) { via-ast -Target $t -CodeFile $cf } else { via-ast -Target $t -Symbol $s -CodeFile $cf }
                } else {
                    if ([string]::IsNullOrWhiteSpace($s)) { via-ast -Target $t -Clipboard } else { via-ast -Target $t -Symbol $s -Clipboard }
                }
            }
        }
    } else {
        Write-Host "`n[提示] 未安裝 PwshSpectreConsole,短指令仍可用:via-pano / via-bak / via-ast" -ForegroundColor DarkGray
    }
    Write-Host "`e[38;2;163;190;140m✔ VIA 已就緒｜可直接貼上/輸入指令(隨時輸入 via 重開選單)`e[0m`n"
}

# 進入 PowerShell 自動啟動 VIA 主控台
via
