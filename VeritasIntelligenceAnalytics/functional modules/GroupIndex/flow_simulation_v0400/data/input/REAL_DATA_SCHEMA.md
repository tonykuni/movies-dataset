# Real Data CSV Schema

輸入檔皆使用 UTF-8 CSV。日期可讀入常見格式，輸出一律正規化。`Ticker` 建議使用 `2330.TW`／`6488.TWO`。

| File | Required Columns | Key |
|---|---|---|
| `membership.csv` | `GroupId`, `GroupName`, `Ticker`, `IndexEligible` | `GroupId + Ticker` |
| `price.csv` | `Date`, `Ticker`, `Adj_Close` | `Date + Ticker` |
| `institutional.csv` | `Date`, `Ticker`, `ForeignNetAmount`, `InvestmentTrustNetAmount`, `DealerNetAmount` | `Date + Ticker` |
| `margin_short.csv` | `Date`, `Ticker`, `MarginBalanceValue`, `ShortBalanceValue` | `Date + Ticker` |
| `active_etf_pcf.csv` | `Date`, `Ticker`, `ETFId`, `ActiveETFFlowAmount` | `Date + Ticker + ETFId` |
| `main_force.csv` | `Date`, `Ticker`, `MainForceNetAmount`, `BranchConcentration` | `Date + Ticker` |

建議欄位：

- membership：`Name`, `Market`, `MarketVerified`, `MarketSource`, `CandidateRole`, `FlowEligible`, `DisplayOnly`, `PrimaryEconomicIdentity`, `UITier`, `SourceVersion`。
- price：`Volume`, `TurnoverValue`, `DayTradeTurnover`, `MarketCap`。
- margin_short：若已計算，可提供 `MarginNetFlow`, `ShortNetFlow`；否則由餘額差分產生。

缺值規則：Adj Close 最多 forward-fill 3 日；Volume、Turnover、法人、融資融券、ETF flow 與主力分點全部保留缺值，不可 forward-fill。沒有 `main_force.csv` 時必須輸出未決，不得以自營商推估主力。

分類 U/I 角色由 20D／60D 同步性與領先性證據計算，輸出 `A_LEADER`、`B_PEER`、`C_LAGGARD_EXCEPTION` 與 `UNRESOLVED`。C 類以 `dormant` 保留，`IncludeInGroupIndex=false` 只套用到下次再平衡，不回寫當期指數。人工 × 只會新增 `EXCLUDE_PROPOSED` 或 `KEEP` 決策事件；不會刪除 canonical membership。
