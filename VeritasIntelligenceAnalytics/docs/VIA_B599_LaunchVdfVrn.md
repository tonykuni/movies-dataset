# 批599 — 啟動 VRN + VDF,2023-07-01 ~ 今

操作員令:「啟動指令透過 VRN VDF 2023-07-01~今」。

---

## 一、起始日設在**參數庫**,不是設在指令上

「2023-07-01」的正本是 `VIA_InputConsole_Spec_v0100.json` 的 `user.group_starts`
(批392 立的「整類遮罩」)。所以照冊設,不是在 CLI 上塞一個旗標:

```
via-console set group-start=tw_equity:2023-07-01   (macro / financials / etf / intl 同)
```

逐鍵複驗過冊裡真的寫進去了(不是只看 `OK:` 那一行):

```json
user.group_starts = {"intl":"2023-07-01","tw_equity":"2023-07-01",
                     "macro":"2023-07-01","financials":"2023-07-01","etf":"2023-07-01"}
defaults.start   = "2023-01-01"   ← 不動(群組值優先,只增不減)
```

> **VRN 的 `pipeline` 群組沒有任何日期參數。** 那 15 項吃的是
> `dir` / `codes` / `limit` / `in` / `out`。所以「2023-07-01~今」對 VRN 是 **no-op**
> ——講成「VRN 也跑了這個區間」就是假的。

`CGC_MDL149 v0116` 另加一件:把 `group_starts` 的**現值印在頁的範圍列上**。
頁上看不到現值的話,「跑了 2023-07-01 起」這句話**沒有出處**。

## 二、真跑(`--apply`),48 項

```
via-vcgc matrix --family vdf,vrn --apply
→ 48 項 = vdf 33 + vrn 15
   GREEN 23 · GATED 15 · RED 3 · NODATA 3 · PLAN 2 · ABSENT 2
```

### GATED 15 —— 這就是「2023-07-01~今」真正的答案

起始日設好了,但**真的要抓資料的 15 支全部卡在同意閘**,引擎自己 fail-closed 拒跑:

```
tw_prices_inc · tw_history · tw_chips · tw_trading_value · tw_daytrade_stock ·
tw_daytrade_files · macro_fred · macro_detail · macro_lanes · fin_statements ·
tw_revenue_codes · tw_revenue_backfill · estimate_bands · global_universe · global_lanes
```

每一支印的都是「**同意閘未開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)**」。
**閘是你的手,我不代設。** 要真的補 2023-07-01 起的資料,在工作站:

```powershell
$env:VIA_NET_CONSENT    = "YES"
$env:VIA_SCRAPE_CONSENT = "YES"
via-vcgc matrix --family vdf --apply        # 起始日已經在冊上,不必再帶
```

### RED 3 —— 拆開看,只有一支是真的資料紅

| 項 | 引擎自己說的 | 判讀 |
|---|---|---|
| `vdf/tw_align` | 逐日 `價 892 · 籌碼 **0** · MISALIGNED` | **真紅**:本容器籌碼表一列都沒有,價籌當然對不齊 |
| `vdf/vdf_quantguard_run` | `[NEED_INPUT] run requires --in <Parquet>` | **缺參數**,不是壞掉 |
| `vrn/vrn_unified` | `[ERROR] at least one --in file/directory is required` | **缺參數**,不是壞掉 |

後兩支冊上的參數欄寫著 `in,out`,但**沒有人給值**。
要我填什麼進去是**操作員裁定**(LL90),本批**只點名不代填**。

順帶一個尺的觀察:`CGC_MDL158 judge()` 把「缺必要參數」判成 **RED**。
誠實一點該是第五態 `NEED_INPUT`——但那要改 MDL158 的判定,
不在本批範圍,列為 **PENDING_OPERATOR**。

### NODATA 3 · PLAN 2

- `tw_chips_derive`(上游 `tw_chip_margin` 沒表)· `db_localdb_scan`(來源根是工作站路徑)· `vrn_markdown`(無可轉檔)——**缺料不是壞掉**
- `tw_universe_update` / `db_localdb_apply` = **寫庫動詞**,家族全掃**永不代跑**,要跑得 `--ids` 明點(同「`--approve-remove` 只在明令下」律)

## 三、引擎檢查邏輯 GREEN 16 / RED 1(又是自己)

③ 那一格第一次跑又報 `CGC_MDL149` 紅——因為我剛新增 v0116,元件自動編號冊還沒同步。
`registry-sync --apply`(新 1 · 變更 78 · **退役 0**)之後 **22/22**。

**這是第二次了**(批598 是 v0115)。同一把尺,連續兩批都第一跑就抓到我自己的註冊缺口
——那正是它該做的事。

## 四、一個必須講的更正

批597 我說「`tw_chip_inst` / `tw_chip_margin` **連表都不存在**」。
那句話對**本容器的 DuckDB** 是對的;但參數冊的庫表頁(`VIA_VDFArchitecture_v0100.json`,
2026-09-15 工作站快照)顯示 `tw_chip_inst` **1,165,675 列**、`tw_chip_margin` 1,145,409 列。

兩個都是真的,講的是**不同的東西**:

- **容器的庫**:沒有籌碼表(所以 `tw_align` 判 MISALIGNED、批596 那個空表守衛才會被踩到)
- **工作站的庫**(冊上的快照):籌碼表有一百多萬列

**本機綠不等於倉裡綠,倉裡的數字也不等於本機的數字。**(LL155 的另一面)

---

## 五、設了參數之後,尺自己翻臉了(MDL139 v0109)

照冊設完 `user.group_starts` 五個群組,`CGC_MDL139` 自測**四檢連紅**:

| 檢 | 寫死了什麼 |
|---|---|
| ② 參數→argv 白名單 | 「統一起始 **2023-01-01** 自動帶入 start\|since」 |
| ⑥ status 結構 | 同上 |
| ⑨ 統一起始/整類起始 | 「預設 **2023-01-01**」 |
| ④ set 個別改動 | 「changelog **兩筆**」(`len(u["changelog"]) == 2`) |

那些數字是**操作員還沒設過任何參數**時的樣子。也就是說:
**用了這本冊該有的功能(`via-console set group-start`),它自己的尺就翻臉。**

逐項二分證過因果,不是猜的:

```
清空 group_starts          → 4 紅剩 1
再移走 VIA_Reports/datahome → 仍剩 ④(changelog 已有 5 筆 ≠ 2)
```

**v0109 的修法**:斷言用的 spec 先把**操作員設定過的那一塊**
(`starts` / `group_starts` / `changelog`)回到空基線 ——
量的是「**給這些輸入會產生什麼 argv**」,不是「**這台機器現在設了什麼**」。
要看現況的檢另外從活冊讀。

實測:帶著 2023-07-01 的設定、帶著 datahome 目錄、在格子的 `PYTHONPATH` 下,**18/18 全綠**。

> **設過參數就把自測弄紅的尺,是壞的尺** —— 它量的不是行為,是「你有沒有動過它」。
