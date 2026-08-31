# VIA 系統詳細交接報告(操作員交付正典;批177 原文照錄零改寫)
> 收容註記:操作員 2026-08-26 交付;證據基準=2026-08-13~08-18 工作站側治理紀錄。
> 雲端側逐項實測對照=VIA_Handover_Gap_Register_v0100.json(六態;NOT_ACTIVATED 遵狀態機)。

---

VIA 系統詳細交接報告

VIA Central Governance Console · Supportive Modules · VDF · VRN · VAP

def 文件類型：系統交接報告（Handover Report）
def 系統名稱：Veritas Intelligence Analytics
def 交接範圍：中央治理控制台、共用支援模組、資料工程、報告解析、視覺分析
def 證據基準：現有附件與 2026-08-13 至 2026-08-18 的治理紀錄
def 重要限制：本報告中的「狀態」是文件證據狀態，不代表 2026-08-27 當下已完成正式啟用

⸻

def 01 · 執行摘要

VIA 採用「中央控制平面＋共用基礎能力＋領域子系統」架構：

* VIA Central Governance Console 決定系統是否可掃描、測試、修補、整合、晉級或啟用。
* Supportive Modules 提供 SSOT、註冊、環境治理、網路韌性、運算加速與 Runtime Bridge。
* VRN 把券商報告、PDF、圖片、表格與文字轉成可驗證的結構化資料。
* VDF 擷取、清洗、標準化、儲存並更新台股、全球市場、總體、財報、籌碼與 ETF 資料。
* VAP 將已通過資料契約與品質驗證的結果轉成圖表、儀表板、HTML、PNG 與 PDF。

整個系統最重要的責任分界是：

中央治理決定能不能做；Supportive Modules 決定如何安全地做；VRN 與 VDF 生產證據；VAP 呈現證據。

任何子系統不得自行宣告為正式啟用，也不得用「已找到檔案、AST 通過、Staging Ready、Contract Pass」取代真實資料、整合、使用者測試與正式啟用。

2026-08-17 的完整治理計畫把整體狀態記為 HOLD_REMEDIATION_REQUIRED，啟用狀態為 NOT_ACTIVATED；其狀態鏈要求從 FILE_DISCOVERED 一路通過到 POST_ACTIVATION_STABLE，前一狀態不能自動推導後一狀態。 VIA_Central_Governance_Complete_Execution_Plan_20260817.md

⸻

def 02 · 系統總體架構

外部資料來源／使用者文件
        │
        ├── PDF／Word／HTML／圖片／券商報告
        │                       │
        │                       ▼
        │                 VRN 文件解析層
        │         Converter → Layout → OCR → Table
        │         → Normalize → Validate → Summarize
        │                       │
        │                       ▼
        ├── TWSE／TPEX／MOPS／YFinance／總體資料來源
        │                       │
        │                       ▼
        │                 VDF 資料工程層
        │         Fetch → Normalize → Validate → Store
        │         → Incremental Update → Dataset Contract
        │                       │
        └───────────────────────┤
                                ▼
                    Central SSOT／Registry
                                │
                     Schema／Hash／Evidence
                                │
                                ▼
                       VAP 視覺呈現層
                 Chart／Dashboard／HTML／PNG／PDF
                                │
                                ▼
                 VIA Central Governance Console
             Audit → Stage → Promote → Monitor／Rollback

def 子系統責任矩陣

層級	子系統	主要責任	不應承擔的責任
控制平面	VIA Central Governance	Root 仲裁、SSOT、Registry、Gate、測試、核准、回滾、證據	不直接實作財務計算、OCR 或圖表邏輯
共用基礎	Supportive Modules	環境、網路、加速、註冊、規則、Runtime Context	不擁有 VDF／VRN／VAP 的業務語意
文件資料	VRN	PDF、OCR、表格、文字、基本資料與財務資料抽取	不自行定義市場資料真實來源
市場資料	VDF	擷取、標準化、更新、儲存、資料品質與資料集	不自行決定正式啟用，不在圖表層修改數據
呈現層	VAP	視覺契約、圖表、儀表板、輸出與互動	不重新計算或靜默修正上游資料

既有盤點把 VAP 定義為 visual analytics/presentation layer、VRN 定義為 report/PDF→I/O extraction、VDF 定義為 data forge database/fetch/normalize。 VIS_REVIEW_ALL_MATRICES_v0100.json

⸻

def 03 · VIA Central Governance Console

def 03.1 · 系統定位

VIA Central Governance Console 是整套 VIA 的唯一控制平面與權限入口。其權威來源為：

* Central SSOT Registry
* Synonym／Regex Governance
* Module Registry
* Schema／Contract Registry
* Gate Evidence
* Expected Hash
* Checkpoint／Rollback Evidence
* Approval Token

中央治理的預設模式為 AUDIT，允許模式為：

模式	行為
AUDIT	唯讀盤點、AST、契約、資料品質與風險檢查
STAGE	在獨立 Staging／Sandbox 建立候選版本，不覆寫 Canonical
PROMOTE	只有在 Token、Expected Hash、Checkpoint、Rollback 與所有 Gate 通過時才能晉級

治理文件明定 Central Governance 是 SSOT controller 與 subsystem entry；2026-08-13 的 Integration Gate 雖為 Ready for Staging，但明確註明沒有自動啟用，也沒有修改來源。 貼上的 Markdown (1).md

def 03.2 · 中央治理的核心功能

def A · Root 與權威仲裁

中央治理必須先判定哪一個目錄才是 Canonical Root。已記錄的候選包括：

* C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics
* C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics

任何 OneDrive 路徑不得直接作為 Mother Root 或 Active Runtime；最多只能作為唯讀來源候選，先複製至本機 Staging，再比對 Hash。Root 仲裁需要 Manifest、Owner ID、Git HEAD、Registry Path、核心治理資源 Hash Set、環境快照與不同 Root 的 AST／Token Diff。 VIA_Central_Governance_Complete_Execution_Plan_20260817.md

def B · 全景式掃描

中央治理應掃描：

* Python AST
* PowerShell AST
* JavaScript Parser
* JSON／YAML／TOML Contract
* Import／Dependency Graph
* Duplicate／Semantic Duplicate
* Hard-coded Path
* Encoding
* Forbidden API
* Import-time Side Effect
* Shared-write Risk
* Hydra Risk
* Missing／Divergent Variant
* UI Overflow／Wrap／Viewport

現有 Dashboard 包含執行分析、工具矩陣、LEGO 20-CMD、智慧登錄、ETS 工具台、Smart Engine 與 Checklist，並包含 AST Call Graph、Dependency Engine 與 Semantic Duplicate Engine 等功能。 VPN_v35_Dashboard (3).html

def C · 三輪修補治理

輪次	處理內容	限制
Round 1	全面盤點與 Parallel-Safe 修補	不碰共享權威與 Hydra 高風險節點
Round 2	依依賴拓樸排序修補	先 SSOT、Registry、Environment、Contract，再修領域模組
Round 3	微調、清理、格式與穩定化	不得加入新的架構性改寫

最大輪次固定為三輪，超過三輪必須轉為 HOLD，避免在同一次執行中持續修改系統。

def 03.3 · Gate 架構

def 全系統 T0–T9

Gate	驗證內容
T0	Root、Owner、Manifest、Hash、Canonical Identity
T1	Python／PS／JS Native AST 與靜態安全
T2	JSON／YAML Schema、參數、Boolean、Null、Encoding、Path Contract
T3	真實資料唯讀存取、Row Count、Grain、Freshness
T4	Duplicate、Null、Ticker、Date、OHLC、Adjustment、Cross-Source
T5	Unit、Dataset、Regression、Failure Injection
T6	六流程／十二通道整合、隔離、Exit Code、Hash
T7	使用者測試、數值、Viewport、HTML／PNG／PDF
T8	Approval Token、Expected Hash、Checkpoint、Rollback
T9	啟用後 Heartbeat、錯誤率、資源、資料新鮮度與回歸測試

每一個子系統另有 S01–S12 獨立 Gate；不得用 VAP 的 PASS 抵銷 VDF 的 FAIL，也不得用 VRN 的 AST PASS 抵銷 VRN 的資料品質問題。 VIA_Central_Governance_Complete_Execution_Plan_20260817.md

def 03.4 · Console 輸入與輸出

def 輸入

* Mother Root 與 Candidate Roots
* Run Mode
* Run ID
* Python Environment Alias
* StartDate／EndDate
* UpdateMode
* Retry
* MaxRounds
* Lane Timeout
* Approval Token
* Expected Registry SHA-256
* Expected Plan SHA-256

def 輸出

* HTML UI Matrix
* JSON Evidence
* CSV Matrix
* Markdown Summary
* Log／JSONL History
* Patch Proposal
* Checkpoint
* Hash Chain
* Rollback Plan
* Activation Decision

⸻

def 04 · Supportive Modules 詳細交接

Supportive Modules 是共用基礎能力層。正確做法不是讓每個 VDF、VRN 或 VAP 模組自行重複 import、建立執行緒池、管理代理伺服器或決定環境，而是由共用 Runtime Context 統一供應。

def 04.1 · Supportive Module 責任表

模組	主要責任	主要輸入	主要輸出
VIA_SSOT_Unified.py	Regex、Synonym、Alias、Canonical Naming、規則查詢	名稱、Ticker、日期、程式碼、資產內容	正規化值、規則命中、Violation、Asset JSON
VIA_RegistryCore_v1.py	Append-only 模組註冊、Identity、Dependency、Environment Route	模組檔案、Manifest、Capability Map	Registry JSON、History JSONL、HTML Report
VIA_EnvManager.py	venv 掃描、套件健康、衝突、安裝決策與修復計畫	Environment Root、Alias、Route、Package Request	Health、Conflict、Install Plan、HTML
VeritasAegisNexus.py	網路韌性、Rate Limit、Retry、Circuit Breaker、Cache、Failover	URL、Headers、來源政策	Response、Fetch Evidence、Cache、Failure Status
VeritasCeleritas.py	CPU／RAM／Thread Budget、Batch、Map、Cache、Compression	Workload、Items、Resource State	Accelerated Result、KPI、Status Report
VIA_Runtime_Bridge_All_in_One.py	將核心模組掛入共享 ctx	Task、Payload、Runtime Config	Runtime State、Task Result、Error Evidence
VIA_Panorama_AST_RuntimeInjector.py	Python AST、Compile、靜態盤點與 Patch Plan	Base Root	JSON／HTML Patch Plan、Summary

def 04.2 · VIA_SSOT_Unified

SSOT 是命名與規則的唯一真實來源，提供三類介面：

1. 一般函式：normalize、extract、contains
2. 單例鏈式介面：get_ssot()
3. 智慧資產介面：asset_dump、asset_load、asset_patch

現有語料涵蓋台股代碼、Yahoo Ticker、Bloomberg Ticker、日期格式、財務空值、財報標題、檔案路徑、版本、模組碼、Anchor、風險碼與 HTML 結構。 VIA_SSOT_Unified.py

def 交接要求

* 所有 Ticker Regex 只能由 SSOT 擁有。
* VRN、VDF、VAP 不得各自維護不同版本 Regex。
* 規則更新採 append-only。
* 舊規則標為 deprecated，不直接刪除。
* 每次規則變更需附範例、版本、Owner 與測試。

def 04.3 · VIA Registry Core

Registry Core 負責：

* 模組掃描與註冊
* IAIC／AST／5D Identity
* 模組版本與 Hash
* Capabilities
* Dependencies
* Environment Alias
* Entry Callable
* Append-only 歷史
* Latest Record 判定
* 執行紀錄

Registry 設計明確要求 append-only，不覆蓋歷史，並將模組解析、環境路由與執行入口集中治理。 VIA_RegistryCore_v1.py

def 交接風險

目前上傳版本仍存在 /mnt/data/... 與特定舊檔名候選路徑。這些路徑只能視為開發或匯入候選，不能直接作為正式 Registry Authority。正式啟用前必須由 Root Arbitration 重綁至 Canonical Root。

def 04.4 · VIA EnvManager

EnvManager 負責：

* 探索 base、via_*、Paddle、Camelot 等環境
* 檢查 python.exe、pyvenv.cfg
* 執行 pip check／uv pip check
* 盤點核心套件
* 分類 High／Medium／Low Risk Libraries
* 檢查 base 與 via_* 的高風險套件重疊
* 建立安裝或重建計畫
* 輸出環境健康與衝突報告

其輸出包含 SSOT JSON、Health JSON、Conflict JSON、Command Plan、Install Request、JSONL History 與 HTML Report。 VIA_EnvManager.py

def 交接原則

* 新套件不能直接安裝進任意環境。
* 必須先提交 Install Request。
* 高風險套件原則上隔離於專用環境。
* via_core 只保留治理與通用資料能力。
* paddleocr、TensorFlow、Torch、Camelot、Playwright 等不得未經 Gate 混入 base。
* 修復命令只可先產生 Proposal，不應立即執行刪除或重建。

def 04.5 · VeritasAegisNexus

Aegis 是網路與外部資料來源保護層，包含：

* User-Agent 管理
* Headers Builder
* Proxy Pool
* Exponential Backoff
* Circuit Breaker
* Sync／Async HTTP
* 429／503 Retry
* Rate Limiter
* Cache
* 多來源 Failover
* YFinance Shield
* TWSE／TPEX 資料來源
* DuckDB Type Guard
* SQLite HTTP Cache
* Robots／Compliance Policy

其主要任務是讓 VDF 與 VRN 不需要自行重複實作網路重試、限流與快取。 VeritasAegisNexus.py

def 重要上線阻擋

在已提供版本的 HttpConfig 中可看到 verify_ssl=False 的預設值。除非後續 Canonical 版本已有中央契約覆寫與測試證據，否則正式環境應將此視為安全阻擋，不得直接啟用。

def 04.6 · VeritasCeleritas

Celeritas 是運算資源與效能治理層，涵蓋：

* CPU／Physical Core 偵測
* RAM Pressure
* Thread Budget
* Adaptive Chunk
* Batch Processing
* Thread／Process／Joblib／Ray／Dask 路由
* Lazy Import
* LRU／TTL／SQLite Cache
* Polars-first DataFrame
* JSON Accelerator
* Compression
* Hashing
* GC Tuner
* Memory Pool
* xmap、xbatch、xfetch、xcache
* Self-test 與 Status Report

引擎明確列出 CPU、RAM、Thread Budget、Memory Pool、Adaptive Chunk、Parallel Engines、Cache、DataFrame、JSON、Compression 與 Cross-Acceleration 等能力。 VeritasCeleritas.py

def 交接限制

* Celeritas 可以決定執行方式，不能改變財務或資料語意。
* 資源壓力降級時必須記錄，不可靜默變更結果。
* 自動初始化、Warm Pool 與 import-time 行為必須受中央 Gate 控制。
* 在 AST Gate 前，不應因 import Celeritas 而啟動執行緒池或修改環境變數。

def 04.7 · Runtime Bridge

Runtime Bridge 將 EnvManager、Registry、SSOT、Aegis、Celeritas 掛載到共用 def_VIARuntimeContext，讓任務使用統一的：

def def_task(ctx, ...)

它負責 Bootstrap、Registry Resolve、Environment Install Plan、Accelerated Batch／Map、Task Wrapper 與 Self-test。 VIA_Runtime_Bridge_All_in_One.py

def 目前重大路徑風險

上傳版本的 def_PARAM_SUPPORTIVE_ROOT 指向 OneDrive：

C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module

這與「OneDrive 不得作為 Active Root」的治理政策衝突。正式交接時應改為由 Central Governance 注入 Canonical Root，不應讓 Runtime Bridge 保留單一硬編碼權威路徑。

def 04.8 · Panorama AST Runtime Injector

此模組可以：

* 讀取 Python
* ast.parse
* compile
* py_compile
* 列出 Functions
* 找出 Main Guard
* 產生 JSON／HTML Patch Plan

但對 .ps1、.json、.md、.html 等檔案，目前只做 Index，沒有完整 Native Parser 驗證。 VIA_Panorama_AST_RuntimeInjector.py

因此不得把這個工具單獨的 PASS 稱為完整 Polyglot AST PASS；PowerShell 與 JavaScript 必須使用各自的 Native Parser。

⸻

def 05 · VDF：VeritasDataForge 詳細交接

def 05.1 · 系統定位

VDF 是 VIA 的資料基礎層，負責把外部市場資料轉成：

* 可重跑
* 可增量更新
* 可追溯
* 可驗證
* 可由 DuckDB 查詢
* 可輸出 Parquet／CSV
* 可供 VRN Cross-validation
* 可供 VAP 視覺化

def 05.2 · 主要模組

現有資產盤點包含：

模組	主要功能
VDF_MDL001_TWEquityEngine	台股價格、交易與基礎資料
VDF_MDL002_YFinanceFetchingEngine	Yahoo Finance 全球價格與補充資料
VDF_MDL003_SentimentMacroEngine	情緒與總體資料
VDF_MDL004_TWFullMarketEngine	台股全市場資料
VDF_MDL005_TWStockFilter	股票清單與篩選
VDF_MDL006_FinancialModel	財務模型與計算
VDF_MDL007_SSOTResolver	VDF 與 SSOT 的欄位／名稱解析

上述模組名稱可在系統盤點中看到，同時也顯示 VAP Scope Copy 內存在 VDF 與 VRN 副本，因此必須透過 Registry 判定唯一權威來源。 貼上的 Markdown (1).md

def 05.3 · VDF 資料範圍

def 台股

* 上市／上櫃股票清單
* Adj Open／High／Low／Close
* Volume／Turnover／Market Cap
* 三大法人
* 外資持股率
* 融資／融券
* 券資比
* 當沖
* 月營收
* 單季／累計／年度財報
* 主動式 ETF 每日持股
* 台股 ETF 規模與資金流

def 全球市場

* 全球股票
* 股票指數
* ETF
* 匯率
* 利率
* 商品
* 航運
* 跨資產風險

def 總體經濟

* 通膨
* 就業
* 勞參率
* 收入
* 零售
* 進出口
* 財政收支
* PMI
* GDP 與支出法構成
* 官方政策利率
* 跨區域利差

def 05.4 · 資料處理規則

* 先檢查現有資料，再增量擷取。
* Grain 必須明確，例如 Date + Ticker。
* 所有資料需去重。
* 中斷後可 Resume。
* 每一來源保留 Source、As-of Date、Fetch Time 與 Proxy／Derived 標誌。
* Adjusted Price 與原始 Price 不得混用。
* 成交量不可用前值補齊。
* 空白價格若採前值處理，必須標記 Imputation。
* 下游不能把 Proxy 或 Derived 資料洗成 Actual。
* CSV 使用可驗證的 UTF-8 編碼。
* Parquet 與 DuckDB Schema 必須有版本。

def 05.5 · VDF 與 VRN 的關係

VRN 從券商報告抽取：

* 目標價
* 評等
* EPS
* 財報數值
* 敘述
* 預估

VDF 提供：

* 官方財報
* 市價
* 調整後價格
* YFinance 補充
* 市場與總體資料

兩者透過 CrossValidator 比對後，才能產生 Confidence、Mismatch Class 與 Evidence。VRN 不應直接把券商預估當成官方事實，VDF 也不應覆寫報告原文。

def 05.6 · 文件基準狀態與阻擋

2026-08-17 的治理證據記錄：

* v0140A：CONTRACT_ONLY_PASS
* v0140B：HOLD_REMEDIATION_REQUIRED
* v0140B R06：1,871 筆資料中有 205 筆 OHLC 一致性問題
* v0161：因 OpenHtml 型別、Null／Empty Supported 與 Exit Code 3 失敗
* v0162：Static 與 Focused Regression 已通過，但仍等待真實參數 E2E 重跑

因此，VDF 不能僅因部分模組標示 AUTHORITATIVE_ACTIVE 就視為整體已完成正式資料啟用。 VIA_Central_Governance_Complete_Execution_Plan_20260817.md

⸻

def 06 · VRN：VeritasReportNova 詳細交接

def 06.1 · 系統定位

VRN 是報告與非結構化文件解析系統，負責：

* 將不同格式轉成標準 PDF
* 判斷頁面類型與版面
* 決定是否需要 OCR
* 抽取財務表格
* 擷取公司與報告基本資料
* 分析文字敘述
* 標準化財務欄位
* 產生摘要
* 與外部資料交叉驗證
* 保留 Confidence 與 Evidence

def 06.2 · 功能管線

階段	模組	輸入	輸出
M01	Unified PDF Converter	PDF／圖片／HTML／文字	標準化高品質 PDF
M02	Page／Layout Classifier	標準 PDF	Page Map、Layout、Table Region
M03	OCR Engine／Table Restorer	需 OCR 頁面、Layout	OCR JSON、修復後文字／表格
M04	Financial Table Extractor	OCR＋Page Classification	結構化財務表
M05	Basic Info Extractor	OCR＋Classification	BasicInfo 30 欄
M06	Narrative Analyzer	Body Text	Narrative JSON
M07	Data Normalizer	Financial Table	FinancialData 76 欄 × N 年
M08	Summarizer／CrossValidator	Basic＋Narrative＋Financial	Summary、Confidence、Mismatch

既有 Review Matrix 記錄 M01–M08 的上下游與模組級 PASS，包括 BasicInfo 30 欄、FinancialData 76 欄及 Summarizer 結構化輸出。 VIS_REVIEW_ALL_MATRICES_v0100.json

def 06.3 · 新舊命名鏈問題

目前可看到兩套相近命名：

def 功能階段名稱

* VRN_M01_UnifiedPDFConverter
* VRN_M02_PageClassifier
* VRN_M03_OCREngine
* …
* VRN_M08_SummarizerV5

def 程式資產名稱

* VRN_MDL001_Converter.py
* VRN_MDL002_LayoutExtractor.py
* VRN_MDL003_TableRestorer.py
* VRN_MDL004_OCR_FetchingPDFTable_v1.py
* VRN_MDL005_OCRFetchingPDFText_v1.py
* VRN_MDL006_ConsolidatorAndPhaseValidator.py
* VRN_MDL007_APIDataFetcher.py
* VRN_MDL008_CrossValidator.py

這兩組名稱應由 Registry 建立明確 Alias／Stage Mapping，不得同時被視為兩套 Active Pipeline，否則會形成 Hydra：同一責任有兩個 Owner、兩個 Hash 與兩個修補入口。

def 06.4 · VRN 輸出

* Standardized PDF
* Page Classification JSON
* Layout／Zone JSON
* OCR Text JSON
* Financial Table JSON
* BasicInfo JSON
* Narrative JSON
* Normalized FinancialData
* Summary
* Validation Matrix
* Confidence Score
* CSV
* Parquet
* Quarantine Evidence

現有 Converter 與 LayoutExtractor 資產包含 PDF 驗證、CSV／Parquet 輸出、頁面分類、第一頁區塊擷取與表格區域偵測。 貼上的 Markdown (1).md

def 06.5 · 驗證邏輯

CrossValidator 包含：

* 數值精度正規化
* 單位轉換
* 容許誤差
* 單筆比較
* Mismatch Classification
* API Fallback
* 預估算術檢查
* 成長合理性
* Confidence 計算
* DataFrame／Check Matrix 輸出

這代表 VRN 的完成標準不是「OCR 有文字」，而是資料可以被解釋、比對、分類差異並提供信任分數。 貼上的 Markdown (1).md

def 06.6 · 主要風險

* 掃描 PDF 沒有文字層。
* 表格跨頁。
* 券商版面差異。
* 中文／英文／數字 OCR 混淆。
* 民國年與西元年。
* 千元／百萬元／億元單位誤判。
* EPS、營收、毛利率欄位語意錯置。
* 報告預估與官方實績混合。
* 同公司多個 Ticker 候選。
* 低 Confidence 資料被下游當成確定資料。

所有低信任結果應進 Quarantine，不得靜默修正後輸出為 PASS。

⸻

def 07 · VAP：Veritas AutoPlot／Visual Analytics Platform 詳細交接

def 07.1 · 系統定位

VAP 是純粹的視覺分析與呈現層，負責：

* Data Adapter
* Chart Contract
* Template
* Annotation
* Indicator Display
* Dashboard Layout
* HTML／PNG／PDF Export
* Responsive UI
* Visual Validation
* Renderer Lock
* Visual Evidence

VAP 不應在圖表函式內重新擷取資料、修補 OHLC、變更 Ticker 或替上游填補缺失值。

def 07.2 · VAP 核心元件

* vap_config
* vap_data_adapter
* vap_chart_*
* vap_indicators
* vap_annotations
* vap_templates
* vap_export
* vap_server
* via_autoplot_engine

def 07.3 · 圖表契約

VAP Chart Spec 不是單純的圖表名稱，而是至少包含：

欄位	說明
code	圖表唯一代碼
group	圖表分類
zh／en	中英文名稱
axes	軸數量
axisMode	SINGLE／DUAL_LOCKED／NONE
axisContract	刻度與間隔規則
dataShape	時序、XY、Distribution、Matrix
fields	必要欄位
rule	視覺與統計限制
renderer	Plotly／VAP SVG
templateGovernance	Append-only、Version、Archive、Restore
sourceEvidence	規格來源

VAP v015 的規格檔已把資料形狀、軸契約、Renderer、模板治理與來源證據納入圖表定義。 VIA_VAP_All_Chart_Specs_v015.csv

def 07.4 · Renderer 與輸出

VAP Workbench v019 的 Renderer 測試包含：

* Plotly 2.35.0 Bundled Runtime
* 不依賴 CDN
* Self-contained HTML
* VAP SVG
* HTML／PNG／PDF Export Contract
* 40／40 Plotly Canonical Coverage
* 40／40 VAP SVG Canonical Coverage

這表示 Renderer 與圖表規格層已有相當完整的測試證據，但不代表所有 Dashboard 都已接上正式資料。 VAP_Workbench_v019.html

def 07.5 · 已鎖定的視覺規範

* 淺色系，避免大面積黑色。
* Header 使用 Veritas Intelligence Analytics 品牌。
* 字體以 Inter、Noto Sans TC、DM Mono 為核心。
* 單軸優先。
* 雙軸必須使用明確 Axis Contract。
* 台股 K 線紅漲綠跌。
* 成交量與 K 線方向同色。
* 圖表標題不得重疊。
* 刻度間隔需左右一致。
* 卡片緊密、可堆疊、不得超出 Viewport。
* 左側控制面板可收合。
* 手機介面需簡化。
* 英文圖表名稱採一致大小寫。
* 所有圖表需顯示資料日期、來源與狀態。

def 07.6 · VAP 尚未完成的部分

部分 Dashboard Blueprint 仍被標記為：

PLAN_ONLY_WAITING_LIVE_DATA

例如 Global ETF Flow、Price＋Flow Dual Axis、Technical Event Timeline。這些 Blueprint 可以視為版面與規格準備完成，但不能宣稱已完成正式資料綁定。 VIA_VAP_All_Chart_Specs_v014.json

⸻

def 08 · 跨子系統資料流與介面

def 08.1 · 標準流程

def 文件來源流程

Broker PDF
→ VRN Converter
→ Page／Layout Classification
→ OCR／Table Extraction
→ Basic／Narrative／Financial Normalization
→ VDF Official／Market Data Cross-validation
→ SSOT Field Mapping
→ DuckDB／Parquet
→ VAP Dashboard
→ Central Governance Evidence

def 市場資料流程

TWSE／TPEX／MOPS／YFinance／Macro Source
→ Aegis Network Policy
→ VDF Fetcher
→ Schema／Ticker／Date Normalization
→ Data Quality
→ DuckDB／Parquet
→ Factor／Index／Flow Calculation
→ VAP Visualization
→ Central Governance Gate

def 08.2 · 建議統一資料封包

以下屬交接建議，應成為版本化 JSON Contract：

{
  "run_id": "RUN_YYYYMMDD_HHMMSS",
  "artifact_id": "VDF_DATA_000001",
  "subsystem": "VDF",
  "schema_version": "1.0.0",
  "source_name": "TWSE",
  "source_type": "OFFICIAL",
  "as_of_date": "2026-08-27",
  "grain": ["Date", "Ticker"],
  "row_count": 0,
  "content_sha256": "",
  "quality_status": "PASS|WARN|HOLD|FAIL",
  "data_class": "ACTUAL|DERIVED|PROXY|ESTIMATED",
  "evidence_path": "",
  "warnings": [],
  "errors": []
}

每一個下游都必須繼承 data_class。例如上游是 PROXY，VAP 不能只顯示漂亮圖表而把它標成 Actual。

⸻

def 09 · 日常操作 Runbook

def 09.1 · Audit

1. 開啟 PowerShell 7。
2. 以單一 Governance Launcher 進入 Audit。
3. 執行 Root Arbitration。
4. 驗證 Registry、SSOT、Environment。
5. 執行 Python／PowerShell／JavaScript Native Parser。
6. 執行 Contract 與 Real-data Read-only。
7. 產生 HTML／JSON／CSV Evidence。
8. 不修改 Canonical，不啟用 Runtime。

def 09.2 · Stage

只有 Audit 無 Blocking 時才可 Stage：

1. 建立唯一 Run ID。
2. 建立 Checkpoint。
3. 複製候選檔至 Staging。
4. 套用 Expected Hash Guard。
5. 執行三輪修補。
6. 執行 Unit、Dataset、Regression、Failure Injection。
7. 執行六流程／十二通道整合。
8. 執行 UI 與使用者測試。
9. 保留原檔與完整 Diff。

def 09.3 · Promote

只有以下條件全部存在才可 Promote：

* Approval Token
* Expected Registry Hash
* Expected Plan Hash
* Checkpoint
* Rollback Plan
* T0–T8 全部通過
* 每個子系統 S01–S12 通過
* 無未解決 Hydra
* 無未解決 Data Quality Blocking

def 09.4 · 啟用後

* 至少監控三個完整運作週期。
* 驗證 Heartbeat。
* 驗證錯誤率。
* 驗證資料新鮮度。
* 驗證記憶體與執行緒釋放。
* 每次增量更新後重跑 Regression。
* 若 Hash 漂移、Schema 漂移或資料品質惡化,立即 Rollback／Isolate。

⸻

def 10 · 已知風險與優先處理矩陣

優先級	風險	影響	建議處理
P0	Canonical Root 尚未完成最終仲裁	所有 Registry、Path、Hash 可能指向不同來源	先完成 T0 Root Arbitration
P0	Runtime Bridge 硬編碼 OneDrive	違反 Active Root Policy	改由 Governance 注入路徑
P0	VDF R06 有 205／1,871 OHLC 不一致	價格與回測結果不可信	逐來源分類 Adjustment／Missing／Source Difference
P0	Ready／Staging／Contract 被誤當 Activated	造成錯誤上線判斷	嚴格使用狀態機
P0	Functional 與 Supportive 存在重複模組	Hydra、修補錯檔、雙 Owner	Registry Alias＋Canonical Owner
P0	Aegis SSL 驗證預設可能關閉	中間人攻擊與資料完整性風險	Production 強制 TLS Verify
P1	Celeritas Import-time 初始化	AST 前可能產生副作用	Gate 前禁 Import,延遲 Bootstrap
P1	Panorama AST 對非 Python 只做 Index	可能誤報全語言 PASS	使用 Native PS／JS Parser
P1	VRN 兩套 M01–M08／MDL001–008 命名	Pipeline 重複與 Registry 混淆	建立 Stage Alias Map
P1	VAP Scope Copy 含 VDF／VRN 副本	視覺層可能引用過期程式	VAP 只引用 Contract,不持有執行副本
P1	部分 VAP Dashboard 仍無 Live Data	UI 看似完成但資料未接通	標示 Plan-only,不准 Promote
P2	高風險套件分散於多環境	安裝衝突與記憶體壓力	EnvManager 統一路由與隔離

⸻

def 11 · 正式交接檢查表

編號	必須交接的證據	完成標準
H01	Canonical Root Decision	Root、Owner、Git HEAD、Manifest、Hash 完整
H02	Central SSOT Snapshot	Regex、Synonym、Schema、Version 可還原
H03	Registry Snapshot	無 Duplicate ID、Missing Owner、Divergent Active
H04	Environment Matrix	via_core／via_vdf／via_vrn 等狀態明確
H05	Supportive Runtime Test	五個核心模組 Bootstrap、Self-test、Error Evidence
H06	VRN Pipeline Matrix	M01–M08 Input／Output／Schema／Test 完整
H07	VDF Dataset Matrix	Source、Grain、Rows、Freshness、DQ、Hash 完整
H08	VAP Chart Registry	Chart Contract、Renderer、Export、Data Binding 完整
H09	End-to-End Test	PDF／市場來源一路到 Dashboard
H10	Failure Injection	Network、Missing Field、Bad Schema、Timeout、Low Memory
H11	User Test	數值、圖表、Viewport、中文、匯出格式
H12	Checkpoint／Rollback	可在不損傷 Canonical 下還原
H13	Approval Evidence	Token、Expected Hash、Owner Approval
H14	Post-Activation Monitoring	至少三個完整週期穩定

⸻

def 12 · 交接接受標準

系統只有在以下條件同時成立時,才能宣告交接完成:

1. Canonical Root 唯一。
2. Active Owner 唯一。
3. Duplicate Active Implementation 為零。
4. 未決 Divergent Variant 為零。
5. Critical AST Error 為零。
6. Contract Tests 100% 通過。
7. 真實資料可唯讀取得。
8. Data Quality Blocking 為零。
9. Critical Regression Tests 100% 通過。
10. 每條整合 Lane 都有 Terminal Status。
11. VAP 數值可回溯至 VDF／VRN Evidence。
12. Checkpoint 與 Rollback 已實測。
13. Approval Token 與 Expected Hash 完整。
14. 啟用後至少三個完整週期穩定。

⸻

def 13 · 最終交接結論

VIA 不是單一 Python 程式,也不是單一 HTML Dashboard,而是一套分層治理的分析平台:

* VIA Central Governance Console 是決策、權限與稽核中心。
* Supportive Modules 是安全、環境、網路、註冊、加速與執行基礎。
* VRN 將非結構化報告轉為有證據的結構化資料。
* VDF 將外部市場資料轉為可信、可更新、可查詢的資料資產。
* VAP 將已驗證資料轉為一致、可互動、可匯出的視覺產品。

截至現有證據基準,系統已具備相當完整的治理設計、支援模組、VRN 管線、VDF 模組與 VAP Renderer;但中央治理文件仍將整體狀態標為 HOLD_REMEDIATION_REQUIRED／NOT_ACTIVATED。最關鍵的接手工作不是繼續增加更多引擎,而是先完成 Canonical Root 仲裁、去除重複權威、修復 VDF 真實資料品質問題、消除硬編碼路徑與 import-time 副作用,最後以受控 Gate 完成真正的端到端啟用。
