# 雙橋 100%(操作員 2026-11-06「啟用 注入 AST 加速器導入 PS/PY 檔案 100% · 網路工具導入向外擷取引擎含 VDF 100%」)· 實錄

量尺 = **VCGC 自己的橋掃器 `CGC_MDL124_BridgeSweeper v0111`**(AST 定位插入點 · 只插標記塊原碼一字不動 · 預設 dry-run · `--apply` 才寫 · 尾版律 · 豁免名冊讀 `CGC_MDL156` 尾版)。
Mega-Prompt 點名的 `via_ast_bridge_probe.py / via_ast_bridge_injector.py` 本倉沒有;上面這支就是它們的實體。

| 量尺 | 注入前(dry-run 15:23)| 注入後(dry-run 15:31)|
|---|---|---|
| VDF/accel | 146/146 100% | 146/146 100% |
| VDF/net(向外擷取引擎網路橋;`--net-callers` 外呼件 35/35)| 146/146 100% | 146/146 100% |
| VAP/accel | 225/225 100% | 225/225 100% |
| VRN/accel | 161/172 **93.6%**(缺 11)| **171/171 100%** |
| VIA(supportive)/accel | 1128/1130 99.8%(缺 2)| **1128/1128 100%** |
| **ALL/accel** | 1793/1840 97.4% | **1800/1800 100%** |
| PS 尾版 PS-ACCEL(`--ps --root . --ps-tail`)| 1009/1009 **100%**(版史 38 不算)| 同 |

## 注了什麼(11 支 · 全部 compile 過 · 自測)

| 檔 | 自測 |
|---|---|
| `VRN_SystemManager_v0261.py` | 6/6 PASS(鏈 v0261→…→v0245)|
| `VRN2_ChainShip_v0101.py` | OK 27 · FAIL 0 |
| `VRN2_Publish_v0101.py` | 4/4 |
| `VRN2_VDFBridge_v0100.py` | 6/6 |
| `VRN_ENG397_P1Segment_v0129.py` | 35/35 |
| `VIA_SSOT_Unify_v0100.py` | 3/3 |
| `VRN2_UIAction_v0107.py` | rc 2 = 要 `VRN2_UIAction_Config.json`(桌機才有)· compile 過 |
| `nonstock_v0310/reuse/vrn2/VRN_M07_Summarizer.py` · `VRN_MDL003_TableRestorer.py` | PASS |
| `nonstock_v0310/reuse/vrn2/VRN_M03_PDF_Layout_JSON_v3.py` | rc 3 = 本直譯器沒 fitz(ABSENT 是設計)· compile 過 |
| `supportive modules/SUP_MDL753_VIACommonUtils_v0113.py` | PASS |

## 沒注、改用名冊豁免的(`CGC_MDL156_VIAAcceleratorControl v0115` · 名冊 +4 條 · 自測 6/6)

| 豁免 | 理由 |
|---|---|
| `functional modules/VRN/nonstock_v0310/engine/`(非個股摘要器 v0310 **操作員原件**)| CLAUDE.md:操作員原件 byte-exact + 交接冊 frozen_sources SHA;注橋 = 改 bytes = 打破凍結 |
| `docs/handoff/ai/`(VRN2_RoundAll 各版 · SettleAll 各版 · 入倉原件)| 都是**一行 SHA-256 釘住**的發布件;`--apply` 的 ALL 總表那一趟真的注進了 33 支 RoundAll + VQG v0105 → 本輪已 `git checkout` 還原 bytes,再以名冊擋 |
| `functional modules/VQG/` | VQG 一行 SHA 釘住(SettleAll PINNED + frozen_sources)|
| `supportive modules/agent_os/` | Agent OS 一行 SHA 釘住(SettleAll PINNED);v0102 第 3 行本來就帶 `[VIA:ACCEL-BRIDGE:v0111]` 標記 |

一行 SHA 釘住的檔案,完整性由一行守(同 `VIA_HTML_UI` 正典的理由);它們要加速器橋 → 出**新版號**再注(add-only),不改已釘住的 bytes。

## 獨立性(Mega-Prompt 紅線 1)· AST 掃 372 支尾版

跨系統直接 import **2 件**(VDF → VRN):`VDF_MDL006_FinancialModel_v0100.py` · `VDF_MDL003_SentimentMacroEngine_v0100.py` 直接 `import VRN_SupportBridge…`。這是 VDF 自己的事(交 VDF owner:改走檔案契約或 VCGC 席位);本輪只攔截、不改。

## 副作用與教訓

- 橋掃器 `--subsystems --apply` 除了四個根,最後「ALL 總表」那一趟也會寫(`do_print=False`),所以 dry-run 的 PLAN 清單**少於**實際寫入的檔 → 之後要注,先 `--subsystems`(乾跑)+ 看 `git status`,再決定。
- 注橋後所有依賴這些檔的交接案證據會再次 `EVIDENCE_INVALID`(相依 SHA 變)→ 重測佇列在本輪之後重跑。
