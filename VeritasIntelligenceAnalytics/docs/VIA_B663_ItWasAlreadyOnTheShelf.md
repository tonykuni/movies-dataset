# 批663 · 那份附件三個多月前就在架上了

## 你的令

> 1. 分類整合同意自只增不減 ssot regex 同義字 附件參考全部同步更新
> 2. 不懂 請說明

## 先量:附件是什麼

`InvestmentRegexPattern_VALIDATED.py` v3.0 · 2,804 行 · 141 個 `PatternDef` + 6 條數字格式式。

我第一件事不是接線,是拿它跟樹上比。比出來的結果是:

```
附件  sha 965c033ed23eca5a
倉內  functional modules/VRN/InvestmentRegexPattern_VALIDATED.py
逐行差異:14 行 —— 全部是 VIA 自己加的加速器橋
```

而且早就有晉升紀錄:

```
supportive modules/VIA_Canonical_Units/InvestmentRegexPattern_PROMOTION_RECORD_v0100.json
record_date  2026-08-05
sha256       965c033ed23eca5a…   ← 跟你剛附的那份,一個位元都不差
status_after ACTIVE — VRN 欄位 regex 唯一真相
```

**這份附件在倉裡躺了三個多月,而且已經被收割、已經晉升。**

## 我上一輪差點做錯的事

我原本要新建一本 `VIA_FinancialFieldRegex_SSOT_v0100.json`,把 147 欄 × 499 式寫進去。

沒做,是因為我多翻了一個架子:

```
functional modules/VRN/knowledge/VRN_FinData_Synonym_v0100.json   195 欄 · 1,178 條同義
functional modules/VRN/knowledge/VRN_FinStatement_Synonym_v0100.json  7 表 · 141 科目
   policy:「科目歸屬自 pattern 庫 StatementType」   ← 就是這份附件
```

逐群比,**44 / 23 / 25 / 6 / 22 / 21 —— 一欄不差**。

真做下去,會做出**同一本書的第三個副本**,而且每一步看起來都很合理。
→ **LL306:「這是新料」這個判斷,取決於我翻了哪個架子。**

## 我更正一個誤判

上一輪我說「附件帶進來 8 條全新 pattern(eps_basic 4 + eps_diluted 4)」。**錯的。**

那 8 條早就在冊裡,在 `basic_eps` / `diluted_eps` 底下 —— 冊自己還記著 `merged_from: ["eps_basic"]`。
我的比對器拿鍵名直比,`eps_basic ≠ basic_eps`,就判了「缺」。

```
正本 499 式 → 落冊 499/499 · 一條不缺
```

→ **LL307:比對兩份東西之前,先問「我比的那個 key,兩邊是同一個名字嗎」。**
(LL299 是「row 真的有這個 key 嗎」,這次是「key 真的是同一個名字嗎」——同一條河的第二個渡口。)

## 真缺口在下游:料在 A,門開在 B

`VRN_Financial_Synonyms_SSOT.py` 的 `METRIC_SYNONYMS` 有 18 個正規名。
拿這 18 個名字去冊裡查「認得出頁面上哪些字」:

| | |
|---|--:|
| 查得到辨識式 | 12 |
| **在冊、但 patterns 0 條** | **4** — `ebit` · `eps` · `ocf` · `op_profit` |
| **冊裡根本沒這個鍵** | **2** — `eps_basic` · `eps_diluted`(冊裡叫 `basic_eps`/`diluted_eps`) |

**18 個正規名裡,6 個走不到辨識式。三分之一。**

看 `eps` 那一筆就懂了:

```
eps          zh=基本每股盈餘   patterns=[]        ← 上游 normalize_metric("每股盈餘") 吐這個
basic_eps    zh=基本每股盈餘   patterns=5 條      ← 料在這裡
```

同一個中文名、兩個鍵、中間沒有橋。**L101「一個名字只能有一扇門」的反面。**

## 修法:搭橋,只增不減,零新造詞

兩條車道,**都只取冊上既有的字**:

| 車道 | 依據 | 筆數 |
|---|---|--:|
| **A** `alias_index` | 冊自己記的 `merged_from` 反查(鍵被摺掉了,名字還在被上游喊) | 4 |
| **B** `same_as` | 同中文名**逐字相同**、一邊有式一邊空 | 13 |

逐字相同才算。「營業現金流」≠「營業活動現金流」—— 那兩個字面不同,**要不要當同一件事是你的裁定,不是我的**(LL90)。

只增不減,逐鍵驗過:

```
metrics 鍵 195 → 195 · 消失 0 · 新增 0 · **既有值被改 0**
逐欄新欄     same_as · same_as_basis
頂層新欄     alias_index · same_as_count · pending_operator · bridge_policy
```

查詢跟橋走,而且**借來的看得見**:

```
patterns_of(book, "eps")  →  5 式,借自 basic_eps
patterns_of(book, "revenue") → 6 式,自有
```

不把別人的式當自己的,免得下游以為這一欄本來就認得出。

## 結果

```
正規名 18 · 走得到辨識式 16(其中 4 個是借來的)· 仍然斷鏈 2
借道:eps→basic_eps · eps_basic→basic_eps · eps_diluted→diluted_eps · op_profit→operating_income
斷鏈:ebit · ocf     ← 兩個都在待裁定名單上
```

## 新的一本小冊,和一個被跳過三個月的東西

正本 `NUMBER_PATTERNS` 那 6 條是帶 capture group 的**擷取式**(從一段字裡把數字抓出來),
不是欄位同義字。收割器 v0104 第 219 行誠實跳過了它,理由也寫了 —— **但沒給下一步**(L92)。

所以它三個多月來哪裡都不在。本批給它自己的冊:

```
VRN_NumberFormat_Regex_v0100.json · 6 式
amount_tw · amount_parenthesis · percentage · ratio · eps · per_share
```

不混進同義冊 —— 混了,「認得出欄位名」跟「抓得出數字」就變成同一件事。

## 對帳器:那個躺了三個多月的 20

晉升紀錄自報 **525 pattern 定義**。我用 AST 數正本:

```
141 PatternDef × 499 式  +  6 數字格式式  =  505
紀錄自報 525 · 實有 505 · **差 20**
```

差在哪不重要,重要的是:**那個數字從 2026-08-05 寫上去,到今天沒有任何東西在對它。**

所以本批留的不是一次修正,是一支**對帳器**:

```
via-finlex --reconcile
```

- 用 **AST 零執行**當第二把尺(收割器是執行正本取屬性;自己數自己不叫對帳)
- 逐條比正本 ↔ 冊
- 量 18 個正規名走不走得到辨識式
- 待裁定的 **19 欄逐欄列名**

→ **LL308:一個沒有對帳器的數字,就只是一個看起來很負責的數字。**

## 誠實態:GATED 不是紅燈

對帳站的 rc 不是二分的:

| rc | 態 | 什麼時候 |
|--:|---|---|
| 0 | GREEN | 一條不缺、零斷鏈 |
| 1 | RED | 正本的式沒落冊,**或**斷鏈的名字不在待裁定名單上(橋該接沒接上,引擎的錯) |
| **4** | **GATED** | 斷鏈的名字**全都在**待裁定名單上 —— 料齊、判斷做完、剩那一步不歸我 |

格子新增期望值 `gated_ok`(rc 0 或 4 都算過)。

把 GATED 算成紅,等於逼自己去填一個該由你填的空;填下去就是發明同義字。
**判錯的紅燈和假綠一樣傷。**

## 待你裁定的 19 欄

這 19 欄辨識式 0 條、兩條車道都接不上(中文名跟冊上有式的那個不一樣):

```
capital_expenditure · cashflow_per_share · cfps · debt_change · diluted_shares · ebit
eps_qoq · eps_yoy · long_term_investment_change · non_current_liabilities · ocf · operating_cost
parent_equity · period · sales_qoq · sales_yoy · share_capital · shareholders_equity
working_capital_change
```

兩個具體的例子,你一句話就能結掉:

1. **`ebit`** — 冊上 zh 是空的,en 是 `EBIT`。台灣財報實務裡 EBIT 常被當成「營業利益」,
   但兩者不完全相等(營業外收支怎麼算)。要不要接到 `operating_income`(有 5 式)?
2. **`ocf`** — zh「營業現金流」。冊上另有 `operating_cf`(zh「營業活動現金流」,1 式)
   和 `operating_cash_flow`(zh「營業活動淨現金流入(出)」,4 式)。三個名字、三條路。

要接的話,指名「A 併到 B」就好。我不自己填。

## 本批動到的

| 檔 | |
|---|---|
| `functional modules/VRN/vrn_finlex_v0105.py` | 搭橋 + `patterns_of` + `--reconcile` + 數字格式冊;廿三檢 |
| `functional modules/VRN/knowledge/VRN_NumberFormat_Regex_v0100.json` | 新冊 6 式 |
| `functional modules/VRN/knowledge/VRN_FinData_Synonym_v0100.json` | +`same_as`/`alias_index`/`pending_operator`(既有值零改動) |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0420.py` | `gated_ok` 期望值 + 對帳站;264→265 |

## 還沒登錄的一扇門

`via-finlex` **在 `Register-VIA-Commands-v0232.ps1` 裡找不到,根目錄也沒有 `via-finlex.cmd` 梭。**

也就是說這支引擎跑了這麼久,你在工作站**沒有短令可以叫它**,只能打全路徑。
`--reconcile` 也一樣。

L70 說未經你逐次許可我不得動任何 `.ps1`。所以我只到這裡,不代改。
要的話給我一句「准改 Register 加 via-finlex」,我就補上短令 + 梭。
