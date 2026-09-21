# Register-VIA-Commands-v0237.ps1 — 批672(操作員令「以後跑完都要生成矩陣式報告 BY RICH,字小,優化矩陣排版規格」;L70 逐次許可沿用本令):+via-matrixspec(別名 矩陣規格;CGC_MDL173)。為什麼要有這一支:批669–671 之間我一口氣做了四支會落頁的引擎(MDL169 六域 · MDL170 VDF 鏈 · MDL171 全景計畫 · MDL172 VRN 鏈),**四支各自帶一份 css=("body{...")**。四份幾乎一樣但不是同一份:字級 13/12.5/13 各有各的,深淺配色只有一支有,手機寬度只有一支顧到。「排版規格」如果活在四個地方,它就不是規格,是四個人各自的習慣(L30)——操作員說「字小」的那一刻,要改的地方有四個。所以這一批把規格收成一份:矩陣 10.5px(原 12.5–13px)、rich padding (0,1)、box=SIMPLE_HEAD、Console width 200(寧可橫捲也不讓欄位換行,換行的矩陣對不齊)、數字 tabular-nums、深淺兩套但**不給切換鈕**(零彈窗律)、手機只有矩陣橫捲、三顆鍵(MD/JSON/複製)全內嵌零外連,MD 由引擎產一份給頁、**JS 永不自己拼第二份**。四支引擎同時升版接上:MDL169 v0104 · MDL170 v0101 · MDL171 v0101 · MDL172 v0101。其餘沿用 v0236。
# Register-VIA-Commands-v0220.ps1 — 批574:+via-govaudit(別名 制度稽核;CGC_MDL164:操作員 14 庫 + 3 自適應機制藍圖逐條判——冊在/有料/**有活讀者**三件缺一不可;零活讀者=ORPHAN 孤兒冊;另報單一讀者與多冊並存)。CGC_MDL160 v0101 +Veritas Header 契約(第四級 TARGET:已立契約尚未施工,**永不判燈**;via-uiunify header 印正典規格)。其餘沿用 v0219。
# Register-VIA-Commands-v0219.ps1 — 批573:+via-mastercard(別名 母檔卡;CGC_MDL163:母檔 310 KB / 約 87,932 token → 卡 約 1,761 token,省 98%;卡是**索引不是母檔**,零網路零 DB 只讀倉內 SSOT=任何機器跑出來都一樣;export --publish 只寫卡、絕不寫母檔)。其餘沿用 v0218。
# Register-VIA-Commands-v0218.ps1 — 批571:**短令找不到時,冊自己講原因**。工作站實錄:操作員打 via-cmdcard / via-vdfcov 得到「無法辨識」,而同一個視窗 via-datahome 跑得動——因為那個視窗點的是**舊冊**。這種來回已經第三次(批564 兩次是真的沒登錄,這次是視窗沒重點),每次都要一趟往返才知道是哪一種。本版註冊 CommandNotFoundAction:凡是 via-* 找不到就當場分辨**①冊上有但本視窗沒點到(給重點指令)②冊上也沒有(那才是真漏登錄)**,並印出本視窗點的版本 vs 磁碟最新版本。其餘沿用 v0217。
# Register-VIA-Commands-v0217.ps1 — 批570:**撞號更正** via-peis 改指 CGC_MDL161(舊 MDL158 與既有 CGC_MDL158_VIAPanoramaAuditRepair 撞號,已退役)。+via-cmdcard(別名 指令卡;CGC_MDL162:一行一指令的卡+凍結冊,AI 讀卡不讀原始碼;freeze --apply 要帶 --evidence;verify 抓漂移)+via-vdfcov(別名 涵蓋閘;VDF_ENG090:兩張名單欄位齊不齊·月營收涵蓋·總經×akshare 對照)+via-uiunify(別名 畫面統一;CGC_MDL160:三級契約,不代改頁)。其餘沿用 v0216。
# Register-VIA-Commands-v0216.ps1 — 批569:+via-vdfinc(別名 增量閘;VDF_ENG089:庫裡已經有什麼→自 2023 起到最新**只列缺口**→--deep 逐日反連結;零網路零寫庫無 --apply)+via-vrnmatrix(別名 驗證矩陣;VRN_ENG083:代跑 ENG072→ENG073 後出**驗證過**的四態矩陣+零 CDN 頁)。via-peis 改走 ConvertTo-VIACleanArgs。工作站實錄 `via-peis scan --family vdf,vrn` → ABSENT「家族沒有可掃的起點:['vdf vrn']」——PowerShell 把 `vdf,vrn` 當陣列傳,轉行程參數時用空白相連。**冊裡早就有這一課**(ConvertTo-VIACleanArgs 的註解逐字寫著同一個坑),我寫 via-peis 時沒走它。兩邊都修:本檔走輔助函式;CGC_MDL158 v0101 也自己切 [,\s;]+。其餘沿用 v0215。
# Register-VIA-Commands-v0215.ps1 — 批568:+via-peis(別名 能力庫;CGC_MDL158 PEIS 能力引擎掛線口:搜尋→AST 全景→聚眾→低風險無損耗合併→完整測試→鎖定→能力抽象→快速截取 RUN(capability,params);正本收容零觸碰、以 subprocess 代跑;status|scan --family|cards|run|report;零網路·零安裝·不改來源·**不提供 --apply**(能力表落地是操作員的裁定))。其餘沿用 v0214。
# Register-VIA-Commands-v0214.ps1 — 批564:+via-consensus(別名 共識橋;VDF_ENG088 共識融合橋:正典 consensus_daily/latest 皆 0 列,而收容件引擎寫的是它自己的 consensus_current/history/long——兩邊從來沒接上過;status|plan|sync [--apply];零網路·不代設同意閘·來源缺不猜對映)。**這是補我自己的漏**:批563 立了 ENG088 卻沒跑功能註冊七處,操作員照我給的指令打 via-consensus 兩次都得到 not recognized。其餘沿用 v0213。
# Register-VIA-Commands-v0209.ps1 — 批534(接手 B533 實測修):via-central 身分字串改由解析到的控制面檔名推得(v0208 釘死 v0100)+ 新增 via-central dispatch(經 CGC157 固定路由一次跑完 VRN/VDF/QuantGuard,誠實四態 GREEN/YELLOW/RED)+ via-quantguard 支援 probe(polars/numpy/duckdb 在不在;缺=ABSENT 印 pip 令=你的手,不代裝);其餘沿用 v0208。
# Register-VIA-Commands-v0213.ps1 — 批544:+via-unified(統一主控頁:TAB1 給 AI · TAB2 內嵌三張頁 · 整頁轉 JSON/MD)。
# Register-VIA-Commands-v0212.ps1 — 批542:+via-pyprog(中央 py 啟動器六檢+耗時實測)。中央外套加速:首發 1137→280ms · 後續 279→37ms。
# Register-VIA-Commands-v0211.ps1 — 批541:+via-vrnrules(VRN 研報六欄規則正本樞紐 SUP_MDL749:status|drift|conflicts|harvest|selftest)。
# Register-VIA-Commands-v0208.ps1 — 批523:QuantGuard ENG086、SuperAccel、Celeritas/Aegis mounts 已註冊；舊技術指標生產接線移除；網路閘預設關閉。
# VIA command registry: central EngineBus / InputConsole / Workflow SSOT are the source of truth.
# Python engines must carry the standard ACCEL-BRIDGE and use the registered family environment.
# Historical command aliases are not retained in the active command book.
# QuantGuard commands: via-quantguard / 量化技術引擎 / 技術指標引擎 / 技術指標。
# Register-VIA-Commands-v0204.ps1 — 批515:+via-vdf-extra5(別名 五額外;VDF 五個額外資料試跑=匯流排 matrix --ids 月營收/三大報表/主動ETF持股/FRED宏觀/國際宇宙;觸網=你的手 $env:VIA_NET_CONSENT)+ via-vatetf(VETF 改名 VATETF;應用端:直接讀 VDF 擷取庫);其餘沿用 v0203。
# Register-VIA-Commands-v0203.ps1 — 批514:+中央治理家族六令 via-cgfamily/via-cgconsole/via-cgengine/via-cgrouter/via-cgdownward/via-samename(CGC_MDL150 擁有者;預設 dry-run;閘/權杖=你的手)+ via-iface -Need 陣列以逗號合回(實錄 need ['首頁 ocr'] 命中 0)+ Set-VIABoot 母殼帶 PYTHONHOME 誠實印黃(L32;根治=你的手);其餘沿用 v0202。
# Register-VIA-Commands-v0202.ps1 — 批513:+via-iface(MDL054 v0102 綁定合約層 sync/connect/graft/status;別名 合約);其餘沿用 v0201。
# Register-VIA-Commands-v0201.ps1 — 批511 併線:v0200(並行線 批508:via-rungate 預設 vdf,vrn 有界/via-ryg -Full/via-vcgc -Apply)+ via-envrecover(批508 律 L24 環境復原)+ via-panorama(並行線全景修復啟動器);其餘沿用。
# =====================================================================
# Register-VIA-Commands-v0200.ps1 — 批508:via-rungate 預設只驗 vdf,vrn；via-ryg 預設有界 selftest，-Full 才走 production 動詞；其餘沿用 v0199。
# Register-VIA-Commands-v0179.ps1 — VIA 短指令唯一定義處(批394 續章 操作員令「重新把我要在電腦跑的指令整合成一個 PS 指令含進入環境,一個指令跑完全部,把我還沒做的整合到這裡」→ +via-oneshot(Invoke-VIA-OneShot 尾版;九段:S1 解卡(委派 Unstick;本副本缺該件即自 origin 取單檔繞 bootstrap 死結)→ S2 點源尾版冊+via-pin → S3 進入 via_core 虛境(在位才進)+via-envgov 唯讀計畫 → S4 via-accel-import --apply --approve → S5 via-rungate --fast → S6 via-price/via-chip/via-align/via-fred(鑰在位才跑,只判在位不讀不印)→ S7 via-psrepair-ast+via-pstest → S8 via-selftest 207 站 → S9 via-productgate+via-projects+誠實三態總表;每段獨立計時與三態、任一段不擋後段、逾時 kill 不卡斷、邊跑邊吐進度與心跳、段 rc 回報(rc≠0 必紅=不假綠);-DryRun/-SkipAccel/-SkipData/-SkipMatrix;別名 一鍵)。本件三枚自犯錯皆真跑才現形並已修:Start-Job 是新工作階段故段內短令必 not recognized(改 job 內先點源尾版冊)、輸出緩衝到結束才吐=長跑段畫面全白(改邊跑邊收+心跳)、早期判定式抓不到 python 缺檔錯誤而 0.7s 回 OK=假綠(改 rc+缺件樣式+錯誤樣式三者合判)。批394 續章 操作員實錄(他不在電腦前要我代跑):副本卡「合併進行中+兩件連字號版號族 Register 衝突」,該副本拉齊醫生尾版僅 v0101(只認底線版號)→ 連字號族必判 MANUAL 而停=bootstrap 死結(要解倉庫才拿得到新醫生,而新醫生就在解不開的倉庫裡);更深一層:那輪 merge 起於舊 origin commit,解完後還要再 merge 當日新 commit,同兩件第二輪又衝突 → 解一次不夠,必須迴圈至 UP_TO_DATE。故 +via-unstick(Invoke-VIA-Unstick 尾版:醫生 >= v0102 即委派 sync --apply 零重造,否則走最小迴圈——台帳交醫生 ledger_union 聯集(append-only,絕不取單邊)、其餘衝突取遠端版(先發先得律)、完成合併後再拉,迴圈收斂;殘留 stash 衝突亦按律裁決;零 force 零刪除;-DryRun 只診斷;解完自動點源尾版冊)。雲端腳手架端到端真測 PASS:兩輪收斂、台帳聯集 4 筆、髒檔與未追蹤件零遺失、升版 v0174→v0177、點源後新令在位。批394 操作員令「啟動 PowerShell 指令語法多輪並行安全修正引擎(AST 雙模錨點+錯誤分流+並行安全修正+沙盒啟動驗證),test debug optimize test debug till they work」→ +via-psrepair-ast(CGC_MDL146:T1 AST Parser/T2 PSScriptAnalyzer(缺=SKIP 不代裝)/T3 Command-Param Inspector;F1 行尾註解截斷續行=Parallel-Fixable 真修(續接運算子上提本行末+註解搬續行末,token 零變更,此法即主線 PSRepair v0102→v0103 的真修法,pwsh 實測驗證「只搬註解」不足以解),R1 硬寫磁碟機代號/R2 Join-Path 空值=Report-Only 只列不改;修正一律 version-forward 且目標版號已存在即拒寫(Hydra 守衛),正本零觸碰零刪除零 force;尾版必綠、封存版壞=WARN 凍結不改;寫前沙盒解析+寫後複驗,任一不過即放棄該檔;收斂即停 VIA_AST_ROUNDS;預設唯讀,--apply 才修;別名 語法修)。雲端實測:尾版 ParseError 0 · 解析綠 158 · 封存版紅 4(全為已被 v0103 取代的 Invoke-VIA-PSRepair-v0102.ps1=凍結不改)=WARN 誠實態;批391 我方指令寫死版號之錯(給 v0175 而該副本只有 v0174=必然 not recognized)→ via-copies 產出指令一律尾版 glob、+--heal 明令自癒;批389 操作員令「test debug by yourself till it works perfectly」→ +via-pstest(MDL145 PowerShell 真測閘:AST 解析閘(尾版必綠/封存版壞=WARN)+真分叉自癒功能閘+具名參數回歸閘;pwsh 缺=SKIP);批387 工作站實錄:PS C:\Users\tonyk> via-vdffetch → not recognized,因 profile 載的是 Downloads\movies-dataset-b381 舊副本的短令冊 → +via-copies(MDL144 副本醫生:掃同機所有副本×Register 尾版×動詞在位×分歧/未合併,判誰最新並印立即可用與一勞永逸指令;全唯讀);批386 工作站實錄:merge --abort 後本地 main 與 origin/main 分叉→ via-reload 只會 --ff-only 永遠拉不動(Not possible to fast-forward)→ via-reload 分叉時自動委派 MDL143 拉齊醫生(merge --no-ff + 按律解衝突;零 force 零刪除);+via-medic 直呼;批385 工作站實錄:工作副本卡未完成合併(UU/AA)→ via-reload 只印「拉齊失敗」不指路、新短令永不到 → via-reload 偵測未合併態並印精準解法;+--resolve-theirs 明令解(衝突檔取 origin/<分支> 版+台帳聯集;零刪除零 force);批384 操作員令「將所有加速器依照 via_envmanager 規定導入 via_core via_ 相關環境」→ +via-accel-import(MDL142 加速器套件導入閘:Celeritas 88 件冊 × MDL135 路由 → via_core/via_vdf/via_vrn/via_vap;plan 唯讀,--apply --approve 才裝,base 零觸碰);批384 工作站實錄修:via-vdffetch 陣列潑灑 @a 把 "-Year" 當位置參數傳成年份值(畫面 [FAIL] -Year 需四位數年份,收到:-Year)→ 改雜湊潑灑 @p(具名參數);批383 操作員令「用一個 powershell 啟動 vdf 包含進入環境」→ via-vdffetch 改薄包裝委派 Invoke-VIA-VdfFetch-v*.ps1(唯一正本:自找根/自進環境/家族境 python 批384/同意閘不覆蓋 批408);批381→合流:+via-vdffetch [年份](預設 2023;單一指令:年份旗標→20 加速器→Hydra 哨兵→十一步資料鏈十道並行→存證;零跳出零互動不卡斷);批423 操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」:+via-allgreen(尾版律起 Invoke-VIA-AllGreen-v*.ps1;別名 統包)。工作站實錄 via-go 停在「── ① TEST(自測矩陣)──」不動=看起來死機,根因兩條皆在 AllGreen v0100:①`$out = & `$PY @Argv 2>&1 | Out-String` 把子行程輸出緩衝到結束才吐(200 站期間畫面全白)②`$StageTimeoutSec` 宣告了但**全檔從未使用**=任一站真卡住就永遠等。v0101 改 Start-Process+邊跑邊 tail、逾時 Kill 記 TIMEOUT、Write-Progress 進度列、開跑點 20 加速器名;格子 v0262 補動態進度條/SELFTEST_PROGRESS.json 心跳/Ctrl+C 安全落檔(rc=130)。via-go 是操作員自己 PATH 上的檔(批358 讓位律),短令冊不佔該名,改登錄 via-allgreen;批421 操作員令「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE MODULES TO SUPPORT VRN」:+via-gle(SUP_MDL743 GLE 全後端統轄橋;status|probe|route;別名 版面橋)+via-nlp(SUP_MDL744 NLP 應用系統統轄橋;status|roster|delta|demo;別名 語意橋)。GLE v2.1.0 上傳包對在庫 b245 逐檔比對 16/18 位元相同,installer 唯一差異是 ${ExitCode}: 改成 $ExitCode:(PowerShell 會把冒號誤讀成限定符=上傳版反而是回歸,不採),另一枚 dist whl 是原始碼建置產物=**不重複收容**,改把在庫收容件升格為全樹可用支援服務;NLP 確為新版,VIA_NLP_Application_System v1.8.0 68 檔入收容夾。兩橋修同一個真缺口:ENG072 v0106/ENG073 v0113 把 NLP 收容夾**寫死** VIA_NLP_OneEngine_v1.1.0(18 模組),v1.5.0/v1.8.0(39 模組,含 table_ops/layout_analysis/content_roles)收容了也永遠掛不上=尾版律破口;現由橋統一解析,橋缺席則原樣退回直掛=零回歸;批408 同意閘不覆蓋律:六個短令(via-fred/via-revfill/via-etfhist/via-etfuniv/via-chip/via-price)自 批360/368/374/375/394 起每次呼叫都寫死 $env:VIA_NET_CONSENT="YES";$env:VIA_SCRAPE_CONSENT="YES"——覆寫式;但閘二的包內法遵 def_validate_consent 只認 I_ACCEPT_RESPONSIBLE_SCRAPING,字串 "YES" 永遠 BLOCK,且因為每呼必覆寫,操作員就算自己設了正確 token 也會被短令蓋掉=爬蟲道永遠不可達(批407 掛上的 scrape 道等於死路);改法=Set-VIAGateDefaults:只在「該閘未設」時才補預設值,已設者一律尊重(不移除既有預設行為=既有六令零行為變更;亦不代操作員設任何新意圖);批400 八流程並進:via-entry 動詞白名單 +deadends(MDL136 短令死路掃描器)+ via-deadends 別名;收尾閘登錄樞紐任務 closeout(Deck v0134/Manager v0121);批398 操作員令「將 VRN VAL 收個尾吧」:+via-closeout [vrn|vap|all] [--run] [--dir 夾](MDL141 收尾閘:VRN 驗證逐份五段鏈+核對態 DONE|FAIL|PENDING;VAP 逐圖驗;CLOSEOUT_latest.md)+ via-vrnval/via-vapval 別名;批397 雙副本律:工作站實錄 新視窗 profile 點源 Github 母副本(main c14d428c;v0148)→ via-reload 分支感知拉 origin/main=拉不到 PR #30 未併的批381–396 → via-famui/via-console 不認;b381 副本(claude/… v0161)只在該夾啟動的視窗生效 → +via-pin(把 profile 點源行換成本窗副本;--show 只看;只改 profile 一行,兩副本檔案零觸碰)+ via-reload 雙副本提示;批396 工作站實錄修:+via-rebuild(MDL050 多環境隔離重建/旁建零破壞;via-envgov digest「下一指令」指路的 via-rebuild --env 在冊內從未登錄=死路;無參數=--offline 唯讀計畫);via-entry 次序文字 15 步→16 步含 console/handover;批394 工作站實錄修:+via-chip(ENG056 籌碼增量)/via-price(ENG054 價格增量;別名 via-tw-backfill)——ENG081/ENG056 docstring 指路的 via-chip 從未登錄=死路;籌碼止 08-25 根因=日更鏈 ③ 跑時價表尚無 08-26 後交易日(ENG064 回補在後才補齊),現在重跑即補;批393 工作站實錄修:+via-bg 背景引擎進程唯讀一覽(誰持 DuckDB 單寫者鎖一看便知;絕不 Stop-Process;實錄:[FAIL] 庫忙曾指路 via-status 但那是同步頁不是進程表);via-align 基準日律/持鎖者解析在引擎側 ENG081;批392 操作員令「參數最小化;台股除財報外抓全部;國際資訊勾選放右面板;啟動跑一切;VRN TAB2/3/4;起始統一 2023-01-01;VAP 規格與圖;VIA Central Console=超詳細系統狀態如 handover reports 一頁堆疊矩陣可轉 MD 接棒」→ +via-handover(MDL140 接棒狀態台:build|status|md;--open;別名 接棒/接棒LIVE);via-console 頁改 批392 版(整類起始日遮罩輸入/國際資訊右面板勾選/VRN 單鍵啟動/TAB BASIC INFO·SUMMARY·FINANCIAL DATA 核對 VDF 為主/VAP 規格與圖/跑成功?);批391 工作站實錄「start http://127.0.0.1:8765/console 被 VIA_NO_OPEN 抑制;via-align update --apply 撞單寫者鎖 traceback」→ via-open 認 http(s):// URL(只走瀏覽器 exe;別名 LIVE/主控台LIVE=樞紐 /console)+via-console --open 樞紐在線=開 LIVE 網址、離線=開快照頁;ENG081 讓庫律;批390 操作員令「左面板輸入/右面板矩陣;VDF 查詢標的分類細項(總體經濟 PMI/通膨/就業;台股 TWSE/TPEX 可新增代碼);起始日個別可改;財報當季/累計/年度年起迄;DEFAULT 最新;庫狀況;日交易×籌碼數量對齊更新清單;parquet 增量 DuckDB;右側矩陣篩選/大到小;Windows U/I 下拉/勾選/全選/全不選;VRN 資料夾拖曳/啟動/動畫/整體跑況 BASIC INFO/SUMMARY/FINANCIAL DATA;VAP 簡輸入」→ +via-console(MDL139 輸入主控台:build 頁|status|set k=v|argv|run --item;--open 走 via-open 主控台;樞紐在線 http://127.0.0.1:8765/console 可啟動)+via-align(VDF_ENG081 台股日交易×籌碼數量對齊 check|update --apply|status;vdf 境 python)+via-open 別名 主控台/輸入;批388 操作員令「若能跑 vdf vrn 的 u/i」→ via-famui vdf|vrn|vap|all [--open](MDL138 家族 U/I 再生閘:家族境 python 真跑頁面產生器→頁新鮮/零 CDN 判準→FAMILY_UI 索引頁;via-vdfui/via-vrnui 別名;via-open 別名 VDF/VRN/四點/家族);批387 工作站實錄「Windows autocrlf 工作副本 CRLF → Grok CmdMatrix 尾段 via-enter | Out-Null 未去除,載入即 cd 到主 clone」→ 去尾段 regex 容 \r;via-rungate --family vrn 誤判動詞/via_vrn_312 無 duckdb → MDL137 動詞白名單+--approve-install 補庫;批386 Grok 主控台 VRN 契約接回母倉:via-vrn4=一題四點文摘(VRN_ENG080;潛在上漲空間=目標價除權息調整後 vs 最新 adj close;K2 稀釋 EPS n～n+3 YoY;K3/K4 首頁其餘;K5 風險可空;quote-or-abstain 不發明不平均;via_vrn_312 python);批385 工作站實錄「via-reload 在 b381 worktree(claude/… 分支)固定拉 origin/main → ff 失敗 HEAD 8be0780 不動 → via-entry/via-vdfdb/via-vapone/via-rungate 永遠 not recognized;舊版 MDL135 不識 --only-kind 卻靜默照跑全段」→ via-reload 分支感知(當前分支≠main 即拉 origin/<分支>;印分支與 HEAD 前後)+MDL135 旗標白名單誠實停+via-envgov conflicts 衝突明細;批384 操作員令「以此為中央控管將 session_01R2d69oa1AGvnPVwjSUdSv5(VIA系統後續工作;claude/via-system-followup-tz7k9t@c14d428=main=本分支基底)整合完畢;vdf vrn 能跑」→ VDF/VRN/VAP 引擎短令一律以家族境 python 啟動(Get-VIAEnvPython vdf|vrn|vap;境缺=base 退路)+via-rungate(MDL137 能跑閘:家族境 python 真跑引擎自測;--fast/--all;status)+via-py <family> <script> 通用家族啟動器;批383 操作員令「將 river-beam-aurora-acorn 裡面的檔案接回做為整合為一入口」+「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合;vap 補充;vdf vrn 要弄到實際能跑;vdf 要將資料庫存入;之前有的資料庫整理好抓過的不必再抓」→ +via-entry(唯一入口燈板/plan/roster;--scan/--open/--console)+via-env(→via-envgov 正本)+via-grok(Grok 短令冊;matrix 右側板)+via-webconsole(Grok 網頁主控台 8080;同意閘)+via-vapone(VAP ONE 72 檢)+via-vdfdb(本機三庫整併 DuckDB;抓過不再抓)+via-envpy/Get-VIAEnvPython(家族境 python 解析;功能件住 via_ 境=啟動器指對 python)+載入即接 Grok CmdMatrix(去尾段自動執行;撞名母倉先發先得)+via-open 別名 矩陣/入口;批381 操作員令「依照已成功地建構布局向上新增;最壞還原成原本規劃;base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」→ +via-envgov(CGC_MDL135 環境治理統一引擎:全景式分析 base/via_core/via_* → uv 毫秒快篩 → base 該有冊閉包 → 衝突立拔家族路由 → Zero-Hydra 分流拓撲三輪 → LKGC/rollback → 四分區 UI Matrix;預設 run --offline 唯讀;apply --approve 才動;base 移除另 --approve-remove)+via-envgov-auto(Invoke-VIA-EnvGovernance 單一 PowerShell 一貼即用;-Background 非阻塞);批380 操作員令「用一個 PowerShell 完成所有動作 不影響系統健康 不可造成九頭龍風險 20 的加速器 不卡斷」→ via-autorun 四閘版:①20 加速器點亮 ②Hydra 哨兵 H1–H6 先行(H3/H5 阻擋=誠實停) ③全程零跳出零 TTY 等待 ④逾時 kill 不卡斷;批379 操作員在電腦前「自動完成所有動作 不要打開 VS Code 我不知道要怎麼辦」→ +via-autorun 一鍵全自動(雙擊 via-autorun.cmd 即可;結束停窗)+git 永不開編輯器 env;批378 操作員令「不要一直開啟 VS Code,全自動完成一切」→ 載入即全域 VIA_NO_OPEN=1(所有短令零跳出;看頁只走 via-open 瀏覽器道;VIA_OPEN_PAGES=1 可解);批377 +via-lanes 十道並行安全編排(MDL134;Hydra 哨兵)+via-mobile --lanes;批376 +via-productgate 產品資格閘九閘(MDL133);via-mobile 末段 +productgate digest;批375 +via-etfhist 每日持股史深;批374 +via-etfuniv 主動 ETF 宇宙日更;批373 +via-etfrev 主動 ETF×月營收合流;批371 via-ves→MDL132 橋(尾版鏡像+安全種子+雙跑;--raw 直通原件);批370 +via-ves 唯讀 E3 標準化掃描;批368 +via-projects 四專案完工矩陣;+via-revfill 月營收史深;批367 via-reload 同名雙物大寫原件復位;批366 via-mobile 零跳出 VIA_NO_OPEN=1;批362 via-fred 無動詞=run;批360/361 +via-fred/via-vdfarch;批254 立;批260 +via-all;批316 +via-pipeline;批323 +via-accel/via-accel-check;批325 +via-rotation/via-repo-optimize;批327 +via-vapstack;批328 +via-reload;批330 +via-plotlaw;批331 via-reload 先拉齊;批332 +via-system/via-api;批333 +via-master;批335 +via-complete;批336 +via-intake-roster;批337 via-reload 拉齊誠實+產出頁自動讓位;批338 可編輯模板排除;批339 短令清單動態;批340 +via-datahome/via-complete 分離啟動器;批342 +via-six 六流程 Zero-Hydra 編排;批344 via-complete watch/stop;批345 +via-bridge-sweep)
# =====================================================================
# 批254 摩擦修:舊制=Register-Profile 把函式全文塞 $PROFILE(要跑 via
# +開新視窗+每加一指令就 v010x 重貼)。新制=點源架構:
#   ①本檔=十指令唯一定義處(global 域;git pull 即最新)
#   ②$PROFILE 只留一行點源(VIA.ps1 自動補;舊 v010x 段無害,點源
#     在後=後定義勝)
#   ③當場生效:. "<本檔路徑>"(不用新視窗不用 via)
# =====================================================================
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path
# 批614:同時釘一份 global。理由是自動重點源——在 scriptblock 裡 `. 冊` 的話,
#   `$VIA` 只活在那個 scope,離開就沒了,之後從全域呼叫任何短令都會找不到根。
#   `function global:` 的函式解析 `$VIA` 會沿 scope 鏈走到 global,所以釘這一份就接得上。
$global:VIA = $VIA
# 批486/B531:所有 py 指令統一走 Invoke-VIAPython(25 加速器控制面 + 動態進度條 + 邊跑邊轉播 + 逾時不卡斷;stdout 走 pipeline,上游捕捉照舊)
$viaPyProg = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"; if (Test-Path -LiteralPath $viaPyProg) { . $viaPyProg } else { Write-Host "  [VIA] VIA_PS_PyProgress_Module.ps1 缺(中央唯一入口不可用;已 fail-closed 停止)" -ForegroundColor Red; function global:Invoke-VIAPython { param([string]$Family="",[string]$Python="",[int]$TimeoutSec=0,[Parameter(ValueFromRemainingArguments=$true)][object[]]$Rest) Write-Host "  [Invoke-VIAPython] 中央 helper 缺失;禁止繞過 VIA 直呼 Python" -ForegroundColor Red; $global:LASTEXITCODE = 2 } }
$global:VIARegisterPath = $MyInvocation.MyCommand.Path   # 批383:撞名守衛掃描本冊用

# 批378:全域零跳出律——.html 預設程式=VS Code,任何 --open 皆會彈 VS Code(批366 只管 via-mobile 不夠)。載入短令冊即設 VIA_NO_OPEN=1:
# py 側 SUP_MDL737 閘(webbrowser/os.startfile 頁面目標 no-op)+PS 側 PS-ACCEL 閘(Start-Process/Invoke-Item)全樹生效;頁面只落檔。
# 想看頁:via-open <頁名片段>(只走瀏覽器 exe,永不經 .html 預設程式);想恢復舊行為:$env:VIA_OPEN_PAGES="1" 後 via-reload。
if ($env:VIA_OPEN_PAGES -ne "1") { $env:VIA_NO_OPEN = "1" }
# 批379:git 永不開編輯器(core.editor=code --wait 會彈 VS Code 等你關窗=卡住);GIT_EDITOR=true 接受預設訊息;不問密碼提示
$env:GIT_EDITOR = "true"; $env:GIT_MERGE_AUTOEDIT = "no"; $env:GIT_SEQUENCE_EDITOR = "true"; $env:GIT_TERMINAL_PROMPT = "0"
function global:Get-VIANewest([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
# 批408/B533:同意閘不覆蓋且 fail-closed。未明確設置時固定為 OFF；VIA 絕不代操作員開網路。
# 每次呼叫都覆寫,操作員自設的值永遠被蓋掉;閘二包內法遵只認 I_ACCEPT_RESPONSIBLE_SCRAPING
# (見 functional modules/VRN/webscraping_dualengine_*/VIA_WebScraping_Compliance_SSOT.json 的
# required_consent_token),"YES" 過不了 def_validate_consent → check_url 一律 DENY → 爬蟲道不可達。
# 本函式只在「未設」時補預設值(既有六令行為零變更),已設者尊重;仍不代操作員設任何新意圖。
function global:Set-VIAGateDefaults {
    if (-not $env:VIA_NET_CONSENT)    { $env:VIA_NET_CONSENT = "OFF" }
    if (-not $env:VIA_SCRAPE_CONSENT) { $env:VIA_SCRAPE_CONSENT = "OFF" }
}
# 批408:閘態一覽(唯讀;絕不印原值,只報是否等於期望 token)
function global:via-gates {
    $g1 = $env:VIA_NET_CONSENT; $g2 = $env:VIA_SCRAPE_CONSENT
    $tok = "I_ACCEPT_RESPONSIBLE_SCRAPING"
    $s1 = if ($g1 -eq "YES") { "OPEN" } elseif ($g1) { "SET(非 YES)" } else { "未設" }
    $s2 = if ($g2 -eq $tok) { "OPEN(期望 token)" } elseif ($g2) { "SET 但非期望值(過不了包內法遵)" } else { "未設" }
    Write-Host ("  [閘一 VIA_NET_CONSENT   ] " + $s1) -ForegroundColor $(if ($g1 -eq "YES") { "Green" } else { "Yellow" })
    Write-Host ("  [閘二 VIA_SCRAPE_CONSENT] " + $s2) -ForegroundColor $(if ($g2 -eq $tok) { "Green" } else { "Yellow" })
    Write-Host ("  [說明] http/headers 兩道只需閘一;scrape 道另需閘二=期望 token。要開爬蟲道請自行親設:") -ForegroundColor DarkGray
    Write-Host ('         $env:VIA_SCRAPE_CONSENT = "' + $tok + '"') -ForegroundColor DarkGray
    Write-Host ("  [律] 本系統永不代操作員設任何同意閘;短令只在該閘未設時補預設,已設者尊重。") -ForegroundColor DarkGray
}
# 批383:家族境 python 解析(操作員令「vdf vrn 要弄到實際能跑」:功能件住 via_ 境(Baseline 冊 docs→via_vrn_312/data_fetch→via_vdf_312/plot_ui→via_vap_312),啟動器須指對境 python;base 只放共用工具)
# 序:$env:VIA_PY_<FAMILY> 覆寫 > 境根(VIA_ENV_ROOT/VIA_ENV_ROOTS/~\envs/C:\Users\tonyk\envs/conda envs/$VIA\Environments/$VIA\.venv-via_<f>)×候選名(Baseline 別名 via_<f>_312/via_<f>/…)> "python"(base 退路;via-envpy 誠實印黃);規則正本+自測=CGC_MDL136 EntryBridge envpy
# 批476 啟動層:所有 PY 檔案都要加上加速器 → 不逐檔改(量過:VDF 4/109、VRN 0、VAP 0 綁著;逐檔=幾百個新版本檔),
#   改成本視窗起的每一支 python 起跑就自動載 <VIA>\supportive modules\bootstrap\sitecustomize.py。
#   PYTHONPATH 只前置不覆蓋;VIA_FAMILY 由 via-py / 匯流排按家族設(網路正典件只掛 vdf);同意閘一個字不碰。
function global:Set-VIABoot {
    $b = Join-Path $VIA "supportive modules\bootstrap"
    if (-not (Test-Path -LiteralPath $b)) { return }
    $env:VIA_ROOT = $VIA
    if ($env:PYTHONHOME) { Write-Host ("  [VIA] 母殼帶 PYTHONHOME=" + $env:PYTHONHOME + " → 家族境子行程會載錯版標準庫(SRE module mismatch;批514 Z15 根因)。VIA 子行程已自動撤(L32),根治=你的手:Remove-Item Env:PYTHONHOME;查 `$PROFILE / ~\envs\via_core\Scripts\Activate.ps1 / [Environment]::GetEnvironmentVariable('PYTHONHOME','User')") -ForegroundColor Yellow }
    $cur = "" + $env:PYTHONPATH
    if ($cur -notlike ("*" + $b + "*")) { $env:PYTHONPATH = if ($cur) { $b + [IO.Path]::PathSeparator + $cur } else { $b } }
}
Set-VIABoot
function global:Get-VIAEnvPython([string]$Family) {
    $f = ("" + $Family).ToLower(); if (-not $f) { return "python" }
    $ov = [Environment]::GetEnvironmentVariable("VIA_PY_" + $f.ToUpper()); if ($ov -and (Test-Path -LiteralPath $ov)) { return $ov }
    $alias = @{ "vdf" = @("via_vdf_312", "via_vdf", "via_vdf_313"); "vrn" = @("via_vrn_312", "via_vrn", "via_extract_312", "via_vrn4"); "vap" = @("via_vap_312", "via_vap", "via_vap_313"); "core" = @("via_core_312", "via_core", "venv_core"); "ocr" = @("via_paddle_311", "via_paddle_312", "via_ocr", "paddle_312", "paddle_311"); "table" = @("via_camelot_311", "camelot_311"); "html" = @("via_html_312"); "nlp" = @("via_nlp"); "ml" = @("via_ml"); "tools" = @("via_tools_312") }
    $names = @(); if ($alias.ContainsKey($f)) { $names += $alias[$f] }; $names += @(("via_" + $f + "_312"), ("via_" + $f), ("via_" + $f + "_313"), ("via_" + $f + "_311"), (".venv-via_" + $f))
    $roots = @($env:VIA_ENV_ROOT) + @(("" + $env:VIA_ENV_ROOTS).Split(";")) + @("$env:USERPROFILE\envs", "C:\Users\tonyk\envs", "$env:USERPROFILE\miniconda3\envs", "$env:USERPROFILE\Miniconda3\envs", "$env:USERPROFILE\anaconda3\envs", "$env:USERPROFILE\.virtualenvs", "$VIA\Environments", $VIA) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    foreach ($r in $roots) { foreach ($n in $names) { foreach ($sub in @("Scripts\python.exe", "python.exe", "bin\python3", "bin\python")) { $p = Join-Path (Join-Path $r $n) $sub; if (Test-Path -LiteralPath $p) { return $p } } } }
    return "python"
}
function global:via-envpy { $f = if ($args.Count -gt 0) { "" + $args[0] } else { "vdf" }; $p = Get-VIAEnvPython $f; if ($p -eq "python") { Write-Host ("  [envpy] " + $f + " 境未見 → base 退路 python(建境:via-envgov apply --approve(ENSURE_ENV);或設 `$env:VIA_PY_" + $f.ToUpper() + ")") -ForegroundColor Yellow } else { Write-Host ("  [envpy] " + $f + " → " + $p) -ForegroundColor Green }; $p }
# 批383:Grok 主控台短令矩陣接回(收容包 b383 scripts/VIA-CmdMatrix.ps1;原件零觸碰;操作員令「將裡面的檔案接回做為整合為一入口」)
# ①去尾段自動執行(欄 0:via-enter 進母根/via-matrix WPF 板/LOAD 燈=違批378 零跳出律)②撞名守衛:母倉先發先得(via-entry/via-env 母倉正本;Grok 同名改 -grok 尾綴;內部呼叫鏈同步改指)
# ③Grok 非 global 助手(Lamp/Get-VIAZh/…)升 global(函式域點源後仍可用);規則正本+驗證=CGC_MDL136 EntryBridge(cmdmatrix-clean);$env:VIA_GROK_MATRIX="0" 可不載
function global:Import-VIAGrokMatrix {
    $cm = "$VIA\supportive modules\references\intake\VIA_GrokConsole_AuroraAcorn_b383\scripts\VIA-CmdMatrix.ps1"
    if (-not (Test-Path -LiteralPath $cm)) { return @() }
    try {
        $t = Get-Content -LiteralPath $cm -Raw -Encoding UTF8
        $t = [regex]::Replace($t, "(?m)^via-enter \| Out-Null[ \t\r]*$", "")   # 批387:CRLF 工作副本容 \r(否則載入即執行 via-enter → cd 主 clone)
        $t = [regex]::Replace($t, "(?m)^try \{ via-matrix \}.*$", "")
        $t = [regex]::Replace($t, "(?m)^Lamp 'GREEN' 'LOAD'.*$", "")
        $mine = @("via-entry", "via-env") + @([regex]::Matches((Get-Content -LiteralPath $global:VIARegisterPath -Raw -Encoding UTF8), "function global:(via[\w-]*)") | ForEach-Object { $_.Groups[1].Value })
        $ren = @()
        foreach ($m in @([regex]::Matches($t, "function global:(via[\w-]*)") | ForEach-Object { $_.Groups[1].Value })) {
            if ($mine -contains $m) {
                $t = $t.Replace(("function global:" + $m + " {"), ("function global:" + $m + "-grok {"))
                $t = [regex]::Replace($t, ("(?m)^(\s*)" + [regex]::Escape($m) + "\s*$"), ('$1' + $m + "-grok"))
                $ren += ($m + "→" + $m + "-grok")
            }
        }
        $t = [regex]::Replace($t, "(?m)^function (?!global:)([\w-]+)", 'function global:$1')
        . ([scriptblock]::Create($t))
        $verbs = @([regex]::Matches($t, "function global:(via[\w-]*)") | ForEach-Object { $_.Groups[1].Value })
        Write-Host ("  [Grok 矩陣] " + $verbs.Count + " 令已載(" + ($ren -join " ") + ";尾段自動執行已去;via-grok 看冊;via-matrix 開右側板)") -ForegroundColor DarkCyan
        return $verbs
    } catch { Write-Host ("  [Grok 矩陣] 載入失敗(不影響母倉短令):" + $_.Exception.Message) -ForegroundColor Yellow; return @() }
}
$VIAGrokVerbs = @(); if ($env:VIA_GROK_MATRIX -ne "0") { $VIAGrokVerbs = @(Import-VIAGrokMatrix) }
$global:VIAGrokVerbs = $VIAGrokVerbs   # 批614:同理(自動重點源後仍找得到)

function global:regen-all { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL096_SyncStatus_v*.py") --regen-all }
function global:via { powershell -NoProfile -ExecutionPolicy Bypass -File "$VIA\VIA.ps1" }
function global:via-status { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL096_SyncStatus_v*.py") --open }
function global:via-selftest { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL064_SelftestGrid_v*.py") @args }
function global:selftest { via-selftest @args }
function global:via-intake { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Collect-VIA-Intake-v*.ps1") @args }
function global:via-help { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL102_CommandRoster_v*.py") --print }
function global:via-md { Invoke-VIAPython -Family "vrn" (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG075_DocToMarkdown_v*.py") run @args }
# 批421:兩收容系統升格為 VRN 支援模組(操作員令 REGISTER AND IMPLEMENT ...)。
# via-gle=GenericLayoutEngine v2.1.0 全後端統轄橋(SUP_MDL743;status|probe|route)
#   ——收容件早在庫,但只有 ENG072 私掛且只用一支,30 後端矩陣與多引擎路由全樹無人呼叫。
function global:via-gle { Invoke-VIAPython -Family "vrn" (Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL743_GenericLayoutHub_v*.py") @args }
# via-nlp=VIA_NLP_Application_System v1.8.0 統轄橋(SUP_MDL744;status|roster|delta|demo)
#   ——修尾版律破口:ENG072/ENG073 舊版把收容夾寫死 v1.1.0(18 模組),
#     v1.5.0/v1.8.0(39 模組:table_ops/layout_analysis/content_roles…)收容了也掛不上。
function global:via-nlp { Invoke-VIAPython -Family "vrn" (Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL744_NLPApplicationHub_v*.py") @args }
# 批423(操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」):via-allgreen=統包全流程尾版啟動器。
# 為什麼要新登錄一個名:工作站的 via-go 是**操作員自己放在 PATH 上的檔**(批358 已記
# 「同名=九頭龍→讓位」,所以短令冊永遠不定義 via-go),而它指的是寫死的
# Invoke-VIA-AllGreen-v0100.ps1——也就是說 v0101 的卡斷修**傳不到操作員手上**。
# 倉庫這邊改用尾版律 glob 起 Invoke-VIA-AllGreen-v*.ps1,新版一落地就自動生效。
# v0101 修的兩條:①子行程輸出不再被 Out-String 吞(邊跑邊轉播)
#                 ②$StageTimeoutSec 真正接線(v0100 宣告了卻整檔沒用過=永遠等下去)
function global:via-allgreen { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest "$VIA\supportive modules\registry" "Invoke-VIA-AllGreen-v*.ps1") @args }
Set-Alias -Name 統包 -Value via-allgreen -Scope Global -Force
Set-Alias -Name 版面橋 -Value via-gle -Scope Global -Force
Set-Alias -Name 語意橋 -Value via-nlp -Scope Global -Force
Set-Alias -Name 語法修 -Value via-psrepair-ast -Scope Global -Force
Set-Alias -Name 解卡 -Value via-unstick -Scope Global -Force
Set-Alias -Name 一鍵 -Value via-oneshot -Scope Global -Force
function global:via-prompt { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL109_PromptManager_v*.py") @args }
function global:via-analysis { Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG068_ETFConsensusAnalysis_v*.py") run; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG069_RevenueConsensusAnalysis_v*.py") run }
function global:via-manager { Invoke-VIAPython (Get-VIANewest "$VIA" "VIA_SYSTEM_MANAGER_v*.py") @args }
function global:via-rootcheck { & cmd /c "$VIA\VIA-ROOTCHECK.cmd" }
function global:via-tower-reset { & cmd /c "$VIA\VIA-TOWER-RESET.cmd" }
function global:via-ssot { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL115_SSOTRegexDict_v*.py") @args }
function global:via-register { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL113_UnifiedRegistry_v*.py") @args }
function global:via-health { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL114_CommandCenterBridge_v*.py") run }
function global:via-tpn { Invoke-VIAPython -Family "vap" (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG011_TemplateRegistry_v*.py") @args }
function global:via-psrepair { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-PSRepair-v*.ps1") @args }
function global:via-all { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-All-v*.ps1") @args }
# 批323/B531:25 項加速器唯一入口。--activate 先點亮 SUP_MDL737，再由 CGC_MDL156 驗收。
# PS roster→PS runtime→Python sitecustomize→SuperAccel/Celeritas/Aegis mount 全部 GREEN 才算 READY。
function global:via-accel {
    $a = @($args)
    $control = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL156_VIAAcceleratorControl_v*.py"
    $super = Get-VIANewest "$VIA\supportive modules" "SUP_MDL737_SuperAccelModule_v*.py"
    if (-not $a) { $a = @("selftest") }
    if ($a -contains "--activate") {
        Invoke-VIAPython $super "--activate"
        Invoke-VIAPython $control "selftest"
    } elseif ($a[0] -in @("status", "selftest", "manifest", "routes")) {
        Invoke-VIAPython $control $a
    } elseif ($a[0] -in @("--status", "--selftest", "--manifest", "--routes")) {
        Invoke-VIAPython $control (($a[0] -replace '^--', ''))
    } else {
        Invoke-VIAPython $super $a
        Invoke-VIAPython $control "status"
    }
}
# 批384:加速器套件導入閘(MDL142;冊=Celeritas 尾版 _LIB_MAP 88 件;路由=MDL135 尾版 core_whitelist/high_risk/purpose_hints;
#   境=via_core/via_vdf/via_vrn/via_vap(別名序);探針 find_spec 零副作用;GPU 無卡/需系統二進位/平台不符=誠實不列計畫;
#   base 零觸碰(除 --include-base);--apply --approve 才裝(uv 優先退 pip);同意閘未開=拒裝)
#   via-accel-import [--env-root <envs 根>] [--apply --approve] [--include-base] [--timeout N] [digest]
function global:via-accel-import { Set-VIAGateDefaults; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL142_AccelImport_v*.py") @args }
function global:via-accel-check {
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL117_AccelCoverage_v*.py") run
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL156_VIAAcceleratorControl_v*.py") selftest
}
# 批325:故事族群輪動橋接(ENG072 尾版;run 預設,可帶 export/preflight/--pkgtest)+repo 衛生一鍵(只宜工作站)
function global:via-rotation { Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG072_StoryRotationBridge_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-repo-optimize { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-RepoOptimizer-v*.ps1") @args }
# 批327:VAP Seaborn 垂直圖組橋接(ENG015 尾版;預設 stock 2330;可帶 stock <代碼> | heatmap | --selftest)
function global:via-vapstack { Invoke-VIAPython -Family "vap" (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG015_SeabornStackBridge_v*.py") $(if ($args) { $args } else { @("stock", "2330") }) }
# 批328 實錄:拉齊後既開視窗仍是舊短令冊(profile 只在開窗時點源)→via-reload=本窗重點源尾版冊,免開新視窗
# 批331 實錄:via-reload 只重載磁碟冊,未拉齊=仍舊版→先 fetch+ff-only 再重載(分流不動;VIA-ALL 才對齊)
# 批337 實錄:工作站 pull 被本地再生頁(VIA_UI_Portal)差異擋下,而 via-reload 靜默 2>$null=假拉齊(HEAD 不動仍印「已拉齊」)。
# 改:①fetch ②ui_support 產出頁本地差異=再生物→自動還原讓位(git checkout;誠實印件數)③ff-only 失敗=印 git 原話+阻擋檔清單(不 reset 不 stash 其他檔)④重載尾版冊+印 HEAD 前後
# 批386:拉齊醫生(MDL143;status|plan|sync --apply;三態 BEHIND/DIVERGED/AHEAD;衝突逐檔按律:台帳聯集/同名雙物讓位遠端/再生物取遠端/其餘 MANUAL 誠實停)
# 批387:副本醫生(MDL144;同機多副本體檢=Register 尾版版號/動詞在位/分支 HEAD/與遠端分歧/未合併/髒度 → 判誰最新 → 印立即可用+一勞永逸(via-pin)指令;全唯讀不改 profile)
# 批389:PowerShell 真測閘(MDL145;P1 AST 解析 VIA 根全 .ps1(尾版必綠,封存版壞=WARN 具名)/P2 真建 git 倉造分叉跑啟動器驗自癒/P3 點源短令冊驗 via-vdffetch 具名參數;pwsh 缺=SKIP 誠實)
function global:via-pstest { $env:VIA_PWSH = $(if ($env:VIA_PWSH) { $env:VIA_PWSH } else { (Get-Command pwsh -ErrorAction SilentlyContinue).Source }); Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL145_PsTestGate_v*.py") @args }
function global:via-oneshot { $t = (Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-OneShot-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1); if ($t) { & $t.FullName -Root (Split-Path $VIA -Parent) @args } else { Write-Host "  [FAIL] Invoke-VIA-OneShot-v*.ps1 不在本副本(先 via-unstick 或自 origin 取出)" } }
function global:via-unstick { $t = (Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-Unstick-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1); if ($t) { & $t.FullName -Root (Split-Path $VIA -Parent) @args } else { Write-Host "  [FAIL] Invoke-VIA-Unstick-v*.ps1 不在本副本(先拉齊或從 origin 取出)" } }
function global:via-psrepair-ast { $env:VIA_PWSH = $(if ($env:VIA_PWSH) { $env:VIA_PWSH } else { (Get-Command pwsh -ErrorAction SilentlyContinue).Source }); Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL146_PsAstRepair_v*.py") @args }
function global:via-copies { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL144_CopyDoctor_v*.py") @args }   # 批391:+--heal(對最新副本呼拉齊醫生 sync --apply;零 force 零刪除)
function global:via-medic { $root = Split-Path $VIA -Parent; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL143_MergeMedic_v*.py") @(if ($args) { $args } else { @("status") }) --root $root }
function global:via-reload {
    $root = Split-Path $VIA -Parent
    $before = git -C $root rev-parse --short HEAD
    # 批385:分支感知拉齊——當前分支=main 拉 origin/main;否則(worktree 在 claude/… 等分支)拉 origin/<當前分支>;detached=main
    $branch = (git -C $root rev-parse --abbrev-ref HEAD 2>$null); if (-not $branch -or $branch -eq "HEAD") { $branch = "main" }
    $target = "origin/" + $branch
    git -C $root fetch -q origin $branch 2>$null
    # 批385:未完成合併偵測(UU/AA/DU/UD/AU/UA)——此態下任何 merge/pull 皆被擋,且 stash 也救不了;誠實指路或明令解
    $unmerged = @(git -C $root status --porcelain 2>$null | Where-Object { $_ -match "^(UU|AA|DU|UD|AU|UA) " } | ForEach-Object { $_.Substring(3).Trim('"') })
    if ($unmerged.Count -gt 0) {
        Write-Host ("  [VIA] 未完成合併 " + $unmerged.Count + " 件=拉齊必被擋(誠實):`n    " + ($unmerged -join "`n    ")) -ForegroundColor Yellow
        if ($args -contains "--resolve-theirs") {
            # 明令解:衝突檔一律取 origin/<分支> 版(同名雙物=先發先得;台帳聯集已在該版內)→ 完成合併提交;零刪除零 force
            foreach ($f in $unmerged) { git -C $root checkout $target -- $f 2>$null; git -C $root add -- $f 2>$null }
            $msg = "解未完成合併(via-reload --resolve-theirs):衝突 " + $unmerged.Count + " 件取 " + $target + " 版(同名雙物讓位先發者;台帳聯集版;零刪除零 force)"
            git -C $root -c user.name="tonykuni" -c user.email="tonyhuang0122@gmail.com" commit -q -m $msg 2>$null
            if ($LASTEXITCODE -eq 0) { Write-Host "  [VIA] 已解並提交;續拉齊" -ForegroundColor Green }
            else { Write-Host "  [VIA] 解後提交未成(誠實;可能已無待提交項)" -ForegroundColor Yellow }
        } else {
            Write-Host "  [VIA] 解法(二選一,皆零刪除):`n    ① 放棄這次合併回到乾淨態:git -C `"$root`" merge --abort   (無 merge 可放棄時用 git -C `"$root`" reset --merge)`n    ② 保留並以遠端版解衝突:via-reload --resolve-theirs" -ForegroundColor Cyan
            return
        }
    }
    # 批386:分叉(本地與遠端各有提交)=--ff-only 永遠失敗 → 委派 MDL143 拉齊醫生(merge --no-ff + 按律解衝突;零 force 零刪除)
    $cnt = (git -C $root rev-list --left-right --count ("HEAD..." + $target) 2>$null)
    if ($cnt -match "^\s*(\d+)\s+(\d+)") {
        $ahead = [int]$Matches[1]; $behind = [int]$Matches[2]
        if ($ahead -gt 0 -and $behind -gt 0 -and ($args -notcontains "--no-medic")) {
            Write-Host ("  [VIA] 分叉:本地獨有 " + $ahead + " 提交 · 遠端獨有 " + $behind + " 提交 → 拉齊醫生接手(merge --no-ff;台帳聯集;同名雙物讓位遠端;零 force 零刪除)") -ForegroundColor Cyan
            $medic = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL143_MergeMedic_v*.py"
            if ($medic) { python $medic sync --apply --branch $branch --root $root }
            else { Write-Host "  [VIA] 拉齊醫生缺(CGC_MDL143_MergeMedic_v*.py)→ 手動:git -C `"$root`" merge --no-ff --no-edit $target" -ForegroundColor Yellow }
        }
    }
    # 批348 再生物冊:引擎每次自測/再生會回寫的追蹤檔=產物非正本→拉齊前自動還原讓位(誠實印件數);台帳 VIA_AutoCode_Registry 永不還原(append-only)
    $regen = "^VeritasIntelligenceAnalytics/(supportive modules/ui_support/.*\.html|supportive modules/registry/VIA_(Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict|Schema_Registry|Tool_Escalation_Ladder|Unified_Register|IndustryUnifiedMap|Problem_Ledger|NetModules_Integration_Register|AccelModules_Integration_Register|VDFArchitecture|ProjectCompletion|ProductGate|ParallelLanes|AccelImport)_v\d+\.json|VIA-TOWER-RESET\.cmd|functional modules/VAP/references/intake/VAP_v025_Complete_Package/(output|spec)/.*\.json)$"
    $gen = @(git -C $root status --porcelain 2>$null | Where-Object { $_.Substring(0,2) -match "M" } | ForEach-Object { $_.Substring(3).Trim('"') } | Where-Object { $_ -match $regen -and $_ -notmatch "EditableTemplate" -and $_ -notmatch "VIA_AutoCode_Registry" })  # 批338:可編輯模板=操作員手改件,永不還原
    if ($gen.Count -gt 0) { git -C $root checkout -q -- $gen 2>$null; Write-Host ("  [VIA] 產出頁本地差異 " + $gen.Count + " 件=再生物,已還原讓位(誠實):" + ($gen -join ", ")) -ForegroundColor DarkYellow }
    $out = (git -C $root merge --ff-only $target 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        # 批347:阻擋檔=本地未提交→自動 stash(含未追蹤;記名)→ff-only→pop(VIA.ps1 Sync-Repo 同律;pop 衝突=stash 留存誠實印)
        $blk = @(git -C $root status --porcelain 2>$null)
        if ($blk.Count -gt 0 -and $out -match "overwritten|local changes|Not possible to fast-forward|Diverging") {
            $stMsg = "via-reload " + (Get-Date -Format "yyyyMMdd_HHmmss")
            git -C $root stash push --include-untracked -q -m $stMsg 2>$null
            Write-Host ("  [VIA] 阻擋檔 " + $blk.Count + " 件已 stash(" + $stMsg + "),拉齊後自動還原") -ForegroundColor DarkYellow
            $out = (git -C $root merge --ff-only $target 2>&1 | Out-String).Trim()
            $ffrc = $LASTEXITCODE
            $pop = (git -C $root stash pop 2>&1 | Out-String).Trim()
            if ($LASTEXITCODE -ne 0) { Write-Host ("  [VIA] stash 還原衝突(誠實;stash 留存,手動 git stash pop):" + $pop) -ForegroundColor Yellow } else { Write-Host "  [VIA] 阻擋檔已原樣還原" -ForegroundColor DarkYellow }
            if ($ffrc -ne 0) { Write-Host ("  [VIA] 拉齊仍失敗(誠實;非阻擋檔問題=分歧,見 git 原話):" + $out) -ForegroundColor Yellow }
            $global:LASTEXITCODE = $ffrc
        } else {
            Write-Host ("  [VIA] 拉齊失敗(誠實):" + $out) -ForegroundColor Yellow
            if ($blk.Count -gt 0) { Write-Host ("  [VIA] 阻擋檔:`n    " + ($blk -join "`n    ")) -ForegroundColor Yellow }
        }
    }
    # 批367 同名雙物讓位後復位:小寫梭 via-all/via-rootcheck/via-tower-reset.cmd 已 git mv 入收容冊;Windows 大小寫不分=git 刪小寫可能連帶刪掉大寫原件實體→缺即自 HEAD 復位(唯讀 checkout;誠實印)
    $caseOrig = @("VIA-ALL.cmd", "VIA-ROOTCHECK.cmd", "VIA-TOWER-RESET.cmd") | Where-Object { -not (Test-Path -LiteralPath (Join-Path $VIA $_)) -and (git -C $root ls-files --error-unmatch ("VeritasIntelligenceAnalytics/" + $_) 2>$null) }
    if ($caseOrig.Count -gt 0) { foreach ($c in $caseOrig) { git -C $root checkout -q -- ("VeritasIntelligenceAnalytics/" + $c) 2>$null }; Write-Host ("  [VIA] 同名雙物讓位後大寫原件復位 " + $caseOrig.Count + " 件:" + ($caseOrig -join ", ")) -ForegroundColor DarkYellow }
    $r = Get-VIANewest $VIA "Register-VIA-Commands-v*.ps1"; . $r
    $after = git -C $root rev-parse --short HEAD
    Write-Host ("  [VIA] 短令冊重載:" + (Split-Path $r -Leaf) + " · 分支 " + $branch + "(拉 " + $target + ")· HEAD " + $before + " → " + $after + $(if ($before -eq $after -and $LASTEXITCODE -ne 0) { "(未拉齊;看上方 git 原話)" } else { "" })) -ForegroundColor Green
    $pinDir = Get-VIAPinnedDir; if ($pinDir -and ($pinDir -ne $VIA)) { Write-Host ("  [VIA] 雙副本:新視窗預設(profile)=" + $pinDir + " ≠ 本窗 " + $VIA + " → 要讓新視窗也用本副本:via-pin(批397;只改 profile 一行)") -ForegroundColor DarkYellow }
}
# 批330:繪圖/TA 資料律稽核(價=還原 量=扣當沖;CGC_MDL118 尾版 --audit)
function global:via-plotlaw { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL118_PlotDataLaw_v*.py") $(if ($args) { $args } else { "--audit" }) }
# 批332:系統總台=六主體標準 U/I(VIA 首頁所有擷取資料/VDF/VAP/主動 ETF 分類/族群輪動/月營收);via-system 再生頁並開啟(樞紐在線=LIVE;否則 SNAPSHOT 誠實);via-api <主體> 印後端 JSON
function global:via-system { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL120_SystemUI_v*.py") $(if ($args) { $args } else { "--open" }) }
function global:via-api { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL119_SystemAPI_v*.py") $(if ($args) { $args } else { "subjects" }) }
# 批333:總控台=Codex 設計正本(VIA_SYSTEM_MANAGER 尾版 ui 再生)由樞紐同源 /master 供應(CSRF 權杖注入;file:// 唯讀預覽自動導同源);via-master=再生頁+開 /master(樞紐未起先打 via)
function global:via-master { Invoke-VIAPython (Get-VIANewest "$VIA" "VIA_SYSTEM_MANAGER_v*.py") ui --no-open; Start-Process "http://127.0.0.1:8765/master" }
# 批335:一鍵完工=未完工作冊(via-complete 印冊)+完工鏈 16 步依序跑(via-complete run;--only a,b 子集;--skip-net 離線試跑);閘(批212/P08/P09/P18)零自動解除
# 批336:上船件冊=references/intake 全收容包 × 整合鏈(引擎/頁/短令/任務)頁;via-intake-roster --open
function global:via-intake-roster { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL122_IntakeRoster_v*.py") $(if ($args) { $args } else { "--open" }) }
# 批340:一鍵完工=分離工人+直播尾讀(Invoke-VIA-Complete 啟動器;PS-ACCEL;關窗不斷;Ctrl-C 只離開觀看);無參數=印未完工作冊
# 批344:via-complete watch=重接最新 LAUNCH log 直播(Ctrl-C 只離開);via-complete stop=依最新 RUN_*/PROGRESS.json 停 MDL121 本體+當前步子程序(工人 Ctrl-C 免疫後唯一停止法)
function global:via-complete { if ($args.Count -gt 0 -and $args[0] -eq "watch") { $lg = Get-ChildItem "$VIA\VIA_Reports\completion" -Filter "LAUNCH_*.log" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; if ($lg) { Write-Host ("  [watch] " + $lg.FullName + "(Ctrl-C 只離開)") -ForegroundColor Cyan; Get-Content -Path $lg.FullName -Wait -Tail 20 -Encoding UTF8 } else { Write-Host "  [watch] 無 LAUNCH log" -ForegroundColor Yellow }; return }
    if ($args.Count -gt 0 -and $args[0] -eq "stop") { $pj = Get-ChildItem "$VIA\VIA_Reports\completion" -Filter "PROGRESS.json" -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1; if (-not $pj) { Write-Host "  [stop] 無 PROGRESS.json(無在跑工人)" -ForegroundColor Yellow; return }; $j = Get-Content $pj.FullName -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($id in @($j.pid, $j.self_pid)) { if ($id) { $pr = Get-Process -Id $id -ErrorAction SilentlyContinue; if ($pr) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; Write-Host ("  [stop] 已停 PID " + $id + "(" + $pr.ProcessName + ")") -ForegroundColor Yellow } else { Write-Host ("  [stop] PID " + $id + " 不在(已結束)") -ForegroundColor DarkGray } } }; Write-Host ("  [stop] 步 " + $j.step + "/" + $j.total + " " + $j.id + " · " + $pj.FullName) -ForegroundColor DarkGray; return }
    if ($args.Count -gt 0 -and $args[0] -eq "run") { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-Complete-v*.ps1") @($args | Select-Object -Skip 1) } else { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL121_CompletionAutomator_v*.py") @args } }
# 批340:資料本機家=接點律(倉內 output_hub→本機資料家 Junction;145 引擎零改;增量更新經接點寫入本機);via-datahome=status;via-datahome link/find/unlink
# 批490:操作員宣告資料家 C:\Users\tonyk\VIA System\via_database(parquet 本體 + duckdb 管家);via-datahome catalog [-Tables]=家內清點→一頁目錄;via-datahome plan=倉內散落整併計畫(只列不動)
function global:via-datahome {
    # 批491:-Relink=重接死接點(只換接點不動資料);-Point <倉內相對夾>=加接點
    $a = @($args | ForEach-Object { if ($_ -eq "-Tables") { "--tables" } elseif ($_ -eq "-DryRun") { "--dry-run" } elseif ($_ -eq "-Relink") { "--relink" } elseif ($_ -eq "-Point") { "--point" } else { $_ } })
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL123_DataHome_v*.py") @a
}
Set-Alias -Name 資料家 -Value via-datahome -Scope Global -Force
Set-Alias -Name 庫目錄 -Value via-datahome -Scope Global -Force
# 批350:紅站一鍵補齊鏈(MDL125:datahome 接點→OpenCC 輔助安裝→global 全球擷取→consensus/revenue_consensus→--refail 複驗;NET 步雙同意閘;誠實三態;心跳進度條);via-fixall=印步冊;via-fixall run [--only a,b] [--dry]
function global:via-fixall { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL125_FixAll_v*.py") @args }
# 批358:手機一鍵改名 via-mobile(工作站實錄:PATH 上已有操作員之 via-go=「VIA AllGreen 一鍵統包 v0100」;同名=九頭龍→讓位);=拉齊→六流程 dry-run→紅站補齊鏈(含時段實測)→digest
# 批366:操作員令「不要一直跳出 VS Code,自動到底完成所有動作」→ via-mobile 全程 VIA_NO_OPEN=1(SUP_MDL737 v0104 py 閘+PS-ACCEL 模組 PS 閘;所有頁面只落檔不跳出;結束後 via-open 可看);--open 覆寫
function global:via-mobile { $o = ($args -contains "--open"); $a = @($args | Where-Object { $_ -ne "--open" }); $env:VIA_NO_OPEN = $(if ($o) { "0" } else { "1" }); via-reload; Write-Host "--- [via-mobile] 六流程 dry-run(零跳出 VIA_NO_OPEN=$env:VIA_NO_OPEN)---" -ForegroundColor Cyan; via-six --no-open; Write-Host "--- [via-mobile] 紅站補齊鏈 ---" -ForegroundColor Cyan; if ($a -contains "--lanes") { $a = @($a | Where-Object { $_ -ne "--lanes" }); via-lanes run @a } else { via-fixall run @a }; Write-Host "--- [via-mobile] 四專案完工矩陣 ---" -ForegroundColor Cyan; via-projects digest; Write-Host "--- [via-mobile] 產品資格閘(九閘)---" -ForegroundColor Cyan; via-productgate digest; $env:VIA_NO_OPEN = $(if ($env:VIA_OPEN_PAGES -eq "1") { "0" } else { "1" }); Write-Host "--- [via-mobile] 完成;頁面已落檔未跳出;看頁:via-open 產品 / via-open 竣工 / via-open 架構 ---" -ForegroundColor Cyan }
# 批353:網路車道時段基準(操作員令「先測一些時段」;chart/chart×N(accel_map)/yf 三車道同標的同時段實測秒數與成功率;零入庫;親跑=同意);via-netbench [--tickers 2330,2317] [--days 60] [--workers 4] [--pause 0.35]
function global:via-netbench { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL126_NetBench_v*.py") run @args }
# 批360/361:FRED 宏觀 SSOT 擷取(ENG074;macro_ssot 190 series 從新往舊;checkpoint;accel_map+節流;parquet+DuckDB us_macro+polars 鏡;落 output_hub/mega=接點→本機資料家;鑰缺=當場輸入;親跑=同意);via-fred [run|status|lamps] [--since 1990-01-01] [--workers 4] [--rpm 100] [--only CPIAUCSL,UNRATE] [--fred-key <key>]
function global:via-fred { Set-VIAGateDefaults; $a = @($args); if (-not ($a | Where-Object { $_ -in @("run", "status", "lamps", "help") })) { $a = @("run") + $a }; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG074_FredMacroSSOT_v*.py") @a }
# 批368:月營收全市場史深回補(ENG075;MOPS t21sc03 上市/上櫃 國內/KY 月檔 2023-01→ 從新往舊;Big5;只增 anti-join;checkpoint;親跑=同意);via-revfill [run] [--since 2023-01] [--workers 3] [--max-months N] | status;(名 via-rev 讓位另線工作站別名=先發先得)
function global:via-revfill { Set-VIAGateDefaults; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG075_MonthlyRevenueBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
# 批371:VES 橋(MDL132)=尾版鏡像(史版不當多頭)→第 1 跑→安全種子決策(VIA 動詞冊/橋塊 REJECT/selftest 群 REJECT;append-only)→第 2 跑確定性套用;唯讀;--apply 永不經短令;via-ves [--root <相對子樹>] [--no-seed] [--single];via-ves --raw <VES 原生參數…>(直通收容原件,如 --slice <碼>)
function global:via-ves { if ($args -contains "--apply") { Write-Host "  [via-ves] --apply 不經短令(操作員親打 python <VES> --apply --token <hint>;Zero-Hydra 律)" -ForegroundColor Yellow; return }; if ($args -contains "--raw") { $ves = Get-VIANewest "$VIA\supportive modules\references\intake\VIA_VES_EngineStandardizer_b*" "via_engine_standardizer.py"; $a = @($args | Where-Object { $_ -ne "--raw" }); if (-not ($a -contains "--root")) { $a = @("--root", "$VIA\VIA_Reports\ves\tails_tree") + $a }; if (-not ($a -contains "--out")) { $a = @("--out", "$VIA\VIA_Reports\ves\out") + $a }; python $ves --no-ml-probe @a; return }; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL132_VesBridge_v*.py") run @args }
# 批375:主動 ETF 每日持股史深覆蓋+缺口回補(ENG078;IPO 起應有交易日 vs 快照;車道冊 VIA_ActiveETF_HistoryLanes VERIFIED 才呼;缺源=NO_SOURCE 誠實;親跑=同意);via-etfhist [daily [--offline] [--max-days N] | backfill | status]
function global:via-etfhist { Set-VIAGateDefaults; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG078_ActiveETFHoldingsHistory_v*.py") $(if ($args) { $args } else { "daily" }) }
# 批374:主動 ETF 宇宙日更(ENG077;A 碼律 ^\d{5}A$ + 國內成分揭露律;TWSE 官方冊→etf_book 後備→既有聯集只增;寫 ENG051 SSOT csv;親跑=同意);via-etfuniv [run [--offline] | status]
function global:via-etfuniv { Set-VIAGateDefaults; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG077_ActiveETFUniverse_v*.py") $(if ($args) { $args } else { "run" }) }
# 批373:主動 ETF 持股×月營收動能(ENG076;兩專案合流層;零網路;加權 yoy/重疊榜;頁 VIA_UI_ETFRevenueMomentum);via-etfrev [run|status]
function global:via-etfrev { Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG076_ETFRevenueMomentum_v*.py") $(if ($args) { $args } else { "run" }) }
# 批379/380/B531:via-autorun=一鍵全自動四閘版:①via-accel --activate(25 加速器控制面)②via-lanes plan(Hydra 哨兵 H1–H6;H3/H5 FAIL=誠實停)③via-mobile --lanes(拉齊→六流程→十道並行→矩陣→產品閘)④lanes digest;零跳出、零 TTY 等待(VIA_FRED_PROMPT=0)、逾時 kill 不卡斷;雙擊 via-autorun.cmd 同效且結束停窗
function global:via-autorun { $env:VIA_NO_OPEN = "1"; $env:VIA_FRED_PROMPT = "0"; $env:GIT_EDITOR = "true"; $env:PYTHONUTF8 = "1"
    Write-Host "=== [via-autorun] 一鍵全自動(單一 PowerShell;零跳出;不卡斷;約 20–60 分鐘)===" -ForegroundColor Cyan
    Write-Host "--- ① 25 加速器點亮與中央線控(CGC_MDL156;缺席=誠實 SKIP 零影響)---" -ForegroundColor Cyan; try { via-accel --activate } catch { Write-Host ("  [加速器] " + $_.Exception.Message) -ForegroundColor Yellow }
    Write-Host "--- ② 九頭龍哨兵 H1–H6(唯讀;H3 進程雙頭/H5 尾版律 FAIL=誠實停,不跑)---" -ForegroundColor Cyan; $plan = (via-lanes plan 2>&1 | Out-String); Write-Host $plan
    if ($plan -match "H3 FAIL|H5 FAIL") { Write-Host "=== [via-autorun] 九頭龍風險(見上 H3/H5)=停;請先關閉另一條在跑的補齊鏈或修尾版後重試 ===" -ForegroundColor Red; return }
    Write-Host "--- ③ 全自動主鏈(拉齊→六流程 dry-run→十道並行補齊→四專案矩陣→產品閘)---" -ForegroundColor Cyan; via-mobile --lanes
    Write-Host "--- ④ 十道並行存證 ---" -ForegroundColor Cyan; via-lanes digest
    Write-Host "=== [via-autorun] 畢;看頁:via-open 產品 ===" -ForegroundColor Cyan }
# 批378:via-open <片段|路徑>=只走瀏覽器可執行檔(Edge/Chrome/Firefox 依序),永不經 .html 預設程式(VS Code);缺瀏覽器=印路徑。別名:產品→ProductGate 竣工→ProjectCompletion 架構→VDFArchitecture 道→ParallelLanes 總控→MasterControl
function global:via-open { $alias = @{ "產品" = "VIA_UI_ProductGate"; "竣工" = "VIA_UI_ProjectCompletion"; "架構" = "VIA_UI_VDFArchitecture"; "道" = "VIA_UI_ParallelLanes"; "總控" = "VIA_UI_MasterControl"; "整" = "VIA_UI_Consolidated"; "系統" = "VIA_UI_SystemConsole"; "矩陣" = "VIA_MasterControl_Matrix"; "入口" = ("" + $VIA + "\VIA_Reports\entry\ENTRY_latest.html"); "VDF" = "VIA_UI_VDFArchitecture"; "VRN" = "VIA_UI_VRNControlTower"; "四點" = ("" + $VIA + "\VIA_Reports\vrn\four_point\DIGEST_latest.html"); "家族" = ("" + $VIA + "\VIA_Reports\ui\FAMILY_UI_latest.html"); "主控台" = "VIA_UI_InputConsole"; "輸入" = "VIA_UI_InputConsole"; "LIVE" = "http://127.0.0.1:8765/console"; "主控台LIVE" = "http://127.0.0.1:8765/console"; "總控LIVE" = "http://127.0.0.1:8765/master"; "接棒" = "VIA_UI_Handover"; "接棒LIVE" = "http://127.0.0.1:8765/handover" }; $q = if ($args.Count -gt 0) { "" + $args[0] } else { "VIA_UI_ProductGate" }; if ($alias.ContainsKey($q)) { $q = $alias[$q] }; if ($q -match '^https?://') { $bx0 = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1; if ($bx0) { Start-Process -FilePath $bx0 -ArgumentList $q; Write-Host ("  [via-open] " + (Split-Path $bx0 -Leaf) + " ← " + $q + "(樞紐 LIVE 道;批391)") -ForegroundColor Green } else { Write-Host ("  [via-open] 未找到瀏覽器 exe;請手動以瀏覽器開:" + $q) -ForegroundColor Yellow }; return }; $ui = Join-Path $VIA "supportive modules\ui_support"; $f = if (Test-Path -LiteralPath $q) { Get-Item -LiteralPath $q } else { Get-ChildItem -LiteralPath $ui -Filter "*.html" | Where-Object { $_.Name -like ("*" + $q + "*") } | Sort-Object Name | Select-Object -Last 1 }; if (-not $f) { Write-Host ("  [via-open] 找不到頁:" + $q + "(ui_support 內 *.html 片段或完整路徑)") -ForegroundColor Yellow; return }; $bx = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1; if ($bx) { Start-Process -FilePath $bx -ArgumentList ("`"" + $f.FullName + "`""); Write-Host ("  [via-open] " + (Split-Path $bx -Leaf) + " ← " + $f.Name) -ForegroundColor Green } else { Write-Host ("  [via-open] 未找到瀏覽器 exe;請手動以瀏覽器開:" + $f.FullName) -ForegroundColor Yellow } }
# 批377:十道並行安全編排(MDL134;FixAll 步冊→資源鏈 DAG:同庫序跑/鏈間並行≤10;Hydra 哨兵 H1 同名/H2 同版/H3 進程雙頭(鎖)/H4 單寫者/H5 尾版;離線 net 步 SKIP;零 force);via-lanes [plan | run [--workers N] [--only a,b] [--dry] | digest];via-mobile --lanes=補齊鏈改並行
# 批381/383:via-vdffetch [年份] [--limit N] [--dry]=單一指令抓該年以後全部 VDF 資料(預設 2023)。
#   批383 改薄包裝:唯一正本=Invoke-VIA-VdfFetch-v*.ps1(尾版律)——該腳本自找 VIA 根、自進環境(點源短令冊尾版)、
#   用 vdf 家族境 python(批384 Get-VIAEnvPython)、同意閘不覆蓋(批408 Set-VIAGateDefaults)、20 加速器、
#   Hydra 哨兵 H1–H6(H3/H5 FAIL=誠實停)、十一步資料鏈十道並行、末印 lanes+projects digest。
#   新視窗一貼即用(不需先載短令冊):powershell -NoProfile -ExecutionPolicy Bypass -File "<VIA>\Invoke-VIA-VdfFetch-v0100.ps1" -Year 2023
function global:via-vdffetch {
    $y = if ($args.Count -gt 0 -and ("" + $args[0]) -match "^\d{4}$") { "" + $args[0] } else { "2023" }
    $s = Get-VIANewest $VIA "Invoke-VIA-VdfFetch-v*.ps1"
    if (-not $s) { Write-Host "  [via-vdffetch] 啟動腳本缺(Invoke-VIA-VdfFetch-v*.ps1;先 via-reload)" -ForegroundColor Yellow; return }
    # 批384:具名參數必用雜湊潑灑(陣列潑灑=位置參數,"-Year" 會被當成 $Year 的值)
    $p = @{ Year = $y }
    if ($args -contains "--dry") { $p["Dry"] = $true }
    $li = [Array]::IndexOf([string[]]@($args | ForEach-Object { "" + $_ }), "--limit")
    if ($li -ge 0 -and $args.Count -gt ($li + 1)) { $p["Limit"] = [int]("" + $args[$li + 1]) }
    elseif ($env:VIA_HIST_LIMIT -match "^\d+$") { $p["Limit"] = [int]$env:VIA_HIST_LIMIT }
    & $s @p
}
function global:via-lanes { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL134_ParallelLanes_v*.py") $(if ($args) { $args } else { "plan" }) }
# 批376:產品資格閘(MDL133;九閘 G1 矩陣存證/G2 短令↔梭/G3 樞紐任務/G4 頁衛生/G5 再生物讓位/G6 鑰匙守衛/G7 引擎尾版/G8 短令在位/G9 用法;QUALIFIED/CONDITIONAL/NOT_QUALIFIED 永不假綠);via-productgate [build --open | digest | --json]
function global:via-productgate { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL133_ProductGate_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批368:四專案完工矩陣(MDL131;VDF/VRN/主動 ETF/月營收 × grid 存證 × DuckDB 深度 × 任務/頁/令;RYG+下一指令;八段循環證據);via-projects [build --open | digest]
function global:via-projects { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL131_ProjectCompletion_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批360:VDF 資料架構(ENG073;SSOT 12 類→現役表/引擎/車道對映;DuckDB 盤點;--optimize dry-run 只增不減;--go 才寫;頁 VIA_UI_VDFArchitecture);via-vdfarch [build --open | --optimize [--go]]
function global:via-vdfarch { Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG073_DataArchitecture_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批352:VIA SuperHtml Parser(HTML content+UI component+JS/CSS logic+backend→Markdown;bs4/lxml/esprima/tinycss2/markitdown;NLP OneEngine v1.5.0 語意橋;自建根 C:\VIA\VeritasSuperHtmlParser);via-superhtml <路徑...> [-NoOpen] [-NlpSource <zip|夾>];需 pwsh 7
function global:via-superhtml { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; $t = @($args | Where-Object { $_ -notmatch "^-" }); $o = @($args | Where-Object { $_ -match "^-" }); if ($t.Count -gt 0) { & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-SuperHtmlParser-v*.ps1") -Targets $t @o } else { & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-SuperHtmlParser-v*.ps1") @o } }
# 批345:橋塊掃描/注入(ACCEL-BRIDGE 全樹/NET-BRIDGE VDF;預設 dry-run;--apply 才寫;排除冊=獨立工具不可動/凍結群/收容原件/退役);via-bridge-sweep [--net] [--accel] [--root <rel>] [--apply]
function global:via-bridge-sweep { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL124_BridgeSweeper_v*.py") @args }
# 批342:六流程 Zero-Hydra 編排(Invoke-VIA-SixStreams 尾版;九流分離子進程/獨立 log/硬逾時/文字進度條;PS-ACCEL;缺件=誠實 SKIP;tally 逐字取各工具 [計] 行);via-six [-GoToken GO_v1] [-NoOpen] [-StreamTimeoutS 900];需 pwsh 7
# 批354:via-six 正主=CGC_MDL127_SixStreams(py;九子行程並行;A01–A20 加速器燈;dry-run 預設;--go 只放行 S1);via-six --ps=退 Invoke-VIA-SixStreams ps1 後備
function global:via-six { if ($args -contains "--ps") { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-SixStreams-v*.ps1") @($args | Where-Object { $_ -ne "--ps" }) } else { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL127_SixStreams_v*.py") run @args } }
# 批354:系統結構總冊(MDL128;七域+治理核;--probe --days 2 兩日試鏈)/生命週期 RACI(MDL129;via-loop=≤25 行 digest)/UI 橋接整合台(MDL130;spec+template→VIA_UI_Consolidated;VHUIRE 品質閘)
function global:via-charter { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL128_SystemCharter_v*.py") $(if ($args) { $args } else { "--open" }) }
function global:via-loop { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL129_LifecycleRACI_v*.py") $(if ($args) { $args } else { "digest" }) }
function global:via-ui { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL130_UIBridge_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批316:族群分類一鍵管線(補料→ENG070 自測+run→ENG071 自測+run→開頁;pwsh 缺退 powershell)
function global:via-pipeline { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-GroupPipeline-v*.ps1") @args }

# 批381:環境治理統一引擎(MDL135):①全景式分析 base+via_core*+via_*/paddle*/camelot*(平行探針硬逾時不卡斷)②uv pip check 毫秒快篩(退 pip)③base 該有冊(Baseline 冊:工具鏈+引擎核心+LOW)+相依閉包=該有;閉包外=拉出候選 ④衝突要求者家族整包路由(via_core 白名單→家族 target_env(如 OCR→paddle_312 contrib 錨)→purpose hints→5D→黑環境)⑤H1–H6 九頭龍分流:Parallel-Fixable 並行/Sequence-Dependent 拓撲序 ⑥三輪 R1/R2/R3 ⑦uv pip compile 多輪沙盒模擬(同意閘)⑧apply --approve 只跑 GREEN 非破壞段;base 移除 --approve-remove 且目標境 VERIFY 綠後 ⑨LKGC 晉升律+rollback(LKGC lock 逐境 sync;無=原本規劃重建)⑩logs/env_governance.log JSONL+四分區矩陣;批382 +rename 命名律(非 via_ 境換名重建:uv venv 同 Python+lock sync+check;--approve-remove 退役舊境)+base 共用冊/功能件家族(docs/html_parse/data_fetch/nlp/dev_tools/plot_ui→既有 via_ 境)+專屬境覆寫;via-envgov [run|panorama|plan|apply|lkgc|rollback|rename|matrix|digest] [--offline] [--approve] [--approve-remove] [--only S02,S03] [--env-root P] [--base-python EXE]
function global:via-envgov { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL135_EnvGovernance_v*.py") $(if ($args) { $args } else { @("run", "--offline") }) }
# 批381:單一 PowerShell 一貼即用(Invoke-VIA-EnvGovernance 尾版):①20 加速器點亮 ②全景+計畫(唯讀)③-Approve 執行 GREEN 段(-ApproveRemove 破壞段)④矩陣落檔零跳出;-Online 開同意閘;-Background 背景 Job 不阻塞(-Watch 直播 log);-Open 只走瀏覽器 exe
# 批609:`Sync-VIA-Bootstrap` 只是個檔,操作員直接打它當然打不通——治理件全家都有短令,只有它沒有。
#   via-sync        = 同步解卡(fetch → 備份+stash → ff-only → 印尾版與下一步)
#   via-sync -Onboard [-Commit] [-Push] = 上船母資料夾(預設只清點)
#   固定檔名 + glob 取尾版:升版不會再變成「你那一版沒有那個檔」(L85)。
# 批612 撞名修正(工作站實錄:我叫他打 via-sync,跑到的是別人的):
#   `bin\via-sync.ps1` **早就存在**,它做的是
#       git fetch origin / git merge origin/claude/via-system-followup-tz7k9t / git push origin main
#   ——寫死另一條分支 + **推 main**。我批609 用同一個名字登了新函式,
#   於是同一句 `via-sync` 在不同殼、不同 PATH 解析到不同東西。
#   **裁定哪一支是正本是操作員的事(LL90)**,所以這裡不搶名:
#   via-sync 改成**攤開兩支、要求指名**的守門函式,零動作。
#   新的同步解卡短令叫 `via-presync`(批612 量過:全樹 285 個短令名裡沒有這個名字)。
function global:via-sync {
    Write-Host "  [停] 'via-sync' 這個名字在本倉有兩個獨立實作,我不替你挑(LL90)。" -ForegroundColor Yellow
    $old = Join-Path $VIA "bin\via-sync.ps1"
    $new = Get-VIANewest "$VIA\launchers" "Sync-VIA-Bootstrap-v*.ps1"
    if (Test-Path $old) {
        Write-Host "   ① 舊件 bin\via-sync.ps1 —— fetch + merge **寫死分支** + **git push origin main**" -ForegroundColor Red
        Write-Host "      真要跑:pwsh -NoProfile -File `"$old`"" -ForegroundColor DarkGray
    }
    if ($new) {
        Write-Host "   ② 新件 $(Split-Path $new -Leaf) —— fetch → 整包備份 + stash(只收追蹤檔)→ **只做 ff-only**,不推不碰 main" -ForegroundColor Green
        Write-Host "      要這一支請打:via-presync" -ForegroundColor Green
    }
}

# 批613:再生物還原閘(CGC_MDL167)。三次卡死同一個病根——跑完之後沒人把引擎
#   自己長出來的東西放回去,下一次 pull 就被它擋住(批605/606/612)。
#   **預設零動作**:via-regen 只攤開分類;要還原是 via-regen --apply(你的手)。
#   對不上樣式的一律判「不明」**不還原**——引擎寫到原始碼和你自己改的長得一樣,只有你分得出來。
#   取名前照 L88 掃過全樹 286 個短令名:via-regen 沒有被佔用。
function global:via-regen { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL167_RegenRevert_v*.py") @args }

# 批622:VRN 邏輯架構索引冊。無動詞=守門(冊上指標還是不是樹上尾版)· build=重建 · --selftest=七檢
#   登錄的理由不是「有個 .cmd 就好」:MDL157 檢「貼給操作員的每一個 via-* 都要解析得到真指令」
#   當場抓到 docs 裡的 via-vrnbook 是幽靈令——**我要他打的東西,必須是他打得動的**(L89)。
function global:via-vrnbook { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "via_vrn_logic_book_v*.py") @args }
# 批664(操作員逐次許可 L70:「准改 Register 加 via-finlex」):
#   via-finlex=財務字庫收割引擎(vrn_finlex 尾版)。批663 量到它**跑了這麼久都沒有短令**,
#   工作站只能打全路徑——做好的東西站在系統外面,跟沒做一樣(批647 同律)。
#   無參數=印用法;--build 收割落六冊;--ask <詞> 跨冊查;--all 全覽頁;
#   --reconcile 正本↔冊對帳(批663;誠實 rc 0 GREEN / 4 GATED / 1 RED);--selftest 廿三檢。
#   走 VRN 家族境 python(引擎住在 functional modules\VRN)。
function global:via-finlex {
    $a = @(ConvertTo-VIACleanArgs $args)
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "vrn_finlex_v*.py"
    if (-not $eng) {
        Write-Host "  [via-finlex] FAIL:vrn_finlex_v*.py 缺" -ForegroundColor Red
        $global:LASTEXITCODE = 2; return
    }
    Invoke-VIAPython -Python (Get-VIAEnvPython "vrn") $eng @a
}
Set-Alias -Name 財務字庫 -Value via-finlex -Scope Global -Force
# 批664:via-state=VIA 六域現況矩陣(CGC_MDL168)。ENV/LIBS/SSOT/TOOLS/VDF/VRN 六域,
#   逐列誠實態 + **出處** + **年齡**(一個數字沒有年齡會誤導,LL304)。
#   無參數=主控台矩陣(rich;缺 rich 自動降級純文字並講出來);html=落 rich 直出 HTML
#   (零 CDN 零外連,file:// 直開);--json <路徑>=現況紀錄另存;--selftest 十六檢。
#   每跑一次自動落 STATE_<時間戳>.json(歷史)+ STATE_latest.json(現況)+ STATE_LEDGER.tsv(台帳)。
#   **家族境的格在容器是 GATED 不是紅**——那是缺料不是壞掉,工作站才量得到真答案。
function global:via-state {
    $a = @(ConvertTo-VIACleanArgs $args)
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL169_VIAStateMatrix_v*.py") @a
}
Set-Alias -Name 現況矩陣 -Value via-state -Scope Global -Force
# 批667(操作員令「VDF 是獨立引擎…邏輯·因子·參數·引擎串連一下,給我一個 PS 指令啟動他們,
#   自 2023-07-01 開始的資料,邊測邊修直到成功,跳出 HTML MATRIX SUMMARY BY RICH」
#   +「要加入我指令的加速器及網路工具」):
#   via-vdfchain=VDF 獨立鏈串連器(CGC_MDL170)。十站:
#     0a 加速器掛載(VIA_SuperAccel_Module)· 0b 網路工具掛載(SUP_MDL740→AegisNexus 正典)
#     0c VDF 獨立性(逐支量,收容件路徑不算依賴)
#     1 參數(ENG053)· 2 邏輯(ENG073)· 3a/3b 因子(ENG061/062)
#     4a/4b/4c 引擎(ENG090 涵蓋閘/ENG089 增量閘/ENG091 稽核閘)
#   **一句到底**:`via-vdfchain run` = 跑七站 + 落 rich HTML MATRIX + 跳出頁。
#   預設起始日 2023-07-01(--since YYYY-MM-DD 可覆寫)。
#   無參數=plan(只攤開零動作);--resume 只重跑上回沒過的站(邊測邊修直到成功)。
#   **同意閘永不代設**:要觸網的站沒開閘一律 GATED(缺料不是壞掉),
#   你自己在視窗打 $env:VIA_NET_CONSENT='YES' 再 `via-vdfchain run --resume`。
#   走 VDF 家族境 python。誠實 rc:0 GREEN · 1 RED · 2 NODATA · 3 ABSENT · 4 GATED。
function global:via-vdfchain {
    # LL284:ConvertTo-VIACleanArgs 回陣列,單元素時 PowerShell 會拆成字串,**必須包 @()**。
    $a = @(ConvertTo-VIACleanArgs $args)
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL170_VDFChainRunner_v*.py"
    if (-not $eng) {
        Write-Host "  [via-vdfchain] FAIL:CGC_MDL170_VDFChainRunner_v*.py 缺" -ForegroundColor Red
        $global:LASTEXITCODE = 2; return
    }
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") $eng @a
}
Set-Alias -Name VDF鏈 -Value via-vdfchain -Scope Global -Force
# 批670(操作員令「PS 指令加入全景式分析 · 錯誤識別 · 可同時處理/依序處理 ·
#   不可傷害系統指令 · 產生九頭龍風險 · 一次同時解決一批問題」):
#   via-panoplan=全景式分析 + 批次修復規劃器(CGC_MDL171)。**只規劃不動手。**
#   ① 錯誤識別四類:REAL_GAP 真缺 / RULER 尺的錯 / NEED_DATA 缺料 / GATED 等閘
#      ——只有 REAL_GAP 進修復波;把後三類排進波,人就會去動不該動的東西。
#   ② 分波:同一波內目標檔案**互不相交**才算可並行;相交或有前置依賴的排後面。
#   ③ 九頭龍風險件與禁動詞件(Stop-Process/Remove-Item/conda remove/pip uninstall/
#      force push/--approve-remove/改 .ps1)**一律不進波**——前者要你看過,後者不該做。
#   ④ 預設零動作:它不執行任何修復,只印「誰先誰後、哪些可以一起」。
#   判準向 CGC_MDL124 橋掃器**整支取用**(連雜湊冊凍結夾那段分支),不自備第二份。
#   無參數=計畫表;html=落 rich HTML(零 CDN 零外連);--selftest 廿一檢。
#   誠實 rc:0 無事 · 1 有真缺 · 2 只有缺料 · 4 只有等閘 · 5 只有尺的錯。
function global:via-panoplan {
    $a = @(ConvertTo-VIACleanArgs $args)
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL171_PanoramaBatchPlanner_v*.py"
    if (-not $eng) {
        Write-Host "  [via-panoplan] FAIL:CGC_MDL171_PanoramaBatchPlanner_v*.py 缺" -ForegroundColor Red
        $global:LASTEXITCODE = 2; return
    }
    Invoke-VIAPython $eng @a
}
Set-Alias -Name 全景計畫 -Value via-panoplan -Scope Global -Force
# 批671(操作員令「將 VRN 實測完畢」):
#   via-vrnchain=VRN 六層鏈實測器(CGC_MDL172)。**鏈表不寫死**——
#   直接讀批665 已覆核的六層冊 VIA_VRN_LogicArchitecture_SSOT_v0100.json:
#     L0_輸入識別 4 · L1_擷取 15 · L2_結構與知識 13 · L3_驗證 4 · L4_產出 5 · L5_儲存 3 = 44
#   冊改了鏈跟著改,不必回來改這支(L30 一個出處;手寫第二份鏈表就是第二顆頭)。
#   **層間依序、層內並行**:後一層吃前一層的產出,同層節點彼此不相依——
#   這不是效能選擇,是資料流的形狀(也正好回答批670 的「哪些可以一起」)。
#   第 0 站沿用批667 兩件:加速器 VIA_SuperAccel_Module · 網路 SUP_MDL740→AegisNexus 正典。
#   **一句到底**:`via-vrnchain run` = 逐層跑 + 落 rich HTML MATRIX + 跳出頁。
#   頁上同時有「引擎鏈」與「實際數據驗證」兩張矩陣 + 逐列舉證,三顆鍵(MD/JSON/複製)零外連;
#   MD 由引擎 to_markdown() 產一份給頁,**JS 不自己拼第二份**(L30)。
#   run --fast 每節點逾時 60s;run --only L2 只跑某層;run --resume 只補上回沒過的。
#   逾時=NODATA 不是 RED(沒跑完沒有結論,批616 律);同意閘沒開=GATED 不是壞掉。
#   走 VRN 家族境 python。誠實 rc:0 GREEN · 1 RED · 2 NODATA · 3 ABSENT · 4 GATED。
function global:via-vrnchain {
    # LL284:ConvertTo-VIACleanArgs 回陣列,單元素時 PowerShell 會拆成字串,**必須包 @()**。
    $a = @(ConvertTo-VIACleanArgs $args)
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL172_VRNChainRunner_v*.py"
    if (-not $eng) {
        Write-Host "  [via-vrnchain] FAIL:CGC_MDL172_VRNChainRunner_v*.py 缺" -ForegroundColor Red
        $global:LASTEXITCODE = 2; return
    }
    Invoke-VIAPython -Python (Get-VIAEnvPython "vrn") $eng @a
}
Set-Alias -Name VRN鏈 -Value via-vrnchain -Scope Global -Force
# 批672(操作員令「以後跑完都要生成矩陣式報告 BY RICH,字小,優化矩陣排版規格」):
#   via-matrixspec=矩陣式報告排版規格(CGC_MDL173)。**它是排版,不是引擎**——
#   不產生任何新資料、不判任何燈、不碰任何庫。
#   一份規格,四支引擎共用(MDL169/170/171/172);操作員要改字級,只要改這裡一個數字。
#   無參數=印規格(可貼給操作員對);demo=落一張示範頁(看得到字級與密度);
#   --selftest 二十檢(含負向:改 SPEC 字級頁上要跟著變、塞一條真外連零外連檢要敗)。
#   誠實 rc:0 GREEN · 1 RED · 2 NODATA(rich 缺席=缺料不是壞掉,**不代裝套件**)。
function global:via-matrixspec {
    $a = @(ConvertTo-VIACleanArgs $args)
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL173_MatrixReportSpec_v*.py"
    if (-not $eng) {
        Write-Host "  [via-matrixspec] FAIL:CGC_MDL173_MatrixReportSpec_v*.py 缺" -ForegroundColor Red
        $global:LASTEXITCODE = 2; return
    }
    Invoke-VIAPython $eng @a
}
Set-Alias -Name 矩陣規格 -Value via-matrixspec -Scope Global -Force

# 批625 操作員令「整合入一個 PS 指令,25 加速器,動態進度條,測試修正 VRN 直到成功」。
#   輪迴律:**下一輪一定要跟這一輪不一樣**,找不到可調整的差異就誠實停——
#   把同一句跑三次不叫修正(批624 LL205)。
function global:via-vrnaudit {
    $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
    $f = Get-VIANewest "$VIA\launchers" "Invoke-VIA-VRNAudit-v*.ps1"
    if (-not $f) { Write-Host "  [FAIL] 找不到 launchers\Invoke-VIA-VRNAudit-v*.ps1" -ForegroundColor Red; return }
    & $ps -NoProfile -ExecutionPolicy Bypass -File $f @args
}
Set-Alias -Name VRN實測 -Value via-vrnaudit -Scope Global -Force
Set-Alias -Name VRN冊 -Value via-vrnbook -Scope Global -Force

# 批612:同步解卡的正名(via-sync 撞名,不再用它)
function global:via-presync {
    $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
    $f = Get-VIANewest "$VIA\launchers" "Sync-VIA-Bootstrap-v*.ps1"
    if (-not $f) { Write-Host "  [FAIL] 找不到 launchers\Sync-VIA-Bootstrap-v*.ps1" -ForegroundColor Red }
    else { & $ps -NoProfile -ExecutionPolicy Bypass -File $f @args }
}

# 批609:ALL-IN-ONE 也配一支短令(同樣 glob 取尾版,不寫死版號)
function global:via-allinone {
    $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
    $f = Get-VIANewest "$VIA\launchers" "Invoke-VIA-AllInOne-v*.ps1"
    if (-not $f) { Write-Host "  [FAIL] 找不到 launchers\Invoke-VIA-AllInOne-v*.ps1" -ForegroundColor Red; return }
    & $ps -NoProfile -ExecutionPolicy Bypass -File $f @args
}

# 批612:本冊有名字定義兩次(後者靜默生效)。**不替操作員裁定哪一個是正本**,只講出來。
#   via-panorama(第 442 行 / 第 1018 行)· via-ssot(第 166 行 / 第 825 行)
#   要哪一個是正本,請你裁;裁完我再把另一支退役。查:via-cmdrun collide
function global:via-envgov-auto { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-EnvGovernance-v*.ps1") @args }

# 批495 操作員令「透過 envmanager 安全地導入全部工具,基於目前環境衝突問題修復後,如環境工具管理所定」→ MDL135 v0101 tools 動詞
#   via-envtools [-Apply] [-Approve] [-Env via_vrn_312] [--env-root P] ;讀工具冊 VIA_ToolRoster_SSOT_v*.json,逐境探針→修復/安裝/外部/驗證
#   plan 唯讀寫 VIA_Reports\env_governance\TOOLS_PLAN_latest.json/.ps1;-Apply -Approve 才裝,且要 $env:VIA_NET_CONSENT='YES'(不代設)
function global:via-envtools {
    $a = @("tools")
    $i = 0
    while ($i -lt $args.Count) {
        $x = "" + $args[$i]
        if ($x -eq "-Apply") { $a += "--apply" }
        elseif ($x -eq "-Approve") { $a += "--approve" }
        elseif ($x -eq "-Env" -and $i + 1 -lt $args.Count) { $a += @("--tool-env", ("" + $args[$i + 1])); $i++ }
        else { $a += $x }
        $i++
    }
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL135_EnvGovernance_v*.py") @a
}
Set-Alias -Name 工具導入 -Value via-envtools -Scope Global -Force

# 批508 操作員令「環境安裝出了問題可以先還原原本前次環境然後把所有工具順序安裝上 中高風險一律單獨隔離」→ MDL135 v0107 recover 動詞(律 L24 環境復原律)
#   via-envrecover [-Execute] [-Approve] [-ApproveRemove] [-Baseline] [-To LKGC_x.json] [-Env via_x] [--env-root P];plan 唯讀寫 VIA_Reports\env_governance\RECOVER_latest.json/.ps1
#   ①還原前次(LKGC lock 逐境;無則 Baseline 原本規劃;sync 破壞段只在 -ApproveRemove)②順序裝全部工具(core→LOW 家族→MEDIUM 隔離→HIGH 隔離→外部→驗證)③_M/_H 一律同名獨立境不借 alt
#   -Execute -Approve 才跑,且要 $env:VIA_NET_CONSENT='YES'(不代設);① 不受 L19 擋(LKGC 本身曾 GREEN),② 新裝段過 L19(via-rungate GREEN 24h 內)否則 RESTORED_BLOCKED_UNITEST 誠實停
function global:via-envrecover {
    $a = @("recover")
    $i = 0
    while ($i -lt $args.Count) {
        $x = "" + $args[$i]
        if ($x -eq "-Execute") { $a += "--execute" }
        elseif ($x -eq "-Approve") { $a += "--approve" }
        elseif ($x -eq "-ApproveRemove") { $a += "--approve-remove" }
        elseif ($x -eq "-Baseline") { $a += "--baseline" }
        elseif ($x -eq "-To" -and $i + 1 -lt $args.Count) { $a += @("--to", ("" + $args[$i + 1])); $i++ }
        elseif ($x -eq "-Env" -and $i + 1 -lt $args.Count) { $a += @("--tool-env", ("" + $args[$i + 1])); $i++ }
        else { $a += $x }
        $i++
    }
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL135_EnvGovernance_v*.py") @a
}
Set-Alias -Name 環境復原 -Value via-envrecover -Scope Global -Force

# 批511 併線:並行線(批508 panorama-v0103)的全景修復啟動器 launchers\Invoke-VIA-Panorama-v*.ps1(pwsh 7;-Months 2 -StationTimeout 600 -FetchTimeout 7200 -BatchSize 20 [-Fetch] [-ReadOnly];落 VIA_Reports\panorama)
function global:via-panorama { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest "$VIA\launchers" "Invoke-VIA-Panorama-v*.ps1") @args }
Set-Alias -Name 全景修復 -Value via-panorama -Scope Global -Force

# 批513 操作員令「未來所有引擎會因為不同需求彈性調配嫁接,interface 合約自適應式 connect sync 功能要強大完善」→ MDL054 v0102 綁定合約層(L30:在冊的擁有者上加,不另起)
#   via-iface                         舊:全境 AST 合約掃描+自動編號+漂移(寫 VIA_Interface_Contract_Registry);-Dry 零寫入
#   via-iface sync [-Apply]           主控台冊(id→引擎 glob/verb/params)× 尾版引擎 AST 旗標:VERB_DRIFT/PARAM_DRIFT/ENGINE_ABSENT/VERSION_BUMP/未暴露;-Apply 只增 contract
#   via-iface connect -Need a,b [-Family vdf]   嫁接候選(只列 argv);via-iface graft -Item ID -Engine GLOB [-Dir D] [-Apply]   換引擎前驗相容(只增候選);via-iface status
function global:via-iface {
    $a = @()
    $i = 0
    while ($i -lt $args.Count) {
        $x = "" + $args[$i]
        if ($x -eq "-Dry") { $a += "--dry" }
        elseif ($x -eq "-Apply") { $a += "--apply" }
        elseif ($x -eq "-SelfTest") { $a += "--selftest" }
        elseif ($x -eq "-Need" -and $i + 1 -lt $args.Count) { $a += @("--need", ((@($args[$i + 1]) | ForEach-Object { "" + $_ }) -join ",")); $i++ }   # 批514:PowerShell 把 a,b 拆成陣列;以逗號合回(引擎端 v0103 亦寬收空白)
        elseif ($x -eq "-Family" -and $i + 1 -lt $args.Count) { $a += @("--family", ("" + $args[$i + 1])); $i++ }
        elseif ($x -eq "-Item" -and $i + 1 -lt $args.Count) { $a += @("--item", ("" + $args[$i + 1])); $i++ }
        elseif ($x -eq "-Engine" -and $i + 1 -lt $args.Count) { $a += @("--engine", ("" + $args[$i + 1])); $i++ }
        elseif ($x -eq "-Dir" -and $i + 1 -lt $args.Count) { $a += @("--dir", ("" + $args[$i + 1])); $i++ }
        else { $a += $x }
        $i++
    }
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL054_IfaceContract_v*.py") @a
}
Set-Alias -Name 合約 -Value via-iface -Scope Global -Force

# 批514 操作員令「將中央管理系統不足的部分補上」→ 中央治理家族(VIA-SYS-MGR-001 主控台 · VIA-GOV-ENG-001 詞彙引擎 · VIA-SYS-MGR-003 下行控制 · VIA-SYS-ENG-003 檔案優先序 · 同名整併 ps1)
#   正位 supportive modules\VIA_Central_Governance\VIA_CentralGovernanceFamily_b514\(原名零觸碰;MANIFEST_b514.json md5 冊);擁有者=CGC_MDL150(L30:啟動/工作夾/閘只寫一處);工作夾 VIA_Reports\central_governance\
#   via-cgfamily [status|plan]        五成員最新快照 → FAMILY_latest.json(VCGC 十一段);plan=一貼即用
#   via-cgconsole [--probe] [--commit] [--root R]   主控台複驗 dry-run(快照 <root>\output\SYS;--probe 動態載入模組頂層/--commit 發 URN 台帳=你的手)
#   via-cgengine [引擎旗標…]           預設 --selftest;--seed/--observe X/--normalize X 皆 dry-run;--commit=你的手
#   via-cgrouter [--root R] [--ocr]   檔案優先序 L0/L1 唯讀掃描 → central_governance\priority
#   via-cgdownward [--commit --token T] [--strict-chain]   下行控制 dry-run;變更類能力要 --commit --token(你的手)
#   via-samename [--commit --token T] [--diverged] [--root R]   同名整併只報告(pwsh 7);-Commit 只在權杖對上
function global:via-cgfamily { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL150_CentralGovernanceFamily_v*.py") $(if ($args) { $args } else { @("status") }) }
function global:via-cgconsole { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL150_CentralGovernanceFamily_v*.py") "console" @args }
function global:via-cgengine { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL150_CentralGovernanceFamily_v*.py") "engine" @args }
function global:via-cgrouter { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL150_CentralGovernanceFamily_v*.py") "router" @args }
function global:via-cgdownward { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL150_CentralGovernanceFamily_v*.py") "downward" @args }
function global:via-samename { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL150_CentralGovernanceFamily_v*.py") "samename" @args }
Set-Alias -Name 中央治理家族 -Value via-cgfamily -Scope Global -Force
Set-Alias -Name 中央主控台 -Value via-cgconsole -Scope Global -Force
Set-Alias -Name 詞彙引擎 -Value via-cgengine -Scope Global -Force
Set-Alias -Name 優先路由 -Value via-cgrouter -Scope Global -Force
Set-Alias -Name 下行控制 -Value via-cgdownward -Scope Global -Force
Set-Alias -Name 同名整併 -Value via-samename -Scope Global -Force

# 批515 操作員令「VDF 擷取五個額外資料試跑即可」→ 五額外=冊上核心台股日交易/籌碼之外的五組擷取:tw_revenue_codes(月營收 ENG063)· fin_statements(三大報表 ENG082)·
#   etf_holdings_daily(主動 ETF 持股 ENG078)· macro_fred(FRED 宏觀 ENG074)· global_universe(國際 11 類 ENG066);走匯流排 matrix --apply-family vdf --ids(寫庫動詞明點)--profile run;
#   觸網=你的手(先 $env:VIA_NET_CONSENT='YES';批512 令「要用的閘就打開」);-Timeout 秒(預設 900);-Ids 可換清單;-Test 只跑有界 selftest 不觸網
function global:via-vdf-extra5 {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL148_EngineBus_v*.py"
    if (-not $eng) { Write-Host "  [via-vdf-extra5] FAIL:CGC_MDL148_EngineBus_v*.py 缺" -ForegroundColor Red; return }
    $ids = "tw_revenue_codes,fin_statements,etf_holdings_daily,macro_fred,global_universe"; $tmo = 900; $profile = "run"
    $i = 0
    while ($i -lt $args.Count) {
        $x = "" + $args[$i]
        if ($x -eq "-Ids" -and $i + 1 -lt $args.Count) { $ids = ((@($args[$i + 1]) | ForEach-Object { "" + $_ }) -join ","); $i++ }
        elseif ($x -eq "-Timeout" -and $i + 1 -lt $args.Count) { $tmo = [int]$args[$i + 1]; $i++ }
        elseif ($x -eq "-Test") { $profile = "test" }
        $i++
    }
    if ($profile -eq "run" -and -not $env:VIA_NET_CONSENT) { Write-Host "  [via-vdf-extra5] 同意閘未開(VIA_NET_CONSENT 空):真抓要你的手 `$env:VIA_NET_CONSENT='YES';現在只跑 -Test(有界 selftest,零網路)" -ForegroundColor Yellow; $profile = "test" }
    Write-Host ("=== VDF 五額外資料試跑 · " + $ids + " · profile " + $profile + " · timeout " + $tmo + "s(落 VIA_Reports\engine_bus;矩陣頁)===") -ForegroundColor Cyan
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") $eng matrix --apply-family vdf --ids $ids --profile $profile --timeout "$tmo" --html
}
Set-Alias -Name 五額外 -Value via-vdf-extra5 -Scope Global -Force
# 批515 操作員令「VETF 改名為 VATETF;直接抓 VDF 擷取的資料庫來用,他是應用端;VDF 基金只抓主動式台股 ETF 其他基金不抓」→ 同一函式雙名(只增不減);VATETF=應用端,零自抓
Set-Alias -Name via-vatetf -Value via-vetf -Scope Global -Force
Set-Alias -Name 主動ETF應用 -Value via-vetf -Scope Global -Force

# 批516 操作員令「除錯成功後才 Veritas Taiwan Monthly Revenue Analysis VTMRA · TA-LIB 確認測試無誤」
#   via-vtmra [test|status] [--timeout 600] [--json]   VTMRA 家族測試閘(CGC_MDL152;家族境 vdf 真跑七成員自測;零網路;落 VIA_Reports\vtmra)
function global:via-vtmra { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL152_VtmraGate_v*.py") $(if ($args) { $args } else { @("test") }) }
# ── 批523:via-quantguard —— QuantGuard ENG086 正主橋(Polars 技術分析/因子/PIT;SuperAccel bridge;Celeritas+Aegis intake mounts;network gate OFF)
function global:via-quantguard { $env:VIA_FAMILY = "vdf"; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG086_QuantGuardOneBridge_v*.py") $(if ($args) { $args } else { @("status") }) }
Set-Alias -Name 量化技術引擎 -Value via-quantguard -Scope Global -Force
Set-Alias -Name 技術指標引擎 -Value via-quantguard -Scope Global -Force
Set-Alias -Name 技術指標 -Value via-quantguard -Scope Global -Force
# ── 批524:via-market-lists —— VDF_ENG087 中央市場清單治理(股票全集/主動ETF/熱門族群去重;離線可驗收;結果檔非GREEN不得假綠)
function global:via-market-lists { $env:VIA_FAMILY = "vdf"; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG087_MarketListGovernance_v*.py") $(if ($args) { $args } else { @("status") }) }
Set-Alias -Name 市場清單驗收 -Value via-market-lists -Scope Global -Force
Set-Alias -Name 台股清單 -Value via-market-lists -Scope Global -Force
# ── 批519:via-workflow —— 工作流重組台(CGC_MDL153;catalog | validate <id> | run <id> [--profile test|run] [--continue] | ui-contract [--apply] | db-summary | page [--publish];零彈窗:頁用 via-open 開)
function global:via-workflow { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL153_WorkflowComposer_v*.py") $(if ($args) { $args } else { @("status") }) }
Set-Alias -Name 工作流 -Value via-workflow -Scope Global -Force
Set-Alias -Name 月營收分析 -Value via-vtmra -Scope Global -Force

# 批383:單一入口(操作員令「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合」):via-entry=母倉唯一入口燈板(GitHub/Mother/Data/Env/PATH/EnvGov/VDF-DB/VAP/Matrix/Console/Grok;零網路;落 VIA_Reports/entry)
# via-entry plan=一貼即用 11 步;via-entry roster=短令冊(母倉∪Grok 撞名冊);--scan 加跑 via-envgov 全景;--open 開矩陣頁(瀏覽器道零跳出);--console 帶起 Grok 網頁主控台(背景)
function global:via-entry { $a = @($args); if ($a.Count -gt 0 -and ($a[0] -in @("plan", "roster", "status", "envpy", "deadends"))) { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") @a; return }
    Set-Location -LiteralPath $VIA; $env:VIA_ROOT = $VIA; $env:PYTHONNOUSERSITE = "1"; $env:PYTHONUTF8 = "1"; if (-not $env:VIA_NET) { $env:VIA_NET = "0" }
    Write-Host ("=== [via-entry] VIA 唯一入口(母倉 " + $VIA + ";Grok 主控台=via-webconsole 子入口;LIVE 預設關 VIA_NET=" + $env:VIA_NET + ";零跳出 VIA_NO_OPEN=" + $env:VIA_NO_OPEN + ")===") -ForegroundColor Cyan
    foreach ($f in @("vdf", "vrn", "vap")) { $p = Get-VIAEnvPython $f; Write-Host ("  [境] " + $f + " → " + $p + $(if ($p -eq "python") { "(base 退路;功能件境未見)" } else { "" })) -ForegroundColor $(if ($p -eq "python") { "Yellow" } else { "Green" }) }
    Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") status
    if ($a -contains "--scan") { Write-Host "--- [via-entry] 環境治理全景(唯讀)---" -ForegroundColor Cyan; via-envgov run --offline }
    if ($a -contains "--open") { via-open 矩陣 }
    if ($a -contains "--console") { via-webconsole --background }
    Write-Host "  [via-entry] 次序:via-entry plan(16 步)· via-envgov · via-envgov apply --approve --only-kind REPAIR_BASE · via-rungate(能跑閘)· via-console --open(輸入主控台)· via-handover --open(接棒台)· via-famui vdf,vrn --open(家族 U/I)· via-vdfdb scan · via-vapone · via-open 矩陣 · via-webconsole" -ForegroundColor Cyan }
# 批383:via-env=環境治理正本(MDL135 via-envgov;Grok 版 39 行樁改名 via-env-grok 留冊);via-grok=Grok 短令冊(load 重載;matrix 開 WPF 右側板)
function global:via-env { via-envgov @args }
function global:via-grok { if ($args -contains "load") { $global:VIAGrokVerbs = @(Import-VIAGrokMatrix) }; if ($args -contains "matrix") { if (Get-Command via-matrix -ErrorAction SilentlyContinue) { via-matrix } else { Write-Host "  [via-grok] via-matrix 未載(收容包缺或 VIA_GROK_MATRIX=0;via-grok load)" -ForegroundColor Yellow }; return }; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") roster }
# 批383:via-webconsole=Grok 網頁主控台(收容包 b383;TanStack/Vite;npm run dev 0.0.0.0:8080):node_modules 缺=須 npm install 觸網→ --install 或 $env:VIA_NET_CONSENT="YES" 同意閘;--background 另窗最小化(關窗即停;不 Stop-Process)
function global:via-webconsole { $dir = "$VIA\supportive modules\references\intake\VIA_GrokConsole_AuroraAcorn_b383"; if (-not (Test-Path -LiteralPath "$dir\package.json")) { Write-Host ("  [via-webconsole] 收容包缺 " + $dir) -ForegroundColor Yellow; return }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Host "  [via-webconsole] 未見 npm(Node 22);裝 Node 後再試;離線總控矩陣頁:via-open 矩陣" -ForegroundColor Yellow; return }
    if (-not (Test-Path -LiteralPath "$dir\node_modules")) { if (($args -contains "--install") -or ($env:VIA_NET_CONSENT -eq "YES")) { Write-Host "  [via-webconsole] npm install(觸網;同意閘已過)…" -ForegroundColor Cyan; Push-Location -LiteralPath $dir; try { npm install --no-audit --no-fund } finally { Pop-Location } } else { Write-Host "  [via-webconsole] node_modules 缺=需 npm install(觸網);同意:via-webconsole --install(或 `$env:VIA_NET_CONSENT='YES')" -ForegroundColor Yellow; return } }
    if (-not (Test-Path -LiteralPath "$dir\node_modules")) { Write-Host "  [via-webconsole] node_modules 仍缺(npm install 失敗?)=誠實停" -ForegroundColor Red; return }
    Write-Host "  [via-webconsole] http://localhost:8080(Grok 主控台;LIVE 預設關 VIA_NET=0;KEY 永不入檔)" -ForegroundColor Green
    if ($args -contains "--background") { Start-Process -FilePath $env:ComSpec -ArgumentList "/k npm run dev" -WorkingDirectory $dir -WindowStyle Minimized; Write-Host "  [via-webconsole] 已於最小化視窗帶起(關該窗即停)" -ForegroundColor Green } else { Push-Location -LiteralPath $dir; try { npm run dev } finally { Pop-Location } } }
# 批383:via-vapone=VAP ONE 單檔整合引擎(VAP_ENG016;圖規 SSOT 40/圖規鎖/批330 資料律/零依賴 SVG+Plotly+Matplotlib 車道;無參數=--selftest;via_vap_312 python 優先=全車道)
function global:via-vapone { $py = Get-VIAEnvPython "vap"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG016_AutoplotOne_v*.py") $(if ($args) { $args } else { "--selftest" }) }
# 批383:via-vdfdb=本機三庫整併入正典 DuckDB(VDF_ENG079;C:\新增資料夾\新增資料夾\VIA_db_part1_prices/part2_chips/part3_rest;COPY_ONLY anti-join 只補缺鍵;檔冊 sha 已入=跳過;ckpt=ENG064 checkpoint 重建=抓過不再抓;need=缺口清單);無參數=scan 唯讀;run --apply 才寫
# 批564:via-consensus=共識融合橋(VDF_ENG088)。無參數=status(誠實四態:0 列與缺來源分得開);plan=唯讀對映計畫(來源缺時不猜);sync --apply=COPY_ONLY 反連結搬列。
function global:via-consensus { $py = Get-VIAEnvPython "vdf"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG088_ConsensusFusionBridge_v*.py") $(if ($args) { $args } else { "status" }) }
Set-Alias -Name 共識橋 -Value via-consensus -Scope Global -Force
# 批568:via-peis=PEIS 能力引擎掛線口(CGC_MDL158)。無參數=status(收容正本在不在+它自己的 69 檢);
#   scan [--family vdf,vrn,vap,cgc,sup] = INTAKE→SCAN→CLUSTER→TEST→LOCK→ANNOTATE→STORE(AUDIT;零重複=誠實 NODATA 不報紅);
#   cards [能力] = 能力卡 capsule(AI 只讀卡,不讀全文原始碼=省 token 的正主);run <能力> [--params JSON] = 快速截取層;report = token 節省帳。
#   **沒有 --apply**:能力表落地與引擎鎖定是操作員的裁定,要落地請直接對收容正本下令。
function global:via-peis { $a = ConvertTo-VIACleanArgs $args; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL161_PEISCapabilityEngine_v*.py") $(if ($a) { $a } else { "status" }) }
Set-Alias -Name 能力庫 -Value via-peis -Scope Global -Force
# 批569:via-vdfinc=增量擷取閘(VDF_ENG089)。操作員令「VDF 自2023年後到最新的增量擷取,不要重複 BATCH FETCHING」。
#   無參數=scan(每張表的水位);plan [--since 2023-01-01] [--until] = **只列缺口**;plan --deep = 逐日反連結(真正的不重抓清單);
#   audit = 哪幾支尾版擷取引擎抓之前沒看庫。零網路 · 零寫庫 · **沒有 --apply**(要真的去抓是你的手)。
function global:via-vdfinc { $a = ConvertTo-VIACleanArgs $args; $py = Get-VIAEnvPython "vdf"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG089_IncrementalFetchGate_v*.py") $(if ($a) { $a } else { "scan" }) }
Set-Alias -Name 增量閘 -Value via-vdfinc -Scope Global -Force
# 批569:via-vrnmatrix=VRN 驗證矩陣(VRN_ENG083)。操作員令「用 C:\測試樣本報告 的檔案實測,驗證過的輸出用矩陣表示」。
#   run --in "<報告夾>" [--db] = 代跑 ENG072→ENG073 後出矩陣;matrix [--db] = 只讀既有庫不重跑。
#   每一格是**擷到且驗過**才 GREEN;驗不過/驗不了=YELLOW(理由分得開);沒擷到=NODATA;欄位不存在=ABSENT。零網路 · 零寫庫 · 零 CDN。
# ── 批640:via-vrnmd = 本文還原一鍵鏈(操作員令「INTEGRATE INTO ONE PS CODE WITH 25 加速器」)──
#   為什麼要有它:工作站實錄兩次打錯——
#     ① `via-py "functional modules/..." run`  ← via-py 第一個參數是**家族**不是腳本
#     ② `via-py vrn "functional modules\..."`   ← 少了母資料夾 VeritasIntelligenceAnalytics
#   兩次都不是引擎壞,是**要人手打路徑就一定會打錯**。路徑由冊解、版號由 Get-VIANewest 解,
#   人只要打一個字。
#
#   加速器:25 加速器走 py 側的 [VIA:ACCEL-BRIDGE] 正典橋(SUP_MDL737),
#   引擎 import 時自動掛。這裡**只確保不被關掉**,不代設任何同意閘
#   (VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 一律不碰——那是操作員的手)。
#
#   動詞:
#     via-vrnmd                 只跑還原(讀既有 sidecar)
#     via-vrnmd --chain         先跑 ENG072 首頁三法再還原(sidecar 會更新)
#     via-vrnmd --apply         還原 + 表格入庫
#     via-vrnmd --selftest      自測
function global:via-vrnmd {
    $a = ConvertTo-VIACleanArgs $args
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG085_MarkdownRestore_v*.py"
    if (-not $eng) {
        Write-Host "  [via-vrnmd] FAIL:VRN_ENG085_MarkdownRestore_v*.py 缺(冊上有令、樹上沒件)" -ForegroundColor Red
        return
    }
    # 加速器只開不關:已經被設成 0 的話尊重操作員,不覆蓋
    if ($null -eq $env:VIA_ACCEL -or $env:VIA_ACCEL -eq "") { $env:VIA_ACCEL = "1" }
    $chain = ($a -contains "--chain")
    $rest = @($a | Where-Object { $_ -ne "--chain" })
    if ($chain) {
        $e72 = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG072_FirstPageText_v*.py"
        if (-not $e72) {
            Write-Host "  [via-vrnmd] --chain 要 VRN_ENG072_FirstPageText_v*.py,但它缺" -ForegroundColor Red
            return
        }
        Write-Host ("  [via-vrnmd] 鏈 1/2 首頁三法 " + (Split-Path $e72 -Leaf)) -ForegroundColor DarkCyan
        Invoke-VIAPython -Family "vrn" $e72 "run"
        if ($LASTEXITCODE -ne 0) {
            Write-Host ("  [via-vrnmd] 鏈 1/2 rc=" + $LASTEXITCODE + " —— **不往下跑**(半條鏈不算跑過 L83)") -ForegroundColor Red
            return
        }
    }
    Write-Host ("  [via-vrnmd] " + $(if ($chain) { "鏈 2/2 " } else { "" }) + "本文還原 " + (Split-Path $eng -Leaf)) -ForegroundColor DarkCyan
    Invoke-VIAPython -Family "vrn" $eng $(if ($rest) { $rest } else { "run" })
}

function global:via-vrnmatrix { $a = ConvertTo-VIACleanArgs $args; $py = Get-VIAEnvPython "vrn"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG083_VerifiedMatrix_v*.py") $(if ($a) { $a } else { "matrix" }) }
Set-Alias -Name 驗證矩陣 -Value via-vrnmatrix -Scope Global -Force
# 批659(操作員逐次許可 L70):via-repairprice=補庫價與上漲空間(VRN_ENG073 repair-price)。
#   零網路 · 零擷取 · 不碰正本報告;**無 --apply 一律乾跑**(乾跑會把前幾筆逐件印出來——
#   批659 就是那幾行明細救的:摘要說「新拿到 37 件」,明細才看得出它們全是同一天的舊價)。
#   無參數=乾跑。加 --apply 才寫庫。--db <路徑> 可指定另一本庫。
function global:via-repairprice {
    # LL284:ConvertTo-VIACleanArgs 回陣列,PowerShell 會把單元素陣列拆成字串,
    #   於是 `--apply` 的 $a[0] 會拿到字元 '-'。**必須包 @()。**
    $a = @(ConvertTo-VIACleanArgs $args)
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG073_ReportStructuredDB_v*.py"
    if (-not $eng) {
        Write-Host "  [via-repairprice] FAIL:VRN_ENG073_ReportStructuredDB_v*.py 缺" -ForegroundColor Red
        $global:LASTEXITCODE = 2; return
    }
    # 動詞與旗標要先在 PowerShell 這邊組成一個陣列再 splat;
    #   寫成 `@("repair-price") + $(...)` 擺在參數位置會被拆成三個參數(不是相加)。
    $argv = @("repair-price") + $a
    Invoke-VIAPython -Python (Get-VIAEnvPython "vrn") $eng @argv
}
Set-Alias -Name 補庫價 -Value via-repairprice -Scope Global -Force
# 批570:via-cmdcard=指令卡與凍結冊(CGC_MDL162)。L65「AI 讀卡,不讀原始碼」;L66「凍結但留鉤子」。
#   cards=一行一指令(名稱·別名·背後引擎·鉤子·一句話)+ token 帳;freeze [--apply --evidence <存證>];verify=凍結後被動過沒有(DRIFT 指名)。
#   **沒有 unfreeze**:解凍是操作員的裁定。
function global:via-cmdcard { $a = ConvertTo-VIACleanArgs $args; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL162_CommandCardFreeze_v*.py") $(if ($a) { $a } else { "cards" }) }
Set-Alias -Name 指令卡 -Value via-cmdcard -Scope Global -Force
# 批570:via-vdfcov=VDF 資料涵蓋閘(VDF_ENG090)。universe=兩張名單欄位齊不齊(缺欄逐欄給補法;要觸網的標 GATED);
#   revenue=月營收涵蓋(停在哪個月);macro=總經×akshare 候選對照(預設全 UNVERIFIED,--probe 才驗且**不代裝**)。零網路零寫無 --apply。
function global:via-vdfcov { $a = ConvertTo-VIACleanArgs $args; $py = Get-VIAEnvPython "vdf"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG090_DataCoverageGate_v*.py") $(if ($a) { $a } else { "universe" }) }
Set-Alias -Name 涵蓋閘 -Value via-vdfcov -Scope Global -Force
# 批570:via-uiunify=U/I 畫面統一閘(CGC_MDL160)。contract=三級契約;scan=逐頁判定;plan=只列不合的並指名該由哪支引擎再生。
#   LAW 違反=RED(零 CDN/零彈窗/charset/viewport/lang)· UNIFY 缺=YELLOW(主題令牌/頁腳/標題)· ADVISORY 永不判紅。**不代改頁**。
function global:via-uiunify { $a = ConvertTo-VIACleanArgs $args; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL160_UIUnifyGate_v*.py") $(if ($a) { $a } else { "scan" }) }
Set-Alias -Name 畫面統一 -Value via-uiunify -Scope Global -Force

# 批647 操作員裁定「VIA_HTML_UI 進 VIA,為可調整統一銜接系統的 TEMPLATE」。
#   via-ui = 正典 TEMPLATE 一鍵開(零 server:三支入口頁 file:// 直開就會動)。
#   **預設就開**——操作員令「本機自動跳出 HTML U/I NO SERVER」;
#   不想跳出就設 VIA_NO_OPEN=1(批366 零跳出閘,本令不繞過它)。
#   --check = 只驗不開(逐檔 sha256 對 manifest 223 筆 + 三支入口頁離線契約機器驗)。
function global:via-ui {
    $a = ConvertTo-VIACleanArgs $args
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL160_UIUnifyGate_v*.py"
    if (-not $eng) { Write-Host "  [via-ui] FAIL:CGC_MDL160_UIUnifyGate_v*.py 缺(冊上有令、樹上沒件)" -ForegroundColor Red; return }
    $check = ($a -contains "--check")
    $rest = @($a | Where-Object { $_ -ne "--check" })
    $argv = @("template") + $rest
    if (-not $check) { $argv += "--open" }
    Invoke-VIAPython $eng $argv
}
Set-Alias -Name 畫面 -Value via-ui -Scope Global -Force
# 批573:via-mastercard=母檔卡(CGC_MDL163)。L65「AI 讀卡,不讀原始碼」推到交接這一層。
#   card=印卡(+token 帳);export=卡落報告夾;export --publish=寫入倉內卡。
#   **絕不寫母檔**:母檔正主是 docs\VIA_Handover_ONEPAGE.md,要更新請在工作站跑 via-vcgc page --publish(LL49)。
function global:via-mastercard { $a = ConvertTo-VIACleanArgs $args; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL163_MasterFileCard_v*.py") $(if ($a) { $a } else { "card" }) }
Set-Alias -Name 母檔卡 -Value via-mastercard -Scope Global -Force
# 批574:via-govaudit=制度健全度稽核(CGC_MDL164)。audit=14 庫+3 機制逐條判;plan=只列不健全的+怎麼補;spec=印藍圖。
#   判準三件缺一不可:冊在 · 有料 · **有活樹上真的有引擎讀它**。零活讀者=ORPHAN(不是紅燈,但它沒在治理任何東西)。
#   另報「單一讀者」(那一支一動就變孤兒)與「多冊並存」(哪本是正本=操作員裁定,LL90)。零網路零寫無 --apply。
function global:via-govaudit { $a = ConvertTo-VIACleanArgs $args; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL164_GovernanceCompletenessAudit_v*.py") $(if ($a) { $a } else { "audit" }) }
Set-Alias -Name 制度稽核 -Value via-govaudit -Scope Global -Force
function global:via-vdfdb { $py = Get-VIAEnvPython "vdf"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG079_LocalDbConsolidate_v*.py") $(if ($args) { $args } else { "scan" }) }
# 批508:via-rungate 無參數=VDF+VRN 各 3 站有界驗收；明帶參數仍完整直通(--all/--family vap/--approve-install 等不丟)。
function global:via-rungate { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL137_RunGate_v*.py") $(if ($args) { $args } else { @("run", "--fast", "--family", "vdf,vrn") }) }
function global:via-py { if ($args.Count -ge 1) { $env:VIA_FAMILY = ("" + $args[0]).ToLower() }; if ($args.Count -lt 2) { Write-Host "  用法:via-py <vdf|vrn|vap|core|ocr|table> <script.py> [args](家族境 python 啟動;境缺=base 退路)" -ForegroundColor Yellow; return }; $py = Get-VIAEnvPython ("" + $args[0]); Write-Host ("  [via-py] " + $args[0] + " → " + $py) -ForegroundColor DarkCyan; Invoke-VIAPython -Python $py @($args | Select-Object -Skip 1) }
# 批386:via-vrn4=研報一題四點文摘+潛在上漲空間(VRN_ENG080;目標價除權息同口徑後向因子鏈;最新 adj close;quote-or-abstain);無參數=run;show <ticker|report_file>;--ticker/--limit
function global:via-vrn4 { $py = Get-VIAEnvPython "vrn"; Invoke-VIAPython -Python $py (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG080_FourPointDigest_v*.py") $(if ($args) { $args } else { "run" }) }
# 批388:via-famui=家族 U/I 再生閘(MDL138):以家族境 python 真跑 VDF/VRN/VAP 頁面產生器→頁新鮮/零 CDN 判準→索引 FAMILY_UI_latest.html;--open 只走 via-open 瀏覽器道;--no-build 只驗頁;via-vdfui/via-vrnui 別名
function global:via-famui { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" -and $_ -notin @("vdf", "vrn", "vap", "all") }); $fam = @($a | Where-Object { $_ -in @("vdf", "vrn", "vap", "all") } | Select-Object -First 1); $fam = if ($fam) { "" + $fam } else { "all" }; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL138_FamilyUI_v*.py") run --family $fam @rest; if ($o) { via-open 家族 } }
function global:via-vdfui { via-famui vdf @args }
function global:via-vrnui { via-famui vrn @args }
# 批390:via-console=輸入主控台(MDL139 左輸入/右矩陣;零 CDN):無參數=build 頁;status [--json];set k=v…(tw-add=2330:TWSE start=<item>:YYYY-MM-DD|latest days=<item>:N macro-cats=Business,Prices fin-period=累計 fin-from=2022 vrn-dir=<夾> vap-code=2330…);argv --item <id> k=v;run --item <id> k=v [--dry];--open=via-open 主控台(樞紐在線時開 http://127.0.0.1:8765/console 才可按啟動;file:// 頁=SNAPSHOT 只看並印等價短令)
function global:via-console { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" }); Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL139_InputConsole_v*.py") @rest; if ($o) { $live = $false; try { $tc = New-Object System.Net.Sockets.TcpClient; $ar = $tc.BeginConnect("127.0.0.1", 8765, $null, $null); $live = $ar.AsyncWaitHandle.WaitOne(400) -and $tc.Connected; $tc.Close() } catch { $live = $false }; if ($live) { via-open LIVE } else { Write-Host "  [via-console] 樞紐 8765 未在線=開快照頁(只看;要按啟動:先 via 帶起樞紐,再 via-console --open 或 via-open LIVE)" -ForegroundColor Yellow; via-open 主控台 } } }
# 批390:via-align=台股每日交易資訊×籌碼 數量對齊與股票清單更新(VDF_ENG081;vdf 境 python):check [--days N](逐日核對 ALIGNED/PARTIAL/MISALIGNED;差集清單)| update [--apply](最新日 價∪籌碼 ∩ 冊 → tw_universe anti-join 只增 + parquet 增量)| status
# 批392:via-handover=接棒狀態台(MDL140):超詳細系統狀態分門別類堆疊矩陣一頁(git/PR/環境治理/能跑閘/家族 U/I/樞紐任務/庫狀況/對齊/本機三庫/VRN 跑況/VAP 產出/日更鏈/候操作員/次步)+ HANDOVER_latest.md(可轉 MD 接棒);無參數=build;status|md;--open=樞紐在線開 LIVE /handover 否則快照頁
function global:via-handover { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" }); Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL140_HandoverConsole_v*.py") @rest; if ($o) { $live = $false; try { $tc = New-Object System.Net.Sockets.TcpClient; $ar = $tc.BeginConnect("127.0.0.1", 8765, $null, $null); $live = $ar.AsyncWaitHandle.WaitOne(400) -and $tc.Connected; $tc.Close() } catch { $live = $false }; if ($live) { via-open 接棒LIVE } else { via-open 接棒 } } }
function global:via-align { Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG081_UniverseAlign_v*.py") $(if ($args) { $args } else { "check" }) }
# 批393:via-bg=背景引擎進程一覽(唯讀;工作站實錄:via-align 撞 DuckDB 單寫者鎖時 [FAIL] 句指路「via-status」,但 via-status 開的是同步頁不是進程表)。
#   Get-CimInstance Win32_Process 篩 python/pwsh/powershell 命令列含 VIA 引擎/boot 鏈/樞紐 → 列 PID/已跑分鐘/引擎+動詞;絕不 Stop-Process(只看;等其跑完再 via-align)。
function global:via-bg {
    $rx = 'VeritasIntelligenceAnalytics|via_boot_update|VDF_ENG|VRN_ENG|VAP_ENG|CGC_MDL|SUP_MDL|VIA_SYSTEM_MANAGER|VIA\.ps1'
    $eng = '((?:VDF|VRN|VAP|CGC|SUP)_(?:ENG|MDL)\d{3}_[A-Za-z0-9]+(?:_v\d{4})?\.py|via_boot_update\.(?:ps1|sh)|VIA\.ps1|VIA_SYSTEM_MANAGER_v\d{4}\.py)'
    $rows = @()
    try {
        Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and ($_.Name -match '^(python|pwsh|powershell)') -and ($_.CommandLine -match $rx) } | ForEach-Object {
            $cl = $_.CommandLine
            $lab = $cl.Substring(0, [Math]::Min(70, $cl.Length))
            if ($cl -match $eng) {
                $m = $Matches[1]
                $tail = @(($cl.Substring($cl.IndexOf($m) + $m.Length)).Trim().Trim('"').Split(' ') | Where-Object { $_ })
                if ($tail.Count -gt 0 -and -not $tail[0].StartsWith('-')) { $lab = "$m $($tail[0])" } else { $lab = $m }
            }
            $min = if ($_.CreationDate) { [int]((Get-Date) - $_.CreationDate).TotalMinutes } else { -1 }
            $rows += [pscustomobject]@{ PID = $_.ProcessId; 分鐘 = $min; 程式 = $_.Name; 引擎 = $lab }
        }
    } catch { Write-Host ("  [via-bg] 無法列進程:" + $_.Exception.Message) -ForegroundColor Yellow; return }
    if ($rows.Count -eq 0) { Write-Host "  [via-bg] 無 VIA 背景引擎進程(DuckDB 單寫者鎖應已釋放;可 via-align check / via-align update --apply)" -ForegroundColor Green; return }
    Write-Host ("  [via-bg] VIA 背景引擎進程 " + $rows.Count + " 個(唯讀一覽;持 DuckDB 單寫者鎖者多為 ENG064 回補/boot 日更鏈;等其跑完再 via-align;絕不 Stop-Process)") -ForegroundColor Cyan
    $rows | Sort-Object 分鐘 -Descending | Format-Table -AutoSize | Out-String -Width 160 | Write-Host
}
# 批394:via-chip=籌碼增量(VDF_ENG056:run [--days N] | --derive | --status);via-price=價格增量(VDF_ENG054 v0101 增量律:依各標的 MAX(date) 只抓缺口;run [--limit N] [--full] | --status);
#   via-tw-backfill=ENG054 docstring 原名別名。同意閘同 via-fred(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT=YES);以 via_vdf_312 python 啟動;撞單寫者鎖=引擎自身庫鎖律誠實停。
function global:via-chip { Set-VIAGateDefaults; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG056_ChipBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-price { Set-VIAGateDefaults; Invoke-VIAPython -Family "vdf" (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG054_TWDailyBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-tw-backfill { via-price @args }
# 批398:via-closeout=收尾閘 MDL141(VRN 驗證收尾 VAL:報告夾每一份 收件→首頁→入庫→財報頁→四點 + TAB2/TAB4 核對態 → DONE|FAIL|PENDING;VAP 產出收尾:逐圖驗 SVG/PNG/HTML/PDF+零 CDN+台帳)
#   [vrn|vap|all] [--run](先經 MDL139 run --item 跑鏈再收尾)[--dir 報告夾] [--json];落 VIA_Reports/closeout/CLOSEOUT_latest.md/.json(接棒台讀);以 via_vrn_312 python 啟動(duckdb 在);--open=以瀏覽器開 MD 所在夾外之 Handover(接棒台含收尾矩陣)。
function global:via-closeout { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" }); Invoke-VIAPython -Family "vrn" (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL141_ClosingGate_v*.py") @rest; if ($o) { via-handover --open } }
# ── 批470:via-vrnin —— Windows 原生 I/O 輸入(批465 造的,但當時**沒進短令冊**)
# 全景分析照出來的第一項:工具造了、梭(via-vrnin.cmd)也有,可是操作員的唯一
# 入口是短令冊,冊裡沒有它就等於**建了叫不到**。造了不接線,和沒造差別很小。
# 三條道都在這一支:零參數=開原生選檔對話框;-Pick Folder=選夾;-Path=直接給。
# 拖曳仍走同夾的 via-vrnin.cmd(檔案總管不把拖曳路徑傳給 .ps1,只傳給 .cmd)。
function global:via-vrnin { $p = Get-VIANewest "$VIA\supportive modules" "VIA_WinIO_InputPicker_v*.ps1"; if (-not $p) { Write-Host "  [via-vrnin] FAIL:VIA_WinIO_InputPicker_v*.ps1 缺(尾版律 glob 找不到)" -ForegroundColor Red; return }; if ($args.Count -eq 0) { & $p -Pick File } else { & $p @args } }
# ── 批471:via-bus —— 引擎調度匯流排 CGC_MDL148(一條匯流排,四家共用)
# 冊只有一本:VIA_InputConsole_Spec_v0100.json(37 項)。本短令只是它的門。
#   via-bus                      目錄(冊 → 尾版 → 在位)
#   via-bus vrn                  只看 vrn 家族
#   via-bus run vrn              真跑 vrn 家族,其餘照樣只解析,產多矩陣 HTML
#   via-bus run vrn,vap          真跑兩族
#   via-bus one vrn_firstpage    只跑點名的那一項(**寫庫動詞只認這條路**)
# 預設不動手:不加 run/one 一律只解析(dry)。調度層的預設值錯一次,
# 代價是在別人的機器上動了不該動的東西。
function global:via-bus {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL148_EngineBus_v*.py"
    if (-not $eng) { Write-Host "  [via-bus] FAIL:CGC_MDL148_EngineBus_v*.py 缺(尾版律 glob 找不到)" -ForegroundColor Red; return }
    $py = Get-VIAEnvPython "vrn"
    $a = @($args)
    if ($a.Count -eq 0) { Invoke-VIAPython -Python $py $eng catalog; return }
    switch ($a[0]) {
        "run" { $f = if ($a.Count -gt 1) { $a[1] } else { "vrn" }
                Invoke-VIAPython -Python $py $eng matrix --apply-family $f --html @($a | Select-Object -Skip 2) }
        "one" { if ($a.Count -lt 2) { Write-Host "  [via-bus] 用法:via-bus one <項id>" -ForegroundColor Yellow; return }
                Invoke-VIAPython -Python $py $eng call --item $a[1] --apply @($a | Select-Object -Skip 2) }
        "census" { Invoke-VIAPython -Python $py $eng census @($a | Select-Object -Skip 1) }
        default { if ($a[0] -in @("vdf", "vrn", "vap")) { Invoke-VIAPython -Python $py $eng catalog --family $a[0] }
                  else { Invoke-VIAPython -Python $py $eng @a } }
    }
}
function global:via-busui { $p = Join-Path $VIA "VIA_Reports\engine_bus\ENGINE_BUS_MATRIX.html"; if (Test-Path -LiteralPath $p) { via-open $p } else { Write-Host "  [via-busui] 頁還沒產(先跑 via-ryg 或 via-bus run vrn,vap)" -ForegroundColor Yellow } }
# ── 批474 B:via-ryg —— **一頁式紅黃綠燈矩陣,跑完自己跳出來**
# 操作員令(B):「一頁式矩陣報告…紅黃綠燈…自動跳出來」。
# 零彈窗律(批378 VIA_NO_OPEN=1)管的是「**沒人要求就別跳**」;
# 這一令是操作員親手打的,**打了就該跳**——兩條律不衝突,分界線是「誰要求的」。
#   via-ryg                VDF+VRN 有界 selftest(不跑全量回補);產五矩陣頁;**自動開**
#   via-ryg vrn            只驗 vrn
#   via-ryg vdf,vrn -Full  明示 production 模式(保留冊上動詞與全部參數；網路/寫庫閘照舊)
#   via-ryg -NoOpen        不開(給自動化鏈路用)
#   via-ryg -DryAll        一支都不真跑(只要那張圖)
#   via-ryg -Timeout 300   逐項逾時秒數(批474 v0108:預設 900;有心跳,畫面不再白)
# 五張矩陣:①家族×狀態 ②引擎目錄 ③調度結果 ④產出契約 ⑤**庫況**
# 矩陣五是批474 新加的,因為前四張回答不了操作員問的 C:
#   **引擎綠不綠,回答不了「庫裡到底有沒有料」**——一支引擎可以完美地跑完,
#   然後把資料寫進一張空表。只報前者就是一種假綠。
# 批488 工作站實錄:`via-ryg -Timeout 300# 先 Ctrl+C…`——註解黏在數字後面,PowerShell 把 300# 給了 -Timeout、把「先」當家族名;
#   包裝一邊丟 InvalidArgument 一邊照跑「真跑 先」。判錯的參數和判錯的燈一樣傷:要嘛擋下來說清楚,要嘛別跑。
function global:ConvertTo-VIACleanArgs {
    # 參數裡出現 # = 有人把註解一起貼進來:截掉 # 之後、丟掉後面所有字,並提醒。回傳乾淨陣列。
    param([object[]]$Raw)
    $out = @(); $hit = $false
    # PowerShell 把 `vrn,vap` 這種逗號寫法當**陣列**傳進來(不是字串);要攤平成逐個 token,
    # 不然 "$t" 會變成 "vrn vap"(空白相連),家族驗證就把合法輸入擋掉。
    $flat = @(); foreach ($t in @($Raw)) { if ($t -is [System.Array]) { foreach ($x in $t) { $flat += $x } } else { $flat += $t } }
    foreach ($t in $flat) {
        if ($null -eq $t) { continue }
        $s = "$t"
        if ($s -match '#') { $hit = $true; $head = $s.Substring(0, $s.IndexOf('#')); if ($head) { $out += $head }; break }
        $out += $s
    }
    if ($hit) { Write-Host ("  [參數] 看起來把註解一起貼進來了(從 # 起截掉);實際採用:" + ($out -join ' ')) -ForegroundColor Yellow }
    # 不用 ,$out:呼叫端再包 @() 會變成「一個元素是陣列」(第一版就這樣,-DryAll/-Timeout 全看不見,真跑了 vrn,vap)
    return $out
}
function global:via-ryg {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL148_EngineBus_v*.py"
    if (-not $eng) { Write-Host "  [via-ryg] FAIL:CGC_MDL148_EngineBus_v*.py 缺(尾版律 glob 找不到)" -ForegroundColor Red; return }
    $a = @(ConvertTo-VIACleanArgs $args)
    $noOpen = ($a -contains "-NoOpen") -or ($a -contains "--no-open")
    $dryAll = ($a -contains "-DryAll") -or ($a -contains "--dry")
    $full = ($a -contains "-Full") -or ($a -contains "--full")
    $tmo = 0; $ti = [array]::IndexOf($a, "-Timeout")
    if ($ti -ge 0) {
        $v = if ($ti + 1 -lt $a.Count) { "$($a[$ti + 1])" } else { "" }
        if (-not [int]::TryParse($v, [ref]$tmo) -or $tmo -le 0) { Write-Host ("  [via-ryg] 誠實停:-Timeout 要正整數秒,收到「{0}」。用法:via-ryg [vdf|vrn|vap[,…]] [-Timeout 300] [-NoOpen] [-DryAll] [-Full]" -f $v) -ForegroundColor Yellow; return }
    }
    # 批488 自犯錯(v0184 起就在):沒給 -Timeout 時 $ti=-1,$ti+1=0 → 第一個位置參數永遠被跳過,
    # `via-ryg vrn` 其實一直跑的是預設 vrn,vap。守衛加上 $ti -ge 0。
    $pos = @(); for ($i = 0; $i -lt $a.Count; $i++) { if ($ti -ge 0 -and ($i -eq $ti -or $i -eq $ti + 1)) { continue }; if ($a[$i] -notmatch '^-') { $pos += $a[$i] } }
    $fam = if ($pos.Count) { ($pos -join ',') } else { "vdf,vrn" }   # 結案閘預設只要求 VDF+VRN；位置參數全收
    $bad = @(($fam -split ',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ -notin @("vdf", "vrn", "vap") })
    if ($bad.Count) { Write-Host ("  [via-ryg] 誠實停:家族只認 vdf / vrn / vap(可逗號合寫),收到「{0}」。用法:via-ryg [vdf|vrn|vap[,…]] [-Timeout 300] [-NoOpen] [-DryAll] [-Full]" -f ($bad -join ',')) -ForegroundColor Yellow; return }
    $profile = if ($full) { "run" } else { "test" }
    $extra = @("--profile", $profile); if ($tmo -gt 0) { $extra += @("--timeout", "$tmo") }
    $py = Get-VIAEnvPython "vrn"
    Write-Host ""
    Write-Host "=== VIA 一頁式紅黃綠燈矩陣(五矩陣;零 CDN)===" -ForegroundColor Cyan
    if ($dryAll) { Write-Host ("  模式 : 全解析(profile={0};一支都不真跑)" -f $profile) }
    elseif ($full) { Write-Host ("  模式 : **明示 Full** production 真跑 {0};寫庫動詞仍須 --ids 明點" -f $fam) -ForegroundColor Yellow }
    else { Write-Host ("  模式 : 有界 selftest 驗收 {0};production 動詞/參數只留契約、不執行" -f $fam) }
    Write-Host   ("  引擎 : {0}" -f (Split-Path -Leaf $eng))
    Write-Host ""
    if ($dryAll) { Invoke-VIAPython -Python $py $eng matrix --html @extra }
    else         { Invoke-VIAPython -Python $py $eng matrix --apply-family $fam --html @extra }
    $rc = $LASTEXITCODE
    $p = Join-Path $VIA "VIA_Reports\engine_bus\ENGINE_BUS_MATRIX.html"
    if (-not (Test-Path -LiteralPath $p)) {
        Write-Host "  [via-ryg] 頁沒產出來(上面應有原因);不假裝成功" -ForegroundColor Red; return }
    if ($noOpen) { Write-Host ("  頁 : {0}(-NoOpen 故不開)" -f $p) -ForegroundColor Cyan }
    else { Write-Host ("  頁 : {0}" -f $p) -ForegroundColor Cyan; via-open $p }
    if ($rc -ne 0) { Write-Host ("  [via-ryg] 調度回 rc={0}=有項目沒過,頁上紅黃格即是" -f $rc) -ForegroundColor Yellow }
    $global:LASTEXITCODE = $rc
}
Set-Alias -Name 紅黃綠 -Value via-ryg -Scope Global -Force
Set-Alias -Name 燈板 -Value via-ryg -Scope Global -Force
# ── 批492 操作員上傳 VIA_VRN_UnifiedReportEngine_v0100(檔名×首頁×財務頁三源互證;parquet SSOT;容器自測 23/23;零寫死路徑;
#   --allow-web-official 預設關=同意閘不碰)。收容 functional modules\VRN\references\intake\VIA_VRN_UnifiedReportEngine_v0100_b492(正本零觸碰;尾版律 glob)
#   via-vrnuni -SelfTest | via-vrnuni --in <報告夾或 pdf> --out <夾> [--official-listings <csv>] [--csv --json --duckdb]
#   未給 --module-dir 時自動指到 functional modules\VRN(借用 FirstPageEngine/ENG072 尾版);未給 --out 時落 VIA_Reports\vrn\unified
function global:via-vrnuni {
    $eng = Get-VIANewest "$VIA\functional modules\VRN\references\intake\VIA_VRN_UnifiedReportEngine_v0100_b492" "VIA_VRN_UnifiedReportEngine_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnuni] FAIL:收容件 VIA_VRN_UnifiedReportEngine_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } else { $_ } })
    if (-not $a) { $a = @("--selftest") }
    if ($a -notcontains "--selftest") {
        if ($a -notcontains "--module-dir") { $a += @("--module-dir", "$VIA\functional modules\VRN") }
        if ($a -notcontains "--out") { $a += @("--out", "$VIA\VIA_Reports\vrn\unified") }
    }
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name 統一報告 -Value via-vrnuni -Scope Global -Force

# ── 批493 操作員律「非 OCR 擷取必用;抓不到才 OCR,從簡單工具組往雙引擎、往 Paddle;成功=資料標示還原、文字修復;
#   非 OCR 兩引擎互核,再與非 OCR 核對;成功的邏輯存中央邏輯庫」→ VRN_ENG082 擷取中央邏輯庫(ENG072 v0117 綁它)
#   via-vrnlogic [status|reset-backends] | -SelfTest ;台帳 VIA_Reports\vrn\extraction_logic\(只增)
#   同檔再跑=命中不重抽(64 份第二次秒級);掃描件 OCR 階梯 simple→dual→paddle 共用預算(預設 150s/件;VIA_OCR_BUDGET_SEC 可調)
function global:via-vrnlogic {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG082_ExtractionLogic_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnlogic] FAIL:VRN_ENG082_ExtractionLogic_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } else { $_ } })
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name 邏輯庫 -Value via-vrnlogic -Scope Global -Force
# ── 批504 操作員上傳 VIA_VRNLogic_AllInOne_v0201 + financial_data_standardization → SUP_MDL748 財務邏輯統轄橋(只掛不搬;正本零觸碰)
#   via-finlogic [status|opinion <科目名>|rating <字>] | -SelfTest ;第二意見只註記不改 canonical(登錄進 SSOT=你定);政策因子隨 via-vrnlogic sync-db 入庫
function global:via-finlogic {
    $eng = Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL748_FinancialLogicHub_v*.py"
    if (-not $eng) { Write-Host "  [via-finlogic] FAIL:SUP_MDL748_FinancialLogicHub_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } else { $_ } })
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name 財務邏輯 -Value via-finlogic -Scope Global -Force
# ── 批505 三大報表擷取引擎 VDF_ENG082(填主控台冊 vdf/fin_statements 缺席;收容件 yfinance 車道走 AegisNexus session;MOPS 探路)
#   via-finstat [run|status|-Dry] [--only 2330,2317] [--limit 5] [--years 5] ;run 前 $env:VIA_NET_CONSENT='YES' + VIA_SCRAPE_CONSENT(你的手;我不代設)
function global:via-finstat {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG082_FinStatements_v*.py"
    if (-not $eng) { Write-Host "  [via-finstat] FAIL:VDF_ENG082_FinStatements_v*.py 缺" -ForegroundColor Red; return }
    Set-VIAGateDefaults
    $a = @($args | ForEach-Object { if ($_ -eq "-Dry") { "--dry" } else { $_ } })
    if (($a -contains "--dry") -and -not ($a -contains "run")) { $a = @("run") + $a }
    if (-not ($a | Where-Object { $_ -in @("run", "status") })) { $a = @("status") + $a }
    Invoke-VIAPython -Family "vdf" $eng @a
}
Set-Alias -Name 三大報表 -Value via-finstat -Scope Global -Force
# ── 批506 Veritas Central Governance Console(CGC_MDL149;律 L20 唯一對接口:政策庫/邏輯庫/因子庫/資料庫/引擎調度/多矩陣/環境工具/註冊表/交接)
#   via-vcgc [status|page|onepage|audit|register-plan|registry-sync|check] [-Publish|-Apply] | -SelfTest ;registry-sync 預設計畫、-Apply 才寫 append-only 元件編號冊；check=VDF+VRN 完整 GREEN 24h 內
function global:via-vcgc {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    if (-not $eng) { Write-Host "  [via-vcgc] FAIL:CGC_MDL149_VeritasCentralGovernanceConsole_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } elseif ($_ -eq "-Publish") { "--publish" } elseif ($_ -eq "-Apply") { "--apply" } else { $_ } })
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython -Family "vrn" $eng @a
    if (($a -contains "page") -and (Test-Path "$VIA\VIA_Reports\vcgc\VIA_UI_CentralGovernanceConsole_v0100.html")) { via-open "$VIA\VIA_Reports\vcgc\VIA_UI_CentralGovernanceConsole_v0100.html" }
}
Set-Alias -Name 中央控管 -Value via-vcgc -Scope Global -Force
# ── 批525:via-functional-acceptance —— CGC_MDL154 單一功能級整合驗收 gate
#   僅執行既有中央/VRN/VDF/VAP selftest 與資料證據核驗；輸出 JSON/HTML；RED 或 PARTIAL_BLOCKED 不得假綠。
function global:via-functional-acceptance {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL154_VIAFunctionalAcceptance_v*.py"
    if (-not $eng) { Write-Host "  [via-functional-acceptance] FAIL:CGC_MDL154_VIAFunctionalAcceptance_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } else { $_ } })
    if (-not $a) { $a = @("run") }
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name VIA功能驗收 -Value via-functional-acceptance -Scope Global -Force
Set-Alias -Name 功能級驗收 -Value via-functional-acceptance -Scope Global -Force
# ── CGC_MDL155:統一 SSOT／Regex 同義字／附件自動編碼受控驗收(中央唯一入口) ──
#   via-ssot [selftest|status|manifest|routes|classify <text>]；不執行收容模組、不開網路。
function global:via-ssot {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL155_VIAUnifiedSSOTAutoCode_v*.py"
    if (-not $eng) { Write-Host "  [via-ssot] FAIL:CGC_MDL155_VIAUnifiedSSOTAutoCode_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args)
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name SSOT治理 -Value via-ssot -Scope Global -Force
# via-firstpage:首頁三法擷取器 ENG072 尾版直呼(-Force 忽略邏輯庫命中整批重抽;-RetryFailed 只重試 FAIL 件;-OcrBudget N 每件 OCR 預算秒;--in 檔/夾可重複)
function global:via-firstpage {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG072_FirstPageText_v*.py"
    if (-not $eng) { Write-Host "  [via-firstpage] FAIL:VRN_ENG072_FirstPageText_v*.py 缺" -ForegroundColor Red; return }
    $a = @()
    $i = 0
    while ($i -lt $args.Count) {
        $x = "" + $args[$i]
        if ($x -eq "-Force") { $a += "--force" }
        elseif ($x -eq "-RetryFailed") { $a += "--retry-failed" }    # 批497:只重試 FAIL 件(忽略 TTL),命中件不重抽
        elseif ($x -eq "-SelfTest") { $a += "--selftest" }
        elseif ($x -eq "-OcrBudget" -and $i + 1 -lt $args.Count) { $a += @("--ocr-budget", ("" + $args[$i + 1])); $i++ }
        else { $a += $x }
        $i++
    }
    if ($a -notcontains "--selftest") { $a = @("run") + $a }
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name 首頁擷取 -Value via-firstpage -Scope Global -Force

# ── 批474 C:via-census —— **庫況**(表在不在 · 有幾列 · 日期跨多久)
# 操作員問「VDF 到底能不能跑」。能跑閘(via-rungate)答不了那題:
# 引擎能跑 ≠ 庫裡有料。這一令唯讀掃全樹 .duckdb,逐表報四態:
#   GREEN 有列且跨度夠 · AMBER 有列但薄 · NODATA 表在列數 0 · ABSENT 碼裡當表用但庫裡沒有
#   批485:via-census -Hygiene = 庫衛生唯讀審計(哨兵列 1900-01-01 數出來 + DELETE 只寫不跑;_repo_ 副本 vs 正庫 MAX 日期);零寫入
function global:via-census {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL148_EngineBus_v*.py"
    if (-not $eng) { Write-Host "  [via-census] FAIL:CGC_MDL148_EngineBus_v*.py 缺" -ForegroundColor Red; return }
    # 批490:預設一本庫一行(省貼回來的 token);-Tables 逐表;-Hygiene 唯讀審計。家=env VIA_DATA_HOME/目錄頁/MDL123 冊
    $a = @($args | ForEach-Object { if ($_ -eq "-Hygiene") { "--hygiene" } elseif ($_ -eq "-Tables") { "--tables" } else { $_ } })
    Invoke-VIAPython -Family "vrn" $eng census @a
}
Set-Alias -Name 庫況 -Value via-census -Scope Global -Force
Set-Alias -Name 庫衛生 -Value via-census -Scope Global -Force
# 批476:via-boot=啟動層實證:每個家族真的起一個子行程,印它看到的(加速器 | 網路件 | via_net 可 import | 同意閘)
function global:via-boot {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL148_EngineBus_v*.py"
    if (-not $eng) { Write-Host "  [via-boot] FAIL:CGC_MDL148_EngineBus_v*.py 缺" -ForegroundColor Red; return }
    Invoke-VIAPython -Family "vrn" $eng boot @args
}
Set-Alias -Name 啟動層 -Value via-boot -Scope Global -Force
# ── 批477:via-vetf —— VETF 持股×Consensus 擴充(封印包 b242 的 adapter;16 檢通過,但從沒登錄)
#   Forward P/E = 最新 adj close ÷ FactSet EPS(EPS 缺/零/負 → fail-closed 留空,不出誤導倍數);
#   預設 candidate 沙盒,只寫 VIA_Reports\vetf_consensus,不碰正庫。
#   via-vetf                       持股=ActiveTWETF.duckdb::holdings_daily · 價=vdf_tw_market.duckdb::tw_prices_adj(自動找庫)
#   via-vetf -Factset <檔> -Yfinance <檔> -AsOf 2026-09-12 -Holdings <庫::表> -Prices <庫::表>
function global:via-vetf { Invoke-VIAPython (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG085_VatetfBridge_v*.py") $(if ($args) { $args } else { @("run") }) }   # 批520:正主橋(對接口合約自適應;adapter 收容件零觸碰;status|run [--asof YYYY-MM-DD] [--no-consensus])
Set-Alias -Name 共識擴充 -Value via-vetf -Scope Global -Force
# ── 批522:via-fplogic —— 第一頁邏輯補缺正主橋(VRN_ENG086;收容件 functional modules\VRN\references\intake\VIA_VRN_FirstPageEngine_v0101_b522 零觸碰;status|gap|bench [--limit N]|enrich [--in DIR] [--limit N];vrn 境 python)
function global:via-fplogic { $env:VIA_FAMILY = "vrn"; Invoke-VIAPython (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG086_FirstPageLogicBridge_v*.py") $(if ($args) { $args } else { @("status") }) }
Set-Alias -Name 首頁邏輯 -Value via-fplogic -Scope Global -Force
# ── 批544:via-unified —— VIA 統一主控頁(TAB1 給 AI 的一頁 · TAB2 內嵌三張既有頁;整頁可轉 JSON/MD)
#   跑一輪 via-ryg / via-panorama / via-vcgc 會跳出三個瀏覽器分頁,三張各講一段真相。
#   本頁不重算也不重畫它們,只把它們 iframe 內嵌到 TAB2,再把散在四個 SSOT 的東西排成 TAB1。
#   via-unified            產頁(同時落 .json / .md;零 CDN · 零彈窗 · 只讀正本)
#   via-unified json       整頁 payload 印成 JSON(可直接餵給下一個 AI)
#   via-unified md         整頁印成 Markdown
#   via-unified status     一行現況
#   via-unified selftest   十一檢(含收容件位元體檢與負控)
function global:via-unified { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL159_VIAUnifiedConsole_v*.py") $(if ($args) { $args } else { @("page") }) }
Set-Alias -Name 統一主控 -Value via-unified -Scope Global -Force

# ── 批542:via-pyprog —— 中央 py 啟動器六檢(所有 py 指令都走 Invoke-VIAPython,它快一點全系統就快一點)
#   via-pyprog            六檢:stdout 一行不少 · rc 不吞 · stderr 不混進 pipeline · 逾時停得住不卡斷
#   via-pyprog -Bench     六檢 + 首發/後續耗時(批542 之前:首發 1137ms · 後續 279ms)
function global:via-pyprog {
    $t = Get-VIANewest "$VIA\supportive modules" "VIA_PS_PyProgress_Selftest_v*.ps1"
    if (-not $t) { Write-Host "  [via-pyprog] FAIL:VIA_PS_PyProgress_Selftest_v*.ps1 缺" -ForegroundColor Red; return }
    & $t @args
}
Set-Alias -Name 啟動器自測 -Value via-pyprog -Scope Global -Force

# ── 批541:via-vrnrules —— VRN 研報六欄規則正本樞紐(SUP_MDL749;唯一讀冊口;零改線·零網路·不落檔)
#   冊 = supportive modules\registry\VRN_FieldRules_SSOT_v0100.json(券商/評等/目標價/財報/email/電話)
#   via-vrnrules                   一行狀態(冊在不在·評等詞幾個·券商證據分級·消費端幾支)
#   via-vrnrules drift             逐支現役引擎列「正本有、它沒有」的規則(只量它真的在抽的欄位)
#   via-vrnrules conflicts         去衝突:同一別名對到多個正典名 = 撞名,必須是 0
#   via-vrnrules harvest           邊實測邊長同義字:拿 64 份真語料端出候選,一律 PENDING_OPERATOR
#                                  (**只提候選,絕不自己寫進正本冊**——正本要長,是你點頭那一刻才長)
#   via-vrnrules selftest          十檢自測(含候選閘門負控:假的擋掉、真的放得出來)
function global:via-vrnrules { $env:VIA_FAMILY = "vrn"; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL749_VRNFieldRuleHub_v*.py") $(if ($args) { $args } else { @("status") }) }
Set-Alias -Name 研報規則 -Value via-vrnrules -Scope Global -Force

# ── 批529:via-nlpvrn —— NLP文字修復+證據型摘要→VRN ENG072/ENG073→VDF ENG087 唯讀狀態
#   單一入口;輸入可重複 -In <PDF/DOCX/夾>;預設寫 functional modules\VRN\db\vrn_reports.duckdb
#   NLP 輸出 vrn_nlp_text_summary(保留 normalized_text/source hash/evidence span)；不覆寫 ENG073 canonical 欄位
#   -DB/-Out/-Points/-Force 映射到 Python；網路預設關閉，VDF RED 會誠實回報資料覆蓋缺口，不假綠
function global:via-nlpvrn {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG087_NLPTextSummaryBridge_v*.py"
    if (-not $eng) { Write-Host "  [via-nlpvrn] FAIL:VRN_ENG087_NLPTextSummaryBridge_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object {
        if ($_ -eq "-In") { "--in" }
        elseif ($_ -eq "-DB") { "--db" }
        elseif ($_ -eq "-Out") { "--out" }
        elseif ($_ -eq "-Points") { "--points" }
        elseif ($_ -eq "-Force") { "--force" }
        elseif ($_ -eq "-SelfTest") { "selftest" }
        elseif ($_ -eq "-Status") { "status" }
        else { $_ }
    })
    if (-not $a) { $a = @("status") }
    if (-not ($a | Where-Object { $_ -in @("run", "status", "selftest") })) { $a = @("run") + $a }
    if (($a -contains "run") -and -not ($a -contains "--db")) { $a += @("--db", "$VIA\functional modules\VRN\db\vrn_reports.duckdb") }
    if (($a -contains "run") -and -not ($a -contains "--out")) { $a += @("--out", "$VIA\VIA_Reports\vrn\nlp_pipeline") }
    $env:VIA_FAMILY = "vrn"
    Invoke-VIAPython -Family "vrn" $eng @a
    if ($a -contains "run") {
        $html = "$VIA\VIA_Reports\vrn\nlp_pipeline\NLP_VRN_VDF_latest.html"
        if (Test-Path -LiteralPath $html) {
            Write-Host "  [via-nlpvrn] 三頁 HTML 矩陣：$html" -ForegroundColor Cyan
            Start-Process -FilePath $html
        }
    }
}
Set-Alias -Name NLP研報 -Value via-nlpvrn -Scope Global -Force
Set-Alias -Name NLP串接 -Value via-nlpvrn -Scope Global -Force
# ── 批532:via-nlpunified —— SUP_MDL866 統一 NLP 控制入口(Hub→VRN→VDF；附件只走受控 intake)
#   -Text/-File/-Points 對應離線 NLP；-SelfTest/-Status 只讀；不啟動 AKShare、排程、安裝或 auto-fix
function global:via-nlpunified {
    $eng = Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py"
    if (-not $eng) { Write-Host "  [via-nlpunified] FAIL:SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py 缺" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object {
        if ($_ -eq "-Text") { "--text" }
        elseif ($_ -eq "-File") { "--file" }
        elseif ($_ -eq "-In") { "--in" }
        elseif ($_ -eq "-DB") { "--db" }
        elseif ($_ -eq "-Out") { "--out" }
        elseif ($_ -eq "-Points") { "--points" }
        elseif ($_ -eq "-Force") { "--force" }
        elseif ($_ -eq "-SelfTest") { "selftest" }
        elseif ($_ -eq "-Status") { "status" }
        elseif ($_ -eq "-RunText") { "text" }
        elseif ($_ -eq "-Pipeline") { "pipeline" }
        else { $_ }
    })
    if (-not $a) { $a = @("status") }
    if (-not ($a | Where-Object { $_ -in @("status", "selftest", "text", "pipeline") })) { $a = @("text") + $a }
    $env:VIA_FAMILY = "vrn"
    Invoke-VIAPython -Family "vrn" $eng @a
}
Set-Alias -Name NLP統一 -Value via-nlpunified -Scope Global -Force
Set-Alias -Name via-nlp-unified -Value via-nlpunified -Scope Global -Force
# ── 批533:via-central —— VIA 唯一接觸口；先過 CGC157，再由 VIA 子入口 dispatch
#   via-central status                         唯一入口/registry/bootstrap/network gate 自測
#   via-central vrn -SelfTest                  VIA→VRN_ENG087 實測
#   via-central vdf -Status                    VIA→VDF architecture/status 實測
#   via-central quantguard -SelfTest           VIA→VDF_ENG086 QuantGuard 實測
#   子系統不得繞過此門直接宣稱已完成 VIA 驗收；網路同意仍由操作員明確設定。
function global:via-central {
    param(
        [ValidateSet("status", "vrn", "vdf", "quantguard", "dispatch", "all")][string]$Family = "status",
        [Parameter(ValueFromRemainingArguments = $true)][object[]]$Rest
    )
    $ctl = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL157_VIAUniqueEntryControl_v*.py"
    if (-not $ctl) { Write-Host "  [via-central] FAIL:CGC_MDL157 唯一接觸口控制面缺失" -ForegroundColor Red; $global:LASTEXITCODE = 2; return }
    $env:VIA_CENTRAL_ENTRY = "1"; $env:VIA_ENTRY_CONTROL = [System.IO.Path]::GetFileNameWithoutExtension($ctl)   # 批534:身分=解析到的尾版,不釘死
    Invoke-VIAPython -Family "core" $ctl selftest
    if ($global:LASTEXITCODE -ne 0) { Write-Host "  [via-central] STOP:CGC157 未 GREEN，不派送子系統" -ForegroundColor Red; return }
    $r = @($Rest)
    if ($r.Count -eq 0) { $r = @("-SelfTest") }
    switch ($Family) {
        "status" { return }
        { $_ -in @("dispatch", "all") } {
            # 批534:中央固定路由一次跑完三家族(家族境 python;誠實四態)→ VIA_Reports\entry\VIA_UNIQUE_ENTRY_DISPATCH_latest.json
            Invoke-VIAPython -Family "core" $ctl dispatch --family all
            return
        }
        "vrn" { via-nlpvrn @r; return }
        "vdf" {
            if ($r -contains "-Status") { via-vdfarch "--selftest" } elseif ($r -contains "-SelfTest") { via-vdfarch "--selftest" } else { via-vdfarch @r }
            return
        }
        "quantguard" {
            $q = @($r | ForEach-Object { if ($_ -eq "-SelfTest") { "selftest" } elseif ($_ -eq "-Status") { "status" } else { $_ } })
            via-quantguard @q; return
        }
    }
}
function global:via-unique-check { via-central status @args }
Set-Alias -Name VIA中央 -Value via-central -Scope Global -Force
Set-Alias -Name via-unique -Value via-unique-check -Scope Global -Force
# ── 批522:via-daytrade —— 個股當沖量值(VDF_ENG055 L15;線上三源誠實 + 檔案收容道 L45:via-daytrade --from-file A.csv,B.csv --date 2026-09-12 [--market TWSE|TPEX];收容夾 functional modules\VDF\references\intake\daytrade_files;觸網項=你開閘)
function global:via-daytrade { $env:VIA_FAMILY = "vdf"; Invoke-VIAPython (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG055_OmniFetch_v*.py") (@("run", "--lane", "L15") + @($args)) }
Set-Alias -Name 當沖量值 -Value via-daytrade -Scope Global -Force
# ── 批535:via-panorama —— 全景稽核修復正主(CGC_MDL158;scan|fix|tests|report|all;--apply 才寫檔;收容件/退役夾零觸碰)
function global:via-panorama {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL158_VIAPanoramaAuditRepair_v*.py"
    if (-not $eng) { Write-Host "  [via-panorama] FAIL:CGC_MDL158 全景稽核修復正主缺" -ForegroundColor Red; $global:LASTEXITCODE = 2; return }
    $a = @($args); if ($a.Count -eq 0) { $a = @("scan") }
    Invoke-VIAPython -Family "core" $eng @a
}
Set-Alias -Name 全景修復 -Value via-panorama -Scope Global -Force
# ── 批535:via-panorama-all —— 一貼式(進環境→25 加速器→全景分析→修→測→多 TAB 報告自動跳出)
function global:via-panorama-all {
    $ps = Join-Path $VIA "VIA_B535_PANORAMA_ALL_IN_ONE.ps1"
    if (-not (Test-Path -LiteralPath $ps)) { Write-Host "  [via-panorama-all] FAIL:$ps 缺" -ForegroundColor Red; $global:LASTEXITCODE = 2; return }
    & $ps @args
}
Set-Alias -Name 全景一貼 -Value via-panorama-all -Scope Global -Force
# ── 批477:via-twrev —— 台股月營收動能引擎 v2.7(收容 b477;封印副本零觸碰)
#   引擎全靠相對路徑(config.yaml:data/ output/ logs/),所以給它一個工作家 VIA_Reports\twrev:
#   首跑把封裝的 config.yaml + data/ 種進去,程式碼仍從收容夾 import(一份碼,Zero-Hydra),資料只住工作家。
#   via-twrev [selftest|demo|analyze|report|groups|breakout|fetch|run]   預設 selftest
#   fetch/run 觸 MOPS 網路:只看同意閘,不代設;閘沒開=誠實停。
function global:via-twrev {
    $pkg = Join-Path $VIA "functional modules\VDF\references\intake\TWREV_v2.7_FULL_b477"
    if (-not (Test-Path -LiteralPath (Join-Path $pkg "twrevenue\cli.py"))) { Write-Host "  [via-twrev] FAIL:收容包 TWREV_v2.7_FULL_b477 缺" -ForegroundColor Red; return }
    $verb = if ($args.Count -ge 1) { "" + $args[0] } else { "selftest" }
    if ($verb -in @("fetch", "run")) {
        if ($env:VIA_NET_CONSENT -ne "YES" -or -not $env:VIA_SCRAPE_CONSENT) { Write-Host "  [via-twrev] 誠實停:$verb 會向 MOPS 抓資料,同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT 由你自己設,我不代設)" -ForegroundColor Yellow; return }
    }
    $home = Join-Path $VIA "VIA_Reports\twrev"
    if (-not (Test-Path -LiteralPath (Join-Path $home "config.yaml"))) {
        $null = New-Item -ItemType Directory -Path $home -Force
        Copy-Item -LiteralPath (Join-Path $pkg "config.yaml") -Destination $home
        Copy-Item -LiteralPath (Join-Path $pkg "data") -Destination (Join-Path $home "data") -Recurse
        Write-Host ("  [via-twrev] 工作家首建:{0}(config + data 自封裝種入;封裝副本零觸碰)" -f $home) -ForegroundColor DarkGray
    }
    $prev = "" + $env:PYTHONPATH; $env:PYTHONPATH = if ($prev) { $pkg + [IO.Path]::PathSeparator + $prev } else { $pkg }
    $env:VIA_FAMILY = "vdf"
    Push-Location $home
    try { Invoke-VIAPython -Family "vdf" -m twrevenue.cli $verb @($args | Select-Object -Skip 1) } finally { Pop-Location; $env:PYTHONPATH = $prev }
    if ($verb -in @("report", "run", "demo")) { $h = Join-Path $home "output\monthly_revenue_dashboard.html"; if (Test-Path -LiteralPath $h) { Write-Host ("  儀表板:{0}(看:via-open '{0}')" -f $h) -ForegroundColor Cyan } }
}
Set-Alias -Name 月營收 -Value via-twrev -Scope Global -Force
# ── 批481:操作員令「看另外兩個專案裡面有沒有授權使用?授權使用」
# via-revphase —— 月營收 × 產業 × 族群 相位/領先落後 v030(收容 b481;8 檢 + --self-test 真跑皆綠)
#   引擎只吃 CSV/Parquet,而月營收與公司主檔住在 vdf_tw_market.duckdb(tw_monthly_revenue / tw_listings)
#   → 先以 vdf 境 python 匯出成 CSV 到 VIA_Reports\revphase\in\,再明給 --input/--company-master/--output-dir。
#   via-revphase            真跑(讀你的庫;零網路;產出 VIA_Reports\revphase\out)
#   via-revphase -SelfTest  合成 36 期自測(免庫免網路)
function global:via-revphase {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\references\intake\VDF_TW_MonthlyRevenue_CrossGroupPhase_v030_b481" "vdf_tw_monthly_revenue_cross_group_phase_engine_v*.py"
    if (-not $eng) { Write-Host "  [via-revphase] FAIL:收容包 b481 缺" -ForegroundColor Red; return }
    $py = Get-VIAEnvPython "vdf"; $env:VIA_FAMILY = "vdf"; $env:VIA_ROOT = $VIA
    $home = Join-Path $VIA "VIA_Reports\revphase"; $null = New-Item -ItemType Directory -Path (Join-Path $home "in") -Force; $null = New-Item -ItemType Directory -Path (Join-Path $home "out") -Force
    if ($args -contains "-SelfTest") { Invoke-VIAPython -Python $py $eng --self-test --output-dir (Join-Path $home "out") --log-level WARNING; return }
    $db = Get-ChildItem -LiteralPath (Join-Path $VIA "functional modules\VDF\output_hub") -Recurse -Filter "vdf_tw_market.duckdb" -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '_repo_|_self_test' } | Select-Object -First 1
    if (-not $db) { Write-Host "  [via-revphase] 缺料(誠實停):找不到 vdf_tw_market.duckdb" -ForegroundColor Yellow; return }
    $inRev = Join-Path $home "in\VDF_TW_MonthlyRevenue.csv"; $inCo = Join-Path $home "in\StockTickerListDatabase.csv"
    $code = "import duckdb,sys;c=duckdb.connect(sys.argv[1],read_only=True);" +
            "c.execute(""COPY (SELECT code AS ticker, ym AS period, revenue FROM tw_monthly_revenue) TO '"+ ($inRev -replace '\\','/') +"' (HEADER, DELIMITER ',')"");" +
            "c.execute(""COPY (SELECT code AS ticker, name, market, industry FROM tw_listings) TO '"+ ($inCo -replace '\\','/') +"' (HEADER, DELIMITER ',')"");" +
            "print('匯出 tw_monthly_revenue',c.execute('SELECT COUNT(*) FROM tw_monthly_revenue').fetchone()[0],'列 · tw_listings',c.execute('SELECT COUNT(*) FROM tw_listings').fetchone()[0],'列')"
    Invoke-VIAPython -Python $py -c $code $db.FullName
    if ($LASTEXITCODE -ne 0) { Write-Host "  [via-revphase] 匯出失敗(上面應有原因);不假裝成功" -ForegroundColor Red; return }
    Invoke-VIAPython -Python $py $eng --input $inRev --company-master $inCo --output-dir (Join-Path $home "out") --log-level WARNING @($args | Where-Object { $_ -ne "-SelfTest" })
    $q = Get-ChildItem -LiteralPath (Join-Path $home "out") -Filter "*QualityReport*.json" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($q) { $j = Get-Content -LiteralPath $q.FullName -Raw | ConvertFrom-Json; Write-Host ("  品質閘:{0}" -f (($j.checks | ForEach-Object { $_.check_id + "=" + $_.status }) -join " ")) -ForegroundColor Cyan }
    else { Write-Host "  [via-revphase] 沒有品質報告產出(上面應有原因);不假裝成功" -ForegroundColor Yellow }
}
Set-Alias -Name 營收相位 -Value via-revphase -Scope Global -Force
# via-etfhold —— 主動 ETF 每日持股引擎 v1.1.0(ENG051 v0102:去硬寫根 + 正典網路件優先;27 檢)
#   via-etfhold -SelfTest   27 檢(免網路;根=VIA_Reports\etfhold,不碰正庫)
#   via-etfhold             日更真跑:根=你的 output_hub\active_tw_etf(自 VIA_ROOT 推);觸網→只看同意閘,不代設
function global:via-etfhold {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG051_ActiveTWETF_Holdings_v*.py"
    if (-not $eng) { Write-Host "  [via-etfhold] FAIL:VDF_ENG051_ActiveTWETF_Holdings_v*.py 缺" -ForegroundColor Red; return }
    $py = Get-VIAEnvPython "vdf"; $env:VIA_FAMILY = "vdf"; $env:VIA_ROOT = $VIA
    if ($args -contains "-SelfTest") {
        $r = Join-Path $VIA "VIA_Reports\etfhold"; $null = New-Item -ItemType Directory -Path $r -Force
        $env:VIA_ACTIVE_TW_ETF_ROOT = $r; try { Invoke-VIAPython -Python $py $eng --self-test } finally { Remove-Item Env:VIA_ACTIVE_TW_ETF_ROOT -ErrorAction SilentlyContinue }; return }
    if ($env:VIA_NET_CONSENT -ne "YES" -or -not $env:VIA_SCRAPE_CONSENT) { Write-Host "  [via-etfhold] 誠實停:日更會向 MoneyDJ/TWSE 抓持股,同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT 由你自己設,我不代設)" -ForegroundColor Yellow; return }
    Invoke-VIAPython -Python $py $eng @args
}
Set-Alias -Name 持股日更 -Value via-etfhold -Scope Global -Force
# ── 批473:via-ppp —— PDFPlumber-Plus(引擎早在庫內,缺的一直是啟動器)
# 上傳的那份啟動器把三個路徑全寫死(母倉根 / inbox / outputs),照收會壞:
# 那個母倉根**不是**操作員實際在跑的副本(批452/453 三副本災難的起因)。
# 收容版改成:根自腳本位置解析 · 收件夾**讀冊** · 產出落 VIA_Reports。
#   via-ppp                    冊上收件夾有 PDF 就整批跑,沒有就誠實跳
#   via-ppp -Pdf <檔>          單檔
#   via-ppp -In <夾>           指定夾(系統任何位置)
#   via-ppp -Open              跑完把 HTML 報告叫出來(零彈窗律:預設不跳)
function global:via-ppp {
    $p = Get-VIANewest "$VIA" "Invoke-VIA-PDFPlumberPlus-v*.ps1"
    if (-not $p) { Write-Host "  [via-ppp] FAIL:Invoke-VIA-PDFPlumberPlus-v*.ps1 缺(尾版律 glob 找不到)" -ForegroundColor Red; return }
    & $p @args
}
function global:via-vrnval { via-closeout vrn @args }
function global:via-vapval { via-closeout vap @args }
# 批400:via-deadends=短令死路掃描器(MDL136 deadends):掃引擎 docstring/[FAIL] 句/docs/README 內 via-* 令,對照短令冊+梭;未登錄=死路(批394 via-chip/批396 via-rebuild 同類);落 VIA_Reports/entry/DEADENDS_latest.json;--json/--quiet
function global:via-deadends { via-entry deadends @args }
# 批397 雙副本律:via-pin=把 $PROFILE 的 VIA 點源行換成「本窗副本」($VIA=本檔所在 VeritasIntelligenceAnalytics 夾),讓以後每個新視窗預設載本副本尾版短令冊;
#   --show 只看(本窗副本 vs profile 預設副本,各印分支/HEAD);只改 profile 一行,兩副本檔案零觸碰;換回=到另一副本的視窗再 via-pin。pwsh 與 Windows PowerShell 各有 $PROFILE,各自 via-pin 一次。
function global:Get-VIAPinnedDir { try { if (Test-Path -LiteralPath $PROFILE) { $m = Select-String -LiteralPath $PROFILE -Pattern '\. \(Get-ChildItem "([^"]+)\\Register-VIA-Commands-v\*\.ps1"' | Select-Object -First 1; if ($m) { return $m.Matches[0].Groups[1].Value } } } catch { }; return "" }
function global:via-pin {
    $pinned = Get-VIAPinnedDir
    $rootH = Split-Path $VIA -Parent
    $bH = (git -C $rootH rev-parse --abbrev-ref HEAD 2>$null); $hH = (git -C $rootH rev-parse --short HEAD 2>$null)
    Write-Host ("  [via-pin] 本窗副本:" + $VIA + "(" + $bH + " " + $hH + ";" + (Split-Path $global:VIARegisterPath -Leaf) + ")")
    if ($pinned) { $rootP = Split-Path $pinned -Parent; $bP = (git -C $rootP rev-parse --abbrev-ref HEAD 2>$null); $hP = (git -C $rootP rev-parse --short HEAD 2>$null); Write-Host ("  [via-pin] 新視窗預設(profile " + $PROFILE + "):" + $pinned + "(" + $bP + " " + $hP + ")") } else { Write-Host ("  [via-pin] 新視窗預設(profile " + $PROFILE + "):(無 VIA 點源行)") }
    if ($args -contains "--show") { return }
    if ($pinned -eq $VIA) { Write-Host "  [via-pin] 已是本副本;無事" -ForegroundColor Green; return }
    $line = '. (Get-ChildItem "' + $VIA + '\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
    try {
        if (!(Test-Path -LiteralPath $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
        if ($pinned) {
            $rx = '^\. \(Get-ChildItem "[^"]+\\Register-VIA-Commands-v\*\.ps1"'
            $new = @(Get-Content -LiteralPath $PROFILE | ForEach-Object { if ($_ -match $rx) { $line } else { $_ } })
            Set-Content -LiteralPath $PROFILE -Value $new -Encoding UTF8
        } else {
            @("", "# [VIA:PROFILE:v0201] 點源尾版(pull 即最新;永久免重貼)", $line) | Add-Content -Path $PROFILE -Encoding UTF8
        }
        Write-Host ("  [via-pin] 新視窗預設已換 → " + $VIA + "(舊:" + $(if ($pinned) { $pinned } else { "無" }) + ";只改 profile 一行;兩副本檔案零觸碰;換回=到另一副本的視窗 via-pin)") -ForegroundColor Green
    } catch { Write-Host ("  [via-pin] profile 寫入失敗(誠實):" + $_.Exception.Message) -ForegroundColor Yellow }
}
# 批396:via-rebuild=多環境隔離重建計畫引擎 MDL050(via-envgov digest「下一指令」指路的 via-rebuild --env/--split;旁建零破壞=原境不動,驗綠後切換候裁)。
#   無參數=--offline(只 ①~④+⑦ 唯讀計畫;零網路);via-rebuild --env <境>=只治理單一環境(② 起需網路;無網路段誠實 NOT_RUN);--selftest 十四檢。base python(MDL050 自管 uv)。
#   MDL050 尾版旗標只認 --env/--roots/--rounds/--offline/--selftest;MDL135 提案的 --split <境>(拆分)尚無=改以 --env <境> --offline 唯讀計畫並印明(不讓引擎靜默跑全境)。
function global:via-rebuild { $a = @($args); if ($a -contains "--split") { $i = [Array]::IndexOf($a, "--split"); $e0 = if ($i -ge 0 -and $i + 1 -lt $a.Count) { "" + $a[$i + 1] } else { "" }; Write-Host ("  [via-rebuild] MDL050 尾版尚無 --split(拆分候裁;MDL135 提案)→ 改以 --env " + $e0 + " --offline 唯讀計畫(原境不動)") -ForegroundColor Yellow; $a = @("--env", $e0, "--offline") }; Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL050_EnvRebuild_v*.py") $(if ($a) { $a } else { @("--offline") }) }
# --- 自註冊:$PROFILE 補一行點源(冪等;標記 v0200) -------------------
try {
    # 批260:profile 行改尾版 glob(v0200 曾寫死 v0100 路徑=新版不自動吃)
    $mark = "# [VIA:PROFILE:v0201] 點源尾版(pull 即最新;永久免重貼)"
    if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
    if (-not (Select-String -Path $PROFILE -Pattern "VIA:PROFILE:v0201" -Quiet -ErrorAction SilentlyContinue)) {
        $dir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $line = '. (Get-ChildItem "' + $dir + '\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
        @("", $mark, $line) | Add-Content -Path $PROFILE -Encoding UTF8
        Write-Host "  [註冊] profile 點源一行已入(以後 pull 即自動最新)" -ForegroundColor Green
    }
} catch { }
# 批339:短令清單改動態自本檔實掃(實錄:靜態字串停在 v0112,新令 via-master/via-complete/via-intake-roster 未列)
$viaCmds = (Select-String -LiteralPath $MyInvocation.MyCommand.Path -Pattern '^function global:([\w-]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Where-Object { $_ -notin @("Get-VIANewest", "Get-VIAEnvPython", "Import-VIAGrokMatrix") }) -join "/"
Write-Host ("  [VIA] 短指令已生效於本視窗(" + (Split-Path $MyInvocation.MyCommand.Path -Leaf) + "):" + $viaCmds) -ForegroundColor Cyan
if ($VIAGrokVerbs.Count -gt 0) { Write-Host ("  [VIA] +Grok 矩陣 " + $VIAGrokVerbs.Count + " 令(母倉撞名者 -grok):" + ($VIAGrokVerbs -join "/") + " · 唯一入口:via-entry") -ForegroundColor DarkCyan }

# ── 批571:短令找不到時,冊自己講原因(不要再為了「是哪一種」多跑一趟)──────────
#   ① 本視窗點的冊版本(點源當下記下來)
$global:VIA_REGISTER_LOADED = (Split-Path $MyInvocation.MyCommand.Path -Leaf)
$global:VIA_REGISTER_ROOT = $VIA
#   ② 找不到 via-* 時:分辨「冊上有但沒點到」vs「冊上也沒有」
$ExecutionContext.InvokeCommand.CommandNotFoundAction = {
    param($CommandName, $EventArgs)
    if ($CommandName -notlike 'via-*') { return }
    try {
        $newest = Get-ChildItem -LiteralPath $global:VIA_REGISTER_ROOT -Filter 'Register-VIA-Commands-v*.ps1' -File -ErrorAction SilentlyContinue |
                  Sort-Object Name | Select-Object -Last 1
        if (-not $newest) { return }
        $loaded = $global:VIA_REGISTER_LOADED
        $inBook = (Select-String -LiteralPath $newest.FullName -Pattern ("^function global:" + [regex]::Escape($CommandName) + "\s*\{") -Quiet) -or
                  (Select-String -LiteralPath $newest.FullName -Pattern ("^Set-Alias\s+-Name\s+" + [regex]::Escape($CommandName) + "\s") -Quiet)
        Write-Host ""
        if ($inBook) {
            # 批614:v0218 起會**講出**是哪一種,但它只給建議——操作員還是得自己再打一次。
            #   批613/614 工作站實錄:他照我寫的打 via-presync / via-allinone,兩支都「冊上有但沒點到」,
            #   而要拉新冊得先用 via-presync ——**解卡的工具又在被卡住的那一側**(L85 第四次)。
            #   所以這一版不只是講:**自己重點源尾版冊,然後把原來那句重跑一次**。
            #   防迴圈:同一個名字只自動接一次($global:VIA_AUTORELOAD 記名)。
            if (-not $global:VIA_AUTORELOAD) { $global:VIA_AUTORELOAD = @{} }
            if (-not $global:VIA_AUTORELOAD[$CommandName]) {
                $global:VIA_AUTORELOAD[$CommandName] = $true
                Write-Host ("  [VIA] '" + $CommandName + "' 本視窗點的是 " + $loaded +
                            ",磁碟最新是 " + $newest.Name + " → **自動重點源後重跑一次**") -ForegroundColor Yellow
                $n = $newest.FullName; $c = $CommandName
                $EventArgs.CommandScriptBlock = { . $n; & $c @args }.GetNewClosure()
                $EventArgs.StopSearch = $true
                return
            }
            Write-Host ("  [VIA] '" + $CommandName + "' **冊上有,但本視窗沒點到**(自動重點源已試過一次仍不通)。") -ForegroundColor Yellow
            Write-Host ("        本視窗點的:" + $loaded + "   磁碟最新:" + $newest.Name) -ForegroundColor DarkYellow
            Write-Host "        手動重點一次(或 via-reload):" -ForegroundColor DarkYellow
            Write-Host "        . (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName" -ForegroundColor Cyan
        } else {
            Write-Host ("  [VIA] '" + $CommandName + "' **冊上也沒有**(磁碟最新 " + $newest.Name + ")。") -ForegroundColor Red
            Write-Host "        這是真的漏登錄,不是視窗沒重點——請把這一行貼回給 AI。" -ForegroundColor DarkYellow
        }
        Write-Host ""
    } catch { }
}

# ═══════════════════════════════════════════════════════════════════════════
# 批649 操作員令:「INTEGRATE INTO ONE PS CODE WITH 25 加速器去完成以上全部
#                 動態進度條及百分比」
#   「以上全部」= 批643–648 這一輪立的八站,一次跑完、逐站誠實四態、總表收斂。
#
#   進度條**不另造**(L30 一個出處):
#     Id 12  Show-VIAAccel20    — 25 加速器點亮(既有)
#     Id 13  Invoke-VIAPython   — 單站脈動(既有;不知總長 → 30 秒一輪)
#     Id 11  本令新增           — **鏈層真百分比**(站數已知,所以這一條是真的比例)
#
#   依賴律(L83 只跑一半不算跑過):前置站沒綠,後續站**誠實 SKIP 並指名原因**,
#   不偷跑也不假裝跑過。彼此獨立的盤點站則互不牽連——一站紅不拖垮其他站。
#   同意閘:**本令絕不代設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT**;
#   需要觸網的站一律 GATED 並印出該由操作員設什麼。
# ═══════════════════════════════════════════════════════════════════════════
function global:via-run25 {
    # **必須包 @()**:ConvertTo-VIACleanArgs 回傳陣列,PowerShell 在只有一個元素時會把它拆成純字串。
    # 那時 $a.Count 仍是 1,但 $a[0] 變成第一個**字元** '-' —— `--list` 於是永遠不匹配。
    # 真跑出來的樣子是:`via-run25 --list` 不列站表,**直接把八站全跑了一遍**。
    # 兩個參數以上(`--only template`)反而正常,所以這個洞只在「單旗標」時張開。→ LL284
    # 第二個洞:`--skip a,b,c` 在呼叫端就被 PowerShell 當**陣列**傳進來,
    # ConvertTo-VIACleanArgs 又刻意把它攤平(那是為了 `--family vrn,vap` 才立的行為),
    # 於是旗標後面跟著的是 N 個 token,不是一個。只吃一個 → 其餘全被判成「不認得的參數」。
    # 治法:旗標之後一路吃到下一個以 '-' 開頭的 token 為止。
    $null = Test-VIABookFresh      # 批653:先講清楚這個視窗載的是哪一本冊
    $a = @(ConvertTo-VIACleanArgs $args)
    $inDir = ""; $only = @(); $skip = @(); $listOnly = $false; $bad = @()
    for ($i = 0; $i -lt $a.Count; $i++) {
        $tok = [string]$a[$i]
        $nxt = if ($i + 1 -lt $a.Count) { [string]$a[$i + 1] } else { "" }
        switch -regex ($tok) {
            '^--in$'   { if ($nxt) { $inDir = $nxt; $i++ } else { $bad += "--in(缺夾名)" }; break }
            '^--only$' { $j = $i + 1; while ($j -lt $a.Count -and -not ([string]$a[$j]).StartsWith('-')) { $only += ([string]$a[$j]).Split(','); $j++ }
                         if ($j -eq $i + 1) { $bad += "--only(缺站名)" }; $i = $j - 1; break }
            '^--skip$' { $j = $i + 1; while ($j -lt $a.Count -and -not ([string]$a[$j]).StartsWith('-')) { $skip += ([string]$a[$j]).Split(','); $j++ }
                         if ($j -eq $i + 1) { $bad += "--skip(缺站名)" }; $i = $j - 1; break }
            '^--list$' { $listOnly = $true; break }
            '^-'       { $bad += $tok; break }
            default    { $bad += $tok; break }
        }
    }
    if ($bad.Count) {
        # 悄悄吃掉一個旗標,然後照跑全部 —— 那比報錯危險得多。認不得就**誠實停**。
        Write-Host ("  [via-run25] 不認得的參數:" + ($bad -join " ") + " —— 誠實停,不裝作跑過") -ForegroundColor Red
        Write-Host "  [下一步] --list 只列站表 · --in <研報夾> 才跑抽取 · --only k1,k2 · --skip k1,k2" -ForegroundColor Yellow
        $global:LASTEXITCODE = 1
        return
    }
    if ($null -eq $env:VIA_ACCEL -or $env:VIA_ACCEL -eq "") { $env:VIA_ACCEL = "1" }

    $VRN = "$VIA\functional modules\VRN"
    $VDFE = "$VIA\functional modules\VDF\engine"
    $REG = "$VIA\supportive modules\registry"
    # 站表:key · 中文 · 家族 · 引擎 glob · 參數 · 前置站(要綠才跑)· 註
    $stations = @(
        @{ k = "extract"; zh = "首頁抽取(ENG072)";        fam = "vrn"; dir = $VRN;  pat = "VRN_ENG072_FirstPageText_v*.py";      arg = @();           needs = @(); note = "要 --in <研報夾>;沒給就 SKIP(不拿舊料冒充新跑)" }
        @{ k = "restore"; zh = "本文還原(ENG085)";        fam = "vrn"; dir = $VRN;  pat = "VRN_ENG085_MarkdownRestore_v*.py";    arg = @("run");      needs = @();        note = "批636–640;保全率/二尺一致率" }
        @{ k = "structdb"; zh = "結構入庫(ENG073)";       fam = "vrn"; dir = $VRN;  pat = "VRN_ENG073_ReportStructuredDB_v*.py"; arg = @("run");      needs = @();        note = "研報六欄入庫" }
        @{ k = "digest"; zh = "一題四點文摘(ENG080)";     fam = "vrn"; dir = $VRN;  pat = "VRN_ENG080_FourPointDigest_v*.py";    arg = @("run");      needs = @("structdb"); note = "批641/643;L99 除權息基準·誠實分母" }
        # 批651 操作員令「VRN 之前有非常成功的實測成功紀錄…從最成功的狀態去修改優化直到成功」。
        #   去挖:**批630B 判對率 100.0% = PASS ÷(PASS+FAIL) = 302/302 · FAIL 0 格**。
        #   那是 VRN 至今最成功的一次量測,容器今天重跑仍然 302/302 rc=0 —— 東西還在。
        #   **但它不在這條鏈上。** 你每天跑的 via-run25 八站裡沒有矩陣,
        #   於是 VRN 的頭號成功指標從來不會出現在你眼前(LL279 又一次)。本批開站。
        @{ k = "matrix"; zh = "驗真矩陣·判對率(ENG083)"; fam = "vrn"; dir = $VRN;  pat = "VRN_ENG083_VerifiedMatrix_v*.py"; arg = @("matrix"); needs = @("structdb"); note = "批630B 最成功紀錄 302/302;零彈窗(認 VIA_NO_OPEN)" }
        @{ k = "roster"; zh = "名冊×價表涵蓋(ENG090)";    fam = "vdf"; dir = $VDFE; pat = "VDF_ENG090_DataCoverageGate_v*.py";   arg = @("roster");   needs = @();        note = "批644;整所缺席判定(零網路)" }
        @{ k = "net2";   zh = "雙橋第二層(清掃器)";       fam = "";    dir = $REG;  pat = "via_bridge_sweeper_v*.py";            arg = @("--net2");   needs = @();        note = "批646;socket/ssl/http.client 那一層(零寫入)" }
        @{ k = "template"; zh = "正典 TEMPLATE(MDL160)";  fam = "";    dir = $REG;  pat = "CGC_MDL160_UIUnifyGate_v*.py";        arg = @("template"); needs = @();        note = "批647;223 筆 sha256 + 離線契約機器驗" }
        @{ k = "surface"; zh = "U/I 面與 L100 邊界";      fam = "";    dir = $REG;  pat = "CGC_MDL160_UIUnifyGate_v*.py";        arg = @("surface");  needs = @();        note = "批648;宣告面不得打 hub" }
    )
    $allKeys = @($stations | ForEach-Object { $_.k })
    $unknown = @(@($only + $skip) | Where-Object { $_ -and ($allKeys -notcontains $_) })
    if ($unknown.Count) {
        Write-Host ("  [via-run25] --only/--skip 指到不存在的站:" + ($unknown -join ",") + " —— 誠實停") -ForegroundColor Red
        Write-Host ("  [下一步] 站名只有這些:" + ($allKeys -join " · ")) -ForegroundColor Yellow
        $global:LASTEXITCODE = 1
        return
    }
    if ($only.Count) { $stations = @($stations | Where-Object { $only -contains $_.k }) }
    if ($skip.Count) { $stations = @($stations | Where-Object { $skip -notcontains $_.k }) }
    if ($stations.Count -eq 0) {
        # 挑到零站然後印 GREEN 0,是假綠裡最沒道理的一種:一站都沒跑,憑什麼綠。
        Write-Host "  [via-run25] 篩完之後一站都不剩 —— 不判綠,誠實停" -ForegroundColor Red
        $global:LASTEXITCODE = 1
        return
    }

    if ($listOnly) {
        Write-Host "  [via-run25] 站表($($stations.Count) 站;--only/--skip 可挑)" -ForegroundColor Cyan
        foreach ($s in $stations) {
            $dep = if ($s.needs.Count) { " ← 需 " + ($s.needs -join ",") } else { "" }
            Write-Host ("    {0,-9} {1,-28} {2}{3}" -f $s.k, $s.zh, $s.note, $dep)
        }
        $global:LASTEXITCODE = 0   # 只列不跑也是一個「跑完」的態:不接 rc 就會留著上一個令的 rc 騙人(LL207)
        return
    }

    $RCZH = @{ 0 = "GREEN"; 1 = "RED"; 2 = "NODATA"; 3 = "ABSENT"; 4 = "GATED" }
    $res = [ordered]@{}
    $t0 = Get-Date
    $n = $stations.Count
    Write-Host "=== via-run25 · 批643–648 全鏈 $n 站 · 25 加速器(VIA_ACCEL=$($env:VIA_ACCEL))===" -ForegroundColor Cyan
    Show-VIAAccel20

    for ($i = 0; $i -lt $n; $i++) {
        $s = $stations[$i]
        $pct = [int]($i * 100 / $n)
        Write-Progress -Id 11 -Activity "VIA 全鏈 · 25 加速器" `
            -Status ("{0}/{1} · {2}" -f ($i + 1), $n, $s.zh) -PercentComplete $pct

        $blocked = @($s.needs | Where-Object { $res[$_] -ne 0 })
        if ($blocked.Count) {
            $res[$s.k] = 5
            Write-Host ("  [SKIP  ] {0,-28} 前置未綠:{1}(L83:只跑一半不算跑過,不偷跑)" -f $s.zh, ($blocked -join ",")) -ForegroundColor DarkYellow
            continue
        }
        $eng = Get-VIANewest $s.dir $s.pat
        if (-not $eng) {
            $res[$s.k] = 3
            Write-Host ("  [ABSENT] {0,-28} 缺件:{1}(冊上有令、樹上沒件)" -f $s.zh, $s.pat) -ForegroundColor DarkGray
            continue
        }
        $argv = @($s.arg)
        if ($s.k -eq "extract") {
            if (-not $inDir) {
                $res[$s.k] = 5
                Write-Host ("  [SKIP  ] {0,-28} 沒給 --in <研報夾>;**不拿舊 sidecar 冒充一次新抽取**" -f $s.zh) -ForegroundColor DarkYellow
                continue
            }
            $argv = @("run", "--in", $inDir)
        }
        $sw = [Diagnostics.Stopwatch]::StartNew()
        if ($s.fam) { Invoke-VIAPython -Family $s.fam $eng $argv } else { Invoke-VIAPython $eng $argv }
        $rc = [int]$LASTEXITCODE
        $sw.Stop()
        $res[$s.k] = $rc
        $zh = if ($RCZH.ContainsKey($rc)) { $RCZH[$rc] } else { "rc$rc" }
        $col = switch ($rc) { 0 { "Green" } 1 { "Red" } 2 { "Yellow" } 3 { "DarkGray" } 4 { "Magenta" } default { "Yellow" } }
        Write-Host ("  [{0,-6}] {1,-28} {2:n1}s · {3}" -f $zh, $s.zh, $sw.Elapsed.TotalSeconds, $s.note) -ForegroundColor $col
    }
    Write-Progress -Id 11 -Activity "VIA 全鏈 · 25 加速器" -Completed

    $g = @($res.Values | Where-Object { $_ -eq 0 }).Count
    $r = @($res.Values | Where-Object { $_ -eq 1 }).Count
    $nd = @($res.Values | Where-Object { $_ -eq 2 }).Count
    $ab = @($res.Values | Where-Object { $_ -eq 3 }).Count
    $ga = @($res.Values | Where-Object { $_ -eq 4 }).Count
    $sk = @($res.Values | Where-Object { $_ -eq 5 }).Count
    $el = ((Get-Date) - $t0).TotalSeconds
    Write-Host ("  [計] GREEN {0} · RED {1} · NODATA {2} · ABSENT {3} · GATED {4} · SKIP {5} · {6:n0}s" -f $g, $r, $nd, $ab, $ga, $sk, $el) -ForegroundColor Cyan
    Write-Host "  [律] 同意閘未代設(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手);NODATA≠壞掉,是缺料" -ForegroundColor DarkGray
    $global:LASTEXITCODE = if ($r -gt 0) { 1 } elseif ($nd + $ab + $ga + $sk -gt 0) { 2 } else { 0 }
    return
}
Set-Alias -Name 全鏈 -Value via-run25 -Scope Global -Force

# ─────────────────────────────────────────────────────────────────────────────
# 批649 續:被同名後定義「無聲吃掉」的三扇門,各自補回一個名(只增不減;活的那支一律不動)
# ─────────────────────────────────────────────────────────────────────────────
# CGC_MDL157 v0105 新動詞 `shadow` 拿自己掃這本冊,掃出來的是:
#   v0227(批647 之前)被吃 2 · v0228(批647,我加的)被吃 3。
# PowerShell 的 `function global:X` 寫第二次是**後定義無聲覆蓋前定義**:
# 沒有警告、沒有 rc、格子照綠、梭照在、樹上的檔照在——只有那支引擎從冊上永遠消失。
#   via-ssot     378→941  前者 CGC_MDL115_SSOTRegexDict 被 MDL155 吃掉
#                         ——那正是操作員點名「優先 SSOT REGEX」的那一支
#   via-panorama 497→1134 前者 launchers\Invoke-VIA-Panorama-v*.ps1 被 MDL158 吃掉
#   via-ui       378→692  前者 CGC_MDL130_UIBridge 被我批647 的 MDL160 template 吃掉
# 裁決:活著的那三支(MDL155 / MDL158 / MDL160)是現行慣用,名字不動;
#       被吃掉的三支各開一扇自己的門,從此兩邊都到得了。
function global:via-ssotregex { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL115_SSOTRegexDict_v*.py") @args }
Set-Alias -Name 正則字典 -Value via-ssotregex -Scope Global -Force
function global:via-uibridge { Invoke-VIAPython (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL130_UIBridge_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
Set-Alias -Name 畫面橋 -Value via-uibridge -Scope Global -Force
function global:via-panorama-run { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest "$VIA\launchers" "Invoke-VIA-Panorama-v*.ps1") @args }
Set-Alias -Name 全景啟動 -Value via-panorama-run -Scope Global -Force

# ─────────────────────────────────────────────────────────────────────────────
# 批653:冊新鮮度哨兵 —— 「你跑的是舊版」這句話,第四次由我來講
# ─────────────────────────────────────────────────────────────────────────────
# 操作員實錄:他 pull 到 v0230(九站,含矩陣)之後,在**同一個 PS 視窗**打 via-run25,
# 畫面印的是 `全鏈 8 站`。引擎沒錯、冊也沒錯 ——
# **PowerShell 的 global 函式是點源當下烙進這個工作階段的,拉新檔不會換掉已載入的函式。**
# 批629 就記過同一件事,當時的結論是「這句話該由工具講,不該由我連講三次」。
# 今天它第四次發生,所以這次不是提醒,是**每個令自己會講**。
# 梭(via-run25.cmd)天生免疫:它每次都現場解析尾版冊再點源。
function global:Test-VIABookFresh {
    $loaded = $global:VIARegisterPath
    $dir = if ($loaded) { Split-Path -Parent $loaded } else { $VIA }
    $r = [ordered]@{ loaded = "(未知)"; newest = ""; fresh = $true; how = "" }
    $newest = Get-ChildItem -LiteralPath $dir -Filter "Register-VIA-Commands-v*.ps1" -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if (-not $newest) { $r.how = "找不到任何命令冊——量不到就不判(不假裝新鮮)"; return $r }
    if ($loaded) { $r.loaded = Split-Path -Leaf $loaded }
    $r.newest = $newest.Name
    $r.fresh = ($r.loaded -eq $r.newest)
    $r.how = ". '" + $newest.FullName + "'"
    if (-not $r.fresh) {
        Write-Host ("  [冊不新鮮] 這個視窗載的是 " + $r.loaded + ",樹上已經有 " + $r.newest +
                    " —— **你現在跑的是舊版的令**") -ForegroundColor Yellow
        Write-Host ("  [下一步] 在這個視窗點源尾版(或改用同名 .cmd 梭,梭每次都現場解析尾版):") -ForegroundColor Yellow
        Write-Host ("           " + $r.how) -ForegroundColor Yellow
    }
    return $r
}
function global:via-fresh {
    $r = Test-VIABookFresh
    if ($r.fresh) {
        Write-Host ("  [冊新鮮] 這個視窗載的就是尾版 " + $r.newest) -ForegroundColor Green
        $global:LASTEXITCODE = 0
    } else { $global:LASTEXITCODE = 2 }
    return
}
Set-Alias -Name 冊新鮮 -Value via-fresh -Scope Global -Force
