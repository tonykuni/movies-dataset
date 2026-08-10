# def VIA Global Flow / Event Resonance / ETF Flow SSOT
# def Detailed Hand-over Report
# def 日期：2026-08-07

> 歸檔註記(2026-08-10):本文為操作員交接報告原文,自對話訊息逐字保存;
> 為 MultiFactor 模組之方法論 SSOT。引擎 v0100 已於同日到位並驗證(見模組 README)。

---
## def 01｜交接摘要
本階段已完成一套金融市場多因子 SSOT 方法論規劃，核心目標是把「全球金融事件、美元共振、ETF 資金流、股債匯商品反應、事件時間軸、驗證與反驗證」整合成可追溯、可驗證、可演化的系統。
目前已有兩個重要基礎檔案：
| def 檔案 | def 角色 | def 狀態 |
| --- | --- | --- |
| def SSOT_VPT_ingest.json | 既有 SSOT 治理與 ingest 範例 | 可作金融 SSOT 治理模板 |
| def VIA_Console (2).html | 全球資金流動整合 Console | 可作多視圖 UI 外殼 |

`SSOT_VPT_ingest.json` 已明確包含治理政策，例如「只增不減」、「投影不得 Confirmed」、「provenance 必附」等，這些規則應完整移植到金融事件、ETF flow、美元共振模型。
`VIA_Console (2).html` 是一個「VIA · 全球資金流動 整合 Console」，已整合儀表板、世界資金流、風險層級流、累積淨流、正規化走勢、情境模擬、商品終端、族群監控、參數規格等九個視圖，適合承接未來 SSOT Dashboard。

---
## def 02｜已確立的總方向
目前不再只是做單一報告，而是建立：
```text
def VIA_Global_Market_Event_Resonance_SSOT
def VIA_ETF_Flow_Validity_Relation_Strength_SSOT
def VIA_USD_MultiFactor_Resonance_Attribution_Model
def VIA_MultiFactor_Causality_Resonance_Testing_Plan
```
整體系統目的：
```text
def 事件時間軸 → def 因子分類 → def 跨資產反應 → def ETF flow 驗證
→ def 美元共振歸因 → def 關連性 / 顯著性 / 領先性 / 影響性 → def 多因子共振
→ def 反驗證 → def 隱形因子偵測 → def 模型准入 → def SSOT 回寫
```

---
## def 03｜核心治理規則
| def 規則 | def 說明 |
| --- | --- |
| def append-only | 只增不減，不覆寫歷史判斷 |
| def provenance required | 每個事件、因子、資料來源都要有 provenance |
| def projection cannot be confirmed | 推估、投影、模型結果不得標 Confirmed |
| def correlation is not causality | 相關性不得直接寫成因果 |
| def event requires URL evidence | 事件必須有官方、新聞、研究或資料 URL |
| def validation before model update | 模型權重或規則更新必須連回驗證紀錄 |
| def anti-validation required | 沒有反證測試，不得標 supported |
| def target-specific causal role | 因果角色必須相對於特定 target，不得泛稱主因 |
| def no subjective fixed weights | 不用人工主觀權重，改用系統客觀驗證產生參數 |
| def no peak-only inference | 不用事件峰值直接回推主因 |

---
## def 04｜已完成的方法論主軸
### def 04.1｜關連性
A 與 B 是否一起動？方向是否一致？關係是否穩定？
方法:Pearson correlation(線性)、Spearman(排名)、rolling correlation(動態)、direction hit rate(方向一致率)、conditional correlation(分 regime)、tail correlation(危機尾部共振)。

### def 04.2｜顯著性
這個關係是否可能只是隨機？影響幅度是否有經濟意義？
方法:p-value、confidence interval、effect size、bootstrap、HAC / Newey-West、multiple testing correction、false discovery rate。

### def 04.3｜領先性
誰先動？誰只是結果？誰是同步確認？
方法:lead-lag correlation、Granger test、VAR、local projection、transfer entropy、event sequence test。

### def 04.4｜影響性
A 變動後，B 受影響多大？
方法:beta、effect size、incremental R²、drawdown contribution、permutation importance、SHAP / attribution。

### def 04.5｜多因子共振
| def 等級 | def 條件 | def 解讀 |
| --- | --- | --- |
| def R0 | 單一因子波動 | 不算共振 |
| def R1 | 兩個同類因子同向 | 初級共振 |
| def R2 | 跨資產因子同向 | 有市場意義 |
| def R3 | 股債匯商品信用共同確認 | 高風險共振 |
| def R4 | ETF flow / 外資流確認 | 資金共振 |
| def R5 | 官方事件 / 政策反應確認 | 系統性事件 |
| def R6 | 反驗證後仍成立 | 高可信共振 |

---
## def 05｜事件 SSOT 方法論
事件必須是可驗證資料物件。
必要時間欄位:background_start_date、trigger_date、market_break_date、stress_peak_date、policy_response_date、normalization_date、event_end_date。
必要證據欄位:evidence_id、source_name、source_type(official/news/research/data/policy_statement)、source_url、source_date、source_event_date、evidence_role(date_anchor/policy_anchor/market_reaction/causal_claim)、source_reliability(HIGH/MEDIUM/LOW)、verification_status(verified/pending/stale/conflicted)。

---
## def 06｜峰法推論改善原則
```text
def 峰值是結果證據，不是因果證據。
def 用 peak 定義壓力高點。用 trigger 找事件起點。用 lead-lag 找時間順序。
def 用 controls 找獨立解釋力。用反驗證排除假因果。用 SSOT 保存證據與不確定性。
```
不應寫:「2022 股債下跌是因為美元上漲」。
應寫:「在 2022 rate shock 事件中,US2Y 與 10Y real yield 相對於 QQQ/TLT drawdown 呈現 driver 角色,DXY 相對於 EEM/EM FX 壓力呈現 transmission/amplifier 角色,ETF flow 對部分區域呈現 outcome/confirmation 角色,causal_status = supported,仍需通過 USD-control、price-control、regime split 反驗證」。

---
## def 07｜ETF Flow 有效性方法論
五層驗證:Data Validity(shares outstanding/NAV/AUM 交叉)、Proxy Validity(holdings purity/AUM coverage/tracking error)、Relation Validity(correlation/rank/lead-lag)、Predictive Validity(forward return/drawdown warning/hit rate)、Causal Validity(event study/VAR/Granger/反驗證)。
ETF flow 型態:Primary(ΔShares×NAV)、AUM-Implied、Secondary Trading Pressure(≠真 flow)、Holdings-Allocated、USD-Adjusted。
反驗證:price-control、USD-control、volume-control、lag inversion、placebo ETF、hedged ETF、leverage inverse exclusion、lookahead bias、regime split。

---
## def 08｜美元多因子共振模型
因子群:USD Price(DXY/UUP/BIS NEER-REER)、Rates(US2Y/10Y/30Y/curve)、Real Yield(10Y real/TIP-TLT/breakeven)、Fed Policy(EFFR/SOFR/IORB/Fed futures)、Liquidity(balance sheet/reserves/TGA/RRP)、Credit(HYG/JNK/LQD/EMB/HY spread)、Volatility(VIX/MOVE/VVIX)、Commodity(Oil/Copper/Gold/DBC)、Regional FX(JPY/CNH/KRW/TWD/BRL/MXN/INR)、ETF Flow(SPY/QQQ/EEM/VWO/EWT/EWY)。
美元角色:Safe-Haven(VIX↑ HYG↓ EMB↓ DXY↑)、Rate-Driven(US2Y↑ real yield↑ DXY↑)、Liquidity-Squeeze(reserves↓ TGA↑ EM FX↓ DXY↑)、Confidence-Loss(美股跌 長債跌 黃金漲 美元不漲或下跌)。

---
## def 09｜因果角色標籤
driver(領先、增量解釋力、反證通過)、amplifier(放大波動)、transmission(傳導壓力)、outcome(結果)、feedback(結果反饋原因)、confirmation(同步確認)、noise(不穩定或反證失敗)、hidden(未命名但結構顯示存在)。
同一因子對不同 target 可有不同角色(DXY 對 EEM = transmission/amplifier;DXY 對 US2Y = outcome 或 coincident;real_yield 對 QQQ = driver;ETF flow 對價格 = outcome/confirmation/amplifier 需驗證)。

---
## def 10｜隱形因子規劃
強因子 = 已命名且驗證後具高影響力;隱形因子 = 未命名但由資料結構顯示存在。
偵測:PCA、ICA、dynamic factor model、clustering、network graph、residual correlation、change point detection、nonlinear embedding。
隱形因子不得標 Confirmed,只能標:Hidden_Candidate、Hidden_Supported、Hidden_NeedsInterpretation、Hidden_Rejected。

---
## def 11｜客觀參數由系統產生
不採人工固定權重(如 30/35/35)。改為:系統自動產生候選參數 → 歷史事件驗證 → 反驗證淘汰假訊號 → 樣本外選擇 → 寫回 SSOT。
系統產生參數:time_window(5d/20d/60d/120d/event window 比較)、factor_rank、regime_label、causal_role、resonance_level、hidden_factor、model_permission(allow/monitor_only/reject)、review_priority(risk×uncertainty×market impact)。

---
## def 12｜建議引擎分層
E01 Data Legality & Provenance、E02 Factor Registry、E03 Event Timeline、E04 Time Alignment、E05 Relation、E06 Significance、E07 Lead-Lag、E08 Impact、E09 Resonance、E10 Causality Role、E11 Anti-Validation、E12 Hidden Factor、E13 Model Permission、E14 SSOT Update。

---
## def 13｜SSOT 核心資料表
factor_registry、target_registry、event_registry、event_evidence_ledger、factor_relation_ledger、resonance_matrix、anti_validation_ledger、hidden_factor_ledger、model_permission_ledger、model_update_ledger。

---
## def 14｜Console 對應規劃
九視圖承接:儀表板(今日主因/共振等級/警示)、世界資金流(ETF flow 區域)、風險層級流(T1-T4)、累積淨流、正規化走勢(股債匯金油)、情境模擬(事件/regime)、商品終端(DXY/WTI/Brent/Gold/台指期)、族群監控、參數規格(SSOT schema/驗證規則/模型准入)。

---
## def 15｜模型准入規則
只有關連性→monitor_only;顯著但 effect size 小→monitor_only;有 effect size 無領先性→confirmation_only;領先但反證失敗→reject;僅單一 regime→regime_specific;控美元後失效→USD_shadow;控價格後失效→price_chasing;樣本外+反證通過→allow;無 provenance→不得 Confirmed;推估/投影→不得 Confirmed。

---
## def 16｜目前已生成 / 已上傳資產
SSOT_VPT_ingest.json(治理模板)、VIA_Console (2).html(Console 外殼)、VIS_Launch_All.ps1(已安檢)、VIS_Launch_All.v011_SAFE.ps1(安全強化版)、VIA_Global_Event_Resonance_SSOT / ETF Flow Validity SSOT / MultiFactor Testing Plan(方法論已定義,尚未落地成檔)。

---
## def 17｜目前不應做的事
不應直接寫完整交易模型(schema 未定稿)、不應人工指定固定權重、不應只用 correlation、不應只用 peak date 推論主因、不應把 ETF flow 當真實市場 flow、不應把推估值標 Confirmed、不應讓無 provenance 資料進模型。

---
## def 18｜下一步建議
Phase A(完善規劃,不寫程式):SSOT schema、evidence_status enum(Confirmed/Estimated/NeedsVerify/Rejected)、event_type taxonomy(credit/liquidity/rate/fiscal/commodity/geopolitical)、factor_role taxonomy、model_permission、validation plan、Console 視圖規格。
Phase B(設計文件):System Design Memo、Data Dictionary、Engine Responsibility Matrix、Validation Method Ledger、Anti-Validation Checklist、UI Wireframe Spec。
Phase C(最後寫程式):Python engine、PowerShell launcher、DuckDB/Parquet storage、HTML dashboard、JSON config、validation report。

---
## def 19｜總結
```text
def 不是看單一指標。不是做一次性報告。不是手動指定權重。
def 不是用峰值回推原因。不是用相關性假裝因果。
```
真正目標:用合法資料建立因子與事件 SSOT;用客觀參數計算關連/顯著/領先/影響;
用多因子共振判斷特殊市場情境;用反驗證排除假訊號;用隱形因子偵測補足未知結構;
用模型准入規則決定 allow/monitor_only/reject;用 Console 顯示結果;
用 SSOT 保存證據、錯誤、驗證與模型更新。

最終工作名稱:
```text
def VIA MultiFactor Resonance SSOT Workbench
def 全球多因子共振驗證與金融事件 SSOT 工作台
```
