# VAP Seaborn v2.2 規格

## 1. SSOT 與 renderer

- Defaults schema：`VIA-VAP-SEABORN-DEFAULTS/2.2`
- Data source schema：`VIA-VAP-DATA-SOURCE/2.2`
- Data quality schema：`VIA-VAP-DATA-QUALITY/2.2`
- Diagnostics schema：`VIA-VAP-DIAGNOSTICS/2.2`
- Chart config schema：`schema_version = 2.2`
- 原則：設定只增不減；異動需保留版本與 changelog。

v2.2 明確拆分兩種輸出責任：

| 輸出 | renderer | 契約 |
| --- | --- | --- |
| PNG／PDF／SVG | Seaborn／Matplotlib | 高畫質靜態輸出，Seaborn palette、版面、刻度與顏色規則共用 |
| HTML | Plotly（預設） | 自包含、離線、互動式垂直堆疊；hover、zoom、series toggle 與 normalized checkbox |

HTML 若設定 `html_renderer = svg`，則降級為離線內嵌 Matplotlib SVG 預覽；靜態檔案不依賴 Plotly Kaleido。

## 2. ChartSpec 基本契約

```json
{
  "schema_version": "2.2",
  "id": "tw_ohlcv",
  "type": "candlestick",
  "axis_mode": "dual",
  "x": "Date",
  "open": "Adj Open",
  "high": "Adj High",
  "low": "Adj Low",
  "close": "Adj Close",
  "volume": "Volume",
  "missing": "ffill",
  "bar_alpha": 0.75,
  "area_alpha": 0.5,
  "up_color": "#D62728",
  "down_color": "#2CA02C"
}
```

一般圖型使用 `y` 與可選的 `secondary_y`；`candlestick` 必須使用完整 adjusted OHLCV 五欄。完整參數與預設值請看 [`VAP_v22_PARAMETER_REFERENCE.md`](VAP_v22_PARAMETER_REFERENCE.md)。

## 3. 軸模式

### Single

- `axis_mode = single`。
- 所有 `y` 由左軸繪製。
- 即使設定 `secondary_y` 也不繪製，驗證報告會提出警告。

### Dual

- `axis_mode = dual`。
- `y` 屬左軸，`secondary_y` 屬右軸。
- 左右軸擁有獨立單位、格式、圖型、線寬、透明度及零軸策略。
- `vap_locked` 讓兩邊保持相同 tick 數；左右軸各自計算適合自己的數值範圍，不假設不同單位具有相同比率。

### Auto

- 有 `secondary_y` 時建立右軸，否則維持單軸。
- `candlestick` 由 OHLC 放左軸，Volume 放右軸；不要求在 `secondary_y` 重複 Volume。

## 4. Candlestick + Volume

- `open`、`high`、`low`、`close` 均宣告為已調整價格（adjusted price）。系統不從 raw OHLC 推導或重算 adjusted price。
- `close >= open` 為紅色漲，`close < open` 為綠色跌；預設色為 `#D62728`／`#2CA02C`。
- Volume 柱逐列沿用相同紅／綠顏色，`bar_alpha` 預設 `0.75`。
- `missing = ffill` 只可把已存在時間列的價格缺值向前延續；Volume、TurnoverVolume、成交股數永不 ffill／interpolate／zero。
- 系統不補週末或休市日；時間缺口只進入 quality diagnostics。
- `candle_width_ratio` 以相鄰有效 X 值的最小正間隔為上限，確保 K 線與柱不交疊；預設 `0.88`。
- 價格軸預設 `axis_zero_policy = exclude`，Volume 軸預設包含零，以放大價格波動同時包住 OHLC 最大／最小值。

## 5. 堆疊與垂直圖組

- `absolute`：保留原始量值；正值與負值分開累積。
- `percent100`：每列正規化為 1；只接受非負、可加總的組成資料。
- `stacked_bar`、`stacked_area` 支援一般堆疊；`stacked_bar_100`、`stacked_area_100` 固定為 0%～100%。
- `area_alpha` 預設 `0.50`；正負 stacked area 分別從零線向上／向下累積。
- 垂直圖組與圖內堆疊是不同概念：前者把 panel 依 `charts[]` 順序向下追加，後者在同一座標內累積 series。
- 每次 UI 新增圖表追加到 `charts[]` 尾端；可透過 move 操作重排。

## 6. 刻度與範圍

- `vap_locked` 預設為 5 ticks、4 intervals；雙軸只鎖定 tick 數，不鎖定相同數值 `dtick`。
- 合法步距為 `1.25 / 2 / 2.5 / 5 × 10^n`，必要時延伸 `10 × 10^n`。
- Y 範圍必須包住有效資料最大／最小值；在此約束下縮小上下留白以最大化波動可讀性。
- `axis_zero_policy = include` 時必須包含零；`exclude` 僅在非柱狀價格／比率情境使用；`auto` 依圖型選擇。
- formatter 依步距推導固定小數位，保留尾零，例如 `1.25`、`2.50`；不把 2.50 顯示成 2.5。
- `y_format`／`secondary_y_format` 支援 `auto`、`number`、`comma`、`magnitude`、`percent`。

## 7. Normalized series

- `normalized_y` 是額外的比較序列清單，不覆寫原始 `y`、OHLC 或 Volume。
- Plotly HTML 中 normalized series 預設 `visible = legendonly`，保留在圖例／勾選控制中；勾選後可查看，取消即可隱藏。
- Normalized 使用獨立的無標籤 overlay 軸並以 hover 顯示原值，不與既有右軸 Volume 共用數值範圍。
- 靜態 PNG／PDF／SVG 不提供互動 checkbox；主圖資料與一般 series 仍照靜態契約輸出。

## 8. Data source 與自動建議

```json
{
  "schema": "VIA-VAP-DATA-SOURCE/2.2",
  "kind": "duckdb",
  "path": "data/tw_market.duckdb",
  "table": "tw_prices_adj",
  "sheet": "",
  "query": "",
  "encoding": "utf-8-sig"
}
```

- SQLite／DuckDB 使用唯讀連線；遠端 SQLAlchemy adapter 僅提交經檢查的單一 `SELECT`／`WITH` 查詢。
- 自訂 SQL 只允許 `SELECT` 或 `WITH` 開頭的單一 statement。
- 圖表只要求必要欄位，Parquet 與資料庫會做欄位投影；`max_rows` 防止錯誤設定一次載入過大資料。
- discovery 會保存來源 declared type、nullable、primary key、index（來源支援時），並從欄名／dtype 推斷 `datetime`、`price`、`volume` 等語意。
- 若發現 Date、完整 adjusted Open／High／Low／Close 與 Volume，建議優先產生 `candlestick_volume`；否則依序退回 price + volume、price、flow、percentage 或 category + numeric 建議。
- 自動建議只填入初始 ChartSpec，不略過使用者確認；可在 UI 或 JSON 修改後再新增到圖組。

## 9. Auto-Fixer 與品質契約

- 原始資料來源永遠唯讀，所有處理只作用於 render copy。
- `quality_mode = audit` 為預設；`off` 只在使用者明確指定時停用。
- `invalid_date_policy = fail|drop`。
- `duplicate_date_policy = fail|last|first`，預設 `fail`，避免 `Ticker + Date` 資料被 date-only 靜默去重。
- `outlier_policy = report|none|clip_iqr`，預設 `report`；金融尖峰不會被默默平滑。
- `outlier_iqr_multiplier` 預設 `3.0`。
- `missing = none|ffill|interpolate|zero|drop`；ffill／interpolate 會排除 Volume 類欄位。
- 不自動建立週末或休市日；日期缺口只依觀測頻率稽核。
- 每張圖在 report 內保留 before、after、issues、repairs、`data_changed` 與 `render_optimization`。
- `render_max_points` 預設 `5000`；縮減只作用於 renderer copy，方法與列數必須寫入 audit，不可靜默抽樣。

## 10. 相容性與安全

- v1 的 `project.data` 與 chart-level `data` 仍可使用；v2.2 優先讀取 `data_source`，找不到才降級至舊欄位。
- 原始來源不回寫；輸出檔案以暫存檔與原子重新命名避免半成品。
- SQLAlchemy URL 的密碼、token、secret、明文 query 與 sample values 不寫入 manifest、report 或 UI 狀態；遠端來源仍必須使用資料庫端唯讀帳號。
- Seaborn 與 Plotly 共用同一份 ChartSpec、DataSourceSpec、Defaults、Diagnostics 與刻度規則；Plotly hover／zoom 不會污染靜態 renderer。
