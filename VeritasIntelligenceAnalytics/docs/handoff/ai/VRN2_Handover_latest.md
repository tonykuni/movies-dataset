# VRN-2 交接報告 · ActivateVRN-2 v0122 · 2026-10-18

> 給下一個 AI 工作階段:先讀本檔,再讀使用者貼回的貼包(≤300 行,結尾 NEXT:)。不要重讀整份程式;要看程式先用 VCGC 省 Token 卡(`read` / `slice` / `chain`)。
> **重要**:v0122 在 Claude Code 雲端容器(repo `tonykuni/movies-dataset` 分支 `claude/optimistic-goodall-yhalc5`)以 repo 內 19 份真實 PDF 實測;**使用者機器最後一次實跑仍是第 35 輪(v0118)**。下一步 = 使用者執行 v0122。

---

## 1. 系統定義(已鎖定 · 本輪未改)

- **VRN-2** = 獨立子系統:自己的 MAIN(`ActivateVRN-2.py` → `VRN-2 SystemManager`)、自己的 SSOT(`VRN2_SSOT_v####.json`)、自己的 U/I 協定(`vrn2://`)。三系統對等(L120):VCGC / VDF / VRN 互不改對方的正本、冊、號、檔,只讀監控。
- **VRN-1** = 另一團隊(`C:\Users\tonyk\VIA-VDF-VRN`)。可互相學方法,**不照抄程式碼**(本輪:學 VRN-2 自己的雙讀法精神,另寫第二讀取器逐值對欄;v0232 不複製 v0231 程式,用「同一段程式碼重新綁定」)。
- **範圍**:只做個股報告 → FILENAME · 首頁(本文 + 資訊區)· 年度財報頁(年度財報及數據分解)· 100% 還原 · 一標題四重點 · 輸出驗證無誤 · U/I 自動跳出且可操作。
- **治理**:只增不減(新版號 · 前版不動)· 成功即鎖、只准變好 · 精準 AST 錨點修正 · 不產生九頭龍 · 每版過修正閘 · 漏斗原則 · **每個 PY / PS 指令接加速器 · 指令第一步提高 CPU / DRAM 效能**(2026-10-18 使用者令)。

---

## 2. 檔案位置(使用者機器)

VIA 根目錄:`C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`(簡稱 `<ROOT>`)

| 類別 | 位置 | 說明 |
|---|---|---|
| **啟動器(MAIN 入口)** | `C:\Users\tonyk\Downloads\ActivateVRN-2.py` | **v0122** · 一鍵完成全部步驟 · 雜湊見 `docs/handoff/ai/vrn2_release_v0122/VRN2_Release_v0122.json` |
| 程式夾 | `<ROOT>\functional modules\VRN\` | 管理器鏈 / 引擎 / 摘要器 / 處理器 |
| **VRN-2 設定冊** | `…\VRN\SSOT\VRN2_SSOT_v0100.json` | 來源夾 · 範圍 · 交付項 · 取用規則 · 漏斗參數(本輪未改) |
| 輸入設定冊 | `…\VRN\SSOT\VRN_Config_v####.json` | 最新版 `input_dir` 指向範圍夾;`vrn2_source_dir` 記原來源 |
| 原始樣本 | `C:\測試樣本報告` | 97 份 PDF |
| 個股範圍夾 | `<ROOT>\VIA_Reports\vrn2\scope_in\` | 每輪自動同步(只放個股報告) |
| 範圍冊 | `<ROOT>\VIA_Reports\vrn2\VRN2_Scope_latest.json` | stock / non_stock |
| **輸出冊** | `<ROOT>\VIA_Reports\vrn2\output\` | `VRN2_BasicInfo / FinancialData / Summary_latest.{json,csv,parquet}` · **v0122 新增 `VRN2_Rejected_latest`(剔除冊 · 每筆帶理由)** · FinancialData 新增 `VERIFY`(對欄 / 未定位 / 空值記號)、`ITEM_RAW`(科目清理前原字串) |
| **U/I** | `<ROOT>\VIA_Reports\vrn2\VRN2_UI_latest.html` | 左側操作面板 + 右側 10 分頁(新增「剔除冊」)· 每輪自動跳出 |
| 切割檢視 | `<ROOT>\VIA_Reports\vrn2\p1view\P1VIEW_latest.html / .md` | AI 讀 `.md` |
| 完成判定 | `<ROOT>\VIA_Reports\vrn2\VRN2_Completion_latest.json`(+ `_Rounds.jsonl`) | v0122 多一項「輸出值驗證」 |
| 啟動紀錄 | `<ROOT>\VIA_Reports\vrn2\VRN2_Activate_latest.json` | v0122 加 `par`(平行段各步實測秒數 · 下輪排序用)/ `par_workers` / `par_wall` |
| 驗收明細 | `<ROOT>\VIA_Reports\vrn2\VRN2_Acceptance_latest.{json,csv}` | |
| 快取 | `…\vrn2\p1_cache\` · `acc_cache\` · `ocr_cache\` · `summary\` | 刪 `p1_cache` = 全部重新擷取 |
| 備份 | `…\vrn2\backup\<時間>\` | 鎖定時備份 |
| U/I 動作紀錄 | `…\vrn2\ui_actions.log` | 含被拒絕的網址 |
| 鎖定 | `…\VRN\registry\VRN2_Lock_<時間>.json` · `VRN2_Lock_latest.json` · `VRN2_Stock_Lock_latest.json` | |
| 成功模組登記冊 | `…\VRN\registry\VRN2_Module_Success_Register.json`(+ `_History.jsonl`) | 判定完成才寫 · v0122 起登記管理器 v0232 |
| 元件登記冊 | `…\VRN\registry\VRN2_Component_Register_v####.json` | 暫編 · 待 VCGC 核號 |
| 補裝帳本 | `…\VRN\registry\VRN_PipLedger.json` | PyPI 沒有的不再重試 · 網路錯誤 24h 不重試 |
| 封存夾 | `…\VRN\_archive_vrn2\` + `ARCHIVE_MANIFEST.jsonl` | ⑩ · v0122 起**不搬 GitHub 上的檔、不搬現役版仍引用的檔** |
| 隔離區 | `…\VRN\_quarantine\` | 落地自測失敗的檔 |
| U/I 處理器 | `…\VRN\VRN2_UIAction_v0102.py` + `VRN2_UIAction_Config.json` | v0102 帶加速器橋 · 設定檔多記 `handler` |
| 協定登錄 | `HKCU\Software\Classes\vrn2` | 只寫目前使用者 · 不碰 `via://` |
| OCR 隔離環境 | `C:\Users\tonyk\envs\vrn2_ocr\` + 橋 `VRN2_OCRBridge_v0100.py` | 主環境不裝 OCR 套件 |
| **交接報告** | `<ROOT>\docs\handoff\ai\VRN2_Handover_latest.md`(+ `VRN2_Handover_v0122.md`) | ⑨ 上船時自動落地(與 repo 內同一份) |
| 本輪證據 | `<ROOT>\docs\handoff\ai\vrn2_release_v0122\` | 發行清單(雜湊)· 驗證報告 · U/I 實測結果 |
| GitHub | `tonykuni/movies-dataset` | ⑨ 只提交 VRN-2 程式(含管理器前版鏈)/ 設定冊 / 交接報告 |

---

## 3. 版本紀錄

### 3.1 現役版本(v0122 內嵌 · 啟動時依序自動落地)

| 元件 | 版本 | 大小 | SHA-256(前 12) | 本輪 |
|---|---|---|---|---|
| ActivateVRN-2.py | **v0122** | 見發行清單 | 見發行清單 | 新 |
| VRN-2 SystemManager(前版) | v0231 | 215,605 | `ddff2743b478` | 一起內嵌(使用者機器尚未落地過) |
| VRN-2 SystemManager(尾版) | **v0232** | 43,966 | `42e682ba5074` | 新(薄尾) |
| VRN_ENG397_P1Segment(擷取) | **v0127** | 180,699 | `c2e8e39e5584` | 新 |
| VRN_ENG062_SummarizerV1(摘要) | v0112 | 62,297 | `e6d73e29fc48` | 未變 |
| VRN2_UIAction(U/I 處理器) | **v0102** | 5,180 | `56d5b20689e3` | 新(v0101 號保留給舊環境 ④ 自動產生的那支) |
| VRN2_OCRBridge(OCR 橋) | v0100 | 4,778 | `4b21f0694d0e` | 未變 |
| rule_catalog_runtime.json | — | 449,121 | `e5b881716c84` | 未變 |

### 3.2 版本鏈

| 啟動器 | 管理器 | ENG397 | ENG062 | 處理器 | 主要內容 |
|---|---|---|---|---|---|
| v0110 – v0118 | v0221 – v0228 | v0119 – v0124 | v0107 – v0111 | — | OCR 隔離 · 假綠校正 · 雙讀 · 恆等式 · 冪等閘 · 範圍聚焦 · 三本冊 · 漏斗 · ⑨ 上船(**使用者機器實跑到這裡**) |
| v0119 – v0120 | v0229 – v0230 | v0125 – v0126 | v0112 | — | 對齊口徑統一 · 快取 · 成功登記 · 精簡 · ⑩ 封存(只在沙盒) |
| v0121 | v0231 | v0126 | v0112 | v0100 | U/I 左側面板 + 9 分頁 · `vrn2://` · 補裝帳本(只在沙盒) |
| **v0122** | **v0231 → v0232** | **v0127** | v0112 | **v0102** | 輸出值驗證 · 平行段 · 守門(見第 7 節) |

> 使用者機器上的管理器鏈:GitHub 有 v0114–v0153(VCGC 側 VRN 線);本機另有 VRN-2 的 v0154–v0228(未上 GitHub)。v0229 / v0230 從未落地 → v0231 的前版會是 **v0228**;v0122 落地 v0231 時先自測(前版 v0228),失敗即隔離、不落地 v0232。

---

## 4. SSOT 現況

### 4.1 `VRN2_SSOT_v0100.json`(本輪未改)

| 欄位 | 值 |
|---|---|
| system / owner / independent | `VRN-2` / `VRN-2 SystemManager` / `true` |
| source_dir | 第一次執行時取自 `VRN_Config.input_dir`(使用者機器 = `C:\測試樣本報告`) |
| scope / scope_dir | `stock_only` / `<ROOT>\VIA_Reports\vrn2\scope_in` |
| deliverables | FILENAME · 首頁(本文 / 資訊區)· 年度財報頁 · 100% 還原 · 一標題四重點 · 輸出驗證 · HTML U/I |
| funnel | T0 文字層 → T1 換引擎 → T2 OCR 200 DPI → T3 OCR 325 DPI → T4 待人工 · `ocr_min_conf 0.85` · `ocr_min_chars 40` · `max_tier T3` |

### 4.2 其他冊

| 冊 | 現況 |
|---|---|
| `VRN_Config_v####.json` | 每輪若 `input_dir` 不是範圍夾就出新版(只增不減)· 平行段中只有範圍聚焦會寫(九頭龍守門允許設定冊 +1 版) |
| `VRN_PipLedger.json` | v0121 起;使用者機器預計記入 PyPI 沒有的 3 個與網路失敗的 3 個 |
| `VRN2_Module_Success_Register.json` | 尚未在使用者機器產生(要 ⑧ 完成) |
| `VRN2_Rejected_latest`(新) | 每輪重寫 · 剔除的值 + 理由(主冊只含驗證過的值) |

### 4.3 待 VCGC / 操作員裁決(不由 VRN-2 自己改)

1. **管理器檔名家族撞線**:`VRN_SystemManager_v####` 同時是 VCGC 側 VRN 線(GitHub v0114–v0153)與 VRN-2(本機 v0154 起)。⑨ 上船後 GitHub 尾版會變成 VRN-2 的管理器 → 請操作員裁決:改名(例:`VRN2_SystemManager_v####`)或確認 VRN-2 即 VRN 的接續。v0122 已加撞號守門(同名不同內容不提交)。
2. **引擎編號撞號**:VRN-2 的 `VRN_ENG397_P1Segment` / `VRN_ENG396_AssetIndex` 與 repo 既有 `VRN_ENG397_PluginHub_v0100` / `VRN_ENG396_ReportEntities_v0100` 同號不同物(「不同來源不得因值相同合併編號」)→ 交 VCGC 核號。
3. 元件登記冊「暫編 VRN2-<類>-####」未核號 · `VRN2_SSOT` 未登 VCGC 書冊目錄 · VRN-2 收尾需求未登中央需求冊(本輪未動 VCGC 冊:L120 三系統對等,由操作員決定是否登錄)。

---

## 5. 完成判定(⑧)

| 條件 | 擋完成? |
|---|---|
| 實測退步 · 交互驗證 JSON ↔ CSV ↔ 燈號 · 鎖定 + 備份 · 冪等 | 紅擋 |
| ② 覆蓋 ≥97% · ③ 數字回原文 · ⑤ 一標題四重點 · ⑥ AUDIT 新輸入 · 個股四項 | 紅擋 |
| ① 計算驗證 | 同表不平才紅 |
| 輸出冊完整 · 調節輪 · ⑦ 基本資料雙讀 | 黃提醒 |
| **輸出值驗證(v0122 新)**:基本資料逐欄原文回查 · 年度數據逐值第二讀取器對欄 · 剔除數 | 黃提醒(主冊只含驗證過的值 · 剔除進剔除冊) |
| **v0122 啟動器另加**:完成判定檔必須是本輪寫的 · ⑦ 不紅 · ② / ⑥ 自測不紅 | 不符 → ⑧ 紅(不再沿用舊檔假綠) |

通過後:成功模組登記 → ⑨ 上船 GitHub(含管理器前版鏈 · 撞號守門)→ ⑩ 整併封存(不搬 GitHub 上的檔)→ U/I 自動跳出。

---

## 6. 實測結果

| 環境 | 版本 | 結果 |
|---|---|---|
| 使用者機器 · 第 34 輪 | v0115 等級 | 97 份 · 完成 · 紅 0 黃 1 |
| 使用者機器 · 第 35 輪 | v0118 | 範圍 55 份 · 未完成(實測退步 1 · 推斷 Citi-3231) |
| 雲端容器 · v0121 原樣 | 19 份真實 PDF(repo intake) | ENG397 v0126 **自測 33/34 → 被隔離**(沒有 PyMuPDF);④ 另出 `VRN2_UIAction_v0101.py`(九頭龍);⑥ 引擎不見了仍判 4/4 綠 |
| **雲端容器 · v0122** | 同上(個股 14 份) | 啟動器自測 **12/12** · 管理器 v0231 **33/33** · v0232 **11/11** · ENG397 v0127 **34/34** · 冷跑 44 秒 / 熱跑 32 秒(擷取快取 13/14)· 平行段 6 步 3 路 · 新增九頭龍頭 0 · 連跑兩次四本冊逐位元相同 |
| 輸出值獨立驗證(另寫的驗證器 · pdfplumber + pypdfium2) | v0122 輸出 | 基本資料 **145/145 欄**對原文;年度數據 **3,973 筆**:3,949 筆對到期間欄 + 24 筆人工逐列核對正確;**錯值 0**;剔除 212 筆(一格多值 183 · 非數據列 25 · 科目混入 2 · 並排表錯欄 2)進剔除冊 |
| U/I 真瀏覽器(Chromium · Playwright) | v0232 面板 | **20/20**:4 個 `vrn2://` 動作 · 不上船核取改寫連結 · 10 分頁各自只顯示一頁 · 完成判定面板永遠可見 · 重新整理記得分頁 · 送出狀態 · 還原先確認 · 備援指令(第一步升優先權 → PS 加速器 → 實際啟動器路徑)· 剪貼簿 · 無腳本錯誤 |
| `vrn2://` 處理器 v0102 | 12 種網址 | 6 種合法全收 · 6 種(`rm -rf` · `via://` · `;calc` · `../..` · `http://` · 空)全拒並記錄 |
| ⑨ / ⑩ 對照(同一測試樹 · 假完成) | v0121 vs v0122 | v0121:上船 7 檔(沒有前版鏈)→ **新 clone 跑尾版 rc 1**(前版 v0153 再往下找不到);⑩ **刪掉 GitHub 上的 `VRN_ENG062_SummarizerV1_v0103.py`**。v0122:上船 11 檔(含前版鏈)→ 新 clone 尾版自測 **PASS**;⑩ 保留 v0103 |
| **未能在容器驗證** | — | ⑤ 一標題四重點(ENG062 需要 PyMuPDF · 容器不裝套件)→ **BLOCKED,不是綠**;vrn2:// 協定註冊(非 Windows);OCR(未建隔離環境) |

---

## 7. 本輪修正(全景檢查 → 逐步修復 → 實測)

| # | 發現(證據) | 修法 | 實測 |
|---|---|---|---|
| 1 | 基本資料 `TEL` 寫成比對說明「2/2 一致」(7 份全錯) | v0232:TEL 寫原文號碼(兩條讀法都讀到才輸出 · 保留原文括號) | 145/145 |
| 2 | 華南 Email 輸出 `1-10863@…`(頁尾頁碼「- 1-」被跨行規則接上) | v0232:跨行接回只接字母開頭片段 · Email 只收原文詞界內帳號 | `10863@entrust.com.tw` |
| 3 | 瑞基分析師輸出 `Lily Tsai`(Email 推算 · 原文印「蔡欣妤」);華南誤取「電子信箱」 | v0232:原文 Email 上一行姓名 / 「研究員 姓名」/ 同行緊鄰 · 欄位標籤不當姓名 · 推算值標推算 | 蔡欣妤 · 許願 |
| 4 | 年度數據 202 筆不是單一值(Old/New/Diff 擠在一格、表頭列、底線列、科目混入)+ 2 筆並排表錯欄(JP-2330 P20 COGS) | v0232:逐值第二讀取器對欄 · 不合格進剔除冊(帶理由) | 錯值 0 |
| 5 | 科目黏到浮水印 / 章節名(「,凱基 應收帳款周轉天數」「Ratios Adj. tax rate」) | v0232:整個科目原文找不到時才去前綴 · 原字串留 `ITEM_RAW` | 驗證器科目檢查全過 |
| 6 | ENG397 總頁數只靠 PyMuPDF → 沒有時「快訊 / Note 不適用」判不出 → 自測失敗被隔離 | ENG397 v0127:改用 pypdfium2 → pdfplumber 頁數(有 fitz 時結果不變) | 34/34 |
| 7 | 處理器 v0100 沒有加速器橋 → ④ 另出 v0101(九頭龍 · 違反 L103) | 處理器 v0102 帶橋 · 從 U/I 開的視窗結束時等 Enter | ④ 不再出新檔 |
| 8 | ⑥ 引擎被隔離後仍 4/4 綠(根本沒引擎) | ⑥ 加「ENG397 存在且自測過」 | — |
| 9 | ⑧ 讀到舊的完成判定檔就上船(⑦ 中斷時假綠) | ⑧ 只認本輪寫的檔 · ⑦ 不紅 | 自測 |
| 10 | ⑨ 只送尾版 → GitHub 上跑不起來 | ⑨ 送尾版在 GitHub 上沒有的前版鏈 · 先 fetch 比對撞號 | 新 clone PASS |
| 11 | ⑩ 搬走 GitHub 上的 ENG062 v0101–v0103(v0112 還在載入 v0103) | ⑩ 不搬 git 追蹤中 / 現役版引用的檔 · git 狀態不明就不封存 | 保留 v0103 |
| 12 | ① 沒有 psutil 時量不到 RAM / CPU、也不升優先權 | ① ctypes / /proc 後援 · Windows 用 SetPriorityClass | RAM 16.2 GB 量到 |
| 13 | `python -c` 指令沒接加速器 | `_pyc` 一律先接加速器橋(約 0.25 秒) | 自測 |
| 14 | 步驟全部序跑 | ④b 平行段:③b OCR / ⑥c 協定 / ⑥b 範圍 / ENG397 自測 / 加速器匯入 / 編譯檢查 同時跑 · 路數依 CPU-1、RAM、CPU 使用率動態 · 上輪最長的先跑 · 前後比對檔頭 | 九頭龍 0 |
| 15 | U/I 備援指令沒接加速器、路徑寫死、不上船狀態不同步、剪貼簿失敗無後援、按鈕無回饋 | v0232 面板(見第 6 節 U/I 實測) | 20/20 |

---

## 8. 已知問題與待辦(依優先序)

| # | 項目 | 狀態 | 需要 |
|---|---|---|---|
| 1 | **使用者執行 v0122** | 待執行 | 確認:v0231 以 v0228 為前版自測通過;⑤ 綠(有 PyMuPDF);第 35 輪退步(Citi-3231)解除;⑧ 完成 → ⑨ 上船(會帶 v0154 起的管理器鏈)→ ⑩ |
| 2 | 管理器家族撞線 / 引擎編號撞號(第 4.3 節) | 待裁決 | 操作員 / VCGC |
| 3 | 剔除冊 183 筆「一格多值」(修正前 / 後 / 差異子欄位) | 未拆 | 依子表頭拆成 `期間 + 子欄` 再驗證(下一版) |
| 4 | 並排表錯欄(JP-2330 P20 · 晶心科 P5) | 已剔除 | ENG397 並排表切開再精修 |
| 5 | 華南 4 份(使用者機器):目標價 · ⑤ 3/4 | v0232 已修 Email / 分析師(repo 有原檔 `華南投顧-3017-奇鋐`) | 實跑確認 |
| 6 | 凱基慧洋電話只有一條讀法讀到 → TEL 不輸出 | 照保守規則留空(⑦ 黃) | 側欄電話收進首頁區塊 |
| 7 | JP-2330 資產恆等式差約 350 億 | 真實發現 · 黃 | 人工確認 |
| 8 | MQ-1560 影像 PDF(T4 待人工) | OCR 隔離環境 | 使用者機器 OCR |
| 9 | ADJ CLOSE · 報告日前收盤價 · 中文名稱 · `.TW/.TWO` | 待 VDF | VDF 股價庫與上市櫃清單路徑 |
| 10 | Parquet | 需 pandas + pyarrow | 使用者機器確認 |
| 11 | ⑦ 雙讀與輸出冊尚未納入逐項只增不減鎖 · 從 VRN-1 學:合成真值語料閘 · 標題分解 · 現價對資料庫收盤價分欄 | 未做 | — |

---

## 9. 收尾進度(對照範圍交付項)

| 交付項 | 狀態 |
|---|---|
| FILENAME 解析 | ✅ 個股四項檔名 14/14 綠(容器)· 52/52(使用者第 34 輪) |
| 首頁本文 + 資訊區 | ✅ |
| 年度財報頁 + 數據分解 | ✅ 3,973 筆全部驗證(3,949 對欄)· 🟡 183 筆多值格待拆 |
| 100% 還原 | 🟡 覆蓋門檻 ≥97% · 主冊值 100% 對原文 · 多值格 / 錯欄進剔除冊待精修 |
| 一標題四重點 | ✅ 使用者機器(第 34 輪)· ⛔ 容器 BLOCKED(無 PyMuPDF) |
| 輸出驗證無誤 | ✅ 基本資料 145/145 · 年度數據錯值 0 · 冪等 · 交互驗證 |
| HTML U/I 自動跳出 + 可操作 | ✅ 真瀏覽器 20/20(`vrn2://` 註冊待使用者 Windows 確認) |
| 基本資料 BASIC INFO | 🟡 ADJ CLOSE 類待 VDF |
| 輸出 JSON / CSV / Parquet | 🟡 Parquet 視環境 |
| 漏斗調節輪由 MAIN 控制 | ✅ |
| 成功即鎖 · 成功模組登記 | ✅ |
| 精簡整併 | ✅ ⑩ 不再誤搬 GitHub 檔 |
| 完成後上船 GitHub | ✅ 容器測試樹(含前版鏈 · 撞號守門)· 使用者機器待驗 |
| 每個指令接加速器 · 第一步 CPU / DRAM | ✅ 檔案型 py · `python -c` · PS 備援指令 |
| 六個獨立步驟同步跑 · 動態排序 | ✅ ④b 平行段 |

**整體**:容器內能驗的都已實測通過;剩下 ⑤(需 PyMuPDF)與 Windows 專屬項目要在使用者機器跑 v0122 確認。

---

## 10. 執行方式

```powershell
& {
  # ① 第一步:CPU 閒(<60%)時本視窗升「高於標準」(子行程繼承)· 釋放記憶體
  try { $c = (Get-CimInstance Win32_Processor -ErrorAction Stop | Measure-Object LoadPercentage -Average).Average; if ($c -lt 60) { (Get-Process -Id $PID).PriorityClass = 'AboveNormal' } } catch { }
  [GC]::Collect()
  # ② 接 PS 加速器(找不到不影響)
  $R = "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"
  $m = Join-Path $R 'supportive modules\VIA_PS_Accel_Module.ps1'; if (Test-Path -LiteralPath $m) { . $m }
  $A = "C:\Users\tonyk\Downloads\ActivateVRN-2.py"
  if (-not (Test-Path -LiteralPath $A)) { Write-Host "[RED] 找不到 $A · 請先下載 ActivateVRN-2.py v0122" -ForegroundColor Red; return }
  $mm = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
  $V = if ($mm) { [int]$mm.Matches[0].Groups[1].Value } else { 0 }
  if ($V -lt 122) { Write-Host "[RED] Downloads 裡這份是 v$('{0:D4}' -f $V) · 請重新下載 v0122" -ForegroundColor Red; return }
  $py = Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
  if (-not $py) { Write-Host "[RED] 找不到 python" -ForegroundColor Red; return }
  Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue
  Write-Host "[計] VRN-2 · ActivateVRN-2 v$('{0:D4}' -f $V) · 完成後自動上船 GitHub" -ForegroundColor Yellow
  & $py.Source $A
}
```

- 只實測不上船:`$env:VIA_VRN2_NO_PUSH = '1'`(或 U/I 勾「這次不上船」)。
- 關閉平行段(排查用):`$env:VIA_VRN2_PAR = '1'`;指定路數:`'3'`。
- 還原封存:`python ActivateVRN-2.py --restore-archive`(或 U/I「↩ 還原封存舊版」· 會先確認)。
- 全部重新擷取:U/I「↻ 清快取後重跑」。

---

## 11. 給下一個 AI 的關鍵規則(本輪新增在前)

- **輸出值要獨立驗證**:用不同讀取器逐值回查(值在該頁 · 同列有科目 · 落在期間表頭那一欄);只檢查「檔案有產生」或「數字在頁面某處」都不夠(本輪「數字在頁面」100%,但仍有 202 筆不是單一值、2 筆錯欄)。
- **驗證器本身也要被驗**:本輪驗證器先後誤報(逗號分行、並排表取錯表頭、科目折行、欄位標籤當姓名都曾讓它說錯)→ 每次 FAIL 先看原文再下結論。
- **環境相依不能決定燈號**:判定只用必裝的讀取器(pdfplumber / pypdfium2);選裝套件(PyMuPDF)缺席時結果要一樣。
- **薄尾鏈要完整上船**:只送尾版 = GitHub 上跑不起來;新增尾版要確認前版是誰(v0232 自測要求前版 = v0231)。
- **封存 / 搬檔前先問 git**:git 追蹤中的檔不是 VRN-2 的,不能搬。
- **平行只放互不相連的步驟**:會裝套件(③)、會出 .py(④)、會掃描整樹(⑤)的一律序跑;平行段前後比對檔頭。
- 先分診再修 · 口徑一致 · 假綠校正 · 不適用 ≠ 黃燈 · 快取鍵包含所有輸入 · 自測不寫真正的 registry · 上船只提交 VRN-2 自己的檔(沿用前輪規則)。
