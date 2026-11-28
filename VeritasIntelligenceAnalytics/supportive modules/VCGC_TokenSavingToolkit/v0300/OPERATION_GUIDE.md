# VIA PanoramaFusion SuperEngine v0300

同一個 Python 入口提供兩動作，接回現有 VCGC 工具、Graphify、OmniRoute 與各系統管理器。v0200 原檔保留；v0300 另交新版。

| 動作 | 主指令 | 行為 |
|---|---|---|
| 1：模組化、指令簡化、整合、註冊 | `1 --apply --retire` 或 `unify --apply --retire` | 三輪檢查、同檔 AST 合批、依賴排程、FNC-LIB、工具橋、正式註冊／別名稽核、可回滾退役、全面複驗 |
| 2：VCGC 全景、修復與除錯 | `2 --apply` 或 `sweep --apply` | 三輪覆蓋與來源一致性、AI／GitHub／圖譜／路由狀態、AST 修復候選、完整管理器與最後複驗；此動作不退役舊檔 |
| 兩者共用一次三輪 | `both --apply --retire` | 同一份基準完成兩動作，避免重複掃同一來源 |

未帶 `--apply` 時產生候選與收據。`--check-only` 只檢查、不建立修復套用。`--offline` 停用模型檢核，仍可盤點，且會因必要路由證據不足而阻擋套用。`workflow.auto_repair=false` 也會阻止修復。原有 `fusion` CLI 已接入新三輪流程。

## 一行啟動

在倉內這個資料夾(`supportive modules\VCGC_TokenSavingToolkit\v0300`)開啟 PowerShell 7,叫**有防護的尾版** v0305(它沿薄尾鏈載入 v0300 本體;不要直接跑 v0300,也不要從 `VIA_PanoramaFusion_Complete_v0300.zip` 解壓出來跑——那是 v0300 凍結發行包,沒有 v0302 起的防護):

```powershell
python .\VIA_PanoramaFusion_SuperEngine_v0305.py --root "$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics" both
```

v0302 起 `--apply` 不寫回原檔(只出候選夾與收據,收據寫 `apply_refused`)、只修 VCGC 自己的檔、環境只稽核(重建由操作員 `via-envgov apply --approve`)、深修不外送原始碼。也可用 `.\VIA_PanoramaFusion_Start_v0305.ps1 both`。

首次會建立 `%LOCALAPPDATA%\VIA\PanoramaFusion\engine_config_v0300.json`。未接入的管理器／來源會明確受阻。先依本文件與 `VIA_Integration_Contract_v0300.json` 補上現有 VCGC 的精確 argv、註冊清單、環境 SSOT、測試契約及端點。所有 `--root`、`--work`、`--config` 放在子指令之前。

可先執行 `init` 建設定；若明確指定舊 v2 設定，會另存 `_v0300.json`，原檔不覆寫。自訂設定時，既有系統啟動器須傳入 `VIA_DUAL_CONFIG` 的絕對路徑。

PS 啟動器只設定 UTF-8 及呼叫 Python。使用已有 PS 視窗即可保留視窗。`all`／`boot` 延續先降壓、三獨立 PID／日誌／健康收據；核心 Lane 已接入本次共用流程。

## 三輪、同批修復與最後檢查

1. 第一輪：正向盤點 manifest 全部註冊項，讀取 AST 骨架、錨點、SHA 及問題。
2. 第二輪：反向核對範圍與 ETag；未變更的骨架可重用。這是快取／來源一致性檢查，沒有宣稱是另一套獨立分析算法。
3. 第三輪：Python 原碼重新實讀 SHA 與 AST；核對來源漂移、缺檔及範圍變化。
4. 依 Graphify 與 AST import 建立依賴排程。同檔修復合成一個 task；不同檔、同依賴層可受控並行；有依賴的先後執行；循環列為待協同修復。
5. 在副本完成一輪 AST 修復，跑原版／候選契約、橋執行、各系統管理器、註冊及編號稽核。全部通過才寫正式檔。
6. 寫入後另做第四次全範圍檢查、完整 manager、來源對應的 Graphify 覆蓋證據、紅燈棘輪及 DuckDB／Parquet 留存驗證。任何必要步驟失敗，依 journal 回滾。

每輪都有應掃／已掃／略過，漏項不會被當成刪除。沒有正式 manifest 的探索盤點為 DISCOVERY_ONLY，不能代替正式覆蓋驗收。大型 DB 的內容正確性仍由所屬 manager 驗證，schema 不代表內容通過。

## 哪些問題能同批解決

- 已明確列入 `mcp_modules` 的 stdio MCP 診斷 `print()`：定位呼叫名稱後改成具型別的 stderr helper，保留 stdout 給協定。含顯式 `file=` 或動態 kwargs 的呼叫不盲改。
- 相鄰、完全相同的一般 `import`：在 AST 位元座標移除重複語句；`from ... import` 不自動去除。仍需契約／manager 驗證。
- 已提供的完整 def 補丁：同檔多符號以原始座標一次合併，從下往上切片；重疊補丁、錯誤 SHA、改動呼叫綁定或移除錨點會被拒絕。
- 所有候選 Python 的鎖定加速器橋，以及靜態辨識出的 HTTP／Session 模組之網路工具橋，交由共用候選與原生測試檢查。

不確定的回傳型別、金融公式、來源語意、動態匯入、循環依賴、資料路由與跨系統契約，保留明確待辦，由所屬 manager 或具證據的完整 def 補丁處理。語法已損壞而無法建立 AST 時，該檔列錯，其他獨立修復可先存候選，整輪不套用。

設定 `workflow.patch_file` 為本機 JSON 補丁陣列，每筆需 `path`、`symbol`、`before_sha256`、`replacement_def`，可加 `depends_on`。路徑必須在已註冊 Python 範圍。補丁可以補型別，不能任意改參數／預設值／裝飾器；新增未核准 I/O、動態呼叫、匯入或外部寫入會被阻擋。`approved_new_calls` 僅由你核准的既有治理設定提供，模型不能自行放寬。

## 最新正式工具與實際加速

此次從 GitHub `main` 的 `519ad418ca48871d031b907c43c635648bb5f9af` 鎖冊核對：

| 工具 | 正式版 |
|---|---|
| VeritasCeleritas | v1141 |
| AegisNexus | v1652 |
| Panorama／Token 工具 | v0125 |
| NLP Orchestrator | v0108 |

四份正式工具的版本與 SHA 證據列於 `VIA_Source_Locks_v0300.json`，工具正本沿用既有 VCGC 鎖冊指定路徑。執行時仍核對本機正式鎖冊。後續真正最新版本由 `tool_refresh` adapter 的新收據確認，不能把本次快照當作永遠最新。

批次修復會實際呼叫鎖定加速器的 `parallel_map`；存在 `thread_budget` 時讀取其預算，並再限制至最多 2 worker。原生入口與產生的橋會執行實際預算初始化。沒有可用 API 就受阻，不使用空 decorator 冒稱已加速。沒有宣稱任意既有算法因此自動變成零拷貝。

## 自動註冊與短指令

候選含 `VIA_CommandBindings_v0300.json`，列出 `via-fuse`、`via-panorama`、`via-super`、`via-super-tools`、`via-super-risks`。由既有 VCGC `registry_stage` 產生正式候選冊，核對所有 alias、命令測試、編號及 owner，再與來源同次可復原套用。

清單產生後的別名狀態是 CANDIDATE；只有原生註冊收據通過才算可用。引擎不自行發號、不修改 PS profile、不推 GitHub main。`registry_stage` 必須依現行 VCGC 的需求／工作流／ReworkGuard／提交／編號政策處理，不能自行用假 PASS 代替。

原生收據除了既有零遺失／零改身分／零重號，另需 `registered_aliases` 包含全部短指令、`commands_checked=true`、`alias_collisions=0`。退役還需 `retirement_audit` 的 chain-unused、尾版全動詞、已鎖成功數、owner 與舊 alias 保留證據。薄尾仍在載入鏈上或有唯一能力時保留。

## Graphify、AI 與儲存接線

Graphify 優先定位。原生 `graphify` adapter 會收到 `{query}` 與 `{manifest}`；來源 manifest 是模組相對路徑與完整 SHA，核對前、後的來源版本。回覆需 `source_manifest_sha256` 精確相等、`coverage_complete=true`、`uncovered=0`。單純服務在線或回 PASS 不足。衍生 graph／receipt JSON 不放進模組指紋，避免自我更新循環。

AI 對話來源使用本機匯出／已授權 `source_adapters`；沒有權限或匯出者列 NOT_CONNECTED，不讀瀏覽器憑證。GitHub 的本機 Git 快照與真正遠端查詢分開；現場遠端查詢走 `github_scan` adapter。OmniRoute 健康與實際模型推論分開，API 金鑰只讀環境變數。

超過 40 個檔案的例行模型請求，按功能群彙整全部來源數、符號數、規則命中數與 manifest SHA；逐檔 AST 與座標完整留在本機。高階函式修復另走有界目標窗。此版尚未實作 TS26 全鍵模型結果快取；不冒稱供應商 Token／費用節省已做 A/B 驗收。

現行 VCGC 規格要求 DuckDB 管理、Parquet 保存上下文。原生流程必須通過 `context_gate` 的 `owner=VCGC`、`duckdb_verified=true`、`parquet_verified=true`，並由 `context_store` 的回傳 SHA 證明證據包已寫入。失敗會回滾已套用的來源。此引擎不另建 syscat 或號碼主庫。既有 SQLite 僅用可丟棄的 ETag／AST 快取；缺 DuckDB 不接受 SQLite 作上下文主庫替代。

目前執行環境缺少 duckdb、pyarrow、polars、pytest，沒有繞過 VCGC 私自 pip 補裝。原生安裝與儲存由現有管理器接入。agent-mem 的記憶寫入只有在權威儲存成功後才交付；原生自帶的儲存不能因此宣稱已轉為 DuckDB。

## 清單與驗證

```powershell
python .\VIA_PanoramaFusion_SuperEngine_v0305.py tools
python .\VIA_PanoramaFusion_SuperEngine_v0305.py risks
python .\VIA_PanoramaFusion_SuperEngine_v0305.py token tools
python .\VIA_PanoramaFusion_SuperEngine_v0305.py token verbs
python .\VIA_PanoramaFusion_SuperEngine_v0305.py test --selftest
```

完整清單在 `VIA_Risk20_TokenTools_v0300.md`、CSV 與 `VIA_VCGC_Capabilities_v0300.json`。13 外部能力來自既有 v0103 規格；32 Token 功能逐項區分已實作／部分／待所屬 adapter，不將規劃當成啟用。

三輪來源收據在 `VIA_ThreeRound_Snapshot_Audit_v0300.json`。本次掃的是你提供的 v0101 備份內 749 個 Python 檔，三輪與最後全查每輪略過 0；探索盤點仍為 BLOCKED，未寫回你的 PC、GitHub 或原始備份。

本次測試的完整數量、結果、SHA 及範圍以 `VIA_QA_Receipt_v0300.json` 為準。測試使用 Linux 隔離 fixture、本機模型假端點與固定 SHA 假工具；原生 Windows、真實 OCR／資料庫品質、真實模型推論、遠端控制與正式 VCGC 發號仍待實機證據。契約子程序是程序隔離，不是 OS 安全沙盒。
