# 台灣電子零組件業 · 通用 BOM 模板計畫

_一套模板通吃電子業各廠：多階 BOM、替代料、AVL、位號、合規、變更控制，且接得上 AUTO SSOT（料號原始不動＋系統自動編碼、append-only、ECN 串接）。引擎已實作並測試（38/38）。_

---

## 一、設計原則

1. **一套模板、跨廠通用**：欄位與品類骨架抽象自電子業共通結構，換公司不改模板。
2. **不遺漏不出包**：驗證沿用完整性哲學——每個缺口都有原因，缺必填即 FAIL。
3. **原始料號不動、系統另編**：Item_PN 原封保留，AUTO SSOT 另鑄系統碼（雙軌可追溯）。
4. **只增不減**：版次/替代料/供應商 append-only，歷史可回溯，ECN 串「為什麼改」。
5. **公私分離**：品類骨架是公開通用知識；各廠實際 BOM/成本/供應商是機密，留本機。

---

## 二、欄位字典（9 群 · 36 欄 · 9 必填★）

| 群組 | 欄位 |
|------|------|
| **階層** | Level★、Parent_PN、Find_No |
| **品項識別** | Item_PN★、Description★、Mfr、Mfr_PN、Commodity★ |
| **用量** | Qty★、UOM★、Ref_Des（位號） |
| **採購供應** | Vendor、AVL、Alt_Group（替代料群）、Sourcing_Status、Lead_Time |
| **技術規格** | Value、Tolerance、Package、Rating、Temp_Grade |
| **生命週期** | Item_Status★、RoHS★、REACH、Halogen_Free、MSL |
| **成本** | Unit_Cost、Currency、Cost_Roll（累計） |
| **變更控制** | Rev★、ECN_No、Eff_From、Eff_To |
| **追溯** | Where_Used（系統自算）、Created_By、Created_At |

必填 9 欄：`Level, Item_PN, Description, Commodity, Qty, UOM, Item_Status, RoHS, Rev`。

---

## 三、品類骨架（7 大類 · 22 子類，可自動歸類）

| 大類 | 子類 |
|------|------|
| 主動元件 Active | IC、電晶體(MOSFET/GaN/SiC)、二極體 |
| 被動元件 Passive | 電阻、電容(MLCC/電解/鉭)、電感/磁珠、晶振 |
| 電磁機構 | 連接器、繼電器、開關、變壓器 |
| 機構件 | 外殼、散熱、緊固、標籤 |
| 板類 Board | PCB、軟板 FPC |
| 線材 Cable | 線束、排線 FFC |
| 其他 | 原材料、包材、軟韌體 |

`classify_commodity()` 自動歸類：MLCC→電容、STM32→IC、GaN→電晶體、散熱片→散熱……跨廠通用。

---

## 四、驗證規則（不遺漏不出包）

| 規則 | 說明 |
|------|------|
| 必填檢查 | 9 必填欄任一為空即 FAIL（每筆列出缺哪欄） |
| 位號≠用量 | Ref_Des 數量須等於 Qty（如 C1,C2 → Qty=2） |
| 孤兒母件 | 被引用為 Parent 卻未定義 → 標記 |
| 單一供應源 | Sourcing_Status=單一源 → 供應風險警示（建議尋二源） |
| 合規欄位 | 外銷 RoHS/REACH 不可空 |
| 成本累計 | 子件成本×用量滾算到母件（cost_rollup） |

**實測**：一張 5 列 BOM，故意留一列缺 Description/Commodity 且位號≠用量 → **正確 FAIL 並列出三個原因**，單一源料件另標警示。

---

## 五、BOM 樹操作（已實作）

- **build_tree**：母子關係樹。
- **where_used**：反查某料件被哪些母件用（往上追鏈）——實測 `Q-GAN → PCBA-MAIN → PSU-500W`。
- **cost_rollup**：成本由下往上滾算——實測 PSU-500W = 76。
- **diff_bom**：兩版比對（給 ECN 用）——新增/刪除/用量變更，實測正確。

---

## 六、與 AUTO SSOT 串接

```
BOM 匯入 → 品類自動歸類 → 驗證(不遺漏) → Item_PN 原封 + 系統自動編碼
  → 版次/ECN append-only 入庫 → where-used/成本 系統自算
  → 郵件/PLM 的「為什麼改」用 ECN_No 串進來 → SSOT
```
料號原始不動、系統另編、變更可回溯——完全接上前面建好的 AUTO CODING / AUTO SSOT。

---

## 七、導入計畫（Rollout）

| 階段 | 內容 | 產出 |
|------|------|------|
| P1 定義 | 鎖欄位字典 + 品類骨架 | 空白模板 CSV/Excel |
| P2 匯入 | 客戶現有 BOM 對映進模板 | 對映後 BOM |
| P3 驗證 | 跑 validate_bom，補齊缺漏 | 完整性報告(未解釋遺漏=0) |
| P4 替代料/AVL | 建 Alt_Group 與合格供應商 | 供應風險清單 |
| P5 合規 | 補 RoHS/REACH/無鹵/MSL | 合規檢核表 |
| P6 樹與成本 | where-used、成本累計 | 反查表＋成本總帳 |
| P7 串 SSOT | 接 ECN/郵件的「為什麼改」 | 全景 BOM SSOT |

**先試點**：單一產品線一張 BOM 走完 P1–P3，確認流程對，再全量。

---

## 八、交付檔案

- `bom_template.py`：模板引擎（欄位字典、品類骨架、驗證、樹操作）。
- `BOM_Template_Blank.csv`：空白模板（36 欄表頭），廠商直接填。
- `BOM_Template_Sample.csv`：填好的多階範例（含 GaN/電容/替代料/單一源）。

---

_品類骨架為公開電子業通用知識；各廠實際 BOM/料號/成本/供應商為機密，本工具設計上留各自本機、絕不外傳。_
