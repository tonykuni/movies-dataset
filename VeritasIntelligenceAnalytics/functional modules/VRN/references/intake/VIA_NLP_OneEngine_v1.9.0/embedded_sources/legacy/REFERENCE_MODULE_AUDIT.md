# VIA NLP Application System：參考模組靜態稽核

稽核日期：2026/09/08  
版本：1.8.0

## 稽核方法

五份使用者提供的 ZIP 僅進行檔名、封裝安全、JSON／Markdown 契約與原始碼靜態檢查。沒有 import、執行、安裝或直接合併其中程式碼；因此表內的對應是架構證據與候選歸屬，不是已驗證的執行期相容性聲明。

## 參考能力對應

| 參考包 | 靜態辨識能力 | v1.7 大型模組歸屬 | 採用方式 |
|---|---|---|---|
| `b000352b…zip` | CPU-first 語意插件、20 actions、append-only knowledge、受治理 ML／DL | `NLP-CORE`、`KNOWLEDGE-GRAPH`、`GOVERNANCE-QUALITY` | 吸收契約概念；未執行或複製未知 runtime |
| `889e9dd9…zip` | Generic Layout Engine、OCR／layout adapters | `FORMAT-LAYOUT-IO` | 用作 adapter 分層與 fallback 設計證據 |
| `1106936f…zip` | Markdown editing、structure／sentence／table／evidence gates | `NLP-CORE`、`FORMAT-LAYOUT-IO` | 用作衍生修復層與 evidence gate 設計證據 |
| `files (1).zip` | Engine Standardizer、AST inventory、call graph、cluster、scaffold、decision card | `CODE-INTELLIGENCE`、`GOVERNANCE-QUALITY` | 用作元件註冊、依賴圖與禁止自動拼接的設計證據 |
| `VIA_Batch347_Bundle (3).zip` | Registry modules 與批次封裝 | `SYSTEM-MANAGER`、`EXPORT-REPORTING` | 用作註冊與輸出邊界的設計證據 |

## 七大模組責任

| 模組 | 獨立責任 | 主要輸入／輸出 |
|---|---|---|
| `NLP-CORE` | 修復、斷句、分類、實體、完整摘要、脈絡重組 | Text → NLP／summary／content roles |
| `FORMAT-LAYOUT-IO` | 本機格式抽取、Markdown layout、來源封裝 | Files → lossless layout records |
| `CODE-INTELLIGENCE` | AST／詞法、函式與類別契約、依賴、候選模板 | Code evidence → static registry |
| `KNOWLEDGE-GRAPH` | 知識體、SSOT、雙語 Mind Map、動態版本鏈 | NLP records → typed graph |
| `GOVERNANCE-QUALITY` | 事實、來源、衝突、升版與安全閘門 | Candidate outputs → pass／review／block |
| `RUNTIME-ACCELERATION` | CPU／RAM 准入、快取、批次、optional providers | Work request → bounded execution |
| `EXPORT-REPORTING` | JSON／Markdown／ZIP、manifest、handoff | Validated artifacts → deterministic package |

`SYSTEM-MANAGER` 只管理註冊、依賴、路由、生命週期和健康狀態。它不解析文字、不修改知識、不執行抽取程式碼，也不允許動態 import。

## 安全結論

- 五份 ZIP 通過 CRC、路徑穿越、symlink 與基本壓縮炸彈檢查。
- 不完整片段保持隔離，狀態為 `blocked` 或 `review_required`。
- 同名參數依 family／function scope 保存；不同值不自動決勝。
- 第三方 library 只登錄名稱與證據；不自動 import、install 或下載。
- 候選模組歸屬以 V／M／P 證據等級記錄，不宣稱已完成 runtime 驗證。
