# 2026-11-10 晚 · 省 Token 全景卡 + 自建平台管理者版 + 同一組 MCP 給所有 AI

操作員四令合一:「新增一個引擎協助 AI 節省 TOKEN · 全景式分析到底 · 動詞引擎 · 與 AI 充分互動」·
「視覺鎖定為 U/I 模板 · 自建構省 TOKEN」·「OMNIROUTE 跨 AI · Claude 有的 ChatGPT / Manus / Gemini / Copilot 一樣 MCP」·
「VCGC 完成完善實測收尾 · 自建平台管理者版 · 卡片式:TOKEN 節省 · 中央管理 · 加速器 / 網路工具 / NLP / LAYOUT」。

先查既有才寫(不重工):骨架卡 / 切片 = CGC_MDL158 v0117;編號 = CGC_MDL237;鎖定模板 = VIA_WorkbenchLock v0102;
多平台 MCP 設定 = VIA_MCP_Engine v0102;VCGC MCP = CGC_MDL279 v0102。本輪只補它們沒有的那塊。

## 1. VIA_SystemCard v0100(`docs/handoff/ai/` · VCGC 發號 VIA-CORE-MDL861)

| 動詞 | 做什麼 |
|---|---|
| `scan <夾/倉…> --track A\|B [--ref origin/main] --out <夾>` | A = 本機資料夾;B = git ref(ls-tree / cat-file,私有倉也讀、不截斷)。兩軌各寫自己的輸出夾 |
| `card [--budget 3000] [--system S]` | 依 Token 預算出卡:事後閘 · 五系統矩陣 · 尾版入口(凍結前版只計數) |
| `find <regex>` · `where <名>` · `slice <檔> <定義>` | 定位 → 只取一段原文;`where` 前版只留 2 條 + 計數 |
| `system <S>` · `numbers [--missing]` · `diff <A> <B>` | 某系統尾版 · 編號覆蓋(只查不發)· A×B 對帳 |
| `mcp --out <夾>` | stdio 只讀 MCP:via_card · via_find · via_where · via_system · via_numbers · via_slice |

事後閘全實算:G1 檔案守恆 · G2 AST 守恆 · G3 掃描零變動 · G4 孤兒 ≤5% · G5 尾版編號覆蓋 · G6 來源可讀。
輸出:index.jsonl · summary.json · card.md · index.parquet · 每系統一頁 `VIA_SystemCard_<S>.html` + Hub(`index.html` / `matrix.html`)。
頁面全部套 WorkbenchLock 鎖站模板(css / js / 頁模板一字不改 + 品牌 + 響應式),鎖的 check 綠。
Hub = **管理者版**:五系統總表 + VCGC 卡片三區(省 Token 4 · 中央管理 7 · 支援工具 8);燈是實比 —— 鎖冊條目 sha 相符才綠,尾版檔在 = 黃(本頁不代跑自測),冊 = 冊自報燈。

### 容器實測(2026-11-10)
- 自測 15/15;交接案 V-systemcard-v0100 rc 0。
- B 軌 movies-dataset + via-vdf-vrn @ origin/main:51,117 檔 · 78 秒 · G1/G2/G3/G4/G6 綠 · G5 尾版 3,588 有號 2,225 空號 1,363(照實黃)。
- A 軌工作樹:51,292 檔 · G3 綠(A 軌預設不掃 VIA_Reports:輸出夾,別的行程一直在寫)。
- A×B:SYNC 50,849 · LOCAL_AHEAD 364 · A_SKIPPED 189 · SIZE_ONLY 70 · DIVERGED 7。
- 卡 ≈3,026 tokens(預算 3,000;閘與矩陣是必出段)。Playwright 1440 / 400 寬:pageerror 0 · console error 0 · 不橫捲。
- 本輪抓到並修的真 bug:號冊 MDL 2.6 MB 超過 1 MB 讀上限 → 原本「有號 0」;兩倉同掃時 VRN 標籤全域判 → VRN-2 被標成 VRN-1。

## 2. VIA_MCP_Engine v0103(倉根 · v0102 一字不改 · SHA 釘住)
- 目錄 +3:`via-systemcard` · `via-vcgc`(CGC_MDL279 尾版)· `omniroute`(`omniroute --mcp`;HTTP `http://127.0.0.1:20128/api/mcp/stream` 要 Bearer)。
- `parity`:同一組 MCP 套到 Claude Code · Claude Desktop · Codex · ChatGPT Chat · Manus · Gemini CLI · Copilot VS Code · Copilot github.com。
  本機 5 個寫設定(先備份,只合併本引擎管理的名稱;預設只渲染,`--write` 才寫);遠端 3 個給 supergateway 橋 + OmniRoute 原生 HTTP,**要 HTTPS 隧道 = 操作員的手,燈黃**;Gemini Chat 無 MCP 入口 = 灰。
- 自測 v0102 66/66 + v0103 11/11;主控台 v0192 契約 9/9(同 stem .html · 上限 5)。容器握手:via-systemcard 6 工具 · via-vcgc 17 工具綠;OmniRoute 沒裝 → RED 照實。

## 3. 桌機一行(PowerShell;在倉根)
```powershell
# A 軌兩夾 + B 軌兩倉,各寫各的夾,再對帳
python VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SystemCard_v0100.py scan "$env:USERPROFILE\OneDrive\Documents\VeritasIntelligenceAnalytics" "$env:USERPROFILE\OneDrive\Documents\movies-dataset" --track A --out VeritasIntelligenceAnalytics\VIA_Reports\systemcard\A
python VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SystemCard_v0100.py scan . --track B --ref origin/main --out VeritasIntelligenceAnalytics\VIA_Reports\systemcard\B
python VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SystemCard_v0100.py diff VeritasIntelligenceAnalytics\VIA_Reports\systemcard\A VeritasIntelligenceAnalytics\VIA_Reports\systemcard\B
start VeritasIntelligenceAnalytics\VIA_Reports\systemcard\B\index.html
# 同一組 MCP 給所有 AI(先看,再寫)
python VIA_MCP_Engine\VIA_MCP_Engine_v0103.py parity --probe
python VIA_MCP_Engine\VIA_MCP_Engine_v0103.py parity --write
# OmniRoute(要 Node 22.22–22.x 或 24–26;金鑰在它的儀表板設,不進倉)
npm install -g omniroute
```

## 4. 沒做 / 做不到(照實)
- OmniRoute 容器未裝(npx 60 秒握手逾時)→ 桌機裝;供應商金鑰只在它的儀表板。
- 遠端平台(ChatGPT · Manus · Copilot github.com · Claude Design)要 HTTPS 隧道,本引擎只給指令,不代開。
- 空號 1,363 支尾版程式:發號只經 CGC_MDL237(操作員排序)。
- Ponytail(Claude Code skill · 外部)· Amydoc(查不到是什麼)· autoharness(目錄裡的 harness 外掛可能是它,待操作員確認)· ChartDB(容器無)→ 未接,不冒充。
