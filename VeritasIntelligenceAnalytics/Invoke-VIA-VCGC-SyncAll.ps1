#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $via
Set-Location -LiteralPath $root
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path $via "supportive modules/registry/CGC_MDL192_MacroParamSync_v0100.py"
$know = Join-Path $via "supportive modules/registry/CGC_MDL191_KnowledgeAsset_v0100.py"
$refresh = Join-Path $via "functional modules/VDF/engine/VDF_ENG113_MacroMethod_v0100.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python $py
if ($LASTEXITCODE -ne 0) { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; exit $LASTEXITCODE }
& python $know
if ($LASTEXITCODE -ne 0) { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; exit $LASTEXITCODE }
if ([string]::IsNullOrWhiteSpace($env:FRED_API_KEY)) {
    Write-Host '{"via":"vcgc","refresh":"SKIP","why":"FRED_API_KEY is not set"}'
} else {
    & python $refresh --refresh
}
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $LASTEXITCODE
