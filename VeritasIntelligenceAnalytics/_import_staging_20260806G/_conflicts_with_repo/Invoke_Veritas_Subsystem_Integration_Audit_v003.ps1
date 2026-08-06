# Veritas Subsystem Integration Audit v003 · review-only launcher
$ErrorActionPreference = "Stop"
$def_Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_LocalPy = "py"
$def_Script = Join-Path $def_Base "Veritas_Subsystem_Integration_Audit_v003.py"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def Veritas · Subsystem Integration Audit v003" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def Policy: append-only · review-only · no DB write · no canonical merge · no delete" -ForegroundColor Yellow
if (!(Test-Path $def_Script)) {
  Write-Host "def Script not found at project root. Put Veritas_Subsystem_Integration_Audit_v003.py there first." -ForegroundColor Red
  Write-Host "def PowerShell remains open." -ForegroundColor Cyan
  return
}
& $def_LocalPy -3.13 $def_Script
Write-Host ""
Write-Host "def PowerShell remains open." -ForegroundColor Cyan
