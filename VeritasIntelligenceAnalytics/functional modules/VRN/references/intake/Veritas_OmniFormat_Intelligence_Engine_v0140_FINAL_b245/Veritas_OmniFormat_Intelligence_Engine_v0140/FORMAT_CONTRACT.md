# Veritas OmniFormat 讀取與輸出格式契約

契約：`veritas.omniformat-format-contract/1.4`  
引擎：`ENG-VOFIE-001`  
子系統：`VIA-SUBSYS-VOFIE-001`

## 不變量

1. 每個來源在讀取前後都驗證 `byte_size + BLAKE2s`；來源只讀、不覆寫、不刪除。
2. Reader 必須回傳 `SourceRecord`：來源 ID、路徑、格式、編碼、原始雜湊、完整抽取文字、抽取雜湊與格式中繼資料。
3. 原始抽取全文必須寫入 Universal Content IR；正規化、隔離與重構只產生新的候選表示。
4. 重複主題只寫入 `duplicate_of`，不得移除。
5. 已存在且非空的輸出目錄不得覆寫；必須建立新的時間戳 run 目錄。
6. 來源 HTML 的 JavaScript 只抽取為證據，不得執行；AI 改寫只能產生候選，不得直接套用。
7. v1.0 完整輸出契約繼續有效；v1.1 增加 `simple` 五檔；v1.2 增加雙語言工具治理；v1.3 增加 NoHydra；v1.4 增加 Runtime Copy 治理與真實三輪唯讀掃描。
8. 簡易模式最多 5 個輸入；ENGINE／SYSTEM 的主要輸出檔名與數量完全相同。

## 輸入格式

| 類型 | 副檔名／格式 | Reader 行為 | Canonical 結果 | ST |
|---|---|---|---|---|
| 文字 | TXT、LOG、RST | 編碼偵測、換行正規化候選、主題錨點切分 | Markdown + IR | ST-CORE |
| Markdown | MD、Markdown | Fence 補標候選、Heading／長度切分 | Markdown + IR | ST-CORE |
| HTML | HTML、HTM、XHTML | 語意內容與 UI 規格雙軌抽取，script 不執行 | Markdown + UI IR | ST-CORE |
| Word | DOCX | OOXML 段落、Heading、表格依文件順序抽取 | Markdown + IR | ST-ADAPTER |
| PowerPoint | PPTX | 依投影片與 shape 順序抽取文字 | Markdown + IR | ST-ADAPTER |
| Excel | XLSX、XLSM | 工作表、儲存格與公式表示；不執行巨集 | Markdown table + IR | ST-ADAPTER |
| 表格 | CSV、TSV | Delimiter 偵測、UTF-8 BOM 支援、欄列保留 | Markdown table + IR | ST-CORE |
| 結構資料 | JSON、JSONL、NDJSON、XML、YAML、YML、TOML、INI、CFG | Tree 表示或原文保留 | Markdown + IR | ST-CORE |
| PDF | PDF | 可選 pypdf，依頁序抽取 | Page-ordered Markdown | ST-OPTIONAL |
| 程式碼 | Python、PowerShell、JS、TS、C、C++、C#、Java、Go、Rust、Ruby、PHP、Swift、Kotlin、SQL、Shell、Dart、Elixir 等 | AST 或結構 Adapter；不執行來源 | Component IR + Markdown | ST-CORE |

未知純文字副檔名會使用安全文字 Reader；二進位格式若沒有已登記 Adapter，必須明確 `HOLD`，不可猜測內容。

## 文字與主題重構

1. 保留完整來源文字與行號。
2. 以 Markdown Heading、HTML Heading、格式錨點與最大主題長度切分。
3. 每個 Topic 寫入 `topic_id`、來源行範圍、分類、tags、內容雜湊與 ST 定位。
4. 相同內容標記 canonical／duplicate，兩者都留在 IR。
5. `svg`、工具提示與對話殘片等只進 quarantine；仍保留原文、行號與雜湊。

## 跨語言程式元件契約

每個程式元件至少包含：`language`、`unit_type`、`symbol`、`signature`、起訖行、`syntax_status` 與內容雜湊。Python 使用 AST；其他語言使用可替換結構 Adapter。未通過語法／結構與 fixture 等價測試時，重寫結果只能是 `HOLD` 候選。

## HTML 雙軌契約

- Content lane：Heading、paragraph、list、table、link、image 轉為語意 Markdown。
- UI lane：form、input、select、textarea、button、link、事件、endpoint、script/style 證據轉為 UI Spec。
- Template lane：由 Python 產生本地分離的 `HTML + CSS + JavaScript`；無 CDN、鍵盤可操作、支援響應式、深色偏好與 reduced motion。

## 輸出格式

| 輸出 | 定位 | 驗證 |
|---|---|---|
| Markdown | 完整人可讀 canonical 與程式元件 | ST Matrix、來源追溯、內容保留 |
| JSON IR | 機器可讀 SSOT | Schema、來源全文、hash、quality |
| Word | 緊湊型完整參考指南 | Render、Heading、表格幾何、a11y |
| PowerPoint | 架構、統計、品質與決策摘要 | 逐頁 render、overflow test |
| Excel | Summary、Topic Matrix、Sources、ST、UI QA、Readme | 公式錯誤掃描、逐表 render |
| CSV | Topic Matrix | BOM、欄位與列數 |
| HTML/CSS/JS | 本地互動模板 | HTML 結構、CSS、JS syntax、無遠端依賴 |

## v1.1 Simple Five 契約

根目錄必須恰好出現下列五個檔案：

| Key | 固定檔名 | 最低驗證 |
|---|---|---|
| `md` | `Veritas_VOFIE_Reconstructed.md` | ST、整合動作、完整主題與來源追溯 |
| `html` | `Veritas_VOFIE.html` | CSS／JS／資料內嵌、無遠端依賴、來源 script 不執行 |
| `component_json` | `Veritas_VOFIE_ComponentSpecs.json` | UI Spec、Code Units、Consolidated View、160 failures、完整 IR |
| `docx` | `Veritas_VOFIE_Reconstructed.docx` | 有效 OOXML、字型宣告、可渲染；python-docx 缺少時 stdlib 降級 |
| `csv` | `Veritas_VOFIE_TopicMatrix.csv` | UTF-8 BOM、固定欄位、可解析引用 |

- `ENGINE`：不得在根目錄或 `_system/` 產生治理 sidecar。
- `SYSTEM`：根目錄仍恰好五檔；治理資料只能放在 `_system/`。
- 輸出目錄已非空時使用新的 timestamp sibling，不覆寫既有內容。

## v1.1 整合動作契約

`text_merge → code_merge → restructure → deduplicate → optimize` 依固定順序執行。每個 action 都回傳 `enabled / status / affected / source_mutated / policy`。`source_mutated` 必須永遠是 `false`；deduplicate 只影響視圖，完整 Topic 仍保留。

## v1.2 雙語言工具契約

1. `config/polyglot_tool_catalog.json` 必須各有 20 個 JavaScript 與 PowerShell 免費 CPU 工具，tool ID 唯一、fallback 非空。
2. 十項 capability × Python／JavaScript／PowerShell 必須恰為 30 個 matrix rows，且不得有未覆蓋 capability。
3. 工具偵測不得安裝套件、匯入 PowerShell 模組或改 PATH；缺少時明確回報 `NOT_INSTALLED`。
4. JavaScript 工具只經 `via-ui`、PowerShell 工具只經 `via-ps`，不得污染 base 或互相跨路由。
5. `tool-plan` 只依使用者要求的 capability 選工具；預設 `PLAN_ONLY`。`--execute-safe` 只允許唯讀 syntax parse。
6. 每次安全執行都必須驗證來源執行前後 size 與 BLAKE2s 完全相同。
7. SYSTEM 可在 `_system/PolyglotToolAudit.json` 保存精簡快照；ENGINE 的五檔根目錄契約不變。

## 失敗復原契約

`config/failure_catalog.json` 必須包含 8 stages × 20 failures。展開後每一項 failure 至少有兩個 `RECOVERY_HANDLERS` 中已實作的 handler；handler dry-run 必須回報 `source_mutated=false`。任一必需 Gate 失敗時 activation 必須 `HOLD`。

## v1.3 NoHydra 契約

1. `config/hydra_risk_catalog.json` 必須恰有 20 個唯一、連續排序的九頭龍風險。
2. 每項至少有兩個 detectors、兩個 breakers、三個 solutions、SOP 與 never-again control。
3. 高風險 default action 固定為 `HOLD`；unknown risk 必須 fail-closed。
4. 三輪為硬上限：Panorama read-only → parallel-safe proposals → sequential dependency review。
5. Canonical source 永遠唯讀；Runtime Copy 也只有明確真實寫入核准後才可寫。
6. Hydra audit 不得 import 被掃模組、啟動程序、連網、寫 DB 或修改來源。
7. SYSTEM 增加 `_system/HydraRiskAudit.json`；ENGINE 的五個根檔仍完全不變。
8. Activation 必須把 Hydra Gate 當獨立必需 Gate；任何 finding 或來源 mutation 都必須 `HOLD`。

## NLP／VSIS 整合

## v1.4 Runtime Copy 契約

1. Canonical／SSOT 只讀；引擎不提供 canonical promotion 命令。
2. 真實寫入要求精確 token `YES_FOR_ANY_REAL_WRITE`，且只寫入新建、版本化、run-local Runtime Copy。
3. Runtime Copy 最多接收 5 個存在且不重複的來源；逐檔保存來源與副本 BLAKE2s。
4. hash state 固定：`MISSING→APPLY`、`PROPOSED→SKIP`、`ORIGINAL→BACKUP_APPLY`、`OTHER→FAIL_CLOSED`。
5. `rollback-check` 只做 dry-run 完整性檢查，`real_rollback_performed=false`、`canonical_mutated=false`。
6. Activation 必須通過 Runtime Copy safety test；缺核准 token 時建立動作必須 `HOLD`。
7. SYSTEM 可增加 `RuntimeCopySafetyTest.json` 與 `HydraRiskMatrix.html`，根目錄五檔契約不變。

找到相鄰 `VIA_SemanticIntelligenceSubsystem_v0120` 或 `VIA_VSIS_ROOT` 時，VOFIE 調用 VSIS 1.2 的 `normalize`、`segment`、`categorize`、`semantic_check`。結果寫入 `quality.vsis_bridge`。找不到時使用確定性本地降級，格式與來源保留能力不受影響。

## 唯一擴充入口

未來新增或停用整合工具修改 `config/tool_registry.json`；JavaScript／PowerShell 候選與能力映射修改 `config/polyglot_tool_catalog.json`。新增工具保留新 `tool_id`；舊工具只能設 `enabled: false`，不得刪除。需要新解析器時再增加 Reader Adapter，但 Universal IR、ST-FROZEN、來源 hash gate 與既有格式不得改變。
