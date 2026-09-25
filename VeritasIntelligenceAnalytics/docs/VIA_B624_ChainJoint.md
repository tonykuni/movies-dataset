# 批624:兩支都 rc=0,整條報 OK,而鏈的後半段根本沒收到輸入

你跑的:

```
via-vrnmatrix run --in "C:\測試樣本報告"
[VRN_ENG083 v0100] 鏈實跑 · OK
   VRN_ENG072_FirstPageText_v0134.py rc=0 · …SyntaxWarning: invalid escape sequence '\.'
   VRN_ENG073_ReportStructuredDB_v0129.py rc=0 · [報告型別] 個股 42 · 產業 10 · 大盤晨報 6 · 海外 3 · 研討會 3
[VRN_ENG083 v0100] matrix · ABSENT · 庫不在:…\VRN\output\vrn_reports.duckdb
                                        (先跑 `via-vrnmatrix run --in <報告夾>`)
```

看起來完全正常:兩支 rc=0、64 份報告分好類、整條 OK。**三件事都是假的。**

---

## 一 · ENG073 一個旗標都沒收到

`run_chain` 給 ENG072 的是 `--in <你的夾>`,給 ENG073 的**只有 `run`**。
而 ENG073 的旗標叫 `--dir`：

```python
# v0100
steps = [_call(e72, ["run", "--in", str(src)])]
a73 = ["run"] + (["--db", db] if db else [])      # ← 夾呢？
```

所以那「個股 42 · 產業 10 …」**很可能根本不是你的檔**,是 ENG073 自己預設夾裡的東西。
兩支都 rc=0,於是整條報 OK ——**`rc=0` 只說「沒爆」,不說「接上了」。**

## 二 · 兩邊各用各的預設庫

| 誰 | 預設庫 |
|---|---|
| ENG083(讀矩陣) | `functional modules/VRN/output/vrn_reports.duckdb` |
| ENG073(寫庫) | `functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb` |

**兩個完全不同的檔。**所以 ENG073 就算寫了,`matrix` 也永遠讀不到。

## 三 · 修法句指回你剛剛打的那一句

`matrix` 說「庫不在…**先跑 `via-vrnmatrix run --in <報告夾>`**」——
那正是你剛做完的事。根因是那句話把兩種狀態壓成一句:

* **這一層還沒跑過** → 該叫你去跑
* **跑過了但庫沒落在這裡** → 該叫你去找庫

這是 L19 死結(LL195)的小號版本:閘沒有出口,而且出口的牌子指著來路。

---

## v0101 怎麼修

```python
dbp = Path(db) if db else DEFAULT_DB          # 庫在這裡解析一次
dbp.parent.mkdir(parents=True, exist_ok=True)
steps = [_call(e72, ["run", "--in",  str(src)])]
steps.append(_call(e73, ["run", "--dir", str(src), "--db", str(dbp)]))   # 兩半吃同一個
...
if not bad and not dbp.exists():              # rc=0 + 檔案不在 = NODATA,不是 OK
    out["state"] = "NODATA"
```

自測 18 → **21 檢**,三檢都照關節不照回傳值:

* ⑤ **關節**:`run_chain` 原始碼裡要看得到 `--dir` / `--db` / `str(src)`
* ⑥ **兩半吃同一個庫**:`dbp` 解析一次再往下傳
* ⑦ **兩態兩句**:沙盒各造一次「父夾不存在」與「父夾有東西但沒有庫」,兩句話必須不同,
  而且後者**不得**出現 `via-vrnmatrix run --in`

## 順帶:那一行假警告

`VRN_ENG072_v0134.py:7: SyntaxWarning: invalid escape sequence '\.'` ——
抬頭存證用的 Windows 路徑寫在非 raw 字串裡。碼一個字沒錯,
但**看久了會開始略過警告**,那才是真正的代價。

`v0135` 修法一個字元:抬頭的三引號前加 `r`。編譯警告 1 → **0**,自測 51/51。

> 寫這條版史的時候我自己又踩一次:第一版把那三個引號**寫進註解裡**,
> 當場把抬頭提早關掉,SyntaxError 指著一個中文句號。
> 說明跳脫字元的註解,自己不能帶跳脫字元。

---

## 重跑一次就知道真假

```powershell
via-presync
via-vrnmatrix run --in "C:\測試樣本報告"
```

這次如果數字跟上次不一樣,那就證明上次 ENG073 看的不是你的夾。
如果庫還是沒出現,v0101 會說 **NODATA** 並告訴你去看 ENG073 的 `status`,
**不會再叫你重跑一次**。

## 登錄

* 課 206(+LL204/LL205/LL206)· 台帳 1229
* 新件:`VRN_ENG083_VerifiedMatrix_v0101.py` · `VRN_ENG072_FirstPageText_v0135.py` ·
  `CGC_MDL064_SelftestGrid_v0379.py`(站名 18→21 檢)
