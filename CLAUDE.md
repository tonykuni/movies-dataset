# 給 AI 的讀檔規則(批707;L65 Token 撙節律)

**系統對等獨立(政策 L123 修訂 L120 · L128 VRN 統稱 · L129 各自註冊;操作員 2026-11-13 令「VRN-2 為主 VRN-1 為輔 整合後通稱 VRN」「VRN VDF VCGC 獨立系統 各自註冊」)**:
VRN · VDF · VCGC(另有 VQG · VAP)各是獨立系統,各是自己系統的入口(VCGC = `CGC_MDL149` 主控台 · VDF = `VDF_SystemManager` 尾版 ·
VRN = `VRN_SystemManager` 尾版 / `ActivateVRN-2.py`:VRN-2 為主體,VRN-1(另一團隊的倉,不在本倉、只讀)為輔,經 `VRN2_PeerBridge` 借用補強),
互不干涉(不改他系統的正本 / 冊 / 號 / 檔)、互相只讀監控(看對方自報的燈與收據,只攤開不代修)、各自獨立運作。
系統名稱寫 VRN / VDF / VCGC / VQG / VAP;只有談來源、借用或倉位細節時才分開寫 VRN-1 / VRN-2(L123 ② 對系統名稱一項由 L128 取代)。
各系統各自以自己的代碼註冊(VIA-VRN-* · VIA-VDF-* · VIA-VCGC-* · VIA-VQG-* · VIA-VAP-*),尾版帶編號 · 版本 · 註冊時間(L129)。
下文的 VCGC 指令是 **VCGC 自己的** 工具與檢查(省 Token 卡、交接、串測),不是 VRN / VDF 的唯一入口或閘門。

**第一步(操作員 2026-09-29 令 · 政策 TOKEN-1):先過 VCGC 的省 Token 步,照它給的卡讀檔。**

```bash
V=$(ls "VeritasIntelligenceAnalytics/supportive modules/registry/"CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | tail -1)
VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt   # 別接 | head:截斷的 BrokenPipe 會被記成 VCGC 失敗
```

- 卡上是**經 VCGC 啟用**(鎖冊 `VIA_ToolVersion_Lock_v0100.json` 的 `token` / `nlp`)、**實測過**的工具,指令可原樣貼上:
  `read`(骨架卡)→ `slice`(一個定義)→ `digest`(日誌只留判決行)· `--if-etag`(沒變回 304)· `pack`(整夾索引)· NLP `--brief`(長文摘要)。
- v0117 起另有 `chain <家族名>`(薄尾版本鏈圖:誰是本體、誰蓋了誰)· `.json` 用 `read`(兩層卡,`--depth N`)、`slice <檔> <JSON 路徑>`(`a.b[0]` · `[-1]` · `[*]` · `[鍵=值]`)· `.jsonl` 用 `read`(欄位次數 · 首末列)。
- VCGC 每個動作的第一行都是這一步的短版;這一步紅(沒啟用 / 鎖檔被改 / 實測不過)VCGC 就停,不讀政策、不開子系統。
- 工具換版只經 `via-vcgc tools activate token <CGC_MDL158_…_vNNNN.py> --apply`;不要自己取尾版。
- 原檔比卡片小(約 40 行內)直接看;不把原文貼回對話。

**工具優先(操作員 2026-11-19 18:17 令 · VCGC-REQ235;律號待登)**:AI 執行任何指令之前,先讀本檔(CLAUDE.md),再看一次省 Token 與支援工具的註冊清單,有現成功能就優先用它,不自己另寫、不整檔讀。

```bash
E=$(python3 -c "import json;print(json.load(open('VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v0100.json',encoding='utf-8'))['token']['path'])")
python3 "$E" tools    # 註冊清單:鎖冊每一家的現役檔 · VIA-TOOL 號 · 做什麼 · 何時用 · 指令(三數 應列 · 已列 · 略過)
python3 "$E" verbs    # 省 Token 工具全部動詞一行一個(read · slice · digest · pack · --if-etag · chain · delta · fix · cache …)
```

- 清單只讀三本冊合成,不另立正本:鎖冊 `VIA_ToolVersion_Lock_v0100.json`(誰現役)× 引擎版本冊 `VIA_EngineVersion_Register_v0100.json`(VIA-TOOL 號)× AI 功能卡 `VIA_AI_FunctionCard_SSOT` 尾版的 `tool_registry`(每家做什麼 · 何時用 · 指令)。工具換版或新增一家,三本一起更新;清單不是全綠就先回報。
- 每次接手先 `python3 "$E" delta`(只看跟上一輪比新增 / 已解的問題),不讀整張全景。
- 清單上的工具功能夠用卻自己另寫(讀表、記憶體控管、出網、PDF / OCR、摘要、日誌摘要)= 黃,收據寫理由。
- CGC_MDL158 每一版都要在本檔明寫動詞表 `VERBS`(主控台舊本體的省 Token 門用字串找 `"read"` 等字;轉接薄尾漏寫 → status 等動詞 rc 2,2026-11-19 實錄)。
- **工具新版登候選的號(操作員 2026-11-19 授權「授權 0253,之後同類照前例」)**:VCGC 還沒有發 VIA-TOOL 號的動詞前,工具新版登 `role=candidate` 照 REQ187 / REQ188 前例取號——共用 VIA-TOOL 空間(元件冊 + 引擎版本冊)在 本機 ∪ origin/main ∪ 開著的 PR 最大號之上,寫入後 `run CGC_MDL237_NumberingSystem audit` 的 XCODE / DUPREG 必須 0。只限工具候選列;其他號仍只由 VCGC 編號引擎發。

**先讀骨架卡,不讀原始碼。** 本倉的單檔動輒上千行,整檔讀進來很耗 token。大檔(約 >200 行)或整個資料夾一律先走全景代讀:

```bash
E=$(python3 -c "import json;print(json.load(open('VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v0100.json',encoding='utf-8'))['token']['path'])")   # 鎖版那一支(= token 卡上的路徑)
python3 "$E" read <檔或夾…>            # 骨架卡:匯入 · 定義樹(行號/簽章/首行說明)· AST 錯誤;給夾=一檔一行全景
python3 "$E" slice <檔> <名|Class.method>   # 只取一個定義的原始碼(帶行號)
python3 "$E" digest <日誌>             # 跑測日誌只留判決行(紅日誌誠實回 rc1)
```

- 唯讀:不寫檔、不執行被讀的檔(只做 `ast.parse`;`.ps1` 只做文字剖析)。
- 錯誤分兩層:治理七類(ACCEL/NET/VERB/HARDIMP/PINVER/SYSEXE/TALIB,只在 VIA 樹內算)+ 通用 AST 類
  (SYNTAX/DUPDEF/UNREACH/BAREEXC/SWALLOW/MUTDEF;v0114 起 +COMPILE(ast 過、compile 不過,例:橋注在 `from __future__` 前)+TAILAPI(尾版比前版少公開名稱又沒轉接);PowerShell:PSDUPFN/PSDOCSTR)。全都只報位置,不自動改。
- 先 `read` 看定義樹 → 用 `slice` 或帶 offset/limit 的讀檔只取要改的那一段。
- 操作員端同一個功能:`via-panorama read <路徑>` / `via-panorama slice <檔> <名>`;整張卡 `via-vcgc token`。

**不要**為了看說明而跑 `CGC_MDL064_SelftestGrid_v*.py --help`:它不吃 `--help`,會把整張格子跑起來並重寫已追蹤的檔(批707 實錄 21 檔)。單站用 `--only <站名子字串>`。

**交接防遺漏（VCGC-REQ075；2026-09-29）**：每次接手在 token 後，經 VCGC 主控台(VCGC 自己的入口;四系統對等,L123)執行 `handoff check`。
讀 `VeritasIntelligenceAnalytics/docs/handoff/HANDOFF_latest.json` 的摘要、pending 與相依變更，不從對話記憶推定已完成。
每次更新把新需求登錄中央需求冊／工作流冊，待辦只能帶理由轉態，不能消失；不同資料來源不得因值相同合併編號。
只重跑有相依變更的已宣告測試（`handoff test <case>`），接續 registry-sync、中央編號與 SDD 驗證，再 `handoff checkpoint`。
`handoff` 綠燈僅代表交接資料完整；`closeout_lamp` 才代表驗收，BLOCKED／REVIEW／缺證據絕不能寫成成功。
凍結來源不改；仍被薄尾引用的舊模組不搬走。測試證據與下一步詳見 `VeritasIntelligenceAnalytics/docs/handoff/README.md`。

**AI 必用功能(VCGC-REQ082;側線 2026-09-29 i)**:token 之後、動手之前跑 `VIA_FROM_VCGC=YES python3 "$V" functions`,照卡上的順序用。
卡的正本是 `VIA_AI_FunctionCard_SSOT_v*.json` 尾版(這裡不另抄;token 卡尾端也會印三行摘要)。必做三件:
改任何薄尾家族(出新版號檔)前先 `python3 "$E" chain <家族名>`;動到 SSOT / 正則 / 同義字 / 編號 / 命名 / 註冊前後各跑一次
`VIA_FROM_VCGC=YES python3 "$V" ssot panorama`;編號寫入後 `run CGC_MDL237_NumberingSystem audit` 必須遺失 0 · 改身分 0 · 重號 0。

**VCGC 全功能串測(VCGC-REQ085;側線 2026-09-30 b)**:`handoff check` 之後跑 `VIA_FROM_VCGC=YES python3 "$V" test --quick`(`enter` 與 PS 操作台也跑同一流程)。
站表正本 `VIA_VCGC_FunctionInventory_SSOT_v*.json`;新增 / 換版任何 VCGC 指令或模組後跑 `test`(整輪,沒變的站沿用),
新指令沒登盤點冊 = 黃;改過的尾版會自動跑它的 `--selftest`,版本與 UTC 時間只增寫進 `VIA_VCGC_FunctionLedger_v0100.jsonl`(要一起提交)。

**指令一律 Python · 加速器經 AST 導入而且真的生效(操作員 2026-11-25 20:32 令 · VCGC-REQ266;待登律號,不是律;細化 L117)**
原文:「所有指令都用 py 撰寫,注入 AST 導入加速器,強力執行」。
- AI 交付的每個動作(檢查、登記、編號、報告、啟動)都寫成 `.py`:新檔,或既有管理器的動詞。PS / 短令只做三件事:落檔、叫一個 python 動詞、開它產的頁。對話裡的多步 shell 只是 AI 自己的操作,不算交付。
- 每支新檔或新版號 `.py`:第 3 行 `# [VIA:ACCEL-BRIDGE:v0111]`,下接加速器橋區塊。
- 「導入」以語法樹為準:`python3 "$E" read <檔>` 的匯入欄要有 `VIA_SuperAccel_Module`。
- 「強力執行」= 執行時真的載到:載入後 `VIA_ACCEL is not None`。自測要有這一項;只有標記、載不到 = 假加速 = 黃。
- 有對外擷取的引擎,另經語法樹導入鎖冊上的網路工具;沒有對外擷取的不加。
- 交付前三檢:`ast.parse` + `compile` 過 · 自測連過三次 · 上面的載入檢查過。
- 例外(不注橋):交接冊 `frozen_sources` 的凍結原件。#728 在兩支 VRN 凍結原件上注橋,破了凍結,LAYOUT / NLP 因此轉紅;已依裁定 ⑮ A 在 #742 還原。

**同一則裁定的另兩項(架構規劃 v0101 待裁 ⑬ ⑭)**
- ⑬ 路由:不新設 AI 路由冊。AI 要知道某系統有哪些動作,讀那個系統 SystemManager 自報的 `verbs --json`;沒有這個動詞的系統 = 灰,VCGC 不代補。
- ⑭ VCGC MCP 加唯讀工具 `vcgc_read_card`(`CGC_MDL279_MCPServer` v0107 起,`.mcp.json` 已指到它)。
  - 它只回省 Token `read` 的骨架卡,不回全文、不給 slice。
  - 只收 VIA 根之下的 `.py .ps1 .psm1 .json .jsonl .md`。
  - VIA_Reports、資料 / 研報 / 收件類夾,以及 `.parquet .duckdb .csv .pdf` 等資料檔一律拒絕:能離開本機的只有程式碼結構與 schema。

---

**2026-11-16 操作員令(逐題定案;REQ 號與律號待 VCGC 登錄後補。登錄前是「待登需求」,不是律;與上文衝突時以上文與政策冊為準並回報)**

- **解凍**:RC-1 凍結與「新增延後」自本日解除。新增仍走原流程:需求冊 → 工作流冊 → 薄尾新版 → 該系統 manager 實測 → 註冊 / 編號 / SDD → `handoff checkpoint`。
- **省 Token 全程開著**:token 卡不只是第一步。讀任何約 >200 行的檔、任何資料夾、任何日誌,一律 `read` / `slice` / `digest` / `pack` / `--if-etag` / NLP `--brief`。沒走卡就整檔讀 = 黃,收據要寫理由。每批回報列出用了哪些省 Token 工具。
- **摘要三數**:任何全景、摘要、貼回包都帶「應掃 / 已掃 / 略過清單」,對不上 = 紅。省 Token 只能壓形式,不能縮範圍。
- **覆蓋率以生效計**:加速器 / 網路橋要「標記在 + 執行時載得到」才算覆蓋;只有標記 = 黃。
- **SKIP 不是綠**:缺依賴而跳過 = 黃;設計上不在本倉 = 灰。
- **自動監控**:VCGC / VDF / VRN-2 各自在自己的入口加 `monitor` 動詞,只彙總既有引擎(UNIT / INTEGRATION / SYSTEM / USER-TEST / 輸出驗證 / HTML U/I 同步;輸入 · 輸出 · 參數 · 時間範圍;MDL · ENG · CLS · FNC · LIB;ENV-LIB;資料庫)。不新增引擎、不跨系統改檔;沒有對應引擎的格子亮灰。
- **資料邊界**:能離開本機的只有程式碼結構與 schema。市場資料、研報、庫內容不送任何外部模型或代理;Graphify 只跑本機 AST 模式;OmniRoute 不進任何引擎的執行路徑;Claudeflare 不接。
- **驗收**:入口 MAIN 主機實跑綠 + 輸出對表頭冊驗過 +(VDF)選定範圍內無待補 / 未量 + 操作員用滑鼠走完該系統 U/I。
- **HTML U/I 已視覺鎖定**:顏色、字體、版面只取 `VIA_UI_FormatLock` / `VIA_UI_Template_SSOT` / 各系統 VisualSpec 的鎖定尾版;只同步內容與修壞掉的,不改任何視覺值。
- **VDF 擷取範圍**:全部台股全選全擷取;主動式台股 ETF 名冊全選 + 每日持股;加權、櫃買指數每日量價;財報只抓 `3017`、`3324`、`NVDA` 加上 VRN-2 研報出現過的個股(三大報表完整版);國際個股可增減(以 `NVDA` 為範例);其餘全擷取;族群起始時間可改,改一族整族一起改。只改範圍冊,不改擷取引擎邏輯。
- **一個主工作倉**:本機多份副本只認一份,其餘只標記、不同步改。工作倉在 OneDrive 而 token 紅在 I/O error 屬環境紅:停下回報,不繞過。

**過去一個月反覆重工的六個原因與解法**

1. 規則當天改、當天全面回補 → 新規則先登需求冊,只重跑相依有變的 case(`handoff test <case>`),不全量重跑。
2. 多線並行撞批號 / 版號 / MDL 號 → 取號前掃 本機 ∪ origin/main;先提交再編號;`audit` 三個 0。
3. 沒有驗收條件就開工 → 開工前先定 輸入 / 輸出 / 完成條件(可用 `/via-grill` 逐題問到定案);收據帶命令、rc、SHA。
4. 整檔讀、貼原文、重驗已鎖成功 → 走 token 卡;已鎖且位元沒變的不重驗;`reusable_successes` 直接沿用。
5. 把標記、單元測試、對話裡的「完成了」當成完成 → 只認生效率、主機實測、`closeout_lamp` 與 SDD。
6. 同一功能多份(副本倉、`_sha` 分身、相似引擎)→ 先 `chain` 看誰是本體;已有同功能就掛動詞,不另做。

本日交接、給 Cowork 的提示詞與跨 AI 工具矩陣:`VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_Handover_20261116_Night_Closeout.md`。

**2026-11-16 補強(來源:`VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_RecurringIssues_PolicyReview_20261116.md` 的十二個常見問題;同樣是「待登需求」,不是律)**

- **交出前先模擬桌機**:要操作員打的指令,先在容器用「Windows 路徑 + 家目錄當工作目錄 + 落後分支」跑一次;指令開頭自己定位倉根、檢查要跑的檔在不在,不在就印 fetch / switch 那一行。
- **併線先比兩邊**:動工前 `git fetch origin main` 並比對 本分支 ∪ origin/main 的版號與編號;同名不同內容以 main(已發布)為準,分支內容改發新版號。2026-11-16 實錄:兩線自 11-10 分開,53 檔撞名、`VDF_SystemManager_v0176` 與 `VDF_MDL017` 撞號(清單 `VIA_MergeMain_20261116_Conflicts.json`)。
- **刪舊版先證明**:在拿掉該檔的副本上把尾版每個動詞實跑一遍才准刪;懶載入、名字釘死前版的都算「用到」。
- **要求的目標缺一不綠**:輸入名單(代號 / 族群 / 序列)有一個沒結果,總燈不得綠,逐項點名。
- **掃描用語法樹**:判「有沒有 import / 出網 / 橋」用 AST,不用字串搜尋(VRN `MDL002` 被字串誤判為出網)。
- **單位與字形先統一**:跨來源比對前讀單位欄,金額統一百萬元(每股值不換);標籤全形轉半形、去空白再查表。
- **共用冊寫入要鎖**:作業系統檔案鎖 + 唯一暫存檔名 + 原子換檔;不刪別人的鎖。
- **跨平台位元組**:算雜湊前先統一成 LF;自測放一份 CRLF 檔。
- **長跑要有心跳、並行要有監工**:子行程每 30 秒內至少一行;過熱減道並暫停最新子行程,冷卻恢復,至少留一支在跑。
- **入湖範圍**:監控快照、執行紀錄、名單表不當資料入湖;擷取後跑 VDF `datamatrix`,多餘列 > 0 = 黃並點名。
- **`--help` 不得有副作用**:沒看過的工具先 `read` 骨架,不直接下 `--help`。
- **新檔不含本機路徑**;**閘收到錯形路徑當場拒絕、零寫入**;**頁面文字與底色對比 ≥ 4.5**。

**每天開機更新**:工作站 `pwsh -NoProfile -ExecutionPolicy Bypass -File "VeritasIntelligenceAnalytics\supportive modules\registry\via_boot_update.ps1"`(每日首跑才實跑;log 在 `VIA_Reports/boot_update_logs/`);容器是同鏈的 `via_boot_update.sh`(SessionStart 喚起)。它照常令自己開同意閘並自補套件,所以 AI 不代跑,由操作員的手啟動。收工跑 `via-vcgc handoff daily`。

**每日教訓帳(操作員 2026-11-16 令;待登需求)**:接手先讀 `VeritasIntelligenceAnalytics/docs/handoff/daily/VIA_DailyChecklist_latest.md`(問題 → 根因 → 處理 → 下次怎麼檢查);收工把當天新遇到的問題照同樣欄位加到 `VIA_DailyLessons_Ledger_v0100.jsonl` 帳尾(只增、不改舊列),再重生清單。

**2026-11-18 操作員令(待登需求,不是律;與上文衝突時以上文與政策冊為準並回報)**

- **指令模塊化、簡化**:要操作員打的指令一律一行,走各系統入口尾版的動詞;同一件事不給兩種打法。
- **重複功能先併再簡化**:先 `chain` 看誰是本體;差異補進本體家族的新版號、掛成動詞,不另做一支。刪舊版仍照「刪舊版先證明」。
- **動語法樹很小心**:注入或改寫一律先複製到 TEMP 做,`ast.parse` 與 `compile` 都過、自測過才落檔;批次修補用 VCGC 的 `CGC_MDL158 fix`(先乾跑看清單,再 `--apply`),收容夾、凍結來源、不在這次範圍的系統不動。
- **加速器覆蓋全部引擎、網路工具覆蓋對外擷取的引擎(如 VDF)**:以各系統引擎矩陣的 accel / net 兩欄為準(語法樹裡真的匯入 + 執行時載得到 + 鎖冊上的工具檔在);只有標記不算。
- **啟動順序**:第一步先降 CPU / DRAM 壓力並等系統靜下來 → 依這台機器的能力同時跑 **3~6** 支互不相干的流程 → 監工過熱就減道、暫停最新子行程,冷卻再恢復。這段用 Python 啟動器(`VDF_MDL022_SafeParallelLaunch` / `VRN_MDL260_SafeParallelLaunch` 尾版;VRN 的道數在 `VRN_ParamControl_SSOT` 尾版的 `slots_min` / `slots_max`),PS 只負責進環境與呼叫它。

**2026-11-18 補強二(來源:2026-11-16 ~ 11-18 操作員 19 則訊息的逐則整理;更早的原文已不可查,只剩摘要。同樣是「待登需求」,不是律)**

- **三系統各自能單獨啟動,SSOT 只有一套**:VCGC / VRN / VDF 各走自己的入口就能啟動與實測,不需要另外兩個在跑。SSOT 是同一套、權限不同:每個系統只寫自己的冊與自己的夾;讀別人的只讀;VCGC 只發號,不替 VRN / VDF 自己的正本發號(邊界閘擋下就照擋)。
- **範圍以當則訊息為準**:每批只做操作員那一則訊息與它點名的清單;途中看到範圍外的問題只記下回報,不動手。收尾報告要寫「範圍外改動檔數」,不是 0 就點名並說明。
- **完成一項收一項**:每完成一項就依序 註冊編號 → 寫鎖定帳(檔 · 版本 · UTC 時間 · 內容雜湊)→ 每日備份 → 提交推送 → 回報,不累積到批尾。
- **成功只增不減**:開工先讀鎖定帳與交接冊的已鎖成功數;收工再讀一次,變少 = 紅並點名少了哪一項。
- **交給操作員的 PS 只有一支**:它只負責進環境與呼叫各系統的 Python 啟動器;出新版時同一則回覆點名作廢的舊版。
- **VDF 每支擷取引擎都要能單獨啟動、單獨實測**;輸入參數依類別集中在參數冊,不寫死在引擎檔裡。
- **收尾成功的條件不能打折**:輸出驗證無誤 + HTML U/I 無誤 + 主機實跑。容器跑出來的結果一律標「容器」;連不到桌機時只能交一行指令並標「未在主機實跑」,不得寫收尾成功。
- **收尾報告用稽核寫法**:發現幾項、關了幾項、沒關的逐項點名並寫缺什麼證據;還有沒關的就不寫「收尾成功」。
- **同一系統跨日還沒綠**:先交「哪條驗收條件沒過 · 缺什麼證據 · 誰能補」再往下做。

- **舊短指令改走 Python**(操作員 2026-11-18):短指令背後的動作改成呼叫 Python 入口,帶加速器橋,並行時照「先降壓 → 3~6 道 → 監工」的安全機制;PS 只留進環境與轉呼叫。逐批改,每批先列清單再動。

**2026-11-24 操作員令「重工因素寫成指令的預設偵測 · 解決方案內建」(待登需求 VCGC-REQ255;不是律)**

- **重工守門預設跑**:出新版號、發號、推送、開 PR 之前一律先跑
  `python3 "$(ls VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_ReworkGuard_v*.py | sort | tail -1)" check --fetch-prs`(尾版;看已提交 + 工作樹)。
  紅 = 不推(已鎖被改 · 版號插到尾版底下 · 開著的 PR 同號同檔名 · 新冊版少了 base 的列 · 明文金鑰);黃照它印的「解法 / 指令」修,不修就在收據寫理由。
  13 類根因與解法:`… causes`;一週數字:`… report`。PR 守門 workflow 的 rework-guard job 跑 base 上的尾版(PR 改不掉)。
- **發號接在開著的 PR 之上**:編號引擎從本機冊尾 +1;開著的 PR 已用的號(MDL · SSOT · ENV · 分類碼)要先避開,發完再跑一次 check(2026-11-24 實錄:#722 / #730)。

**2026-11-24 操作員令「環境安裝規範」(待登需求 VCGC-REQ258;不是律。全文 `VeritasIntelligenceAnalytics/docs/VIA_Environment_EightHub_Policy_v0101.md`)**

- **順序固定,前一步不過後一步不做**:① 全面檢視 base · `via_core` · 所有 `via_*` 境(八路衝突檢查 + pip check + 多層 site 互撞 + 工具冊缺件 + 加速器)→ ② 有衝突風險:不新增,把風險移開、該境立刻重建(`via-envgov plan` → `via-envgov apply --approve` 的 REBUILD 段),重建後回 ① → ③ 檢查無誤後,沒裝的工具列入新增 → ④ 特殊環境及分類一律單獨安裝(Baseline `package_env_overrides` / `families` 成員不進 base)→ ⑤ 清華 · 阿里 · 官方三鏡像同時解析新增(零安裝)、推算裝後新增衝突 → ⑥ 寫新增計畫(全部釘版)→ ⑦ 直接執行計畫,不再測。
- **一行入口**:`via-health`(⑦ 之前全做);只查 `via-install --plan-check`;照計畫裝 `via-install --from-plan --yes`。不直接 pip;同意閘只在安裝閘子行程裡設。
- **多版本共存**:numpy、pyarrow 這類常用件允許不同 Python 版本 / 不同境各用各的版本;同一境多版遮蔽或 ABI 錯配才是要重建的風險。
- **不邊裝邊測**:不在安裝途中拆批重試、不在裝後整套重驗;要驗就是下一輪 `via-health` 的 ①。
- 跟「待操作員裁定」第 1 項的關係:本令把「有風險就重建」寫成規範步驟;重建仍走 `via-envgov apply --approve`(保留舊境與 LKGC),AI 不自己刪境。

**待操作員裁定(兩邊的話對不上,AI 不自己選邊;裁定前照較保守的一邊做)**

1. **已裁定(操作員 2026-11-18)**:授權 AI 開兩道同意閘、經 VCGC 安裝閘(`CGC_MDL056_InstallGate` 尾版)安裝套件、推送到 GitHub 的工作分支,不用逐次再問。界線:安裝只走安裝閘(不直接 pip);開閘只在執行那一步的行程裡設、不寫進任何檔;重建或刪除環境、合併 PR、改 .ps1 既有檔不在這次授權內。每批回報寫明用到哪一項。
2. 「相同功能只留一個」對上「成功只增不減」「仍被引用的舊模組不搬走」:只留一個是實體刪除,還是留檔標停用?(裁定前:不刪。)
   **部分裁定(操作員 2026-11-25 · VCGC-REQ262 第 5 節)**:「一旦確認最強／最穩定版本運作無誤,立即清理並刪除舊版與冗餘工具以釋放空間」→ 可以實體刪除,只刪沒人用的,三條都過才刪:
   ① `python3 "$E" chain <家族名>` 顯示沒有任何尾版經 PRIOR 鏈、glob 或釘死的名字載入它;② 照「刪舊版先證明」在拿掉它的副本上把尾版每個動詞實跑過;③ 鎖定帳的已鎖成功數刪前刪後一樣。
   薄尾鏈上的前版(尾版靠它跑)不在此列;刪除單獨一個 PR,逐檔列出三條的證據。
3. 「SSOT 同一」「透過 VCGC 整合套用」對上「互不干涉」:哪幾本是共用正本、誰能寫?VCGC 的工具能不能直接改 VDF / VRN 的檔?(裁定前:VCGC 工具只在該系統自己的範圍內套用,改到別的系統就還原。)
   **部分裁定(操作員 2026-11-19 18:10 · VCGC-REQ234)**:「VCGC/VRN/VDF/VAP/VCG 是獨立系統都由各自的 SYSTEM MANAGER 控制一切 · 獨立系統該有的功能分給各自系統 · VCGC 現在也是由一個獨立 VCGC SYSTEM MANAGER 管理(`CGC_SystemManager` 尾版;席位冊 tails.VCGC)· 政策管理大家一樣存取 · SSOT 同一冊 · VCGC 進行收尾」。寫入權沒有改:每個系統只寫自己的冊與夾、讀別人的只讀;「VCG」照錄,疑為 VQG,待確認。
   **部分裁定(操作員 2026-11-21 · VRN-REQ023)**:「他們全都是獨立的系統,他們當然可以擁有自己的一套資料」「同意 VRN 自己發號不用等 VCGC 核號」→ VRN 自己的號(引擎 VRN-E · 冊 VRN-B · 參數 VRN-P · 元件 VRN2-<類>)由 VRN 管理器自己發、自己定案(`VRN_SystemManager` v0279 起狀態 = 已確認(VRN 自發)、請號清單空)。VCGC 中央編號照舊只替 VRN 的程式檔發 VIA-VRN-* 號,邊界閘照舊擋 VCGC 替 VRN 正本發號。
   **部分裁定(操作員 2026-11-21 · VDF-REQ038)**:「同意 VDF 也自己發號 你決定」→ VDF 帳本(`VDF_SSOTSync` v0103 起)的 VDF-<類>-#### 就是 VDF 自己的定案號:待核條目一律轉已確認(VDF 自發)、請號清單空、不再讀 VCGC 核發冊;先前已由 VCGC 核發的 ssot_id 與「已確認(VCGC)」照留(歷史不改寫)。
4. 「不擴大範圍」對上同一則裡的「新增功能」「注入全部」:新增算不算外擴?(裁定前:訊息裡點名的才做。)
5. 連不到桌機時,「自動完成」做到哪裡算完?(裁定前:容器驗證 + 交一行指令,標未實跑。)
6. **已裁定(操作員 2026-11-20)**:「頁面文字與底色對比 ≥ 4.5」對上「HTML U/I 已視覺鎖定」→ **用鎖定色、不改**。U/I 驗收時對比不足照實列出(資訊),不改顏色、不當成要修的紅。
7. (2026-11-25 · VCGC-REQ262 第 3 節)「所有 `.py` 強制導入 Polars · DuckDB · Numba · NumExpr · orjson」對上「加速器 = 鎖冊上的 `[VIA:ACCEL-BRIDGE]` 橋」與「系統獨立:引擎在沒裝某些件的境也要載得起來」:加速器覆蓋 100% 是指每個檔都掛橋,還是每個檔都匯入這五個運算庫?(裁定前:指掛橋;五個運算庫只在用得到的引擎裡用,照環境規範裝在該境。)
8. (2026-11-25 · VCGC-REQ262 第 4 節)「偵測到依賴衝突立即銷毀整個受損環境重建」對上第 1 項「重建或刪除環境不在授權內」與 REQ258「重建保留舊境與 LKGC」:AI 能不能自己銷毀環境?(裁定前:不能;AI 只出 `via-envgov plan`,`via-envgov apply --approve` 由操作員下。)
9. (2026-11-25 · VCGC-REQ265)附件提案「同一引擎最多留現行版 + 兩個備份(N-2),其餘刪除」對上「只增不減」「仍被引用的舊模組不搬走」:要不要把 N-2 定成規則?(裁定前:不刪,只標退役候選;刪除仍照第 2 項三條件。)
10. (2026-11-25 · VCGC-REQ265)架構規劃要求 `via-vdf` / `via-vrn` 直指自己的啟動器、不經 VCGC 中樞,但要改既有 `.ps1` / `.cmd`,不在第 1 項授權內:授不授權?(裁定前:只出規格與演練,不改既有檔。)

**2026-11-18 補強三(操作員當晚訊息:「系統獨立主要是避免任一系統尤其是 VCGC 升級更動造成全面癱瘓」「加速器覆蓋每個動作 100%」「45 分鐘太慢」;待登需求,不是律)**

- **系統獨立怎麼驗**:在一份拿掉 `supportive modules/registry/CGC_*.py` 的副本上,VDF、VRN 各自的入口與現役引擎要載得起來;載不起來 = 紅並點名。用到別的系統模組的地方一律要有退路(同判法、沒同意照樣關),不准開檔就丟例外。出新版前跑一次這個演練。
- **各系統的 Python 啟動器就是該系統的入口**:子行程帶自己的入口標記;引擎的閘不得只認別的系統(含中央 PS)的入口。
- **自測綠不算擷取過**:對外擷取的引擎,每晚至少一次開閘的限量真擷取(空庫或副本庫);自測要有一檢走「庫已存在 + 來源有回來」那條路。
- **自測不吃本機狀態**:自測一律在暫存夾造資料;「這台剛好沒資料才會過」不算。
- **加速器覆蓋以語法樹為準、全系統算**:VCGC、VDF、VRN、VQG、VAP 的現役尾版都要真的匯入;只有標記那一行 = 黃。
- **註冊同步與編號前工作樹要全乾淨**(未追蹤的容器產物先清);背景有 git 動作時,提交後看 `git log -1` 與 `git status`。
- **慢要先量再說**:回報耗時要分開寫「空庫從頭抓」與「平常增量」,並點名最慢的那一支與原因。

<!-- VIA:CLAUDE-CH5-6:BEGIN -->

**2026-11-24 操作員令(第五 · 六章原文照錄;待登需求,不是律;與上文衝突時以上文與政策冊為準並回報)**

---

## 5. 備份與 Graphify 快照協議（Backup & Snapshot Gate）

當使用者要求「進行備份」、「建立快照」或「執行 Graphify 備份」時，**嚴禁未經確認直接覆蓋既有檔案或掃描 `via_database` 實體大檔**。若使用者未在指令中指定參數，AI 必須先拋出以下 **6 題高密度選擇題組合**（單次互動鎖定邊界，等待使用者以快捷口令回覆後再執行）：

### 5.1 進場必問 6 大問題組合（Compact Clarification Matrix）
| 編號 | 確認維度 | AI 進場必問具體問題 | 選項與預設安全護欄（Guardrails） |
| :--- | :--- | :--- | :--- |
| **Q1** | **備份範圍（Scope）** | 本次備份的納管範圍為何？ | • **A（預設）**：僅引擎倉 `movies-dataset`（程式碼 + 三本尾版冊）<br>• **B**：引擎倉 + 隔離區 `sapphire-prism-baker-amber` 差異快照<br>• **C**：含 `VIA_Database_Topology_Index.md`（※嚴格排除 `via_database` 實體大檔） |
| **Q2** | **Graphify 備份層級** | Graphify 圖譜要採用哪一種備份模式？ | • **Mode A**：僅複製 `graphify-out/graph.json` 與 `GRAPH_REPORT.md` 快照<br>• **Mode B**：先執行 `graphify update .` 與 `--wiki`，再打包整個 `graphify-out/`<br>• **Mode C（最推薦）**：先跑 `Sync-ViaWikiAndBooks.ps1` 刷齊三冊與圖譜，綠燈後再打包 |
| **Q3** | **備份存放位置** | 備份壓縮檔要放在哪個路徑？ | • **本地隔離區（預設）**：本機非 OneDrive 磁碟或專案外的 `_via_backups/`（避免 OneDrive 同步鎖死）<br>• **倉內暫存**：專案根目錄 `.sdd_bak/`（已列入 `.gitignore` 與 `.graphifyignore`） |
| **Q4** | **版本輪替上限** | 舊有備份快照如何清理？ | • **5 份輪替（預設）**：同一類型最多保留最新 5 份，超出自動刪除最舊快照<br>• **單次覆蓋**：僅保留最新 1 份基準快照 |
| **Q5** | **前置門禁檢查** | 備份前是否強制執行唯讀健康檢查？ | • **Fail-Closed（預設）**：先跑 `Invoke-VcgcMasterGate.ps1` 與 AST 簽章檢查，紅燈即中止備份<br>• **強制快照**：忽略警告，直接對現狀進行原樣封存 |
| **Q6** | **Git 狀態連動** | 本地備份完成後，是否需要操作 Git？ | • **純本地歸檔（預設）**：不執行 `git commit`，避免備份動作干擾版本紀錄<br>• **建立安全檢查點**：同步建立一筆本地 `git commit -m "chore(backup): ..."` |

- **快捷回覆口令範例**：使用者回覆「`Q1選C、Q2選Mode C、Q3放本機隔離區、Q4保留5份輪替、Q5走Fail-Closed、Q6純本地歸檔，直接執行`」即可直接啟動。

### 5.2 備份執行與安全鐵律
- **原子備份與輪替上限**：所有本地備份檔必須先寫入暫存檔（`.sdd_tmp`）驗證非空後再移動至備份區，同一目標最多保留 **5 份**歷史快照。
- **禁區隔離**：嚴禁將 `graphify-out/` 或 `.sdd_bak` 備份檔當作新的 SSOT 冊註冊進 `VIA_VRN_LogicArchitecture_SSOT_v0100.json`。

---

## 6. 每日收工自我檢查與蟲攻擊盤點協議（4-Gate Audit Protocol）

當使用者要求「自我檢查今日成果」、「盤點錯誤與蟲攻擊」或進入每日收工覆盤時，AI 必須遵循 **Evidence-First（證據優先）、Zero-Token（指紋與狀態卡導向）、Fail-Closed（紅燈阻斷）** 三大原則，禁止空泛回答「已完成」，每項結論必須綁定 `Commit SHA`、`檔案路徑`、`AST 節點` 或 `Exit Code`：

### 6.1 四層防禦稽核問題組（跨 AI 通用標準）
1. **第一組：今日實質成果與架構對齊盤點（Deliverables & SSOT Alignment）**
   - 列出今日在引擎倉（`movies-dataset`）與隔離區（`sapphire-prism-baker-amber`）實際寫入/修改的檔案、對應 `Commit SHA` 與解決的問題。
   - 逐一標註三本尾版冊（`LogicArchitecture`、`Policy_Laws`、`ToolRoster`）與衍生產物（`graphify-out/graph.json`、`graphify-out/wiki/index.md`、`VIA_Database_Topology_Index.md`）為 `SYNCED` 或 `OUT_OF_SYNC`。
   - 確認今日是否遵守 `CLAUDE.md` 省 Token 規範，有無違規全倉掃描或誤觸 `via_database` 實體路徑。
2. **第二組：今日已發生錯誤與修補軌跡（Errors & Incident Log）**
   - 列出今日遭遇的所有報錯（`SyntaxError`、BOM 編碼異常、DB 檔案鎖定 Lock、權限拒絕或路徑錯誤），說明根因（RCA）、修復手段，以及**如何透過自動化守衛/門禁防止再次發生**。
3. **第三組：蟲攻擊與九頭龍回歸偵測（Bug Attacks & Hydra Regressions）**
   - **公開介面保全（`VF_FUNCTIONS_KEPT`）**：確認修改或升級尾版的 `.py` 模組未遺失或破壞既有的公開方法（如 `VDF_SystemManager.collect()`）。
   - **雙橋接與路由繞道**：確認最新尾版 `.py` 完整掛載 `CGC_MDL158` 加速器橋（且位於 `from __future__` 下方），且無任何模組繞過 `via-vcgc` / `SystemManager` 直連 `via_database`。
   - **靜默失敗與快取毒化**：確認無遇到缺值自動補 0 或回傳 `NODATA` 掩蓋異常的情況（嚴守 `FAIL_CLOSED`）。
4. **第四組：未解決技術債與跨 AI 交接狀態卡（Unresolved Issues & Handoff Card）**
   - 依風險排序（`P0 阻斷` / `P1 高風險` / `P2 優化`）列出遺留紅燈、警告與待合併隔離區差異。
   - 最後必須輸出 **250 字以內的標準跨 AI 交接狀態卡**：
     - `[整體健康度]`：`GREEN` / `YELLOW` / `RED`
     - `[最新基準點]`：分支名稱 @ Commit SHA
     - `[今日已閉環]`：（限 3 點以內，附證據）
     - `[明日第一動]`：（明確指出下一個要執行的單一指令或檔案座標）

<!-- VIA:CLAUDE-CH5-6:END -->

<!-- VIA:CLAUDE-ADDENDA-20261125:BEGIN -->

**2026-11-25 操作員補充條文「系統架構與工程規範」七節(待登需求 VCGC-REQ262;不是律。原文照錄於需求冊 v0311;這裡只寫本檔原本沒有的部分,已有的只指出在哪一段,不重抄;與上文衝突時以上文與政策冊為準,並列入「待操作員裁定」)**

- **1 系統邊界與 SSOT**(已有:開頭「系統對等獨立」· 補強二「SSOT 只有一套」· 補強三「系統獨立怎麼驗」)
  - 跨系統共享的只有 SSOT 冊與標準正則(例:台股四碼、首位非 0 · Bloomberg `TT` 後綴 · 動態滾動參數規範);其餘程式、資料、參數一律各系統自有。
  - 同步、比對、引用以**功能檔名**為準:家族名 + `_vNNNN`(例 `VDF_ENG066_GlobalUniverse_v0103.py`)。不靠路徑或號碼猜;改名就是新家族,要登需求。
  - 原文列的 VPNS 照錄;VPNS 還沒有席位(席位冊 tails 沒有它),登席位前不當獨立系統管。
- **2 SDD 與 AST 節點手術**(已有:「解凍」的新增流程 · 「動語法樹很小心」)
  - 先規格:需求冊 → 工作流冊寫好輸入 / 輸出 / 完成條件,再動程式。
  - 改程式固定四步,不整檔覆寫:`read` 找到節點 → `slice` 只取那一個函式或類別 → 在 TEMP 改好、放回原位(`ast.parse` 與 `compile` 都過)→ 單元測試(該檔 `--selftest`)+ 整合測試(`handoff test <case>`)。
  - 薄尾家族照舊出新版號檔、前版一字不動;「放回原位」指新版檔裡的同一個節點。
  - 改完用 `read` 看 TAILAPI 類必須 0(尾版沒少公開名稱)。原本的 `clones` / `baseline` / `sigdiff` 在已關閉、未合併的 #689,不在現役 v0121。
- **3 PS / PY 分工與 100% 覆蓋**(已有:L117 · 「舊短指令改走 Python」· 補強三「加速器覆蓋以語法樹為準」)
  - PS 只留系統啟動、備份、讀取備份這類短指令;任何判斷、迴圈、清單處理都寫在 Python。
  - 加速器覆蓋 = 每個 `.py` 的 `[VIA:ACCEL-BRIDGE]` 橋語法樹裡真的匯入,而且執行時載得到(`VIA_SuperAccel_Module` → `SUP_MDL737` 尾版)。
  - 網路工具 100% 只算有對外擷取的檔。
  - Polars 等五個運算庫怎麼算,見待裁定 7。
- **4 VCGC 全景巡檢與環境衝突**(已有:環境安裝規範 REQ258,八路表與三鏡像全文在 `VeritasIntelligenceAnalytics/docs/VIA_Environment_EightHub_Policy_v0101.md` · 每天開機更新 · 收工 `handoff daily`)
  - **每日第一個動作**:token 卡 → `via-health`(環境 ①)→ `python3 "$E" delta`。
  - **每日最後一個動作**:`via-vcgc handoff daily`。
  - 兩次都要點名「標記在、執行時載不到」的加速器(假加速 = 黃)。
  - 原文「8 個衝突偵測套件」就是八路表那 8 路(identity · ABI 標籤 · 需求不滿足 · 同境重複 / 遮蔽 · `pip check` · 工具冊缺件 · BASE 禁放家族 · 特殊執行檔),不另立一份清單。三鏡像 = 清華 · 阿里 · 官方 PyPI(⑤)。
  - 中高衝突風險或很難編譯的件(原文「ripple」照錄,實際套件名待確認)走 ④ 分流,裝進專屬境(Baseline `package_env_overrides` / `families`),不進 base 或 `via_core`。
  - 多版本白名單:numpy 這類基礎科學計算件與 Python 3.10–3.13 可以多版並存;同一境裡多版遮蔽仍是風險。
  - 「銷毀重建」見待裁定 8。
- **5 工具去重與清理**(已有:「重複功能先併再簡化」· 「刪舊版先證明」· 待裁定 2)
  - NLP · Layout · 加速器 · 網路工具的汰弱留強:先用 `tools` 清單看每家現役檔,再 `chain` 找本體;刪除照待裁定 2 的部分裁定。
  - 倉內不放沒納管的測試腳本或備份殘檔:暫存一律放 TEMP;`.sdd_bak` · `.sdd_tmp` · `graphify-out` 已列入 `.gitignore`。
- **6 省 Token 與 Graphify**(已有:「第一步」· 「工具優先」· 第五章)
  - **工具缺口先說**:token 卡與 `tools` 清單沒有合用的動詞時,回覆裡先寫一行「缺口:要做什麼 · 最接近的現有動詞 · 差在哪」,再用通用方法(標準 AST、小腳本)完成,收據記黃。
  - Graphify 摘要只讀本機產物,資料邊界照舊。
- **7 每日復盤與重工歸因**(已有:「每日教訓帳」· 重工守門 REQ255)
  - 開工的第一則回覆先列前一日教訓:讀 `VIA_DailyChecklist_latest.md`,只列條目,不貼全文。
  - 前一日有重工(重改 · 環境報錯 · 退回重做)就逐項寫「原因 · 防呆對策」,加到 `VIA_DailyLessons_Ledger_v0100.jsonl` 帳尾。
  - 對得上 `VIA_ReworkGuard … causes` 13 類的,寫出類別。

<!-- VIA:CLAUDE-ADDENDA-20261125:END -->

<!-- VIA:CLAUDE-VCGC-FIRST-20261125:BEGIN -->

**2026-11-25 操作員令「接下來所有動作 AI 都要優先選擇 VCGC 的動作去完成」與架構規劃(待登需求 VCGC-REQ265;不是律)**

- **選動作的順序**(每一步都照這個):
  1. VCGC 現成的動作:token 卡上的工具 · `tools` / `verbs` 清單 · VCGC 主控台與管理器的動詞 · `via-*` 短指令(`via-help` 列全部)。
  2. 該系統自己 SystemManager 的動詞。
  3. 都沒有才自己寫:先在回覆寫一行「缺口:要做什麼 · 最接近的動作 · 差在哪」,收據記黃。
- **界線不變**:
  - VCGC 的動作是工具,不是閘門。
  - VDF / VRN 的業務動作(擷取 · 分析 · 報告 · 發自己帳本的號)走它們自己的 SystemManager,VCGC 不代做。
  - 會寫到別的系統的檔或冊的 VCGC 動作不做,改交該系統。
- 收據寫「用了哪個 VCGC 動作」;能用卻沒用、自己另寫 = 黃,寫理由。
- **架構規劃**:`VeritasIntelligenceAnalytics/docs/VIA_SystemArchitecture_SDD_v0100.md`,是規劃稿,等操作員核准。
  - 核准前只做唯讀的 P0 基線與 P2 對位,不動程式。
  - 核准後依它的 §9 階段做,VCGC 先。
  - 新增或改任何 SystemManager 動詞,先對它 §3 的標準契約(五系統同一份動詞表與 rc)。

<!-- VIA:CLAUDE-VCGC-FIRST-20261125:END -->
