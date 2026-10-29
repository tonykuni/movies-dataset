# VRN-2 一鍵 v0146(cmd / PowerShell 都能貼 · 套件 v0146 = 啟動器 v0146 + runtime v0146 = v0145 + Workbench v0102 · 處理器 v0109 · SSOTSync v0101 · HistoryAlign · DataIntegrate · ConsensusJoin · 共識引擎 v0120)

操作員 2026-10-29 政策:三系統獨立;SSOT / Regex / 同義字 / 政策由基層提出(ID 空白)→ VCGC 偵測衝突 → 使用者 + AI 修正 → VCGC 核號 → 子系統自動補填;VRN-2 快速收尾用 HTML U/I:輸出位置可用 Windows I/O(拖曳 / 對話框)或連接雲端,輸出 Parquet 增量擷取,增量擷取用 DuckDB 管理。

桌機 2026-10-29 08:14 實跑 v0144(52 份 · 2422 秒):前後端已連結、⑬ 走 duckdb 正式路徑、⑤b 綠;但 ⑦ 1201 秒裡約 1050 秒管理器沒有輸出 —— 擷取快取 52/52 命中,真正在跑的是 v0243 的冪等閘(3 份 ×2 單路序跑、不吃快取)。操作員問「是第一次啟動還是加速器沒作用」:都不是。

桌機 2026-10-29 10:25 實跑 v0145(52 份 · 2546 秒):CPU 被別的程序佔 87.5% → 啟動器自動降 1 路、優先權不變;冪等閘並行有效(151 秒 · R1 73 / R2 78)、⑬ duckdb 增量綠(新檔 0 / 已知 52);慢在輸出冊 969 秒(第二讀取器回查 10,908 值 · 單路 + OneDrive I/O)。紅燈同前(3014TT POINT_3 · 3 份年度數據缺項 → 要貼回 zip)。操作員問「昨天不是可以擷取 TWSE/TPEX/YFINANCE 資料嗎 現在為何不行」:昨天跑的是桌機線自己的啟動器(管理器 v0249 有 ⑥e MarketFetch);本套件線(管理器 v0243 → v0255)從來沒有這一步 —— v0146 補上。

v0146 = v0145 入口 + runtime v0146(= runtime v0145 的 167 個成員逐位元保留 + 8 個新檔):

| 元件 | 版本 | 改了什麼 |
|---|---|---|
| Workbench | v0102(v0101 留著)| 表頭雙語(Report Date / 報告日期 · … · Adjusted Target Price / 調整後目標價;不在清單的欄底線 → 空格 · 原欄名在 title)· 內容全部靠上 · 金額欄顯示為**百萬台幣 + 千分位**(依列 ITEM / TABLE 判原單位:bn → ×1000 · thousand → ÷1000 · 沒標視為百萬;每股 / 倍數 / % 原值 · 滑鼠停留看原值)· 統計磚 clamp + 逐 px 自動縮到放得進(不再爆格)· 左欄「輸出檔案夾 · 長線資料庫(Parquet 增量)」在其他系統 Gate 之上 · 右欄第一區 = 輸入去重矩陣 + 目前引擎狀態(含 ⑥e / ⑥f / ⑬ / ⑬b / ⑬c)· 舊資料庫整合提問(整合 / 不要)· 歷史對齊表 · 資料冊多 Combined / FinancialAligned / Deleted · logo 留白 1.5% · LANCZOS 放大 180%(仍透明無框無特效)|
| 市場擷取 ⑥e | 借共用夾 `functional modules\VRN\VRN2_MarketFetch_v*.py`(桌機線工具 · 只讀 · 最新號)| 跑完 ⑦ 後 `--fetch`(TWSE / TPEX / Yahoo 還原價 · 年度財報)再 `--fill` → `VIA_Reports\vrn2\market\VRN2_Market_latest.json`;共用夾沒有 → 灰;缺 yfinance 等套件 → 黃交 VCGC;`$env:VIA_VRN2_NO_MARKET='1'` 不抓;上限 `$env:VRN2_MARKET_WAIT`(預設 1800 秒)|
| 共識合併 ⑥f | VRN2_ConsensusJoin v0100 + 操作員上傳的 VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine v0120(原樣內附)| 代號 = 基本資料冊 TICKER → 引擎抓 FactSet(鉅亨)/ YFinance 共識 → `consensus\VRN2_Consensus_latest.json` → **Combined 冊** `output\VRN2_Combined_latest.{json,csv,parquet}`:每份報告一列,欄序 REPORT_DATE · FILENAME · TICKER · YFINANCE_TICKER · BLOOMBERG_TICKER · NAME · BROKER · ANALYST · RATING · TARGET_PRICE · **TARGET_PRICE(ADJ)** · **FACTSET_TARGET_PRICE_MEDIAN** · **YFINANCE_TARGET_PRICE_MEDIAN** · **2026 / 2027 / 2028_DILUTED_EPS_FACTSET** · **2026 / 2027 / 2028_PER_FACTSET**(真實年份 · n = 今年)· CURRENT_PRICE_REPORT · UPSIDE_PCT(ADJ) · ADJ_CLOSE · ADJ_CLOSE_BEFORE_REPORT · TOPIC & SUMMARY · STATUS;缺 yfinance → 黃、欄留空;`$env:VIA_VRN2_NO_CONSENSUS='1'` 不抓 |
| 歷史對齊 ⑬b | VRN2_HistoryAlign v0100 | 每份報告:科目同義字 → 年度期間 → 單位倍率自動對(1 / 1000 / 0.001 …)→ **至少一期**(金額 0.97 ~ 1.03 或每股)對上才覆蓋 → 歷史覆蓋預估(VALUE_FINAL / VALUE_SOURCE / RECON_RATIO · 報告值留 VALUE_REPORT)→ 差 > 3% 的報告值進**刪除區** `VRN2_Deleted_latest` → 加減法(毛利 = 營收 − 成本 · 稅後 = 稅前 − 稅)/ 乘除法(毛利率 · 營益率 · 淨利率 · ROE · 營收成長率)檢驗只報不改 → `VRN2_FinancialAligned_latest.{json,csv,parquet}` + 收據 `VRN2_HistoryAlign_latest.json`;沒市場資料 → 灰;一期都沒對上 → 黃不覆蓋 |
| 舊資料庫整合 ⑬c | VRN2_DataIntegrate v0100 + 處理器 v0109 | 掃輸出夾及其上一層 / `VIA_Reports\vrn2\legacy_in` / `$env:VRN2_INTEGRATE_DIRS` 的 CSV / TSV / XLSX / Parquet / JSON / Google Sheet 匯出 CSV(.gsheet 捷徑只列)→ 自適應欄位對齊(同義字 + 內容型態 · 對不到的欄保留 X_)→ Workbench 問「要不要整合?」→ `vrn2://integrate?apply=1`:新整合檔 `<輸出夾>\VRN2\integrated\VRN2_Integrated_<冊>_<時間>.{json,csv,parquet}`(VRN-2 冊 ∪ 舊檔 · 同鍵同值去重 · 同鍵不同值兩邊都留標 CONFLICT)→ 重讀核對 → **原檔絕不刪**,核對過才複製到 `%TEMP%\VRN2_Integrate_<時間>\originals\` 提醒自行處理;不要 → `dismiss=1`(同內容下次不再問)|
| SSOT 提案 | VRN2_SSOT_Proposals v0100 + SSOTSync v0101 | Gemini 對話的 9 條提案(台股代號 TWSE / Yahoo / Bloomberg 三形式 · ETF 尾碼分類 · 台北 / 香港電話 · 評等代碼 0 ~ 5 中英同義字 · 目標價同義字 · 分析師職稱 · U/I 數值格式)`ssot_id` 空白 · `VRN2-PROP-xxxx` → 併進 ⑤b 的核號請求冊,等 VCGC 核發 |
| 啟動器 | ActivateVRN-2 v0146 | ⑥e / ⑥f 在 ⑦ 之後、⑬b / ⑬c 在 ⑬ 之後;收據 `VRN2_Closeout_v0146.json` 多 `market` / `consensus` / `history_align` / `integrate`;非關鍵步驟只灰 / 黃、不轉紅;Workbench v0102 · 處理器 v0109 · SSOTSync v0101;v0145 的管理器 v0255 與 v0144 的 ⑤b / ⑬ 照舊 |

前一版 v0145 = v0144 入口 + runtime v0145(= runtime v0144 的 166 個成員逐位元保留 + 1 個新檔):

| 元件 | 版本 | 改了什麼 |
|---|---|---|
| 管理器 | VRN_SystemManager v0255(v0243 留著 · 釘名前版 v0243;v0244 ~ v0254 是桌機線 `functional modules\VRN` 的號,本線跳過)| 冪等閘契約不變(同主跑子行程路徑 · 不吃擷取快取 · R1 / R2 / 主跑紀錄三方比對 · GREEN / STALE_RECORD / NONDETERMINISTIC),只改跑法:每波**一份一個單路子行程並行**(預設 3 路 · `$env:VRN2_IDEM_LANES`)· R1 跑完才跑 R2(OCR 快取不會被同一份的兩次同時寫)· 每 30 秒心跳 · 每波 / 每份秒數進 `IDEMPOTENCE_latest.json` 的 `timing`;階段計時(擷取迴圈 · 驗收 + 摘要 · 輸出冊 · U/I 輸出冊頁 · 調節輪 · 冪等閘)即時印、收尾一行 `[計] 階段耗時` · `VIA_Reports\vrn2\VRN2_Phase_Timing_latest.json` |
| 啟動器(v0145)| ActivateVRN-2 v0145 | 改指管理器 v0255 · 收據 `VRN2_Closeout_v0145.json`;v0144 的 ⑤b / ⑬ / 處理器 v0108 / Workbench v0101 與 v0143 的單機閘 / 上限 / ⑫b 補放照舊 |

前一版 v0144 = v0143 入口 + runtime v0144(= runtime v0142 的 162 個成員逐位元保留 + 4 個新檔):

| 元件 | 版本 | 改了什麼 |
|---|---|---|
| 處理器 | VRN2_UIAction v0108(v0104 留著;v0105 / v0107 是桌機線 publish 處理器的號,本線跳過)| `vrn2://pick?kind=outdir`:Windows 資料夾對話框選**輸出夾**(可新建;選 OneDrive / Google Drive / Dropbox 同步夾 = 連接雲端)→ `VIA_Reports\vrn2\VRN2_Output_Config.json`;`vrn2://outdir?reset=1` 取消;`--set-outdir`;舊版 U/I 左側多「輸出位置(window I/O)」區塊 |
| 增量庫 | VRN2_OutputStore v0100 | 啟動器 ⑬:四本冊 + Workbench + 收據鏡像到 `<輸出夾>\VRN2\latest`;增量 Parquet 庫 `<輸出夾>\VRN2\vrn2_store.duckdb`(DuckDB:catalog 按 SHA-256 · 各冊帶 run_id / file_sha · 只追加本輪新檔的列 · 同檔同 SHA 再跑 0 列 · 檔改了當新檔、舊列保留)+ `parquet\<冊>\run=<id>.parquet` · `catalog.parquet`(DuckDB 原生寫);沒 duckdb 套件 → pyarrow 備援(黃並說明);未設輸出夾 → 灰、輸出留在 `VIA_Reports\vrn2\output` |
| SSOT-ID 協作 | VRN2_SSOTSync v0100 | 啟動器 ⑤b:讀元件登記冊 → 待核號條目寫請求冊 `contract/VRN2_NUMBER_REQUEST_latest.json`(`ssot_id` 空白 · VRN-2 內部自撞另列)→ 讀 VCGC 核發冊 `VCGC_NUMBER_GRANT_latest.json` → 核發的補填 `ssot_id`、衝突的標「待人判」→ 新版登記冊(只增不減)· `VRN2_NUMBER_STATE_latest.json`;協定見 `docs/handoff/ai/VIA_SSOT_ID_Protocol_v0100.md` |
| Workbench | v0101(v0100 留著)| 03 匯出頁:「輸出位置 · window I/O」(選輸出夾 / 取消 / 拖曳區 → 放開自動開對話框)+「增量 Parquet 庫 · DuckDB 管理」收據表;04 交接頁:「SSOT · Regex · 同義字 · 政策編號協作」狀態表 |
| 啟動器(v0144)| ActivateVRN-2 v0144 | 註冊處理器 v0108 · ⑤b · ⑬ · 收據多 `ssot_sync` / `output_store`;`$env:VRN2_OUTPUT_DIR` 可預設輸出夾;v0143 的單機閘 / 上限 / ⑫b 補放照舊 |

套件 `VRN2_Closeout_v0146.zip`(SHA-256 `67fde9888e9f466d8f3ccf45f2afd2a2d4873e3d82d66493d5ee65202916bb96` · 從 `vrn2_release_v0146` 取 · 解壓到 `%USERPROFILE%\Downloads\VRN2_Closeout_v0146`)。
沒有 .ps1:下面那一行(cmd 也能貼)從 GitHub 讀本檔的一鍵程式碼、核對 SHA-256 才執行;一鍵再核對套件雜湊與套件內逐檔雜湊才解壓。

| 步驟 | v0146 做什麼 |
|---|---|
| ① ② ③ ③b | 同 v0145(套件雜湊 + 逐檔核對 → 解壓 → 定位 VRN-2 程式夾)|
| ④ | `python ActivateVRN-2_v0146.py [--source …]`:單機閘 → ①~⑤ → ⑤b SSOT-ID 核號同步(含提案冊)→ ⑥ → ⑦(管理器 v0255)→ **⑥e 市場擷取 → ⑥f 共識合併(Combined 冊)** → ⑧~⑫ → ⑫b 補放 → 四點原文核對 → 收據 → ⑬ 輸出位置 · 增量庫 → **⑬b 歷史對齊 → ⑬c 舊資料庫整合掃描** → Workbench v0102 渲染 + 開啟 |
| ⑤ | 摘要多七行:⑬ 輸出位置 / 增量庫 · ⑤b SSOT-ID · 階段耗時 · **⑥e 市場擷取 · ⑥f 共識合併 · ⑬b 歷史對齊 · ⑬c 舊資料庫整合**(都讀 `VRN2_Closeout_v0146.json`)|
| ⑤b ⑤c | vrn2:// 處理器 = `functional modules\\VRN2\\VRN2_UIAction_v0109.py`(設定檔 v0146 · 多 `vrn2://integrate`)· U/I 有輸入區塊 · 沒開就代開 |

開關:`$env:VIA_VRN2_NO_MARKET` / `VIA_VRN2_NO_CONSENSUS` / `VIA_VRN2_NO_HISTORY` / `VIA_VRN2_NO_INTEGRATE` 各關一步 · `$env:VRN2_MARKET_WAIT` / `VRN2_CONSENSUS_WAIT` 上限 · `$env:VIA_FETCH_PY` 擷取用的 Python(預設 `%USERPROFILE%\envs\via_tw_fetch`)· `$env:VRN2_INTEGRATE_DIRS` 多掃的夾 · `$env:VRN2_SOURCE` 來源夾 · `$env:VRN2_OUTPUT_DIR` 輸出夾(沒在 U/I 選過時用)· `$env:VRN2_PACKAGE` · `$env:VRN2_LAUNCHER_ARGS` · `$env:VRN2_NO_REPASS` · `$env:VRN2_NO_UI` · `$env:VRN2_FORCE_PARALLEL` · 四個上限變數。
VRN-2 主體(ENG397 · 摘要器 · 驗證器 · 工具橋 · OCR 橋 · 管理器 v0255)與 runtime v0145 的 167 個成員一個位元組都不動(v0101 / v0108 / v0100 留著,薄尾疊在上面;基本資料 / 年度數據 / 摘要三冊不改,Combined / FinancialAligned / Deleted 是新冊);共用夾的 MarketFetch 與上傳的共識引擎只借用不改;VRN-1 / VDF / VCGC 不碰(SSOT-ID 只讀 VCGC 的核發冊)。

## 在「命令提示字元(cmd)」或 PowerShell 都能貼的一行(建議用這個)

這一行在 cmd 或 PowerShell 貼上都可以:它開 Windows PowerShell → 從 GitHub 分支 `claude/optimistic-goodall-yhalc5`(讀不到 → `main`)讀本檔的一鍵程式碼 → **核對 SHA-256** → 才執行(不存檔 · 不改執行原則 · 結束碼 GREEN 0 / YELLOW 2 / RED 1)。

```bat
powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAEMAbwBuAHQAaQBuAHUAZQAnAAoAdAByAHkAIAB7ACAAWwBDAG8AbgBzAG8AbABlAF0AOgA6AE8AdQB0AHAAdQB0AEUAbgBjAG8AZABpAG4AZwAgAD0AIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAgAH0AIABjAGEAdABjAGgAIAB7ACAAfQAKACQAUgAgACAAPQAgAGkAZgAgACgAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACkAIAB7ACAAJABlAG4AdgA6AFYAUgBOADIAXwBSAE8ATwBUACAAfQAgAGUAbABzAGUAIAB7ACAAJwBDADoAXABVAHMAZQByAHMAXAB0AG8AbgB5AGsAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdABcAFYAZQByAGkAdABhAHMASQBuAHQAZQBsAGwAaQBnAGUAbgBjAGUAQQBuAGEAbAB5AHQAaQBjAHMAJwAgAH0ACgAkAEIAcgAgAD0AIAAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnAAoAJABQACAAIAA9ACAAJwBWAGUAcgBpAHQAYQBzAEkAbgB0AGUAbABsAGkAZwBlAG4AYwBlAEEAbgBhAGwAeQB0AGkAYwBzAC8AZABvAGMAcwAvAGgAYQBuAGQAbwBmAGYALwBhAGkALwB2AHIAbgAyAF8AcgBlAGwAZQBhAHMAZQBfAHYAMAAxADQANgAnAAoAJABIACAAIAA9ACAAJwA5AGYANwA0ADkAMAA4ADAANgBkADEAOABjADgAYgBlADAAMABlAGMAZgA2AGEANABmADQAMwBlAGIAZQBlAGYANQA2ADUAYwAwAGMAYwBiAGIAYwAzAGEAZAA3AGUAYQA1AGYAOAAyADIAYgBiADcAZgAyAGEANAA4AGIAZgBhACcACgBXAHIAaQB0AGUALQBIAG8AcwB0ACAAKAAnAFsAVgBSAE4ALQAyAF0AIABQAG8AdwBlAHIAUwBoAGUAbABsACAAJwAgACsAIAAkAFAAUwBWAGUAcgBzAGkAbwBuAFQAYQBiAGwAZQAuAFAAUwBWAGUAcgBzAGkAbwBuACAAKwAgACcAIAC3ACAAnl8gAEcAaQB0AEgAdQBiACAAgIsATnWTIAB2ADAAMQA0ADYAIAALeg9fvHgoADhoDVwgAFMASABBAC0AMgA1ADYAIACMX/dXTIgpACcAKQAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABZAGUAbABsAG8AdwAKACQAdABvAHAAIAA9ACAAZwBpAHQAIAAtAEMAIAAkAFIAIAByAGUAdgAtAHAAYQByAHMAZQAgAC0ALQBzAGgAbwB3AC0AdABvAHAAbABlAHYAZQBsACAAMgA+ACQAbgB1AGwAbAAKAGkAZgAgACgALQBuAG8AdAAgACQAdABvAHAAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIAAkAFIAIAANTi9mIABnAGkAdAAgAAlQFmJ+Yg1OMFIgAGcAaQB0ACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAGUAeABpAHQAIAAxACAAfQAKACQAdABvAHAAIAA9ACAAIgAkAHQAbwBwACIALgBUAHIAaQBtACgAKQAKACQAdAAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACgAWwBJAE8ALgBQAGEAdABoAF0AOgA6AEcAZQB0AFQAZQBtAHAAUABhAHQAaAAoACkAKQAgACgAJwB2AHIAbgAyAF8AYgBvAG8AdABfACcAIAArACAAKABHAGUAdAAtAEQAYQB0AGUAKQAuAFQAbwBTAHQAcgBpAG4AZwAoACcAeQB5AHkAeQBNAE0AZABkAF8ASABIAG0AbQBzAHMAJwApACkACgBOAGUAdwAtAEkAdABlAG0AIAAtAEkAdABlAG0AVAB5AHAAZQAgAEQAaQByAGUAYwB0AG8AcgB5ACAALQBGAG8AcgBjAGUAIAAtAFAAYQB0AGgAIAAkAHQAIAB8ACAATwB1AHQALQBOAHUAbABsAAoAJAB6ACAAPQAgAEoAbwBpAG4ALQBQAGEAdABoACAAJAB0ACAAJwBvAG4AZQBjAGwAaQBjAGsALgB6AGkAcAAnADsAIAAkAG8AawB6ACAAPQAgACQAZgBhAGwAcwBlAAoAZgBvAHIAZQBhAGMAaAAgACgAJABiACAAaQBuACAAJABCAHIALAAgACcAbQBhAGkAbgAnACkAIAB7AAoAIAAgAGYAbwByAGUAYQBjAGgAIAAoACQAdwAgAGkAbgAgADAALAAgADIALAAgADQALAAgADgALAAgADEANgApACAAewAgAGkAZgAgACgAJAB3ACkAIAB7ACAAUwB0AGEAcgB0AC0AUwBsAGUAZQBwACAALQBTAGUAYwBvAG4AZABzACAAJAB3ACAAfQA7ACAAZwBpAHQAIAAtAEMAIAAkAHQAbwBwACAAZgBlAHQAYwBoACAALQBxACAAbwByAGkAZwBpAG4AIAAkAGIAIAAyAD4AJgAxACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACkAIAB7ACAAYgByAGUAYQBrACAAfQAgAH0ACgAgACAAZwBpAHQAIAAtAEMAIAAkAHQAbwBwACAAYQByAGMAaABpAHYAZQAgAC0ALQBmAG8AcgBtAGEAdAA9AHoAaQBwACAALQBvACAAJAB6ACAAKAAnAG8AcgBpAGcAaQBuAC8AJwAgACsAIAAkAGIAIAArACAAJwA6ACcAIAArACAAJABQACkAIABWAFIATgAyAF8ATwBuAGUAQwBsAGkAYwBrAF8AdgAwADEANAA2AC4AbQBkACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAE4AdQBsAGwACgAgACAAaQBmACAAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAALQBlAHEAIAAwACAALQBhAG4AZAAgACgAVABlAHMAdAAtAFAAYQB0AGgAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACQAegApACkAIAB7ACAAJABvAGsAegAgAD0AIAAkAHQAcgB1AGUAOwAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAoACcAWwAIil0AIAAATnWTC3oPX7x4hk+QbiAARwBpAHQASAB1AGIAIAAnACAAKwAgACQAYgApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEQAYQByAGsARwByAGEAeQA7ACAAYgByAGUAYQBrACAAfQAKAH0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAG8AawB6ACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAgIsNTjBSIABHAGkAdABIAHUAYgAgAAZSL2UgACQAQgByACAAFmIgAG0AYQBpAG4AIACEdgBOdZMLeg9fvHgoALJ9740gAC8AIABnAGkAdAApACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAGUAeABpAHQAIAAxACAAfQAKAEUAeABwAGEAbgBkAC0AQQByAGMAaABpAHYAZQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJAB6ACAALQBEAGUAcwB0AGkAbgBhAHQAaQBvAG4AUABhAHQAaAAgACQAdAAgAC0ARgBvAHIAYwBlAAoAJABtAGQAIAA9ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFIAZQBhAGQAQQBsAGwAVABlAHgAdAAoACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHQAIAAnAFYAUgBOADIAXwBPAG4AZQBDAGwAaQBjAGsAXwB2ADAAMQA0ADYALgBtAGQAJwApACwAIABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAApACAALQByAGUAcABsAGEAYwBlACAAIgBgAHIAYABuACIALAAgACIAYABuACIACgAkAGMAbwBkAGUAIAA9ACAAWwByAGUAZwBlAHgAXQA6ADoATQBhAHQAYwBoACgAJABtAGQALAAgACcAKAA/AHMAKQBgAGAAYABwAG8AdwBlAHIAcwBoAGUAbABsAFwAbgAoAC4AKgA/ACkAXABuAGAAYABgACcAKQAuAEcAcgBvAHUAcABzAFsAMQBdAC4AVgBhAGwAdQBlAAoAJABzAGgAYQAgAD0AIAAtAGoAbwBpAG4AIAAoAFsAUwBlAGMAdQByAGkAdAB5AC4AQwByAHkAcAB0AG8AZwByAGEAcABoAHkALgBTAEgAQQAyADUANgBdADoAOgBDAHIAZQBhAHQAZQAoACkALgBDAG8AbQBwAHUAdABlAEgAYQBzAGgAKABbAFQAZQB4AHQALgBFAG4AYwBvAGQAaQBuAGcAXQA6ADoAVQBUAEYAOAAuAEcAZQB0AEIAeQB0AGUAcwAoACQAYwBvAGQAZQApACkAIAB8ACAARgBvAHIARQBhAGMAaAAtAE8AYgBqAGUAYwB0ACAAewAgACQAXwAuAFQAbwBTAHQAcgBpAG4AZwAoACcAeAAyACcAKQAgAH0AKQAKAGkAZgAgACgAJABzAGgAYQAgAC0AbgBlACAAJABIACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAAE51kwt6D1+8eCAAUwBIAEEALQAyADUANgAgAA1ODVwoACQAcwBoAGEAKQC3ACAADU73V0yIIgAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAZQB4AGkAdAAgADEAIAB9AAoAVwByAGkAdABlAC0ASABvAHMAdAAgACgAJwBbAEcAUgBFAEUATgBdACAAAE51kwt6D1+8eCAAUwBIAEEALQAyADUANgAgACcAIAArACAAJABIAC4AUwB1AGIAcwB0AHIAaQBuAGcAKAAwACwAIAAxADIAKQAgACsAIAAnACAA+HYmeyAAkiEgAChXIABQAG8AdwBlAHIAUwBoAGUAbABsACAA4Yj3V0yIJwApACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEcAcgBlAGUAbgAKAHQAcgB5ACAAewAgACYAIAAoAFsAcwBjAHIAaQBwAHQAYgBsAG8AYwBrAF0AOgA6AEMAcgBlAGEAdABlACgAJABjAG8AZABlACkAKQAgAH0AIABjAGEAdABjAGgAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACgAJwBbAFIARQBEAF0AIAAATnWT91dMiC1Ot2UoACpnFGUqYoR2i08WWSkAOgAnACAAKwAgACQAXwAuAEUAeABjAGUAcAB0AGkAbwBuAC4ATQBlAHMAcwBhAGcAZQAgACsAIAAnACAAtwAgACcAIAArACAAJABfAC4ASQBuAHYAbwBjAGEAdABpAG8AbgBJAG4AZgBvAC4AUABvAHMAaQB0AGkAbwBuAE0AZQBzAHMAYQBnAGUAKQAgAC0ARgBvAHIAZQBnAHIAbwB1AG4AZABDAG8AbABvAHIAIABSAGUAZAA7ACAAJABnAGwAbwBiAGEAbAA6AEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAAPQAgADEAIAB9ACAAIAAgACMAIABDAG8AZABlAHgAIAAjADUANQAxADoAi08WWQOQ+lGGT19OgYkgAHIAYwAgADEACgBlAHgAaQB0ACAAJAAoAGkAZgAgACgAJABuAHUAbABsACAALQBuAGUAIAAkAGcAbABvAGIAYQBsADoATABBAFMAVABFAFgASQBUAEMATwBEAEUAKQAgAHsAIABbAGkAbgB0AF0AJABnAGwAbwBiAGEAbAA6AEwAQQBTAFQARQBYAEkAVABDAE8ARABFACAAfQAgAGUAbABzAGUAIAB7ACAAMAAgAH0AKQAgACAAIAAjACAAdgAwADEANAA2ACgAQwBvAGQAZQB4ACAAIwA1ADUAMAApADoATgBFAFgAVAAgAIR2yHE2Xt5WGZALUFBbTIgLeoR2IAByAGMAKABHAFIARQBFAE4AIAAwACAAtwAgAFkARQBMAEwATwBXACAAMgAgALcAIABSAEUARAAgADEAIACSISAAYwBtAGQAIACEdiAAJQBFAFIAUgBPAFIATABFAFYARQBMACUAKQAKAA==
```

或:在 cmd 先輸入 `powershell` 按 Enter,再貼下面整段程式碼。

程式碼 SHA-256(本文 · 一行核對的就是這個):`9f7490806d18`

```powershell
& {
  # ===== VRN-2 一鍵 v0146(套件 v0146 = 啟動器 v0146 + runtime v0146 = v0145 + 8 個新成員;v0146 = 桌機 2026-10-29 10:25 貼回 2546 秒(CPU 被佔 87.5% → 1 路)+ 操作員 U/I 與資料需求:Workbench v0102 雙語表頭 / 靠上 / 百萬台幣千分位 / 自動縮放 / 左欄輸出夾 / 右欄去重矩陣 + 引擎狀態 / logo 180% · ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 MarketFetch)· ⑥f 共識 Combined(FactSet / YFinance 中位數 · 真實年度 EPS / PER)· ⑬b 歷史對齊(至少一期對上才覆蓋 · 刪除區)· ⑬c 舊資料庫整合(問使用者 · 原檔不刪)· 非關鍵步驟不轉紅;v0145 = 套件 v0145 = 啟動器 v0145 + runtime v0145 = v0144 + 管理器 v0255 · 桌機 2026-10-29 08:14 實跑 2422 秒的速度修正:冪等閘每波 3 份並行(VRN2_IDEM_LANES)· 每 30 秒心跳 · R1 / R2 計時進 IDEMPOTENCE 收據 · 階段計時 VRN2_Phase_Timing_latest.json + 一行總表 · ⑤ 摘要多印階段耗時;v0144 = 啟動器 v0144 + runtime v0144 · 操作員 2026-10-29 政策:⑬ 輸出位置(U/I 選輸出夾 · Windows 對話框 / 拖曳 → 對話框 / OneDrive 等同步夾 = 雲端)+ 增量 Parquet 庫(DuckDB · 只追加 SHA-256 新檔的列 · pyarrow 備援)· ⑤b SSOT-ID 核號同步(VRN-2 側:請求冊 ssot_id 空白 → 讀 VCGC 核發 / 衝突 → 自動補填出新版登記冊)· 處理器 v0108(v0105 / v0107 是桌機線的號)· Workbench v0101;v0143 = 啟動器 v0143 + runtime v0142 不動;v0143 = 桌機 2026-10-29 實跑貼回的修正:單機閘(同一 VIA 根另一個啟動器還在跑就不跑 · VRN2_FORCE_PARALLEL=1 強制)· ⑫b 逾時 120→600 秒且子行程失敗由本支補放 U/I 輸入區塊 · ⑦ 無輸出上限 1500→3600 秒 · 工具冊 300→900 秒 · ⑪ 等驗證 1800→3600 秒 · 收據 VRN2_Closeout_v0146.json 多 guard / limits / ui_block;前一版 = v0141 入口 + 摘要器 ENG062 v0117(四點開頭不再帶頁首列 / 標題列 / 小標題)+ Workbench U/I v0100(操作員 2026-10-28 上傳範本視覺鎖定 · 綁本輪收據與輸出冊 · 收尾後自動產出並開啟 · VRN2_Logo.png 自動去背);v0142 = 另一團隊收尾套件 v0104 的 v0140 入口 + 修正:摘要器 ENG062 v0116 四點補齊階梯(短訊 / bullet / 整頁文字 · 每點仍是原文精確字串)· 管理器 v0243 冪等閘走主跑同一條子行程路徑重跑兩次並分類(GREEN / 主跑紀錄過期 → 清該檔快取自動再跑一輪 / 引擎非冪等)· 原文核對 v0104 缺句 = 待核對不是 FAIL · 獨立驗證器 v0110;v0142 整合一支 第二回:驗證器 v0110 DUPKEY 位置證據 · 對調診斷 · EPS 格 · 摘要每類都出現 · ⑫a 借工具前 fast-forward VRN-1 的倉;v0135 Codex #561 修正:驗證器 v0104 空值記號看該格 · 字距只接逗點 / 小數點後的空白;v0134 整合一支:處理器 v0104 · U/I 開不開只認 VRN2_NO_UI · ⑨ 交接不回退;一鍵的 ⑤b / ⑤c 留著當備援 · v0133 前後端連結:U/I 左側「輸入(window I/O)」→ vrn2://pick 開 Windows 對話框選檔案夾 / 檔案(pdf · word · txt · 影像)→ 稽核 → 當來源夾 · 三類只開「個股報告/訊息」· ⑤b 檢查 vrn2:// 註冊與 U/I 區塊 · $env:VRN2_SOURCE 直接指定來源夾)· v0132(工具橋 v0101:借不到 VRN-1 的工具時說清楚下一步 · VRN-1 / VRN-2 / VDF / VCGC 各自獨立)· v0131(工具相互取用:② 借出工具冊 · ⑫ 借 VRN-1 的 PIVOT 資料庫工具 · VRN-2 主體不動)· v0130 判定(⑪ 報告三段都看 · PS 自驗只驗本輪的冊 · 成功看本輪 ⑧ 完成燈)· v0129 一鍵全流程(依 MAIN 登記紀錄定位程式夾 · U/I「驗證過的輸出」· 啟動器 ⑪ 背景獨立驗證寫回 U/I · 一格整列拆開 · 重複列只留一筆 · 表頭列移出 · 段落標題同一欄 · 驗證器 v0102):① CPU / DRAM → ② PS 加速器 → ③ 取得 v0129(GitHub 分支 · SHA-256 驗證 · 舊版留備份)→ ③b 定位 VRN-2 程式夾(VIA 根 · MAIN 成功紀錄 · VIA_ROOT · 倉裡找)→ ④ 執行(啟動器 ①~⑪ · 完成後自動上船 · 驗證寫回後開 U/I)→ ⑤ 摘要 · 印驗證摘要(啟動器沒驗到才自己驗)→ NEXT =====
  # 只增不減:不刪任何檔(舊啟動器改名備份)· 不動別的系統(VCGC / VDF)的檔 · 驗證只讀 · 報告寫在 VIA_Reports\vrn2\verify_independent
  $R      = if ($env:VRN2_ROOT)  { $env:VRN2_ROOT }  else { "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics" }   # VIA 根
  $Pk     = if ($env:VRN2_PACKAGE) { $env:VRN2_PACKAGE } else { Join-Path $env:USERPROFILE 'Downloads\VRN2_Closeout_v0146' }             # 套件夾(啟動器 v0146 + 私有 runtime v0142 + 橋 · 不是單一檔)
  $A      = Join-Path $Pk 'ActivateVRN-2_v0146.py'                                                                                        # 啟動器位置(套件內)
  $Br     = 'claude/optimistic-goodall-yhalc5'                                    # v0146 發行所在的 GitHub 分支(只讀取 · 不切換分支 · 讀不到 → 改讀 main)
  $RelP   = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0146'     # 發行夾(repo 根起算)
  $Want   = '67fde9888e9f466d8f3ccf45f2afd2a2d4873e3d82d66493d5ee65202916bb96'   # VRN2_Closeout_v0146.zip SHA-256(套件 · 內含啟動器 v0146 + runtime v0146 清單 = v0145 + Workbench v0102 · 處理器 v0109 · SSOTSync v0101 · HistoryAlign · DataIntegrate · ConsensusJoin · 提案冊 · 共識引擎 v0120)
  $NoPush = $false        # $true = 只實測不上船
  $Verify = $true         # 啟動器 ⑪ 沒驗到(例:舊版 / 中斷)時 PS 自己用落地的驗證器驗(只讀)
  $LArgs  = @(); if ($env:VRN2_LAUNCHER_ARGS) { $LArgs = $env:VRN2_LAUNCHER_ARGS -split ' ' }   # 例:--no-install
  if ($env:VRN2_SOURCE) { $LArgs += @('--source', $env:VRN2_SOURCE) }                        # v0142 直接指定來源夾(例:C:\測試樣本報告)· 沒設就用 U/I 選的 / VRN2_SSOT / 預設
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
  $t0 = Get-Date; $tmp = Join-Path ([IO.Path]::GetTempPath()) ("vrn2_v0146_" + $t0.ToString('yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  function Say($lamp, $msg) { $c = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; GRAY = 'DarkGray' }[$lamp]; Write-Host ("[{0}] {1}" -f $lamp, $msg) -ForegroundColor $c }
  $me = Get-Process -Id $PID; $prio0 = $me.PriorityClass; $via0 = $env:VIA_ROOT; $vrn0 = $env:VRN2_ROOT
  try {
    # ① 第一步:CPU / DRAM(CPU 閒 <60% → 本視窗升「高於標準」· 子行程繼承 · 結束還原)+ 釋放記憶體
    $cpu = $null; $ram = $null
    try { $cpu = [int](Get-CimInstance Win32_Processor -ErrorAction Stop | Measure-Object LoadPercentage -Average).Average } catch { }
    try { $ram = [math]::Round((Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).FreePhysicalMemory / 1MB, 1) } catch { }
    if ($cpu -ne $null -and $cpu -lt 60) { try { $me.PriorityClass = 'AboveNormal' } catch { } }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    Say GREEN ("① CPU / DRAM · CPU {0} · 可用 RAM {1} · 優先權 {2} → {3}" -f $(if ($cpu -ne $null) { "$cpu%" } else { '量不到' }), $(if ($ram -ne $null) { "$ram GB" } else { '量不到' }), $prio0, (Get-Process -Id $PID).PriorityClass)
    # ② PS 加速器(找不到不影響)
    $m = [IO.Path]::Combine($R, 'supportive modules', 'VIA_PS_Accel_Module.ps1')
    if (Test-Path -LiteralPath $m) { . $m; Say GREEN "② PS 加速器已接 · $m" } else { Say GRAY "② 找不到 VIA_PS_Accel_Module.ps1(不影響)" }
    if (-not (Test-Path -LiteralPath $R)) { Say RED "找不到 VIA 根 $R"; $global:LASTEXITCODE = 1; return }
    $py = if ($env:VRN2_PY) { $env:VRN2_PY } else { (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source }
    if (-not $py) { Say RED "找不到 python(不要用 WindowsApps 的假 python)"; $global:LASTEXITCODE = 1; return }
    # 每個 python 指令都先接正本加速器(VeritasCeleritas 最新版號 · 找不到 = 不改行為)
    $wrap = Join-Path $tmp 'vrn2_accel_run.py'
    [IO.File]::WriteAllText($wrap, @'
# [VIA:ACCEL-BRIDGE:v0111] 先接正本加速器(找不到 = 不改行為)再執行目標 .py
import re, runpy, sys
from pathlib import Path
root, target = Path(sys.argv[1]), sys.argv[2]
sys.argv = [target] + sys.argv[3:]
sup = root / "supportive modules"
c = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")), key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
try:
    if c:
        sys.path.insert(0, str(c[-1].parent))
        __import__(c[-1].stem)
except Exception:  # noqa: BLE001
    pass
sys.path.insert(0, str(Path(target).resolve().parent))
runpy.run_path(target, run_name="__main__")
'@, (New-Object Text.UTF8Encoding $false))
    function Q($s) { '"' + $s + '"' }
    # ③ 取得套件 v0142:本機套件夾的 VRN2_Closeout_v0146.zip 雜湊對(且啟動器在)→ 直接用;不是 → 從 GitHub 分支(讀不到 → main)讀發行夾(git fetch + git archive · 不切換分支)· 套件雜湊 + 套件內逐檔雜湊都對才解壓 · 舊套件夾改名備份
    $zk = Join-Path $Pk 'VRN2_Closeout_v0146.zip'; $jk = Join-Path $Pk 'VRN2_Release_v0146.json'
    $have = if ((Test-Path -LiteralPath $zk) -and (Test-Path -LiteralPath $A)) { (Get-FileHash -LiteralPath $zk -Algorithm SHA256).Hash.ToLower() } else { '' }
    $rel = $null; $nchk = 0; $b = ''
    if ($have -eq $Want) {
      # Codex #566:快路徑也逐檔核對 —— 把已驗過的本機 zip 解到暫存,套件夾每個檔的雜湊都要和它一樣;缺檔 / 不同(被改 · 壞掉)→ 當作沒有套件,從本機這份 zip 重新解壓(舊夾改名備份)
      $chk = Join-Path $tmp 'chk'; Expand-Archive -LiteralPath $zk -DestinationPath $chk -Force
      $src = Join-Path $chk 'VRN2_Closeout_v0146'
      $bad = @(Get-ChildItem -LiteralPath $src -File | Where-Object { $fp = Join-Path $Pk $_.Name; -not (Test-Path -LiteralPath $fp) -or ((Get-FileHash -LiteralPath $fp -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash) } | ForEach-Object { $_.Name })
      $nchk = @(Get-ChildItem -LiteralPath $src -File).Count
      if ($bad.Count -gt 0) {
        Say YELLOW ("③ 本機套件夾有 {0} 個檔與已驗證的 zip 不同或不在({1})→ 不用它,從本機這份 zip 重新解壓" -f $bad.Count, ($bad -join ' · '))
        $have = ''
        if (Test-Path -LiteralPath $jk) { $rel = Join-Path $tmp 'rel'; New-Item -ItemType Directory -Force -Path $rel | Out-Null; Copy-Item -LiteralPath $zk -Destination (Join-Path $rel 'VRN2_Closeout_v0146.zip') -Force; Copy-Item -LiteralPath $jk -Destination (Join-Path $rel 'VRN2_Release_v0146.json') -Force }
      }
    }
    $top = $null; if (Get-Command git -ErrorAction SilentlyContinue) { $top = (git -C $R rev-parse --show-toplevel 2>$null) }; if ($top) { $top = "$top".Trim() }
    if ($top -and $have -ne $Want -and -not $rel) {
      foreach ($b in $Br, 'main') {
        $ok = $false
        foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }
        if (-not $ok) { continue }
        $z = Join-Path $tmp 'vrn2_release_v0146.zip'
        git -C $top archive --format=zip -o $z "origin/${b}:$RelP" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $rel = Join-Path $tmp 'rel'; Expand-Archive -LiteralPath $z -DestinationPath $rel -Force; break }
      }
    }
    if ($have -ne $Want) {
      if (-not $rel) { Say RED "③ 本機套件不是 v0146,且讀不到 GitHub 分支 $Br 或 main(網路 / git)· 請手動下載 VRN2_Closeout_v0146.zip 解壓到 $Pk"; $global:LASTEXITCODE = 1; return }
      $zl = Join-Path $rel 'VRN2_Closeout_v0146.zip'; $mj = Join-Path $rel 'VRN2_Release_v0146.json'
      if (-not ((Test-Path -LiteralPath $zl) -and (Test-Path -LiteralPath $mj))) { Say RED "③ GitHub 分支的發行夾 $RelP 缺 VRN2_Closeout_v0146.zip / VRN2_Release_v0146.json · 不使用"; $global:LASTEXITCODE = 1; return }
      $man = Get-Content -Raw -Encoding UTF8 -LiteralPath $mj | ConvertFrom-Json
      $got = (Get-FileHash -LiteralPath $zl -Algorithm SHA256).Hash.ToLower()
      if ($got -ne $Want -or $man.package.sha256 -ne $Want) { Say RED "③ 下載的套件雜湊不對($got)· 不使用"; $global:LASTEXITCODE = 1; return }
      Expand-Archive -LiteralPath $zl -DestinationPath (Join-Path $tmp 'l') -Force
      $new = [IO.Path]::Combine($tmp, 'l', 'VRN2_Closeout_v0146')
      $pm = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $new 'PACKAGE_SHA256.json') | ConvertFrom-Json
      foreach ($f in $pm.files) { $fp = Join-Path $new $f.path; if (-not (Test-Path -LiteralPath $fp) -or ((Get-FileHash -LiteralPath $fp -Algorithm SHA256).Hash.ToLower() -ne $f.sha256)) { Say RED "③ 套件內 $($f.path) 雜湊不對 · 不使用"; $global:LASTEXITCODE = 1; return } }
      if (-not (Test-Path -LiteralPath $new -PathType Container) -or -not (Test-Path -LiteralPath (Join-Path $new 'ActivateVRN-2_v0146.py'))) { Say RED "③ 套件解壓後找不到 ActivateVRN-2_v0146.py · 不使用"; $global:LASTEXITCODE = 1; return }
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Pk) | Out-Null
      if (Test-Path -LiteralPath $Pk) { $bak = $Pk + '_' + $t0.ToString('yyyyMMdd_HHmmss') + '.bak'; Move-Item -LiteralPath $Pk -Destination $bak; Say GREEN "③ 舊套件夾已改名備份 → $bak" }
      Copy-Item -LiteralPath $new -Destination $Pk -Recurse -Force
      Copy-Item -LiteralPath $zl -Destination $zk -Force
      Copy-Item -LiteralPath $mj -Destination $jk -Force
      Say GREEN "③ 套件 v0146 就位(SHA-256 $($Want.Substring(0,12)) · 套件內 $(@($pm.files).Count) 檔逐檔核對相符 · 來源 $(if ($b) { "GitHub $b" } else { '本機已驗證的 zip' }))→ $Pk"
    } else { Say GREEN "③ 本機已是 v0146 套件(SHA-256 $($Want.Substring(0,12)) · 套件夾 $nchk 檔與已驗證的 zip 逐檔相符)· $Pk" }
    # ③b 定位 VRN-2 程式夾(BEGIN):啟動器先看環境變數 VIA_ROOT · 先確認那裡真的有 functional modules\VRN · 沒有就找 · 找到才帶給啟動器(只在這個視窗 · 結束還原)
    $hasV = { param($p) $p -and (Test-Path -LiteralPath ([IO.Path]::Combine($p, 'functional modules', 'VRN')) -PathType Container) }
    $root = $null
    $how = 'VIA 根'
    if (& $hasV $R) { $root = $R }
    else {                                                                   # MAIN VRN-2 SystemManager 上次成功時寫的紀錄:鎖檔在 VRN\registry\ → 程式夾
      $sj = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2', 'VRN2_Success_latest.json')
      if (Test-Path -LiteralPath $sj) {
        try { $lk = (Get-Content -Raw -Encoding UTF8 -LiteralPath $sj | ConvertFrom-Json).lock; if ($lk) { $vv = Split-Path -Parent (Split-Path -Parent $lk); if (Test-Path -LiteralPath $vv -PathType Container) { $root = Split-Path -Parent (Split-Path -Parent $vv); $how = "MAIN 成功紀錄 $sj" } } } catch { }
      }
    }
    if ($root) { }
    elseif ($via0) { $root = @($via0, [IO.Path]::Combine($via0, 'VeritasIntelligenceAnalytics')) | Where-Object { & $hasV $_ } | Select-Object -First 1; if ($root) { $how = '環境變數 VIA_ROOT' } }
    if (-not $root) {
      $base = if ($top) { $top } else { Split-Path -Parent $R }
      $hit = @(Get-ChildItem -LiteralPath $base -Recurse -Depth 4 -Directory -Filter 'VRN' -ErrorAction SilentlyContinue | Where-Object { $_.Parent.Name -eq 'functional modules' -and $_.FullName -notmatch '_archive|_quarantine' -and @(Get-ChildItem -LiteralPath $_.FullName -Filter 'VRN_SystemManager_v*.py' -ErrorAction SilentlyContinue).Count -gt 0 })
      if ($hit.Count -ge 1) {
        $root = $hit[0].Parent.Parent.FullName; $how = "倉裡找到($base)"
        if ($hit.Count -gt 1) { Say YELLOW ("③b 找到 {0} 個 functional modules\VRN · 用第一個 {1}(其他:{2})" -f $hit.Count, $root, (($hit | Select-Object -Skip 1 | ForEach-Object { $_.FullName }) -join ' · ')) }
      }
    }
    if (-not $root) {
      Say RED ("③b 找不到 VRN-2 程式夾 functional modules\VRN · VIA 根 {0}(存在 {1})· 環境變數 VIA_ROOT = {2}" -f $R, (Test-Path -LiteralPath $R), $(if ($via0) { $via0 } else { '未設' }))
      if (Test-Path -LiteralPath $R) { Say GRAY ("    VIA 根底下的夾:{0}" -f ((Get-ChildItem -LiteralPath $R -Directory -ErrorAction SilentlyContinue | Select-Object -First 30 | ForEach-Object { $_.Name }) -join ' · ')) }
      if ($top) {
        $brn = git -C $top branch --show-current 2>$null
        $ntr = @(git -C $R ls-files -- 'functional modules/VRN' 2>$null).Count
        Say GRAY ("    git:目前分支 {0} · git 記錄裡 functional modules\VRN 有 {1} 個檔(有記錄但夾不在 = 被移走 / 刪除 / 換了分支)" -f $brn, $ntr)
      }
      Say YELLOW "③b 交給啟動器 v0146 依 MAIN 登記紀錄再找一次(它會印出查過的地方)"
    }
    else {
    if ($root -ne $R) { Say YELLOW ("③b VRN-2 程式夾不在 {0} → 改用 {1}(輸出 / 報告也讀這裡)" -f $R, $root); $R = $root }
    if ($via0 -and $via0 -ne $root) { Say YELLOW ("③b 環境變數 VIA_ROOT 原本是 {0}(那裡沒有 functional modules\VRN 或不是這個 VIA 根)→ 這次改成 {1}(只在這個視窗 · 結束還原)" -f $via0, $root) }
    $env:VIA_ROOT = $root; $env:VRN2_ROOT = $root                                                 # v0142:啟動器先看 VRN2_ROOT(私有 runtime 落在 functional modules\VRN2)
    Say GREEN ("③b VRN-2 程式夾 {0}(來源 {1})· 私有 runtime → {2}" -f [IO.Path]::Combine($root, 'functional modules', 'VRN'), $how, [IO.Path]::Combine($root, 'functional modules', 'VRN2'))
    }
    # ③b(END)
    # ④ 執行(啟動器自己做 ①~⑪:CPU/DRAM · 定位 · 船包補回 · 落地 v0231→v0239 + 獨立驗證器 · 補裝 · 加速器 · 平行段 · 登記 · 測試 · vrn2 --run · ⑪ 背景驗證 ∥ 完成判定 · 上船 · 封存 · 驗證寫回 U/I → 開 U/I)
    if ($NoPush) { $env:VIA_VRN2_NO_PUSH = '1' } else { Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue }
    Write-Host ("[計] VRN-2 一鍵 v0146 · ActivateVRN-2 v0146(套件 · 私有 runtime v0146 = v0145 + Workbench v0102(雙語表頭 · 靠上 · 百萬台幣千分位 · 自動縮放 · 輸出夾格 · 去重矩陣 + 引擎狀態)· 處理器 v0109(vrn2://integrate)· SSOTSync v0101(提案冊)· HistoryAlign v0100 · DataIntegrate v0100 · ConsensusJoin v0100 · 共識引擎 v0120;⑥e 市場擷取(借共用 MarketFetch)· ⑥f 共識 Combined · ⑬b 歷史對齊 · ⑬c 舊資料庫整合掃描;管理器 v0255 · OutputStore v0100 · 摘要器 v0117 · 驗證器 v0110 · 原文核對 v0104;v0144 = 輸出位置 window I/O · DuckDB 增量 Parquet 庫 · SSOT-ID 協作;v0143 = 單機閘 · 上限 · ⑫b 補放)· {0}" -f $(if ($NoPush) { '只實測不上船' } else { '收尾驗證(套件啟動器不上船 · ⑨ 灰)' })) -ForegroundColor Yellow
    $noOpen0 = $env:VIA_NO_OPEN; if ($env:VRN2_NO_UI -eq '1') { $env:VIA_NO_OPEN = '1' } else { Remove-Item Env:\VIA_NO_OPEN -ErrorAction SilentlyContinue }   # v0142:VIA 設定檔的 VIA_NO_OPEN=1 會讓啟動器不開 U/I → 一鍵要跳出 U/I,先拿掉(結束還原)· $env:VRN2_NO_UI = 1 才不開
    & $py $A @LArgs
    $rcL = $LASTEXITCODE
    if ($null -ne $noOpen0) { $env:VIA_NO_OPEN = $noOpen0 } else { Remove-Item Env:\VIA_NO_OPEN -ErrorAction SilentlyContinue }
    # ⑤ 摘要 · 獨立驗證:啟動器 ⑪ 本輪已驗(報告時間 ≥ 開始)→ 直接用;沒有 → 輸出冊是本輪寫的(≥ 開始 - 5 秒 · 同啟動器 ⑪)才由 PS 用落地的驗證器自己驗(與摘要同時跑 · 只讀 · 判決也寫回 U/I)· 舊冊不驗
    $v2 = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2'); $od = Join-Path $v2 'output'
    $fdj = Join-Path $od 'VRN2_FinancialData_latest.json'
    $fdNew = (Test-Path -LiteralPath $fdj) -and ((Get-Item -LiteralPath $fdj).LastWriteTime -ge $t0.AddSeconds(-5))
    $vp = $null; $vd = Join-Path $v2 'verify_independent'; $vr = $null; $vlog = $null
    $lv = if (Test-Path -LiteralPath $vd) { Get-ChildItem -LiteralPath $vd -Filter 'VRN2_IndependentVerify_*.json' | Where-Object { $_.LastWriteTime -ge $t0.AddSeconds(-5) } | Sort-Object LastWriteTime | Select-Object -Last 1 } else { $null }
    if ($lv) { $vr = $lv.FullName; $vlog = $vr -replace '\.json$', '.txt' }
    elseif ($Verify -and $fdNew) {
      $vdir = @([IO.Path]::Combine($R, 'functional modules', 'VRN2'), [IO.Path]::Combine($R, 'functional modules', 'VRN')) | Where-Object { Test-Path -LiteralPath $_ -PathType Container } | Select-Object -First 1
      $ver = if ($vdir) { Get-ChildItem -LiteralPath $vdir -Filter 'VRN2_IndependentVerifier_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1 } else { $null }
      if ($ver) {
        New-Item -ItemType Directory -Force -Path $vd | Out-Null
        $vr = Join-Path $vd ("VRN2_IndependentVerify_{0}.json" -f $t0.ToString('yyyyMMdd_HHmmss'))
        $vlog = $vr -replace '\.json$', '.txt'
        $vp = Start-Process -FilePath $py -ArgumentList @((Q $wrap), (Q $R), (Q $ver.FullName), (Q $od), (Q (Join-Path $v2 'scope_in')), (Q $vr), '--ui', (Q (Join-Path $v2 'VRN2_UI_latest.html'))) -NoNewWindow -PassThru -RedirectStandardOutput $vlog -RedirectStandardError ($vlog + '.err')
        Say GRAY "啟動器本輪沒有驗證報告 → PS 用 $($ver.Name) 自己驗本輪的輸出冊(只讀 · 判決寫回 U/I)"
      }
    }
    elseif ($Verify -and (Test-Path -LiteralPath $fdj)) { Say YELLOW "獨立驗證不跑 · 輸出冊不是本輪寫的($((Get-Item -LiteralPath $fdj).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')) · ⑦ 沒跑完)· 不驗舊冊、不把舊冊判決寫進 U/I" }
    $sum = Join-Path $tmp 'vrn2_sum.py'
    [IO.File]::WriteAllText($sum, @'
import json, sys, datetime
from collections import Counter
from pathlib import Path
v2, t0 = Path(sys.argv[1]), datetime.datetime.fromisoformat(sys.argv[2])
def j(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
c = j(v2 / "VRN2_Completion_latest.json") or {}
fresh = bool(c.get("ts")) and datetime.datetime.fromisoformat(c["ts"]) >= t0 - datetime.timedelta(seconds=5)
lamp = "GREEN" if fresh and c.get("verdict") == "完成" and not c.get("red") else "RED"
print("%s|⑧ 完成判定 · %s · 紅 %s · 黃 %s · %s · %s" % (lamp, c.get("verdict", "?"), c.get("red", "?"), c.get("yellow", "?"), c.get("manager", "?"), "本輪" if fresh else "不是本輪寫的(⑦ 沒跑完)"))
for it in c.get("items") or []:
    if it.get("lamp") in ("RED", "YELLOW"):
        print("%s|   %s · %s" % (it["lamp"], it["name"][:24], it["detail"][:150]))
od = v2 / "output"
b, f, s, r = (j(od / ("VRN2_%s_latest.json" % n)) or [] for n in ("BasicInfo", "FinancialData", "Summary", "Rejected"))
sub = [x for x in f if x.get("SUBCOL")]
rc = Counter(str(x.get("REASON", "")).split("(")[0][:10] for x in r)
pq = sorted(p.name for p in od.glob("VRN2_*_latest.parquet"))
st = list((od / "_stale").glob("*.parquet")) if (od / "_stale").is_dir() else []
_fd = od / "VRN2_FinancialData_latest.json"
_new = _fd.exists() and datetime.datetime.fromtimestamp(_fd.stat().st_mtime) >= t0 - datetime.timedelta(seconds=5)
print(("GREEN|" if _new else "YELLOW|(不是本輪寫的舊冊)") + "輸出冊 · 基本資料 %d · 年度數據 %d 筆(子欄 %d · 依子表頭更正 %d)· 一標題四重點 %d · 剔除冊 %d(%s)" % (len(b), len(f), len(sub), sum("更正" in (x.get("VERIFY") or "") for x in sub), len(s), len(r), " · ".join("%s %d" % kv for kv in rc.most_common(4))))
print("%s|Parquet %d / 4%s" % ("GREEN" if len(pq) == 4 else "YELLOW", len(pq), (" · 舊檔移到 output\\_stale %d 個(本輪沒寫 Parquet · 缺 pandas / pyarrow)" % len(st)) if st else ""))
import hashlib, re as _re
up = v2 / "VRN2_UI_latest.html"
pg = up.read_text(encoding="utf-8") if up.exists() else ""
h = hashlib.sha256()
for x in f:
    h.update(("\x1f".join(str(x.get(k, "")) for k in ("FILENAME", "PAGE", "TABLE", "ITEM", "PERIOD", "SUBCOL", "VALUE")) + "\x1e").encode("utf-8"))
m = _re.search(r'window\.VRN2_IV=\{"ver":"[^"]*","ts":"([^"]*)","fp":"([0-9a-f]{16})"', pg)
tab = "id='vrn2vo-h'" in pg
if not tab:
    print("YELLOW|U/I %s · 沒有「驗證過的輸出」分頁(管理器不是 v0237 以後)" % up)
elif m and m.group(2) == h.hexdigest()[:16]:
    print("GREEN|U/I %s · 「驗證過的輸出」分頁 · 獨立驗證判決已寫回(%s · 冊指紋 %s 相同)" % (up, m.group(1), m.group(2)))
else:
    print("YELLOW|U/I %s · 「驗證過的輸出」分頁 · 獨立驗證%s" % (up, "結果是別一輪的(指紋不同)" if m else "尚未寫回"))
cl = j(v2 / "VRN2_Closeout_v0146.json") or {}
if cl:
    ps_ = cl.get("passes") or []
    q = cl.get("source_quotes") or {}
    print("%s|⑧b 收尾收據 v0146 · rc %s · 跑了 %d 輪(%s)· 四點原文核對 %s %s · 輸出缺項 %d" % ({0: "GREEN", 2: "YELLOW"}.get(cl.get("rc"), "RED"), cl.get("rc"), len(ps_), " / ".join(str(p.get("idempotence", "")) for p in ps_), q.get("verdict"), q.get("counts"), len(cl.get("output_gaps") or [])))
    for g in (cl.get("output_gaps") or [])[:6]:
        print("YELLOW|   缺項 · %s" % json.dumps(g, ensure_ascii=False)[:150])
    for st_ in cl.get("steps") or []:
        if st_.get("lamp") == "RED":
            print("RED|   紅燈步驟 · %s · %s" % (str(st_.get("step"))[:30], str(st_.get("detail"))[:140]))
else:
    print("YELLOW|⑧b 沒有收尾收據 VRN2_Closeout_v0146.json(啟動器 v0146 沒跑完 · 或單機閘拒跑:看上面 [RED] 單機閘 那行)")
wb = cl.get("workbench") or {}
if wb:
    print("%s|Workbench U/I v0102 · %s" % ("GREEN" if wb.get("lamp") == "GREEN" else "YELLOW", (wb.get("path") or wb.get("detail") or "")[:150]))
else:
    print("YELLOW|Workbench U/I 沒渲染(收據沒有 workbench 欄)")
st_ = cl.get("output_store") or {}
if st_.get("lamp") == "GRAY":
    print("GRAY|⑬ 輸出位置未設定 · 輸出留在 VIA_Reports\\vrn2\\output(Workbench「選擇輸出夾…」或 $env:VRN2_OUTPUT_DIR)")
elif st_:
    print("%s|⑬ 輸出位置 %s · 增量庫 %s · 新檔 %d / 已知 %d · 追加 %s · parquet %d%s" % ({"GREEN": "GREEN", "YELLOW": "YELLOW"}.get(st_.get("lamp"), "RED"), st_.get("output_dir", ""), st_.get("store_engine", ""), len(st_.get("new_files") or []), len(st_.get("known_files") or []), " / ".join("%s %s" % (k, v) for k, v in (st_.get("appended") or {}).items()), len(st_.get("parquet_files") or []), (" · " + st_["why"]) if st_.get("why") else ""))
ss_ = cl.get("ssot_sync") or {}
if ss_:
    print("%s|⑤b SSOT-ID 核號同步 · %s" % ({"GREEN": "GREEN", "YELLOW": "YELLOW", "GRAY": "GRAY"}.get(ss_.get("lamp"), "YELLOW"), (ss_.get("detail") or "")[:200]))
for k_, lb_ in (("market", "⑥e 市場擷取(TWSE / TPEX / Yahoo)"), ("consensus", "⑥f 共識合併(FactSet / YFinance → Combined)"), ("history_align", "⑬b 歷史對齊(歷史覆蓋預估 · 刪除區)"), ("integrate", "⑬c 舊資料庫整合掃描")):
    x_ = cl.get(k_) or {}
    if x_:
        print("%s|%s · %s" % ({"GREEN": "GREEN", "YELLOW": "YELLOW", "GRAY": "GRAY"}.get(x_.get("lamp"), "YELLOW"), lb_, (x_.get("detail") or "")[:220]))
    else:
        print("GRAY|%s · 收據沒有這一欄(啟動器不是 v0146)" % lb_)
pt_ = j(v2 / "VRN2_Phase_Timing_latest.json") or {}
if pt_:
    print("GRAY|階段耗時(秒 · 管理器 %s)· %s · 其他 %.0f · 總 %.0f" % (pt_.get("manager", ""), " · ".join("%s %.0f" % (p_.get("phase", ""), p_.get("seconds", 0)) for p_ in (pt_.get("phases") or [])) or "無", pt_.get("untimed_s", 0), pt_.get("total_s", 0)))
else:
    print("GRAY|階段耗時 · 沒有 VRN2_Phase_Timing_latest.json(管理器不是 v0255 或 ⑦ 沒跑完)")
idm = j(v2 / "IDEMPOTENCE_latest.json") or {}
if idm:
    print("%s|冪等閘 · %s · %s · %s" % ("GREEN" if idm.get("lamp") == "GREEN" else "RED", idm.get("classification"), " · ".join(str(f.get("file", ""))[:24] for f in idm.get("files") or []), (idm.get("method") or "")[:70]))
tm = j(v2 / "tools" / "VRN2_ToolManifest_v0100.json") or {}
if tm.get("offers"):
    print("GREEN|② 借出工具冊 %s · %s" % (v2 / "tools" / "VRN2_ToolManifest_v0100.json", " · ".join("%s %s" % (t.get("id"), "能用" if t.get("ready") else "不能用") for t in tm["offers"])))
else:
    print("YELLOW|② 借出工具冊沒寫(看啟動器 ② 那行)")
pb = v2 / "pivot" / "VRN2_Pivot_Borrow_latest.json"
pj = j(pb) or {}
if pj and datetime.datetime.fromtimestamp(pb.stat().st_mtime) >= t0 - datetime.timedelta(seconds=5):
    pc = pj.get("counts") or {}
    print("GREEN|⑫ PIVOT 資料庫(借用 %s %s · sha256 %s)· 事實 %s/%s · 年度 %s 列 · 衝突 %s · %s" % (
        (pj.get("borrow") or {}).get("from", "?"), (pj.get("borrow") or {}).get("id", "?"), str((pj.get("borrow") or {}).get("sha256", ""))[:12],
        pc.get("kept"), pc.get("facts"), pc.get("pivot_report_annual"), pc.get("conflicts"), v2 / "pivot" / "VRN_Pivot_v0100.html"))
else:
    print("GRAY|⑫ PIVOT 資料庫本輪沒寫(VRN-1 的工具借不到或不借 · VRN-2 照常 · 看啟動器 ⑫ 那行)")
'@, (New-Object Text.UTF8Encoding $false))
    $sumOut = & $py $wrap $R $sum $v2 $t0.ToString('yyyy-MM-ddTHH:mm:ss') 2>&1
    foreach ($ln in $sumOut) { $p = "$ln" -split '\|', 2; if ($p.Count -eq 2) { Say $p[0] $p[1] } else { Write-Host $ln } }
    # 上船狀態:GitHub 上的 VRN-2 船包是否和本機相同(v0125 起只送 VRN-2 船包 · 本機別的提交不代推)
    if ($top) {
      $u = git -C $R rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
      if ($NoPush) { Say GRAY "⑨ 這次不上船" }
      elseif (-not $u) { Say YELLOW "⑨ 目前分支沒有上游(看不出 GitHub 上的船包)" }
      else {
        $ub = "$u" -split '/', 2; git -C $R fetch -q $ub[0] $ub[1] 2>&1 | Out-Null
        git -C $R diff --quiet $u HEAD -- docs/handoff/ai/vrn2_ship docs/handoff/ai/VRN2_Handover_latest.md 2>$null
        $same = ($LASTEXITCODE -eq 0)
        $ahead = git -C $R rev-list --count "$u..HEAD" -- . ':(exclude)docs/handoff/ai/vrn2_ship' ':(exclude)docs/handoff/ai/VRN2_Handover_latest.md' ':(exclude)docs/handoff/ai/VRN2_Handover_v0147.md' 2>$null
        Say $(if ($same) { 'GREEN' } else { 'YELLOW' }) ("⑨ GitHub {0} 上的 VRN-2 船包 {1}" -f $u, $(if ($same) { '與本機相同(已上船)' } else { '與本機不同(沒推上去 · 看上面 ⑨ 那行的原因)' }))
        if ("$ahead" -match '^\d+$' -and [int]$ahead -gt 0) { Say GRAY ("本機另有 {0} 個動到別的檔的提交沒推到 {1}(不是 VRN-2 的 · VRN-2 不代推)" -f $ahead, $u) }
      }
    }
    $vok = $null
    if ($vp) {
      if (-not $vp.WaitForExit(1800000)) { try { $vp.Kill() } catch { }; Say YELLOW "獨立驗證超過 30 分鐘 · 已停(不影響輸出)"; $vr = $null }
      else { $vok = ($vp.ExitCode -eq 0) }
    } elseif ($vr) {
      # 啟動器 ⑪ 的報告:照驗證器自己的結束碼規則看三段(基本資料 / 一標題四重點 任一欄 FAIL · 年度數據錯值列 fin_bad)+ 日誌的 [FAIL] 行 · 讀不到 = 沒過
      $vok = $false
      try {
        $vj = Get-Content -Raw -Encoding UTF8 -LiteralPath $vr | ConvertFrom-Json
        if (-not $vj.version -or $null -eq $vj.basic -or $null -eq $vj.summary -or $null -eq $vj.fin_bad) { throw '報告缺欄位' }
        $nf = (@($vj.basic) + @($vj.summary) | Where-Object { $_ } | ForEach-Object { $_.checks.PSObject.Properties | Where-Object { "$($_.Value)" -like 'FAIL*' } } | Measure-Object).Count
        $nb = ($vj.fin_bad | Measure-Object).Count
        $lt = Get-Content -Encoding UTF8 -LiteralPath $vlog -ErrorAction SilentlyContinue
        $vok = ($nf -eq 0) -and ($nb -eq 0) -and -not ($lt -match '^\s+\[FAIL\]') -and -not ($lt -match '^\[驗證\] 年度數據 .*(FAIL|MISALIGNED|BADVALUE|BADITEM|SUBFAIL|TRANSFAIL|DUPKEY|QTRCOL|DUPROW|HDRVAL|SECFAIL)')
        if (-not $vok) { Say YELLOW ("獨立驗證報告:基本資料 / 一標題四重點 FAIL 欄 {0} · 年度數據錯值 {1} 筆 · {2}" -f $nf, $nb, $vr) }
      } catch { Say YELLOW "獨立驗證報告讀不到或不完整($vr · $($_.Exception.Message))· 當作沒過" }
    }
    if ($vr -and (Test-Path -LiteralPath $vlog)) {
      $vt = Get-Content -Encoding UTF8 -LiteralPath $vlog
      $ve = if (Test-Path -LiteralPath ($vlog + '.err')) { Get-Content -Encoding UTF8 -LiteralPath ($vlog + '.err') | Where-Object { $_ -notmatch 'FontBBox' } } else { @() }
      if (($ve -join ' ') -match 'ModuleNotFoundError') { $vok = $null; Say GRAY "獨立驗證跳過 · 缺 pdfplumber / pypdfium2(不補裝)" }
      else {
        foreach ($ln in ($vt | Where-Object { $_ -match '^\[驗證\]' })) { Say $(if ($vok) { 'GREEN' } else { 'YELLOW' }) "獨立驗證 $ln" }
        foreach ($ln in ($vt | Where-Object { $_ -match '^\s+\[FAIL\]' } | Select-Object -First 8)) { Say YELLOW $ln.Trim() }
        Say $(if ($vok) { 'GREEN' } else { 'YELLOW' }) ("獨立驗證({0}){1} · 報告 {2}" -f $(if ($lv) { '啟動器 ⑪' } else { 'PS 自己驗' }), $(if ($vok) { ' 錯值 0' } else { ' 有待核對 → U/I「驗證過的輸出」看 ✗ 格(先看原文再判 · 驗證器也要被驗)' }), $vr)
        $dg = "$vr.digest.txt"
        if (Test-Path -LiteralPath $dg) {
          Write-Host "──── 驗證摘要(貼給 AI 只要這份 · 完整在 $dg)────" -ForegroundColor Cyan
          Get-Content -Encoding UTF8 -LiteralPath $dg | Select-Object -First 40 | ForEach-Object { Write-Host $_ }
        }
      }
    } elseif ($Verify -and ($fdNew -or -not (Test-Path -LiteralPath $fdj))) { Say GRAY "獨立驗證跳過 · 啟動器沒驗、也找不到落地的驗證器或輸出冊" }
    # ⑤b 前後端連結檢查(v0142 · Codex #550 修正):HKCU 的 vrn2:// 指令解析成「python」「處理器」兩段 · 處理器要 = 本機 VRN-2 程式夾裡的 VRN2_UIAction_v0108.py(整條路徑 · 檔在;或那一夾有啟動器本輪寫的 VRN2_UIAction_Config.json)· python 檔在 · 第三段是 "%1" · U/I 有「輸入(window I/O)」區塊 · 有輸入紀錄;⑤b 的燈併進最後 NEXT(紅 → 紅 · 黃 → 最多黃)
    function Chk5b($R, $py, $regCmd, $uiTxt, $inp) {
      $norm = { param($p) try { if ($p) { [IO.Path]::GetFullPath($p).TrimEnd('\', '/').ToLowerInvariant() } else { '' } } catch { '' } }
      $hExp = [IO.Path]::Combine($R, 'functional modules', 'VRN2', 'VRN2_UIAction_v0108.py')   # v0144:處理器 v0108 在私有 runtime(v0105 / v0107 是桌機線的 publish 處理器)
      $qa = @([regex]::Matches([string]$regCmd, '"([^"]*)"') | ForEach-Object { $_.Groups[1].Value })
      $regExe = if ($qa.Count -ge 1) { $qa[0] } else { '' }; $regH = if ($qa.Count -ge 2) { $qa[1] } else { '' }
      $u1Ok = [bool]($qa.Count -ge 3 -and $qa[2] -eq '%1')   # Codex #551:少了 "%1"(或被換成固定網址)→ 點按鈕時網址送不到處理器 → 不算接上
      $hIn = [bool]($regH -and (Test-Path -LiteralPath $regH -PathType Leaf))
      $hSame = [bool]($hIn -and ((& $norm $regH) -eq (& $norm $hExp)))
      $hCfg = $false; $cfgP = if ($regH) { Join-Path (Split-Path -Parent $regH) 'VRN2_UIAction_Config.json' } else { '' }
      if ($hIn -and -not $hSame -and ($regH -match '[\\/]VRN2_UIAction_v0109\.py$') -and (Test-Path -LiteralPath $cfgP)) { try { $cf = Get-Content -Raw -Encoding UTF8 -LiteralPath $cfgP | ConvertFrom-Json; $hCfg = ($cf.version -eq 'ActivateVRN-2 v0146') -and ($cf.handler -eq 'VRN2_UIAction_v0108.py') } catch { } }
      $hOk = $hSame -or $hCfg
      $exeOk = [bool]($regExe -and (Test-Path -LiteralPath $regExe -PathType Leaf))
      $samePy = [bool]($exeOk -and $py -and ((& $norm (Split-Path -Parent $regExe)) -eq (& $norm (Split-Path -Parent $py))))
      $blkOk = [bool](($uiTxt -match "id='vrn2-input'") -and ($uiTxt -match '個股報告/訊息') -and ($uiTxt -match '產業報告/展望') -and ($uiTxt -match '其他投資報告') -and ($uiTxt -match 'vrn2://pick\?kind=folder'))
      if ($hOk -and $exeOk -and $u1Ok -and $blkOk) { $l = 'GREEN'; $m = '⑤b 前後端已連結:vrn2:// → {0}({1} · 檔在 · 帶 "%1")· python {2}{3} · U/I 有「輸入(window I/O)」區塊(個股報告/訊息 可選 · 產業報告/展望 / 其他投資報告 尚未開放)' -f $regH, $(if ($hSame) { '整條路徑 = 本機 VRN-2 程式夾' } else { '程式夾 = 啟動器本輪登記的(VRN2_UIAction_Config.json v0146)' }), $regExe, $(if ($samePy) { '' } else { '(與本一鍵用的 python 不同夾 · 能跑就好)' }) }
      elseif ($blkOk -and -not $regCmd) { $l = 'YELLOW'; $m = '⑤b U/I 有輸入區塊,但 vrn2:// 沒註冊(HKCU)→ 按鈕不會有反應;在 Windows 重跑一次啟動器(⑥c 會註冊並讀回核對)或用 $env:VRN2_SOURCE' }
      else { $l = 'RED'; $m = '⑤b 前後端沒接上:vrn2:// 註冊 {0} · U/I 輸入區塊 {1}' -f $(if (-not $regCmd) { '沒有' } elseif (-not $regH) { '解析不出處理器(' + $regCmd + ')' } elseif (-not $hIn) { '指向不存在的 ' + $regH + '(要的是 ' + $hExp + ')' } elseif (-not $hOk) { '指向 ' + $regH + '(舊的 / 搬走的檢出 · 要的是 ' + $hExp + ')' } elseif (-not $exeOk) { 'python 不在 ' + $regExe } elseif (-not $u1Ok) { '少了 "%1"(第三段是 ' + $(if ($qa.Count -ge 3) { $qa[2] } else { '空' }) + ')→ 網址送不到處理器 · 重跑啟動器 ⑥c 重新註冊' } else { '正確' }), $(if ($blkOk) { '在' } else { '不在(重跑啟動器 ⑫b)' }) }
      $mi = if ($inp) { '⑤b 目前輸入 · {0} · {1}({2})· {3}' -f $inp.cat_label, $inp.source_dir, $inp.how, $inp.audit_line } else { if ($l -eq 'GREEN') { $l = 'YELLOW' }; '⑤b 沒有輸入紀錄(VRN2_Input_latest.json)· 啟動器 ②b 沒跑到' }
      [pscustomobject]@{ lamp = $l; msg = $m; inpMsg = $mi; inpOk = [bool]$inp; hOk = $hOk; hSame = $hSame; hCfg = $hCfg; exeOk = $exeOk; u1Ok = $u1Ok; samePy = $samePy; blkOk = $blkOk; regH = $regH; regExe = $regExe }
    }
    $v2p = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2'); $uiP = Join-Path $v2p 'VRN2_UI_latest.html'
    $regCmd = ''; try { $regCmd = [string](Get-ItemProperty -Path 'HKCU:\Software\Classes\vrn2\shell\open\command' -ErrorAction Stop).'(default)' } catch { }
    $uiTxt = if (Test-Path -LiteralPath $uiP) { [IO.File]::ReadAllText($uiP, [Text.Encoding]::UTF8) } else { '' }
    $inpP = Join-Path $v2p 'VRN2_Input_latest.json'; $inp = $null; try { $inp = Get-Content -Raw -Encoding UTF8 -LiteralPath $inpP | ConvertFrom-Json } catch { }
    $c5 = Chk5b $R $py $regCmd $uiTxt $inp
    Say $c5.lamp $c5.msg
    Say $(if ($c5.inpOk) { 'GREEN' } else { 'YELLOW' }) $c5.inpMsg
    # ⑤c U/I 沒跳出來就一鍵代開(啟動器自己的紀錄寫「沒有自動開啟」= 帶了 --no-open 或 VIA_NO_OPEN=1)· $env:VRN2_NO_UI = 1 不開
    $lgA = Get-ChildItem -LiteralPath $v2p -Filter 'ActivateVRN-2_*.log' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    $c5cBad = $false
    $uiNo = [bool]($lgA -and (Select-String -LiteralPath $lgA.FullName -Pattern '沒有自動開啟|開不了' -Quiet))   # 啟動器自己沒開(--no-open / VIA_NO_OPEN)或 os.startfile 失敗(開不了)都要代開
    if ($env:VRN2_NO_UI -eq '1') { Say GRAY '⑤c U/I 不開(VRN2_NO_UI = 1)' }
    elseif ($uiNo -and (Test-Path -LiteralPath $uiP)) { try { Start-Process -FilePath $uiP; Say GREEN ('⑤c U/I 由一鍵開啟(啟動器沒開:--no-open 或 VIA_NO_OPEN=1)· ' + $uiP) } catch { $c5cBad = $true; Say YELLOW ('⑤c U/I 開不了(' + $_.Exception.Message + ')· 請手動開 ' + $uiP) } }
    elseif (-not (Test-Path -LiteralPath $uiP)) { $c5cBad = $true; Say YELLOW ('⑤c 找不到 U/I ' + $uiP) }
    else { Say GRAY '⑤c U/I 已由啟動器開啟' }
    $d = [int]((Get-Date) - $t0).TotalSeconds
    # 成功 = 啟動器 rc 0 且 本輪 ⑧ 完成燈綠(VRN2_Completion_latest.json 是本輪寫的 · 完成 · 紅 0)· 啟動器 v0129 不論 ⑧ 都回 0 → 不能只看 rc
    $ok8 = [bool]($sumOut | Where-Object { "$_" -like 'GREEN|⑧ 完成判定*' } | Select-Object -First 1)
    # v0142(Codex #550 / #559):⑤b 與 ⑤c(U/I 開不了)併進最後的燈 —— 前後端沒接上(紅)→ 紅;vrn2:// 沒註冊 / 沒輸入紀錄(黃)→ 最多黃;只有 ⑧ 綠 + 驗證錯值 0 + ⑤b 綠 才是 GREEN(rc 0)
    $lamp = if ($rcL -eq 1 -or -not $ok8 -or $c5.lamp -eq 'RED') { 'RED' } elseif ($rcL -eq 0 -and $vok -eq $true -and $c5.lamp -eq 'GREEN' -and $c5.inpOk -and -not $c5cBad) { 'GREEN' } else { 'YELLOW' }   # v0142:啟動器 rc 2 = 有待核對(OCR 原文 / 缺項)→ 最多黃
    $msg = @{ RED = $(if ($rcL -eq 1 -or -not $ok8) { 'VRN-2 有紅燈(⑧ 完成判定不是本輪的綠 或 啟動器 rc 1:紅燈步驟 / 四點原文核對 FAIL / 冪等非冪等)· 看 ⑧b 收尾收據與冪等閘那兩行 · 把貼包(≤300 行 · 結尾 NEXT)貼回' } else { 'VRN-2 ⑧ 本輪完成,但 ⑤b 前後端沒接上(vrn2:// 指向別的 / 不存在的處理器 · 或 U/I 沒有輸入區塊)→ 重跑啟動器(⑥c 重新註冊並讀回核對 · ⑫b 重放區塊)· 把 ⑤b 那兩行貼回' })
              GREEN = 'VRN-2 一鍵 v0146 跑完 · ⑧ 本輪完成 · 獨立驗證錯值 0 · U/I 已開在「驗證過的輸出」(最後有 PIVOT 資料庫連結 · 左側「輸入」可選檔案夾 / 檔案 · 目前只開個股報告/訊息)· 把 ⑨ / ⑪ / ⑫ 三行 + 驗證摘要貼回'
              YELLOW = $(if ($c5.lamp -eq 'YELLOW' -and -not $c5.hOk) { 'VRN-2 ⑧ 本輪完成 · 但 vrn2:// 沒註冊(HKCU)→ U/I 按鈕不會動 · 在 Windows 重跑一次啟動器(⑥c 會註冊並讀回核對)或用 $env:VRN2_SOURCE · 把 ⑤b 那兩行貼回' } elseif ($c5cBad) { 'VRN-2 ⑧ 本輪完成 · 但 U/I 開不了(啟動器與一鍵都開不了)→ 請手動開 ' + $uiP } elseif (-not $c5.inpOk) { 'VRN-2 ⑧ 本輪完成 · 但沒有輸入紀錄(②b 沒跑到)→ 把 ②b 那行貼回' } elseif ($vok -eq $false) { 'VRN-2 ⑧ 本輪完成 · 獨立驗證有待核對 → U/I「驗證過的輸出」看 ✗ 格 · 把驗證摘要貼回' } elseif ($rcL -eq 2) { 'VRN-2 ⑧ 本輪完成 · 啟動器 rc 2:有待核對(OCR 原文待核對原圖 / 輸出缺項 / 非 Windows 的 ③)→ 看 ⑧b 收尾收據那行 · 把它貼回' } else { 'VRN-2 ⑧ 本輪完成 · 獨立驗證沒跑完 / 沒寫回 → 把 ⑪ 那行貼回' }) }[$lamp]
    Write-Host ("NEXT: [{0}] {1} · 交接報告 {2} · 啟動器 rc {3} · {4} 秒" -f $lamp, $msg, ([IO.Path]::Combine($R, 'docs', 'handoff', 'ai', 'VRN2_Handover_latest.md')), $rcL, $d) -ForegroundColor $(@{ RED = 'Red'; GREEN = 'Cyan'; YELLOW = 'Yellow' }[$lamp])
    $global:LASTEXITCODE = @{ GREEN = 0; YELLOW = 2; RED = 1 }[$lamp]
  } finally {
    try { (Get-Process -Id $PID).PriorityClass = $prio0 } catch { }
    if ($null -ne $via0) { $env:VIA_ROOT = $via0 } else { Remove-Item Env:\VIA_ROOT -ErrorAction SilentlyContinue }
    if ($null -ne $vrn0) { $env:VRN2_ROOT = $vrn0 } else { Remove-Item Env:\VRN2_ROOT -ErrorAction SilentlyContinue }
  }
}
```

## 一行實際做的事(boot · 給看的 · 上面那行就是它的 base64)

```text
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$R  = if ($env:VRN2_ROOT) { $env:VRN2_ROOT } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
$Br = 'claude/optimistic-goodall-yhalc5'
$P  = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0146'
$H  = '9f7490806d18c8be00ecf6a4f43ebeef565c0ccbbc3ad7ea5f822bb7f2a48bfa'
Write-Host ('[VRN-2] PowerShell ' + $PSVersionTable.PSVersion + ' · 從 GitHub 讀一鍵 v0146 程式碼(核對 SHA-256 後執行)') -ForegroundColor Yellow
$top = git -C $R rev-parse --show-toplevel 2>$null
if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git" -ForegroundColor Red; exit 1 }
$top = "$top".Trim()
$t = Join-Path ([IO.Path]::GetTempPath()) ('vrn2_boot_' + (Get-Date).ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $t | Out-Null
$z = Join-Path $t 'oneclick.zip'; $okz = $false
foreach ($b in $Br, 'main') {
  foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }
  git -C $top archive --format=zip -o $z ('origin/' + $b + ':' + $P) VRN2_OneClick_v0146.md 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $okz = $true; Write-Host ('[計] 一鍵程式碼來源 GitHub ' + $b) -ForegroundColor DarkGray; break }
}
if (-not $okz) { Write-Host "[RED] 讀不到 GitHub 分支 $Br 或 main 的一鍵程式碼(網路 / git)" -ForegroundColor Red; exit 1 }
Expand-Archive -LiteralPath $z -DestinationPath $t -Force
$md = [IO.File]::ReadAllText((Join-Path $t 'VRN2_OneClick_v0146.md'), [Text.Encoding]::UTF8) -replace "`r`n", "`n"
$code = [regex]::Match($md, '(?s)```powershell\n(.*?)\n```').Groups[1].Value
$sha = -join ([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($code)) | ForEach-Object { $_.ToString('x2') })
if ($sha -ne $H) { Write-Host "[RED] 一鍵程式碼 SHA-256 不對($sha)· 不執行" -ForegroundColor Red; exit 1 }
Write-Host ('[GREEN] 一鍵程式碼 SHA-256 ' + $H.Substring(0, 12) + ' 相符 → 在 PowerShell 裡執行') -ForegroundColor Green
try { & ([scriptblock]::Create($code)) } catch { Write-Host ('[RED] 一鍵執行中斷(未攔截的例外):' + $_.Exception.Message + ' · ' + $_.InvocationInfo.PositionMessage) -ForegroundColor Red; $global:LASTEXITCODE = 1 }   # Codex #551:例外逃出來也要 rc 1
exit $(if ($null -ne $global:LASTEXITCODE) { [int]$global:LASTEXITCODE } else { 0 })   # v0146(Codex #550):NEXT 的燈帶回這個子行程的 rc(GREEN 0 · YELLOW 2 · RED 1 → cmd 的 %ERRORLEVEL%)
```
