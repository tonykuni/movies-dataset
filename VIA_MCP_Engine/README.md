# VIA MCP Engine(v0101)

泛用型多 AI 平台 MCP 設定引擎:**Python 後端 + 只靠滑鼠操作的 HTML 前端**。
把「哪個 AI 平台 → 接哪幾個 MCP Server → 用什麼執行器 → 秘密放哪 → 設定檔寫到哪」五件事收成一個本機平台;
**每個平台最多掛 5 個 MCP**。

本引擎是 VIA 根下的獨立工具,不讀寫 VRN-1 / VRN-2 / VDF / VCGC 的任何正本、冊、號、檔。

## 啟動

```bash
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py serve
```

經 VCGC(CGC_MDL149 v0192 起的 `mcp` 動詞,子指令原樣下放):

```bash
VIA_FROM_VCGC=YES via-vcgc mcp serve
```

`via-vcgc mcp` 不帶參數印短卡;`mcp doctor` / `mcp selftest` 是 VCGC 串測的三個只讀站(盤點冊 v0183:V-mcp · V-mcp-doctor · V-mcp-selftest)。

瀏覽器自動開 `http://127.0.0.1:8765/`(只綁本機)。畫面三欄,照 ①②③ 點:

| 步 | 欄 | 做什麼 |
|---|---|---|
| ① | 平台 | 點一個平台(Claude Desktop / Cowork · Claude Code · Claude Design · ChatGPT Codex · ChatGPT Chat / Projects · Copilot(VS Code)· Copilot(github.com)· Gemini CLI · Gemini Chat / NotebookLM · Manus · Perplexity · Cursor · Windsurf) |
| ② | 已加入 | 看 5 個格子;點參數藥丸選資料夾 / 檔案 / 開關;點 **−** 移除 |
| ③ | MCP 目錄 | 點 **+** 加入(滿 5 個自動變灰);「推薦 / 全部」切換;「不建議」預設收合 |

然後按 **預覽設定**(dry-run,不寫檔)→ **套用**(先備份舊檔再合併寫入)。
每個格子右側的 **▶** 是「測試啟動」:用渲染出來的指令真的把該 MCP 跑起來,走 stdio JSON-RPC `initialize` → `tools/list`,
回報 server 名稱、版本與工具數(第一次 npx / uvx 會先下載套件,慢一點);**▶ 全部測試啟動** 逐個跑完目前平台的五個。
秘密只從憑證庫或環境變數注入子行程,stderr 回報前先遮掉。
Claude Code / VS Code 的設定檔放在「專案資料夾」,左下角按鈕用滑鼠選。

### 平台四種模式(卡片右側徽章)

- **本機**:直接寫設定檔(Claude Desktop / Cowork、Claude Code、Codex CLI、VS Code Copilot、Gemini CLI、Cursor、Windsurf)。
- **貼上**:產生 `mcpServers` JSON,你貼進該 App 的連接器設定(Perplexity 桌面版)。
- **遠端**:平台只收 HTTPS URL(ChatGPT Chat / Projects、Claude Design、Copilot github.com、Manus)。
  引擎給 `supergateway` 橋接指令把本機 stdio MCP 變成 HTTP;要給雲端平台用還需 HTTPS 隧道。
- **無**:目前沒有 MCP 入口(Gemini Chat / NotebookLM),只給替代建議。

## MCP 目錄(免費 · 開源 · 主流維護 · 安全 ★)

| 分組 | 項目 |
|---|---|
| 核心 | Filesystem ★5 · Memory ★5 · Git ★5 · GitHub ★5 · Fetch ★4 · Sequential Thinking ★5 |
| 資料庫 | SQLite ★5 · DuckDB ★4 · PostgreSQL ★4 |
| 雲端硬碟 | OneDrive / M365 ★4 · Google Drive ★4 · Dropbox ★3 |
| 知識庫 | Obsidian ★5 · Notion ★4 |
| 搜尋 | Brave Search ★4 · Playwright ★4 |
| 不建議 | Discord ★3 · Telegram ★3(權限過大 / API 常變;預設收合) |

目錄與平台都是 `VIA_MCP_Engine_v0101.py` 頂端的資料表(`CATALOG` / `PLATFORMS`),加一筆就多一個選項,不用改邏輯。

## 自適應

- 偵測 OS、node / npx / uvx / docker / git / PowerShell、憑證庫(Windows 憑證管理員 · macOS Keychain · libsecret)、各平台既有設定檔。
- 執行器缺了會警告但照寫設定;GitHub 缺 docker 時改用本機 `github-mcp-server` 二進位。
- Windows 自動用 `cmd /c npx …` 包(Claude Desktop 直接 spawn `.cmd` shim 常失敗)。
- 套用 = **合併**:保留設定檔裡別人的 server 與其他鍵,只覆寫本引擎管理的名稱;重複套用不累積;舊檔備份在 `~/.via_mcp_engine/backups/`。
- Codex 走 TOML(`[mcp_servers.<名>]`),VS Code 走 `servers` + `inputs`,其餘走 `mcpServers`。

## 秘密永不落地

- Token / 連線字串 **不寫進任何設定檔、state 或日誌**;`secret_mode=plain` 直接被拒。
- Windows:產生 `~/.via_mcp_engine/wrappers/start-<名>.ps1`,啟動時從憑證管理員取 `GITHUB_PAT_READONLY` 等鍵,設定檔只指向包裝器。
  存入:`cmdkey /generic:GITHUB_PAT_READONLY /user:via /pass:<Token>`(PowerShell 另需 `Install-Module CredentialManager -Scope CurrentUser`)。
- macOS:`security find-generic-password`;Linux:`secret-tool lookup`(沒有憑證庫就退到作業系統環境變數並警告)。
- VS Code:用 `inputs`(`password: true`),由 VS Code 加密保存。

## GitHub Token:檢查 + 唯讀驗證 + 自動清理

畫面上 **🔐 GitHub Token 檢查** 三步全按鈕:

1. **檢查類型 / 範圍 / 到期**:classic(`ghp_`)看 `X-OAuth-Scopes`,有 `repo` 即判為可寫;fine-grained(`github_pat_`)標頭不揭露,提示去做第 3 步。
2. **載入倉清單 → 選測試倉**(建議專門的測試倉)。
3. **唯讀驗證**:讀 5 項應成功(倉資訊 · README · Issues · PR · 分支 SHA),寫 3 項應被拒(建 Issue · 建分支 · PUT 檔案)。
   寫入若**意外成功** = Token 不是唯讀 → 立刻關閉測試 Issue、刪除測試分支 / 檔案,判決 `NOT_READONLY`。
   **臨時倉模式**:用 `GITHUB_ADMIN_TOKEN` 建私有臨時倉 → 用唯讀 Token 測 → 刪臨時倉(admin Token 只做這兩件事)。

結果只含遮罩後的 Token;證據 JSON 落在 `~/.via_mcp_engine/evidence/`。

命令列同功能:

```bash
GITHUB_PERSONAL_ACCESS_TOKEN=… python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py token check
GITHUB_PERSONAL_ACCESS_TOKEN=… python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py token readonly-test --repo owner/repo
GITHUB_PERSONAL_ACCESS_TOKEN=… GITHUB_ADMIN_TOKEN=… python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py token readonly-test --temp
```

## 命令列(前端做得到的,命令列都做得到)

```bash
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py doctor
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py platforms
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py catalog
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py add claude-desktop filesystem paths=D:\Research
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py add claude-desktop github
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py apply claude-desktop --dry-run
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py apply claude-desktop
```

## 測試

```bash
python3 VIA_MCP_Engine/VIA_MCP_Engine_v0101.py selftest
```

離線、用假 HOME、假 GitHub 傳輸與假 MCP server,不連網、不碰真實設定檔;涵蓋目錄完整性、上限 5、各格式渲染、
Windows / Linux 包裝器、合併與備份、拒絕明文秘密、Token 判決與自動清理、資料夾瀏覽、API 路由、probe 握手與遮秘密(64 項)。
`tests/test_engine.py` 是同一套自測的 pytest 入口;`--selftest` 與 `selftest` 同義(VCGC `run … --selftest` 慣例)。

使用者測試(容器 2026-11-05 實跑):`probe` 真啟動 Filesystem(14 工具)· Memory(9)· Fetch(1)· SQLite(8)· Sequential Thinking(1)全綠;
Playwright 真點擊走完加 MCP → 選夾 → 參數開關 → ▶ 測試啟動 → 套用 → 複製到 Codex(TOML)→ 遠端橋接 → Token 三步(對本機假 GitHub:唯讀 Token READONLY_OK、可寫 Token NOT_READONLY 並自動清理)。
假 GitHub 用 `VIA_MCP_GITHUB_API=http://127.0.0.1:<port>` 指過去,正式環境不設此變數。

## 檔案

```
VIA_MCP_Engine/
├─ VIA_MCP_Engine_v0101.py     後端 + CLI + 自測(標準庫,Python 3.11+)
├─ VIA_MCP_Engine_v0101.html   前端(單檔、無外部資源、深淺色自動;與後端同 stem 同版號)
├─ tests/test_engine.py        pytest 入口
└─ README.md
```

換版:出新版號檔(`_v0102.py` + `_v0102.html`),舊版留著;VCGC 的 `mcp` 動詞自動取最大版號。

執行期資料在 `~/.via_mcp_engine/`(`state.json` · `backups/` · `wrappers/` · `evidence/`),可用 `VIA_MCP_HOME` 改位置;不進 git。
