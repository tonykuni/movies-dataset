# 引擎調度匯流排 CGC_MDL148(批471)

> 操作員令:「**功能性引擎功能性化 可讓多個子系統調度**」
> 「實測修正無誤後顯示 html u/多矩陣結果摘要及資料 **全部 SSOT**」

---

## ⓪ 先更正我自己上一輪公布過的判斷

我拿操作員那 64 份真檔名實測,回報「第一場 2026年投資大趨勢」等三份研討會的
`2026` 被當成代號,是引擎缺陷。**那個結論是錯的,而且錯的是我的量法。**

| | 我的量法(裸建 `TickerFilename()`) | 引擎正線(`roster=nr.code_roster()`) |
|---|---|---|
| 代號冊 | **0 檔** | **1,979 檔** |
| `2026` | 判成代號 ❌ | **正確拒絕** ✅ |
| `2002 / 2015 / 2023 / 2027 / 2030` | 收 | **全收** ✅ 鋼鐵股一支沒誤殺 |

更難堪的是**儀器有報,是我沒看**:`parse_filename()` 的回傳裡本來就有
`roster_state` 欄,裸建時它明明白白印著「冊不可得(未經庫對帳)」——我那張表
沒把這一欄印出來,就直接把它當引擎缺陷報出去。**判錯的紅燈和假綠一樣傷。**

64 份用正線重量的結果:

| 量到 | 數 |
|---|---|
| 分類正確 | **64 / 64**(個股 42 · 產業 10 · 大盤晨報 6 · 海外 3 · 研討會 3) |
| 代號正確 | **42 / 42**(含 `3014TT` 彭博尾綴 · `(6533,N,中立)` 括號內 · `(3706 TT)` 空格式) |
| 日期正確 | **61 / 64**(民國 `1141202`→2025-12-02 · 六碼 `251208` · 八碼皆通) |
| 無日期 3 份 | 檔名裡本來就沒有日期——**缺料,不是缺陷** |
| 誤判 | **0** |

---

## 一 · 先查再造:缺的不是引擎,是**統一的呼叫契約**

量到的(不是規劃的):

* 調度用的 SSOT **早就有** —— `VIA_InputConsole_Spec_v0100.json` 已宣告 **37 項引擎**
  (vdf 24 / vrn 7 / vap 6),每項都帶 `engine{dir,glob,verb}`、`params`、`outputs`。
  **本件不另立第二本冊**——另立=正典換了沒人跟得上。
* 但**調度的碼四家各寫各的**:

| 調度者 | 怎麼叫引擎 |
|---|---|
| `CGC_MDL095_DeckServer` | `Popen` × 12 |
| `CGC_MDL137_RunGate` | `subprocess.run` × 3 |
| `CGC_MDL139_InputConsole` | `subprocess.run` × 1 |
| `CGC_MDL141_ClosingGate` | 自己一套 |

  每一家都重寫:尾版 glob 解析、家族 python 選擇、逾時、結果解讀。
  同一件事四份實作=九頭龍;引擎換了介面,四個地方都要記得改,而
  **漏改的那一份不會報錯,只會靜靜走錯**。

這就是「功能性化」缺的那一格:引擎有功能,但**沒有一個統一的呼叫契約**。

### 契約

```
catalog(family=None)          冊上 37 項 × 尾版解析 × 在位實測
call(item_id, params, ...)    統一呼叫 → 統一結果字典
matrix(family, ids, apply,    批量調度 → 多矩陣資料
       apply_families)
render(data, out)             實測結果 → 多矩陣 HTML(零 CDN;樣板走 MDL089)

state ∈ GREEN | NODATA | AMBER | RED | TIMEOUT | ABSENT | PLAN
```

**缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)在狀態上分得死死的:

| 燈 | 意思 | 判準(要亮得出證據) |
|---|---|---|
| `NODATA` | **缺料**:上游沒料 | 引擎自己印了「誠實停」之類的話,**原文帶回** |
| `ABSENT` | **缺件**:引擎檔 / 相依套件 / **必要參數** 不在位 | 引擎自述缺席,或 argparse 自己的抱怨 |
| `PLAN` | 沒動手:dry,或**寫庫動詞**被家族閘擋下 | — |
| `RED` | **真的壞掉** | 以上都沒命中的 rc≠0,一律照舊紅 |

---

## 二 · v0100→v0105:同一批的**五次實跑、五次自我修正**

每一次都是**我的尺錯,不是引擎錯**。尾版 v0105 的版沿革載全程。

### v0101 — VRN 7 項實跑報 RED 3

那三支印的都是「無報告件(誠實)」。**缺料不是壞掉。**
想改用 `rc=2` 當判準,**量過之後否決**:全樹 `return 2` 有 **163 處**,
其中只有 **46 處**是誠實停,117 處是用法錯/缺庫等別的意思——**rc 不是穩定慣例**。
改認引擎**自己印的那句話**,並把命中原文帶回當證據。

### v0102 — VAP 6 項實跑報 RED 4,逐項查完**只有 1 支真壞**

| 項 | 引擎真的印了什麼 | 該判 | v0101 判成 |
|---|---|---|---|
| `vap_dashboard` | `[缺料] 缺 4 項 … [補料] 誠實停 rc2` | NODATA | RED ❌ |
| `vap_std_dashboard` | `plotly 缺席=誠實停` | ABSENT(缺件) | RED ❌ |
| `vap_one_render` | `argparse: argument --render: expected one argument` | ABSENT(缺參數) | RED ❌ |
| `vap_stack` | `CatalogException: Table tw_daily_prices does not exist` | **RED** | RED ✅ |

三條修法:

1. **「誠實停」才是這套系統的正典句**——全樹 **451 處**,而 v0101 那張字表是照 VRN
   幾支的措辭湊的,只認得 VRN 的方言。
2. **缺件 ≠ 缺料**。判缺參數**只認 argparse 自己講的話**——
   **不能用「冊上有宣告 params 就別跑」一刀切**:冊上 21 項宣告了 params,
   其中 **20 項沒給參數照樣跑得好好的**(量過),一刀切等於誤殺 20 項。
   (跟「排除 2000–2030 修年份」是同一種爛招。)
3. **`--apply` 不該是全有全無**。VDF 24 項按下去=同時發動 `tw_history` 全史回補、
   `tw_chips` 籌碼回補,還有兩支動詞本來就帶 `--apply` 的寫庫件
   (`tw_universe_update` / `db_localdb_apply`)。新增:

   * `--apply-family vrn,vap` 只在點名的家族真跑
   * `--ids a,b,c` 只跑點名的項
   * **寫庫動詞閘**:動詞含 `--apply` 的項,家族全掃**永不代跑**,
     要跑必須 `--ids` 明點(同「`--approve-remove` 只在明令下」律)

### v0103 — 實跑後 `git status` 冒出從沒入過庫的夾

```
functional modules/VAP/engine/vap_one_out/RUN_.../vap_one.html
```

**調度層讓引擎在原始碼樹裡生檔。** 根因是我在 v0100 寫的 `cwd=引擎檔所在目錄`;
ENG016 的 `--out` 預設是相對路徑。
**正本零觸碰不是只管「不要改別人的檔」,也管「不要在別人家裡生檔」。**

改 cwd 之前先量(不是先猜):

* 冊上在位 **36 支**,**36 支全部用 `__file__` 定位自己**
* `os.getcwd` / `Path.cwd()` / `chdir` —— **0 支**
* ENG016 從無關目錄實跑:rc=0,行為不變

→ 改到 `VIA_Reports/engine_bus/_cwd/` 底下跑。

### v0104 — 讀自己產的頁,發現說謊的是**頁**

* 頁首在 `--apply-family` 下照印「模式 **只解析(dry)**」——那一跑 vrn+vap 是真跑的。
  **一張報實測結果的頁,第一行把自己的模式講錯。**
* 矩陣四拿 `(VIA/宣告).exists()` 判產出。量了冊:**60 條宣告裡 34 條是資料庫表名**,
  不是檔案路徑 → 那 34 條永遠寫「缺」。**矩陣四超過一半的格子在說謊**:
  `vrn_structdb` 剛入庫 71 筆,頁上照樣說它的 `vrn_report_basic`「缺」。

### v0105 — 同一張表再讀一遍,又抓到第三種形狀

`VIA_UI_VRNControlTower_v0100.html` 還是寫「缺」,而 `vrn_ui` 那一跑報「頁 3/3 新鮮」。
冊上有 **7 條是沒有目錄的裸檔名**,真的頁住在 `supportive modules/ui_support/`,
我卻拿 VIA 根去接。**我一直在用「一種判法」去問三種不同的問題。**

判法改成照宣告的**形狀**分四路:

| 形狀 | 怎麼判 |
|---|---|
| 含萬用字元 | **不判**(判不了就說判不了) |
| 路徑形(有 `/`) | 接 VIA 根問檔案系統 |
| 裸檔名形 | **去全樹找**(排除 references),找到就講落在哪 |
| 表名形 | **問庫**(唯讀 `SHOW TABLES`;支援 `庫.duckdb::表`) |

一張庫都開不了 → 寫「判不了」,**不寫成缺**。

---

## 三 · 連帶的兩支根修(都是匯流排實跑照出來的)

### `CGC_MDL118_PlotDataLaw v0101` — 庫在 ≠ 表在

`ohlcv()` 只擋了「庫檔不在」(`DB_TW.exists()`),沒擋「庫在但表不在」。
新機器/剛建的空庫正是這個形狀,於是 `CatalogException` 裸奔到最上層,
一支**只是沒料**的引擎被報成**壞掉**。

修在**正主一處**,三個呼叫者(`VAP_ENG009` / `ENG013` / `ENG015`)一起好——
不是三支各寫一份預檢(那是第二、三、四顆頭)。

順帶量到:**v0100 自己的自測在空庫機器上直接崩**,連 `[計]` 都印不出來。
它的檢 ④ 用的守門正是我剛修掉的那個不足守門(`DB_TW.exists()`)——**檢法自己要先站得住**。

### `VAP_ENG015_SeabornStackBridge v0103` — 因由不上 stdout 等於沒說

缺料被標成 `FAIL`,而且真因由只寫進 RUN json,外面看到的只有一行索引頁 + `rc=2`。
改 `SKIP` + 逐件印狀態與因由。

離開碼改動(全數缺料且零 PASS → rc2)**量過才改**:全樹搜過,
**沒有任何調度者在讀本支 `run` 的 rc**(SelftestGrid 沒收它,ClosingGate/FamilyUI/DeckServer
都沒叫它,短令 `via-vapstack` 也不分支)。而這一改正好對齊批400 F5 給 ENG009 立的
「缺料誠實停 rc2」慣例——本支原本回 0 才是異類:**什麼都沒產出卻報綠**。

---

## 四 · 又兩個「看不見的儀器」

`CGC_MDL118` 立於**批330**、`VAP_ENG015` 收容於**批327**,
到批471 為止 —— **兩支都不在自測格上**。沒有站,所以沒有人叫過它們,
MDL118 的自測會崩這件事就一直沒被發現,直到匯流排一次調度 VAP 6 項把它照出來。

`CGC_MDL064_SelftestGrid v0294` 三站一起設(204 → **207 站**):

| 站 | 檢數 |
|---|---|
| 引擎調度匯流排(批471) | 十九檢 |
| 繪圖/TA 資料律(批330 立;批471 **補站**) | 七檢 |
| Seaborn 垂直圖組橋接(批327 收容;批471 **補站**) | 九檢 |

---

## 五 · 更正自測格一條舊記載的**事實錯誤**

`CGC_MDL064` 的 `v0252→v0253`(批418)寫著:

> 「…**2026 恰好也是真實上市代號 聚亨**,連逐驗名冊都擋不住」

批471 實測名冊:

* **聚亨 = 2022**(鋼鐵工業 · TWSE),不是 2026
* `2026` 在 `tw_listings_industry` 的 **1,978 檔裡一筆都沒有**(`tw_listings` 891 筆也沒有)

ENG073 v0108 的年份守衛**本身是對的**(年份形狀的四碼需要裁決),但那條紀錄
**給的理由寫錯了公司**。舊條目不改(那是歷史),在 v0294 追記更正——
留著錯的理由,下一個人會照著它去修一個不存在的問題。

---

## 六 · 實測結果

### 自測

| | |
|---|---|
| `CGC_MDL148` 十九檢 | **19 / 19** |
| `CGC_MDL118` 七檢 | **7 / 7** |
| `VAP_ENG015` 九檢 | **9 / 9** |
| Grid 三新站 | **OK 3 · FAIL 0** |

### 實跑(37 項 · 真跑家族 vrn,vap)

| 燈 | 數 |
|---|---|
| GREEN | 7 |
| NODATA(缺料) | 4 |
| ABSENT(缺件) | 3 |
| PLAN(沒動手) | 23 |
| **RED** | **0** |

逐項(非 PLAN):

| 燈 | 項 | 因由 |
|---|---|---|
| GREEN | `vrn_firstpage` `vrn_structdb` `vrn_finpages` `vrn_fourpoint` `vrn_digest` `vrn_ui` `vap_one_demo` | — |
| NODATA | `vrn_markdown` | 「無可轉檔(誠實)」 |
| NODATA | `vap_stack` | 「庫在但缺表:tw_daily_prices(表 18 張)」 |
| NODATA | `vap_heatmap` | 「ENG070 ROTATION 存證缺(先跑分類引擎)」 |
| NODATA | `vap_dashboard` | 「誠實停 rc2 · 缺 4 項表」 |
| ABSENT | `vap_std_dashboard` | 缺件:`plotly 缺席` |
| ABSENT | `vap_one_render` | 缺參數:`argument --render: expected one argument` |
| ABSENT | `vdf/fin_statements` | 引擎不在位(冊上宣告、檔案沒有) |

### 產出契約(本輪實跑項)

**在 10 · 缺 3 · 判不了 5**。三個「缺」都是真的缺
(`vap_stack`/`vap_heatmap` SKIP 了沒產出;`vap_std_dashboard` 卡在 plotly 沒產頁)。

---

## 七 · 怎麼用

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName

via-bus                      # 目錄(冊 → 尾版 → 在位)
via-bus vrn                  # 只看 vrn 家族
via-bus run vrn              # 真跑 vrn,其餘照樣只解析,產多矩陣 HTML
via-bus run vrn,vap          # 真跑兩族
via-bus one vrn_firstpage    # 只跑點名的那一項(寫庫動詞只認這條路)
via-busui                    # 開多矩陣頁
```

**預設不動手**:不加 `run`/`one` 一律只解析(dry)。
調度層的預設值錯一次,代價是在別人的機器上動了不該動的東西。

---

## 八 · 本批的紀律

* 零網路 · 預設 dry · 零 CDN · 零彈窗
* **寫庫動詞閘**:家族全掃永不代跑
* **同意閘絕不代設**(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 一律候操作員)
* 正本零觸碰:本批跑 `vrn_ui` 會重生 `VIA_UI_DailyBrief_v0100.html` 等正本頁,
  而本容器是空庫 → 每一輪跑完都 `git checkout --` 還原,**一個字都沒進 commit**

## 九 · 還開著的(候操作員裁決)

| | 事 | 狀態 |
|---|---|---|
| A | `vap_stack` 那條鏈要真跑出圖,得先有 `tw_daily_prices`(本容器空庫) | 候工作站實跑 |
| B | 姊妹倉 `VIA-VDF-VRN` 分歧(`grok/via-token-gov-20260910` 領先 main 93 / 落後 54) | 候裁決 |
| C | 3 支 VENDOR 檔移入 `_quarantine_pip_vendor` | 候裁決 |
| D | `panorama_xcheck_v110.py` import 不存在的 `MDL001_Conv_v110` | 候裁決 |
| E | 其餘 11 支仍綁舊 `tw_listings`(`VDF_ENG052`/`ENG081` 是**寫入者**,不得一律改) | 候裁決 |
| F | **正本頁再生閘**:任何人在空庫環境跑 `via-famui`,會把操作員的正本頁改寫成「缺(誠實)」——本批靠人工還原擋了 4 次,應該由 MDL138 自己擋 | **新開,建議下一批做** |
