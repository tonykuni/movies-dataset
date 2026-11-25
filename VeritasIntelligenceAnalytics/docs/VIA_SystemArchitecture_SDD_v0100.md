# VIA 獨立系統標準架構(SDD 規劃書)v0100

> 2026-11-25 依操作員令(17:53):
> 「系統亂掉了。根據現在 CLAUDE.md SDD 規範,從頭規劃 VCGC / VDF SYSTEM MANAGER / VRN SYSTEM MANAGER 的架構,先忽略現在有什麼功能。
> 然後善用 VCGC 讀取所有相關聯的檔案,分類整合,補上新架構的功能,還有空的再補。
> 獨立系統架構 · 不可用 TA-Lib · 用 PY 寫指令(含短指令)· 全部按照既有 CLAUDE.md。
> 接下來所有動作 AI 都要優先選擇 VCGC 的動作去完成,寫入 CLAUDE.md。
> 先寫規劃,再想目前功能如何模塊化重組,來完成 VCGC。」
>
> - 需求號:VCGC-REQ265。
> - 狀態:**規劃稿,等操作員核准**。本稿沒有改任何程式。
> - 現況數字都是雲端容器在 main `29dc2804a` 上用 VCGC 工具量的,不是主機實測。
> - 用到的 VCGC 工具:token 卡 · `delta` · `read` · `slice` · `chain` · 各管理器的 `help`,以及 11-22 VCGC 清點(應列 362 · 已列 362 · 略過 0)。

---

## 0 為什麼要重新規劃(現況量到的)

| 量到的現象 | 數字 | 違反 CLAUDE.md 哪一條 |
|---|---|---|
| VCGC 有三個入口同時在用:主控台 `CGC_MDL149`(101 版、60 個動詞)· 管理器 `CGC_SystemManager`(21 版)· 短指令中樞 `VCGC_CommandHub`(17 版);另有 26 個「入口 · 管理器 · 指令台」家族 | 3 + 26 | 指令模塊化:同一件事不給兩種打法 |
| `CGC_SystemManager` 沒有標準動詞:`help` `version` `verbs` `health` `status` 全都落到「資料座」卡;印出的版本是 v0115,實際尾版是 v0120 | 5 個動詞 0 個有效 | 三系統對等:各由自己的 SystemManager 控制一切 |
| `via-vdf` / `via-vrn` 由 VCGC 的 `VCGC_CommandHub` 轉交給 VDF / VRN 的管理器(v0102 第 12 行) | VCGC 壞 = VDF / VRN 短指令也壞 | 系統獨立:避免 VCGC 升級造成全面癱瘓 |
| 倉根有 205 個 `via-*.cmd` 舊短指令 | 205 | 只留 via-vdf / via-vrn / via-vcgc / via-view(L119) |
| 薄尾鏈太長:VCGC 主控台 101 版 · VRN 管理器 96 版 · VDF 管理器 90 版 | — | 重複功能先併再簡化 |
| `supportive modules` 有 813 個家族,沒有「屬於哪個系統」的欄位 | 813 | 每個系統只寫自己的冊與夾 |
| 「VRN 報告鏈治理件」放在 VCGC | 33 個家族 | 獨立系統該有的功能分給各自系統(REQ234) |
| 程式檔沒登記(token 卡監控) | 2438 支 | 新增照「需求 → 工作流 → 註冊 / 編號」 |
| 字串釘死前版當路徑(delta 新增) | 11 處 | 刪舊版先證明(懶載入、釘死名字都算用到) |

**檔案量**(容器以 git ls-files 量,不含收件 / 參考夾)

| 系統 | 家族 | 檔 |
|---|---|---|
| VCGC | 298 | 1573 |
| VDF | 184 | 717 |
| VRN | 283 | 811 |
| VAP | 87 | 158 |
| VQG | 2 | 11 |
| SUP(未分主) | 813 | 1063 |

結論:各個功能多半都在,問題出在**入口太多、主人不明、鏈太長**。所以本稿先定架構,再把現有家族逐一放進新位置;空著的位置之後再補。

---

## 1 設計原則(每條都對到 CLAUDE.md)

1. **五個系統對等獨立**:VCGC · VDF · VRN · VQG · VAP 各有一個 SystemManager,是自己唯一的入口。
   - 不改別的系統的正本 / 冊 / 號 / 檔。
   - 互相只讀對方自報的燈與收據。
   - 依據:開頭「系統對等獨立」· REQ234。
2. **拿掉 VCGC 也能活**:在拿掉 `CGC_*.py` 的副本上,VDF / VRN 的入口、短指令、現役引擎都要載得起來。用到 VCGC 工具的地方一律要有退路,工具不在就亮灰燈,不准丟例外。依據:補強三。
3. **PY 是全部,PS 只啟動**:
   - 判斷、迴圈、檢查、註冊、編號、報表全都寫在 Python。
   - 短指令(`.cmd` / PS 函式)只做三件事:進環境 → 呼叫該系統的 Python 啟動器 → 開它產出的 U/I。
   - 依據:L117 · 舊短指令改走 Python · REQ262 §3。
4. **加速器 100%(掛橋)· 網路工具 100%(對外擷取的檔)**:以語法樹裡真的匯入 + 執行時載得到為準。禁用 TA-Lib。依據:補強三 · REQ262 §3。
5. **SSOT 一套、寫權分開**:
   - 跨系統只共享 SSOT 冊與標準正則。
   - 每個系統只寫自己的冊;VRN / VDF 自己發自己帳本的號(11-21 裁定)。
   - VCGC 只替程式檔與律條發中央號。
6. **只增不減**:出新版號檔,前版不動;已鎖成功數只增不減。刪舊版要照待裁定 2 的三條件。
7. **SDD**:需求冊 → 工作流冊(輸入 / 輸出 / 完成條件)→ 實作 → 測試 → 註冊 / 編號 → SDD → `handoff checkpoint`。
8. **省 Token**:讀檔走 VCGC token 工具;AI 先選 VCGC 的現成動作(見 §12 寫入 CLAUDE.md 的新規)。
9. **資料邊界**:能離開本機的只有程式結構與 schema。
10. **U/I 已視覺鎖定**:每個系統一張靜態雙欄頁(左輸入、右分頁),只同步內容,不改視覺值。

---

## 2 總架構

```
                 操作員(滑鼠 · 一行短指令)
                          │
   ┌──────────┬──────────┼──────────┬──────────┐
 via-vcgc    via-vdf    via-vrn    via-vqg    via-vap        ← L0 短指令(各自直指自己的 L1,互不經過)
   │           │          │          │          │
 CGC 啟動器  VDF 啟動器  VRN 啟動器  VQG 啟動器  VAP 啟動器    ← L1 Python 啟動器(入口標記 · 降壓 · 3~6 道 · 監工)
   │           │          │          │          │
 VCGC SM     VDF SM     VRN SM     VQG SM     VAP SM          ← L2 SystemManager(同一份動詞契約,§3)
   │           │          │          │          │
 VCGC 服務群  VDF 服務群  VRN 服務群   …          …            ← L3 服務(本系統自己的功能群)
   │           │          │
 引擎        擷取引擎     分析 / 報告引擎                        ← L4 引擎(各自能單獨啟動 · --selftest)
   └───────────┴──────────┴──── L5 共用件(唯讀使用;鎖冊指定):加速器橋 · 網路工具 · token 工具 · U/I typekit

系統之間只有三條線(§7):① SSOT 冊唯讀 ② 資料契約(VDF 發布 → VRN 唯讀)③ 自報收據(燈 · 收據 JSON)唯讀
VCGC 的合併檢視頁 = 監控用,不是入口。
```

---

## 3 SystemManager 標準契約(五個系統同一份)

每個 SystemManager 都要有下面這張動詞表,名稱、參數形狀、rc 一致。

### rc 與收據
- **rc**:0 綠 · 1 紅 · 2 黃 / 過期 / 沒量 · 3 缺件 · 4 等同意閘(沿用 VDF / VRN 現行)。
- **收據**:每個動詞寫一份 `VIA_Reports/<sys>/<verb>/<VERB>_latest.json`,欄位:系統 · 動詞 · 版本 · UTC · rc · 燈 · 三數(應 / 已 / 略過)· 證據路徑。

### 標準動詞

| 群 | 動詞 | 做什麼 | 完成條件 |
|---|---|---|---|
| A 身分 | `help` · `version` · `verbs [--json]` | 動詞表、每個動詞由哪一版處理、版本鏈 | `verbs --json` 機器可讀;三數對得上 |
| A 健康 | `health` · `status` | 自己的環境、套件、冊、資料家;只報自己 | 缺件 rc 3,不丟例外 |
| B 執行 | `launch [--plan]` · `run <引擎>` · `engines` · `params` | 降壓 → 3~6 道 → 監工;單一引擎單獨跑;參數從參數冊讀 | 子行程每 30 秒內有心跳;容器結果標「容器」 |
| C 驗證 | `selftest` · `test [--quick]` · `conform` · `closeout` | 自測;串測;CLAUDE.md 合規(加速器 / 網路橋 / TA-Lib / PS / 獨立性);收尾燈 | `conform` 用 AST 判;收尾燈只認主機實跑 + 輸出驗證 + U/I |
| D 帳冊 | `records` · `ssot` · `number` · `sdd` | 自己的收據、冊、自己的號、自己的 SDD | 只寫自己的冊 |
| E 觀察 | `monitor` · `peers` · `page` | 彙總自己的引擎;只讀別人的自報;靜態雙欄 U/I | 沒有對應引擎的格子亮灰 |
| F 維護 | `backup` · `graph` · `tools` | 備份、圖譜、列出可用的支援工具 | VCGC 工具不在 → 灰,不中斷 |

- 每個系統的業務動詞(VDF 的 `parquet` `datamatrix`、VRN 的 `extract` `provenance` 等)掛在標準表後面,一個功能只有一個動詞。
- 舊動詞(`enter` `door` `go` `all` 這類)改成轉接到新動詞,印出「已改名 → 新動詞」,不刪。

---

## 4 VCGC 系統(先做)

VCGC 是治理系統。它的服務是給所有系統**唯讀使用的治理工具**,但不是別人的閘門。

### 入口
- `via-vcgc <動詞>` → CGC 啟動器 → `CGC_SystemManager`(唯一入口)。
- `CGC_MDL149` 主控台降為服務群 **G0 主控台**:它的 60 個動詞依 §11 對到 SM 的動詞。
- `VCGC_CommandHub` 降為「短指令目錄」,只負責 `via` / `via-help`(列出 · 說明)和 VCGC 自己的短指令。**它不再轉交 via-vdf / via-vrn**。

### 服務群

| 服務群 | 做什麼 | 給誰用 |
|---|---|---|
| G1 讀取與省 Token | token 卡 · read · slice · digest · pack · chain · delta · brief · tools · verbs | 全部 AI;各系統的 `tools` 動詞唯讀列出 |
| G2 規則與政策 | CLAUDE.md · 政策律冊 · 同義字 / 正則 / 參數 / 契約冊 · conform 規則 | 規則是資料(冊);各系統自己的 `conform` 讀冊來判 |
| G3 編號與註冊 | 中央編號(程式檔 · 律條)· registry-sync · audit · 元件冊 · 引擎版本冊 | VCGC 發號;VDF / VRN 自己的帳本號自己發 |
| G4 需求 · 工作流 · 交接 · 收尾 | 需求冊 · 工作流冊 · handoff · closeout 帳 · 已鎖成功帳 · 每日教訓帳 | 全部系統登需求(寫入權照冊) |
| G5 環境與安裝 | via-health · 八路衝突 · 三鏡像 · 安裝閘 · envgov 計畫 · 工具鎖冊 | 安裝的唯一大門 |
| G6 閘與守門 | 重工守門 · secrets · 同意閘檢查 · 鎖 · 預檢 | 推送 / 發號 / 開 PR 前 |
| G7 覆蓋與橋 | 加速器 / 網路橋的 AST 覆蓋率 · 注入(先複製到 TEMP)· 獨立演練 | 只報,修補由各系統出新版 |
| G8 同步 · 備份 · 圖譜 · MCP | 每日備份 · Graphify(本機 AST)· MCP / omniroute · GitHub | 各系統的 `backup` / `graph` 可呼叫;不在就灰 |
| G9 跨系統觀察 | 讀各系統自報的收據 → 合併檢視頁 | 監控,不是入口;只攤開,不代修 |

### VCGC 自己的引擎
- 排程 / 啟動:候選是 `VCGC_StartupEngine`。v0100 本體 + v0101 薄尾已在 main;單檔有 DAG、硬體配額、完成典籍、各系統掛載契約。
- 它只排 VCGC 自己的工作。VDF / VRN 各用自己的啟動器(`VDF_MDL022` / `VRN_MDL260`)。

---

## 5 VDF 系統

- **入口**:`via-vdf <動詞>` → VDF 啟動器 → `VDF_SystemManager`。

| 服務群 | 做什麼 |
|---|---|
| D1 範圍與參數 | 擷取範圍冊(全台股 · 主動式 ETF · 指數 · 財報名單 · 國際)· 宇宙冊 · 參數冊;改一族整族一起改 |
| D2 擷取引擎 | 一個來源一支引擎;網路工具 100%;同意閘 fail-closed;主路失敗走備用,輸入輸出不變 |
| D3 啟動與排程 | 降壓 → 3~6 道 → 監工 → 合併(單一寫入者 · 只補缺鍵) |
| D4 資料平面 | DuckDB / parquet · 資料家(`VDF_DataHome_SSOT`)· datamatrix(多餘列 > 0 = 黃) |
| D5 品質 | 輸出對表頭冊 · 覆蓋報告(要求的目標缺一不綠、逐一點名)· 每晚限量真擷取 |
| D6 發布 | 資料契約:發布表 + 資料集收據(schema 在 SSOT)給 VRN 唯讀 |
| D7 U/I | VDF 自己的雙欄頁 |

---

## 6 VRN 系統

- **入口**:`via-vrn <動詞>` → VRN 啟動器 → `VRN_SystemManager`。
- VRN-2 為主;VRN-1 經 `VRN2_PeerBridge` 只讀借用。

| 服務群 | 做什麼 |
|---|---|
| R1 輸入 | 只讀 VDF 發布的資料契約(唯讀連線,不 import VDF 程式);研報收件 |
| R2 分析引擎 | 因子 · 族群 · 資金流 · 財報;純 Python / 數值庫,禁 TA-Lib |
| R3 報告鏈 | 報告組裝 · 版面 · NLP 摘要;現在放在 VCGC 的「VRN 報告鏈治理件」33 家族歸還這裡 |
| R4 啟動與排程 | `VRN_MDL260`;道數在 `VRN_ParamControl_SSOT` |
| R5 品質 | 報告驗證 · provenance(資料來源可追) |
| R6 同儕橋 | VRN-1 只讀 |
| R7 U/I | VRN 自己的雙欄頁 |

VQG / VAP 套同一份契約(§3)。這一輪只登位置,不動工。

---

## 7 系統之間的介面(只有三條)

1. **SSOT 冊**:各冊有「主人」欄;主人寫,別人只讀。
2. **資料契約**:
   - VDF 發布資料集(表名 · schema · 起訖 · 列數 · 收據 sha)。
   - VRN 用唯讀連線讀;VDF 改 schema 要出新版契約,舊版保留到 VRN 換完。
3. **自報收據**:各系統把 `health` / `monitor` / `closeout` 的收據寫在自己的報告夾,別人只讀。

**不允許的**:跨系統 import · 寫別人的夾或冊 · 經別人的程式轉交自己的入口。`conform` 用 AST 驗:直接 import 他系統模組 = 紅。

---

## 8 家族與版本

- 一個功能 = 一個家族 = 功能檔名(家族名 + `_vNNNN`)。
- **本體合併(fold)**:薄尾鏈太長時,把整條鏈的行為併成一支新版本體(不再靠 PRIOR)。
  - 合併後:公開名稱不少(TAILAPI 0)· 每個動詞實跑結果和合併前一樣 · 已鎖成功數不變。
  - 合併後舊版能不能刪,照待裁定 2 的三條件。
- 附件提案「同一引擎最多留現行版 + 兩個備份(N-2)」= 合併之後的目標,列入待裁定 9。裁定前不刪。

---

## 9 SDD 階段與驗收

| 階段 | 內容 | 驗收條件 | 誰 |
|---|---|---|---|
| P0 基線 | 鎖住現況:各管理器 `verbs` / `chain` / 已鎖成功數 / 註冊數 | 基線收據 | AI(唯讀) |
| P1 規格 | 本稿 + 需求冊(VCGC-REQ265)+ 工作流冊每系統一條(輸入 / 輸出 / 完成條件) | 操作員核准本稿 | 操作員核准 |
| P2 對位 | §11 的對照表做成機器可讀冊(家族 → 系統 · 服務群 · 動詞 · 本體 / 備份 / 退役候選) | 應列 = 已列,略過 0 | AI |
| P3 契約 | 三個 SM 各出新版:補齊 §3 標準動詞(轉接到現有功能,不重寫引擎)+ `conform --contract` | 三個 SM 的 `verbs --json` 都對得上契約 | AI → 操作員主機實跑 |
| P4 歸位 | 逐服務群:選本體、本體合併、標備份 / 退役;一次一個家族 | 每個家族合併前後動詞結果一致 · 已鎖成功數不減 | AI(一家一 PR) |
| P5 獨立演練 | 拿掉 `CGC_*` 的副本上跑 VDF / VRN 的入口與引擎;短指令直指自己 | 載不起來 = 紅並點名 | AI(容器)+ 主機 |
| P6 驗收 | 主機實跑 + 輸出驗證 + 操作員用滑鼠走完 U/I | `closeout_lamp` 綠 + SDD 綠 | 操作員 |

**順序**:VCGC(P3 → P5)→ VDF → VRN → VQG / VAP。每完成一項就 註冊編號 → 寫鎖定帳 → 提交推送 → 回報。

---

## 10 VCGC 第一批(核准後就做)

1. `CGC_SystemManager` 新版:補 §3 的 A 群(`help` · `version` · `verbs --json` · `health` · `status`),版本字串由檔名取,不寫死。
2. 把主控台 60 個動詞依 §11 做成 SM 的轉接表(`verbs` 印出「動詞 → 由哪個家族處理」)。
3. 新增 `conform --contract`:檢查任一 SM 的 `verbs --json` 是否符合 §3。三個系統都能跑,VCGC 不在時 VDF / VRN 用自己的副本規則(規則在 SSOT 冊)。
4. 短指令改道規格:via-vdf / via-vrn 直指自己的啟動器。先出規格與演練腳本;動 `.ps1` 既有檔不在授權內,由操作員決定。

---

## 11 現有功能怎麼重組(對照表)

### 11.1 VCGC:11-22 清點的 25 群 → 新位置

| 清點群(項數) | 新位置 | 怎麼處理 |
|---|---|---|
| 入口 · 管理器 · 指令台(26) | 入口 = `CGC_SystemManager`;G0 主控台 = `CGC_MDL149` | 其餘 24 家族(AutoPilot · MasterHub · MDL069 SystemManager · UnifiedShell · EngineBus · GovernanceConsole ×2 · CommandDeck …)改成轉接,列退役候選 |
| 主控台動詞:同步與觀察(9) | §3 E 群 · G9 | `sync` `sync-check` `synchronizer` 併成 `monitor` 的子動詞;`peers` `records` 保留 |
| 主控台動詞:頁面與外掛(6) | E `page` · G8 | `onepage` `overview` 併入 `page`;`agentos` `graphify` `mcp` 進 G8 |
| 主控台動詞:入口與流程(12) | A · B 群 | `enter` `door` `go` `all` `run-all` `exec` `activate` `gate` 併成 `launch` / `run`(舊名轉接) |
| 主控台動詞:測試與驗收(10) | C 群 | `check` `probe` `val` `audit` 收進 `test` / `conform` 的子動詞;`sdd` 移 D |
| 主控台動詞:SSOT · 編號 · 註冊(7) | D 群 · G3 | `books` `lexicon` `link` `register` `register-plan` `registry-sync` `ssot` |
| 主控台動詞:省 Token 與交接(9) | G1 · G4 | `token` `tools` `chain` `nlp` `layout` → G1;`handoff` `closeout` `ledger` → G4 |
| 主控台動詞:盤點與全景(7) | G1 · E | `panorama` `inventory` `matrix` `engines` `manifest` `workflow` `dbm` |
| 編號 · 註冊 · 命名(21) | G3 | 含紅燈 `CGC_MDL278_NumberGrant`(VDF / VRN 已自己發號,先確認還有沒有人用) |
| 環境 · 套件 · 工具版本(15) | G5 | 已大致齊(REQ258) |
| SSOT · 同義字 · 正則 · 參數 · 契約(15) | G2 | 含紅燈 `CGC_MDL246_ValidationSSOT` |
| 閘 · 鎖 · 預檢(19) | G6 | 重工守門(ReworkGuard)當本體 |
| 測試 · 驗收 · 收尾 · 交接(27) | G4 · C 群 | `CGC_MDL140_HandoverConsole` 當交接本體 |
| 覆蓋率 · 橋 · 加速器(19) | G7 | — |
| 治理 · 政策 · 禁令(20) | G2 | — |
| 同步 · 備份 · GitHub · 部署(10) | G8 | — |
| 跨系統只讀觀察(15) | G9 | — |
| **VRN 報告鏈治理件(33)** | **歸還 VRN R3 / R5** | VRN 出新版接手;VCGC 端只留只讀觀察 |
| NLP · 版面 · 文件收件(14) | G1 | 鎖冊的 `nlp` / `layout` 當本體 |
| AI · MCP · Agent 外掛(9) | G8 | — |
| 全景 · 省 Token · 稽核(10) | G1 | `CGC_MDL158` 當本體 |
| 修補 · 救援(8) | G7 | — |
| 工作流 · 流程(4) | G4 | — |
| 鎖版工具(9) | L5 共用件 | 鎖冊指定,唯讀使用 |
| 頁面 · U/I · 矩陣 · 報告(21) | E `page` · G9 | 含紅燈 `CGC_MDL095_DeckServer`(靜態頁不需要 server,列退役候選) |
| 沒有版號的檔(7) | 登記或退役 | 先登記再判 |

### 11.2 VDF 管理器 35 個標準動詞 + 資料平面 3 個(scope · inputs · parquet)+ monitor · synchronizer → 契約

| 契約群 | 現有動詞 |
|---|---|
| A | help · version · health · status · route |
| B | launch · engines · engine-matrix · params · scope · inputs |
| C | selftest · test · conform · parity · closeout · datamatrix |
| D | records · ssot · regex · synonyms · number · sdd · catalog · links |
| E | peers · page · monitor · synchronizer |
| F | backup · graphify · omniroute · mcp · install · bridges · tools · conflict · read · sync · parquet |

- **缺**:`verbs --json`。
- **改名**:`graphify` → `graph`。原名保留轉接。

### 11.3 VRN 管理器 26 個標準動詞 + 7 個後加動詞 → 契約

| 契約群 | 現有動詞 |
|---|---|
| A | help · version · verbs · health · status |
| B | launch · engines · engine-matrix · resources · extract |
| C | selftest · test · conform · parity · closeout · provenance |
| D | records · catalog · links |
| E | peers · page · monitor · synchronizer |
| F | backup · graphify · omniroute · mcp · install · bridges · tools · conflict · read · sync |

- **缺**:D 群的 `ssot` / `number` / `sdd`。11-21 裁定後 VRN 自己發號,要有自己的動詞。
- **缺**:`params`。現在讀 `VRN_ParamControl_SSOT`。

### 11.4 SUP(813 家族)
P2 時逐家族標主人,四選一:VCGC · VDF · VRN · 共用件。共用件只限鎖冊指定的那幾家(加速器 · 網路工具 · token · nlp · layout …)。標完才知道哪些該搬家、哪些是退役候選。

---

## 12 缺口(空的再補)

| # | 缺口 | 補在哪 | 階段 |
|---|---|---|---|
| 1 | `CGC_SystemManager` 沒有標準動詞 | VCGC SM 新版 | P3(第一批) |
| 2 | 三個系統都沒有契約檢查 `conform --contract` | G2 規則 + 各 SM 的 conform | P3 |
| 3 | via-vdf / via-vrn 經 VCGC 中樞轉交 | 各系統啟動器 + 短指令改道 | P3 / P5(動 .ps1 待授權) |
| 4 | VDF 缺 `verbs --json`;VRN 缺 `ssot` / `number` / `sdd` / `params` | 各 SM 新版 | P3 |
| 5 | SUP 813 家族沒有主人欄 | 對位冊(P2) | P2 |
| 6 | VRN 報告鏈治理件 33 家族在 VCGC | VRN R3 / R5 | P4 |
| 7 | 未登記程式 2438 支 | G3 registry-sync | P2 |
| 8 | 205 個舊 `via-*.cmd` | 改成印「已改名 → 新指令」的轉接(不刪) | P5(待授權) |
| 9 | VQG 沒有 SystemManager(只有 AllInOne);VAP 只有 v0100 | 套 §3 契約 | VCGC / VDF / VRN 之後 |
| 10 | 合併(fold)工具:`clones` / `baseline` / `sigdiff` 在已關閉的 #689 | G1 新版 | P4 前 |
| 11 | 字串釘死前版 11 處(delta) | 各家族新版改成 glob 取尾版 | P4 |
| 12 | 紅燈三家:DeckServer · ValidationSSOT · NumberGrant | 先判有沒有人用,再修或列退役 | P4 |

---

## 13 待操作員裁定(本稿新增)

| 編號 | 題目 | 裁定前怎麼做 |
|---|---|---|
| 9 | 附件提案「同一引擎最多留現行版 + 兩個備份(N-2)」對上「只增不減」「仍被引用的舊模組不搬走」 | 不刪,只標退役候選 |
| 10 | 短指令改道要動既有 `.ps1` / `.cmd`,不在 11-18 授權內 | 只出規格與演練,不改 |
| 11 | `VCGC_StartupEngine`(已在 main)要不要當 VCGC 的排程本體;它的 `mount` 契約要不要改成 §3 | 列候選,先不換 |
| 12 | 附件提到的「隔離區 main `4dae719`」與「私人新資料夾 VeritasIntelligenceAnalytics」不在本倉 | 未核,不動 |

---

## 14 給 AI 的一句話

先 VCGC 的動作,再系統自己的動詞,最後才自己寫;自己寫之前先回報缺口。本稿核准前,只做 P0 / P2(唯讀),不動任何程式。

---

## 15 附件「全景盤點與遷移評估」提示的核對(雲端能查的部分)

操作員 17:53 與 18:01 兩次附上同一份給 Claude 的提示(Phase 1 盤點 → Phase 2 報告 → 核准後 Phase 3 逐一遷移 · N-2)。雲端能查的照實核了,查不到的標「未核」。

| 提示裡寫的 | 核對結果(容器 · git) | 對本稿的意義 |
|---|---|---|
| 隔離區 `main` `4dae719` | 本倉沒有這個提交 → 是另一個倉;**未核** | 倉名與權限要操作員給 |
| `vcgc/startup-engine-v0100` `62e5d7c1`,`VCGC_StartupEngine_v0100.py` 85474 B,blob `0bb400b9` | `62e5d7c1` 上確實是 85474 B · `0bb400b9`。分支現在在 `bb95a35c`,比 main 領先 0、落後 6 → **已整條併進 main**。main 上的 v0100 是 110250 B,另有 v0101 薄尾 | 不用再遷;§4 排程候選用 main 版 |
| `grok/vdf-isolated-v0100` `f917003d` 與 `vdf/isolated-start-v0100` 同一版 | **同一提交** `f917003d`。比 main 領先 18、落後 610;22 檔 · +4442 行;PR #677 **已關閉、未合併** | 含 `VDF_MDL029_SystemManager` · `MDL030_LessonLedger` · `MDL031_IndependentSystem`。列為 VDF P3 / P4 的參考來源,逐檔對位,不整包併 |
| `grok/local-main-1493eb83`:本機 main 有 638 個遠端沒有的提交 | 這條分支比 main **領先 0**、落後 857 → 它的提交 main 全都有 | 沒有遺漏要追 |
| `grok/sp500-sector-074dbba` 與 `vdf/sp500-sector-active-v0100` 無共同祖先 | 不成立:`074dbba` 本身就是兩者的共同祖先,也已在 main 裡 | 沒有覆蓋衝突;桌機那條分支另有自動提交 `660bdf73` 誤收 VDF 檔,修正仍等操作員同意 |
| 本機舊倉 `…\Documents\movies-dataset` 與私人新資料夾 `…\Documents\VeritasIntelligenceAnalytics` | 本對話**沒有連到桌機** → **未核** | 照 CLAUDE.md「一個主工作倉」:先由操作員指定哪一份是主工作倉,其餘只標記 |
| VCGC / VDF / VRN 的虛擬環境與套件是否照規範裝齊 | 桌機狀態 → **未核** | 桌機跑一行 `via-health`(REQ258 ①),把黃紅精簡包貼回 |
| VCGC「安全接口 / 沙盒整合」 | 現有:安裝閘 · 重工守門 · 同意閘 fail-closed · 修補先複製到 TEMP · 全景守衛只改副本 | 列入 G5 / G6 / G7;缺的是 §12 #2 契約檢查與 #3 短指令改道 |
| Phase 3 一次一個引擎 + N-2 | 一次一個 = §9 P4「一家一 PR」;N-2 = 待裁定 9 | 核准前不刪、不搬 |
