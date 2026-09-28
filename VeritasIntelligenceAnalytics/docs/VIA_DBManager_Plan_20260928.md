# VIA_DBManager · 資料庫管理優化規劃(依現況重新規劃,只採用適合的)

操作員 2026-09-28 令:資料庫管理優化與 HTML U/I 參考「適合才採用」,用我們的標準模板規劃;先把現況讀一次,再重新規劃。
參考來源是操作員貼來的一段外部 AI 對話(以下稱「提案」)。**提案把本倉當成 MovieLens 電影資料(movies / ratings / tags / links.csv),那是虛構的**;本倉是 VIA 台股資料系統,以下全部以樹上實際的冊與程式為準。

## 0. 結論

1. 提案要的功能,**七成樹上已經有正主**:
   - 一頁目錄與逐表普查:CGC_MDL123 DataHome、CGC_MDL148 EngineBus `db_census`、CGC_MDL098 DataCatalog。
   - 增量鍵:L27、L37,ENG054 的 MAX(date)−3 天重疊,ENG089 的缺口規劃。
   - 去重補缺:SUP_MDL753 `upsert_rows` / `upsert_select`。
   - 批次擷取:SUP_MDL753 `batch_fetch`、網路統包 SUP_MDL740、同意閘 CGC_MDL224。
   - 匯出:ENG045 OutputHub、ENG055 `export`。
   - Parquet + DuckDB 版面約定:VIA_DataHome_SSOT `layout_contract`。
2. 所以 **VIA_DBManager 不是新蓋一套**,而是放在 VCGC 裡的**門面(facade)**:
   - 一個入口,把上述正主串起來,給 U/I 一份統一輸出(L20:CGC_MDL149 是所有庫的唯一接觸口;L30:同類不重複)。
   - 自己只補**真的缺的四塊**:跨庫數量核對、選取式匯出(MD / JSON / Big5 + 範圍選取)、儲存最佳化計畫(row group / 重複層)、API 呼叫帳。
3. U/I 不另做一頁:接在剛做好的主控台藍圖(CGC_MDL227,制式模板 + synchronizer)上,加一個「資料庫」家族與分頁。

## 1. 現況(讀一次的結果)

來源:`VIA_DB_Table_SSOT_v0100.json`,操作員工作站 via-census 實測,2026-09-13(批475 貼回)。**已經 15 天沒更新。容器裡沒有正庫(`output_hub/mega/` 是空的),所以這份數字不能在容器重量**;第一步要在工作站重跑普查。

| 庫 | 表數 | 總列數 | 最大的表 |
|---|---|---|---|
| `vdf_tw_market.duckdb` | 39 | 13,686,478 | tw_daily_prices 2.13M · tw_prices_adj 2.13M · prices_canonical 2.13M · features_daily 2.13M · tw_trading_daily 1.47M · 籌碼三表各 1.1M |
| `vdf_global_market.duckdb` | 11 | 1,107,695 | us_macro 285K · global_daily 204K ×4 層 |
| `ActiveTWETF.duckdb` | 6 | 585 | active_tw_etf_universe 260 |
| **合計** | **56** | **≈14.8M** | 另有 12 張「已知舊表不在」 |

**從現況直接看得出來的問題(優化的真正目標)**

| # | 現象 | 影響 | 處理原則 |
|---|---|---|---|
| A | 價格四層同列數:`tw_daily_prices → tw_prices_adj → prices_canonical → features_daily` 都是 2.13M 列;global 也是四層各 204K | 最大的空間重疊來源。提案擔心的「新舊並存重疊」其實已經發生在這裡 | 先在工作站量每層欄位重疊與可否由上一層決定性推得;能推得的改 VIEW。**只出計畫,刪表是操作員的手(L10)** |
| B | `tw_daily_prices` 最早日期是 1900-01-01 | 哨兵列污染,跨度與增量起點都會算錯 | 既有 `db_hygiene` 只寫 SQL 不執行;維持「先標不刪」 |
| C | 7 張表 0 列(vrn_extraction_logic、via_policy_*、via_handover、tw_financial*) | 有的是還沒同步,有的是還沒抓 | 核對表分成「冊說該有」和「目前 0」兩態,不當綠 |
| D | 22 張表沒有日期範圍(`~`) | 選期間匯出、增量都沒有日期欄可用 | 普查要說出每表的日期欄或「無日期欄」,U/I 期間選擇器照實停用 |
| E | 量測已 15 天 | 頁上數字不是現在 | 目錄頁帶量測時間,超過門檻顯示 STALE(ENG089 `catalog_freshness` 已有) |

**規模**:全部約 1,480 萬列,zstd Parquet 估計合計只有數百 MB 級。這個量級決定了下面幾條「提案不適用」。

## 2. 提案逐條對照(適合才採用)

| 提案項目 | 判定 | 樹上正主 / 理由 |
|---|---|---|
| Parquet 存、DuckDB 管 | **已是規則** | L10 + `layout_contract`:parquet(zstd)是本體;DuckDB 是管家,表 = VIEW over `read_parquet`。L90:DuckDB 是正本,CSV / JSON / Sheets 是單向派生、不回灌 |
| 分區依日期 / 市場,不依 ticker | **已是規則** | `layout_contract` 按年分片 `part-YYYY.parquet` |
| 「單日單檔」 | **不採用** | 日資料一年約 250 個交易日,單日單檔會變成上千個小檔(正是提案自己要避免的碎檔)。本規模用**一年一檔**(既有約定) |
| RowGroup 128–256MB | **修正後採用** | 單表整本才幾十 MB,128MB 的 row group 等於整檔一組,失去下推效果。改為:年檔內依 (date, ticker) 排序、**依列數**設 ROW_GROUP_SIZE(先在工作站量,起點 DuckDB 預設 122,880 列)。樹上目前**完全沒有** row group 設定 → 列入缺口 |
| Metadata cache(一頁目錄) | **已有** | MDL123 `catalog()` 寫 `DATAHOME_CATALOG_latest.json`;token_saving_rules 已規定「測試 / 抓取只讀這一頁,不掃湖、不逐表 COUNT(*)」 |
| Incremental cache | **已有** | ENG054 / ENG064 checkpoint;L27 先查庫缺口;L37 MAX(date)−3 天重疊 + anti-join。不另開一本 incremental_cache.parquet(會變第二本帳) |
| 去重 + 補缺(MERGE) | **已有,不換寫法** | SUP_MDL753 `upsert_rows` / `upsert_select`(key anti-join、`fill` 只補空欄、`plan=True` 只數不寫)。改用 MERGE 會變第二把尺(L05 / L30) |
| 批次入庫(COPY + CTAS) | **已有** | ENG051 `COPY … ZSTD` + 原子換名;L28 先落 parquet / BOM-CSV journal 再交易入庫 |
| Batch fetching 省 API | **已有** | SUP_MDL753 `batch_fetch`(分塊、並行、失敗減半、每 80 項 checkpoint)· SUP_MDL740 重試退避 · CGC_MDL224 同意閘 |
| 核對資料數量 | **缺(要做)** | 只有個別引擎自報(ENG064「抓 X · 入 Y」、ENG045 回讀)。**沒有跨庫「冊說 vs 實量」核對** |
| U/I 一口氣攤牌 + 選表 / 欄 / 期間 / 格式匯出 | **部分有,要接起來** | DataCatalog 頁只看不選;ENG045 / ENG055 能整庫匯出,不能選範圍。缺選取式匯出 |
| CSV 編碼 | **已有 utf-8-sig;Big5 缺** | 預設 utf-8-sig(Excel 開不亂碼)。Big5 / cp950 要另做,**Big5 放不下的字要逐字報數,不偷換成 ?** |
| Google Sheet | **採用「相容 CSV」** | ENG045 已產 gsheet 相容 CSV。直接寫 Sheets API 要 OAuth + 同意閘,**不當預設** |
| Markdown / JSON 匯出 | **缺(要做)** | 目前只有狀態報告轉 MD。MD 只給小範圍(上限列數,超過改建議 CSV) |
| 「新引擎不複製舊資料,只存 unified_output.parquet」 | **修正後採用** | 概念對(舊程式不改、U/I 只讀一個出口)。但統一輸出是**目錄 + 按需查詢**,不是再存一份資料:U/I 讀目錄頁;要資料時才按選取範圍查 DuckDB,匯出到 VIA_Reports(再生件,不 commit) |
| Token 成本估計欄 | **修正定義** | 提案把兩種 token 混在一起,要分開講:**AI 讀取 token**:由「給 AI 看的是目錄頁與選取子集,不是整表」決定,可用讀取的列數 × 欄數 / 位元組當代理指標;**API 擷取**:用呼叫次數計,不是 token。不編一個「預估 Token 成本」數字 |
| AQL / 語意查詢 / 自然語言轉 SQL | **不採用(現階段)** | 多一層語言與轉譯器,與「少一層、單一出處」相反;U/I 的選取式查詢已涵蓋需求 |
| Hot path materialize | **暫不做** | 1,480 萬列的 DuckDB 本身就是熱路徑;先量再說 |
| 雲端部署 / React | **不採用** | 本系統是本機工作站 + 制式 HTML 模板(零伺服器、零 CDN) |

## 3. VIA_DBManager 定義(放在 VCGC)

- 名稱:**VIA_DBManager**(操作員命名)。
- 檔名依本倉慣例:`supportive modules/registry/CGC_MDL228_VIADBManager_v0100.py`(MDL228 已查全部遠端分支無人用)。
- 位置:VCGC 中央治理;經 CGC_MDL149 唯一入口派送(L20)。
- 原則:
  - 唯讀為預設。
  - 寫只寫 VIA_Reports。
  - 動正庫的一律只出計畫,由操作員 `--apply`。
  - 自測零污染(L17:清掉 `VIA_DB_*` / `VIA_DATA_HOME`,只用暫存庫)。

| 功能 | 做法 | 委派的正主 | 新寫的部分 |
|---|---|---|---|
| ① 現況總覽 `overview` | 三庫 × 表:列數、日期欄、範圍、量測時間、新鮮度、四態 | MDL123 `catalog` / `table_stat` · EngineBus `db_census` · Table_SSOT(冊上期望) · ENG089 `catalog_freshness` | 合併成一份固定欄位總表 |
| ② 數量核對 `reconcile` | 冊說該有 / 上次量 / 這次量 → OK · 少了 · 多了 · 0 列 · 表不在 | Table_SSOT `min_rows` / `rows_seen` · `table_stat` | **新**:核對表與差異原因 |
| ③ 選取式匯出 `export` | 庫 → 表 → 欄 → 期間 → 格式(CSV utf-8-sig / CSV Big5 / gsheet CSV / MD / JSON);唯讀連線,只選必要欄(欄裁切)+ WHERE 期間(下推) | ENG045 OutputHub 寫檔與回讀核對 | **新**:範圍選取、Big5 逐字報數、MD / JSON 上限 |
| ④ 儲存最佳化計畫 `optimize --plan` | 四層重複量測、年檔 row group 建議、哨兵列、碎檔數 | ENG073 `optimize_plan` · EngineBus `db_hygiene` | **新**:重複層量測(只出計畫,不刪不改) |
| ⑤ API 呼叫帳 `apicalls` | 每次擷取的呼叫數、批數、失敗重試、跳過(已在庫) | SUP_MDL740 / `batch_fetch` 的計數 | **新**:一本只增的呼叫帳(省了多少次看得到) |
| ⑥ 統一輸出 | 一份 JSON 給 U/I(主控台藍圖直接吃) | — | 固定欄位 |

**固定欄位**:取提案裡合用的,去掉虛構的。
- **總覽列**:DB · TABLE · ROWS · ROWS_EXPECTED · DATE_COL · DATE_LO · DATE_HI · MEASURED_AT · FRESHNESS · WRITERS · STATE(GREEN / AMBER / RED / NODATA / ABSENT)· NOTE
- **匯出結果**:DB · TABLE · COLUMNS · RANGE · ROWS · FORMAT · ENCODING · LOSSY_CHARS · OUTPUT_PATH · READBACK_ROWS · SECS

## 4. U/I(制式模板,接在 CGC_MDL227 主控台)

- **左面板:加一個「DB」家族**。
  - 流程:庫 → 表(列出列數與日期範圍)→ 勾欄位 → 期間(沒有日期欄的表停用並說明)→ 格式。
  - 「匯出(乾跑)」先顯示將讀幾列、幾欄、寫到哪。
  - 真匯出經 VCGC 入口,不在頁上直接寫檔。
- **右面板:總覽加一張「資料庫」卡**:三庫 KPI(表數 · 總列 · 最新日 · 新鮮度)。
- **新增分頁「資料庫」**,放在「引擎」之後、「結果」之前:
  - 56 表的總表,可依庫、狀態篩選。
  - 熱圖:庫 × 四態。
  - 核對差異列、重複層計畫。
  - 最近一次匯出紀錄。
- 同一套 synchronizer 對接;模板原文零改動。

## 5. 分期(每期一個還原點)

| 期 | 內容 | 碰不碰正庫 | 誰能在哪做 |
|---|---|---|---|
| P1 | `overview` + `reconcile` + 主控台「資料庫」分頁(讀目錄頁與冊) | 唯讀 | 容器可做程式與沙盒自測;**真數字要工作站跑一次普查貼回** |
| P2 | 選取式匯出(CSV utf-8-sig / Big5 / gsheet CSV / MD / JSON),只寫 VIA_Reports | 唯讀連線 | 同上 |
| P3 | `optimize --plan`:四層重複量測、row group 建議、哨兵列 | 只量不改 | 工作站量;改動候操作員 `--apply` |
| P4 | API 呼叫帳 | 只增一本帳 | 容器可做,工作站驗 |

## 6. 候操作員裁定

1. 要不要照這個分期做?建議先做 P1 + P2:唯讀,馬上看得到全貌、也能選範圍匯出。
2. 價格四層(A)能推得的改 VIEW:要等 P3 的量測出來再裁,本規劃不動。
3. Google Sheet 直接寫入 API(OAuth)要不要做;目前只給相容 CSV。
4. 工作站跑一次:`via-census`(或 EngineBus `census --tables`)+ DataHome `catalog`,把結果貼回,現況表才是今天的數字。
