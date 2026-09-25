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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114M_final_apply_authorization_gate\RUN_20260622_234820_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE\report\VIA_v0114M_FinalApplyAuthorizationGate_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114M_final_apply_authorization_gate\RUN_20260622_234820_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114M_final_apply_authorization_gate\RUN_20260622_234820_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE\_final_apply_authorization_gate" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114M_final_apply_authorization_gate\RUN_20260622_234820_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE\output\VIA_v0114M_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114M_final_apply_authorization_gate\RUN_20260622_234820_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE\output\VIA_v0114M_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114M_final_apply_authorization_gate\RUN_20260622_234820_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE\output\Invoke-VIA-v0114N-Precheck-After-v0114M.ps1" # If blocked only by final authorization, rerun v0114M with: # -def_PARAM_FINAL_APPLY_AUTHORIZATION "YES_I_AUTHORIZE_v0114N_FINAL_APPLY_PACKAGE_REVIEW_ONLY_NO_APPLY_IN_v0114M" # v0114M never applies anything.

