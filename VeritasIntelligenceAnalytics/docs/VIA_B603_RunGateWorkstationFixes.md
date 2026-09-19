# 批603 — 工作站 `via-rungate` 實錄三修 + 摘要同族掃描

操作員貼回工作站 `via-rungate` 全文:**vdf RED · vrn GREEN · vap RED · 總判 RED**。
三個紅燈在本容器**一個都量不到**,全部是實錄逼出來的。

---

## 〇、先講你會踩到的:你跑的還是 `v0108`

兩段 digest 仍印 `MDL135 v0108(批509)`,而且 `via-envgov resume` 印出**引擎說明書**
—— 那是 v0108 遇到不認得的動詞時的 `print(__doc__)`。結論只有一個:**批601/602 的檔案不在你的樹上**。

診斷(一次貼完,會直接印出 `via-envgov` 到底抓到哪一支):

```powershell
cd "C:\Users\tonyk\OneDrive\Documents\movies-dataset"
git rev-parse --abbrev-ref HEAD
git log --oneline -3
git fetch origin claude/via-envmanager-governance-7cls8h
git status -sb
Get-ChildItem ".\VeritasIntelligenceAnalytics\supportive modules\registry\CGC_MDL135_EnvGovernance_v*.py" | Select-Object -Last 3 Name
```

最後一行印出來如果只到 `v0108`,就是 pull 沒落地。

**更正我上一則寫錯的一句**:我叫你點源 `Register-VIA-Commands-v0199.ps1` —— 倉上尾版是
**`v0220`**(你實際跑到的也是 v0220,`.cmd` 梭自己挑尾版挑對了)。是我報了個舊號。

## 一、`VDF_ENG090` 漏 `import os`(真紅,已修)

```
NameError: name 'os' is not defined
  VDF_ENG090_DataCoverageGate_v0102.py line 280, in macro
```

`macro(probe=True)` 要 `dict(os.environ)`,而檔頭沒 `import os`。

**為什麼本容器一路綠?因為這裡沒裝 akshare。** `find_spec("akshare") is None` 就 ABSENT 回頭了,
那一行**從來沒被走到**。第⑮檢只驗了「沒裝時誠實 ABSENT」——「裝了會怎樣」這半邊在本容器永遠量不到。

`v0103`:補 `import os` + 第㉑檢造一個**假 akshare** 進 `sys.path`/`PYTHONPATH`,逼著走有裝的那一半。
對照組實證:同一段對 `v0102` 跑 → 重現 `NameError`;對 `v0103` 跑 → OK。→ 新律 **L83**

## 二、紅了卻看不出哪一檢紅(已修)

```
[FAIL] vdf VDF_ENG088_ConsensusFusionBridge_v0101.py · [OK] ⑦ 紀律宣告 | [計] 七檢 OK 6 · FAIL 1
                                                        ↑ 這是綠的
```

RunGate 的 tail 取 `alll[-2:]` = **最後一檢(綠)+ 計數行**,真正紅的那一檢在上面。
你只能自己重跑一次才知道是哪一檢。這跟批602 **L81**(digest 截斷吃掉「執行」那一行)是同一個病。

`v0106`:紅的時候先取 `[FAIL]` 那幾行再補計數行,綠的維持原樣。合成引擎正反兩向釘(第⑱檢)。

**ENG088 那一檢我沒有修** —— 本容器 7/7(這裡沒有那份來源庫),要等 v0106 把它指出來才知道是哪一檢。

## 三、`pyarrow` 半拆被判成引擎壞(已修判讀)

```
AttributeError: module 'pyarrow' has no attribute '__version__'
  C:\Users\tonyk\envs\via_vap_312\Lib\site-packages\pandas\compat\pyarrow.py line 14
```

批596 已經替 `VAP_ENG015` 認過 `ModuleNotFoundError`,但**半拆件拋的是 `AttributeError`**
—— 形狀不同就整個漏掉,**尺只認一種「缺」**。

`v0106` 加 `ENV_BROKEN` 態,**用證據判不用字串猜**:最內層 frame 必須在 `site-packages`
(不在我們樹裡)**且**訊息符合缺件/半拆形狀,兩個條件缺一不可。判定與「必要庫缺」同級 **YELLOW** 並點名。

第⑲檢**正反兩向都釘**:同一句話炸在自己樹裡 → 照樣 `FAIL` 且 `RED`。
不然這條路就變成把真 bug 漂白的後門。→ 新律 **L84**

**vap 的料還是要你自己裝**(不代裝):`pandas` 缺、`pyarrow` 半拆。

## 四、LL160 要求的同族掃描 —— 而第一支是我自己

律訂完順手掃「還有誰在做同樣的摘要」,全樹尾版三支:

| 引擎 | 原本 | 處置 |
|---|---|---|
| `CGC_MDL064_SelftestGrid` | `[-2:]` | **v0365 同律修** |
| `CGC_MDL161_PEIS` | `[-1:]`(只給一行) | **v0107 同律修**(30/30) |
| `CGC_MDL148_EngineBus` | `[-6:]` | 夠寬,不動 |

第一支就是活證據:**這一輪我看格子的紅站,畫面給我的正是「綠的 ㉒ + 計數行」**,
我是自己重跑 MDL149 才找到紅的是 ⑬。律咬到我了我都沒發現。

## 五、過程中我做錯一件事(已復原)

替 MDL161 開新版時 `cp v0102 v0103` —— **v0103 本來就存在**(樹上 v0102…v0106),
等於**拿舊版蓋新版**(v0102 是 21 檢、v0106 是 30 檢)。`git status` 出現 ` M` 才發現,
立刻 `git checkout --` 復原,改以 v0106 為基底開 v0107。

兩個錯疊在一起:① 沒先 `ls` 就假設下一號是空的;
② **grep 只命中 v0102 就以為 v0102 是尾版** —— 它之所以只有它命中,正是因為新版早改過那一行。
→ **LL161**:`cp` 前先 `test -e … && 停`;寫完立刻看 `git status`,新版檔應該永遠是 `??`,出現 ` M` 就是蓋到人。

---

自測:`VDF_ENG090 v0103` 20/20 · `CGC_MDL137 v0106` 19/19 · `CGC_MDL161 v0107` 30/30。
