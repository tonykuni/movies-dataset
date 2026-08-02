# SAP 模組完整參考（中英雙語 · 交易碼 · 表單代碼 · 內容說明）
# SAP Module Reference (Bilingual · T-Codes · Form Codes · Content)

_標準物件與交易碼，適用 ECC 與 S/4HANA（S/4 差異另註）。T-code = 交易碼，可直接對映到 VIS Workbench 統一 Record。_

---

## MM · 物料管理 · Materials Management
**核心職責 Core Responsibility：** 採購、庫存管理、物料主檔、發票校驗、供應商評估 / Procurement, Inventory Management, Material Master, Invoice Verification, Vendor Evaluation

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 物料主檔 Material Master | MM01/02/03 | MARA + 視圖 | 料號、基本/採購/庫存/會計視圖 |
| 採購申請 Purchase Requisition | ME51N/52N/53N | EBAN | 內部請購：料號、數量、需求日 |
| 採購訂單 Purchase Order (PO) | ME21N/22N/23N | EKKO/EKPO | 對外採購：供應商、價格、交期 |
| 收貨 Goods Receipt (GR) | MIGO | MSEG/MKPF（S/4: MATDOC） | 移動類型 101，入庫憑證 |
| 發票校驗 Invoice Verification | MIRO | RBKP/RSEG | 三方比對 PO↔GR↔發票 |
| 採購資訊記錄 Info Record | ME11/12/13 | EINA/EINE | 料號×供應商 價格條件 |
| 供應商主檔 Vendor Master | XK01（S/4: BP） | LFA1 | 供應商基本/公司/採購資料 |
| 合約/排程協議 Outline Agreement | ME31K/ME31L | EKKO | 長期採購框架 |
| 庫存總覽 Stock Overview | MMBE | — | 各廠/儲位即時庫存 |

## PP · 生產計劃 · Production Planning
**核心職責 Core Responsibility：** 需求管理、物料需求規劃(MRP)、生產訂單、BOM、途程、產能規劃 / Demand Mgmt, MRP, Production Orders, BOM, Routing, Capacity Planning

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 物料清單 Bill of Materials (BOM) | CS01/02/03 | STKO/STPO | 產品結構樹：父件↔子件、用量（PLM 核心） |
| 途程 Routing | CA01/02/03 | PLKO/PLPO | 作業順序、工時、工作中心 |
| 工作中心 Work Center | CR01/02/03 | CRHD | 產能、費率、排程基礎 |
| 生產訂單 Production Order | CO01/02/03 | AUFK/AFKO/AFPO | 生產指令：料號、數量、日期、狀態 |
| 計劃訂單 Planned Order | MD11/12/13 | PLAF | MRP 產出的建議生產 |
| 物料需求規劃 MRP Run | MD01/02/03 | — | 淨需求運算 |
| 製程訂單 Process Order (PP-PI) | COR1/02/03 | — | 流程業（化工/食品）專用 |
| 主配方 Master Recipe (PP-PI) | C201/202/203 | — | 流程業配方＋作業 |

## SD · 銷售與配銷 · Sales & Distribution
**核心職責 Core Responsibility：** 詢報價、銷售訂單、交貨、開票、定價、信用管理 / Inquiry-Quotation, Sales Orders, Delivery, Billing, Pricing, Credit Mgmt

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 詢價 Inquiry | VA11/12/13 | VBAK/VBAP | 客戶詢問 |
| 報價 Quotation | VA21/22/23 | VBAK/VBAP | 對客戶報價（有效期、價格） |
| 銷售訂單 Sales Order | VA01/02/03 | VBAK/VBAP | 客戶、料號、數量、交期、價格 |
| 交貨單 Outbound Delivery | VL01N/02N/03N | LIKP/LIPS | 揀貨、發貨 |
| 帳單/發票 Billing | VF01/02/03 | VBRK/VBRP | 開立發票、過帳到 FI |
| 定價條件 Pricing Condition | VK11/12/13 | KONV（S/4: PRCD_ELEMENTS） | 價格/折扣/稅 |
| 客戶主檔 Customer Master | XD01（S/4: BP） | KNA1 | 客戶基本/銷售資料 |

## QM · 品質管理 · Quality Management
**核心職責 Core Responsibility：** 進料/製程/出貨檢驗、品質通知、檢驗計劃、品質證書、供應商品質 / Incoming/In-process/Outgoing Inspection, Quality Notifications, Inspection Plans, Certificates

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 檢驗批 Inspection Lot | QA01/QA32 | QALS | 待檢批次：料號、批號、檢驗類型 |
| 品質通知 Quality Notification | QM01/02/03 | QMEL | 客訴/不良/8D，缺陷與對策 |
| 檢驗計劃 Inspection Plan | QP01/02/03 | PLKO/PLMK | 檢驗特性、規格上下限 |
| 結果記錄 Results Recording | QE01 | QASR | 量測值輸入 |
| 使用決策 Usage Decision | QA11 | QAVE | 允收/拒收判定 |
| 品質證書 Certificate (CoA) | — | — | 出貨品質證明 |

## PM/EAM · 廠房維護 · Plant Maintenance
**核心職責 Core Responsibility：** 設備管理、預防保養、維修通知/訂單、故障分析 / Equipment Mgmt, Preventive Maintenance, Notifications/Orders, Breakdown Analysis

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 設備主檔 Equipment Master | IE01/02/03 | EQUI | 設備序號、位置、保養歷程 |
| 功能位置 Functional Location | IL01/02/03 | IFLOT | 廠房結構層級 |
| 維修通知 Maintenance Notification | IW21/22/23 | QMEL | 故障報修、異常 |
| 維修訂單 Maintenance Order | IW31/32/33 | AUFK | 維修工單、工時、備料 |

## PS · 專案系統 · Project System
**核心職責 Core Responsibility：** WBS 結構、網路活動、里程碑、專案成本與進度（≈ MS Project）/ WBS, Network Activities, Milestones, Project Cost & Schedule

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 專案建構器 Project Builder | CJ20N | PROJ | 專案總覽整合入口 |
| WBS 元素 WBS Element | CJ01/02/03 | PRPS | 工作分解結構（對應 MS Project WBS） |
| 網路活動 Network Activity | CN21/22/23 | AFVC/AFKO | 活動、相依、工期 |
| 里程碑 Milestone | — | MLST | 關鍵節點 |

## FI · 財務會計 · Financial Accounting
**核心職責 Core Responsibility：** 總帳、應收(AR)、應付(AP)、資產會計、財報 / General Ledger, AR, AP, Asset Accounting, Financial Statements

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 會計憑證 GL Document | FB01/FB50 | BKPF/BSEG（S/4: ACDOCA） | 借貸分錄 |
| 應付發票 AP Invoice | FB60 | BKPF/BSEG | 供應商應付 |
| 應收發票 AR Invoice | FB70 | BKPF/BSEG | 客戶應收 |
| 資產主檔 Asset Master | AS01/02/03 | ANLA | 固定資產、折舊 |
| 供應商/客戶明細 Line Items | FBL1N/FBL5N | — | 未清項查詢 |

## CO · 管理會計 · Controlling
**核心職責 Core Responsibility：** 成本中心、內部訂單、產品成本、獲利分析(CO-PA) / Cost Centers, Internal Orders, Product Costing, Profitability Analysis

| 表單 Form (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 成本中心 Cost Center | KS01/02/03 | CSKS | 費用歸屬單位 |
| 內部訂單 Internal Order | KO01/02/03 | AUFK | 專案/活動成本歸集 |
| 產品成本 Product Costing | CK11N/CK40N | KEKO | 標準成本計算 |
| 獲利分析 CO-PA | KE30 | CE1xxxx | 依產品/客戶/區域看獲利 |

## PLM · 產品生命週期功能（橫跨 MM/PP/QM）· Product Lifecycle Mgmt
**核心職責 Core Responsibility：** 物料/BOM/途程主資料、工程變更、文件管理、變式配置、分類 / Master Data, Engineering Change, Document Mgmt, Variant Config, Classification

| PLM 功能 Function (中/EN) | 交易碼 T-Code | 物件/表格 Object | 內容說明 Content |
|------|------|------|------|
| 變更主檔 Change Master (ECM) | CC01/02/03 | AENR | 工程變更號、生效日、變更範圍 |
| 工程變更申請/單 ECR / ECN | (S/4 Change Record) | — | 變更的申請與核准——「為什麼改」 |
| 文件資訊記錄 Document (DMS) | CV01N/02N/03N | DRAW | CAD 圖、規格書，掛到物料/BOM |
| 物料 BOM Material BOM | CS01/02/03 | STKO/STPO | 產品結構（與 PP 共用） |
| 途程 Routing | CA01/02/03 | PLKO/PLPO | 製程定義（與 PP 共用） |
| 特性 Characteristic | CT04 | CABN | 分類用特性（如電壓、材質） |
| 類別 Class | CL01/02 | KLAH | 物料分類群組 |
| 變式配置 Variant Config (VC) | CU01/CU41 | — | 可配置產品的規則與相依 |

---

## 四系統互補 · How They Complement
```
SAP        = 定案結果數字 Final numbers（PO/SO、料號、BOM、變更單號）
MS Project = 預定時程骨架 Planned schedule（WBS、Baseline）← 對應 SAP PS
PLM/ECM    = 產品結構與變更 Structure & changes（BOM 改版、ECR/ECN）
Email      = 真實決策脈絡 Real decision context（為什麼改、誰承諾）
```
**關鍵 Key insight：** SAP ECM 只記「BOM v1→v2」，但「為什麼改」常只在郵件裡。VIS Workbench 用交易碼/單號當錨點把四者串起來。

## 對映到 VIS Workbench · Mapping
**已內建 Built-in：** `sap_mm`(EKKO)、`sap_pp`(AFKO)、`sap_sd`(VBAK)、`ms_project`(UID)、`outlook`、`gmail`。
**最高價值可加 To add：** `plm_ecm`(AENR)、`sap_qm`(QMEL)、`sap_ps`(PRPS)。

## 誠實提醒 · Caveats
1. 標準物件；各公司常有 Z/ZZ 自訂欄位與不同 client，對照可 config 一行覆寫。
2. ECC vs S/4HANA：MSEG→MATDOC、BSEG+ACDOCA、KONV→PRCD_ELEMENTS、供應商/客戶→BP，以實際匯出欄位為準。
3. 交易碼各版本可能微調；以客戶系統實際 T-code 為準。
