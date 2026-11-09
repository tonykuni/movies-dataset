# VIA RC-1 W1 重跑報告(P2 / P4 / P8 v2)

`[MODE] RC-1 W1` · `[GO] HOLD` · 2026-11-09T07:46Z · 基底 main `04df4b879` + W1 工作樹 · 前版 W0:`VIA_RC1_W0_Audit_20261109.md`(NO-GO)

## W1 做了什麼(HARD FREEZE 六類內)

| 類 | 內容 |
|---|---|
| AST Fix | 4 支橋塊搬到 from __future__ 之後(行多重集合不變)→ 出貨範圍 compile 0 |
| Config Fix | JSON 62 BOM + 12 控制字元 → 讀不進 77 → 3 |
| Conflict Fix | 9 份位元相同副本 → 轉接殼(公開名稱齊) |
| Bug Fix | MDL245 v0107 + MDL246 v0102(tests 列表式同病兩支;check 整輪跑完;LESSON-0006) |
| Documentation Fix | Policy v0114 +L124 · 工作流 VCGC v0134(WKF025 tests · WKF028)· VDF v0107(WKF015 tests)· 需求 v0232(REQ203 · REQ022 歸屬)· 盤點 v0207 · 交接冊 +1 案 +7 項 · 衝突冊 v0101 · 教訓冊 v0101 |
| Test Fix | handoff test sdd_validator_v0107 · validation_ssot_v0102 rc 0 標記見到;相依變了的已宣告案重跑(sdd · numbering · vdf_consensus_fixture · vdf_universe_r50 rc 0);編號 --apply --scope 15 檔 +725 列 遺失 0 改身分 0 重號 0 · VCGC 缺號 0 |

## P2 重算

| 項 | W0 | W1 |
|---|---|---|
| py compile 失敗(出貨範圍) | 8 | **0** |
| py compile 失敗(全樹) | 8 | 4(凍結 quarantine / intake) |
| JSON 讀不進 | 77 | **3**(2 空 · 1 intake JSONC) |
| 治理核心位元相同副本 | 8 | **0**(換殼 9) |
| 活目錄重名 .py | 114 | 116(含殼;內容不同的留 W2) |

## P4 Hydra · YELLOW

位元相同的治理核心副本 8 份 → 轉接殼;剩的都是內容不同的雙頭(ssot/VIA_SSOT_Unified · 10_Core_Runtime/Runtime_Bridge · AegisNexus 兩份 exec 引用),要 diff 裁誰是正本 → W2;277 _sha 分身與 15 組同號異名沿用(操作員裁)。不再是「各 3 份一模一樣」的多頭 → 不是 NO-GO 條件,是 HOLD 的 Medium Conflict。

| 治理件 | 現況 |
|---|---|
| `VIA_EnvManager.py` | 1 正本 + 2 殼 |
| `VIA_RegistryCore_v1.py` | 1 正本 + 2 殼 |
| `VIA_Panorama_AST_RuntimeInjector.py` | 1 正本 + 2 殼 |
| `VIA_Runtime_Bridge_All_in_One.py` | 1 正本 + 1 殼 + 1 異本(10_Core_Runtime,W2 diff) |
| `VIA_SSOT_Unified.py` | 1 正本 + 1 殼 + 1 異本(ssot/,8345 行,W2 diff) |
| `VeritasAegisNexus.py` | 尾版 network/_v1652 + 1 殼 + 2 份有 exec 引用的異本(20 / 37 處,W2) |

## P4 SSOT 全景(VCGC 主控台)

[SSOT 全景] YELLOW · 上下單向 VCGC → VDF → VRN → SUP · 探針 7 · 全格無紅(W0:上下連結@VCGC RED)

- 上下連結@VCGC YELLOW:工作流 28 · 步 131 · 需求 203 · 單向 0 · 待重驗鎖 4(WKF007 / 010 / 011 …)· 中央結構檢 GREEN —— W0 的 RED 是 MDL245 崩潰的假紅
- 自動編號@VCGC YELLOW:尾版 306 · 有號 306 · 缺號 0(本輪 --scope 11 檔 +631 列)· 只增稽核 列 121059 → 121784(+725)· 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1(紅列 54 = 冊上宣告碼 ≠ 發出號,沿用)
- 自動編號@VRN YELLOW:缺號 1(VRN_M03_PDF_Layout_JSON_v3.py,無四碼版號)
- 命名 YELLOW(四車道):同號異名 VCGC 8 · VDF 4 · VRN 2 · SUP 1 組(操作員裁)· 沒版號 .py 849(Z281 不計燈)
- 同義字 YELLOW:booksync 網域冊 NONCANONICAL 1 · SYNONYM_LIBRARY 副本 DIVERGED(沿用)

## 閘序(VCGC 主控台 · 單一行程 · 依序)

| 步 | 指令 | rc | 結果 |
|---|---|---|---|
| 01 | `registry-sync --apply` | 0 | 元件冊同步 · 他冊已發 28 號 · 撞號 0 · 時間欄補 UTC 78 |
| 02 | `run CGC_MDL237_NumberingSystem --apply` | 2 | [HOLD] 全域 --apply 不是收件操作;只准已提交的 --apply --scope |
| 03 | `run CGC_MDL237_NumberingSystem audit` | 2 | YELLOW · 列 121059 → 121153(+94)· 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1 · FPSTALE 534 · UNCOMMITTED 150 |
| 04 | `handoff test sdd_validator_v0107` | 0 | rc 0 · 標記見到 · 收據 docs/handoff/evidence/sdd_validator_v0107.json |
| 05 | `ssot panorama` | 2 | YELLOW · 探針 7 · 無紅(上下連結@VCGC RED → YELLOW) |
| 06 | `test --quick` | 2 | YELLOW · 站 12(綠 10 · 黃 2 · 紅 0)· case 246/246 · workflow 131/131 · compile 錯 0 · 缺橋 0 |
| 07 | `handoff check` | 1 | RED 157(CHANGED_CODE_WITHOUT_TEST 84 多為未提交 · EVIDENCE_INVALID 59 多為相依變了 · 工作項格式 4 → 本輪修) |
| 11 | `run CGC_MDL237_NumberingSystem --apply --scope <11 檔>` | 1 | 衝突閘 BLOCK:子系統邊界 RED —— VIA_Workflow_VDF_SSOT_v0107.json 是 VDF 正本,VCGC 不代發號 → 剔除後重跑 |
| 13 | `handoff test <相依變了的 14 案>` | 0/1 | sdd · numbering · vdf_consensus_fixture · vdf_universe_r50 rc 0;validation_ssot_v0101 rc 1 = MDL246 同病(→ v0102);celeritas_gate_v0104 rc 1 = 既有債(Parse-VCGC-Sources-v0100.ps1 無模板章,L70);其餘 8 案名只是工作項不是宣告測試(KeyError) |
| 21 | `run CGC_MDL237_NumberingSystem --apply --scope <10 檔>` | 0 | 放行 · +622 列(PLCY 483 · FNC 94 · STP 26 · WKF/REQ/MDL/CLS)· 遺失 0 · 改身分 0 · 重號 0 |
| 31–33 | `registry-sync --apply · numbering --scope MDL246 v0102 · audit` | 0/0/2 | +9 列 · 合計 121059 → 121784(+725)· 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1(沿用)· FPSTALE 534 · UNCOMMITTED 150(沿用) |
| 34 | `handoff test validation_ssot_v0102` | 0 | rc 0 · 標記見到 |
| 35 | `ssot panorama(第二輪)` | 2 | YELLOW · 無紅 · 自動編號@VCGC 缺號 0 · 上下連結@VCGC YELLOW(待重驗鎖 4) |
| 36 | `test --quick(第二輪)` | 2 | YELLOW · 站 12(綠 10 · 黃 2 · 紅 0)· case 247/247 · workflow 131/131 · compile 錯 0 · 缺橋 0 |
| 41–42 | `handoff test sdd_validator_v0107 · handoff check` | 0/1 | 收據重發 rc 0;交接閘 RED 141(CHANGED_CODE_WITHOUT_TEST 80 · EVIDENCE_INVALID 52 · MODULE_UNREGISTERED 5 · ACCEL_BRIDGE_MISSING 4)—— REQ203 項 0 紅;餘為跨輪欠帳(W0 122 → 本輪相依變更一度 157 → 141) |

## SYSTEM MATRIX

| 系統 | 燈 | 入口 | 證據 | RC-1 PASS? |
|---|---|---|---|---|
| VCGC | **YELLOW** | `CGC_MDL149_…Console test --quick` | test --quick 2026-11-09(第二輪,MDL246 v0102 登站後):YELLOW · 站 12(綠 10 · 黃 2 · 紅 0)· case 247/247 · workflow 131/131 · 家族尾版 283 支 compile 錯 0 · 缺橋 0;黃 2 = V-handoff-check(交接閘 RED 141,跨輪欠帳)· P-entry(容器無 pwsh,不冒充綠) | 自判 YELLOW:交接閘 RED(跨輪欠帳 + 本輪相依變更)與容器無 PowerShell;站無紅 |
| VDF | **YELLOW** | `VDF_SystemManager_v0168 --selftest` | W0 收據沿用(6/6 · NET-BRIDGE 83/83)· 本輪 VDF_MDL014 --selftest 67/67 · VDF-WKF015 補 tests 欄(v0107)· ENG088 v0103 橋塊修正後 compile 過;reader chain 封印收據仍未取得 | PENDING:DoD 兩段缺一段(reader chain 收據 → W2 桌機) |
| VRN-2 | **YELLOW** | `VRN_SystemManager_v0262 --selftest` | W0 收據沿用(5/5)· SUP_MDL749 v0114 橋塊修正後 compile 過 · 缺號 3 支已發號(+94 列)· 4 支 GO_M01 模組冊控制字元修好 | 四本書 DoD 未驗 · 啟動器 local-only(本倉 v0132 / 本機 v0178)→ W2 |
| VQG | **GRAY** | `VQG_AllInOne_v0107 --selftest` | W0 收據沿用 12/12 | RC-1 保留 · 不阻擋 |
| VAP | **GRAY** | `VAP_AllInOne_v0302 --run-self-test` | W0 收據沿用 status=PASS · 8 支 SCOPE_COPY 模組冊控制字元修好 | RC-1 保留 · 不阻擋(真實子系統) |

## HYDRA REPORT(衝突登記冊 v0101)

| ID | 嚴重 | 狀態 | 一句話 |
|---|---|---|---|
| CONFLICT-00001 | CRITICAL | CONTAINED(只在審閱夾,未入倉) | 上傳包 VCGC_MultiMatrix_Integration_v0193.zip / Resilience_v0194.zip 各含 CGC_MDL149_VeritasCentralGovernanceConsol |
| CONFLICT-00002 | MEDIUM | PARTIAL | VeritasAegisNexus(網路橋本體)在活目錄有 8 份、4 種內容。 |
| CONFLICT-00003 | MEDIUM | CONTAINED(審閱包) | Review Kit v0106.4 的 scripts/via_governance_mcp_v0105.py(3 工具:via_status · via_inventory_query · via_token_pre |
| CONFLICT-00004 | HIGH | PARTIAL | 114 個 .py 檔名在多個活目錄重複;其中治理核心各 3 份:VIA_EnvManager.py · VIA_SSOT_Unified.py · VIA_RegistryCore_v1.py · VIA_Runtim |
| CONFLICT-00005 | MEDIUM | OPEN | 277 個 `_sha<hex8>` 分身檔(例 VIA_Panorama_AST_RuntimeInjector_sha63cefe28.py · StartVIAUnified_shaa1b427ff.ps1)。 |
| CONFLICT-00006 | MEDIUM | OPEN(沿用 · 待操作員裁) | 15 組同一編號掛不同名:VCGC 8(CGC_MDL135 EnvGovernance/EnvPlan · CGC_MDL142 AccelImport/TWNameBook · CGC_MDL149 BoxesFlo |
| CONFLICT-00007 | LOW | OPEN | 275 個遠端分支(vcgc 138 · 根 54 · claude 30 · codex 11 …);抽樣 12 支非 claude 分支各有 1104–3342 筆未併入 main 的提交。 |
| CONFLICT-00008 | HIGH | FIXED | compileall 8 支失敗(見 P2)。 |
| CONFLICT-00009 | LOW | FIXED | JSON 77 支讀不進:62 BOM(utf-8-sig 可讀)· 13 語法(控制字元 / JSONC)· 2 空檔(vdf_network_report.json · CGE/Console/inventory/m |
| CONFLICT-00010 | LOW | FIXED | ssot panorama「上下連結@VCGC」RED:正主呼叫失敗 AttributeError 'list' object has no attribute 'get'(第 203 次重複)。 |
| CONFLICT-00011 | LOW | FIXED | 缺號 5(VDF_MDL014_ThreeCodeUniverse_v0100 · VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310 · VRN_ENG115_HeaderFrameTemp_v |
| CONFLICT-00012 | MEDIUM | OPEN | VRN-2 啟動器 ActivateVRN-2 本倉只有 docs 內的 release zip 到 v0132;本機 vrn2_work 最高 v0178;操作員表列 v0149+。管理器本倉尾版 v0262、本機 v |

## LESSON REPORT(+LESSON-0006)

**LESSON-0006 · 工具自己炸 = 假紅,會遮住後面所有誠實燈** —— Root Cause:CGC_MDL245 v0100 三處寫死 (w.get('tests') or {}).get(...);工作流冊 v0133 起 WKF022+ 的 tests 改成 TST 列表,驗證器一碰到就 AttributeError,整輪 X-* 列一條都沒出來,ssot panorama 把「上下連結@VCGC」記 RED(第 203 次)。 Prevention:① 檢查器一列一列失敗,不整輪炸(每個 X-* 自己 try,炸了記 RED 附 repr,其餘照跑);② 冊換形狀前先給驗證器一個帶新形狀的自測(薄尾 add-only);③ 連續同一例外出現 >3 次就是工具病不是冊病,先修工具。

## GO / HOLD / NO-GO

| 條件 | 結果 |
|---|---|
| VCGC PASS | ✘ YELLOW(站 12 綠 10 黃 2 紅 0;黃 = 交接閘 RED · 容器無 pwsh) |
| VRN PASS | ✘ 自測 PASS 但四本書 DoD 未驗 · 啟動器 local-only(W2) |
| VDF PASS | ✘ PENDING —— 自測 ✔ · 橋接 100% ✔ · reader chain 封印收據 GRAY(W2) |
| Compile Error = 0 | ✔ 出貨範圍 0(W0 8 → 0;全樹餘 4 = 凍結 quarantine / intake,範圍外) |
| Critical Conflict = 0 | △ CONFLICT-00001 CRITICAL 仍 CONTAINED(未入倉,不採用) |
| Hydra = GREEN | ✘ YELLOW(RED → YELLOW:位元相同副本已收斂成殼;剩內容不同的雙頭 3 件待 W2 diff 裁定) |
| Lesson Registry Updated | ✔ v0101(+LESSON-0006) |
| Policy Registry Updated | ✔ v0114 +L124 RC1_AUDIT_MODE_READONLY(AgentOS LAW-10 對映) |
| Conflict Registry Updated | ✔ v0101(FIXED 4 · PARTIAL 2 · 沿用 6;0 消失) |

**[GO] HOLD** —— NO-GO 兩條都清了(Compile 0 · Hydra 不再 RED)→ HOLD。HOLD 三條:Medium Conflict 6 筆(3 件要 W2 diff 裁)· 工具登記(缺號已清 0;交接閘 RED 141(W0 122;REQ203 工作項 0 紅;其餘跨輪欠帳,逐案多輪))· 文件(CGE / V018E-F 佐證)。三個 PASS 條件:VCGC YELLOW · VRN-2 四本書未驗 · VDF reader chain 收據未取得。

## [NEXT]

1. W1 收口(本 PR 併入後):MDL246 v0102 · 教訓冊 v0101 · W1 報告三檔已提交 → --apply --scope 補發號 → registry-sync --apply;VDF 工作流冊 v0107 的發號走 VDF 車道(VCGC 衝突閘「子系統邊界」擋 VCGC 代發)
2. W2 桌機:① ssot/VIA_SSOT_Unified.py vs 根正本 diff、10_Core_Runtime/Runtime_Bridge vs 根正本 diff → 裁正本、另一份換殼;② AegisNexus 兩份 exec 引用(20 / 37 處)逐支改指 network/_v1652 再換殼;③ VRN-2 四本書(真 PDF)· 本機 ActivateVRN-2 v0178 入倉;④ VDF reader chain V018E/F 原收據;⑤ CGE v0400 manifest 重出
3. W3:登記冊(Conflict / Lesson)升入 supportive modules/registry 並編號;WKF/STP/REQ 43 碼 --apply --scope;15 組同號異名操作員裁;交接閘逐案
4. W4:P8 v3 → 三個 PASS 條件齊 + Hydra GREEN → GO → tag rc-1

---
```
[MODE] RC-1 W1
[GO]   HOLD —— NO-GO 兩條都清了(Compile 0 · Hydra 不再 RED)→ HOLD。HOLD 三條:Medium Conflict 6 筆(3 件要 W2 diff 裁)· 工具登記(缺號已清 0;交接閘 RED 141(W0 122;REQ203 工作項 0 紅;其餘跨輪欠帳,逐案多輪))· 文件(CGE / V018E-F 佐證)。三個 PASS 條件:VCGC YELLOW · VRN-2 四本書未驗 · VDF reader chain 收據未取得。
[NEXT] W1 收口(本 PR 併入後):MDL246 v0102 · 教訓冊 v0101 · W1 報告三檔已提交 → --apply --scope 補發號 → registry-sync --apply;VDF 工作流冊 v0107 的發號走 VDF 車道(VCGC 衝突閘「子系統邊界」擋 VCGC 代發)
```
