# VIA VDF FETCH ONE · VDF-390 擷取總冊(SSOT 收容存證)

> 收容存證(批104,2026-08-23):操作員核定原文,收容原樣零改寫。儲存維護並遵守。
> 附令(原文,含手機錯字保留):「台股個股自動清鮮京待驗證 台股主動式etf清單攻心自動驗種維書
> header: Date tickrt / yfinence ticker ./ bloomberg ticker . name . opem low high close volume turnover /
> 三大法人賣賣超 / 融資融券/券資比/融資維持率 / 融券維持率 / 當沖交易 / 當沖比
> yfinance抓Date yfinance ticker / namr / close / adj close / volume 然後資仄串成一行
> 加權指數/櫃買指數都用twse/ tpex 存另一資料庫」
> 判讀(檔內對讀用):台股個股自動清單=待驗證;台股主動式 ETF 清單=自動驗證維護;
> 個股日表 header=Date·ticker·yfinance_ticker·bloomberg_ticker·name·open·low·high·close·volume·turnover·
> 三大法人買賣超·融資融券·券資比·融資維持率·融券維持率·當沖交易·當沖比;
> yfinance 抓 Date·yfinance_ticker·name·close·adj_close·volume 後與前者串成同一行;
> 加權指數/櫃買指數用 TWSE/TPEX 官方源,存另一資料庫。
> 結構化對映:VDF_FetchOne_Matrix_Registry_v0100.json(ENG046 機器轉錄);
> 行表 schema:VDF_TWEquity_DailyRow_Schema_v0100.json。

---

## yfinance價格 · 股/ETF/指數

	PX-01	
台股上市 OHLCV + 籌碼
TWSE	vdf_fetchers_market	日	
open · high · low · close · adjClose · volume · 三大法人
22 · 25 · 29	✓ DONE
	PX-02	
台股上櫃 OHLCV + 籌碼
TPEX	vdf_fetchers_market	日	
同上
22 · 25	✓ DONE
	PX-03	
全球股票/ETF OHLCV+Adj
YFINANCE	vdf_fetchers_market	日	
open…adjClose · volume · splitRatio
21 · 28 · 70	✓ DONE
	PX-04	
全球指數總表(所有下列指數彙整)
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume · chgPct
42 · 61 · 70	✓ DONE
	PX-04A	
美國 ^GSPC ^DJI ^IXIC ^RUT ^NDX
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume · breadth
42 · 61	✓ DONE
	PX-04B	
美國類股 ^SOX ^SOXX ^BKX ^XAU ^DJT
YFINANCE	vdf_fetchers_market	日	
close · adjClose · relStrength
61 · 14	✓ DONE
	PX-04C	
台灣 ^TWII ^TWOII ^NTX 台灣50
TWSE + YFINANCE	vdf_fetchers_market	日	
close · volume · 法人買賣超
25 · 42	✓ DONE
	PX-04D	
日本 ^N225 ^TOPX 東證核心30
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49 · 61	✓ DONE
	PX-07A	
日本股市 · 指數群全量
YFINANCE + JPX	vdf_fetchers_market	日	
N225 · TOPIX · TOPIX Core30 · Mothers · JASDAQ · JPX400 · close · adjClose · volume
49 · 61	✓ DONE
	PX-07B	
日本股市 · 東證 33 業種指數
JPX	vdf_fetchers_market	日	
sectorIndex ×33 · close · volume · relStrength
49 · 61	📡 PROXY
	PX-07C	
日本股市 · 外資買賣超與投資部門別
JPX 投資部門別	vdf_fetchers_market	週	
foreignNet · individualNet · trustNet · dealerNet
49 · 66	📡 PROXY
	PX-07D	
日本股市 · 個股量價(TOPIX 成分)
YFINANCE (.T)	vdf_fetchers_market	日	
open…adjClose · volume · 逐檔
49 · 22	✓ DONE
	PX-07E	
日本股市 · 空單餘額與信用交易
JPX	vdf_fetchers_market	週	
shortBalance · marginBalance · ratio
49 · 68	📡 PROXY
	PX-08A	
韓國股市 · 指數群全量
YFINANCE + KRX	vdf_fetchers_market	日	
KOSPI · KOSPI200 · KOSDAQ · KRX100 · close · adjClose · volume
49 · 61	✓ DONE
	PX-08B	
韓國股市 · KRX 業種指數
KRX	vdf_fetchers_market	日	
sectorIndex · close · volume · relStrength
49 · 61	📡 PROXY
	PX-08C	
韓國股市 · 外資與機構買賣超
KRX	vdf_fetchers_market	日	
foreignNet · institutionNet · individualNet · byTicker
49 · 66	📡 PROXY
	PX-08D	
韓國股市 · 個股量價(半導體重點)
YFINANCE (.KS/.KQ)	vdf_fetchers_market	日	
005930 · 000660 等 · open…adjClose · volume
49 · 61	✓ DONE
	PX-08E	
韓國 · 半導體出口與晶片景氣連動
關稅廳 + KRX	vdf_fetchers_derived	月·日	
chipExportYoY · kospiSemiIdx · correlation
49 · 61	📡 PROXY
	PX-04E	
中國 ^SSEC ^SZSC 滬深300 創業板
YFINANCE + AKSHARE	vdf_fetchers_market	日	
close · volume · northboundFlow
49 · 66	✓ DONE
	PX-04F	
香港 ^HSI 恆生科技 國企
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49 · 66	✓ DONE
	PX-04G	
韓國 ^KS11 ^KQ11
YFINANCE	vdf_fetchers_market	日	
close · adjClose · foreignFlow
49 · 61	✓ DONE
	PX-04H	
歐洲 ^STOXX50E ^GDAXI ^FCHI ^FTSE ^IBEX ^SSMI
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49	✓ DONE
	PX-04I	
印度 ^NSEI ^BSESN
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49 · 14	✓ DONE
	PX-04J	
東南亞 ^STI ^KLSE ^SET ^JKSE ^VNINDEX ^PSI
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49	✓ DONE
	PX-04K	
澳紐 ^AXJO ^NZ50
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49 · 4C	✓ DONE
	PX-04L	
加拿大 ^GSPTSE · 墨西哥 ^MXX
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49	✓ DONE
	PX-04M	
拉美 ^BVSP ^MERV ^IPSA
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49	✓ DONE
	PX-04N	
中東 ^TASI ^ADI ^TA125
YFINANCE	vdf_fetchers_market	日	
close · adjClose · volume
49	📡 PROXY
	PX-04O	
新興市場 ^MSCIEF ^MSCIWORLD ACWI
MSCI(ETF 代理)	vdf_fetchers_market	日	
close · adjClose · regionWeight
49 · 66	📡 PROXY
	PX-04P	
指數本地幣 vs 美元計價報酬
VDF 推導(指數 × FX)	vdf_fetchers_derived	日	
localRet · usdRet · fxEffect
49 · 61	✓ DONE
	PX-05A	
區域指數 ETF 對照 · 美國
YFINANCE	vdf_fetchers_market	日	
SPY · VOO · IVV · QQQ · DIA · IWM · nav · aum · units
65 · 66	✓ DONE
	PX-05B	
區域指數 ETF 對照 · 歐洲
YFINANCE	vdf_fetchers_market	日	
VGK · EZU · FEZ · EWG · EWU · EWQ · nav · aum · units
65 · 49	✓ DONE
	PX-05C	
區域指數 ETF 對照 · 日本 / 韓國
YFINANCE	vdf_fetchers_market	日	
EWJ · DXJ · BBJP · EWY · nav · aum · units
65 · 49	✓ DONE
	PX-05D	
區域指數 ETF 對照 · 中國 / 香港 / 台灣
YFINANCE + TWSE	vdf_fetchers_market	日	
MCHI · FXI · KWEB · ASHR · EWH · EWT · 0050 · nav · aum · units
65 · 49	✓ DONE
	PX-05E	
區域指數 ETF 對照 · 印度 / 東南亞
YFINANCE	vdf_fetchers_market	日	
INDA · INDY · EWS · EWM · THD · EIDO · VNM · nav · aum · units
65 · 49	✓ DONE
	PX-05F	
區域指數 ETF 對照 · 新興 / 全球 / 拉美 / 中東
YFINANCE	vdf_fetchers_market	日	
EEM · VWO · ACWI · VT · EWZ · EWW · KSA · EIS · nav · aum · units
65 · 49	📡 PROXY
	PX-05G	
區域指數 ETF 對照 · 澳加
YFINANCE	vdf_fetchers_market	日	
EWA · EWC · nav · aum · units
65 · 49	✓ DONE
	PX-06A	
行業指數 · 美國 GICS 11 大類
S&P(FRED 代理)	vdf_fetchers_market	日	
sectorIndex ×11 · close · relStrength
61 · 65	✓ DONE
	PX-06B	
行業 ETF · SPDR 11 大類
YFINANCE	vdf_fetchers_market	日	
XLK · XLF · XLV · XLE · XLI · XLY · XLP · XLU · XLB · XLRE · XLC · nav · aum · units
61 · 65 · 66	✓ DONE
	PX-06C	
行業 ETF · 科技細分主題
YFINANCE	vdf_fetchers_market	日	
SMH · SOXX · IGV · CIBR · SKYY · ARKK · BOTZ · ROBO · nav · aum · units
61 · 65	✓ DONE
	PX-06D	
行業 ETF · 金融 / 醫療 / 工業細分
YFINANCE	vdf_fetchers_market	日	
KRE · KBE · IBB · XBI · IHI · ITA · JETS · XHB · nav · aum · units
61 · 65	✓ DONE
	PX-06E	
行業 ETF · 能源 / 原物料 / 公用細分
YFINANCE	vdf_fetchers_market	日	
XOP · OIH · AMLP · XME · LIT · COPX · URA · TAN · ICLN · nav · aum · units
4C · 65	✓ DONE
	PX-06F	
行業指數 · 台股 29 類股
TWSE	vdf_fetchers_market	日	
sectorIndex · close · volume · 法人買賣超
25 · 61	✓ DONE
	PX-06G	
行業輪動相對強弱矩陣
VDF 推導(Adj)	vdf_fetchers_derived	日	
sector×period · relStrength · rank · zscore
61 · 70	✓ DONE
	PX-05	
費城半導體指數 ^SOX 成分與權重
YFINANCE + issuer	vdf_fetchers_market	日	
member · weight · close
61 · 14	✓ DONE
	PX-06	
波動度族(VIX VVIX MOVE SKEW)
Yahoo	vdf_fetchers_market	日	
close
61 · 68	✓ DONE
	PX-07	
日內走勢 + 分鐘量
YFINANCE 1m/5m	vdf_fetchers_market	分	
ts · price · volume
26 · 27	✓ DONE
	PX-08	
K 線技術族(SMA/EMA/BB)
VDF 推導	vdf_fetchers_derived	日	
sma · ema · bbUpper · bbLower(基於 Adj)
27	✓ DONE

## 商品 · 現貨/期貨

	CM-01	
Brent 原油 現貨 + 期貨
YFINANCE(BZ=F) + EIA	vdf_fetchers_market	日	
spot · front · M2 · basis
4C · 42 · 70	✓ DONE
	CM-02	
WTI 原油 現貨 + 期貨
YFINANCE(CL=F) + EIA	vdf_fetchers_market	日	
spot · front · M2 · basis
4C · 42	✓ DONE
	CM-03	
黃金 現貨 + 期貨
YFINANCE(GC=F)	vdf_fetchers_market	日	
spot · front · basis
4C · 44	✓ DONE
	CM-04	
貴金屬(銀/白金/鈀)
YFINANCE	vdf_fetchers_market	日	
close · adjClose
4C	✓ DONE
	CM-05	
工業金屬(銅/鋁/鎳)
YFINANCE + AkShare	vdf_fetchers_market	日	
close
4C · 14	✓ DONE
	CM-06	
大宗農產(玉米/小麥/黃豆)
YFINANCE	vdf_fetchers_market	日	
close
4C	✓ DONE
	CM-07	
BDI 波羅的海乾散貨
AKSHARE	vdf_fetchers_macro	日	
index
4C · 42	✓ DONE
	CM-08	
SCFI 上海出口貨櫃
AKSHARE	vdf_fetchers_macro	週	
index
4C	✓ DONE
	CM-09	
天然氣 / 電價
YFINANCE + EIA	vdf_fetchers_market	日	
close
4C · 14	✓ DONE
	CM-10	
黃金 ETF(實物 + 礦業)
YFINANCE + issuer	vdf_fetchers_etf_holdings	日	
GLD · IAU · SGOL · GLDM · GDX · GDXJ · nav · aum · units · tonnesHeld
4C · 65 · 66	✓ DONE
	CM-11	
白銀 · 白金族 ETF
YFINANCE + issuer	vdf_fetchers_etf_holdings	日	
SLV · SIVR · PPLT · PALL · nav · aum · units · ozHeld
4C · 65	✓ DONE
	CM-12	
原油 ETF(WTI / Brent / 油服)
YFINANCE + issuer	vdf_fetchers_etf_holdings	日	
USO · BNO · UCO · XLE · XOP · OIH · nav · aum · units · rollSchedule
4C · 65 · 66	✓ DONE
	CM-13	
天然氣 · 能源綜合 ETF
YFINANCE	vdf_fetchers_etf_holdings	日	
UNG · BOIL · AMLP · nav · aum · units · rollCost
4C · 65	✓ DONE
	CM-14	
綜合商品 ETF(廣基)
YFINANCE + issuer	vdf_fetchers_etf_holdings	日	
DBC · PDBC · GSG · COMT · nav · aum · units · weightByCommodity
4C · 65	✓ DONE
	CM-15	
工業金屬 · 農產 ETF
YFINANCE	vdf_fetchers_etf_holdings	日	
CPER · COPX · JJC · DBA · CORN · WEAT · SOYB · nav · aum · units
4C · 65	✓ DONE
	CM-16	
商品 ETF 實物持有量(噸/桶/盎司)
issuer 每日揭露	vdf_fetchers_etf_holdings	日	
tonnes · barrels · ounces · Δholdings
4C · 66	✓ DONE
	CM-17	
商品 ETF 淨流入 / 流出
Δunits × NAV	vdf_fetchers_derived	日	
netFlowUSD · Δunits · cumFlow · byCommodity
66 · 4C	✓ DONE
	CM-18	
原油庫存(商業 · Cushing · SPR)
EIA 週報 + API	vdf_fetchers_market	週	
commercialCrude · cushing · spr · gasoline · distillate · API 前一日
4C · 42	✓ DONE
	CM-19	
原油供給(美國產量 · OPEC+ 配額)
EIA 週報 + OPEC MOMR	vdf_fetchers_market	週·月	
usProduction · opecQuota · opecOutput · complianceRate
4C	📡 PROXY
	CM-20	
原油需求與平衡表
IEA OMR + EIA STEO	vdf_fetchers_macro	月	
globalDemand · supplyDemandBalance · oecdStocks · 需求端 ~60% 運輸
4C	📡 PROXY
	CM-21	
鑽井平台數與頁岩成本
Baker Hughes + EIA	vdf_fetchers_market	週	
rigCount · dutcBreakeven · permianBakkenCost
4C · 14	✓ DONE
	CM-22	
原油期貨曲線與轉倉排程
YFINANCE + CME	vdf_fetchers_market	日	
frontM1 · M2 · M3 · curveShape · rollDates
4C · 65	✓ DONE
	CM-23	
實體金屬倉儲與持有量
LBMA + LME + issuer	vdf_fetchers_market	日	
lbmaVault · lmeWarehouse · etfTonnes · 交叉驗證
4C · 65	📡 PROXY
	CM-24	
農產供需平衡(WASDE)
USDA WASDE	vdf_fetchers_macro	月	
production · endingStocks · stockToUse · exportSales
4C	✗ TODO
	CM-25	
商品 flow 代理 ETF × 價格基準對照
VDF 推導	vdf_fetchers_derived	日	
commodity · proxyEtf · priceBenchmark · isFuturesProxy · rollDecayFlag
4C · 65	✓ DONE

## 匯率 · 利率

	FX-01	
美元指數 DXY
YFINANCE	vdf_fetchers_market	日	
close
2A · 42 · 4C	✓ DONE
	FX-02	
主要匯率(EUR JPY GBP CNY TWD)
YFINANCE	vdf_fetchers_market	日	
close
2A · 43	✓ DONE
	FX-03	
美債殖利率曲線(1M–30Y)
Treasury / FRED	vdf_fetchers_fiscal	日	
tenor · yield
2C · 43	✓ DONE
	FX-04	
殖利率利差(10Y-2Y / 10Y-3M)
VDF 推導	vdf_fetchers_derived	日	
spread
2C · 42	✓ DONE
	FX-05	
隔夜利率(SOFR EFFR RRP)
FRBNY(FRED 代理)	vdf_fetchers_macro	日	
rate
2A · 45	📡 PROXY
	FX-06	
公司債信用利差(IG / HY OAS)
FRED	vdf_fetchers_macro	日	
oas
61 · 68	✓ DONE
	FX-07	
TIPS 實質利率 + 通膨補償
FRED	vdf_fetchers_macro	日	
real · breakeven
45 · 4C	✓ DONE

## 美國總經 · 領先

	US-L01	
ISM 製造業 PMI(含分項)
ISM(FRED 代理)	vdf_fetchers_macro	月	
headline · newOrders · production · employment · prices
42 · 47	📡 PROXY
	US-L02	
ISM 非製造業 PMI(含分項)
ISM(FRED 代理)	vdf_fetchers_macro	月	
headline + 分項
42 · 47	📡 PROXY
	US-L03	
Markit / S&P Global PMI
S&P Global	vdf_fetchers_macro	月	
mfg · svc · composite
42	📡 PROXY
	US-L04	
ConfBoard LEI 領先指標
ConfBoard(FRED 代理)	vdf_fetchers_macro	月	
index · mom
42	📡 PROXY
	US-L05	
初領失業金 + 續領
DOL(FRED)	vdf_fetchers_macro	週	
initial · continuing · 4wma
42 · 48	✓ DONE
	US-L06	
建照 + 新屋開工
Census(FRED)	vdf_fetchers_macro	月	
permits · starts
42	✓ DONE
	US-L07	
耐久財新訂單(除運輸/資本財)
Census(FRED)	vdf_fetchers_macro	月	
total · exTransport · coreCapex
42	✓ DONE
	US-L08	
密大消費者信心 + 通膨預期
UMich(FRED 代理)	vdf_fetchers_macro	月	
sentiment · exp1y · exp5y
42 · 46	📡 PROXY
	US-L09	
ConfBoard 消費者信心
ConfBoard(FRED 代理)	vdf_fetchers_macro	月	
confidence · present · expect
42 · 46	📡 PROXY
	US-L10	
OECD CLI G7/G20
OECD(FRED 代理)	vdf_fetchers_macro	月	
cli
49	📡 PROXY
	US-L11	
ISM 製造業 10 分項全展開
ISM(FRED 代理)	vdf_fetchers_macro	月	
newOrders · production · employment · supplierDeliveries · inventories · customerInv · prices · backlog · exports · imports
42 · 47	📡 PROXY
	US-L12	
ISM 非製造業 9 分項全展開
ISM(FRED 代理)	vdf_fetchers_macro	月	
business · newOrders · employment · deliveries · inventories · prices · backlog · exports · imports
42 · 47	📡 PROXY
	US-L13	
地區 Fed 製造業調查(5 區)
Empire/Philly/Richmond/KC/Dallas	vdf_fetchers_macro	月	
general · newOrders · shipments · employment · pricesPaid
42	✓ DONE
	US-L14	
NFIB 小企業樂觀指數 + 分項
NFIB(FRED 代理)	vdf_fetchers_macro	月	
optimism · hiringPlans · capexPlans · pricePlans · uncertainty
42	📡 PROXY
	US-L15	
NAHB 房市指數 + 分項
NAHB(FRED 代理)	vdf_fetchers_macro	月	
hmi · presentSales · futureSales · trafficBuyers
42	📡 PROXY
	US-L16	
成屋 + 新屋銷售 · 庫存月數
NAR/Census(FRED)	vdf_fetchers_macro	月	
existingSales · newSales · monthsSupply · medianPrice
42	✓ DONE
	US-L17	
MBA 房貸申請 · 購屋/再融資
MBA	vdf_fetchers_macro	週	
purchaseIdx · refiIdx · rate30y
42	📡 PROXY
	US-L18	
消費者信心 8 分項對照(密大×ConfBoard)
UMich + ConfBoard(FRED)	vdf_fetchers_macro	月	
current · expect · buyCond · jobsPlentiful · jobsHard · incomeExp · exp1y · exp5y
42 · 46	📡 PROXY
	US-L19	
金融條件指數(NFCI · ANFCI)
Chicago Fed(FRED)	vdf_fetchers_macro	週	
nfci · anfci · riskSub · creditSub · leverageSub
42 · 61	✓ DONE
	US-L20	
銀行信貸緊縮 SLOOS
Fed SLOOS	vdf_fetchers_macro	季	
tighteningC&I · CRE · mortgage · consumer · demand
42 · 45	📡 PROXY
	US-L21	
運輸領先族(卡車噸位/鐵路裝載/ATA)
ATA/AAR(FRED 代理)	vdf_fetchers_macro	月	
truckTonnage · railCarloads · intermodal
42 · 4C	📡 PROXY
	US-L22	
半導體出貨 B/B + 全球銷售
SEMI / WSTS	vdf_fetchers_macro	月	
bookToBill · globalSales · yoy
61 · 14	✗ TODO

## 美國總經 · 同時

	US-C01	
實質 GDP + GDP 平減指數
BEA(FRED 代理)	vdf_fetchers_macro	季	
real · nominal · deflator
42 · 43	📡 PROXY
	US-C02	
GDP 恆等式四大組成(C I G NX)
BEA(FRED 代理)	vdf_fetchers_macro	季	
c · i · g · x · m · share
42	📡 PROXY
	US-C03	
非農就業新增 + 修正
BLS(FRED)	vdf_fetchers_macro	月	
nfp · private · revision
42 · 48	✓ DONE
	US-C04	
失業率 U3/U6 + 勞動參與率
BLS(FRED)	vdf_fetchers_macro	月	
u3 · u6 · lfpr · empPopRatio
42 · 48	✓ DONE
	US-C05	
失業持續期分布
BLS(FRED)	vdf_fetchers_macro	月	
<5w · 5-14w · 15-26w · 27w+
48	✓ DONE
	US-C06	
ADP 民間就業(民間數據對照)
ADP	vdf_fetchers_macro	月	
change
48	📡 PROXY
	US-C07	
職缺 JOLTS + 離職率
BLS(FRED)	vdf_fetchers_macro	月	
openings · quits · hires
48	✓ DONE
	US-C08	
平均時薪 + 週工時
BLS(FRED)	vdf_fetchers_macro	月	
ahe · awh · yoy
48	✓ DONE
	US-C09	
零售銷售 + 核心(control group)
Census(FRED)	vdf_fetchers_macro	月	
total · core · yoy
42 · 46	✓ DONE
	US-C10	
個人消費 PCE + 個人所得/儲蓄率
BEA(FRED 代理)	vdf_fetchers_macro	月	
pce · income · savingRate · yoy
42 · 46	📡 PROXY
	US-C11	
工業生產 + 產能利用率
FRB(FRED)	vdf_fetchers_macro	月	
ip · capacity
42	✓ DONE
	US-C12	
進出口 + 貿易餘額
Census/BEA(FRED)	vdf_fetchers_macro	月	
exports · imports · balance
42 · 43	✓ DONE
	US-C13	
GDP 貢獻度拆解(百分點)
BEA(FRED 代理)	vdf_fetchers_derived	季	
contribC · contribI · contribG · contribNX · inventoryEffect
42	📡 PROXY
	US-C14	
民間投資細分(住宅/設備/智財/存貨)
BEA(FRED 代理)	vdf_fetchers_macro	季	
residential · equipment · ip · structures · inventoryChange
42	📡 PROXY
	US-C15	
政府支出細分(聯邦國防/非國防/州與地方)
BEA(FRED 代理)	vdf_fetchers_macro	季	
fedDefense · fedNonDefense · stateLocal
42 · 43	📡 PROXY
	US-C16	
進出口細分(商品/服務 · 主要貿易夥伴)
Census(FRED)	vdf_fetchers_macro	月	
goods · services · byPartner · petroleumEx
42 · 43	✓ DONE
	US-C17	
零售銷售 13 分項
Census(FRED)	vdf_fetchers_macro	月	
motorVehicle · gasStation · food · building · health · clothing · eCommerce · furniture · electronics · sporting · general · misc · restaurants
42 · 46	✓ DONE
	US-C18	
PCE 三大類(耐久/非耐久/服務)
BEA(FRED 代理)	vdf_fetchers_macro	月	
durable · nonDurable · services + yoy
42 · 46	📡 PROXY
	US-C19	
非農就業 12 產業分項
BLS(FRED)	vdf_fetchers_macro	月	
mfg · construction · retail · leisure · health · professional · govt · transport · finance · info · mining · other
42 · 48	✓ DONE
	US-C20	
民間 vs 官方就業數據對照
BLS × ADP × 家戶調查	vdf_fetchers_derived	月	
nfp · adp · householdEmp · gap · diffusionIdx
48	✓ DONE
	US-C21	
廣義失業率(計入勞參率缺口)
VDF 推導	vdf_fetchers_derived	月	
u3 · u6 · adjU · lfprGap · missingWorkers
48	✓ DONE
	US-C22	
工業生產分項(製造/採礦/公用)
FRB(FRED)	vdf_fetchers_macro	月	
manufacturing · mining · utilities · hiTech · capacityByGroup
42	✓ DONE
	US-C23	
企業庫存與銷售比(製/批/零)
Census(FRED)	vdf_fetchers_macro	月	
invSalesRatio by 層級 · inventoryChange
42	✓ DONE
	US-C24	
消費信貸 + 循環/非循環
Fed G.19(FRED)	vdf_fetchers_macro	月	
revolving · nonRevolving · totalYoY
42 · 46	✓ DONE
	US-C25	
家庭債務與違約率(信用卡/車貸/學貸)
NY Fed HHDC	vdf_fetchers_macro	季	
balanceByType · delinquency30 · 90
42 · 46	📡 PROXY
	US-C26	
個人儲蓄率 + 可支配所得
BEA(FRED 代理)	vdf_fetchers_macro	月	
savingRate · dpi · realDPI
42 · 46	📡 PROXY
	US-C27	
汽車銷售年化 SAAR
BEA(FRED)	vdf_fetchers_macro	月	
totalSAAR · lightTruck · auto
42 · 46	✓ DONE
	US-C28	
貨幣供給 M1 M2 + 流通速度
Fed(FRED)	vdf_fetchers_macro	月	
m1 · m2 · velocity · yoy
42 · 45	✓ DONE

## 美國總經 · 落後 / 物價

	US-G01	
CPI + 核心 CPI(全分項)
BLS(FRED)	vdf_fetchers_macro	月	
headline · core + 8 大類分項 yoy · mom
42 · 47	✓ DONE
	US-G02	
PPI + 核心 PPI(分項)
BLS(FRED)	vdf_fetchers_macro	月	
final demand + 分項
42 · 47	✓ DONE
	US-G03	
PCE 物價 + 核心 PCE(分項)
BEA(FRED 代理)	vdf_fetchers_macro	月	
headline · core + 分項
42 · 47	📡 PROXY
	US-G04	
單位勞動成本 + 生產力
BLS(FRED)	vdf_fetchers_macro	季	
ulc · productivity
42	✓ DONE
	US-G05	
企業獲利(稅後)
BEA(FRED 代理)	vdf_fetchers_macro	季	
profits
42	📡 PROXY
	US-G06	
房價(Case-Shiller / FHFA)
S&P/FHFA(FRED)	vdf_fetchers_macro	月	
index · yoy
42	✓ DONE
	US-G07	
CPI 八大類全展開
BLS(FRED)	vdf_fetchers_macro	月	
food · energy · housing · apparel · transport · medical · recreation · education · other
42 · 47	✓ DONE
	US-G08	
CPI 關鍵細項(住房租金/OER/二手車/機票/醫療)
BLS(FRED)	vdf_fetchers_macro	月	
shelter · rentPrimary · OER · usedCars · newCars · airfare · medicalSvc · foodAway
42 · 47	✓ DONE
	US-G09	
CPI 切分(核心服務/核心商品/超級核心)
VDF 推導	vdf_fetchers_derived	月	
coreServices · coreGoods · superCore · exShelter
42 · 47	✓ DONE
	US-G10	
CPI 黏性 vs 彈性物價
Atlanta Fed(FRED)	vdf_fetchers_macro	月	
sticky · flexible · stickyExFood
47	✓ DONE
	US-G11	
PPI 產業鏈三階(原料/中間/最終)
BLS(FRED)	vdf_fetchers_macro	月	
crude · intermediate · finalDemand + 分項
42 · 47	✓ DONE
	US-G12	
PPI 服務 vs 商品分項
BLS(FRED)	vdf_fetchers_macro	月	
goods · services · trade · transportWarehouse · energyPPI
47	✓ DONE
	US-G13	
核心 PCE 分項(醫療/住房/金融服務)
BEA(FRED 代理)	vdf_fetchers_macro	月	
healthcare · housing · finSvc · marketBased · trimmedMean
42 · 47	📡 PROXY
	US-G14	
Trimmed Mean PCE + 中位數 CPI
Dallas/Cleveland Fed	vdf_fetchers_macro	月	
trimmedPCE · medianCPI · 16pctTrim
47	✓ DONE
	US-G15	
進出口物價指數
BLS(FRED)	vdf_fetchers_macro	月	
importPrice · exportPrice · exPetroleum
42 · 47	✓ DONE
	US-G16	
雇用成本指數 ECI + 亞特蘭大薪資追蹤
BLS + Atlanta Fed	vdf_fetchers_macro	季	
eciTotal · wages · benefits · wageTracker
47 · 48	✓ DONE
	US-G17	
單位勞動成本細分(製造/非農商業)
BLS(FRED)	vdf_fetchers_macro	季	
ulcMfg · ulcNonfarm · productivityByGroup
42	✓ DONE
	US-G18	
通膨預期(市場 × 調查)
FRED + UMich + NY Fed SCE	vdf_fetchers_derived	月	
breakeven5y · 5y5y · umich1y · sce1y · sce3y
45 · 47	✓ DONE
	US-G19	
企業獲利分項(金融/非金融/海外)
BEA(FRED 代理)	vdf_fetchers_macro	季	
financial · nonFinancial · rowProfits · margin
42	📡 PROXY
	US-G20	
破產與商業倒閉統計
AOUSC / Census	vdf_fetchers_macro	季	
ch7 · ch11 · businessExits
42	✗ TODO
	US-G21	
租金領先指標(Zillow/ApartmentList)
Zillow · ApartmentList	vdf_fetchers_macro	月	
newLeaseRent · yoy · leadShelterCPI
47	✗ TODO

## 財政 · 公債

	FI-01	
財政部日報 DTS 收支
Treasury FiscalData	vdf_fetchers_fiscal	日	
deposits · withdrawals · balance
43	✓ DONE
	FI-02	
財政部月報 MTS 收支明細
Treasury FiscalData	vdf_fetchers_fiscal	月	
receipts · outlays by 類別 · share
43	✓ DONE
	FI-03	
財政盈餘 / 赤字
VDF 推導(MTS)	vdf_fetchers_derived	月	
surplus · deficit · gdpRatio
43	✓ DONE
	FI-04	
聯邦債務餘額 + 債限
Treasury	vdf_fetchers_fiscal	日	
totalDebt · heldByPublic · limit
43	✓ DONE
	FI-05	
公債發行/標售 + 持有人結構
Treasury / TIC	vdf_fetchers_fiscal	月	
issuance · bidCover · holders
43	✓ DONE
	FI-06	
主權評等 + 展望(三大機構)
Rating agencies	vdf_fetchers_fiscal	事件	
agency · rating · outlook · asof
43	✗ TODO

## 聯準會 · 政策

	FD-01	
FOMC 決議 + 聲明措辭
Fed	vdf_fetchers_fed	事件	
date · rate · statementDiff
45	✓ DONE
	FD-02	
SEP 點陣圖 + 預測
Fed	vdf_fetchers_fed	季	
dots · gdp · unemp · pce
45	✓ DONE
	FD-03	
政策語調評分(hawk/dove)
VDF 推導 NLP	vdf_fetchers_fed	事件	
toneScore · keyPhrases
45	✓ DONE
	FD-04	
官員發言時序 + 立場
Fed 講稿	vdf_fetchers_fed	事件	
speaker · date · stance · url
45	✓ DONE
	FD-05	
市場隱含路徑(Fed Funds 期貨)
CME	vdf_fetchers_fed	日	
impliedProb by meeting
45	📡 PROXY
	FD-06	
資產負債表 + 準備金
Fed H.4.1(FRED)	vdf_fetchers_macro	週	
totalAssets · reserves · rrp
45	✓ DONE

## 全球總經 · 區域

	GL-01	
歐元區 政策利率 / HICP / PMI
ECB(FRED 代理)	vdf_fetchers_macro	月	
rate · hicp · pmi
49	📡 PROXY
	GL-02	
日本 政策利率 / CPI / Tankan
BOJ(FRED 代理)	vdf_fetchers_macro	月	
rate · cpi · tankan
49	📡 PROXY
	GL-03	
英國 政策利率 / CPI
BOE(FRED 代理)	vdf_fetchers_macro	月	
rate · cpi
49	📡 PROXY
	GL-04	
中國 PMI / CPI / PPI / 社融
AKSHARE	vdf_fetchers_macro	月	
pmi · cpi · ppi · tsf
49	✓ DONE
	GL-04A	
中國 A 股指數與板塊(AkShare)
AKSHARE	vdf_fetchers_market	日	
滬深300 · 中證500 · 申萬行業 · 北向資金
49 · 61	✓ DONE
	GL-04B	
中國商品期貨全品種(AkShare)
AKSHARE	vdf_fetchers_market	日	
螺紋鋼 · 鐵礦 · 焦煤 · 純鹼 · PVC · 棕櫚 · close · volume · oi
4C · 14	✓ DONE
	GL-04C	
中國宏觀月報全表(AkShare)
AKSHARE	vdf_fetchers_macro	月	
固定資產投資 · 社零 · 工業增加值 · 房地產投資 · 出口
49	✓ DONE
	GL-04D	
中國貨幣與信貸(AkShare)
AKSHARE	vdf_fetchers_macro	月	
M1 · M2 · 新增人民幣貸款 · LPR · 存款準備率
49 · 45	✓ DONE
	GL-04E	
中港基金與 ETF 資料(AkShare)
AKSHARE	vdf_fetchers_etf_holdings	日	
fundNav · aum · holdings · southboundFlow
65 · 66	✓ DONE
	GL-04F	
AkShare 中文欄位標準化對映
VPNS rename map	vdf_fetchers_derived	事件	
zhField→canonicalField · unit · freq · source
SSOT	✓ DONE
	GL-05	
台灣 景氣燈號 / 外銷訂單 / 出口
國發會 · 財政部	vdf_fetchers_macro	月	
signal · orders · exports
49 · 25	✗ TODO
	GL-06	
東南亞(SG MY TH VN ID)總經
官方統計 + IMF	vdf_fetchers_macro	月	
gdp · cpi · pmi · exports
49	✗ TODO
	GL-07	
南亞(IN)總經 + 產能移轉指標
MOSPI + RBI	vdf_fetchers_macro	月	
gdp · cpi · iip
49 · 14	✗ TODO
	GL-08	
中東(SA AE)油收與主權基金
官方 + IMF	vdf_fetchers_macro	季	
oilRevenue · gdp
49	✗ TODO
	GL-09	
澳洲 政策利率 / CPI / 鐵礦出口
RBA + ABS	vdf_fetchers_macro	月	
rate · cpi · exports
49	✗ TODO
	GL-10	
全球 GDP 恆等式對照表
VDF 推導	vdf_fetchers_derived	季	
country · c · i · g · nx · deflator
49	✓ DONE
	GL-11	
歐元區 製造業 PMI 全分項
S&P Global / HCOB	vdf_fetchers_macro	月	
headline · output · newOrders · employment · inputPrices · outputPrices · backlog · stocks · 含德法義西
49	📡 PROXY
	GL-12	
歐元區 服務業與綜合 PMI 全分項
S&P Global / HCOB	vdf_fetchers_macro	月	
services · composite + 分項 · 含德法義西
49	📡 PROXY
	GL-13	
日本 製造業與服務業 PMI 全分項
au Jibun Bank / S&P Global	vdf_fetchers_macro	月	
mfg · svc · composite + newOrders · employment · prices
49	📡 PROXY
	GL-14	
中國 官方 PMI(製造 · 非製造 · 綜合)全分項
國家統計局(AkShare)	vdf_fetchers_macro	月	
mfgPMI · nonMfgPMI · composite + production · newOrders · newExport · employment · prices · 大中小型企業
49	✓ DONE
	GL-15	
中國 財新 PMI(製造 · 服務)
Caixin(AkShare)	vdf_fetchers_macro	月	
caixinMfg · caixinSvc · composite + 分項 · 與官方對照
49	✓ DONE
	GL-16	
英國 製造業與服務業 PMI 全分項
S&P Global / CIPS	vdf_fetchers_macro	月	
mfg · svc · construction · composite + 分項
49	📡 PROXY
	GL-17	
台灣 製造業 PMI 與非製造業 NMI 全分項
中華經濟研究院	vdf_fetchers_macro	月	
pmi · nmi + 新增訂單 · 生產 · 人力 · 存貨 · 客戶存貨 · 未來展望
49 · 25	✗ TODO
	GL-18	
韓國 · 印度 · 東南亞 製造業 PMI
S&P Global	vdf_fetchers_macro	月	
KR · IN · SG · MY · TH · VN · ID · PH mfgPMI + 分項
49	📡 PROXY
	GL-19	
澳洲 · 加拿大 · 巴西 · 墨西哥 PMI
S&P Global / AiG	vdf_fetchers_macro	月	
AU · CA · BR · MX mfg+svc PMI
49	📡 PROXY
	GL-20	
全球 PMI 綜合矩陣(擴張收縮熱圖)
VDF 推導	vdf_fetchers_derived	月	
country×sector · level · Δmom · above50Breadth · diffusion
49 · 61	✓ DONE
	GL-21	
歐元區 HICP 全分項 + 核心
Eurostat(FRED 代理)	vdf_fetchers_macro	月	
headline · core · food · energy · nonEnergyGoods · services + 成員國
49 · 47	📡 PROXY
	GL-22	
歐元區 PPI 全分項
Eurostat(FRED 代理)	vdf_fetchers_macro	月	
total · exEnergy · intermediate · capital · durable · nonDurable
49 · 47	📡 PROXY
	GL-23	
日本 CPI 全分項(含核心核心)
總務省(FRED 代理)	vdf_fetchers_macro	月	
headline · coreExFresh · coreCore · energy · services · goods
49 · 47	📡 PROXY
	GL-24	
日本 企業物價 PPI / 進出口物價
日銀	vdf_fetchers_macro	月	
domesticCGPI · exportPI · importPI + 分項
49 · 47	📡 PROXY
	GL-25	
中國 CPI / PPI 全分項
國家統計局(AkShare)	vdf_fetchers_macro	月	
cpi · core · food · pork · energy · ppi · 生產資料 · 生活資料 + 分項
49 · 47	✓ DONE
	GL-26	
英國 CPI / CPIH / RPI 全分項
ONS(FRED 代理)	vdf_fetchers_macro	月	
cpi · cpih · rpi · core · services · goods + 分項
49 · 47	📡 PROXY
	GL-27	
台灣 CPI / 核心 CPI / WPI 全分項
主計總處	vdf_fetchers_macro	月	
cpi · coreCpi · wpi + 食物 · 居住 · 交通 · 教養娛樂 · 醫療
49 · 25	✗ TODO
	GL-28	
韓國 · 印度 · 東南亞 CPI / PPI
官方統計 + FRED	vdf_fetchers_macro	月	
KR · IN · SG · MY · TH · VN · ID cpi · core · ppi
49 · 47	📡 PROXY
	GL-29	
全球通膨矩陣(CPI × PPI × 核心)
VDF 推導	vdf_fetchers_derived	月	
country · cpiYoY · coreYoY · ppiYoY · vsTarget · realRate
49 · 47	✓ DONE
	GL-30	
主要經濟體就業數據全分項
官方統計 + FRED + AkShare	vdf_fetchers_macro	月	
EA · JP · CN · UK · KR · TW · IN · unemployment · participation · jobVacancy · wageGrowth · youthUnemp
49 · 48	📡 PROXY
	GL-31	
歐元區 就業細項(成員國 · 青年 · 長期)
Eurostat(FRED 代理)	vdf_fetchers_macro	月	
byCountry · youth · longTerm · partTime · laborCost
49 · 48	📡 PROXY
	GL-32	
日本 就業細項(有效求人倍率 · 現金薪資)
厚生勞動省(FRED 代理)	vdf_fetchers_macro	月	
jobsToApplicants · unemployment · cashEarnings · realWage · overtimeHours
49 · 48	📡 PROXY
	GL-33	
中國 就業細項(城鎮調查 · 青年 · 農民工)
國家統計局(AkShare)	vdf_fetchers_macro	月	
urbanSurveyUnemp · youth16-24 · migrantWorkers · newUrbanJobs
49 · 48	✓ DONE
	GL-34	
台灣 就業細項(失業率 · 勞參率 · 薪資)
主計總處	vdf_fetchers_macro	月	
unemployment · lfpr · regularEarnings · totalEarnings · overtimeHours
49 · 48 · 25	✗ TODO
	GL-35	
韓國 就業細項(產業別 · 青年)
統計廳	vdf_fetchers_macro	月	
unemployment · byIndustry · youth · participation
49 · 48	📡 PROXY

## AI 概念股 · US AI Complex

	AI-00	
AI 概念股宇宙清單(30 檔 · 五大類)
VIA 族群定義 + YFINANCE	vdf_fetchers_market	日	
ticker · name · tier · subGroup · mcap · spxWeight · 占 SPX 市值約 44%
61 · 14	✓ DONE
	AI-01	
核心半導體與算力晶片(7 檔)每日量價
YFINANCE	vdf_fetchers_market	日	
NVDA · AMD · AVGO · TSM · QCOM · INTC · MRVL · open…adjClose · volume · turnover
61 · 22	✓ DONE
	AI-02	
基礎設施 · 硬體組裝 · 記憶體(7 檔)每日量價
YFINANCE	vdf_fetchers_market	日	
MU · SMCI · DELL · HPE · ASML · WDC · VRT · open…adjClose · volume
61 · 14	✓ DONE
	AI-03	
雲端服務巨頭 Hyperscalers(5 檔)每日量價
YFINANCE	vdf_fetchers_market	日	
MSFT · GOOGL · AMZN · META · ORCL · open…adjClose · volume
61	✓ DONE
	AI-04	
軟體 · 平台 · 大數據應用(6 檔)每日量價
YFINANCE	vdf_fetchers_market	日	
PLTR · NOW · CRM · ADBE · IBM · AI · open…adjClose · volume
61	✓ DONE
	AI-05	
終端硬體 · 資安 · 邊緣應用(5 檔)每日量價
YFINANCE	vdf_fetchers_market	日	
AAPL · TSLA · CRWD · PANW · S · open…adjClose · volume
61	✓ DONE
	AI-06	
AI 族群日內分鐘量價
YFINANCE 1m/5m	vdf_fetchers_market	分	
ts · price · volume · vwap · 盤前盤後
26 · 61	✓ DONE
	AI-07	
AI 族群市值與 SPX 權重貢獻
YFINANCE + S&P	vdf_fetchers_derived	日	
mcap · spxWeight · contribToIndex · concentrationTop7
61 · 66	✓ DONE
	AI-08	
AI 族群等權 vs 市值權重指數
VDF 推導(Adj)	vdf_fetchers_derived	日	
equalWeightIdx · capWeightIdx · breadthDivergence
61 · 70	✓ DONE
	AI-09	
AI 族群相對強弱與輪動(五大類)
VDF 推導(Adj)	vdf_fetchers_derived	日	
tierRelStrength · rank · rotationSignal · zscore
61 · 70	✓ DONE
	AI-10	
AI 族群估值(Forward PER · PSR · PEG)
YFINANCE + 共識	vdf_fetchers_consensus	日	
fwdPER · psr · peg · percentile5y
29 · 61	✓ DONE
	AI-11	
AI 族群共識 EPS 與目標價
yfinance + FactSet	vdf_fetchers_consensus	週	
dilutedEPS · target · analystCount · ratingMix
29	✓ DONE
	AI-12	
AI 族群資本支出與 AI 營收揭露
財報 + 法說	vdf_fetchers_financials	季	
capex · aiRevenue · dcRevenue · guidance
22 · 14	📡 PROXY
	AI-13	
AI 族群成交量異常與量能排行
VDF 推導	vdf_fetchers_derived	日	
volumeZ · relVolume · turnoverRank · unusualFlag
61 · 66	✓ DONE
	AI-14	
AI 族群選擇權未平倉與隱波
YFINANCE options	vdf_fetchers_market	日	
openInterest · ivRank · putCallRatio · skew
68 · 61	📡 PROXY
	AI-15	
AI 族群 ETF 曝險與被持有次數
issuer + VDF 推導	vdf_fetchers_derived	日	
etfCount · totalWeight · heldByThemeEtf
65 · 61	✓ DONE
	AI-16	
AI 供應鏈台美對照(台股受惠股連結)
VIA ACLS + TWSE	vdf_fetchers_derived	日	
usTicker↔twTicker · supplyRole · correlation
25 · 61	✓ DONE

## 擷取矩陣 · VDF v4.3 Acquisition Matrix

	MX-A1	
A1 台股上市 TWSE 全市場量價
TWSE	vdf_fetchers_market	日	
全 ~980 檔 · OHLCV · adjClose · 三大法人 · 融資 · 當沖 · px+adj+chip → 對映 PX-01
22 · 25	✓ DONE
	MX-A2	
A2 台股上櫃 TPEX 全市場量價
TPEX	vdf_fetchers_market	日	
全 ~838 檔 · 同上欄位 → 對映 PX-02
22 · 25	✓ DONE
	MX-A3	
A3 台股指數(加權 · 櫃買 · 電子 · 金融)
TWSE + TPEX	vdf_fetchers_market	日	
TAIEX · OTC · 電子類 · 金融類 · 量價+法人 → 對映 PX-04C
25 · 61	✓ DONE
	MX-A4	
A4 國際個股量價 + Adj Close
YFINANCE	vdf_fetchers_market	日	
open…adjClose · volume → 對映 PX-03 · AI-01~05
61 · 22	✓ DONE
	MX-A5	
A5 國際股價指數
YFINANCE	vdf_fetchers_market	日	
→ 對映 PX-04A…P(16 區域子項)
49 · 61	✓ DONE
	MX-A6	
A6 FX 外匯
YFINANCE	vdf_fetchers_market	日	
→ 對映 FX-01 · FX-02
2A · 42	✓ DONE
	MX-A7	
A7 Commodities 大宗商品期貨
YFINANCE + AKSHARE	vdf_fetchers_market	日	
→ 對映 CM-01…CM-09
4C	✓ DONE
	MX-A8	
A8 Bonds 債券
Treasury + FRED	vdf_fetchers_fiscal	日	
→ 對映 FX-03 · FX-04 · FI-04
2C · 43	✓ DONE
	MX-A9	
A9 Volatility VIX 系列
Yahoo	vdf_fetchers_market	日	
VIX · VVIX · MOVE · SKEW → 對映 PX-06
68 · 61	✓ DONE
	MX-A10	
A10 Crypto 加密貨幣
YFINANCE + CoinGecko	vdf_fetchers_market	日	
→ 對映 CY-01…CY-10
4C · 66	📡 PROXY
	MX-A11	
A11 台股 ETF(被動式)
TWSE + 投信	vdf_fetchers_etf_holdings	日	
→ 對映 EF-12 全清單成分權重
65 · 25	✓ DONE
	MX-A12	
A12 台股 ETF(主動式)
投信官網 ×17	vdf_fetchers_etf_holdings	日	
v4.3 記 18 檔 → 現行 37 檔(EF-01A…X · EF-40A…F · EF-41A…G)
65 · 6A	✓ DONE
	MX-B1	
B1 Prices 物價(CPI / PCE / PPI)
FRED 代理	vdf_fetchers_macro	月	
→ 對映 US-G01…G21 全分項
42 · 47	📡 PROXY
	MX-B2	
B2 Labor 勞動力
BLS(FRED)	vdf_fetchers_macro	月	
→ 對映 US-C03…C08 · C19…C21
42 · 48	✓ DONE
	MX-B3	
B3 Rates 利率與殖利率曲線
Treasury + FRED	vdf_fetchers_fiscal	日	
→ 對映 FX-03…FX-07
2C · 45	✓ DONE
	MX-B4	
B4 Fiscal 財政(DTS + MTS + Debt)
Treasury FiscalData	vdf_fetchers_fiscal	日·月	
→ 對映 FI-01…FI-06
43	✓ DONE
	MX-B5	
B5 Fed Policy + Sentiment + Misc
Fed + AAII + CNN	vdf_fetchers_fed	事件·日	
→ 對映 FD-01…FD-06 · SE-01…SE-13
45 · 68	✓ DONE
	MX-C1	
C1 Regional ETFs(全球 ETF 宇宙 77 檔)
issuer + YFINANCE	vdf_fetchers_etf_holdings	日	
→ 對映 PX-05A…G 區域指數 ETF 對照
65 · 49	✓ DONE
	MX-C2	
C2 Sector ETFs(SPDR + 主題)
YFINANCE	vdf_fetchers_market	日	
→ 對映 PX-06B…E
61 · 65	✓ DONE
	MX-C3	
C3 Bond ETFs
issuer + YFINANCE	vdf_fetchers_etf_holdings	日	
→ 對映 EF-26 存續期 · 信評 · YTM
65 · 43	✓ DONE
	MX-C4	
C4 Commodity / FX ETFs
issuer + YFINANCE	vdf_fetchers_etf_holdings	日	
→ 對映 CM-10…CM-17
4C · 65	✓ DONE
	MX-D1	
D1 主動式 ETF 持股 · 依投信分組(10 家)
投信官網	vdf_fetchers_etf_holdings	日	
issuer 分組 + 4 段 fallback → 對映 EF-01 全清單
65 · 6A	✓ DONE
	MX-D2	
D2 TDCC 集保資料
TDCC 集保	vdf_fetchers_tdcc	週	
受益人數 + 股權分散 → 對映 EF-04 · EF-21
65 · 25	✓ DONE
	MX-E1	
E1 台股共識(全市場 ~1,900 檔)
Cnyes(FactSet)	vdf_fetchers_consensus	週	
target · rating · EPS → 對映 CS-01…CS-06
29 · 22	✓ DONE
	MX-00	
擷取矩陣總覽 · 5 大 Section / 24 子類
VDF v4.3 Cockpit	vdf_fetchers_derived	事件	
section · subsection · features(px·adj·chip) · coverage · status · 只增不減
SSOT	✓ DONE

## 資金流品質 · Flow Quality

	FQ-01	
三大法人買賣超(TWSE T86)
TWSE T86	vdf_fetchers_market	日	
foreign · trust · dealerNet · byTicker · T+1 起可用(ASOF JOIN 強制)
25 · 66	✓ DONE
	FQ-02	
融資融券餘額(TWSE MI_MARGN)
TWSE MI_MARGN	vdf_fetchers_market	日	
marginBalance · shortBalance · Δmargin · Δshort · T+1
25 · 68	✓ DONE
	FQ-03	
融資維持率 · 使用率 · 券資比
VDF 推導(MI_MARGN)	vdf_fetchers_derived	日	
maintenanceRatio · utilizationRate · shortToMarginRatio · 非 TWSE 原生,須以融資餘額成本基礎推估
68 · 25	✓ DONE
	FQ-04	
當沖成交值與當沖比
TWSE 當沖統計	vdf_fetchers_market	日	
dayTradeValue · cashDayTrade · marginDayTrade · dayTradeRatio
25 · 66	✓ DONE
	FQ-05	
去當沖真流(存量差分優先)
VDF 推導	vdf_fetchers_derived	日	
netFlowExDayTrade = 存量差分(當沖自動抵消)· 周轉類才扣當沖成交值
66 · 25	✓ DONE
	FQ-06	
SBL 借券賣出餘額(法人空方)
TWSE SBL	vdf_fetchers_market	日	
sblShortBalance · lendingBalance · 外資空單多走 SBL 不入融券,券資比會漏
68 · 25	✓ DONE
	FQ-07	
資料品質折扣權重(data-quality-adjusted)
VDF 推導	vdf_fetchers_derived	日	
dayTradeDiscount · maintenanceFragility · confidenceWeight → FIS 折扣
66 · 61	✓ DONE
	FQ-08	
買賣超語意閘門(zero-sum 標記)
VDF 品質閘門	vdf_fetchers_derived	日	
isZeroSum · useAsDirectionOnly · marketNetIsZero · 禁作「總流入」字面解讀
66	✓ DONE
	FQ-09	
T+1 時效紀律與 ASOF JOIN 稽核
VDF 品質閘門	vdf_fetchers_derived	日	
availableAt · asofJoinKey · lookaheadViolation
SSOT · 66	✓ DONE
	FQ-10	
ETF 每日投資組合 PCF(創贖真值)
TWSE PCF	vdf_fetchers_etf_holdings	日	
pcfBasket · creationUnit · cashComponent · estCashAmount
65 · 66	✓ DONE
	FQ-11	
投信投顧公會 規模與受益人數
SITCA 投信投顧公會	vdf_fetchers_etf_holdings	月	
fundAum · holders · netAssetΔ · 與 TWSE 交叉驗證
65 · 25	✓ DONE
	FQ-12	
指數隱含總流與覆蓋率(推估標記)
VDF 推導	vdf_fetchers_derived	日	
impliedIndexFlow = ETF淨流$ ÷ coverage · evidenceTier · isAmplifiedEstimate
66 · 61	✓ DONE
	FQ-13	
流量交叉驗證(ETF 創贖 × T86 × 北向 × EPFR)
多源交叉	vdf_fetchers_derived	日	
etfFlow · t86Net · northbound · epfrFlow · leadLag · consistencyScore
66 · 49	📡 PROXY

## 加密貨幣 · Crypto & ETF

	CY-01	
主要幣種現貨價量(BTC ETH SOL…)
YFINANCE + CoinGecko	vdf_fetchers_market	日	
close · volume · marketCap · dominance
4C · 61	📡 PROXY
	CY-02	
加密總市值 · 穩定幣總量
CoinGecko	vdf_fetchers_market	日	
totalMcap · stablecoinSupply · Δsupply
4C · 66	📡 PROXY
	CY-03	
美國現貨比特幣 ETF(11 檔)
issuer + YFINANCE	vdf_fetchers_etf_holdings	日	
IBIT · FBTC · GBTC · ARKB · BITB · HODL · BRRR · BTCO · EZBC · BTCW · DEFI · nav · aum · units
65 · 66	✓ DONE
	CY-04	
美國現貨以太 ETF(9 檔)
issuer + YFINANCE	vdf_fetchers_etf_holdings	日	
ETHA · FETH · ETHW · ETHV · QETH · EZET · ETHE · ETH · CETH · nav · aum · units
65 · 66	✓ DONE
	CY-05	
加密 ETF 每日淨流入 / 流出
issuer 揭露 + Δunits×NAV	vdf_fetchers_derived	日	
netFlowUSD · ΔunitsBTC · cumFlow · byIssuer
66 · 65	✓ DONE
	CY-06	
加密 ETF 持幣量與託管
issuer 月報 + 鏈上	vdf_fetchers_etf_holdings	日	
btcHeld · ethHeld · custodian · Δcoins
66	📡 PROXY
	CY-07	
期貨型與槓桿加密 ETF
YFINANCE	vdf_fetchers_market	日	
BITO · BITX · ETHU · rollYield · basis · decay
4C · 65	📡 PROXY
	CY-08	
加密期貨基差 · 資金費率
CME + 交易所	vdf_fetchers_market	日	
cmeBasis · perpFundingRate · openInterest
68 · 4C	✗ TODO
	CY-09	
礦工與鏈上指標
鏈上資料源	vdf_fetchers_derived	日	
hashRate · minerRevenue · exchangeBalance · netflow
66	✗ TODO
	CY-10	
加密與風險資產相關係數
VDF 推導(Adj)	vdf_fetchers_derived	日	
corrVsSPX · corrVsGold · corrVsDXY · rolling90d
61 · 4C	✓ DONE

## 情緒 · 部位

	SE-01	
AAII 散戶多空
AAII	vdf_fetchers_sentiment	週	
bull · bear · neutral · spread
68	✓ DONE
	SE-02	
CNN Fear & Greed(含 7 分項)
CNN	vdf_fetchers_sentiment	日	
composite + 7 factors
68	✓ DONE
	SE-03	
Put/Call Ratio
CBOE	vdf_fetchers_sentiment	日	
equity · index · total
68	📡 PROXY
	SE-04	
CFTC COT 法人淨部位(管理基金)
CFTC COT	vdf_fetchers_sentiment	週	
managedMoneyNet · commercial · nonReportable · openInterest · 週五發布(截至週二)
68 · 4C	✗ TODO
	SE-05	
融資融券 + 借券
TWSE / FINRA	vdf_fetchers_market	日	
margin · short
25 · 68	✓ DONE
	SE-06	
牛熊證發行與街貨量(港股)
HKEX	vdf_fetchers_sentiment	日	
bull · bearOutstanding · strikeDistribution · netΔ
61 · 68	✗ TODO
	SE-07	
牛熊街貨重心與回收價分布
HKEX	vdf_fetchers_derived	日	
recallLevel · heatmapByStrike · bullBearRatio
61 · 68	✗ TODO
	SE-08	
牛熊指標 · 市場寬度型
VDF 推導(Adj)	vdf_fetchers_derived	日	
advDecLine · pctAbove200dma · newHighsLows · mcClellan
61 · 68	✓ DONE
	SE-09	
牛熊指標 · 綜合多空評分
VDF 推導	vdf_fetchers_derived	日	
bullBearScore · regime(牛 · 熊 · 盤整) · confidence
61 · 68	✓ DONE
	SE-10	
AAII 多空差(牛熊價差)
AAII	vdf_fetchers_sentiment	週	
bullBearSpread · 8wma · percentile
68	✓ DONE
	SE-11	
Investors Intelligence 顧問牛熊比
II(代理)	vdf_fetchers_sentiment	週	
bulls · bears · correction · ratio
68	📡 PROXY
	SE-12	
台股多空指標(融資餘額×主力×櫃買比)
TWSE + TPEX	vdf_fetchers_derived	日	
marginRatio · otcToTwseRatio · bigPlayerNet
25 · 68	✓ DONE
	SE-13	
牛熊市場週期判定與轉折標記
VDF 推導(Adj 價)	vdf_fetchers_derived	日	
cycleState · drawdownFromPeak · daysInRegime · turnDate
61 · 70	✓ DONE

## ETF · 資金流

	EF-01	
台股股票型主動式 ETF 全清單(24 檔 · 末碼 A)
TWSE + 投信官網 ×17	vdf_fetchers_etf_holdings	日	
code · name · issuer · listDate · holding · weight · shares · Δshares · turnover
65 · 6A	✓ DONE
	EF-01A	
00980A 主動野村臺灣優選
野村投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配 · 首檔 2025-05
65 · 6A	✓ DONE
	EF-01B	
00981A 主動統一台股增長
統一投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01C	
00982A 主動群益台灣強棒
群益投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01D	
00984A 主動安聯台灣高息
安聯投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01E	
00985A 主動野村台灣50
野村投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 半年配
65 · 6A	✓ DONE
	EF-01F	
00986A 主動台新龍頭成長
台新投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 年配
65 · 6A	✓ DONE
	EF-01G	
00987A 主動台新優勢成長
台新投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 年配
65 · 6A	✓ DONE
	EF-01H	
00991A 主動復華未來50
復華投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 半年配
65 · 6A	✓ DONE
	EF-01I	
00992A 主動群益科技創新
群益投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01J	
00993A 主動安聯台灣
安聯投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 年配
65 · 6A	✓ DONE
	EF-01K	
00994A 主動第一金台股優
第一金投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01L	
00995A 主動中信台灣卓越
中國信託投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01M	
00996A 主動兆豐台灣豐收
兆豐投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01N	
00998A 主動復華金融股息
復華投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · —
65 · 6A	✓ DONE
	EF-01O	
00999A 主動野村臺灣高息
野村投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01P	
00400A 主動國泰動能高息
國泰投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 月配
65 · 6A	✓ DONE
	EF-01Q	
00401A 主動摩根台灣鑫收
摩根投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · —
65 · 6A	✓ DONE
	EF-01R	
00403A 主動統一升級50
統一投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01S	
00404A 主動聯博動能50
聯博投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01T	
00405A 主動富邦台灣龍耀
富邦投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01U	
00406A 主動中信台灣收益
中國信託投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 月配
65 · 6A	✓ DONE
	EF-01V	
00407A 主動凱基台灣
凱基投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · —
65 · 6A	✓ DONE
	EF-01W	
00408A 主動第一金優股息
第一金投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 季配
65 · 6A	✓ DONE
	EF-01X	
00410A 主動永豐科技趨勢
永豐投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · cash · 半年配
65 · 6A	✓ DONE
	EF-40	
台股掛牌 海外股票型主動 ETF 全清單(6 檔 · 末碼 A)
TWSE + 投信官網	vdf_fetchers_etf_holdings	日	
code · name · issuer · listDate · holding · weight · countryMix
65 · 6A	✓ DONE
	EF-40A	
00983A 主動中信ARK創新
中國信託投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · countryMix · sectorMix · ARK 授權 · 全球創新
65 · 6A	✓ DONE
	EF-40B	
00988A 主動統一全球創新
統一投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · countryMix · sectorMix · 全球科技創新
65 · 6A	✓ DONE
	EF-40C	
00989A 主動摩根美國科技
摩根投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · countryMix · sectorMix · 美股科技
65 · 6A	✓ DONE
	EF-40D	
00990A 主動元大AI新經濟
元大投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · countryMix · sectorMix · AI 主題
65 · 6A	✓ DONE
	EF-40E	
00997A 主動群益美國增長
群益投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · countryMix · sectorMix · 美股成長
65 · 6A	✓ DONE
	EF-40F	
00402A 主動安聯美國科技
安聯投信	vdf_fetchers_etf_holdings	日	
holding · weight · shares · Δshares · countryMix · sectorMix · 美股科技
65 · 6A	✓ DONE
	EF-41	
台股掛牌 債券型主動 ETF 全清單(7 檔 · 末碼 D)
TWSE + 投信官網	vdf_fetchers_etf_holdings	日	
code · name · issuer · duration · creditMix · ytm
65 · 43	✓ DONE
	EF-41A	
00980D 主動野村優選非投等債
野村投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 非投等債 · 月配
65 · 43	✓ DONE
	EF-41B	
00981D 主動統一美債
統一投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 美國公債
65 · 43	✓ DONE
	EF-41C	
00982D 主動群益優選非投等債
群益投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 非投等債 · 月配
65 · 43	✓ DONE
	EF-41D	
00983D 主動中信優選投等債
中國信託投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 投等債 · 月配
65 · 43	✓ DONE
	EF-41E	
00984D 主動安聯美元債
安聯投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 美元綜合債
65 · 43	✓ DONE
	EF-41F	
00985D 主動野村全球債
野村投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 全球綜合債
65 · 43	✓ DONE
	EF-41G	
00986D 主動第一金優選債
第一金投信	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder · Δholdings · 投等債
65 · 43	✓ DONE
	EF-42	
主動式 ETF 總表(37 檔 · 股票24 + 海外6 + 債券7)
TWSE	vdf_fetchers_etf_holdings	日	
code · type · issuer · listDate · aum · holders · status · 只增不減
65 · 25	✓ DONE
	EF-43	
主動式 ETF 新掛牌與募集追蹤
TWSE 公告 + 投信	vdf_fetchers_etf_holdings	事件	
code · ipoDate · ipoSize · issuer · benchmark · feeSchedule
65	✓ DONE
	EF-06	
主動式 ETF 持股交集與分歧矩陣
VDF 推導	vdf_fetchers_derived	日	
ticker×etf · overlapPct · consensusRank · divergence · syncSignal
65 · 6A	✓ DONE
	EF-07	
主動式 ETF 同步加碼 / 減碼訊號
VDF 推導(快照差)	vdf_fetchers_derived	日	
ticker · etfCount · netAdd · netCut · estAmount
65 · 6A	✓ DONE
	EF-08	
主動報酬歸因(選股 / 配置)
VDF 推導(Adj 價)	vdf_fetchers_derived	日	
activeRet · vsBenchmark · selection · allocation
65 · 61	✓ DONE
	EF-09	
週轉率 · 新進與撤出股票池
VDF 推導	vdf_fetchers_derived	週	
turnoverRate · newEntry · exitList · holdDays
65 · 6A	✓ DONE
	EF-10	
規模 · 折溢價 · 受益人數
TWSE + 投信 + TDCC	vdf_fetchers_etf_holdings	日	
aum · nav · premium · holders · unitsΔ
65 · 25	✓ DONE
	EF-11	
主動 vs 被動 ETF 資金流對比
TWSE + 投信	vdf_fetchers_etf_holdings	日	
activeFlow · passiveFlow · netShift
65 · 66	✓ DONE
	EF-12	
台股被動式 ETF 全清單 · 成分與權重
TWSE + 投信 + 指數公司	vdf_fetchers_etf_holdings	日	
code · name · indexTracked · holding · weight · shares
65 · 25	✓ DONE
	EF-13	
ETF 淨值 NAV · 市價 · 折溢價
TWSE + 投信	vdf_fetchers_etf_holdings	日	
nav · close · premiumPct · intradayIOPV
65	✓ DONE
	EF-14	
ETF 規模 AUM · 流通在外單位數
TWSE + 投信	vdf_fetchers_etf_holdings	日	
aum · unitsOutstanding · Δunits · creationRedemption
65 · 66	✓ DONE
	EF-15	
ETF 申購買回申報(初級市場流量)
TWSE	vdf_fetchers_etf_holdings	日	
creations · redemptions · netCreation
65 · 66	✓ DONE
	EF-16	
ETF 配息紀錄 · 除息日 · 殖利率
投信 + TWSE	vdf_fetchers_etf_holdings	事件	
exDate · payDate · dividend · annualYield · frequency
65	✓ DONE
	EF-17	
ETF 收益平準金與可分配收益
投信月報	vdf_fetchers_etf_holdings	月	
levelingFund · distributableIncome · coverRatio
65	✗ TODO
	EF-18	
ETF 內扣費用(管理/保管/總費用率)
投信公開說明書	vdf_fetchers_etf_holdings	季	
mgmtFee · custodyFee · totalExpenseRatio · turnoverCost
65	✓ DONE
	EF-19	
ETF 追蹤誤差與追蹤差異
VDF 推導(Adj NAV vs 指數)	vdf_fetchers_derived	日	
trackingError · trackingDiff · rSquared
65 · 70	✓ DONE
	EF-20	
ETF 流動性(成交量/量能/買賣價差)
TWSE	vdf_fetchers_market	日	
volume · turnoverValue · bidAskSpread · depth
65	✓ DONE
	EF-21	
ETF 受益人數與持股分散(全市場)
TDCC 集保	vdf_fetchers_tdcc	週	
holders · Δholders · distributionBands
65 · 25	✓ DONE
	EF-22	
ETF 融資融券與借券餘額
TWSE	vdf_fetchers_market	日	
marginBalance · shortBalance · lendingBalance
65 · 68	✓ DONE
	EF-23	
槓桿 / 反向 ETF 部位與正逆價差
TWSE + 投信	vdf_fetchers_etf_holdings	日	
leverage · inverse · futuresPosition · rollCost
65 · 4C	✓ DONE
	EF-24	
期貨型 ETF 轉倉成本與展期損耗
VDF 推導	vdf_fetchers_derived	日	
rollYield · contango · backwardation · decay
4C · 65	✓ DONE
	EF-25	
海外股票型 ETF 成分與區域配置
issuer + YFINANCE	vdf_fetchers_etf_holdings	日	
holding · weight · countryMix · sectorMix
65 · 49	✓ DONE
	EF-26	
債券型 ETF 存續期 · 信評 · YTM
投信 + issuer	vdf_fetchers_etf_holdings	日	
duration · creditMix · ytm · oas · maturityLadder
65 · 43	✓ DONE
	EF-27	
ETF 產業與主題曝險彙總
VDF 推導	vdf_fetchers_derived	日	
sectorExposure · themeExposure · topHoldingConcentration
65 · 61	✓ DONE
	EF-28	
ETF 重疊度矩陣(任兩檔)
VDF 推導	vdf_fetchers_derived	日	
etfA×etfB · overlapPct · sharedWeight
65	✓ DONE
	EF-29	
ETF 報酬與風險指標(含配息再投入)
VDF 推導(Adj)	vdf_fetchers_derived	日	
totalRet · priceRet · vol · maxDD · sharpe · sortino
65 · 70	✓ DONE
	EF-30	
美國 ETF 資金流(區域/資產/主題)
issuer + EPFR 代理	vdf_fetchers_etf_holdings	週	
flow · aum · netΔ · byCategory
65 · 66	📡 PROXY
	EF-31	
ETF 成分股被持有次數排行
VDF 推導	vdf_fetchers_derived	日	
ticker · etfCount · totalWeight · totalShares
65 · 61	✓ DONE
	EF-32	
ETF 上市 / 募集 / 清算事件簿
TWSE 公告	vdf_fetchers_etf_holdings	事件	
listDate · ipoSize · liquidationNotice · status
65	✓ DONE
	EF-33	
資金流計算基礎欄位(全 ETF)
TWSE + issuer	vdf_fetchers_etf_holdings	日	
unitsOutstanding(t) · unitsOutstanding(t-1) · nav · fxRate · asof
66 · 65	✓ DONE
	EF-34	
淨流入 / 流出 主算式
VDF 推導	vdf_fetchers_derived	日	
netFlow = Δunits × NAV(當日,原幣) → USD · TWD 雙幣別
66 · 65	✓ DONE
	EF-35	
流入流出拆解(價格效應 vs 流量效應)
VDF 推導	vdf_fetchers_derived	日	
ΔaumTotal · priceEffect · flowEffect · fxEffect
66 · 61	✓ DONE
	EF-36	
累計流量與流量動能
VDF 推導	vdf_fetchers_derived	日	
cumFlow1w · 1m · 3m · ytd · flowMomentumZ
66	✓ DONE
	EF-37	
流量佔規模比(flow / AUM)
VDF 推導	vdf_fetchers_derived	日	
flowToAum · percentileRank · crowdingFlag
66 · 61	✓ DONE
	EF-38	
跨類別資金流矩陣(區域×資產×主題)
VDF 推導	vdf_fetchers_derived	日	
region×asset×theme · netFlow · rank · rotationSignal
66 · 61	✓ DONE
	EF-39	
資金流資料缺口與代理標記
VDF 品質閘門	vdf_fetchers_derived	日	
source · isProxy · missingDays · confidence
66 · 65	✓ DONE
	EF-02	
全球 ETF 資金流(區域/資產/主題)
issuer + EPFR 代理	vdf_fetchers_etf_holdings	週	
flow · aum · netΔ
65 · 66	📡 PROXY
	EF-03	
ETF 規模與折溢價
YFINANCE + issuer	vdf_fetchers_etf_holdings	日	
aum · nav · premium
65	✓ DONE
	EF-04	
集保受益人數 + 股權分散
TDCC 集保	vdf_fetchers_tdcc	週	
holders · distribution
65 · 25	✓ DONE
	EF-05	
跨資產資金輪動矩陣
VDF 推導	vdf_fetchers_derived	週	
assetClass · flowRank · zscore
66 · 61	✓ DONE

## 共識 · 評價

	CS-01	
稀釋 EPS 共識(FY1/FY2)
yfinance + FactSet(Cnyes)	vdf_fetchers_consensus	週	
dilutedEPS · median · high · low
29 · 22	✓ DONE
	CS-02	
目標價 + 分析師家數
yfinance + FactSet	vdf_fetchers_consensus	週	
target · high · low · analystCount
29 · 22	✓ DONE
	CS-03	
評等分布(買入/持有/賣出)
yfinance + FactSet	vdf_fetchers_consensus	週	
ratingMix · consensusScore
29	✓ DONE
	CS-04	
Forward PER / PBR
VDF 推導(Adj 價 ÷ 共識)	vdf_fetchers_derived	日	
fwdPER · fwdPBR · percentile
29 · 22	✓ DONE
	CS-05	
EPS 修正動能(revision breadth)
VDF 推導	vdf_fetchers_derived	週	
revUp · revDown · breadth
29	✓ DONE
	CS-06	
標準化評價 vs 現實背離度
VDF 推導	vdf_fetchers_derived	日	
zScore · divergence
61 · 29	✓ DONE

## 財報 · 三大報表

	FN-00	
台股全上市櫃公司清單(全量基準)
TWSE + TPEX	vdf_fetchers_financials	日	
ticker · name · market · industry · listDate · shareCapital · sharesOutstanding · 全 1,9xx 檔
22 · 25	✓ DONE
	FN-01	
損益表 · 單季(全台股)
MOPS	vdf_fetchers_financials	季	
revenue · cogs · gross · opex · opIncome · nonOp · preTax · tax · netIncome · minorityInt · parentNet
22 · 14	✓ DONE
	FN-01A	
損益表 · 年度(全台股)
MOPS	vdf_fetchers_financials	年	
同單季欄位 · FY 合併與個體
22 · 14	✓ DONE
	FN-01B	
損益表 · 累計期間(Q1 / H1 / 前三季)
MOPS	vdf_fetchers_financials	季	
cumRevenue · cumOpIncome · cumNet · 累計對比
22	✓ DONE
	FN-02	
資產負債表 · 單季(全台股)
MOPS	vdf_fetchers_financials	季	
cash · AR · inventory · currentAssets · PPE · totalAssets · AP · shortDebt · longDebt · totalLiab · equity · parentEquity
22	✓ DONE
	FN-02A	
資產負債表 · 年度(全台股)
MOPS	vdf_fetchers_financials	年	
同單季欄位 · FY 底數
22	✓ DONE
	FN-03	
現金流量表 · 單季(全台股)
MOPS	vdf_fetchers_financials	季	
cfo · cfi · cff · capex · depreciation · amortization · netChangeCash · fcf
22	✓ DONE
	FN-03A	
現金流量表 · 年度(全台股)
MOPS	vdf_fetchers_financials	年	
同單季欄位 · FY 合計
22	✓ DONE
	FN-03B	
現金流量表 · 累計期間
MOPS	vdf_fetchers_financials	季	
cumCfo · cumCapex · cumFcf
22	✓ DONE
	FN-04	
比率分析(獲利 / 償債 / 週轉 / 成長)
VDF 推導	vdf_fetchers_derived	季·年	
gm · om · npm · roe · roa · roic · currentRatio · quickRatio · debtRatio · intCover · dso · dio · dpo · ccc · revYoY · epsYoY
22	✓ DONE
	FN-05	
每股分析 · 基本 vs 稀釋 EPS
MOPS + VDF 推導	vdf_fetchers_financials	季·年	
basicEPS · dilutedEPS · weightedShares · dilutedShares · dilutionPct
22 · 29	✓ DONE
	FN-05A	
每股分析 · EBITDA per Share
VDF 推導	vdf_fetchers_derived	季·年	
ebitda = opIncome + D&A · ebitdaPerShare · ebitdaMargin
22 · 29	✓ DONE
	FN-05B	
每股分析 · 帳面 / 現金流 / 股利 / 營收
VDF 推導	vdf_fetchers_derived	季·年	
bps · cfps · fcfps · dps · sps · payoutRatio
22 · 29	✓ DONE
	FN-05C	
每股分析 · 滾動四季 TTM
VDF 推導	vdf_fetchers_derived	季	
ttmEPS · ttmDilutedEPS · ttmEBITDAps · ttmSps · ttmFcfps
22 · 29 · 70	✓ DONE
	FN-05D	
股本變動與稀釋因子(增資 / 減資 / 分割)
MOPS + TWSE	vdf_fetchers_financials	事件	
capitalChange · exRightDate · adjFactor · convertibleDilution
22 · PX	✓ DONE
	FN-06	
月營收 · 全台股逐檔
MOPS	vdf_fetchers_financials	月	
revenue · yoy · mom · cumRevenue · cumYoy · lastYearSame · 全上市櫃
22 · 25	✓ DONE
	FN-06A	
月營收 · 創新高與連續成長標記
VDF 推導	vdf_fetchers_derived	月	
newHighFlag · consecMonths · 3mma · 12mma · yoyTrend
22 · 25	✓ DONE
	FN-06B	
月營收 · 產業與族群彙總
VDF 推導	vdf_fetchers_derived	月	
industryRevenue · groupYoy · contribution · breadth
25 · 61	✓ DONE
	FN-07	
財報公告時程與更新旗標
MOPS 公告	vdf_fetchers_financials	事件	
announceDate · period · isRestated · auditType · delayFlag
22	✓ DONE
	FN-08	
合併 vs 個體 · IFRS 對映
MOPS	vdf_fetchers_financials	季·年	
consolidated · parentOnly · ifrsTag · unitScale
22	✓ DONE
	FN-09	
股利政策與除權息
MOPS + TWSE	vdf_fetchers_financials	事件	
cashDiv · stockDiv · exDate · payDate · yieldOnCost
22 · 65	✓ DONE
	FN-10	
財報品質閘門(全量完整性檢查)
VDF 品質閘門	vdf_fetchers_derived	季	
coverageRate · missingTickers · balanceCheck · signCheck · unitCheck
22 · SSOT	✓ DONE

---

## VIA VDF FETCH ONE · VDF-390 儀表宣告值

資料項 Items 17 · 領域 Domains 187 · 來源 Sources 10 · Fetchers 20 · Engines 296 · Done 75 · Proxy 19 · Todo
① 參數與總冊 PARAMS · REGISTRY
② 契約 · 稽核 · 代碼字典 CONTRACT · AUDIT · SYMBOLS

### 價格來源優先序
凡有 adjClose 者一律優先於 close,並以 Adj 全序列計算報酬、正規化與技術指標;無 adj 者以一般價格為準。遇 stock split 同步調整 volume。

### 缺值與頻率對齊
價格缺值取前一交易日;成交量不補。混頻(日×月)以低頻為對齊基準,堆疊圖共用同一時間映射,絕對對齊。

### 必要欄位
required date · value;optional series · unit · freq · adjClose · volume · source · asof。單位隨欄位帶入以決定左右軸。

### 狀態驗證 · Status Provenance
DONE fetcher 已實作且例行跑通;PROXY 以代理源近似(FRED 代理、ETF 代指數),須標記;TODO 尚未接線。本頁狀態為宣告值,實際可用性須由 vdf_api 健康檢查回寫;未接後端時以宣告為準,不得視為已驗證。

### 權威層級
官方(政府/交易所/央行) > 授權商業源 > 代理(FRED proxy) > 推導模型。代理與推導須標記來源與計算式,不得混入官方層。

### 憑證層級表
| 層級 Tier | 項數 | 憑證 Credential | 可得性判定 Availability |
|---|---|---|---|
| 免憑證 · 公開端點 | 261 | 無 | 判定可得 — TWSE / TPEX / MOPS / Treasury FiscalData / yfinance / TDCC / 投信官網 / akshare / Census / BLS / Fed / OECD,受頻率限制與 robots 約束 |
| FRED API KEY | 78 | P4 必填 | 金鑰未設定 · 判定不可得 — 涵蓋 CPI/PCE/PPI 全分項、勞動力、殖利率曲線、金融條件 |
| 授權 · 訂閱源 | 19 | 付費授權 | 未授權前不可得 — MSCI 指數、LME / LBMA 金屬、IEA OMR、S&P Global / Caixin PMI、SEMI-WSTS、CME、FactSet(Cnyes 代)、Investors Intelligence |
| 爬取 · 無公開 API | 13 | 逐源議定 | 合規確認後方可得 — ADP、MBA、AAII、CNN F&G、NAR、ATA / AAR、NFIB、NAHB、CoinGecko;狀態多為 proxy |
| 尚未接線 TODO | 19 | — | 不可得 — fetcher 未實作,不得視為可得 |

### 期貨/現貨對映表
| 標的 Instrument | 期貨 · 主代碼 Futures | 現貨 · 代理 Spot / Proxy | 來源 Source | 對映 Code |
|---|---|---|---|---|
| Brent 原油 | BZ=F 期貨(ICE 近月) | BNO 代現貨 · EIA Brent Spot | YFINANCE + EIA | CM-01 · CM-22 |
| WTI 原油 | CL=F 期貨(NYMEX 近月) | USO 代現貨 · EIA Cushing WTI Spot | YFINANCE + EIA | CM-02 · CM-18 |
| WTI 次月 / 曲線 | CL=F M2 · M3 | — | YFINANCE + CME | CM-22 |
| Brent–WTI 價差 | BZ=F − CL=F | — | VDF 推導 | CM-01 · CM-02 |
| 天然氣 | NG=F 期貨 | UNG 代現貨 | YFINANCE + EIA | CM-09 · CM-13 |
| 汽油 / 熱燃油 | RB=F · HO=F | — | YFINANCE | CM-09 |
| 黃金 | GC=F 期貨(COMEX) | XAUUSD=X 現貨 · LBMA 定盤 | YFINANCE + LBMA | CM-03 · CM-23 |
| 白銀 | SI=F 期貨 | XAGUSD=X 現貨 | YFINANCE + LBMA | CM-04 · CM-11 |
| 白金 | PL=F 期貨 | XPTUSD=X 現貨 | YFINANCE | CM-04 |
| 鈀金 | PA=F 期貨 | XPDUSD=X 現貨 | YFINANCE | CM-04 |
| 黃金 ETF 實物噸數 | — | GLD · IAU · GLDM tonnesHeld | issuer 每日揭露 | CM-10 · CM-16 |
| 銅 | HG=F 期貨(COMEX) | LME Copper Cash · AkShare 滬銅 | YFINANCE + AKSHARE | CM-05 · CM-23 |
| 鋁 / 鎳 / 鋅 | LME 3M · AkShare 滬鋁滬鎳滬鋅 | — | AKSHARE + LME | CM-05 |
| 鐵礦砂 | AkShare 大商所 i 主連 | — | AKSHARE | CM-05 |
| 玉米 / 小麥 / 黃豆 | ZC=F · ZW=F · ZS=F | — | YFINANCE | CM-06 · CM-24 |
| 黃豆油 / 黃豆粉 | ZL=F · ZM=F | — | YFINANCE | CM-06 |
| 糖 / 咖啡 / 可可 / 棉花 | SB=F · KC=F · CC=F · CT=F | — | YFINANCE | CM-06 |
| 美元指數 DXY | DX-Y.NYB · DX=F 期貨 | — | YFINANCE | FX-01 |
| 新台幣 | TWD=X(USD/TWD) | 央行盤中即時 | YFINANCE + CBC | FX-02 |
| 日圓 | JPY=X(USD/JPY) | — | YFINANCE | FX-02 |
| 歐元 | EURUSD=X | — | YFINANCE | FX-02 |
| 英鎊 | GBPUSD=X | — | YFINANCE | FX-02 |
| 人民幣 · 在岸 CNY | CNY=X(USD/CNY) | 中國外匯交易中心中間價 | YFINANCE + AKSHARE | FX-02 |
| 人民幣 · 離岸 CNH | CNH=X(USD/CNH) | — | YFINANCE | FX-02 |
| 在岸離岸價差 CNY−CNH | — | — | VDF 推導 | FX-02 |
| 1M / 3M / 6M | ^IRX(13週)· Treasury par yield | DGS1MO · DGS3MO · DGS6MO | Treasury + FRED | FX-03 |
| 1Y / 2Y / 3Y | DGS1 · DGS2 · DGS3 | — | Treasury + FRED | FX-03 |
| 5Y / 7Y / 10Y | ^FVX(5Y)· ^TNX(10Y)· DGS5/7/10 | — | Treasury + FRED | FX-03 |
| 20Y / 30Y | ^TYX(30Y)· DGS20 · DGS30 | — | Treasury + FRED | FX-03 |
| 10Y−2Y · 10Y−3M 利差 | T10Y2Y · T10Y3M | — | VDF 推導 + FRED | FX-04 |
| TIPS 實質利率 · 通膨補償 | DFII10 · T10YIE | — | FRED | FX-07 |
| VIX | ^VIX · VX=F 期貨 | — | YFINANCE + CBOE | PX-06 · SE-01 |
| VVIX / SKEW / MOVE | ^VVIX · ^SKEW · ^MOVE | — | YFINANCE + ICE | PX-06 |
| VIX 期限結構 | VX=F M1 · M2 · M3 | — | CBOE + YFINANCE | PX-06 |
| 比特幣 | BTC-USD · BTC=F 期貨(CME) | — | YFINANCE + CME | CY-01 |
| 以太幣 | ETH-USD · ETH=F 期貨 | — | YFINANCE + CME | CY-02 |
| 主流幣(SOL/XRP/BNB/ADA/DOGE) | SOL-USD · XRP-USD · BNB-USD · ADA-USD · DOGE-USD | — | YFINANCE + CoinGecko | CY-03…CY-07 |
| 現貨 BTC / ETH ETF | IBIT · FBTC · ETHA · nav/aum/units | — | issuer + YFINANCE | CY-08 · CY-09 |
| BDI 波羅的海乾散貨 | AkShare bdi 指數 | — | AKSHARE | CM-07 |
| SCFI 上海出口貨櫃 | AkShare scfi | — | AKSHARE | CM-08 |
| 台股加權 · 櫃買 | ^TWII · ^TWOII | — | YFINANCE + TWSE | PX-04C |
| 費城半導體 | ^SOX | SOXX · SMH 代理 | YFINANCE | PX-06C |

無真實現貨行情者(原油、天然氣)以 EIA 官方 spot 或 ETF 代理標記,並帶 isFuturesProxy 與 rollDecayFlag(CM-25),不得逕稱現貨。

VIA VDF FETCH ONE · VDF-FETCH/1.0
