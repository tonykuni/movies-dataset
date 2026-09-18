# 批576 · 畫面統一:先把尺自己修乾淨,再立頁頭正本件

## 一、自我更正:我報給你的「106 張 · RED 43」是灌水的

批575 我剛立了 **L68(尺不得比律窄,分母要攤開)**。批576 拿它回頭量自己的 U/I 閘,
第一個被抓到的就是我自己:

| 頁家族 | 被數了幾遍 | 為什麼 |
|---|---|---|
| `VIA_UI_ReportDigest.html` | **17** | 每個 digest 跑次夾各一份 |
| `VIA_UI_Hub.html` | **9** | v0100–v0108 全算 |
| `VIA_UI_VapDeck.html` | 6 | v0100–v0105 |
| `VIA_UI_GovDeck.html` | 5 | v0100–v0104 |
| `VIA_UI_CentralGovernanceConsole.html` | 2 | 兩個夾 |

套上我們**早就有的尾版律**之後,真數字是:

```
全掃 106 張  →  **尾版律後 72 張 · GREEN 39 · YELLOW 15 · RED 18**
```

> 分母灌水和分母縮水一樣傷:縮水讓人以為都做完了,**灌水讓人以為做不完** —— 兩種都會讓人不去修。

## 二、18 張紅的原因高度集中,而且全在頁頭

```
zero_cdn 9（+1 併發） · zero_popup 4 · viewport 5 · lang 2
```

每一支產頁引擎各自抄一份 `<head>`,就會各自漏掉不同的一項(L61 規則收斂律)。
所以不一張一張補頁,而是立**一個頁頭正本**。

## 三、`SUP_MDL750_VeritasUIHead_v0100`(12 檢全綠)

```python
from SUP_MDL750_VeritasUIHead_v0100 import page, veritas_header, SUBSYSTEMS
html = page("VIA · 資料鍛造 VDF 現況台", body, subsystem="VeritasDataForge")
```

一次滿足畫面統一閘的**全部 13 條**契約:

| 級別 | 條目 | 狀態 |
|---|---|---|
| LAW | 零 CDN · 零彈窗 · UTF-8 · viewport · lang | ✔ |
| UNIFY | `<title>` · `:root` 主題令牌 · 頁腳 VIA 標記 | ✔ |
| ADVISORY | 深色模式 `prefers-color-scheme` | ✔ |
| **TARGET** | veritas-header 結構 · 母品牌行 · 三行小/大/小 · 水墨 `#121417`/`#090A0B` | **✔ 真的施工了** |

你批574 給的規格一個字都沒改:三行 13px/26px/13px、`#8C99A6`/`#F0F4F8`/`#737D87`、
padding `32px 40px`、gap `8px`、六個子系統定位句、右側預留狀態燈號位。
第三行沒有定位句時**整行不出**(誠實留白,不塞佔位字)。

**自測的做法是把閘的尺搬過來對自己跑**(契約耦合):
`selftest` 直接 `import` CGC_MDL160 尾版的 `CONTRACT`,逐條驗自己的產出。
閘改了尺,這裡當場紅 —— 兩邊永遠不會各說各話。

## 四、`CGC_MDL160` v0101→v0102(15→19 檢)

- **尾版律分母**,並在 note 同時印全掃與尾版兩個數字(分母要看得見)
- **owner 收窄成四級證據**:`write`(檔名附近有寫檔動作)> `title`(頁的 `<title>` 出現在引擎裡)> `mention`(只提到)> `none`
  實測 **write 14 · title 42 · mention 9 · none 7**
  舊版會印「該由 A/B/C/D/E/F/G/H 再生」——**八個候選等於沒有 owner**(L30 一功能一主)
- **無再生者的 7 張**,fix 改講「**這張頁自己就是正本,要改就是直接改它**」,
  不再寫「請操作員指認」(那是把球丟回去)
- v0101 釘舊行為的第⑨檢**一起改掉** —— 尺跟著行為走,不是關掉它

## 五、回歸

```
全格子 241 站 · OK 239 · FAIL 0 · SKIP 2
SUP_MDL750 12/12 · CGC_MDL160 v0102 19/19 · VCGC 20/20
```

**本批零 PowerShell 改動、零套件安裝**(L70)。
`via-uiunify` 用 `Get-VIANewest` 自動接到 v0102;`SUP_MDL750` 是程式庫,不需要短令。

## 六、下一步(批577 要做的)

18 張紅裡有 11 張找得到 owner 引擎 —— 讓它們改用 `SUP_MDL750.page()`,紅就會一起掉。
另外 7 張無再生者的,直接改頁本身。

```powershell
via-uiunify              # 72 張四級判燈 + 尾版律分母
via-uiunify plan         # 18 紅 15 黃逐張,每張講得出下一步
via-uiunify header       # Veritas 表頭正典規格
```
