# VIA｜官方數據收件率：CES 機構 vs CPS 家庭 · 雙方比較 v001

Generated: 2026-07-05 · 來源：SF Fed / Atlanta Fed / BLS OSMR / Census（公開）
一句話：**兩份調查收件率都長期下滑；市場當天反應的「非農首報」建立在收件率最低（<45%–60%）的樣本上——你原本說的「60% 掉到 40 幾%」，對 CES 首報成立。**

---

## 1. 雙方比較表

| 面向 | **CES 機構調查**（非農 / payroll） | **CPS 家庭調查**（失業率）|
|---|---|---|
| 調查對象 | 企業／機構（以 UI 稅號抽樣）| 家庭／個人 |
| 樣本規模 | ~119,000 事業體 / ~631,000 worksites；每月約 270,000 份回覆 | ~60,000 家庭 |
| **收件率（疫情前/十年前）** | 疫情前十年 **≈60%** | 十年前 **高 80%** |
| **收件率（近年）** | 首次估計 **<45%**（2024/6–2025/1 谷底，部分因 sample-initiation 下降）| **≈70% 上下**；2025 關門後 Sep→Nov 再跌 **~5pp** |
| 收件三段結構 | 首報(低) → 二修 → 終值 **~90%+** | 單次收集（MIS 1–8 輪換）|
| 月變動誤差 | 樣本大 → 月變動誤差**小**（±約122k）| 樣本小 → 月變動誤差**大**（±約650k）|
| 主要失真風險 | 首報樣本不足 → 後續大修正、年度 benchmark（2025/3 −89.8 萬）| 非回應偏誤；**2025/10 整月 CPS 資料遺失**（政府關門）|
| 因應 | — | BLS/Census 2027 導入 web self-response |

---

## 2. 重點解讀

**CES（機構／非農）**
- SF Fed：CES 首次估計收件率「疫情前十年在 60% 上下，之後降到**低於 45%**」。
- 三段收件：**首報**收件率最低 → 二修、終值補到 ~90%+。**問題在於：市場當天反應的是首報，卻是收件率最低的那一版**，所以每月修正幅度大。
- BLS OSMR 註記：2024/6–2025/1 的低收件率部分來自 sample-initiation 下降（非純非回應）。

**CPS（家庭／失業率）**
- Census：CPS 十年前常態收件率在**高 80%**，此後持續下滑（近年約 70% 級距）。
- Atlanta Fed：2025 政府關門後，CPS 收件率 Sep→Nov **驟降近 5 個百分點**；**2025 年 10 月整月 CPS 資料遺失**，導致 Oct 2025 與 Oct 2026 的年增（YoY）出現缺口。
- 關門前無寄發前置信函 → 11 月的面訪成為 10 月與 11 月世代的首次接觸，壓低回覆。

**共同**
- 兩者皆長期下滑；**CES 首報跌最凶**。此為全球現象（英國 LFS、加拿大 LFS 同樣下滑）。
- ⚠ CRS 澄清：收件率下滑**不是每月修正的主因**（主因是後續補件），但**對年度 benchmark 修正影響較大**——引用時要精準，別把兩者混為一談。

---

## 3. 對你原始論點的驗證
- 你最初稱「官方收件率從 60% 以上掉到 40 幾%」。
- **對 CES（非農首報）成立**：疫情前 ≈60% → 近年 <45%（SF Fed）。方向與量級都對。
- 先前我在故事定稿把這句降級為「定性：長期下降」，是因為缺一手數字；**現在有 SF Fed 一手圖佐證，可升級為可引用的具體區間（~60% → <45%）**，但仍建議標注「首報 first-closing」以免與終值 90%+ 混淆。

---

## 4. 對風險引擎 D6 的意義
- 「首報樣本不足 → 大修正」是「就業數據隱藏失真」的**制度性**來源，與家庭 vs 機構背離、benchmark −89.8 萬、勞參崩並列。
- 標準化建議：把「首報收件率」本身當一個資料品質折扣因子——收件率越低，該月非農首報在 D6 的權重越低（併入 data_quality_adjusted 分數）。

---

## 5. 缺口 / 待補
- CES / CPS **近月單月收件率精確值**：BLS OSMR「Household and establishment survey response rates」頁有逐月圖表與表格，建議 VDF 直接抓該頁數列（非 FRED series）。
- CPS 近年精確收件率（~70% 是級距，非單月官方值）待該頁確認。

---

## 6. 來源（URL）
- BLS OSMR 收件率總頁（逐月圖表）：https://www.bls.gov/osmr/response-rates/home.htm
- CPS 收件率方法頁：https://www.bls.gov/cps/methods/response_rates.htm
- SF Fed：低收件率是否威脅 data dependence（CES ~60%→<45%）：https://www.frbsf.org/research-and-insights/publications/economic-letter/2025/03/do-low-survey-response-rates-threaten-data-dependence/
- Atlanta Fed：2025 關門後 CPS 收件率驟降：https://www.atlantafed.org/research-and-data/publications/policy-hub-macroblog/2026/04/09/more-than-missing-data-survey-response-rates-following-2025-government-shutdown
- Census：CPS 現代化（十年前高 80%）：https://www.census.gov/programs-surveys/cps/about/modernization.html
- CES vs CPS 比較（BLS）：https://www.bls.gov/web/empsit/ces_cps_trends.htm
