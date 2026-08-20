Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\report\VIA_v0113K_RowLevelFinalPreview_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\_v0114_sandbox_candidate_input_pack"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\_v0114_sandbox_candidate_input_pack\VIA_v0114_INPUT_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\_v0114_sandbox_candidate_input_pack\VIA_v0114_INPUT_RowPolicyPack.csv" | Select-Object -First 30 | Format-Table -AutoSize

pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\output\Invoke-VIA-v0114-Preflight-After-v0113K.ps1"

# Next:
# v0114 may generate sandbox patch candidate and diff preview only.
# No source mutation. No canonical merge. No DB write.
# Input JSON:
# C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\_v0114_sandbox_candidate_input_pack\VIA_v0114_SandboxPatchCandidate_InputPack.json
