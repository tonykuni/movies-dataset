# VIA Taiwan Active ETF Consensus UI v001

## 交付內容

- `index.html`：純 HTML 結構。
- `styles.css`：完整響應式 CSS。
- `app.js`：資料聚合、ETF 勾選、篩選、排序、Adapter JSON 載入及匯出。
- `VIA_Taiwan_Active_ETF_Consensus_Standalone.html`：CSS／JavaScript 全部內嵌，Windows 雙擊即可開啟。

## 核心功能

1. 五頁籤：績效矩陣、ETF 清單、持股 × Consensus、動作分類、資料請求。
2. ETF 勾選後重新計算 AUM 加權持股及持有廣度。
3. FactSet／YFinance Target Low、Mean、Median、High 分欄顯示。
4. FactSet EPS N、N+1、N+2 與 Forward P/E。
5. Portfolio Forward P/E 使用加權 Earnings Yield，不直接平均個股 P/E。
6. 支援搜尋、族群、品質及資料來源篩選。
7. 支援欄位排序及 CSV／JSON 匯出。
8. 可載入 `VETF_ConsensusEnrichment_Adapter_v001.py` 產生的 JSON Array 或 `{ "records": [...] }`。
9. 響應式電腦／平板／手機版面及列印樣式。

## Adapter JSON 最低欄位

```text
analysis_date
etf_code
ticker
company_name
holding_weight
price_adj_close
fs_target_low / mean / median / high
yf_target_low / mean / median / high
fs_eps_n_mean / fs_eps_n1_mean / fs_eps_n2_mean
record_status
quality_flags
```

缺失欄位會顯示 `—`，不會以零值冒充正式共識資料。

## 驗證結果

- React／TypeScript ESLint：PASS。
- Standalone JavaScript Syntax：PASS。
- Standalone Build Script Syntax：PASS。
- Standalone HTML：無重複 ID、必要節點齊全。
- Standalone CSS／JavaScript：全部內嵌，沒有外部 CDN 相依。

畫面內建數字明確標記為 `DEMO SNAPSHOT`；載入 Adapter JSON 後改為 `LOADED CANDIDATE`。正式資料仍須通過 P0／P1 Gate。
