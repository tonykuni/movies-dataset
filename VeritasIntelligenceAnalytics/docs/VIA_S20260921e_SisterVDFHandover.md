# VIA 交接紀錄 · 側線 2026-09-21 e(branch `claude/busy-bell-97sa4f`;姊妹倉 VIA-VDF-VRN → VDF session 交接接手;主線批號由併線的手指定 L25)

〇 這一批不是操作員直接下的令,是**跨 session 交接**:姊妹倉 `tonykuni/VIA-VDF-VRN` 的 Claude session(session_019RDuSzMmVQmsRCnPaDxbMX)13:18Z 以排程訊息把它交接膠囊裡「與 VDF 啟動鏈有關的部分」(§四、§七)交給本線;它引述的操作員令是「**將專案中所有的 VRN 接到此處理**」(VRN 部分交母系統 VRN session `claude/awesome-bardeen-h0wm5v`,VDF 部分交本線)。那條線收不到回覆,所以結果寫在這裡(它要求的「寫進母倉交接文」)。

**驗真(先量,不信轉述)**:① PR #23(`claude/festive-ptolemy-ts2yyh`,head `c1989e618c`)在 GitHub 上是 **open**、base `88de4b0` = 姊妹倉 main(PR #35「語義管線加速 7.9×」08:48Z 已併);② 該分支 `docs/VIA_VRN_HANDOVER.md` 一/四/五/七/八 節內容與訊息一致;③ 母倉掉球冊本來就有 A(姊妹倉同步 · 候工具層權限)、Z67(#23 未併 · 20 支 vrn-*.ts 無對表)、Z68(EnvManager 漂移)——工具層權限這次已開(add_repo 唯讀成功,淺 clone 於 `/home/user/via-vdf-vrn`,main `88de4b0`)。不變式(膠囊 §八)與本線既有律同:只增不減 · 引擎正本零觸碰 · 不代設 CONSENT · LIVE 關 · 零 force push · 注入器 dry-run · `references/intake` 不編輯。

## 一 · 做了什麼、沒做什麼

- **做**:量、對表、寫進交接文(本文)+ 掉球 Z106–Z108 + 台帳一條。**零程式改動、零引擎複製、零注入**。
- **沒做,及為什麼**:
  1. 不把姊妹倉 `VDF_PricesCanonical.py` / `VDF_FactorLibrary.py` 抄進母樹——引擎正本零觸碰,而且它們寫的 `prices_canonical` 是 32 欄的**表**,母樹的 `prices_canonical` 是 ENG060 的 9 欄**視圖**(批178「正典取數視圖」),同名不同形,寫進同一庫就是九頭龍;先裁再動(Z106)。
  2. 不在母樹跑姊妹倉注入器 `--apply`——母 48 支 `.ps1` 都要動 = L70 逐次許可;姊妹倉 §四 已做過 dry-run(47 支帶 `[VIA:PS-ACCEL:v0100]` 只加車道不重複 dot-source;48/48 pwsh 解析通過),母樹現在**沒有任何** `$VIAPS20` / `[VIA:PS-ACCEL20:v0100]` 宣告(grep 0)。要不要注入是裁定(Z107)。
  3. 探針 JSON 不餵格子——`VRN_PanoramaProbe` 的 S01–S10 是 VRN 管線十段(PATH_RESOLVE → SUMMARIZER),不是 VDF 啟動就緒的八項;要進格子是 VRN 對接口的域,交 VRN session;容器沒有 64 件位元組,只會全 BLOCKED 在 S02。

## 二 · PS20 車道 ↔ VIA_ACCEL25 對照表(膠囊 §七 要的那張)

尺:姊妹倉 `src/lib/via/accel.ts` PS-01–20(layer / needs / boost 原文)↔ 母 `supportive modules/registry/VIA_PS_Accelerators_25_Roster_v0100.ps1` 01–25(`VIA_PS_Accel_Module.ps1` 的 `$global:VIA_ACCEL20` 是同一冊前 20 條的退路,`VIA_ACCEL25` = 20 + 21–25)。「對應」= 同一件事;「部分」= 同一類但尺不同;「無」= 25 冊沒有這一層。

| PS 車道 | 層 | 做什麼(accel.ts 原文) | 母 25 冊 | 強度 | 說明 |
|---|---|---|---|---|---|
| PS-01 AsyncPool | fetch | 工作者池 8→16 | 21 資源預算與自動節流 | 部分 | 並行度是資源預算的一種;母另有模組級 `Invoke-VIAParallel` |
| PS-02 HttpReuse | fetch | 連線重用 | — | 無 | 屬網路正典 VeritasAegisNexus 會話層;25 冊只管閘與斷路(23) |
| PS-03 TimeoutBudget | fetch | 單序列 7s 截止 | 18 非阻塞 PS 執行 | 部分 | 母是 `Invoke-VIAGuarded` 看門狗逾時 kill,姊妹是每序列預算 |
| PS-04 RetryOnce | fetch | 僅一輪、fail-closed | 23 網路同意閘與斷路器 | 部分 | 斷路器語意同(一輪後閉) |
| PS-05 ConsentGate | fetch | 無 KEY 不外呼 | 23 網路同意閘與斷路器 | 對應 | 母閘 = `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`(L07/L08),姊妹閘 = KEY 在不在;**兩邊都不代設** |
| PS-06 SeriesCache | cache | 序列觀測記憶快取 | 22 快取、去重與斷點續跑 | 對應 | |
| PS-07 ParquetYearPart | cache | parquet year 分區落盤 | 22 | 部分 | 母的分區律 = 批128 mega 產物圈(parquet/duckdb 本機不入版控) |
| PS-08 SortDateId | struct | (date, series_id) 排序 | 24 輸入輸出契約與 Schema 驗證 | 部分 | 排序是契約的一部分;母 DB 表冊只記表/欄不記序 |
| PS-09 DictEncode | struct | 類別欄字典編碼 | 24 | 部分 | |
| PS-10 ChunkAlign | struct | 32/64B 對齊(SIMD 前提) | — | 無 | 25 冊沒有儲存體內部層;最近的 11 只「量」性能不做 |
| PS-11 MinMaxIndex | struct | RowGroup 跳過 | — | 無 | 同上 |
| PS-12 BloomProbe | struct | series_id 成員探針 | — | 無 | 同上 |
| PS-13 Batch64k | struct | Arrow batch 65536 | 21 | 部分 | 批量 = 記憶體預算 |
| PS-14 HotColumns | struct | date, series_id, value 靠前 | 24 | 部分 | |
| PS-15 TypedCols | struct | int32 / float64,禁 object | 24 | 對應 | Schema 驗證 |
| PS-16 PolarsLazy | compute | select / unique / 列裁剪 | 19 多引擎整合(Celeritas 常駐) | 對應 | 母正典 `VeritasCeleritas.py` 有 `_build_polars_backend` / `to_polars` / `_is_polars_lazy` |
| PS-17 SIMDScan | compute | AVX2/AVX-512 形狀核 · 執行期探測 | — | 無 | 母 Celeritas 沒有 SIMD 形狀核(grep 無);最近的 11 |
| PS-18 DuckDBScan | query | 謂詞下推 + 期末列 | 19 | 對應 | 母正典 Celeritas `_build_duckdb_backend`;L35 正典 DuckDB |
| PS-19 PredPush | query | WHERE date/series 先裁 | 19 | 部分 | |
| PS-20 PipeParallel | query | 抓取 ∥ 編碼 ∥ 查詢 | 18 · 21 | 部分 | 母 `Invoke-VIAParallel` + 資源預算 |

計:對應 5 · 部分 10 · 無 5(PS-02 / 10 / 11 / 12 / 17)。**反向**:母 25 冊的 01–17、20、25(AST · 語意 · Hydra · 依賴拓撲 · 沙盒 · 自動修正 · 三輪全景 · SSOT 對齊 · 矩陣 · 錯誤分群 · 性能分析 · 子系統同步 · 回滾 · 覆蓋率 · 修序 · 進度 · 說明 · 部署 · 證據雜湊)在 PS20 **一條都沒有**。結論:兩本冊不是同一層——PS20 是**資料面車道**(抓取 → 快取 → 結構 → 計算 → 查詢),VIA_ACCEL25 是**治理面加速器**;只有 18/19/21/22/23/24 六條重疊。所以不是「二選一」也不是「合併成一本」,是**兩層各一本**:PS20 宜登記為 25 冊 #19(多引擎整合)之下的資料面子冊。這是裁定,寫成 Z107,不代做。

## 三 · VDF↔VRN 對接點 ↔ 母倉正典對表(膠囊 §七 第二條)

| 姊妹倉件 | 講什麼 | 母倉正典 | 對得上嗎 | 差在哪 |
|---|---|---|---|---|
| `functional modules/VDF/engine/VDF_PricesCanonical.py`(517 行;冊 `config/ssot/VDF_PricesFactorRegistry.candidate.json`,registration_state **candidate**;表 `prices_canonical` **32 欄**:raw_/adj_ OHLC · adj_factor · volume_ex_daytrade · trading_value_ex_daytrade · no_trade_confirmed · validation_status · year;22 條欄別名;零網路;帶 ACCEL+NET 橋;測試 `functional modules/VDF/tests/test_VDF_PricesFactorIntegration.py` 12 測) | 調整價正典**候選** | `VDF_ENG060_AdjPriceLayer` v0104:表 `tw_prices_adj` / `gl_prices_adj`(ticker/date/open/high/low/close=adj/volume/factor/data_class)+ **視圖** `prices_canonical`(批178 正典取數視圖;`VDF_ENG061` 唯一輸入;`VRN_ENG069`/`ENG070` 取 close;`VAP_ENG009` 要它) | **同名不同形** | 母是 9 欄視圖,姊妹是 32 欄表(多 raw_*、除當沖量值、no_trade、validation);寫進同一庫撞名(view vs table)= Hydra。附帶量到:`VIA_DB_Table_SSOT_v0100.json` 把 `prices_canonical` 記成**表**且 writers 空(rows_seen 2,128,168 與 `tw_prices_adj` 同數 = 視圖),`tw_prices_adj` writers 也空(其實是 ENG060)→ 冊要補(Z106) |
| `VDF_FactorLibrary.py`(708 行;長表 `factor_values` 22 欄:factor_id/version/formula_id/input_hash 血緣;只吃 prices_canonical;活動量一律 ex-daytrade;TA-Lib provider 受能力冊閘) | 因子庫候選 | `VDF_ENG061_FeatureStore` v0102(寬表 `features_daily`,唯一輸入 prices_canonical 視圖)+ TA-Lib OneEngine 橋(批520) | 同源不同形 | 母寬表、姊妹長表;姊妹的「除當沖量」母 `tw_prices_adj` 沒有(成交值在 `tw_trading_daily`/ENG057,當沖在 ENG055 L15 車道)|
| `src/lib/via/digest-four.ts` | 一題四點 P1 上漲空間 = 目標價(`exdiv.ts` 除權息調整)× VDF adj close;`ADJ_CLOSE_CACHE` **寫死 5 檔**(2330/2317/2454/2303/2637,2026-08-27,src VDF_CACHE) | `VRN_ENG080_FourPointDigest` v0109:K1 最新 adj close 取 `tw_daily_prices` 最後交易日;TP_adj = TP × F(F = (adj/close)@報告日 ÷ @最新日);票不在價表 / 無 adj_close = 不算、不拿 close/共識頂替 | 邏輯同、料不同 | 母走活庫,姊妹走寫死快取(Console 展示);姊妹 `opts.adj` 的形狀 {date, adj, src} 可由母 ENG080 `price_context` 供給——要接是 Console 讀母庫,不是母樹改 |
| `src/lib/via/vrn-field-cache.ts` | 57 欄財報欄位 TWSE / TWS / YF 三碼對照(yf 鍵唯一 55) | `VDF_ENG082_FinStatements` v0102(三大報表擷取;yfinance 欄名 0 處 = 用自家欄名)· `SUP_MDL749` 六欄規則正本樞紐(研報六欄,不是財報欄)· `VIA_SSOT_SynonymUnion`(同義字聯集 ≈1,430 葉) | 無對應 | 母樹沒有「TWSE ↔ yfinance 財報欄」對照冊;57 欄是候選收容件——只增不減:收進 `references/intake` 或作 ENG082 的別名冊(Z108)|
| `src/lib/via/vdf-prices-factor.ts` | Console 對候選冊的投影(契約 ok = datasets.prices_canonical.table == "prices_canonical" …) | `VIA_DB_Table_SSOT_v0100.json`(53 張 VDF 表)· `VDF_Param_Registry_v0100.json`(678 參數) | 部分 | 同一件事(表契約)兩本冊;姊妹冊自標 candidate,母冊是 SSOT |

## 四 · 橋(膠囊 §四 在母樹的唯讀實測,本線只複核不重跑)

ACCEL 橋 RESOLVED → `supportive modules/VIA_SuperAccel_Module.py` → `SUP_MDL737_SuperAccelModule_v0105`;NET 橋 → `network/via_net_unified_v0101.py`——與本線 d 批 `VDF_SystemManager launch` ④ 量到的同一對。姊妹倉兩支 VDF 引擎在無 duckdb / pandas / pyarrow 的境橋 graceful(`VIA_ACCEL=None`、`_via_net()` 回 None),與母 VDF 啟動就緒的判準一致:境缺 = ABSENT,不是壞;啟動鏈行為不變,不代設 CONSENT。

## 五 · 掛著(接續 Z105 → Z106–Z108;Z67 的 VRN 對表是 VRN session 的,不重複登)

- Z106 `prices_canonical` 同名不同形(母 ENG060 視圖 9 欄 vs 姊妹候選表 32 欄):裁哪個是正典;DB 表冊補「VIEW by ENG060」與 `tw_prices_adj` writers;姊妹引擎要進母樹就先改名(或改成寫 `tw_prices_adj` 的上游)。
- Z107 PS20 ↔ 25 冊:兩層各一本,PS20 登記為 #19 之下的資料面子冊?母樹 48 支 `.ps1` 要不要真的注入 `$VIAPS20`(L70)?
- Z108 57 欄 TWSE / YF 財報對照:收容(`references/intake`)或作 ENG082 別名冊。

## 六 · 給姊妹倉 session 的回話(它收不到,寫在這)

收到 §四 / §七。做了:對照表(二)、對接點對表(三)、橋複核(四);沒做:不抄引擎、不注入、不餵探針(一)。你這邊要改的只有一件:`VDF_PricesFactorRegistry.candidate.json` 的表名 `prices_canonical` 在母庫是 ENG060 的視圖,候選表要改名或改層(Z106)。

## 七 · 指標

姊妹倉 PR #23 `https://github.com/tonykuni/VIA-VDF-VRN/pull/23`(head `c1989e618c`;膠囊 `docs/VIA_VRN_HANDOVER.md`;驗證矩陣 `docs/VIA_BRIDGE_AND_VRN_PANORAMA.md`)· 母倉本線:`VIA_S20260921d_VDFLaunch.md`(啟動就緒)· `VIA_DroppedBalls_B507.md`(A · Z67 · Z68 · Z106–Z108)。
