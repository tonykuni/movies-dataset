# VIA NLP OneEngine v1.9.0

這次先讀取既有成品原始碼，再把附件的文字前處理與語料去重功能接到同一個 Python 入口。

## 查到的既有版本

| 成品 | 可確認日期 | 本次採用範圍 |
|---|---|---|
| VIA_NLP_Application_System v1.8.0 | 2026-09-08 | 原始套件完整內嵌；摘要證據、知識體、主題重組、程式片段分析、31 組選配 provider 註冊與原 CLI 保留 |
| MarkdownEditingEngine v1.4.0 FINAL | 2026-09-12 | 接入 Python 文字／表格結構分析；附外觀快照模組與規則來源。Node／Rust／Go 格式化工具鏈未搬進新預設流程 |
| 本次附件「貼上的文字 (1).txt」 | 2026-09-27 台北時間 | 作為功能需求及缺陷案例；沒有直接執行附件裡的程式 |

「最新」指本次在既有檔案中找到的最高 NLP 成品版本；沒有宣稱已核對所有 GitHub 分支或使用者 Windows 磁碟。

## 單檔的具體含義

`VIA_NLP_OneEngine_v1_9_0.py` 是唯一 Python 入口。新功能以完整 `def` 分段，參數集中在檔首 `DEFAULTS`。

為保留 v1.8 的功能與匯入關係，單檔內嵌經 SHA-256 核對的來源封包；第一次使用舊版分析／Markdown 分析時，會將 73 個來源及設定檔展開到結果目錄內。後續載入前逐檔核對；若發現檔案被改動，明確停止，不靜默覆蓋。這是單一分派入口，並未將數十個來源模組硬接成同一個 Python 命名空間。

核心只需 Python 3.11+ 標準庫；模型權重不包含在本包。`embedded_sources` 提供可讀來源，`nlp_build` 提供建置模板與回歸測試。

## 已整合的工作

| 功能 | 行為與限制 |
|---|---|
| 中英標點、全形英文字母、控制字元 | 正文依上下文修復；金融數值、代碼、URL、程式碼、表格先保護。全形數字與歧義數字標點預設保留 |
| PDF 複製文字斷行 | `unwrap=true` 才開啟；只合併符合長行及句界規則的文字。沒有 PDF BBox 時不猜欄序，不保證還原原版面 |
| 巢狀引號 | 配對成功且包含中文才轉為「」／『』；英文撇號及不完整引號保留 |
| 斷句、RAG 切塊 | 預設規則斷句；每塊保存 processed_text 的字元範圍與 SHA-256。超長無標點句可硬切；程式碼等不可分割區塊可超限，但明示 oversize |
| 常見個資遮罩 | 明確開啟 `redact=true`；檢查台灣一般身分證檢查碼，遮罩手機與 Email。遮罩結果不含原文／原始 CSV、JSON metadata；這不是完整 PII 偵測模型 |
| 既有 NLP 分析 | `process` 預設同時使用 v1.8 的 analyze；`--analysis-task knowledge` 加入知識體、摘要證據、主題及程式重建。新文字修復投影與舊版來源分析分開保存 |
| Markdown 結構分析 | `--markdown-analysis` 接入既有 v1.4 的標題／段落／表格／風險檢查 |
| TXT／MD／CSV／TSV／JSONL 批次 | JSONL 與 CSV 逐筆讀取；有界 worker 批次、單一 SQLite 寫入者、錯誤列明示。CSV 僅處理指定文字欄，輸出為可追溯 JSONL 記錄，不會重寫原 CSV |
| 增量與續跑 | 依來源內容、metadata、版本、設定雜湊重用結果。重跑會重新掃描輸入，以避免檔案變更後誤跳過；不是盲目從舊位元組位置續接 |
| 去重 | SQLite 保存原始列與 LSH band 索引；候選使用原始 shingle 集合計算精確 Jaccard，並要求數值序列一致 |
| 去重投影 | 完全相同文字可分流；近似文字預設 NEAR_REVIEW 且仍在 retained.jsonl。只有設定 `near_action=project` 才將已驗證近似文移至 duplicates.jsonl；兩邊與原始輸入都保留 |
| 報告 | 暖白、小字、分頁矩陣 HTML；右上角可匯出 MD／JSON。這是離線結果報告，不是已接上母系統的即時管控伺服器 |

批次使用有界執行緒池；1 與 4 worker 已核對結果一致。沒有宣稱 CPU 純 Python 規則能藉執行緒等比例加速。模型流程會強制單 worker，以避免重複載入重型權重。

## 模型接點

| 接點 | 設定 | 狀態 |
|---|---|---|
| FunASR ct-punc | `punc_model` 本地完整模型目錄 | 已撰寫接點；未用真實權重推論驗證 |
| wtpsplit-lite SaT | `sat_model` 本地模型目錄 | 已撰寫接點；輸出需逐字覆蓋；不符合時退回規則斷句並標 REVIEW |
| CKIP Transformers WS | `ckip_model` 本地 WS checkpoint 與 tokenizer 目錄 | 已撰寫接點；本次未增加新的 POS／NER 接點 |
| OpenCC s2twp | `s2twp=true` | 選配投影；套件缺失會標 REVIEW |
| Jieba | `tokenizer=jieba` | 選配分詞；預設 Unicode token 切割不冒稱語言學斷詞 |
| pycorrector MacBERT | `spell_model` 本地目錄 | 僅產生建議，不自動改寫專有名詞或研究判斷 |

這次未安裝上述選配模型套件或下載權重。`health` 的 INSTALLED_NOT_VALIDATED 只代表套件可發現，不代表模型可用。已設定但無法載入的 provider 會在記錄標 REVIEW。啟用模型前檢查可用記憶體，Windows 缺 psutil 時會明示需要監測套件。模型 RAM 門檻在 `DEFAULTS.model_min_available_mb`。

附件中須更正的敘述：

- SaT 的主要工作是句子邊界切分，不能當成 ct-punc 的補標點替代品。
- deepmultilingualpunctuation 預設 FullStop 模型列的是英、法、德、義等語言，不能據此宣稱支援中文。
- ct-punc 的中英補標點能力，不等於本包已驗證英文 true-casing 或財經文字準確率。
- MinHash 相似度是估計；本版最後驗證使用真正的 shingle 集合 Jaccard。
- 串流讀入不等於總索引固定 RAM。原附件的 set／dict 仍隨文件數增加；本版改放 SQLite，但磁碟使用量仍隨語料增加。
- LSH 碰撞只是候選，不應直接刪文；即使通過 Jaccard，近似文本仍可能有語意差異，所以預設保留送審。

官方參考：

- https://github.com/modelscope/FunASR
- https://huggingface.co/funasr/ct-punc
- https://github.com/superlinear-ai/wtpsplit-lite
- https://github.com/ckiplab/ckip-transformers
- https://github.com/oliverguhr/deepmultilingualpunctuation
- https://ekzhu.com/datasketch/lsh.html

## Windows 一次啟動

將 ZIP 解壓縮後，在 PowerShell 執行：

```powershell
& '.\Launch-VIA-NLP.ps1'
```

會先建立／進入 `via_nlp_v190` 專用環境，再跑 34 項內建測試，最後開啟矩陣。需已有 Python 3.12 與 uv 或 py launcher；不會下載 Python，也不會更改全域套件。沒有 `exit` 或 `Stop-Process`，不關閉 PowerShell。

帶入實際 TXT／MD 或文字資料夾：

```powershell
& '.\Launch-VIA-NLP.ps1' -InputPath 'C:\Data\研究文字'
```

PDF／DOCX 的來源抽取功能仍由完整保留的 `legacy` 入口提供，依舊版套件需求安裝選配文件依賴；本次未新增 OCR 模型，也沒有將掃描檔 OCR 列為通過。

## Python 指令

先啟用自己的 `via_` 環境，再執行以下指令。所有命令共用同一支 PY：

```text
python VIA_NLP_OneEngine_v1_9_0.py health
python VIA_NLP_OneEngine_v1_9_0.py self-test --output .\selftest
python VIA_NLP_OneEngine_v1_9_0.py process --file .\article.md --output .\result --markdown-analysis --analysis-task knowledge
python VIA_NLP_OneEngine_v1_9_0.py batch --input .\raw --output .\cleaned
python VIA_NLP_OneEngine_v1_9_0.py dedup --input .\corpus.jsonl --output .\dedup
python VIA_NLP_OneEngine_v1_9_0.py legacy -- providers
python VIA_NLP_OneEngine_v1_9_0.py legacy -- process --task knowledge --file .\article.docx
```

JSON 設定覆寫範例（僅有需要改的參數）：

```json
{
  "encoding": "utf-8-sig",
  "unwrap": true,
  "chunk_chars": 800,
  "overlap_chars": 80,
  "csv_cols": ["title", "content"],
  "workers": 4,
  "keep": "longest",
  "near_action": "review"
}
```

```text
python VIA_NLP_OneEngine_v1_9_0.py --config settings.json batch --input .\raw --output .\cleaned
```

CP950 檔案請明確設 `encoding=cp950`。不會以 replacement character 靜默吞掉解碼錯誤。JSONL 去重輸入固定 UTF-8，壞行保存在 errors.jsonl 與 SQLite 原始列。

## 檢驗證據與實際限制

- 原 v1.8 套件：115 項測試通過。
- 新單檔核心：34 項測試通過。
- 整合及故障案例：34 項回歸通過；包含強制 LSH 碰撞、禁止遞移錯合併、最長代表、候選上限、預設近似送審與隱私輸出。
- 56 個內嵌 Python 檔案：AST 與 compile 通過。
- 實際附件 77,493 字元完成修復投影、切塊、Markdown 分析與既有 knowledge 分析；數值守門通過。引號與數字標點有歧義，結果為 REVIEW，不是無條件 PASS。
- HTML 的 JavaScript 語法檢查通過；環境沒有 Chromium 可執行檔，未完成瀏覽器視覺及點擊驗收。
- 尚未在使用者 Windows 執行、尚未用真實權重驗證模型、尚未跑 50GB 效能壓測；不宣稱大模型準確率、吞吐量或完成中央治理／GitHub 部署。
- 一個 JSONL record 與單篇文字仍受 `max_record_bytes`／`max_chars` 限制；過大時明確停止／列 ERROR。大型 corpus 指很多有界 record，並非單行 50GB。
- 批次 SQLite 會保存處理結果；去重 SQLite 另外保存原始 JSONL，磁碟容量須足夠。LSH 有漏召回可能，候選超過上限標 REVIEW，不假稱查全。
- 所有原始輸入不覆寫。每次結果在新的 run 目錄，檢查點可重用；同一輸出位置由作業系統檔案鎖限制單一寫入者。

若要重建單檔，在交付包根目錄執行 `python nlp_build/build.py`；產物會放在 `deliverables` 子目錄。執行 `python nlp_build/regression.py` 可重跑整合測試。保留原始 ZIP 是為了重建與來源稽核。
