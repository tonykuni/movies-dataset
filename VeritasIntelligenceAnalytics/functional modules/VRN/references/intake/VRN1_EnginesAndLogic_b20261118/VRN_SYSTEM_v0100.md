# VRN-1 獨立系統 v0100

> **正名（2026-10-15）**：這個系統叫 **VRN-1**。它有自己的 MAIN
> （`VRN_Main_v0100.py`），不受 VRN-2／VDF／VCGC 影響，也不是誰的子系統。
> 操作員的**單一入口**是 `artifacts/VRN-1.ps1` —— 診斷與管線都走它，
> 不必記 MAIN 的路徑：
>
> ```powershell
> .\VRN-1.ps1 all        # 一個指令收掉全部（啟動體檢 → 封章鏈 → 實測 → HTML 驗證 → 收尾）
> .\VRN-1.ps1            # 35 具診斷
> .\VRN-1.ps1 full       # 診斷 + VRN 閘鏈（兩邊都綠才綠）
> .\VRN-1.ps1 run        # 完整實測
> .\VRN-1.ps1 check      # 只驗冊與註冊
> .\VRN-1.ps1 build / lock / matrix / pasteback / accel / standalone / selftest / sync
> ```
>
> **跑完就上傳（2026-10-19）** —— 兩個旗標一個管寫入、一個管連網，推上 origin 兩件都要；
> 而且**只有收尾完成的那一輪才上得去**（`def_wrapup` 說了算，不是「跑完就算」）：
>
> ```powershell
> .\VRN-1.ps1 all -Apply -SyncRepository     # 跑完整鏈，驗過才提交 → fetch → 快轉 → push
> .\VRN-1.ps1 sync                           # 空跑：只印出會做什麼，不寫也不連遠端
> ```
>
> **不想記路徑就用倉根那兩支啟動程式**（`%~dp0` 取自己的位置，沒有東西要填，可雙擊）：
>
> ```
> VRN-1.cmd          跑完整鏈、開 HTML，不上傳
> VRN-1-Sync.cmd     跑完整鏈，驗過就提交並推上 GitHub
> ```
>
> **處理的報告型別（2026-10-15 起三類各走各的路）**
>
> | 類別 | ENG393 DocClass | 路徑 | 輸出 |
> |---|---|---|---|
> | 個股報告或資訊（一個個股） | `STOCK` | FULL | 首頁＋年度財報頁，一報告一列 |
> | 產業資訊及展望（多個個股） | `INDUSTRY_OUTLOOK` | COVERAGE | 每家受評公司一列，共用 ReportID |
> | 其他投資報告 | `NEWS_DIGEST` / `OTHER_INVEST` / `OTHER` | REGISTER | 只分類登錄，不抽財務 |
>
> 政策寫在 `ssot/VRN_TitleTrim_SSOT_v0100.json#focus.doc_class_policy`，
> 判斷只有一份（`VRN_PageRegions.class_policy`）。
>
> **啟動器（2026-10-15）**：`artifacts/ActivateVRN-1.py`，對應操作員機器上的
> `ActivateVRN-2`。步驟編號照同一個習慣排，但每一步都轉給 VRN-1 裡已經在管
> 那件事的東西，一個判斷不開第二份實作：
>
> | 步驟 | 問誰 |
> |---|---|
> | ① 定位管理器 | `VRN_REGISTRY_v0100.json` 的 `main` 欄 |
> | ② 環境檢查 | 倉根 `requirements-dev.txt`（**不自動補裝**，見下） |
> | ③ 加速器覆蓋 | `scripts/VIA_BridgeInjector.py --check`（CI 跑的同一支） |
> | ④ 元件登記／封章 | 註冊冊 · `ssot/VRN_EngineLock_SSOT_v0100.json` |
> | ⑤ 互動對象 | `VRN_Main.INTERACTIONS` · `VRN_LocalDB.candidates()` |
> | ⑥ 啟動前快測 | MAIN 的 `selftest` |
> | ⑦ 啟動 | 動作原樣交給 MAIN |
>
> 和 VRN-2 啟動器刻意不同的一點：**這裡不自動補裝套件**。VRN-1 的相依釘在
> `requirements-dev.txt`，版本是實測過的決定，不在啟動時連網補；缺了就照實說缺，
> 對應的閘會略過，而略過不算證明。
>
> `artifacts/VRN-1.ps1` 的管線動作改走這支啟動器，因此不再寫死 MAIN 的路徑。
>
> **一個指令收掉整條鏈 · 加速器看得見（2026-10-16）**：操作員「把上述所有指令整合為一；
> 要加速加速器」。
>
> `VRN_Main_v0100.py all` = **build → lock → check → run**，吃 `run` 的全部旗標
> （`--samples`／`--no-cache`／`--no-open`…）。順序是相依關係不是排版：
> build 不先做，新函式沒編號、lock 會算錯指紋；lock 不先做，改過的引擎在 run 的 G18 會紅。
> **第一個硬失敗就停** —— 地基沒好還往下跑，只會得到一份建立在壞地基上的完整報告。
> `check` 的 AMBER（只有 WARN）不算硬失敗。引擎與冊都沒動過時 `--skip-seal` 跳過前三步。
>
> **加速器：不補模組，讓它掛得上、看得見。** 裁決「加速器缺席是設計如此，補模組＝九頭龍」
> 不變 —— 沙箱裡 `supportive modules/VIA_SuperAccel_Module.py` 不存在，我沒有、也不會寫一支。
> 能做的是讓掛載這件事不再是黑箱：
>
> - `all` 第一行就報車道，而且是**真的 import 一次之後**才報，不是只看檔案在不在：
>   `[ALL] 加速器：掛上 · <canonical> · 來源 <來源> · <路徑>`，或 `沒掛上 · 退回 stdlib 執行緒池 · <import 的錯誤>`。
>   檔案在不等於掛得上 —— 一支壞掉的加速器被印成「掛上」就是假綠燈，而這個系統最不該有的就是假綠燈。
>   掛載也排在 build／lock **之前**，它們的逐檔掃描（AST 注入、REGEX 冊、註冊冊 SHA）才吃得到 `accel_map`；
>   只在 `run` 裡掛，前三步整段走 stdlib 執行緒池。這裡只掛載不 `activate()`：
>   `activate()` 會套行程級上限，它的回報留在 `run` 的 P04 那一列，一個判斷一個地方。
>   （這一條是 Codex 在 PR #54 指出來的；兩個測試把它釘住：
>   `test_all_never_announces_an_accelerator_it_could_not_import`、`test_all_mounts_the_accelerator_before_the_seal_steps`。）
> - `accel` 找不到時列出**找過哪裡**（走訪順序、每個位置在不在），不再印一行空的「候選位置：」。
> - 掛載鏈路證過：`VIA_ACCEL_HOME` 指到一個放著 `VIA_SuperAccel_Module.py` 的資料夾，
>   `accel` 立刻 `[PASS] 來源 VIA_ACCEL_HOME`，`all` 開頭也跟著報「掛上」。
>
> 操作員機器上 `MOTHER_ACCEL_DEFAULT` 指的是
> `%USERPROFILE%\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules`
> —— 那是母倉工作樹的位置，所以**那邊很可能本來就掛得起來**，跑一次 `accel` 就知道。
>
> **還沒做、但量得出來的加速**（實檔 534 檔、各閘合計 1944 秒）：
>
> | 閘 | 秒 | 車道 |
> |---|---|---|
> | G06 入庫 | 772 | `worker_process`（已平行） |
> | G08 冪等 | 601 | `worker_process`（已平行） |
> | **G19 聚焦** | **232** | **`sequential`** |
> | **G07 首頁** | **196** | **連 P09 都沒記錄** |
>
> G19 與 G07 卡的正是 G06 已經解掉的那件事（PyMuPDF 不能多執行緒共用 → 每塊一個子行程）。
> 把那個證過的做法套過去是下一個真正的加速，**但沙箱語料只有 107 檔（G19 只花 1 秒），
> 這裡量不出效果，盲改兩個閘的風險不值得** —— 等操作員決定。
>
> **VRN-1 是獨立系統（2026-10-16 操作員重申）**：有自己的 MAIN（`VRN_Main_v0100.py`）、
> 自己的 SSOT（`ssot/`，REGEX／同義字／表頭冊／引擎鎖都自己發）、自己的編號（`VRN-ENG…`）。
> **參數可以向別的系統拿，只要不衝突；判斷不外包、也不被接管。**
>
> 這條線在程式碼裡是結構保證的，不是口號：
>
> | 邊界 | 怎麼保證的 |
> |---|---|
> | 編號只發給自己的檔 | `VRN_AstId.targets()` 用 `engine/` 非遞迴 glob；`ssot/` 收來的冊與 `references/` 凍結包永不編號 |
> | 母倉引擎是副本不是分身 | `engine/mother/` 逐位元組複製，`test_lock_is_the_mother_byte_copy` 守著；VRN 只委派不重寫 |
> | 不取代母系統的治理入口 | `VRN-1.ps1` 不是 `scripts/VIA-Launch-Console.ps1`；不改它、不被它呼叫 |
>
> 2026-10-16 全景稽核（唯讀）的結果：退役定位點 18 個**全部有接班人**（11 個是
> `VRN_Matrix` 一次改名規範化、`write_copy`→`write_copy_file`、`context_from`→`report_context`、
> 一個測試被三條更細的取代）；編號 1236 個零重複、零孤兒、零漏編號、號碼沒回收；
> 14 組已知答案蓋 58 個檔沒有一個指到不存在的檔。**成功的部份沒有遺失。**
>
> VCGC 唯讀稽核 39 道閘 33 PASS／5 WARN／1 FAIL，`HYDRA_GUARD` 查到的九頭龍是 **0**。
> 那一個 FAIL 是 `G07 INTERFACE_CONTRACT mismatch 1` —— `artifacts/VRN-1.ps1` 的參數表
> 從基線（10-14 種下的 11 個）長到 13 個（`Action` 來自收成單一指令、`Rest` 來自旗標轉送）。
> 兩次都是刻意的介面變更，**不是缺陷**；重新種基線要走母系統的 STAGE→APPROVE（帶核准
> token），那是操作員的動作，VRN-1 不碰 —— 碰了就破壞上面第三條邊界。
>
> **一標題四重點（2026-10-16）**：首頁引擎本來就算 `summary_four_points`，但倉內除了
> 產生它的那一行之外沒有任何消費端，表頭冊上也沒有欄 —— 算完掉在地上，沒輸出、沒驗證、
> 沒上鎖。這一版把它接成輸出表 `vrn_summary_points`（表頭冊 v0107，一份報告四列，
> 鍵 file + point_no），G16 逐欄驗、進鎖（49 支）。實檔實測 420 列／105 檔／每檔剛好 4 列。
>
> 接上去立刻看見一個本來看不見的內容問題：`summary.build` 拿 `body_zone[0]`／`[1]` 當
> 動能與催化劑，但 body_zone 第一行常常是券商抬頭，所以「動能」那一點會印出
> 「○○證券投資顧問 … 分析師 ○○○」；標題的官方名稱也常是「官方名稱待查」。
> **這是內容判斷，不在本次範圍內動** —— 但它現在看得見了，這正是接到輸出的用處。
>
> **輸出後驗證無誤自動跳 UI（2026-10-16）**：`VRN_Main run` 跑完開 HTML 報告。
> RED 不開（紅燈要看的是終端機那幾行 FAIL，不是漂亮頁面）；`--no-open`／`VRN_NO_OPEN`／
> `CI` 可關；沒有桌面環境照實說一行，絕不讓整跑失敗。
>
> **現價以 adj close 為基準、動態更新（2026-10-16）**：操作員「全部使用最新的 adj close
> 或報告前一日的 adj close 為基準動態更新」。
>
> 起因是 534 檔真實報告實測 RED：輸出鎖 `BROKEN 12`，**12 個全部是 `cover.current_price`**，
> 其他部位一個都沒有（HELD 477）。不是引擎退步 —— 那個值本來就是資料庫收盤價
> （`_db_price_part` 的 `source: "db"`），行情庫一更新值就變，而鎖只比 `(檔案 SHA, 部位)`
> 的值。鎖有一個 db 例外，但只在「從非 db 變成 db」那一次放行；之後每一次市場變動都掉進
> BROKEN。同一份報告隔天再跑必紅。
>
> 三件事一起定下來，**同一個紀律：比對要拿同一種量比**。
>
> | | 用什麼 | 為什麼 |
> |---|---|---|
> | 現價的**值**（帶走的基準） | **adj close** | 操作員裁決；報告日前最後一個交易日，庫裡沒有就退到最新一天 |
> | 現價的**狀態**（VERIFIED／CONFLICT） | 原始收盤價 | 報告印在紙上的是原始收盤價，不是還原價（handover L99／L104）。拿 adj 去比印出來的數字，只要除過權息就一律誤判成 CONFLICT |
> | **上漲%** 重算 | 原始收盤價 | 報告印的上漲% 是它自己拿原始價算的 |
>
> `adj_close` 缺就是缺，不拿 `close` 頂替（L99）—— 那種情況值照實是原始收盤價，`why` 會說。
>
> 鎖多一個狀態 **DYNAMIC（矩陣記號「動」）**：記最新的值與基準日（看得到變化、`history`
> 有 log），但永不判退步。舊帳本不用手動清 —— 下一跑那 12 筆自己從 BROKEN 轉成 DYNAMIC
> （已證）。目前沒有 `unlock` 子指令，所以「自己會好」這件事是刻意的。
>
> **三條報告路徑同步（2026-10-15）**：G06 入庫不再一份接一份。G19 聚焦已經替每一份
> 算好走哪條路，那份路徑表交給資料庫引擎 `process_documents_many()` 去分流 ——
> 三條路各自獨立往前跑，塊先按路徑分、再按量切（三條路的量差很多：實測
> FULL 59 · COVERAGE 22 · REGISTER 25，一條路一塊的話牆鐘會被最長那條綁住）。
>
> 做法照 `VRN_PageRegions.analyze_many`（同一個倉裡同一套：每塊一個子行程、照輸入
> 順序組回來、哪一塊掛了就在本行程重做不丟），不另立一種。子行程而不是執行緒，
> 因為 PyMuPDF 不能多執行緒共用。工人數照 `VRN_RunCache.cache_resources()` 的安全預算。
> `VRN_BATCH_INPROC=1` 切回循序，是同一份程式碼的另一條路。
>
> **工人是一個池子，不是一波一波。** 同時活著的子行程由一個號誌壓在預算內（派工器
> 怎麼排都破不了），做完一塊就馬上拿下一塊。分波會立一道柵欄，最後一波只剩一塊在跑
> 時其他工人全空等 —— 實測同一批 6.12 秒，換成池子 4.38 秒。
> 塊因此可以切得比工人多：一個工人幾塊是量出來的（107 檔、三個工人，各三次取中位）
> —— 一塊 6.57 秒 · **兩塊 4.83 秒** · 三塊 5.30 秒 · 循序對照 9.75 秒；
> 一塊太粗（牆鐘被 FULL 那 59 檔整塊綁住），三塊以上碎到被子行程啟動成本吃回去。
>
> 實測（107 檔，同一份程式碼只切 `VRN_BATCH_INPROC`）：
>
> | | 循序 | 三路同步 |
> |---|---|---|
> | G06 入庫 | 9.92 秒 | **4.38 秒** |
> | G08 冪等 | 9.74 秒 | **5.09 秒** |
> | 各閘合計 | 32.3 秒 | **25.6 秒** |
> | 牆鐘 | 41 秒 | **33 秒** |
>
> 兩邊的結論一模一樣：`AMBER PASS=368 WARN=10 SKIP=7 FAIL=0`。
>
> **接線上三個會讓分流形同沒開的洞**（都是「看起來有分流、其實沒有」）：
>
> 1. G19 交出來的聚焦表只帶 `doc_class` 不帶 `process`，路徑表整張空掉，三條路併成
>    一條（車道記的是 `streams: {"ALL": 106}`）。
> 2. 那張表上的 `kept` 是 `"Y"`／`"N"` 兩個**字串**，`if r.get("kept")` 兩個都算真。
> 3. G08 冪等自己另開一份參數，沒帶路徑表也沒帶工人預算 —— 它和 G06 寫同一個資料夾，
>    還會把 G06 那份車道紀錄蓋掉。現在兩關都記進 P09（`def_note_batch_lane`），
>    車道上看得到 `FULL 59、COVERAGE 22、REGISTER 25`。
>
> **工人不自己重建對照表**（Codex PR #50 P1）：母行程那份代號／券商／評等對照表寫成
> 一份 `lookups.json` 讓所有工人共用。工人重建的話，`--online-name-update` 併進來的
> 線上名冊會在子行程裡消失。同一類還有 `BROKER_DISPLAY` —— 它是 `load_broker_alias_ssot()`
> 順手填的模組級表，不跟著搬的話每一列 `BrokerDisplay` 都是空字串，而且只有分流那條路錯。
>
> 分流順便逼出一個**本來就有、與分流無關**的不確定性：別名等長時（`KGI` / `kgi`）
> 誰先，只按長度排的話看的是 `aliases` 自己的順序，而那個順序隨行程的字串雜湊種子
> 變 —— 同一份檔、同一支循序程式，`PYTHONHASHSEED` 0/1/2 會記下不同的別名拼法。
> 四處（兩支引擎的券商與評等別名）統一加字面平手規則 `(-len, 字面)`。選到哪一家
> broker 不受影響，定的是記哪個拼法。
>
> **管理器的名字（三邊不同，不是同一支被改名）**
>
> | 系統 | 管理器 | 出處 |
> |---|---|---|
> | VRN-2（操作員機器，現役） | `VRN_SystemManager_v0214.py` | `ActivateVRN-2` 的 ② 定位：「已在且 hash 同」 |
> | 母倉（收進本倉的冊） | `VRN_SystemManager_v0104.py` / `v0105.py` | `ssot/03_ssot/VRN_Audit_Evidence_v0100.json`、`VRN_Workflow_VRN_SSOT_v0105.json` |
> | VRN-1（本倉） | **`VRN_Main_v0100.py`** | 本檔上方、註冊冊 `main` 欄 |
>
> VRN-2 的管理器名字沒改過（版號走到 v0214）；改名的是 VRN-1 —— 正名成獨立系統時
> 把管理器叫回 MAIN。母倉那兩支的檔案本體不在本倉，只在收來的冊裡被引用。

本體是 2026-09-23 在 106 份真實報告上跑到 FAIL 0 的那一版 VRN：

- `VRN_Evidence_Core` v0100
- 首頁引擎 v0106、資料庫引擎 v0105、證據核心 v0102
- `VRN_AutoTestLoop` v0104（v0102 收緊 G11 真值閘：每筆真值都要被評到、非個股細類不同列黃燈；v0103 評等比對原文；v0104 加 G13 收來的冊當量尺）
- `VRN_BookCheck_v0100`：從其他對話收來的冊，當量尺用（只量不改）

這一版不改它們的判讀邏輯，只把它們收成一個自己站得住的系統，不跟 VIA／VDF 混在一起。

| 項目 | 檔案 | 作用 |
|---|---|---|
| 獨立 MAIN | `VRN_Main_v0100.py` | 唯一入口：實測、自測、建冊、驗冊、單獨複製測試、加速器 |
| Windows 啟動器 | `Invoke-VRN-Main-v0100.ps1` | 預設跑 `C:\測試樣本報告`；有進度條和看門狗；報告用瀏覽器開 |
| 獨立註冊 | `VRN_REGISTRY_v0100.json` | 登記 VRN 資料夾內每個檔案的類別、版本、SHA-256，以及有沒有加速器橋 |
| 獨立 SSOT：REGEX | `ssot/VRN_REGEX_SSOT_v0100.json` | 200 條 regex，各登記一次，附 232 個使用點，加上代碼主檔的 48 條 |
| 獨立 SSOT：同義字 | `ssot/VRN_SYNONYM_SSOT_v0100.json` | 兩支引擎和證據核心在執行期實際生效的表，跨引擎衝突照列 |
| 知識書索引 | `ssot/VRN_SSOT_INDEX_v0100.json` | VRN 讀的每一本書：版本、SHA-256、出處、讀者 |
| VRN 自有知識副本 | `ssot/VRN_Broker_Dict_v0100.json`<br>`ssot/VRN_Rating_Dict_v0100.json`<br>`ssot/VIS_VRN_TickerFilenameSSOT_v0100.py` | 引擎先讀這裡，`attachments/` 只是備援 |
| 收來的冊（2026-10-10） | `ssot/` 裡 10 本，出處在 `ssot/VRN_BOOKS_PROVENANCE_v0100.json` | 券商、評等、目標價、電郵、電話、財報科目、驗證法；見下方「收來的冊」 |

## 在 Windows 上跑真實報告

```powershell
cd "C:\Users\tonyk\VIA-VDF-VRN\functional modules\VRN"
pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VRN-Main-v0100.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VRN-Main-v0100.ps1 -Truth "C:\VRN_Truth\real_truth.json"
```

不帶參數時：
- 樣本讀 `C:\測試樣本報告`；
- 只處理個股報告的檔名、第一頁、年度財報頁（G19），其他頁與非個股不處理；要整份全部處理就加 `-AllPages`；
- 輸出寫到 `%LOCALAPPDATA%\VRN_Main\<時間>\`；
- 報告是 `VRN_Main_Report_v0100.html`，用 Edge／Chrome／Firefox 開，不交給 `.html` 的預設程式。設 `VIA_NO_OPEN=1` 或帶 `-NoOpen` 就不開。

跑的順序：
1. 前置閘：P04 加速器 → P01 環境 → P02 SSOT 三本冊 → P03 註冊冊 → P11 AST 編號 → P16 引擎鎖 → P07 樣本（只讀，留 SHA-256 存證）→ P08 收來的冊 → P12 本機資料庫 → P13 本機 03_ssot → P14 個股報告拆解
2. `VRN_AutoTestLoop` G01–G19，逐檔顯示進度（G19 聚焦在 G06 之前跑：只處理個股報告的檔名、第一頁、年度財報頁）
3. P09 加速器覆蓋、P10 TEMP 與刪除
3. 寫出報告

其他指令都用 `-Command <名稱>`：

| 指令 | 作用 |
|---|---|
| `selftest` | 離線自測：三本冊、註冊冊、加速器、106 個檔名 oracle、收來的冊 |
| `check` | 只驗 `ssot/`、註冊冊和 AST 編號，不寫檔 |
| `build` | 改過程式或知識書之後跑：先 AST 注入編號（只加註解），再重建 `ssot/` 各冊和註冊冊 |
| `standalone` | 把 VRN 資料夾單獨複製到暫存區再跑，證明不依賴倉庫其他部分 |
| `accel` | 顯示加速器狀態 |
| `lock` | 已知答案逐組證明，全過的引擎與冊記下指紋（`ssot/VRN_EngineLock_SSOT_v0100.json`）；改過引擎之後跑。輸出鎖帳本看 `python VRN_Main_v0100.py lock --status`，解鎖 `--unlock 檔名 [--part 部位]` |
| `update` | 2026-10-12：更新到工作分支（`-Branch`，預設 `claude/amazing-hawking-tjzssr`）：只抓這一個分支（遠端同時有 `ChatGPT` 與 `chatgpt/…`，Windows 不分大小寫，抓全部會撞名）→ 切過去 → 只快轉。本機有改過還沒提交的檔就停，不蓋掉；不能快轉也停，不強制 |
| `version` | 印目前的版本（commit、分支）與 G17／G18／G19 引擎在不在；每次啟動也會先印這一行 |

PowerShell 端的每個動作都走 PS 加速器（操作員 2026-10-12「PS指令也要加加速器」）：
- 18 非阻塞看門狗：Python、pip、每一個 git 步驟都有逾時，逾時整樹結束、回 124；
- 16／17 動態進度與說明；
- 22 快取去重：跑完找報告、矩陣、DataFrame、待修清單、聚焦清單時，輸出夾只掃一次；
- 本倉找不到 PS 加速器時，從 `-AccelHome`／`VIA_ACCEL_HOME`／母倉預設位置掛上；`Invoke-VRN-AutoTest.ps1` 也一樣（新增 `-AccelHome`、`-TimeoutSec`）。

## 加速器

各 `.py` 檔頭的 `[VIA:ACCEL-BRIDGE:v0100]`，以及 `.ps1` 的 `[VIA:PS-ACCEL20:v0100]`，都維持原樣。本倉不放加速器程式碼。

啟動時依下列順序找加速器：
1. `-AccelHome`
2. 環境變數 `VIA_ACCEL_HOME`
3. 從 VRN 資料夾往上找 `supportive modules`
4. 母倉預設位置 `%USERPROFILE%\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules`

找到之後：
- **Python 端**：`VRN_Main` 以路徑載入 `VIA_SuperAccel_Module`，鏈是 `SUP_MDL737` v0110 → v0109 → v0108 → `VeritasCeleritas_v1141`。之後同一行程載入的每支引擎，橋都接得到它；`activate()` 會套用執行緒預算。
- **PS 端**：啟動器 dot-source 同一處的 `VIA_PS_Accel_Module.ps1`，掛上 PS 25 加速器（`Write-VIAProgress` 進度條、`Invoke-VIAGuarded` 看門狗）。

找不到加速器時照跑，判讀不受影響，報告寫「無加速」。

2026-10-10 在沙盒用母倉 `ef8e3ef9` 的加速器實測：
- Python 端載入 `SUP_MDL737_SuperAccelModule_v0110` 與 Celeritas 1.14.0，PS 端掛上 25/25；
- 判讀結果和無加速時逐列相同；
- 這組合成語料的瓶頸是純 Python 的 PDF 解析，所以有沒有加速器都是 32 秒，沒有量到加速。

## 評等：讀原文、顯示原文、不分類（操作員 2026-10-10）

- `Rating` 欄和首頁摘要顯示的是報告上印的字，例如「買進」「中立」「Overweight」；檔名格位保留原代碼，例如 `OW_增加持股`。
- 詞表只用來在頁面上找到評等字，不決定等級，也不對應任何中央標準鍵。
- `RatingFine`、`RatingKey` 不再填。欄位保留，因為規則是只增不減。
- 測試端的比對方式：
  - 合成語料：比對頁面上印的字。
  - 真值檔記的是原文：逐字比。
  - 真值檔記的是等級（BUY…）：只在測試裡用證據核心同一套詞表，把原文對回等級來比。所以舊的真值檔不必重做，引擎輸出也不帶等級。

## 券商：GF 照原文顯示，不套中央 批679 拒絕清單（操作員 2026-10-10）

- 以下 6 家照報告上印的認成券商：廣發 GF、中信證券（英文 CITIC Securities）、中信建投 CSC、中金 CICC、海通 HAITONG、國泰君安 GTJA。
  名單放在 `VRN_Evidence_Core.MAINLAND_BROKER_ALIASES`，由 VRN 自己持有；兩支引擎都在讀字典之前先登記這份名單。
- 長名先佔住整段文字，所以：
  - 「國泰君安」不會被認成國泰；
  - 「中信建投」不會被認成中國信託；
  - 「China International Capital」不會被認成群益。
- 這些名稱只有在指出發行人的位置才算數，包括發行人行、揭露、著作權、對方的 e-mail 網域，或後面接「研究所」。
  單獨佔一行的頁首／頁尾刊頭也算，例如「廣發證券股份有限公司」「CITIC Securities Co., Ltd.」；同一行只能再有公司字尾和標點。
  內文裡的引用（例如「根據中信建投數據」）、資料來源行、內文中間單獨一行的名稱都不算。
- 「中信證券」照 VRN 自己的機構表和使用者字典，仍然是 CTBC。
- `VRN_Broker_Dict` 裡「中信」「國泰」兩個大雜燴條目內的中國券商名稱，現在歸各自的公司。字典本身一個字都沒改，只增不減。
- 真值檔若有列在 `accept.broker` 標了 `DENIED`：G11 只列黃燈，提醒更新那一列，不判紅。

## 收來的冊：從其他對話整合進實測（操作員 2026-10-10）

操作員令：「擷取其他對話中的 BROKER DICT RATING LIST TARGET PRICE DICT EMAIL TEL 所有 FINANCIAL ACCOUNT AND VALIDATION METHOD 快整合進入實測階段」。

怎麼找的：
- 讀其他對話的紀錄（VRN 線、動詞整合、VDF、VCGC、VRN系統啟動處理、每日交接等），找出每一類最新的冊在哪裡、哪一版。
- 再到母倉 main（`ef8e3ef9`）逐檔取原檔。母倉其他 20 條未併分支逐一比過，沒有更新的版本。
- 逐位元組複製進 `ssot/`。每本的母倉路徑、commit、哪個對話建的、SHA-256，都寫在 `ssot/VRN_BOOKS_PROVENANCE_v0100.json`。

| 類別 | 冊（`ssot/`） | 內容 |
|---|---|---|
| BROKER DICT | `VRN_Broker_Dict_v0103.json` | 28 家正典、中英文名、別名、電郵網域別名。母倉主線在 `7928007e`（2026-10-06）把它刪了；照只增不減，從加進來的 `130040c2` 取回 |
| RATING LIST | `VRN_S05_FieldRegistry_v0103.json` 的 `rating_list`、`VRN_FieldRules_SSOT_v0101.json` 的 `canon_map`、`VIA_SSOT_SynonymUnion_v0107.json` 的 rating | 只拿來在頁面上找字、檢查印出來的字在不在詞表；不分類 |
| TARGET PRICE DICT | S05 的 `target_price_dict` 與 `TARGET_PRICE_LABEL / VERB / TAIL`（v0103 收千分位）、`VIA_VRN_ExtractRules_SSOT_v0100.json` 的對照容差 | 目標價同義字、前次目標價停用字 |
| EMAIL | S05 `EMAIL_FULL`、`email_domain_to_broker`（42 網域）；`VIA_VRN_ReportFieldRules_SSOT_v0101.json` 網域補遺 | 數字信箱是員工編號，不是姓名 |
| TEL | `VIA_VRN_ReportFieldRules_SSOT_v0101.json` 的電話次序與守衛；S05 `TEL_TW_FULL`；`VRN_Contact_Regex_v0100.json` | 先台北再香港再手機再國際碼，前面吃掉的區間後面不再讀 |
| FINANCIAL ACCOUNT | `VRN_FinLexicon_SSOT_v0109.json`（76 科目）、S05 `financialdata_fields`（76 欄）、SynonymUnion `fin_account`（632） | 財報列標能不能被冊命名 |
| VALIDATION METHOD | `VRN_FieldRules_SSOT_v0101.json` 財報恆等式 7 條、`VIA_VRN_ExtractRules_SSOT_v0100.json` 對照容差、`VIA_VRN_FieldSpec_SSOT_v0100.json` 15 欄六態、`VIA_Validation_SSOT_v0100.json` 驗證法登記 | 見下方 G13 |

沒有收的：
- `VIA_Central_Synonym_Regex_v0107.json`：中央的冊。放進本倉會讓中央治理判紅（冊內裁定與碼冊把同一批評等字各列一次 = 8 個同義字多主；7 條重複 pattern，其中電話、電郵式本來就是 VRN 首頁引擎自己的）。VRN 要的評等字、電話、電郵、目標價，別的冊都有，所以不收整本，也不去放寬治理閘。
- 中央拒絕清單（VRN 不套用）、`70_VRN_Rules` 的 `.py`（是程式不是冊，鎖檔全部對不上）、VCGC 工具（留在倉庫根鏡像）。理由逐條寫在出處檔。

怎麼進實測：
- **引擎**：證據核心 v0102 先讀 VRN 自己 `ssot/` 裡最新的規則書（`VRN_FieldRules_SSOT_v0101`、`VIA_VRN_ReportFieldRules_SSOT_v0101`），鏡像只當備援。這兩本對 v0100 只增不減：多了強力買進／強力賣出的字、40 個職稱、台灣手機與國際碼。106 個檔名 oracle 不變。
- **G13 BOOKS**（AutoTestLoop v0104）：每一份首頁、每一列財報，都拿回冊上對，引擎答案一個字都不動。
  - 券商在不在冊；中國券商是 VRN 自己照原文認的，列 `VRN_OWN`，不算分歧。
  - 電郵網域指向的券商與首頁券商是否一致；數字信箱列 `UNVERIFIABLE`。
  - 電話：冊讀到、引擎沒讀到的列 `BOOK_ONLY`。
  - 評等：印出來的字在不在詞表。
  - 目標價：用冊的式子重讀，容差 0.5%（ExtractRules R-CMP-01）；非個股報告不比。
  - 財報列標：引擎命名、只有冊命名得出、都不認得、非列標。
  - 財報恆等式：毛利 = 營收 − 營業成本、毛利率、營益率、淨利率、資產 = 負債 + 權益、EPS = 淨利 ÷ 股數。缺運算元就照實列 `INSUFFICIENT`。
  - 冊自己的例子對不上自己，是冊的缺陷，列黃燈，不改冊。
- **G12**：VCGC 鏡像缺席（VRN 單獨複製出去）時，改讀 VRN 自己的規格副本，六態照冊判，不再整閘略過。
- **P08 BOOKS**（`selftest` 與實測都跑）：8 本當量尺的冊都在、S05 的 40 條 regex 對自己的 94 個例子、研報欄位尺的 5 條電話式在 Python 都能編譯。

## 第三輪（操作員 2026-10-10）：資料庫、TEMP、加速器、AST 編號、REGEX／同義字

操作員令：「擷取其他對話中的 DATE BROKER DICT EMAIL 香港台灣TEL RATING LIST 三種代號 TARGET PRICE LIST DICT 從DATABASE擷取資料NAME ADJ CLOSE …
善用TEMP補強記憶體 但刪除原則要建立 加速器深入所有動作 注入AST 分類說明編號 所有引擎編號版本註冊 REGEX SSOT 同義字要建構完成
參考其他GITHUB但目前邏輯不可動 只增加SSOT REGEX 同義字 AST注入 加速器覆蓋等功能」。

**判讀邏輯一個字都沒動**：合成語料原有的 376 列答案逐列相同（代號、評等、目標價、券商、三平台、公司名），106 個檔名 oracle 不變；
AST 注入前後每一支程式的 AST 完全相同。新增的都是另外的欄、另外的冊、另外的閘。

### 本機資料庫：公司名稱、ADJ CLOSE（`engine/VRN_LocalDB_v0100.py`，唯讀）
- 找資料庫的順序：`VRN_LOCALDB` → `VIA_DB_VDF_TW_MARKET` → 資料家（`VIA_DATA_HOME`，沒設就是 `%USERPROFILE%\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database`）
  裡的 `VIA_Parquet_Catalog.duckdb`（只有它真的有下面的表或視圖才用）→ 資料家底下的 `vdf_tw_market.duckdb`（`mega` 優先、最新優先；`_repo_`、`_from_old_`、selftest、stash 不用）。
- 表（VDF 寫的，見 ENG079 / ENG073 / CGC_MDL142）：公司名稱讀 `tw_listings_industry`，沒有才讀 `tw_listings`；價格讀 `tw_daily_prices`（`adj_close`）。
- 規矩照交接 L99 / L104：
  - **永不拿 close 頂替 adj_close**：缺 adj_close 就是缺；
  - 報告日基準 = 報告日前最後一個交易日；
  - 因子 = 同一列的 adj_close ÷ close；
  - 調整後目標價 = 目標價 × 報告日因子 ÷ 最新日因子；
  - 基準超過 14 天、最新價超過 30 天，值照列、狀態寫 STALE。
- 資料庫引擎 v0105 在每列**最後面加新欄**：`NameDB`、`AdjCloseReport`、`AdjCloseLatest`、`AdjFactor*`、`TargetPriceAdj`、`UpsideAdjPct`、`LocalDBStatus`、`LocalDBPath`。原有欄位一個都不改。
- 找不到資料庫、沒有 duckdb，都照實寫在 `LocalDBStatus`，判讀照常。
- 閘：P12（實測前先看資料庫在哪、各表幾列）、G14（這一輪補到幾家名稱、幾家 ADJ CLOSE、幾筆過期）；G12 的「公司名稱、ADJ 收盤、調整後目標價」有資料庫時照實算，不再寫「要觸網」。

### TEMP 與刪除原則（`engine/VRN_TempStore_v0100.py`、`ssot/VRN_TEMP_POLICY_v0100.json`）
- 和母倉 `SUP_MDL867_TempSpill`（L107、R-TEMP-01）同一個 TEMP 根、同一本刪除帳 `purge_ledger.jsonl`。
- 跑的時候 TMP / TEMP / duckdb 落碟都指到本輪夾。首頁逐行文字、AST 注入前的原檔備份都放這裡，不整批壓在記憶體。
- 刪除原則九條寫在冊上，重點：
  - 只刪有 VRN 擁有者標記的 run_* 夾；
  - 不跟隨連結；
  - 路徑含 VIA_Reports、supportive modules、functional modules、.git、registry、ssot 一律不刪；
  - 每個工具只留最新 5 輪；超過 10 GB 從最舊的刪，正在跑的那一輪永不刪；
  - 每一筆刪除都記帳；
  - 樣本、報告、真值、冊永遠不放進 TEMP。
- 閘：P10（本輪夾、大小、這次依規則刪了幾輪、哪些依規則留下）。

### 加速器覆蓋（P09）
- 純讀取、純計算的動作走加速器的 `accel_map`：
  - REGEX 冊逐檔 AST 掃描；
  - 註冊冊與 INDEX 的 SHA-256；
  - 樣本存證；
  - AST 注入規劃；
  - G13 冊式重讀。
- 兩支引擎的逐檔判讀（G06 / G07 / G08）不拆執行緒，因為判讀邏輯不可動。它們在 P04 `activate()` 之後的同一個行程裡跑，P09 列為「加速器行程掛載」。
- P09 逐一列出每個動作實際走了哪一條道、幾項、幾秒。加速器沒掛上時照實寫「退回 stdlib 執行緒池」。

### AST 編號（`engine/VRN_AstId_v0100.py`、`ssot/VRN_ID_SSOT_v0100.json`）
- 每個模組、類別、函式都有編號，形狀同中央階層但由 VRN 自己發：
  - 引擎 `VRN-ENG001`…，例如 ENG001 首頁、ENG002 資料庫、ENG003 證據核心；
  - MAIN `VRN-MAN001`、測試 `VRN-TST…`、啟動器 `VRN-PSL…`；
  - 函式、類別如 `VRN-ENG001-FNC045`。
- 每一筆都有分類（TEST / GATE / EXTRACT / VALIDATE / IO / BUILD / REPORT / ENTRY / INIT / CLASS / LOGIC）、說明（docstring 第一行）和模組版本；註冊冊每一列也帶編號、分類、模組版本。
- 注入只加註解：每支檔頭三行，每個 def / class 上面一行。寫回前 AST 必須和原檔相同，不同就拒寫。Windows 的 CRLF 照留。
- 編號永不回收：函式消失標 RETIRED，號碼不再發。
- `build` 自動注入；`check` 與 P11 驗證每個 def 都有號碼、和冊相符。

### REGEX 與同義字冊建構完成
- **REGEX 冊**：
  - 每一條程式 regex 加了細分類：DATE、BROKER、EMAIL、TEL_TW、TEL_HK、RATING、TICKER_TW / TICKER_YF / TICKER_BBG（三種代號）、TARGET_PRICE、NAME、FINANCIAL…；
  - 收來的冊上的 regex 98 條登記在 `book_patterns`，例如 S05 的日期、代號、電郵、電話、目標價，研報欄位尺的台北 / 香港 / 手機 / 國際電話，規則書 v0101 的式子；
  - 和程式一模一樣的 5 條（三種代號、數字信箱、一條日期）不重寫，掛在程式那一筆的 `book_sources`；
  - 掃描器自己的檔名清單不再被當成 regex。
- **同義字冊**：
  - 多了 `book_terms`，依類別登記冊上的同義字：日期、券商、電郵網域、評等偵測詞、三種代號、目標價（含「前次」停用字）、公司名稱、ADJ CLOSE、分析師職稱、財報科目 76 個；
  - 券商冊與引擎的對照只顯示：分裂 0、代碼名不同 2（BOA / BOFA、MCQ / MACQUARIE）、冊有引擎沒有 9（電郵網域片段）；
  - 要不要併進引擎由操作員裁定。

## 本機 03_ssot（操作員 2026-10-11，選「兩個都做」）

操作員給的 `C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_02_vrn\03_ssot`（53 個檔）是母倉 `functional modules/VRN/SSOT` 的同步夾。

- **收進 VRN**：
  - 母倉 main（`c88acc4f`）上拿得到的，逐位元組收進 `ssot/03_ssot/`，目錄照原樣，含 `v2/`、`v2/generations/`；
  - 共收 36 檔，每一檔的母倉路徑和 SHA-256（LF）記在 `ssot/VRN_03SSOT_PROVENANCE_v0100.json`。
- **擋下的檔（列在同一本的 `not_taken`）**：
  - 最上層是 JSON 陣列的 2 檔：中央治理把這種檔判 parse FAIL；
  - 檔名帶 MDL024／027／033／059／069／105 的 6 檔：中央台帳已把這 6 個號碼發給別的檔，收進來會在 G32 出現 6 件編號衝突；
  - 只在操作員電腦上、母倉沒有的 9 檔：FinLexicon v0110、LayoutRestore v0101、MasterList、MDL089／090 的 `_v0100` 及各自的 `.integration`。
- **每一家取最新版（P08、G13）**：
  - 收來的冊在 VRN `ssot/`、`ssot/03_ssot/`、操作員本機 03_ssot 三處比版本號，取最新的；
  - 例如本機有 FinLexicon v0110，就用它，不用 VRN 的 v0109；
  - 不是 VRN `ssot/` 來的冊，報告會寫「較新的版本取自：…」；
  - `.integration.json` 是整合報告，不是冊，不算。
- **P13 本機 03_ssot（唯讀）**：
  - 逐檔對照本機和 VRN 的副本：相同、內容不同、本機較新、只在本機、只在 VRN；
  - 結果寫在輸出夾的 `VRN_LocalSSOT_Compare_v0100.json`，本機資料夾一個字都不寫；
  - 有「本機較新／內容不同／只在本機」就是 WARN，列出檔名；要帶進 VRN，請推到母倉，或把檔交給我。
- **環境變數**：`VRN_LOCAL_SSOT` 可以指別的資料夾；設成空字串就不讀本機。
- **判讀不變**：引擎判讀不讀 `ssot/03_ssot/`。

## 個股報告拆解與還原（操作員 2026-10-11）

操作員：「inputs 示那些個股報告的檔案名稱拆解、首頁的資訊區、本文區切割資訊區、年度財報告面左頁對切、不同圖在上下切，output 確定有辦法還原資料轉為資料庫並擷取到對的輸出值並驗算通過，use all sample document，只擷取個股報告……所有動作都要加入加速器……評價方法……financial data 加減法及除法驗算法自其他抓完備」。

- **不另寫第二份**：
  - 母倉已經有這些引擎，逐位元組收進 `engine/mother/`：
    - ENG392：XY 切；
    - ENG393：個股分類；
    - ENG394：版面還原；
    - ENG395：評價法詞典；
    - ENG396：目標價、公司名稱、評價法。
  - `engine/VRN_PageRegions_v0100.py` 依路徑載入它們，並把 VRN 自己 `ssot/` 的冊交給它們。它們不讀 VRN 以外的地方，也不寫任何檔。
  - 出處在 `ssot/VRN_ENGINES_PROVENANCE_v0100.json`，編號 VRN-MOM001–005。
- **一號一檔**：
  - ENG393、ENG394 的 v0101 薄尾沒有收：同一個引擎號兩個檔，會讓中央治理 G32 編號衝突。
  - ENG394 v0101 做的四件事照原樣移植在 wrapper 的 `tail_v0101`：目錄修正、去重、兩種編號、截取完整度。
  - ENG393 v0101 只在傳入首頁主標題時才改變結果；VRN 只傳檔名，不需要它。
- **每一份樣本的流程**：
  1. 檔名拆解：類別、代號、規則、證據、公司名稱。只有個股報告往下走，其他列出類別和理由。
  2. 版面：每頁先左右、再上下切。每一區是資訊區、本文區、圖或排除區：
     - 資訊區：首頁右側卡片、頁首／頁尾帶、鍵值密集區、表格；
     - 本文區：一句一列，帶所屬標題和兩種編號（S0001、節.句）；
     - 排除區：免責聲明、跨頁重複的頁眉頁尾。
  3. 表格：合併格補值；整欄全空就左右拆，整列全空或出現新表頭就上下拆。
  4. 截取完整度：文字層每一個字都要被截到（≥ 99.9%），漏掉的原文寫進資料庫。
  5. 表格還原成「科目 × 期別 × 數值」：
     - 科目名稱是 `VRN_AnnualExtract_SSOT_v0100.json` 的 key（79 個科目，中英列標）；
     - 期別包含 2025E、FY25、1Q26、2H25、民國 113 年；
     - 只印年份的表頭（2026）也認得。
  6. 加減除驗算：`ssot/VRN_FinIdentity_SSOT_v0100.json` 共 36 條，每條註明出處：
     - 加減：毛利、營業利益、稅前、稅後、資產 = 負債 + 權益、流動 + 非流動、現金流、FCF、EBITDA；
     - 除法：毛利率、營益率、淨利率、EPS、每股淨值、ROE、ROA、負債比、流動比、速動比、本益比、股價淨值比、殖利率、配發率；
     - 另有年增率（六種狀態）和全年 = 四季加總；
     - 出處：FieldRules v0101、Method SSOT def07–def18、AnnualExtract formulas、首頁引擎 FinancialValidation。
  7. 判定：
     - 容差照 Method def15：差 ≤ Tol = PASS，≤ 3×Tol = WARN，> 3×Tol = FAIL；
     - 比率差 100 倍、每股類差 10 的次方 = UNIT_SCALE；
     - 結果印在表上、算式要的數字沒印 = INSUFFICIENT；
     - 只量不改。
  8. 目標價前次 → 本次（漲跌幅），評價法（倍數 × 指標 ≈ 目標價，容差 3%），方法詞（16 種）。
  9. 資料庫 `VRN_ReportRegions_v0100.sqlite`，表有 reports、regions、tables_、rows_、checks、sentences、entities、excluded、completeness。
- **加速器**：
  - PyMuPDF 不能多執行緒共用，所以檔案分塊，每塊一個子行程。
  - 分塊派工走加速器 accel_map，結果經 TEMP 回來（P09 列出）。
- **閘門**：
  - P14（`selftest`）：4 份已知答案的報告，逐項對答案，93 項；
  - G15（實測）：全部樣本加上同樣 4 份；資料庫在輸出夾的 `autotest/round1/`。
- **已知的限制**：
  - TXT／DOCX 沒有版面座標，走 ENG394 的文字模式：沒有左右上下切，而且會漏句（合成語料約 80%）。G15 照列 WARN，漏掉的原文在資料庫。
  - 影像檔要 OCR。
  - 官方實績比對要觸網（LIVE 關）。
- **判讀不變**：合成語料原有 378 列答案逐列相同，多出的只有 G15 的列與新模組的編譯列。
- **驗證矩陣（操作員「output the verified results in matrics」）**：
  - G15 在資料庫旁寫 `VRN_Verified_Matrix_v0105.html`。每一份樣本一列，並排：
    - 檔名拆解；
    - 首頁引擎原值；
    - 本機資料庫的 NAME／ADJ CLOSE；
    - 冊上驗證（G13）；
    - 版面左右上下切；
    - 表格還原、加減除驗算；
    - 目標價前→今、評價法。
  - 第二張表是「檔案 × 期別」對每一條驗算式的結果。
  - 另有兩個 CSV（UTF-8 BOM，Excel 直接開）。
  - 啟動器印出路徑，並和報告一起用瀏覽器開。
- **操作員上傳的 5 支 .py（2026-10-11）**：
  - 檔案本身不收，只收挑過的資料，寫進 `ssot/VRN_OperatorLabels_SSOT_v0100.json`：
    - 列標 213 個、整列標 regex 314 條，對到 84 個運算元；
    - TWSE／twstock／yfinance 欄名對照 46 個；
    - 券商叫法 32 家（只列候選，不併入）。
  - 每一項沒收的都寫了理由，例如「原物料」不是存貨總額、「商譽」是另一個科目、`net_income_cf` 的式子其實是稅前淨利、評等分類與 VRN「照原文」相衝。
  - 驗算式加 3 條（共 39 條）：
    - 現金淨增減 = 三種現金流 + 匯率影響；
    - 負債及權益總計 = 負債 + 權益；
    - 稀釋 EPS ≤ 基本 EPS（違反只到 WARN）。
  - 整列標 regex 只在書上的列標對不到時才用，而且整個列標要完全吻合（不是子字串），所以 EBT 不會吃到 debt。

## 輸出 DataFrame（操作員 2026-10-11「範圍限縮獨立系統VRN 輸出DATAFRAME 請確認完成」）

- **表頭正本**：`ssot/VRN_Output_Header_SSOT_v0100.json`。
  - 共 13 張輸出表：基本資料、財報數字、G15 資料庫九張、兩張驗證矩陣。
  - 每一欄寫明：名稱、型別（str／int／float／date／datetime／bool）、必填、主鍵，以及中文與顯示名。
  - 每一張表寫明最少列數。
  - 格式和母倉 `VIA_Output_Header_SSOT` 相同。
- **驗法**：母倉 `CGC_MDL249_DataFrameLock` 逐位元組收在 `engine/mother/`（VRN-MOM006），VRN 只叫它的 `check_table`：

  | 情況 | 判定 |
  |---|---|
  | 缺必填欄 | RED |
  | 多出冊上沒有的欄 | YELLOW（表頭未定案） |
  | 型別轉不過 | RED |
  | 必填但空 | RED |
  | 主鍵重複 | RED |
  | 列數不足 | RED |
  | 來源不在 | NODATA（照實寫，不冒充綠） |

- **G16**（每輪實測）：把這一輪的每一張輸出載成 pandas DataFrame 驗過。
  - 寫出 `autotest/round1/dataframes/<表>.parquet`（int → Int64、float → float64）和 `.csv`（UTF-8 BOM）；
  - 驗證結果寫在 `VRN_DataFrame_Lock_v0100.json`。
- **P14**（`selftest`）：已知答案報告的資料庫九張表也照表頭冊驗。
- **防漂移**：測試逐欄比對表頭冊和資料庫引擎的欄位次序、G15 的 SQLite 結構，兩邊不一樣就 FAIL。
- **實測結果**：合成語料 107 檔，13 張全部 GREEN。
  - 基本資料 106 列 × 70 欄；
  - 財報數字 696 列 × 55 欄。

- **表頭冊 v0101**（2026-10-11 G17／G18）：`ssot/VRN_Output_Header_SSOT_v0101.json` = v0100 的 13 張原封不動（測試逐字比對）+ 5 張新表，共 18 張；DataFrame 引擎改讀 v0101。

## 標題分拆、TRIM、鎖（操作員 2026-10-11「"C:\測試樣本報告" 只擷取個股報告的標題分拆識別 首頁及年度財報頁來進行基本資料清理TRIM後分拆識別 實測實修正 正確鎖功能鎖成功部分及引擎 位成功的持續實測實際修正直到輸出正確可驗證無誤」）

規則全部在冊上：`ssot/VRN_Method_SSOT_v0100.json`（def02 標題、def03 首頁、def05 列標、def16 NULL）與新冊 `ssot/VRN_TitleTrim_SSOT_v0100.json`（不可見字元一律寫成 `\u` 跳脫，冊裡沒有隱形字）。

- **只取個股報告**：ENG393 DocClass 判 STOCK 才往下；其他照實列原因。
- **標題分拆**（`engine/VRN_TitleTrim_v0100.py`，G17）：
  - 找標題照 def02 的來源次序：PDF metadata 標題（`Microsoft Word - x.docx` 這類不算）→ 第一頁上方 25% → 最大／次大字 → 前三行含公司＋代碼＋類型。**不假設第一行**。
  - 緊鄰、字級相近的行併成一個標題（標題印成兩行）。
  - 拆成 def02 七段：公司、代碼、市場、報告類型、核心觀點、評等變動、目標價變動。
    - 代碼：多個代碼不把第一個當主體；2021–2030 的四碼先當年份，檔名同號才算代碼。
    - 市場：只有 TT 就不產生 .TW／.TWO（def02 market_unknown_no_generate）。
    - 報告類型：多於一個就留候選和信心分數，不硬選。
    - 評等變動：動詞要緊挨評等詞；評等照原文印。
- **TRIM**（def02 八步）：全形轉半形 → NFKC → 異體字（含 PDF 常見的 CJK 部首補充區字）→ 不可見字元與重複空格 → 破折號／冒號／括號統一。
  - 原文 `raw` 永遠保留，清理後是 `clean`，比對用 `fold`。
  - 數字、百分比、負號、幣別少一個 = TRIM_LOSS（紅燈）。
  - 數值版另建：括號負數、倍數不轉百分比（def16）。
- **首頁基本資料**：每一行先 TRIM，再分 def03 七區，讀券商、日期、評等原文、目標價、現價、上漲空間（照 def03 重算比對）、分析師、電郵、電話、Yahoo 代碼。
- **年度財報頁**：G15 還原的表格逐格 TRIM，用 G15 同一套函式再讀一次；驗算 TRIM 前後各跑一次。
  - TRIM 只能讓驗算變好，變差 = TRIM_REGRESSION（紅燈）。
  - NULL（NA／NM／—）照印、不改 0；三角形符號 REVIEW，不猜正負。
- **兩條獨立讀法一致才算對（VERIFIED）**。
  - 讀法：檔名、首頁引擎、資料庫引擎（含它自己讀的財報表）、ENG396 全文、加減除驗算。
  - 狀態：

    | 狀態 | 意思 |
    |---|---|
    | VERIFIED | 兩條獨立讀法一致：上鎖 |
    | SINGLE | 只有一條讀法：值乾淨但鎖不住 |
    | NOT_PRINTED | 報告沒印（選填段落）：不是錯 |
    | CONFLICT | 讀法不一致：列待修 |
    | MISSING | 個股報告該有卻沒讀到：列待修 |
    | REVIEW | 多候選或要人判：列待修 |
    | UNMAPPED | 列標對不到科目（def05，不猜）：列待修 |
    | REPORT_CHECK | 驗算不過（讀錯或報告本身不一致）：列待修 |

- **鎖**（`engine/VRN_Lock_v0100.py`，G18、P16、`lock` 指令）：
  - 引擎鎖：`lock` 逐組跑已知答案（檔名 oracle、收來的冊、版面還原、DataFrame、標題與 TRIM、鎖、本機資料庫、TEMP），全過的引擎與冊記下 AST／JSON 指紋。
    - 只加註解（AST 編號）指紋不變；邏輯一改，`check`／測試就紅燈，要重跑 `lock` 重新驗過才換鎖。
    - 目前鎖住 37 支；PanoramaProbe 沒有已知答案，照實不鎖。
    - 指紋用自己的 AST 正規化（不用 `ast.dump`：它在 Python 3.12 → 3.13 改了輸出），Python 3.11／3.12／3.13 算出來一樣；測試有固定答案。
  - 輸出鎖：帳本在 VRN 資料夾外（`VRN_LOCK_HOME`，否則 `%LOCALAPPDATA%\VRN_Main\locks`），真報告的值不進倉庫。
    - 以「檔案 SHA-256 + 部位」為鍵。
    - VERIFIED 第一次 = NEW 上鎖；之後同值 = HELD；值變了或不見了 = BROKEN（紅燈，擋下）。
    - 要改就操作員明確解鎖；檔案內容變了 = 新檔，舊鎖不套。
    - 合成語料的帳本只放本輪資料夾，不碰操作員的帳本。
  - 待修清單：沒驗證的部位與退步的鎖寫成 `VRN_FixList_v0100.csv`／`.json` 與 `VRN_FixList_Paste_v0100.txt`。
    - 排序：優先 0 退步、1 不一致／缺／掉字、2 要人判、3 只有一條讀法。
    - 啟動器跑完會印出路徑和前幾行；**整份貼回對話**，下一輪照它修。
- **實測找到並修正的**（只修新引擎，既有引擎判讀不動）：
  - 全形數字與括號（`１，０００`、`（10）`）、全形負號 `－12`、零寬字元：G15 讀不到，TRIM 後讀到；已知答案逐項驗證。
  - PyMuPDF 預設裁掉頁面外的字（標題少一個字），改為不裁。
  - 英文標籤「Analyst」比對到電郵 `analyst@…`，改為跳過電郵／網址裡的字。
  - 年度財報格加資料庫引擎當第二讀法。
  - 待修清單是空的時候 JSON 寫成 `[]`，G16 誤判「缺必填欄」：空的 JSON 來源改為 0 列、表頭照冊。
  - 引擎鎖的指紋原本用 `ast.dump`，換 Python 版本就變：改成與版本無關的正規化（3.11／3.12／3.13 實測相同）。
  - 合成語料 107 檔（個股 59）：1615 個部位 VERIFIED 1369、NOT_PRINTED 236；年度財報格 612/612 VERIFIED；首頁基本資料 469/531；FAIL 0。
    - 待修 10 項：5 項是合成語料本身的毛病（2 檔沒印券商；3 檔把分析師名印成公司名，G17 抓出與檔名不一致）；
      5 項是同一個 TXT 檔只有一條讀法（首頁引擎不讀 TXT）。
    - 既有閘門逐列對前一次基準：378 列一列不少、狀態一個沒變，只多新閘門的列。
- **輸出表**（表頭冊 v0101，G16 驗）：`vrn_title_parts`（每檔一列七段）、`vrn_trim_parts`（每個部位）、`vrn_annual_cells`（每一格 TRIM 前後）、`vrn_lock_status`、`vrn_fix_list`。

## 只處理個股報告的檔名、第一頁、年度財報頁（操作員 2026-10-11「只擷取個股報告中的FILENAME / 1ST PAGE / 年度財報頁進行處理 其他多餘的」）

- **怎麼做**（`engine/VRN_Focus_v0100.py`，G19，在 G06 之前跑；門檻在 `ssot/VRN_TitleTrim_SSOT_v0100.json` 的 `focus`）：
  1. 每個檔案先拆檔名（ENG393）：非個股整份不處理，照列原因。
  2. 個股 PDF 每頁只讀一次文字（TRIM 後）。第一頁一定留；年度財報頁也留。
     - 年度財報頁 = 至少 2 個年度期別（2024A、2025E、FY25、113年…；季與半年不算）＋至少 8 個數字＋足夠的列標對得到財報科目（4 個；印了報表名稱的話 2 個）。
     - 本文、圖、免責、只有季資料的表都不留。
  3. 留下的頁在 TEMP 存成「聚焦副本」（同檔名，固定存法：同樣的頁存兩次位元組相同）。G06 起每一道閘都讀副本。
     - DOCX／TXT 沒有頁，個股就整份帶過去；個股影像照原檔帶（引擎照實列 OCR_REQUIRED）。
     - 掃頁失敗的個股 PDF 整份帶過去，列 REVIEW，不漏。
  4. 原檔只讀：SHA-256 前後相同才 PASS。
- **頁碼**：清單 `VRN_Focus_Manifest_v0100.csv／.json` 記「副本第幾頁 = 原檔第幾頁」；G17 的年度財報頁、每一格、每個部位都換回原檔頁碼。G15 資料庫裡的頁碼是副本頁碼，對照看清單。
- **鎖**：輸出鎖用原檔的 SHA-256，不用副本。
- **真值（G11）**：真值裡的非個股列 WARN（操作員範圍外）；真值寫個股、檔名拆解卻判非個股而被排除 = FAIL。
- **個股報告找不到年度財報頁**：G19 列 WARN，並進待修清單（`focus.annual_pages`，REVIEW）：確認報告本來就沒有，或告訴我是第幾頁。
- **輸出表**：表頭冊 v0102（v0101 的 18 張原封不動）加 `vrn_focus_files`（每個檔案：處理與否、原檔頁數、保留頁、年度財報頁、略過頁數、原檔 SHA-256）。
- **要整份全部處理**：`run --no-focus`（啟動器 `-AllPages`），回到之前的做法。
- **已知答案**（P17、引擎鎖的證明）：五頁個股報告（封面、本文、年度財報、季表、免責）只留第 1、3 頁；產業報告不處理；副本每一頁和原檔那一頁的文字一字不差；同頁同位元組；原檔不動。

## 真報告實測第一輪（C:\測試樣本報告，2026-10-12，b8ac050）

- **跑出來的樣子**：534 個檔案 → 個股 58 份處理（G19），個股 PDF 477 頁只讀 117 頁（年度財報頁 95）；全程約 5 分鐘（舊版 2166 秒）。輸出鎖 398 個部位全部 HELD、BROKEN 0。
- **紅燈與修法**（既有引擎判讀不動）：

  | 看到的 | 原因 | 修法 |
  |---|---|---|
  | G16 `vrn_basic_info` AdjCloseReportDate 1 筆不是 date | pandas 拿第一筆的格式套整欄，另一種寫法就判壞 | 日期欄逐筆讀、統一寫成 ISO；真的讀不出來仍是 RED，並印出樣本 |
  | G16 `vrn_financial_data` PeriodLabelRaw 48 列空、`vrn_regions_rows` metric_raw 52 列空 | 引擎對沒印期別／沒有列標的數字照實留空；表頭冊把它們設成必填是錯的 | 表頭冊 v0103：這兩欄改非必填（冊上逐項寫明，測試核對 v0103 = v0102 + 只有這兩項） |
  | G16 `vrn_title_parts` 狀態欄空 | 掃描檔找不到標題 | 狀態寫 NO_TITLE |
  | 標題「泓德能源(6873) - 逢低買進 $208」vs 首頁引擎「泓德能源(6873) 逢低買進 $208」判 CONFLICT | 兩行標題合併時插的「 - 」 | 比對只看字母、數字、中文 |
  | 神達現價讀成 2025 | 「股價 2025/11/27 …」的日期被當數字 | 價格先拿掉日期再讀；點號分隔要年月日三段齊（169.5 是價格） |
  | 日期讀到 2024-12-09／2026-06-03 | 取了首頁第一個出現的日期 | 「報告日期」標籤行 > 頁首 > 標題區 > 其他；法說會、除息、股東會等事件日期跳過 |
  | 券商讀成 FIRST | 「first half」的 first 當成第一金 | first、capital、mega、ms、gs… 這類普通字要接證券／投顧／Securities／Research 才算；先看頁首與分析師區，免責最後 |
  | 泓德目標價 345 vs 208 | 讀法各說各話 | 「前次目標價」不當目標價；印了上漲空間與現價時，現價 ×（1 + 上漲空間）反推也算一票，平手時算術那方排前面 |
  | GS／MS 報告找不到年度財報頁 | 外資把年度寫成 12/25E、Dec-25E | G15 期別多認這兩種（要有 A／E／F／P 或 12 月；11/27、Jan-25 不算） |

- **待修清單多了依據**：首頁讀到的值寫出是第幾行、那一行的原文；找不到年度財報頁的檔案寫出最像的那一頁、讀到的期別、沒認出的期別樣子、對不到科目的列標。下一輪照它修。
- **已知答案**：TitleTrim 加第 4 份報告（照這次實測的版面：前次目標價、帶日期的股價、事件日期、first half、免責提到別家券商）。
- **改名（判讀不變）**：全庫能力字典測試要求未分類函式名 < 35%，G19 之後超過一點。三支只在自己檔內用的小函式改成字典認得的名字：`write_copy` → `write_copy_file`、`context_from` → `report_context`、本輪新增的 `bad_samples` → `table_bad_samples`。前兩支舊編號退役（號碼不回收），引擎鎖重新證明。

## 真報告實測第二輪（C:\測試樣本報告，2026-10-12，1b4e718）

- **跑出來的樣子**：FAIL 5 → 2；G16 紅表 4 → 1；找不到年度財報頁 10 → 5（剩下的是 Note／Takeaway 短評與一份掃描檔）；個股 PDF 讀 134/477 頁（年度財報頁 95 → 115）；首頁 VERIFIED 208 → 212、CONFLICT 55 → 49；鎖 HELD 398、BROKEN 0、NEW 15。
- **紅燈與修法**（既有引擎判讀不動）：

  | 看到的 | 原因 | 修法 |
  |---|---|---|
  | G16 `vrn_basic_info` AdjCloseReportDate 樣本 `'<NA>'` | G08 冪等那次再入庫，pandas 把上一次的 parquet 讀回成空值是 pd.NA 的字串欄，寫出時 `str(pd.NA)` 變成文字 `<NA>`：第二次入庫改了第一次寫成空白的內容 | 資料庫引擎寫 parquet 的空值處理多認 pd.NA；舊檔裡的 `<NA>` 文字回成空白。測試：同一批入庫兩次內容完全相同（舊程式在這裡失敗） |
  | 泓德券商讀成 FIRST | 「第一階段」的「第一」是第一金的別名 | 第一、統一、大和、亞東、大華、新光這些常見中文詞當券商別名時，後面要接證券／投顧／證期／資本；長的別名（第一金）照舊 |
  | 兆豐四份（泓德、神達、志強、望隼）目標價讀成 345／78／125／233 | 兆豐首頁「前次投資建議：日期」的下一行是前次評等與目標價；本次的在頁首框「投資評等 目標價」的下一行 | 照證據核心同一套知識寫進 TitleTrim 冊：前次那一行不讀、標籤列取下一行、「前次／upside to／from」後面的標籤不算、前次投資建議的日期不是報告日 |
  | 同一行 ENG396 也讀 345 | ENG396（母倉引擎，不改）讀到前次那一行 | ENG396 的值等於前次那一行印的目標價時，照列「讀到前次那一行，不計」，不投票 |
  | 神達現價 26、志強現價 10 | 「12X 26(F) PER」「股價10-11x」 | 數字後面接 %、倍、x、億、年、(F)、「-11x」都不是價格（證據核心 _NOT_PRICE_AFTER 再加兩種） |
  | 志強「現價×(1+上漲空間)」投了 12.3 | 用了讀錯的現價 | 改成逐對試：兩條讀法的目標價與現價，只有一對合得上印的上漲空間才各投一票（目標價、現價都投）；合不上就不投 |
  | 中信金這類被研究公司 | 標題「中信金(2891)」會被讀成券商中信 | 被研究公司自己的名字（檔名、標題、首頁引擎）不當券商（首頁引擎同一個做法） |
  | 啟動器只印待修清單前 8 項、聚焦清冊另外複製失敗 | — | `VRN_Main_v0100.py pasteback`／啟動器 `-Command paste`：總結、全部優先 0／1、聚焦清冊個股列寫成 `VRN_PasteBack_v0100.txt`，跑完自動複製到剪貼簿 |

- **待修清單多了依據**：首頁那一行之外，再寫上一行與區塊名（看得出是不是前次那一行）。
- **已知答案**：TitleTrim 加第 5 份報告（兆豐頁首框、前次投資建議、第一階段、股價10-11x、12X 26(F) PER）；舊程式在這份讀成 78、CONFLICT，新程式 128、VERIFIED。

## 真報告實測第三輪（C:\測試樣本報告，2026-10-12，552f44d）

- **跑出來的樣子**：**FAIL 0**（第一次）、G16 全綠、BROKEN 0、HELD 413；首頁 CONFLICT 49 → 36；待修 673 → 661。
- **操作員要求**「全景式：修復產出後的文字、表格、分類分清楚」→ 貼回檔改成五段：一 燈號表、二 數字表、三 待修清單**按部位分類**（每個部位一張表：檔案、狀態／鎖、值、各讀法、首頁那一行）、四 **首頁原文**（有衝突的檔逐行列：行號、區塊、x 座標、★前次）、五 聚焦清冊表。原文只在第四段，表格用 `|` 分欄。
- **紅字與修法**（既有引擎判讀不動）：

  | 看到的 | 原因 | 修法 |
  |---|---|---|
  | 兆豐三份目標價仍讀到前次（78／125／233），「首頁上一行」卻是本文 | 右側框「前次投資建議：日期」和它下一行中間夾著左欄本文（照 y 排序時不相鄰），第二輪「讀取順序的下一行」沒接上 | 用**幾何**找同一欄的下一行（下方 ≤ 3 行高、左右重疊、最近）；TXT／DOCX 沒座標時照讀取順序 |
  | 3014TT 電話讀頁尾公司電話，引擎讀分析師的 +886 2 2326 9812 | TRIM 的電話式不認「+886 2」（國碼後一位區碼）；也沒分區塊先後 | 電話式加 +886 一、二位區碼；分析師、e-mail、電話**全部收下**，分析師區先、頁尾最後 |
  | 6933 e-mail 兩位分析師各讀一個 | 一份報告兩位分析師 | 引擎讀到首頁任何一個就算一致，值取共同那一個；「首頁全部」照列 |
  | 6933 目標價 MISSING、評等變動 NOT_RATED vs MAINTAIN | 未評等（NR）報告本來沒目標價；MAINTAIN 是維持字的預設 | 標題／檔名／首頁／引擎任一處說 NR：目標價 NOT_PRINTED 不是 MISSING；引擎的 MAINTAIN 不計，檔名 NR 多一票 |
  | 券商 MISSING 28 | 字裡沒券商別名（logo 是圖） | 用 e-mail 網域當首頁的讀法（kgi.com → KGI），來源寫明 |
  | G19 找不到年度財報頁 5 檔（Note／Takeaway／速報／NR／掃描） | 短評本來沒有 | 檔名帶 Note／Takeaway／速報／Memo／NR 的短評沒年度財報頁 = PASS 照列；完整報告找不到才 WARN |

- **已知答案**：TitleTrim 加第 6 份（前次框夾本文、兩位分析師、+886 2、NR 沒目標價、券商只在網域）；119/119。
- **還缺的證據**：112 項優先 1 的全貌（貼回檔第三、四段）。第四段的首頁原文是下一輪修讀法的依據。

## 真報告實測第四輪（C:\測試樣本報告，2026-10-12，02cd986）

- **跑出來的樣子**：鎖第一次擋下東西（BROKEN 1 → RED），但是假警報：帳本把電話「0223269899」當數字讀成 223269899（掉 0、浮點），這次 TRIM 又把分機 7960 接進號碼。首頁 CONFLICT 36 → 30、MISSING 28 → 26；G19 短評不再 WARN（只剩掃描檔 MQ-1560）。
- **紅字與修法**（既有引擎判讀不動）：

  | 看到的 | 原因 | 修法 |
  |---|---|---|
  | 國泰神達 cover.tel BROKEN：鎖住 '223269899' → 這次 '8.862232699e+11' | 帳本 canonical 把全數字字串當浮點；分機進了號碼 | 10 碼以上的數字字串照字串；電話部位比**後 8 碼**（國碼、區碼的 0、分機不算差異）；TRIM 的電話值只收主號碼 |
  | 志強／望隼目標價仍讀到前次（125／233） | 兆豐完整報告寫「前次投資建議 2025.08.06:」——冒號在日期**後面**，第二輪的式子只認冒號在前 | 前次那一行的式子兩種都認；「前次投資建議 日期:」後面接的標籤也不算本次 |
  | CLST 目標價讀 3,600 | 「raise our TP from NT$3,600 to NT$4,200」取了第一個數 | 標籤後是 from A to B／由 A 上調至 B／to B from A：本次是 to 後面那個，A 記為前次 |
  | CLST 現價讀 4,200 | 「12M price target」裡的 price 被當現價標籤 | 現價標籤前後 14 字內有 target／目標／12M 的不算 |
  | 3014TT／6933 標題 CONFLICT：引擎最大字是「I」、「國泰證券子公司 2023/10/05」 | 引擎的最大字那一行是頁首或殘字 | 不到 4 個字、或帶日期又沒有標題裡的代碼：照列、不投票（標題變 SINGLE，不是 CONFLICT） |
  | 貼回檔 82 KB | 第四段把本文每行都列 | 本文行只列被待修清單點到的那幾行（±1），其餘區塊照列；每檔 30 行、20 檔 |

- **已知答案**：加第 7 份（兆豐志強版面：冒號在日期後、頁首框、股價10-11x）、第 8 份（CLSA 英文：TP from／to、12M price target、分機）。
- **解鎖**：這次的 BROKEN 是帳本自己的假警報，修法後同一支電話會回到 HELD，**不用解鎖**。

## 核對矩陣（console，2026-10-12）

操作員：「real test and output validated results in matrix by rich for my reviewing」。

- **`engine/VRN_Matrix_v0100.py`**：一次實測的驗證結果畫成矩陣——**每份個股報告一列、每個部位一欄**（代碼、公司、券商、日期、評等、目標價、現價、上漲%、分析師、電話、年度財報格），格子是「讀到的值 ＋ 記號 ＋ 鎖」：✓ VERIFIED · ✗ CONFLICT · ~ SINGLE · ! MISSING · – 沒印 · ? 要人看；鎖 HELD · 新 NEW · 破 BROKEN（粗紅）。下面一張部位總計表和圖例。
- **rich 有就用**（操作員機器上裝了就用 rich 的表格與顏色；VRN 不裝任何套件），**沒有就同樣版面的純文字**＋ANSI 顏色（不是終端機、`--plain`、`NO_COLOR` 時不上色）；中英文寬度算對（CJK 兩格）。
- **跑完自動畫**：`run` 結束時印在 console（`--plain-matrix`、`--matrix-rows N`）；單獨看：`VRN_Main_v0100.py matrix [--out 夾] [--plain] [--rows N]`，啟動器 `-Command matrix`。同時寫 `VRN_Matrix_Console_v0100.txt`（無顏色）到輸出夾。
- 來源只是收攏（不另算）：G17 的 `VRN_TitleTrim_Results_v0100.json`、G18 的 `vrn_lock_status.json`、G15 的 `VRN_Verified_Matrix_v0105.csv`（G17 沒讀到券商時補）。G15 的 HTML 矩陣照舊。
- 已知答案：`selftest` 10 項（同寬、記號、鎖、G15 補格、總計、顏色只在要求時、BROKEN 粗紅、寫檔、沒結果說清楚、rich 可有可無）；列進引擎鎖。

## 代號紀錄與合併冊（2026-10-12）

操作員：「用四碼代號去資料庫找到 YFINANCE TICKER / BLOOMBERG TICKER / NAME / ENGLISH NAME / BROKER / ANALYST / TITLE / EMAIL / TEL / RATING / TARGET PRICE(ADJ.) / TARGET PRICE(ORIGINAL) / ADJ CLOSE / ADJ CLOSE BEFORE REPORT DATE / UPSIDE % 相關邏輯及 SSOT 同義字 REGEX 在一次跨不同專案整合去重不衝突整合一次完善一次」。

- **`engine/VRN_TickerRecord_v0100.py`** 兩件事：
  1. **合併冊 `ssot/VRN_TickerRecord_SSOT_v0100.json`**（`build-book` 生成）：倉內每一本有別名／標籤／regex 的冊——VRN 券商字典 v0100、v0103、券商清單、同義字聯集 v0107、同義字庫 v4、VRN 同義字冊（執行期）、操作員標籤冊、評等字典、S05 欄位冊、欄位規則、研報欄位尺、聯絡 regex、TitleTrim 冊、REGEX 冊、代碼主檔——合併成**一份**：券商別名 → 正典鍵（以 v0103 鍵為正典，首頁引擎答的那一套；同義字聯集對鍵的裁定 MEGABANK→MEGA 照用；v0100 的 YT 這類縮寫降為別名）、e-mail 網域 → 券商、評等詞 → 粗級（BUY／HOLD／SELL／NOT_RATED，只用來比對同級，輸出照原文）、目標價／現價／上漲／分析師／評等／日期標籤、前次字、各欄位的 regex。**去重**：casefold 相同折一條（券商別名 316 條，折掉 1,781 條重複），來源全列；**衝突**：同一別名兩本冊給不同正典 → 列在 `conflicts`，兩邊都留，不自動裁定（中信 CTBC／CITIC、國泰 CATHAY／國泰君安、Morgan Stanley 有一本冊寫 JPM 這類，操作員裁）。每本來源冊記 SHA-256；來源冊改了而合併冊沒重建，`selftest`（引擎鎖的證明）就紅。
  2. **紀錄**：一份個股報告一列、15 欄，每欄「值、狀態、來源」。不重讀報告：代號／公司／券商／分析師／標題／e-mail／電話／評等／目標價（原）取 G17 兩條讀法的結果；YF 代號取本機資料庫 `yf_ticker`（首頁印的 .TW/.TWO 碼一致 = VERIFIED，沒有就市場推）；Bloomberg 取首頁印的「<代號> TT」，沒印就推（DERIVED）；NAME 取資料庫（和報告中文名一致 = VERIFIED）；英文名取報告印的（資料庫沒有英文名欄，沒印 = NOT_PRINTED）；目標價（調整）、ADJ CLOSE（最新、報告日前）、上漲（調整後）取資料庫引擎列上的本機資料庫欄；上漲另列「印的／VRN 重算／資料庫調整後」。`lookup CODE --db` 單獨查四碼。
- **G20 RECORD**（G18 之後、G16 之前）：寫 `autotest/round1/titletrim/vrn_ticker_record.json/.csv`；表頭冊 **v0104** 加這張表（v0103 的 19 張原封不動），G16 驗；合併冊與來源冊不一致 = FAIL。
- **看**：`matrix --view record`／啟動器 `-Command matrix -View record`：15 欄矩陣，記號多「庫」（本機資料庫）、「推」（推算）；文字版 `VRN_Matrix_Record_v0100.txt`。
- **本輪沒動的**：既有引擎的判讀；原來各本冊（只增不減，合併冊是另一本）。

## 真報告實測第五輪（C:\測試樣本報告，2026-10-12，889085e）

- **跑出來的樣子**：RED（PASS 208 · WARN 18 · SKIP 4 · FAIL 13）。BROKEN 15 全是 cover.tel（鎖住的值 '8.862232698e+11' → 這次 '886223269812'）；G20 RECORD 說合併冊「來源冊變了」；本機資料庫第一次在場，標題七段 CONFLICT 36（Wiwynn vs 緯穎、頎邦 vs 頎邦科技股份有限公司、慧洋 vs 慧洋-KY）；首頁 CONFLICT 22（Citi 3231 現價 TRIM=4.0 vs 引擎 114.0 這類）；Daiwa 兩份券商 CONFLICT。鎖 HELD 449、鎖住部位 464。
- **紅字與修法**（既有引擎判讀不動）：

  | 看到的 | 原因 | 修法 |
  |---|---|---|
  | cover.tel BROKEN 15：'8.862232698e+11' → '886223269812' | 第四輪之前寫的帳本把電話當浮點存，只剩 10 位有效數字（失真，後 8 碼對不回來） | 舊值是失真浮點（`d.ddde+NN`）而新值以 10 位有效數字寫回去相同 = 同值 → HELD；帳本改記完整號碼（`healed` 事件記在帳本紀錄），**不用解鎖** |
  | G20 RECORD FAIL：合併冊來源冊變了 | 操作員的 Windows 檢出是 CRLF，每本來源冊的 SHA-256 都和入庫時不同 | 來源冊算 SHA 前先把 CRLF 折成 LF（合併冊、G20、selftest 同一個算法） |
  | title.company CONFLICT：首頁引擎=Wiwynn vs 本機資料庫=緯穎 | 標題沒印公司時，不同文字的名稱也被拿來互比 | 以標題（沒有就第一個有值的來源）的文字為準，另一種文字的名稱照列不投票（來源名後註「不同文字，不比」） |
  | 頎邦 vs 頎邦科技股份有限公司、慧洋 vs 慧洋-KY | 資料庫是官方全名，報告是簡稱 | 公司名比對去掉 -KY 與公司形式字（股份有限公司／Corp／Co., Ltd.…）後，相等或一方是另一方的開頭／包含（中文 2 字起、英文 4 字起）就算同一家 |
  | 現價讀 4／16／19／17（Citi 3231 114.0 讀成 4.0） | 「Price (as of 4 Jun 2025)」「股價 (May 19, 2026)」裡英文日期的「日」被當價格 | 日期式子加英文月份三種寫法（4 Jun 2025、May 19, 2026、Jun 2025），價格行先拿掉；標籤後的括號註記放寬到 28 字 |
  | Daiwa 3653／6278 券商 CONFLICT（e-mail 網域 daiwacm-cathay） | 網域用字找券商讀到 cathay | e-mail 網域先查合併冊的 `email_domain`（最長鍵先、兩本冊有爭議的鍵跳過），再退回字典 |

- **已知答案**：TitleTrim 冊 `date_like_rx` 加英文月份並記 `date_like_note_r5`；TITLETRIM 證明的 covers 多列合併冊（讀法現在讀它）；Lock selftest 11 項、TickerRecord 13 項；三支測試各加一條。
- **還要證據的**（等貼回檔第 4 段）：凱基 2891 中信金／啟碁 的券商 CONFLICT、晶心科／頎邦／達發 的日期 CONFLICT、UBS 6409 目標價 1128、3014TT 標題頁首殘字。
- **母倉 FirstPageEngine v0113 矩陣**（2026-09-11，64 件）：官方證券名、目標價與本輪讀法一致（泓德 208、神達 128、志強 145、望隼 238、3014TT 187 CATHAY、CLST 4200），可當 G11 真值的第三條讀法；轉換器 `truth-from-matrix`（下一節），真值檔照舊只在操作員手上。

## 第五輪重跑（C:\測試樣本報告，2026-10-12T23:23，仍是 889085e）

操作員重跑時還沒 `-Command update`（版本列印 889085e），所以 BROKEN 15、G20、Wiwynn／緯穎這些第五輪已修的照舊出現；`-Command truth` 也因此不認得。這次的窄視窗矩陣把值印出來，看得到第五輪沒涵蓋的幾件：

| 看到的 | 原因 | 修法 |
|---|---|---|
| 凱基 6 份現價 = 報告日的「日」（19／15／17） | 價格行的日期沒有年份（5月19日、May 19、19-May-26）就沒被拿掉 | 日期式子加沒有年份的月日三種寫法（英文月份要大寫開頭，may 是普通字），價格行先拿掉 |
| Daiwa 3653／6278 目標價 MISSING | Hold 報告在目標價標籤後寫 n.a.（母倉矩陣也記 N/A_TP_DECLARED_NA） | 目標價標籤後直接寫 n.a.／N/A／不適用 = 報告寫明沒有目標價：NOT_PRINTED，理由寫出第幾行 |
| 待修清單的證據一直回不來（62 KB 貼回檔沒貼） | 操作員貼的是 console | 待修清單（txt／csv／json，不是 G16 驗的 `vrn_fix_list` 表，那張表頭冊 v0104 不動）每列多一欄 `evidence`：那個部位讀自首頁第幾行與原文（TRIM 沒讀到值時，列出第一個帶標籤的行；標題列標題）；不一致排在缺的前面；啟動器跑完印待修清單前 60 行（不是 12 行） |
| `-Truth` 給了不存在的 .truth.json | 還沒轉檔 | `-Truth` 直接給貼文檔也可以：不是 JSON 就先用 VRN_TruthMatrix 轉成旁邊的 `.truth.json` 再交給 G11 |

- 還要證據的照舊：MS-1590 公司讀成「trade tension…」、凱基 2891／啟碁／華南 2762 券商、晶心科／頎邦／達發日期、UBS 6409 目標價 1128——更新後重跑，console 的待修清單會直接印出那幾行原文。

## 真報告實測第六輪（C:\測試樣本報告，2026-10-13，b42f45f）

- **跑出來的樣子**：AMBER，**FAIL 0**、BROKEN 0（第五輪的 15 支電話自動改記完整號碼，HELD 472）。公司 CONFLICT 26 → 1、現價 CONFLICT 8 → 2。console 第一次帶回每個不一致的首頁原文行，這輪 27 個 CONFLICT、24 個 MISSING 都照原文找到原因。
- **紅字與修法**（既有引擎判讀不動，改在 TRIM 讀法與冊）：

  | 看到的（首頁原文） | 原因 | 修法 |
  |---|---|---|
  | Daiwa 3653／6278 券商 TRIM=CATHAY：「helen.chien@daiwacm-cathay.com.tw」 | e-mail 裡的 cathay 被當券商字，網域規則沒跑到 | e-mail／網址裡的字不算券商字；網域查合併冊時跳過不是引擎鍵的正典（DAIWA-CATHAY），下一個鍵 daiwacm-cathay = DAIWA |
  | 啟碁 TRIM=YUANTA：「EPS 3.37元大致符合預期」 | 元（新台幣）＋大致 | 中文券商別名前面緊接數字不算；元大要接證券／投顧 |
  | 華南 2762 TRIM=TAISHIN：「今年已在台新增10家分店」 | 在台＋新增 | 台新、元大、華南、中信、國泰當普通字：要接證券／投顧／永昌等字 |
  | 凱基 2891 TRIM=CTBC：「主要中信銀提存前獲利」 | 被研究的中信金的子公司 | 同上（中信要接證券／投顧） |
  | 頎邦、達發 日期 2061-08-04／2016-04-03：「市值 (NT$bn/US$mn) 150.8 / 4,777」 | 讀成民國 150 年 8 月 4 日 | 日期兩個分隔符要相同、點號旁不留空、後面不接千分位、年份不超過明年 |
  | 凱基儒鴻現價 318、貿聯 600：「52 週股價 (低 \ 高) (NT$): 318.0 -466.0」 | 52 週區間的「股價」 | 現價標籤前後有 52 週／區間／低 \ 高 的不算 |
  | MS-2308 上漲 15%：「potential upside to our mid-term growth rate of 15%」 | 內文 | 上漲空間的數字要在標籤後 20 字內 |
  | UBS 6409 目標價：ENG396 全文 = 2026 | 年份 | ENG396 的全文目標價像年份（1990 到明年 +1 的整數）不投票，照列（TRIM＋首頁引擎 1128 一致 → VERIFIED） |
  | 凱基貿聯 e-mail「13.7terry.lee@kgi.com」、慧洋電話「7.6886 2 2181 8710」 | 表格數字黏上去 | e-mail 前面黏的小數拿掉；電話前面緊接數字或小數點的不收 |
  | 國泰神達評等 TRIM=S：「ESG 評等社會(S)」 | ESG 評等 | 評等標籤前面 8 字內有 ESG／永續／信用／MSCI 的不算 |
  | 華南慧洋評等 TRIM=區間（原文「投資評等區間持有」） | 只印了別名 | 照原文印全：區間持有（首頁引擎讀買進，照樣 CONFLICT，要人看） |
  | 瑞基公司「未評等瑞基」 | 標題裡評等字黏在公司名前 | 公司名前的未評等／無評等拿掉 |
  | 南亞、啟碁、晶心科、欣銓、瑞基、光焱、國光生、國泰神達 標題 CONFLICT：首頁引擎最大字 =「個股報告」「個股摘要」「投資 顧問」 | 那是版頭，不是標題 | 首頁引擎最大字沒有代碼、也沒有公司名，而 TRIM 標題有代碼：不投票（照列） |
  | JP-2330／3653 標題「tsmc(2330TW)-JPM-250718」 | PDF 屬性 Title，不是首頁印的 | 標題來自 PDF 屬性時不和首頁印的字比（照列）；代碼與公司仍照比 |
  | 晶心科日期：首頁 2025/12/06（兩條讀法一致）vs 檔名 251208 | 檔名是發送日 | 首頁兩條讀法一致、檔名晚 1–7 天：檔名照列不比；早於首頁或晚超過 7 天照樣 CONFLICT |
  | Note／Memo／Takeaway 的評等、目標價 MISSING（17 項） | 短評本來不一定印 | 短評（冊的 short_report_words）沒讀到評等／目標價 = NOT_PRINTED，理由寫明；讀到了照樣比 |
  | 待修清單證據行把「FTPS」當目標價標籤 TP | 證據行用子字串找標籤 | 證據行改用讀法同一套標籤規則 |

- **還要人看的**：華南慧洋評等（首頁原文「區間持有」，兩支首頁引擎都讀買進）；凱基慧洋電話（TRIM 不收黏字後，只剩首頁引擎的 09251125012，11 碼，像少一位或多一位）；JP 兩份的標題（PDF 屬性 vs 首頁最大字）；Daiwa／GS-1590 的評等 MISSING（首頁沒有「評等」標籤，原文要看第 4 段）。

## 公司名稱與價格一律取資料庫（2026-10-13）

操作員：「公司名稱價格一率至DATABASE去取」，資料在 `via_database\vdf_database\`（tw__tw_listings.parquet、tw__tw_listings_industry.parquet、tw__tw_daily_prices.parquet，及其他 VDF 匯出）。

- **讀哪裡（`engine/VRN_LocalDB_v0100.py`）**：先讀 `vdf_database` 的 parquet 檔（記憶體裡的 duckdb、唯讀視圖、不複製不寫入），沒有才讀 `vdf_tw_market.duckdb`／`VIA_Parquet_Catalog.duckdb`。位置：`VRN_LOCALDB_PARQUET` 指定的夾，否則 `<資料家>\vdf_database`（資料家 = `VIA_DATA_HOME`，否則 `%USERPROFILE%\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database`）。欄位靠名字對：VDF 的名稱優先（code、name、date、ticker、close、adj_close），常見別名也認（stock_id、stock_name、trade_date 寫成 20260518、symbol、Close、Adj Close、證券代號…）；對到哪一欄寫在 `describe()`。名冊：tw_listings_industry 的簡稱優先，沒有才用 tw_listings。
- **公司名（G17 title.company）**：值 = 資料庫的名稱（四碼代號查名冊）。報告讀到的（標題、首頁引擎、檔名）拿來核對：同一種文字有一個是同一家（去掉 -KY、股份有限公司等，開頭相同也算）= VERIFIED；同一種文字的都指別家 = CONFLICT（要人看，值仍是資料庫的）；報告只有英文名或沒讀到 = SINGLE（另一種文字的照列「不同文字，不比」）。資料庫沒有這個代號才照舊用報告的讀法。
- **現價（G17 cover.current_price）**：值 = 資料庫的**原始收盤價**（報告印的是原始收盤價，不是調整後）：報告當日或報告日前最後一個交易日，看報告印的是哪一個；兩個都對不上 = CONFLICT（值取報告日前最後一個交易日），報告沒印 = SINGLE。來源寫「資料庫收盤價 YYYY-MM-DD」。adj_close 規則照舊（調整後目標價、ADJ CLOSE 用 adj_close，從不拿 close 頂）。
- **報告自己讀到的值**留在部位的 `printed`；代號紀錄（G20）的 NAME 用資料庫、用 `printed` 核對中文名，英文名取報告印的（名冊有英文名欄時也給）。
- **鎖**：值改取資料庫是**換來源，不是退步**——原鎖換成資料庫的值（VERIFIED 重新上鎖、其他放開），帳本記 `source_db` 事件，不算 BROKEN；之後資料庫的值再變照樣擋。公司名同一家的寫法差異（慧洋／慧洋-KY、頎邦／頎邦科技股份有限公司）算同值。
- **矩陣**：值取自資料庫的格子多一個「庫」（例：`慧洋-KY ✓庫鎖`）。
- **已知答案不碰真資料庫**：TitleTrim 自測與單元測試用的是虛構報告（2330 一千元），跑自測時資料庫關掉，每台機器的證明結果相同。
- **快取**：入庫步驟的快取鑰匙包含 parquet 檔的大小與修改時間；資料庫更新了就重讀。

## 速度：先看機器、TEMP 快取、六步同時跑（2026-10-13）

操作員：「上面指令執行速度太慢 確認所有PS都有加速器 善用TEMP強力支援不足的記憶體 過去跑過的資料在輸入還沒換之前不要刪除 TEMP 避免重跑 再進行前檢視一下CPU/記憶體/TEMP加總的能力 在不影響指令系統不產生九頭龍風險下進行六個獨立步驟同時跑」。

- **先看機器（P00 RESOURCES）**：開工前量 CPU 核數、記憶體總量與可用、TEMP 剩餘、快取已用；據此定 G15 版面還原的子行程數（留 1 核、每支約 0.6 GB、最多 8 支）與快取上限（TEMP 剩餘的 25%，最多 `VIA_CACHE_MAX_GB`，預設 10 GB）。console 第一行 `[RESOURCES]`。
- **TEMP 快取（`engine/VRN_RunCache_v0100.py`）**：快取在 `<TEMP 根>/VRN_Main/cache`（`%LOCALAPPDATA%\Temp\VIA_progress\VRN_Main\cache`；TEMP 清掃只刪 run_* 夾，快取跨輪留著）。快的是最重的五步：

  | 步驟 | 重用的條件（鑰匙） |
  |---|---|
  | P07／G19 原檔 SHA-256 | 檔案大小與修改時間沒變（git 的作法）：沒動過的檔不再讀 |
  | G19 聚焦副本 | 每份原檔的 SHA ＋ 聚焦程式（含 TitleTrim、PageRegions、母倉引擎）＋ 冊；副本放在 `focus_copies/<樣本組>`，同一組樣本同一個夾 |
  | G06 入庫、G08 冪等 | 輸入檔（聚焦副本）的 SHA ＋ 輸出夾呼叫前的內容（這一輪的路徑不算）＋ 參數 ＋ 入庫／首頁／證據核心／本機資料庫／代碼主檔程式 ＋ 冊 ＋ 本機資料庫檔；還原時夾裡寫的舊輸出路徑換成這一輪的 |
  | G07 首頁引擎 | 檔名 ＋ 檔案 SHA ＋ 首頁／證據核心／代碼主檔程式 ＋ 冊 |
  | G15 版面還原 | 檔名 ＋ 檔案 SHA ＋ PageRegions 與母倉引擎 ＋ 冊（已知答案的 4 份每輪照算） |

  鑰匙另含 Python 與套件版本（PyMuPDF、pdfplumber、pdfminer、pandas、pyarrow、numpy、python-docx、duckdb）與影響引擎的環境變數。程式用 AST 指紋（build 注入的編號註解不算）；冊用正規化 JSON（CRLF、鍵順序不算）。**冊的相依取「全部冊減掉確定沒讀的」**（每輪生成的編號、索引、引擎鎖、REGEX、同義字、代號紀錄、表頭冊、TEMP 政策；G17 之前的步驟另減 TitleTrim 冊）——2026-10-13 逐一追蹤實測時每步開了哪些檔量出來的；冊多算只會慢、不會用到舊答案。
- **刪除（寫進 `ssot/VRN_TEMP_POLICY_v0100.json` 的 cache 段）**：輸入沒換不刪；樣本換了留現在與上一組；同一組樣本但引擎或冊改了，該步驟這一輪沒用到的舊答案刪；超過上限最久沒用的先刪；每筆刪除記在 `<快取>/purge_ledger.jsonl`。同時開兩個 VRN：後開的不用快取（照常重跑），不互相蓋。`-NoCache`／`--no-cache` 這一輪全部重讀；`python engine/VRN_RunCache_v0100.py status|clear|resources`。
- **六個獨立步驟同時跑**：P01 環境（載入 PyMuPDF、pandas…）、P02 SSOT 三本冊、P03 註冊冊＋P11 AST 編號、P16 引擎鎖、P07 樣本 SHA、P08 冊＋P14 本機資料庫＋P13 本機 SSOT——都只讀檔、載入套件、算雜湊，沒有一個開 PDF；用執行緒同時跑，列照原來的順序回來。要開 PDF 的 P15（造已知答案 PDF）在它們之後單獨跑（PyMuPDF 不能多執行緒共用）。**零九頭龍**：模組載入加鎖（同一模組只載一次）；「靜音」只靜本執行緒（不再整個換掉 console，免得多執行緒換回時 console 不見）；一步出錯變成那一步的 FAIL 列，其他照跑。
- **看時間**：跑完印 `[TIME]`（各閘秒數，最慢的在前）、`[CACHE]`（每步命中／重讀、省幾秒）；報告多 `P00 RESOURCES`、`P00 CACHE`、`P20 CACHE`、`P20 TIME` 列，迴圈報告 JSON 多 `timing`、`cache`、`resources`。
- **沙盒實測**（同一個固定樣本夾 107 檔，4 核）：

  | 跑法 | 全程 | 各閘合計 |
  |---|---|---|
  | 不用快取 | 35 秒 | 27.5 秒 |
  | 第一次（建快取） | 36 秒 | 29.8 秒 |
  | 第二次（全部命中） | 18 秒 | 11.2 秒 |

  第二次的 TitleTrim 結果、待修清單、代號紀錄、財報資料、驗證矩陣、DataFrame 全部和不用快取的那次逐檔相同；快取還原的入庫夾和它當時算出來的逐位元組相同。暫改 TitleTrim 冊：只有聚焦重做，入庫、首頁、版面還原照樣命中（聚焦副本位元組沒變）；暫改券商字典：入庫與首頁重讀。真報告的五步佔一輪大部分時間，只改 TRIM／鎖這類後段程式時，重跑主要剩 G17 之後。
- **PS 加速器**：`Invoke-VRN-Main-v0100.ps1`、`Invoke-VRN-AutoTest.ps1` 兩支都 dot-source `VIA_PS_Accel_Module.ps1`（看門狗 `Invoke-VIAGuarded`、進度 `Write-VIAProgress`），P03 也檢查每支 .py／.ps1 都帶加速器橋。啟動器用 `-NoProfile`，所以個人設定檔載入的 63 秒不在 VRN 的時間裡。

## 母倉矩陣 → G11 真值檔（2026-10-12）

操作員貼了母倉 `VIA_VRN_FirstPageEngine v0113` 的解讀矩陣（2026-09-11，64 件：報告檔／型別／代號／券商／報告日／官方證券名／TP／評等／各閘判定）。它是同一批報告的第三條讀法，拿來當 G11 的已知答案。

- **`engine/VRN_TruthMatrix_v0100.py`**：把整頁貼文（記事本存檔，UTF-8／UTF-16 都可；tab、markdown `|`、多空格分欄都認）轉成 G11 讀的真值檔。欄位靠表頭名找（報告檔、型別、代號(頁面)／(檔名)、券商(頁面)／(檔名)、報告日、官方證券名、TP、評等、文字層、總判、各閘），不靠位置；第一格是檔名的行才算一列。
- **怎麼轉**：型別 個股→STOCK、產業→INDUSTRY、大盤晨報／海外→MARKET、研討會→EVENT、總經→MACRO；代號取頁面的、沒有取檔名的；券商經**合併冊**（GOLDMAN→GS、MORGANSTANLEY→MS、MACQUARIE→MCQ；兩本冊有爭議的別名以首頁引擎那本（v0103）的讀法為主、兩個讀法都收進 `accept.broker`；沒一本冊認得的照印並標記）；評等詞對成等級（BUY／HOLD／SELL／NOT_RATED，ADD 算 BUY，和證據核心同一套），引擎輸出照舊是原文；目標價照數；官方證券名當公司名；文字層 NO_TEXT 的掃描檔 `text_layer=false`。
- **矩陣沒說的不判**：真值列多一個 `unknown` 清單——矩陣沒有現價欄，所以每筆個股的現價都是「不保證」；報告日 `-`、評等 `-`、目標價 `-` 而閘是 WARN 的也是（母倉自己沒讀到，不等於報告沒印）；只有閘寫 `N/A_TP_DECLARED_NA` 的才是「報告自己說沒目標價」。日期只在母倉總判 PASS 的列才判（檔名與頁面在那裡一致）。G11 的 `def_truth_compare` 對 `unknown` 裡的欄不比（只加這一條，舊真值檔沒有 `unknown` 照舊）。
- **真值檔不入庫**：預設寫在貼文檔旁邊 `<貼文>.truth.json`，`--out` 另指；路徑在 VRN 樹裡就拒寫。
- **用**：`VRN_Main_v0100.py truth-from-matrix <貼文.txt> [--out 真值.json]`，啟動器 `-Command truth -Matrix <貼文.txt> [-Out 真值.json]`；之後 `run --truth 真值.json`／啟動器 `-Truth 真值.json` 就有 G11 逐欄比對（代號／券商／日期／評等／目標價錯一格 = FAIL）。
- 已知答案：`selftest` 19 項（合成的 7 列，不含真報告）；列進引擎鎖，covers 含合併冊。
- 第五輪重跑後補：母倉自己的券商鍵也收進 `accept.broker`（首頁引擎答 MACQUARIE、合併冊寫 MCQ，兩個都算對）；`run --truth`／`-Truth` 直接給貼文檔也行（先轉再用）。

## SSOT 規則（子系統生成、VCGC 只檢衝突）

- **REGEX**：程式裡的 regex 是執行本體，冊是唯一登記處。改了任何一條就跑 `build`；`check` 會逐條列出新增、消失、使用點改動，行號變動不算。冊裡 `shared` 標出用在多處的 regex，是合併候選，不自動合併。
- **同義字**：冊的內容取自引擎載入完知識書之後的執行期狀態，載入順序是內建 → `SYNONYM_LIBRARY_v4` → `ssot/` 字典，一個別名只有一個主人。衝突只顯示、不自動改；要改同義字，就改 `ssot/` 或 `knowledge/` 裡的書，再跑 `build`。
- **出處**：`ssot/` 的三份副本，在複製當下和 `attachments/` 原書逐位元組相同。之後原書如果變動，`check` 顯示 CONFLICT（黃），VRN 副本仍為準。
- **行尾**：所有 SHA-256 都以 LF 行尾計算，Windows CRLF 取出不影響。

## 獨立性證明

`standalone` 會把 VRN 資料夾單獨複製出去再跑。結果：
- 引擎讀的 5 本知識書全部在 VRN 資料夾內；
- 兩支引擎對 106 個檔名的答案，和在倉庫內逐筆相同。

改版前（`ea1a2e8`）單獨複製時，券商字典、評等字典、檔名代號 SSOT 三本書都找不到：首頁引擎少 27 個券商別名，資料庫引擎少 50 個。

## 待操作員裁定（只顯示，未改判讀）

> **2026-10-18 逐條對過現況。** 一份過期的待辦比沒有待辦更糟 —— 操作員會照著去做已經做完的事，
> 或照著一個重現不出來的數字去查。下面每一條都標了最後一次量到的時間與數字。

1. **共用 regex：56 條**（2026-10-18 重量；舊紀錄寫 19 條，已過期）。合併候選，詳見 REGEX 冊的
   `shared`（`VRN_REGEX_SSOT_v0100.json` → `shared`，56 個 RX 代號）。
   參考：2026-10-17 用 VCGC 既有的整合規劃器掃過 200 個候選，只有 1 個可證明安全，而且是 3 行的
   `_decimals` —— 為了零收益把兩支綁在一起，當時判斷不划算。

2. **首頁引擎的評等變動**（2026-10-11 G17 找到）：首頁引擎在整頁找「上調」，「目標價上調至」被當成
   評等調升（UPGRADE）；本文的「維持在高檔」被當成 MAINTAIN。G17 的標題讀法正確（動詞要緊挨評等詞），
   兩者不一致時列 CONFLICT 進待修清單。要不要改首頁引擎（「目前邏輯不可動」）由操作員決定。
   > **2026-10-18：現行合成語料重現不出來。** `title.rating_action` 59 檔全是 `NOT_PRINTED` ——
   > 語料生成器根本不印評等變動那一句。引擎的行為可能還在，但**現在沒有樣本能證明它**。
   > 要裁定，得先有一份會印「評等由中立上調至買進」而且本文另有「目標價上調至」的樣本。

3. **資料庫引擎的 ReportTitle 取第一行**（2026-10-11 G17）：合成語料 59 檔有 57 檔取到券商頁首，
   違反 def02「不假設第一行」。G17 另出 def02 標題（`vrn_title_parts.title_clean`），引擎本身沒改；
   要不要讓資料庫引擎改用 G17 的標題由操作員決定。
   > **2026-10-18 重量：還是 57/59**（`db_title` 與 `title_clean` 相同的只有 2 檔，其餘 57 檔的
   > `db_title` 都是「<券商>證券投資顧問 <CODE> Securities Research」）。這一條照舊成立。

4. **ENG396 叫不出公司名的個股檔 29 個**（2026-10-18 新列）：那 29 檔的合成頁用佔位名「測試公司」，
   等於**公司名抽取沒有驗到**（`Citi-3231 20250604.pdf`、`CLST-6669 20251001.pdf`、
   `Daiwa-1319 20231011.pdf` 這類檔名裡本來就沒有中文公司名）。G05 CORPUS 會列出來。
   要補覆蓋，得讓這些檔的合成頁帶上可辨識的公司名 —— 但**不可以回頭自己解析檔名**（那是第二顆頭，
   見下面「已裁定」）。由操作員決定要不要補、以及補成什麼。

已裁定 / 已完成：
- 「評等跨引擎分歧」：評等顯示原文、不分類，所以沒有等級可以分歧。
- 「GF 與批679」：GF 照原文顯示。
  **2026-10-18 合成語料現況：ROUND 1 PASS 374 · WARN 6 · SKIP 7 · FAIL 0**（舊紀錄寫
  「PASS 357 / WARN 1 / FAIL 0」，已過期）。
- ~~「PanoramaProbe 沒有已知答案，所以不在引擎鎖裡」~~ → **已完成**（2026-10-17）。
  `selftest()` 給了 14 條檔名契約的已知答案（NFKC、副檔名、日期合法性、代號／券商／報告日），
  兩邊都接好了：`def_run_proofs()` 與 `VRN_TitleTrim_SSOT` 的 `lock.proofs.covers`。
  現況 `VRN_EngineLock_SSOT_v0100.json`：證明組 15 個（含 `panorama`，`ok: true`、`14/14`）、
  鎖住 50 支、`unlocked` 空的；`engine/VRN_PanoramaProbe.py` 的 `proofs` 是 `["panorama"]`。
- 「語料自己再判一次公司名」：**不做**。#58／#59 拆掉的那一份在 -KY 與「中信金」上把分析師寫成公司，
  裝回去當退路，3 筆 CONFLICT 就會回來。缺口用「報出來」處理，不用「再判一次」處理。

## 治理

- LIVE 關、不連網、不安裝套件、不設定 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`。
- 真實報告和真值檔只放在操作員手上，不入庫。
- `VRN_Main` 的 `main()` 自行設定 `VIA_FROM_VCGC=YES`，作為自立閘座（與 FLOW 針相容），並保留 `def main` / `def selftest`。
- VCGC 鏡像（倉庫根 `supportive modules/registry`）屬於 VCGC，不屬於 VRN：VRN 會和它互動；鏡像缺席時，證據核心退回內建表照跑。

---

> **一個指令：`.\VRN-1.ps1 all`（2026-10-16）**：操作員「給我一個指令去啟動；所有 py／ps
> 都要加入加速器；現在只進行 VRN-1；善用 VCGC 的節省 token 工具；VDF 所有引擎都要加入
> 網路工具；HTML U/I 輸出驗證無誤為收尾目標」。
>
> **先查了現況，結果是五件事裡有三件早就做完了** —— 缺的是接線與可見度，不是新引擎：
>
> | 要的 | 查出來的現況 |
> |---|---|
> | 一個指令 | `all` 在 MAIN 裡，但 `VRN-1.ps1` 的 ValidateSet 沒有它 —— 操作員按不到 |
> | 所有 py／ps 加速器 | **已經 100%**：`scripts/VIA_BridgeInjector.py --check` = PASS（py 92/92 · ps1 47/47） |
> | VDF 引擎網路工具 | **已經 3/3**，`[VIA:NET-BRIDGE:v0100]` 批115 全導入令 |
> | VCGC 省 token | 正本在 Root SSOT `#/token_governance/capsule_policy`，收尾沒用它 |
> | HTML U/I 驗證 | 只產出、會自動開，**沒有任何檢查** |
>
> 跳過的 10 支每一支都有成文理由（`sealed-delivery` 7：有位元組清單的封存交付／
> `engine-original` 2：加速器與網路工具本體／`stdlib-only-bundle` 1：VUE 自己封了
> 「只用標準庫」，加橋會破壞那個契約）—— 不是漏掉，是法。啟動器的④現在把理由印出來。
>
> **做的四件事，全部委派既有擁有者：**
>
> 1. `VRN-1.ps1 all` → `ActivateVRN-1.py all` → 啟動體檢（①~⑥，啟動器自己的）→ MAIN 的
>    `all`（build → lock → check → run）。體檢紅燈就停，不往下跑。
> 2. ④ 多印 VDF 網路工具橋的數字（注入器本來就算了，只是沒顯示）；⑥ 多一列「網路工具」，
>    **問擁有者 VDF 引擎的 `VIA_NET_TOOL_PATH`**，不自己再抄一份查找邏輯；同意閘
>    `VIA_NET_CONSENT` 照實回報，**本支不代設**（法遵雙閘）。
> 3. **P20 UI 閘**：HTML 存在不算數，要跟 JSON 對得上才算數 —— 標籤開合、結論、計數、
>    閘列數、每一個 href 點得到。驗不過 `run` 就回非零，**收尾目標是驗證無誤，不是有檔案**。
> 4. 收尾印 VCGC 的 token 預算（`def_capsule_budget()` 讀 Root SSOT，讀不到就標成
>    `engine-default` 並說為什麼）。貼回檔超過就說超多少、該怎麼分段貼，**不自己改上限**。
>
> **Codex 在 PR #55 又挑掉兩個「看起來對、其實沒在驗」**（兩個都實測重現過）：
> 結論與計數原本拿**整份文件**做 substring —— 但同一個結論在迴圈摘要那段也寫著，
> 主標 `<p class="v">` 寫錯照樣綠燈；改成只比對那一格（比對要拿同一種量比）。
> capsule 的「省略」那一行沒算進預算 —— 600 字上限實測寫出 643 字；改成從多到少試到
> **整份（含尾巴）放得下**為止，`chars` 也改回報檔案實際長度，不是選段時算的帳。
>
> **P20 UI 第一次真跑就抓到一個真的壞連結**：報告裡「迴圈明細」的 `href` 寫裸檔名，
> 但那個檔在 `out/autotest/` 底下 —— 點下去是 404，一直沒人發現。href 改成相對報告的路徑；
> 閘也改成驗 HTML 裡**真正寫的那個 href**，不是拿檔名去猜（猜的話壞連結照樣綠燈）。

---

> **量了才改：G19 子行程化、手機版面、以及被推翻的那個目標（2026-10-17）**：操作員
> 「持續實際測試修正優化／使用者測試／整合測試／啟動測試，結果驗證無誤顯示於使用者面前」。
>
> **先量，結果推翻了原本要做的事。** 放大語料到 1070 檔跑一次，各閘 194 秒：
>
> | 閘 | 秒 | 車道 |
> |---|---|---|
> | G06 入庫 | 47.6 | `worker_process` |
> | G08 冪等 | 44.8 | `worker_process` |
> | G07 首頁 | 40.9 | `sequential`（**已入法**） |
> | G15 版面還原 | 30.8 | 內部子行程 |
> | G17 標題 TRIM | 14.0 | `sequential`（**已入法**） |
> | **G19 聚焦** | **3.9** | `sequential` ← 只佔 2% |
>
> 原本的計畫是「G19 與 G07 一起子行程化」。查下來兩件事都不成立：
>
> 一、**G07 不能動**。`ACCEL_BY_DESIGN` 裡已經寫著「首頁引擎實例與快取共用，不拆執行緒
>     （判讀邏輯不可動）」—— G06／G08／G17 同列。那是既有裁定，不是沒人想到。
> 二、**那份語料量不出 G19**。平均每個個股檔只有 **0.9 頁**，而 G19 的成本是**按頁**走的。
>     放大「檔數」是錯的軸。改用**頁數型語料**（98 份 × 40 頁 = 3920 頁）才量得到真相。
>
> **頁數型語料上的實測：9.70 秒 → 3.48 秒（2.8 倍）。** 做法是套 `VRN_PageRegions.analyze_many`
> 已經證過的那條：每塊一支子行程、失敗的塊在本行程重做（結果少一份比慢一點嚴重得多）、
> 輸入順序原樣回來。本行程與子行程走**同一支 `one()`**，所以兩條路不可能給出不同答案。
>
> **快不算數，要證明判讀沒變**：107 筆逐檔判讀指紋完全相同、107 份聚焦副本逐檔 SHA-256
> 完全相同；`VRN_Focus` 自測 14/14。測試 `test_worker_lane_and_in_process_lane_give_the_same_answer`
> 把它釘住（連聚焦副本的位元組都比）。
>
> P09 的車道改成讀引擎實際走的那條 —— 之前那行寫死 `sequential`，引擎改走子行程之後
> 它還是會印「逐一」，報告與事實不符就是假報告。
>
> **使用者測試（第一次真的用瀏覽器開報告）抓到一個真缺陷**：390px 下量到 **736px 水平溢出**，
> 「狀態」整欄被推出畫面外 —— 看不到燈號的報告等於沒有報告。窄螢幕改成每列一張卡，
> 四個值各自一行。修後兩個視寬都是 0 溢出，控制台零錯誤。
>
> **留給操作員裁定**：`VRN_TitleTrim.analyze_many` 收了 `mapper` 參數卻從頭到尾沒用過
> （函式體是純循序迴圈，永遠回 `lane: "sequential"`）。沒有任何呼叫端傳它。G17 本來就
> 入法不拆，所以這個參數是**宣稱有、實際沒接**的死參數 —— 下一個人接上它會靜靜地沒有效果。
> 要拿掉還是改寫說明，是介面的事，等裁定。

---

> **【規則】輸出驗證無誤才算收尾完成（2026-10-17）**：操作員「輸出的結果應規定驗證無誤後
> 才算是真正的收尾自動完成」。這一條從此是規則，不是習慣。
>
> 判準只有一份 —— `def_wrapup()`。三件全過才算完成：
>
> 1. 閘沒有 `FAIL`
> 2. P20 UI 對得上（HTML 的結論、計數、閘列數、每個連結與 JSON 一致）
> 3. 鏈上游沒有硬失敗
>
> **跑完不等於跑對，產得出檔案也不等於那份檔案能拿去用。**
>
> console 的 `[收尾]` 那一行、`all` 在鏈上游停掉時的那一行、以及交接 capsule 的抬頭，
> 三個地方都讀同一支函式 —— 不會出現「螢幕上說完成、檔案裡說沒事」這種兩套說法。
>
> **補掉的洞**：在這條規則之前，`def_write_capsule` 完全不知道驗證結果。一次 `FAIL=3`、
> UI 對不上的跑，照樣產出一份抬頭寫著「貼這一份就好」的交接摘要 —— 拿到的人會直接當它
> 可以用。現在抬頭第一行就是結論：
>
> ```
> [收尾] 完成 · 輸出驗證無誤才算收尾完成
> [收尾] **未完成** · … —— 卡在：閘 FAIL 3；UI 驗證對不上：結論與 JSON 相符
> [注意] 以下是現況，不是可以交出去的結果。先把上面那幾項弄綠再談收尾。
> ```
>
> `all` 在 build／lock／check 任一關停掉時也印這一行 —— 規則少印一次，就等於多了一個
> 「沒說不算數」的出口。五種情形（全綠／閘紅／UI 對不上／鏈上游失敗／兩件都壞）各有測試。

---

> **封章補滿 50 支；三件「以為沒做」其實早就做好了（2026-10-18）**：操作員「ps／py 都要有
> 最新加速器及模組、功能成功的模組都要註冊、參數有無高度整合不要類似檔案重複一堆、
> 若 non-OCR 做得好就不需要更複雜的工具」。**先查，四件裡三件已經成立**，只有一件真的缺。
>
> | 要求 | 查證 |
> |---|---|
> | 最新加速器與模組 | 橋**全是 v0100、零漂移**（ACCEL 104 · NET 8 · PS20 50 · PS 6）；覆蓋 py 92/92、ps1 47/47 |
> | 功能成功的模組都要註冊 | **49/49 全登記**，沒遺漏、沒幽靈登記 |
> | non-OCR 夠用就別上重工具 | **早就在省** —— 見下 |
> | 封章 | **缺一支** ← 真的缺的只有這個 |
>
> **non-OCR 那條的決定性實驗**：拿一份真實形狀的報告（封面 ＋ 1 頁年度財報 ＋ 38 頁內文）：
>
> | | 頁數 | G15 版面還原 |
> |---|---|---|
> | 原檔（假如沒接聚焦） | 39 頁 | 0.86 秒 |
> | **聚焦副本（實際走的）** | **1 頁** | **0.15 秒** |
>
> `samples = Path(state["focus"]["folder"])` —— G19 之後整條鏈就改用聚焦副本，重工具只看
> 留下來的頁。**省了 5.7 倍，而且本來就在省。** 前一天記的「G15 佔 48%」是語料造成的假象：
> 那批 40 頁檔每頁都像年度財報頁，所以全被留下 —— 語料不具代表性，不是管線浪費。
>
> **真的缺的那一支：`VRN_PanoramaProbe.py` 登記了卻鎖不住。** 鎖是靠 `run_module_selftest()`
> 證的，而它沒有 `selftest()`，所以每一次 `check` 都掛著「未鎖 1 支」。補上 **14 條已知答案**
> （NFKC、副檔名切分、日期合法性、檔名契約的代號／券商／報告日、燈號映射 —— 每一條的
> 正確答案都是**檔名本身的事實**，不是跑出來再抄回去的）。
>
> 接線踩到一個坑值得記：只把它加進 `def_run_proofs()` **不夠**，鎖還是說「沒有已知答案
> 證明它」。檔案與證明組的對照表在 SSOT 冊的 `lock.proofs.covers` —— 兩邊都接上才算數。
>
> **結果：鎖住 50 支、未鎖 0，`check` 從 AMBER 變 `GREEN · FAIL=0 WARN=0 SKIP=0 PASS=12`。**
> 這個系統第一次全綠。
>
> **整合（用 VCGC 既有的 `consolidate`，不自己寫一支找重複的工具）**：掃 200 個候選 ——
> **可合 1 · 擋下 7 · 待證據 192**。擋得對：`parquet_ident` vs `parquet_quote`、
> `empty_financial_row` vs `empty_basic_row` 的 AST 形狀相似度 1.0，但**探針回傳不同**。
> 長得像不等於可以合，這正是九頭龍守衛該做的事。
>
> 唯一可合的是三行的 `_decimals`（TitleTrim 與 PageRegions 各一份，5 組探針回傳一致）。
> **沒有合** —— 為三行而在兩支「各自能獨立自證」的引擎之間架一條 import，是拿結構耦合換
> 零功能收益，牴觸操作員自己設的前提「不傷系統健康」。規劃器的政策也寫著「跨模組退役
> 視為需順序修正」。**留給操作員裁定。** 結論：樹已經很緊，沒有「一堆重複」。

---

> **收掉兩件待裁定：四重點選句、死參數（2026-10-18）**：操作員「依你建議，自覺快完成時
> 實測、修正、收尾」。五件待裁定裡，**兩件本來就該由我做完，兩件不是我能決定的，
> 一件我已經給過結論**：
>
> | 待裁定 | 處置 |
> |---|---|
> | `_decimals` 三行要不要合 | 已有結論：**不合**（拿耦合換零收益），不再等 |
> | `analyze_many` 的死參數 | **做掉** |
> | 四重點選句挑到券商抬頭 | **做掉** |
> | G07 契約基準線 | **不是我能做的** —— 母系統 STAGE→APPROVE |
> | `parse_num` 與母倉 ENG394 不一致 | **不是我能決定的** —— 母倉是那個判斷的主人 |
>
> **一、四重點的動能與催化劑整組錯位（實測 6/6）**
>
> ```
> 動能   兆豐證券投資顧問 … 分析師 王小明 analyst@example-research.com (02)…   ← 聯絡行
> 催化劑  主要動能來自 AI 伺服器需求、產品組合改善與新產能開出。                  ← 真正的動能句
> ```
>
> 程式直接拿 `body_zone` 的前兩句，而第一句是券商抬頭 —— 真正的動能句被擠到催化劑那一格，
> 整組往前錯一位。**不需要發明新判斷**：含分析師信箱的句子是聯絡行，用引擎自己的
> `parse_email()` 把它們排除在候選之外，排序照舊。修後 6/6 正確：
>
> ```
> 動能   主要動能來自 AI 伺服器需求、產品組合改善與新產能開出。
> 催化劑  催化因素：新客戶認證通過、下半年旺季；風險：匯率波動與原物料成本上升。
> ```
>
> 晨會報告只有一句內容時，催化劑誠實標「未揭露」—— 沒有硬掰。
>
> **已知代價，寫進程式也釘了測試**：聯絡行沒有句號而與下一句黏成一句時（`_link_sentences`
> 會黏），整句被丟掉，黏在後面那段內容也跟著不見。取捨是實測決定的：丟掉換來正確的
> 動能與催化劑；被丟掉的那段多半是 EPS 預估，第 2 點本來就獨立抽過，全文也還在
> `main_text_raw`。`test_a_contact_line_glued_to_the_next_sentence_takes_it_down_with_it`
> 把這個代價釘住 —— **不藏起來**，哪天改選句規則會被提醒要一起想。
>
> **仍然留給操作員的**：「第一句是動能、第二句是催化劑」這個**位置規則**本身沒有動。
> 哪一句才算動能是判斷層的事，我只清掉了候選名單裡不該在的東西。
>
> **二、`VRN_TitleTrim.analyze_many` 的死參數**
>
> `mapper` 與 `action` 只出現在簽名與說明裡，函式體從頭到尾沒用過，永遠回
> `lane: "sequential"`，也沒有任何呼叫端傳過。**宣稱有、實際沒接的參數比沒有更糟** ——
> 下一個人接上它會靜靜地沒有效果，而且不會有任何地方報錯。拿掉，說明改成實話，
> 並寫明這一關不拆是 `ACCEL_BY_DESIGN` 的裁定，不是少做了平行化。

---

> **Codex PR #57 P2：`EPS@5.2` 被讀成信箱（2026-10-18）**：四重點的聯絡行過濾器用
> `parse_email()` 判斷「這句是不是聯絡行」，而它的網域樣式是 `[A-Za-z0-9.\-]+` —— **純數字也收**。
>
> 實測重現：
>
> ```
> 我們預估 2025 年 EPS@5.2 元。 → [{'analyst_id': 'EPS', 'broker_domain': '5.2'}]   誤判
> 目標價 TP@168 元。            → [{'analyst_id': 'TP',  'broker_domain': '168'}]   誤判
> ```
>
> 後果不只是抽錯分析師：含這種財務簡寫的**正文句會被當成聯絡行丟掉**，動能與催化劑整組
> 位移、催化劑變「未揭露」。我前一個修正因此在這一類報告上製造了新的錯。
>
> **修在源頭，而且順手解掉一個小九頭龍**：`parse_email`（抽取）與 `validate_email`（驗證）
> 本來各寫一份樣式 —— 同一個判斷兩份實作，所以同一個缺陷也在兩邊。改成全檔一份 `RE_EMAIL`，
> 網域必須以**字母結尾的頂級域**收尾：
>
> ```
> EPS@5.2 / TP@168              → 不是信箱 ✓
> analyst@example-research.com  → 是信箱 ✓
> a@b.co（短網域）               → 仍然是信箱 ✓
> ```
>
> 這件事值得記住的不是那條 regex，是**順序**：我在 PR #55／#57 連續兩次，修的都是
> 「驗證器自己沒被驗證」。這一次是我新加的過濾器引進新錯 —— 加一道判斷,就等於加一處
> 可能說謊的地方。


## 語料不是決定性的 → TEMP 快取等於白做（2026-10-18）

操作員說「整個系統非常吃資源且跑得非常慢」。實測下去，最大的一塊不是演算法，是**一個
已經蓋好、卻從來沒命中過的快取**。

連跑兩輪，中間什麼都不改、同一個 `--out`：

```
batch 命中 0／重讀 2 · first_page 命中 0／重讀 58 · focus 命中 0／重讀 1 · regions 命中 2／重讀 105
省約 0.1 秒
```

命中率 2/168。原因在語料生成端，不在快取：

| 檔型 | 數量 | 每輪都變的原因 |
|---|---|---|
| `.pdf` | 98 | MuPDF 每次存檔都生一組隨機 `/ID` 寫進 trailer |
| `.docx` | 7 | python-docx 把當下時鐘寫進每一個 zip 成員 |
| `.txt`／`.jpg` | 2 | 用複製的 —— **只有這兩檔穩定，剛好等於命中數** |

兩種情況的**內容都是一樣的**（docx 兩輪的成員內容 SHA 相同，只有 `date_time` 在跳；
PDF 兩輪同樣 8868 位元組，只差 56 個位元組，全在 `/ID`）。但位元組一變，快取就把它
當新檔，於是每輪都付雜湊與記帳的錢、拿不到任何回報 —— **淨值是負的**。

修法是兩個參數，沒有新模組：`doc.save(..., no_new_id=True)`、docx 存完把 zip 時間戳
正規化成固定值。

```
語料位元組一致   2/107  →  107/107
快取命中       2/168  →  168/168（regions 107、first_page 58、batch 2、focus 1）
省下            0.1 秒 →  21.1 秒
整輪牆鐘        33.0 秒 →  17.7 秒（1.87×）
```

輸出值一個都沒變：`部位 VERIFIED 1313 · NOT_PRINTED 236 · SINGLE 64 · MISSING 2 · CONFLICT 0`
前後相同 —— 只有 `/ID` 與時間戳在動，判讀讀的是文字。

`tests/test_VRN_AutoTestLoop.py::test_the_same_input_writes_the_same_bytes` 把這個前提釘住；
把 `no_new_id` 拿掉它就紅。

## 語料自己又判了一次「哪個是公司」= 3 筆 CONFLICT（2026-10-18）

操作員的前提是「先讓系統輸出值經驗證 100% 正確」。實測只剩 3 筆 CONFLICT，而且都是同一個形狀：

```
凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf  title.company  標題＋首頁引擎=賴偉中  vs  檔名=慧洋
凱基投顧_2891 中信金_施志鴻_20260519.pdf   title.company  標題＋首頁引擎=施志鴻  vs  檔名=中信金
凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf  title.company  標題＋首頁引擎=李承泰  vs  檔名=貿聯
```

**讀法沒有錯 —— 錯的是語料。** 合成的那頁標題真的印著「賴偉中(2637 TT)」，首頁引擎忠實
讀回來，交叉比對照實說兩條讀法不一致。分析師的名字是怎麼跑到公司位置的？因為
`def_synthetic_truth` 自己用 `company_fragments ＋ cjk` **又判了一次**「檔名裡哪個是公司」，
而那一份判錯兩種情況：

* **`-KY`**：`protect()` 在切詞前就把 `慧洋-KY` 整段抽走，所以它進不了 `company_fragments`
  —— 走訪到的第一個中文詞變成分析師「賴偉中」。
* **`中信金`**：生成器呼叫 `broker_matches(tok)` 時**沒帶** `exclude_prefix_fragments`，
  「中信金」撞上券商別名「中信」（CTBC）被跳過，落到「施志鴻」。
  （引擎自己的 `_filename_fields` 有帶，所以引擎不會犯這個錯。）

修法是**減法**：刪掉生成器那段迴圈，改問 ENG396 —— 「檔名裡哪個是公司」本來就只有它說了算，
而且 `decompose()` 同一次呼叫連 `doc_class` 一起給，連多問一次都不必。ENG396 五個都答對，
包含兩個 `-KY` 與「中信金」。

```
CONFLICT  3 → 0        VERIFIED  1310 → 1313        優先1 待修  5 項 → 2 項
```

> **留著的兩筆是誠實的**：`3014TT-20231005.pdf`、`6933_AMAX-KY_個股介紹報告.pdf` 的
> `cover.broker` 是 MISSING。這兩個檔名裡沒有券商，合成頁就真的沒印券商行，系統說
> 「該有、我沒讀到」是對的。把生成器改成一律印券商就會變綠 —— 那是彎曲樣本來換綠燈，不做。

> **順手記下、但沒有動**：`-KY` 的公司名進不了 `company_fragments`，在引擎裡也是這樣
> （`凱基投顧_2637 慧洋-KY_賴偉中` → `['賴偉中']`）。那份清單在引擎裡只拿來當
> 「別把公司讀成券商」的排除名單，而 `慧洋`／`貿聯` 都不是券商別名，所以沒有造成錯的輸出。
> 既然沒有可證明的錯，就不去動一支已鎖的引擎。

## 加速器的執行緒預算要在第一步就套上（2026-10-18）

操作員：「**指令第一步為提高 CPU/DRAM 效能**」。查下來，本倉**沒有任何一行**在拉高
CPU/DRAM —— 沒有 `setpriority`／`sched_setaffinity`／`OMP_NUM_THREADS`／GC 調參。
P00 RESOURCES 只是**量**（CPU 4 核、記憶體 15.2/15.7 GB、TEMP 28.5 GB），再算出子行程預算。

能拉高的那個機制是**加速器自己的** `activate(apply_limits=True)`，回報 `thread_budget`。
本倉不另做一套 —— 補一個就是九頭龍（既有裁定：「加速器缺席是設計如此，補模組＝九頭龍」）。
但 `all` 鏈本來是**只掛載、不 activate**，要等到第四步 `run` 的 P04 才套，等於
build／lock／check 前三步整段沒有預算。

改成第一步就 `activate=True`，回報還是只有 P04 那一列：activate 一個行程只跑一次，
P04 讀的是同一份 `ACCEL_STATE`。**一個判斷、一個地方，只是提前套用。**

這台機器上加速器不在，所以這件事**量不到**，只能證明次序：
`test_the_thread_budget_is_applied_before_the_first_seal_step` 把 build／lock／check／run
四步換成 no-op，各自回報看到的 activate 次數，第一步就必須是 1；把 `activate=True` 拿掉它就紅。

順手補掉一個假綠燈：沒有 `thread_budget` 時原本會印「執行緒預算 None 已套用」。
改成「這支加速器沒有回報執行緒預算」，並加測試釘住。

## 六步同時跑：排程已經沒有東西可排（2026-10-18）

操作員要「六個暫時獨立不相連的流程可同步去跑」「最佳化動態化步驟安排」。前者**已經是
現況**，後者**沒有東西可最佳化**，據實記下來：

`def_run_steps_side_by_side` 用 `ThreadPoolExecutor(max_workers=len(steps))` —— 六條在
t=0 同時起跑，牆鐘 = 最慢那一步。實測完成順序與秒數：

```
[1/6] P07 樣本 0.0 · [2/6] P16 引擎鎖 2.1 · [3/6] P08／P13／P14 2.2
[4/6] P02 SSOT 三本冊 3.8 · [5/6] P03 註冊冊＋P11 AST 4.7 · [6/6] P01 環境 4.9
一條接一條 15.7 秒 → 同時跑 5.1 秒
```

工人數 ≥ 工作數時，排序不影響牆鐘 —— 要再快只能讓**最慢那一步**變快，而最慢的
4.9 秒對一輪 17.7 秒來說，就算歸零也只省 1 秒。這一輪真正的加速來自別處（上面的快取）。

## 驗收：每一份報告是否 100% 過關（2026-10-18）

操作員：「跳出 HTML U/I 我直接在上面操作，看另外 80 個報告是否可達 100% 過關」。
自動跳出的那份報告本來只有**閘**的層級（56 列），看不到「哪一份報告過了、哪一份沒過」。
補上 `P21 驗收`，就畫在同一份報告裡。

**「過關」不是這一段定義的。** 優先序是待修清單（`VRN_TitleTrim.fix_rows`）算的，
`def_acceptance` 只是把它讀回來按檔分組：

```
過關    逐項驗過，而且待修清單上沒有優先 0／1／2 的項
待修    有優先 0（已鎖部位退步）／1（讀法不一致·該有沒讀到·掉字）／2（要人判）
未逐項驗 非個股（晨會、產業展望、盤後）：沒有逐項部位可驗，不混進分母假裝過關
```

優先 3（SINGLE：只有一條讀法、鎖不住）**不算待修** —— 那是鎖不住，不是讀錯。
自己再判一次「過不過關」就是第二顆頭：同一個問題會長出兩個答案，而且遲早不一樣。

合成語料實測：

```
P21 驗收  WARN  逐項驗過的報告 57/59 份 100% 過關（另有 48 份非個股，沒有逐項部位可驗）
          待修：3014TT-20231005.pdf、6933_AMAX-KY_個股介紹報告.pdf（都是 cover.broker MISSING）
```

表格每份報告一列，附篩選框（沿用驗證矩陣那一頁同一種寫法，不另外發明）。
真瀏覽器實測：輸入「待修」→ 107 列收斂成 2 列，連原因一起顯示；清空回到 107 列。

> **UI 閘的列數檢查跟著改了**：驗收表進來以後，整份文件的 `<tr>` 不再只有閘列。
> `_TagBalance` 改成只數 `<table id="gates">` 裡面那些 ——「閘列數與 JSON 相符」比的本來
> 就是閘表格，數到別張表就不是在比同一種量。`test_the_acceptance_table_does_not_inflate_the_gate_row_count`
> 用 40 份報告的驗收表釘住；把範圍限制拿掉它就紅。

> **手機又差點破版**：`#q` 沒寫 `box-sizing:border-box`，390px 下實測溢出 2px。
> 這是 2026-10-17 那次 736px 溢出之後的同一類錯 —— 加一個元素就要重量一次，不能用看的。

## Codex PR #58 兩條 P2：一條照修，一條拒絕它的修法（2026-10-18）

### 一、docx 正規化失敗會留下壞檔 —— 真的，重現了

`def_docx_stable` 原本直接用 `"w"` 開同一個路徑。**那一行就已經把檔案截斷了**，
寫到一半失敗（磁碟滿）時 `except` 把例外吞掉，留下的是壞掉的 docx：

```
before: 5262 bytes · 成員 ['word/document.xml', '[Content_Types].xml']
after : 5143 bytes · 成員 ['word/document.xml']        ← Word 開不起來
```

而 `def_build_corpus` 接著照常算 SHA、報 PASS —— 語料裡混進一個壞檔還說它好。
我原本那行註解寫「最多就是少一次快取命中」是錯的：代價是整份檔案。

改成寫暫存檔、`os.replace` 原子換上去，失敗就 `unlink`，原檔一個位元組都沒動。

### 二、ENG396 叫不出名字 → 退成「測試公司」：缺口是真的，退路不能裝回去

Codex 要「保留檔名解析的退路」。**不採用** —— 那條退路就是這次拆掉的第二顆頭，
而且它正是在三個檔上把分析師寫成公司的那一份：

```
慧洋-KY → 賴偉中     中信金 → 施志鴻     貿聯-KY → 李承泰
```

裝回去當 fallback，這三筆 CONFLICT 就會回來（它們恰好是 ENG396 答得出、迴圈答錯的）。

查過能不能讓 ENG396 自己認得 `志強-KY` —— 它只在名字被**單獨切出來**時才答：

```
'20251204兆豐個股報告-志強-KY(6768)'    → []
'...(_6768_)'（decompose 現有的重試）    → []
'_6768_ 20251204兆豐個股報告-志強-KY()'  → []
'_6768_ 志強-KY'                        → ['志強']   ← 只有這個會
```

要湊出最後那一行，就得先決定「檔名裡哪一段是公司」—— 那就是 ENG396 的判斷本身。
**沒有不長第二顆頭的修法。**

所以改成讓缺口被看見，而不是沉默地變成 `測試公司`：

```
WARN  G05 CORPUS  ENG396 叫不出公司名的個股檔 1 個（退成「測試公司」）
                  20251204兆豐個股報告-志強-KY(6768).pdf
                  —— 這幾檔的公司名抽取沒有驗到；不自己補一套檔名判讀（那是第二顆頭）
```

少一檔覆蓋換三檔判對是划算的，但不能偷偷換。Codex 說的 false-green 風險成立，
解法是**報出來**，不是把錯的那一份判斷請回來。

> 這兩條放在一起看才完整：同樣是 P2，一條是我寫壞的（照修），一條是我有意的取捨
> （說明理由、把代價列出來）。差別在有沒有可證明的錯 —— 第一條我重現給它看，
> 第二條我把三個反例與四次 ENG396 探測列出來。

## 加速器覆蓋率：兩邊都是 100%，但要用對判準（2026-10-18）

操作員要「所有 PY PS 檔都有加速器、覆蓋率 100%」。**我第一次量錯了**，記在這裡免得下次再錯：

| 我一開始的做法 | 結果 | 錯在哪 |
|---|---|---|
| 全倉 grep `[VIA:ACCEL-BRIDGE` | py 90.7%、ps1 2.1% | ps1 根本不用這個標記；py 把寫明的豁免也算成缺 |
| 用 `VIA_BridgeInjector` 自己的規則 | **py 92/92、ps1 47/47 = 100%** | ✓ |

**ps1 的判準是 `VIA-ENTER-ENV` 頭塊**，不是 `[VIA:PS-ACCEL:v0100]` —— 後者註解寫得很清楚：
「mother-tree dot-source block（批255 全樹導入）; never duplicated」，是母樹的 legacy 標記，
注入器刻意不重複注入。拿它當判準，47 支會有 46 支被誤判成缺橋。

py 的 15 支豁免，每一條都是注入器裡寫明的規則，不是漏掉：

| 支數 | 豁免原因 | 規則 |
|---|---|---|
| 5 | `.grok/` 平台技能腳本 | `SKIP_DIR_NAMES` |
| 4 | 已封存交付（位元組清單） | `SEALED_MANIFEST_NAMES` |
| 3 | `references/intake/` 收進來的參考 | `SKIP_REL_PATTERNS` |
| 2 | **加速器本體自己** | `ENGINE_ORIGINAL_RE` |
| 1 | `via_unified_engine.py`：自測封印「只用標準庫」 | `STDLIB_ONLY_BUNDLES` |

> 最後那一條值得單獨記：那支的自測封的是「我只 import 標準庫」。加一個 try-guard 的橋
> 也會破壞那個封印 —— **覆蓋率不是愈高愈好，是每一支都要符合它自己的契約。**

## 動詞分類：11 類，規則在程式裡不在我嘴裡（2026-10-18）

VRN 樹裡 **1307** 個帶 `[VRN-ID]` 的函式／類別。動詞由 `VRN_AstId_v0100.py` 的 `ITEM_RULES`
依**函式名前綴**判定，依序比對、先中先得，類別落 `CLASS`、其餘落 `LOGIC`：

```
LOGIC 712 (54.5%) · TEST 238 (18.2%) · IO 93 (7.1%) · CLASS 64 (4.9%)
EXTRACT 45 · ENTRY 39 · GATE 38 · INIT 23 · VALIDATE 22 · BUILD 20 · REPORT 7
```

`EXTRACT`（抽值）與 `VALIDATE`（驗值）分成兩類不是修辭 —— 那正是 PR #57 的缺陷形狀：
`parse_email` 與 `validate_email` 各寫一份樣式，同一個缺陷也就在兩邊。現在共用一條 `RE_EMAIL`。

第二種動詞是**動作怎麼跑**（P09 ACCEL，這一輪 24 個）：
`thread_pool` 19 · `worker_process` 2（G06 入庫、G08 冪等）· `cache` 2 · `sequential` 1（G17）。

## 資源預算改成可調，而且要說出誰是瓶頸（2026-10-18）

操作員問「記憶體不夠時怎麼用 TEMP 補」。查下來，**這台機器的瓶頸根本不是記憶體**：

```
可用記憶體 15.0/15.7 GB  →  記憶體允許 25 支子行程
CPU 4 核（留 1）          →  CPU 只允許  3 支   ← 卡在這
```

舊的 `why` 只印公式（「CPU n 核留 1 · 每支約 0.6 GB · 最多 8 支」），看不出**現在是哪一項在擋**，
於是調哪個旋鈕都是猜的。改成：

1. 回傳多帶 `by_cpu`／`by_mem`／`ceiling`／`per_worker_gb`／`bottleneck`，`why` 直接寫「卡在 CPU」。
2. 五個旋鈕可用環境變數調，讀不懂就退回預設、超出範圍就夾住（打錯一個值不該讓整輪跑不動）：

```
VIA_VRN_WORKERS      硬指定子行程數
VIA_VRN_WORKER_GB    每支子行程假設吃多少記憶體（預設 0.6）
VIA_VRN_WORKERS_MAX  上限（預設 8）
VIA_CACHE_SHARE      TEMP 快取佔剩餘空間的比例（預設 0.25）
VIA_CACHE_MAX_GB     TEMP 快取絕對上限 GB（預設 10）
```

**預設一個字都沒變**：不設任何環境變數時仍是 3 支子行程、7.1 GB 上限，
`test_no_environment_variable_means_the_old_numbers` 釘住這一點。

> 為什麼不直接把數字調大：因為我沒有操作員那台機器的 `[RESOURCES]` 那一行。
> 憑空調只是換一個猜的數字。讓他自己調、並且看得到瓶頸，比我猜一個值誠實。

## 三到六條獨立動線：六條已經在跑，再切會切壞證明（2026-10-18）

六條同時跑的那一段，是**彼此沒有相依**的六項（環境／SSOT 三本冊／註冊冊＋AST／引擎鎖／
樣本 SHA／本機冊與資料庫）。再往下切不行，理由是資料相依：

```
G15 版面還原  →  G17 標題 TRIM     G17 吃 G15 還原好的表格
G19 聚焦      →  G06 入庫          G06 讀的是聚焦後的副本
G06 入庫      →  G08 冪等          G08 的意義就是「再跑一次結果要一樣」
```

而最貴的兩步正是 G06（4.3 秒）與 G08（5.2 秒）。把它們並起來省 4 秒，
代價是**冪等這個證明消失** —— 不做。

## 我給的旋鈕會把引擎鎖弄紅（Codex PR #61 P1，2026-10-18）

上一節那五個環境變數，有一個我沒想到的後果：

```
$ VIA_VRN_WORKERS=9 python engine/VRN_RunCache_v0100.py selftest   → exit 1
```

`selftest` 驗的是 `1 <= res["workers"] <= 8`。**8 變成可調之後，那就不是不變式，
是把一個設定值當常數驗。** 後果是 runcache 那組證明過不了 → 引擎鎖封不起來 → check 紅。
**旋鈕把鎖弄紅，比旋鈕沒用更糟。**

而且範圍比 Codex 舉的例子更廣：`workers = min(by_cpu, by_mem, ceiling)`，
所以在 32 核的機器上，光 `VIA_VRN_WORKERS_MAX=16` 就會得到 16 > 8，同樣踩中。
這台只有 4 核（`by_cpu=3` 先擋住）所以看不出來 —— **操作員那台核心數多的話會中**。

修法不是把不變式放寬成「接受設定範圍」，是寫成**真正的那一條**：

```python
# 至少 1 支；沒有硬指定時不超過三條限制裡最小的那條；硬指定時照辦
res["workers"] >= 1 and res["workers"] <= max(1, min(res["by_cpu"], res["by_mem"], res["ceiling"]))
```

這比舊的更強 —— 舊的只驗一個魔術區間，新的驗整個夾取決策。紅隊過：把
`min(by_cpu, by_mem, ceiling)` 改成 `by_cpu * 99`，這一條就紅（workers 297）。

> **這一條我自己第一版寫錯了，值得記住**：新加的旋鈕已知答案，原本驗
> `junk["workers"] == base["workers"]`。紅隊時發現它是空的 —— 壞值退回 `low`(0.05 GB) 時
> `by_mem` 變 302，但 `workers = min(3, 302, 8)` 仍是 3，跟預設一樣。
> 改成驗**真正被用到的那個值** `per_worker_gb == 0.6` 才紅得起來。
>
> 這是這個專案第三次撞到同一種形狀：**驗一個會塌掉的衍生值，等於沒驗。**
> 前兩次是 PR #55 的「拿整份文件比結論」與 PR #57 的「驗證器自己沒被驗證」。

驗證：`VIA_VRN_WORKERS=9` 下 lock 鎖住 50 支、check GREEN；selftest 在 不設／9／33／1
四種值下都 exit 0；240 項測試全過。

## 兩個閘都開：接 OCR、補 29 檔覆蓋（2026-10-19）

### 補 29 檔覆蓋：佔位名要每檔不一樣

ENG396 叫不出名字時退回「測試公司」—— 29 檔**共用同一個字串**。那表示首頁引擎
就算回傳一個常數也驗得過，等於那 29 檔的公司名抽取根本沒驗到。

改成綴上代號（引擎自己抽出來的，**不是我再解析一次檔名**）：

```
Citi-3231 20250604.pdf   → 測試公司3231
CLST-6669 20251001.pdf   → 測試公司6669
Daiwa-1319 20231011.pdf  → 測試公司1319
凱基投顧_2637 慧洋-KY_…    → 慧洋        （ENG396 認得的不受影響）
```

這不宣稱它是公司名，只是一個**可分辨的**合成佔位名：每檔都得把自己那個名字原樣讀回來。
檔名裡沒有公司，所以那一票仍是 SINGLE，不會製造 CONFLICT。

### 接 OCR：能力接上了，但 OCR 的字不進判讀

這個容器裡沒有 tesseract、`apt` 又不能用，所以裝了純 pip 的 `rapidocr_onnxruntime`
（ONNX 版，不需要系統二進位檔）。**實測它讀中文會掉字**：

```
畫進去：台積電(2330 TT) 營運動能延續    投資評等：買進  目標價：NT$1250.0
讀回來：台電（2330  TT)  營運動能延續   投資等：買進    目標價：NT$1250.0
        ↑ 掉「積」                      ↑ 掉「評」
```

數字與拉丁字全中（2330、1250.0、2181-8888、TT），**中文會掉字**。

所以 `VRN_Ocr_v0100` 的結果一律帶 `source="OCR"` 與 `lossy_cjk=True`，
而且 **P22 OCR 那一列明說「OCR 的字不進判讀」**。理由：這個系統的 VERIFIED 定義是
「兩條讀法一致」。把一條會掉字的讀法算進去，製造的是假綠燈，不是覆蓋率。

模組只做一件事 —— 把影像變成文字，不判讀。`OCR_REQUIRED` 的判斷留在
PageRegions 與 TitleTrim 原處（那兩支判的是「文字層有沒有字」，JPEG 本來就沒有），
**沒有在它們之外再長一套讀法**。

三層引擎依序試，第一個能用的就用，並把用了哪一支寫進結果：

```
pymupdf-tesseract   PyMuPDF 內建，要系統裝 Tesseract（Windows 常見）
rapidocr            純 pip，不需要系統二進位檔（容器裡裝得起來）
pytesseract         Tesseract 的 Python 包裝
```

> **語料那張假 jpg 也換掉了**：本來是 `\xff\xd8\xff\xe0` 加 64 個零 —— 那種檔連 OCR 都沒得讀，
> 證不了任何事。改成畫一張有已知文字的真圖（位元組固定，不打壞 TEMP 快取）。

> **沒有引擎時的退路也寫成已知答案**：CI 上沒有任何 OCR 引擎，`available()` 回空字串、
> `read()` 回 error 不丟例外、結果照樣標 `source=OCR`。自測在有／沒有引擎兩種情況下都跑得完，
> 並且印出是哪一種 —— 不會因為 CI 沒引擎就假裝證過了讀取。

`註冊 150 檔 · 鎖住 51 支引擎與冊 · 未鎖 0`（新模組已登記並封進引擎鎖，兩個地方都接：
`def_run_proofs()` 與 SSOT 的 `lock.proofs.covers`）。

---

## 2026-10-19（二）Codex PR #62 的三條 P1：「接上了」跟「真的在用」是兩件事

上一輪把 OCR 接進來，報告上寫「OCR 已接（見 P22）」。Codex 審完指出三件事，**三件都對**，
而且第一件正是這個倉一再犯的同一種錯：**改了一句話，沒改行為**。

### P1-1　說「已接」，但沒有任何地方真的呼叫它

全倉搜過：`VRN_Ocr_v0100.read()` 只有自己的 selftest 在叫。影像檔照舊
`SKIP_OCR_REQUIRED` 跳過，OCR 一個字都沒讀。上一版做的事只是把
`"OCR_REQUIRED (image input, OCR not wired)"` 換成「OCR 已接」——
**那不是修好，那是換一句話繼續說謊**，跟它想修掉的那句是同一個毛病。

現在 G06 那一列真的送進 OCR，把讀到什麼寫進報告：

```
OCR_REQUIRED：影像沒有文字層。OCR（pymupdf-tesseract／chi_tra+eng）讀到 N 字、M 行，
第一行「…」。這些字**不進判讀**（source=OCR／lossy_cjk=true）
```

判讀照舊不吃它。`def_ocr_note()` 只回字串、不回值 —— 回值就有第二條讀法混進 VERIFIED 的風險。

### P1-2　環境缺件讓整輪倒掉

`selftest` 裡 `import pymupdf` 沒包起來，`def_gate_ocr` 的 try 又只包了
`def_load_module`。裝了 rapidocr 卻沒裝 PyMuPDF 的機器，P22 會丟
`ModuleNotFoundError` 把整條指令帶走。

修法不只是包 try。**三態**：

```
PASS   驗過了
FAIL   驗了，不對
GAP    這台機器驗不到（畫不出已知圖、沒有中文語言包）
```

為什麼要第三態：算成 FAIL，`lock` 就會因為環境條件而紅 —— 那是 Codex #61 那個坑，
已經修過一次了；算成 PASS，就是把沒驗到的講成驗過了。所以它自己一個狀態，
`selftest` 不因它回 1，P22 把它畫成 WARN，報告上看得見。

### P1-3　中文語言包沒選 —— 而且底下還藏著更大的一個

Codex 說 `get_textpage_ocr()` 預設 `language='eng'`，中文會讀錯。對。
但照著查下去，發現**更根本的一條**：對影像檔不給 `full=True`，它直接丟

```
RuntimeError: source or target not a PDF
```

而這個例外被 `read()` 的 try 吞掉，外面看起來只是「讀到空的」。所以上一版在任何
裝了 Tesseract 的機器上，OCR 是**一個字都讀不到**，自測還會紅
（實測 EXIT=1，四個數字/拉丁 token 全缺）。沙箱裡剛好沒裝 Tesseract、走到 rapidocr，
所以我上一輪沒踩到 —— 這就是為什麼 CI 綠不等於對。

### 順帶更正我自己寫過的一句話

上一輪寫「OCR 中文會掉字」。那是 **rapidocr 的行為，不是通則**。
同一張已知圖，兩支引擎實測（`tesseract 5.3.4` + `chi_tra`）：

| 引擎 | 數字與拉丁字 | 中文 |
| --- | --- | --- |
| `pymupdf-tesseract`（`chi_tra+eng`） | 4/4 全中 | 6/7；`目標價` 只是被斷成 `目標\n價`，**沒掉字**，但夾雜 `\|]`、`。` 之類雜訊 |
| `rapidocr` | 4/4 全中 | 5/7；`台積電`→`台電`、`投資評等`→`投資等`，**真的掉字** |

所以已知答案改成**只量不判**：硬性要求只有「數字與拉丁字全中」與「中文不能整段讀錯
（≥4/7）」，實際失真每輪量出來印在旁邊。把某一種失真寫成「必須發生」，
等於要求引擎永遠不要變好 —— 那是另一種假綠燈。

共通的只有一件事沒變：**OCR 的字不等於文字層的字，不進判讀**。

### 回歸測試

`tests/test_VRN_Ocr.py` 11 案。驗過它們會紅：對修好之前的程式跑，9 案報錯；
把 `read()` 單獨退回舊的呼叫形狀（拿掉 `full=True` 與 `language`），
`test_a_known_image_really_comes_back_as_text` 紅在
`RuntimeError: source or target not a PDF` —— 抓的就是那個 bug 本身，不是函式在不在。

### 同一輪的兩條 P2：我才剛做的 GAP，最大的洞沒補到

**P2-1　沒有引擎時，「沒跑到」被算成「過了」。**

三態是為了讓「這台機器驗不到」看得見。結果沒有引擎的那條分支只記了
error-contract 一條 PASS，**真的讀一張已知圖那一條根本沒跑，卻沒記成 GAP**。
統計那行於是寫「過 5／紅 0／**沒驗到 0**」，而 `lock` 收到 `rc=0` 就把 `ocr`
當成證過了。CI 上沒有任何 OCR 引擎 —— 也就是說它每一輪都在這麼報。

這正是這個倉一再踩的「驗一個沒跑到的東西，等於沒驗」，而且是**我才剛蓋好防護欄
就從旁邊走過去**。補上 GAP 之後：`過 5／紅 0／沒驗到 1`。

**P2-2　挑引擎沒看中文讀不讀得了。**

`available()` 判 `ok` 時沒把中文語言包算進去，只寫進 `why`。所以一台裝了
Tesseract（沒中文包）又裝了 rapidocr 的機器，會挑 Tesseract —— 然後把中文讀成

```
6MB( 2330 / Simanaeia / HAS / : Bit / BR: NT$1250.0
```

那不是降級，是垃圾。而且旁邊就站著一支自帶中文的 rapidocr 沒人理。

改成**讀得了中文的優先**，不照 `ENGINE_ORDER` 硬排；三支都讀不了中文時照實在
`why` 裡說「只好用它」。實測 `tess-no-cjk` 情境從 `pymupdf-tesseract`（中文 0/7）
變成 `rapidocr`（7/7 全過）。有中文包時仍然是 `pymupdf-tesseract`，不讓位。

兩條的回歸測試都驗過會紅：對修好之前的程式跑，分別紅在
`AssertionError: 'pymupdf-tesseract' != 'rapidocr'` 與
`[] is not true：沒有引擎時要記下「讀取那一條沒跑」`。

### 2026-10-19　TEMP run 資料夾撞名：Windows 的時鐘一格有 15.6 毫秒那麼長

PR #64 的 Windows CI 紅在一個跟那個 PR 無關的地方：

```
FileExistsError: [WinError 183] Cannot create a file when that file already exists:
  ...\vrn_t\run_20261019_072539_803660_6732
```

`VRN_TempStore.open_run()` 用 `run_<%Y%m%d_%H%M%S_%f>_<pid>` 當資料夾名，
然後 `mkdir(parents=True, exist_ok=False)`。同一個 process 連開兩次 run
（`test_a_failed_delete_is_recorded_as_failed` 就是這樣：開一個、關掉、再開一個），
在 **Windows 上系統時鐘一格約 15.6 毫秒**，兩次 `datetime.now()` 很可能拿到
同一個微秒值 —— pid 又一樣，名字就完全相同，整輪被 `FileExistsError` 帶走。

**這不是 flake，是真的 bug。** 任何在一格時鐘內開兩個 run 的程式都會炸，
只是 Linux 的時鐘細得多，所以沙箱裡撞不到。把時鐘凍住就必然重現。

修法：撞到就在名字後面補序號。

```
run_20261019_072539_803660_7580        先建的
run_20261019_072539_803660_7580_2      同一格時鐘的第二個
```

序號擺在**最後**是有理由的：`sweep` 用 `sorted(key=lambda p: p.name)` 決定
「舊的在前」。時間戳在最前面，所以跨時間的排序不受影響；同一格時間內
`..._7580` 也還是排在 `..._7580_2` 前面，正好是建立順序。
`exist_ok=True` 不能用 —— 那會讓兩個 run 共用一個資料夾，連鎖都鎖不住。

回歸測試 `test_two_runs_in_the_same_clock_tick_do_not_collide`（時鐘凍住，
讓那一格必然發生）驗過會紅：對修好之前的程式跑，紅在跟 CI 一模一樣的
`FileExistsError`。

---

## 2026-10-19（三）七條財報恆等式從來沒跑過 —— 而且其中一條還在寫錯值

操作員「邊測邊修到 100% 正確」。第一輪實測就撞到一個大的：
內層 7 個 SKIP **全部**是財報恆等式。

```
恆等式 GP_SUB  毛利 = 營收 − 營業成本       SKIP · INSUFFICIENT 174
恆等式 GM_DIV  毛利率 = 毛利 ÷ 營收 × 100    SKIP · INSUFFICIENT 174
恆等式 OP_SUB  營業利益 = 毛利 − 營業費用     SKIP · INSUFFICIENT 174
恆等式 OPM_DIV 營業利益率 = 營業利益 ÷ 營收   SKIP · INSUFFICIENT 174
恆等式 NM_DIV  淨利率 = 稅後淨利 ÷ 營收       SKIP · INSUFFICIENT 174
恆等式 BS_ADD  資產 = 負債 + 權益            SKIP · INSUFFICIENT 174
恆等式 EPS_DIV EPS = 稅後淨利 ÷ 流通股數      SKIP · INSUFFICIENT 174
```

這七條正是**會抓出財務數字抽錯**的檢查。174 個期間，一次都沒執行過。
這個倉自己的規矩是「skip ≠ proof」。

### 三個疊在一起的原因

**一、四條結構上永遠不可能被評估。** 冊上的恆等式點名
`cogs`／`opex`／`net_margin`／`shares`，但 `IDENTITY_OPERANDS` 裡**沒有對映**。
`identity_state` 只要一個運算元是 None 就回 INSUFFICIENT —— 報告上看起來像
「這次資料剛好不全」，其實是接線斷了，換任何語料都一樣。

`selftest` 本來就有 `identity_state` 的已知答案，但它自己餵
`{"revenue": 100.0, "cogs": 60.0, …}`，所以**驗到了算式、驗不到接線**。
同一個坑的第四次。

**二、「淨利率(%)」被認成 NetIncome —— 這是寫錯值，不是漏讀。**
`METRIC_ALIASES` 沒有 NetMargin，而 `normalize_metric_name` 取最長命中的別名：
「稅後淨利率」裡有「稅後淨利」(4 字)，沒有更長的候選，於是**百分比被寫進金額欄位**。
真報告上這會默默污染 NetIncome。實測：

```
淨利率(%)      -> NetIncome      ← 錯
稅後淨利率(%)   -> NetIncome      ← 錯
營業成本／營業費用／流通股數          -> （認不出來，整列丟掉）
```

**三、合成語料只印四列**（營收、毛利率、稅後淨利、EPS），所以就算接線修好，
桶裡也湊不齊運算元。

### 修法

詞彙與對映都是**資料不是邏輯** —— 判斷仍然只有 `identity_state` 一處，不造第二顆頭：

- `METRIC_ALIASES` 補 `COGS`／`OperatingExpense`／`NetMargin`／`SharesOutstanding`。
  「淨利率」(3 字) 與「稅後淨利率」(5 字) 都掛在 NetMargin 下，長度蓋過「淨利」「稅後淨利」。
- `IDENTITY_OPERANDS` 補那四個運算元。
- `def_table_rows` 改成印一期完整、而且**自己對得起來**的 15 列
  （用整數反推：營業成本 = 營收 − 毛利，所以 GP_SUB 精確成立，不是乘完再四捨五入）。
- `BookCheck.selftest` 加一道守門：**冊上每個恆等式運算元都要接得到 MetricName**。
  驗過它會紅 —— 把對映退回舊版，它指名道姓說 `['cogs', 'net_margin', 'opex', 'shares']`。

### 補完之後掉出第二個缺口：總負債與股東權益對不到科目

財務表補齊後，驗收從 57/59 掉到 **8/59**，306 個 UNMAPPED、優先 2。
不是對映器的錯 —— 它照 `def05 unmappable_rule：REVIEW_REQUIRED，不猜` 拒絕猜，
然後把缺口指出來。真正的缺口在操作員冊的**不對稱**：

```
assets        資產總額 · 資產總計 · 總資產     ← 券商用語補了
liabilities   負債總額 · 負債總計              ← 沒補「總負債」
equity_total  權益總額 · 股東權益總額           ← 沒補「股東權益」
```

券商報告寫「總負債／股東權益」，MOPS 寫「負債總額／權益總額」。補上對稱的兩個詞，
並驗過「總負債比率」沒有被「總負債」搶走（仍是 `debt_ratio`）。

### 結果

| | 基準 | 修完 |
| --- | --- | --- |
| 內層 SKIP | **7** | **0** |
| 內層 PASS | 375 | **382** |
| VERIFIED 部位 | 1313 | **2843** |
| 主報告 | FAIL 0 · WARN 25 | FAIL 0 · WARN 25 |
| 驗收 | 57/59 | 57/59 |

七條恆等式現在真的在 174 個桶上跑 —— **1,218 次從來沒做過的驗算**。
VERIFIED 多出 1530 個部位，而 SINGLE（64）、MISSING（2）、NOT_PRINTED（236）一個沒變，
也就是說多出來的全是**真的被兩條讀法驗過**的，不是把沒驗的算成驗過。

### 回歸測試

`tests/test_VRN_BookCheck.py` 十案，每一條都擋住一個具體的再犯：

- 冊上每個運算元都接得到 MetricName
- 每個運算元都有引擎認得的中文標籤（接得到還不夠，標籤認不出整列還是會被丟掉）
- 「淨利率(%)」不可以被歸成金額
- 語料湊得齊運算元，七條都跑得動
- **七條都要證明抓得出錯的那一邊** —— 只會過的檢查等於沒有檢查
- 少一個運算元要回 INSUFFICIENT，不可以悄悄算過
- 語料印的每一個列標，版面引擎都要對得到科目
- 補「總負債」不可以把「總負債比率」搶走

### 同一輪的 USER-TEST：內層報告在手機上溢出 792 像素

真的開瀏覽器（Chromium 390×844）跑過兩份報告：

```
VRN_Main_Report_v0100.html    水平溢出 0 px      · console 0 錯
VRN_AutoTest_Report.html      水平溢出 792 px    · console 0 錯
```

390px 的螢幕上內層那份寬到 1182px，操作員得左右拖才看得完。兩個來源：

1. `.cards{grid-template-columns:repeat(6,minmax(110px,1fr))}` ——
   六欄固定最小寬，光這一列就要 6×110 + 5×10 = 710px。改成 `auto-fit` 自動折行。
2. 細節欄塞的是絕對路徑，沒有斷行機會。`td` 加 `overflow-wrap:anywhere`。

改完 390px 下 `scrollWidth == clientWidth == 390`，零溢出。

順帶：加了 `overflow-wrap:anywhere` 之後徽章被從中間切開（`PARTIA/L`、`NOT_W/IRED`），
所以 `.pill` 要 `white-space:nowrap`。這種只有看截圖才發現得了 —— JSON verdict 說「沒溢出」
的時候它確實沒溢出，但字是斷的。

主報告不用動：它早就有 `@media (max-width:640px)` 把表格攤成卡片，而且 `td` 有
`word-break:break-word`。這次是照搬它的作法，不另外發明一套。

### ACTIVATE：從任何資料夾都啟動得了

操作員之前在 `C:\Users\tonyk` 打 `.\artifacts\VRN-1.ps1` 得到
「無法將 … 字詞辨識為 Cmdlet」。那不是程式的問題，是相對路徑在別的資料夾找不到檔。

實測：用絕對路徑從 `/tmp` 啟動 `artifacts/ActivateVRN-1.py all --out …`，
整條鏈跑到 `[收尾] 完成`。啟動器是薄包裝，直接把子指令轉給 `VRN_Main_v0100.py`
的同一個 MAIN —— 沒有第二套參數解析，所以不會出現「從啟動器跑跟直接跑結果不一樣」。

### Codex #65 的兩條：單位被表頭搶走、分類漏一個

**P1　列標自己的單位被表頭蓋過去。**

`infer_unit_and_scale()` 把列標與表頭黏成一條字串再比子字串：

```python
context = normalize_unicode_text(f"{metric_raw} {table_context}")
```

於是表頭的「百萬」對**每一列**都會贏：

```
項目 (NT$ 百萬元) · 流通股數(百萬股)  ->  ('NT$m', 'TWD', 1000000.0)   股數被當成錢
項目 (NT$ 百萬元) · 每股盈餘(元)      ->  ('NT$m', 'TWD', 1000000.0)   每股「元」被乘一百萬
```

Codex 只點了第一條（我新加的列），但查下去**第二條在那之前就已經錯了** ——
`每股盈餘` 本來就在語料裡，它的單位後設資料一直是錯的。

括號裡的單位是**那一列自己**講的，表頭只是沒人講話時的退路。改成
`def_unit_of(text)` 說不出單位就回 `None`，列標先問、表頭後問、都問不到才 `raw`。

順序是有意義的，寫在函式的 docstring 裡：

```
「百萬股」裡有「百萬」      -> 股數要排在幣別前面
「元」在「台幣百萬元」「千元」裡都有 -> 要排在它們後面
```

實測 14 個列標全對，表頭退路沒修掉（`營收` + `單位：新台幣十億元` → `NT$bn`；
`某科目` + 空表頭 → `raw`）。

**P2　`SharesOutstanding` 沒有分類，整列落成 `Other`。**

我把 `COGS`／`OperatingExpense`／`NetMargin` 三個都加進 `METRIC_CATEGORY_MAP` 了，
就是漏掉這一個。出處查過操作員冊的 `field_crosswalk`：

```json
"shares": {"from": "financial_classification_rules.BALANCE_FEATURES.SharesOutstanding"}
```

所以是 `Balance Sheet`。補上，並加一條守門擋整類：
**`METRIC_ALIASES` 裡每個指標都要有分類** —— 下次再漏，測試先講話。

回歸測試八條，對修好之前的碼六條紅，紅在
`'NT$m' != 'm shares'`、`('NT$m','TWD',1000000.0) != ('NT$','TWD',1.0)`、
`['SharesOutstanding'] != []`。

---

## 2026-10-19（四）第二輪 DEBUG：G15 的「文字模式會漏句」其實有規則

恆等式是藏在 **SKIP** 裡的。第二輪就去翻剩下的 WARN，看有沒有同一類。
七個內層 WARN 逐一看過，六個是已經寫下來的事實（29 檔叫不出名、那張圖、本機資料庫、
兩筆原檔沒印的券商、鎖與待修清單）。剩下那個 **G15 截取完整度** 值得重量一次 ——
因為它的百分比隨著語料表變大從 81.11% 動到 87.39%，會動的數字就不該照抄舊結論。

### 漏的是同一段，不是隨機漏句

八個檔漏掉的是**完全相同的 75 個字**，而且以 `元。` 開頭 —— 切在一個詞中間：

```
before:  "1元,2026年6.19"
missing: "元。主要動能來自AI伺服器需求、…風險:匯率波動與原物料成本上升。"
after:   "項目(NT$百萬元)20"
```

也就是**本文結尾與表頭之間**那一段。量出來的規則：

| 情境 | 漏字 | 表 | 列 |
| --- | --- | --- | --- |
| 本文 + 表（原樣） | 75 | 1 | **0** |
| 本文 + 多一句 + 表 | 99 | 1 | 0 |
| 本文 + 多兩句 + 表 | 123 | 1 | 0 |
| 本文 + 只有表頭一列 | **0** | 0 | 0 |
| 只有本文、沒有表 | **0** | 0 | 0 |
| **同一份真值改成 PDF** | **0** | 2 | **42** |

所以不是「文字模式會漏句」，是**本文後面緊接扁平表時，表前的本文尾段整段不進句子**，
漏多少就等於那一段多長。而且文字模式**抽不到任何表格列**（PDF 同一份抽得到 42 列）。

試過在本文與表之間加空行、加表標題、兩者都加 —— 都沒用，所以不是語料格式的問題，
是 ENG394 的 `text_restore` 本身。

### 為什麼不修

ENG394 在 `engine/mother/`，母倉逐位元組鏡像。VRN 這邊確實有合法的延伸點
（`VRN_PageRegions.tail_v0101()` 在記憶體裡冪等地擴充已載入的 ENG394，不動母倉位元組），
技術上補得進去。**但不該補。**

資料庫引擎（ENG002）**已經**在讀同一張扁平表 —— 那 174 個財務桶、七條恆等式的運算元，
全是從它來的。在 PageRegions 再寫一支扁平表解析器，就是同一個判斷長出第二顆頭。

代價也量過了，不是用猜的：整輪 64 個 SINGLE 裡 **59 個是 `cover.current_price`**
（全格式共通，因為本機資料庫不在，跟文字模式無關）。文字模式真正多付的，是語料裡
那唯一一個 `.txt` 檔的 5 個 `title.*` 部位。8 個文字檔在 107 檔語料裡，影響有界且小。

所以做的是**把話說準**：G15 那一列的訊息從籠統的「ENG394 文字模式會漏句」換成上面量到的
規則、對照 PDF 的數字、漏掉的原文去哪查（資料庫 completeness 表的 `missing_text` 欄），
以及「不補第二支解析器」這個決定與它的理由。

要不要補，是操作員的裁量，不是我單方面決定 —— 但要補之前，得先想清楚兩支解析器
對同一張表給出不同答案時，哪一支說了算。

### Codex #66 的兩條：我自己寫了一條會說謊的訊息

上一節把 G15 的規則量清楚、寫進訊息裡。Codex 審完指出兩件事，**兩件都對**，
而且第二件正是我整個 session 在修的那個毛病。

**P2-1　寫在被切掉的地方，等於沒寫。**
`def_render_html` 只渲染 `detail[:400]`、主控台只印 `detail[:140]`。
那一列的 detail 前面是六個檔名，光檔名就吃掉前 140 字 —— 我加的 360 字說明，
操作員**一個字都看不到**。實測 detail 總長 596，400 之後被切掉的正好是
「原文去哪查」「為什麼不補」「代價多少」那三段。

拆成三列，每一列的 detail 都短到主控台看得完。

**P2-2　我把合成語料上量到的病因，套到任何殘缺的文字檔上。**
那段訊息寫死「本文尾段緊接扁平表」，還引 75／99／123 字與 PDF 抽 42 列。
但觸發條件只是「有 txt／docx 沒到 99.9%」—— 操作員拿真報告跑 `--samples` 時，
**完全不相干的抽取缺口也會被貼上這個根因**。報告在說謊，只是這次說謊的是我。

改成以**這一輪自己的證據**判定：缺口後面接的字，要真的是這份檔某張表的開頭
（`def_text_gap_split`）。對得上才說是那個樣子，對不上就只報本檔漏了多少、漏的是什麼，
不替它斷病因。引用的數字也換成本輪實測，不再引合成語料的固定值 ——
這一輪印的是「漏 75 字，接在表『項目(NT$百萬元)』前」，那是量出來的，不是抄的。

回歸測試五條，兩邊分支都證：對得上的要說得出「接在表⋯前」，對不上的
**不可以**出現「接在表」三個字；沒有表的檔永遠不會對上；沒有缺口明細就照實說；
以及組出來的 detail 要塞得進 HTML 真的會渲染的 400 字。

### Codex #67：同一類錯誤，再深一層

上一節把「不要替不相干的**檔**斷病因」修好了。Codex 緊接著指出：檔內也一樣。

`def_text_gap_split` 用 `next(...)` 取第一個對得上表頭的缺口，就把**整個檔**判成
表格相鄰那一類。而 ENG392 的 `missing_segments(src, ext, limit=20)` 一頁最多留 20 段
（頁層呼叫用 10）——一個檔同時有「卡在表前」和別的缺口時，後者被無聲吞掉，
報告卻說這個檔的缺口是表格造成的。

**我修好了「不要套到不相干的檔」，卻留下「不要套到檔內不相干的那一段」。**

改成逐段分類：每一段各自判，一個檔有兩種缺口就同時出現在兩邊；列的措辭也從
「N 檔」改成「N 段」，因為數的本來就是段。

回歸測試兩條，對逐檔那一版紅在 `0 != 1 : []`（不相干那段被吞掉）與 `1 != 6`
（六段只數到一段）。第二條盯的是「進去幾段，兩邊加起來就要是幾段」——
不准有缺口無聲消失。

### 2026-10-19 真實輸出實測：表頭脈絡把金額標成百分比

拿 10/17 那份 105 檔語料快照跑完整鏈，翻資料庫引擎真正寫出去的列，看見這個：

```
6141 列  營收          unit='%'   scale=1.0
6141 列  毛利率(%)      unit='%'   scale=1.0
6141 列  稅後淨利       unit='%'   scale=1.0
6141 列  每股盈餘(元)    unit='NT$' scale=1.0
```

營收 11,507、稅後淨利 1,420，單位都是百分比。

`parse_financial_tables_to_records` 取 `rows[:3]` 當表頭脈絡。表頭底下第二列就是
「毛利率(%)」——**資料列的列標進了表頭脈絡**。`def_unit_of` 的階梯又是 % 先判，
於是同一張表裡每一列金額都被標成百分比。

Codex #65 P1 修的是「列標自己的單位要贏過表頭」，那一半是對的。沒修到的是
**「表頭」根本不是表頭**：取到第三列，就把隔壁科目的單位當成全表的單位。

退路只能是表頭與它上面的標題列，所以脈絡取到 `rows[: header_idx + 1]` 為止。

#### 比想像的更糟：表頭寫對了也會輸

```
項目(NT$百萬元) | 2024A | 2025F        舊：營收 → ('%', 1.0)
營收            | 11,507 | 13,200       新：營收 → ('NT$m', 1,000,000.0)
毛利率(%)       | 25.3   | 26.1
```

表頭明明白白寫了「(NT$百萬元)」，營收照樣被隔壁列的 (%) 蓋掉，連 ×1,000,000
一起掉。金額差一百萬倍，而且型別是錯的。

#### 為什麼 16 組已知答案一次都沒紅

兩個原因，都要寫下來：

一、`def_UnitInferenceTests` 那六條**全部直接把 HEADER 字串餵給函式**。函式本來就
是對的，錯的是呼叫它的那條路——`table_context` 怎麼組出來。驗了函式不等於驗了
那條路。新加的三條走 `parse_financial_tables_to_records`，對舊版紅在
`('%', 1.0) != ('NT$m', 1000000.0)` 與 `'%' == '%' : 營收 是金額，不是百分比`。

二、語料自己的表格列序剛好避開它。`def_table_rows` 是
`項目 → 營收 → 營業成本 → 毛利 → 毛利率(%) → …`，`rows[:3]` 只吃到
「項目／營收／營業成本」，沒有任何 (%)。**同一份已知答案語料在這個缺陷上是瞎的**，
所以這一輪重建語料後跑出來的 14 種列標單位全對，不能當成這條修正的證據——
證據是上面那兩條迴歸測試，和 10/17 快照裡那 12,282 列真的被寫錯的輸出。

沒有為了製造紅燈去改語料的列序：那個列序本來就是台灣券商表格的印法。

### 同一輪：全景掃描把兩個對的檔判成要修

`VIA_SystemPanorama_v0100.py` 的 `MOJIBAKE_DETECTOR_HINT` 認得兩種「U+FFFD 是偵測器
本身」的寫法：運算子在前（`-match "<U+FFFD>"`）、運算子在後（`"<U+FFFD>" in text`）。

認不得第三種——**正規式的字元集**：

```python
GARBAGE_RX = re.compile(r"[<U+FFFD><U+E000>-<U+F8FF>]|\(cid:\d+\)")
```

於是 ENG392（母倉逐位元組鏡像）被判 `replacement_char / LOCKED`，抄了同一條樣式的
`VRN_REGEX_SSOT_v0100.json` 被判 `replacement_char / NEEDS_REBUILD`。報告等於叫人去
「修」一個跟母倉完全一致的檔，和一本內容本來就對的產生冊。

判準不變，只是多認一種寫法。掃完：`NEEDS_REBUILD 2 → 1`、`LOCKED 11 → 10`、
`BY_DESIGN 79 → 81`，而倉裡那三個**真的**轉碼掉字的第三方包（.vercel 兩個、
attachments 一個 html）原樣留在 `replacement_char`——放寬判準沒有把真的一起放過。

### 糾正：我把一份舊快照叫成「真實報告」

這一輪我先拿 `f_before`（10/17 的語料快照）跑，看到 3 筆 `title.company CONFLICT`
（賴偉中／施志鴻／李承泰，都是分析師名字佔了公司位置），寫下「真實語料暴露出
合成語料藏住的缺陷」。

錯了。打開檔案一看：98 個 PDF 裡 51 個印著同一句「營運動能延續，評價仍具吸引力」，
分析師全是「王小明 analyst@example-research.com」。那是**合成語料**，而且是 10/17
的舊版——`def_synthetic_truth` 10/18 的註解把這三個案例講得清清楚楚
（`-KY` 在 protect() 被抽走、「中信金」被當成券商「中信」），早就改成只問 ENG396 一次。

用現在的產生器重建語料再跑：`公司 ✓58/~1`，CONFLICT 0 筆。那 3 筆是舊快照的
產物，不是產品缺陷。讀法把標題裡的「賴偉中(2637 TT)」讀成公司名、再跟檔名交叉比對
報 CONFLICT、拒絕上鎖（lock: OPEN, priority 1）——那是系統**正常運作**。

要是我照著「修」讀法、讓檔名贏過文件，真報告就會壞。檢查輸入是什麼，和檢查輸出對不對，
是同一件事的兩半。

### 更正的更正：我更正了一件本來沒錯的事，而且新的解釋也是錯的

這一節原本寫「`7bd66b7` 的提交訊息把 PASS 39→36 歸因到 `--no-cache`，那個歸因是錯的，
真正的原因是冷快取沒東西可報」。Codex 在 PR #68 上指出這段站不住，查過確實如此。

`def_open_run_cache` **一定**會放一列 `P00 CACHE`：`cache.enabled` 就 PASS，不 enabled 就 WARN。
`def_close_run_cache` 在 `summary["enabled"]` 為真時**一定**放 `P20 CACHE` 與 `P20 TIME`，
不管命中幾筆。所以冷快取**照樣**會有這三列 —— 三列不見只有一個意思：**快取根本沒啟用**。

那為什麼 main 上那一輪（`m68`，沒加 `--no-cache`）也是 36？答案就印在我沒讀的那一列上：

```
[WARN] P00 CACHE · TEMP 快取：這一輪不用 :: 另一個 VRN 正在用快取：這一輪不用快取（照常全部重跑）
```

**鎖被佔住了。** 我把 m68 丟到背景跑，同時在前景跑 20 套測試，那些測試自己會跑 autotest 迴圈
（測試輸出裡就有 `[G06] TEMP 快取：…`）。兩個 VRN 搶同一個快取家目錄，後到的就不用快取。

所以正確的帳是：

| 跑法 | `P00 CACHE` 的理由 | PASS |
| --- | --- | --- |
| `r69` | `--no-cache`：這一輪全部重跑 | 36 |
| `m68` | 另一個 VRN 正在用快取 | 36 |
| `m68b` | `/tmp/Temp/VIA_progress/VRN_Main/cache`（TEMP 根） | 39 |

`7bd66b7` 對 `r69` 講的那句**本來就是對的**。錯的是我後來看到 m68 也是 36，就改口說成
「冷快取」——**我更正了一件沒錯的事，而且換上去的解釋是錯的**。

#### 這次的教訓跟前幾次不一樣

前幾次是「驗了一個不會跑到的東西」。這次是更難看的一種：**閘門已經把原因用中文印在列上了，
我沒讀**。我甚至還跑了一個「對照實驗」（m68b）去確認自己的猜想 —— 實驗結果和猜想一致，
但那個一致是巧合，因為兩種情況都會讓快取關掉。**同一個觀測對得上，不代表機制講對了。**

便宜的做法一直都在：`P00 CACHE` 那一列的 detail 就是 `cache.why`，直接說為什麼不用快取。
下次看到計數變了，先讀閘門自己給的理由，再談歸因。

#### 順帶一條真的發現

並行跑測試會讓同時在跑的那一輪**靜靜地失去快取**。這不是缺陷（鎖本來就該這樣，而且它誠實
報了），但量效能或比對計數時要記得：旁邊不能有第二個 VRN 在跑，否則量到的是沒有快取的數字。

#### 乾淨序列基準（旁邊沒有第二個 VRN）

上面那段是從讀碼推出來的。合併後再量一次，這次**序列跑、旁邊什麼都沒有**，兩輪：

| | `P00 CACHE` | 外層 | 內層 |
| --- | --- | --- | --- |
| 第一輪（快取是空的） | PASS · TEMP 根 | **PASS 39** · WARN 25 · SKIP 2 | PASS 383 · WARN 8 · SKIP 0 · FAIL 0 |
| 第二輪（快取有東西） | PASS · TEMP 根 | **PASS 39** · WARN 25 · SKIP 2 | PASS 383 · WARN 8 · SKIP 0 · FAIL 0 |

**第一輪的快取是空的，三列照樣都在，PASS 一樣 39。** 這就把「冷快取沒東西可報」那個說法
直接量死了 —— 不只是讀碼推出來的，是跑出來的。36 那兩輪從頭到尾都是「快取沒啟用」：
一輪是 `--no-cache`，一輪是鎖被我自己並行跑的測試佔住。

這張表就是這台機器上的基準。**要跟它比對，旁邊不能有第二個 VRN 在跑**，否則量到的是
沒有快取的數字（而且 `P00 CACHE` 會老實告訴你為什麼）。

## 2026-10-19 VRN-1：單一 PS 指令、HTML 掛名、收尾才上傳

操作員 2026-10-19：「名稱 VRN-1 跟另一個 VRN-2 作區別 · 自動跳出 HTML U/I 含報告及
驗證過內容 · 成功確認收尾登陸上傳 GITHUB AND SYNC ALL · 給我一個 PS 指令啟動此系統」。

入口沒有新開一支 —— `artifacts/VRN-1.ps1` 本來就是文件指定的操作員單一入口
（見本檔「正名 VRN-1」那節）。這一輪是把它測到真的能用，並補上缺的最後一段。

### 一、HTML 沒有掛自己的名字

`<title>` 是「VRN 獨立系統報告」、`<h1>` 是「VRN 獨立系統 · VRN_Main_v0100」。
操作員機器上 VRN-1 與 VRN-2 會同時開著，瀏覽器分頁並排時**分不出哪份是哪套**。

改成：

```
<title>VRN-1 研究報告系統 · 實測報告</title>
<h1>VRN-1 研究報告系統 · VRN_Main_v0100</h1>
VRN-1（本系統，MAIN 是 VRN_Main_v0100）—— 不是操作員機器上那套 VRN-2
（VRN_SystemManager_v0214.py，由 ActivateVRN-2 啟動）。
```

### 二、收尾判決機器讀不到

`def_wrapup` 是「這一輪能不能拿去用」的唯一判準，但它只活在 console 那一行與交接
capsule 裡 —— **報告 JSON 裡沒有**。下游（例如要不要上傳）就只能自己再判一次，
那是同一個判斷長第二顆頭：哪天 `def_wrapup` 的條件改了，上傳那條路會安靜地用舊規則放行。

改成把它原樣寫回 `VRN_Main_Report_v0100.json` 的 `wrapup` 鍵。補寫在 UI 驗證之後是
刻意的（`wrap` 要等 `ui_rows` 才算得出來）；P20 UI 比的是結論、計數、列數與連結，
多一個頂層鍵不在它的比對範圍內。

### 三、`-Apply` 與 `-SyncRepository` 在管線動作上被安靜吃掉

實測重現（PowerShell 7.4.6）：

```
VRN-1 check -SyncRepository -Apply   →  照跑 check，兩個旗標一個字都沒提
```

管線動作在加速器自檢之前就 `exit`，那兩個旗標只有診斷那條路的 GIT1／GIT2 在讀。
`param` 區自己就寫著「旗標被安靜吃掉⋯比直接報錯還糟」，這兩個卻正是那樣。

現在：能用的就用，用不到的講出來為什麼 —— 動作產不出實測、只給一個旗標、
收尾沒完成，三種各有各的話。

### 四、上傳：只有收尾完成的那一輪才上得去

新增 `VRN_Main_v0100.py sync`（`VRN-1 sync` 走同一條路）：

```
讀報告的 wrapup → 提交 → fetch → 落後就快轉 → push -u origin <branch>
```

**預設是空跑**，把每一步要做什麼印出來，一個位元組都不寫、不連遠端；`--apply` 才真的做。
和倉裡既有的規矩一致：`-Apply` 管寫入、`-SyncRepository` 管連網，推上 origin 兩件都要。

fail-closed 的幾處，都是「寧可停下來也不要猜」：

| 情況 | 為什麼停 |
| --- | --- |
| 報告沒有 `wrapup` 鍵 | 舊版 MAIN 跑的。**沒有判決就是沒有判決，不可以當成過了** |
| `wrapup.done` 是 false | 沒驗過的結果推上去，下一個人看到的是一條綠的分支 |
| detached HEAD | 沒有分支就沒有上游，不猜要推去哪 |
| 落後且超前（分叉） | ff 併不過去，怎麼併是人的決定 |

### 五、`--out` 從來就穿不過 PowerShell

實測發現的既有缺陷，不是這次改出來的（拿 HEAD 的版本重現過）：

```
VRN-1 run --out X  →  Parameter cannot be processed because the parameter name 'out'
                      is ambiguous. Possible matches include: -OutVariable -OutBuffer.
```

PowerShell 把 `--out` 前綴比對到共用參數就停掉，**連 MAIN 都沒跑到**。逐個試過：
`--samples`／`--rounds`／`--no-cache`／`--synthetic`／`--no-open` 都正常，只有 `--out` 會撞。

修法是宣告成**精確**參數名 `-Out`（精確比對優先於前綴比對），再翻回 MAIN 的 `--out`；
`-Out X` 與 `--out X` 兩種寫法都通。先在小探針上證過才改正式檔。

### 操作員的單一指令

倉根兩支啟動程式，**沒有任何路徑要填**（`%~dp0` 取自己的位置），可雙擊也可在 CMD／PowerShell 裡跑：

```
VRN-1.cmd          跑完整鏈、開 HTML，不上傳
VRN-1-Sync.cmd     跑完整鏈，驗過就提交並推上 GitHub
```

分成兩支而不是用旗標：「會推上 origin」不該靠記得加參數，也不該是雙擊的預設行為 —— 檔名自己講清楚。

絕對路徑是刻意的：上一輪操作員遇到的啟動失敗就是 cwd 不對 + 相對路徑。
`VRN-1.ps1` 開頭的 VIA-ENTER-ENV 會自己找倉根，所以從任何目錄用絕對路徑叫也成立。

**為什麼要做成檔案而不是叫人貼一行**：貼指令要填路徑，而我連續三次給出填不起來的版本 ——
`<倉根>` 佔位符、`cd /d`（CMD 語法貼進 PowerShell）、相對路徑（人根本不在倉裡）。
操作員那邊的畫面是 `引數 'artifacts\VRN-1.ps1' 無法辨識為指令碼檔案名稱` 連三次。
**要填的東西就是會填錯的東西**，所以改成兩支取自己位置的啟動程式，把「填」整個拿掉。

### 六、第一次真的用它上傳，就推了一顆紅的

`VRN-1 all -Apply -SyncRepository` 第一次實跑：鏈全綠、收尾完成、提交、推上 origin，
`87ce66e`。然後對那顆 commit 跑 `check`：

```
[CHECK] RED · FAIL=1 WARN=0 SKIP=0 PASS=11
         P03 REGISTRY · 內容與登記 SHA-256 相符 · VRN_SYSTEM_v0100.md
```

原因是我自己：鏈跑到一半我改了這份文件。`build` 在 `[ALL 1/4]` 就跑完了，註冊冊記的是
改之前的 SHA；等鏈綠燈、sync 提交時，樹裡已經多了一個冊上沒有的版本。

**這不是操作失誤而已 —— 這是這個功能本來就缺的一道門。**

> 那一輪的綠燈，是**跑 check 那一刻**的綠燈。
> 提交發生在之後。**驗過的東西，不一定就是提交出去的東西。**

所以 `sync --apply` 在真的 `git add` 之前，再驗一次倉本身的一致性，用的是 `check`
指令那四組（`def_check_ssot` + `def_check_registry` + `def_gate_astid` + `def_gate_engine_lock`），
沒有另寫一套判準。對不上就不提交，並且把對不上的檔名講出來：

```
[SYNC] 不提交 · 工作樹跟冊對不上（跑完之後又被改過？先跑 build 再來）：
[SYNC]   [FAIL] P03 REGISTRY · 內容與登記 SHA-256 相符 · VRN_Main_v0100.py; VRN_SYSTEM_v0100.md
```

這道門是拿那顆紅 commit 當樣本證出來的 —— 先讓它真的推了一次，才知道要擋什麼。

### 七、`--run` 比 `--out` 更糟：它是**無聲**綁錯的

修完 `--out` 之後，第一次真的用 `VRN-1 sync --run <資料夾>`，MAIN 說「找不到任何一輪實測的報告」。
資料夾明明在。

`VRN-1.ps1` 自己有一個 `-RunStamp` 參數。`--run` 前綴比對上它，於是：

```
param 有 -RunStamp 時：  RunStamp='/tmp/v3'   Rest=[]
加上精確的 -Run 之後：    RunStamp=''          Run='/tmp/v3'
```

**值被送進了另一個參數，`$Rest` 是空的，沒有任何錯誤。** `--out` 至少會報
「ambiguous」然後停下來；`--run` 是照跑、照綠燈、只是你打的那個路徑去了別的地方。

修法同上（精確參數名 `-Run`），但重點不是這一個旗標 —— 是**這一類**：
本支每多一個自己的參數，MAIN 那邊就多一組會被無聲吃掉的旗標，而清單會過期。

所以同時加了一道不會過期的門：管線動作跑的時候，本支專屬的診斷參數
（`-Mode -RunStamp -TailLines -NoEvidence -Quiet -JsonOut`）只要被綁上就講出來：

```
YELLOW VRN-1  這幾個是診斷用的，管線動作 sync 吃不到，這次沒有生效：-RunStamp -TailLines
YELLOW VRN-1  （要傳給 MAIN 的旗標直接寫，例如 --rounds 2；-Out 與 -Run 有專屬參數）
```

操作員打的字沒有生效，就要讓他知道。不講，他會以為生效了 —— 這一輪我自己就是這樣
被騙了一次。

### 八、我拿一個不存在的問題打折扣

交付時我寫了一句「PowerShell 5.1 相容性只能從語法判斷，我測的是 7.4.6」。操作員回：
**「全部用 PS 7 以上，為何下調？」**

他是對的，而且答案就印在我整輪都在改的那個檔的**第一行**：

```powershell
#requires -Version 7.0
```

倉裡 36 支 `.ps1` 都這樣宣告，CI 也是 `shell: pwsh`（PS 7）跑 windows-latest。
**5.1 從來不在範圍內。** 我那句不是誠實，是多餘的保留 —— 拿一個不會發生的情境來替
真正驗過的東西打折扣，讀的人會以為我沒把握。該講的是驗了什麼、沒驗到什麼，
不是替沒人要用的環境留退路。

#### 同一次抓到的兩件真東西

**一、我不小心加了 BOM。** 用 `utf-8-sig` 寫檔，PowerShell 檔就多了 BOM。倉裡 47 支
`.ps1` 有 45 支沒有 BOM，`VRN-1.ps1` 原本也沒有。PS 7 不需要它。已移除，
跟原版的差異回到只剩我真正改的那四段。

**二、PSScriptAnalyzer 早就在指那個 bug 了。** 拿釘住的 1.24.0 比對改動前後：

```
改動前   Error 0   Warning 19   （其中 PSReviewUnusedParameter 5）
改動後   Error 0   Warning 13   （PSReviewUnusedParameter 0）
```

那 5 個「宣告了卻沒用到的參數」就包含 `-Apply` 與 `-SyncRepository` ——
**linter 一直在報「這兩個參數沒人用」，而那正是「旗標被安靜吃掉」的另一種講法。**
報告看得到，只是沒人去讀。

#### 連帶更正一條過期的註記

`.github/workflows/powershell-lane-verify.yml` 的抬頭寫著「這個沙箱沒有 pwsh
（也下載不到，proxy 403），所以本機也驗不了」。**那條現在是錯的** —— 官方 tarball
下得到，PSScriptAnalyzer 也 Install-Module 得起來。這一輪的語法、PSSA 與**實際執行**
全都是推之前在本機先驗過的。註記已更正，附上指令 —— 不然下一個人會照著它相信
「.ps1 只能等 CI」。

### 九、Codex #70：三條，而且 P1 那條是我半套的守門

PR #70 合併得比我推更正快一步，所以這三條是對 `dad491f`（已在 main）提的。全部成立。

#### P1 · 報告沒有綁在要推出去的那棵樹上

我加的一致性守門寫在 `if changed and apply_now:` 裡面。於是：

> **工作樹乾淨、但有還沒推的 commit** —— 那條路一個閘都沒過，照樣拿舊報告的綠燈推出去。

我前一節才剛寫下「驗過的東西不一定就是提交出去的東西」，然後只修了一半：
修到了「提交之前」，沒修到「推之前」。

而且就算有東西要提交，一致也只說明「冊與檔**現在**對得上」，不說明**這份報告驗的就是
這些檔**。拿三天前一輪成功的報告，配今天的樹，照樣過。

兩個都修：
- 閘移到函式這一層，不管有沒有要提交，**推之前一定驗**；
- 收尾判決帶上 `registry_sha256`（跑那一輪時註冊冊的 sha）。註冊冊裡有倉內每個受管檔的
  內容雜湊，所以改過任何一個，要嘛 check 紅（冊沒重建），要嘛這個 sha 變（冊重建了）——
  兩種都抓得到。對不上就說「這份報告驗的不是現在這棵樹」。

#### P2 · 先 commit 再 fetch，遠端有進度時必然判成分叉

順序寫反了。遠端有新東西 + 本機有改動時：commit → fetch → `behind>0 且 ahead>0` →
判「分叉」停下 —— 留下一顆孤兒 commit，而它本來只要快轉就好。
改成 **fetch、快轉、然後才 commit**。

#### P2 · origin 上還沒有這個分支就永遠推不出去

`git fetch origin <新分支>` 會 `fatal: couldn't find remote ref`（實測 code=128），
而我把 fetch 的非零一律當致命 → `return 1`。下面那條 `behind is None`「第一次推」的路
**永遠走不到**，雖然程式裡明明寫了它、也用了 `push -u`。

改成先問 `ls-remote --heads origin <branch>`：分得出「遠端沒有這個分支」和「連不上遠端」。
前者是第一次推，後者才是錯誤。

#### 四條迴歸測試，對 `bc40ccc`（合併後的 main）全部紅

```
-1 not greater than 0 : sync 沒先問 ls-remote
3381 not less than 2904 : fetch 要在本機 commit 之前
8 != 4 : 一致性閘巢在條件裡（縮排 8），乾淨的樹就跳過了
'wrap["registry_sha256"]' not found
```

第三條我特地驗**縮排**而不是「有沒有呼叫」—— 因為原本就有呼叫，錯的是它巢在哪一層。
驗「有沒有」會綠，這正是上一輪沒擋住的原因。

### 十、Codex #71 P1：同一類錯誤的第三次

修完 #70 那三條，Codex 對修正本身又提一條 P1 —— **而且是同一類**：

> 快轉換掉了 `HEAD` 與工作樹。開頭那次閘與指紋比對，問的是**快轉前**那棵樹；
> 之後 commit 與 push 的，是**遠端帶進來的檔 + 本機還沒提交的改動**那個組合 ——
> 這個組合沒有任何一輪實測涵蓋過，註冊冊指紋也可能因此對不上。

三次都是同一句話的不同位置：

| | 閘跑的那一刻 | 真正送出去的那一刻 |
| --- | --- | --- |
| #70 前 | 跑 `check` 時 | 提交時（我改了文件） |
| #70 P1 | 提交前（且只在「有東西要提交」時） | 推時（乾淨的樹整個跳過） |
| #71 P1 | 動手之前 | **快轉之後**（樹被換掉了） |

**每一次我都修了「那一個位置」，沒修「這件事本身」。**

所以這次把閘與指紋抽成具名函式 `def_sync_tree_ok(payload, when)`，`when` 是「在哪一刻問的」，
印在訊息裡。它被呼叫**不只一次**是設計，不是重複：

- 「動手之前」—— 快點停下來，還沒碰網路；
- 「快轉 N 顆之後」—— **這一次才算數**，就在 commit 與 push 之前。

對得上也印一行（`冊與註冊冊一致（12 項 FAIL 0），報告指紋 adb31904… 對得上`）——
守門靜靜放行，看的人分不出它跑過沒有。

#### 一個連帶的真實後果

快轉若帶進受管檔的改動，指紋就會對不上，sync 會停下來說「要推就重跑一輪」。
**那是對的**：遠端那些改動確實沒有任何一輪實測驗過。這會讓「落後很多顆」時多跑一輪，
代價是分鐘級；省下的是「推出一份沒人驗過的組合」。

#### 這條的迴歸測試驗「呼叫幾次、在哪裡」

```
1 not greater than or equal to 2 : 快轉之後沒有再驗一次,只在開頭驗
```

不是驗「有沒有呼叫」—— 開頭那次本來就在。要驗的是**快轉之後還有沒有**，
以及它在不在 commit 之前。前兩次沒擋住，都是因為驗的是「有沒有」。

---

## 2026-10-19 第二輪：門檻的九頭龍、非原子寫入、TEMP 空間閘

這一輪沒有人回報問題。起點是上一輪收尾那兩個數字：`WARN 22 · SKIP 2`。
照「skip ≠ proof」去翻，兩個 SKIP 都是環境造成的（沒給樣本資料夾、這台沒有本機 SSOT），
誠實；但 WARN 裡翻出三件真的。

### 一、同一張報告上，兩顆頭講相反的話

上一輪的收尾報告裡並排印著：

```
P21 驗收   PASS   逐項驗過的報告 3/3 份 100% 過關
G00 LOCK   WARN   待修 3 項
```

講的是**同樣那三項**（`priority 3 · cover.current_price · SINGLE`）。

「待修清單上的項擋不擋收尾」在三個地方有三個答案：

| 位置 | 判法 | |
|---|---|---|
| `def_acceptance`（MAIN） | `priority <= 2` | 對，而且 `ACCEPT_RULE` 白紙黑字寫著 |
| `G00 LOCK`（MAIN） | 有列就 WARN | 錯 |
| `G18 待修清單`（AutoTestLoop） | 有列就 WARN | 錯 |

後兩處不是做了**別的決定** —— 它們從來沒問過這個問題，`if fixes:` 是偷懶的預設值。
諷刺的是 `def_acceptance` 自己的 docstring 早就寫過警告：

> **這裡不定義「過關」**……自己再判一次就是第二顆頭 —— 同一個問題會出現兩個答案，而且遲早不一樣。

門檻收進 `VRN_AutoTestLoop.def_fix_blocks` 一處（它產生那份清單，而且沒有被引擎鎖；
MAIN 本來就用 `def_load_module` 載它）。三邊都走它：`def_fix_blocks`（逐列）、
`def_fix_blocking`（整份清單）、`def_fix_blocking_from_counts`（`{優先序: 項數}`，
G00 LOCK 從 JSON 讀回來就是這個形狀，所以鍵是字串）。

**列數照舊印出來，沒有藏。** 59 檔那一輪現在是：

```
G00 LOCK   WARN   鎖：NEW 2843 · HELD 0 · BROKEN 0 · 待修 66 項（擋住收尾 2 項）
P21 驗收   WARN   逐項驗過的報告 57/59 份 100% 過關 · 待修 2 個檔
```

兩邊都是 2。改之前操作員只看得到「待修 66 項」，連不到 P21 的那 2 個檔。

改這一條的時候我自己先做出一個退步：清單空的時候 `fix_priority` 是 `{}`，
問門檻會拿到「算不出來」，於是 0 項待修會被印成 WARN。測試釘住了這一條。

### 二、`def_write_json` 不是原子寫入 —— 而收尾報告正是要讀回來的那一份

四支引擎（AutoTestLoop、RunCache、Lock、TempStore）早就是 `tmp` → `os.replace`，
AutoTestLoop 甚至寫了註解說明為什麼：「原子換檔：成功才生效，失敗時原檔一個位元組都沒動」。
**MAIN 的 `def_write_json` 漏了**，是裸的 `write_text` —— 而它寫的是
`VRN_Main_Report_v0100.json`，也就是 `def_sync_blockers` 上傳前要讀回來的那一份。

不是理論風險。同一個寫入器，一邊寫一邊讀 400 次：

```
舊寫法（write_text）    讀到半份 JSON 296 次
新寫法（os.replace）    讀到半份 JSON   0 次
```

**不 fsync**：`os.replace` 保證「不會看到半份」，fsync 保證「斷電後還在」。
這些檔每一輪都重寫，斷電後本來就要重跑，為那個保證每次多付幾毫秒不值得。

同一類的另一處記在這裡但**沒有動**：`VRN_Lock_v0100.Ledger.save()` 的 tmp 檔名是
`with_suffix(".tmp")`，**沒有帶 pid**，兩個行程同存一本帳本會撞在同一個 tmp 上。
那支是引擎鎖住的檔，照規矩要先 `lock` 重新驗過已知答案才換鎖；改它要為這一件事
重發 51 支指紋，留給下一輪單獨處理。

### 三、`P10 TEMP` 從來不看剩餘空間

TEMP 是這條鏈上**唯一真的會用完**的資源，而這道閘報本輪夾、報清掉幾輪，就是不報還剩多少。
用完的樣子不是一聲乾淨的錯誤：寫到一半的檔留在那裡，下一個讀它的人拿到 JSONDecodeError
—— 和第二條是同一件事的兩面。

新增 `def_gate_temp_space`。**第一版我寫錯了**：拿 `budget_gb` 當門檻，而
`budget = min(cap, 剩餘的 25%)`，所以 `free < budget` 恆不成立 —— 那個 WARN 分支
永遠跑不到，而一道永遠不會警告的閘跟沒有這道閘是一樣的。改用快取**被設定的上限**
`VIA_CACHE_MAX_GB`（預設 10 GB，用引擎自己的 `cache_env_num` 讀，不另開一套）當尺。
測試裡有一條 `test_every_branch_is_reachable` 就是釘這件事。

### 四、worker 天花板：卡住的不是硬體，是一個猜出來的常數

`cache_resources` 算 `workers = min(by_cpu, by_mem, ceiling)`，而 `ceiling` 預設寫死 8。
這台（4 核）量到的是 `by_cpu 3 · by_mem 25 · ceiling 8` —— **記憶體根本不是瓶頸**，
它准 25 支。但核心數超過 8 的機器上，`by_cpu`（核數減一）會被那個 8 整個吃掉。

`VRN_RunCache_v0100.py` 是引擎鎖住的檔，而且**這台只有 4 核，我量不到那個改善** ——
不為量不到的東西去動鎖住的引擎。改在 `artifacts/VRN-1.ps1`（它跑在操作員的機器上，
核數在那裡才知道）：核數大於 8 時才把 `VIA_VRN_WORKERS_MAX` 抬到核數，
**絕不往下調，也不覆蓋操作員自己設的值**。抬天花板不等於放生 —— 真正的上限
仍是 `by_cpu` 與 `by_mem` 的小者，記憶體那一道還在。

### 五、擋住收尾的那 2 項：是 fixture，不是漏讀

59 檔裡 2 項 `cover.broker MISSING`。**這次先看了文件內容才下判斷**（上次我把
fixture 性質的 3 筆 CONFLICT 講成產品問題）：

| 檔 | 首頁第一行 |
|---|---|
| 華南投顧-2606-裕民（過） | `華南證券投資顧問  HUANAN Securities Research` |
| 3014TT-20231005（擋） | `測試公司3014(3014 TT) …`，**整份沒有券商那一行** |
| 6933_AMAX-KY（擋） | 同上 |

合成語料的產生器只在檔名含券商代號時才寫券商抬頭。文件裡沒有券商可讀，
`MISSING` 就是正確答案。要證「真的漏讀」只能用操作員機器上的真實報告。

### 六、VDF：那支檔不在任何一個倉裡

> **界線（2026-10-19 操作員重申）：VRN-1、VRN-2、VDF、VCGC 是四套獨立系統，互不干涉。**
> 這一節記在 VRN 的文件裡，只因為那個要求是在這一場對話裡提的 —— **VRN 這邊沒有為它改任何一行**，
> 也沒有任何 VRN 的修法以「VDF 會同時跑」為前提。
> 我在對話裡講過兩次「操作員會同時跑 VRN 和 VDF，快取鎖爭用就是證據」—— **那是錯的**：
> `VRN_RunCache_v0100.py:383` 的訊息寫的是「另一個 **VRN** 正在用快取」，
> 而那次爭用的真因是我自己並行跑的測試。本輪所有寫入安全的量測
> （296/400、70/400、symlink、權限）都是在 VRN 單一系統內做的，結論不依賴那個前提。


操作員說「把 VDF 那個倉加進來一起修」。三個倉都加進來搜過了
（`VIA-VDF-VRN`、`VeritasIntelligenceAnalytics`、`via_01_vdf`）：
**`ActivateVDF` 零命中，「VDF 獨立一鍵」零命中。** `VDF_MDL013_ActivateVDF_v0100.py`
只在操作員那台機器上，沒有進版控 —— 所以那支本身修不了，照實說。

但錯誤訊息讀得更準了。**實驗推翻了我原本的讀法：**

| 檔案內容 | `json.load` 的錯誤 |
|---|---|
| `1234\n5678`（JSONL 用 json.load 讀） | `Extra data: line 2 column 1` |
| `true{"a":1}`（**中間沒有換行**） | `Extra data: line 1 column 5 (char 4)` ← 就是這個 |

所以**不是** JSONL 被 `json.load` 讀的那個 bug（那會報 line 2）。
`line 1 column 5` 要求前 4 個字元是一個完整 JSON 值、**緊接著**還有東西、中間沒換行。
最可能是：同一個開啟的檔案被寫了兩次，或用短內容覆蓋長檔案而沒有 `truncate()`。

可達的 VDF 碼（`via_01_vdf/engine`、`functional modules/VDF`）掃過了：
全部是 `write_text(json.dumps(...))`，沒有雙重 dump、沒有 append、
沒有 `r+`/`seek(0)` 不 truncate 的寫法 —— **那個 bug 不在可達的碼裡**。
（VRN 的三處 `seek(0)` 都是上鎖／解鎖用的，不是寫入。）

### 七、6 處 `FNCNEW<n>`：不是沒發編號，是疊在真編號上的垃圾

一開始我以為 `VRN_AstId` 給六支函式發的是佔位號而不是序號。**查過之後不是那樣**
—— 注入器的原始碼裡根本沒有 "NEW" 這個字串，而那六行每一行的**下一行就是真編號**：

```
# [VRN-ID] VRN-MAN001-FNCNEW4 · IO     ← 不在 ID 冊裡
# [VRN-ID] VRN-MAN001-FNC114 · IO      ← 在冊上的真編號
def def_write_capsule(...)
```

六處全部如此，沒有任何一支函式是只靠佔位號。所以那不是治理漏洞，是某個舊版注入器
留下的陳舊重複 —— 注入器只加不刪，所以它們一直疊在那裡。危害是：
任何用 `[VRN-ID] (\S+)` 抓第一個命中的工具（包括這份文件裡那些讀原始碼的測試）
會拿到一個不存在於 ID 冊的編號。

清掉了。而且順手驗證了一件治理機制的事實：**兩支被引擎鎖的檔（`VRN_Focus`、
`VRN_PanoramaProbe`）編輯之後，不跑 `lock` 直接 `check`，`P16 LOCK` 照樣 PASS
（守住 51 · 改了 0）** —— 鎖的是 AST 指紋，註解不算。紅的只有 `P03 REGISTRY`
的內容 SHA-256，那是 `build` 的事。所以「動到鎖住的引擎就一定要重發指紋」不對，
要看動到的是不是 AST。

### 八、CI 教的那一課：原子寫入在 Windows 上會把「讀到半份」換成「直接炸掉」

上一節的原子寫入推上去，CI 紅了一條 —— 而且是**這台 Linux 怎麼跑都不會紅**的一條：

```
PermissionError: [WinError 5] Access is denied:
  '...\VRN_Main_Report_v0100.json.2272.tmp' -> '...\VRN_Main_Report_v0100.json'
```

Windows 的 `os.replace` 在**目標檔正被另一個握把開著**時會失敗。我的測試有個讀取者
一邊讀一邊讓寫入者換檔 —— 於是兩側都拿到 `PermissionError`：寫的那一側換不了檔，
讀的那一側在換檔的瞬間開不了檔。

這不是測試的毛病，**操作員就是在 Windows 上跑**。換句話說：我那個「原子寫入」在他那台
會把「偶爾讀到半份」換成「這一輪直接炸掉」。那不是改善。

Windows 上那個握把是毫秒級的（讀報告的人、防毒、索引器都會造成它），所以標準做法是
**有界重試**：`def_retry_access`，20 次 × 50 ms ＝ 最多 1 秒，撐不過就照實丟出去
（那就不是暫時的了）。寫入與讀取兩側都走它 —— `def_read_json` 也包進去，
因為收尾鏈正是從那裡把報告讀回來的。

只重試 `PermissionError`。檔案不在是 `FileNotFoundError`，重試 20 次只是讓錯誤慢一秒才出現。

**我在 Linux 上證不了那條路**，所以測試改成直接測重試邏輯本身（`TestAccessRetry`，
平台無關：暫時失敗要等過去、永久失敗要丟出來、其他錯誤不重試、呼叫端真的有走它）。
真正的證明是 CI 的 Windows runner 從紅轉綠。

### 九、鎖帳本的 tmp 撞名（這次動了鎖住的引擎）

第二節記下「沒動」的那一處，這一輪處理掉了 —— 因為我把「不划算」這個判斷量過了：
`lock` 重新驗過已知答案再換指紋，這一輪跑了四次，每次兩分鐘、每次綠。
那不是不划算，那是這條鏈本來就設計好的動作。

`VRN_Lock_v0100.Ledger.save()` 的 tmp 檔名是 `with_suffix(".tmp")`，**沒有帶 pid**。
兩個行程同存一本帳本就會撞在同一個 tmp 上：A 寫完要換檔的瞬間 B 已經把它截短重寫，
A 於是把 B 寫到一半的內容 rename 成正式帳本。先量再改：

```
共用 .tmp（現況）        讀壞 70 次 · 換檔時 tmp 已被搶走 156 次
帶 pid/thread 的 tmp     讀壞  0 次 · 換檔時 tmp 不見     0 次
```

帳本是擋退步的那一份 —— 它壞掉等於守門自己先倒。慣例跟 `VRN_RunCache` 同一個。
`lock` 重新驗過 Lock 引擎的已知答案（13/13）才換的指紋。

`Ledger.log` 沒動：它是單行 append，兩個平台都是原子的。
引擎那一側**沒有**加 `def_retry_access`：那支是葉節點、不能 import MAIN，
複製一份就是第二顆頭。照實記在這裡，不假裝它已經防住 Windows 的換檔窗口。

### 十、MAIN 的原子寫入收成一個

第二節只改了 `def_write_json`，但 MAIN 還有三處裸的 `write_text`，其中一處
（第 2294 行）就是**操作員會開的那份 HTML**。四處全部走同一個
`def_write_atomic(path, text, newline)` —— MAIN 這一側只有那一份實作。

`newline=None` 這個參數是留給貼回檔的：它本來就吃平台換行，不在這裡偷偷改掉它的行尾。

### 十一、把自己的 diff 當成別人的來讀，抓到同一個 bug 的第三個實例

`08199d3` 推上去之後，我用審查的眼光把整份 diff 再讀一次 —— 然後在自己剛寫的碼裡
看到幾十分鐘前才修掉的那個 bug：

```python
tmp = path.with_name(path.name + f".{os.getpid()}.tmp")     # def_write_atomic，只帶 pid
tmp = self.path.with_name(... f".{os.getpid()}.{threading.get_ident()}.tmp")  # 剛修好的 Lock.save
```

只帶 pid 不夠，而且 **MAIN 正是會並行跑前置步驟的那一支**（`_MODULE_LOCK` 的註解
自己寫著「the pre-steps run side by side」）。同一個行程裡兩條執行緒寫同一個路徑，
就會算出同一個 tmp 名字 —— 和 `VRN_Lock.save()` 那個一模一樣。
一邊加固 Lock、一邊在 MAIN 留著弱的版本，說不過去。

**而且這次沒有停在原始碼斷言。** 我原本加的測試是「原始碼裡要有 `threading.get_ident()`」
—— 那種測試在 bug 不長成那個字面時會假綠。所以補了一條真的開兩條執行緒寫同一個檔的，
再把 tmp 名字暫時改回只帶 pid 驗它抓不抓得到：

```
只帶 pid        test_two_threads_writing_one_path_do_not_tear_it  FAIL · 讀壞 44 次
帶 pid+thread   同一條測試                                        PASS · 讀壞  0 次
```

在壞的版本上也會過的測試等於沒有測試。驗過才算。

### 十二、把同一把尺量過全部六個 `os.replace` 現場（結論：另外四處不用改）

修完 MAIN 與 `VRN_Lock` 之後，剩下四處的 tmp 檔名其實更弱 —— 但**弱不等於會出事**。
逐一查可達性，不是看字面：

| 現場 | tmp 檔名 | 兩個寫入者會不會打到同一個路徑 |
| --- | --- | --- |
| `VRN_TempStore.put_json` | `with_suffix(".json.tmp")`，**連 pid 都沒有** | **不會**。slot 的 key 是檔名，每檔唯一；而 G07 是「逐一（不拆執行緒）—— 首頁引擎實例與快取共用」。run 資料夾又是每個行程自己的。 |
| `VRN_RunCache` STAT_MEMO | 帶 pid | **不會**。快取資料夾跨行程共用，但 pid 把它們分開；行程內一輪只寫一次。 |
| `VRN_RunCache` INDEX | 帶 pid | **不會**。同上，`cache_close` 一輪一次。 |
| `VRN_AutoTestLoop` zip 正規化 | 帶 pid | **不會**。每個 zip 各自一條路徑，而且失敗只失去一次快取命中（它自己有註解說明）。 |

**所以這四處不動。** 不為不可達的競態去改三支引擎鎖住的檔 —— 那只是把 diff 變大，
把審查的注意力從真的東西上移開。

對照之下，修掉的那兩處是**可達**的，理由不一樣：
`VRN_Lock` 的帳本是**所有行程共寫的同一個路徑**（實測讀壞 70 次）；
`def_write_atomic` 則是這一輪才變成**通用**寫入器 —— 它未來的呼叫端我管不到，
所以門檻要訂在最嚴的那一邊。

**如果哪天 G07 改成並行**，`put_json` 這一條就從「不會」變成「會」。
記在這裡，不是記在某個人的腦袋裡。

---

## 2026-10-19 第三輪：Codex 的四條，全部打在我這一輪寫的碼上

PR #72 的 Codex 摘要停在第一顆 `2714836`（只有兩支 `.cmd`）—— 它的觸發條件是
「PR 開啟／草稿轉正式／`@codex review` 留言」，**不是每次 push**。
所以後面六顆、也就是所有實質的程式碼改動，一次都沒被審過。留言請它審，回來四條：
兩個 P1、兩個 P2，**每一條都在我這一輪新寫的碼上**。四條都自己驗過才動手。

### 一（P1）· 可預測的 tmp 名字＝可以被預埋 symlink

我組的名字是 `<名字>.<pid>.<thread>.tmp` —— 唯一，但**可預測**。
輸出夾若是 `/tmp` 這種別人也寫得進去的地方，攻擊者先在那個名字上放一個 symlink，
`write_text` 就跟著它走。實驗（不是推論）：

```
預先放好 symlink: report.json.10894.140484016590976.tmp -> 受害者.txt
受害者檔現在的內容: '{\n "機密": "報告內容"\n}\n'     ← 被報告內容整個覆蓋
目標檔存在嗎: True                                  ← 而且它自己變成指向受害者的 symlink
```

任意檔案覆寫，外加報告變成別名。改用 `tempfile.mkstemp`：`O_CREAT|O_EXCL`、名字隨機
—— 不可預測、而且存在就失敗。順帶它也接管了「唯一性」，所以自己組 pid+thread 的那段
可以整個拿掉：**唯一性由 O_EXCL 保證，不是靠猜不到的名字。**

### 二（P1）· 原子換檔把目標檔的權限丟掉了

裸的 `write_text` 蓋舊檔會沿用舊檔的 mode；換成 tmp＋rename 之後變成沿用 tmp 的。實測：

```
原本權限 0600  →  原子換檔之後 0644     （我的改動造成的）
對照 裸 write_text  0600  →  0600        （原本是對的）
```

等於把報告內容攤開給同機器其他人看 —— 我在「修」安全性的那一輪，自己開了一個洞。
改成：目標檔存在時先把它的 mode 抄到 tmp 上再換；目標不存在時留 mkstemp 的 0600
（比 umask 預設更緊，只會更安全，不會更鬆）。

### 三（P2）· 我寫的空間閘，跑在它要防的事情發生之後

`def_cmd_run_body` 起於 2749、AutoTestLoop 跑在 2793、而我的空間閘在 2855 ——
**整整在重活做完 62 行之後**。一道防磁碟耗盡的閘跑在耗盡之後，等於沒有這道閘。

這就是這份文件從頭到尾一直在記的那個老毛病（「閘跑的那一刻，和真正出事的那一刻，
不是同一刻」），而這一次是我自己犯的，寫在我自己剛加的新閘上。

改成：`def_cmd_run_body` 一開頭就驗，FAIL 當場停、連中介檔都不寫；
收尾那一次留著，但它只是**回報**，不是防線。同一支 `def_gate_temp_space`
被叫兩次 —— 一支函式、兩個時刻，不是兩套判準。

### 四（P2）· 我抬掉的那個上限，正是「量不到記憶體」時唯一剩下的防線

`cache_resources` 裡 `by_mem = ... if mem_avail else cpu` —— **記憶體探測失敗時
`by_mem` 直接等於 `cpu`**。所以寫死的 `ceiling = 8` 不只是個保守的常數，
它是量不到記憶體時唯一還在擋的東西。我在啟動器把它抬到核數，等於在 32 核的機器上
讓它在完全沒有記憶體量測的情況下開出約 31 支重量級子行程。

**撤掉了。** 而且我加它的時候就說過：這台只有 4 核，那個好處我量不到。
拿量不到的好處去換一道真的防線，不划算。大機器要調，系統自己會講
（bottleneck 印「卡在上限」並點名 `VIA_VRN_WORKERS_MAX`），由知道自己機器的人去設 ——
那個人有記憶體的實情，這支啟動器沒有。

### 測試也跟著換掉：字面斷言 → 行為

原本兩條是「原始碼裡要有 `os.getpid()`／`threading.get_ident()`」。唯一性既然改由
O_EXCL 保證，那種斷言就只是在鎖住一個寫法。換成真的跑：預埋 symlink 看受害者檔有沒有被動、
0600／0644 看權限有沒有保住、低磁碟看 `def_cmd_run_body` 停不停得下來（它真的印出
`[STOP]` 並回 1，而且沒有留下任何中介檔）。
順序那一條留在原始碼層 —— 因為**順序本身就是那一條的全部**。

---

## 2026-10-19 第四輪：非 PDF 的財務表整張不見（修了我這一層，缺口還在）

合併後的 main 重跑一輪，內層 9 條 WARN 裡有兩條指向同一件事：
「截取完整度未達 99.9% 的 8 檔」和「文字檔缺口：8 段是本文尾段緊接扁平表」。
8 個檔、同一個結構位置、每檔漏 75 字 —— 不是隨機，所以去挖。

### 一、先量，再說有多嚴重

漏掉的那 75 字是**整段本文結尾**（主要動能／催化因素／風險），不是裝飾。
但真正的規模要看財務列的產出：

```
副檔名   檔數   有財務列的檔   財務列總數
.pdf      98        51          2142
.docx      7         0             0
.txt       1         0             0
.jpg       1         0             0   （OCR,設計使然）
```

**非 PDF 的財務表是整張不見，不是掉幾個字。** 而且不是「存成錯的數字」——
`rows_` 和 `checks` 對這些檔一列都沒有，下游認不得那種標籤就整張丟掉了。
無聲掉掉比無聲算錯好，但仍然是輸出缺口。

### 二、VRN 自己的那一半：`_docx_text` 把 Word 表攤平成一欄

Word 的表格**每一個儲存格裡都有自己的 `<w:p>`**，而 `VRN_PageRegions._docx_text`
是抓全文所有 `<w:p>` 用換行接起來。實測一份 `.docx`：

```
<w:tbl> 1 張 · <w:tr> 15 列 · <w:tc> 60 格 · <w:p> 68 段
_docx_text 產出 68 行 —— 60 格各自一行,行列結構整個沒了
```

改成照文件順序走：`<w:tbl>` 裡每個 `<w:tr>` 的儲存格用 tab 接成一行（和 `.txt`
的扁平表同形狀），表外的 `<w:p>` 仍是一行。7 個 `.docx` 全部 68 行 → 23 行
（8 段本文 ＋ 15 列表），而且**表外段落逐字相同** —— 封面欄位靠的是它們，
`VRN_TitleTrim` 也吃這支，不能動到。

不引 python-docx：G06 的 `extract_docx_text_and_zones` 已經用它把表讀得好好的，
但兩邊要的東西不一樣（這裡要「一段文字」、那裡要「結構化的表」），所以各自留著 ——
形狀對得上就夠，不必為了統一而硬合。

### 三、**修完之後缺口還在** —— 量過才說

```
副檔名   改前 有列/檔數  列數      改後 有列/檔數  列數
.docx        0/7          0            0/7          0     ← 沒變
.pdf        51/98      2142           51/98      2142     ← 沒退步
completeness RED 8/59                      8/59           ← 沒變
```

所以這一節要分成三句話，不能混成一句：
**(1)** VRN 自己碼裡的缺陷修好了（4 條測試在舊版全紅，證明它們真的會抓）；
**(2)** 沒有退步 —— 動了鎖住的引擎，98 個 PDF 的 2142 列一列不差；
**(3)** 輸出缺口**還在**，而且不在本倉。

### 四、卡在哪：ENG394 的表頭還原

`VRN_ENG394_LayoutRestore` 的 `text_tables` 把「連續的、結尾是數字的行」當成表的列。
表頭那一行（`項目(NT$百萬元) 2024A 2025E 2026E`）因為沒有純數字欄位**不算一列**，
被歸進第一列前面的 `gap` —— 於是出現 `項目(NT$百萬元) 2024A 2025E 2026E營收`
這種黏合。接著它只從 `header_vocab` 找**連續的表頭詞**來還原欄名，
而 `2024A/2025E/2026E` 不在那份詞表裡 → 找不到 chain → 欄名退成 `欄1/欄2/欄3`
→ 沒有年度就沒有財務列。

`engine/mother/VRN_ENG394_LayoutRestore_v0100.py` 是 **MIRROR_MOTHER**
（母倉逐位元組鏡像，改一個位元組就對不上），**不是本倉能改的**。

### 五、一個刻意沒拉的槓桿（要操作員決定）

`header_vocab` 在 **VRN 自己的冊**裡（`ssot/VRN_LayoutRestore_SSOT_v0100.json`），
由 VRN 餵進 ENG394 的 `_SSOT_CACHE`。加上年度欄頭的樣式，理論上就能讓它認得表頭
—— 那是不動母倉鏡像的唯一合法路徑。

**沒有拉。** 那本冊驅動**每一份報告**，包括現在跑出 2142 列、7 條恆等式全過的
98 個 PDF。為了 8 個檔去改全體的判準，風險不該由寫碼的人單方面承擔。
要不要拉、拉多大，是操作員的決定；真要做，驗收標準是
「.docx 的財務列從 0 變成有，而且 PDF 的 2142 列一列不差」。

---

## 2026-10-19 第五輪：時間一律三形、TEMP 交叉對照，以及我自己寫的兩句浮誇

操作員 2026-10-19：「時間擷取後格式一律為 YYYY YYYY-MM YYYY-MM-DD
擷取的資料後不同來源擷取相同資料將有中間檔 TEMP 標註不同來源用來交叉對照使用
相互對照兩個以上相同即算對照成功」。

三條規則落地的位置：

| 規則 | 落在哪 | 閘 |
|---|---|---|
| 時間一律三形 | `def_time_scan` 掃每一張輸出表的時間欄 | `P23 TIME` |
| TEMP 標註不同來源 | `def_cross_source_temp` 寫 TEMP bucket `cross_source` | G17 的一列 |
| 兩個以上相同即對照成功 | 判準本來就在 `VRN_TitleTrim._vote`（`len(top["groups"]) >= 2`） | `P24 CROSS` |

### 一、`ReportDateDisplay`：同一個時間的第二種表示法

`VRN_Integrated_ReportDatabase_Engine` 原本把 `report_date` 的 `-` 換成 `/` 另存一欄。
**一律就是一律，會漂移的正是第二種表示法。** 欄位照留（它在表頭冊的契約裡，`required=false`），
值改成和 `ReportDate` 同形；要斜線的人在顯示那一層自己轉。

這一改讓 `test_VRN_ReportDatabase_Engine` 原本釘死 `"2025/08/22"` 的那一行紅掉 ——
**那是對的**：行為刻意變了，測試就該紅。改法不是把字串換掉就算了，而是把**規則**釘上去
（`ReportDateDisplay == ReportDate`，且兩者都要合 `^\d{4}(-\d{2}(-\d{2})?)?$`），
再附帶那個已知答案。釘規則的測試換個語料還站得住，釘字串的不會。

### 二、`agree` 這一欄：規則本來就在，但數字掉在地上

`_vote` 一直都在數「支持採用值的來源群組數」—— `VERIFIED` 的定義就是它 `>= 2`。
但那個數字只進了 `why` 的中文句子（「標題+檔名+首頁引擎 一致」），**沒有欄、沒有輸出**。
下游要驗只能解析散文；真要用就得自己再數一遍 —— 那就是第九顆頭。

所以 `_vote` 一併記下 `agree`，`part_rows` 多一欄，`P24` 讀數字。

**型別一定要一致**：整數與空字串混在同一欄，G16 寫 parquet 時 Arrow 推不出型別
（`ArrowInvalid: Could not convert '' with type str: tried to convert to int64`）。
第一版就是這樣紅的。一律字串，讀的那一側自己 `int()`。

### 三、欄加了、冊沒加：G16 判 YELLOW，而 YELLOW 不是紅燈

`vrn_trim_parts` 多一欄 `agree` 之後，`test_VRN_AutoTestLoop.test_titletrim_and_lock_gates`
紅在 `'YELLOW' != 'GREEN'`。原因是表頭冊 `extra_ok: false` —— 冊上沒有的欄就是「多出欄」。

**這個洞 v0106 的 `process` 欄已經踩過一次。** 照同一條慣例補：
**出本冊新版，不在舊版上改**（舊版是 content hash 鎖住的）—— `VRN_Output_Header_SSOT_v0108.json`
= v0107 + 只有它自己宣告的那一筆 `changes_v0108`，`HEADER_BOOK` 指到新版。

為了讓它下次自己現形，測試不只比對版本差異，還直接拿 `part_rows` 寫出的欄名
去對**跑的那一本**（`D.load_book()`，不是我手挑的檔名）：
換版忘了改常數、或加欄忘了加冊，兩種都紅。兩個方向我都先證過會紅，才留下來。

### 四、我自己寫的 P24 標題，把沒驗到的算成驗過的

第一版的標題是「對照成功的部位 **1310** 個 · 來源數不足的 0 個」。

實測 1310 個 `VERIFIED` 裡，**只有 640 個走這條規則**；剩下 670 個
（`annual.*` 612、`title.core_view` 58）是別條路徑判的 —— 年度財報的部位是**驗算式**
那條路判 `VERIFIED` 的，它不代表有兩個來源讀到同一個值。

那句話會被讀成「1310 個都過了兩來源對照」。這跟
「不知道不等於沒事」是同一件事的另一面：**別人驗的，不等於我驗過的**。

改成標題只說這條規則真的驗到的那 640 個，並且把另計的 670 個放在標題上
（`各自路徑另計 670 個`），`own_kinds` 按群統計（`annual.*`／`title.*`）—— 整群都看得到，
不是只列前幾名。

### 五、同一句浮誇，在 TEMP 那一列又寫了一次（而且是兩層）

G17 的中間檔那一列原本寫「可對照部位 1257（對照成功 **1252**）」，用的是 `state == "VERIFIED"`。
同一個錯誤：1252 裡只有 640 是這條規則對上的。

改成讀 `agree` 之後還有第二層：`CONFLICT` 的部位 `agree` 也可能 `>= 2`
（兩個來源讀到同值、第三個不同）。把它算進「兩來源以上對上」就又多報 3 個 ——
**兩個來源讀到同值但有人不同意，不是對照成功。**

最後收成四個互斥的桶子，而且**加起來必須等於可對照部位總數**：

```
可對照部位 1257（對上 640 · 讀法不一致 3 · 別條路徑 612 · 其他 2）
```

倉內已有的紀律（`test_every_segment_is_accounted_for`：進去幾段，兩邊加起來就要是幾段）
搬過來：`sum(tally.values()) == parts`。有缺口就紅，不會無聲消失。

兩版錯的數法我都先改回去跑過、確認測試會紅，才算這一條測到東西
——「在壞的版本上也會過的測試等於沒有測試」。為此還把語料加強過一次：
原本的 fixture 用 `state` 數剛好也是 2，兩個數字分不開，測試會放它過去。

### 六、這一輪的實測（106 檔真實報告，操作員的語料）

```
build/lock/check  GREEN · FAIL=0 WARN=0 SKIP=0 PASS=12 · 鎖住 51 支引擎與冊
run               AMBER · FAIL=0 WARN=21 SKIP=1 PASS=43 · 收尾完成
P23 TIME          PASS · 合規 99084 筆（10 欄）· 0 欄不合規
                        原文欄不受規則管：period_raw／PeriodLabelRaw（照實點名，不是默默跳過）
P24 CROSS         PASS · 兩個以上來源對上 640 · 來源數不足 0 · 各自路徑另計 670
G16 DATAFRAME     GREEN（21 張表全綠；加欄前 vrn_trim_parts 是 YELLOW）
G17 TEMP 中間檔    59 檔 · 1257 個可對照部位，四類加總 1257
測試套件          408 案全過（VRN 17 套 + VDF 1 + artifacts 1）
```

TEMP 中間檔長這樣（實檔，`cross_source` bucket）：

```json
{"part": "title.ticker", "value": "2308", "state": "VERIFIED", "agree": 3,
 "sources": {"標題": "2308", "檔名": "2308", "首頁引擎": "2308"},
 "why": "標題+檔名+首頁引擎 一致"}
```

### 七、一個沒做的擴張（說清楚界線在哪）

`annual.*` 的 612 個部位要不要也給 `agree`？它們的 `sources` 有三個鍵
（`表格（TRIM）`、`原印`、`資料庫引擎`），看起來像三個來源 —— **但前兩個是同一次列印的
TRIM 前後，是同一個來源。** 把它們當兩票就是拿一個讀法假裝成兩個，比不報更糟。

真正能當第二票的是 `資料庫引擎同值`（`db_state == "AGREE"`）與驗算式；
這一輪的實測本機資料庫 `ABSENT`，所以大部分年度部位**本來就沒有第二個來源可對照**——
規則對它們不適用，照實分開數、點名，才是「不知道不等於沒事」的正確寫法。
要不要把驗算式當一組投票人（`_vote` 已有 `arith` 這一組的先例）接進去，
是會動到 `VRN_TitleTrim` 這支鎖住引擎的核心判斷的擴張，留給操作員決定。

---

## 2026-10-19 第六輪：Codex PR #73 的兩條 —— 一條是我的真漏洞，一條會把壞答案鎖起來

### 一（P2，接受並修掉）· 我的 P23 有一條前置濾網，放過的正是最該抓的

`def_time_scan` 第一版長這樣：

```python
if not TIME_YEARISH_RX.search(value):      # 值裡沒有連續四位數字 → 跳過
    continue
if TIME_OK_RX.match(value): ...
```

Codex 指出：`ReportDate=unknown`、`PageDate=09/15`、`FiscalQuarter=Q1`
這些非空、欄名在管、也不是結構值的值，全部沒有連續四位數字 → **被默默跳過，閘照報 PASS**。

**他說得對，而且實測比他舉的例子更糟**：這條濾網在 106 檔實測語料裡濾掉
**24564 筆** `vrn_financial_data.csv:PeriodType = FY` —— 一筆都沒驗過，閘卻一直是 PASS。
這跟「閘跑的那一刻和真正出事的那一刻不是同一刻」是同一家族的缺陷：
**我寫了一道閘，然後自己在它前面放了一張網。**

這個倉的語料裡民國年是常態（`華南投顧-2606-裕民-1141202.pdf`）。
`1141202` 有連續四位數字、擋得到；但 `114/12/02` 沒有 —— 它會從那張網的洞裡掉下去。

修法不是把網改小，是**拆掉**：非空、欄名在管、不是結構值，就一定要過 `TIME_OK_RX`。
`PeriodType` 這種「說的是時間的**種類**，不是時間值」的欄，改成**照欄名明講的例外**
（`TIME_ABOUT_WORDS = {type, kind, label, conflict, status}`，和 `TIME_WORDS` 共用同一套
切詞法 —— 切法只有一份），而且在閘的說明欄點名：

```
PASS · 合規 99084 筆（10 欄）
     · 原文欄不受規則管：period_raw（24480）、PeriodLabelRaw（24564）、period_raw（24480）
     · 欄名說的是時間的種類／狀態，不是時間值：DateConflict（0）、PeriodType（24564）
     · 結構不是時間值：PartialDates（2）
```

順手補上的是 `DateConflict`：它裝的是「檔名 X vs 首頁 Y」這種診斷句。
這一輪的語料它全是空的，所以濾網時代看不出問題 —— 但網一拆、而它沒被明確排除的話，
哪天真的有日期對不上，P23 就會為了一句診斷文字變紅。**那是潛伏的假紅燈，不是功能。**

測試照老規矩：四類加總必須等於非空值總數（`test_every_value_is_accounted_for`），
而且把濾網改回去跑過、確認 `114/12/02 / Q1 / unknown / 9/15 / 民國一一四年` 會從 PASS 變 FAIL。

### 二（P1，不接受 —— 實測證據反過來）· 「兩票就算對照成功」會鎖進分析師的名字

Codex 說：`g1=v, g2=v, g3=other` 時 `agree` 是 2，但 `_vote` 先走
`len(clusters) > 1` 那條，回 `CONFLICT`；這「牴觸了兩個來源相同即對照成功的規則」。

**事實部分他說得沒錯**，但那是這支引擎**本來就有**的判準（docstring 原文：
`VERIFIED: >= 2 groups agree and no voter disagrees`），不是這個 PR 改的；
這個 PR 只是把本來就算出來的 `agree` 記成一欄。`VRN_TitleTrim` 是 ENGINE_LOCKED，
那條判準有已知答案 151/151 的證明背著。

**要不要照他說的改？去看實測語料裡那三筆 2 比 1。** 三筆全是 `title.company`：

| 檔案 | 多數（標題＋首頁引擎） | 少數（檔名） |
|---|---|---|
| `凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf` | 賴偉中 | 慧洋 |
| `凱基投顧_2891 中信金_施志鴻_20260519.pdf` | 施志鴻 | 中信金 |
| `凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf` | 李承泰 | 貿聯 |

**多數讀到的是分析師的名字，少數讀到的才是公司。三比零，多數全錯。**

照 P1 改下去，這三筆會從「CONFLICT，要人看」變成「VERIFIED，上鎖」——
把分析師的姓名當成公司名鎖進帳本。59 檔個股報告裡的 3 檔，不是假想情境，是量出來的。

所以**沒有改**：路徑是真的（這類案例真的存在），但那個修法在真實資料上是淨損失。
「兩個以上相同即算對照成功」和「有人不同意就不算驗過」在 2 比 1 時會撞車，
要往哪邊倒是會動到輸出值、動到鎖住引擎核心判斷的決定 —— 那是操作員的決定，
不是寫碼的人單方面能承擔的。已在 PR 的那條 thread 上附實測表回覆。

要真的往多數倒，驗收標準先寫在這裡：
**那三筆的 `title.company` 必須是慧洋／中信金／貿聯，不是分析師姓名**；
做不到就表示該修的是「標題與首頁引擎為什麼把分析師讀成公司」，不是放寬對照門檻。

---

## 2026-10-19 第七輪：把分析師讀成公司 —— 修根因，不放寬門檻

操作員 2026-10-19，看完 Codex P1 那條 thread 後拍板：
**「多數讀到分析師是錯的 修那個 不要放寬門檻」**。

### 一、真相在標題原文裡

| 檔案 | 標題原文 | 原本讀到的公司 |
|---|---|---|
| `凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf` | `賴偉中(2637 TT) 營運動能延續，評價仍具吸引力` | 賴偉中 |
| `凱基投顧_2891 中信金_施志鴻_20260519.pdf` | `施志鴻(2891 TT) …` | 施志鴻 |
| `凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf` | `李承泰(3665 TT) …` | 李承泰 |
| `3653健策凱基投顧 向子慧 (3).txt` | `向子慧(3653 TT) …` | 向子慧 |

**第 4 筆原本沒人看見**：它是 SINGLE（`~`，只有一條讀法）而不是 CONFLICT，
所以不在那三筆紅字裡 —— 同一個缺陷，比較安靜的那一半。

同版型的對照組（`儒鴻(1476 TT)`、`頎邦`、`達發科技`、`宏致`）標題印的是真公司，
所以**不是版型問題，是「代號前面那一段就是公司」這條規則沒問過那一段是不是人**。

### 二、判斷放一處：分析師是誰本來就有人在算

`VRN_Evidence_Core` 已經同時有 `extract_analysts`（頁上）與 `filename_analysts`（檔名）。
公司名卻有**兩個讀法**各自取「代號前面那一段」：本檔的 `company_name_on_page`、
`VRN_TitleTrim` 的 `_company_before`。所以新規則只寫一份 —— `is_analyst_name` 放在
已經懂名字的那一支，兩個讀法都來問它：

```
VRN_Evidence_Core.is_analyst_name(name, analyst_names)   ← 唯一一份判斷
   ├─ company_name_on_page(..., analysts=…)              ← 首頁這一路
   └─ VRN_TitleTrim._is_analyst(name, ctx)               ← 標題這一路（借，不另寫姓氏表）
```

名單由 `analyze()` 一次算出（頁上 ∪ 檔名）、經首頁引擎 `analyst_names` 往上帶。

### 三、修的過程踩到四個坑，四個都量過

**坑 1：擋掉一個錯答案換來另一個錯答案。**
擋掉 `賴偉中` 之後 `company_name_on_page` 繼續往下掃，撿到代號表那一行
`'Bloomberg 2637 TT    Yahoo'`。代號該有公司名的位置印的是人，那就是「這一頁沒印公司」
—— 取到人名就到此為止，回 `None`，不繼續找。

**坑 2：`國光生` 從正確變成讀不到（真退步）。**
`filename_analysts` 的規則是「2-3 個中文字、第一個字在姓氏冊裡」，
而 `國光生`、`全台` 照字面就符合。原本只是名單裡多幾個人名、沒人消費；
一旦拿它去**擋**公司名，誤判就變成真損失。

分辨方法不用新知識：**公司名緊挨著自己的代號**（`國光生(4142,Note)`、`2637 慧洋`），
分析師離得遠。所以貼著代號的那一段不算分析師；代號那一段自己就含中文
（`3653健策凱基投顧`）時公司已經在裡面，旁邊那一段照算。
實測 106 檔檔名：只少掉 `國光生` 與 `全台`×2 這 3 筆誤判，分析師一個沒丟。

**坑 3：G18 鎖擋下連帶退步。**
`賴偉中` 不再是公司之後，它的字也就沒被標成「用掉了」，於是漏進核心觀點：
`營運動能延續,評價仍具吸引力` → `賴偉中, 營運動能延續,評價仍具吸引力`，三檔 BROKEN。
認出它是人名之後那一段**還是用掉了** —— 標題確實印了這幾個字，也知道它是什麼。
**這一個不是我自己看出來的，是鎖擋下來的。**

**坑 4：函式會了，那條路沒走到。**
`analyst_names` 算好了、首頁引擎也傳了，但 `FPE_KEYS_FOR_TRIM`（G17 能看到的首頁欄位白名單）
沒放它，標題那一路照舊讀成分析師。單元測試全過、實測照錯 ——
「驗了函式不等於驗了那條路」。測試因此直接拿 `VRN_TitleTrim` 讀的欄位去對白名單。

另外 `.txt` 那一檔沒有首頁引擎結果，名單是空的（PDF 三檔修好了，它沒有）。
檔名那一半本來就算得出來，所以 `report_context` 自己補算一次 ——
同一支函式兩個呼叫端，不是兩顆頭。

### 四、刻意沒做：不拿檔名頂上

擋掉人名之後**不**把檔名的答案填進「標題」這一票。填了的話標題這一票的值其實來自檔名，
而 `_vote` 數的是群組數 —— 標題＋檔名就變成「兩個來源一致」，**一個來源假裝成兩個**。
同一條線我在 Codex P1 那條 thread 上拒絕過，自己這邊也不能做。
標題沒印公司就是沒印，照實 `NOT_PRINTED`。

### 五、實測結果（106 檔，`--no-cache`）

```
公司部位      修前 ✓55 / ✗3(CONFLICT) / ~1   →   修後 ✓55 / ~3(SINGLE) / !1(MISSING)
              三筆 CONFLICT 的值從 賴偉中／施志鴻／李承泰 變成 慧洋／中信金／貿聯
P21 驗收      54/59 → 56/59 份 100% 過關
待修擋住收尾   5 項 → 3 項
G18 鎖        BROKEN 0 · HELD 1310（修坑 3 之前是 BROKEN 3）
已知答案       titletrim 151/151 · first_page_oracle 全過（lock 重新驗過）
首頁公司名     98 檔 PDF：95 檔一字未動，3 檔從分析師變成「沒印」
測試          425 案（VRN/VDF/artifacts）+ 423 案（治理）全過
```

**為什麼是 +2 而不是 +3**：`.txt` 那一檔從 SINGLE 變成 MISSING，P21 少算一份。
那不是退步 —— 它原本帶著錯的公司名（向子慧）卻照樣算「100% 過關」，
P21 在把一個錯答案數成過關。現在它誠實地不算。

### 六、剩下那一筆：`3653健策凱基投顧 向子慧 (3).txt`（說清楚界線）

這一檔的公司 `健策` **在報告正文裡出現 0 次** —— 整份文件從來沒印過它，
只存在於檔名，而且和代號黏在一起：`3653健策凱基投顧`。
所以 MISSING 是**事實正確**的狀態，不是讀漏。

要救回來得讓檔名拆解看出 `3653` + `健策` + `凱基投顧` 三段的邊界。
公司名那一段由母倉 `VRN_ENG396_ReportEntities`（MIRROR_MOTHER，逐位元組，不能改）認；
VRN 這邊已經有一個 workaround（把代號前後補下底線讓它看見邊界），
再往下就要用券商別名冊去剝尾巴 —— 那是**一條新的檔名解析規則**，
而這種「代號＋公司＋券商全黏在一起」的檔名在 106 檔語料裡只有 1 檔。

**沒有做。** 為 1 檔去動所有檔名的拆解規則，風險不該由寫碼的人單方面承擔。
要做的驗收標準先寫在這裡：**那一檔的 `title.company` 要是 健策，
而且另外 105 檔的 `company_names` 一個字不差。**

---

## 2026-10-20 第八輪：把最後 3 筆補到 59/59（補的是讀法與分類，不是編值）

操作員 2026-10-20：「把那 3 筆缺的補到 100% 過關　可參考 VRN-2 的工具邏輯內容」。

三筆：`3014TT-20231005.pdf`、`6933_AMAX-KY_個股介紹報告.pdf` 的 `cover.broker` MISSING，
`3653健策凱基投顧 向子慧 (3).txt` 的 `title.company` MISSING。

**參考不等於依賴**：VRN-2 側的欄位規則樞紐
（`supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub`）讀過了 ——
它的 `broker_of` 自己不比對，委派單一正本實作，證據不足就回 `None`，
而且用受評公司名當否決詞（和我上一輪修的「分析師不是公司」是同一家族）。
**那套作法照抄進 VRN-1 自己的引擎，執行期不呼叫它** ——
四個系統互不干涉，這一條沒有因為「可以參考」就鬆掉。

### 一、兩筆券商：量過才知道「不是讀漏，是沒印」

先用自己發明的機構字正則掃，兩檔都「有機構字」—— **那是量錯的**。
汙染源是 `analyst@example-research.com` 裡的 `research`，而冊上
`broker_alias_rule_r6` 明文寫著「e-mail／網址裡的字不算」。
照冊上的規則先清掉 e-mail 與網址，再用冊上**已經有的** `cover.broker_context_rx`
（`securities|sec\b|investment|research|financial|capital markets|證券|投顧|投信|金控|證期|期貨|資本|永昌`）
重量，59 檔分得一清二楚：

| `cover.broker` | 清過 e-mail 後有機構字 | `broker_evidence` 讀到 | 檔數 |
|---|---|---|---|
| VERIFIED | 有 | 有 | 50 |
| VERIFIED | 沒有 | 沒有 | 7（華南 Memo，券商在**檔名**裡） |
| MISSING | 沒有 | 沒有 | **2** |

那兩檔：首頁 1159 行零券商別名、零機構字、網域 `example-research.com` 不在網域冊、
檔名也沒有券商。**唯一能「補」的方式就是編一個出來** —— 那不做。

做的是改分類。冊上本來就有三條同形的例外：
`short_report_rule`（短評沒評等與目標價）、`nr_rule`（未評等沒目標價）、
`tp_declared_none_rule`（寫明 n.a.）—— 都是「報告沒印就是 NOT_PRINTED，不是 MISSING」。
`cover.broker` 的 expected 原本一律 True，所以沒有第四條。這一版補上，判準同樣來自冊。

**這不是放寬讀券商的門檻**：讀法一條都沒動，變的只是「讀不到」記成哪一種。
守門寫成測試：**首頁有機構字卻讀不到 → 照舊 MISSING**（那是真缺陷，要紅）。
那一格在這份語料裡是 0 檔，所以閘以前從來不必分這兩種。
把例外改成無條件（也就是真的放寬門檻）那一版，測試會紅 —— 三個方向都先證過。

### 二、第三筆：公司名黏在檔名裡，邊界由 VRN 開、名字由母倉認

`3653健策凱基投顧 向子慧 (3).txt`：`健策` 在正文出現 **0 次**，只在檔名，
而且代號＋公司＋券商三段之間一個分隔符都沒有。

`VRN_ENG396_ReportEntities` 是 MIRROR_MOTHER（逐位元組，不能改），它要看得到邊界才認得公司名。
`decompose` 裡**本來就有同一招**的 workaround（`2330台積電` → 補成 `_2330_台積電`）。
這一版只是把券商那一邊也切開，切點由 VRN 自己的券商別名冊說：

```
3653健策凱基投顧 向子慧 (3)   → ENG396 回 []
_3653_健策凱基投顧 向子慧 (3) → ENG396 回 []        （舊 workaround 不夠）
_3653_健策_凱基投顧 向子慧 (3) → ENG396 回 ['健策']   ← 這一版
```

**公司名是 ENG396 認的，不是我剝字串剝出來的** —— `_split_glued_broker` 只回一個
「補了分隔符的檔名」，認不認得還是母倉說。三道守門：token 要以**這份報告的代號**開頭、
剩下那段要以冊上的中文別名結尾、切完兩邊都不能空。
實測語料裡另外三個「長得像」的 token（`6533,N,中立`、`2026年投資大趨勢`、`2026海外投資展望`）
在這三道守門前就被擋掉；106 檔檔名只有 1 檔的 `company_names` 變了，105 檔一字未動。

### 三、實測（106 檔，`--no-cache`）

```
驗收 P21      56/59 → 59/59 份 100% 過關（WARN → PASS）
G00 LOCK      待修 69 項（擋住收尾 3 項）→ 67 項（擋住收尾 0 項）（WARN → PASS）
P14 REGIONS   冊 8/8 → 9/9（券商冊接進來了）
公司部位       ✓55 / ~3 / !1  →  ✓55 / ~4   （MISSING 清零；~ 是單一來源，值正確）
券商部位       ✓57 / !2  →  ✓57 / –2        （– 是「報告沒印」）
run           AMBER · FAIL=0 · 收尾完成
已知答案       titletrim 151/151 · regions 4/4 · 全組 PASS（lock 重新驗過）
測試          430 案（VRN/VDF/artifacts）+ 423 案（治理）全過
```

少掉的兩列（`P20 CACHE`／`P20 TIME`）是 `--no-cache` 才沒有的快取統計，不是閘消失。

### 四、剩下的 WARN 是什麼（說清楚，不含糊）

59/59 之後 `run` 還是 AMBER，因為 WARN 不等於錯：
本機資料庫 ABSENT、`.docx`／`.txt` 的截取完整度未達 99.9%（第四輪那個 ENG394 缺口）、
加速器沒掛（這台容器沒有）、以及待修清單上剩的 67 項全是 **優先 3（SINGLE：只有一條讀法，
鎖不住，不是讀錯）**。擋住收尾的項數是 **0**。

---

## 2026-10-20 第九輪：Codex PR #74 兩條，兩條都成立；而 P1 的答案是操作員給的

### 一（P2，接受）· 別名要取「引擎組好的那張表」，不是生冊

Codex：`broker_aliases()` 只讀每筆記錄的 `aliases` 陣列，把 canonical key 丟掉了；
生冊 v0100 有這種記錄，`3653健策華南投顧.txt` 照樣切不開。

**查證成立**：v0100 有 10 筆（華南、日盛、統一、大華、合庫、康和、宏遠、麥格理、里昂、摩根士丹利）
的 key 本身就是中文名、底下沒有 `aliases`。

但**他建議的修法單獨做救不了他自己舉的例子** —— 生冊的 key 是 `華南`，
而 `3653健策華南投顧` 的尾巴是 `華南投顧`。真正解決的是**換表**：改用首頁引擎真正在用的
`BrokerRatingDict.b`（60 → 128 個中文名），那裡 `華南投顧` 是 `HUANAN` 這一筆的 alias。
實測 `3653健策華南投顧.txt` → `['健策']`，106 檔回歸仍只有 1 檔變。

順帶兩件誠實的事：
`+ [canon]` 留著但**今天一個名字都沒多加**（組好的表 key 全是英文），註解照實寫；
另外加了 `_glued_token` 這個便宜的形狀檢查擋在前面 —— 別名表要載首頁引擎才拿得到，
不能每個檔都載（實測 106 檔裡只有 4 檔問得到）。

### 二（P1，接受；判準由操作員給）· 「沒印」要照券商名該在的四個位置判

Codex：「首頁沒有機構字就算沒印券商」會把**報告印了不認得的券商名**（`Jefferies`，
後面沒接 Securities）也判成沒印 —— 把字典缺口當成合法缺席，把完成度灌水。**他說得對。**

我先去找乾淨的分界線，沒找到：98 檔 PDF **共用同一個 e-mail 網域** `analyst@example-research.com`
（GS、MS、凱基、華南…全都一樣），而且**沒有任何一檔有免責／版權聲明**。
那兩檔跟「真報告印了我不認得的券商」在檔案內部長得一模一樣。我把兩條路攤開問操作員。

**操作員給的不是選項，是知識**：
> 「券商名收穫縮寫同義字等一定位在 FILENAME 首頁 各頁下方小字體頁尾 或是報告後方小字體附錄等」

照這四個位置重量，答案立刻清楚 —— 而且發現 VRN **本來就把券商名抽出來了卻丟掉**：

```
20250819兆豐個股報告-泓德能源(6873).pdf  跨頁重複帶 = 兆豐證券投資顧問MEGA Securities Research
GS-1590 20251203.pdf                 跨頁重複帶 = 大華證券投資顧問GS Securities Research
3014TT-20231005.pdf                  跨頁重複帶 = 測試公司(3014 TT)營運動能延續…（只有標題行）
6933_AMAX-KY_個股介紹報告.pdf            跨頁重複帶 = 個股介紹報告(6933 TT)營運動能延續…（只有標題行）
```

G15 早就把各頁頁眉／頁尾抽成 `excluded`（理由寫「跨頁重複(出現在 40/40 頁)」），
裡面就是發行機構帶。所以判準不用詞表，用**結構**：

> 跨頁重複帶裡只要有「不是本報告標題」的文字 → 發行機構帶存在而我們沒讀到 → **維持 MISSING**。

`Jefferies` 會落在這一格（它會出現在那一帶），Codex 的路徑就此堵死；
檔名／首頁／後方小字附錄這三個散文位置照舊用冊上的 `cover.broker_context_rx` 判機構字。

實測 59 檔個股報告：

| cover.broker | 有「非標題」的跨頁重複帶 | 檔數 |
|---|---|---|
| VERIFIED | 有 | 49 |
| VERIFIED | 沒有（`.docx`／`.txt` 沒有重複帶，券商在檔名） | 8 |
| NOT_PRINTED | 沒有 | **2** |

這比我原本那條（只看首頁機構字）嚴得多，而 59/59 仍然成立。

### 三、這一輪學到的

**兩次量錯都出在「我自己發明判準」**：第一次用自己寫的機構字正則（被 e-mail 裡的 research 汙染），
第二次把範圍限在首頁（而券商名在頁尾那一帶）。
兩次的修正都來自**系統或操作員已經有的東西** —— 冊上的 `broker_context_rx`、
G15 已經抽好的 `excluded` 帶、操作員口述的四個位置。
自己發明判準之前，先問這個系統是不是已經知道答案。

---

## 2026-10-20 第十輪：現價被**鄰欄的目標價**誤殺 —— 59/59 全軍覆沒，而守門是對的那半邊

### 一、線索：同一行、同一套讀法，一個讀到一個沒讀到

上一輪收尾後待修清單剩 67 項、全是優先 3（SINGLE）。按部位攤開：

```
cover.current_price 59 · title.company 4 · cover.tel 1 · title.core_view 1 · title.market 1 · title.text 1
```

`cover.current_price` 在 **59 份個股報告裡全部** 只有「首頁引擎」一個來源，永遠湊不到第二票，
所以永遠鎖不住。而同一行印的是：

```
投資評等：賣出    目標價：NT$182.5    收盤價：NT$140.4
```

**目標價 VERIFIED、收盤價 SINGLE。** 同一行、同一套讀法，一個讀到一個沒讀到 —— 這個不對稱就是缺陷。

### 二、第一次量錯（記在這裡，因為原因很常見）

第一次探針我拿**未經 TRIM** 的原字串去掃守門視窗，看到「前 14 字」是 `價：NT$182.5    `，
沒有 `目標`，於是判定守門沒開火、往別處找。

錯在：引擎讀的不是原字串，是 **TRIM 過的** `clean`。TRIM 會把連續空白收成一個空白：

```
原印： '投資評等：賣出    目標價：NT$182.5    收盤價：NT$140.4'
TRIM： '投資評等:賣出 目標價:NT$182.5 收盤價:NT$140.4'
```

一收，`收盤價` 從第 27 個字挪到第 21 個字，前 14 字變成 `' 目標價:nt$182.5 '` —— `目標` 就在裡面。
**量的時候要量引擎真正看到的那個字串。**

### 三、根因：守門的兩側不是同一把尺

冊上 `current_price_rule`：「現價標籤前後 14 字內有 target／目標／12M 的不是現價」，
`current_price_rule_r6` 再補一條「52 週股價 (低 \ 高) 是一年區間」。規則本身沒錯，
錯的是兩側的寫法不一致：

| 側 | 寫法 | 效果 |
|---|---|---|
| 標籤**後** | `rx.match(after)` | **錨定**：那個字要緊接著標籤 |
| 標籤**前** | `rx.search(before)` | **不錨定**：14 字裡任何一處都算 |

冊上自己舉的兩個例子（`12M price target NT$4,200`、`52 週股價 (低 \ 高)`），
那個字都是**緊貼著標籤**的。所以「相鄰」才是冊的本意，14 字只是容錯寬度。
前側不錨定，等於讓**前一欄自己的標籤和數字**跑進來投反對票。

修法：前側改成和後側同一把尺 —— 字要**收在標籤前**（中間只容得下分隔符號）。
`engine/VRN_TitleTrim_v0100.py#_cp_qualified`，冊上 `current_price_rule` 同步改寫、新增 `current_price_rule_r7`。
**門檻一個字都沒放寬**：`current_price_not_near_rx` 那串字原封不動。

### 四、改之前先量完整個語料（106 檔）

把守門換成相鄰版，逐檔比對前後：

| 結果 | 檔數 |
|---|---|
| 讀出來的現價不變 | 47 |
| 從「讀不到」變成「讀到」 | **59** |
| 從某個值變成**另一個**值 | **0** |

沒有任何一檔的值被改掉，只有本來空的被填上。再把 59 個新值拿**未經 TRIM 的原頁字串**
用另一支正則獨立核對：**59/59 與紙面相符、0 筆不符**。

再把「舊守門開火、新守門不開火」的所有位置列出來當回歸面 —— 全語料只有 **59 種樣式，全部是同一種**：
`目標價:NT$XXX ` 擋在 `收盤價` 前面。冊上自己的例子逐條驗過，照樣擋：

```
12M price target NT$4,200        舊擋 新擋
12M target price NT$200          舊擋 新擋
52 週股價 (低 \ 高) (NT$): …      舊擋 新擋
52-week price range: …           舊擋 新擋
12-month price objective NT$600  舊擋 新擋
投資評等:賣出 目標價:… 收盤價:…   舊擋 新讀   ← 只有這一種變
```

### 五、為什麼鎖了這麼多輪都沒抓到：已知答案沒走過這條路

`build_fixtures` 原本 8 份已知答案，評等框**每個欄位各佔一行**：

```
投資評等：買進
目標價：ＮＴ＄１，２００
收盤價：NT$1,000
```

一行一欄，前一欄不會擠進 14 字窗 —— 所以這條路 lock 從來沒走過。
而真實語料 **59/59 全是一行三欄**。

**補第 9 份已知答案**（`20260518兆豐個股報告-聯詠(3034).pdf`），評等框照真實版型印成一行。
在沒修的引擎上，這份已知答案的 `cover.current_price` 會紅：

```
[FAIL] 20260518兆豐個股報告-聯詠( · cover.current_price · 要 140.4 得 None
[TITLETRIM] 162/163
```

修好以後 163/163。**在壞的版本上也會過的測試等於沒有測試** —— 新增的 7 條單元測試
（`def_CloseNextToTargetTests`）同樣逐一還原驗過：壞版本上 4 條紅，
另外 3 條是護欄（兩個版本都要綠，證明門檻沒被放寬）。

順手把兩個檔裡寫死的 `8`（樣本份數）改成跟著 `build_fixtures` 走 ——
寫死的數字就是第三處知道同一件事的地方。

### 六、實測（106 檔真實報告）

| | 修前 | 修後 |
|---|---|---|
| 部位 VERIFIED | 1310 | **1369**（+59） |
| 部位 SINGLE | 67 | **8** |
| 待修 優先 0/1/2/3 | 0/0/0/67 | 0/0/0/**8** |
| P24 兩個以上來源對上 | 640 | **699** |
| 每檔逐項驗收 | 59/59 過關 | 59/59 過關 |
| 燈號 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 | 同 |

矩陣上那一欄從 `~`（只有一條讀法）整排變成 `✓`：**現價 ✓59**，CONFLICT 0 筆。

剩下的 8 項：`title.company` 4、`cover.tel` 1、`title.core_view` 1、`title.market` 1、`title.text` 1 ——
全是優先 3（只有一條讀法、鎖不住，不是讀錯）。

**一次量錯要記下來**：冷快取那一輪 WARN=20，比基準多一條。
查下去是 `P09 ACCEL` 的「動作清單」多列了一條（這一輪跑了 G19 子行程那條道），
加速器在這台機器上沒掛，所以每一條都是 WARN。
快取熱起來以後 **WARN=19，和基準一字不差**。
**燈號對不上就要查到底，不能說「大概是環境」。**

### 七、這一輪學到的

**守門的兩側要用同一把尺。** 一邊錨定、一邊不錨定，看起來只是寫法差異，
實際上是兩條不同的規則 —— 而冊上只寫了一條。寬的那一側遲早會吃到鄰居的字。

**已知答案的版型要蓋到真實語料的版型。** 8 份已知答案全部用「一欄一行」，
真實語料 59/59 用「一行三欄」—— 函式驗過了，那條路沒驗過。
**驗了函式不等於驗了那條路。**

### 八、Codex PR #75 P2（成立，是我這一輪自己打進去的退步）

> `Target-Price NT$4,200` / `Target (Price): NT$4,200` 這類，分隔符號不在列舉裡，
> 守門就不開火 —— 目標價會被當成現價讀進來。

**實測，三個都重現**（而且 `main` 上三個都是 `None`，確定是我打進去的）：

```
修前（main）                       修後（第一版）                     再修（這一版）
Target-Price NT$4,200     None  →  current_price 4200  ✗  →  None ✓
Target (Price): NT$4,200  None  →  current_price 4200  ✗  →  None ✓
12M-Price NT$4,200        None  →  current_price 4200  ✗  →  None ✓
52週-股價 318              None  →  current_price  318  ✗  →  None ✓
```

錯在我把「緊鄰」實作成 `rstrip(" :：)")` —— **列舉分隔符號**。列舉一定會漏。
改成問一句話：**那個字和標籤中間，還有沒有字母、數字、漢字？** 沒有就是緊鄰。
這把尺系統裡已經有了（`_bare_text`，判「這一帶是不是標題行」用的同一把），直接借，不另寫一條。

順手把**標籤後面**那側也換成同一把尺。原本 `Price-Target NT$4,200` 取不到值，
是因為取值那一段剛好湊不出數字，**不是守門擋的** —— 現在是守門擋的。

語料回歸：106 檔，這一版與上一版**一檔都沒差**（修的是列舉漏掉的形狀，語料裡沒有這種形狀）；
對 `main` 仍然是 59 筆 `None → 值`、0 筆值被改掉。
新增 2 條測試，第一條在上一版上會紅（`AssertionError: 4200.0 is not None : Target-Price NT$4,200`）。

**這一輪第三次量錯，三次都是同一種**：自己發明判準（機構字正則、首頁範圍、列舉分隔符號），
而系統裡本來就有一把量好的尺。

---

## 2026-10-20 第十一輪：代號紀錄只問了一條讀法 —— 而紙上印著的碼被記成「沒讀到」

### 一、先把上一條線索查死：七條恆等式的 SKIP 是誠實的

這一輪開場，內層 7 個 SKIP 全是財報恆等式，6141 個桶全 `INSUFFICIENT`。
文件 2026-10-19 那一則寫著「七條恆等式現在真的在 174 個桶上跑 —— 1,218 次從來沒做過的驗算」，
說法對不上，所以先查。

語料的財報表只印四列：

```
項目 (NT$ 百萬元) | 2024A | 2025E | 2026E
營收 · 毛利率(%) · 稅後淨利 · 每股盈餘(元)
```

七條恆等式要的運算元（營業成本、毛利、營業費用、資產、負債、權益、流通股數）**紙上一個都沒有**。
`INSUFFICIENT` 是對的。那一則講的是「財務表補齊後」的語料，那份語料已經不在了。
恆等式本身的回歸測試在 `tests/test_VRN_BookCheck.py`，照舊有效。
**結論：不是缺陷，不動。**（查這一條花的時間不算浪費 —— 文件和實測對不上就得查到底。）

### 二、真缺陷在代號紀錄：一整欄永遠鎖不住，還藏了一筆 MISSING

`vrn_ticker_record.csv` 的 15 欄狀態攤開來看：

```
yfinance_ticker_state    SINGLE 58 · MISSING 1
bloomberg_ticker_state   SINGLE 58 · DERIVED 1
```

兩整欄 **59 份報告裡一筆 VERIFIED 都沒有** —— 和上一輪的現價同一個形狀。

而首頁明明印著：

```
報告日期：2025/08/19    Bloomberg 6873 TT    Yahoo 6873.TW
```

根因：`record_of` 只問**首頁引擎**一條讀法（`fpe["page_codes"]`）。
TRIM 那一側其實也讀到了同一批碼 —— `title.market` 的「首頁 Yahoo 代碼（TRIM）」就是從
`_ticker_hits` 來的 —— 但 `cover_fields` 只留下市場別，碼本身沒交出去。
一個讀者 ⇒ 永遠 SINGLE。

更糟的是沒有首頁引擎結果的檔（`3653健策凱基投顧 向子慧 (3).txt`，.txt 不走首頁引擎）：

| | 紙上第 3 行 | 舊紀錄 |
|---|---|---|
| yfinance | `Yahoo 3653.TW` | `''` **MISSING** |
| bloomberg | `Bloomberg 3653 TT` | `3653 TT` **DERIVED（推的）** |

印著的碼記成「沒讀到」，印著的碼記成「推算出來的」。**兩筆都是錯的值／錯的來源。**

### 三、修法：把已經讀到的交出去，不新寫讀法

- `cover_fields` 把 `page_hits` 裡的平台碼**照首頁引擎自己的形狀**（`raw / core / platform / market`）
  交出來，市場別仍走冊上的 `market_of_form`，不另造一套對映。
- `record_of` 兩條讀法一起看：一致 = `VERIFIED`、不一致 = `CONFLICT`、只有一條 = `SINGLE`；
  **紙上沒印才輪到推算**（`DERIVED`），原本的退路一個字沒變。

沒有新的解析、沒有新的詞表、沒有放寬任何門檻 —— 只是把 TRIM 本來就讀到的東西接上。

### 四、第二件事：守門只看兩欄，所以那筆 MISSING 沒人看見

G20 的守門是：

```python
missing = [... for k in ("ticker", "name") if r.get(k + "_state") == "MISSING"]
```

**15 欄裡只看 2 欄。** 所以 `yfinance_ticker` 記成 MISSING 了，閘上那一列只印出
「VERIFIED 15 · MISSING 1」的總數，沒有人被點名，待修清單 8 項裡一項都沒有它，
驗收照樣 59/59 過關。改成 15 欄都看，而且 `CONFLICT` 也要喊（比 MISSING 更嚴重，原本完全沒查）。

### 五、實測（106 檔真實報告）

| | 修前 | 修後 |
|---|---|---|
| `yfinance_ticker_state` | SINGLE 58 · **MISSING 1** | **VERIFIED 58** · SINGLE 1 |
| `bloomberg_ticker_state` | SINGLE 58 · **DERIVED 1** | **VERIFIED 58** · SINGLE 1 |
| 值被改掉的列 | — | **1 筆**（`.txt` 的 yfinance `'' → 3653.TW`，就是紙上印的那個） |
| 其他 13 欄 | — | **一格都沒變** |
| 燈號 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 | **同** |
| 內層 | PASS=318 WARN=7 SKIP=7 FAIL=0 | **同** |
| 驗收 | 59/59 | 59/59 |

剩下那 1 筆 SINGLE 就是那個 .txt：沒有首頁引擎結果，只有 TRIM 一條讀法 —— 照實記 SINGLE，不灌成 VERIFIED。

### 六、測試（每一條都在壞版本上紅過）

- `VRN_TickerRecord.selftest` 加 3 條已知答案（兩條一致 = VERIFIED／只有 TRIM = SINGLE 且來源是「印的」／不一致 = CONFLICT）：
  舊 `record_of` 上 **15/18**。
- `tests/test_VRN_TickerRecord.py` 加 4 條：舊碼紅 3 條，第 4 條是護欄（兩邊都沒印 → 照舊 DERIVED／MISSING）。
- `tests/test_VRN_TitleTrim.py` 加一組**走整條路**的：`cover_fields → record_of`，
  並且把「TitleTrim 交出的鍵 = 代號紀錄讀的鍵」釘住 —— `FPE_KEYS_FOR_TRIM` 那次就是栽在鍵沒接上。
- `tests/test_VRN_AutoTestLoop.py` 加一條：G20 守門要看滿 15 欄、要喊 CONFLICT；舊守門上紅。

### 七、這一輪學到的

**一整欄都是 SINGLE，就是一條讀法掉了，不是報告沒印。**
上一輪的現價是這個形狀，這一輪的 YF／Bloomberg 代號也是。
下次看矩陣先掃「有沒有哪一欄從頭到尾沒有 VERIFIED」——那比單點的 CONFLICT 更值得查。

**守門的範圍要跟著輸出走。** 紀錄從 2 欄長成 15 欄，守門還停在 2 欄，
那 13 欄就等於沒有守門 —— 數字印在總表上（「MISSING 1」），但沒有人被點名，等於沒說。

### 八、Codex PR #76 兩條 P2，兩條都成立（都是我這一輪自己打進去的）

**P2-A 資料庫把「兩條讀法互相不一致」蓋掉了。** 我寫的是

```python
agree = any(fold_text(v) == fold_text(listing["yfinance_ticker"]) for _w, v in yf_reads)
```

資料庫 `2330.TW`、首頁引擎 `2330.TW`、TRIM `2330.TWO` → `any` 成立 → `VERIFIED`。
**而 CONFLICT 正是我這一輪才加進來、而且剛要求 G20 喊出來的那一種。** 實測重現，改成先看兩條讀法有沒有打架：
打架就 CONFLICT，資料庫不當和事佬；兩條一致時資料庫照舊是第三個佐證。

**P2-B 括號裡的碼沒被收進第二條讀法。** `鴻海 (2317.TW)`、`TSMC (2330 TT)` 這種
「整頁唯一印的碼就在括號裡」，`_ticker_hits` 會先用 `paren_rx` 吃掉它、壓住後面重疊的
yahoo／bloomberg 比對，`how` 停在 `"paren"`，我的篩選就整個漏掉 —— 代號紀錄還是只有一條讀法。

```
'鴻海 (2317.TW) 法說會摘要'      修前 []  →  修後 [('yfinance', '2317.TW', 'TWSE')]
'TSMC (2330 TT) 先進製程'        修前 []  →  修後 [('bloomberg', '2330 TT', '')]
'國光生(4142,Note)-CTBC'         修前 []  →  修後 []       ← 不是平台碼，照樣不收
'慧洋-KY(2637-KY) 速報'          修前 []  →  修後 []
```

**認不認得不自己列表**：把括號內容拿去問冊上同一組 `yahoo_rx` / `bbg_rx`。
（上一輪的教訓就是「列舉一定會漏」，這裡直接不列舉。）

語料回歸：106 檔，整張代號紀錄與上一版**一格都沒差**（這兩種形狀語料裡沒有，資料庫也不在），
燈號與驗收同基準。新增 2 條已知答案（TitleTrim 164/164、Record 19/19）與 3 條單元測試，
在上一版上分別紅 1 條、紅 1 條、紅 2 條。

## 2026-10-20 第十二輪：操作員「VRN-1 自動修正直到100%正確 輸出驗證後的OUTPUT及HTML U/I」

### 一、新的一道閘：G21 驗證過的輸出（`engine/VRN_OutputVerify_v0100.py`，VRN-ENG021）

G16 寫出 DataFrame 之後，**每一筆**回原檔逐欄證明，證不出來的不進輸出：

```
原檔（不是聚焦副本）→ pypdfium2 取字元座標自己排行（VRN-1 的擷取走 pdfplumber / PyMuPDF，這裡換一條讀法）
  → 科目那一列 → 科目後面那一段數字（並排表遇到下一個科目字就停；「(1.4)ppts」這種黏單位的格算在這一段裡）
  → 值那一列正上方最近的期間表頭 → 用 x 座標把值對到表頭那一欄
  → 分組表頭（期間底下有 修正後 / 修正前 / 差異 …）：值要落在那一組「本次」那個子欄
  → 那一欄的期間 = 這一列寫的年 / 季，才算證實
```

* 能從原檔確定的才**自動修正**（期間 · 值 · 子欄），改完**再證一次**；證不出來的寫進剔除冊、附理由。
* 輸出：`<round>/verified/` 底下 `vrn_verified_financial_data` · `vrn_verified_annual_cells` · `vrn_verified_ticker_record` ·
  `vrn_verified_summary_points` · `vrn_output_corrections`（前 → 後）· `vrn_output_rejected`（CSV + Parquet）·
  `VRN_Verified_Output_v0100.html`（分頁、檔案篩選、搜尋、換頁、深色模式、手機寬不左右捲）。
* 主報告多一行 `G00 VERIFIED`、多一節「驗證過的輸出」連到那一頁；`lock` 的已知答案多一組 `outputverify`（14 項）。
* 一份投影片轉的 PDF 字元框會重疊（台新：排出來是「報報報 用」），電話 / 電郵 / 重點句另拿 pypdfium2 的內容流文字再對一次 ——
  仍是原檔的字，只是第二種讀法。

### 二、量到的根因（倉內 19 份真報告，逐筆回原檔）

| # | 現象（實檔） | 根因 | 修在哪 |
|---|---|---|---|
| 1 | 晶心科 電話 `02220232024`；慧洋 電話 `09251125012` | 首頁引擎的電話 regex 從別的數字中間開始、跨行；表頭「2022 2023 2024」、走勢圖軸「09-25 11-25 01-26」都讀成電話 | `VIA_VRN_FirstPageEngine.FieldValidation`：不從數字中間開始、不跨行，區碼之後每段至少 3 碼 |
| 2 | MS 2308 / 3661 的標題是 `+886 2 2730-2865 - Samantha Chen`；CLSA 的標題接著電話 | 電話裡的四碼被當成代號（+4 分）；聯絡資訊行沒有被排除 | `VRN_TitleTrim`：電話範圍內的數字不算代號；有電話 / 電郵的行不是標題、標題也不接它 |
| 3 | 瑞基 標題 `未評等瑞基(4171 TT)` | 同一列的字依「底邊四捨五入」排，右邊的「未評等」排到左邊 | `page_lines` 依 x 由左到右；標題同列同字級的字照左到右併成一行（`瑞基(4171 TT) 未評等`） |
| 4 | MS 標題只讀到上半行 | 兩行標題中間夾著右欄分析師欄的字 | 接下一行時跳過另一欄（x 不重疊）的字 |
| 5 | JPM 標題 `tsmc(2330TW)-JPM-250718`；改了之後一度變成 `Overweight - 2330.TW, 2330 TT - Price …` | PDF 屬性 Title 是檔名；代號欄那一行分數贏過公司名 | 屬性 Title 結尾是 6/8 碼日期戳 = 檔名（`metadata_junk_rx`）；只有代號的行不加代號分；以評等 / 價格標籤起頭的行不接進標題 |
| 6 | CLST 34 筆「期間 T / 空白」、值是半截（`,744`、`9`） | 兩張圖表上下疊、共用欄線，被抽成一張表；欄線把字切開（`2025C`|`T` · `220`|`,744` · `2`|`Q25`） | `VRN_Integrated_ReportDatabase_Engine`：資料列之後又出現期別表頭 → 下一張表；表頭兩格接起來才是期別 → 那兩欄整欄接回 |
| 7 | 凱基 3665 第 2 頁：1Q26 營收讀成 23,224（其實是 2Q26F 修正後）、2Q26F 讀成 2.6（調幅） | 分組表頭各期間底下子欄數不同（1Q26：實際數 / 凱基預估 / 差異 …；2Q26F：修正後 / 修正前 / 調幅 …；2028F 只有凱基預估），舊法「子欄數 ÷ 期間數」平均切 | `VRN_Evidence_Core._subcolumns`：子欄從左到右切成連續的組，每組左右中點對準它的期間字（逐組累加的表求最小偏差）；每組自己的「本次」欄：修正後 > 實際數 > 自家預估 |
| 8 | CLST 期初現金 4 格「驗過」，靠的是資料庫引擎把「Opening cash 23,169」歸成 **OperatingProfit** | 舊的子字串歸類（op…）；這一輪改成整字比對後那一列消失，期初現金掉回 SINGLE | 資料庫引擎加 `CashBegin` / `CashEnd`（標籤取自 `VRN_FinIdentity_SSOT` cash_begin / cash_end，加 Opening / Closing cash）—— 第二條讀法回來，而且科目對 |
| 9 | CLSA 標題只讀到「Wiwynn」、JPM 只讀到「TSMC」，核心觀點變成公司名 | 最大字那一行只有公司名，標題在下面同一欄（中間夾評等價格行）；凱基「慧洋-KY」用掉公司名後剩「-KY」 | 公司名單獨一行 → 接下面同一欄、比內文大的那一行（評等價格行跳過）；首頁引擎讀到的公司名在標題裡算「用掉」（不當標題那一票）；`-KY` 不進核心觀點；首頁引擎最大字是同一列兩欄（`TSMC Overweight`）時，和標題的任一行一致就算一致 |
| 10 | 凱基 3665 首頁 EV/EBITDA 5 筆證不出來 | 科目比它的數字低 4.6 pt，數字那一行左邊是分析師欄的人名 | 驗證端：數字那一行在科目欄沒有自己的字、而且離它最近的科目行就是這一行 → 同一列，照常逐欄對 |

### 三、驗證器自己錯過的地方（照實寫）

* **第一版 G21 把凱基 3665 第 2 頁的錯值標成「證實」**（1Q26 營收 23,224、2Q26F 營收 2.6 …）。原因和根因 7 一模一樣 ——
  抽取那一支和驗證那一支是同一個人寫的，用了同一個「平均切」的假設。抓到它的是**第二道檢查**
  （暫存夾那支、用欄數而不是座標對位的驗證器）。兩邊現在各自用位置分組，已知答案加了一張子欄數不同的分組表。
* **第一版 G21 拿聚焦副本當原檔，又套一次頁碼換算**：值仍是報告裡的真數字，但「原檔第 N 頁」的註記錯了。改成回原檔驗。
* 第二道檢查器自己的誤報也一條一條修掉（月-年欄頭的季、`ppts` 單位、散文裡出現的科目字、同一行後面的別欄、電話的第二讀法、
  `Gross-profit margin` / `Net income margin` 的字面），修完它在**舊輸出**上只剩那 2 筆真錯 —— 證明它不是被調到放水。
* MISALIGNED 的修法順序：這一列的期間另有別列也在講 → 改期間；沒有 → 先補這一列自己那一欄的值（凱基 1Q26 → 實際數 20,864）。

### 四、結果（`--no-cache`，同一份程式碼跑兩份語料）

真報告的 7 筆自動修正全是 CLST Figure 1（預估修正表）：抽表只抽到 old 那一欄，G21 依座標改成 new（例：營收 2025CT 829,319 → 879,897）。

```
真報告 19 份（倉內 fixtures，唯讀複製）
  G21 年度數據        1,733 / 1,733 筆（逐欄證實 1,726 · 自動修正 7 · 剔除 0；期初 / 期末現金多出 34 筆）
  G21 年度財報格      354 / 354 格
  G21 代號紀錄        104 / 104 欄（14 份個股）
  G21 一標題四重點    證實 42 · 報告沒揭露 34 · 剔除 0
  第二道檢查          錯 0 · 對 2,021 · 它自己證不了 207（欄數對位證不了的分組表 / 轉置表，不是錯）
  P21 驗收            8 / 14 份 100% 過關（和 main 同一張待修單：CLST · Citi · Daiwa · MQ · 瑞基 ×2）
  G17 部位            VERIFIED 154（main #77 是 145）· 鎖 BROKEN 0
  P23 時間三形        PASS（0 欄不合規）
  收尾                完成（FAIL 0 · 鎖 BROKEN 0）
合成語料 107 檔
  G21                 年度數據 2,436 / 2,436 · 年度財報格 2,142 / 2,142 · 代號紀錄 529 / 529 欄 · 重點 174 · 剔除 0 · 自動修正 0
  P21 驗收            59 / 59 份 100% 過關 · 鎖 PASS
  第二道檢查          5,277 項全對（錯 0 · 證不了 0）
引擎鎖 lock           已知答案 17 組全過 · 鎖住 52 支
check / selftest      GREEN 12/12 · GREEN 33/33
測試                  473 案（VRN / VDF / artifacts 21 套）· 248 案（治理）· unified-engine 87/87 · 全景 GREEN · 基準 AMBER（照規則不擋）· 樹沒被改動
HTML U/I（Chromium）  兩份輸出各 27 / 27（分頁 · 列數 = JSON 計數 · 換頁 · 檔名篩選 · 搜尋 · 嵌入安全 · 手機寬不左右捲 · 深色模式 · 0 個 JS 錯誤）
```

剔除前後（真報告）：第一版 G21 剔除 63 筆（CLST 34 · 凱基 3665 第 2 頁 12 · Daiwa 淨利率 3 · 半行 5 · 代號紀錄 8 · 重點 1）
→ 這一輪 0 筆。修好的是**擷取端**（根因 1–9），不是把驗證放寬；放寬的只有根因 10 那一條，而且有反例測試
（數字那一行自己有科目、或別的科目行更近 → 不算）。

### 五、接在第十一輪之後（同一天另一條線先合進 main）

這一輪一開始的底是 #73；寫完時 main 已經到 #77（第八到第十一輪：券商沒印、現價誤殺、代號紀錄第二讀法）。
重新接到 #77 上（中途 main 又從 #76 走到 #77，同樣的方法再接一次）：原始碼的衝突手合（TitleTrim 只有檔頭計數、測試兩邊各加一個類別都留），
**產生的冊（ID / REGEX / INDEX / 註冊冊 / 引擎鎖 / 代號紀錄合併冊）一律取 main 的再跑 build / lock 重生，不手改**；
我這邊新函式 / 新測試的編號和 main 撞號（ENG014-FNC095/096、FNC099；TST012-FNC057/058），拿掉讓 build 重發。

同一份 19 份真報告，**main（#77）本身是紅的**：P23 時間格式 `FiscalQuarter` 有 576 格寫成 `Q1`，收尾卡住。
接上這一輪之後 P23 PASS、收尾完成。逐部位和 main 比，變了 27 個：標題 / 電話 / 核心觀點 / 期初期末現金 / 營益率，
狀態比 main 低的 3 個逐一看過 —— JPM 公司名 main 是 VERIFIED，但那一票來自 PDF 屬性 Title（檔名 `tsmc(2330TW)-JPM-250718`，
頁上沒印）；瑞基核心觀點從 NOT_PRINTED 變成 SINGLE，是讀到了頁上真的副標，排序上看起來「降」，實際是補上。

### 六、界線（沒做的、做不到的）

* 操作員手上的 106 檔語料不在這台機器；這裡量的是倉內 19 份真報告 + 合成語料 107 檔。
* OCR 引擎都不在（P22 WARN）：影像檔照舊 `OCR_REQUIRED`，OCR 出來的字不進驗證。
* 「證實」的意思是：值在原檔那一頁、那一列、那一欄（含子欄）。**不是**「值在頁上某處」。證不出來就剔除，不猜。
* CLST Figure 1（預估修正 old / new）抽表只抽到 old 那一欄：資料庫引擎照抽，G21 依座標改成 new（修正冊逐筆前後值）。
  資料庫引擎沒有因此學會讀 new —— 那一欄根本不在它抽到的表裡。
* 標題的公司名單獨一行時，標題接的是下面同一欄、比內文大的那一行；底下沒有比內文大的字就不接，也不拿公司名充當核心觀點。


## 2026-10-20 第十三輪：操作員「VRN-1 VRN-2工具可相互取用 · 可驗證性高精準度還原後表格可改為資料庫形式PIVOT · 兩個系統元主體邏輯不變但各式可以找缺少的工具 · 獨立系統兩個MAIN」

### 一、兩個 MAIN、兩本工具冊、兩支各寫各的工具橋

```
VRN-1  MAIN = VRN_Main_v0100.py          工具橋 engine/VRN_ToolBridge_v0100.py（VRN-ENG023）
       借出工具冊 ssot/VRN_ToolManifest_v0100.json（build 寫 · check P25 驗 sha256）
         table.pivot_db   engine/VRN_PivotDB_v0100.py · build_pivot_db（契約 VIA_PivotFacts/1）
VRN-2  MAIN = ActivateVRN-2.py → VRN-2 SystemManager（movies-dataset 倉 · 啟動器 v0131）
       工具橋 VRN2_ToolBridge_v0100.py · 借出工具冊 <VIA 根>/VIA_Reports/vrn2/tools/VRN2_ToolManifest_v0100.json
         section.near     段落標題（VRN-2 管理器第三讀法 pdfplumber 字詞框 + v0239 的 _sec_near）
         ocr.image        OCR（VRN-2 的 OCR 隔離環境 envs/vrn2_ocr · rapidocr）
```

* **借 = 讀對方的工具冊 → 冊上每個檔逐一核對 sha256 → 依路徑載入（獨立模組名 · 載入時不寫 __pycache__）→ 只寫自己的輸出夾。**
  對方的檔一個都不改、不複製進自己的倉；對方沒有 / 檔改過 / 自己標「不能用」→ 不借、照實寫（WARN，不是 FAIL）；
  找不到對方 = 只用自己的工具。兩支工具橋沒有共用一行程式碼，只靠工具冊（`VIA_ToolManifest/1`）對話。
* **借讀法，不借判準。** VRN-1 借 VRN-2 的段落標題「讀法」；判準（成長率 / 比率段落底下的金額科目 = 錯）是 VRN-1 自己的
  `VRN_OutputVerify.section_semantic`。VRN-2 借 VRN-1 的 PIVOT「工具」；哪些格可以進去（⑪ 獨立驗證判對位）是 VRN-2 自己決定的。
* 主體邏輯不變：資料庫引擎、首頁引擎、TitleTrim、Evidence_Core 一行沒動；OutputVerify 多一個**可選**參數 `section_of`（不給 = 行為不變，
  已知答案有一條專門驗這件事）。
* 找 VRN-2：`VIA_VRN2_ROOT` → VRN-2 交接報告的 VIA 根（`C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`）
  → 家目錄底下 → VRN-1 倉旁邊。`VRN_NO_BORROW=1` = 這次不借（比對「借 / 不借」用）。

### 二、G22 PIVOT 資料庫（`engine/VRN_PivotDB_v0100.py` · VRN-ENG022）

G21 驗證過的年度數據 → **事實表**（一格一列：系統 · 檔 · 代號 · 頁 · 表 · 科目 · 印的科目字 · 單位 · 期間鍵 · 值 · 原值 · 驗證狀態 · 說明）
→ **PIVOT**（年度欄 `YYYY` · 季度欄 `YYYY-MM` 季末月；表層 = 一張表一列科目 · 報告層 = 同一份報告跨表合併）→ `<round>/pivot/`：

* `VRN_Pivot_v0100.sqlite`（標準庫，一定寫得出來）· `VRN_Pivot_v0100.duckdb`（有 duckdb 才寫；另建 `v_*` 檢視用 **DuckDB 原生
  `PIVOT … ON period_key IN (…)`** 算一次，和實體表逐格比對 → 不一致 = FAIL）· 每張表 CSV（UTF-8 BOM）+ Parquet · HTML U/I · JSON 摘要。
* 只收 VERIFIED / CORRECTED、有期間、有數值的格。**同一格兩個不同的證實值不挑一個：格子留空、列進「衝突」**（`kind`：sign = 正負不同 ·
  scale = 差 10 的次方 · value = 真的不同）。
* **印的位數不同的同一個數不是衝突**（4,458 與 4,457.8）：每一格依原值的小數位算出印的精度（half_ulp）；印得最細的那幾個要相同，
  其他每一個都要是它四捨五入出來的 → 取最細的，列進「精度合併」。Python 與 DuckDB 檢視用同一條規則各算一次（變異測試：把規則改壞，
  DuckDB 比對一定抓到）。
* 報告層只合「印的科目字一樣」的列：`EPS (NT$)**`（自家）與 `EPS (NT$)§`（共識）、reported / adjusted、千元表與百萬元表是不同的量。
* 檔名照原字（全形「？」不能被 NFKC 改成「?」—— 那就不是那個檔了）；HTML 標題寫系統名（VRN-1 / VRN-2，不寫籠統的 VRN）。
* `lock` 已知答案多兩組：`pivotdb`（18 項）· `toolbridge`（10 項）；`outputverify` 19 項（多段落標題 5 項）。

### 三、G23 借用工具 + G21 段落標題（借來的讀法 · VRN-1 的判準）

G23 在每次執行的第一輪最前面找 VRN-2、借 `section.near` 與 `ocr.image`。借到 `section.near` → G21 證實過的每一筆再問
「科目上方同一欄最近的段落標題」：

| 段落標題 | 這一列的科目 | 判 |
|---|---|---|
| Growth / YoY / QoQ / % chg / 成長 / 年增 | 金額科目（營收 · 毛利 · 營業利益 · 稅前 · 淨利 · EPS · 資產 …） | **剔除**（值是成長率，不是金額） |
| (%) · Margin(s) · Ratio(s) · Return · 率 | 金額科目 | **剔除**（值是百分比 / 比率） |
| 混合單位（NT$m, % · 百萬元 · 每股盈餘 (NT$)） | 任何 | 不判 |
| 其他（P&L · Estimates · 沒有標題） | 任何 | 合 |

讀法倒了（例外）→ 不剔除、記錯誤數（沒讀到 = 不判，不拿來當證據）。`ocr.image`：VRN-1 自己三支 OCR 都不在時，G06 / P22 改借 VRN-2 的
（結果形狀和 VRN_Ocr.read 一樣；engine 寫明是 VRN-2 的；OCR 的字照舊不進判讀）。

### 四、這一輪量到的（倉內 19 份真報告）

**PIVOT 的衝突表是第二道檢查。** 第一次把 G21 驗證過的 1,733 筆轉成 PIVOT，報告層 83 個衝突 —— 80 個是「同一個科目底下其實是不同的量」
（報告層鍵只用科目 → 改成科目 + 印的科目字）、3 個是同一個數印的位數不同（精度合併），**剩下 4 個是真錯**：

```
MS 3661 第 10 頁  左表 Net profits 6,446 / 5,426 / 13,493 / 15,409
                  右表 Growth(%) 底下 Net profits 93.8 / -15.8 / 148.7 / 14.2   ← G21 證實成「淨利」
```

G21 證得出來（值確實在那一列、那一欄），但**那一列在 Growth(%) 段落底下** —— VRN-1 沒有段落標題的讀法，看不出來。
VRN-2 有（v0239 修 SECTION 用的就是它）→ 借來之後整份 19 份逐筆問一次：

| | 不借（VRN_NO_BORROW=1） | 借 VRN-2 section.near |
|---|---|---|
| G21 年度數據 | 1,733 / 1,733（含 39 筆錯） | **1,694 / 1,733**（剔除 39 筆，附理由與證據） |
| G22 PIVOT 衝突 | 4（WARN） | **0** |
| 收尾 | 完成（衝突是 WARN · 錯值仍在證實輸出裡） | 完成 |

39 筆逐筆回原檔看過，**全是真錯**：MS 3661 第 10 頁右表 Growth(%) 底下 Turnover / Operating profits / Pretax profits / Net profits / EPS
各 4 年（20）+ Margins (%) 底下 Net Profit 4 年（被歸成 NetIncome · 4）；MS 2308 第 6 頁 QoQ Growth (%) / YoY Growth (%) 底下的
Sales / Gross Profit / Operating Profit / Pretax Profit（15 · 金額列的字是 Net sales / Gross profit / Operating income / Pre-tax income，
growth 段落用的是另一組字）。留下來有段落標題的 384 筆逐類看過：Margins (%) 底下是毛利率 / 營益率 / 淨利率、Other ratios (%) 底下是
PB / EV/EBITDA、P&L / Estimates / 百萬元 底下是金額 —— 沒有一筆該剔沒剔。

### 五、工具自己錯過的地方（照實寫）

* **PIVOT 報告層第一版只用科目當鍵**：EPS (NT$)** 與 EPS (NT$)§、千元表與百萬元表、reported / adjusted 全擠進同一格 → 83 個「衝突」。
  改成科目 + 印的科目字 → 7 → 精度合併 → 4（真錯）。
* **精度合併第一版只認完全相同**：4,458（整數表）與 4,457.8（一位小數表）判衝突。改成依印的精度判；DuckDB 檢視也改用同一條規則，
  變異測試（把 Python 那邊的規則改回「只認完全相同」/「挑第一個」）DuckDB 比對都會抓到。
* **VRN-2 的 `_sec_near` 在並排表上回空白**：MS 3661 第 10 頁左表最後一欄的數字（x 282）落在右表科目欄（x 319）±40 pt 內，
  整列餵進去會把左表的數字當成這一列的科目 → 判成數據列 → 一路走到期間表頭 → 沒有標題。VRN-2 的本體不改（那是 VRN-2 的事、也是它主體邏輯的一部分）；
  VRN-2 的工具橋只餵科目欄起點以右的字。
* **轉置表的假剔除**：華南 3017 第 1 頁「年度 營收 毛利率(%) …」是欄頭在上的表，`營收` 是欄頭不是列 → 往上找到隔壁欄頭「毛利率」當段落標題
  → 5 筆營收被誤剔。改：有給值 → 只用有這個值的那一列；值不在科目那一列（轉置表 / 欄頭在上）→ 不定、不判。
* **check 的工具冊路徑**：第一版從工具冊往上兩層當倉根（少一層）→ P25 說檔不在；check 抓到、改好（自測也加了「冊上 sha256 和檔不同 → 點名跑 build」）。
  閘號一度用了已被 P24 CROSS 佔用的 P24 → 改 P25。
* **檔名被 NFKC 改字**：`AI末日論？假的.pdf` 變成 `AI末日論?假的.pdf`。檔名改照原字（其他文字照舊 NFKC），已知答案加一條。

### 六、結果（`--no-cache`，同一份程式碼）

```
真報告 19 份（借 VRN-2）  G21 年度數據 1,694 / 1,733（自動修正 7 · 段落標題剔除 39）· 年度財報格 354 / 354 · 代號紀錄 104 / 104 · 一標題四重點 42
                         G22 PIVOT 事實 1,694 · 年度 223 列 · 季度 85 列（表層 267 / 101）· 衝突 0 · 精度合併 3 · 還原表 7,312 格 · DuckDB 原生 PIVOT 比對 OK
                         G23 section.near 借到 · ocr.image：VRN-2 的 OCR 隔離環境在 → 借到（2 / 2 · P22 PASS）；不在 → 對方標不能用、照實 REFUSED（兩種都實跑過）
                         P21 8 / 14（同上一輪，待修清單沒變）· P23 PASS · 收尾 完成 · 不借（VRN_NO_BORROW=1）：1,733 / 1,733（含 39 筆錯）· PIVOT 衝突 4（WARN）
合成語料 107 檔           G21 2,436 / 2,436 · G22 年度 812 列 · 衝突 0 · P21 59 / 59 · 收尾 完成
VRN-2 借 VRN-1 的 PIVOT   沙盒樹（倉內 19 份 · 個股 14）：事實 4,653 / 4,905（⑪ 判對位才收）· 年度 1,060 列 · 衝突 18（報告層：符號慣例 5 · 跨表同名 13，回原檔看過是原檔本身兩張表印的不同）
引擎鎖 lock               已知答案 19 組全過 · 鎖住 54 支 · check GREEN 13 / 13（含 P25 工具冊）· selftest GREEN 33 / 33
測試                      487 案（VRN / VDF / artifacts 23 套）· 205 案（治理）· unified-engine 175 · 樹沒被改動
HTML U/I（Chromium）      PIVOT 頁 VRN-1 29 / 29 · VRN-2 29 / 29（8 個分頁 · 列數 = JSON · 年度欄依時間 · 換頁 · 檔名篩選（原檔名）· 搜尋 · 嵌入安全 · 手機寬 · 深色模式 · 0 個 JS 錯誤）
```

### 七、界線（沒做的、做不到的）

* VRN-1 的資料庫引擎本身沒有段落標題的讀法（主體邏輯不變）：沒有 VRN-2 時，成長率 / 比率段落底下被歸成金額的值照舊會被 G21 證實，
  只有 G22 的衝突表（WARN）會點名其中跟別張表撞到的格 —— 所以兩個系統要一起在。這一輪的根因修法是「借」，不是在 VRN-1 裡另寫一份。
* OCR：這台容器原本沒有 VRN-2 的 OCR 隔離環境 → VRN-2 的工具冊標 `ocr.image` 不能用 → G23 照實 REFUSED（只用自己的 → P22 WARN「都不在」）。
  照 VRN-2 啟動器 ③b 的作法另建一份（Python 3.11 · rapidocr_onnxruntime · numpy<2 · 只在暫存區、不進倉）之後：G23 借到 2 / 2、
  P22 PASS（借來的 OCR 讀已知圖，數字與拉丁字全中）；MQ-1560 影像 PDF 借來讀到 17,123 字 · 391 行（「2o26」這種錯照樣有 → OCR 的字照舊不進判讀）。
  這 19 份沒有影像檔，G06 的 OCR 路徑（SKIP_OCR_REQUIRED）這一輪沒有觸發。
* VRN-2 那邊的報告層衝突（損益表 / 資產負債表同名 Minority interest、CLSA 兩張表的 Other current assets、MS 2308 926 / 925）不是讀錯，
  是同一份報告兩張表本來就印得不同：格子留空、列在衝突表，不挑。
* 操作員手上的 106 檔語料不在這台機器；VRN-1 的倉不能從這裡推（另一團隊的倉，只讀）→ 修改以 patch / bundle 交給操作員套用。

## 2026-10-20 第十四輪：Codex PR #79 的三條，三條都成立 —— 其中一條在真報告上已經把錯值送進了驗證過的輸出

操作員：「一路實測修復到底 TEST DEBUG OPTIMIZE … FACILITATE … USER-TEST … ACTIVATE … TILL THEY WORKS PERFECTLY. 授權全自動完成」；
並重申「VCGC VRN-1 VRN-2 VDF 皆是獨立系統，有獨立的 MAIN，獨立運作互不影響」。這一輪只改 VRN-1 自己的引擎與冊，
借用照第十三輪：只讀對方的工具冊與檔、逐檔核對 sha256；借不到就只用自己的，照常跑完。

### 一（P1，接受）· 科目歸類的括號整段刪掉 → `Turnover (X)` 成了營收

Codex：`def_metric_key` 把括號裡的字全刪，`EPS (pre-tax)` 等於 `EPS`、`Revenue (YoY)` 等於 `Revenue`，
而 G21 也不擋英文的 `pre-tax`。

**查證成立，而且比他說的更糟**：19 份真報告裡 GS 6415 財務摘要表的 `Turnover (X)`（資產週轉率，0.4 / 0.5 / 0.6 / 0.7 倍）
被歸成 `Revenue`，4 筆**通過 G21、進了驗證過的年度數據與 PIVOT** —— 值在原檔那一格是對的，科目是錯的。

修法（資料庫引擎 `def_parse_metric_label`）：括號只去兩種 —— **單位**（幣別 · 規模 · % · x · 股）與既有的限定詞
（adjusted · reported · diluted · fully-diluted · FD · basic · core · recurring · consolidated · loss）；
其他括號字（pre-tax · YoY · excl. leases · % YoY）留在鍵裡 → 認不出來 → 不進年度數據（寧可少一列）。
列標自己寫了倍數卻不是倍數科目（PER · PBR · EV/EBITDA）、寫了 % 卻不是百分比科目 → 也認不出來。
G21 另加一道（不依賴引擎）：金額科目的列標自己寫了 `(x)` / `(…%…)` → 剔除；EPS 的排除字加 `pre-tax` / `before tax`。

在 19 份真報告 + 合成語料的 236 個列標上新舊對照：只差 2 個列標 —— `Turnover (X)`（錯的那 4 筆）與
`EV/EBITDA (excl. leases) (X)`（4 筆 · 定義不同的變體，不再當成一般的 EV/EBITDA；照 Codex 的建議只去單位）。
`流通股數(百萬股)` 第一版被誤殺（單位表沒有「股」）→ 對照抓到、補上。

### 二（P1，接受）· 組合段落只問「每個字詞在原文某處」

Codex：多欄首頁的退路把原文變成集合，丟了順序、遠近與次數；拿常見字重排的句子也會被標 VERIFIED。

**查證成立**：真報告 18 段走這條退路，其中幾段本身就是兩欄交錯拼出來的（Daiwa 1319 的句子中間夾著側欄的
`Core EPS (FD) change 7.4 6.1 5.8`），而重排的句子確實會過。

修法（`tile_summary_text`）：這一段要能從頭到尾切成**同一頁**原文裡的連續片段
（每段在那一頁兩種讀法之一裡一字不差，片段之間不能跨讀法）；帶數字的片段至少 8 字（數字不能單獨從別處搬來）；
三段以上時短片段（< 8 字）合計不能超過全段的 25%。驗證註記寫「第 N 頁 K 段原文依序拼成」。
18 段量過：17 段在第 1 頁切得出來（2–11 段）→ 證實；1 段剔除 —— 凱基 2637 首頁那段
`N 升 (%) 22.4 N 漲空間 (%) 7.3 A (% % )上 漲 %`（字框疊在一起讀亂的「潛在上升空間」）：`升%22.4n` 這個數字片段沒有上下文。
已知答案加四條：兩欄交錯 → 證實 · 頁上的字重排 → 剔除（短片段）· 跨頁拼 → 剔除 · 數字從別處搬來 → 剔除。

### 三（P2，接受）· 代號只要四位數出現在原文任何地方就算

Codex：報告裡四位數到處都是（年份、價格、表格值），錯的代號會被證實。**查證成立，而且檔名那半邊也有同一個洞**：
`s in fn` 是子字串比對，`MQ-1560 20260520.pdf` 裡 `2026`、`0520` 都「在檔名裡」。

修法：檔名要是**獨立的一段**（前後不是數字）；原文要在**代號的位置**上 —— 帶交易所 / 平台記號（`2330.TW` · `2330 TT` · `6669TT` · `2330-TW`）、
括號裡（`奇鋐(3017)`）或「代號 / 股號 / ticker」後面；兩種讀法都查。
14 份真報告的代號原本就全部同時在檔名與這些位置（照實量過），所以沒有誤殺；已知答案：`2025`（檔名日期的一截、原文的年份）· `1130`（價格）→ 剔除。

### 四、順帶修的（FACILITATE）· 借不到時說下一步

VRN-2 的倉在、但還沒跑過 VRN-2 v0131 以上（沒有工具冊）→ G23 以前只說「找不到」；現在說「VRN-2 在 <路徑>，但還沒有工具冊 → 先跑一次 VRN-2 一鍵 v0131 以上」。
sha256 不符 → 多一句「VRN-2 的檔換過但工具冊沒重寫：再跑一次 VRN-2 一鍵」。VRN-2 那邊（VRN-2 自己的工具橋 v0101）對 VRN-1 做同樣的事。

### 五、工具自己錯過的地方（照實寫）

* 根目錄的治理測試 `test_v0200_dictionary_classifies_the_governance_vocabulary` 一度紅：倉裡沒被歸類的公開函式名 466 個，門檻 465.85
  （HEAD 本來就是 464 / 465.15，壓線）。我新加的兩個名字不在治理詞彙裡 → 改名 `def_parse_metric_label` / `tile_summary_text`（測試門檻不動）。
* 單位表第一版讓 `us` / `nt` / `in` 單獨成立 → `Sales (US)`（美國地區的營收）會被當成單位括號、歸成 Revenue；提交前重讀自己的差異抓到 →
  這三個字單獨出現不算單位（`US$ in mn` 照舊）· 已知答案與單元測試各加一條。
* 第一次跑單元測試用錯了探索參數（`-t .`，tests 不是套件）→ 不是測試紅，是沒跑到；改用 `-s tests` 重跑。

### 六、結果（`--no-cache`）

```
真報告 19 份（借 VRN-2）  G21 年度數據 1,686 / 1,725（逐欄證實 1,679 · 自動修正 7 · 段落標題剔除 39）· 年度財報格 354 / 354 · 代號紀錄 104 / 104
                         一標題四重點 41 + 沒揭露 34 · 剔除 1（上面那段讀亂的首頁字）· G22 PIVOT PASS · G23 借到 2 / 2 · 收尾 完成
                         和第十三輪比：驗證過的年度數據只少那 8 筆（Turnover (X) 4 · EV/EBITDA (excl. leases) 4），其餘一筆不差
不借（VRN_NO_BORROW=1）   1,725 / 1,725（G21 照實說沒借到段落標題）· 收尾 完成
VRN-2 不在場              G23 WARN「VRN-2 在 …，但還沒有工具冊 → 先跑一次 VRN-2 一鍵 v0131 以上」· 只用自己的 · 收尾 完成
合成語料                  G21 2,436 / 2,436 · 代號紀錄 529 / 529 · 摘要 174 + 沒揭露 58 · 剔除 0（和第十三輪一模一樣）· 收尾 完成
引擎鎖 / 冊               lock 54 支 · check GREEN 13 / 13 · selftest GREEN 33 / 33 · 輸出驗證自測 22 / 22（新加 3 條各自做過變異測試：改回舊邏輯 → 只紅那一條）
測試                      VRN 425 · 根目錄 423（跳過 6）· VDF 20 · artifacts 45 · 全過
```

### 七、界線

* `EV/EBITDA (excl. leases)` 現在不進年度數據：它是定義不同的變體。要收，得先給它自己的科目（不是併進 EV_EBITDA）—— 留給操作員裁定。
* 組合段落的判準證的是「同一頁、依序、一字不差的原文片段拼成」，不是「原文有這一句」：兩欄交錯的首頁段落本來就不是一句話。
  要更嚴（例如只收單欄的句子），得先讓首頁引擎分欄 —— 那是首頁引擎的主體邏輯，這一輪不動。

## 2026-10-20 第十五輪：收尾判準是「輸出驗證無誤於 HTML U/I」—— 真瀏覽器看到驗證頁一列被擠成 180 px 高

操作員：「授權全自動完成到收尾 實測實際修正自動完成直到輸出結果驗證結果無誤於HTML U/I即收尾完成」。
第十四輪合併進 main（PR #79 · 7693aee）之後，用操作員一鍵（VRN-1 / VRN-2 操作員一鍵 v0101 · VRN-1 從 GitHub 全新複製）實跑兩個系統，
四個 HTML U/I 用真的 Chromium 逐頁實測：VRN-2 U/I 35 / 35 · VRN-2 PIVOT 29 / 29 · VRN-1 PIVOT 29 / 29 · VRN-1 驗證過的輸出 27 / 27 —— 數字全對。

### 一、看截圖才看到的：驗證頁一列 180 px 高

驗證過的輸出頁（`VRN_Verified_Output_v0100.html`）年度數據分頁，一列 180 px 高、一頁 50 列要捲很久。逐欄量：`VerifyNote`（48 字）
在 30 多欄的寬表裡被自動版面擠成 88 px 寬，折成 9 行。值沒錯，是讀不下去。

修法（只動頁面）：畫表時字數超過 24 的格子加 `long` 類別，`#tb td.long{min-width:20em}` —— 欄寬取那一欄最寬的最小寬度，
長文字欄撐開、列高回到兩三行，表格本來就能左右捲。U/I 實測加一條「第一頁每一列都不超過 120 px 高」：舊頁 201 px → FAIL（咬得住），新頁 PASS。

### 二、結果

```
真報告 19 份（借 VRN-2 · 從操作員一鍵 v0101 跑出來的那一份工具冊）  G21 年度數據 1,686 / 1,725（逐欄證實 1,679 · 自動修正 7 · 段落標題剔除 39）· 年度財報格 354 / 354
                         · 代號紀錄 104 / 104 · 一標題四重點 41 + 沒揭露 34 · 收尾 完成 —— 數字和第十四輪一模一樣（這一輪只動頁面）
HTML U/I（Chromium）      驗證過的輸出 28 / 28（多一條：第一頁每一列 ≤ 120 px · 舊頁 201 px FAIL → 新頁 76 px PASS）· PIVOT 29 / 29
引擎鎖 / 冊               lock 54 支 · check GREEN 13 / 13 · selftest GREEN 33 / 33 · 輸出驗證自測 22 / 22
測試                      VRN 425 · 根目錄 423（跳過 6）· 全過
```

## 2026-10-20 第十六輪：全景式檢查一切 —— 找到一個真的資料問題：同一夾重建時留下上一次的 Parquet / DuckDB

操作員：「全景式檢是一切找出問題分為可一次性解決或順序解決用精準AST定位一口氣修一輪但不可有九頭龍風險或是傷害既有系統模組或是成果 獨立系統有獨立的MAIN」。
PR #80（第十五輪）三個 CI 紅燈 2 秒就結束，也一起查到底。

### 一、怎麼查的

* 全景（只讀、不執行）：`panorama-matrix --static` 掃整個倉 948 檔（Python 115 · PowerShell 47）；
  VCGC 鎖版的骨架卡工具（CGC_MDL158 v0117）逐支 `read` 115 支 Python，問題逐條帶行號：吞例外 280 · 重複定義 15 · 裸 except 5 · 語法 / 編譯錯 0。
* CI：三個 job 的 `runner_id` 是 0、沒有任何步驟跑起來、日誌 404；重跑一次一樣。同一個帳號的公開倉（movies-dataset）Windows CI 08:38 還是綠的，
  本倉是私有倉 → 是私有倉的 Actions 分鐘數 / 花費上限，不是程式。本機照五個 workflow 的步驟逐步重跑 c370f29：全過。

### 二、分類（可一次解決 / 要順序解決 / 不動）

| 類 | 項目 | 處理 |
|---|---|---|
| 一次解決 | `VRN_PivotDB_v0100.write_files`（L433）· `write_duckdb`（L359）· `VRN_OutputVerify_v0100._write_table`（L1146）：寫不出 Parquet / 沒有 duckdb 時，同一夾上一次的檔還留著 | 本輪修掉（下面三）|
| 順序解決 | CI 紅燈：私有倉 Actions 分鐘數 / 花費上限 | 操作員到 GitHub Settings → Billing 處理；恢復後 CI 才會真的跑 |
| 不動 | 重複定義 15 · 裸 except 5：全在 `attachments/` 的引擎原件（VeritasCeleritas · VeritasAegisNexus · 舊版 MDL006 / MDL008）| 是鎖定的原件（橋注入器也刻意跳過），一改就斷鎖 = 九頭龍 |
| 不動 | 吞例外 280：引擎裡的是「可選套件不在就退回」「清暫存檔失敗不擋主流程」「逐列解析不合就跳過」 | 是設計，改成丟例外會讓主流程在不重要的地方停；逐一看過我自己的兩支，只有上面那三處會留下錯的資料 |
| 不動 | 同族分散 26 · PowerShell `param(` 不是首句 2（都在 `attachments/`）| 既有結構；`.ps1` 不改（L70）|
| 不是 VRN-1 的 | VCGC 骨架卡工具每讀一支都印 `SyntaxWarning: invalid escape sequence '\*'` | 是 VCGC 工具自己的字串，四系統互不干涉，只記下、不代修 |

### 三、修的那一個：同一夾重建，舊的 Parquet / DuckDB 跟新的 CSV 對不上

VRN-2 的 ⑫ 借 VRN-1 的 `table.pivot_db`，寫進 VRN-2 自己一直沿用的 `VIA_Reports\vrn2\pivot`（不清空）。
重現：同一夾建兩次，第一次一切正常，第二次值改了、但寫不出 Parquet（沒有 pyarrow 或寫到一半壞掉）、也沒有 duckdb →
CSV 是新值 9999，Parquet 還是舊值 1200，舊的 `.duckdb` 也還在。打開夾子看的人會看到兩份不一樣的數字。

修法（只加三行、不加函式、不改主體邏輯）：寫不出的那一刻把同名的舊檔刪掉 —— `write_files` 的 except、`write_duckdb` 沒有 duckdb 的那一支、
`_write_table` 的 except 各一行 `unlink(missing_ok=True)`。寫得出來的時候一個位元組都不變。

### 四、結果

```
重現腳本            修前 STALE（CSV 9999 · Parquet 1200 · 舊 duckdb 在）→ 修後 CLEAN
新單元測試 2 條     test_rebuild_without_parquet_or_duckdb_keeps_no_old_file · test_table_written_again_without_parquet_keeps_no_old_parquet
                    舊程式碼 2 條都 FAIL（咬得住）→ 新程式碼 2 條都 OK
VRN-2 借用實測      VRN-2 自己的工具橋 v0101 借到新版 table.pivot_db（sha256 adadf2a5…）· 指紋 f4fb28bf836fcfb3 和 v0132 實跑相同
                    · 同一夾再借一次、模擬沒有 pyarrow / duckdb → 舊 Parquet 8 支全清、CSV 8 支在、指紋仍相同
CI 本機重跑         五個 workflow 逐步照跑（每次全新暫存夾）· 全過
真報告 19 份          G21 年度數據 1,686 / 1,725（逐欄證實 1,679 · 自動修正 7 · 剔除 39）· 年度財報格 354 / 354 · 代號紀錄 104 / 104
                     · 一標題四重點 41 + 沒揭露 34 · 收尾 完成；驗證過的六張表和第十五輪逐格相同（只有 CreatedAt / UpdatedAt 時間戳不同）
                     · PIVOT 指紋 6a508702ffcf29bf 和第十五輪相同
HTML U/I（Chromium） 驗證過的輸出 28 / 28 · VRN-1 PIVOT 29 / 29 · VRN-2 PIVOT（舊 Parquet 清掉、只剩 CSV 的那一夾）29 / 29
引擎鎖 / 冊           lock 54 支 · check GREEN 13 / 13 · selftest GREEN 33 / 33
測試                 VRN 427（多 2 條）· 根目錄 423（跳過 6）· 全過
```

### 五、界線

* 寫不出的那一刻才刪舊檔；舊檔被別的程式開著鎖住（Windows）時刪不掉 → 這一次的 PIVOT 直接報錯，不默默留舊值。
  有 duckdb 時本來就是這樣（`os.replace` 換不過去會報錯），現在沒有 duckdb 時也一致。
* VRN-2 主體、VRN-2 的工具橋、VRN-2 的冊一個位元組都沒動；VRN-2 發行文件裡記的是 v0132 實跑時看到的舊 sha256（紀錄，不是鎖），
  借用時一律現場拿 VRN-1 的工具冊逐檔核對。
* 吞例外 280 處沒有一處改成丟例外 —— 那是九頭龍：每一處都是「這裡失敗不該擋主流程」的設計。

> 第十五、十六輪是 PR #79 那一條的延續（PR #80 · 分支 `claude/optimistic-goodall-yhalc5`）；下面分隔線之後是 PR #78 那一條。
---

# 2026-10-20 兩條分支同時在跑：以下是 PR #78 這一條的輪次

這一份是兩個 session 共用的紀錄。第十一輪之後分成兩條：

* 上面到「第十四輪：Codex PR #79 的三條」是 **PR #79 那一條**（PIVOT 資料庫、工具橋、OutputVerify），已經併進 main。
* 下面是 **PR #78 這一條**（完整度回補、助手引擎可見、快取鑰匙、agree、四重點 EPS、上漲空間、HTML U/I）。

**兩條各自從第十二輪開始編號，所以號碼會重複** —— 要找某一輪，看日期加標題，不要只看號碼。
兩條動到的檔案在 2026-10-20 09:5x 併過一次（`git merge origin/main`），衝突只出在這一份文件、
兩支測試檔（各自新增的類別，兩邊都留）、以及每輪重生的那幾本冊（照規矩用 `build` / `lock` 重生，不手改）。

---

## 2026-10-20 第十二輪：文字檔的內文被母引擎吞掉兩成 —— 8 檔 RED 擺著，而漏的正是四重點的料

### 一、怎麼找到的：把每一張輸出表的狀態欄全部攤開掃一遍

上一輪學到「一整欄從頭到尾沒有 VERIFIED 就是一條讀法掉了」。這一輪把它變成例行動作 ——
**每一張輸出表、每一個狀態欄，全部列出分布**。掃出三件事：

```
vrn_regions_checks       state  INSUFFICIENT 306/306      ← 恆等式，語料沒印運算元，誠實
vrn_title_parts          market_state UNKNOWN_NO_GENERATE 59/59  ← 標題只印 (6873 TT)，TT 分不出上市櫃，誠實
vrn_regions_completeness state  RED 8                     ← 這個不誠實地擺著
```

### 二、RED 8 筆：8 個 .docx／.txt **每一檔**都只收到八成

```
3653健策凱基投顧 向子慧 (3).txt     387 字 → 收 312 字（80.62%）· 漏 75 字
華南投顧-2762-世界健身-KY-Memo…     386 字 → 80.57%  · 漏 75 字
…（8 檔全部如此，PDF 2040 頁全 GREEN）
```

漏掉的是同一段，而且是**有意義的正文**：

```
主要動能來自 AI 伺服器需求、產品組合改善與新產能開出，毛利率可望維持在高檔。
催化因素：新客戶認證通過、下半年旺季；風險：匯率波動與原物料成本上升。
```

這兩句正是**四重點的第 3、4 點**。冊上的規矩寫得很清楚：
`completeness = 文字層每一個字都要被收走（≥ 99.9% GREEN）`。RED 擺著就是沒守。

### 三、根因在母引擎，而母引擎不能改

文字檔沒有版面座標，走的是 ENG394 的 `text_restore`。量出來的行為：

| 內文行數 | 來源內文字數 | 母引擎收到的 body 字數 |
|---|---|---|
| 4 | 127 | 135 |
| 5 | 174 | **135**（沒增加） |
| 6 | 210 | 218 |
| 7 | 248 | **218**（沒增加） |
| 8 | 283 | **218**（沒增加） |

body 會**停住**。換一組合成語料更誇張：12 行內文，母引擎**一行都沒收**（完整度掉到 29.81%）。
扁平表一出現，內文就會被吞掉一截，吞多少看行數與長度。

`engine/mother/VRN_ENG394_LayoutRestore_v0100.py` 是鏡像區，**一個位元都不能改**。
所以補在 VRN 這一側 —— 這條路本來就有（VRN 已經移植了 ENG394 v0101 的尾巴、
`_fill_excluded_text` 也是在這一層把母引擎留白的文字填回去）。

### 四、修法：只補「整行沒被收走的」，而且不准靠量表反推

```python
kept, excl = _captured_text(res)          # 完整度量表用的同一個收集函式
have = _key(kept + " " + excl)            # 比對用這支引擎自己的 _key（去空白、轉小寫），不另立一把尺
for raw in text.split("\n"):
    line = raw.strip()
    if _key(line) and _key(line) not in have:   # 整行的字一個都沒被收走 → 補
        ... anchor = f"c{at}-{at + len(line)}"  # 定位照母引擎自己的寫法：來源字元區間
```

三條自我約束：

1. **補的是原文**，不是重寫 —— 測試直接拿 `anchor` 去切來源字串比對，必須一字不差。
2. **不靠量表反推**。拿 `missing_segments`（量表算出來的缺口）去補，等於讓量表自己證明自己；
   這裡的判準是結構的：「整行沒被任何區塊收走」。
3. **補不等於沒事**：完整度那一列多一個 `recovered_lines`，補了幾行看得見。

### 五、實測（106 檔真實報告）

| | 修前 | 修後 |
|---|---|---|
| `vrn_regions_completeness` | GREEN 2040 · **RED 8** | **GREEN 2048 · RED 0** |
| 8 檔的截取率 | 80.37–80.67% | **100.0%**（各補回 3 行） |
| `vrn_regions_sentences` | 108 列 | **132 列**（+24 = 8 檔 × 3 行） |
| 內層 | PASS=318 WARN=7 SKIP=7 FAIL=0 | PASS=318 **WARN=5** SKIP=7 FAIL=0 |
| 燈號 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 | **同** |
| 驗收 · VERIFIED · 待修 | 59/59 · 1369 · 8 | **同** |

消掉的兩個內層 WARN 就是這件事本身：
`截取完整度：未達 99.9% 的 8 檔`、`文字檔缺口：8 段是「本文尾段緊接扁平表」`。
**那兩行 WARN 早就把病灶指出來了，只是沒有人去修** —— WARN 不是沒事。

### 六、半路踩到的一個坑（記下來）

第一版我把補回的塊寫成 `anchor: ""`，單元測試全過、實測也漂亮，
但合成語料那一輪 G16 紅了：

```
FAIL G16 DATAFRAME  vrn_regions_sentences · RED · anchor:必填但 12 筆空
```

**表頭冊說 `anchor` 是必填**。補回來的塊也要有定位，而且要照母引擎自己的格式（`c<起>-<迄>`）。
改完順手把 `subcategory` 也對齊成 `BODY`（同樣是必填欄）。
教訓：往輸出表塞新列之前，先看表頭冊要求哪些欄必填 —— 自測綠不等於整條鏈綠。

### 七、這一輪學到的

**把狀態欄全部攤開掃一遍，比盯著單點猜有效。** 三輪下來，三個真缺陷
（現價、代號、文字檔內文）都是這樣找到的：先看「哪一欄整欄都是同一個不好的值」。

**WARN 擺著就會長住。** 這兩行 WARN 連缺口在哪一段都寫出來了，還是擺了好幾輪。
閘喊出來只是第一步，喊完要有人修。

### 八、Codex PR #78 三條 P2，三條都成立（都是我這一版自己打進去的）

**P2-A 半行被收走時，整行補回去會變成重複。** 母引擎只收到 `…2026年17.07`，我把整行
`我們預估…17.07 元。` 當成「沒收走」整行補上去 —— 同一句在 `sentences` 出現兩次，
而 `dedup` 只清 `_key` 完全相同的塊，前綴對整行清不掉。
改成用**來源字元區間**判重疊（不是模糊比字）：原塊 `c0-251` 疊到 `c210-254`，
就把原塊尾巴接長成 `c0-254`、只接上 `text[251:254]`，不另開一塊。

**P2-B 補回的塊接在最後面，句號會倒著發。** 「表在前、內文在後」時：

```
修前  S0001 c152-169 原 '結論這一句在表後面…'    ← 後面的句子拿到 S0001
      S0002 c0-15    補 '開頭這一句在表前面…'
修後  S0001 c0-15    補 '開頭這一句在表前面…'
      S0003 c152-169 原 '結論這一句在表後面…'
```

編號之前照來源位置排回去（全部塊都解得出 `c<起>-<迄>` 才排，不動 PDF 那條路）。

**P2-C 補回的證據只活在記憶體。** 我在完整度那一列加了 `recovered_lines`，
但 SQLite 的 `completeness`／`sentences` 兩張表沒有這一欄、`analyze()` 的句子投影
也沒把 `recovered` 帶出去 —— 報表看起來就只是「100% GREEN」，**看不出中間動過手**。
這條打到我自己寫的設計目標（「補不等於沒事」）。補法照冊的規矩 **出新版不改舊版**：
`VRN_Output_Header_SSOT_v0109.json` = v0108 + 兩個宣告過的加欄
（`vrn_regions_completeness.recovered_lines`、`vrn_regions_sentences.recovered`），
SQLite 兩張表同步加欄，`VRN_DataFrame.HEADER_BOOK` 指到 v0109。

### 九、實測（三條修完）

| | PR #78 第一版 | 修完 |
|---|---|---|
| `vrn_regions_sentences` | 132 列（含 8 筆重複） | **124 列**（重複清掉） |
| `recovered_lines` 合計 | 只在記憶體 | **24**（CSV／SQLite 都有） |
| 標記為補回的句子列 | 看不出來 | **24** |
| 完整度 | GREEN 2048 | **同** |
| 燈號 · 驗收 | FAIL=0 WARN=19 PASS=45 · 59/59 | **同** |

單元測試 397 passed（+4），三條新測試在第一版上全紅。

---

## 2026-10-20 第十三輪：DocClass 引擎缺三支助手引擎，而且沒有任何地方說

### 一、先說兩個「查了沒事」的結果（沒事也要量過才能說）

這一輪先把輸出值本身獨立驗過一次 —— 不是看系統自己的兩條讀法對不對得上，
而是**我自己寫正則去掃原始頁面文字**，再和輸出表比：

```
59 檔 × 10 欄（代號 · 評等 · 目標價 · 收盤價 · 分析師 · 電郵 · 電話 · 報告日 · YF 碼 · Bloomberg 碼）
= 590 格，與紙面不符：0 筆
```

跨表同一事實是否打架（代號／公司／券商／評等／目標價，`ticker_record` vs `trim_parts` vs `regions_reports`）：
**0 筆不一致**。

（過程中我自己的探針錯了一次：電話那欄我把已經含 `02` 的捕獲群再補一個 `0`，
59 檔全部「不符」。輸出是對的，錯的是量尺 —— 又一次。）

### 二、再掃「整欄全空」，這次掃出真的

| 表 | 全空的欄 | 查下來 |
|---|---|---|
| `vrn_basic_info` | 25 欄 | 本機 VDF 資料庫缺席（G14 有報）＋ 語料沒印 —— 誠實 |
| `vrn_financial_data` | 21 欄 | 語料的財報表只印四列 —— 誠實 |
| `vrn_regions_regions` | `left_right`、`band` | 8160 個區塊的 path 全是 T／B，**一個 L／R 都沒有** —— 語料是單欄頁，左右切本來就切不出東西，誠實 |
| `vrn_regions_reports` | **`broker_raw`、`report_date`** | **不誠實** ↓ |

`broker_raw` 與 `report_date` 在 107 檔全空，而同一輪的 `basic_info.Broker = MEGA`、
`ReportDate = 2025-08-19`、`cover.broker` 與 `cover.date` 都是 VERIFIED。同一個 `decompose()`
填得出 `ticker` 與 `company_names`，就是這兩欄填不出來。

### 三、根因：ENG393 的三個助手引擎都不在這個倉裡

```python
# engine/mother/VRN_ENG393_DocClassVerify_v0100.py
m73b = m73.parse_broker(stem) if m73 else ""      # ← m73 是 None
date  = m73.parse_date(stem)  if m73 else ""      # ← 同上
```

逐一探測母引擎的助手：

```
eng393: eng072=缺（eng072 不在）· eng073=缺（eng073 不在）· eng114=缺（eng114 不在）· eng392=有
```

`engine/mother/` 只鏡了五支（392／393／394／395／396），而 **ENG393 自己還要叫三支**，三支都不在。
107 檔實測，ENG393 整路靜默降級：

```
broker_raw          0 / 107
report_date         0 / 107
fine_kind_eng073    None × 107
fine_type_eng114    None × 107
class_confidence    拿不到 broker_present_stock 與 agree_fine_type 兩個加分
ticker_of()         「這四位數是不是年份」的守衛沒跑
                    （ENG073 的 _date_spans / _is_year_like；那支函式的說明自己寫著「三道守衛」）
```

**而 `Mother.errors` 是空的。** 沒有閘、沒有 WARN、沒有任何一行字說少了三支引擎。

對照組：本機 VDF 資料庫缺席會在**三個地方**報出來（G14 LOCALDB WARN、`LocalDBStatus: ABSENT`、
紀錄表的 `adj_close_state: ABSENT`）。缺一支**引擎**卻一聲不響。

### 四、修法：讓它被看見，不替它補值

`Mother` 多一個 `degraded`：載完五支母引擎後，把每一支身上形如 `engNNN()` 的零參數取用函式叫一次，
回 `(None, why)` 的就記下來。G15 多一列 **WARN**（不是 FAIL）點名缺了哪幾支。

三條自我約束：

1. **不混進 `errors`** —— `def_gate_regions` 看到 `M.errors` 就 `return`，混進去 G15 會直接收攤，
   讀得到的值反而全不驗了。助手缺席不致命（590 格實測值都對），所以自己一欄、喊 WARN。
2. **只叫零參數的** —— ENG392 的 `eng072_check` 要參數，叫爆了不算助手缺席（測試釘住）。
3. **不替它補值。** 用 VRN 自己的檔名讀法去填 `broker_raw`／`report_date` 很容易，
   但那是**把 ENG073 的判斷再做一次**（九頭龍），而且那一欄的意思會從「ENG073 解出來的」
   變成「誰解的都算」。這是操作員要決定的，不是我。

### 五、實測

| | 修前 | 修後 |
|---|---|---|
| 缺三支助手引擎 | **沒有任何地方說** | G15 一列 WARN，指名 `eng393:eng072/073/114` |
| 內層 | PASS=318 WARN=5 SKIP=7 FAIL=0 | PASS=318 **WARN=6** SKIP=7 FAIL=0 |
| 外層燈號 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 | **同** |
| 驗收 | 59/59 | **同** |

**WARN 多一條是這一輪的目的，不是副作用。** 本來就缺三支引擎，只是以前沒人說。

### 六、這一輪學到的

**「整欄全空」要一欄一欄問為什麼。** 這次掃出 50 幾個全空欄，四類原因裡三類是誠實的
（資料庫不在、語料沒印、單欄頁切不出左右），只有一類是真的 —— 但那一類牽出三支不在的引擎。
一眼掃過去說「都是環境問題」就會錯過。

**缺一支引擎要和缺一個資料庫一樣大聲。** 資料庫缺席報三個地方，引擎缺席一聲不響 ——
同樣是「拿不到就降級」，待遇不該差這麼多。

---

## 2026-10-20 第十四輪：改了冊，`regions` 的鑰匙一個字沒變

### 一、怎麼找到的：不是看宣告，是改一本冊再比鑰匙

TEMP 快取每一步都有一把鑰匙（輸入檔的 SHA、引擎的 AST 指紋、它讀的每一本冊）。
鑰匙沒變就沿用上次的答案。所以鑰匙少算一本冊 = 改了那本冊，系統還是端舊答案出來，
而且**不會有任何一行字說它端的是舊的**。

`engine/VRN_RunCache_v0100.py` 上有一張「這一步不讀這些冊」的豁免表：

```python
DATA_NOT_READ_BY = {"batch": {"…VRN_TitleTrim_SSOT_v0100.json"}, "first_page": {"…VRN_TitleTrim_SSOT_v0100.json"},
                    "regions": {"…VRN_TitleTrim_SSOT_v0100.json"}, "focus": set()}
```

我沒有讀這張表就相信它，直接**改一本冊再比鑰匙**：把 `focus.doc_class_policy.INDUSTRY_OUTLOOK.process`
從 `COVERAGE` 改成 `SKIP`，四把鑰匙前後對照 ——

| 步驟 | 改冊之前 | 改冊之後 | |
|---|---|---|---|
| `focus` | `3c81c248…` | `e47e0e1b…` | 變了 ✓ |
| `batch` | `30210c38…` | `30210c38…` | 沒變（它真的沒讀）✓ |
| `first_page` | `b2aed1cf…` | `b2aed1cf…` | 沒變（它真的沒讀）✓ |
| **`regions`** | **`5a290319…`** | **`5a290319…`** | **沒變 —— 但它讀** ✗ |

### 二、它讀在哪裡，而且讀的是「要不要處理」

```python
# engine/VRN_PageRegions_v0100.py:75
TITLETRIM_SSOT = SSOT_DIR / "VRN_TitleTrim_SSOT_v0100.json"
```

`focus_book()` 從這本冊取 `doc_class_policy`，`class_policy()` 用它決定 `out["process"]`：
**FULL／COVERAGE／REGISTER／SKIP** —— 一份報告到底要不要拆、拆到哪一層。
這不是邊角參數，是這一步最上游的那個開關。

改了這本冊，`regions` 會拿**舊政策算出來的**版面還原結果當這一輪的答案。
比起算錯，這種更難抓：輸出看起來完全正常，只是它回答的是上一次的問題。

### 三、順手把同一類問題掃完：AST 掃原始碼，不只掃這一本

一本一本試會漏。所以寫一支掃描：把每一步**自己的程式碼檔**（`cache_code_files(step)`）
用 AST 解析，取出所有字串常數（**註解與 docstring 不算** —— 那是人在說話，不是程式在開檔），
再和它宣告「沒讀」的檔名對照。四個步驟掃下來，說謊的只有兩筆：

| 步驟 | 宣告沒讀 | 實際 |
|---|---|---|
| `regions` | `VRN_TitleTrim_SSOT_v0100.json` | **真的讀 —— 這一輪修掉** |
| `focus` | `VRN_TickerRecord_SSOT_v0100.json` | 提到，但那條路不會走到（下段） |

`focus` 那筆是真的例外：合併冊只出現在 `VRN_TitleTrim_v0100.py:1165` 的 `_domain_broker()` 裡，
而 `focus` 快取裝的是「留哪幾頁」的清冊，那條路從頭到尾不叫 `_domain_broker`。
更重要的是**合併冊每一輪 `build` 都重生** —— 算進鑰匙等於每輪必定全失效，快取形同關掉。
所以它留在豁免表裡，但是**連理由一起寫在程式碼與測試裡**（`ALLOWED` 白名單），
下一個人要改，得先把那段理由讀掉。

### 四、順便抓到的：舊測試把這個缺陷「寫進去保護」

修完跑測試，紅的是一條**舊的**：

```
FAIL: test_each_step_depends_on_what_it_reads
  self.assertNotIn("ssot/VRN_TitleTrim_SSOT_v0100.json", data, step)
AssertionError: 'ssot/VRN_TitleTrim_SSOT_v0100.json' unexpectedly found in […] : regions
```

那條測試要求的，**正好就是這個缺陷**。它不是沒測到，是**測了、而且釘住了錯的那一邊**。
這比沒有測試更糟：以後任何人把這一行修對，測試會先紅給他看，他很可能就改回去了。

改法是把 `regions` 從那條迴圈裡拿出來，正面寫它**必須**被算進去，
並且把「2026-10-20：這一行原本也要求 regions 跳過，那是把缺陷寫進測試」留在旁邊。

### 五、新測試，兩道，而且都在壞版本上紅過

| 測試 | 怎麼守 | 壞版本上 |
|---|---|---|
| `test_editing_the_routing_policy_moves_the_keys_of_the_steps_that_read_it` | 真的改冊、真的比鑰匙（改完還原） | **紅** `'5a290319…' == '5a290319…'` |
| `test_no_step_skips_a_file_its_own_code_actually_opens` | AST 掃字串常數對豁免表 | **紅** `['ssot/VRN_TitleTrim_SSOT_v0100.json'] != []` |
| 舊的 `test_each_step_depends_on_what_it_reads`（改正方向後） | 正面要求算進去 | **紅** |

三條都在未修的 `DATA_NOT_READ_BY` 上紅過，修回去才轉綠 —— 在壞版本上也會過的測試等於沒有測試。

### 六、實測

| | 修前 | 修後 |
|---|---|---|
| 改 `doc_class_policy` 之後 `regions` 的鑰匙 | **不動**（端舊答案） | **會動** `9d24d456…` → `607a64c4…` |
| `batch` / `first_page` 的鑰匙 | 不動 | **仍然不動**（沒有連坐） |
| 測試 | 400 | **402**，全過 |
| `check` | GREEN FAIL=0 WARN=0 | **同** |
| 鎖 | 51／51 | **同** |
| 107 檔實測 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 · 驗收 59/59 · HELD 1369 | **同** |

修完那一輪（鑰匙換過，`regions` 整個冷掉）是 `重讀 107 / 命中 0`、G15 114.8 秒、外層 **WARN=18**；
下一輪回到 `命中 107 / 重讀 0`、G15 **0.5 秒**（整鏈 140.6 → 26.0 秒）、外層 **WARN=19**。
那一條 WARN 的差別不是退步：`P09 ACCEL · G15 版面還原：TEMP 快取` 這一列**有命中才會存在**，
冷的那一輪沒有命中，所以沒有這一列。**一次性冷掉是修鑰匙必然的代價，不是副作用。**

### 七、這一輪學到的

**宣告會過期，量測不會。** 這張豁免表 2026-10-13 量的時候是對的；之後 `PageRegions`
長出了 `focus_book()`，表沒跟著改。靠人維護的「我不讀這些」清單一定會落後於程式碼，
所以守門要用**改冊比鑰匙**（實測）和 **AST 掃字串**（掃碼）兩道，不是靠維護宣告。

**測試會站在缺陷那一邊。** 修對了卻紅了一條舊測試，第一反應不該是「我是不是改壞了」，
要先問**那條測試要求的是哪一邊**。這一輪它要求的是錯的那一邊。

---

## 2026-10-20 第十五輪：1313 個可對照部位裡，612 個沒說「幾組讀成同一個」

### 一、怎麼找到的：把 PASS 的那一列攤開看數字

這一輪掃的是**閘過了、但數字自己在講話**的列。G17 有這麼一列，狀態 PASS：

```
跨來源對照中間檔：59 檔 · 可對照部位 1313（對上 699 · 讀法不一致 0 · 別條路徑 612 · 其他 2）
```

**1313 個裡面有 612 個進了「別條路徑」。** 那個桶子的定義是「VERIFIED 但沒有 agree
（年度財報是驗算式那條路判的）」—— 是我自己上一輪寫的。可是同一輪的另外兩列說：

```
G13 BOOKS  恆等式 ×7：INSUFFICIENT 6141     ← 驗算式一次都沒算成
G15 REGIONS 加減除驗算：INSUFFICIENT 306     ← 同上
```

**驗算式一條都沒過，那 612 個是誰判的？** 去翻部位本身：

```
part   annual.basic_eps@2024
value  4.21
state  VERIFIED
why    驗算 PASS：資料庫引擎同值
agree  （空的）
sources {"表格（TRIM）": "4.21", "原印": "4.21", "資料庫引擎": 4.21}
```

判它的不是驗算式，是**第二個讀法讀到同一個數字** —— 和那 699 個一模一樣的機制。
差別只有一個：這條路沒把 `agree`（支持採用值的來源群組數）寫下來。

### 二、根因：造部位的路有五條，寫 `agree` 的只有一條

`agree` 是 `_vote()` 算的。但 `VRN_TitleTrim_v0100.py` 裡**手工組 part dict 的路還有四條**，
每一條都把這個數字漏掉：

| 路 | 做什麼 | 語料實測 |
|---|---|---|
| `annual_parts()` | 年度財報每一格 | **612 個** |
| `_title_only()` | 標題沒印、但別處讀到的欄位 | **1 個**（`_vote` 算好了，重組 dict 時丟掉） |
| `_db_company_part()` | 公司名取資料庫 | 0（本機資料庫 ABSENT，這一輪沒走到） |
| `_db_price_part()` | 現價取資料庫 | 0（同上） |

後兩條在這台機器上量不到，但洞是一樣的 —— 操作員手上有資料庫，它們天天走。

### 三、後果：操作員自己要的那個數字，少報了 47%

操作員 2026-10-19：「相互對照兩個以上相同即算對照成功」。那條規則讀的就是 `agree`。
讀不到 → 跨來源對照只好把它當不算數：

```
對上 699 / 1313   ← 報告上印的
對上 1311 / 1313  ← 實際上
```

而且 TEMP 中間檔裡那 612 列的 `agree` 欄位是空字串，下游要套操作員那條規則也套不了。

### 四、修法：不另立第二把尺，只把判過的結果數起來

「資料庫引擎讀到的算不算同值」**上游 cell 已經判過**（`db_state` = AGREE／DISAGREE），
所以這裡不重新比數字 —— 重比就是第二顆頭。表格（TRIM）與原印是同一個讀法的前後兩面，算一組：

```python
groups = (int(bool(c0.get("printed_clean") or c0.get("printed_raw")))
          + int(any(c.get("db_state") == "AGREE" for c in cs)))
```

另外三條路同理：`_title_only` 把 `_vote` 算好的數字帶過去；兩條資料庫路各自數
它**已經算出來的**那串 `agree` 清單有幾個群組。

### 五、連儀表一起修：一個桶子不可以收兩種意思

「別條路徑」原本同時收「驗算式判的」和「根本沒寫 agree 的」，**而且是 PASS**。
一個桶子收兩種意思、又不會喊，就沒有人會去看它 —— 612 個就是這樣躺了一輪。拆成兩個：

```
別條路徑      VERIFIED、**說了**幾組但不到兩組（驗算式判的，不是第二個讀法）
沒說幾組對上   部位根本沒帶 agree —— 造部位的那條路忘了寫  → WARN，點名是哪些部位
```

### 六、又一條把缺陷寫進去保護的舊測試

跑測試紅的是一條舊的：`test_the_temp_file_marks_every_source_and_counts_by_agree`。
它的 fixture 用 `agree: ""` **代表**「驗算式判的」，並斷言 `別條路徑: 2` 且 `status PASS` ——
把「空的」當成一種意思，正好就是這一輪的缺陷。（第十四輪也遇過一次：舊測試釘住錯的那一邊。）

改法：fixture 裡驗算式判的那兩個老實寫 `agree: "1"`，「沒寫」另有自己的桶子。測試原本要守的
（「用 state 數會是 3，真的對上只有 1 個」）一字未動。

### 七、實測

| | 修前 | 修後 |
|---|---|---|
| 跨來源對照 | 對上 **699** · 別條路徑 **612** | **對上 1311** · 別條路徑 0 · 沒說幾組對上 0 |
| 兩個以上來源卻沒帶 `agree` 的部位 | **613** | **0** |
| `vrn_trim_parts.agree` 的 612 個 annual 列 | 空 | **全部 2** |
| 測試 | 402 | **410**，全過 |
| `check` / 鎖 | GREEN · 51／51 | **同** |
| 107 檔實測 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 · 驗收 59/59 | **同** |

### 八、這一輪學到的

**PASS 的那一列也要讀數字。** 這條列從頭到尾是 PASS，而它印著 612 —— 占可對照部位的 47%。
燈號對不代表內容對，閘印出來的數字自己會講話，前提是有人去讀。

**一個桶子只能收一種意思。** 「VERIFIED 但沒有 agree」把「另一條路判的」和「這條路忘了寫」
綁在一起，兩種的處置完全相反（前者正常、後者是 bug），綁在一起就等於兩種都不處理。

**同一件事有五條路做，就會有四條忘記。** 不是哪一條路寫錯，是「造部位」這件事沒有單一出口。
這一輪先把四條補齊並加守門（有兩個以上來源就一定要說幾組對上），單一出口是下一步的事。

---

## 2026-10-20 第十六輪：一標題四重點的第 2 點，105/105 份都是「未揭露」

### 一、怎麼找到的：產品的頭版那張表，一整欄只有一個值

`vrn_summary_points` 是這套系統的招牌（倉庫說明第一句就是「VRN 一題四點」）。攤開 420 列：

```
point 1  揭露 58 / 未揭露 47   不同文字 59   評等 買進 / 目標價 190.0 / 上漲空間 29.96%
point 2  揭露  0 / 未揭露 105  不同文字  1   未揭露            ← 一整欄
point 3  揭露 105             不同文字 10   主要動能來自 AI 伺服器需求…
point 4  揭露 80 / 未揭露 25   不同文字 10   催化因素：…；風險：…
```

**第 2 點是「稀釋 EPS」，105 份報告沒有一份有。** 去翻紙面：

```
98 份 PDF 的第一頁：有 EPS 字樣 51 · 沒印 47
  20250819兆豐個股報告-泓德能源(6873).pdf   我們預估泓德能源 2025 年稀釋 EPS 5.43 元，2026 年 6.87 元。
  20251128兆豐訪談速報-神達(3706).pdf      我們預估神達 2025 年稀釋 EPS 5.56 元，2026 年 7.04 元。
```

**印著，而且印得清清楚楚。**

### 二、根因：九個選用參數，倉內沒有任何呼叫端會傳

```python
def run(self, filename, chars=None, title_codes=None, table_chars=None,
        per=None, eps=None, current_price=None, source_historical=None, report_historical=None,
        official_name="", official_market=None, page_width=None, page_height=None):
```

四個呼叫端（首頁引擎自己的 CLI、資料庫引擎、AutoTestLoop 兩處）一律只給
`name / chars / page_width / page_height`。於是：

```python
point(eps and ("稀釋 EPS " + str(eps)), {"eps_diluted": eps})   # eps 永遠是 None → "未揭露"
out["target_price"] = self.fv.validate_target_price(tp, per=per, eps=eps, ...)   # PER × EPS 那一項從來沒算過
```

更糟的是引擎自己的註解寫著「第 2 點本來就獨立抽過」—— **那張安全網不存在**。
註解描述的是一條沒有人接起來的路。

### 三、修法：問冊，不要自己列詞

`knowledge/SYNONYM_LIBRARY_v4.json` 的 `scopes.financial_concept` 早就定好了，而且每一筆自帶守則：

```
稀釋每股盈餘 / 稀釋EPS / Diluted EPS  → EPS_DILUTED   guard: Do not replace basic EPS
基本每股盈餘 / 基本EPS / Basic EPS    → EPS_BASIC     guard: Do not treat as diluted EPS
```

所以照 `target_terms` 那條既有的路吸冊上的詞（`eps_terms`），**EPS_BASIC 的一個都不收**，
再加一支和 `extract_target_price` 同形狀的 `extract_diluted_eps`。`run()` 改成：
沒傳就自己從首頁讀，**傳了的照舊優先**（呼叫端拿得到更可靠的值時這裡不搶）。

一個小地方要講清楚：冊上寫「稀釋EPS」，紙上印「稀釋 EPS」。`_spaced()` 只在**字種交界處**
允許空白（「稀釋 EPS」算、「稀 釋 E P S」不算），不是把整個詞放寬。

### 四、連根因一起修：沒人傳不是錯，沒人傳又沒人說才是

引擎多一張 `RUN_INPUTS_NOT_WIRED`，九個選用輸入一個一個寫清楚**為什麼現在沒接**：

```python
"per": "本益比要從年度財報頁或本機資料庫來，而 G07 跑在那兩者之前",
"table_chars": "G15 版面還原已經在做同一件事，接起來就是第二顆頭",
"official_name": "要本機 VDF 資料庫；缺席時 header 照實印「官方名稱待查」",
...
```

測試掃**正式路徑**的呼叫端比對這張表，漏一個就紅。關鍵的一條自我約束：
**測試傳過不算接起來** —— `tests/test_VRN_FirstPageEngine.py` 自己就會傳 `official_market`，
拿它當證據，這條守門會被自己騙過去。（第一版就是這樣綠的，改成只掃 `tests/` 以外才紅。）

### 五、實測

| | 修前 | 修後 |
|---|---|---|
| 四重點第 2 點 | **未揭露 105/105** | **揭露 58**（全部 58 份 STOCK）· 未揭露 47（全部非 STOCK） |
| 第 2 點的不同內容 | 1 | **59** |
| `validate_target_price` 的 PER × EPS | 從來沒算過 | 接上了（`per` 仍未接，理由寫在表上） |
| 測試 | 410 | **415**，全過（新 5 條全部先在未修的碼上紅過） |
| `check` / 鎖 | GREEN · 51／51 | **同** |
| 107 檔實測 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 · 驗收 59/59 | **同** |

誠實交代兩個邊界：`Diluted EPS of NT$5.43` 這種「標籤和數字中間插一個 of」讀不到 ——
`extract_target_price` 有同一個限制，這一輪沒有單方面放寬它（放寬就是新規則）；
`3653健策…(3).txt` 不在四重點表裡，因為 G07 只讀 `.pdf` / `.docx`，那是另一件事。

### 六、這一輪學到的

**招牌功能也要攤開數。** 「一題四點」是這套系統對外的第一句話，而它的第 2 點在**每一份**報告上
都是空的，四個月沒有人看出來 —— 因為那張表每一輪都 GREEN：四點齊、欄位齊、主鍵不重複。
**格式對不等於內容在。**

**註解會替不存在的路作保。** 「第 2 點本來就獨立抽過」這句話讓我在上一輪讀到它時放過了一次。
下次看到註解說「這個別的地方有做」，要去把那個地方找出來，不是相信它。

**選用參數是沉默的死路。** 必填參數漏了會爆，選用參數漏了只會安靜地退回預設值。
九個選用輸入全部沒人傳，沒有任何一個地方說過 —— 這跟第十三輪「缺三支助手引擎卻一聲不響」
是同一種病。

---

## 2026-10-20 第十七輪：算出來的上漲空間，被記成「報告沒印」

### 一、怎麼找到的：把 21 張輸出表的每一欄掃過，找「整欄只有一個值」

這次把掃法推到底：**每一張表、每一欄**，如果每一列都有值而且值全都一樣，就列出來。
掃出 16 張表、50 幾欄。大部分是誠實的（合成語料本來就同一個分析師、同一個幣別、單欄頁），
但有一欄不是：

```
vrn_ticker_record   upside_pct_state = NOT_PRINTED   59/59
```

### 二、同一輪的另外兩張表，把同一個數字當成 DERIVED 印出來

```
vrn_summary_points  point 1   「評等 賣出 / 目標價 182.5 / 上漲空間 29.99% (DERIVED)」   58 份
vrn_basic_info      UpsideDownsidePct = 29.99                                      59 份
vrn_ticker_record   upside_pct       =（空）         upside_pct_state = NOT_PRINTED
                    upside_pct_calc  = 29.99         59/59 有值、11 個相異值
```

`upside_pct_calc` 與 `basic_info.UpsideDownsidePct` **59/59 完全相符**。
更直接的證據是 `cover.upside` 這個部位自己的 why：

```
state  NOT_PRINTED
why    沒印；VRN 重算 29.99%（def03）
```

**數字算出來了，只活在那句中文裡，欄位是空的、狀態寫著「報告沒印」。**
這句話我自己在第十五輪的 `_vote` 註解裡寫過一模一樣的：「只活在 why 那句中文裡，下游要驗只能去解析散文」。

### 三、根因：第十一輪補過的那一格，這一欄沒跟上

代號那幾欄在第十一輪補了 DERIVED（`put_code`）：

```python
elif derived:
    put(key, derived, "DERIVED", derived_source)     # 推算得出來，就不該記成沒讀到
```

上漲空間這一欄還是老寫法 —— 算完了才把值掛在旁邊，狀態完全不看它：

```python
put("upside_pct", up.get("value", ""), up.get("state") or "NOT_PRINTED", "首頁印的（cover.upside）")
rec["upside_pct"]["calc"] = calc          # ← 算好的值擺在這裡，沒有人看
```

### 四、修法：用它自己算好的那個數字，不另算一次

```python
if up.get("value") not in ("", None):          # 紙上印了，照舊，一個字都不改
    put("upside_pct", up["value"], up.get("state") or "NOT_PRINTED", "首頁印的（cover.upside）")
elif calc is not None:                          # 沒印、但真的算得出來
    put("upside_pct", calc, "DERIVED", "首頁沒印；VRN 重算 (目標價−現價)÷現價（現價用報告印的原始收盤價，不是 adj）")
else:                                           # 沒目標價或沒現價 —— 這時候才真的是沒印
    put("upside_pct", "", up.get("state") or "NOT_PRINTED", "首頁印的（cover.upside）")
```

三條自我約束：**不發明新狀態**（DERIVED 這一格第十一輪就在了）、**不另算一次**
（交出去的值就是 `calc`，測試直接斷言 `value is calc`）、**印了的優先**
（紙上有數字就用紙上的，重算的仍然擺在 `calc` 供對照，兩邊差多少看得見）。

### 五、實測

| | 修前 | 修後 |
|---|---|---|
| `upside_pct_state` | **NOT_PRINTED 59/59** | **DERIVED 59/59** |
| `upside_pct` 有值 | **0/59** | **59/59**（11 個相異值） |
| 值 vs `upside_pct_calc` | — | **相符 59/59** |
| 值 vs `basic_info.UpsideDownsidePct` | — | **相符 59/59** |
| G20 代號紀錄 | VERIFIED 639 · ABSENT 177 · **NOT_PRINTED 120** · SINGLE 8 | VERIFIED 639 · ABSENT 177 · **NOT_PRINTED 61 · DERIVED 59** · SINGLE 8 |
| 測試 | 415 | **419**，全過（4 條新的，2 條在未修的碼上紅過，2 條是護欄） |
| 107 檔實測 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 · 驗收 59/59 | **同** |

### 六、這一輪順手查過、結果是誠實的（負面結果照報）

| 查什麼 | 結果 |
|---|---|
| `評價法 0 句 · 方法詞 0` | 語料 51 份只有標題的「評價仍具吸引力」，沒有任何一份印本益比／DCF／EV-EBITDA —— 誠實 |
| `926708.jpg` OCR_REQUIRED | 那是 **68 bytes 的空殼 JPEG**，PIL 也認不出來 —— 刻意的「沒有文字層」樣本，誠實 |
| `src/lib/via/catalog.ts` 89 條路徑有 84 條檔案不在 | 那是**艦隊清冊**（母倉 `tonykuni/movies-dataset` 與操作員機器上的工具），不是本倉路徑 —— 不是缺陷 |
| `VRN_Method_SSOT` 33 條 defNN 裡 18 條碼裡沒提到 | 冊與冊之間互相引用（識別式的 `source` 就寫著 def10／def12），不是「沒人讀」—— 不是缺陷 |

（第三、第四條我一開始都當成缺陷，量下去才發現不是。先量再說，這一輪省掉兩次白工。）

### 七、這一輪學到的

**同一個事實在三張表上要說同一句話。** 四重點說 DERIVED、basic_info 給了數字、代號紀錄說「沒印」——
三張表都是同一輪、同一份報告、同一個數字。操作員看哪一張就得到哪一個答案。

**補過的那一格要回頭看還有誰沒跟上。** 第十一輪給代號補了 DERIVED，當時沒有回頭問
「還有哪幾欄也是推算得出來的」。這一輪就是那個沒問的問題自己長出來的。

---

## 2026-10-20 第十八輪：修好的東西，操作員在 HTML U/I 上一個字都看不到

操作員 2026-10-20：「實測實際修正自動完成**直到輸出結果驗證結果無誤於 HTML U/I 即收尾完成**」。
照這個標準回頭驗，前兩輪的修正全部不算數。

### 一、怎麼找到的：真的用瀏覽器開，不是看 curl 回 200

Chromium + Playwright，五份 HTML × 桌機 1440 與手機 390，抓 console 錯誤、頁面錯誤、
橫向溢出，再把畫面上的數字與 JSON 逐項比。render 本身乾淨（0 console 錯、0 頁錯），
但比數字的時候斷在兩個地方：

```
✓ 燈號 AMBER · FAIL 0 · WARN 19 · SKIP 1 · PASS 45     都在畫面上
✗ 「推」（DERIVED）只出現 1 次                            ← 那 1 次還是檔名裡的「上漲推升日股收漲」
✗ 貼回文字裡找不到「稀釋 EPS」
```

### 二、量出來的實況：代號紀錄這張表，收尾根本不畫

| 看得到的地方 | 有沒有代號紀錄 15 欄 |
|---|---|
| `VRN_Main_Report_v0100.html`（收尾會自動開的那份） | **沒有** |
| `VRN_AutoTest_Report.html` | 沒有（只有一列統計） |
| `VRN_Verified_Matrix_v0105.html` | 沒有（那是每檔 40 欄的驗證矩陣，不是代號紀錄） |
| `VRN_Matrix_Console_v0100.txt` | 沒有（那是**部位**矩陣，上漲% 那一欄取 `cover.upside`，照樣是 `–`） |
| `VRN_Matrix_Record_v0100.txt` | **這個檔從來沒被寫出來過** |
| `vrn_ticker_record.csv` | 有 |

程式碼裡 `RECORD_COLUMNS`、`OUT_RECORD_NAME`、`build_record_matrix()` 全都在，
`show_report_matrix(view="record")` 也有、而且矩陣引擎自己的已知答案還驗過它
（「代號紀錄矩陣：15 欄、庫／推 記號」）—— **只是一輪實測的收尾從來不叫它**
（`def_show_matrix(out, …)` 用的是預設的 `view="parts"`）。

這和第十六輪是同一種病：**宣告了、測過了、就是沒有人在正式路徑上接起來。**
結果是第十一輪（代號兩條讀法對上）與第十七輪（上漲空間 DERIVED）修好的欄位，
操作員打開 HTML 一個字都看不到。

### 三、修法：把它畫進操作員會開的那份，而且要跟來源對得上

1. **HTML 多一段「代號紀錄 · 四碼代號 → 15 欄」**。欄位、記號、狀態統計、
   連記號說明（LEGEND）**一律取自 `VRN_Matrix.build_record_matrix`**，不在 MAIN 裡另立一套。
2. **收尾順手把 `VRN_Matrix_Record_v0100.txt` 寫出來**（畫面上不再印第二張大表：
   `def_show_matrix` 多一個 `stream`，記錄那一份寫進 StringIO，只印一行檔案路徑）。
3. **UI 閘多一項**：HTML 裡的份數與「推」的格數，要和 `vrn_ticker_record.json` 對得上。
   畫了一張表、數字卻是另一回事，和「結論對不上」同一種危險。

### 四、實機截圖抓到的第二個問題

16 欄在桌機會超出畫面。第一版用 `.wide{overflow-x:auto}` 讓它在自己的框裡橫向捲 ——
捲到最右邊看得到「29.99 推」了，**但第一欄整欄空白**：看得到數字，不知道是哪一份報告。
改成第一欄 `position:sticky;left:0`，再截一次圖確認報告名跟著留在畫面上。

### 五、實測

| | 修前 | 修後 |
|---|---|---|
| HTML 有沒有代號紀錄 | **沒有** | **有** · 59 份 × 15 欄 |
| 上漲% 在畫面上 | 看不到 | **29.99 推 / 29.96 推 / 30.02 推 …** |
| `VRN_Matrix_Record_v0100.txt` | **從來沒寫出來** | 每一輪都寫 |
| UI 閘 | 6 項 | **7 項**（多「代號紀錄與 G20 相符 · 59 份 · 推 59 格」） |
| 主報告 HTML | 36,017 字 | 47,388 字 |
| 瀏覽器實測 | — | 桌機／手機各 5 頁：console 錯 0 · 頁錯 0 · 主報告橫向溢出 **False**（兩種寬度） |
| 測試 | 419 | **422**，全過（3 條新的，2 條在未修的 MAIN 上紅過） |
| 107 檔實測 | AMBER FAIL=0 WARN=19 SKIP=1 PASS=45 · 驗收 59/59 | **同** |

半路自己踩的坑：只跑 `build` 沒跑 `lock` 就去跑實測，G18 直接紅
（`ssot/VRN_TickerRecord_SSOT_v0100.json` 指紋變了）。閘擋對了 —— 鏈的順序是
`build → lock → check → run`，少一步就不算。

### 六、這一輪學到的

**「修好了」要看操作員看得到的那個畫面。** 第十一、十七輪的修正在 CSV 裡是對的、
在單元測試裡是綠的、在閘的統計數字裡也看得到 —— 唯獨操作員打開的那份 HTML 沒有。
以輸出表為終點的驗證，會漏掉「這張表沒有人畫」。

**畫面也要和來源對數字。** 新的那一段如果只是「畫出來了」，下一輪它靜靜少畫幾份也不會有人知道。
所以同一輪就把它接進 UI 閘：份數、推幾格，兩邊對不上就紅。

---

## 2026-10-20 操作員裁定：`ConfidenceScore` 改名加註（財報數字那一欄）

### 怎麼發現的

合併 main 之後把新舊輸出表再掃一次「整欄只有一個值」，掃到：

```
vrn_financial_data.ConfidenceScore          = 0.72   24,564 列全部一樣
vrn_verified_financial_data（同一欄）        = 0.72   24,564 列全部一樣
```

來源是一行字面值：

```python
# engine/VRN_Integrated_ReportDatabase_Engine.py
"ConfidenceScore": 0.72 if period.get("FiscalYear") else 0.62,
```

**它不是量出來的**，冊上也沒有任何地方定義它怎麼算。而它旁邊那一欄是 `ValidationStatus = PASS` ——
看報表的人會把 0.72 當成量測過的信心度。

這和前幾輪抓到的毛病是同一類，方向相反：前幾輪是「算出來了卻沒寫進欄位」（上漲空間、agree），
這次是「沒有算，欄位卻有數字」。

### 為什麼不自己決定

三條路都動到操作員的東西：在冊上定義它怎麼算（**發明新規則**）、把欄位拿掉（**動既有輸出契約**）、
改名加註（**命名決定**）。所以列給操作員選，不自己挑。
**操作員 2026-10-20 裁定：(3) 改名加註。**

### 做了什麼

| | |
|---|---|
| 欄名 | `ConfidenceScore` → **`ConfidenceScorePrior`**（`vrn_financial_data` 這一張，以及由它衍生的 `vrn_verified_financial_data`） |
| 表頭冊 | 出新版 **v0110**（v0109 原封保留），`changes_v0110` 一條，`zh` 寫明「固定先驗值（非量測）：年度列 0.72、非年度列 0.62，引擎寫死，沒有任何冊定義怎麼算」 |
| 值 | **一個字都沒動** —— 改的是名字與說明 |
| `vrn_basic_info.ConfidenceScore` | **不動**。那一個是 `score_basicinfo_confidence()` 真的算出來的（實測 **7 個相異值**，不是常數） |

### 實測

| | 修前 | 修後 |
|---|---|---|
| `vrn_financial_data` 的欄名 | `ConfidenceScore`（1 個相異值） | **`ConfidenceScorePrior`**（1 個相異值，值不變） |
| `vrn_verified_financial_data` | 同上 | **自動跟著改**（OutputVerify 是 `dict(r, …)` 照抄欄位，不另列清單） |
| `vrn_basic_info.ConfidenceScore` | 7 個相異值 | **7 個相異值，沒被碰到** |
| 表頭冊 | v0109 | **v0110 = v0109 + 只有宣告的那一筆**（測試用既有的 `undo_edit` 還原比對） |
| 測試 | 458 | **460**，全過 |
| `check` / 鎖 | GREEN 13/13 · 54 支 | **同** |
| 107 檔實測 | AMBER FAIL=0 WARN=20 SKIP=1 PASS=47 · 驗收 59/59 | **同** |

一條自我約束寫進測試：**改名就是改名，不可以兩個名字並存**，而且 `basic_info` 那一欄被一起改掉就要紅
（`test_v0110_is_v0109_plus_only_the_confidence_rename`、`test_the_engine_writes_the_renamed_column_and_leaves_the_measured_one`）。

### 學到的

**常數欄要分兩種看。** 「整欄同值」掃出來的東西，一種是語料誠實（同一個幣別、同一個分析師），
另一種是**程式裡寫死的數字偽裝成量測值**。後者不會讓任何閘變紅，因為它從來沒有錯過 ——
它只是從來沒有量過。

---

## 2026-10-20 第十九輪：一份個股報告拿到 0 個四重點，而兩個地方都說它過關

### 一、先說兩個「查了沒事」的大驗證（負面結果照報）

這一輪先把從來沒獨立驗過的那一塊驗掉：**年度財報表的 24,480 格數值**。

VRN 走的是帶座標的表格抽取（pdfplumber／PyMuPDF）。我用**另一條路**：只讀文字層，
照「`項目…` 那一行之後 N 行是期別，再每 (1+N) 行一組」自己解，再和 `vrn_annual_cells` 逐格比：

```
年度財報格獨立對照（24,480 格）：一致 24,480 · 不一致 0
```

第二件：**整條鏈的決定性**（這次含合併進來的 PIVOT 與驗證過的輸出）。兩輪逐檔比對 104 個輸出檔：

```
一樣 95 · 不一樣 9
```

9 個全部查過：7 個只差時間戳或輸出資料夾路徑（結構比對 0 處差異），
`VRN_Pivot_v0100.duckdb` 差 262 KB —— **把 11 張表全部讀出來逐列雜湊，內容完全相同**
（DuckDB 的檔案位元組本來就不穩定，那不是資料）。

### 二、掃到的：跨表參照完整性，有一個缺口

| 檢查 | 結果 |
|---|---|
| 每一檔都有聚焦紀錄 | ✓ 107/107 |
| 每份個股一列代號紀錄 | ✓ 59/59 |
| 每份個股一列標題分拆 | ✓ 59/59 |
| 驗證過的代號紀錄蓋滿個股 | ✓ 59/59 |
| **四重點涵蓋個股** | **✗ 58/59** —— `3653健策凱基投顧 向子慧 (3).txt` 一點都沒有 |

### 三、為什麼沒有人說

G07 的張數守則**拿自己讀到的檔當分母**：

```python
by_file = {}                                  # 只放 LAST_FOURPOINTS 裡有的
for r in LAST_FOURPOINTS: by_file.setdefault(r["file"], []).append(r["point_no"])
short = {f: nos for f, nos in by_file.items() if sorted(nos) != [1, 2, 3, 4]}
... "每一份**讀得到首頁**的報告都剛好四點，編號 1–4"
```

它自己的說明就寫著「讀得到首頁的」—— **讀不到的那一份不在分母裡**，所以它永遠 PASS。
而驗收那一側同時說 59/59 過關（`.txt` 那份 17 個部位全對，確實過關）。
兩個地方都對，合起來少掉一份報告的招牌輸出，沒有人說。

### 四、修法：讓它被看見，不替它補點

涵蓋率算在 **G20**（個股是哪幾檔要等 G17 才知道），WARN、點名：

```
WARN G20 RECORD  一標題四重點涵蓋：個股 59 檔 · 有 58 · 沒有 1
                 3653健策凱基投顧 向子慧 (3).txt —— G07 只讀 .pdf / .docx，其他格式讀不到首頁就生不出四重點（不補、照實說）
```

**不替它補點**：要補就得替 `.txt` 合成字元框，而那會生出一個來路不明的「第二個公司名來源」——
那是編值，不是讀值。要真的補，得先決定 `.txt` 的首頁怎麼定義，那是操作員的決定。

### 五、半路自己踩的坑

第一版拿 `LAST_TITLETRIM` 整份當分母 —— 它裝的是**全部 107 檔**（非個股是 `status: NOT_STOCK`），
於是那張 68 bytes 的空殼 jpg 也被算成「少了四重點的個股報告」：

```
修前（分母錯）  一標題四重點涵蓋：個股 107 檔 · 有 105 · 沒有 2   …、926708.jpg
修後            一標題四重點涵蓋：個股  59 檔 · 有  58 · 沒有 1
```

**分母錯了，WARN 就是雜訊。** 測試把這件事釘住：fixture 裡故意放一張非個股，它不准出現在結果裡。

### 六、實測

| | 修前 | 修後 |
|---|---|---|
| 沒有四重點的個股報告 | **沒有任何地方說** | **G20 一列 WARN，點名是哪一份** |
| 內層 | PASS=324 WARN=11 SKIP=7 FAIL=0 | PASS=324 **WARN=12** SKIP=7 FAIL=0 |
| 外層燈號 | AMBER FAIL=0 WARN=20 SKIP=1 PASS=47 | **同** |
| 驗收 | 59/59 | **同** |
| 測試 | 460 | **463**，全過 |

### 七、這一輪學到的

**守門不可以拿自己的產出當分母。** 「每一份讀得到的都對」永遠是真的 —— 讀不到的那一份
正是要被看見的那一份。這和第十八輪「只畫讀得到的表」是同一個毛病換個位置。

**負面結果也要留下數字。** 24,480 格獨立對照全中、兩輪輸出內容完全相同 —— 這兩件事沒有改任何程式，
但下次有人懷疑「值到底對不對」「跑兩次會不會不一樣」，有紙可查，不必重做。

## 2026-10-20 第二十輪：每一輪重生的冊，git 不知道它是機器寫的 —— 合併就把 `<<<<<<<` 寫進 JSON 裡

操作員：「解決 GITHUB 衝突問題」。

### 一、先量現況，不要先猜

兩條分支（PR #78 本支、PR #80）都從 main 的 `7693aee` 長出來。試合併一次（`git merge-tree`，
不動工作區），卡住的是這 7 個檔：

```
functional modules/VRN/VRN_REGISTRY_v0100.json
functional modules/VRN/VRN_SYSTEM_v0100.md
functional modules/VRN/ssot/VRN_EngineLock_SSOT_v0100.json
functional modules/VRN/ssot/VRN_ID_SSOT_v0100.json
functional modules/VRN/ssot/VRN_REGEX_SSOT_v0100.json
functional modules/VRN/ssot/VRN_SSOT_INDEX_v0100.json
functional modules/VRN/ssot/VRN_TickerRecord_SSOT_v0100.json
```

原始碼一個都沒有。**7 個裡 6 個是每一輪 `build`／`lock` 會整個重寫的冊，第 7 個是只往後加的日誌。**
上一次（`ff18d1c` 併 main）也是同一個形狀：5 本重生的冊 + 註冊冊 + 這份日誌 + 2 個測試檔。

這不是偶發。**只要兩條分支都跑過鏈，就一定在這幾個檔上撞車**，每一次都要人工介入。

### 二、撞車之後 git 做了什麼（實驗，不是推論）

拿一個空倉，兩邊各改同一本 JSON 冊，合併：

```json
{
  "a": 1,
<<<<<<< HEAD
  "b": 77
=======
  "b": 99
>>>>>>> other
}
```

`json.load` 當場 `JSONDecodeError`。**冊不再是冊。** 而且人就算手工接回來也只是猜 ——
下一次 `build` 本來就會把整本蓋掉；接錯了也不會有人發現，因為接出來的東西「格式對」。

這就是第十二輪那句的另一面：格式對不等於內容在。更糟的是接回來的冊會記著**另一棵樹**的指紋。

### 三、為什麼沒有人說：宣告了，但沒有人讀

`SSOT_BOOKS` 上本來就有 `generated` 旗標。查了兩件事：

1. **只標到 4 本**：REGEX、同義字、引擎鎖、AST 編號。
   漏了合併冊（`VRN_TickerRecord_SSOT_v0100.json` —— 它的說明欄明明寫著「build-book 生成」，
   可是那是散文，沒有任何程式讀得到）、INDEX 冊、借出工具冊、註冊冊。
2. **沒有任何一行程式讀它。** `grep '\["generated"\]\|get("generated")'` 在 VRN 全樹只掃到
   `def_build_index_book` 把旗標**原樣抄進 INDEX 冊**，再沒有別人。

又是同一個家族：**宣告了但沒人接**（第八輪助手引擎、第九輪快取鑰匙、第十一輪四重點第 2 點）。

### 四、修法

**1. 把宣告補齊，而且只有一份。**

- `VRN_TickerRecord_SSOT_v0100.json` 補上 `"generated": True`。
- 本身不在 `SSOT_BOOKS` 上的三個，列進新的 `GENERATED_OFF_BOOK`，**逐條寫明為什麼不在冊上**
  （註冊冊就是註冊冊本身；INDEX 冊逐本記 sha256，把自己列進去會變成記自己的指紋，寫完當場對不上；
  借出工具冊由 `VRN_ToolBridge` 自己寫、自己驗）。
- `def_generated_paths()` 把兩邊合起來 —— 之後誰要用都從這裡拿，不准另抄一份名單。

**2. 讓它真的被讀：`build` 由宣告生成 `functional modules/VRN/.gitattributes`。**

```
ssot/VRN_REGEX_SSOT_v0100.json  -merge      ← 每輪重生的 8 個檔
VRN_SYSTEM_v0100.md             merge=union ← 只往後加的日誌
```

- `-merge` = 兩邊都改過時**不要逐行併**。工作區留本地那一份（**仍是合法 JSON**），
  路徑**照樣標成衝突** —— 沒有任何東西被安靜地選掉。跑 `build`／`lock` 重生之後才算解掉。
  只有一邊改過時 git 照常直接取那一邊，行為不變。
- `merge=union` = 兩邊的輪次都留。敢這樣列是因為量過：這份日誌兩條分支相對共同祖先是
  913+/0− 與 327+/0−，**沒有任何一行是改舊的**。
- 放在 VRN 自己的資料夾，不是倉根：VRN 是獨立系統，它的合併規矩不替別的系統決定。

**3. 守門：`def_gate_gitattributes()`（P02 SSOT）。**
`.gitattributes` 要跟宣告逐字相同，不同就 FAIL。以後誰加一本 `build` 會重寫的冊卻忘了標 `generated`，
這裡就紅 —— 而不是等到下一次跨分支合併，由 git 把 `<<<<<<<` 寫進那本冊裡才發現。

**4. 一條指令：`VRN_Main_v0100.py merge --into main --apply`。**
分工刻意不對稱：

| 撞到的是 | 怎麼辦 |
|---|---|
| 宣告過的重生檔 | 跑 `build`／`lock` **整個重生**。不接、不猜、**不取一邊** |
| 只往後加的日誌 | `merge=union` 已經併好，這裡只確認它不再卡著 |
| **其他任何檔** | **停下來**。衝突標記原樣留著，合併留在進行中，由人決定 |

為什麼非得重生不可：取一邊會過 —— 冊看起來是合法 JSON、git 也不吵，可是它記的是**另一棵樹**
的指紋。那種錯要等到下一次 `check` 或下一次別的系統來借工具才爆，而那時已經推上去了。

髒樹拒絕；重生完先跑 `check`（用 `_all_check()` 同一套判準，不自己再寫一套），有 FAIL 就不提交。
預設空跑，`--apply` 才真的動 —— 和 `sync` 同一個規矩。

### 五、怎麼證明新測試不是擺著好看

10 條新測試，退回修之前的 MAIN 全部掛（2 failures + 8 errors）。其中兩條是**讀碼**而不是比清單：

- `test_build_writes_nothing_that_the_declaration_misses` —— 掃 `def_cmd_build` 的 **AST**，
  每一個 `def_write_json(<常數>, …)` 的目標都必須在宣告上。拿修之前的碼跑，它精準指出
  `INDEX_BOOK` 和 `REGISTRY_PATH` 兩個漏網的。拿清單比清單只是把同一份名單抄兩次。
- `test_a_book_whose_role_says_generated_carries_the_flag` —— 說明欄寫了「生成」就必須有旗標。
  修之前它指出 `VRN_TickerRecord_SSOT_v0100.json`。

另外三條是**真的開一個 git 倉做一次真的合併**：宣告過的冊合併後必須還是合法 JSON 且仍標成衝突；
沒宣告的 `.py` 必須照常留衝突標記（證明沒有把 git 的判斷整個關掉）；日誌兩邊的輪次都要在。

### 六、半路自己踩的坑（寫下來，因為方向對不代表能用）

`merge` 第一版拿 `def_rel(VRN_ROOT)` 當路徑前綴 —— 而那支的基準就是 `VRN_ROOT`，算出來是 `"."`。
git 回報衝突時給的是**相對倉根**的 `functional modules/VRN/...`，兩邊對不上，
於是**每一個重生檔都會被判成「要人判」**，指令每次都停在那裡。

方向是安全的（停下來，不亂解），可是指令整個沒用 —— 而且不會有任何東西說它沒用。
修法是把換算抽成 `def_generated_paths_from(root)`，merge 和測試用同一支；
測試不比字串長相，直接拿 `git ls-files` 問倉：換算出來的每一條都要真的是被追蹤的檔。

### 七、實測

| | 修前 | 修後 |
|---|---|---|
| 宣告 `generated` 的檔 | 4（而且沒人讀） | **8，`build` 與 `check` 都讀** |
| 合併時 JSON 冊 | **被寫進 `<<<<<<<`，不再是合法 JSON** | **仍是合法 JSON，但照樣標成衝突** |
| 日誌撞車 | 每次都要人工接 | **union，兩邊的輪次都留** |
| 沒宣告的檔 | 照 git 規矩 | **同（刻意不動）** |
| check | GREEN 13/13 | **GREEN 14/14**（多一道 `.gitattributes` 閘） |
| 註冊 | 161 檔 | **162 檔** |
| 測試 | 463 | **474**，全過 |

### 八、這一輪學到的

**git 不知道哪些檔是機器寫的 —— 除非有人告訴它。** 一個每輪重生的產物和一行手寫的邏輯，
在 git 眼裡沒有差別，於是它用同一套規矩對待兩者：對後者剛好，對前者是把冊弄壞。

**「說明欄寫了」不算宣告。** `VRN_TickerRecord_SSOT_v0100.json` 的 role 文字從第一天就寫著
「build-book 生成」，而旗標是空的。散文給人看，欄位給程式看 —— 只有後者會被守門讀到。

**補旗標不算修好，要有人讀它才算。** 這一輪真正的修不是多標 4 本，是讓 `build` 依它生成規矩、
讓 `check` 依它守門。旗標再完整，沒人接就還是第八、九、十一輪那個家族。

## 2026-10-20 第二十一輪：守門說「Bloomberg 代號」，數的是 Yahoo 那一欄

操作員：「繼續找下一個真缺陷」。

### 一、先說一個查錯方向的（負面結果照報，連自己踩的也報）

掃「哪些宣告沒人接」時，量到 `VRN_RunCache` 的 `DATA_NOT_READ` 說
`ssot/VRN_TickerRecord_SSOT_v0100.json`「沒有任何被快取的步驟讀它」，
而 `engine/VRN_TitleTrim_v0100.py:1278` 的 `_domain_broker()` 真的 `json.loads` 它 ——
看起來就是第九、十四輪那個毛病的第三次。**改下去之前先讀第十四輪的測試，發現它早就看過這一筆**，
而且列進 `ALLOWED`，附兩條理由。逐條驗：

| 第十四輪的理由 | 驗法 | 結果 |
|---|---|---|
| focus 那條路不會叫 `_domain_broker` | `VRN_Focus` 只用 `T.books`／`T.regions`／`T.trim`；`_domain_broker` 只在 `cover_fields` 裡，而 `cover_fields` 只被 G17 的 `analyze()` 叫 | **成立** |
| 合併冊每輪重生，算進去等於每輪必失 | 連跑兩次 `build`：第一次換指紋（因為我改過引擎 → REGEX 冊變 → 合併冊內嵌它的 sha），第二次不變 | **成立** |

所以第十四輪是對的，我的掃法（檔案層級找字串常值）太粗：**一支引擎在某個步驟的 CODE 清單上，
不等於那個步驟會跑到它的每一個函式。** 已經寫好的改動全部退掉，倉回到 HEAD，`check` 仍 GREEN。

留下來的教訓：**要推翻前一輪的判斷，先把前一輪的理由逐條驗過。** 不驗就改，是把對的改成錯的。

### 二、真缺陷：兩列相鄰、數字一模一樣

G12 的 15 欄覆蓋表：

```
yf_ticker         yfinance 代號     GATED   59/125
bloomberg_ticker  Bloomberg 代號    GATED   59/125     ← 一模一樣
```

讀碼：

```python
"yf_ticker":        sum(1 for r in rows_t if r.get("YF_TICKER")),
"bloomberg_ticker": sum(1 for r in rows_t if r.get("YF_TICKER")),   # ← 同一個欄位
```

**名字說 Bloomberg，量的是 Yahoo。** 同一個 dict 裡其他不顯然的行都帶註解
（`# v0104: local VDF database (NameDB)`、`# v0103: the printed rating is there`），這一行一個字都沒有 ——
不是刻意，是抄下來忘了改。

後果不是數字錯（兩者在這份語料剛好都是 59），是**這一列永遠不會告訴你 Bloomberg 的事**：
Bloomberg 的讀法整個壞掉歸零，它照樣顯示 59；Yahoo 壞了，它反而跟著掉。

### 三、根因在更前面：平台標籤在落檔時被丟掉

VRN 讀得到 Bloomberg 代號 —— 首頁引擎有 `rx_bb`（`([1-9]\d{3})\s+TT`），
證據核心的 `page_codes` 每一筆都帶 `kind`（yfinance／bloomberg／paren／label），
G20 的代號紀錄 `bloomberg_ticker` 是 **59/59**（VERIFIED 58 · SINGLE 1）。

可是落到 `vrn_basic_info` 的時候：

```python
"PageCodes": " | ".join(sorted({c.get("core", "") for c in ev.get("page_codes", []) if c.get("core")})),
```

**只留四碼 core，平台標籤丟了。** 三平台交叉比對的重點就是「哪個平台印的」——
丟掉平台，這一欄就不含它名字說的那件事。所以守門沒得數，只好去抄隔壁。

而且這一欄 **寫了之後沒有任何人讀**：全倉只有兩個位置提到 `PageCodes`，一個是欄位清單、
一個是寫它的那一行。冊上它的 `zh` 是**空字串** —— 四個相鄰欄位裡唯一沒有中文說明的。
沒人讀，所以沒人發現它少了一半。

### 四、修法

**1. 平台標籤一路留到表上。** `PageCodes` 改成 `<平台>:<原文>`，` | ` 相接：

```
bloomberg:6873 TT | yfinance:6873.TW
```

不加新欄、不動表結構 —— 那一欄本來就在，只是沒裝它該裝的東西。

**2. 新冊 `VRN_Output_Header_SSOT_v0111.json`**（v0110 原封保留），`changes_v0111` 一筆：
把 `PageCodes` 的 `zh` 從空字串補成格式說明，並寫明為什麼改。

**3. 守門數真的那一腳。** 新增 `def_platform_codes()` 把欄位拆回 {平台: [原文]}，
`bloomberg_ticker` 數標著 `bloomberg` 的那一腳。**舊格式（只有 core）解出來是空的**，
不是當成 bloomberg —— 守門寧可說「沒有」，也不要把不知道算成有。

### 五、怎麼證明新測試不是擺著好看

5 條新測試，退回修之前的兩支引擎全部掛（2 failures + 3 errors）。其中一條是真的守門，不是比字串：

```python
no_bb = [{"PageCodes": "yfinance:6873.TW"}, …]
self.assertEqual(count(no_bb), 0, "Bloomberg 的讀法沒了，這一列還是滿的 —— 它數的不是 Bloomberg")
no_yf = [{"PageCodes": "bloomberg:6873 TT"}, …]
self.assertEqual(count(no_yf), 2, "Yahoo 沒了不該牽動 Bloomberg 這一列")
```

**拔掉 bloomberg 那一腳這一列要掉、拔掉 yfinance 它不准動** —— 舊碼兩條都過不了。

### 六、順手拆掉一個每輪都會紅一次的測試

`test_the_book_in_use_declares_every_column_titletrim_writes` 寫死 `assertEqual(book["version"], "v0110")`，
於是每出一本新表頭冊就紅一次，而紅的原因跟它要守的事（欄位對不對）無關 —— 那種紅會教人把紅當噪音。
改成問 `ssot/` 自己：跑的那一本要是號碼最大的那一本。守的事一樣，不用每輪手改。

### 七、實測

| | 修前 | 修後 |
|---|---|---|
| `PageCodes` | 只有四碼 core，平台丟掉 | **`<平台>:<原文>`，平台留著** |
| 那一欄的 `zh` | **空字串**（沒人定義過） | **寫明格式與平台清單（冊 v0111）** |
| G12「Bloomberg 代號」 | 數 `YF_TICKER` | **數真正標著 bloomberg 的那一腳** |
| Bloomberg 壞掉時那一列 | **不會動** | **會掉** |
| check | GREEN 14/14 | **同** |
| 註冊 | 162 檔 | **163 檔**（多一本冊） |
| 測試 | 474 | **479**，全過 |

### 八、這一輪學到的

**兩列相鄰、數字一模一樣，要當成問題看。** 它可能是巧合，也可能是其中一列根本沒在量自己的東西。
這一輪就是後者，而且擺了很久沒人看出來 —— 因為那個數字「看起來很合理」。

**欄位沒人讀，就不會有人發現它少了一半。** `PageCodes` 寫了 125 份報告的資料，平台標籤丟了一半的意思，
而全倉沒有一行讀它，冊上連中文說明都沒有。第二十輪的「宣告了沒人接」換成了「寫了沒人讀」。

**推翻前一輪之前，先驗前一輪的理由。** 第一節那個誤判差一點就改下去了；救回來的不是更細的掃法，
是「去把第十四輪為什麼這樣寫讀完」。

## 2026-10-20 第二十二輪：沒跑的守門不說自己沒跑

操作員：「修掉 -Branch 預設值，然後繼續找下一個真缺陷」。

### 一、先修那個會害人拉錯碼的預設值

`Invoke-VRN-Main-v0100.ps1` 的 `-Branch` 預設值寫死 `claude/amazing-hawking-tjzssr` ——
那條分支早就不是在跑的那一條。`-Command update` 不帶參數跑下去，會**安靜地把操作員切到舊碼**，
而且跑起來一切正常，只是跑的是上個月的 VRN。

修法不是把它換成今天這一條（換了又會過期一次），是**不要寫死**：
不給 `-Branch` 就跟著現在 checkout 的那一條走（detached 才退回 `main`）。
「更新我」本來就是這個意思，而且永遠不會過期。

順手掃全倉還有沒有同一個坑：只掃到 `ssot/03_ssot/VRN_SisterLineage_Sync_v0100.json` 的
`sister_ref`，但那條分支還在、commit 也對得上，而且那是母倉的歷史同步記錄、VRN 沒有人讀它 —— 不是同一回事。

### 二、找下一個真缺陷：改用「跑了幾秒」當掃法

這一輪換一條軸 —— **耗時表**。一個閘跑了 0 秒，要嘛它真的沒事做，要嘛它根本沒跑。

```
G23 借用工具      0.000 秒   ← 0 秒，但產了 3 列（借不到 VRN-2 的工具冊，照實報）→ 誠實
G11 真值         0.000 秒   ← 0 秒，而且**一列都沒產**
```

再查三處，三處都說不出話：

| 問 | 答 |
|---|---|
| 內層 107 檔實測，G11 產了幾列？ | **0 列** |
| `truth_summary` 寫了什麼？ | **`{}`** |
| 外層 69 列裡有誰提到真值？ | **一列都沒有** |

碼：

```python
def def_gate_truth(engines, truth_path, out_dir, run_id):
    if not truth_path:
        return [], {}          # ← 靜靜回空
```

**最糟的是它不一致**：同一支函式，「真值檔給了但讀不動」會回一列 FAIL ——
所以**壞掉看得見，從來沒給看不見**。

而倉內早就有規矩：`G01` 編譯、`G03` 檔名 oracle、`G04` 稽核、`G05` 語料，
輸入缺席都會留一列 `SKIP` 說為什麼。只有 G11 不留。

後果一句話：**沒比對真值的報告，和比對過而且全過的報告，在畫面上長得一模一樣。**

### 三、修法

照 G01／G03／G04／G05 同一個規矩，缺席就留一列：

```
[SKIP] G11 TRUTH · 人工真值逐欄比對
       沒給真值檔（MAIN 的 --truth／啟動器的 -Truth）：這一輪沒有任何一欄跟人工真值比對過。
       真值檔只在操作員手上、不入庫，所以缺席是常態 —— 但沒跑不等於沒事
```

真值檔本來就只在操作員手上、不入庫，所以缺席是常態 —— **常態也要說**，
不然「沒跑」會被讀成「跑過沒事」。既有的 FAIL 路徑一個字都不動。

### 四、怎麼證明新測試不是擺著好看

4 條新測試，退回修之前的 G11：3 條掛（2 failures + 1 error），第 4 條是護欄、本來就該過。
最後一條不比字串也不讀宣告，直接把兩種輸入都跑一遍：

```python
for truth in ("", "/不存在的路徑/truth.json"):
    rows, _ = self.loop.def_gate_truth(self.loop.Engines(), truth, None, "RID")
    self.assertTrue(rows, f"truth={truth!r} 時一列都沒回")
```

**這支不管餵什麼，都不准一列都不回。**

啟動器那邊也加了 3 條：任何一支啟動器的參數預設值都不准長得像一條工作分支
（`(claude|codex|grok|via)/…`）、沒給 `-Branch` 要跟著現在這一條、改了語意要有 `.PARAMETER` 說明。
退回修之前的 `.ps1` 全部掛。

### 五、這一輪學到的

**0 秒是一條線索，不是一個數字。** 一個閘跑 0 秒，可能是它真的沒事做（G23 借不到工具，照實報了 3 列），
也可能是它根本沒被叫到。分辨方法不是看秒數，是看**它有沒有留下任何一句話**。

**同一支函式裡兩種缺席卻兩種待遇，就是漏的那一種。** G11 的「讀不動」會 FAIL、「沒給」回空 ——
一支函式自己對自己不一致，比兩支函式不一致更難被發現，因為沒有第二個地方可以比對。

**寫死的名字從寫下那一刻就開始過期。** `-Branch` 的預設值是這一輪最便宜也最危險的一個：
它不會報錯、不會變紅，只是讓人跑到舊碼。

---

## 2026-10-21 第二十三輪：第十七輪修好了三張表，第四張還在說「報告沒印」

### 一、怎麼找到的：先把兩條像缺陷的線索查死，才往下走

這一輪開場先看 107 檔實測剩下的 WARN 與 SKIP。兩條看起來很像缺陷的，**查到底之後都不是**：

| 線索 | 查法 | 結論 |
|---|---|---|
| 七條財報恆等式 6141 桶全 `INSUFFICIENT` | 翻本檔 3455 行那一則 | 已驗明：這 107 份報告紙上根本沒印營業成本／毛利／營業費用／資產／負債／權益／流通股數。`INSUFFICIENT` 是誠實的 |
| `營收 unit='%'` | 重量一次 | 本檔 1969 行那一筆已經修好 —— 現在 `營收=NT$m·scale=1e6`、`毛利率(%)=%`、`稅後淨利=NT$m`、`每股盈餘(元)=NT$` |

**要推翻前一輪的判斷，先把前一輪的理由逐條驗過。** 第二十一輪在這裡吃過一次虧
（把第十四輪已經允許的事當成新缺陷），這一輪先驗再說，省掉兩次白工。

### 二、真缺陷：同一個數字，部位說「沒印」，代號紀錄說「推算得出來」

107 檔實測，同一輪的輸出裡：

```
vrn_ticker_record   upside_pct_state = DERIVED      59/59   值 30.0 / 30.01 / 29.99 / 29.98（11 個相異值）
vrn_basic_info      UpsideDownsidePct = 29.99       59/59
vrn_summary_points  point 1「上漲空間 29.99% (DERIVED)」
vrn_trim_parts      cover.upside  value=""  state=NOT_PRINTED   59/59
                                  why="沒印；VRN 重算 29.99%（def03）"     ← 數字只活在這句中文裡
```

操作員每一輪在終端看到的**部位矩陣**，因此印：

```
部位總計：… 目標價 ✓59 · 現價 ✓59 · 上漲% –59 · 分析師 ✓59 …
記號：… – 報告沒印 …
```

**59 份報告，上漲空間全部標成「報告沒印」，而同一輪系統自己算出來的值就在隔壁那張表上。**

### 三、根因：第十七輪修的是下游那一層，上游這一格沒跟上

第十七輪（本檔 4552 行）處理的是 `VRN_TickerRecord.record_of` 裡的 `put("upside_pct", …)`，
把代號紀錄那一欄改成 `DERIVED`。但**部位本身**是 `VRN_TitleTrim.verify` 產的：

```python
if up_printed is None:
    parts.append({"part": "cover.upside", "value": "", "state": "NOT_PRINTED", "sources": {},
                  "why": f"沒印；VRN 重算 {calc:.2f}%（def03）" if calc is not None else ""})
```

`calc` 算出來了，格式化進一句中文，**欄位留空、狀態寫「報告沒印」**。
這正是第十七輪自己點名的毛病，原封不動地留在上游。第十七輪的結語寫著

> **同一個事實在三張表上要說同一句話。**

—— 這是**第四張**。而且因為部位是上游，矩陣、鎖帳本、待修清單讀的都是它。

### 四、修法：照第十七輪的三條自我約束，一條不改

```python
if up_printed is None and calc is not None:
    parts.append({"part": "cover.upside", "value": round(calc, 2), "state": "DERIVED",
                  "sources": {"VRN 重算": round(calc, 2)}, "why": UPSIDE_DERIVED_WHY + "（def03）"})
elif up_printed is None:
    parts.append({"part": "cover.upside", "value": "", "state": "NOT_PRINTED", "sources": {}, "why": ""})
```

1. **不發明新狀態** —— `DERIVED` 這一格第十一輪就在了，`MARK`／`COLOR` 兩張表早就有「推」。
2. **不另算一次** —— 交出去的就是同一行上面算好的 `calc`。
3. **印了的優先** —— 底下兩支（印了／算不出來）一個字都沒動；算不出來時仍然是誠實的 `NOT_PRINTED`。
4. **四捨五入到兩位** —— 代號紀錄與 `basic_info.UpsideDownsidePct` 本來就是兩位，幾張表要印同一個數字。

連帶三處，都是同一件事的另一半：

- **`VRN_TickerRecord`**：部位現在會交出 DERIVED，這一支照收 —— 但 why 要跟著狀態走，
  沒印的值不可以寫成「首頁印的」。**引用部位自己那句 why**，不在這裡另寫一次
  （同一句話兩個地方寫，下次只會改到一邊）。句子本身收進 `UPSIDE_DERIVED_WHY` 一個常數。
- **`VRN_Matrix` 部位總計**：那張表的狀態欄是寫死的
  `("VERIFIED","CONFLICT","SINGLE","MISSING","NOT_PRINTED","REVIEW")` —— **沒有 DERIVED**。
  不補這一欄，59 格推算值會從總計表上整個消失。順手抽成
  `TOTAL_STATES_WITH_ANNUAL` / `TOTAL_STATES_RECORD` 兩個常數，測試才守得住。
- **圖例**：「推」本來只寫在「代號紀錄另有」那一段。上漲% 這一欄開始印推，圖例沒跟上，
  操作員就會在部位那張表上看到一個圖例沒解釋的記號。

### 五、不會動到的地方（修之前先量過）

| 擔心 | 量法 | 結果 |
|---|---|---|
| 59 個新鎖、隔天全變 BROKEN | `VRN_Lock.apply`：`elif it.get("state") == "VERIFIED": lock = "NEW"` | **只有 VERIFIED 會上鎖**。DERIVED 和原本的 NOT_PRINTED 一樣落在 `OPEN`，不新增鎖、不會破 |
| 待修清單多 59 列 | `VRN_TitleTrim_SSOT.verify.fix_priority` | 清單只收 `TRIM_LOSS/TRIM_REGRESSION/CONFLICT/MISSING/REVIEW/UNMAPPED/REPORT_CHECK/SINGLE`。`NOT_PRINTED` 與 `DERIVED` 都不在裡面，前後都是 0 列 |
| G21 驗證器會剔掉 59 筆 | 代號紀錄那一欄**本來就已經是** DERIVED，而 G21 這一輪 529/529 欄全過 | 這條路早就走過，沒有新路 |

### 六、測試（先在未修的碼上證明會紅）

`tests/test_VRN_TitleTrim.py` · `def_UpsideThatVrnRecomputedIsNotNotPrintedTests`（5 條）

| 測試 | 未修的碼 |
|---|---|
| `test_not_printed_but_recomputed_is_derived_on_the_part_itself` | **紅**（`NOT_PRINTED != DERIVED`）|
| `test_the_number_does_not_live_only_in_the_prose` | **紅**（`value == ''`）|
| `test_the_part_and_the_ticker_record_say_the_same_number` | **紅**（`DERIVED != NOT_PRINTED`：兩張表當場互相矛盾）|
| `test_a_printed_upside_still_wins` | 綠（護欄：印了的那條沒被碰到）|
| `test_without_a_target_or_a_price_it_really_is_not_printed` | 綠（護欄：不過度延伸）|

`tests/test_VRN_Matrix.py` · `test_a_derived_part_is_shown_as_derived_not_as_not_printed`
—— 未修的碼上**紅**（圖例解釋不了那個記號），同時守住「格子印推」「總計表有 DERIVED 這一欄」。

`git stash push` 掉三支引擎、跑一次、`git stash pop` 還原 —— **在壞的版本上也會過的測試等於沒有測試**。

### 七、這一輪學到的

**修到下游，不等於修到了。** 第十七輪把代號紀錄那一欄改對了，量出來 59/59 DERIVED，
表上也看得見 —— 收工。但那個值是**下游重算**出來的，上游的部位仍然說「沒印」。
一個事實有幾個地方說得出口，就要幾個地方一起改；只改看得見的那一個，
下一輪換一張表看，它還在說舊話。

**寫死的狀態清單，會把新狀態吃掉而且不出聲。** `TOTAL_STATES_WITH_ANNUAL` 少一個
`DERIVED`，59 格值不會報錯、不會變紅，只是從總計表上消失 —— 和 `-Branch` 的預設值同一種安靜。
抽成常數不是為了好看，是為了讓測試有東西可以指著問「它在不在裡面」。

### 八、同一輪的續篇：外部審查在派遣器上點出兩條，查過屬實，都修

PR #81 上 Codex 留了三條 P2。**逐條量過**，兩條是真的、而且其中一條正是這個倉最在意的那件事：

**（一）`check --only` 打錯字會印 GREEN。** 未修的碼上實跑：

```
$ python3 scripts/VIA_HandleAll_v0100.py check --only typo
[HANDLE-ALL] GREEN · PASS=0 FAIL=0 SKIP=0        ← 一個系統都沒跑
$ echo $?
0
```

`if only and spec["id"] != only: continue` 把每一個系統都篩掉，`rows` 是空的，
`bad` 也是空的 → 綠燈、回 0。**一張沒跑過的體檢表，長得跟全過一模一樣** ——
和第二十二輪 G11 同一個形狀，只是這次是我自己當輪寫進去的。
修法：打錯的目標當場擋下（回 2），並把填得了的四個列出來。

**（二）失敗子行程的 stderr 被吃掉。** `(tail[-1] if tail else "") or <stderr 切片> and ""`
拆開來是 `A or (B and "")`：`tail` 空的時候，stderr 有行 → `B` 真 → 整條算成 `""`；
stderr 也空 → `[]`。argparse 錯誤、早期崩潰這些只寫 stderr 的失敗，FAIL 列上一個字都沒有。
抽成 `def_detail(done)`：stdout 最後一行優先 → stderr 最後一行 → `""`（不是 `[]`），
兩個呼叫點都改成叫它。

**（三）派遣器沒有接進 35 個短指令**（`via-handle` 還指向舊的 `VIA-Handle-All.ps1`，
而且用 `Get-Location` 拼路徑 —— cwd 相對，正是操作員那三次失敗的同一個根因）。
`grep -rln "VIA_HandleAll"` 只找得到它自己、它的測試、交接文件 —— **這一條也是真的**。

**但這一輪不推它，理由是驗不了。** 容器裡沒有 pwsh（`apt` 在沙箱裡裝不了），
而 `VIA-CmdMatrix.ps1` 是定義全部 35 個短指令的那一支：裡面一個語法錯誤，
會把操作員唯一叫得動的入口整組弄壞。推一段連 parse 都跑不過的 PowerShell 進去，期望值是負的。
**這個倉的規矩是「量不到就不要說它是對的」，同一把尺要用在自己身上。**
提案（用 `$PSScriptRoot` / `$env:VIA_ROOT` 而不是 `Get-Location`、`@args` 透傳、舊路徑留退路）
寫在 PR 的 thread 上，等倉主決定；thread 不關。

測試三條（`tests/test_via_handle_all.py`），先在未修的碼上證明會紅：

| 測試 | 未修的碼 |
|---|---|
| `test_an_unknown_only_target_is_rejected_not_reported_green` | **紅**（returncode 0、stdout 有 GREEN）|
| `test_a_failed_child_keeps_its_stderr_line` | **ERROR**（`def_detail` 根本不存在）|
| `test_a_known_only_target_still_runs_just_that_one` | 綠（護欄：擋錯字不可以順手把對的也擋掉）|

**別人指出來的缺陷，也要自己量一次再認。** 三條裡兩條當場複現、一條事實成立但修不動 ——
照單全收和照單全拒一樣懶。

---

## 2026-10-21 第二十四輪：P09 的 16 列永遠是 WARN —— 燈號在開跑前就定了

操作員：「將沒有綠的部分全部修正」。先把 20 個 WARN + 1 個 SKIP 一條一條列出來分類，
再決定哪些是真缺陷、哪些是這台機器少了東西、哪些是紙上就沒有。

### 一、量出來的分佈：20 個 WARN 裡，16 個是同一個閘

```
P04 ACCEL    加速器未載入（模組在母倉）                        1
P12 LOCALDB  找不到 vdf_tw_market.duckdb                      1
P13 LOCAL-SSOT 這台電腦沒有 03_ssot（SKIP）                    1
G00 AUTOTEST 輪內彙總                                         1
G00 BORROW   找不到 VRN-2 的工具冊                             1
P09 ACCEL    ← 16 列                                         16
```

而那 16 列裡包含這些：

```
[WARN] cache · 107 項 · 0.0 秒 · 檔案與讀法都沒變：沿用上次的還原結果     ← 最好的結果
[WARN] worker_process · 106 項 · 42.4 秒 · 掛掉 0 塊、本行程補做 0 份    ← 成功
[WARN] 逐一 · 引擎自己的逐檔順序與 upsert，不拆執行緒（判讀邏輯不可動）    ← 照設計就是不拆
[WARN] 退回 stdlib 執行緒池 · 6 項 · 一條接一條要 27.5 秒，同時跑 7.6 秒  ← 快了 3.6 倍
```

### 二、根因：判準只看車道名，完全不看它自己量到的數字

```python
ok = e["lane"] in ("accel_map", "process_mount")
rows.append(def_row("P09 ACCEL", e["action"], "PASS" if ok else "WARN", ...))
```

`items`、`seconds`、`failed_chunks` 一個都沒看。而那兩條唯一會 PASS 的車道都要
`VIA_SuperAccel_Module.py`（在母倉、不在本倉）—— 所以**這台機器上 P09 的每一列在開跑前就註定是 WARN**，
一個會跑、但答案早就寫死的閘。

更要緊的是：「加速器在不在」`P04 ACCEL` 已經判過一次，還附了怎麼補的提示。
P09 再判一次 —— **同一個判斷做兩遍，就是這個倉最忌諱的九頭龍**。

第三件事，`failed_chunks` 這個結構化數字在合併那一行被丟掉：

```python
row = merged.setdefault(key, {"action":…, "lane":…, "items": 0, "seconds": 0.0, "why": e.get("why", "")})
```

掛了幾塊只剩下 `why` 那句中文 —— 第十七輪、第二十三輪講過的同一句話，第三次出現。

### 三、修法：燈號讀結構化的事實，「加速器在不在」留給 P04

```python
def def_accel_verdict(e):
    failed = int(e.get("failed") or 0)
    if failed:                                       # 子行程真的掛了塊
        return "WARN", f"掛掉 {failed} 塊"
    if e["lane"] == "sequential" and not e.get("by_design"):
        return "WARN", "一條接一條跑，而且沒說為什麼"
    return "PASS", ""
```

- `failed` / `by_design` 一路從記錄端帶過來（`def_accel_note` 多兩個參數，合併那一行也一起帶），
  **不去解析 why 那句中文**。
- `LANE_ZH` 補上後來才加的 `cache` / `worker_process`（之前報告上直接印英文 lane 名）。
- 總覽那一列照實印車道分佈，**資訊一個字都沒少**，只是不再把「加速器不在」判第二次。

### 四、不是放寬門檻 —— 護欄先寫好

`test_serial_without_a_reason_is_still_a_warning`：真的一條接一條跑、又說不出理由，仍然 WARN。
這一條在**修之前就是綠的**，證明這一輪不是把所有東西刷成 PASS。
其餘四條（快取命中、子行程掛 0 塊、照設計逐一、整輪沒加速器但每個動作都做完）在未修的碼上全紅。

### 五、實測（107 檔，鏈序 build → lock → check → run）

| | 修前 | 修後（沒有加速器） | 修後（`--accel-home` 指到母倉） |
|---|---|---|---|
| 外層 | WARN **20** · SKIP 1 · PASS 48 | WARN **4** · SKIP 1 · PASS 64 | WARN **3** · SKIP 1 · PASS **67** |
| 輪內 | PASS 324 · WARN 11 · SKIP 8 · FAIL 0 | 同 | 同 |
| P09 車道 | 16 列全 WARN | 15 列全 PASS | `加速器 accel_map 6 · 行程掛載 3 · 快取 2 · 子行程 2 · 執行緒池 1 · 逐一 1` |
| FAIL | 0 | 0 | 0 |

**加速器路徑這個容器裡從來沒跑過。** 把 `--accel-home` 指到母倉
`VeritasIntelligenceAnalytics/supportive modules`，`SUP_MDL737_SuperAccelModule_v0110` +
`VeritasCeleritas 1.14.0` 掛得上，P04 轉綠、P09 真的出現 `accel_map` / `process_mount` 車道 ——
提示寫了很久，這一輪第一次驗證它是對的。

### 六、剩下的三個 WARN + 一個 SKIP：量過，都不是碼的問題

| 剩下的 | 查法 | 結論 |
|---|---|---|
| `P12 LOCALDB` 找不到市場 duckdb | 母倉裡也沒有 | 操作員機器上的市場庫（倉說明寫著「parquet 留本機」）|
| `P13 LOCAL-SSOT` 沒有 03_ssot | 母倉裡也沒有 | 操作員機器上的資料夾 |
| `G00 BORROW` 找不到 VRN-2 工具冊 | 母倉裡也沒有 | VRN-2 執行時自己寫的，只在操作員機器上 |
| `G00 AUTOTEST` | — | 輪內 11 WARN / 8 SKIP 的卷動 |

這三樣**沒有任何一個倉拿得到**，在操作員自己的機器上本來就會自己轉綠。
硬把它們刷成 PASS 就是說謊。

### 七、先量再說，省下一次白工：`.txt` 的四重點

輪內還剩一條 `G20 一標題四重點涵蓋：有 58 · 沒有 1`——
那一檔是 `3653健策凱基投顧 向子慧 (3).txt`，`G07 只讀 .pdf / .docx`。
打開那個檔，**四重點該有的全在紙上**（標題、評等、目標價、收盤價、EPS 預估、動能、催化、風險），
而且同一份檔 G17／G06 都讀得到（矩陣上 `3653 ✓鎖 · 健策 · KGI ✓鎖 · 賣出 ✓鎖 · 632.5 ✓鎖`）。
看起來就是個artificial的格式限制。

**所以先接起來量一次**：照 `_chars_from_docx` 的做法把 `txt_lines` 合成字元框
（txt 沒有字級，整頁同一號），餵進 `FirstPageEngine.run`：

```
公司:   | 券商: None | 日期: None
評等: None | 目標價: None | 現價: None
分析師: None | 電話: None
summary_four_points: {}
```

**全空。** 首頁引擎是靠字級與座標認版面的，`.txt` 沒有版面，接上去只會生出一個
「有欄位但每一格都空」的答案 —— 比誠實地說「讀不到」更糟。
那一列現在寫的「不補、照實說」是對的，不動。

### 八、這一輪學到的

**一個閘的每一列都是同一個燈號，那它就沒有在判斷。** 16 列全 WARN，和 16 列全 PASS
一樣沒有資訊量；差別只在前者還會把真正該看的 4 個 WARN 埋掉。
看到一整欄同一個值，不管是全綠還是全黃，都要當成問題看。

**「做完了沒」和「用了哪條路」是兩件事。** 把後者當成前者的燈號，就等於宣布
「只要環境不完美，這個閘永遠紅」—— 那不是守門，那是背景噪音。

### 九、把 `via-handle` 接到派遣台 —— 以及一句我自己說錯的話

操作員：「推那段 PowerShell」。上一則我寫著「容器裡沒有 pwsh（`apt` 在沙箱裡裝不了），所以驗不了」。
**那句話是錯的**，而且更新的答案就在這個倉自己的檔案裡 ——
`.github/workflows/powershell-lane-verify.yml` 的開頭註解：

> 2026-10-19 更正：**裝得起來。** 官方 tarball 下得到……
> 所以 .ps1 的語法、PSSA、以及**實際執行**都可以在推之前先驗，不必等這條 lane。

是另一輪的自己查出來並寫下來的，而我用的是更早的印象。**倉裡寫過的答案，比我記得的新。**

#### 裝起來，真的驗

```
pwsh 7.4.6                        （官方 tarball）
parse · 38 個檔 · 失敗 0           （CI 第二步的同一段碼）
PSScriptAnalyzer 1.24.0 · 38 個檔 · Error 0 筆   （版本從 SSOT 讀，與 CI 同一個判準）
bridge coverage: PASS (0 problems)              （CI 第四步）
```

而且**從 `/tmp` dot-source 之後實跑**（不是只看語法）：

```
via-handle where              → 倉根、四套系統的絕對路徑，全對
via-handle check --only vrn   → [CHECK] GREEN · PASS=14 · exit 0
via-handle check --only typo  → [FAIL] 沒有這個系統，一個都沒跑 · exit 2
（把派遣台拿掉）via-handle     → YELLOW HANDLE 未見派遣台…仍可用 via-entry / via-rev / via-gh
```

#### 驗出來的兩個 bug —— 都在我自己貼在 PR 上的提案裡

1. **`Find-ViaPython` 回的是陣列，不是單一路徑。** 我提案寫 `& (Find-ViaPython) $py @args`，
   那會把整個陣列當指令名。改成 `@(…) | Select-Object -First 1`。
2. **`scripts/VIA-Enter-Root.ps1` 不是「回傳倉根」的小工具。** 它是一支**會 `Set-Location` 的腳本**，
   而且底部的 `Enter-ViaProject` 會切到**母倉** `VeritasIntelligenceAnalytics`。
   我提案寫 `$root = (& "$PSScriptRoot\VIA-Enter-Root.ps1")` —— 跑起來會把人帶到別的倉去。

**紙上看起來對的碼，跑起來兩個錯。** 這就是為什麼要先裝 pwsh。

#### 實際的修法

倉根**不從 `Get-Location` 推**（操作員那三次失敗的根因就是 cwd 相對），而是照本檔最上方
`VIA-ENTER-ENV` 區塊同一組哨兵（`VIA_CentralGovernance.py` + `config/ssot/VIA_SystemMaster.via`），
從 `$PSScriptRoot` 往上找 6 層。`$env:VIA_ROOT` 排第一順位但**一樣要過哨兵** ——
因為同一支檔案裡的 `via-enter`（`Enter-ViaProject`）會把 `$env:VIA_ROOT` 改寫成母倉路徑。

找到派遣台就用受管 Python 叫它、`@args` 透傳、回傳碼照傳；找不到才退回舊的 `VIA-Handle-All.ps1`，
**原本的行為一個字沒改**。`via-entry` 加一行灰燈，說各系統的 MAIN 走 `via-handle`。

#### 測試

`test_the_short_command_via_handle_reaches_this_dispatcher`（舊檔上**紅**）守三件事：
接上了、倉根不是從 cwd 推的、找不到派遣台仍退得回舊路徑。

寫這一條的時候**又踩到同一個坑**：第一版 `assertNotIn("Get-Location", body)` 抓到的是
自己註解裡那句「**不用 Get-Location**」—— 和 `test_it_dispatches_instead_of_deciding` 第一版
一模一樣的錯。改成先把註解行濾掉再比碼。**測試要比碼，不要比說明文字**，這句話記第二次了。

### 十、接錯頭了：`via-handle` 在操作員機器上是殘樁

操作員實測回報：

```
PS C:\Users\tonyk> via-handle check --only vrn
[DEPRECATED] via-handle 已覆蓋(2026-10-08 操作員令)。改用 via-vdf / via-vrn / via-vcgc / via-view;…
2
```

**上一輪我把派遣台接到一支已經死掉的指令上。** 根因在母倉
`docs/handoff/ps/VIA-Commands-Override-v0102.ps1`（`$PROFILE` 最後一行 dot-source，操作員令 2026-10-08）：

```powershell
$keep = @('via-vdf','via-vrn','via-vcgc','via-view','via-help', …)
$old  = Get-Command -CommandType Function | Where-Object {
          ($_.Name -match '^(via-|via$|Set-VIA|Test-VIA|regen-all|selftest$)') -and ($keep -notcontains $_.Name) }
foreach ($c in $old) { Set-Item -Path ("Function:\global:" + $c.Name) -Value $body -Force }   # $body = 印一行、return 2
```

**凡是 `^via-` 又不在 keep 清單裡的，一律蓋成殘樁。** `via-handle` 正是被蓋的那一批。

我查不到這件事的原因也要記下來：覆蓋器在**母倉**、啟動器 `Invoke-VIA-Launch-v0187.ps1` 在
操作員的 `Downloads\`——**兩個都不在本倉**。上一輪我只讀了本倉的 `scripts/VIA-CmdMatrix.ps1`
就認定那裡的 `via-handle` 是活的。**改一支指令之前，要先問「這台機器上真正跑的是哪一份定義」。**

#### 修法：用一個覆蓋器掃不到的名字

`scripts/VIA-HandleAll-Shim.ps1`（新）定義兩個：

| 名字 | 會不會被蓋 | 什麼時候用 |
|---|---|---|
| `Invoke-ViaAll` | **不會**（不符合 `^via-`） | 任何載入順序都活 —— 預設用這個 |
| `via-all` | 會，如果在覆蓋器之前載入 | 放在 `$PROFILE` 之後載入才留得住 |

倉根一樣從 `$PSScriptRoot` 往上找哨兵，不看 cwd。

#### 兩種載入順序都實跑過（pwsh 7.4.6，照覆蓋器原文那段 regex 模擬）

| 順序 | `via-all` | `Invoke-ViaAll` |
|---|---|---|
| 墊片 → 覆蓋器 | `[DEPRECATED] 殘樁` · 2 | **跑得動** |
| 覆蓋器 → 墊片 | **跑得動** | **跑得動** |

`parse · 39 檔 · 失敗 0` · `PSScriptAnalyzer 1.24.0 · Error 0` · `bridge coverage: PASS (0 problems)`。

#### 派遣台自己也要說得出實話

`list` 現在印出「操作員機器上還活著的短令」（`LIVE_SHORTCMDS`，從實測來的事實，不是猜的），
以及怎麼用 `Invoke-ViaAll` 叫到它。`VIA-CmdMatrix.ps1` 的 `via-handle` 旁邊加註：那一段在操作員
機器上叫不到，要走墊片。

#### 寫測試時第三次踩同一個坑

`assertNotIn("Get-Location", text)` 這次抓到的是 **VIA-ENTER-ENV 與 PS-ACCEL20 兩個
「全庫同文、勿手改」固定區塊**裡的碼 —— 不是我寫的那一段。改成只看 `Invoke-ViaAll` 的函式體。
前兩次是抓到自己的 docstring、抓到自己的註解；這次是抓到不歸我管的固定區塊。
**比對之前先把範圍切到「我負責的那幾行」。**

#### 這一輪學到的

**接線之前，先確認那一頭是活的。** 倉裡的定義不等於機器上跑的定義 ——
中間可能隔著一層 `$PROFILE`、一份覆蓋器、一支在 `Downloads\` 的啟動器。
上一輪我驗了語法、驗了 PSSA、甚至實跑過 —— 但全部都在**我自己的容器**裡，
那裡沒有那層覆蓋器。**驗得再仔細，驗錯環境還是零分。**
