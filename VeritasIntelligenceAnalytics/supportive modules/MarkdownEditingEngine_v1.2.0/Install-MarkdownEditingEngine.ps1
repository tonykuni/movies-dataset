[CmdletBinding()]
param(
    [switch]$InstallSystemRuntimes,
    [switch]$SkipNode,
    [switch]$SkipPython,
    [switch]$SkipRust,
    [switch]$SkipGo,
    [switch]$SkipPandoc,
    [switch]$SkipMdBook,
    [string[]]$PythonIndexUrls = @(
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "https://mirrors.aliyun.com/pypi/simple",
        "https://pypi.org/simple"
    ),
    [switch]$WaitForKey
)

$ErrorActionPreference = "Stop"
$EngineRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvRoot = Join-Path $EngineRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$RequirementsPath = Join-Path $EngineRoot "requirements.lock.txt"
$CargoManifest = Join-Path $EngineRoot "rust\Cargo.toml"
$RustOutput = Join-Path $EngineRoot "bin\mdscan.exe"
$GoSource = Join-Path $EngineRoot "go\cmd\mdlinkcheck"
$GoOutput = Join-Path $EngineRoot "bin\mdlinkcheck.exe"
$InstallReportRoot = Join-Path $EngineRoot "reports\install"
$InstallRunId = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$WingetPackages = @{
    Python = "Python.Python.3.12"
    Node = "OpenJS.NodeJS.LTS"
    Pandoc = "JohnMacFarlane.Pandoc"
    Rust = "Rustlang.Rustup"
    Go = "GoLang.Go"
}

function defAssert-NativeSuccess {
    param([Parameter(Mandatory)][string]$Name)
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE." }
}

function defRefresh-ProcessPath {
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = @($MachinePath, $UserPath) -join ";"
}

function defInstall-WingetPackage {
    param([Parameter(Mandatory)][string]$Id)
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is unavailable; install $Id manually."
    }
    & winget install --id $Id --exact --accept-package-agreements --accept-source-agreements --silent
    defAssert-NativeSuccess -Name "winget install $Id"
    defRefresh-ProcessPath
}

function defEnsure-Command {
    param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$WingetId)
    if (Get-Command $Name -ErrorAction SilentlyContinue) { return }
    if (-not $InstallSystemRuntimes) {
        throw "$Name is missing. Re-run with -InstallSystemRuntimes or install it manually."
    }
    defInstall-WingetPackage -Id $WingetId
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name remains unavailable after installing $WingetId. Start a new PowerShell session and run the installer again."
    }
}

function defInstall-PythonTools {
    if ($SkipPython) { return }
    defEnsure-Command -Name "python" -WingetId $WingetPackages.Python
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        & python -m venv $VenvRoot
        defAssert-NativeSuccess -Name "Python venv creation"
    }
    New-Item -ItemType Directory -Path $InstallReportRoot -Force | Out-Null
    & $VenvPython -m pip freeze | Set-Content -LiteralPath (Join-Path $InstallReportRoot "pip-freeze-before-$InstallRunId.txt") -Encoding utf8
    $Installed = $false
    foreach ($IndexUrl in $PythonIndexUrls) {
        Write-Host "Trying Python package index: $IndexUrl"
        & $VenvPython -m pip install --index-url $IndexUrl --upgrade pip
        if ($LASTEXITCODE -ne 0) { continue }
        & $VenvPython -m pip install --index-url $IndexUrl --requirement $RequirementsPath
        if ($LASTEXITCODE -eq 0) {
            $Installed = $true
            break
        }
    }
    if (-not $Installed) { throw "Python dependency installation failed on all configured package indexes." }
    & $VenvPython -m pip check
    defAssert-NativeSuccess -Name "Python dependency consistency check"
    & $VenvPython -m pip freeze | Set-Content -LiteralPath (Join-Path $InstallReportRoot "pip-freeze-after-$InstallRunId.txt") -Encoding utf8
}

function defInstall-NodeTools {
    if ($SkipNode) { return }
    defEnsure-Command -Name "node" -WingetId $WingetPackages.Node
    defEnsure-Command -Name "npm" -WingetId $WingetPackages.Node
    Push-Location $EngineRoot
    try {
        & npm install --ignore-scripts --no-audit --no-fund
        defAssert-NativeSuccess -Name "Node dependency installation"
    }
    finally { Pop-Location }
}

function defBuild-RustValidator {
    if ($SkipRust) { return }
    defEnsure-Command -Name "cargo" -WingetId $WingetPackages.Rust
    & cargo build --release --manifest-path $CargoManifest
    defAssert-NativeSuccess -Name "Rust validator build"
    Copy-Item -LiteralPath (Join-Path $EngineRoot "rust\target\release\mdscan.exe") -Destination $RustOutput -Force
}

function defBuild-GoValidator {
    if ($SkipGo) { return }
    defEnsure-Command -Name "go" -WingetId $WingetPackages.Go
    Push-Location (Join-Path $EngineRoot "go")
    try {
        & go build -trimpath -o $GoOutput $GoSource
        defAssert-NativeSuccess -Name "Go validator build"
    }
    finally { Pop-Location }
}

function defInstall-DocumentBuilders {
    if (-not $SkipPandoc) { defEnsure-Command -Name "pandoc" -WingetId $WingetPackages.Pandoc }
    if (-not $SkipMdBook) {
        defEnsure-Command -Name "cargo" -WingetId $WingetPackages.Rust
        if (-not (Get-Command mdbook -ErrorAction SilentlyContinue)) {
            & cargo install mdbook --locked
            defAssert-NativeSuccess -Name "mdBook installation"
        }
    }
}

function defMain {
    New-Item -ItemType Directory -Path (Join-Path $EngineRoot "bin") -Force | Out-Null
    defInstall-PythonTools
    defInstall-NodeTools
    defBuild-RustValidator
    defBuild-GoValidator
    defInstall-DocumentBuilders
    & (Join-Path $EngineRoot "MarkdownEditingEngine.ps1") doctor
    defAssert-NativeSuccess -Name "MarkdownEditingEngine doctor"
}

defMain
[Environment]::ExitCode = 0
if ($WaitForKey) {
    Read-Host "安裝與檢查完成，按 Enter 關閉"
}
