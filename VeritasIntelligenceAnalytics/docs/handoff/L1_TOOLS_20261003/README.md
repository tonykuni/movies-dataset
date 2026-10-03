# L1 本地正規化工具升級（2026-10-03）

入口：VCGC `run SUP_MDL866_VIAUnifiedNLPOrchestrator`，新版 v0107。保留舊 v0106 與鎖定的 NLP token 工具；未改 token 啟用版本。TA-Lib 禁用。

主流程：Pydantic 嚴格輸入 → Polars NFKC/trim → casefold → 中央核准同義字（scope 隔離）→ 最長不重疊精確匹配 → RE2 擷取與日期/Decimal 驗證 → RapidFuzz 待審候選 → Pandera 輸出契約 → Parquet/CSV + SHA manifest。輸出保留原文、來源、中央規則代碼、規則雜湊、正規化字元座標與隔離原因。L1 的 ssot_code 一律 null；清洗成功不等於中央批准註冊。

同義字只投影 VIA_Numbering_SSOT 的中央同義冊 GREEN 有效列，不套用任意外部映射；單獨數字別名不做全文替換。同 scope 一詞多義隔離。來源不同不合併；同來源/record_id 同內容保留重複位置，異內容隔離。未知 scope 不自動猜測。

## 指令

在既有 VCGC 呼叫後加以下參數（input/out 建議絕對路徑，VCGC 子行程工作目錄可能不同）：

- `run SUP_MDL866_VIAUnifiedNLPOrchestrator --selftest`
- `run SUP_MDL866_VIAUnifiedNLPOrchestrator l1-tools`
- `run SUP_MDL866_VIAUnifiedNLPOrchestrator l1-clean --input <JSON-list> --out <folder> --backend aho --regex-backend re2`
- `run SUP_MDL866_VIAUnifiedNLPOrchestrator l1-review --input <JSON-request>`

每筆清洗輸入：record_id、source_id、scope、text（字串或 null）；禁止額外欄位。附 input_fixture.json 是中央字典 CLI 測資。

| 工具 | 實作角色 |
|---|---|
| pyahocorasick / FlashText / Polars | 可替換精確匹配後端 aho/flashtext/polars；CJK、英文邊界與 UTF8 座標交叉測試 |
| google-re2 / DuckDB | 可選 re2/duckdb 擷取後端；SQL 參數綁定、DuckDB 禁外部存取 |
| RapidFuzz | 未知詞相似候選；分数至少 90，最多 5 個，不自動同義化 |
| regex | escaped literal 的一字容錯，0.02 秒 timeout |
| Jellyfish | Jaro-Winkler；Soundex 僅英文 ASCII，不當中文發音判定 |
| PolyFuzz | 有界 TF-IDF 分群候選 |
| recordlinkage | 先按 market blocking，再公司名稱相似比對 |
| spaCy | 明示本地 lookup 詞形表，非完整金融 NLP 模型 |
| Gensim / FastText | 本地模型檔 SHA 驗證後提供鄰近詞候選；Gensim 用有界 JSON 向量，不讀 pickle |
| NLTK WordNet | 明示本地 corpus_dir；無語料回 RESOURCE_MISSING，不下載 |
| Pydantic / Pandera | 嚴格輸入與 Polars 輸出契約，攔截偽造 SSOT 編號 |

review 輸入 lane 可為 regex/jellyfish/polyfuzz/recordlinkage/spacy/gensim/fasttext/wordnet；各自必要欄位見引擎 review_request 完整定義。候選結果全是待審；語義相關不等於同義，不能自動發號。Gensim/FastText 測試只有合成模型，正式金融模型與 WordNet 語料仍待提供和驗證。

## 環境與限制

已在隔離 via_l1_tools_env 的 Linux/Python 3.12 實測 16 套件；完整版本見 requirements-linux-py312.lock.txt，pip check 無衝突。PolyFuzz 0.4.3 使用 Matplotlib 已移除的 API，實測固定 Matplotlib 3.8.4、NumPy 1.26.4、SciPy 1.13.1、spaCy 3.7.5 解決組合相容性。此 lock 是本次 Linux 可重現測試環境，不宣稱 Windows/Python 3.13 wheel 可用。執行引擎不自動安裝套件或下载模型。

限制在引擎頂部集中：每批最多 1,000 筆、每文 32,768 字元、字典 50,000 別名、待審列表 256 詞。RapidFuzz 仍需掃描候選字典，大量未知詞工作負載需分批與實際基準評估；未宣稱通用速度排名。FlashText 不是 O(1)，DuckDB 使用 RE2 而非 PCRE，字串替換不保證 zero-copy。

輸出 SHA 驗證通過才重用；CSV 公式前綴中和、UTF8 BOM，Parquet 保留原文。manifest 最後寫入；未宣稱多檔跨程序崩潰原子性。VIA_FROM_VCGC 是入口契約，不是安全認證。一般 Regex 重疊证明與中央未明 scope 的舊候選仍須 REVIEW。

治理：VCGC-REQ134 / VCGC-WKF015，註冊與發號沿用 CGC237；本批未建立第二套 allocator。既有主機 DB、OCR、134 引擎 Windows lanes 與全域紅黃燈未因這次 47 項通過而結案。
