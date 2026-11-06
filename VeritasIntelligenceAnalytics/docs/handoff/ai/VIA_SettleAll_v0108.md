# VIA_SettleAll v0108 · 一支程式 · 系統矩陣(操作員 2026-11-06「INTEGRATE ALL INTO ONE CODE · 守住所有已完成功能 · 矩陣式呈現 · 三種燈號 · 成功就記時間 / 版本 / 狀態 · Agent OS 屬於 VCGC」)

v0107 一字不動;新增 **⑫ 系統矩陣**,其餘段照舊(① 環境 ② AST ③ 同步 ④ VDF ⑤ VRN ⑥ VCGC ⑦ Graphify ⑧ VQG ⑨ Agent OS ⓫ 政策全景 ⑩ 報告)。

| 項 | 內容 |
|---|---|
| 矩陣列 | VRN-2 · VDF · **VCGC**(子列:Agent OS · Graphify · MCP 伺服器 · 政策全景 L103)· VQG · VAP(支援模組 · 未納入自動測試)|
| 三種燈 | 🟢 本輪實測過 · 🟡 能動但有條件 · 🔴 沒過(⚪ = 這輪沒測 · 例如 ③ 沒同步時 ④ ⑥ 不跑)|
| 欄 | 燈 · 版本尾(從工作樹家族尾版取)· 狀態(本輪)· 秒 · **上次綠(時間 · 版本)** |
| 成功就記 | 綠的那列追加到**只增帳** `VIA_Reports\settle\VIA_SystemMatrix_Ledger.jsonl`(時間 · 版本 · 狀態 · run)· 舊行不動;矩陣的「上次綠」欄從帳裡讀 → 這輪黃了也看得到已完成功能守在哪一版 |
| 輸出 | `VIA_Reports\settle\VIA_SystemMatrix_latest.json / .md / .html`;Windows 跑完自動開 HTML(`VIA_NO_OPEN=1` 不開);貼回包含帳 |
| MCP 子列 | 工作樹有 `CGC_MDL279_MCPServer_v*.py` 就跑它的自測(12 項 · 秒級);沒有 = ⚪「同步後才有」|

自測 37 / 37(新:矩陣燈 / 子列掛法 / 只增帳追加 2 筆 / 上次綠讀回 / 第二輪舊行不動)。容器實跑:9 列 · 🟢 2(Agent OS · MCP)🟡 2 🔴 1(VQG 容器無庫)⚪ 4 · 帳 +2。

## 桌機一行(PowerShell 7 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0108";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0108.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0108.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'A628681884170D4188CE3487BBE13ED2149CBF6B7681839F919B916BCEEE0741'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

桌機第一輪預期:VRN-2 🟡(DATA_GAP · 待修 0)· VDF ⚪(③ 沒同步不跑)· VCGC ⚪ · Agent OS 🟡 · Graphify 🟡 · MCP ⚪(工作樹沒同步)· VQG 🟡 · VAP ⚪。③ 那 28 支改動你裁定後再貼,VDF / VCGC / MCP 就會變成有燈。
