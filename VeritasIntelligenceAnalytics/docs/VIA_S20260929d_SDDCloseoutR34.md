# 側線 2026-09-29 d:三系統收尾(SDD 收尾 R34)—— 探測 · 三組修正 · 隔離整條重跑 · 鎖燈 v0107

主線批號由併線的手指定(L25)。本批接在 PR #369(f9ac2d18)之後。

## 一、操作員令(原文)

- 「close out these three projects.」
- 「activate and verify the results.」(收尾進行中追加)

解讀:三系統 = VCGC · VDF · VRN;收尾 = 工作流 VCGC-WKF004 sdd_closeout(`via-vcgc go` 實測輪 → `sdd check` → `sdd selftests` → `sdd real` → `sdd lock` → `sdd closeout`)。
**啟用** = `sdd lock --apply` 寫下一版燈鎖冊(過關就鎖);**驗證** = 鎖後再跑 `sdd check`,X-LOCK 要綠、點名的是新冊,鎖住的是尾版,判定照實。
全程經 VCGC(`VIA_FROM_VCGC=YES` · `VIA_VCGC_PUSH=NO`),同意閘不開(L07/L08),不代裝套件(容器沒有 pwsh / polars / pdfplumber / pydantic / paddleocr)。

**結果**:鎖燈 `VIA_LampLock_v0107.json`(程式指紋 8593371c7960)· 已鎖 14 · 未鎖 13 全是操作員端 · 鎖後 X-LOCK 綠 · 判定 **CLOSED_WITH_OPERATOR_ITEMS**。
過程中量到並修好 AI 端 7 件(三組修正;另有 3 個格子站名照實數),其中最後一件是第一次鎖燈之後複查才認出來的,所以撤回未提交的第一版鎖冊、整輪重跑再鎖(第五節)。

## 二、先量:探測輪(改碼之前)

探測輪 = go-20260929-052201-3017(容器重現 `via-vcgc go` 的 26 步)+ ai-r34-probe-20260929-053308(token · status · 註冊同步乾跑 · 編號乾跑 · check · selftests · real)。

| 量到的 | 所以 |
|---|---|
| Polars 批換掉 ENG079 · ENG081 · ENG085 的尾版,`sdd check` 的 X-LOCK 仍綠(「已鎖 14 條工作流,尾版都沒換」) | **X-LOCK 看不見換版**:v0100 以含版號的路徑當鍵,尾版一換就對不到,被當成沒換 |
| ENV MANAGER RED:唯一的紅是必備執行檔 `pwsh` 在 PATH 上找不到 | 裝件是操作員的手,可是驗證器沒有這種成因 → VCGC-WKF001 記成 AI 端 FAIL |
| 單一路徑驗證 RED 一步:① ENV MANAGER(同一個 pwsh) | `pathverify_dbpanel` 只認 DB 面板那一種因 → 追不到 → VCGC-WKF002 也記成 AI 端 FAIL |
| VDF_ENG089 v0106 自測 ⑤ 紅:資料家目錄在、一本庫都沒有時 ABSENT 沒講下一步 | 前版自己的律(ABSENT 要講得出先跑哪一句)在空資料家不成立 → `self:all` 紅 → VCGC-WKF003 · VDF-WKF004 FAIL |
| VDF_ENG054 v0110 自測紅 | 它要求正式庫不在,容器本機 `functional modules/VDF/output_hub`(未入倉 233 MB)有前幾回測試留下的庫。當時當成「量到容器」;第一次鎖燈後複查才認出這是工作站一定會紅的缺陷(第五節) |
| L14 全庫同步 rc 0 | 寫進的是容器本機 `output_hub/mega/vdf_tw_market.duckdb`(via_policy_factors 2027 列)—— 量到的是容器,不是倉 |
| 格子站名「增量擷取閘二十四檢」,實數 29 | 站名檢數要照實(LL213) |

探測輪 `sdd real`:AI 端 FAIL 6 條(VCGC-WKF001 · 002 · 003 · VDF-WKF001 · 003 · 004)+ VCGC-WKF004 未跑;`sdd selftests` 54 支 OK 46 · FAIL 2(rc 1)。

## 三、第一組修正(c066dd3d)

| 檔 | 改了什麼 |
|---|---|
| `CGC_MDL245_SDDValidator_v0102`(新,薄尾) | ① X-LOCK 依家族比尾版(`_family()` 去掉檔名版號);家族不在步上 = `(不在步上)` 也算換。② `fail_cause` 多兩種,只讀正主**本輪**報告(時間 ≥ 本輪第一個事件):`envmgr_exe_absent`(ENV MANAGER 的 RED 全是「⑩ 執行檔 · X(必備)」且註記「找不到」)· `pathverify_traced`(路徑驗證每一步 RED 都追得到 DB 面板 / ENV MANAGER 的成因;有一步追不到就不標) |
| `VDF_ENG089_IncrementalFetchGate_v0107`(新,薄尾) | ABSENT 且原因沒帶指令的,補上下一步(`via-datahome status` → `catalog --tables` → 抓料要操作員開同意閘);狀態不動(仍 ABSENT,不假綠) |
| `CGC_MDL064_SelftestGrid_v0502`(新) | 站名「增量擷取閘二十四檢」→ 二十九檢 |
| 工作流冊 VCGC v0101 · VDF v0100(原檔改) | VCGC-WKF001-STP004 帶 `fail_cause: envmgr_exe_absent`;VCGC-WKF002-STP002 → `pathverify_traced`(涵蓋舊的 `pathverify_dbpanel`);兩冊 `fail_cause_rule` 列四種 |

## 四、整條重跑再抓到兩件(第二組修正 74898e99)

第一次正式收尾輪(go-20260929-062335-31399,鏈**不 resume**、容器本機資料暫移)照出探測輪看不到的兩件:

| 檔 | 為什麼 · 改了什麼 |
|---|---|
| `VRN_ENG083_VerifiedMatrix_v0120`(新,全檔) | ㊸ 只讀 ENG073 **尾版**原始碼找正典表;ENG073 v0139(R33b)起是 119 行薄尾,建表字面量在前版 → 表上 0 欄 → ㊸ 紅 → VRN 鏈 RED → VCGC-WKF002 被擋。`--resume` 一直沿用舊綠,整條重跑才看得到。現在 `eng073_schema()` 沿版本鏈由新往舊讀(建表字面量取鏈上最新有 `vrn_report_basic(` 的一份,`BASIC_EXTRA_COLS` 取最新定義的一份),同一檢帶正反控;檢數仍 58 |
| `VRN_ENG082_ExtractionLogic_v0111`(新,薄尾) | `sync-db` 的 rc 2 同時涵蓋 SKIP · PARTIAL · BUSY · FAIL,中樞事件只記 rc,分不出「資料家空、沒庫可寫」與「庫忙 / 寫壞」→ VDF-WKF001-STP005 停在沒有成因的 FINDING。現在每輪把結果落成 `SYNCDB_latest.json`(state · why · targets · ok/busy/fail · explicit_db · dry_run);同步本身一字未動;自測沒指定存證夾就不寫(真目錄零觸碰) |
| `CGC_MDL245_SDDValidator_v0102`(本 PR 新檔,原檔修) | `finding_cause`:FINDING 也照正主本輪報告追因。`syncdb_no_target` = 本輪 SKIP、目標 0 本、不是乾跑、也不是指名 `--db` → 資料家空 = 操作員端。鏈上有 RED / CRASH 的工作流不替它找因;`step:` 證據跟著帶手 |
| 工作流冊 VDF v0100 · 規則文字(原檔改) | VDF-WKF001-STP005 帶 `finding_cause: syncdb_no_target`;兩冊規則補 finding_cause |
| 格子 v0502(本 PR 新檔,原檔修) | 站名「VRN 擷取中央邏輯庫十二檢」→ 二十六檢(站名早就少算,照實數) |
| VRN 六層冊重建 | ENG082 → v0111 · ENG083 → v0120 |

## 五、第一次鎖燈之後複查到第三件(84d26151)

第一次收尾輪(go-20260929-070125-14399 + ai-r34-final-20260929-071203 · 程式指紋 2109ed8140b9)已經 `lock --apply` 寫出 v0107:
已鎖 14 · 未鎖 13 全操作員端 · 鎖後 X-LOCK 綠 · CLOSED_WITH_OPERATOR_ITEMS。寫文件時回頭對探測輪的 ENG054 紅,照實量:

| 量到的 | 所以 |
|---|---|
| VDF_ENG054 v0110 的自測斷言正式庫 `VDF/output_hub/mega/vdf_tw_market.duckdb`(v0109 寫死的路徑)**不在**:`present is False` | 只有沒資料的機器才過;工作站抓過日價(正常狀態)就紅 |
| 同一台機器實量:正式庫在(206 MB)→ v0110 rc 1;正式庫暫移 → rc 0 | 第一次收尾輪的綠來自隔離,不是來自程式。鎖下去,工作站第一次 `sdd selftests` 就讓 `self:all` 紅,已鎖的 VCGC-WKF003 · VDF-WKF004 判回歸 |

所以撤回**未提交**的 v0107 與收尾報告(兩份連同那一輪的 check / real / self 存證留在 scratchpad),修好、整輪重跑、重新鎖:

| 檔 | 改了什麼 |
|---|---|
| `VDF_ENG054_TWDailyBackfill_v0111`(新,薄尾) | `db_status()` · `main()` 一字未動(平常仍讀正式庫、唯讀)。自測掛 `_load()`:只有自測設了暫存路徑才把前版載入的 `DB_TW` 換掉;五種庫況各驗一次(不在 · 從 2022-07-01 起有列 · 空表 · 起點晚於 2022-07-01 · 沒有日價表),前版自測在「暫存路徑不在」下照跑;正式庫零觸碰(不開 · 不建 · 大小與 mtime 不變)。六檢 |
| 格子 v0502(本 PR 新檔,原檔修) | 站名「台股回補工人十二檢」→ 六檢(v0110 起自測只剩 1 檢,站名早就多算) |

三組修正的登錄(對 main 實算):元件冊 新 26 · 退役 0(變更 107 = 薄尾重定義的函式 source 移到尾版);編號冊只增合併 ENG +4(VIA-VDF-ENG305 · 306 · VIA-VRN-ENG307 · 308;ENG 號碼各子系統各自一條序)· MDL +2 · FNC +127(VCGC 65 · VDF 16 · VRN 46),main 既有列 0 變、0 少;容器雜訊(FM 862 · TST 6 · 時間戳翻動)全丟;SSOT 46 本 n/sha 一致。總控頁照 LL49 重產:第一組讓 MDL245 候核名稱回正名,之後兩次重產只差時間戳,不收。

## 六、收尾輪為什麼隔離、為什麼不 resume

- **容器本機資料暫移**:`functional modules/VDF/output_hub`(未入倉 · 233 MB,前幾回容器測試留下的庫)在收尾輪期間移到 scratchpad,跑完原樣移回。
  不移的話,收尾量到的是容器的庫(探測輪的 L14 全庫同步就寫進了容器本機的庫;DB 面板在資料家缺庫時也會退回倉內預設庫)。收尾要量的是「乾淨取出的倉」。
- **空的資料家**:`VIA_DATA_HOME` 指到空的暫存夾 = 還沒抓料的工作站;要資料的步會照實落到操作員端(抓料觸網要操作員開同意閘)。
- **鏈不 resume**:VDF / VRN 鏈跑器(CGC_MDL170 / 172)的 `--resume` 會把上一回的綠照抄,**跨尾版也照抄**。ENG083 ㊸ 從 ENG073 v0139 起就紅,resume 輪一直是綠 —— 收尾輪一律整條重跑。
- **隔離不能證明工作站會綠**:隔離只排除容器汙染,反過來也會把「只在沒資料時才過」的檢查洗綠(第五節)。所以修好之後另跑一次**工作站樣**整張自測:容器本機資料放回原位 → `sdd selftests` 54 支 OK 48 · FAIL 0 · rc 0(探測輪同一環境 OK 46 · FAIL 2 · rc 1)。

## 七、收尾輪結果(啟用 + 驗證)

輪:go-20260929-075614-10789(HEAD 84d26151 · 程式指紋 8593371c7960 · 26 步 · 635 s · 鏈不 resume · 空資料家 · 容器本機資料暫移)+ ai-r34-final-20260929-080706(13 步)。

| 步 | 結果 |
|---|---|
| go 輪 · VDF 鏈 | GREEN 7 · RED 0 · GATED 1(同意閘)· NODATA 2(沒料)→ rc 4 |
| go 輪 · VRN 鏈 | GREEN 44 · RED 0 · GATED 1 · NODATA 3 · ABSENT 3(paddleocr · pdfplumber · pydantic 缺)→ rc 3;ENG083 綠(第一次正式輪是 RED) |
| go 輪 · L14 全庫同步 | SKIP · 目標 0 本(本輪 `SYNCDB_latest.json`) |
| `sdd check`(鎖前) | YELLOW:X-REQ-OPEN(既有 13 條)· X-LOCK 點名 7 處換版(下表) |
| `sdd selftests` | 54 支 · OK 48 · FAIL 0 · FINDING 2 · rc 0(另兩行 FAIL 是已宣告的 known_open:CGC_MDL154 功能驗收 · VRN_ENG073 缺 pydantic,不計) |
| `sdd real` | OK 14(VCGC-WKF004 由本輪 lock / closeout 事件補上)· 未鎖 13 全是操作員端 · AI 端 0 |
| **`sdd lock --apply`(啟用)** | **已鎖 14 · 未鎖 13 → 寫 `VIA_LampLock_v0107.json`** |
| **`sdd check`(鎖後複驗)** | **X-LOCK GREEN「已鎖 14 條工作流,尾版都沒換(依家族比 · VIA_LampLock_v0107.json)」**;整體 YELLOW 只剩 X-REQ-OPEN |
| **`sdd closeout --apply`** | **CLOSED_WITH_OPERATOR_ITEMS** · 靜態 YELLOW · 已鎖 14 · 未鎖 13(操作員端 13 · 本輪沒跑 0 · 要修 0)→ `docs/VIA_SDD_Closeout_R33_v0100.md` |

換鎖(v0106 → v0107,6 條工作流 7 個版本釘 = 鎖前 X-LOCK 點名的那 7 處;其餘 8 條尾版沒換,重新確認):

| 工作流 | 層級 | 舊 → 新 |
|---|---|---|
| VCGC-WKF003 ai_change | real | CGC_MDL245_SDDValidator v0101 → v0102 |
| VCGC-WKF004 sdd_closeout | real | CGC_MDL245_SDDValidator v0101 → v0102 |
| VDF-WKF004 vdf_daily_update | selftest | VDF_ENG054_TWDailyBackfill v0110 → v0111 · VDF_ENG081_UniverseAlign v0102 → v0103 |
| VDF-WKF005 vdf_db_governance | selftest | VDF_ENG079_LocalDbConsolidate v0103 → v0104 |
| VDF-WKF006 vatetf_pipeline | selftest | VDF_ENG085_VatetfBridge v0105 → v0106 |
| VRN-WKF005 vrn_logic_nlp | selftest | VRN_ENG082_ExtractionLogic v0110 → v0111 |

**燈鎖冊獨立核對**(不經驗證器,另寫一支直接讀冊比對):prior = v0106 · 指紋 8593371c7960 · 兩個輪號 · 14 條共 32 個版本釘全是目前的家族尾版 ·
換鎖 7 處恰等於鎖前 X-LOCK 名單 · 已鎖 / 未鎖集合與 v0106 相同 · 未鎖 13 全 `operator_hand`、`ai_open` 0 · 冊上其餘段落(舊燈鎖 locked / nodes …)除 prior 外位元組相同。

**未鎖 13 條 = 操作員的手**(驗證器照本輪報告追到的因):

| 操作員的手 | 解掉的工作流 | 下一步 |
|---|---|---|
| 裝 pwsh 並放進 PATH | VCGC-WKF001(ENV MANAGER 必備執行檔)· VCGC-WKF002(路徑驗證的紅全追到同一個 pwsh) | 工作站有 PowerShell 7 就在 PATH 上;沒有 → 裝好再 `via-vcgc go` |
| 開同意閘抓料(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`,L07/L08) | VDF-WKF001(0b GATED · 3a/3b NODATA · 資料家空:sync-db 0 本 · DB 面板 ABSENT 63 列)· VDF-WKF002 · VDF-WKF003 · VRN-WKF001(網路工具 GATED · ENG064 / ENG067 / ENG068 沒料)· VRN-WKF002(沒料 + 缺套件)· VCGC-WKF005(價史只到 2024-01-02,驗收要 2023-01-01 起) | 在**你的**視窗開閘,帶資料家跑 `via-vcgc go` |
| 裝套件 polars · pdfplumber · pydantic · paddleocr | VDF-WKF008 · VDF-WKF009 · VCGC-WKF005(QuantGuard 缺 polars)· VRN-WKF004(ENG073 ㉑㉒㉓ 要 pydantic;首頁擷取要 pdfplumber)· VRN-WKF006(pdfplumber)· VRN-WKF002 · VRN-WKF001(ENG057 paddleocr · ENG072 pdfplumber · ENG073 pydantic) | `via-install <套件>`(裝件是操作員的手,L19) |
| 正本唯讀(CANON) | VDF-WKF007 vtmra_family | 正本不改;實測走匯流排 `call --item`,要有資料家 |

與上一版比較:

| | R33c(v0106) | R34(v0107) |
|---|---|---|
| 程式指紋 | 040178d7f8e1 | 8593371c7960 |
| 實測輪 | go-20260929-014327-2328 | go-20260929-075614-10789(整條重跑 · 隔離 · 空資料家) |
| 已鎖 / 未鎖 | 14 / 13 | 14 / 13(同一組;7 處換鎖到新尾版) |
| 未鎖裡 AI 端 | 0 | 0(探測輪時 6 條 AI 端 FAIL,全數修好或追到操作員端的因) |
| X-LOCK | 綠(以含版號路徑比,看不見換版) | 綠(依家族比) |
| 判定 | CLOSED_WITH_OPERATOR_ITEMS | CLOSED_WITH_OPERATOR_ITEMS |

收尾報告沿用驗證器寫死的檔名 `docs/VIA_SDD_Closeout_R33_v0100.md`(標題也寫死「R33」),內容是本輪 R34 的(產生時間 · 指紋 · 輪號見檔頭);見待辦。

## 八、驗證

| 項 | 結果 |
|---|---|
| 收尾輪(啟用 + 鎖後複驗) | 見第七節:lock --apply 寫 v0107 · 鎖後 X-LOCK GREEN · CLOSED_WITH_OPERATOR_ITEMS |
| 燈鎖冊獨立核對 | 32 個版本釘全是尾版 · 換鎖 7 = X-LOCK 名單 · 未鎖 13 全操作員端 · 其餘段落位元組相同 |
| 追因(本輪報告) | VCGC-WKF001-STP004 → 缺必備執行檔 pwsh · VCGC-WKF002-STP002 → 路徑驗證的紅全追到 pwsh · VDF-WKF001-STP005 → 資料家空(sync-db SKIP · 目標 0 本) |
| 工作站樣整張自測(容器本機資料在) | 54 支 · OK 48 · FAIL 0 · FINDING 2 · rc 0(探測輪同環境 OK 46 · FAIL 2 · rc 1) |
| ENG054 v0111 兩種環境 | 正式庫在(206 MB):v0111 6/6 rc 0 · v0110 rc 1;正式庫不在:v0111 6/6 rc 0 · v0110 rc 0;正式庫大小與 mtime 前後一致 |
| ENG073 的 3 個 FAIL | 單跑 61/64,㉑㉒㉓ 全是「正典載入失敗 ModuleNotFoundError: pydantic」→ 裝件,不是藏在 ABSENT 底下的缺陷 |
| 突變 | 37/37 全抓:CGC_MDL245 v0102 20 · VRN_ENG082 v0111 5 · VDF_ENG089 v0107 4 · VRN_ENG083 v0120 2 · VDF_ENG054 v0111 6(ENG054 在正式庫存在的環境跑) |
| 擊斃閘 v0103 `--base origin/main --run-selftest` | 通過 rc 0 · 判 17 檔 · 11 條全過 · 既有債 2(ENG083 · 格子的既有撞號) |
| 格子 v0502 `--only` | 增量擷取閘 · VRN 擷取中央邏輯庫 · VRN 驗證矩陣 · 台股回補工人 四站 OK |
| VCGC `val`(驗證 SSOT) | GREEN · 八道規則全綠 · 交叉代碼 22 |
| VCGC `sdd check`(提交前) | YELLOW:X-REG · X-NUM 綠(新檔都已登錄、編號);只剩既有 X-REQ-OPEN 與 X-LOCK 點名換版(鎖後轉綠) |
| 編號冊 | 46 本 n/sha 一致;對 main 既有列 0 變 · 0 少 |
| 容器狀態還原 | 每一輪跑完都照清單還原容器重產的已追蹤檔(教訓冊 · 布建帳 · 引擎整併冊 · 功能驗收 / 自動編碼頁 · VapStack);容器本機資料原樣移回(233 MB) |

## 九、教訓(照實記)

- **鎖用含版號的路徑當鍵,等於沒鎖**:尾版一換,舊鍵對不到,被當成「沒換」。X-LOCK 要依家族比尾版;家族不在步上也算換。
- **隔離只排除汙染,不保證工作站會綠**:收尾輪把容器本機資料暫移,量到乾淨的倉;可是 ENG054 v0110 的自測正好要求「沒有正式庫」,隔離讓它綠、工作站會紅。鎖之前要在有資料的環境(工作站樣)再跑一次整張自測。
- **斷言「某個真路徑不在」的自測,把環境寫進了測試**:自測要改用暫存路徑,在有資料 / 沒資料兩種機器各跑一次當正反控。
- **鎖冊提交前可以撤,提交後只能開下一版**:第一次鎖燈沒提交就先複查,查到問題撤回重跑,冊號仍是 v0107,歷史乾淨。
- **`--resume` 會跨尾版照抄舊綠**:ENG083 ㊸ 從 ENG073 v0139 起就紅,resume 輪一直綠。收尾輪一律整條重跑;跑器要記每站的尾版,換版就作廢那一站的綠(待辦)。
- **讀原始碼的檢查碰到薄尾會失明**:ENG083 ㊸ 只讀 ENG073 尾版,薄尾之後建表字面量在前版 → 0 欄。凡是剖析原始碼的檢查都要沿薄尾鏈走(與 Polars 批「薄尾要讓兩個讀者都看懂」同一類)。
- **一個 rc 多種意思,驗證器就追不到因**:`sync-db` 的 rc 2 同時是 SKIP · PARTIAL · BUSY · FAIL,中樞事件只記 rc。正主要落一份本輪報告,驗證器只讀本輪那一份。
- **成因只認本輪報告**:報告時間要 ≥ 本輪第一個事件,舊報告不能拿來替這一輪的 FAIL / FINDING 開脫(突變 M2 · M5 · M13 就是在驗這一條)。
- **VCGC 回紅會記進教訓冊**:收尾輪的 `sdd real` / `sdd selftests` 回 1(別條工作流在操作員端)· ENV MANAGER / 路徑驗證回 1 都會被記成重複出錯(一輪 7 筆);照規矩逐輪 `git checkout --` 還原,不入倉。
- **背景等待別用會比中自己的 `pgrep -f`**:`until ! pgrep -f merge_numbering.py` 的命令列本身就含這個字串,永遠等不完;改寫成 `pgrep -f "merge_numbering[.]py"`。

## 十、待辦(本批做不到或不在範圍,照實交出)

| 項 | 為什麼本批不做 | 下一步 |
|---|---|---|
| 鏈跑器 `--resume` 跨尾版照抄舊綠(CGC_MDL170 · CGC_MDL172) | 收尾輪以整條重跑繞過;改跑器是另一件治理件新版 | 新版:resume 狀態記每站的尾版,換版就作廢那一站的綠,再補一條正反控 |
| DB 面板在資料家缺庫時退回倉內預設庫 | 本輪以暫移容器本機資料繞過 | DB 面板新版:資料家缺庫就照實報缺,不退回倉內 |
| 收尾報告檔名與標題寫死 R33(`docs/VIA_SDD_Closeout_R33_v0100.md`) | 驗證器改碼會換指紋,整輪要重跑;本輪內容是 R34,由本文件說明 | 下一版驗證器:標題帶輪號(由工作流冊或參數給),檔名固定一個「最新」名 |
| 編號冊既有列刷新(updated_at · 使用者 · 燈號 · TST 列;含格子改名的站) | 容器只補新鍵;這些欄位該由正本環境給 | 工作站(選做):`via-vcgc run --family core CGC_MDL237_NumberingSystem --apply` 然後 `via-vcgc sdd check` |
| CGC_MDL223 座位上傳只提交座位檔(承 S20260929c) | VCGC 治理件,不在本批範圍 | 新版:`git commit -m … -- <座位檔>`;有 MERGE_HEAD 或暫存區有別的檔就回 `held` |
| VCGC v0172 薄尾偵測也要認 `STEM = "<家族>"`(承 S20260929c) | main 既有缺口 | VCGC 新版把條件放寬成 `_?STEM`,補正反控,再 `registry-sync --apply` |
| Polars 一致性 ⑫(承 S20260929c) | 容器沒有 polars,依規不代裝 | 工作站裝 polars 後 `via-vcgc run --family core SUP_MDL755_VIAPolarsFrame probe` |

## 十一、還原

- 刪本批新檔,即回到尾版律的前一版:CGC_MDL245 v0102 · VDF_ENG089 v0107 · VDF_ENG054 v0111 · VRN_ENG082 v0111 · VRN_ENG083 v0120 · 格子 v0502。
- 燈鎖冊:刪 `VIA_LampLock_v0107.json`,v0106 回到尾版(刪了新檔之後尾版也回到 v0106 鎖的那一組)。
- 工作流冊兩本 · VRN 六層冊 · 元件冊 · 編號冊(ENG · MDL · FNC_VCGC · FNC_VDF · FNC_VRN)與 `VIA_Numbering_SSOT_v0100.json` · 總控頁 · 收尾報告 · 流水帳:`git restore --source=f9ac2d18` 對應檔(= 本批之前的 main)。
