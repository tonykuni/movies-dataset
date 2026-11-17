# VIA 外部工具 × VCGC 內部工具 · 搭配表 v0100

> 2026-11-17 · 操作員令:「外部工具導入啟用並與內部工具完整搭配」;選 Graphify(只用本機 AST)· Prettier · Ponytail · OmniRoute;
> 「先把本機環境與工具安裝設置沒衝突問題後再進行」。資料邊界照 11-16 決策 G-03:只有程式碼結構與 schema 可以離開本機;Claudeflare 不接。

## 怎麼裝(桌機一鍵,先查衝突才裝)

`Invoke-VIA-VCGC-ExternalTools-v0100.ps1`(交付分支 `claude/vdf-listsfetch-v0100` 的 `claude-deliveries/`)。

1. **預檢(只讀)**:真 Python · Node 版本 · npm · git · Claude Code CLI · PATH 上既有 graphify / prettier · 既有 Ponytail / OmniRoute · 連接埠 20128 · 磁碟 · 記憶體 · 工具夾不在 OneDrive · 本倉 `VIA_Graphify v0101` 開機行 sha。每支工具一盞燈;**紅的那支這次不裝**。
2. **安裝**:全部裝在 `%LOCALAPPDATA%\VIA\tools`;不改 PATH、不 `-g`、不碰 OneDrive、不裝 Node / Python(缺了報紅並給一行指令)。
3. **自測 + 收據**:`VIA_Reports/vcgc/tools/` 下的 `VIA_ExternalTools_latest.{json,md,html}`、`VIA_ExternalTools_Preflight_latest.json`、`VIA_PrettierCheck_latest.json`。

## 搭配表

| 外部工具 | 釘版 / 位置 | 內部對口 | 怎麼用 | 邊界 |
|---|---|---|---|---|
| Graphify | graphifyy 0.9.100(經本倉 `VIA_Graphify v0101`)· 隔離 venv | `CGC_MDL158` read · slice · pack · chain | Graphify 管「誰呼叫誰、跨檔走向」的導航;要引用證據仍用 MDL158 骨架卡。圖收據 `graphify/latest` 經 VCGC MCP 讀 | `--code-only` · `GRAPHIFY_BACKEND=none` · 離線;文件與圖片不送任何模型;圖不是正式證據 |
| Prettier | prettier 3.3.3 · `%LOCALAPPDATA%\VIA\tools\prettier`(本地) | `VIA_UI_FormatLock` · `VIA_UI_Template_SSOT` | **只檢不寫**(`--check`):列出 Markdown / HTML / JS 排版不一致的檔;收據 `tools/prettier-check` | 鎖定 U/I 檔、報告夾、`.py` / `.ps1` 排除;不自動 `--write`;不改任何鎖定值 |
| Ponytail | Claude Code 外掛 `ponytail@ponytail` | 薄尾新版規則 · 貼回包(verb-interaction)· `CLAUDE.md` | 讓 Claude Code 少寫碼、先找既有件;與「不重寫、出薄尾新版」同向;`CLAUDE.md` 規則仍優先 | 只在操作員本機;倉內零改動。移除:`node scripts/uninstall.js` → `/plugin remove ponytail` |
| OmniRoute | v2.9.5 · `%LOCALAPPDATA%\VIA\tools\OmniRoute` · Node 18–23 · 埠 20128 | `VIA_MCP_Engine v0103`(各 AI 平台設定)· VCGC MCP 唯讀門面 | 本機 AI 閘道,依任務換模型;VIA 引擎的執行路徑一律不經過它 | G-03:只送程式碼結構與 schema;市場資料 / 研報 / 庫內容不送;只綁本機;**不自動啟動**;模型金鑰由操作員自己填 |

## AI 怎麼讀到結果(不用讀檔、不用問操作員)

`CGC_MDL279_MCPServer v0105` 把四份收據登成唯讀資源:`tools/external` · `tools/external-md` · `tools/preflight` · `tools/prettier-check`;
`graphify/latest` 早在 v0101 就有。倉根 `.mcp.json` 指到 v0105(疊在 v0104 回饋包三把鍵之上)。大收據走 v0103 的分頁讀。

## 不做的事

不代設同意閘 · 不改任何系統的檔 · 不推 main · 不碰 TA-Lib · 不接 Claudeflare · 不讓外部工具進 VIA 引擎的執行路徑。
