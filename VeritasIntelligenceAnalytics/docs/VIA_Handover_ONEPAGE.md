# VIA 一頁交接 · Veritas Central Governance Console(VCGC v0104 · 批511)

> 產生 2026-09-15 07:31:10 · 唯一對接口(律 L20):政策庫 · 邏輯庫 · 因子庫 · 資料庫 · 引擎調度 · 多矩陣 · 環境工具 · 註冊表 · 交接。動態段(矩陣/RunGate/工具計畫/資料家)以**你機器上最新一次 `via-vcgc onepage`** 為準;倉內這份是 commit 時的快照。

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
0. 對齊遠端(L25 多 AI 交會律):git fetch origin claude/via-envmanager-governance-7cls8h; git status --short; git log --oneline HEAD...origin/claude/via-envmanager-governance-7cls8h
   落後→ git pull --ff-only;本機有別的線(未推的 commit/未追蹤的新版號檔)→ 先 commit 到側枝 local/parallel-B<批> 並 push,再對齊;永不在陳舊樹上造件。
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
   VCGC=$(ls "supportive modules/registry"/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | sort | tail -1)   # 尾版律:永遠拿最新版號
   python3 "$VCGC" status
   python3 "$VCGC" --selftest
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

0. push 前 git fetch 再比對(HEAD...origin 無分歧);新版號檔要先看遠端有沒有同名(撞名=另一條線在跑,見 L25/LL13)。

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
- **L24**(批508;環境)環境復原律:環境安裝出了問題 → ①先還原前次環境(LKGC lock 逐境;無 LKGC 則 Baseline 原本規劃;sync 破壞段只在 --approve-remove)②再把所有工具順序裝上(core 白名單→LOW 家族境→MEDIUM 隔離境→HIGH 隔離境→外部本體→驗證)③中高風險(_M/_H 家族)一律單獨隔離境,不借 alt 境;plan 唯讀,--execute --approve 才跑,同意閘不代設;①不受 L19 擋(LKGC 本身即曾 GREEN),②新裝段仍過 L19
- **L25**(批509;交接)多 AI 交會律:每個工作階段第一步 git fetch + git status + git log HEAD..origin 比對;落後就先 pull --ff-only 再造件;本機/另一 AI 的並行線一律先 commit 到側枝並 push(local/parallel-B<批>),再把工作分支對齊遠端;只由一隻手併(併時只增不減:版本檔名撞名者高版號另起,律/台帳/掉球清單取聯集);永不在陳舊樹上造件、永不 force push
- **L26**(批511 併線(並行線 批508 panorama-v0103);中央治理)全景修復與調度只由VCGC呼叫既有EngineBus及原引擎；不建立第二套擷取器、環境管理器或政策正本。
- **L27**(批511 併線(並行線 批508 panorama-v0103);增量)每次擷取前查正庫的日期、標的、欄位缺口；範圍預設最近兩個曆月且排除當日未完成資料。
- **L28**(批511 併線(並行線 批508 panorama-v0103);續傳)批次先存來源Parquet/UTF8-BOM CSV，再交易式入庫，成功才原子記帳；中斷先重播已存批次，失敗與空資料不得冒充完成。
- **L29**(批511 併線(並行線 批508 panorama-v0103);驗證)獨立失敗不阻斷其他診斷；保存完整斷言與未修原因；尚有待修或必要驗收缺席不得INSTALL_OK。
- **L30**(批512;架構)相似整合律(操作員令「類似參數功能引擎就整合優化」):同一判準、同一子行程環境、同一啟動邏輯、同一參數冊只寫一處(冊的擁有者),其餘轉呼叫;新件先找既有件,找到就整合優化不另起;撞名/同功能副本(檔名帶 (2)/(3)、new modules engines/*)一律去重或入收容冊

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
- LL11(批508)壞境上疊裝只會越疊越壞(via_vap_312 pyarrow 半拆、paddle 境 ppstructure 相依斷):先回到前次乾淨基線再按序裝,借 alt 境把 webui/ml_boost 件混進 vap/ml/vdf 境是 Hydra 病根,故 _M 比照 _H 單獨隔離
- LL12(批509)RunGate 把家族境「解譯器壞(SRE module mismatch:標準庫錯配)」判成「必要庫缺」並開補庫令——判錯的紅燈與假綠同罪:import re 都不行時,pip install 是錯藥;先探解譯器(-E/-S/-I 三試分病因:環境變數/site 層/venv 本體),再談庫
- LL13(批509)操作員機器出現本倉沒有的 CGC_MDL149 v0103 / Register v0200 / 律 27 lessons 14——另一條 AI 並行線在同一台機器上造件而沒拉遠端;結果 via-envrecover 不存在、台帳停在 1041、Grid 停在 v0301。檔案是唯一記憶,但兩條線各寫各的記憶=兩個腦;交會律 L25 立
- LL14(批510)矩陣 vrn_firstpage 每跑 600s TIMEOUT,螢幕停著 PPP「OCR 引擎載入失敗…paddle_static」讓操作員以為沒有 OCR 引擎——其實 tesseract 直道在做工;燒時間的是 16 件 PARTIAL 每跑都重燒整條 OCR 階梯(命中律只認 SUCCESS/FAIL)。命中律要涵蓋 PARTIAL(TTL 內不重燒;--retry-failed 才重抽);最後一行不等於病因
- LL15(批511 併線(並行線 批508 panorama-v0103))暫存輸出不等於輸入隔離；selftest須明示禁止掃入正式incoming。
- LL16(批511 併線(並行線 批508 panorama-v0103))截斷矩陣why會丟失失敗斷言；完整每站日誌與進度必须隨測試保存。
- LL17(批511 併線(並行線 批508 panorama-v0103))API空回或逾時不得加入done；以資料庫存在及欄位驗證為準，非checkpoint單方宣稱。
- LL18(批511 併線(並行線 批508 panorama-v0103))ETF逐列autocommit會留下假完整快照；一日持股應同一交易提交，快照日期覆蓋與持股完整性分開。
- LL19(批511)併線實錄:操作員機器上的線是 main(8071a062)+並行 commit,不是本分支;側枝推上來後量到 734 件新增,374 件與倉內 byte 同、48 件互為孿生、.via_envmanager 163MB 執行期狀態被 commit 進來;四個檔撞名(Register v0200/ENG072 v0126/RunGate v0102/MDL149 v0102)各自內容不同。併法:撞名者留並行線內容、本線改動移到更高版號並帶上對方功能(只增不減);律/lessons 取聯集保留 orig_id;執行期狀態 gitignore;孿生只刪未被引用者。兩條線各寫各的記憶=兩個腦,L25 交會律不是建議是必須
- LL20(批512)Z15 實錄:PYTHONHOME 空、PYTHONPATH 只有 bootstrap、via_vdf_312 = C:\Python313 3.13.7 的 venv;RunGate 的 -c 探針 import re 過,站以檔案起跑卻 SRE module mismatch,而匯流排在同一 venv 跑 vap 引擎正常——差在站的子行程環境(cwd=引擎夾)與匯流排 child_env 不同一處;兩處各寫一套子行程環境=Hydra;整合成一處並把 traceback 的 File 路徑(where)印出來,病因才會自己說話
- LL21(批512)批511 併線時把本線 RunGate 的補丁切片用「下一個 def install_missing」當界,結果把中間 10 個既有函式一併複製進 v0103(_bridge/python_for/probe_libs 各兩份;自測仍綠=看不出來)。切片要以緊接的下一個 def 為界,併完 grep '^def ' 數重複

## 二 · 安裝核可(L19)與環境工具

- RunGate:YELLOW · 2026-09-08T19:17:29 · 齡 156.2 h · 必驗 ['vdf', 'vrn'] · 覆蓋 {'vdf': {'ok': False, 'why': '燈=YELLOW、家族境非 OK', 'required_ok': 4, 'required_n': 4, 'engines_ok': 8, 'engines_n': 8}, 'vrn': {'ok': False, 'why': '家族未測'}} → **BLOCKED_UNITEST** · 原因 ['總燈=YELLOW≠GREEN', 'RunGate 時間缺/來自未來/逾 24h', 'vdf:燈=YELLOW、家族境非 OK', 'vrn 家族未測']
- 工具冊導入計畫:ABSENT · - · 件態 - · 風險 - · 段 - · 未路由 - · 白名單留置 -(TOOLS_PLAN_latest.json 不在(via-envtools))
- 環境復原(L24):PLAN · 2026-09-15 05:30:50 · 還原 原本規劃(Baseline;無 LKGC 或 --baseline) · 段 16 · 單獨隔離境 ['via_mix_ds_np2_M', 'via_mix_http_M', 'via_iso_ml_cuda_H'] · 借境封鎖 ['via_mix_ds_np2_M', 'via_mix_http_M', 'via_iso_ml_cuda_H'] · 次序 RESTORE → CORE → LOW → MEDIUM → HIGH → EXTERNAL → VERIFY;安裝出問題=`via-envrecover`(①還原前次 ②順序裝 ③_M/_H 單獨隔離;-Execute -Approve 才跑,① 不受 L19,② 過 L19)
- 裝件=操作員的手:`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`(閘不代設;L19 未綠=BLOCKED_UNITEST)

## 三 · 邏輯庫 · 因子庫 · 資料庫

- 邏輯庫 OK:件 2 · 判準 {'SUCCESS': 2} · 壞後端 [] · 政策因子 414 列 · 全庫同步 {'hash': '3d89567d5b7c', 'counts': {'未入': 1}, 'dbs': 1} · 交接三處 {'doc': 'VIA_Handover_ONEPAGE.md', 'sha': '6d3d7463298f', 'root': '同', 'home': '缺'}
- 因子庫 OK:130 列 · {'SUP_MDL748:allinone 2.1.0': 77, 'SUP_MDL748:financial_data_standardization': 53} · 掛載 {'allinone': 'OK VIA_VRNLogic_AllInOne_v0201.py 2.1.0', 'fds': 'OK financial_data_standardization.py · 28 欄 · 合併損傷件(__main__ 示範缺 5 法,程式庫面可用)'}
- 庫表冊 OK:54 表(批505)· 全庫表 4 · 庫 ['ActiveTWETF.duckdb', 'vdf_global_market.duckdb', 'vdf_tw_market.duckdb']
- 資料家 ABSENT:VIA_Reports/datahome/DATAHOME_CATALOG_latest.json 不在(via-datahome catalog) · 庫 - · 表 - · 湖 -

## 四 · 引擎調度 · 多矩陣實測

- 五矩陣 OK:2026-09-14T11:21:39 · profile run · 真跑 ['vdf'] · 項 43 · 態 {'GATED': 12, 'NODATA': 5, 'PLAN': 18, 'ABSENT': 2, 'GREEN': 6}
- Deck 任務 65 · 規格項 44 · 格子站 217(在位 217)· Register 指令 111 · Manager 正式名稱 任務 66 / 引擎 81

## 五 · 指令與參數(不丟失;來源 Register-VIA-Commands-v0201.ps1)

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
- `via-envrecover`(別名 環境復原):via-envrecover [-Execute] [-Approve] [-ApproveRemove] [-Baseline] [-To LKGC_x.json] [-Env via_x] [--env-root P];plan 唯讀寫 VIA_Reports\env_governance\RECOVER_latest.json/.ps1
- `via-panorama`(別名 全景修復)
- `via-entry`:via-entry plan=一貼即用 11 步;via-entry roster=短令冊(母倉∪Grok 撞名冊);--scan 加跑 via-envgov 全景;--open 開矩陣頁(瀏覽器道零跳出);--console 帶起 Grok 網頁主控台(背景)
- `via-env`:批383:via-env=環境治理正本(MDL135 via-envgov;Grok 版 39 行樁改名 via-env-grok 留冊);via-grok=Grok 短令冊(load 重載;matrix 開 WPF 右側板)
- `via-grok`:批383:via-env=環境治理正本(MDL135 via-envgov;Grok 版 39 行樁改名 via-env-grok 留冊);via-grok=Grok 短令冊(load 重載;matrix 開 WPF 右側板)
- `via-webconsole`:批383:via-webconsole=Grok 網頁主控台(收容包 b383;TanStack/Vite;npm run dev 0.0.0.0:8080):node_modules 缺=須 npm install 觸網→ --install 或 $env:VIA_NET_CONSENT="YES" 同意閘;--background 另窗最小化(關窗即停;不 Stop-Process)
- `via-vapone`:批383:via-vapone=VAP ONE 單檔整合引擎(VAP_ENG016;圖規 SSOT 40/圖規鎖/批330 資料律/零依賴 SVG+Plotly+Matplotlib 車道;無參數=--selftest;via_vap_312 python 優先=全車道)
- `via-vdfdb`:批383:via-vdfdb=本機三庫整併入正典 DuckDB(VDF_ENG079;C:\新增資料夾\新增資料夾\VIA_db_part1_prices/part2_chips/part3_rest;COPY_ONLY anti-join 只補缺鍵;檔冊 sha 已入=跳過;ckpt=ENG064 checkpoint 重建=抓過不再抓;need=缺口清單);無參數=scan 唯讀;run --apply 才寫
- `via-rungate`:批508:via-rungate 無參數=VDF+VRN 各 3 站有界驗收；明帶參數仍完整直通(--all/--family vap/--approve-install 等不丟)。
- `via-py`
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
- `via-vcgc`(別名 中央控管):via-vcgc [status|page|onepage|audit|register-plan|registry-sync|check] [-Publish|-Apply] | -SelfTest ;registry-sync 預設計畫、-Apply 才寫 append-only 元件編號冊；check=VDF+VRN 完整 GREEN 24h 內
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

## 六 · 註冊稽核(所有引擎/模組/功能/工具/環境)

- 中央自動編號冊 OK · ACTIVE 4749/4753 · **缺 4** · 類別 {'class': 91, 'engine': 77, 'environment': 43, 'function': 3947, 'feature': 76, 'module': 141, 'package': 250, 'system': 10, 'tool': 114}
- 尾版引擎/模組家族 227 · 中央冊已登 227 · **未登 0** · 操作介面有掛載 185 · 內部件無操作介面 42(誠實分列，不拿編號片段假命中)

## 七 · 自動編號註冊表(台帳)

- 全域台帳 1047 筆 · 元件 147 · 更新 2026-09-14
- 元件冊 OK · ACTIVE 4749 · RETIRED 1 · 更新 2026-09-15T06:42:34 · {'class': 91, 'engine': 77, 'environment': 43, 'function': 3947, 'feature': 76, 'module': 141, 'package': 250, 'system': 10, 'tool': 114}
- 類別 current:系統 1 · 支援性工具 1 · 功能性工具 1 · 模組 1 · 引擎 19 · 函數庫 1 · 打包產品 8

- 2026-09-14 17:32 批507 AI 交接提示詞 / 固定格式 / 掉球清單 / VCGC 〇九段
- 2026-09-15 05:30 批508 環境復原律 L24 / recover 動詞 / _M 不借 alt / 順序安裝
- 2026-09-15 05:46 批509 多 AI 交會律 L25 / RunGate v0102 解譯器探針 / MDL135 v0108 ENV_BROKEN_INTERP / 啟動層護欄
- 2026-09-15 06:14 批510 PARTIAL_HIT(ENG082 v0109)/ ENG072 v0126 部分命中 / LL14
- 2026-09-15 06:45 批511 併線 / 撞名四檔高版號另起 / 律冊聯集 / 孿生去重 45 / .via_envmanager 不入倉 / VCGC registry-sync
- 2026-09-15 07:31 批512 RunGate v0104 整合匯流排 child_env / where / 引擎夾 cwd 試 / 探針失敗≠缺庫 / 同意閘;L30;L07 note

## 八 · 交接本文(來源 VIA_Handover_20260914_B498.md;逐批紀錄見該檔)


> 立案:操作員令「**修正收尾 實測修正 VDF/VRN 將邏輯因子政策入庫 更新 GITHUB 母系統 HANDOVER REPORT**」。
> 前一份:`docs/VIA_Handover_20260913_B474.md`(批474–497 逐批紀錄仍在那裡,本份不重抄)。
> 這份檔的目的只有一個:**下一個接手的人不必看對話紀錄就能接上**。對話會卡斷,檔案不會。

---

### 〇 · 先想省 token,想好才動(批475 律,仍在)

- 不重讀大檔:`grep -n` 要改的那段,前後看幾行。
- 操作員貼回來的實測輸出**直接當量測結果**。
- 一問題一小版本檔;一批一 push;不順手擴大範圍。
- 自測輸出只印判定行與 `[計]`。

### 〇-b · 批490–498 新收到的律(原文照錄)

1. 「**data save in parquet and managed by duckdb**. this is database file: `C:\Users\tonyk\VIA System\via_database` integrate and consolidate into database storage structure which saving the largest token when fetching and testing.」→ 資料家律(批490–491):家在倉外;鏡根 `via_database\movies-dataset\data`;搬=`link`(junction,hash 定生死,零刪除),**不複製**(三副本病);刪資料是操作員的手。
2. 「**vrn 非 ocr 擷取式必要使用**,若還抓不到改用 ocr 從較簡單的工具組往雙引擎往 paddle;成功包含資料標示還原、文字修復;非 ocr 有兩個相同的相互核對,再跟非 ocr 核對;邏輯方法及其他驗證擷取方法成功後存於**中央邏輯庫**。」(批493)
3. 「**透過 envmanager 安全地導入全部工具**,基於目前環境衝突問題修復後。」(批495)
4. 「未經過我同意,目前這兩個是我指令**唯一的加速器及網路工具**,重新掛載」→ VeritasCeleritas / VeritasAegisNexus(批494;737/740 留作橋,不直 import)。
5. 「**先使用非 ocr 擷取修正驗證,失敗的輸入採用輕量型 ocr 往重型 ocr;如果都失敗,先把 dpi 提高 300~350**。」(批496)
6. 「**中高風險者直接拉出獨立環境及相關工具單獨隔離**;numpy 這種常撞的可多環境多版本搭配多 Python;加速器及網路工具中的工具很多**請勿遺漏**。」(批497)
7. 「修正收尾 實測修正 VDF/VRN 將**邏輯因子政策入庫** 更新 GITHUB 母系統 HANDOVER REPORT」(批498,本批)。

---

### 一 · 批498 做了什麼(收尾批,七件)

| # | 件 | 檔 | 自測 |
|---|----|----|-----|
| ① | **邏輯因子政策入庫**:`sync-db` 把中央邏輯庫台帳 + 律冊/工具冊/資料家冊/Baseline 的政策因子攤平寫進 DuckDB 兩張表 `vrn_extraction_logic`、`via_policy_factors`(CREATE OR REPLACE,不動其他表;庫忙=BUSY 誠實) | `VRN_ENG082_ExtractionLogic_v0102.py`(`resolve_db`:--db > `VIA_DB_VDF_TW_MARKET` > 資料家 rglob 最新 > output_hub/mega) | 14/14 |
| ② | ENG072 每次跑完 `[邏輯庫]` 後**自動 sync-db**(失敗只印一行不擋主流程) | `VRN_ENG072_FirstPageText_v0121.py` | 36/37(⑤ 空夾誠實 rc2 = 容器舊紅,v0116 基線同紅) |
| ③ | 庫表冊 +2 表(51 表;寫入端 VRN_ENG082) | `VIA_DB_Table_SSOT_v0100.json` | — |
| ④ | 匯流排**同意閘誠實態 GATED**(紫燈):引擎 fail-closed 拒跑不是壞掉;停因序 GATED → 缺件(套件壞)→ 相對 import → 缺參數 → 缺件 → 缺料 NODATA(含「Table … does not exist」「Catalog Error」「根缺」)→ 才是 RED | `CGC_MDL148_EngineBus_v0121.py` | 43/43;容器 VDF 矩陣 ABSENT 2 · GATED 12 · GREEN 6 · NODATA 5 · PLAN 18 · **RED 0** |
| ⑤ | **via_core 白名單律**收尾:無家族的加速器通用件列 `[未路由]`(69 件)永不排進 via_core;via_core 非白名單缺件(容器例:joblib)只留置 `WHITELIST_HOLD` 不排裝;白名單單一來源=`VIA_EnvManager.py def_PARAM_VIA_CORE_WHITELIST`(21 件,讀不到才用內建備份) | `CGC_MDL135_EnvGovernance_v0104.py` | 38/38 |
| ⑥ | 母系統登錄:Deck +4 任務(`vrn_logic` / `vrn_logic_syncdb` / `datahome_catalog` / `env_tools`;正式任務 60);Manager 正式名稱 +5 任務 +3 引擎;總控頁再生 | `CGC_MDL095_DeckServer_v0138.py`、`VIA_SYSTEM_MANAGER_v0123.py`、`ui_support/VIA_UI_MasterControl_v0100.html` | 25/25 |
| ⑦ | 工具冊記實測:四境 `python_measured` 3.13.7、via_paddle_311 `never_install`(opencv 兩件)、`fleet_measured_2026-09-14` | `VIA_ToolRoster_SSOT_v0100.json` | — |

**沒做、也不該做的**:再生出來的 `VIA_VDFArchitecture_v0100.json` / `VIA_UI_VDFArchitecture` / `VIA_UI_VapStack` / 可編輯模板 —— 容器沙盒庫是空的,再生會把正本改成 0 列,**一律 revert**(可編輯模板排除律,批498 起)。

---

### 一-b · 批499 · 你貼的 `via-firstpage -RetryFailed` 實錄 + 兩條新令

> 令一:「**所有的庫政策邏輯因子庫都要同步更新**」 → 全庫同步律。
> 令二:「修最後一回 同步更新 **母檔案夾、資料庫及 github 路徑都要有 handover report**」 → 交接三處律。

#### 實錄讀出(直接當量測,不重跑)

| 現象(你貼的) | 根因 | 修 |
|------|------|----|
| `OCR_BUDGET(已用 404s / 257s / 1138s / 328s > 150s)` | 第二階把**整份 PDF** 餵給編排器=全卷 OCR;40 頁簡報就是 1138 秒。預算只在階與階之間查,單一階殺不掉 | ENG072 v0122 ① OCR 只送第 1 頁(fitz 切一頁暫存,同檔只切一次)③ 直呼 tesseract 車道 `subprocess timeout=剩餘預算`(硬殺)④ 每階耗時入 tag `耗時(simple 12s, …)` |
| `via-vrnlogic` 印「後端:尚無紀錄」,但 OCR 明明跑了 | `tesseract:PASS/0元素` 與 `easyocr:SKIPPED_UNAVAILABLE` 都不記;車道整階「不在位」不記;PPP `UNAVAILABLE` 不記 → **每一件都重載 Paddle 模型、重探 easyocr** | ② 全記:跑了零元素=EMPTY、UNAVAILABLE/SKIPPED=BROKEN、有字=OK;**分境鍵** `name`(本境)/`name@via_paddle_311`(車道)/`ppp:paddleocr`(道二);下一件直接 SKIP |
| `lane=via_paddle_311:本境無此階後端:paddleocr,…(在位:apache_pdfbox,marker)` | 車道只講「不在位」,查不了 | 執行器 SUP_MDL747 v0101 逐支照抄 GLE 探針 message(缺 paddlepaddle?缺主程式?)+ `probe` 欄 + `pages` |
| `tesseract:PASS/0元素`(而 `[OCR 語言]` 說 chi_tra 在) | 編排器的 tesseract 零元素,看不出是影像空白還是讀不出 | 直呼 tesseract 車道回 **墨量%**:近空白=渲染出問題;有墨讀不出=升 DPI/換後端 |
| `easyocr:SKIPPED_UNAVAILABLE 探針=requires easyocr, torch, and cached models` | via_vrn_312 無 easyocr;via_paddle_311 有 easyocr 但無 torch/模型檔 | **你的手**(裝 + 模型檔要網路,閘你開) |
| PPP:`paddlepaddle is not installed`(via_vrn_312 有 paddleocr 3.7 無 paddle) | 道二在本境永遠壞,卻每件重試 | 記 `ppp:paddleocr`+本境 `paddleocr` BROKEN(24h);`[OCR 就緒]` 帶「標壞 n」 |
| `[入庫]` 一行都沒印 | 你那次跑的是 pull 前的 ENG082(還沒有 sync_db) | v0122 缺 sync_db 時印 `[入庫] 缺:…git pull 後重跑` |

#### 兩條新律怎麼落地

- **全庫同步律**(ENG082 v0103):`sync-db` 預設對**資料家每本 .duckdb**(沙盒除外)+ `VIA_DB_*` + 首選庫寫同一份 `vrn_extraction_logic` / `via_policy_factors`(同一個 hash),每本各留一列 `via_policy_sync` 對帳單;`via-vrnlogic` 印 `[入庫同步] n 庫 · 同步 x · 落後 y · 未入 z`。政策因子多了**後端健康**(哪支在哪境壞、為什麼)與判準統計。`--db PATH` 仍可單庫。
- **交接三處律**:交接報告在 ① `docs/VIA_Handover_*.md`(github 正本)② 倉根 `VIA_HANDOVER_LATEST.md`(母檔案夾;隨 git pull 到;ENG082 ⑯ 檢 sha 同一份)③ 每本庫 `via_handover` 表 + 資料家根 `VIA_HANDOVER_LATEST.md`(資料庫路徑;sync-db 落)。`via-vrnlogic` 印 `[交接三處]`。
- 庫表冊 53 表(+`via_policy_sync`、`via_handover`;三張政策表 db 欄改「全庫」)。

#### 你的手(裝件都要閘 + Approve)

- `via_paddle_311` 缺 **paddlepaddle**(paddleocr 3.3.1 沒 paddle 等於沒裝)→ `via-envtools` 會列 INSTALL_TOOLS;裝完 `via-vrnlogic reset-backends`。
- 雙引擎階要 **torch + easyocr 模型檔**(via_paddle_311)。
- 裝好之前,階梯會誠實 SKIP 標壞的後端,不再每件燒幾百秒。

#### 一貼即用(批499)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic reset-backends       # ① 清舊健康標記(新鍵分境)
via-firstpage -RetryFailed        # ② 4 件重試:看每階 耗時(…)、tesseract_direct 墨量%、lane probe 因由;跑完 [入庫] 全庫 + [交接]
via-vrnlogic                      # ③ 後端逐支 OK/EMPTY/BROKEN@境 + [入庫同步] + [交接三處]
via-census -Tables                # ④ 每本庫應多 via_policy_sync / via_handover
via-envtools                      # ⑤ via_paddle_311 該列 paddlepaddle/torch;裝=你開閘:$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve
```

---

### 一-c · 批500 · 你貼的 `via-census -Tables` 與 `via-envtools` 實錄

| 現象(你貼的) | 讀出 | 修 |
|------|------|----|
| 六本家內庫都有 `via_handover`/`via_policy_sync`/`via_policy_factors`/`vrn_extraction_logic`(同一時間戳 20:42) | **全庫同步律成了** | — |
| 這四張表在每本庫都點「冊外」,而且 `via_policy_sync`/`via_handover` 點 AMBER「1 天」 | 冊上 db 欄寫的是「全庫(…)」機器對不上;對帳單一列一天不是老化,是**假 AMBER**(判錯的燈和假綠一樣傷) | 匯流排 v0122:冊上 `db_scope=all_home` 的表對每本家內庫都算冊上;`lamp=rows` 的表只看列數(列數≥min_rows=GREEN、零列=NODATA)。庫冊四表 +`via_ingest_ledger` 標 lamp=rows |
| `via_paddle_311 ABSENT pymupdf(No module named 'fitz')`,其餘 12 件 OK(paddlepaddle/paddleocr/easyocr/torch 都在) | **這就是車道「本境無此階後端」的根因**:GLE 的 OCR 轉接器要 fitz 渲染頁面,fitz 不在,整批轉接器 off,只剩 apache_pdfbox/marker | T01 `INSTALL_TOOLS via_paddle_311 pymupdf`——**你的手**(閘 + Approve)。裝完 `via-vrnlogic reset-backends` 再 `via-firstpage -RetryFailed`,paddle 階就會真的跑 |
| `via_vap_312`:pandas BROKEN(pyarrow 無 `__version__`)、pyarrow 半拆、seaborn 缺 | 半拆件 | T03 REPAIR + T04 INSTALL——你的手 |
| `[未路由] 69 件` 裡有 numpy/pandas/pyarrow/duckdb/requests/openpyxl/orjson/polars/rich/loguru | 這些在 `def_PARAM_VIA_CORE_WHITELIST` 上,**白名單制=白名單件該進 via_core**,不該列未路由 | MDL135 v0105:無家族但在白名單上的加速器件路由到 via_core(只增);未路由只剩非白名單件 |
| `via_iso_ml_cuda_H → via_ml`,要把 jax+tensorflow 裝進既有 torch 境 | 違反「中高風險者直接拉出獨立環境」 | MDL135 v0105:HIGH 家族只認同名獨立境(ENSURE_ENV `via_iso_ml_cuda_H`),不借 alt;MEDIUM 家族仍可用 alt |
| `via_mix_http_M → via_core`(httpx/aiohttp ABSENT、anyio 留置) | httpx/aiohttp 在白名單,進 via_core 合律;anyio 不在,留置對 | — |

自測:匯流排 四十四檢 44/44;MDL135 四十檢 40/40(㊲ 改白名單件進 via_core;㊴ HIGH 不借 alt);庫冊 53 表(批500)。

#### 一貼即用(批500)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-envtools                      # ① 計畫應變:未路由變少(白名單件進 via_core);via_iso_ml_cuda_H 改 ENSURE_ENV 獨立境
# $env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve   # ② 你決定要裝才跑:T01 via_paddle_311 pymupdf 是 OCR 車道的關鍵一件
via-vrnlogic reset-backends       # ③ 裝完清健康標記
via-firstpage -RetryFailed        # ④ paddle 階應真的跑(lane=via_paddle_311 不再「本境無此階後端」)
via-census -Tables                # ⑤ 四張政策表應「冊上」+ GREEN
```

---

### 一-d · 批501 · 你貼的 `-RetryFailed` 與 `census` 尾段(批500 之後)

| 現象(你貼的) | 讀出 | 修 |
|------|------|----|
| `候OCR 4 → 1`;`第二場…海外投資展望.pdf · OCR_simple:tesseract_direct(dpi=300,墨量 15.4%,3s) · SUCCESS` | **直呼 tesseract 車道把三件失敗抽回來了**,每件 3 秒 | — |
| 剩的一件 `第一場 2026年投資大趨勢(57 頁)`:`tesseract_direct:EMPTY(墨量 97.7%;有墨讀不出)`,HQ300 也 97.7% | 黑底白字簡報封面;tesseract 不反白讀不到 | ENG072 v0123 ① 墨量 >50% 先反白再 OCR(直呼車道 + 第三階高畫質重繪都做;tag 帶 [反白]);容器黑底白字合成頁反白後讀得到 |
| `頁1/57`、`耗時(simple 4s, dual 3s, paddle 0s, ppp 0s)` | 只送第 1 頁成了:57 頁簡報 OCR 從 1138 秒變 4 秒 | — |
| `lane=via_paddle_311:本境無此階後端:paddleocr(探針無此名)…(在位:apache_pdfbox,marker,paddleocr_ppstructure,poppler,tesseract)` | pymupdf 裝進去後 tesseract 在位了;但**兩套名對不上**:階梯用轉接器名(paddleocr/paddle_ppstructure/paddle_pdf_pipeline/easyocr),後端矩陣回的是規格名(paddleocr_ppstructure/tesseract/…,沒有 easyocr 這格)→ paddle 三支永遠「不在位」 | 執行器 SUP_MDL747 v0102 `ADAPTER_REQ`:照抄 GLE 各 adapter.probe(paddle 三支=paddleocr+paddle 模組;easyocr=easyocr+torch;tesseract=pytesseract+主程式);ENG072 v0123 ② 行程內派送 import 同一份(同一判準只寫一處) |
| `壞後端 ['easyocr','paddle_pdf_pipeline@via_paddle_311','paddle_ppstructure@via_paddle_311','paddleocr','paddleocr@via_paddle_311','ppp:paddleocr']` | 分境健康記錄成了;但 `@via_paddle_311` 那三筆是名對不上造成的**誤標** | pull 後 `via-vrnlogic reset-backends` 一次,新判準重探 |
| `[入庫] OK ×6 · 全庫同步 OK · hash 5febb3ff2983`、`[交接] 資料家根 ←`、census 四張政策表全「冊上」GREEN、`AMBER 32→12` | 全庫同步律 + 交接三處律 + 燈修全成了 | — |

#### 一貼即用(批501)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic reset-backends       # ① 清掉名對不上造成的 @via_paddle_311 誤標
via-firstpage -RetryFailed        # ② 剩的一件:應見 [反白];paddle 階應派到 via_paddle_311 真的跑(不再「探針無此名」)
via-vrnlogic                      # ③ 後端 paddleocr@via_paddle_311 應 OK/EMPTY,不再 BROKEN
```

---

### 一-e · 批502 · 你貼的 `-RetryFailed` 與 `via-vrnlogic`(批501 之後)

| 現象(你貼的) | 讀出 | 修 |
|------|------|----|
| `paddle:OCR_EMPTY[…paddleocr:PASS/0元素; paddle_ppstructure:FAIL 錯=RuntimeError: A dependency error occurred during pipeline cr…][lane=via_paddle_311]`,耗時 paddle 27s | **paddle 車道真的在 via_paddle_311 跑了**(名對上了);paddleocr 跑了零元素(送的是未反白的黑底頁);另兩支是 PaddleX 相依錯(訊息被切在 160 字,尾巴才寫「請裝 …」) | ENG082 v0104 後端 why 記 400 字、status 印 150 字 → 下次貼回來就知道要裝哪個 extra |
| 第三階 `paddle:SKIP(lane=via_paddle_311 後端皆標壞 paddle_ppstructure,paddle_pdf_pipeline)`——車道的 paddleocr 明明只是 EMPTY | **我的 bug**:本境標壞的 `paddleocr`(PPP 壞)被我從**車道**候選名單一起剔掉,車道只剩兩支壞的 | ENG072 v0124 ① 本境鍵與車道鍵分開:派車道用整階名單,車道自己濾 @境 鍵(㊷) |
| `dual:OCR_EMPTY[tesseract+easyocr;…easyocr:SKIPPED_UNAVAILABLE…]`(本境跑了 3 秒) | 本境沒 easyocr,雙引擎階在本境只是重跑 tesseract=白跑;easyocr+torch 在 via_paddle_311 | ② 本階「新增的後端」本境不就緒 → 直接派車道境,不在本境重跑上一階試過的後端 |
| `tesseract_direct:EMPTY(墨量 97.7%[反白])`,HQ300 反白後 `墨量 15.3%` 仍零字 | 反白成了,但封面大字疏排,tesseract 預設版面分析(psm 3)常找不到 | ③ 零字再試 `--psm 11`(疏字)→ `--psm 6`(整塊),tag 帶 `psm=3→11→6`(㊸) |
| `後端 paddleocr@via_paddle_311 EMPTY`、`[入庫同步] 6 庫 · 同步 6`、`[交接三處] 倉根 同 · 資料家根 同` | 分境健康、全庫同步、交接三處全成了 | — |

自測:ENG072 四十三檢 42/43(⑤ 容器舊紅);ENG082 十六檢 16/16。

#### 一貼即用(批502)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic reset-backends       # ① 清掉 160 字被切的舊紀錄
via-firstpage -RetryFailed        # ② 剩的一件:dual 應派車道(easyocr 在 via_paddle_311);第三階 paddle 應跑反白頁;直呼車道 psm=3→11→6
via-vrnlogic                      # ③ 後端 paddle_ppstructure@via_paddle_311 的錯全文(尾巴的「請裝 …」)貼回來——那是你的手
```

---

### 一-f · 批503 · 批502 跑到了:64 件全部抽出

| 你貼的 | 讀出 |
|------|------|
| `[OCR_simple:tesseract_direct(dpi=300,l=chi_tra+chi_sim+eng,psm=3→11,墨量 97.7%[反白],5s)[繁化]] 第一場 2026年投資大趨勢.pdf · 124 字` | 最後一件:反白 + `--psm 11`(疏字)5 秒讀出;psm 3 讀不到、psm 11 讀到=封面大字疏排,版面分析要選疏字模式 |
| `[計] 64 件 · 候OCR 0`;`件 64:PARTIAL 16 · SUCCESS 48`;`壞後端 無` | **首頁擷取 64/64**;四件掃描件全走直呼 tesseract 車道(3–22 秒/件),雙引擎與 paddle 階這一輪沒有需要用到 |
| `[入庫] OK ×6 · hash fc135c673f24 · [入庫同步] 同步 6 · [交接三處] 同/同` | 全庫同步 + 交接三處成了(policy 78 列=後端健康表清掉後少了 6 列,對) |
| `via-vrnlogic` 把 `tesseract_direct(dpi=300,…,墨量 14.8%,22s)` 四件列成四種「法」各 1 | 法名帶了每件參數;ENG082 v0105 法名切到「(」為止,同法一行 |

下一個品質前線(不是故障,是操作員律的第二句「成功包含資料標示還原」):**PARTIAL 16** 件=互核 AGREE 但標示未全還原;台帳 `labels_ok=False` 的件在 `LOGIC_LEDGER.jsonl`,`via-vrnlogic` 可數。要不要追,你定。

還掛在你的手上的三件(不影響 64/64,但雙引擎/paddle 階要真的能用得先裝):
- `paddle_ppstructure@via_paddle_311` PaddleX 相依錯(下次跑到會記 400 字全文,尾巴的「請裝 …」)。
- `easyocr` 模型檔(via_paddle_311 有 easyocr+torch,缺 cached models;網路,閘你開)。
- 道二 PPP 在 via_vrn_312 缺 paddlepaddle(paddleocr 3.7 無 paddle)——不裝也行,paddle 階走車道。

---

### 一-g · 批504 · 你上傳的五件財務邏輯 + `via-vrnlogic`「同步 1 · 落後 5」

#### 先認錯:五本真庫的政策表被我的自測污染了

`[入庫同步] 同步 1 · 落後 5(hash fe4d7cff83b3)`——那個 hash 是 **ENG072 自測時的台帳狀態**。批498 我把 ENG072 自測 ㊲ 的首選庫導向暫存,
但批499 全庫同步律之後 `sync_targets` 還會掃 `VIA_DATA_HOME` 與 `VIA_DB_*`,所以 `via-ryg` 跑格子自測時,把 8 筆 fixture 寫進了你
**五本真庫**的 `vrn_extraction_logic` / `via_policy_factors` / `via_policy_sync` / `via_handover`(vdf_tw_market 因為被導向暫存而倖免;其餘表零觸碰)。
修:ENG082 v0106 `VIA_SELFTEST=1` 時 `sync_targets` 只認 env 指定的那一本(不掃家、不掃 VIA_DB_*);ENG072 v0125 自測期間設旗 + 家指暫存 + 暫撤其他 VIA_DB_*(結束還原);
兩邊各加一檢(ENG082 ⑰、ENG072 ㊹)。**復原=你跑一次 `via-vrnlogic sync-db`**(CREATE OR REPLACE 覆寫回真台帳,其餘表不動)。

#### 五件上傳量測(先量再造)

| 件 | 量測 | 處置 |
|---|------|------|
| `VIA_VRNLogic_AllInOne_v0201.py` | **新**。VIA-VRN-LOGIC-001 2.1.0;純標準庫;離線;容器 `--selftest` 十六檢 16/16;有 `--install apply` 自裝功能 | 收容 `references/intake/VIA_VRNLogic_AllInOne_v0201_b504/` + MANIFEST;**永不 apply**;掛載走橋 |
| `vdf_fetchers_financials.py` | **新**。TW→MOPS(存根,實際回空)→退 yfinance;直呼 requests/yfinance | 收容 `VDF/references/intake/vdf_fetchers_financials_b504/`;**只收不掛線**(批494 律:網路只認 AegisNexus) |
| `financial_data_standardization.py` | 與倉內 `functional modules/VRN/` 同本(CRLF 差);合併損傷件(class 先於 imports;`__main__` 示範缺 5 法),程式庫面可用(28 欄對照、15 正則、評等/期間關鍵字、交互驗證) | 不重複收容;橋以 sys.modules 登錄後 import(dataclass 註記解析才過——這就是 finlex 走 AST 的原因) |
| `VRN_ENG074_FinancialPages_v0106.py` | 與倉內尾版同本(CRLF 差) | 不收;本批出 v0107 |
| `VDF_MDL006_FinancialModel.py` | = 倉內 `VDF_MDL006_FinancialModel_sha3da0113e.py` 去掉加速/網路橋頭的原件(45 行差全是橋頭) | 不重複收容 |

#### 造了什麼

- **SUP_MDL748 財務邏輯統轄橋 v0100**(只掛不搬):`second_opinion(科目)`(AllInOne FINANCIAL_SYNONYMS + FDS 28 欄)、`rating_of`(BUY/HOLD/SELL/NOT_RATED)、`parse_filename`、`validate_formulas`、`policy_rows()`(兩本冊攤平 130 列);九檢 9/9。
- **ENG074 v0107**:SSOT `normalize_metric` 未命中(UNKNOWN)才問第二意見,只寫在 raw_text 註記 `[二見 total_assets@allinone]` 與跑完的「候 register」清單,**canonical 不改**(單一真相仍是 `VRN_Financial_Synonyms_SSOT`;要不要登錄=你定)。量過:SSOT 沒有 總資產/股東權益/營業活動現金流/營業毛利/流動比率,兩本冊都有——這就是二見的價值。十九檢 18/19(⑬ 容器舊紅:v0106 基線同紅,NO_TICKER/NO_DATE 在容器的 crosscheck 夾具;你機器上批466 曾 18/18)。
- **ENG082 v0106**:政策因子 +橋兩本冊(via_policy_factors 84 → 210 列左右);自測零污染律;十八檢 18/18。
- 登冊:Register v0197 `via-finlogic [status|opinion <科目>|rating <字>] | -SelfTest`(別名 財務邏輯);Deck v0139 `fin_logic`(釘 61);Manager v0124 正式名稱;格子 v0299 +一站;主控台冊 +`fin_logic`。

#### 一貼即用(批504)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 覆寫回真台帳(政策表 +財務兩本冊);6 庫應同一 hash
via-vrnlogic                      # ② [入庫同步] 應 同步 6
via-finlogic -SelfTest            # ③ 九檢
via-finlogic                      # ④ 橋現況 + 二見範例
via-vrn4                          # ⑤ 四站鏈重跑:ENG074 v0107 末行 [二見] 候 register 清單貼回來(要不要登錄 SSOT=你定)
via-ryg -Timeout 300              # ⑥ 跑完再 via-vrnlogic 一次:應仍 同步 6(自測不再污染真庫)
```

---

### 一-h · 批505 · 你貼的 `via-ryg` 矩陣 + 「實測 vdf vrn vetf」

| 你貼的 | 讀出 | 修/做 |
|------|------|------|
| `[37/44] vrn/vrn_logic · VRN_ENG082 v0106 → RED` | ENG082 自測 ⑮/⑰ 在你機器上跑:bootstrap 匯出的 `VIA_DB_*` 真庫全進了 `sync_targets`,目標數對不上=FAIL;**而且 ⑮ 又把 fixture 寫進真庫**(容器加一個 `VIA_DB_FAKE1` 就重現:假庫多出四張政策表) | ENG082 v0107:整段自測先撤 `VIA_DB_*`/`VIA_DATA_HOME`、設 `VIA_SELFTEST=1`,結束還原;⑲ 證明;容器帶假 VIA_DB_* 跑 19/19 且假庫零觸碰。**你 pull 後跑一次 `via-vrnlogic sync-db` 復原** |
| `[12/44] vdf/fin_statements · 缺席 (PLAN)` | 主控台冊這格從批442 起就是 PLANNED、母倉無引擎;你上傳的 `vdf_fetchers_financials.py` 就是它 | **VDF_ENG082_FinStatements v0100 上船**(只掛收容件不搬):雙閘 fail-closed(`gate_state`;閘你開)、yfinance 車道以 AegisNexus `ResilientHTTPClient` session 注入(新版 yfinance 拒收就退原生並講明)、MOPS 走 NetUnified `http_text` 探路(解析=候)、`tw_financial` 23 欄+fetched_at 派生層冪等、parquet 由 duckdb COPY 落 `mega/fin`(零 pyarrow);八檢 8/8;`via-bus catalog` 已見 `[在位] vdf/fin_statements … 動詞=run` |
| VDF 26 項全 PLAN | 矩陣預設「真跑 vrn,vap;其餘只解析」;帶 `--apply` 的寫庫動詞永不代跑(要 `--ids` 明點) | 實測 vdf=`via-ryg vdf,vrn -Timeout 600`;紫=閘未開(你開閘再跑);PLAN=寫庫動詞要 `--ids`;紅才是要修 |
| `[38/44] vrn/fin_logic → GREEN`、`vrn_finpages v0107 GREEN`(UNKNOWN 科目 69/59=候 register) | 批504 的橋與二見上線了 | `via-vrn4` 跑完看 ENG074 末行 `[二見]` 清單 |
| vap 三項 ABSENT(pyarrow 半拆 / pandas 缺) | 同批500:T03/T04 你的手 | `$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve` |

登冊:主控台冊 `fin_statements` 接引擎(SHIPPED);庫表冊 +`tw_financial`(54 表);Register v0198 `via-finstat [run|status|-Dry] [--only …] [--limit N] [--years N]`(別名 三大報表);Deck v0140 `fin_statements`(釘 62);Manager v0125;格子 v0300 +一站。
(批505 第一次 commit d80adde4 只上了一半——登冊腳本在 Deck 說明行的錨點上斷了;本段與 Deck/Manager/Grid/台帳在 批505b 補齊。)

#### 一貼即用(批505:實測 vdf · vrn · vetf)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 先復原被自測污染的五本真庫(覆寫回真台帳;其餘表不動)
via-vrnlogic                      # ② [入庫同步] 應 同步 6;vrn_logic 站之後應 GREEN
via-finstat -Dry --only 2330,2317 # ③ 三大報表:只列目標,不碰網路
# $env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='<你的>'; via-finstat run --only 2330,2317 --years 5   # 你開閘才跑;via_vdf_312 要有 yfinance(缺=缺件誠實停)
via-ryg vdf,vrn -Timeout 600      # ④ 實測 vdf+vrn(vetf=vdf 家族第 21 項 vdf_vetf_consensus):紫=閘未開 · PLAN=寫庫動詞要 --ids · 紅才是要修
via-vetf                          # ⑤ VETF 持股×Consensus 獨跑(candidate 沙盒)
via-bus tails                     # ⑥ 紅項因由 + 引擎尾段,貼回來
```

---

### 一-i · 批506 · 大令:倉衛生 · 政策庫 · Veritas Central Governance Console(唯一對接口)· 安裝核可律 · 一頁交接

| 令 | 做了 | 證據 |
|---|------|------|
| 檢視母資料夾/GitHub 多餘資料與大量 HTML,刪 | 先量:38,917 追蹤檔、1,113 HTML、14,625 SVG、12,656 PNG、pack 560MB、VAP 3.1GB(ICON_FORGE 1.5GB)。**只刪有 md5 證據且檔名未被引用的重複件 394 件 464MB**(ICON_FORGE/ASSETS 同 md5 孿生 323 · BACKUP 孿生 71);未刪候裁八類列在報告 | `docs/VIA_RepoHygiene_B506.md/.json`(每筆 md5 + 保留孿生);批506a |
| 所有上述要求 → 政策庫 + lessons-learned | `VIA_Policy_Laws_SSOT_v0100.json`:23 律(L01–L23)+ 10 lessons;ENG082 v0108 攤平入 `via_policy_factors`(sync-db 全庫同步) | `via-vrnlogic sync-db` 後 `via-census -Tables` |
| Veritas Central Governance Console 為唯一對接口 | `CGC_MDL149_VeritasCentralGovernanceConsole v0100`(只讀不造):政策庫/邏輯庫/因子庫/資料庫/引擎調度(Deck 64 任務·規格 44 項·格子 217 站·Register 109 指令含用法與別名=**指令參數不丟失**)/多矩陣/環境工具/自動編號註冊表/註冊稽核/L19 安裝核可/一頁交接;十一檢 11/11 | `via-vcgc [status|page|onepage|audit|register-plan|check] [-Publish]`(別名 中央控管) |
| 所有引擎模組功能工具環境都要註冊 | 註冊稽核:硬碟引擎家族(尾版)227 · 已登冊 186 · **未登冊 41**(誠實列於一頁交接第六段);`via-vcgc register-plan` 出建議登冊清單(只列不寫;核准後另批登冊) | `VIA_Reports/vcgc/REGISTER_PLAN.md` |
| 環境統一測式無誤後才可核可安裝 | 律 L19:MDL135 v0106 `tools --apply --approve` 與 `apply --approve` 在同意閘之後再過 RunGate 閘(判定 GREEN 且 24h 內),否則 BLOCKED_UNITEST 零動作;㊵ 三態證明;VCGC `check` 同律 | `via-rungate` → `via-vcgc check` → 才 `via-envtools -Apply -Approve` |
| 詳細 handover 整合成同一頁 + 環境工具管理 + 自動編號註冊表 | VCGC 一頁交接 `docs/VIA_Handover_ONEPAGE.md`(八段:政策庫/安裝核可與環境工具/邏輯因子資料庫/引擎調度與多矩陣/指令與參數/註冊稽核/自動編號註冊表/交接本文三四五段);倉根 `VIA_HANDOVER_LATEST.md` = 同一頁;每本庫 `via_handover` 表隨 sync-db 入 | 動態段以你機器 `via-vcgc onepage -Publish` 為準;倉內是 commit 時快照 |
| 實測 vdf/vrn 通過即可 | vrn 五矩陣 GREEN(vrn_logic 站修好);vdf 真跑=你機器 `via-ryg vdf,vrn`(閘你開;寫庫動詞 --ids) | 貼回 `via-bus tails` |

登冊:Register v0199 `via-vcgc`;Deck v0141 `vcgc_status`/`vcgc_page`(釘 64);Manager v0126;格子 v0301 +一站;MDL135 站→v0106(四十檢);ENG082(VRN)→v0108(十九檢)。

#### 一貼即用(批506)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h     # 會刪 394 件重複件(git 可回溯)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 政策庫 23 律 + lessons + 交接一頁入六本庫
via-vcgc                          # ② 唯一對接口現況(八庫一眼)
via-vcgc page -Publish            # ③ 一頁交接 + 頁(以你機器的報告為準;-Publish 才寫 docs/倉根/頁)
via-rungate                       # ④ 環境統一測式(RunGate)
via-vcgc check                    # ⑤ L19:GREEN 且 24h 內 → INSTALL_OK,才准 via-envtools -Apply -Approve
via-vcgc register-plan            # ⑥ 未登冊 41 家族的登冊建議(只列;你核准我再登)
via-ryg vdf,vrn -Timeout 600      # ⑦ 實測 vdf+vrn;via-bus tails 貼回來
```


### 一-j · 批507 · 「這是多 AI 寫作的工具?要一個 prompt 完整引導下一個 AI 接手不掉球;檢查掉球紀錄;格式長久使用;收尾更新母檔案夾/資料庫夾/GitHub」

| 令 | 做了 | 證據 |
|---|------|------|
| 是不是多 AI 接力寫的 | **是**。每一段對話都會被壓縮/換人,AI 自己沒有記憶;**檔案是唯一的記憶**(倉 = 母檔案夾 = 每本庫的 `via_handover` 表三處同一頁)。所以「不掉球」= 把球寫進檔、寫進台帳、寫進掉球清單,並由 VCGC 一頁交接把三者攤在同一頁 | `docs/VIA_AI_Handover_Prompt_v0100.md` D 段 |
| 一個 prompt 完整引導下一個 AI | `docs/VIA_AI_Handover_Prompt_v0100.md` **A 段**=開場提示詞(整段貼進新對話即可:讀三個檔 → 12 條律 → 接手驗收三指令 → 工作節奏 → 掉球定義);VCGC 一頁交接 **〇 段** 原文嵌入,所以 `VIA_HANDOVER_LATEST.md` 一開就是提示詞 | `via-vcgc onepage` 第 〇 段 |
| 給交接者(離場 AI)的收尾 | 同檔 **B 段**=收尾清單 8 條(每條要證據路徑:commit/push 乾淨、台帳、交接本文 一-N 段、掉球清單、sync-db、page -Publish、自測、母檔案夾拉齊);做不到的寫「沒做+為什麼」,不准沉默 | 本段就是照 B 段收的 |
| 格式長久使用 | 同檔 **C 段**=交接紀錄固定格式 〇–八(批號/令/做了/證據/沒做/掉球/一貼即用/驗收貼回);交接本文每批一節 `一-N` 就是這格式;掉球清單只增不減、結案劃線 | `docs/VIA_DroppedBalls_B507.md`(24 列 · 未結 23 · ~~W~~ 已結) |
| 檢查上述掉球為紀錄 | 掉球審計:A/D/G/I/P/R/S/T/U/V/X/Y 舊球 + Z1–Z12 本輪新球(Z1 PARTIAL 16 標示還原、Z2 未登冊 40 家族、Z3 衛生第二階、Z4 MOPS 解析、Z5/Z6 vdf·vetf·三大報表真跑=操作員的手、Z9 公式驗證、Z11 治理項入規格、Z12 MasterControl 你機器重生);每列有 狀態/誰/下一步 | VCGC 一頁交接 **九 段** 自動帶入(列數/未結數) |
| VCGC 帶提示詞與掉球 | `CGC_MDL149 v0101`:`prompt_doc()`(尾版 `docs/VIA_AI_Handover_Prompt_v*.md`)、`dropped_balls()`(尾版 `docs/VIA_DroppedBalls_B*.md`);一頁 〇/九 兩段;頁卡;格子站「特殊」標示(PYCODE/自我引用站不判紅);十二檢 12/12 | `via-vcgc page -Publish` |
| 收尾:母檔案夾 / 資料庫夾 / GitHub | GitHub:批507 commit+push;母檔案夾=你 `git pull` 後倉根 `VIA_HANDOVER_LATEST.md`(sha 與 docs/ONEPAGE 同);資料庫夾(可不用):`via-vrnlogic sync-db` 把同一頁寫進每本庫 `via_handover` + 資料家根副本 | 下方一貼即用 |

沒做(誠實):Z1–Z12 都還掛著(見九段);本輪沒有新裝任何套件、沒有設任何同意閘、沒有動正本。

#### 一貼即用(批507)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vrnlogic sync-db              # ① 同一頁交接(含提示詞 + 掉球)入每本庫 via_handover + 資料家根
via-vcgc                          # ② 唯一對接口現況
via-vcgc page -Publish            # ③ 以你機器的報告重生一頁交接(〇 提示詞 … 九 掉球)+ 倉根 + 頁
via-rungate                       # ④ 環境統一測式
via-vcgc check                    # ⑤ L19 安裝核可(GREEN 且 24h 內才 INSTALL_OK)
via-ryg vdf,vrn -Timeout 600      # ⑥ 實測 vdf+vrn
via-bus tails                     # ⑦ 貼回來
```

**給下一個 AI 的第一句話**:打開 `VIA_HANDOVER_LATEST.md`,第 〇 段照貼,第 九 段是你的待辦,第 八 段是史。


### 一-k · 批508 · 「環境安裝出了問題可以先還原原本前次環境然後把所有工具順序安裝上 中高風險一律單獨隔離」

| 令 | 做了 | 證據 |
|---|------|------|
| 先還原原本前次環境 | 律 **L24 環境復原律** 入政策庫冊(+LL11);MDL135 v0107 新動詞 `recover`(`via-envrecover`):① 還原前次 = LKGC lock 逐境 `uv pip install -r lock`(非破壞);`sync` 破壞段只在 `-ApproveRemove`;無 LKGC → Baseline 原本規劃重建 | `via-envrecover`(plan 唯讀)→ `VIA_Reports\env_governance\RECOVER_latest.json/.ps1` |
| 然後把所有工具順序安裝上 | 順序安裝律:段依境層級 **CORE 白名單 → LOW 家族境 → MEDIUM 隔離境 → HIGH 隔離境 → 外部本體 → 驗證**(同境內 建境→修復→安裝→驗證);`via-envtools` 同序;recover 模式下隔離境 `uv venv` 可建(只增) | `.ps1` 第 ② 段;㊶ 段序證明 |
| 中高風險一律單獨隔離 | `_M` 家族比照 `_H`:只認同名獨立境,**不借 alt 境**(webui 不借 via_vap_312、ml_boost 不借 via_ml/via_vdf、http_async 不借 via_core);隔離境不在 → 建同名境,件不進 alt 境(借境封鎖) | 工具冊 `risk_policy.MEDIUM` 改;㊶ 有 alt 在位仍 ENV_ABSENT |
| 閘 | ① 不受 L19 擋(LKGC 本身即曾 GREEN;同意閘仍要)② 新裝段過 L19(`via-rungate` GREEN 24h 內)否則 **RESTORED_BLOCKED_UNITEST** 誠實停,先 rungate 再跑一次(① 已做段 no-op);無同意閘 = BLOCKED_CONSENT 零動作 | ㊶;MDL135 四十一檢 41/41 |
| 登冊 | Register v0200 `via-envrecover`(別名 環境復原)· Deck v0142 `env_recover`(釘 65)· Manager v0127 · Grid v0302 · VCGC v0102 二段 +環境復原 · 台帳 1043 | `via-vcgc` 二段 |

沒做(誠實):容器裡沒有你的境,recover 只能出 Baseline 模式的唯讀計畫;你機器上有 LKGC_latest 才會走 lock 還原。真跑=你的手(下方 ⑤)。

#### 一貼即用(批508)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-envgov lkgc                   # ① 有沒有前次基線(LKGC_latest;沒有=recover 走 Baseline 原本規劃)
via-envrecover                    # ② 復原計畫(唯讀):①還原 ②順序裝 ③隔離;看 RECOVER_latest.ps1
via-vcgc                          # ③ 二段看 環境復原 燈
# 真跑(你的手):$env:VIA_NET_CONSENT='YES'; via-envrecover -Execute -Approve        # sync 破壞段另加 -ApproveRemove
via-rungate                       # ④ ① 做完後環境統一測式;GREEN 才放行 ②
# $env:VIA_NET_CONSENT='YES'; via-envrecover -Execute -Approve                      # ⑤ 再跑一次:② 順序裝(① no-op)
via-vrnlogic sync-db              # ⑥ 律 L24 入每本庫 via_policy_factors
```


### 一-l · 批509 · 你貼的實錄(via-envrecover 不存在 · via-vcgc v0103 · RunGate RED「必要庫缺」其實是 SRE module mismatch)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `via-envrecover` 不認得;`via-vcgc` 印 **v0103 批508**、律 27、lessons 14、227/227 登冊、中央冊 4734;台帳 **1041**;Grid 仍 v0301 | 遠端分支 = 我的 HEAD(5814e09e),遠端所有分支都沒有 v0103/律 27 → **你機器上有另一條 AI 並行線**(從批506b 分出,沒拉我的批507/508);你的 `git pull` 多半因分歧沒併(貼裡看不到那段) | 律 **L25 多 AI 交會律** + LL13;接手提示詞第 0 步=先對齊遠端;掉球 Z14;一貼即用:先把那條線 commit 到側枝並 push,再把工作分支對齊遠端 → 我出批510 併線(只增不減) |
| `via-rungate` RED:vdf/vrn 全站 0.2s `assert _sre.MAGIC == MAGIC, "SRE module mismatch"`,卻判「必要庫缺:duckdb,pandas,numpy,pyarrow」並開補庫令 | **判錯的紅燈**:家族境 python 連 `import re` 都不行=解譯器壞(標準庫錯配),補庫是錯藥;第一次 via-vcgc 還是 RunGate GREEN,之後才壞=中間有東西動了境或環境變數 | RunGate **v0102**:先探解譯器,-E/-S/-I 三試分病因(環境變數 PYTHONHOME/PYTHONPATH · site 層 · venv 本體),存證 pyvenv.cfg 與現值;RED 理由=解譯器壞(不列缺庫);補庫 SKIP;不探庫不跑站;次步=診斷+重建境(候裁);十二檢 12/12 + LL12 |
| 同病會傳到工具冊/復原 | v0107 探針失敗會把整境當 UNKNOWN/缺件 | MDL135 **v0108**:探針帶 SRE/MAGIC/encodings → 境 ENV_BROKEN_INTERP · 件 INTERP_BROKEN · 只出 REBUILD_ENV 候裁段(印 Remove-Item/uv venv/lock 三行;永不自跑,--approve-remove 亦不跑=境刪除是你的手);㊷ 四十二檢 42/42 |
| 啟動層快取套變數 | `sitecustomize` 會把 ACCEL_ACTIVATION 快取 applied 裡所有大寫鍵設進 env——若哪天快取帶了 PYTHONHOME/PYTHONPATH,子行程家族境就是這個病 | 護欄:PYTHON*/PATH/VIRTUAL_ENV/CONDA_PREFIX 永不從快取套(就地改;無版號檔) |
| 掛著 | SRE 根因要你機器的三試結果才定;並行線要你推側枝才能併 | Z14 / Z15 |

#### 一貼即用(批509;三段:① 保住並行線並對齊 ② 診斷解譯器 ③ 復原計畫)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git status --short | Select-Object -First 30; git log --oneline -3; git branch --show-current                     # ① 先量:哪些檔是那條線的
git switch -c local/parallel-b508; git add -A; git commit -m "本機並行線快照(VCGC v0103/Register v0200/律 27;未併)"; git push -u origin local/parallel-b508
git switch -C claude/via-envmanager-governance-7cls8h origin/claude/via-envmanager-governance-7cls8h                  # 工作分支對齊遠端(那條線已在側枝,零遺失)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
$env:PYTHONHOME; $env:PYTHONPATH                                                                                     # ② 診斷:這兩個值直接貼回
Get-Content C:\Users\tonyk\envs\via_vdf_312\pyvenv.cfg
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -c "import sys;print(sys.version)"
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -E -c "import re;print('E ok')"
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -S -c "import re;print('S ok')"
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -I -c "import re;print('I ok')"
via-rungate                       # v0102:印 [INTERP] 病因 + 三試;次步不再叫你 pip install
via-envrecover                    # ③ 復原計畫(唯讀;解譯器壞境列 REBUILD_ENV 候裁行)
via-vcgc                          # 二段:環境復原燈
```


### 一-m · 批510 · 你問「沒有 OCR 引擎嗎??」(矩陣 vrn_firstpage TIMEOUT 600 · 螢幕停著 PPP「OCR 引擎載入失敗…paddle_static」)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `[VIA_PDFPlumberPlusEngine] OCR 引擎載入失敗,掃描頁將標記為 NO_OCR:RuntimeError: Engine 'paddle_static…` 停在「引擎最後一行」280 秒 | 那是**道二 PPP 收容件自己的 paddle 載入器**(paddleocr 2.x API 對不上你機器的 3.x),失敗一次記 BROKEN 24h 跳過;**不是沒有 OCR 引擎**:tesseract 直道(chi_tra+chi_sim+eng;批469 裝、批503 讀出 57 頁反白簡報 124 字)在做工,easyocr 要模型檔,paddle 走 via_paddle_311 車道。「最後一行」只是螢幕上最後印的那行,OCR 在跑時不印字 | LL14;答在本段 |
| 矩陣 `vrn_firstpage TIMEOUT 600.23`;你上次 `-RetryFailed` 也是 OCR_BUDGET 404/257/1138/328s | 燒時間的是 **16 件 PARTIAL 每跑都重燒整條階梯**:邏輯庫 lookup 只認 SUCCESS=HIT、FAIL=FAIL_HIT,PARTIAL 一律 None → 16 × 階梯(tesseract→easyocr→paddle 車道→HQ)≫ 600s | ENG082 **v0109** +PARTIAL_HIT(產物在且 TTL 內不重燒;⑳ 二十檢 20/20);ENG072 **v0126** 印 `[LOGIC_PARTIAL_HIT]`、卡片自舊產物重建、跑完印「部分命中 N」;`-RetryFailed` 涵蓋 PARTIAL(印 `[RETRY_PARTIAL]`);㊺ 四十五檢 |
| 你的樹還是 Grid v0301、台帳 1041 | 批509 的對齊區塊還沒跑(那條並行線還在你機器上跑 PANORAMA/policy_append/registry_sync) | 先跑批509 ① 保住並行線再對齊,否則這批也拉不到 |

#### 一貼即用(批510;接在批509 ① 對齊之後)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
tesseract --version | Select-Object -First 1; tesseract --list-langs                    # OCR 引擎本體與語言包(chi_tra 要在)
via-vrnlogic                                                                          # 後端健康表:壞後端 = 24h 內跳過的那些
via-firstpage                                                                         # 例行跑:64 件應為 命中 48 · 部分命中 16(秒級)
via-ryg vrn -Timeout 600                                                              # vrn_firstpage 不該再 TIMEOUT
# 要重抽 16 件 PARTIAL(慢;每件走整條階梯):via-firstpage -RetryFailed
```


### 一-n · 批511 · 「vdf也加進來整合去重」+ 你貼的實錄(側枝已推 · tesseract 3 語 · via-firstpage 48/16 · via-ryg vrn GREEN 10)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `git branch --show-current` = **main**(8071a062 = origin/main + 本線 c93ad32e 的本機合併);136 檔未推的並行線 → 側枝 `local/parallel-b508-09151416`(7cc9031f)已推;工作分支已對齊本線 | 你機器一直在 main 上跑,不是本分支;並行線 = panorama-v0103(VCGC v0102/v0103、RunGate v0102、Bus v0123–v0125、ENG072 v0126/v0127、ENG073 v0125、ENG074 v0108、VDF ENG057/063/064/066/078 新版、launchers/Invoke-VIA-Panorama、律 L24–L27、lessons LL11–LL14、元件冊 4734)+ `.via_envmanager/` 163 MB 執行期狀態 | **併線**:`git merge` 側枝,8 個衝突照 L25 解——撞名四檔(Register v0200/ENG072 v0126/RunGate v0102/MDL149 v0102)留並行線內容,本線改動移到更高版號並帶上對方功能:**Register v0201**(+via-envrecover/via-panorama)、**ENG072 v0128**(並行 v0127 夾具 + PARTIAL_HIT;45/45,連容器舊紅 ⑤ 都綠了)、**RunGate v0103**(並行假綠修 + 解譯器探針;12/12)、**MDL149 v0104**(並行 registry-sync/panorama + 復原段;14/14);律冊聯集 29 律 19 lessons(並行線 L24–L27→L26–L29、LL11–LL14→LL15–LL18,orig_id 保留);`.via_envmanager/` 不入倉(.gitignore;側枝保有) |
| 併入後新增 734 件:374 件與倉內 byte 同(git blob 同 sha)、48 件互為孿生、312 件獨有 | 「整合去重」= 只刪 byte 同且路徑/檔名未被引用者 | 刪 45(VeritasPulse_v14 15 · VDF_final 13 · VAP 6 · taiwan_revenue 4 · output 2 · 帶 (2)/(3) 的副本 5);留 377(路徑或檔名被引用);獨有 312 一律留;報告 `docs/VIA_RepoHygiene_B511.md/.json` |
| 並行線引擎在併線樹上自測 | Bus v0125 46/46 · ENG073 v0125 36/36 · ENG074 v0108 19/19 · VDF ENG064 v0111 9/9 · ENG078 v0108 29/29 · ENG066 v0102 8/8 · ENG063 v0105 9/9 · ENG057 v0101 6/6 | 全綠;VCGC v0104 `registry-sync --apply`:活元件 4749 · 新 16 · 變更 430 · 退役 1 |
| 並行線 VCGC ⑩ 釘死兩串固定字(「操作員最後一棒」「bounded matrix 已 38/38 GREEN」)——那份 handover 沒進倉,⑩ 在任何人的樹上都紅 | 判錯的紅燈 | v0104 ⑩ 改結構判準:八段真的嵌了尾版交接本文(來源名 + 最後一個 ## 標題降級後在頁裡) |
| `tesseract v5.3.3` · chi_sim/chi_tra/eng;`via-vrnlogic` 64 件 PARTIAL 16 · SUCCESS 48;壞後端 無 | OCR 引擎在、語言包在 | 答了「沒有 OCR 引擎嗎」:有三條,那行是道二 PPP 的載入器 |
| `via-firstpage`(批509 樹):命中 48,16 件 PARTIAL **全是數位 PDF DUAL_ZONES**,合計秒級;`via-ryg vrn -Timeout 600`:vrn_firstpage **GREEN 30.89s**,vrn 10 GREEN · vrn_markdown NODATA(缺料) | **批510 的歸因錯了**:600s TIMEOUT 不是 PARTIAL 重燒 OCR,是並行線 panorama 自己的 vrn_firstpage 跑法;PARTIAL_HIT 仍有效(少做 16 次非 OCR 重抽) | Z18 記錯;LL14 文字下批修 |

沒做(誠實):`new modules engines/*`(另線引擎收容件,檔名帶 (2)/(3))只去重未入 intake 冊上(Z17);並行線 `via-panorama` 的 policy_append/registry_sync 會自動寫律冊與元件冊——併線後冊已聯集,它再跑可能重複追加 → **先不要跑 via-panorama**,批512 對表後放行(Z19);SRE 三試(Z15)仍等你貼。

#### 一貼即用(批511)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h                 # 併線後的樹(含你那條線 + vdf 新版)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0201
via-vrnlogic sync-db              # 律 29 + lessons 19 入六本庫
via-vcgc                          # 唯一對接口:元件冊 4749 · 二段環境復原燈
via-rungate                       # 並行線預設:vdf,vrn 各 3 站有界;v0103 會印 [INTERP] 解譯器病因(貼回)
via-ryg vdf,vrn -Timeout 600      # 並行線預設 profile=test(有界);production 用 -Full
via-firstpage                     # 應為 命中 48 · 部分命中 16(秒級)
$env:PYTHONHOME; $env:PYTHONPATH; Get-Content C:\Users\tonyk\envs\via_vdf_312\pyvenv.cfg   # Z15 診斷,一起貼
```


### 一-o · 批512 · 「要用的閘就打開 類似參數功能引擎就整合優化」+ Z15 診斷實錄(PYTHONHOME 空 · PYTHONPATH=bootstrap · venv=C:\Python313 3.13.7)

| 量到 | 判讀 | 做了 |
|---|------|------|
| `$env:PYTHONHOME` 空;`$env:PYTHONPATH` 只有 bootstrap;`via_vdf_312\pyvenv.cfg`:home=C:\Python313、3.13.7、`python -m venv` 建的 | 環境變數層清白;venv 是標準 venv,不是 uv | 三試(-E/-S/-I)你沒跑到,但 RunGate 自己的 `-c` 探針已證明:**-c 在倉根 import re 過**,**站以檔案起跑必炸**(vdf/vrn/vap 全站 0.2s SRE module mismatch);而匯流排在同一 via_vap_312 跑 vap 引擎正常(pyarrow 半拆、pandas 缺是真的缺) → 病在「站的子行程環境/cwd 層」,不是 venv 本體 |
| 你的樹還是批509(Register v0200、Grid v0302、Bus v0122、ENG072 v0125) | 批510/511 沒拉;`git pull --ff-only` 那行沒跑 | 這批區塊第一行還是 pull |
| RunGate 與匯流排各寫一套子行程環境 | 兩處=Hydra(L30) | **RunGate v0104**:站環境改用匯流排 `child_env()`(只寫一處)、cwd 改匯流排慣例暫存夾(批477 那課)、站 FAIL 印 **where**(traceback 最內層 File 路徑=哪一份 re/_compiler.py)、解譯器探針加「引擎夾當 cwd」試 + `re.__file__` 對 base_prefix(不在 base 下=STDLIB_SHADOW 印路徑)、庫探針本身炸=探針失敗不是缺庫(不再開補庫令)、`--approve-install` 過同意閘(L07);十五檢 15/15 |
| 「要用的閘就打開」 | 操作員授權:一貼即用可直接列 `$env:VIA_NET_CONSENT='YES'` 與 `--approve-install`(你貼=你的手);AI 端仍不自設 | L07 加 note;安裝仍過 L19(RunGate GREEN)——RunGate RED 的根因是解譯器,裝庫治不了,所以次序是:診斷 → 修解譯器層 → RunGate → 補庫 |
| 「類似參數功能引擎就整合優化」 | 立 **L30 相似整合律**;批511 v0103 併線切片把 10 個既有函式複製了一份(自測仍綠看不出)→ LL21 | v0104 從並行 v0102 乾淨重建;Z20 列整合候選(VCGC panorama vs recover、new modules engines 副本、UI 再生器) |

沒做(誠實):SRE 根因仍要你機器的 where 路徑才定(v0104 會印);`via-panorama` 仍先不要跑(Z19)。

#### 一貼即用(批512;閘照你的令直接列)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName   # v0201
via-rungate --family vdf                                                       # v0104:看 [INTERP] re=… 與每站 where: 那行
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe "functional modules\VDF\engine\vdf_input_matrix_v0100.py" --selftest 2>&1 | Select-Object -First 14   # 完整 traceback
& C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe -c "import re,sys;print(re.__file__);print(sys.path)"
Test-Path C:\Python313\python313.zip; Get-ChildItem C:\Python313 -Filter *.zip
git ls-files --others "functional modules\VDF\engine" "functional modules\VRN" "functional modules\VAP\engine" | Where-Object { $_ -match '\.py$' } | Select-Object -First 20   # 未追蹤的 .py=遮蔽嫌疑
# where 指到 C:\Python313\Lib 以外的 re → 那個檔/夾就是遮蔽,刪掉(你的手)再 via-rungate
# where 指到 C:\Python313\Lib\re 本身 → venv 本體錯配,重建(你的手):
#   Remove-Item -Recurse -Force C:\Users\tonyk\envs\via_vdf_312; C:\Python313\python.exe -m venv C:\Users\tonyk\envs\via_vdf_312
#   $env:VIA_NET_CONSENT='YES'; via-rungate --family vdf --approve-install      # 補庫道(不受 L19;閘照你的令)
```

---

### 二 · 操作員機器實況(他貼的 EnvManager v0300 AUDIT,run ENV-20260914_112000;直接當量測)

| 事實 | 影響 |
|------|------|
| 48 境在 `C:\Users\tonyk\envs` | 工具冊 `VIA_ENV_ROOT` 對得上 |
| `via_vrn_312` / `via_vdf_312` / `via_vap_312` / `via_paddle_311` 全是 **Python 3.13.7**(名不符實) | 冊上記 `python_measured`;不改名(EnvManager 才是境主) |
| `via_paddle_311`:easyocr 1.7.2 · paddleocr 3.3.1 · pytesseract | ENG072 OCR 派送目標(`_ocr_env_python()` 找它;`VIA_OCR_DISPATCH=1` 強制) |
| `via_vrn_312`:paddleocr 3.7.0 · torch · pymupdf · pdfplumber · reportlab;**無 easyocr** | 雙引擎階梯的 easyocr 段走 paddle 境 |
| `via_vap_312`:**pyarrow 半拆**(dist 名單缺)、seaborn 缺 | `via-envtools` 會列 REPAIR/INSTALL;裝是他的手 |
| `via_core` 14 件白名單境 | 批498 ⑤:永不排裝非白名單件 |
| `via_vdf`(38 件,py3.12,numpy 1.26.4)= 登錄 profile;`via_vdf_312` 未登錄(advisory) | **哪一境是 VDF 正境=操作員決定**(見三-U) |
| MIGRATION_REQUIRED:camelot_311 · paddle_311 · vif_aio · vif_core · vmt_pm | EnvManager 的事,本系統只讀不搬 |
| `paddleocr 3.x` 不吃 2.x 參數(`show_log` / `use_gpu` / `use_angle_cls`) | ENG082 `install_paddle_compat()` 已剝(批493 900 秒根因) |

---

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

## 九 · 掉球清單(來源 VIA_DroppedBalls_B507.md;列 32 · 未結 30;只增不減,結案劃線)

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
| Z13 | 批508 環境復原(L24)真跑:你機器 `via-envrecover` → `-Execute -Approve`(① 還原)→ `via-rungate` → 再 `-Execute -Approve`(② 順序裝);容器只有唯讀計畫 | 操作員的手 | 操作員 | 貼回 `via-envrecover` 與 `via-vcgc` 二段 |
| ~~Z14~~ | ~~操作員機器上的並行線不在遠端任何分支;要先推到側枝才能併~~ | **已結(批511)**:側枝 `local/parallel-b508-09151416` 已推、已併入本線(撞名者高版號另起;律/lessons 聯集;.via_envmanager 不入倉;孿生去重 45 件) | — | — |
| Z15 | via_vdf_312/via_vrn_312/via_vap_312 解譯器壞(SRE module mismatch):已貼 PYTHONHOME 空 · PYTHONPATH=bootstrap · pyvenv.cfg home=C:\Python313 3.13.7(python -m venv);-c 探針過、以檔案起跑必炸、匯流排同 venv 跑 vap 正常 → 差在站的子行程環境/cwd 層;RunGate v0104 印 where(traceback File 路徑)+ 引擎夾 cwd 試 + re.__file__ | 等實錄 | 操作員 | 貼回 `via-rungate --family vdf` 的 [INTERP]/where 行與手動 traceback |
| Z16 | PARTIAL 16 件(Z1)自批510 起例行跑不再重燒 OCR(部分命中);要重抽=你機器 `via-firstpage -RetryFailed`(涵蓋 PARTIAL);矩陣 vrn_firstpage 應不再 600s TIMEOUT,貼回驗 | 操作員的手 | 操作員 | 貼回 `via-ryg vrn -Timeout 600` 的 vrn_firstpage 秒數 |
| Z17 | 並行線 PANORAMA_HANDOVER-v0103「已列入下一輪」:Windows VRN 三站真實失敗斷言與 OCR runtime 自動收集、VETF 快照日期覆蓋 vs 持股完整性、gap plan 只代表查庫完成;`new modules engines/*` 另線收容件(檔名帶 (2)/(3))候裁入 references/intake | 未做 | AI | 下一批照該檔「已列入下一輪」逐項 |
| Z18 | 批510 我把 vrn_firstpage 600s TIMEOUT 歸因給「16 件 PARTIAL 每跑重燒 OCR」——你的實錄證明那 16 件是數位 PDF(DUAL_ZONES,合計 30.89s);600s 是並行線 panorama 自己的 vrn_firstpage 跑法,不是本線;PARTIAL_HIT 仍有效但歸因改正 | 已在 一-n 更正 | AI | 無 |
| Z19 | 並行線 `via-panorama` 的 policy_append/registry_sync 會自動寫律冊與元件冊;併線後冊已聯集(L26–L29 orig_id),它再跑可能重複追加 → 先不要跑;要對表(它的 id 判斷 vs 聯集後 id) | 未做 | AI | 批513 對表後放行 |
| Z20 | 「類似參數功能引擎就整合優化」(L30)候選:RunGate 站環境→已改用匯流排 child_env(批512);VCGC panorama 動詞 vs MDL135 recover(還原/補抓);`new modules engines/*` 副本引擎 vs functional modules 正本;VIA_UI_* 多頁再生器 | 部分做 | AI | 逐對比對,只留一處 |
| ~~W~~ | ~~8 件 FAIL_HIT 首頁件重抽~~ | 已結(批503) | — | 64/64 |

