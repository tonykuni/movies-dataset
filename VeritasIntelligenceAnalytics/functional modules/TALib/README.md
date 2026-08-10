# VIA TALib — TA-Lib 技術指標引擎(Adj 鐵律)

2026-08-11 歸檔(操作員令:new engine · 有 adj close 全部轉 adj,缺才用一般價)。

## Adj 鐵律(引擎讀 VAP SSOT `vap_spec.json` price 節,零寫死)

- `adj_close` 在位 → **全部 OHLC × (adj/close)**、volume ÷ factor(split 慣例)、
  provenance `price_basis="adj"`、圖表標題掛 **" (adj)"** 後綴
- 缺席 → 一般價 + `price_basis="raw"` 誠實標示(fallbackWhenNoAdj)
- selftest 內嵌 1:2 分割樣本驗證:adj 價量跨分割**連續**、factor 0.5↔1.0 正確

## 指標:64 型(原生 numpy 60 · Hilbert 4 型誠實 talib_only)

分類對照 `ssot/talib_indicators_classification.md`(12 類 + 轉折點基準):
趨勢(SMA/EMA/DEMA/TEMA/KAMA)· 動量(RSI/STOCH/STOCHF/STOCHRSI/WILLR/CCI/CMO/
MOM/ROC×3)· 量能(OBV/AD/ADOSC/MFI)· 波動(ATR/NATR/TRANGE/BBANDS/STDDEV/VAR)·
價格×4 · MACD×3 · 方向(ADX/ADXR/DX/±DI/±DM)· 極值×5 · SAR×2 · 統計(CORREL/
BETA/SUM)· K線型態×10(錘子/刺透/晨星/烏雲/暮星…)。
RSI/ATR/ADX 用 Wilder 原典平滑;`talib` C 庫在位時 `--backend talib` 直用
(selftest 自動交叉核對,缺席誠實 SKIP)。

## 動詞

```powershell
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 talib probe
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 talib sample -o ohlcv.csv
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 talib compute --file ohlcv.csv --indicators rsi,macd,bbands --out ind.csv
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 talib signals --file ohlcv.csv
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 talib chart --file ohlcv.csv --out ta_charts
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 talib selftest
```

資料檔收 .csv/.tsv/.json/.sqlite/.duckdb;欄名別名自動對位(含中文)。
`signals` 依 SSOT 轉折點基準出旗標(**訊號≠建議**);`chart` 經 VAP 圖庫出
K線/RSI/MACD 三面板(標題誠實帶 price_basis)。

## 本容器驗收(2026-08-11)

selftest **10 PASS / 1 SKIP(talib 未安裝) / 0 FAIL**:SMA/EMA 精確值、RSI 極端
方向、MACD 恆等式、BBANDS 恆等式、TRANGE 手算、**adj 鐵律含分割與 raw 後備**、
型態構造樣本、全譜 compute+signals、Hilbert 誠實、registry 對照 SSOT。
chart 三面板成品親眼驗證:D180 分割點價量連續、" (adj)" 後綴在位。

## docs/

兩份 TA-Lib 參考 PDF(14 頁/19 頁)依上傳脈絡原樣歸檔;容器缺 PDF 工具未逐頁
驗讀,誠實註記。兩份上傳 MD 逐位元相同,歸一份為 ssot。
