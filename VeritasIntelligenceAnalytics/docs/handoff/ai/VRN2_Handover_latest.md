# VRN-2 交接報告 · ActivateVRN-2 v0124 · 2026-10-18(多值格拆子欄 · 獨立系統收尾)

> 給下一個 AI 工作階段:先讀本檔,再讀使用者貼回的貼包(≤300 行,結尾 NEXT:)。不要重讀整份程式;要看程式先用省 Token 卡(`read` / `slice` / `chain`)。
> **操作員裁決(2026-10-18)**:「都是獨立系統 · 完成 VRN-2 及收尾 · 自動完成」→ VRN-2 / VCGC / VDF 三系統各自獨立:VRN-2 不寫進別的系統的家族、不經 VCGC 核號、不登 VCGC 中央冊。
> **狀態**:v0124 在 Claude Code 雲端容器以 repo 內 19 份真實 PDF 實測 **⑧ 完成 · 紅 0**(新樹 · 再跑 · 從 v0123 升級 · 新電腦從 GitHub 還原 四種都過);三本冊獨立驗證 **錯值 0**(年度數據 4,425 筆,含 452 筆子欄)。使用者機器最後一次實跑仍是第 35 輪(v0118)→ 下一步 = 使用者執行 v0124。

---

## 1. 系統定義

- **VRN-2** = 獨立子系統:MAIN = `ActivateVRN-2.py` → `VRN-2 SystemManager`;自己的 SSOT(`VRN2_SSOT_v####.json`)、自己的 U/I 協定(`vrn2://`)、**自己的上船位置 `docs/handoff/ai/vrn2_ship/`**、**自己的編號(元件登記冊 `VRN2-<類>-####` 即正式號 · 不送 VCGC 核號)**。
- **與其他系統的界線(獨立)**:`functional modules\VRN` 夾裡 `VRN_SystemManager_v0114–v0153`、`VRN_ENG062_SummarizerV1_v0101–v0103`、`SSOT\VRN_Config_v0100.json` 是 VCGC 側 VRN 的檔(GitHub 上 git 追蹤中)。VRN-2 只讀取(管理器鏈的底層、摘要器舊 API),**不改、不搬、不上船覆蓋**;VRN-2 自己出的版本(管理器 v0154 起、ENG062 v0104 起、VRN_Config v1000 起)只在本機與 VRN-2 船包裡。
- **VRN-1** = 另一團隊(`C:\Users\tonyk\VIA-VDF-VRN`):互相學方法、不照抄程式碼。
- **範圍**:只做個股報告 → FILENAME · 首頁(本文 + 資訊區)· 年度財報頁(年度財報及數據分解)· 100% 還原 · 一標題四重點 · 輸出驗證無誤 · U/I 自動跳出且可操作。
- **治理**:只增不減 · 成功即鎖、只准變好 · 精準錨點修正 · 不產生九頭龍 · 每版過修正閘 · 漏斗原則 · 每個 PY / PS 指令接加速器 · 指令第一步提高 CPU / DRAM 效能 · 互不相連的步驟同時跑(動態排序)。

---

## 2. 檔案位置(使用者機器)

VIA 根目錄:`C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`(簡稱 `<ROOT>`)

| 類別 | 位置 | 說明 |
|---|---|---|
| **啟動器(MAIN)** | `C:\Users\tonyk\Downloads\ActivateVRN-2.py` | **v0124** · 雜湊見 `docs/handoff/ai/vrn2_release_v0124/VRN2_Release_v0124.json` |
| 程式夾(本機執行) | `<ROOT>\functional modules\VRN\` | 管理器鏈 v0154–v0234 / ENG397 / ENG062 / 處理器(VRN-2 的檔都不在 git 追蹤) |
| **VRN-2 船包(GitHub)** | `<ROOT>\docs\handoff\ai\vrn2_ship\VRN2_Bundle_latest.zip` + `.json` | ⑨ 完成時寫入並提交 · 只含 VRN-2 自己的檔 · 清單記相依的 GitHub 檔(路徑 + blob)· 內容沒變位元組就不變 |
| VRN-2 設定冊 | `…\VRN\SSOT\VRN2_SSOT_v####.json` | 來源夾 · 範圍 · 交付項 · 漏斗參數(換電腦來源夾不同 → 自動出新版) |
| 輸入設定冊(VRN-2 本機副本) | `…\VRN\SSOT\VRN_Config_v1000 起` | VRN-2 的管理器鏈從這裡讀 input_dir;VCGC 側用 v0100(不同號段) |
| 原始樣本 / 範圍夾 / 範圍冊 | `C:\測試樣本報告` · `<ROOT>\VIA_Reports\vrn2\scope_in\` · `…\vrn2\VRN2_Scope_latest.json` | |
| **輸出冊** | `<ROOT>\VIA_Reports\vrn2\output\` | `VRN2_BasicInfo / FinancialData / Summary / Rejected_latest.{json,csv,parquet}` · 年度數據欄位:`VERIFY` / `ITEM_RAW` / **`SUBCOL`(v0124 新:子欄標籤 · 空 = 一般格)** |
| Parquet 舊檔 | `…\vrn2\output\_stale\`(v0124 新) | 本輪寫不出 Parquet(缺 pandas / pyarrow)時,上一輪的 Parquet 移到這裡(不刪)· 避免讀到舊值 |
| **U/I** | `<ROOT>\VIA_Reports\vrn2\VRN2_UI_latest.html` | 左側操作面板 + 右側分頁(含剔除冊 · **子欄拆分總表**)· 每輪自動跳出 |
| 完成判定 / 啟動紀錄 | `…\vrn2\VRN2_Completion_latest.json`(+ `_Rounds.jsonl`)· `VRN2_Activate_latest.json`(含平行段秒數) | |
| 快取 | `…\vrn2\p1_cache\` · `acc_cache\` · `ocr_cache\` · `summary\` | |
| 鎖 / 成功登記 / 元件登記 | `…\VRN\registry\VRN2_Lock_*.json` · `VRN2_Module_Success_Register.json` · `VRN2_Component_Register_v####.json` | 鎖與成功登記帶時間 → 留本機;元件登記冊進船包 |
| 封存 / 隔離 | `…\VRN\_archive_vrn2\`(+ `ARCHIVE_MANIFEST.jsonl`)· `…\VRN\_quarantine\` | ⑩ 只搬 VRN-2 自己的舊版(升級時 ENG062 v0113 → 封存) |
| U/I 處理器 / 協定 | `…\VRN\VRN2_UIAction_v0102.py` + `VRN2_UIAction_Config.json` · `HKCU\Software\Classes\vrn2` | |
| OCR 隔離環境 | `C:\Users\tonyk\envs\vrn2_ocr\` + `VRN2_OCRBridge_v0100.py` | |
| **交接報告** | `<ROOT>\docs\handoff\ai\VRN2_Handover_latest.md`(+ `VRN2_Handover_v0124.md`) | ⑨ 自動落地(與 repo 同一份) |
| 本輪證據 | `<ROOT>\docs\handoff\ai\vrn2_release_v0124\` | 發行清單 · 驗證報告 · 日誌 · 截圖 · 測試工具 |

---

## 3. 版本紀錄

### 3.1 現役版本(v0124 內嵌 · 依序自動落地)

| 元件 | 版本 | 大小 | SHA-256(前 12) | 本輪 |
|---|---|---|---|---|
| ActivateVRN-2.py | **v0124** | 見發行清單 | 見發行清單 | 新 |
| VRN-2 SystemManager | v0231 → v0232 → v0233 → **v0234** | 215,605 / 43,966 / 10,066 / 27,553 | `ddff2743b478` / `42e682ba5074` / `25e33a714860` / `d8a564b2c442` | v0234 新(薄尾 · 前版必須 v0233) |
| VRN_ENG397_P1Segment | v0127 | 180,699 | `c2e8e39e5584` | 未變 |
| VRN_ENG062_SummarizerV1 | **v0114** | 63,825 | `62beeaf65576` | 新 |
| VRN2_UIAction | v0102 | 5,180 | `56d5b20689e3` | 未變 |
| VRN2_OCRBridge | v0100 | 4,778 | `4b21f0694d0e` | 未變 |
| rule_catalog_runtime.json | — | 449,121 | `e5b881716c84` | 未變 |

### 3.2 版本鏈

| 啟動器 | 管理器 | ENG397 | ENG062 | 主要內容 |
|---|---|---|---|---|
| v0110 – v0118 | v0221 – v0228 | v0119 – v0124 | v0107 – v0111 | **使用者機器實跑到這裡**(第 35 輪) |
| v0119 – v0121 | v0229 – v0231 | v0125 – v0126 | v0112 | 只在沙盒(快取 · 精簡 · ⑩ · U/I 面板 · vrn2://) |
| v0122 | v0231 → v0232 | v0127 | v0112 | 輸出值驗證 · 平行段 · 守門 |
| v0123 | → v0233 | v0127 | v0113 | 獨立上船(船包)· 新電腦還原 · 截斷重點補全文 · 數字比數值 · 評等不當標題 |
| **v0124** | → **v0234** | v0127 | **v0114** | 一格多值拆子欄(452 筆)· 擷取分組錯的格依子表頭更正 · 電話第三讀取器 · 八碼日期不當目標價 · Parquet 舊檔隔開 · U/I 子欄總表 |

> 使用者機器的管理器:GitHub 有 VCGC 側 v0114–v0153;本機有 VRN-2 的 v0154–v0228(v0229 / v0230 從未落地)→ v0231 的前版會是 v0228。v0124 依序落地 v0231 → v0232 → v0233 → v0234,每支自測過才落下一支;不過就隔離、停在前一支。若使用者已跑過 v0123,前三支「已在且 hash 同」,只落 v0234。

---

## 4. SSOT 現況

| 冊 | 現況 |
|---|---|
| `VRN2_SSOT_v0100.json` | system VRN-2 · independent true · scope stock_only · 交付項 7 · funnel(T0→T4 · 0.85 · 40 字 · max T3)· 換電腦來源夾不同 → 出 v0101(只增) |
| `VRN_Config_v1000 起` | VRN-2 本機副本(input_dir → 範圍夾)· 號段與 VCGC 側 v0100 分開 |
| `VRN2_Component_Register_v####` | **VRN-2 正式編號**(`VRN2-<類>-####`)· 獨立系統 → 不送 VCGC 核號 |
| `VRN_PipLedger.json` | PyPI 沒有的不重試 · 網路錯誤 24h 不重試 |
| `VRN2_Bundle_latest.json` | 船包清單:每檔路徑 · 大小 · SHA-256 · 相依的 GitHub 檔(路徑 + blob) |
| 中央冊 | **不登**(獨立系統)· VCGC 只讀監控 |

---

## 5. 完成判定(⑧)

| 條件 | 擋完成? |
|---|---|
| 實測退步 · 交互驗證 · 鎖定 + 備份 · 冪等 · ② 覆蓋 ≥97% · ③ 數字回原文 · ⑤ 一標題四重點 · ⑥ AUDIT · 個股四項 | 紅擋 |
| ① 計算驗證 | 同表不平才紅 |
| 輸出冊完整 · 調節輪 · ⑦ 雙讀 · 輸出值驗證(剔除進剔除冊) | 黃提醒 |
| 啟動器:完成判定檔必須本輪寫的 · ⑦ 不紅 · ② / ⑥ 不紅 | 不符 → ⑧ 紅 |

通過後:成功模組登記 → ⑨ 上船(VRN-2 船包)→ ⑩ 封存(只搬 VRN-2 自己的舊版)→ U/I。

---

## 6. 實測結果(雲端容器 · 19 份真實 PDF · 個股 14 份)

| 項目 | 結果 |
|---|---|
| 自測 | 啟動器 v0124 **15/15** · 管理器 v0231 33/33 · v0232 11/11 · v0233 6/6 · **v0234 14/14** · ENG397 v0127 34/34 |
| 完整實跑(有 PyMuPDF 的隔離測試環境) | **⑧ VRN-2 完成 · 紅 0 · 黃 7** → ⑨ 船包 12 檔(管理器鏈 5 支 · 相依 GitHub 檔 2)→ ⑩ · 約 70 秒 |
| 再跑一次 | ⑨「GitHub 已是最新 · 船包無變更」(不重送)· 約 50 秒 |
| **從 v0123 升級**(同一棵樹先跑 v0123 再換 v0124) | 只落 v0234 + ENG062 v0114(其餘「已在且 hash 同」)→ ⑧ 完成 → ⑨ 船包 11 → 12 檔 → ⑩ 封存被取代的 ENG062 v0113 |
| **新電腦(從 GitHub clone)** | ② 船包補回 12 檔(雜湊全對)→ ⑧ 完成 → ⑨(來源夾不同 → SSOT v0101 / Config v1002 只增) |
| ⑨ 提交內容 | 只有 `vrn2_ship/` 船包 + 清單 + 交接報告 · **functional modules 0 檔** |
| **輸出值獨立驗證**(另寫的驗證器 · 不 import VRN-2) | 基本資料 **194/194 欄**;一標題四重點 **63/63**;年度數據 **4,425 筆**:3,949 對欄 + 24 人工核對 + **452 子欄對位(pdfplumber 另查)**;**錯值 0** |
| 驗證器反向測試 | 把開發中真的出過的錯放回去(中點分組錯 · 季度段標成年度 · 子欄標籤對調 · 少拆一個值)→ **4 種全被抓到**;原樣 0 錯 |
| U/I 真瀏覽器 | **21/21**(新增:子欄拆分分頁可見 · 每張表一列) |
| 沒有 PyMuPDF 的環境 | 擷取 / 年度數據 / 基本資料照常(ENG397 v0127);⑤ 摘要與電話第三讀取器需要 PyMuPDF(③ 會補裝) |
| ③ 環境檢查 | 容器用 `--no-install` 不能補裝加速器的選用套件(pyvips / watchdog …)→ 紅 · 不擋 ⑧(與 v0123 相同;使用者機器會補裝) |

---

## 7. 本輪修正(v0123 → v0124)

| # | 發現 | 修法 | 實測 |
|---|---|---|---|
| 1 | 剔除冊 183 格「一格多值」(Daiwa New / Previous / Change · GS Old / New / Diff · Cons. / GS / %Diff · 凱基 修正後 / 修正前 / 調幅 / YoY / 共識 / 差異) | v0234 依子表頭拆成「期間 + 子欄」(`SUBCOL` 欄):pypdfium2 對位 · 兩條讀法整列數值序列相同 · 第二讀取器整頁只有一列對得上 · 每個值一對一對到最近的子欄標籤 | **138 格 → 452 筆**;剔除冊 212 → 74 |
| 2 | 期間表頭不在組的中點(凱基貿聯 2026F / 2027F 六欄 · 2028F 四欄):用中點分組會把 2027F「差異(%) 3.2」分到 2028F(標籤變「差異(%) #1 / #2」);擷取引擎自己的格也分錯 → 「與擷取的格一致」擋不住 | 子表頭切組:組內標籤不可重複 · 期間表頭要落在組內 · 取最置中的切法且要唯一(差 <4pt = 分不出 → 不拆)· 擷取分組不同時整列每格都要是多值才更正 · VERIFY 標「擷取分組更正(依子表頭)」 | 貿聯 80 筆更正 · 驗證器 0 錯 |
| 3 | 同一張表下半段換成季度(GS P5「2Q26E 3Q26E 4Q26E」)→ 季度值被標成 2026E / 2027E / 2028E | 遇到下一個表頭就停(擷取的列 + 第二讀取器的行都停) | 季度值不進年度數據 |
| 4 | 科目欄的單位字「百萬元」被當成子欄 → 切法分不出來 → 凱基整張不拆 | 子欄只收擷取引擎子表頭欄裡的字(中文黏在一起 → 子字串比) | 凱基慧洋 108 筆 |
| 5 | Daiwa「Operating profit margin」科目換行 → 用科目找行找到「Operating profit」那一行 | 改用整列數值序列找行(要唯一) | 9 筆拆出 |
| 6 | 凱基慧洋電話只有一條讀法讀到 · Daiwa「(886) 2 8758 6254」· 凱基貿聯「886.2.2181.8729」規則沒收 → TEL 空白 | 電話第三讀取器:pypdfium2 ∩ PyMuPDF 兩個獨立讀取器都讀到才輸出 · 收兩種國際寫法(v0231 首頁規則不動) | 3 份補上 · 驗證器 PASS |
| 7 | 華南目標價空白(首頁歷史表「目標價(元)⏎20251113」日期被當價格 → 與 1,780 衝突) | ENG062 v0114:八碼日期(西元 YYYYMMDD / 民國 YYYMMDD)不當價格(其他 13 份逐字不變) | 目標價 1,780 · 上漲空間 計算 32.8% |
| 8 | v0234 第一版 `_rebind(PRIOR._out_books)` 包到 v0233 的包裝 → 自己叫自己 → RecursionError(⑦ 輸出冊紅) | 直接叫前版(前版包裝自己再叫 v0232)· 自測加「空輸入跑完輸出冊不遞迴」 | 自測 14/14 |
| 9 | 寫不出 Parquet(缺 pandas / pyarrow)時上一輪的 Parquet 還在 → 讀到舊值 | 比本輪 JSON 舊的 Parquet 移到 `output/_stale/`(不刪) | 自測 |
| 10 | U/I 看不到拆分結果 | U/I 加「子欄拆分」分頁(檔案 · 表 · 期間 · 子欄 · 筆數 · 依子表頭更正筆數) | U/I 21/21 |
| 11 | 完成判定面板寫「VRN-2 SystemManager v0232」(v0123 起就是前版包裝自己的版號 · 實際尾版不是它) | 管理器欄寫實際在跑的尾版 | 「v0234」 |

(v0123 的 8 項 · v0122 的 15 項修正見 `VRN2_Handover_v0123.md` / `VRN2_Handover_v0122.md` 第 7 節。)

---

## 8. 已知問題與待辦(依優先序)

| # | 項目 | 狀態 | 需要 |
|---|---|---|---|
| 1 | **使用者執行 v0124** | 待執行 | 確認 v0231 以本機 v0228 為前版自測通過;⑤ 綠;第 35 輪退步(Citi-3231)解除;⑧ 完成 → ⑨ 第一次送出 VRN-2 船包(含 v0154 起的管理器鏈) |
| 2 | 剔除冊剩 74 筆:Daiwa P2 季度表 42 格(擷取把表切成兩段 · 3Q24E / 4Q24E 與年度欄掉到別處)· JP-2330 P20 並排表 / MS-3661 P6 沒有子表頭的多值 3 格 · 非數據列 25 · 科目混進數值欄 2 · 數值 x 不在期間欄 2 | 帶理由剔除(不是錯值) | ENG397 並排表 / 切表精修 |
| 3 | 多值欄各自獨立:ANALYST / EMAIL 依字母排序、TEL 依 PDF 順序,數量也可能不同(CLST 1 位分析師 2 支電話)→ **不能依位置配對** | 照實 | 若要配對 → 另加「分析師 + 電話 + Email」分組欄 |
| 4 | JP-2330 資產恆等式差約 350 億 · MQ-1560 影像 PDF(T4) | 真實發現 / 待 OCR | 人工確認 / OCR 隔離環境 |
| 5 | ADJ CLOSE · 報告日前收盤價 · 中文名稱 · `.TW/.TWO` | 待 VDF(不衝突即取用) | VDF 股價庫與上市櫃清單路徑 |
| 6 | Parquet | 需 pandas + pyarrow(寫不出時舊檔移 `_stale`) | 使用者機器確認 |
| 7 | 電話 MISSING 4 份(晶心科 / 瑞基 ×2 / 華南):PDF 本身沒有電話 | 正確 | — |
| 8 | ⑦ 雙讀與輸出冊的逐項只增不減鎖 · 從 VRN-1 學:合成真值語料閘 · 標題分解 · 現價對資料庫收盤價分欄 | 未做 | — |

---

## 9. 收尾進度

| 交付項 | 狀態 |
|---|---|
| FILENAME 解析 | ✅ 14/14(容器)· 52/52(使用者第 34 輪) |
| 首頁本文 + 資訊區 | ✅(TEL 三讀取器 · 華南目標價補上) |
| 年度財報頁 + 數據分解 | ✅ 4,425 筆錯值 0(含 452 筆子欄)· 🟡 剔除冊 74 筆(帶理由) |
| 100% 還原 | 🟡 覆蓋 ≥97% · 主冊值 100% 對原文 · 季度切表 / 並排表在剔除冊 |
| 一標題四重點 | ✅ 63/63 驗證(容器有 PyMuPDF 時) |
| 輸出驗證無誤 | ✅ 三本冊獨立驗證錯值 0 · 驗證器反向測試 4/4 |
| HTML U/I 自動跳出 + 可操作 | ✅ 21/21 · 子欄拆分分頁(`vrn2://` 註冊待 Windows) |
| 基本資料 BASIC INFO | 🟡 ADJ CLOSE 類待 VDF |
| JSON / CSV / Parquet | ✅ / ✅ / 🟡 視環境(舊檔不會冒充本輪) |
| 漏斗 · 成功即鎖 · 精簡整併 | ✅ |
| 完成後上船 GitHub | ✅ 獨立船包 · 新電腦可還原 · 無變更不重送 · 從 v0123 升級可 |
| 指令接加速器 · 第一步 CPU / DRAM · 平行段 | ✅ |

**整體**:功能與驗證在容器全部完成(⑧ 完成 · 紅 0);剩使用者機器實跑確認與第 8 節的資料型 / 精修項目。

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
  if (-not (Test-Path -LiteralPath $A)) { Write-Host "[RED] 找不到 $A · 請先下載 ActivateVRN-2.py v0124" -ForegroundColor Red; return }
  $mm = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
  $V = if ($mm) { [int]$mm.Matches[0].Groups[1].Value } else { 0 }
  if ($V -lt 124) { Write-Host "[RED] Downloads 裡這份是 v$('{0:D4}' -f $V) · 請重新下載 v0124" -ForegroundColor Red; return }
  $py = Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
  if (-not $py) { Write-Host "[RED] 找不到 python" -ForegroundColor Red; return }
  Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue
  Write-Host "[計] VRN-2 · ActivateVRN-2 v$('{0:D4}' -f $V) · 完成後自動上船(VRN-2 船包)" -ForegroundColor Yellow
  & $py.Source $A
}
```

- 只實測不上船:`$env:VIA_VRN2_NO_PUSH = '1'`(或 U/I 勾「這次不上船」)· 關閉平行段:`$env:VIA_VRN2_PAR = '1'`。
- 還原封存:`python ActivateVRN-2.py --restore-archive` · 全部重新擷取:U/I「↻ 清快取後重跑」。
- 新電腦:clone repo → 放好啟動器 → 照上面執行(② 自動依船包補回 VRN-2 檔)。

---

## 11. 給下一個 AI 的關鍵規則(本輪新增在前)

- **薄尾包裝不可再 rebind 前版的包裝**:前版函式本身已是包裝(裡面叫 `PRIOR.x`)時,`_rebind(PRIOR.x)` 會讓它在本版命名空間裡叫到自己 → 遞迴。包裝直接叫 `PRIOR.x(...)`;`_rebind` 只用在前版的「本體」(例 `vrn2`)。自測要真的跑一次包裝(空輸入也好)。
- **「兩邊一致」不等於「對」**:擷取引擎與第二讀取器用同一種錯的規則(中點分組)會一致地錯。分組要用結構條件(組內標籤不重複 · 表頭落在組內 · 置中且唯一),並用第三種讀法(pdfplumber 字詞框)另查。
- **表的邊界**:同一張表下半段換期間(季度)要停;第二讀取器找行要限在本段、序列要唯一。
- **驗證器要能抓到真錯**:每修一種錯,就把那種錯放回輸出跑一次驗證器(反向測試),抓不到就是驗證器的洞。
- **缺值 ≠ 錯值,但也要查原文**:MISSING 先看 PDF 有沒有(Daiwa / 貿聯有 → 補;晶心科 / 瑞基 / 華南沒有 → 正確)。
- **獨立系統**:VRN-2 不寫進別的系統的家族、不靠 VCGC 核號 / 中央冊;共用夾裡 git 追蹤中的檔是別的系統的 → 只讀。上船只寫 `docs/handoff/ai/vrn2_ship/` 與 VRN-2 交接報告。
- **船包要穩定**(固定時間 · 排序 · 帶時間的紀錄不進船包)· **不要用測試替身上船**(容器的前版鏈是 `TESTSTUB`)· **驗收資料不要截斷** · **數字比數值** · **輸出值要獨立驗證**。
- 環境相依不能決定燈號 · 薄尾鏈要完整 · 搬檔前先問 git · 平行只放互不相連的步驟 · 先分診再修 · 口徑一致 · 假綠校正 · 不適用 ≠ 黃燈 · 快取鍵包含所有輸入 · 自測不寫真正的 registry。
