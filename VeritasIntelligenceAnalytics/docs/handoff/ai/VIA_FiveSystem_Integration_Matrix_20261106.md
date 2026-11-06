# 五系統整合進度矩陣(2026-11-06 · 由收據與冊歸納 · 只讀)

對等獨立:VRN-1(他隊倉 · 只讀)· VRN-2 · VDF · VCGC(含 Agent OS / Graphify / MCP 工具)· VQG;VAP 為支援模組(供 VRN-2 繪圖 · 非獨立系統)。燈:🟢 收據證明收尾 · 🟡 能動但有條件 · 🔴 還沒收 · ⚪ 未啟用 / 等料。

| 系統 | 入口(自己的)| 版本尾 | 容器 | 桌機(最近實錄)| VCGC 登錄 | 下一步(誰)|
|---|---|---|---|---|---|---|
| VRN-1 | via-vdf-vrn 倉 MAIN | main 876a4f6(10-21)| — | — | 只讀互看 | 他隊 |
| VRN-2 | ActivateVRN-2 → VRN_SystemManager v0261 · RoundAll v0135 · Handle-All v0127 | runtime v0176 | 🟢 自測 111 項 | 🟢 11-04 收尾頁 DATA_GAP(VRN-2 0 · 資料源 3)· confirm 已記 | 案 manager(操作員 10-10 暫緩待裁)· VRN_logic_index 既有 false | 兆豐 4 份分析師原文 PDF(資料源)· 非個股四重點等 v0300 三支模組 |
| VDF | VDF_SystemManager v0168 · ActivateVDF | ENG113/115/116 v0104(網路工具)| 🟢 自測 rc 0 · ui 6 GREEN(v0101 容器)| 🔴 桌機跑到舊版 v0162(工作樹沒同步)· 但 VQG 讀到它 351 個日線 parquet | 交接案 +4(main 線)· 盤點冊 v0182 | 桌機同步(SettleAll v0105)· 日線補 market / session_index / available_on 三欄(VQG 嚴格綠要) |
| VCGC | CGC_MDL149 v0191 主控台 · PS 操作台 | 盤點冊 v0184 · 需求冊 v0209 · 編號稽核 0/0/0 | 🟡 quick 綠 9 黃 1 紅 0 · full 跑中 · SDD 無紅 · 交接閘 105 既有項 | 🔴 主控台 rc 1 = 一本小 JSON 壞(SettleAll v0105 會指名)| REQ183(VQG)· E-mcp-server | 桌機修壞 JSON + 同步;交接閘歷史 CCWT 42 逐案補或裁 |
| ├ Agent OS | VIA_AgentOS v0102(1.0.2 hardened)| 引擎 SHA 釘 | 🟢 48/48 | 🟡 47 + 1 symlink 權限(環境)· 儀表板出 | MDL1198 | Windows 開發人員模式(操作員)|
| ├ Graphify | v0101 一行 · SettleAll ⑦ | graphifyy 0.9.100 | ⚪ 容器無隔離環境 | 🟡 VRN / VRN_Shared / VDF 綠 · VCGC 要 ≥ 6 GB 可用 | — | 關程式後單跑 VCGC 那張 |
| └ MCP | CGC_MDL279 v0100(stdio 只讀)| v0100 | 🟢 自測 12/12 | ⚪ 待桌機同步後貼用戶端設定 | 盤點冊 v0186 站 E-mcp-server | 用戶端(Claude Desktop / Manus)接上後讀卡與收據 |
| VQG | VQG_AllInOne v0105(薄尾)+ v0104 原檔 | SHA 釘 | 🟢 自測 10 項 · 容器 GRAY(無 VDF 庫)| 🟡 三次 closeout rc 0 · 0050.TW 探針 · 曆是推的 | MDL001/002 · 案 vqg · REQ183 · 站 C-vqg | VDF 三欄 → GREEN(VDF 線)|
| VAP(支援)| VAP_AllInOne v0101(操作員桌機檔 · 未上傳)| — | — | — | 盤點 I-* 站 | 要入倉請上傳 |

## 整合面(跨系統只讀互看)

| 接點 | 狀態 |
|---|---|
| VQG ← VDF 資料庫(只讀 parquet)| 🟡 通(DERIVE_READY · 351 檔)· 嚴格綠要 VDF 三欄 |
| VRN-2 ← VDF 市場資料(⑥e MarketFetch · TWSE / TPEX)| 🟢 v0163 起 |
| VCGC ← 各系統收據(handoff / test / systems)| 🟢 容器 · 🔴 桌機(工作樹)|
| 外部代理 ← VCGC(MCP)| 🟢 伺服器就緒 · ⚪ 用戶端未接 |
| 非個股摘要 v0300 ← VRN-2 版面 / 修文 / NLP 模組 | 🔴 三支模組缺(internal/ · reuse/vrn2/)|

## 真正卡住全局的一件事
桌機倉工作樹(main · 落後 216 · 28 支 VRN 舊版真的改過)—— 同步過了,VDF ui · VCGC 主控台 · MCP 用戶端設定三件一起解。
