# 批606 — 第三層擋路物:未追蹤件撞名(LL163)

追蹤檔清乾淨(`備份 0 個追蹤檔`)之後,`ff-only` **還是**停:

```
error: The following untracked working tree files would be overwritten by merge:
        VeritasIntelligenceAnalytics/_patches/Apply-B600-vrn_unified.ps1
        VeritasIntelligenceAnalytics/_patches/CGC_MDL148_EngineBus_v0127_to_v0128.diff
        VeritasIntelligenceAnalytics/_patches/_apply_bus_diff.py
Please move or remove them before you merge.
```

PR #41 把 `_patches\` 那幾個檔**commit 進分支**了,而工作站同路徑是**未追蹤**的 —— 兩邊撞在一起。

批605 的腳本刻意寫死「未追蹤件一根不碰」。理由正當,但**不完整**。

> 紀律要保的是「**不損失**」,不是「不移動」。**移開保存 ≠ 刪除。** → **LL163**

## 修法

`Sync-VIA-Bootstrap-v0100.ps1`(就地更新)+ `Invoke-VIA-AllInOne-v0105.ps1`:

```
撞名集合 = git diff --name-only --diff-filter=A HEAD origin/<b>
          ∩ git ls-files --others --exclude-standard
```

| 規矩 | 為什麼 |
|---|---|
| **只搬交集** | 不是整個 `_patches\` 夾清掉 —— 尺太寬跟太窄一樣壞 |
| 搬去 `VIA_Reports\presync_<ts>\_untracked_collisions\` | **不是刪**;原檔連同本機內容整份保存 |
| `git hash-object` vs `git rev-parse origin/<b>:<path>` **逐檔比位元組** | 把「其實一模一樣」和「真的不同」分開報數,不用猜 |
| **沒撞到的未追蹤件一根不碰** | 那一條紀律原封不動 |

實測(scratch 倉造同形狀情境,跑的是倉裡那一支的實際位元組):

```
撞到 3 個未追蹤件(位元組相同 1 · 不同 2)→ 全部保住本機內容
沒撞到的 CGC_MDL148_EngineBus_v0128.py 一字不差
分支回到 ## br...origin/br(無落後)
```

順手修掉一個尾版律:bootstrap 的「下一步」原本寫死 `Invoke-VIA-AllInOne-v0104.ps1`,
改成 glob 取尾版 —— **寫死版號的話升版又會變成「你那一版沒有那個檔」,正是 L85 要防的事**。

## 為什麼 `Sync-VIA-Bootstrap` 就地改版而不出 v0101

版本尾碼是給「引擎換代要能並存」用的。**解卡件的價值恰好相反:它必須是一個永遠不變的路徑。**
一旦出了 v0101,下次操作員手上那一份又會是「沒有新功能的舊版」——
就是 L85 第一次踩到的那個坑。沿革寫在檔頭,改了什麼看 git log。

## 同一個卡點連續三跑才通

| 跑 | 擋路物 | 我當時看到的 |
|---|---|---|
| ① | 沒 pull | `[behind 3]` |
| ② | 41 個髒的追蹤檔 | `local changes would be overwritten` |
| ③ | 3 個撞名的未追蹤件 | `untracked working tree files would be overwritten` |

每一跑只揭露**下一層**。「清掉眼前這一個」和「問清楚還有幾層」是兩件事 ——
而 `Please move or remove them before you merge` 這句話本身就寫著解法,
我第一次讀的時候把它當成背景略過了。

**結果**:操作員已到 `b381d230` · `MDL135` 尾版 `v0110` · `ALL-IN-ONE 在不在: True`。
