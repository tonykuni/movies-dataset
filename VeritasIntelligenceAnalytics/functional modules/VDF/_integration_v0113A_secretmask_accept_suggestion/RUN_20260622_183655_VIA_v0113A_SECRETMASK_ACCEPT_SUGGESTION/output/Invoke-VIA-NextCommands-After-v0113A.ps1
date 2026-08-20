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
