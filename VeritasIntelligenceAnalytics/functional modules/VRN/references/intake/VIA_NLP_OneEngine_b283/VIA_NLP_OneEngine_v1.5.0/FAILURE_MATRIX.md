# VIA NLP One Engine：65 類失效防護矩陣

| # | 失效模式 | 已嵌入防護 | 狀態 |
|---:|---|---|---|
| 1 | 多請求同時觸發 OOM | 全域併發閘門；LLM 單路鎖；重型任務 admission gate | 已實作 |
| 2 | PyTorch VRAM 碎片 | 卸載時 `gc.collect()`、`empty_cache()`、`ipc_collect()` | 已實作 |
| 3 | CPU RAM 累積 | bounded cache、LRU model pool、TTL、壓力強制卸載 | 已實作 |
| 4 | 超長 Context | `max_text_chars`、檔案上限、chunking／overlap | 已實作 |
| 5 | Ollama 無回應 | 絕對 timeout、例外轉換、Tier 4 明確失敗 | 已實作 |
| 6 | JSON／結果寫入損毀 | 同目錄暫存檔、flush、fsync、`os.replace` | 已實作 |
| 7 | Worker 重複搶任務 | stage 間原子 replace；僅一個 claim 成功 | 已實作 |
| 8 | 殭屍任務 | 啟動時與外部可呼叫的 stale recovery、最大重試 | 已實作 |
| 9 | pending 萬檔退化 | `max_pending_jobs`；正式大規模部署建議改 SQLite／Redis | 部分；已設上限 |
| 10 | 檔案描述符耗盡 | 同步 bounded workers；所有檔案使用 context manager | 已實作 |
| 11 | LLM 自癒無限迴圈 | `MAX_LLM_RETRIES=2`，失敗保留 deterministic 結果 | 已實作 |
| 12 | Markdown 污染 JSON | fenced JSON 清除、`json.loads`、物件型別檢查 | 已實作 |
| 13 | Prompt injection | `<article>` 不可信資料邊界、固定 system policy | 已實作；非絕對保證 |
| 14 | JSON 未轉義／少欄位 | schema keys、型別、四點摘要數量驗證 | 已實作 |
| 15 | 災難性 Regex 回溯 | 僅使用線性／有界規則；輸入長度先設上限 | 已實作 |
| 16 | FastAPI event loop 阻塞 | 同步 CPU endpoint 交給 FastAPI threadpool；重任務另走 queue | 已實作 |
| 17 | 客戶端斷線孤兒 | 長任務採 job id，不綁定 HTTP 連線生命週期 | 已實作 |
| 18 | 任務洪流 | Token bucket、最大 batch、最大 pending、併發 semaphore | 已實作 |
| 19 | CORS 錯配／放太寬 | 預設不啟用 CORS、不遠端綁定 | 已實作安全預設 |
| 20 | Payload bomb | Content-Length gate、Pydantic 長度、檔案大小上限 | 已實作 |
| 21 | Null／控制字元 | 前置 sanitizer 移除控制字元 | 已實作 |
| 22 | Big5／GBK 編碼 | UTF-8 → Big5／CP950 → GB18030 → replacement | 已實作 |
| 23 | 未知 task／schema | task 白名單、路由 fail closed | 已實作 |
| 24 | OCR 亂碼 | 不自動視為可靠正文；需外部 OCR 品質閘門 | 明確限制 |
| 25 | 空 RAG 結果 | `context` 可為空，不傳空向量給 LLM；Embedding 回傳維度 0 | 已實作 |
| 26 | 跳題重組遺漏原文 | immutable segment ledger、offset、逐段與全文 SHA-256、重建驗證 | 已實作 |
| 27 | 修復稿污染來源 | 原文與 optimized view 分層；衍生內容僅用 segment reference 指向來源 | 已實作 |
| 28 | SSOT 錯誤自動升版 | 僅產生 candidate；literal escaping；衝突明列；人工批准才升版 | 已實作 |
| 29 | 對話內惡意程式碼 | 只做 AST／lexical parse，`execution_authorized=false`，不執行抽取內容 | 已實作 |
| 30 | 翻譯破壞程式片段 | code fence placeholder、還原驗證、來源與譯文 hash、translation memory | 已實作 |
| 31 | 網頁翻譯自動化失控 | `google_web` fail closed；只允許離線、本機或官方 API 後端 | 已實作 |
| 32 | 跳題後舊主題無法回接 | CPU sparse hierarchy、類別 anchor、Topic Episode、return link | 已實作 |
| 33 | 聚類壓縮造成內容遺失 | top-level topic 之外保留 Episode、segment graph 與完整來源／完善稿帳本 | 已實作 |
| 34 | 回饋同文異標污染模型 | normalized-text label conflict gate；候選訓練 fail closed | 已實作 |
| 35 | 小型神經網路未收斂卻升版 | convergence capture；未收斂 challenger 不具勝出資格；promotion 預設關閉 | 已實作 |
| 36 | 設定／模型升版後命中舊快取 | cache key 納入 Engine 版本、Knowledge config、治理 policy、模型 fingerprint 與翻譯設定 | 已實作 |
| 37 | 同公司跨跳題無法回接 | Ticker／結構 ID 穩定 anchor 加權並保留 anchor evidence | 已實作 |
| 38 | 不同股票因共同泛詞被誤合併 | Ticker anchor conflict penalty；主題輸出保留 assignment confidence | 已實作 |
| 39 | 主題達上限後硬塞無關內容 | 專用 unresolved capacity bucket；明示非語意歸類 | 已實作 |
| 40 | 完善稿改動關鍵數字或代碼 | 受保護事實 Counter 比對；失敗逐字回退來源並記錄原因 | 已實作 |
| 41 | 表格合併格自動補值製造假資料 | 逐格 verbatim；空格保留；合併候選只供 review、永不自動套用 | 已實作 |
| 42 | 多檔輸入順序不穩定造成結果漂移 | resolved path 去重、確定排序、逐檔 Record ID 與 hash | 已實作 |
| 43 | 討論重貼造成知識重複膨脹 | normalized exact deduplication；所有 occurrence 與來源仍保留 | 已實作 |
| 44 | 多個參數值被靜默選一個 | conflict register；每個候選、來源與順序明列；human required | 已實作 |
| 45 | 同函式多版本被自動拼接成壞程式 | revision family；candidate 僅提案；automatic merge=false | 已實作 |
| 46 | 無語言標籤的 code fence 被高信心誤判 | heuristic confidence、低信心 review gate、保留原始 code | 已實作 |
| 47 | 未解析函式呼叫被錯誤自動綁定 | unresolved／ambiguous interface register；automatic binding=false | 已實作 |
| 48 | 大量結果只寫一半或封裝損毀 | 同目錄暫存、fsync、原子 replace、ZIP test 與固定 timestamp | 已實作 |
| 49 | 零散命令被錯誤猜補後直接執行 | 只依明示續行符重建；保留逐行原文；`execution_authorized=false` | 已實作 |
| 50 | 不完整續行命令被當成可用 | continuation balance gate；低信心；review queue；fail closed | 已實作 |
| 51 | 同一命令重貼造成程序膨脹 | 穩定 Command ID 去重；所有 occurrence 與來源仍保留 | 已實作 |
| 52 | Mind Map 更新靜默刪除舊節點 | deprecation candidate；previous snapshot hash；不套用到上一版 | 已實作 |
| 53 | Mind Map 自動修正錯誤 canonical | update／conflict proposal 均 human required；automatic canonical mutation=false | 已實作 |
| 54 | 雙語輸出捏造未知翻譯 | 只用固定／來源明示詞庫；未知內容保留來源並標記 `needs_translation` | 已實作 |
| 55 | 新增早排序檔案導致全部 Record ID 位移 | 檔名 + source SHA-256 穩定 Record key；來源順序另欄保存 | 已實作 |
| 56 | Markdown 未知結構被丟棄 | 未知內容保留為 paragraph；全部字元串接與 SHA-256 驗證 | 已實作 |
| 57 | Layout 分類回寫破壞原文 | layout／NLP repair 全為 derivative；automatic source mutation=false | 已實作 |
| 58 | MarkItDown 被拿來讀遠端 URL | 只允許已 resolve 本機檔案與 `convert_local()`；無 remote-capable fallback | 已實作 |
| 59 | MarkItDown 外掛／LLM 產生未治理內容 | `enable_plugins=false`；不傳 LLM client；metadata 明示離線政策 | 已實作 |
| 60 | 缺 MarkItDown／converter 卻回傳空白成功 | 缺件、缺 `convert_local()` 或非字串結果一律明確失敗 | 已實作 |
| 61 | 問答回接推論被當成確定事實 | reply link 附 confidence／evidence／review flag；不生成銜接句 | 已實作 |
| 62 | 標準模板缺欄位被 AI 猜補 | missing slot 明列；repair proposal 只要求找來源或標示 N/A | 已實作 |
| 63 | 完整 Python 檔被切成大量假碎片 | Source Record 副檔名優先做全檔 AST；內容 hash 驗證；區間防重複 | 已實作 |
| 64 | AST set／tuple／bytes 無法輸出 JSON | deterministic JSON-safe normalization；set 排序、bytes 轉 hex | 已實作 |
| 65 | 可選工具被誤認為已安裝或自動啟用 | Provider Registry 只讀偵測；auto-install/import/execute 全關閉 | 已實作 |

## 額外治理

- 稽核記錄不保存原文，只保存長度、輸入 SHA-256、路由與耗時。
- email 與台灣手機格式在稽核中遮罩。
- active ML model 必須有 manifest 與 SHA-256 完整性驗證。
- `auto_promote=false`：模型候選不會在無人知情時自動上線。
- 深度模型預設不下載、不載入、不遠端呼叫。
