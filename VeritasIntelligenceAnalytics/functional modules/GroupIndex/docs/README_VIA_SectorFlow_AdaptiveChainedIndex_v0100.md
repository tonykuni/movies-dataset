# def VIA 族群資金流 × 全動態 Criteria × 無斷裂鏈接指數 v0.1.00

## def 系統目的

將「台股族群量價/資金位移」設計方法(Leader/Peer/Laggard 三分類、剔除 Laggard 的
鏈接指數、扣除台積電與當沖的實質資金、四路主力歸因、宏觀壓力閘門)工程化為
可執行、可驗證、可回測的 VIA 管線,並完成:

```text
def TEST-1 → DEBUG-1 → OPTIMIZE-1 → TEST-2 → DEBUG-2 → BACK-TEST
→ DEBUG-3 → CONSOLIDATE → TEST-3 → DEBUG-4 → ACTIVATE → FINAL-TEST
def 外層收斂迴圈:Hard Failure > 0 即自動重跑,直到全綠(本輪第 1 次迭代即收斂)
```

## def 原設計缺陷修復(Repair Ledger)

| Repair | 原設計問題 | 修復 |
|---|---|---|
| def R01 | 殘差化使用固定 0.40/0.60 Beta | 逐股滾動 OLS(截距 + SOX(t-1) + TWSE) |
| def R02 | Leader/Peer 判定含固定相關係數紅線 | GMM-BIC 動態狀態 + 置換證據 |
| def R03 | 固定基期重算造成換檔跳空 | 幾何鏈接 + 連續性稽核 + 對照組 gap 證據 |
| def R04 | max-lag 搜尋放大偶然峰值 | circular-shift max-lag 置換 null |
| def R05 | 固定資金位移/量能門檻 | HHI 集中度動態分位 + 族群 CV 帶 |
| def R06 | 投信 Z 門檻固定 1.2 | expanding 池化 median+3·1.4826·MAD(資料導出) |
| def R07 | 規模分級固定 0.85/0.35 邊界 | GMM 動態分級 + 後驗信心遲滯緩衝 |
| def R08 | 宏觀乘數固定 0.5/1.5 切點 | 壓力指數 GMM 狀態離散化 + median/MAD fallback |

## def 核心方法

```text
def Universe
= SSOT 14 個 L1 族群 × 298 檔 COUNT 成員(含 2330)
+ 合成 ETF/權證/特別股注入 → 清洗必須全數隔離(fail-closed)

def Real Turnover
= Turnover - Daytrade Turnover(非負)

def Market Denominator
= Σ Real Turnover - Real Turnover(2330)

def Chained Index
= 剔除 LAGGARD 之 LEADER/PEER 池
× sqrt(前日實質成交額) 加權
× I(t) = I(t-1) × (1 + R_basket)
× 基期 2026-01-02 = 100.0
× 半年首個交易日換檔(H1/H2),連續性稽核 gap ≤ 1e-8

def Roles(半年定審,回看 60 交易日,零窺探)
= 指數衰減加權 lead-lag(動態 max-lag)
+ circular-shift 置換證據
+ GMM-BIC 同步/領先狀態
→ LEADER / PEER / LAGGARD / MEMBER(+ Floor Fallback)

def Capital Flow States(全動態門檻)
= STEALTH_ACCUMULATION / INFLOW_EXPANDING / OUTFLOW_DRAINING
/ RETAIL_WHALE_SPECULATION / NEUTRAL_ROTATION
(自身歷史 expanding robust-z × 池化 3-MAD 顯著性 × HHI 動態分位)

def Signals
= DYNAMIC_SETUP / DYNAMIC_BUY / DYNAMIC_EXIT / HOLD
(宏觀壓力 GMM 狀態 → 曝險乘數 1.0/0.5/0.0 閘門)
```

## def Back-test 結果(controlled DGP,4 情境 × 2 種子)

| 情境 | Event Precision | Event Recall | False Alarm | 連續性 |
|---|---:|---:|---:|---|
| def ROTATION | 0.90–0.97 | 1.000 | ≤0.007 | PASS |
| def STEALTH_ACCUMULATION | 0.94–0.95 | 1.000 | ≤0.005 | PASS |
| def DRAIN | 0.80–0.84 | 1.000 | ≤0.011 | PASS |
| def MARKET_TIDE(null world) | — | — | ≤0.010 | PASS |

```text
def Market Tide 殘差控制
= raw within-corr 中位 ~0.62-0.66 → residual ~0.10(假族群性被剝除)

def 鏈接法必要性
= 固定基期重算法換檔日人工跳空最大 3.2%~11.5%;鏈接法 gap = 0

def 宏觀熔斷
= MARKET_TIDE 壓力階梯觸發 20-24 個停開倉日

def 上述數字是受控世界的邏輯驗證,不代表真實交易勝率。
```

## def 最終狀態

```text
def Final Gate = CONTROLLED_ACTIVATION_PASS_REVIEW_WARNINGS_RETAINED
def Hard Failures = 0(24 項 HARD 全 PASS)
def Review Warnings = 1(F26:SSOT 無 MethodA 角色成員,保留 fail-closed)
def Pytest = 9 passed
def Convergence Iterations = 1
def Manifest = VERIFIED(不可變後驗)
def Canonical Mutation / Network / Order = 0 / 0 / 0
```

## def 執行

```powershell
python .\VIA_SectorFlow_AdaptiveChainedIndex_v0100.py
python -m pytest -q test_VIA_SectorFlow_AdaptiveChainedIndex_v0100.py
```

## def 真實資料接線

替換 `def_generate_sector_panel` 為真實面板即可,分析核心不必重寫:

```text
def 必要欄位
= Date × Ticker × AdjClose × Turnover × DaytradeTurnover
× ForeignNet × TrustNet × DealerNet × WhaleNet
def 宏觀欄位
= SOXRet / TWSERet / VIXLevel / US10YDiff / JPYDiff / TWDResidual / OilDiff
(TWDResidual = 台幣對美元指數滾動 OLS 殘差,外資真錢匯流強度)
```

## def 沙盒執行邊界

```text
def Python Engine / Pytest / Controlled Back-test / HTML / Manifest
= 已在本沙盒實際執行並通過
def 前端 React 儀表板(Treemap/折線/長條)
= 屬另一交付層;本引擎輸出之 CSV/PNG/HTML 為其資料契約來源
```
