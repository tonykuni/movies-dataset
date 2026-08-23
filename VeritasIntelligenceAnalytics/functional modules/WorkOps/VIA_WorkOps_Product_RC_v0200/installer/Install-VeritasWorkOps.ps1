#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$InstallRoot = "$env:LOCALAPPDATA\VeritasWorkOps",
    [switch]$SkipDependencies
)
$ErrorActionPreference = "Stop"
function def_Step([string]$Name,[int]$Pct) {
    Write-Progress -Activity "Veritas WorkOps Installation" -Status $Name -PercentComplete $Pct
    Write-Host ("def [{0,3}%] {1}" -f $Pct,$Name) -ForegroundColor Cyan
}
try {
    def_Step "Preflight" 5
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw "PowerShell 7+ required." }
    $Source = Split-Path -Parent $PSScriptRoot
    if (-not (Test-Path (Join-Path $Source "engines\VIA_ENG105_WorkopsApiServer.py"))) { throw "Invalid WorkOps package source." }

    def_Step "Prepare install root" 15
    New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
    $AppRoot = Join-Path $InstallRoot "app"
    if (-not (Test-Path $AppRoot)) {
        New-Item -ItemType Directory -Force -Path $AppRoot | Out-Null
    }

    # Append/update installation: never delete user data/config.
    def_Step "Copy application files" 25
    # Program assets may be updated. User-owned config is never overwritten.
    $CopyDirs = @("engines","ui","templates","manifests","registry","docs")
    foreach ($d in $CopyDirs) {
        $src = Join-Path $Source $d
        $dst = Join-Path $AppRoot $d
        if (Test-Path $src) {
            New-Item -ItemType Directory -Force -Path $dst | Out-Null
            Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
        }
    }
    $ConfigSrc = Join-Path $Source "config"
    $ConfigDst = Join-Path $AppRoot "config"
    New-Item -ItemType Directory -Force -Path $ConfigDst | Out-Null
    if (Test-Path $ConfigSrc) {
        Get-ChildItem -Path $ConfigSrc -File | ForEach-Object {
            $Target = Join-Path $ConfigDst $_.Name
            if (-not (Test-Path $Target)) {
                Copy-Item $_.FullName $Target
                Write-Host "def CONFIG INIT : $($_.Name)" -ForegroundColor Green
            } else {
                Write-Host "def CONFIG KEEP : $($_.Name)" -ForegroundColor DarkGray
            }
        }
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $AppRoot "templates\user") | Out-Null
    foreach ($f in @("requirements-core.txt","requirements-windows.txt","README_PRODUCT.md")) {
        if (Test-Path (Join-Path $Source $f)) { Copy-Item (Join-Path $Source $f) (Join-Path $AppRoot $f) -Force }
    }

    # Preserve runtime data across upgrades.
    foreach ($d in @("out","runtime","ssot","backups","restore_staging","logs","benchmark")) {
        New-Item -ItemType Directory -Force -Path (Join-Path $AppRoot $d) | Out-Null
    }

    def_Step "Locate Python 3.12+" 35
    $Python = $null
    foreach ($candidate in @("py","python","C:\Python313\python.exe","C:\Python312\python.exe")) {
        try {
            if ($candidate -eq "py") {
                $v = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $v) { $Python = $v.Trim(); break }
            } else {
                $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
                if ($cmd) {
                    $ver = & $cmd.Source -c "import sys; print(int(sys.version_info >= (3,12)))" 2>$null
                    if ($ver -eq "1") { $Python = $cmd.Source; break }
                } elseif (Test-Path $candidate) {
                    $ver = & $candidate -c "import sys; print(int(sys.version_info >= (3,12)))"
                    if ($ver -eq "1") { $Python = $candidate; break }
                }
            }
        } catch {}
    }
    if (-not $Python) { throw "Python 3.12+ not found. Install Python first or use winget: winget install Python.Python.3.12" }

    def_Step "Create/reuse local venv" 45
    $Venv = Join-Path $InstallRoot "venv"
    if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
        & $Python -m venv $Venv
        if ($LASTEXITCODE -ne 0) { throw "venv creation failed." }
    }
    $Vpy = Join-Path $Venv "Scripts\python.exe"

    if (-not $SkipDependencies) {
        def_Step "Install Python dependencies" 60
        & $Vpy -m pip install --upgrade pip
        & $Vpy -m pip install -r (Join-Path $AppRoot "requirements-core.txt")
        if ($LASTEXITCODE -ne 0) { throw "Core dependency install failed." }
        & $Vpy -m pip install -r (Join-Path $AppRoot "requirements-windows.txt")
        if ($LASTEXITCODE -ne 0) { Write-Host "def WARN Windows optional dependencies not fully installed." -ForegroundColor Yellow }
    }

    def_Step "Compile and health check" 75
    & $Vpy -m compileall -q (Join-Path $AppRoot "engines")
    if ($LASTEXITCODE -ne 0) { throw "Python compile failed." }

    Push-Location $AppRoot
    try {
        & $Vpy "engines\VIA_ENG136_WorkopsSsotStore.py" snapshot | Out-Null
        & $Vpy "engines\workops_module_lifecycle_manager.py" health | Out-Null
        & $Vpy "engines\VIA_ENG113_WorkopsDiagnostics.py" build | Out-Null
    } finally { Pop-Location }

    def_Step "Create launcher" 85
    $Launcher = Join-Path $InstallRoot "Start-VeritasWorkOps.ps1"
    @"
#requires -Version 7.0
`$ErrorActionPreference = 'Stop'
`$AppRoot = '$($AppRoot.Replace("'","''"))'
`$Python = '$($Vpy.Replace("'","''"))'
Set-Location `$AppRoot
Start-Process -FilePath `$Python -ArgumentList @('engines\VIA_ENG105_WorkopsApiServer.py') -WorkingDirectory `$AppRoot
Start-Sleep -Milliseconds 900
Start-Process 'http://127.0.0.1:8775/'
"@ | Set-Content -Path $Launcher -Encoding UTF8

    # Desktop shortcut, current user only.
    try {
        $Desktop = [Environment]::GetFolderPath("Desktop")
        $ShortcutPath = Join-Path $Desktop "Veritas WorkOps.lnk"
        $Shell = New-Object -ComObject WScript.Shell
        $Shortcut = $Shell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = (Get-Command pwsh).Source
        $Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`""
        $Shortcut.WorkingDirectory = $AppRoot
        $Shortcut.Description = "Veritas WorkOps"
        $Shortcut.Save()
    } catch { Write-Host "def WARN Desktop shortcut not created: $($_.Exception.Message)" -ForegroundColor Yellow }

    def_Step "Write install receipt" 95
    $Pkgs = & $Vpy -m pip freeze
    $Receipt = [ordered]@{
        InstalledAt = (Get-Date).ToString("o")
        InstallRoot = $InstallRoot
        AppRoot = $AppRoot
        Python = $Vpy
        PowerShell = $PSVersionTable.PSVersion.ToString()
        Packages = @($Pkgs)
        Policy = "local-only / no auto-send / no mailbox delete / human-confirm critical actions"
    }
    $Receipt | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $InstallRoot "install_receipt.json") -Encoding UTF8

    def_Step "Complete" 100
    Write-Progress -Activity "Veritas WorkOps Installation" -Completed
    Write-Host ""
    Write-Host "def INSTALL PASS" -ForegroundColor Green
    Write-Host "def Launcher : $Launcher"
    Write-Host "def App      : http://127.0.0.1:8775/"
}
catch {
    Write-Progress -Activity "Veritas WorkOps Installation" -Completed
    Write-Host "def INSTALL FAIL: $($_.Exception.Message)" -ForegroundColor Red
    throw
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
