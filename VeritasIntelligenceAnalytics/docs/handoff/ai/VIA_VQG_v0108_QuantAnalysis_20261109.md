# VQG v0108 · 新增指標與量化分析(操作員 2026-11-09「VQG VAP VCGC 一併順勢完成 · VQG 可能有增加指標 · 量化分析內容以增加」)

規格依據:`VIA_AgentOS_SuperPrompt_v2.0_20261108.md` §B `/quant-roll`:動態 rolling CRITERIA · 台債 10y 為 rf · 乾淨資金流動比排除當沖與 2330 非當沖扭曲 · 禁硬編碼靜態值。
四系統對等(L123):只動 VQG 自己的檔;VAP 一字不動(只實測它吃不吃得下);VCGC 只登冊 / 編號 / 閘。

## 一、VQG v0108 = v0107 薄尾(v0107 一字不改 · SHA 釘住 · 公式引擎仍 v0104 三解)

| 指標 | stable_id | 單窗 | S1 | S2 | S3 | 要的輸入欄 |
|---|---|---|---|---|---|---|
| obv | VQG.IND.OBV | 20 | n 日 OBV 增量(股) | 增量 / n 日總量(−1..1) | 乾淨量(扣當沖) | volume(S3 另要 daytrade_volume / clean_volume) |
| atr | VQG.IND.ATR | 14 | Wilder 平滑 | 簡單均 | ATR / 收盤(fraction) | high · low |
| clean_flow_ratio | VQG.IND.CLEAN_FLOW_RATIO | 20 | 乾淨量 n 日均 / 前 n 日均 | 乾淨成交值 | 中位數比 | daytrade_volume(或 clean_volume)· turnover |
| rolling_sharpe | VQG.IND.ROLLING_SHARPE | 60 | (均報酬 − rf 日化) / 標準差 | 均 / 標準差(不年化) | Sortino | rf_annual(台債 10y;rf 日化用序列自己近一年交易日數推,不寫死 252) |
| rel_strength | VQG.IND.REL_STRENGTH | 60 | 票 − 基準 n 日報酬 | (1+r)/(1+r_b)−1 | 票 − 2330 因子序列 | benchmark_adj_close + benchmark_market(S3 另要 factor_adj_close) |

缺輸入一律 null + 原因,不補不猜。欄名對照新增 high / low / rf_annual / factor_adj_close(v0105 load_series 只載認得的欄)。
export-vap 預設指標:sma rsi macd → + volatility drawdown obv atr clean_flow_ratio rolling_sharpe rel_strength(window_plan 25 組 · 75 列 ≤ v0104 上限 100)。

## 二、量化分析(有加工 · 給其他應用 · 不登 VAP 來源)

export-vap 跑完後讀 `indicators/<票>` + `series/<票>`,每張票出 `analysis/<票>.json`,全部票 `vqg_quant_analysis.parquet / .csv / .json`:
趨勢(價 vs SMA 20/60/120 → ALL_ABOVE / MIXED / ALL_BELOW)· 動能(RSI 14 + 自身歷史百分位 · MACD 柱符號與連續日數)· 波動(VOL 20 百分位 · 五分位)· 回撤(DD 60)·
真實波幅 %(ATR S3 百分位)· 量能方向(OBV S2)· 乾淨資金流動比 · Sharpe(超額 rf / raw)· Sortino · 相對強弱(基準 / 2330 因子)· `missing_inputs` · `lamp`。
門檻全部來自序列自己的歷史分布;只有定義性常數(RSI 50 · 柱 0 · 價 vs 均)。
寫完重生 `SHA256SUMS.txt`(含新檔)· `export_receipt.json` 與 `VIA_Reports/vqg/VQG_ExportVAP_latest.json` 加 `analysis` 節。

## 三、本輪實測(容器 2026-11-09)

- `VQG_AllInOne_v0108.py selftest`:**本版 12/12 + v0107 鏈 PASS**(含 v0105 全部)· 全景(token read)**0 報** · chain:v0108 → v0107 → v0105 → v0104。
- 真 VDF 夾具(2 批次 · 2 票 · high/low/volume 有,當沖 / rf / 基準欄無):`export-vap --indicator-points 60` **rc 0**;⑤ 10 指標 · 一票一表 2(VAP 閘過 2)· 快照 150 列;量化分析 2 票 **YELLOW**(缺 DAYTRADE / RF / BENCHMARK 三欄 → 照實列)。
- **VAP v0302** `--config <新匯出>/VAP_AllInOne_v0300.config.json`:`/api/health` READY · catalogTables 4 · 0 errors;`/api/catalog` 含 OBV_20_S1 / ATR_14_S3 / ROLLING_SHARPE_60_S2 欄;quant_analysis 不在目錄(照設計)。VAP 契約(`VIA_VQG_to_VAP_Contract_20261106.md`)不變。

## 四、還沒綠的 · 誰的手

| 項 | 現況 | 手 |
|---|---|---|
| clean_flow_ratio · obv S3 | null(VDF 日線沒 daytrade_volume / clean_volume) | VDF 線出欄(VDF 自己的版本) |
| rolling_sharpe S1 | null(沒 rf_annual = 台債 10y) | VDF 線出 rf 序列 |
| rel_strength | null(沒 benchmark_adj_close / benchmark_market;S3 另要 factor_adj_close = 2330) | VDF 線出基準 / 因子欄 |
| VQG / VAP 進 L122 治理器 | `CGC_MDL270_RegistryGovernor_v0106` SUBS = (VCGC, VDF, VRN),VDF / VRN 路徑在 4 處硬編碼 → 要出 v0107 薄尾改四處;憲法矩陣 VQG / VAP 仍 YELLOW NOT_IN_L122_GOVERNOR | 操作員 W2 裁後 AI 出薄尾 |
| 桌機真 VDF 庫 | 容器只有夾具 | 桌機:`python "functional modules\VQG\VQG_AllInOne_v0108.py" export-vap`(庫根照 VDF 冊或 `$env:VQG_VDF_ROOT`)→ VAP v0302 `--config` |
