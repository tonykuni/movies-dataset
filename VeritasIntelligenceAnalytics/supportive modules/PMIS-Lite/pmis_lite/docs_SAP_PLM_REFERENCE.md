# SAP 常用模組 × 細項 × 表單單據 × 對應 PLM 功能

_標準模組結構參考（適用 ECC 與 S/4HANA；S/4 差異另註）。SAP 物件/表格一併列出，方便對映到 VIS Workbench 統一 Record。_

---

## 一、SAP 常用運作模組總覽

| 分類 | 模組 | 全名 | 核心職責 |
|------|------|------|---------|
| 物流 | **MM** | Materials Management | 採購、庫存、物料主檔、發票校驗 |
| 物流 | **PP** | Production Planning | MRP、生產訂單、BOM、途程、產能 |
| 物流 | **SD** | Sales & Distribution | 報價、銷售訂單、交貨、開票、定價 |
| 物流 | **QM** | Quality Management | 檢驗批、品質通知、檢驗計劃、證書 |
| 物流 | **PM/EAM** | Plant Maintenance | 設備、功能位置、維修通知/訂單 |
| 物流 | **WM/EWM** | (Extended) Warehouse Mgmt | 倉儲、儲位、傳輸訂單 |
| 專案 | **PS** | Project System | WBS、網路、里程碑（≈ MS Project） |
| 財務 | **FI** | Financial Accounting | 總帳、應收 AR、應付 AP、資產 |
| 財務 | **CO** | Controlling | 成本中心、內部訂單、產品成本、獲利分析 |
| 人資 | **HCM** | Human Capital Mgmt | 人事、薪資、工時、組織 |

---

## 二、各模組細項 + 主要表單單據（含 SAP 物件）

### MM 物料管理
細項：採購、庫存管理、物料主檔、供應商主檔、發票校驗、採購資訊記錄。

| 單據/表單 | SAP 物件 | 說明 |
|----------|---------|------|
| 採購申請 PR | EBAN | Purchase Requisition |
| 採購訂單 PO | EKKO/EKPO | Purchase Order（抬頭/明細） |
| 收貨 GR | MSEG/MKPF（S/4：MATDOC） | 物料憑證 |
| 發票 IR | RBKP/RSEG | 發票校驗 |
| 資訊記錄 | EINA/EINE | 料號×供應商 價格 |
| 合約/排程協議 | EKKO（類型 K/L） | Outline Agreement |

### PP 生產計劃
細項：需求管理、MRP、生產訂單、BOM、途程、工作中心、產能規劃。PP-PI（流程業）用製程訂單+主配方。

| 單據/表單 | SAP 物件 | 說明 |
|----------|---------|------|
| 計劃訂單 | PLAF | Planned Order |
| 生產訂單 | AUFK/AFKO/AFPO | 抬頭/工單/明細 |
| **物料清單 BOM** | STKO/STPO | Bill of Materials（PLM 核心） |
| **途程 Routing** | PLKO/PLPO | 作業順序/工時 |
| 工作中心 | CRHD | Work Center |
| 製程訂單/主配方 | (PP-PI) | 流程業專用 |

### SD 銷售配銷
細項：詢價、報價、銷售訂單、交貨、開票、定價、信用管理。

| 單據/表單 | SAP 物件 | 說明 |
|----------|---------|------|
| 詢價/報價 | VBAK/VBAP（類型） | Inquiry/Quotation |
| 銷售訂單 | VBAK/VBAP | Sales Order |
| 交貨單 | LIKP/LIPS | Delivery |
| 發票/帳單 | VBRK/VBRP | Billing |
| 定價條件 | KONV（S/4：PRCD_ELEMENTS） | Pricing |

### QM 品質管理
細項：進料/製程/出貨檢驗、品質通知、檢驗計劃、品質證書、供應商品質。

| 單據/表單 | SAP 物件 | 說明 |
|----------|---------|------|
| 檢驗批 | QALS | Inspection Lot |
| 品質通知 | QMEL | Quality Notification（客訴/8D） |
| 檢驗計劃 | PLKO/PLMK | Inspection Plan |
| 品質證書 | — | CoA/CoC |

### PM 廠房維護 / PS 專案系統
- PM：設備主檔（EQUI）、功能位置（IFLOT）、維修通知（QMEL）、維修訂單（AUFK）。
- **PS：WBS 元素（PRPS）、網路活動（AFVC）、里程碑——這是 SAP 內建的專案管理，與 MS Project 雙向對照的關鍵。**

### FI / CO 財務
- FI：會計憑證（BKPF/BSEG；S/4：ACDOCA 通用日記帳）、AR/AP、資產（ANLA）。
- CO：成本中心（CSKS）、內部訂單（AUFK）、產品成本、獲利分析 CO-PA。

---

## 三、對應的 PLM 功能（SAP PLM 橫跨 MM/PP/QM）

SAP PLM 不是單一模組，而是一組跨模組功能。核心對應如下：

| PLM 功能 | SAP 物件/交易 | 對應到哪些運作模組 | 補的是什麼 |
|---------|--------------|------------------|-----------|
| **物料/零件主檔** | MARA + 各視圖（CS/MM/PP/QM view） | MM/PP/SD/QM 共用 | 產品身分基準 |
| **BOM 管理** | STKO/STPO（CS01/02/03） | PP（製造BOM）、SD（銷售BOM） | 產品結構 |
| **途程/主配方** | PLKO/PLPO | PP、PP-PI | 製程定義 |
| **工程變更管理 ECM** | 變更主檔 AENR（CC01/02）、ECR/ECN | 改 BOM/途程/物料/文件 | **「為什麼改」——郵件 SSOT 要補的塊** |
| **文件管理 DMS** | 文件資訊記錄 DIR（CV01N/DRAW） | 圖面/規格 掛到物料/BOM | CAD圖、規格書 |
| **分類系統 CL** | 特性 CABN、類別 KLAH | 物料/批次分類 | 找料、變式 |
| **變式配置 VC/LO-VC** | 配置輪廓、特性 | SD（可配置產品）、PP | 客製化產品 |
| **規格管理** | (EHS/PLM) | QM、法規 | 成分/法規 |
| **產品結構 iPPE** | — | 汽車/高科技 | 複雜結構 |

### 三系統互補的完整圖像（回到你的 SSOT 目標）
```
SAP        = 定案的結果數字（PO/SO 金額、料號、BOM、變更單編號）
MS Project = 預定的時程骨架（WBS、Baseline、里程碑）  ← 對應 SAP PS
PLM/ECM    = 產品結構與變更（BOM 改版、ECR/ECN）
郵件        = 真實的決策脈絡（為什麼改、誰承諾、線下決策）
```
**關鍵**：SAP 的 ECM 記錄「BOM 從 v1 改到 v2」，但**「為什麼改」常只在郵件裡**（「客戶電話要求公差縮小」）。VIS Workbench 把四者對齊到同一 Record，用 append-only 時序總帳，還原「誰在何時、因為什麼，決定了這項變更」——這是 SAP 或 MS Project 單獨做不到的。

---

## 四、對映到 VIS Workbench（哪些已做、哪些可加）

**已內建預設**：`sap_mm`（EBELN）、`sap_pp`（AUFNR）、`sap_sd`（VBELN）、`ms_project`（UID）、`outlook`、`gmail`。

**建議可加的預設**（依你行業優先）：
- `sap_qm`（QMEL 品質通知/客訴）——接客訴 8D 到 SSOT
- `sap_ps`（PRPS/AFVC 專案）——與 MS Project 交叉稽核
- `plm_ecm`（AENR 變更主檔 / ECR / ECN）——**最高價值**，把工程變更接進來
- `plm_bom`（STKO/STPO BOM）——產品結構
- `plm_dms`（DIR 文件）——圖面/規格關聯
- `sap_fi` / `sap_co`（財務/成本）——專案成本總帳

---

## 五、誠實提醒

1. **標準 vs 客製**：上述是 SAP 標準物件；各公司常有 Z/ZZ 自訂欄位與不同 client 設定，故每條對照都可在 config 一行覆寫。
2. **ECC vs S/4HANA**：S/4 簡化了部分表格（物料憑證 MSEG→MATDOC、FI/CO 合併為通用日記帳 ACDOCA、定價 KONV→PRCD_ELEMENTS），對映時以實際匯出欄位為準。
3. **PLM 版本差異**：SAP PLM 在 ECC、S/4HANA、以及與外部 PLM（如 Teamcenter）整合時，物件與交易碼略有不同。
