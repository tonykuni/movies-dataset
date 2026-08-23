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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
