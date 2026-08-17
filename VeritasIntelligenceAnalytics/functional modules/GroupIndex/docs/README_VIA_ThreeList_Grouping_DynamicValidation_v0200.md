# def VIA 三清單 × 台股族群 × 動態 Criteria 驗證管線 v0.2.00

## def 系統目的

本套件將三份來源整理成彼此隔離的資料契約，並完成：

```text
def TEST
→ def DEBUG
→ def OPTIMIZE
→ def TEST
→ def CONSOLIDATE
→ def TEST
→ def BACK-TEST
→ def DEBUG
→ def USER-TEST
→ def ACTIVATE
→ def FINAL-TEST
```

## def 三份來源角色

```text
def List A
= 238 筆股票列級 membership
= 39 個族群
= 238 個唯一股票
= canonical candidate
= CountingFlag COUNT

def List B
= VIA ONE 範圍與治理控制契約
= 不產生 membership
= CONTROL_ONLY

def List C
= Thermal Solution / CPO / PCB 三個動態測試 cohort
= 27 筆
= DISPLAY_ONLY
= 永不覆蓋 List A
```

## def 動態 Criteria

正式判斷不使用固定 `0.85`、`P85`、固定相關係數或固定分數紅線。

系統以：

```text
def Gaussian Mixture Model
+ def BIC 元件數選擇
+ def Robust Scaling
+ def Cross-group Null
+ def Leave-One-Out Synchrony
+ def Circular-shift Max-lag Permutation
```

自動產生：

```text
def Hotness State
= LOW / MID / HIGH / MIXED

def Synchrony State
= LOW / MID / HIGH / MIXED

def Leadership State
= LOW / MID / HIGH / MIXED

def Group Validity
= VALID_GROUP / MONITOR_GROUP / NEEDS_SPLIT_OR_REVIEW / GROUP_NOT_SEPARABLE
```

## def 主要輸出

```text
def group_index_full_daily.csv
= 39 群 Full Equal-Weight Index

def group_index_core_daily.csv
= 依動態角色與族群有效性清洗後 Core Equal-Weight Index

def member_role_metrics.csv
= 每檔熱門度、同步性、最佳 lag、PermutationEvidence、DynamicRole

def group_validity_summary.csv
= 每群 residual correlation、PC1、跨群 Null lift 與有效性

def trading_capacity_latest.csv
= 成交值、成交穩定度、價格衝擊導出的動態交易容量分類

def dynamic_criteria_ledger.csv
= 每次執行的 GMM 中心、資料導出切點與方法
```

## def 最終狀態

```text
def Final Gate
= CONTROLLED_ACTIVATION_PASS_REVIEW_WARNINGS_RETAINED

def Hard Failure
= 0

def Review Warning
= 4

def Pytest
= 7 passed

def Canonical Mutation
= 0

def Network Execution
= 0

def Order Execution
= 0
```

四項 Review Warning 是來源衝突，不是程式錯誤：

```text
def List B 宣告 31 群，List A 實際 39 群
def List C 有 9 檔未匹配 canonical registry
def List C 有 4 筆 Yahoo suffix 衝突
def CPO / PCB 名稱相似但成員定義不一致
```

## def 執行

### def Python

```powershell
python .\VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py
```

### def PowerShell 7

```powershell
pwsh -NoExit -ExecutionPolicy Bypass -File `
  ".\Invoke-VIA-ThreeList-Grouping-DynamicValidation-v0200.ps1" `
  -OpenHtml 1 `
  -KeepOpen 1
```

## def 真實資料邊界

目前 Back-test 使用 deterministic controlled DGP，目的為驗證：

```text
def Dynamic Criteria 是否會隨 regime 改變
def Market Tide 是否被 residualization 排除
def Structured rotation / low-vol / shock 是否高於 Null
def 三份清單能否完整進入指數與熱力圖管線
```

它不是實盤投資績效。要升級成真實回測，需接：

```text
def Date
def YFTicker
def Adj_Close
def Turnover_Value
```

並依 point-in-time 可得日重跑相同 Gate。

## def 沙盒執行邊界

```text
def Python Engine / Pytest / Controlled Back-test / HTML / Manifest
= 已在本沙盒實際執行並通過

def PowerShell 7 Launcher
= 已完成靜態結構與必要命令檢查
= 本沙盒未安裝 pwsh，因此未宣稱 PowerShell Runtime / AST 實跑通過
```
