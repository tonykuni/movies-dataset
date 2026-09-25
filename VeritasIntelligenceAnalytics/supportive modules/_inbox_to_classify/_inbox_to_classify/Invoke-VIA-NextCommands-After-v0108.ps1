# =============================================================================
# def VIA · Next Commands after v0108
# =============================================================================

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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_secondstep_closeout\RUN_20260622_180721_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0108\report\VIA_SecondStep_CloseoutPlanner_Report_v0108.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_secondstep_closeout\RUN_20260622_180721_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0108\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_secondstep_closeout\RUN_20260622_180721_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0108\_toolbox_used"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_firststep_panorama\RUN_20260622_175906_VIA_INTEGRATION_FIRSTSTEP_v0106_WORKER\report\VIA_IntegrationFirstStep_Panorama_Report_v0106.html"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_secondstep_closeout\RUN_20260622_180721_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0108\output\VIA_P0_DomainReview.csv" | Select-Object -First 30 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_secondstep_closeout\RUN_20260622_180721_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0108\output\VIA_P1_PathReview.csv" | Select-Object -First 30 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_secondstep_closeout\RUN_20260622_180721_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0108\output\VIA_SubsystemIntegrationPlan.csv" | Format-Table -AutoSize

# Policy:
# No delete. No Stop-Process. No canonical overwrite. No source mutation before P0/P1 review.

