# S20261014 收尾一鍵:隔離區找回 · AI 常用動作引擎 · 輸出表頭全面 + DataFrame 固定 · 自壓頁五支 · 一支 PS 串全部

操作員 2026-10-14(逐字,需求冊 v0193 VCGC-REQ180/181/182 入冊):
「丟失的文件可到隔離區尋找　修正完善收尾功能不要發散　ＶＤＦ　ＶＲＮ　輸出ＨＥＡＤＥＲ還要檢查權全面　自動更新台股權清單及主動式台股ＥＴＦ全清單
ＥＴＦ資料要抓到ＮＡＶ　ＡＵＭ　ＣＡＳＨ　ＩＮＦＬＯＷ　ＡＮＤ　ＯＵＴ　ＦＬＯＷ　ＡＮＤ　ＢＲＥＡＫＤＯＷＮ　輸出ＨＥＡＤＥＲ完整確認然後ＤＡＴＡＦＲＡＭＥ固定
ＤＡＤＡＢＡＳＥ結構最佳化省ＡＰＩ擷取ＴＯＫＥＮ及ＡＩ讀取現況　回顧對話紀錄ＡＩ常做的動作做引擎讓ＡＩ啟動接受結果在反饋以節省ＴＯＫＥＮ
… 整合起來進一個ps指令一起執行 …」→「繼續收尾 開PR 綠了就合併 給我一個指令去完成以上全部」

## 一、一個指令(工作站)

```powershell
pwsh -NoProfile -File VeritasIntelligenceAnalytics\launchers\Invoke-VIA-OneShot-v0100.ps1 -Consent -Apply -Since 2023-06-01
```

- `-Consent` = 操作員親手開同意閘(只在本行程設 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`=YES,跑完還原);AI 不代打。
- `-Apply` = 寫入(ENG094 進庫 · DataFrame 鎖帳 · VCGC closeout --apply);仍不 push(`VIA_VCGC_PUSH=NO`)。
- 不帶旗標 = 乾跑 + 同意閘關(抓網段只看計畫 / SKIP)。其他:`-Grid`(格子整張重跑)· `-Only 1,5,10` · `-NoOpen`。
- 跑完自動跳出 `VIA_Reports\aiops\AIOPS_RUN_latest.html`(15 段燈號表);結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件。

## 二、十五段(各系統走自己的入口 / 管理器,L120)

| # | 段 | 正主 |
|---|---|---|
| 1 | VCGC 省 Token | CGC_MDL149 `token` |
| 2 | VCGC 交接 check | CGC_MDL149 `handoff check` |
| 3 | 隔離區找回(丟失檔) | CGC_MDL276 `lost` |
| 4 | AI 庫卡 | CGC_MDL277 `dbcard` |
| 5 | 台股清單 + 主動式台股 ETF 全清單 → 全步擷取 | Invoke-VIA-VdfFetch 尾版(v0108) |
| 6 | 主動 ETF NAV · AUM · 單位數 · 淨流入 / 流出 | VDF_ENG094 `fetch` |
| 7 | 主動 ETF 持股 / 產業 breakdown | VDF_ENG094 `breakdown` |
| 8 | VDF 管理器 | VDF_SystemManager 尾版 `status` |
| 9 | VRN 管理器 | VRN_SystemManager 尾版 `status` |
| 10 | 輸出表頭全面 + DataFrame 固定 | CGC_MDL249 `all` |
| 11 | PS 檢查(加速器橋 · 自壓頁) | CGC_MDL277 `pslint` |
| 12 | 撞號(對 origin/main 新增) | CGC_MDL277 `collide` |
| 13 | 整合全景實測 | CGC_MDL248 FullCheck |
| 14 | VCGC 收尾 | CGC_MDL149 `closeout` |
| 15 | AI 狀態索引 | CGC_MDL277 `status` |

## 三、新件

- **CGC_MDL276_QuarantineRecover v0100**:隔離區(`functional modules/VIA_RetiredEngines` · `VIA_RetiredEngines`)索引 446 檔(清單 414 · 無清單批次推回 32);`lost` 掃登記冊引用 → 丟失 0;`restore` 只複製、核 sha256、目的地有檔拒絕,隔離區沒有才從 git 取回;只增帳。自測 7/7。
- **CGC_MDL277_AiOps v0100**:AI 每輪重做的動作 → 一個動詞一張卡。`status`(93 份報告判決 + 交接頭 · etag / 304)· `dbcard`(輸出庫每表列數 · 日期區間,先看卡再決定抓不抓)· `collide --base`(只報新增撞號)· `pslint`(重用 FullCheck + BridgeSweeper)· `killgate` · `report`。自測 6/6。
- **CGC_MDL249_DataFrameLock v0101**:+json 型別 · `coverage`(VDF / VRN 全部輸出庫每表 vs 表頭冊)· `all`(check → coverage → lock)。自測 5/5(+v0100 15/15;前版公開面 check_table 等照轉)。
- **VIA_Output_Header_SSOT_v0102**:+7 表(etf_book · tw_listings · active_tw_etf_universe · etf_holdings_changes · etf_fetch_status · etf_holdings_coverage · etf_stats_daily),欄位照寫入程式 DDL / 列字典(evidence 帶檔:行)。容器實資料 9 表 GREEN → 鎖帳 +9。
- **自壓頁五支新版**(許可冊 P013–P017):唯一入口 v0112 · RunAll v0103 · CloseoutChain v0101 · GitHubFirst-Closeout v0101 · SyncFolders v0101 —— 自己的頁改走 `Open-VIAOwnPage`(cmdlet 全名,不經零跳出閘代理)+ 還原 `VIA_NO_OPEN`;pslint 自壓頁 6 → 0。
- **收尾一鍵 v0100**(許可冊 P018):本文第一節。

## 四、照實(不是綠的)

- 毛申購 / 毛贖回(units_subscribed · units_redeemed)仍查無官方端點 → NULL;資金流入 / 流出 = 淨流量正負拆分(kind=ESTIMATE)。
- 表頭覆蓋:輸出庫 5 · 表 43 · 有表頭 9 · 冊外有資料 28 · 冊外空表 6 → 交接待辦 VCGC-REQ158:header-coverage(各 manager 照寫入程式補)。
- VRN 管理器 status RED(邏輯索引過期 2)= VRN 自己的 manager 處理(L120,本批不代修)。
- 版號:未併分支 `claude/kind-cannon-pti15g` 也用了需求冊 v0193–v0199、盤點冊 v0168–v0177、VCGC-REQ180/181;本批照主線連號(需求冊 v0193 · 盤點冊 v0168 · VCGC-REQ180–182;刪除閘 KILL-11 不准跳號 · 編號系統只發連號),該分支若之後併入由後併者改號(LL334)。

## 五、容器實跑紀錄

2026-10-14 容器 pwsh 7 實跑 2118 秒
- 結束碼 1:

- ① 省 Token GREEN 3.9s
- ② 交接 check RED(本批新模組未登錄
- 相依證據因新檔失效 → 登錄後重測)· ③ 隔離區找回 GREEN(丟失 0)· ④ 庫卡 GREEN
- ⑤ VdfFetch v0108 -Dry GREEN 37.9s
- ⑥ ENG094 fetch SKIP(同意閘關 NO_CONSENT)· ⑦ breakdown GREEN(143 列)· ⑧ VDF 管理器 YELLOW(邏輯 STALE;容器實跑時誤標 SKIP,已改為只有抓網段才可 SKIP)· ⑨ VRN 管理器 RED(邏輯索引過期 2,VRN 自己的)· ⑩ 表頭 all YELLOW(NODATA 12
- 冊外 28)· ⑪ pslint GREEN
- ⑫ collide GREEN(新增 0)· ⑬ FullCheck RED 1899.6s(三橋 GREEN:ACCEL 1645/1645
- NET 137/137
- PS-ACCEL 993/993
- 自擋開頁 0;串測逾時 1800s
- 單一路徑版本不齊 3
- 格子存證 366.7h 舊
- 交接驗收 RED)· ⑭ closeout(乾跑)RED:停在 VRN provenance 案(rc 0 但標記「[來源回歸] fail=0」沒印,VRN 自己的)· ⑮ status:98 份報告紅 17;總頁 AIOPS_RUN_latest.html 經 Open-VIAOwnPage 實際跳出(xdg-open 記錄 07:38:24)

## 六、S20261014b 續修(操作員「繼續修 VRN provenance 和表頭補齊」)

- **VRN provenance**:VRN_SystemManager v0152 —— v0111 起 main 以 `"--selftest" in args[:2]` 攔自測,`provenance --selftest` 被吃成管理器自測鏈,來源回歸測試從沒跑到(收據自 10/07 標記都沒見到)。本版 provenance 先直送 VRN_ENG114 尾版;自測 5/5;handoff test provenance rc 0 ·「[來源回歸] fail=0; tests=23」。待辦 VRN-REQ007 / VCGC-REQ099:provenance → VERIFIED。
- **表頭補齊**:VIA_Output_Header_SSOT_v0103 +34 表(冊外有資料 28 + 空表 6),每張附寫入程式檔:行與 upsert 鍵;整表重建 / VIEW 的表記每列一筆的邏輯鍵;先刪再插、沒有逐列鍵的表不設主鍵。CGC_MDL249 coverage:輸出庫 5 · 表 43 · 有表頭 **43** · 冊外 0;check GREEN 42 · NODATA 12 · RED 1;鎖帳 +33。
- **照實**:gl_sentiment_daily RED = 資料重複(Z297,歸 VDF);vrn_report_metrics 同期多候選值 = 擷取歧義(Z298,歸 VRN);VRN 管理器 status 的邏輯索引過期 2 仍待 VRN。
- 需求冊 v0194:VCGC-REQ180/181/182 的 homes 改成 SDD 認得的歸屬(v0193 寫模組檔名 → X-REQ「歸屬指到不存在」)。

## 七、S20261014c 續修(操作員「繼續修 Z297 Z298 和 VRN 邏輯索引」)

- **Z297 sentiment 重鍵(VDF)**:根因 = VDF_ENG055 L11 把 CNN graphdata 歷史序列(最近幾天同一 UTC 日有好幾個時間點)和「今值」接成一批送正典 `upsert_rows`;正典 anti-join 只擋庫裡已在的鍵,同一批裡的重鍵照插(v0110 起 `dedup_source=False`,正典不改,不擴範圍)。
  - VDF_ENG055 **v0123** 薄尾:L11 送庫前依 (date, index) 留最後一筆(今值在最後 = 當日最新;與 ENG229 同判準),LANES L11 換成本版;自測 6/6(⑥ 前版同一份輸入插 5 列 / 相異鍵 3 = 測得到 Z297)。
  - VDF_ENG229 **v0101** 薄尾 +`dedupe`:乾跑只報;`--apply` 刪整列重複多出的列;同鍵不同值只報 CONFLICT,`--keep-last` 才留最後寫入那筆;只增帳 `sentiment_dedupe_ledger.jsonl`。自測 7/7 + 前版 10/10。容器庫 256 → 252。
  - CGC_MDL249:gl_sentiment_daily GREEN 252 列並鎖帳。
- **Z298 研報指標多候選(VRN)**:VRN_ENG073 **v0140** 薄尾 `resolve_metrics` 掛在 run 的 `extract_one`:① eps 原文是 19xx–21xx 四位整數 = 年份,丟 ② 同鍵同值併 ③ 同鍵仍多值 → status 標 `CONFLICT:<原狀態>`、值都留(不替操作員挑值;ENG080 摘要來源欄會帶出 `metrics:CONFLICT:…`)。`metrics-resolve [--db] [--apply]` 收斂既有資料(依 report_file 先刪再插,與 run 同寫法)。容器 `VRN/db/vrn_reports.duckdb`(有追蹤,一併提交)77 → 74 列;CGC_MDL249 vrn_report_metrics GREEN 74 列並重鎖。
  - 照實:完整 `--selftest` 接前版鏈,前版 ㉑㉒㉓(缺 pydantic)· ㉝(NLP)四紅是既有環境缺件,本版不洗綠(rc 照傳 1;收斂五檢 `metrics-resolve --selftest` 5/5)。真衝突 2 組:3014TT 2024 EPS 11.00 / 9.53 · 南亞 2027 EPS 12.95 / 18(原文「2026、2027 年 EPS 分別為 12.95 及 18」→ 擷取把兩個值都記到 2027)待人看原文。
- **VRN 邏輯索引**:`via_vrn_logic_book_v0112 build`(冊是產物)→ 指標 55 在位且為尾版 55 · 過期 0(ENG086 v0119→v0120 · SUP_MDL749 v0116→v0117 · 本批 ENG073 v0139→v0140)。VRN 管理器 status:邏輯 GREEN · 連結 RED 0;剩 ABSENT 3(參數冊缺 VRN_RESEARCHREPORT_SSOT_ACTIVE · 引擎鏈缺件)是既有狀況,非本批。
- 交接:新案 sentiment_dedupe · omnifetch_sentiment · metrics_resolve · vrn_logic_index(皆 rc 0、標記見到);待辦 VCGC-REQ158:sentiment-dup · VRN-REQ008:metrics-multi-candidate → VERIFIED,新增 VRN-REQ008:logic-index VERIFIED。需求冊 v0195(既有條補證據,不開新號)。
- **工作站**(庫不進 git 的那幾本由操作員在自己的庫跑;經 VCGC):

```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset; git pull --ff-only; cd VeritasIntelligenceAnalytics
$env:VIA_FROM_VCGC = 'YES'      # 經系統自己的 manager 進入的旗(不是網路同意閘)
$vdf = (Get-ChildItem 'functional modules\VDF\VDF_SystemManager_v*.py' | Sort-Object Name | Select-Object -Last 1).FullName
$vrn = (Get-ChildItem 'functional modules\VRN\VRN_SystemManager_v*.py' | Sort-Object Name | Select-Object -Last 1).FullName
# 家族 python(依賴裝在 via_vdf_312 / via_vrn_312 等各自的境;裸 python 可能缺 duckdb):有 Get-VIAEnvPython 用它,沒有照同一命名規則找
function Get-VIAFamPy([string]$f) {
  if (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { return (Get-VIAEnvPython $f) }
  $ov = [Environment]::GetEnvironmentVariable('VIA_PY_' + $f.ToUpper()); if ($ov -and (Test-Path -LiteralPath $ov)) { return $ov }
  foreach ($r in @($env:VIA_ENV_ROOT, "$env:USERPROFILE\envs", "$env:USERPROFILE\miniconda3\envs", "$env:USERPROFILE\anaconda3\envs") | Where-Object { $_ }) {
    foreach ($n in @("via_${f}_312", "via_$f", "via_${f}_313")) { foreach ($sub in @('python.exe', 'Scripts\python.exe')) { $p = Join-Path (Join-Path $r $n) $sub; if (Test-Path -LiteralPath $p) { return $p } } } }
  return 'python' }
$pyVdf = Get-VIAFamPy vdf; $pyVrn = Get-VIAFamPy vrn; "VDF python: $pyVdf"; "VRN python: $pyVrn"
& $pyVdf $vdf engine run VDF_ENG229_CNNFearGreedHistory dedupe            # 乾跑看重複
& $pyVrn $vrn metrics-resolve                                             # 乾跑(VRN_SystemManager v0153 直送 ENG073)
& $pyVdf $vdf engine run VDF_ENG229_CNNFearGreedHistory dedupe --apply
& $pyVrn $vrn metrics-resolve --apply
```

- 更正(S20261014d):本節初版寫 `via-vdfsys` / `via-vrnsys` —— 這兩個短令 2026-10-08 已覆蓋成 DEPRECATED 殘樁(工作站實錄印 [DEPRECATED]、rc 2,沒執行)。
  現行短令 `via-vdf` / `via-vrn` 的參數是 `[string[]]$VerbArgs`,位置參數只收得到第一個,多參數動詞(engine run … dedupe --apply)要直呼 manager 尾版,如上;直譯器用家族境(同 `via-vrnsys` 原本的 `Get-VIAEnvPython`;PR #524 審查)。

- 交接:工作站庫另立待辦 VCGC-REQ158:sentiment-dup-workstation · VRN-REQ008:metrics-workstation(PENDING,主機收據到了才轉 VERIFIED;AGENTS 6)。
- PR #523 審查四條:① 收斂只動 eps(目標價 / 殖利率原樣通過)② ENG073 v0140 自測 rc 3 只在前版紅逐檢都歸得到缺件(㉑㉒㉓ ← pydantic)時給;前版另有既有紅(㉝ 寫死 NLP 樞紐 v1.8.0)→ rc 2 YELLOW ③ 工作站庫待辦另立 ④ 交接案改經各自 manager(VDF_SystemManager engine run · VRN_SystemManager v0153 metrics-resolve / logic)。
- CI「VDF · manager and daily data contracts」第一輪紅:tests/test_via_global_incremental_v0100 在尾版模組上換屬性,v0123 初稿用「前版模組 + __getattr__」換不到 → v0123 改回 v0122 的做法(本體 exec 進自己的全域)。
