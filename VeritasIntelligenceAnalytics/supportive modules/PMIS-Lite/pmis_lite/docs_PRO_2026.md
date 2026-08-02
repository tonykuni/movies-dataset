# PMIS-Lite PRO：補強主流 PLM × Notion 級 UI × 自動簡報 × 樞紐/智慧學習 × Process Mining × PMBOK 骨架

_定位：不重造 PLM，而是做「架在任何 PLM 之上的本機智慧工作層」——吃各家 PLM 匯出，補強其弱點、導入其優點，疊加四大 PRO 能力，用 PMBOK 串成核心。_

> **誠實邊界**：受規範產業（醫材/航太）的「變更控制系統紀錄（system of record）」仍應留在已驗證的 PLM。PRO 版是**可視化/分析/SSOT 智慧層**，不取代法規層的控制權威。這個邊界讓你導入時站得住腳。

---

## 一、主流 PLM 的優點導入 × 弱點補強

| 主流 PLM | 優點（PRO 導入） | 弱點（PRO 補強） |
|---------|-----------------|-----------------|
| **Windchill / Teamcenter** | BOM、變更治理、合規結構最強 → 導入 append-only 變更帳、狀態機、合規欄位 | 貴、重、上手慢、客製難、維護成本高 → PRO：本機免費、Notion 級 UI、滑鼠三回合客製、零安裝 |
| **Arena（雲）** | 易實作、易學、導航簡單、更新頻繁 → 導入門外漢一鍵體驗 | 進階資料管理/模擬較弱、雲端資料主權疑慮 → PRO：本機主權、進階樞紐+Process Mining 分析 |
| **Propel** | 易用、Salesforce 整合 → 導入跨部門協作視角 | 缺進階產品資料/模擬 → PRO：自動分析+智慧學習補上 |
| **OpenBOM** | Excel 風、CAD 整合強、易上手 → 導入「Excel 化」親和介面 | 學習曲線、偶發卡頓 → PRO：本機穩定、無雲端依賴 |
| **Aras（開源）** | 可組態、開源透明 → 導入 payload-driven 客製哲學 | 需工程資源自架 → PRO：設定產生器零代碼客製 |

**核心策略**：導入「強項的結構」（BOM/變更/合規/狀態機），補強「共通的痛」（貴、重、慢、UI 老、雲端疑慮、分析弱），用本機免費 + Notion UI + 智慧分析一次解決。

---

## 二、四大 PRO 能力

### 1. Notion 級使用者介面（block 式、可組態）
- **NiceGUI**（MIT，Vue.js/Quasar、Material Design、純 Python、即時更新、可打包桌面原生）——快速做出乾淨的看板/表格/頁面。
- **Reflex**（純 Python 全棧、60+ Radix UI 元件、編譯成 Next.js）——要 Notion 級元件豐富度時用。
- 體驗：block 式頁面（料件/變更/利害關係人各一塊）、看板（NPI 階段門）、可拖拉、即時。沿用你的 Visual Lock 色票與印章語彙。

### 2. 自動產生最佳化簡報 PPT / Layout
- **python-pptx**（已在用，升級）——自動生成分產品/風險/里程碑頁。
- **Jinja2**——版面/報告模板引擎，把資料套進固定版型。
- **WeasyPrint**——HTML→PDF 精緻版面（週報/儀表板列印級輸出）。
- 智慧：依資料自動選版型（單產品→時序頁；多風險→風險矩陣頁），沿用既有 slides.py。

### 3. 樞紐分析 + 自動分析 + 智慧學習
- **pandas `pivot_table` / Polars group_by**——樞紐：產品×階段×狀態交叉分析。
- **PyGWalker**——Tableau 式拖拉樞紐探索，門外漢不寫碼就能切資料。
- **DuckDB**——進程內跑分析 SQL，支撐大資料樞紐。
- **scikit-learn**——智慧學習：自動分群（相似專案）、分類（信件意圖）、異常偵測（卡關預警）。
- **river**——**線上增量學習**：隨新郵件/變更持續自我學習，不需整批重訓（呼應「智慧學習」）。

### 4. Process Mining（流程挖掘）
- **pm4py**（開源主流，⚠ AGPL-3.0）——從事件時間戳還原真實流程圖、找瓶頸、合規檢查（規定流程 vs 實際流程的偏差）。
- **NetworkX + Graphviz**——流程/相依拓撲、狀態機圖、BOM 結構圖。
- 用途：自動畫出「設計→EVT→DVT→PVT→MP 經歷幾次退件迴圈、哪關最久」，接你已做的 panorama 停滯偵測。

> ⚠ **pm4py 是 AGPL-3.0**：自用/內部分析沒問題；若要做成閉源商品散佈，需評估其商業授權。可先用 NetworkX 自建輕量「directly-follows graph」做基本流程圖，避開授權限制。

---

## 三、PMBOK 骨架帶入（核心功能 + 圖示）

把 PMBOK 十大知識領域當成 PRO 版的**功能骨架與圖示系統**，每個領域對應一塊功能與一個一字章/icon：

| PMBOK 知識領域 | 對應 PRO 功能 | 圖示概念 |
|---------------|--------------|---------|
| 整合管理 | SSOT 單一真相、跨來源串接 | 〇 合（匯流） |
| 範疇管理 | BOM/料件清單、工作項目樹 | ⊞ 範 |
| 時程管理 | MS Project 排程、里程碑、panorama 時序 | ⏱ 程 |
| 成本管理 | ERP 金額對帳、變更成本影響 | $ 本 |
| 品質管理 | 完整性 gate、合規檢查、conformance | ✓ 質 |
| 資源管理 | 利害關係人登錄、負責人指派 | ◷ 源 |
| 溝通管理 | 郵件來回全景、追蹤事項 | ✉ 訊 |
| 風險管理 | 停滯預警、卡關偵測、異常學習 | △ 險 |
| 採購管理 | PLM 變更/單據、供應商歸一 | ⊟ 採 |
| 利害關係人管理 | 組織拓撲、參與度分析 | ☷ 眾 |

**PMBOK 7 原則層**（價值導向）也可作為設計準則：以價值為核心、系統思維、領導、剪裁（tailoring）、品質內建、複雜度因應、風險應對、適應與韌性——剛好對齊本系統「泛用但合身、備援、append-only」的設計。

前台 UI 用這十個圖示做頂層導覽（Notion 式側邊欄），點一個領域就進該塊功能——既專業又一眼好懂。

---

## 四、TOP 15 本機免費函式庫（實作以上全部）

| # | 函式庫 | 實作的 PRO 能力 | 授權 |
|---|--------|----------------|------|
| 1 | **NiceGUI** | Notion 級瀏覽器 UI（看板/表格/頁面，可打包桌面） | MIT |
| 2 | **Reflex** | 純 Python 全棧、60+ Radix 元件（Notion 級豐富度） | Apache |
| 3 | **python-pptx** | 自動產生 PPT 簡報 | MIT |
| 4 | **Jinja2** | 報告/版面模板引擎 | BSD |
| 5 | **WeasyPrint** | HTML→PDF 精緻版面輸出 | BSD |
| 6 | **pandas** | `pivot_table` 樞紐分析 | BSD |
| 7 | **Polars** | 高速 group_by/樞紐 | MIT |
| 8 | **PyGWalker** | Tableau 式拖拉樞紐探索（門外漢免寫碼） | Apache |
| 9 | **DuckDB** | 進程內分析倉儲，支撐大資料樞紐 | MIT |
| 10 | **Plotly** | 互動式圖表 | MIT |
| 11 | **scikit-learn** | 智慧學習：分群/分類/異常偵測 | BSD |
| 12 | **river** | 線上增量學習（隨資料自我學習） | BSD |
| 13 | **pm4py** | Process Mining（流程發現/合規/瓶頸） | ⚠ AGPL-3.0 |
| 14 | **NetworkX** | 流程/相依/BOM 拓撲（亦可替代 pm4py 做輕量流程圖） | BSD |
| 15 | **Graphviz** | 流程圖/狀態機/組織圖渲染 | CPL/EPL |

**搭配既有棧**：pyarrow（零拷貝）、matplotlib（靜態圖）、transitions（狀態機）、rapidfuzz（對齊）——已在前幾份文件登錄。

---

## 五、落地優先序（最小改動、最大感受）

1. **先做 Notion 級前台殼（NiceGUI）**——把現有 result_html 升級成 block 式頁面 + PMBOK 十圖示側欄，門外漢一眼專業。
2. **樞紐 + PyGWalker 嵌入**——一塊「自由探索」頁，拖拉就能切產品×階段×狀態。
3. **Process Mining 輕量版（NetworkX）先上**——用事件序列畫 directly-follows graph 找瓶頸；避開 pm4py 的 AGPL，需要進階再評估。
4. **自動簡報升級（python-pptx + Jinja2）**——依資料自動選版型輸出週報 PPT。
5. **智慧學習（scikit-learn → river）**——先離線分群/異常，再上線上增量學習，做「越用越準」的卡關預警。
