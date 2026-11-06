# VeritasAutoPlot v0300 · All-In-One

## 交付結果

- `VAP_AllInOne_v0300.py`：單一 Python Engine，整合唯讀資料 Adapter、VDF/VQG Gate、Catalog、HTTP Bridge、圖片/模板保存、SSOT/Context/Function Inventory API 與啟動器。
- `VAP_AllInOne_UI_v0300.html`：單一自包含 HTML Workbench，已內嵌 5 個 JavaScript 引擎，不再依賴 `../js/*.js`。
- `VAP_Function_Inventory_v0300.json`：完整函式與能力清冊。

## 盤點數量

- Python 函式：70
- JavaScript 模組函式：62
- HTML Workbench 函式：459
- 具名函式合計：591
- Active 圖形能力：40 Canonical + 5 Composite = 45
- 歷史相容圖庫：28（僅作 lineage/import，不覆蓋 Active SSOT）
- 能力群組：28；已解析衝突：12

## 啟動

```powershell
python .\VAP_AllInOne_v0300.py --run-self-test
python .\VAP_AllInOne_v0300.py
```

預設只綁定 `127.0.0.1:8765`，啟動後自動開啟 HTML UI。若不希望自動開瀏覽器：

```powershell
python .\VAP_AllInOne_v0300.py --no-browser
```

列出完整函式清冊：

```powershell
python .\VAP_AllInOne_v0300.py --function-inventory
```

## API

- `/api/health`、`/api/catalog`、`/api/refresh`
- `/api/images`、`/api/templates`
- `/api/context`、`/api/functions`、`/api/spec`

## 治理邊界

- 正式輸入固定 `VDF/VRN → VQG → VAP`；VAP 不下載價格、不重算因子、不回寫上游。
- 股票價格僅接受 Adjusted Price 證據；Volume/Turnover 不在 VAP 內靜默補值。
- SQLite/DuckDB 唯讀；Runtime 僅 loopback；SVG/模板保存維持 SHA-256 與 Append-Only。
- 原始附件與 v027 套件未改動。
