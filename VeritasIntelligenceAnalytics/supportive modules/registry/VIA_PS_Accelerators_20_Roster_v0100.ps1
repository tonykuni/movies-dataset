# =====================================================================
# 20 PowerShell Accelerators (SYSTEM MANAGER & Governance Engine)
# 收容存證(批103,2026-08-21):操作員核定原文,收容原樣。
# 實體承接:VIA_PS_Accel_Module.ps1($VIA_ACCEL20+三原語)。
# =====================================================================

# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$Accelerators = @(
    # --- 原生 15 個分析、修正與治理加速器 ---
    "01. AST 精準解析加速器 (AST Precision Parser Accelerator)",
    "02. 多語言語意模型加速器 (Multi-Language Semantic Model Accelerator)",
    "03. 九頭龍風險預測加速器 (Hydra Risk Prediction Accelerator)",
    "04. 依賴拓撲排序加速器 (Dependency Topology Sorting Accelerator)",
    "05. 沙盒隔離執行加速器 (Sandbox Isolation Execution Accelerator)",
    "06. 自動修正建議生成加速器 (Auto-Fix Suggestion Generation Accelerator)",
    "07. 三輪全景式分析加速器 (Three-Round Panoramic Analysis Accelerator)",
    "08. SSOT 對齊加速器 (SSOT Alignment Accelerator)",
    "09. 視覺化矩陣生成加速器 (Visual Matrix Generation Accelerator)",
    "10. 錯誤分類與分群加速器 (Error Classification & Clustering Accelerator)",
    "11. 性能與複雜度分析加速器 (Performance & Complexity Analysis Accelerator)",
    "12. 多子系統同步檢視加速器 (Multi-Subsystem Synchronization Accelerator)",
    "13. 版本差異與回滾加速器 (Version Diff & Rollback Accelerator)",
    "14. 覆蓋率與回歸檢查加速器 (Coverage & Regression Verification Accelerator)",
    "15. 修正順序最佳化加速器 (Fix-Order Optimization Accelerator)",

    # --- 新增 5 個執行、回饋與整合加速器(非阻塞、不卡斷) ---
    "16. 動態進度條加速器 (Dynamic Progress Bar Accelerator)",
    "17. 動態說明加速器 (Dynamic Status Narration Accelerator)",
    "18. 非阻塞 PowerShell 執行加速器 (Non-Blocking PowerShell Accelerator)",
    "19. 多引擎整合加速器 (Multi-Engine Integration Accelerator)",
    "20. 自動部署與環境初始化加速器 (Auto-Deploy & Init Accelerator)"
)
