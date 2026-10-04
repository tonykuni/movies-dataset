# VIA NLP Application System 測試報告

報告版本：1.8.0  
測試日期：2026/09/08  
平台：Linux container、Python 3.12.13  
目標環境：Windows 11、PowerShell 7、Python 3.11+  

## 結論

核心系統在最小依賴模式下可啟動。單元／整合測試共 115 項，全部通過；v1.8.0 保留 v1.7.0 的 105 項契約，另增證據型完整摘要、超長無標點有界切割、跨 chunk 代表性、逐點原文雜湊、分類政策與版面區域轉換稽核。深度模型、MarkItDown 與部分 CPU 選裝套件未在測試環境下載；DOCX 實檔採標準 OOXML 後備路徑。OCR、MarkItDown 實際轉換、Embedding／LLM／Argos 與全部 provider 在目標 Windows 電腦上仍需另做容量、相容性與準確率驗收。

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
| CPU Provider Registry | v1.5 的 21 組不減；新增 CPU01–CPU10；總數 31 | PASS |
| Unicode 修復閘門 | 受保護數字變更即拒絕；候選永不自動套用 | PASS |
| 編碼候選 | confidence + byte round-trip；低信心走確定性後備 | PASS |
| 中英文斷句／語言路由 | BlingFire／Lingua 缺件仍有有界後備；mixed 不被覆蓋 | PASS |
| SSOT 比對 | RapidFuzz 候選不升版；Aho-Corasick exact offset | PASS |
| 近重複偵測 | LSH candidate + exact Jaccard；不合併、不刪除 | PASS |
| Mind Map 驗證 | 缺失 endpoint fail-to-review；圖譜不被修改 | PASS |
| JSON／詞典加速 | msgspec round-trip gate；MARISA index 可重建 | PASS |
| 向後相容 | v1.5 Knowledge output keys 全部為 v1.6 子集合 | PASS |
| 完整摘要 | 非重疊 chunk span、逐塊 hash、全部字元消費、禁止靜默截斷 | PASS |
| 本文／非本文 | 廣告、導覽、來源封裝、頁首頁尾、聯絡欄、側欄與不確定內容 | PASS |
| 金融防誤判 | 「廣告支出」、電子紙廣告看板、12/25、3/26、獨立表格數值 | PASS |
| 修復投影 | NFKC 後數值／單位多重集合一致才採用；來源永不回寫 | PASS |
| 模組組合 | code／parameter／function／class／library 作用域、依賴與衝突 | PASS |
| 七大模組 | NLP-CORE 獨立；SYSTEM-MANAGER 僅整合、無領域邏輯 | PASS |
| 安全路由 | 只呼叫程式內註冊 handler；動態 import 與未知 action fail closed | PASS |
| v1.6.1 相容 | v1.6.1 Knowledge output keys 全部保留於 v1.7 | PASS |
| 證據型摘要 | 逐點 source span／SHA-256／chunk ID／語言／選取理由 | PASS |
| 摘要長度上限 | 超長無標點輸入仍保證每點有界 | PASS |
| Chunk 代表性 | 預算足夠時所有有效 chunk 均有最終摘要點 | PASS |
| 分類稽核 | fail-closed 政策、閾值、區域轉換、留存／排除率 | PASS |
| v1.7 相容 | v1.7 的 105 項測試契約全部保留 | PASS |

## v1.8.0 實際完整摘要與證據驗證

以附件 `fetched text to be fixed..txt` 與 `對話紀錄20260708.docx` 執行兩次正式 `reconstruct-bundle`。DOCX 使用標準 OOXML 本機後備抽取；全程未使用網路、LLM、瀏覽器或執行抽取程式碼。

| 指標 | 結果 |
|---|---:|
| Source Records／合併文字 | 2／189,128 字元 |
| 來源／Layout 精確重建 | PASS／PASS |
| 全文／本文摘要輸入消費 | 100%／100% |
| 本文／全文 chunks | 9／10 |
| 有代表點 chunks | 9/9／10/10 |
| 本文／全文摘要點 | 12／12 |
| 逐點 evidence span／hash | PASS／PASS |
| 最長摘要點／上限 | 745／900 字元 |
| 重複摘要點 | 0 |
| 版面區域轉換軌跡 | 186 |
| 內容單元／本文／非本文 | 5,011／2,799／2,212 |
| 本文投影／非本文保留 | 162,928／26,200 字元 |
| Segments／Topics／Returns | 642／97／268 |
| Knowledge Units／Tables／Instructions | 2,084／90／355 |
| 非本文刪除／來源回寫／程式執行 | 0／0／0 |
| 兩次實檔 ZIP SHA-256 | `c264ec94021ea05ee30b196c191362314fddcdaa729face037fab76e02bb773b` |

「逐點 evidence PASS」表示每個摘要點的 span 均能逐字取回原文，且獨立重算 SHA-256 一致。這證明可追溯性與完整消費，不等於語意摘要已達人工 Gold Set 的「完美」；實際準確率仍需人工標註來計算 precision／recall。

## v1.7.0 實際完整摘要與非本文驗證

以附件 `fetched text to be fixed..txt` 與 `對話紀錄20260708.docx` 執行正式 `reconstruct-bundle`。DOCX 使用標準 OOXML 本機後備抽取；全程未使用網路、LLM、瀏覽器或執行抽取程式碼。

| 指標 | 結果 |
|---|---:|
| Source Records／合併文字 | 2／189,128 字元 |
| 來源／Layout 精確重建 | PASS／PASS |
| 完整輸入摘要消費率／靜默截斷 | 100%／0 |
| 內容單元／本文單元／非本文單元 | 5,011／2,799／2,212 |
| 本文投影／非本文保留 | 162,928／26,200 字元 |
| 版面標記／明示側欄 | 565／1,479 單元 |
| 作者聯絡／廣告／頁碼 | 137／6／10 單元 |
| 修復投影事實閘門／摘要採用 | PASS／是 |
| Segments／Topics／Returns | 642／97／268 |
| Knowledge Units／Tables／Instructions | 2,084／90／355 |
| 大型模組／組合模組／元件 | 7／6／6 |
| Python fragments／不完整待審 | 6／3 |
| 非本文刪除／來源回寫／程式執行 | 0／0／0 |
| 實際重建 ZIP SHA-256 | `7a2a8b4de6ef199c702d7e648f7c2c44159d3aa4f76be38ed20912b33850eeb8` |

「非本文」代表不進入預設本文摘要，不代表刪除；每項都保留來源文字、span、SHA-256、角色與理由，且完整輸入摘要仍消費全部 189,128 字元。`review_blocks=0` 只表示這份實際資料沒有低信心未知類型，並不表示語意分類已達人工 Gold Set 的完美準確率。

## v1.6.1 實際雜亂報告／對話驗證

以附件 `fetched text to be fixed..txt` 與 `對話紀錄20260708.docx` 執行正式 `reconstruct-bundle`。全程未使用網路、LLM 或執行抽取程式碼。

| 指標 | v1.6.0 | v1.6.1 |
|---|---:|---:|
| 合併文字 | 189,128 | 189,128 |
| Segments | 38 | 642 |
| Topics／Returns | 2／1 | 97／268 |
| Report layout groups | 0 | 59 |
| Knowledge Units | 323 | 2,084 |
| Mind Map Nodes／Edges | 580／681 | 3,778／6,056 |
| Code languages | TOML 5、CSS 1（誤判） | Python 6 |
| Python AST 可解析／不完整待審 | 0／6 | 3／3 |
| 精確 alias／近重複候選 | — | 3,726／2，均未截斷 |
| 來源／Layout 逐字重建 | PASS／PASS | PASS／PASS |
| 未解主題容量桶 | — | 0 |

兩段標點完善候選因可能改動 `NT$650` 與 URL 的受保護事實而自動退回原文。12 組參數衝突、52 個未回答問題與 3 段不完整 Python 片段仍明確保留在 review queue，沒有假裝自動修好。

## v1.6 真實 HTML／Python 驗證

以附件 1 份 HTML 與 7 份 Python 執行完整 Knowledge 重建。全程未使用網路、LLM、瀏覽器或執行附件程式碼。

| 指標 | 結果 |
|---|---:|
| Source Records／合併文字 | 8／569,650 字元 |
| Segments／Topics／Topic Returns | 1,652／22／1,131 |
| 來源／Refinement／Organized／Layout | 100%／100%／100%／100% |
| Functions／Module Templates | 397／8 |
| Mind Map Nodes／Edges | 6,271／4,000（設定上限） |
| CPU providers／本環境可用 | 10／1 (`charset-normalizer`) |
| Graph missing endpoints／Contract round-trip | 0／PASS |
| 自動來源改寫／自動合併刪除 | 0／0 |
| 完整重建時間／峰值 RSS | 約 10.27 秒／220,880 KB |

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
Ran 105 tests
OK
```

## 驗收界線

- 已驗證：Tier 1／2 核心、無損知識重組、指令／命令還原、跳題復返、雙語 Mind Map 3.0、動態版本差異、程式拓撲、ML／Tiny MLP 演化治理、翻譯後端邊界、快取、佇列、CLI。
- 尚需目標機驗證：實際 spaCy 語言模型、Sentence Transformers 模型、Ollama 模型、GPU／VRAM 行為與 FastAPI 選裝套件。
- Windows PowerShell 安裝腳本採非破壞預設；只有使用者明確傳入 `-ForceRecreate` 才重建專案內虛擬環境。
- 新虛擬環境的線上 editable install 因本測試容器禁止外部套件存取而未執行；已改做離線 `pyproject.toml` 與 CLI 結構驗證。目標機仍須執行 PowerShell 安裝腳本完成最終驗收。
