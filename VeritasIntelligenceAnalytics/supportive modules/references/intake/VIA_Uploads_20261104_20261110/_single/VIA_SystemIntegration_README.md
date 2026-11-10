# VIA System Integration Engine v1.0

## 交付方式

核心只有一個 Python 檔案 `VIA_SystemIntegrationEngine.py`。HTML、CSS、JavaScript 內嵌於同一檔，不需要 React、Node.js 或外部 CDN 才能使用基本畫布。

## 安裝與啟動（Windows PowerShell）

```powershell
py -m pip install fastapi "uvicorn[standard]"
py .\VIA_SystemIntegrationEngine.py --self-test
py .\VIA_SystemIntegrationEngine.py --smoke
py .\VIA_SystemIntegrationEngine.py --serve
```

預設瀏覽器網址：`http://127.0.0.1:8765`；如需修改請用 `--port 8766`。完成的 JSON、SQLite 會輸出到啟動目錄下 `VIA_SystemIntegration_Data`。可以用 `--data-dir` 指定新的路徑。Windows 亦可使用 `python` 取代 `py`。

## 進階（選用）

```powershell
py -m pip install polars duckdb networkx graphviz
```

- Polars：每次執行另存不可覆寫的 Run ID 專屬 Parquet 快照（三類：狀態、需求、原子稽核）。
- DuckDB：附加 run summary、狀態矩陣、需求矩陣、AST 原子事件鏡像表。
- NetworkX：DAG 拓撲統計；沒有時使用內建拓撲排序。
- Graphviz：可搭配輸出的 DOT 文字進一步渲染；本引擎不自行執行 `dot` 外部程式。

## 已可實際執行

1. 拖曳式 SVG 節點畫布、連線編輯、縮放、平移、JSON 匯入匯出。
2. FastAPI / WebSocket 逐節點狀態推送（RUNNING、PASS、FAIL、BLOCKED、SKIPPED），可中止後續節點。
3. Kahn DAG 拓撲排序、循環依賴拒絕、資料型別與執行階段反向連線拒絕。
4. 限定安全節點類型；對使用者輸入 AST 只做解析與修復預覽，不進行 `exec`。
5. SSOT、REGEX、同義字正規化、衝突阻斷；真的跑 10 項內建 unit checks 與 2 項 integration checks 及 120 筆並行系統運算。
6. 真實沙盒檔案原子寫入及故意失敗後 SHA-256 回滾驗證（不修改外部檔案）。
7. 雙矩陣：五階段節點狀態，以及 10 個治理需求在 T1 至 T5 的驗證證據。
8. SQLite 只透過應用程式 INSERT 歷史記錄、串聯 SHA-256 雜湊鏈、獨立 JSON 歸檔。
9. 同拓撲歷史真實批次之 Rolling latency gate；少於 3 期改用保底值，不寫入虛構歷史資料。
10. 外部格式交換：Drawflow JSON、Mermaid、Graphviz DOT、React/Svelte Flow、Cytoscape.js、AntV X6、BPMN 2.0 XML（後四種只轉模型，不會自行執行外部平台）。

## 20 工具的正確整合界線

工具面板共有 20 個能力描述。**「READY」代表本引擎具備對應的格式轉換或分析功能，不代表所有第三方函式庫都已安裝或所有原生 UI 已接通**。包含 Prefect、Airflow、Dagster、SpiffWorkflow、Node-RED、Rete.js 等重型平台，目前為 `ADAPTER_ONLY`，需要對應服務的設定、認證及獨立環境，才可建置真正的雙向呼叫。

## 安全與品質注意

- 預設只綁定 127.0.0.1；本機工作階段 Token 防止其他網站直接呼叫寫入 API，HTTP/WebSocket 進行 Origin 檢查。
- 預設關閉外部網路。只有程式頂部 `OPTIONAL_NETWORK=True` **且**執行時給 `--allow-network` 才能向 `NETWORK_ALLOWED_HOSTS` 的 HTTPS URL 發送 HEAD；不允許轉址。
- 不執行任意 Python、shell 或外部任務，不會自動安裝 Python 套件，不會自行修改使用者的專案原始碼。
- AST 解析率、需求證據率、測試通過率與「程式碼覆蓋率」是不同概念；未執行 `coverage` 時程式碼覆蓋率顯示為未測量。
- Rolling 機制僅輔助偵測退化；單元／整合／系統／結果驗證仍是必須通過的硬性閘門。
- SQLite 只增不減是**應用層政策**，並非 DB 本身不可竄改。SHA-256 鏈可協助偵測部分修改，但不能保證抵抗有權限重算所有雜湊的管理者。
- BPMN/XML/React Flow/Cytoscape/X6 匯出是圖結構交換，不會將任意函式轉成可安全執行的對方平台任務。
- 本交付未修改使用者本機原始碼，也未更新 GitHub。

## 自動測試驗證

使用 `--self-test` 執行 21 個標準庫單元／負向測試，`--smoke` 執行預設完整工作流。API/WebSocket、JSON 格式轉接、拒絕非法節點、AST 阻斷、失敗傳播、稽核鏈變更偵測，均已在隔離測試工作區測試。環境缺少 Polars 和 DuckDB 且無法連線安裝，因此兩者的實際執行尚未驗證；Chromium 瀏覽器導航受本測試環境政策限制，前端已透過 Node 語法檢查，未宣稱完成實際滑鼠互動的瀏覽器 E2E。
