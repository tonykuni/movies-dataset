# VRN-2 薄尾鏈隨船 · VRN2_ChainShip v0101 · 2026-10-29(桌機實跑貼回 → 缺的環先在本機別處找)

> 範圍:只有 VRN-2 自己的檔(`functional modules/VRN/` 下的 VRN_SystemManager / VRN_ENG### / VRN2_* 版號檔 · `SSOT/VRN2_*` 冊 · `_vdf_fetch/`)。
> 不碰 VRN-1 / VDF / VCGC 的任何檔;只增不減:新增工具 v0101 + 本冊,v0100 的工具與冊都留著不改。

## 0. v0101 為什麼出(桌機 2026-10-29 01:33 貼回)

| 項 | 實況 |
|---|---|
| 桌機 ② 補船 | `[結果] RED · 補船前 check rc 1 · ship rc 2 · 補船後 check rc 1`:ship 推了東西(rc 2 = 推被拒或有同名不同內容),但 check 仍缺 `VRN_SystemManager_v0248 / v0253` |
| 判讀 | 缺的環**不在桌機的 `functional modules/VRN`**:桌機線的啟動器跑在私有 runtime(`functional modules/VRN2` · exact ship v0153 · 管理器 v0243),v0249 / v0254 這些尾版是由另一條線的 ⑨ 推上去的,它們釘的前版落在別的夾(私有 runtime · 備份夾 · Downloads 的套件 zip)或根本沒生成 |
| 雲端已補 | `v0231 · v0239 · v0242` 從倉內 zip 原樣取回(PR #571 00336db36);`v0248 · v0253` + SSOT 三冊倉內任何 zip 都沒有 |
| v0101 | `ship` 先 `recover`:每個缺的環在 VIA 樹(含 `functional modules/VRN2` · `VIA_Reports/vrn2/backup`)· `--extra` 指定夾 · `%USERPROFILE%\Downloads` 下 `VRN2_*` 夾與 zip(含套件 zip 內的 runtime zip)找同名檔;**內容唯一且語法 / JSON 過 → 原樣複製進 VRN 夾(冊進 SSOT/)再隨船**;多份不同內容 → 只列不代選(`[FIND?]`);找不到 → `[FIND-]`;`--no-recover` 關 |

## 2. 工具:`functional modules/VRN/VRN2_ChainShip_v0101.py`(sha256 `81b47d7f9b838cf1f0539792b5bab7cf4e526206e37c1903c03cc9f3e86bacc0`)

| 動詞 | 做什麼 | rc |
|---|---|---|
| `check` / `check --heads` | 同 v0100(釘名前版盤點 · TRACKED / BUNDLED / MISSING · 引用冊) | MISSING>0 → 1 · 只有 BUNDLED / 引用冊缺 → 2 · 全在位 → 0 |
| `recover [--extra 夾]` | 只找缺的環並複製進 VRN 夾,不碰 git;印 `[FIND] 檔 ← 來源`、`[FIND?]`、`[FIND-]`、`[SKIP]` | 全找到 → 0 · 有代選不了 / 找不到 / 內容不過 → 2 |
| `ship [--commit] [--push] [--no-recover] [--extra 夾]` | 先 recover(預設)→ 同 v0100 的在位未入倉補船;收據多 `recover` 欄 | 同 v0100;recover 有黃 → 2 |
| `--selftest` | v0100 的 19 項 + 8 項(同內容兩份當一份 · 套件 zip 內 runtime zip · 兩份不同內容不代選 · Downloads 非 VRN2_* 夾不找 · ship 先 recover 再帶上船 · 補船後 check · --no-recover) | 0 / 1 |

收據:`VIA_Reports/vrn2/VRN2_ChainShip_latest.json`(被 .gitignore 排除)。白名單以外一律不帶;recover 只複製**缺的環**(check 判 MISSING 或引用冊缺的那些名字),不碰任何在位的檔。

## 1. 容器實測發現(回到本地實測的第一個紅)

| 項 | 實況 |
|---|---|
| 現象 | 乾淨 clone(origin/main 918461d4)跑 `VRN_SystemManager_v0254.py --selftest` → `FileNotFoundError: 前版 VRN_SystemManager_v0253.py 不在 · v0254 不接`(rc 1) |
| 根因 | ⑨ 自動上船只帶「當輪新落地的檔」(v0152 收尾只 2 檔 · v0155 收尾只 5 檔);薄尾釘名的前版留在桌機沒入倉 |
| 倉上缺(釘名直接指到的) | `VRN_SystemManager_v0242` · `v0248` · `v0253`(再往前的 v0241 · v0246 · v0247 · v0250~v0252 要補上後才看得到) |
| 引用冊未入倉 | `SSOT/VRN2_Regex_v0100.json` · `VRN2_RestoreRiskCatalog_v0100.json` · `VRN2_Publish_Config_v0100.json`(v0240 / v0244 / v0249 / Publish / UIAction 引用;桌機生成) |
| 影響 | 任何從倉啟動的 VRN-2(雲端 Claude · 另一台機 · CI)都載不起管理器;缺漏清單 #12「兩線入口合一」沒有前提 |
| 旁證 | 另一條雲端分支 `claude/vrn2-closeout-authorization-y4ixl7` 的 `VRN2_CloudAudit_20261028.md` §2 / §6 同判定(它選擇不出工具、不開 PR) |

## 2 (v0100). 工具 v0100:`functional modules/VRN/VRN2_ChainShip_v0100.py`(sha256 `cfee9e2d056d3eca063b8693889a148db0959e4c46c468f412266582cd7ab608`)

| 動詞 | 做什麼 | rc |
|---|---|---|
| `check` | 每一個 VRN-2 版號檔的釘名前版(`PRIOR_NAME` / 字串釘名,同家族且版號較小才算)往回走到底;每一環判 TRACKED(夾內在位)/ BUNDLED(只在 `docs/handoff/ai/vrn2_ship/VRN2_Bundle_latest.zip`)/ MISSING;另列「引用的 VRN2_ 冊未入倉」 | MISSING>0 → 1 · 只有 BUNDLED / 引用冊缺 → 2 · 全在位 → 0 |
| `check --heads` | 只走各家族尾版(短版) | 同上 |
| `ship` | 用 git 找「本機在位但未入倉」的白名單檔(未追蹤 + 已暫存但 HEAD 沒有的)→ `git add`;已追蹤但內容不同 = 同名不同內容 → 只列不覆寫;語法不過的 .py / 不合法 JSON / >8 MB 不帶 | 有同名不同內容 / 跳過 / push 被拒 → 2 |
| `ship --commit --push` | 只含這些檔落一筆提交,推當前分支(被拒 = 分支落後 → 黃,交 ⑨ 持續解衝突) | 同上;不是 git 倉 → 1 |
| `--selftest` | 臨時 git 倉 + 合成鏈,19 項(先 ship 再 ship --commit 也進提交 · 尾版判定 · 鏈走到底 · BUNDLED / MISSING / 引用冊 · 白名單 · 語法跳過 · 同名不同內容不覆寫 · 提交只含加入檔 · 收據 · 非 git 倉拒跑) | 0 / 1 |

收據:`VIA_Reports/vrn2/VRN2_ChainShip_latest.json`(被 .gitignore 排除)。白名單以外(輸出冊 · 帳本 · `_archive_vrn2/` · `registry/` · 任何他系統的檔)一律不帶。

## 3. 桌機一鍵(貼進 PowerShell;5.1 / 7 都可 · v0101:ship 會先 recover)

做的事:① 倉裡沒有工具 v0101 就從本分支(合併後 `origin/main`)取 → 核對 sha256(CRLF 容忍)② `check` ③ `ship --commit --push`(先 recover:缺的環在本機別處找到就先複製進來)④ 再 `check` 看鏈是否補齊。
程式碼 SHA-256(本地實測一輪 `$H_CS` 核對的就是這個):`78ef9852c1dc1a902f342f10d7a0b37e03531ae34c72a7010dd350a85607bcd6`
推的是**當前分支**(main 或 vrn2-auto);被拒不重試、不 force,交啟動器 ⑨。

```powershell
& {
  $REPO = "C:\Users\tonyk\OneDrive\Documents\movies-dataset"
  $REL  = "VeritasIntelligenceAnalytics/functional modules/VRN/VRN2_ChainShip_v0101.py"
  $WANT = "81b47d7f9b838cf1f0539792b5bab7cf4e526206e37c1903c03cc9f3e86bacc0"
  if (-not (Test-Path -LiteralPath (Join-Path $REPO ".git"))) { Write-Host "[RED] 不是 git 倉:$REPO" -ForegroundColor Red; return }
  $T = Join-Path $REPO ($REL -replace '/', '\')
  $py = Get-Command python, py, python3 -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
  if (-not $py) { Write-Host "[RED] 找不到 python" -ForegroundColor Red; return }
  $env:PYTHONUTF8 = "1"
  if (-not (Test-Path -LiteralPath $T)) {
    git -C $REPO fetch -q origin main claude/optimistic-goodall-yhalc5 2>$null
    foreach ($ref in @('origin/main', 'origin/claude/optimistic-goodall-yhalc5')) {
      & $py.Source -I -c "import subprocess,sys;r=subprocess.run(['git','-C',sys.argv[1],'show',sys.argv[2]+':'+sys.argv[3]],capture_output=True);sys.exit(1) if (r.returncode or not r.stdout) else open(sys.argv[4],'wb').write(r.stdout)" $REPO $ref $REL $T
      if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $T)) { Write-Host "[工具] 從 $ref 取得 VRN2_ChainShip_v0101.py"; break }
    }
  }
  if (-not (Test-Path -LiteralPath $T)) { Write-Host "[RED] 取不到 VRN2_ChainShip_v0101.py(fetch 不到 main / 分支)" -ForegroundColor Red; return }
  $sha = (Get-FileHash -LiteralPath $T -Algorithm SHA256).Hash.ToLower()
  $lf = ([IO.File]::ReadAllText($T) -replace "`r`n", "`n")
  $shaLF = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($lf))) -replace '-', '').ToLower()
  if ($sha -ne $WANT -and $shaLF -ne $WANT) { Write-Host "[RED] 工具雜湊不符:$($sha.Substring(0,12))(要 $($WANT.Substring(0,12)))" -ForegroundColor Red; return }
  Write-Host "[工具] VRN2_ChainShip_v0101.py 雜湊相符 $($WANT.Substring(0,12))"
  & $py.Source $T check;                $rc1 = $LASTEXITCODE
  & $py.Source $T ship --commit --push; $rc2 = $LASTEXITCODE
  & $py.Source $T check;                $rc3 = $LASTEXITCODE
  $lamp = if ($rc3 -eq 1 -or $rc2 -eq 1) { "RED" } elseif ($rc3 -eq 0 -and $rc2 -eq 0) { "GREEN" } else { "YELLOW" }
  Write-Host ("[結果] {0} · 補船前 check rc {1} · ship rc {2} · 補船後 check rc {3}(0 綠 · 2 黃 · 1 紅)· 收據 {4}" -f $lamp, $rc1, $rc2, $rc3, (Join-Path $REPO "VeritasIntelligenceAnalytics\VIA_Reports\vrn2\VRN2_ChainShip_latest.json"))
}
```

看什麼:
- `check` 看的是**本機夾內**:桌機上前版都在,補船前通常就是綠;紅只會出現在乾淨 clone(雲端 / CI)。`ship` 的 `[ADD]` 行才是重點 = 要上船的前版與冊;`[YEL] 同名不同內容` 行 = 桌機改過已入倉的檔 → 不覆寫,照規則出 v+1;`[SKIP] SYNTAX` = 語法不過的檔不帶。
- 補船後 `check` 綠 = 鏈補齊;黃 = 還有只在船包的環或引用冊沒在 `SSOT/`;紅 = 新冒出來的缺版(前一次看不到的更前版)→ 再貼一次。
- `[PUSH] 被拒(分支落後)` = 本機落後 origin;提交已落本機,下一輪啟動器 ⑨ 持續解衝突會帶上去。

## 4. 規則(給下一個 AI)

- 只增不減:工具永不改已追蹤的檔、不 `git checkout` 覆寫、不 force push、不刪;同名不同內容只列。
- 下一輪 ⑨ 自動上船前先跑 `VRN2_ChainShip_v0101.py check`;紅就先 `ship --commit`,再上船(建議把它納進 ⑨ 的前置;啟動器不在倉,這一步只能由桌機線改)。
- 雲端 / CI 用 `check`(唯讀,不碰 git)當鏈完整性的燈;rc 1 = 倉不能自載 VRN-2。
- 版號:本冊不出任何 SystemManager / ENG397 / ENG062 新版(桌機線正在 v0254 / v0129 / v0114 上推進,雲端沒樣本、沒前版,出了驗不了)。

## 5. 容器測試紀錄(2026-10-28)

| 測試 | 結果 |
|---|---|
| `VRN2_ChainShip_v0100.py --selftest` | OK 19 · FAIL 0 |
| `check`(倉 origin/main 918461d4 + 本工具) | RED · 起點 426(家族尾版 71)· 環 522 · MISSING 3 · BUNDLED 0 · 引用冊缺 8 列(3 本) |
| `check --heads` | RED · MISSING 1(v0253;v0244 / v0249 非尾版不在短版裡)|
| `ship`(容器,乾跑) | 只抓到本工具自己(未入倉時)· 跳過 0 · 同名不同內容 0 |
| 桌機一鍵模擬(pwsh 7.4.6 · 本機 clone · 植入未入倉前版 + 冊 + 改過的已追蹤檔 + 垃圾檔) | 見 §6 |
| VCGC 全景 `read` 本工具 | 無 AST 錯誤(SYNTAX / DUPDEF / UNREACH / BAREEXC / SWALLOW / MUTDEF 皆 0) |

## 5b. v0101 容器測試(2026-10-29)

| 測試 | 結果 |
|---|---|
| `VRN2_ChainShip_v0101.py --selftest` | OK 27 · FAIL 0(v0100 的 19 + recover 8) |
| `recover`(本倉 clone · 容器 Downloads 空) | YELLOW · 缺 5 · 複製 0 · 找不到 5(v0248 · v0253 · SSOT 三冊 —— 雲端沒有,正是要桌機找的) |
| 桌機預期 | `ship` 先印 `[FIND] VRN_SystemManager_v0253.py ← <找到的路徑>` 再 `[ADD]`;若印 `[FIND?]` = 同名兩份不同內容 → 貼回那兩行我來判;`[FIND-]` = 整台機找不到 → 那條線的前版沒生成,要桌機線重出 |

## 6. 桌機一鍵模擬(容器 pwsh · v0100 當時)

以 origin/main 918461d4 為底的本機 clone(`--shared`)上,植入桌機會有的狀態後,貼 §3 的一鍵(把 `$REPO` 換成 clone 路徑;其餘一字不改;pwsh 7.4.6):

| 植入 | 期望 | 實得 |
|---|---|---|
| 未入倉前版 v0241 · v0242 · v0246~v0248 · v0250~v0253(各 1~2 行的釘名樁) | 全部 `[ADD]` | 10 檔 `[ADD]` ✓ |
| 未入倉冊 `SSOT/VRN2_Regex / RestoreRiskCatalog / Publish_Config _v0100.json` | `[ADD]` | 3 本 `[ADD]` ✓ |
| 倉裡沒有本工具 | 從 `origin/claude/optimistic-goodall-yhalc5` 取 · sha 相符 · 一併 `[ADD]` | ✓(合併後會從 `origin/main` 取) |
| 語法壞的 `VRN2_BadSyntax_v0100.py` | `[SKIP] SYNTAX 行 1` · 不進提交 | ✓ |
| 已追蹤的 `VRN_SystemManager_v0245.py` 加一行 | `[YEL] 同名不同內容 · 不覆寫` · 不進提交 · 工作樹原樣 | ✓ |
| 垃圾檔 `VRN2_run_notes.txt` | 不帶 | ✓(未出現) |
| 已暫存但沒提交的 `VRN_SystemManager_v0253.py`(模擬「先 ship 再 ship --commit」· Codex P2) | 也進 `[ADD]` 與提交 | ✓(第二次模擬加入) |
| 提交 / 推送 | 一筆只含 13 檔 · 推當前分支 | `[COMMIT] e14a756c · 補 13 個` · `[PUSH] 推上 desk-test2` ✓ |
| 補船後 `check` | MISSING 0 | GREEN · 起點 436 · 環 541 · MISSING 0 ✓ |
| 總燈 | ship rc 2(有同名不同內容 + 跳過)→ YELLOW | `[結果] YELLOW · 補船前 check rc 0 · ship rc 2 · 補船後 check rc 0` ✓ |

第一次模擬(誤以本機舊 main 為底)另外證明:底不同時 `check` 會老實報缺的那一環(v0240 / v0249),不會冒充綠。
模擬用的分支 `desk-test` / `desk-test2` 只在容器本機,已刪;沒有推到 GitHub。

## 7. Codex 審查(PR #570)回覆

| 發現 | 處置 |
|---|---|
| P1 新 Python 沒帶既有加速器橋(AGENTS.md 第 4 條;全景 `read` 報 ACCEL) | 已加同家族既有的 `# [VIA:ACCEL-BRIDGE:v0111]` 標記(與 VRN2_Publish / UIAction / SystemManager v0254 同款);`from __future__` 位置不變;全景 `read` ACCEL 消失 |
| P2 先 `ship` 再 `ship --commit --push` 第二次靜默不提交(已暫存的檔不在 `ls-files --others`) | 候選 = 未追蹤 ∪ `git diff --cached --diff-filter=A`(已暫存但 HEAD 沒有);自測 ⑲ + 桌機模擬(預先暫存 v0253)都進提交 |

## 8. 下一步(桌機)

1. 本 PR 合併後(或直接用本分支),在桌機貼 §3 → 看 `[ADD]` 清單與 `[結果]`。
2. 推被拒 → 下一輪 ActivateVRN-2 ⑨ 會帶上去;推成功 → 雲端 / CI 再跑 `check` 應轉綠(只剩「只在船包」的黃,若有)。
3. 之後每輪 ⑨ 前先 `check`;桌機線若願意,把 `VRN2_ChainShip_v0100.py check` 納入啟動器 ⑨ 的前置(啟動器不在倉,由桌機線改)。
