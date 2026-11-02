# VIA 三系統 U/I 同一模板 · 收尾紀錄 · 2026-11-01(VRN · VDF · VCGC)

> 操作員 2026-11-01:「VRN-2 完成上述工作後 · 呈現在 HTML U/I 上的子系統名稱還原為 VeritasReportNova · 成為 VRN 唯一系統 · 完成後開始針對 VDF / VCGC CLOSE OUT ·
> 擁有相同的 U/I 模板視覺或動畫視覺鎖定 · 功能全面完成 · 印章 logo 為透明去背無框無特效 · 以紅字大小為依據跟 header 文字做 header 大小 logo 最佳化調節加入 · 請自動測試實測實際修正」。
> 只增不減:每一項都是新版號檔,前版一字不改。四系統各自讀自己的檔;共用的只有模板冊與共用資產(「三台獨立,只共用 typekit 顏色與版面」)。

## 1. 模板 = VeritasReportNova Workbench 範本

| 項 | 內容 |
|---|---|
| 來源 | 操作員 2026-10-28 鎖定的「VIA VRN-2 Workbench」範本 → VRN2_Workbench v0100 ~ v0104(VRN 套件 v0169 · runtime v0160)|
| 顏色 | 米白紙底 #f5f4f0 · 白卡 · 線 #dbd9d3 · 墨 #1e1d1a · 印泥紅 #b5291a · 頁首色條 紅 → 琥珀 → 藍 → 青 · 燈四色鎖定不變(#16a34a / #f59e0b / #dc2626 / #9ca3af)|
| 字型 | DM Sans(內文)· DM Mono(小字 / 表頭 / 代碼)· Syne(標題 / 分頁)· Noto Sans TC(中文)· 零網路(字型包隨頁解出)|
| 字體階層 | 頁首大寫等寬小字 10px → h1 20 ~ 22px / 800 → 標語 12px · 區標 / 欄頭等寬大寫 10px · 列名 13px / 500 · 統計數字等寬 20px · 摘要卡 22 ~ 26px |
| 動畫 | 按鈕 / 分頁 / 列 hover 背景 .15s · 卡片邊框 .18s · 明細展開 .2s(-6px → 0)· 紅燈慢閃(各系統既有)|
| 印章 | 操作員附圖(「理」+ 小印「窮理盡性」· 本來就透明去背)· 無框無陰影無濾鏡 · **主印框高 = 頁首文字區塊高**(瀏覽器實量 · 44 ~ 120px)· 小印垂右下 |

## 2. 各系統做了什麼

| 系統 | 新版 | 說明 |
|---|---|---|
| VRN(VeritasReportNova)| Workbench v0104 · 套件 v0169 · RoundAll v0125 · Handle-All v0117 | 畫面名稱 VeritasReportNova / VRN(檔名 · 指令 · 收據 · 輸出冊資料不改)· 00 系統現況(輸出冊 × 來源 × 端點 × DataFrame 表頭)· 內建印章 · 版本鎖 v0102 |
| 共用(VCGC 管)| `VIA_UI_Template_SSOT_v0104.json` · `ui_support/VIA_UI_Seal_v0100.png` · `ui_support/VIA_UI_Fonts_v0100.zip` | 三系統同一套 tokens / design.css;systems 只差品牌字;assets 節 = 印章 + 字型(雜湊鎖)|
| VCGC | `CGC_MDL274_HealthMatrix_v0116.py` | 操作台 / 入口頁:範本頁首(印章 · VERITAS CENTRAL GOVERNANCE · Veritas Central Governance Console)· 字型 · 「VRN U/I」分頁改指 VeritasReportNova Workbench(只讀)· 入口頁 VRN 燈讀 VRN 自報收尾頁(只讀)|
| VDF | `VDF_ENG236_FetchMatrixUI_v0101.py` · `VDF_SystemManager_v0167.py` | 擷取矩陣多「表頭 / DataFrame Headers」欄(VDF 自己的 ENG237 唯讀讀庫 · 存快取)· 擷取矩陣頁與 VDF 操作頁範本頁首(印章 · VERITAS DATA FORGE · Veritas Data Forge)· 管理器 v0167 讓前版鏈自測照 v0103 那一代的冊驗 |

## 3. 測試(雲端容器 · Linux · Python 3.13 · 沒有 pwsh / duckdb)

| 項 | 結果 |
|---|---|
| HealthMatrix v0116 自測 | 12/12 · 前版鏈 v0112 17/17 · v0113 7/7 · v0114 7/7 · v0115 11/11 |
| VCGC 操作台實渲染(真流程 main ui · 路徑指暫存夾)| 頁首主印框 27–94px 對齊文字 27–93px · 標題 / 分頁 Syne · 米白底 · 字型載入 · 健康矩陣 iframe 換範本 · JS 錯 0 |
| ENG236 v0101 自測 | 12/12 · v0100 16/16 |
| ActivateVDF v0116 自測(經 ENG236 尾版)| 7/7 |
| VDF 管理器鏈自測 | 本容器與改動前基準相同:只差 5 項 db check / db move(沒有 duckdb · 改動前就紅)· 新增 0;前版 v0161 / v0153 單跑:尾冊下 4 + 2 紅 → v0167 的 v0103 年代冊下 0 |
| VCGC 中央編號 | 只登本批 +295 列 · audit 遺失 0 · 改身分 0 · 重號 0(冊內不一致 1 = 改動前就有)|
| VCGC registry-sync | 乾跑 新 64 · 變 117 · 退役 0 · 撞號 0 → --apply |
| VCGC 全功能串測 | 見第 4 節 |

## 4. 沒做到 / 要桌機做的

- **DataFrame 表頭(VDF DuckDB 表)要在桌機讀**:容器沒有 duckdb,欄名格寫「未讀到」(原因在頁首);桌機跑 VDF ui 一次就會讀庫、存快取 `VIA_Reports/vdf/FETCH_MATRIX_columns_latest.json`。
- **PowerShell 沒實跑**:容器沒有 pwsh;VRN 一行入口的雜湊鏈在 Python 端照 PowerShell 算法核過。
- **VCGC 串測紅站 4 個都是改動前就紅**(TestAuto v0106 · NumberingSystem v0119 · UIEngine v0107 缺 duckdb · NumberGrant v0100;在 origin/main 乾淨工作樹同樣 rc 1)· SDD X-NUM 既有缺號仍待 VCGC 處理。
- **「功能全面完成」只做到 U/I 這一層**:VDF / VCGC 的功能面(資料庫健康 · 擷取 · 治理待辦 104 項)這一輪沒有動;收尾燈以各系統自己的收尾頁為準(VRN = REVIEW · VCGC closeout_lamp = YELLOW)。
- **CLAUDE.md / AGENTS.md 的四系統命名規則(L123)沒改**:那是 VCGC 的政策冊;VRN 唯一系統只改了畫面上的名字。

## 5. 桌機要做的

1. 拉這條分支(或合併後的 main):`git -C "$HOME\OneDrive\Documents\movies-dataset" pull --ff-only origin claude/vrn2-closeout-authorization-y4ixl7`
2. VRN:貼 `vrn2_release_v0169/VRN2_HandleAll_v0117.md` 的最短一行(或 `VRN2_Handover_Desktop_20261101.md` 第 10 節)。
3. VCGC:`via-vcgc`(預設 ui)→ 操作台頁首換成印章範本 · 「VRN · VeritasReportNova」分頁。
4. VDF:`via-vdf`(ui)→ 擷取矩陣頁籤多表頭欄(第一次會讀庫)· 操作頁頁首換成印章範本。
5. 看到 `[RED]` 或頁首沒換 → 貼回給 AI。
