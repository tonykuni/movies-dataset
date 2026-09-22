# 給 AI 的讀檔規則(批707;L65 Token 撙節律)

**先讀骨架卡,不讀原始碼。** 本倉的單檔動輒上千行,整檔讀進來很耗 token。大檔(約 >200 行)或整個資料夾一律先走全景代讀:

```bash
E="VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_VIAPanoramaAuditRepair_v0105.py"   # 取尾版:ls …_v*.py | tail -1
python3 "$E" read <檔或夾…>            # 骨架卡:匯入 · 定義樹(行號/簽章/首行說明)· AST 錯誤;給夾=一檔一行全景
python3 "$E" slice <檔> <名|Class.method>   # 只取一個定義的原始碼(帶行號)
```

- 唯讀:不寫檔、不執行被讀的檔(只做 `ast.parse`;`.ps1` 只做文字剖析)。
- 錯誤分兩層:治理七類(ACCEL/NET/VERB/HARDIMP/PINVER/SYSEXE/TALIB,只在 VIA 樹內算)+ 通用 AST 類
  (SYNTAX/DUPDEF/UNREACH/BAREEXC/SWALLOW/MUTDEF;PowerShell:PSDUPFN/PSDOCSTR)。全都只報位置,不自動改。
- 先 `read` 看定義樹 → 用 `slice` 或帶 offset/limit 的讀檔只取要改的那一段。
- 操作員端同一個功能:`via-panorama read <路徑>` / `via-panorama slice <檔> <名>`。

**不要**為了看說明而跑 `CGC_MDL064_SelftestGrid_v*.py --help`:它不吃 `--help`,會把整張格子跑起來並重寫已追蹤的檔(批707 實錄 21 檔)。單站用 `--only <站名子字串>`。
