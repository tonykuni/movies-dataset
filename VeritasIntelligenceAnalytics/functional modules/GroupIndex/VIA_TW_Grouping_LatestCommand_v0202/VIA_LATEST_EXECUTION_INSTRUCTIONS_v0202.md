# def VIA 台股族群分類與族群指數最新執行指令 v0.2.02

## def 01｜用途

本套件以 `VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py` 為唯一計算核心，執行：

```text
def 三清單正規化後的 39 群 / 238 檔 membership
def Point-in-Time 族群資格驗證
def CORE_MEMBER / CONDITIONAL_MEMBER / SPURIOUS_REVIEW
def Leader / Peer / True Laggard / Mixed / Outlier
def Full / Core / Leader-Peer / Laggard / Capacity 指數
def Residual Heatmap、PC1、Cross-Group Null、Permutation
def 量價輪動與 Dynamic Criteria Ledger
def Devil Validation、Walk-Forward、HTML 與 SHA256
```

## def 02｜日期契約

```text
def Warm-up Start       = 2025-01-02
def Evaluation Baseline = 2026-01-02
def End Date             = 本地資料最新可用日期
def Index Base           = Evaluation Baseline 當日或其後第一個有效共同交易日 = 100
```

暖機資料不列入 2026 年正式績效，只供 60／120／240 日證據窗口與動態狀態估計使用。

## def 03｜動態 Criteria 契約

市場判定不得硬編碼固定相關係數、固定百分位或固定 Z-Score。正式判定由：

```text
def Robust Scaling
def GMM-BIC / Empirical Distribution Separation
def Cross-Group Matched Null
def Adversarial Null
def Circular-Shift Permutation
def Expanding Temporal Persistence
def Walk-Forward Expected Loss
```

自動產生當期邊界。治理不變項（No Look-Ahead、Duplicate Count、COUNT 唯一性）仍維持硬 Gate。

## def 04｜資料要求

最低價格資料：

```text
def Date
def Ticker
def Adj_Close
def Volume
def Turnover
```

建議市場因子資料：

```text
def Date
def TAIEX_Return
def TPEX_Return
def TSMC_Return
def SOX_PreviousSession_Return
```

`Adj_Close` 不得由 Raw Close 靜默替代；Volume、Turnover、DayTrade 與資金流不得 forward-fill。

## def 05｜一鍵執行

請先解壓本 ZIP，再從套件根目錄執行：

```powershell
pwsh -NoExit -ExecutionPolicy Bypass -File ".\Invoke-VIA-TW-Grouping-Latest-v0202.ps1" `
  -Mode Real `
  -PricePath "$env:USERPROFILE\OneDrive\桌面\tw_stock\StockData.parquet" `
  -FactorPath "C:\VIA_LOCAL_CACHE\tw_stock\TW_Market_Factors.parquet" `
  -WarmupStartDate "2025-01-02" `
  -EvaluationStartDate "2026-01-02" `
  -EndDate "" `
  -RunPytest $true `
  -OpenHtml $true `
  -NonBlocking $true `
  -KeepPowerShellOpen $true
```

`EndDate` 留空代表使用本地資料最新日期。

## def 06｜證據邊界

```text
def Controlled DGP PASS ≠ 真實市場分類有效
def FactorPath 缺失時可做初步殘差檢查，但不可直接 Promote 剔除
def 第三類成員只進 REVIEW / QUARANTINE，不物理刪除 SSOT
def 新 membership 最早下一交易日生效，不回寫歷史指數
```

## def 07｜主要輸出

```text
def index.html
def ui_contract.json
def csv/latest_classification.csv
def csv/group_validity_snapshots.csv
def csv/role_snapshots.csv
def csv/group_indices_daily.csv
def csv/group_rotation_daily.csv
def csv/dynamic_criteria_ledger.csv
def csv/devil_validation_ledger.csv
def csv/walk_forward_validation.csv
def manifest.json
def SHA256_MANIFEST.json
```
