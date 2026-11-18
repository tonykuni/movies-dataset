# 現況顯示接線收據(2026-11-18)

操作員 2026-11-18:「請你接線」。接續 `VIA_StatusDisplay_IntegrationReady_20261118.md` 列的五步。全部薄尾新版,前版一字不動。只在容器跑過,不算主機實測。

## 怎麼用

| 要做什麼 | 指令 |
|---|---|
| 跑一輪並看結論 | `via-vcgc monitor status`(加 `--actor claude` 或 `chatgpt` 記主力) |
| 只看上一輪 | `via-vcgc monitor status --last` |
| 整合說明 | `via-vcgc monitor status manifest` |
| AI 經 MCP 讀 | `via://vcgc/status`(細項讀 `via://vcgc/feedback-delta`) |

rc:綠 0 · 黃 2 · 紅 1 · 引擎不在 3。`monitor` 其他子動詞(scan · watch · dashboard · lessons · sync · show)照舊走 VIA_Panorama。

## 接了什麼

| 步 | 檔 | 號 | 驗證(容器) |
|---|---|---|---|
| 入口 | `CGC_MDL149_VeritasCentralGovernanceConsole_v0197.py` | VIA-VCGC-MDL1653 | 自測 16/16;經入口實跑 rc 1(現況本來就紅) |
| 偵測 | `CGC_MDL282_LocalMonitor_v0103.py` | VIA-VCGC-MDL1655 | 自測 42 項過(含前版鏈) |
| MCP | `CGC_MDL279_MCPServer_v0106.py` | VIA-VCGC-MDL1654 | 本版 6 項過 · v0105 鏈 rc 0 |
| 契約 | `VIA_SystemReceipt_Contract_SSOT_v0101.json` | 冊不發號 | +`status-display`(選配);其餘各節與前版相同 |
| 需求 | `VIA_Requirements_SSOT_v0256.json` | VCGC-REQ225(待編號) | 舊 284 條與前版相同 |
| 工作流 | `VIA_Workflow_VCGC_SSOT_v0152.json` | VCGC-WKF043(4 步;待編號) | SDD:X-CODE · X-ENGINE · X-REQ-BACK 綠 |
| 盤點 | `VIA_VCGC_FunctionInventory_SSOT_v0245.json` | 冊不發號 | test --quick:verb 58/58 · workflow 181/181 · 新 0 |

## 兩個設計決定

1. **掛在既有動詞底下,不另起。** VCGC 的 `monitor` 從 v0182 就在(→ VIA_Panorama)。一開始寫成頂層 `monitor` 會把它蓋掉;改成子動詞 `monitor status`。
2. **自己的收據登成選配,而且不讀自己的燈。** 這份收據彙總的是五個系統的現況,計入 VCGC 的系統燈會把別人的紅算到 VCGC 頭上;現況顯示又會讀契約冊,若讀自己上一輪的燈,紅一次就永遠紅。現在對這一筆只看在不在、必填欄、時效。

## 還沒做 / 要操作員的手

- Windows 主機實跑 `via-vcgc monitor status`(頁面彈出 · 剪貼簿 · 燈);MCP 客戶端實讀一次。過了 VCGC-REQ225 才能從 PARTIAL 轉 COVERED。
- `registry-sync --apply`(註冊冊;SDD X-REG 紅在這)與整輪編號(VCGC-WKF043 · REQ225 的號;冊上那 74 筆檔不在的列)都要批准,沒有代跑。
- `handoff checkpoint` 沒跑:交接冊另一條線(#661)正在改,兩邊同時寫會撞。
- 撞號:本批用了主控台 v0197 · MCP v0106 · 需求冊 v0256 · 工作流冊 v0152 · 盤點冊 v0245 · MDL1653–1655;gifted-dijkstra 那條線(未併)也用了同樣的版號與 1646–1679。後併的那一邊要改發新號。
- test --quick 整輪仍紅,三支都不是本批的檔:`CGC_MDL237_NumberingSystem_v0121` 自測 CANDIDATE_LIMIT · `CGC_MDL261_UIEngine_v0108` 缺 duckdb(容器)· `CGC_MDL278_NumberGrant_v0100`。
