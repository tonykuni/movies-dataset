# VCGC MCP 啟用與三來源同步(2026-11-07 · 操作員「activate MCP, update and sync」)

## 容器實測(真 stdio 握手 · 不是假主控台)

| 項 | 結果 |
|---|---|
| 伺服器 | `supportive modules/registry/CGC_MDL279_MCPServer_v0101.py --serve --root VeritasIntelligenceAnalytics` |
| initialize | protocolVersion 2025-06-18 · serverInfo vcgc / VIA VCGC(只讀)/ v0101 |
| tools/list | 17:vcgc_token · vcgc_functions · vcgc_status · vcgc_sync_check · vcgc_handoff_check · vcgc_test_inventory · vcgc_matrix · vcgc_sdd · vcgc_ssot_panorama · vcgc_events · vcgc_workflow · vcgc_systems · vcgc_tools · vcgc_chain · vcgc_help · vcgc_mcp_doctor · via_receipt |
| resources/list | 27(via://vcgc/test · vcgc/handoff · vcgc/token-activation · settle/latest · vqg/closeout · graphify/latest …) |
| tools/call vcgc_mcp_doctor | isError false · VIA_MCP_Engine v0102 回報 |
| resources/read via://settle/latest | 讀到 SettleAll v0117 報告 JSON |
| --selftest | v0100 12 項 + v0101 4 項 全過 |
| 絕對路徑 / 相對路徑(cwd = 倉根) | 兩種啟法握手皆 rc 0 |

## 三種用戶端設定

1. **Claude Code(本倉 `.mcp.json` · 已入倉)**:開本倉的會話會提示啟用 project MCP server「vcgc」,同意後即可叫 `vcgc_token` → `vcgc_functions` → `vcgc_handoff_check`。相對路徑,Windows / Linux 共用;command `python`(桌機 py launcher 或既有 via_core 的 python 都可,要能 import 標準庫即可,伺服器零第三方套件)。
2. **Claude Desktop(桌機)**:`%APPDATA%\Claude\claude_desktop_config.json` 的 `mcpServers` 貼入下面;或直接 `python "…\CGC_MDL279_MCPServer_v0101.py" --client-config --root "C:\Users\tonyk\OneDrive\Documents\movies-dataset"` 印出再貼。

```json
{
  "mcpServers": {
    "vcgc": {
      "command": "python",
      "args": [
        "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics\\supportive modules\\registry\\CGC_MDL279_MCPServer_v0101.py",
        "--serve",
        "--root",
        "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics"
      ],
      "env": { "PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES" }
    }
  }
}
```

3. **Manus(自訂 MCP server)**:同上 command / args(stdio);Manus 連上後只能**讀** VCGC 的卡與收據(白名單外動詞一律 isError;零網路;不寫冊 / 鎖 / 快照 / 推送)。

## 三來源同步狀態(2026-11-07 14:20Z)

| 來源 | 狀態 |
|---|---|
| GitHub `tonykuni/movies-dataset` main | 107da7d99(PR #603 併入);工作分支 = main 內容 |
| 本會話(claude.ai/code session_01EqCmJddeqG39YccBtDLGPA) | 工作樹乾淨 · 今日併入 #601 · #602 · #603 |
| Manus `manus.im/app/jlcCGjChDJG1KgzkR8YtIz` | 容器只讀到 app 外殼(「Manus」一字),要登入;分享頁 `/share/…` 只有標題「規劃 VIA 整合 agentmemory、Ponytail、OmniRoute 等工具」→ 內容請在桌機匯出後上傳,或在 Manus 內接上 VCGC MCP 讓它自己讀 |

## 桌機兩行(先自測再貼設定)

```powershell
$via="$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics";$env:VIA_FROM_VCGC='YES';python "$via\supportive modules\registry\CGC_MDL279_MCPServer_v0101.py" --selftest;python "$via\supportive modules\registry\CGC_MDL279_MCPServer_v0101.py" --client-config --root "$HOME\OneDrive\Documents\movies-dataset"
```
