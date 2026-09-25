# VIA 官方免費來源優先 + FinMind 台股資金流擷取引擎

## 擷取內容

| 中文資料 | 優先來源 | FinMind 用途 | 擷取粒度 |
|---|---|---:|---|
| 台股分點資料表 | FinMind `TaiwanStockTradingDailyReport` | 歷史及每日更新 | Standard：股票 × 交易日；SponsorPro：全市場 × 交易日 |
| 台股八大行庫買賣表 | FinMind `TaiwanStockGovernmentBankBuySell` | 全部；屬資料商整理值 | 每交易日全市場，下載後保留目標股票 |
| 當日券商分點統計表 | FinMind `TaiwanStockTradingDailyReportSecIdAgg` | 全部 | 每檔股票可查日期區間 |
| 鉅額交易買賣日報表 | FinMind `TaiwanStockBlockTradingDailyReport` | 全部 | 2026-04-28 起，每交易日全市場 |
| 鉅額交易日成交資訊 | TWSE／TPEX 官方 API | 2023 起歷史缺口及官方失敗備援 | 最新日先抓兩市全市場，再按股票篩選 |
| 台股產業鏈資金流向 | FinMind `TaiwanStockIndustryChainMoneyFlow` | 全部 | 每交易日一個 request |
| 集保戶股權分散表 | TDCC 官方開放資料 | 2023 起歷史週資料及官方失敗備援 | 最新週全市場一次下載 |
| 台股日價量 | TWSE／TPEX 官方 OpenAPI | 歷史缺口及官方失敗備援 | 最新日兩市全市場快照 |
| 三大法人寬表 | FinMind `TaiwanStockInstitutionalInvestorsBuySellWide` | 全部，維持自營／避險欄位一致 | 每檔股票可查日期區間 |
| 融資融券 | TWSE／TPEX 官方 OpenAPI | 歷史缺口及官方失敗備援 | 最新日兩市全市場快照 |
| 當沖量值 | FinMind `TaiwanStockDayTrading` | 全部，維持個股買賣金額欄位一致 | 每檔股票可查日期區間 |

所有資料共用 batching、coverage、額度閘門及斷點續傳。官方最新快照成功後先寫入 coverage，FinMind 只補未覆蓋的歷史區間；官方任一市場失敗時不建立 coverage，FinMind 會自然接手。自營商判斷會分開「自行買賣」與「避險」，方向訊號不把避險買賣直接當成看多或看空。

券商分點官方網頁具有驗證碼且僅提供當日查詢，本引擎不破解驗證碼、不輪替代理，也不把受限網頁當作批次 Open API；分點資料因此維持由 FinMind 擷取。

## 啟動

1. 編輯程式頂部參數，或把約 250 檔代碼放進 `tickers_250.txt`。
2. Windows PowerShell 執行：

```powershell
.\Run_FinMind_TW_Flow.ps1 --start-date 2023-01-01 --end-date latest --plan-only
```

3. `hybrid`／`finmind_only` 啟動時會以隱藏方式詢問 API Token。Token 只存在記憶體，不寫入設定、DuckDB、稽核報告或輸出檔。
4. 確認計畫後正式執行：

```powershell
.\Run_FinMind_TW_Flow.ps1 --source-mode hybrid --start-date 2023-01-01 --end-date latest
```

來源模式：

- `--source-mode hybrid`：預設；官方免費最新快照優先，FinMind 補歷史及失敗缺口。
- `--source-mode finmind_only`：完全沿用 v1.4.0 行為。
- `--source-mode official_only`：只更新可由官方完整取得的最新快照，不詢問 FinMind Token。

每日只更新最新交易日的全部啟用資料，可直接雙擊或執行：

```powershell
.\Run_TW_Hybrid_Latest.ps1
```

只更新最新交易日的原始分點與分點彙總，可獨立執行：

```powershell
.\Run_FinMind_Branch_Latest.ps1
```

它會在啟動時詢問 Token，先找最近21個日曆日中的最新交易日，只啟用兩個分點資料集；完成資料會立即寫入相同 DuckDB，後續再執行資金圈分析即可。

## Veritas Codex Nexus 整合

`Run_FinMind_TW_Flow.ps1` 會透過 `Invoke-VeritasCodexNexus.ps1` 的 `FinMind/Fetch` 任務啟動，不再直接呼叫引擎。預設導入：

```text
C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules\VeritasCeleritas.py
C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules\VeritasAegisNexus.py
```

也可直接由既有 Nexus 入口執行：

```powershell
$Supportive = "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules"

& "$Supportive\Invoke-VeritasCodexNexus.ps1" `
    -Mode FinMind `
    -Task Fetch `
    -FinMindEnginePath "$Supportive\VIA_FinMind_TW_Flow_Engine.py" `
    -CeleritasPath "$Supportive\VeritasCeleritas.py" `
    -AegisPath "$Supportive\VeritasAegisNexus.py" `
    -FinMindArgs @('--start-date','2023-01-01','--end-date','latest','--branch-mode','auto','--range-batch-mode','two_year')
```

實際啟用範圍：

- VeritasCeleritas：CPU／記憶體預算、執行緒環境、RAM-aware checkpoint batch。
- VeritasAegisNexus：Circuit Breaker、連續錯誤保護與治理狀態。
- FinMind 專用額度控制仍由本引擎負責，避免通用加速器把 API 瞬間推到 402／IP 封鎖。
- Aegis 中的代理輪替、IP 輪替、Token 輪替與 anti-scrape bypass 對 FinMind 全部停用。

## 疑似資金管理圈與大戶行為分析

`VIA_TW_Branch_Capital_Circle_Engine.py` 使用日資料執行兩階段分析：

1. 在相似股票族群內，依同日同股方向、同步持續性、成本相似度、交易量規律、股票重疊與族群偏好建立分點關聯分數。
2. 僅將互為 Top-K 高分鄰居的分點合併為疑似資金圈，再結合三大法人、融資融券、當沖、價量及鉅額交易判定 WH-001～WH-040 行為候選。

公開分點是券商自營與客戶交易的彙總通路，因此輸出只代表「疑似相同資金管理圈／相近交易策略來源」，不能確認特定自然人、法人或違法行為。

族群對照至少需要以下欄位；同一股票可用多列加入多個族群：

```csv
stock_id,group_id,group_name,member_role
3017,AI_SERVER,AI伺服器,LEADER
3324,AI_SERVER,AI伺服器,PEER
```

完成資料擷取後執行：

```powershell
.\Run_TW_Branch_Capital_Circle.ps1 `
    -GroupMap "C:\path\stock_group_map.csv" `
    -DuckDBPath ".\_codex_out\FinMind_TW_Flow_Output\FinMind_TW_Flow.duckdb"
```

不帶 `-GroupMap` 時會顯示輸入提示，可直接把 CSV 或 Parquet 拖入視窗。

主要輸出：

| 輸出表 | 用途 |
|---|---|
| `capital_circle_summary` | 資金圈、信心、主要族群及疑似投信／自營／外資型態 |
| `capital_circle_member` | 每個資金圈包含哪些分點及成員分數 |
| `capital_circle_edge` | 分點兩兩關係分數與七項組成 |
| `capital_circle_behavior_daily` | 每日個股／族群 WH 行為、分數與證據 |
| `capital_circle_behavior_catalog` | WH-001～WH-040 可判定程度及資料限制 |

日資料無法可靠判定尾盤集中下單、消息前布局、現貨加期貨避險及事件前降曝險；這些行為會保留在 catalog 並標示需要分時、事件或期貨部位資料，不會勉強產生結論。

## 分點擷取模式

- `--branch-mode auto`：正式執行時先探測 SponsorPro 日檔；可用就採日檔，否則退回 Standard。
- `--branch-mode standard`：一檔股票、一天一個 request，額度成本最高。
- `--branch-mode sponsorpro`：一天一個全市場 Parquet，下載後只保留目標約 250 檔。

`--plan-only` 的 auto 為避免多耗一次付費 request，保守地以 Standard 計算。若已確定有 SponsorPro，規劃時請明確加 `--branch-mode sponsorpro`。

## 提高每次 Request 資料量

引擎只採用 FinMind 官方端點允許的較大粒度，不以多 Token、代理或 IP 規避額度：

| 資料集 | 最大化方式 | 限制 |
|---|---|---|
| `TaiwanStockTradingDailyReport` | SponsorPro `storage_objects` 全市場日檔 | Standard 官方限定單一股票／單一交易日，不能合法合併多日 |
| `TaiwanStockTradingDailyReportSecIdAgg` | 同一股票用較長 `start_date`～`end_date` | 日期越長，JSON、RAM 與失敗重送成本越高 |
| `TaiwanStockBlockTrade`、日價量、三大法人、融資融券、當沖 | 同一股票用較長日期區間 | 約 250 檔時完整區間最省 request；兩年批次較容易續傳 |
| 八大行庫、鉅額買賣日報、產業鏈資金流 | 每日全市場 | 官方資料粒度本身就是一天一個 request |

區間批次可選：

- `--range-batch-mode two_year`：預設；每兩個曆年一批，較原年度模式減少約 50% 區間 requests。
- `--range-batch-mode full_history`：一檔股票完整期間一個 request，額度最省；若本機 RAM 不足或 API 逾時，改回 `two_year`。
- `--range-batch-mode calendar_year`：一年一批，回應最小、重送成本最低。

FinMind SDK 的 async batch 仍會送出多個 requests，只能縮短等待延遲，不能減少會員額度用量，因此本引擎不會用無節制並行突破限速。

## 斷點續傳與增量更新

- 預設由「最新交易日 → 2023-01-01」反向回補；中斷時優先留下近期可用資料。
- 每 25 requests 執行 DuckDB `CHECKPOINT` 並原子更新 `audit/FinMind_Checkpoint_Status.json`。
- 每個 request 成功後立即寫入 DuckDB 與 `request_ledger`，不是等整批完成才寫。
- 日期區間型 API 預設依兩個曆年由新到舊批次回補；會先完成兩個資料集的最新窗口，再處理較舊窗口。
- `request_ledger`：記錄每個日／股票 partition 是否成功；成功項目重跑會自動跳過。
- `range_coverage`：合併已完成的相鄰日期區間；即使回傳 0 筆也記錄已查範圍，切換年度／兩年／完整歷史模式不會因 task 名稱改變而重抓。
- `fetch_cursor`：保留最新查詢終點；隔日重跑只查 coverage 後的新日期。
- DuckDB 依各資料表自然鍵 `INSERT OR REPLACE`；API 重送不會累積重複列。
- 達到額度保留值時狀態為 `paused_quota`。下一個額度視窗重跑同一指令即可續傳。
- 連續 5 次網路錯誤會安全暫停為 `paused_network`，避免離線時大量無效重試。
- Ctrl+C 會先固定 checkpoint、輸出當時可用的 Parquet／CSV 與稽核報告，再安全結束。

## 輸出

```text
FinMind_TW_Flow_Output/
├─ FinMind_TW_Flow.duckdb
├─ parquet/   # Parquet，檔名無副檔名
├─ csv/       # UTF-8-SIG CSV，檔名無副檔名
└─ audit/     # 每次執行 JSON 稽核報告
```

輸出日期為 `YYYY/MM/DD`；DuckDB 內部維持 API 原生 `YYYY-MM-DD`，便於比較與增量游標。

每張輸出表均新增三個來源欄位：

| 欄位 | 用途 |
|---|---|
| `source_provider` | `TWSE`、`TPEX`、`TDCC` 或 `FINMIND` |
| `source_mode` | `official_api`、`official_open_data` 或 `finmind_api` |
| `source_dataset` | 實際官方端點／FinMind Dataset 識別 |

自然鍵不包含來源；同日期、同股票、同交易的官方資料會取代 FinMind 重複列，但來源欄位會保留最後成功寫入者，方便稽核。

## 額度與時間

FinMind 官方文件目前標示 Token 為「每小時」額度，而不是固定每日額度；不同付費方案上限可能不同。引擎啟動後呼叫 `user_info`，讀取 API Key 當下的 `user_count` 與 `api_request_limit`，因此畫面估算以你的實際方案為準。

以約 250 檔、2023-01-01 至 2026-08-29、約 887 個交易日及 600 requests/hour 粗估：

| 分點／區間模式 | 約需 requests | 理論時間 |
|---|---:|---:|
| Standard + `calendar_year` | 約 229,400 | 382.3 小時／15.9 天連續 |
| Standard + `two_year` | 約 225,900 | 376.5 小時／15.7 天連續 |
| Standard + `full_history` | 約 224,150 | 373.6 小時／15.6 天連續 |
| SponsorPro + `calendar_year` | 約 9,740 | 16.2 小時 |
| SponsorPro + `two_year` | 約 6,240 | 10.4 小時 |
| SponsorPro + `full_history` | 約 4,490 | 7.5 小時 |

Standard 的原始分點約 22.05 萬 requests，仍佔總量絕大部分；股權分散表歷史回補會再增加區間 requests。官方免費來源主要降低「完成建庫後的每日更新」成本；第一次回補 2023 年至今仍以 FinMind SponsorPro + `full_history` 最有效率。

實際數字會因真實交易日、已完成斷點、帳號當下已用額度與指定股票數而變動，請以 `--plan-only` 輸出為準。

## 額度合規與錯誤處理

- 引擎在 `api_request_limit` 前保留安全額度，不會刻意越過會員上限。
- 收到 `402 Requests reach the upper limit` 立即停止，不持續重送。
- 收到 Token／權限／參數等永久性 4xx 錯誤時 fail closed，不做無限 retry。
- 不輪替 Token、帳號、代理 IP 或其他方式規避額度；如需更高吞吐量，使用 FinMind 正式升級方案。
- 超額回應本身通常是平台配額控管，不應直接解讀為刑事違法；但繞過限制、持續造成大量錯誤請求或超出資料授權範圍，可能違反服務條款並觸發 IP 封鎖，實際法律責任仍依使用方式判斷。

## 已知資料限制

- 原始分點資料官方明列 2023-01-11～2023-01-17 等日期缺資料；引擎會跳過已知整日缺漏。
- 八大行庫官方另列少數缺漏日；引擎不以錯誤值補零。
- `TaiwanStockGovernmentBankBuySell` 是 FinMind／資料商整理表，不等同政府基金或「國家隊」真實持倉；若由公股券商分點自行加總，只能標示為代理指標。
- TDCC 最新資料採每週最後營業日收盤後快照；持股分級 16 為差異數調整、17 為合計，不能與 1～15 級重複加總。
- 產業鏈資金流歷史資料採「目前」產業鏈分類回算；一家公司可屬多個產業鏈，產業鏈比例合計可大於 100%。
- 鉅額交易買賣日報表只從 2026-04-28 起提供，2023 年起始不代表此前有資料。
