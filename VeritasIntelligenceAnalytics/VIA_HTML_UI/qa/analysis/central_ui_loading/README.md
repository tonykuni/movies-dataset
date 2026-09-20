# VIA Central UI Loading Optimization Analysis

這個子資料夾分析中央 UI 的非同步載入、Code Splitting、DOM 首屏瓶頸，以及 adaptive compact v3 的資產優化成果。資料來自目前 `VIA-UI-Standalone-NoServer.html` 的 browser DOM 量測、source byte 分解與 Chromium file:// 視覺／互動回歸。

## 最新 v3 / v4 交付

`VIA-Central-UI-Adaptive-Compact-v3-Report.md` 是最新的透明無框印章 Logo、自動最佳化 layout、PC／平板／手機響應式與前後資產大小對比報告。`VIA-Central-UI-Adaptive-Compact-v3-Report.html` 可直接以 `file://` 開啟。`charts/central_ui_adaptive_v3_before_after.png` 視覺化 v3 前後的文件、Logo、CSS 與 JavaScript 大小。

`VIA-Engine-Hub-v4-Plotly-Seaborn-Report.md` 是目前最新的圖表整合報告，記錄 Plotly-like SVG geometry、Seaborn semantic palette、折線／面積／柱狀模式、tooltip/crosshair 與五核心 Engine Hub UAT。v4 目前中央 UI 約 172 KB；v3 的 164 KB 是加入圖表互動引擎前的基線。

`data/central_ui_adaptive_v3_profile.json` 保存 v3 的檔案大小、Logo render 尺寸、Performance API smoke measurement、DOM 數量與 UAT 結果。`adaptive_v3_visual_findings.md` 記錄中央 UI 與 SYNCHRONIZER 的桌機、平板、手機視覺檢查。

## 首屏與 DOM 基礎分析

`VIA-Central-UI-Loading-Optimization-Report.md` 與 `VIA-Central-UI-Loading-Optimization-Report.html` 保留原始首屏瓶頸與 Code Splitting 建議。`charts/` 內含 payload、DOM region、DOM tag 與延後掛載候選圖表；`data/` 內含 JSON／CSV 原始資料與 Code Splitting 計畫。

## 判讀限制

FCP、DOMContentLoaded 與 Load event 是單次 `file://` Performance API smoke measurement，不是正式的 P50／P95 benchmark。正式性能比較應固定瀏覽器、viewport、冷啟動／暖啟動，重複至少 10 次，並保存 median、P95、long task 與互動後模組載入時間。
