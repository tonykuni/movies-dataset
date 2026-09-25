# 批619:12_MatrixConsole 沒有卡 · 41 盞紅燈沒有一盞是真的

操作員貼回一整段 `via-allinone` 逐字稿,最後一行是:

```
[###############.....]  74%  步 12/15 12_MatrixConsole  已跑 159s/3600s(4%)  ·  卡斷
```

兩件事。一件是他看到的(卡斷),一件是他沒注意到但更嚴重的(41 盞假紅)。

---

## 一 · 那一步沒有卡,它是零輸出

量法:在容器裡直接跑同一支引擎。

```
$ python3 CGC_MDL149_VeritasCentralGovernanceConsole_v0117.py matrix --family vdf,vrn,vap
```

全程 **21 行輸出**:

| 行數 | 內容 |
|---|---|
| **18** | `@@PROGRESS\|65.1\|實測 3/17 · CGC_MDL155 統一 SSOT` 之類 |
| 3 | 最後的摘要 + 一頁路徑 |

而 `Invoke-VIA-AllInOne` 的噪音樣式第一條就是:

```powershell
$script:NoisePat = '^\s*(@@PROGRESS\||\[[█░]|[|/\-\\]\s+\[[█░])'
```

**一律丟掉。**所以這一步在畫面上不是慢,是**什麼都沒有**;逾時 3600s,就是一小時的全黑。
他在 159s 打「卡斷」是完全合理的判斷。

最冤的地方在 `CGC_MDL158` 自己的註解:

```python
def _p(pct: float, msg: str) -> None:
    """動態進度條協定:PowerShell 端解析 @@PROGRESS|<pct>|<msg> → Write-Progress。"""
```

**那個「PowerShell 端」從來沒有被寫出來。**協定有生產者,沒有消費者;
PowerShell 這側只學會了一件事——把它刪掉。

同一課的第三次:

* 批616 沒有進度
* 批617 有進度,但走 `Write-Progress`,在逐字稿裡看不見
* 批619 資訊明明就在 stdout 上,**是我自己刪的**

### v0111

`@@PROGRESS` 升為**第二個內層進度來源**。優先序:

```
心跳(SELFTEST_PROGRESS.json) > @@PROGRESS > 時間粗估(封頂 0.9)
```

兩個外部來源都要求**本步開始之後**才算數(LL179 同律:時間新不代表出處對)。
它仍然不逐行印(會洗版)——丟掉的是**行**,不是**資訊**。

容器實跑 `-Only 12_MatrixConsole`:

```
[#...................]   4%  步 12/15 ... 已跑  64s/3600s( 2%) · 內層 67% 實測 4/17 · CGC_MDL148 引擎匯流排
[#...................]   6%  步 12/15 ... 已跑  97s/3600s( 3%) · 內層 83% 實測 15/17 · VRN_ENG073 報告結構庫
[#...................]   6%  步 12/15 ... 已跑 105s/3600s( 3%) · 內層 89% 中央派送 dispatch --family all
```

全樹量過:吐 `@@PROGRESS` 的有 **8 個家族**,其中 `CGC_MDL158` / `CGC_MDL159`
正好覆蓋 `11_PanoramaScan` 與 `12_MatrixConsole` ——兩個最久沉默的步。

### 順帶收掉一句每步都念的話

批617 我替心跳加了「是不是本步寫的」判準,判不是就印
「內層心跳是本步**開始之前**寫的(上一跑留下的),不採用」。

看起來很誠實——直到逐字稿貼回來:**十五步裡只有第 13 步會寫心跳**,
其餘十四步每秒印一次這句話,而它講的是一個跟本步完全無關的檔案。
誠實的話講在不相干的地方就是噪音。v0111 改成沒來源時一句帶過:
`(時間粗估;本步沒有內層進度來源)`。

---

## 二 · 41 盞紅燈沒有一盞是真的

同一段逐字稿裡,`09_GovAudit` 的收容正本零觸碰閘:

```
工作站   (夾 58 · GREEN  5 · RED 41 · UNKEPT 11 · NODATA 1)
容器     (夾 58 · GREEN 46 · RED  0 · UNKEPT 12 · NODATA 0)
```

**一棵樹不會有兩個真相。**41 個收容正本不可能在他不知情的情況下同時被改。
所以紅的是尺。

根因:`_sha256()` 讀的是**原始位元組**,而 Windows 上 git 依 `core.autocrlf`
把 LF 換成 CRLF——同一個檔多出「行數」個位元組,sha 當然不符。
`.gitattributes` 目前只對四棵子樹寫了 `-text`,理由欄寫得很清楚:

```
# VTR subsystem: manifest hashes raw bytes - checkout must be byte-exact (no CRLF conversion)
VeritasIntelligenceAnalytics/functional*modules/VTR/** -text
```

**`references/intake/**` 不在裡面。**

最刺的是:這件事 **`CGC_MDL159` 在批546 就解過**(檢⑪「行尾無關」,
raw 不符就比 LF 正規化後的),那個修法躺在隔壁一支引擎裡 **73 批**沒人帶過來。
**一個病根修在一支引擎上,不叫修好。**升為 **L93 跨機器判定不一致律**。

### v0108

四態變五態。raw 不符時再比 `CRLF→LF` 正規化的 sha;對得上判 **EOL**,對不上才是 RED。
嚴重度次序:`RED(真被動過) > UNKEPT(原件沒留) > EOL(只差行尾) > GREEN`。

沙盒三條路全走過(L83:半條路不算跑過):

```
原樣 GREEN 1 · 只換行尾 EOL 1(不是紅)· 真的改字 RED 1
```

容器實樹不變(`GREEN 46 · RED 0 · UNKEPT 12 · EOL 0 · NODATA 0`),自測 22 檢 → **23 檢**。

### 根治那一行,是操作員的手

真正的根治是在 `.gitattributes` 補:

```gitattributes
VeritasIntelligenceAnalytics/supportive*modules/references/intake/** -text
```

**我沒有代做。**那一行會讓他下次 checkout 重新正規化一整片檔——
那是動他磁碟的事,裁定權在他。引擎這邊先把假紅停掉。

---

## 三 · 一個我自己排錯的流程(順手記下來)

全格子第一次跑出 `FAIL 1`:VCGC 中央控管台檢 ⑬ 報 `ACTIVE 5410/5412`。
第一反應是去翻 MDL149 的碼——**碼一個字都沒問題**。

5412 − 5410 = 2,正好是這一批新加的兩支函式(`_sha256_lf`,以及自測沙盒裡的巢狀 `_mk`)。
檢 ⑬ 是拿**冊**比**樹**,冊還沒同步,它當然報缺 2。跑一次 `registry-sync --apply`
(`新 2`),那一站當場轉綠。

批618 沒踩到純粹是運氣:那一批新增的檔剛好都落在元件冊掃不到的兩個盲區(LL187),
沒有一支新函式進得了冊,分母沒變。

`Invoke-VIA-AllInOne` 的步序本來就是對的(`08_RegistrySync` 排在 `13_SelftestGrid` 前面)
——**錯的是我在容器裡自己排的流程**。往後固定:

```
registry-sync --apply  →  全格子  →  via-regen --apply  →  commit
```

---

## 登錄

* 法 91(**+L93 跨機器判定不一致律**)· 課 191(+LL188/LL189/LL190/LL191)· 台帳 1217
* 新件:`launchers/Invoke-VIA-AllInOne-v0111.ps1` ·
  `supportive modules/registry/CGC_MDL164_GovernanceCompletenessAudit_v0108.py` ·
  `supportive modules/registry/CGC_MDL064_SelftestGrid_v0373.py`(站名 22→23 檢;站數不變 253)
