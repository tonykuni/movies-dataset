# def VIA_TW_GroupingIndexRotationUnifiedEngine v0.2.01 — Detailed Hand-over

## def 01｜Canonical Owner

```text
def Engine      = VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py
def Contract    = VIA_TW_GROUPING_ROTATION_CONTRACT_V0201
def Membership  = VIA_ThreeList_CanonicalMembershipInput_v0100.csv
def UI          = Engine-generated index.html + ui_contract.json
def Policy      = local-only / append-only evidence / no order execution
```

## def 02｜整合基礎

原始價量引擎提供 Adjusted Close fail-closed、Volume 不補值、動態門檻、FDR、Leader/Peer/Lagger 與 purged walk-forward 等基礎；原測試也保護 ticker suffix、低共動不可誤標 Laggard 與 Base-100 指數。原 Flow Monitor 則定義了 groupIndex、groupFlow、classification、validation 等前端資料需求。

v0.2.01 修正原架構中的三項主要衝突：

```text
def Group validity 不再依賴角色一定可分
def Laggard 不再被所有正式指數排除
def Python output 與 HTML input 改用同一 JSON Contract
```

## def 03｜最終 Demo 證據

```text
def Membership rows             = 238
def Groups                      = 39
def Unique stocks               = 238
def Price rows                  = 38,080
def Group-validity snapshots    = 156
def Role snapshots              = 952
def Group-index rows            = 11,918
def Rotation rows               = 6,240
def Heatmaps                    = 39
def Pytest                      = 20 passed
def Validation                  = 15 PASS / 1 HOLD / 0 FAIL
def Runtime                     ≈ 33 seconds in current sandbox
def Peak RSS                    ≈ 360 MB
def Order execution             = 0
```

Demo Gate 為 HOLD，原因僅是受控合成資料邊界；不可將受控結果描述為實盤勝率。

## def 04｜本輪 Debug / Optimize 記錄

```text
def D01 向量化 point-in-time 多指數，移除逐日逐股慢迴圈
def D02 修正 Date + Group 指標錯位
def D03 修正 UTF-8 BOM 欄位問題
def D04 修正 role effective date 只在截斷日曆中搜尋
def D05 修正 latest snapshot 落在最後交易日、沒有下一有效日
def D06 修正角色與族群有效性綁死
def D07 修正 Laggard 被全部排除
def D08 增加 Cross-group adversarial null maximum
def D09 增加 expanding-median temporal devil validation
def D10 消除 MARKET_TIDE controlled world 假 promotion
def D11 增加五類 point-in-time chain-linked index
def D12 統一 Python ↔ HTML JSON contract
```

## def 05｜Controlled Back-test

| Scenario | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ROTATION | 3 | 0 | 3 | 1.00 | 0.50 | 0.667 |
| MARKET_TIDE | 0 | 0 | 0 | — | — | — |
| LOW_VOL_HIDDEN | 3 | 0 | 3 | 1.00 | 0.50 | 0.667 |
| SHOCK | 3 | 0 | 3 | 1.00 | 0.50 | 0.667 |

這是受控 DGP 的方法測試。它證明目前規則可以拒絕純市場潮水，並在三種真群組世界保留部分真陽性；不代表 live accuracy。

## def 06｜Production Handoff Gate

正式市場評估前必須完成：

```text
def 讀取 StockData.parquet 的真實 Adj OHLC / Volume / Turnover
def 接入 TAIEX、SOX 前一交易日與必要外部因子
def 接入三大法人、融資、融券與當沖 point-in-time usable_from
def 接入 Membership ValidFrom / ValidTo 歷史版本
def 2020-01 起 walk-forward 重播
def 交易容量、滑價與成分變更 Divisor 驗證
def Devil / Placebo / Market Tide / Regime split 全數重跑
```

## def 07｜禁止事項

```text
def 不可把 Demo precision 當成實盤精準率
def 不可用 Raw Close 代替 Adj Close
def 不可 forward-fill Volume 或 flow
def 不可用最新角色回填歷史
def 不可讓 DISPLAY_ONLY membership 重複計數
def 不可讓 HTML 自行重算分類邏輯
def 不可直接下單
```
