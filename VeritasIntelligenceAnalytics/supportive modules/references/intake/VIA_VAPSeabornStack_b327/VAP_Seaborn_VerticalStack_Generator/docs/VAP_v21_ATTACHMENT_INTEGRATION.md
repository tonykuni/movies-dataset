# VAP v2.2 附件整合決策

本文件記錄 `貼上的 Markdown (1)(20260902-141243).md` 對 v2.2 的影響。附件包含多輪 Plotly、Seaborn、Dash、CSS 與 JavaScript 範例拼接；它保留需求意圖，但不直接作為可執行 SSOT。正式規則集中在 defaults、ChartSpec、DataSourceSpec 與 quality diagnostics。

## v2.2 已整合

- 單圖、單軸、雙軸、堆疊與持續向下加圖。
- Plotly 自包含離線互動 HTML 垂直堆疊，與 Seaborn／Matplotlib 高畫質 PNG／PDF／SVG 分工。
- Seaborn palette 與明確欄位顏色映射可同時套用到一般圖、堆疊圖及靜態 renderer。
- adjusted OHLCV candlestick；台股慣例紅漲綠跌，Volume 柱逐列沿用 K 線顏色。
- 價格 `ffill` 只處理已存在時間列；Volume、TurnoverVolume 與成交股數永不補值。
- 雙軸相同 tick count、左右軸各自計算 nice step；合法步距為 `1.25 / 2 / 2.5 / 5 × 10^n`。
- 固定小數尾零（例如 `1.25`、`2.50`）、最大化有效波動且包住最大／最小值。
- 柱透明度 `bar_alpha = 0.75`、線下面積透明度 `area_alpha = 0.50`；柱寬自動縮至最小不交疊間隔。
- `normalized_y` 在 Plotly HTML 中預設隱藏但可透過圖例勾選顯示。
- 欄位、日期、空值、重複日期、缺口與 IQR 極端值稽核；Alerts、transformations 與獨立 audit JSON。
- Windows 11 檔案／資料夾選擇，來源自動 sniff 與資料庫 schema discovery。

## 經修正後的附件做法

| 附件做法 | v2.2 正式規則 |
| --- | --- |
| 左右軸使用相同 `dtick` | 左右軸各自計算適用數值的 step，只鎖定相同 tick count |
| 補滿所有日曆日 | 不製造週末／休市日，只稽核觀測缺口 |
| 對整張表線性插值 | 只有明確選擇才處理數值欄；Volume 永不 ffill／interpolate／zero |
| 自動 IQR clipping | 預設 report-only；`clip_iqr` 必須由使用者明確啟用 |
| 只用 `chart-main`／`chart-sub` | 使用任意長度 `charts[]`，可新增、排序、刪除、單圖或完整圖組輸出 |
| 所有參數平鋪 | 常用參數與進階設定分層，並可在 defaults UI 修改 |
| 只用 close 假造 K 線 | Candlestick 必須有完整 adjusted Open／High／Low／Close／Volume |
| CDN 載入 Plotly | HTML 內嵌 Plotly runtime，離線仍可開啟 |

## Plotly 與 Seaborn 的邊界

- Plotly 只負責 HTML 的 hover、zoom、legend toggle、normalized checkbox 與垂直 panel 互動。
- Seaborn／Matplotlib 負責 PNG／PDF／SVG 的靜態色彩、版面與向量輸出。
- 兩邊共用 ChartSpec、DataSourceSpec、Defaults、Diagnostics 與刻度契約，不把 Plotly API 塞入 Seaborn 靜態繪圖函式。
- Dash callback、CSS Grid browser runtime 與未定義公式的 Vibration／Advance／Proximity 不納入 v2.2。

## 資料安全底線

1. 原始來源唯讀。
2. 所有修正只存在於 render copy。
3. 重複日期預設 `fail`，避免多股票同日資料靜默遺失。
4. 極端行情預設不改值。
5. 修正前後與實際動作都寫入 audit。
6. 連線密碼不得進入 manifest、報告或 UI 狀態。
