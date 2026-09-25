# 批586 — 備用件納入 PEIS,並跟活樹斷開

操作員令:`1. yes`(要不要把 `_backup` / `RetiredEngines` 也納入 PEIS 掃描)+
`自測完成,拿先前的路徑的樣品去修正,完成;先跟 via / vdf 斷開`。

---

## 一、先講結論:備用件裡有沒有活樹沒有的東西?

**有,兩組。其餘不是遺漏。**

| | 活樹 | 墓園 | 判讀 |
|---|---|---|---|
| **OCR 影像前處理** | `recognize` 0 · `skew` 0 · `denoise` 0 · `grayscale` 0 · `enhance_contrast` 0 · `16bit` 0 · `tiff` 0 · 簡繁轉換 0 | 全部都有 | **真的沒有**。活樹的 OCR 本身是齊的(42 個能力,`tesseract` / `paddleocr` 兩條車道都在),缺的是**進 OCR 之前**那一段:歪斜校正、去雜訊、灰階、對比增強。掃描件辨識率就是靠這一段。 |
| **盤中 VWAP 防禦 · 下市情境壓測** | `vwap` 0 · `scenario`/`stress` 0 | `validate.intraday_vwap_defense` · `misc.scenario_delisting` · `run.scenario_cold` | **真的沒有** |
| TA-Lib 指標包(約 30 個:`adosc` `adxr` `cci` `cmo` `dema` `kama` `macdext` `mfi` `sar` `stoch` …) | 沒有 | 有 | **依法退役**,不是遺漏 —— L50 明令禁用 TA-Lib |
| WorkOps 專案管理(`milestone` `cpm` `pm_sla_breach` `reschedule` `devil_advocate` …) | 沒有 | 有 | 退役的產品線,不在 VIA 範圍 |
| 電影 / 地理資料集(`yearly_tmdb` `gdelt_articles` `overpass_country` `vmt`) | 沒有 | 有 | 不在 VIA 範圍 |

撿不撿回活樹是操作員的裁定(LL90),本批**不代撿**。

---

## 二、尺是怎麼走到這個結論的 —— 三層收斂,每一層都要講清楚為什麼縮

```
墓園 261 檔 / 3283 函式 → 1595 能力
  ↓ 名字只在墓園出現                     only_dead  989   ← 這一層不是答案
  ↓ 連詞根都在活樹找不到                  suspect    120
  ↓ 壓平葉名(walkforward ↔ walk_forward)  suspect    105
  ↓ 人逐條看完                            真的缺       2 組
```

**989 什麼都不代表。**改名、重構、拆函式都會製造它 —— 批585 量過同一件事:
348 族疑似 8 族,真掉的只有一族。所以 `deadcheck` 的輸出**分兩層**,而且在 `why` 裡
明講第一層是候選不是判決。

`120 → 105` 那一步是**拿實測樣品修出來的**:`misc.walkforward` 被判成「活樹沒有」,
可是活樹明明有 `misc.walk_forward` —— 差的只是一條底線。同類的還有
`validate.lookahead` vs `validate.no_future_leakage`、`misc.walkforward` vs `misc.walk_forward`、
`compute.comovement`、`misc.balance_identity`。加一層壓平葉名比對就撈掉 15 個假疑似。

---

## 三、本批真正的根因修:**假的零**

`FAMILIES["retired"]` 第一版寫死成 `["VIA_RetiredEngines"]`。跑出來 **0 支 .py**。

如果我直接拿去回報,操作員收到的答案會是「備用件裡沒有東西」。

實際上樹上有**兩座墓園**:

| 路徑 | .py |
|---|---|
| `VIA_RetiredEngines/`(根下,批581 起) | **0** |
| `functional modules/VIA_RetiredEngines/`(批180 起十一波) | **261** |

備份夾同理,散在**七處**(`supportive modules/_nexuscore_*/RUN_*/_backup`、
`VIA_Reports/*/_backup`),不是單一路徑。

那個 0 不是「沒有」,是**尺沒伸到**。

改法不是再去記一次路徑 —— 是**改走全樹 glob**:樹上有幾座吃幾座,不靠我記得。
→ **LL138:假的零跟假綠是同一件事,而且更難發現 —— 紅燈會有人吵,零不會。**
凡是回報「0 / 無 / 沒有」的結論,都要能說出**尺伸到哪裡**;說不出來就不是結論。

這跟 LL131(分母灌水/縮水)、批583 的 Windows 分隔符,是同一個病灶的三種長相:
**尺的涵蓋範圍沒有人在量。**

---

## 四、斷開(操作員令「先跟 via / vdf 斷開」)→ L72

死樹與活樹**不同掃**。混掃會把墓園的舊件算進活樹的帳,「活樹有幾個重複、省多少 token」
這些數字當場失真,而且失真的方向是**看起來更好**。

三條實作:

1. **同掃回 `GATED`**(rc=4 —— 閘住不是壞,是被擋),並指名兩條各自的令:
   ```
   via-peis scan --family vdf
   via-peis scan --family retired
   ```
2. **兩棵樹兩個庫**:`VIA_Capability_Store__vdf.sqlite` / `__retired.sqlite`,
   封印只跟自己的 plan 比對(批585 那個「封印指紋沒有對應記錄」就是這樣來的)。
3. **讀也要斷**:沒明示家族時,回退只在**活樹的庫**裡挑,而且挑**蓋得最寬**的那本。

第 3 條是自測當場抓到的:回退原本挑**最新**的庫 —— 剛掃完 retired,最新的就是墓園那本,
`run` / `cards` 於是拿墓園當能力庫,檢⑱ 直接 FAIL。**斷開不是只斷掃描,讀也要斷。**

附帶:排除清單的放行門**只對本次明示的那一族有效**。沒指名 `retired` 就照舊排除;
收容正本 `references/intake` **永遠**不放行 —— 正本零觸碰沒有例外。

---

## 五、實測數字

```
via-peis scan --family retired     OK      261 檔 · 3283 函式 → 1595 能力 · 折疊 922 · 近似 296 · 省 99.42%
via-peis scan --family backup      NODATA  0 檔(七座備份夾,容器樹內 0 支 .py — 誠實報零)
via-peis deadcheck --family retired OK     墓園 1595 × 活樹 9134 → only_dead 989 · suspect 105
via-peis scan --family retired vdf  GATED  斷開閘;指名兩條令 · 兩庫 __vdf / __retired
CGC_MDL161 v0104 --selftest         二十五檢 OK 25 · FAIL 0
```

## 六、登錄(L70:不動任何 `.ps1`)

- `CGC_MDL161_PEISCapabilityEngine_v0104.py` — `deadcheck` 是**既有短令 `via-peis` 的新動詞**,
  不是新短令,所以不需要改 register(L70 優先於七處的 ②)。
- `CGC_MDL064_SelftestGrid_v0354.py` — PEIS 站 21→25 檢(站點用 `newest(...)` 自動指尾版)。
- `VIA_Policy_Laws_SSOT_v0100.json` — +L72 +LL138 +LL139(律 69→70,課 137→139)。
- `VIA_AutoCode_Registry_v0100.json` — 台帳 1133→1137。

---

## 七、全格跑出來的三盞紅燈(LL117:推之前先跑全格)

243 站跑完:**OK 236 · FAIL 7 · SKIP 2**。逐盞查完之後,真的只有三件事:

| 站 | 根因 | 處置 |
|---|---|---|
| 5 站 duckdb 鎖衝突(調整後價格層/驗證共識庫/族群聚合因子層/Yahoo 共識/鉅亨 FactSet) | 平行跑時搶同一個 `vdf_tw_market.duckdb`;全格自己的「平行敗→序跑」重試後**不再出現** | 併發假紅,無須修 |
| **制度健全度稽核 檢⑰**(MDL164 自我指涉棘輪) | **真紅,而且抓到的就是我這批新寫的 `deadcheck`** —— 見下 | 已修,棘輪回綠 |
| **中央控管台 檢⑬**(MDL149 元件編號冊覆蓋) | 本批新增兩支尾版件,中央元件自動編號冊沒跟上(ACTIVE 5372/5379) | `via-vcgc registry-sync --apply` 補登:新 7 · 變更 38 · **退役 0** |

### 棘輪抓到我 —— 而且抓對了

`deadcheck` 把**活樹能力庫**當對照集。可是本檔住在 `supportive modules/registry` = `cgc` 族,
活樹庫掃 cgc 時會把**本檔自己的函式**收成能力,那些能力接著就進了「活樹有什麼」。

於是:我只要多寫一個帶 `recognize` 字樣的函式,墓園那支 `misc.recognize` 就自動不再是疑似
—— **我用自己的版本號製造了一個假的進步**。批578 在 MDL164 身上踩過一模一樣的坑。

修法:對照集扣掉「只由 `_SELF_FAMILY` 貢獻」的能力,並把扣掉幾個(`self_excluded`)**報出來**。
實測目前 **0**(活樹庫是在 v0104 出生之前掃的),但機制先在位,下一次掃就擋得住。
棘輪:SAFE 3→4 · **基線外 0**。

---

## 八、順手抓到的一件事:引擎報錯自己的版本

全格跑到 MDL149 時,橫幅印 **v0113** —— 而我跑的是 **v0114** 的檔。
`VERSION = "0113"` 是寫死常數,開新版複製時忘了改,於是這支引擎在**每一份它寫的報告**上
都報錯自己的版本。

全樹量了一次:

```
尾版件裡寫死 VERSION 常數的  6 支
  與檔名相符                 4
  **不符                     2**   CGC_MDL149_v0114 印 0113 · CGC_MDL153_v0101 印 0100
```

改法不是把常數改對(下次複製還會再錯一次),是**從檔名推導**:
`VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]`。兩支都改了。

**誠實揭露:這件事目前沒有尺在守。**全樹只有 6 支寫死、現況 0 違規,我判斷不值得為此再開一支
MDL157 新版號(那又會變成「修尺」而不是交東西)。先記成 **LL140** 慣例;再犯一次就上閘。
