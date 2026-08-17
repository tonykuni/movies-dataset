# VIA · GroupIndex — 台股族群分類 × 族群指數 × 動態 Criteria 驗證

跨會話導入(2026-08-17)。本模組承載兩代族群治理資產:

## 1. 三清單動態驗證引擎 v0200(套件正典)+ v0201(相容修正)

| 檔案 | 說明 |
|---|---|
| `engine/VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py` | 套件正典引擎(SHA-256 鎖定於 `evidence/PACKAGE_SHA256_MANIFEST_v0200.json`,零改寫) |
| `engine/VIA_ThreeList_Grouping_DynamicValidationPipeline_v0201.py` | v0200 + R09:T03 f-string 內嵌 regex 反斜線導致 Python < 3.12 無法編譯 → 移出 f-string(3.11 相容);`VERSION = 0.2.01` |
| `engine/test_VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py` | 套件正典 pytest(需操作員機上的 `inputs/` 三 HTML 與 `RUN_FINAL_V0200` 證據;沙盒不可重演) |
| `engine/Invoke-VIA-ThreeList-Grouping-DynamicValidation-v0200.ps1` | PowerShell 7 啟動器(檔名還原為套件正典名;sha 與套件 manifest 一致) |
| `docs/README_…_v0200.md` / `docs/…_Handover_v0200.md` | 套件 README 與交接報告 |

v0200 特性:List A(238 檔/39 群 canonical)× List B(治理契約)× List C(動態 cohort,
DISPLAY_ONLY 永不覆蓋 canonical);GMM-BIC 動態 Criteria(零固定 0.85/P85/0.60/0.80 紅線);
市場殘差熱力圖;四情境受控回測;Final Gate `CONTROLLED_ACTIVATION_PASS_REVIEW_WARNINGS_RETAINED`
(Hard Failures 0 / Review Warnings 4 / Pytest 7 passed)。

## 2. SubGroup SSOT v0100(新一代次族群輸入)+ 沙盒驗證管線

| 檔案 | 說明 |
|---|---|
| `input/VIA_TW_SubGroup_SSOT_v0100.xlsx` | 次族群 SSOT:14 L1 / 77 L2 / 378 成員列(301 唯一 ticker);`計入族群指數` 欄位控管一股多族群重複計數(298 COUNT / 80 DISPLAY_ONLY) |
| `input/VIA_TW_SubGroup_Matrix_v0100_1.html` | 台股次族群矩陣 v0100 檢視器(L1/L2/L3 功能格) |
| `engine/via_subgroup_sandbox_validation_v0100.py` | SSOT → v0201 分析核心的沙盒驗證管線(TEST→DEBUG→OPTIMIZE→TEST→CONSOLIDATE→BACK-TEST→USER-TEST→ACTIVATE) |
| `engine/test_via_subgroup_sandbox_validation_v0100.py` | 沙盒 pytest 閘(7 tests) |
| `evidence/RUN_SUBGROUP_SANDBOX_V0100/` | 沙盒證據(test ledger、scenario summary、validity、角色指標、動態 criteria ledger、77 群指數日線、SHA256 manifest) |

沙盒實測(Python 3.11.15,2026-08-17):

```text
Status        = SANDBOX_VALIDATION_PASS_REVIEW_WARNINGS_RETAINED
Hard Failures = 0(S01–S15 全 PASS)
Review Warn   = 2(S16 五個 L2 無 COUNT 成員;S17 單一 COUNT 成員族群 within-corr 不可算)
Pytest        = 7 passed(-W error)
Market Tide   = raw within-corr 0.728 → residual 0.005(殘差化控制重演成功)
Criteria      = 跨情境/種子 digest 全異;MarketThresholdHardcoded = 0
```

## 邊界

- 價格/成交值仍為 deterministic controlled DGP:只驗證方法與管線,不是實盤績效。
- 真值接線(`Date × YFTicker Adj_Close / Turnover_Value`、`^TWII` 因子)依 v0200 交接報告
  §09,分類/指數/熱力圖/Gate 不必重寫。
- 熱力圖與指數 PNG 寫入 `output/`(不入版控,重跑即得);證據 CSV/JSON 入 `evidence/`。
- v0200 套件檔案為 append-only 正典;任何修正以新版號旁建(如 v0201),不改寫原件。
