# 側線 2026-09-30 b:VCGC 全功能盤點 · 一條串測 · AI 進場同流程 · 版本時間紀錄(VCGC-REQ085,第一段)

主線批號由併線的手指定(L25)。本批基於 main 95acadf49(PR #378 併入)。新版號與 Z 號都用 LL334 掃過 243 個遠端分支。
需求冊跳過 v0107:PR #379(Codex 草稿)已占用 v0107,本批取 v0108(prior v0106)。兩邊誰後併,誰就要出新版合併兩邊的需求。

## 一、操作員原話(逐字)

| # | 原話 | 入冊 |
|---|---|---|
| 1 | VCGC所有功能盤點如先前所說用一個PS檔案串聯測試啟動一切不遺漏 且AI進入系統也會跑這流程後面生成的指令也會跑這個流程 任何更新留紀錄版本及時間  範圍不發散完成VCGC | VCGC-REQ085(需求冊 v0108,PARTIAL) |
| 2 | 目前進頓交接 | 工序令(照做:交接) |
| 3 | 先完成手頭部分開PR | 工序令(照做:本段收在盤點冊 · 串測引擎 · VCGC 入口;PS 入口列下一段) |

## 二、本段交付

| 檔 | 做什麼 | 驗證(實跑) |
|---|---|---|
| `VIA_VCGC_FunctionInventory_SSOT_v0100.json`(新) | VCGC 全功能站表正本:74 站。覆蓋動詞 40 · 席位 6 · 必用卡 13 · 交接案 10 · 工作流步 39 · PS 入口 1,每項對一個站或寫明豁免理由(8 項)。站只收唯讀或乾跑形式 | `test inventory` GREEN(新 0 · 缺 0) |
| `CGC_MDL224_TestAuto_v0101.py`(沿用既有 `test` 門,不另開家族) | 照冊跑站,盤點不靠記:<br>• 動詞由 VCGC 180 個版本的 AST 自動抽,其餘五類讀各自正本。冊上沒登 = 新(黃,並先跑所在尾版的 `--selftest`);冊上有、樹上沒有 = 缺(紅)。<br>• 全部 CGC 家族尾版(250 支)在記憶體 compile,並檢加速器橋。<br>• 更新過的尾版(紀錄冊比 sha)自動跑 `--selftest`,之後生成的指令也會進流程。<br>• 紀錄冊只增,記版本 · sha16 · UTC 時間 · 燈;CRLF 當 LF,工作站 autocrlf 不會被當成變更。<br>• 沿用:相依指紋同 + 上次綠 + 24 小時內。`--quick` 給 AI 進場用。<br>• 防遞迴 | 自測 10/10 |
| `CGC_MDL149_VeritasCentralGovernanceConsole_v0180.py` | • `test` 改走 MDL224 尾版(v0160 把門釘死在 v0100)。<br>• `enter` 在 go 前先跑 `test --quick`;`--card`(AI 進場)也跑;串測紅 → 入口紅;串測中不遞迴。<br>• `help` 的「目前生效入口」修回尾版:v0177 把目錄接到自己,v0178 / v0179 沒接回,一直印 v0177 | 本版 6/6 · 前版鏈 `[交接入口] fail=0` |
| `VIA_VCGC_FunctionLedger_v0100.jsonl`(新,只增) | baseline 295 項:250 家族尾版 · 5 本冊 · PS 入口 · 39 動詞。`.gitattributes` 設 `merge=union`,多分支同時追加不衝突 | 第一次整輪寫入 |
| 需求冊 v0108 · VCGC 工作流冊 v0105 | +VCGC-REQ085;WKF001-STP008「VCGC 全功能串測」(正主 CGC_MDL224 尾版) | SDD(見第四節) |
| 功能卡 · CLAUDE.md · 交接冊 · 席位冊 | • 功能卡:必用第 4 步 `test --quick`(handoff 之後),禁令加「新指令要登盤點冊」,門加 test。<br>• CLAUDE.md 加同一步。<br>• 交接冊:新 case `chain`,工作項 +3(1 件 VERIFIED、2 件帶理由待辦)。<br>• 席位冊 CONSOLE → v0180 | 交接 check / test |
| 掉球帳(只增) | Z286(見第三節) | — |

## 三、盤點實測與首輪串測

**盤點實測**:在容器的乾淨工作樹,逐支經 VCGC 跑 64 支。**沒有一支寫已追蹤檔**。

- 動詞:抽到 40 個,實跑 37 個;另外 3 個分別是 go 別名、不是真動詞、本流程自己。
- rc 2 是黃燈,多為待操作員裁定或容器沒資料:ssot · ssot plan · ssot panorama · sdd · inventory · check · panorama · dbm。
- `workflow` 單獨跑 rc 1:整輪符合性要 go 的事件才判得出來,本站只驗「動詞可用」。

| 指令(經 VCGC) | rc | 秒 | 寫已追蹤檔 |
|---|---|---|---|
| `token` | 0 | 4.2 | 0 |
| `functions` | 0 | 0.2 | 0 |
| `help` | 0 | 37.8 | 0 |
| `status` | 0 | 10.6 | 0 |
| `handoff check` | 0 | 2.5 | 0 |
| `sync-check` | 0 | 2.9 | 0 |
| `ssot` | 2 | 7.4 | 0 |
| `ssot plan` | 2 | 7.1 | 0 |
| `ssot panorama` | 2 | 13.4 | 0 |
| `sdd` | 2 | 3.2 | 0 |
| `val` | 0 | 1.6 | 0 |
| `workflow` | 1 | 0.7 | 0 |
| `events 5` | 0 | 0.7 | 0 |
| `registry-sync` | 0 | 2.0 | 0 |
| `matrix --no-tests` | 0 | 1.6 | 0 |
| `inventory` | 2 | 48.6 | 0 |
| `sync` | 0 | 2.4 | 0 |
| `check` | 2 | 2.3 | 0 |
| `audit` | 0 | 2.8 | 0 |
| `panorama` | 2 | 3.3 | 0 |
| `page` | 0 | 11.0 | 0 |
| `onepage` | 0 | 11.5 | 0 |
| `register-plan` | 0 | 3.1 | 0 |
| `layout --selftest` | 0 | 0.9 | 0 |
| `support` | 0 | 1.9 | 0 |
| `books` | 0 | 2.0 | 0 |
| `lexicon` | 0 | 1.9 | 0 |
| `ledger` | 0 | 2.0 | 0 |
| `probe` | 0 | 1.8 | 0 |
| `systems` | 0 | 5.2 | 0 |
| `dbm` | 2 | 0.8 | 0 |
| `door` | 0 | 0.9 | 0 |
| `tools` | 0 | 1.4 | 0 |
| `selftest` | 2 | 1.8 | 0 |
| `test` | 0 | 13.6 | 0 |
| `enter --card --no-pull` | 0 | 12.5 | 0 |
| `chain` | 0 | 10.8 | 0 |
| `run --family core CGC_MDL238_OperatorConsole --selftest` | 0 | 2.6 | 0 |
| `run --family core CGC_MDL240_EnvManager --selftest` | 0 | 1.8 | 0 |
| `run --family core CGC_MDL243_TalibCommandScan --selftest` | 0 | 1.3 | 0 |
| `run --family core CGC_MDL242_PathVerify --selftest` | 0 | 3.8 | 0 |
| `run --family core CGC_MDL058_Lessons --selftest` | 0 | 1.3 | 0 |
| `run --family core CGC_MDL124_BridgeSweeper --selftest` | 0 | 1.4 | 0 |
| `run --family core CGC_MDL207_PolicyRun --selftest` | 0 | 1.3 | 0 |
| `run --family core CGC_MDL205_TalibBan --selftest` | 0 | 1.5 | 0 |
| `run --family core CGC_MDL220_SuccessLedger --selftest` | 0 | 1.3 | 0 |
| `run --family core CGC_MDL217_ManagerMatrix --selftest` | 0 | 1.2 | 0 |
| `run --family core CGC_MDL221_SystemBackup --selftest` | 0 | 1.8 | 0 |
| `run --family core CGC_MDL222_SubsystemProbe --selftest` | 0 | 1.6 | 0 |
| `run --family core CGC_MDL223_FlowConsistency --selftest` | 0 | 1.9 | 0 |
| `run --family core CGC_SystemManager --selftest` | 0 | 1.5 | 0 |
| `run VDF_SystemManager --selftest` | 0 | 4.4 | 0 |
| `run --family core SUP_MDL866_VIAUnifiedNLPOrchestrator --selftest` | 0 | 1.3 | 0 |
| `nlp` | 0 | 1.0 | 0 |
| `matrix --ids via_functional_acceptance --no-tests` | 0 | 1.7 | 0 |
| `matrix --ids via_ssot_autocode --no-tests` | 0 | 1.7 | 0 |
| `matrix --ids via_accelerator_control --no-tests` | 0 | 1.6 | 0 |
| `matrix --ids via_unique_entry_control --no-tests` | 0 | 1.7 | 0 |
| `matrix --ids vrn_dispatch --no-tests` | 0 | 1.6 | 0 |
| `matrix --ids vdf_dispatch --no-tests` | 0 | 1.7 | 0 |
| `matrix --ids quantguard_dispatch --no-tests` | 0 | 1.8 | 0 |
| `matrix --ids via_panorama_audit --no-tests` | 0 | 1.8 | 0 |
| `matrix --ids via_unified_nlp --no-tests` | 0 | 1.7 | 0 |
| `matrix --ids vrn_nlp_vrn_vdf_pipeline --no-tests` | 0 | 1.9 | 0 |

**首輪整輪 `test --full`**(未登錄前):74 站中綠 60 · 黃 9 · 紅 4;家族尾版 250 支 compile 錯 0 · 缺橋 0。紅 4 站:

- `V-sdd` · `V-inventory`:本批新檔還沒註冊、還沒編號(X-REG / X-NUM)。登錄後重跑,結果見第四節。
- `L-backup` · `S-vcgc-manager`:**既有問題 Z286**。`CGC_MDL221_SystemBackup` 自測只要 `VIA_Reports/vdf_chain/VDFCHAIN_latest.json` 存在,就判 `chain_file` 失敗;`CGC_SystemManager` 自測連帶紅。
  - 乾淨工作樹是綠的;跑過 VDF 鏈的機器(本容器 9/29 · 工作站)一律紅。
  - 這是串測抓到的真問題。照「範圍不發散」本段不修,列交接待辦 `VCGC-REQ085:backup-stale`。
- 黃燈照實保留(黃不是綠),包括 PS 入口站「待辦:v0108 還沒出」。

## 四、登錄與收尾實測

- **註冊**:registry-sync --apply(新 35 · 變更 13;之後修正兩次各 1)。新時間都寫 UTC。
- **編號只登本批**:+59 列。audit 基準 main 95acadf49:101,705 → 101,764 · 遺失 0 · 改身分 0 · 重號 0 · 註冊完整性六檢全 0。
- **SDD**:只剩既有的黃燈,X-REQ-OPEN 19(含本批 PARTIAL)與 X-LOCK 6。
  - 中途抓到一個錯:REQ085 歸屬放了 .py 檔名,X-REQ 紅。v0108 還沒發布,直接修正。
- **交接**:10 案(含新 case chain)全部 rc 0。checkpoint 後 `handoff check` GREEN(findings 0),驗收燈 YELLOW。
  - 中途抓到三處冊寫法錯,已修:工作項少 receipt · managed_modules 放了 glob · json 放進 managed_modules。
  - v0180 原本也定義 `show_current_help`,元件冊就把這函式的來源從 v0177 移走,交接冊管的 v0177 變成「未註冊」。管理範圍只增不減、不能拿掉 v0177,所以改名成 `_show_help_v0180`。
- **最終整輪 `test`**(登錄後):76 站,綠 64 · 黃 9 · 紅 3,其中 61 站沿用。
  - 盤點 動詞 40/40 · 席位 6/6 · 必用卡 13/13 · 交接案 10/10 · 工作流步 39/39 · PS 1/1。
  - 家族尾版 250 支:compile 錯 0 · 缺橋 0 · 更新 2(v0180 · MDL224 v0101 都自動跑了自測,綠)。
  - 紀錄冊 +5 行(三本冊 · 兩支尾版,各帶版本 · UTC 時間 · 燈)。
  - 中途抓到並修正:動詞項沒有 sha,空值與缺欄被判成不同,每輪都誤記「changed」。自測 ⑤ 補了這一格。
- **紅 3 站照實**:
  - Z286 兩站:`L-backup` · `S-vcgc-manager`。
  - `V-inventory`:讀到本容器 9/29 的格子存證(`VIA_Reports` 本機、不入 git),棘輪退步 20。乾淨工作樹沒有存證 = NODATA 黃,不是本批造成。
- **併 main(PR #380)後**:#380 加的 `CGC_MDL209_VdfStart_v0101` · `VDF_SystemManager_v0120` 沒有任何交接案涵蓋,也沒註冊,main 自己的 `handoff check` 就是紅(CI 最後一步會紅)。
  - 本批帶進的修補:交接冊加 case `vdfstart`(`CGC_MDL209_VdfStart --selftest`,會載 VDF 管理器尾版),工作項 `VCGC-REQ085:base-380` VERIFIED。
  - 同時做了 registry-sync,並用明列這兩檔的 `--scope` 編號:+15 列。
  - 11 案 rc 0,`handoff check` GREEN;audit 基準 main 0cf6ddfa1:101,705 → 101,781 · 遺失 0 · 改身分 0 · 重號 0。
  - 最終整輪 76 站:綠 64 · 黃 9 · 紅 3(同上 3 站)。#380 的 MDL209 v0101 被當成「更新的尾版」自動跑自測(綠),紀錄冊 +4 行。
- **總控頁**:新尾版說明變了,在乾淨工作樹重產,合約 19/19。
- **帳本** +1365。

## 五、交接(下一手照做)

1. 進場:`token` → `functions` → `handoff check` → **`test --quick`**(新的必用第 4 步)。
2. 下一段 `VCGC-REQ085:ps-entry`:出 `Invoke-VIA-OperatorConsole-v0108.ps1`,v0107 一字不動;操作員本令即 L70 逐次許可。
   - ①a 省 Token 之後加「①g VCGC 全功能串測」:console `test`,`-Full` 時帶 `--full`;紅 → exit 2。
   - ⑦ 上傳的紀錄冊加 `VIA_VCGC_FunctionLedger_v0100.jsonl`。
   - 盤點冊 P-entry 站就會從「待辦黃」轉成實驗:pwsh Parser 語法 + 串測步在。
   - 容器可在暫存區放 portable pwsh 7.4.6 實跑。
3. `VCGC-REQ085:backup-stale`(Z286):出 CGC_MDL221 新版修比法。
4. 新增 / 換版任何 VCGC 指令或模組之後:跑 `test`(整輪,沒變的站沿用)。新指令登進盤點冊新版號;紀錄冊的新行要一起提交。

## 六、跟進:Codex 對已併 PR #378 的四條審查(新版號檔修,前版不動)

| 審查 | 成立? | 修法 |
|---|---|---|
| P1 沒有 origin/main 的檢出,`base_ref()` 退回 HEAD → `--apply --scope` 回「範圍 0 檔」當成功 | 成立 | `CGC_MDL237_NumberingSystem_v0110`:`real_base()` 依序找 origin/main → main → origin/HEAD;都找不到就拒跑 rc 2、一列不寫(可給 `--base <ref>` 或明列檔);`scope` 乾跑也標出基準真假 |
| P1 `--apply --scope <檔…>` 明列檔時 dirty 設成空 → 未提交的明列檔照樣發號 | 成立 | 同版:明列檔也算 dirty,未提交的擋下並列出;全都未提交 = rc 2 |
| P2 名冊第二次啟用起 prior 不前進(v0104 的 prior 停在 v0102) | 成立 | `CGC_MDL233_ToolActivate_v0105`:`roster_next()` 一律把 prior 設成直接前版 |
| P2 席位 0 列也放行 → 鎖冊換了卻沒有現役指標 | 成立 | 同版:席位檢查改「恰一列」;實冊六家每家正好一列 |

自測:MDL237 v0110 本版 5/5(v0109 · v0108 鏈照過)· MDL233 v0105 +4/4(v0100–v0104 鏈全過;v0104 ㉖ 的本體身分斷言照原樣跑完再換裝本版)。

## 七、第二段:唯一 PS 入口串上串測(VCGC-REQ085:ps-entry)

操作員令「go on」:接著做 `VCGC-REQ085:ps-entry`。

| 檔 | 做什麼 |
|---|---|
| `Invoke-VIA-OperatorConsole-v0108.ps1` | ①a 省 Token 之後加「①g VCGC 全功能串測」:經主控台跑 `test`(`-Full` → `test --full`);總判紅或沒有總判行 → 整輪 exit 2;紅站與「新 / 缺」各列前 12 行。⑦ 上傳的紀錄冊多帶 `VIA_VCGC_FunctionLedger_v0100.jsonl`。v0107 一字不動 |
| `CGC_MDL224_TestAuto_v0102.py` | 實跑抓到的兩個串測引擎缺陷(掉球帳 Z287,同段結):① 版號同時認 `_vNNNN` 與 `-vNNNN`(PS 入口站不再誤判 ABSENT;紀錄冊記到 PS 入口版本)② 串測期間自開 `test-…` 輪號,入口輪記在報告 `hub` 欄(回傳與 `TEST_latest.json`),跑完還原。v0101 不動 |

### pwsh 實跑(portable pwsh 7.4.6,乾淨工作樹 · 隔離資料夾 · `-SkipSweep -NoOpen -NoUpload -NoBuild`)

| 輪 | ①g 串測 | 工作流(操作台 go 輪) | PSRC |
|---|---|---|---|
| 第一輪(v0101 引擎) | 紅 1:P-entry「ABSENT Invoke-VIA-OperatorConsole-v*.ps1」 | **紅**:事件 89 · 不在冊上的步 61 · 順序紅 6(「H3 宣告在 H4 之前,實跑在後」…)—— 串測 75 站的事件記進了 go 輪 | 2 |
| 第二輪(v0102 引擎) | P-entry **綠**(pwsh Parser 過 · 串測步在);紅 1 = V-sdd,只因實跑樹是複本、v0102 沒在那棵樹登錄(主樹已登錄) | **黃**:事件 17 · 不在冊上的步 2 · 順序紅 0;黃 = H6 / D1 / D2 / R2 本輪沒跑(`-SkipSweep`、沒建庫) | 2 |

- 兩輪的 ⑥ 單一路徑驗證都是 rc 2,v0107 就有,不是本段造成的。
- 這一段只證明 ①g 接上了、以及兩個引擎缺陷修好了,不代表整條操作台綠燈。
- 主樹整輪串測沒設 `VIA_PWSH` 時,P-entry 照實黃(「沒有 pwsh:語法沒量」,不冒充綠);設了 `VIA_PWSH` 才驗 pwsh Parser。

## 八、第三段:收尾 VCGC(Z286 · VCGC-REQ085:backup-stale)

操作員令「收尾VCGC」。REQ085 最後一條待辦是 Z286:備份自測在跑過 VDF 鏈的機器上一律紅,串測 L-backup · S-vcgc-manager 兩站跟著紅。

根因:鏈跑器在計畫模式(`mode: plan`)和真跑都會寫 `VDFCHAIN_latest.json`。v0100 要防的是「照計畫寫出報告」(do_not 第一條),但它分不出兩種,只要檔在就判失敗。

| 檔 | 做什麼 |
|---|---|
| `CGC_MDL221_SystemBackup_v0101.py` | 讀鏈報告的 schema 與 mode:schema `VIA.VDFChain.v1` · mode 以 run 開頭 · 有 stages 與 generated = `RAN_AFTER_BACKUP`,鎖定照成立,卡片標 `stale` 並寫「要重備」(不自動改冊);plan · 非鏈跑器 · 讀不到 = 照 v0100 判 `chain_file`。自測 6/6(五種報告情境 + 實樹);v0100 不動 |
| `CGC_SystemManager_v0111.py` | `backup` 走 v0101(v0110 把 v0100 釘死);其餘照 v0110。席位冊 VCGC → v0111 |
| 盤點冊 `VIA_VCGC_FunctionInventory_SSOT_v0101.json` | 交接案 `backup` 的覆蓋指到既有站 L-backup(同一支自測);其餘一字不動 |
| 需求冊 `VIA_Requirements_SSOT_v0109.json` | VCGC-REQ085 PARTIAL → COVERED,理由 = 三個交接工作項都 VERIFIED;其餘 110 條不動。v0107 仍被 PR #379 占用 |
| 交接冊 | 新案 `backup`;工作項 `VCGC-REQ085:backup-stale` → VERIFIED |
| 掉球帳 | Z286 以只增結案列結案 |

驗收燈 `closeout_lamp` 另計;交接 GREEN 只代表交接資料完整。

## 九、第四段:整合全景實測一鍵 PS(VCGC-REQ086)

操作員令(逐字):「先把這個面檢視實測的工具整合為一」「給我一個整合後的POWRESHELL跳書HTML報告如今天清晨」「請加入PS加速器模板並檢查系統中的引擎都有加入最新版加速器 VDF加入最新的網路工具 從VCGC VDF VRN提供這個PS指令我自己貼上去跳出HTML U/I如今天早上 熱PS去跑 請提供一個整合後指令」「跑完直接開PR合併給我指令」。

| 檔 | 做什麼 |
|---|---|
| `launchers/Invoke-VIA-FullCheck-v0100.ps1`(新) | 一鍵:模板接法(CELERITAS-TEMPLATE-JOIN + Celeritas 正主)· PS 25 加速器橋 · 只經 Invoke-VIAPython 叫 VCGC;跑完跳出 `VIA_Reports\fullcheck\FULLCHECK_latest.html`。參數 `-Full`(全部重量)· `-Grid`(自測格子整張重跑)· `-NoOpen` · `-Only 0,5` · `-SystemDir`;結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件 |
| `CGC_MDL248_FullCheck_v0100.py`(新) | 六段依序、紅了照跑:⓪ 三橋覆蓋與最新版(CGC_MDL124 乾跑 + 載入版 vs 樹上最新)→ ① VCGC 串測 → ② SSOT 全景 → ③ 單一路徑驗證 → ④ 自測格子(預設讀存證並標時間,`-Grid` 才重跑)→ ⑤ 交接(讀 check 輸出行)。燈讀各正主本輪報告,沒更新的照紅;每段 + 總判只增寫 `VIA_VCGC_FullCheck_Ledger_v0100.jsonl`(UTC · 尾版 · 版號 · sha16 · 秒數 · HEAD)。自測 9/9 |
| 三橋補缺(Z288) | VDF 網路橋 131/131 · PS 25 加速器橋 928/928(73 支尾版經橋掃 `--apply` 補上)|
| 冊 | 需求冊 v0110(+VCGC-REQ086)· 盤點冊 v0102(站 C-fullcheck)· 交接冊(案 fullcheck · 工作項 VCGC-REQ086:fullcheck)|

pwsh 實跑(容器,-NoOpen):六段跑到底,296.9 秒。⓪ 三橋 綠(ACCEL 1628/1628 · NET 131/131 · PS-ACCEL 928/928 · 載入 = 最新)· ① 串測 紅 1(V-inventory 棘輪:昨天格子 FAIL 24)· ② 全景 黃(紅 0)· ③ 單一路徑 紅(容器沒跑 go 的路徑步;版本 72 支全齊)· ④ 格子存證 36 小時前 FAIL 24 · ⑤ 交接。實跑中抓到本支自己的缺陷:`handoff check` 紅時不重寫 HANDOFF_latest.json,第 ⑤ 段誤判「報告沒更新」→ 改讀 check 的輸出行(自測 ⑨),`--only 5` 實跑確認 9 條 findings 全列。

操作員端一行指令(倉根,Windows PowerShell 7):

```powershell
git pull; pwsh -NoProfile -ExecutionPolicy Bypass -File .\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-FullCheck-v0100.ps1
```

## 十、CI「VIA Master Control UI」反覆紅:根因與防法

| 次 | 現象 | 根因 |
|---|---|---|
| main #998(PR #380) | `handoff check` 紅 | 新尾版沒有交接案涵蓋就併進 main(當時補:案 vdfstart) |
| main #1005(PR #383) | `handoff check` 紅 16 條(收據失效 · 改過沒測 · fullcheck 收據不在) | PR 在本分支**收尾做到一半**時被合併(393425bab = 註冊同步那一步;收據與 checkpoint 還沒提交) |
| 分支各中間推送 | 同上 | 收尾每一步都推送,中間狀態本來就紅 |
| PR #384(run 36723641938) | 合約測試 test_22 `ConnectionAbortedError [WinError 10053]`(交接已綠) | DeckServer 拒絕 POST 時沒讀掉請求本文就關連線,Windows 送 RST(時序競態;Z289)→ `CGC_MDL095_DeckServer_v0161` 拒絕前先讀掉本文 |

防法:
1. AI 端(本段起照做):收尾在本機全部跑完(註冊 → 編號 → 稽核 → 交接各案 → checkpoint → check 綠 → 整輪串測),**才一次推送**;中途不推。
2. 倉庫設定(操作員的手):GitHub → Settings → Branches → `main` 開「Require status checks to pass before merging」,勾 `Windows bundled Chromium UAT`。開了之後 CI 紅就按不了合併,半成品進不了 main。
3. 本段修復:分支接回合併後的 main(只剩編號與收據兩個提交沒進 main),補齊後一次推送、新 PR 綠了才合併。

## 十一、第五段:PS 自擋開頁(Z290)· 整合全景實測 PS v0101

操作員原話(逐字):「這個ＰＳ指令一定沒有加加速模板自動跳出ＨＴＭＬ」

**實測屬實。** 容器 portable pwsh 7.4.6、不帶 `-NoOpen` 跑 `Invoke-VIA-FullCheck-v0100.ps1 -Only 0`:頁有產出,但最後一行是「[VIA_NO_OPEN] 抑制跳出 …FULLCHECK_latest.html」——沒跳出。第九節的實跑都帶 `-NoOpen`,開頁那段從沒被跑到;需求冊 REQ086 證據寫「跳 HTML」不成立(v0112 更正)。

根因:v0100 為了不讓引擎各自跳頁先設 `VIA_NO_OPEN=1`,到 finally 才還原;同一行程的 PS 加速器模組(PS-ACCEL 橋 · `VIA_PS_PyProgress_Module` · 命令冊都會載)從批366 起裝了全域的 `Invoke-Item` / `Start-Process` 代理(零跳出閘),看到 `VIA_NO_OPEN=1` 就把 .html 目標靜默略過 → 自己的總報告也被吃掉。

| 項 | v0100 | v0101 |
|---|---|---|
| 跳頁 | 不跳(被自己的 `VIA_NO_OPEN=1` 擋) | 跳:`Microsoft.PowerShell.Management\Invoke-Item`(帶模組名,不經代理);假 xdg-open 收到頁(`pwsh -File` 與熱 PS `&` 兩式) |
| 呼叫端自己設 `VIA_NO_OPEN=1` | 不開、不說 | 照守不開,印黃字教怎麼開 |
| 加速模板 | 點源 Celeritas 正主 · 只印版號 | 全樹標準 `[VIA:PS-TEMPLATE:v0101]` 模板塊(646 支同一段)· 開跑印 版號 · 已套用 · 執行緒 · 優先權 · 結尾 MATRIX SUMMARY(六段燈 · 秒數 · 摘要) |
| 輸出 | 整輪跑完才一次印 | 邊跑邊印(上色) |
| 熱 PS 用 `&` 跑 | 結尾一律 Restore(連視窗自己套的也還原) | 只還原本支套上的;`VIA_NO_OPEN` / `VIA_FROM_VCGC` / `VIA_VCGC_PUSH` / 資料夾原樣還原(實測優先權 Normal → Normal) |

防再犯:`CGC_MDL248_FullCheck_v0101` 的 ⓪ 段多一項「PS 自擋開頁」—— PS 尾版(家族最新;不含 VIA_Reports / history / intake)裡自設 `VIA_NO_OPEN=1` 後、沒先換回原值就用不帶模組名的 `Invoke-Item` / `Start-Process` / `ii` 開頁 → 紅並點名檔 · 行;明寫判斷 `VIA_NO_OPEN` 的(VIA.ps1 零跳出律)不算。自測 5/5 + 前版 9/9。

全樹掃出的同病尾版(⓪ 段每輪點名):

| 檔 | 行 | 處置 |
|---|---|---|
| `Invoke-VIA-OperatorConsole-v0108.ps1`(唯一入口;v0100 起每一版都是) | L400 ①e 模板預覽 · L665 結尾簡單版驗證頁 | 新版 v0109 已備妥(同一個 `Open-VIAOwnPage` · finally 還原;其餘一字不動),**.ps1 要操作員 L70 逐次許可**(擊斃閘 KILL-05)→ 交接待辦 `VCGC-REQ086:console-runall-own-page` |
| `Invoke-VIA-RunAll-v0102.ps1` | L258 多頁矩陣 | 同上(v0103 已備妥) |
| `launchers/Invoke-VIA-GitHubFirst-Closeout-v0100.ps1` · `launchers/Invoke-VIA-VCGC-CloseoutChain-v0100.ps1`(PR #386) | L409 · L338(還原寫在開頁下一行) | 另一個 session 仍在活動,不就地出版;兩支也缺 PS-ACCEL 橋 → 交接待辦 `VCGC-REQ086:closeout-own-page` |

附帶抓到(Z291):`registry/VIA_PS_Accelerators_25_Roster_v0100.ps1` 是被加速模組點源的函式庫,卻帶整段模板塊(開頭 `$VIACelTplOwn = $false`)→ 把呼叫端「本支套上」旗標蓋掉,結尾不還原(等 PowerShell.Exiting 才還原)。FullCheck v0101 先在自己檔內另存旗標繞過;根治要動全樹共用的載入點,待操作員許可。

擊斃閘 `CGC_MDL187 v0103 --base origin/main --run-selftest`:rc 0 · 許可 1(P012:FullCheck v0101 · 釘 sha256)· 債 1(薄尾委派前版自測)。

收尾:(本段收尾數字見下一行)

操作員端(熱 PS 直接貼,站在倉內任何資料夾;PowerShell 7):

```powershell
git pull --ff-only
$f = (Get-ChildItem (Join-Path (git rev-parse --show-toplevel) 'VeritasIntelligenceAnalytics\launchers\Invoke-VIA-FullCheck-v*.ps1') | Sort-Object Name | Select-Object -Last 1).FullName; if ($PSVersionTable.PSVersion.Major -ge 7) { & $f } else { pwsh -NoProfile -ExecutionPolicy Bypass -File $f }
```

PowerShell 7 的視窗就在本視窗跑(熱 PS · 模板只動本行程、跑完還原);Windows PowerShell 5.1 自動改叫 pwsh 子行程。參數照加:`& $f -Full` · `-Grid` · `-NoOpen` · `-Only 0,5`。
