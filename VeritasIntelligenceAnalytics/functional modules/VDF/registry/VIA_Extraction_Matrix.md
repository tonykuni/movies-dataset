# VIA 擷取資料矩陣(只增不減)


## A · 全球指數流 (Index FIS)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 1 | 美股大盤 | S&P500 ^GSPC/SPY · 道瓊 ^DJI/DIA · 那斯達克100 ^NDX/QQQ · 羅素2000 ^RUT/IWM | ICI 週度 + ETF 創贖 | 日 | Y(ICI+創贖) | T1 | 指數 FIS 方向/強度 |
| 2 | 台股大盤 | 加權 ^TWII/0050 · 櫃買 ^TWOII/006201 | TWSE T86 + 創贖 | 日 | Y | T1/T4 | 指數 FIS |
| 3 | 亞洲 | 日經 ^N225/EWJ · 韓 ^KS11/EWY · 港 ^HSI/2800.HK · 中 000300/MCHI/ASHR · 印 ^NSEI/INDA | EPFR/北向AKShare/NSDL/日銀 | 日 | Y | T1/T4 | 指數 FIS |
| 4 | 歐洲 | DAX ^GDAXI/EWG · FTSE ^FTSE/EWU · STOXX50 ^STOXX50E/VGK | EPFR | 日 | Y | T1 | 指數 FIS |
| 5 | 新興市場 | MSCI EM EEM/VWO/IEMG | EPFR/IIF | 日 | Y | T1 | 指數 FIS |

## B · ETF FIS 宇宙 (依風險層 ~70檔)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 6 | T0 防禦/低波 | SHV·BIL·AGG·BND·TLT · USMV·SPLV · GLD | 創贖/issuer AUM | 日 | Y | T1 | risk_tier FIS |
| 7 | T1 核心市值 | SPY·VOO·IVV·VTI·QQQ·DIA·IWM | 創贖/AUM | 日 | Y | T1 | 市場β FIS |
| 8 | T2 產業/主題 | XLK·SMH·XLE… · BOTZ·ARKK·ICLN·LIT | 創贖 | 日 | Y | T1 | 主題β FIS |
| 9 | T2 區域/國別 | EWT·EWJ·EWY·MCHI·INDA·EEM | 創贖 | 日 | Y | T1 | 區域β FIS |
| 10 | T4 槓桿/反向 | TQQQ·SQQQ·SOXL·SOXS·UPRO·SPXU·UVXY | 創贖 | 日 | Y | T4 | 高波動(部位) |

## C · 台股族群 & 個股流 (核心)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 11 | 族群分類 | 31 群(v1.0×24 + v1.1×7)L/P/G | File1 族群分類 SSOT | — | Y(只增不減errata) | SSOT | grouping 骨架 |
| 12 | 個股角色 | 百餘檔 Leader/Peer/Laggard(hot/lead/chg) | File1 + VDF 計算 | 日 | Y | T1/T4 待VDF | 個股下鑽層 |
| 13 | 法人買賣超($) | 三大法人 | TWSE T86 | 日 EOD | Y | T1 | 族群流方向(當沖免疫) |
| 14 | Δ融資餘額 | 逐檔融資 | TWSE MI_MARGN | 日 EOD | Y | T1 | 族群流(當沖免疫) |
| 15 | 個股→族群上捲 | Σ主動ETF持股增減 × File1 | 主動ETF PCF + grouping | 日 | Y | T1 | 主動資金族群流(真值) |

## D · 台股主動式ETF & 選股 (展現層)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 16 | 主動ETF清單 | 25 檔 00980A…00423A(末碼A股票型) | TWSE 主動式ETF專頁 | 日 | Y | T1 | 展現(不入訊號測試) |
| 17 | 績效 Matrix | 7 horizon 1/5/10/20/60/120/240日 | 收盤 adj | 日 | N | T1 | 績效排行 |
| 18 | 持股異動/選股 | NEW/加碼/減碼/出清/持平 | TWSE 每日投組 PCF | 日 | Y | T1 | 選股→族群上捲(接C) |
| 19 | 規模/受益人數 | 日變動 | 投信投顧公會 | 日/週 | Y | T1 | 主動資金流真值 |

## E · 全球商品流 (現貨/期貨/供給/庫存/成本)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 20 | 能源-原油 | WTI/Brent USO·BNO·USL·DBO;現貨 FRED DCOILWTICO/DCOILBRENTEU | ETF創贖 + CFTC COT + EIA | 日/週 | Y(3源並存) | T1/T4 | 商品FIS+基本面 |
| 21 | 能源-氣/汽油 | 天然氣 UNG(DHHNGSP)· 汽油 UGA | 創贖 + EIA週儲(週四)+ COT | 日/週 | Y | T1/T4 | 商品FIS |
| 22 | 貴金屬 | 金 GLD/IAU(LBMA/COMEX)· 銀 SLV · 白金鈀 PPLT/PALL | 創贖 + COT + 倉儲/持金噸數 | 日 | Y | T1 | 商品FIS |
| 23 | 工業金屬 | 銅 CPER/COPX(LME/COMEX/SHFE)· 基本金屬 DBB · 鈾 URA · 鋰 LIT | 創贖 + COT + 倉儲 | 日/週 | Y | T1/T4 | 商品FIS |
| 24 | 農產 | 黃豆 SOYB · 玉米 CORN · 小麥 WEAT · 廣基農 DBA | 創贖 + COT + USDA WASDE | 日/週/月 | Y | T1/T4 | 商品FIS |
| 25 | 廣基/商品股 | DBC·PDBC·GSG · 金礦 GDX · 能源股 XLE | 創贖 + COT | 日 | Y | T1 | 商品FIS |
| 26 | 碳權/運費(新增) | 碳權 KRBN · 波羅的海運價 BDI/BDRY | 創贖 + Baltic Exchange | 日 | Y | T1/T4 | 實體流動代理 |
| 27 | 供給/庫存/成本 | EIA產量·Cushing庫存 · OPEC MOMR · LME/LBMA倉儲 · USDA · roll/儲存/邊際成本 | EIA/OPEC/LME/USDA | 週/月/日 | Y | T1/T4 | 基本面疊加 |

## F · 加密資產 (Crypto)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 28 | 主要幣 | BTC(主導~56%)·ETH·XRP·SOL·… 依市值 | CoinGecko/CMC 市值主導率 | 日/即時 | Y | T1 | 加密方向 |
| 29 | 現貨ETF創贖/持幣 | BTC IBIT/FBTC/GBTC · ETH ETHA/FETH · SOL · XRP XRPC/GXRP · LTC LTCC | Farside / issuer 持幣量 | 日 | Y | T1 | 加密FIS(當沖/roll免疫) |
| 30 | 穩定幣 | USDT · USDC | 市值/鏈上 | 即時 | Y | T1 | 現金等價(排除方向流) |

## G · 美股指數分族群進出

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 31 | SPX→11 GICS | XLK·XLV·XLF·XLY·XLC·XLI·XLP·XLE·XLU·XLRE·XLB | sector ETF 創贖/FIS | 日 | Y | T1 | 分族群進出(真實) |
| 32 | DJI→成分族群 | 30 成分(價格加權)依 sector | 成分 NetFlow | 日 | Y | T4 待接 | 分族群進出 |
| 33 | NDX→Mag7/類股 | Mag7 vs 其餘 IT/Comm/ConsDisc | 成分 / QQQ 權值 | 日 | Y | T4 待接 | 分族群進出 |

## H · 資金品質指標 (TWSE)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 34 | 融資使用率 | 槓桿浮額 | MI_MARGN + 融資限額 | 日 | Y | T1 | 品質(高=散戶槓桿) |
| 35 | 融資維持率 | 整戶擔保維持率 <130% 追繳 | 衍生:融資成本基礎 vs 現價 | 日 | Y | 衍生估計 | 品質脆弱度(非原生欄位) |
| 36 | 券資比 | 融券/融資 | MI_MARGN | 日 | Y | T1(漏SBL) | 品質(兩側槓桿+軋空) |
| 37 | 當沖比 | 當沖值/總值 | TWSE 每日當日沖銷統計 | 日 | Y | T1 | data-quality 折扣權重 |
| 38 | 借券賣出 SBL | 法人空方 | TWSE/TDCC 借券 | 日 | Y | T1 | 補券資比漏的法人空 |

## I · 情緒/風險指標 (新增)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 39 | ^VIX 隱含波動 | VIX spot | CBOE | 即時/日 | Y | T1 | risk-off 溫度 / RORO |
| 40 | VIX 期限結構 | VIX/VIX3M · VVIX | CBOE | 日 | Y | T1 | contango/backwardation |
| 41 | AAII 散戶多空 | Bull/Bear/Neutral % | AAII 週報(週四) | 週 | Y | T1 | 散戶情緒(反指) |
| 42 | CNN Fear & Greed | 7 分量複合指數 | CNN(可拆 7 分量) | 日 | Y(拆分量) | T1 | 綜合情緒 |
| 43 | Put/Call Ratio | 總量/指數/個股 | CBOE | 日 | Y | T1 | 選擇權情緒 |
| 44 | NAAIM/II 投顧情緒 | 專業部位/多空 | NAAIM / Investors Intelligence | 週 | Y | T1 | 專業情緒(對照散戶) |
| 45 | MOVE 債券波動(新增) | MOVE index | ICE BofA | 日 | Y | T1 | 債市 risk-off 溫度 |
| 46 | MMF 場邊現金(新增) | 貨幣市場基金總資產 | ICI 週報 | 週 | Y | T1 | 場邊現金真值(RORO) |

## J · 宏觀數據 (政府 vs 民間差異,新增)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 47 | PMI 製造/服務 | 官方 vs 民間 | 中 NBS官方 / Caixin民間 · 美 ISM / S&P Global | 月 | Y(官vs民並存) | T1 | 景氣 + 官民差異 |
| 48 | CPI 通膨 | 官方 vs 民間即時 | BLS官方 / Truflation · Cleveland Fed Nowcast · MIT BPP | 月/日 | Y(官vs民) | T1 | 通膨 + 官民差異 |
| 49 | PPI 生產者 | 官方 | BLS | 月 | Y | T1 | 生產者通膨 |
| 50 | 官民差異指標 | 官方 − 民間 | 計算(只增不減保留兩源) | 月 | Y | 衍生 | 數據品質/領先訊號 |
| 51 | 宏觀因子 | 利率/DXY/殖利率曲線/信用利差 | FRED | 日 | Y | T1 | 接全球sim RISK/USD/INFL/GEO |
| 52 | 進出口/貿易(新增) | 台灣出口訂單·出口值(AI供應鏈領先) · 各區貿易差額 | 財政部/經濟部 · 各國海關 | 月 | Y | T1 | 拉動因子:基本面領先 |
| 53 | 央行資產負債表(新增) | Fed 總資產 WALCL(QE/QT) · ECB/BOJ B/S | FRED / 各央行 | 週 | Y | T1 | 推動因子:全球流動性供給 |

## K · AUM 多來源計算 (並存,新增)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 54 | 法1 現貨ETF | AUM = Σ(shares × NAV) | issuer/創贖 | 日 | 並存 | T1 | AUM 真值 |
| 55 | 法2 期貨ETF | AUM = 持倉 × 價 | issuer | 日 | 並存 | T1 | AUM |
| 56 | 法3 holdings-sum | Σ(成分 × 價) | holdings 明細 | 日 | 並存 | T1 | AUM 交叉驗證 |
| 57 | 法4 issuer 申報 | 官方申報 AUM | issuer 官方 | 日 | 並存 | T1 | AUM 基準 |
| 58 | 一致性檢查 | 四法差異 → 一致性/勘誤 | 計算(只增不減保留各法) | 日 | Y | 衍生 | 多源一致性 QA |

## M · 債券 公債/公司債 (各區域,新增)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 59 | 存續期梯(美公債) | SHV·BIL(T-bill)· SHY(1-3y)· IEF(7-10y)· TLT(20y+)· GOVT(全)· TIP/VTIP(抗通膨) | ETF創贖 + ICI債券流 | 日/週 | Y | T1 | 利率曲線資金流 |
| 60 | 信用層(美) | 投等 LQD·VCIT·VCSH · 高收 HYG·JNK · 銀行貸款 BKLN · 可轉債 CWB | ETF創贖 + HY/IG OAS 確認 | 日 | Y(流×利差同向確認) | T1 | 信用風險偏好 |
| 61 | 區域-國際/歐 | BNDX(國際綜合)· IGOV(國際公債)· 歐 IG | ETF創贖 + EPFR | 日/週 | Y | T1 | 區域債流 |
| 62 | 區域-新興 | 硬通貨 EMB vs 當地貨幣 EMLC · 新興公司 CEMB | ETF創贖;EMB/EMLC 相對流=美元壓力 | 日 | Y(硬vs當地並存) | T1 | EM 債流+USD壓力 |
| 63 | 公債需求端真值 | 標售 bid-to-cover · indirect bidders% · Fed H.4.1 custody(週)· TIC(月,滯後)· primary dealer 部位 | US Treasury / NY Fed / FRED | 週/月 | Y(4源並存) | T1 | 外國/官方需求 |
| 64 | 美債期貨 positioning | ZT/ZF/ZN/ZB 管理基金淨部位 | CFTC COT | 週五(至週二) | Y | T1 | 債券版法人買賣超 |
| 65 | 台灣債券ETF | 00679B 元大美債20年 等(被動末碼B·主動末碼D) | TWSE/TPEX 規模·受益人·創贖 | 日 | Y | T1 | 台灣散戶美債流(兆級) |
| 66 | 信用利差確認 | HY OAS(BAMLH0A0HYM2)· IG OAS(BAMLC0A0CM) | FRED | 日 | Y | T1 | 流向確認閘 |

## N · 匯率/利率/利差/股市吸引力 (新增)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 67 | 美元指數 | DXY(ICE)· 廣義美元 FRED DTWEXBGS | FRED / ICE | 日 | Y | T1 | USD regime 因子 |
| 68 | 各區匯率 | USDJPY·EURUSD·USDTWD·USDCNY·USDKRW·USDINR | FRED / 各央行 | 日 | Y | T1 | FX 壓力 |
| 69 | 央行政策利率 | Fed·ECB·BOJ·台CBC·PBOC·BOK·RBI | 各央行 + BIS policy rates | 會期/月 | Y(BIS彙整並存) | T1 | 利率水位 |
| 70 | 利差 carry | 政策利差 vs Fed · 2Y/10Y 主權利差 vs US | FRED 殖利率系列 | 日 | Y | T1 | carry 流因子 |
| 71 | 指數 forward earnings | 各主要指數 fwd EPS/盈餘 | FactSet(付費) ∥ Yardeni·指數商factsheet(免費代理) | 週/月 | Y(付費/免費並存) | T1 | 估值分子 |
| 72 | Forward P/E 轉換 | fwdPE = Σ市值/Σfwd盈餘(=價格/fwdEPS) | 計算(市值口徑) | 日 | Y | 衍生 | 估值 |
| 73 | 股市吸引力 | E/P(=1/fwdPE) − 當地10Y;跨區相對 vs US | 計算 | 日 | Y | 衍生 | 流向預測因子(ERP proxy) |
| 74 | 三因子合成 | 吸引力 × 利差 × USD → 實測IC加權入 fusion | harness E3 | 日 | Y | 衍生 | 接 measured-weight fusion |

## L · 真值/交叉驗證源 (彙總)

| # | 小項目 | 標的/代碼 | 來源 | 頻率 | 多源 | 證據 | 用途 |
|---|---|---|---|---|---|---|---|
| 75 | 台股源 | TWSE(T86/MI_MARGN/當沖/PCF)· TDCC集保 · 投信投顧公會 · 北向 AKShare | 官方/公會 | 日 | Y | T1 | 台股真值池 |
| 76 | 美股/全球源 | ICI週度 · EPFR/IIF · FRED · EIA · CFTC COT · USDA WASDE · LBMA/WGC · LME · OPEC MOMR | 官方/機構 | 日/週/月 | Y | T1 | 全球真值池 |
| 77 | 情緒/加密源 | CBOE(VIX/PutCall)· AAII · CNN · NAAIM · Farside(crypto) | 官方/供應商 | 日/週 | Y | T1 | 情緒/加密真值池 |
