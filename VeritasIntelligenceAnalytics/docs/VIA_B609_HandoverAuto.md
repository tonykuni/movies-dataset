# 批609 — 自動交接報告 + `via-sync` 短令(操作員大授權)

操作員令:**TEST / DEBUG / OPTIMIZE / AUTO-CONSOLIDATE / AUTO SYNC / SAVE ALL STATUS AND
HANDOVER REPORT AUTOMATICALLY**。

---

## 一、你剛踩到的兩個缺口

### `Sync-VIA-Bootstrap` 打不通

```
PS> Sync-VIA-Bootstrap
無法將 'Sync-VIA-Bootstrap' 字詞辨識為 Cmdlet、函式、指令檔或可執行程式的名稱。
```

**治理件全家都有短令,只有它沒有。** 補上(`Register v0221` + `.cmd` 梭):

```powershell
via-sync                              # 同步解卡(fetch → 備份+stash → ff-only → 印尾版與下一步)
via-sync -Onboard                     # 上船母資料夾:唯讀清點
via-sync -Onboard -Commit [-Push]     # 真的上船(你的手)
via-allinone [-SkipHeavy] [-MaxLines 30]
```

兩支都**glob 取尾版、不寫死版號** —— L85 那個坑不再踩第二次。

### `via-intake` 的 `Not possible to fast-forward`

```
[同步] pull --ff-only:fatal: Not possible to fast-forward, aborting.
```

那表示**你本地有 origin 沒有的 commit**(分岔),不是 ff 能解的。看一眼:

```powershell
git log --oneline origin/claude/via-envmanager-governance-7cls8h..HEAD
```

有東西的話,那就是「該上船」的一部分 —— `via-sync` 會誠實停在 `DIVERGED` 不亂動。

## 二、自動交接報告(每一跑都產)

`v0107` 每一跑自動寫 `VIA_Reports\accelerated_test\<ts>\HANDOVER.md`:

```
判定 / 母資料夾 / 同步態(落後·領先·stash·撞名) / HEAD / 加速器 / 家族境退路
步驟表(步 · 家族 · 態 · rc · 秒 · 因由)
紅的逐個點名  ← 每一條都指得到自己的 log
產出驗證(FRESH / STALE / MISSING)
上船清點(該上船 / 再生物 / 暫存)
下一步
```

**實測 63 行** —— 取代你一直在貼的 400+ 行主控台。以後**貼這一份就夠**。

## 三、第 16 步:上船清點(唯讀)

AUTO SYNC 只做了 `pull` 那一半。另一半是「母資料夾裡有什麼還沒進 git」——
每一跑浮出來,但**只清點不動**;要上船是 `via-sync -Onboard -Commit`,你的手。

實測(對本倉真跑):正確抓到 4 件未追蹤
(`Register-VIA-Commands-v0221.ps1` · `Invoke-VIA-AllInOne-v0107.ps1` · `via-sync.cmd` · `via-allinone.cmd`)。

## 四、誠實界定 —— 「pass audit and run perfectly」我這邊做不完

你的全格第一段是 **OK 196 · FAIL 52**(序跑複判轉綠 12,剩約 40 紅)。

**那 ~40 個紅在你那台。本容器 250 站 248 綠,我重現不出來。**

這不是推託,是三件事實:
- 本容器沒有 akshare / 沒有那些來源庫 / 沒有那 46 個境
- 本容器 py3.11、你 py3.12(`\e` 那件就是這樣漏的)
- 本容器全格 292s、你 2314s(差 8 倍)

**所以流程是**:你跑 `via-allinone` → 把 `HANDOVER.md` 貼回來(63 行,不是 400 行)→
我逐站看「紅的逐個點名」那一段,能在倉內修的就修、只有你那台才有的就指名要什麼證據。

那份報告是**為了這個 round-trip 而生的**,不是為了好看。
