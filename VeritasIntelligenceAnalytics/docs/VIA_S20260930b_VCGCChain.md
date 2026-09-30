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
