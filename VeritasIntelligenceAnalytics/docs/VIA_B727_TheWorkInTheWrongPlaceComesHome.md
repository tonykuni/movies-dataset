# 批727 · 錯位置的成果搬回正位 · VRN 重整實測 · SSOT 冊同步自動相互更新檢查 · 2026-09-23

> 操作員令(原文):「讀取 session_019RDuSz… 他在錯誤位置進行的成果 · session_01RLMQGZ… 的數次趨近於成功的經驗 ·
> 讀取 VCGC 的相關工具 SSOT REGEX 同步自動相互更新檢查 · 重整 VRN 實測修正到成功 · 實測資料 <OneDrive 分享夾>」,
> 隨後補一句 `https://github.com/tonykuni/movies-dataset`——**正位是母倉**。
> 沿用令:「"C:\測試樣本報告" 實測實修正直到成功」「py 指令都要加入加速器;ps 指令都要加入 25 個加速器;動態進度條不卡斷、動態百分比」。

## 一 · 讀出來的三件事

| 來源 | 讀到什麼 |
|---|---|
| session_019RDuSz(「VRN系統啟動處理」)→ 姊妹倉 `tonykuni/VIA-VDF-VRN` 分支 `claude/festive-ptolemy-ts2yyh` | PR #23 併進姊妹倉 main 之後又推了兩筆:**41ce6d4**「real-report loop reaches zero FAIL」與 **34d91ac**「Windows run shows per-file progress」。在操作員 OneDrive 的 **106 份實檔**上,自測迴圈第一輪 RED(PASS 125 · WARN 79 · FAIL 23),收斂到 **AMBER · PASS 260 · WARN 9 · FAIL 0**;人工真值表上兩支引擎的關鍵欄全對(券商 105/105 · 評等 48/48 · 目標價 41/41 · 現價 45/45)。同一份真值上母倉正本 ENG086(經 SUP_MDL749)只有 評等 23/48 · 目標價 31/41 · 券商 58/60。**這些成果全在姊妹倉——錯位置。** 該 session 掛的 artifact「VRN 全景實測」是 09-14 的舊探針頁(64 件全卡在 S02 無位元組),不是 09-23 的實檔結果 |
| session_01RLMQGZ(「VIA Integration」)→ 母倉側線 `claude/via-envmanager-governance-7cls8h` | 批695–726 已由 PR #72/#76–#91 併進 main。趨近成功的經驗:兩次成功(批628/634 規則正本 64 份真研報 · 批678 同義字聯集)各有七條標準(點名正本 · 操作員原文逐字 · 鄰近鎖 · cross_check · 多態欄 · 不抄第二份 · 拒收留因由);**真料打得出探針打不出的洞**(81 份真首頁打出四個洞);**分母要一起講**(電郵錨 78.3%/每錨,但只有 50.6% 的報告有電郵);**先看尾版再改**(批725 改到 ENG068 v0103 而尾版是 v0106);**先問 vcgc status 再 grep**(批726)|
| 母倉現況(main 0b457a85) | 13 支姊妹倉件早在 PR #70(bee8a683)以 **965504f 的版本**進母倉 `functional modules/VRN/engine|tests`,批702 在上面清了陸券;**41ce6d4 / 34d91ac 那兩筆從來沒進母倉**。main 上這一夾的 pytest **連收集都過不了**(名冊 `src/lib/via/incoming-roster.ts` 在姊妹倉根) |

## 二 · 搬回正位:VRN 第二血統(姊妹倉 34d91ac → 母倉)

**三方合併**:base = 姊妹倉 965504f(PR #70 帶進來的那一版)· ours = 母倉現況(含批702 陸券清除、NET-BRIDGE)· theirs = 姊妹倉 34d91ac。三支引擎 **0 衝突**、合併後三直譯器 ast 全過;批702 的清除與 NET-BRIDGE 都留著。新件 `VRN_Evidence_Core.py`(1800 行,規格 v0.2.0 §7「一套證據規則給兩支引擎」)與其測試原樣進來後再修。

母倉在其上另修(**母倉的法**,姊妹倉沒有):

| 件 | 修什麼 | 為什麼 |
|---|---|---|
| `VRN_Evidence_Core.py` v0101 | ① 拒絕清單**一本**:`deny_phrases()` = 疊加層 `deny_keys`(操作員批413/679;母倉閘的正本)∪ CGC_MDL177;② `broker_evidence` 改成**一場最長者勝的比賽**(被拒名與合法別名一起比長短,批681 律);③ `deny_shadowed()` / `is_denied_token()` 給兩支引擎共用;④ 不再把兩個陸券 CJK 名寫在 `GENERIC_BROKER_ALIASES`(改從 CGC_MDL177 讀) | 實測漏洞:「本報告由**摩通**研究部出具」→ JPM(操作員批413「去摩通」);「**中信**證券研究部」的「中信」被 CTBC 接走(批681 那個坑);CGC_MDL177 verify 把寫出來的陸券名當活資料(rc1) |
| `VIA_VRN_FirstPageEngine.py` / `VRN_Integrated_ReportDatabase_Engine.py` | 別名比對每一個命中先問 `deny_shadowed`(檔名層也守);證據核心以**獨名** `vrn_engine_evidence_core` 載入、只認同夾那一支 | 母倉另有一支舊的 `VRN_Evidence_Core.py`(收容夾 v0.2.0 包);同一行程裡有人 `import VRN_Evidence_Core` 就會被接錯 |
| `VRN_AutoTestLoop.py` v0102 | G03 期望值認拒絕清單(稽核包 oracle 的 broker=GF 在母倉期望空);**G10 母倉模式**(v0101 在母倉整段 SKIP——連拒絕清單都沒驗;現在工具讀正本、三支自測、整本拒絕清單 × 頁面層 + 檔名層、負控 +摩根士丹利/摩根大通/中信投顧、同義字對帳);名冊讀收容副本(母倉沒有 `src/lib/via/`);每檔印 `[進度] k/K`(三批合一條 0→100%);`--selftest` 門(VRN/tests 全部單元測試 + 合成 8 檔一輪) | 母倉法 · 批694 進度協定 · 六層鏈與格子要有門可敲 |
| `VRN_PanoramaProbe.py` v0101 | APP_ROOT:倉根沒有 app 就用收容夾 `VIA_GrokConsole_AuroraAcorn_b383`(名冊位元相同、十段表相同);SSOT 冊先找活冊 `VRN/knowledge|SSOT` | main 上 2 支測試因此紅 |
| 測試 | GF oracle 兩支測試認拒絕清單;+`test_one_deny_gate_longest_wins`;+`test_engines_ignore_a_foreign_module_named_like_the_core`(對舊載入器必紅,已證) | |

**結果(容器)**:VRN/tests **64/64**(main 上是收集錯誤);自測迴圈合成語料 107 檔 **AMBER · PASS 358 · WARN 1 · SKIP 0 · FAIL 0**(WARN=926708.jpg 要 OCR,未接);G10 母倉模式全 PASS(CGC_MDL181 5/5 · CGC_MDL182 18/18 · CGC_MDL177 43/43 · 拒絕清單 37 名兩層不漏 · 負控 7 條照解 · 券商同義字 SAME 149 / SISTER_ONLY 44 · 評等 SAME 31 / SISTER_ONLY 26,零衝突);CGC_MDL177 verify **rc0**。

**沒搬的**(刻意):姊妹倉 `supportive modules/**` 鏡像(母倉是源頭;照抄會把 PR #75 的 VRN_FieldRules 倒回去)、`DELIVERY_MANIFEST.json`、姊妹倉 `knowledge/SYNONYM_LIBRARY_v3/v4`(會把陸券帶回來)、`scripts/VIA_VCGC_Sync.py`(姊妹倉那一側的工具;母倉這一側由 CGC_MDL184 對稱量)。`functional modules/VRN/Invoke-VRN-AutoTest.ps1` **一字未動**(改 .ps1 要逐次許可;母倉入口改走 via-vrnrun 第六步)。

## 三 · SSOT 冊同步自動相互更新檢查(兩支新工具)

**CGC_MDL184 SisterMirrorSync v0100**(母倉 ↔ 姊妹倉,唯讀):
- ① VCGC 鏡像新鮮度:讀姊妹倉 `DELIVERY_MANIFEST.json`,逐條對母倉尾版 → SAME / SAME_EOL / NEW_VERSION / CHANGED / GONE_IN_MOTHER。**實測(姊妹倉 34d91ac)**:6 SAME · `VRN_FieldRules_SSOT` CHANGED(PR #75 券商來源法)· SUP_MDL749 NEW_VERSION(鏡像 v0112,母倉已到 **v0114**)→ YELLOW,指路「在姊妹倉跑 VIA_VCGC_Sync --apply」。
- ② 第二血統同步:同步冊 `VIA_VRN_SisterLineage_Sync_v0100.json` 記下本批兩邊 12 檔的 LF 指紋;之後逐檔 IN_SYNC / SISTER_AHEAD / MOTHER_AHEAD / BOTH_CHANGED / MISSING。
- 十九檢(沙盒兩棵假樹;CRLF 不算內容;`--ref` 讀 git 不動工作樹;唯讀/零網路/同意閘)。

**CGC_MDL185 SsotBookSync v0100**(母倉內六條邊,唯讀,每一條都委派正主):

| 邊 | 批727 前 | 批727 後 | 誰修的 |
|---|---|---|---|
| E1 RegexDict 普查新鮮度 | STALE(樣式 1269→1340)| **FRESH** | CGC_MDL115 run(冊在刻意入倉名單) |
| E2 SynonymUnion 聯集冊新鮮度 | STALE(09-21 那一次;gate_bypass 10 支 vs 活的 37 支)| **FRESH** | CGC_MDL176 plan --apply(641 條對映零增零減,只刷新閘況) |
| E3 拒絕清單逐解析器 | **LEAK**:SUP_MDL749 增補冊讀冊口 16 名解得出(陸券英文名、中金、海通…)| **HOLDS**(6 支解析器全守,負控照解) | **SUP_MDL749 v0114** +㊽(同一個閘:ENG086 `_gate176` ∪ CGC_MDL177;名單零字面)· 第二血統 v0101 |
| E4 兩本網域冊 | NONCANONICAL · SPELLING 2 | 同(**候裁**) | — |
| E5 同名冊副本 | DIVERGED(SYNONYM_LIBRARY 2/5 · Rating_Dict 4/5 · Broker_Dict 4/5)| 同(**候裁**) | — |
| E6 四本台股代號 regex 冊 | DISAGREE(0050 / 00878 / 00981A / 2026 等探針判法不同)| 同(**候裁**:各冊範疇本來就是不同的操作員裁定) | — |

總判由 **RED → YELLOW(rc0)**。「自動」的意思:STALE 的邊會印出正主那一支的重生指令;寫不寫是批次/操作員的手,本支永遠不寫冊。二十八檢。

## 四 · via-vrnrun 第六步(`Invoke-VIA-VRN-v0103.ps1`)

- **V6 VRN 實檔自測迴圈(12 閘)**:樣本預設 `C:\測試樣本報告`;夾不在就跑合成語料並**講明不是實測**;`-Truth` 給人工真值檔才開 G11;落點 `VIA_Reports\vrn_autotest\<時間>`(不入 git);經 `Invoke-VIAPython`(25 加速器)跑,迴圈的 `[進度] k/K` 驅動第六步的真百分比。容器實測:`VIA_PYPROG_LAST n=321 d=321 pct=100`。`-NoAutoTest` 只跑前五步。
- **L102 Celeritas 模板**:AI 產出的 .ps1 一律接模板——本支以**模組範圍**接(模板的嚴格模式與 `$script:` 狀態關在裡面,不外溢到前五步)。**實測模板本身接不上**:`VeritasCeleritas.PS7.ps1` 第 24 行在嚴格模式下讀未設的 `$script:CeleritasPS7`、第 83 行讀未設的 `$OFS`,**第一次載入就炸**(容器 pwsh 7.4;沒有任何一站驗過它)。兩行修法在沙盒副本驗過:接上、不外溢、優先權 AboveNormal、收尾還原 Normal。**修它是改 .ps1(L70)→ 掉球 Z120 候許可**;修好之前本支照實印「模板未接(原因)」,不擋跑。
- V2 標籤不再寫死「44 節點」(冊現在 45)。L70 許可:操作員本輪「重整 VRN 實測修正到成功」+ 沿用令;新版號檔,刪檔即回退,v0102 一字未動。

## 五 · 六層冊 +1 節點(`via_vrn_logic_book_v0107`)

L3_驗證 +`functional modules/VRN/engine/VRN_AutoTestLoop.py`(門 = `--selftest`)。六層鏈(CGC_MDL172)敲這一個節點就把整條第二血統驗一遍。冊重建時順便把**批707 的再生物還原倒回去的舊冊**拉回來:側線批707 跑 `via-regen --apply`,把本冊還原成 v0101/批641 的舊樣(`off_book_pending` 的 ENG088 待裁定、built_by/version 全掉了);v0107 build 後回到 v0107 · 45 指標 · ENG088 待裁定在位。十七檢 17/17。

## 六 · 誠實燈:CGC_MDL181 v0101

庫在(開機掛件先落了 11 張 VDF 表)但 `vrn_report_basic` 不在時,v0100 直接 `select count(*)` → CatalogException 整支炸(rc1);庫缺席回 rc3 而格子站期望 rc0。v0101:先 `show tables`,表不在 = NODATA 逐欄照列並指路 · 庫缺/表不在都是缺料 rc2(批693B 同律);格子站期望改 nodata_ok。六檢。

## 七 · 沒做到的(照實講)

- **OneDrive 實測資料抓不下來**:分享頁對非瀏覽器回 403、舊 API 要登入;要拿匿名權杖才讀得到,被本環境的自動許可分類器以「憑證探查」擋下——**我不繞**。容器只能跑合成語料;實檔實測在工作站(`C:\測試樣本報告`,via-vrnrun 第六步)。三條路見掉球 Z124。
- **券商來源法三方打架**(Z121):PR #75(操作員 09-21 裁定:檔名 → 第一頁左右區;電郵網域只算弱證)vs 第二血統證據核心(電郵 > 揭露 > 發行人 > 抬頭 > 本文)vs CGC_MDL182(網域定券商)。本批**不裁**,三條並存照實列。
- **儲存法**(Z122):第二血統資料庫引擎說「Parquet 是唯一主庫」,母倉批615 裁定正典是 DuckDB、Parquet 只是派生。
- 母倉正本 ENG086 在同一份真值上落後(評等 23/48 · 目標價 31/41);要不要把證據核心的規則回灌正本 = 操作員裁(Z127)。
- E4/E5/E6 三條黃邊(Z123)、姊妹倉鏡像落後與姊妹倉自己合成語料 GF 的紅(Z125)、格子裡 SUP_MDL749 站登兩次(Z126)。

## 八 · 全格子 v0475(容器;PATH 帶 /opt/pwsh)

站 +4:VRN 第二血統總驗 · 母倉↔姊妹倉同步十九檢 · SSOT 冊同步自測 · SSOT 冊同步實跑;站名兩處改(SUP_MDL749 五十檢 · CGC_MDL181 六檢,實跑 nodata_ok)。結果見本批 commit 訊息與台帳。

## 九 · 工作站(一貼即用)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git pull origin claude/awesome-bardeen-h0wm5v
git log --oneline -1
via-vrnrun 2>&1 | Tee-Object -FilePath "$env:TEMP\vrnrun_b727.txt"
Select-String -Path "$env:TEMP\vrnrun_b727.txt" -Pattern '\[Celeritas\]|\[加速器\]|\[進度\] \d+/6|\[V[1-6]\]|\[ROUND|\[DONE\]|FAIL G|WARN G|RED|\[計\]|判對率|可判率|rc=' | ForEach-Object { $_.Line }
Invoke-VIAPython -Python (Get-VIAEnvPython "vrn") "supportive modules\registry\CGC_MDL185_SsotBookSync_v0100.py" check
```

要貼回:`git log` 一行 · `[Celeritas]` 一行 · `[進度] k/6` 六行 · V6 的 `[ROUND …] PASS= WARN= SKIP= FAIL=` 與 `[DONE]` 行 · 任何 `FAIL G..` / `WARN G..` 行 · CGC_MDL185 最後的 `[計]` 行。
有人工真值檔(例如 `C:\VRN_Truth\real_truth.json`)就加 `via-vrnrun -Truth <路徑>`,G11 才會開。
