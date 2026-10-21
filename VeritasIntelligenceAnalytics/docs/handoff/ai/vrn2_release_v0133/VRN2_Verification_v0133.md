# VRN-2 v0133 容器實測紀錄(2026-10-21 · 前後端連結 · U/I window I/O 輸入 · 三類只開個股報告/訊息)

操作員令(2026-10-21):「做好啟動系統實測準備 … 檢查用 ActivateVRN-2.ps1 啟動前後端並連結 · 讓使用者在 HTML 上用 window I/O 輸入檔案夾或檔案(pdf / word / txt / image / 檔案夾)·
分為三種:個股報告/訊息 · 產業報告/展望 · 其他投資報告 · 現在進行的是個股報告/訊息,其他功能關閉 · 準備好測試無誤後留意是否都有註冊成功 · 上傳 GitHub、衝突一併解決 · 下一步換輸入檔案 audit `C:\測試樣本報告`」。
四系統(VRN-1 · VRN-2 · VDF · VCGC)各自獨立、各有自己的 MAIN;本輪只動 VRN-2 的啟動器與 U/I 處理器。

## 1. 主體不動(逐位元組)

`VRN2_Release_v0133.json` 內嵌清單與 v0132 比:管理器鏈 v0231 → v0239、ENG397 v0127、ENG062 v0114、獨立驗證器 v0102、U/I 處理器 v0102、工具橋 v0101、OCR 橋 v0100、規則目錄
**16 支 sha256 全部相同**;新增 `VRN2_UIAction_v0103.py`(sha256 `3e478229c8e1…` · v0102 留在原處 · 只增不改)與交接報告 `VRN2_Handover_v0133.md`。改動的只有啟動器本身(v0132 → v0133)。

| 檔 | SHA-256 |
|---|---|
| `ActivateVRN-2_v0133.py`(1,902,460 bytes) | `d9411dcb333ba253dfc5eb640ddcf5ed3ae6a75f5b0000e25708276d06f45c10` |
| `ActivateVRN-2_v0133.zip`(成員 `ActivateVRN-2.py`) | `78997365c230ae7ecf712b4cf7e8e361714ea7d5ca89412f1a2e034a375ce303` |
| 一鍵程式碼(`VRN2_OneClick_v0133.md` 內 · 即 ActivateVRN-2.ps1)| `149832822f95…`(一鍵自己核對 · Codex #550 + #551 修正後;#550 修正後 `21ab900abfd0…` · 修正前 `9008c34b70bc…`)|

## 2. 自測

| 項目 | 結果 |
|---|---|
| 啟動器 `ActivateVRN-2.py --selftest` | **31 / 31**(比 v0132 多 4 條:內嵌處理器 v0103 雜湊 · 處理器自測 · 步驟次序 ②b / ⑫b · ②b 來源寫 VRN2_SSOT 新一版、設定檔還沒寫也能稽核、`--source` 指不在的夾 → 紅)|
| U/I 處理器 `VRN2_UIAction_v0103.py --selftest` | **11 / 11**(URL 解析 · 型別表 = ENG397 EXT · 稽核分類 · 選資料夾 / 選檔案 → 暫存 · 拒絕未開放兩類 · 取消 · `--set-source` · v0102 的 run / run-clean / restore-archive 照舊)|

## 3. 沙盒樹端到端(倉內 19 份真實 PDF · 個股 14 · OCR 隔離環境是真的 · VRN-1 = 本機倉)

| 情境 | 輸入 | 結果 |
|---|---|---|
| A1 預設來源 | 環境 `VIA_VRN_INPUT` → 19 份 | ②b 綠(檔 19 · 個股範圍 14 · 範圍外 5)· ⑥c 灰(非 Windows 不註冊 · 設定檔已寫 · 處理器 v0103)· ⑥b 範圍夾 14 · ⑦ **14 / 14 全綠** · ⑧ 完成 紅 0 黃 4 · ⑨ 上船(fast-forward)· ⑪ 錯值 0(年度數據 4,905)· ⑫ 事實 4,653 / 4,905 · ⑫b 綠「新放進面板」· **註冊核對 全部登記成功** |
| P1pick U/I 選資料夾(測試掛鉤) | 子集 9 檔 = PDF 6 · Word 1 · TXT 1 · 影像 1 | 稽核 個股 5 · 範圍外 1(檔名規則來自 `VRN_SystemManager_v0231.py`)· 非 PDF 3(已收下 · 本版主體只擷取 PDF)· U/I 區塊「換掉同一塊」|
| P1 重跑(不帶環境變數) | 讀 `VRN2_Input_latest.json` | ②b 綠「U/I 選的(資料夾)」· 寫 VRN2_SSOT 新一版 · ⑥b 範圍夾只剩 5 · ⑦ 5 / 5 · ⑧ 完成 · ⑪ 錯值 0 · ⑫ 2,056 / 2,214 |
| P2pick U/I 選檔案(測試掛鉤) | 2 PDF + 1 txt | 複製到 `input_pick\<時間>\` · 稽核 檔 3 · 個股 2 · 非 PDF 1 |
| P2 重跑 | 暫存夾 | ②b 綠「U/I 選的(檔案 → 暫存夾)」· ⑦ 2 / 2 · ⑧ 完成 · ⑪ 錯值 0 · ⑫ 833 / 848 |
| R / R2 | `vrn2://pick?cat=industry` · `cat=other` | 處理器拒絕 rc 3 ·「尚未開放(現在只做 個股報告/訊息)」|
| audit | `vrn2://audit` | 綠 · 重新稽核暫存夾 · 輸入歷史 `VRN2_Input_History.jsonl` 共 6 筆(環境 → 掛鉤 → 資料夾 → 掛鉤 → 檔案 → 重新稽核)|

③ 環境檢查在沙盒是紅(`--no-install` · 加速器要的 7 個套件沒裝 · v0130 ~ v0132 沙盒同一燈 · 使用者機器 ③ 會補裝)—— 不是本輪的改動。

### 3.1 U/I 真瀏覽器(Chromium · Playwright)

| 測試 | 頁 | 結果 |
|---|---|---|
| 輸入區塊 `ui_input.js`(14 條) | A1 · P1 · P2 · 一鍵情境頁 | **14 / 14 × 4**:只有一塊 · 三類 radio(個股已選、另外兩類 disabled 且點不動)· 三個 vrn2:// 按鈕(`pick?kind=folder&cat=stock` · `pick?kind=files&cat=stock` · `audit`)· 稽核文字含來源夾 · 在 190px 面板內、「這次不上船」之後「開啟」之前 · 原 4 個動作不變 · 分頁腳本照常 · 手機寬度可見 · 無腳本錯誤 |
| 既有 U/I `ui_test.js`(35 條) | 一鍵情境頁 + 它的 output 冊 | **35 / 35**:4 個 vrn2:// 動作 · nopush 切換 · 12 個分頁 · 驗證過的輸出每格 = 年度數據冊 · 凱基 2637 目標價 104.0 · CSV 下載 · 指紋不同不套用 · 無腳本錯誤(v0133 的區塊沒把任何舊功能擠掉)|

## 4. 一鍵(使用者機器情境 · 沙盒 · pwsh 7.4)

Downloads 是 **v0132** 啟動器 · 發行夾 `vrn2_release_v0133` 在 GitHub 分支 · `$env:VRN2_SOURCE` 指向樣本夾 · 貼「一行」:
一鍵程式碼 SHA-256 `149832822f95`(Codex #550 + #551 修正後的最終版;#550 修正後 `21ab900abfd0` 那一輪結果相同;修正前 `9008c34b70bc` 的紀錄在 `logs_v0133.zip/scen_oneclick_v0132_to_v0133_pre_codex550.log`)相符 → ③ 舊啟動器備份 `ActivateVRN-2_v0132_<時間>.py.bak` · 取 v0133(雜湊相符)→ ①~⑫ 全走(②b 綠「啟動器 --source」· ⑦ 14 / 14 · ⑧ 完成 · ⑨ 上船 · ⑪ 錯值 0 · ⑫ 綠 · ⑫b 綠)→
**⑤b 前後端連結檢查**:
* `[YELLOW] ⑤b U/I 有輸入區塊,但 vrn2:// 沒註冊(HKCU)` —— 容器是 Linux,沒有 HKCU,所以啟動器 ⑥c 是灰、一鍵 ⑤b 是黃;**在 Windows 上 ⑥c 會寫 HKCU 並讀回核對,⑤b 應為綠**(黃燈的下一步寫在燈上:重跑啟動器或用 `$env:VRN2_SOURCE`)。
* `[GREEN] ⑤b 目前輸入 · 個股報告/訊息 · <樣本夾>(啟動器 --source)· 檔 19(PDF 19 · Word 0 · TXT 0 · 影像 0)· 個股範圍 14 · 範圍外 5`
* 修正前:`NEXT: [GREEN] VRN-2 一鍵 v0133 跑完 …`(⑤b 黃卻 GREEN —— Codex P1 抓到的問題)
* **修正後**:`NEXT: [YELLOW] VRN-2 ⑧ 本輪完成 · 但 vrn2:// 沒註冊(HKCU)→ U/I 按鈕不會動 · 在 Windows 重跑一次啟動器(⑥c 會註冊並讀回核對)或用 $env:VRN2_SOURCE · 把 ⑤b 那兩行貼回 · … · 啟動器 rc 0 · 143 秒`;一行(boot)結尾把燈帶回子行程 → **行程 rc 2**(再跑一次確認:①~⑫ 仍全綠 · NEXT YELLOW · rc 2)。
①~⑫ 仍全綠(⑦ 14 / 14 · ⑧ 完成 · ⑪ 錯值 0 · ⑫ 4,653 / 4,905 · ⑫b 綠 · 註冊核對 全部登記成功);黃只來自 ⑤b,在 Windows(⑥c 寫 HKCU 並讀回核對)應為 GREEN。

## 4b. Codex #550 兩個發現 → 一鍵修正(只動一鍵程式碼 · 啟動器 v0133 與主體不動)

| 發現 | 問題 | 修法 |
|---|---|---|
| P1 最後的燈沒算 ⑤b | ⑤b 黃 / 紅(vrn2:// 沒註冊 · 指向別的處理器 · U/I 沒區塊)時 NEXT 仍 GREEN、rc 0 | `$lamp`:⑧ 不綠或 rc≠0 或 ⑤b 紅 → RED;⑧ 綠 + 驗證錯值 0 + ⑤b 綠 + 有輸入紀錄 → GREEN;其餘 YELLOW(rc 2)· 訊息寫明是 ⑤b 哪一種;一行的 boot 結尾 `exit $LASTEXITCODE`,燈帶回子行程 rc(cmd 的 `%ERRORLEVEL%`)|
| P2 處理器只比檔名 | HKCU 指令只要含 `VRN2_UIAction_v0103.py` 就算接上(舊的 / 搬走的檢出 / 不存在的檔也過) | `Chk5b`:把指令解析成「python」「處理器」兩段 · 處理器整條路徑正規化後 = 本機 VRN-2 程式夾的 v0103 且檔在(或那一夾有啟動器本輪寫的 `VRN2_UIAction_Config.json` v0133)· python 檔在 · 訊息寫明要的是哪一條 |

單元測試 `tools/test_chk5b.py`(從 ps1 抽出 `Chk5b` 與 `$lamp` / `$msg` 原文 · pwsh 7.4 · 假 HKCU 指令 / U/I / 輸入紀錄):**19 / 19**
—— 正確 → GREEN rc 0;同檔名別的檢出 → RED「舊的 / 搬走的檢出」+ NEXT RED rc 1;不存在的檔 → RED;舊處理器 v0102 → RED;沒註冊 + 區塊在 → YELLOW + NEXT YELLOW rc 2「vrn2:// 沒註冊」;沒註冊 + 沒區塊 → RED;python 不在 → RED;沒輸入紀錄 → YELLOW「沒有輸入紀錄」;路徑含 `..` → 正規化相同 GREEN;別的夾但有 v0133 設定檔 → GREEN;設定檔是 v0132 → RED;python 別的夾 → GREEN 註明不同夾;驗證有待核對 → YELLOW;啟動器 rc 1 → RED;沒引號 → RED「解析不出處理器」。(紀錄 `logs_v0133.zip/chk5b_unit_v0133.log`)

### 4c. Codex #551 再兩個發現(都是 P2)→ 同一支一鍵程式碼再修

| 發現 | 問題 | 修法 |
|---|---|---|
| 一行(boot)的早退 `return` rc 0 | 不是 git 倉 / 讀不到 GitHub / SHA 不對 三個紅燈 `return` → `powershell -EncodedCommand` 仍 rc 0 | 三個紅燈改 `exit 1`;一鍵自己的四個早退紅燈(找不到 VIA 根 / python / 讀不到 v0133 / 雜湊不對)也先設 `$global:LASTEXITCODE = 1`;③ 發行夾缺 zip / 發行冊 → 紅燈 return(以前會讓 `Expand-Archive` 丟例外);boot 用 `try / catch` 包住整段程式碼,例外逃出來 → `[RED] 一鍵執行中斷` + rc 1 |
| ⑤b 沒檢查 `"%1"` | HKCU 指令 python / 處理器都對、但少了 `"%1"` 或被換成固定網址 → 點按鈕網址送不到處理器,⑤b 卻綠 | `Chk5b` 第三段必須是 `%1`(`$u1Ok`)才算綠;不是 → RED 並列出第三段是什麼 |

單元測試 `tools/test_chk5b.py` 加 3 條 → **22 / 22**(少了 `"%1"` → RED「少了 "%1"」· 第三段是固定網址 → RED 列出 `vrn2://run` · 正確指令 `u1Ok` 綠訊息寫「帶 "%1"」)。

一行(boot)失敗路徑實測(pwsh 7.4 · 假 GitHub = 本機 bare 倉 · `logs_v0133.zip/boot_fail_[a-e]_v0133.log`):

| 情境 | 結果 |
|---|---|
| (a) `VRN2_ROOT` 不是 git 倉 | `[RED] … 不是 git 倉或找不到 git` · **rc 1** |
| (b) 分支上的一鍵程式碼被改一個字(`$NoPush` 值)| `[RED] 一鍵程式碼 SHA-256 不對(…)· 不執行` · **rc 1** |
| (c) 分支 / 路徑都讀不到 | `[RED] 讀不到 GitHub 分支 … 的一鍵程式碼` · **rc 1** |
| (d) 發行夾只有 md、沒有 zip / 發行冊 | 以前:`Expand-Archive` 丟例外 · rc 0;現在:`[RED] ③ GitHub 分支的發行夾 … 缺 ActivateVRN-2_v0133.zip / VRN2_Release_v0133.json` · **rc 1** |
| (e) 完整發行夾 · 本機沒啟動器 · python 是 `/bin/false` | 下載 v0133 雜湊相符 → 啟動器跑不起來 → `NEXT: [RED] VRN-2 有紅燈(… 啟動器 rc 不是 0)` · **rc 1** |

## 5. 註冊核對(操作員要的「是否都有註冊成功」)

啟動器收尾印一行 `[計] 註冊核對 · ⑤ 元件登記 GREEN · ⑥c U/I 操作協定 <燈> · ② 定位 VRN-2 程式夾 GREEN · 處理器 VRN2_UIAction_v0103.py · 全部登記成功`;
⑥c 在 Windows 寫 `HKCU\Software\Classes\vrn2\shell\open\command` 後 **讀回核對**(不同 → 黃、寫明讀到什麼);一鍵 ⑤b 再從 HKCU 讀一次,核對指向 `VRN2_UIAction_v0103.py`、U/I 有 `id='vrn2-input'` 與三類標籤。
容器內三處都跑到:⑤ 綠 · ② 綠 · ⑥c 灰(非 Windows)· 一鍵 ⑤b 黃(同一原因)。

## 6. 本版照實說的限制

* **非 PDF(word / txt / 影像)**:U/I 會收下、稽核會逐型別點數並寫「已收下 · 本版主體只擷取 PDF」;VRN-2 主體(ENG397 · 管理器 vrn2scope)這一版只擷取 PDF,不假裝有處理。
* **產業報告/展望 · 其他投資報告**:U/I 灰掉「尚未開放」,處理器也拒絕(rc 3);只開 個股報告/訊息。
* ③ 環境檢查沙盒紅是 `--no-install` 的既有燈(見 §3)。
* 一鍵 ⑤b 的 HKCU 核對只能在 Windows 變綠(§4);修正後 ⑤b 不綠 NEXT 就不綠 —— Linux 沙盒的一鍵 NEXT 因此是黃(rc 2),這是照實說,不是退步。

## 7. 下一步(操作員)

在 Windows 貼一鍵(或 `$env:VRN2_SOURCE = 'C:\測試樣本報告'` 後貼)→ 看 ⑥c 讀回核對 · 註冊核對 · ⑤b 三燈 → U/I 左側「輸入」📁 選擇檔案夾 → `C:\測試樣本報告` → 區塊顯示稽核(檔 / 個股範圍 / 範圍外 / 非 PDF)→「▶ 完整重跑」。
