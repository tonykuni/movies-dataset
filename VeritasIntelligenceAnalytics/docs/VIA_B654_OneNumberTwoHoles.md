# 批654 · 一個數字底下是兩個洞

## 你的令

> 檢視上下對話及母系統 GITHUB,整合 SSOT REGEX 同義字、邏輯、參數、因子,
> **只增不減去衝突,自測自修改直到成功**。

矩陣第一次在鏈上跑滿 105 份,照出兩件事。兩件都是**字彙衝突**,不是資料問題。

---

## 一、上漲空間整欄 GREEN 0

```
上漲空間   upside_state 為 EXACT_MATCH_DB / ROUNDING_ONLY_DB   GREEN 0  YELLOW 38  NODATA 67
```

容器 81 份是 `0 / 30 / 51` —— **同一個簽名**。整欄零綠,那是一盞不會亮的燈。

### 兩邊講的不是同一種語言

| | |
|---|---|
| ENG083 的尺收 | `EXACT_MATCH_DB` · `ROUNDING_ONLY_DB` |
| ENG073 實際寫 | `EXACT_MATCH` · `ROUNDING_ONLY` · `DB_DERIVED` · `SINGLE_SOURCE` · `MISSING_SOURCE` |

`_DB` 那個後綴,只在一段**條件寫錯的**程式碼裡才加得上:

```python
if basic["upside_state"] in ("MISSING_SOURCE", "SINGLE_SOURCE") \
        and basic["upside_db"] is not None:
```

於是最荒謬的事情發生了 —— 看你自己那一行實跑:

```
[EXACT_MATCH] 6873 泓德能源 TP=208.0 P=169.5 庫P=169.5(P_CONFIRMED_DB)
              升幅 報告=22.7 算=22.7 庫算=22.7
```

**頁上寫的、我自己算的、庫裡算的,三個都是 22.7。**
這是可能拿得到的最強證據,而它寫出來的狀態是 `EXACT_MATCH` —— 尺不收。

### 改法:只增不減

**既有狀態字的拼法一個都沒動**(下游還在讀)。動的只有條件:

```python
if basic["upside_db"] is not None:          # ← 從「先前是什麼態」改成「庫算得出來沒有」
```

理由很簡單:`_DB` 講的是「**這一格拿庫對照過**」,那是**證據有沒有到位**的事實,
跟它先前是什麼狀態無關。

### 怎麼知道這不是把燈刷綠?看它會不會讓東西變壞

```
[EXACT_MATCH] 3231 緯創 CITI TP=165.0 P=114.0 庫P=109.5(P_DB_CONFLICT)
              升幅 報告=44.7 算=44.7 庫算=50.7
```

頁上的 P 跟庫的 P 就差了 4%,升幅當然對不上 —— 這一筆會被降成 `FORMULA_MISMATCH_DB`。
**會變壞的那一半,才是這把尺誠實的證據。**

### 容器證不出來,我就說證不出來

```
容器庫:列 2 · upside_db 非空 0 · price_db 非空 0 · tw_daily_prices 表不存在
```

容器沒有台股價表,**結構上跑不到 `_DB` 那條路**。所以證明落在自測:
檢 ㊹ 自己建一個帶價的 DuckDB,一份該升(`EXACT_MATCH_DB`)、一份該降(`FORMULA_MISMATCH_DB`)。

把舊邏輯注回去:

```
[FAIL] ㊹ 庫對得上就要記成 `_DB`,對不上就要降級 …
[計] 四十四檢(44 檢) OK 43 · FAIL 1
```

尺咬得住。

---

## 二、「評等 NODATA 35」底下是兩個洞

矩陣印出這個數字,標準動作是「補同義字」。**真的拆開數:**

```
[評等]   **同義字缺口 0 份 / 0 種說法** · 抽取缺口 35 份
[券商]   同義字缺口 1 份 / 1 種說法('GF')· 抽取缺口 19 份
[分析師] 抽取缺口 30 份(沒有原字串可收=不是同義字的事)
```

| 缺口 | 意思 | 下一步 |
|---|---|---|
| **同義字缺口** | 原字串抓到了,正典冊查不到那個說法 | 補一個字就會好,**裁定權在你** |
| **抽取缺口** | 原字串**根本沒抓到** | 補同義字一點用都沒有,那是上游的事 |

> **評等那 35 個 NODATA,同義字缺口是零。**
> 「同義字持續完善」這個待辦,在這個缺口上**一份都救不到**——
> 而我在它底下掛了好幾批。 → **LL291**

合成一個數字,治法就被合成一個。給不出下一步的數字,通常是因為它把兩件事加在一起了。

### 候選一律 PENDING_OPERATOR

評等與券商的正典住在 `VIA_Financial_Institution_SSOT_v0100.py` —— **READ_ONLY 正典**。
`candidates` 車道**只列不寫**,一個字都沒動(LL90:同義的裁定權在操作員)。

目前唯一一個同義字候選:

```
  1 份 · 'GF'   例:GF-Thoughts on TPU Competition with GP…
```

要不要收,你說了算。

### 零新增短令

`via-vrnmatrix` 本來就透傳動詞,所以直接可用,沒有多長一顆頭:

```powershell
via-vrnmatrix candidates
```

---

## 你這邊

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
. .\VeritasIntelligenceAnalytics\Register-VIA-Commands-v0231.ps1
via-run25                    # 上漲空間那一欄應該會第一次出現 GREEN
via-vrnmatrix candidates     # 同義字候選(只列不寫)
```

上漲空間會綠多少,**只有你的機器答得出來**——容器沒有價表。
`roster` 那盞仍是 NODATA(6 檔老 ETF 缺價),補價要 `VIA_NET_CONSENT`,那是你的手。
