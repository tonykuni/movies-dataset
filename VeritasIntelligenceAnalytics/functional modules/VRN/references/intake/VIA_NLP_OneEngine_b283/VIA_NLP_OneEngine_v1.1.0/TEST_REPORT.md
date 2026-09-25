# VIA NLP One Engine 測試報告

報告版本：1.1.0  
測試日期：2026/08/27  
平台：Linux container、Python 3.12.13  
目標環境：Windows 11、PowerShell 7、Python 3.11+  

## 結論

核心引擎在最小依賴模式下可啟動。單元／整合測試共 24 項，全部通過；涵蓋通用文章、跳題對話無損重組、Topic Episode／復返鏈、內容完善帳本、雙層 Mind Map、AI typed graph、SSOT、程式依賴拓撲、ML／Tiny MLP challenger、三輪治理、分段翻譯記憶與 Google 網頁後端拒絕策略。深度模型未隨測試下載；已以固定向量驗證 Deep Semantic Graph 邏輯，但實際 Embedding／LLM 模型仍須在目標電腦另做容量與準確率測試。

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
Ran 24 tests
OK
```

## 驗收界線

- 已驗證：Tier 1／2 核心、無損知識重組、跳題復返、雙層 Mind Map、程式拓撲、ML／Tiny MLP 演化治理、翻譯後端邊界、快取、佇列、CLI。
- 尚需目標機驗證：實際 spaCy 語言模型、Sentence Transformers 模型、Ollama 模型、GPU／VRAM 行為與 FastAPI 選裝套件。
- Windows PowerShell 安裝腳本採非破壞預設；只有使用者明確傳入 `-ForceRecreate` 才重建專案內虛擬環境。
- 新虛擬環境的線上 editable install 因本測試容器禁止外部套件存取而未執行；已改做離線 `pyproject.toml` 與 CLI 結構驗證。目標機仍須執行 PowerShell 安裝腳本完成最終驗收。
