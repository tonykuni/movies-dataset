# VIA Investment Performance & Responsive Analysis

本資料夾包含 2026-09-16 對 VIA 投資管理模組、中央 UI 首屏載入、DOM 分布、CI quality gate 與響應式測試的分析。

## 主要報告

- `VIA-Investment-Performance-Responsive-Report.md`：投資管理模組效能、容量與響應式詳細分析
- `VIA-Investment-Performance-Responsive-Report.html`：可直接以 `file://` 開啟的自適應淺色 HTML 報告
- `central_ui_loading/VIA-Central-UI-Adaptive-Compact-v3-Report.md`：透明無框印章 Logo、自動最佳化 layout、資產前後對比與 v3 UAT
- `central_ui_loading/VIA-Central-UI-Adaptive-Compact-v3-Report.html`：v3 可直接以 `file://` 開啟的視覺報告
- `central_ui_loading/VIA-Engine-Hub-v4-Plotly-Seaborn-Report.md`：Plotly × Seaborn chart engine、五核心 Engine Hub 與 tooltip/crosshair UAT
- `central_ui_loading/VIA-Central-UI-Loading-Optimization-Report.md`：非同步載入、Code Splitting 與 DOM 首屏瓶頸建議

## 最新 v3 重點

中央 UI 與 SYNCHRONIZER 改用透明去背、無框、無陰影、無 filter 的小尺寸印章 Logo。v3 基線中央 UI 檔案由約 1.56 MB 降至 164 KB，Logo payload 由約 1.43 MB 降至 22.5 KB；v4 Engine Hub 加入本機 Plotly-like SVG 圖表與互動後，目前 UI 約 172 KB。1440px PC、768px 平板與 390px 手機均通過自適應視覺檢查，沒有水平 overflow；中央 UI 搜尋／篩選／modal／UI Lab／add-on 與 SYNCHRONIZER 投資範本回歸均通過。

## 圖表

原投資分析圖表位於 `charts/`。中央 UI 載入與 v3 圖表位於 `central_ui_loading/charts/`，包含 payload 瓶頸、DOM region、DOM tag、延後掛載候選與 v3 前後資產對比。

## 原始資料

原投資分析資料位於 `data/`。中央 UI v3 的可稽核量測位於 `central_ui_loading/data/central_ui_adaptive_v3_profile.json`，Code Splitting 計畫位於 `central_ui_loading/data/central_ui_code_split_plan.json`。

## 判讀限制

瀏覽器載入指標是單次 `file://` Performance API smoke measurement，不是多次重複的 P50／P95 benchmark。響應式 UAT 驗證指定 viewport 下的版面與水平溢出，不等同於 FPS、記憶體峰值或壓力測試。
