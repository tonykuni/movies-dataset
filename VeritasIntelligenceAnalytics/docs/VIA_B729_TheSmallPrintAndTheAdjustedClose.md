# 批729 · 附錄小字認券商與評等法 · 目標價與前一日價換 ADJ CLOSE · 2026-09-24

> 操作員令(原文):「DILUTED 券商 RATING 目標價在修正後本文集上左右資訊區都會出現 查同意字SSOT 分析師中英文姓名在職稱或電郵及電話之上
> 昨天有新增REGEX並強調@左邊通常為分析師名 右邊通常為券商 第一頁頁尾小自體不相關內文採局部識別可抓到券商 報告後小字體不相關附錄可抓到局部識別券商
> 文件名分解後可抓中英文券燒縮寫採局部 報告後方小自己附錄可抓到所有平等法可增加道同意自」
> 中途令(原文):「所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE」
> 沿用令:「"C:\測試樣本報告" 實測實修正直到成功」「py 指令都要加入加速器;ps 指令都要加入 25 個加速器;動態進度條不卡斷、動態百分比」。

## 一 · 七條擺放規則,逐條對到程式碼

先量再動:七條裡五條第二血統早就有(批713 / 批728 帶回來的規則),**缺的是「報告後方的小字附錄」那兩條**。

| # | 操作員規則 | 第二血統落點 | 本批 |
|---|---|---|---|
| 1 | DILUTED / 券商 / RATING / 目標價在左右資訊區,查同義字 SSOT | 評等、目標價的標籤詞讀正本 `VRN_FieldRules_SSOT`(批634)與機構 SSOT;頁尾帶「稀釋 / diluted / 目標價 / 評等」的行保留(`_KEEP_FOOTER`);EPS 表由 `column_tables` / `transposed_tables` 讀;`xv_zone_presence` 驗資訊區與本文都有料 | 既有 |
| 2 | 分析師中英文姓名在職稱或電郵、電話之上 | `_chinese_name_above`(往上 6 行內單獨一段的 2–3 字中文名)· CGC_MDL182 每個電郵一個視窗(批713 錨點回溯) | 既有 |
| 3 | @ 左邊是分析師、右邊是券商 | `reverse_name`(@ 左反推姓名:只 `.` `_` 分詞,`-` 保留)· 網域冊定券商(EMAIL 層,最強) | 既有 |
| 4 | 第一頁頁尾小字(與本文無關)局部識別券商 | `broker_evidence`:末 8 行頁尾帶 = HEADER 層;`©` / `copyright` / `著作權` = DISCLOSURE;「證券 / 投顧 / 投資顧問」接在別名後 = ISSUER | 既有 |
| 5 | **報告後方小字附錄局部識別券商** | **新** `appendix_lines` / `appendix_evidence`(見二) | **本批** |
| 6 | 檔名分解抓中英文券商縮寫(局部) | 首頁引擎 `_filename_fields`:逐 token 最長別名優先、公司名片段排除、拒絕清單先跑 | 既有 |
| 7 | **附錄的評等定義(所有評等法)可增加到同義字** | **新** `rating_scale`:只出候選,不寫冊(見二) | **本批** |

## 二 · 附錄小字(VRN_Evidence_Core v0102 · 首頁引擎 v0104)

- **哪裡算附錄**:最後 3 頁(第 1 頁除外);**小字** = 字級 < 0.9 × 首頁本文字級(本文字級 = 首頁字元最多的那個字級,四捨五入到 0.5pt)。一頁的檔 = `NODATA`(沒有附錄),不是錯。
- **券商**:同一支 `broker_evidence`、同一道拒絕閘(被拒名在小字裡出現也只記 DENIED,永不成為發行人)。只有附錄這一次呼叫把揭露句式放寬到中文(`版權所有` / `本報告由…發佈` / `免責聲明` / `分析師聲明` / `important disclosures` …)——**首頁判法逐位不變**(106 份真值是在 v0101 判法上量的)。
- **首頁引擎怎麼用**:首頁已有強證(EMAIL / DISCLOSURE / ISSUER)→ **附錄永不翻案**;首頁弱 → 附錄強證補上,`broker_tier = APPENDIX_<層>`;附錄說的和檔名不一樣 → 記 `broker_conflict`(REVIEW),**不悄悄贏**。
- **評等法**:`買進(Buy):預期…` / `Outperform (OP): …` 這種定義行收成候選,每個詞標 KNOWN / NEW(對合併評等詞表);NEW 詞只有在它的配對詞是 KNOWN 時才給建議鍵(`甲乙試評 ~ Outperform`),兩個都不認得就不猜。**只出候選、一本冊都不寫**——同義字只增不減,要經樞紐(CGC_MDL176 / SUP_MDL749)。
- **出口**:`python VRN_Evidence_Core.py appendix <pdf|資料夾>... [--out 夾] [--last N]` → `VIA_Reports/vrn_appendix/APPENDIX_latest.json|.md`(每檔 `[進度] k/N`);自測迴圈 v0103 每輪寫 `RATING_SCALE_CANDIDATES.json` 並印一行 `[附錄]`。

## 三 · 目標價與前一日價換 ADJ CLOSE,上漲空間用最新 ADJ CLOSE

**算法只有一份**:母倉 L99(批659 操作員裁示)—— 因子 = 報告日前一交易日的 `adj_close / close`;目標價(ADJ)= 目標價 × 因子;上漲空間 = 目標價(ADJ)÷ **最新** `adj_close` − 1。正本在 ENG073,本批只補它漏的一塊、再讓第二血統委派它(LL404)。

| 件 | 本批做了什麼 |
|---|---|
| **ENG073 v0137** | 量過才動:目標價換 ADJ 與上漲空間用最新 ADJ 是 L99 早就寫好的;**漏的是「前一日的價格」**——因子拿前一日 close/adj_close 算,那一天的 ADJ CLOSE 本身從沒落欄。+`price_prev_close` / `price_prev_adj` / `price_prev_date`(只增不減;有代號與報告日就填,和有沒有目標價無關)。因子與前一日價走同一個查詢(`_prev_close_adj`)。+`adj_quote()`:L99 的委派口。缺價因由的檔數改現場數(原寫死 892)。自測 +⓯ ⓰ → 57/57 |
| **證據核心 v0102** `adj_basis()` | 找 ENG073 尾版(按版號排,不寫死)與市場庫(ENG073 的解析器:`VIA_DB_VDF_TW_MARKET` > `VIA_DATA_HOME` > mega 路徑 > 樹內搜尋;印出來的行收進 `why`),**唯讀開庫**、問 `adj_quote`、原樣轉回。問不到的每一種都具名:`ADJ_NO_ENGINE` / `ADJ_NO_DB` / `ADJ_NO_DUCKDB` / `ADJ_DB_BUSY` / `ADJ_ERROR`;問到了就是 ENG073 自己的 `ADJ_OK` / `ADJ_NO_KEY` / `ADJ_NO_TARGET` / `ADJ_NO_FACTOR`(帶因由)/ `ADJ_NO_LATEST` / `ADJ_ABSURD(…)`。**永不編一個 1.0 出來**。CLI:`VRN_Evidence_Core.py adj <代號> <報告日> [目標價] [--db 庫]` |
| **首頁引擎 v0104** | `upside` 改 ADJ 口徑:`basis = ADJ_LATEST`,`DERIVED_ADJ` 或 `NO_ADJ`(帶 state 與因由),並帶 `target_price_adj` · `price_prev_close / price_prev_adj / price_prev_date` · `page_price_adj`(頁面印的價 × 同一個因子)· 最新 adj close 與日期。**頁面算術**(目標價 ÷ 頁面價)留作 `upside_page`——v0103 把它標成「latest adjusted close」,其實除的是頁面價,這次照實改標。非台幣目標價(`USD` / `HKD`)不放到台股 adj close 上算(`ADJ_CURRENCY(…)`);產業 / 市場 / 總經報告沒有標的,不問 |
| **資料庫引擎 v0103**(schema `VRN_SCHEMA_20260924_004`) | `UpsideDownsidePct` = ADJ 上漲空間;+12 欄只增不減(`UpsideBasis` · `UpsideState` · `UpsidePagePct` · `TargetPriceAdj` · `AdjFactor` · `AdjFactorDate` · `PrevClose` · `PrevCloseAdj` · `PrevCloseDate` · `CurrentPriceAdj` · `LatestAdjClose` · `LatestAdjDate`),數值欄定型。ADJ 缺 → 格子空、`UpsideState` 講為什麼,**頁面值不頂替** |
| **自測迴圈 v0103** | 每檔記 ADJ 狀態;報告 `adj` 摘要(算出幾檔、其餘各卡在哪一種、最多的因由、逐檔明細);主控台一行 `[ADJ]`。**量測,不是關卡**:缺價照實報名字,不判 FAIL |

**容器實量**(合成語料 107 檔,一輪):`[ADJ] 算出 10/58 檔(有目標價者)· 其餘 ADJ_NO_KEY 47 · ADJ_NO_FACTOR 45 · ADJ_ABSURD 3`。合成語料的目標價是造出來的(頁面上漲空間一律約 30%),所以 ADJ 數字在合成檔上**沒有意義**,ABSURD 護欄照常擋下極端值;`ADJ_NO_FACTOR` 45 檔全是上市股——**容器的價表沒有上市所**(`tw_daily_prices` 893 檔全是 .TWO,掉球 Z155)。真值要在工作站量(十)。

**下游消費端稽核**(操作員說「所有」,所以每一個會出上漲空間的地方都對了一次):

| 消費端 | 現況 | 處置 |
|---|---|---|
| ENG073 v0137(正本) | L99 ADJ 車道;RAW 車道具名 `RAW_CLOSE` 不冒充 | 本批補前一日價 |
| 第二血統首頁引擎 / 資料庫引擎 / 自測迴圈 | 原本用頁面價算、還標成 adjusted | 本批改委派 ENG073 |
| 母倉首頁引擎 v0127 | 批426-H 起**拒用未復權價**算上漲空間(`is_adjusted=False` 回 None) | 不用動 |
| ENG083 v0119 驗真矩陣 | 讀 ENG073 的 `upside_adj` / `upside_adj_state` | 不用動 |
| ENG080 v0109 四點摘要 | 自己算因子鏈(報告日因子 ÷ 最新日因子)。容器量過 **893/893 檔最新日因子 = 1**,所以數值與 L99 相同;**唯一分歧**:因子推不出(報告日缺 / 報告日前無價列)時,拿**原始目標價**對最新 adj close 算——這條被批643 自測 ㉗ 逐字釘住 | **Z156**(要改得出 v0110 並改 ㉗,那是該線的自測;等操作員點頭) |
| ENG069 v0105 共識庫 → ENG079 控制塔 / VAP_ENG014 | `upside_pct = target_median ÷ 同日 close − 1`(原始價,但同一時點) | **Z157**(共識線) |

## 四 · 併線與號碼(LL334)

推之前查了全部 37 條遠端分支:**批729、ENG073 v0137、VDF_ENG093 v0102 沒有人用過**。main 在本批進行中前進到 **e81b0b5b**(PR #93 VDF 側線第三段 · PR #94 VIA Integration 批727a–k,帶進 VRN_ENG086 v0116 與 `VRN_FieldRules_SSOT` 的改動)。

本線先 commit(`批729(一)` 1cfaf893)再 `git merge`(不 rebase、不 force-push):衝突六檔——四本生成冊取 main 再由正主重生(registry-sync 活 9510 · 新 64 · 退役 0;六層冊 v0107 build,ENG073 尾版改指 v0137;正則清冊 CGC_MDL115 v0101 樣式 1369 · 共用 720;總控頁 manager v0148)、AutoCode 台帳兩邊追加的條目全留(1313 + 側線 7 + 本線 2)、掉球冊手併(**Z137 兩份實證合成一列**:工作站 2026-09-23 那份與容器 pwsh 7.4 第 24/83 行那份;Z138 兩邊逐位相同)。main 的格子 v0477 自 ae13939b 以後一字未動,本線 v0478 已含它的兩站。併後 VRN/tests **84/84**(main 改過的 `VRN_FieldRules_SSOT` 沒有打到第二血統)。

## 五 · 測試與自測

- VRN/tests **84/84**(+`test_VRN_Appendix` 10 支:小字篩選與發行人 · 一頁 NODATA · 首頁判法不變 · 被拒名永不當發行人 · 弱首頁補上 · 強首頁不翻案 · 與檔名衝突記 REVIEW · 評等法 KNOWN/NEW/建議 · 首頁引擎帶評等法 · CLI 只寫報告不寫冊;+`test_VRN_AdjBasis` 10 支:臨時 DuckDB 上手算逐位 · 代號與日期各種寫法 · 每一種缺具名 · 查價永不寫庫 · 解析器認資料家目錄頁 · CLI · 首頁引擎 ADJ 與頁面分開 · 外幣目標價不算 · 缺價不退頁面值 · 資料庫欄)。測試不存任何真實價格,價表是測試當下建的臨時庫。
- 自測迴圈 `--selftest` OK 2/2;合成一輪 **AMBER · PASS 357 · WARN 1 · FAIL 0**(WARN = 926708.jpg 要 OCR)。
- ENG073 v0137 自測 **57/57**;VCGC v0128 **37/37**;CGC_MDL185 24/24;CGC_MDL184 19/19;契約 OK。

## 六 · 全格子 v0478(容器;PATH 帶 /opt/pwsh)

站數 348(fast)不變;本樹現在有 VDF_ENG093(PR #93 帶進 main),批728 那兩站不再因「引擎缺」SKIP:一鍵啟動台自測實跑 OK,資料庫狀況頁實跑回 rc3(容器沒有目錄)照實仍計 SKIP。

| 段 | 內容 | 結果 |
|---|---|---|
| 第一段平行跑 | 併 main 後的樹 | 紅 1:「PowerShell 語法與參數名閘」。A 語法道是具名舊債(棘輪:基線 5 支 / 53 筆,新壞 0);**真正的紅是 C 轉義道**:`VDF_ENG093_LaunchConsole_v0101.py` 問參數頁內嵌 JS 的 `\d` 寫在非 raw 的 f-string(py3.12 會在操作員終端印 SyntaxWarning;**main 同紅**,不是本批造成的) |
| 修 | VDF_ENG093 **v0102**(母線代修,Z160) | 只改那一個跳脫:**整支模組 AST 與 v0101 完全相同**(產生的頁逐位元不變)· 自測 12/12 · 閘 GREEN · 啟動器以萬用字元取尾版,自動接上 |
| 第二段序跑複判 | 平行敗 4 站(其中 3 站是單寫者庫鎖撞) | 全部轉綠 |
| **合計** | | **OK 342 · FAIL 0 · SKIP 6 · TIMEOUT 0**(884 秒;存證 `VIA_Reports/selftest_runs/GRID_20260924_070017.json`,不入 git) |

SKIP 6 全是環境缺件,照實列:reconcile 對帳(沒有對帳報告)· 全景批次修復計畫實跑 · 三個專案打包就緒實跑 · 功能級整合驗收實跑(這三站 rc 是現況分類)· 格子自指佔位 · VDF 資料庫狀況頁實跑(容器沒有 CGC_MDL123 目錄 = rc3)。

格子跑完之後又動了兩處:ENG073 v0137 的缺價因由改成現場數(v0135 起寫死「892 檔全是 .TWO」,容器現在 893 檔;庫裡有上市價時改說「這一檔不在」,下一步不同),ADJ 測試多釘這一條。單站複驗 `--only`:報告結構化入庫 · VDF 一鍵啟動台自測 · VRN 第二血統總驗 · 母倉↔姊妹倉同步 全 OK;VRN/tests 84/84;ENG073 自測 57/57。再生閘(CGC_MDL167)倒回格子寫的 40 支再生物(備份 `VIA_Reports/regen_revert/20260924_071739`),ENG093 v0102 進樹後 registry-sync(活 9510 · 退役 0)與正則清冊(樣式 1369 · 共用 722)重跑,契約 OK。

## 七 · 掉球(新列)

| 代號 | 事 | 狀態 | 誰 | 下一步 |
|------|----|------|----|--------|
| Z155 | 容器市場庫 `tw_daily_prices` 893 檔全是 .TWO(上櫃),**上市所整個不在**:上市股的 ADJ 上漲空間一律 `ADJ_NO_FACTOR`(批729 合成一輪 45 檔)。第二血統照實報 `NO_ADJ`、**不退頁面值**;ENG073 另有具名 `RAW_CLOSE` 車道 | 開(資料缺) | VDF 線 → 操作員 | 工作站跑一次 V6 看 `[ADJ]` 那一行:算出數明顯變多 = 工作站庫有上市價;仍卡 `ADJ_NO_FACTOR` = 要補上市所價(`via-market-lists` 補名冊 + `via-price` 抓價,**要開同意閘,AI 不開**) |
| Z156 | ENG080 v0109 四點摘要自算因子鏈(報告日因子 ÷ 最新日因子);容器量過 893/893 檔最新日因子 = 1,數值與 L99 相同。**唯一分歧**:因子推不出(報告日缺 / 報告日前無價列,`adjust_method=NONE`「目標價照列」)時,`upside(tp_adj if tp_adj is not None else tp, adj)` 拿**原始目標價**對最新 adj close 算——操作員 09-24「所有目標價…都要換成 ADJ CLOSE」之下這是混基準;批643 自測 ㉗ 逐字釘住這一行 | 候(操作員確認) | 操作員 → ENG080 線 | 准就出 v0110:因子推不出 → 上漲空間不算、講因由(同 L99 的 `ADJ_NO_FACTOR` / `ADJ_NO_KEY`),㉗ 改釘新行;要不要一併改成委派 ENG073 `adj_quote`(一個算法一個地方)同時裁 |
| Z157 | 共識庫 ENG069 v0105 `upside_pct = target_median ÷ 同日 close − 1`(原始價、同一時點;ENG079 控制塔與 VAP_ENG014 儀表板都讀它)。操作員 09-24「上漲空間都要用最新的 ADJ CLOSE」還沒落到共識線 | 開 | 共識線(VRN ENG069/070 · VAP) | 新版:目標中位數 × 共識日因子 ÷ 最新 adj close − 1,委派 ENG073 `adj_quote`(報告日取共識日的次一交易日,因子即共識日那一列);舊欄留,只增不減 |
| Z158 | 附錄評等法的新詞(V6 工作夾 `RATING_SCALE_CANDIDATES.json` · `VIA_Reports/vrn_appendix/APPENDIX_latest.md` 的 new_words)只是**候選**:NEW 詞有 KNOWN 配對才給建議鍵,兩個都不認得就不猜 | 候(工作站實測後操作員裁) | 操作員 → VCGC ssot 門 | 工作站產出候選 → 操作員圈選 → 走樞紐只增不減(CGC_MDL176 聯集 / SUP_MDL749 增補冊);證據核心與自測迴圈永不寫冊 |
| Z159 | 附錄的兩個門檻(末 3 頁 · 字級 < 0.9 × 首頁本文)只在合成 PDF 上定過;106 份實檔沒量(容器拿不到,Z144) | 候(工作站實測) | 操作員 → 母線 | 工作站 `Invoke-VIAPython -Family vrn ".\functional modules\VRN\engine\VRN_Evidence_Core.py" appendix "C:\測試樣本報告"`:看「讀到附錄小字 N/M」與逐檔 `why`;要調只改 `APPENDIX_PAGES` / `SMALL_RATIO`,並附量測 |
| ~~Z160~~ | ~~VDF_ENG093 v0101(側線 2026-09-23,PR #93 進 main)問參數頁內嵌 JS 的起始日檢查 `\d` 寫在非 raw 的 f-string → 全格子「PowerShell 語法與參數名閘」C 轉義道紅(main 同紅;py3.12 會在操作員終端印 SyntaxWarning)~~ | 已結(批729) | 母線代修 → VDF 側線知悉 | **v0102 已由母線用掉**:只改那一個跳脫,整支模組 AST 與 v0101 相同(產生的頁逐位元不變)、自測 12/12;側線下一版請出 **v0103** |

## 八 · 沒做到的(照實講)

- **實檔實測還是在工作站**:容器只有合成語料(一頁,沒有附錄);OneDrive 實測資料仍抓不進 AI 環境(Z144,不繞)。附錄的兩個門檻(末 3 頁、0.9 倍本文字級)是在合成 PDF 上定的,要用 `C:\測試樣本報告` 量過才准調(Z159)。
- **上市股的 ADJ 上漲空間在容器算不出**:價表沒有上市所(Z155)。工作站的庫若有,`[ADJ]` 那一行就會看到數字變多;若也沒有,要開同意閘補價——**AI 不開閘**。
- ENG080 的原始目標價退路(Z156)與共識庫的同日 close(Z157)**本批不越線改**:兩支各有自己的線與自測,改法寫在掉球列,等你點頭。
- 評等法候選要不要進同義字冊(Z158)是操作員裁;迴圈只產候選。

## 九 · 工作站(一貼即用;批729 第三版:先解卡,再切到最新 main)

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
    if (git status --porcelain --untracked-files=no) { git stash push -m "workstation-local-before-b729" }
    git stash list | Select-Object -First 3
    git fetch https://github.com/tonykuni/movies-dataset main
    git merge-base --is-ancestor main FETCH_HEAD 2>$null; $ff = ($LASTEXITCODE -eq 0)
    if (-not (git rev-parse -q --verify refs/heads/main)) { git switch -c main FETCH_HEAD } elseif ($ff) { git switch main; git merge --ff-only FETCH_HEAD } else { git switch -c ("main-latest-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
} else { "  [解卡] 人寫件卡在衝突,不自動處理,先停:" + ($held -join " · ") }
if ($held.Count -eq 0 -and $LASTEXITCODE -eq 0 -and (Test-Path .\Invoke-VIA-VRN-v0103.ps1) -and (Test-Path ".\functional modules\VRN\VRN_ENG073_ReportStructuredDB_v0137.py")) {
    "  [後] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
    Invoke-VIAPython -Family vrn ".\functional modules\VRN\engine\VRN_Evidence_Core.py" appendix "C:\測試樣本報告"
    Invoke-VIAPython -Family vrn ".\functional modules\VRN\engine\VRN_Evidence_Core.py" adj 6147 2026-05-19 280
    via-vrnrun 2>&1 | Tee-Object -FilePath "$env:TEMP\vrnrun_b729.txt"
    Select-String -Path "$env:TEMP\vrnrun_b729.txt" -Pattern '\[Celeritas\]|\[進度\] \d+/6|\[V[1-6]\]|\[ROUND|\[DONE\]|\[附錄\]|\[ADJ\]|FAIL G|WARN G|RED|rc=' | ForEach-Object { $_.Line }
} else { Write-Host "  [拉取] 沒拉到批729,先停(上面幾行就是原因)" -ForegroundColor Red; git status --short | Select-Object -First 15 }
```

- **解卡**:卡在合併就 `git merge --abort`;卡在再生冊(六層冊、U/I 頁、再生冊)就取已提交的版本(V1 每跑都會重建);**人寫件(例如 AutoCode 台帳)卡住就整段停,什麼都不動**。
- `via-regen --apply` 只倒回引擎再生的頁與冊,倒之前整包備份;其餘本機改動收進 `git stash`,**保留不刪**(`git stash list` 看得到)。
- **切到最新 main**(PR #96 已把批729 併進 main):本機沒有 main 就建;本機 main 落後就快轉;本機 main 有自己的提交就另開 `main-latest-<時間>`,本機 main 一字不動。原本所在分支與它的本機提交都留著。
- 容器以 pwsh 7.4 實跑四種情境:stash 放回卡住 · 合併卡住 · 本機 main 分岔 · 台帳卡住(停)。

要貼回:`[前]` 幾行 · `[解卡]` 行 · `git stash list` 三行 · `[後]` 一行 · `appendix` 最後一行 · `adj` 前兩行 · V6 的 `[ROUND …]`、`[附錄]`、`[ADJ]`、`[DONE]` 各一行 · 任何 `FAIL G..` 行;停下來就貼停的那一行與下面的 `git status`。

## 十 · 工作站第一次回報(2026-09-24;**跑到的是舊碼**)

**判定**:`via-vrnrun` 只跑了五步(V1–V5;本分支 `Invoke-VIA-VRN-v0103.ps1` 才有 V6),六層鏈裡 ENG073 那一行最後一檢是 ⓮(v0137 到 ⓰)——工作站那棵樹是舊碼(Invoke-VIA-VRN v0102 · ENG073 v0136),**批727–729 都沒拉進去**(原先以為是 main;第二次回報才看出它停在 envmanager 分支,見十一)。最可能的兩個原因:本機每跑都會改寫的冊與頁擋住合併(批613 記過的病根,`via-regen` 就是為它立的),或新版 git 在分支分岔時 `git pull` 要求先指定合併方式。新的一貼即用改成:`via-regen --apply`(再生物倒回,先整包備份)→ 其餘本機改動 `git stash`(**保留不刪**,`git stash list` 看得到)→ `git fetch` + `git merge FETCH_HEAD` → 驗 v0103 與 v0137 在場才往下跑。

**量到的**(舊碼,工作站真庫):

| 步 | 結果 |
|---|---|
| V2 六層鏈 44 節點 | GREEN 32 · NODATA 14 · RED 0 · GATED 0 · ABSENT 0(rc2 = 缺料,不是壞) |
| V3 ADJ 上漲空間 | 算得出 **39**(ADJ_OK 25 + ADJ_OK(因子1)14)· ADJ_NO_KEY 49 · ADJ_NO_TARGET 17 · **ADJ_NO_FACTOR 0**——3231 · 2383 · 6669 · 1319 · 3706 這些上市股都算成,**工作站庫有上市價**,Z155 只是容器的缺(已結)。目標價年齡:STALE_365 15 · FRESH_90 10 · AGING_180 8 · EXPIRED_OVER_1Y 6(描述性,不參與判燈) |
| V4 驗真矩陣 105 份 × 7 欄 | **判對率 100%**(461/461)· **可判率 62.7%**(461/735)、扣掉不適用 67.1%(461/687)。缺口:目標價 NODATA 58 · 上漲空間 67 · 評等 33 · 分析師 34 · 券商 15 · 報告日 8 |
| V4 第二顆頭(Z88) | 舊 `functional modules\VRN\output\vrn_reports.duckdb`(105 列 `vrn_report_basic`,最後寫於 09-20)仍在。容器掃了全部尾版:ENG083 只把它當候選之一;**ENG085 v0106 仍往這個舊路徑寫 `vrn_md_tables`**——封存後 ENG085 下一跑會在舊路徑重建一本只有表格的庫(那本沒有 `vrn_report_basic`,矩陣不再報第二顆頭);要不要讓 ENG085 改寫資料家那本,另裁 |
| V5 | 工作站 Python 3.13 每跑印三行 jieba 的 SyntaxWarning(第三方套件自己的原始碼跳脫,不是本樹);下一跑還在再處理 |

可判率 67.1% 的缺口是母線第一血統(ENG073 → ENG083)在 105 份真檔上的擷取覆蓋;第二血統在同一批真值上的成績見批728(評等 48/48 · 目標價 41/41),要不要回灌正本仍是 Z146。批729 的附錄與 ADJ 要等工作站真的拉到本分支、V6 跑完才有真數。

## 十一 · 工作站第二次回報(第二版一貼即用;還是沒拉到)

工作站**不在 main**:停在另一條線的分支 `claude/via-envmanager-governance-7cls8h`,HEAD `16524649`「解未完成合併(MergeMedic)」——**只在工作站本機**(任何遠端分支都沒有這一筆)。
樹上卡著一個衝突:六層冊 `VIA_VRN_LogicArchitecture_SSOT_v0100.json` 是 `UU`,另有五支再生物已暫存(M)。`git stash` 回「needs merge」、`git merge` 回「unmerged files」,第二版的守門照設計停下,**沒有在舊碼上又跑一輪**。
`via-regen --apply` 倒回了 4 支再生物(備份 `VIA_Reports\regen_revert\20260924_154511`)。
看樣子是「合併完再放回暫存(stash pop)」時撞到六層冊;這種卡法**沒有 MERGE_HEAD**,單用 `git merge --abort` 解不開——第三版一貼即用兩種卡法都處理,並加 `git reflog` 三行,下次看得出是誰讓它卡住。

