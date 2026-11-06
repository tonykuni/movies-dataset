# VIA 全景收尾審計矩陣 · 2026-11-06T15:32:36(容器 · 只讀各系統自報;桌機數字標「桌機 22:19」)

| 燈 | 系統 / 項目 | 版本 | VCGC 編號 | 狀態 | 證據 / 備註 |
|---|---|---|---|---|---|
| ⚪ | VRN-2 | RoundAll v0135 · SM v0261 | VIA-VRN-MDL330 · 2026-11-03 | 容器:收尾 — · VRN-2 待修 — · 資料源 — | 桌機 22:19:🟡 收尾 DATA_GAP · VRN-2 待修 0 · 資料源 3 |
| ⚪ | VDF | SM v0168 | VIA-VDF-MDL237 · 2026-11-01 | 容器:這輪沒測 | 桌機 22:19:🟡 不在舊版上跑:工作樹落後分支 254 提交且 ③ 沒合併(VRN_SystemManager v0254←v0261 · |
| ⚪ | VCGC | 主控台 v0192 · 盤點冊 v0187 | VIA-VCGC-MDL1625 · 2026-11-05 | 容器:這輪沒測 | 桌機 22:19:🟡 不在舊版上跑:工作樹落後分支 254 提交且 ③ 沒合併(VRN_SystemManager v0254←v0261 · |
| 🔴 | 　└ VCGC 站表 | 盤點冊 0187 | — | 容器:320 站 · 🟢 248 🟡 15 🔴 51 ⚪ 6 · 盤點冊 0187 · 狀態到 2026-11-06T15:32 | — |
| ⚪ | 　└ Agent OS | v0102 | VIA-SUP-MDL1198 · 2026-11-04 | 容器:這輪沒測 | 桌機 22:19:🟡 selftest 48 項 · 失敗 0 錯誤 1(環境 N/A 1 · 真的 0)· skills rc 0 · st |
| ⚪ | 　└ Graphify | v0101 一行 · graphifyy | — | 容器:這輪沒測 | 桌機 22:19:🟡 VRN 🟢 · VRN_Shared 🟡 · VDF 🟢 · VCGC 🟡 |
| 🟢 | 　└ MCP 伺服器 | v0101 | VIA-VCGC-MDL1627 · 2026-11-06 | 容器:自測 12 項 · 不過 0 | 桌機 22:19:⚪ 工作樹沒這支(同步後才有) |
| 🟡 | 　└ 政策全景 L103 | SettleAll v0113 | — | 容器:L103 · .py 3646(沒加速器橋 17 · 網路 import 沒網路橋 65)· .ps1 1028(沒 Celeritas 161)· 快取命中 4623 · 例 v | 桌機 22:19:🟡 L103 · .py 4072(沒加速器橋 21 · 網路 import 沒網路橋 78)· .ps1 1041(沒 C |
| ⚪ | VQG | AllInOne v0105 | VIA-VQG-MDL002 · 2026-11-04 | 容器:這輪沒測 | 桌機 22:19:🟡 closeout YELLOW · ① 自測=GREEN ② VD=YELLOW ③ 探針=YELLOW |
| 🟢 | VAP(支援模組) | AllInOne v0300 · SM v0100 | VIA-VAP-MDL051 · 2026-11-06 | 容器:VAP_AllInOne v0300 自測 PASS · 檢查 16 項 · 不過 0 · rc 0 · 0 秒 · 缺選用套件 duckdb talib | 桌機 22:19:⚪ 未納入自動測試(供 VRN-2 繪圖 · 桌機 VAP_AllInOne 未上傳) |
| 🟢 | 模組矩陣 ⑭ | 509 模組尾版 | — | 容器:509 模組尾版 · 🟢 280 🟡 0 🔴 4 ⚪ 225 · AST 錯 0 · 無加速器橋 1 · VRN-2 ⚪90 · VDF ⚪98 · VCGC ⚪283 · VCG | 桌機 22:19:🟢 527 模組尾版 · 🟢 280 🟡 1 🔴 1 ⚪ 245 · AST 錯 0 · 無加速器橋 0 · VRN-2 🟡 |
| 🟢 | PS / PY 加速器橋 100%(尾版律 · VCGC 橋掃器為準) | CGC_MDL124 v0111 · 名冊 CGC_MDL156 v0115 | VIA-VCGC-MDL1587 | VDF/accel 146/146 (100.0%) · VDF/net 146/146 (100.0%) · VAP/accel 225/225 (100.0%) · VRN/accel 171/171 (100.0%) · VIA/accel 1128/1128 (100.0%) · ALL/a | 本輪注入 11 支(VRN 10 · SUP_MDL753)· 操作員原件 / 一行釘住件以名冊豁免(13 條) |
| 🟢 | PS 尾版 PS-ACCEL 橋 | CGC_MDL124 --ps --ps-tail | — | root=. · 掃 1223 · 已掛 1009 · 缺 0 · 版史 38 · 排除 176 · 計畫 0(dry-run) · 覆蓋 100.0% | 版史 38 不算 |
| 🟢 | VDF / 向外擷取引擎 網路工具橋 100% | via_net_injector v0101 · 橋掃 NET | VIA-VCGC-MDL1346 | VDF/net 146/146 (100.0%) | --net-callers:外呼件 35/35 · 非擷取 111 不算 |
| 🔴 | 獨立性違規攔截(尾版跨系統直接 import) | AST 掃 372 支尾版 | — | 違規 2:VDF→VRN 2 | 例:VDF:VDF_MDL006_FinancialModel_v0100.py→VRN_SupportBridge · VDF:VDF_MDL003_SentimentMacroEngine_v0100.py→VRN_SupportBridge |
| 🟡 | Graphify 程式圖(桌機 22:19 收據) | v0101 一行 | — | VRN 🟢 節點 7300 邊 17252 · VRN_Shared 🟡 節點 — 邊 — · VDF 🟢 節點 15426 邊 34793 · VCGC 🟡 節點 — 邊 — | VRN_Shared / VCGC 需 ≥ 6 GB 可用記憶體 |
| 🟡 | VIA Agent OS(桌機 22:19 收據) | v0102 | VIA-SUP-MDL1198 | selftest 48/48 · 失敗 0 · 錯誤 1(symlink 權限)· skills 8 | Windows 開發人員模式才全綠 |

## VCGC 站表(320 站 · VIA_VCGC_FunctionInventory_SSOT_v0187.json)

| 類型 | 站 | 🟢 | 🟡 | 🔴 | ⚪ |
|---|---|---|---|---|---|
| 主控台動詞 | 45 | 27 | 12 | 4 | 2 |
| 交接案 | 230 | 184 | 0 | 45 | 1 |
| 引擎自測 | 9 | 6 | 1 | 0 | 2 |
| PowerShell 入口 | 7 | 5 | 1 | 0 | 1 |
| 項鏈派送 | 10 | 10 | 0 | 0 | 0 |
| 舊套 v0100 | 7 | 7 | 0 | 0 | 0 |
| 品質閘候選契約 | 5 | 5 | 0 | 0 | 0 |
| 席位自測 | 3 | 2 | 0 | 1 | 0 |
| SSOT 中央資產 | 2 | 1 | 1 | 0 | 0 |
| 本地工具契約 | 2 | 1 | 0 | 1 | 0 |

## 模組矩陣小計(509 列)

| 系統 | 模組 | 🟢 | 🟡 | 🔴 | ⚪ | AST 錯 | 無橋 |
|---|---|---|---|---|---|---|---|
| VRN-2 | 90 | 0 | 0 | 0 | 90 | 0 | 1 |
| VDF | 98 | 0 | 0 | 0 | 98 | 0 | 0 |
| VCGC | 283 | 279 | 0 | 4 | 0 | 0 | 0 |
| VCGC·支援 | 33 | 0 | 0 | 0 | 33 | 0 | 0 |
| VCGC·Agent OS | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| VQG | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| VAP | 3 | 1 | 0 | 0 | 2 | 0 | 0 |

## SHA-256 憑證

| 檔 | SHA-256 |
|---|---|
| SettleAll v0113(一行) `VIA_SettleAll_v0113.py` | `b5b75b7b9dbfde3a10cb4a70b193b337cd9c08174fe0a460c88a335a0f9852b0` |
| MCP 伺服器 v0101 `CGC_MDL279_MCPServer_v0101.py` | `8cff4c941bbc52952aa3e75fae20574837645bfb0874bc0d4d2884c768cefdd2` |
| 加速器控制 / 豁免名冊 v0115 `CGC_MDL156_VIAAcceleratorControl_v0115.py` | `5a5903cce1c71275a7509dedf27249260a1191fa5a3ad1da7a118b3783dc501d` |
| VAP All-In-One v0300(原件) `VAP_AllInOne_v0300.py` | `0b888607096d5a0fd514b143f80486af5d83b38c9429344b6ae073cec8330ba9` |
| VRN-2 SystemManager v0261(本輪注橋後) `VRN_SystemManager_v0261.py` | `6100460b53f8e3ee597d19a30bed9310168724edf1a413b71813e6bb23ab6633` |
| VCGC 盤點冊 v0187 `VIA_VCGC_FunctionInventory_SSOT_v0187.json` | `91c9641f409c34973ca04862a3108a7e328f190a8a90951c06ec25316b25c87e` |

## Mega-Prompt 點名但本倉**沒有**的元件(照實說 · 不假裝)

- `via_ast_bridge_probe.py` / `via_ast_bridge_injector.py` → 本倉對應 **CGC_MDL124_BridgeSweeper**(AST 定位插入點 · 只增不減 · dry-run 預設)+ **via_net_injector**;探針 = `token` + SettleAll ⓫ + MDL158 `read / slice`。
- `VeritasDependencyGraphEngine.py` / `DependencyGraph.json` → 本倉是 **Graphify**(隔離 venv · code-only)。
- `SmartAssetRegistry.json` / `mcp_registry.json` / `mcp_router.py` / `Invoke-VcgcMasterGate.ps1` / `Sync-VIAMotherSystem.ps1` → **不存在**;MCP 設定由 VIA_MCP_Engine v0102,MCP 伺服器由 CGC_MDL279 v0101。
- `VDF_SystemManager_v0104` / `VRN_SystemManager_v0104` / `VCGC v0130` → 樹上尾版是 **VDF v0168 · VRN-2 v0261 · 主控台 v0192**;`VAP-CH-01~28` 是 v027 舊圖庫,v0300 是 40 Canonical + 5 Composite。
- `>90% Token 節省`:實測只有單檔卡片層級(MDL158 骨架卡 省 92.3–94.6%),沒有系統級量測,不宣稱。
