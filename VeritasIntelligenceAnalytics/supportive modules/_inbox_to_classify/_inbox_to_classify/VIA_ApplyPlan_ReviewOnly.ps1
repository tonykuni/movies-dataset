# VIA Apply Plan · Review Only
# Generated: 2026-06-17 01:25:55
# This file is intentionally non-destructive.
# It lists the safe order:
# 1. Fix PowerShell parse errors first.
# 2. Rerun Polyglot CTR.
# 3. Only when FAIL=0, run PSScriptAnalyzer -Fix / ruff --fix in sandbox.
# 4. Re-run VDF / VRN user smoke test.
# 5. Only after review, manually copy confirmed files to original.

Write-Host "Review-only apply plan. No changes are performed." -ForegroundColor Yellow
Write-Host "Report: C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\report\VIA_FirstStep_PanoramaSandbox_Report.html"
Write-Host "Command review: C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_CommandReview_StrengthWeakness.csv"
Write-Host "Top libs: C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_Top10_LocalFreeLibs_ByFunctionLanguage.csv"
Write-Host "Top20 process mining libs: C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox\runs\RUN_20260617_012548_VIA_FIRSTSTEP_PANORAMA_SANDBOX\registry\VIA_Top20_EnterpriseForms_To_ProcessMining_Libs.csv"

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
