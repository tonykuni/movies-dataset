# Veritas OmniFormat Intelligence Engine v1.4 最終測試報告

最終狀態：**ACTIVE / PASS**  
測試日期：2026-08-30  
架構：CPU-only；不需要 GPU

## 結果摘要

| 驗證 | 結果 |
|---|---|
| Python unit／regression | 67 / 67 PASS |
| 引擎 self-test | 46 / 46 PASS |
| ENGINE／SYSTEM user-test | 29 / 29 PASS |
| Activation | ACTIVE；Hydra 與 Runtime Copy safety 均為必需 Gate |
| 一般 failure framework | 8 stages × Top 20 = 160 保留 |
| NoHydra framework | 20 risks、60 solutions、20 SOP、20 never-again controls |
| 三輪唯讀掃描 | 3 / 3；每輪均有 post-scan，來源 hash 不變 |
| 人工 Hydra fixture | HYDRA-F05；HOLD；exit code 3；來源 hash 不變 |
| Runtime Copy 未核准 | HOLD；未建立副本；exit code 4 |
| Runtime Copy 已核准 | PASS；版本化 run-local copy；canonical 不變 |
| Rollback dry-run | PASS；未執行真實 rollback；canonical 不變 |
| Hash state machine | 四態全部符合固定決策 |
| SYSTEM 根檔 | 固定 5 / 5 |
| SYSTEM sidecars | 10 / 10，含 Hydra HTML matrix 與 Runtime Copy safety |
| JavaScript／PowerShell 工具 | 20 + 20 與 30-row matrix 保留 |

## 安全與治理驗證

- Canonical／SSOT 維持 `READ_ONLY`；沒有 canonical promotion endpoint。
- 三輪 audit 都實際重掃並建立 `post_scan_complete=true` 證據，不 import 目標、不連網、不啟程序、不寫 DB。
- 高風險或未知狀態一律 `HOLD`／fail-closed；不會因第三輪結束而放寬 Gate。
- Runtime Copy 只有精確 token `YES_FOR_ANY_REAL_WRITE` 可建立，且只進新建版本化 run-local 目錄。
- Hash state 固定為 `MISSING→APPLY`、`PROPOSED→SKIP`、`ORIGINAL→BACKUP_APPLY`、`OTHER→FAIL_CLOSED`。
- Rollback check 驗證 manifest、來源與副本 BLAKE2s，但 `real_rollback_performed=false`。

## SYSTEM E2E

內建樣本以 SYSTEM role 執行後，根目錄恰有 MD、self-contained HTML、Component Specs JSON、DOCX、CSV 五檔；`_system/` 恰有十個治理 sidecars。Hydra HTML 管理矩陣為無 CDN 的單檔，包含且只包含 20 個風險列。DOCX 與所有 JSON 均通過結構檢查。

## 外部工具揭露

引擎會偵測免費 JavaScript／PowerShell 工具並提供 deterministic fallback。未安裝的外部工具只標記 `NOT_INSTALLED`，不視為實際通過；VOFIE 不會自動下載、安裝或修改 PATH。

## 結論

v1.4 是 add-only 升級。Full convert、simple-five、NLP／VSIS、JavaScript／PowerShell Top-20、160 failures 與 NoHydra Top-20 均保留；新增的 Runtime Copy、rollback dry-run、hash state machine、三輪 post-scan 與 HTML 管理矩陣已通過整合測試，來源與 canonical 均未修改。
