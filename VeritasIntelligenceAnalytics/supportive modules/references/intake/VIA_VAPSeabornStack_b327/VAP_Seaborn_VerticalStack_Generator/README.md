# VAP Seaborn Visual Intelligence Generator v2.3.1

VAP Seaborn v2.3.1 是一套離線可執行的單圖、圖庫與垂直圖組生成器。它將「資料來源 → 欄位分析 → 單圖設計／預覽 → 存入圖庫 → 加入堆疊 → 拖曳排序 → 靜態與互動輸出」整合在同一套介面，適合研究圖、交易圖與資料庫驅動的圖組。

v2.3.1 採用雙 renderer，並針對實際 UAT 修正資料來源切換、圖庫併發、單軸殘留右軸、刻度尾零、Windows 啟動與輸出開啟等問題：

- **Plotly**：HTML 使用互動式垂直堆疊圖，共享 X 軸，可 hover、縮放、開關 series；`normalized_y` 以隱藏但可勾選的 series 放在圖中。
- **Seaborn／Matplotlib**：PNG、PDF、SVG 使用高畫質靜態輸出；Seaborn palette 與顏色設定會沿用到線、柱、堆疊與面積圖。

## 最快啟動方式

第一次使用，雙擊：

```text
Setup-and-Run-VAP-Seaborn-Stack.cmd
```

它會在套件內建立獨立 `.venv`、安裝固定範圍的依賴套件並開啟桌面介面，不修改其他 Python 環境。已完成安裝後可直接雙擊：

```text
VAP-Seaborn-Stack-UI.cmd
```

Windows 11 建議使用 Python 3.12；命令列也可以明確指定套件內的執行檔：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 桌面介面、圖庫與向下加圖

主要編輯區由三個可聚焦的區域組成：

1. **左側資料來源**：可收合；掃描檔案、Sheet 或資料庫，查看 declared type、Pandas dtype、語意型別、單位、空值、極端值、唯一值與範圍。
2. **中央單圖／圖庫／堆疊**：先完成單圖，可存入 VAP 圖庫，再將圖庫項目加入目前圖組；清單可用滑鼠上下拖曳排序。
3. **右側規格修正**：可收合；一般設定與左軸、右軸以樹狀結構呈現。常用值使用下拉選單或勾選，線寬、透明度、刻度與格式仍可完整調整。

建議流程（目前表單可先直接預覽，不必先加入圖組）：

```text
選擇來源 → 掃描／分析欄位 → 完成單圖 → 存入圖庫 → 從圖庫加入堆疊 → 拖曳排序 → 輸出
```

圖庫保存的是可重用的圖表規格，不會把來源資料複製進圖庫；可依名稱、標籤、圖型或欄位搜尋。加入圖組時會產生獨立圖表項目，不會改動圖庫原件。每次加入預設追加到 `charts[]` 最下方；輸出依清單順序由上到下排列。

標準圖高為 **420 px**。每張邏輯單圖的高度以標準高度倍數決定；圖數增加時畫布依倍數自動增高。完整操作與狀態界線請看 [`docs/VAP_v23_GALLERY_STACK_EDITOR.md`](docs/VAP_v23_GALLERY_STACK_EDITOR.md)。

## 圖表能力

| 功能 | 說明 |
| --- | --- |
| 單圖輸出 | 從圖組選一張，獨立輸出 PNG／PDF／SVG／HTML |
| 單圖圖庫 | 完成單圖後保存、搜尋，並從圖庫加入目前堆疊 |
| 單軸 | 一個實體 Y 軸，可繪一或多序列 |
| 雙軸 | 左右軸分別設定欄位、名稱、單位、格式與圖型；預設維持相同 tick 數 |
| 右軸圖型 | `line`、`bar`、`area` |
| 垂直圖組 | 持續向下追加，共享日期軸、滑鼠上下拖曳，並依標準高度倍數自動增高 |
| 堆疊 | `stacked_bar`、`stacked_area`、`stacked_bar_100`、`stacked_area_100` |
| 一般圖型 | `line`、`bar`、`area`、`scatter`、`step`、`heatmap` |
| K 線與成交量 | `candlestick` 邏輯單圖展開成 75% K 線與 25% Volume 兩個上下單軸 panel，共享 X 時間軸 |
| Seaborn color combo | `deep`、`muted`、`Set2`、`tab10`、`viridis` 等 palette 可在全域或單圖覆寫 |
| 自動版面 | 依圖數、420 px 標準高度倍數、layout profile 與 X 軸密度計算畫布及日期刻度 |
| 大資料保護 | 預設每圖最多渲染 5,000 點；折線保留多序列首尾／極值包絡，K 線做連續桶 OHLCV 聚合，完整資料仍用於品質稽核 |

### Candlestick + Volume 規則

Candlestick 必須指定 `open`、`high`、`low`、`close`、`volume` 五個欄位。價格欄位視為已經是 **adjusted price**；程式不從未調整價格推導或重算 adjusted OHLC。輸出時，一個邏輯 Candlestick 會展開成上下兩列：K 線列占該圖高度 75%，Volume 列占 25%；兩列各自只有一個 Y 軸並共享 X 時間軸。預設台股顏色為：

- 收盤價高於或等於開盤價：紅色 `#D62728`（漲）。
- 收盤價低於開盤價：綠色 `#2CA02C`（跌）。
- 每根 Volume 柱沿用同一根 K 線的紅／綠色，透明度預設 `0.75`。
- 價格缺值可使用 `missing = ffill` 從前一個交易日延續；Volume 與成交股數欄位永遠不會被 ffill、interpolate 或 zero 補值。
- 已有時間列不會因週末或休市日被擴增；缺口只稽核、不製造虛假交易日。

### 標準高度與單圖倍數

- 標準圖高為 `420 px`；一般圖預設 `1.0×`，需要更多空間時以圖高倍數調整。
- K 線／量仍屬同一個邏輯圖表項目，先計算整體高度，再以 `75% / 25%` 分成兩個實體單軸 panel。
- 所有 panel 共享時間軸；上方 panel 可隱藏重複 X 標籤，最下方保留完整日期標籤。
- HTML 依標準像素高度渲染；PNG／PDF／SVG 由相同相對高度換算實體尺寸，避免不同格式的比例漂移。

### 面積、柱寬與波動範圍

- 一般柱與堆疊柱的柱寬由相鄰 X 值自動計算，間隔盡量小但不交疊。
- K 線寬由 `candle_width_ratio` 控制，預設 `0.88`；不規則交易日仍以最小正間隔限制寬度。
- 柱圖透明度預設 `bar_alpha = 0.75`；線下填色預設 `area_alpha = 0.50`。
- 自動 Y 範圍會包住有效資料的最大／最小值；柱圖依 `axis_zero_policy` 可包含零，價格 K 線預設不強迫從零開始，以保留波動幅度。

## 刻度契約

預設 `tick_policy = vap_locked`，左右軸各自計算合理範圍，但保持相同 tick 數（預設 5 個、4 個等距區間），不強迫不同單位使用相同數值間距。步距只取以下 nice steps 的 `10^n` 倍數：

```text
1.25、2、2.5、5（必要時延伸為 10） × 10^n
```

刻度範圍會在包住最大／最小值的前提下盡量緊湊。小數格式會保留必要精度與尾零，例如 `1.25`、`2.50`；可用 `y_format`／`secondary_y_format` 選擇 `auto`、`number`、`magnitude`、`percent` 或 `comma`。需要一般 Matplotlib 自動刻度時可改成 `tick_policy = auto`。

## 自動辨識資料來源

| 類型 | 辨識與讀取 |
| --- | --- |
| CSV／TSV | 編碼降級、指定欄位與列數限制 |
| Parquet／無後綴 Parquet | 以 `PAR1` 檔頭辨識並做欄位投影 |
| 無後綴 CSV／TSV | 依文字內容與 delimiter 辨識；UTF-8 失敗時降級 CP950 |
| Parquet 資料夾 | 遞迴掃描 partition，可指定資料集 |
| Excel | 自動列出 Sheet |
| JSON／JSONL | 欄位與語意型別分析 |
| SQLite | 唯讀開啟，自動列出 table／view |
| DuckDB | 唯讀開啟，自動列出 schema.table |
| SQLAlchemy URL | PostgreSQL／MySQL／SQL Server 等；需安裝對應 driver |

主要欄位語意：`datetime`、`identifier`、`price`、`volume`、`currency`、`percentage`、`flow`、`count`、`numeric`、`category`、`text`、`boolean`。完整來源範例請看 [`docs/DATABASE_EXAMPLES.md`](docs/DATABASE_EXAMPLES.md)。

Discovery manifest 會在來源允許時保存 declared type、nullable、primary key 與 index，不保存樣本值、明文 query 或連線密鑰。SQLite／DuckDB 以唯讀模式開啟；遠端 SQLAlchemy 流程只提交單一 `SELECT`／`WITH`，拒絕寫入關鍵字，並遮蔽 URL 密碼、token 與 secret。遠端資料庫仍必須使用資料庫端的唯讀帳號，不能把文字檢查視為權限控制。

## 可調參數速查

v2.2 完整欄位、型別與預設值仍可查閱 [`docs/VAP_v22_PARAMETER_REFERENCE.md`](docs/VAP_v22_PARAMETER_REFERENCE.md)；v2.3 新增的圖庫、標準高度與編輯器契約請看 [`docs/VAP_v23_GALLERY_STACK_EDITOR.md`](docs/VAP_v23_GALLERY_STACK_EDITOR.md)。以下是最常用的分組：

**Project（全域）**：`title`、`subtitle`、`source_label`、`width_inch`、`panel_height_inch`、`standard_panel_height_px`、`dpi`、`style`、`context`、`palette`、`shared_x`、`figure_face_color`、`axes_face_color`、`output_directory`、`output_name`、`output_formats`、`watermark`、`max_rows`、`render_max_points`、`sample_rows`、`date_column`、`max_x_ticks`、`layout_profile`、`html_renderer`。

**Chart（單圖）**：`id`、`type`、`title`、`x`、`y`、`secondary_y`、`axis_mode`、`secondary_type`、`unit`、`secondary_unit`、`height_ratio`／標準高度倍數、`palette`、`colors`、`alpha`、`secondary_alpha`、`bar_alpha`、`area_alpha`、`line_width`、`secondary_line_width`、`marker_size`、`stack_mode`、`bar_gap_ratio`、`bar_width_ratio`、`candle_width_ratio`、`open`、`high`、`low`、`close`、`volume`、`up_color`、`down_color`、`normalized_y`、`show_legend`、`show_zero_line`、`axis_zero_policy`、`secondary_axis_zero_policy`、`tick_policy`、`tick_count`、`y_format`、`secondary_y_format`、`max_x_ticks`、`auto_optimize`、`render_max_points`（可選，留空沿用全域）、`show_latest_label`、`show_outliers`、`where`、`cmap`、`center`、`annot`、`annot_format`、`heatmap_index`、`heatmap_columns`、`heatmap_value`、`heatmap_aggfunc`。

**Quality（單圖資料安全）**：`quality_mode`、`invalid_date_policy`、`duplicate_date_policy`、`outlier_policy`、`outlier_iqr_multiplier`、`missing`。預設先稽核再提出修正；所有修正只作用於 render copy，不回寫來源。

### Normalized series

把欄位放入 `normalized_y` 後，該 series 會在 Plotly HTML 中以「隱藏但可勾選」狀態載入，使用者可在圖例勾選後查看；原始值與主圖軸不會被改寫。Normalized 使用獨立的隱藏刻度軸，因此即使同圖右軸是百萬級 Volume，勾選後也不會被壓扁。PNG、PDF、SVG 為靜態輸出，會保留主圖與一般 series，互動式隱藏控制只存在於 HTML。

## CLI

掃描資料來源：

```powershell
.\.venv\Scripts\python.exe vap_seaborn_stack_generator.py discover `
  --source "C:\Data\tw_market.duckdb" `
  --table tw_prices_adj `
  --output output\tw_prices_manifest.json
```

自動建立第一張圖；若資料同時具備 Date、完整 adjusted OHLC 與 Volume，會優先建議 Candlestick + Volume：

```powershell
.\.venv\Scripts\python.exe vap_seaborn_stack_generator.py auto-config `
  --source "C:\Data\tw_market.duckdb" `
  --table tw_prices_adj `
  --config tw_price_stack.json
```

新增 Candlestick + Volume：

```powershell
.\.venv\Scripts\python.exe vap_seaborn_stack_generator.py add `
  --config tw_price_stack.json `
  --id price_volume_candle `
  --type candlestick `
  --preset candlestick_volume `
  --x Date `
  --open "Adj Open" `
  --high "Adj High" `
  --low "Adj Low" `
  --close "Adj Close" `
  --volume Volume
```

新增雙軸線／柱圖：

```powershell
.\.venv\Scripts\python.exe vap_seaborn_stack_generator.py add `
  --config tw_price_stack.json `
  --id price_volume `
  --type line `
  --preset price_volume_dual `
  --axis-mode dual `
  --x Date `
  --y "Adj Close" `
  --secondary-y Volume `
  --secondary-type bar
```

生成完整圖組或指定單圖：

```powershell
.\.venv\Scripts\python.exe vap_seaborn_stack_generator.py render --config tw_price_stack.json
.\.venv\Scripts\python.exe vap_seaborn_stack_generator.py render-one --config tw_price_stack.json --id price_volume_candle
```

## Presets

- `candlestick_volume`：adjusted OHLCV、紅漲綠跌、價格 ffill／量不補、75% K 線＋25% Volume 上下兩列單軸。
- `price`：價格單軸折線，排除零軸。
- `price_volume_dual`：價格左軸線、Volume 右軸，可改成 `line`／`bar`／`area`。
- `volume`：成交量單軸柱圖，包含零軸。
- `signed_flow`：正負資金流柱圖與零線。
- `composition`：`stacked_area` 的 100% 組成圖。
- `multi_series`：多序列單軸折線。
- `heatmap`：樞紐式熱圖。

所有預設值集中在 `vap_defaults.json`；程式會將未列出的內容與內建 SSOT 合併，因此局部修改不會破壞必要設定。修改後可在 UI 的「全域預設值」頁保存。

## 輸出

- `PNG`：Seaborn／Matplotlib 高 DPI 靜態圖。
- `PDF`：向量 PDF，可直接列印或放入報告。
- `SVG`：向量 SVG。
- `HTML`：`html_renderer = plotly` 時為自包含、離線可開啟的 Plotly 互動垂直堆疊圖；不依賴 CDN。若改成 `svg` 則輸出離線內嵌 Matplotlib SVG 預覽。
- `<output_name>_report.json`：圖型、軸模式、renderer、刻度策略、堆疊模式、完整列數、實際渲染列數與欄位。
- `<output_name>_audit.json`：結構化 Alerts、資料修正、渲染縮減方法與稽核軌跡。
- `<config>_source_manifest.json`：資料來源、table／sheet、欄位分析與建議。

## 測試

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

測試涵蓋舊版相容、所有圖型、單圖／圖庫／圖組流程、未儲存表單預覽、標準高度與 K 線／Volume 兩列單軸、拖曳重排、雙軸鎖定刻度、OHLCV 顏色與空值規則、100% 堆疊、CSV／SQLite／Parquet／DuckDB、格式 sniff、品質稽核、離線 Plotly HTML、normalized series 控制、50,000 列壓力測試、跨程序原子交易、安全遮蔽、Windows launcher、預設值合併與錯誤攔截。

詳細規格請看 [`docs/VAP_v2_SPEC.md`](docs/VAP_v2_SPEC.md)、v2.3 編輯器規格請看 [`docs/VAP_v23_GALLERY_STACK_EDITOR.md`](docs/VAP_v23_GALLERY_STACK_EDITOR.md)、參數表請看 [`docs/VAP_v22_PARAMETER_REFERENCE.md`](docs/VAP_v22_PARAMETER_REFERENCE.md)、資料庫來源請看 [`docs/DATABASE_EXAMPLES.md`](docs/DATABASE_EXAMPLES.md)。
