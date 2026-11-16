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
