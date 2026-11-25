# VCGC 工具盤點與目標架構 v0100(規劃稿 · 只讀量測 · 沒改任何程式)

> 2026-11-25 操作員:「先做好整體的架構,盤點 VCGC 的工具重新架構」。
> 本稿承 `VIA_SystemArchitecture_SDD_v0101`(全系統五層與治理三冊),只講 **VCGC 自己的工具怎麼收斂**。
> 實作已交給 #745 那條線(操作員同日裁定);本稿是給那條線和操作員對齊用的藍圖。
> 量法:VCGC 省 Token 工具 `CGC_MDL158 v0121` 的 `tools` · `chain`,各入口自報的 `help`,以及只看檔名與 `ast.get_docstring` 第一行的家族盤點。沒有整檔讀任何大檔。容器量,未在主機實跑。

## 0 三數

- **應掃**:VIA 根下所有帶 `_vNNNN` 的 `.py`。
- **已掃**:482 個家族、1,146 支檔。依名稱分類如下:
  - CGC_MDL:286 家族
  - SUP_MDL:84 家族
  - VIA_*:54 家族
  - VCGC_*:3 家族
  - 其他:55 家族
- **略過**:
  - `functional modules/`:VDF、VRN、VAP、VQG 是獨立系統,不在 VCGC 範圍。
  - `VIA_RetiredEngines`、`intake`、`_quarantine`、`references`、`backup`、`archive`、`evidence`、`VIA_Reports`、`__pycache__`。

## 1 現況:VCGC 有 7 個對人入口,彼此重疊

| 入口 | 尾版 | 鏈長 | 自報角色 | 問題 |
|---|---|---|---|---|
| `CGC_SystemManager` | v0120 · 87 行 | 21 版(釘名 11) | REQ234:「VCGC SYSTEM MANAGER 控制一切」 | **`verbs` / `help` 都沒實作**,打下去印的是資料席位 JSON → ⑬ 裁定的「路由讀 `verbs --json`」在 VCGC 自己身上是灰 |
| `CGC_MDL149` 主控台 | v0202 · 299 行 | **101 版** | 「VCGC 自己的入口」:token、handoff、test、run、ssot、overview、monitor、synchronizer、graphify、agentos… | 實質上的總入口,但不是 REQ234 指定的那支;動詞散在 101 版裡 |
| `VCGC_CommandHub` | v0119 · 244 行 | 19 版 | 22 條 `via-*` 短令 + 21 個舊名 | 短令層,背後又叫主控台 / 管理器 / 各 runner |
| `VIA_SYSTEM_MANAGER` | v0151 · 103 行 | 52 版 | MasterControl 頁 | 名字像總管,實際只是一張頁 |
| `docs/handoff/ai` runner 群 | — | — | FastRun(6 版)· ApplyRun(9)· SettleAll(19)· HostBoot(1)· RepoSafeSync(7)· DailyBackup(4)· ReworkGuard(4) | 每支都是「一行跑完一串」,彼此重疊 |
| `CGC_MDL279` MCP | v0107 | 8 版 | 17 + 1 個工具(含 `vcgc_read_card`) | 對外 AI 的入口,OK |
| PS 殼 | — | — | `Register-VIA-Commands` v0186–v0219、`VIA_ProfileLoader`、Downloads 裡的 `Invoke-VIA-*` | 舊 PS 鏈與新 Python 鏈並存 |

**同一件事有多種打法**(違反 11-18「同一件事不給兩種打法」):

| 功能 | 現在的打法 |
|---|---|
| 備份 | `via-bak`(Hub)· `VIA_DailyBackup` · ApplyRun G 道 · `CGC_SystemManager backup` · `CGC_MDL*_SystemBackup` |
| 健康 / 環境 | `via-health`(FastRun)· `CGC_MDL274_HealthMatrix` · 主控台 `health` · 管理器 `toolbox check` · ApplyRun E 道 |
| Graphify | 主控台 `graphify` · Hub `via-graph` · `CGC_MDL280` · 外部 Phase0 工具 |
| 開機 / 一鍵 | `via_boot_update.ps1` · `VIA_HostBoot` · `VIA_SettleAll` · ApplyRun `go` · Hub `boot` · `VCGC_StartupEngine` |
| 交接 | 主控台 `handoff` · `CGC_MDL140_HandoverConsole` |
| 頁面 / 總覽 | 主控台 `overview` · `synchronizer` · `monitor` · `VIA_SYSTEM_MANAGER` · `CGC_MDL274` 頁 · `CGC_MDL283` |

**家族分群**:286 個 CGC_MDL 家族、880 支檔,依名稱關鍵字分:

| 群 | 家族 | 檔 | 代表 |
|---|---|---|---|
| G1 省 Token · 讀取 · 全景 | 26 | 53 | MDL158 PanoramaAuditRepair · MDL283 CardMatrixFeedback · MDL280 AgentOSHub |
| G2 編號 · 註冊 · SSOT · 冊 | 32 | 90 | MDL237 NumberingSystem · MDL245 SDDValidator · MDL270 RegistryGovernor |
| G3 交接 · 測試 · 收尾 · 鎖 | 44 | 92 | MDL140 HandoverConsole · MDL224 TestAuto · MDL064 SelftestGrid · MDL056 InstallGate |
| G4 環境 · 安裝 · 加速器 · 網路 | 35 | 86 | MDL274 HealthMatrix · MDL233 ToolActivate · MDL124 BridgeSweeper · MDL135 EnvGovernance |
| G5 UI · 頁面 · 監控 · 報告 | 31 | 61 | MDL261 UIEngine · LocalMonitor |
| G6 備份 · 同步 · Git · 還原 | 5 | 8 | SystemBackup · SyncStatus |
| G7 啟動 · 排程 · 並行 | 6 | 19 | MDL127 SixStreams · VDFChainRunner · VRNChainRunner |
| **G0 名字分不出來** | **107** | **271** | 含 MDL149 主控台、MDL279 MCP、EngineBus、CentralGovernanceEngine |

另外,CGC 家族有 **73 支尾版超過 400 行**。

## 2 目標架構:一個入口 → 七個服務群 → 引擎 → 鎖冊工具

```
L0  短令(PS 只進環境)  via-<動詞>                       ← VCGC_CommandHub 尾版:只做「名字 → 管理器動詞」對照,不寫邏輯
L1  Python 啟動器        降壓 → 3~6 道 → 監工              ← 共用 SafeParallelLaunch 判法
L2  VCGC 唯一入口        CGC_SystemManager 尾版             ← REQ234;verbs --json / help / version / health 必備
L3  服務群(7)          G1 讀取 · G2 冊號 · G3 驗收 · G4 環境 · G5 頁面 · G6 備份同步 · G7 啟動
L4  引擎                 現有 CGC_MDL 家族,一支做一件事,能單獨 --selftest
L5  工具                 鎖冊 9 支:accelerator · network · token · nlp · layout · frame · praddle · pdfplumber …
```

**規則**:

1. **入口唯一**。`CGC_SystemManager` 是 VCGC 唯一對人入口(REQ234)。
   - 主控台 MDL149 降為 G1 / G3 的服務群本體。
   - 原有動詞照舊能叫,不刪(轉接,成功只增不減)。
2. **一個功能一個動詞**。上面六組重疊各收成一個管理器動詞,舊打法全部變轉接:
   - `backup`:`backup` · `backup restore` · `backup card`
   - `health`:環境 · 加速器 · 網路 · 工具冊
   - `graph`:status · build · query
   - `boot`:同步 → 先期檢查 → 收據
   - `handoff`:check · test · checkpoint · daily
   - `overview`:一張頁
3. **路由表自報**。
   - 管理器出 `verbs --json`,每列寫:動詞 → 服務群 → 引擎家族 → 鎖冊工具 → 舊名。
   - Hub 的 22 + 21 條、主控台的動詞、MCP 工具都從這張表產生,不各自維護。
   - 這也就是 ⑬ 裁定的路由來源。
4. **行數量本體**。管理器本體合併後 ≤ 400 行(SDD v0101 B1);服務群單檔 ≤ 500 行,超過就拆。
5. **runner 歸位**:
   - FastRun、ApplyRun、SettleAll、HostBoot 的步驟改成 `boot` 動詞的道。
   - RepoSafeSync、DailyBackup、ReworkGuard 留作 G6 / G3 的引擎。

## 3 第一批(低風險、可單獨上線,每步都是薄尾新版,不刪檔)

| # | 做什麼 | 為什麼先做 | 驗收 |
|---|---|---|---|
| 1 | `CGC_SystemManager` 新版補 `verbs --json` · `help` · `version` | 現在打 `verbs` 印的是資料席位;⑬ 路由在 VCGC 身上是灰 | `verbs --json` 列出所有動詞 → 服務群 → 引擎;自測從 PS 的 x 路與選單兩條路打進去 |
| 2 | 管理器路由表 + `conform --contract` | 讓 Hub / 主控台 / MCP 從同一張表產生 | 舊名全部指得到;差異 0 |
| 3 | 六組重疊各收成一個動詞(先轉接、不搬程式) | 解「同一件事多種打法」 | 每個舊打法印一行「舊 → 新」後照跑;結果與前版逐位元相同 |
| 4 | G0 的 107 個家族逐一歸群(只標冊,不改檔) | 名字分不出來就無法分責 | 元件冊每列有 `group` 欄;未歸群 0 |
| 5 | 主控台 101 版鏈:用 `chain` 標本體,出「本體合併版」候選 | 鏈太長,每次載入要走 101 層 | 合併版自測 = 原鏈自測;原鏈照留(刪除照 REQ262 三條另案) |

## 4 不做的事

- 不刪任何檔:退役閘 11-25 證明 0 / 78,寫死前版名的拆掉之前刪不了。
- 不跨系統改檔:VDF / VRN 的 `verbs --json` · `handoff` 由它們自己的管理器補。
- 不改 `.ps1` 既有檔,不新增引擎種類;新能力掛既有家族的新動詞。

## 5 待操作員裁定

| # | 題目 | 裁定前怎麼做 |
|---|---|---|
| A | VCGC 唯一入口是 `CGC_SystemManager`(照 REQ234),還是主控台 MDL149(現在實際在用的)? | 照 REQ234,主控台當服務群;兩邊都能叫 |
| B | 六組重疊動詞的正名用哪個字(例:`bak` 還是 `backup`) | 取管理器已有的字,短令名照舊 |
| C | runner 群(FastRun · ApplyRun · SettleAll · HostBoot)收成 `boot` 的道之後,舊 runner 何時停用 | 標「轉接」,不停用 |

NEXT: 操作員裁 A / B / C → #745 那條線照第 3 節第 1 步開始(管理器 `verbs --json`)。
