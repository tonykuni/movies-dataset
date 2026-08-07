#requires -Version 5.1
<#
================================================================================
 activate.ps1  ——  VIA Forge 一鍵啟動 (雙擊即跑)
================================================================================
 這支是「最省事入口」。它只做三件事：
   1. 定位自己所在資料夾 (不管你從哪裡雙擊)
   2. 確保用 PowerShell 7 (pwsh) 執行；若當前是 Windows PowerShell 5，
      會自動改用 pwsh 重啟本腳本 (VIA_Forge_Launcher 需要 v7)
   3. 呼叫 VIA_Forge_Launcher.ps1 完成：建 venv → 裝套件 → 四引擎 self-test
      → 起後端 → 開瀏覽器 → 健康檢查

 用法：
   雙擊 activate.ps1           # 一鍵全自動
   或在終端： .\activate.ps1
   .\activate.ps1 -Stop        # 優雅關閉後端
   .\activate.ps1 -NoBrowser   # 不自動開瀏覽器

 若雙擊被「執行原則 (ExecutionPolicy)」擋下，改用內附的 activate.bat 雙擊，
 它會以 -ExecutionPolicy Bypass 只對這一次執行放行 (不改系統設定、不需管理員)。
================================================================================
#>

param(
    [switch]$NoBrowser,
    [switch]$Stop,
    [switch]$Governance,
    [string]$PromptSource = "",
    [string]$PromptFile = "",
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"

# --- 1. 定位本腳本所在資料夾 -------------------------------------------------
# 多重 fallback：正常執行用 $PSScriptRoot / MyInvocation.Path；
# 若被「逐行貼進視窗」或 dot-source 導致兩者皆 null，退回目前工作目錄，
# 並提醒使用者正確的啟動方式（不再直接崩潰）。
$Here = $null
if ($PSScriptRoot) {
    $Here = $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
    $Here = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    $Here = (Get-Location).Path
    Write-Host ""
    Write-Host "提醒：偵測不到腳本檔路徑（可能是把內容貼進視窗執行）。" -ForegroundColor Yellow
    Write-Host "改用目前資料夾定位：$Here" -ForegroundColor Yellow
    Write-Host "建議正確啟動方式：雙擊 activate.bat，或執行  .\activate.ps1" -ForegroundColor DarkGray
    Write-Host ""
}

Set-Location $Here
$Launcher = Join-Path $Here "VIA_Forge_Launcher.ps1"

if (-not (Test-Path $Launcher)) {
    Write-Host "在此資料夾找不到 VIA_Forge_Launcher.ps1：" -ForegroundColor Red
    Write-Host "  $Here" -ForegroundColor Red
    Write-Host "請把 activate.ps1 放到與 VIA_Forge_Launcher.ps1 同一層（有 via_forge.py 那層），" -ForegroundColor DarkGray
    Write-Host "或先  cd 到該資料夾再執行  .\activate.ps1" -ForegroundColor DarkGray
    Write-Host "按 Enter 離開..." -ForegroundColor DarkGray
    try { [void][System.Console]::ReadLine() } catch { }
    return
}

# --- 2. 確保使用 PowerShell 7 (pwsh) ----------------------------------------
# VIA_Forge_Launcher.ps1 標記 #requires -Version 7.0。
# 若目前是 Windows PowerShell 5.x，嘗試找 pwsh 並用它重跑本腳本。
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($pwsh) {
        Write-Host "偵測到 Windows PowerShell $($PSVersionTable.PSVersion)；改用 PowerShell 7 執行..." -ForegroundColor Yellow
        $fwd = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$($MyInvocation.MyCommand.Path)`"")
        if ($NoBrowser) { $fwd += "-NoBrowser" }
        if ($Stop)      { $fwd += "-Stop" }
        if ($Governance) { $fwd += "-Governance" }
        if ($PromptSource) { $fwd += "-PromptSource"; $fwd += $PromptSource }
        if ($PromptFile) { $fwd += "-PromptFile"; $fwd += $PromptFile }
        if ($OpenReport) { $fwd += "-OpenReport" }
        & $pwsh.Source @fwd
        return
    } else {
        Write-Host "警告：未找到 PowerShell 7 (pwsh)。" -ForegroundColor Yellow
        Write-Host "VIA_Forge_Launcher 需要 v7。請安裝：https://aka.ms/powershell (免管理員的 zip 版亦可)" -ForegroundColor Yellow
        Write-Host "仍嘗試以目前版本繼續（可能因語法失敗）..." -ForegroundColor DarkGray
    }
}

# --- 3. 呼叫完整 Launcher ----------------------------------------------------
$fwdArgs = @{}
if ($NoBrowser) { $fwdArgs["NoBrowser"] = $true }
if ($Stop)      { $fwdArgs["Stop"] = $true }
if ($Governance) { $fwdArgs["Governance"] = $true }
if ($PromptSource) { $fwdArgs["PromptSource"] = $PromptSource }
if ($PromptFile) { $fwdArgs["PromptFile"] = $PromptFile }
if ($OpenReport) { $fwdArgs["OpenReport"] = $true }

try {
    & $Launcher @fwdArgs
} catch {
    Write-Host ""
    Write-Host "啟動過程發生錯誤：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host "常見原因：Python 未安裝 / venv 建立失敗 / 埠被占用。" -ForegroundColor DarkGray
}

# 若是雙擊執行（非 -Stop），停在畫面讓使用者看到結果
if (-not $Stop) {
    Write-Host ""
    Write-Host "（後端已在背景執行。此視窗可關閉；要停止請執行 .\activate.ps1 -Stop）" -ForegroundColor DarkGray
    Write-Host "按 Enter 關閉此啟動視窗..." -ForegroundColor DarkGray
    try { [void][System.Console]::ReadLine() } catch { }
}
