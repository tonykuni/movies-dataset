# 批612 — 我叫他打的指令,在他機器上是另一個東西

上一批我在回覆裡寫「打 `via-sync`」。他打了。跑到的不是我寫的那支。

```powershell
# bin\via-sync.ps1 —— 早就存在,和我無關
git fetch origin
git merge origin/claude/via-system-followup-tz7k9t   # ← 寫死另一條分支
git push origin main                                  # ← 推 main
git log --oneline -3
```

他畫面上每一行都對得起來:merge 的是**別條分支**(所以冒出一堆 ChipWar/GroupIndex 髒檔)、
`! [rejected] main -> main` 被拒、尾巴三行 `批88 / 批81` 是那條分支的歷史。

而我批609 登的同名函式 `via-sync`,在 `Register-VIA-Commands-v0221.ps1` 裡 ——
**在他拉不下來的 commit 裡**(他磁碟最新是 v0220)。

兩個錯疊在一起:

1. **取名前沒掃名字**(新法 L88)
2. **解卡的工具又放在被卡住的那一側**(L85,第三次)

---

## 一、撞名閘:難的是分母(LL174)

第一版尺把「同一個名字既有 Register 函式、又有 `.cmd`」都算撞名 ——
285 個短令名裡 **146 個中**。

那不是發現問題,那是把**設計本身**當成問題:批340 律規定每個短令配一支同名 `.cmd` 梭
(點源 Register 尾版 → 叫 `%~n0` 同名函式)。**梭是契約,不是撞名。**

分出「梭」與「獨立實作」之後:

```
短令名 285 · 真撞名 18 · 基線外 0 · 同冊重複定義 2
  [危] via-sync → bin/via-sync.ps1
```

**命中率高到不合理,該懷疑的是判準,不是慶祝抓到很多。**

真撞名 18 筆,全部是 `bin\` 底下留著一支同名的舊獨立實作:

```
via · via-accel · via-all · via-console · via-etfhold · via-iface · via-intake
via-master · via-pipeline · via-ppp · via-py · via-rebuild · via-repo-optimize
via-selftest · via-six · via-sync · via-ui · via-vrnin
```

其中只有 `via-sync` 會動 git 遠端 —— 所以它被**單獨標危險**。
`git push` / `git merge origin/<寫死分支>` 這一類不只是撞名,
是**叫人打一句話就推了遠端**。

順手還抓到同一份 Register 裡 `via-panorama` 與 `via-ssot` **各定義兩次**
(後者靜默蓋掉前者)。只講,不改 —— 哪一個是正本由操作員裁定(LL90)。

---

## 二、不搶名

`via-sync` 這個名字既然已經是別人的,新件就不該硬搶。v0222 的作法:

- **`via-sync`** → 守門函式,零動作,把兩支攤開要求指名
- **`via-presync`** → 同步解卡的正名(量過:285 個名字裡沒有這個)

實跑:

```
[停] 'via-sync' 這個名字在本倉有兩個獨立實作,我不替你挑(LL90)。
 ① 舊件 bin\via-sync.ps1 —— fetch + merge **寫死分支** + **git push origin main**
 ② 新件 Sync-VIA-Bootstrap-v0100.ps1 —— fetch → 備份 + stash → **只做 ff-only**,不推不碰 main
    要這一支請打:via-presync
```

---

## 三、解卡區塊:零檔案依賴,兩條路都跑過

L85 說過三次了,這次交付前先用 pwsh 7.4.6 對**真的 git 倉**跑:

| 路 | 結果 |
|---|---|
| ff-only 成功 | 備份落檔 → stash → `Fast-forward` → 印新 HEAD;**未追蹤檔一根沒碰** |
| 分岔(本地有 origin 沒有的 commit) | `fatal: Not possible to fast-forward` → **誠實停**,印出該查的那一行 |

它只做四件事:印出**你動的是哪一份倉**(批452 雙副本病)、整包備份、
stash(只收追蹤檔)、`merge --ff-only`。**不推、不碰 main、不 merge 別條分支。**

落檔:`launchers/Unstick-VIA-Paste-v0100.ps1`(也可直接貼)。

---

## 四、為什麼他的倉一直髒

`git pull` 被 `VIA_Component_Inventory_SSOT_v0100.json` 擋住,
`via-sync` 被幾十支 ChipWar/GroupIndex 引擎擋住 —— 那些都是**跑引擎時再生出來的追蹤檔**。

我在容器裡每一批 commit 前都做 LL49 還原(這一批還原了 30 支),
**他那邊沒有人做**,所以每跑一次 ALL-IN-ONE 就多一批,下一次 pull 就更難。

這是下一批該做的:把 LL49 還原做成引擎,跑完自動還原再生物,而不是靠我記得。
