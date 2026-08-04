#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VDF Lane 1 · Final Seal Health" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Read active/frozen pointer and open latest final report."
Write-Host ""

$PointerPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VDF_ACTIVE_POINTER.json"
$RelatedPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active"

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