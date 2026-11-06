# VCGC 工具功能矩陣(2026-11-06 · 全站實測 · 由 VCGC 自己的冊生成 · 只讀)

來源:盤點冊 `VIA_VCGC_FunctionInventory_SSOT_v0183.json`(314 站)· **全站串測** `test --full`(test-20261106-084614-511 · 2026-11-06T08:46 UTC · head 6d8fe7e · 1405 秒)→ GREEN 252 · YELLOW 14 · RED 51 · 工具鎖版冊 · 省 Token 啟用收據 · AI 必用卡 v0102。燈 = 容器實跑;紅的逐站附**原因分類**(容器環境 ≠ 桌機:缺 yfinance / fastparquet / PyMuPDF / NLP 13 套件、測試境 numpy 1.26 都是容器的事,桌機 11-05 環境有 pyarrow 24 · polars 1.40 · fitz 1.27)。

## 0. MCP

之前:VCGC 沒有任何 MCP 程式碼。**現在:`CGC_MDL279_MCPServer_v0100`(stdio · JSON-RPC 2.0 · 協定 2025-06-18 · 只讀)**:16 個工具 = 唯讀動詞白名單經子行程跑主控台(閘與事件照走)· 11 份收據資源 · 寫冊 / 鎖 / 推送動詞一律拒 · 零網路 · 自測 12/12 · 盤點冊 v0186 站 `E-mcp-server`。用戶端設定與用法:`docs/handoff/ai/VCGC_MCP_v0100.md`。

## 1. 省 Token 工具(token 席位 `CGC_MDL158_VIAPanoramaAuditRepair_v0117.py` · nlp 席位 `SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py` · 啟用收據 2026-10-18 03:21:57)

| 工具 | 做什麼 | 狀態 |
|---|---|---|
| `read` | 骨架卡(.py/.ps1 定義樹;.json 兩層;.jsonl 欄位) | 啟用 · 實測(收據 6/6) |
| `slice` | 一個定義或一段 JSON 路徑 | 啟用 · 實測(收據 6/6) |
| `digest` | 日誌只留判決行 | 啟用 · 實測(收據 6/6) |
| `pack` | 整夾索引 | 啟用 · 實測(收據 6/6) |
| `--if-etag` | 沒變回 304,沿用上一張 | 啟用 · 實測(收據 6/6) |
| `chain` | 薄尾版本鏈圖 | v0117 起有 |
| `brief` | NLP 長文摘要(SUP_MDL866 text --file <檔> --brief) | 啟用 · 實測(收據 6/6) |

## 2. 鎖版工具席位(換版只經 `tools activate … --apply`)

| 席位 | 現任 |
|---|---|
| accelerator | `VeritasCeleritas_v1141.py` |
| network | `VeritasAegisNexus_v1652.py` |
| layout | `SUP_MDL743_GenericLayoutHub_v0110.py` |
| nlp | `SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py` |
| token | `CGC_MDL158_VIAPanoramaAuditRepair_v0117.py` |
| frame | `SUP_MDL755_VIAPolarsFrame_v0100.py` |
| praddle | `VRN_ENG398_PraddleExtractor_v0100.py` |
| pdfplumber | `SUP_MDL746_PDFPlumberPlusHub_v0102.py` |
| ocr | `via_ocr_super_v0102.py` |

## 3. AI 必用步

| 步 | 指令 | 何時 | 做什麼 |
|---|---|---|---|
| 1 | `VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt` | 每次進場第一步 | 啟用並實測省 Token 工具;紅了就停,不讀政策、不開子系統 |
| 2 | `VIA_FROM_VCGC=YES python3 "$V" functions` | token 之後 | 印本卡:必用順序 · 指令 · 何時用 · 禁止 |
| 3 | `VIA_FROM_VCGC=YES python3 "$V" handoff check` | 接手時(換對話 / 換接手者) | 讀交接快照的摘要、待辦、相依變更;不從對話記憶推定已完成 |
| 4 | `VIA_FROM_VCGC=YES python3 "$V" test --quick  →  收尾前 test(整輪)` | handoff 之後(每次進場);新增 / 換版任何 VCGC 指令或模組之後 | VCGC 全功能串測:盤點冊(VIA_VCGC_FunctionInventory_SSOT)逐站跑 · 新指令未登錄 = 黃 · 更新過的尾版自動跑 --selftest · 版本與 UTC 時間寫進 VIA_VCGC |
| 5 | `python3 "$E" read <檔或夾> [--depth N]` | 讀任何約 >200 行的檔或整夾之前 | 骨架卡(定義樹 · AST 問題);.json 看兩層、.jsonl 看欄位次數與首末列 |
| 6 | `python3 "$E" slice <檔> <定義名/Class.method/JSON 路徑>` | 只要改或看其中一段 | 只取一個定義;JSON 路徑 a.b[0] · [-1] · [*] · [鍵=值] |
| 7 | `python3 "$E" chain <家族名/任一版的檔> [--all]` | 改任何薄尾家族(出新版號檔)之前 | 版本鏈圖:誰是本體、前版怎麼接、誰蓋了誰;防薄尾盲點 |
| 8 | `python3 "$E" digest <日誌>` | 看跑測日誌 | 只留判決行;紅日誌誠實回 rc 1 |
| 9 | `VIA_FROM_VCGC=YES python3 "$V" ssot panorama [--full]` | 動到 SSOT / 正則 / 同義字 / 編號 / 命名 / 註冊之前與之後 | 六族 × VCGC → VDF → VRN → SUP 上下單向檢測到底;輸入沒變的格沿用 |
| 10 | `VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL237_NumberingSystem --apply --scope  →  run CGC_MDL237_Num` | 程式與冊提交之後(先提交再編號)、編號冊提交之前 | 只登本批(範圍 = 對 main 有變的已提交檔;不帶 --scope 的全量 --apply 要操作員下令)· audit 遺失 · 改身分 · 重號 必須全 0,另查註冊完整性 IMMUT · DUPREG · XC |
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

## 5. 全站 × 燈 × 原因(分類)

### V · VCGC 動詞(42 站 · GREEN 26 · RED 4 · YELLOW 12)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| V-token | 省 Token 第一步 | `token` | GREEN | 1.5 |  |
| V-functions | AI 必用功能卡 | `functions` | GREEN | 0.2 |  |
| V-handoff-check | 交接防遺漏檢查 | `handoff check` | YELLOW | 15.2 | <unknown>:3: SyntaxWarning: invalid escape sequence '\*' |
| V-status | 流程閘(政策 · 座位 · 加速器 / 網路) | `status` | GREEN | 25.2 |  |
| V-sync-check | 同步檢查(座位 + 註冊乾跑 + SDD) | `sync-check` | GREEN | 1.0 |  |
| V-help | 用法 | `help` | GREEN | 2.1 |  |
| V-ssot | SSOT 第四扇門檢 | `ssot` | YELLOW | 7.9 | [沿用] policy · 鑰匙 d1b545740f860fde · 27s 前算的(--fresh 強制重算) |
| V-ssot-plan | SSOT 零寫規劃 | `ssot plan` | YELLOW | 7.4 | [沿用] policy · 鑰匙 d1b545740f860fde · 35s 前算的(--fresh 強制重算) |
| V-ssot-panorama | SSOT 六族四層全景 | `ssot panorama --no-write` | YELLOW | 48.7 | <unknown>:3: SyntaxWarning: invalid escape sequence '\*' |
| V-sdd | SDD 驗證 check | `sdd` | YELLOW | 3.0 | <unknown>:3: SyntaxWarning: invalid escape sequence '\*' |
| V-val | 三系統驗證 SSOT check | `val` | GREEN | 2.0 |  |
| V-workflow | 流程符合性動詞可用(整輪判定由 PS 結尾帶輪號跑) | `workflow` | YELLOW | 1.8 | VCGC-WKF002 exit NOT_RUN |
| V-events | 中樞事件 | `events 5` | GREEN | 0.7 |  |
| V-registry-sync | 元件註冊乾跑 | `registry-sync` | GREEN | 2.6 |  |
| V-matrix | 冊 × 啟動矩陣(PLAN) | `matrix --no-tests` | GREEN | 2.1 |  |
| V-inventory | 工具盤點 · 棘輪 · 撞號 | `inventory` | YELLOW | 52.8 | <unknown>:6: SyntaxWarning: invalid escape sequence '\C' |
| V-sync | 資料樞紐 | `sync` | GREEN | 2.6 |  |
| V-check | 安裝核可檢 | `check` | YELLOW | 2.2 | [沿用] policy · 鑰匙 a5dedb53bab941a3 · 55s 前算的(--fresh 強制重算) |
| V-audit | 稽核 | `audit` | GREEN | 3.1 |  |
| V-panorama | 全景(PLAN 預覽) | `panorama` | YELLOW | 2.8 | [沿用] policy · 鑰匙 a5dedb53bab941a3 · 60s 前算的(--fresh 強制重算) |
| V-page | 中央頁(落 VIA_Reports,不 publish) | `page` | GREEN | 12.0 |  |
| V-onepage | 一頁交接(落 VIA_Reports,不 publish) | `onepage` | GREEN | 11.4 |  |
| V-register-plan | 註冊計畫 | `register-plan` | GREEN | 3.0 |  |
| V-layout | Layout 樞紐自測 | `layout --selftest` | RED | 11.0 | 環境 · 版面樞紐 ⑥ PRADDLE 原生行 0(無 PyMuPDF) |
| V-support | NLP / Layout 路由 | `support` | GREEN | 4.1 |  |
| V-nlp | NLP 門 | `nlp` | GREEN | 1.2 |  |
| V-door | NLP / Layout 出口 | `door` | GREEN | 1.1 |  |
| V-books | 政策 · 邏輯 · 參數冊指標 | `books` | GREEN | 2.1 |  |
| V-lexicon | 正則 · 同義字 · 參數紀錄 | `lexicon` | GREEN | 2.0 |  |
| V-ledger | 成功帳 | `ledger` | GREEN | 2.0 |  |
| V-probe | 子系統探針 | `probe` | RED | 2.0 | 資料 · 還原點無過關紀錄 |
| V-systems | 系統卡 | `systems` | RED | 5.6 | 資料 · 還原點無過關紀錄 |
| V-dbm | 資料庫中央管控(容器無資料家 = NODATA 黃) | `dbm` | YELLOW | 2.8 | <unknown>:3: SyntaxWarning: invalid escape sequence '\*' |
| V-tools | 鎖版工具卡 | `tools` | GREEN | 1.5 |  |
| V-chain | VCGC 一鏈(計畫 · 不寫入) | `chain` | GREEN | 12.7 |  |
| V-enter-card | 唯一入口卡(不拉不啟動;串測中不遞迴) | `enter --card --no-pull` | GREEN | 19.5 |  |
| V-monitor | VIA 全景監控(只讀;經 run 走閘)· 教訓卡 | `monitor lessons` | GREEN | 5.5 |  |
| V-closeout | VCGC 一指令收尾(乾跑:--skip-tests,不寫收據 · 不提交 · 不推) | `closeout --skip-tests` | YELLOW | 21.3 | ⑩  全綠閘 略過:串測中(防遞迴;串測自己就是全功能檢查) |
| V-gate | VCGC 全綠閘(乾跑:只點編號稽核 · 母子連接;全探針由 v0185 自測驗,串測中不遞 | `gate --only 編號稽核,母子連接` | GREEN | 7.0 |  |
| V-link | 母子自動連接(乾跑:不寫冊) | `link` | GREEN | 0.2 |  |
| V-guard | 寫入前衝突閘(乾跑:只判不寫) | `guard` | RED | 2.3 | 同步 · 分支落後 main |
| V-exec | 執行監控卡(唯讀) | `exec --last 5` | YELLOW | 0.2 | ok    08:58:37 R rc 0 0.0s · link |

### S · 席位(3 站 · GREEN 2 · RED 1)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| S-vcgc-manager | 席位 VCGC 管理器自測 | `run --family core CGC_SystemManager --selftest` | GREEN | 1.8 |  |
| S-vdf-manager | 席位 VDF 管理器自測 | `run VDF_SystemManager --selftest` | GREEN | 117.4 |  |
| S-nlp | 席位 NLP 正主自測 | `run --family core SUP_MDL866_VIAUnifiedNLPOrchestrator --sel` | RED | 2.8 | 環境 · NLP L1 缺 13 套件 |

### E · VCGC 引擎(8 站 · GREEN 6 · YELLOW 1 · 未排 1)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| E-operator-console | 操作台引擎自測 | `run --family core CGC_MDL238_OperatorConsole --selftest` | GREEN | 2.3 |  |
| E-envmanager | ENV MANAGER自測 | `run --family core CGC_MDL240_EnvManager --selftest` | GREEN | 1.4 |  |
| E-talib-scan | TA-Lib 活指令掃自測 | `run --family core CGC_MDL243_TalibCommandScan --selftest` | GREEN | 1.2 |  |
| E-pathverify | 單一路徑驗證自測 | `run --family core CGC_MDL242_PathVerify --selftest` | GREEN | 4.2 |  |
| E-lessons | 教訓帳自測 | `run --family core CGC_MDL058_Lessons --selftest` | GREEN | 1.5 |  |
| E-bridge-sweeper | 橋掃自測 | `run --family core CGC_MDL124_BridgeSweeper --selftest` | GREEN | 2.6 |  |
| E-number-audit | 編號只增稽核(唯讀) | `run --family core CGC_MDL237_NumberingSystem audit` | YELLOW | 8.3 | <unknown>:3: SyntaxWarning: invalid escape sequence '\*' |
| E-mcp-server | VCGC MCP 伺服器薄殼(stdio · 只讀)自測 | `run CGC_MDL279_MCPServer --selftest` | 未排 |  |  |

### I · 整合 / 派送(10 站 · GREEN 10)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| I-via_functional_acceptance | 項鏈 via_functional_acceptance 派送計畫(PLAN 乾跑) | `matrix --ids via_functional_acceptance --no-tests` | GREEN | 2.0 |  |
| I-via_ssot_autocode | 項鏈 via_ssot_autocode 派送計畫(PLAN 乾跑) | `matrix --ids via_ssot_autocode --no-tests` | GREEN | 2.4 |  |
| I-via_accelerator_control | 項鏈 via_accelerator_control 派送計畫(PLAN 乾跑) | `matrix --ids via_accelerator_control --no-tests` | GREEN | 2.3 |  |
| I-via_unique_entry_control | 項鏈 via_unique_entry_control 派送計畫(PLAN 乾跑) | `matrix --ids via_unique_entry_control --no-tests` | GREEN | 2.1 |  |
| I-vrn_dispatch | 項鏈 vrn_dispatch 派送計畫(PLAN 乾跑) | `matrix --ids vrn_dispatch --no-tests` | GREEN | 2.1 |  |
| I-vdf_dispatch | 項鏈 vdf_dispatch 派送計畫(PLAN 乾跑) | `matrix --ids vdf_dispatch --no-tests` | GREEN | 2.0 |  |
| I-quantguard_dispatch | 項鏈 quantguard_dispatch 派送計畫(PLAN 乾跑) | `matrix --ids quantguard_dispatch --no-tests` | GREEN | 2.3 |  |
| I-via_panorama_audit | 項鏈 via_panorama_audit 派送計畫(PLAN 乾跑) | `matrix --ids via_panorama_audit --no-tests` | GREEN | 2.2 |  |
| I-via_unified_nlp | 項鏈 via_unified_nlp 派送計畫(PLAN 乾跑) | `matrix --ids via_unified_nlp --no-tests` | GREEN | 2.1 |  |
| I-vrn_nlp_vrn_vdf_pipeline | 項鏈 vrn_nlp_vrn_vdf_pipeline 派送計畫(PLAN 乾跑) | `matrix --ids vrn_nlp_vrn_vdf_pipeline --no-tests` | GREEN | 6.1 |  |

### L · 律 / 政策(7 站 · GREEN 7)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| L-policy | v0100 舊套 policy(CGC_MDL207_PolicyRun) | `run --family core CGC_MDL207_PolicyRun --selftest` | GREEN | 1.8 |  |
| L-talib | v0100 舊套 talib(CGC_MDL205_TalibBan) | `run --family core CGC_MDL205_TalibBan --selftest` | GREEN | 1.8 |  |
| L-ledger | v0100 舊套 ledger(CGC_MDL220_SuccessLedger) | `run --family core CGC_MDL220_SuccessLedger --selftest` | GREEN | 1.2 |  |
| L-matrix | v0100 舊套 matrix(CGC_MDL217_ManagerMatrix) | `run --family core CGC_MDL217_ManagerMatrix --selftest` | GREEN | 1.2 |  |
| L-backup | v0100 舊套 backup(CGC_MDL221_SystemBackup) | `run --family core CGC_MDL221_SystemBackup --selftest` | GREEN | 1.2 |  |
| L-probe | v0100 舊套 probe(CGC_MDL222_SubsystemProbe) | `run --family core CGC_MDL222_SubsystemProbe --selftest` | GREEN | 1.2 |  |
| L-flow | v0100 舊套 flow(CGC_MDL223_FlowConsistency) | `run --family core CGC_MDL223_FlowConsistency --selftest` | GREEN | 2.3 |  |

### L1 · 律 L1(2 站 · GREEN 1 · RED 1)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| L1-local-selftest | L1 本地工具整合契約 | `run SUP_MDL866_VIAUnifiedNLPOrchestrator --selftest` | RED | 3.2 | 環境 · NLP L1 缺 13 套件 |
| L1-local-tools | L1 套件資源盤點 | `run SUP_MDL866_VIAUnifiedNLPOrchestrator l1-tools` | GREEN | 4.7 |  |

### P · PowerShell / 平台(6 站 · GREEN 6)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| P-entry | 唯一 PS 入口:語法(pwsh Parser)+ 串測步在 | `—` | GREEN | 0.0 |  |
| P-step1 | Step1 同步與 LKGC 一次貼:語法(pwsh Parser)+ 章在(CELERIT | `—` | GREEN | 0.0 |  |
| P-vdf_fill | VDF 補缺擷取 PS 啟動器:語法(pwsh Parser)+ 章在(CELERITAS- | `—` | GREEN | 0.0 |  |
| P-vdf_groups_ui | VDF 族群 U/I PS 啟動器:語法(pwsh Parser)+ 章在(CELERITA | `—` | GREEN | 0.0 |  |
| P-ui_engine | 一鍵 U/I 引擎 PS 啟動器:語法(pwsh Parser)+ 章在(CELERITAS | `—` | GREEN | 0.0 |  |
| P-ui_cmds | 操作台短令 Register 尾版:語法(pwsh Parser)+ 章在(十件短令 · I | `—` | GREEN | 0.0 |  |

### QG · QuantGuard(5 站 · GREEN 5)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| QG-VDF_ENG086_QuantGuardOneBridge | VDF_ENG086_QuantGuardOneBridge 本輪候選契約驗證 | `run VDF_ENG086_QuantGuardOneBridge --selftest` | GREEN | 6.0 |  |
| QG-CGC_MDL237_NumberingSystem | CGC_MDL237_NumberingSystem 本輪候選契約驗證 | `run CGC_MDL237_NumberingSystem --selftest` | GREEN | 95.8 |  |
| QG-VDF_ENG117_ForwardVintage | VDF_ENG117_ForwardVintage 本輪候選契約驗證 | `run VDF_ENG117_ForwardVintage --selftest` | GREEN | 1.9 |  |
| QG-VDF_ENG117_ForwardVintageDoor | VDF_ENG117_ForwardVintageDoor 本輪候選契約驗證 | `run VDF_ENG117_ForwardVintageDoor --selftest` | GREEN | 1.3 |  |
| QG-VDF_ENG110_USMacroProbe | VDF_ENG110_USMacroProbe 本輪候選契約驗證 | `run VDF_ENG110_USMacroProbe --selftest` | GREEN | 1.4 |  |

### SSOT · SSOT(2 站 · GREEN 1 · YELLOW 1)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| SSOT-assets-plan | SSOT 候選衝突規劃 | `run CGC_MDL237_NumberingSystem assets-plan` | YELLOW | 76.0 | <unknown>:209: SyntaxWarning: invalid escape sequence '\*' |
| SSOT-assets-view | SSOT 中央資產唯讀三表投影 | `run CGC_MDL237_NumberingSystem assets-view` | GREEN | 2.2 |  |

### C · 交接案(229 站 · GREEN 184 · RED 45)

| 站 | 名稱 | 指令 | 燈 | 秒 | 紅 / 黃原因 |
|---|---|---|---|---|---|
| C-dataframe_lock | 交接案 dataframe_lock(CGC_MDL249_DataFrameLock -- | `run --family core CGC_MDL249_DataFrameLock --selftest` | RED | 1.6 | 環境 · 容器系統 Python 沒 fastparquet |
| C-vrn_docclass | 交接案 vrn_docclass(VRN_ENG393_DocClassVerify --s | `run --family vrn VRN_ENG393_DocClassVerify --selftest` | RED | 2.9 | 資料 · 還原點無過關紀錄 |
| C-vrn_layout | 交接案 vrn_layout(VRN_ENG394_LayoutRestore --self | `run --family vrn VRN_ENG394_LayoutRestore --selftest` | RED | 10.6 | 資料 · 還原點無過關紀錄 |
| C-tool_coverage_matrix | 交接案 tool_coverage_matrix(CGC_MDL230_ToolCovera | `run --family core CGC_MDL230_ToolCoverageProbe --selftest` | RED | 116.5 | 資料 · 還原點無過關紀錄 |
| C-vdf_fred_clock | 交接案 vdf_fred_clock(VDF_ENG074_FredMacroSSOT -- | `run --family vdf VDF_ENG074_FredMacroSSOT --selftest` | RED | 2.3 | 環境 · 測試境 numpy 1.26 vs pyarrow 2.0 |
| C-vdf_finstmt_gate2 | 交接案 vdf_finstmt_gate2(VDF_ENG082_FinStatements | `run --family vdf VDF_ENG082_FinStatements --selftest` | RED | 10.1 | 環境 · 缺套件 |
| C-vrn_header_frame | 交接案 vrn_header_frame(VRN_ENG115_HeaderFrameTem | `run --family vrn VRN_ENG115_HeaderFrameTemp --selftest` | RED | 4.4 | 環境 · 測試境 numpy 1.26 vs pyarrow 2.0 |
| C-praddle | 交接案 praddle(VRN_ENG398_PraddleExtractor --self | `run --family vrn VRN_ENG398_PraddleExtractor --selftest` | RED | 5.2 | 資料 · 還原點無過關紀錄 |
| C-layout_praddle | 交接案 layout_praddle(SUP_MDL743_GenericLayoutHub | `run --family vrn SUP_MDL743_GenericLayoutHub --selftest` | RED | 2.5 | 環境 · 版面樞紐 ⑥ PRADDLE 原生行 0(無 PyMuPDF) |
| C-nlp_praddle | 交接案 nlp_praddle(SUP_MDL866_VIAUnifiedNLPOrches | `run --family vrn SUP_MDL866_VIAUnifiedNLPOrchestrator --self` | RED | 5.1 | 環境 · NLP L1 缺 13 套件 |
| C-first_page_engine | 交接案 first_page_engine(VIA_VRN_FirstPageEngine  | `run VIA_VRN_FirstPageEngine --selftest` | RED | 4.7 | 資料 · 還原點無過關紀錄 |
| C-nlp_optional | 交接案 nlp_optional(SUP_MDL866 v0108 --selftest;L | `run SUP_MDL866_VIAUnifiedNLPOrchestrator --selftest` | RED | 3.2 | 環境 · NLP L1 缺 13 套件 |
| C-vdf_fetch_system | 交接案 vdf_fetch_system(VDF 獨立擷取系統 MDL008(冊 · 改寫  | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-vdf_fetch_integration | 交接案 vdf_fetch_integration(VDF 擷取系統整合測試:七支全鏈 ·  | `run VDF_SystemManager fetch test` | RED | 1.8 | 環境 · 缺 yfinance(VDF 擷取) |
| C-vdf_fetch_v0101 | 交接案 vdf_fetch_v0101(MDL008 v0101 總控入口 · 冊 v010 | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-vdf_list_stock | 交接案 vdf_list_stock(MDL009 全台股清單(開頭五欄 · 驗證七項 ·  | `run VDF_MDL009_TWStockList --selftest` | RED | 1.9 | 環境 · 容器系統 Python 沒 fastparquet |
| C-vdf_list_etf | 交接案 vdf_list_etf(MDL010 主動式 ETF 清單(ENG077 律 ·  | `run VDF_MDL010_ActiveETFList --selftest` | RED | 1.6 | 環境 · 容器系統 Python 沒 fastparquet |
| C-vdf_list_stock_v0101 | 交接案 vdf_list_stock_v0101(MDL009 v0101 年區代碼 202 | `run VDF_MDL009_TWStockList --selftest` | RED | 1.9 | 環境 · 容器系統 Python 沒 fastparquet |
| C-vdf_fetch_v0102 | 交接案 vdf_fetch_v0102(MDL008 v0102 冊 v0102(MDL00 | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-vdf_fetch_fill | 交接案 vdf_fetch_fill(MDL008 v0103 fetch fill 補缺擷 | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-vdf_list_stock_v0102 | 交接案 vdf_list_stock_v0102(MDL009 v0102 網路工具 AST | `run VDF_MDL009_TWStockList --selftest` | RED | 1.9 | 環境 · 容器系統 Python 沒 fastparquet |
| C-vdf_fetch_v0104 | 交接案 vdf_fetch_v0104(MDL008 v0104 網路工具 AST 真橋 · | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-vdf_fetch_v0105 | 交接案 vdf_fetch_v0105(MDL008 v0105 urllib / yfin | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-vdf_fetch_v0106 | 交接案 vdf_fetch_v0106(MDL008 v0106 block / fixtu | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-celeritas_gate_v0103 | 交接案 celeritas_gate_v0103(Celeritas 產出契約閘 v0103 | `run CGC_MDL183_CeleritasPolicyGate --selftest` | RED | 79.4 | 資料 · 還原點無過關紀錄 |
| C-vdf_fetch_v0107 | 交接案 vdf_fetch_v0107(MDL008 v0107 live curl_cff | `run VDF_MDL008_FetchSystem --selftest` | RED | 10.5 | 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) |
| C-tool_probe_v0106 | 交接案 tool_probe_v0106(工具覆蓋矩陣 v0106:無版號舊 PS 檔有同族 | `run CGC_MDL230_ToolCoverageProbe --selftest` | RED | 122.4 | 資料 · 還原點無過關紀錄 |
| C-version_panorama_loader | 交接案 version_panorama_loader(版本全景:加速器載入器尾版 SUP_ | `run CGC_MDL225_VersionPanorama --selftest` | RED | 1.7 | 資料 · 還原點無過關紀錄 |
| C-celeritas_gate_v0104 | 交接案 celeritas_gate_v0104(Celeritas 產出契約閘 v0104 | `run CGC_MDL183_CeleritasPolicyGate --selftest` | RED | 79.4 | 資料 · 還原點無過關紀錄 |
| C-via_unified | 交接案 via_unified(所有短令一個入口 via:轉派 · list · which | `run CGC_MDL264_ViaUnified --selftest` | RED | 1.5 | 資料 · 還原點無過關紀錄 |
| C-vdf_refill | 交接案 vdf_refill(VDF 管理員 v0130 refill:計畫 · GATED | `run VDF_SystemManager_v0130 --selftest` | RED | 55.5 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-cov_vrn_firstpage_engine | 交接案 cov_vrn_firstpage_engine(VIA_VRN_FirstPage | `run VIA_VRN_FirstPageEngine --selftest` | RED | 4.7 | 資料 · 還原點無過關紀錄 |
| C-vdf_manager_v0152 | 交接案 vdf_manager_v0152(VDF_SystemManager v0152  | `run VDF_SystemManager_v0152 --selftest` | RED | 94.1 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-vdf_manager_v0153 | 交接案 vdf_manager_v0153(VDF_SystemManager v0153  | `run VDF_SystemManager_v0153 --selftest` | RED | 96.8 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-ui_engine_v0105 | 交接案 ui_engine_v0105(CGC_MDL261 v0105 VCGC 操作台字 | `run CGC_MDL261_UIEngine_v0105 --selftest` | RED | 7.2 | 資料 · 還原點無過關紀錄 |
| C-health_matrix_v0113 | 交接案 health_matrix_v0113(CGC_MDL274 v0113 健康矩陣頁 | `run CGC_MDL274_HealthMatrix_v0113 --selftest` | RED | 1.4 | 資料 · 還原點無過關紀錄 |
| C-vdf_manager_v0154 | 交接案 vdf_manager_v0154(VDF_SystemManager v0154  | `run VDF_SystemManager_v0154 --selftest` | RED | 96.8 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-ui_engine_v0106 | 交接案 ui_engine_v0106(CGC_MDL261 v0106 VCGC 操作台展 | `run CGC_MDL261_UIEngine_v0106 --selftest` | RED | 10.3 | 資料 · 還原點無過關紀錄 |
| C-health_matrix_v0114 | 交接案 health_matrix_v0114(CGC_MDL274 v0114 健康矩陣頁 | `run CGC_MDL274_HealthMatrix_v0114 --selftest` | RED | 4.1 | 資料 · 還原點無過關紀錄 |
| C-vdf_manager_v0155 | 交接案 vdf_manager_v0155(VDF_SystemManager v0155  | `run VDF_SystemManager_v0155 --selftest` | RED | 98.9 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-vdf_manager_v0156 | 交接案 vdf_manager_v0156(VDF_SystemManager v0156: | `run VDF_SystemManager_v0156 --selftest` | RED | 102.1 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-vdf_manager_v0157 | 交接案 vdf_manager_v0157(VDF_SystemManager v0157: | `run VDF_SystemManager_v0157 --selftest` | RED | 102.9 | 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) |
| C-health_matrix_v0115 | 交接案 health_matrix_v0115(CGC_MDL274_HealthMatri | `run CGC_MDL274_HealthMatrix_v0115 --selftest` | RED | 4.3 | 資料 · 還原點無過關紀錄 |
| C-ui_engine_v0107 | 交接案 ui_engine_v0107(CGC_MDL261_UIEngine v0107: | `run CGC_MDL261_UIEngine_v0107 --selftest` | RED | 9.6 | 資料 · 還原點無過關紀錄 |
| C-vdf_eng045_outputhub | 交接案 vdf_eng045_outputhub(VDF_ENG045_OutputHub  | `run --family vdf VDF_SystemManager engine run VDF_ENG045_Out` | RED | 7.7 | 資料 · 還原點無過關紀錄 |
| (綠的 184 案省略 · 全在 TEST_latest.json) | | | | | |

## 6. 紅燈原因彙總(51 站)

| 原因 | 站數 |
|---|---|
| 資料 · 還原點無過關紀錄 | 20 |
| 環境 · 擷取自測要先有全市場快照(無網 / 無 yfinance) | 8 |
| 引擎自測 · 前版鏈 v0151 自測紅(VDF 線) | 7 |
| 環境 · 容器系統 Python 沒 fastparquet | 5 |
| 環境 · NLP L1 缺 13 套件 | 4 |
| 環境 · 版面樞紐 ⑥ PRADDLE 原生行 0(無 PyMuPDF) | 2 |
| 環境 · 測試境 numpy 1.26 vs pyarrow 2.0 | 2 |
| 同步 · 分支落後 main | 1 |
| 環境 · 缺套件 | 1 |
| 環境 · 缺 yfinance(VDF 擷取) | 1 |

## 7. 禁止事項(卡上原文)

- TA-Lib 一律不用(L50;技術指標唯一正主是 QuantGuard)
- 不改 .ps1(L70:操作員逐次許可;要改就把「哪一行 · 哪一支 · 為什麼」寫成一次貼交操作員)
- 不裝套件、不代設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT / FRED_API_KEY(都是操作員的手)
- 不跑 CGC_MDL064_SelftestGrid --help(會重寫已追蹤檔;單站用 --only)
- 新功能一律新版號檔(L04)、只增不減;凍結來源不改;仍被薄尾引用的舊模組不搬走
- 黃不是綠:BLOCKED / REVIEW / 缺證據 / 同意閘沒開 不能寫成成功
- 已發布的版號冊不就地改(出新版號檔,prior 指回前版);鎖版工具新版先登 role=candidate,席位只由 tools activate 改(架構正本 VIA_Registry_Architecture_SSOT)
- 新指令 / 新模組:登進 VIA_VCGC_FunctionInventory_SSOT(出新版號;測法或豁免理由),否則串測黃;改過的尾版串測會自動跑它的 --selftest 並記版本與時間
- 不把 VCGC 寫成或當成唯一入口 / 閘門;VCGC · VDF · VRN 三個 SYSTEM MANAGER 對等、互不影響、互相只讀監控,問題由該系統自己的 manager 修(L120)
