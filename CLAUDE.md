# 給 AI 的讀檔規則(批707;L65 Token 撙節律)

**第一步(操作員 2026-09-29 令 · 政策 TOKEN-1):先過 VCGC 的省 Token 步,照它給的卡讀檔。**

```bash
V=$(ls "VeritasIntelligenceAnalytics/supportive modules/registry/"CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | tail -1)
VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt   # 別接 | head:截斷的 BrokenPipe 會被記成 VCGC 失敗
```

- 卡上是**經 VCGC 啟用**(鎖冊 `VIA_ToolVersion_Lock_v0100.json` 的 `token` / `nlp`)、**實測過**的工具,指令可原樣貼上:
  `read`(骨架卡)→ `slice`(一個定義)→ `digest`(日誌只留判決行)· `--if-etag`(沒變回 304)· `pack`(整夾索引)· NLP `--brief`(長文摘要)。
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
