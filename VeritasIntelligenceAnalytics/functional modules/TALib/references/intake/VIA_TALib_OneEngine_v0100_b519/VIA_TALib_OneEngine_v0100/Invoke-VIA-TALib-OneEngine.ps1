[CmdletBinding()]
param(
    [ValidateSet("run", "validate", "catalog", "defaults", "self-test")]
    [string]$Mode = "self-test",
    [string]$Config = (Join-Path $PSScriptRoot "VIA_TALib_OneEngine.config.json"),
    [string]$Source = "",
    [string]$Database = "",
    [ValidateSet("auto", "duckdb", "sqlite", "sqlalchemy")]
    [string]$DatabaseType = "auto",
    [string]$DatabaseUrl = "",
    [string]$Table = "",
    [string]$Query = "",
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "output"),
    [ValidateSet("raw", "ex_daytrade")]
    [string]$DisplayMode = "raw",
    [string]$Functions = "",
    [string]$Formats = "parquet,csv",
    [string]$CatalogOutput = "",
    [string]$DefaultsOutput = "",
    [string]$Python = "",
    [switch]$Install
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$EnginePath = Join-Path $PSScriptRoot "VIA_TALib_OneEngine.py"
$RequirementsPath = Join-Path $PSScriptRoot "requirements.txt"

function Resolve-ViaPython {
    param([string]$RequestedPython)

    if ($RequestedPython) {
        return $RequestedPython
    }
    $Candidates = @(
        (Join-Path $env:USERPROFILE "miniconda3\envs\via_vdf\python.exe"),
        (Join-Path $env:USERPROFILE "anaconda3\envs\via_vdf\python.exe"),
        (Join-Path $env:USERPROFILE "miniforge3\envs\via_vdf\python.exe"),
        "python"
    )
    foreach ($Candidate in $Candidates) {
        if ($Candidate -eq "python") {
            $Command = Get-Command python -ErrorAction SilentlyContinue
            if ($Command) {
                return $Command.Source
            }
        }
        elseif (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return $Candidate
        }
    }
    throw "找不到 Python；請以 -Python 指定 via_vdf 的 python.exe。"
}

function Add-ArgumentValue {
    param(
        [System.Collections.Generic.List[string]]$Arguments,
        [string]$Name,
        [string]$Value
    )

    if (-not [string]::IsNullOrWhiteSpace($Value)) {
        $Arguments.Add($Name)
        $Arguments.Add($Value)
    }
}

function Invoke-OneEngine {
    param([string]$PythonPath)

    $Arguments = [System.Collections.Generic.List[string]]::new()
    $Arguments.Add($EnginePath)
    $Arguments.Add($Mode)

    if ($Mode -in @("run", "validate", "catalog", "self-test")) {
        Add-ArgumentValue -Arguments $Arguments -Name "--config" -Value $Config
    }
    if ($Mode -in @("run", "validate")) {
        Add-ArgumentValue -Arguments $Arguments -Name "--source" -Value $Source
        Add-ArgumentValue -Arguments $Arguments -Name "--database" -Value $Database
        Add-ArgumentValue -Arguments $Arguments -Name "--database-type" -Value $DatabaseType
        Add-ArgumentValue -Arguments $Arguments -Name "--database-url" -Value $DatabaseUrl
        Add-ArgumentValue -Arguments $Arguments -Name "--table" -Value $Table
        Add-ArgumentValue -Arguments $Arguments -Name "--query" -Value $Query
    }
    if ($Mode -eq "run") {
        Add-ArgumentValue -Arguments $Arguments -Name "--output-dir" -Value $OutputDirectory
        Add-ArgumentValue -Arguments $Arguments -Name "--display-mode" -Value $DisplayMode
        Add-ArgumentValue -Arguments $Arguments -Name "--functions" -Value $Functions
        Add-ArgumentValue -Arguments $Arguments -Name "--formats" -Value $Formats
    }
    if ($Mode -eq "catalog") {
        Add-ArgumentValue -Arguments $Arguments -Name "--output" -Value $CatalogOutput
    }
    if ($Mode -eq "defaults") {
        Add-ArgumentValue -Arguments $Arguments -Name "--output" -Value $DefaultsOutput
    }

    & $PythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "VIA TA-Lib OneEngine 結束碼：$LASTEXITCODE"
    }
}

function Main {
    $PythonPath = Resolve-ViaPython -RequestedPython $Python
    if ($Install) {
        & $PythonPath -m pip install -r $RequirementsPath
        if ($LASTEXITCODE -ne 0) {
            throw "相依套件安裝失敗。"
        }
    }
    Invoke-OneEngine -PythonPath $PythonPath
}

Main

