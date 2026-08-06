# VIA｜資料抓取總登記表（Data Fetch Registry）v001

Generated: 2026-07-05
用途：一次列出風險引擎 9 維度（D1–D9）＋計分規格＋附錄 A/B 待補＋VDF v003 P0 所需的**全部外部資料**，按來源分類。
入庫：VIA_TWChip_Warehouse（DuckDB + Parquet、Hive 分區、ledger 去重、raw-response audit、append-only、UTF-8 No-BOM）。
標記：**Feeds**=餵哪個維度；**Freq**=頻率；**Tier**=T1 真值/T4 代理；**Cost**=Free/Gated；**Pri**=P0 先做。

---

## 0. 優先級總覽

| Pri | 範圍 | 解鎖 |
|---|---|---|
| **P0** | TWSE T86 / MI_MARGN / MI_INDEX + TAIFEX 期貨 + FRED 就業/利率；20 交易日窗涵蓋 6/23–6/26 | D1/D2/D4 升 V、D6/D7 可算 |
| P1 | 個股價量、估值 BWIBBU、零股、AkShare 北向、ICI、yfinance 指數/ETF | D8a/D9、D8c 三角 |
| P2 | EPFR/NSDL/KRX/日銀/HKEX、社群流量、政府基金 | D8b/c 完整、D3/D5 建管線 |

---

## 1. TWSE 證交所（上市）— Free · T1

| Dataset | Code | Fields | Feeds | Freq | Pri | Notes |
|---|---|---|---|---|:--:|---|
| 三大法人買賣超(個股) | **T86** | 外資/投信/自營 買賣超(張·金額) per stock | D2 | 日 | P0 | raw 原始回應+錯誤碼必存；0 rows 必修 |
| 三大法人買賣金額(大盤) | **BFI82U** | 三大法人買/賣/合計金額 | D2 | 日 | P0 | 6/24 −2,102 億驗證 |
| 外資及陸資買賣超彙總 | **TWT38U** | 外資買賣超彙總 | D2 | 日 | P0 | 6/24 −1,774 億、6/26 −1,432 億驗證 |
| 融資融券餘額 | **MI_MARGN** | 融資買/賣/現償/餘額、融券，個股+大盤 | D1 | 日 | P0 | 兩市 8,134.8 億驗證 |
| 大盤收盤行情/統計 | **MI_INDEX** | 加權指數 OHLC、漲跌家數、成交值 | D4 | 日 | P0 | 窗必涵蓋 6/23/24/26 |
| 每日成交量值 | **FMTQIK** | 成交股數/金額/筆數/指數 | D4 | 日 | P1 | 量能 |
| 個股日成交 | **STOCK_DAY** | OHLCV per stock | D4/D9 | 日 | P1 | 僅日 OHLC；台積電**盤中高低需另源** |
| 個股 PER/PBR/殖利率 | **BWIBBU_d** | PER、PBR、殖利率 per stock | D9 | 日 | P1 | 估值 |
| 盤後零股 | **TWTASU** | 零股成交金額/量 | D1 | 日 | P1 | 散戶代理 710.7 億 |
| 外資持股/集保 | **MI_QFIIS** | 外資持股比率 | D2 | 日 | P2 | 輔助 |

> ⚠️ 缺口：**台積電/個股盤中(intraday)高低**——TWSE 日檔只有日 OHLC，真 intraday 需盤中即時或券商 feed（附錄 A A005 的 2,525/2,535 爭議即因此）。

---

## 2. TPEx 櫃買中心（上櫃）— Free · T1

| Dataset | Endpoint | Fields | Feeds | Freq | Pri | Notes |
|---|---|---|---|---|:--:|---|
| 三大法人買賣超(櫃買) | 依修正 swagger slug | 外資/投信/自營 OTC | D2 | 日 | P0 | 用 Warehouse 已校正 slug |
| 融資融券(櫃買) | 依修正 swagger slug | 櫃買融資餘額 | D1 | 日 | P0 | 2,084.4 億驗證 |
| 櫃買指數 | 依修正 swagger slug | TPEx index OHLC、漲跌家數 | D4 | 日 | P0 | |
| 個股日成交(櫃買) | 依修正 swagger slug | OHLCV | D4/D9 | 日 | P1 | 小型股廣度 |
| 外資買賣超(獨立表) | 依修正 swagger slug | TPEx 外資淨買超 | D8 | 日 | P1 | FIS 櫃買 T4→T1 真值源 |

> TPEx 各表**確切 API slug 以 VIA_TWChip_Warehouse 已對 swagger 修正的版本為準**，此處僅列資料集名稱，避免寫死錯誤 slug。

---

## 3. MOPS 公開資訊觀測站 — Free

| Dataset | Fields | Feeds | Freq | Pri | Notes |
|---|---|---|---|:--:|---|
| 月營收 | 營收、YoY、MoM per company | D9/產業(E1–E4) | 月 | P1 | 產業預測層 |
| 財務報表 | 損益/資產/現金流 | D9/產業 | 季 | P2 | forward 基本面 |
| 董監持股/質押 | insider holdings、質押比 | D2(輔) | 月 | P2 | 大戶行為輔證 |
| 重大訊息 | material info | event | 事件 | P2 | 事件旗標 |

> ⚠️ **政府基金/八大行庫/國安基金部位 NOT on MOPS**——見 §7「無標準 API」清單（D5 缺口）。

---

## 4. yfinance — Free · 指數/ETF/殖利率/FX

| Ticker/Type | Fields | Feeds | Freq | Pri | Notes |
|---|---|---|---|:--:|---|
| 指數 `^TWII ^TWOII ^GSPC ^DJI ^IXIC ^NDX ^SOX ^RUT ^KS11 ^N225 ^HSI ^GDAXI ^FTSE ^NSEI ^STOXX50E` | OHLCV | D4/D6/D8 | 日 | P1 | 全球指數 |
| FIS ETF `0050.TW 006208.TW 006201.TW SPY IVV VOO QQQ DIA IWM EEM VWO IEMG EWY EWG EWJ INDA MCHI FXI ASHR EWU VGK EWT` | shares_outstanding、NAV、close、volume | D8 | 日 | P1 | **NetFlow=ΔShares×NAV**；shares_out 常延遲/不全→須 issuer/ICI 對帳 |
| 個股 `2330.TW MU` | OHLCV、forwardPE、priceToBook | D9/D6 | 日 | P1 | forward 指標品質有限 |
| 殖利率 `^TNX(10Y) ^FVX(5Y) ^TYX(30Y) ^IRX(13w)` | yield | D7 | 日 | P1 | **2Y 無直接 ticker → 用 FRED DGS2** |
| FX `USDTWD=X DX-Y.NYB(DXY)` | rate | D7/D8 | 日 | P1 | FX 調整 |

> ⚠️ FIS 最弱環節＝ETF **shares_outstanding**；低覆蓋率(3–11%)時「隱含總流」會爆（中國 −1.5 兆案例）→ 需 winsorize + 覆蓋率閘（計分規格 R1/R3）。

---

## 5. FRED — Free（需 API key）· 美國總經/利率

| Series ID | Name | Feeds | Freq | Pri | Notes |
|---|---|---|---|:--:|---|
| **PAYEMS** | 非農就業 | D6 | 月 | P0 | 含修正軌跡 |
| **UNRATE** | 失業率 U-3 | D6 | 月 | P0 | 假下降偵測 |
| **CIVPART** | 勞動參與率 LFPR | D6 | 月 | P0 | 61.5% 崩 |
| **EMRATIO** | 就業人口比 E/P | D6 | 月 | P0 | 59.0% |
| **U6RATE** | U-6 | D6 | 月 | P1 | |
| **RSAFS / RSXFS** | 零售銷售(名目/ex-auto) | D6 | 月 | P1 | 名目 vs 實質背離 |
| **CPIAUCSL / CPILFESL** | CPI / 核心 CPI | D6/D7 | 月 | P0 | 4.2% 三年高 |
| **FEDFUNDS / DFEDTARU / DFEDTARL** | 有效利率 / 目標區間上下限 | D7 | 日 | P0 | 3.50–3.75% |
| **DGS2 DGS5 DGS10 DGS20 DGS30 DGS3MO** | 公債殖利率曲線 | D7 | 日 | P0 | **2Y 在此** |
| **T10Y2Y** | 10Y−2Y 利差 | D7 | 日 | P1 | 曲線倒掛 |
| **UMCSENT** | 密大消費者信心 | D6 | 月 | P1 | 5 月 44.8 歷史低 |

> ⚠️ **ISM PMI 已自 FRED 下架**（NAPMPI 僅歷史）→ 見 §7 用 ISM 官網/PR。BLS **收件率**非 FRED series → 見 §7 BLS OSMR。

---

## 6. AkShare — Free · 中國真值源

| Function（約定名） | Data | Feeds | Freq | Pri | Notes |
|---|---|---|---|:--:|---|
| `stock_hsgt_north_net_flow_in` / `stock_hsgt_hist` | 北向資金(滬股通/深股通)淨流 | D8c | 日 | P1 | **取代 MCHI ETF 隱含流的偏誤**（WEAK-tier 三角） |
| `stock_zh_index_daily` | 滬深300 等指數 OHLC | D4/D8 | 日 | P1 | |
| A 股融資融券(可選) | 兩融餘額 | D8c 輔 | 日 | P2 | |

---

## 7. Other — 真值源、gated、無標準 API

| Source | Data | Feeds | Access | Pri | Notes |
|---|---|---|---|:--:|---|
| **TAIFEX 期交所** | 三大法人期貨/選擇權未平倉、**外資台指期淨空單**、大額交易人 | D2 | Free | **P0** | 83,605 口驗證 |
| **BLS API** | CES/CPS 原始、修正、**benchmark**；OSMR **收件率** | D6 | Free(key) | P0 | 收件率頁非 series，需另抓表 |
| **ISM** | 製造/服務 PMI + subcomponents(New Orders/Employment/Prices) | D6/D8 | Gated/PR | P1 | 官網/PR newswire；6 月服務 7/6 發布 |
| **ICI** | 美國週度基金流 | D8a | Free CSV | P1 | **FIS 美股 STRONG 真值源** |
| **Conference Board** | 消費者信心 CCI | D6 | Gated | P2 | |
| **UMich** sca.isr.umich.edu | 信心明細+通膨預期 | D6 | Free CSV | P2 | |
| **CFTC COT** | 商品/FX/公債期貨 positioning | D8c | Free | P1 | WEAK-tier 三角(商品/匯/債) |
| **NSDL/CDSL** | 印度 FII/DII 流 | D8c | Free/Gated | P2 | INDA 真值源 |
| **KRX** | 韓國外資淨買賣 | D8c | Free/Gated | P2 | EWY 真值源 |
| **日銀/投信協會** | 日本資金流 | D8c | Gated | P2 | EWJ 真值源 |
| **HKEX** | 港股 ETF/南向 | D8c | Free/Gated | P2 | HSI T4→T1 |
| **EPFR / IIF** | 全球/EM 基金與組合流 | D8 | **Paid/Gated** | P2 | 暫用 ETF 代理，標 gated |
| **LBMA / WGC** | 黃金流 | D8b | Free | P2 | Gold ETF 三角 |
| **on-chain / GBTC** | 加密淨流 | D8b | Free/API | P2 | Crypto 三角 |
| **社群/投顧流量** | 頻道觸及/轉貼/討論區聲量 | **D3** | Custom scrape | P2 | **無標準 API，須自建管線** |
| **國安基金/財政部/八大行庫** | 政府基金部位、成本 | **D5** | Disclosure/News | P2 | **無 API，揭露+推估，列假設不列事實** |

---

## 8. 來源 → 維度解鎖矩陣

| 維度 | 主來源 | 現況 | 抓到後 |
|---|---|---|---|
| D1 融資槓桿 | TWSE MI_MARGN、TPEx 融資、TWSE TWTASU | M | → V |
| D2 外資/籌碼 | TWSE T86/TWT38U/BFI82U、**TAIFEX** | M/部分V | → V |
| D3 社群情緒 | 社群/投顧流量(自建) | P | 建管線後才可算 |
| D4 廣度背離 | TWSE MI_INDEX/FMTQIK/STOCK_DAY、TPEx 指數 | M | → V |
| D5 政府基金 | 揭露/新聞(無API) | P | 只當假設 |
| D6 美國總經 | **FRED** + BLS + ISM + UMich | V | 已可算 |
| D7 Fed/利率 | **FRED**（含 DGS2） | V | 已可算 |
| D8 全球資金流 | yfinance ETF + ICI/AkShare/CFTC/NSDL/KRX… | X→ | 換真值源後 D8a→V、D8c 三角 |
| D9 估值錨 | TWSE BWIBBU、yfinance forward、MOPS | 部分V | → V |

---

## 9. 入庫與治理約定（每個抓取器共用）

- **Raw-response audit**：先存原始回應 + HTTP 狀態 + 錯誤碼，再解析（TWSE 0 rows 必留證）。
- **Append-only + ledger 去重**：以 (source, dataset, date, key) 為 ledger 主鍵，重跑不覆蓋。
- **Hive 分區**：`source=/dataset=/dt=YYYYMMDD` 存 Parquet；DuckDB 查詢層。
- **證據標記**：每列帶 `evidence_status`（Confirmed_Public / Estimated_ThirdParty_NeedsVerify / Synthetic）——投影/代理**不得標 Confirmed**（承 ingest.py 規則）。
- **20 交易日窗**：TTFI 窗必涵蓋 2026-06-23 / 06-24 / 06-26（目前停在 6/16，**P0 必修**）。
- **編碼**：輸出 UTF-8 No-BOM；CSV 用 UTF8BOM。

---

## 10. 立即可動（P0 清單）
1. TWSE：T86 / MI_MARGN / MI_INDEX（+ BFI82U / TWT38U）raw audit 版抓取器，窗推進到涵蓋 6/23–6/26。
2. TPEx：三大法人 / 融資 / 指數（用已校正 swagger slug）。
3. TAIFEX：外資台指期淨部位（83,605 口）。
4. FRED：PAYEMS / UNRATE / CIVPART / EMRATIO / CPI / FEDFUNDS / DFEDTARU-L / DGS2-30。
5. 全部進 Warehouse（raw→parquet→duckdb），跑 `verified` 與 `breadth_only` 兩分數。

> D3（社群）、D5（政府基金）無標準 API，列 P2 自建/揭露推估，**驗證前只當假設，不入 verified 分數**。
