# VIA Supportive HardGate Seal
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
$VIA_SUPPORTIVE_HARDGATE_SEALED = $true
$VIA_SUPPORTIVE_HARDGATE_JSON = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Supportive_HardGate_Seal.json"
$VIA_SUPPORTIVE_HARDGATE_RUNNER = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\Invoke-VIA-SupportiveHardGate.ps1"

