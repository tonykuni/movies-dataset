# =============================================================================
# def VIA · Next Commands after v0111
# =============================================================================

Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\report\VIA_FifthStep_SmokeDiagnosticAcceptGate_Report_v0111.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_CandidateSmokeDiagnostics.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_FixedSmokeResults.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_P0_AcceptGate_Template.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_P1_PathAlias_AcceptGate_Template.csv" | Format-Table -AutoSize

# Run fixed smoke again manually:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\Invoke-VIA-RunAllFixedSmoke-v0111.ps1"

# Next safe phase:
# v0112 = only generate canonical patch candidates after P0/P1 accept gate is reviewed.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
