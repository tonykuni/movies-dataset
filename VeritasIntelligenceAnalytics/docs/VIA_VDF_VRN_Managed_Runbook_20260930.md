# VCGC → VDF → VRN 實測與操作（2026-09-30）

本批新增版本保留全部舊引擎。隔離測試使用真 DuckDB / Parquet，行情為模擬；VRN 執行原擷取正主處理合成 TXT 與倉內合成 PDF。**尚未驗證 Tony 的 Windows 正式資料家、真行情下載、正式報告全樣本或開機排程。** 不以本批通過取代原有 SDD / 主機待辦。

## 啟動條件與 CSV

沿用已安裝的 `via-vcgc` 入口。環境需已有 Python、duckdb、polars、pandas；PDF 擷取需 PyMuPDF 或 pdfplumber。缺件依既有 ENV MANAGER 處理。網路更新沿用 ENG054 的既有同意閘；程式不代設同意。常駐更新沒有 AI / LLM 呼叫，因此不消耗模型 token；行情供應商仍有自己的配額、條款、網路費與限制，不能保證零 API 成本。

CSV UTF-8 或 UTF-8 BOM，第一列固定為 `TICKER,NAME`。每列一個商品，逗號名稱以 CSV 雙引號包覆。不要讓 Excel 把代號轉成數字。附範例 `docs/examples/VDF_products_v0100.csv`：

```csv
TICKER,NAME
2330.TW,台積電
0050.TW,元大台灣50
6488.TWO,環球晶
```

數字代號一定加 `.TW`（上市）或 `.TWO`（上櫃），系統不猜市場。核對欄名／欄數／重複／代號格式／空白名称／既有名稱衝突，任一錯誤整批拒絕；不呼叫網路確認證券存在或名稱正確。最多 100,000 列、16 MiB。重匯同一商品不新增、不改啟用狀態。

## VDF 指令

以下 `$D` 是新的受管資料夾，不能直接指定已有正式庫的非空目錄。在 PowerShell 可設定：

```powershell
$D = 'C:\Users\tonyk\VIA System\via_database\vdf_managed'
via-vcgc run VDF_SystemManager store contract
via-vcgc run VDF_SystemManager store validate-csv --csv .\products.csv
via-vcgc run VDF_SystemManager store --root "$D" init
via-vcgc run VDF_SystemManager store --root "$D" import-csv --csv .\products.csv
via-vcgc run VDF_SystemManager store --root "$D" status --full
# 明示啟用後才會被 update/start 選中；也可用 --csv 批次啟用。
via-vcgc run VDF_SystemManager store --root "$D" activate --ticker 2330.TW
via-vcgc run VDF_SystemManager store --root "$D" update
via-vcgc run VDF_SystemManager store --root "$D" inspect
via-vcgc run VDF_SystemManager store --root "$D" sample --ticker 2330.TW --limit 10
# 前景常駐：先更新一次，以後每小時更新；Ctrl+C 停止。
via-vcgc run VDF_SystemManager store --root "$D" start --interval 3600
```

`--root` 必須在 store 子命令前。省略則解析中央 DataHome 下 `vdf_managed`，不另造倉內正式庫。`status` 只看目錄與 catalog 摘要；`--full` 展開商品。`inspect` 才實讀 Parquet 欄位與筆數，`sample` 限量讀資料。可直接以 DuckDB 唯讀開啟 `vdf_catalog.duckdb` 查 `prices` view；明細只存 ZSTD Parquet，不再存一份日價 DuckDB 表。

新增預設停用；activate 本身不下載。常駐迴圈每輪重新讀商品清單，新啟用商品下一輪自動加入。每個商品從 MAX(Date) 前 3 天補起，空庫自 2022-07-01 起；已確認到目標日則零行情工作，重疊舊鍵不覆寫、不重複，有不同值回 PARTIAL。台北時間 16:00 前以昨日日價為目標，週末回退；**未內建台灣假日表**，假日／來源延遲保留 PARTIAL 並於下輪重試。`api_jobs` 是商品工作數，不是供應商 HTTP 次數。

```powershell
# 暫停更新且保留所有資料
via-vcgc run VDF_SystemManager store --root "$D" deactivate --ticker 2330.TW
# 明示刪除：先停用並記 tombstone，再刪該商品整個受管目錄與 catalog。
via-vcgc run VDF_SystemManager store --root "$D" delete --ticker 2330.TW
# 唯讀舊庫，依已匯入商品分批複製日價至 Parquet；不變更啟用狀態。
via-vcgc run VDF_SystemManager store --root "$D" migrate-legacy --db 'C:\Users\tonyk\VIA System\via_database\vdf_tw_market.duckdb'
```

刪除只涵蓋受管庫內該商品的全資料（本版 daily prices），**不掃描／删除其他舊 DuckDB、備份、報告或來源 CSV**。舊資料若要全面移轉、停用舊排程並刪除，需先盤點所有主機副本；目前未冒稱完成。刪除失敗可重跑 delete，tombstone 商品不會被背景復活；重新匯入同代號屬明示重新新增。單寫入鎖涵蓋更新／匯入／刪除，避免競態；異常退出的 `.writer.lock` 不自動強搶，必須先確認原程序已停止。

本版不替主機註冊開機服務。可在 Windows 工作排程器「登入時」執行既有 Python 與 VCGC 入口：參數 `"<repo>\VeritasIntelligenceAnalytics\supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v0178.py" run VDF_SystemManager store --root "<D>" start --interval 3600`，起始位置為 repo；採「已有執行個體則不啟動」。使用該主機原有 VCGC 啟動環境與同意政策；先完成手動一次更新再設定。此項仍待主機實測。

## HEADER 鎖定

欄序取現有 `prices_core`（16 欄）：

| 欄位 | 型別 / 來源 |
|---|---|
| Date | DATE，來源 date |
| Ticker / YFinance_Ticker | VARCHAR，CSV 完整代號，含市場後綴 |
| Bloomberg_Ticker | VARCHAR，目前 NULL |
| Name | VARCHAR，匯入名稱 |
| Open / Low / High / Close / Adj_Close | DOUBLE，來源原值 |
| Adj_Open / Adj_Low / Adj_High | DOUBLE，目前 NULL，不推算 |
| Volume | BIGINT，拒絕負值／小數／非有限值／超出精確轉換範圍 |
| Turnover / Market_Cap | DOUBLE，目前 NULL |

未知來源欄位、不同商品、型別／日期不符即拒絕。不把 16 欄具備誤當成 16 欄都有真實值。既有 ENG054 8 欄正庫仍保留。受管庫 marker 同時保存欄位型別，不能悄悄改契約。

## 聚焦 VRN 的實測

新增 `VRN_SystemManager_v0111` 精確派送 `read logic`，避免 v0109 的全 argv 字串比對攔錯命令；新增 `probe` 使用既有 Integrated ReportDatabase Engine，沒有另抄擷取規則。

```powershell
via-vcgc run VRN_SystemManager --selftest
via-vcgc run VRN_SystemManager probe --selftest
via-vcgc run VRN_SystemManager provenance --selftest
via-vcgc run VRN_SystemManager read logic --json
# input 可為本機 PDF/TXT/DOCX 或資料夾；output 必須是尚不存在的新目錄。
via-vcgc run VRN_SystemManager probe --input 'C:\Reports\sample.pdf' --output 'C:\VRN_Test\run_001' --vdf-root "$D"
```

VDF→VRN 商品對照唯讀，保留四碼股票名稱、上市櫃市場及 Yahoo 代號；**原 VRN 名稱 parser 限首碼非零的台灣四碼股票**，ETF／海外代號明列 unsupported，不猜、不剪裁。缺 `--vdf-root` 仍可做獨立原檔擷取。

输出 `VRN_PROBE.json` 含命令結果、輸入 SHA、HEADER、實讀筆數、來源對照及未驗收項；另有原正主的 BasicInfo / FinancialData Parquet、DuckDB、JSON、HTML。PyArrow 缺席時經 DuckDB 寫真 Parquet，不偷改成 CSV。欄位順序沿用正主。損毀 Parquet 直接拋錯，不能視為空表。

回傳 `rc=0 / EXECUTED_REVIEW_REQUIRED` 只代表本次擷取和落地成功；不代表欄位值正確。失敗檔案 rc1，空批次或略過 OCR rc2；正式報告、年報單位／期別、OCR、全樣本準確率仍待驗收。舊入口保留，其歷史行為不被追溯改寫。

## 證據

每一案由 `via-vcgc handoff test <case>` 留下命令、rc、目標 marker、相依 SHA 與完整日誌：`vdf_dispatch`、`vdf_manager`、`vdf_store`、`vrn_manager_route`、`vrn_probe`。`handoff checkpoint` 的可續接燈不等於全系統 closeout 燈；原有主機、鎖漂移、OCR 待辦保留。
