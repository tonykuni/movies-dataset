# 三系統全景式檢視 → 問題矩陣 → 第一輪安全修正(VCGC-REQ180 · 2026-10-12)

操作員令(2026-10-12,原話逐字入需求冊 VCGC-REQ180):「用VCGC節省TOKEN工具全景式檢是VCGC/VDF SYSTEM MANAGER及相關SSOT引擎REGEX同義字 收尾完成VCGC VDF後並啟動VCGC及VDF系統跳出HTML U/I完成功能」「…將問題分為可同時修正及應順序修正…不產生九頭龍風險前提下 進行一輪安全修正後 再進行一次事後全景式顯示…成功被鎖定及記錄 錯誤越來越少…直到VDF VCGC這2個獨立系統完美運作無誤…跳出HTML U/I」

全景只讀(VCGC 省 Token 工具 read / slice / digest;L120 三系統對等:VRN 的項只攤開不代修)。燈:紅 = 壞 · 黃 = 缺料 / 環境 / 待裁 · 綠 = 過。

## 一、問題矩陣(改前 → 改後;容器)

| # | 系統 | 項 | 改前 | 根因(讀日誌 / 原始碼定位) | 類 | 錨點(AST) | 修法 | 改後(容器) | 歸屬 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | VCGC | 串測 V-val | 紅 | 驗證冊沒登多段交叉代碼 X-REQ-BACK · X-REQ-OPEN · X-PEER · X-PEER-TEXT;MDL246 v0100 正則 `^X-[A-Z]+$` 只認單段 | 可同時 | `CGC_MDL246_ValidationSSOT_v0100.check` L214-252 | MDL246 **v0101**(換兩條正則,本體不動;8/8)+ 冊 **VIA_Validation_SSOT_v0101**(只增 4 碼 + 三系統 cross_check) | **綠**(`val` GREEN rc 0 · 交叉代碼 27) | AI |
| 2 | VCGC | 串測 P-ui_cmds | 紅 | Register-VIA-Commands 自 v0270 是 PS 薄尾(每版點源前版);站只讀尾版文字,章在 v0269 / v0273 | 可同時 | `CGC_MDL224_TestAuto_v0101.ps_check` L322 | TestAuto **v0106**:章對整條點源鏈(≤ 64 支 · 不迴圈 · 不在略過),章全在才 pwsh 語法檢;6/6 | **黃**(容器沒 pwsh,章在鏈上 7 支;工作站有 pwsh → 綠) | AI |
| 3 | VDF | 串測 C-vdf_fetch_groups_v0100–v0105(6 站) | 紅 ×6 | **不是網路**:v0100 自測 ⑫ 斷言 3 個庫,但 `_db_files` 的根含 VDF 活資料樞 `functional modules/VDF/output_hub`(2026-10-02 起有 vdf_tw_market.duckdb;工作站必有)→ 4 庫 → 整條鏈 FAIL | 可同時 | `VDF_MDL012_FetchGroups_v0100._db_files` L741 · `find_db` L358 · ⑫ L1154 | VDF_MDL012 **v0106**:只在自測跑前版鏈時把 find_db 換「只在自測家找」,跑完換回;正式路徑不動;4/4 · 鏈 10/10 · 9/9。六案標記釘 v0106(v0102 / v0104 / v0105 改跑尾版) | **綠 ×6**(handoff test 六案 rc 0 標記在) | AI |
| 4 | VCGC | SDD X-NUM(V-sdd · V-closeout ⑥) | 紅(4 支) | CGC_MDL183 v0105 · CGC_MDL140 v0107 沒編號;健康矩陣另列 VCGC 7 支 · VDF 4 支沒號 | 順序(先 registry-sync 再編號) | 編號冊 VIA_NumberBooks | registry-sync --apply(新 7 · 變 18)→ MDL237 --apply --scope 19 檔(+288 列)→ audit 遺失 0 · 改身分 0 · 重號 0 | X-NUM 只剩 VRN 2 支(見 #9) | AI |
| 5 | VCGC | 交接閘 5 紅(V-closeout ①⑨ · 全景閘「落後 482 · 快照 213h · 未登 102」) | 紅 | CHANGED_CODE_WITHOUT_TEST:ENG086 v0102(案要 polars)· MDL264 v0100(案要 pwsh)· VRN FirstPageEngine v0130(案要真 sidecar ≥ 20)· SUP_MDL749 v0116 / v0117(操作員 VRN 暫緩);checkpoint 紅就拒寫 → 全景閘永遠落後 | 順序(工作站先過五案 → checkpoint) | `CGC_MDL140_HandoverConsole_v0101.checkpoint` L293 | 容器不能過(不裝套件);工作站一貼(見三) | 紅(工作站可清) | 操作員(工作站) |
| 6 | VCGC | SDD X-LOCK 黃 6 處 | 黃 | 已鎖工作流尾版換了(MDL156 v0114 · MDL866 v0108 · MDL140 v0107 · MDL149 v0191 · VDF_SystemManager v0154 · VRN_SystemManager v0151) | 順序(交接綠 → real → lock) | `CGC_MDL245_SDDValidator_v0103.lock` L96(交接不綠拒寫) | 工作站交接綠後 `sdd real` → `lock --apply`(燈鎖冊下一版;VRN-WKF008 交 VRN) | 黃 | AI(工作站交接綠後) |
| 7 | VCGC/VDF | 串測 C-vdf_akshare_v0101 / v0102 · C-via_unified · P-entry / P-step1 / P-vdf_fill / P-vdf_groups_ui / P-ui_engine · V-ssot / V-check / V-panorama · QG-ENG086 | 紅 3 · 黃 9 | 容器環境:polars 缺 · pwsh 缺 · VIA_ENV_ROOT 沒設;不裝套件(操作員令) | — | — | 工作站環境齊就綠;容器照實 | 同 | 操作員(環境) |
| 8 | VRN | 串測 C-vrn_layout · C-first_page_engine · C-cov_vrn_firstpage_engine · V-systems(VRN logic 紅)· 健康矩陣 VRN lib 缺 pdfplumber | 紅 | reportlab 缺 · 真 sidecar 只在工作站 · VRN 邏輯冊紅 · pdfplumber 缺 | — | — | VRN 自己的 manager / 工作站;VCGC 只攤開(L120) | 同 | VRN |
| 9 | VRN | SDD X-NUM 剩 2 支 | 紅 | VRN_ENG086_FirstPageLogicBridge_v0120 · VRN_SystemManager_v0151(工作站 v0192)沒編號;L120「不改他系統的號」 | — | — | VRN 自己編(或操作員授權:`run CGC_MDL237_NumberingSystem --apply --scope <兩支>`) | 紅 | VRN / 操作員 |
| 10 | VCGC | E-number-audit FPSTALE 529 | 黃 | 529 / 800 本 SSOT 冊指紋過期(VCGC/SUP 336 · VRN 108 · VDF 85;無版號 275 · 有版號 254,多在 new modules engines / GroupIndex / intake 歷史件) | 順序(先定「活冊不驗指紋」規則) | `CGC_MDL237_NumberingSystem_v0109.fpstale` L355 | 重編只會再過期(活冊天天改);本輪不動,待編號規則分「活冊 / 凍結冊」 | 黃 | AI(下一輪) |
| 11 | VCGC | V-workflow 黃(NOT_RUN 44)· V-ssot-panorama 黃(要 --full) | 黃 | 工作流實測沒跑;SSOT 全景沒跑全量 | 順序 | — | `sdd real`(重;工作站)· `ssot panorama --full` | 黃 | AI |
| 12 | VCGC | 工作站主控台印 `SyntaxWarning: invalid escape sequence` | 黃 | 79 處 docstring 帶反斜線沒用 r"""(MDL156 v0114 L3 `\*` · MDL273 v0102 L6 `\C` …);Python 3.12+ 編譯時警告,容器 3.11 不印;掃描器重剖「變更檔」時冒出 | — | 各檔第 3 行 docstring | 不就地改已發布檔;各家族下一版用 r""";本輪新尾版已照做 | 黃(工作站 registry-sync --apply 後不再重剖) | AI(各家族下一版) |
| 13 | 三系統 | 健康矩陣「副本檔名 → DORMANT 候選」黃 · 版號有洞 | 黃 | `_sha` 存證副本是操作員 2026-10-10 裁定保留的;版號洞是歷史 | — | `CGC_MDL274_HealthMatrix` 語意判定 | 展現層可改「存證副本(裁定保留)」不計黃;本輪不擴 | 黃 | AI(下一輪) |

## 二、事後全景(容器,修完第一輪再量一次)

| 量尺 | 改前 | 改後 | 說明 |
|---|---|---|---|
| VCGC 全功能串測(整輪) | 252 站 · 紅 17 · 黃 15 · 綠 220 | 250 站 · 紅 10 · 黃 15 · 綠 225 | 清掉 V-val · P-ui_cmds · C-vdf_fetch_groups ×6;新紅 1 = E-number-audit(IMMUT 誤判交接收據 → MDL237 v0118,見 #14) |
| 剩下的紅 | — | V-sdd · V-closeout(VRN X-NUM + 交接 5 紅)· V-systems(VRN logic 紅)· C-vrn_layout(reportlab)· C-first_page_engine · C-cov_vrn_firstpage_engine(sidecar)· C-vdf_akshare ×2(polars)· C-via_unified(pwsh)· E-number-audit(→ v0118) | 全屬 VRN / 環境 / 工作站,容器不代裝不代修 |
| 交接檢查 | 紅 5 | 紅 5(同五支) | 本輪新案 / 改釘案 11 案全 rc 0 標記在:validation_ssot_v0101 · chain · vdf_fetch_groups ×6 · progress_journal · vdf_activate · numbering |
| SDD check | X-NUM 紅 4 支 | X-NUM 紅 2 支(VRN) | X-LOCK 黃 6 · X-REQ-OPEN 黃 75 不變 |
| 驗證 SSOT(val) | 紅 rc 1 | 綠 rc 0(交叉代碼 27) | 冊 v0101 + MDL246 v0101 |
| 編號稽核 | 黃(FPSTALE 529) | 列 115859 → 116263(+404)· 遺失 0 · 改身分 0 · 重號 0 · FPSTALE 529 | IMMUT 6 → 0(v0118) |
| 健康矩陣 | VCGC 黃 · VDF 黃 · VRN 紅 | 同 | VRN 紅 = pdfplumber 缺(容器);VCGC 有號 1148 → 全部 CGC 尾版有號 |
| SSOT 全景 | 黃 rc 2 | 黃 rc 2(探針 7,沿用 5) | 上下單向 VCGC → VDF → VRN → SUP 無新發現 |

| # | 系統 | 項 | 改前 | 根因 | 類 | 錨點 | 修法 | 改後 | 歸屬 |
|---|---|---|---|---|---|---|---|---|---|
| 14 | VCGC | 串測 E-number-audit(事後新紅) | 紅 | 六份交接收據 `docs/handoff/evidence/vdf_fetch_groups_v010x.json` 重跑後改了;v0109 IMMUT 把「檔名 *_vNNNN.json + 同夾 ≥ 2 版」當已發布版號冊,收據的 _vNNNN 其實是案名,依設計覆寫(MDL140 先按 SHA 封存) | 順序(修規則 → 重編 → 重跑案) | `CGC_MDL237_NumberingSystem_v0109.immut_violations` L316 | MDL237 **v0118**:IMMUT 具名豁免 `docs/handoff/evidence/`,其餘規則不動;5/5 · v0117 7/7 | 黃(FPSTALE 529 照舊) | AI |

鎖定與記錄:成功版都釘在交接案(釘版 + UTC 時間 + 原因)與編號冊(版號 + 時間);SDD 燈鎖(`lock --apply`)被交接閘擋(容器 5 紅屬工作站 / VRN),在工作站一貼裡做。

## 三、R71 VDF 並行擷取 · 頁 USER-TEST(VDF-REQ018;容器,2026-10-12)

操作員令原話入冊 VDF-REQ018(`VIA_Requirements_SSOT_v0195.json`)。做了什麼、量到什麼:

| # | 項 | 做法 | 容器實測 | 歸屬 |
|---|---|---|---|---|
| 15 | VDF 引擎全帶版號加速器 / 網路工具 | 稽核(乾跑,只讀):`run CGC_MDL124_BridgeSweeper`(NET 根 functional modules/VDF · ACCEL 根) | NET 掃 524 · 已掛 137 · 缺 0 · 覆蓋 100%;ACCEL 計畫 0 | 齊,無缺可補 |
| 16 | PS 加速模塊 | PS 入口(Invoke-VIA-VdfFetch-v0108 · Invoke-VDF-FetchFill-v0100 · Invoke-VIA-RealTest-v0106 · Invoke-VDF-FetchGroupsUI-v0100 …)查 Invoke-VIACeleritasScoped / Invoke-VIAPython | 已帶;`.ps1` 不改(L70) | 齊 |
| 17 | 清單引擎先跑 | 擷取冊 `009` VDF_MDL009_TWStockList(台股全市場清單,自動更新)· `010` VDF_MDL010_ActiveETFList(主動式 ETF 清單);冊上每支擷取引擎都 `needs` 這兩支 → `VDF_MDL012_FetchGroups_v0107 run` 先跑兩支,紅就停(rc 5) | fixture 煙霧(暫存家):010 rc 0 → 才起道 | AI |
| 18 | 3~5 流程並行 · CPU / DRAM / TEMP 上限 | v0107:族群依 DuckDB 庫 / 同引擎 / 相依分道(真冊:vdf_tw_market 4 族群一道 · vake 4 族群一道一列 011d · ETF · 指數 · 全球 · parquet)· `--jobs 1~5`(auto = CPU − 1)· 起每支前量 CPU% / DRAM 可用 / TEMP 可用(psutil,退 stdlib),超限等(`--cpu-max 85 --mem-min-gb 2 --temp-min-gb 5 --govern-wait 600`)· 子行程 `VIA_TEMP_ROOT` / `VIA_DUCKDB_TEMP_DIR` / `VIA_DUCKDB_MEM_PCT = 50 ÷ 流程`(MDL262 規則,TEMP 為主)· 子行程直接從 MDL008 尾版起(`run_v0107` 的 `__file__` 換裝不是執行緒安全)· 一筆 fg_runs + `_fetch_groups/PARALLEL_latest.json` | 自測 9/9 · 前版鏈 v0106 → v0100 PASS(六案標記照印);fixture 煙霧:兩道同時起、目錄 ok,引擎 fixture 下照自己的閘回 rc 2/3/4(不是本版的錯) | AI;live 要雙閘(工作站) |
| 19 | 跳出 HTML U/I 帶驗證結果 · 功能鍵 USER-TEST | 頁多一頁「並行擷取 · USER-TEST」+ 左面板「並行流程」「並行跑族群」「USER-TEST」鈕;`usertest` 動詞:建頁(報告夾)→ 靜態驗 → Chromium / Chrome / Edge headless 逐鍵點、讀 #cmd、切頁籤、全選 / 清除 → 結果掛頁 | Chromium headless:79 綠 · 0 紅(功能鈕 11 · 收尾鈕 6 · 新鈕 2 · 頁籤 17 · 全選 / 清除 · 快照);正式頁已重建(含結果) | AI |
| 20 | VCGC 檢視沒裝的工具 | `run CGC_MDL273_EnvToolAudit ext` · `run CGC_MDL240_EnvManager` | pdftoppm 缺 → winget 計畫(oschwartz10612.Poppler;`ext --apply` 要本視窗 VIA_NET_CONSENT=YES)· pdfplumber 缺(VRN 首頁文字)· polars / reportlab / pwsh 缺(容器專屬);不裝套件 | 操作員(環境) |
| 21 | BASIC INFO / FINANCIAL DATA / 1ST PAGE MAIN TEXT / 1ST INFO AREA 書實測 | VRN 首頁四區 = VRN 自己(L120);工作站 `via-realtest` | 容器無樣本、無 pdfplumber | VRN / 工作站 |

登錄:交接案 `vdf_fetch_groups_v0107` · `vdf_fetch_groups_usertest`(+ v0100 / v0101 / v0103 三案相依 +v0107)· 站 `C-vdf_fetch_groups_v0107` · `C-vdf_fetch_groups_usertest`(盤點冊 v0169)· VDF-REQ018(需求冊 v0195)· 編號批(v0107 · 兩冊)。

收尾量測(容器,2026-10-12):registry-sync 新 36 · 變 8;編號批 +49(FNC 43 · ENV 2 · MDL 1 · REQ 1 · SSOT 2)· audit 遺失 0 · 改身分 0 · 重號 0(冊內不一致 1 · FPSTALE 為既有黃);sdd check YELLOW(X-REQ 綠;X-LOCK / X-REQ-OPEN 黃照舊);交接案 vdf_fetch_groups_v0107 · usertest · v0100 / v0101 / v0103 · vdf_activate · numbering ×4 · chain 全 rc 0 標記在;handoff check 回到同 5 紅(工作站 / VRN 的 CHANGED_CODE_WITHOUT_TEST);test --quick 站 7(綠 5 · 黃 2 · 紅 0)· 盤點 案 172/172 · 尾版 279 支 compile 錯 0 · 缺橋 0。

## 四、工作站一貼(操作員;v3)
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
git fetch origin claude/kind-cannon-pti15g
git merge --ff-only origin/claude/kind-cannon-pti15g      # 印出結果;不是 Fast-forward / Already up to date 就先停
cd VeritasIntelligenceAnalytics
$V = (Get-ChildItem "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$env:VIA_FROM_VCGC = "YES"; Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue
# 0 冊同步(工作站本機 VRN 檔登錄;已授權)→ sdd
python $V registry-sync --apply
python $V sdd check
# 1 工具:沒裝的列出(pdftoppm → winget 計畫;--apply 要本視窗 $env:VIA_NET_CONSENT='YES',操作員的手)
python $V run CGC_MDL273_EnvToolAudit ext
python $V run CGC_MDL240_EnvManager
python $V run CGC_MDL262_DuckTempHook status
# 2 VDF:清單引擎先跑 → 分道並行(live 要雙閘,本視窗:$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES')
python $V run --family vdf VDF_SystemManager universe
python $V run --family vdf VDF_MDL012_FetchGroups run --groups ALL --jobs 4 --mode live
# 3 頁:功能鍵實測 → 重建正式頁(結果掛頁)→ 跳出
python $V run --family vdf VDF_MDL012_FetchGroups usertest
python $V run --family vdf VDF_MDL012_FetchGroups ui
python $V run --family vdf VDF_SystemManager ui
via-groups-ui
# 4 交接 → 快照 → 真跑 → 鎖成功版
foreach ($c in @("vdf_fetch_groups_v0107","vdf_fetch_groups_usertest","qg_onebridge","via_unified","first_page_engine","cov_vrn_firstpage_engine","vrn_ssot_consistency")) { python $V handoff test $c }
python $V handoff check
python $V handoff checkpoint
via-realtest
python $V run CGC_MDL245_SDDValidator real
python $V run CGC_MDL245_SDDValidator lock --apply
# 5 VCGC 頁
python $V run CGC_MDL274_HealthMatrix matrix
python $V run CGC_MDL261_UIEngine build --open
```
VRN 自己的尾版(工作站 v0194)編號:先提交那支,再 `python $V run CGC_MDL237_NumberingSystem --apply --scope "functional modules/VRN/VRN_SystemManager_v0194.py"` → `audit`(正斜線路徑;絕對路徑不算)。

## 五、VRN 自報(工作站 `C:\Users\tonyk\VIA-VDF-VRN` · VRN-MAIN 2026-10-12T06:26;L120 只攤開不代修)

來源:操作員貼回的 VRN_Main 報告(RED · FAIL 2 · WARN 6 · PASS 41;樣本 個股 58/534 · 頁 117/477)。VRN 的 VRN_Main / autotest / titletrim / 表頭冊 v0102 / 鎖帳本都只在工作站鏈,不在本倉(容器只到 ENG086 v0120 · ENG394 v0102 · 表頭冊 v0101),所以錨點只到本倉有的規則本體;改 VRN 檔要操作員令,VRN 自己的手。

| # | 閘 | 現況 | 根因(照報告與規則本體讀) | 類 | 修法(給 VRN) |
|---|---|---|---|---|---|
| V1 | G16 DATAFRAME | 19 張:綠 15 · 紅 4 | 驗法 `CGC_MDL249_DataFrameLock_v0100.check_table`(L142–199):`required` 欄 NaN / 空字串 = 紅「必填但 N 筆空」;型別轉不過 = 紅 | — | 每一紅先分「引擎留空」或「冊上必填訂太嚴」兩種,看 `autotest\round1\dataframes` 的那幾列就能定 |
| V1a | vrn_basic_info | 58 × 70 · `AdjCloseReportDate` 1 筆不是 date | 報告日沒有調整收盤(假日 / 無價)時寫了哨兵字串而不是空值 | 可同時 | 無價寫 NULL,狀態放 `_state` 欄;冊上該欄 nullable |
| V1b | vrn_financial_data | 4219 × 55 · `PeriodLabelRaw` 必填但 48 空 | 期別表頭(合併格 / 直排)沒跟著數字列帶下來 | 可同時 | 期別標籤沿欄向下傳;帶不到的列 `REVIEW` 不留空 |
| V1c | vrn_regions_rows | 605 × 13 · `metric_raw` 必填但 52 空 | 數字格沒有科目字(TRIM 掉字 / 跨列科目) | 可同時 | 科目沿列傳;TRIM 不得吃掉科目字(與 P1「TRIM 掉字」同源) |
| V1d | vrn_title_parts | 58 × 22 · 一份報告五個 `*_state` 空 | def02 七段拆不開的那一份,狀態欄寫了空白 | 可同時 | 狀態欄永不空:拆不開寫 `UNPARSED`(狀態是設計上的必填) |
| V2 | G18 引擎鎖 | HELD 38 · UNLOCKED 1(`VRN_PanoramaProbe.py`) | 沒有已知答案證明(沒有固定樣本的自測) | 可同時 | 給探針一個已知答案自測,或鎖規則對唯讀探針豁免 → 39/39 |
| V3 | G18 輸出鎖 | NEW 398 · OPEN 1013(NOT_PRINTED 323 · CONFLICT 107 · SINGLE 280 · MISSING 30 · UNMAPPED 261 · REVIEW 12) | 第一輪建鎖;待修 690 = CONFLICT 107 + MISSING 30(優先 1 = 137)+ UNMAPPED 261 + REVIEW 12(優先 2 = 273)+ SINGLE 280(優先 3) | 順序 | 先修 V4(優先 1 的根因集中在 TRIM 讀法)→ 第二輪再鎖;SINGLE 280 要第二個讀法(ENG396 全文)才有證明 |
| V4 | 優先 1 讀法不一致(8 例樣本) | 8 例裡 7 例是「首頁(TRIM)」讀法落單:broker FIRST vs MEGA · date 2024-12-09 / 2026-06-03 vs 檔名日 · current_price 2025.0(年份當價格)· 標題多「 - 」 | TRIM 讀法的正則:價格吃到四位數年份;日期抓到頁上另一個日期(前次報告日 / 資料日 / 有效期);券商抓到免責聲明裡的別名;標題比對沒先正規化 | 可同時 | ① 價格正則排除年份 / 日期 token ② `cover.date` 只認等於檔名日的那個,其餘日期進 `data_date` / `valid_until` ③ 券商只在刊頭區抓,否則照檔名 + 首頁引擎多數 ④ 標題先正規化(去「 - 」「－」空白)再比,免得假衝突 |
| V5 | 優先 1 目標價仲裁 | 泓德(6873):TRIM + ENG396 = 345 vs 首頁引擎 = 208;印 22.7% vs 重算 103.54%(def03) | 多數決(2 比 1)選了 345,但 def03 `upside_pct`(kernel v0102 L120)用 208 才算回印的 22.7%(標題也印「逢低買進 $208」);345 是別的數(如 52 週高) | 順序(V4 之後) | 仲裁順序改:先用 def03「哪個候選算回印的上漲空間」選目標價,算不回再多數決;神達(3706)78 vs 128 同法 |

量尺(第二輪要看的):G16 紅 4 → 0;引擎鎖 39/39;CONFLICT 107 與 MISSING 30 歸零後 OPEN 降 137;SINGLE 280 要第二讀法才動。

## 六、R72 族群頁版面最佳化(VDF-REQ018 第三則;容器 2026-10-12)

操作員看過工作站 `via-groups-ui` 跳出的頁(那一跑還是 v0105 尾版,分支未合):「字體大小有位階但畫面凌亂,要用工具最佳化」。容器用 headless Chromium 截 1600×2400 對照:

| # | 凌亂處(截圖) | 工具 / 修法(v0108 薄尾) | 改後 |
|---|---|---|---|
| 22 | 左面板一條到底約 2000px:輸入 → 15 功能鍵 → 6 收尾鍵 → Live log → 17 個頁鈕(與上方頁籤重複)→ 母系統 / 他系統連結 | 每節 `<details>`:① 輸入控制 · ② 功能 開;③ 收尾 · 頁 · 回母系統 · 跳到其他系統 收並標鈕數;Live log 擷取中才開 | 一屏看完輸入與功能鍵;收著的節一眼知鈕數 |
| 23 | 引擎表短欄(最後跑 · 模式 · rc · 燈)逐字直排;檔名欄在字中間斷行 | VDF 自己的字級套件(VIA_UI_Template_SSOT v0102 tokens / auto_layout,經 VDF_SystemManager `typekit_block`,與全景 / 健康 / UIEngine 頁同一份):短欄不換行 · 長欄限寬 · 寬表橫捲 · 之後長出來的表照樣吸附 | 表頭一行;檔名縮成檔名(全路徑在 title) |
| 24 | 燈欄在最後一欄;空格空白 | 展現規則(頁內 JS 只動 DOM):燈欄第一 · 問題在前 · 空值 — · 路徑縮檔名 · 表頭不換行 | 結果表黃列在最前、燈在第一欄 |
| 25 | usertest 瀏覽器實測在新頁「沒回探針」 | 根因:套件程式給每個 `<pre>` 補 `style="font-family:…"`,v0107 精確比對 `<pre id="VIA_UT">` 落空 → v0108 放寬讀法並換進 v0107 | 79 綠 · 0 紅(鈕在收著的節裡照樣可點) |

不變:功能鍵 / 頁籤 / 輸入 id 集合與 v0107 完全相同(自測 ④ 逐一比對);正式路徑(run · usertest · 各動詞)一字不動。自測 7/7 · 前版鏈 v0107 → v0100 PASS。
工作站看法:合併分支後 `via-groups-ui`(或 `python $V run --family vdf VDF_MDL012_FetchGroups ui`)重建頁再開。

## 七、R73 一鍵全部(VDF-REQ018「INTEGRATE ALL ABOVE INTO ONE」;容器 2026-10-12)

之前分開給的六件(Open-VIA-VDF 問參數頁 · 族群並行 run · usertest · 族群頁 ui · 主頁 ui · via-groups-ui 跳出)合成 VDF_SystemManager v0155 的一個動詞:

```powershell
python $V run --family vdf VDF_SystemManager all        # 問參數頁跳出 → 在頁上按啟動 → 其餘自動;跑完族群頁跳出
```

| 步 | 做什麼 | 燈的意思 |
|---|---|---|
| health | VDF 健康(檔族 · 號 · 登記 · 橋) | 黃 = 版號語意等既有黃 |
| ready | 啟動就緒(本版 read_launch 門;問參數頁上那一格之前 ABSENT 的根因 = 薄尾鏈接不到 v0104 的本體) | GATED / ABSENT 黃不擋;RED = 啟動器 / 鏈缺 |
| ask | Open-VIA-VDF 尾版(pwsh 子行程):問參數頁 → 你按啟動 → 11 步擷取 → 資料庫狀況頁 | rc 0 完成或不啟動;2 逾時沒決定;沒有 pwsh 跳過照實 |
| groups | VDF_MDL012 run --groups ALL --jobs auto --mode live(清單 009 · 010 先跑 → 分道並行) | rc 4 GATED 黃(本視窗沒開雙閘);rc 5 清單紅 → 後面全 SKIP |
| lists | universe list(範圍冊 + 市場清單 → 輸入清單 OUT-01) | rc 2 NODATA 黃 |
| usertest · page · hub | 功能鍵實測 → 族群頁重建(結果掛頁)→ 主頁 | — |
| open | 跳出族群頁(VIA_NO_OPEN=1 / --no-open 不開),主頁路徑印出 | — |

旗標:`--no-ask`(不問、不跑 11 步)· `--skip a,b` · `--groups X,Y` · `--jobs 3~5` · `--mode fixture|block` · `--dry`(只列計畫)。報告 `VIA_Reports/vdf/ONE_LAUNCH_latest.json`(+ runs.jsonl)。
容器實測:自測 8/8 · 前版鏈 v0154 → v0131 全 PASS;`all --dry` 經 VCGC 列 9 步、啟動器取 Open-VIA-VDF-v0103、pwsh 缺就跳過 ask 並講原因;`all --skip ask --mode fixture --groups TW_INDEX --no-open` 整跑:health GREEN · ready RED(容器沒有短令冊「啟動器/鏈缺:Register via-vdffetch」,工作站應 GREEN / GATED)· groups RED(fixture 下引擎照自己的閘回紅,同 R71)· lists YELLOW(容器無清單)· usertest GREEN 79/0 · page GREEN · hub GREEN · 總燈 RED 照實,九步一列都在 ONE_LAUNCH_latest.json。

## 八、工作站一貼(操作員;v4 = 一個指令)
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
git fetch origin claude/kind-cannon-pti15g
git merge --ff-only origin/claude/kind-cannon-pti15g
cd VeritasIntelligenceAnalytics
$V = (Get-ChildItem "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$env:VIA_FROM_VCGC = "YES"; Remove-Item Env:VIA_NO_OPEN -ErrorAction SilentlyContinue
python $V registry-sync --apply
# 族群並行那一步要本視窗先開雙閘(操作員的手):$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'
python $V run --family vdf VDF_SystemManager all     # 問參數頁跳出 → 在頁上按啟動 → 其餘自動 → 族群頁跳出
```
跑完貼回視窗最後的 `[計] VDF_SystemManager_v0155 all · …` 那一行與 `VIA_Reports\vdf\ONE_LAUNCH_latest.json`;之後交接:`handoff test vdf_manager_v0155`、`vdf_fetch_groups_v0108`、`vdf_fetch_groups_usertest` 與工作站五案 → `handoff checkpoint` → `via-realtest` → `sdd real` → `lock --apply`。

## 九、R74 短令 `activate_vdf`(VDF 前後端一鍵,從 HTML U/I 操作;VDF-REQ019;容器 2026-10-12)
操作員令:「設立一個指令啟動VDF 短指令activate_vdf 啟動前後端系統介面 從html u/i操作」
- `Register-VIA-Commands-v0276.ps1`(點源 v0275;v0275 以前一字不動;L70 這一次的許可):`function global:activate_vdf` + 別名 `activate-vdf` · `啟動VDF全部`;同名梭 `activate_vdf.cmd`(不設 VIA_NO_OPEN:頁要跳)。
- 四段:① `CGC_MDL265_VdfVrnReadiness` 母系統監控(只提醒不擋;`-SkipCheck` 略過 · `-Repair` 修)② 啟動前改(下載夾 `VIA_UI_Input.json` → `CGC_MDL261_UIEngine import`;`--start / --add / --remove / --import` → `VDF_SystemManager activate`;沒 `-Apply` = 乾跑)③ `VDF_SystemManager all`(健康 → 啟動就緒 → 問參數頁[前端:頁上按啟動 → 11 步擷取 → 狀況頁] → 族群並行[後端] → 輸入清單 → USER-TEST → 族群頁 → 主頁 → 跳出族群頁)④ `CGC_MDL261_UIEngine build` → 跳出操作頁;收尾一行 `[activate_vdf] 燈 · 各步 rc · 報告 VIA_Reports\vdf\ONE_LAUNCH_latest.json`。
- 旗標:`-SkipCheck · -Repair · -Apply · -NoAsk · -NoOpen · -Dry · --groups · --jobs · --mode · --skip · --home · --start · --add · --remove · --import`;雙閘永不代設。
- 容器驗法(無 pwsh):PS 文字剖析問題 0(v0276 · 梭)· `CGC_MDL157 status`:冊上 208 支 via-* 短令原缺梭 23 支(含 via-activate-vdf · via-groups-ui)本輪補範本梭 → 全有梭 · 零釘死;剩「失門 via-activate-vdf 樣式取不出」「別名歧指 總檢→via-precheck/via-review」兩項是 v0274/v0275 既有(只攤開不代修)· `CGC_MDL265` 自測 10/10 · 交接案 `activate_vdf_v0276`(MDL157 自測:命令冊沿鏈讀到 v0276)。函式本體要工作站實跑。
- 工作站(操作員的手):
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
git fetch origin claude/kind-cannon-pti15g
git merge --no-edit origin/claude/kind-cannon-pti15g      # 本機有自己的提交也能併(--ff-only 會拒;衝突就把訊息貼回)
cd VeritasIntelligenceAnalytics
Test-Path .\Register-VIA-Commands-v0276.ps1                 # 要 True;False = 併入沒成,先看上面 merge 的訊息
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 或任何殼直打 activate_vdf(同名 .cmd 梭)
Get-Command activate_vdf | Select-Object Name, Source       # 要看到 activate_vdf;沒有 = 點到的尾版不是 v0276
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'   # 要抓才開(本令永不代設)
activate_vdf        # 問參數頁跳出 → 頁上按啟動 → 其餘自動 → 族群頁 + 操作頁跳出;只看計畫:activate_vdf -Dry -NoAsk
```
跑完貼回 `[activate_vdf] …` 那一行與 `[計] VDF_SystemManager_v0155 all · …` 那一行;之後 `handoff test activate_vdf_v0276` · `tooling` → `handoff checkpoint`。

實錄 2026-10-12(工作站第一次):`activate_vdf` 無法辨識 → 點源的尾版不是 v0276(`--ff-only` 在本機有自己提交時會拒併,之後的指令照跑)。一貼改成 `git merge --no-edit`,並加 `Test-Path` / `Get-Command` 兩道檢查。

## 十、R74b 三台獨立操作台裁定 → `activate_vdf` 改純 VDF(Register v0277;VCGC-REQ181 · VDF-REQ019;容器 2026-10-12)
操作員裁定:「vrn vdf vcgc都是獨立操作台 只是顏色及layout基本規劃相同」。工作站實錄(第一次真跑):`activate_vdf` 起來了,但 `VDF_SystemManager` 尾版仍是 v0154 → 「未知動詞 'all'」rc 2(分支 68 筆沒併全,只拿到兩個 Register 檔);④ 開的是 VCGC 的統一操作頁(CGC_MDL261)。
- `Register-VIA-Commands-v0277.ps1`(點源 v0276;v0276 以前一字不動)蓋過 `activate_vdf`:① 啟動前改走 VDF 自己的 `activate --import` / 文字改動 ② `VDF_SystemManager all`(尾版 < v0155 → 紅、不起,不假跑)③ 經 `via-open` 跳出 VDF 主頁 `VIA_Reports\vdf\VDF_UI_latest.html` + 族群頁;`-Check` 才跑 VCGC 只讀監控(不帶 --repair);載入印「[VIA] Register 尾版 v0277 …」旗標行。VIA_NO_OPEN 只管 VCGC 自己的頁。
- 冊:需求 v0199(+VCGC-REQ181 裁定原話;VDF-REQ019 evidence / next 更新)· 盤點 v0173(+C-activate_vdf_v0277)· 交接案 activate_vdf_v0277 + 工作項 VDF-REQ019:activate_vdf 帶理由轉回 PENDING → 收據後 VERIFIED。
- 工作站(操作員的手;本機有自己的提交 → 用拉齊醫生真併,帳本聯集):
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 先載現有尾版,拿到 via-medic
via-medic sync --apply --branch claude/kind-cannon-pti15g      # 真併(stash 髒樹 → merge → 帳本按律聯集 → 還原);有紅就整段貼回
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # 再載:要看到「[VIA] Register 尾版 v0277」
Get-Command activate_vdf | Select-Object Name, Source
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'   # 要抓才開
activate_vdf        # 只看計畫:activate_vdf -Dry -NoAsk
```
跑完貼回 `[activate_vdf] …` 那一行與 `[計] VDF_SystemManager_v0155 all · …` 那一行;之後 `handoff test activate_vdf_v0277` · `tooling` → `handoff checkpoint`。

操作員重申(2026-10-12):「重申vcgc vrn vdf為三個獨立系統 可動到彼此 但相互查」→ 讀作三個獨立系統、互不改動彼此、只相互查(只讀監控);入 VCGC-REQ181 第二則原話(需求冊 v0200)。v0277 照此:`-Check` 只讀不修,啟動前改只動 VDF 自己的帳本。

## 十一、R74c 問參數頁「啟動就緒」假紅修正(VDF_SystemManager v0156;VDF-REQ018;容器 2026-10-12)
工作站問參數頁(14:59,來源 `VDF_SystemManager_v0155.py` = 分支已併):「啟動就緒 RED · [修] 這些是樹上的檔,不是設定:git pull…」。
- 根因:v0104 `read_launch` ④ 只讀 Register 尾版一檔找 16 個啟動短令(`function global:via-vdffetch {` …);冊自 v0244 起是薄尾,16 個短令全在 v0243 → 尾版單檔永遠找不到 → 假紅(容器也一樣,之前誤判為「容器無短令冊」)。
- v0156(薄尾):代答前把 v0104 的 `_src` 換成「Register 冊沿 dot-source 鏈讀」的讀器(尾版 → 前版;只讀不執行;防環;非 Register 檔照舊),代答完還原;v0155 的 `READY` 指到本版門(`all` 的 ready 步同);鏈的讀法 = VCGC 唯一入口控制 v0106 的同一條正則(抄尺不抄程式,不載 VCGC)。自測 8/8 + 前版鏈 v0149 → v0155 全 PASS;ENG093 `readiness()` 經尾版門 `cmds_missing` 空。
- 問參數頁同時報的資料庫狀況(VDF 自報,照攤):目錄 STALE 4.1 小時 · 分類燈 RED(營收 NODATA 202607 · ETF 滯後 47 · 宏觀 48 · 國際 46 · 其他 103)· 增量缺口 32 表(多數止於 2026-08-25/27)。11 步擷取已送出 → 跑完 `via-datahome catalog` → `via-vdfinc plan`。
- 冊:交接案 vdf_manager_v0156 + 工作項 VDF-REQ018:ready_door(PENDING → 收據後 VERIFIED)· 盤點 v0174(+C-vdf_manager_v0156)· 需求 v0201(VDF-REQ018 evidence / next)。v0156 加入 `VDF_SystemManager_v*.py` 相依 glob → 12 案重跑。

## 十二、R75 VDF 單元檔亂碼:先修檔 → 擷取工具加解碼器 → 真抓一次 · 真匯出一次(VDF-REQ020;容器 2026-10-12)
操作員令:21 個 `via_database\vdf_database\tw__*.parquet · gl__*.parquet`「先把它修正為非亂碼 再回朔到擷取他的工具加上亂碼問題解碼器 解取實用一次 輸出實用一次」。
- 根因(倉內實錄,只攤開):網路工具「當文字」那一步 — Aegis `fetch_text` 用 `resp.text`(無 charset 的 Big5 回應被當 latin-1 → 可逆亂碼)· SUP_MDL740 標準庫退路 `decode("utf-8","replace")`(U+FFFD,不可逆)· urllib 退路 `errors='ignore'`(丟位元組)。單元檔由 ENG065 檔名協定(tw__ → vdf_tw_market · gl__ → vdf_global_market)匯入 DuckDB。
- 四支(全經 VCGC `run` 由名解析 rc 0):
  - `supportive modules/network/SUP_MDL756_SmartDecode_v0100.py` 亂碼問題解碼器:`smart_decode`(BOM → 宣告 charset → `<meta charset>` → utf-8 嚴格 → cp950 / big5hkscs / gb18030 嚴格 + 常用字可信度門檻;永不 replace / ignore)· `demojibake`(可逆反解 latin1→utf8 / latin1→cp950 / cp950→utf8 …;U+FFFD 誠實 UNRECOVERABLE)· `plan_values`(一欄一種轉換多數決)。自測 13/13。
  - `SUP_MDL740_NetUnified_v0119.py` 薄尾:`http_text` 雙閘先行 → 先位元組(Aegis `fetch_bytes` → 標準庫 `http_bytes` 重試道)→ 智慧解碼 → `{data · via+smartdecode · encoding · lossy}`;拿不到位元組退前版 + 可逆反解。`via_net_unified` 轉接件自動接到尾版,所有走 `http_text` 的引擎(ENG063 月營收 MOPS CSV · ENG082 · …)不改一字即受惠。自測 9/9 + 前版鏈(鎖冊核心 v1652 不動)。
  - `functional modules/VDF/engine/VDF_ENG235_MojibakeRepair_v0100.py`:`scan <路徑>`(每檔每欄 可修 / 不可逆 + 樣本;GREEN / YELLOW / RED)· `fix <路徑> [--apply] [--backup-dir] [--no-db-backup] [--units-only]`(parquet 先備份 `_pre_mojibake/` 再 DuckDB 重寫,欄序 · 型別 · 列數核對;DuckDB 表整檔備份後 `UPDATE … FROM` 對應表;U+FFFD 原樣不猜;冪等)。報告 `VIA_Reports\vdf\mojibake\`。自測 8/8。
  - `VDF_ENG065_DbImport_v0102.py` 薄尾:匯入前先 `ENG235 fix --apply --units-only`(`VIA_MOJIBAKE_FIX=0` 關掉);自測 6/6 + 前版鏈。
- 冊:交接案 smartdecode_v0100 · netunified_v0119 · mojibake_repair_v0100 · db_import_v0102;工作項 VDF-REQ020:fetch_decoder · repair_tool(收據後 VERIFIED)· workstation_run(操作員的手);需求 v0202(VDF-REQ020 原話 + 21 檔名)· 盤點 v0175(+4 站)。
- 工作站(操作員的手;容器看不到那 21 個檔):
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-medic sync --apply --branch claude/kind-cannon-pti15g
$V = (Get-ChildItem "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$env:VIA_FROM_VCGC = "YES"
$D = "C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_database"
python $V run --family vdf VDF_ENG235_MojibakeRepair scan "$D"            # ① 只讀:每檔每欄 可修 / 不可逆 + 樣本 → 先貼回這張
python $V run --family vdf VDF_ENG235_MojibakeRepair fix "$D" --apply     # ② 修:原檔備份到 $D\_pre_mojibake\;parquet 重寫(欄序型別不變)
python $V run --family vdf VDF_ENG235_MojibakeRepair scan "$D"            # ③ 複掃:應只剩不可逆(U+FFFD,要回源重抓)
$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'                # ④ 解取實用一次(擷取工具已帶解碼器;閘是你的手)
python $V run --family vdf VDF_ENG063_MonthlyRevenue run                   #    MOPS Big5 CSV 走 http_text → 正字
python $V run --family vdf VDF_ENG065_DbImport import "$D"                 # ⑤ 輸出實用一次:修好的單元匯進 DuckDB(匯入前再過一次解碼器)
python $V run --family vdf VDF_SystemManager db check                      #    看庫:表 · 列數 · 最晚日
```
貼回 ①③ 的 `[計] VDF_ENG235_MojibakeRepair_v0100 scan · 燈 …` 兩行、④ ⑤ 最後的 `[計]` 行;不可逆的欄(U+FFFD)列出來,我再回源對應到該抓的引擎。

## 十三、R76 設計稿「Veritas Header」視覺:1a VCGC · 1b VRN · 1c VDF 只跟視覺設計與顏色(VCGC-REQ182;容器 2026-10-12)
操作員令:「1a for vcgc html u/i design 1b for vrn 1c for vdf only follow visual design and colors.」(Claude Design 分享連結容器連不到)→「… sent to claude code web, check the workspace」(兩檔上傳;只差一個縮圖模板)。承同日「vrn vdf vcgc都是獨立操作台 只是顏色及lauout基本規劃相同」。
- 設計稿正本:`supportive modules/ui_support/VIA_UI_Design_VeritasHeader_v0100.dc.html`(sha256 入冊);稿全是行內樣式(無 `:root` 變數,CGC_MDL241 `plan` 對不上)→ 容器逐節取值。
  - 1a 母系統:米白紙底 `#f2f1ec` · 白卡 · 線 `#dbd9d3` · 字 `#1b1a17` · 淡 `#6b6860` · 青 `#2f6f6f` · 印泥紅 `#9e2b25`;左欄 268px;標題襯線(Cormorant Garamond)· 標籤等寬(SFMono / Consolas)· 中文襯線(Noto Serif CJK TC)。
  - 1b VRN 青花:頁首條 `#ccd8ea` · 字 `#16233d` · 鈷藍 `#24457f` · 白瓷左欄 274px · 六色頂條 · ADOPTED `#3d7a52`。
  - 1c VDF 汝窯天青:頁首條 `#cfe0dc` · 字 `#16302b` · 青瓷綠 `#3c6660` · 左欄 `#f2f8f6`(線 `#cfdcd8`)232px · 主鈕青瓷綠白字。
  - 不收:8–9.5px 等寬小字(低於 10px 硬條件)· 設計稿的 PASS / REVIEW / HOLD 文字色不當燈色(燈四色鎖定 2026-10-06)· 外部字型連結(零網路:本機有才用,否則 Georgia)· 未內嵌的印章 / 底圖(`assets/*.png`)。
- 冊:`VIA_UI_Template_SSOT_v0103.json`(v0102 不動):tokens 改色 + 新 token(serif · cjk-serif · seal · hair · chip · shadow · sys · sys-bg · panel-2 · nav · nav-dim · caption · aside-w · tag · brand · brand-sub · brand-zh)+ `systems`(VCGC / VRN / VDF / VAP 各自覆蓋)+ `design`(來源 · sha · 取值法 · 頁首規劃 · `css` 只用 `var(--token)` · `serif_selector`);字級 / 字重 / 日期 / auto_layout / presentation / 燈四色一字不動。
- 三系統各自的尾版(各讀冊上自己那一組;L120 互不寫檔):
  - `VDF_SystemManager_v0157.py`(1c):字級套件本體(v0154 v2;鏈上每份 `typekit_book` / `typekit_block`)換成本版 → 同一段 `<style>` 尾端接 `:root{全部 token}` + design.css(仍一段 style + 一段 script,冪等換新);JS 字體吸附對 `h1 / .via-serif / .brand` 放行;v0144 的 `ui_theme_load` 改讀冊尾版 + systems.VDF(via-theme 段 / 清單 theme 名跟冊走)。自測 9/9 + 前版鏈 v0131–v0156 全 PASS。VDF 頁 · vdf 夾 `*_latest.html` · 族群頁(MDL012 經尾版 `typekit_block`)全套。
  - `CGC_MDL274_HealthMatrix_v0115.py`(1a):同法(v0114 v2 本體;v0112 `ui_theme_load`);`portal` 後把入口頁 `VIA_Reports/VIA_UI_latest.html` 也補套;`theme preview` 出三系統頁首預覽頁 `VIA_Reports/review/vcgc_health/VIA_UI_DesignPreview_latest.html`(1a / 1b / 1c 各一區,inline token 覆蓋,只攤開冊值)。自測 11/11 + 前版鏈 PASS。
  - `CGC_MDL261_UIEngine_v0107.py`(1a 操作台):同法(v0106 v2 本體 · v0105 build 用的那份);design.css 把範本自己的 `--paper / --paper2 / --ink / --mute / --blue / --co / --soft / --r` 對到冊 token,所以 v0103 範本不改字就換色。自測 9/9 + 前版鏈 PASS。
  - 1b VRN:倉內不出 VRN 尾版(衝突裁定甲 / 撤回令);冊 `adoption.VRN` 寫了讀法 = 冊尾版 tokens + `systems.VRN`(燈四色仍鎖)+ `design.css` 接在字級套件 CSS 後;預覽頁 1b 區可先看。
- 容器實跑(全經 VCGC `run`):VDF `ui`(5 頁 新套 5)· `VDF_MDL012_FetchGroups ui` · MDL274 `ui` / `portal`(入口頁補套 inserted)/ `theme preview`(WRITTEN)· MDL261 `build`(3.4 MB 一段套件);每頁 `[VIA:DESIGN:VIA_UI_Template_SSOT_v0103.json]` 各一段;Chromium 無頭截圖核對(襯線在容器退 DejaVu Serif;工作站有 Cormorant Garamond / 新細明體才是設計稿字)。
- 冊:需求 v0203(+VCGC-REQ182 原話兩則)· 盤點 v0176(+C-vdf_manager_v0157 · C-health_matrix_v0115 · C-ui_engine_v0107;`theme preview` 豁免理由)· 交接案三件 + 工作項 VCGC-REQ182:vdf_1c · vcgc_1a_matrix · vcgc_1a_console(收據後 VERIFIED)· vrn_1b(操作員 VRN 側)· workstation_view(操作員)。
- 工作站一貼(看頁;改色只改冊出 v0104):
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-medic sync --apply --branch claude/kind-cannon-pti15g
activate_vdf                                                            # 1c:VDF 頁(汝窯天青)+ 族群頁
$V = (Get-ChildItem "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$env:VIA_FROM_VCGC = "YES"
python $V run CGC_MDL274_HealthMatrix theme preview                      # 1a / 1b / 1c 三區預覽頁(開 VIA_Reports\review\vcgc_health\VIA_UI_DesignPreview_latest.html)
python $V run CGC_MDL274_HealthMatrix ui                                 # 1a:VCGC 頁 + 健康矩陣頁
python $V run CGC_MDL261_UIEngine build --open                           # 1a:操作台
```
貼回:哪一頁 · 哪個顏色 / 字體 / 邊角要改(對照冊 `tokens` / `systems` 鍵名);1b 等 VRN-MAIN 下一版照冊套後貼 `[計]` 行。

## 十四、R77 清單先行:台股個股清單(VDF_MDL009)+ 主動式台股 ETF 清單(VDF_MDL010)先跑、輸出作為其他引擎的輸入、VDF 一鍵啟動(VDF-REQ021;容器 2026-10-13)
操作員令:「要先確令台股個股清單生成引擎自動更新以及主動式台股ETF清單自動更新生成引擎正常作業  輸出作為其他引擎的輸入  VDF 一鍵啟動」+ 問參數頁貼回(v0103 · 11 步矩陣沒有清單引擎 · 啟動就緒 GREEN 來源 v0157 · 資料庫目錄 STALE 25.8h · 分類 RED · 缺口 43 表自 2026-08-25)。
- 兩支清單引擎(擷取第一步 ①②,2026-10-03):`VDF_MDL009_TWStockList`(v0100–v0102;TWSE STOCK_DAY_ALL + t187ap03_L · TPEX OpenAPI;驗證 V1–V7;輸出 `0-1-TWStockList/tw_stock_list_latest.parquet/.csv` + `vdf_master_lists.duckdb` 表 `tw_stock_list` 增量)· `VDF_MDL010_ActiveETFList`(v0100;t187ap47_L · ENG077 代碼律 / 揭露律;輸出 `0-2-ActiveETFList/active_etf_list_latest.*` + 表 `tw_active_etf_list`)。容器自測(經 VCGC run):MDL009 7/7 · 9/9 · 5/5;MDL010 7/7。入口律 `VIA_FROM_VDFSM=YES` 或 VCGC;網路只走鎖版工具(雙閘在工具裡)。
- 「輸出作為其他引擎的輸入」本來就是冊上的硬規則:`VDF_FetchSystem_SSOT_v0106.json` 35 支引擎 `needs ['009','010']`;`VDF_MDL008` 清單不在不檢其他輸出;`VDF_MDL012` 族群頁清單先行(紅就停 rc 5)→ `activate_vdf` / `VDF_SystemManager all` 的 groups 步本來就先跑它們。
- 缺口 = 問參數頁那條一鍵(`via-vdffetch` → `CGC_MDL134 run --only $stepBook`):步冊 `CGC_MDL125` 沒有這兩步 → 矩陣看不到、並行道不先跑。三支薄尾(都不動 .ps1):
  - `CGC_MDL125_FixAll_v0112.py`:plan() = 前版 18 步 + datahome 之後插 `tw_list`(MDL009 尾版 run)· `etf_list`(MDL010 尾版 run);net · 逾時 600;自測 6/6 + 前版七檢。
  - `CGC_MDL134_ParallelLanes_v0102.py`:鏈冊 += lists(tw_list 等 datahome · etf_list 等 tw_list;同鏈序跑);資料鏈每步 after += etf_list(pip / node 安裝鏈除外);`--only` 子集沒列清單步也自動帶上(啟動器 `$stepBook` 與 `-Steps` 照舊);清單步子行程帶 `VIA_FROM_VCGC=YES`;自測 8/8 + 前版九檢。容器 `plan`:步 20 · 鏈 9(lists:tw_list → etf_list);`run --only datahome,hist_2023,global --dry`:5 步,清單步自動加入並先於 hist_2023 / global(離線全 SKIP,誠實)。
  - `VDF_ENG093_LaunchConsole_v0105.py`:矩陣最前兩列 tw_list · etf_list 鎖定必跑(checked · disabled · class lock;JS 的 boxes() 與 -Steps 不含它們,交並行道自動先跑);逐一引擎自測也測它們;頁首 v0105;自測 7/7 + 前版鏈;容器渲染截圖核對。
- 自動更新 = 每次一鍵啟動都先重抓當日清單並增量進庫;倉內沒有獨立排程器(`via_boot_update.ps1` / `VIA.ps1` 不呼叫清單引擎)—— 要每日自動就把 `via-vdffetch` 掛進每日鏈(操作員的手)。
- 冊:需求 v0204(+VDF-REQ021 原話 + 貼回)· 盤點 v0178(+C-fixall_v0112 · C-lanes_v0102 · C-launch_console_v0105)· 交接案三件 + 工作項 VDF-REQ021:list_engines_ok / list_engines_ok_etf / lists_first_book / lists_first_lanes / lists_first_page(收據後 VERIFIED)· workstation_run(操作員)。
- 工作站一貼:
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-medic sync --apply --branch claude/kind-cannon-pti15g
$V = (Get-ChildItem "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$env:VIA_FROM_VCGC = "YES"
python $V run --family vdf VDF_MDL009_TWStockList run          # ① 台股個股清單:真抓今天(雙閘在工具裡;閘關 = DENY 誠實)
python $V run --family vdf VDF_MDL010_ActiveETFList run        # ② 主動式台股 ETF 清單
python $V run --family vdf VDF_MDL009_TWStockList status       #    看 0-1 / 0-2 的 verify_report.json 燈與 vdf_master_lists.duckdb 列數
activate_vdf                                                    # ③ 問參數頁:前兩列 tw_list · etf_list 鎖定 → 按「用預設參數啟動」
```
貼回 ①② 的 `[計]` 行、`status` 那張、以及啟動後 lanes 存證裡 tw_list · etf_list 兩列(OK · 秒數)。
- 收尾(容器 2026-10-13 10:30 UTC):需求 v0206(VDF-REQ021 homes 只留交接冊 + 盤點冊 v0178;三支模組在 modules 欄)→ SDD X-REQ GREEN · 整體 YELLOW(X-REQ-OPEN 80 · X-LOCK 6 既有)· registry-sync 新 0 · 編號稽核 遺失 0 · 改身分 0 · 重號 0(冊內不一致 1 既有)· 重跑收據 cov_vdf_eng093 · vdf_manager_v0155 · vdf_manager_v0156 · chain(新 0 · 缺 0)· numbering 五件全綠 · handoff check 回到既有五紅(ENG086 v0102 · VRN FirstPageEngine v0130 · SUP_MDL749 v0116 / v0117 · CGC_MDL264 v0100)· test --quick YELLOW 紅 0(verb 46/46 · case 187/187 · 279 支 compile 錯 0;黃 = V-handoff-check 既有五紅 · P-entry 容器沒 pwsh)。提交 6a2e8dc8 → 55f74cd8 → 01d2f72a → dda04e7d → a4d50727 → e66668dc → b4540707 → d1a2c5b2 → 本次。
- 工作站貼回(操作員 2026-10-13 20:32(工作站本地時間;Invoke-VIA-VdfFetch v0108 → v0107 → CGC_MDL134 run)):單跑 VDF_MDL009_TWStockList v0102 run OK · 1,985 筆 · 12.4s(status 卡沒貼;verify_report 燈未見)。① 7 步舊清單補齊:台股上市櫃清單 GREEN 249s · 主動式 ETF 總清單 NODATA rc 2 63s(同一支 ENG077)· 主動 ETF 每日持股 NODATA rc 2 67s(PENDING_SOURCE 22 · 今日已抓 2)· 名碼官方定奪 GREEN 145s · 股票日快照 GREEN 85s(tw_universe +0,基準日 2026-09-21)· 新上市 / 下市 GREEN 50s(1,985 · NEW 0 · DELISTED 0)· 每日兩張清單檔 GREEN 39s(台股個股 1,985:加權 1,090 · 櫃買 895;主動式 ETF 22 已驗證 22)。② PLAN 步 20 · 鏈 9(lists:tw_list → etf_list)· LIVE 13 步 = 問參數頁 11 步 + 清單 2 步(問參數頁決定行仍印「步 11/11」:鎖定列不經 -Steps,道上自動帶上 —— 設計如此;道橫幅印前版 ENGINE_TAG v0101,功能已是 v0102)。道 1/13 datahome OK 11.1s · 2/13 tw_list OK 121.5s · 3/13 etf_list OK 46.3s · 4/13 hist_2023 OK 26.3s · 5/13 revenue_backfill OK 5.9s · 6/13 etf_universe FAIL 47.3s(ENG077 rc 2:官方冊消失 1 ['00998A' 主動復華金融股息] → MISSING_FROM_SOURCE 候查不刪)· 之後「[Invoke-VIAPython] 逾 1800s 已停」→ [activate_vdf] RED · all rc 124;步 7–13(global · fred · etf_fetch · etf_history · consensus · revenue_consensus · etf_revenue)沒跑完。
  - 判讀:清單先行 + 輸出餵其他引擎在工作站實證成立(VDF-REQ021:workstation_run VERIFIED);一鍵整程 RED 不是清單接線,是既有天花板。天花板根因:activate_vdf(Register v0277)→ via-vcgc run --family vdf VDF_SystemManager all → Invoke-VIAPython 沒帶 -TimeoutSec → 預設 1800s(VIA_PS_PyProgress_Module;$env:VIA_PY_TIMEOUT_SEC 可調,0 = 不設限);問參數頁等待(≤ 15 分)+ ① 7 步 698s + ② 道並行都在同一支 python 子樹內,整程被殺 → rc 124。VdfFetch-v0107 內層那次 Invoke-VIAPython 也沒帶 -TimeoutSec(同一條 env 可解)
  - 本次解法(操作員):`$env:VIA_PY_TIMEOUT_SEC = 0`(或 `14400`)後再 `activate_vdf`;長久解法要 Register v0278(activate_vdf 比照 via-in v0263 放寬天花板、結束還原),新 .ps1 版號待操作員逐件准(L70)。
  - 00998A(主動復華金融股息)官方冊消失 → ENG077 rc 2 → 道 etf 鏈停:操作員裁定下市 / 改碼或「候查不擋道」(VDF-REQ021:etf_universe_00998A)。持股 PENDING_SOURCE 22 = 揭露時點,資訊而已。
  - 工作站自報(L120 只攤開):VRN_SystemManager 尾版 v0198 未入註冊冊 / 未編號、註冊冊待同步 new 1916 · changed 108 · stale 85、main 本地獨有 112 提交未推 —— 工作站 `via-vcgc registry-sync --apply` 與推送是操作員的手。
  - 冊:需求 v0207(evidence ⑤ + next + 貼回原話)· 交接項 workstation_run VERIFIED + 新三項 one_launch_ceiling · etf_universe_00998A · lanes_banner_tag。
  - 收尾(容器 2026-10-13 13:10 UTC):需求 v0207 → registry-sync 新 0 · 編號稽核 遺失 0 · 改身分 0 · 重號 0 · SDD YELLOW(X-REQ GREEN)· 交接項 workstation_run 掛 lanes_v0102 收據(交接閘 VERIFIED 需收據;受理憑據 = 工作站貼回)· numbering 收據重跑綠 · handoff check 回到既有五紅 · test --quick YELLOW 紅 0(verb 46/46 · case 187/187)。
- R77c(操作員 2026-10-13「准 Register v0278 出版 00998A 標退役  VDF 資料庫狀況 STALE」):Register-VIA-Commands-v0278.ps1(操作員准 2026-10-13;L70):點源 v0277、只蓋 activate_vdf —— ② all 呼叫前比照 via-in(v0263):$env:VIA_PY_TIMEOUT_SEC 沒設 / 不是數字 / 小於 14400 就放寬到 14400 秒,跑完還原,設 0 照你的;env 由 pwsh 子行程(問參數頁 → VdfFetch)繼承,內層那次 Invoke-VIAPython 同受惠;其餘與 v0277 一字不差(diff = 點源行 + 10 行天花板段 + 旗標行);activate_vdf.cmd 梭照 glob 取尾版自動接上;容器無 pwsh:括號平衡 73/73 · 全景剖析 問題 0 · CGC_MDL157 自測 rc 0,函式本體要工作站實跑。VDF_ENG077_ActiveETFUniverse_v0106.py(薄尾,本體照尾版律仍是 v0101)+ 退役冊 functional modules/VDF/VDF_ActiveETF_Retired_SSOT_v0100.json(00998A 主動復華金融股息 · 裁定「00998A 標退役」2026-10-13 · 只增不減,撤銷填 revoked_at):① unify 之後濾掉退役碼(不入當日宇宙列 · 不入 SSOT csv · ENG051 不再抓其持股)② persist 之後註冊表 status=RETIRED · daily_required=FALSE(不刪列)③ 不計官方冊消失(rc 不因它回 2)· run 收尾印 [退役];自測 9/9(冊在 · 濾 · 撤銷不濾 · RETIRED · 離線 rc 2 誠實)。工作站下一次一鍵 / etf_universe 跑到就把 00998A 那列改標。VDF 資料庫狀況頁貼回(VDF_ENG093 v0105 · 2026-10-13 21:03:17):各步結果 PART 但那份是 LANES_20260924_145157(頁自己註明比本次決定早 = 今天那趟被殺前沒寫 LANES_*.json);資料庫目錄 FRESH(21:03 重點)· 分類燈 RED(ETF 滯後 48 · 宏觀 49 · 國際 47 · 其他 104;營收 NODATA)· 增量缺口 表 73 有缺口 32(tw__tw_daily_prices → 2026-08-25 缺 49 · tw_chip_inst / margin → 2026-08-25 缺 415 · gl__global_daily → 2026-08-25 缺 49 …)· 引擎狀況(FG_20261012T113922Z 族群跑):RED rc 1 = e054 TWDailyBackfill · e057 TradingValueBackfill · e056 ChipBackfill · e078 ActiveETFHoldingsHistory · e082 FinStatements · e066 GlobalUniverse · e074 FredMacroSSOT;rc 124 = e232 TWIndexOfficial · 011d AkshareFetcher;YELLOW e063 rc 2;GREEN 009 · 010 · e077 · 006 · e113 · e229 · e116 · e115。
  - 判讀:STALE = 今天一鍵被天花板殺掉(LANES 沒寫、頁掛 2026-09-24 那份)+ etf 鏈停;v0278 + 退役冊之後重跑一次才算驗(交接項 one_launch_rerun);FG_20261012 的 7 紅 rc 1 要 fg_runs log(交接項 db_stale_engines)。
  - 冊:需求 v0208 · 盤點 v0179(+C-activate_vdf_v0278 · C-eng077_v0106)· 交接案兩件 + 項 one_launch_ceiling / etf_universe_00998A → VERIFIED(收據)· 新項 one_launch_rerun · db_stale_engines。
  - 收尾(容器 2026-10-13 14:30 UTC):registry-sync 新 5 · 變更 8 · 退役 16(掃描器只把家族尾版算活件,ENG077 v0101–v0103 的本體列(尾版執行期 exec 載入)標 RETIRED;執行行為不變,自測 9/9)· 編號 --scope 要用 VIA 相對路徑(第一次用倉根相對路徑 → 寫入 無;退役冊是 VDF 正本,VCGC 子系統邊界閘擋下不編,照 VDF 其餘冊無表號)→ ENG +1 · MDL +1 · FNC VDF +12 · FNC CORE +1 · SSOT 列 +4 · 稽核 遺失 0 · 改身分 0 · 重號 0 · SDD YELLOW(X-NUM 回綠)· 收據 activate_vdf_v0278 · eng077_v0106 · tooling · vdf_manager_v0156 · chain(新 0 · 缺 0)· numbering 全綠 · handoff check 回到既有五紅 · test --quick YELLOW 紅 0(verb 46/46 · case 189/189)。
  - 工作站第二次貼回(2026-10-13 23:52 本地):道 1/13 datahome OK 25.9s · 2/13 tw_list OK 75.3s · 3/13 etf_list OK 23.7s · 4/13 hist_2023 OK 19.8s · 5/13 revenue_backfill FAIL 6.7s · 6/13 etf_universe FAIL 41.0s · 7/13 consensus FAIL 45.7s → 仍「[Invoke-VIAPython] 逾 1800s 已停」· all rc 124。判讀:1800 秒整點被殺 + etf_universe 仍 FAIL = 那個視窗跑的還是 v0277 + ENG077 v0105(分支沒併或沒重新點源;v0278 會在 ② 前印「天花板放寬到 14400 秒」、旗標行印「尾版 v0278」)。尾段三個 `python $V run …` 全部 can't open file 'run' = 那個視窗沒定義 `$V`(改用 `via-vcgc run --family vdf …` 短令,或先定義 `$V`)。新紅 revenue_backfill · consensus 要 VIA_Reports\lanes\RUN_<stamp>\*.log 尾段才能定根因。

## 十五、VRN 自報(工作站 `C:\測試樣本報告` · VRN 貼回 v0100 · 20261013T220225 · 2026-10-13T22:03:56;L120 只攤開不代修)
來源:操作員貼回的 VRN 五段報告(AMBER · FAIL 0 · WARN 9 · SKIP 0 · PASS 45;AutoTest 第 1 輪 AMBER PASS 210 · WARN 20 · SKIP 4 · FAIL 0;樣本 個股 58 / 534 · 頁 134 / 477 · 年度財報頁 115;鎖 NEW 0 · HELD 487 · BROKEN 0 · OPEN 919;待修 599 = 優先1 5 · 優先2 268 · 優先3 326)。VRN 的 VRN_Main / autotest / titletrim / 鎖帳本都只在工作站鏈,不在本倉;本節只攤開,不改 VRN 任何檔。

| # | 閘 | 現況 | 誰的手 |
|---|---|---|---|
| V1 | G14 LOCALDB | 新鮮度 過期 58:資料庫最新價日 2026-08-25(今天 2026-10-13) | **VDF**:同 R77c 根因(一鍵被殺、tw_daily_prices 停在 2026-08-25);v0278 + 重跑後就不過期 |
| V2 | P13 LOCAL-SSOT | 本機較新 4 · 只在本機 13(VRN_FinLexicon_SSOT_v0110(.integration) · VRN_LayoutRestore_SSOT_v0101(.integration) · VRN_MasterList_v0100 · VRN_MDL024 … v139O · VRN_MDL027 …) | 操作員:推到母倉或交給 AI;倉內不出 VRN 尾版(衝突裁定甲 / 撤回令) |
| V3 | P16 / G18 LOCK | 未鎖 1 支 VRN_PanoramaProbe.py(沒有已知答案證明);上次之後改過 2 支(VRN_TitleTrim_v0100 · VRN_TickerRecord_SSOT_v0100 換新指紋) | VRN-MAIN:給 PanoramaProbe 一組已知答案才鎖 |
| V4 | G19 FOCUS / G06 BATCH | 找不到年度財報頁 1(MQ-1560 20260520.pdf = 掃描檔 OCR_REQUIRED)· no ruled table 5(MQ-1560 · 光焱 7728 · 宏致 3605 Takeaway · 國光生 4142 · 瑞基 4171;後四檔為中信 / 凱基 Note 型,表在第 2 頁但列標對不到科目) | 操作員:確認那五份本來就沒有年度財報表,或告知頁碼;MQ-1560 要 OCR |
| V5 | 優先 1(5 項) | cover.rating MISSING ×4(Daiwa-3653 · Daiwa-6278 · GS-1590 20251203 = 首頁 Target price: n.a. / 無評等字樣;MQ-1560 無文字層)· cover.target_price MISSING ×1(MQ-1560) | VRN-MAIN:Daiwa / GS 這三份首頁沒有評等字,MISSING 是誠實;MQ-1560 要 OCR |
| V6 | G13 BOOKS | 電話 ENGINE_ONLY 11 · BOOK_ONLY 14;目標價 DISAGREE 1(慧洋 2637:engine 104 vs book 12.2)· ENGINE_ONLY 20;恆等式 GM_DIV FAIL 2 · OPM_DIV FAIL 37 · BS_ADD FAIL 20(INSUFFICIENT 居多) | VRN-MAIN:兩值都留的設計沒錯;慧洋 104 vs 12.2 像單位 / 列抽錯,要人判 |
| V7 | G15 REGIONS · G17 TITLETRIM | 截取完整度未達 99.9% 26 檔(97.4%–98.7%)· 標題 57/58 · 首頁基本資料 VERIFIED 286/524 · SINGLE 109 · 資料庫引擎 ReportTitle 與 def02 標題不同 50 檔(照列不改) | VRN-MAIN |
| V8 | P09 ACCEL | 加速器未掛上 2 個動作(G19 逐檔掃頁 534 項 31.5s · G17 逐檔 58 項 7.2s:PyMuPDF 不能多執行緒共用)· P00 退回 stdlib 執行緒池(6 項 9.1s) | VRN-MAIN:設計限制,照報 |
| V9 | 3.3 對不到科目的列標 261 格 | 多為 Daiwa 現金流 / 比率列標(Capex/sales、EV/FCF、ROIC、WACC、Debtor days …各 4 次)與中文(其他資產 · 流動負債分配後) | VRN-MAIN:詞表 / 同義字冊要加列標;倉內 VRN 正典不動 |

## 十六、R78 在地測試全景修補(操作員 2026-10-14;VCGC+VDF,VRN 不動;六流程並行)
令:「VRN VDF VCGC已經是獨立系統不互相影響 各有各的MAIN 用VCGC節省TOKEN工具全景式檢視這個在地測試VRN SYSTEM MANAGER及關連一切 確認所有PY PS工具都咬加裝最新加速器 所有連結項目JSON格視資料流動 可順利運作掌握 識別可同步修正 或順序修正的錯誤 用AST定位點錨點 再不發生九頭龍風險不損壞引擎不傷害系統的模式將為成功鎖定的問題看能否三步驟內解決 流程跟兩天內的紀錄相同 錯誤應該不住降低減少 同步六個獨立流程進行修補完善加快速度 三個系統各有各的MAIN 此對話指處理VCGC VDF 不動VRN」。貼回:貼回(2026-10-14):activate_vdf 旗標 v0278 已生效;[2/9] ask 逾時沒點(內層 NODATA rc 2)但步燈 GREEN rc 0;[4/9] groups GATED rc 4(視窗沒設閘);[6/9] usertest RED rc 1(MDL012 v0107 usertest 綠 39 紅 1 static)→ all RED rc 1;引擎狀況頁 FG_20261012T113922Z:rc 1 = e054 e057 e056 e078 e082 e066 e074,rc 124 = e232 011d;健康矩陣 VDF 黃 26 · VCGC 黃 67;產品閘(2026-09-13)G6 鑰匙守衛 FAIL(FRED 鑰明文 9 支舊檔)· G2 WARN 孤梭 3;工作站 SDD RED(VRN v0204 未登記);問參數頁 02:42:50 13 列 · consensus 用 VRN_ENG071_CnyesFusion_v0103.py · 資料庫 STALE · 缺口 56。

| 流 | 發現(AST 錨點) | 修(≤3 步 · 薄尾 / 冊,本體不動) | 剩下誰的手 |
|---|---|---|---|
| S1 usertest | S1 usertest:容器 MDL012 v0108 usertest --browser off = 綠 39 · 紅 0(冊 v0107 之後仍 39/0);工作站那 1 紅是資料相依的 static 列,容器看不到 → 要 VIA_Reports\vdf\ui\VDF_FetchGroups_USERTEST_latest.json 的紅列(cmd_usertest 本來就印 [RED] key · note);find_browser 已含 VIA_BROWSER_EXE → Playwright → PATH → Program Files Chrome / Edge | 無(容器 39/0) | 操作員貼紅列 |
| S2 ask 燈 | v0155 L190 RUN_CMD · L294 pwsh -Command;Open-VIA-VDF-v0103 Stop-VIAOpenVdf 只設 LASTEXITCODE | S2 ask 燈:VDF_SystemManager_v0158(薄尾;本體 v0155 不動):Open-VIA-VDF-v0103.ps1 只設 $global:LASTEXITCODE 不 exit,pwsh -Command ". '<opener>'" 回 0 → 步燈假綠;v0158 把那條 -Command 補 `; exit $LASTEXITCODE`(只在 pwsh · -Command · 點源形狀 · 沒 exit 時),RUN_CMD 本體換成本版、冪等(MDL012 v0108 再載本檔不疊層);自測 7/7(含 v0157 → v0155 前版自測) | 工作站重跑看 [2/9] |
| S3 引擎紅 / 逾時 | ENG232 v0101 run L104-108 · v0100 run L203-227(L225 單次 upsert);MDL008 v0107 L96 BOOK_V0106 · v0101 child L314 `HERE / row[file]`;MDL012 v0107 launch_child L368 max(timeout, timeout_s) | S3 引擎紅 / 逾時:e232 rc 124 根因 = 族群冊帶 --start 2022-07-01 關掉 v0101 增量、v0100 整段(1,118 營業日 × 7 外呼 + 1.4 s/日)抓完才 upsert 一次 → 1800 s 被殺零進度;VDF_ENG232_TWIndexOfficial_v0102(薄尾):31 天一段逐段 upsert · 給 --start 但庫內兩指數已過它就從 next_start 接續 · 任一段 OK = OK · DENY/FAIL 當段即停;自測 10/10(v0101 8/8 · v0100 9/9)。冊 VDF_FetchSystem_SSOT_v0107:e232 → v0102 + timeout_s 14400 · e077 → v0106(退役冊生效)· e054 仍 v0109(v0110/v0111 是唯讀狀態卡,why_v0104 裁)· 其他 34 支同 v0106;VDF_MDL008_FetchSystem_v0108(薄尾):冊按尾版 glob(MDL012 早就 glob,兩邊同一本)· 子行程從本版起;自測 8/8(v0107 → v0101 鏈全 PASS)。011d:14400 s 列上限已照 MDL012 launch_child / MDL008 run_v0107;_call 無逐呼叫逾時,要 011d_live.log 再定。e074 rc 1 = 任一 FRED 序列 FAIL 即紅(紅冊設計;via-fred status → --retry-parked)。e054 e057 e056 e078 e082 e066 rc 1:自測全綠,rc 1 只能是執行期例外([MDL008] 例外 行)→ 要 VIA_Reports\vdf_fetch\_logs\<id>_live.log(每次同 id 覆寫,重跑前先複製);e054 是道頭,e057/e056 的「交易日曆空」多半是它的連鎖 | 操作員貼 _logs/<id>_live.log |
| S4 加速器 / 橋 | S4 加速器 / 橋:BridgeSweeper v0111 乾跑 PY ACCEL supportive 2680/缺 0 · registry 1560/缺 0 · VDF 533/缺 0 · NET VDF 缺 0 · PS-ACCEL supportive 327/缺 0 · launchers 27/27 · VDF 171/缺 0 · 根層 PS 441 缺 0;鎖 Celeritas v1141 / Aegis v1652 sha 對,SUP_MDL737 v0110 · SUP_MDL740 v0119 尾版,PS7 v1141,17 支活 PS 入口全有 PS-ACCEL;ToolMatrix GREEN(PY 1586/1586 · 網 73/73 · VDF 網 123/123 · PS 677/677 · 模板 188/188)。G1 修:supportive modules/accelerator/VeritasCeleritas.py(未版號正本座,894779cb 2026-10-08 sweep 把橋注在 from __future__ 之前 → SyntaxError)→ 橋段移到 __future__ 之後(py_compile 過;R2 P1 同類修法;80276330 之前就是沒橋的 shim)。G2:SUP_MDL740_NetUnified_v0119 沒進版本登記冊(VIA-TOOL 只到 v0118)→ 本輪編號 scope 帶它。G3:PS 模板既有債 28 支(VDF 0 支;L70 操作員的手)。EnvManager 其餘 RED = 容器事實(無 pwsh / venv) | G1 正本座橋段移位;G2 編號 scope 帶 MDL740 v0119 | G3 L70 |
| S5 冊 / 資料流 | S5 冊 / 資料流:health 檔族 135(紅 0 黃 26 綠 109)· links 193 條 GREEN 191 STALE 1(Essentia 卡書 370h)GATED 1(鏈快照離線)· 引擎矩陣 100 支 可啟動 86 不能起 0 缺件 1(polars 容器)· 表矩陣 78 GREEN 75 GRAY 3;冊→讀者→懸空:FetchSystem e054/e077 釘舊(→ 冊 v0107 修 e077;e054 故意)· Fetch_Orders 004 九道不在 Param map · Param_Engine_Map 27/57 by_engine 鍵指不存在檔(ENG053 v0103 版本前進另案)· TableHeader 3 GRAY(table register --apply 已自登)· FunctionMatrix(fn register --apply:項 1739 · NEW 91 · GONE 61 · 留白 94 → 編號後 fn number pull);dormant 乾跑 22 支 _sha 副本 = 操作員 2026-10-10 還原裁定,**不得 --apply**(會再搬走、再弄壞 MDL008);VDF_AutoCodeRegistryEngine_shad7fd781ac69f.py 無號無登記要裁定;版號洞 3(SM v0138 · ENG090 v0101 · ENG234 v0101 = 從未存在 / 批573 刪) | 冊 v0107 · MDL008 v0108 · fn/table register --apply · fn/table number pull | dormant 裁定 · Param map 另案 |
| S6 鑰匙 / 產品閘 | S6 鑰匙守衛 G6:同一把 32 hex 鑰(sha256 指紋 = ProductGate KEY_HASHES 第 2 筆)在 10 支追蹤檔 15 行:new modules engines/VDF_MDL003_SentimentMacroEngine.py(34 · 92)· VDF_final/{README.md 156 · cockpit/index.html 447 · 1254 · config/macro_ssot.json 9 · vdf_fetch_matrix.json 8 · vdf_fetch_matrix.md 11 · via_master_ssot.json 49 · 164 · src/vdf_core.py 91 · src/vdf_fetchers_macro.py 138 · 219}+ references/intake/VIA_VDF_Engines_b716/VDF_MDL003_SentimentMacroEngine_2.py(34 · 76;MANIFEST 鎖位元);活讀者 0(ENG074 本體 v0103 fred_key 只讀 env / .fred_api_key / 提示;ssot_path 讀已遮罩的 b360);鑰已在 git 歷史與 origin/main(660834a5)→ 無論遮不遮都要換鑰。遮罩法(待准):13 行換 <REDACTED:VDF_FRED_API_KEY>(b360 / _from_vap 已用同款);收容區「原件零觸碰」與 b716 MANIFEST 要操作員裁;AI 不自改。G2 孤梭 WARN = ProductGate v0102 只讀最新 Register 檔 + 大小寫集合差(Windows 大小寫不分)→ ProductGate v0103 薄尾:register_fns 沿 dot-source 鏈(v0278 → … → v0243)收 function global: · 梭名小寫比對;G6 key_scan 不動;自測 [計] CGC_MDL133_ProductGate_v0103 薄尾 7/7 · PASS | ProductGate v0103(G2);G6 不動(待裁) | 換鑰 · 准遮罩 |

- 冊:需求 v0209(新 VDF-REQ022)· 盤點 v0180 · 交接案 vdf_manager_v0158 · eng232_v0102 · mdl008_v0108 · productgate_v0103 · 交接項 14 件(VERIFIED 6 · PENDING 8)。
- 操作員:① 貼 VIA_Reports\vdf\ui\VDF_FetchGroups_USERTEST_latest.json 的紅列(或 usertest 印的 [RED] 行)② 貼 VIA_Reports\vdf_fetch\_logs\{e054,e057,e056,e078,e082,e066,e074,011d}_live.log 各最後 30 行(先複製,下次跑會覆寫)③ FRED 鑰:換鑰 + 准不准遮罩 13 行(含 b716 收容件與 MANIFEST)④ groups 要在自己視窗設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 再跑 ⑤ 工作站 via-vcgc registry-sync --apply 登 VRN v0204(VRN 的手)⑥ 併分支後 activate_vdf 重跑一次(one_launch_rerun)。

### 十六-b、R78b(貼回 ② 三條道 log 尾 + 收尾實錄)
- 操作員貼回 ②(2026-10-14 03:00 前後):activate_vdf 第三趟(工作站仍是 v0155 鏈:ask 逾時沒點 NODATA rc 2 但步燈 GREEN rc 0 · groups GATED rc 4 · usertest RED 綠 39 紅 1 · all RED rc 1)+ RUN_20261013_235304 三條道的 log 尾:revenue_backfill = VDF_ENG075 v0105 → v0104 → v0103 rebuild_view L292 duckdb.connect(DB_TW) → IO Error「vdf_tw_market.duckdb 正由另一個程序使用 · File is already open in …uv\python\cpython-3.12.12…\python.exe (PID 372)」;consensus = VRN_ENG071_CnyesFusion_v0103 run L189 同一把鎖、同一個 PID 372(VRN 檔只讀不改);etf_universe = ENG077 v0105 的 00998A MISSING_FROM_SOURCE(v0106 退役冊已修,待併)
- S7 道上的 DuckDB 鎖:鏈冊 tw 鏈本來就序跑(hist_probe → hist_2023 → group_class → revenue_backfill → consensus → revenue_consensus),單寫者律沒破;持鎖的 PID 372 是**前一趟**(20:32 那趟被 Invoke-VIAPython 1800 秒天花板殺掉)留下的引擎子行程 —— 外層只殺到 MDL134 本體,_exec 的 p.kill() 來不及跑,孤兒抓著 vdf_tw_market.duckdb;Hydra 律 H3 只看 FixAll 心跳與步鎖(鎖記本體 PID,本體死了就回收),看不到孤兒。CGC_MDL134_ParallelLanes_v0103(薄尾;本體 v0101 / v0102 不動):① Windows 子行程起在 Job Object(KILL_ON_JOB_CLOSE,編排被殺子樹一起死;逾時殺整個 job)② 子行程 PID 記進該趟 CHILDREN.json,preflight 加 H3b 孤兒(沒 ended 且 PID 活)列 pid 與步名(WARN,零 force 不代殺)③ 步 log 的 DuckDB 鎖訊息 → 道上 note 前綴 DB_BUSY pid N 持 <庫名>;自測 9/9(含 v0102 8/8 · v0101 九檢)
- S8 收尾實錄:v0158 的自測把 v0157 → v0128 前版鏈輸出導進緩衝 → 交接閘 9 案(argv 尾版 VDF_SystemManager --selftest,標記是 v0128/v0129 的 [計])rc 0 但 marker False → EVIDENCE_INVALID;VDF_SystemManager_v0159(薄尾):自測先照印 v0157 整條鏈,再重做 v0158 六檢,run / all / ask 行為一字不差。SUP_MDL740_NetUnified_v0119 補進版本登記冊(VIA-TOOL-0249,只增一列;VIA-SUP-TOOL 由 CGC_MDL237 依冊發)
- 已知雜訊(不在本輪):`<unknown>:3: SyntaxWarning: invalid escape sequence '\*'` = CGC_MDL156_VIAAcceleratorControl_v0114.py 第 3 行說明字串的 `\*`(非 raw 字串),AST 掃描每次剖析都印一次;修法 = MDL156 下一版把它寫成 `\\*`,或掃描器用 SyntaxWarning 濾器剖析;無功能影響。
- 冊:需求 v0210 · 盤點 v0181 · 交接案 vdf_manager_v0159 · mdl134_v0103 · 交接項 +2(manager_selftest_output · lanes_db_lock_orphan)· engine_reds_logs 理由更新;版本登記冊 +SUP_MDL740 v0119(VIA-TOOL-0249)。
- 操作員:① 先看 PID 372 是誰:Get-CimInstance Win32_Process -Filter "ProcessId=372" | fl ProcessId,ParentProcessId,CreationDate,CommandLine;是 VIA 引擎孤兒就 Stop-Process -Id 372,再跑 revenue_backfill / consensus(或整趟);② 併分支後 activate_vdf:ask 逾時應 YELLOW rc 2、00998A 印 [退役]、e232 逐段入庫;③ 仍要 e054 e057 e056 e078 e082 e066 e074 的 _logs\<id>_live.log 尾 30 行(FG 那趟的 rc 1 不一定同一把鎖)
