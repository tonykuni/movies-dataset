param(
  [string]$InputPath="C:\測試樣本報告",
  [string]$Python="python",
  [string]$OutDir="",
  [switch]$Doctor,
  [switch]$SelfTest,
  [switch]$OpenHtml
)
$ErrorActionPreference="Stop"
$Root=$PSScriptRoot
$Engine=Join-Path $Root "engine\VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300.py"
if(-not $OutDir){$OutDir=Join-Path $Root "output"}
Write-Host "=============================================================="
Write-Host " VIA NON-STOCK SUMMARIZER ENGINE v0300"
Write-Host " VRN-2 Layout + Text Repair + NLP | One Report One Row"
Write-Host "=============================================================="
if($Doctor){ & $Python $Engine --doctor; Read-Host "Press Enter"; exit $LASTEXITCODE }
if($SelfTest){ & $Python $Engine --selftest; Read-Host "Press Enter"; exit $LASTEXITCODE }
& $Python $Engine $InputPath --outdir $OutDir
$rc=$LASTEXITCODE
if($OpenHtml){$h=Join-Path $OutDir "REPORT_SUMMARY.html"; if(Test-Path $h){Start-Process $h}}
Read-Host "Press Enter to close"
exit $rc
