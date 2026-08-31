#requires -Version 7.0
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VRN Lane 1 · Active Entry Health" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Read-only VRN entry health. Does not run extraction."
Write-Host ""

$PointerPath = ""
$RelatedPath = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\Invoke-VRN.ps1"

function Read-JsonSafe($Path){
    try {
        if(Test-Path -LiteralPath $Path){
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {}
    return $null
}

if($PointerPath -and (Test-Path -LiteralPath $PointerPath)){
    $p = Read-JsonSafe $PointerPath
    if($p){
        Write-Host "Pointer Status : $($p.status)"
        Write-Host "Pointer Risk   : $($p.risk)"
        Write-Host "Pointer Path   : $PointerPath"
    }
}

if($RelatedPath){
    Write-Host "Related Path   : $RelatedPath"
    if(Test-Path -LiteralPath $RelatedPath){
        if((Get-Item -LiteralPath $RelatedPath).PSIsContainer){
            Write-Host "Related Exists : Directory"
            $html = Get-ChildItem -LiteralPath $RelatedPath -Recurse -File -Filter "*.html" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if($html){
                Write-Host "Opening HTML   : $($html.FullName)"
                Start-Process $html.FullName
            }
        } else {
            Write-Host "Related Exists : File"
        }
    } else {
        Write-Host "Related Exists : False" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Read-only launcher. No DB write. No Stop-Process. No destructive delete." -ForegroundColor Green

