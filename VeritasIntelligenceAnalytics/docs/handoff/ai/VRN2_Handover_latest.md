# VRN-2 交接報告 · ActivateVRN-2 v0122 · 2026-10-18

> 給下一個 AI 工作階段:先讀本檔,再讀使用者貼回的黃 / 紅貼包(≤300 行,結尾 NEXT:)。不要重讀整份程式。
> **重要**:v0119 ~ v0122 只在沙盒驗證過;使用者機器最後一次實跑是**第 35 輪(v0118)**。下一步是請使用者執行 v0122。

---

## 1. 系統定義(已鎖定)

- **VRN-2** = 完全獨立的子系統:自己的 MAIN(`ActivateVRN-2.py` → `VRN-2 SystemManager`)、自己的 SSOT(`VRN2_SSOT_v####.json`)、自己的 U/I 協定(`vrn2://`)。
- **VRN-1** = 另一團隊(`C:\Users\tonyk\VIA-VDF-VRN`,`VRN-MAIN`)。可互相學方法與工具,**不可照抄程式碼**。
- 參數可向 VDF / VCGC 取用,**不衝突即可**。
- **範圍**:只做**個股報告** → FILENAME · 首頁(本文 + 資訊區)· 年度財報頁(年度財報及數據分解)· 100% 還原 · 一標題四重點 · 輸出驗證無誤 · U/I 自動跳出且可操作。
- **治理**:只增不減(新版號,前版不動)· 成功即鎖、只准變好 · 精準 AST 錨點修正 · 不產生九頭龍 · 每版過修正閘 · 漏斗原則(輕的先用,不夠才升層)。

---

## 2. 檔案位置(使用者機器)

VIA 根目錄:`C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`(以下簡稱 `<ROOT>`)

| 類別 | 位置 | 說明 |
|---|---|---|
| **啟動器(MAIN 入口)** | `C:\Users\tonyk\Downloads\ActivateVRN-2.py` | v0122 · 一鍵完成全部步驟 |
| 程式夾 | `<ROOT>\functional modules\VRN\` | 管理器 / 引擎 / 摘要器 / 處理器 |
| **VRN-2 設定冊** | `<ROOT>\functional modules\VRN\SSOT\VRN2_SSOT_v0100.json` | 來源夾 · 範圍 · 交付項 · 取用規則 · 漏斗參數 |
| 輸入設定冊 | `…\VRN\SSOT\VRN_Config_v####.json` | 最新版 `input_dir` 指向範圍夾;`vrn2_source_dir` 記原來源 |
| 原始樣本 | `C:\測試樣本報告` | 97 份 PDF(另 TXT 1 / WORD 7 / IMG 201 不在範圍) |
| 個股範圍夾 | `<ROOT>\VIA_Reports\vrn2\scope_in\` | 每輪自動同步(只放個股報告) |
| 範圍冊 | `<ROOT>\VIA_Reports\vrn2\VRN2_Scope_latest.json` | stock / non_stock 判定(下一輪沿用) |
| **三本輸出冊** | `<ROOT>\VIA_Reports\vrn2\output\` | `VRN2_BasicInfo / FinancialData / Summary_latest.{json,csv}`(有 pyarrow 時加 `.parquet`) |
| **U/I** | `<ROOT>\VIA_Reports\vrn2\VRN2_UI_latest.html` | 左側操作面板 + 右側 9 分頁 · 每輪自動跳出 |
| 切割檢視 | `<ROOT>\VIA_Reports\vrn2\p1view\P1VIEW_latest.html / .md` | AI 讀 `.md`,不用截圖 |
| 完成判定 | `<ROOT>\VIA_Reports\vrn2\VRN2_Completion_latest.json`(+ `_Rounds.jsonl`) | |
| 驗收明細 | `<ROOT>\VIA_Reports\vrn2\VRN2_Acceptance_latest.{json,csv}` | |
| 擷取快取 | `<ROOT>\VIA_Reports\vrn2\p1_cache\` | 刪掉即全部重新擷取 |
| 驗收快取 | `<ROOT>\VIA_Reports\vrn2\acc_cache\` | `VIA_VRN2_NO_ACC_CACHE=1` 可停用 |
| OCR 快取 | `<ROOT>\VIA_Reports\vrn2\ocr_cache\` | |
| 摘要快取 | `<ROOT>\VIA_Reports\vrn2\summary\` | |
| 備份 | `<ROOT>\VIA_Reports\vrn2\backup\<時間>\` | 每次鎖定時備份 |
| U/I 動作紀錄 | `<ROOT>\VIA_Reports\vrn2\ui_actions.log` | |
| 鎖定 | `…\VRN\registry\VRN2_Lock_<時間>.json`、`VRN2_Lock_latest.json`、`VRN2_Stock_Lock_latest.json` | |
| **成功模組登記冊** | `…\VRN\registry\VRN2_Module_Success_Register.json`(+ `_History.jsonl`) | 判定完成才寫 |
| 元件登記冊 | `…\VRN\registry\VRN2_Component_Register_v####.json` | |
| 補裝帳本 | `…\VRN\registry\VRN_PipLedger.json` | PyPI 沒有的不再重試 · 網路錯誤 24h 不重試 |
| 加速器帳本 | `…\VRN\registry\VRN_AccelFix_Ledger.jsonl` | |
| **封存夾** | `…\VRN\_archive_vrn2\` + `ARCHIVE_MANIFEST.jsonl` | ⑩ 移入的被取代舊版 · `--restore-archive` 可還原 |
| 隔離區 | `…\VRN\_quarantine\` | 落地檢查失敗的檔 |
| U/I 處理器 | `…\VRN\VRN2_UIAction_v0100.py` + `VRN2_UIAction_Config.json` | `vrn2://` 白名單動作 |
| 協定登錄 | `HKCU\Software\Classes\vrn2` | 只寫目前使用者 · 不碰 `via://` |
| OCR 隔離環境 | `C:\Users\tonyk\envs\vrn2_ocr\` + 橋 `VRN2_OCRBridge_v0100.py` | 主環境不裝 OCR 套件 |
| **交接報告** | `<ROOT>\docs\handoff\ai\VRN2_Handover_latest.md`(+ 版本檔) | ⑨ 上船時自動落地 |
| GitHub | `tonykuni/movies-dataset`(使用者的 repo) | ⑨ 只提交 VRN-2 程式 / 設定冊 / 交接報告 |

---

## 3. 版本紀錄

### 3.1 現役版本(v0122 內嵌 · 啟動時自動落地)

| 元件 | 版本 | 大小 | SHA-256(前 12) |
|---|---|---|---|
| ActivateVRN-2.py | **v0122** | — | — |
| VRN-2 SystemManager | **v0232** | — | 見啟動器 MGR_SHA |
| VRN_ENG397_P1Segment(擷取) | **v0126** | 180,293 | `17652875168c` |
| VRN_ENG062_SummarizerV1(摘要) | **v0113** | — | 見啟動器 EXTRAS |
| VRN2_UIAction(U/I 處理器) | **v0100** | 3,059 | `21dc93de2f37` |
| VRN2_OCRBridge(OCR 橋) | **v0100** | 4,778 | `4b21f0694d0e` |
| VRN_ENG396_AssetIndex | v0102 | — | 未變(前鏈) |

### 3.2 本階段版本鏈(2026-10-16 ~ 10-18)

| 啟動器 | 管理器 | ENG397 | ENG062 | 主要內容 |
|---|---|---|---|---|
| v0110 | v0221 | v0119 | v0107 | OCR 隔離環境 · OCR 階梯 · 數字碎片接合 |
| v0111 – v0113 | v0222 – v0224 | v0120 – v0121 | v0108 – v0109 | OCR 表重建 · 假綠鎖校正 · OCR 快取 · OCR 檔驗收 900 秒 |
| v0114 | v0225 | v0122 | v0110 | 全景黃燈:不適用改備註 · 非資料框 · 並排表拆開 · 逐行 PDF 接段落 · 免責不當重點 · OCR 算術交叉驗證 |
| v0115 | v0225 | v0123 | v0111 | GS 填色資訊框救回 · GS Forecast 表重建 · 其他頁資訊框取目標價 |
| v0116 | v0226 | v0123 | v0111 | 向 VRN-1 學:⑦ 基本資料雙讀 · 資產恆等式 · 冪等閘 |
| v0117 | v0227 | v0123 | v0111 | 獨立收尾:VRN2_SSOT · 範圍聚焦 · 三本輸出冊 |
| v0118 | v0228 | v0124 | v0111 | 調節輪(漏斗)交 MAIN · ⑨ 上船 GitHub |
| v0119 | v0229 | v0125 | v0112 | 第 35 輪修正:對齊口徑統一 · 年度數據冊表頭判斷 · 退步寫檔名 |
| v0120 | v0230 | v0126 | v0112 | 擷取 / 驗收快取 · 成功模組登記 · 精簡(4.2 → 1.3 MB)· ⑩ 整併封存 |
| v0121 | v0231 | v0126 | v0112 | U/I 左側操作面板 + 9 分頁 · `vrn2://` 協定 · 補裝帳本 |
| **v0122** | **v0232** | v0126 | **v0113** | 待辦收尾:MQ 目標價(OCR · 候選消歧)· 凱基雙讀字型插字 · ⑦ 與輸出冊納入只准變好 |

---

## 4. SSOT 現況

### 4.1 `VRN2_SSOT_v0100.json`(VRN-2 獨立設定冊)

| 欄位 | 值 |
|---|---|
| system / owner / independent | `VRN-2` / `VRN-2 SystemManager` / `true` |
| source_dir | 第一次執行時取自當時的 `VRN_Config.input_dir`(使用者機器應為 `C:\測試樣本報告`) |
| scope / scope_dir | `stock_only` / `<ROOT>\VIA_Reports\vrn2\scope_in` |
| deliverables | FILENAME · 首頁(本文 / 資訊區)· 年度財報頁(年度財報及數據分解)· 100% 還原 · 一標題四重點 · 輸出驗證 · HTML U/I |
| borrow_rule | 參數可向其他系統取用(VDF 上市櫃清單 / 股價庫等)· 不衝突即可 · 不照抄程式 |
| funnel.order | T0 文字層 → T1 換引擎 → T2 OCR 200 DPI → T3 OCR 325 DPI + 前處理 → T4 待人工 |
| funnel.ocr_ladder / min_conf / min_chars / max_tier | `200,325p` / `0.85` / `40` / `T3` |

- 內容有變才出新版(`v0101`…),由 `vrn2scope` 動詞維護。
- 漏斗參數由啟動器帶入引擎環境變數(`VIA_VRN2_OCR_LADDER` / `_MIN_CONF` / `_MIN_CHARS`);`max_tier` 設 `T0` / `T1` 時不啟用 OCR。

### 4.2 其他設定 / 帳本

| 冊 | 現況 |
|---|---|
| `VRN_Config_v####.json` | v0117 起每輪若 `input_dir` 不是範圍夾就出新版指向它(只增不減) |
| `VRN2_Scope_latest.json` | 每輪寫出;下一輪排除上輪判定的非個股(第一次執行只能靠檔名排除) |
| `VRN_PipLedger.json` | v0121 新增;使用者機器上預計記入 `VIS-UltimateAccelerator-V12-MEGA` / `superextract` / `via-nlp-engine`(PyPI 沒有)與 `docling` / `gspread-dataframe` / `yake`(網路) |
| `VRN2_Module_Success_Register.json` | v0230 新增;尚未在使用者機器產生 |

### 4.3 待確認的 SSOT 事項

- 元件登記冊的「黃 = 暫編待 VCGC 核號」仍未核號。
- 管理器檔名家族 `VRN_SystemManager_v####`(修正閘靠它找尾版)改名需交 VCGC。
- VRN2_SSOT 尚未登記到 VCGC 的 Policy / 書冊目錄。

---

## 5. 完成判定(⑧)現行條件

| 條件 | 擋完成? |
|---|---|
| 實測退步(鎖過的檔不得退步 · 紅燈會寫出檔名) | 紅擋 |
| 交互驗證 JSON ↔ CSV ↔ 燈號 | 紅擋 |
| 鎖定 + 備份 | 紅擋 |
| 冪等(重跑 3 份 · 不吃快取 · 逐字相同) | 紅擋 |
| 輸出冊完整(基本資料 / 年度數據 / 一標題四重點) | 黃提醒 |
| 調節輪(有 T4 待人工判黃) | 黃提醒 |
| ① 計算驗證(利潤率 · 上漲空間 · 摘要 EPS · 資產恆等式 · OCR 算術交叉驗證) | 同表不平才紅 |
| ② 覆蓋 ≥97%(排除圖內座標字 · 旋轉字 · 頁面最底 8%) | 紅擋 |
| ③ 數字回原文 | 紅擋 |
| ⑤ 一標題四重點(含成功紀錄比對 3 份) | 紅擋 |
| ⑥ AUDIT 新輸入 | 紅擋 |
| ⑦ 基本資料雙讀 | 最多黃 |
| 個股四項 | 紅擋 |

通過後依序:成功模組登記 → ⑨ 上船 GitHub → ⑩ 整併封存 → U/I 自動跳出。

---

## 6. 實測結果

| 環境 | 版本 | 結果 |
|---|---|---|
| 使用者機器 · 第 34 輪 | v0115 等級 | 97 份 · 擷取燈 綠 83 / 黃 14 · 個股四項 52/52 全綠 · **完成 · 紅 0 黃 1** |
| 使用者機器 · 第 35 輪 | v0118 | 範圍聚焦 55 份 · **未完成**(實測退步 1,推斷 Citi-3231,對齊口徑不一致)· 其餘紅 0 |
| 沙盒 · v0121 | 21 份(含 GS 3 份) | 連跑兩次皆 **完成 · 紅 0 黃 2** · 冪等綠 · 輸出逐字相同 · ⑨ 提交 9 檔 · ⑩ 封存 13 個 · U/I 9 分頁(jsdom 實測可操作) |
| 沙盒 · v0120 速度 | 21 份 | 連跑三次:189 → 96 → 22 秒(擷取 / 驗收快取) |
| 修正閘 | 每版 | 新增九頭龍頭 0 · 既有檔被改 0 · 在地測試新增失敗 0 |

---

## 7. 已知問題與待辦(依優先序)

| # | 項目 | 狀態 | 需要 |
|---|---|---|---|
| 1 | **使用者執行 v0121** | 待執行 | 確認第 35 輪的退步(Citi-3231)已因 v0125 對齊口徑統一而解除;確認快取、U/I 按鈕、⑨⑩ 在使用者機器運作 |
| 2 | 第 35 輪 10 份「財報表沒對到期間欄」(daiwa / CLST / GFHK / MS-3661 / 南亞 / 啟碁 / 華南 4) | v0125 已改口徑,**未在實檔驗證** | 執行結果;仍黃時附原檔 |
| 3 | 華南 4 份:目標價未擷取 · ⑤ 3/4 · 分析師空白 · Email 帳號被截(`450@entrust.com.tw`) | 未修 | **華南原檔**(沙盒只有 Memo 版) |
| 4 | JP-2330 資產恆等式差約 350 億 | 真實發現,維持黃 | 人工確認(報告科目口徑) |
| 5 | 凱基慧洋分析師電話 | ✅ v0232 已修(字型插字「88)6」)· ⑦ 轉綠 | — |
| 6 | MQ-1560 目標價 | ✅ v0113 已修(855.00 · 上漲空間 32.8%)| — |
| 7 | ADJ CLOSE · 報告日前收盤價 · 外資報告中文名稱 · yfinance `.TW` / `.TWO` | 標「待 VDF」 | **VDF 股價庫與上市櫃清單的路徑 / 格式** |
| 8 | Parquet 輸出 | 需使用者環境有 pandas + pyarrow | 執行結果確認 |
| 9 | `vrn2://` 第一次使用 | 瀏覽器會詢問是否開啟 pythonw | 使用者允許一次 |
| 10 | ⑦ 雙讀與輸出冊只准變好 | ✅ v0232 已做 | — |
| 10b | 基本資料冊 TEL 欄誤填狀態說明(「1/1 一致」)| ✅ v0232 已修:改填號碼並統一格式 +國碼-區碼-號碼 | — |
| 11 | 從 VRN-1 尚未學的:合成真值語料閘 · 輸出逐欄位鎖 · 標題分解 · 現價對資料庫收盤價(分兩欄) | 未做 | 第 7 項的 VDF 路徑 |
| 12 | 元件核號 · 管理器檔名改名 · SSOT 登記 | 交 VCGC | — |

---

## 8. 收尾進度(對照範圍交付項)

| 交付項 | 狀態 |
|---|---|
| FILENAME 解析(代號 / 日期 / 券商) | ✅ 個股四項 52/52 |
| 首頁本文 + 資訊區切割擷取 | ✅ |
| 年度財報頁 + 數據分解 | ✅(年度數據冊 · 華南待原檔) |
| 100% 還原 | 🟡 覆蓋門檻 ≥97%(頁尾 / 圖內座標字依規則排除)· 未達 VRN-1 的 99.9% 目標 |
| 一標題四重點 | ✅(⑤ · 華南 / Note 類部分 3/3 不適用) |
| 輸出驗證無誤 | ✅ ①②③⑤⑥⑦ + 冪等 + 交互驗證 |
| HTML U/I 自動跳出 + 可操作 | ✅ 沙盒(使用者機器待驗) |
| 基本資料 BASIC INFO | 🟡 18 欄中 ADJ CLOSE 類待 VDF |
| 輸出 JSON / CSV / Parquet | 🟡 Parquet 視環境 |
| 漏斗調節輪由 MAIN 控制 | ✅ |
| 成功即鎖 · 成功模組登記 | ✅ |
| 精簡整併(不留一堆類似檔) | ✅ 啟動器 4.2 → 1.3 MB · 舊引擎封存 |
| 完成後上船 GitHub | ✅ 沙盒(使用者機器待驗) |

**整體**:功能面在沙盒已全部完成並驗證;等使用者機器跑 v0121 確認後,剩下的是第 7 節的資料型待辦(華南原檔、VDF 路徑)。

---

## 9. 執行方式

```powershell
& {
  $A = "C:\Users\tonyk\Downloads\ActivateVRN-2.py"
  if (-not (Test-Path -LiteralPath $A)) { Write-Host "[RED] 找不到 $A · 請先下載 ActivateVRN-2.py v0122" -ForegroundColor Red; return }
  $m = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
  $V = if ($m) { [int]$m.Matches[0].Groups[1].Value } else { 0 }
  if ($V -lt 122) { Write-Host "[RED] Downloads 裡這份是 v$('{0:D4}' -f $V) · 請重新下載 v0122" -ForegroundColor Red; return }
  $py = Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
  if (-not $py) { Write-Host "[RED] 找不到 python" -ForegroundColor Red; return }
  Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue
  Write-Host "[計] VRN-2 · ActivateVRN-2 v$('{0:D4}' -f $V) · 完成後自動上船 GitHub" -ForegroundColor Yellow
  & $py.Source $A
}
```

- 只實測不上船:改設 `$env:VIA_VRN2_NO_PUSH = '1'`(或 U/I 勾「這次不上船」)。
- 還原封存的舊版:`python ActivateVRN-2.py --restore-archive`(或 U/I「↩ 還原封存舊版」)。
- 全部重新擷取:U/I「↻ 清快取後重跑」。

---

## 10. 給下一個 AI 的關鍵規則

- **先分診再修**:紅燈分「中斷 / 環境 / 真紅」;只對真紅出新版(前版不動)。
- **口徑一致**:同一件事(例:年度表是否對齊)全系統只能有一個判斷標準;擷取燈、個股四項、輸出冊必須共用。
- **假綠校正**:上輪的綠建立在錯誤內容上(橫幅標題、免責重點、圖例)不算退步,但必須在貼包列出。
- **不適用 ≠ 黃燈**:記入 `na` 備註,U/I 以灰字顯示;個股四項判斷同時看 reasons 與 na。
- **快取**:鍵值必須包含所有會影響結果的輸入(內容雜湊 + 程式指紋 + 參數);冪等閘不得吃快取。
- **後援只在需要時啟用**(摘要器接段落、短風險句、其他頁資訊框),其他券商路徑不變,成功紀錄比對不得受影響。
- **交付前必驗**:自測 → 真檔回歸(與上一版逐字比對並說明差異)→ 修正閘 → 從乾淨環境完整實跑(必要時連跑多次)→ 檢查輸出**內容**品質(不只檢查檔案存在)→ 前端腳本用 jsdom 實際執行。
- **自測不得寫入真正的 registry**(與鎖定共用注入的 `reg` 參數)。
- **上船只提交 VRN-2 自己的檔**,絕不提交 PDF / 輸出 / 範圍夾,不動使用者其他暫存變更。
