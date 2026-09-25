# 批575 · 兩支獨立工具的覆蓋 —— 「是不是沒按我要求」的量測答案

操作員原話:**「是不是沒按我要求所有PY檔案裝這個加速器 所有VDF檔案沒有裝這網路工具
沒我允許不可以改 POWERSHELL 加裝30個加速EXTENSIONS. 政策化」**

量測 2026-09-17 · `CGC_MDL156_VIAAcceleratorControl_v0105`(30→35 檢,GREEN 35/35)
**本批零 PowerShell 改動 · 零套件安裝**

---

## 一、結論:你問對了,而且問到的是**尺**的問題

| 問題 | 舊尺怎麼回答 | 真答案 |
|---|---|---|
| 所有 PY 都裝加速器? | 「活樹尾版 807/807,100%」 | 100% 的**分母沒攤開**。全樹 3411 支、尾版 1571 支、具名豁免 1398 支,舊尺一個字都沒講 |
| 所有 VDF 都裝網路工具? | 「網路缺 0」 | 那是**負向尺**(沒人生呼叫)。換成批115 原文的**正向尺**(每支都要掛):**VDF 活件 64 · 掛橋 61 · 缺 3** |

**缺的那三支是我自己寫的**:`VDF_ENG088`(批569)· `VDF_ENG089`(批569)· `VDF_ENG090`(批570/573)。
它們不 `import` 任何網路庫,而舊尺的條件是「**已經 import 網路庫才問你有沒有掛橋**」——
所以它們從出生到現在,從來沒有被問過。

> 尺放在那裡不是為了讓報告好看,是為了讓新寫的東西一出生就被問到。

---

## 二、加速器:分母現在攤開了

```
全樹 3411 支
 = 尾版 1571(第①檢分母,全問,加速器橋覆蓋 100%)
 + 非尾版舊版 1840(尾版律:同家族只問最後一支)
具名豁免 1398 支 / 18 類(其中 594 支同時是尾版,尺仍然問了它們——寧可問多)
**不明原因沒問 0**
```

18 類豁免每一類都寫在 `_TREE_EXEMPT` 裡並附理由(收容件正本零觸碰 / 退役墓園 / 第三方虛境 /
批180 凍結群 / 產物夾 …)。**名單要能被讀、被質疑、被改**,不是一個口頭說「那幾支不算」的數字。

---

## 三、網路工具:三支補掛完成

用 `via_bridge_sweeper_v0101` **自己的注入器**補掛(位元與批115 當年注入的 807 支一致,graceful 零行為變更):

| 引擎 | 作法 | 自測 |
|---|---|---|
| `VDF_ENG089_IncrementalFetchGate_v0100` | 就地補掛 | 16/16 |
| `VDF_ENG090_DataCoverageGate_v0102` | 就地補掛 | 19/19 |
| `VDF_ENG088_ConsensusFusionBridge` | **v0101 新版**(尾版律) | 7/7 |

ENG088 補完當場紅一檢:它的第①檢禁「`importlib` 這個字出現在本檔」(用來證明「只定位不執行收容件」),
而網路橋塊正好用 `importlib` 去載**正典網路工具**。**舊尺是代理指標,生的是假紅**——
收窄成「不得拿 importlib 去載**收容件**」(排除網路橋塊)才是它本來要講的話。
因為動到自測尺,ENG088 走尾版律開 v0101,v0100 原地不動;
短令 `via-consensus` 用 `Get-VIANewest` 自動接到新版 = **零 PowerShell 改動**。

---

## 四、你上傳的兩支工具:沒有漂移

| | 上傳正本(LF 正規化) | 庫內掛載本 | 結果 |
|---|---|---|---|
| `VeritasCeleritas.py` | `4ce66aa9f763` · 237,062 B | `supportive modules/VeritasCeleritas.py` | **完全相同** |
| `VeritasAegisNexus.py` | `f5f81f04479d` · 203,952 B | `supportive modules/network/VeritasAegisNexus.py` | **完全相同** |

與批345 凍結原件的唯一差異 = 批102 注入的 14 行 `[VIA:ACCEL-BRIDGE]` 塊,和 b345 manifest 記載一致。
收容於 `supportive modules/references/intake/VIA_TwoTools_b575/`(byte-exact,CRLF 原樣,只收不掛線)。

> 自我更正:我第一次拿**裸 md5** 比,判成「上傳比庫內任何一份都新」——那是錯的,差別只是 CRLF/LF。

---

## 五、唯一的真差異:L50 talib 曝險(**等你裁定**)

`SUP_MDL737` 的解析順序:

```
CEL_CANDIDATES = ['VeritasCeleritas.py',
                  '50_Protection_Acceleration/VeritasCeleritas.py',
                  'accelerator/VeritasCeleritas.py']   ← L50 合規的那一份排第三
```

- 執行期實際載入 **第一名** `supportive modules/VeritasCeleritas.py` —— 它帶 `talib = _si("talib")` 惰性路徑與 `_TalibStub`
- `accelerator/VeritasCeleritas.py` 把 talib 整條換成 QuantGuard(**L50 合規**)——但排第三,**永遠解析不到**

本境 `find_spec('talib')` 找不到 → 未活化,所以判 **PENDING_OPERATOR 不判紅**
(判紅會變成你清不掉的紅燈,而清它需要你的裁定;LL129)。
**若哪天工作站裝了 talib,這一檢會立刻轉紅** —— 因為那時候是真違規。

一行修法:`CEL_CANDIDATES` 把 `accelerator/` 提到第一(改 `SUP_MDL737`,**不動兩支工具本體**)。
批345 不可動律 + LL90:**裁定權在你**。

---

## 六、政策化(三條律入冊)

| 律 | 內容 |
|---|---|
| **L68 尺不得比律窄** | 正向令的分母就是令的分母;要縮只能用**具名豁免**(寫在碼裡、附理由、報告印出「全樹幾支/問了幾支/沒問幾支落在哪類」);「不明原因沒問 > 0」= 紅。**負向尺不能當正向令的證據** |
| **L69 VDF 全檔掛網路工具** | 每支 VDF 活件尾版都要帶 `[VIA:NET-BRIDGE]`,不是「有 import 才掛」。新引擎**出生就要掛** |
| **L70 PowerShell 與套件都是操作員的手** | 未經**逐次**許可不得改任何 `.ps1`、不得加裝任何加速 extension/套件。新引擎需短令 → 先做成既有短令的新動詞或新版檔(`Get-VIANewest` 自動接);非改不可時寫成一次貼交給操作員。**此律優先於功能註冊七處的第②處** |

教訓 `LL130`。

---

## 七、怎麼驗

```powershell
via-accel selftest        # 35 檢:③分母攤開 ④VDF正向尺 ⑤解析順序 ⑥L50曝險 ⑦正本指紋
via-accel-check           # 覆蓋閘 + 控制面
via-consensus             # 自動接到 ENG088 v0101
```

## 八、關於「加裝 30 個加速 EXTENSIONS」

我把你那句讀成**禁令**:沒你許可不改 PowerShell、不加裝。所以本批一行 `.ps1` 都沒動,
一個套件都沒裝,並把它寫成 L70。

如果你的意思其實是「**去把 30 個加速 extension 裝起來**」,那需要你一句話,
而且照 L70 與既有的不代裝律,**安裝指令由你貼**(目前 PS 加速器名冊是 25 項:
`VIA_PS_Accelerators_25_Roster_v*.ps1`)。你說要哪 30 個、或要我先列出 25→30 的差集,我就去列。
