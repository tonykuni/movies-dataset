# VCGC MCP 伺服器 v0100(CGC_MDL279 · stdio · 只讀 · 2026-11-06)

操作員:「透過 MCP 連結 … 用矩陣顯示整合工具 … 接續 Manus 收尾 VCGC · 完全授權」。VCGC 之前對外只有主控台動詞、PowerShell 操作台、收據 JSON;本模組把**只讀**那一部分照 MCP(Model Context Protocol · JSON-RPC 2.0 over stdio · 協定版 2025-06-18)露出去。

## 露什麼 · 不露什麼

| 類 | 內容 |
|---|---|
| 工具(16)| `vcgc_token` · `vcgc_functions` · `vcgc_status` · `vcgc_sync_check` · `vcgc_handoff_check` · `vcgc_test_inventory` · `vcgc_matrix` · `vcgc_sdd` · `vcgc_ssot_panorama` · `vcgc_events` · `vcgc_workflow` · `vcgc_systems` · `vcgc_tools` · `vcgc_chain(family)` · `vcgc_help` · `via_receipt(key)`;每個 = 子行程跑 VCGC 自己的主控台(`VIA_FROM_VCGC=YES python CGC_MDL149_… <動詞>`),它的閘與事件紀錄照走;rc 0 綠 · rc 2 黃(不算錯)· 其他紅 |
| 資源(11)| `via://vcgc/test` · `vcgc/handoff` · `vcgc/token-activation` · `settle/latest` · `vqg/closeout` · `graphify/latest` · `agent-os/selftest` · `vrn2/closeout` · `vdf/ui-manifest` · `matrix/vcgc-tools` · `matrix/closeout-panorama`(只讀 VIA_Reports / docs 收據;沒有的照實說「還沒有」)|
| **不露** | 會寫冊 / 鎖 / 快照 / 推送 / 同意閘的動詞:checkpoint · tools activate · registry-sync --apply · go / enter · sync · install · backup(白名單外一律 isError);family 參數只收家族名(殼字元拒) |
| 網路 | 零(stdio);不 import socket / http / urllib / requests(自測 ⑫ 查原始碼)|

自測 12 / 12(假主控台 · 不碰 VCGC):initialize / ping / tools/list / tools/call(綠 · 黃 · 拒絕四種)/ chain 帶參數 / resources list+read(含沒有的收據)/ 未知方法 -32601 / stdio 串流(通知不回 · 壞 JSON -32700)/ client-config。盤點冊 v0186 +站 `E-mcp-server`(v0184 / v0185 是 main 另一工作階段的:P-mcp · V-mcp · V-mcp-doctor · V-mcp-selftest = VIA_MCP_Engine 的站)。

## 桌機怎麼接(Claude Desktop · Manus 或任何 MCP 用戶端)

1. 桌機倉先同步到本分支(SettleAll v0105 一行 · 或 `git -C "C:\Users\tonyk\OneDrive\Documents\movies-dataset" fetch origin claude/optimistic-goodall-yhalc5` 後 checkout 該檔)。
2. 先自測:`python "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules
egistry\CGC_MDL279_MCPServer_v0100.py" --selftest`
3. 印設定:`python "…\CGC_MDL279_MCPServer_v0100.py" --client-config --root "C:\Users\tonyk\OneDrive\Documents\movies-dataset"`,或直接貼下面這段到用戶端的 MCP 設定(Claude Desktop:`%APPDATA%\Claude\claude_desktop_config.json`;Manus:它的 MCP / Connectors 設定頁,欄位同名):

```json
{
  "mcpServers": {
    "vcgc": {
      "command": "python",
      "args": [
        "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics\\supportive modules\\registry\\CGC_MDL279_MCPServer_v0100.py",
        "--serve",
        "--root",
        "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset"
      ],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

4. 用戶端連上後先叫 `vcgc_token` → `vcgc_functions` → `vcgc_handoff_check`(= AI 必用卡順序),收據用 `via_receipt` 或 resources。

## Manus 那兩個連結(容器實測)

- `manus.im/share/jlcCGjChDJG1KgzkR8YtIz`:可讀文字只有標題「規劃 VIA 整合 agentmemory、Ponytail、OmniRoute 等工具」與「Manus task replay completed.」,沒有進度、檔名、版本、MCP 字樣 → **接不到它的進度內容**;要接續它,得把那個任務的產出(檔案 / 文字)匯出上傳。
- `viaatlas-39ozanmz.manus.space`:只有標題「VIA Subsystem Workspaces v0106.4」+ 一張 base64 圖,無文字。
- `manus.im/app/…`:要登入,容器讀不到。

MCP 是雙向接點:Manus 接上本伺服器後能**讀** VCGC 的卡與收據;VCGC 這邊不會因此多出任何寫入路徑。

## 與 main 的 VIA_MCP_Engine(v0102 · 2026-11-05 另一工作階段)分工

| | VIA_MCP_Engine v0102(+ Invoke-VIA-MCP v0100 · 主控台 v0192 `mcp` 動詞)| CGC_MDL279_MCPServer v0100(本檔)|
|---|---|---|
| 角色 | **用戶端設定引擎**:哪個 AI 平台接哪幾個 MCP server(每平台最多 5 個)· 預覽 / 套用設定檔 · 真啟動探測 | **被接的伺服器**:把 VCGC 唯讀動詞與收據露成 MCP 工具 / 資源 |
| 接法 | 在 Engine 的 MCP 目錄裡加一筆自訂 server:command `python` · args = 本檔 `--serve --root <倉根>`(即 `--client-config` 印出的那段)→ 平台(Claude Desktop / Manus …)就同時接上 VCGC | — |
| 不重疊 | Engine 不露 VCGC 動詞;本檔不寫任何設定檔 | |

## v0101(2026-11-06 · 操作員「MCP 功能完善化對接一切」· v0100 一字不動 · 薄尾 `CGC_MDL279_MCPServer_v0101.py`)

- 資源 **11 → 27**:多 ⑫ 系統矩陣 · ⑭ 模組矩陣 · VCGC 站表矩陣 · ⑬ VDF 引擎矩陣(json / md)· SETTLE 報告 md · VCGC 測試狀態冊 · VCGC 功能帳 · Agent OS status / skills · VRN-2 RoundAll · VCGC 兩天新增功能整理 · 架構基線 B1–B5 對照 · VAP v0300 函式清冊(全部只讀 · 零寫入 · 零網路)。
- 工具 **16 → 17**:`vcgc_mcp_doctor` = 主控台 v0192 的 `mcp doctor`(只讀偵測各 AI 平台設定)。
- `--client-config` 的 command 指到 v0101。自測:v0100 的 12 項 + 本版 4 項全過。
- Claude Desktop / Manus / Claude Code 設定:把 `python CGC_MDL279_MCPServer_v0101.py --client-config --root <倉根>` 印出的 JSON 貼進用戶端的 mcpServers。
