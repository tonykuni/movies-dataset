# VDF 缺漏檢查 · 2026-11-10(對照操作員貼上的「台股資料擷取完整矩陣 · VDF CentralHub」T1–T5)

只讀檢查(grep 尾版引擎,排除 intake / references / 測試);不改任何 VDF 檔。VDF 由 VDF 自己的 manager 修(L122)。

| 表 | 矩陣要求 | VDF 現況(尾版家族) | 判定 |
|---|---|---|---|
| T1 stock_list | ticker · name · market · yf_ticker | `VDF_MDL009_TWStockList` v0102:date · ticker · yf_ticker · bloomberg_ticker · name · market · industry | 有 |
| T1 stock_list | isin_code · listing_date · par_value · **shares_issued** · capital | MDL009 **沒存**。上市日期 / 面額 / 已發行股數 / 實收資本在 MDL009 已抓的 t187ap03_L / O 裡就有,只是沒留;ISIN 要另抓 isin.twse.com.tw | **缺(高)** —— shares_issued 是 T5 持股率的分母 |
| T2 index_daily | 加權 / 櫃買 OHLC · 量 · 值 · 漲跌 | `VDF_ENG232_TWIndexOfficial` v0101(增量)· ENG099 同日對齊 | 有 |
| T3 stock_price | OHLCV raw + adj_close(auto_adjust=False)+ adj O/H/L | `VDF_ENG060_AdjPriceLayer`(adj_factor = adj_close / close)· AdjPrice_Rule_SSOT v0100 | 有 |
| T4 chip_daily | T86 / 3i 三大法人 · MI_MARGN / TPEX 融資券 · TWTB4U 當沖 · ROC 日期 | `VDF_ENG056_ChipBackfill` · ENG055 OmniFetch · ENG092 | 有 |
| T5 derived | 融資維持率 · 券資比 | ENG052 / ENG056 有計算;ENG098 欄 `margin_maint_pct` · `short_margin_ratio` | 有 |
| T5 derived | **三大法人持股率** fi / it / dt_hold_pct(淨買賣超累積 ÷ shares_issued)· inst_total_pct | ENG098 / ENG099 **只消費**欄 `foreign_holding_pct` · `trust_holding_pct` · `dealer_holding_pct`;倉內**沒有任何引擎產生**這三欄(搜 hold_pct / cumsum / cum_shares = 0) | **缺(高)** |
| 外資持股 | MI_QFIIS 官方外資持股比 | 尾版引擎 0 支用到 | 缺(中)—— 可作 fi_hold_pct 的官方對照 |

## 建議(待操作員核可;VDF 自己出新版號檔,不就地改)
1. `VDF_MDL009_TWStockList` v0103 薄尾:t187ap03 已抓的列多留 listing_date · par_value · shares_issued · capital;ISIN 另一源。
2. 新引擎(VDF 編號由 VCGC 發):三大法人持股率 = 淨買賣超自起始日 cumsum ÷ shares_issued;外資用 MI_QFIIS 官方值對帳;輸出接 ENG098 現有欄名(不改 ENG098)。

## 附帶查核
- Markdown 模組:倉內只有 intake 參考件(`Invoke-VIA-MarkItDown-v0101.ps1` · `MarkdownEditingEngine_v1.2.0`),未啟用;容器無 `markitdown` 套件。SVG 本身是文字(XML),上傳後可直接讀,不需轉檔。
- 操作員提到的 5 張 SVG 在桌機 `OneDrive\Pictures\Camera Roll\`,容器讀不到 —— 需上傳。
