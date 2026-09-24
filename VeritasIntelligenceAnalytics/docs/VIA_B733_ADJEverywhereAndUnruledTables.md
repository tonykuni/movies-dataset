# 批733 · 共識上漲空間全線換 ADJ · 沒有框線的表也讀、讀了要加得起來 · 自測真的不碰正式庫 · 2026-09-24

> 操作員 2026-09-24(批732 以 PR #112 併進 main 之後):「開pr及繼續完成全部 實測自修正值到完成」。
> 常令:「所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE」「自測實測自AUDIT直到完工 結果也要實測正確性」。
> PR #112 已由你開、併(16:56),Codex 程式與安全審查都跑完、零建議;本批照規矩從新的 main 重起分支(同名),另開新 PR。

## 一 · 共識上漲空間:全線換成最新 ADJ CLOSE(Z157 結)

批732 把 ADJ 上漲空間落進共識庫(VRN_ENG069 v0106 的旁表 + 視圖 `consensus_latest_adj`)、控制塔先換。本批把**其餘每一個讀共識上漲空間的地方**都換掉——
全樹逐支查過 `upside_pct` 的讀者(尾版),共識線就這些:

| 件 | 從前 | 本批 |
|---|---|---|
| VDF_ENG068 v0106 主動 ETF×共識 | `consensus_latest.upside_pct × 100`(原始價)| 讀 `consensus_latest_adj.upside_adj`;視圖不在 → 退回舊欄、頁上寫「原始價舊欄」;+⑦ |
| VDF_ENG069 v0109 月營收×共識 | 同上 | `q_join(adj)`:同一條 SQL 只換兩處(來源視圖、上漲空間欄),換不到就當場炸不靜靜退回;+⑧ 合成庫證 ADJ 車道 · ⑨ 頁上基準 |
| VAP_ENG014 v0103 標準儀表板 | 數字照吃上面兩支 | 兩張卡的標題寫出基準(字取自引擎的 `UPSIDE_BASIS`,一處定義);+⑦ |
| CGC_MDL095 DeckServer v0160 `/stock_data` | 共識列 c[8] = 原始價上漲空間 | 只增不減:每列尾端加 c[9] = ADJ(÷100,跟 c[8] 同單位)· c[10] = ADJ 狀態(判定走 ENG069 的視圖,STALE / NOT_RUN 一處算);+㉖ 暫存庫夾具 |
| CGC_MDL094 CommandDeck v0101 個股卡 | 「upside」欄 = c[8] | 「upside(最新 ADJ)」= c[9];算不出給狀態;舊橋沒有 c[9] → 顯示 c[8] 並標「原始價」;+⑩ |

量(容器):

- ETF×共識:22 檔 ETF 都有加權上漲空間(v0105 也是 22);**平均覆蓋權重 7.0% → 5.8%**——舊版的覆蓋來自 2454、2317 兩檔,
  它們的原始價是鉅亨自帶的 close;容器的價表**沒有一檔上市(.TW)股票**,ADJ 算不出、狀態寫「上市所整個不在 ADJ 表」。
  工作站價表齊,這兩檔會回來、而且是 ADJ。
- 月營收×共識:容器沒有月營收表(誠實缺料模式 4/4);另在合成庫上跑全檢 9/9:2330 取 ADJ 17.5(不是舊欄 20.0)、
  6173 取 33.2、2317 沒有 ADJ 就不入四象限。
- 指揮台:`upA()` 三種情形實跑——ADJ 30.0% · 「— ADJ_NO_FACTOR」(滑過看完整原因)· 舊橋「25.0%(原始價)」;整頁 JS 語法檢查過。
  指揮台頁是再生物:工作站跑一次 `regen-all` 就換新頁。

## 二 · 沒有框線的財報表(Z195)

工作站那 105 份裡 7 份報「no financial rows (no ruled table found)」。本引擎在有框線的表讀不到 EPS 時,本來就會退回「欄對齊」讀法
(證據核心 `column_tables`),但只看前 4 頁、而且表頭只認得 `2024A` `12/25E` `1Q25` 這幾種寫法。拿你那張截圖的表、**拿掉框線**、
放到 8 頁報告的第 6 頁實量:

| | 修前 | 修後 |
|---|---|---|
| 讀對的格 | **0 / 36**(表頭只認得 `2024`、`2025(F)` 兩欄 → 標籤邊界算到頁外,整張表一列都不收)| **36 / 36** |
| 恆等式 | — | **18 / 18** · 預估欄 12 · 季別缺年 0 |

改了什麼:

| 件 | 修什麼 |
|---|---|
| 證據核心 期別字樣(只增不減)| 年在前的季與半年(`25Q1` `2025Q1` `25Q4(F)` `25Q4F` `25H1` `1H25`)· 帶「年」的年(`2024年` `2025年(F)`)· `1Q25(F)`;反例 `25Q5` `25H3` `61,360` 不收 |
| 證據核心 表頭沒認全的防線 `_unnamed_columns` | 底下數字排出來的欄比表頭認得的期別多 = 有欄的表頭沒認出來 → **這張表不讀**。橫式寬頁實測:拿掉這道防線,25Q3 的營收會被歸到 `2025(F)` 底下,**而且恆等式照樣成立**(每一列錯得一樣)——所以不能只靠恆等式 |
| 證據核心 後段頁 `pdf_column_tables_later` | 有框線的表和前 4 頁都讀不到損益表時,往後讀到第 40 頁,但**只讀字面上像損益表的頁**(營業收入 / 毛利 / 每股盈餘 / Revenue / EPS …),長報告(初次評等)的財報在後段 |
| 證據核心 期別的門 | `2025年(F)` ENG074 讀不出 → 拿掉「年」再問一次(預估旗標才不會掉)|
| 資料庫引擎 v0106 `gate_fallback_tables` | **沒有框線讀出來的表要加得起來才入庫**;加不起來 → 不入庫,在那一份報告的 ValidationIssues 寫 `FIN_TABLE_REJECTED(表 · 哪一條 · 印多少 · 算多少)`;沒有可驗的(例:只有 EPS)照收;有框線的表不變(照批732 只警告)|
| 資料庫引擎 v0106 `drop_reread_tables` | 本批實測抓到:截圖那張**有框線**的表沒有 EPS 列,欄對齊讀法也在同一頁跑,表頭認得季之後**把同一張表又讀一次**(72 列 = 36 格 × 2)。欄對齊讀出來的表,數字有六成以上跟同頁的框線表一樣 = 同一張表,不收。(`2024A 2025F` 這種表頭以前就會重讀,一併修)|
| 自測迴圈 G06 | 被擋下的表 WARN 點名:`unruled financial table left out (does not add up): …` |

測試 `test_VRN_FinancialTable.py` 11 → **17** 條:第 6 頁無框線表逐格對 · 表頭沒認全不猜(有 / 沒有防線各跑一次)·
加不起來的表不入庫且點名(走整批入庫路徑)· 只有 EPS 的表照收 · 框線表不讀兩次 · 新表頭字樣逐一。
合成 20 份一輪:GREEN 99 / 0 / 0,`[財報]` 那一行跟批732 一字不差(17/20 · 預估欄 136)——沒有回歸、沒有重讀。

## 三 · 自測真的不碰正式庫(Z189 結)

批731 估「約 23 支自測可能開可寫連線」是字面掃的。本批改成**量**:每一支自測跑前跑後,三本正式庫(台股 · 全球 · 主動 ETF)的位元組與 mtime 各記一次。

| | 結果 |
|---|---|
| VDF_ENG061 v0104 因子庫 | **寫了正式庫**:自測呼叫 build(),在正式台股庫與全球庫上 CREATE OR REPLACE `features_daily`(台股庫 193,212,416 → 160,182,272 位元組;對照組再跑一次 → 162,803,712)|
| VDF_ENG062 v0103 族群因子層 | **寫了正式庫**:`group_features_daily`(→ 158,609,408)|
| 其餘 VDF 自測(ENG050 052 055 056 058 060 063 066 068 069 070 071 073 082)· CGC_MDL092 098 119 123 | 前後一致(自測本來就把庫指到暫存、或只讀)|
| **VDF_ENG061 v0105 · VDF_ENG062 v0104** | 輸入表**唯讀**複製進暫存庫(ATTACH … READ_ONLY),build() 寫暫存庫,①–⑨ / ①–⑧ 判準一字不動(同一份真資料);+⑩ / +⑨ build() 那一刻庫指向暫存夾;正式庫被鎖 → 誠實 NODATA(格子本站 nodata_ok)。**前後一致**,7 秒 / 1 秒 |
| 全格子前後三本正式庫 | **全格子(v0488,355 站,686 秒)跑前跑後三本正式庫位元組與 mtime 一個都沒變**(台股 158,609,408 · 全球 15,478,784 · 主動 ETF 3,420,160) |

AST 複核:尾版自測裡剩下的 14 個可寫連線,全都先把庫路徑換成暫存夾才連(ENG057 064 075 076 077 078 · CGC_MDL123)。

## 四 · 財務字庫的三個比率詞(Z197)——要你定

- 母線財務字庫(`vrn_finlex` 收割冊)沒有 營業成本率 · 營業費用率 · 費用率。
- 母線正典 regex 庫 `InvestmentRegexPattern_VALIDATED.py` 的 `cost_of_sales` 式**不錨定**,「營業成本率」這個比率詞會被它當成營業成本(金額)命中
  ——跟批732 第二血統防的是同一種錯(百分比變金額)。目前只有字庫收割器用這個庫,沒有引擎拿它分列。
- 母線財報頁引擎 ENG074 用的是 `VRN_Financial_Synonyms_SSOT`,它自己寫明:營業成本 / 營業費用**不在**這本冊上(缺運算元 = 恆等式驗不了),
  而且「要不要登錄 = 操作員定」。所以本批**不代登**。
- 提議(你點頭我就做,只增不減):① `VRN_Financial_Synonyms_SSOT` 登錄 COGS(營業成本 · 銷貨成本 · Cost of Revenue / Sales / Goods Sold)與
  OperatingExpense(營業費用 · Operating Expense(s) · OPEX)——ENG074 零改碼生效,它的恆等式就有運算元;② 比率另立 COGSRatio(營業成本率 · 銷貨成本率)
  與 OperatingExpenseRatio(營業費用率 · 費用率 · OPEX Ratio),跟第二血統 v0105 同一組鍵名;③ 正典 regex 庫加兩條比率式,並把 `cost_of_sales` 的
  中文式改成不吃後面的「率」(這一條是**改既有式**,不是純加——所以一定要你定)。

## 五 · 驗證

| 項 | 結果 |
|---|---|
| VRN/tests | **124**(財報表格 17 條:截圖表有框線 / 無框線第 6 頁 / 表頭沒認全不猜 / 加不起來不入庫 / 只有 EPS 照收 / 框線表不讀兩次 / 新表頭字樣)|
| 自測迴圈 合成 20 份一輪 | GREEN 99 / 0 / 0 · `[財報]` 跟批732 一字不差 |
| VDF ENG068 v0106 · ENG069 v0109 · VAP ENG014 v0103 | 7 / 7 · 缺料模式 4 / 4(合成庫全檢 9 / 9)· 7 / 7 |
| CGC_MDL095 v0160 · CGC_MDL094 v0101 | 26 / 26 · 10 / 10(`upA()` 三種情形實跑、整頁 JS 語法過)|
| VDF ENG061 v0105 · ENG062 v0104 | 10 / 10 · 9 / 9,正式庫前後一致(舊版對照組:兩支都改了正式庫)|
| VCGC · 契約 | 37 / 37 · 19 / 19 · registry-sync APPLIED |
| **全格子 v0488** | **OK 348 · FAIL 1 · SKIP 6** · 686 秒(`GRID_20260924_172816.json`)· 唯一的紅仍是 CGC_MDL157 的 MDL135 撞號(Z190,等你裁定)· **正式庫前後一致** |
| 稽核(CGC_MDL158)| 新版本件數 = 前版(0 新增);`VRN_AutoTestLoop` 的 PINVER 是 main 上就有的一行(ticker master 檔名)|
| 陸券拒絕清單(CGC_MDL177 verify)| 活的 0 支 |
| PR #112 的 Codex 審查 | 程式 · 安全兩道都跑完、零建議 |

## 六 · 掉球

| 號 | 變化 |
|---|---|
| Z157 | **結**:共識上漲空間全線 ADJ(資料 · 控制塔 · ETF · 月營收 · 儀表板 · 指揮台)|
| Z189 | **結**:量出來只有 ENG061 / ENG062 兩支真的寫正式庫,改成暫存庫;全格子前後正式庫一致 |
| Z195 | 進行 → **候(工作站實量那 7 份)**:容器能量的全做完(截圖表無框線 0 → 36/36)|
| Z197 | **等你定**:第四節三條提議(① ② 純加,③ 改既有式)|

## 七 · 工作站(一貼即用)

同批732 那一段,只換成認批733 的檔(`supportive modules\registry\CGC_MDL095_DeckServer_v0160.py`)、分支叫 `b733-時間`;`via-vrnrun` 跑完再三步:
共識庫 build 一次(ADJ 算得出幾列)· 主動 ETF×共識分析跑一次(加權上漲空間換成 ADJ)· `regen-all`(指揮台頁換成「upside(最新 ADJ)」欄)。
本批沒有改任何 .ps1。

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
    if (git status --porcelain --untracked-files=no) { git stash push -m "workstation-local-before-b733" }
    git stash list | Select-Object -First 3
    git fetch https://github.com/tonykuni/movies-dataset main
    git merge-base --is-ancestor main FETCH_HEAD 2>$null; $ff = ($LASTEXITCODE -eq 0)
    if (-not (git rev-parse -q --verify refs/heads/main)) { git switch -c main FETCH_HEAD } elseif ($ff) { git switch main; git merge --ff-only FETCH_HEAD } else { git switch -c ("main-latest-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    if (-not (Test-Path ".\supportive modules\registry\CGC_MDL095_DeckServer_v0160.py")) {
        "  [拉取] main 還沒併批733 → 改拉批733 的分支(它 = main + 批733,本機另開 b733-時間,不動 main)"
        git fetch https://github.com/tonykuni/movies-dataset claude/awesome-bardeen-h0wm5v
        if ($LASTEXITCODE -eq 0) { git switch -c ("b733-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    }
} else { "  [解卡] 人寫件卡在衝突,不自動處理,先停:" + ($held -join " · ") }
if ($held.Count -eq 0 -and $LASTEXITCODE -eq 0 -and (Test-Path .\Invoke-VIA-VRN-v0104.ps1) -and (Test-Path ".\supportive modules\registry\CGC_MDL095_DeckServer_v0160.py")) {
    "  [後] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
    $log = "$env:TEMP\vrnrun_b733.txt"
    via-vrnrun 2>&1 | Tee-Object -FilePath $log
    Invoke-VIAPython -Family vrn ".\functional modules\VRN\VRN_ENG069_ConsensusDB_v0106.py" build 2>&1 | Tee-Object -FilePath $log -Append
    Invoke-VIAPython -Family vdf ".\functional modules\VDF\engine\VDF_ENG068_ETFConsensusAnalysis_v0106.py" 2>&1 | Tee-Object -FilePath $log -Append
    regen-all 2>&1 | Select-Object -Last 3 | Tee-Object -FilePath $log -Append
    Select-String -Path $log -Pattern '\[Celeritas\]|\[加速器\]|平行池|\[進度\] \d+/6|\[V[1-6]\]|\[進度\] \d+/\d+ L3|\[ROUND|\[DONE\]|\[ADJ\]|\[財報\]|財報恆等式|unruled financial table|no financial rows|\[共識庫\]|\[ETF共識\]|\[榜\]|rc=|總計|via-open' | ForEach-Object { $_.Line }
} else { Write-Host "  [拉取] main 跟批733 分支都沒拉到(上面幾行就是原因),先停" -ForegroundColor Red; git status --short | Select-Object -First 15 }
```

## 八 · 要貼回什麼

1. V6 的 `[財報]` 那一行,以及 G06 有沒有 `unruled financial table left out` 的 WARN(有的話整條貼)——那 7 份沒框線的報告現在讀到了幾份;
2. 兩行 `[共識庫]`(工作站價表齊,ADJ 算得出幾列)· 共識庫 build 之後主動 ETF×共識頁的加權上漲空間(`[榜]` 前三行);
3. `regen-all` 之後指揮台個股卡的共識表(截圖或貼那一格)。
