# VDF FETCH ONE · 擷取資料總冊(操作員批228 貼入原件收容)
收容時間:2026-08-28 · 血統:操作員對話貼入(as-received 轉錄)· append-only
宣告性質:「本頁狀態為宣告值,實際可用性須由 vdf_api 健康檢查回寫;
未接後端時以宣告為準,不得視為已驗證。」

## 總覽計數(宣告值)
- 390 資料項 Items · 17 領域 Domains · 187 來源 Sources · 10 Fetchers · 20 Engines
- 狀態:296 DONE · 75 PROXY · 19 TODO
- 標記:🔒 VDF-FETCH/1.0 · ADJ 優先 · VIA-M-VDFONE

## 核心規則(契約層)
1. **價格來源優先序**:凡有 adjClose 者一律優先於 close,並以 Adj 全序列
   計算報酬、正規化與技術指標;無 adj 者以一般價格為準。遇 stock split
   同步調整 volume。
2. **缺值與頻率對齊**:價格缺值取前一交易日;成交量不補。混頻(日×月)
   以低頻為對齊基準,堆疊圖共用同一時間映射,絕對對齊。
3. **必要欄位**:required date · value;optional series · unit · freq ·
   adjClose · volume · source · asof。單位隨欄位帶入以決定左右軸。
4. **狀態驗證**:DONE=fetcher 已實作且例行跑通;PROXY=以代理源近似
   (FRED 代理、ETF 代指數)須標記;TODO=尚未接線。
5. **權威層級**:官方(政府/交易所/央行)> 授權商業源 > 代理(FRED proxy)
   > 推導模型。代理與推導須標記來源與計算式,不得混入官方層。

## 憑證層級(可得性)
| 層級 | 項數 | 憑證 | 判定 |
|---|---|---|---|
| 免憑證公開端點 | 261 | 無 | 可得(TWSE/TPEX/MOPS/Treasury/yfinance/TDCC/投信官網/akshare/Census/BLS/Fed/OECD) |
| FRED API KEY | 78 | P4 必填 | 貼入當下宣告「金鑰未設定→不可得」(涵蓋 CPI/PCE/PPI 全分項、勞動力、殖利率曲線、金融條件)※雲端 key 在位(gitignored);工作站候放 key |
| 授權·訂閱源 | 19 | 付費授權 | 未授權不可得(MSCI/LME/LBMA/IEA OMR/S&P Global PMI/SEMI-WSTS/CME/FactSet(Cnyes 代)/II) |
| 爬取·無公開 API | 13 | 逐源議定 | 合規確認後方可得(ADP/MBA/AAII/CNN F&G/NAR/ATA·AAR/NFIB/NAHB/CoinGecko;多為 proxy) |
| TODO 未接線 | 19 | — | 不可得 |

## 參數契約(全系統僅 4 可變參數;localStorage:vdf_params)
- **P1 國際股票清單 Ticker Universe**:唯一可增減參數;輸入顯示分離;
  字典解析;38 檔預置(美股 22:NVDA/AMD/AVGO/TSM/MU/INTC/QCOM/ARM/
  MRVL/SMCI/DELL/ANET/VRT/MSFT/GOOGL/AMZN/META/AAPL/ORCL/CRM/NOW/PLTR;
  台上市 6:2330/2454/2317/6669/3231/2382;上櫃 1:3324;日 3:6758/8035/
  6857;韓 2:005930/000660;港 3:1211/0700/0981;歐 1:ASML.AS)。
  後綴規約 .TW/.TWO/.HK/.T/.KS/.KQ/.AS/.L/.DE/.PA;純數字 4 碼=台股自動補綴。
- **P2 財報預設標的**:2330.TW · 3324.TWO · NVDA(台走 MOPS,美走 yfinance)
- **P3 起始日期 START_DATE**:2018-01-01(暫定可改;改此值即重抓全域歷史)
- **P4 FRED API KEY**:32 字元小寫英數;78 項總經序列必要憑證

## 資料庫現況摘要(依 4 參數推算宣告)
登錄 390 項/17 領域;P1=38 檔;歷史 8.7 年(2018→今);估計總列數 8.3M;
FRED 解鎖 0 項(貼入當下)。
資料集×估列:國際股票量價 38×日=83k(PX-03·MX-A4)/台上市 980×日=2.1M
(MX-A1)/台上櫃 838×日=1.8M(MX-A2)/財報三大表 3×季=315(FN-01…03)/
每股+月營收 3×月=312(FN-04…06)/主動 ETF 持股 37×日=3.2M(EF-01A…X·
MX-D1·MX-A12)/全球 ETF 宇宙 77×日=168k(MX-C1…C4)/美總經 78 項
(FRED 未設定)/台股共識 1,900×週=855k(Cnyes 代 FactSet;CS-01…06·MX-E1)。

## 17 領域計數
價格 48 · 商品 25 · 匯率利率 7 · 美國領先 22 · 美國同時 28 · 美國落後 21 ·
財政公債 6 · 聯準會 6 · 全球區域 41 · AI 概念股 17 · 擷取矩陣 25 ·
資金流品質 13 · 加密貨幣 10 · 情緒部位 13 · ETF 資金流 80 · 共識評價 6 ·
財報 22。

## 390 項代碼冊(碼|項|來源|fetcher|頻率|狀態;欄位細則見原頁)
### 價格 PX(48)
PX-01 台上市 OHLCV+籌碼|TWSE|market|日|DONE
PX-02 台上櫃 OHLCV+籌碼|TPEX|market|日|DONE
PX-03 全球股票/ETF OHLCV+Adj|YFINANCE|market|日|DONE
PX-04 全球指數總表|YFINANCE|market|日|DONE
PX-04A 美 ^GSPC ^DJI ^IXIC ^RUT ^NDX|YFINANCE|日|DONE
PX-04B 美類股 ^SOX ^SOXX ^BKX ^XAU ^DJT|YFINANCE|日|DONE
PX-04C 台 ^TWII ^TWOII ^NTX 台灣50|TWSE+YF|日|DONE
PX-04D 日 ^N225 ^TOPX 東證核心30|YFINANCE|日|DONE
PX-04E 中 ^SSEC ^SZSC 滬深300 創業板|YF+AKSHARE|日|DONE
PX-04F 港 ^HSI 恆生科技 國企|YFINANCE|日|DONE
PX-04G 韓 ^KS11 ^KQ11|YFINANCE|日|DONE
PX-04H 歐 ^STOXX50E ^GDAXI ^FCHI ^FTSE ^IBEX ^SSMI|YF|日|DONE
PX-04I 印 ^NSEI ^BSESN|YF|日|DONE
PX-04J 東南亞 ^STI ^KLSE ^SET ^JKSE ^VNINDEX ^PSI|YF|日|DONE
PX-04K 澳紐 ^AXJO ^NZ50|YF|日|DONE
PX-04L 加墨 ^GSPTSE ^MXX|YF|日|DONE
PX-04M 拉美 ^BVSP ^MERV ^IPSA|YF|日|DONE
PX-04N 中東 ^TASI ^ADI ^TA125|YF|日|PROXY
PX-04O 新興 MSCI(ETF 代理)|MSCI|日|PROXY
PX-04P 指數本地幣 vs 美元計價|VDF 推導|日|DONE
PX-05 ^SOX 成分與權重|YF+issuer|日|DONE
PX-05A 區域 ETF 美(SPY VOO IVV QQQ DIA IWM)|YF|日|DONE
PX-05B 區域 ETF 歐(VGK EZU FEZ EWG EWU EWQ)|YF|日|DONE
PX-05C 區域 ETF 日韓(EWJ DXJ BBJP EWY)|YF|日|DONE
PX-05D 區域 ETF 中港台(MCHI FXI KWEB ASHR EWH EWT 0050)|YF+TWSE|日|DONE
PX-05E 區域 ETF 印+東南亞(INDA INDY EWS EWM THD EIDO VNM)|YF|日|DONE
PX-05F 區域 ETF 新興/全球/拉美/中東(EEM VWO ACWI VT EWZ EWW KSA EIS)|YF|日|PROXY
PX-05G 區域 ETF 澳加(EWA EWC)|YF|日|DONE
PX-06 波動度族(VIX VVIX MOVE SKEW)|Yahoo|日|DONE
PX-06A 美 GICS 11 行業指數|S&P(FRED 代)|日|DONE
PX-06B SPDR 11 行業 ETF(XLK…XLC)|YF|日|DONE
PX-06C 科技細分(SMH SOXX IGV CIBR SKYY ARKK BOTZ ROBO)|YF|日|DONE
PX-06D 金融醫療工業細分(KRE KBE IBB XBI IHI ITA JETS XHB)|YF|日|DONE
PX-06E 能源原物料公用細分(XOP OIH AMLP XME LIT COPX URA TAN ICLN)|YF|日|DONE
PX-06F 台股 29 類股指數|TWSE|日|DONE
PX-06G 行業輪動相對強弱矩陣|VDF 推導(Adj)|日|DONE
PX-07 日內走勢+分鐘量|YF 1m/5m|分|DONE
PX-07A 日本指數群全量|YF+JPX|日|DONE
PX-07B 東證 33 業種|JPX|日|PROXY
PX-07C 日本外資與部門別買賣|JPX|週|PROXY
PX-07D 日本個股(TOPIX 成分)|YF .T|日|DONE
PX-07E 日本空單與信用|JPX|週|PROXY
PX-08 K 線技術族(SMA/EMA/BB;Adj 基)|VDF 推導|日|DONE
PX-08A 韓國指數群全量|YF+KRX|日|DONE
PX-08B KRX 業種|KRX|日|PROXY
PX-08C 韓外資機構買賣超|KRX|日|PROXY
PX-08D 韓個股(半導體重點)|YF .KS/.KQ|日|DONE
PX-08E 韓半導體出口×晶片景氣|關稅廳+KRX|月·日|PROXY
### 商品 CM(25)
CM-01 Brent 現+期(BZ=F;BNO/EIA)|YF+EIA|日|DONE
CM-02 WTI 現+期(CL=F;USO/EIA)|YF+EIA|日|DONE
CM-03 黃金現+期(GC=F;XAUUSD/LBMA)|YF+LBMA|日|DONE
CM-04 貴金屬(SI=F PL=F PA=F+現貨)|YF|日|DONE
CM-05 工業金屬(HG=F;LME/滬)|YF+AKSHARE|日|DONE
CM-06 農產(ZC ZW ZS ZL ZM SB KC CC CT)|YF|日|DONE
CM-07 BDI|AKSHARE|日|DONE
CM-08 SCFI|AKSHARE|週|DONE
CM-09 天然氣/電價(NG=F RB=F HO=F;UNG)|YF+EIA|日|DONE
CM-10 黃金 ETF(GLD IAU SGOL GLDM GDX GDXJ+噸數)|YF+issuer|日|DONE
CM-11 白銀白金族 ETF(SLV SIVR PPLT PALL)|YF+issuer|日|DONE
CM-12 原油 ETF(USO BNO UCO XLE XOP OIH)|YF+issuer|日|DONE
CM-13 天然氣能源 ETF(UNG BOIL AMLP)|YF|日|DONE
CM-14 綜合商品 ETF(DBC PDBC GSG COMT)|YF+issuer|日|DONE
CM-15 工金農產 ETF(CPER COPX JJC DBA CORN WEAT SOYB)|YF|日|DONE
CM-16 商品 ETF 實物持有量(噸/桶/盎司)|issuer|日|DONE
CM-17 商品 ETF 淨流(Δunits×NAV)|VDF 推導|日|DONE
CM-18 原油庫存(商業/Cushing/SPR)|EIA 週報+API|週|DONE
CM-19 原油供給(美產量/OPEC+ 配額)|EIA+OPEC MOMR|週·月|PROXY
CM-20 原油需求平衡表|IEA OMR+EIA STEO|月|PROXY
CM-21 鑽井平台數+頁岩成本|Baker Hughes+EIA|週|DONE
CM-22 原油期貨曲線+轉倉(M1 M2 M3)|YF+CME|日|DONE
CM-23 實體金屬倉儲(LBMA/LME/ETF 交叉)|LBMA+LME+issuer|日|PROXY
CM-24 農產供需 WASDE|USDA|月|TODO
CM-25 商品 flow 代理 ETF×價格基準|VDF 推導|日|DONE
### 匯率利率 FX(7)
FX-01 DXY(DX-Y.NYB DX=F)|YF|日|DONE
FX-02 主要匯率(EUR JPY GBP CNY CNH TWD+價差)|YF+CBC+AKSHARE|日|DONE
FX-03 美債殖利率曲線 1M-30Y|Treasury+FRED|日|DONE
FX-04 利差 10Y-2Y/10Y-3M|VDF 推導+FRED|日|DONE
FX-05 隔夜利率(SOFR EFFR RRP)|FRBNY(FRED 代)|日|PROXY
FX-06 公司債信用利差 IG/HY OAS|FRED|日|DONE
FX-07 TIPS 實質+通膨補償(DFII10 T10YIE)|FRED|日|DONE
### 美國領先 US-L(22)
L01 ISM 製造(分項)|FRED 代|月|PROXY
L02 ISM 非製造(分項)|FRED 代|月|PROXY
L03 S&P Global PMI|S&P|月|PROXY
L04 ConfBoard LEI|FRED 代|月|PROXY
L05 初領+續領失業金|DOL(FRED)|週|DONE
L06 建照+新屋開工|Census(FRED)|月|DONE
L07 耐久財新訂單|Census(FRED)|月|DONE
L08 密大信心+通膨預期|UMich 代|月|PROXY
L09 ConfBoard 信心|代|月|PROXY
L10 OECD CLI|代|月|PROXY
L11 ISM 製造 10 分項全展開|代|月|PROXY
L12 ISM 非製造 9 分項全展開|代|月|PROXY
L13 地區 Fed 製造調查 5 區|官方|月|DONE
L14 NFIB 小企業|代|月|PROXY
L15 NAHB 房市|代|月|PROXY
L16 成屋+新屋銷售|NAR/Census(FRED)|月|DONE
L17 MBA 房貸申請|MBA|週|PROXY
L18 消費信心 8 分項對照|UMich×CB|月|PROXY
L19 金融條件 NFCI/ANFCI|Chicago Fed(FRED)|週|DONE
L20 SLOOS 信貸緊縮|Fed|季|PROXY
L21 運輸領先(ATA 卡車/AAR 鐵路)|代|月|PROXY
L22 半導體 B/B+WSTS 全球銷售|SEMI/WSTS|月|TODO
### 美國同時 US-C(28)
C01 GDP+平減|BEA 代|季|PROXY;C02 GDP 四組成|代|季|PROXY;
C03 非農+修正|BLS(FRED)|月|DONE;C04 U3/U6+勞參|DONE;C05 失業持續期|DONE;
C06 ADP|PROXY;C07 JOLTS|DONE;C08 時薪工時|DONE;C09 零售+core|DONE;
C10 PCE+所得儲蓄|代|PROXY;C11 工業生產+產能|DONE;C12 貿易|DONE;
C13 GDP 貢獻拆解|代|PROXY;C14 民間投資細分|代|PROXY;C15 政府支出細分|代|PROXY;
C16 進出口細分|DONE;C17 零售 13 分項|DONE;C18 PCE 三大類|代|PROXY;
C19 非農 12 產業|DONE;C20 民間 vs 官方就業對照|DONE;C21 廣義失業率|DONE;
C22 工業生產分項|DONE;C23 庫存銷售比|DONE;C24 消費信貸 G.19|DONE;
C25 家庭債務違約 NY Fed|PROXY;C26 儲蓄率+DPI|代|PROXY;C27 汽車 SAAR|DONE;
C28 M1 M2+速度|DONE
### 美國落後/物價 US-G(21)
G01 CPI+核心全分項|DONE;G02 PPI+核心|DONE;G03 PCE 物價|代|PROXY;
G04 ULC+生產力|DONE;G05 企業獲利|代|PROXY;G06 房價 CS/FHFA|DONE;
G07 CPI 八大類|DONE;G08 CPI 關鍵細項(shelter/OER/二手車…)|DONE;
G09 CPI 切分(核心服務/商品/超核)|推導|DONE;G10 黏性彈性物價|DONE;
G11 PPI 三階|DONE;G12 PPI 服務商品|DONE;G13 核心 PCE 分項|代|PROXY;
G14 Trimmed/Median|DONE;G15 進出口物價|DONE;G16 ECI+薪資追蹤|DONE;
G17 ULC 細分|DONE;G18 通膨預期(市場×調查)|DONE;G19 獲利分項|代|PROXY;
G20 破產統計|TODO;G21 租金領先 Zillow|TODO
### 財政公債 FI(6)
FI-01 DTS 日報|DONE;FI-02 MTS 月報|DONE;FI-03 盈餘赤字推導|DONE;
FI-04 債務餘額+債限|DONE;FI-05 發行標售+持有人|DONE;FI-06 主權評等|TODO
### 聯準會 FD(6)
FD-01 FOMC 決議聲明|DONE;FD-02 SEP 點陣|DONE;FD-03 語調 NLP|DONE;
FD-04 官員發言|DONE;FD-05 FF 期貨隱含路徑|CME|PROXY;FD-06 H.4.1 資產負債|DONE
### 全球區域 GL(41)
GL-01 歐 rate/HICP/PMI|代|PROXY;GL-02 日 rate/CPI/Tankan|代|PROXY;
GL-03 英|代|PROXY;GL-04 中 PMI/CPI/PPI/社融|AKSHARE|DONE;
GL-04A 中 A 股指數板塊|DONE;GL-04B 中商品期貨全品種|DONE;
GL-04C 中宏觀月報全表|DONE;GL-04D 中貨幣信貸|DONE;GL-04E 中港基金 ETF|DONE;
GL-04F AkShare 欄位標準化對映|DONE;GL-05 台景氣燈號/外銷訂單|TODO;
GL-06 東南亞|TODO;GL-07 印度|TODO;GL-08 中東|TODO;GL-09 澳洲|TODO;
GL-10 全球 GDP 恆等式|推導|DONE;GL-11 歐製造 PMI 分項|PROXY;
GL-12 歐服務綜合 PMI|PROXY;GL-13 日 PMI|PROXY;GL-14 中官方 PMI 全分項|DONE;
GL-15 財新 PMI|DONE;GL-16 英 PMI|PROXY;GL-17 台 PMI/NMI(中經院)|TODO;
GL-18 韓印東南亞 PMI|PROXY;GL-19 澳加巴墨 PMI|PROXY;
GL-20 全球 PMI 熱圖|推導|DONE;GL-21 歐 HICP 分項|PROXY;GL-22 歐 PPI|PROXY;
GL-23 日 CPI 分項|PROXY;GL-24 日 CGPI|PROXY;GL-25 中 CPI/PPI 分項|DONE;
GL-26 英 CPI/RPI|PROXY;GL-27 台 CPI/WPI(主計總處)|TODO;
GL-28 韓印東南亞 CPI/PPI|PROXY;GL-29 全球通膨矩陣|推導|DONE;
GL-30 主要體就業全分項|PROXY;GL-31 歐就業細項|PROXY;GL-32 日就業細項|PROXY;
GL-33 中就業細項|DONE;GL-34 台就業細項|TODO;GL-35 韓就業細項|PROXY
### AI 概念股 AI(17)
AI-00 宇宙清單 30 檔五大類(占 SPX ~44%)|DONE;AI-01 核心半導體 7 檔|DONE;
AI-02 基建硬體記憶體 7 檔|DONE;AI-03 Hyperscalers 5 檔|DONE;
AI-04 軟體平台 6 檔|DONE;AI-05 終端資安 5 檔|DONE;AI-06 日內分鐘|DONE;
AI-07 市值+SPX 權重貢獻|DONE;AI-08 等權 vs 市值權指數|DONE;
AI-09 相對強弱輪動|DONE;AI-10 估值 fwdPER/PSR/PEG|DONE;
AI-11 共識 EPS+目標價|DONE;AI-12 capex+AI 營收揭露|PROXY;
AI-13 量能異常排行|DONE;AI-14 選擇權 OI+IV|PROXY;AI-15 ETF 曝險|DONE;
AI-16 台美供應鏈對照|DONE
### 擷取矩陣 MX(25)
MX-00 總覽 5 Section/24 子類|DONE;A1 台上市|DONE;A2 台上櫃|DONE;
A3 台指數|DONE;A4 國際個股+Adj|DONE;A5 國際指數|DONE;A6 FX|DONE;
A7 商品|DONE;A8 債券|DONE;A9 VIX 系|DONE;A10 Crypto|PROXY;
A11 台被動 ETF|DONE;A12 台主動 ETF(37 檔)|DONE;B1 物價|PROXY;
B2 勞動|DONE;B3 利率|DONE;B4 財政|DONE;B5 Fed+情緒|DONE;
C1 區域 ETF 77 檔|DONE;C2 行業 ETF|DONE;C3 債券 ETF|DONE;
C4 商品/FX ETF|DONE;D1 主動持股 10 投信|DONE;D2 TDCC 集保|DONE;
E1 台股共識 1,900 檔|DONE
### 資金流品質 FQ(13)
FQ-01 T86 三大法人(T+1 ASOF)|DONE;FQ-02 MI_MARGN 融資券|DONE;
FQ-03 維持率/使用率/券資比(推估)|DONE;FQ-04 當沖值當沖比|DONE;
FQ-05 去當沖真流(存量差分)|DONE;FQ-06 SBL 借券賣出|DONE;
FQ-07 品質折扣權重|DONE;FQ-08 zero-sum 語意閘|DONE;
FQ-09 T+1 ASOF 稽核|DONE;FQ-10 PCF 創贖真值|DONE;
FQ-11 SITCA 規模受益人|DONE;FQ-12 指數隱含總流(推估標記)|DONE;
FQ-13 多源交叉驗證(ETF×T86×北向×EPFR)|PROXY
### 加密 CY(10)
CY-01 主要幣現貨|PROXY;CY-02 總市值+穩定幣|PROXY;
CY-03 現貨 BTC ETF 11 檔|DONE;CY-04 現貨 ETH ETF 9 檔|DONE;
CY-05 加密 ETF 淨流|DONE;CY-06 持幣量託管|PROXY;CY-07 期貨槓桿型|PROXY;
CY-08 基差資金費率|TODO;CY-09 礦工鏈上|TODO;CY-10 對風險資產相關|DONE
### 情緒部位 SE(13)
SE-01 AAII|DONE;SE-02 CNN F&G 7 分項|DONE;SE-03 Put/Call|PROXY;
SE-04 CFTC COT|TODO;SE-05 融資券借券|DONE;SE-06 港牛熊街貨|TODO;
SE-07 牛熊重心回收價|TODO;SE-08 市場寬度|DONE;SE-09 綜合多空評分|DONE;
SE-10 AAII 多空差|DONE;SE-11 II 顧問牛熊|PROXY;SE-12 台股多空指標|DONE;
SE-13 週期判定轉折|DONE
### ETF 資金流 EF(80)
EF-01 台主動股票型 24 檔(00980A…00410A 逐檔 EF-01A…X)|投信×17|日|DONE
EF-40 海外主動 6 檔(00983A/00988A/00989A/00990A/00997A/00402A)|DONE
EF-41 債券主動 7 檔(00980D…00986D)|DONE;EF-42 主動總表 37 檔|DONE;
EF-43 新掛牌募集追蹤|DONE;EF-02 全球 ETF 資金流|EPFR 代|PROXY;
EF-03 規模折溢價|DONE;EF-04 TDCC 受益人|DONE;EF-05 跨資產輪動|DONE;
EF-06 持股交集分歧|DONE;EF-07 同步加減碼|DONE;EF-08 報酬歸因|DONE;
EF-09 週轉/新進撤出|DONE;EF-10 規模折溢價受益人|DONE;
EF-11 主動 vs 被動流|DONE;EF-12 台被動全清單|DONE;EF-13 NAV/IOPV|DONE;
EF-14 AUM/units|DONE;EF-15 申贖初級市場|DONE;EF-16 配息|DONE;
EF-17 平準金|TODO;EF-18 內扣費用|DONE;EF-19 追蹤誤差|DONE;
EF-20 流動性|DONE;EF-21 受益人分散|DONE;EF-22 融資券借券|DONE;
EF-23 槓反部位|DONE;EF-24 轉倉損耗|DONE;EF-25 海外成分區域|DONE;
EF-26 債券 ETF 存續信評 YTM|DONE;EF-27 產業主題曝險|DONE;
EF-28 重疊度矩陣|DONE;EF-29 報酬風險(Adj)|DONE;EF-30 美 ETF 流|PROXY;
EF-31 被持有次數|DONE;EF-32 事件簿|DONE;EF-33 流量基礎欄位|DONE;
EF-34 淨流主算式 Δunits×NAV|DONE;EF-35 價格 vs 流量效應|DONE;
EF-36 累計+動能|DONE;EF-37 flow/AUM|DONE;EF-38 跨類別矩陣|DONE;
EF-39 缺口代理標記|DONE
### 共識評價 CS(6)
CS-01 稀釋 EPS FY1/FY2|DONE;CS-02 目標價+家數|DONE;CS-03 評等分布|DONE;
CS-04 fwd PER/PBR(Adj÷共識)|DONE;CS-05 修正動能|DONE;CS-06 背離度|DONE
### 財報 FN(22)
FN-00 全上市櫃清單|DONE;FN-01 損益單季|DONE;FN-01A 年度|DONE;
FN-01B 累計|DONE;FN-02 資產負債單季|DONE;FN-02A 年度|DONE;
FN-03 現金流單季|DONE;FN-03A 年度|DONE;FN-03B 累計|DONE;
FN-04 比率分析 16 項|DONE;FN-05 基本 vs 稀釋 EPS|DONE;
FN-05A EBITDA/share|DONE;FN-05B BPS/CFPS/DPS/SPS|DONE;
FN-05C TTM 滾動|DONE;FN-05D 股本變動稀釋因子|DONE;FN-06 月營收逐檔|DONE;
FN-06A 創高連續標記|DONE;FN-06B 產業族群彙總|DONE;FN-07 公告時程|DONE;
FN-08 合併 vs 個體|DONE;FN-09 股利除權息|DONE;FN-10 品質閘門|DONE
