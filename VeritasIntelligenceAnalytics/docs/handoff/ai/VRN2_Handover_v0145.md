# VRN-2 交接報告 v0145 · 2026-10-27（第 48 → 59 輪 · 啟動器 v0124 → v0145）

> 給人看的在前（進度總表、缺漏清單），給下一個 AI 的在後（技術決定、規則、路徑）。
> 原則不變：只增不減 · 薄尾新版（前版不動）· 同名不同內容不覆寫 · 基層建、VCGC 審核編號 · 缺套件交 VCGC。

## 1. 今日結果（第 59 輪 · 2026-10-27 23:16）

| 項目 | 狀態 |
|---|---|
| 完成判定 ⑧ | **完成** · 紅 0 黃 5 · 52 份個股報告全綠 · 退步 0 · 鎖定 `VRN2_Lock_20261027_230231.json` |
| 上船 ⑨ | 主分支 298 筆落後無法自動合併 → 推到 `vrn2-auto`（81dc26dfc）。**v0144 起改持續解衝突推主分支**（第 60 輪驗證） |
| 封存 ⑩ | 完成（被取代舊版 0） |
| 市場資料 ⑥e | 路徑問題已解（橋接根），卡在鎖冊雜湊（CRLF）→ **v0106 修**（第 60 輪驗證） |
| 發布層 | 已跑：累計 BasicInfo 52 · Summary 52 · FinancialData 8,391（11,513 去重後）· VIA 根在 OneDrive 自動同步 · Google Sheet 未啟用 |
| SSOT 統一冊 | 145 條（regex 41 · 同義字 101 · 規則 3）· 衝突 0 · VCGC 冊未找到 |
| U/I 處理器 | `VRN2_UIAction_v0105.py`（publish 動作 + 轉交另一線 v0103 的 pick / audit） |

## 2. 現役版本

| 元件 | 版本 | 內容 |
|---|---|---|
| 啟動器 | **ActivateVRN-2 v0145** | 內嵌下列全部 · 缺才落地 · 雜湊比對 · CRLF 容忍 |
| VRN-2 SystemManager | **v0249**（鏈 v0244→v0245→v0246→v0247→v0248→v0249） | v0245 分析師標籤 / 四重點補滿 · v0246 市場資料接回 · v0247 V2 規範 · v0248 Headers V3 · v0249 發布層 + 面板 |
| 擷取引擎 ENG397 | v0129（鎖 `33ff9eae8c11`） | 未動 |
| 摘要器 ENG062 | v0114 現役 | 未動 |
| MarketFetch | **v0106**（v0100～v0105 保留） | 包 VDF_TW_DataFetchEngine v036（不改一字） |
| VDF 引擎包 | `_vdf_fetch\VDF_TW_DataFetchEngine_v036.py`（24 檔） | 離線回歸 28/28 |
| 發布引擎 | VRN2_Publish v0100 | 累計 / 格式 / 雲端 / Google Sheet |
| U/I 處理器 | VRN2_UIAction v0105 | 另一線 v0102～v0104 保留 |
| SSOT 統一引擎 | VIA_SSOT_Unify v0100 | 每輪 ②s |
| SSOT 冊 | VRN2_Regex v0103 · VRN2_Synonyms v0101 · VRN2_BasicInfo_Headers v0100 · VRN2_Publish_Config v0100 | 只增不減 |

## 3. 今日時間軸（啟動器版本 → 做了什麼）

| 版 | 管理器 | 內容 |
|---|---|---|
| v0124～v0129 | v0243→v0244 | 兩線合併（共同祖先 v0231 · 合併點 v0243/v0244）· `_acc_parallel` 重綁（假退步）· ⑨ 假綠 / 未追蹤衝突 / vrn2-auto 備援 |
| v0130～v0133 | v0244 | ⑥d VDF 橋探測 · SSOT 冊 · ③ LIBS 交 VCGC · `--diagnose` · CRLF 容忍 · ②r 鏈修復（v0152/v0153 內嵌） |
| v0134 | v0245 | 分析師「研究員：」標籤（兆豐 4 份抓到）· 四重點不足本文平均取 |
| v0135～v0136 | v0246 | MarketFetch v0100/v0101 · Regex v0103 三種代碼 × 9 類 ETF · 市場資料接回基本資料 / 摘要 |
| v0137 | v0246 | ②s 三系統 SSOT 統一冊（VRN + VDF + VCGC 若在 · 編號留 VCGC） |
| v0138 | v0246 | MarketFetch v0102 只抓必要日期（最新 7 天 + 報告日前 7 天 · 相近合併）+ 年度財報 n-3～n |
| v0139 | **v0247** | V2 規範：純小數 · ROE 平均權益 · PER 稀釋 · 實際蓋過預估一期核對（減法 + 除法 · 自動辨單位）· STATUS 末欄 · ②s `v2` 未定義修 · ⑥e 失敗自動 `--doctor` |
| v0140 | **v0248** | Headers V3：固定 16 欄 + 7 項 × 三年 + 近期雙月內暨財報發布前標註（倒數第二欄）+ STATUS 末欄 · 表頭冊 + 正式英文 CSV |
| v0141 | **v0249** | 發布層：累計去重（duckdb · TEMP 溢寫）· parquet / CSV UTF-8 BOM / Google Sheet 服務帳戶 · 雲端同步夾偵測 · 面板「發布設定」區 |
| v0142 | v0249 | MarketFetch v0104：價格每輪重抓 · 財報只補缺 · latest 過期才抓 |
| v0143 | v0249 | MarketFetch v0105 橋接根（鎖冊 path 相對 movies-dataset 多一層）· UIAction v0105 · ⑥e 失敗黃燈不擋完成 |
| v0144 | v0249 | MarketFetch v0106 鎖冊雜湊 CRLF 正規化（真換版不繞過）· ⑨ 持續解衝突 |
| **v0145** | v0249 | 本交接報告 |

## 4. 缺漏清單（依優先序）

| # | 項目 | 狀態 / 下一步 |
|---|---|---|
| 1 | ⑥e 市場資料 | v0106 正規化雜湊：第 60 輪看「只差行尾」是否出現並轉綠。若印「鎖冊過期」= 網路工具真的換版 → **交 VCGC 重鎖**（VRN 不繞過） |
| 2 | 市場填值 / V2 核對 / V3 比率 | 全部依賴 ⑥e；通了之後看「市場填值 代號 n · 完整 x」「v0247 V2 規範 … 通過 / 不過」「三年 EPS 有值」 |
| 3 | ⑨ 主分支 | v0144 持續解衝突第一次會併回落後的 298 筆（衝突留本機 · 對方新增保留 · 帳本 `registry\VRN2_GitMerge_Ledger.jsonl`）。若仍退 vrn2-auto，貼包會印原因 |
| 4 | DPS 遞延規則（V2 第 5 條） | **未實作**：VDF v036 無股利資料集。需在 VDF 加 TWSE 除權息 OpenAPI 擷取後才能認列；目前 STATUS 註記 |
| 5 | U/I 依設計模板 1b 簡化 | **未做**：`claude.ai/design/...Veritas Header.dc.html` 讀取需核准或匯出附檔 |
| 6 | VCGC `governance_vocab.json` | 統一冊每輪找不到 → 需告知路徑或 VCGC 把它放到 VIA 根下固定位置；三份副本在 `VIA_Reports\vrn2\ssot_unified\` 等 VCGC 核號 |
| 7 | ③ 缺必裝 3 | docling（PyPI）· superextract · via_nlp_engine（後兩者是內部模組，pip 不到 → 路徑掛載 / 本機 wheel）· 請求冊 `registry\VRN2_ENV_REQUEST_latest.json` · 交 VCGC |
| 8 | Google Sheet | 引擎與面板就緒；需服務帳戶 JSON + 試算表分享 + gspread（缺 → 交 VCGC） |
| 9 | 輸出冊缺項 8 份 | Daiwa-6278 / 欣銓 / 振曜 年度數據 · MQ-1560 TITLE · 兆豐 4 份「四點原文證據未齊」（另一線口徑） |
| 10 | 華南 Email CONFLICT | `1-450@entrust.com.tw` ≠ `450@entrust.com.tw`（疑分機黏在前）· 判 CONFLICT 不輸出是對的 · 需原文片段定案 |
| 11 | 兆豐基本資料一格多值 / 本文碎片 | ENG397 下一輪 |
| 12 | 兩線入口合一 | Closeout `Invoke-VRN2-Closeout` + ActivateVRN-2 · 穩定後 |

## 5. 規則與技術決定（給下一個 AI）

- **薄尾鏈**：v0244 是兩線合併點；新版 ≥ v0245；每版 `PRIOR_NAME` 指前版；`_acc_parallel` 等必須 `_rebind` 本版；`vrn2 / _native_vrn2` 內部的 `_out_books / _ui_panel_html / completion` 走本版。
- **血緣**：`LINEAGE`（原始 sha）+ `LINEAGE_NORM`（CRLF→LF 正規化 sha）；工作樹 CRLF 不算外來 / 退步 / 不覆蓋。使用者機器上的 v0246 是「寫死 MarketFetch v0100」版（sha `c95ad0eda610`），v0247 以它為前版。
- **只增不減**：同名不同內容立即停止不覆寫；U/I 處理器版號跨兩線取最高（v0105 轉交 v0103）。
- **市場資料**：價格 / 還原價每輪重抓（Yahoo 因子會變）；財報 (代號, 年度) 已落盤不再打 MOPS；latest 只在缺或過法定期限（3/31 · 5/15 · 8/14 · 11/14）才抓。缺 Adj Close 不拿 Close 冒充；核對超差 MISMATCH 留空。
- **橋接根**：`%TEMP%\VIA_progress\vrn2_via_root\supportive modules\registry\VIA_ToolVersion_Lock_v0100.json`（path 絕對化 · sha 正規化後相同才改用實際位元組雜湊）+ 加速器轉接；引擎 `--via-root` 指向它；引擎仍走鎖版網路工具並驗雜湊。
- **V2 規範**（v0247）：歷史實際蓋過預估需「一期重複核對」通過（比率 0.97～1.03 · 差額記錄）才允許同檔預估被蓋；原值不刪（`VALUE` / `VALUE_FINAL` / `VALUE_SOURCE` / `RECON_RATIO` / `RECON_DIFF`）；百分比純小數；ROE = NI / 平均權益；PER 嚴格稀釋 EPS；STATUS 末欄。
- **Headers V3**（v0248）：欄序固定；程式鍵不變，介面 / 匯出用 Formal English Title Case（`SSOT\VRN2_BasicInfo_Headers_v0100.json` · `VRN2_BasicInfo_latest_formal.csv`）；N = 報告年；標註欄 = 兩個月內（≤ 61 天）+ 最近已結束期間的法定期限之前 / 之後。
- **發布層**：累計主鍵（BasicInfo / Summary = FILENAME · FinancialData = FILENAME|ITEM|PERIOD_STD|PAGE|ZONE）去重保留最新 RUN_TS；duckdb `temp_directory` = TEMP；CSV UTF-8 BOM；Excel 1,048,576 列 / Sheet 1,000 萬格提醒；Google 三步（服務帳戶 JSON → 分享給 client_email → 面板選檔 + 貼網址）；VIA 根已在 OneDrive 內不另複製。
- **SSOT 統一**：基層（VRN）建一本 + 衝突清單，三份副本內容相同，`number` 留空給 VCGC；regex 等價寫法（測試向量相同）= EQUIVALENT 不算衝突。
- **⑨**：只提交 VRN-2 自己的檔；完成才推；持續解衝突（merge upstream · 衝突留本機 · 對方新增保留 · 我方刪對方改留對方 · 帳本）；仍失敗退 vrn2-auto。
- **環境**：LIBS / ENV 由 VCGC 安裝；VRN-2 只檢查並寫請求冊；OCR 隔離環境 `envs\vrn2_ocr`；VDF 包另有 `envs\via_tw_fetch`。

## 6. 路徑

- VIA 根 `<ROOT>` = `C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`
- 程式夾 `<ROOT>\functional modules\VRN\` · SSOT `…\VRN\SSOT\` · 血緣 `…\VRN\registry\VRN2_Lineage_Register.json` · VDF 包 `…\VRN\_vdf_fetch\` · 封存 `…\VRN\_archive_vrn2\`
- 輸出 `<ROOT>\VIA_Reports\vrn2\output\VRN2_{BasicInfo,FinancialData,Summary}_latest.*`（+ `_formal.csv` · `VRN2_Reconcile_latest.json`）· 市場 `…\vrn2\market\VRN2_Market_latest.json` · VDF 落盤 `…\vrn2\market\vdf\` · 發布 `…\vrn2\publish\cumulative\` · 統一冊 `…\vrn2\ssot_unified\`
- 鎖冊 `<ROOT>\supportive modules\registry\VIA_ToolVersion_Lock_v0100.json`（network.path 相對 movies-dataset）
- 啟動器 `C:\Users\tonyk\Downloads\ActivateVRN-2.py` · git 分支 main / `vrn2-auto`

## 7. 執行

```powershell
& {
  $A = "C:\Users\tonyk\Downloads\ActivateVRN-2.py"
  if (-not (Test-Path -LiteralPath $A)) { Write-Host "[RED] 找不到 $A" -ForegroundColor Red; return }
  $m = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
  $V = if ($m) { [int]$m.Matches[0].Groups[1].Value } else { 0 }
  if ($V -lt 145) { Write-Host "[RED] v$('{0:D4}' -f $V) · 請重新下載 v0145" -ForegroundColor Red; return }
  $py = Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
  if (-not $py) { Write-Host "[RED] 找不到 python" -ForegroundColor Red; return }
  Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue
  & $py.Source $A
}
```
