param(
    [string]$UnifiedInputSSOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json",
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

try {
    if (-not [System.IO.File]::Exists($UnifiedInputSSOT)) {
        throw "UnifiedInputSSOT missing."
    }

    $cfg = Get-Content -LiteralPath $UnifiedInputSSOT -Raw -Encoding UTF8 | ConvertFrom-Json

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA ACTIVATION GATEWAY PARAM FIRST" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Action : $Action"
    Write-Host "SSOT   : $UnifiedInputSSOT"
    Write-Host "Status : READY"
    Write-Host "PowerShell remains open. No exit was called." -ForegroundColor Green
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "PowerShell remains open. No exit was called." -ForegroundColor Yellow
}
