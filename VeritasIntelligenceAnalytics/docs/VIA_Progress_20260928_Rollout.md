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
