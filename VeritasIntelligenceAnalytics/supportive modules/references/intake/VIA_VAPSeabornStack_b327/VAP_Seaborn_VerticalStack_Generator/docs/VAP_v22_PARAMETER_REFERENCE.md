# VAP v2.2 參數參考

本表對應 `vap_defaults.json`、桌面 UI 與 `vap_seaborn_stack_generator.py`。設定採 JSON；單圖設定放在 `charts[]`，同名單圖值會覆寫全域 `project` 或 chart default。未指定的欄位由 SSOT 預設值補齊。

## 1. Project 全域參數

| 參數 | 預設 | 用途 |
| --- | --- | --- |
| `title` / `subtitle` | Veritas Intelligence Analytics / Seaborn Visual Intelligence Generator | 圖組標題與副標題 |
| `source_label` / `watermark` | 資料來源 / 理 · VAP | 來源標籤與浮水印 |
| `width_inch` | `15.5` | 畫布寬度（英吋） |
| `panel_height_inch` | `2.55` | 單一 panel 基準高度（英吋） |
| `dpi` | `300` | PNG 預設印刷級高解析度；PDF／SVG 仍為向量 |
| `style` | `whitegrid` | Seaborn style：`whitegrid`、`white`、`ticks`、`darkgrid` |
| `context` | `notebook` | Seaborn context：`paper`、`notebook`、`talk`、`poster` |
| `palette` | `deep` | Seaborn／Matplotlib 全域 palette；可用 `deep`、`muted`、`pastel`、`bright`、`dark`、`colorblind`、`Set1`、`Set2`、`Set3`、`tab10`、`tab20`、`rocket`、`mako`、`flare`、`crest`、`viridis`、`coolwarm`、`Spectral`、`RdYlGn` |
| `shared_x` | `true` | 垂直圖組共用 X 軸；heatmap 例外 |
| `figure_face_color` / `axes_face_color` | `#F5F7FA` / `#FFFFFF` | 畫布與 panel 背景 |
| `output_directory` | `output` | 輸出目錄 |
| `output_name` | `vap_seaborn_chart` | 輸出檔名前綴 |
| `output_formats` | `png,pdf,svg,html` | 可選 `png`、`pdf`、`svg`、`html` |
| `html_renderer` | `plotly` | `plotly` 產生互動 HTML；`svg` 產生離線 Matplotlib SVG HTML |
| `max_rows` | `500000` | 單次最多讀取資料列數 |
| `render_max_points` | `5000` | 每張圖送入靜態與 HTML renderer 的最大點數；完整資料仍用於品質稽核 |
| `sample_rows` | `5000` | discovery 與 UI 分析抽樣列數 |
| `date_column` | `Date` | 資料來源的預設日期／時間欄位 |
| `max_x_ticks` | `10` | X 軸最多日期刻度數 |
| `layout_profile` | `compact_desktop` | `compact_desktop`、`standard`、`accessible` |
| `series_colors` | `{}` | 欄位名到顏色的明確映射；優先於 palette |

## 2. Chart 圖表參數

| 參數 | 預設 | 用途 |
| --- | --- | --- |
| `id` / `title` | `chart` / `chart` | 唯一識別與顯示標題 |
| `type` | `line` | `line`、`bar`、`area`、`scatter`、`step`、`candlestick`、`stacked_bar`、`stacked_area`、`stacked_bar_100`、`stacked_area_100`、`heatmap` |
| `x` | `Date` | X 軸欄位 |
| `y` | `[]` | 左軸一或多個序列；candlestick 由 OHLC 欄位取代 |
| `secondary_y` | `[]` | 雙軸右側序列；stacked／heatmap 不使用 |
| `axis_mode` | `auto` | `single`、`dual`、`auto` |
| `secondary_type` | `line` | 右軸 `line`、`bar`、`area` |
| `unit` / `secondary_unit` | 空字串 | 左／右軸標籤 |
| `height_ratio` | `1.0` | panel 相對高度；K 線預設 preset 為 `1.5` |
| `palette` / `colors` | `null` / `{}` | 單圖 palette 或欄位顏色映射；未指定時沿用 project |
| `alpha` | `0.82` | 一般線、散點等透明度 |
| `bar_alpha` | `0.75` | 一般柱、堆疊柱、Volume 柱透明度 |
| `area_alpha` | `0.50` | 線下 area／stacked area 填色透明度 |
| `line_width` | `1.65` | 左軸線寬 |
| `secondary_alpha` / `secondary_line_width` | `0.88` / `1.35` | 右軸線條透明度與線寬 |
| `marker_size` | `22` | scatter 點大小 |
| `bar_gap_ratio` | `0.22` | 柱狀系列之間的視覺間隔；演算法仍確保不交疊 |
| `bar_width_ratio` | `0.92` | 長條寬度／最小有效 X 間隔；接近 1 可縮小間隔但不得等於或超過 1 |
| `stack_mode` | `absolute` | `absolute` 或 `percent100`；100% 圖型固定為百分比 |
| `where` | `post` | step 圖階梯方向：`pre`、`post`、`mid` |
| `positive_negative_colors` | `false` | 單序列正負柱使用不同顏色 |
| `show_legend` | `true` | 是否顯示圖例 |
| `show_zero_line` | `false` | 是否畫零線 |
| `axis_zero_policy` | `auto` | `include`、`exclude`、`auto`；柱圖通常包含零，價格圖通常排除零 |
| `secondary_axis_zero_policy` | `auto` | 右軸是否包含零 |
| `show_latest_label` | `false` | 顯示最後一筆值標籤 |
| `show_outliers` | `false` | 是否在圖上標示稽核出的極端值 |
| `max_x_ticks` / `auto_optimize` | `10` / `true` | panel X 軸密度、版面與大資料渲染最佳化 |
| `render_max_points` | 留空 | 單圖覆寫渲染點數上限；留空沿用 project，範圍 `2..500000` |

## 3. Candlestick + Volume 專用參數

| 參數 | `candlestick_volume` 預設 | 用途 |
| --- | --- | --- |
| `open` | `Adj Open` | 已調整開盤價欄位 |
| `high` | `Adj High` | 已調整最高價欄位 |
| `low` | `Adj Low` | 已調整最低價欄位 |
| `close` | `Adj Close` | 已調整收盤價欄位 |
| `volume` | `Volume` | 成交量欄位；不可由空值策略補值 |
| `price_basis` | `adjusted` | 價格基準宣告；程式不重算 adjusted price |
| `derive_adjusted_prices` | `false` | 保持 false，避免從 raw OHLC 推導 adjusted OHLC |
| `up_color` | `#D62728` | 收盤 >= 開盤的紅色 |
| `down_color` | `#2CA02C` | 收盤 < 開盤的綠色 |
| `candle_width_ratio` | `0.88` | K 線寬度／最小有效 X 間隔；範圍為 0 到 1 之間 |
| `missing` | `ffill` | OHLC 缺值以前一個交易日價格延續；Volume 永不補值 |
| `secondary_type` | `bar` | Volume panel 使用柱圖；不建立價格列右軸 |
| `secondary_y_format` | `magnitude` | 獨立 Volume panel 以 K、M、B 等量級格式顯示 |

若交易資料沒有完整五欄 OHLCV，請不要把一般 close line 偽裝成 K 線；改用 `price_volume_dual` 或 `price` preset。資料若已有時間列但該列 OHLC 缺值，ffill 只填價格欄，不會填 Volume，也不會新增日期列。

## 4. 刻度與格式

| 參數 | 預設 | 用途 |
| --- | --- | --- |
| `tick_policy` | `vap_locked` | `vap_locked` 保持雙軸相同 tick 數；`auto` 交給 Matplotlib／Plotly 自動處理 |
| `tick_count` | `5` | 每軸 tick 數；雙軸兩側各自計算範圍但使用相同數目 |
| nice step | `1.25 / 2 / 2.5 / 5 × 10^n` | 只選易讀步距；必要時延伸 `10` |
| `y_format` | `auto` | `auto`、`number`、`comma`、`magnitude`、`percent` |
| `secondary_y_format` | `auto` | 右軸格式，同上 |

當步距含小數時，formatter 會使用固定小數位並保留尾零：`1.25` 不會變成 `1.3`，`2.50` 不會變成 `2.5`。範圍會包住有效最大／最小值，同時盡量減少上下留白。

## 5. Quality 與空值

| 參數 | 預設 | 可選值與規則 |
| --- | --- | --- |
| `quality_mode` | `audit` | `audit` 或 `off`；預設只檢查、不改原始來源 |
| `invalid_date_policy` | `fail` | `fail` 或 `drop` |
| `duplicate_date_policy` | `fail` | `fail`、`last`、`first`；多股票資料建議保留 `fail` |
| `outlier_policy` | `report` | `report`、`none`、`clip_iqr` |
| `outlier_iqr_multiplier` | `3.0` | IQR clipping 倍數 |
| `missing` | `none` | `none`、`ffill`、`interpolate`、`zero`、`drop`；ffill／interpolate 排除 Volume、TurnoverVolume、成交股數 |

每張圖會輸出 before／after、issues、repairs 與 `data_changed`；所有修正只存在於 render copy，原始 CSV、資料庫或 Parquet 不會被寫回。

資料超過 `render_max_points` 且 `auto_optimize = true` 時，品質稽核仍基於完整處理後資料；只有送入 renderer 的副本會縮減。Line／area／step 依連續桶保留多序列首筆、極小、極大、末筆；candlestick 使用 Open=first、High=max、Low=min、Close=last、Volume=sum 的連續桶聚合；其他圖型使用明示等距抽樣。方法、輸入／輸出點數與警告均寫入 report／audit，不會靜默處理。

## 6. Heatmap 參數

`heatmap` 使用 `heatmap_index`、`heatmap_columns`、`heatmap_value` 與 `heatmap_aggfunc`（預設 `mean`），並可調 `cmap`、`center`、`annot`、`annot_format`。一般圖表不要填 heatmap 欄位；Candlestick 也不需要這些欄位。

## 7. Normalized HTML 控制

`normalized_y` 是逗號分隔的欄位清單。Plotly HTML 會把它們轉為 normalized series、預設隱藏但保留在圖例／勾選控制中；點選圖例即可顯示，取消即可隱藏。Normalized trace 使用獨立、無刻度標籤的 overlay 軸，hover 顯示原值，因此不會被既有百萬級 Volume 右軸壓扁。這個狀態不影響 adjusted OHLC、Volume、原始值或靜態 PNG／PDF／SVG。

## 8. 最小設定範例

```json
{
  "project": {
    "palette": "deep",
    "html_renderer": "plotly",
    "output_formats": ["png", "pdf", "svg", "html"]
  },
  "charts": [
    {
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
      "normalized_y": ["Normalized Return"],
      "bar_alpha": 0.75,
      "area_alpha": 0.5,
      "bar_width_ratio": 0.92,
      "up_color": "#D62728",
      "down_color": "#2CA02C"
    }
  ]
}
```
