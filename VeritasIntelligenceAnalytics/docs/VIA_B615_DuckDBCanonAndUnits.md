# 批615 — DuckDB 是正典(裁定)+ 數字終於帶著單位

操作員裁定:**VRN 正典儲存層 = DuckDB。**

`vdf_tw_market.duckdb` 的七張 `vrn_*` 表是正典;
Parquet / CSV / JSON / Google Sheet 全部是**派生層,單向,永不回灌**。

批472 的原令措辭是「Parquet 當唯一真實主資料庫」,批615 覆蓋之 ——
**兩條令都留著,時序為準,不刪舊令**。

`VRN_ENG081_ParquetMainDB` 的實作其實從來沒變過:它 v0100 自己就量過並寫在抬頭 ——
「資料早就在正典 DuckDB 裡,所以本件是派生車道,不是第二套抽取」。
v0101 改的只是名分,並釘上單向律。

---

## 一、庫裡的數字沒有單位(LL178)

```
revenue  營業收入淨額  2023  REPORT_STATED  5839.0
```

**百萬元還是千元?下游無從得知。**

VRN 早就有 `UNIT_SCALE`:兩個值比一比,落在 1e±2/3/6 附近就判「這是單位差不是錯」。
那個判斷是對的,但它只能在**對照的時候**回答「這兩個數大概差 1000 倍」,
答不出「這個數到底是什麼單位」。單獨一列就永遠是謎。

而頁面上其實白紙黑字寫著「單位:新台幣百萬元」—— **資訊在抽取當下就在手上,只是沒被記下來。**

> **能在來源當下記下的事實,不要留到下游去推論。**
> 推論會有信心區間,事實不會。

### 補法

v0111 在抽取當下掃頁面的單位宣告:

```
單位:新台幣百萬元 / NT$ mn / US$mn / 單位:千元 / 億元 / 人民幣百萬 …
→ unit='百萬元' · currency='TWD' · scale=1e6 · unit_src='PAGE_DECL:新台幣百萬元'
```

**只認寫出來的。** 頁面沒寫就留 NULL 並記 `NO_DECL(頁面沒有寫單位;不由數值大小反推)`。
由數值大小反推會把一個誠實的缺口變成一個看起來很確定的錯誤。

語意單位另判,不吃頁面的金額宣告:

| 類 | 單位 | 例 |
|---|---|---|
| 比率 | `%` | 毛利率、YoY、ROE、殖利率 |
| 倍數 | `x` | PER、PBR、EV/EBITDA |
| 每股 | `TWD/股` | EPS、BVPS、DPS |

---

## 二、`1Q25` 整欄被丟掉

```python
PERIOD_TOKEN_RX = r"^(20\d{2}|\d{2}Q[1-4]|1[01]\d)…"
```

吃得下 `24Q1`(年在前),**吃不下 `1Q25`(季在前)** —— 那是外資報告最常見的寫法。
一個 token 不匹配,`parse_header` 就判這行不是表頭,**整張表的那一欄全部丟掉**。

v0111 兩種寫法都解,並補 `1H25` / `2H25` / `FY26` / `TTM` / `LTM` / 民國三碼,
拆成 `period_type` / `fiscal_year` / `fiscal_quarter`:

```
1Q25 → FQ · 2025 · Q1        25Q1 → FQ · 2025 · Q1   (同結構)
1H25 → FH · 2025             FY26 → FY · 2026
114  → FY · 2025(民國)      上半年 → UNPARSED:上半年(留空,說出原文)
```

---

## 三、順手拆掉一顆未爆彈

```python
con.execute("INSERT INTO vrn_report_financial VALUES (?,?,?,?,?,?,?,?)",
            list(r.values()))
```

**靠 dict 順序的位置參數。** 而 WORD 道的列多了 `mops_rank` / `mops_why` 兩鍵 ——
10 個值塞 8 個位置。加欄時一併改成具名欄位 INSERT。

---

## 四、遷移只增不減

`ALTER TABLE … ADD COLUMN IF NOT EXISTS` 八欄,舊列留 NULL。

**NULL 的意思是「還沒重抽」,不是「沒有單位」** —— 兩者不可混為一談。
要填滿就重跑一次 `via-vrnin` / ENG074,新抽的列才會帶單位。

---

## 五、自審

第一版檢㉑ 拿 `period_parts("1Q25") == period_parts("25Q1")` 比**整個 dict**,
而 `why` 欄記的是原文、本來就該不同,於是它判自己紅。
改成只比 `period_type` / `fiscal_year` / `fiscal_quarter` 三欄結構。

尺要量的是「兩種寫法解出同一個**結構**」,不是「兩個 dict 長得一模一樣」。

---

## 還沒做的(你說的②③)

- **② `EvidenceJson`**:規格建議的統一證據欄。樹上目前是**逐欄狀態**
  (`upside_state` / `price_state` / `ssot_state` / `conflicts` / `broker_src` / `kind_reason`),
  我認為比單一 ConfidenceScore 好;缺的是把 filename tokens、首頁 anchors、
  ticker candidates 這些**中間證據**也留下來。
- **③ 儲存層**:你已經裁定,不動。
