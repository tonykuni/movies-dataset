# VIA Agent OS + VCGC + System Integration Engine v3.0

**單一 Python 主程式、內嵌 HTML/CSS/JavaScript，多頁控制台。** `VIA_SystemIntegrationEngine.py` 為 ZIP 內的直接啟動名稱；ZIP 外亦提供版本化檔名。Python 3.11+。

## 啟動（Windows PowerShell）

解壓 ZIP 後進入程式資料夾，再執行：

```powershell
py -m pip install fastapi "uvicorn[standard]" pyarrow psutil
py .\VIA_SystemIntegrationEngine.py --self-test
py .\VIA_SystemIntegrationEngine.py --agent-self-test
py .\VIA_SystemIntegrationEngine.py --serve --port 0
```

系統在 PowerShell 顯示本機網址，預設瀏覽器會開啟 HTML UI；PowerShell 執行期間保持開啟。只聆聽 `127.0.0.1`，無需 Node 或 CDN 來顯示基本 UI。若使用者原先的 Python 虛擬環境已有依賴，不必重新安裝。**啟動前不會自動安裝套件、改寫既有環境或上傳 GitHub。**

指定既有專案來源、啟動唯讀掃描：

```powershell
py .\VIA_SystemIntegrationEngine.py --serve --port 0 `
  --project-root "C:\path\to\your\repository" `
  --vcgc-root "C:\path\to\your\VCGC\registry"
```

請將上方路徑換成您實際允許讀取的本機資料夾。未指定來源時 UI 顯示 `NO_SOURCE`，不會使用假資料取代實機核對。CLI 的 `--project-root` 支援多層子套件 `.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.jsx`, `.tsx`, `.ps1`, `.psm1`, `.html`, `.htm`, `.json`，預設每個檔案不超過 1 MiB，最多 400 個檔案。含有程式碼的檔案**只讀，不 import、不 exec、不執行 PowerShell**。

## 介面頁數與責任分離

原有控制台頁面完全保留：01 I/O Parameters / SSOT Matrix、02 Executive Dashboard、03 Governance、04 Testing、05 Workflow DAG、06 多矩陣報告、07 Visual QA、08 v0105 原始快照、09 Technical Versions。新增：

- **10 Agent Skills & Router**：8 個本地 Skill Contract、依賴 DAG，選擇 Integration／Code／Research／Investment 工作類型，建立工作計畫並執行可驗證的本機診斷。Claude／GPT／Gemini／DeepSeek 僅有路由候選，未取得 API 憑證與允許前絕不假裝已呼叫。
- **11 VCGC Registry & Conflicts**：唯讀檢視 `--vcgc-root` JSON 候選、同義字碰撞、SSOT ID 重複且內容不同、REGEX 編譯錯誤、尚未發號；不代替 VCGC 發號，也不修改母系統或子系統。
- **12 Panoramic AST / Memory**：Python `ast` 靜態分析、相對 import 依賴、HTML DOM 重複 ID、JSON 解析、JS／PS 詞法層訊號；三輪檢查報告。五類可由使用者明確同意寫入的長期記憶（架構／因子／策略／研究／程式模式），`operating_memory` 第六類為預留治理元資料，**無 VCGC 核准不得修改**。

## 核心功能與證據

1. 原有 DAG 編輯、拓撲排序、JSON 載入與匯出、WebSocket 執行、節點追蹤、AST 自動修復預覽、沙盒原子寫入與 SHA-256 回滾仍保留。
2. 原有 Matrix Governance 的五階段測試：Unit、Integration、System、Verification、Close-Out。Parquet 為正式資料輸出的必要套件；缺少 `pyarrow` 時此項會 FAIL，並且 Go-Live 持續 BLOCKED。CSV 使用 UTF-8 BOM，金額以 Decimal 驗證。
3. 原有 20 種 Python / JavaScript 圖形化工具的相容性轉接目錄仍保留。新增 17 項跨語言 AST／靜態分析／CST／Playwright／Lighthouse 的**能力探測**。僅偵測到安裝不等於有成功執行整合。
4. Graphify、agentmemory、Ponytail、OmniRoute 與 Agent Skills 內建橋接契約；其中本機 `AGENT_SKILLS` 可以工作，外部 MCP / Agent Plugin／AI 模型仍顯示 `NOT_CONNECTED`。沒有檢查憑證就不做跨模型自動切換，也不承諾固定的節省 Token 比例。
5. Agent 計畫輸出 `PLAN_ONLY`；本機診斷輸出 `LOCAL_DIAGNOSTICS_ONLY`，將已測量的本機工作與需要外部 agent、交易資料、人工決策的步驟分開標示。
6. 持久記憶 SQLite 採新增事件與雜湊鏈，禁止 UPDATE / DELETE 的應用層觸發器，但無法防止取得檔案寫入權限的人篡改檔案。記憶必須手動勾選同意才寫入；含金鑰、debug log 等內容會被拒絕。
7. Playwright 視覺 QA 可在本機有 Chromium 時操作；提供桌面、筆電、平板、手機 × 三種字距／密度之 12 個檢查組合。Lighthouse 必須另行安裝並顯式開啟；不會在背景默默啟動外部 CLI。

## 完整 CLI

```powershell
py .\VIA_SystemIntegrationEngine.py --doctor
py .\VIA_SystemIntegrationEngine.py --self-test
py .\VIA_SystemIntegrationEngine.py --agent-self-test
py .\VIA_SystemIntegrationEngine.py --smoke
py .\VIA_SystemIntegrationEngine.py --matrix-test
py .\VIA_SystemIntegrationEngine.py --agent-report --project-root .\MyProject --vcgc-root .\Registry
py .\VIA_SystemIntegrationEngine.py --visual-test
py .\VIA_SystemIntegrationEngine.py --serve --port 0
```

**請注意** `--matrix-test` 必須有 `pyarrow`；`--visual-test` 必須有 Chromium / Playwright 並且允許瀏覽器導航本機 URL。真正的 UI 伺服器與 Python 後端需一同運作，ZIP 裡的 HTML Preview 只是方便離線檢視畫面，無法離線呼叫 API。

## 為什麼不把每個工具都直接合併成一個 import？

Airflow、Dagster、SpiffWorkflow、Node-RED、React Flow、Graphify MCP、OmniRoute 與 PSScriptAnalyzer 各有不同的獨立執行環境或協定。此程式採 **single orchestrator, optional adapters**：保留接口規格與可探測安裝狀態，避免虛假的「全部已連線」，並且不要為了使用一個畫布而啟動多套不相容的排程器。真正接通外部服務需要各工具配置、權限驗證、契約測試、實際數據與稽核。

## 未完成的正式驗證

截至本次交付，此工作區已確認 44／44 Python 回歸案例、12／12 離線 Chromium UI 尺寸組合；本機 DAG smoke test 已批准，但只是本機範例。獨立嚴格治理 63 項案例，因未安裝 pyarrow，有 3 項直接或連帶失敗。尚未執行使用者 Windows / PowerShell 實機驗證、VCGC 的中央發號、VDF/VRN 實機整合、外部模型呼叫、168 小時長測、真實瀏覽器到 HTTP 的完整自動化 E2E、資料庫容量驗證與授權系統整合。**正式生產放行持續為 BLOCKED**，不可把本機測試證據當作正式核准。
