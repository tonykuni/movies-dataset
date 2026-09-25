# 批652 · 我補了兩個口,而那支引擎有四個口

## 你的實跑把我批651 的修打回來了

```
[VRN_ENG085 v0105] run · OK · 105 份 · 一致 1093/1123 = 97.3%
     14 次 · ENG085=標題/H1 vs 分析器=paragraph/段落  例:'M'
```

**一個數字都沒動。** 內容閘上線了,16 塊 `'M'` 一塊都沒轉。

去數才知道:ENG085 有 **4 個** `add("標題", …)`。我批651 補了 **2 個**。

補兩個漏兩個,等於沒補。

### 合成重現真正的那條路

```python
restore({"heads": [{"text": "M", "size": 34, "level": "H1"}],
         "body": "M台積電(2330)第三季展望\nMorgan Stanley 認為這是一句正文。"})
```

無閘的輸出:

```
標題/H1  'M'                      ← LAYOUT 標的 H1,原本黏在行首,切出來
本文/句  '台積電(2330)第三季展望'
標題/H2  'M'                      ← 同一條路,降 H2
本文/句  'organ Stanley 認為這是一句正文。'   ← ⚠ M 被切走了
```

**logo 字母黏在行首被切出來** —— 那就是你那 16 塊。
而且順手照出第二個傷:`Morgan Stanley` 的 `M` 被當標題切走,本文變成 `'organ Stanley…'`。
字沒少(保全率照樣 100%),但**一個真的字母被搬到別的列去了**。

### 兩道閘

| | 擺哪 | 治什麼 |
|---|---|---|
| ① | `add()` —— **唯一出口** | 判成什麼。現在的 4 個口、以後新加的口,都一定經過 |
| ② | 切之前 | 要不要切。頭不夠格就**整行不切**,`Morgan Stanley` 留完整 |

有閘之後:

```
本文/句  'M'                                  ← 字級×粗體像標題,但內容不夠(有效字元 1 個)
本文/句  'Morgan Stanley 認為這是一句正文。'      ← 完整
```

### 而且這次尺是咬得住的

```
裝回兩道閘 → 34 檢 OK 34 · FAIL 0
拿掉兩道閘 → 34 檢 OK 33 · FAIL 1   ← ㉞ 當場紅
```

批651 我第一版的端到端檢,拿掉閘**也照樣 OK** —— 那是一盞不會亮的燈。
換成真正那條路(logo 黏行首)之後才咬得住。 → **LL289**

容器 81 份:v0104 / v0105 / v0106 **逐行輸出相同**(保全 100% · 二尺量到 73 · 表格 8 列)=零回歸。

---

## 那盞 CRLF 紅燈:閘問出來的答案是對的

你的機器回報:

```
[問 git] core.autocrlf=true
         check-attr → CHANGELOG.md: text: unset · git 看得見被改過的 0 件
[RED] 位元鎖生效,但 git 認為工作副本是乾淨的 …
```

我照這個局面在沙盒**重現出來了**:

```
git status 看得見:0 · check-attr: text: unset      ← 跟你機器一模一樣
批650 那一道 git checkout HEAD -- pkg  → a \r \n    ← 重現失敗
閘給你的 rm --cached + checkout        → a \n       ← 有效,status 乾淨
```

**那一道還沒被你下過。** 下了就會轉綠。

但 v0108 有個我自己的毛病:治法第一行永遠印批650 那一道(在這個局面**已證實無效**),
下面才印有效的那一道 —— 等於自己製造一次白跑。v0109 改成**治法跟著實測走**。

---

## 全景對照:那個 session 的東西,該拿哪一塊

你指的 `session_01FQMN8uBxreDrzmDUpPrXTG`(單一引擎整合與獨立運作)在**另一個倉庫**
`tonykuni/VIA-VDF-VRN`,分支 `claude/charming-brown-2qaooh`,PR #32 已併。

核心件是 `VIA_CentralGovernance.py` —— **6,577 行**。逐條量對照:

| 那邊的能力 | VIA 母系統的正主 | |
|---|---|---|
| Python A01–A25 加速覆蓋 | `CGC_MDL156_VIAAcceleratorControl_v0109` | 已有 |
| base／via_* 環境總管 | `CGC_MDL135_EnvGovernance_v0113` | 已有 |
| PowerShell 多輪 AST 自修 | `CGC_MDL146_PSRepair-AST` | 已有 |
| 唯讀全景審計＋計畫 | `CGC_MDL158_VIAPanoramaAuditRepair_v0103` | 已有 |
| 中央治理 Console | `CGC_MDL139_InputConsole_v0110` + `MDL140` | 已有 |
| 聯邦索引與呼叫圖 | `CGC_MDL128_SystemCharter_v0101` | 已有 |
| 引擎功能編號權威 | `VCGC registry-sync`(活元件 5,623) | 已有 |
| 一鍵 launch 走完整循環 | `via-run25`(九站) | 已有 |
| 三鏡競速 | 母系統 83 支檔案提到 | 已有 |
| 當機恢復 checkpoint | 母系統 330 支檔案提到 | 已有 |

> **整包導入 = 專案史上最大一次九頭龍。不做。**

那個 session 真正**新**的只有一件 —— 就是它標題講的那件:

> **引擎能把自己打包成 byte-identical 的單檔交付**(PR #31 / #32)

而它對得上 VIA 一個反覆發生的真痛點:

- 批397 雙副本律 —— 你的 profile 點源的是另一個副本
- 批629 「你跑的是舊版」這句話該由工具講
- 批649 `via-vdfcov roster` 在你機器上 invalid choice —— **不是引擎壞,是我貼指令時你還沒 pull**

**採不採、放進哪一支引擎,裁定權在你**(比照 LL90 同義字)。
本批只出對照表,**正典一個字都沒動**。

---

## 你這邊

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
git rm --cached -r -q -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
via-run25
```

第二三道是沙盒重現你那個局面後驗過的,不是猜的。
跑完之後 `template` 那盞會綠,ENG085 的 16 塊 `'M'` 應該會從分歧統計裡消失。
