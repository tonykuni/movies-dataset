# VCGC / VDF 實擷盤點(容器 · 2026-10-05)

依操作員令「實測出資料盤點無誤才算成功」。資料家:容器 scratchpad `real_20261005/vdf_fetch`(資料不進 git)。
跑法:`via-vcgc run --family vdf VDF_MDL012_FetchGroups run --groups … --home <家>`(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 只在該條命令開)→ `monitor`。

## 判定:容器端 **PARTIAL**(不是成功)

| 族群 | 表 | 列數 | 最新日 | 燈 | 說明 |
|---|---|---|---|---|---|
| SHIPPING | 8 張(AkShare) | 44,823 | 2026-09-29 | GREEN 5 · YELLOW 3 | YELLOW = 來源本身月頻 / 週頻落後(LPI 62 天、WCI 15 天),非擷取錯 |
| TW_PRICE_VOL | tw_daily_prices | 586,004 | 2026-10-02 | GREEN | TPEX 892 檔全到;**TWSE 被 WAF 擋 → 0**(上市部分缺) |
| TW_PRICE_VOL | tw_trading_daily | 444,994 | 2025-03-26 | RED | e057 全量回補中被整輪 3000 秒上限截斷(未完成,不是資料錯) |
| SENTIMENT | cnn_fear_greed(e229) | 1,563 | 2026-10-02 | 已落庫 | OK |
| SENTIMENT | sentiment_daily(e115)· aaii(e116) | — | — | NODATA | 引擎 DENY:「only via Invoke-VIAPython」= 只准工作站 PS 路徑(設計如此) |
| US_MACRO | us_macro(e074 / e113) | — | — | NODATA | FRED_API_KEY 未設 → SKIP / DENY(不空轉) |

## 要工作站補的(容器做不到)

1. `TWSE`:工作站網路跑 e054 / MDL009(容器出口被 WAF 擋)。
2. `FRED`:`via-fred --fred-key <你的 key>` 後跑 US_MACRO。
3. `SENTIMENT`:工作站 `via-sentiment` / `via-aaii`(Invoke-VIAPython 路徑)。
4. `tw_trading_daily`:e057 單獨跑完回補(不設整輪上限)。
5. 跑完 `via-monitor` 回貼:四族群全 GREEN / 合理 YELLOW 才轉成功。

## 交叉驗證用途

TPEX 實抓名單(892)已用來驗 `TaiwanStockGroup.json` 的市場別(修 9 支)。
