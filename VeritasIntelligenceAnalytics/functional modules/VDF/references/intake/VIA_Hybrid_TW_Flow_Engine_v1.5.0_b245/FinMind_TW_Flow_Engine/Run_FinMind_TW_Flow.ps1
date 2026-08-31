$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".venv")) {
    py -3.12 -m venv .venv
}

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

$Nexus = Join-Path $PSScriptRoot "Invoke-VeritasCodexNexus.ps1"
$ForwardArgs = @($args)
& pwsh -NoLogo -NoProfile -File $Nexus `
    -Mode FinMind `
    -Task Fetch `
    -Python $Python `
    -FinMindEnginePath (Join-Path $PSScriptRoot "VIA_FinMind_TW_Flow_Engine.py") `
    -CeleritasPath (Join-Path $PSScriptRoot "VeritasCeleritas.py") `
    -AegisPath (Join-Path $PSScriptRoot "VeritasAegisNexus.py") `
    -FinMindArgs $ForwardArgs
$ExitCode = $LASTEXITCODE

Write-Host "`nEngine exit code: $ExitCode"
Read-Host "按 Enter 結束（視窗不會自動關閉）"
exit $ExitCode
