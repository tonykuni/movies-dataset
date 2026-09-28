# VIA 進度表 · 2026-09-28 操作員裁定落地(每步一個還原點,推 GitHub 即更新)

側線 2026-09-28(主線批號由併線的手指定 L25)· 分支 `claude/vcgc-vrn-read-forward`。
操作員裁定:① 依擬建議(P1–P7 依建議順序套)② Z218 批345 正本**退役** ③ 加速器 / 網路工具 / layout 一律用**最新版**;附件(Gemini 對話)「適度採用、不大幅修正」,過時或與樹不符者不採用。

還原方法(任一步都可退):`git checkout <還原點 SHA> -- <檔>`,或整批 `git revert <該步 commit>`;不用 force、不用 Remove-Item。

| 步 | 內容 | 還原點(做之前的 HEAD) | 狀態 | 證據 |
|---|---|---|---|---|
| R0 | 起點(PR #327 已併;本分支多 3 筆紀錄 commit) | 83613315 | — | — |
| R1 | P7:`.gitattributes` 補三支原位元 sha 鎖的 `-text` | 83613315 | 完成 | `git check-attr text` 三支 unset、對照檔 unspecified |
| R2 | P1:`__future__` 橋位三支新版號(SUP_MDL749 v0115 · VDF_ENG088 v0104 · CGC_MDL180 v0101)+ P4:VRN 邏輯索引冊 build | 5cd370c2 | 完成 | MDL749 v0115 50/50 · MDL180 v0101 7/7;邏輯冊 53/53 過期 0;status SSOT 連動 BROKEN 4→0(YELLOW 7 · GREEN 5)、邏輯庫 RED→OK、VRN 系統管理 RED→STALE/NODATA |
| R3 | P2:`VIA_SYSTEM_MANAGER_v0150`(在自己的 namespace 跑 v0148 本體 + v0149 拔 TALib 鍵;模組層覆寫 OUT/TEMPLATE_OUT 生效)+ 追蹤頁 `VIA_UI_MasterControl_v0100.html` 依正主重生(test_11) | c8594d1c | 完成(容器);CI 待推送後量 | `test_master_control_contract_v0102` 容器 19 測 OK(原 4 測 setUpClass 就炸)· v0150 --selftest rc0 十檢 10/10 · v0148 與 v0150 產頁逐字同(146 族、486 個「正式名稱待治理」)|
| R4 | Z218 退役:基線冊 `immutable_b345.retired_20260928` + `CGC_MDL183_CeleritasPolicyGate_v0101`(只改 ⑤) | 6b10cc50 | 完成 | v0101 --selftest 8 檢 OK 8 · FAIL 0(原 7/1);[PS ] 基線外新缺 0;[PY ] 缺橋 91 照舊(Z223) |
| R5 | Z230 用最新版(layout v0109 · 既有加速橋 · 網路 v0117/v0116)+ P6 主控台 v0162(`layout --selftest` 走樞紐)+ 附件適度採用:全景 v0114 多 COMPILE / TAILAPI 兩類 + 沙盒驗收測試 + layout 登冊 | 70db2d47 | 完成 | v0162 `layout --selftest` → 樞紐 v0109 [OK] rc0、status 照舊;全景 v0114 正控(MDL749 v0114→COMPILE、MANAGER v0149→TAILAPI)負控(v0115、v0150 無);測試 5 passed(unittest 與 pytest);全景自測 43/44(⑭ 與 v0113 同,既有 Z234);layout 登冊 1/5/0 → APPLIED → 0/0/0,元件冊 10995→10996 |

**附件(Gemini 對話)採用對照**:採用 = `__future__` 以 compile 驗(COMPILE)、尾版公開 API 不退化(TAILAPI)、每步還原點、沙盒驗收測試;**不採用**(與樹不符或風險高)= 七支新腳本(`via_ast_bridge_*`、`via_uat_b305_ast_healer`、`via_patch_mdl179_synchub`、`via_ssot_sdd_hydrator`、`via_vcgc_mcp_server`、`Invoke-VcgcMasterGate.ps1`)—— 它們的橋標記(`cross_init`/`clean_for_duckdb_x`/`ScrapeGate`)在本樹不存在,批次注入會把假橋與替身類別寫進幾百支檔;樹上已有正主(via_accel_injector · CGC_MDL183 · CGC_MDL156 · CGC_MDL158),另造 = 第二把尺(L05)。MCP 伺服器、git hook、CI 工作流改動列為之後可議,不在本批。

| 收尾 | 全格子(容器)OK 300 · FAIL 46 → **OK 306 · FAIL 40**(無新紅,6 站轉綠;再生件 stash 未 commit)· PR [tonykuni/movies-dataset#328](https://github.com/tonykuni/movies-dataset/pull/328) 已開(不 approve、不 merge) | e3149646 | 完成 | 主控台 status 會自動提交並推送 SubsystemSeat 同步(57199124);之後量測一律設 `VIA_VCGC_PUSH=NO` |
| R6 | CI 修正:PR #328 的 Windows UAT 只剩 test_11。原因:R5 我把變更說明插在 v0114 / 閘 v0101 docstring 的第一行,總管取名用的是 docstring 第一行,於是 M151 從「PowerShell 代讀誤報修正 治理模組」掉成「正式名稱待治理」;加上 R3 之後的新尾版沒有重生追蹤頁 | 5100abdf | 完成(容器) | 變更說明移到原第一行之後;追蹤頁照正主重生;test_master_control_contract 19 OK · 全景沙盒測 5 OK · 閘 8/8 · layout 登冊 0/0/0 |
| R7 | CI #328 第三輪 + Codex 三條:① VRN_ENG090 v0103 燈號冊改讀最新一版有 LAMPS 的 VRN_SystemManager(尾版 v0108 是薄尾)② VDF_ENG055 v0121 · VDF_ENG077 v0104:ca098982 的兩層薄尾丟了 lane_global / run / unify,新尾在自己的 namespace 跑具體實作 v0118 / v0101 + 同一個 ScrapeGate 換裝 ③ 閘 v0101 ⑧ 改審自己(VERSION v0101、讀 __file__)④ 全景 v0114 TAILAPI 薄尾往回走到具體實作(Codex)⑤ 追蹤頁再重生 | febffe67 | 完成(容器) | 工作流 Python 全段本機過:總管 10/10 · 契約 19 OK · ENG090 23/23 · daily 五支 + ETF 全 OK · 全景測 6 OK · 閘 8/8;TAILAPI 正控抓到 ENG055 v0120 / ENG077 v0103 |

## 第二輪(PR #328 已併;操作員「GO ON」)

| 步 | 內容 | 還原點 | 狀態 | 證據 |
|---|---|---|---|---|
| R8 | Z223 PY 缺橋 91:逐支在所有已追蹤 JSON 冊裡找這支檔的內容 sha / md5 —— 8 支被鎖或證據冊釘住,記進 `py_readonly`(`added_20260928b` 逐支寫明哪本冊);其餘 83 支由正主 `via_accel_injector.inject_py` 補橋,逐支再 `compile()`。另補 R7 漏跑的 `via-vrnbook build`(ENG090 v0103 新尾版讓冊過期) | 0add58b5 | 完成(容器) | CGC_MDL183 **整體 GREEN 第一次**(PY 缺 0 · PS 新缺 0 · 自測 8/8);83 支每支只加 14 行;MDL193 九鎖 + SuccessLedger 全 true;沒有封章冊點名這 83 支;CI 工作流 Python 全段 OK;邏輯冊 53/53;status 邏輯庫 OK · VRN STALE/NODATA |
| R9 | Z234 全景 ⑭ 兩條假紅:`tail_contains` 只讀尾版字面,可是 VDF_ENG087 v0104 載 v0103 本體、VIA_SYSTEM_MANAGER_v0150 exec v0148 本體,憑據其實在實際跑的本體裡。新尾版 `CGC_MDL158 v0115`:沿尾版**實際載入**(程式碼字串常數點名 + 有 exec/runpy/importlib/__getattr__)的較舊同族檔往回走到具體實作;markers 在整串找,markers_absent 整串都不得出現;說明/註解只提到舊版不算載入(第一版連註解都跟,把 MDL158 自己也標成薄尾,當場收緊)。v0114 留作版史 | 06b4e5c5 | 完成(容器) | 自測 45/45(⑭ GREEN,新 ⑭b 沙盒);已修冊 tail_contains 九條全 GREEN(F536-PINVER · F537-MGR 由 RED 轉 GREEN,並寫出實際本體);新 pytest `test_panorama_thin_tail_markers_v0100.py` 4/4(連舊 6 條共 10/10);總管/Deck 自測 rc0;契約測 19/19;邏輯冊未變 GREEN;閘 PY 缺 0 |
| R10 | ① Z233:486 處「正式名稱待治理」= 243 列 × 頁上兩處;名稱來源查清(正式名冊 → 候核名冊 → 尾版 docstring 第一行),這 243 支第一行是英文變更說明或無說明。自動回推只救 23 列且含殘句 → **不自動上名**,出工作清單 `docs/VIA_FormalName_Worklist_Z233.md` 候操作員核名。② P5 / Z228:InputConsole 冊補 `central/vcgc_layout_review`(附件 v0104 那一項,逐字)。「格子會洗掉」經實證是誤判(見 P5(結)),沒有產生器要修 | 2af032e2 | 完成(容器) | 整張格子帶寫入稽核鉤子:冊的樹上寫入 0;A/B 其餘站逐字同、EngineBus 72/72;layout 登冊乾跑 0/0/0;契約測 OK · Deck 26/26 · 總管 rc0。格子/主控台重生的 37 件已 stash,未 commit |
| R11 | 操作員令「VCGC/VDF/VRN 左面板參數 · 右面板多分頁(總覽第一、結果最後)· 收集需求的引擎 · 對接制式 U/I 與 synchronizer」→ 新模組 `CGC_MDL227_ConsoleBlueprint_v0100`。參數只從 InputConsole 冊來,引擎在位與 PLAN 只從 EngineBus 來,已修冊交給全景、盤點交給總管,零第二把尺;對接時模板原文零改動,預置契約沿用 VRN_ENG089。設計見 `docs/VIA_Console_Blueprint_Design_20260928.md` | f2ed7917 | 完成(容器) | 自測 13/13;Chromium 實跑零 JS 錯誤 · 手機無橫捲 · 預置 ADDED · synchronizer 停用後中央頁即時隱藏;加速橋由正主注入器補;閘 PY 缺 0 · PS 新缺 0;總管頁重生(模組 236→237);邏輯冊未變;契約測 OK · 總管 rc0 · Deck 26/26 |
| R11b | 操作員問「功能實測結果如何」→ 補一輪瀏覽器功能實測,抓到真 bug:左面板自己拼旗標,對 tw_history 產出 `--range`,ENG064 不認。改成把參數 → 指令的翻譯委派正主 CGC_MDL139 `resolve_argv`(`argv` 唯讀解析 / `run --dry` 乾跑),欄位只給正主會接的鍵 | bc26f1ec | 完成(容器) | 自測 14/14(+⑬ 活樹無 --range);瀏覽器 32/32 零 JS 錯誤;終端實跑頁面產生的指令:READY / BAD_PARAM / --ticker 三態都對,零寫入 |
| R12 | 資料庫管理 P1+P2 + 三項計畫(操作員裁定:開工 · 三項 · `_repo_` = 對帳副本):新模組 `CGC_MDL228_VIADBManager_v0100`(門面:目錄只讀 DataHome 一頁 · 三態與普查同尺 · 核對冊上期望 · 匯出 csv/gsheet 委派 ENG045、另補 Big5/MD/JSON/parquet · 三項計畫只出計畫)+ VCGC `CGC_MDL149 v0163` `dbm` 路由 + 主控台 `CGC_MDL227 v0101` DB 家族與資料庫分頁 | d5991565 | 完成(容器) | MDL228 自測 15/15(沙盒家用正主 catalog 產目錄;正庫檔修改時間前後一致);主控台 15/15;瀏覽器 15/15 + 33/33 零 JS 錯誤;契約測 OK · 總管 rc0 · Deck 26/26 · 閘 PY 缺 0;總管頁重生;**真數字要工作站 `via-datahome catalog -Tables` 後才有**(容器無正庫,資料庫分頁照實 NODATA) |
| R13 | 工作站首跑實量(目錄 2026-09-28 11:16:58:正庫 5 · 對帳副本 2 · 71 表 · 15,783,873 列 · 湖 30 夾 806 檔 · 壞檔 21;核對 RED 2 · AMBER 31;計畫 壞 21 · mega 20 · raw 3)抓到的修正 → `CGC_MDL228 v0101`:① PowerShell 把 `--cols a,b,c` 拆成三個參數,v0100 默默只匯 1 欄 → 收齊、多餘字與不認得旗標一律擋;② 政策同步表(寫入者 VRN_ENG082)依 L14 在每本庫都有 → GREEN,不報冊外(16 條雜訊);③ plan 印精簡摘要;④ 新動詞 `ui` 以同一份目錄重建主控台 | 06bc7064 | 完成(容器) | 自測 18/18;主控台 15/15;VCGC v0163 路由到 v0101;契約測 OK;閘 PY 缺 0 |

**教訓(R13)**:PowerShell 會把沒加引號的 `a,b,c` 當成陣列傳給程式。凡是逗號清單型的參數,CLI 都要收齊多個字;多出來的字一律擋下,不能默默吞掉。

**教訓(R11b)**:凡是「參數 → 指令」,先找正主翻譯器(CGC_MDL139 `resolve_argv`)。自己拼旗標,就是第二把尺(L05),實測當場就錯。

**教訓(R10)**:stash 格子重生件時要**逐檔點名**,不要整批收;不然自己手改的檔會被一起收掉,再誤判成「被格子洗掉」。

**教訓(兩次了)**:開新尾版的同一個 commit 裡,一定要跑 `via-vrnbook build`;新尾版如果會出現在 MasterControl 頁上,追蹤頁也要重生。不然 status 的邏輯庫會變紅,CI 的 test_11 也會紅。
