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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
