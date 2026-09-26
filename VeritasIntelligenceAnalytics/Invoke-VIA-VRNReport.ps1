#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Split-Path -Parent $via)
$env:VIA_FROM_VCGC = "YES"
if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
$folder = Join-Path $via "functional modules/VRN"
$eng = Get-ChildItem -LiteralPath $folder -Filter "VRN_ENG110_TabReport_v*.py" | Sort-Object Name | Select-Object -Last 1
if (-not $eng) { throw "VRN_ENG110_TabReport 不在這棵樹" }
$py = "python"
foreach ($cand in @(
        (Join-Path $env:USERPROFILE "envs\via_vrn_312\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_vdf_312\Scripts\python.exe"),
        "python")) {
    if (-not (Test-Path -LiteralPath $cand) -and -not (Get-Command $cand -ErrorAction SilentlyContinue)) { continue }
    & $cand -c "import fitz" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $cand; break }
}
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& $py $eng.FullName
$code = $LASTEXITCODE
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
