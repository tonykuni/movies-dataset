# 側線 2026-09-29 g:命令冊 v0263 +`via-in`(別名 進入環境)—— 進倉 + VCGC 入口流程一句完成

主線批號由併線的手指定(L25)。本批接在 PR #372(36dccaba)之後。

## 一、操作員令(原文)

- 「加 via-in 短令到命令冊 v0263」

這就是 L70 要的**逐次許可**:只許這一支命令冊、只加這一個短令。上一批(側線 2026-09-29 f,`via-vcgc enter`)把這一行寫成一次貼交操作員,本批照令加進冊。

## 二、改了什麼

| 檔 | 內容 |
|---|---|
| `Register-VIA-Commands-v0263.ps1`(新,薄尾) | 同 v0259–v0262 的寫法:函式庫式模板章兩行 · dot-source v0262 · `$global:VIARegisterPath`;只加 `via-in` 與別名 `進入環境`;v0262 以前一字不動(LF · 無 BOM,同 v0259–v0262) |
| `via-in.cmd`(VIA 根)· `bin/via-in.cmd`(新) | 短令必有梭(CGC_MDL157 批543 律);可執行段與 `via-vrnfin` 的標準梭逐位元相同(pwsh 優先 → 點源命令冊尾版 → 呼同名函式;不釘版號);CRLF 同既有梭 |
| `VIA_ModuleChange_Permits_v0100.json`(原冊增一筆) | 許可 P011:KILL-05(L70)· `Register-VIA-Commands-v0263.ps1` · 釘 sha256 `15ac481a…` · 操作員 2026-09-29 原話。之後再動一個位元,擊斃閘照殺 |

`via-in` 做的事:

1. `$VIA` 不在 → FAIL、rc 2(命令冊沒點源)。
2. `via-entry`:進 `$VIA`(在倉內 —— 之後 `git push` 不會再報 not a git repository)、設環境、印家族境 python、入口燈板。
3. 逾時:整輪常超過 `Invoke-VIAPython` 預設 1800 秒;`VIA_PY_TIMEOUT_SEC` 沒設 / 不是數字 / 比 7200 小 → **本次**放寬到 7200,結束(含 Ctrl+C)還原;設 0(不設限)或 ≥ 7200 就照你的。
4. `via-vcgc enter` + 你給的參數(VCGC v0173:第一步 → 只快轉的更新 → 閘 → 加速器 → 工具版本 → 交 `go` 跑整輪)。

## 三、驗證

| 項 | 結果 |
|---|---|
| 入口控制 CGC_MDL157 v0106 `status` | 加之前 **rc 2**:「一貼即用區塊裡的每個 `via-*` 都要是真指令」紅 —— 上一批文件的一次貼寫了 `via-in`,當時還不存在(ghost)。加之後 **rc 0 · 29/29**:427 個呼叫全解得到 · 冊上 185 個短令全有梭 · 零釘死版號 · 兩個梭檢的負控都咬得住 |
| 殺手閘 CGC_MDL187 v0103(`--base origin/main --run-selftest`) | 第一次:KILL-05(L70)擊斃 v0263 —— 閘照設計擋 AI 改 `.ps1`。記上許可 P011(位元釘死)後:**11 條全過 · [許可] 1** |
| PS 模板章 CGC_MDL183 v0102 | PS 掃描面 971 · 帶模板章 917 · 既有債 53 · **基線外新缺 0** |
| TA-Lib 活指令 CGC_MDL243 | rc 0 |
| 全景 PS 文字剖析 | 問題 0(函式 1 支);大括號 / 小括號 / 引號配對平衡 |
| 格子 `--only` | 唯一接觸口控制面二十六檢 OK · 三個專案打包就緒閘廿三檢 OK · 短令能跑閘十五檢 FAIL(見下) |
| PowerShell 語法 | 容器沒有 pwsh;CI 的「VRN value and template regressions」一步用 `[System.Management.Automation.Language.Parser]::ParseFile` 解析**尾版命令冊**(= v0263),本文件在 `docs/**` 觸發這條 workflow |

**短令能跑閘(CGC_MDL165 v0101)的紅是既有的,不是本批造成的**:同一支自測在 main 原樣(v0262 當尾版)就紅三檢,`0 令`;加 v0263 後 `1 令`,判決不變。
原因是「薄尾盲點」同一類(v0172 記過第 6 處):MDL165 只讀**尾版命令冊一本**,v0244 起命令冊都是薄尾,指令都在前版,它讀不到。
修法(本 PR 不擴大):MDL165 出 v0102 薄尾,命令冊改用 CGC_MDL157 v0106 的 `read()`(沿 dot-source 鏈讀、扣掉新冊拆掉的)。

## 四、登錄

- 元件冊:`registry-sync --apply` 新 1(`tool|via-in` = `VIA-TOOL-0194`)· 變更 0。
  **更正(側線 2026-09-29 h,Codex #373 P1):** 0194 早由引擎版本冊發給 token 引擎(一號兩主),via-in 已改發 `VIA-TOOL-0211`,舊號留在該筆的 `recoded_from`;見 `VIA_S20260929h_ToolCodeCollision.md`。
- 編號冊只增合併:`VIA-CORE-MDL481` Register-VIA-Commands-v0263 · FNC_CORE +1(`via-in`);元件冊的 content_sha 換新;各冊 n/sha 核過一致。
- 命令卡冊 `VIA_Command_Cards_v0100.json` **沒有重凍**:凍結器 CGC_MDL162 v0100 只讀尾版命令冊一本,在薄尾冊上重凍會把 169 張卡洗成 1 張。卡冊從 v0244 起就停在 v0243(既有債,同上一段的薄尾盲點);要補,先出 MDL162 的沿鏈讀新版。
- 台帳 1360(ADD)。

## 五、操作員怎麼用

第一次(工作站拉新版、重載命令冊):

```powershell
via-reload
via-in
```

之後每天只要 `via-in`。常用:

- `via-in --card`:只出卡(位置 · 更新 · 閘 · 加速器 · 工具版本),不啟動。
- `via-in --no-pull`:不更新。
- `via-in -Full -NoOpen`:參數照傳給 `go`。
- 別名:`進入環境`。

cmd 殼打 `via-in` 走同名 `.cmd` 梭:流程照跑,但 cmd 自己的目前資料夾不會跟著進倉(子行程改不了父殼);要在 cmd 下 git 指令,先 `cd /d` 到倉根。

## 六、還原

- `git revert` 本批的合併提交;或刪掉 `Register-VIA-Commands-v0263.ps1`(尾版律退回 v0262,`via-in` 就不在)與兩支 `via-in.cmd`,許可冊刪 P011,元件冊 / 編號冊 / 編號 SSOT 還原到前一版。
