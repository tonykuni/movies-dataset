# VIA Claude 主提示詞 v0100 · 基線核對與差異列(2026-11-09 · 容器只讀盤點)

來源:操作員上傳 5 份(VIA_Claude_Master_Prompt_v0100.md · 六系統審查包指南 v0106.4 · VCGC AI handover v0106.4 ×2(同檔)· NON_STOCK_CORE README_v0400.md)。
上傳檔是待核對資料,不擴張授權;本檔只記「提示詞說的基線」對「GitHub main 實況」的差異。沒有實測的項一律 NOT_RUN,不是綠。

## 1. 能力 / 來源 / 版本基線(現場確認)

| 項 | 提示詞 §2 寫的 | main f7f681e66 實況 | 判定 |
|---|---|---|---|
| 執行所在 | Windows 桌機 REPO_ROOT / DATA_ROOT / PARENT_REPO | 雲端容器 `/home/user/movies-dataset`;無 C: 磁碟、無 pwsh、無桌機 venv | 桌機路徑不可視為已可存取 |
| VCGC 後端 | CGC_MDL149 **v0194**(SHA 66e8333…) | 尾版 **v0192**(v0190–v0192 在倉);v0193 / v0194 不在倉 | 差異:v0193/v0194 只在桌機 Downloads(另一工作階段交付) |
| 統一入口 | Invoke-VIA-AllInOne-**v0101**.ps1(SHA 0a1aea8d…) | 倉內 `launchers/Invoke-VIA-AllInOne-v0104…v0111.ps1`,8 支 SHA 皆不等於 0a1aea8d | 差異:v0101 與倉內版史是兩條平行家族,接回前要 `chain` 比對 |
| 主套件 / 前端 | VCGC_MultiMatrix_Resilience_v0194.zip · VCGC_MultiMatrix_v0194.html | 倉內 0 筆 | 不在倉(NOT_IN_REPO) |
| 審查包 v0106.4 | public/subsystems-v0106.4.html · via_governance_mcp_v0105.py · stage_subsystem_workspaces | 倉內 0 筆 | 不在倉;其自報 gate = RED / BLOCKED(見 §3) |
| NON_STOCK_CORE | v0400 單檔內嵌 core(README 自報自測 9/9 · 回歸 41/41) | 倉內只有 v0310(`functional modules/VRN/nonstock_v0310/`),`internal/NON_STOCK_CORE_v0200.py` 仍缺(README_MISSING 2026-11-06) | v0400 未上傳未入倉;若 v0400 真內嵌 SHA 92f53d82… 的核心,可補 v0310 缺口(交接案 #96) |
| 交接 checkpoint | checkpoint.json · NEXT_ACTION.md | 既有 `docs/handoff/HANDOFF_latest.json`(lamp GREEN · closeout YELLOW · pending 104)+ 本檔 | 不另造同義副本;沿用既有冊 |
| 五系統 | 「中央 + 四個業務系統」(VCGC 中央) | 政策 L123 / L125:VCGC · VDF · VRN-2 · VQG · VAP **對等獨立**,VRN-1 外倉只讀;編號是唯一跨系統關聯 | 系統範圍差異列(§4) |

## 2. 本輪已核對可用的 Token 工具(不是全部 20 項)

已啟用且實測(鎖冊 `VIA_ToolVersion_Lock_v0100.json`):`token` 卡 read / slice / digest / pack / chain · NLP `--brief`。
容器可用:git diff · rg · Python ast · SQLite / DuckDB · Playwright(預裝 Chromium)。
不可用 / 未裝:pwsh 原生 Parser(容器無 pwsh)· Graphiti · AgentMemory · Sourcegraph · Neo4j · OmniRoute(桌機 npm)。
Ponytail:Claude Code 外掛,桌機側啟用;本倉只記錄啟用步驟(`via_settleall_v0118` 文件)。
其餘 T01–T20 狀態 = DISCOVERED / UNVERIFIED,不作「已啟用」宣稱。

## 3. 審查包 v0106.4 自報的 VCGC RED(原文 ID,只攤開不代修)

| ID | 內容 | 對應本倉 |
|---|---|---|
| OBS-0001 | 無 VCGC connector / server 或 owner registry 收據;TokenEngine add-on 只本地測 | 本倉 MCP 握手收據在 `docs/handoff/ai/mcp/`(2026-11-07);審查包未讀本倉 → 它的 RED 是「它沒看到」,不是本倉失效 |
| OBS-0186 | 未提供可核實的 VCGC MCP URL / stdio 指令、憑證與實機 root | 同上;stdio 設定在 `.mcp.json`;實機 root 由操作員桌機提供 |
| OBS-0194 | 舊「排他替換」Token 政策 vs 最新「附加」規則衝突;不得自動套用舊政策 | 與 CLAUDE.md 一致:工具換版只經 `via-vcgc tools activate … --apply`;本倉未套用審查包任何政策 |

審查包其餘:Tony-NB UNAVAILABLE · native runtime NOT_RUN · 正式註冊 false。這些是它自己的 scope,不改本倉燈。

## 4. 規則衝突(需操作員裁,AI 不自裁)

| # | 提示詞 | 本倉既有令 | 本輪做法 |
|---|---|---|---|
| C1 | §1-2「不自動推送 GitHub」 | 2026-11-09 令「閘過了就推、回 Codex、更新 PR」 | 只推 **feature 分支**(可回復),不動 main、不合併 |
| C2 | §3「中央 + 四業務」 | L123/L125 五系統對等、VCGC 只是自己的入口 | 沿用 L123/L125;提示詞的表列為「系統範圍差異」 |
| C3 | §3 寫「VRN」籠統 | 2026-10-19 令分寫 VRN-1 / VRN-2 | 本檔一律分寫 |
| C4 | §2 基線 v0194 / v0101 | 倉內 v0192 / v0111 | 桌機版若要入倉,走 add-only 新版號 + `chain`,不改名冒充 |
| C5 | §9 要 checkpoint.json / NEXT_ACTION.md | 既有 HANDOFF_latest.json + 需求冊 | 不另造;§6 即 NEXT_ACTION |

## 5. 今天「白做工」疑問的紀錄答案(摘要,詳見對話)

VRN-2 / VRN-1(REQ197):矩陣 · 借用 9 缺口 · 只讀證明 · 借出清單 4/4 → VERIFIED;`integration-not-done` BLOCKED 等操作員裁整合範圍。
VDF:管線 fixture 跑通;live 擷取是桌機項(REQ192/193/195 · REQ145/147/150 PENDING),桌機 checkout 落後 main 所以檔「找不到」。

## 6. 下一個最小動作(順序)

1. 操作員桌機:`git -C <repo> pull --ff-only origin main`,`Test-Path …VIA_DesktopFourBlocks_v0100.py` 回 True 後跑四區塊 live 擷取。
2. 操作員決定:C1–C5;v0193 / v0194 主控台、v0101 入口、MultiMatrix、審查包 v0106.4、NON_STOCK_CORE v0400 哪些要上傳入倉(入倉即走 add-only + chain + 編號 audit)。
3. AI(上傳到後):v0400 核對內嵌核心 SHA → 補 v0310 `internal/` 缺口 → 接 VRN-2 非個股車道自測(交接案 #96)。
4. 20 工具 / 20 機制矩陣:只登已實測者;其餘留 UNVERIFIED,不湊數。
