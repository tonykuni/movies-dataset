# VCGC 這兩天(2026-11-04 → 11-06)新增功能 · 完整整理(從 VCGC 自己的冊生成 · 不憑記憶)

來源:盤點冊 v0179(桌機現況)→ v0186(分支)· 需求冊 v0211 · 功能帳 VIA_VCGC_FunctionLedger · 編號冊 · GitHub PR #585–#596。「Manus」= 操作員在 manus.im 的工作區與 VIA Atlas 靜態站(PR #592);其餘來自 Claude 的兩條分支。燈 = 容器 / 桌機實測,沒測寫 ⚪。

## 一、新功能(入口 · 來源 · VCGC 登錄 · 實測)

| 功能 | 入口 | 來源(PR · 日期)| VCGC 登錄 | 實測燈 | 待辦 |
|---|---|---|---|---|---|
| **VIA_MCP_Engine v0102**(多 AI 平台 MCP 設定引擎:Claude Code / Cowork / ChatGPT / Copilot / Gemini … doctor · 預設五個 · probe · apply · token)| `via-vcgc mcp …`(主控台 v0192 新動詞)· `VIA_MCP_Engine/VIA_MCP_Engine_v0102.py` + .html | #591 / #593 · 11-05(claude/mcp-multi-ai-architecture)| 盤點冊 v0184 站 V-mcp · V-mcp-doctor · V-mcp-selftest · C-vcgc_console_v0192;需求冊 v0210 **VCGC-REQ184**;功能帳 verb:mcp added v0192 | 🟢 容器 test --quick V-mcp rc 0 | 桌機要同步到 v0192 才有 |
| **Invoke-VIA-MCP-v0100.ps1**(一支 PS:找倉 → pull → mcp doctor / 預設五個 / probe / apply / token → serve)| 倉根 `VeritasIntelligenceAnalytics/Invoke-VIA-MCP-v0100.ps1` | #594 · 11-05 | 盤點冊 v0185 站 P-mcp;需求冊 v0211 | 🟡 容器沒 pwsh 語法沒量(P-entry 黃) | 桌機 pwsh 7 實跑 |
| **CGC_MDL279_MCPServer v0100**(VCGC 的 MCP **伺服器**薄殼:stdio JSON-RPC 2.0 · 16 個只讀工具 · 11 個收據資源 · 寫動詞拒絕)| `python CGC_MDL279_MCPServer_v0100.py --serve / --client-config / --selftest` | 本分支 · 11-06(#596) | 盤點冊 v0186 站 E-mcp-server;編號 **VIA-VCGC-MDL1626**;功能帳 family added GREEN 2026-11-06T14:02Z | 🟢 自測 12 / 12(⑫ 每輪跑) | 接 Manus / Claude Desktop 用 `--client-config`(`VCGC_MCP_v0100.md`)|
| **VIA Atlas 靜態審閱站 v0100**(Manus 產出 · viaatlas-39ozanmz.manus.space 的本機版)| `review/VIA_Atlas_LocalSite_v0100/` · `bin/via-atlas.cmd` | #592 · 11-05(via-atlas-static-site-v0100)| **沒入冊**(不是 VCGC 模組 · 靜態頁)| ⚪ 未實測(靜態 HTML) | 要不要登盤點冊由操作員定 |
| **VQG 入 VCGC**(VeritaQuantGuard v0105 · 只讀 VDF 庫)| `functional modules/VQG/VQG_AllInOne_v0105.py` | #590 · 11-04 / 11-05 | 盤點冊站 C-vqg;需求冊 v0209 **VCGC-REQ183**;編號 VIA-VQG-MDL002;交接冊 case vqg | 🟡 桌機 closeout YELLOW(351 日線 · 探針 0050.TW) | 探針黃 = 資料面,VQG 自己的 |
| **VIA Agent OS v0102**(屬 VCGC · 本機優先 · 8 Skills · Token 儀表板)| `supportive modules/agent_os/VIA_AgentOS_v0102.py`(⑨ 每輪跑)| v0178 輪 · 11-04 | 編號 **VIA-SUP-MDL1198**;⑫ 子列 | 🟡 桌機 48 項 · 1 環境錯(symlink 權限)· 8 Skills PASS · 執行 0 | Windows 開發人員模式才全綠 |
| **Graphify 程式圖**(隔離 venv · code-only)| `VIA_Graphify` 一行 v0101(⑦ 每輪 changed 模式)| 本分支 · 11-03 | ⑫ 子列 | 🟡 桌機 VRN 🟢 VDF 🟢 · VRN_Shared / VCGC 記憶體不夠不跑 | 需 ≥ 6 GB 可用 |
| **VIA_SettleAll v0102 → v0112**(一支收尾:同步 · 五系統燈 · ⑫ 系統矩陣 · ⑬ VDF 全引擎自測 · ⑭ 模組矩陣 · 只增帳)| `docs/handoff/ai/VIA_SettleAll_v0112.py` 一行 | 本分支 · 11-04 → 11-06(#595 #596)| 不入冊(交接工具 · 不是 VCGC 模組);報告進 VIA_Reports/settle | 🟢 自測 41 / 41 · 容器 / 桌機實跑 | 桌機貼 v0112 一行 |
| **VDF 收尾交接案 ×40**(r2 尾版 API · 吞例外 · 工作站 manager · fetch groups · ENG236 / 237 / SSOTSync 覆蓋)| VCGC `handoff test <case>` | #589 · 11-04(claude/vrn2-closeout-authorization)| 盤點冊 v0180–v0183 站 C-vdf_* · C-cov_vdf_*;功能帳 ToolingInventory v0103 | 🟢 容器 test --full 站表內(紅 = NODATA / 環境) | — |
| **CGC_MDL278_NumberGrant v0100**(編號授予)| `run CGC_MDL278_NumberGrant` | main · 11-01 | 站 C-cov_cgc_numbergrant;功能帳 added(11-01 RED) | 🔴 功能帳 2026-11-01 RED(VCGC 自己的 test 會更新) | VCGC 自己重測 |

## 二、盤點冊 v0179 → v0186 新增站(51 站 · 依類)

- **其他交接案(VRN / SUP / AI 動作)**(7):`C-aiops` · `C-ps_ownpage` · `C-quarantine_recover` · `C-metrics_resolve` · `C-omnifetch_sentiment` · `C-sentiment_dedupe` · `C-sup_mdl756_v0100`
- **VDF 交接案(r2 尾版 API / 吞例外 / 工作站 / 覆蓋)**(36):`C-vdf_activatevdf` · `C-vdf_fetchgroups_home` · `C-vdf_manager_split_xcheck` · `C-vdf_manager_db_verify` · `C-vdf_r2_tailapi_eng057` · `C-vdf_r2_tailapi_eng059` · `C-vdf_r2_tailapi_eng075` · `C-vdf_r2_tailapi_eng100` · `C-vdf_r2_tailapi_eng102` · `C-vdf_r2_tailapi_eng110` · `C-vdf_r2_tailapi_eng113` · `C-vdf_r2_tailapi_eng115` · `C-vdf_r2_tailapi_eng116` · `C-vdf_r2_swallow_eng050` · `C-vdf_r2_swallow_eng052` · `C-vdf_r2_swallow_eng069` · `C-vdf_r2_tailapi_eng056` · `C-vdf_xsrc_verifier` · `C-vdf_ws_manager_all` · `C-vdf_ws_fetch_groups` · `C-vdf_eng065_v0102` · `C-vdf_eng235_v0100` · `C-vdf_eng077_v0106` · `C-vdf_mdl014_v0100` · `C-vdf_ws_manager_ready` · `C-vdf_ws_fetch_groups_layout` · `C-vdf_ws_manager_design` · `C-vdf_ws_eng093_lists` · `C-vdf_ws_sync_worktree` · `C-vdf_ws_manager_fetch_quiet` · `C-vdf_ws_manager_junction` · `C-vdf_eng045_outputhub` · `C-vdf_manager_frozen_sample` · `C-cov_vdf_eng236` · `C-cov_vdf_eng237` · `C-cov_vdf_ssotsync`
- **VCGC 主控台 / 編號**(2):`C-cov_cgc_numbergrant` · `C-vcgc_console_v0192`
- **VQG**(1):`C-vqg`
- **MCP(設定引擎 · PS 一支 · 伺服器)**(5):`V-mcp` · `V-mcp-doctor` · `V-mcp-selftest` · `P-mcp` · `E-mcp-server`

## 三、需求冊新增(VCGC-REQ180–184)

| 需求 | 內容 | 狀態 |
|---|---|---|
| VCGC-REQ180 | 操作員令(2026-10-12):「用VCGC節省TOKEN工具全景式檢是VCGC/VDF SYSTEM MANAGER及相關SSOT引擎REGEX同義字 收尾完成VCGC VDF後並啟動VCGC及VDF系統跳出HTML U/I完成功能」「用VCGC的節省TOKEN工具全景式檢是VRN SYSTEM | PARTIAL |
| VCGC-REQ181 | 操作員裁定(2026-10-12):「vrn vdf  vcgc都是獨立操作台  只是顏色及lauout基本規劃相同」 | RECORDED |
| VCGC-REQ182 | 操作員令(2026-10-12):「1a for vcgc html u/i design 1b for vrn 1c for vdf only follow visual design and colors. https://claude.ai/design/p/68463cc8-2b29-442 | PARTIAL |
| VCGC-REQ183 | VQG 與 VRN-1 / VRN-2 / VDF / VCGC 對等獨立(互不干涉 · 只讀互看):只讀 VDF 資料庫(位置照 VDF 的冊 VDF_DataHome_SSOT)、不寫 VDF 的夾、不連網;指標公式 / 三解 / 驗證照操作員原檔 v0104(一字不改 · SHA 釘住);VD | PARTIAL |
| VCGC-REQ184 | 操作員令(2026-11-05):「VIA MCP to Claude Code/Cowork/Design, ChatGPT Chat/Project/Codex, Copilot Chat/Notebook, Germini Chat/Notebook, Manus, Perplexity, P | PARTIAL |

## 四、功能帳(VIA_VCGC_FunctionLedger)11-04 起的非冊事件

| 時間(UTC)| 事件 | 家族 / 動詞 | 版本 | 燈 |
|---|---|---|---|---|
| 2026-11-04T03:04 | changed | family:CGC_MDL253_ToolingInventory | v0103 | GREEN |
| 2026-11-05T10:21 | changed | family:CGC_MDL149_VeritasCentralGovernanceConsole | v0192 | GREEN |
| 2026-11-05T10:21 | added | verb:mcp | v0192 | — |
| 2026-11-06T14:02 | added | family:CGC_MDL279_MCPServer | v0100 | GREEN |

## 五、桌機現況(2026-11-06 22:19 貼回)與下一動

- 桌機還在 main 122bab5f8(盤點冊 v0179 · 主控台 v0191):以上**除 Agent OS / Graphify / SettleAll 外都還沒到桌機**,原因是 ③ 同步被兩支被改的凍結版(VRN_SystemManager v0152 / v0153)擋住。
- 下一動:貼 `VIA_SettleAll_v0112.md` 那一行 → ③ 備份並還原那兩支 → 合併 → 主控台 v0192 · 盤點冊 v0186 · MCP 伺服器 · 編號冊全部到桌機 → ⑫ / ⑭ 有燈。
- 「主要來自 Manus」:倉裡能查到的 Manus 產出只有 **VIA Atlas 靜態站(#592)**;MCP 引擎 / PS / 伺服器 / VQG / Agent OS / SettleAll 都是 Claude 分支。桌機 404 個未追蹤檔裡若有 Manus 的新模組,v0112 的報告會列出檔名,再決定入倉。
