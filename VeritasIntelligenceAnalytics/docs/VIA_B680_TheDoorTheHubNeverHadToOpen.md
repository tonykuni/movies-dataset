# 批680 · 樞紐一個位元都沒改,卻已經過閘了

批678 量到一句話:**讀券商冊的活尾版 10/10 都沒走過拒絕閘**。
操作員批413 的裁定(「大陸券商刪除」「去摩通」)立了、留痕了,
可是真正在讀研報券商名的那幾支,從來沒有經過它。

批679 把陸券從冊上刪乾淨了 —— 但那是**把料拿掉**,不是**把門接上**。
料拿掉之後,下一個人只要把一家陸券加回冊上,它就會照樣被解析出來,
而且沒有任何一盞燈會紅。這一批接的是門。

## 一 · 先量,才知道門該裝在哪

`SUP_MDL749` 的 `broker_of()` 有**一個出口**,而且那個出口是**委派**:

```python
def broker_of(text, filename="", ticker=None):
    mod, why = matchers()                      # ← mod 就是 VRN_ENG086
    canon, how = mod.safe_broker_ev(text, veto=veto)
    if not canon and filename:
        canon, how = (mod.safe_broker(filename), "檔名") ...
    return canon, how
```

所以門裝在 **ENG086 的 `safe_broker_ev()`**,樞紐**不必升版**就一起過閘。

這件事不只是省工 —— 它是**必須**的:`SUP_MDL749_VRNFieldRuleHub_v0111.py`
**已經被側線 PR #53 佔走**(他們在同一天加了增補冊讀冊口)。
我從自己的 v0110 造 v0112,會讓他們那個讀冊口在尾版律下**整個消失**。
LL334(版號是跨分支的共用資源)立下來才幾個小時就兌現了一次。

## 二 · 門長什麼樣

一段可複用的 `[VIA:DENY-GATE]` 區塊,照樹上既有的 `ACCEL-BRIDGE` 慣例寫:

```python
def _via_deny_reason(*values) -> str:
    """任何一個值在拒絕清單上就回一句因由;都不在(或疊加層缺席)回空字串。"""
```

三條規矩:

* **名單不在裡面。** 它在疊加層的 `deny_keys`(操作員批413 那一份)。L30 一個出處。
* **疊加層缺席 / 讀不到 / 任何例外 → 原樣放行。** 缺件不是壞掉,而且零行為變更。
* **被拒回 `(None, "拒絕:…")`,不是靜默 `None`。** 查無與被拒是兩件事 ——
  靜默回 `None` 會讓下一個人以為「冊上沒有這家」,然後跑去把它加回冊上。

接上的兩支:

| 支 | 出口 | 版號 |
|---|---|---|
| `VRN_ENG086_FirstPageLogicBridge` | `safe_broker_ev()` / `safe_broker()` | v0109 → **v0110** |
| `SUP_MDL015_VISVRNBrokerAliasFullList` | `def_normalize_broker_name()` | v0100 → **v0101** |

`SUP_MDL015` **從來沒有自測門**,所以格子上一直沒有它的站(LL317 沒有自測門的支不准敲)。
接閘的同時把門補上(六檢)並送上站 —— 沒有站的支,改壞了也不會有人知道。

## 三 · 一個永遠不觸發的閘等於沒有閘

批679 已經把冊清乾淨了,所以**今天這個閘在真跑裡一次都不會觸發**。
那就必須用**正控**證明它咬得住(LL89):

```
ENG086   解出被拒機構 → (None, '拒絕:拒絕清單:…')      解出 YUANTA → ('YUANTA', '文內')
MDL015   把被拒機構塞回表裡 → 解不出來                    元大 → Yuanta
樞紐     broker_of() 同樣被擋 —— 而它一個位元都沒改
```

合法券商逐個驗過沒退步:`元大→YUANTA` · `凱基→KGI` · `高盛→GOLDMANSACHS` ·
`里昂→CLSA` · `國泰證期→CATHAY` · `中國信託→CTBC`。

## 四 · 兩把尺,分兩欄各自報

`CGC_MDL176` 的 `gate_bypass()` 量的是**檔案裡有沒有那幾個字**。
它會把樞紐判成「沒過閘」—— **判得沒錯,它量的就是文字**,看不到委派。

所以另開一欄 `gate_behaviour()`:**真的跑一次**正控,回 GREEN / RED / NODATA。

```
文字尺   過閘 3 / 10
行為尺   GREEN · 樞紐委派給 VRN_ENG086_…v0110,而那一支有閘
```

**兩把尺不相加**(LL327)。混成一個數字,讀的人就分不清「改了檔」跟「行為對了」。

## 五 · 我在這一批犯了三個錯,三個都被自己的閘擋下來

### ① 「不准出現 X」的檢,天生會把 X 抄進來 —— 第三次

要證明拒絕閘會咬,就得餵它一個被拒的名字。我**三次**都直接把「廣發」打進檢裡 ——
而那就是又抄了一份名單,陸券清除閘三次都當場把我判成「還帶著活的陸券解析資料」,**三次都判得對**。

出路只有一條:**探針值從那一份名單當場取**。

```python
_probe = (_via_deny_sample(1) or [""])[0]      # 從 deny_keys 取第一條
```

順帶好處:操作員哪天改了名單,這個正控會自動跟著改,不會變成釘住舊名單的殭屍。

### ② 改尺的時候把尺改鬆了

`verify()` 原本只看 `#`,所以我寫在 **docstring** 裡「為什麼不可以抄名單」那句話,
被自己的尺判成資料。尺的盲點,不是樹的問題 —— 所以修尺。

但第一版修法是「這個字在某個 docstring 裡出現過就整份當散文」,
**負控當場抓到**:一個 docstring 提到廣發、字典裡也有廣發的合成檔,被判成「只有註解」。
**那是把尺改鬆了,而不是改對。**

改成用 AST 取 docstring 的**行號範圍**逐行判,四態全對:

| 情況 | 應該判 |
|---|---|
| 只有 docstring 提到 | 散文 |
| 只有 `#` 註解提到 | 散文 |
| 只有資料裡有 | **資料** |
| docstring 提到 **而且** 資料裡也有 | **資料** |

> 改尺之後一定要證明它沒有變鬆,不然「照出來的變少」會被讀成「問題變少」。

### ③ 自測探針寫進活樹

四態控第一版把探針檔寫進 `functional modules/VRN/`,跑完雖然 `unlink`,
但中斷一次就會留在樹上 —— 註冊稽核當場點名「未登 `_b680_selftest_probe`」。
**自測不准跟活樹共用地盤**(LL319)。改成 `verify(root=)` 可指定掃描根,自測掃暫存夾。

另外還有兩個小的:`__future__` 匯入必須緊接 docstring(我的區塊插到它前面,整支解析不過);
`relative_to(VIA)` 在掃暫存夾時會炸(基準要跟著掃描根走)。

## 六 · 順手照出一條停在舊裁定的期待值

`SUP_MDL015` 的 smoke 案例 `CLST-6669 → CLST`,**v0100 接閘之前跑就已經是紅的**。
根因是**批541 操作員裁定「CLSA = CLST 是同一家(里昂)」**,冊上早已併成 CLSA。

這支從來沒有自測門,所以這個紅躺了很久沒人看見。
改**期待值**不是改尺:裁定變了,期待值就該跟著變(LL332 同型)。

## 七 · 沒做的,以及為什麼(L87)

* **沒有碰 `SUP_MDL749`** —— v0111 被側線 PR #53 佔走(見第一節)。它的行為已經過閘了。
* **還有 7 支沒過閘**:`VRN_ENG062` · `vrn_report_digest` · `VIS_VRN_BrokerAlias_{Compatibility,Extension}` ·
  `VIS_VRN_PDFTextLayerFallbackPlan` · `VIS_VRN_Q1_AliasRoutePatch` · 樞紐(文字尺)。
  它們各有各的出口形狀,一批接兩支、每支配正控,比一次接七支然後沒有一支驗過要好。
* **沒有登記任何 `via-*` 短令** —— L70,這一批的令裡沒有 PS。

## 八 · 收

| 檔 | 是什麼 |
|---|---|
| `functional modules/VRN/VRN_ENG086_FirstPageLogicBridge_v0110.py` | 接拒絕閘 · 廿二檢 |
| `supportive modules/70_VRN_Rules/SUP_MDL015_VISVRNBrokerAliasFullList_v0101.py` | 接閘 + **補自測門** · 六檢 |
| `supportive modules/registry/CGC_MDL176_SynonymUnion_v0100.py` | +`gate_behaviour()` 行為尺 · 卅一檢 |
| `supportive modules/registry/CGC_MDL177_ChinaBrokerPurge_v0100.py` | `verify()` 認得 docstring + 可指定掃描根 + 四態控 · 卅七檢 |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0433.py` | +`SUP_MDL015` 站 |

> **LL336:「不准出現 X」的檢,天生會把 X 抄進來。** 探針值要從那一份名單當場取,不是打字打進去。

> **LL337:改尺之後要證明它沒有變鬆。** 照出來的變少,可能是問題變少,也可能是尺變鈍了 —— 這兩件事看起來一模一樣。
