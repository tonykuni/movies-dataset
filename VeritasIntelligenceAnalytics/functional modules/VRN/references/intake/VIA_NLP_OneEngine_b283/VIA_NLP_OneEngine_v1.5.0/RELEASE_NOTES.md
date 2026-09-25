# VIA NLP One Engine v1.5.0

發布日期：2026/09/01

## 本版成果

- 新增 Microsoft MarkItDown 可選本機 intake；只允許 `convert_local()`，plugins、LLM、URL 與網路關閉，轉換結果明示為 Markdown 分析投影。
- 新增 `VIA_MARKDOWN_LAYOUT_ANALYSIS/1.0`，涵蓋常用 block／inline Markdown 類型，所有來源字元可逐字重建，NLP 修復只存在衍生層。
- 新增 `VIA_CONTEXT_RECONSTRUCTION/1.0`：文章／對話／混合／程式文件模式、功能分類、topic threads、reply candidates 與未回答問題清單。
- 新增 `VIA_FUNCTION_CLASSIFICATION/1.0` 與 `VIA_CODE_RESTORATION/1.0`：397 個實際函式可依 AST 證據分類，並重建為 8 份不執行、不寫入的來源模組模板。
- 新增 `VIA_TEMPLATE_RECONSTRUCTION/1.0`，依文章、對話、技術規格或程式選擇標準模板；所有 slot 來源化，缺欄位不得猜補。
- Mind Map 加入 context thread、function、standard template 與 layout type typed nodes，沿用 snapshot hash chain 與人工動態修正閘門。
- 20 組 Python／JavaScript 開發工具及 Microsoft MarkItDown 納入 21 組唯讀 Provider Registry；不自動安裝、import、執行或啟動瀏覽器。
- 多檔程式重建改由 Source Record 副檔名做完整檔案分析；實際附件從 327 個碎片收斂為 8 個來源模組，無效區塊 66 → 0、低信心語言 44 → 0。
- Python AST 常值統一為 deterministic JSON representation，修正 `set` 等安全解析後無法寫入快取／JSON 的缺陷。
- 58 項自動測試全部通過；8 份實際 HTML／Python、569,650 字元達成來源與 Layout 100% 重建，兩次 reconstruction ZIP SHA-256 相同。

## v1.4.0 基線成果

- 新增 `VIA_INSTRUCTION_RECONSTRUCTION/1.0`：自然語言指令分類、逐步程序、前置條件、驗證關係與中英文標籤。
- 新增 PowerShell／Bash／CMD 續行命令重建；完全相同命令合併為穩定 ID，但所有 occurrence 均保留，命令永不執行。
- 新增 `VIA_BILINGUAL_KNOWLEDGE_BODY/1.0`：主題、知識層、指令、程序、程式版本族及衝突的雙語機器契約。
- Mind Map 升級至 `VIA_MIND_MAP_JSON/3.0`／`VIA_KNOWLEDGE_GRAPH/3.0`，提供 `human_view.zh`、`human_view.en` 與雙語 typed nodes／edges。
- 新增 `VIA_MIND_MAP_EVOLUTION/1.0`：snapshot hash chain、跨版 node／edge delta、修正提案與 rollback reference。
- `reconstruct-bundle --previous-package` 及 PowerShell `-PreviousPackage` 可把上一版 Knowledge Full／Mind Map 納入比較。
- Source Record ID 改為檔名 + source SHA-256 穩定鍵；新增較早排序檔案不再改變既有 Record ID。
- 43 項自動測試全部通過；實際 149,489 bytes 語料達成 100% 來源與事實完整性，重建 61 條指令、2 個唯一命令（4 次 occurrence），並成功連接 v1.3 → v1.4 Mind Map。

## v1.3.0 基線成果

- 新增整批討論紀錄入口 `reconstruct-bundle`，可依確定順序讀取多檔或資料夾並建立 Source Record Ledger。
- 新增 Knowledge Object Registry：穩定 ID、全 occurrence、決策／需求／問題／行動／參數 registers、exact deduplication、衝突及取代審查鏈。
- 新增 Code Reconstruction 3.0：版本家族、完全重複版、差異修訂、候選版、symbol registry、interface graph、unresolved／ambiguous call。
- 靜態程式語言擴充至 Python、PowerShell、JavaScript、TypeScript、JSON、SQL、HTML、XML、CSS、YAML、TOML、Bash。
- 未標 code fence 改以信心化語言推定；低信心、語法錯誤與缺介面一律列入 review，不假成功。
- 新增原子輸出與可重現 Handoff ZIP：Summary、Knowledge、Mind Map、Code、Source Ledger 及完整 Evidence Package。
- 36 項自動測試全部通過；實際 149,489 bytes 跳題 Markdown 兩次輸出 ZIP SHA-256 完全一致。
- 實際語料產出 418 個知識物件、57 組待審衝突、88 個表格、41 個程式區塊及 36 個程式版本家族；4 個無效片段與 20 個低信心語言結果均 fail-to-review。

## 延續 v1.2.0 能力

- 僅強化 NLP 核心；未修改行情、匯率、利率、爬蟲、Dashboard 或其他 VIA 支援模組。
- 主題重組加入穩定 Entity Anchor：相同 Ticker 可跨跳題回接，不同 Ticker 的衝突會降低誤合併機率。
- 主題數達上限時改用 `unresolved_capacity_bucket`，不再以最近相似度硬塞無關段落。
- 完善稿加入受保護事實核對；數字、金額、百分比、日期、URL、Email 或 Ticker 變動即 fail closed，逐字還原來源段落。
- 新增 `VIA_STRUCTURED_TABLE/1.0`：Markdown／key:value 表格抽取、來源行號、segment reference、逐格保真與 SHA-256。
- 新增 Gold Set 評估：B-cubed、Topic Return precision／recall／F1、candidate-only threshold grid search 與候選指紋。
- 門檻校準不自動套用，ML `auto_promote=false` 與 Tier 3／4 預設關閉維持不變。
- 30 項自動測試全部通過；108,374 字元實際跳題 Markdown 達成 100% 原文重建、完善覆蓋與整理覆蓋，並抽取 87 個可追溯結構表。

## 延續 v1.1.0 能力

- CPU Sparse Hierarchical Topic Reconstruction：跨多段跳題後可回接同一主題，並建立 Topic Episodes。
- 來源與完善稿雙帳本：原文、offset、SHA-256、refinement、語意角色與修改紀錄全程可追溯。
- Mind Map 2.0：human tree + AI typed graph，包含 topic／episode／segment nodes 與切換、復返、來源關係。
- Engine Blueprint 2.0：函式參數與回傳介面、呼叫關係、外部依賴、拓撲順序、循環與人工啟用閘門。
- ML 演化升級：資料去重、同文異標拒絕、分層驗證、SGD champion 與兩層 Tiny MLP CPU challenger。
- 可選 Deep Semantic Enrichment：僅在明確啟用 Tier 3 時載入本機 Embedding，不保存原始向量。
- 自動 candidate evaluation 可按回饋筆數觸發；自動 promotion 仍維持關閉。

- 將原先以會議紀錄為中心的修復概念提升為「任何文章／任何文字」通用引擎。
- 四級 Task Router、Lazy Model Pool、RAM／CPU Watchdog、OOM admission gate。
- 通用 repair／analyze／structure／keywords／entities／summarize／classify 任務。
- 可選 spaCy、Sentence Transformers、ONNX Runtime、Ollama；預設不下載且不載入。
- HashingVectorizer + SGDClassifier 增量 ML，人工回饋與 Macro-F1 候選升版閘門。
- SQLite WAL cache、batch checkpoint、原子 stage queue、stale task recovery。
- FastAPI、CLI、淺色響應式監控 Dashboard、Windows PowerShell 一鍵安裝。
- 跳題對話無損 segment ledger、Body of Knowledge、Mind Map、SSOT 與 VIA Keyword。
- Python／PowerShell／JavaScript／TypeScript／JSON 唯讀解析與 Engine JSON 整合藍圖。
- Mega-Prompt 治理契約：三輪分析、六條管線、20 Accelerators、Zero-Hydra 風險矩陣。
- Argos／Ollama／Google Cloud 分段翻譯；明確拒絕不穩定的 Google 網頁自動貼上模擬。
- v1.1.0 的 24 項自動測試、三份實際附件驗證與 500 篇短文併發壓測均保留為基線。

## 安全預設

- 僅綁定 localhost。
- 深度模型與 LLM 關閉。
- 模型自動升版關閉。
- 稽核記錄不保存原文，只保存輸入雜湊與處理 metadata。
- 模糊詞只提出候選，不靜默更改文章事實。

## 相容性

- Python 3.11+。
- Windows 11／PowerShell 7 為主要部署目標。
- Linux 與 macOS 可使用 Python CLI；PowerShell 一鍵安裝流程針對 Windows。
