# VDF 系統架構及介面釐清書 v0100

> 操作員令 2026-08-13:「亂掉了 我們先完成VDF的系統…請先釐清楚VDF的系統架構及介面」。
> 本書=以庫內正本(MDL000 README 正典、Subsystem Manifest、MDL272 存證、Invoke-VDF.ps1)
> 與操作員工作站完整目錄清單(~190 項)對帳所得。AI 只整理不發明;缺席誠實列缺。

---

## 一、系統定位

VDF = **Veritas Data Forge · 資料鍛造子系統**(編號 04 / 設計正典名 VERITAS DATA FORGE / 1c)。
角色:市場資料**取數層**(全系統唯一允許對外抓取之層;不爬站鐵律之豁免區)+
基本面/財務資料的**正典化與建庫**。上游=各官方/公開源;下游=VRN 研報、VAP 繪圖、FlowSystem。

## 二、五層架構(MDL 編號正典,19 件全在庫)

```
L0 啟動/介面層
   Invoke-VDF.ps1(主啟動器:status/開DB/開header registry/看pointer/看SSOT/看manifest;唯讀六動作)
   Start-VIA-VDF-v0101..0103.ps1 · via-vdf 動詞 · UserTest-Start-VDF-Lane2-ReadOnlyInventory.ps1
   VDF_MDL501_DataModuleController.html(31 模組控制台 UI)· VDF_MDL501_FetchContractManager.py
   VIA_Sub_vdf.html(母頁子模板)
        │
L1 擷取引擎層(MDL001-007,核心 7+1)
   001 TWEquityEngine(2263L)· 001-VRF TWUniverseVerify(585L)
   002 YFinanceFetchingEngine(175 tickers/19 群組,1802L)
   003 SentimentMacroEngine(FRED47+AKShare13+AAII/CNN,1466L)
   004 TWFullMarketEngine(1071L)· 005 TWStockFilter(1003L)
   006 FinancialModel(5y+三大報表+PE/PB Band,1385L)· 007 SSOTResolver(四源解析,1221L)
        │ imports
L2 共用函式庫層(MDL101-105)
   101 OutputManager(所有寫檔依賴之核)· 102 FormatUpgrader(無改碼升級 001/002)
   103 MasterRegistry(741L)· 104 RegistryLoader · 105 CrossValidator(13 交叉檢啟用)
        │
L3 工具/測試層(MDL201·301-303)
   201 GenerateFullRegistry(產 238 items)
   301 SystemTest · 302 FinalActivation(9 phases,ALL PERFECT 已實證)· 303 RegistryActivation(四階段)
        │
L4 Registry 資料層(MDL401-404 + registry/)
   401 Schema(Draft-07)· 402 Sample(18)· 403 Full(238,可再生,gitignore)· 404 CoverageReport
   registry/VIA_VDF_Fetch_Contract.json(VDF-FETCH/1.0,code VIA-M-VDFONE,277 項 PASS)
   registry/VIA_Extraction_Matrix(md/csv/v14 SSOT html)
        │
L5 資料面(輸入/輸出/庫)
   倉:input/ output/ db/ temp/(庫內)⟷ INPUT/ OUTPUT/ ASSETS/ db/ _vdf_inputs/ _vdf_outputs/(工作站)
   生產庫:module\VeritasDataForge\data\via.duckdb(22 表;MDL272 存證:
     vrn_basicinfo_consensus 1,861×129 · vrn_financial_actual_canonical 27×20)
   輸出格式:Parquet(必)+DuckDB+CSV(utf-8-sig)+JSON+GSheet(stub)
```

**附掛家族(financialdata 鏈,VDF 根鏡像歸戶,12 件在庫)**
`extraction_store(建庫器 v029vrn1d)→ MDL097 選源 → MDL215 triflow staging(產 158 報告)
→ MDL218 confirm_verify(產 160 報告)→ MDL252≡253 final_seal → MDL187 quality layer(誠實紅存證)
→ MDL272 Sidecar Sync(指針+安全閘全鎖)`;政策全鏈 no_fake_fill / NO_CANONICAL_MUTATION。

**治理發佈鏈(工作站在地,庫未收)**
`_integration_firststep_panorama … v0114T` 共 34 站 + Invoke-VIA-Integration/v0113/v0114 啟動器約 60 支
(NoStall/NoClose 樣式,Secret 三段處置、sandbox 修補、release 封裝、最終人工授權閘)。
定位=VDF 之**發佈治理走廊**,與引擎運行面正交。

## 三、介面清單(對外可操作面)

| 介面 | 型 | 動作 |
|---|---|---|
| `Invoke-VDF.ps1` | PS7 CLI | status/open-database/open-header-registry/show-active-pointer/show-ssot/show-output-manifest(全唯讀) |
| `via-vdf` | cmd 動詞 | contract check 取數契約盤點 |
| `py VDF_MDL302_FinalActivation.py --no-pause` | CLI | 一鍵全系統 9 phases 驗證 |
| 生產序 | CLI | 001→001-VRF→002→003→005→006→007(README 依賴順序) |
| `VDF_MDL501_DataModuleController.html` | UI | 31 模組總覽/增刪查/PowerShell 指令產生/JSON 配置下載 |
| `VDF_MDL501_FetchContractManager.py` | 工具 | 取數契約管理 |
| 母頁 04 頁籤 → `VIA_Sub_vdf.html` | UI | 動詞複製/拖曳 precheck/深層 UI 連結 |
| `config.template.json`(工作站) | 配置 | 消費者參數模板【候上傳】 |

## 四、對帳:工作站清單 vs 庫內(完成 VDF 的差距)

### ✅ 已在庫(核心完整)
19 編號件全套 + MDL004 + Manifest + Invoke-VDF.ps1 + EngineCapability csv/json 對 +
financialdata 家族 12 件 + engine/ registry/ qa/ template/ 子目錄 + 契約鏈全綠存證。

### 🅰 A 級缺件(系統完成必需,候上傳)
1. **VRN_MDL011**_VRN_BasicFinancial_Confidence_Method_Review JSON(010/012 之間缺號!)
2. **config.template.json**(L0 消費者配置模板)
3. **README.md**(VDF 根另一份,與 MDL000 並存者)
4. **StockReportFinancialData.csv / .json**(根層資料對)
5. **Start-VDF-Lane2-ReadOnlyInventory.ps1**(庫內僅 UserTest- 版)
6. **VDF_KeyCommodityIndex/** 目錄內容
7. **ui/** 目錄內容(工作站 VDF\ui\ — 庫內 VDF 無 ui/)
8. Invoke-VDF-**Fetch**.ps1 / Invoke-VDF-**Nexus**-Panorama3RoundGate.ps1(庫內 network/ 有副本 — 待與工作站版雜湊對版)

### 🅱 B 級(治理鏈存證,量大,依令再收)
34 個 `_integration_*` 站目錄 + ~60 支 Invoke-VIA-Integration/v0113x/v0114x.ps1 + `_vdf_*` 15 目錄
+ _nostall_turbo_launcher。建議:先收啟動器 ps1 家族(文字小),站目錄產物按需。

### 🅲 C 級(副本/再生/暫存,原則不收)
sha 後綴存證副本 9 件(內容疑=行尾變體;EngineCapability 兩件已驗證同一)· __pycache__ ·
\*.bak ×3 · parse_\*.txt(audit_tools 已存證)· MDL403(可再生,gitignore 政策)。

## 五、建議完成序(候示下)

1. 上傳 A 級 1-7(8 項小件)→ 即歸戶補洞。
2. A 級 8:雜湊對版 network/ 兩支 Fetch/Nexus;同=記帳,異=工作站版讓位歸 VDF 根。
3. B 級啟動器家族一波收齊(治理走廊入庫存證)。
4. 介面接線驗證:MDL501 UI 指令 ↔ via-vdf ↔ Invoke-VDF 三徑一致性實測。
5. 收斂:VDF 完成宣告 = 19 編號件 + A 級全補 + 介面三徑實測綠 + MDL302 ALL PERFECT(已有)。

— append-only · 誠實口徑 · 2026-08-13
