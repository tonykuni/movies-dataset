# 給 AI 的讀檔規則(批707;L65 Token 撙節律)

**三系統對等獨立(政策 L120;操作員 2026-10-10 令「不再視為一入口 三系統獨立」)**:VCGC · VDF · VRN 三個 SYSTEM MANAGER 對等,
各是自己系統的入口(VCGC = `CGC_MDL149` 主控台 · VDF = `VDF_SystemManager` 尾版 · VRN = `VRN_SystemManager` 尾版),
互不影響(不改他系統的正本 / 冊 / 號 / 檔)、互相只讀監控(看對方自報的燈與收據,只攤開不代修)、各自獨立運作。
下文的 VCGC 指令是 **VCGC 自己的** 工具與檢查(省 Token 卡、交接、串測),不是 VDF / VRN 的唯一入口或閘門。

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

**交接防遺漏（VCGC-REQ075；2026-09-29）**：每次接手在 token 後，經 VCGC 主控台(VCGC 自己的入口;三系統對等,L120)執行 `handoff check`。
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
