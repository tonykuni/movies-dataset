# =============================================================================
# def VIA · Next Commands after v0113D
# =============================================================================

Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\report\VIA_v0113D_ManualSecretResolution_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\output\VIA_v0113D_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_SecretResolution_RESOLVED.csv" | Format-Table -AutoSize

# P0/P1 still manual:
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_P0_RefinedManualGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_P1_RefinedManualGate.csv"

# After manual P0/P1 edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\output\Invoke-VIA-v0114-Precheck-After-v0113D.ps1"

# v0114 may only generate sandbox patch candidate, not overwrite canonical source.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
