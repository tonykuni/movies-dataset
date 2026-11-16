# 交接 · 2026-11-16 · 併 main + 改發號 + CLAUDE.md 補強

## 做了什麼
1. **併 main**:`origin/main`(667a86086,PR #634–#653)併進 `claude/optimistic-goodall-yhalc5`。兩線自 2026-11-10(9ed1bb138)分開:
   分支領先 218 提交、main 領先 114 提交,53 個檔同名不同內容(含同版號的管理器、引擎、需求冊、工作流冊與編號冊)。
   依版號律(main 上已發布的檔不改)**53 檔全部取 main 的內容**;分支的內容留在歷史 c3cfa40ea,逐檔清單在
   `VIA_MergeMain_20261116_Conflicts.json`。併後 247 個 json / jsonl / py 全部可解析 / 可編譯。
2. **撞號改發**(分支上的檔沒進過 main,所以改名 / 改版不違反版號律):
   | 原(分支) | 撞到 main 的 | 改發 | VCGC 編號 |
   |---|---|---|---|
   | `VDF_SystemManager_v0176`(datamatrix) | main 的 v0176(內容不同) | `VDF_SystemManager_v0184` = main v0183 + datamatrix | VIA-VDF-MDL284 |
   | `VDF_MDL017_SafeParallelLaunch` | `VDF_MDL017_UserApiKeys` | `VDF_MDL022_SafeParallelLaunch_v0100` | VIA-VDF-MDL285 |
   | `VDF_ENG240_DataScopeMatrix_v0100` | 編號冊取 main 後原號作廢 | 檔名不變 | VIA-VDF-ENG368 |
   | `VRN_MDL260_SafeParallelLaunch_v0100` | 同上 | 檔名不變 | VIA-VRN-MDL347 |
3. **CLAUDE.md**:保留 L128 / L129 表頭(政策冊尾版 v0124),加入操作員 2026-11-16 逐題定案(照上傳檔原文)、
   十二條補強(來源 `VIA_RecurringIssues_PolicyReview_20261116.md`)、每天開機更新指令。

## 驗證(容器)
- `VDF_SystemManager_v0184 --selftest` 7/7(內含 main v0183 全套;main 的 R2 檢在併入後會掃到分支線薄尾 v0172 → v0184 具名豁免並印理由;main 的 v0183 自己在併後樹上這一項是紅,檔不改)。
- `VDF_MDL022` · `VRN_MDL260` 自測各 14/14;併後實跑兩支 YELLOW(同意閘未開 · 矩陣 / 收尾 / 衝突 / 安裝計畫黃)。
- 橋覆蓋:VDF 加速器 109/109 · 網路 11/11;VRN 加速器 84/85(唯讀豁免 1 · 缺 0)。
- 編號稽核:基準 667a86086 · 遺失 0 · 改身分 0 · 重號 0 · IMMUT 0 · 撞號 0。
- 總經交叉比對(`VDF_MDL016` 最新三期,2026-11-09 已有):容器 12 對全 NODATA(沒有 VAKE 庫與官方庫),要在桌機跑。

## 還沒做 / 做不到的(照實)
- **桌機連不到**:這個雲端工作階段沒有任何桌機資料夾可用,`C:\測試樣本報告` 的 VRN 個股 / 非個股實測、VDF 2022-01-01 起實抓、
  輸出驗證、操作員用滑鼠走 U/I,都要在桌機跑(指令見下)。容器沒有 pwsh,`.ps1` 沒有實跑過。
- **每天開機更新器**(`via_boot_update.ps1` / `.sh`)會自己開同意閘、自補套件 → AI 不代跑。
- 分支上被 main 蓋過的 53 檔裡,分支獨有的需求 / 工作流列(需求冊 v0249–v0252、工作流冊 VCGC v0147 / v0148 · VDF v0109 · VRN v0110)
  沒有併回 main 的冊:要逐列比對後另出新版號冊(待辦,不能消失)。
- 併後 `handoff check`、SDD(X-COL VRN-WKF010 欄位不齊 · 註冊冊不是尾版若干)沒有清;`VIA_Handover_20261116_Night_Closeout.md` 不在本倉也不在 main。
- 模擬桌機工作樹時把容器磁碟用滿一次(已清;冊檔事後逐本驗過可解析),當時那一輪 `test --quick` 因此中斷,之後重跑。
- **併後 `test --quick` = RED(站 13:綠 8 · 黃 2 · 紅 3)**。交接案已對上(交接冊補回分支獨有 46 案 + 24 工作項 · 盤點冊 v0244 登 main 新增 22 案 → case 345/345 · 新 0 · 缺 0)。三站紅都是「改過的尾版自動自測」,根因是兩線的版號冊還沒對帳:
  | 紅站 | 訊息 | 根因 |
  |---|---|---|
  | `CGC_MDL237_NumberingSystem_v0121` | `ValueError: CANDIDATE_LIMIT` | 分支線的檔(政策冊 v0118–v0124 等)在 main 的編號冊裡沒有號,待編號候選超過上限;大批發號(數千列)要操作員點頭再做 |
  | `CGC_MDL246_ValidationSSOT_v0102` | V-XREF:工作流冊引用了驗證冊沒登記的交叉代碼(例 C-daily-backup · VCGC-WKF036) | 工作流冊尾版是分支線的、驗證冊是 main 的 |
  | `CGC_MDL261_UIEngine_v0108` | 前版 v0107 自測 8/9 | 前版鏈用的冊代與併後尾版不同代 |
  黃 2:`handoff check` rc 1(交接閘原本就紅)· 容器沒有 pwsh。

## 桌機指令(PowerShell 7;一段一段貼)
```powershell
# ① 同步到這條分支(已含 main)。用 VDF 工作樹(不在 OneDrive);沒有就用主 checkout
$W = "$env:LOCALAPPDATA\VIA\movies-dataset-vdf-main"; if (-not (Test-Path $W)) { $W = "$env:USERPROFILE\OneDrive\Documents\movies-dataset" }
git -C $W fetch origin claude/optimistic-goodall-yhalc5; git -C $W checkout --detach FETCH_HEAD; Set-Location $W
# ② 每天開機更新(它自己開同意閘 · 每日首跑才實跑)
pwsh -NoProfile -ExecutionPolicy Bypass -File "VeritasIntelligenceAnalytics\supportive modules\registry\via_boot_update.ps1"
# ③ VDF(v0101):先降壓 → 資料家 = 文件夾下 VeritasIntelligenceAnalytics\via_database(自動找;也可 --data-home 指定)→ 3~5 支同時 →
#    橋閘 100% 才增量擷取(ActivateVDF)→ parquet 同步 · 範圍矩陣 · 總經三期 · 收尾頁(要真的出網,先自己設兩道同意閘)
py "VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL022_SafeParallelLaunch_v0101.py" run
# ④ VRN(v0101):先降壓 → 3~5 支同時 → 用測試樣本夾跑個股 + 非個股整輪 → 輸出矩陣 → 收尾頁
py "VeritasIntelligenceAnalytics\functional modules\VRN\VRN_MDL260_SafeParallelLaunch_v0101.py" run --roundall-args "--source C:\測試樣本報告"
# ⑤ 總經:官方 × AKShare 最新三期
py "VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL016_MacroCrossCheck_v0102.py" run
```
`git checkout --detach` 遇到未提交改動會自己中止、不覆蓋;中止時把訊息貼回。

## 2026-11-16 補記:桌機回報「卡斷且好慢」→ 啟動器 v0101
- 根因(查程式):v0100 的擷取步直接叫 ENG239 → FetchGroups,用倉內預設擷取夾(空的)→ 等於從 2022 整個重抓;也沒走 VDF 正式入口 ActivateVDF
  (記憶體准入閘 · 工具載入防遞迴 · 照 VDF_DataHome_SSOT 找資料家)。
- v0101:① 第一步降壓並等系統靜下來 ② 資料家用操作員指定的 via_database(底下有 vdf_database 就用它),只讀清點,子行程帶 VIA_VDF_DB_HOME
  ③ 道數夾 3~5;橋閘 / 不重複擷取計畫 / 清單閘 / OmniRoute 四支同時起,橋閘 100% 才擷取 ④ 心跳印每支靜了幾秒與子行程數。
- 容器驗證:自測 VDF 23/23 · VRN 21/21;用模擬資料家從別的資料夾實跑,順序正確、ActivateVDF 收到 --db-home。容器的紅是環境(同意閘沒開 · 沒裝 yfinance · 假資料家只有一本庫)。
- 沒驗到的:桌機真資料家的實際內容與速度;`.ps1` 與 Windows 行為。跑完請把最後 30 行或 `VIA_Reports\vdf\launch\VDF_Launch_latest.json` 貼回。
