# 批596 — VDF_ENG070 那支真紅

操作員令:`VDF_ENG070 那支真紅 繼續修`

批595 量過 VDF 45 支尾版引擎、40 支有自測:**GREEN 36 · RED 3 · NODATA 1**。
三紅裡兩支是 duckdb 鎖競爭(重跑就綠),**真紅只有 VDF_ENG070 一支**。

---

## 一、它紅得有多安靜

跑起來的樣子:

```
[族群分類] 24 族群指數 · LEADER 97 / PEER 363 / LAGGER 227 / UNRELATED 205 · 大中小 90/267/535 · VIA_UI_GroupClassIndex_v0100.html
  [榜] 通信網路 聚焦 190.7 · 等權 124.5 · 階層 137.6
  [故事] 誠實停:KeyError: 'story'
```

`run()` 回 **rc0**、存證 `GROUP_CLASS_20260917.json` 照寫、U/I 頁照產。
但**一整段故事性分群不見了**——`MASTER_LIST` / `ROTATION` / `WINDOW_COMPARE` /
`STORY_CLASS` / `STORY_MEMBER` 五種產物一個都沒有。

自測則是另一種假象:`_latest("STORY_CLASS_*.json")` 回 `None`,下一行
`.read_text()` 直接 `AttributeError`,**七個檢驗一起變 FAIL**——
把「缺料」報成「壞掉」。十八檢當時是 `OK 11 · FAIL 7`。

---

## 二、根因鏈(逐段量出來的,不是猜的)

1. `_data_ready()` 回 **True**、`run()` 回 **rc0**、①–⑥ 全過
   → 引擎**真的跑了**,主產物完整。
2. `VIA_Reports/group_class/` 裡**沒有** `STORY_CLASS_*` / `ROTATION_*` / `MASTER_LIST_*`
   → `_latest(...)` 回 `None` → 自測崩。
3. 第 1599 行 `if story.get("summ"):` 把整段輸出關掉;而整段包在
   `except Exception as exc: story["err"] = f"{type(exc).__name__}: {exc}"` 裡
   → **例外被接住、塞進一個 dict 欄位、然後那個欄位從來沒被寫出去**。
   存證 JSON 的頂層鍵是 `['meta','constitution','roles','sizes','top_att']`,**沒有 `err`**。
4. 帶真 `roles` 重放,例外原文:

```
File ".../VDF_ENG070_GroupClassificationIndex_v0111.py", line 1063, in build_master
  mm = mm.merge(cs, on=["ticker", "story"], how="left")
KeyError: 'story'
```

5. 直接量 `capital_style()` 的空表守衛:

```
EMPTY-GUARD 欄位 = ['ticker', 'foreign_ratio', 'capital_style', 'capital_asof']
缺 story ? True
```

而有料路徑是 `out.append({"ticker": r.ticker, "story": sname, ...})`——**五欄**。
金流整庫缺(`tw_chip_inst` 表不在)→ 走空表守衛 → `cs` 沒有 `story` 欄 →
`merge(on=["ticker","story"])` → `KeyError`。

`classify_story` 本身是好的(`mem 51 · summ 22 · panel 33507`),
**不是缺料,是程式缺一欄**。

---

## 三、三修(v0112)

### ① 根因:空表守衛的欄位與語意都要和有料路徑一致

語意面也錯了:整庫無金流的正解是**每一列「候料」**
(同有料路徑 `foreign_ratio` 缺時的判法),不是「沒有這些列」。

```python
if not len(flows):
    mb = (members[["ticker", "story"]].drop_duplicates().copy()
          if members is not None and len(members)
          else pd.DataFrame(columns=["ticker", "story"]))
    mb["foreign_ratio"] = None
    mb["capital_style"] = "候料"
    mb["capital_asof"] = None
    return mb[["ticker", "story", "foreign_ratio", "capital_style", "capital_asof"]]
```

### ② 故事段三態入存證,RED 時 rc 回 1

```python
story["state"] = ("RED" if story.get("err") else
                  "GREEN" if story.get("summ") else "NODATA")
meta = {..., "story_state": story["state"], "story_err": story.get("err"),
        "story_trace": story.get("trace"), "story_note": STORY_STATE_NOTE[story["state"]]}
...
return 1 if story["state"] == "RED" else 0
```

- **GREEN** 五種產物都寫了
- **RED** 拋例外 → 產物缺席 → `rc=1`(**舊版恆 0**)
- **NODATA** 沒例外但群摘要空(登錄冊/資料不足)→ `rc=0`,但存證講明白

### ③ 自測缺件報 NODATA,不再崩

`_story_state()` 讀存證的 `meta.story_state` / `meta.story_err`;
`_gate(name)` 在故事段非 GREEN 時把該檢報成 **NODATA 並指名缺因**,
七個故事段依賴的檢驗(⑦⑧⑩⑪⑭⑮⑯⑰⑱)一律走這條路。
計數行改成 `十八檢三態 OK/FAIL/NODATA`,`selftest` 回 `1 if fails else (2 if nodata else 0)`。
缺因**只印一次**,逐檢只帶短標(省 TOKEN)。

---

## 四、實測(兩組,含對照組)

**正組**(本境資料在位):

```
[計] 十八檢三態 OK 18 · FAIL 0 · NODATA 0      (72 秒)
```

**對照組**(不改引擎,行程內把 `capital_style` 換成必拋的函式,重現原病):

```
rc = 1 (舊版此處恆 0)
meta.story_state = RED
meta.story_err   = KeyError: 'story'
[計] 十八檢三態 OK 10 · FAIL 1 · NODATA 7 · 缺因:故事段=RED(見上)
selftest rc = 1
```

① 誠實 FAIL(引擎真的紅),七個依賴檢誠實 NODATA、**不崩、不假綠**。

---

## 五、格子自己的洞:這支引擎從來沒有站

量法:VDF 引擎尾版 **38 支有 `--selftest`**,格內 **29 支有站**。
缺的正是 **VDF_ENG070 / ENG071 / ENG072** 三支。

> ENG070 的真紅之所以能躲這麼久,根本原因不是它壞得隱密,是**沒有人跑它**。
> **「引擎有自測」和「自測有人跑」是兩件事,只有後者算治理。**

`CGC_MDL064_SelftestGrid_v0363` 補三站,**245 → 248**。
期望值三支都用 `nodata_ok`(rc0 或 rc2 皆 OK,**rc1 照樣紅**):

| 站 | 本境實測 | 秒 |
|---|---|---|
| 族群分類×價格指數十八檢三態(ENG070) | OK 18 · FAIL 0 · NODATA 0 | 72 |
| 族群回測六檢(ENG071) | OK 6 · FAIL 0 | 37 |
| 故事輪動橋八檢(ENG072) | OK 1 · NODATA 1 · SKIP 6(rc2) | 0 |

---

## 六、立法

**L78 空表守衛同構律**——任何「資料為空就提早回傳」的守衛,回傳的**欄位集合**
與**語意**都必須與有料路徑一致。欄少一個,下游 `merge(on=[...])` 就是 `KeyError`;
語意錯一格,下游算出來的是假的。

尺(AST):同函式內 `return pd.DataFrame(columns=[...])` 的欄集 vs `append({...})` 的鍵集,少者點名。
**對照組驗過尺不是壞的**:ENG070 **v0111 抓到 1 處**(`capital_style` 缺 `story`)、**v0112 為 0**;
全樹尾版 360 支掃出 **0 處**(唯讀掃描,已套 L77 排除清單)。

**LL151 被接住的例外,必須改變某個看得見的東西**——否則那不是誠實,是把紅燈鎖進抽屜。三件:

1. **`err` 欄位不是存證**——沒寫進檔案的東西,下一個人讀不到,等於沒有。
2. **rc 必須帶狀態**——一整段分析死掉而 rc 還是 0,是引擎級假綠,比整支崩掉更難查。
3. **自測不能崩在缺件上**——把「缺料」報成「壞掉」,跟把「壞掉」報成「沒事」一樣傷。

---

## 七、誠實註記

- 本境 `tw_chip_inst` / `tw_chip_margin` 表**不存在**,所以 `capital_style` 走的正是空表守衛那條路
  ——這個根因在**有籌碼資料的機器上跑不出來**。工作站若已回補籌碼,ENG070 v0111 也會是綠的;
  **綠在那裡不代表這個蟲不在**,它只是還沒被踩到。
- `外資內資主導` 這一欄在本境全部是 **「候料」**。那是誠實標,不是分析結果——
  要拿到真的 Foreign/Domestic/Mixed,得先跑 `via-chip`(籌碼回補)。
- ENG072 本境 rc2 是**上游沒料**,不是壞掉;它自己的八檢已經會誠實 SKIP。

---

## 八、修好上游之後,下游第一次被走到(全格複跑的兩盞紅)

補完三站跑全格,**250 站 OK 241 · FAIL 7 · SKIP 2**;格子自己的第二段「讓庫律序跑複判」
把 5 盞平行鎖撞的假紅轉綠,剩 **2 盞真紅**:

| 站 | 原因 | 是不是我造成的 |
|---|---|---|
| Seaborn 垂直圖組橋接九檢(VAP_ENG015) | `ModuleNotFoundError: No module named 'seaborn'` | **是**——但不是改壞,是**第一次被走到** |
| Veritas 中央控管台二十檢(CGC_MDL149)⑬ | 元件自動編號冊 `ACTIVE 5340/5343` | **是**——我漏了功能註冊七處的一處 |

先做對照組:拿**沒改過的舊格子 v0362** 跑同樣兩站,**兩站一樣紅**
——證明紅的不是我新加的三站,再往下查才查到真因。

**① VAP_ENG015**:以前 `ROTATION_*.json` 不在,它走「缺件=誠實 SKIP」;
現在 ENG070 修好、檔案真的產出了,它才**第一次**去跑收容包,於是量到本境沒裝 seaborn。
v0103 把這個報成 **FAIL**——正是 LL151 第三條的鏡像:**把環境缺件報成壞掉,跟把壞掉報成沒事一樣傷**。
`VAP_ENG015_SeabornStackBridge_v0104` 加 `_absent_mod()`:收容包 import 不到自己的相依
→ 誠實 **SKIP 並指名缺哪一支**,**不代裝套件**。收容正本
(`references/intake/VIA_VAPSeabornStack_b327/`)**一個位元組沒動**。
→ 九檢 OK 9 · FAIL 0,④ 的註記是「收容包相依缺席:seaborn(不代裝套件;裝了再跑)」。

**② CGC_MDL149 ⑬**:本批新增三個版本檔(ENG070 v0112 / Grid v0363 / VAP_ENG015 v0104),
**元件自動編號冊沒同步**。`VCGC registry-sync --apply`:**新 4 · 變更 92 · 退役 0 · AST錯 0**。
逐鍵驗過 diff 只動 `source`(尾版路徑前移)/ `line`(行號位移)/ `changed_at`,加 4 筆新記錄,
**零 ACTIVE→RETIRED**——只增不減沒有被破。

兩件都不是「ENG070 改壞了」,但**兩件都是這批造成的可見狀態改變**,推給別人就是逃。
→ **LL152**。

修完兩件再跑一次全格:

```
[計] OK 248 · FAIL 0 · SKIP 2(誠實三態)· 227s · 存證 GRID_20260918_104234.json
```

(第一段平行有 4 盞紅,全部被格子自己的「讓庫律序跑複判」轉綠=**duckdb 鎖撞的假紅**,不是引擎的事。)

**LL49 收尾**:全格跑完會拿本容器的**空沙盒庫**把 20 多張 U/I 頁與六本註冊表再生一次
(`VIA_Schema_Registry` 少 142 行、`VIA_IndustryUnifiedMap` TWSE 25→24、
`VIA_Engine_Consolidation_Register` n_unused 115→100……),那些**一律還原不提交**。
本批只留三本親手改的冊(台帳/政策庫/元件編號冊)+ 四個新檔。
