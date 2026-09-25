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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114J_explicit_final_user_approval_gate\RUN_20260622_232510_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE\report\VIA_v0114J_ExplicitFinalUserApprovalGate_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114J_explicit_final_user_approval_gate\RUN_20260622_232510_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114J_explicit_final_user_approval_gate\RUN_20260622_232510_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE\_explicit_final_user_approval_gate" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114J_explicit_final_user_approval_gate\RUN_20260622_232510_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE\output\VIA_v0114J_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114J_explicit_final_user_approval_gate\RUN_20260622_232510_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE\output\VIA_v0114J_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114J_explicit_final_user_approval_gate\RUN_20260622_232510_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE\output\Invoke-VIA-v0114K-Precheck-After-v0114J.ps1" # If blocked only by approval, rerun v0114J with: # -def_PARAM_FINAL_USER_APPLY_ACCEPT "YES_I_ACCEPT_FINAL_APPLY_REVIEW_NEXT_ONLY_NO_APPLY_IN_v0114J" # v0114J never applies anything.

