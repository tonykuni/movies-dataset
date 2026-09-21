# VIA 交接紀錄 · 側線 2026-09-21(branch `claude/busy-bell-97sa4f`;主線批號由併線的手指定 L25)

操作員令:
① 上傳五件(共識融合引擎 · VETF 封存包 · `VIA_SSOT_Additive_Audit_v0100.zip` · `SYNONYM_LIBRARY_2.json` · `VRN_WORKFLOW_SPEC.md`)「**整合優化 UNITTEST FOR ALL**」
② 「**註冊這些後更新完 VRN 相關可以進行最後一次實測收尾;開始前先檢視今天弄了什麼,有無過去的規定遺漏**」

〇 接手提示詞 → 見 docs/VIA_AI_Handover_Prompt_v*.md(尾版)。本側線的接手驗收在第八段。

## 一 · 律(本批沒有新律;引用既有律的地方逐條註明)

沒有新收到的律原文。用到的:L02/L18 七處登記 · L03 收容零觸碰 · L04 尾版律 · L17 自測只落暫存 · L22/LL49 再生冊不入 git · L25 多 AI 交會(先併主線再造件)· L30 一功能一主 · L57 誠實分母 · L70 .ps1 逐次許可 · L92 修法句 · L93 先疑尺 · L99 目標價 ADJ 口徑 · L101 一名一門 · LL34/LL306 先比 md5 · LL90 同義字裁定權在操作員 · LL199 四面登錄。

## 二 · 開始前的檢視(操作員令②的前半)

**今天到令②為止做了什麼**:5 筆 commit 只動 `docs/VIA_VDF_StatusReview_20260921.md`(VDF 唯讀審視 〇–十二段);收容夾與樞紐 v0111 複本未提交。

**對律抓到的遺漏 → 怎麼補**

| # | 遺漏 | 補法 | 證據 |
|---|---|---|---|
| 1 | L25:造件前側線落後主線 15 筆(批663–677、PR #54),Grid/Register 尾版都會寫錯 | `git merge origin/main`(零衝突,merge 2ca697c6) | 樹尾:Grid **v0430**、Register **v0240**、Deck v0157、Manager v0146、樞紐 v0110 |
| 2 | L18 七處登記一處都沒做 | 本批做齊(第三段) | MDL174 四面登錄 VRN GREEN;MDL157 shadow 被吃 0 |
| 3 | L70:改 Register 屬 .ps1 | 依令②「註冊這些」作逐次許可;走新版號檔 v0241,可刪檔回退 | Register v0241 檔頭第一行寫明 |
| 4 | VRN 索引冊釘樞紐 v0110,新版一出守門會紅 | `via-vrnbook build` 重建冊,不手改 | 守門 GREEN:指標 50 · 在位且為尾版 50 · 過期 0 |
| 5 | 尾版誤判(自己在本批踩的):把 Grid 尾版當 v0429 造了 v0430,而主線尾版**就是 v0430**,複本蓋掉主線檔 | `git checkout` 還原,改造 v0431;**尾版要用 find/glob 量,不用被 `tail` 截掉的清單猜**(L93) | Grid v0431 檔頭記著這一課 |

其餘已守住:收容零觸碰(位元相同、manifest 逐件 md5/sha256)· 先比 md5 · 包內測試只在暫存副本跑 · VIA_Reports 不入 git · 候選一律 PENDING_OPERATOR · L99 只列不裁 · 不設同意閘不裝套件。

## 三 · 本批做了什麼

**先比 md5(LL34/LL306)——五件只有一件是新料**

| 上傳 | bytes | md5 | 處置 |
|---|---|---|---|
| `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120_2.py` | 187,802 | aefb3b30… | 與 `VRN/references/intake/` 同名收容件**位元相同** → 不收第二份 |
| `VETF_FINAL_SEAL_20260829_013330.zip` | 5,006,801 | c0b6b1ee… | 解壓後 `SHA256SUMS.txt`(125 列)與 `VDF/references/intake/VETF_FINAL_SEAL_b242/` 位元相同(md5 0f538582…)→ 不收 |
| `VIA_SSOT_Additive_Audit_v0100.zip` | 146,167 | e6fe0d13… | **30 件原名原字節收於** `functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100_b20260921/` + `_INTAKE_MANIFEST_b20260921.json` |
| `SYNONYM_LIBRARY_2.json` | 172,418 | 4a946821… | = 包內 `SYNONYM_LIBRARY.json` → 不另收 |
| `VRN_WORKFLOW_SPEC.md` | 11,026 | 96ee2a83… | = 包內同名件 → 不另收 |

**第二輪附件(操作員令「整合附件」)——三件,零新料**

| 上傳 | bytes | md5 | 判定 |
|---|---|---|---|
| `VRN_WORKFLOW_SPEC_1.md` | 11,026 | 96ee2a83… | 與已收 `VRN_WORKFLOW_SPEC.md` **位元相同** → 不收 |
| `SYNONYM_LIBRARY_4.json` | 172,418 | 4a946821… | 與已收 `SYNONYM_LIBRARY.json` **位元相同** → 不收 |
| `VIA_SSOT_Additive_Audit_v0100_2.zip` | 122,931 | 64c76feb… | **更早一代的同一包**:25 件裡 21 件與已收位元相同,4 件是 v0.2.0 之前的版本(`audit_ssot.py` 無 workflow_extension 段、`SYNONYM_LIBRARY.json` 只有 4 域 393 鍵/792 筆、README 無 v0.2.0 段、DELIVERY_MANIFEST 無 content_version),缺 v0.2.0 才有的 5 件(Evidence_Core / test / EXTENSION / QA / SPEC)。**舊冊 ⊆ 新冊實證:393 鍵/792 筆在已收冊全部找得到,缺 0**;舊包自帶 30 檢在暫存副本全過 → 不收第二份(收了會成為 `ADDITIVE_GLOB` 的尾版,把讀冊口指回舊冊;只增不減不等於把舊代再擺一份)。雜湊逐件記在 manifest `prior_generation_uploads` |

包內 `baseline/` 九件對回活樹在 8e8e766f 的 blob:七件 **只差檔尾一個換行**(GitHub API 正規化)、一件只差 CRLF、一件包內沒有;零內容差。包的 `baseline_bytes_unchanged` 只證明包沒動自己的副本,manifest 另外記了對活樹的判定。

**造件(件 / 檔(版號) / 自測 n/n / 證據)**

| 件 | 檔(版號) | 自測 | 證據 |
|---|---|---|---|
| 樞紐增補讀冊口 | `supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0111.py` | **48/48**(43 舊檢一字不動 + ㊷–㊻) | `additive_library / resolve_synonym / additive_conflicts / additive_candidates`;新動詞 `additive`(rc 0 RESOLVED · 1 SOURCE_REQUIRED · 2 UNKNOWN · 3 ABSENT);`status` 多印「增補冊 OK 443 詞/7 域 · 多義 10」;3.11/3.12 `-W error` 編譯過 |
| 正主橋 | `functional modules/VRN/VRN_ENG088_SsotAdditiveBridge_v0100.py` | **19/19**(含兩負控) | `tests`:暫存副本跑包內 **30/30 + 48/48**,收容夾 sha256 前後 `8c6a193e…` 相同;`drift` 八列;`candidates` 36 條 PENDING_OPERATOR;落檔唯一出口 `_write`;`sys.dont_write_bytecode` |
| 單元測試 | `supportive modules/registry/tests/test_vrn_ssot_additive_v0100.py` | **20/20**(py3.11 與 3.12 同過) | 收容 × 樞紐 × 包內測試 × 落差 × 橋 五層;跨機器敏感點寫在檔頭(L93) |
| 規格項 | `VIA_InputConsole_Spec_v0100.json` +`vrn_ssot_additive`(vrn pipeline 群,**不進 chain_default**) | 匯流排 `matrix --profile test --ids vrn_ssot_additive` **GREEN 1.32s** | `verb=["status"]`(冊上 verb = 實跑 argv)· `test_verb=["--selftest"]` |
| 格子站 | `CGC_MDL064_SelftestGrid_v0431.py`(主線尾版 v0430) | `--only "SSOT 增補"` 2 站 OK · `--only "研報六欄規則正本樞紐"` OK | 樞紐站改名 四十三 → **四十八檢**;+增補審計橋十九檢;+增補單元測試二十檢 |
| Register + 梭 | `Register-VIA-Commands-v0241.ps1`(+`via-ssotadd`,別名 `增補審計`)· `via-ssotadd.cmd`(根,批340 契約寫法)· `bin/via-ssotadd.cmd` | MDL157 shadow:函式 166 · 別名 86 · **被吃 0 · 失門 0** | 檔頭第一行寫明 L70 逐次許可來源 |
| Deck 任務 | `CGC_MDL095_DeckServer_v0158.py` +`vrn_ssot_additive`(argv = 家族境 python → ENG088 `tests`) | **25/25**(py3.12) | 釘 89 → 90 **兩處**(① 與 ㉕ 都釘了數;第一版只改 ① 被 ㉕ 抓到) |
| Manager 正式名稱 | `VIA_SYSTEM_MANAGER_v0147.py` +任務名「研報同義字增補審計」+引擎名「同義字增補審計橋(…)」 | **10/10**(py3.12);總控頁契約測試 **19/19**(= CI 那支) | 引擎名第一版含 `SSOT`/`PENDING_OPERATOR` 被 test_05「正式名稱不得含程式識別字」抓到 → 改純中文 |
| 總控頁 | `supportive modules/ui_support/VIA_UI_MasterControl_v0100.html`(Manager 再生;LL49 唯一保留的再生頁) | test_11 tracked 頁 = 產生器 | 正式工作項目 89 → 90 · 現役引擎族 105 → 106 |
| 台帳 | `VIA_AutoCode_Registry_v0100.json` ledger +1(op ADD · 引擎) | 序列化與原檔同式(indent=2,無檔尾換行) | `updated_at` 跟著推 |
| VRN 索引冊 | `VIA_VRN_LogicArchitecture_SSOT_v0100.json`(`via-vrnbook build` 再生) | 守門 GREEN 50/50 | 只動三行:built_at、樞紐 tail/head → v0111 |
| 交接 | 本檔 + `docs/VIA_VDF_StatusReview_20260921.md` 十三段 | — | `VIA_HANDOVER_LATEST.md` 是 VCGC 再生頁,不手改 |
| VRN 啟動器修(工作站實錄修) | `Invoke-VIA-VRN-v0101.ps1`(一行:`$chainArgs = @(if ($Quick) { 'run'; '--fast' } else { 'run' })`) | 容器無 pwsh,無法實跑;依 PowerShell 語意與冊上 LL284 診斷 | 不帶 `-Quick` 時 `@('run')` 經 if 輸出被拆成字串,`@chainArgs` 對字串 splat 逐字元展開 → 鏈收到 `'r'`(操作員實錄 V2 rc=2)。L70 逐次許可=本輪令「更新完 VRN 相關可以進行最後一次實測收尾」;`via-vrnrun` 走尾版 glob,刪檔即回退 |

**沒做、且說明為什麼**

| 事 | 為什麼 | 下一步 |
|---|---|---|
| `VIA_Command_Cards_v0100.json` 再生 | `via-cmdcard cards` 在本樹跑出 330 行差:卡冊還停在 Register **v0218**,再生會一口氣補進主線 v0219–v0240 的 23 個短令,不是側線該帶的差 | 併線後在合併樹上跑一次 `via-cmdcard cards`(操作員的手) |
| `VIA_Engine_Consolidation_Register_v0100.json` | 六層鏈實跑時被某節點再生(+14 行 candidates);容器沙盒再生的冊不 commit(LL49) | 已 `git checkout` 還原 |
| CI workflow 加新測試 | `.github/workflows/via-master-control-ui.yml` 只跑總控契約那一支;改 workflow 是主線治理 | 一貼即用的兩行在第七段 |
| ENG088 進 VRN 六層索引冊 | 它是稽核件,不在六層鏈上;要歸哪一層是裁定 | 第五段 P6 |

## 四 · 實錄讀出(容器實測;工作站實測是第八段的事)

| 站 | 結果 | 讀出 |
|---|---|---|
| 樞紐 v0111 `--selftest` | 48/48 | ㊹ 只增不減實證:樞紐 38 個評等別名冊上全在、正典都在候選、`rating_words()` 66 詞全在冊 |
| ENG088 `tests` | GREEN:`audit_ssot.py` rc0 30/30 · `test_vrn_evidence.py` rc0 48/48 · 零觸碰 True | 包自帶測試在本樹的 python 3.11 也過 |
| ENG088 `drift` | GREEN 2 · YELLOW 6(表在下) | 九型代表碼**兩把尺同答**;差都在「冊上沒有的東西」 |
| ENG088 `candidates` | 36 條,一律 PENDING_OPERATOR;包自述 `mode=REVIEWABLE_CANDIDATE_NOT_INSTALLED · runtime_enabled=False` | 不替它升級 |
| 單元測試 | 20/20(3.11)· 20/20(3.12) | — |
| Deck / Manager / 契約測試(py3.12 = CI) | 25/25 · 10/10 · 19/19 | 契約測試在 origin/main 乾淨樹也是 19/19,兩盞紅是我造的、已修 |
| 格子 `--only` | 3 站 OK | 存證落 VIA_Reports(不入 git) |
| 匯流排 test profile | `vrn_ssot_additive` GREEN | 第一版 RED:冊上 `verb` 是實跑 argv,五個動詞一起丟給 argparse |
| MDL157 shadow / MDL174 四面登錄 | 被吃 0 / VRN ④ GREEN(橋 50/50 · Register 2/2 · 梭 2/2 · 格子站 在) | — |
| **六層鏈 `run --fast`(容器基礎 python,無家族境)** | GREEN 16 · RED 16 · GATED 1 · NODATA 13 → rc 1 | RED 16 = 9 `ModuleNotFoundError`(duckdb…)+ ENG060(pymupdf/openpyxl 缺)+ ENG087/MDL141/ENG080(duckdb 缺)+ ENG067(依賴鏈)+ ENG083 (53)(54);**這七盞在 origin/main 乾淨樹上一模一樣**(worktree 逐支對過)→ 容器缺家族境,不是側線造成。批677 在有家族境的容器量到 GREEN 33 · RED 0 · GATED 1 |
| ENG083 `matrix` | ABSENT:`vrn_reports.duckdb` 不在容器 | 真正的最後實測要在工作站跑 `via-vrnrun` |

**工作站實錄(操作員貼回 2026-09-21 14:56;via_vrn_312 境)**

| 你貼的 | 讀出 | 修 |
|---|---|---|
| `via-vrnrules additive` / `via-ssotadd tests|drift|candidates` | 與容器逐字同答:30/30 + 48/48 零觸碰 True;八列燈同;36 條候選 | 不動 |
| `via-selftest --only "SSOT 增補"`:橋站 OK 3.8s;**單元測試站 FAIL** test_02:活樹側 md5 `8883cc6d` ≠ 記的 `aefb3b30` | 容器裡 `8883cc6d` 正是同一檔的 **CRLF 變體**(頂層那份是 LF;把它換成 CRLF 的 md5 逐字相同)。工作站那份是 `.gitattributes -text` 加上之前 autocrlf 的舊轉換殘留;位元內容同(L93 批619 同型:尺讀原始位元組) | manifest 逐件另記 `md5_lf/sha256_lf`、重複件記 `live_md5_lf/crlf_variant_md5`;test_01/test_02 與橋 ⑦ raw 對不上就退一步比 LF 正規化 → **EOL_ONLY 自成一態不判紅**,正規化後也不同才紅。容器模擬工作站(兩份轉 CRLF)→ 20/20 綠並印 `[EOL_ONLY] 2 件` |
| `via-vrnrun` V1 冊重建 rc=0 | 冊指標 44 · 待裁定 2 | — |
| `via-vrnrun` **V2 六層鏈 rc=2:「[用法] plan \| run … (收到 'r')」** | 鏈根本沒跑。根因在啟動器第 52 行:不帶 `-Quick` 時 `@('run')` 單元素陣列經 if 輸出被 PowerShell 拆成字串 `'run'`,`via-vrnchain @chainArgs` 對字串 splat 逐字元展開 → 鏈收到 `r`/`u`/`n`(LL284 同族;批677 沒踩到是因為容器直接跑 python) | `Invoke-VIA-VRN-v0101.ps1` 一行包 `@()`。今天要跑就直接打 `via-vrnchain run`(參數走 `$args`,不經那一行) |
| V3 `via-repairprice --apply` rc=0 | 105 列 · 有改動 0 · 新拿到庫價 0;ADJ 上漲空間算得出 39(ADJ_OK 25 + 因子1 14);目標價年齡 STALE_365 15 · FRESH_90 10 · AGING_180 8 · EXPIRED_OVER_1Y 6;RAW 車道 0 | 與批675/677 同型;不動 |
| V4 `via-vrnmatrix` rc=0 | 105 份 × 7 欄 · 格子 735 · GREEN 461 · YELLOW 11 · NODATA 215 · NA 48;**判對率 100.0% = 461/461**;可判率 62.7%(扣不適用 67.1%);第二顆頭:`output/vrn_reports.duckdb` 也有 `vrn_report_basic`(09-20 07:54 舊) | ENG083 既有提示;裁定在 P9 併線後看要不要清舊庫 |
| V5 `via-console` rc=0 | 3053 KB 零 CDN 快照 | — |

**工作站六層鏈(操作員貼回 `via-vrnchain run`;同意閘 YES 是操作員的手)**

| 計 | GREEN 29 · RED 3 · GATED 0 · NODATA 14 · ABSENT 0 → RED(rc 1) |
|---|---|
| 3 紅 | `SUP_MDL746_PDFPlumberPlusHub` 九檢 FAIL 1 · `CGC_MDL141_ClosingGate` ⑭(報告夾律/主庫路徑律;工作站 64 份在 incoming)· `VRN_ENG068_DailyBrief` ⑨ 市場寬度句(features_daily 2026-09-14:530/1978)——**三支都不讀樞紐/橋**(grep SUP_MDL749/ENG088/additive 皆 0),是主線既有的工作站條件 |
| 讀樞紐的 7 支 | ENG073 · ENG074 · ENG080 · ENG083 · ENG084 · ENG085 · ENG088 **全 GREEN**(樞紐 v0111 沒有改壞任何讀冊者) |
| NODATA 14 | 12 支「沒有自測門」+ ENG072 逾時 180s(沒跑完=沒有結論)+ ENG064(rc=1 缺料) |
| 資料驗證段 | 與 V4 同一組數字(105 × 7;判對率 100.0% = 461/461) |
| 格子 `--only "SSOT 增補"` | 兩站 OK(橋 3.8s · 單元測試 9.3s)——test_02 的 CRLF 殘留已由 EOL_ONLY 一態吸收 |

對照批677 容器(有家族境):GREEN 33 · RED 0 · GATED 1 · NODATA 12。差在工作站的 3 紅與 ENG072 逾時,都不在側線範圍。

**與容器不同的一個數字**:橋 `tests` 的收容夾 sha256 容器 `8c6a193e…` vs 工作站 `9226276…`——tree_sha 連 manifest 一起算,manifest 在工作站被 autocrlf 留成 CRLF 的可能性最高(30 件收容件逐件 sha256 在工作站全對,所以差只在 manifest 本身)。零觸碰證明是同一台機器前後對,不受影響。

**drift 八列(只攤開不裁定;每列在 JSON 帶下一步)**

| 列 | 燈 | 量到 |
|---|---|---|
| TICKER_TYPES | 🟢 | 九型 16 顆代表碼樞紐 `ticker_kind` 與包內 `ticker_schema.json` 同答 |
| TICKER_V_SUFFIX | 🟡 | 正典 U/V 同歸期貨型;包把 V 另立外幣期貨型 |
| TICKER_EXTRA_TYPES | 🟡 | 包多 K/C/M/S/V 五型;冊上沒有 → 樞紐回 UNCLASSIFIED 不硬塞 |
| UPSIDE_BASIS | 🟡 | 包:口徑不合回 BASIS_MISMATCH,不套因子;律 L99:因子鏈 → 同一例 22.5%(包同口徑 25.0%)。兩套口徑同列不混 |
| BROKER_PARTIAL | 🟡 | 106 檔名:同答 76 · 只有包認得 4 · 兩邊都沒 7 · **兩邊答不同 19**(鍵橋兩邊都套) |
| DATE_PARSE | 🟢 | 106 檔名:同答 97 · 兩邊都沒 9 · 不同 0 |
| RATING_POLYSEMY | 🟡 | 冊 10 鍵多義 vs 樞紐 intake_conflicts 2;差的 8 個 = STRONG_BUY/STRONG_SELL 那把老尺(批630B) |
| KEY_BRIDGE | 🟡 | 包內 BOA→BOFA · MCQ→MACQUARIE · JP/JPMORGAN→JPM…,不在任何正典冊 |

**我自己在本批踩的坑(都已修,記著)**

1. 橋自測 ①② 第一版假紅:自測讀到自測本身 docstring 裡的「import requests」「DuckDB」字串(LL 批504/506 同族)→ 改措辭。
2. Grid 尾版誤判造成同號複本蓋掉主線檔(第二段 #5)。
3. Register 登記腳本把撞名斷言放在插入表頭之後(自己撞自己)→ 斷言移前。
4. 規格項 `verb` 語意用錯(動詞清單 vs 實跑 argv)→ 匯流排 RED → `verb=status`、`test_verb=--selftest`。
5. Manager 引擎正式名稱含拉丁識別字 → 契約測試 test_05 紅 → 純中文。
6. Deck 釘數兩處(① 與 ㉕),只改一處 → ㉕ 紅 → 兩處都改。
7. BROKER_PARTIAL 的「不同」把單邊有答混進去 → 拆成 `disagree`(兩邊都有答、答不同)與 `one_sided`(L57)。

## 五 · 掉球清單(只增不減;結案劃線)

| 代號 | 事 | 狀態 | 誰 | 下一步 |
|---|---|---|---|---|
| P1 | STRONG_BUY / STRONG_SELL 是否為獨立正典鍵(`rating_keys()` 6 鍵 vs `canon_map` 4 鍵;冊 8 個多義鍵卡在這) | 候 | 操作員 | 裁了才改 `VRN_FieldRules_SSOT rating.canon_map`(樞紐讀冊);沒裁之前判詞帶 `--source` |
| P2 | K/C/M/S/V 外幣型 ETF 納不納九型;V 是否從期貨型拆出 | 候 | 操作員 | 納之前先舉得出市場真實代號;納了改 `ticker.corrected.types_ordered` 與三平台式 |
| P3 | 上漲空間口徑:包 BASIS_MISMATCH vs L99 因子鏈 | 候 | 操作員 | 接法:ENG080 因子鏈先把目標價換 ADJ 口徑(留轉換紀錄)再呼 `compute_upside`;兩車道具名(批675 LL327) |
| P4 | 包內 KEY_BRIDGE 要不要進 `VRN_FieldRules_SSOT` broker 區 | 候 | 操作員 | 進冊由樞紐讀;不進就留在包裡 |
| P5 | 36 條候選同義字(34 alias + GFHK + 未驗 token) | 候 | 操作員 | `via-ssotadd candidates` 逐條;點頭的才進正本冊 |
| P6 | ENG088 歸 VRN 六層索引冊哪一層(目前不在鏈上) | 候 | 操作員 | `via-vrnbook build` 的歸位表 |
| P7 | 券商檔名局部識別 19 件兩把尺答不同 | 未做 | AI(裁定後) | 逐件看鍵橋/別名覆蓋;要併就提給 ENG086 `safe_broker` 正本 |
| P8 | 卡冊 `VIA_Command_Cards_v0100.json` 停在 v0218 | 操作員的手 | 操作員 | 併線後 `via-cmdcard cards` |
| P9 | 側線併入治理線 + 批號 | 操作員的手 | 操作員 | 只由一隻手併(L25);台帳/規格/索引冊取聯集 |
| P10 | 工作站最後一次實測(`via-vrnrun` V1–V5,真研報) | 操作員的手 | 操作員 | 第七段 |
| P11 | CI 只跑總控契約測試;新單元測試沒進 CI | 候 | 操作員 | 第七段兩行 |
| ~~P12~~ | ~~啟動器 v0101 在工作站實跑驗證~~ | **結案** | — | 操作員貼回 `via-vrnrun`(HEAD e3db1365,點的冊 v0241):V2 印 `=== VRN 六層鏈 · run ===`,GREEN 29 · RED 3 · NODATA 14,與直跑 `via-vrnchain run` 同答;V1/V3/V4/V5 rc=0 |
| P14 | 工作站六層鏈 3 紅(MDL746 九檢 FAIL 1 · MDL141 ⑭ · ENG068 ⑨)+ ENG072 逾時 180s | 候 | 主線 | 不在側線範圍(三支都不讀樞紐/橋);併線後由主線逐支讀 FAIL 那一行修;ENG072 可用 `via-vrnchain run --only L2` 拉長逾時看它到底要多久 |
| P13 | 工作站 `references/intake/` 有 autocrlf 舊轉換殘留(至少共識融合引擎那份) | 候 | 操作員 | `git ls-files --eol "VeritasIntelligenceAnalytics/functional modules/VRN/references/intake/VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py"` 看 w/crlf;要清就 `git rm --cached` 該檔再 `git checkout -- 該檔`(不動 blob);不清也沒事,尺已把 EOL_ONLY 分開 |

## 六 · 你的手

- 併線與批號(P9)。
- 五個裁定(P1–P6),都不急;沒裁之前系統照舊,樞紐既有判定一位元沒變。
- 工作站 `via-vrnrun`(P10):不裝套件、不設同意閘;閘沒開就把可貼的一行印出來。

## 七 · 一貼即用(工作站 PowerShell;前兩行固定)

```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
git fetch origin claude/busy-bell-97sa4f; git status --short; git log --oneline HEAD...origin/claude/busy-bell-97sa4f | head
git checkout claude/busy-bell-97sa4f      # 或在治理線上:git merge origin/claude/busy-bell-97sa4f(只由一隻手併 L25)
cd .\VeritasIntelligenceAnalytics
. .\Register-VIA-Commands-v0241.ps1        # 點源尾版(或直接打同名 .cmd 梭,梭每次現場解析尾版)
via-vrnrules                               # 一行狀態:… 增補冊 OK 443 詞/7 域 · 多義 10(按來源判)
via-vrnrules additive                      # 冊況 · 多義 10 · 對回樞紐 4 · 候選 36
via-vrnrules additive --in "Strong Buy"    # rc 1 SOURCE_REQUIRED(BUY|STRONG_BUY 都回);帶 --source institution.broker_ratings → rc 0 STRONG_BUY
via-ssotadd                                # 橋一行狀態
via-ssotadd tests                          # 暫存副本跑 30+48 檢 + 收容夾 sha256 前後對
via-ssotadd drift                          # 八列落差表(JSON 落 VIA_Reports\vrn\ssot_additive\RUN_<ts>\)
via-ssotadd candidates                     # 36 條 PENDING_OPERATOR
via-selftest --only "SSOT 增補"             # 格子兩站
via-selftest --only "研報六欄規則正本樞紐"    # 格子樞紐站(四十八檢)
python ".\supportive modules\registry\tests\test_vrn_ssot_additive_v0100.py"   # 20 檢;基礎 python 3.12 即可
via-vrnbook                                # 守門:冊已重建到樞紐 v0111(GREEN)
via-vrnchain run                           # 六層鏈直跑(不經啟動器那一行;今天就能補 V2)
via-vrnrun                                 # 批677 五步(尾版 = Invoke-VIA-VRN-v0101;V2 修了單元素陣列拆字串)
via-selftest --only "SSOT 增補"             # 單元測試站現在該綠;若有 CRLF 殘留會印 [EOL_ONLY] n 件,不判紅
```

CI 若要接新測試(主線治理,兩行;`.github/workflows/via-master-control-ui.yml`):
```powershell
$env:VIA_TEST2 = Tail (Join-Path $reg "tests") "test_vrn_ssot_additive_v*.py"   # 放在 $test 那一行旁
python "$env:VIA_TEST2"                                                          # 放在「Run isolated MasterControl contract tests」那一步之後
```

## 八 · 接手驗收(三個指令與預期)

| 指令 | 預期 |
|---|---|
| `via-vrnrules --selftest` | `[計] 48 檢 OK 48 · FAIL 0` |
| `via-ssotadd --selftest` | `[計] 19 檢 OK 19 · FAIL 0`;⑧ 印 `audit_ssot.py rc0 30/30 · test_vrn_evidence.py rc0 48/48 · 零觸碰 True` |
| `python ".\supportive modules\registry\tests\test_vrn_ssot_additive_v0100.py"` | `Ran 20 tests … OK` |
| `via-vrnrun`(或 `via-vrnchain run`) | V2 印 `=== VRN 六層鏈 · run ===` 與 `[計] GREEN n · RED n · GATED n · NODATA n`,不再是 `[用法] … (收到 'r')` |

不符就先疑尺(L93):看是哪台機器、哪個 python、收容夾有沒有被 autocrlf 動過(收容夾在 .gitattributes `-text`,不該動)。

## 九 · VRN 邏輯讀出(操作員令「讀取 session_01JaiaB5DWiYqyU6v4wcu6L1 vrn邏輯」;2026-09-21)

**那個工作階段讀不到**:`get_session` 回的是「VIA 项目接手」(2026-09-21 07:03–07:35Z · 分支 `claude/brave-goldberg-ri5k42` · 狀態 review_ready · 最後一句 `stage ⑥ running (per-stock turnover increments)`)。遠端**沒有**這條分支、全倉沒有任何 commit 帶它的 Claude-Session 尾註、ListAgents 搆不到它 → 它的工作還在那個容器裡沒 push(LL331:量出「沒有」再去樹上問一次,問過了)。要讓這裡讀得到,在那個階段打一行:`git push -u origin claude/brave-goldberg-ri5k42`。以下是**樹上現在的** VRN 邏輯,直接從六層冊讀出來,不手抄。

冊 `VIA_VRN_LogicArchitecture_SSOT_v0100.json` · schema VIA.VRN.LogicArchitecture.SSOT.v1 · 由 via_vrn_logic_book_v0104 建於 2026-09-21 05:37 · 鏈即冊(CGC_MDL172 的 44 節點就是這本冊的 layers)。

| 層 | 節點 | 這一層在做什麼 | 節點(尾版) |
|---|---|---|---|
| L0_輸入識別 | 4 | 檔名 → 股號/券商/日期;識別錯了後面全錯 | MDL030_VISVRNTickerFilenameSSOT · MDL031_VISVRNTickerRegexShim · MDL015_VISVRNBrokerAliasFullList · ENG084_FilenameTokenParse |
| L1_擷取 | 15 | 非 OCR 優先,抓不到才退 OCR;由簡到繁(批493 操作員令) | ENG082_ExtractionLogic · ENG060_TextOmni · ENG058_TableOmni · ENG057_ScanOcrRescue · ENG056_PdfForensics · ENG059_GapMultirescue · ENG075_DocToMarkdown · ENG077_OmniFormatBridge · MDL747_OcrLaneRunner · MDL746_PDFPlumberPlusHub · ENG017_MDL004OCRFetchingPDFTable · ENG018_MDL005OCRFetchingPDFText · ENG023_MDL011DailyFetcher · ENG052_DocxEngine · ENG070_YahooConsensus |
| L2_結構與知識 | 13 | 把抽出來的字變成有欄位的東西 | ENG072_FirstPageText · ENG073_ReportStructuredDB · ENG074_FinancialPages · ENG063_Lexicon · ENG064_KnowledgeStack · ENG085_MarkdownRestore · ENG086_FirstPageLogicBridge · ENG087_NLPTextSummaryBridge · ENG055_OfficeMerge · ENG066_NLPSupportHub · ENG067_MindMapSSOT · ENG071_CnyesFusion · ENG078_NLPOneBridge |
| L3_驗證 | 4 | 「有值」不等於「對」——驗過才准進矩陣(批569) | ENG083_VerifiedMatrix · ENG076_RegressionGate · MDL141_ClosingGate · ENG049_ContentReconcile |
| L4_產出 | 5 | 給人看的那一層 | ENG080_FourPointDigest · ENG068_DailyBrief · ENG079_ControlTowerDashboard · ENG062_SummarizerV1 · ENG065_MailIntel |
| L5_儲存 | 3 | L90:正典=DuckDB;其餘全是派生層,單向永不回灌 | ENG081_ParquetMainDB · ENG050_ContentStore · ENG069_ConsensusDB |

**規則正本(rule_canons;鏈上每一層都跟這 10 本拿規則,不各抄)**

| 名 | 正本 | 職責 |
|---|---|---|
| 方法冊_def01_21 | `vrn_method_kernel_v0102.py` | 方法核:def01–def21(含期間解析) |
| 六欄規則 | `SUP_MDL749_VRNFieldRuleHub_v0111.py` | 研報六欄規則正本樞紐 |
| 財務邏輯 | `SUP_MDL748_FinancialLogicHub_v0100.py` | 財務邏輯樞紐 |
| 版面樞紐 | `SUP_MDL743_GenericLayoutHub_v0100.py` | 通用版面樞紐 |
| NLP 應用 | `SUP_MDL744_NLPApplicationHub_v0102.py` | NLP 應用樞紐 |
| Markdown 結構 | `SUP_MDL745_MarkdownStructureHub_v0100.py` | Markdown 結構樞紐 |
| 階段別名 | `VIA_VRN_StageAlias_Map_v0100.json` |  |
| 繁簡轉換 | `VIA_ZhConvert_S2TWP_CharMap_v0100.json` | 批611:opencc 缺席時的凍結對照表;**函式消失不是降級,是斷線** |
| 基本資料欄 | `StockReportBasicInfo.json` |  |
| Sheet 產出計畫 | `StockReport_GoogleSheet_OutputPlan.json` |  |

**今日裁定(rulings_today)**

- 批611:簡→繁不再依賴 opencc:凍結對照表 2,784 筆(落在 VRN_ENG064_KnowledgeStack_v0102.py, VIA_ZhConvert_S2TWP_CharMap_v0100.json)
- 批615:操作員裁定:VRN 正典儲存層 = DuckDB(L90)(落在 VIA_Policy_Laws_SSOT_v0100.json#L90, VRN_ENG081_ParquetMainDB_v0101.py)
- 批615:數值入正典必須帶**宣告出來的**單位,不得由數值大小反推(LL178)(落在 VIA_Policy_Laws_SSOT_v0100.json#L90 配套②, VRN_ENG074_FinancialPages_v0111.py)
- 批615:期間拆解:1Q25 與 25Q1 同義(ENG074 檢㉑ 只比三個結構欄,不比 why)(落在 VRN_ENG074_FinancialPages_v0111.py)
- 批618:poppler 是 VRN 的活相依,列入 PATH 搬家白名單(不得盲剝)(落在 VIA_BadEnv_Blacklist_v0102.json#path_tool_anchors, via_conflict_guard_v0101.py)

**待裁定(off_book_pending,0)**


**已知缺口(known_gaps,2)**

- {"item": "財報欄位清單(FinancialData)沒有與 StockReportBasicInfo.json 對稱的正本冊", "state": "PENDING_OPERATOR", "why": "量過:VRN 夾內有 StockReportBasicInfo.json,沒有 StockReportFinancialData.json。欄位清單目前散在 ENG074 的程式碼裡。要
- {"item": "L0-L5 六層的層名(本冊第一次寫下來的那六個名字)", "state": "REVIEWED_B665", "why": "操作員批665 授權「你決定 你覆核 你完成」。**裁定:六層層名與層數維持。**改名/改層數要重做 50 個指標與 15 支歸位,換不到任何一個新的判斷力。原本提的兩個怪處,量過之後錯的不是層名,是『一支引擎只能站一層』這個假設:① L2 混著加工站

**律的綁定(law_bindings)**:["L90 VRN 正典儲存層=DuckDB(批615 操作員裁定)", "L30 一功能一主(擷取文字修復的擁有者=ENG082)", "L54 尾版律(本冊所有指標一律 glob 尾版,不寫死版號)"]

**側線在這張圖上的位置**:樞紐 `SUP_MDL749`(六欄規則正本)是 rule_canons 之一,v0111 只多讀冊口,冊已重建指到 v0111;`VRN_ENG088` 是稽核件,不在六層鏈上(不進 chain_default),歸哪一層是 P6 的裁定。工作站六層鏈實跑:讀樞紐的 7 支全綠;3 紅(MDL746 · MDL141 · ENG068)都不在樞紐/橋的讀者名單上(P14)。
