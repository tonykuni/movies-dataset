# 全部台股清單 · 主動式台股 ETF 驗證清單:取得方法與統一讀取口(2026-09-28)

操作員令:「find out method to fetch all taiwan stock list & all active taiwan stock etf validated list as input to many engines.」

**結論:** 已經有正主寫入者和正主資料表,**不需要**再寫一支抓取器。真正缺的是**統一的讀取口**:各引擎目前自己讀、自己寫 regex(樹上有四種寫法)。這次補上 `VDF_ENG087_MarketListGovernance_v0105`,它是兩張清單唯一的讀取口,只讀、不上網。更新時依下面 §4 的順序,經 VCGC 跑既有的寫入者。

---

## 1 官方來源(誰抓、抓哪裡)

| 清單 | 官方端點 | 正主寫入者 | 落地 |
|---|---|---|---|
| 全部台股(上市) | `https://openapi.twse.com.tw/v1/opendata/t187ap03_L` | VDF_ENG055 OmniFetch 車道 **L1** `lane_listings` | `vdf_tw_market.duckdb::tw_listings_industry`(CGC_MDL142 認定正主) |
| 全部台股(上櫃) | `https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O` | 同上 | 同上 |
| 主動式台股 ETF 總清單 | `https://openapi.twse.com.tw/v1/opendata/t187ap47_L`(基金類型判定國內或國外成分),後備 etf_book | VDF_ENG077 ActiveETFUniverse `run` | `ActiveTWETF.duckdb::active_tw_etf_registry`(`status` 欄:ACTIVE_DOMESTIC / FOREIGN_COMPONENT / UNKNOWN_TYPE / MISSING_FROM_SOURCE) |
| 主動 ETF 驗證(持股) | 各投信每日持股揭露 | VDF_ENG078 ActiveETFHoldingsHistory `daily` | `ActiveTWETF.duckdb::holdings_daily` |
| 股票日快照(衍生,選用) | 不上網 | VDF_ENG081 UniverseAlign `update --apply` | `tw_universe`(價表∪籌碼 ∩ 清單) |

網路都走 SUP_MDL740 與 CGC_MDL224 ScrapeGate。同意閘由操作員自己開,見 `via-gates`,引擎不代設。

## 2 一套規則(v0105 起全樹以這份為準)

| 項目 | 規則 | 為什麼 |
|---|---|---|
| 普通股代號 | `^[1-9]\d{3}$` | 四碼,首碼 1–9。`00xx` 四碼是 ETF;五、六碼是權證、特別股、ETN |
| 交易所 | 只收 TWSE / TPEX(上市、TSE、加權 → TWSE;上櫃、OTC、TWO、櫃買 → TPEX) | 認不得的照數剔除並列出,不猜 |
| 去重 | 同代號只留一列;同碼掛兩所 → AMBER 並點名 | |
| 後綴 | `.TW` / `.TWO` / ` TT` 先剝,讀出時再依所別補 `yf_ticker` | 價表鍵是 `1101.TW`(批307) |
| 兩所下限 | 任一所 0 家 = RED;低於軟下限(加權 900、櫃買 700)= AMBER | 抓回一半不能算綠(Z227 教訓) |
| 主動式台股 ETF | 代號 `^00\d{3}A$`,且 registry `status = ACTIVE_DOMESTIC`(沒有 status 欄時看 `domestic`,再沒有才看 `daily_required`) | `D` 結尾是主動債券,`B` 是債券;國外成分與下架的不列入 |
| 「驗證過」 | 這檔在 `holdings_daily` 有持股列(`00981A` 與 `00981A.TW` 視為同一檔,取最晚持股日) | registry 是總清單,持股是驗證 |
| 交叉核對 | 股票庫 `tw_listings` 裡掛牌的主動 A 碼不在總清單 → AMBER「總清單可能漏抓」 | |

**舊寫法(v0105 之後不要再照抄):**
- ENG054 / ENG055 用 `isdigit() and len == 4`。t187ap03 本身只有公司,所以抓取時無害;但拿同一條規則去篩含 ETF 列的表(例如 `tw_listings`),`0050` 會被當成股票。
- ENG087 v0104 用 `^00\d{2,3}A$`。
- ENG077 用 `^\d{5}A$`。
- ENG054 還有 `_ACTIVE_TW = ^00\d{2,3}A$`。

## 3 讀取口(給所有引擎)

```python
import importlib.util
from pathlib import Path
eng_dir = VIA / "functional modules" / "VDF" / "engine"
tail = sorted(eng_dir.glob("VDF_ENG087_MarketListGovernance_v*.py"))[-1]      # 尾版律 L54,不釘版號
spec = importlib.util.spec_from_file_location("tw_lists", tail)
L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)

stocks = L.load_stock_list()          # {"state","why","rows":[{code,name,market,yf_ticker,industry}],"counts":{TWSE,TPEX},"dropped",...}
etfs   = L.load_active_etfs()         # {"state","why","rows":[{ticker,name,issuer,fund_type,verified,last_holdings_date}],...}
codes  = L.stock_codes()              # ["1101", "1102", ...];狀態不是 GREEN/AMBER 時回 []
a_all  = L.active_etf_codes()                       # 總清單
a_ok   = L.active_etf_codes(verified_only=True)     # 只要有持股驗證過的
```

- 庫的路徑依序讀 `VIA_DB_VDF_TW_MARKET` → `VIA_DB_TW` → 預設。v0103 和 v0104 各讀一個名字,v0105 兩個都認。ETF 庫讀 `VIA_DB_ACTIVETWETF`。
- 一律 `read_only=True`。不上網,不寫庫。
- 命令列:
  - `python VDF_ENG087_…_v0105.py lists [--json]`:寫 `VIA_Reports/vdf/central_lists/TW_LISTS_latest.json`(逐檔列;再生件,不 commit)。
  - `refresh --plan`:印出更新順序。
  - `status` 與 `run` 保留 v0104 的行為。
- 面板:`via-vcgc dbm panel`,或 `.\Invoke-VIA-DBPanel-v0100.ps1`。第 [4] 區顯示兩張清單的狀態、檢查、剔除數、交叉核對與更新順序。

## 4 更新順序(經 VCGC;本讀取口與面板只列指令、不代跑)

1. `via-console run --item macro_lanes lanes=L1`:抓兩所上市櫃清單,寫 `tw_listings_industry`。要網路。
2. `via-console run --item etf_universe`:主動 ETF 總清單,寫 `active_tw_etf_registry`。要網路。
3. `via-console run --item etf_holdings_daily`:抓每檔持股,等於做驗證。要網路。
4. `via-console run --item tw_universe_update`:股票日快照,選用。寫庫件,等日更鏈沒在跑時再跑。
5. `via-vcgc dbm panel`,或 `.\Invoke-VIA-DBPanel-v0100.ps1`:驗收兩張清單。唯讀。

每天自動跑是工作站排程的事(L70,Z227)。容器不代排。

## 5 目前讀這兩張清單的引擎(遷移清單:改成呼叫讀取口,每支開新版號 L04)

| 系統 | 引擎 | 目前怎麼讀 | 建議 |
|---|---|---|---|
| VDF | ENG070 / 072 / 079 / 081 / 082 / 090 | 直接讀 `tw_listings` | 改讀 `load_stock_list()`(正主表是 `tw_listings_industry`) |
| VDF | ENG063 | 走 VRN_ENG069 `fetch_universe` | 改讀 `stock_codes()` |
| VDF | ENG059 | 自己的來源 | 改讀 `stock_codes()` |
| VDF | ENG078 `universe()` · ENG094 · ENG051 | 讀 registry | 改讀 `active_etf_codes()` |
| VDF | ENG055 | 另有一支自己抓的 ETF 路徑 | 只留寫入者角色,不另當清單 |
| VRN | ENG069 `fetch_universe` | 自抓 | 改讀 `stock_codes()` |
| VRN | ENG067 / 073 / 080 / 086 / 090 | 讀 `tw_listings` | 改讀 `load_stock_list()` |
| VAP | ENG009 | 寫死 2330 / 2317 / 2454 | 改讀 `stock_codes()`(或保留當示範,註明不是清單) |
| VAP | ENG013 | 讀 `tw_listings_industry`,以及 etf_book `is_active`(定義不同) | ETF 改讀 `active_etf_codes()` |
| CGC | MDL095 / 118 / 139 / 142 / 131 | 各自讀表 | 顯示端改讀讀取口的 summary |

## 6 查到的斷線(已記掉球)

- `supportive modules/registry/via_boot_update.ps1` L81 仍跑 `VDF_ENG054 … run`。ENG054 v0110 起只是狀態卡,不會抓清單,也不會抓價。L87 則直接釘 `VDF_ENG051_ActiveTWETF_Holdings.py`。
- ENG087 v0104 的 `run` 只委派兩張狀態卡(ENG054 `--status`、ENG077 `status`),不會更新清單。v0105 在 `run` 印出這個事實,並指向 `refresh --plan`。
- 抓主動 ETF 的有三條路:
  - ENG077,正主。
  - ENG051 `activeList`,只收國內,且內建 bootstrap。
  - `GroupIndex/engine/VIA_ActiveStockETF.py`,繞過 SUP_MDL740 與同意閘。
- VDF_ENG078 v0112 是薄尾,但沒有轉接前版的公開名稱(全景判 TAILAPI):`coverage`、`daily`、`backfill` 等,以模組方式呼叫會 AttributeError。命令列 `main` 照常,所以 §4 第 3 步不受影響。
- ENG087 v0103 讀 `VIA_DB_VDF_TW_MARKET`,v0104 讀 `VIA_DB_TW`。v0105 已修,兩個都認。
