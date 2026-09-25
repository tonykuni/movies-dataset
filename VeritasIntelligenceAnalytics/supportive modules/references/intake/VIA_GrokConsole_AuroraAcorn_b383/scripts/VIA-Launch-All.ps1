#requires -Version 7.0
# VIA · 全啟動 → 轉交 VIA-Activate.ps1（GitHub 對帳 + 探針）
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$act = Join-Path $here 'VIA-Activate.ps1'
if (Test-Path -LiteralPath $act) {
    & $act
    return
}
# 後備：舊路徑探針
$Root = "C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics"
if (-not (Test-Path -LiteralPath $Root)) {
    Write-Host "ROOT_MISSING  $Root" -ForegroundColor Yellow
    return
}
Set-Location -LiteralPath $Root
Write-Host "ENTER  $(Get-Location)" -ForegroundColor Green
return
