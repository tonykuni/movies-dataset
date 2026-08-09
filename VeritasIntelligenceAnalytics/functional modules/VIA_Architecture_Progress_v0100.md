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
