# VIA 大架構進度總表 v0100(2026-08-09)

操作員令:「先暫時回到 VIA 5 = VDF VRN VAP 整個大架構進度」。
本文為六大子系統(五大 + WorkOps)全盤盤點正本 — 依庫內實證(兩路全庫探查 +
登錄簿 + 提交史),誠實標注「在庫」與「僅工作站」。只增不減;更新以新版追加。

## 〇、治理資產即況

- 登錄簿:**29 引擎(ENG-001~029)· 8 打包產品 · 5 專案子系統 · 48 筆 ledger**(append-only)
- 審計記錄:**1,279 筆**(supportive modules/audit_tools/)· git 提交 **283 筆**(main=工作分支同步)
- 六槽標準佈局(engine/input/db/template/temp/output)已定於 README_SUBSYSTEM_LAYOUT.md;
  System Manager v0162B 依表發現子系統

## 一、六系統進度總表

| 系統 | 定位 | 完成度評語 | 關鍵事實 |
|---|---|---|---|
| **WorkOps** | 郵件×專案智慧治理(本波主線) | **生產運轉中** — 最活躍 | ENG-015/017-023/026-029 共 13 引擎;指揮板 v0117(⓪流程圖/半自動建構/三段追蹤/回覆判讀/報告產生器);ALL v0104 一支到底;八層路由;實機多輪全綠(AUTO 129/87 案) |
| **VRN** | 研報 OCR/PDF 萃取+治理(Report Nova) | **深且大;庫內=規則+SSOT+管線,執行端在工作站** | MDL001-008 全管線在庫;70_VRN_Rules 25 規則模組(FinancialSSOT v0608/BrokerAdapters v06146);SSOT v1+v2 schema/records 在庫;治理天花板 v0615703;**v0156 intake 槽與 300 筆驗證模組正本在工作站,庫內僅指標** |
| **VDF** | 台股市場資料鍛造(Data Forge) | **半鏡像+一條全綠新線** | 文件載 19 模組,庫內約半(MDL001/003/004/005/006/301/302 實碼共 ~7,000 行);**缺 MDL002 YFinance/MDL007 SSOTResolver/MDL101 OutputManager(僅工作站)**;movies intake v001=唯一全綠實證(sqlite+QA 證據);VIA_Pipeline(2026-08-08)=最新最乾淨:回測→自我演化→魔鬼代言人 7 攻擊,誠實 NOT VALIDATED |
| **VAP** | 視覺功能管理(AutoPlot:icons/templates/繪圖) | **資產量最大;引擎實跑出圖;編排層薄** | autoplot 引擎 v001/v002(零依賴 HTML+SVG 雙軸,visual lock 遵守)實跑 13 張圖;Workbench v009/v010+Command Center UI;registry 34 檔資產庫(icon/asset/grouping,10MB 級真庫存);vap_orchestrator.js 僅 105 行骨架 |
| **VMT** | 郵件追蹤自動化(Mail Tracker) | **碼齊、資料未布建、未升格** | via_master_engine v0103+八階段模組(收斂/回信吸收/CPM/探勘/SuperBOM);審計明載 code_gaps: ZERO;**但 VMT_ROOT 資料層(ssot.json/superbom.duckdb)未種**→板④頁顯示未布建;家在 supportive modules,無 functional modules 主目錄與 manifest |
| **VTR** | 中英會議紀錄修復(DG-IN) | **工程最乾淨、功能最早期** | 確定性層完成(語言偵測/正規化/名詞保護/信心閘門 0.85/0.60/補丁重放);501 行測試=全系統唯一像樣測試檔;詞庫 SSOT 治理同 VRN 政策;**8 步修復只完成 2 步+保護,模型層與 JS 引擎未實作** |

## 二、系統間接縫(已通的線)

- WorkOps ↔ VMT:板④頁唯讀附掛 VMT_ROOT;收斂引擎(AUTO/ASK/QUARANTINE)概念共用
- WorkOps ↔ VRN:via-ocr 統一路由(ENG-026)蓋四套 OCR 存量;VisualLock v0159 入庫為視覺正本
- VDF ↔ VIA_Pipeline:rotation_engine(ENG-024)AST 抽取 candidate 分類法不複製(去重原則)
- VDF ↔ VAP:movies intake 產 sqlite → autoplot 自動發現出圖(intake→autoplot 端到端已證)
- VDF ↔ VRN:PointerSeal/SourceFallback 縫合 manifest 在 registry
- 啟動器:bin/ 30 支;**VAP/VTR 無 bin 啟動器**(各走自家入口/One-Click)

## 三、誠實缺口與風險(候令排序)

1. **VMT 資料布建**:`via-vmt-init` 工作站實跑種資料層 → 板④頁即活;順手升格 functional modules/VMT + manifest(佈局一致性)
2. **VDF 三缺件回庫**:MDL002/007/101 只在工作站 — registry 有 sha 可驗,回庫即補全鏡像
3. **VRN v0156 intake 槽**:標準槽已定 VRN/input/incoming/,工作站 Downloads 舊位僅 fallback — 實料落庫或確認改道
4. **登錄簿殘影**:多處 registry 指 `C:\Users\tonyk\...` 且有 exists:false / ENGINE_MISSING 列 — registry 描述的是超集,對帳候令
5. **VTR 模型層**:後六步+JS 引擎未實作(規格已齊,候令開工)
6. **VAP 編排層**:orchestrator.js 骨架化,資產庫大而無專屬碼模組
7. via-pipe 尚未接真行情(via_fetch_prices 在 PMIS-Lite,未接線);策略閘門誠實 NOT VALIDATED=待真資料重跑

## 四、近期主線紀要(2026-08-08~09)

WorkOps 衝刺:ENG-028 WOP 識別(八層路由/學習迴圈/87 案實戰)→ ENG-029 回覆解析(M3 三層)
→ 板 v0113~v0117(流程圖/半自動建構/三段追蹤/判讀欄/報告產生器)→ SSOT 詞彙去重
(workops_lexicon + org_lexicon 149 家)→ M365 規劃書與準確度報告全文裁定落地。

紅線全程未動:唯讀 · 絕不代寄/代跑 · 原件零觸碰 · 編號永不變 · 基底零觸碰 · 只增不減 · 參數=JSON。

## 補遺二(2026-08-10 操作員「完成 vdf vrn vap」令)

- **VDF**:取數契約 SSOT 歸位 — `VDF/registry/VIA_VDF_Fetch_Contract.json`(VDF-FETCH/1.0,
  14 域 277 項:ok 217 / proxy 45 / todo 15;10 個 fetcher 模組;Adj 優先/前值補價/低頻對齊/
  權威層級規則入冊)。todo 15 項=下一步取數開發清單(如 US-L22 半導體 B/B)。
- **VAP**:操作員貼附 40+ 路徑經倉內比對 — chartlib/spec SSOT、Workbench v005/v009/v010、
  UNIT03 系列(倉內 v0111R2/v0112/v0113 較貼附之 v0111 新)、duckdb parquet 加速器、
  v8 master、panorama maturity 全在位;**真缺 3 件待上傳**:GuardedDynamicSandbox-v0109.ps1、
  VIA_VAP_Chart_Library_Builder.html、VIA_VAP_System.html(UI 版)。
- **VRN**:VisualLock v0159 為 UI 風格正本(板 v0119+ 已採);VRN 本體(Guarded Entry v217、
  Batch AllInOne、staging 修復系)原狀在位,無本輪改動需求。

## 補遺三(2026-08-10 操作員「更新所有子系統 注意位階」令)— 全系統位階與現況定格

```
位階 1  VIA 母系統(bin 啟動器 · registry 編號正本 89 筆 · VIA_SSOT · VisualLock UI 正本)
  ├─ 位階 2  Veritas WorkOps(SUB-006)── 產品主線,PRODUCTIZED_FULL_LOOP
  │    ├─ 引擎 ENG-015/017-048(歸戶八層 AUTO 129/ASK 0 · 回覆三層 · 自測 7 段 ·
  │    │   TO-DO 七批 · 簡報 · 稽核包 · 矩陣 · 搜尋/里程碑/時間軸/結案/教訓/保留/首跑)
  │    ├─ 板 v0123 十面(今日作戰面/確認中心/準確度)· ALL v0105 十三段 · 日節奏 16/11/16
  │    ├─ 模組 VMT(位階 2.5;資料層待 init;quarantine:BatchMailer 紅線隔離)
  │    ├─ 模組 VTR(位階 2.5;逐字稿確定性修復正本;49 測試)
  │    └─ 模組 MeetingLoop(位階 2.5;會議循環 v005;實機 9/9;ENG-048 橋入對帳)
  ├─ 位階 2  VDF(SPJ-VDF)── 結案基線 PASS;取數契約 277 項;MDL501 增減管理
  ├─ 位階 2  VRN(SPJ-VRN)── 結案基線 PASS;VisualLock v0159=全系統 UI 風格正本
  └─ 位階 2  VAP(SPJ-VAP)── 結案基線 PASS;9 artifacts;chartlib v002 升級鏈完整
位階 3  引擎(編號永不變;晉升必納 selftest)   位階 4  側車(append-only)
```

- 位階鐵則:模組不越級(MeetingLoop→ENG-048 橋→WorkOps 帳);編號主權=位階 1 registry;
  共用資產經 Shared_Lexicon_Registry 登記;結案=基線封存非停用,重跑 via-closure 落新基線。
- 待操作員:控管表(嚴格提示詞)· Gold Set 首測 · VMT via-vmt-init;候令:VTR 模型層/JS、
  RC 產品線 payload、Graph(IT 核准後)。

## 補遺三(2026-08-12 操作員「先暫停,檢查 VIA母版及 VRN/VDF/VAP 是否完成並整合完,準備對接U/I」令)

四系統對接前總檢 — 本輪 Linux 實測 + 兩路全庫深掃。誠實判定:**母版就緒、VAP 引擎層就緒、
VRN 核心完好但接縫有斷鏈、VDF 缺件最多未達整合完**。

### 總表

| 系統 | 本輪實測 | 完成度判定 | 對接U/I就緒 |
|---|---|---|---|
| **VIA母版 v0132** | BoardQA 四層全綠(unit+integration 14/14 · system 真瀏覽器 9/9 · 封印 4cb90a0b 驗真);spec master 6 段重建 OK | **完成** | **就緒** — 但板上尚無四子系統磁貼/連結(對接主幹缺) |
| **VAP v007** | demo→auto 三圖→index OK;--sql DuckDB 虛表 OK;--panels 三面板 OK;seaborn/plotly 引擎可載;SSOT 1.1.4 | **引擎層完成** | **有條件** — Workbench v009/v010 用 cdn.plot.ly+Google Fonts 違在地化鐵律(離線圖斷);編排層 orchestrator.js 105 行骨架;3 件 UI 候上傳 |
| **VRN** | MDL001-008 全 py_compile 過 · manifest 9/9 hash lock · HealthCheck Linux 可跑(曾 89 PASS/0 FAIL READY)· 53 凍結鎖=全庫最嚴 | **核心完成(執行端在工作站)** | **有條件** — 斷鏈與蔓生見下 |
| **VDF** | MDL501 契約 check PASS(14 域 277 項:ok 217/proxy 45/todo 15)· movies intake DryRun GREEN · MDL301/302 可跑但內部 ❌(見下) | **半成 — 骨架治理好,本體缺件多** | **未就緒** |

### 各系統誠實缺口(本輪查實,file:line 級)

**VRN**(核心穩,接縫傷):
1. `Invoke-VIA-ALL.ps1:203/439` 指向 `VRN/VRN_GO.ps1` — 檔案全庫不存在,ALL 該站必 FAIL(斷鏈)。
2. README 載 27 檔,實樹缺 3 支:`VRN_SmokeTest.py`/`VRN_Pipeline_Runner.py`/`panorama_xcheck_v110.py`(帳實不符)。
3. 母版 45 支板腳本零 VRN 磁貼;VAP 僅收其 v0159 設計源(樣式線,無資料線)。
4. `VRN_Finalize_Core_v2_1.py:479` FactSet 橋= STUB(交叉驗證一臂未實作)。
5. 入口蔓生 ≥12 支 AIO 並存(v139G 硬編碼死路徑;Finalize_AIO_v2 檔頭仍寫 v1)— canon 未標。
6. 規則層 5 支草稿無凍結鎖(TickerRegex SSOT 過渡中);runtime 槽(input/output/db)全空=本 checkout 未實跑。

**VDF**(缺件最多):
1. **v0160 三本體全缺確證** — manifest 在籍(14cf1344/fb01cd25/57e03031)但全庫無任一檔命中此 sha;僅後續變體 v0160A/B/C 在位。登錄簿 :1363 已誠實在案=候上傳(工作站正本)。
2. README 21 模組缺 11:MDL002/007/**101(OutputManager — 眾寫入端所依)**/103/104/105/201/303/501控制台HTML 等。
3. **MDL301/302 假綠**:exit 0 但內部 Imports 0/7、兩項自測 ❌(肇因 MDL101 缺)— 任何以退出碼把關的 CI 皆抓不到。
4. 全 VDF 樹零 `.freeze.lock.json`(VRN 有 53)— 無凍結正本記號;亦無 VisualLock 封印(VRN/WorkOps 皆有)。
5. 板零磁貼;治理 runtime SSOT 零引用;FlowSystem 個股角色欄明標「**待VDF**」= 接縫懸空。
6. Windows 硬編碼:MDL004:64/MDL102:35 `C:\Users\tonyk\OneDrive...`;Consolidator.ps1 `$Execute=$true` 具真搬移(勿在 Linux 端碰)。

**VAP**:
1. Workbench v009/v010 `cdn.plot.ly/plotly-2.35.0` + Google Fonts — runtime U/I 違在地化鐵律。
2. 3 件候上傳:GuardedDynamicSandbox-v0109.ps1 / VIA_VAP_Chart_Library_Builder.html / VIA_VAP_System.html(UI 版)。
3. 編排層薄(vap_orchestrator.js 骨架)。

**母版**:
1. 板未串四子系統與 FlowSystem hub(板內 flow_hub 引用 0;VAP 僅 Note Pro 一線;VRN/VDF 零)— 「所有介面互通」缺母幹線。
2. 板亦未連 spec master 最後一頁(Spec_Master 引用 0)。

### 對接U/I 準備清單(候令,依優先)

1. **母版對接列**:板新增「子系統」磁貼帶 — flow_hub.html / VAP output index+Workbench / VRN 報告 Grid / VDF v3.5 維運平台 HTML / VIA_Spec_Master_LastPage.html(一板通達全系統)。
2. **VAP 在地化**:Workbench plotly 內嵌化+字體降級(比照 FlowSystem inline 先例)。
3. **VRN 斷鏈修**:ALL 之 VRN_GO 站改指現行入口(Batch-AllInOne-v0100 或 Guarded-Entry v217)或誠實除名;README 對帳;canon 入口標記。
4. **VDF 假綠改誠實**:MDL301/302 內部 ❌ 時 exit 非零;缺件清單(11 模組+v0160 三本體)= 工作站候上傳令。
5. VDF/VRN 板磁貼與 VisualLock 補齊(VDF 無封印)。

紅線不動:候上傳件正本在工作站,AI 只整理不發明 — 不代生 v0160 三本體與 VRN 缺檔。
