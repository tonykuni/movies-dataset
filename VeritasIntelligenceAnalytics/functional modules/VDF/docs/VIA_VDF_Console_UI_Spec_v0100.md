# VIA VDF 主控台 UI 設計契約 v0100(2026-08-31 行動端規格)

原型頁:claude.ai artifact「VDF 資料鑄造主控台」。registry 實測 238 項(FRED 源 48/yfinance 186)。

## def 左面板 = 參數輸入(僅此三類,其餘一律預設)

| 輸入 | 規則 |
| --- | --- |
| FRED API Key | **輸入一次即儲存**(本機 VIA_Deploy_Config.json,gitignore 不入庫);要更換才重輸 |
| 財報抓取範圍 | 當季(季報)/ 累計(YTD)/ 年報(含 PDF 附註)三選框 → VRN 車道 |
| 國際市場代號新增 | 輸入 via_code(如 Global.Index.EWG);Registry append-only 入冊後 fetcher 自動派發 |
| 起始日期 | 唯一日期參數;**迄日一律=最新** |

## def 右面板 = 資料庫狀態板(整理後庫存,每區:筆數/起訖/新鮮度)

1. **台股**:上市/上櫃普通股**分開列**(各 N 檔);每日交易+三大法人+融資券+當沖 →
   **每日總資訊單表**(整合視圖);加權/櫃買指數日線。registry:TW.Equity×15、TW.Index×34。
2. **國際股票/指數**:Global.Equity×10、Global.Index×40(SPY/QQQ/EWT/EWJ/FXI…)、
   US.Index×22(S&P500/NDX/SOX/**VIX**/XL 類股)、Sentiment×2(AAII/FearGreed)。
3. **商品貴金屬原油**:×11(金 GC/銀 SI/銅 HG/WTI CL/布蘭特 BZ/天然氣 NG…);FX×8;Crypto×5。
4. **美國經濟數據**:物價×6(CPI/PCE/PPI/UMich)、就業×6(非農/失業率/LFPR/時薪/JOLTS/初領)、
   房市×3(Case-Shiller/開工/30Y房貸)、成長×5(GDP/工業生產/產能利用/零售)、Fed×2+金融條件×3。
5. **美債/利率**:×16(FFR 上下限/SOFR/2Y/5Y/10Y/30Y 殖利率/利差)+信用×3(HY OAS/LQD)。
6. **ETF 分區**:registry 內 ETF 型 ×93 —— 美債(SHY/IEI/IEF/TLT/TIP)、信用(LQD/HYG/JNK)、
   區域(EWT/EWJ/EWY/FXI/MCHI/EEM/VWO)、台股(0050/006208/00878/00919/00929…)。
   **全部可算 AUA 與資金流進出**:ΔSharesOutstanding × NAV(T1 真流,GlobalETFFlow 引擎)。
7. **國際總經/央行(可新增 backlog)**:中國 GDP/PMI/宏觀/期貨/航運已入冊;
   待新增:ECB/BoJ/BoE 政策利率、全球 PMI 系列、政府支出/收入、詳細 PDF 經濟報告(VRN 車道)、歐日 CPI。

## def VRN 財報還原管線(交叉檢核契約)

1. 抓財報**首頁**與**年度財務報表頁**(多路來源)。
2. Layout 引擎 + OCR 還原表格原貌,按頁面類別分流 → BasicInfo / Summary / FinancialData。
3. 多路抓取交叉檢核(同欄位異源比對)。
4. 與 **VDF 歷史資料逐值比對,全部吻合才入庫**;不吻合 fail-closed 留審(100% 對帳)。

## def VAP 圖表契約

multiple plot 與 stacked plot 皆須支援 —— 現況:VIS 三加權指數(Equal/Tier/Attention 並立)、
GroupIndex 儀表板三大法人扣當沖堆疊資金流、月營收儀表板族群動能。VAP-CH-01..40 軸鎖不變。

## def 已部署確認(使用者提問)

- **主動式台股 ETF 分析**:已部署(VIA_ActiveStockETF,19/19+59/59,宇宙自動發現/NEW 標記/AUM/申贖流)。
- **月營收分析**:已部署(twrevenue:三層動能,**族群 31 群** group_analysis + **整體市場** analysis,
  週期股分流不進排名;selftest 8/8 + demo 端到端)。
