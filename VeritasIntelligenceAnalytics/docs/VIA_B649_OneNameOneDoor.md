# 批649 · 一個名字只能有一扇門

## 你的令

> INTEGRATE INTO ONE PS CODE WITH 25 加速器去完成以上全部　動態進度條及百分比

## 做出來的東西:`via-run25`

一個指令跑完批643–648 立的八站。容器實跑:

```
=== via-run25 · 批643–648 全鏈 8 站 · 25 加速器(VIA_ACCEL=1)===
  [加速器] 25 格 · 快取 12/88 庫 · 執行緒預算 3
  [SKIP  ] 首頁抽取(ENG072)      沒給 --in <研報夾>;**不拿舊 sidecar 冒充一次新抽取**
  [GREEN ] 本文還原(ENG085)      0.7s
  [GREEN ] 結構入庫(ENG073)      6.2s
  [GREEN ] 一題四點文摘(ENG080)    1.8s
  [NODATA] 名冊×價表涵蓋(ENG090)   0.3s   ← 批644 量到的 TWSE 整所缺席,還在
  [GREEN ] 雙橋第二層(清掃器)       16.4s
  [GREEN ] 正典 TEMPLATE(MDL160) 0.2s
  [GREEN ] U/I 面與 L100 邊界     1.1s
  [計] GREEN 6 · RED 0 · NODATA 1 · ABSENT 0 · GATED 0 · SKIP 1 · 27s
  [律] 同意閘未代設(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手)
```

### 進度條**沒有新造**

樹上本來就有兩條,再造第三條就是九頭龍:

| Id | 誰 | 怎麼動 |
|---|---|---|
| 12 | `Show-VIAAccel20`(既有) | 25 加速器點亮 |
| 13 | `Invoke-VIAPython`(既有) | 單站脈動——**不知道總長,所以 30 秒一輪** |
| **11** | **本批新增** | **鏈層真百分比**——站數已知,這一條的比例是真的 |

### 依賴律不偷跑

`digest` 要 `structdb` 先綠。前置沒綠就 **SKIP 並指名原因**,不假裝跑過(L83)。
彼此獨立的盤點站互不牽連——一站紅不拖垮其他站。

### 編排器不開格子站

`via-entry` 立的規矩:編排器只配**冊 + 梭**,不開站。
站屬於它呼叫的那些引擎——編排器自己沒有可以獨立判的燈(LL199 例外)。

---

## 但這一批真正該講的,是順手照出來的另一件事

做完整合,我照慣例查「via-run25 這個名字有沒有人用過」。
順手把整本冊的函式名排一次序——**跳出三個重複**。

於是寫了 `CGC_MDL157 shadow`,拿它掃自己的冊:

```
v0227(批647 之前)  被吃 2
v0228(批647,我加的) 被吃 3
```

PowerShell 的 `function global:X` 寫第二次,是**後定義無聲覆蓋前定義**。
沒有警告、沒有 rc、格子照綠、梭照在、樹上的檔照在:

| 名字 | 前定義(死) | 後定義(活) |
|---|---|---|
| `via-ssot` | **`CGC_MDL115_SSOTRegexDict`** | `CGC_MDL155` |
| `via-panorama` | `launchers\Invoke-VIA-Panorama-v*.ps1` | `CGC_MDL158` |
| `via-ui` | `CGC_MDL130_UIBridge` | `CGC_MDL160 template`(**批647,我**) |

第一列那支,正是你一再點名的「**優先 SSOT REGEX**」。
它樹上一直在、格子站一直綠,但從 批535 起,冊上沒有門。

第三列是我自己造的。批647 我要給正典 TEMPLATE 一個短令,
挑了 `via-ui` 這個名字——**而 378 行早就有一個 `via-ui`**。我沒查就寫了。

> **LL279 說「做好的東西站在系統外面,跟沒做一樣」。這次發生在冊自己身上。**

### 最難看的一層

守「唯一入口」的就是 MDL157 自己。它讀冊用的是:

```python
def function_bodies(text) -> dict[str, str]:
    return {m.group(1): m.group("body") for m in pattern.finditer(text)}
```

**dict 後者覆蓋前者。**
負責守唯一性的那把尺,正好是全樹唯一看不見重複的那把(LL257 檢比到自己)。

---

## 這盞燈判的是什麼

不判「有沒有被同名覆蓋」——那會逼人去刪已經推出去的一千四百行裡的死定義。
判的是 **被覆蓋的那支引擎還到不到得了**:

```
[RESCUED] via-panorama  屍體指 Invoke-VIA-Panorama-v*.ps1  另有門 via-panorama-run
[RESCUED] via-ssot      屍體指 CGC_MDL115_SSOTRegexDict_v*.py 另有門 via-ssotregex
[RESCUED] via-ui        屍體指 CGC_MDL130_UIBridge_v*.py   另有門 via-uibridge
→ 被吃 3(其中失門 0)
```

三扇新門 + 三個梭(`via-ssotregex` / `via-uibridge` / `via-panorama-run`)。
活著的那三支名字**一個都沒動**——你的手已經記住它們了。

### 尺自己被驗過三次

1. **合成負控**:造一本「被吃且無門」的假冊 → 抓到 ORPHAN;造一本「被吃但另有門」→ RESCUED;乾淨冊 → 0。
2. **連字號族**:第一版正則只認 `_v*`,漏掉 `Invoke-VIA-Panorama-v*.ps1`,
   於是 via-panorama 明明有門卻被判 ORPHAN。**尺看不見不等於樹上沒有**(L93)。
3. **註解不算門**:第一版用整段函式本文比對,一句**提到引擎樣式的註解**就被算成一扇門
   (via-run25 的說明文字當場「救」了 panorama)。註解跑不動任何東西 —— 那是假綠。

### 還有一件:MDL130 連格子站都沒有

回頭查才發現,`CGC_MDL130_UIBridge` 的十一檢**真跑得起來**(OK 11 · FAIL 0),
但它從來沒有一個格子站。**冊上沒門、格子上沒站**——紅了也沒人會知道。
格子 v0405 補上那一站。

---

## 我自己那支新令的三個洞(都是真跑才現形)

| # | 症狀 | 根因 |
|---|---|---|
| ① | `via-run25 --list` **不列站表,把八站全跑了一遍** | `ConvertTo-VIACleanArgs` 回傳陣列,PowerShell 在只有一個元素時拆成純字串;`$a.Count` 還是 1,`$a[0]` 卻是第一個**字元** `'-'`。兩個 token 以上反而正常,所以這洞只在單旗標時張開 → **LL284** |
| ② | `--skip a,b,c` 報「不認得的參數 b c」 | 逗號清單在呼叫端就被當陣列傳進來,`ConvertTo-VIACleanArgs` 又刻意攤平(那是為 `--family vrn,vap` 立的)。旗標後面是 N 個 token,不是一個 |
| ③ | `--only nosuch` 篩到**零站**,迴圈一次沒跑,計數全 0 → **印 GREEN** | 一站都沒跑,憑什麼綠 |

三個口的治法一樣:**誠實停**(rc=1)+ 把可用站名印出來(L92)。
連「只列不跑」的 `--list` 也自己接 rc=0——不接就留著上一個令的 rc 騙人(LL207)。→ **LL285**

一個「只想看看計畫」的旗標,實際效果是「執行全部」。
這種洞不會在寫的時候看見,只會在**真的打那一行**的時候看見。

---

## 立的律

**L101 —— 一個名字只能有一扇門;被同名後定義吃掉的那支,必須另開一扇自己的門。**

判的不是「有沒有被覆蓋」,是「被覆蓋的那支還到不到得了」。
守門人 `via-entry`→`CGC_MDL157 shadow`,上線第一件事是拿它掃自己的冊(LL231)。

## 你這邊要做的

```powershell
cd C:\...\movies-dataset
git pull origin claude/via-envmanager-governance-7cls8h
via-run25 --list      # 先看站表
via-run25             # 跑全鏈(動態進度條 + 百分比)
via-ssotregex         # 你點名的 SSOT REGEX,現在到得了了
```

`via-run25` 需要觸網的站一律 GATED 並印出該設什麼——
**`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 這一批一樣沒代設,那是你的手。**
