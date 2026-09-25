# VIA QuantGuard™｜台股自建量化與技術分析引擎

**VIA QuantGuard™** 是一個以資料可見性、數值穩定性與可稽核回放為核心的量化品質閘門。這個 MVP 是一個 **local-first、Polars-first** 的計算核心。它不依賴 TA-Lib，也不把 Pandas 放進指標計算層。輸入可以來自 Parquet、資料庫查詢或自訂 fetcher；輸出仍是 Polars DataFrame，方便後續寫回 Parquet、DuckDB、PostgreSQL 或前端 API。

## 核心結論

股票的價格型指標一律使用 `adj_close`；任何只有 raw `close` 的輸入會被拒絕。分析層的成交量與成交值一律使用先扣除當沖的 `non_day_trade_volume` 與 `non_day_trade_turnover`，raw `volume`、raw `total_turnover` 不可直接進入指標，避免當沖被重複計算。官方 TWSE／TPEX fetcher 應在資料邊界先完成扣當沖與合法性檢查。當市場資料只有未調整 `close` 而沒有還原價時，系統不會直接混用；可在資料邊界用 yfinance 的 `Close` 與 `Adj Close` 建立還原因子，然後把計算結果轉成 Polars。yfinance 只負責補足價格，不得替代 TWSE／TPEX 的成交值來源。

Polars 目前提供原生 `rolling_cov`，其 `ddof` 預設為樣本共變異數的自由度調整，並可用 `min_samples` 控制有效觀測數。[1] 因此本專案不再用固定的 `N/(N-1)` 去修補含有缺失值的展開式共變異數。若資料跨市場且確實要把休市日視為持有上一個收盤價，才明確設定 `forward_fill_prices=True`；預設不填價格，避免把估計值誤當成觀測值。Polars 的 EWM API 也明確區分 `adjust`、`min_samples` 和 `ignore_nulls`，本專案在每一個動態訊號中固定記錄這些計算約定。[2]

## 已實作模組

| 模組 | 函式 | 主要輸出 | 預設規則 |
|---|---|---|---|
| 資料輸入 | `load_data` | Polars DataFrame／LazyFrame | Parquet、資料庫 query、自訂 fetcher 三選一 |
| 報酬 | `add_returns` | `ret` | 價格必須是 `adj_close` |
| 滾動風險 | `rolling_beta_corr` | `rolling_beta`、`rolling_corr`、`effective_n` | 樣本共變異數，缺失值不自動填補 |
| 技術指標 | `technical_indicators` | RSI、ATR、MACD、布林通道、SMA、報酬波動與 Z-score | 支援 5／10／20／60／120 日；RSI 14、MACD 12/26/9、ATR 14 為指標基準週期 |
| 風險指標 | `calculate_risk_metrics` | Rolling Sharpe、Sortino、Calmar、VaR、CVaR、最大回撤 | 報酬與無風險率頻率一致；尾部損失保留明確 quantile 政策 |
| 統計指標 | `rolling_statistical_features`、`rolling_r2` | 自相關、量價相關、R²、偏度、超額峰度 | 相同配對視窗、ddof、最小樣本與零變異政策固定 |
| 資料治理 | `prepare_non_day_trade_activity`、`validate_governance_frame` | 扣當沖、ADJ 價格、缺值與原始欄位防呆 | raw volume／raw turnover 不得直接進分析層 |
| 跨市場對標 | `align_confirmed_closes` | close_utc backward as-of 對齊、跨 session lag | 使用 IANA 時區與交易日曆，不用曆日硬 join |
| PIT 回放 | `PointInTimeStore`、`DeterministicReplay` | revision as-of、回放 manifest、future append guard | `confirmed_only` 預設要求 available_at／confirmed_at 都不晚於 cutoff |
| DuckDB 歷史回測 | `scripts/run_backtest_with_duckdb.py` | PIT replay、Factor Composite、next-bar strategy return、Sharpe／Max Drawdown | revision Parquet + 台灣交易日曆；可輸入自訂權重 |
| VIA QuantGuard™ | `tests/test_quantguard_regression.py` | Sharpe、Max Drawdown、技術指標與因子 golden regression | 固定 fixture、欄位級 tolerance、CI merge gate |
| 中央管理 | `ssot_manifest`、`policy_table`、`logic_table`、`factor_table` | 政策庫、邏輯庫、因子庫、參數庫 | 由 `ssot/quant_engine_ssot.json` 保存版本化 SSOT |
| 去大盤 | `build_residual_returns` | 動態 Beta、殘差報酬、低波動遮罩 | EWM 動態 Beta；波動分位數使用歷史滾動門檻 |
| 族群指數 | `build_sector_index` | 族群日報酬 | 可用成交值或其他 point-in-time 權重；沒有權重時等權平均 |
| TOCA | `build_toca` | 留倉資金、去台積電資金佔比、滯後 EWM Z-score | 分母為全市場留倉資金減 2330 留倉資金 |
| 期現貨意圖 | `analyze_foreign_intent` | `pure_hedging`、`active_shorting`、`short_covering`、`neutral` | 3 日現貨累計搭配期貨 OI EWM Z-score |
| 實質籌碼金額 | `calculate_real_capital_flows` | 法人買賣超金額、融資變動金額、成交值佔比 | 張數 × 1,000 × VWAP；未提供 VWAP 時直接失敗 |
| 價格補足 | `fetch_yfinance_adjusted_prices` | `close`、`adj_close` | 只用於補價格，不用於成交值 |
| 特徵工程 | `build_feature_matrix` | 趨勢、動能、波動、量價、突破與品質欄位 | 以當日可得資料建立；可另外加入明確命名的未來報酬標籤 |
| 參數治理 | `encode_parameters`、`render_parameter_text` | 穩定代碼、分類、單位、預設值、中文說明 | 可直接供 dashboard、CSV、API 與 run manifest 使用 |
| Benchmark catalog | `benchmark_catalog_table` | 優點、缺點、修正、替代方案 | 避免把單一大盤指數誤當成所有問題的唯一基準 |

## 安裝與測試

```bash
cd /home/ubuntu/quant_engine_mvp
python3 -m pip install -e '.[test]'
PYTHONPATH=. pytest -q
```

目前測試結果為 **37 passed，1 skipped**。測試涵蓋指標分類、技術與相關性指標、風險指標、跨象限特徵、參數編碼與文字顯示、Benchmark catalog、扣當沖資料邊界、IANA 時區與 DST、跨市場 close_utc 對齊、晚收盤 anti-lookahead、完整 Parquet 範例流程、revision as-of、confirmed-only、initial-release、future append invariance、未來列防護、deterministic replay manifest、DuckDB persistence contract、DuckDB Factor Composite 歷史回測 CLI、多因子 composite、flash crash、volatility spike 與缺失觀測 stress scenarios、TOCA 的無前視 Z-score、法人金額轉換、期現貨分類、殘差報酬、族群等權指數，以及缺少還原價或 raw volume 時的失敗行為。PostgreSQL contract test 在沒有 `TEST_POSTGRES_DSN` 的本地環境會 skip，CI service job 會實際執行。

## 輸入資料契約

### 價格與技術指標

最低欄位為：

```text
date: Date 或 Datetime
ticker: str
adj_close: numeric
```

技術指標另外需要 `non_day_trade_volume`，以及下列其中一組 OHLC 欄位：

```text
adj_high, adj_low
```

或：

```text
high, low, close
```

分析層不接受 raw `volume`。若官方資料同時提供 raw volume 與 day-trade volume，先在 ingestion boundary 執行：

```python
from quant_engine import prepare_non_day_trade_activity

analysis_activity = prepare_non_day_trade_activity(official_raw_activity)
```

第二種情況會以 `adj_close / close` 將 `high` 和 `low` 轉成 adjusted OHLC，再計算 ATR 和布林通道；raw `close` 只可作為建立還原因子的邊界欄位，不會進入技術指標。這是為了避免把 raw high/low 與 adjusted close 混在同一條價格序列中。

### 官方成交值與當沖

TOCA 需要一列一個交易日與股票代號，且只接受扣當沖後的成交值：

```text
date
ticker
non_day_trade_turnover
```

raw `total_turnover` 和 `day_trade_turnover` 應由 TWSE／TPEX 官方資料管線產生，並先轉成唯一的 `non_day_trade_turnover = total_turnover - day_trade_turnover`；TOCA 與法人比例只接受後者。TWSE 的個股歷史頁提供個別證券每日成交值／成交量資料。[3] TWSE 也說明當沖統計在 T 日、T+1 日可能調整，並於 T+2 日完成最終修正。[4] 因此 ingestion layer 必須用 `(date, ticker)` 作為 upsert key，並保存 `retrieved_at`、`data_as_of`、`source`、`revision_status` 和版本資訊。當沖不得在另一模組再次從 raw turnover 扣除或加回。

### 法人與信用交易

`calculate_real_capital_flows` 需要：

```text
date
ticker
adj_close
non_day_trade_turnover
foreign_net_shares
trust_net_shares
margin_change_shares
```

法人大額代理使用 `net_shares × 1,000 × adj_close`，法人比例的分母是 `non_day_trade_turnover`。融資增減代理使用 `change_shares × 1,000 × adj_close`。兩者都是語意明確的 proxy，不可宣稱為精確現金流。

## 三種資料接入方式

### Parquet

```python
from quant_engine import load_data, technical_indicators, EngineConfig

prices = load_data(source="data/ohlcv.parquet")
result = technical_indicators(
    prices,
    config=EngineConfig(windows=(5, 10, 20, 60, 120)),
)
result.write_parquet("data/features/technical.parquet")
```

### 資料庫

```python
from quant_engine import load_data, build_toca

frame = load_data(
    query="""
        SELECT date, ticker, non_day_trade_turnover
        FROM twse_tpex_turnover
        WHERE date BETWEEN :start_date AND :end_date
    """,
    connection=connection,
)
toca = build_toca(frame, ewm_half_life=10, z_min_samples=20)
```

資料庫查詢應在資料庫內先完成分區與日期篩選。計算核心只接收已經符合欄位契約的 Polars frame，不在函式內偷偷改變資料源。

## 台美跨市場對標：春節、休市與收盤時間

台灣與美國不能以相同曆日直接 inner join。台灣現貨交易日由 TWSE／TPEX 日曆決定，美國交易日由 NYSE／NASDAQ 日曆決定；春節可能造成台灣連續多日 `closed`，但美國仍有交易。這些日期不是零報酬，也不是需要補出的虛擬 K 棒。日曆庫應保留 `market`、`date_local`、`status`、`open_local`、`close_local`、`timezone`、`source`、`retrieved_at` 與版本。

時間對齊固定使用 IANA 時區：台灣 `Asia/Taipei`，美國 `America/New_York`。美東夏令時間會讓美股收盤相對 UTC 改變，不能硬編碼台美永遠相差 12 或 13 小時。每一筆 bar 應保留 `market_session_date`、`close_utc`、`available_at`、`confirmed_at`。對台灣訊號而言，只有 `US.close_utc <= TW.close_utc` 的美股收盤才可使用；通常美股同一美國交易日收盤晚於台灣收盤，因此會落到下一個台灣交易日，而不是灌回當日。

```python
from quant_engine import align_confirmed_closes

aligned = align_confirmed_closes(
    confirmed_market_prices,
    left_market="TW",
    right_market="US",
)
```

`align_confirmed_closes()` 使用 backward `close_utc` as-of join，不會跨台灣春節盲目 forward-fill；輸出 `right_session_date` 與 `cross_session_lag` 供稽核。價格線各自以 `adj_close` 建立 Base-100 或報酬序列；若要比較共同路徑，可用確認後的共同 session。若要建立台灣訊號的美股外生特徵，則使用最後一個在台灣 cutoff 前已確認的美股收盤，並記錄其來源 session date。

完整可執行的 Parquet 範例位於 [`examples/tw_us_cross_market_risk.py`](examples/tw_us_cross_market_risk.py)。它會完成資料載入、確認值過濾、台美 close-as-of 對齊、Base-100 價格線、報酬、風險指標與 `build_feature_matrix()` 接回：

```bash
PYTHONPATH=. python3 examples/tw_us_cross_market_risk.py \
  --tw-parquet data/tw_2330_confirmed.parquet \
  --us-parquet data/us_spy_confirmed.parquet \
  --tw-ticker 2330 \
  --us-ticker SPY \
  --output-dir example_output
```

台灣輸入至少要有 `market_code`、`ticker`、`market_session_date`、`close_utc`、`adj_close`、`adj_high`、`adj_low` 與 `non_day_trade_volume`。美國 benchmark 至少要有 `market_code`、`ticker`、`market_session_date`、`close_utc` 與 `adj_close`。第一個台灣 cutoff 若沒有更早的美股已確認收盤，範例會保留資料缺口，不會自行補值。

Point-in-time 欄位、revision schema、as-of SQL 與回放器設計請參考 [`POINT_IN_TIME_REPLAY_DESIGN.md`](POINT_IN_TIME_REPLAY_DESIGN.md)。

### Point-in-Time 回放與反未來視

回放模組已集中在 `quant_engine/replay.py`。它不負責重新發明指標公式，而是先建立 cutoff 可見資料，再把同一個 `build_feature_matrix()` 接到每個歷史 session：

```python
from datetime import date

import polars as pl

from quant_engine import (
    DeterministicReplay,
    PointInTimeStore,
    ReplayConfig,
    build_replay_sessions,
)

revisions = pl.read_parquet("data/normalized_market_revisions.parquet")
calendar = pl.read_parquet("data/tw_calendar_versioned.parquet")

store = PointInTimeStore(revisions)
sessions = build_replay_sessions(
    calendar,
    market_code="TW",
    start=date(2024, 1, 1),
    end=date(2024, 12, 31),
    execution_lag_sessions=1,
)

result = DeterministicReplay(
    store,
    config=ReplayConfig(policy="confirmed_only"),
).run(
    sessions,
    feature_kwargs={"include_risk_metrics": True},
)

result.decisions.write_parquet("output/replay_decisions.parquet")
for manifest in result.manifests:
    print(manifest.replay_id, manifest.output_hash)
```

`PointInTimeStore.as_of()` 的 `confirmed_only` 政策同時限制 `available_at` 與 `confirmed_at`，並在每個 observation key 中選擇 cutoff 前最後可見版本。測試輔助函式 `assert_no_future_rows()` 與 `assert_future_append_invariant()` 可以直接放入資料管線的 user-test 或 CI gate。

## CI/CD 自動化與持久化 backend

專案已加入 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)。每次 push、pull request 或手動 workflow 都會執行完整測試、`tests/test_replay.py` 的 anti-lookahead gate、Python 編譯與 SSOT JSON 驗證。PostgreSQL job 另外啟動 PostgreSQL 16 service，使用同一份 revision fixture 驗證持久化 adapter 與記憶體 store 的 as-of 結果一致。

本地執行方式：

```bash
python -m pip install -e ".[test,persist]"
python -m pytest -q
python -m pytest -q tests/test_replay.py -m anti_lookahead
```

新增指標時，至少要同步加入三種測試：公式邊界測試、缺值／暖機測試，以及 `future append invariance` 測試。CI 會在指標測試與 replay 測試任一失敗時阻擋合併。指標函式只能接收 replay runner 傳入的 cutoff snapshot，不可在函式內自行查詢全量資料。

### VIA QuantGuard™ 數值回歸 gate

固定 benchmark 位於 [`tests/fixtures/performance_regression_fixture.json`](tests/fixtures/performance_regression_fixture.json)，測試位於 [`tests/test_quantguard_regression.py`](tests/test_quantguard_regression.py)。risk 與 stress 的 expected values 應由獨立 reference calculation 產生；因子輸出則保存經 review 的版本化 golden baseline，並另外以手算的多因子權重組合值驗證組合層沒有重算或補值偏差。

回歸容忍度分三層。整數狀態與分類標籤必須完全相等；累積報酬與簡單平均通常使用 `1e-12`；rolling 統計與浮點 EWM 使用 `1e-10`。若需要放寬容忍度，必須同步修改 fixture 版本、變更原因與 review 記錄，不能在測試中直接把 tolerance 調大來掩蓋數值漂移。

CI 的 QuantGuard gate 是：

```bash
python -m pytest -q --strict-markers \
  tests/test_quantguard_regression.py -m regression
```

因此重構下列任一部分都會被數值 gate 檢查：風險年化、Sharpe 分母、equity curve、Max Drawdown window、EMA seed、rolling window、因子條件、缺值暖機與特徵欄位依賴。若只新增欄位而不改既有欄位，應維持原 fixture 的輸出 hash 或欄位級 golden values；若刻意改變定義，必須建立新 fixture ID，而不是覆寫舊基準。

### 多因子組合 fixture

多因子測試應把三件事同時版本化：輸入因子欄位、權重與組合輸出。現在的 fixture 使用：

```json
{
  "weights": {
    "trend_regime": 0.4,
    "momentum_confirmation": 0.3,
    "volume_flow_confirmation": 0.3
  },
  "expected_last": {
    "factor_composite": 0.7,
    "factor_composite_quality_count": 3
  }
}
```

對應的正式 API 是：

```python
from quant_engine import build_factor_composite

combined = build_factor_composite(
    feature_matrix,
    factor_weights={
        "trend_regime": 0.4,
        "momentum_confirmation": 0.3,
        "volume_flow_confirmation": 0.3,
    },
    normalize_weights=True,
    require_complete=True,
)
```

`require_complete=True` 時，只要任何輸入因子為 null，組合值就維持 null；同時輸出 `factor_composite_quality_count`。因此資料缺口不會被誤當成零分，也不會因部分因子缺失而改變權重比例。

### Stress Testing fixture

Stress fixture 位於同一個 JSON 的 `stress` 陣列，目前包含三類情境：

| 情境 | 驗證目的 |
|---|---|
| `flash_crash` | 驗證單日大跌會反映在 Max Drawdown、VaR 與 CVaR |
| `volatility_spike` | 驗證波動率突然上升時 Sharpe、Sortino 與尾部風險的方向 |
| `missing_observations` | 驗證 null 不會被當成零報酬，也不會跳過資料品質檢查 |

每一個 stress case 都應保存自己的 `window`、`min_samples`、完整 returns 序列與 expected last-row metrics。測試除了比較 golden values，也應加入方向性 assertion，例如 flash crash 的 Max Drawdown 必須低於 `-0.20`，CVaR 必須反映大於 20% 的尾部損失。這能避免單純 numeric fixture 被錯誤地調整到看似通過。

新增 stress 情境的流程是：先以獨立 reference calculation 產生 expected values，再加入 JSON fixture，接著以 `pytest.mark.parametrize` 執行，最後由 CI 的 `-m regression` gate 驗證。不得在測試中呼叫同一個 production 函式產生 expected value，否則 production 與測試可能同時包含相同錯誤。

### DuckDB backend

`DuckDBPointInTimeStore` 與記憶體 `PointInTimeStore` 使用相同的 `as_of()` 契約。它適合單機研究、批次回測與可重現 CI：

```python
from quant_engine import DuckDBPointInTimeStore

store = DuckDBPointInTimeStore.connect("data/quant_engine.duckdb")
try:
    store.create_schema()
    store.append(normalized_revision_frame)

    visible = store.as_of(
        cutoff_utc,
        market_code="TW",
        ticker="2330",
        policy="confirmed_only",
    )
finally:
    store.close()
```

`append()` 只追加 revision，不使用更新覆寫歷史資料。`as_of()` 以資料庫 window function 實作：先限制 `available_at`、`confirmed_at` 與 revision 狀態，再對每個 observation key 取最新可見版本。安裝依賴：

```bash
python -m pip install -e ".[persist]"
```

### PostgreSQL backend

多使用者或長期服務化部署可以改用 PostgreSQL，計算層完全不需要改動：

```python
from quant_engine import PostgresPointInTimeStore

store = PostgresPointInTimeStore.connect(
    "postgresql://quant:password@db.example/quant"
)
try:
    store.create_schema()
    store.append(normalized_revision_frame)
    visible = store.as_of(
        cutoff_utc,
        market_code="US",
        ticker="SPY",
        policy="confirmed_only",
    )
finally:
    store.close()
```

PostgreSQL adapter 使用 `psycopg`，並與 DuckDB 共用 `SQL_REVISION_SCHEMA`、revision 欄位契約與 anti-lookahead 查詢語意。CI 使用 `TEST_POSTGRES_DSN` 啟用 PostgreSQL contract test；本地沒有資料庫時該測試會安全 skip，但 DuckDB integration test 仍會執行。

持久化 backend 的完整 schema、索引與 revision 語意見 [`POINT_IN_TIME_REPLAY_DESIGN.md`](POINT_IN_TIME_REPLAY_DESIGN.md)。

## DuckDB 歷史回測與 Factor Composite

正式回測入口是 [`scripts/run_backtest_with_duckdb.py`](scripts/run_backtest_with_duckdb.py)。它會把 revision Parquet append 到 DuckDB，按照每一個台灣交易日的 `close_utc` 建立 confirmed-only cutoff，使用當時可見的美股 benchmark 計算相對特徵，再建立 Factor Composite，最後用下一根 bar 的 position 計算策略報酬。

```bash
python -m pip install -e ".[test,persist]"

python scripts/run_backtest_with_duckdb.py \
  --db-path data/quant_engine.duckdb \
  --revision-parquet data/market_observation_revision.parquet \
  --calendar-parquet data/tw_calendar.parquet \
  --target-ticker 2330 \
  --factor-weights '{"trend_regime":0.4,"momentum_confirmation":0.3,"volume_flow_confirmation":0.3}' \
  --start-date 2022-01-01 \
  --end-date 2025-12-31 \
  --long-threshold 0.5 \
  --short-threshold -0.5 \
  --output-dir output/backtest_2330
```

`--factor-weights` 也可以指定 JSON 檔案。預設權重是趨勢 0.4、動能 0.3、量流 0.3，會以權重絕對值總和正規化。當任一必要因子缺值時，`factor_composite` 會維持 `null`，而非補成零。

回測會產生：

| 輸出 | 內容 |
|---|---|
| `replay_decisions.parquet` | 每個 cutoff 的當日特徵、Factor Composite 與 replay audit 欄位 |
| `backtest_returns.parquet` | `signal_t`、`position_t_plus_1`、策略報酬與策略 equity |
| `backtest_risk_metrics.parquet` | Sharpe、Sortino、VaR、CVaR、Max Drawdown 與 CAGR |
| `replay_manifests.json` | 每個 session 的 input/output hash 與資料品質資訊 |
| `backtest_summary.json` | 權重、threshold、資料筆數與最後一列風險輸出 |

若 DuckDB 已載入同一批 revision，可以使用 `--skip-load` 重跑不同日期區間或 threshold；不能對同一資料庫重複 append 相同 `revision_id`。策略訊號會先使用 session `t` 的 composite，再以 `signal_t.shift(1)` 作為目前 bar 的 position，避免同 bar lookahead。

## 分發與模組相依性

`pyproject.toml` 是 Python package 的正式相依性來源；`requirements.txt` 保留給簡單的本地環境建立。分發時，核心套件不會強制安裝資料庫 driver 或 yfinance：

| 模組 | 安裝方式 | 內容 |
|---|---|---|
| Core | `pip install .` | `quant_engine` 與 Polars |
| Test | `pip install '.[test]'` | Pytest 與所有 unit／regression test |
| Persistence | `pip install '.[persist]'` | DuckDB、pytz、PostgreSQL `psycopg` |
| Price fallback | `pip install '.[yfinance]'` | yfinance 與 pyarrow；只負責補 adjusted price |
| VIA QuantGuard™ | `pip install '.[test,persist]'` | 數值回歸、anti-lookahead 與 backend contract gate |

打包腳本位於 [`scripts/package_project.sh`](scripts/package_project.sh)。它會依序執行完整 strict-marker 測試、VIA QuantGuard™ regression、anti-lookahead suite、Python compile、SSOT JSON 驗證，清理 cache 與 editable metadata，最後執行 `unzip -t` 驗證 ZIP 完整性：

```bash
cd /home/ubuntu/quant_engine_mvp
python -m pip install -e '.[test,persist]'
./scripts/package_project.sh
```

預設輸出：

```text
via_quantguard_quant_engine_20260916.zip
```

ZIP 內含 source、tests、golden fixtures、CI workflow、README、PIT 設計、SSOT 與 examples。它排除 `.pytest_cache`、`__pycache__`、`.pyc`、editable `.egg-info` 與 `example_output`，因此不會把本機暫存狀態帶入分發包。安裝成 wheel 時，`[tool.setuptools] packages = ["quant_engine"]` 確保 `ssot` JSON 目錄不會被誤判成第二個 Python package；完整測試與 fixture 則隨 source ZIP 分發並由 CI 執行。

## 中央管理：政策庫、邏輯庫、因子庫、參數庫與 SSOT

中央治理程式位於 `quant_engine/governance.py`，負責固定不應由單一指標函式自行改寫的規則。`ssot/quant_engine_ssot.json` 是可被 dashboard、資料管線、回測與驗證工作讀取的版本化快照；匯出方式為：

```bash
PYTHONPATH=. python3 scripts/export_ssot.py
```

| 中央庫 | API | 內容 |
|---|---|---|
| 政策庫 | `policy_table()`、`MARKET_POLICIES` | ADJ-only、扣當沖、IANA 時區、確認值、缺值與 T+1 執行 |
| 邏輯庫 | `logic_table()`、`INDICATOR_LOGIC_LIBRARY` | 指標公式、來源、暖機與邊界語意 |
| 因子庫 | `factor_table()`、`FACTOR_LIBRARY` | 趨勢、動能、波動、量價、相對市場、風險與籌碼因子 |
| 參數庫 | `PARAMETER_REGISTRY`、`PARAMETER_POLICIES` | 穩定代碼、分類、單位、預設值與驗證規則 |
| SSOT | `ssot_manifest()`、`ssot/quant_engine_ssot.json` | 版本化中央不變量與所有庫的快照 |

政策層與計算層分離，因此 `risk.py`、`statistics.py`、fetcher 或外部 dashboard 都可以獨立使用，同時透過 `build_feature_matrix()` 接回主系統。若政策庫要求 `non_day_trade_volume` 或 `adj_close`，任何模組都不能自行用 raw `volume` 或 raw `close` 覆蓋。

### 自訂 fetcher

```python
from quant_engine import load_data, rolling_beta_corr


def official_fetcher(start, end):
    # 這裡呼叫自己的 TWSE/TPEX 官方 fetcher。
    # 回傳 Polars DataFrame，不回傳 pandas DataFrame。
    return polars_frame

prices = load_data(
    fetcher=official_fetcher,
    fetcher_kwargs={"start": "2024-01-01", "end": "2025-01-01"},
)
metrics = rolling_beta_corr(prices, window=60, min_samples=50)
```

## 關鍵統計約定

### 1. 滾動 Beta 與相關係數

```text
Beta_t = Cov_sample(asset_ret, benchmark_ret) / Var_sample(benchmark_ret)
Corr_t = Cov_sample(asset_ret, benchmark_ret) /
         (Std_sample(asset_ret) × Std_sample(benchmark_ret))
```

輸出 `effective_n`，用來知道每個視窗實際使用了多少同步報酬。當大盤變異數或任一標準差接近零時，結果為 null，而不是回傳無限大或任意補零。這符合風險指標的「不可定義」處理原則。

### 2. 指標週期

`windows=(5, 10, 20, 60, 120)` 是跨指標的標準輸出週期。這不會覆寫指標本身的 benchmark 週期：RSI 預設 14，ATR 預設 14，MACD 預設 12／26／9，布林通道預設 20。若要調整 RSI 或 MACD 週期，使用 `EngineConfig`，而不是把所有指標強行套成同一個天數。

### 3. TOCA 與 Z-score

```text
retained_cap = non_day_trade_turnover
valid_market_cap = Σ(retained_cap) - retained_cap_2330
toca_ratio = retained_cap / valid_market_cap
```

Z-score 使用前一日以前的歷史：

```text
mean_prev_t = EWM(toca_ratio[0:t-1])
std_prev_t  = EWM_STD(toca_ratio[0:t-1])
z_t = (toca_ratio_t - mean_prev_t) / std_prev_t
```

如果歷史標準差為零，Z-score 為 null。不能加上任意 epsilon 後把「沒有可辨識波動」偽裝成極端訊號。

### 4. 去大盤族群關聯

動態殘差報酬為：

```text
residual_ret_t = asset_ret_t - dynamic_beta_t × benchmark_ret_t
```

低波動遮罩使用 EWM ATR 的歷史滾動分位數，門檻在當日不能看到當日的 ATR。這樣才能把「熱門才算關聯」轉化成可回測的規則，而不是用完整樣本的事後分位數美化結果。

## 技術指標八大類

技術指標不應只按名稱堆疊。較適合量化引擎的分類方式，是依照訊號所描述的市場維度分成八類。前四類是 OHLCV 可以直接生成的核心指標；相對市場、風險、統計結構與籌碼／基本面類則需要基準、外部資料或額外治理，應在資料時間點對齊後再加入。

| 類別 | 主要問題 | 重要指標 | 量化用途與注意事項 |
|---|---|---|---|
| 趨勢 | 價格方向是否持續 | SMA、EMA、MACD、ADX、+DI／-DI | 用於趨勢濾網與方向確認。均線週期高度相關，不應把多個週期無限制地全部送入模型。 |
| 動能 | 上漲或下跌是否過度 | RSI、KD、ROC、Williams %R、典型價偏離 | 用於超買超賣、轉折與動能強弱。動能指標在盤整與趨勢市場的解讀不同。 |
| 波動率 | 價格變動幅度是否擴大 | True Range、ATR、布林通道、報酬波動率 | 用於部位大小、停損距離與波動狀態。ATR 應同時保留價格單位與 `atr_pct` 比率。 |
| 成交量與資金流 | 價格方向是否獲成交量支持 | OBV、MFI、CMF、rolling VWAP、Volume Ratio | 用於量價確認與異常成交偵測。成交值若涉及台股，應優先使用 TWSE／TPEX 官方口徑。 |
| 相對市場 | 個股走勢有多少是市場或族群因素 | Beta、Correlation、Residual Return、族群指數、相對強弱 | 先剝離大盤，再研究族群內的真實共振。同步交易日、缺失值與 benchmark 時點必須明確。 |
| 籌碼／估值／微結構 | 是誰在推動，以及價格是否偏離基本面 | 法人實質金額、融資融券、TOCA、PE/PB bands、期現貨意圖 | 這些不是單純 OHLCV 指標，必須保留發布時間、修訂狀態與 point-in-time 規則，避免資料洩漏。 |
| 統計結構／相關性 | 報酬是否延續、反轉或與量價／基準同步 | 自相關、報酬—成交量相關、報酬—振幅相關、rolling correlation | 相關性不是因果；常數序列、小樣本與多重檢定必須保留 null 並使用 FDR／陰性對照。 |
| 風險調整 | 報酬是否值得承擔其波動與尾部損失 | Beta、Sharpe、Sortino、Calmar、VaR、CVaR、最大回撤 | 風險指標不等同方向訊號；必須固定無風險率、MAR、年化因子、尾部分位與回撤定義。 |

### MVP 已補齊的核心欄位

`technical_indicators` 現在除原有的 RSI、ATR、MACD、SMA、布林通道外，還輸出 EMA、ADX、+DI／-DI、KD、ROC、Williams %R、CCI、MFI、CMF、OBV、ADL、rolling VWAP、Keltner、Donchian、`volume_ratio`、`obv_slope`、`bb_width`、`bb_position` 與 `atr_pct`。所有欄位都以 `ticker` 為時間序列分組，股票價格計算基準仍是 `adj_close`，成交量基準是 `non_day_trade_volume`。

## 參數自動編碼與文字顯示

附件的治理規格要求參數具有穩定代碼、類別、單位、預設值、Benchmark 與替代方案。MVP 以 `PARAMETER_REGISTRY` 實作這個契約。參數本身仍由 `EngineConfig` 驗證；registry 只負責讓相同設定能夠以機器可讀與人類可讀兩種形式輸出。

```python
from quant_engine import EngineConfig, encode_parameters, render_parameter_text

config = EngineConfig(
    windows=(5, 20, 60),
    rsi_period=14,
    atr_period=14,
)

# 給 dashboard、CSV 或 API
parameter_table = encode_parameters(config)

# 給 CLI、報告或操作人員閱讀
print(render_parameter_text(config))
```

參數代碼採穩定命名，不把目前數值塞進代碼中。例如 `TRD_MACD_FAST` 代表 MACD 快線週期，`VOL_ATR` 代表 ATR 週期，`GOV_PRICE_BASIS` 代表價格基準。當使用者覆寫預設值時，輸出狀態會從 `DEFAULT` 變成 `OVERRIDE`。未登錄參數不會靜默消失，而會標記為 `UNREGISTERED`，要求補上語意與治理資訊。

目前主要分類代碼如下：

| 分類代碼 | 中文顯示 | 內容 |
|---|---|---|
| `TREND` | 趨勢 | EMA、MACD、ADX、方向指標 |
| `MOMENTUM` | 動能 | RSI、KD、ROC、Williams %R |
| `VOLATILITY` | 波動率 | ATR、布林通道、波動率 |
| `VOLUME_FLOW` | 成交量／資金流 | MFI、CMF、OBV、VWAP |
| `RELATIVE_MARKET` | 相對市場 | Beta、Correlation、Residual Return |
| `MICROSTRUCTURE` | 籌碼／微結構 | 法人、融資融券、TOCA、估值 |
| `STATISTICAL_STRUCTURE` | 統計結構／相關性 | 自相關、量價相關、R²、偏度、峰度 |
| `RISK` | 風險調整 | Beta、Sharpe、Sortino、Calmar、VaR、CVaR、回撤 |
| `DATA_GOVERNANCE` | 資料治理 | 價格基準、成交值來源、最小樣本、資料滯後 |

## Benchmark pros／cons 與替代方案

Benchmark 不是只有「大盤指數」一種。附件中要求同時保留原始市場、排除巨型股、族群等權、自由流通市值與陰性對照。引擎提供 `benchmark_catalog_table()` 輸出完整比較表：

```python
from quant_engine import benchmark_catalog_table

benchmark_table = benchmark_catalog_table()
print(benchmark_table)
```

| Benchmark 代碼 | 適用場景 | 優點 | 缺點 | 修正與替代方案 |
|---|---|---|---|---|
| `MARKET_INDEX` | 全市場 Beta、組合風險 | 最容易取得，代表整體系統性風險 | 台股權值集中，可能被 2330 或少數大型股支配 | 並列 `EX_GIANT_MARKET`、等權市場與市場廣度 |
| `EX_GIANT_MARKET` | 中小型股、族群共振、TOCA | 降低巨型權值對結果的支配 | 不再是可直接投資的市場組合，會移除巨型股風險 | 與原始大盤並列，並另報巨型股貢獻 |
| `GROUP_EQUAL_WEIGHT` | 族群方向、PCA、共振 | 不讓單一大型股代表整個族群 | 小型低流動性股票被賦予相同權重 | 加入流動性與 coverage gate，並與自由流通市值版本比較 |
| `GROUP_LAGGED_FREE_FLOAT` | 可投資指數與資金容量 | 接近實際可投資曝險 | 權重資料可能延遲或修訂，大型股可能重新主導 | 僅用 t-1 權重，並設定單一權重上限 |
| `LEAVE_ONE_OUT_GROUP` | 個股相對族群強弱 | 排除個股自己，避免機械式高相關 | 小族群基準不穩定 | 設定最少 peer 數，成分變動重設 episode |
| `NEGATIVE_CONTROL` | PCA／CCF／領先關係驗證 | 可檢查假相關與資料探勘偏誤 | 需要 block permutation 與多重檢定，計算成本高 | 使用隨機匹配、產業中性與日期置換對照 |

### Benchmark 缺點的處理原則

第一，不用單一 Benchmark 決定結論。至少保留 `MARKET_INDEX` 與一個去巨型股或族群基準。第二，任何族群內的個股相對強弱，優先使用 Leave-One-Out 基準，避免個股同時出現在被解釋值與基準中。第三，族群指數必須用每日報酬鏈結，不得直接平均名目股價。第四，權重必須是 point-in-time 且至少落後一個交易日；陰性對照則只用於驗證，不得拿來產生交易訊號。

## 新增相關性指標

`technical_indicators()` 已加入下列以個股為單位的 rolling correlation：

| 指標 | 定義 | 解讀 |
|---|---|---|
| `return_autocorr_N` | 報酬與前一期報酬的 N 日 rolling correlation | 檢查短期延續或反轉結構；接近零表示線性自相關弱 |
| `return_volume_corr_N` | 報酬與成交量 log return 的 N 日 rolling correlation | 檢查價格變動是否伴隨量能變化 |
| `return_range_corr_N` | 報酬與日內振幅 `(high-low)/adj_close` 的 N 日 rolling correlation | 檢查方向變動與波動擴張是否同步 |
| `rolling_corr` | 個股報酬與 Benchmark 報酬的 rolling correlation | 衡量市場或族群同步性 |
| `correlation_confirmation_count` | 20 日三項相關性為正的項目數 | 作為量價／報酬結構的簡潔確認特徵 |

這些相關係數遇到有效樣本不足、常數序列或標準差為零時會保留 `null`，不會用零偽造「沒有相關」。相關性也不等於因果關係；正式族群驗證仍需去市場 Beta、PCA／RMT、CCF、block permutation、FDR 與陰性對照。

## 風險指標

風險指標不屬於技術面方向訊號，但必須納入同一個可回測特徵框架，避免模型只看報酬、不看風險：

| 指標 | 定義 | 注意事項 |
|---|---|---|
| `rolling_sharpe` | 年化平均超額報酬／樣本標準差 | `risk_free_rate` 必須與報酬頻率一致；零標準差輸出 null |
| `rolling_sortino` | 年化平均超額報酬／下行偏差 | 需固定 MAR 與負報酬平方的下行定義 |
| `rolling_calmar` | CAGR／最大回撤絕對值 | 必須由 equity curve 計算，不可直接用平均報酬代替 |
| `rolling_var` | 損失序列的 rolling quantile | 固定信賴水準、插值法、持有期與最小樣本 |
| `rolling_cvar` | 超過 VaR 的尾部平均損失 | 不可只呼叫 quantile 便宣稱得到 CVaR |

獨立使用：

```python
from quant_engine import RiskConfig, calculate_risk_metrics

risk = calculate_risk_metrics(
    adjusted_prices,
    config=RiskConfig(
        window=60,
        min_samples=30,
        periods_per_year=252,
        annual_risk_free_rate=0.0,
        var_confidence=0.95,
    ),
)
```

接回系統時 `build_feature_matrix()` 預設加入上述風險欄位，也可以在只想生成技術面時關閉：

```python
technical_only = build_feature_matrix(
    adjusted_prices,
    include_risk_metrics=False,
)
```

統計模組則獨立輸出 `return_autocorr_N`、`return_volume_corr_N`、`return_skew_N`、`return_excess_kurtosis_N` 與 `return_r2_lag1_N`。所有 rolling 視窗都只使用當列及歷史資料；常數序列、零變異、樣本不足與尾部樣本不足都保留 null。

附件中的 28 個指標族與 G01–G13 閘門，部分屬於日線 OHLCV 可直接計算的特徵，部分則需要正式的 TWSE／TPEX／VDF、PIT 族群名單、SBL、券商分點、ETF 快照或估值資料。本 MVP 先落地可驗證的參數 registry、Benchmark catalog 與相關性指標；未接線的模組不能被標示為 production-ready。

## 跨象限特徵工程

`build_feature_matrix` 不把 50 個高度相關的指標直接拼接，而是保留幾個可解釋的跨類特徵。它至少涵蓋趨勢、動能、波動率、量價流與統計結構五個象限，並可選擇加入市場 Beta、相關係數、法人資金比例與 TOCA 熱度。

| 特徵 | 定義 | 類型 |
|---|---|---|
| `price_vs_ema_20`、`price_vs_ema_60` | `adj_close / EMA` | 趨勢位置 |
| `ema_spread_20_60` | `(EMA20 - EMA60) / EMA60` | 趨勢方向 |
| `momentum_score` | `(RSI - 50) / 50` | 動能標準化 |
| `volatility_ratio_20_60` | `return_vol_20 / return_vol_60` | 波動狀態 |
| `volatility_expansion` | `bb_width_20 - bb_width_60` | 波動擴張 |
| `volume_shock_20` | `volume / volume_sma_20 - 1` | 成交量異常 |
| `volume_flow_confirmation` | `CMF20 > 0` 且 `Volume Ratio20 > 1` | 量價確認 |
| `return_autocorr_20` | 報酬與前一期報酬的 20 日 rolling correlation | 報酬延續／反轉結構 |
| `return_volume_corr_20` | 報酬與成交量 log return 的 20 日 rolling correlation | 價量同步程度 |
| `return_range_corr_20` | 報酬與日內振幅的 20 日 rolling correlation | 方向與波動同步程度 |
| `correlation_confirmation_count` | 三項 20 日相關性為正的數量 | 相關性確認摘要 |
| `breakout_20` | 今日收盤價突破前 20 日最高收盤價 | 突破訊號 |
| `breakdown_20` | 今日收盤價跌破前 20 日最低收盤價 | 破位訊號 |
| `return_to_atr` | `日報酬 / atr_pct` | 波動調整後動能 |
| `cross_quadrant_long_confirmation` | 趨勢、動能、量價三者同時確認 | 組合訊號 |
| `feature_quality_count` | 核心特徵目前可用的數量 | 資料品質 |
| `institutional_amount_ratio` | 法人實質買賣超金額／當日總成交值 | 籌碼流量；預設使用前一交易日值 |
| `toca_z_score` | 去台積電實質留倉資金佔比的滯後 EWM Z-score | 籌碼熱度；預設使用前一交易日值 |
| `capital_flow_confirmation` | `institutional_amount_ratio > 0` 且 `toca_z_score > 0` | 法人流入與留倉熱度同向 |
| `capital_flow_heat` | `institutional_amount_ratio × toca_z_score` | 資金流量與異常熱度的交互強度 |

範例：

```python
from quant_engine import build_feature_matrix

features = build_feature_matrix(
    prices,
    windows=(5, 10, 20, 60, 120),
    label_horizons=(5, 20),
)
```

若要加入籌碼特徵，先分別建立兩張以 `(date, ticker)` 為唯一鍵的資料表。第一張可直接使用 `calculate_real_capital_flows()` 的輸出；第二張可直接使用 `build_toca()` 的輸出：

```python
from quant_engine import (
    build_feature_matrix,
    build_toca,
    calculate_real_capital_flows,
)

capital = calculate_real_capital_flows(
    institutional_and_margin_raw,
).select([
    "date", "ticker", "institutional_amount_ratio",
])

toca = build_toca(
    official_turnover,
    ewm_half_life=10,
    z_min_samples=20,
).select([
    "date", "ticker", "toca_z_score",
])

features = build_feature_matrix(
    prices,
    institutional_features=capital,
    toca_features=toca,
    feature_lag_sessions=1,
    label_horizons=(5, 20),
)
```

`feature_lag_sessions=1` 是預設值。它把某股票在交易日 `t` 的籌碼觀測值放到下一個交易日 `t+1` 的特徵列。這適合收盤後才公布或可能在 T+1／T+2 修訂的資料。若資料表已經在 ingestion layer 以「可用時間」完成 point-in-time 對齊，可以將它設為 `0`；不應僅因為觀測日期相同，就假設資料在同日收盤前已可交易。

兩張籌碼表若存在重複 `(date, ticker)`，函式會直接失敗，不會任意聚合。缺少籌碼資料的日期會保留為 null，`capital_feature_quality_count` 和總 `feature_quality_count` 會反映實際可用欄位數。當兩個欄位都存在時，函式會另外產生 `capital_flow_confirmation` 與 `capital_flow_heat`。

`label_horizons` 產生的 `label_forward_return_5` 和 `label_forward_return_20` 是監督式學習的未來標籤，不是當日特徵。它們使用 `shift(-horizon)`，只能放在訓練資料的 label 欄位，不能在訊號生成或模型輸入中使用。最後幾個交易日因為尚未觀察到完整未來區間，標籤自然為 null。

### 建議的最小模型特徵組合

第一版模型不需要所有欄位。可先使用一個跨象限、低共線性的組合：`price_vs_ema_60` 描述長期趨勢，`momentum_score` 描述動能，`volatility_ratio_20_60` 描述波動狀態，`volume_shock_20` 與 `cmf_20` 描述量價資金流，`rolling_beta` 或 `residual_return_60` 描述市場相對風險，再加入 `rolling_sharpe`／`rolling_sortino` 與 `feature_quality_count` 作為風險與資料品質控制。若再加入法人、TOCA 或估值特徵，應用 `(date, ticker)` 對齊，並把公布時間作為可回測的可用時間，而不是只用觀測日期。

## 資料治理與回測注意事項

官方資料與補足資料必須分開記錄。建議每批資料都保存以下欄位：

| 欄位 | 意義 |
|---|---|
| `source` | `TWSE`、`TPEX`、`yfinance` 或資料庫名稱 |
| `retrieved_at` | 實際抓取時間 |
| `data_as_of` | 觀測日期或最後修訂日期 |
| `price_basis` | `raw_close`、`split_adjusted` 或 `adjusted_close` |
| `turnover_basis` | 官方成交值口徑 |
| `revision_status` | `provisional`、`final` 或 `revised` |
| `calendar` | TWSE、TPEX 或跨市場同步規則 |

回測不可把今天下載的修正版資料直接當成過去當天已知資料。尤其是當沖資料，TWSE 明確說明 T+2 才完成最終修正。[4] 若要研究當日可交易訊號，應建立 point-in-time ingestion；若只是研究日後解釋，則可使用最終修正版，但必須標記為 revised。

## 後續建置順序

第一階段應固定資料契約、日期／代號主鍵、公司行動處理和官方資料版本。第二階段再把技術指標、動態 Beta、TOCA 和籌碼模組寫入日分區 Parquet 或 DuckDB。第三階段才接族群分群、回測、參數敏感度和前端圖表。這個順序可以先驗證數學與資料正確性，避免先做畫面後才發現同一個「成交值」在不同模組使用了不同口徑。

## References

[1]: https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.rolling_cov.html "Polars rolling covariance API"
[2]: https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.ewm_mean.html "Polars exponentially weighted moving mean API"
[3]: https://www.twse.com.tw/en/trading/historical/stock-day.html "TWSE Daily Trading Value/Volume of Individual Securities"
[4]: https://www.twse.com.tw/en/trading/day-trading.html "TWSE Objects and Statistics for Day Trading"
[5]: https://ranaroussi.github.io/yfinance/ "yfinance documentation"
