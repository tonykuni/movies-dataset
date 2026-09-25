# VIA Strongest First Step Command
# Safe read-only + additive bootstrap.
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
pwsh -NoProfile -ExecutionPolicy Bypass -File "" -Root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" -Downloads "C:\Users\tonyk\Downloads" -SupportiveDir "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules" -AllowNetworkInstall $True -InstallLightPSModules $True -InstallHeavyPythonPackages $False -RunToolDryProbe $True -CreateSandbox $True -OpenReport $True

