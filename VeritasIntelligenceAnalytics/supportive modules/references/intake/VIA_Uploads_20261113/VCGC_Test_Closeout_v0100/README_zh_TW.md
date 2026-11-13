# VCGC Test Closeout v0100

Veritas Intelligence Analytics  
VCGC · Unit → Integration → System → Result Verification → Close-Out

## 從過去的哪套引擎接續

| 既有來源 | 查得的內容 | 本版的接法 |
|---|---|---|
| VCGC MultiMatrix Resilience v0194 | `matrix --help` 實際列出 **14 個公開子動詞**。M17 有 20 項失敗防護 | 隨包附原版 Python，SHA-256 一致。用 `matrix selftest` 與 `matrix resilience-test` 重新跑 45 項回歸與 22 項故障測試，驗證 JSON 收據 |
| AiVerbBridge 與既有 VCGC token 用法 | 歷史紀錄中確認 6 條路徑 `read`、`slice`、`digest`、`pack`、`etag`、`chain`。`--brief` 為選項 | 以收據定位、內容雜湊、故障去重、差量摘要與輸出上限接續這套省額度流程。可用已安裝主控重新探測 `token --help` |
| VIA System Integration Engine v0300 | 舊版已做五階段矩陣。當時嚴格治理因 `pyarrow` 缺少，通過 60/63 | 可在專案 Profile 加入 `agentos_matrix` 檢查。接受原版 SHA-256，實際呼叫 `--matrix-test`，核對 JSON gate 與案例數 |
| Windows 正式 VCGC 與功能站 | 主控會委派舊版本。已安裝版本、全部動詞數及站數待實機盤點 | `-NativeConsole` 可重新核對該主控。加 `-StationRegistry` 會讀官方功能站 JSON，另外計數有效 ID |

14 個動詞與 6 條歷史 token 路徑各有範圍，不可直接相加。功能站數、獨立 MCP 工具數與主控 CLI 動詞也分開看。套件會使用兩個已驗證的測試動詞，功能站數須使用你實際的 `VIA_VCGC_FunctionInventory_SSOT_v*.json`。

[既有 v0194](https://chatgpt.com/library?file_id=libfile_da12ed7fc1f48191b7907f089a0691a9&account_id=personal) · [既有 v0300](https://chatgpt.com/library?file_id=libfile_e554e48cbc708191b81b5193f205bfd0&account_id=personal)

## 一鍵執行

完整解壓後，在 PowerShell 7 進入目錄。預設用既有 Python 3.11+ 執行，結束後開離線 HTML 測試矩陣。必要時以 `-Python` 指定 VIA 虛擬環境。

```powershell
& .\Start-VCGC-Test-Closeout-v0100.ps1
```

先盤點實際主控、測試站，或演練自動修正與重測。

```powershell
& .\Start-VCGC-Test-Closeout-v0100.ps1 -InventoryOnly -NativeConsole 'C:\實際路徑\CGC_MDL149_實際主控.py' -StationRegistry 'C:\實際路徑\VIA_VCGC_FunctionInventory_SSOT_實際版本.json'
& .\Start-VCGC-Test-Closeout-v0100.ps1 -RepairDemo
```

`-RepairDemo` 會讓第一輪故意失敗。引擎在副本加入已登錄的 JSON 值，核對原始 SHA，重測受影響檢查，再以新副本跑完整五階段。實際專案用 `-Profile` 指向自己的契約 JSON。

## 反饋與收尾

| 行為 | 引擎會做什麼 |
|---|---|
| 開始前 | 驗證五階段、需求至少跨兩階段、先後依賴、範圍、來源和執行環境雜湊 |
| 跑測試 | 候選目錄執行既定指令，有界逾時與日誌。要求本輪新產出的 JSON 斷言或含測試案例的 JUnit |
| 查結果 | Python AST／編譯、JSON 型別與欄位、CSV 唯一鍵與內容對帳、可選 Parquet schema。原始檔案雜湊會再核對 |
| 修正 | 遇到已定義的 JSON 故障才進入修正，支援新增缺值、精確舊值替換、別名搬移。修正只能作用於副本，需核對舊檔雜湊及條件 |
| 重測 | 先重跑相關測試與必要依賴，再用新副本完整驗證。逾時重試成功仍保留待確認 |
| 結案 | 收據、日誌、關鍵產物與 HTML 封存雜湊。會回傳 `PASS_LOCAL` 或 `BLOCKED`，正式放行由 VCGC 原生驗收 |

- 30 項失敗與解法見 `FailureMatrix_v0100.json` 及離線 HTML。F01–F20 沿用 v0194，F21–F30 補上測試漏跑、空 JUnit、重試假綠、舊輸出、對帳、上下文洩漏、重複回饋、來源改動、修復衝突及完整回歸。
- 每個 run 用 UUID。在同一 Profile、程式、輸入及環境下重送 UUID，已封存的結果會直接回傳。中斷且全部已執行站都可重播時，會用全新候選副本再跑。可能已有副作用的非重播站會回報待核對。
- 連續跑同一 Profile 時，可加 `-Since <前次 Run ID>`。反饋只列新故障指紋，保留重複與省略數；可用收據 ID 向下讀。完整日誌留在本機執行目錄。
- 專案的測試指令由本機操作者的 Profile 選定，於副本工作目錄執行。應選用自身可審查的測試指令。這個目錄邊界適用於引擎的讀寫與候選修正，子程序仍使用 Windows 帳戶的 OS 權限。

```powershell
python .\VCGC_Test_Closeout_v0100.py feedback <RUN_ID> --budget 1800
python .\VCGC_Test_Closeout_v0100.py evidence <RUN_ID> input-contract --round baseline
python .\VCGC_Test_Closeout_v0100.py verify <RUN_ID>
```

## Graphify 與 OmniRoute

```powershell
& .\Start-VCGC-Test-Closeout-v0100.ps1 -Profile .\Profile_Repair_Demo_v0100.json -Graphify
& .\Start-VCGC-Test-Closeout-v0100.ps1 -Profile .\YourProfile.json -Graphify -Since '<前次 Run ID>' -RouteModel '<本機 OmniRoute Model 或 Combo ID>'
```

- **Graphify**。使用現有 `graphifyy` CLI，核對執行檔雜湊，在候選工作區執行 `graphify extract . --code-only --out …`。程式從圖譜讀取程式檔關係，擴充局部重測範圍，並可在前次 run 比較中列受影響的檢查。圖譜缺席時，測試以明確的 Profile 依賴繼續。Graphify 圖譜不會移除或取代任何完整回歸站。
- **OmniRoute**。先在 PC 啟動自己的 OmniRoute；本程式只連 `127.0.0.1` 的 OpenAI 相容 `/v1/chat/completions`。在本機安全設定 `VIA_OMNIROUTE_API_KEY` 後才指定 `-RouteModel`。只有封存且仍為 `BLOCKED` 的結果才送一筆請求，欄位是最多 8 組故障代碼與階段，由你選的 Model／Combo 路由。回覆以診斷建議保存，若 gateway 回傳 usage，會記錄用量。同一 run、模型和內容重送會讀取收據；連線不明時保留 `IN_DOUBT`。OmniRoute 可能將該精簡內容交給其已設定的模型供應商。
- 單獨查看有問題的 run 可用 `python .\VCGC_Test_Closeout_v0100.py omniroute <RUN_ID> --model <MODEL_OR_COMBO>`。埠預設 20128，可透過 `--port` 或 `-RoutePort` 指定。

[Graphify](https://github.com/Graphify-Labs/graphify) · [OmniRoute](https://github.com/cheaper-inference/OmniRoute)

## 跨 AI

CLI 和 JSON 收據為同一套協定。任何可在 PC 呼叫 CLI 的助理均可共用 run ID。使用 MCP 時，可在選定的 Python 環境安裝 `requirements-mcp.txt`。以下指令產出帶絕對路徑的 stdio 設定。

```powershell
python -m pip install -r .\requirements-mcp.txt
python .\VCGC_Test_Closeout_v0100.py mcp-config
python .\VCGC_Test_Closeout_v0100.py mcp-config --profile .\Profile_VCGC_Native_v0100.json
```

預設 5 支唯讀工具 `verbs`、`status`、`feedback`、`case`、`evidence`。上述最後一個指令另開 `run`，只有本機選定且雜湊鎖定的 Profile 可以跑。工具全名均為 `vcgc_closeout_<工具>`。同一 run ID 可從 Claude Code、Codex、Gemini CLI／Antigravity、GitHub Copilot 的支援客戶端接著查。ChatGPT 網頁須經支援工作區的 MCP 連線，例如 Secure MCP Tunnel，設定須在該工作區完成。長時間測試可在 PowerShell 讓引擎持續運作，模型以 run ID 查狀態。

[MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) · [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

## 專案 Profile

複製隨附的 JSON 及欄位範例。將 `source` 指向實際專案，`inputs` 指定明確檔案或資料夾。相對路徑使用 `/`。每站應填 `id`、`stage`、`kind`、`requirements` 及必要的 `depends`。可列 `watch` 供影響範圍計算。

| 檢查 | 設定重點 |
|---|---|
| `python_ast`／`file` | `path` |
| `json` | `path`、`assertions: [{path: [欄位或索引], equals: 值}]` |
| `csv_equal` | `path`、`reference`、`key: [唯一鍵欄位]` |
| `parquet` | `path`、`columns`，需要當前 Python 環境已有 `pyarrow` |
| `command` | `argv` 陣列、`output`、`format`、JSON `assertions`，並明列 `replay_safe` 與需要時的 `retry_timeout` |
| `native_matrix` | `action: selftest` 或 `resilience-test` |
| `agentos_matrix` | `path` 為原版 v0300 Python，納入 `inputs`。嚴格矩陣需要 `pyarrow` |
| `closeout` | 只放最後階段，核對本輪之前所有站 |

詳細資料預設位於 `%LOCALAPPDATA%\VCGC\Test_Closeout_v0100\runs\<RUN_ID>`。環境未執行真實 Windows 原生 VCGC、各 AI 帳號、真實 Graphify 或 OmniRoute 供應商。附帶 QA 區分真實 v0194 測試、Linux MCP stdio、Graphify CLI 替身與 OmniRoute 本機測試服務。
