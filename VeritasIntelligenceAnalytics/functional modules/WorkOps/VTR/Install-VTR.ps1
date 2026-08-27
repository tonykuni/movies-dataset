#Requires -Version 5.1
<#
.SYNOPSIS
    VTR 一鍵安裝器 · 全新電腦也能用。

.DESCRIPTION
    假設這是一台**全新的 Windows 電腦**：除了 Windows 內建的 PowerShell 之外，
    什麼都沒裝。這支程式會自動把 VTR 需要的東西一次補齊，然後幫你驗證：

      1. 檢查有沒有 Python（VTR 唯一需要的執行環境）
      2. 沒有的話，自動下載安裝（優先用 winget；不行就從 python.org 官方下載）
      3. 把 PATH 設好，讓這個視窗立刻就能用 Python
      4. 跑一次完整驗證，確認 VTR 真的能動

    給初學者：**你不需要懂任何指令。** 直接雙擊 `Install-VTR.cmd` 就會開始，
    全程會用中文告訴你正在做什麼、成功還是失敗、下一步該做什麼。

.PARAMETER SkipInstall
    只檢查、不自動安裝 Python（若你想自己手動裝）。

.PARAMETER SkipVerify
    裝完不跑 VTR 完整驗證。

.PARAMETER PythonVersion
    自動安裝時要裝的 Python 版本（預設 3.12）。

.EXAMPLE
    雙擊 Install-VTR.cmd
    最簡單。全自動，看中文提示即可。

.EXAMPLE
    .\Install-VTR.ps1
    在已開啟的 PowerShell 視窗手動執行，效果相同。

.NOTES
    需要管理員權限嗎？**不需要。** Python 以「僅目前使用者」方式安裝，不會動到系統。
    退出碼：0 全部就緒 · 1 安裝或驗證未完成 · 10 需要你手動處理（會有中文說明）。
#>
[CmdletBinding()]
param(
    [switch] $SkipInstall,
    [switch] $SkipPowerShell,
    [switch] $UpgradePowerShell,
    [switch] $SkipVerify,
    [string] $PythonVersion = '3.12',
    [switch] $NoColor
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:Root = $PSScriptRoot

# --------------------------------------------------------------------------- #
# 給初學者看的輸出（大字、清楚、中文）
# --------------------------------------------------------------------------- #

function Initialize-Utf8 {
    try {
        [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
        $global:OutputEncoding    = New-Object System.Text.UTF8Encoding($false)
    } catch { }
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
}

function Say {
    param([string] $Text = '', [string] $Colour = 'Gray')
    if ($NoColor) { Write-Host $Text } else { Write-Host $Text -ForegroundColor $Colour }
}

function Say-Title {
    param([string] $Text)
    Say ''
    Say ('══════════════════════════════════════════════════════════════') 'DarkCyan'
    Say ("  $Text") 'White'
    Say ('══════════════════════════════════════════════════════════════') 'DarkCyan'
}

function Say-Step { param([int]$N, [string]$T) Say ''; Say ("  步驟 $N ── $T") 'Cyan' }
function Say-OK   { param([string]$T) Say ("     ✓ $T") 'Green' }
function Say-Fail { param([string]$T) Say ("     ✗ $T") 'Red' }
function Say-Wait { param([string]$T) Say ("     … $T") 'Yellow' }
function Say-Note { param([string]$T) Say ("       $T") 'DarkGray' }

# --------------------------------------------------------------------------- #
# Python 偵測（與 Invoke-VTR.ps1 使用相同的無雙引號探針，避免 5.1 引號問題）
# --------------------------------------------------------------------------- #

function Find-Python {
    $candidates = @(
        @{ Exe = 'py';      Args = @('-3') },
        @{ Exe = 'python3'; Args = @() },
        @{ Exe = 'python';  Args = @() }
    )
    foreach ($c in $candidates) {
        if ($null -eq (Get-Command $c.Exe -ErrorAction SilentlyContinue)) { continue }
        try {
            $code  = 'import sys;print(sys.version_info[0]);print(sys.version_info[1])'
            $probe = @($c.Args) + @('-c', $code)
            $out = & $c.Exe @probe 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $nums = @($out) | ForEach-Object { ([string]$_).Trim() } |
                    Where-Object { $_ -match '^\d+$' }
            if ($nums.Count -lt 2) { continue }
            $major = [int]$nums[0]; $minor = [int]$nums[1]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) { continue }
            return [pscustomobject]@{
                Exe = $c.Exe; Args = $c.Args; Version = "$major.$minor"
            }
        } catch { continue }
    }
    return $null
}

function Update-SessionPath {
    # 安裝後，PATH 的變更只對「新開的視窗」生效。這裡把註冊表裡的 PATH
    # 重新讀進目前視窗，讓剛裝好的 Python 立刻可用，不必叫初學者重開視窗。
    try {
        $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
        $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
        $joined  = (@($machine, $user) | Where-Object { $_ }) -join ';'
        if ($joined) { $env:Path = $joined }
    } catch { }
}

# --------------------------------------------------------------------------- #
# PowerShell 7 偵測與安裝（一開始就把最新版準備好）
# --------------------------------------------------------------------------- #

function Get-PwshPath {
    # 找 pwsh（PowerShell 7+）。先問 PATH，再試常見安裝位置
    # （winget/安裝腳本剛裝完，PATH 在本視窗可能還沒更新）。
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bases = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA) |
             Where-Object { $_ }
    foreach ($b in $bases) {
        foreach ($sub in @('PowerShell\7\pwsh.exe', 'Microsoft\PowerShell\7\pwsh.exe')) {
            $p = Join-Path $b $sub
            if (Test-Path -LiteralPath $p) { return $p }
        }
    }
    return $null
}

function Get-PwshVersion {
    param([string] $Exe)
    try {
        $v = & $Exe -NoProfile -Command '$PSVersionTable.PSVersion.ToString()' 2>$null
        return ([string]$v).Trim()
    } catch { return $null }
}

function Install-PowerShell7 {
    # 先試 winget（官方來源、自動取最新版）。
    if ($null -ne (Get-Command winget -ErrorAction SilentlyContinue)) {
        Say-Wait '使用 winget 安裝最新版 PowerShell…'
        try {
            $a = @('install', '--exact', '--id', 'Microsoft.PowerShell',
                   '--source', 'winget', '--silent',
                   '--accept-package-agreements', '--accept-source-agreements')
            & winget @a | Out-Host
            if ($LASTEXITCODE -eq 0) { return $true }
            Say-Note "winget 退出碼 $LASTEXITCODE，改用官方安裝腳本（免管理員）。"
        } catch {
            Say-Note "winget 失敗：$($_.Exception.Message)，改用官方安裝腳本。"
        }
    }
    # 備援：微軟官方安裝腳本，解壓到使用者目錄並加入 PATH —— 不需要管理員。
    Say-Wait '從 aka.ms 官方腳本安裝最新版 PowerShell（免管理員）…'
    try {
        $installer = Invoke-RestMethod -Uri 'https://aka.ms/install-powershell.ps1' -UseBasicParsing
        $sb = [ScriptBlock]::Create($installer)
        $dest = Join-Path $env:LOCALAPPDATA 'Microsoft\PowerShell\7'
        & $sb -Destination $dest -AddToPath
        return $true
    } catch {
        Say-Fail "PowerShell 安裝未成功：$($_.Exception.Message)"
        return $false
    }
}

function Ensure-PowerShell7 {
    $exe = Get-PwshPath
    if ($null -ne $exe) {
        $ver = Get-PwshVersion -Exe $exe
        if ($UpgradePowerShell -and -not $SkipPowerShell) {
            Say-Wait "已安裝 PowerShell $ver，依 -UpgradePowerShell 嘗試升級到最新…"
            if (Install-PowerShell7) {
                Update-SessionPath
                $exe = Get-PwshPath; $ver = Get-PwshVersion -Exe $exe
            }
        }
        Say-OK "PowerShell 7 已就緒：版本 $ver"
        return $true
    }

    if ($SkipPowerShell) {
        Say-Wait '未安裝 PowerShell 7，且指定了 -SkipPowerShell；改用內建的 Windows PowerShell 5.1 繼續。'
        return $false
    }

    Say-Wait '沒偵測到 PowerShell 7，開始安裝最新版（可能要幾分鐘）…'
    Say-Note '若跳出「使用者帳戶控制 (UAC)」詢問，點「是」即可。'
    Say-Note '不能點（沒有管理員權限）也沒關係，會自動改用免管理員的方式安裝。'

    [void](Install-PowerShell7)
    Update-SessionPath
    $exe = Get-PwshPath

    if ($null -ne $exe) {
        Say-OK "PowerShell 7 安裝完成：版本 $(Get-PwshVersion -Exe $exe)"
        return $true
    }

    # 裝好了但本視窗還沒吃到 PATH，或安裝未成功 —— 都不影響後續（5.1 也能跑）。
    Say-Wait 'PowerShell 7 尚未在本視窗生效（多半是 PATH 要重開視窗才更新）。'
    Say-Note 'VTR 在內建的 Windows PowerShell 5.1 上也能正常運作，這一步不影響驗證。'
    Say-Note '想立刻改用 7：關掉視窗重開一次；日後雙擊 Run-VTR.cmd 會自動優先用 pwsh。'
    return $false
}

# --------------------------------------------------------------------------- #
# Python 自動安裝
# --------------------------------------------------------------------------- #

function Install-PythonViaWinget {
    if ($null -eq (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
    Say-Wait "使用 winget 安裝 Python $PythonVersion（僅目前使用者，不需要管理員）…"
    $id = "Python.Python.$PythonVersion"
    try {
        # 陣列參數 + 呼叫運算子：不用 Start-Process，避免路徑含空白時被拆開。
        $args1 = @('install', '--exact', '--id', $id, '--source', 'winget',
                   '--scope', 'user', '--silent',
                   '--accept-package-agreements', '--accept-source-agreements')
        & winget @args1 | Out-Host
        if ($LASTEXITCODE -eq 0) { return $true }
        Say-Note "winget 退出碼 $LASTEXITCODE，改用官方安裝檔。"
        return $false
    } catch {
        Say-Note "winget 失敗：$($_.Exception.Message)，改用官方安裝檔。"
        return $false
    }
}

function Install-PythonViaDownload {
    # 從 python.org 官方下載安裝檔並靜默安裝。這是 winget 不可用時的備援。
    $ver = if ($PythonVersion -match '^\d+\.\d+$') { "$PythonVersion.0" } else { $PythonVersion }
    # 使用者可傳完整版號（如 3.12.7）；只給到次版號時補一個具體修訂號。
    $arch = if ([Environment]::Is64BitOperatingSystem) { 'amd64' } else { 'win32' }
    $url = "https://www.python.org/ftp/python/$ver/python-$ver-$arch.exe"
    $tmp = Join-Path $env:TEMP "python-$ver-$arch.exe"

    Say-Wait "從官方下載：$url"
    try {
        $old = $ProgressPreference; $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        $ProgressPreference = $old
    } catch {
        Say-Fail "下載失敗：$($_.Exception.Message)"
        Say-Note "多半是版號 $ver 不存在或沒有網路。用 -PythonVersion 指定一個確切版本（例如 3.12.7），或見下方手動步驟。"
        return $false
    }

    Say-Wait "安裝中（靜默、僅目前使用者、自動加入 PATH）…"
    try {
        # 安裝檔是視窗程式，必須等它跑完 → 用 Start-Process -Wait。
        # 這裡用「陣列」形式的 ArgumentList，每個元素是一個獨立參數，
        # 不會有「路徑含空白被拆開」的問題（那是字串形式 ArgumentList 才有的雷）。
        $p = Start-Process -FilePath $tmp -Wait -PassThru -ArgumentList @(
            '/quiet', 'InstallAllUsers=0', 'PrependPath=1',
            'Include_launcher=1', 'Include_test=0'
        )
        if ($p.ExitCode -ne 0) {
            Say-Fail "安裝檔退出碼 $($p.ExitCode)"
            return $false
        }
        return $true
    } catch {
        Say-Fail "安裝失敗：$($_.Exception.Message)"
        return $false
    } finally {
        Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue
    }
}

function Show-ManualPythonHelp {
    Say ''
    Say "  需要你手動處理（只有這一步，之後全自動）：" 'Yellow'
    Say-Note "1. 打開瀏覽器到 https://www.python.org/downloads/windows/"
    Say-Note "2. 下載最新的 Python 3 安裝檔（Windows installer, 64-bit）"
    Say-Note "3. 執行安裝時，務必勾選最下面的『Add python.exe to PATH』"
    Say-Note "4. 裝好後，重新雙擊 Install-VTR.cmd 即可"
}

# --------------------------------------------------------------------------- #
# 完整驗證（呼叫 Invoke-VTR.ps1 做子程序，避免它的 exit 把本視窗關掉）
# --------------------------------------------------------------------------- #

function Invoke-FullCheck {
    $invoke = Join-Path $script:Root 'Invoke-VTR.ps1'
    if (-not (Test-Path -LiteralPath $invoke)) {
        Say-Fail "找不到 Invoke-VTR.ps1（應與本程式在同一資料夾）"
        return 1
    }
    # 開一個子程序去跑驗證，這樣 Invoke-VTR.ps1 結尾的 exit 只會結束子程序，
    # 不會關掉安裝器視窗。**優先用剛裝好的 PowerShell 7**，找不到才退回目前的殼。
    $host_exe = Get-PwshPath
    if ([string]::IsNullOrWhiteSpace($host_exe)) {
        try { $host_exe = (Get-Process -Id $PID).Path } catch { }
    }
    if ([string]::IsNullOrWhiteSpace($host_exe)) { $host_exe = 'powershell' }
    & $host_exe -NoProfile -ExecutionPolicy Bypass -File $invoke | Out-Host
    return $LASTEXITCODE
}

# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

Initialize-Utf8

Say-Title 'VTR 一鍵安裝器 · 中英文會議紀錄修復引擎'
Say "  這支程式會自動把需要的東西裝好，你只要看提示就行。" 'DarkGray'
Say "  會先裝最新版 PowerShell，再裝 Python，最後驗證。全程免管理員。" 'DarkGray'

$exitCode = 0

try {
    # --- 步驟 1：最新版 PowerShell ------------------------------------------ #
    Say-Step 1 '確認 / 安裝最新版 PowerShell 7'
    [void](Ensure-PowerShell7)

    # --- 步驟 2：檢查 Python ------------------------------------------------ #
    Say-Step 2 '檢查 Python（VTR 唯一需要的執行環境）'
    $py = Find-Python

    if ($null -ne $py) {
        Say-OK "已安裝：$($py.Exe) $(@($py.Args) -join ' ')  版本 $($py.Version)"
    }
    elseif ($SkipInstall) {
        Say-Fail '找不到 Python，且指定了 -SkipInstall（不自動安裝）'
        Show-ManualPythonHelp
        exit 10
    }
    else {
        Say-Wait '沒找到 Python，開始自動安裝（這一步可能要幾分鐘）…'

        $installed = Install-PythonViaWinget
        if (-not $installed) { $installed = Install-PythonViaDownload }

        Update-SessionPath
        $py = Find-Python

        if ($null -eq $py) {
            Say-Fail '自動安裝後仍找不到 Python'
            Say-Note '有時 PATH 需要重開視窗才會生效。請關掉這個視窗，再雙擊一次 Install-VTR.cmd。'
            Say-Note '若再次失敗，請照下面的手動步驟做一次即可。'
            Show-ManualPythonHelp
            exit 10
        }
        Say-OK "安裝完成：$($py.Exe) 版本 $($py.Version)"
    }

    # --- 步驟 3：完整驗證 --------------------------------------------------- #
    if ($SkipVerify) {
        Say-Step 3 '略過驗證（-SkipVerify）'
        Say-Note '之後想檢查，雙擊 Run-VTR.cmd 即可。'
    }
    else {
        Say-Step 3 '執行 VTR 完整驗證'
        Say-Note '（環境檢查 → 詞庫 → 引擎測試 → manifest 稽核）'
        $code = Invoke-FullCheck
        if ($code -eq 0) {
            Say-OK 'VTR 全部通過，環境就緒'
        } else {
            Say-Fail "驗證未全過（退出碼 $code）"
            $exitCode = 1
        }
    }
}
catch {
    Say ''
    Say-Fail $_.Exception.Message
    $exitCode = 1
}

# --- 結語 ------------------------------------------------------------------ #
Say-Title '完成'
if ($exitCode -eq 0) {
    Say "  一切就緒。以後你只要：" 'Green'
    Say "    • 雙擊 Run-VTR.cmd          → 跑完整檢查" 'White'
    Say "    • 把逐字稿放進 input 資料夾，執行 Run-VTR.cmd -Action Restore -Path .\input\" 'White'
    Say-Note '不需要記指令；上面兩個就夠日常使用。'
} else {
    Say "  還沒完全就緒。上面紅色 ✗ 那行寫了原因與下一步。" 'Yellow'
    Say-Note '照著做通常一次就好。卡住的話，把整個畫面截圖或複製給協助你的人。'
}
Say ''

exit $exitCode

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
