# VCGC 工具功能矩陣(2026-11-06 · 由 VCGC 自己的冊生成 · 只讀 · 不讀原始碼)

來源:盤點冊 `VIA_VCGC_FunctionInventory_SSOT_v0183`(313 站)· 最新串測收據 `VIA_Reports/vcgc/TEST_latest.json`(test-20261104-164556-2068 · 2026-11-04T16:45 · head afa763f · 總燈 YELLOW · quick 模式只排 10 個 quick 站,其餘沿用 / 沒排)· 工具鎖版冊 `VIA_ToolVersion_Lock_v0100` · 省 Token 啟用收據 · AI 必用卡 `VIA_AI_FunctionCard_SSOT_v0102`。燈:GREEN = rc 0 · YELLOW = rc 2 或閘紅 · 「未排」= 盤點冊有登但 quick 沒跑(`test --full` 才全跑)。

## 0. MCP 現況

VCGC registry 1,568 支 .py **沒有任何 MCP server / client 程式碼**(全文 grep `mcp` 零命中);VCGC 對外只有三種介面:主控台動詞(`VIA_FROM_VCGC=YES python3 CGC_MDL149_… <動詞>`)· PowerShell 操作台(`enter` / `go` · 短令 via-*)· 收據 JSON(`VIA_Reports/**`)。要讓 Manus 這類外部代理接上 VCGC,得新寫一支 MCP server 薄殼把動詞與收據露出去(新範圍 · 本矩陣只記現況);Manus 的 app 頁要登入、容器讀不到。

## 1. 省 Token 工具(token 席位 `CGC_MDL158_VIAPanoramaAuditRepair_v0117.py` · nlp 席位 `SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py` · 啟用收據 2026-10-18 03:21:57 · 6/6 實測)

| 工具 | 做什麼 | 狀態 |
|---|---|---|
| `read` | 骨架卡(.py/.ps1 定義樹;.json 兩層;.jsonl 欄位) | 啟用 · 實測過(收據 6/6) |
| `slice` | 一個定義或一段 JSON 路徑 | 啟用 · 實測過(收據 6/6) |
| `digest` | 日誌只留判決行 | 啟用 · 實測過(收據 6/6) |
| `pack` | 整夾索引 | 啟用 · 實測過(收據 6/6) |
| `--if-etag` | 沒變回 304,沿用上一張 | 啟用 · 實測過(收據 6/6) |
| `chain` | 薄尾版本鏈圖 | v0117 起有 · 不在啟用收據六項內 |
| `brief` | NLP 長文摘要(SUP_MDL866 text --file <檔> --brief) | 啟用 · 實測過(收據 6/6) |

## 2. 鎖版工具席位(換版只經 `tools activate <家族> <檔> --apply`)

| 席位 | 現任 | 冊上說明 |
|---|---|---|
| accelerator | `VeritasCeleritas_v1141.py` | 2026-09-25 side line. The v1.14.0 package still calls _si('talib') and is not the lock. |
| network | `VeritasAegisNexus_v1652.py` | R20c operator 2026-09-28: 全部接新的透過VCGC註冊導入; 1.65.1 body + old-line anti-block ladder and pr |
| layout | `SUP_MDL743_GenericLayoutHub_v0110.py` | VCGC activation |
| nlp | `SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py` | VCGC activation |
| token | `CGC_MDL158_VIAPanoramaAuditRepair_v0117.py` | VCGC activation |
| frame | `SUP_MDL755_VIAPolarsFrame_v0100.py` | 操作員 2026-09-29 令「go on add polars to all necessary engines 記憶體不足可用temp替代用」;Codex #369 P2 修 |
| praddle | `VRN_ENG398_PraddleExtractor_v0100.py` | VCGC activation |
| pdfplumber | `SUP_MDL746_PDFPlumberPlusHub_v0102.py` | VCGC activation |
| ocr | `via_ocr_super_v0102.py` | VCGC activation |

## 3. AI 必用步(VCGC-REQ082 · 照順序)

| 步 | 指令 | 何時 | 做什麼 |
|---|---|---|---|
| 1 | `VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt` | 每次進場第一步 | 啟用並實測省 Token 工具;紅了就停,不讀政策、不開子系統 |
| 2 | `VIA_FROM_VCGC=YES python3 "$V" functions` | token 之後 | 印本卡:必用順序 · 指令 · 何時用 · 禁止 |
| 3 | `VIA_FROM_VCGC=YES python3 "$V" handoff check` | 接手時(換對話 / 換接手者) | 讀交接快照的摘要、待辦、相依變更;不從對話記憶推定已完成 |
| 4 | `VIA_FROM_VCGC=YES python3 "$V" test --quick  →  收尾前 test(整輪)` | handoff 之後(每次進場);新增 / 換版任何 VCGC 指令或模組之後 | VCGC 全功能串測:盤點冊(VIA_VCGC_FunctionInventory_SSOT)逐站跑 · 新指令未登錄 = 黃 · 更新過的尾版自動跑 --selftest · 版本與 UTC 時間寫進 VIA_VCGC_FunctionL |
| 5 | `python3 "$E" read <檔或夾> [--depth N]` | 讀任何約 >200 行的檔或整夾之前 | 骨架卡(定義樹 · AST 問題);.json 看兩層、.jsonl 看欄位次數與首末列 |
| 6 | `python3 "$E" slice <檔> <定義名/Class.method/JSON 路徑>` | 只要改或看其中一段 | 只取一個定義;JSON 路徑 a.b[0] · [-1] · [*] · [鍵=值] |
| 7 | `python3 "$E" chain <家族名/任一版的檔> [--all]` | 改任何薄尾家族(出新版號檔)之前 | 版本鏈圖:誰是本體、前版怎麼接、誰蓋了誰;防薄尾盲點 |
| 8 | `python3 "$E" digest <日誌>` | 看跑測日誌 | 只留判決行;紅日誌誠實回 rc 1 |
| 9 | `VIA_FROM_VCGC=YES python3 "$V" ssot panorama [--full]` | 動到 SSOT / 正則 / 同義字 / 編號 / 命名 / 註冊之前與之後 | 六族 × VCGC → VDF → VRN → SUP 上下單向檢測到底;輸入沒變的格沿用 |
| 10 | `VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL237_NumberingSystem --apply --scope  →  run CGC_MDL237_NumberingSyst` | 程式與冊提交之後(先提交再編號)、編號冊提交之前 | 只登本批(範圍 = 對 main 有變的已提交檔;不帶 --scope 的全量 --apply 要操作員下令)· audit 遺失 · 改身分 · 重號 必須全 0,另查註冊完整性 IMMUT · DUPREG · XCODE · FPST |
| 11 | `VIA_FROM_VCGC=YES python3 "$V" registry-sync  →  registry-sync --apply` | 新增 / 換版模組之後 | 元件註冊冊:先乾跑看新 / 變 / 過期 / 撞號,批准才 --apply |
| 12 | `VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL245_SDDValidator check` | 每批收尾前 | X-* 交叉檢;X-REQ-BACK 需求 ↔ 工作流回指;X-LOCK 換尾版要重驗 |
| 13 | `VIA_FROM_VCGC=YES python3 "$V" handoff test <case>  →  handoff checkpoint` | 每批收尾 | 只重跑相依變更的已宣告測試,收據帶命令 · rc · 標記 · 相依 SHA;保存交接快照 |

## 4. 門(doors)

| 動詞 | 做什麼 |
|---|---|
| `enter [--card] [--no-pull]` | VCGC 自己的入口流程(三系統對等,不是唯一入口;L120):第一步 → 位置 / 更新 → 閘 → 加速器 → 工具版本 → go |
| `go` | VCGC 的 PowerShell 編排(操作台);VDF / VRN 各由自己的 SystemManager 啟動(L120);AI 容器沒有 pwsh 時不冒充跑過 |
| `run <引擎> [參數]` | 經閘與事件紀錄逐項執行任一正主(含 --selftest) |
| `status` | 閘:政策整冊 · 子系統座位 · 加速器 / 網路已接 |
| `sync-check` | 座位 + 註冊冊乾跑 + SDD 檢(同步檢查) |
| `ssot [plan|verify|panorama]` | SSOT 第四扇門:正則 · 同義字逐格委派正主;panorama = 六族四層全景 |
| `matrix` | 冊 × 啟動矩陣 × 引擎四態 × 修復候選(預設 PLAN) |
| `workflow [輪號] / events [筆數]` | 流程符合性 / 真實事件 |
| `tools activate <家族> <檔> --apply` | 鎖版工具換版的唯一路(token · nlp · layout …) |
| `handoff check|checkpoint|test <case>` | 交接防遺漏 |
| `test [--quick|--full|inventory]` | VCGC 全功能串測(盤點冊驅動;enter 與 PS 操作台都跑) |
| `functions` | 本卡 |
| `help` | 用法(help --full 版史) |
| `functions --json → playbooks` | 編號作業手冊:ENV 環境安裝 E01–E12 · 唯一頁 R01–R03 · 單引擎 G01–G04 · 工作站同步 W01–W04(AI 與操作員照號做) |

## 5. 盤點冊 313 站 × 最新串測燈(分類)

### V · VCGC 動詞(主控台指令)(42 站 · GREEN 4 · YELLOW 1 · 未排 37)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| V-token | 省 Token 第一步 | `token` | GREEN | 0.8 |
| V-functions | AI 必用功能卡 | `functions` | GREEN | 0.2 |
| V-handoff-check | 交接防遺漏檢查 | `handoff check` | YELLOW | 14.9 |
| V-status | 流程閘(政策 · 座位 · 加速器 / 網路) | `status` | GREEN | 16.1 |
| V-sync-check | 同步檢查(座位 + 註冊乾跑 + SDD) | `sync-check` | GREEN | 1.1 |
| V-help | 用法 | `help` | 未排 |  |
| V-ssot | SSOT 第四扇門檢 | `ssot` | 未排 |  |
| V-ssot-plan | SSOT 零寫規劃 | `ssot plan` | 未排 |  |
| V-ssot-panorama | SSOT 六族四層全景 | `ssot panorama --no-write` | 未排 |  |
| V-sdd | SDD 驗證 check | `sdd` | 未排 |  |
| V-val | 三系統驗證 SSOT check | `val` | 未排 |  |
| V-workflow | 流程符合性動詞可用(整輪判定由 PS 結尾帶輪號跑) | `workflow` | 未排 |  |
| V-events | 中樞事件 | `events 5` | 未排 |  |
| V-registry-sync | 元件註冊乾跑 | `registry-sync` | 未排 |  |
| V-matrix | 冊 × 啟動矩陣(PLAN) | `matrix --no-tests` | 未排 |  |
| V-inventory | 工具盤點 · 棘輪 · 撞號 | `inventory` | 未排 |  |
| V-sync | 資料樞紐 | `sync` | 未排 |  |
| V-check | 安裝核可檢 | `check` | 未排 |  |
| V-audit | 稽核 | `audit` | 未排 |  |
| V-panorama | 全景(PLAN 預覽) | `panorama` | 未排 |  |
| V-page | 中央頁(落 VIA_Reports,不 publish) | `page` | 未排 |  |
| V-onepage | 一頁交接(落 VIA_Reports,不 publish) | `onepage` | 未排 |  |
| V-register-plan | 註冊計畫 | `register-plan` | 未排 |  |
| V-layout | Layout 樞紐自測 | `layout --selftest` | 未排 |  |
| V-support | NLP / Layout 路由 | `support` | 未排 |  |
| V-nlp | NLP 門 | `nlp` | 未排 |  |
| V-door | NLP / Layout 出口 | `door` | 未排 |  |
| V-books | 政策 · 邏輯 · 參數冊指標 | `books` | 未排 |  |
| V-lexicon | 正則 · 同義字 · 參數紀錄 | `lexicon` | 未排 |  |
| V-ledger | 成功帳 | `ledger` | 未排 |  |
| V-probe | 子系統探針 | `probe` | 未排 |  |
| V-systems | 系統卡 | `systems` | 未排 |  |
| V-dbm | 資料庫中央管控(容器無資料家 = NODATA 黃) | `dbm` | 未排 |  |
| V-tools | 鎖版工具卡 | `tools` | 未排 |  |
| V-chain | VCGC 一鏈(計畫 · 不寫入) | `chain` | 未排 |  |
| V-enter-card | 唯一入口卡(不拉不啟動;串測中不遞迴) | `enter --card --no-pull` | 未排 |  |
| V-monitor | VIA 全景監控(只讀;經 run 走閘)· 教訓卡 | `monitor lessons` | 未排 |  |
| V-closeout | VCGC 一指令收尾(乾跑:--skip-tests,不寫收據 · 不提交 · 不推) | `closeout --skip-tests` | 未排 |  |
| V-gate | VCGC 全綠閘(乾跑:只點編號稽核 · 母子連接;全探針由 v0185 自測驗,串測中不遞迴) | `gate --only 編號稽核,母子連接` | 未排 |  |
| V-link | 母子自動連接(乾跑:不寫冊) | `link` | 未排 |  |
| V-guard | 寫入前衝突閘(乾跑:只判不寫) | `guard` | 未排 |  |
| V-exec | 執行監控卡(唯讀) | `exec --last 5` | 未排 |  |

### S · 席位(各系統 SYSTEM MANAGER 自測)(3 站 · 未排 3)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| S-vcgc-manager | 席位 VCGC 管理器自測 | `run --family core CGC_SystemManager --selftest` | 未排 |  |
| S-vdf-manager | 席位 VDF 管理器自測 | `run VDF_SystemManager --selftest` | 未排 |  |
| S-nlp | 席位 NLP 正主自測 | `run --family core SUP_MDL866_VIAUnifiedNLPOrchestrator --selftest` | 未排 |  |

### C · 交接案(VIA_Handoff_Continuity 宣告測試)(229 站 · 未排 229)

229 個交接案 = `VIA_Handoff_Continuity_SSOT` 的 test_cases 逐案一站(`run --family … <尾版> --selftest` 等唯讀形式);逐案清單在盤點冊 `coverage.case`,容器 11-04 `handoff check` 後 235/235 案都有站。quick 模式不排它們,`test --full` 才全跑。

### E · VCGC 引擎(環境 · 路徑 · 教訓 · 橋 · 編號稽核)(7 站 · 未排 7)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| E-operator-console | 操作台引擎自測 | `run --family core CGC_MDL238_OperatorConsole --selftest` | 未排 |  |
| E-envmanager | ENV MANAGER自測 | `run --family core CGC_MDL240_EnvManager --selftest` | 未排 |  |
| E-talib-scan | TA-Lib 活指令掃自測 | `run --family core CGC_MDL243_TalibCommandScan --selftest` | 未排 |  |
| E-pathverify | 單一路徑驗證自測 | `run --family core CGC_MDL242_PathVerify --selftest` | 未排 |  |
| E-lessons | 教訓帳自測 | `run --family core CGC_MDL058_Lessons --selftest` | 未排 |  |
| E-bridge-sweeper | 橋掃自測 | `run --family core CGC_MDL124_BridgeSweeper --selftest` | 未排 |  |
| E-number-audit | 編號只增稽核(唯讀) | `run --family core CGC_MDL237_NumberingSystem audit` | 未排 |  |

### I · 整合 / 派送站(10 站 · 未排 10)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| I-via_functional_acceptance | 項鏈 via_functional_acceptance 派送計畫(PLAN 乾跑) | `matrix --ids via_functional_acceptance --no-tests` | 未排 |  |
| I-via_ssot_autocode | 項鏈 via_ssot_autocode 派送計畫(PLAN 乾跑) | `matrix --ids via_ssot_autocode --no-tests` | 未排 |  |
| I-via_accelerator_control | 項鏈 via_accelerator_control 派送計畫(PLAN 乾跑) | `matrix --ids via_accelerator_control --no-tests` | 未排 |  |
| I-via_unique_entry_control | 項鏈 via_unique_entry_control 派送計畫(PLAN 乾跑) | `matrix --ids via_unique_entry_control --no-tests` | 未排 |  |
| I-vrn_dispatch | 項鏈 vrn_dispatch 派送計畫(PLAN 乾跑) | `matrix --ids vrn_dispatch --no-tests` | 未排 |  |
| I-vdf_dispatch | 項鏈 vdf_dispatch 派送計畫(PLAN 乾跑) | `matrix --ids vdf_dispatch --no-tests` | 未排 |  |
| I-quantguard_dispatch | 項鏈 quantguard_dispatch 派送計畫(PLAN 乾跑) | `matrix --ids quantguard_dispatch --no-tests` | 未排 |  |
| I-via_panorama_audit | 項鏈 via_panorama_audit 派送計畫(PLAN 乾跑) | `matrix --ids via_panorama_audit --no-tests` | 未排 |  |
| I-via_unified_nlp | 項鏈 via_unified_nlp 派送計畫(PLAN 乾跑) | `matrix --ids via_unified_nlp --no-tests` | 未排 |  |
| I-vrn_nlp_vrn_vdf_pipeline | 項鏈 vrn_nlp_vrn_vdf_pipeline 派送計畫(PLAN 乾跑) | `matrix --ids vrn_nlp_vrn_vdf_pipeline --no-tests` | 未排 |  |

### L · 律 / 政策站(7 站 · 未排 7)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| L-policy | v0100 舊套 policy(CGC_MDL207_PolicyRun) | `run --family core CGC_MDL207_PolicyRun --selftest` | 未排 |  |
| L-talib | v0100 舊套 talib(CGC_MDL205_TalibBan) | `run --family core CGC_MDL205_TalibBan --selftest` | 未排 |  |
| L-ledger | v0100 舊套 ledger(CGC_MDL220_SuccessLedger) | `run --family core CGC_MDL220_SuccessLedger --selftest` | 未排 |  |
| L-matrix | v0100 舊套 matrix(CGC_MDL217_ManagerMatrix) | `run --family core CGC_MDL217_ManagerMatrix --selftest` | 未排 |  |
| L-backup | v0100 舊套 backup(CGC_MDL221_SystemBackup) | `run --family core CGC_MDL221_SystemBackup --selftest` | 未排 |  |
| L-probe | v0100 舊套 probe(CGC_MDL222_SubsystemProbe) | `run --family core CGC_MDL222_SubsystemProbe --selftest` | 未排 |  |
| L-flow | v0100 舊套 flow(CGC_MDL223_FlowConsistency) | `run --family core CGC_MDL223_FlowConsistency --selftest` | 未排 |  |

### L1 · 律 L1 站(2 站 · 未排 2)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| L1-local-selftest | L1 本地工具整合契約 | `run SUP_MDL866_VIAUnifiedNLPOrchestrator --selftest` | 未排 |  |
| L1-local-tools | L1 套件資源盤點 | `run SUP_MDL866_VIAUnifiedNLPOrchestrator l1-tools` | 未排 |  |

### P · PowerShell / 平台站(6 站 · GREEN 1 · 未排 5)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| P-entry | 唯一 PS 入口:語法(pwsh Parser)+ 串測步在 | `—` | GREEN | 0.0 |
| P-step1 | Step1 同步與 LKGC 一次貼:語法(pwsh Parser)+ 章在(CELERITAS-T | `—` | 未排 |  |
| P-vdf_fill | VDF 補缺擷取 PS 啟動器:語法(pwsh Parser)+ 章在(CELERITAS-TEMP | `—` | 未排 |  |
| P-vdf_groups_ui | VDF 族群 U/I PS 啟動器:語法(pwsh Parser)+ 章在(CELERITAS-TE | `—` | 未排 |  |
| P-ui_engine | 一鍵 U/I 引擎 PS 啟動器:語法(pwsh Parser)+ 章在(CELERITAS-TEM | `—` | 未排 |  |
| P-ui_cmds | 操作台短令 Register 尾版:語法(pwsh Parser)+ 章在(十件短令 · Invok | `—` | 未排 |  |

### QG · QuantGuard 站(5 站 · 未排 5)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| QG-VDF_ENG086_QuantGuardOneBridge | VDF_ENG086_QuantGuardOneBridge 本輪候選契約驗證 | `run VDF_ENG086_QuantGuardOneBridge --selftest` | 未排 |  |
| QG-CGC_MDL237_NumberingSystem | CGC_MDL237_NumberingSystem 本輪候選契約驗證 | `run CGC_MDL237_NumberingSystem --selftest` | 未排 |  |
| QG-VDF_ENG117_ForwardVintage | VDF_ENG117_ForwardVintage 本輪候選契約驗證 | `run VDF_ENG117_ForwardVintage --selftest` | 未排 |  |
| QG-VDF_ENG117_ForwardVintageDoor | VDF_ENG117_ForwardVintageDoor 本輪候選契約驗證 | `run VDF_ENG117_ForwardVintageDoor --selftest` | 未排 |  |
| QG-VDF_ENG110_USMacroProbe | VDF_ENG110_USMacroProbe 本輪候選契約驗證 | `run VDF_ENG110_USMacroProbe --selftest` | 未排 |  |

### SSOT · SSOT 站(2 站 · 未排 2)

| 站 | 名稱 | 指令(唯讀 / 乾跑)| 燈 | 秒 |
|---|---|---|---|---|
| SSOT-assets-plan | SSOT 候選衝突規劃 | `run CGC_MDL237_NumberingSystem assets-plan` | 未排 |  |
| SSOT-assets-view | SSOT 中央資產唯讀三表投影 | `run CGC_MDL237_NumberingSystem assets-view` | 未排 |  |

## 6. 禁止事項(卡上原文)

- TA-Lib 一律不用(L50;技術指標唯一正主是 QuantGuard)
- 不改 .ps1(L70:操作員逐次許可;要改就把「哪一行 · 哪一支 · 為什麼」寫成一次貼交操作員)
- 不裝套件、不代設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT / FRED_API_KEY(都是操作員的手)
- 不跑 CGC_MDL064_SelftestGrid --help(會重寫已追蹤檔;單站用 --only)
- 新功能一律新版號檔(L04)、只增不減;凍結來源不改;仍被薄尾引用的舊模組不搬走
- 黃不是綠:BLOCKED / REVIEW / 缺證據 / 同意閘沒開 不能寫成成功
- 已發布的版號冊不就地改(出新版號檔,prior 指回前版);鎖版工具新版先登 role=candidate,席位只由 tools activate 改(架構正本 VIA_Registry_Architecture_SSOT)
- 新指令 / 新模組:登進 VIA_VCGC_FunctionInventory_SSOT(出新版號;測法或豁免理由),否則串測黃;改過的尾版串測會自動跑它的 --selftest 並記版本與時間
- 不把 VCGC 寫成或當成唯一入口 / 閘門;VCGC · VDF · VRN 三個 SYSTEM MANAGER 對等、互不影響、互相只讀監控,問題由該系統自己的 manager 修(L120)

## 7. 總計

| | 數 |
|---|---|
| GREEN | 5 |
| YELLOW | 1 |
| 未排 | 307 |
| 盤點覆蓋 | verb 46 · seat 6 · card 13 · case 235 · workflow 84 · ps 2 |
