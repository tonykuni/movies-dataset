# VIA NLP One Engine 測試報告

報告版本：1.5.0  
測試日期：2026/09/01  
平台：Linux container、Python 3.12.13  
目標環境：Windows 11、PowerShell 7、Python 3.11+  

## 結論

核心引擎在最小依賴模式下可啟動。單元／整合測試共 58 項，全部通過；v1.5 新增 MarkItDown 安全入口、逐字 Markdown Layout、亂序脈絡重建、函式分類、程式模組模板、標準模板及 Provider Registry。深度模型與 MarkItDown 選裝套件未隨測試下載；實際 OCR、Embedding／LLM／Argos 與各選裝 provider 仍須在目標電腦另做容量、相容性與準確率測試。

批量壓力測試以 8 個呼叫執行緒衝擊引擎、引擎內部限制 2 個並行槽，連續處理 500 篇短文：0.958 秒、約 521.9 篇／秒，最大 RSS 增量約 3.06 MB。此數字只代表本測試機的 Tier 1／2 短文基準，不應外推到長文、Tiny MLP 訓練或深度模型。

## 測試矩陣

| 類別 | 項目 | 結果 |
|---|---|---|
| 通用文章 | `auto` 路由至完整文章分析 | PASS |
| 文字修復 | 高信心詞庫、重複標點、原稿與 diff | PASS |
| 文件類型 | 新聞與一般文章辨識 | PASS |
| 雙語 | 中英混合語言判定 | PASS（修正後） |
| 金融實體 | 2330.TW、日期、百分比；年份不誤判 ticker | PASS |
| 長文 | 固定上限、chunk overlap、終止條件 | PASS |
| 快取 | 第二次相同請求命中 SQLite cache | PASS |
| 斷點 | batch checkpoint resume | PASS |
| 回饋 | SQLite feedback 與最少樣本 gate | PASS |
| ML | HashingVectorizer + SGD candidate 訓練、驗證、升版 | PASS |
| 完整性 | active model manifest + SHA-256 | PASS |
| 稽核 | append-only hash chain 與竄改偵測 | PASS |
| 佇列 | submit → claim → complete 原子生命週期 | PASS |
| 編碼 | Big5 文章安全讀取 | PASS |
| OOM 安全 | Tier 3 未啟用時 fail closed | PASS |
| 無損重組 | segment ledger、來源 offset、SHA-256、逐字重建 | PASS |
| 跳題回接 | Topic Episode、switch、return link、jumpiness ratio | PASS |
| 內容完善 | refinement ledger、roles、changes、衍生雜湊、100% coverage | PASS |
| 知識體 | Body of Knowledge、Mind Map、SSOT、VIA Keyword | PASS |
| AI 圖譜 | typed nodes／edges、source join、derivative join | PASS |
| 程式治理 | AST、interface contract、dependency topology；抽取內容永不執行 | PASS |
| Mega-Prompt | 三輪、六管線、20 Accelerators、Zero-Hydra | PASS |
| 翻譯 | 分段、translation memory、code fence 保留 | PASS |
| 網頁邊界 | `google_web` 後端明確拒絕，不模擬繞行 | PASS |
| 併發壓力 | 8 呼叫執行緒、2 引擎槽、500 篇短文 | PASS |
| 封裝結構 | `pyproject.toml`、console script、10 組 extras | PASS |
| 實際 DOCX | 讀取附件 `NLP.docx` 58,753 字元並抽取 15 關鍵字 | PASS（7.782 ms） |
| ML 資料品質 | 去重、同文異標 fail closed、deterministic stratified validation | PASS |
| 神經 challenger | 兩層 Tiny MLP CPU 訓練、收斂狀態、champion 選擇 | PASS |
| Entity Anchor | 同 Ticker 跨跳題回接；不同 Ticker 抑制誤合併 | PASS |
| 事實完整性 | 金額／日期／代碼遭修改即 fail closed 回復逐字來源 | PASS |
| 結構表 | Markdown 表格逐格保真、來源行號、AI graph join、禁止靜默填值 | PASS |
| Gold Set | B-cubed、Topic Return PRF 與 candidate-only threshold calibration | PASS |
| 多檔輸入 | 確定排序、重複路徑去重、symlink 忽略、逐檔 extracted text hash 還原 | PASS |
| 知識物件 | 穩定 ID、重複 occurrence 合併、角色 registers 與 Evidence Matrix | PASS |
| 知識衝突 | 參數多值明列；explicit supersession 只提審查、不自動套用 | PASS |
| 程式版本 | exact duplicate／distinct revision／candidate family；禁止自動合併 | PASS |
| 程式介面 | symbol registry、dependency topology、ambiguous／unresolved call | PASS |
| 多語程式 | Python／PowerShell／JS／TS／JSON／SQL／HTML／XML／CSS／YAML／TOML／Bash | PASS |
| 交接封裝 | 10 個結果檔、原子寫入、ZIP 完整性及兩次可重現 hash | PASS |
| 指令還原 | prerequisite／requirement／decision／action／verification／prohibition 與來源鏈 | PASS |
| 命令還原 | PowerShell 續行、多次 occurrence 去重、不完整命令 fail closed、永不執行 | PASS |
| 雙語知識體 | `zh`／`en` 結構、未知內容保留來源並標記待翻譯 | PASS |
| Mind Map 3.0 | 中／英 human view、雙語 typed graph 與完整結構標籤 | PASS |
| 動態修正 | snapshot chain、node／edge delta、禁止靜默刪除與 canonical mutation | PASS |
| 穩定來源 ID | 新增較早排序檔案後，既有 Record ID 不位移 | PASS |
| 上一版安全讀取 | 未知 JSON shape 與超大 previous package fail closed | PASS |
| Markdown Layout | block／inline 類型、未知內容 fallback、逐字重建 | PASS |
| MarkItDown 邊界 | 未安裝 fail closed；本機檔案限定；plugins／LLM／URL 關閉 | PASS |
| 脈絡重建 | 文件模式、功能標籤、threads、reply candidates、未回答問題 | PASS |
| 函式分類 | 名稱、AST contract、calls、imports 與 dependency 證據 | PASS |
| 程式模板 | 完整 Source Record 模組、set JSON 化、禁止寫入與執行 | PASS |
| 標準模板 | source-filled slots、missing-slot proposal、禁止猜補 | PASS |
| Provider Registry | 20 組開發工具 + MarkItDown 唯讀盤點與安全策略 | PASS |

## v1.5 實際 HTML／Python 驗證

以本次附件 1 份 HTML 與 7 份 Python 執行正式 `reconstruct-bundle` 兩次；圖片未在缺少 MarkItDown／OCR 時被假定為文字。全程未使用網路、LLM、瀏覽器或執行附件程式碼。

| 指標 | 結果 |
|---|---:|
| Source Records／來源 bytes／合併文字 | 8／891,860／569,650 字元 |
| Segments／Topics／Topic Returns | 1,652／22／1,131 |
| Layout Blocks／逐字重建 | 5,548／100% |
| Code Source Modules／Invalid／Low-confidence | 8／0／0 |
| Classified Functions／Module Templates | 397／8 |
| Context Threads／Reply Candidates／Unanswered | 22／23／17 |
| Knowledge Units／待審衝突 | 2,000（設定上限）／284 |
| 自動程式合併／寫檔／執行 | 0／0／0 |
| 兩次可重現 reconstruction package SHA-256 | `a73b5edfee657c0aa3621b8e495370f55d7db74a08303c60aa839103987e3cc4` |

第一次實際全檔 AST 驗證找出 Python `set` 常值無法 JSON 序列化的缺陷；修正為 deterministic JSON array 並新增回歸測試後，完整流程通過。仍列為 review required 的項目是跨檔同名 symbol、未解析外部 calls 與 HTML lexical-only 驗證，沒有將它們假報為完成。

## v1.4 實際討論紀錄驗證

以附件 `貼上的 Markdown (2).md` 執行正式 `reconstruct-bundle`，並將 v1.3 的 `VIA_Knowledge_Full.json` 作為 `--previous-package`。全程未使用網路、LLM 或深度模型。

| 指標 | 結果 |
|---|---:|
| 原始檔／合併文字 | 149,489 bytes／108,681 字元 |
| Source Records／Segments | 1／169 |
| Topics／Returns | 6／157 |
| Knowledge Units／待審衝突 | 418／57 |
| Instructions | 61 |
| 唯一 Commands／Occurrences | 2／4 |
| Structured Tables | 88 |
| Code Blocks／Revision Families | 41／36 |
| 來源重建／事實完整性 | 100%／100% |
| 指令執行／自動 conflict resolution／自動 canonical mutation | 0／0／0 |
| Mind Map 版本鏈 | v1.3 legacy snapshot → v1.4 sequence 2 |
| 兩次可重現 reconstruction package SHA-256 | `223922942d330d72633667ffd5d891d2714fe4e689b79555403e85a81ec53000` |

## v1.3 整批使用者測試（基線）

以附件 `貼上的 Markdown (2).md` 透過正式 `reconstruct-bundle` CLI 執行兩次。原始檔 149,489 bytes，抽取文字 108,374 字元；加入來源紀錄信封後為 108,661 字元。兩次均未使用網路、LLM 或深度模型。

| 指標 | 結果 |
|---|---:|
| Source Records／Segments | 1／169 |
| Topics／Returns | 6／157 |
| Knowledge Units／待審衝突 | 418／57 |
| Structured Tables | 88 |
| Code Blocks／Revision Families | 41／36 |
| 無效程式片段／低信心語言 | 4／20，全部 review required |
| 來源重建／事實完整性 | 100%／100% |
| 自動衝突解決／自動程式合併／執行程式 | 0／0／0 |
| 單次引擎耗時 | 約 977.59 ms |
| 兩次結果 ZIP SHA-256 | `7e27ef1668add03faaa97e4433ad81c0f38405cfa3be0d6face5733a4bc19912` |

## v1.2 實際噪音語料驗證

使用附件 `貼上的 Markdown (2).md` 做 v1.1／v1.2 同資料對照；資料含高度跳題對話、重複程式碼與大量 Markdown 表格。此測試不使用網路、LLM 或深度模型。

| 版本 | 字元 | Segments | Topics | Returns | Graph Nodes | 結構表 | 逐字重建／整理覆蓋 | 事實輸出通過 | 耗時 | Max RSS |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| v1.1.0 | 108,374 | 169 | 10 | 153 | 343 | 不支援 | 100%／100% | 不支援 | 774.82 ms | 23,160 KB |
| v1.2.0 | 108,374 | 169 | 6 | 157 | 426 | 87 | 100%／100% | 100% | 975.65 ms | 24,228 KB |

Topics／Returns 數量是結構輸出，不等於品質分數；主題正確性必須用人工 Gold Set 的 B-cubed 與 Topic Return F1 驗收。v1.2 的新增安全與表格能力在本機約增加 200.83 ms 與 1,068 KB Max RSS。

## 實際附件驗證

三份高跳動、跨主題或長篇附件均通過 `source_ledger` 精確重建。以下時間為本容器的單次本地基準，沒有呼叫 LLM 或網路服務：

| 輸入 | 字元 | Segments | Topics／Episodes | Returns | Graph Nodes | 程式片段／介面 | 完善／整理覆蓋 | 精確重建 | 耗時 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `TEST MESSAGE(1).txt` | 125,949 | 277 | 11／119 | 108 | 408 | 0／0 | 100%／100% | PASS | 2,326.57 ms |
| `全球資金流動追蹤強度及力度及金額及理由.docx` | 105,619 | 130 | 29／77 | 48 | 237 | 24／4 | 100%／100% | PASS | 1,638.16 ms |
| `大盤是多頭空頭轉折盤整(1).docx` | 28,519 | 54 | 14／36 | 22 | 105 | 3／0 | 100%／100% | PASS | 423.60 ms |

「精確重建」只聲明來源完整性，不代表衍生摘要或分類一定正確。所有整理結果都保留 segment reference，供人工查核與回溯。

## 實際測試指令

```text
python scripts/run_tests.py
```

```text
Ran 58 tests
OK
```

## 驗收界線

- 已驗證：Tier 1／2 核心、無損知識重組、指令／命令還原、跳題復返、雙語 Mind Map 3.0、動態版本差異、程式拓撲、ML／Tiny MLP 演化治理、翻譯後端邊界、快取、佇列、CLI。
- 尚需目標機驗證：實際 spaCy 語言模型、Sentence Transformers 模型、Ollama 模型、GPU／VRAM 行為與 FastAPI 選裝套件。
- Windows PowerShell 安裝腳本採非破壞預設；只有使用者明確傳入 `-ForceRecreate` 才重建專案內虛擬環境。
- 新虛擬環境的線上 editable install 因本測試容器禁止外部套件存取而未執行；已改做離線 `pyproject.toml` 與 CLI 結構驗證。目標機仍須執行 PowerShell 安裝腳本完成最終驗收。
