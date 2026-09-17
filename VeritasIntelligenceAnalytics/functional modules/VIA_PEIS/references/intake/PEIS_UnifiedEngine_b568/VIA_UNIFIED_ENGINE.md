# VIA Unified Engine（單一引擎：聚眾整合、封印標註、資料庫最佳化）

`engine/via_unified_engine.py` 把原本散在多支工具的引擎整合工作收成**一支引擎、一個行程**，
既能掛入 VIA 系統（plugin），也能離開本庫單獨執行（independent）。

整合的最大目標是**節省 AI token**：把「同功能、不同名稱／不同工具」的引擎函式聚眾成能力，
測試成功就封印並標註成**能力卡（capability card）**；之後 AI 只讀卡就能呼叫能力，不必讀全文原始碼。
第二個目標是**資料庫最佳化**：能力庫用內容定址與增量掃描，省掉重複下載、重複讀取與重複建構的成本。

| 項目 | 值 |
|---|---|
| 候選 ID | `VIA-VIA-ENG996`（`config/ssot/VIA_LibraryRegistry.candidate.via#/records`，state `CANDIDATE`） |
| 權威路徑 | `config/ssot/VIA_SystemMaster.via#/engine_registry`（正式登錄由 `CGC-PROMOTE-WORKER-001` 寫入） |
| 協定 | `VIA-ENGINE-1.0`；引擎規格 `v0200`（`v0100` 的能力表與治理參數仍讀得進來，寫出一律正規化） |
| 依賴 | 純標準庫（含 `sqlite3`）；不連網、不安裝、不改動來源檔 |
| 前身 | VIA CANON CPU、VIA Engine Standardizer、VIA Engine Unifier、**VIA PEIS 引擎鎖定與能力截取治理大腦**、`engine/governance_engine.py` 的唯讀盤點 |
| 能力表 | `config/ssot/VIA_PEISCapabilityMap.via`（CME v2.0：能力、版本池、性能矩陣、策略、SSOT 字典） |
| 治理參數 | `config/ssot/central_governance_parameters.json#unified_engine`（門檻只能收緊，不能放寬；`peis_engine` 為前身別名） |

## 1. 一條鏈十一個階段

```
INTAKE → SCAN → CLUSTER → TEST → LOCK → EVIDENCE → POOL → HYDRA → MAP → ANNOTATE → STORE
 尋找    AST    聚眾      影子   封印    沙箱證據   版本池  全景    能力表   能力卡    能力庫
 輸入    正規化  同功能    對照   （測試          （引擎  衝突   （AUDIT
                 分群            成功才鎖）        鎖定）  分析    預設）
```

前六個階段是「產生證據」（CANON CPU／Standardizer／Unifier 那一半），
後五個階段是「治理大腦」（PEIS 那一半）：證據夠了才鎖引擎、才動能力表。
`ingest` 只跑前五階段；`govern` 跑完整條；`expand` 另跑八階段全景擴充（見第 9 節）。

1. **INTAKE**：收 `--src`（檔案或資料夾，可重複），跳過 `.git`／`__pycache__`／`node_modules` 等目錄。唯讀。
2. **SCAN**：AST 解析出每個函式的簽章、docstring 首行、工具家族、16 項風險碼與
   **α-rename Merkle 指紋**（變數改名、型別註記、docstring 不影響指紋）。語法錯誤的檔案被隔離成空結果，不改寫。
3. **CLUSTER（聚眾）**：先用同義詞表把函式名收斂成 `verb.object` 能力 id，同能力內再依指紋分成
   variant；指紋相同者直接折疊（`dup`），指紋不同但 shingle Jaccard ≥ 0.82 者標成近似（`near`）。
   **功能不變、只增不減**：不同實作一律保留為 variant，不會被覆寫。
4. **TEST**：對 default variant 找出可用探針，其餘 variant 用同一組輸入做**影子對照**，
   結果相同才算等價（浮點容差 `1e-9`）。
5. **LOCK**：只有測試 PASS 才 `SEALED`；SKIPPED／FAIL 一律 `PENDING`。
   **已封印永不解封**（後續掃描失敗也沿用舊封印），能力消失則轉 `DORMANT`。`engine_id` 由能力與 variant 決定，跨執行穩定。
6. **ANNOTATE**：每個能力產一張卡。卡片遵守 Root SSOT
   `token_governance.capsule_policy` 的 `REFERENCE_FIRST_DELTA_ONLY`（預設 12000 字元／24 張），
   **capsule 永不夾帶原始碼全文**。
7. **STORE**：寫入 SQLite 能力庫（見第 4 節）。

治理半邊（`govern` 才跑）：

8. **EVIDENCE**：把沙箱測試換算成 `VerificationEvidence`——探針通過數、可執行 variant
   覆蓋率、重跑一致性。**分歧的 variant 算不通過**（同一能力名稱兩種行為就不該路由），
   `benchmark_score` 恆為 0.0：沙箱不量時間，那 0.10 權重要靠外部 benchmark 證據。
9. **POOL**：證據過門檻才鎖成版本池條目。外部沙盒／benchmark 證據可用
   `govern --evidence <json>` 匯入，**那是 `benchmark_score` 唯一的合法來源**
   （本引擎自己的通道恆為 0.0）。
   `performance = 0.40 正確性 + 0.30 覆蓋率 + 0.20 穩定度 + 0.10 基準分`，
   任何一項未達門檻即 `def_LockRefused`，不進能力表。
   自動鎖定的引擎身份 = 來源模組、版本 = 內容雜湊前綴（`c<sha12>`），
   所以版本池天然 append-only；治理指派的正式身份用 `lock --engine-id/--engine-version`。
   鎖定同時記 `sha256` 與 `lock_seal`（身份＋版本＋內容雜湊＋性能分數的決定性指紋）。
10. **HYDRA**：全景衝突分析（見第 8 節），判 `SYNC_FIXABLE` 或 `SEQUENTIAL_FIX`。
11. **MAP**：寫 CME v2.0 能力表，**預設 AUDIT 不落地**，`--apply` 才寫，且 append-only。

## 2. 能力卡怎麼省 token

卡片只帶 AI 呼叫能力真正需要的欄位，空欄位一律省略，鍵名全部縮寫並在 capsule 開頭附一次 legend：

```json
{"cap":"compute.portfolio_score","eng":"E-COMPUTE-PORTFOLIO-SCORE-V1","st":"SEALED",
 "fp":"1af29efc4875e111","sig":"compute_portfolio_score(prices, weights)","at":"pkg/e.py#L2",
 "doc":"以權重加總報酬並回傳分數；缺值以前一筆補齊。","risk":["R01","R02"],"dup":1,
 "test":{"probe":"sequence_sequence","in":"[[1.0,2.0,3.0],[4.0,5.0,6.0]]","out":"10.686667","eqv":1,"div":0},
 "tok":{"body":420,"card":201}}
```

上面這張卡是 `selftest` 的實際輸出：兩份 AST 等價實作（命名與變數名完全不同）折成一張卡，
`dup: 1` 表示折疊掉一份，420 token 的原始碼換成 201 token 的卡。

`tok` 就是這張卡的帳：`body` 是同一能力全部原始碼的估算 token，`card` 是卡片本身。
capsule 另附 `token_ledger`：

| 欄位 | 意義 |
|---|---|
| `source_tokens` | AI 若讀全文要付的 token |
| `card_tokens` | capsule 內卡片合計 |
| `header_tokens` | capsule 固定成本（legend／policy／load_order），語料越大越攤平 |
| `capsule_tokens` | `header_tokens + card_tokens`（填入前估算，誤差 ≤ 3 token） |
| `known_card_tokens` | 這次已知的全部卡片合計（delta 只送其中一部分） |
| `saved_tokens` / `saved_percent` | `source_tokens − capsule_tokens`；**小語料可能為負，帳照實報**。`verify` 在語料還沒攤平 header 時把 token 閘門報成 SKIPPED 並給出損益兩平點，不會為了好看而放寬門檻 |

實測（可自行重跑驗證）：

```bash
python engine/via_unified_engine.py ingest --src engine --src scripts --src tests \
  --db /tmp/vue.db --root . --mode plugin --json
```

10 個檔案、381 個函式收斂成 357 個能力（6 份完全重複被折疊，2 對近似），
全文 151,594 token，一份 24 張卡的 capsule 只有 5,863 token（`header` 1,368 + `cards` 4,495），
**省下 145,731 token（96.1%）**。357 張卡全部留在本機能力庫（62,624 token，等於 AI 讀全部卡也只要四成），
capsule 只帶其中最省的 24 張。`engine/via_unified_engine.py` 自己當語料時，
`selftest` 與 CI 都會驗證節省率 ≥ 50%（數字隨庫內容變動，門檻不變）。

卡片不足時才讀 `at` 指向的那一段原始碼——這就是 capsule `load_order` 的三步。

## 3. 封印與執行（fail-closed）

* **只有 `SEALED` 能力可以 RUN**，`PENDING` 一律拒絕並回非零碼。
* 回傳是統一 envelope：`{"p","c","a","r","status","reason","result","path"}`；
  `audience=upstream`（預設）不含引擎 id、指紋或策略，也不回傳原始碼。
* 測試有兩條通道，證據上分得清楚（`sandbox_gate` 欄位）：
  **沙箱**（`VUE-SANDBOX-PROBE`，行程內、受限 builtins）與
  **模組級隔離**（`VUE-MODULE-ISOLATED`，`--allow-module-exec` 才啟用）。
  後者會**真的 import 來源模組**（跑它的 module-level 程式碼），所以預設關閉；
  啟用時一個來源檔一個子行程、`-I` 隔離模式、`VIA_NET=0`、有逾時與輸出上限，
  超過單批上限就分批而不是截斷（截斷等於靜默漏測）。
  本庫實測：封印數 **23 → 62**（+170%），10 個批次／7 個檔案。
* 測試與沙箱 RUN 共用同一個受限沙箱，五層防線：
  1. 只收 module 層、無裝飾器、無模組互參（vendorable）且參數 ≤ 4 的函式；
  2. AST 審核擋掉 `import`／`while`／`global`／generator／`with`／dunder 屬性／
     `open`·`eval`·`exec`·`getattr` 等名稱／過大常數；
  3. 執行命名空間換成受限 builtins（沒有 `__builtins__`、沒有 I/O）；
  4. `sys.settrace` 行數預算（預設 20000 行）；
  5. 例外一律收斂成「探針失敗」資料，不讓引擎崩掉。

被擋下的函式會帶 `skip_reason`（例如 `while`、`forbidden-name:open`、`import`），
理由寫在卡上，可稽核。

## 4. 資料庫最佳化（省掉下載／讀取／建構）

能力庫是單一 SQLite 檔（`--db`），省略時只在記憶體跑。
**`--db` 請指到庫外**（例如 `%TEMP%`／`/tmp`）：引擎不改來源檔，但把能力庫寫進工作樹
會留下未追蹤檔，弄髒 console 的 clean-tree 檢查。`verify` 省略 `--db` 時只在記憶體跑。

| 手段 | 做法 | 省下什麼 |
|---|---|---|
| 內容定址去重 | 相同 `body_sha256` 的原文只存一份（`vue_blob`） | 重複實作的儲存與建構成本（`dedup_tokens`） |
| stat 增量 | `size` + `mtime_ns` 相同就直接沿用既有列，**檔案完全不讀** | `reused_files`／`reused_bytes`／`reused_tokens` |
| sha256 回退 | 只被 touch 過（mtime 變、內容同）就沿用列，不重新解析 | 重複 AST 建構 |
| 欄位投影 | `query --columns cap,eng,sig` 只回傳指定欄位，未知欄位一律拒絕 | 呼叫端不必拉整張卡 |
| 卡片預算排序 | `saved_tokens DESC` 索引，取「最省的前 N 張」是一次 DB 排序 | 不必重新估算 token |
| 全卡留庫、capsule 限量 | 全部能力卡留在本機（零 AI token 成本），capsule 只帶上限內的子集 | AI 端的 context |

同一條指令跑第二次：`parsed_files: 0`、`reused_files: 10`、`reused_bytes: 496245`、
`reused_tokens: 167800`——一個檔案都沒重讀、一次 AST 都沒重建，封印數與第一輪一致
（封印跨執行沿用）。改動其中一個檔案時只有那個檔案會重新解析；檔案消失則從庫裡淘汰（`forgotten_files`）。

## 4A. delta capsule：第二次交棒只送變更

`REFERENCE_FIRST_DELTA_ONLY` 的 delta 從 v0200 起真的成立。給 `--handoff <id>`
（每個上游 AI／每個 audience 各一條基線）之後：

| 情況 | capsule 帶什麼 |
|---|---|
| 第一次 | 全部卡片，`delta.new` 列出能力 |
| 沒有任何變更 | **0 張卡**，只有 `delta.unchanged = {count, digest}` |
| 新增／內容變更 | 只帶那幾張卡（`delta.new`／`delta.changed`） |
| 能力消失 | 只給名字（`delta.retired`），不必解釋 |

`delta.rule` 就寫在 capsule 裡：「沒列在 new／changed 的能力＝上次那張卡仍然有效」。
實測兩支函式的語料：第一次 1,051 token、第二次 **684 token（0 張卡）**；
語料越大差距越大，因為第二次只剩 header 與 digest。

基線存在能力庫的 `vue_handoff` 表（handoff × audience × 能力），`--no-record`
可以預覽 delta 而不動基線，`capsule --diff` 只要摘要不要卡片。

## 4B. 黑盒原則：上游 AI 只看得到能力

`audience` 決定回傳面：

| audience | 誰用 | 卡片／回傳帶什麼 |
|---|---|---|
| `upstream`（預設） | 上游 AI | `cap`／`st`／`dom`／`sig`／`doc`／`risk`／`test`／`tok`；**沒有** `eng`、`fp`、`at`，capsule 也不帶引擎區塊與引擎檔路徑 |
| `governance` | 操作者／稽核 | 完整卡片，含 `eng`、`fp`、`at`，可做 reference-first 追查 |

`def_assert_blackbox` 對每個上游回傳做兩道檢查：

* **結構性**——任何一層出現 `engine_id`／`engines`／`version`／`strategy`／`sha256`／
  `entrypoint`／`source_path`／`lock_seal`／`performance_matrix` 欄位即拒絕。
* **字面性**——出現長度 ≥ 8 的私有字串（engine_id、entrypoint、sha256、策略名）即拒絕；
  版本號這類短字串靠結構性檢查擋下，避免把 `"3.3"` 誤判成洩漏。

這道守門員抓到兩個真的洩漏，兩次都是它先叫的：

1. capsule 原本在 `call.command` 裡寫了 `python engine/via_unified_engine.py run …`，
   而那個路徑正是能力表登錄的 `source_path`。現在 upstream 只給 envelope 與
   `RUN(capability, params)`，`command` 只在 `governance` 面出現。
2. 開啟模組級補測之後，探針**輸出**變成真實物件——`def_plugin_manifest` 的探針輸出
   整份都含引擎 id 與檔案路徑。所以 upstream 卡片一律過 `def_redact_for_upstream`：
   探針輸入／輸出／說明命中私有字串或洩漏欄位名就換成 `<redacted:Nchars>`，
   簽章與能力名稱照留（AI 還是叫得動，只是看不到那個值）。

上游拿到的永遠只有：

```json
{"c":"math","status":"GREEN","reason":"","result":10,"elapsed_ms":0,"trace_id":"0a17ffc0",
 "p":"VIA-ENGINE-1.0","a":"RUN","r":"RESULT_ONLY","path":"capability-map"}
```

失敗時 `reason` 只有代碼（`NO_LOCKED_ENGINE`／`ENGINE_SEAL_DRIFT`／`ENTRYPOINT_MISSING`／
`EXECUTION_ERROR:<型別>`），不含路徑或引擎名稱。

## 4C. Fail-Safe 與 Zero-Hydra

`govern` 與 `lock` 在寫能力表前一律先做全景分析，永不盲目覆寫：

| 衝突 | 判定 |
|---|---|
| `VERSION_POOL_COLLISION`（同引擎同版本、內容雜湊不同） | `SEQUENTIAL_FIX` |
| `STRATEGY_REDEFINITION`（既有版本的策略被改寫） | `SEQUENTIAL_FIX` |
| `FUNCTION_OWNERSHIP_DRIFT`（函式被改掛到別的能力） | `SEQUENTIAL_FIX` |
| `DEPENDENCY_CYCLE`（能力相依成環） | `SEQUENTIAL_FIX` |
| 純新增（新能力／新版本／新函式） | `SYNC_FIXABLE` |

判成 `SEQUENTIAL_FIX` 時能力表一個字都不寫，報告給出編號修復計畫與
AST 雙模定位（定義點 SYMBOL + 呼叫點 CALL）與下游相依清單；人工裁決後重跑
`govern --apply` 才會落地。`hydra_risk` 只有 `ISOLATED`／`BLOCKED` 兩種值。

合併時踩到並修掉的一個真問題：PEIS 原本「一檔一引擎」，鎖定會宣告整個檔案的公開符號；
統一引擎一個檔案有很多能力，照抄就會讓同檔能力互相宣告對方的函式，被自己的全景分析
判成 `FUNCTION_OWNERSHIP_DRIFT`。現在 `def_lock_engine(functions=...)` 讓呼叫端界定
這次鎖定實際擁有的函式，`lock` 子指令省略時才沿用整檔語意。

## 4D. 八階段全景自動擴充（`expand`）

`govern` 走能力庫那條線；`expand` 走全庫語意那條線，用來發現「還沒登錄進字典的新能力」：

| # | 階段 | 產出 |
|---|---|---|
| 1 | `EngineScanner` | Git tracked 引擎檔（`engine/`、`functional modules/`、`public/via/`），AST + SHA-256 |
| 2 | `SemanticExtractor` | 語義標準化名稱（`trend_predict` → `predict_trend`，去雜訊前綴 `def_`／`via_`） |
| 3 | `EmbeddingGenerator` | 64 維 blake2b 簽名雜湊向量（決定性，跨平台一致） |
| 4 | `SimilarityMatrixBuilder` | 全域相似度矩陣（能力一致 0.50＋token Jaccard 0.30＋餘弦 0.20） |
| 5 | `PanoramicClusterer` | 單鏈聚類 |
| 6 | `CapabilityAbstractor` | `NEW_CAPABILITY`／`EXTEND_CAPABILITY`／`CANDIDATE_CAPABILITY` |
| 7 | `CapabilityMapUpdater` | CME v2.0（append-only，AUDIT 預設不落地） |
| 8 | `PanoramicAbstractExpander` | 大引擎插槽（`E-Signal → predict_trend`）開放給 AI 截取 |

字典沒命中的符號一律 `unclassified`，只會變成**候選**能力等字典登錄，
不會用不認識的 token 自己捏造能力名稱污染能力表。本庫實測：8 個領域能力
（data／env／govern／math／predict／report／scan／signal）＋9 個候選群，裁決 `SYNC_FIXABLE`。

## 4E. 兩套 token 量測，都標明估算器

| 量測 | estimator | baseline | fast |
|---|---|---|---|
| 能力卡 vs 讀全文 | `vue-alnum4-v1`（原始碼文字） | 該語料全部函式原文 | capsule（header + 卡片） |
| RUN vs 自己選引擎 | `peis-json4-v1`（JSON payload） | 該能力的版本池、性能矩陣、策略與驗證證據 | `RUN(capability, params)` 一行 |

第二套會標 `band`（`BELOW_FLOOR`／`IN_TARGET`／`ABOVE_TARGET`，目標帶 70–90%）。
`routing_workload_reduction_percent` 是路由候選數的縮減比例，屬於 CPU／RAM 開銷的
**代理指標**，不是機器層級實測值——報告裡就是這樣標示的。

## 5. 獨立使用

```bash
# 自測（不需要本庫、不需要網路）
python engine/via_unified_engine.py selftest

# 掃描任意來源並建庫
python engine/via_unified_engine.py ingest --src /path/to/code --db ~/vue.db --root /path/to/code

# 給 AI 的能力 capsule（可再壓 token 預算）
python engine/via_unified_engine.py capsule --db ~/vue.db --status SEALED --budget-tokens 1500 --json

# 只讀需要的欄位
python engine/via_unified_engine.py query --db ~/vue.db --columns cap,sig,test

# RESULT_ONLY 執行已封印能力（能力庫沙箱路徑）
python engine/via_unified_engine.py run --db ~/vue.db --capability compute.mean --args "[[1,2,3]]"

# 完整治理循環（證據→版本池→Zero-Hydra→CME 能力表；預設 AUDIT 不寫）
python engine/via_unified_engine.py govern --src engine --db ~/vue.db --root . --output ~/vue-out
python engine/via_unified_engine.py govern --src engine --db ~/vue.db --root . --apply

# 八階段全景擴充（找還沒登錄的能力）
python engine/via_unified_engine.py expand --root . --json

# 用外部沙盒證據鎖定一支引擎
python engine/via_unified_engine.py lock --root . --engine-path "functional modules/VDF/engine/VDF_FactorLibrary.py" \
  --engine-id VIA-VDF-ENG002 --engine-version 1.0.0 --evidence ~/evidence.json

# 上游 AI 唯一被允許的呼叫面（能力表路徑，黑盒）
python engine/via_unified_engine.py run --root . --capability math --params '{"values":[1,2,3]}'

# token 節省帳（加 --root 一併看 CME 能力表現況）
python engine/via_unified_engine.py report --db ~/vue.db --root .

# 一鍵閘門（自測 → 治理循環 AUDIT → 逐條斷言，七道）
python engine/via_unified_engine.py verify --root .

# 引擎身份卡（規格、估算器、字典與門檻；本身就很省 token）
python engine/via_unified_engine.py version --json

# 提高封印率：沙箱擋下的再做模組級隔離補測
python engine/via_unified_engine.py govern --src engine --db ~/vue.db --root . --allow-module-exec

# 外部 benchmark 證據（唯一能讓 benchmark_score 非零的途徑）
python engine/via_unified_engine.py govern --src engine --db ~/vue.db --root . --evidence ~/evidence.json

# delta capsule：同一個上游 AI 第二次只拿變更
python engine/via_unified_engine.py capsule --db ~/vue.db --root . --handoff ai-1 --json
python engine/via_unified_engine.py capsule --db ~/vue.db --root . --handoff ai-1 --diff --no-record
```

兩支前身的旗標式呼叫都仍可用，會轉譯成對應子指令：
CANON CPU 的 `--selftest`、`--scan <path>`，PEIS 的 `--mode expand|lock|run|report`
（出現在任何位置都會轉）。`--json` 與 `--quiet` 放在子指令前後都可以；
燈號與進度條一律走 stderr，所以 `--json` 的 stdout 永遠是單一份可解析 JSON。

## 5B. 把引擎輸出成獨立成品（`export`）

```bash
python engine/via_unified_engine.py export --out ~/dist --zip
```

產出 `~/dist/via-unified-engine-independent/`：引擎本體（**逐位元組複製**）、
`README.md`、空白 CME 能力表、`MANIFEST.json`（每個檔案的 sha256、引擎身份卡、
自測結果），另可打包 `.zip`。

**匯出一定會驗證**：在輸出目錄以子行程跑一次匯出後的自測，
`MANIFEST.selftest.independent` 為 true 才算成功；跑不起來就 fail-closed 不產出
（`--no-verify` 可略過，但那就等於沒有證據）。這是「複製成功」與「真的能獨立運作」
的差別。

實測把成品放到一個**沒有 `.git`、沒有 `config/ssot`** 的目錄：

| 動作 | 結果 |
|---|---|
| `selftest` | 69/69 |
| `ingest --src src` | 2 個函式收成 1 個能力（AST 等價折疊）、封印 1、`policy.source = engine-default` |
| `ingest --allow-module-exec` | 封印 1 → 2（需要 `json` 的那支靠模組級通道過） |
| `capsule --handoff ai-1`（第二輪） | 0 張卡、`unchanged 2`、卡片 token 0 |
| `run --capability compute.mean` | `result 4.0`、黑盒 envelope |
| `verify` | 七道閘門 PASS（小語料的 token 那列 SKIPPED） |

交棒基線也有管理面：`handoff --db <file>` 列出每條基線（能力數、最後交棒時間），
`handoff --forget <id>` 清掉一條（下次那個 handoff 會拿到完整 capsule）。

## 6. 掛入系統

```bash
python engine/via_unified_engine.py manifest --root . --db ~/vue.db
```

`manifest` 輸出 `VIA.EnginePlugin` candidate 描述：engine 身份、`writer: false`、
七個階段、entry points、風險碼字典，以及 `capsule_policy`——
**有 Root SSOT 時 policy 來自 `config/ssot/VIA_SystemMaster.via`，沒有時退回引擎內建上限**，
這就是「掛入系統」與「獨立運作」共用同一支引擎的界面。

Python 內嵌：

```python
from pathlib import Path
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "via_unified_engine", "engine/via_unified_engine.py")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine   # dataclass 解析型別要用，別省
spec.loader.exec_module(engine)

report = engine.def_ingest([Path("engine")], database=Path("vue.db"),
                           mode="plugin", root=Path("."))
answer = engine.def_plugin_invoke(
    {"p": "VIA-ENGINE-1.0", "c": "compute.mean", "a": "RUN", "r": "RESULT_ONLY"},
    arguments=[[1, 2, 3]], database=Path("vue.db"))
```

`a: "CARD"` 則只回一張卡（`CARD_ONLY`），連結果都不算。

## 7. 治理邊界

* 來源檔**永不改動**：只解析、只讀取；`source_mutation: false` 寫在每份報告裡。
* 只產生 candidate 與證據；`config/ssot/VIA_SystemMaster.via` 仍只由
  `CGC-PROMOTE-WORKER-001` 寫入，本引擎不碰 Root SSOT。
* 不連網、不安裝、不殺行程、不推 Git；`selftest` 會 AST 自檢本檔沒有匯入任何網路套件、只用標準庫。
* v0200 的別名表全部 fail-closed：SSOT 領域字典、動詞表、物件表任一個別名被兩個
  分類宣告就拒絕載入（v0100 的動詞／物件表用 dict comprehension 建表，重複別名會被
  後者靜默覆蓋，字典本身就成了漂移來源）。實測本庫未分類符號 **215 → 79**。
* 風險碼 16 → **24**（新增 assert 驗證、遮蔽 builtin、自我遞迴、非決定性時間與隨機、
  硬編絕對路徑、疑似機密字面值、網址字面值），全部由同一次 AST 走訪判定。
* 指紋的節點型別 id 取自名稱雜湊，**與掃描順序及行程無關**——原型用序號配發，
  同一份語料換個順序就換指紋，封印帳與資料庫無法沿用，本引擎已修正並由 `selftest` 守住。

## 8. 證據與測試

```bash
python -m py_compile engine/via_unified_engine.py
python engine/via_unified_engine.py selftest          # 69 項不變式
python engine/via_unified_engine.py verify --root .   # 七道閘門一次跑完
python engine/via_unified_engine.py export --out /tmp/dist --zip  # 獨立成品＋自我驗證
python -m unittest -v tests/test_via_unified_engine.py   # 118 項（含 PEIS 併入的 67 項）
```

CI：`.github/workflows/unified-engine-verify.yml`（編譯 → selftest → unittest →
對本庫實跑 `ingest`／`govern`／`expand` → 檢查 token 帳與增量 →
`git diff --exit-code` 證明全程唯讀、AUDIT 沒有動到 SSOT）。
