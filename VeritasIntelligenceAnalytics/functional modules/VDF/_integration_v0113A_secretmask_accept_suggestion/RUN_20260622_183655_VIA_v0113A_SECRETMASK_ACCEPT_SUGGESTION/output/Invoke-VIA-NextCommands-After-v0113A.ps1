# =============================================================================
# def VIA · Next Commands after v0113A
# =============================================================================

Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\report\VIA_v0113A_SecretMask_AcceptSuggestion_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\_user_edit_sanitized"

# Review safe boards
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\output\VIA_v0113A_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\output\VIA_v0113A_SecretReview.csv" | Format-Table -AutoSize

# Open editable sanitized CSVs
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\_user_edit_sanitized\VIA_v0113A_USER_EDIT_P0_Suggestion_SANITIZED.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113A_secretmask_accept_suggestion\RUN_20260622_183655_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION\_user_edit_sanitized\VIA_v0113A_USER_EDIT_P1_PathAlias_Suggestion.csv"

# Important:
# Keep def_user_accept blank until you manually decide.
# Do not set all rows to YES automatically.
# For secret rows, rotate external key if the value was real.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
