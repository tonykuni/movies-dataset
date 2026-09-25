# VIA 交接紀錄 · 批663–664(2026-09-20)

> 範圍(操作員批664 令):**限縮於** 環境 LOGGING · 所有的庫 LIBS · SSOT REGEX 同義字 ·
> 支援性工具 · VDF · VRN。先完成 VRN(它要電腦開機才實測得到)。其他先不動。

---

## 〇 · 一句話

批663 把「附件是不是新料」問清楚了(**不是**,三個多月前就在架上),真缺口在下游。
批664 把「VIA 到底握不握有現況」做成一支**可以重跑的引擎**,而它上線第一跑就照出三件事 ——
其中兩件是我自己的尺歪了,一件是倉裡躺了很久的真缺陷。

---

## 一 · 批663 · 那份附件三個多月前就在架上了

### 量到的

```
附件 InvestmentRegexPattern_VALIDATED.py  sha 965c033ed23eca5a
倉內 functional modules/VRN/ 同名檔       逐行差異 14 行(全是 VIA 自己加的加速器橋)
晉升紀錄 2026-08-05 已在,sha 一個位元不差
正本 141 PatternDef × 499 式 + 6 條數字格式式 = 505
落冊 499/499 —— **一條不缺**
```

我原本要新建一本 SSOT 收那 147 欄。沒做,因為多翻了一個架子:
`knowledge/VRN_FinData_Synonym_v0100.json` 已有 195 欄 1,178 條,逐群比 44/23/25/6/22/21 一欄不差。
→ **LL306:「這是新料」這個判斷,取決於我翻了哪個架子。**

### 更正一個誤判

我說過「附件帶進 8 條全新 pattern」。**錯的**。那 8 條早在 `basic_eps`/`diluted_eps` 底下,
冊自己記著 `merged_from`。我的比對器拿鍵名直比,`eps_basic ≠ basic_eps` 就判了缺。
→ **LL307:比對之前先問「我比的那個 key,兩邊是同一個名字嗎」。**

### 真缺口:料在 A,門開在 B

`VRN_Financial_Synonyms_SSOT` 的 18 個正規名拿去冊裡查辨識式:

| | |
|---|--:|
| 查得到 | 12 |
| 在冊但 patterns 0 條 | 4(`ebit`·`eps`·`ocf`·`op_profit`)|
| 冊裡沒這個鍵 | 2(`eps_basic`·`eps_diluted`,冊裡叫 `basic_eps`/`diluted_eps`)|

修法:搭橋,只增不減,**零新造詞**。

| 車道 | 依據 | 筆 |
|---|---|--:|
| A `alias_index` | 冊自己記的 `merged_from` 反查 | 4 |
| B `same_as` | 同中文名**逐字相同**、一邊有式一邊空 | 13 |

逐字相同才算 —— 「營業現金流」≠「營業活動現金流」,那是**你的裁定**(LL90)。
逐鍵驗過:`metrics 195→195 · 消失 0 · 新增 0 · 既有值被改 0`。

結果:**正規名走得到 16/18**(其中 4 個借道),斷鏈 2 全在待裁定名單。

### 新的一支對帳器

晉升紀錄自報 **525**、AST 數正本實有 **505**,差 20 躺了三個多月沒人發現。
→ **LL308:一個沒有對帳器的數字,就只是一個看起來很負責的數字。**

---

## 二 · 批664 · VIA 六域現況矩陣(CGC_MDL168)

### 它是什麼

一支引擎,六個域,逐列誠實態,**每列帶出處與年齡**:

| 域 | 量什麼 | 怎麼量 |
|---|---|---|
| ENV | 家族境 python · 環境治理三本存證 | 在不在 + 存證多舊 |
| LIBS | 家族必要/選用庫 | **當場 import**(不是查表;查表回答的是三個月前) |
| SSOT | regex/同義字七本冊 | 筆數 · **逐條編得過嗎** · 有沒有活讀者 |
| TOOLS | 支援性工具 | 尾版家族 · 有沒有 `--selftest` · 格子總判 |
| VDF | 引擎尾版 · 存證年齡 · 站燈 | 讀既有存證(零重跑) |
| VRN | 同上 + 批663 對帳 | 實跑 `--reconcile` |

輸出三件:主控台 rich 矩陣 · **rich 直出 HTML**(`export_html(inline_styles=True)`,零 CDN 零外連,
`file://` 直開,零 `<script>`)· LOGGING 三件(`STATE_<時間戳>.json` 歷史 + `STATE_latest.json` 現況
+ `STATE_LEDGER.tsv` append-only 台帳)。

> 樹上從來沒有人用過 rich 的 `record=True`/`export_html`(只在收容夾的外來件裡有)。
> 這支是第一個。`CGC_MDL110` 三軌測試矩陣**不碰**,它做的是 system/user/validation 三軌
> 而且明寫「零重測」;本支做的是六域資產現況 × 實測,兩件事。

### 上線第一跑照出三件事

**① 我的尺把冊的說明欄當 regex 去編。**
`VRN_NumberFormat_Regex` 的 `policy` 那句話帶括號帶破折號,編不過 → 報了一盞紅燈。
那是**判錯的紅燈**(LL302 第二次發作)。修:說明欄鍵名前綴/後綴一起認,
超長字串判散文但**記進 skipped 讓它看得見**(靜默跳過等於自己給自己開豁免)。

**② 我的尺把冊「自己點名的落選清單」當成冊的缺陷。**
MDL115 v0101 刻意留著 `dropped_uncompilable`(具名不靜默,那是負責任的做法),
我轉頭把它數成「這本冊有 5 條壞式」——**因為它誠實而懲罰它**。修:落選子樹整棵跳過。

**③ 全樹 regex 清冊把式記斷了 —— 這件是真的。**

```
top_shared[9]  '<meta\s+name=["\'          ← 斷在跳脫過的引號上
top_shared[24] '\b(Buy|Sell|…|Outperform|' ← 隱式相接只拿到第一段
```

根因在 MDL115 自己的尺:`re\.(?:compile|…)\s*\(\s*r?(['"])(.+?)\1`。
`(.+?)\1` 非貪婪吃到**第一個同款引號**就收手,碰到式子裡跳脫過的引號就斷。
那條 `<meta` 式有 **43 個檔**共用 —— 誰拿冊上那條去全樹取代,會一無所獲而且不知道為什麼。

修:**MDL115 v0101 改走 AST 零執行**,跳脫與隱式相接由 Python 自己還原。
順手補 L77(掃描根一律帶排除清單):退役夾與隔離區的死碼本來被算進全樹分母。

```
樣式 1264 → 1110(補排除,分母變誠實)
top_shared 編不過 2 → 0
「真語法壞」3 → 0(那三支全住在 VIA_RetiredEngines/_review_quarantine,是死碼不是現況)
AST 解不開 9 → 6,而且**逐檔分類**:
   6 檔是 py<3.12 讀不動 3.12 語法(容器 3.11、工作站家族境 3.12)—— **不是檔壞**
   0 檔是真的語法壞掉
```

> 把那 9 檔混成一句「解不開」,會害人去修 6 支根本沒壞的檔,而真壞的照樣沒人管。

---

## 三 · 你要的四件,逐件交代

| 你的令 | 狀態 | 在哪 |
|---|---|---|
| 准改 Register 加 via-finlex | **做了** | `Register-VIA-Commands-v0233.ps1` + `via-finlex.cmd` |
| HTML TESTING MATRIX BY RICH | **做了** | `via-state html` → `VIA_Reports/state_matrix/VIA_State_Matrix_v0100.html` |
| LOGGING:ENV/LIBS/SSOT/同義字/支援性工具/VDF/VRN | **做了** | `CGC_MDL168` 六域;每跑一次落三件紀錄 |
| 交接報告 | **這一份** | `docs/VIA_Handover_20260920_B664.md` |

### 短令(兩支新的,pwsh 實測過真函式不是假樁)

```powershell
via-finlex --reconcile     # 正本↔冊對帳(rc 0 GREEN / 4 GATED / 1 RED)
via-finlex --build         # 收割落六冊
via-finlex --ask 每股盈餘   # 跨冊查

via-state                  # 六域矩陣(主控台)
via-state html             # 落 rich HTML + 三件紀錄,自動開頁
via-state --selftest       # 十八檢
```

> HTML 報告**不入倉** —— `.gitignore` 第 205 行寫著 `VIA_Reports/*  # run-local reports (never committed)`。
> 那條規矩是對的:容器量到的家族境是 GATED,把它當成你的現況就是 LL49。
> 你在工作站打 `via-state html`,量到的才是你的機器。

---

## 四 · 容器這一跑的六域現況(**這是容器,不是你的機器**)

```
RED 0 · GREEN 24 · GATED 6 · NODATA 3 · ABSENT 0  →  GATED
```

GATED 那 6 格全部是同一件事:**容器沒有家族境**(未設 `VIA_ENV_ROOT`)。
家族庫缺 `plotly` 之類,在容器是缺料不是壞掉。**真答案在你的機器上**:

```powershell
via-rungate --family vrn      # VRN 家族境逐庫探針
via-rungate --family vdf
via-state                     # 然後六域矩陣那幾格會從 GATED 變成真燈
```

**不代裝套件** —— 那是你的手。

---

## 五 · 還掛著的事(逐項,不含糊)

### 5.1 待你一句話就能結的(批663 對帳器列出來的 19 欄,最急的兩個)

```
ebit  冊上 zh 空、en=EBIT。要不要接 operating_income(5 式)?
      台灣實務常把 EBIT 當營業利益,但兩者不完全相等(營業外收支怎麼算)。
ocf   zh「營業現金流」。另有 operating_cf「營業活動現金流」1 式、
      operating_cash_flow「營業活動淨現金流入(出)」4 式。三個名字三條路。
```

指名「A 併到 B」我就接。其餘 17 欄同性質,`via-finlex --reconcile` 會逐欄列名。

### 5.2 L0–L5 六層的層名還沒被你覆核

VRN 邏輯架構索引冊把整條鏈切成六段,**那六個名字是我歸納的**,冊上自己寫著「請操作員覆核」。
批662 我又依那六層歸位了 15 支引擎 —— 一個暫定的框架用久了會變成事實上的正典,只是沒人裁過。

兩個具體的怪處:
- **L2 叫「結構與知識」**,裡面同時有 ENG074 財報頁(加工站)和 ENG063 詞庫(參考書)。
- **L5 叫「儲存」**,底下三支全標「非正典」—— 正典儲存(DuckDB,批615 你裁的)那一格是空的。

你回「可以」/「第 N 層改叫 X」/「應該是幾層」,三選一即可。

### 5.3 py<3.12 讀不動的 6 檔(不是壞,是版本)

`CGC_MDL116_UnifiedShell_v0106..0110` 等,f-string 裡有反斜線(PEP 701 才鬆綁)。
容器 py3.11 解不開走了退路,**你的家族境是 3.12,那邊解得開**。
在你機器上跑 `via-ssotregex --selftest`,`needs_py312` 應該會是 0。

### 5.4 更早的,沒動(範圍限縮)

- 評等/分析師 抽取缺口(上游擷取)
- 5 個券商同義候選(`GF`/`MORGANSTANLEY`/`UBS`/`CAPITAL`/`DAIWA`)PENDING_OPERATOR
- 12 個 UNKEPT 收容夾
- `VIA_Reports/regen_revert/` 備份夾累積了 40+ 個(每次再生閘 --apply 留一份);不影響判斷,但會長

---

## 六 · 本批實測(全部是真跑,不是宣稱)

```
finlex 廿三檢            OK 23 · FAIL 0
finlex --reconcile       正本式 505 · 落冊 499/499 · 正規名走得到 16/18 · → GATED
MDL115 九檢(v0101)      OK 9 · FAIL 0 · 樣式 1110 · top_shared 編不過 0 · 真語法壞 0
MDL168 十八檢            OK 16 · FAIL 0
MDL168 實跑              RED 0 · GREEN 24 · GATED 6 · NODATA 3 → GATED
Register v0233           pwsh 真函式實測:via-finlex / via-state 都叫得動
HTML 報告                21,651 bytes · 零外連 · 零 <script> · 六域齊
VCGC 二十三檢            OK 23 · 元件冊 5685/5685 · AST錯 0
VRN 索引冊               11 檢 OK 11 · 守門 指標 50 過期 0 GREEN
```

(全格子與再生閘的數字見本批 commit 訊息。)

---

## 七 · 本批動到的檔

| 檔 | |
|---|---|
| `functional modules/VRN/vrn_finlex_v0105.py` | 搭橋 + `patterns_of` + `--reconcile` + 數字格式冊;廿三檢 |
| `functional modules/VRN/knowledge/VRN_NumberFormat_Regex_v0100.json` | 新冊 6 式 |
| `functional modules/VRN/knowledge/VRN_FinData_Synonym_v0100.json` | +`same_as`/`alias_index`/`pending_operator`(既有值零改動)|
| `supportive modules/registry/CGC_MDL115_SSOTRegexDict_v0101.py` | 改走 AST · L77 排除清單 · 九檢 |
| `supportive modules/registry/CGC_MDL169_VIAStateMatrix_v0100.py` | 六域現況矩陣 + rich HTML + LOGGING;十八檢 |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0420/0421.py` | `gated_ok` 期望值 + 三站;264→267 |
| `Register-VIA-Commands-v0233.ps1` · `via-finlex.cmd` · `via-state.cmd` | 短令與梭(L70 逐次許可) |
