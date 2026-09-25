# 當沖量值檔案收容夾(批522;律 L45 只收不掛線)

交易所的個股當沖量值頁面對 python 客戶端回 WAF 安全頁(TWSE rwd/TPEX 皆 302 Security Redirect);
openapi `exchangeReport/TWTB4U` 只有**標的冊**(Date/Code/Name/Suspension),沒有量值。
所以量值走**你的瀏覽器**:

1. TWSE 上市:https://www.twse.com.tw/zh/trading/day-trading/twtb4u.html → 選日期 → 「全部」→ 下載 CSV
2. TPEX 上櫃:https://www.tpex.org.tw/zh-tw/mainboard/trading/info/day-trading.html → 選日期 → 下載 CSV
3. 把 CSV(或 JSON)放進本夾(檔名含日期最好,如 `TWTB4U_20260912.csv` / `tpex_daytrade_20260912.csv`),或直接:
   `via-daytrade --from-file A.csv,B.csv --date 2026-09-12`
4. 跑 `via-daytrade`(= ENG055 run --lane L15):先試線上三源(誠實),再收本夾內尚未收過的檔 → `tw_daytrade_stock`
5. `via-quantguard status` 看 QuantGuard/SSOT；把已治理的調整後 OHLCV Parquet 明確交給 `via-quantguard run --in <檔> --out <夾>` → 量能指標只用扣當沖量值(L41)

冊 `_ingested.json` 記已收檔(檔名:大小);同檔不重收。本夾內容不入 git(只留本 README)。
