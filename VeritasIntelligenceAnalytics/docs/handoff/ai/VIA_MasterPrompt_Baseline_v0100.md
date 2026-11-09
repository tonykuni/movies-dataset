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


## 2b. 操作員貼來的 Gemini 分享(省 Token 工具候選,主提示詞 §4 的續表;全部 DISCOVERED / UNVERIFIED,不裝)

分享連結 `share.gemini.google/EhfQgofAViEM` 本容器讀不到(302 → gemini.google.com 空頁),內容以操作員貼文為準。
貼文裡的數字(「省 70 倍」「40k stars」「94%」)是工具作者 / 搜尋摘要的宣稱,不是本專案量測(§5 K20:無計量標 UNKNOWN)。

| ID | 候選 | 類型 | 本倉現況 | 採用條件 |
|---|---|---|---|---|
| T21 | rtk(Rust Token Killer) | CLI 輸出壓縮 | 未裝;本倉同功能 = VCGC `digest`(日誌只留判決行,已鎖版實測) | 只在 digest 蓋不到的 npm / docker 輸出有需要時評估 |
| T22 | Caveman | 回覆精簡 skill | 未裝;CLAUDE.md 已要求對話只回報變更 / 證據 / 阻擋 | 不裝(與既有規則重疊) |
| T23 | PromptThrift MCP | 歷史壓縮 MCP | 未裝;宿主已有 context 摘要 | 要先查精確專案身分與資料外送(K14 / §1-6) |
| T24 | code-context-engine(elara-labs) | 本機向量索引 MCP | 未裝;本倉同功能 = `token` 卡 read / slice / pack + Graphify 圖譜 | 要 embedding 費用與外送授權核對 |
| T25 | super-token-saver | session 還原 | 未裝 | 身分未核(名稱泛用),UNVERIFIED |
| T26 | Token Economizer(「Microsoft」) | 重試迴圈攔截 | 未裝;本倉 P5 律「相同失敗最多兩次」已覆蓋 | 出處「微軟」未核,UNVERIFIED |
| T27 | Headroom | payload / AST 壓縮 | 未裝 | 出處未核,UNVERIFIED |
| T28 | Portal / Shunt(「Spotify」) | 讀取分流到便宜模型 | 未裝 | 會把本倉原始碼送第三方模型 → 需操作員外送授權(§1-6) |
| T29 | codeburn | Token × git 看板 | 未裝 | 可讀性高、無外送;若要量測 K20 可評估 |
| T30 | `.claudeignore` 排除清單 | 設定 | **Claude Code 不讀 `.claudeignore`**(它遵守 `.gitignore` 與 settings 的 deny 規則);本倉 `.gitignore` 已排除 __pycache__ / .venv / VIA_Reports 等 | 不另建;要擋讀取用 `.claude/settings.json` permissions.deny |

已在本倉有紀錄的三支(T12 Ponytail · Graphify · OmniRoute)維持 `via_settleall_v0118` 文件的啟用步驟,桌機裝完 ⑳ 才轉綠。

## 2c. 桌機 git 現況(操作員 2026-11-09 貼回)

`git pull --ff-only origin main` → `Not possible to fast-forward`:桌機分支**有本機提交**與 main 分岔(不是只落後)。
另有 ~50 個未追蹤檔(`functional modules/VRN/registry/VRN_Engine_Register_v0100…v0128.json` · `vrn_*.py` · `webscraping_dualengine_v20260819/*` · 根目錄 `_git_conflict/` `registry/`),
抽查 5 個都**不在 main**(= 桌機本地產物,不會被合併蓋掉)。解法見對話:先建備份分支 → `merge --no-ff origin/main` → 衝突就 `--abort` 貼回。

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

## 5b. 後續上傳(同日,同一 Manus 審查包家族)

| 檔 | 判定 |
|---|---|
| Review Kit v0106.4 zip + .sha256 + 收據 json | SHA 一致;四個 U/I 檔已位元組鎖入 `review/VIA_Workbench_LockSite_v0106_4/`;其餘(治理資料 33 MB · 審查包自己的 py / ps1)不入倉、不執行 |
| 六系統指南 / VCGC handover md(各上傳 3 次) | 同內容(cmp 相同);見 §3 |
| VIA_Matrix_Audit_v0105_1 json / xlsx(22 工作表)· Full Model json.gz(36,837 列)· ZIP 稽核 md v0105.2 · RED 修復計畫 md v0105.2 · matrix_detail 收據 | 它那輪的 36,837 列模型與 12 RED(5 系統閘 · 5 治理衝突 · 2 環境閘),scope = 它的 add-on zip bf5ac1a1…,不是本倉燈;只記錄 |
| mcp_stdio_smoke_v0105_2.py(上傳 2 次) | 不執行;它要的 `scripts/via_governance_mcp_v0105.py` 與 engines 不在本倉 |

## 5c. Manus 子任務結果交叉核對(操作員 2026-11-09 貼回)

| Manus 宣稱 | 本倉核對 | 判定 |
|---|---|---|
| EnvManager v0101 @ commit 7bf30ea6 SHA-256 `8c1cdc6a…` | `git show 7bf30ea6:…CGC_MDL240_EnvManager_v0101.py` sha256 = `8c1cdc6a57f75f9a…`;main 尾版同為 v0101,同 sha | **一致**(審的是真檔) |
| 「VIA_FROM_VCGC 只在 docstring,實作沒看到閘」 | v0101 是薄尾(L10「規矩照前一版」);閘在前版 v0100 的 main() 實作 | 宣稱對 v0101 單檔成立,對家族不成立(閘沒丟) |
| 原生 MCP v0102 離線自測 66/66(scratch · 無憑證) | `VIA_MCP_Engine/VIA_MCP_Engine_v0102.py` 在 main;本倉 `.mcp.json` 指的是 VCGC 只讀 MCP `CGC_MDL279_MCPServer_v0101`(stdio · 16 工具 · 零網路),兩者不同物 | 只記錄;不把 Manus scratch 結果當本倉收據 |
| 「VCGC 功能庫重號:281 families / 238 unique module_id;以 candidate_id = family+path 保留,不改號不丟」 | 本倉在 commit 7bf30ea6 實算:CGC_MDL 檔 1467 支 · 家族(號+名)286 · 不同 MDL 號 238 · **13 個號被 >1 家族共用**(MDL123 DataHome/SixStreams · 124 BridgeSweeper/SystemCharter · 125 · 126 · 135 · 142 …)= 交接冊 `VCGC-REQ131:number-collisions` PENDING「撞號 14 組 · 操作員裁定命名」;VCGC 號冊以家族(號+名)為鍵,audit 重號 0 | Manus 做法與 L122 / L125 一致(AI 不改正式號;裁名是操作員 W2);31 MiB 模型 gzip 內嵌 = 本倉工作台同一信封(本倉頁 0.45–0.53 MB) |
| 「以 viaatlas-39ozanmz.manus.space 為功能介面視覺鎖」 | 已是:`review/VIA_Atlas_LocalSite_v0100/`(位元組鎖 · VisualLock v0100 `--vl-*` 24 token);本輪工作台鎖(審查包 U/I)管五系統工作台頁 | 兩鎖並存各管各頁;合一 = W2 |

## 6. 下一個最小動作(順序)

1. 操作員桌機:`git -C <repo> pull --ff-only origin main`,`Test-Path …VIA_DesktopFourBlocks_v0100.py` 回 True 後跑四區塊 live 擷取。
2. 操作員決定:C1–C5;v0193 / v0194 主控台、v0101 入口、MultiMatrix、審查包 v0106.4、NON_STOCK_CORE v0400 哪些要上傳入倉(入倉即走 add-only + chain + 編號 audit)。
3. AI(上傳到後):v0400 核對內嵌核心 SHA → 補 v0310 `internal/` 缺口 → 接 VRN-2 非個股車道自測(交接案 #96)。
4. 20 工具 / 20 機制矩陣:只登已實測者;其餘留 UNVERIFIED,不湊數。
