# 批728 · 錯位置的成果搬回正位 · VRN 重整實測 · SSOT 冊同步自動相互更新檢查 · 2026-09-23

> 操作員令(原文):「讀取 session_019RDuSz… 他在錯誤位置進行的成果 · session_01RLMQGZ… 的數次趨近於成功的經驗 ·
> 讀取 VCGC 的相關工具 SSOT REGEX 同步自動相互更新檢查 · 重整 VRN 實測修正到成功 · 實測資料 <OneDrive 分享夾>」,
> 隨後補一句 `https://github.com/tonykuni/movies-dataset`——**正位是母倉**。
> 沿用令:「"C:\測試樣本報告" 實測實修正直到成功」「py 指令都要加入加速器;ps 指令都要加入 25 個加速器;動態進度條不卡斷、動態百分比」。

## 一 · 讀出來的三件事

| 來源 | 讀到什麼 |
|---|---|
| session_019RDuSz(「VRN系統啟動處理」)→ 姊妹倉 `tonykuni/VIA-VDF-VRN` 分支 `claude/festive-ptolemy-ts2yyh` | PR #23 併進姊妹倉 main 之後又推了兩筆:**41ce6d4**「real-report loop reaches zero FAIL」與 **34d91ac**「Windows run shows per-file progress」。在操作員 OneDrive 的 **106 份實檔**上,自測迴圈第一輪 RED(PASS 125 · WARN 79 · FAIL 23),收斂到 **AMBER · PASS 260 · WARN 9 · FAIL 0**;人工真值表上兩支引擎的關鍵欄全對(券商 105/105 · 評等 48/48 · 目標價 41/41 · 現價 45/45)。同一份真值上母倉正本 ENG086(經 SUP_MDL749)只有 評等 23/48 · 目標價 31/41 · 券商 58/60。**這些成果全在姊妹倉——錯位置。** 該 session 掛的 artifact「VRN 全景實測」是 09-14 的舊探針頁(64 件全卡在 S02 無位元組),不是 09-23 的實檔結果 |
| session_01RLMQGZ(「VIA Integration」)→ 母倉側線 `claude/via-envmanager-governance-7cls8h` | 批695–726 已由 PR #72/#76–#91 併進 main。趨近成功的經驗:兩次成功(批628/634 規則正本 64 份真研報 · 批678 同義字聯集)各有七條標準(點名正本 · 操作員原文逐字 · 鄰近鎖 · cross_check · 多態欄 · 不抄第二份 · 拒收留因由);**真料打得出探針打不出的洞**(81 份真首頁打出四個洞);**分母要一起講**(電郵錨 78.3%/每錨,但只有 50.6% 的報告有電郵);**先看尾版再改**(批725 改到 ENG068 v0103 而尾版是 v0106);**先問 vcgc status 再 grep**(批726)|
| 母倉現況(main 0b457a85;本批進行中 main 又前進到 6f89390d,見四) | 13 支姊妹倉件早在 PR #70(bee8a683)以 **965504f 的版本**進母倉 `functional modules/VRN/engine|tests`,批702 在上面清了陸券;**41ce6d4 / 34d91ac 那兩筆從來沒進母倉**。main 上這一夾的 pytest **連收集都過不了**(名冊 `src/lib/via/incoming-roster.ts` 在姊妹倉根) |

## 二 · 搬回正位:VRN 第二血統(姊妹倉 34d91ac → 母倉)

**三方合併**:base = 姊妹倉 965504f(PR #70 帶進來的那一版)· ours = 母倉現況(含批702 陸券清除、NET-BRIDGE)· theirs = 姊妹倉 34d91ac。三支引擎 **0 衝突**、合併後三直譯器 ast 全過;批702 的清除與 NET-BRIDGE 都留著。新件 `VRN_Evidence_Core.py`(1800 行,規格 v0.2.0 §7「一套證據規則給兩支引擎」)與其測試原樣進來後再修。

母倉在其上另修(**母倉的法**,姊妹倉沒有):

| 件 | 修什麼 | 為什麼 |
|---|---|---|
| `VRN_Evidence_Core.py` v0101 | ① 拒絕清單**一本**:`deny_phrases()` = 疊加層 `deny_keys`(操作員批413/679;母倉閘的正本)∪ CGC_MDL177;② `broker_evidence` 改成**一場最長者勝的比賽**(被拒名與合法別名一起比長短,批681 律);③ `deny_shadowed()` / `is_denied_token()` 給兩支引擎共用;④ 不再把兩個陸券 CJK 名寫在 `GENERIC_BROKER_ALIASES`(改從 CGC_MDL177 讀) | 實測漏洞:「本報告由**摩通**研究部出具」→ JPM(操作員批413「去摩通」);「**中信**證券研究部」的「中信」被 CTBC 接走(批681 那個坑);CGC_MDL177 verify 把寫出來的陸券名當活資料(rc1) |
| `VIA_VRN_FirstPageEngine.py` / `VRN_Integrated_ReportDatabase_Engine.py` | 別名比對每一個命中先問 `deny_shadowed`(檔名層也守);證據核心以**獨名** `vrn_engine_evidence_core` 載入、只認同夾那一支 | 母倉另有一支舊的 `VRN_Evidence_Core.py`(收容夾 v0.2.0 包);同一行程裡有人 `import VRN_Evidence_Core` 就會被接錯 |
| `VRN_AutoTestLoop.py` v0102 | G03 期望值認拒絕清單(稽核包 oracle 的 broker=GF 在母倉期望空);**G10 母倉模式**(v0101 在母倉整段 SKIP——連拒絕清單都沒驗;現在工具讀正本、三支自測、整本拒絕清單 × 頁面層 + 檔名層、負控 +摩根士丹利/摩根大通/中信投顧、同義字對帳);名冊讀收容副本(母倉沒有 `src/lib/via/`);每檔印 `[進度] k/K`(三批合一條 0→100%);`--selftest` 門(VRN/tests 全部單元測試 + 合成 8 檔一輪) | 母倉法 · 批694 進度協定 · 六層鏈與格子要有門可敲 |
| `VRN_PanoramaProbe.py` v0101 | APP_ROOT:倉根沒有 app 就用收容夾 `VIA_GrokConsole_AuroraAcorn_b383`(名冊位元相同、十段表相同);SSOT 冊先找活冊 `VRN/knowledge|SSOT` | main 上 2 支測試因此紅 |
| 測試 | GF oracle 兩支測試認拒絕清單;+`test_one_deny_gate_longest_wins`;+`test_engines_ignore_a_foreign_module_named_like_the_core`(對舊載入器必紅,已證);PR #75 的 `test_broker_source_zones.py` 補加速器橋(正主注入器;掉球 Z138 結) | |

**結果(容器,併線後重量)**:VRN/tests **64/64**(main 上是收集錯誤);`VRN_AutoTestLoop --selftest` 2/2(64 支單元測試 + 合成 8 檔一輪 FAIL 0);自測迴圈合成語料 107 檔 **AMBER · PASS 358 · WARN 1 · SKIP 0 · FAIL 0**(WARN=926708.jpg 要 OCR,未接);G10 母倉模式全 PASS(拒絕清單 37 名兩層不漏 · 負控 7 條照解 · 券商同義字 SAME 149 / SISTER_ONLY 44 · 評等 SAME 31 / SISTER_ONLY 26,零衝突);CGC_MDL177 verify **rc0**。

**沒搬的**(刻意):姊妹倉 `supportive modules/**` 鏡像(母倉是源頭;照抄會把 PR #75 的 VRN_FieldRules 倒回去)、`DELIVERY_MANIFEST.json`、姊妹倉 `knowledge/SYNONYM_LIBRARY_v3/v4`(會把陸券帶回來)、`scripts/VIA_VCGC_Sync.py`(姊妹倉那一側的工具;母倉這一側由 CGC_MDL184 對稱量)。`functional modules/VRN/Invoke-VRN-AutoTest.ps1` **一字未動**(改 .ps1 要逐次許可;母倉入口改走 via-vrnrun 第六步)。

## 三 · SSOT 冊同步自動相互更新檢查:一道門,門後一支正主

**`via-vcgc ssot` 就是那道門**(側線 2026-09-23 在 VCGC v0126 開的第四扇門:check → plan → plan -Apply → verify,逐格委派正主)。本批把門後缺的四格補上(VCGC **v0128** 門 ⑥,正主 **CGC_MDL185**),另立 CGC_MDL184 量母倉 ↔ 姊妹倉。

**門 ⑥ 冊同步(CGC_MDL185 SsotBookSync v0100;唯讀、每一格委派正主、正主自己點燈、門只翻譯)**:

| 格 | 批728 前 | 批728 後 | 誰修的 |
|---|---|---|---|
| booksync.deny 拒絕清單 × 每一個券商解析器 | **LEAK**:SUP_MDL749 增補冊讀冊口 16 名解得出(陸券英文名、中金、海通…);第二血統「摩通」→ JPM | **HOLDS**:37 名 × 6 支解析器全守,負控照解 | **SUP_MDL749 v0114** +㊽(同一個閘:ENG086 `_gate176` ∪ CGC_MDL177;名單零字面)· 第二血統 v0101 |
| booksync.domains 兩本網域冊 | NONCANONICAL 1 · SPELLING 2 | 同(**候裁 Z143**) | — |
| booksync.copies 同名冊副本 | DIVERGED(SYNONYM_LIBRARY 2/5 · Rating_Dict 4/5 · Broker_Dict 4/5)| 同(**候裁 Z143**) | — |
| booksync.ticker 四本台股代號 regex 冊 | DISAGREE(0050 / 00878 / 00981A)| 同(**候裁 Z143**:各冊範疇本來就是不同的操作員裁定) | — |

門的其餘九格(側線 v0126 已委派)本批的變化:③ union.missing **缺 0 條**(本線第一筆 CGC_MDL176 `plan --apply`,641 條零增零減只刷新閘況);⑤ regexdict.book 收尾鏈交正主 **CGC_MDL115 v0101** 重建(樣式 1346 · 共用 710 · 編不過 0 · python 3.11);hub.* 四格改由 SUP_MDL749 **v0114** 答(尾版律自動換)。

`via-vcgc ssot` 實量:**YELLOW · 13 格 · GREEN 6 · YELLOW 7 · 紅 0**(黃 = 待操作員裁定;`ssot plan` 逐條列)。

**CGC_MDL184 SisterMirrorSync v0100**(母倉 ↔ 姊妹倉,唯讀):
- ① VCGC 鏡像新鮮度:讀姊妹倉 `DELIVERY_MANIFEST.json`,逐條對母倉尾版 → SAME / SAME_EOL / NEW_VERSION / CHANGED / GONE_IN_MOTHER。**實測(姊妹倉 34d91ac)**:5 SAME · CGC_MDL181 NEW_VERSION(母倉 v0101)· `VRN_FieldRules_SSOT` CHANGED(PR #75 券商來源法)· SUP_MDL749 NEW_VERSION(鏡像 v0112,母倉 **v0114**)→ YELLOW,指路「在姊妹倉跑 VIA_VCGC_Sync --apply」(Z145)。
- ② 第二血統同步:同步冊 `VIA_VRN_SisterLineage_Sync_v0100.json` 記下本批兩邊 12 檔的 LF 指紋;之後逐檔 IN_SYNC / SISTER_AHEAD / MOTHER_AHEAD / BOTH_CHANGED / MISSING。併線後實量 **GREEN**。
- 十九檢(沙盒兩棵假樹;CRLF 不算內容;`--ref` 讀 git 不動工作樹;唯讀/零網路/同意閘)。

## 四 · 併線:同一天兩條線各長一支「SSOT 冊同步檢」

本批做到一半,main 從 0b457a85 前進到 **6f89390d**(PR #92,側線 2026-09-23:VDF 三支治理版 · VCGC v0126/v0127 ssot 門 · 格子 v0475/v0476)。**兩條線同一天回應了同一句操作員令**,也撞了號(LL334):

| 撞到的 | 怎麼收 |
|---|---|
| 格子 v0475(兩線都出) | 本線改以 main 的 **v0476 為底**(先出 v0477;第二輪又撞,最後是 v0478,見下表);側線各版的站一字不動 |
| 掉球 Z120 起號(兩線都從 Z120 起) | main 的 Z120–Z138 原號不動;本線 Celeritas 實證併進 **Z137**(容器 pwsh 7.4:第 24 行與第 83 行都要改);本線「格子重複站」即 **Z132**;**Z138**(PR #75 測試缺加速器橋)本線第一筆已補 → 已結;其餘本線條目改號 **Z141–Z146** |
| 冊同步檢兩處量同一件事(Zero-Hydra L05 / LL316) | CGC_MDL185 第一版有六條邊,其中「RegexDict 普查新鮮度」與「聯集冊新鮮度」門的 ⑤ ③ 早就委派同兩支正主,而且 ⑤ 有 python 版本只升不降的護欄(本線那條沒有:容器 3.11 與工作站 3.13 會來回覆寫)→ **拿掉這兩條**,剩下四條沒有任何一支量過的,掛成門 ⑥(VCGC v0128 +㊲)。格子不另立 CGC_MDL185 實跑站——側線那三站(ssot · ssot plan · ssot verify)就是它的實跑 |

做法:本線工作先 commit(那一筆的訊息還寫著「批727(一)」——撞號是之後才量到的,歷史照實留),再 `git merge` main(不 rebase、不 force-push);三本生成冊取 main 再由正主重生(registry-sync · CGC_MDL115 v0101 · manager),掉球冊手併。

**推之前再查所有分支,又撞了兩處(同一天第三、四條線)**:

| 撞到的 | 誰先推 | 本線改成 |
|---|---|---|
| 批727 | VIA Integration 線 `claude/via-envmanager-governance-7cls8h` 4cdb368e(22:27「批727:我量的那條式子,不是跑的那條」;ENG086 v0116) | **批728**(本文檔名、各引擎版史、台帳一律改;本線前兩筆 commit 訊息裡的「批727」照實留在歷史,不改寫) |
| 格子 v0477 · 掉球 Z139–Z140 | VDF 側線第三段 `claude/busy-bell-97sa4f` ae13939b(22:47「一個指令開 VDF」;VDF_ENG093) | 格子 **v0478 = main v0476 + 側線 v0477 的兩站 + 本線三站**(哪條先併,尾版格子都不掉站;側線兩站在本樹 SKIP「引擎缺」直到它併進來)· 掉球 **Z141–Z146** |

兩線都還沒併進 main,本線不把它們的工作帶進來(不是本線的範圍);只做兩件讓之後併線不打架的事:
- `test_broker_source_zones.py` 的加速器橋,VIA Integration 線也補了同一塊,只差檔頭說明後一個空行——本線補上那個空行,兩邊**逐位元相同**,誰後併都不會衝突。
- ENG086 v0116 對 v0115 只改了目標價線索 `_TP_CUES` 與 `main` / `selftest`(模組層逐項比過);本線 SUP_MDL749 v0114 用到的 `_gate176` / `safe_broker_ev` / `broker_gate_state` / `_is_upside_context` 一字未動,樹上也沒有別支讀 `_TP_CUES`——併進來相容。

兩個本批自己犯、格子抓到的錯(照實記):
- VCGC v0128 ㊲ 第一版把假正主寫成 class 裡的 `def check` → 本台 `source_guard()` 以函數名索引(連巢狀定義一起收),拿假正主蓋掉了本台的 `check()`,⑳ 當場紅;改成 SimpleNamespace 包一支另取名的函數。
- 收尾鏈第一次重建正則清冊用了 `CGC_MDL115_SSOTRegexDict_v*.py` 萬用字元——展開成 v0100 與 v0101 兩支,跑的是**舊的 v0100**(樣式 1526 · 共用 792)。改用尾版 v0101 重跑(1346 · 710)覆蓋。

## 五 · via-vrnrun 第六步(`Invoke-VIA-VRN-v0103.ps1`)

- **V6 VRN 實檔自測迴圈(12 閘)**:樣本預設 `C:\測試樣本報告`;夾不在就跑合成語料並**講明不是實測**;`-Truth` 給人工真值檔才開 G11;落點 `VIA_Reports\vrn_autotest\<時間>`(不入 git);經 `Invoke-VIAPython`(25 加速器)跑,迴圈的 `[進度] k/K` 驅動第六步的真百分比。容器實測:`VIA_PYPROG_LAST n=321 d=321 pct=100`。`-NoAutoTest` 只跑前五步。
- **L102 Celeritas 模板**:AI 產出的 .ps1 一律接模板——本支以**模組範圍**接(模板的嚴格模式與 `$script:` 狀態關在裡面,不外溢到前五步;同側線 Invoke v0105 的「不包裹」接法)。**實測正主接不上**:`VeritasCeleritas.PS7.ps1` 第 24 行在嚴格模式下讀未設的 `$script:CeleritasPS7`,第一次載入就炸;第 24 行改掉後,第 83 行 `OFS = $OFS` 也炸(容器 pwsh 7.4;格子沒有任何一站驗過它)。兩行修法在沙盒副本驗過:接上、不外溢、優先權 AboveNormal、收尾還原。**修它是改 .ps1(L70)→ 掉球 Z137 候許可**;修好之前本支照實印「模板未接(原因)」,不擋跑。
- V2 標籤不再寫死「44 節點」(冊現在 45)。L70 許可:操作員本輪「重整 VRN 實測修正到成功」+ 沿用令;新版號檔,刪檔即回退,v0102 一字未動。

## 六 · 六層冊 +1 節點(`via_vrn_logic_book_v0107`)

L3_驗證 +`functional modules/VRN/engine/VRN_AutoTestLoop.py`(門 = `--selftest`)。六層鏈(CGC_MDL172)敲這一個節點就把整條第二血統驗一遍。冊重建時順便把**批707 的再生物還原倒回去的舊冊**拉回來:側線批707 跑 `via-regen --apply`,把本冊還原成 v0101/批641 的舊樣(`off_book_pending` 的 ENG088 待裁定、built_by/version 全掉了);v0107 build 後回到 v0107 · 45 指標 · ENG088 待裁定在位。十七檢 17/17。

## 七 · 誠實燈:CGC_MDL181 v0101 · VAP_ENG014 v0102 · CGC_MDL119 v0105

- **CGC_MDL181**:庫在(開機掛件先落了 VDF 表)但 `vrn_report_basic` 不在時,v0100 直接 `select count(*)` → CatalogException 整支炸(rc1);庫缺席回 rc3 而格子站期望 rc0。v0101:先 `show tables`,表不在 = NODATA 逐欄照列並指路 · 庫缺/表不在都是缺料 rc2(批693B 同律);格子站期望改 nodata_ok。**第一版只改了 measure()**,render() 還只認量過的形狀,一讀 `n_reports` 就 KeyError——全格子「研報欄位規格實跑」咬到(自測 ⑥ 只驗 measure 所以綠);render 補 NODATA 分支,⑥ 改成連 render 一起驗。六檢。
- **VAP_ENG014 v0102**:就緒探針只看 `consensus_latest`,本境少 `monthly_revenue_analysis` 就整支 FAIL 6;改成真的呼叫 `gather()`,缺料=誠實模式。
- **CGC_MDL119 v0105**(操作員中途令「自測自修正再測再修正直到成功」):全格子 v0478 第一跑只剩一盞紅「系統 API 三態自測」,main 上也紅。量到的:容器庫有 16 張表,**沒有 `tw_listings_industry` 也沒有 `etf_book`**;正主 VAP_ENG013 v0105 自己的自測(批693)早就把「族群 0 組 / ETF 冊 0 檔」判成 NODATA,聚合層的 ④ ⑤ 還判 FAIL——同一件事兩把尺。改走三態:**缺料要正主講得出因由**(轉呈 VAP_ENG013 自己記下的 SQL 錯 `Table … does not exist` 與 etf_list 的 note),表都在而 0 組照舊 FAIL(工作站上那才是真的有事);+⑨ 合成件三態都咬;自測抬頭版號改從檔名推(v0104 還印 v0100)。十二檢 OK 9 · NODATA 3 · FAIL 0。

## 八 · 沒做到的(照實講)

- **OneDrive 實測資料抓不下來**:分享頁對非瀏覽器回 403、舊 API 要登入;要拿匿名權杖才讀得到,被本環境的自動許可分類器以「憑證探查」擋下——**我不繞**。容器只能跑合成語料;實檔實測在工作站(`C:\測試樣本報告`,via-vrnrun 第六步)。三條路見掉球 **Z144**。
- **券商來源法三方打架**(**Z141**):PR #75(操作員 09-21 裁定:檔名 → 第一頁左右區;電郵網域只算弱證)vs 第二血統證據核心(電郵 > 揭露 > 發行人 > 抬頭 > 本文)vs CGC_MDL182(網域定券商)。本批**不裁**,三條並存照實列。
- **儲存法**(**Z142**):第二血統資料庫引擎說「Parquet 是唯一主庫」,母倉批615 裁定正典是 DuckDB、Parquet 只是派生。
- 母倉正本 ENG086 在同一份真值上落後(評等 23/48 · 目標價 31/41);要不要把證據核心的規則回灌正本 = 操作員裁(**Z146**)。
- 門 ⑥ 三格黃(**Z143**)、姊妹倉鏡像落後與姊妹倉自己合成語料 GF 的紅(**Z145**)、格子裡 SUP_MDL749 站登兩次(**Z132**,刪站要操作員點頭)、Celeritas 正主兩行(**Z137**,L70)、再生物冊漏 ProductGate 那一條(**Z147**;冊以最後一跑重跑後入倉)。
- **明文 API 鑰(Z148,既有)**:產品資格閘的鑰匙守衛以指紋比對,已知的 FRED 鑰明文在 10 支受追蹤檔(上傳夾 9 支 + 收容夾 b716 一支),本批 diff 零命中。鑰已在 git 歷史裡,要先撤銷換新;遮罩檔案要動上傳夾與收容夾,等你點頭。

## 九 · 全格子 v0478(容器;PATH 帶 /opt/pwsh)

站 +3(側線 v0477 的 352 → 355;本樹 = main v0476 的 350 + 側線 v0477 兩站〔本樹 SKIP 引擎缺〕+ 本線三站):VRN 第二血統總驗 · 母倉↔姊妹倉同步十九檢 · SSOT 冊同步自測;站名改:VCGC 三十七檢 · ssot 三站敘述補門 ⑥ · SUP_MDL749 五十檢 · CGC_MDL181 六檢(實跑 nodata_ok)。

**三跑,最後一跑全綠。**

| 跑 | 內容 | OK | FAIL | SKIP | TIMEOUT |
|---|---|---|---|---|---|
| 一 | 本線 v0477 內容(改號前) | 339 | 1 | 6 | 0 |
| 二 | v0478 | 340 | 1 | 7 | 0 |
| 三 | v0478 + CGC_MDL119 v0105 | **341** | **0** | 7 | 0 |

一、二兩跑唯一的紅都是「系統 API 三態自測」(main 上同紅)。操作員中途令「自測自修正再測再修正直到成功」→ CGC_MDL119 v0105(見七)→ 第三跑 **FAIL 0**(793 秒;存證 `VIA_Reports/selftest_runs/GRID_20260923_232815.json`,不入 git)。平行段撞到單寫者庫的站,序跑複判全部轉綠。

SKIP 7 全是環境缺件,照實列:reconcile 對帳(沒有對帳報告)· 全景批次修復計畫實跑 · 三個專案打包就緒實跑 · 功能級整合驗收實跑(這三站 rc 是現況分類)· 格子自指佔位 · VDF 側線兩站(VDF_ENG093 在 busy-bell 分支,併進 main 前本樹沒有這支)。

## 十 · 工作站(一貼即用)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git pull --no-edit https://github.com/tonykuni/movies-dataset claude/awesome-bardeen-h0wm5v
git log --oneline -1
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-vcgc status 2>&1 | Select-Object -First 2
via-vcgc ssot
via-vrnrun 2>&1 | Tee-Object -FilePath "$env:TEMP\vrnrun_b727.txt"
Select-String -Path "$env:TEMP\vrnrun_b727.txt" -Pattern '\[Celeritas\]|\[加速器\]|\[進度\] \d+/6|\[V[1-6]\]|\[ROUND|\[DONE\]|FAIL G|WARN G|RED|\[計\]|判對率|可判率|rc=' | ForEach-Object { $_.Line }
```

要貼回:`git log` 一行 · `via-vcgc status` 第一行(要是 `[VCGC] v0128`)· `via-vcgc ssot` 第一行與任何 `[RED` 行 · `[Celeritas]` 一行 · `[進度] k/6` 六行 · V6 的 `[ROUND …] PASS= WARN= SKIP= FAIL=` 與 `[DONE]` 行 · 任何 `FAIL G..` / `WARN G..` 行。
pull 直接指 `https://github.com/tonykuni/movies-dataset`,不依賴本機 `origin` 指到哪。有人工真值檔(例如 `C:\VRN_Truth\real_truth.json`)就加 `via-vrnrun -Truth <路徑>`,G11 才會開。
