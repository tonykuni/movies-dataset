# 批604 — ALL-IN-ONE v0104:真正卡住的是同步,不是引擎

操作員令:「all integrate into one ps code with 25 accelerators」。

---

## 一、確診:你貼的 `git status -sb` 第一行就是答案

```
## claude/...7cls8h...origin/...7cls8h [behind 3]
946132b0 (HEAD -> claude/...) 批600:ALL-IN-ONE 全系統加速實測 v0103
```

`fetch` 成功了(`43fa91dd..8059f3de`),但**工作樹還停在批600**,落後 3 個 commit。

`pull` 沒進去的原因也在同一張圖裡:你有 **41 個被改過的追蹤檔**(再生的 U/I 頁與註冊表),
其中 `VIA_Component_Inventory_SSOT_v0100.json` 這三批我也動過 ——
**git 為了不蓋掉你的修改,拒絕合併**。於是 `via-envgov` 永遠挑到 `v0108`,
`resume` 這種新動詞一律掉進 `print(__doc__)`(那份「說明書」就是這麼來的)。

所以 ALL-IN-ONE 的第一件事不是跑引擎,是**把同步做完**。

## 二、v0104 新的第 0 段 SYNC

```
fetch → 算 ahead/behind → (髒的話)備份 + stash → merge --ff-only → 印 HEAD
```

**紅線寫死在腳本裡:**

| # | 規矩 | 為什麼 |
|---|---|---|
| ① | 只 stash **追蹤檔**(`git stash` 不帶 `-u`) | 你的 `?? CGC_MDL148_EngineBus_v0128.py`、`_patches\`、`*.bak_b600_*` **一根不碰** |
| ② | stash 前先**整包複製**到本跑存證夾 | 一份在 stash、一份是看得見的檔案;兩條退路 |
| ③ | 只做 `--ff-only` | 真的分岔就**誠實停**,不自動 merge、不 rebase、不 force |
| ④ | `-NoSync` 可整段跳過 | 你不想讓它動工作樹的時候 |
| ⑤ | 同步沒成功 → 判定至少 **YELLOW** | 跑的可能不是最新版,不准綠 |

## 三、這一支是**真的跑過**才交的

批600 那次我交了一支語法對、行為錯的 `.ps1`(`$Args` 是自動變數,子行程收不到參數)。
這次容器裡有 `pwsh 7.4.6`,所以造了一個**和你工作站同形狀**的 scratch 倉:

```
落後 3 · 一個被改過的追蹤檔(遠端也改過同一支)· 兩個未追蹤件
```

把**檔案裡第 67–143 行原封不動**抽出來跑,逐件量:

| # | 量什麼 | 結果 |
|---|---|---|
| ① | 未追蹤件內容有沒有變 | `EngineBus v0128` 內容一字不差 · `_patches/` 在 |
| ② | stash 能不能還原 | `stash@{0}: VIA-AllInOne-presync-…` |
| ③ | 看得見的備份 | 裡面是**你的**那份內容,不是倉上的 |
| ④ | 新版檔到位 | `v0109/v0110/v0111` 都在 |
| ⑤ | 分支狀態 | 回到 `## testbr...origin/testbr`(無落後) |

**反面也釘**:製造分岔(`ahead 1, behind 2`)再跑一次 →
`DIVERGED` 誠實停、**HEAD 沒動、沒有多 stash 一筆**。

另外 AST 掃過參數名,無自動變數撞名(`Args/Input/Error/Host/Matches/PSItem/This/…`)。

## 四、15 步(v0103 的 12 步 + 批601/602 的三個唯讀動詞)

```
01 SuperAccel   02 NetUnified    03 加速器控制面   04 RunGate(能跑閘)
05 envgov tools 06 envgov plan   07 envgov resume  08 registry-sync --apply
09 制度健全度   10 畫面統一閘    11 全景稽核 scan  12 矩陣控制台
13 全格 250 站  14 一頁交接      15 安裝核可 check
```

紅的那一步的 `Why` 併批603 L81 同律:**把 `[FAIL]` 那幾行帶進總表**,不只給 rc。

## 五、怎麼跑

```powershell
cd "C:\Users\tonyk\OneDrive\Documents\movies-dataset"
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-AllInOne-v0104.ps1"
```

常用開關:

```powershell
-NoSync          # 不要動工作樹(只跑實測)
-SkipHeavy       # 跳過第 13 步全格(省 5 分鐘)
-Only envgov     # 只跑步驟名含 envgov 的那幾步
-Families vdf,vrn
```

**它不會**:設 `VIA_NET_CONSENT`、裝任何套件、刪任何檔、force push。
vap 的 `pandas` 缺件與 `pyarrow` 半拆仍要你自己裝 —— 第 04 步會把它們列成 `ENV_BROKEN` 並點名。
