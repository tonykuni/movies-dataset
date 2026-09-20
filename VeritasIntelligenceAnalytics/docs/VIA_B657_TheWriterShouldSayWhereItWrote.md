# 批657 · 寫的人要說出自己寫到哪一本

## 定案:批655 是對的,批656 是我自我懷疑錯了

ENG073 v0132 加了一行。容器實跑:

```
[結構庫] vrn_report_basic 寫入 → …/functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb
```

而 ENG083 v0112 讀的是:

```
functional modules/VRN/output/vrn_reports.duckdb
```

**兩個不同的檔案。這是程式碼事實,不是對你機器的推論。**
(`run()` 就是 `_resolve_db()` → `connect` → `INSERT`;它自己的自測 ⑱⑲ 本來就在同一本庫裡
建 `tw_daily_prices`、再讀 `vrn_report_basic`。)

### 我為什麼在批656 推翻了一個正確的結論

因為你那一跑的 `candidates`(讀 `output/`)算出券商缺口 **15**,
和 ENG073 那一跑的「券商正典鍵 90/105」**剛好吻合**。

但 `output/` 那本**本來就是同一支引擎、同一批 105 份、在更早一次跑寫下的** ——
數字一樣是**必然**,不是巧合。

> **我拿一個本來就會相等的數字,去推翻一個讀過原始碼才得到的結構事實。** → **LL295**

而且批656 我還說「容器結構上看不見這個洞」。
**容器一直有這個分歧,只是從來沒有人把它印出來。沒印出來,不等於不存在。**

---

## 治法最便宜的那一半:讓寫的人自己講

一行 `[結構庫] … 寫入 →`,這一類來回三批的爭論就結束了。

## 另一半:我的候選名單抄了一半

批656 我讓 ENG083「照 ENG073 的次序解庫」,**只抄了它「資料家環境變數」那一半**,
沒抄它的**舊路徑鏈**。於是在沒有環境變數的容器裡,
ENG073 實際寫入的那一本 **根本不在候選名單裡** ——
看起來像修好了,其實一格都沒動。 → **LL296**

補上同一個常數位置之後,容器實跑:

```
[庫] …/VDF/output_hub/mega/vdf_tw_market.duckdb
     ← VDF mega 價庫(ENG073 舊路徑鏈的落點;結構表也寫在這裡)(候選中**最後被寫過**的一本)
[**第二顆頭**] 另有 1 本庫也有 vrn_report_basic ——
        81 列 · 最後寫於 2026-09-20 11:51 · VDF mega 價庫
        81 列 · 最後寫於 2026-09-19 21:44 · VRN 舊路徑 output/vrn_reports.duckdb
```

**舊的那一本差了整整一天。** 時間戳一擺出來,誰新誰舊不用討論。

零綠探針也跟著換了數字:

```
upside_state:MISSING_SOURCE×51 · SINGLE_SOURCE×21 · EXACT_MATCH×5 · ROUNDING_ONLY×2 · DB_DERIVED×2
upside_db:(NULL)×79 · 35.3×1 · 11.5×1
```

多出來的 `DB_DERIVED×2` 與兩個 `upside_db` 數字,**就是讀到新那一本才看得到的**。

---

## 你這邊(這次會真的變)

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
. .\VeritasIntelligenceAnalytics\Register-VIA-Commands-v0231.ps1
via-run25
```

你會看到兩行新的:

- ENG073 那一段多一行 **`[結構庫] vrn_report_basic 寫入 → …`**
- 矩陣那一段多一行 **`[庫] …`** 與(若有兩本)**`[**第二顆頭**]` 連時間戳**

而「上漲空間」那一欄 —— 你的 mega 庫裡有 `EXACT_MATCH_DB` / `ROUNDING_ONLY_DB`,
矩陣現在讀得到它們,**應該會第一次出現 GREEN**。

如果還是 0,零綠探針會把 `upside_state` 的分佈直接印在旁邊 ——
那一行會告訴我們是缺料還是尺的事,**不需要我再猜第四次**。
