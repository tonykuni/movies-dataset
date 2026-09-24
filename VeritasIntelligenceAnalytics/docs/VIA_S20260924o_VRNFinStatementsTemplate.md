# VIA 側線 2026-09-24 第十五段 · 交易所財報 VRN 模板頁(制式 HTML U/I · SYNCHRONIZER 交接 · 上下自動燈號)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924n_PR116ReviewFix.md`(ENG082 v0104 / v0105)。
> 操作員令(原話):
> - 「實測無誤後結果驗證無誤後收尾並用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」
> - 「上下的自動連結更新新增檢查機能建構須完成」
> - 「進行自設自修正時測修改直到成功收尾聯上 HTML NU/I 使用者測試無誤 開啟運作無誤 上下建立自貢燈心機制」
> - 「REAL TEST DEBUG OPTIMIZE TEST CONSOLIDATE TEST DEBUG USER-TEST DEBUG ACTIVATE TEST DEBUG TILL IT WORKS PERFECT. 自動傳PR自動批種完成 最後實測要HTML U/I結果報告」

## 一 · 一句話

交易所財報(ENG082 `run --mops` 落的兩張表)現在有一張 VRN 模板頁。
- 頁的樣式照 VIA_HTML_UI 制式模板:配色、密度、印章 Logo 都現讀套件。
- 資料交接由 SYNCHRONIZER 控制:按一下就交給 SYNCHRONIZER,中央 UI 從同一份狀態收到。
- 上下游各有一排自動燈。

## 二 · 你在工作站怎麼用

| 步 | 做什麼 | 看到什麼 |
|---|---|---|
| 1 | `via-finstat run --mops`(閘由你開) | 交易所財報進庫(上一段的車道) |
| 2 | `via-vrnui`(家族頁名冊已經有這一頁;或直接 `python "functional modules/VRN/VRN_ENG089_FinStatementsTemplate_v0100.py" run`) | 產出 `supportive modules/ui_support/VIA_UI_VRNFinStatements_v0100.html` |
| 3 | 開那一頁 → 按「交接到 SYNCHRONIZER」 → 按「開 SYNCHRONIZER」或「開中央 UI」 | SYNCHRONIZER 的目前範本變成「VRN 交易所財報 · 季 · 資料時點」;中央 UI 左側「自定義模組」出現 VRN 模組,名稱帶燈 |
| 4 | `python "functional modules/VRN/VRN_ENG089_FinStatementsTemplate_v0100.py" check` | 上下連結逐條一盞燈(不寫任何檔) |
| 5 | (可選)`node "supportive modules/registry/tests/uxtest_vrn_finstatements_v0100.js"` | 瀏覽器真開三頁實測,產出 `VIA_Reports/ui_vrn_finstat_test_artifacts/uxtest_vrn_finstatements_report.html`(單檔 HTML 結果報告,截圖內嵌)。要 Node + Playwright + Chromium;沒有就照實丟錯,不假綠 |

瀏覽器不給 localStorage(或 SYNCHRONIZER 規則不准)時,按「下載信封」,再到 SYNCHRONIZER 按「匯入 JSON/CSV/Excel」選那個檔,效果一樣。

## 三 · SYNCHRONIZER 怎麼控制交接

頁只照 SYNCHRONIZER 存在狀態裡的同步規則走,不自己做主:

| SYNCHRONIZER 的規則 | 頁怎麼做 |
|---|---|
| 範圍「全部」或「只同步模組」、衝突「最新優先」 | 可以交接。系統模組照留在最前面,VRN 模組接在後面(同 SYNCHRONIZER「取代」模式);檢視 / 版面 / 規則照你現在的 |
| 範圍「手動」或「只同步檢視」、或衝突「本機優先」 | 不寫,燈 = 閘,告訴你改用「下載信封 → 匯入」 |
| 目前已經是本範本、資料比本頁舊 | 頁一打開就自動更新(自動更新) |
| 目前已經是本範本、資料比本頁新 | 不蓋回去,燈 = 過期,請你重產本頁(兩頁不會互蓋) |
| 目前是別的範本(例:投資研究) | 不動;按交接先告訴你會換掉哪個範本,再按「確定交接」才換 |

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
  - 信封合 SYNCHRONIZER 規格。
  - `check` 另驗:頁與庫同一時點 · 頁內鍵名 = 套件現讀 · 頁零外連 · 信封檔 = 頁內嵌那一份。
- **瀏覽器端交接燈**:頁上現量,就是上表那幾種情況。

同一組燈也寫進 SYNCHRONIZER 信封的模組名稱與備註,所以 SYNCHRONIZER 和中央 UI 側欄看得到同一盞燈。

## 五 · 上下自動連結 / 更新 / 新增 / 檢查

| | 上游 | 下游 |
|---|---|---|
| 連結 | ENG082、正典、套件都取尾版現解,不釘版號 | 家族頁名冊(CGC_MDL138 v0102 新增一項)· U/I 契約(CGC_MDL153 掃頁自動收)· VRN_SystemManager(VCGC 尾版清單自動認到)· SYNCHRONIZER / 中央 UI(同一把鍵) |
| 更新 | 每次 run 重讀庫 | `via-vrnui` 自動重產本頁;SYNCHRONIZER 是本範本舊資料時,頁一開就自動更新 |
| 新增 | 市場 / 業別 / 季全部從庫與 ENG082 常數長出來:多一個就多一列、一個模組、一張圖,不改碼 | 新頁自報再生短令:頁頭 `<meta name="via-refresh">`,CGC_MDL153 v0102 冊上沒寫的頁就讀它,新頁不必再改契約那一支 |
| 檢查 | `check`(上游 6 盞) | `check`(下游 10 盞)· 自測二十二檢 · 瀏覽器實測十七檢 |

## 六 · 改了什麼

| 檔 | 版 | 自測 |
|---|---|---|
| `functional modules/VRN/VRN_ENG089_FinStatementsTemplate_v0100.py` | 新 | 22/22 |
| `supportive modules/registry/CGC_MDL138_FamilyUI_v0102.py` | v0101→v0102:ROSTER vrn 加這一頁;資料閘分支的附註照頁新鮮講「本趟新產 / 在位舊版 / 缺」(原本一律寫「頁在位舊版」,不誠實 L92) | 8/8(③ 夾具多一支) |
| `supportive modules/registry/CGC_MDL153_WorkflowComposer_v0102.py` | v0101→v0102:U/I 契約的再生短令,冊上沒寫的讀頁自報的 `via-refresh` | 12/12(⑥ 夾具多兩頁) |
| `supportive modules/registry/tests/uxtest_vrn_finstatements_v0100.js` | 新:瀏覽器使用者實測 + HTML 結果報告 | 17/17 |
| `.gitignore` | 生成頁 `VIA_UI_VRNFinStatements_v*.html` 不入 git(同 ControlTower) | — |
| `supportive modules/ui_support/VIA_UI_MasterControl_v0100.html`(LL49 例外) | 正主管理器重產:多了一個引擎族,「現役引擎族」108 → 109 | 主控台契約 19/19 |
| 冊(就地) | 元件冊 · 正則清冊重建 · 帳一筆 · 掉球 Z210–Z212 | — |

VIA_HTML_UI 套件一個位元組都沒改(CGC_MDL160 sha256 223/223)。

## 七 · 怎麼證明

- **自測 22/22**(暫存夾、零網路、不碰真庫):
  - 全齊 → rc0;旁邊有人唯讀開著照樣跑;庫 md5 前後相同。
  - 信封合規格;驗器正控:六種壞信封都抓得到。
  - 上市被擋 → 缺料「缺 12/12 · 交易所擋」;閘沒開 → 閘。
  - 撥到 11/20 → 新鮮度過期「已過 6 日」。
  - 自動新增:業別、季多出來會自己長。
  - 庫不在 / 撞鎖 / 上游不在,都誠實說原因。
  - `check` 抓得到:頁舊、名冊沒登錄、信封檔被改、套件換鍵名、頁是舊鍵名產的、契約擁有者不對、契約檔壞、燈號冊少一盞。
  - 惡意字串全跳脫。
- **改壞測試**:
  - Python 39 個全抓到。第一輪抓 30 個,沒抓到的 9 個都是測試缺口,已補斷言或夾具後重跑。
  - 頁上交接 JS 11 個全抓到。第一輪抓 9 個;沒廣播、「只同步檢視」沒擋這兩個,補測後抓到。
- **瀏覽器使用者實測 17/17**(容器 Chromium,三頁全 file://):
  - 開頁零錯誤;燈、KPI、矩陣、圖都畫出來。
  - 三頁同源;交接後 SYNCHRONIZER 與中央 UI 都收到,頻道上有廣播。
  - 重開不重寫。
  - 檢視跟著 SYNCHRONIZER 走。
  - 三種規則都擋得住。
  - 只往新的方向自動更新。
  - 換範本先問。
  - 下載信封;SYNCHRONIZER 匯入信封 / 歷史 CSV。
  - 手機 390 寬不橫捲。
- **真資料對照**(開發用真庫副本:錄下的 TPEX 12 端點經 ENG082 v0105 寫進容器真庫副本;TWSE 被擋):
  - 上櫃:綠(齊 12/12、2026Q2、892 家、29,368 項、冊上 893)。
  - 上市:缺料(交易所擋)。
  - rc2 照實報。
  - `check` 下游 10 盞全綠(先跑 `via-workflow ui-contract` 讓契約收頁)。
- **家族頁再生閘**:CGC_MDL138 v0102 只放這一項真跑。產生器 rc2 → 判「DATA 資料側、本趟新產」;索引頁連到這一頁。
- **回歸**:
  - 格子 v0491 相關六站全 OK:三大報表 · 增量擷取閘 · 工作流重組台 · 家族 U/I 再生閘 · VRN 子系統管理對接口 · U/I 畫面統一閘。
  - VCGC 37/37 · ssot verify rc0(RED 0)。
  - 本機照 CI 綠:主控台契約 19/19、瀏覽器 UAT rc0。新增一個引擎族讓總控頁「現役引擎族」108 → 109,MasterControl 頁照 LL49 用正主管理器重產入倉(先重現 test_11 紅,重產後轉綠)。
  - 全景代讀:VRN_ENG089 零報;MDL138 / MDL153 v0102 的吞例外是 v0101 原樣帶下來的,數量不變。
  - py3.12 / 3.13 `-W error` 編譯過;Node 語法檢查過。
  - 增量擷取閘普查照舊:新引擎不出網,私有去重寫入 0。

## 八 · 還沒做 / 要你裁

- **Z210(你裁)**:VIA_HTML_UI 中央 UI 的既有缺陷。
  - 同步段在另一個 `<script>` 呼叫 `toast()`,解析到 `window.toast`(id="toast" 的元素),所以每收到一次遠端狀態就拋一次 `TypeError: toast is not a function`。
  - 狀態照樣套用,只是提示出不來、主控台紅字。
  - 基線實量:不經本頁、只用 SYNCHRONIZER 套範本 + 套檢視,一樣拋 2 次。
  - 套件是正本(sha256 冊),要修得出套件新版。
- **Z211(等 PR #104)**:格子要加一站「VRN 交易所財報模板二十二檢」,跟 Z204 的站名一起出下一版。格子 v0492 被 PR #104 用掉、還沒併進 main。
- **Z212(你的手 L70)**:短令(例 `via-vrnfin run|check|status`)要動 Register-VIA-Commands 的 .ps1,等你點頭。現在用 `via-vrnui` 重產、用 python 指令 check。
- 主控台規格冊沒加項(會牽動主控台幾張追蹤中的生成頁);`vrn_ui` 那一項已經會連本頁一起重產。你要專屬一項再說。

## 九 · 還原

刪掉 `VRN_ENG089_FinStatementsTemplate_v0100.py`、`CGC_MDL138_FamilyUI_v0102.py`、`CGC_MDL153_WorkflowComposer_v0102.py`、`uxtest_vrn_finstatements_v0100.js`,尾版就回到 v0101;冊與 `.gitignore` 都是就地改的,`git revert` 就能回去。生成頁與 `VIA_Reports/vrn/finstat/` 是再生類,刪掉不影響任何東西。SYNCHRONIZER 裡的 VRN 範本:在 SYNCHRONIZER 按「清除」或套別的範本即可。

本段:
- 沒有動任何 `.ps1`;
- 沒有改任何 intake 正本,也沒有改 VIA_HTML_UI 套件;
- 沒有設任何同意閘或金鑰環境變數;
- 沒有裝任何套件;
- 沒有打任何真端點;
- 真庫一律只用副本。
