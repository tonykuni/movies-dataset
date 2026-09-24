# 批732 · 表要自己加得起來 · 共識的上漲空間換成最新 ADJ CLOSE · 自測不再碰正式庫 · 2026-09-24

> 操作員 2026-09-24:貼回 via-vrnrun 全程(批731 交代要量的 Z188)+ 一張截圖——`C:\測試樣本報告\20251128兆豐訪談速報-神達(3706).pdf`
> 第 4 頁「財務報表 · 季度損益表」;跑到一半再傳一支 `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120_2.py`(沒有附話)。
> 常令:「所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE」「自測實測自AUDIT直到完工 結果也要實測正確性 請自動完成」。
> 一句話:截圖那張表是**真值**——拿它量,舊引擎只讀對一半;修好之後,表自己要加得起來(毛利 = 營收 − 成本、四季和 = 全年),加不起來就是讀錯。

## 一 · 工作站實錄(Z188:批731 修的有沒有到)

| 步 | 批731 貼回 | 批732 貼回 | 看法 |
|---|---|---|---|
| V1 冊重建 | 1 秒 | 1 秒 | — |
| V2 六層鏈 | 438 秒 · rc 2 | 500 秒 · rc 2(GREEN 32 · NODATA 15)| L3 `VRN_AutoTestLoop` **NODATA 180.1 秒**(撞節點上限;容器同一支約 52 秒)· ENG073 89.3 · MDL141 45.9 · ENG076 44.4 · ENG082 41.5 · ENG083 25.8 秒 |
| V3 庫價與上漲空間 | 19 秒 | 11 秒 | — |
| V6 實檔自測(106 份)| **1800 秒撞天花板被停** | **934 秒跑完 · rc 0** | AMBER:PASS 242 · WARN 9 · FAIL 0;**自測報告自己用 Edge 開了**(`[via-open] msedge.exe`)|
| └ G06 整批入庫 | 20 分 13 秒(一顆核心)| 11 分 15 秒(**2 個工作行程**)| 為什麼只有 2 個:見下 |
| └ G07 首頁逐檔 | 6 分 36 秒 | **1 分 38 秒** | 頁與附錄只解析一次 |
| └ G08 冪等 | 整批再入庫,第 17 份被砍 | **1 分 54 秒**(抽 12,首尾必在)| — |
| 合計 | 2268 秒 | 1456 秒 | Celeritas「模板已接」· PS 加速器 25/25 冊在位 |

- **2 個行程的由來**:加速器的執行緒預算在那台機器上算出來是 2(實體核心 × 記憶體壓力),平行池照它開——那是加速器的治理,池不越權改它。
  但主控台只印「2 個」,看不出為什麼。本批 `VRN_BatchPool v0101` 把來源印在同一行(容器實例):
  `[VRN] 平行池 3 個工作行程(20 份;…;來源 VIA_ACCEL_ACTIVE_THREADS=3(加速器執行緒預算:實體核心 × 記憶體壓力) · 本機 邏輯 4 · 實體 4 · 上限 6 · 份數÷2=10 → 3;要改:VRN_BATCH_WORKERS=N)`。
  想讓工作站多開:`$env:VRN_BATCH_WORKERS=4`(上限 6);記憶體吃緊時加速器給 2 是對的,不建議硬拉。
- **V2 的 L3 還是 NODATA**:自測門在工作站超過 180 秒(容器 52 秒)。本批自測門每跑完一個單元檔就印一行
  `· 12.3s 完成 test_VRN_XXX.py 8.1s · 11 支`,下次貼回就看得出時間花在哪一支(Z196)。
- **WARN 9 條**:7 份 PDF「no financial rows (no ruled table found)」(沒有框線的表,本引擎只讀有框線的——Z195)·
  1 張 .jpg 要 OCR · 1 份 MQ-1560 是掃描檔(G07 沒有文字層)。後兩條是已知的 OCR 缺口。

## 二 · 財報表格讀得對不對(截圖那一張當真值)

截圖第 4 頁的季度損益表(單位百萬元;7 列 × 6 欄,營業外收支那一列空白):

| 3706 神達 | 2024 | 25Q1 | 25Q2 | 25Q3 | 25Q4(F) | 2025(F) |
|---|---|---|---|---|---|---|
| 營業收入淨額 | 61,360 | 23,665 | 26,624 | 24,762 | 34,667 | 109,718 |
| 營業成本 | 53,991 | 20,886 | 23,770 | 21,476 | 30,472 | 96,604 |
| 營業毛利淨額 | 7,368 | 2,779 | 2,854 | 3,285 | 4,195 | 13,114 |
| 營業費用 | 5,585 | 1,540 | 1,602 | 1,614 | 2,080 | 6,835 |
| 營業淨利(損) | 1,784 | 1,240 | 1,253 | 1,672 | 2,115 | 6,279 |
| 利息收入 | 181 | 30 | 44 | 26 | 69 | 170 |

測試 `functional modules/VRN/tests/test_VRN_FinancialTable.py`(新,11 條)把這張表**照截圖的格子**畫進一份 5 頁 PDF 的第 4 頁,
走第二血統資料庫引擎的整批入庫路徑,逐格比對:

| 量 | 修前 | 修後 |
|---|---|---|
| 讀對的格 | **18 / 36** | **36 / 36** |
| 營業成本 · 營業費用 · 利息收入三列 | 不認得(同義字沒有)| 認得 |
| 「25Q1」這種季別 | 12 格**沒有年**(`Q1` 不知道是哪一年)| 2025-Q1 |
| 「25Q4(F)」「2025(F)」預估欄 | 0 / 12 標成預估 | 12 / 12 |
| 恆等式(毛利 = 營收 − 成本 · 營業利益 = 毛利 − 費用 · 四季和 = 全年)| 無此檢 | **18 / 18 成立** |

改了什麼:

| 件 | 修什麼 |
|---|---|
| 證據核心(`VRN_Evidence_Core.py`)| **期別的門**:`period_parts()` 委派母線 `VRN_ENG074_FinancialPages` 尾版(尾版律 glob)解「25Q1」「25Q4(F)」「2025(F)」「113年」;裸 3 碼年(「113」)不收,免得跟數字撞 |
| 資料庫引擎 v0105(`VRN_Integrated_ReportDatabase_Engine.py`)| 同義字只增不減:`COGS`(營業成本 · 銷貨成本 …)· `COGSRatio` · `OperatingExpense`(營業費用 …)· `OperatingExpenseRatio` · `NonOperatingIncome`(營業外收支 · 業外損益 …)· `InterestIncome`;期別先問證據核心的門、預估字樣標 Estimate;**`financial_identity_checks()`**:容許 = 每一項印出來的最後一位的一半,錯的那一條點名印出來(`毛利 = 營收 − 營業成本 · 2025-Q1 · 表 T3:印 2,779 · 算 2,779(差 0,容許 1.5)`)|
| 首頁引擎第二血統 v0105 | 表頭期別同一個門 |
| **母線首頁引擎 v0129**(新;v0127 留)| `parse_period` 認「2025(F)」「25Q4(E)」「Q3A」這種尾巴;+㊷ 九例;41 / 41(㊳ 無料 NODATA 同 v0127)。**原擬 v0128**——commit 前 LL334 全分支掃描,側線 `claude/upbeat-feynman-1uurww`(批708,還沒併 main)今天已用 v0128(刪一個被蓋掉的死碼 `_esc`,行為零變更)→ 改號 v0129,並把它那 4 行一併帶上:兩條線誰先併進 main,尾版都同時有兩邊的修改(v0129 對它的 v0128 只差本批這一段)|
| 自測迴圈 | G06 每份報告跑恆等式:不成立 → WARN 點名;季別缺年 → WARN;主控台一行 `[財報]`;報告頁多一節「財報表格讀得對不對(批732:表要自己加得起來)」|

同義字**跟母線財務字庫同一個意思,不打架**(`via-finlex --ask` 實查):營業成本 / 銷貨成本 → cogs 一族(cost_of_sales · operating_cost 同一件事)·
營業費用 → operating_expense · 營業外收支 / 業外損益 → non_operating_income · 利息收入 → interest_income。
只有三個比率詞(營業成本率 · 營業費用率 · 費用率)母線冊上還沒有 → 候選(Z197,不代寫冊)。

容器合成 20 份一輪:`[財報] 表格抽到 17/20 份 PDF · 恆等式 0/0 成立(0 份有可驗的表)· 不成立 0 條 · 季別缺年 0 列 · 預估欄 136 列`
——合成表沒有成本列,所以沒有可驗的恆等式;**真的考驗是截圖那張(18/18)與工作站那 105 份**,下次貼回 `[財報]` 那一行。

## 三 · 共識線:上漲空間換成最新 ADJ CLOSE(Z157)

**上傳的整合引擎**:跟樹上四份收件**逐位元相同**(`functional modules/VRN/references/intake/` · `VDF/…/VETF_FINAL_SEAL_b242/…/Legacy_Consensus_Engines/` ·
`supportive modules/…/VIA_GrokConsole_AuroraAcorn_b383/attachments/`;`VRN_SSOT_Books_b561/` 那份只差 CRLF)——沒有新東西要收,收件夾原件不動。
它的 `target_*_upside_vs_adj_close_pct = 目標 ÷ yfinance 最新 adjClose − 1`:共識日就是最新交易日時,跟本批的算法同一個數;
共識日較舊、或是券商報告時,本批多乘基準日因子(那段時間配的息不再被算成上漲空間)。

| 件 | 修什麼 |
|---|---|
| **VRN_ENG069_ConsensusDB v0106**(新;v0105 留)| 每一列委派 ENG073 尾版 `adj_quote`(L99 的唯一算法;LL404 不長第二顆頭):**目標中位數 × 基準日因子 ÷ 最新 adj close − 1**,因子分母走交易所收盤。基準日:共識快照 = **共識日那一列**(傳共識日 + 1 天,`adj_quote` 取「前一交易日」)· 券商報告 = 報告日前一交易日(L99 原意)。**舊表一欄不加**——ENG070 / ENG071 用 14 個位置的 `INSERT … VALUES` 寫 `consensus_daily`,加欄等於弄壞別人的寫入;結果落**旁表 `consensus_adj`**,另開視圖 **`consensus_latest_adj`**。別支事後改寫了目標 → `ADJ_STALE` 不給數;新列還沒算 → `ADJ_NOT_RUN`。單位跟 ENG073 一樣:`upside_adj` 是百分比。新段不拖垮舊段:一列算壞 → 那一列 `ADJ_ERROR(例外名)`、其餘照算;ADJ 整段壞 → 舊欄照建、因由印在 `[共識庫]` 那一行(兩條都用假引擎實打過)|
| **VRN_ENG079_ControlTowerDashboard v0101**(新)| 控制塔的直方圖與明細前 30 改讀 `upside_adj`;視圖不在 → 退回舊欄並**在頁上寫明「原始價舊欄」**,不讓舊數字頂著 ADJ 的名字出現;+⑦ |

量(容器正式庫,198 列):

| | 舊欄 `upside_pct` | 新 `upside_adj` |
|---|---|---|
| 有數字的列 | 3(全是 CNYES 自帶 close;舊 join 只認 `.TW`,EXTERNAL 195 列全 NULL)| **20**(ADJ_OK)|
| 算不出的 | 195 列 NULL,不說為什麼 | ADJ_NO_FACTOR 124(容器價表只有 893 檔,每列帶 `adj_block_reason`)· ADJ_NO_TARGET 54 |
| 控制塔頁上有數的檔 | 0 / 195(去重挑分析師多的那一列,那列沒有 close)| 20 / 195 |
| build 時間 | — | 4.5 秒(含 198 列 ADJ)|

夾具(手算,不問 ENG073):9901 共識日 09-08、09-10 除息 3 元 → **舊式 34.0%、ADJ 30.0%**——多算的就是那 3 元股息。

還沒換的讀者:VDF `ENG068 ETFConsensusAnalysis` / `ENG069 RevenueConsensusAnalysis` 自己拿 `target ÷ close` 算上漲空間,VAP `ENG014` 儀表板讀它們——
那是 VDF / VAP 線,Z157 留開,寫清楚下一步(改讀 `consensus_latest_adj.upside_adj`)。

## 四 · 自測不再碰正式庫(Z189 第一支)

v0105 的自測兩次 `build()` 都寫**正式庫**、拿寫鎖,平行格子撞別站的讀鎖就紅(批731 v0480 實錄)。v0106:

- ②–⑩ 全在暫存庫:四檔 + 一份券商報告(除息 · 上櫃尾碼 · 沒價 · 沒目標 · 報告日 = 除息日),答案寫在夾具說明裡一行一行手算;
- ⑪⑫ 正式庫**只開唯讀**:外部源覆蓋(原②的 ≥190 檔)· ADJ 試算 vs 獨立 SQL(基準日 · 最新 adj · 目標 × 因子 · 百分比四項);
  正式庫被別的行程寫鎖中 → 誠實 SKIP(Z189 其餘各支還沒改);
- ⑬ 最後量:本支開過的每一條連線都記下來,正式庫**一次都沒被可寫地打開過**(容器:9 條,暫存 8 · 正式庫 1 條唯讀;正式庫 193,212,416 位元組、mtime 前後一致)。

**這個尺當場抓到一個真錯**:第一版 ⑫ 紅——9 列 ADJ_OK 的數字全對,但 `target_median_adj` 是空的
(ENG073 的欄名是 `target_price_adj`,旁表叫 `target_median_adj`,對不上就靜靜地存成 NULL)。修了對照表,⑨ 也加驗這一欄。

變異測試(每一種改錯,自測都要紅;四種全紅):

| 改錯 | 誰紅 |
|---|---|
| 共識快照不加 1 天(用共識日前一交易日)| ⑨:9902 變 10.0%(因子 0.98 @ 09-08)|
| 券商報告也加 1 天 | ⑨:9901 券商變 28.9%(因子 1.0 @ 09-10)|
| 正式庫那條連線改成可寫 | ⑬ 點名那條連線 |
| 視圖拿掉 ADJ_STALE 守衛 | ⑩:目標改寫後仍給 30.0% |

## 五 · 驗證

| 項 | 結果 |
|---|---|
| 截圖真值表(`test_VRN_FinancialTable` 11 條)| 36 / 36 格 · 恆等式 18 / 18 · 預估欄 12 · 季別缺年 0;錯位的成本列會被點名 |
| VRN/tests | **118 / 118**(71 秒)|
| ENG069 v0106 自測 | **13 / 13**(3.4 秒)· 正式庫 193,212,416 位元組與 mtime 前後一致 · 變異四種全紅 · 平行格子裡照綠 |
| ENG079 v0101 自測 | **7 / 7** |
| 母線首頁引擎 v0129 | 41 OK · ㊳ NODATA(容器沒有 sidecar,同 v0127)|
| 自測迴圈 合成 20 份一輪 | GREEN 99 / 0 / 0 · `[財報]` 一行 · 平行池那一行帶來源 |
| VCGC · 契約 | 37 / 37 · 19 / 19 · registry-sync APPLIED(新 8 · 變更 194)|
| 全格子 v0481 第一跑 | OK 347 · FAIL 1 · SKIP 7 · 931 秒(`GRID_20260924_153227.json`)|
| 全格子 v0481 第二跑(改號 v0129 與兩處具名之後;把 `/opt/pwsh` 放上 PATH,PS 語法閘真跑)| **OK 348 · FAIL 1 · SKIP 6** · 960 秒(`GRID_20260924_155243.json`)|
| 唯一的紅 | CGC_MDL157「engine numbers are unique per family」:新撞號 CGC_MDL135(**Z190**,main PR #105 帶進來,等你裁定;本批沒碰)|
| 稽核(CGC_MDL158 全景代讀)| ENG069 v0106 · ENG079 v0101 **0 件**(前版各有一處吞例外,本批改成具名:讀不了的券商 JSON 列名印出 · 控制塔頁寫出讀不到的原因);首頁 v0129 9 件 = v0127 既有的 9 處吞例外(DUPDEF 1 件隨側線那一刀消失),本批 0 件新增 |
| 共識庫 build(容器正式庫)| 198 列 · ADJ_OK 20 · 4.5 秒 |
| 再生物還原閘 CGC_MDL167 | 還原 40 支再生頁(先備份);留下刻意入倉的 4 本(元件冊 · regex 清冊 · VRN 邏輯架構冊 · 總控頁)|

**併 main(兩次)**:收尾時 main 前進兩次——先是 `16e6081f`(PR #110 側線 busy-bell:去重寫入收正典 · 同意閘 · 格子 v0482–v0486),
併完驗完要推之前又前進到 `ca9ed7de`(PR #111 同一條側線第十段:去重寫入全族收正典 · 格子 v0487 · 掉球 Z194)。照規矩每次都先 commit 再 merge(不 rebase):

- 掉球表取聯集依號排:側線的 Z183–Z187 · Z191–Z194 原樣;本批 Z188 結 · Z189 進度;**本批新列原擬 Z194–Z197,PR #111 先用了 Z194 → 改號 Z195–Z198**(文內引用一併改)
- 元件冊與 regex 清冊:每次都取 main 版,再由建冊器重建(registry-sync / CGC_MDL115),兩邊的新元件一起編號
- 格子:本批的站名改名原擬 v0487(第一次併完時全分支沒有 v0487),PR #111 先把 v0487 用掉 → **改號 v0488 = 它的 v0487 + 本批一行改名**
- 併完在格子 v0488 上再跑一次全格子:

| 併 main 之後 | 結果 |
|---|---|
| 第一次併(PR #110)· 格子 v0487(本批當時的改名版)| OK 348 · FAIL 1 · SKIP 6 · 935 秒(`GRID_20260924_161751.json`)|
| **第二次併(PR #111)· 格子 v0488** · registry-sync · 邏輯冊 · regex 清冊 · 總控頁 · 契約 19 / 19 · VCGC 37 / 37 | **OK 348 · FAIL 1 · SKIP 6** · 935 秒(`GRID_20260924_163856.json`);站名「驗證共識庫十三檢」OK;唯一的紅仍是 CGC_MDL157 的 MDL135 撞號(Z190)|

## 六 · 掉球

| 號 | 變化 |
|---|---|
| Z157 | ENG069 段 + VRN 控制塔 ENG079 **做完**;VDF ENG068 / ENG069 → VAP ENG014 還在算自己的 `target ÷ close` → 留開 |
| Z188 | **結**:工作站實量——V6 934 秒跑完(天花板以內)· 自測報告自動開 Edge · Celeritas 模板已接 · G07 98 秒 · G08 114 秒;剩的兩條拆成 Z196 與本文第一節 |
| Z189 | ENG069 v0106 做完(第一支);其餘約 23 支自測可寫連線照舊逐支改 |
| **Z195**(新)| 沒有框線的財報表不讀:工作站 105 份裡 7 份「no ruled table found」 |
| **Z196**(新)| 工作站 V2 的 L3 自測門 180.1 秒 NODATA:看每單元一行找最慢那支 |
| **Z197**(新)| 母線財務字庫缺三個比率詞(營業成本率 · 營業費用率 · 費用率)|
| **Z198**(新 · 同批結)| 格子站名「驗證共識庫八檢」→ 十三檢:側線 busy-bell 在本批收尾時連併兩次(PR #110 · #111,格子到 v0487),本批改名落在**格子 v0488**(只換數字;LL334 掃過全分支沒有 v0488)|

## 七 · 工作站(一貼即用)

同批731 那一段,只換成認批732 的檔(`VRN_ENG069_ConsensusDB_v0106.py`)、分支叫 `b732-時間`;`via-vrnrun` 跑完再多兩步:
共識庫 build 一次(日更鏈 ⑦b 本來就會跑;這次先跑,當場看 ADJ 算得出幾列)、自測門單獨跑一次(V2 只顯示每個節點最後兩行,每單元的秒數要單獨跑才看得到)。
跑手還是 v0104(本批沒有改任何 .ps1)。

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
$top = git rev-parse --show-toplevel
"  [前] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
git reflog -3 --format="  [前] %h %gs"
if (git rev-parse -q --verify MERGE_HEAD) { "  [前] 卡在合併:" + (git log --oneline -1 MERGE_HEAD) + " → merge --abort"; git merge --abort }
$held = @()
foreach ($p in @(git -C $top diff --name-only --diff-filter=U)) { if ($p -match '(ui_support/.+\.html|registry/VIA_(VRN_LogicArchitecture_SSOT|Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict|Schema_Registry|Unified_Register|ParallelLanes|ProjectCompletion|ProductGate|Component_Inventory_SSOT)_v\d+\.json)$') { git -C $top checkout HEAD -- $p; "  [解卡] 再生冊取提交版:" + $p } else { $held += $p } }
if ($held.Count -eq 0) {
    git reset -q
    via-regen --apply
    if (git status --porcelain --untracked-files=no) { git stash push -m "workstation-local-before-b732" }
    git stash list | Select-Object -First 3
    git fetch https://github.com/tonykuni/movies-dataset main
    git merge-base --is-ancestor main FETCH_HEAD 2>$null; $ff = ($LASTEXITCODE -eq 0)
    if (-not (git rev-parse -q --verify refs/heads/main)) { git switch -c main FETCH_HEAD } elseif ($ff) { git switch main; git merge --ff-only FETCH_HEAD } else { git switch -c ("main-latest-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    if (-not (Test-Path ".\functional modules\VRN\VRN_ENG069_ConsensusDB_v0106.py")) {
        "  [拉取] main 還沒併批732 → 改拉批732 的分支(它 = main + 批732,本機另開 b732-時間,不動 main)"
        git fetch https://github.com/tonykuni/movies-dataset claude/awesome-bardeen-h0wm5v
        if ($LASTEXITCODE -eq 0) { git switch -c ("b732-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    }
} else { "  [解卡] 人寫件卡在衝突,不自動處理,先停:" + ($held -join " · ") }
if ($held.Count -eq 0 -and $LASTEXITCODE -eq 0 -and (Test-Path .\Invoke-VIA-VRN-v0104.ps1) -and (Test-Path ".\functional modules\VRN\VRN_ENG069_ConsensusDB_v0106.py")) {
    "  [後] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
    $log = "$env:TEMP\vrnrun_b732.txt"
    via-vrnrun 2>&1 | Tee-Object -FilePath $log
    Invoke-VIAPython -Family vrn ".\functional modules\VRN\VRN_ENG069_ConsensusDB_v0106.py" build 2>&1 | Tee-Object -FilePath $log -Append
    Invoke-VIAPython -Family vrn ".\functional modules\VRN\engine\VRN_AutoTestLoop.py" --selftest 2>&1 | Tee-Object -FilePath $log -Append
    Select-String -Path $log -Pattern '\[Celeritas\]|\[加速器\]|平行池|\[進度\] \d+/6|\[V[1-6]\]|\[進度\] \d+/\d+ L3|\[ROUND|\[DONE\]|\[附錄\]|\[ADJ\]|\[財報\]|財報恆等式|季別缺年|FAIL G|WARN G|\[共識庫\]|完成 test_|\[計\]|rc=|總計|via-open' | ForEach-Object { $_.Line }
} else { Write-Host "  [拉取] main 跟批732 分支都沒拉到(上面幾行就是原因),先停" -ForegroundColor Red; git status --short | Select-Object -First 15 }
```

## 八 · 要貼回什麼

1. V6 的 `[財報]` 那一行 + G06 的 `財報恆等式 … 不過` WARN(有的話整條貼)——**哪一份、哪一條、印多少、算多少**;
2. V6 的 `[VRN] 平行池 …` 那一行(看來源是不是 `VIA_ACCEL_ACTIVE_THREADS=2`);
3. V2 L3 自測門那一段每單元的 `· …s 完成 test_…py …s` 各行(Z196);
4. `python "functional modules/VRN/VRN_ENG069_ConsensusDB_v0106.py" build` 的兩行 `[共識庫]`(工作站的價表齊,ADJ 算得出幾列)。
