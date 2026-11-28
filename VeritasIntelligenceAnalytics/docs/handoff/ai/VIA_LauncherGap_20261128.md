# 啟動器缺口表(GOVERNANCE-ADDENDUM Step 3–4 · 2026-11-28 · 唯讀盤點)

來源:操作員 2026-11-28 附錄 §3 / §4 / §5 / §6 與 Step 3–4;CLAUDE.md 同日附錄與待裁定 11–14。
取證方式:token `read` 骨架卡 + 語法樹抽動詞(比較式裡的單字串、`VERBS` 常數、`add_parser`),不整檔讀。
燈:綠 = 現有件已做到;黃 = 有但不完整;紅 = 沒有;灰 = 只能在主機上驗。容器結果,未在主機實跑。

## 一、短指令對照(附錄要的九個 → 現有件)

| 附錄短指令 | 現有件(尾版) | 燈 | 缺口 |
|---|---|---|---|
| `boot` | `docs/handoff/ai/VIA_HostBoot_v0110.py`(11 版)· `VCGC_CommandHub_v0122` 的 `via-run`(VDF launch → VRN MDL260) | 黃 | 沒有「降壓 → 三道 → 備份 / 環境 → 遠端狀態」的單一流程;HostBoot 與 Hub 各做一段 |
| `scan` | `via-pano` / `via-panorama`(Hub)· `CGC_MDL158` `read` / `pack` | 綠 | — |
| `fix` | `CGC_MDL158 fix`(先乾跑,再 `--apply`) | 綠 | — |
| `audit` | `run CGC_MDL237_NumberingSystem audit` · `VIA_ReworkGuard_v0104 check --fetch-prs` | 綠 | — |
| `backup` / `restore` | `via-bak`(`VIA_DailyBackup_v0105`:`full` · `latest` · `test`) | 黃 | 還原動詞沒找到明寫的 `restore`;輪替份數待對第五章「5 份」 |
| `remote` | 無(`VIA_HostBoot_v0101` 只記「雲端連不到桌機 → 桌機跑、交收據」) | 紅 · 灰 | 只能在主機上做;照待裁定 14,先做「只檢查、寫 `remote_control_status.json`」 |
| `test` | `via-vcgc test --quick` · `handoff test <case>` · 各檔 `--selftest` | 綠 | 沒有 pytest 套件可套 `--tb=line -q`;照舊用 `digest` |
| `status` | `via`(Hub,取代舊 `via-status`)· `VCGC_StartupEngine_v0101 status` | 黃 | 兩個入口都叫 status;照「重複功能先併」先 `chain` 定本體 |

統一入口候選兩支:`VCGC_CommandHub_v0122.py`(倉根 · via-* 短令)與 `supportive modules/registry/VCGC_StartupEngine_v0101.py`(start · launch · status · health · lock · plan · resume …)。
附錄要「整合至既有 VCGC_StartupEngine 架構」;Hub 已是操作員在打的入口。動工前先 `chain` 兩家、定誰是本體,再掛動詞,不另做第三支。

## 二、先降壓 → 三道(附錄 §4)

| 要求 | 現有 | 燈 | 缺口 |
|---|---|---|---|
| 執行緒上限環境變數 | `VeritasCeleritas_v1141`(加速器)· `VDF_MDL013` 等 107 檔設 `OMP_NUM_THREADS`,20 檔設 `POLARS_MAX_THREADS` | 黃 | 各系統各設;VCGC 啟動層沒有統一設 |
| 背景行程 below-normal | `VDF_MDL022_SafeParallelLaunch`(v0100 起) | 黃 | 只有 VDF 的啟動器;VCGC 層沒有 |
| 開跑前降壓等靜 | `VRN_MDL260_SafeParallelLaunch_v0103`(固定 3 道、開跑前先降壓) · `VDF_MDL022` | 黃 | 系統層各有,VCGC 統一啟動沒有 |
| 三個獨立子行程 · 各自 PID / 日誌 / 健康收據 | `VIA_FastRun_v0105`(並行 · 每項一行 · 全文 .txt) | 黃 | FastRun 的分組不是附錄的三道(環境備份 · MCP 核心 · 遠端);沒有每道的健康收據檔 |
| 清孤兒程序 | 無 | 紅 · 灰 | 照待裁定 14:只清本啟動器自己記過 PID 的 |
| 長任務防休眠 `SetThreadExecutionState` | 無(0 檔) | 紅 · 灰 | Windows 主機才有;結束要還原 |

## 三、快讀快備份 · 環境 100%(附錄 §5)

| 要求 | 現有 | 燈 | 缺口 |
|---|---|---|---|
| 環境全面檢視 | `via-health`(REQ258 ① 八路檢查) | 綠 | — |
| 依計畫安裝 | `via-install --plan-check` · `--from-plan --yes`(`CGC_MDL056_InstallGate`) | 綠 | 自動補裝見待裁定 13 |
| 指紋快讀(`.dist-info` SHA-256) | 無明寫 | 紅 | 要新增「指紋沒變就沿用上一輪」 |
| `vcgc_env_coverage` · `missing_count` 兩個數 | 無這兩個欄名 | 黃 | `via-health` 收據要加這兩欄 |
| 違禁套件名單 | TA-Lib(現行唯一禁庫) | 黃 | OpenCV / FinMind 見待裁定 13(VRN 現役 `VRN_ENG394_LayoutRestore` 與加速器 v1141 匯入 `cv2`) |
| 原子備份 · SHA-256 · 5 份輪替 | `VIA_DailyBackup_v0105` | 黃 | 輪替份數與 `.sdd_tmp` → `os.replace` 寫法待逐項對 |

## 四、MCP · Graphify · OmniRoute(附錄 §1 · Lane 2)

| 要求 | 現有 | 燈 | 缺口 |
|---|---|---|---|
| 省 Token MCP | `CGC_MDL279_MCPServer_v0107`(`vcgc_read_card` · graphify) | 綠 | stdout 只給協定、診斷走 stderr:待逐支驗 |
| Graphify | `via-graph`(Hub v0122 修過路由)· 只跑本機 AST | 綠 | — |
| OmniRoute | `via-omniroute`(舊名照原意) | 灰 | 不進執行路徑;見待裁定 11 |

## 五、建議分批(每批照 SDD:需求冊 → 工作流冊 → 薄尾新版 → 實測 → 註冊 / 編號 → 收據)

1. 先 `chain` `VCGC_CommandHub` 與 `VCGC_StartupEngine`,定本體(不另做第三支)。
2. 本體加 `boot`:降壓(本行程與子行程的執行緒上限 · below-normal)→ 三道子行程(各自 PID · 日誌 · 健康收據)→ 一行就緒摘要。遠端那一道先只回報狀態。
3. `via-health` 收據加 `vcgc_env_coverage` / `missing_count` 與指紋快讀。
4. `via-bak` 補 `restore` 動詞、輪替份數對第五章。
5. 主機實跑一次端對端,收據貼回;容器結果一律標「容器」。

待裁定 11–14 定案前,第 2 批的遠端與清程序、第 3 批的自動補裝都照「裁定前」那一邊做。
