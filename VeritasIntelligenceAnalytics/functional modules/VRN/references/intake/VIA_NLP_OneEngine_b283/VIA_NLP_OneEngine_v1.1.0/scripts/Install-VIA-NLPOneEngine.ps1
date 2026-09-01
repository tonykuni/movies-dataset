[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonCommand = "py",
    [string]$PythonVersion = "3.12",
    [string]$VenvName = ".venv",
    [ValidateSet("minimal", "api", "ml", "full")]
    [string]$InstallProfile = "ml",
    [switch]$Offline,
    [switch]$ForceRecreate,
    [switch]$RunTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"


function Write-Step {
    param([string]$Message)
    Write-Host ("[VIA] " + $Message) -ForegroundColor Cyan
}


function Resolve-ProjectPath {
    param([string]$InputPath)
    $resolved = [System.IO.Path]::GetFullPath($InputPath)
    if (-not (Test-Path -LiteralPath (Join-Path $resolved "pyproject.toml") -PathType Leaf)) {
        throw "pyproject.toml not found under: $resolved"
    }
    return $resolved
}


function Resolve-PythonLauncher {
    param([string]$Command, [string]$Version)
    $found = Get-Command $Command -ErrorAction Stop
    if ($Command -eq "py" -or $found.Name -eq "py.exe") {
        return @($found.Source, "-$Version")
    }
    return @($found.Source)
}


function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')"
    }
}


function Get-InstallTarget {
    param([string]$Profile)
    switch ($Profile) {
        "minimal" { return "." }
        "api" { return ".[api,monitor]" }
        "ml" { return ".[api,monitor,ml,zh,documents]" }
        "full" { return ".[all,test]" }
        default { throw "Unsupported install profile: $Profile" }
    }
}


function Test-SafeVenvTarget {
    param([string]$Root, [string]$VenvPath)
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $venvFull = [System.IO.Path]::GetFullPath($VenvPath).TrimEnd('\', '/')
    if (-not $venvFull.StartsWith($rootFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Venv must be located inside ProjectRoot: $venvFull"
    }
    if ($venvFull -eq $rootFull) {
        throw "Refusing to use the project root as a venv target."
    }
}


$ProjectRoot = Resolve-ProjectPath -InputPath $ProjectRoot
$VenvPath = Join-Path $ProjectRoot $VenvName
Test-SafeVenvTarget -Root $ProjectRoot -VenvPath $VenvPath
$Launcher = Resolve-PythonLauncher -Command $PythonCommand -Version $PythonVersion
$LauncherExe = $Launcher[0]
$LauncherArgs = @($Launcher | Select-Object -Skip 1)

Write-Step "VIA NLP One Engine preflight"
Invoke-Checked -Executable $LauncherExe -Arguments ($LauncherArgs + @("-c", "import sys; assert sys.version_info >= (3,11), sys.version"))

if ($ForceRecreate -and (Test-Path -LiteralPath $VenvPath)) {
    Write-Step "Remove explicitly selected project-local virtual environment"
    Remove-Item -LiteralPath $VenvPath -Recurse -Force
}

if (-not (Test-Path -LiteralPath $VenvPath)) {
    Write-Step "Create isolated virtual environment"
    Invoke-Checked -Executable $LauncherExe -Arguments ($LauncherArgs + @("-m", "venv", $VenvPath))
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "Virtual environment Python not found: $VenvPython"
}

if (-not $Offline) {
    Write-Step "Update packaging tools"
    Invoke-Checked -Executable $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
}

$InstallTarget = Get-InstallTarget -Profile $InstallProfile
Write-Step "Install profile: $InstallProfile"
$InstallArguments = @("-m", "pip", "install", "--editable", $InstallTarget)
if ($Offline) {
    $InstallArguments += "--no-index"
}
Invoke-Checked -Executable $VenvPython -Arguments $InstallArguments

Write-Step "Run engine health check"
Invoke-Checked -Executable $VenvPython -Arguments @("-m", "via_nlp_engine", "--config", (Join-Path $ProjectRoot "config\default.json"), "health")

if ($RunTests) {
    Write-Step "Run complete unit and integration suite"
    Invoke-Checked -Executable $VenvPython -Arguments @((Join-Path $ProjectRoot "scripts\run_tests.py"))
}

Write-Host ""
Write-Host "VIA NLP One Engine is ready." -ForegroundColor Green
Write-Host "Python : $VenvPython"
Write-Host "Health : & `"$VenvPython`" -m via_nlp_engine --config `"$(Join-Path $ProjectRoot 'config\default.json')`" health"
Write-Host "Server : & `"$VenvPython`" -m via_nlp_engine --config `"$(Join-Path $ProjectRoot 'config\default.json')`" serve"
