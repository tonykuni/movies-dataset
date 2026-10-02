# AI 夜間紀錄 · 2026-10-02(明天從這份接續)

> 只增不減。每一輪工作站交接紀錄(docs/handoff/workstation/WS_HANDOVER_*.md)推上來,AI 讀完就在這裡加一段。

## 起點(UTC 2026-10-01 21:20 · 台北 10-02 05:20)

- 工作站已貼上 6 輪迴圈:每輪 `git pull` → `via-realtest -AutoInstall -NoOpen`(自動取最新版號)→ 交接紀錄推 GitHub → 等 20 分鐘;結束碼 0 即停。
- AI 端:每 5 分鐘讀 GitHub(新交接紀錄 · PR CI · main CI);紅就修 → 開 PR → 綠即合併。
- 不做:強制關機(AI 沒有通道,也不在每天用的指令裡埋關機;要的話操作員自己在迴圈 break 那行加 `Stop-Computer -Force`)。
- 不做:代設網路同意閘(-AutoInstall 是操作員親手的開閘)。

## 已在 main 的(今晚之前)

| PR | 內容 |
|---|---|
| #409 | via-realtest v0100(25 PS 加速器 · VDF ∥ VRN ∥ 覆蓋 ∥ ENV ∥ 衝突 · 紅字 / 黃字) |
| #410 | ENV MANAGER 逐項進度 v0101 · realtest v0101 · VRN 鏈 RED 0(ENG086 v0119 · test_SourceProvenance) |
| #411 | realtest v0102(拉齊 → 實測 → 樣本 → 交接紀錄 → 推 GitHub)· v0103(三路線 · 環境完整安裝 · 全景 AST 錨點 · 總控頁) |
| #413 | VDF 74 支逐支自測 RED 5 → 0(ENG089 v0108 · ENG074 v0107 · ENG088 v0105 · ENG072 v0105 · ENG082 v0107)· realtest v0104(例外進交接紀錄) |

## 本段(R47)

- realtest v0105:VCGC 下放檢查接進每一輪 —— `sdd check`(工作流冊)與 `ssot panorama`(參數 / regex / 同義字 / 編號 / 上下連結)背景並行,紅黃列逐行進交接紀錄。需求 VCGC-REQ109。

## 工作站第 1 份交接紀錄(v0103 · 04:51 台北)摘要

- ENG093 ⑦ 紅 → #413 的 ENG089 v0108 修好(下一輪應消失)。
- 環境:ENV RED → AMBER(工具冊 rc 2 · 家族境補庫 rc 1)。
- 樣本驗證 305 件:有首頁 RED —— 首頁文字 / 表格 / 摘要是操作員保留範圍,AI 不動。
- v0101 中途例外、沒寫貼給 AI 檔 → v0104 起把例外收進交接紀錄。

## 輪次紀錄

(下面每一輪由 AI 追加)

### R48 · UTC 21:56–22:30(台北 05:56–06:30)

- main CI 在 #415(另一 session 的 VCGC v0185)合併後紅:test_11 總控頁與正主不同步 → #416 依正主重產(2 行),契約 19/19 → 綠即合併。
- 工作站第 2 份交接紀錄 `WS_HANDOVER_20261002_051143`(跑的是 v0104,HEAD 3ec73468):
  - **紅 ① 實測本體 v0101 一進 ③ 就拋「找不到屬性 'after'」@ 行 197**(04:15 那輪的「v0101 例外」也是它)。Celeritas PS7 模板開了 StrictMode,五條並行線只有 ENV 有 `after` 鍵 → VDF ∥ VRN 兩條鏈整輪沒起跑。
    修:`Invoke-VIA-RealTestCore-v0102.ps1`(只改那一行,`$ln.Contains("after")`)+ `Invoke-VIA-RealTest-v0106.ps1`(呼叫 RealTestCore 尾版)。舊 v0101 不動(L70)。
  - **紅 ② VCGC 全功能串測 紅 2 站,名字沒進紀錄**:站列是 `[RED   ]`(補空白),v0104/v0105 正則只抓得到 `[YELLOW]`。v0106 改 `\[(RED|YELLOW)\s*\]`,下一輪就看得到是哪兩站。容器同一指令:綠 6 · 黃 1(P-entry:容器沒 pwsh)· 紅 0。
  - 環境 AMBER(工具冊 rc 2 · 家族境 rc 1;VDF_MDL003 SentimentMacro 自測 NODATA 1 → 被記 FAIL):已知、未擴張。
  - 樣本 305 件:全文覆蓋 100%、缺數字 0;總判 RED 來自 ENG072 首頁 RED(操作員保留範圍,AI 不動)。
  - 交接檢查 GREEN(findings 0)。
- 需求冊 v0134:+VCGC-REQ111(本修);操作員 R48 原話「子系統向上通報 SYNC TO VCGC · VCGC 邊看 SSOT 編號」歸 VCGC-REQ110(母子連接)加引述。

### R49 · UTC 22:30–02:00

- 工作站自 UTC 21:11 後沒有新交接紀錄(停滯);v0106(修 StrictMode 'after')已在 main,等工作站下一輪。
- PR #417(另一 session · VCGC v0186)撞號解掉:main 為準,#417 改 REQ112 / REQ113 · FNC-C4031 · 需求冊 v0135 重建;44 case 重跑全綠。CI PS7 job 卡在「黃也退出 1」(CI 檔要補 exit 0,被系統判為繞過 CI 擋下)→ 待操作員裁。
- VCGC→VDF 啟動:VDF 鏈 RED 0;74 支逐支 GREEN 65 · RED 0。
- VDF 輸入範圍 / 輸出表頭歸 VDF 管理員(VDF-REQ016):`VDF_InputUniverse_SSOT_v0100`(IN 3 · OUT 5 · E 11 · 順序照 main 工作流冊)· `VDF_SystemManager_v0121`(universe headers / list / check / loop / frame / validate;驗證經 CGC_MDL249)· `VDF_ENG232_TWIndexOfficial_v0100`(加權 / 櫃買官方指數;隔離區收容件 b360 解析,TA-Lib 0,網路走 SUP_MDL740)。
- VRN 代號 regex 四冊收斂:僅攤開分歧,待操作員裁(未動 VRN 冊)。

### R50 · UTC 01:30–03:30

- PR #420(R49)CI:UAT 綠;PS7 gate 紅 = main 同病(#417 後 main 也紅)。本 PR 先補掉能補的「母子連接 VCGC-REQ113→VCGC-WKF012 單向」(link --apply → VCGC 工作流冊 v0111);剩衝突哨兵黃(ETF 名碼 00980A/00981A/00982A 待操作員裁),步驟 rc 全是 0/2,但 job 仍以 1 結束(PS 步驟最後的原生退出碼外漏)→ CI 檔問題,待操作員裁。已在 PR 留言後合併(b2350b5b)。
- 操作員 R50 令:動作引擎化 · 管理員串流程 · 版號 + 時間鎖 · Parquet 由 DuckDB 管(增量)· 三方對照 · 三表同日數量 · 兩個管理員互比一樣強(VDF-REQ017)。
  - `VDF_InputUniverse_SSOT_v0101`:+OUT-06 加權三來源 · OUT-07 三表同日代號數 · xcheck / parquet / lock 節 · 順序 15 站收在 E-11:lock。
  - `VDF_SystemManager_v0122`:universe xcheck(ENG232 官方 · ENG055 tw_market_agg.taiex · yfinance ^TWII 代理;價量 / 籌碼 / 成交值三表個股代號逐日比)· parquet(寫手 CGC_MDL238,目錄列數沒變略過)· lock(VDF-WKF011 的尾版 + 自測 + VIA_LampLock)· parity。OUT-01/06/07 只增進 DuckDB。自測 11/11 + 前版 14/14。
  - `VDF_ENG232_TWIndexOfficial_v0101`:不給 --start = 兩指數 MAX(date) 較早者 + 1 天;已最新零外呼。8/8 + 前版 9/9。
  - `CGC_MDL252_ManagerParity_v0100`(中央一支,VDF/VRN 不互相匯入):AST 動詞盤點 + 11 項能力表。初測 VRN 缺 4、兩邊都缺 3 → 補完後 **GREEN 11/11**。
  - `VRN_SystemManager_v0111`:outputs headers / frame / validate / loop / xcheck(VRN_ENG393 三重對照彙總)/ parquet / lock。11/11 + 前版 PASS。
  - 工作流冊 VDF v0102(+VDF-WKF011 十步)· 需求冊 v0137(+VDF-REQ017)· 盤點冊 v0123(+4 站)· 交接案 4 個全過 · 編號稽核 遺失 0 / 改身分 0 / 重號 0。
  - 容器實跑:xcheck / parquet / validate OUT-06 = NODATA(無實庫;資料家為 Windows 路徑)照實;WKF011 = OPEN,待 SDD selftests → real → lock --apply。
- 工作站第 3 份交接紀錄 `WS_HANDOVER_20261002_080732`(main bd405ee6):
  - ④ PS 加速器橋 155/156:唯一缺的是 `WorkOps/engines/.venv_pm/Scripts/Activate.ps1`(venv 產物,第 3 次重複)→ `CGC_MDL230_ToolCoverageProbe_v0105`:含 pyvenv.cfg 的夾不算 PS 尾版。3/3 + 前版全 PASS。
  - VCGC 站 GATE `policy_step`(V-handoff-check · V-status · upd:DeckServer)+ 八路衝突 BLOCKED(待裝 6 段)· paddlepaddle 未裝(VRN 擷取逾時)· 本機 TA-Lib 可 import:環境面,操作員手。
- R50 收尾:
  - PR #421 UAT 紅兩層:① test_11 總控頁與正主不同步(本 PR 加 CGC_MDL252 → 中央治理模組 260 → 261)→ 照先例依正主重產(契約 19/19);② 第 10 步紅使第 13 步(pip duckdb/pandas)被跳過,第 14 步才缺庫 → v0122 自測補「duckdb 不在 = ②–⑧ 照實略過」(防禦,重現過再修)。
  - SDD:自測整輪(63 支)→ real:VDF-WKF011 OK(10 步全 OK,層級 selftest)→ `SDDValidator lock --apply` → **VIA_LampLock_v0108:VDF-WKF011 LOCKED · 鎖於 2026-10-02 02:32:06 · 10 支引擎尾版 + 編號**;`universe lock` = LOCKED。
- R51(PR #422 已合):操作員「所有檔案加入加速器 vdf檔案加入網路工具」→ 正主注入器 CGC_MDL124 v0108 全樹掃:PY 加速器 1771/1771 · VDF 網路工具 132/132(最後 10 支是 VAP/ASSETS/SCOPE_COPY 的 VDF 副本)· PS 0 缺;其餘全是注入器自己的排除規則(HTML_UI 封印 21 · 閘唯讀 10 · b514 凍結 4 · 唯讀正本 1 · 加速器本身 1 · VDF 歷史版 23)。
- R51b(操作員「你決定自動完成」三項待裁):
  - ① 主動 ETF 名碼衝突 00980A / 00981A / 00982A(種子冊與批104 矩陣輪錯一位):根因是 FLOW_ENG023 的 --refresh 只轉 SEED_KNOWN,衝突態與 34 檔待驗永遠沒人處理 → `FLOW_ENG023_FlowTwActiveEtf_v0101`:官方名錄(t187ap47_L + STOCK_DAY_ALL,經 SuperAccel.fetch、閘在工具裡)定奪,誰跟官方名一致取誰,原值留 seed_*;兩候選都不符照實留衝突;名稱不符記 NAME_MISMATCH_OPENAPI 不覆寫。沒收到官方名錄 / 仍有衝突 = rc 2(不算成功)。自測 10/10 + 前版 6/6;容器閘關實跑 = SKIP rc 2、冊不動。第三方佐證(Yahoo TAI meta)00980A 野村 · 00981A 統一 · 00982A 群益,與矩陣一致。冊由官方資料寫,不由 AI 手改(AI 直改註冊冊兩次被權限擋,照擋)。
    操作員一步:工作站開同意閘 `via-vcgc run FLOW_ENG023_FlowTwActiveEtf --refresh` → 衝突哨兵 ③ 轉綠 → gate GREEN → CI PS7 閘綠。
  - VCGC v0187:`run` 給檔路徑時 v0168 的 _tail 回相對路徑、子行程 cwd 換到引擎夾 → 路徑拼兩次(handoff test 實錄 rc 2)→ 一律轉絕對路徑;stem 多找 FlowSystem 引擎夾。自測 10/10 + 前版鏈全 PASS([交接入口] fail=0)。
  - ② PS7 CI 紅:根因就是 ① 的衝突 WARN 讓 gate YELLOW;CI yml 放行被判繞過(照擋),走 ① 根治。
  - ③ VRN 四冊代號 regex:裁定保留各冊範疇(STOCK4 · INSTRUMENT_ALL · TEXT_EXTRACT_STOCK),探針只比同範疇(下一批:範疇冊 + CGC_MDL185 v0101)。
  - 盤點冊 v0124(+C-etf_registry_resolve)· 需求冊 v0139(VDF-REQ014 引述 + 證據)· 交接案 etf_registry_resolve / entry 全過。
  - 既有紅(非本批):V-systems 的 VRN logic RED = VRN 自家邏輯冊 v0112 記 ENG086 v0118、磁碟已 v0119(R43 起);冊歸 VRN,VCGC 不改。
- R51b 收尾:PR #423 合併(e1a5784f)。UAT 第一輪紅 = test_11 總控頁嵌 VCGC 尾版說明行(v0187 換了)→ 依正主重產(契約 19/19),後面 pandas 錯是 pip 步被跳過的連帶。PS7 紅 = 已知 ETF 衝突 WARN(PR 上留言一次)。
- R51c(三項待裁之三 · VRN 四冊代號 regex):裁定保留各冊範疇,不合併。
  - `VIA_TickerRegex_Scope_SSOT_v0100`:三範疇 STOCK4_LOCKED(中央 LOCKED)· INSTRUMENT_ALL(規則冊 corrected)· STOCK_TEXT_EXTRACT(TickerRegexSSOT + 寬鬆式),每範疇對 9 探針宣告收 / 拒;式的正本仍在各冊,本冊不改式。
  - `CGC_MDL185_SsotBookSync_v0101`:E4 逐冊對自己範疇預期;偏離 = SCOPE_DRIFT(黃)· 未宣告冊 = UNSCOPED(黃)· 範疇冊缺 = 退回 v0100 原判(不假綠)。自測 10/10 + 前版 24/24。
  - ssot panorama 前後:正則@VCGC YELLOW(DISAGREE:0050 / 00878 / 00981A)→ 綠(AGREE)。已知限制:年份四碼(2026)fullmatch 層各冊都收,靠上下文,不在本冊改。
  - 需求冊 v0140(VCGC-REQ110 引述 + 證據)· 盤點冊 v0125(+C-ticker_regex_scope)· 交接案 ticker_regex_scope 過。
- R52(操作員:「從vcgc進vdf … 2023-06-01~最新 所有資料啟動」「一個ps指令加入加速器先 … 補齊台股清單及主動式台股etf清單 再全部同步啟用」「全景式掃描 … 工作前製作葉子指令ps擋」):
  - 容器經 VCGC 實跑 CGC_MDL134 plan(18 步 · H1–H5 OK)→ run 15 步(VIA_HIST_SINCE=2023-06-01;pip 鏈 · vap_node 是裝件,AI 不跑)。終態 PART · OK 3 · FAIL 10 · SKIP 2 · 3156s:
    資料家是工作站 Windows 路徑 → datahome SKIP、hist_probe / hist_2023 / group_class / global / consensus / revenue_consensus 庫缺;TWSE 擋容器 IP → etf_universe / etf_history;
    revenue_backfill 真的上 MOPS 抓到 59 段、逾時 2400s 停在 56%(**MDL134 對 net 步在子行程設同意閘 = 起跑即同意,既有設計**;我先前說「容器網路步會 GATED」是錯的,已更正);
    refail 重跑 33 站 OK 14;etf_fetch · etf_revenue · digest OK。資料只落容器暫存庫(不提交)。容器副作用檔全部 git checkout 還原。
  - `Invoke-VIA-VdfFetch-v0108.ps1`(薄尾):① 依 VDF_ENG087 refresh --plan 順序經 VCGC 補兩張清單 → ② 原參數交 v0107 全部步並行;七個 ① 指令在容器經 VCGC 逐一驗 argv。
  - `Invoke-VIA-QuickScan-v0100.ps1`(葉子指令,唯讀):閘 · CGC_MDL230 覆蓋矩陣 · AST 全景 · test --quick · ENV MANAGER · 八路衝突 → 總表 + 自動開頁。
    容器實測:覆蓋 GREEN(PS 加速器橋 708/708 · 模板章 188/188);AST 0 SYNTAX/COMPILE,ACCEL 32 件全在豁免 / 正本(HTML_UI 22 · ENG112 · 加速器本身 · intake 8);
    動詞 46/46 · case 52/52 · workflow 49/49 · compile 錯 0 · 紅 0;ENV / 八路是容器環境(無 pwsh · 家族境未建),工作站照葉子指令量。
  - 需求冊 v0141(VDF-REQ014 · VCGC-REQ092 引述 + 證據)。
