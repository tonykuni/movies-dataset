# =============================================================================
# def VIA · Next Commands after v0113C
# =============================================================================

Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\report\VIA_v0113C_SecretResolutionGate_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution"

# Review secret resolution board
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_SecretResolution.csv" | Format-Table -AutoSize

# Review readiness
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\output\VIA_v0113C_ReadinessGate.csv" | Format-Table -AutoSize

# Open manual edit boards
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_SecretResolution.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_P0_RefinedManualGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_P1_RefinedManualGate.csv"

# After manual review/edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\output\Invoke-VIA-v0114-Precheck-After-v0113C.ps1"

# Only after precheck returns OK:
# v0114 may generate sandbox patch candidate.
# Still no canonical overwrite.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
