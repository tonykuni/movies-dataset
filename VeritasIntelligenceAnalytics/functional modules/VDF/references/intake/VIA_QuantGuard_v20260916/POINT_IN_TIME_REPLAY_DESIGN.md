# Point-in-Time 資料庫與回放器設計規劃

## 結論

下一階段的核心不是再增加一個技術指標，而是讓每個特徵都能回答：「在某一個歷史時點，系統當時究竟看得到什麼？」因此資料庫必須同時保存市場事件的有效時間、資料被來源發布的時間，以及資料修訂的版本。回放器則必須以決策時間逐日重建可見資料，再呼叫同一套 `quant_engine` 計算函式。

推薦採用 **append-only observation + bitemporal metadata + deterministic replay**。第一版可以使用 Parquet 加 DuckDB 建立本地可重現環境；當資料寫入、多人查詢與權限需求增加時，再把相同資料契約搬到 PostgreSQL。無論儲存引擎為何，計算層只接受通過 point-in-time 查詢的 Polars DataFrame。

目前已將第一版回放核心集中實作於 `quant_engine/replay.py`。`PointInTimeStore` 負責 immutable revision 的 as-of 選取；`DeterministicReplay` 負責逐 session 執行特徵計算與輸出 manifest；`assert_no_future_rows()` 與 `assert_future_append_invariant()` 負責資料層反未來視檢查。現有 Pytest 測試套件已驗證 revision、確認狀態、跨市場 cutoff、未來資料追加不變性與 deterministic manifest。

> **重要區分：** `session_date` 說明資料代表哪一個交易日；`available_at` 說明資料最早何時可被管線取得；`confirmed_at` 說明資料何時成為來源確認版本。三者不能用同一個日期欄位代替。

## 一、時間模型

### 1. 有效時間與可用時間

每筆市場資料至少有兩個時間軸。第一個是 **valid time**，代表資料描述的市場事件，例如台股 2026-09-15 的收盤價。第二個是 **transaction／availability time**，代表資料進入可用資訊集合的時間，例如官方當沖資料在 T+1 或 T+2 修訂後才可取得。

`quant_engine` 的預設治理規則是：訊號只能使用已完成且已確認的資料。對日線價格而言，至少要有 `bar_closed_at`；對可能在 T+1 或 T+2 修訂的官方成交值與當沖資料，還必須有 `confirmed_at`。如果研究目的需要模擬「當天收盤後立即取得的初版資料」，可以另外使用 `as_of_policy="bar_closed_or_initial_release"`，但不能把這種結果與 `confirmed_only` 結果混在同一個回測版本中。

### 2. 跨市場 cutoff

每一個回放決策列都必須有明確的 `cutoff_utc`。台灣收盤訊號的 cutoff 通常是台灣交易日收盤確認時間；美國收盤晚於台灣收盤時，美國當日收盤不得進入同一個台灣訊號列。`align_confirmed_closes()` 已用 backward `close_utc` as-of join 實作這條規則。

台灣與美國的本地日期不能直接比較。台灣使用 `Asia/Taipei`，美國使用 `America/New_York`；美國夏令時間會改變其 UTC 開收盤時間。交易日曆也必須區分 `open`、`closed`、`settlement_only` 與 `early_close`。官方交易日曆應以版本化快照保存，而不是在程式中硬編一份固定假日表。[1] [2]

## 二、資料庫分層

### 1. Raw immutable layer

這一層保存來源原文或來源回應的不可變副本。每次抓取都建立新的 `ingestion_id`，不可覆寫舊檔。除了檔案本身，也要保存來源 URL 或 endpoint、查詢參數、抓取時間、內容 hash、HTTP 狀態、解析器版本與來源版本。

Raw 層不是計算層。它可以含有 `close`、`volume`、`total_turnover` 與 `day_trade_turnover`，但這些欄位只能在 ingestion boundary 被轉換，不能直接傳入技術指標。

### 2. Normalized observation layer

這一層將來源資料轉成標準化觀測值。價格分析欄位必須是 `adj_close`，成交量與成交值必須是 `non_day_trade_volume` 與 `non_day_trade_turnover`。如果資料供應商只有 raw OHLC，必須在此層完成還原價轉換，並保存還原因子與來源欄位。

建議的價格觀測欄位如下：

| 欄位 | 意義 |
|---|---|
| `market_code` | `TW`、`US` 或其他市場代碼 |
| `ticker` | 市場內標的代碼 |
| `interval` | `1d`、`1h` 等固定頻率 |
| `market_session_date` | 交易所本地 session 日期 |
| `bar_open_utc` | bar 開始時間，UTC |
| `bar_closed_at` | bar 完成時間，UTC |
| `adj_open`、`adj_high`、`adj_low`、`adj_close` | 調整後價格欄位 |
| `non_day_trade_volume` | 扣除當沖後的分析成交量 |
| `non_day_trade_turnover` | 扣除當沖後的分析成交值 |
| `exchange_timezone` | IANA timezone |
| `calendar_version` | 使用的交易日曆版本 |
| `source_ref` | 對應 raw artifact 的來源識別碼 |

`adj_open`、`adj_high` 與 `adj_low` 若無法可靠建立，不能用 raw 欄位假裝替代；該列應保留資料品質狀態並由需要 OHLC 的函式拒絕或輸出 null。

### 3. Revision layer

修訂資料不可用 SQL `UPDATE` 覆蓋成單一現值。每次修訂都追加一列，並透過 revision metadata 表達其版本關係。最低欄位如下：

| 欄位 | 意義 |
|---|---|
| `observation_key` | `(market_code, ticker, interval, market_session_date, field_group)` 的穩定鍵 |
| `revision_id` | 每一版本的唯一 ID |
| `revision_no` | 同一觀測鍵的遞增版本號 |
| `revision_status` | `provisional`、`confirmed`、`superseded`、`retracted` |
| `available_at` | 這個版本最早可被資料管線取得的 UTC 時間 |
| `confirmed_at` | 來源確認這個版本的 UTC 時間，可為 null |
| `supersedes_revision_id` | 被本版本取代的版本 |
| `ingested_at` | 本地系統實際寫入時間 |
| `source_hash` | 原始內容 hash |
| `parser_version` | 解析器或 fetcher 版本 |

價格、成交值、當沖、法人、融資融券與族群成分都要使用同一種 revision 語意。不能只替成交值保留修訂，卻讓族群成分或 benchmark 權重永遠使用事後最終值。

## 三、推薦的關聯式 schema

以下 DDL 是 PostgreSQL 風格的設計草稿；DuckDB 可以用相同欄位與大部分 SQL 語法建立本地版本。

```sql
CREATE TABLE market_calendar (
    market_code        TEXT NOT NULL,
    session_date       DATE NOT NULL,
    status             TEXT NOT NULL CHECK (status IN
                         ('open', 'closed', 'settlement_only', 'early_close')),
    timezone           TEXT NOT NULL,
    open_utc           TIMESTAMPTZ,
    close_utc          TIMESTAMPTZ,
    source_ref         TEXT NOT NULL,
    calendar_version   TEXT NOT NULL,
    retrieved_at       TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (market_code, session_date, calendar_version)
);

CREATE TABLE market_observation_revision (
    revision_id            BIGSERIAL PRIMARY KEY,
    market_code            TEXT NOT NULL,
    ticker                 TEXT NOT NULL,
    interval               TEXT NOT NULL,
    field_group            TEXT NOT NULL DEFAULT 'market_bar',
    market_session_date   DATE NOT NULL,
    revision_no            INTEGER NOT NULL,
    bar_closed_at          TIMESTAMPTZ,
    available_at           TIMESTAMPTZ NOT NULL,
    confirmed_at           TIMESTAMPTZ,
    revision_status        TEXT NOT NULL CHECK (revision_status IN
                              ('provisional', 'confirmed', 'superseded', 'retracted')),
    supersedes_revision_id BIGINT REFERENCES market_observation_revision(revision_id),
    adj_open               DOUBLE PRECISION,
    adj_high               DOUBLE PRECISION,
    adj_low                DOUBLE PRECISION,
    adj_close              DOUBLE PRECISION,
    non_day_trade_volume   DOUBLE PRECISION,
    non_day_trade_turnover DOUBLE PRECISION,
    exchange_timezone      TEXT NOT NULL,
    calendar_version       TEXT NOT NULL,
    source_ref             TEXT NOT NULL,
    source_hash            TEXT NOT NULL,
    parser_version         TEXT NOT NULL,
    ingested_at            TIMESTAMPTZ NOT NULL,
    UNIQUE (market_code, ticker, interval, field_group, market_session_date, revision_no)
);

CREATE INDEX ix_observation_asof
    ON market_observation_revision
       (market_code, ticker, interval, field_group, market_session_date, available_at DESC);

CREATE INDEX ix_observation_cutoff
    ON market_observation_revision
       (available_at, confirmed_at, market_code, ticker);
```

實務上，`revision_id` 仍然是物理主鍵；`observation_key` 的唯一性要由 `(market_code, ticker, interval, field_group, market_session_date)` 表達。`revision_no` 在同一 observation key 內遞增。若同一列資料拆成價格、成交值、籌碼與成分多個 field group，必須分開維護版本，避免不同來源的修訂互相覆蓋。

## 四、Point-in-Time 查詢規則

### 1. Confirmed-only 查詢

對一個回放 cutoff，資料庫應先排除尚未可用的版本，再在每個 observation key 中選出 cutoff 前最後一個版本。若治理模式是 `confirmed_only`，還必須要求 `confirmed_at <= cutoff_utc`。後續才使用 `revision_status='confirmed'` 的觀測值。

```sql
WITH visible AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY o.market_code, o.ticker, o.interval,
                         o.field_group, o.market_session_date
            ORDER BY o.available_at DESC, o.revision_no DESC,
                     o.revision_id DESC
        ) AS rn
    FROM market_observation_revision o
    WHERE o.market_code = :market_code
      AND o.interval = '1d'
      AND o.available_at <= :cutoff_utc
      AND o.confirmed_at IS NOT NULL
      AND o.confirmed_at <= :cutoff_utc
      AND o.revision_status = 'confirmed'
      AND o.market_session_date <= :cutoff_session_date
)
SELECT *
FROM visible
WHERE rn = 1
  AND revision_status <> 'retracted';
```

`available_at` 與 `confirmed_at` 的排序不可省略。只用 `market_session_date <= cutoff_date` 會把 T+2 才出現的修訂資料錯誤帶回 T 日回測，形成 revision lookahead。

### 4. 實作 backend adapter

`quant_engine/replay.py` 將資料庫差異限制在同一個 `_DatabasePointInTimeStore` adapter。`DuckDBPointInTimeStore` 與 `PostgresPointInTimeStore` 都提供 `create_schema()`、`append()`、`as_of()`、`count_visible_excluded()` 與 `close()`。`DeterministicReplay` 只依賴 `PointInTimeReader` protocol，因此替換儲存引擎不會改變特徵計算。

```python
from quant_engine import (
    DeterministicReplay,
    DuckDBPointInTimeStore,
    PostgresPointInTimeStore,
)

duck = DuckDBPointInTimeStore.connect("data/quant.duckdb")
duck.create_schema()
duck.append(normalized_revision_frame)

# PostgreSQL 使用相同的 reader contract；兩者都可以直接傳給 replay runner。
postgres = PostgresPointInTimeStore.connect(postgres_dsn)
postgres.create_schema()
postgres.append(normalized_revision_frame)

runner = DeterministicReplay(duck)
visible = duck.as_of(cutoff_utc, market_code="TW")
```

`append()` 先套用 `PointInTimeStore._normalize()` 的 revision key、版本號與全域 ID 驗證，再以 parameterized SQL 寫入。`as_of()` 的 SQL window function 與記憶體版本使用相同的分區鍵：`market_code`、`ticker`、`interval`、`field_group`、`market_session_date`。表名只接受簡單 SQL identifier，查詢條件則全部使用 parameter binding。

### 2. 可重現的初版資料查詢

若要研究收盤後立即取得的資料，政策應明確改成 `initial_release`。這時仍保留 `confirmed_at`，但查詢以 `available_at <= cutoff_utc` 為主要條件，並將 `revision_status='provisional'` 標記在輸出品質欄位中。這個模式不能命名為 `confirmed_only`，也不能與最終確認回測結果直接比較而不標記版本。

### 3. 跨市場 as-of 查詢

取得台灣訊號所需的美股 benchmark 時，先取台灣每個 session 的 `close_utc` 作為左側 cutoff，再以美股 `close_utc <= cutoff_utc` 做 backward as-of join。這正是 `align_confirmed_closes()` 的契約。若台灣在春節休市，回放器不建立不存在的台灣列；下一個台灣交易日才重新查詢最新可用的美股資料。

## 五、回放器設計

### 1. 元件責任

回放器應由五個明確元件組成：

1. **CalendarProvider**：提供某個 cutoff 前已知的市場 session、開收盤與假日狀態。
2. **PointInTimeStore**：以 `as_of(cutoff_utc, policy)` 查詢各市場與各資料域的可見版本。
3. **Normalizer**：將 raw artifact 轉成 canonical adjusted-price 與 ex-day-trade schema。
4. **FeatureRunner**：呼叫 `technical_indicators()`、`calculate_risk_metrics()`、`rolling_statistical_features()` 與 `build_feature_matrix()`。
5. **ReplayWriter**：保存每次回放的輸入 snapshot、SSOT 版本、參數 hash、輸出 hash 與資料缺口。

計算函式不應自行查詢資料庫。這樣可以讓同一套 Polars 函式同時被每日管線、批次回測與單元測試使用。

### 2. 回放流程

對每一個台灣交易 session，回放器依序執行以下步驟：

```python
for tw_session in calendar.sessions("TW", start, end, status="open"):
    cutoff = tw_session.close_utc

    tw_prices = store.as_of(
        market="TW",
        cutoff_utc=cutoff,
        policy="confirmed_only",
    )
    us_prices = store.as_of(
        market="US",
        cutoff_utc=cutoff,
        policy="confirmed_only",
    )

    aligned_benchmark = align_confirmed_closes(
        pl.concat([tw_prices, us_prices], how="diagonal_relaxed"),
        left_market="TW",
        right_market="US",
    )

    features = run_features(
        tw_prices,
        benchmark=aligned_benchmark,
        cutoff_utc=cutoff,
    )

    decision = run_signal(features, decision_time=cutoff)
    execution_time = calendar.next_open("TW", after=cutoff)
    writer.write(decision, execution_time=execution_time)
```

`run_signal()` 在這份規劃中代表研究或紙上模擬邏輯，不代表送出任何交易。執行時間只保存為下一個可用台灣 session，不能用同一根收盤 bar 假設成交。

### 3. Replay manifest

每一次回放都要寫一份 manifest，至少包含：

```json
{
  "replay_id": "2026-09-15T06:30:00Z__TW__confirmed_only",
  "cutoff_utc": "2026-09-15T06:30:00Z",
  "as_of_policy": "confirmed_only",
  "ssot_version": "TW-QUANT-ENGINE-SSOT/0.3.0",
  "policy_version": "TW-QUANT-POLICY/0.3.0",
  "engine_git_commit": "...",
  "parameter_hash": "...",
  "calendar_versions": {"TW": "2026.09", "US": "2026.08"},
  "source_revision_max": {"TW": 123456, "US": 789012},
  "input_snapshot_hash": "...",
  "output_hash": "...",
  "data_quality": {
    "missing_sessions": 0,
    "unconfirmed_rows_excluded": 4,
    "future_rows_rejected": 0
  }
}
```

這份 manifest 讓同一個回放結果可以被重建、比較與稽核。若只保存最後的 feature Parquet，而沒有 cutoff、資料版本與參數 hash，日後即使程式碼相同，也無法判斷差異來自資料修訂還是程式修改。

## 六、Replay anti-leak 測試

下一階段至少要建立以下自動化測試：

| 測試 | 預期結果 |
|---|---|
| 在 cutoff 後新增一筆美股收盤 | cutoff 當日的台灣 benchmark 不改變 |
| 將 T+2 的當沖修訂加入資料庫 | T 日的 `confirmed_only` 回放不看得到該修訂 |
| 將未來交易日加入 Parquet | 過去 session 的 feature hash 不改變 |
| 台灣春節期間沒有台灣列 | 不產生虛假零報酬或虛假 OHLC |
| 美國夏令時間切換 | `close_utc` 對齊仍使用正確的美東時間 |
| 右側 benchmark close 晚於台灣 cutoff | 該列被排除，下一個可用台灣 session 才出現 |
| 來源回傳重複 `(date,ticker)` | ingestion job 拒絕或明確建立 revision，不任意聚合 |
| 缺少 adjusted price | 技術指標計算失敗或輸出資料缺口，不退回 raw close |
| 只有 raw volume | 分析層拒絕，不把當沖量重複加入 |
| 同一 replay manifest 重跑 | input snapshot hash 與 output hash 一致 |

其中最重要的是 **future append invariance**：把未來資料追加到資料庫後，所有早於追加時間的回放輸出都必須維持相同 hash。這個測試比單看某個指標數值更能捕捉資料查詢層的前視偏誤。

## 七、建置順序

第一階段的核心已完成 Parquet／記憶體版本。建立 immutable raw artifact、normalized observation、revision metadata 與 calendar snapshot 後，將資料交給 `PointInTimeStore.as_of()`。這一階段不需要先做完整策略回測，但必須能對任一 cutoff 輸出可見資料 snapshot；目前已由 `tests/test_replay.py` 驗證。

第二階段的整合入口已完成於 `DeterministicReplay.run()`。下一步是把 `examples/tw_us_cross_market_risk.py` 的檔案載入邏輯替換為正式 `PointInTimeStore` fetcher，並將 `align_confirmed_closes()`、`calculate_risk_metrics()` 與 `build_feature_matrix()` 的輸入全部改由資料庫 as-of 查詢提供。所有輸出仍寫入 replay manifest。

第三階段加入 revision replay 與 property-based anti-leak tests。對同一交易日故意插入初版資料、T+1 修訂與 T+2 最終版本，確認不同 cutoff 只看到各自當時可得的版本。

第四階段才考慮將儲存層搬至 PostgreSQL 或其他服務化資料庫。搬遷時不得改變 canonical columns、revision semantics、as-of query contract 或 replay manifest；只有物理儲存與索引方式可以更換。

## References

[1]: https://www.twse.com.tw/en/trading/holiday.html "Taiwan Stock Exchange Holiday Schedule"
[2]: https://www.nyse.com/markets/hours-calendars "NYSE Holidays and Trading Hours"
[3]: https://www.tradingview.com/pine-script-docs/concepts/time/ "TradingView Pine Script Time Concepts"
[4]: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/ "TradingView Other Timeframes and Data"
[5]: https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.join_asof.html "Polars DataFrame join_asof"
