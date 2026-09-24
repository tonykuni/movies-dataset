# 批733 · 共識上漲空間全線換 ADJ · 沒有框線的表也讀、讀了要加得起來 · 自測真的不碰正式庫 · 2026-09-24

> 操作員 2026-09-24(批732 以 PR #112 併進 main 之後):「開pr及繼續完成全部 實測自修正值到完成」。
> 常令:「所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE」「自測實測自AUDIT直到完工 結果也要實測正確性」。
> PR #112 已由你開、併(16:56),Codex 程式與安全審查都跑完、零建議;本批照規矩從新的 main 重起分支(同名),另開新 PR。
> 收尾時 main 又前進兩次(側線 PR #113 · #114:關聯層去重寫入收正典),照規矩先 commit 再 merge(不 rebase);掉球表取聯集;
> 格子站名改檢數原擬 v0490 → 側線 PR #114 先用了 → 改落 **v0491**(LL334)。

## 一 · 共識上漲空間:全線換成最新 ADJ CLOSE(Z157 結)

批732 把 ADJ 上漲空間落進共識庫(VRN_ENG069 v0106 的旁表 + 視圖 `consensus_latest_adj`)、控制塔先換。本批把**其餘每一個讀共識上漲空間的地方**都換掉——
全樹逐支查過 `upside_pct` 的讀者(尾版),共識線就這些:

| 件 | 從前 | 本批 |
|---|---|---|
| VDF_ENG068 v0106 主動 ETF×共識 | `consensus_latest.upside_pct × 100`(原始價)| 讀 `consensus_latest_adj.upside_adj`;視圖不在 → 退回舊欄、頁上寫「原始價舊欄」;+⑦ |
| VDF_ENG069 v0109 月營收×共識 | 同上 | `q_join(adj)`:同一條 SQL 只換兩處(來源視圖、上漲空間欄),換不到就當場炸不靜靜退回;+⑧ 合成庫證 ADJ 車道 · ⑨ 頁上基準 |
| VAP_ENG014 v0103 標準儀表板 | 數字照吃上面兩支 | 兩張卡的標題寫出基準(字取自引擎的 `UPSIDE_BASIS`,一處定義);+⑦ |
| CGC_MDL095 DeckServer v0160 `/stock_data` | 共識列 c[8] = 原始價上漲空間 | 只增不減:每列尾端加 c[9] = ADJ(÷100,跟 c[8] 同單位)· c[10] = ADJ 狀態(判定走 ENG069 的視圖,STALE / NOT_RUN 一處算)· **c[11..13] ADJ 目標價 高 / 低 / 中位**(跟 c[9] 同一個 adj_factor)· **c[14..15] 最新 ADJ 收盤與日期**(PR #115 審查);c[9] 沒數 → c[11..15] 全空;+㉖ 暫存庫夾具 |
| CGC_MDL094 CommandDeck v0101 個股卡 | 「upside」欄 = c[8];高 / 低 / 中位 = 原始目標價 | 「upside(最新 ADJ)」= c[9];**目標高 / 低 / 中位(ADJ)** + **最新 ADJ 收盤**(中位 ÷ 收盤 − 1 就是 upside;PR #115 審查);算不出給狀態、目標價顯示原始價並標「(原始)」;舊橋沒有 c[9] → 顯示 c[8] 並標「原始價」;+⑩ |

量(容器):

- ETF×共識:22 檔 ETF 都有加權上漲空間(v0105 也是 22);**平均覆蓋權重 7.0% → 5.8%**——舊版的覆蓋來自 2454、2317 兩檔,
  它們的原始價是鉅亨自帶的 close;容器的價表**沒有一檔上市(.TW)股票**,ADJ 算不出、狀態寫「上市所整個不在 ADJ 表」。
  工作站價表齊,這兩檔會回來、而且是 ADJ。
- 月營收×共識:容器沒有月營收表(誠實缺料模式 4/4);另在合成庫上跑全檢 9/9:2330 取 ADJ 17.5(不是舊欄 20.0)、
  6173 取 33.2、2317 沒有 ADJ 就不入四象限。
- 指揮台:`upA()` 三種情形實跑——ADJ 30.0% · 「— ADJ_NO_FACTOR」(滑過看完整原因)· 舊橋「25.0%(原始價)」;整頁 JS 語法檢查過。
  PR #115 審查後目標價同基準,四種列實跑:ADJ 列 目標 135 / 99 / **117** · 最新 ADJ 收盤 **90** · upside **30.0%**(117 ÷ 90 − 1);過期列 目標「140(原始)」· 收盤「—」· 「— ADJ_STALE」;舊橋 目標「150(原始)」· 「34.0%(原始價)」。
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
| 證據核心 後段頁 `pdf_column_tables_later` | 有框線的表和前 4 頁都讀不到損益表時,往後讀到第 40 頁,但**只讀字面上像損益表的頁**(營業收入 / 毛利 / 每股盈餘 / Revenue / EPS …),長報告(初次評等)的財報在後段;**以真頁數為上界**(PR #115 審查:頁碼過了最後一頁 pdf_page_chars 回的是空頁不是 None,2 頁的報告會被重開解析 36 次)|
| 證據核心 期別的門 | `2025年(F)` ENG074 讀不出 → 拿掉「年」再問一次(預估旗標才不會掉)|
| 資料庫引擎 v0106 `gate_fallback_tables` | **沒有框線讀出來的表要加得起來才入庫**;加不起來 → 不入庫,在那一份報告的 ValidationIssues 寫 `FIN_TABLE_REJECTED(表 · 哪一條 · 印多少 · 算多少)`;沒有可驗的(例:只有 EPS)照收;有框線的表不變(照批732 只警告)|
| 資料庫引擎 v0106 `drop_reread_tables` | 本批實測抓到:截圖那張**有框線**的表沒有 EPS 列,欄對齊讀法也在同一頁跑,表頭認得季之後**把同一張表又讀一次**(72 列 = 36 格 × 2)。欄對齊讀出來的表,數字有六成以上跟同頁的框線表一樣 = 同一張表,不收。(`2024A 2025F` 這種表頭以前就會重讀,一併修)|
| 自測迴圈 G06 | 被擋下的表 WARN 點名:`unruled financial table left out (does not add up): …` |

測試 `test_VRN_FinancialTable.py` 11 → **18** 條:第 6 頁無框線表逐格對 · 表頭沒認全不猜(有 / 沒有防線各跑一次)·
加不起來的表不入庫且點名(走整批入庫路徑)· 只有 EPS 的表照收 · 框線表不讀兩次 · 新表頭字樣逐一 · 後段頁掃描停在最後一頁(數真解析次數;舊迴圈對照組紅)。
合成 20 份一輪:GREEN 99 / 0 / 0,`[財報]` 那一行跟批732 一字不差(17/20 · 預估欄 136)——沒有回歸、沒有重讀。

## 三 · 自測真的不碰正式庫(Z189 結 · 收尾時再抓到一支)

批731 估「約 23 支自測可能開可寫連線」是字面掃的。本批改成**量**:每一支自測跑前跑後,三本正式庫(台股 · 全球 · 主動 ETF)的位元組與 mtime 各記一次。

| | 結果 |
|---|---|
| VDF_ENG061 v0104 因子庫 | **寫了正式庫**:自測呼叫 build(),在正式台股庫與全球庫上 CREATE OR REPLACE `features_daily`(台股庫 193,212,416 → 160,182,272 位元組;對照組再跑一次 → 162,803,712)|
| VDF_ENG062 v0103 族群因子層 | **寫了正式庫**:`group_features_daily`(→ 158,609,408)|
| 其餘 VDF 自測(ENG050 052 055 056 058 060 063 066 068 069 070 071 073 082)· CGC_MDL092 098 119 123 | 前後一致(自測本來就把庫指到暫存、或只讀)|
| **VDF_ENG061 v0105 · VDF_ENG062 v0104** | 輸入表**唯讀**複製進暫存庫(ATTACH … READ_ONLY),build() 寫暫存庫,①–⑨ / ①–⑧ 判準一字不動(同一份真資料);+⑩ / +⑨ build() 那一刻庫指向暫存夾;正式庫被鎖 → 誠實 NODATA(格子本站 nodata_ok)。**前後一致**,7 秒 / 1 秒。PR #115 審查:前置出錯**只有真的撞鎖**(DuckDB 原話「Could not set lock on file」)才判 NODATA,缺 duckdb = ABSENT rc3(格子判缺件),庫壞 / 程式錯不吞 → 紅(原本一律 NODATA,本站 nodata_ok 會把壞掉吞成綠);+⑪ / +⑩ 判法本身;缺料那條路的計數行更正 |
| 全格子前後三本正式庫(v0488)| 跑前跑後位元組與 mtime 一個都沒變(台股 158,609,408 · 全球 15,478,784 · 主動 ETF 3,420,160)——**但這個量法抓不牢**,見下兩列 |
| **CGC_MDL121 v0104 完工自動化** | 併 main 後再跑全格子 v0491:台股庫 **mtime 在跑的那 11 分鐘裡變了**(位元組沒變)。逐站前後量,抓到它:自測 ④ 真跑完工鏈的 `revenue_groups` 步 = `VDF_ENG063 --groups`,那支以**可寫**打開正式台股庫、`CREATE TABLE IF NOT EXISTS` + `CREATE OR REPLACE VIEW`(改了正式庫的結構)。v0488 那一輪沒量到,是剛好別站鎖著庫、ENG063 開不了 → 誠實回 0——**時有時無**。批733 前面的 AST 掃描只看自測自己的連線,經子行程呼叫別支引擎的看不到 |
| **CGC_MDL121 v0105** | ④ 改成同一套 run() 跑**替身步**(暫存夾一支印「1/1」的小檔頂 revenue_groups;COMPLETION 存證 + 步 log 落盤照驗),引擎真跑歸 ENG063 自己的自測(本來就用暫存庫);+⑩ 三本正式庫整支自測前後位元組與 mtime_ns 不變。**十檢 10/10**;監看器實證:v0104 一跑 → 台股庫 WAL 建 / 寫 / 併回主檔(CLOSE_WRITE);v0105 → 零事件 |
| **全格子 + 檔案監看(inotify)** | 改成**看每一次可寫打開**,不只比跑前跑後:全格子 v0491 跑的時候同時監看三本正式庫的資料夾(CLOSE_WRITE = 有人以可寫打開過再關上,就算一個位元組都沒寫)。**兩輪全格子(修後 · 各約 690 秒)整跑都零次可寫打開:CLOSE_WRITE 0 · MODIFY 0 · 建 / 刪 0(對照:CGC_MDL121 v0104 單跑一次就有 WAL 建 / 寫 / 併回主檔)** |
| **格子自己守門(v0491)** | 每一次全格子跑前跑後各 stat 三本正式庫,存證 GRID json 多一欄 `prod_db`,摘要多一行 `[正式庫]`;變了只**警告**(工作站上同時段你另外跑的日更 / 回補也會改它,格子分不出是誰);要找站就 `--only <站名子字串>`,那條路也前後 stat、印同一行。格子自測 +⑦ 守門實跑 |

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

## 五 · 產品閘的核心站鑰匙(Z201 結)

LL213:站名裡的檢數要手動跟。本批四站加了檢(因子庫 九 → 十 · 族群聚合因子層 八 → 九 · 指揮台 九 → 十 · 執行橋 八 → 二十六,執行橋的「八」是批208 的數、之後各版加檢站名都沒跟),改站名之前先查「誰拿站名當鑰匙」——查到產品閘 CGC_MDL133:

| | v0101 | v0102 |
|---|---|---|
| 核心站鑰匙 | 字面「執行橋八檢」「指揮台九檢」**帶著檢數**:站名一跟,那一站**靜靜**掉出核心(紅了也不算核心紅)| 不看檢數:「執行橋…檢(批208」「指揮台…檢(批204」|
| 批376 八站 | 字面「(批376)」右括號要緊接;批406 持股史深改「(批376/406…」、批611 產品資格閘改「(批376;批611…」之後**只數到 7** | 「(批376」後接 ) / ; 都算 → 9 站(八站 + 產品資格閘本身,跟批376 設計時一樣)|
| 真存證的 G1 | **FAIL**「存證早於 v0225(批376 八站未入)」——從批611 起一直這樣誤判,存證其實是新的 | **WARN**:核心站 17/17 · 批376 9 站 · 唯一的紅是 Z190 MDL135 撞號(產品閘的分類器判它「料側?」,所以是 WARN 不是 FAIL)|
| 以後誰再改站名 | 沒人知道 | +⑩ 盯尾版格子:每把鑰匙至少認到一站、批376 至少 8 站,認不到就紅 |

其餘八閘一字不動(①–⑨ 輸出逐字相同)。格子 v0491 六站只換檢數:上面四站 + 產品資格閘 九 → 十 + 全面自測矩陣自身 五 → 七(第三節守門 +⑦,本來就少寫一檢)。
其他拿站名當鑰匙的:專案完工矩陣 CGC_MDL131 認「因子庫」「回補」這種不帶數的字,不受影響;各頁與冊上的站名是再生物,跟著格子。
順手普查:全格子站名帶檢數、自測印明確計數的 144 站裡 **35 站對不上**(Z202,候你定:① 一次對齊 或 ② 改律站名不寫檢數)。

## 六 · 驗證

| 項 | 結果 |
|---|---|
| VRN/tests | **125**(財報表格 18 條:後段頁停在最後一頁 · 截圖表有框線 / 無框線第 6 頁 / 表頭沒認全不猜 / 加不起來不入庫 / 只有 EPS 照收 / 框線表不讀兩次 / 新表頭字樣)|
| 自測迴圈 合成 20 份一輪 | GREEN 99 / 0 / 0 · `[財報]` 跟批732 一字不差 |
| VDF ENG068 v0106 · ENG069 v0109 · VAP ENG014 v0103 | 7 / 7 · 缺料模式 4 / 4(合成庫全檢 9 / 9)· 7 / 7 |
| CGC_MDL095 v0160 · CGC_MDL094 v0101 | 26 / 26 · 10 / 10(`upA()` 三種情形實跑、整頁 JS 語法過)|
| PR #115 CI(Windows UAT,只裝標準庫)| 第一輪紅:CGC_MDL095 v0160 ㉖ 無條件 `import duckdb`,那個環境沒有 → 整支自測炸。改成缺 duckdb 就誠實 SKIP(`OK 25 · FAIL 0 · SKIP 1(㉖ 本境缺件)`),有 duckdb 的境照跑 26 / 26;本機以只有標準庫的 venv 重跑 CI 四支自測 + 契約 19 / 19 + 瀏覽器 UAT(Playwright 1.55)全過 |
| VDF ENG061 v0105 · ENG062 v0104 | 11 / 11 · 10 / 10,正式庫前後一致(舊版對照組:兩支都改了正式庫);沒有 duckdb 的境 → ABSENT rc3;負控:假撞鎖 → NODATA 2、假程式錯 → 照常丟出;缺料路 十一檢 OK 3 · NODATA 1 · SKIP 7 / 十檢 OK 3 · NODATA 1 · SKIP 6 |
| VCGC · 契約 | 37 / 37 · 19 / 19 · registry-sync APPLIED(併 main 後再跑,同)|
| CGC_MDL133 v0102 產品閘 | 10 / 10(①–⑨ 輸出跟 v0101 逐字相同)· 真存證 G1 FAIL(誤判)→ WARN |
| CGC_MDL121 v0105 完工自動化 | 10 / 10 · 正式庫前後一致(v0104 對照組:改了台股庫)|
| 格子自測(全面自測矩陣自身)| 7 / 7(+⑦ 正式庫守門實跑)|
| 全格子 v0488(併 main 前)| OK 348 · FAIL 1 · SKIP 6 · 686 秒(`GRID_20260924_172816.json`)|
| 全格子 v0491(併 main 後 · MDL121 修前)| OK 348 · FAIL 1 · SKIP 6 · 692 秒(`GRID_20260924_180127.json`)· **台股庫 mtime 變了** → 抓到 CGC_MDL121 v0104 |
| **全格子 v0491(修後 · 檔案監看)** | **OK 348 · FAIL 1 · SKIP 6** · 686 秒(`GRID_20260924_183735.json`)· 唯一的紅仍是 CGC_MDL157 的 MDL135 撞號(Z190,等你裁定)· 改名六站全綠 · 正式庫前後一致(台股 158,609,408 · 全球 15,478,784 · 主動 ETF 3,420,160)· 監看 兩輪全格子(修後 · 各約 690 秒)整跑都零次可寫打開:CLOSE_WRITE 0 · MODIFY 0 · 建 / 刪 0(對照:CGC_MDL121 v0104 單跑一次就有 WAL 建 / 寫 / 併回主檔) |
| 稽核(CGC_MDL158)| 新版本件數 = 前版(0 新增);`VRN_AutoTestLoop` 的 PINVER 是 main 上就有的一行(ticker master 檔名)|
| 陸券拒絕清單(CGC_MDL177 verify)| 活的 0 支 |
| PR #112 的 Codex 審查 | 程式 · 安全兩道都跑完、零建議 |
| **PR #115 的 Codex 審查** | 安全零建議;程式三條全屬實、全修:① P2 後段頁掃描不停在最後一頁 → 以頁數為上界 + 測試 ② P1 指揮台原始目標價站在 ADJ upside 旁 → 橋帶 ADJ 目標價與最新 ADJ 收盤、卡片同基準 ③ P1 ENG061 / ENG062 前置出錯一律判 NODATA → 只有撞鎖才算 |

## 七 · 掉球

| 號 | 變化 |
|---|---|
| Z157 | **結**:共識上漲空間全線 ADJ(資料 · 控制塔 · ETF · 月營收 · 儀表板 · 指揮台)|
| Z189 | **結**:ENG061 / ENG062 自測寫正式庫 → 暫存庫;收尾時再抓到 CGC_MDL121(經子行程可寫開正式庫)→ v0105 替身步;全格子檔案監看零可寫打開;格子每跑自己守門 |
| Z195 | 進行 → **候(工作站實量那 7 份)**:容器能量的全做完(截圖表無框線 0 → 36/36)|
| Z197 | **等你定**:第四節三條提議(① ② 純加,③ 改既有式)|
| Z201 | 新開即結:產品閘核心站鑰匙帶檢數、批376 只數到 7 → G1 從批611 起誤判;CGC_MDL133 v0102(第五節)|
| Z202 | 新開 · 候你定:全格子站名檢數普遍沒跟(144 站裡 35 站對不上);本批只改自己碰到的六站;① 一次對齊 或 ② 改律站名不寫檢數 |
| Z203 | 新開 · 候 VME 線:「VME 核心八檢」三輪全格子紅 1 次(8/8 PASS 後結束時 C++ 中止;第二段序跑轉綠),單跑 / 平行 96 次重現 0 次;那支經 pandas 載入 pyarrow;提議單執行緒讀回或啟動層收 pyarrow——**不當 flake** |

## 八 · 工作站(一貼即用)

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

## 九 · 要貼回什麼

1. V6 的 `[財報]` 那一行,以及 G06 有沒有 `unruled financial table left out` 的 WARN(有的話整條貼)——那 7 份沒框線的報告現在讀到了幾份;
2. 兩行 `[共識庫]`(工作站價表齊,ADJ 算得出幾列)· 共識庫 build 之後主動 ETF×共識頁的加權上漲空間(`[榜]` 前三行);
3. `regen-all` 之後指揮台個股卡的共識表(截圖或貼那一格)。
