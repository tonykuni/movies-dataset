# PLM 2026：最佳解決方案 × 核心流程 × TOP 25 本機免費函式庫

_為「泛用型 SSOT 工具吃 PLM 匯出檔」而寫：不取代 PLM，而是在本機把 PLM 匯出的料件/BOM/變更資料修復、編號、重組、串接進你的 SSOT。_

---

## 一、2026 最佳 PLM 解決方案（依「合身度」而非「功能多寡」選）

2026 年的共識：**最佳不是功能最多的，而是最貼合你的 CAD 生態與規模的**。CAD 廠牌是企業級 PLM 的首要選型因子。

### Tier 1 — 旗艦企業級（50+ 人、複雜 BOM 與變更管理）
| 系統 | 最適 | 強項 |
|------|------|------|
| **Siemens Teamcenter** | 汽車 / 用 NX | BOM、變更管理、ERP 整合、MBSE |
| **PTC Windchill** | 醫療 / 用 Creo | 多 CAD、變更治理最強、品質合規（醫材） |
| **Dassault 3DEXPERIENCE/ENOVIA** | 航太 / 用 CATIA | 設計到製造單一平台、數位孿生 |
| **Aras Innovator** | 法規嚴管、需長期客製 | **開源應用層**、無升級稅、可組態性最高 |
| **CONTACT Elements** | DACH/歐洲工業 | 模組化、平衡型 |

### Tier 2 — 雲端中市場（想幾週內上線，50–200 人）
Arena（PTC，醫材/電子強）、Propel（Salesforce 整合）、Duro、OpenBOM（Excel 風、易上手、CAD 整合強）、Autodesk Fusion Manage、Oracle Agile、SAP PLM（CPG/原生 ERP）。

### 開源 / 免費選項
**Aras Innovator** 是主要的開源應用層 PLM（社群版免費、可自架、規格透明）。其餘 OpenPLM 偏舊、功能受限；OpenBOM 為雲端 freemium。

### 2026 趨勢
雲原生、**AI-native PLM（"cognitive thread"）**、PLM↔ERP 數位主線整合、MBSE 模型化系統工程。

> **對你的工具的意義**：你不必跟這些競爭。你的定位是「本機、跨來源、合規的 SSOT」——把上述任何 PLM 的**匯出檔**吃進來修復重組，並和郵件/MS Project 串成單一真相。客戶用 Teamcenter 或 Aras 都不影響你的引擎。

---

## 二、PLM 六大核心流程（你的工具該「enrich」的對象）

1. **BOM 管理**：EBOM→MBOM、多階展開、where-used 反查、用量/版次。
2. **變更管理（ECR→ECN→ECO）**：變更請求→通知→命令，含影響分析與簽核鏈。
3. **生命週期狀態機**：料件版次（In Work→In Review→Released→Obsolete）；NPI 階段門（Concept→EVT→DVT→PVT→MP）。
4. **組態/有效性管理**：版次控制、變體/選配、生效日（effectivity）。
5. **合規與品質**：RoHS/REACH、FDA/ISO、CAPA、文件控管。
6. **數位主線 / ERP 整合**：需求追溯、PLM↔ERP 對帳、MBSE。

**你的 SSOT 能加值的點**：用 append-only 事件帳把「變更歷程」留痕；用 BOM 樹把零散料件重組；用狀態機把里程碑對齊；用 diff 比對「信中承諾交期 vs ERP 實際單據」。

---

## 三、TOP 25 本機免費函式庫（enrich PLM 功能，全部離線可跑）

### A. PLM 匯出解析（CSV/Excel/XML）
1. **pandas** — 表格主力，讀 BOM/料件清單匯出。
2. **openpyxl** — Excel BOM 多表、合併儲存格、計算值。
3. **lxml** — 解析 PLM 的 XML 匯出（Teamcenter PLM XML、Windchill 匯出）。

### B. CAD / 工程檔中繼資料（料號、版次、PMI、料件屬性）
4. **ezdxf 1.4.4** — DXF 標準工具，讀 header 變數 + 圖元 + 圖框文字（MIT，含 C 擴充）。
5. **pythonocc-core (OCCT)** — STEP/IGES 完整存取，含產品資料與 **PMI 標註**；CAD 中繼資料抽取的業界標準（LGPL，建議 conda 裝）。
6. **steputils** — 純 Python 讀 STEP 文字結構（輕量，無需 OCCT）。
7. **IfcOpenShell** — IFC/BIM（營建/廠房資產）讀寫。
8. **trimesh** — 3D 模型中繼資料（面數、材質、單位），可走目錄批次。
9. **cadquery / build123d** — 參數化 3D，必要時程式化重建幾何。
10. **gerbonara** — Gerber/PCB（電子業）解析，抽板層與料件。

### C. BOM 樹與相依分析
11. **networkx** — BOM 多階樹、where-used 反查、迴圈偵測、關鍵路徑。
12. **anytree** — 輕量樹結構，BOM 階層展開與列印。

### D. 變更/版次/狀態機
13. **transitions** — 生命週期狀態機（EVT→DVT→PVT→MP；ECR→ECN→ECO），含守衛條件。
14. **deepdiff** — 版次/BOM 差異比對（新增/刪除/變更料件、用量改變）。
15. **jsonschema** — 校驗匯出結構符合預期合約。

### E. 資料合約 / 編號 / 對齊
16. **Pydantic v2** — 欄位防呆，料號格式不符即攔截（Rust 核心）。
17. **rapidfuzz** — 料號/品名模糊比對，手打筆誤對齊 canonical ID。
18. **recordlinkage** — 供應商/料件實體歸一化（去重、配對）。
19. **pint** — 工程單位處理（mm/inch、kg/g、公差換算），避免單位災難。

### F. 文字 / 規格書 / NLP
20. **pdfplumber + PyMuPDF** — 規格書/承認書 PDF 文字與表格。
21. **ftfy**（或 charset-normalizer）— 治 PLM/ERP 匯出的 Big5/亂碼。
22. **spaCy** — 從信件/文件抽料號、ECN 編號、期限、單位。

### G. 倉儲 / 增量 / 視覺
23. **DuckDB + Polars + PyArrow** — 進程內 SSOT 倉儲，BOM/變更事件 append-only 增量。
24. **dlt** — 無連接器收容，PLM 匯出自動推導 schema、增量載入。
25. **graphviz + plotly** — BOM 結構圖、變更影響圖、NPI 階段門 Process Mining。

> **誠實標註**：(a) 開源界沒有現成的「BOM 管理」單一套件——BOM 樹是用 networkx/anytree 自己建。(b) pythonocc-core / cadquery / ifcopenshell 較重、依賴 OCCT，建議 conda 或獨立 venv 隔離（與你既有的環境隔離原則一致）；DXF 用 ezdxf 最輕。(c) DWG 原生需先用 ODA File Converter 轉 DXF 再用 ezdxf。

---

## 四、落地建議：把 PLM enrich 接進你的 SSOT（最小改動）

- **新增一個 `plm_cad` adapter**：沿用既有 adapter 介面，回傳統一 Record；CAD 中繼資料（料號/版次/PMI）變成 Record 欄位。
- **BOM 樹用 networkx 重建**：以「父料號→子料號」建有向圖，存進 SSOT，支援 where-used 反查。
- **變更用 append-only 事件帳**：每筆 ECN 是一個事件，配 deepdiff 算出實際改了哪些料件/用量——對齊你「只增不減」治理。
- **狀態機用 transitions**：把里程碑（EVT/DVT/PVT/MP）與料件版次狀態機碼化，自動判定「卡在哪關最久」（接你已做的 panorama 停滯偵測）。
- **重型 CAD 庫隔離**：pythonocc/cadquery 放獨立 venv，主流程用備援鏈呼叫（讀不到就降級為「僅料件清單，無幾何」），不拖垮輕量主鏈。
