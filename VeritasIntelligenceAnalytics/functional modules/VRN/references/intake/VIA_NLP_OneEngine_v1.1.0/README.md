# VIA NLP One Engine

VIA NLP One Engine 是一套以一般 CPU／RAM 為優先的本地 NLP 單一入口。它能處理任何文章或文字，不限定會議紀錄；預設只啟動低資源規則與機器學習元件，較重的 spaCy、Embedding 與 Ollama 只在路由需要、設定允許且資源閘門通過時載入。

## 已完成能力

- 任意文章：一般文章、新聞、研究內容、報告、投資討論、逐字稿與中英混合文字。
- 通用文字修復：編碼、控制字元、空白、重複標點、SSOT 詞庫、高信心錯字、原稿／修復稿／差異。
- 文章分析：自動文件類型、語言、關鍵字、規則／ML 分類、實體、摘要、重點、待辦與決策。
- 跳題對話重組：CPU 稀疏階層語意、時間／發言者／標題／code fence 分段、Topic Episode 與跨段復返鏈，原始 segment ledger 可逐字重建。
- 內容完善：來源帳本與 refinement ledger 分層；完善稿包含高信心修復、角色、語意單元、改動與雜湊，不覆蓋原文。
- 知識體：Body of Knowledge、供人閱讀的階層 Mind Map、供 AI 使用的 typed knowledge graph、SSOT／Regex 候選與 VIA Keyword。
- 程式整合藍圖：抽取 Python／PowerShell／JavaScript／TypeScript／JSON，建立函式介面、參數、呼叫依賴、拓撲順序、循環與 Hydra 風險。
- 分段翻譯：Argos 離線、本機 Ollama 或 Google Cloud API；含 translation memory、原文 hash 與 code fence 保留。
- 四級任務路由：Tier 1 規則與輕量 ML、Tier 2 結構化抽取、Tier 3 Embedding、Tier 4 本地 LLM。
- 資源安全：RAM／CPU 閾值、重型任務准入、模型 TTL、LRU 卸載、單機併發閘門、LLM 串行鎖。
- 加速：HashingVectorizer、增量 `partial_fit`、SQLite WAL 快取、自適應批次、斷點續跑。
- 受治理的自動進化：去重與標籤衝突檢查 → 分層驗證 → 線性 SGD champion／CPU 小型神經網路 challenger → Macro-F1 與退化閘門 → SHA-256 升版。
- 長任務：原子檔案佇列、pending／processing／completed／failed、重試與殭屍任務復原。
- 治理：輸入雜湊、敏感資訊遮罩、append-only JSONL、SHA-256 hash chain。
- 入口：Python API、CLI、FastAPI（選裝）、Windows PowerShell 一鍵安裝。

## 四級路由

| Tier | 預設工作 | 主要元件 | 資源策略 |
|---|---|---|---|
| 1 | 正規化、修復、關鍵字、分類、抽取式摘要 | Python 規則、可選 Jieba、Scikit-learn | 常駐輕量 |
| 2 | 文章結構化、跳題重建、NER、知識圖譜 | CPU Sparse Semantics、Regex NER、可選 spaCy | 有界特徵、延遲載入 |
| 3 | Embedding／深度語意關聯／語義檢索／離線翻譯 | Sentence Transformers、ONNX Runtime、Argos | 明確啟用、資源准入 |
| 4 | 生成摘要、複雜結構化、對話 | 本地 Ollama 量化模型 | 明確啟用、單路推論、完成即卸載 |

Tier 3 與 Tier 4 預設關閉。引擎不會自行下載模型，也不會因缺少深度套件而拖垮 Tier 1／2。

## 最快開始

Python 3.11+：

```powershell
cd VIA_NLP_OneEngine
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ml,monitor]"
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\default.json health
```

分析任何文字：

```powershell
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\default.json process `
  --task auto `
  --text "台積電 2330.TW 今日公布營收，市場關注 AI 投資。"
```

分析檔案：

```powershell
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\default.json process `
  --task auto `
  --file "C:\Data\article.docx"
```

支援一般文字、Markdown、JSON／JSONL、CSV／TSV、HTML／XML、YAML、TOML、INI、Python、PowerShell、JavaScript／TypeScript、SQL、DOCX；PDF 需安裝 `documents` extra。文字解碼依序嘗試 UTF-8、Big5／CP950、GB18030，最後才以替代字元安全讀取。

## Windows 一鍵安裝

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\Install-VIA-NLPOneEngine.ps1 -InstallProfile ml -RunTests
```

`minimal` 不裝額外套件；`api` 加入 FastAPI；`ml` 加入監控與增量機器學習；`full` 加入所有選裝能力，但仍不下載模型。

## Python API

```python
from via_nlp_engine import ProcessRequest, VIAEngine

with VIAEngine("config/default.json") as engine:
    result = engine.process(
        ProcessRequest(
            text="任何中英文文章都可以在這裡分析。",
            task="auto",
            quality="balanced",
        )
    )
    print(result.to_dict())
```

### 主要任務

- `auto`／`analyze`：通用文章完整分析。
- `reorganize`：跳題對話無遺漏切割與主題重組。
- `knowledge`：Body of Knowledge + Mind Map + SSOT + VIA Keyword + code blueprint。
- `govern`：依 `config/governance.json` 產生三輪分析、六管線、20 加速器與 Hydra Matrix。
- `translate`：分段翻譯與翻譯記憶；不支援非正式 Google 網頁自動貼上。
- `repair`：高信心文字修復、原稿、修復稿與差異。
- `normalize`：字元與標點正規化。
- `keywords`：關鍵字。
- `classify`：受治理 ML 或規則 fallback。
- `entities`：日期、金額、百分比、台股代碼等；可選 spaCy。
- `structure`：任意文章結構化。
- `summarize`：預設抽取式；啟用 Tier 4 後可使用本地 LLM。
- `embed`：可選本地 Embedding。
- `chat`：可選 Ollama。
- `restore_transcript`：舊名稱相容入口，底層仍使用通用 `structure`。

## 跳題對話 → Body of Knowledge

```powershell
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\default.json process `
  --task knowledge `
  --file "C:\Data\mixed_dialogue.txt"
```

核心輸出：

- `source_ledger`：每段原文、segment ID、字元起訖與 SHA-256。
- `refinement_ledger`：每段完善稿、角色、語意單元、修改紀錄、來源及衍生雜湊。
- `completeness`：原文字數、重建字數、coverage ratio、完整原文 hash。
- `dialogue_flow`：原始時間線、主題切換、復返鏈與跳動比例。
- `body_of_knowledge.organized_sections`：主題 Episode、原文、完善稿、摘要、Requirements／Decisions／Questions／Issues／Actions／Parameters。
- `mind_map`：`VIA_MIND_MAP_JSON/2.0`；同時提供 human tree 與 `VIA_KNOWLEDGE_GRAPH/2.0` AI nodes／edges。
- `ssot_dictionary`：canonical／aliases／安全 literal regex／衝突／人工升版狀態。
- `via_keywords`：治理、NLP、工程、金融、工作流與文件新發現詞。
- `code_registry`：語言、AST／語法、函式、類別、參數、來源與風險。
- `code_integration_blueprint`：`VIA_ENGINE_BLUEPRINT/2.0`，含 interface contracts、參數衝突、依賴拓撲與 build stages；預設 `execution_authorized=false`。

重組層不取代原文。即使 optimized view 或 Mind Map 有錯，仍可用 `source_ledger` 逐字還原輸入。

### CPU 知識重組參數

所有門檻都在 `config/default.json` 頂層集中管理：

```json
{
  "knowledge": {
    "max_segment_chars": 8000,
    "topic_threshold": 0.18,
    "topic_merge_threshold": 0.31,
    "max_topics": 40,
    "max_features_per_segment": 96,
    "max_ai_graph_edges": 4000,
    "deep_similarity_threshold": 0.62
  },
  "ml": {
    "auto_evolve_every_feedback": 50,
    "auto_promote": false,
    "neural_min_samples": 200,
    "neural_hidden_layers": [128, 32],
    "evolution_estimated_ram_mb": 512
  }
}
```

`topic_threshold` 越低越容易把隔很遠的對話回接；`topic_merge_threshold` 越高越不易把相近主題過度合併。即使主題被合併，Episode、segment ledger 與 AI graph 仍保留原始細節。

## VIA Central Governance Console 對齊

`config/governance.json` 已將 Mega-Prompt 轉為機器可讀治理契約：

- 最多三輪：全面分析 → 拓撲順序 → 收尾硬化。
- 六管線：Code AST、SSOT／Regex、模組解耦、效能、沙盒驗證、UI Matrix。
- 20 Accelerators：每個均有 implementation mapping，避免只列名稱不落地。
- 四區矩陣：`MODULE`／`ENGINE`／`FUNCTION-LIB`／`OTHERS`。
- Zero-Hydra：不可信對話中的程式碼只解析，不執行；高風險變更必須人工授權。
- PowerShell：有 `pwsh` 時使用正式 PowerShell AST Parser；沒有時標示 lexical fallback，不假裝完整 AST 驗證。

治理任務：

```powershell
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\default.json process `
  --task govern `
  --file "C:\Data\mixed_prompt_and_code.md"
```

## FastAPI

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[api,ml,monitor]"
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\default.json serve
```

預設僅綁定 `127.0.0.1:8765`：

- `GET /health`
- `POST /v1/process`
- `POST /v1/batch`
- `POST /v1/feedback`
- `POST /v1/evolve?promote=false`
- `GET /v1/models`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`

若要網路存取，必須明確開啟 `security.allow_remote_bind`、啟用 API key，並在反向代理層加 TLS、來源限制與請求大小限制。

## 受治理的持續學習

1. 使用 `feedback` 儲存已確認分類標籤。
2. 每 50 筆回饋可自動觸發 candidate evaluation；頻率由 `ml.auto_evolve_every_feedback` 控制。
3. 先拒絕重複過多與同文異標，再做 deterministic stratified validation。
4. HashingVectorizer + SGDClassifier 是常態 champion；達到 200 個唯一樣本後，另訓練兩層 CPU Tiny MLP challenger。
5. 神經網路未收斂時只列報告，不可勝出；候選還必須通過 Macro-F1、balanced accuracy、相對退化與檔案雜湊。
6. `ml.auto_promote` 預設為 `false`；只有明確允許且全部品質閘門通過時才替換 active model。

這裡的「自動進化」是資料、特徵、模型 challenger 與版本的受控更新，不是讓程式自行改寫原始碼或讓 LLM 自行部署。

## 深度模型啟用

在複製的設定檔中調整：

```json
{
  "routing": {
    "allow_deep_models": true,
    "allow_llm": true
  },
  "deep": {
    "local_files_only": true,
    "ollama_keep_alive": "0"
  }
}
```

- `local_files_only=true` 可防止 Sentence Transformers 靜默下載。
- `knowledge`／`reorganize`／`govern` 搭配 `quality=deep` 時才載入 Embedding，為 topic graph 加上深度語意關係；向量只在記憶體使用，不寫入結果。
- Ollama `keep_alive="0"` 會要求每次生成後立即卸載模型，節省 RAM／VRAM；批次推論若重視速度，可改成短時間如 `"2m"`。
- CPU 主機建議先使用較小的 Embedding 模型；`bge-m3` 是選裝示例，不代表每台機器都適合。
- 不應把 FP16／FP32 大模型與多個 NLP 模型同時常駐一般電腦。

## 中↔英分段翻譯

### 建議 1：Argos Translate 離線

先安裝 `translate` extra，並由使用者明確安裝所需的 `.argosmodel` 語言包；引擎不會在背景自行下載模型。複製設定檔並啟用：

```json
{
  "routing": {"allow_deep_models": true},
  "translation": {
    "enabled": true,
    "default_backend": "argos",
    "source_language": "zh",
    "target_language": "en",
    "max_chunk_chars": 4500,
    "preserve_code": true
  }
}
```

```powershell
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\local.json process `
  --task translate --backend argos --source-language zh --target-language en `
  --file "C:\Data\article.txt"
```

### 建議 2：本機 Ollama

需同時啟用 `routing.allow_deep_models=true` 與 `routing.allow_llm=true`，並安裝可處理繁體中文的本地模型。使用 `keep_alive="0"` 時每段完成後釋放模型；大量翻譯可調成短 TTL 以減少反覆載入。

### Google Cloud Translation

Cloud Translation 是正式可程式化的 Google 翻譯路徑，需要啟用 billing、API 與 authentication。引擎預設離線，因此每次使用還必須明確傳入 `--allow-network`。官方建議單次約 5,000 code points；本引擎預設 4,500 字元，保留安全餘裕與段落對照。

```powershell
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
.\.venv\Scripts\python.exe -m via_nlp_engine --config config\local.json process `
  --task translate --backend google_cloud --source-language zh-TW --target-language en `
  --allow-network --file "C:\Data\article.txt"
```

免費的 Google Translate 網頁適合人工互動，但本專案不以瀏覽器模擬貼上／複製來繞過正式 API、配額或計費。這種自動化容易受驗證碼、DOM 改版與使用限制影響，不能作為穩定引擎依賴。

## 設定覆寫

所有參數集中於 `config/default.json`。可複製後修改，或以環境變數覆寫：

```powershell
$env:VIA_NLP__RESOURCES__SHED_RAM_PERCENT = "82"
$env:VIA_NLP__ENGINE__MAX_CONCURRENCY = "1"
```

雙底線代表設定層級。API key 僅從 `VIA_NLP_API_KEY` 讀取，不寫入設定或稽核紀錄。

`examples/api_requests.json` 另提供 `knowledge`、`govern` 與本地分段翻譯的完整 JSON request 範例，可直接作為 `/v1/process` body 的起點。

## 測試

```powershell
.\.venv\Scripts\python.exe scripts\run_tests.py
```

完整結果見 `TEST_REPORT.md`，防護對照見 `FAILURE_MATRIX.md`。

## 重要限制

- 規則層只自動套用高信心修正；同音字、專有名詞歧義會列為人工確認，不擅自改寫事實。
- 抽取式摘要不會保證恰好四點；Tier 4 的 JSON 摘要才強制四點並驗證格式。
- spaCy／Embedding／Ollama 的準確率與記憶體取決於實際模型；引擎只能控制載入與降級，不能保證任何硬體都能跑所有模型。
- PDF 若沒有文字層需先經 OCR；本引擎不假裝 OCR 亂碼是可靠正文。

## 參考設計依據

- [FastAPI Lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [Scikit-learn HashingVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.HashingVectorizer.html)
- [Scikit-learn out-of-core text classification](https://scikit-learn.org/stable/auto_examples/applications/plot_out_of_core_classification.html)
- [psutil documentation](https://psutil.readthedocs.io/)
- [Ollama generate API](https://docs.ollama.com/api/generate)
- [Google Cloud Translation setup](https://docs.cloud.google.com/translate/docs/setup)
- [Google Cloud Translation quotas](https://docs.cloud.google.com/translate/quotas)
- [Argos Translate](https://github.com/argosopentech/argos-translate)
