# def VCGC Tool Modules v0100

以 **既有 VCGC 能力為優先、缺口以獨立模組補充** 的交付包。Python 標準庫可完成核心功能；不需要啟動另一個 HTTP UI server。

## def 已核對的現況

- GitHub `tonykuni/movies-dataset` 的 registry tree 共 2,530 項，未截斷；FunctionInventory v0221 有 370 個測試站。這是檔案及宣告站數，不是本次重跑 370 測試。
- GitHub 主控台最高檔名版本為 v0192；先前交付的 v0194 另作來源比對。不能據此推定 Windows 正在執行哪版。
- GitHub handoff：`lamp=GREEN`、`closeout_lamp=YELLOW`、pending 104。交接可續接不等於驗收完成。
- 已有 token/read/slice/digest/etag/chain、MCP 引擎、原生 MCP server、DuckDB UI、SkillExport；不建立第二套中央治理來源。
- Graphify 已有 v0101 發布紀錄，鎖定 graphifyy 0.9.100、獨立 venv、code-only 與分系統圖；此為歷史交付證據，非本次主機驗證。Ponytail 已有旁證，不能判為完全未導入。
- AgentOS v0300 已有 SQLite 記憶、圖形匯出及外部 adapter 目錄；某些 adapter 仍只是接口。
- 兩個 ChatGPT 分享頁與指定 Claude Code session 無法讀取。已讀取附件；沒有假裝已連線到該 session。session URL 不是 MCP endpoint。

`config/tools.json` 提供完整 17 項工具映射、來源、狀態、下一步及候選動詞；`config/evidence.json` 記錄來源檔案與 SHA256。

## def 一鍵啟動

將 ZIP 與 `Start-VCGC-ToolModules-v0100.ps1` 放在 Downloads，於 PowerShell 7 執行：

```powershell
& "$HOME\Downloads\Start-VCGC-ToolModules-v0100.ps1"
```

外層啟動器核對 ZIP SHA256，解壓到獨立 LocalAppData 目錄，再用目前可用的 Python 3.11+ 執行 34 個回歸測試、三輪來源靜態檢查與 HTML。只讀 VIA 原檔、不修改 GitHub、不啟用外部 hooks、不重新安裝環境。每次輸出新 RUN 目錄，保留先前結果，PowerShell 不會被腳本關閉。

也可指定來源：

```powershell
& "$HOME\Downloads\Start-VCGC-ToolModules-v0100.ps1" -SourceRoot "$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"
```

自動來源候選：OneDrive 下的 movies-dataset VIA、Github 下的 VIA-VDF-VRN、Downloads 下的 VIA。實際存在的候選全部列為唯讀輸入。各來源有不同 root_id，不因內容相同合併身分。輸出預設在 `%LOCALAPPDATA%\VIA\ToolModules\Runs`。

## def 短動詞與模組位置

| 動詞 | 完成的工作 | 對應模組 |
|---|---|---|
| panorama | 最多三輪 AST／compile／來源完整性檢查；每輪九矩陣 | inventory.py、report.py |
| catalog | 17 項工具的既有／缺口／待驗清單 | actions.py、config/tools.json |
| context | 依名稱／路徑擇取 AST 短卡；有字元上限與來源 SHA | actions.py |
| compare | 兩份 snapshot 的新增、移除與變更清單 | actions.py |
| module-check | PY 契約、完整 def、SHA、ID／動詞碰撞檢查 | actions.py |
| skills | 只讀 SKILL.md 標頭索引，不載入指示或執行 | actions.py |
| metrics | 真實 usage JSON／JSONL／CSV 聚合、event 去重與衝突拒絕 | actions.py |
| schema | 有 DuckDB 時讀 information_schema；沒有套件就明確失敗 | actions.py |
| graph | 匯出靜態 import 候選關係的 Mermaid；不是 Graphify 運行 | actions.py |
| registration-plan | 產生 VCGC 註冊順序與 MCP 擴充提案 | actions.py |

入口：`VIA_VCGC_ToolModules_v0100.py`；全部參數位於模組頂端或 CLI 參數；每個函式完整提供。

```powershell
python .\VIA_VCGC_ToolModules_v0100.py catalog --out "$env:LOCALAPPDATA\VIA\ToolModules\Runs"
python .\VIA_VCGC_ToolModules_v0100.py context --input '<路徑>\round_3\snapshot.json' --query 'mcp' --budget 4000 --out "$env:LOCALAPPDATA\VIA\ToolModules\ContextRuns"
python .\VIA_VCGC_ToolModules_v0100.py module-check --input .\examples\module.json --out "$env:LOCALAPPDATA\VIA\ToolModules\Runs"
python .\VIA_VCGC_ToolModules_v0100.py metrics --input '<路徑>\usage.jsonl' --out "$env:LOCALAPPDATA\VIA\ToolModules\MetricRuns"
```

`--out` 必須在所有輸入根目錄之外。`--root` 可重複使用，建議固定 `名稱=路徑` 以保持節點身分。行數變化不影響一般函式 ID；條件分支內的定義帶分支定位資訊，移動分支時可能需對照舊 ID。完整來源不會匯入或執行；Python 檢查不能代表 PowerShell AST 或實機執行通過。

## def 新增一個 PY 模組

1. 參考 `examples/normalize_tags.py`：完整提供 `def describe()`、`def execute(request)`、`def main()`，參數放頂端。
2. 建立同資料夾的 manifest JSON，設定 `module_id`、`verb`、`description`、相對 `entry`、檔案 `sha256`、`input_schema`、`output_schema` 與 `capabilities`。
3. 執行 `module-check`。這是靜態接入檢查，不執行新檔案，不將靜態通過冒充 runtime 通過。
4. 經原生 VCGC 做 requirement／workflow／function inventory 新版登錄與中央發號；再由 native manager 驗證結果，才開放派發。

`VTM-TOOL-001…017` 為本套件清冊 ID；`VTM-N-*` 為來源 AST ID；`VTM-CUSTOM-*` 為自訂提案 ID。中央 `ssot_id` 留空，沒有私自搶用 CGC_MDL／REQ／WKF 號碼。一般函式 ID 依 root_id、相對路徑與完整定義名稱產生；雜湊另外記錄版本，禁止用相同數值消除不同來源。

## def MCP 與原生 VCGC 接入

本套件是可執行的補強引擎和可審查的接入提案，尚未改寫既有主控台。原生 `via-vcgc toolmodules` 動詞及新增 MCP tools **尚未註冊**，不能直接假設可呼叫。生成的 Registration_Proposal.json 指出需新增的動詞及順序。

沿用 `CGC_MDL279_MCPServer` 與 `VIA_MCP_Engine`。目前倉庫 `.mcp.json` 指向 MDL279 v0101，而 registry 存在 v0102；這是版本差異，需按實際鎖與收據檢查，不自動把設定改成最高檔名。新增 MCP 工具需在主機驗證 initialize → tools/list → tools/call；不能將 Claude 網頁工作階段 URL 當成 MCP URL。

來源順序：原生 `token` → `functions` → `handoff check` → 家族 `chain` → `ssot panorama` → 新版註冊 → 編號 audit（遺失／改身分／重號皆 0）→ manager 測試 → checkpoint。本次遠端唯讀盤點沒有宣稱已執行這些主機治理命令。

AutoHarness、claude-mem 的學習／壓縮可能另外消耗模型 Token；Ponytail 或 Graphify 的外部 benchmark 不當作 VIA 節省率。ChartDB 是 schema/ERD 工具，DuckDB 是資料庫，dashboard 是顯示層；中立 schema JSON 尚未完成 ChartDB 格式轉換。WordPress 未有站點；Amydoc 身分待確認；Claude code up 先按 steph-frtech 專案列候選，不在既有 VIA 根目錄套用腳手架。

## def 驗證與限制

34 項 Python 契約與回歸測試通過。測試包含來源不執行、不改寫、快取失效、重複定義、不同來源不合併、路徑逸出、ID／動詞碰撞、重複 JSON key、usage 衝突、HTML 注入逃逸及三輪輸出。

本次三輪選定來源：18 個檔案，12 個 Python，1,659 個 AST 節點，0 個 AST／compile／讀取錯誤；第 2、3 輪來源雜湊不變。這不是整個 Windows VIA 或全部子系統的運行驗證；高風險節點只列報，未修改原檔。來源中的重複定義可能是版本包裝，需依賴鏈判定，不能自動刪除。

JavaScript `node --check` 通過。Playwright 本機瀏覽器啟動被 socket 權限阻擋；cloud browser 不允許 file://，所以視覺與互動回歸仍未完成。可在具備既有 Playwright／Chromium 的主機執行：

```powershell
python .\tests\browser_check.py --html '<路徑>\round_3\Matrix.html' --output '<路徑>\browser_receipt.json'
```

Windows PowerShell AST／啟動、原生 Celeritas 全 15 加速器、DuckDB 實機、VCGC 中央註冊、外部工具連線均未實測。腳本在 Windows 啟動時做自身原生 PS Parser 檢查。核心用至多六個唯讀工作緒、內容雜湊快取、有界輸入、忽略依賴目錄、短卡與延遲依賴載入；不將這些冒稱既有 15 加速器全部啟用。

沒有實際模型 usage 就不產生 Token 節省率或費用。metrics 所需欄位：event_id、action、input_tokens、output_tokens；完整相同 event 去重，同 ID 不同數值判 INVALID。輸出 UTF-8 JSON、HTML、Mermaid；這次沒有投資數據，沒有為了格式要求生成空 Parquet。

## def 來源

- https://github.com/tonykuni/movies-dataset
- https://github.com/tigerless-labs/autoharness
- https://github.com/Graphify-Labs/graphify
- https://github.com/DietrichGebert/ponytail
- https://github.com/chartdb/chartdb
- https://duckdb.org/docs/stable/clients/python/overview
- https://developer.wordpress.org/rest-api/
- https://github.com/microsoft/playwright-mcp
- https://agentskills.io/specification
- https://github.com/thedotmack/claude-mem
- https://github.com/vercel-labs/skills
- https://github.com/steph-frtech/claude-code-up

## def 導入 VIA 倉之後(2026-11-27)

- 位置:`VeritasIntelligenceAnalytics/supportive modules/toolmodules/`;入口 `python VIA_VCGC_ToolModules_v0100.py <動詞>`,自測 `--selftest`(34 項回歸 + 各模組加速器實際載入)。
- 加速器:原包只在說明文字寫 `[VIA:ACCEL-BRIDGE]`(只有標記 = 假加速);導入時每支 `.py` 第 3 行加標記、下接真的匯入 `VIA_SuperAccel_Module` 的橋,`MANIFEST_SHA256.json` 與 `examples/module.json` 的雜湊重算。
- 沒收進來的:`Invoke-VCGC-ToolModules-v0100.ps1`(操作員要打的 PS 只留 `Start-VIA-v0100.ps1` 一支)· `validation/` 跑檔(別台機器的輸出,不是程式)。
- **跟現有 VCGC 工具重疊的動詞(先用原生的;這裡的只當補強,不另立正本)**:
  | 本包動詞 | 現有 VCGC 動作 |
  |---|---|
  | catalog | `CGC_MDL158 tools` |
  | panorama | `CGC_MDL158 scan` / `hydra` |
  | context | `CGC_MDL158 read` / `slice` |
  | compare | `CGC_MDL158 delta` |
  | graph | `via-graph`(真 Graphify;本包只出 import 關係的 Mermaid 候選) |
  | skills | 主控台 `agentos skills list` |
- **現有 VCGC 沒有的(本包新增)**:`metrics`(真實 token 用量聚合)· `schema`(DuckDB information_schema)· `module-check`(新模組接入契約靜態檢查)· `registration-plan`(註冊順序提案)。
- 要把重疊的併回 MDL158 家族當動詞,照「重複功能先併再簡化」另開一批(刪舊仍照三條件)。
