[CmdletBinding()]
param(
    [string]$GroupMap = '',
    [string]$DuckDBPath = '',
    [string]$OutputRoot = '',
    [string]$EndDate = 'latest'
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Resolve-DragDropPath {
    param([string]$Value)
    return $Value.Trim().Trim('"').Trim("'")
}

if (-not (Test-Path -LiteralPath '.venv')) {
    py -3.12 -m venv .venv
}

$Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')

if (-not $GroupMap) {
    $GroupMap = Read-Host '請拖入股票族群對照 CSV/Parquet，或輸入完整路徑'
}
$GroupMap = Resolve-DragDropPath -Value $GroupMap
if (-not (Test-Path -LiteralPath $GroupMap)) {
    throw "族群對照檔不存在：$GroupMap"
}

if (-not $DuckDBPath) {
    $DuckDBPath = Join-Path $PSScriptRoot '_codex_out\FinMind_TW_Flow_Output\FinMind_TW_Flow.duckdb'
}
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $PSScriptRoot '_codex_out\FinMind_TW_Flow_Output\capital_circle'
}
$DuckDBPath = Resolve-DragDropPath -Value $DuckDBPath
$OutputRoot = Resolve-DragDropPath -Value $OutputRoot

$Nexus = Join-Path $PSScriptRoot 'Invoke-VeritasCodexNexus.ps1'
$Analyzer = Join-Path $PSScriptRoot 'VIA_TW_Branch_Capital_Circle_Engine.py'
$AnalyzerArgs = @(
    '--duckdb', $DuckDBPath,
    '--group-map', $GroupMap,
    '--output-root', $OutputRoot,
    '--end-date', $EndDate
)

& pwsh -NoLogo -NoProfile -File $Nexus `
    -Mode FinMind `
    -Task AnalyzeCapitalCircle `
    -Python $Python `
    -CapitalCircleEnginePath $Analyzer `
    -CapitalCircleArgs $AnalyzerArgs
$ExitCode = $LASTEXITCODE

Write-Host "`nCapital Circle engine exit code: $ExitCode"
Read-Host '按 Enter 結束（視窗不會自動關閉）'
exit $ExitCode
