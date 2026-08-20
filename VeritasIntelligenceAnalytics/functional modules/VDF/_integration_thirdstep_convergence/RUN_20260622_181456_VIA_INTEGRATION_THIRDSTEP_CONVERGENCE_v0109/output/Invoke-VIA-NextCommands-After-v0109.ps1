# =============================================================================
# def VIA · Next Commands after v0109
# =============================================================================

Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\report\VIA_ThirdStep_ConvergenceSandbox_Report_v0109.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\_sandbox_patch_candidates"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\_toolbox_review"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\output\VIA_P0_DomainDecisionTemplate.csv" | Select-Object -First 40 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\output\VIA_P1_PathAliasMap.csv" | Select-Object -First 40 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\output\VIA_P2_EngineBridgeQueue.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\output\VIA_IntegrationActionBacklog.csv" | Select-Object -First 80 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_thirdstep_convergence\RUN_20260622_181456_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109\output\VIA_Top10LocalFreeLibs_ByFunctionLanguage.csv" | Format-Table -AutoSize

# Next safe phase:
# v0110 should generate sandbox-only adapter candidates.
# It must not overwrite canonical files until P0/P1 review is accepted.
