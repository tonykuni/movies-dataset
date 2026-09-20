# 批664 · 那把尺因為冊很誠實而懲罰了它

## 你的令

> 准改 Register 加 via-finlex。請自動測試自動完成一切後,確認 VRN VDF VIA 實測無誤導入,
> 生成輸出 HTML TESTING MATRIX REPORT BY RICH IN VERY DETAILES。確保 VIA 握所有現況紀錄
> LOGGING FOR ENVIRONMENT 所有的庫 LIBS SSOT REGEX 同義字 支援性工具 VDF VRN。
> 範圍限縮於此。先完成 VRN 因為他要電腦開機時才能實測。

## 先量:要不要新做一支

`CGC_MDL110 三軌測試矩陣` **已存在**,做的是 system/user/validation 三軌,而且明寫
「零重測=全讀既有存證」。所以我沒有再做一次三軌。

本支做的是另一件事 —— **六域資產現況 × 實測**,其中 LIBS 與 SSOT 是**當場 import、當場編 regex**。
查表回答的是三個月前的事。

還有一件真的沒人做過:**樹上從來沒有人用過 rich 的 `record=True` / `export_html`**
(只在收容夾的外來件裡有)。`inline_styles=True` 產出零外連,正好合 L100。

## 引擎上線第一跑,照出三件事

### ① 它把冊的說明欄當 regex 去編

`VRN_NumberFormat_Regex` 的 `policy` 那句話帶括號帶破折號,編不過 → 報了一盞紅燈。

**判錯的紅燈和假綠一樣傷。** 這是 LL302 的第二次發作(寫在說明欄的話被當資料讀走)。

修法不是「把那本冊跳過」,是把判準修對:說明欄的鍵名**前綴/後綴一起認**
(第一版只認完全相等,`why_not_range` 就從 `why` 底下漏出來了),
超長字串判散文 —— 但**記進 `skipped` 讓它看得見**。

> 靜默跳過等於自己給自己開豁免,那正是假綠的長相(L87 豁免必附理由)。

### ② 它把冊「自己點名的落選清單」當成冊的缺陷

MDL115 v0101 刻意留著一份 `dropped_uncompilable` —— 「這些式我收不進來,具名列出」。
那是負責任的做法。

我的尺轉頭把那份名單數成「這本冊有 5 條壞式」。

**等於因為它誠實而懲罰它。** 一本把自己的落選具名列出的冊,跟一本把落選偷偷丟掉的冊,
在我那把尺底下,前者反而比較紅。

→ **LL309:一本冊把自己的落選具名列出來,是負責任;一把尺把那份名單數成它的缺陷,
是在懲罰誠實。落選清單是冊的良心,不是冊的傷口。**

### ③ 全樹 regex 清冊把式記斷了 —— 這件是真的

```
top_shared[9]  '<meta\s+name=["\'            ← 斷在式子裡跳脫過的引號上
top_shared[24] '\b(Buy|Sell|…|Outperform|'   ← 隱式相接只拿到第一段
```

根因在 MDL115 自己的尺:

```python
RX = re.compile(r"""re\.(?:compile|search|…)\s*\(\s*r?(['"])(.+?)\1""")
```

`(.+?)\1` 非貪婪吃到**第一個同款引號**就收手。式子裡只要有一個跳脫過的引號(`["\']`),
它就在那裡斷掉。那條 `<meta` 式有 **43 個檔**共用。

**誰拿冊上那條式去全樹取代,會一無所獲,而且不知道為什麼。**
東西在、只是不對 —— 那是最難查的一種錯。

→ **LL311:寫一條 regex 去讀 regex,永遠會在某個跳脫上斷掉。
去讀原始碼裡的字面,走 AST —— 跳脫與隱式相接讓 Python 自己還原。**

## 順手補上的 L77

改走 AST 之後,冒出 9 個「解不開」的檔。一看,三支的錯是真的語法錯 ——
但它們全住在 `VIA_RetiredEngines/…/_review_quarantine/`。

**掃描根沒帶排除清單**,死碼的 regex 被算進全樹分母(L77)。

```
樣式 1264 → 1110      補排除,分母變誠實(L57)
top_shared 編不過 2 → 0
真語法壞 3 → 0        那三支是死碼,不是現況
```

## 剩下 6 檔「解不開」,不是檔壞

```
CGC_MDL116_UnifiedShell_v0106..0110 等
SyntaxError: f-string expression part cannot include a backslash
```

那個限制 **py3.12(PEP 701)才鬆綁**。容器是 3.11,工作站家族境是 3.12 ——
**同一支檔,兩邊解出來的結果不一樣**。

把它判成「檔壞了」是判錯的紅燈:壞的是我這邊的解譯器版本,不是那支檔。

所以 MDL115 v0101 把解不開的**逐檔分類**:`needs_py312`(版本)vs `syntax_broken`(真壞)。

→ **LL310:「9 檔解不開」混成一句話,會害人去修 6 支根本沒壞的檔,
而真壞的那幾支照樣沒人管。解不開要逐檔說清楚是誰的錯。**

## 誠實態:GATED 不是紅燈

六域矩陣在容器跑出來:

```
RED 0 · GREEN 24 · GATED 6 · NODATA 3 · ABSENT 0  →  GATED
```

那 6 格全是同一件事:**容器沒有家族境**。家族庫缺 `plotly` 之類,在這裡是缺料不是壞掉。

把它判成紅,下一步就會變成「去把套件裝起來」—— 而裝套件是操作員的手。
**一盞判錯的紅燈,會把人推去做一件不該他做的事。**

## HTML 報告為什麼不入倉

```
.gitignore:205  VeritasIntelligenceAnalytics/VIA_Reports/*   # run-local reports (never committed)
```

那條規矩是對的。容器量到的家族境是 GATED,把它 commit 進去、下次有人打開來看,
就會以為那是系統的現況 —— 那正是 LL49 的長相。

引擎、短令、梭都入倉了。**你在工作站打 `via-state html`,量到的才是你的機器。**

## 本批留下的

| | |
|---|---|
| `CGC_MDL169_VIAStateMatrix_v0100.py` | 六域現況矩陣 · rich 直出 HTML · LOGGING 三件;十八檢 |
| `CGC_MDL115_SSOTRegexDict_v0101.py` | 改走 AST · 逐檔分類 · L77 排除清單;九檢 |
| `Register-VIA-Commands-v0233.ps1` + 兩支梭 | `via-finlex` / `via-state`(L70 逐次許可) |
| Grid v0421 | 三站;264 → 267 |
