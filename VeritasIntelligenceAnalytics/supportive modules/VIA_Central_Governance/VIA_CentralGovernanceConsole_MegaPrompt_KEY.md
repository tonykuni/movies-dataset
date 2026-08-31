# 🟥 VIA Central Governance Console:終極旗艦整合版 Mega-Prompt(KEY PROMPT)

> 存檔緣由:使用者指定 "SAVE BELOW FOR THE KEY PROMPT"(2026-08-31)。
> 本檔為逐字保存之核心大腦指令;執行面落地見
> `functional modules/GroupIndex/engine/VIA_GroupIndex_Accel20_Console_v0100.py`(20 加速器全引擎掛載)
> 與 `launch.ps1`(非阻塞啟動器)。

(Ultimate Mega-Prompt: SSOT Registry, AST Dual-Mode Anchoring, 20 Accelerators & 6 Unrestricted Pipelines)

## 🟦 中文版本(正式核心大腦指令)

請啟動「VIA Central Governance Console:全自動沙盒治理與環境修復引擎」,啟用全部 20 個加速器,掛載「中央 SSOT 規範庫、同義字/Regex 治理中心」,對 Base 環境及所有已註冊與動態擴充之子系統(via_core / VRN / VDF / VAP / 新增 via_* 環境)執行標準化部署與穩定化流程。

【核心治理原則與無限制推進指令】

1. 全景式分析與診斷先行:優先啟動全景式分析,調用各類指令與語法識別工具(如 Ruff, PSScriptAnalyzer, Language.Parser 等),對全系統代碼、環境與相依性進行掃描與錯誤分類。
2. AST 雙模錨點定位:針對識別出的問題,動態切換「精準 AST 錨點(精確節點/行號)」或「彈性 AST 錨點(語意特徵簽名)」進行定界鎖定。
3. 六獨立流程無限制推進與錯誤收斂:
   * 後續的「六個獨立流程」若無任何限制,必須在「不損害系統健康、不產生九頭龍連鎖風險(Zero-Hydra Risk)」的絕對前提下,全力同步向前推進到底。
   * 若推進過程中偵測到指令有錯或系統異常,即刻觸發「三輪全景式分析」進行錯誤識別。
   * 識別後,能同步解決的問題(Parallel-Fixable)一口氣全數同時解決;不可同步的問題(Sequence-Dependent)嚴格依賴拓撲順序逐步解決,全程以不影響系統健康、零九頭龍風險為最高依歸。

### 一、VIA EnvManager 環境治理與 SSOT 中央規範

1. SSOT 規範與同義字 Regex 治理:集中管理跨子系統(VRN/VDF/VAP)命名實體、資料契約、同義字庫與 Regex 規則集(`VIA_SSOT_Unified`),消除跨模組語意歧義。
2. uv 極速解析與多鏡像源調度:全面調用 `uv` 解析器與 Local-Free Libs 快篩矩陣。整合清華 (Tsinghua)、阿里 (Aliyun) 及 PyPI 官方鏡像源,即時監測環境健康度。
3. 衝突立拔與動態隔離環境 (via_*):發現衝突風險立即重建環境並拔除風險因子。高風險函式庫、特定工具鏈或多版本需求(如 Plotly 多版本、C++ 擴展、CUDA 引擎),自動分流建立專屬獨立環境(如 `via_lib_plotly_v5`, `via_engine_cuda12`),確保 Base 環境極致精簡最佳化。
4. 非阻塞 PowerShell 啟動器:全流程整合成一支 `launch.ps1`,背景非同步派工(不關閉、不阻塞、不卡斷)。

### 二、三輪全景式分析與錯誤識別(異常觸發時執行)

1. 全景式分析 (Panoramic Analysis):無死角掃描全系統代碼、配置與跨模組呼叫。
2. 全錯誤識別 (Error Identification):運用各類語法診斷工具進行語法、語意、類型與正則匹配標記。
3. 優化點定位 (Optimization Points):資源洩漏、複雜度過高與冗餘路徑定位。
4. AST 結構分析 (AST Structural Analysis):精準與彈性錨點定界。
5. SSOT 對齊檢查 (SSOT Alignment):驗證中央資料字典一致性。
6. 九頭龍風險偵測 (Hydra Risk Detection):鎖定高耦合共用依賴節點。
7. 錯誤分類 (Error Classification):
   * `Parallel-Fixable`(可同時修正)
   * `Sequence-Dependent`(需順序修正)
8. 多子系統同步檢視 (Multi-Subsystem Sync):跨業務模組即時狀態同步。

### 三、六個獨立流程無限制同步推進 (Six Independent Pipelines)

若無異常,以下六大流程全力同步推進到底:

* Pipeline 1: 代碼層 AST 重構與指令語法修復流程
* Pipeline 2: 中央 SSOT 與同義字 Regex 校準流程
* Pipeline 3: 子系統解耦與動態模組插槽註冊流程
* Pipeline 4: uv 依賴解析、衝突立拔與多環境隔離流程
* Pipeline 5: 沙盒多重驗證、性能優化與回歸測試流程
* Pipeline 6: 自適應 HTML UI Matrix 渲染與非阻塞部署監控流程

### 四、三輪精準修正策略(嚴格限制最多三輪)

* 第 1 輪:全面性修正(Comprehensive Fix)— 針對所有 `Parallel-Fixable` 問題,一口氣同時並行解決。嚴格隔離高 Hydra 節點。
* 第 2 輪:順序性修正(Sequential Fix)— 針對 `Sequence-Dependent` 問題,依賴拓撲排序逐步沙盒驗證修正。高風險節點僅給予建議。
* 第 3 輪:收尾性修正(Final Polishing)— 微調、格式化、刪除死碼、性能極致優化,確保系統穩定乾淨。

### 五、沙盒驗證與持續穩定循環

```
test → debug → upgrade → test → debug → optimize → test → debug → consolidate → test → debug → user-test → debug
activate system → test → debug → until perfect
```

### 六、啟用全部 20 個加速器(Accelerators)

1. AST 精準解析加速器
2. 多語言語意模型加速器
3. 九頭龍風險預測加速器
4. 依賴拓撲排序加速器
5. 沙盒隔離執行加速器
6. 自動修正建議生成加速器
7. 三輪全景式分析加速器
8. SSOT 對齊加速器
9. 視覺化矩陣生成加速器
10. 錯誤分類與分群加速器
11. 性能與複雜度分析加速器
12. 多子系統同步檢視加速器
13. 版本差異與回滾加速器
14. 覆蓋率與回歸檢查加速器
15. 修正順序最佳化加速器
16. 動態進度條加速器 (Dynamic Progress Bar)
17. 動態說明加速器 (Dynamic Status Narration)
18. 非阻塞 PowerShell 執行加速器 (Non-Blocking PowerShell)
19. 多引擎整合加速器 (Python + PowerShell + UI)
20. 自動部署與環境初始化加速器 (Auto-Deploy & Init)

### 七、自動跳出 HTML UI Matrix 報告

* 設計規範:採用略小字體(small font),表格高度與寬度具備自動最佳化(Auto-Optimized Layout),儲存格文字過長時強制自動換行(Auto-Wrap)。
* 四大分區:`MODULE` / `ENGINE` / `FUNCTION-LIB` / `OTHERS`。
* 矩陣內容:錯誤矩陣、優化矩陣、Hydra 風險矩陣、依賴拓撲矩陣、修正順序矩陣、數量校驗矩陣、SSOT 對照矩陣。包含紅黃綠燈(RYG)健康度指標、動態進度條與動態說明。

## 🟥 English Version (Production-Ready Mega-Prompt)

Activate the "VIA Central Governance Console: Autonomous Sandbox Governance & Environment Auto-Repair Engine" with all 20 Accelerators fully enabled. Mount the Central SSOT & Synonym/Regex Governance Dictionary. Execute standardized deployment and stabilization across the Base environment and all subsystems (via_core / VRN / VDF / VAP / dynamic slots).

[Core Directives & Unrestricted Advance Protocol]

1. Panoramic Analysis & Diagnostic Scans First: Deploy syntax diagnostic tools (AST, PSScriptAnalyzer, Ruff) to scan, identify, and classify all command and syntax errors across the system.
2. AST Dual-Mode Anchoring: Dynamically switch between Precision AST Anchoring (exact nodes/lines) and Elastic AST Anchoring (fuzzy structural signatures) to lock onto fault locations.
3. Six Pipelines Unrestricted Push & Error Convergence: The Six Independent Parallel Pipelines must push forward to the absolute end without limits, under the strict premise of Zero-Hydra Risk and causing zero harm to system health. If any command error or system anomaly is detected during the advance, immediately trigger the "3-Round Panoramic Error Identification" mechanism. Following identification, resolve all Parallel-Fixable issues simultaneously in one breath. Resolve Sequence-Dependent issues sequentially based on dependency topology. Zero-Hydra Risk remains the absolute invariant.

1. VIA EnvManager & SSOT Specification — SSOT Governance (`VIA_SSOT_Unified`); uv Fast Resolution & Mirror Routing (Tsinghua, Aliyun, PyPI); Instant Conflict Isolation (`via_*` slots, e.g. `via_lib_plotly_v5`, `via_engine_cuda12`); Persistent non-blocking `launch.ps1`.
2. Three-Round Panoramic Analysis (Triggered on Anomaly) — full-system scan, error identification, optimization detection, AST structural analysis, SSOT alignment, Hydra risk detection; classification `Parallel-Fixable` vs `Sequence-Dependent`.
3. Six Independent Parallel Pipelines — (1) Code AST & Syntax Repair, (2) SSOT & Regex Normalization, (3) Subsystem Pluggable Decoupling, (4) uv Fast-Conflict & Environment Isolation, (5) Sandbox Verification, Optimization & Regression, (6) Adaptive UI Matrix & Non-Blocking Deploy.
4. Three-Round Precision Repair Strategy (Max 3 Rounds) — Comprehensive Parallel Fix → Sequential Dependency Fix → Final Polishing & Hardening.
5. Verification & Stabilization Loop —
   `test → debug → upgrade → test → debug → optimize → test → debug → consolidate → test → debug → user-test → debug`
   `activate system → test → debug → until perfect`
6. 20 Accelerators Matrix — AST Precision Parser, Semantic Model, Hydra Risk Predictor, Topology Sorter, Sandbox Isolation, Auto-Fix Generation, Panoramic Analyzer, SSOT Alignment, Matrix Visualization, Error Clustering, Performance Analyzer, Subsystem Sync, Rollback, Coverage Verifier, Fix-Order Optimizer, Dynamic Progress Bar, Dynamic Narration, Non-Blocking PowerShell, Multi-Engine Integration, Auto-Deploy & Init.
7. HTML UI Matrix Output Standard — small typography, auto-optimizing layout, forced auto-wrap; 4 zones `MODULE` / `ENGINE` / `FUNCTION-LIB` / `OTHERS`; Error/Optimization/Hydra/Topology/Fix-Order matrices with RYG health, dynamic progress bars, dynamic narration.
