# 批625:一個 PS 指令跑完 VRN 實測 · 「直到成功」怎麼做才不是假的

操作員令:

> 在檢視一下先前紀錄 檢查一下母資料夾 整合入一個ps指令加入25個加速器 動態進度條
> 加入並更新前一個指令測試修正vrn直到成功 測試樣本如先前

---

## 一 · 母資料夾:容器這邊是乾淨的

```
$ git status --short --untracked-files=all -- . ':(exclude)VeritasIntelligenceAnalytics'
(空)
```

你機器上那句「母資料夾有 2 件還沒進 git」是**你那台的本地件或再生物**,
容器這邊看不到 —— 要我判斷是什麼,把 `via-sync -Onboard` 印的那兩個檔名貼回來。

## 二 · `via-vrnaudit`:一個指令,四段

```powershell
via-vrnaudit                                  # 預設 -In "C:\測試樣本報告"
via-vrnaudit -In "D:\另一批" -MaxRounds 3
via-vrnaudit -In "..." -DbPath "<某個 .duckdb>"
```

| 段 | 做什麼 |
|---|---|
| ① 母資料夾 + 指令冊 | 自找根、點源 Register 尾版 |
| ② **25 加速器** | 點源正典名冊 `VIA_PS_Accelerators_25_Roster_v0100.ps1`,不自己抄一份 |
| ③ VRN 本位解譯器 | `Get-VIAEnvPython vrn`;境缺就誠實說走 base 退路 |
| ④ **輪迴實測** | 鏈實跑 → 驗證矩陣 → 診斷 → 換庫 → 再讀 |

**動態進度條**沿用批619 那套:`@@PROGRESS` 當內層來源,沒來源就標「(時間粗估)」,
原生 `Write-Progress` 全程關掉(逐字稿裡看不見的東西不算進度)。

### 「直到成功」的輪迴律

> **下一輪一定要跟這一輪不一樣;找不到可調整的差異就誠實停。**

把同一句跑三次不叫修正,那只是把同一個結果印三遍(批624 LL205)。
目前只認**一種**可調整的差異,而且是量出來的:

* 鏈跑完了、矩陣卻說庫不在 → 去兩個候選夾找**最近寫入**的 `.duckdb`,下一輪讀那個
* 引擎自己 rc 非誠實態(真的爆了)→ **不重試**,重跑一個會爆的只會再爆一次
* 樣本夾不在 → `ABSENT`,而且**不替你猜路徑**(猜對了也是猜的)

容器實跑,兩半都走過:

```
樣本夾不在      → 裁決 ABSENT(rc=3)「這不是引擎壞了,是料不在」
真 PDF 兩份     → 鏈 NODATA → 換庫 vdf_tw_market → 換庫 vdf_global_market
                → 裁決 NODATA(rc=2)· 輪次 3 步 · 加速器 25/25
```

## 三 · 走另一半才抓到的:我自己在批624 造的假態

第一次拿真 PDF 跑,啟動器印出:

```
[VRN_ENG083 v0101] 鏈實跑 · NODATA
=== VRN AUDIT 裁決 · RED ===
  鏈實跑 rc=1。**引擎自己壞了,重跑不會變好**
```

**畫面說 NODATA,rc 回 1。**批624 我在 `run_chain` 加了 NODATA 這一態,
卻沒動 CLI 那一行 `return 3 if ABSENT else 1` —— **加一個態沒接 rc,那個態就只活在畫面上**。
於是我自己寫的下游照 rc 判,對著一個誠實回報「料不夠」的引擎說它壞了。

`v0102` 修法不只是補那一行:

```python
_RC_OF = {"OK": 0, "GREEN": 0, "RED": 1, "FAIL": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4}
```

再加一檢 **㉒**:掃原始碼把所有 `"state": "X"` 的 X 撈出來,逐個問對照表認不認得 ——
**新增態沒登記就當場點名**,不靠人記得。自測 21 → **22 檢**。

## 四 · 兩個只有真的跑一次才會現形的 PowerShell 坑

1. **反引號是跳脫字元,不是 markdown。**
   我在雙引號字串裡寫 `` `status` `` 當程式碼標記,那個反引號把結尾的引號跳脫掉,
   字串沒關起來,AST 在 **30 行之後**才爆,錯誤訊息指著一個完全無辜的 `[換庫]`。
2. **`-Db` 撞 `-Debug` 的別名。**
   `[CmdletBinding()]` 內建 `-Debug`,別名就是 `db`。
   **AST 一路綠燈,啟動當場 `MetadataError`。**改名 `-DbPath` 時還得記得把
   **我自己印給你的那一行次步句**一起改,不然又是一個幽靈令。

## 五 · 你那邊怎麼跑

```powershell
via-presync
via-reload                       # via-vrnaudit 是 Register v0226 新登錄,不 reload 叫不動
via-vrnaudit                     # 預設就是 C:\測試樣本報告
```

裁決是 `GREEN` / `NODATA` / `ABSENT` / `RED` 四態,rc 一致(0/2/3/1),
逐輪原文落在 `VIA_Reports\vrn_audit\<ts>\`。

## 登錄

* 課 208(+LL207/LL208)· 台帳 1231
* 新件:`launchers/Invoke-VIA-VRNAudit-v0100.ps1` · `via-vrnaudit.cmd` ·
  `Register-VIA-Commands-v0226.ps1` · `VRN_ENG083_VerifiedMatrix_v0102.py` ·
  `CGC_MDL064_SelftestGrid_v0380.py`(站名 21→22 檢)
