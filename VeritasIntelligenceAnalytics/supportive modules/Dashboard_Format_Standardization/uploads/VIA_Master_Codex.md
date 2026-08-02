---
title: VIA · 功能引擎總覽與方法論總表 · 只增不減持續優化計畫
system: Veritas Intelligence Analytics (VIA)
version: v0500
date: 2026-07-01
policy: append-only 只增不減 · human-approval 核可制 · local-sovereign 本地主權 · completeness-honesty 完整性誠實
encoding: UTF-8 (No BOM)
canonical: VIA-DOC-MASTER-CODEX
---

# VIA · 功能引擎總覽與方法論總表

> 截至 2026-07-01,盤點本專案所有功能引擎與方法論,檢視系統目標達成度,並列出「只增不減、持續優化」的計畫。本文件本身即為一個 append-only SSOT 節點。

---

## 0. 文件定位與誠實邊界

本文件把兩類東西分清楚,避免把「藍圖」當成「已完成」:

| 類別 | 定義 | 標記 |
|---|---|---|
| **已建置・已測試** | 在 pmis_lite 套件中實作、44/44 測試通過;或已產出可執行 HTML 平台 | `[BUILT]` |
| **架構藍圖・方法論** | 已設計成規範/流程/Prompt,但需你本機環境或真實外部系統(SAP/PLM/MS Project 真檔)才能落地 | `[DESIGN]` |
| **沙箱不可達** | 需真實股價/信箱/SAP API,沙箱網路擋掉;工具已建好,資料須本機餵入 | `[LOCAL-ONLY]` |

**沙箱限制(誠實聲明):** 目前環境無法讀你本機檔案/信箱、無法抓真實股價(TWSE/yfinance)、無法連真實 SAP。所有引擎均以合成/樣本資料建置與驗證,並提供 CSV 匯入與本機抓取腳本;真實資料在你本機接入即生效。**非投資建議。**

---

## 1. 治理憲章(不變的底層原則)

這些是所有引擎共同遵守、不會因版本演化而改變的鐵律:

1. **只增不減(Add-Only / 只增不減)** — 資料、模組、欄位、功能只新增不覆寫;需改邏輯則建新版本(v2),舊版標 `@deprecated` 保留歷史。刪除須明確宣告「刪除」才解鎖。
2. **核可制(Human-in-the-loop)** — 高風險切換(自製↔委外、覆寫、刪除)需人類簽核;系統提供仲裁方案但不擅自執行破壞性操作。
3. **本地主權(Local Sovereign)** — 資料 100% 留在本地;優先本地免費開源函式庫(DuckDB/Polars/llama.cpp),不外洩至封閉 API。
4. **完整性誠實(Completeness Honesty)** — 寧可 FAIL 也不假裝完整;缺口如實標示,不無中生有。
5. **審計保留(Audit Retention)** — 快取與 `.quarantine` 僅在「下次進程啟動」清理,不在任務結束時刪,保全景除錯軌跡。
6. **編碼鎖定** — HTML/JSON/PS = UTF-8 (No BOM);CSV = UTF-8-BOM。
7. **Visual Lock 美學** — 幾何極簡、低飽和(Seaborn Muted)、紅漲綠跌、無卡通/emoji;色票 `#f5f4f0 / #1e1d1a / #c96b5a 紅漲 / #5a9e6f 綠跌 / #4c78a8 / #439a9a`。
8. **命名憲法** — `VIA*`=基礎設施 / `VDF·VRN·VAP`=功能核心 / `Veritas*`=應用分析;積木式 `Module-Class-Function-Lib` 編號。

---

## 2. 功能引擎登錄(BUILT & TESTED)

### 2.1 pmis_lite Python 套件 — 44/44 測試通過 `[BUILT]`

| 引擎模組 | 職責 | 對應方法論 |
|---|---|---|
| `ingest_engine` | 末日級擷取:magic-byte 偵測、docx/xlsx 自解析(zipfile+XML,零依賴)、亂碼修復、去重、單位分類、guarantee 報告(gap=0 才 PASS) | 全景掃描・完整性誠實 |
| `module_scan` | 掃專案 fan-in 分析 → SUPPORTIVE/FUNCTIONAL/LAUNCHER 分類 + 載入順序建議 | 依賴性檢驗 |
| `fin_verify` | 會計恆等式閘門(資產=負債+權益)、成本結構/損益兩平、校準、同業比較 | 完整性誠實・驗證閘門 |
| `sync_ssot` | SSOT↔MS Project 同步:錨點 [Project-Task]、append-only 版本化、排程死結/資源超載偵測、任務↔BOM 橋接 | MS Project 分流驗證 |
| `sap_bom_ref` | SAP BOM 知識:T-codes(CS01-15)、替代選擇 Q/D/V、不展開四條件 | SAP 尊重・知識管理 |
| `ssot_synonyms` | 同義字增量展開 → 唯一 canonical 基準;衝突守門(改指須宣告) | 唯一 SSOT・只增不減 |
| `plm_pmbok_ref` | PLM(EBOM/MBOM/ECO/版次/生命週期)+ PMBOK(10 領域/5 流程)同步錨定 | PLM+PMBOK 橋接 |
| `super_bom` | 7 公司·23 BU·66 產品族;散熱+電源 38 品類;成本滾算、where-used、diff | Super BOM 架構 |
| `bom_template` | 36 欄位字典(9 必填)、品類分類、成本 roll-up | Super BOM 架構 |
| `autocode` | 零配置自動編碼:`prefix-source-YYMM-hash` 宇宙碼 | Auto-Coding for All |
| `self_train` | 自我學習曲線(train_round) | 智慧演化 |
| `presets` | 8 企業預設(SAP MM/PP/SD、MS Project、PLM ECM/BOM) | 盲探測本體生成 |
| `schema` / `encoding` / `textrepair` / `numbering` / `classify` / `keywords` / `completeness` / `store` | SSOT 基礎層:Record 結構、亂碼修復、內容雜湊、三段分類、完整性、Parquet 儲存 | 雙軌流水線(結構化) |
| `adapters/` | mail_imap · mail_oauth · outlook_desktop · jsonl_mail · enterprise · **msproject**(讀 XML 匯出) · **plm** · excel_csv · supplement | Omni-Data Intake |
| 進入點 | `fetch_mailbox` · `via_launch_driver` · `via_fetch_prices` · `VIS_Launch_All.ps1` · 一鍵批次檔 | 隨插即用 |

### 2.1.1 七大引擎整合門面(`via_engines.VIA`) `[BUILT]`

停止發散、轉為整合:51 底層模組收斂為 **7 大引擎**,單一 `VIA()` 入口全操作(只增不減,底層模組保留不動)。

| 引擎 | 整合底層 | 對外操作 |
|---|---|---|
| **① IntakeEngine 擷取** | ingest_engine · ingest_plus · code_parse · table_repair · smart_asset · adapters.* | `run` `parse_code` `repair_table` `assets` `guarantee` |
| **② SSOTEngine 歸一** | ssot_synonyms · plm_pmbok_ref · autocode | `resolve` `add_synonym` `registry` `autocode` |
| **③ SyncEngine 同步** | sync_ssot · adapters.msproject · adapters.plm | `sync` `conflicts` `link_bom` `ms_anchor` `bom_anchor` |
| **④ BOMEngine 料表** | super_bom · bom_template · psu_taxonomy | `classify` `taxonomy` `validate` `rollup` `where_used` |
| **⑤ FinanceEngine 財務** | fin_verify | `verify` `cost` `calibrate` `peers` |
| **⑥ KnowledgeEngine 知識** | sap_bom_ref · plm_pmbok_ref | `tcode` `select_bom` `plm_concepts` `pmbok_areas` |
| **⑦ GovernanceEngine 治理** | module_scan · completeness · selfcheck | `scan` `import_order` |

用法:`via = VIA(); via.ssot.resolve("AENR"); via.intake.run(paths); via.finance.verify(d)` — 一個物件全通,消費者的 AI 不必逐一認識 51 模組。詳見 `VIA_Capability_Matrix.html`。

### 2.2 HTML 平台(18 支,全部含 PDF + MD 雙匯出) `[BUILT]` `[LOCAL-ONLY 真實資料]`

| 平台 | 核心功能 |
|---|---|
| `VIA_PSU_Thermal_AllInOne` | **旗艦**:三分頁(AUTO SSOT 三階層+族群指數走勢 / Super BOM 料本→毛利率 / 2026-28 forward 評價含全球同業)+ append 日誌 + 只增不減守門 |
| `VIA_Hierarchy_Index_Valuation` | 三階層自動編碼 + L1/L2 族群指數 + 評價(全部+全球同業) |
| `VIA_PSU_Thermal_SSOT` | TH/PW 六軸編號 SSOT、19 檔多軸碼、勘誤面板 |
| `VIA_ThreeGroup_Normalized` | 三組正規化 adj close 均值 vs 加權/櫃買,基準 2026-01-02=100 |
| `VIA_MSProject_SSOT_Sync` | MS Project↔SSOT 同步、衝突偵測、任務↔BOM、SAP BOM 知識 |
| `VIA_Synonym_SSOT_PLM_PMBOK` | 同義字解析器 + 唯一基準登錄 + PLM/PMBOK/MSProject 對映 |
| `VIA_Financial_Statements` | 17 時間欄、7 分頁三大報表、每列 VIA 碼、驗證數學 |
| `VIA_CostStructure_Peer_Verify` | 驗證閘門 + 成本結構兩平 + 同業比較 |
| `VIA_Integrated_Platform` / `SuperBOM_Financial_Model` / `SuperBOM_Detailed_Analysis` | Super BOM + 財務模型整合 |
| 其他 | `VIA_ABS_FinTable/Registry_Console` · `VRN_ReportData_Audit` · `config_builder` · `launcher_minimal` · `result_DEMO` |

---

## 3. 方法論總表(METHODOLOGY CODEX)

### 3.1 SSOT 自動成長 SOP(四步) `[DESIGN→部分 BUILT]`
`Step1 全景掃描與錨點確認` → `Step2 結構化解析與增量設計(Delta)` → `Step3 依賴性與效能檢驗(本地優先)` → `Step4 輸出與更新部署(含 Changelog)`。
> 已落地:sync_ssot / ingest_engine / module_scan 皆遵此流程輸出報告。

### 3.2 雙軌成長流水線 `[DESIGN→部分 BUILT]`
- **結構化軌**:DuckDB+Parquet;Schema 對齊(ALTER ADD COLUMN 不刪)、Append/Upsert 不 Overwrite、資料血緣三欄(`_inserted_at`/`_source_file`/`_engine_version`)。
- **非結構化軌**:Markdown 知識庫 + 函數版本控制(`calc_v2()` + `@deprecated`)、TOC 自動維護、依賴隔離。
> 已落地:store(Parquet)、ssot_synonyms(Markdown 化登錄)、本 MD 匯出機制。

### 3.3 D.A.R.T. 衝突檢測與仲裁 `[DESIGN→部分 BUILT]`
`Detect → Analyze → Resolve → Translate`。衝突分類:**結構衝突(Schema Mismatch)/邏輯衝突(Logic Overlap)/錨點遺失(Anchor Missing)**;隔離至 `.quarantine/` + 現場快照;仲裁產修復腳本;幾何極簡報表。
> 已落地:sync_ssot 的排程/資源衝突偵測、ssot_synonyms 的改指衝突守門。

### 3.4 MS Project / PLM 分流驗證註冊 `[BUILT: MSP anchor / DESIGN: PLM 深度]`
- **MS Project**:錨點 `[Project_ID]-[Task_ID]-[Timestamp]`;相依死結、資源超載(>100% 標 Overallocated 不阻斷)。
- **PLM**:錨點 `[Part_Number]-[Revision]-[State]`;孤兒節點、只增不減升版、Adjacency List + Recursive CTE 展開。

### 3.5 Super BOM 架構(電子零組件泛用) `[BUILT: schema/rollup / DESIGN: DuckDB CTE]`
三表解耦:`M01_ItemMaster`(料號主檔,升版不刪)、`M02_AML`(製造商對應,Pref_Rank 主/替代料)、`M03_BOM_Structure`(父子鄰接表,Alt_Group/Ref_Des/Effective_Date)。
遞迴展開:DuckDB `WITH RECURSIVE`(Accumulated_Qty 累乘、Path 溯源);Polars 向量化成本滾算(group_by Alt_Group + Pref_Rank first,無迴圈)。

### 3.6 M05 估值引擎(join_asof) `[DESIGN / LOCAL-ONLY]`
`price_df.join_asof(mops_df, backward)` 對齊日頻價格×季頻財報(無前視偏誤)→ EPS_TTM/BVPS → ROE/ROA/D-E → PER/PBR/PS。
> 沙箱不可抓真實 TWSE/MOPS;via_fetch_prices.py 在你本機執行後匯入。

### 3.7 同義字 → 唯一 SSOT + PLM/PMBOK 對齊 `[BUILT]`
多術語(ECO=AENR=工程變更單=ECN)→ 唯一 canonical(SSOT-CHANGE);15 基準/138 同義字;PLM+PMBOK 對齊 25 項 0 缺口。

### 3.8 三輪 AI 客製化導入方法論 `[DESIGN]`
`泛用底座極致化 → 三輪 AI 強制客製 → 增量維護 → 智慧演化`:
- **第一輪**:Schema 對應(盲探測 + 本體生成 + 積木編號)。
- **第二輪**:PMBOK/PLM 對齊(把管理心法變成驗證 SQL/Python)。
- **第三輪**:NLP 訓練(學公司術語 → 同義字歸一)。
> 精神已落地於 autocode + ssot_synonyms + plm_pmbok_ref。

### 3.9 零阻力隱形橋接(Invisible AI Bridge) `[DESIGN]`
基層只需「發 Email/丟文件/拖曳」,AI 靜默抓取→清洗→關聯→以舊系統看得懂的語言(SAP BAPI 等)寫回。100% 尊重 SAP/MS Project/PLM 舊系統,降低導入阻力。

### 3.10 泛用型盲探測與自動編碼 `[DESIGN→部分 BUILT]`
盲探測(讀前 N 行 → 型態/分佈/命名慣例)→ 產業推論 → 動態本體(Module-Class-Function-Lib)→ 自動生成 Polars/DuckDB 腳本 → 註冊。
> 已落地:autocode 零配置、module_scan、ingest_engine classify_units(seed)。

---

## 4. 引擎 × 方法論 對映矩陣

| 方法論 \ 引擎 | ingest | module_scan | fin_verify | sync_ssot | sap_bom | synonyms | plm_pmbok | super_bom | autocode |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| SSOT 四步 SOP | ● | ● | ● | ● | | ● | ● | | ● |
| 雙軌流水線 | ● | | ● | ● | | ● | | ● | |
| D.A.R.T. 仲裁 | ● | | ● | ● | ● | ● | | ● | |
| MSP/PLM 分流 | | | | ● | ● | | ● | ● | |
| Super BOM | | | ● | ● | ● | | | ● | ● |
| 同義字唯一基準 | ● | | | | ● | ● | ● | ● | ● |
| 三輪客製 | ● | ● | | | | ● | ● | | ● |

---

## 5. 系統目標檢視(達成度)

| 系統目標 | 現況 | 缺口 |
|---|---|---|
| AUTO CODING FOR ALL | `[BUILT]` autocode + 各 HTML 自動碼 | 跨產業盲探測編碼待強化 |
| AUTO SSOT FOR ALL | `[BUILT]` 同義字唯一基準 + 三階層 + 分類 | 真實資料自動演化須本機 |
| MS Project 同步 | `[BUILT]` 單向 MSP→SSOT + 衝突偵測 | 雙向回寫 XML 待建 |
| PLM + PMBOK 橋接 | `[BUILT]` 25 項對齊 0 缺口 | 真實 PLM 匯出接入待驗 |
| SAP 尊重/整合 | `[DESIGN]` 知識庫 + 錨點 + BAPI 藍圖 | 真實 SAP 連線須企業環境 |
| Super BOM 引擎 | `[BUILT]` schema/rollup / `[DESIGN]` CTE | DuckDB 遞迴展開待本機驗 |
| 財務模型/估值 | `[BUILT]` HTML 評價 + forward / `[LOCAL]` 真價 | join_asof 真實財報待接 |
| 零阻力導入 | `[DESIGN]` 方法論完整 | 前端隱形橋接待實作 |
| Process/Data Mining · DL · KM | `[DESIGN]` 藍圖 | 需 llama.cpp/onnxruntime 本機部署 |

---

## 6. 只增不減持續優化計畫(ROADMAP)

原則:**每一項都是新增,不回頭刪既有功能**;每項標 `現況→目標→驗證閘門→相依`。分四階段,對應「泛用極致 → 客製 → 維護 → 演化」。

### Phase A · 泛用底座極致化(近程)
- **A1 雙向 MS Project 回寫** — 現況:單向;目標:SSOT→可匯入 XML;閘門:回寫後 re-import 一致性;相依:sync_ssot。
- **A2 Super BOM DuckDB 遞迴展開落地** — 現況:schema/rollup;目標:WITH RECURSIVE + Polars rollup 實測百萬節點;閘門:Accumulated_Qty 對帳;相依:super_bom。
- **A3 真實價格/財報接入** — 現況:示意;目標:via_fetch_prices→匯入全平台 LIVE;閘門:基準日 2026-01-02 對齊;相依:M05。
- **A4 同義字餵進擷取引擎** — 目標:ingest 內文自動 resolve() 歸一術語;閘門:跨語言歸一率;相依:ssot_synonyms+ingest。

### Phase B · 三輪 AI 客製化(中程)
- **B1 盲探測本體生成器** — 目標:讀前 N 行自動產 Module-Class-Function 編號 + Schema;閘門:型態推論準確率;相依:autocode+module_scan。
- **B2 PMBOK→驗證碼編譯** — 目標:把 10 知識領域轉成可執行驗證(交期/成本/資源);閘門:每領域至少一條規則;相依:plm_pmbok_ref+fin_verify。
- **B3 NLP 術語學習迴圈** — 目標:從公司文件自動擴充同義字(基準不變);閘門:唯一 canonical 數不增;相依:self_train+ssot_synonyms。

### Phase C · 增量維護(治理)
- **C1 D.A.R.T. 全鏈落地** — 目標:結構/邏輯/錨點三類衝突 → .quarantine + 修復腳本;閘門:靜默錯誤 0;相依:sync_ssot。
- **C2 override 稽核日誌** — 目標:每次宣告刪除/改指寫 append-only(誰/何時/改什麼);閘門:可完整回溯;相依:全平台。
- **C3 資料血緣三欄強制** — 目標:所有寫入帶 `_inserted_at/_source_file/_engine_version`;閘門:缺欄即攔;相依:store。

### Phase D · 智慧演化(遠程,需本機部署)
- **D1 本地 LLM 推論層** — 目標:llama.cpp(GGUF)或 onnxruntime CPU 加速,離線摘要/分類;閘門:純本地無外部 API;相依:資料主權。
- **D2 Process Mining** — 目標:比對工單/日誌找真實瓶頸(Critical Path);閘門:與 MSP 排程交叉驗證。
- **D3 KM 向量庫** — 目標:歷史解方檢索(缺料→過往 Production Version 建議);閘門:建議可追溯來源。
- **D4 Smart Asset Management** — 目標:預測性維護 + 資產生命週期告警;閘門:核可制卡控高風險動作。

---

## 7. Top 20 導入風險與緩解矩陣(排雷指南)

| # | 階段 | 風險 | 緩解 |
|---|---|---|---|
| 1 | 泛用底座 | 盲探測誤判產業 | 三輪確認 + 人工核可 Schema |
| 2 | 泛用底座 | 編碼亂碼跨平台 | UTF-8(No BOM)強制鎖定 |
| 3 | 泛用底座 | 大檔效能瓶頸 | DuckDB/Polars CPU 指令集加速 |
| 4 | 客製輪1 | Schema 對應錯誤 | ALTER ADD COLUMN 不刪 + 隔離區預覽 |
| 5 | 客製輪1 | 舊欄位被覆寫 | 只增不減 + 升版保留 |
| 6 | 客製輪2 | PMBOK 對齊流於形式 | 每領域落地成驗證 SQL/Python |
| 7 | 客製輪2 | PLM 版次衝突 | [Part-Rev-State] 錨點強制升版 |
| 8 | 客製輪3 | 術語歧義 | 同義字 → 唯一 canonical 收斂 |
| 9 | 客製輪3 | 過度客製難維護 | 積木化 Module-Class-Function |
| 10 | 整合 | SAP/MSP 舊系統抵抗 | 100% 尊重 + 隱形橋接 BAPI 靜默寫回 |
| 11 | 整合 | 跨部門資料定義打架 | AI 仲裁 + 人類簽核基準 |
| 12 | 整合 | 靜默錯誤(舊邏輯被覆寫) | D.A.R.T. 攔截 + 現場快照 |
| 13 | 整合 | 交期/產能爆單 | Production Version 自動切換 + 核可 |
| 14 | 維護 | 快取過早清理失審計 | 延遲清理(下次啟動才清) |
| 15 | 維護 | 資料血緣缺失 | 三欄(_inserted_at 等)強制 |
| 16 | 維護 | 版本爆炸難追 | append-only Changelog + TOC |
| 17 | 演化 | 外洩至封閉 API | 本地免費開源函式庫隔離 |
| 18 | 演化 | 模型幻覺污染 SSOT | 完整性誠實 + 驗證閘門 |
| 19 | 演化 | 基層阻力回彈 | 零阻力:發信/丟檔即可,工作變少 |
| 20 | 全程 | 導入摩擦力過大失敗 | 泛用極致→降維客製→漸進演化 |

---

## 8. 附錄

### 8.1 錨點規格
- MS Project:`[Project_ID]-[Task_ID]-[Timestamp]`
- BOM/PLM:`[Part_Number]-[Revision]-[State]`
- 自動宇宙碼:`VIA-{Level}-{Family}-{hash}` / `{prefix}-{source}-{YYMM}-{hash}`
- 唯一 canonical:`SSOT-{CONCEPT}`(15 基準)

### 8.2 LL 慣例(PowerShell 輸出鐵律)
`param()` 首列 · 無區塊註解 · `[IO.File]::WriteAllText` UTF-8 No-BOM · `ProcessStartInfo`+`ArgumentList.Add()`+async drain · 禁 Start-Job/exit/alias · `${var}:` 包裹 · `[ordered].Contains()` · Sort-Object hashtable 語法 · `@()`+`+=` 不用 List.Add · `$script:` 前綴 · Start-Process 僅開 HTML。

### 8.3 檔案清單(本次交付)
- `PMIS-Lite.zip`(pmis_lite 套件 · 44 測試 · 進入點 · 抓價腳本)
- 17 支 HTML 平台(PDF + MD 雙匯出)
- 本文件 `VIA_Master_Codex.md`

### 8.4 版本
- v0500 · 2026-07-01 · 初版總表(append-only,後續只增修訂章節)

---

_本文件遵循只增不減:後續更新以新增章節/附錄或標 `@deprecated` 方式進行,不刪除既有內容。UTF-8 (No BOM)。非投資建議。_
