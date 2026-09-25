# VIA Engine Hub v4：Plotly × Seaborn Chart Integration

**日期：2026-09-16**  
**檔案：** `VIA-UI-Standalone-NoServer.html`  
**執行模式：** local-only、單檔 HTML、無 CDN、無 Server

## 整合結果

中央 UI 的投資研究工作台已將原本的時間範圍 SVG 圖表提升為本機 Plotly × Seaborn chart engine。這不是載入外部 Plotly runtime，而是以 SVG geometry 實作 Plotly-like 的 light dashboard 結構，配合 Seaborn-inspired semantic palette，保留零伺服器與 `file://` 直接開啟限制。

圖表現在支援 **1D、1W、1M、3M** 四段時間範圍，以及 **折線、面積、柱狀** 三種圖形模式。滑鼠／觸控 pointer 移過圖表時，會顯示目前資料點的 crosshair 與 tooltip；圖表點、柱狀與面積會依模式切換。

## 五個核心引擎

| Engine | 職責 | 目前入口 |
|---|---|---|
| `layout` | PC／平板／手機 viewport 標記與 fluid layout | `VIA_ENGINE_HUB.layout.refresh()` |
| `visualization` | palette、range、chart mode、tooltip geometry | `VIA_ENGINE_HUB.visualization` |
| `interaction` | 搜尋、篩選、時間範圍、圖形模式與 pointer events | 既有 UI event layer + chart listeners |
| `state` | v2 localStorage／BroadcastChannel 狀態快照與發佈 | `VIA_ENGINE_HUB.state` |
| `addon` | 未來產業模組與圖表插件註冊 | `VIA_ENGINE_HUB.addon` |

## Palette

| 語意 | 色彩 | 用途 |
|---|---|---|
| Plotly blue | `#4c78a8` | 主線、主要控制、柱狀基底 |
| Seaborn teal | `#72b7b2` | 正向狀態、次要柱狀 |
| Seaborn coral | `#e45756` | focus point、風險與警示 |
| Seaborn yellow | `#f2cf5b` | watch／注意狀態 |
| Seaborn purple | `#b279a2` | 次要分類柱狀 |

## Browser UAT

以 `file:///home/ubuntu/VIA-UI-Standalone-NoServer.html` 執行：

- `window.VIA_ENGINE_HUB` 存在，版本 `4.0.0`
- 五個引擎入口均可用
- 三種圖形模式均可切換，10 個點與 10 個柱狀元素正確產生
- 3M range 正確更新標籤、數值 `+12.38%` 與資料點
- pointer event 正確顯示 crosshair 與 tooltip：`3M · 08/14 · +12.38%`
- 搜尋 `VDF` 回傳 1 筆可見端點
- 桌機與手機均無水平 overflow
- inline JavaScript `node --check` 通過
- 無 `fetch`、WebSocket、EventSource、CDN 或外部 `<script src>` 依賴

## 視覺驗證

- 桌機截圖：`engine_hub_screens/via-desktop-1440.png`
- 手機截圖：`engine_hub_screens/via-mobile-390.png`
- 視覺檢查：`engine_hub_v4_visual_findings.md`

此圖表引擎刻意不引入外部套件，以維持目前 VIA 的單檔可攜性。未來若要接入真實行情資料，只需將 `marketSeries` 替換為同一 schema 的本機資料來源，不必改動 UI、palette 或 chart interaction API。
