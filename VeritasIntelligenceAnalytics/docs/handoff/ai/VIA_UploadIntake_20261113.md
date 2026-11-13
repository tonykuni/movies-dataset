# 上傳件與 PC 檔導入檢查(2026-11-13)

> 操作員令:「檢查有無導入」「檢視工具有無整合 若無則擷取整合進去」;另:「強化 MCP to ChatGPT · Gemini · Claude · Manus · PC FILE」「MCP TO GITHUB 將資料引擎抓進來」「導入」
> 比對法:只讀;git blob + sha256;上傳件不在倉內執行,自測只在拋棄式副本跑。

## 一、上傳的 3 個 zip(讀得到 → 已比對、已收容)

| 上傳 | 結果 | 處置 |
|---|---|---|
| `VCGC_Test_Closeout_v0100.zip` ×2(同 sha `f6901309…`) | 倉內 **沒有**(16 檔 sha 全不在 main 與任一遠端分支,僅 native/VCGC v0194 與 `optimistic-goodall-yhalc5` 分支同 sha)| 原樣收容 `supportive modules/references/intake/VIA_Uploads_20261113/VCGC_Test_Closeout_v0100/`;自帶 SHA256SUMS 16/16 對上;拋棄式副本自測 17 項:16 ok · 1 skipped(選配 `mcp==1.29.0` 不在,AI 不代裝)|
| `wl0104.zip` | 與 `practical-pasteur-p67i78` 分支 `Invoke-VIA-WorkbenchLocal-v0104.ps1` **內容相同只差換行**;main 沒有 WorkbenchLocal | 原樣收容(CRLF 保留,intake 為 -text)|

**為什麼只收容、不啟用**:Test Closeout 與 VCGC 既有的 `closeout` 動詞、`CGC_MDL224` 自動測試、SDD 重疊(L116 一功能一主),它依賴的 VCGC v0194 不在 main;要接成現役引擎,需操作員先定:以它取代哪一段、或只當 F21–F30 的規格來源。

## 二、PC 上的檔(只有檔名 → 只比得到名字)

本 session 沒有可用的 Remote Control 電腦資料夾(`list_computer_folders` 空),容器讀不到 `C:\Users\tonyk\…`。下表只按**檔名**比對 main 與全部遠端分支;「main 有同名」不代表同一版,內容要上傳後才比得出來。

**合計 34 檔:倉內沒有 24 · 已導入(解開版)1 · main 有同名 8 · 只在未合併分支 1。**

| 檔 | 狀態 | 位置 |
|---|---|---|
| `Invoke-VIA-VCGC-MorningEnable-v0101.ps1` | **倉內沒有** | — |
| `Invoke-VIA-VCGC-MorningEnable-v0100.ps1` | **倉內沒有** | — |
| `vcgc-morning.skill` | **倉內沒有** | — |
| `VIA_Policy_Law_Candidate_MorningFirstAction_v0101.json` | **倉內沒有** | — |
| `VIA_Policy_Law_Candidate_MorningFirstAction_v0100.json` | **倉內沒有** | — |
| `VIA_Extraction_Matrix.csv` | **倉內沒有** | — |
| `CGC_CloseoutIntegrate_v0104.py` | **倉內沒有** | — |
| `CGC_Panorama2Roots_v0103.py` | **倉內沒有** | — |
| `CGC_CloseoutIntegrate_v0103.py` | **倉內沒有** | — |
| `CGC_Panorama2Roots_v0102.py` | **倉內沒有** | — |
| `Invoke-VIA-CloseoutAll-v0103.ps1` | **倉內沒有** | — |
| `Invoke-VIA-CloseoutAll-v0102.ps1` | **倉內沒有** | — |
| `CGC_CloseoutIntegrate_v0101.py` | **倉內沒有** | — |
| `Invoke-VIA-Closeout-v0101.ps1` | **倉內沒有** | — |
| `CGC_Panorama2Roots_v0101.py` | **倉內沒有** | — |
| `Invoke-VIA-Panorama2-v0101.ps1` | **倉內沒有** | — |
| `VIA_VCGC_Commercial_Review_v0100.zip` | 已導入(zip 本身不在,解開版在倉)| `review/VIA_VCGC_Commercial_Review_v0100/`(需求冊 v0247 記錄)|
| `VIA_CentralGovernanceEngine.py` | main 有同名(內容未比:檔在 PC) | `VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/VIA_CentralGov` |
| `VIA_DownwardController.py` | main 有同名(內容未比:檔在 PC) | `VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/VIA_DownwardCo` |
| `VIA_EngineHardening.py` | main 有同名(內容未比:檔在 PC) | `references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VIA_Eng` |
| `VIA_EnvDeepProbe.py` | main 有同名(內容未比:檔在 PC) | `references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VIA_Env` |
| `VIA_FilePriorityRouter.py` | main 有同名(內容未比:檔在 PC) | `VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/VIA_FilePriori` |
| `VIA_Launch_NonBlocking_v0100.ps1` | main 有同名(內容未比:檔在 PC) | `references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VIA_Lau` |
| `VIA_Polyglot_Repair_Injector_v0100.ps1` | main 有同名(內容未比:檔在 PC) | `references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VIA_Pol` |
| `VIA_Profile_Doctor_v0100.ps1` | **倉內沒有** | — |
| `VIA_Recover_v0110.ps1` | **倉內沒有** | — |
| `VIA_Round1_CodeRepair_v0100.ps1` | **倉內沒有** | — |
| `VIA_SameNameConsolidator_v0100.ps1` | 只在未合併分支 | VIA_AzureFlow, accel-match … |
| `VIA_SameNameConsolidator_v0110.ps1` | **倉內沒有** | — |
| `VIA_TestAccelerator.py` | **倉內沒有** | — |
| `VIA_ToolchainInstaller_v0100.ps1` | **倉內沒有** | — |
| `VIA_VersionGuard_v0110.ps1` | **倉內沒有** | — |
| `VIA_AuthorityAudit.py` | **倉內沒有** | — |
| `VIA_CentralGovernanceConsole.py` | main 有同名(內容未比:檔在 PC) | `VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/VIA_CentralGov` |

## 三、撞號警示(另一條進行中的分支)

`claude/optimistic-goodall-yhalc5`(領先 main 53 提交、2026-11-13 仍在推)與本分支同時改到:
`CGC_MDL279_MCPServer_v0103.py`(兩邊同名不同內容)· 需求冊 v0249(該分支已到 v0251)· **VCGC-REQ223**(該分支已用於他事)· 功能盤點冊 v0225(該分支已到 v0239)· 交接冊 · 元件冊 · 編號冊。
這些在合併時都會以 git 衝突出現,不會無聲覆蓋;依 L25 由後合併那一手取聯集、程式檔高版號另起(本分支 MCP 改 v0104 即可接在對方 v0103 之後)。**合併先後由操作員定。**

## 四、MCP 強化(PC 檔 · 四平台 · GitHub)現況

已在倉(VIA_MCP_Engine v0102/v0103 + CGC_MDL279):官方 filesystem(本機讀寫,只開點選的資料夾)· GitHub MCP(唯讀 PAT · read_only 預設開)· 8 平台設定(Claude Desktop/Code · Codex · ChatGPT 網頁 · Gemini CLI · Manus · Copilot)· 遠端平台 supergateway 橋 + OmniRoute · via-vcgc MCP 讀檔三動詞(本批)。
缺口(待做):遠端平台的**唯讀 PC 工作夾**全景讀取(CGC_MDL279 `--files-root`,沿用本批的路徑閘與鎖版工具)· 橋接層驗證金鑰 · 通道(Cloudflare Tunnel / Access)由操作員開。Gemini 網頁版冊上仍記「無 MCP 入口」,貼文說可經 Connected Apps,未查證前不改。
「將資料引擎抓進來」:ChatGPT 分享頁只讀得到「Check out this chat」,看不到內容 → 需操作員指名倉 / 引擎名。
