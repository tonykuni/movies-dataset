# Veritas Intelligence Analytics(VIA)

台股/全球市場情報平台:資料鍛造(VDF)× 自動繪圖(VAP)× 研報擷取(VRN),
以 SSOT 單一真相與 hash 鎖定治理貫穿。**2026-08-05 全綠穩態版(Mega 10 域 1208 檔 GREEN)。**

---

## 快速開始

```powershell
# 第一次(或新機器):一鍵布建(冪等、免管理員)
pwsh -File "VeritasIntelligenceAnalytics\Install-VIA.ps1"     # 加 -AutoStart 可開機自啟
```

之後任何終端機、任何目錄:

| 指令 | 作用 |
|---|---|
| `via` | 同步 + VDF 進料 + VAP 繪圖 + 自動開 UI(日常預設) |
| `via-one` | **全系統總啟動器 v0110**:十四階段一支到底(DEPS 預檢+sync+Mega+VMT+CGE+VRN×2+FLOW+IF+FIS+**WORKOPS+FORGE+BRIDGE**+Hub 活化,引擎全動態最新版)或 `-Only <鍵>` 選子系統看 U/I |
| `via-all` | 互動全套:VDF + VAP + VRN 預檢 + Control Tower(不含長跑稽核,不卡斷) |
| `via-audit` | 長跑稽核三件套:TurboOptimizer SafeAudit + Panorama + Polyglot(預期數分鐘以上) |
| `via-tower` | 治理總控台 `http://127.0.0.1:8765`(桌面捷徑同此) |
| `via-shim` | TickerRegex v0100 墊片入口:`via-shim -Target <檔> [-DryRun]` |
| `via-sync` | repo 同步(fetch + merge claude 分支 + push main) |
| `via-batch` | **VRN 批次**:incoming 全部 PDF 過 No-OCR 生產線(並行池、可續跑;`-Fresh` 全部重跑) |
| `via-import` | manifest 匯入:Downloads 批次去重入庫(清單由 Claude 寫進 `import_manifests/`) |
| `via-vmt` | VMT SuperBOM 總指揮 v0103(Porcelain 刊頭;問卷→附件→收斂→CPM,缺件優雅略過) |
| `via-vmt-init` | VMT 資料層 bootstrap:OneShot 對準 VMT 根建 DB/SSOT 種子 + 跑郵件器 + Command Center |
| `via-mega` | 公定處理模式 v0108:三輪全景 **14 域**(+巢狀 git repo 圍堵)(+WORKOPS/FORGE/STORAGE)x 20 加速器 x Matrix;參數置頂可增減(`--set k=v`)、附掛掃描根、parquet 增量 store(DuckDB)、rich 摘要矩陣;hydra 僅平台域+慣例檔名白名單;SSOT 9 項 |
| `via-code` | 自動識別編號器:`via-code <類別> <元件> [suffix]`(冪等給號;`--list`;`--register`) |
| `via-gov` | 中央治理引擎 CGE v0401:TAB 多頁儀表板+台股登記簿 1977 檔(dry-run 預設;`--commit`;`--fetch-tw`) |
| `via-vdf` | VDF 一鍵側欄工作台(v0160C 一般瀏覽器 HTML U/I + 本機 HTTP 橋;SHA256+AST 閘門;回退 v0102/v0101) |
| `via-flow` | FlowSystem OneShot v0101:五鏡頭 FIS+fusion+五 QA 閘+自產 **Porcelain** UI(漲跌色功能語意保留;run-local) |
| `via-if` | VIA-IF 產業預測整合引擎:唯讀掃描+append-only 輸出(`--selftest` 自檢) |
| `via-fis` | FIS 驗證 harness v3:E1/E2/E3 實驗+Matrix 報告(需 `py -m pip install scipy`) |
| `via-pipe` | 統一輪動引擎(回測+自演化+證偽;**待同伴檔 rotation_engine.py 補齊**) |
| `via-envfix` | EnvManager 決策式無衝突安裝:五依賴 plan-install 留痕 → NumPy 黃金律 constraints → py 基底聯合安裝 → pip check 後驗 |
| `via-envgov` | **環境治理統一引擎 MDL135(批381)**:全景式分析 base/via_core/via_* → uv 毫秒快篩 → base 該有冊閉包(Baseline 冊)→ 衝突立拔家族路由(OCR→`paddle_312` 等)→ Zero-Hydra 分流拓撲三輪 → LKGC/rollback(最壞還原原本規劃)→ 四分區 HTML Matrix;預設唯讀 `run --offline`;`apply --approve`(base 移除另 `--approve-remove`);`via-envgov-auto` 單一 PowerShell 一貼即用(`-Online`/`-Approve`/`-Background` 不阻塞);批385 `conflicts [--env X]` 衝突明細+修法、未知旗標誠實停 |
| `via-entry` | **單一入口 MDL136(批383)**:母倉 Register 點源=唯一入口;燈板 GitHub/Mother/Data/Env/PATH/EnvGov/VDF-DB/VAP/Matrix/Console/Grok(零網路)→ `via-entry plan` 一貼即用 11 步 → `via-entry roster` 短令冊(母倉∪Grok 撞名冊:母倉先發先得,Grok 同名 `-grok`);`--scan`/`--open`(總控矩陣 v0700)/`--console`;載入 Register 即接回 Grok `VIA-CmdMatrix`(去尾段自動執行);`via-env`→`via-envgov` 正本;`via-grok matrix` WPF 右側板;`via-envpy <family>` 家族境 python |
| `via-webconsole` | Grok 網頁主控台子入口(收容包 b383;TanStack/Vite;`npm run dev` 8080):`node_modules` 缺=`--install` 觸網同意閘;`--background` 另窗最小化;LIVE 預設關 `VIA_NET=0`;KEY 不入檔 |
| `via-vdfdb` | **本機三庫整併入正典 DuckDB ENG079(批383)**:`C:\新增資料夾\新增資料夾\VIA_db_part1_prices/part2_chips/part3_rest` → `scan` 唯讀盤點(parquet/csv/duckdb/sqlite;欄位別名偵測;路由 px→`tw_daily_prices`(ENG064 鍵;裸碼經 `tw_listings` 對映 yahoo)/chip→`tw_chips_daily`/rest→`tw_rest_daily`)→ `run --apply` COPY_ONLY anti-join 只補缺鍵(既有零觸碰;檔指紋台帳已入冊跳過)→ `ckpt`(ENG064 `--rebuild-ckpt`=抓過不再抓)→ `need --start 2023-01-01` 月粒度缺口 → `coverage`;以 `via_vdf_312` python 啟動;**批389** ENG065 協定檔 `tw__X`/`gl__X` 直入同名正典表(零改名;`date`+`ticker` 鍵 anti-join 否則 EXCEPT;台帳鍵含目標表=改路由自動重做,舊 `local_rest__*` 只增不減留存)+資料家接點燈(非 LINKED=YELLOW → `via-datahome link` 後冪等重跑) |
| `via-vapone` | VAP ONE 單檔整合引擎 VAP_ENG016(批383 vap 補充):圖規 SSOT 40/圖規鎖/批330 資料律/K 線 75/25/零依賴 SVG+Plotly+Matplotlib 車道;無參數=`--selftest` 72 檢;`--axis`/`--list-charts`/`--demo`/`--render`/`--lanes`;以 `via_vap_312` python 啟動=全車道 |
| `via-rungate` | **VDF/VRN/VAP 能跑閘 MDL137(批384)**:「能跑」=家族境 python(`via_vdf_312`/`via_vrn_312`/`via_vap_312`;MDL136 解析)逐庫 import + SelftestGrid 家族站真跑(`--fast` 每族 3 站/預設 8/`--all`;`--family vdf,vrn,vap`);RED=引擎 FAIL、YELLOW=base 退路或必要庫缺;`status` 看上次;鏈路燈(DeckServer v0129 任務冊家族路由=ParallelLanes/CompletionAutomator/MasterControl 同律) |
| `via-py` | 家族境 python 通用啟動器(批384):`via-py vdf "functional modules\VDF\engine\VDF_ENG064_HistoryBackfill_v0108.py" --status`;境缺=base 退路印黃 |
| `via-vrn4` | **研報一題四點文摘 VRN_ENG080(批386)**:標題+K1 潛在上漲空間(目標價 報告正文>VRN_SSOT 多值不平均;最新 adj close;**報告日在除權息前=目標價後向因子鏈同口徑調整**;另存批240 報告時上漲)+K2 稀釋 EPS n～n+3 YoY 主要原因+K3/K4 首頁其餘對半+K5 風險可空;quote-or-abstain、novel numbers QC;`run [--ticker X]`/`show <ticker>`;落 `vrn_four_point_digest` 與 `VIA_Reports/vrn/four_point/DIGEST_latest.html` |
| `via-famui` | **家族 U/I 再生閘 MDL138(批388)**:`via-famui vdf\|vrn\|vap\|all [--open]`,以家族境 python 真跑頁面產生器(vdf:資料架構矩陣+系統總台;vrn:控制塔+每日觀察+一題四點;vap:儀表板×2)+靜態頁,判準=rc0+頁新鮮+零 CDN;索引 `VIA_Reports/ui/FAMILY_UI_latest.html`;`via-vdfui`/`via-vrnui` 別名;`via-open VDF` / `via-open VRN` / `via-open 四點` / `via-open 家族` |
| `via-console` | **輸入主控台 MDL139(批390)**:左面板輸入(VDF 台股代碼冊 TWSE/TPEX 可新增、總體經濟 13 類勾選=FRED `--only` 展開、財報當季/累計/年度年起迄(三大報表 PLANNED 誠實)、逐項起始日「最新」勾/個別可改、天數、車道;VRN 報告夾/Windows 選夾/拖曳→樞紐 `/intake` → 整條鏈啟動;VAP 格式/風格/輸出夾)+右面板矩陣(庫狀況/日交易×籌碼對齊/台股清單/宏觀序列/VRN 跑況 BASIC INFO·SUMMARY·FINANCIAL DATA VERIFIED\|FAIL/VAP 產出/項目冊/執行狀態;篩選、點欄排序預設大到小、全選/全不選);`via-console`=建頁 · `status` · `set k=v` · `argv --item` · `run --item`;`via-console --open`=樞紐在線即以瀏覽器 exe 開 LIVE `http://127.0.0.1:8765/console`(可按啟動),離線開快照頁(只看並印等價短令;`start http://…` 會被零跳出律抑制,請走 `via-open LIVE`);零 CDN;**v2(批392)**:參數最小化——`▶ 啟動全部 VDF` 一鍵跑冊內全部可跑項(台股除財報/月營收外不選股票=抓全部)、統一起始 `2023-01-01`(整類起始遮罩 `YYYY-MM-DD` 淺色提示、只填數字、「-」不動;整類「最新」勾=不帶旗標)、國際資訊冊 INTL_DAILY/INTL_FIN 右面板勾選增減(鏡寫活冊、軟移除)、VRN 拖曳/選夾上傳即自動啟動整條鏈、TAB2 BASIC INFO(VERIFIED\|FAIL)/TAB3 SUMMARY/TAB4 FINANCIAL 核對律(報告值≠VDF 歷史值 → VDF 為主;單位差標)、VAP 規格細節與圖片(樞紐 `/vap_img`)、「跑成功?」三族最近真跑 |
| `via-align` | **台股日交易×籌碼數量對齊 VDF_ENG081(批390)**:`check [--days N]` 逐日核對 `tw_daily_prices` 票數 vs 籌碼(`tw_chip_inst`∪`tw_chip_margin`;code+market→`tw_listings.yf_ticker`)ALIGNED/PARTIAL/MISALIGNED+差集清單;`update --apply` 最新日 價∪籌碼 ∩ 冊 → `tw_universe`(anti-join 只增)+ `mega/tw_universe_<ts>.parquet` 增量;`status`;籌碼落後價表=誠實指路 `via-chip run`;讓庫律(批391):撞日更鏈單寫者鎖=短等重試,逾額誠實 `[FAIL] 庫忙` rc3;以 `via_vdf_312` python 啟動;**基準日律(批393)**:`update` 預設以最新「雙側齊日」(價表票數 ≥ 窗內最大 60%、籌碼有票、ALIGNED/PARTIAL)為清單基準,最新價日殘缺(實錄:只 399 票、籌碼 0)=誠實 YELLOW 改基準並印修法;`--asof YYYY-MM-DD` 指定、`--allow-latest` 強制;`check` 標「價未齊」日;`status` 標殘缺快照與現役 `current_asof`;撞鎖時印持鎖者 PID/引擎並指路 `via-bg` |
| `via-bg` | **背景引擎進程唯讀一覽(批393)**:`Get-CimInstance Win32_Process` 篩 python/pwsh 命令列含 VIA 引擎/boot 鏈/樞紐 → PID、已跑分鐘、引擎+動詞;誰持 DuckDB 單寫者鎖一看便知(多為 ENG064 回補或 boot 日更鏈);絕不 `Stop-Process`,等其跑完再 `via-align`;實錄:`[FAIL] 庫忙` 曾指路 `via-status`,但那是同步頁不是進程表 |
| `via-chip` | **籌碼增量 VDF_ENG056(批394 登錄)**:`run [--days N]`(三大法人+融資融券 雙所逐日;交易日曆=價表實際日期;checkpoint 日×車道;節流 1.2s)· `--derive`(券資比等衍生欄)· `--status`;以 `via_vdf_312` python 啟動、同意閘自動 YES;實錄:籌碼止 08-25 因日更鏈 ③ 跑時價表尚無其後交易日(ENG064 回補在後才補齊),重跑即補;**v0102(批395)**:checkpoint 自庫重建(庫內已有 (date,market) 的日×車道不重抓;實錄待抓 1800 → 只剩真缺)、`--workers N`(預設 4;SuperAccel `accel_map` 每工保留 1.2s 節流;一塊傳輸敗過半=自癒減工)、動態進度條+數字(`[####----] 37.5% 675/1800 · OK · 空 · 敗 · 至日 · 速率 · ETA`;`VIA_Reports/vdf/chips/PROGRESS.json`)、Ctrl+C=先落緩衝列+checkpoint 再停(rc130 零 traceback;重跑續補) |
| `via-price` | **價格增量 VDF_ENG054(批394 登錄;別名 `via-tw-backfill`;批401 +被動 ETF 補源)**:`run [--limit N] [--full]`(增量律:依各標的 MAX(date) 只抓缺口,重疊 3 日 upsert 冪等;價未齊日重跑即補;清單=雙所公司+TWSE ETF 冊四碼被動碼如 0050,五碼+A 主動 ETF 留 `via-etfuniv` 專責)· `--status`;撞單寫者鎖=引擎庫鎖律誠實停(checkpoint 已留) |
| `via-etfuniv` / `via-etfhist` | **主動式台股 ETF 宇宙與每日持股(VDF_ENG077／ENG078;批374/375;批406–409 v0104)**:`via-etfuniv` 自 TWSE `t187ap47_L` ETF 冊抓五碼+A 主動碼 → `active_tw_etf_registry`(國內成分=須每日揭露)+ SSOT `ActiveTWETF_Latest.csv`;`via-etfhist` 算 IPO 以來逐交易日覆蓋帳並回補。**批406 通路修**:車道冊原 16 條投信歷史道全 `PENDING_SOURCE` 且 url 空、唯一 VERIFIED 的 MONEYDJ 只給今日 → 回補恆 `tried 0`。新增 `discover [--apply]`(自 TWSE OpenAPI **規格檔**真列舉資料集,關鍵字篩候選寫回車道冊為 `CANDIDATE`;規格取不到=誠實 `UNREACHABLE` 列已試路徑,**不臆造端點**)、`probe [--ticker] [--date] [--apply]`(對有 url 的非 VERIFIED 車道取一次並跑持股解析,**解析出 ≥5 列真持股才 PASS**;`--apply` 只升通過者、不刪不動他條)、`parse_holdings`(JSON 欄名對映 + HTML 表雙道;不合判準回空不硬填)、DATED 車道真回補(落 ENG051 正本 `holdings_daily`,欄名依現表 `DESCRIBE` 對映、**不建表不改結構**,anti-join 冪等)。**批406c 收緊**:首跑 probe 把 4 個「董監事/大股東/外資持股」資料集誤升 VERIFIED(其一 27,528 列)——判準「≥5 列+四碼代號+數字」太鬆。三道收緊=列數上限 600、負面詞否決(董事/監察人/內部人/大股東/外資/持股比率/轉讓…)、代號相關性(該 ETF 代號須現身或全部四碼代號皆非本 ETF 自身);`probe --apply` 加撤銷道(既有 VERIFIED 重驗不過即降回 CANDIDATE 並記因由)。工作站重跑實測 `PASS 0 · 撤銷 4`。**定論**:TWSE openapi 目錄 12 個資料集全屬內部人/外資/大股東持股,**無**主動 ETF 每日成分,須改走投信 PCF 頁。**批407 三道升級取用**:`fetch_escalating` 依車道 `fetch` 欄起始,`http`(`SUP_MDL740.http_json/http_text`)→ `headers`(`curl_json/http_bytes` 帶瀏覽器式標頭,治多數 UA 型 403,免瀏覽器)→ `scrape`(倉內 Playwright 雙引擎 `PlaywrightBackend`,優先取攔截到的 XHR `network_json` 再退 HTML);得手模式寫回車道冊。爬蟲道前置 `SUP_MDL740.check_url` 必須 `ALLOW` 才啟動,否則印因由與應設之 `VIA_SCRAPE_CONSENT=I_ACCEPT_RESPONSIBLE_SCRAPING`——**絕不代設同意閘**。**批408 爬蟲道可達性修**:`gate2_diagnosis()` 三態——閘二未設/已設但非期望值(短令預設的 `YES`)/已是期望 token;DENY 訊息把差別講白且**不外洩原值**(先前只回「法遵 finding 阻擋」,看不出差在哪)。**批409 真通路(操作員令「你決定 請完成VRN VDF」)**:主動 ETF 持股從「沒有可呼叫的歷史車道」變成「有一條實測驗真的 DATED 車道」。端點由我親自查實(非臆造):`POST https://www.capitalfund.com.tw/CFWeb/api/etf/buyback`,body `{"fundId":"<投信基金編號>","date":"YYYY-MM-DD"}`;基金編號≠股票代號,先 `POST /CFWeb/api/etf/list` 取 `stockNo`→`fundNo` 對照(00982A=399、00992A=500、00997A=502)。實測 `date=2026-09-01` 回 40 列且 `pcf.date1` 隨之改、週六回 `data=null`(誠實無資料)=**真 DATED**。車道 schema 加 `method`/`body`/`pick`/`date_path`/`id_api`;新 `fetch_lane` 單一入口(解編號→渲染→三道取用→pick→解析→**日期硬閘**:點名了哪一日回來就必須是那一日,不符即拒寫,避免今日持股冒充歷史),`probe` 與 `backfill` 共用同一條路;`parse_holdings` 加 `by_id` 相關性(以本檔代號查出的基金編號點名索取=相關性由建構保證;列數上限與反指標否決**不放寬**);`probe` 拿別家代號探到「該投信不發此檔」標 **N/A**、不算 PASS 也**不撤銷**。新動詞 `sync [--apply]`(加法式併入車道冊:新增/補鍵/只升不降/未驗 url 才汰換且舊值留 note/冪等)——車道冊是執行期會被 `--apply` 改寫的檔,工作站那份早與倉內分岔,新設定放程式碼裡再併入,`git pull` 不會撞本機修改。**誠實覆蓋**:23 檔須每日揭露中本批只通群益 3 檔,其餘 13 檔仍缺源。二十六檢 26/26(全注入式假 net,零外呼)+ 真實回應重放端到端驗證。 |
| `via-gates` | **法遵雙閘態一覽(批408;唯讀)**:印閘一 `VIA_NET_CONSENT`(`http`/`headers` 兩道只需此閘)與閘二 `VIA_SCRAPE_CONSENT`(`scrape` 道另需)的狀態,**只報是否等於包內法遵期望的 `I_ACCEPT_RESPONSIBLE_SCRAPING`,絕不印原值**,並附上要自行開啟時該親打的那一行。**登場因由**:`via-fred`/`via-revfill`/`via-etfhist`/`via-etfuniv`/`via-chip`/`via-price` 自 批360/368/374/375/394 起每次呼叫都**覆寫**兩閘為 `YES`,而閘二的包內法遵 `def_validate_consent` 逐字只認 `I_ACCEPT_RESPONSIBLE_SCRAPING` → `gate_state()` 顯示 `open=True` 卻仍 DENY,且操作員自設的正確 token 每呼必被蓋掉=**批407 掛上的爬蟲道其實永遠不可達**。Register v0165 改以 `Set-VIAGateDefaults`(只在該閘**未設**時補預設值,已設者尊重;六令既有行為零變更)取代六處覆寫。**本系統永不代操作員設任何同意閘。** |
| `via-rebuild` | **多環境隔離重建計畫引擎 CGC_MDL050(批396 登錄)**:`via-envgov` digest「下一指令」指路的 `via-rebuild --env <境>`(旁建零破壞:原境不動、驗綠後切換候裁);無參數=`--offline` 唯讀計畫(零網路);`--split <境>` 為 MDL135 提案、MDL050 尾版尚無 → 改以 `--env <境> --offline` 唯讀並印明;`--selftest` 十四檢 |
| `via-pin` | **雙副本律(批397)**:工作站常有兩份副本(Github 母副本在 `main`、b381 副本在 PR 分支);新視窗由 `$PROFILE` 點源的那一份決定短令冊版本,`via-reload` 分支感知只拉該副本所在分支,PR 未併=母副本永遠拉不到新批。`via-pin`=把 profile 的 VIA 點源行換成「本窗副本」,以後新視窗預設載本副本尾版;`--show` 只看(兩副本各印分支/HEAD);只改 profile 一行,兩副本檔案零觸碰;pwsh 與 Windows PowerShell 各自 `$PROFILE`,各 pin 一次 |
| `via-closeout` | **收尾閘 MDL141(批398)**:`via-closeout [vrn\|vap\|all] [--run] [--dir 夾] [--json]`;**VRN 驗證收尾**(別名 `via-vrnval`)=報告夾(`input_reports` ∪ `input/incoming`)每一份 收件→首頁(ENG072 sidecar)→入庫(ENG073)→財報頁(ENG074/metrics)→四點(ENG080)+ TAB2 BASIC INFO/TAB4 FINANCIAL 核對態(沿用 MDL139 正本判準)→ DONE\|FAIL\|PENDING;總判 無報告=YELLOW(候丟 PDF)· 有 FAIL=RED · 未跑完=YELLOW · 全 DONE=GREEN · 庫缺=GREY;次步直指該補的鏈段;**VAP 產出收尾**(別名 `via-vapval`)=規格冊計數+產出夾逐圖驗(SVG 繪圖元素與無外鏈、PNG 簽章與 IHDR、HTML 有圖且零 CDN、PDF 簽章)+VAP ONE 台帳末筆;`--run`=先經 MDL139 `run --item` 跑鏈再收尾(任一段 rc≠0 即停);落 `VIA_Reports/closeout/CLOSEOUT_latest.md`(接棒台 vrn/vap 類含收尾矩陣;`closeout` 燈)。**批403**:逐份併列三方對照欄(檔名×首頁×財報頁表格;AGREE/DIVERGE/UNIT_SCALE/ONLY_TABLE + ticker/date 態),總結 `[三方對照]` 行,DIVERGE=資訊級待人工核不降 verdict,未對照指路 `VRN_ENG074 --crosscheck`。 |
| `via-deadends` | **短令死路掃描器(批400;=`via-entry deadends`)**:掃引擎 docstring/`[FAIL]` 指路句/docs/README 內的 `via-*` 令,對照短令冊(Register 尾版函式∪Grok 12 令∪根梭 `.cmd`),未登錄=死路(批394 `via-chip`、批396 `via-rebuild` 同類);落 `VIA_Reports/entry/DEADENDS_latest.json`;`--json`/`--quiet`。批400 真倉實掃:158 個舊令、2,554 處(多為早期模組 docstring 的 `via-install`/`via-digest`/`via-deps`/`via-store`…,以及本表下方舊段落的 `via-shim`/`via-code`/`via-sync`…)——**本表以 Register 尾版實掃為準,未登錄者屬候登錄,勿當現役短令**;登錄工程候下批 |
| `via-handover` | **接棒狀態台 MDL140(批392)**:只讀母倉現役 `*_latest.json`(入口/環境/能跑閘/家族 U/I/主控台/對齊/清單/覆蓋/本機三庫/VRN/VAP/boot log)+ git 現況 + 缺口冊 → 15 類分門別類堆疊矩陣一頁 `VIA_UI_Handover_v0100.html`(零 CDN;頁內「複製 Markdown」)+ `VIA_Reports/handover/HANDOVER_latest.md`/`.json`;`via-handover`=建頁 · `status` · `md`(印 Markdown);`--open`=樞紐在線開 LIVE `http://127.0.0.1:8765/handover`,離線開快照頁;缺料誠實 UNKNOWN 不假綠;供下一日接棒 |
| `via-bridge` | **Command Bridge**:一鍵前後端對接——後端 B1-B5 探測(接線/SSOT/依賴/資料庫/UI)+ test/debug 三輪 + 多 TAB 前端,首頁=總覽+全系統狀態矩陣(每跑必重生=當下真相) |
| `via-trinity` | 功能三系整合模板:VIA 母刊頭 > 鍛 VDF/研 VRN/鑑 VAP 四 TAB(Porcelain;22 個 {{…}} 資料綁定槽) |
| `via-workops` | **WorkOps 指揮板**:一支到底=唯讀掃描+控管表自動對帳+兩頁指揮板(①專案指揮 ②追蹤哨,≥3 天未回主動跳出);`ui` 開靜態儀表板;`Scan\|Reconcile\|Draft\|FollowUp\|Templates\|All` 走引擎非互動面 |
| `via-forge` | **VIA_Forge 五引擎家族**(45/45 驗收):無參數開工作台 UI;`check` 跑驗收矩陣;`server` 啟本機服務(127.0.0.1) |
| `via-storage` | **Storage Optimizer AIO**:預覽制清理(雙引擎+GUI;`-Execute` 才刪;`-TestAll` 全鏈測試;`.veritas_protect` 禁區跳過) |
| `via-pack` | 子系統獨立打包:`via-pack <cge\|mega\|bridge\|audit\|flow\|if\|vmt\|tools>` — 產品號自動編號(PKG 序號×內容 SHA8,冪等)+ **單機綁定**(Install 綁主機指紋、Launch 驗證,不符 fail-closed)+ **每包自帶封面 U/I**(產品/綁定/manifest 矩陣/報告出口,Launch 自動開)+ 逐檔 SHA256 manifest + zip |
| `via-bridge-sweep` | **橋塊掃描/注入器 CGC_MDL124(批345;批402 v0103 +`--net-callers`)**:`[--accel] [--net] [--ps] [--root 夾] [--apply]`;預設 dry-run 只列 PLAN,`--apply` 才寫(py_compile 雙驗,壞檔 SKIP 原檔不動);`--net --net-callers` 只把 NET-BRIDGE 掛進「真向外擷取」檔(去註解/字串後仍直呼 urlopen/requests/httpx/urllib3/yfinance/aiohttp;本機 socket 探測不計;工具本體 SUP_MDL737/740、via_net_unified、via_aegis_netcore、VIA_NetSupport 與 vendored 件(相對匯入/`pip._vendor`/SPDX 標頭)永不掛=自掛即循環);批402 實掛:ACCEL 註冊夾 5 缺→100%、NET 擷取檔 supportive 18/VRN 5/VAP 14 缺→100%、VDF 3(批115 全導入令)→100%;報告 `VIA_Reports/bridge_sweep/SWEEP_*.json`。橋本身只增不減:塊內只算路徑、`_via_net()` 惰性載入,原檔直呼一行未改。 |
| `via-psrepair` | **PowerShell 指令語法多輪並行安全修正引擎(批253;批403 v0101 卡斷修;批404 v0102 洗版修)**:`-Selftest` 八檢(純字串驗子行程命令建構);無參數=R1 唯讀(Accel20 dry-run+PSScriptAnalyzer 橋,零寫);`-Fix`=R2a Accel20 GO_v1 修 + R2b `CGC_MDL101_PSAstRepair fix`(AST 逐檔、只增不減、失敗原檔不動)→ R3 PostRepairVerify+MDL101 再掃+`VIA.ps1` AST 沙盒解析;HTML 矩陣落 `VIA_Reports/`;沙盒無 pwsh 只能 HEURISTIC_ONLY,正式跑在工作站(pwsh 7)。**批403 卡斷修**:v0100 走 `pwsh -File` 傳陣列 → PowerShell `-File` 不支援陣列,9 個排除樣式被攤平、第 2 個起掉進 `-ThrottleLimit`(Int32)導致 R1/R2a `rc=1` 全滅;v0101 子行程改走 `-Command` + 雜湊表字面量 splatting(陣列真的是陣列、行程仍隔離),每輪加 `Invoke-VIAGuarded` 看門狗(逾時 `rc=124` 誠實印、`-TimeoutSec` 可調)與六段輪次進度條=不卡斷;收容原件零觸碰。PS 20 加速器=`VIA_PS_Accel_Module.ps1`(TOOL-101)`$VIA_ACCEL20` 01–20,`[VIA:PS-ACCEL]` 748/761 在冊 ps1(13 未掛=`VIA_Reports/env_governance/` 再生物);**批404 洗版修**:v0101 的看門狗每 0.8s 一次 `Write-Progress`,主機會重繪**所有**在線進度記錄,把子引擎自己印的真實輸出淹掉;v0102 改本檔 `Invoke-VIAWatched`(同款 `Start-Process`+逾時 `Kill` 整樹回 124,只每 `-HeartbeatSec` 預設 60 秒印一行純文字心跳),輪次改一行 `[輪次 n/6]`,加速器 #16/#17/#18 語意全保留。工作站實跑:R1 `rc=0`、R3a `rc=0`、R3b `rc=0`、R3c GREEN,18 分鐘零吊死;R1 誠實 RED=847 檔 976 findings(parallel-fixable 65),`-Fix` 待操作員下令。 |

## 系統架構

```
functional modules/
├── VDF/   資料鍛造:進料引擎(GREEN gate)、MDL001-006 擷取引擎、
│          registry/(擷取登錄 Schema/Full 238 項/覆蓋率/資料源矩陣 77 項)、六槽標準
├── VAP/   自動繪圖:engine v001(正本)+ chartlib_v002(UNIT03 晉升版)、
│          Workbench v009/v010、spec/(視覺鎖三層,見下)
└── VRN/   研報擷取:生產線 v1.1.0(MDL001-008,manifest hash 9/9)、
           TrustPolish v04.4、Incremental DB AIO、Finalize AIO、SSOT 鏈、六槽標準
supportive modules/
├── ssot/、registry/、audit_tools/       真相層(+同義字引擎/種子)、登錄層(+編號器)、稽核紀錄(永不改寫)
├── 70_VRN_Rules/                        規則模組(TickerFilename SSOT、墊片、券商別名…)
├── VIA_Canonical_Units/                 UNIT03 治理管線(v0109-v0113)+ 判定表 + 晉升記錄
├── VIA_Control_Tower/                   HTML 總控台 v005(Veritas 鎖定版式)
├── VIA_Governance_Runtime/              Mega 引擎 v0100-v0102、v0160A/B/C 工作台家族、installers(OneShot 等)
├── VMT_SuperBOM/                        VMT 引擎家族 + master engine v1.0/v0101/v0102 + BatchMailer + SuperBOM 財務模型
├── VIA_Central_Governance/              CGE 引擎家族 v0100-v0401(唯一正本家)+ TW 登記簿快照
├── specs/                               規格文件庫(宏觀 md 11 篇 + MI 附錄 + EarningsInsight)
├── VIA_FlowSystem/、VIA_Pipeline/、     FlowSystem+FIS 家族、pipeline/io/devils_advocate、
│   VIA_IF_Engine/、VIA_EngineForge/     VIA-IF 引擎、EngineForge 方法論+協調器(批次 G 歸位)
├── ui_support/                          UI 歸檔 base(Hub v0103 + Flow Console + 40+ 儀表板)
└── bin/ + Install-VIA.ps1(於 VIA 根)   20+ 指令 + 一鍵布建
```

## SSOT 總表(現役真相)

| 真相 | 檔案 | 版本 |
|---|---|---|
| 股號規則 | `supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json` | v0100 ACTIVE:四碼首碼非零;2021–2030 交消歧層,**年份排除不得寫入 regex** |
| 消歧實作 | `supportive modules/70_VRN_Rules/VIS_VRN_TickerFilenameSSOT_v0100.py` | 首頁股號 0.97 / 官方清單 0.9 / 日期線索→YEAR / 無佐證→AMBIGUOUS 人工覆核 |
| VAP 繪圖規範 | `functional modules/VAP/spec/ssot/vap_spec.json` | v1.0.0(線粗 1、line 0.9、區域 0.75、柱 0.6/0.8、via 色票鎖定) |
| VAP 圖庫 | `functional modules/VAP/spec/ssot/vap_chartlib.json` | v1.0.1(28 型 VAP-CH-01…28) |
| 視覺判定表 | `supportive modules/VIA_Canonical_Units/VAP_VisualLock_Adjudication_Table_v002.json` | v002 分項閘(方案 A);Seaborn 0.80 為獨立域 |
| Header 鎖 | `functional modules/VAP/spec/Veritas_Header_Masthead_1d.html` | 1d LOCKED(幾何/色票/字體不得覆寫) |
| VRN 資料契約 | `functional modules/VRN/registry/VRN_REPORT_*_SSOT_v0100.json` | v0100(parquet 正本 + DuckDB 鏡像) |
| VRN 生產線 | `functional modules/VRN/registry/VRN_Production_Manifest.json` | v1.1.0(核心模組 SHA256 錨定) |
| 設計鎖 tokens | `supportive modules/ssot/VIA_DesignLock_SSOT_v0102.json` | v0102 ACTIVE(視覺鎖源=VAP_Workbench_v009:暖紙底+墨印+六彩 accent;Porcelain v0101 降前代保留;回退=改引 v0101) |
| 公定處理模式 | `supportive modules/ssot/VIA_MegaPrompt_OfficialMode_v0100.md` | v0100(三輪硬性上限、20 加速器、沙盒循環;執行載體 `via-mega`) |
| AI 撰寫規範 | `supportive modules/ssot/VIA_AICodegen_Prompt_SSOT_v0103.md` | v0103(地板 one v0107/vmt v0103/Hub Live;**動態解析鐵律**嚴禁寫死版號;ENG/PKG 取號義務) |
| 欄位 regex 庫 | `functional modules/VRN/InvestmentRegexPattern_VALIDATED.py` | v3.0 ACTIVE(525 patterns;PROMOTION_RECORD 錨定 SHA256) |
| 同義字引擎 | `supportive modules/ssot/via_synonym_engine_v0100.py` + Seed | v0100 ACTIVE(41 canonical 錨點;同義字增量只增不減) |
| 編碼註冊中心 | `supportive modules/registry/VIA_AutoCode_Registry_v0100.json` | v0100(八架構類別+泛用狀態;六共存域不侵入;`via-code`) |
| regex/同義字普查 | `supportive modules/ssot/VIA_RegexSynonym_Census_v0100.json` | v0100(四族無遺漏;兩遺漏已晉升) |

## 治理原則(不可違背)

1. **只增不減**:SSOT 修改必升版 + changelog;稽核紀錄(audit_tools)永不改寫。
2. **正本不就地修改**:runtime 墊片(`via-shim`)或版本前進(new file);被取代版本進 `_superseded/` 隔離,不刪除。
3. **hash 鎖定交易**:任何晉升附 SHA256 前後對照與 PROMOTION_RECORD。
4. **fail-closed**:替換次數不符、hash 漂移、原因不唯一 → 一律中止不寫檔。
5. **巨檔紅線**:>45MB 永不入 git(.gitignore 已鎖 iconforge 與 v141D6 七檔);產出物(db/output/temp)不入庫。
6. **九頭龍防治**:同名檔以 SHA256 判 REDUNDANT_COPY(去重)或 VERSION_CONFLICT(裁決),不放任並存。

## 日常工作流

- **研報進料**:PDF 丟 `functional modules/VRN/input/incoming/` → Tower 按 intake → probe → lanes → run。
- **舊模組用新股號規則**:`via-shim -Target "functional modules\VRN\VRN_MDL001_StockReportPipeline.py"`(先 `-DryRun` 看報告)。
- **收尾/稽核**:Tower「收尾流程」FLOW A–F(唯讀提案型)與 20 加速器。
- **凍結債務**:106 個舊 regex 檔案見 `audit_tools/TickerRegex_LegacyDebt_Census_v0100.json`(16 墊片候選/53 稽核紀錄/8 已隔離/29 待自然升版)。

## 疑難排解

| 症狀 | 處置 |
|---|---|
| push 被拒 non-fast-forward | `via-sync`(內建 fetch+merge+push;必要時 `git pull --rebase --autostash origin main`) |
| pull 被本機修改擋住 | `git stash push -- <檔>` → pull → push → `git stash pop` |
| 貼上長腳本被截斷 | 不要貼長腳本——一律用 repo 內腳本 + `pwsh -File`(本平台鐵律) |
| ps1 疑似語法錯 | `[System.Management.Automation.Language.Parser]::ParseFile()` 做正式 AST 驗證 |
| 範疇已凍結項目 | 見 `audit_tools/VIA_ScopeFreeze_Closure_v0100.json`;重開需操作員點名 |

---
*營運手冊 2026-08-06 · 對應 Tower v005 / Mega v0106 / VMT v0103 / VDF 工作台 v0160C / UI Hub Live(活化樞紐)+ 靜態 v0108 回退 / TickerRegex v0100 / VRN v1.1.0 / 判定表 v002*
