$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath '.venv')) {
    py -3.12 -m venv .venv
}

$Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')

$Nexus = Join-Path $PSScriptRoot 'Invoke-VeritasCodexNexus.ps1'
$Engine = Join-Path $PSScriptRoot 'VIA_FinMind_TW_Flow_Engine.py'
$ForwardArgs = @(
    '--source-mode', 'finmind_only',
    '--latest-only',
    '--datasets', 'TaiwanStockTradingDailyReport,TaiwanStockTradingDailyReportSecIdAgg',
    '--branch-mode', 'auto',
    '--range-batch-mode', 'full_history',
    '--yes'
)

& pwsh -NoLogo -NoProfile -File $Nexus `
    -Mode FinMind `
    -Task Fetch `
    -Python $Python `
    -FinMindEnginePath $Engine `
    -CeleritasPath (Join-Path $PSScriptRoot 'VeritasCeleritas.py') `
    -AegisPath (Join-Path $PSScriptRoot 'VeritasAegisNexus.py') `
    -FinMindArgs $ForwardArgs
$ExitCode = $LASTEXITCODE

Write-Host "`nLatest branch fetch exit code: $ExitCode"
Read-Host '按 Enter 結束（視窗不會自動關閉）'
exit $ExitCode
