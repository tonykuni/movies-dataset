# VIA 工具導入指引 + 給同仁/AI 的 PROMPT

_一支 PS 啟動器貼上即跑：掃你專案的模組（分支援/功能）→ 跑擷取引擎 → 跑測試 → 出 HTML 報告。此文附「給同仁或 AI」的複製即用 PROMPT。_

---

## 一、我能保證什麼、不能保證什麼（誠實）

- ✅ 引擎、掃描器、驅動器、PS 啟動器全部建好並在此**實測**：44 模組正確分類、擷取完整性保證 PASS、**測試 41/41 PASS**。
- ⚠️ 我在沙箱**無法直接讀你本機** `C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics` 或你的信箱。所以下面的 PS 是**在你機器上跑**時，才會真的掃你的專案、你的資料。

---

## 二、一鍵啟動（單檔貼上即跑）

`VIS_Launch_All.ps1`（PS7）預設值已對準你的路徑：

```powershell
# 直接跑（掃專案 + 測試 + 報告）
pwsh -File .\VIS_Launch_All.ps1

# 加上要擷取的資料夾（word/excel/csv/txt/image 皆可）
pwsh -File .\VIS_Launch_All.ps1 -DataDir 'C:\你的\資料夾'
```

它會：模組盤點（SUPPORTIVE/FUNCTIONAL）→ 引擎擷取（完整性保證＋不去重逐筆編號 CSV/UTF8BOM＋重點摘要）→ 跑全部測試 → 產 `VIS_Launch_Report.html` 並自動開啟。全程唯讀、不動原始檔。

參數：`-ProjectRoot`（掃描標的）、`-PkgParent`（含 `via_launch_driver.py` 與 `pmis_lite` 的資料夾）、`-Python`、`-OutDir`。

---

## 三、支援件先載、功能件後載（導入順序）

掃描器算出 fan-in（被幾個模組引用）自動分類：

- **SUPPORTIVE（支援件，底層先載）**：schema、encoding、numbering、textrepair、classify、keywords、resilience、completeness、store、presets、adapters… 高扇入＝多人依賴的地基。
- **FUNCTIONAL（功能件，上層後載）**：pipeline、ingest_engine、autocode、bom_template、super_bom、psu_taxonomy、self_train、process_mining、report_html… 對外產出能力。

Python 導入時：先 `from pmis_lite import schema, encoding, numbering …`（支援件），再 `import pipeline / ingest_engine …`（功能件）。

---

## 四、給同仁或 AI 的 PROMPT（直接複製）

把下面整段給接手的同仁或他的 AI，就能有步驟地導入並啟動全部 VIA 支援工具：

```
你是我的「VIA 工具導入助手」。我有一套本機工具（pmis_lite / VIS Workbench）與一支
PS7 啟動器 VIS_Launch_All.ps1。請用步驟化、一次一步的方式帶我導入並驗證，
全程遵守：只讀不改原始檔、append-only、任何自動判斷我可否決、不外傳任何資料。

第1步【定位】：確認三個路徑——(a) 專案根 ProjectRoot、(b) 含 via_launch_driver.py 與
   pmis_lite 資料夾的 PkgParent、(c) python 可執行檔。請我逐一貼回確認。

第2步【盤點】：叫我跑 `pwsh -File .\VIS_Launch_All.ps1`（先不帶 DataDir），
   看 HTML 報告的「模組盤點」，把 SUPPORTIVE 與 FUNCTIONAL 的數量與清單貼回，
   你判斷分類是否合理、有沒有該是支援卻被歸功能的。

第3步【導入順序】：依報告，帶我先載 SUPPORTIVE（地基）、再載 FUNCTIONAL（能力），
   給我對應的 import 片段，並解釋每個支援件是給誰用的。

第4步【擷取測試】：叫我加 -DataDir 指到一個小樣本資料夾（word/excel/csv/txt/image），
   重跑，看「完整性保證」是否 PASS、未解釋遺漏是否為 0。若非 0，帶我看是哪些檔、什麼原因。

第5步【測試/Debug】：看報告「測試」段，若有 fail，把失敗測試名稱與訊息貼回，
   你逐一帶我修，修完重跑到全綠。

第6步【擴量】：試點通過後，把 DataDir 換成真實資料夾、或接信箱（fetch_mailbox.py）跑全量。
   最後幫我列「這套工具現在會做什麼、還缺什麼」的檢核清單。

三原則請每步提醒我：(1) 只讀不改原始檔；(2) 只增不減、可回溯；
(3) 完整性寧可 FAIL 也不假裝——未解釋遺漏必須為 0 才算保證全抓。
```

---

## 五、Gmail / Outlook 過去兩週郵件（接法）

信箱擷取由 `fetch_mailbox.py` + `mail_chain`（Outlook COM→OAuth→IMAP 回退）處理，抓下的郵件與附件同樣灌進本擷取引擎走「保證全抓→校正→不去重編號→分類→摘要」。時間窗設兩週：

```powershell
# 抓兩週並跑一條龍（在你機器上）
python .\fetch_mailbox.py --provider outlook --since-days 14 --pipeline
```

_附件（word/excel/pdf/image）交給末日擷取引擎；image 若無 OCR 會誠實標 needs-OCR，可接 via_ocr_surya 補齊。_
