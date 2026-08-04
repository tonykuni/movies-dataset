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
