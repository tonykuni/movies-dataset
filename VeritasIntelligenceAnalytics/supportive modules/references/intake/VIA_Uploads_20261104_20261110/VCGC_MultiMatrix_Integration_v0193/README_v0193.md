# VCGC 五系統多矩陣整合 v0193

本套件的執行檔只有一個 Python 後端和一個 HTML 前端。HTML 不啟動 HTTP 伺服器；Python 的 watch 模式透過本機工作佇列與前端交換資料。

**交付狀態：引擎與介面已完成本次測試；Windows 生產部署、全樹加速／網路覆蓋、原生系統結果驗證仍須在 Tony 的電腦執行。** 預載畫面來自實際取得的 9 個 PY、4 個 JSON 的唯讀掃描，並非兩個 Windows 目錄的完整掃描。45 項內建自測通過；14 項隔離整合驗收中 13 項通過，PowerShell 真實解析 1 項因環境缺件跳過。

## 1. Windows 一次啟動

解壓縮後，在含有下列兩個檔案的資料夾開啟 PowerShell 7：

- `CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py`
- `VCGC_MultiMatrix_v0193.html`

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py matrix install --apply --activate-tools --watch --open
```

Python 需求為 3.11 以上；範例使用已有的 Python 3.12。若實際工作環境位於 `via_core` 或 `via_core_312`，以該環境的 `python.exe` 取代 `py -3.12`。不自動切換、建立或安裝另一套 venv。

預設掃描根目錄：

```text
C:\Users\tonyk\OneDrive\Documents\movies-dataset
C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics
```

預設輸出：

```text
C:\Users\tonyk\AppData\Local\VCGC\MultiMatrix_v0193
```

畫面開啟後按「連接報告資料夾」，選擇上方輸出目錄。Chrome／Edge 等支援 File System Access 的瀏覽器可讀取結果並送出固定動作；不支援時用「匯入掃描 JSON」，命令仍在 PowerShell 執行。Ctrl+C 停止 watch，既有 PowerShell 視窗不會被程式關閉。

若目前原生 VCGC 的測試閘已失敗，安裝會保留檔案並停止。可先用下列命令取得完整診斷和可操作矩陣：

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py matrix scan --activate-tools --watch --open
```

這個命令只建立輸出與快取，不改寫掃描來源。實際的子系統修正仍走原有管理器、版本化變更與測試。未經驗證的全樹注入不會被本工具自動標成完成。

## 2. 原生 VCGC 整合位置

本次核對的 GitHub 基準為 `tonykuni/movies-dataset` 的 commit `4647c8c12e931b6d69730cd0077ecfb41caba1b5`，當時的原生 console 為 v0192。本套件沒有提交或推送 GitHub。

安裝器先找到既有 `VeritasIntelligenceAnalytics\supportive modules\registry`。若現存 console 尾版不是 v0192，或已有更高版，不覆蓋，輸出版本衝突原因。安裝器不從不完整的參照檔重建原生系統。

| 項目 | 安裝動作 |
|---|---|
| 中央入口 | 新增 `supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py` |
| 前端 | 新增 `supportive modules\VCGC_Matrix\VCGC_MultiMatrix_v0193.html` |
| 需求清冊 | 讀取本機 `VIA_Requirements_SSOT` 尾版，新增下一版、補需求與 tally |
| 功能清冊 | 新增下一版 `VIA_VCGC_FunctionInventory_SSOT`，加入 `matrix selftest` station |
| 工作流程 | 新增下一版 `VIA_Workflow_VCGC_SSOT`，登錄掃描、驗證、註冊流程 |
| 原生註冊 | `registry-sync --apply` → CGC_MDL237 只處理本次新增檔案的 scope → 編號 audit → `ssot panorama` → `test --quick` → `handoff check` |
| 正式中央編號 | 由既有中央編號引擎裁定；本地 UUID 不冒充中央 SSOT ID |
| 最終 checkpoint | 保留為原生治理待驗項目；沒有可重跑的原生收據時不自行結案 |

安裝前順序為 `token`、`handoff check`、`functions`、`token chain`、`ssot panorama`、`test --quick`。六項都成功才新增整合檔案。安裝前後的來源雜湊、計畫、交易與命令紀錄會寫入輸出目錄。原生命令的退出碼 0 只記為 `RETURNED_ZERO`，不冒充五階段測試通過。

既有 `via-vcgc` 若使用原生尾版選取機制，安裝後可使用：

```powershell
via-vcgc matrix scan --watch --open
via-vcgc matrix selftest
via-vcgc matrix native-check
```

原有 `token`、`mcp`、`handoff`、`functions`、`test` 等動詞延遲委派到前版鏈，不改變原生所有權。VDF、VRN、VQG、VAP 的管理器仍各自獨立。

## 3. 五個左面板入口與矩陣

| 入口 | 專屬內容 |
|---|---|
| VCGC | 全系統治理、工具、測試、修正、版本、Skill、舊版整合與註冊 |
| VDF | 擷取引擎、輸入資料來源、資料庫輸出與契約 |
| VRN | 報告輸入、擷取欄位、年度數值與結果驗證；VRN-1／VRN-2 由實際檔案識別 |
| VQG | 資料庫輸入、指標定義、公式與參數候選；不另植入 TA-Lib |
| VAP | 圖形定義、軸線、欄位與參數候選 |

M00 總覽；M01 檔案與 AST；M02 加速／網路；M03 輸入；M04 輸出；M05 參數與時間；M06 VQG；M07 VAP；M08 SSOT／依賴；M09 測試／驗證；M10 錯誤；M11 修正；M12 效能；M13 版本稽核；M14 Skill；M15 舊版比較；M16 註冊。

M01 固定八欄：燈號、編號、名稱含版本、更新日期、AST 結構、錯誤與 AST、解決方案、修正與更新紀錄。來源時間是檔案 mtime，與掃描觀測時間、測試完成時間分開；下載參照檔的 mtime 不是 Git 提交日期。

資料依「系統／類別 → 檔案／契約 → AST／欄位」展開。主表分頁，AST 前 120 節點內嵌；完整節點保存在 `nodes` 目錄，連接輸出資料夾後按需讀取。VQG／VAP 會從真實 JSON 中發現公式、指標及圖形定義，不編造不存在的公式。未宣告的輸入／輸出方向顯示 `UNDECLARED`，不以檔名猜測後冒充契約。

## 4. 覆蓋率的精確意義

| 指標 | 分子／分母與限制 |
|---|---|
| 檔案枚舉完整性 | 所有指定目錄皆可讀、沒有未解析的連結或存取錯誤；依賴目錄的排除清單另列 |
| AST parse | 成功原生解析檔數／發現的所有 PY、PS1、PSM1、PSD1；語法錯誤、解析器缺失、大檔限制保留於分母 |
| AST detail | 完整保留詳細節點的檔數／發現檔數；節點達上限會明示截斷 |
| 加速靜態覆蓋 | 有橋接匯入與 API 候選呼叫的可執行來源檔／全部可執行來源檔；純 marker 不算 |
| 加速執行覆蓋 | 有有效工具鎖與實跑探針收據的來源檔／全部可執行來源檔 |
| 網路覆蓋 | 所有 VDF 檔與已識別對外出口列入；動態載入、適用性未決另列，不偷刪分母 |
| 測試覆蓋 | 逐檔 U/I/S/R/C，沒有收據為 NOT_RUN；AST 語法成功不等於測試或結果正確 |

PowerShell 使用 `System.Management.Automation.Language.Parser::ParseFile`，不執行被掃描檔案。缺 PowerShell 時顯示 `PARSER_UNAVAILABLE`。Python 以 `ast.parse` 加 compile 檢查，不 import 被掃描檔案。

工具鎖採用實際本機鎖檔與 SHA256，不自行猜「最新版」。只有 `--activate-tools` 才嘗試載入鎖定 Celeritas 的既有 SuperAccel bridge；外部工具缺件／雜湊不符會留黃燈。本後端另有有界執行緒池、增量 SHA 快取與批次解析，不宣稱已在每一支業務引擎完成 20 個加速器的執行驗證。

## 5. 測試與結果驗證

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py matrix selftest
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py matrix run-tests --plan .\TestPlan.json
```

`TestPlan.json` 是明確契約，並非任意 shell：

```json
{
  "schema": "via.matrix.test-plan/1",
  "tests": [{
    "id": "VQG-UNIT-001",
    "stage": "UNIT",
    "entity": "C:/實際根目錄/VQG_factor_v0100.py",
    "script": "C:/實際根目錄/tests/test_factor.py",
    "script_sha256": "填入實際腳本SHA256",
    "args": [],
    "timeout": 120,
    "input_files": [{"path": "C:/實際根目錄/data/reference.json", "sha256": "填入實際資料SHA256"}],
    "result_json": "C:/Users/tonyk/AppData/Local/VCGC/MultiMatrix_v0193/factor_result.json",
    "assertions": [{"name": "計算與參考值一致", "path": "value", "equals": 4}]
  }]
}
```

實際根目錄須包含在 `--roots`；結果位置須在根目錄或 `--out` 內。所有測試腳本需列出完整 `script_sha256`，所有真正影響結果的輸入都應列入 `input_files`。結果 JSON 每次寫入新的 `run_id`，舊結果未變不能算新實跑。程式停止時寫退出碼、執行時間、日誌雜湊、斷言和引用資料雜湊。

支持階段：`UNIT`、`INTEGRATION`、`SYSTEM`、`RESULT_VALIDATION`、`CLOSE_OUT`。結果驗證應由獨立公式、官方資料或已確認的 golden reference 提供預期值，不能把同一段計算原樣重算當作獨立驗證。

加速／網路執行探針可由真正的測試在結果 JSON 的 `tool_probes` 內提供。加速器需 `tool_sha256`、`source_sha256`、正數 `call_count`、`output_validated: true`；網路另需完整 `outlet_node_ids`、`denied_respected: true`、`origins_verified: true`。只有來源一致、工具鎖匹配且 INTEGRATION 或 SYSTEM 收據有效通過，才採用探針。此介面接收實際探針證據，不自行捏造引擎呼叫次數。

收據有 24 小時預設有效期；來源、依賴集合、規則、工具、環境或引用證據檔改變即標 STALE。全專案 context 採保守失效策略，並非精準只失效最小相依子圖。

## 6. 全景修正與回復

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py matrix repair-plan
```

會輸出逐檔 `repair_plan.json`：語法優先、AST 錨點、來源雜湊、工具缺口與必要驗收。建議順序為並行發現 → 按相依順序修正 → 最後重掃／測試。**本版沒有在未驗證的業務檔案中全面插入程式碼**；需依缺口呼叫既有原生修復流程或以版本化完整函式修正，再取得收據。M11 不會把建議當成已完成修正。

```powershell
py -3.12 .\CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py matrix rollback
```

回復只移除該次安裝新建且內容未被改動的 5 個整合檔案，原先的版本保留。若新檔被修改就拒絕回復。原生 `registry-sync`／編號引擎後續產生的記錄屬中央治理狀態，應由中央治理自身處理；不能宣稱這個 rollback 會撤銷所有原生副作用。

## 7. 舊檔合併結論

| 比較 | 結論 |
|---|---|
| SystemIntegrationEngine 與 v0300 | 34 個同名頂層定義中 32 個 AST 相同，有明確共通能力重複 |
| MatrixGovernance v0100 與 v0300 | 33 個同名頂層定義中 27 個 AST 相同 |
| v0300 | `create_app` 3 次、`main` 2 次定義，可能為刻意包裝；不直接判作程式錯誤 |
| 原生 v0192 | 保留完整舊動詞鏈，新增 v0193 `matrix` 動詞 |
| LayerMatrix／SettleAll | 保留專用矩陣、編排與原始收據，不再啟動一個重複管理介面 |

本次重新整理共通治理能力，不把大型舊檔的全部內容再次內嵌。舊 AgentOS 的記憶體工作流、DAG、多圖形格式匯出等專用功能仍由既有管理器提供，不宣稱已全部重寫進這個後端。完整比較雜湊及函式 AST 雜湊在 `MergeComparison_v0193.json`。

## 8. 六組 Skill 矩陣與 Claude Project

M14 分成 Claude、ChatGPT、Manus、Gemini、Copilot、跨平台，共 22 個能力／使用方式條目。這是能力與使用清冊，不等於 22 個可直接安裝的技能包；帳戶未連接仍顯示 NOT_CONNECTED。

Claude Project 的實際用法：把本 README、該次 `snapshot.json`、相關契約和少量已驗證案例放入專案；先提供 `delta`、檔案 ID 與失敗收據，必要時再讀完整 AST。需要改檔或執行時，交給有本機存取權的 Claude Code／其他執行環境。Claude 聊天看得到 `C:\...` 文字不代表能讀取電腦。

可貼入 Project instructions 的工作規則：

> 使用繁體中文。先確認 snapshot 的範圍、來源、版本與時間，再讀 delta 和相關 file ID／AST ID。保留五系統獨立管理器與原生 VCGC 動詞。不得把靜態 marker、exit 0、模擬測試或舊收據當作目前生產通過。修改提供完整 def，參數集中頂部，保留舊版；來源雜湊不符即停止該變更。每次回報 U/I/S/R/C 證據、未完成項目與精確覆蓋率分母。不得自行推送 GitHub。

官方參考（本次查閱）：

- Claude：https://support.claude.com/en/articles/12512180-use-skills-in-claude
- ChatGPT／Codex：https://developers.openai.com/plugins/concepts/skills
- Manus：https://help.manus.im/en/articles/14753565-how-to-share-and-use-skills-in-manus
- Gemini CLI：https://geminicli.com/docs/cli/skills/
- GitHub Copilot：https://docs.github.com/en/copilot/concepts/customizations/agent-skills

本次提供的 ChatGPT 分享頁與 Claude Code 分享頁未能讀取；未引用其不可取得內容。比較依已取得的既有引擎及 GitHub 固定 commit 正本完成。

## 9. 輸出與稽核

`snapshot.json`、`files.csv`（UTF-8 BOM）、`files.parquet`（已有 pyarrow 時）、完整 `nodes/`、`receipts/`、`events.jsonl`、`repair_plan.json`、`install_plan.json`、`install_transaction.json`、`registration.json`、`native_logs/`、`selftest.json`。`exports.json` 明示 Parquet 是否實際產生；缺 pyarrow 不自動偷偷安裝。

事件鏈是 SHA256 串接的本地可檢查紀錄，沒有簽章或外部時間戳，不宣稱防止有權改寫整條鏈的人偽造。快取不取代證據。工作佇列限定 scan／native-quick／selftest／export，使用工作階段 token、有效期、ID 防重播；沒有任意 shell 或 UI 自動安裝動作。

所有原始庫、舊版引擎和 GitHub 正本在本次雲端工作中均未被修改。Windows 真正部署結果以該主機的 `registration.json` 與原生收據為準。
