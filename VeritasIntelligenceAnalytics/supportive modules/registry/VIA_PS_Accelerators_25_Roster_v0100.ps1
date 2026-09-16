# VIA PowerShell 25 Accelerator Roster v0100
# 只定義能力與治理責任；實際執行仍經 VIA 中央命令冊與同意閘。
$VIA_PS_ACCELERATORS_25 = [ordered]@{
    '01' = 'AST 精準解析加速器 (AST Precision Parser Accelerator)'
    '02' = '多語言語意模型加速器 (Multi-Language Semantic Model Accelerator)'
    '03' = '九頭龍風險預測加速器 (Hydra Risk Prediction Accelerator)'
    '04' = '依賴拓撲排序加速器 (Dependency Topology Sorting Accelerator)'
    '05' = '沙盒隔離執行加速器 (Sandbox Isolation Execution Accelerator)'
    '06' = '自動修正建議生成加速器 (Auto-Fix Suggestion Generation Accelerator)'
    '07' = '三輪全景式分析加速器 (Three-Round Panoramic Analysis Accelerator)'
    '08' = 'SSOT 對齊加速器 (SSOT Alignment Accelerator)'
    '09' = '視覺化矩陣生成加速器 (Visual Matrix Generation Accelerator)'
    '10' = '錯誤分類與分群加速器 (Error Classification & Clustering Accelerator)'
    '11' = '性能與複雜度分析加速器 (Performance & Complexity Analysis Accelerator)'
    '12' = '多子系統同步檢視加速器 (Multi-Subsystem Synchronization Accelerator)'
    '13' = '版本差異與回滾加速器 (Version Diff & Rollback Accelerator)'
    '14' = '覆蓋率與回歸檢查加速器 (Coverage & Regression Verification Accelerator)'
    '15' = '修正順序最佳化加速器 (Fix-Order Optimization Accelerator)'
    '16' = '動態進度條加速器 (Dynamic Progress Bar Accelerator)'
    '17' = '動態說明加速器 (Dynamic Status Narration Accelerator)'
    '18' = '非阻塞 PowerShell 執行加速器 (Non-Blocking PowerShell Accelerator)'
    '19' = '多引擎整合加速器 (Multi-Engine Integration Accelerator)'
    '20' = '自動部署與環境初始化加速器 (Auto-Deploy & Init Accelerator)'
    '21' = '資源預算與自動節流加速器 (Resource Budget & Adaptive Throttle Accelerator)'
    '22' = '快取、去重與斷點續跑加速器 (Cache, Dedup & Checkpoint Accelerator)'
    '23' = '網路同意閘與斷路器加速器 (Network Consent Gate & Circuit Breaker Accelerator)'
    '24' = '輸入輸出契約與 Schema 驗證加速器 (I/O Contract & Schema Validation Accelerator)'
    '25' = '證據雜湊與 HTML/JSON 矩陣加速器 (Evidence Hash & Matrix Export Accelerator)'
}

# 舊名稱相容：既有 PS 命令仍可讀到前 20 項；新命令讀取完整 25 項。
$Accelerators = @($VIA_PS_ACCELERATORS_25.GetEnumerator() | ForEach-Object { "{0}. {1}" -f $_.Key, $_.Value })
$VIA_ACCELERATOR_ROSTER_VERSION = 'VIA_PS_Accelerators_25_Roster_v0100'
