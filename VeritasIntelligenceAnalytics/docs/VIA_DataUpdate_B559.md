# VIA 母系統與資料庫更新 · 批559(2026-09-17 實測)

操作員令「更新母系統與資料庫」。先講**哪一半我在這裡做得完、哪一半做不完**,再給一貼即用。

---

## 一、先把界線講清楚

| | 誰能做 | 為什麼 |
|---|---|---|
| **母系統的登錄冊**(由**程式碼**推導) | ✅ 本境做完了 | AST 掃活樹,不碰任何庫。批558 已跑 `registry-sync --apply`:活元件 **5,179** · 新 5 · 退役 0 |
| **母系統的頁與 DB 衍生登錄冊** | ❌ 本境**不可以**做 | 容器的沙盒庫是空的,再生出來會用假資料覆蓋正本(LL49)。批554 實測過:`VIA_Schema_Registry` 會掉表、`VIA_IndustryUnifiedMap` 的 TWSE 25→24 |
| **資料庫回補** | ❌ **要你的手** | 全部需要觸網。`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 我一律不代設(短令冊 `Set-VIAGateDefaults` 只在未設時補 `OFF`,從不開啟) |

所以下面第二節是**我量出來的現況**,第三節是**你貼一次就跑完**的更新。

---

## 二、資料庫現況(`via-census` + `via-vdfdb coverage` 實測)

### 台股總庫 `vdf_tw_market.duckdb`(179 MB · 22 表 · 2,376,856 列)

| 表 | 列 | 檔數 | 期間 | 判 |
|---|---|---|---|---|
| `features_daily` / `prices_canonical` / `tw_daily_prices` / `tw_prices_adj` | 各 577,733 | 892 | 2024-01-02 ~ **2026-09-16** | 滯後 1 天,正常 |
| `tw_trading_daily` | 57,649 | — | ~ 2026-09-16 | 正常 |
| `tw_valuation_daily` | 4,429 | — | 2026-09-08 ~ 09-16 | 正常 |
| `tw_daytrade_market` | 12 | — | 2026-09-01 ~ 09-16 | 正常 |
| `tw_rates_cbc` | 308 | — | ~ 2026-08-01 | 月頻,正常 |
| `tw_market_agg` | 6 | — | 2026-09-01 ~ **2026-09-08** | **滯後 9 天** |
| `consensus_daily` / `consensus_latest` | **0** | — | — | **空**(= 掉球 Z43 FactSet 共識) |

**冊上宣告、庫裡沒有的 15 張**:
`tw_chip_inst` · `tw_chip_margin` · `tw_chip_derived` · `group_features_daily` · `tw_universe` ·
`analyst_estimates` …

> **籌碼整組缺**(三大法人/融資券/衍生),這是目前最大的一塊。

### 其餘庫

| 庫 | 現況 |
|---|---|
| `vdf_global_market.duckdb` | 9 表 · 192,653 列 · 最新 **2026-09-17**(滯後 0)· 缺 `us_macro` · `macro_series_registry` |
| `ActiveTWETF.duckdb` | 6 表 · 2,522 列 · GREEN |
| `VDF_TW_MonthlyRevenue.duckdb` | 13 表 · 3,012 列 · 最新 **2025-12-01** ← 舊 |
| `revenue.duckdb`(TWREV) | 84,864 列 · 最新 **2026-05-01** |
| `vrn_reports.duckdb` | 5 表 · **8 列** ← 本境如此;你那邊有 64 份,不要拿這個數字當結論(LL49) |
| `VIA_DATA_HOME`(家) | **缺**:`C:\Users\tonyk\Github\movies-dataset\data` 不在 → 家內庫 0 本 |

---

## 三、一貼即用(在你的機器上跑)

**同意閘那兩行是你的手**——我不代設,你要跑觸網段就自己貼上去;不貼就只跑離線段,
兩種跑法都不會壞,只是離線段補不了資料。

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName

# ── 0) 先看現況(唯讀,永遠先跑這個)
via-census
via-vdfdb coverage

# ── 1) 觸網同意(**這兩行是你的手,我不代設**;不要的話整段跳過)
$env:VIA_NET_CONSENT   = "YES"
$env:VIA_SCRAPE_CONSENT = "I_ACCEPT_RESPONSIBLE_SCRAPING"

# ── 2) 資料庫回補(次序有意義:先價量,籌碼才對得上交易日)
via-price                 # ENG054 台股日價增量
via-chip                  # ENG056 籌碼增量 ← 目前整組缺,這一步最重要
via-align update --apply  # ENG081 日交易×籌碼數量對齊 + 股票清單更新
via-market-lists          # ENG087 市場清單治理(tw_universe)
via-revfill               # ENG075 月營收史深(目前滯後到 2025-12)
via-fred                  # ENG074 FRED 宏觀(us_macro 缺;**需要 FRED 金鑰**)
via-etfuniv ; via-etfhist # 主動 ETF 宇宙 + 持股史深

# ── 3) 母系統再生(**要在你的機器跑**,因為它讀真庫)
via-vcgc registry-sync --apply
via-vcgc page --publish
via-manager                # 總控頁 81 項任務再生
via-famui all              # VDF/VRN/VAP 三家 U/I 再生

# ── 4) 收尾驗收
via-ryg vdf,vrn
via-census
```

---

## 四、跑完之後我需要你回貼的三樣

1. `via-census` 的 `[庫況]` 那幾行 —— 我才知道籌碼補進來沒有
2. `via-vdfdb coverage` 的表 —— 看 `consensus_daily` 是不是還是 0
3. `via-ryg vdf,vrn` 的最後一行

> 這三樣一貼回來,我就直接當量測用(不再問第二次)。

## 五、要你的手、我做不了的(掉球清單,只增不減)

`FRED` 金鑰 · `Z43` FactSet 共識(0 列的根因)· 國際期貨 `BZ=F/CL=F/GC=F` ·
族群分類快照 · `pip install seaborn` · `Z49`/`Z56` 目標價原始 PDF ·
`VIA_DATA_HOME` 那個 `data` 夾不在(要嘛建它,要嘛設 env 指到別處)

另外一條和資料無關但更急:**你機器上有三支比倉庫新的檔**——
`ENG072 v0135` · `ENG086 v0109` · `EngineBus v0128`,`main` 與本分支都沒有。
**請推上來**,否則下一批就是兩個頭。
