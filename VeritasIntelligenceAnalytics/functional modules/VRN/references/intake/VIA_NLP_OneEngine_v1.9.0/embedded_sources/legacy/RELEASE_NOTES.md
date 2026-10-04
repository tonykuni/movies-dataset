# VIA NLP Application System v1.8.0

## v1.8.0 NLP-CORE 證據型摘要升級

- 新增 `VIA_EVIDENCE_SUMMARIZER/1.0`；每個摘要點均含原文、絕對 span、SHA-256、chunk ID、語言與選取理由。
- 摘要單點預設上限 900 字元；超長、無標點文字仍會依可追溯區間切成有界單元，禁止巨型原文伪裝成摘要點。
- 改為「先選各 chunk 代表點，再依全域分數補齊」；在點數預算足夠時，每個有效 chunk 都必須出現於最終摘要。
- 完整保留 v1.7 的 `summary` / `key_points` / `chunks` / `coverage` 欄位，僅增加 `evidence_points` / `quality` / `languages`。
- 本文／非本文分類新增保守 fail-closed 政策、閾值、版面區域轉換軌跡、留存率、排除率及高信心排除數。
- 全文摘要與本文摘要同時輸出；非本文只從預設本文摘要排除，原文、分類理由、span 與雜湊全部保留。
- NLP-CORE 新增 `evidence_summarizer` 受控操作；仍為獨立零依賴大模組，由 SYSTEM-MANAGER 以明示 allow-list 路由。
- 115 項自動測試全數通過；其中 10 項為 v1.8 新回歸，v1.7 的 105 項全部保留。
- 兩份實際附件共 189,128 字元；本文 9/9 chunks、全文 10/10 chunks 均有代表點，證據 span／hash 全部通過，最長摘要點 745 字元，重複點 0。
- 實檔重建封裝兩次可重現，ZIP SHA-256 均為 `c264ec94021ea05ee30b196c191362314fddcdaa729face037fab76e02bb773b`。

發布日期：2026/09/08

## v1.7.0 增量升級

- 新增 `VIA_CONTENT_ROLE_ANALYSIS/1.0`，逐字分類本文、證據、程式、中繼資料、導覽、廣告、頁首頁尾、來源封裝與不確定內容。
- 新增完整階層式抽取摘要；`full_input_summary` 消費所有來源字元，`body_summary` 只排除高信心非本文，不確定內容保守保留。
- 新增本文修復投影與事實多重集合閘門；數字、金額、百分比、日期或單位不一致即回到原始本文，不回寫來源。
- 新增 `本文區`／`右資訊區`／文件邊界狀態；修正金融詞彙含「廣告」、財報期別及獨立數值被誤分類的問題。
- 新增 `VIA_MODULE_COMPOSITION_REGISTRY/1.0`，將 parameter、function、class、library 與 code fragment 依作用域、證據及依賴模組化。
- 新增 `VIA_SYSTEM_MANAGER/1.0` 與七個大型模組；`NLP-CORE` 保持零依賴獨立運作，SYSTEM-MANAGER 不包含領域邏輯。
- 新增 Python AST class contract，以及 JavaScript／TypeScript／PowerShell class 候選；抽取程式碼永不執行，不完整片段永不自動拼接。
- Mind Map 增加 macro module、composition module、component、dependency、candidate assignment 與 decision card 節點／關係。
- 105 項自動測試全部通過；兩份實際附件共 189,128 字元，來源與 Layout 均逐字可還原，完整摘要消費率 100%。
- 實檔識別 5,011 個內容單元；預設本文 162,928 字，非本文／側欄 26,200 字、2,212 單元，全部仍保留於來源與 non-body register。

發布日期：2026/09/08

## v1.6.1 增量修正

## v1.6.1 增量修正

- 新增研究報告檔名、`DUAL_ZONES`、本文區、右資訊區的無損布局邊界。
- 新增中文章節、數字章節及 `HTML`／`MD+` 等來源格式標記的切段。
- 提升不完整 Python 片段辨識，避免將運算式、`elif`、NumPy／Pandas 與函式呼叫誤判為 TOML 或 CSS。
- 新增 `fragment_classification`；不完整程式只標記為候選並送人工審核，絕不補寫或執行。
- 新增 Source Record 邊界與 59 組實際報告 `layout_group_id`，防止跨檔／跨報告錯接。
- 年份與布局 ID 不再作股票／文件語意錨點；ASCII alias 增加單字邊界與停用詞閘門。
- v1.6.0 的 10 個 CPU 工具與既有功能全部保留。

發布日期：2026/09/08

## 本版成果

- v1.5 所有欄位、21 組 provider 與既有重建能力完整保留，另加 10 組 CPU NLP provider；Provider Registry 總數增為 31。
- 新增 `VIA_CPU_NLP_AUGMENTATION/1.0`：Unicode 修復、編碼辨識、斷句、語言路由、模糊 alias、精確多模式關鍵字、近重複候選、圖譜驗證、合約序列化與壓縮詞典索引。
- 10 個 provider 均為 optional extra，未安裝時使用標準庫確定性後備；不在引擎啟動時 import，不自動安裝、下載或連網。
- `charset-normalizer` 必須同時通過 confidence 與 round-trip byte gate；亂碼修復候選若更動受保護事實即拒絕。
- MinHash／LSH 結果再以 exact Jaccard 驗證，且永不自動合併或刪除來源；RapidFuzz 結果永不自動升版 SSOT。
- NetworkX／後備 validator 只讀檢查 Mind Map 端點、循環、self-loop 與 orphan，不會靜默修改節點或關係。
- Reconstruction Package 新增 `VIA_CPU_NLP_Augmentation.json`，完整記錄每個後端、fallback、候選、信心與安全閘門。
- 85 項自動測試全部通過；本版兩份實際附件、189,128 字元產生 642 segments、97 topics、268 returns、2,084 knowledge units、90 tables 與 59 report groups，來源／Layout 皆可逐字重建。
- 真實語料完整 v1.6 重建約 10.27 秒，峰值 RSS 約 220,880 KB；圖譜缺失端點 0、來源改寫 0、自動去重刪除 0。

## v1.5.0 基線成果

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
