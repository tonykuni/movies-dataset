#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VRN Lane 3 · Engine Capability Plan" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Read-only VRN engine/capability review."
Write-Host ""

$PointerPath = ""
$RelatedPath = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"

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