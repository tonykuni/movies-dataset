# Veritas Intelligence Analytics 母系統 15 項必備能力詳細說明

**文件版本：** v1.0  
**日期：** 2026-08-25  
**作者：** Manus AI  
**適用範圍：** VIA 母系統、VRN、VDF、VAP、VPN、SSOT 與共用 ModPack

> **母系統的本質不是把多個工具放在同一個資料夾，而是用一致的身份、契約、狀態、證據與治理規則，管理所有子系統的完整生命週期。**

## 一、整體定位

Veritas Intelligence Analytics（VIA）應被定位為整個 Veritas 生態系統的**控制平面、治理中心與共享能力平台**。VRN 負責 WORD、PDF、IMAGE 等台灣股票個股報告的擷取、辨識與資料庫化；VDF 負責金融資料的擷取、清洗、維護與 Parquet、DuckDB、CSV、Google Sheet 輸出；VAP 負責資料理解、自動選圖、視覺化與洞察產生；VPN 則負責檔案、AST、依賴、資產、HTML 與系統健康的全景掃描。VIA 母系統不應重複實作這些業務功能，而應規定它們如何被識別、啟動、連結、監控、驗證、修復與稽核。[1]

![VIA 15 項能力治理閉環](https://private-us-east-1.manuscdn.com/sessionFile/WWiYWCwsrQXodRmwvNyLWK/sandbox/7QIT3Nh1yA690YjNidGbV3-images_1787671574359_na1fn_L2hvbWUvdWJ1bnR1L1Zlcml0YXNBdXRvUGxvdC9WSUFfMTVfQ2FwYWJpbGl0aWVzX0Zsb3c.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvV1dpWVdDd3NyUVhvZFJtd3ZOeUxXSy9zYW5kYm94LzdRSVQzTmgxeUE2OTBZak5pZEdiVjMtaW1hZ2VzXzE3ODc2NzE1NzQzNTlfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwxWmxjbWwwWVhOQmRYUnZVR3h2ZEM5V1NVRmZNVFZmUTJGd1lXSnBiR2wwYVdWelgwWnNiM2MucG5nIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzg5NDMwNDAwfX19XX0_&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEUCID6pVi-9Wf404Sht5Z2hEYaDWfqN3cbL7upq5eiIpjGWAiEAyEO-g-8Lsms4ePvxt-w5WXyTXSx5hKT~kHve2WiGL5I_)

十五項能力可分為四個相互依賴的能力群。**治理與身份群**確保系統知道「誰是誰、什麼才是真實狀態」；**工程標準群**確保所有模組以同一種方式建構與呈現；**執行與整合群**負責跨系統流程和資料交換；**營運與韌性群**則確保系統可觀測、可恢復且可持續運行。

| 能力群 | 包含能力 | 核心問題 |
|---|---|---|
| 治理與身份 | 1 統一身份、2 單一真實來源、4 自動決策、12 統一註冊表 | 系統中的實體如何被識別、記錄與治理？ |
| 工程標準 | 6 統一模板、7 功能模組化、8 視覺一致性 | 新模組如何避免重複建設與規格分歧？ |
| 執行與整合 | 5 流程編排、9 資料連結、10 統一啟動 | 子系統如何依正確順序交換資料並執行？ |
| 營運與韌性 | 3 品質保證、11 統一控制面板、13 統一日誌、14 環境治理、15 自動修復 | 如何知道系統健康、問題在哪裡、能否安全恢復？ |

## 二、共通治理原則

十五項能力必須共享一個標準的執行信封（execution envelope）。任何模組執行、資料集更新、圖表產生、報告入庫、品質檢查或修復動作，都應攜帶相同的追蹤欄位。如此才能讓 SSOT、Registry、日誌、VPN 與控制面板彼此對得起來。

| 建議欄位 | 用途 |
|---|---|
| `schema_version` | 標示事件或紀錄使用的資料契約版本 |
| `event_id` | 本次事件的全域唯一識別碼 |
| `correlation_id` | 串連同一條跨系統流程中的所有事件 |
| `run_id` | 單次管線或工作執行識別碼 |
| `subsystem` | `VRN`、`VDF`、`VAP`、`VPN` 或 `VIA` |
| `module_id` / `asset_id` | 指向統一身份與 Registry 中的對象 |
| `timestamp_utc` | 統一使用 UTC 儲存；介面可轉換為本地時區 |
| `source_ref` / `output_ref` | 輸入、輸出的 URI 或受治理路徑 |
| `content_hash` | 驗證內容是否遭變更並支援重複偵測 |
| `status` | `queued`、`running`、`success`、`warning`、`failed`、`rolled_back` |
| `evidence` | 測試、掃描、日誌、檔案雜湊或驗證報告引用 |

> **責任邊界：** SSOT 保存權威狀態；Registry 保存「有哪些實體及其固定描述」；Log 保存不可變的執行事件；資料庫與 Parquet 保存大量業務資料；控制面板只呈現這些來源，不另造一套狀態。

---

## 1. 統一身份（Unified Identity）

### 定位與目的

統一身份能力解決的是「同一個模組、資料集、報告、圖表或執行工作，在不同子系統中是否仍被認為是同一個對象」。VIA 應透過 **SmartAsset AST + Anchor** 為每一項可治理實體賦予穩定識別碼。識別碼負責跨系統引用；Anchor 則負責在程式碼或文件內精準定位可維護區塊。兩者不可混為一談：`asset_id` 回答「這是什麼」，`anchor_id` 回答「它在內容的哪一個可修改位置」。[1]

| 應納管實體 | 最低身份資訊 | 典型例子 |
|---|---|---|
| 子系統與模組 | `system_id`、`module_id`、版本、入口點 | VRN M07、VDF M01、VAP Chart Engine |
| 資料集與資料表 | `dataset_id`、Schema 版本、來源、內容雜湊 | `index_intl`、`etf_daily`、研究報告資料表 |
| 文件與報告 | `document_id`、股票代碼、報告日期、來源檔案 | 台股個股 PDF、OCR 結果、摘要報告 |
| 視覺資產 | `asset_id`、圖表類型、來源資料引用、參數 | 趨勢圖、資金流圖、估值圖 |
| 執行與事件 | `run_id`、`event_id`、`correlation_id` | 一次 VDF 更新後觸發 VAP 的完整流程 |

### 運作流程與責任邊界

新實體由子系統提出註冊請求，身份服務先做名稱正規化與重複檢查，再生成穩定 ID、內容雜湊與版本資訊，最後寫入 Unified Registry 並在 SSOT 登記目前狀態。子系統不得自行維護另一套永久 ID；暫時性工作 ID 可以由子系統生成，但必須與全域 `run_id` 關聯。

### 治理要求與驗收標準

識別碼一旦發布不得因路徑搬移而改變；資產內容變更時應新增版本而不是覆蓋歷史身份；被淘汰的資產必須標示 `deprecated` 並保留替代關係。驗收時應確認跨 VRN、VDF、VAP、VPN 的相同實體可由單一 ID 查回全部血緣、版本與執行紀錄，且重複 ID 與孤兒資產數量均為零。

---

## 2. 單一真實來源（Single Source of Truth）

### 定位與目的

SSOT 是 VIA 的權威狀態中心，集中管理資產、模組、執行、問題、決策、行動與版本狀態。它不是取代 DuckDB 或 Parquet 的大型資料倉庫，而是保存「目前哪個版本有效、資料在哪裡、誰產生、何時驗證、是否健康」等控制資訊。大量行情、OCR 文字與圖表資料仍保存在專用儲存層，SSOT 保存其引用、Schema、雜湊與狀態。[1]

| SSOT 領域 | 應保存內容 | 不應保存內容 |
|---|---|---|
| 系統狀態 | 子系統版本、健康狀態、最後心跳、啟用狀態 | 完整應用日誌全文 |
| 資產狀態 | 資產 ID、目前版本、來源、位置、雜湊、血緣 | 大型 Parquet 或影像二進位 |
| 執行狀態 | Run、工作階段、開始/結束時間、結果 | 每一筆金融時序資料 |
| 問題治理 | 問題、嚴重度、決策、行動、驗證結果 | 未結構化除錯輸出全集 |
| 組態治理 | 已核准配置版本、環境 Profile、功能旗標 | 明文密鑰與權杖 |

### 運作流程與責任邊界

所有狀態變更必須經由 SSOT API 或受控寫入層，並使用 Schema 驗證、版本檢查與原子交易。讀取可提供快取，但快取失效時必須回到 SSOT。Legacy JSON 可保留為遷移來源或備份，但遷移完成後應轉為唯讀，避免「兩個都能寫」造成狀態分裂。

### 治理要求與驗收標準

SSOT 應具備 Schema 版本、樂觀鎖定或修訂號、完整變更歷史、備份、復原測試與權限分層。驗收標準是：所有生產狀態寫入均可追溯至操作者或自動工作；任一資產可還原至指定版本；故障復原後 Registry、Run 與 Asset 狀態一致；任何子系統不得以本地 JSON 覆蓋母系統權威狀態。

---

## 3. 品質保證（Quality Assurance）

### 定位與目的

品質保證由 VPN M01～M07 全景掃描管線、AST Analyzer、診斷測試與 Repair Commander 共同構成。其目的不是只做語法檢查，而是持續驗證**檔案完整性、程式結構、依賴關係、身份註冊、資料品質、HTML 同步與整體風險**。[1]

| 品質面向 | 主要檢查 | 產生證據 |
|---|---|---|
| 檔案完整性 | 缺檔、重複、錯誤命名、雜湊變更 | File inventory、hash report |
| 程式結構 | Python AST、PowerShell 函式、Anchor 完整性 | AST report、anchor coverage |
| 依賴關係 | 模組依賴、循環依賴、失效入口點 | Dependency graph |
| 資料品質 | Schema、缺值、重複、時間頻率、異常值 | Data profile、quality score |
| 視覺輸出 | HTML 元件、圖表載入、設計令牌、連結完整性 | Render check、UI validation |
| 系統健康 | 服務、資料新鮮度、最後成功執行、資源狀態 | Health snapshot |

### 運作流程與責任邊界

品質檢查應分為提交前、啟動前、執行後與排程巡檢四個關卡。VPN 負責發現與彙整問題；Decision Engine 判斷是否阻擋、警告或進入修復；Repair Commander 只執行已核准的修復計畫。品質系統不得直接修改生產資產而不留下備份、差異與驗證證據。

### 治理要求與驗收標準

每項檢查都應有唯一規則 ID、嚴重度、適用範圍與可重現命令。驗收時，關鍵模組必須通過語法、載入、基本執行與輸出驗證；每個失敗都能對應至資產、Anchor、日誌與修復建議；Quality Gate 的判斷結果必須寫回 SSOT。

---

## 4. 自動決策（Automated Decision）

### 定位與目的

Decision Engine 與 Failure Engine 將原始錯誤轉換為可治理的決策。系統應先將錯誤正規化，再根據影響範圍、嚴重度、可逆性、信心分數與政策，決定忽略、重試、降級、隔離、修復、回滾或要求人工核准。[1]

| 決策等級 | 允許動作 | 典型情境 |
|---|---|---|
| D0 資訊 | 記錄、聚合、趨勢監控 | 非關鍵警告、低風險漂移 |
| D1 自動處理 | 重試、清快取、重建暫存、切換唯讀備援 | 可逆且已知的操作性問題 |
| D2 受控修復 | 套用已核准 Patch、重建索引、回退版本 | 有明確影響範圍與驗證腳本 |
| D3 人工核准 | 修改 SSOT Schema、刪除資料、替換核心模組 | 高風險或不可逆變更 |
| D4 禁止自動化 | 密鑰外洩、資料來源法律問題、未知大規模損壞 | 必須隔離並交由負責人處理 |

### 運作流程與責任邊界

Failure Engine 負責分類與聚合故障，Decision Engine 負責依政策生成決策，Orchestrator 負責執行被核准的行動，VPN 則負責事後驗證。決策紀錄至少需包含輸入證據、規則版本、風險評估、建議動作、核准者、執行結果與回滾結果。

### 治理要求與驗收標準

所有自動決策必須是可重現且可解釋的；同一輸入與同一政策版本應得到相同決策。高風險行動必須具備人工核准點。驗收應透過故障注入案例，確認系統不會因局部錯誤造成跨子系統連鎖破壞，並能在控制面板中呈現完整決策鏈。

---

## 5. 流程編排（Orchestration）

### 定位與目的

Orchestrator 是跨 VRN、VDF、VAP、VPN 的工作調度中心。它需要同時支援串行流程、平行工作、條件分支、重試、超時、取消、續跑與補償動作。其核心不是單純呼叫腳本，而是維持每次執行的狀態機與依賴圖。[1]

| 工作契約欄位 | 說明 |
|---|---|
| `task_id` / `run_id` | 工作定義與單次執行身份 |
| `depends_on` | 上游任務與完成條件 |
| `input_contract` / `output_contract` | 輸入輸出 Schema 或 URI |
| `timeout` / `retry_policy` | 超時、重試次數、退避策略 |
| `idempotency_key` | 確保重跑不會產生重複副作用 |
| `resources` | CPU、記憶體、磁碟、網路需求 |
| `on_failure` | 中止、跳過、降級、回滾或要求核准 |
| `evidence_required` | 任務成功前必須產生的驗證證據 |

### 運作流程與責任邊界

子系統提供可呼叫的標準入口與工作 Manifest；Orchestrator 不理解業務細節，只依契約安排執行。跨系統流程必須以 DAG 表達，例如「VDF 更新成功 → 資料品質通過 → VAP 生成圖表 → VPN 驗證 HTML → SSOT 登記資產」。

### 治理要求與驗收標準

所有工作必須可重入或有補償機制。Orchestrator 應能在程序中斷後從最近成功節點續跑，而不是全部重做。驗收需涵蓋正常流程、上游失敗、逾時、重試、取消、斷電後恢復與重複觸發六類情境。

---

## 6. 統一模板（Unified Template）

### 定位與目的

UltimateTemplate v3 是所有新模組的工程骨架，規定檔頭、模組描述、配置、Anchor、入口點、錯誤處理、日誌、健康檢查與輸出契約。統一模板的價值在於讓 VPN、AST Analyzer、Orchestrator 與自動修復工具可以預測每個模組的結構，而不必為每個腳本建立特例。[1]

| 模板區塊 | 必備內容 |
|---|---|
| Identity | 模組 ID、子系統、版本、擁有者、相容性 |
| Configuration | 環境變數、預設值、Schema 驗證、秘密引用 |
| Anchors | 標準錨點與可修改範圍 |
| Interfaces | CLI、Python API、輸入輸出資料契約 |
| Observability | 結構化日誌、度量、追蹤、健康檢查 |
| Reliability | 超時、重試、冪等、回滾、錯誤碼 |
| Verification | 自我測試、Dry-run、輸出驗證 |
| Registration | Registry Manifest 與 SSOT 註冊掛鉤 |

### 運作流程與責任邊界

建立新模組時，必須先由模板生成骨架，再填入業務區塊；不得直接複製既有模組後任意刪改。模板本身需版本化，舊模組可維持原版本，但必須在 Registry 中標明模板版本與升級路徑。

### 治理要求與驗收標準

驗收應確認新模組不需手動設定即可被 VPN 掃描、被 Registry 辨識、被 Orchestrator 呼叫、被 ModPack E 觀測，並能在錯誤時輸出統一錯誤結構。

---

## 7. 功能模組化（Functional Modularization）

### 定位與目的

ModPack A～F 將跨子系統共用的非業務能力抽離為可插拔模組：A 負責 CPU 加速，B 負責快取與記憶體，C 負責資料序列化，D 負責 HTTP 與網路，E 負責可觀測性，F 負責金融領域共用工具。其目標是避免 VRN、VDF、VAP 各自實作同一套重試、快取、序列化或金融欄位轉換。[1]

| ModPack | 核心責任 | 不應承擔 |
|---|---|---|
| A CPUAccel | 平行計算、批次策略、CPU 能力偵測 | 決定業務結果 |
| B CacheMemory | 快取、TTL、容量、失效策略 | 成為 SSOT |
| C DataSerial | JSON/CSV/Parquet 序列化與 Schema 轉換 | 擅自改變金融語意 |
| D HttpNetwork | HTTP、重試、限流、代理、下載 | 儲存明文密鑰 |
| E Observability | Logging、Metrics、Tracing、Health | 執行高風險修復 |
| F FinanceDomain | Ticker、交易日、財務欄位、頻率轉換 | 與單一資料供應商緊耦合 |

### 運作流程與責任邊界

子系統透過穩定介面引用 ModPack，而不是引用內部函式。每個 ModPack 應公開能力旗標、版本、相容範圍與降級模式。若某一 ModPack 不可用，子系統應能明確失敗或切換受控降級，而不是靜默產生錯誤資料。

### 治理要求與驗收標準

每個 ModPack 必須有獨立測試、效能基準與 API 相容性測試。升級 ModPack 時，需要先在依賴矩陣中評估 VRN、VDF、VAP、VPN 的影響，再以分批方式發佈。

---

## 8. 視覺一致性（Visual Consistency）

### 定位與目的

FusionDashboard 是所有 HTML、圖表、控制面板與報告的統一設計語言。母系統應把色彩、字體、間距、圓角、陰影、狀態色與圖表語意色集中為 Design Tokens，而非散落在各 HTML 與 Python 模組中。Light/Dark 主題應由同一組語意令牌切換，而不是維護兩套獨立樣式。[1]

| 設計層 | 規範內容 |
|---|---|
| Brand | Veritas 徽章、系統名稱、Disciplina / Prudentia / Integritas |
| Semantic Color | 成功、警告、錯誤、資訊、停用、規劃中 |
| Subsystem Color | VRN、VDF、VAP、VPN、SSOT 的固定識別色 |
| Chart Palette | 序列色、正負值、異常值、基準線、事件區間 |
| Typography | 中文、英文、數字、程式碼的字型階層 |
| Components | Card、Table、Tabs、KPI、Badge、Timeline、Alert |
| Accessibility | 對比度、鍵盤操作、色盲辨識、非純色彩提示 |

### 運作流程與責任邊界

Design Tokens 由母系統維護，VAP 負責將其套用到 Plotly 與儀表板；其他子系統只消費 Tokens。任何新色彩或元件都需先進入設計系統版本，再被產品頁面使用。狀態不可只靠顏色表示，還需搭配文字、圖示或形狀。

### 治理要求與驗收標準

驗收應包括 Light/Dark、不同螢幕寬度、表格溢位、中文字型、圖表可讀性與離線開啟測試。任何頁面不得硬編碼未註冊的品牌色；輸出的 HTML 必須保留資產來源、生成時間與版本資訊。

---

## 9. 資料連結（Data Connectivity）

### 定位與目的

資料連結能力負責讓 VDF 的 Parquet、CSV、DuckDB、Google Sheet 成為 VAP 的標準資料來源，並為未來 VRN 結構化報告資料進入 VAP 預留同一套契約。現有 VDFConnector 已承擔檔名解析、目錄掃描、DuckDB 查詢、Google Sheet 讀取與多來源載入；母系統下一步應將這些能力提升為可登記、可驗證、可追蹤的 Data Source Adapter。[1] [2]

| 來源 | 建議角色 | 主要治理要求 |
|---|---|---|
| Parquet | 批次分析的首選交換格式 | Schema、分區、壓縮、內容雜湊、原子寫入 |
| DuckDB | 本地分析查詢與多表整合 | DB 版本、唯讀/讀寫模式、交易、備份 |
| CSV | 相容交換與人工檢視 | UTF-8-SIG、欄位型別、日期格式、引號規則 |
| Google Sheet | 人工協作與外部配置入口 | 工作表 ID、存取權、快取、資料新鮮度、欄位驗證 |
| VRN 結構化資料 | 報告內容與財務敘事來源 | 文件血緣、頁碼/座標、OCR 信心、股票與期間對齊 |

### 運作流程與責任邊界

建議標準流程為：來源發現 → Manifest 解析 → Schema 驗證 → 品質剖析 → 正規化 → 寫入受治理區 → 登記 Dataset Asset → 發布資料可用事件 → VAP 依事件生成圖表。VAP 不應以硬編碼 Windows 絕對路徑尋找最新檔案，而應透過 Dataset Registry 或 Connector 查詢「目前有效版本」。

### 治理要求與驗收標準

所有資料來源需要 `dataset_id`、Schema 版本、時間範圍、Ticker 範圍、更新時間、來源系統、內容雜湊與品質分數。驗收時，同一資料版本重跑應產生相同結果；資料缺欄、時間倒序、重複鍵或部分寫入時，系統必須拒絕發布而不是靜默產圖。

---

## 10. 統一啟動（Unified Launch）

### 定位與目的

SUPREME LAUNCHER 是 VIA 的單一啟動入口。藍圖顯示現有啟動能力已存在，但 v2 尚需完成母系統級整合。它應把環境檢查、組態載入、Registry 同步、SSOT 鎖定、子系統啟動與健康驗證整合為「一鍵完成、失敗可回復」的啟動交易。[1]

| 啟動階段 | 動作 | 失敗處理 |
|---|---|---|
| 1 Preflight | 檢查路徑、磁碟、版本、權限、連接埠 | 立即停止並產生診斷報告 |
| 2 Resolve | 載入環境 Profile、SSOT、Registry、功能旗標 | 不允許使用未知組態啟動 |
| 3 Lock | 建立單例鎖與 Run ID | 避免重複啟動與競態 |
| 4 Start | 依依賴順序啟動服務或批次模組 | 依策略重試或回滾 |
| 5 Verify | 執行健康檢查、資料庫連線與最小測試 | 標記 degraded 或 failed |
| 6 Publish | 寫入 SSOT、開啟控制面板、輸出摘要 | 保留啟動證據與日誌連結 |

### 運作流程與責任邊界

Launcher 只負責啟動與停止，不承擔業務流程編排；跨系統工作由 Orchestrator 負責。Launcher 應支援 `full`、`data-only`、`report-only`、`visual-only`、`diagnostic` 與 `safe-mode` 等 Profile，並提供 Dry-run 顯示將執行的步驟。

### 治理要求與驗收標準

驗收需確認重複點擊不會啟動多份相同服務；部分啟動失敗時能正確停止已啟動元件；啟動摘要清楚列出版本、Profile、健康狀態與控制面板入口；任何密鑰不得出現在命令列或日誌中。

---

## 11. 統一控制面板（Master Control Panel）

### 定位與目的

Master Control Panel 是母系統的觀測與操作介面，但不能成為新的資料真實來源。其畫面資料應來自 SSOT、Unified Registry、結構化日誌、VPN 品質結果與 Orchestrator 狀態。控制面板預設為唯讀；啟動、停止、重跑、修復、回滾等操作需經確認、權限與稽核。[1]

| 儀表板區域 | 必備內容 |
|---|---|
| Executive Overview | 五大子系統健康、資料新鮮度、重大告警、今日執行摘要 |
| Pipeline Monitor | Run、工作節點、進度、依賴、耗時、重試、失敗點 |
| Data Health | VDF 資料表、VRN 報告庫、Schema 漂移、缺口、最新日期 |
| Asset Explorer | 模組、資料集、報告、圖表、版本、血緣、Anchor |
| Quality Center | VPN 掃描分數、問題清單、風險趨勢、驗證證據 |
| Decision & Repair | 決策、核准佇列、修復計畫、差異、回滾狀態 |
| Operations | Launcher Profile、服務狀態、排程、資源、環境漂移 |

### 運作流程與責任邊界

介面使用事件或受控 API 讀取狀態，不應直接掃描整個磁碟或修改 JSON。操作型按鈕只建立 Command，Command 由 Decision Engine、Orchestrator 或 Repair Commander 執行，UI 再顯示結果。這種分離可避免瀏覽器操作直接破壞生產檔案。

### 治理要求與驗收標準

控制面板需有角色權限、操作確認、稽核軌跡、錯誤回饋與資料更新時間。驗收時，畫面中的狀態必須能追溯至來源紀錄；任何控制動作都能取得 Command ID、執行人、前後狀態與結果證據。

---

## 12. 統一註冊表（Unified Registry）

### 定位與目的

Unified Registry 是 VIA 的「全局目錄」，將目前分散的 Asset Registry、Tool Registry、Anchor Registry、Module Registry 與 Dataset Catalog 透過共同主鍵和 Schema 整合。Registry 與 SSOT 的差異是：Registry 說明「有哪些對象、它們是什麼、如何定位」，SSOT 說明「它們現在處於什麼狀態」。藍圖顯示各類註冊表已存在，但全局整合仍屬規劃項目。[1]

| Registry 類型 | 主要內容 |
|---|---|
| Module Registry | 模組 ID、入口、版本、模板、依賴、能力 |
| Asset Registry | 報告、圖表、輸出檔、內容雜湊、父子關係 |
| Dataset Registry | Schema、分區、時間範圍、Ticker、位置、品質 |
| Tool Registry | 可用工具、參數、執行環境、風險等級 |
| Anchor Registry | Anchor 名稱空間、所在檔案、區塊、版本 |
| Service Registry | API、健康端點、連接埠、啟動方式、相依服務 |

### 運作流程與責任邊界

整合程序應採「匯入 → 正規化 → 去重 → 衝突報告 → 人工或規則合併 → 發布」方式，不直接覆蓋原始 Registry。統一後，舊註冊表可作為子系統投影輸出，但全域查詢以 Unified Registry 為準。

### 治理要求與驗收標準

Registry Schema 必須版本化，並支援唯一性、引用完整性與循環依賴檢查。驗收時，任一模組或資產可從 ID 找到所在路徑、版本、上游、下游、擁有者、健康狀態與最近執行；所有失效路徑和孤兒引用都應被 VPN 偵測。

---

## 13. 統一日誌（Unified Logging）

### 定位與目的

統一日誌由 `_logs` 目錄與 ModPack E Observability 提供。其目的不是把所有文字輸出堆到同一個檔案，而是讓每一條事件都具備一致的時間、層級、子系統、模組、Run、Correlation、錯誤碼與資產引用，從而支援跨系統追蹤。[1]

| 欄位 | 說明 |
|---|---|
| `timestamp_utc` | UTC 時間，毫秒精度 |
| `level` | DEBUG、INFO、WARNING、ERROR、CRITICAL |
| `subsystem` / `module_id` | 事件來源 |
| `run_id` / `correlation_id` | 單次執行與跨系統追蹤 |
| `event_code` | 穩定的事件或錯誤代碼 |
| `message` | 人類可讀摘要 |
| `context` | 結構化參數，不含秘密 |
| `asset_id` / `dataset_id` | 受影響對象 |
| `evidence_ref` | 報告、堆疊、截圖或測試結果位置 |

### 運作流程與責任邊界

模組透過 ModPack E 發送結構化事件；本地檔案可作為落地介質，之後再由聚合器建立索引與統計。日誌、Metrics 與 Traces 應共享 Correlation ID。使用者輸入、API Token、Cookie、帳號與完整文件內容需經遮罩或禁止寫入。

### 治理要求與驗收標準

日誌應具備輪替、保留期限、壓縮、存取權限與完整性檢查。驗收時，從控制面板點選一次失敗 Run，應能直接串回 VDF 下載、VAP 產圖、VPN 驗證與修復決策的全部事件，而不需人工比對時間戳。

---

## 14. 環境治理（Environment Governance）

### 定位與目的

CoreEnvGovernance 管理 Python、PowerShell、Node、DuckDB、瀏覽器與套件版本，以及目錄、權限、連接埠、代理與硬體能力。它要防止「在某台電腦可以跑，在另一台不能跑」的環境漂移，並為 Launcher 與 Repair Commander 提供可驗證的基準。[1]

| 治理項目 | 建議控制 |
|---|---|
| Runtime | Python、PowerShell、Node、瀏覽器版本矩陣 |
| Dependencies | 鎖定檔、雜湊、允許來源、離線快取 |
| Paths | `VIA_ROOT` 與相對路徑解析，避免散落絕對路徑 |
| Configuration | dev/test/prod Profile、Schema、預設值與覆寫順序 |
| Secrets | 環境變數或秘密儲存，只保存引用，不寫入 SSOT 明文 |
| Resources | CPU、RAM、磁碟空間、GPU、網路能力與配額 |
| Compatibility | 子系統、模板、ModPack、Schema 的相容矩陣 |

### 運作流程與責任邊界

每次啟動先產生 Environment Snapshot，與核准基準比對；差異分類為允許、警告或阻擋。環境治理只報告與套用被核准的配置，不應在未告知情況下自動升級核心套件。

### 治理要求與驗收標準

驗收需在乾淨環境執行安裝、啟動、測試與移除；同一 Profile 的關鍵版本與行為必須可重現。任何依賴變更都需產生差異報告與回退方式；生產環境禁止浮動版本。

---

## 15. 自動修復（Automated Repair）

### 定位與目的

EnvFix 與 Repair Commander 提供修復能力。必須區分「已有一鍵環境修復工具」與「完整跨系統自動復原管線」：前者可視為既有能力，後者仍需將 Failure Engine、Decision Engine、Anchor Patcher、備份、驗證與回滾完整串接。這也是藍圖中能力狀態與 Roadmap 之間需要明確說明的地方。[1]

| 修復等級 | 自動化程度 | 例子 |
|---|---|---|
| R0 建議 | 僅提供診斷與命令 | 未知錯誤、核心 Schema 衝突 |
| R1 安全自動 | 可逆、無業務資料損失 | 清理暫存、重建快取、建立缺失目錄 |
| R2 受控自動 | 需快照與驗證 | 重新建立索引、回退已知版本、修復 Anchor 區塊 |
| R3 人工核准 | 高影響或可能改變資料 | 修改核心程式、資料遷移、Registry 衝突合併 |
| R4 禁止 | 不允許自動化 | 刪除無備份資料、繞過安全控制、替換未知來源程式 |

### 運作流程與責任邊界

標準修復流程是：診斷 → 建立修復計畫 → 影響分析 → 備份或快照 → Dry-run → 核准 → 套用 → VPN 驗證 → 更新 SSOT → 成功結案或回滾。Repair Commander 不自行決定政策，Decision Engine 決定是否允許；Anchor 系統限定可修改範圍；VPN 提供前後比較與驗證證據。

### 治理要求與驗收標準

任何修復都必須保留原始檔、Patch、前後雜湊、操作者、政策版本與驗證結果。驗收應使用可控制的故障注入測試，確認修復失敗時能回復原狀，且不會因重複執行而持續修改同一資產。

---

## 三、十五項能力如何形成治理閉環

完整閉環應從 Launcher 與環境治理開始，由 Orchestrator 啟動子系統工作；資料透過 Connector 流動並寫入專用儲存；Identity 與 Registry 記錄產出的模組、資料集、報告和圖表；SSOT 保存其權威狀態；統一日誌與 VPN 蒐集執行證據；Decision Engine 根據品質結果產生決策；Repair Commander 套用可控修復；最後再次由 VPN 驗證並將結果呈現在 Master Control Panel。

| 階段 | 主要能力 | 主要輸出 |
|---|---|---|
| 準備 | 10 統一啟動、14 環境治理 | Environment Snapshot、Run ID、啟動計畫 |
| 執行 | 5 流程編排、6 統一模板、7 功能模組化 | 任務狀態、標準化輸出、執行證據 |
| 交換 | 9 資料連結 | Dataset Manifest、Schema 驗證、資料版本 |
| 登記 | 1 統一身份、2 SSOT、12 統一註冊表 | Asset ID、權威狀態、血緣、版本 |
| 觀測 | 3 品質保證、13 統一日誌 | Quality Report、Issue、Trace、健康分數 |
| 決策與復原 | 4 自動決策、15 自動修復 | Decision、Repair Plan、Patch、Rollback |
| 呈現 | 8 視覺一致性、11 統一控制面板 | 一致的健康與治理介面 |

## 四、現況判讀：已存在不等於已達生產級

依母系統藍圖，十五項能力中大多已有對應元件；然而「檔案存在」與「母系統級能力完成」應分開評估。尤其統一啟動、統一控制面板與統一註冊表仍明確列為規劃中。自動修復雖有 EnvFix 與 Repair Commander，但完整的跨系統 Error Recovery Pipeline 仍需工程整合。[1]

| 能力 | 藍圖現況 | 建議成熟度判讀 |
|---|---|---|
| 1 統一身份 | 已有 SmartAsset AST + Anchor | **已具基礎**；需統一 ID API、唯一性與血緣驗證 |
| 2 SSOT | 已有 SSOT Engine | **已具基礎**；需交易、Schema 遷移、備份復原測試 |
| 3 品質保證 | 已有 VPN M01~M07 | **已具主要管線**；需建立品質閘門與自動化測試證據 |
| 4 自動決策 | 已有 Decision + Failure Engine | **已具引擎**；需政策版本、人機核准與故障注入測試 |
| 5 流程編排 | 已有 Orchestrator | **已具引擎**；需 DAG 狀態、冪等、續跑與補償驗證 |
| 6 統一模板 | 已有 UltimateTemplate v3 | **已具標準**；需模板合規掃描與升級機制 |
| 7 功能模組化 | 已有 ModPack A~F | **已具模組**；需 API 相容性與依賴矩陣 |
| 8 視覺一致性 | 已有 FusionDashboard | **已具風格**；需集中 Design Tokens 與自動 UI 驗證 |
| 9 資料連結 | 已有 VDFConnector | **VDF→VAP 已具基礎**；VRN→VAP 尚需資料契約 |
| 10 統一啟動 | Launcher v1；v2 規劃中 | **部分完成**；需交易式啟動、Profile、回滾、健康驗證 |
| 11 統一控制面板 | 規劃中 | **尚待建構**；應以 SSOT/Registry/Event API 為資料源 |
| 12 統一註冊表 | 多個分散 Registry；整合規劃中 | **部分完成**；需共同 Schema、去重與全局查詢 |
| 13 統一日誌 | `_logs` + ModPack E | **已具基礎**；需統一事件 Schema、Correlation 與遮罩 |
| 14 環境治理 | CoreEnvGovernance | **已具工具**；需鎖定版本、環境快照與漂移政策 |
| 15 自動修復 | EnvFix + Repair Commander | **局部完成**；需完整診斷—核准—驗證—回滾閉環 |

## 五、建置優先序

建議不要先做外觀漂亮但資料源不一致的控制面板。第一階段應先穩定身份、SSOT、Registry、事件日誌與資料契約；第二階段再完成 Orchestrator、Connector 與 Launcher；第三階段建立品質閘門、決策與修復閉環；最後才讓 Master Control Panel 成為可信的母系統入口。

| 優先級 | 能力 | 交付重點 | 完成定義 |
|---|---|---|---|
| P0 治理基座 | 1、2、6、12、13、14 | ID、SSOT、模板、Registry、Log、Environment Schema | 所有模組可被唯一識別、查詢、追蹤與重現 |
| P1 執行骨幹 | 5、7、9、10 | Orchestrator、ModPack、Connector、Launcher v2 | VDF→VAP 與 VRN 工作可一鍵、安全、可續跑地執行 |
| P2 品質與韌性 | 3、4、15 | VPN Gate、Decision Policy、Repair Pipeline | 故障可被發現、分類、核准、修復、驗證與回滾 |
| P3 操作體驗 | 8、11 | Design Tokens、Master Control Panel | 介面所示狀態完全來自治理來源且操作可稽核 |

## 六、母系統級驗收矩陣

| 驗收領域 | 最低通過條件 | 證據 |
|---|---|---|
| 身份完整性 | 無重複 ID、無孤兒資產、所有 Anchor 可定位 | Registry integrity report |
| 狀態一致性 | SSOT 與各子系統投影無未解決差異 | SSOT reconciliation report |
| 資料血緣 | 任一 VAP 圖表可追溯至 VDF/VRN 原始來源與版本 | Lineage graph、hash chain |
| 執行可靠性 | 工作可重跑、續跑、取消；重複觸發不產生重複副作用 | Orchestrator scenario tests |
| 品質閘門 | 關鍵錯誤會阻擋發布，警告有政策與責任人 | VPN gate report |
| 可觀測性 | 任一跨系統 Run 可透過 Correlation ID 完整追蹤 | Structured log trace |
| 環境可重現 | 乾淨環境可依鎖定配置完成安裝、啟動與測試 | Environment snapshot、install test |
| 修復安全性 | 修復具備 Dry-run、備份、差異、驗證與回滾 | Repair evidence bundle |
| 介面可信度 | 控制面板的狀態均可連回 SSOT、Registry 或 Log | UI source mapping test |
| 安全與稽核 | 秘密不落盤於日誌；高風險操作有核准與稽核 | Secret scan、audit report |

## 七、建議的三個近期工程里程碑

### 里程碑 A：VIA Governance Contract v1

先凍結 `asset_id`、`module_id`、`dataset_id`、`run_id`、事件信封、SSOT 核心 Schema 與 Registry Schema。同步建立驗證器，讓 VRN、VDF、VAP、VPN 的每個輸出都可自動檢查。這一里程碑完成後，母系統才真正擁有一致語言。

### 里程碑 B：SUPREME LAUNCHER v2 + Orchestrator Runtime

完成 Preflight、Profile、單例鎖、依賴順序、健康檢查、Dry-run、Resume 與 Rollback。以兩條真實流程驗收：第一條是 VDF 更新後自動觸發 VAP；第二條是 VRN 報告處理完成後登記 Asset、寫入資料庫並觸發 VPN 驗證。

### 里程碑 C：Unified Registry + Master Control Panel

先合併分散 Registry，再建控制面板。控制面板第一版以唯讀為主，提供系統健康、Run、資料新鮮度、資產血緣、問題與決策檢視；待命令與權限模型穩定後，再加入啟動、重跑、核准修復與回滾操作。

## 八、結論

VIA 母系統的十五項能力是一個不可任意拆散的治理閉環。**統一身份**提供可追蹤的對象；**SSOT 與 Registry**建立權威資料；**模板、ModPack 與設計語言**建立工程一致性；**Orchestrator、Connector 與 Launcher**讓子系統可靠協作；**日誌、VPN、Decision 與 Repair**提供可觀測與可恢復能力；最後由 **Master Control Panel**把真實狀態呈現給使用者。

最重要的架構原則是：**先建立契約與證據，再增加自動化；先確保可回滾，再允許自動修復；先讓控制面板可信，再讓它具有控制權。** 如此 VIA 才能從工具集合升級為真正可治理、可驗證、可擴展的金融智慧母系統。

## References

[1]: ./VIA_MasterArchitecture.html "VIA Master Architecture — Veritas Intelligence Analytics"
[2]: ./VIA_Ecosystem_Architecture.html "VIA Ecosystem Architecture — Integration Matrix and Data Flow"
