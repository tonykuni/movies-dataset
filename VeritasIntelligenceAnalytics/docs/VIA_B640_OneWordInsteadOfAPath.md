# 批640 · 要人手打路徑,就一定會打錯

## 你的令
> INTEGRATE INTO ONE PS CODE WITH 25 加速器

## 起因是我給錯了兩次指令

你連續兩次照我給的指令啟動 ENG085,兩次都失敗:

| 次 | 你打的(我給的) | 錯在哪 |
|--:|---|---|
| 1 | `via-py "functional modules/VRN/VRN_ENG085_…v0102.py" run` | `via-py` 第一位是**家族**,不是檔名 → python 去開一個叫 `run` 的檔 |
| 2 | `via-py vrn "functional modules\VRN\…"` | 少了母資料夾 `VeritasIntelligenceAnalytics\` → 檔案不存在 |

兩次都不是你打錯,是**我把一條帶路徑的指令貼給你**。
所以治的不是「下次小心」,是那條指令本身不該存在 → **L97**。

## 治法:一個字 `via-vrnmd`

```
via-vrnmd --in "C:\測試樣本報告" --chain
```

`--chain` = 先跑 ENG072 抽取,再跑 ENG085 還原;**ENG072 非零就不往下跑**(L83:只跑一半不算跑過)。
路徑、版號、家族全部由冊當場解:

| 原本要人打的 | 現在誰解的 |
|---|---|
| `functional modules\VRN\VRN_ENG085_…_v0103.py` | `Get-VIANewest` 掃尾版 |
| `vrn`(家族) | 短令自己填 |
| `VeritasIntelligenceAnalytics\` | `$VIA` |
| `VIA_ACCEL=1`(25 加速器) | 短令預設開,已設就不覆蓋 |

## 25 加速器不是新寫的,是接上既有的那一條

`VIA_ACCEL` 這條線本來就在 `SUP_MDL737_SuperAccelModule`(TOOL-047),全樹以
`[VIA:ACCEL-BRIDGE]` 正典塊掛橋。批640 做的是**讓短令預設把它打開**,
不是新造一個加速器(Zero-Hydra)。已經設過值的環境變數不覆蓋 —— 你手上要關得掉。

## 差點漏掉的那一處:梭

Register v0227 加了 `via-vrnmd` 函式之後,全格子當場報紅:

```
[FAIL] 唯一接觸口控制面二十六檢(CGC_MDL157)· RED · 25/26
```

LL199 說新短令要**四處**:加速器橋 · 根目錄梭 · Register 新版號 · 格子開站。
我做了三處,漏了**梭**。cmd 殼看不見 PowerShell 的 global 函式 ——
沒有 `via-vrnmd.cmd`,你在 cmd 視窗打它會得到跟批543 `via-pyprog` 一模一樣的
「無法將…辨識為…」。補上梭之後 26/26 GREEN。

**這是同一批之內,L97 立完就被自己違反一次**:我治好了「要人打路徑」,
卻讓那個新短令本身叫不出來。差別只在這次是格子先抓到,不是你先撞到。

## ENG085 v0102 → v0103:把 30 塊分歧攤在你眼前

你那一跑:**105 份 OK 105 · 表格 758 列 · 保全率全 100.00% · 二尺一致 97.3%(1093/1123)**。
剩下 30 塊「對不上」的明細只在你機器的 manifest 裡,我看不到。
v0103 加 `disagree_pairs()`:跑完直接印出成對統計(誰 vs 誰、幾塊、抽樣兩例),
你不必再去 grep。

抽成函式而不是寫在 `main()` 裡,是因為**容器樣本零分歧** ——
寫在主流程它一行都不會被走過就出貨(L83)。抽出來自測才餵得進假資料 → **LL262**。

## 帳

| 件 | 動作 |
|---|---|
| `Register-VIA-Commands-v0227.ps1` | 新版號(v0226 零觸碰,L70)· +`via-vrnmd` |
| `via-vrnmd.cmd` | **新梭** · 不釘版號(CGC_MDL157 檢②) |
| `VRN_ENG085_MarkdownRestore_v0103.py` | +`disagree_pairs()` · 31 檢 |
| `CGC_MDL064_SelftestGrid_v0396.py` | 261 站 |
| 律 | **L97** 要人手打路徑就一定會打錯 |
| 訓 | **LL261 · LL262** |
| 台帳 | 1257 |
