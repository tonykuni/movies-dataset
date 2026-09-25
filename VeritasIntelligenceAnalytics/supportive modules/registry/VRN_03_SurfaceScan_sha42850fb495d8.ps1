# VRN · Safe Stream 03 · SurfaceScan
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
$Target = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
if(-not $Target -or -not(Test-Path -LiteralPath $Target -PathType Leaf)){ Write-Host "[WARN] Missing target: $Target" -ForegroundColor Yellow; return }
$text=Get-Content -LiteralPath $Target -Raw -Encoding UTF8
$functionCount=([regex]::Matches($text,'(?im)^\s*function\s+')).Count
$paramCount=([regex]::Matches($text,'(?im)^\s*param\s*\(')).Count
$danger=([regex]::Matches($text,'(?i)\bStop-Process\b|\bRemove-Item\b|\bSet-Content\b|\bStart-Process\b|\bsys\.exit\b|\bexit\b')).Count
Write-Host "[OK] SurfaceScan completed." -ForegroundColor Green
Write-Host "Functions     : $functionCount"
Write-Host "ParamBlocks    : $paramCount"
Write-Host "ReviewTokens   : $danger"
Write-Host "[HOLD] SurfaceScan is read-only." -ForegroundColor Yellow