# VRN-2 交接報告 · ActivateVRN-2 v0123 · 2026-10-18(獨立系統收尾)

> 給下一個 AI 工作階段:先讀本檔,再讀使用者貼回的貼包(≤300 行,結尾 NEXT:)。不要重讀整份程式;要看程式先用省 Token 卡(`read` / `slice` / `chain`)。
> **操作員裁決(2026-10-18)**:「都是獨立系統 · 完成 VRN-2 及收尾 · 自動完成」→ VRN-2 / VCGC / VDF 三系統各自獨立:VRN-2 不寫進別的系統的家族、不經 VCGC 核號、不登 VCGC 中央冊。
> **狀態**:v0123 在 Claude Code 雲端容器以 repo 內 19 份真實 PDF 實測 **⑧ 完成 · 紅 0**(含新電腦從 GitHub 還原再跑);使用者機器最後一次實跑仍是第 35 輪(v0118)→ 下一步 = 使用者執行 v0123。

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
| **啟動器(MAIN)** | `C:\Users\tonyk\Downloads\ActivateVRN-2.py` | **v0123** · 雜湊見 `docs/handoff/ai/vrn2_release_v0123/VRN2_Release_v0123.json` |
| 程式夾(本機執行) | `<ROOT>\functional modules\VRN\` | 管理器鏈 v0154–v0233 / ENG397 / ENG062 / 處理器(VRN-2 的檔都不在 git 追蹤) |
| **VRN-2 船包(GitHub)** | `<ROOT>\docs\handoff\ai\vrn2_ship\VRN2_Bundle_latest.zip` + `.json` | ⑨ 完成時寫入並提交 · 只含 VRN-2 自己的檔 · 清單記相依的 GitHub 檔(路徑 + blob)· 內容沒變位元組就不變(不會每輪重送) |
| VRN-2 設定冊 | `…\VRN\SSOT\VRN2_SSOT_v####.json` | 來源夾 · 範圍 · 交付項 · 漏斗參數(換電腦來源夾不同 → 自動出新版) |
| 輸入設定冊(VRN-2 本機副本) | `…\VRN\SSOT\VRN_Config_v1000 起` | VRN-2 的管理器鏈從這裡讀 input_dir;VCGC 側用 v0100(不同號段 · 不衝突)· 不上船成散檔 |
| 原始樣本 / 範圍夾 / 範圍冊 | `C:\測試樣本報告` · `<ROOT>\VIA_Reports\vrn2\scope_in\` · `…\vrn2\VRN2_Scope_latest.json` | |
| **輸出冊** | `<ROOT>\VIA_Reports\vrn2\output\` | `VRN2_BasicInfo / FinancialData / Summary / Rejected_latest.{json,csv,parquet}` · 年度數據有 `VERIFY` / `ITEM_RAW` |
| **U/I** | `<ROOT>\VIA_Reports\vrn2\VRN2_UI_latest.html` | 左側操作面板 + 右側 10 分頁(含剔除冊)· 每輪自動跳出 |
| 完成判定 / 啟動紀錄 | `…\vrn2\VRN2_Completion_latest.json`(+ `_Rounds.jsonl`)· `VRN2_Activate_latest.json`(含平行段秒數) | |
| 快取 | `…\vrn2\p1_cache\` · `acc_cache\` · `ocr_cache\` · `summary\`(摘要器全文 · 輸出冊用來補回截斷的重點) | |
| 鎖 / 成功登記 / 元件登記 | `…\VRN\registry\VRN2_Lock_*.json` · `VRN2_Module_Success_Register.json` · `VRN2_Component_Register_v####.json` | 鎖與成功登記帶時間 → 留本機;元件登記冊進船包 |
| 封存 / 隔離 | `…\VRN\_archive_vrn2\`(+ `ARCHIVE_MANIFEST.jsonl`)· `…\VRN\_quarantine\` | ⑩ 只搬 VRN-2 自己的舊版 |
| U/I 處理器 / 協定 | `…\VRN\VRN2_UIAction_v0102.py` + `VRN2_UIAction_Config.json` · `HKCU\Software\Classes\vrn2` | |
| OCR 隔離環境 | `C:\Users\tonyk\envs\vrn2_ocr\` + `VRN2_OCRBridge_v0100.py` | |
| **交接報告** | `<ROOT>\docs\handoff\ai\VRN2_Handover_latest.md`(+ `VRN2_Handover_v0123.md`) | ⑨ 自動落地(與 repo 同一份) |
| 本輪證據 | `<ROOT>\docs\handoff\ai\vrn2_release_v0123\` | 發行清單 · 驗證報告 · 日誌 · 截圖 · 測試工具 |

---

## 3. 版本紀錄

### 3.1 現役版本(v0123 內嵌 · 依序自動落地)

| 元件 | 版本 | 大小 | SHA-256(前 12) | 本輪 |
|---|---|---|---|---|
| ActivateVRN-2.py | **v0123** | 見發行清單 | 見發行清單 | 新 |
| VRN-2 SystemManager | v0231 → v0232 → **v0233** | 215,605 / 43,966 / 見發行清單 | `ddff2743b478` / `42e682ba5074` / 見發行清單 | v0233 新(薄尾 · 前版必須 v0232) |
| VRN_ENG397_P1Segment | v0127 | 180,699 | `c2e8e39e5584` | 未變 |
| VRN_ENG062_SummarizerV1 | **v0113** | 見發行清單 | 見發行清單 | 新 |
| VRN2_UIAction | v0102 | 5,180 | `56d5b20689e3` | 未變 |
| VRN2_OCRBridge | v0100 | 4,778 | `4b21f0694d0e` | 未變 |
| rule_catalog_runtime.json | — | 449,121 | `e5b881716c84` | 未變 |

### 3.2 版本鏈

| 啟動器 | 管理器 | ENG397 | ENG062 | 主要內容 |
|---|---|---|---|---|
| v0110 – v0118 | v0221 – v0228 | v0119 – v0124 | v0107 – v0111 | **使用者機器實跑到這裡**(第 35 輪) |
| v0119 – v0121 | v0229 – v0231 | v0125 – v0126 | v0112 | 只在沙盒(快取 · 精簡 · ⑩ · U/I 面板 · vrn2://) |
| v0122 | v0231 → v0232 | v0127 | v0112 | 輸出值驗證 · 平行段 · 守門(只在容器) |
| **v0123** | v0231 → v0232 → **v0233** | v0127 | **v0113** | 獨立上船(船包)· 新電腦還原 · 截斷重點補全文 · 數字比數值 · 評等不當標題 |

> 使用者機器的管理器:GitHub 有 VCGC 側 v0114–v0153;本機有 VRN-2 的 v0154–v0228(v0229 / v0230 從未落地)→ v0231 的前版會是 v0228。v0123 依序落地 v0231 → v0232 → v0233,每支自測過才落下一支;不過就隔離、停在前一支。

---

## 4. SSOT 現況

| 冊 | 現況 |
|---|---|
| `VRN2_SSOT_v0100.json` | system VRN-2 · independent true · scope stock_only · 交付項 7 · funnel(T0→T4 · 0.85 · 40 字 · max T3)· 換電腦來源夾不同 → 出 v0101(只增) |
| `VRN_Config_v1000 起` | VRN-2 本機副本(input_dir → 範圍夾)· 號段與 VCGC 側 v0100 分開 |
| `VRN2_Component_Register_v####` | **VRN-2 正式編號**(`VRN2-<類>-####`)· 操作員裁決獨立 → 不再「待 VCGC 核號」 |
| `VRN_PipLedger.json` | PyPI 沒有的不重試 · 網路錯誤 24h 不重試 |
| `VRN2_Bundle_latest.json`(新) | 船包清單:每檔路徑 · 大小 · SHA-256 · 相依的 GitHub 檔(路徑 + blob) |
| 中央冊 | **不登**(操作員裁決:獨立系統)· VCGC 只讀監控 |

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
| 自測 | 啟動器 v0123 **15/15** · 管理器 v0231 33/33 · v0232 11/11 · v0233 6/6 · ENG397 v0127 34/34 |
| 完整實跑(有 PyMuPDF 的隔離測試環境) | **⑧ VRN-2 完成 · 紅 0 · 黃 7** → ⑨ 船包 11 檔(管理器鏈 4 支 · 相依 GitHub 檔 2)→ ⑩ · 約 60 秒 |
| 再跑一次 | ⑨「GitHub 已是最新 · 船包無變更」(不重送) |
| **新電腦(從 GitHub clone)** | ② 船包補回 11 檔(雜湊全對)→ 全部「已在且 hash 同」→ ⑧ 完成 → ⑨ |
| ⑨ 提交內容 | 只有 `vrn2_ship/` 船包 + 清單 + 交接報告 · **functional modules 0 檔** |
| **輸出值獨立驗證**(另寫的驗證器 · pdfplumber + pypdfium2) | 基本資料 **189/189 欄**;一標題四重點 **62/62**(標題 / 重點是原文句 · 「計算」的值重算對:上漲空間 · 各年 EPS YoY);年度數據 **3,973 筆**:3,949 對欄 + 24 人工核對;**錯值 0** · 剔除 212 筆(帶理由) |
| U/I 真瀏覽器 | **20/20** |
| 沒有 PyMuPDF 的環境 | 擷取 / 年度數據 / 基本資料照常(ENG397 v0127);⑤ 摘要需要 PyMuPDF(③ 會補裝) |

---

## 7. 本輪修正(v0122 → v0123)

| # | 發現 | 修法 | 實測 |
|---|---|---|---|
| 1 | ⑨ 把 .py 放進 functional modules\VRN(VRN_SystemManager / ENG062 / VRN_Config 是 VCGC 側也用的家族)→ 影響別的系統 | ⑨ 改送 VRN-2 船包到 `docs/handoff/ai/vrn2_ship/`;別的系統的檔只記相依 | 提交 functional modules 0 檔 |
| 2 | 新 clone 沒有 VRN-2 的管理器鏈 → 跑不起來 | ② 依船包補回(只增不減 · 雜湊對才寫) | 新電腦 ⑧ 完成 |
| 3 | 重點被截在 240 字(Daiwa「2025 年 Core Diluted EPS 6.」)| v0233 用摘要器快取的全文補回(前綴相同才換) | 6.145 · YoY 重算對 |
| 4 | v0232 把對的目標價 / 現價剔除(原文「4,200.00」「3 00 . 0 0」)| v0233 數字比數值(千分位 · 字距 · 小數位) | 7 個值回到輸出冊 |
| 5 | 晶心科標題 = 「中立(Neutral)」 | ENG062 v0113:只有評等的大字行不當標題(其他 13 份標題 / 重點逐字不變) | RISC-V 生態系發展快速,惟短期運營存在不確定性 |
| 6 | 標題 / 重點夾換行、中文字間斷行空白、頭尾「-」 | v0233 整理成單行(不改字) | — |
| 7 | 船包含帶時間的鎖 → 每輪都重送 | 鎖 / 成功登記留本機 | 第二輪「無變更」 |
| 8 | 完成時 NEXT 行夾「耗時 0 秒」 | 去掉 | — |

(v0122 的 15 項修正見 `VRN2_Handover_v0122.md` 第 7 節:TEL · 華南 Email · 分析師 · 年度數據逐值對欄 · 剔除冊 · ENG397 v0127 · 處理器 v0102 · ⑥ / ⑧ / ⑩ 守門 · ① 不靠 psutil · `python -c` 接加速器 · 平行段 · U/I 備援指令。)

---

## 8. 已知問題與待辦(依優先序)

| # | 項目 | 狀態 | 需要 |
|---|---|---|---|
| 1 | **使用者執行 v0123** | 待執行 | 確認 v0231 以本機 v0228 為前版自測通過;⑤ 綠;第 35 輪退步(Citi-3231)解除;⑧ 完成 → ⑨ 第一次送出 VRN-2 船包(含 v0154 起的管理器鏈) |
| 2 | 剔除冊 183 筆「一格多值」(修正前 / 後 / 差異子欄) | 未拆 | 依子表頭拆成「期間 + 子欄」再驗證 |
| 3 | 並排表錯欄(JP-2330 P20 · 晶心科 P5) | 已剔除 | ENG397 並排表切開精修 |
| 4 | 華南目標價空白(首頁「目標價1,780元」與歷史表 1,780 / 1,800 / 576 衝突 → 摘要器保守留空) | 缺值(不是錯值) | 摘要器衝突裁決:首頁敘述句優先於歷史表 |
| 5 | 凱基慧洋電話只有一條讀法讀到 → TEL 不輸出 | 保守留空 | 側欄電話收進首頁區塊 |
| 6 | JP-2330 資產恆等式差約 350 億 · MQ-1560 影像 PDF(T4) | 真實發現 / 待 OCR | 人工確認 / OCR 隔離環境 |
| 7 | ADJ CLOSE · 報告日前收盤價 · 中文名稱 · `.TW/.TWO` | 待 VDF(不衝突即取用) | VDF 股價庫與上市櫃清單路徑 |
| 8 | Parquet | 需 pandas + pyarrow | 使用者機器確認 |
| 9 | ⑦ 雙讀與輸出冊的逐項只增不減鎖 · 從 VRN-1 學:合成真值語料閘 · 標題分解 · 現價對資料庫收盤價分欄 | 未做 | — |

---

## 9. 收尾進度

| 交付項 | 狀態 |
|---|---|
| FILENAME 解析 | ✅ 14/14(容器)· 52/52(使用者第 34 輪) |
| 首頁本文 + 資訊區 | ✅ |
| 年度財報頁 + 數據分解 | ✅ 3,973 筆錯值 0 · 🟡 183 筆多值格待拆 |
| 100% 還原 | 🟡 覆蓋 ≥97% · 主冊值 100% 對原文 · 多值格 / 錯欄在剔除冊 |
| 一標題四重點 | ✅ 62/62 驗證(容器有 PyMuPDF 時) |
| 輸出驗證無誤 | ✅ 三本冊獨立驗證錯值 0 |
| HTML U/I 自動跳出 + 可操作 | ✅ 20/20(`vrn2://` 註冊待 Windows) |
| 基本資料 BASIC INFO | 🟡 ADJ CLOSE 類待 VDF · 華南目標價缺 |
| JSON / CSV / Parquet | ✅ / ✅ / 🟡 視環境 |
| 漏斗 · 成功即鎖 · 精簡整併 | ✅ |
| 完成後上船 GitHub | ✅ 獨立船包 · 新電腦可還原 · 無變更不重送 |
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
  if (-not (Test-Path -LiteralPath $A)) { Write-Host "[RED] 找不到 $A · 請先下載 ActivateVRN-2.py v0123" -ForegroundColor Red; return }
  $mm = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
  $V = if ($mm) { [int]$mm.Matches[0].Groups[1].Value } else { 0 }
  if ($V -lt 123) { Write-Host "[RED] Downloads 裡這份是 v$('{0:D4}' -f $V) · 請重新下載 v0123" -ForegroundColor Red; return }
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

- **獨立系統**:VRN-2 不寫進別的系統的家族、不靠 VCGC 核號 / 中央冊;共用夾裡 git 追蹤中的檔是別的系統的 → 只讀。上船只寫 `docs/handoff/ai/vrn2_ship/` 與 VRN-2 交接報告。
- **船包要穩定**:內容沒變就位元組相同(固定時間 · 排序);帶時間的紀錄不進船包。
- **不要用測試替身上船**:容器裡的管理器前版鏈是測試替身(`TESTSTUB`),船包只能由使用者機器的 ⑨ 產生。
- **驗收資料不要截斷**:輸出要用全文;截斷的值就是錯值(「EPS 6.」)。
- **數字比數值**:原文有千分位、字距拆開、小數位不同;只比字面會把對的值當錯。
- **輸出值要獨立驗證**(不同讀取器 · 逐值 · 對欄 · 組句的「計算」值要重算)· **驗證器本身也要被驗**(每個 FAIL 先看原文)。
- 環境相依不能決定燈號 · 薄尾鏈要完整 · 搬檔前先問 git · 平行只放互不相連的步驟 · 先分診再修 · 口徑一致 · 假綠校正 · 不適用 ≠ 黃燈 · 快取鍵包含所有輸入 · 自測不寫真正的 registry。
