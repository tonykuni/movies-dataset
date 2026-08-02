# VIA · PSU + Thermal · 主索引 MD（B）

> 把前面對話累積的所有 PSU/Thermal 產物串成一張可導航索引:每個產物寫清楚**它是什麼、關鍵匯出、用什麼鍵和別人 join**。
> **誠實邊界**:下列多數引擎/HTML 建於先前 sandbox 或你本機樹;本檔是**目錄索引**,不是把它們重新產一遍。標「（本機/前輪）」者請以你磁碟實檔為準。
> 治理:只增不減 · 外部代碼原封 · VIA 內碼只在旁對齊 · 證據 T1–T4。

---

## 0. 串接骨幹（所有產物共用的 join 鍵）

| join 鍵 | 說明 | 由誰產 |
|---|---|---|
| **公司名** | 中英雙名（如「奇鋐 AVC」） | `sector_registry` / `super_bom` |
| **VIA 內碼** | VIA-DOM/PRD/SUB/KNW/IFC/TPL + 本輪 VIA-SUP/PEER/CUS/EDGE/FIN | `via_codegen.py` / 本輪 `validate.py` |
| **外部代碼** | ticker / yfinance / SAP LIFNR·KUNNR·MATNR / MSP UID | 原平台,VIA 不改 |
| **SAP MType** | FERT / HALB / ROH | `super_bom` / `sap_modules_ref` |

> 一家公司 = 一列 VIA 內碼 + `external_codes[]` 陣列掛所有外碼。奇鋐 vs 雙鴻等競品:公開骨架共用,機密 BOM `sovereignty=confidential` 不共池。

---

## 1. 資料層（Intake / SSOT / 中間層）

| 產物 | 是什麼 | 關鍵匯出 | join 鍵 |
|---|---|---|---|
| `via_pt/schema/*`（本輪 A） | T01–T07 中間層 schema + 驗證器 | 空 CSV + jsonschema + `validate.py`(自動編號/append-only/T-1) | VIA 內碼 |
| `ocr_intake.py`（前輪） | 無 OCR fallback 進料;NFKC + Ticker Regex v2(2021–2030 消歧) | 正規化 token | ticker |
| SSOT canonical align（前輪） | 外部詞 100% 尊重,VIA 只對齊 | 對齊表 | 公司/外碼 |

## 2. BOM 層

| 產物 | 是什麼 | 關鍵匯出 | join 鍵 |
|---|---|---|---|
| `bom_template.py`（前輪） | 通用電子 BOM:欄位字典/必填/品類分類/建樹/where-used/成本 rollup/diff | `template_header()`, `validate_bom()`, `cost_rollup()` | 料號/MType |
| `super_bom_engine.py`（前輪） | 在通用 BOM 上加 **Company / BU / Product_Family 三維** + 散熱品類擴充 | `COMPANY_PROFILES`, `classify_commodity_super()`, `validate_super_bom()` | 公司/BU/品類 |
| `COMPANY_PROFILES` | 台達/康舒（電源）· 雙鴻/奇鋐/健策/三集瑞（散熱）各 BU 產品家族（公開） | 三維骨架 | 公司/BU |

## 3. 產業/公司登錄層

| 產物 | 是什麼 | 關鍵匯出 | join 鍵 |
|---|---|---|---|
| `sector_registry.py`（前輪） | 53 家全球電源/散熱:32 台廠(4 散熱子類)+6 電源+10 國際+11 私有/被併 | `align_codes()`（多平台代碼對齊）· 登錄完整度檢查 | 公司/ticker |
| `sap_modules_ref.py`（前輪） | SAP 模組全編(MM/PP/SD/SCM/CO/BOM/PLM)+ 固定 T-code + 關鍵欄位 | T-code/欄位對照(MATNR/LIFNR/WERKS/AUFNR/KUNNR/KOSTL) | SAP 代碼 |

## 4. 中央參數/代碼生成層

| 產物 | 是什麼 | 關鍵匯出 | join 鍵 |
|---|---|---|---|
| `central/via_params.json`（前輪） | 全模板/UI token/介面契約/SAP 供應商-客戶模板/產業分類/頁面項目 單一真值 | 參數 SSOT | — |
| `central/via_codegen.py`（前輪） | 確定性 VIA 碼生成(VIA-DOM/PRD/SUB/KNW/IFC/TPL) | `gen(domain,...)` | VIA 內碼 |
| `central/via_system_manager.py`（前輪） | append-only 強制 + 核可 gate + sync plan 編排 | 核可/同步 | — |
| `VIA_Central_Activate_Sync.ps1`（前輪） | PS7 啟動器,dry-run 預設,`-Approve` 才寫 | — | — |

## 5. 整合引擎 / 既有 UI

| 產物 | 是什麼 | 備註 |
|---|---|---|
| `via_engines.py`（前輪） | 50+ 模組整併成 7 引擎:Intake/SSOT/Sync/BOM/Finance/Knowledge/Governance,單一 `VIA()` 入口 | 端到端測過 |
| `msproject_io.py`（前輪） | MS Project 2003 XML 雙向 write-back,核可 gate,round-trip 零遺失 | 對齊 MSP |
| `VIA_PowerThermal_Unified.html`（前輪） | 12 個舊 HTML 整併成 8 分頁(registry/分類/ASP/成本GM/財務模型/產業公司/SAP-BOM 對齊) | 本輪內容規格的視覺前身 |
| `VIA_Capability_Matrix.html v2`（前輪） | 50+ 模組能力矩陣,7 引擎分群,fan-in 依賴 | AST 掃描產出 |

## 6. 計畫 / 規格文件（append-only 累積）

| 文件 | 內容 |
|---|---|
| `PSU_Thermal_CrossMatrix_Plan.md`（上輪） | 三軸展開 + 七表 + 擷取矩陣 + 交叉匯總 + 數據 Gate |
| `PSU_Thermal_Interface_Content_Spec.md`（本輪 C） | 全介面**分析內容**規格(不含視覺) |
| 本檔（B） | 主索引 |

---

## 7. 缺口（尚未建，供 evolving SSOT 追）

- T05 供應鏈關聯邊真值(需財報附註 + 人工核可)—— 目前空表。
- T06 財報真值(MOPS,財報優先/法說次之)—— 需你過 Gate。
- T07 製程/capex/廠區知識體 —— 需年報 + 法說逐字抽取。
- 動能引擎(FIS/flow)與 PSU/Thermal 名單的**綁定層**(產業動能 → 公司 → BOM 品類)尚未接線。

---

## 方法論四問

1. **索引真值同步** — 這份 B 是「宣告式」索引;要不要我附一支 `Invoke-VIA-PT-IndexScan.ps1`,在你本機掃這些檔實際在不在位、算 sha12、把索引升級成「有實證的」清單(對齊 VPNS 那套 read-only lane 作法)?
2. **central 是否單源** — 本輪 A 的 7 表要不要直接寫進 `central/via_params.json` 當 `pt_tables` 區段(集中),還是維持 `via_pt/` 獨立目錄(隔離)?
3. **競品隔離落點** — `sovereignty=confidential` 的列要不要各自存到公司分檔(如 `data/_sovereign/AVC.csv`),主表只留公開骨架,徹底不共池?
4. **動能綁定鍵** — 產業動能要用「族群名 → 公司」還是「ticker → 公司」當主綁定鍵?（前者涵蓋未上市,後者精準但漏私有公司）
