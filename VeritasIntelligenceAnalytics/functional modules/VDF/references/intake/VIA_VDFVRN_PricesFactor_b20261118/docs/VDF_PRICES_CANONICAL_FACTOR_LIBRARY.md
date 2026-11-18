# VDF `prices_canonical` 與因子庫整合候選

本候選把先前 VDF、TA-Lib OneEngine、介面控制台與 SSOT 決策收斂成一條可稽核資料鏈。它不直接升級中央 SSOT，也不宣稱本機資料湖或 TA-Lib Runtime 已上線。

## 整合邊界

| 層 | 唯一責任 | 狀態 |
|---|---|---|
| Central Governance | 配發正式 Module/Dataset ID、升級正式 SSOT | 待 CGC promotion |
| `prices_canonical` | Alias 解析、調整價、扣當沖量值、缺口與證據硬閘 | 候選引擎已實作 |
| 核心因子 Provider | 價格、動能、趨勢、風險、流動性 | 候選引擎已實作 |
| TA-Lib Provider | 依中央 161 指標 Registry 檢查 Runtime 能力 | Gate 已實作；本輪 Runtime 未執行 |
| 相對／橫斷面 Provider | Beta、相關、超額報酬、橫斷面排名 | 僅契約，尚未實作 |
| Parquet／DuckDB | 長期增量資料庫 | Output Contract 已定義；實體 Writer 未在本候選啟用 |
| Console | 唯讀顯示契約與候選／Runtime 狀態 | 已接入 `invokeVdfStatus()` |

## 固定資料流

```text
Provider raw rows
→ Central alias resolve
→ source/as-of/fetch/run/hash evidence gate
→ adjusted OHLC
→ raw − daytrade volume/value
→ prices_canonical
→ no-lookahead gate
→ versioned long factor_values
→ Parquet/DuckDB writer（promotion 後接線）
```

## `prices_canonical` 規則

- 主鍵：`market + ticker + data_date`。
- 起點：`2021-01-01`，終點預設 `LATEST`。
- 調整因子：`adj_close_source / raw_close`；調整後 OHLC 全部使用同一因子。
- 因子活動量：只允許 `volume_raw - daytrade_volume` 與 `trading_value_raw - daytrade_trading_value`。
- 原始量和值只供顯示與稽核；禁止作為因子 fallback。
- 只有 `no_trade_confirmed=true` 可沿用上一筆調整後收盤價；量和值固定為零。
- 未確認缺口、Alias 漂移、衝突重複鍵、來源證據缺失、未來可知資料一律 fail closed。

## 因子庫規則

- 因子起點：`2023-01-02`；由 2021 年價格歷史提供 240 個交易日 warm-up。
- 標準窗口：`5/10/20/60/120/240`；年化交易日 `252`。
- 儲存採長表：`market + ticker + data_date + factor_id + factor_version + parameter_set_id`。
- 每列包含 `FormulaId/Version`、因子執行 `RunId`、上游 `InputRunId`、`CalculationTime` 與完整窗口 `InputHash`。
- 核心 Provider 目前實作 simple/log return、base-100、momentum、SMA ratio、realized volatility、drawdown，以及扣當沖成交量／值 z-score。
- TA-Lib 不得以手寫 pandas 指標代替。Runtime 缺少中央 Registry 任一指標時，整個 TA-Lib Provider 顯示 `BLOCKED`。

## SSOT 狀態

`config/ssot/VDF_PricesFactorRegistry.candidate.json` 的狀態固定為：

```text
CANDIDATE_PENDING_CGC_PROMOTION
```

候選只提交契約、程式與證據；不得手動改寫 `VIA_SystemMaster.via`。Central Governance 核准後才配發正式 ID、登錄 Writer 與啟用 Runtime。

## 驗證

```bash
python -m json.tool config/ssot/VDF_PricesFactorRegistry.candidate.json
python -m py_compile "functional modules/VDF/engine/VDF_PricesCanonical.py" "functional modules/VDF/engine/VDF_FactorLibrary.py"
python -m unittest discover -s "functional modules/VDF/tests" -p "test_*.py" -v
node --experimental-strip-types --test src/lib/via/vdf-prices-factor.test.ts
```

CI 另外執行既有 Central Governance audit、完整 VIA TypeScript tests、VETF seal 與 typecheck。
