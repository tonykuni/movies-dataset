# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
<#
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║            VeritasReportNova™ 一鍵自動部署腳本                                   ║
║                   One-Click Deployment System                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

功能:
- 自動檢測系統環境
- 安裝所有必要依賴
- 配置目錄結構
- 驗證安裝
- 生成快速啟動腳本

Author: Tony K.
Version: 2.0.0
#>

#Requires -Version 5.1
#Requires -RunAsAdministrator

[CmdletBinding()]
param(
    [string]$InstallPath = "C:\VeritasReportNova",
    
    [switch]$QuickStart,
    
    [switch]$SkipPythonInstall,
    
    [switch]$SkipPowerShellInstall,
    
    [switch]$Force
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = 'Stop'

# ═══════════════════════════════════════════════════════════════════════════════
# 顏色配置
# ═══════════════════════════════════════════════════════════════════════════════

$Colors = @{
    Success = 'Green'
    Warning = 'Yellow'
    Error   = 'Red'
    Info    = 'Cyan'
    Muted   = 'Gray'
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = 'Info'
    )
    
    $IconMap = @{
        Success = '✓'
        Warning = '⚠'
        Error   = '✗'
        Info    = 'ℹ'
    }
    
    Write-Host "[$($IconMap[$Type])] " -NoNewline -ForegroundColor $Colors[$Type]
    Write-Host $Message -ForegroundColor $Colors[$Type]
}

# ═══════════════════════════════════════════════════════════════════════════════
# Banner
# ═══════════════════════════════════════════════════════════════════════════════

function Show-DeploymentBanner {
    Clear-Host
    
    $Banner = @"
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                   VeritasReportNova™ 自動部署系統                               ║
║                        Automated Deployment System                            ║
║                                                                               ║
║                            版本 2.0.0 (2024-11-18)                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"@
    
    Write-Host $Banner -ForegroundColor Cyan
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 環境檢測
# ═══════════════════════════════════════════════════════════════════════════════

function Test-Administrator {
    $CurrentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = New-Object Security.Principal.WindowsPrincipal($CurrentUser)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PowerShell7 {
    try {
        $Version = $PSVersionTable.PSVersion
        return ($Version.Major -ge 7)
    } catch {
        return $false
    }
}

function Test-PythonInstalled {
    try {
        $null = python --version 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-WingetAvailable {
    try {
        $null = winget --version 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 系統檢查
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-SystemCheck {
    Write-ColorOutput "開始系統環境檢查..." -Type Info
    Write-Host ""
    
    $Checks = @()
    
    # 檢查管理員權限
    if (Test-Administrator) {
        $Checks += [PSCustomObject]@{
            Category = "權限"
            Item     = "管理員權限"
            Status   = "✓ 已具備"
            Action   = "無需操作"
        }
    } else {
        Write-ColorOutput "需要管理員權限才能繼續!" -Type Error
        Write-Host "請以管理員身份重新運行此腳本:" -ForegroundColor Yellow
        Write-Host "  右鍵PowerShell → 以管理員身份運行" -ForegroundColor Yellow
        exit 1
    }
    
    # 檢查Windows版本
    $OSInfo = Get-CimInstance Win32_OperatingSystem
    $OSBuild = [int]$OSInfo.BuildNumber
    
    if ($OSBuild -ge 19041) {  # Windows 10 20H1+
        $Checks += [PSCustomObject]@{
            Category = "作業系統"
            Item     = "Windows版本"
            Status   = "✓ $($OSInfo.Caption) (Build $OSBuild)"
            Action   = "無需操作"
        }
    } else {
        $Checks += [PSCustomObject]@{
            Category = "作業系統"
            Item     = "Windows版本"
            Status   = "⚠ $($OSInfo.Caption) (Build $OSBuild)"
            Action   = "建議升級到Windows 10 20H1或更高"
        }
    }
    
    # 檢查winget
    if (Test-WingetAvailable) {
        $Checks += [PSCustomObject]@{
            Category = "套件管理器"
            Item     = "winget"
            Status   = "✓ 已安裝"
            Action   = "無需操作"
        }
        $Global:HasWinget = $true
    } else {
        $Checks += [PSCustomObject]@{
            Category = "套件管理器"
            Item     = "winget"
            Status   = "✗ 未安裝"
            Action   = "將使用手動安裝方式"
        }
        $Global:HasWinget = $false
    }
    
    # 檢查PowerShell 7
    if (Test-PowerShell7) {
        $Checks += [PSCustomObject]@{
            Category = "PowerShell"
            Item     = "版本 7+"
            Status   = "✓ 已安裝 ($($PSVersionTable.PSVersion))"
            Action   = "無需操作"
        }
        $Global:NeedsPowerShell7 = $false
    } else {
        $Checks += [PSCustomObject]@{
            Category = "PowerShell"
            Item     = "版本 7+"
            Status   = "✗ 未安裝 (當前: $($PSVersionTable.PSVersion))"
            Action   = "將自動安裝"
        }
        $Global:NeedsPowerShell7 = $true
    }
    
    # 檢查Python
    if (Test-PythonInstalled) {
        $PythonVersion = python --version 2>&1
        $Checks += [PSCustomObject]@{
            Category = "Python"
            Item     = "版本 3.8+"
            Status   = "✓ 已安裝 ($PythonVersion)"
            Action   = "無需操作"
        }
        $Global:NeedsPython = $false
    } else {
        $Checks += [PSCustomObject]@{
            Category = "Python"
            Item     = "版本 3.8+"
            Status   = "✗ 未安裝"
            Action   = "將自動安裝"
        }
        $Global:NeedsPython = $true
    }
    
    # 檢查磁碟空間
    $Drive = (Get-Item $InstallPath.Substring(0, 2)).PSDrive
    if (-not $Drive) {
        $Drive = (Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -eq ($InstallPath.Substring(0, 3)) })[0]
    }
    
    $FreeSpaceGB = [Math]::Round($Drive.Free / 1GB, 2)
    
    if ($FreeSpaceGB -ge 5) {
        $Checks += [PSCustomObject]@{
            Category = "磁碟空間"
            Item     = "$($Drive.Name):\ 可用空間"
            Status   = "✓ $FreeSpaceGB GB"
            Action   = "無需操作"
        }
    } elseif ($FreeSpaceGB -ge 2) {
        $Checks += [PSCustomObject]@{
            Category = "磁碟空間"
            Item     = "$($Drive.Name):\ 可用空間"
            Status   = "⚠ $FreeSpaceGB GB"
            Action   = "可能需要更多空間"
        }
    } else {
        $Checks += [PSCustomObject]@{
            Category = "磁碟空間"
            Item     = "$($Drive.Name):\ 可用空間"
            Status   = "✗ $FreeSpaceGB GB (不足)"
            Action   = "請釋放磁碟空間"
        }
        Write-ColorOutput "磁碟空間不足,需要至少2GB可用空間!" -Type Error
        exit 1
    }
    
    # 顯示檢查結果
    $Checks | Format-Table -AutoSize
    
    Write-Host ""
    
    $NeedsAction = $Checks | Where-Object { $_.Action -ne "無需操作" }
    if ($NeedsAction.Count -gt 0) {
        Write-ColorOutput "發現 $($NeedsAction.Count) 個需要處理的項目" -Type Warning
    } else {
        Write-ColorOutput "所有檢查通過!" -Type Success
    }
    
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 安裝函數
# ═══════════════════════════════════════════════════════════════════════════════

function Install-PowerShell7 {
    if ($SkipPowerShellInstall) {
        Write-ColorOutput "跳過PowerShell 7安裝" -Type Info
        return
    }
    
    Write-ColorOutput "開始安裝PowerShell 7..." -Type Info
    
    try {
        if ($Global:HasWinget) {
            Write-Host "使用winget安裝..." -ForegroundColor Gray
            winget install --id Microsoft.PowerShell --source winget --accept-package-agreements --accept-source-agreements
        } else {
            Write-Host "下載安裝器..." -ForegroundColor Gray
            $DownloadUrl = "https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/PowerShell-7.4.0-win-x64.msi"
            $InstallerPath = "$env:TEMP\PowerShell-7.4.0.msi"
            
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $InstallerPath
            
            Write-Host "執行安裝..." -ForegroundColor Gray
            Start-Process msiexec.exe -ArgumentList "/i `"$InstallerPath`" /quiet /norestart" -Wait
            
            Remove-Item $InstallerPath -Force
        }
        
        Write-ColorOutput "PowerShell 7安裝完成" -Type Success
        Write-Host ""
        Write-Host "⚠️  請重新啟動此腳本以使用新安裝的PowerShell 7" -ForegroundColor Yellow
        Write-Host "命令: pwsh -File $($MyInvocation.MyCommand.Path)" -ForegroundColor Cyan
        Write-Host ""
        exit 0
        
    } catch {
        Write-ColorOutput "PowerShell 7安裝失敗: $_" -Type Error
        Write-Host "請手動安裝: https://github.com/PowerShell/PowerShell/releases" -ForegroundColor Yellow
        exit 1
    }
}

function Install-Python {
    if ($SkipPythonInstall) {
        Write-ColorOutput "跳過Python安裝" -Type Info
        return
    }
    
    Write-ColorOutput "開始安裝Python 3.11..." -Type Info
    
    try {
        if ($Global:HasWinget) {
            Write-Host "使用winget安裝..." -ForegroundColor Gray
            winget install --id Python.Python.3.11 --source winget --accept-package-agreements --accept-source-agreements
        } else {
            Write-Host "下載安裝器..." -ForegroundColor Gray
            $DownloadUrl = "https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe"
            $InstallerPath = "$env:TEMP\python-3.11.6.exe"
            
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $InstallerPath
            
            Write-Host "執行安裝..." -ForegroundColor Gray
            Start-Process $InstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
            
            Remove-Item $InstallerPath -Force
        }
        
        # 刷新環境變數
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-ColorOutput "Python安裝完成" -Type Success
        
    } catch {
        Write-ColorOutput "Python安裝失敗: $_" -Type Error
        Write-Host "請手動安裝: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

function Install-PythonPackages {
    Write-ColorOutput "開始安裝Python依賴包..." -Type Info
    
    $Packages = @(
        "pymupdf",
        "camelot-py[cv]",
        "pdfplumber",
        "pandas",
        "numpy",
        "openpyxl",
        "xlsxwriter"
    )
    
    try {
        Write-Host "安裝核心依賴..." -ForegroundColor Gray
        
        foreach ($Package in $Packages) {
            Write-Host "  - $Package" -ForegroundColor Gray
            python -m pip install $Package --break-system-packages --quiet --disable-pip-version-check
        }
        
        Write-ColorOutput "Python依賴包安裝完成" -Type Success
        
    } catch {
        Write-ColorOutput "Python依賴包安裝失敗: $_" -Type Warning
        Write-Host "部分依賴可能未安裝成功,但不影響基本功能" -ForegroundColor Yellow
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 目錄結構創建
# ═══════════════════════════════════════════════════════════════════════════════

function Initialize-DirectoryStructure {
    Write-ColorOutput "創建目錄結構..." -Type Info
    
    $Directories = @(
        $InstallPath,
        "$InstallPath\Config",
        "$InstallPath\Plugins",
        "$InstallPath\Input",
        "$InstallPath\Output",
        "$InstallPath\Output\Analyses",
        "$InstallPath\Logs",
        "$InstallPath\Temp",
        "$InstallPath\Backups"
    )
    
    foreach ($Dir in $Directories) {
        if (-not (Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
            Write-Host "  ✓ $Dir" -ForegroundColor Green
        } else {
            Write-Host "  - $Dir (已存在)" -ForegroundColor Gray
        }
    }
    
    Write-ColorOutput "目錄結構創建完成" -Type Success
}

# ═══════════════════════════════════════════════════════════════════════════════
# 文件部署
# ═══════════════════════════════════════════════════════════════════════════════

function Deploy-Files {
    Write-ColorOutput "部署系統文件..." -Type Info
    
    $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    
    # 部署主腳本
    $MainScript = Join-Path $ScriptRoot "VRN-Orchestrator-v2.ps1"
    if (Test-Path $MainScript) {
        Copy-Item $MainScript -Destination $InstallPath -Force
        Write-Host "  ✓ VRN-Orchestrator-v2.ps1" -ForegroundColor Green
    } else {
        Write-ColorOutput "找不到主腳本: $MainScript" -Type Warning
    }
    
    # 部署Python引擎
    $PythonScript = Join-Path $ScriptRoot "analyze_pdf.py"
    if (Test-Path $PythonScript) {
        Copy-Item $PythonScript -Destination "$InstallPath\Config" -Force
        Write-Host "  ✓ analyze_pdf.py" -ForegroundColor Green
    } else {
        Write-ColorOutput "找不到Python腳本: $PythonScript" -Type Warning
    }
    
    # 部署插件範例
    $PluginExamples = Join-Path $ScriptRoot "VRN-Plugin-Examples.ps1"
    if (Test-Path $PluginExamples) {
        Copy-Item $PluginExamples -Destination "$InstallPath\Plugins" -Force
        Write-Host "  ✓ VRN-Plugin-Examples.ps1" -ForegroundColor Green
    } else {
        Write-ColorOutput "找不到插件範例: $PluginExamples" -Type Warning
    }
    
    # 部署README
    $Readme = Join-Path $ScriptRoot "README.md"
    if (Test-Path $Readme) {
        Copy-Item $Readme -Destination $InstallPath -Force
        Write-Host "  ✓ README.md" -ForegroundColor Green
    }
    
    Write-ColorOutput "文件部署完成" -Type Success
}

# ═══════════════════════════════════════════════════════════════════════════════
# 創建快速啟動腳本
# ═══════════════════════════════════════════════════════════════════════════════

function New-LaunchScript {
    Write-ColorOutput "創建快速啟動腳本..." -Type Info
    
    $LaunchScript = @"
# VeritasReportNova™ 快速啟動腳本
# 雙擊此檔案即可啟動Orchestrator

Set-Location "$InstallPath"
pwsh -NoExit -File "$InstallPath\VRN-Orchestrator-v2.ps1"
"@
    
    $LaunchScript | Set-Content -Path "$InstallPath\啟動VRN.ps1" -Encoding UTF8
    
    Write-ColorOutput "快速啟動腳本創建完成" -Type Success
}

# ═══════════════════════════════════════════════════════════════════════════════
# 驗證安裝
# ═══════════════════════════════════════════════════════════════════════════════

function Test-Installation {
    Write-ColorOutput "驗證安裝..." -Type Info
    Write-Host ""
    
    $ValidationResults = @()
    
    # 檢查目錄
    $RequiredDirs = @("Config", "Plugins", "Input", "Output", "Logs")
    foreach ($Dir in $RequiredDirs) {
        $Path = Join-Path $InstallPath $Dir
        $ValidationResults += [PSCustomObject]@{
            Component = "目錄"
            Item      = $Dir
            Status    = if (Test-Path $Path) { "✓ 存在" } else { "✗ 缺失" }
        }
    }
    
    # 檢查文件
    $RequiredFiles = @("VRN-Orchestrator-v2.ps1", "Config\analyze_pdf.py", "啟動VRN.ps1")
    foreach ($File in $RequiredFiles) {
        $Path = Join-Path $InstallPath $File
        $ValidationResults += [PSCustomObject]@{
            Component = "文件"
            Item      = $File
            Status    = if (Test-Path $Path) { "✓ 存在" } else { "✗ 缺失" }
        }
    }
    
    # 檢查Python
    if (Test-PythonInstalled) {
        $PythonVersion = python --version 2>&1
        $ValidationResults += [PSCustomObject]@{
            Component = "Python"
            Item      = "運行時"
            Status    = "✓ $PythonVersion"
        }
        
        # 檢查關鍵包
        $KeyPackages = @("pymupdf", "pdfplumber", "pandas")
        foreach ($Package in $KeyPackages) {
            $TestCmd = "python -c `"import $Package`" 2>&1"
            $Result = Invoke-Expression $TestCmd
            $ValidationResults += [PSCustomObject]@{
                Component = "Python包"
                Item      = $Package
                Status    = if ($LASTEXITCODE -eq 0) { "✓ 已安裝" } else { "⚠ 缺失" }
            }
        }
    } else {
        $ValidationResults += [PSCustomObject]@{
            Component = "Python"
            Item      = "運行時"
            Status    = "✗ 未安裝"
        }
    }
    
    $ValidationResults | Format-Table -AutoSize
    
    $FailedChecks = $ValidationResults | Where-Object { $_.Status -like "*✗*" }
    $WarningChecks = $ValidationResults | Where-Object { $_.Status -like "*⚠*" }
    
    Write-Host ""
    
    if ($FailedChecks.Count -eq 0 -and $WarningChecks.Count -eq 0) {
        Write-ColorOutput "驗證完成 - 安裝成功!" -Type Success
        return $true
    } elseif ($FailedChecks.Count -eq 0) {
        Write-ColorOutput "驗證完成 - 部分警告 ($($WarningChecks.Count) 項)" -Type Warning
        return $true
    } else {
        Write-ColorOutput "驗證失敗 - 發現 $($FailedChecks.Count) 個錯誤" -Type Error
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════════════

function Start-Deployment {
    Show-DeploymentBanner
    
    Write-Host "安裝路徑: " -NoNewline
    Write-Host $InstallPath -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $QuickStart -and -not $Force) {
        $Confirm = Read-Host "是否繼續? (Y/N)"
        if ($Confirm -ne 'Y') {
            Write-ColorOutput "部署已取消" -Type Info
            exit 0
        }
        Write-Host ""
    }
    
    try {
        # 步驟1: 系統檢查
        Invoke-SystemCheck
        
        # 步驟2: 安裝必要軟體
        if ($Global:NeedsPowerShell7 -and -not $SkipPowerShellInstall) {
            Install-PowerShell7
        }
        
        if ($Global:NeedsPython -and -not $SkipPythonInstall) {
            Install-Python
        }
        
        # 步驟3: 安裝Python依賴
        if (-not $SkipPythonInstall) {
            Install-PythonPackages
        }
        
        # 步驟4: 創建目錄結構
        Initialize-DirectoryStructure
        Write-Host ""
        
        # 步驟5: 部署文件
        Deploy-Files
        Write-Host ""
        
        # 步驟6: 創建啟動腳本
        New-LaunchScript
        Write-Host ""
        
        # 步驟7: 驗證安裝
        $Success = Test-Installation
        
        if ($Success) {
            Write-Host ""
            Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
            Write-Host "║                                                           ║" -ForegroundColor Green
            Write-Host "║              🎉 部署完成! 安裝成功! 🎉                      ║" -ForegroundColor Green
            Write-Host "║                                                           ║" -ForegroundColor Green
            Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
            Write-Host ""
            Write-Host "快速啟動方式:" -ForegroundColor Cyan
            Write-Host "  方法1: 雙擊 " -NoNewline
            Write-Host "$InstallPath\啟動VRN.ps1" -ForegroundColor Yellow
            Write-Host "  方法2: 命令行執行 " -NoNewline
            Write-Host "pwsh -File `"$InstallPath\VRN-Orchestrator-v2.ps1`"" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "詳細文檔: " -NoNewline
            Write-Host "$InstallPath\README.md" -ForegroundColor Cyan
            Write-Host ""
        } else {
            Write-ColorOutput "部署過程中遇到問題,請檢查上方輸出" -Type Warning
        }
        
    } catch {
        Write-ColorOutput "部署失敗: $_" -Type Error
        Write-Host $_.ScriptStackTrace -ForegroundColor Red
        exit 1
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 執行部署
# ═══════════════════════════════════════════════════════════════════════════════

Start-Deployment

# ═══════════════════════════════════════════════════════════════════════════════
# 腳本執行完畢，等待用戶確認
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  部署腳本執行完畢 - 請查看上面的結果" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Read-Host "按Enter鍵關閉視窗"

