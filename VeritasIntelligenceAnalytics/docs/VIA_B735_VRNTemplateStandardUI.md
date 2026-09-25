# 批735 · VRN 模板(制式 U/I 套版 · synchronizer 控制)· 上下游自動連結與新增檢查 · 2026-09-24

> 操作員 2026-09-24(批733 以 PR #115 併進 main 之後):「實測無誤後結果驗證無誤後收尾並用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」
> 「上下的自動連結更新新增檢查機能建構須完成」「若成功跑一次測試文件的成果用我們使用的html u/i顯示」。
> **LL334 改號**:取號前掃了 41 條分支——側線 `claude/upbeat-feynman-1uurww` 已經用了**批734**、**格子 v0492**、**掉球 Z207–Z209**
> (另有 PR #104 改號到批734)。本批改號 **批735**、格子跳號 **v0493**、掉球從 **Z210** 起。VCGC v0129、六層冊 v0108、VRN_ENG089 都沒人用。

## 一 · 做了什麼

| 件 | 改了什麼 |
|---|---|
| **VRN_ENG089_TemplateView v0100**(新)| 把自測迴圈的成果套進制式 U/I(`VIA_HTML_UI` 三入口),**模板一個位元組都不動**;synchronizer 控制;上下游連結冊;新增必上頁;十二檢 |
| VRN_AutoTestLoop v0106(原地改,無版號檔)| 每輪寫完報告就自動建 VRN 模板(落在 `<--out>/template`,永遠在這一輪的輸出夾底下);報告頁頂端橫幅「開中央頁 · 開 synchronizer · 對上一輪新增/異動/消失」;自測門 +③ |
| via_vrn_logic_book v0108 | L4_產出 +1 節點 ENG089(不上冊的話守門 ⑧「每個 VRN_ENG 家族都要被交代」會紅);引擎指標 45 → 46 |
| CGC_MDL149 VCGC v0129 | 一頁交接 +**十六段 VRN 模板**(讀 ENG089 的交接口,本台只翻譯)· 頁 +1 卡 · status +1 行 · +㊳(缺席 = ABSENT、炸掉 = RED 的反面控制);三十八檢 |
| CGC_MDL064 格子 v0493 | +1 站「VRN 模板十二檢」;站名檢數 Veritas 中央控管台 三十七 → 三十八(LL213,只換數字) |

版號補記:批732 / 批733 動過自測迴圈(財報恆等式、沒有框線的表),碼內註記寫 v0105,但 `LOOP_VERSION` 沒跟著改,報告一直印 v0104。本批一起補正,報告從此印 **v0106**。

## 二 · 制式模板怎麼套(模板零改動)

- **建之前先驗模板**:三個入口(啟動頁 `VIA-Complete-System.html` · 中央 U/I `VIA-UI-Standalone-NoServer.html` · `VIA-SYNCHRONIZER-Standalone.html`)逐檔對 `manifest.json` 的 sha256;對不上就不建(BLOCKED,講哪一支)。工作站 git 把換行改成 CRLF 的,換回 LF 再比一次,內容一致照建並點名(同批650:換行 ≠ 內容漂移)。
- **原樣複製到 `ui/`**,檔名不變,模板自己頁與頁之間的相對連結照通。啟動頁逐位元組 = 模板;中央頁與 synchronizer 只**插入**三段(`<!-- VRN-TEMPLATE:… -->` 夾住),拿掉插入段 = 模板原檔(自測 ③ 逐位元組驗)。
  - 預置(`<head>` 之後):synchronizer 共享狀態 `via.sync.state.v2` 的模組冊**只增不減**加一個 `vrn-report-template`。沒存過狀態就用模板自己的 `DEFAULT_MODULES`(建構時從 synchronizer 原始碼抽出來,不另寫一份);VRN 模組已經在(就算被你關掉)→ 一個字都不動;壞 JSON / 舊 v1 → 不寫(自測 ⑨ 用 node 實跑五種狀態)。
  - 資料(`</body>` 之前):這一輪的成果,`type="application/json"`,頁上零連線(借 CGC_MDL160 離線四尺驗,插入段零命中)。
  - 外掛:走模板正式外掛 API——中央頁 `VIA_REGISTER_ADDON`、synchronizer 頁 `VIA_REGISTER_SYNC_ADDON`。
- **由 synchronizer 控制**:中央頁 VRN 面板的開 / 關跟著 synchronizer 模組冊的 `enabled` 走(localStorage + BroadcastChannel `via.sync.v2`,即時)。在 synchronizer 關掉,中央頁面板當場收起;打開就回來;釘選、排序也在 synchronizer。
  - 瀏覽器裡 file:// 頁共用同一份 localStorage,所以 VRN 模組也會出現在你直接開的原版模板 synchronizer 裡(同一份共享狀態,本來就該看得到)。
  - **要收起 VRN 面板請用「停用」(把勾拿掉),不要刪**:停用會一直記著;刪掉的話,下一次開 VRN 模板頁,預置段照只增不減再加回來(它分不出「沒加過」與「被刪掉」)。
- **自適應**:認得的欄畫專屬段(總覽 KPI · 這一輪 · 關卡總表 · 關卡明細 · 欄位規格 · 財報 · 上漲空間 · 附錄 · 相依 · 引擎 · VCGC 尺 …)。**沒人認得的頂層欄一律一欄一段**(「其他欄位:… 自動收」),不吞。逐檔表的欄取每檔記錄鍵的聯集:上游每檔多一個欄,表就多一欄。超過 25 列的表收合;WARN / FAIL / 異動 / 消失的列拉到收合外面,不展開也看得到;收合摘要寫各狀態幾列。

## 三 · 上下游自動連結 · 自動更新 · 新增檢查

- **上游** = 自測迴圈報告 + 產出它的引擎(報告 `engines` 欄,逐支 sha256)+ 模板三入口 + **建構器自己**(本支換版或改碼 → 舊頁判 STALE)。
  報告用「內容簽章」:每輪必變的欄(產生時間 · 工作夾 · 樣本夾 · 最後入庫摘要 · 各輪明細)不算,兩輪結果一樣就是 SAME。檔案本身重寫過另用 `report_sha` 抓:頁上印著產生時間,所以 check 判 STALE、建構也不走「不重寫」捷徑。
- **下游** = 三張衍生頁 + synchronizer 模組 + VCGC 一頁交接(十六段讀 ENG089 的 `handover()`)。
- 每次建構寫連結冊 `VRN_TEMPLATE_LINKS.json`,逐項 NEW / CHANGED / GONE / SAME。**比對基準自動找**:輸出夾自己的上一版;沒有就找同一個上層夾裡上一輪的連結冊。PS 第六步每輪一夾(`VIA_Reports\vrn_autotest\<時間>\`),所以**每一輪自動接上前一輪**,新增 / 異動 / 消失講的是「對上一輪」。
- **新增檢查**:上游新出現的東西(新頂層欄 · 新關卡 · 新檔 · 新欄位規格)逐項點名,而且驗它**真的上了頁**(落在哪一段、那一段有那一列);有一項沒上頁 = 建構 rc1 並點名(反面控制 ⑦:把落點段拿掉,建構必須紅)。
- `check`:上游變了 → STALE;頁被手改或不見 → DRIFT;都對 → OK;沒建過 → rc2。上游、模板、建構器都沒變而且頁都在 → 頁不重寫(冪等)。

## 四 · 跑一次測試文件,成果用制式 U/I 顯示

- **真檔進不了容器**:`C:\測試樣本報告` 的 60 份 PDF + 4 份 DOCX 從來沒掛進 AI 環境(Z51 / Z144)。容器裡跑的是自測迴圈的**標準測試語料**:用名冊檔名合成的 107 檔 PDF / DOCX / TXT / JPG。
- 結果 **AMBER · PASS 358 · WARN 1 · FAIL 0**(29.6 秒),跟前幾次整批跑一模一樣。唯一的 WARN 是 `926708.jpg OCR_REQUIRED`:圖片檔要 OCR,OCR 還沒接,照實標。
- 模板建成 21 段;headless Chromium 實跑:衍生頁**零頁面錯誤** · synchronizer 模組冊第 6 列是 VRN(已啟用、已釘選)· 在 synchronizer 關 → 開,中央頁即時 1 → 0 → 1 · synchronizer 自己的操作紀錄記下「已停用 → 已啟用」。截圖兩張 + 中央頁本體已交給你。
- **跨輪**:同一個上層夾連跑兩輪整批,第二輪自動以第一輪為基準 → **新增 0 · 異動 0 · 消失 0 · 未變 512**(結果一樣就該是這樣);第一輪首建 512 項全算新增。
- 另外一次「把合成的 20 檔當真檔讀」出現 2 條 WARN「no broker」:那是合成檔的檔名本來就沒有券商、又走真檔模式才出現,不是退步。

## 四之二 · 使用者路徑實測(操作員會走的整條路)——抓到一個真 bug

操作員 2026-09-24 追加:「REAL TEST DEBUG OPTIMIZE TEST CONSOLIDATE TEST DEBUG USER-TEST DEBUG ACTIVATE TEST DEBUG TILL IT WORKS PERFECT」。
照 PS 第六步的夾名連跑兩輪(`vrn_autotest\<時間>\` 各一夾),再用 headless Chromium 走一遍操作員的路,13 步:

| # | 步驟 | 結果 |
|---|---|---|
| ① | 報告頁(第六步跑完自動跳出來那頁)頂端有橫幅 | OK · 「對上一輪 新增 0 · 異動 0 · 消失 0」 |
| ② | 點「開中央頁」→ VRN 面板 · KPI | OK · AMBER / PASS 358 / WARN 1 / FAIL 0 / 107 檔 |
| ③ | 側欄「自定義模組」出現 VRN | OK(synchronizer 模組冊帶進來的) |
| ④ | 關卡明細:WARN 那一列在收合外面 · 摘要 · 點開 | OK · 外面 1 列(926708.jpg)· 展開 359 列 |
| ⑤ | 連結段標題講「對上一輪」與增減數 · 新增段講得出「沒有新增」 | OK(修之前:標題沒講對誰比、新增段是一張空表頭) |
| ⑥ | 從面板連結開 synchronizer:模組冊 · 外掛晶片 | OK |
| ⑦ | synchronizer 停用 → 中央頁面板**真的**收起;再啟用 → 回來 | OK(**修之前:紅**) |
| ⑧ | 取消釘選 → 中央頁釘選標記收起;釘回 → 出現 | OK(**修之前:紅**) |
| ⑨ | synchronizer 排序 VRN 往上一格 | OK |
| ⑩ | 按「下載 VRN 資料」→ 真的下載一份 JSON、讀得回來 | OK · 21 段 |
| ⑪ | 中央頁換主題 / 密度 → 面板照常 | OK |
| ⑫ | 手機寬 390 → 頁面不橫向捲 | OK · 390 / 390 |
| ⑬ | 全程零 console error、零 pageerror | OK |

- **抓到的 bug(⑦ ⑧)**:面板本體寫了行內 `display:grid`,**蓋掉了 `hidden` 屬性**——synchronizer 停用 VRN 之後,屬性對了、提示也出來了,
  但 KPI 和表格其實還看得到;釘選標記同一個原因永遠不收。原本的探針只看屬性(`data-vrn-enabled`、`.hidden`),所以一直是綠的。
- **修法**:外掛自己帶一段只作用在 `.vrn-tpl-root` 底下的樣式,`[hidden]` 一律真的藏,版面改用 class、不再寫行內 display;
  標題列在手機寬可換行;JSON 樹自動折行;沒有列的段改成一句話(不畫空表)。
- **防它回來(收進自測)**:ENG089 自測 ⑩ 改成**量高度**判「真的收起再回來」,並加釘選、下載鈕真的下載、手機寬不橫捲;檢數不變(十二檢)。
  反面控制:把 bug 原樣放回去(甚至加 `!important`),⑩ 當場紅,點名「量高度:沒真的收起!」。
- 舊頁當反面控制:同一支使用者路徑測試對修之前的頁跑,⑤ ⑦ ⑧ 三步紅——測試抓得到,修了才綠。

## 四之三 · 最終實測 · HTML U/I 結果報告

操作員同日:「自動傳PR自動批種完成 最後實測要HTML U/I結果報告」。PR #118 開出 34 秒後已由你併進 main(head 795ac45d);
之後的收尾與使用者路徑修正走 PR #119(分支先 commit 再併 main,不 rebase、不強推;那次合併不動任何檔案)。

最終實測全部用最終版程式重跑,每一列都讀真存證 / 真日誌組成驗收報告(與自測迴圈報告同形),再交 ENG089 套進制式 U/I——
**驗收報告本身就是一張 VRN 模板頁**,也順便示範自適應:它多出來的頂層欄(自測摘要 · 格子摘要 · 你的指示 · PR)建構器不認得,照律一欄一段自動收。

| 組 | 內容 | 結果 |
|---|---|---|
| T1 全格子 v0493 | 完整一輪 356 站 + 最終版單跑 VRN 模板站 | PASS 351 · SKIP 6(環境缺件,誠實)· FAIL 0 |
| T2 新件自測 | ENG089 · 自測迴圈 v0106 · 六層冊 v0108 · VCGC v0129 | 12/12 · 3/3 · 17/17 · 38/38 |
| T3 CI 重現 | Windows UAT 各步,只有標準庫的 venv | 8/8(執行橋 ㉖ 缺 duckdb 照實 SKIP,仍 rc0;瀏覽器 UAT 頁錯 0 · 外連 0) |
| T4 使用者路徑 | 報告頁橫幅 → 中央頁 → synchronizer 停用 / 啟用 / 釘選 / 排序 → 收合 → 下載 → 主題 → 手機寬 → 零錯 | 13/13 |
| T5 自測迴圈實跑 | 標準語料 107 檔,兩輪(第二輪自動接上第一輪) | 11 關 PASS · G06 1 WARN(926708.jpg 要 OCR,既有)· 模板兩輪都建成,第二輪對上一輪 0 / 0 / 0 |
| T6 正式庫守門 | 格子 [正式庫] · 外部指紋 · inotify | 3/3 |
| **總** | 464 列 | **AMBER · PASS 457 · WARN 1 · SKIP 6 · FAIL 0** |

唯一的黃是既有的 OCR 未接(Z51 那一類,不是本批);SKIP 是格子本來就照實 SKIP 的環境缺件站。
報告頁與截圖已交給你(中央頁 · 產品頁 · synchronizer)。

## 四之四 · PR #119 之後:Codex 審查 P2 · 版號律(ENG089 v0101 · VCGC v0130 · 迴圈 v0107)

- PR #119 在 21:14:14 由你併進 main(head 0a3dc1f6);最終實測那個 commit(66268665)21:15:19 才推上分支,晚了一分鐘——
  連同下面的修正走下一個 PR(分支先 commit 再併 main,不 rebase、不強推)。
- **Codex 審查 P2(屬實)**:同一個夾重建時,建構器是跟「這個夾的上一版」比,新增段的說明卻一律寫「對上一輪」(連結段標題本來就分對了),
  讓人把手動重建前後的差當成跨輪的差。同一類的用詞也在自測迴圈橫幅 / 主控台行(看有沒有找到上一輪自己猜)與 VCGC 十六段
  (同一個夾重建被印成「首建:找不到上一輪」)——三處一起修,根因只修一次:
  - **VRN_ENG089 v0101**:比對基準的說法一處定義 `basis_text()`(對上一輪 / 對這個夾的上一版 / 首建);`build()` 與 `handover()`
    多回 `compared_to` · `previous` · `basis`,呼叫端照抄。另外帶上 66268665 那一處:走「不重寫」(SAME)也回兩頁路徑。
    自測 ⑥ +同夾重建說法(頁上新增段說明也驗)· ⑪ +跨輪說法(建構回值 · 頁上 · 交接口三處一致),仍十二檢。
    反面控制:同一段腳本對 v0100 跑,同夾重建的說明是「對上一輪沒有新增項目」(錯)、v0101 是「對這個夾的上一版沒有新增項目」。
  - **自測迴圈 v0107**(無版號檔,原地改):橫幅與 [VRN 模板] 行照抄建構器的 `basis`;舊版建構器才退回舊猜法。
  - **VCGC v0130**:十六段照抄交接口的 `basis`,舊版交接口靠 `compared_to` 推;㊳ 加驗三種說法,仍三十八檢。
- **版號律補記(L04)**:v0100 隨 PR #118 併進 main 之後,PR #119 的 86336a94 又原地改了 v0100(當時還不知道 #118 已併)。
  本次起照律出新版:ENG089 v0101、VCGC v0130;v0100 還原成 main 上的位元組、不再動。格子、六層冊、交接口都照尾版律自動換到新版。
- **驗證**:全格子 v0493 再跑一輪 **OK 350 · FAIL 0 · SKIP 6 · TIMEOUT 0**(678 秒,`GRID_20260924_212128.json`;站內實跑:VRN 模板 v0101 11 + SKIP 1(格子境沒有 playwright)· 中央控管台 v0130 38/38 · 第二血統總驗 3/3 · 六層冊 17/17)·正式庫格子守門 / 外部指紋 / inotify 三邊一致零寫入 · ENG089 v0101 帶瀏覽器 12/12 · 契約 19/19 · MDL167 還原 40 支 · 稽核件數新版 = 前版(ENG089 0 · VCGC 3 · 迴圈 6)· LL334 41 條分支零撞號。

## 四之五 · 本輪:自測 · 優化 · 使用者測試第二輪 · 啟用實測(PR #120)

操作員同日:「Self-test debug optimize test debug user-test debug activate test debug till they works perfectly.」
這一輪把 ENG089 v0101 / VCGC v0130 從四個方向再打一遍:自測(含突變反測)、優化(量過才改)、使用者測試第二輪(操作員可能走到的邊角)、
啟用(在正式位置照 PS 第六步的樣子跑,讓 VCGC 讀回來)。每一條都用最終位元組實跑。這一輪修了五處,都是真的會讓操作員看到錯話的地方:

| # | 哪裡 | 怎麼抓到的 | 修法 |
|---|---|---|---|
| 1 | VCGC 頁卡與 status 行寫死「對上一輪」(十六段已照抄 ENG089 的 `basis`,這兩處沒跟上) | 啟用實測:同一個夾重建後,頁卡照樣說「對上一輪」 | VCGC v0130 一處定義 `_vrn_template_basis()`,十六段 · 頁卡 · status 行三處共用;㊳ 加驗原始碼裡不再有寫死的那兩句 |
| 2 | ENG089 走「不重寫」(SAME)時,回的是上一版記錄的數字,配的卻是這一次新算的「對這個夾的上一版」:首建後原封再建印「SAME · 對這個夾的上一版 · 新增 30」,頁上卻寫首建 | **PR #120 Codex 審查 P2**(核對屬實,先重現再修) | SAME = 頁上仍是上一版 → 回值整組照上一版的記錄(比對基準 · 數字 · 新增項 · rc);⑥ 加驗 |
| 3 | 同一根:上一版「新增沒上頁」(rc1),原封再建走 SAME 會回 **rc0** 把問題洗掉(迴圈橫幅的「新增沒上頁」也跟著歸零) | 修第 2 條時自己再讀同一段 | 同上,rc 照上一版;⑦ 加驗原封再建照樣 rc1 並點名 |
| 4 | 讀不動的根(`UNREADABLE`)是模組層字典、從來沒清過(v0100 就這樣):同一個行程裡某次讀不動,之後每次交接都照報「讀不動」 | 審優化那一段時讀到,先重現(第二次已讀得動仍報讀不動) | 交接口每次開頭清空重量;⑪ 加驗 |
| 5 | 總覽「檔案」格:報告沒有 `file_count` 時畫成「0 · 合成語料」——沒有這一欄 ≠ 0 檔(L16) | 本輪驗收報告套進制式 U/I 時,看截圖看到的 | 改成「—」並寫明「報告沒有這一欄」;⑤ 加驗上游少一欄 → 頁上照實寫沒有 |

每一條修正都做了**反面控制**:把修正拿掉的突變副本跑同一份自測,只有對應的那一檢紅(第 1 條 → ㊳,頁卡 / status 行改回寫死各試一次;第 2 · 3 條 → ⑥ ⑦;第 4 條 → ⑪;第 5 條 → ⑤)。

**優化(ENG089 v0101)**:找上一輪 / 交接最新一版原本把 `vrn_autotest` 底下每一輪的連結冊整本讀一遍——工作站一輪一夾會一直累積,
倉又在 OneDrive 上,舊檔可能只是雲端佔位,整夾讀會把它們一個個拉下來(掉球 Z29 同一類)。改成先只 stat(檔案時間),
真正打開的只有最新 5 本(在其中取建構時間最大的;全壞才往下一批)。「共幾版」用 stat 數。⑪ 加 I/O 守門(25 輪只開 ≤5 本)。

實量(夾裡累積 300 輪,各取三次最快;結果兩版完全相同):

| | v0100(main) | v0101 |
|---|---|---|
| 交接口 `handover()` | 0.42 秒 · 打開 301 本 | **0.02 秒 · 打開 6 本**(最新 5 本 + check 再讀最新那一本) |
| 找上一輪 `find_baseline()` | 0.38 秒 · 打開 300 本 | **0.02 秒 · 打開 5 本** |

**使用者測試第二輪(瀏覽器實跑,第一輪 13 步之外的邊角)**:

| 步 | 情境 | 結果 |
|---|---|---|
| ⑭ | 原版模板**自己的** synchronizer(沒有任何插入)也列得出 VRN 模組;在那裡停用 / 啟用 → VRN 中央頁面板真的收起再回來(量高度) | **過**(VRN 頁錯 0) |
| ⑮ | 瀏覽器儲存被封鎖(localStorage 一碰就丟):面板照樣掛上、看得到(沒有狀態 = 預設啟用);插入段不多丟任何錯(與原封模板同條件對照) | **過**(預置照實回報讀不到狀態;多出來的錯 0) |
| ⑯ | 在 synchronizer 按 × 刪掉 VRN 模組 → 模組冊真的沒了、中央頁面板照文件不受控(開著);重開 VRN 頁 → 預置照只增不減加回來 | **過**(錯 0) |
| ⑯b | 先停用再刪:面板先收起 → 刪掉後**即時**回到「不受控 = 開著」(不卡在停用的樣子)→ 重開預置 ADDED | **過**(錯 0) |
| ⑰ | Windows 工作站 git(core.autocrlf)把模板三個入口換成 CRLF:照認並點名 · 照建 · 拿掉插入段 = CRLF 原檔逐位元組 · check OK · 再建 SAME · 瀏覽器實跑 OK · 反面控制(CRLF 之外內容也改)BLOCKED | **過** 7/7 |
| ⑱ | 你的樣本夾叫 `C:\測試樣本報告`:自測迴圈在「中文 + 空白」路徑(`…/路徑 測試/測試樣本報告/<時間>/`)實跑兩輪,第二輪自動接上第一輪;再把第一輪那 13 步(報告頁橫幅 → 中央頁 → synchronizer 關 / 開 / 釘選 / 排序 → 收合 → 下載 → 主題 → 手機寬 → 零錯)整條走一遍 | **過** 13/13(兩輪迴圈都 rc0,第二輪「對上一輪」) |

第二輪沒有抓到產品缺陷,但 ⑰ 暴露一個**自測缺口**:容器裡模板是 LF,「CRLF 仍照認」那條分支十二檢從沒跑過(工作站上才會走到)。
已併進 ENG089 自測(仍十二檢):③ 加 CRLF 模板正路(照認並點名 · 拿掉插入段 = CRLF 原檔 · check OK),⑦ 加 CRLF 之外內容也改 → BLOCKED。
突變反測:把 CRLF 分支拿掉 → 只有 ③ 紅;改成「有 CRLF 就放行」→ 只有 ⑦ 紅。

**啟用實測(正式位置 `VIA_Reports/vrn_autotest/<時間>/`,照 PS 第六步的樣子連跑兩輪 + 同夾重建一次,做完全部移走)**:

| 步 | 結果 |
|---|---|
| 模擬 PS 第六步 20260924_231000:建構器 BUILT · VCGC 交接段說法 = 「首建…」(建構回值 · 交接口 · 十六段三處一致) | 過 |
| 模擬 PS 第六步 20260924_232000:建構器 BUILT · VCGC 交接段說法 = 「對上一輪(…」(建構回值 · 交接口 · 十六段三處一致) | 過 |
| 模擬 PS 第六步 同夾重建:建構器 BUILT · VCGC 交接段說法 = 「對這個夾的上一版(…」(建構回值 · 交接口 · 十六段三處一致) | 過 |
| VCGC status 行(實跑 CLI):說法照抄交接口(同夾重建 = 對這個夾的上一版),不再寫死「對上一輪」 | 過 |
| VCGC 頁卡(整台快照 → page_html 實畫):說法照抄交接口 | 過 |
| 收尾:模擬的輪次夾全部移走(正式報告夾回到原樣) | 過 |
| 六層鏈實跑(MDL172 run --fast):L4 節點 VRN 模板 | 過(節點 GREEN;整條鏈 GREEN 35 · RED 0 · GATED 1 · NODATA 12 · ABSENT 0 · SKIP 0 → GATED,GATED = 等網路同意閘,我不代設;NODATA = 沒有自測門的舊件,照實) |
| VRN 系統管理(尾版)引擎面列得出 `VRN_ENG089_TemplateView_v0101` | 過 |

**本輪 HTML U/I 結果報告**:上面每一列都讀真存證 / 真日誌組成驗收報告,再交 ENG089 套進制式 U/I(報告本身就是一張 VRN 模板頁):
驗收報告 456 列,**GREEN · PASS 450 · WARN 0 · SKIP 6 · FAIL 0**(SKIP = 格子本來就照實 SKIP 的環境缺件站)。報告頁與截圖已交給你(中央頁 · synchronizer);這一張也順手抓到上表第 5 條。

**驗證**:

| 項 | 結果 |
|---|---|
| 全格子 v0493 | **OK 350 · FAIL 0 · SKIP 6 · TIMEOUT 0**(680 秒,`GRID_20260924_220139.json`)。格子跑到一半時 ENG089 又修了三處(第 2–4 條),跑完後再修第 5 條;受影響的站都用最終位元組再跑:VRN 模板十二檢 `--only` OK(格子境沒有 playwright:11 + SKIP 1)· 第二血統總驗 `--only` OK · 中央控管台自測 38/38 |
| 正式庫 | 格子 `[正式庫]` 三本前後一致 · 外部指紋(位元組 + mtime)一致 · inotify 整跑**零次**寫入事件 |
| 新件自測(最終位元組) | ENG089 v0101 **12/12**(帶瀏覽器,6 秒)· VCGC v0130 **38/38** · 六層冊 17/17 · 契約 19/19 |
| 突變反測 | 7/7(ENG089 五個 + VCGC 兩個):每一處修正拿掉,只紅對的那一檢;突變副本跑完即刪,樹上零殘留 |
| 再生鏈 | registry-sync APPLIED(活元件 9729)· 六層冊冊未變 · 正則冊 · 總控頁 · MDL167 還原格子重生的 40 支(有備份)· 一頁交接十六段照實 ABSENT(容器沒有第六步的輪)|
| 稽核 | CGC_MDL158:ENG089 v0101 問題 0;VCGC v0130 三條 SWALLOW 與前版 v0129 同位同數(既有,不是這次加的)|

## 四之六 · 併 main(PR #117 側線第十五段)· 全格子 v0495

本輪推上去之後,main 併進了 PR #117(側線第十五段:VRN 交易所財報模板 VRN_ENG090 · 格子 v0495 · 六層冊 v0109)。PR #120 因此跟 main 衝突,
GitHub 也就沒跑新 head 的 CI。照慣例先 commit 再併 main(不 rebase、不強推):

- 衝突只在四個再生冊 / 頁(元件冊 · 正則冊 · 六層架構冊 · 總控頁):取 main 那一側當底,用倉裡的工具在合併後的樹上重生,不手改。
- 側線那支原名也叫 VRN_ENG089,它照 LL334 讓號成 ENG090;兩支各自獨立(ENG090 不 import ENG089),六層冊 v0109 兩個 L4 節點都在。
- 合併後:ENG089 v0101 12/12 · 側線 ENG090 v0100 22/22 · v0101 23/23 · 六層冊 v0109 17/17 · 契約 19/19 · **全格子 v0495 OK 351 · FAIL 0 · SKIP 6 · TIMEOUT 0**(681 秒,`GRID_20260924_224516.json`;比 v0493 多的一站是側線的新站) · 正式庫格子守門 / 外部指紋 / inotify 三邊一致零寫入 · MDL167 還原格子重生的 40 支(正則冊只差時間戳,一併還原)
- 側線的瀏覽器實測 `uxtest_vrn_finstatements_v0101.js`(不在 CI、不在格子)在這個容器 18/20:⑪ ⑲ 紅。**乾淨的 origin/main 工作樹同樣 18/20**,
  跟 PR #120 無關。根因:容器沒有財報資料,ENG090 走 NODATA,範本名寫「資料 —」,測試改時間戳的正則對不上,「舊資料」造不出來。
  記成掉球 **Z214**(候側線),不在這個 PR 裡改它的程式。它的 ⑱ ⑳(跟批735 VRN 模板在同一份 synchronizer 狀態裡共存)都過。

## 五 · 制式模板的既有缺陷(Z210)——要模板線修

中央 U/I 的同步段呼叫 `toast(...)`,但 `toast` 是另一個 IIFE 裡的區域常數;同步段的範圍裡 `toast` 解析到 `<div id="toast">`(瀏覽器的 window 具名存取)。結果是 **synchronizer 每改一次狀態,中央頁就丟一次 `toast is not a function`**:狀態先套完才丟,功能沒掉,但通知不出來,主控台多一條未攔的錯。

- 證據:ENG089 的瀏覽器實跑**每一次都先拿原封模板對照**(沒有插入的三入口,在 synchronizer 切一個預設模組),原封模板的中央頁就丟這條錯;模板自己的 e2e `test_via_cross_page_sync.py` 沒聽 pageerror,所以一直沒抓到。
- 衍生頁的處置:插入段在外掛掛上時,把外掛 API 給的 `toast`(模板自己的那一支)掛上 `window.toast`。模板修好(`window.toast` 已是函式)這段就不作用。**模板位元組一個都沒動。**
- 模板本身怎麼修要你點頭(L100 正典模板):第一個 IIFE 定義 toast 後加 `window.toast = toast;`,或同步段改呼叫 `window.__viaToast`;重生 manifest;e2e 加聽 pageerror。模板修好那天,ENG089 的對照組會自己印「原封模板對照零錯」。

## 六 · 驗證

| 項 | 結果 |
|---|---|
| VRN_ENG089 自測 | **12/12**(有 node + playwright;⑩ 量高度判真的收起 · 釘選 · 下載 · 手機寬);沒有 playwright 的環境 11 + SKIP 1(瀏覽器那一檢照實 SKIP)|
| 使用者路徑實測 | **13/13**(第四之二節);修之前的頁 ⑤ ⑦ ⑧ 紅(反面控制)|
| 自測迴圈 v0106 自測門 | **3/3**(① VRN/tests 全部單元測試 · ② 合成小批無 FAIL · ③ 模板三頁 + 連結冊落在暫存、報告頁有連結)53 秒 |
| 六層冊 v0108 | 17/17 · 引擎指標 46 |
| VCGC v0129 | **38/38**(registry-sync APPLIED:活元件 9725,新 39)|
| 契約 | 19/19 |
| 格子新站單跑 | VRN 模板十二檢 OK · `[正式庫]` 這 1 站前後三本一致 |
| **全格子 v0493** | **OK 350 · FAIL 0 · SKIP 6 · TIMEOUT 0** · 680 秒(`GRID_20260924_204207.json`);批733 最後一輪 349 → 350(+1 新站)。VRN 模板十二檢那一站在格子跑到一半時 ENG089 又改過一次(BLOCKED 處理),用最終版本 `--only` 單跑再驗一次:OK |
| 正式庫 | 格子自己印 `[正式庫] 三本前後一致`;外部指紋(位元組 + mtime)一致;inotify 監看整跑**零次**寫入事件 |
| 再生物還原閘 | MDL167 還原 40 支格子重生的頁與冊(有備份);刻意入倉的元件冊 / 正則冊 / 總控頁跟最終樹一起提交 |
| CI 重現 | 本機用只有標準庫的 venv(Python 3.11)把 Windows UAT 每一步跑一遍:編譯 · node --check · 系統管理器 10/10 · 執行橋 25 + SKIP 1(缺 duckdb 誠實 SKIP)· 同步狀態 10/10 · VAP 2/2 · 契約 19/19 · 瀏覽器 UX rc0 |

## 七 · 掉球

- **Z210** 制式模板既有缺陷(toast 具名存取)· 候(模板線)· 提議見第五節。
- **Z214** 側線 VRN 財報模板瀏覽器實測 ⑪ ⑲ 在沒有財報資料的環境一定紅(範本名「資料 —」對不上測試的時間戳正則)· 候(側線)· 見第四之六節。
- **Z211** `via-vrnrun` 跑完自動跳出來的是報告頁;要**直接跳 VRN 模板頁**得改 .ps1(L70 逐次許可)· 等你定:① 維持現狀(報告頁頂端點橫幅)② 准改 .ps1,跳報告頁之後再開模板中央頁(在才開,-NoOpen 照舊不跳)。
- Z72 補記:第六步起每輪自動建模板,實檔跑一次就有實檔版的模板頁。

## 八 · 工作站(一貼即用)

同批733 那一段,只換成認批735 本輪的檔(`functional modules\VRN\VRN_ENG089_TemplateView_v0101.py`;PR #120 還沒併進 main 就自動改拉分支)、分支叫 `b735-時間`;跑的是 ENG089 尾版(照尾版律,不寫死版號)。`via-vrnrun` 第六步跑完會自動建模板;跑完再開最新那一版的中央頁、印一次交接口。**本批沒有改任何 .ps1。**

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
    if (git status --porcelain --untracked-files=no) { git stash push -m "workstation-local-before-b735" }
    git stash list | Select-Object -First 3
    git fetch https://github.com/tonykuni/movies-dataset main
    git merge-base --is-ancestor main FETCH_HEAD 2>$null; $ff = ($LASTEXITCODE -eq 0)
    if (-not (git rev-parse -q --verify refs/heads/main)) { git switch -c main FETCH_HEAD } elseif ($ff) { git switch main; git merge --ff-only FETCH_HEAD } else { git switch -c ("main-latest-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    if (-not (Test-Path ".\functional modules\VRN\VRN_ENG089_TemplateView_v0101.py")) {
        "  [拉取] main 還沒併 PR #120 → 改拉批735 的分支(它 = main + 本輪,本機另開 b735-時間,不動 main)"
        git fetch https://github.com/tonykuni/movies-dataset claude/awesome-bardeen-h0wm5v
        if ($LASTEXITCODE -eq 0) { git switch -c ("b735-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    }
} else { "  [解卡] 人寫件卡在衝突,不自動處理,先停:" + ($held -join " · ") }
$tv = (Get-ChildItem ".\functional modules\VRN\VRN_ENG089_TemplateView_v*.py" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1).FullName
if ($held.Count -eq 0 -and $LASTEXITCODE -eq 0 -and (Test-Path .\Invoke-VIA-VRN-v0104.ps1) -and $tv -and (Test-Path $tv)) {
    "  [後] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
    $log = "$env:TEMP\vrnrun_b735.txt"
    via-vrnrun 2>&1 | Tee-Object -FilePath $log
    Invoke-VIAPython -Family vrn $tv status 2>&1 | Tee-Object -FilePath $log -Append
    $run = Get-ChildItem .\VIA_Reports\vrn_autotest -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    $page = if ($run) { Join-Path $run.FullName 'template\ui\VIA-UI-Standalone-NoServer.html' } else { '' }
    if ($page -and (Test-Path $page)) { "  [VRN 模板] 中央頁 " + $page; via-open $page } else { "  [VRN 模板] 這一輪沒有模板頁(看上面 V6 的 [VRN 模板] 那一行)" }
    Select-String -Path $log -Pattern '\[Celeritas\]|\[加速器\]|平行池|\[進度\] \d+/6|\[V[1-6]\]|\[ROUND|\[DONE\]|\[VRN 模板\]|\[ADJ\]|\[財報\]|rc=|總計|via-open' | ForEach-Object { $_.Line }
} else { Write-Host "  [拉取] main 跟批735 分支都沒拉到(上面幾行就是原因),先停" -ForegroundColor Red; git status --short | Select-Object -First 15 }
```

## 九 · 要貼回什麼

1. V6 的 `[VRN 模板]` 那一行(狀態 · 對上一輪新增 / 異動 / 消失 · 中央頁路徑),以及 `status` 印的「最新一版 · 共幾版 · OK / STALE」;
2. 中央頁 VRN 面板的截圖(實檔版);再到 synchronizer 頁把「VRN 研報自測成果」關掉,中央頁面板有沒有當場收起(一句話就好);
3. Z211 你選 ① 或 ②;Z210 模板要不要修(要修我就出模板新版 + manifest + e2e 聽 pageerror)。
