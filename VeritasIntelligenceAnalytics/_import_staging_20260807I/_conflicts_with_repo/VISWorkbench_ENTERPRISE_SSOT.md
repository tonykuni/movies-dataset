# VIS Workbench · 企業系統 SSOT 對齊預設庫 + HTML/JS 讀取

_因為 SAP、MS Project、Outlook/Gmail 都是標準系統、欄位已知，SSOT 對齊可以**事先內建**，現場不必再對。使用者仍可在 config 覆寫任一條。已測試（32/32）。_

---

## 一、核心原則：原始單號不動，系統另編（雙軌）

每個預設標明「原始單號欄位」——這個值**原封不動**存進 `source_ref`（不改變原始編號），系統另外用 numbering 生成自己的 `uid`（自動編號）。兩軌並存、可回溯。未對映的欄位不丟失，收進 `body` 尾端供 NLP。

---

## 二、六大企業系統預設對照（已內建）

| 預設 | 系統/表單 | 原始單號 | 已對映欄位數 |
|------|----------|---------|-------------|
| `sap_mm` | SAP MM 採購單/物料主檔 | EBELN（採購單號） | 8 |
| `sap_pp` | SAP PP 生產訂單/計劃訂單 | AUFNR（生產訂單號） | 6 |
| `sap_sd` | SAP SD 銷售訂單/交貨 | VBELN（銷售單號） | 7 |
| `ms_project` | MS Project 任務表（.xml） | UID（任務原生碼） | 8 |
| `outlook` | Outlook 郵件（COM/PST） | EntryID | 7 |
| `gmail` | Gmail（IMAP/API） | Message-ID | 6 |

### 對照範例（SAP MM → 統一 Record）
| SAP 欄位 | → Record | 說明 |
|---------|---------|------|
| EBELN | source_ref（不動） | 採購單號 |
| MATNR | product | 物料號 |
| MAKTX | title | 物料說明 |
| LIFNR / NAME1 | actor / counterparts | 供應商代碼/名稱 |
| BEDAT | event_time | 採購單日期 |
| MENGE | body | 數量 |
| ELIKZ | status | 交貨完成註記 |

SAP SD 用 VBELN/KUNNR/NETWR/AUDAT/GBSTK；SAP PP 用 AUFNR/GSTRP/STTXT/DISPO；MS Project 用 UID/Name/ResourceNames/Start/PercentComplete/WBS/Text1。**完整對照見 `presets.py`**，一行即可覆寫。

### 三系統互補（為何要一起對齊）
SAP = 結果的定案數字（單號、金額、料號）；MS Project = 預定的時程骨架（WBS、Baseline）；郵件 = 真實的決策脈絡（為什麼改、誰承諾）。三者對齊到同一 Record，才是完整 SSOT。用法：
```json
"sources": [
  {"type":"enterprise","preset":"sap_mm","path":"po_export.csv"},
  {"type":"enterprise","preset":"sap_sd","path":"so_export.html"},
  {"type":"mail_imap","provider":"gmail", ...}
]
```

---

## 三、HTML UI / JavaScript 參數讀取

很多 ERP（SAP GUI for HTML、Web Dynpro）與網頁表單，資料藏在 HTML/JS 裡。`html_ui.py` 用純標準庫（離線）抽出四個面向：

| 抽取 | 來源 | 用途 |
|------|------|------|
| `extract_tables` / `tables_as_dicts` | `<table>` | 報表匯出 → 直接餵 preset |
| `extract_form_fields` | `<input>/<select>/<textarea>` | 表單欄位 name/value/options |
| `extract_data_attributes` | `data-*` 屬性 | UI 參數（如 data-material-id） |
| `extract_js_data` | `<script>` 內 JS 物件/JSON | 前端組態與資料（括號配對安全擷取，寬鬆修單引號/尾逗號/無引號 key） |

**一條龍**：HTML 表格 →`tables_as_dicts`→ `apply_preset("sap_mm")` → Record，原始單號自動保留。實測 SAP GUI for HTML 匯出：表格 2 列、表單 3 控件、data 屬性 2 個、JS 組態 `{"module":"MM",...}` 全抽出。

---

## 四、價值：對齊事先完成 = 現場更快

因為這 6 個系統的對照都預先內建，帶去客戶現場時：SAP 匯出、MS Project 另存 XML、信箱自動讀——**丟進去就自動對齊到統一 Record**，不必當場逐欄對映。客製只發生在「若客戶用了自訂欄位」時覆寫那一兩條，其餘走預設。這就是「泛用引擎、對齊預置、現場零對映」。
