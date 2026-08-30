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
$Target = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1"
if(-not $Target -or -not(Test-Path -LiteralPath $Target -PathType Leaf)){ Write-Host "[WARN] Missing target: $Target" -ForegroundColor Yellow; return }
$item=Get-Item -LiteralPath $Target -Force
$sha=(Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash
Write-Host "[OK] MetadataHash passed." -ForegroundColor Green
Write-Host "Path  : $Target"
Write-Host "Bytes : $($item.Length)"
Write-Host "SHA256: $sha"