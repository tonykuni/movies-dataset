# 批629 ·「你跑的是舊版」這句話,該由工具講

## 零 · 這一批為什麼存在

批626 → 628 連續三批推完。操作員每一次跑出來的都是舊引擎:

```
批626 推完後   矩陣引擎 : VRN_ENG083_VerifiedMatrix_v0102.py   ← 批625 的
批627 推完後   矩陣引擎 : VRN_ENG083_VerifiedMatrix_v0103.py   ← 批626 的
批628 推完後   矩陣引擎 : VRN_ENG083_VerifiedMatrix_v0103.py   ← 還是批626 的
```

**而畫面上看不出樹是舊的。**他只看得到「矩陣引擎 v0103」,看不到「倉裡已經有 v0106」。
於是我連講三次「你還沒拉」,他連跑三次同一條鏈。

> 診斷成本被丟給人,而那本來是工具的事(LL222)。

---

## 一 · 樹齡行(`Invoke-VIA-VRNAudit v0104`)

抬頭多兩行:結構引擎版號,以及——

```
  樹齡     : f64999e7 批626:…
             **本地落後遠端 2 批**(本地 ref 就看得出來,不必連網)
             下一步:git pull origin claude/via-envmanager-governance-7cls8h
             ——底下這一跑用的是**你現在這棵樹上的引擎**,不是倉裡最新的那一支
```

**零網路。**`git rev-list --count HEAD..origin/<branch>` 只讀本地已經有的 remote-tracking ref,
不 fetch、不連線(網路只認 AegisNexus)。

**而且它不敢說「你是最新的」**:

```
  樹齡     : d26178fb 批628:… · 本地 ref 看不出落後
             (**這不等於最新**:origin/<branch> 只新到你上次 fetch 為止;本檔零網路,不代你 fetch)
```

沒 fetch 過的 `origin/<branch>` 只新到上次 fetch 為止,說「齊平」就是假綠。
它只能說「本地 ref 看不出落後」。三態(落後 / 看不出落後 / git 問不到)都渲染過。

---

## 二 · PowerShell 語法與參數名閘(`CGC_MDL168`)

**格子 257 站,零站 parse 過 `.ps1`——而這棵樹有 816 支活的 `.ps1`。**

批625 為此丟掉一整輪,而且兩個坑都是「跑起來才炸」:

| 坑 | 形狀 | `ParseFile` 抓得到嗎 |
|---|---|---|
| ① 反引號 | `Write-Host "看 \`status\`"` —— 反引號緊貼結尾引號,`` `" `` 把引號跳脫掉,字串沒關起來,錯誤訊息指著 30 行後一個無辜的 `[換庫]` | **抓得到** |
| ② 參數名 | `param([string]$Db)` + `[CmdletBinding()]` —— `-Db` 撞 `-Debug` 的別名 `db`,**語法完全合法**,啟動當場 MetadataError | **抓不到** |

所以本閘兩道,刻意分開:

- **A 語法道** `[Parser]::ParseFile` 全樹尾版 `.ps1`
- **B 參數道** 掃 `param(...)` 的參數名與 `[Alias()]`,撞 CommonParameters 別名就點名
  (只在有 `[CmdletBinding()]` 時判——沒有它就不會被塞 CommonParameters,判它是誤殺)

容器實掃:**816 支** · A 道 5 支解析不過(53 筆)· B 道 **0**。

### 夾具沒造對,檢就在量別的東西

第一版我把反引號寫在句中:`` "看 `status` 這一段" ``。
`` `s `` 不是合法跳脫,PowerShell 當成字面 `s`,**字串照樣關得起來**——那不是坑,檢當場紅。
夾具要長得**跟批625 那一行一樣**才算數。

---

## 三 · 棘輪基線:一個永遠紅的站,跟沒有站一樣

上線當天就有 5 支解析不過。若讓它紅著,格子從 `FAIL 0` 變 `FAIL 1`,
看的人很快就學會忽略那一站。照 `CGC_MDL164` 既有的做法立基線:

```
 4 筆  Invoke-VIA-PSRepair-v0102.ps1
28 筆  Invoke-VIA-VRN-Fallback-Activation-v0136.ps1
 9 筆  Invoke-VIA-VRN-OneClick-Sidebar-v0159.ps1
 5 筆  Invoke_VIA_FlowSystem_SandboxPatch_v025.ps1
 7 筆  Run_VIS_HyperBOM_All_In_One_SELF_CONTAINED_v2.ps1
```

**基線內是具名的債,基線外才是新傷。**每一跑都把基線印出來;修好了會提醒收緊基線。

兩條細則:
- **沒有基線時所有語法錯都算新傷**——立一個空基線等於假綠,所以 `--rebaseline` 只在明確要立時跑,不自動。
- 基線是**攤開不是赦免**。那 5 支要不要修,**裁定權在操作員**(LL90)。

---

## 四 · 本批刻意不開短令

`via-pssyntax` 這個名字**沒有出現在任何可執行的地方**。
短令要四個面同時到位才不是幽靈令(加速器橋 · 根目錄梭 · Register 新版號 · 格子開站,LL199),
而那要動 `Register-VIA-Commands.ps1`——**那需要你逐次許可**(L70)。

所以本批只開格子的站。要不要開短令,你說。

順帶一筆舊債:`Register v0226` 裡 `via-vrnrules` 那段**註解**列的動詞還停在
`status|drift|conflicts|harvest|selftest`,沒有批628 加的 `regex|date|ticker`。
功能不受影響(argparse 在引擎裡),但冊上寫的和實際能打的不一樣——要一起補的話也在同一個檔。
