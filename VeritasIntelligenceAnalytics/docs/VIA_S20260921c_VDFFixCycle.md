# VIA 交接紀錄 · 側線 2026-09-21 c(branch `claude/busy-bell-97sa4f`;主線批號由併線的手指定 L25)

操作員令:「**檢視 VDF 現況 · 測試修正各引擎 · 實測 · 修正直到成功 · 全景式分析檢視 · 識別錯誤 · 避免傷害引擎跟系統 · 避免九頭龍風險 ·
可同時修正的錯誤同時修,不能的順序修 · TEST DEBUG OPTIMIZE / CONSOLIDATE / USER-TEST / ACTIVATE · TILL IT WORKS PERFECTLY ·
與總管系統 SSOT REGEX 同義字:上傳更新只增不減不衝突,整合好**」

〇 接手提示詞 → docs/VIA_AI_Handover_Prompt_v*.md(尾版)。本批接手驗收在八、貼行在九。前一批(b)在 `VIA_S20260921b_VDFSystemManager.md`。

## 一 · 律(本批沒有新律;用到的逐條註明)

L04 尾版律(每一支修正都是新版號檔,舊版留作版史)· L05/L30 Zero-Hydra(尺只有一把;抄到函式才算出處 LL316)· L07/L08/L09(不設閘、不裝套件、不觸網)·
L16 誠實四態(0 綠 / 1 紅 / 2 NODATA / 3 ABSENT / 4 GATED)· L57 誠實分母(SKIP 不是綠、不進分母)· L61/LL331 先量再造 · L70(.ps1 一字不動)·
LL49(容器再生冊不入 git,總控頁例外)· LL133(判定器排掉自己的家族)· 批686「ModuleNotFoundError → ABSENT 具名套件」。

## 二 · 先量:全景(容器,零網路,同意閘未開)

| 面 | 量到什麼 | 結論 |
|---|---|---|
| 全格子 289 站(Grid v0438) | **FAIL 82 · SKIP 8**,其餘 OK | 82 站的紅逐站讀:~60 站只有一個根因——**pandas / duckdb / fitz / pyarrow / rich 不在本境**,每支引擎各自把它寫成 FAIL(ModuleNotFoundError 直接炸、或自己印 `[FAIL] duckdb 缺`)。這不是引擎壞,是**尺把「境缺」當「壞掉」** |
| VDF 獨立鏈(CGC_MDL170 v0101 run) | GREEN 6 · **RED 1** · GATED 1 · NODATA 2 → RED | 第 2 站 ENG073 因 `import duckdb` rc=1 判 RED,3a/3b 同一根因卻是 NODATA——同一件事兩種燈 |
| 匯流排 test profile · vdf 家族 66 項 | ABSENT 23 · GREEN 5 · PLAN 32 · **RED 6** | RED 6 = ENG081 ×2 · ENG079 ×4:自測遇 duckdb 缺印 `[FAIL]` rc1 |
| CGC_MDL174 打包閘 VDF | ⑥ 落頁同一份規格 NODATA:3 支落頁,**2 支自己帶一份 CSS**(ENG076 · ENG078) | 尺散了(批672):同一張頁兩份 CSS 就是九頭龍 |
| CGC_MDL164 制度稽核 ⑰ 自我指涉閘 | 基線外 1:**VDF_SystemManager**(NO_EXCLUDE) | 本線 b 批立的門,版史掃描把自己算進分母(LL133) |
| VDF 對接口 status | 邏輯 STALE(卡書 45 張:冊有樹無 1 · 無版號 5 · 樹有冊無 3)· 工具 STALE(Celeritas 三副本兩版本)· 七處 7/7 | 候裁項不變(b 批 Z89/Z90) |
| SSOT/同義字四閘 | MDL115 9/9 · MDL176 30/30(只增不減:底冊 971 條少 0)· SUP_MDL749 48/48 · ENG088 drift YELLOW(KEY_BRIDGE 包內鍵橋不在正典)| 只增不減成立;衝突 5 條是我們自己兩本冊的鍵拼法(候裁,四)|

## 三 · 修在哪裡(可同時修的一起修;每件新版號檔;生產邏輯零改動,改的全是「怎麼講」)

**尺(兩把,先修)**
| 件 | 改了什麼 | 證據 |
|---|---|---|
| Grid **v0439 → v0440**(推之前主線批688 出了自己的 v0438,與本線 b 批的 v0438 撞名;依 L25 取主線 v0438,本線所有格子改動重貼成 v0440,v0439 留作版史)| 站敗但輸出說「第三方套件不在本境」(`No module named 'x'`,且 x 不是 VIA 樹上的自家模組——自家模組集向 CGC_MDL124.tracked_set() 取,不另掃樹)或引擎自報 rc=3 → **SKIP 環境缺件(誠實)**;自家模組炸了照舊 FAIL。三站改 nodata_ok(ENG058 · MDL098 · MDL099 · MDL105 · MDL173:庫/再生頁/rich 不在=NODATA rc2)| 全格子 FAIL 82 → **26**(SKIP 8 → 61,OK 202);單元測試 T01 |
| CGC_MDL170 **v0102** | 同律:ModuleNotFoundError(非自家模組)或 rc=3 → **ABSENT 具名套件**,修法句指路家族境;+⑲ 合成檢(缺件→ABSENT · 壞掉→RED 負控)| 鏈 run:GREEN 6 · **RED 0** · ABSENT 3 · GATED 1;十九檢 19/19 |

**引擎的誠實態(只動自測/報態,生產邏輯一字不動)**
| 件 | 改了什麼 |
|---|---|
| VDF_ENG081 v0101 · VDF_ENG079 v0101 · CGC_MDL141 v0110 | 自測遇 duckdb 缺:`[FAIL] rc1` → `[ABSENT] rc3`,輸出帶 ModuleNotFoundError 字樣讓三把尺同判 |
| VDF_ENG045 v0101 | 格式往返檢遇 pyarrow/duckdb 缺 → [ABSENT] 不進分母,`[計] 5/5 · ABSENT 2`,rc3;真 FAIL 仍 rc1 |
| VDF_ENG058 v0101 · CGC_MDL098 v0102 · CGC_MDL099 v0101 · CGC_MDL105 v0125 | 庫 / 再生頁不在 → `[NODATA]` rc2(缺料≠壞掉);在時全檢照跑 |
| VDF_ENG088 v0103(共識融合橋)· VIA_FinancialInstitution_Overlay v0103 · CGC_MDL088 v0103 · CGC_MDL148 EngineBus v0130 | duckdb / pydantic / 關鍵庫不在 → `[ABSENT]` rc3 或該檢不進分母(匯流排 ㉟) |
| CGC_MDL080 v0101(收尾系統) | 電池單道 rc3 = ABSENT,不再記 FAIL |

**整併(CONSOLIDATE)**
| 件 | 改了什麼 | 證據 |
|---|---|---|
| VDF_ENG076 **v0101** · VDF_ENG078 **v0109** | `render()` 不再自備 CSS/頁殼:殼、CSS、表、KPI、態燈色全部向 **CGC_MDL173** 取(`html_table` / `page_html`),本引擎只拼資料列;規格缺=無樣式誠實頁 | MDL174 ⑥ **GREEN(3/3 接規格)**;單元測試 T04 用合成資料驗 render() |
| VDF_SystemManager **v0102** | LL133:`_SELF_FAMILY` 不進版史分母 | MDL164 ⑰ **23/23**;Grid v0439 的自家模組集改向 CGC_MDL124 取後,⑰ 也不再把格子當新判定器 |

**測(TEST)**:`tests/test_vdf_honest_states_v0100.py` 10 檢(格子分類器 · 鏈跑器缺件/壞掉負控 · 四支引擎 rc 語意 · 兩張頁只接規格 · 匯流排 ㉟ · 對接口自家族)+ `test_vdf_system_manager_v0101.py`(T02 改結構等式:對得上的尾版數 = 橋掃器沒排除的尾版數,不再釘 ≥40——沒 commit 的新版被橋掃器判 untracked 排除,釘死數字在那一刻就紅,同 b 批 ⑱ 那一課)。py3.11 · 3.12 同過。

## 四 · 與總管 SSOT REGEX / 同義字:「上傳更新只增不減不衝突」量到的現況

- **只增不減**:CGC_MDL176 聯集閘「底冊 971 條逐條比對 → 少 0 條」;冊內瑕疵 0;聯集冊 broker 255 · rating 189 · target_price 29 · valuation_method 20 · financial_concept 7 · rating_label 7 · scenario 3。MDL115 樣式 1156 · 共用 651 · 同義字冊 37,九檢 9/9。樞紐 SUP_MDL749 v0111 四十八檢 48/48。
- **衝突**(不是上傳帶進來的,是我們自己兩本冊對同一家用了兩個正典鍵拼法;批678 已列,候操作員裁,LL90):megabank(Megabank vs MEGA)· daiwa capital(Daiwa Securities vs DAIWA)· jp(J.P. Morgan vs JPM)· ibf securities(IBF vs WATERLAND)+1。裁了之後聯集閘自轉綠。
- **上傳的增補**:ENG088 drift 只剩一條 YELLOW——包內 `KEY_BRIDGE`(BOA→BOFA · MCQ→MACQUARIE · JP→JPM)不在任何正典冊;candidates 25 條一律 PENDING_OPERATOR(本橋不抄)。
- **整合好了沒**:冊面整合成立(只增不減 · 無衝突新增);**採用面**有缺口——MDL176「沒過拒絕閘的活支 9/10」(SUP_MDL015 · SUP_MDL749 · VIS_VRN_BrokerAlias ×2 · PDFTextLayerFallbackPlan · Q1_AliasRoutePatch · VRN_ENG062 · VRN_ENG086 · vrn_report_digest 各自解券商別名,沒經 resolve_broker/deny_reason)。那是 VRN 九支的改線,不在本令(VDF)範圍,登掉球 Z97 候裁。
- 疊加層引擎 VIA_FinancialInstitution_Overlay v0103:正典載入要 pydantic,本境沒有 → 以前 ①④⑥ 連環紅,現在 [ABSENT] rc3;工作站(家族境有 pydantic)十檢照跑。

## 五 · 修完之後還紅的(誠實列;不在本令範圍或要操作員的手)

最後一次全格子(Grid v0439,修完後整樹實跑):**OK 207 · FAIL 15 · SKIP 67 · TIMEOUT 0**(修前 FAIL 82 · SKIP 8)。那一跑裡 VRN 索引冊守門與 VRN 對接口實跑兩站紅,是 CGC_MDL141 出了 v0110 讓索引冊指標過期(冊是產物,`via-vrnbook build` 重建後兩站轉綠,冊入 git)。剩下的紅分三類:

| 站 | 根因 | 誰 |
|---|---|---|
| 五日擷取八檢(ENG049)· ETF 持股引擎自測(ENG051) | 兩支**沒版號**的 VDF 檔(b 批 Z90),自測把 yfinance/pandas 不在寫成 FAIL;立版號前不動它們(動了就是第二顆頭) | 操作員裁 Z90 |
| 文字統包六檢 · VRN 六層鏈廿四檢/實跑 · 研報一題四點文摘三十檢 · 首頁全能引擎 ㊳ · PDFPlumber-Plus ⑥ · 三語 SSOT×MindMap ① · 知識堆疊轉接 | VRN 家族:pymupdf/openpyxl/duckdb 不在本境、或要真檔/真庫;同一種「把境缺寫成 FAIL」的病,修法同本批 ENG081 那一行 | VRN 那條線(本令是 VDF) |
| 系統同步樞紐 ③ · 每日觀察摘要 ②③ · 治理台 UI Matrix ② · 工具升階梯 ③④ | 讀真庫列數 / 綠燈率 / OCR 件;容器沒料 | 工作站跑才有結論 |
| TWREV v2.7 selftest(收容 b477 PYCODE 站) | `-m` 啟動於收容包,pandas 不在 → 空輸出 | 收容件,零觸碰 |
| 總控頁契約十九測 test_11 | 新版引擎路徑進了 Deck argv → 總控頁要再生;**已再生**(LL49 例外件,入 git)| 本批已解 |

## 六 · 容器實測總表

| 檢 | 修前 | 修後 |
|---|---|---|
| 全格子 289 站 | FAIL 82 · SKIP 8 | **OK 207 · FAIL 15 · SKIP 67**(FAIL 裡 2 站是索引冊過期,重建後綠;其餘見五) |
| VDF 獨立鏈 run | GREEN 6 · RED 1 · GATED 1 · NODATA 2 → RED | GREEN 6 · RED 0 · ABSENT 3 · GATED 1 → GATED(閘是操作員的手)|
| 匯流排 test profile vdf 66 項 | RED 6 | **RED 0**(ABSENT 29 · GREEN 5 · PLAN 32)|
| MDL174 ⑥ 落頁同一份規格 | NODATA(2 支自帶 CSS)| **GREEN 3/3** |
| MDL164 ⑰ 自我指涉閘 | FAIL(基線外 1)| **23/23** |
| VCGC v0120 · 對接口 v0102 · 鏈跑器 v0102 · 匯流排 v0130 | — | 26/26 · 27/27 · 19/19 · 49/49 |
| 單元測試(兩檔,py3.11/3.12)| — | 10/10 · 20/20 |
| 總控頁契約(py3.12)| test_11 紅(頁未再生)| 19/19 |
| 中央冊 registry-sync | — | 6099/6099 缺 0 · 家族 273/273 |

## 六之二 · 併線(推之前主線又動了兩次)

- main:PR #62/#64(brave-goldberg 批688/689:一頁交接追到現況 · LL306–LL343 入律冊 · 接手提示詞 v0101)→ 掉球冊取主線+本線 b/c 兩段接後(Z89–Z98 沒撞)· 台帳聯集 1294。
- awesome-bardeen 批688(a49f52e4:索引冊建冊冪等 v0106 · VDF_ENG082 v0101 · **Grid v0438**)→ Grid 取主線 v0438、本線改動重貼成 **v0440**;VRN 索引冊以 builder v0106 重建(MDL141 v0110 讓指標過期)· 元件冊取主線再以 VCGC v0120 重跑(6109/6109)· 總控頁再生。
- 併後複測:VCGC 26/26 · 契約 19/19 · 兩檔單元測試 10/10 · 20/20(兩版 Python)· MDL164 23/23 · Grid v0440 `--only` 19 站 OK 15 · SKIP 4 · FAIL 0。

## 七 · 掛著(接續主線掉球冊 Z94 → Z95–Z98)

- Z95 VRN 家族同病(把境缺寫成 FAIL):ENG060 TextOmni · ENG080 · ENG072 …;修法同本批一行(`[ABSENT] rc3` + ModuleNotFoundError 字樣),要在 VRN 那條線做。
- Z96 兩支無版號 VDF 檔(ENG049 · ENG051)的自測境缺判紅,等 Z90 立版號一起做。
- Z97 同義字採用面:MDL176 拒絕閘 9/10 活支沒經 resolve_broker(VRN 九支);冊面已只增不減無衝突。
- Z98 五條券商鍵拼法衝突(megabank · daiwa · jp · ibf +1)候裁(LL90);裁後 MDL176 自轉綠。

## 八 · 接手驗收(一行一答)

1. `via-selftest`(全格子)→ FAIL 只剩五段那幾類;SKIP 的每一站註記都寫「環境缺件(誠實):套件不在本境:…」。
2. `via-vdfchain run` → RED 0(容器 ABSENT 3;工作站家族境應為 GREEN 9 或 GATED)。
3. `python "supportive modules/registry/tests/test_vdf_honest_states_v0100.py"` → Ran 10 · OK。
4. `via-packgate` → VDF ⑥ GREEN。

## 九 · 一貼即用(工作站;閘那兩行是你的手)

```powershell
via-fresh
via-selftest --only "VDF 獨立鏈,台股日交易×籌碼對齊,本機三庫整併,VDF 輸出樞紐,主動ETF×月營收動能,主動ETF持股史深,產業混合分類冊,共識融合橋"
via-vdfchain run
via-packgate
via-vdfsys
```
工作站有家族境(duckdb/pyarrow 在),這些站會走**真跑**那條路,不是容器的 ABSENT/NODATA;紅了才是本批沒量到的東西。
