# def VIA 台股族群分類 × 多族群指數 × 量價輪動統一引擎 v0.2.01

## def 01｜用途

本引擎將下列功能收斂成單一計算真源：

```text
def SSOT 族群 Membership
def Point-in-Time 族群有效性
def Leader / Peer / True Laggard / Outlier 動態角色
def Full / Core / Leader-Peer / Laggard / Trading-Capacity 五類族群指數
def 成交值占比、法人、融資、融券與族群輪動狀態
def Residual Return 關係熱力圖
def Controlled Back-test、惡魔反證與 HTML Monitor
```

系統只作研究與監控，不執行下單。

## def 02｜v0.2.01 的方法修正

1. `MembershipValidity` 與 `RoleSeparability` 分離。有效族群不必強迫存在固定 Leader。
2. 角色在判定日後下一交易日才生效，不回頭套用到歷史。
3. True Laggard 不再從所有指數消失，另建 `LAGGARD_EW`。
4. 使用 Full、Core、Leader-Peer、Laggard、Trading-Capacity 五條指數。
5. Adj Close → Log Return → 市場因子殘差 → Leave-One-Out → Correlation / PC1 / CCF。
6. Dynamic Criteria 使用 GMM-BIC、跨族群 Null、Circular-Shift Permutation 與實際分布，不寫死市場相關係數。
7. 新增 Adversarial Null 上界與 expanding-median 時序反證，阻擋單一期偶然假族群。
8. Python 與 HTML 使用同一個 `ui_contract.json`。

## def 03｜核心輸入

### def Membership

```text
Group, Subgroup, Rank, Ticker, YFTicker, Name, Market,
Dimension, CountingFlag, SourceID, EvidenceStatus
```

### def 價量資料

至少需要：

```text
Date, Ticker, Adj_Close, Volume, Turnover
```

可選：

```text
Adj_Open, Adj_High, Adj_Low, DayTradeTurnover, MarketCap,
ForeignNetAmount, InvestmentTrustNetAmount, DealerNetAmount,
MarginBalanceValue, ShortBalanceValue
```

`Adj_Close` 缺失時 fail-closed；原始 `Close` 不會自動替代。Volume 與資金流不得 forward-fill。

## def 04｜Demo 執行

```powershell
python .\VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py `
  --demo `
  --demo-observations 160 `
  --membership .\VIA_ThreeList_CanonicalMembershipInput_v0100.csv `
  --output-root .\RUN_DEMO_V0201
```

## def 05｜真實本地資料執行

```powershell
python .\VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py `
  --membership .\VIA_ThreeList_CanonicalMembershipInput_v0100.csv `
  --prices "C:\Users\tonyk\OneDrive\桌面\tw_stock\StockData.parquet" `
  --output-root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\outputs\VIA_TW_GroupingIndexRotation_v0201"
```

另有 PowerShell 7 啟動器：

```powershell
pwsh -NoExit -ExecutionPolicy Bypass -File ".\Invoke-VIA-TW-GroupingIndexRotation-v0201.ps1" `
  -Mode Real `
  -RunPytest `
  -OpenHtml `
  -KeepPowerShellOpen
```

## def 06｜測試

```powershell
python -m pytest -q .\test_VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py
```

最終封裝測試為 `20 passed`。受控回測包含：

```text
def ROTATION
def MARKET_TIDE
def LOW_VOL_HIDDEN
def SHOCK
```

`MARKET_TIDE` 的假族群 promotion 為 0；其他三個受控世界均保留真陽性且無假陽性。這些是方法與管線證據，不是實際台股報酬或勝率。

## def 07｜主要輸出

```text
csv/membership_ledger.csv
csv/group_validity_snapshots.csv
csv/role_snapshots.csv
csv/latest_classification.csv
csv/dynamic_criteria_ledger.csv
csv/trading_capacity_latest.csv
csv/group_indices_daily.csv
csv/group_rotation_daily.csv
csv/controlled_backtest_summary.csv
csv/devil_validation_ledger.csv
csv/validation_ledger.csv
ui_contract.json
index.html
plots/heatmaps/*.svg
SHA256_MANIFEST.json
```

## def 08｜Gate 解讀

Demo 最終 Gate 為 `HOLD`，唯一原因是 `SYNTHETIC_BOUNDARY`。所有 Hard Gate 為 PASS。真實資料模式需接入本地 `StockData.parquet` 與 point-in-time 因子／參與者資料後重新驗證，才可評估真實市場有效性。
