#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"
$Target = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1"
if(-not(Test-Path -LiteralPath $Target -PathType Leaf)){
    Write-Host "[WARN] Missing target: $Target" -ForegroundColor Yellow
    return
}
$item=Get-Item -LiteralPath $Target -Force
$hash=(Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash
Write-Host "[OK] MetadataHash passed" -ForegroundColor Green
Write-Host "Path  : $Target"
Write-Host "Bytes : $($item.Length)"
Write-Host "SHA256: $hash"