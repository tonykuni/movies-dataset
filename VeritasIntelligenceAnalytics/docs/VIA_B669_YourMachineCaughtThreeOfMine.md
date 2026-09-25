# 批669 · 你的機器照出我引擎三個錯

## 你貼回來的

```
VIA 六域現況矩陣 · 主機 TONY-NB · python 3.13.7 · VIA_ENV_ROOT=C:\Users\tonyk\envs
GREEN 25 · RED 3 · GATED 0 · NODATA 1 · ABSENT 4 → RED
```

逐列看 —— **其中三件是我這支引擎的錯,不是你樹的錯。**

---

## ① 家族境 python 三格 ABSENT,但 `via-rungate` 找得到

```
via-state    家族境 python · vrn   ABSENT   VIA_ENV_ROOT=…\envs 下找不到 via_vrn_*
via-rungate  GREEN vrn  python=C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe(OK)
```

**同一台機器,兩把尺,相反的答案。** 而錯的是我這把。

我的子路徑清單只試了三種擺法:

```python
("python.exe", "bin/python", "python")     # conda 與 POSIX 的擺法
```

**漏了 Windows venv 的 `<env>\Scripts\python.exe`** —— 而你的就是那一種。

補齊六種:`Scripts/python.exe` · `Scripts/python3.exe` · `python.exe` ·
`bin/python` · `bin/python3` · `python`。

自測⑳ 拿真的目錄結構咬:建一個 `via_vrn_312\Scripts\python.exe` 出來,必須判 GREEN。

> L93 說「先疑尺不疑樹」。這次疑對了 —— **真的是尺。**

---

## ② 三盞 RED 全指向同一份 1.3 天前的存證

```
格子總判        RED  229/252  FAIL 20   GRID_20260919_191156.json  齡 1.3 天
VDF 格子站燈    RED  13/14    FAIL 1    (同一份)
VRN 格子站燈    RED  9/10     FAIL 1    (同一份)
```

那份存證是 **1.3 天前**跑的 —— 而那之後你拉了 **5 批**。
它裡面的 `FAIL 20`、`252 站`,講的是**另一棵樹**。

這是批668 那條的另一個長相:

| 批 | 長相 |
|---|---|
| 批668 | 在格子**裡面**跑 → 讀到的是上一輪 |
| **批669** | 存證比**現在的樹**舊 → 講的是另一棵樹 |

兩者都是**拿別的時候的結論當成現在的**。

改法:存證 mtime 對 HEAD commit 時間。存證比 HEAD 舊 → **NODATA**,並寫明差幾天 +
修法(`via-selftest` 讓存證追上這棵樹)。

---

## ③ `缺 talib` 判 NODATA —— 那是合律不是缺料

**L50 是第一條:「TA-Lib 禁用,QuantGuard 是唯一正主」。**

talib **缺席才是對的**。我把它報成「缺」,等於推你去裝一個被禁的套件。

所以這一條不是豁免,是**方向相反的判準**:

```
talib 缺席  →  合律,不進分母(L57:合律不該被講成缺陷)
talib 在場  →  **RED**「竟然裝著」+ 引 L50 原文
```

---

## 量到的

```
MDL169 廿二檢   OK 22 · FAIL 0
  ⑳ Windows venv Scripts\python.exe   → GREEN
  ㉑ 存證比樹舊                        → 判得出來且講得出差幾天
  ㉒ L50 被禁庫方向相反                → 缺席合律 · 在場違律
```

---

## 你那邊剩下的兩件,是真的

| 列 | 狀態 | 這是真的缺 |
|---|---|---|
| `庫整併稽核存證` | ABSENT | `VIA_Reports/libconsol/` 沒跑過 |
| `其中帶 --selftest` | 180/931 = 19.3% | 沒有自測的工具,壞了只有用的時候才知道 |

第二個不是這一批的範圍,但它是個真數字 —— 931 個支援性工具,**只有 180 個有自測**。

---

## 一句總結

你貼一次實錄,我改三個判準。**兩把尺量同一件事給出相反答案的時候,先查我那把。**
