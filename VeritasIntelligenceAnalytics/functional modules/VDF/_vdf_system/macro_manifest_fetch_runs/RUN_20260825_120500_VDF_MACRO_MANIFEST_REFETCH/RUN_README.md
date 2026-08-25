# RUN_20260825_120500_VDF_MACRO_MANIFEST_REFETCH — 批136 宏觀清單再擷取

**操作員令(批136,2026-08-25):「fetch vdf data again」** — 前次資料擷取
RUN_20260617_001157 之同轉接器、同正典清單再跑(遠端受管容器實網)。

## 結果(誠實三態)

| 項 | 值 |
|---|---|
| 清單 | VIA_data_manifest.json(registry 正本 md5 同一;62 序列) |
| OK_FETCHED | **53/55 自動源**(yfinance 31/31·FRED 22/24) |
| FAIL_FETCH | 2 — FRED `NAPM`/`NMFBAI` 404(ISM PMI 授權下架=歷史既存缺,0617 run 同缺) |
| WARN(設計內) | manual/vendor 5 skip·derived 2 pending(轉接器既定行為) |
| 覆蓋 | 1990-01-02 → **2026-08-25**(市場日線至 08-24/25;FRED 月頻至 2026-07-01=正常滯後) |
| 形狀 | RawWide/TransformedWide 7124×53;RawLong 352,157 列(0617=349,035;**+3,122 觀測**) |
| 欄位 | 與 0617 run 53 欄完全同集(零增零減) |

## 與 RUN_20260617 之差異

1. **單趟直跑** — 非 3-round panorama 閘流程,故無 `consolidated/` 重複層;
   產物全在 `outputs/`。
2. **轉接器零改寫** — `VDF_ManifestFetchAdapter.py` 為 0617 byte-identical 快照。
3. **代理 TLS 自適應** — 容器出網經 TLS 再終結代理,curl_cffi 瀏覽器擬真
   握手遭重置;`proxy_session_driver.py` 向統包網路工具(SUP_MDL740 v0104)
   取無擬真 session 注入 yfinance(同意閘 VIA_NET_CONSENT 先行,fail-closed)。
4. **FRED** — 無 FRED_API_KEY,走轉接器 fredgraph.csv 後備道(200 直達)。

## 檔案

- `proxy_session_driver.py` — 本次驅動器(閘檢+session 注入+轉接器調用)
- `outputs/VDF_MacroFetchStatus.{csv,json}` — 62 序列逐筆誠實狀態
- `outputs/VDF_MacroFetchSummary.json` — 總結存證
- `outputs/VDF_Macro{Raw,Transformed}{Wide,Long}.{csv,json,parquet}` — 資料本體
- `logs/driver.{stdout,stderr}.txt` — 全程日誌
