# VIA Strongest MultiProject First Step
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
pwsh -NoProfile -ExecutionPolicy Bypass -File "" -Root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" -SupportiveDir "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules" -FunctionalRoot "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules" -CreateSandbox $True -RunToolDryProbe $True -RunUserSmokeTest $False -OpenReport $True

