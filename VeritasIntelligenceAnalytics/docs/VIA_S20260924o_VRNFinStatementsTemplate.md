# VIA 側線 2026-09-24 第十五段 · 交易所財報 VRN 模板頁(制式 HTML U/I · SYNCHRONIZER 交接 · 上下自動燈號)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924n_PR116ReviewFix.md`(ENG082 v0104 / v0105)。
> 操作員令(原話):
> - 「實測無誤後結果驗證無誤後收尾並用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」
> - 「上下的自動連結更新新增檢查機能建構須完成」
> - 「進行自設自修正時測修改直到成功收尾聯上 HTML NU/I 使用者測試無誤 開啟運作無誤 上下建立自貢燈心機制」
> - 「REAL TEST DEBUG OPTIMIZE TEST CONSOLIDATE TEST DEBUG USER-TEST DEBUG ACTIVATE TEST DEBUG TILL IT WORKS PERFECT. 自動傳PR自動批種完成 最後實測要HTML U/I結果報告」
>
> **LL334 讓號(第十五段(續))**:本段原本的引擎叫 `VRN_ENG089_FinStatementsTemplate`。主線批735(PR #118 / #119)先把
> `VRN_ENG089` 用在 `VRN_ENG089_TemplateView`,併進 main 了,所以本支讓號為 **`VRN_ENG090_FinStatementsTemplate`**(掃過 41 條遠端分支,
> 沒有人用 VRN_ENG090 當檔名)。下面講的都是新名字;第十節講併 main 時量到、修掉的東西。

## 一 · 一句話

交易所財報(ENG082 `run --mops` 落的兩張表)現在有一張 VRN 模板頁。
- 頁的樣式照 VIA_HTML_UI 制式模板:配色、密度、印章 Logo 都現讀套件。
- 資料交接由 SYNCHRONIZER 控制:按一下就交給 SYNCHRONIZER,中央 UI 從同一份狀態收到。
- 交接**只增不減**:同一份 SYNCHRONIZER 狀態裡別人的模組(系統的、你自建的、批735 VRN 模板掛的)一個都不動。
- 上下游各有一排自動燈。

## 二 · 你在工作站怎麼用

| 步 | 做什麼 | 看到什麼 |
|---|---|---|
| 1 | `via-finstat run --mops`(閘由你開) | 交易所財報進庫(上一段的車道) |
| 2 | `via-vrnui`(家族頁名冊已經有這一頁;或直接 `python "functional modules/VRN/VRN_ENG090_FinStatementsTemplate_v0101.py" run`) | 產出 `supportive modules/ui_support/VIA_UI_VRNFinStatements_v0100.html` |
| 3 | 開那一頁 → 按「交接到 SYNCHRONIZER」 → 按「開 SYNCHRONIZER」或「開中央 UI」 | SYNCHRONIZER 的目前範本變成「VRN 交易所財報 · 季 · 資料時點」;中央 UI 左側「自定義模組」出現 VRN 模組,名稱帶燈 |
| 4 | `python "functional modules/VRN/VRN_ENG090_FinStatementsTemplate_v0101.py" check` | 上下連結逐條一盞燈(不寫任何檔) |
| 5 | (可選)`node "supportive modules/registry/tests/uxtest_vrn_finstatements_v0101.js"` | 瀏覽器真開三頁實測,產出 `VIA_Reports/ui_vrn_finstat_test_artifacts/uxtest_vrn_finstatements_report.html`(單檔 HTML 結果報告,截圖內嵌)。要 Node + Playwright + Chromium;沒有就照實丟錯,不假綠 |

瀏覽器不給 localStorage(或 SYNCHRONIZER 規則不准)時,按「下載信封」,再到 SYNCHRONIZER 按「匯入 JSON/CSV/Excel」選那個檔,效果一樣。

**要收起某個 VRN 模組,請在 SYNCHRONIZER 把它「停用」(把勾拿掉),不要按 ×**:停用會一直記著,自動更新也不會把它打開;
刪掉的話,下一次交接會再加回來(頁分不出「沒加過」和「被你刪掉」——批735 的 VRN 模板也是同一條規則)。

## 三 · SYNCHRONIZER 怎麼控制交接

頁只照 SYNCHRONIZER 存在狀態裡的同步規則走,不自己做主:

| SYNCHRONIZER 的規則 | 頁怎麼做 |
|---|---|
| 範圍「全部」或「只同步模組」、衝突「最新優先」 | 可以交接。模組**只增不減**(同 SYNCHRONIZER 套範本的「合併」模式):別人的模組連啟用 / 釘選 / 順序都不動;自己的模組(id 以 `vrn-finstat-` 起頭)換新名稱(帶燈)與註記、保留你的啟用與釘選;這一趟不再產的自己的模組才拿掉;新的接在最後。檢視 / 版面 / 規則照你現在的 |
| 範圍「手動」或「只同步檢視」、或衝突「本機優先」 | 不寫,燈 = 閘,告訴你改用「下載信封 → 匯入」 |
| 目前已經是本範本、資料比本頁舊 | 頁一打開就自動更新(一樣只增不減) |
| 目前已經是本範本、資料比本頁新 | 不蓋回去,燈 = 過期,請你重產本頁(兩頁不會互蓋) |
| 目前是別的範本(例:投資研究) | 不動;按交接先告訴你會換掉哪個**分析範本**(圖表 / 歷史 / 樞紐),再按「確定交接」才換;模組照樣只增不減 |

頁的密度、主題、字級也跟著 SYNCHRONIZER 的檢視設定走(自適應)。

## 四 · 上下自動燈

燈名全出自 VRN 燈號冊(VRN_SystemManager 尾版的 LAMPS,現讀):綠 · 缺料 · 閘 · 缺件 · 過期 · 壞。

- **上游燈(資料)**
  - 上游引擎 VDF_ENG082:用尾版;判齊用它自己的 `mops_target` / `mops_plan`,本支不另寫判準。
  - 資料庫:唯讀開庫;開不了照實說(例:撞鎖),不當成全缺。
  - 每個市場的**完整度**:還缺幾個端點;交易所擋 = 缺料,閘沒開 = 閘。
  - 每個市場的**新鮮度**:正典 `period_lag`,最新季底 → 下一季期限過了幾天。
- **下游燈(交接與登錄)**
  - SYNCHRONIZER 契約:套件兩頁的鍵名 / 頻道一致。
  - 套件完整:借 CGC_MDL160 的 template 閘。
  - 燈號冊。
  - 家族頁名冊:CGC_MDL138 有沒有這支。
  - U/I 契約:via-workflow ui-contract 有沒有收這一頁、擁有者對不對。
  - 信封合 SYNCHRONIZER 規格(v0101 起多一條:自己的模組 id 都要帶 `vrn-finstat-` 前綴,只增不減靠它認自己的)。
  - `check` 另驗:頁與庫同一時點 · 頁內鍵名 = 套件現讀 · 頁零外連 · 信封檔 = 頁內嵌那一份。
- **瀏覽器端交接燈**:頁上現量,就是上表那幾種情況。

同一組燈也寫進 SYNCHRONIZER 信封的模組名稱與備註,所以 SYNCHRONIZER 和中央 UI 側欄看得到同一盞燈。

## 五 · 上下自動連結 / 更新 / 新增 / 檢查

| | 上游 | 下游 |
|---|---|---|
| 連結 | ENG082、正典、套件都取尾版現解,不釘版號 | 家族頁名冊(CGC_MDL138 v0103)· U/I 契約(CGC_MDL153 掃頁自動收)· VRN_SystemManager(VCGC 尾版清單自動認到)· VRN 六層冊(待裁定清單,守門 ⑧ 交代到)· SYNCHRONIZER / 中央 UI(同一把鍵) |
| 更新 | 每次 run 重讀庫 | `via-vrnui` 自動重產本頁;SYNCHRONIZER 是本範本舊資料時,頁一開就自動更新 |
| 新增 | 市場 / 業別 / 季全部從庫與 ENG082 常數長出來:多一個就多一列、一個模組、一張圖,不改碼 | 新頁自報再生短令:頁頭 `<meta name="via-refresh">`,CGC_MDL153 v0102 冊上沒寫的頁就讀它,新頁不必再改契約那一支 |
| 檢查 | `check`(上游 6 盞) | `check`(下游 10 盞)· 自測二十三檢 · 格子 v0495 一站 · 瀏覽器實測二十檢 |

**上下連結會自己抓到過時的一環**(併 main 時實錄):改號後第一次 `run`,U/I 契約那盞燈當場亮紅「契約認的擁有者是 VRN_ENG089_FinStatementsTemplate_v0100.py」——
契約是上一次 `via-workflow ui-contract` 產的。照燈上的修法重跑 ui-contract,契約自己挑到新的尾版當擁有者,燈轉綠。

## 六 · 改了什麼

| 檔 | 版 | 自測 |
|---|---|---|
| `functional modules/VRN/VRN_ENG090_FinStatementsTemplate_v0100.py` | 新(LL334:由 `VRN_ENG089_FinStatementsTemplate_v0100.py` 改號,內容只換自己的名字) | 22/22 |
| `functional modules/VRN/VRN_ENG090_FinStatementsTemplate_v0101.py` | v0100→v0101:交接只增不減(第十節);合併碼只有一份 `_JS_MERGE`,頁上跑、自測 ㉓ 用 node 跑同一份;驗器 +自己的模組要帶前綴 | 23/23 |
| `supportive modules/registry/CGC_MDL138_FamilyUI_v0102.py` | v0101→v0102:ROSTER vrn 加這一頁;資料閘分支的附註照頁新鮮講「本趟新產 / 在位舊版 / 缺」(原本一律寫「頁在位舊版」,不誠實 L92) | 8/8(③ 夾具多一支) |
| `supportive modules/registry/CGC_MDL138_FamilyUI_v0103.py` | v0102→v0103:ROSTER 那一項的 glob 跟著改號換成 VRN_ENG090,其餘一字不動 | 8/8 |
| `supportive modules/registry/CGC_MDL153_WorkflowComposer_v0102.py` | v0101→v0102:U/I 契約的再生短令,冊上沒寫的讀頁自報的 `via-refresh` | 12/12(⑥ 夾具多兩頁) |
| `supportive modules/registry/via_vrn_logic_book_v0109.py` | v0108→v0109:OFF_BOOK_PENDING +VRN_ENG090(上不上架構冊待你裁,Z213);冊照建冊程式重建 | 17/17 · 守門 GREEN |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0495.py` | v0493→v0495:+1 站「VRN 交易所財報模板二十三檢」;三大報表擷取引擎 二十一 → 二十二(LL213,Z204 結) | 相關 10 站 OK |
| `supportive modules/registry/tests/uxtest_vrn_finstatements_v0100.js` | 新:瀏覽器使用者實測 + HTML 結果報告 | 17/17 |
| `supportive modules/registry/tests/uxtest_vrn_finstatements_v0101.js` | v0100→v0101:+⑱⑲⑳ 跟批735 VRN 模板共存 | 20/20 |
| `.gitignore` | 生成頁 `VIA_UI_VRNFinStatements_v*.html` 不入 git(同 ControlTower) | — |
| `supportive modules/ui_support/VIA_UI_MasterControl_v0100.html`(LL49 例外) | 正主管理器重產 | 主控台契約 19/19 |
| 冊(就地) | 元件冊 · 正則清冊照建冊程式重建 · 六層冊(VIA_VRN_LogicArchitecture_SSOT)照 v0109 重建 · 帳 · 掉球 Z204 結 / Z210 補量 / Z212 / Z213 | — |

VIA_HTML_UI 套件一個位元組都沒改(CGC_MDL160 sha256 223/223)。

## 七 · 怎麼證明

- **自測 23/23**(暫存夾、零網路、不碰真庫):
  - 全齊 → rc0;旁邊有人唯讀開著照樣跑;庫 md5 前後相同。
  - 信封合規格;驗器正控:六種壞信封都抓得到。
  - 上市被擋 → 缺料「缺 12/12 · 交易所擋」;閘沒開 → 閘。
  - 撥到 11/20 → 新鮮度過期「已過 6 日」。
  - 自動新增:業別、季多出來會自己長。
  - 庫不在 / 撞鎖 / 上游不在,都誠實說原因。
  - `check` 抓得到:頁舊、名冊沒登錄、信封檔被改、套件換鍵名、頁是舊鍵名產的、契約擁有者不對、契約檔壞、燈號冊少一盞。
  - 惡意字串全跳脫。
  - ㉒ 子行程只准在 `_run_node`(自測跑 node 用,引擎本體零子行程、零網路)。
  - ㉓ 交接只增不減:node 實跑頁上那一份合併碼,四種狀態(沒狀態 · 別人的模組 + 自建 + 你關掉的自己的 + 不再產的自己的、順序亂排、同 order 平手、系統模組 id 撞前綴 · 再合一次 · 狀態沒系統模組)。
- **改壞測試**:
  - Python 39 個全抓到(v0100 那一輪;第一輪抓 30 個,沒抓到的 9 個都是測試缺口,已補斷言或夾具後重跑)。
  - 合併碼 14 個全抓到(自測 ㉓;第一輪抓 12 個,同 order 平手、系統模組 id 撞前綴兩個補了情境後抓到)。
  - 頁上交接 JS:見第十節的實跑數字。
- **瀏覽器使用者實測 20/20**(容器 Chromium,三頁全 file://):
  - 開頁零錯誤;燈、KPI、矩陣、圖都畫出來。
  - 三頁同源;交接後 SYNCHRONIZER 與中央 UI 都收到,頻道上有廣播。
  - 重開不重寫;檢視跟著 SYNCHRONIZER 走;三種規則都擋得住;只往新的方向自動更新;換範本先問。
  - 下載信封;SYNCHRONIZER 匯入信封 / 歷史 CSV;手機 390 寬不橫捲。
  - ⑱ 跟批735 VRN 模板共存:狀態裡有它的 `vrn-report-template`(你在 SYNCHRONIZER 關掉了)和你自建的「我的筆記」→ 交接後兩個原樣留著,VRN 模組接在後面,SYNCHRONIZER 清單照畫、那個勾還是空的。
  - ⑲ 你關掉的 VRN 模組(上下連結),自動更新之後還是關的,名稱換新。
  - ⑳ 中央 UI 側欄照啟用與否畫:VRN 財報總覽與「我的筆記」在,停用的兩個不在;全程三頁零錯誤(中央 UI 只放行套件已知那一句,Z210)。
  - **反面控制**:同一支測試拿 v0100(舊交接)產的頁跑,⑱ ⑲ ⑳ 三檢紅——測試抓得到,修了才綠。
- **真資料對照**(開發用真庫副本:錄下的 TPEX 12 端點經 ENG082 v0105 寫進容器真庫副本;TWSE 被擋):
  - 上櫃:綠(齊 12/12、2026Q2、892 家、29,368 項、冊上 893)。
  - 上市:缺料(交易所擋)。
  - rc2 照實報。
  - `check` 下游 10 盞全綠。
- **家族頁再生閘**:CGC_MDL138 只放這一項真跑。產生器 rc2 → 判「DATA 資料側、本趟新產」;索引頁連到這一頁。
- **回歸**:見第十節(併 main 之後重跑的才算數)。

## 八 · 還沒做 / 要你裁

- **Z210(模板線,你裁)**:VIA_HTML_UI 中央 UI 的既有缺陷(`toast is not a function`)。主線批735 同一天也量到、登在 Z210,側線的獨立量測補在同一列;要修得出套件新版。
- **Z212(你的手 L70)**:短令(例 `via-vrnfin run|check|status`)要動 Register-VIA-Commands 的 .ps1,等你點頭。現在用 `via-vrnui` 重產、用 python 指令 check。
- **Z213(你裁)**:VRN_ENG090 掛在六層冊待裁定清單。它讀的是 VDF 交易所財報,不是研報六層鏈上的料;一句「上 L4_產出」或「不上」我就落冊。
- 主控台規格冊沒加項(會牽動主控台幾張追蹤中的生成頁);`vrn_ui` 那一項已經會連本頁一起重產。你要專屬一項再說。
- Z204 結(格子 v0495 把站名 二十一 → 二十二);原本「格子加站」那一筆也在 v0495 做掉了,不另立號。

## 九 · 還原

- 刪掉 `VRN_ENG090_FinStatementsTemplate_v0100.py` / `_v0101.py`、`CGC_MDL138_FamilyUI_v0102.py` / `_v0103.py`、`CGC_MDL153_WorkflowComposer_v0102.py`、
  `via_vrn_logic_book_v0109.py`、`CGC_MDL064_SelftestGrid_v0495.py`、`uxtest_vrn_finstatements_v0100.js` / `_v0101.js`,尾版就回到併 main 當時。
- 六層冊刪了 v0109 之後要 `via-vrnbook build` 重建一次(冊版不同步閘會提醒)。
- 冊與 `.gitignore` 都是就地改的,`git revert` 就能回去。
- 生成頁與 `VIA_Reports/vrn/finstat/` 是再生類,刪掉不影響任何東西。
- SYNCHRONIZER 裡的 VRN 範本:在 SYNCHRONIZER 按「清除」或套別的範本即可;VRN 模組在清單裡停用或刪掉都行。

## 十 · 第十五段(續):併 main 批735 · LL334 讓號 · 交接改只增不減

### 1. 撞號,照 LL334 讓號

PR #117 要併的時候 main 已經動了:主線批735(PR #118 / #119)接的是**同一句操作員令**,做的是「VRN 自測迴圈的成果套進制式 U/I」,
出了 `VRN_ENG089_TemplateView`、格子 v0493、掉球 Z210 / Z211。PR 因此變成衝突(`dirty`),CI 沒在新 head 上跑。

| 撞到的 | 主線批735 | 本側線(讓號後) |
|---|---|---|
| 引擎號 | VRN_ENG089_TemplateView | VRN_ENG090_FinStatementsTemplate(檔名沒人用過;命名冊的正典號是另一套對映,「實體檔零改名」) |
| 格子 | v0493 | v0495(v0492 在 PR #104、v0494 在 PR #121 批736 的分支上,都還沒併;以 main 的 v0493 為底) |
| 掉球 | Z210 · Z211 | Z210 同一個缺陷 → 併成一列;原 Z211 在本 PR 做掉;Z212 留號;新 Z213 |

改號照 PR #104 先例:沒併過的檔直接改名(git 認得是改名),內容只換自己的名字(v0100);要改碼的另出新版(v0101、MDL138 v0103)。

### 2. 真的 bug:交接會刪掉別人的模組

批735 的 VRN 模板也把自己的模組 `vrn-report-template` 掛進**同一份** SYNCHRONIZER 狀態(file:// 的頁共用 localStorage)。
v0100 交接照 SYNCHRONIZER「取代」模式:只留系統模組、其餘全換成本頁的——

- 批735 的 `vrn-report-template`、你自建的模組,交接一次就被刪掉;
- 你在 SYNCHRONIZER 關掉的那個,下次開批735 的模板頁又被它的預置段加回來,**而且變成啟用**;
- 你關掉的本頁模組,自動更新一次就又打開了。

v0101 改成 SYNCHRONIZER 套範本的「合併」模式(`applyTemplate` 的 merge 分支:同 id 覆蓋、其餘照留),再多兩條:自己的模組保留你的啟用與釘選;
這一趟不再產的自己的模組才拿掉。順序照 SYNCHRONIZER `normalizeModules`(order 升冪、同值照原順序)。合併碼只有一份,頁與自測共用。

### 3. 漏跑的一站:六層冊守門 ⑧

第十五段第一版的回歸只挑了六站跑,**沒跑「VRN 邏輯架構索引冊十七檢」**。這一站的 ⑧「樹上每一個 VRN_ENG 家族都要被交代」
在 v0107 上實量是紅的(沒被交代 1:VRN_ENG089_FinStatementsTemplate)。v0109 把它掛進待裁定清單(Z213)、冊照建冊程式重建,
自測 17/17、守門 GREEN。這一次改跑**全格子**,不再挑站。

### 4. 驗證(併 main 之後重跑)

- 自測:ENG090 v0100 22/22 · v0101 23/23 · MDL138 v0103 8/8 · 六層冊 v0109 17/17(守門 GREEN)。
- 合併碼改壞 14/14。
- 瀏覽器實測 v0101 20/20;反面控制(v0100 的頁)⑱ ⑲ ⑳ 紅。
- 頁上 JS 改壞 15/15(v0100 取代語意 · 丟使用者停用 · 名稱不換新 · 別人的順序亂掉 · 系統模組丟掉 · 規則沒擋 · 沒廣播 …)。
- **全格子**(本支格子內容,以 v0494 檔名實跑;改號 v0495 只換檔名與表頭):**OK 337 · FAIL 6 · SKIP 14 · TIMEOUT 0**,765 秒,
  存證 `GRID_20260924_215910.json`,正式庫三本前後一致。6 紅**不是本 PR 的**:拿一棵乾淨的 origin/main 工作樹(格子 v0493)
  在同一個容器跑同 6 站,6 站一樣紅、紅在同幾條——
  pdfplumber / fitz 表格引擎(首頁文字擷取 ⑪ · VRN 六層鏈的 L2 ENG072 · VRN 統一報告引擎)· OCR 件沒裝(工具升階梯 ③)·
  生成頁不在這個容器(CGC_MDL120 ⑥ 缺 `VIA_UI_ETFConsensusAnalysis_v0100.html`)· 治理台讀到容器裡的舊存證綠燈率(UI Matrix ②)。
  主線批735 在它自己的容器是 0 紅;這 6 站本 PR 一行都沒碰。
- 改號 v0495 之後再跑 12 站(新站 · 三大報表 · 六層冊兩站 · 家族 U/I · 工作流重組台 · 批735 VRN 模板 · VRN 子系統管理兩站 ·
  U/I 畫面統一閘 · 格子自身七檢 · VCGC 三十八檢)全 OK,正式庫前後一致;元件冊照 v0495 再掃一次(變更 39,之後新 0 · 變更 0)。
- VCGC 38/38 · ssot verify rc0(RED 0)· 本機照 CI:系統管理器 / 執行橋 / 同步狀態 / 標準儀表板自測 rc0 · 主控台契約 19/19 · UAT rc0。
- 全景代讀:ENG090 v0100 / v0101 零報;MDL138 v0103(4)· 六層冊 v0109(1)· 格子(10)的問題數跟前一版一模一樣(沿用的舊債)。
  py3.12 / 3.13 編譯過;Node 語法檢查過;增量擷取閘普查:本支不出網,私有去重寫入 0。
