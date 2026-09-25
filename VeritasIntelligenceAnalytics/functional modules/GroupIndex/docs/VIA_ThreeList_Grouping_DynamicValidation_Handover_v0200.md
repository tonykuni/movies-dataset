# def VERITAS INTELLIGENCE ANALYTICS
# def 三清單 × 台股族群動態驗證管線 v0.2.00 — 詳細交接報告

## def 01｜交付結論

本輪已完成三份輸入的解析、隔離、衝突保留、動態 Criteria、39 群指數、39 張 residual heatmap、多情境回測、使用者測試及受控啟用。

```text
def Final Gate
= CONTROLLED_ACTIVATION_PASS_REVIEW_WARNINGS_RETAINED

def Hard Failures
= 0

def User-test Failures
= 0

def Manifest
= VERIFIED
```

受控啟用僅限 `RESEARCH_SANDBOX`。沒有改寫 canonical、沒有網路抓取、沒有自動下單。

## def 02｜來源治理

### def List A

```text
def rows = 238
def groups = 39
def unique tickers = 238
def role = ROW_LEVEL_CANONICAL_CANDIDATE
def counting = COUNT
```

### def List B

```text
def role = SCOPE_AND_GOVERNANCE_ONLY
def declared File1 groups = 31
def declared File2 codes = 271
def declared TW Console = 149 stocks / 31 groups
```

List B 數字與 List A 現況不同，系統以版本差異保存，不自動判定哪一版取代哪一版。

### def List C

```text
def rows = 27
def groups = 3
def role = DYNAMIC_TEST_COHORT
def counting = DISPLAY_ONLY
```

仲裁結果：

| 動態群 | 候選正式群 | 重疊 | 決策 |
|---|---|---:|---|
| def Thermal Solution | AI 散熱 | 8 / 10 | 別名候選，人工審查 |
| def CPO | AI 高速傳輸 | 1 / 9 | Fail-closed |
| def PCB | PCB | 2 / 8 | Fail-closed |

## def 03｜主要修正

| Repair | 問題 | 修正 |
|---|---|---|
| def R01 | v0100 角色判定仍含固定 0.60 / 0.80 | 改成 GMM-BIC 動態狀態 |
| def R02 | v0100 本地 run folder 與 ZIP 內容可能不一致 | 增加核心輸出完整、Manifest 與 replay Gate |
| def R03 | Canonical 39 群未全部生成 Heatmap | 39 群全部生成 residual heatmap |
| def R04 | Raw correlation 把市場潮水誤認族群性 | 市場殘差 + cross-group null |
| def R05 | 多 lag 搜尋提高偶然峰值 | circular-shift max-lag permutation |
| def R06 | 固定 L/P/G 權重內嵌主觀參數 | Full / Core 主指數改成 equal weight |
| def R07 | GMM 選單一元件時會漏掉廣泛真族群 | 以對 Null 的零差異作數學 fallback，不使用市場固定門檻 |
| def R08 | Manifest 先生成、後續 ledger 再變動 | Manifest 改為最後不可變輸出 |

## def 04｜Back-test 結果

Controlled DGP 使用四種情境、每情境兩個獨立種子：

| 情境 | Validity Precision | Validity Recall | Validity F1 | Role Macro F1 | False Positive |
|---|---:|---:|---:|---:|---:|
| def ROTATION | 0.980 | 0.848 | 0.909 | 0.785 | 0.013 |
| def LOW_VOL_HIDDEN | 1.000 | 0.797 | 0.880 | 0.686 | 0.000 |
| def SHOCK | 0.962 | 0.785 | 0.865 | 0.728 | 0.026 |
| def MARKET_TIDE | Null world | Null world | 0.000 | 0.136 | 0.026 |

Market Tide 中 raw within-correlation 中位約 `0.714`，扣除市場因子後 residual correlation 中位約 `0.001`，證明熱力圖必須使用 residual return，而不是 Adj Close 水位或 raw return。

上述數字是受控世界的邏輯驗證，不代表真實交易勝率。

## def 05｜Dynamic Criteria

市場判定邏輯不含固定：

```text
def corr >= 0.85
def Hotness >= P85
def Synchrony >= 0.60
def Leadership >= 0.80
```

Executable AST audit 結果：

```text
def prohibited fixed market threshold findings = 0
```

每天由輸入分布重新估計：

```text
def component count
def component centers
def posterior state
def data-derived cutpoints
def classification confidence
```

## def 06｜個股角色

每檔股票輸出：

```text
def HotnessRaw
def Synchrony
def BestLag
def BestLagCorr
def ZeroLagCorr
def PermutationEvidence
def LeadershipEvidence
def DynamicRole
def CoreEligible
```

DynamicRole 可能為：

```text
def LEADER
def PEER
def TRUE_LAGGARD
def MEMBER
def MIXED_ROLE
def OUTLIER
```

若資料不可分，允許 `MIXED_ROLE`，不硬貼 Leader / Peer / Laggard。

## def 07｜熱力圖

正式熱力圖使用：

```text
def Adj Close
→ def Log Return
→ def Market Residual
→ def Within-group Correlation
```

共生成 39 張 canonical residual heatmap，均由 HTML 可開啟。

## def 08｜保留警告

四項 Review Warning 必須保留：

1. List B 與 List A 的群數／版本不同。
2. List C 有 9 檔需 ticker registry 仲裁。
3. List C 有 4 筆 `.TW / .TWO` 衝突。
4. CPO 與 PCB 只有名稱近似，成員不足以合併。

這些不是可用程式碼自動消除的錯誤；在正式 registry 證據出現前，系統應繼續 fail-closed。

## def 09｜後續真值接線

下一階段只需要替換 controlled DGP：

```text
def price panel
= Date × YFTicker Adj Close

def turnover panel
= Date × YFTicker Turnover Value

def market factor
= ^TWII return

def technology overnight factor
= SOX / NVIDIA / AMD previous-session return
```

分類、指數、熱力圖、Back-test、User-test 與 Activation Gate 不必重寫。

## def 沙盒執行邊界

```text
def Python Engine / Pytest / Controlled Back-test / HTML / Manifest
= 已在本沙盒實際執行並通過

def PowerShell 7 Launcher
= 已完成靜態結構與必要命令檢查
= 本沙盒未安裝 pwsh，因此未宣稱 PowerShell Runtime / AST 實跑通過
```
