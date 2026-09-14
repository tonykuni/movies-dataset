# VIA 一頁交接 · Veritas Central Governance Console(VCGC v0101 · 批507)

> 產生 2026-09-14 17:32:53 · 唯一對接口(律 L20):政策庫 · 邏輯庫 · 因子庫 · 資料庫 · 引擎調度 · 多矩陣 · 環境工具 · 註冊表 · 交接。動態段(矩陣/RunGate/工具計畫/資料家)以**你機器上最新一次 `via-vcgc onepage`** 為準;倉內這份是 commit 時的快照。

## 〇 · 接手提示詞(給下一個 AI;來源 VIA_AI_Handover_Prompt_v0100.md)

# VIA · AI 接手提示詞與交接格式 v0100(批507;長久使用)

> 這套系統是**多個 AI 工作階段接力寫成的**(每批 `批NNN` 一次 commit),操作員下令、AI 造件、操作員實測貼回、AI 讀實錄修。
> 對話會卡斷,檔案不會。所以「接手不掉球」靠三個檔,不靠對話記憶:
> ① 倉根 `VIA_HANDOVER_LATEST.md`(VCGC 一頁交接;八段 + 〇 接手提示 + 九 掉球清單)
> ② `docs/VIA_Handover_2026MMDD_BNNN.md`(逐批紀錄;最新一份)
> ③ `supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json`(23 律 + lessons;違反=重犯)

---

## A · 給被交接者(接手 AI)——開場提示詞,整段貼進新對話即可

```text
你接手 VIA(VeritasIntelligenceAnalytics)。倉 tonykuni/movies-dataset,分支 claude/via-envmanager-governance-7cls8h,
工作根 VeritasIntelligenceAnalytics/。操作員用中文;工作站 C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics。

先做(不准跳過,任何造件之前):
1. 讀倉根 VIA_HANDOVER_LATEST.md(一頁交接:〇 接手提示 · 一 政策庫 · 二 安裝核可/環境工具 · 三 邏輯/因子/資料庫 ·
   四 引擎調度/多矩陣 · 五 指令與參數 · 六 註冊稽核 · 七 自動編號註冊表 · 八 交接本文 · 九 掉球清單)。
2. 讀 docs/ 最新 VIA_Handover_*_B*.md 的「三 還掛著的事」與最後兩批段落。
3. 讀 VIA_Policy_Laws_SSOT_v*.json 的 23 律;下面 12 條是最常犯的,背起來:
   L01 先想省 token(不重讀大檔,grep 要改的段;操作員貼回的實錄直接當量測)
   L02 只增不減 · L03 正本零觸碰(references/intake 不編輯)· L04 尾版律(引擎改=新版號檔;冊/無版號檔才就地改)
   L05 Zero-Hydra(綁既有引擎;同一判準只寫一處)· L06 零 CDN 零彈窗
   L07 同意閘(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT/金鑰)操作員自設,永不代設
   L08 零 force push;不 Stop-Process;不 Remove-Item/conda remove/pip uninstall;裝件=操作員的手(--approve + 閘)
   L09 加速器/網路只認 VeritasCeleritas/VeritasAegisNexus · L16 誠實四態 ABSENT/NODATA/GATED/RED(判錯的燈和假綠一樣傷)
   L17 自測零污染(VIA_SELFTEST=1;撤 VIA_DB_*/VIA_DATA_HOME;只寫暫存)· L18 功能註冊七處(規格項/格子站/Register/Deck/Manager/台帳/交接)
   L19 環境統一測式 GREEN 24h 內才核可安裝 · L20 VCGC 為唯一對接口 · L23 只刪有 md5 證據的重複件
4. 接手驗收(在容器裡跑,貼結果給操作員,證明你接上了):
   python3 "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py" status
   python3 "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py" --selftest
   git log --oneline -3
5. 讀「九 掉球清單」,把仍掛著的項目原樣列回給操作員,問他要先追哪一顆——不要自己挑。

工作節奏(每一批都一樣):
- 每批一個小主題;commit 訊息「批NNN: …」;push origin claude/via-envmanager-governance-7cls8h(失敗退避重試,不 force)。
- commit 尾註只留 Co-Authored-By / Claude-Session 兩行;倉內任何產物不放模型識別字。
- 造件前先 grep 現況;造完跑 --selftest;新引擎=七處登冊 + 台帳 VIA_AutoCode_Registry(indent=1)+ 交接段。
- 回覆操作員:中文;先講結果;一個 PowerShell 一貼即用區塊,前兩行固定:
    Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
  然後要他貼回哪幾個指令的尾段;他貼回來的實錄直接當量測,不自己重跑。
- 容器沒有他的資料與環境(via_database、48 個 env、Tesseract、Paddle);容器裡的 NODATA/ABSENT 不是壞,寫明「容器」。
- 收尾:via-vcgc page --publish(一頁交接 + 倉根副本 + 頁)→ 台帳 → 交接段 → commit → push;再回覆。

掉球定義:操作員說過、你沒做也沒寫進掉球清單的事。掉球清單只增不減,結案用 ~~刪除線~~ 加「已結(批NNN)」。
```

## B · 給交接者(離場 AI)——收尾清單(每一條都要有證據路徑)

| # | 收尾 | 證據 |
|---|------|------|
| 1 | 所有改動 commit「批NNN」並 push;工作樹乾淨(`git status --short` 空) | commit hash |
| 2 | `via-vcgc page --publish`:一頁交接 `docs/VIA_Handover_ONEPAGE.md`、倉根 `VIA_HANDOVER_LATEST.md`、頁 `ui_support/VIA_UI_CentralGovernanceConsole_v0100.html` 三處同一份 | ENG082 ⑯ 交接三處 = 同 |
| 3 | 掉球清單 `docs/VIA_DroppedBalls_*.md` 更新(新掛的加、結案的劃線);未做的**寫進去比做一半更重要** | 檔在、ONEPAGE 九段有列 |
| 4 | 台帳 `VIA_AutoCode_Registry_v0100.json` 追記本批(code/kind/ts/name 四欄;indent=1) | 筆數 +1 |
| 5 | 逐批紀錄 `docs/VIA_Handover_*_B*.md` 追加本批段(做了什麼/實錄讀出/你的手/一貼即用) | 段在 |
| 6 | 新引擎七處登冊齊(規格/格子/Register/Deck/Manager/台帳/交接);`via-vcgc audit` 未登冊數不增 | audit 數 |
| 7 | 操作員機器要跑的復原/同步指令寫在回覆的 PS 區塊(例:`via-vrnlogic sync-db` 讓六本庫的 via_policy_factors/via_handover 跟上) | 回覆 |
| 8 | 最後一則回覆:結果 → 你的手(操作員待辦)→ PS 區塊 → 要貼回什麼 | — |

## C · 交接紀錄固定格式(長久使用;人與 AI 都讀得懂)

```
# VIA 交接紀錄 · 批NNN(YYYY-MM-DD)
〇 接手提示詞 → 見 docs/VIA_AI_Handover_Prompt_v*.md(尾版)
一 律(新收到的原文照錄;編號進 VIA_Policy_Laws_SSOT)
二 現況快照(VCGC status 八行原樣貼)
三 本批做了什麼(表:件 / 檔(版號) / 自測 n/n / 證據)
四 實錄讀出(表:你貼的 / 讀出 / 修)
五 掉球清單(表:代號 / 事 / 狀態 未做·候·操作員的手·容器紅 / 誰 / 下一步)——只增不減,結案劃線
六 你的手(操作員待辦:閘/裝件/決策)
七 一貼即用(PS 區塊;前兩行固定)
八 接手驗收(接手者要跑的三個指令與預期輸出)
```

## D · 「多 AI 寫作」的規矩(為什麼要這樣)

- 每個 AI 只活一個對話;**檔案是唯一的記憶**。所以規則、掉球、參數、指令全部要落檔,不留在對話裡。
- 同一判準只寫一處(L05):兩個 AI 各寫一份,第三個 AI 只會改到其中一份。
- 自測不讀自測本身的字串(LL:批504/506 兩次自我引用誤判)。
- 登冊腳本逐檔獨立寫入、失敗要可見(LL09:批505 錨點斷掉只上一半還 commit 了)。
- 判錯的燈和假綠一樣傷(L16):接手者第一件事不是造新件,是把上一位的燈對一遍。

## 一 · 政策庫(律 + lessons-learned)

- **L01**(批475;流程)凡是流程皆要想一個節省 TOKEN 的方式,想好才進行;先查再造,先量再改
- **L02**(批475;註冊)所有紀錄/工具/模組/引擎/功能註冊,除非過時,只增不減
- **L03**(批232;正本)正本零觸碰:references/intake 收容件永不編輯;新版=新收容夾 _bNNN + MANIFEST
- **L04**(批254;版本)尾版律:引擎改動=新版號檔;無版號檔(sitecustomize/JSON 冊)才就地改;glob 取尾版
- **L05**(批403;架構)Zero-Hydra:綁既有引擎不重造;同一判準只寫一處(寫兩處只改一邊=另一邊靜靜走錯)
- **L06**(批390;UI)零 CDN · 零彈窗:頁面自足,沒人要求不跳窗
- **L07**(批478;法遵)同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT / 金鑰)一律操作員自設,我不代設;setdefault 只在未設時給預設;fail-closed
- **L08**(批474;安全)零 force push;不 Stop-Process;不 Remove-Item / conda remove / pip uninstall 環境;--approve-remove 只在明令下;裝套件=操作員的手(--approve + 閘)
- **L09**(批494;工具)加速器與網路工具只認 VeritasCeleritas / VeritasAegisNexus;SUP_MDL737/740 留作橋不直 import;網路件只收不掛線除非走 AegisNexus 車道
- **L10**(批490;資料)資料家律:parquet 存、duckdb 管;家在 C:\Users\tonyk\VIA System\via_database;鏡根 via_database\movies-dataset\data;搬=link(junction,hash 定生死,零刪除)不複製;刪資料=操作員的手;census --hygiene 永無 apply
- **L11**(批493/496;VRN)VRN 擷取次序律:非 OCR 一律先跑(兩法互核)→ 修復 → 驗證;失敗才 OCR 階梯 輕→重(simple→dual→paddle);都失敗才畫質提升 DPI 300~350;成功=資料標示還原+文字修復;成功法入中央邏輯庫
- **L12**(批497;環境)環境隔離律:特殊/中高風險件直接拉出獨立境連同相關工具隔離;numpy 等樞紐件可多境多版本多 Python(H2b);加速器與網路工具的工具很多請勿遺漏(全冊聯集)
- **L13**(批498/500;環境)via_core 白名單律:白名單單一來源 VIA_EnvManager def_PARAM_VIA_CORE_WHITELIST;白名單件才進 via_core(只增);非白名單缺件留置 WHITELIST_HOLD;無家族通用件列 [未路由];HIGH 家族只認同名獨立境不借 alt
- **L14**(批499;資料)全庫同步律:所有的庫政策邏輯因子庫都要同步更新——sync-db 對資料家每本 .duckdb 寫同一份(同一 hash)+ via_policy_sync 對帳單
- **L15**(批499;交接)交接三處律:交接報告在 docs(github)、倉根 VIA_HANDOVER_LATEST.md(母檔案夾)、每本庫 via_handover + 資料家根
- **L16**(批474/498;燈)誠實四態:ABSENT(缺件)/NODATA(缺料)/GATED(閘未開)/RED(壞);判錯的紅燈和假綠一樣傷;缺件≠缺料≠壞掉≠閘未開
- **L17**(批410/504/505;測試)自測零污染律:自測只寫暫存;VIA_SELFTEST=1;自測期間撤 VIA_DB_* 與 VIA_DATA_HOME;真庫永不進自測目標
- **L18**(批482;註冊)功能註冊只增不減:新引擎/工具=規格項、格子站、Register 指令、Deck 任務、Manager 正式名稱、台帳、交接七處齊備;指令與參數不丟失
- **L19**(批506;環境)安裝核可律:環境統一測式(RunGate 家族境 python × 套件探針 × 引擎自測)無誤(GREEN,24h 內)後才可核可安裝;否則 BLOCKED_UNITEST 誠實停
- **L20**(批506;架構)唯一對接口律:Veritas Central Governance Console(CGC_MDL149)為各模組引擎連接系統的唯一對接口,統管政策庫/邏輯庫/因子庫/資料庫/VIA 引擎調度/多矩陣實測結果/註冊表/環境工具/交接
- **L21**(批474;資料)所有 VDF 價格資料皆 adj(除權息調整後);報告上是報告日原始價;兩者不可直接比
- **L22**(批478;SSOT)SSOT 正本 VIA_Financial_Institution_SSOT_v0100.py READ_ONLY 不改;台帳 indent=1、衝突取聯集;VIA_Reports 不入 git;容器空沙盒再生的冊/頁不 commit
- **L23**(批506;倉)倉衛生律:只刪有證據的重複件(byte 同、BACKUP 孿生、__DUP__)與過時再生件;正本/收容件/UI 正本頁/唯一副本不刪;每次刪除附清單與 md5 證據(git 可回溯)

**Lessons-learned**

- LL01(批489/490)49 張 ABSENT 是點錯的燈:庫在倉外的資料家;census 先找家再判缺
- LL02(批491)接點死了不是庫沒了:junction LINKED_ELSEWHERE → --relink,不重建庫
- LL03(批493)paddleocr 3.x 拒收 2.x 參數(show_log)=900 秒 TIMEOUT 根因;相容墊片剝參數重試
- LL04(批499)FirstPageText 卻 OCR 全卷=1138 秒;後端 PASS/0元素、SKIPPED_UNAVAILABLE 都沒記=每件重載 Paddle;只送第 1 頁 + 分境健康全記
- LL05(批500)冊上 db 欄寫「全庫」機器對不上=冊外;對帳單一列一天=假 AMBER;db_scope/lamp 欄補上;via_paddle_311 缺 pymupdf=整批 OCR 轉接器 off
- LL06(批501)階梯用轉接器名、後端矩陣回規格名,兩套名對不上=paddle 三支永遠不在位;判準照抄 adapter.probe 只寫一處;黑底白字要反白
- LL07(批502)本境標壞鍵剔掉車道候選=第三階誤 SKIP;本境鍵與車道鍵分開;零字再試 psm 11→6;錯誤全文 400 字
- LL08(批504/505)自測寫進真庫兩次:全庫同步律讓 sync_targets 掃家與 VIA_DB_*,自測只導向首選庫不夠;自測整段撤 VIA_DB_*/VIA_DATA_HOME + VIA_SELFTEST 旗,並用假 VIA_DB 鍵重現證明零觸碰
- LL09(批505)登冊腳本在一個錨點斷掉=只上一半還 commit 了;每檔獨立寫入、失敗要可見、commit 前對清單
- LL10(批506)倉 560MB pack:ICON_FORGE 1.5GB 含 __DUP__/_vN 孿生、BACKUP 939/944 與正本 byte 同、25MB 巨檔四份同本;刪只憑 md5 證據且不動被引用的檔名

## 二 · 安裝核可(L19)與環境工具

- RunGate:YELLOW · 2026-09-08T19:17:29 · 齡 142.3 h → **BLOCKED_UNITEST**
- 工具冊導入計畫:ABSENT · - · 件態 None · 風險 None · 段 None · 未路由 None · 白名單留置 None(TOOLS_PLAN_latest.json 不在(via-envtools))
- 裝件=操作員的手:`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`(閘不代設;L19 未綠=BLOCKED_UNITEST)

## 三 · 邏輯庫 · 因子庫 · 資料庫

- 邏輯庫 OK:件 2 · 判準 {'SUCCESS': 2} · 壞後端 [] · 政策因子 332 列 · 全庫同步 {'hash': 'ef83a0c2b212', 'counts': {'未入': 1}, 'dbs': 1} · 交接三處 {'doc': 'VIA_Handover_ONEPAGE.md', 'sha': 'ed02df243594', 'root': '同', 'home': '缺'}
- 因子庫 OK:130 列 · {'SUP_MDL748:allinone 2.1.0': 77, 'SUP_MDL748:financial_data_standardization': 53} · 掛載 {'allinone': 'OK VIA_VRNLogic_AllInOne_v0201.py 2.1.0', 'fds': 'OK financial_data_standardization.py · 28 欄 · 合併損傷件(__main__ 示範缺 5 法,程式庫面可用)'}
- 庫表冊 OK:54 表(批505)· 全庫表 4 · 庫 ['ActiveTWETF.duckdb', 'vdf_global_market.duckdb', 'vdf_tw_market.duckdb']
- 資料家 ABSENT:VIA_Reports/datahome/DATAHOME_CATALOG_latest.json 不在(via-datahome catalog) · 庫 None · 表 None · 湖 None

## 四 · 引擎調度 · 多矩陣實測

- 五矩陣 OK:2026-09-14T11:21:39 · 真跑 ['vdf'] · 項 43 · 態 {'GATED': 12, 'NODATA': 5, 'PLAN': 18, 'ABSENT': 2, 'GREEN': 6}
- Deck 任務 64 · 規格項 44 · 格子站 217(在位 217)· Register 指令 109 · Manager 正式名稱 任務 64 / 引擎 81

## 五 · 指令與參數(不丟失;來源 Register-VIA-Commands-v0199.ps1)

- `via-gates`
- `via-envpy`
- `via-status`
- `via-selftest`
- `via-intake`
- `via-help`
- `via-md`
- `via-gle`(別名 版面橋):via-gle=GenericLayoutEngine v2.1.0 全後端統轄橋(SUP_MDL743;status|probe|route)
- `via-nlp`(別名 語意橋):via-nlp=VIA_NLP_Application_System v1.8.0 統轄橋(SUP_MDL744;status|roster|delta|demo)
- `via-allgreen`(別名 統包):批423(操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」):via-allgreen=統包全流程尾版啟動器。
- `via-prompt`
- `via-analysis`
- `via-manager`
- `via-rootcheck`
- `via-tower-reset`
- `via-ssot`
- `via-register`
- `via-health`
- `via-tpn`
- `via-psrepair`
- `via-all`
- `via-accel`
- `via-accel-import`:via-accel-import [--env-root <envs 根>] [--apply --approve] [--include-base] [--timeout N] [digest]
- `via-accel-check`
- `via-rotation`
- `via-repo-optimize`
- `via-vapstack`
- `via-pstest`
- `via-oneshot`(別名 一鍵)
- `via-unstick`(別名 解卡)
- `via-psrepair-ast`(別名 語法修)
- `via-copies`
- `via-medic`
- `via-reload`
- `via-plotlaw`
- `via-system`:批332:系統總台=六主體標準 U/I(VIA 首頁所有擷取資料/VDF/VAP/主動 ETF 分類/族群輪動/月營收);via-system 再生頁並開啟(樞紐在線=LIVE;否則 SNAPSHOT 誠實);via-api <主體> 印後端 JSON
- `via-api`:批332:系統總台=六主體標準 U/I(VIA 首頁所有擷取資料/VDF/VAP/主動 ETF 分類/族群輪動/月營收);via-system 再生頁並開啟(樞紐在線=LIVE;否則 SNAPSHOT 誠實);via-api <主體> 印後端 JSON
- `via-master`:批333:總控台=Codex 設計正本(VIA_SYSTEM_MANAGER 尾版 ui 再生)由樞紐同源 /master 供應(CSRF 權杖注入;file:// 唯讀預覽自動導同源);via-master=再生頁+開 /master(樞紐未起先打 via)
- `via-intake-roster`:批336:上船件冊=references/intake 全收容包 × 整合鏈(引擎/頁/短令/任務)頁;via-intake-roster --open
- `via-complete`:批344:via-complete watch=重接最新 LAUNCH log 直播(Ctrl-C 只離開);via-complete stop=依最新 RUN_*/PROGRESS.json 停 MDL121 本體+當前步子程序(工人 Ctrl-C 免疫後唯一停止法)
- `via-datahome`(別名 資料家/庫目錄):批490:操作員宣告資料家 C:\Users\tonyk\VIA System\via_database(parquet 本體 + duckdb 管家);via-datahome catalog [-Tables]=家內清點→一頁目錄;via-datahome plan=倉內散落整併計畫(只列不動)
- `via-fixall`:批350:紅站一鍵補齊鏈(MDL125:datahome 接點→OpenCC 輔助安裝→global 全球擷取→consensus/revenue_consensus→--refail 複驗;NET 步雙同意閘;誠實三態;心跳進度條);via-fixall=印步冊;via-fixall run [--only a,b] [--dry]
- `via-mobile`:批366:操作員令「不要一直跳出 VS Code,自動到底完成所有動作」→ via-mobile 全程 VIA_NO_OPEN=1(SUP_MDL737 v0104 py 閘+PS-ACCEL 模組 PS 閘;所有頁面只落檔不跳出;結束後 via-open 可看);--open 覆寫
- `via-netbench`:批353:網路車道時段基準(操作員令「先測一些時段」;chart/chart×N(accel_map)/yf 三車道同標的同時段實測秒數與成功率;零入庫;親跑=同意);via-netbench [--tickers 2330,2317] [--days 60] [--workers 4] [--pause 0.35]
- `via-fred`:批360/361:FRED 宏觀 SSOT 擷取(ENG074;macro_ssot 190 series 從新往舊;checkpoint;accel_map+節流;parquet+DuckDB us_macro+polars 鏡;落 output_hub/mega=接點→本機資料家;鑰缺=當場輸入;親跑=同意);via-fred [run|status|lamps] [--since 1990-01-01] [--workers 4]
- `via-revfill`:批368:月營收全市場史深回補(ENG075;MOPS t21sc03 上市/上櫃 國內/KY 月檔 2023-01→ 從新往舊;Big5;只增 anti-join;checkpoint;親跑=同意);via-revfill [run] [--since 2023-01] [--workers 3] [--max-months N] | status;(名 via-rev 讓位另線工作站別名=先發先得)
- `via-ves`:批371:VES 橋(MDL132)=尾版鏡像(史版不當多頭)→第 1 跑→安全種子決策(VIA 動詞冊/橋塊 REJECT/selftest 群 REJECT;append-only)→第 2 跑確定性套用;唯讀;--apply 永不經短令;via-ves [--root <相對子樹>] [--no-seed] [--single];via-ves --raw <VES 原生參數…>(直通收容原件,如 --slice <碼>)
- `via-etfhist`:批375:主動 ETF 每日持股史深覆蓋+缺口回補(ENG078;IPO 起應有交易日 vs 快照;車道冊 VIA_ActiveETF_HistoryLanes VERIFIED 才呼;缺源=NO_SOURCE 誠實;親跑=同意);via-etfhist [daily [--offline] [--max-days N] | backfill | status]
- `via-etfuniv`:批374:主動 ETF 宇宙日更(ENG077;A 碼律 ^\d{5}A$ + 國內成分揭露律;TWSE 官方冊→etf_book 後備→既有聯集只增;寫 ENG051 SSOT csv;親跑=同意);via-etfuniv [run [--offline] | status]
- `via-etfrev`:批373:主動 ETF 持股×月營收動能(ENG076;兩專案合流層;零網路;加權 yoy/重疊榜;頁 VIA_UI_ETFRevenueMomentum);via-etfrev [run|status]
- `via-autorun`:批379/380:via-autorun=一鍵全自動四閘版:①via-accel --activate(20 加速器)②via-lanes plan(Hydra 哨兵 H1–H6;H3/H5 FAIL=誠實停)③via-mobile --lanes(拉齊→六流程→十道並行→矩陣→產品閘)④lanes digest;零跳出、零 TTY 等待(VIA_FRED_PROMPT=0)、逾時 kill 不卡斷;雙擊 via-autorun.cmd
- `via-open`:批378:via-open <片段|路徑>=只走瀏覽器可執行檔(Edge/Chrome/Firefox 依序),永不經 .html 預設程式(VS Code);缺瀏覽器=印路徑。別名:產品→ProductGate 竣工→ProjectCompletion 架構→VDFArchitecture 道→ParallelLanes 總控→MasterControl
- `via-vdffetch`:批381/383:via-vdffetch [年份] [--limit N] [--dry]=單一指令抓該年以後全部 VDF 資料(預設 2023)。
- `via-lanes`
- `via-productgate`:批376:產品資格閘(MDL133;九閘 G1 矩陣存證/G2 短令↔梭/G3 樞紐任務/G4 頁衛生/G5 再生物讓位/G6 鑰匙守衛/G7 引擎尾版/G8 短令在位/G9 用法;QUALIFIED/CONDITIONAL/NOT_QUALIFIED 永不假綠);via-productgate [build --open | digest | --json]
- `via-projects`:批368:四專案完工矩陣(MDL131;VDF/VRN/主動 ETF/月營收 × grid 存證 × DuckDB 深度 × 任務/頁/令;RYG+下一指令;八段循環證據);via-projects [build --open | digest]
- `via-vdfarch`:批360:VDF 資料架構(ENG073;SSOT 12 類→現役表/引擎/車道對映;DuckDB 盤點;--optimize dry-run 只增不減;--go 才寫;頁 VIA_UI_VDFArchitecture);via-vdfarch [build --open | --optimize [--go]]
- `via-superhtml`:批352:VIA SuperHtml Parser(HTML content+UI component+JS/CSS logic+backend→Markdown;bs4/lxml/esprima/tinycss2/markitdown;NLP OneEngine v1.5.0 語意橋;自建根 C:\VIA\VeritasSuperHtmlParser);via-superhtml <路徑...> [-NoOpen] [-NlpSour
- `via-bridge-sweep`:批345:橋塊掃描/注入(ACCEL-BRIDGE 全樹/NET-BRIDGE VDF;預設 dry-run;--apply 才寫;排除冊=獨立工具不可動/凍結群/收容原件/退役);via-bridge-sweep [--net] [--accel] [--root <rel>] [--apply]
- `via-six`:批354:via-six 正主=CGC_MDL127_SixStreams(py;九子行程並行;A01–A20 加速器燈;dry-run 預設;--go 只放行 S1);via-six --ps=退 Invoke-VIA-SixStreams ps1 後備
- `via-charter`
- `via-loop`:批354:系統結構總冊(MDL128;七域+治理核;--probe --days 2 兩日試鏈)/生命週期 RACI(MDL129;via-loop=≤25 行 digest)/UI 橋接整合台(MDL130;spec+template→VIA_UI_Consolidated;VHUIRE 品質閘)
- `via-ui`
- `via-pipeline`
- `via-envgov`:批381:環境治理統一引擎(MDL135):①全景式分析 base+via_core*+via_*/paddle*/camelot*(平行探針硬逾時不卡斷)②uv pip check 毫秒快篩(退 pip)③base 該有冊(Baseline 冊:工具鏈+引擎核心+LOW)+相依閉包=該有;閉包外=拉出候選 ④衝突要求者家族整包路由(via_core 白名單→家族 target_env(如 OCR→paddle_312 contrib 
- `via-envgov-auto`
- `via-envtools`(別名 工具導入):via-envtools [-Apply] [-Approve] [-Env via_vrn_312] [--env-root P] ;讀工具冊 VIA_ToolRoster_SSOT_v*.json,逐境探針→修復/安裝/外部/驗證
- `via-entry`:via-entry plan=一貼即用 11 步;via-entry roster=短令冊(母倉∪Grok 撞名冊);--scan 加跑 via-envgov 全景;--open 開矩陣頁(瀏覽器道零跳出);--console 帶起 Grok 網頁主控台(背景)
- `via-env`:批383:via-env=環境治理正本(MDL135 via-envgov;Grok 版 39 行樁改名 via-env-grok 留冊);via-grok=Grok 短令冊(load 重載;matrix 開 WPF 右側板)
- `via-grok`:批383:via-env=環境治理正本(MDL135 via-envgov;Grok 版 39 行樁改名 via-env-grok 留冊);via-grok=Grok 短令冊(load 重載;matrix 開 WPF 右側板)
- `via-webconsole`:批383:via-webconsole=Grok 網頁主控台(收容包 b383;TanStack/Vite;npm run dev 0.0.0.0:8080):node_modules 缺=須 npm install 觸網→ --install 或 $env:VIA_NET_CONSENT="YES" 同意閘;--background 另窗最小化(關窗即停;不 Stop-Process)
- `via-vapone`:批383:via-vapone=VAP ONE 單檔整合引擎(VAP_ENG016;圖規 SSOT 40/圖規鎖/批330 資料律/零依賴 SVG+Plotly+Matplotlib 車道;無參數=--selftest;via_vap_312 python 優先=全車道)
- `via-vdfdb`:批383:via-vdfdb=本機三庫整併入正典 DuckDB(VDF_ENG079;C:\新增資料夾\新增資料夾\VIA_db_part1_prices/part2_chips/part3_rest;COPY_ONLY anti-join 只補缺鍵;檔冊 sha 已入=跳過;ckpt=ENG064 checkpoint 重建=抓過不再抓;need=缺口清單);無參數=scan 唯讀;run --apply 才寫
- `via-rungate`:批384:via-rungate=VDF/VRN/VAP 能跑閘(MDL137):家族境 python 逐庫 import + SelftestGrid 家族站真跑(--fast 每族 3 站;預設 8;--all 全站;--family vdf,vrn,vap;status 看上次);via-py <family> <script.py> [args]=通用家族啟動器
- `via-py`:批384:via-rungate=VDF/VRN/VAP 能跑閘(MDL137):家族境 python 逐庫 import + SelftestGrid 家族站真跑(--fast 每族 3 站;預設 8;--all 全站;--family vdf,vrn,vap;status 看上次);via-py <family> <script.py> [args]=通用家族啟動器
- `via-vrn4`:批386:via-vrn4=研報一題四點文摘+潛在上漲空間(VRN_ENG080;目標價除權息同口徑後向因子鏈;最新 adj close;quote-or-abstain);無參數=run;show <ticker|report_file>;--ticker/--limit
- `via-famui`:批388:via-famui=家族 U/I 再生閘(MDL138):以家族境 python 真跑 VDF/VRN/VAP 頁面產生器→頁新鮮/零 CDN 判準→索引 FAMILY_UI_latest.html;--open 只走 via-open 瀏覽器道;--no-build 只驗頁;via-vdfui/via-vrnui 別名
- `via-vdfui`:批388:via-famui=家族 U/I 再生閘(MDL138):以家族境 python 真跑 VDF/VRN/VAP 頁面產生器→頁新鮮/零 CDN 判準→索引 FAMILY_UI_latest.html;--open 只走 via-open 瀏覽器道;--no-build 只驗頁;via-vdfui/via-vrnui 別名
- `via-vrnui`:批388:via-famui=家族 U/I 再生閘(MDL138):以家族境 python 真跑 VDF/VRN/VAP 頁面產生器→頁新鮮/零 CDN 判準→索引 FAMILY_UI_latest.html;--open 只走 via-open 瀏覽器道;--no-build 只驗頁;via-vdfui/via-vrnui 別名
- `via-console`:批390:via-console=輸入主控台(MDL139 左輸入/右矩陣;零 CDN):無參數=build 頁;status [--json];set k=v…(tw-add=2330:TWSE start=<item>:YYYY-MM-DD|latest days=<item>:N macro-cats=Business,Prices fin-period=累計 fin-from=2022 vrn-dir=<夾> vap-code=
- `via-handover`:批392:via-handover=接棒狀態台(MDL140):超詳細系統狀態分門別類堆疊矩陣一頁(git/PR/環境治理/能跑閘/家族 U/I/樞紐任務/庫狀況/對齊/本機三庫/VRN 跑況/VAP 產出/日更鏈/候操作員/次步)+ HANDOVER_latest.md(可轉 MD 接棒);無參數=build;status|md;--open=樞紐在線開 LIVE /handover 否則快照頁
- `via-align`:批390:via-align=台股每日交易資訊×籌碼 數量對齊與股票清單更新(VDF_ENG081;vdf 境 python):check [--days N](逐日核對 ALIGNED/PARTIAL/MISALIGNED;差集清單)| update [--apply](最新日 價∪籌碼 ∩ 冊 → tw_universe anti-join 只增 + parquet 增量)| status
- `via-bg`:批393:via-bg=背景引擎進程一覽(唯讀;工作站實錄:via-align 撞 DuckDB 單寫者鎖時 [FAIL] 句指路「via-status」,但 via-status 開的是同步頁不是進程表)。
- `via-chip`:批394:via-chip=籌碼增量(VDF_ENG056:run [--days N] | --derive | --status);via-price=價格增量(VDF_ENG054 v0101 增量律:依各標的 MAX(date) 只抓缺口;run [--limit N] [--full] | --status);
- `via-price`:批394:via-chip=籌碼增量(VDF_ENG056:run [--days N] | --derive | --status);via-price=價格增量(VDF_ENG054 v0101 增量律:依各標的 MAX(date) 只抓缺口;run [--limit N] [--full] | --status);
- `via-tw-backfill`:via-tw-backfill=ENG054 docstring 原名別名。同意閘同 via-fred(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT=YES);以 via_vdf_312 python 啟動;撞單寫者鎖=引擎自身庫鎖律誠實停。
- `via-closeout`:批398:via-closeout=收尾閘 MDL141(VRN 驗證收尾 VAL:報告夾每一份 收件→首頁→入庫→財報頁→四點 + TAB2/TAB4 核對態 → DONE|FAIL|PENDING;VAP 產出收尾:逐圖驗 SVG/PNG/HTML/PDF+零 CDN+台帳)
- `via-vrnin`:拖曳仍走同夾的 via-vrnin.cmd(檔案總管不把拖曳路徑傳給 .ps1,只傳給 .cmd)。
- `via-bus`:via-bus one vrn_firstpage    只跑點名的那一項(**寫庫動詞只認這條路**)
- `via-busui`
- `via-ryg`(別名 紅黃綠/燈板)
- `via-vrnuni`(別名 統一報告):via-vrnuni -SelfTest | via-vrnuni --in <報告夾或 pdf> --out <夾> [--official-listings <csv>] [--csv --json --duckdb]
- `via-vrnlogic`(別名 邏輯庫):via-vrnlogic [status|reset-backends] | -SelfTest ;台帳 VIA_Reports\vrn\extraction_logic\(只增)
- `via-finlogic`(別名 財務邏輯):via-finlogic [status|opinion <科目名>|rating <字>] | -SelfTest ;第二意見只註記不改 canonical(登錄進 SSOT=你定);政策因子隨 via-vrnlogic sync-db 入庫
- `via-finstat`(別名 三大報表):via-finstat [run|status|-Dry] [--only 2330,2317] [--limit 5] [--years 5] ;run 前 $env:VIA_NET_CONSENT='YES' + VIA_SCRAPE_CONSENT(你的手;我不代設)
- `via-vcgc`(別名 中央控管):via-vcgc [status|page|onepage|audit|register-plan|check] [--publish] | -SelfTest ;page/onepage 落 VIA_Reports\vcgc(--publish 才入倉三處);check=L19 安裝核可(RunGate GREEN 24h 內)
- `via-firstpage`(別名 首頁擷取):via-firstpage:首頁三法擷取器 ENG072 尾版直呼(-Force 忽略邏輯庫命中整批重抽;-RetryFailed 只重試 FAIL 件;-OcrBudget N 每件 OCR 預算秒;--in 檔/夾可重複)
- `via-census`(別名 庫況/庫衛生):批485:via-census -Hygiene = 庫衛生唯讀審計(哨兵列 1900-01-01 數出來 + DELETE 只寫不跑;_repo_ 副本 vs 正庫 MAX 日期);零寫入
- `via-boot`(別名 啟動層):批476:via-boot=啟動層實證:每個家族真的起一個子行程,印它看到的(加速器 | 網路件 | via_net 可 import | 同意閘)
- `via-vetf`(別名 共識擴充):via-vetf -Factset <檔> -Yfinance <檔> -AsOf 2026-09-12 -Holdings <庫::表> -Prices <庫::表>
- `via-twrev`(別名 月營收):via-twrev [selftest|demo|analyze|report|groups|breakout|fetch|run]   預設 selftest
- `via-revphase`(別名 營收相位):via-revphase -SelfTest  合成 36 期自測(免庫免網路)
- `via-etfhold`(別名 持股日更):via-etfhold             日更真跑:根=你的 output_hub\active_tw_etf(自 VIA_ROOT 推);觸網→只看同意閘,不代設
- `via-ppp`:via-ppp -Open              跑完把 HTML 報告叫出來(零彈窗律:預設不跳)
- `via-vrnval`
- `via-vapval`
- `via-deadends`:批400:via-deadends=短令死路掃描器(MDL136 deadends):掃引擎 docstring/[FAIL] 句/docs/README 內 via-* 令,對照短令冊+梭;未登錄=死路(批394 via-chip/批396 via-rebuild 同類);落 VIA_Reports/entry/DEADENDS_latest.json;--json/--quiet
- `via-pin`:--show 只看(本窗副本 vs profile 預設副本,各印分支/HEAD);只改 profile 一行,兩副本檔案零觸碰;換回=到另一副本的視窗再 via-pin。pwsh 與 Windows PowerShell 各有 $PROFILE,各自 via-pin 一次。
- `via-rebuild`:無參數=--offline(只 ①~④+⑦ 唯讀計畫;零網路);via-rebuild --env <境>=只治理單一環境(② 起需網路;無網路段誠實 NOT_RUN);--selftest 十四檢。base python(MDL050 自管 uv)。

## 六 · 註冊稽核(所有引擎/模組/工具都要註冊)

- 引擎家族(尾版)227 · 已登冊 187 · **未登冊 40**
  - CGC_MDL001_CentralGovernanceEngine_v0401.py(supportive modules/VIA_Central_Governance)
  - CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE_v0611.py(supportive modules/registry)
  - CGC_MDL036_BuildPkgPointers_v0100.py(supportive modules/registry)
  - CGC_MDL037_BuildSpecMaster_v0100.py(supportive modules/registry)
  - CGC_MDL038_BuildSubsystemPages_v0102.py(supportive modules/registry)
  - CGC_MDL039_BuildViaMother_v0105.py(supportive modules/registry)
  - CGC_MDL042_AutoPilot_v0103.py(supportive modules/registry)
  - CGC_MDL043_AutocoderEngine_v0100.py(supportive modules/registry)
  - CGC_MDL051_EnvmgrNostall_v0100.py(supportive modules/registry)
  - CGC_MDL052_EnvmgrRouter_v0101.py(supportive modules/registry)
  - CGC_MDL053_GovernanceConsole_v0100.py(supportive modules/registry)
  - CGC_MDL055_InputPrecheck_v0100.py(supportive modules/registry)
  - CGC_MDL060_NumberEngine_v0100.py(supportive modules/registry)
  - CGC_MDL063_RegistryUnionmerge_v0100.py(supportive modules/registry)
  - CGC_MDL065_SsotEvolve_v0100.py(supportive modules/registry)
  - CGC_MDL067_SupportBridgeInject_v0101.py(supportive modules/registry)
  - CGC_MDL070_T0Audit_v0100.py(supportive modules/registry)
  - CGC_MDL074_AccelBridge_v0100.py(supportive modules/registry)
  - CGC_MDL116_UnifiedShell_v0114.py(supportive modules/registry)
  - CGC_MDL147_EngineSmokeGate_v0101.py(supportive modules/registry)
  - SUP_MDL015_VISVRNBrokerAliasFullList_v0100.py(supportive modules/70_VRN_Rules)
  - SUP_MDL030_VISVRNTickerFilenameSSOT_v0100.py(supportive modules/70_VRN_Rules)
  - SUP_MDL031_VISVRNTickerRegexShim_v0100.py(supportive modules/70_VRN_Rules)
  - SUP_MDL606_AkshareBackupRollbackStagingPlan_v0283.py(supportive modules/network)
  - SUP_MDL607_AkshareCandidateSeedStaging_v0274.py(supportive modules/network)
  - SUP_MDL608_AkshareCandidateStagingFinalAudit_v0275.py(supportive modules/network)
  - SUP_MDL612_AkshareExecutionReadinessReview_v0279.py(supportive modules/network)
  - SUP_MDL619_AkshareSampleCallGate_v0272.py(supportive modules/network)
  - SUP_MDL621_AkshareSignatureDocProbe_v0271.py(supportive modules/network)
  - SUP_MDL623_AkshareSmallScopeSeedPlanGate_v0273.py(supportive modules/network)
  - SUP_MDL624_AkshareUserApprovalGateWriteStageDesign_v0281.py(supportive modules/network)
  - SUP_MDL625_AkshareWriteDryrunCompare_v0282.py(supportive modules/network)
  - SUP_MDL626_FredAkshareCapabilitySealProbe_v0241.py(supportive modules/network)
  - SUP_MDL628_MopsMonthlyRevenueFinalValidator_v0221.py(supportive modules/network)
  - SUP_MDL633_TpexSmallScopeValidator_v0211.py(supportive modules/network)
  - SUP_MDL635_TwseOfficialSeedValidator_v0181.py(supportive modules/network)
  - SUP_MDL637_YfinanceSeedValidator_v0171.py(supportive modules/network)
  - VRN_ENG079_ControlTowerDashboard_v0100.py(functional modules/VRN)
  - VRN_ENG081_ParquetMainDB_v0100.py(functional modules/VRN)
  - VRN_OperatorRegex_TWTicker_v0100.py(functional modules/VRN)

## 七 · 自動編號註冊表(台帳)

- 台帳 1042 筆 · 元件 147 · 更新 2026-09-14
- 類別 current:系統 1 · 支援性工具 1 · 功能性工具 1 · 模組 1 · 引擎 19 · 函數庫 1 · 打包產品 8

- 2026-09-14 18:00 批502 實錄修:車道候選鍵分離 + 階梯派送判準 + psm 階梯 + 錯誤全文
- 2026-09-14 18:30 批503 收尾:首頁擷取 64/64;法計數歸一
- 2026-09-14 19:40 批504 財務邏輯橋(AllInOne+FDS 只掛不搬)+ 自測零污染律 + 五件上傳量測
- 2026-09-14 20:30 批505 vrn_logic 站 RED 根因修(自測隔離)+ 三大報表引擎上船(填缺席)+ 實測 vdf/vrn/vetf 指路
- 2026-09-14 22:10 批506 倉衛生 + 政策庫 + VCGC 唯一對接口 + L19 安裝核可 + 一頁交接
- 2026-09-14 17:32 批507 AI 交接提示詞 / 固定格式 / 掉球清單 / VCGC 〇九段

## 八 · 交接本文(來源 VIA_Handover_20260914_B498.md;逐批紀錄見該檔)

### 三 · 還掛著的事

| 代號 | 事 | 卡在哪 |
|------|----|-------|
| **A** | 姊妹倉 `tonykuni/VIA-VDF-VRN` 同步 | 工具層權限(聊天授權 ≠ 工具授權)。 |
| **D** | 批416 F2 逐家投信 PCF 端點查實 | 需網路 + 同意閘;**閘由操作員自己設**。 |
| **G** | VRN_MDL 數量 300 vs 294 | 同一把尺再量,先記不判。 |
| **I** | VDF SSOT 化 | 冊 + census 對冊比在;`_repo_` 副本庫(P)哪本是正本要冊講。 |
| **P** | `vdf_tw_market_repo_a7752b3` 等副本庫與正庫並存 | 三副本病;`via-census -Hygiene` 只數不刪;刪=他的手。 |
| **R** | ENG072 起手 140 秒靜默(GLE 探 7 個 OCR 後端) | 後端健康已入邏輯庫(BROKEN/OK 24h);GLE 探測本身仍未快取。 |
| **S** | 資料家第二步:parquet 本體 + duckdb VIEW 匯出/接點 | `via-datahome catalog/plan/link` 在;要不要把 31 處散落件 link 進鏡根=他決定。 |
| **T** | `via-vrnuni` 官方名冊 CSV(`tw_listings` → code/name/yf_ticker/industry) | 小橋,未做。 |
| **U** | **VDF 正境:`via_vdf`(登錄,py3.12)還是 `via_vdf_312`(實為 3.13.7,未登錄)** | 治理問題,不是技術問題;工具冊目前路由到 `via_vdf_312`。他一句話定案後改冊。 |
| **V** | via_vap_312 pyarrow 半拆 / seaborn 缺;Tesseract `chi_tra`、easyocr 模型檔 | 全是「裝」——`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`,他的手。 |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件要用新次序重抽~~ | **已結(批503)**:64/64 抽齊,候OCR 0;最後一件 57 頁深底簡報反白 + psm 11 讀出 124 字。 |
| **X** | 容器 ENG072 ⑤ 空夾誠實 rc2 | 容器舊紅(v0116 基線同紅);操作員機器上未見紅。 |
| **Y** | 「Table … does not exist」現在是 NODATA 不是 RED | 若他機器上該表本應存在(冊上有)而燈是 NODATA,那是缺料燈點對了、料真的缺——去查 `via-census -Tables`。 |

---

### 四 · 紀律(每條都付過代價)

1. 先查再造 / 先量再改;判錯的紅燈和假綠一樣傷。
2. 缺件 ≠ 缺料 ≠ 壞掉 ≠ **閘未開**(批498 起四態:ABSENT / NODATA / RED / GATED)。
3. 只增不減 · 正本零觸碰(`references/intake/` 不編輯)· 尾版律(引擎改=新版號檔;無版號檔如 `sitecustomize.py`/JSON 冊才就地改)· Zero-Hydra · 零 CDN · 零彈窗。
4. 同意閘(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` / 金鑰)**一律操作員自己設,我不代設**;`Set-VIAGateDefaults`/`setdefault` 只在未設時給預設。
5. 零 force push · 不 `Stop-Process` · 不 `Remove-Item`/`conda remove`/`pip uninstall` 環境 · `--approve-remove` 只在明令下 · 裝套件=他的手(`--approve` + 閘)。
6. **加速器與網路工具只認 VeritasCeleritas / VeritasAegisNexus**(批494 令);737/740 留作橋。via_core 白名單境永不排裝非白名單件。
7. 資料:parquet 存、duckdb 管、家在 `via_database`;搬=link 不複製;刪=他的手;`census --hygiene` 永無 apply。
8. `VIA_Reports/*` 不入 git;**容器空沙盒再生的冊/頁不 commit**(VDFArchitecture 冊、VDF/Vap 架構頁、可編輯模板)。
9. SSOT 正本 `VIA_Financial_Institution_SSOT_v0100.py` READ_ONLY 不改;台帳 `VIA_AutoCode_Registry_v0100.json` indent=1,衝突取聯集。
10. VDF 價格皆 adj;報告價是原始價;不可直接比。
11. 新引擎/工具=功能註冊只增不減(規格項、格子站、Register 指令、Deck 任務、Manager 正式名稱、台帳、交接)。
12. commit 訊息 `批NNN:…`;倉內產物不放模型識別字。我不 merge、不 approve PR。

---

### 五 · 一貼即用(操作員工作站)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-boot                          # ① 每家族應印「工具:Celeritas(lazy);AegisNexus(lazy)」+ 資料家 VIA_DB_*
via-envtools                      # ② 工具冊導入計畫(唯讀):看 [未路由]/[白名單留置]/[樞紐]/[風險];貼回來
via-firstpage -RetryFailed        # ③ 只重試上次 FAIL 的 8 件(非 OCR→驗證→輕 OCR→重 OCR→DPI 300~350;派送 via_paddle_311)
via-vrnlogic                      # ④ 邏輯庫現況(法/後端健康);跑完 ③ 應多出新法、後端有紀錄
via-vrnlogic sync-db              # ⑤ 邏輯因子政策入庫(vrn_extraction_logic / via_policy_factors)
via-census -Tables                # ⑥ 兩張新表應在 vdf_tw_market.duckdb 列出
via-ryg -Timeout 300              # ⑦ 五矩陣燈:紫=GATED(閘未開,不是壞);紅才是要修的
# 你決定要裝時才跑(裝前 freeze 存證;我不代設閘):
# $env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve
```


## 九 · 掉球清單(來源 VIA_DroppedBalls_B507.md;列 24 · 未結 23;只增不減,結案劃線)

# VIA 掉球清單(漏球審計)· 批507(2026-09-14)· 涵蓋 批474–506

> 律:操作員說過、沒做也沒寫進這裡=掉球。只增不減;結案用 ~~刪除線~~ 加「已結(批NNN)」。狀態:未做 / 候(等操作員裁) / 操作員的手(閘·裝件·決策) / 容器紅(容器沒料,他機器綠或未驗)。

| 代號 | 事 | 狀態 | 誰 | 下一步 |
|------|----|------|----|--------|
| A | 姊妹倉 tonykuni/VIA-VDF-VRN 同步 | 候 | 工具層權限 | 操作員在工具層授權後再做 |
| D | 批416 F2 逐家投信 PCF 端點查實 | 操作員的手 | 需網路+閘 | 開閘後跑 ENG078 sync |
| G | VRN_MDL 數量 300 vs 294 | 未做 | AI | 同一把尺再量 |
| I/P | VDF SSOT 化;`_repo_` 副本庫哪本正本 | 候 | 操作員 | 冊講明後 census 對冊 |
| R | ENG072 起手 GLE 探 7 後端 140 秒未快取 | 未做 | AI | 探測結果落 24h 快取 |
| S | 資料家第二步:31 處散落件 link 進鏡根 | 候 | 操作員 | `via-datahome plan` 核准後 link |
| T | via-vrnuni 官方名冊 CSV 橋 | 未做 | AI | tw_listings → code/name/yf_ticker/industry |
| U | VDF 正境 via_vdf(登錄 py3.12)vs via_vdf_312(3.13.7 未登錄) | 候 | 操作員 | 一句話定案後改工具冊 |
| V | via_vap_312 pyarrow 半拆/pandas/seaborn;via_paddle_311 paddlepaddle(paddle_ppstructure 相依錯)、easyocr 模型檔;Tesseract 已有 chi_tra | 操作員的手 | 閘+Approve | `via-rungate` → `via-vcgc check` → `via-envtools -Apply -Approve` |
| X | ENG072 ⑤ 空夾誠實 rc2 | 容器紅 | — | v0116 基線同紅;他機器未見紅 |
| Y | 「Table … does not exist」現為 NODATA | 已改(批498) | — | 冊上有而缺料=查 census -Tables |
| Z1 | VRN PARTIAL 16 件(互核一致但標示未全還原;操作員律第二句) | 未做 | AI | 逐件看 labels_ok=False 的 repair 紀錄;決定要不要追=操作員 |
| Z2 | 未登冊引擎家族 40(VCGC audit) | 候 | 操作員核准 | `via-vcgc register-plan` 清單;核准後逐支登站 |
| Z3 | 倉衛生未刪八類(ICON_FORGE 餘量 1.1GB、SCOPE_COPY、安裝器三版、ui_support 大頁、.dup.csv、跑批產出、收件夾、sha701 巨檔副本) | 候 | 操作員 | 逐類定案;刪必附證據 |
| Z4 | MOPS 三大報表解析(收容件自述 brittle;ENG082 只探路) | 未做 | AI | 有真回應樣本後再寫解析;`tw_financial` 現靠 yfinance 車道 |
| Z5 | fin_statements 真抓未驗(via_vdf_312 有無 yfinance?閘?) | 操作員的手 | 閘 | `via-finstat -Dry` → 開閘 `via-finstat run --only 2330,2317` 貼回 |
| Z6 | vdf/vetf 真跑未驗(容器無料;矩陣預設只跑 vrn,vap) | 操作員的手 | 閘 | `via-ryg vdf,vrn -Timeout 600` + `via-vetf`,`via-bus tails` 貼回 |
| Z7 | ENG074 ⑬ 三方對照夾具(NO_TICKER/NO_DATE) | 容器紅 | — | v0106 基線同紅;他機器批466 曾 18/18;若他機器也紅=AI 修 |
| Z8 | 格子 3 站 present=False(ChipWar 編譯檢、TWREV 編譯檢=PYCODE 特殊站;selftest grid 自指) | 非掉球 | — | VCGC v0101 標「特殊」不當缺 |
| Z9 | ENG074 公式檢(AllInOne validate_formulas)未接進 crosscheck | 未做 | AI | 加 dimension=formula 列(PASS/FAIL) |
| Z10 | 五本真庫政策表曾被自測污染兩次(批504/505) | 已修(批506 ENG082 v0107) | 操作員復原 | `via-vrnlogic sync-db` 一次;`via-vrnlogic` 應 同步 6 |
| Z11 | 主控台冊 GOV 類治理任務只在 Deck,不在規格冊 families | 未做 | AI | 規格冊加 gov 家族或 VCGC 頁直接列(現已列 Deck 64 任務) |
| Z12 | MasterControl 總控頁未隨 Manager v0124–v0126 再生(容器再生會覆蓋真頁;L22) | 操作員的手 | — | 他機器 `via-manager` 再生一次 |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件重抽~~ | 已結(批503) | — | 64/64 |

