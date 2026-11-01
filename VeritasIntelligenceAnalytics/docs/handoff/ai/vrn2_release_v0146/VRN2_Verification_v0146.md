# VRN-2 v0146 容器實測紀錄(2026-10-29)

桌機 10:25 貼回(v0145 · 2546 秒):87.5% busy by another process at launch → launcher chose 平行 1 路 · 優先權 不變;⑦ ≈1180 (擷取 13 · 驗收+摘要 9 · 輸出冊 969 · 冪等閘 151 (R1 73 / R2 78 · parallel works));⑪ 833 秒;④ 93 + 107 (④ / ④b);⑬ duckdb GREEN · 新檔 0 / 已知 52 (incremental proven);⑥c · ⑤b · ⑫b · Workbench v0101 GREEN · 驗證判決寫回。紅燈:same as 08:14: ⑧b rc 1 ← 四點原文核對 FAIL 1 (3014TT-20231005 POINT_3) · 輸出缺項 3 份年度數據 (Daiwa-6278 · 欣銓 3264 · 華南 6143) → needs VRN2_PasteBack_20261029_102505.zip。判讀:the 969 s 輸出冊 is the native second-reader value verification (10,908 values across 52 PDFs) under CPU starvation (1 lane) + OneDrive I/O; not the idempotence gate any more (151 s). 'Why no TWSE/TPEX/YFinance?': the desktop line's own launcher (manager v0249) has ⑥e; this package line never had it → v0146 adds ⑥e / ⑥f.

## 1. 自測

| 檔 | 結果 |
|---|---|
| VRN2_Workbench_v0102 | [PASS] VRN2_Workbench v0102 --selftest · 13 項 · 不過 0 |
| VRN2_HistoryAlign_v0100 | [PASS] VRN2_HistoryAlign v0100 --selftest · 14 項 · 不過 0 |
| VRN2_DataIntegrate_v0100 | [PASS] VRN2_DataIntegrate v0100 --selftest · 15 項 · 不過 0 |
| VRN2_UIAction_v0109 | [PASS] VRN2_UIAction v0109 --selftest · 6 項 · 不過 0 |
| VRN2_SSOTSync_v0101 | [PASS] VRN2_SSOTSync v0101 --selftest · 6 項 · 不過 0 |
| VRN2_ConsensusJoin_v0100 | [PASS] VRN2_ConsensusJoin v0100 --selftest · 7 項 · 不過 0 |
| ActivateVRN-2_v0146 | [PASS] v0146: ⑥e market fetch (absent → GRAY · no book → GRAY · fetch GREEN + fill YELLOW → YELLOW · opt-out) · ⑥f consensus Combined (opt-out run → Combined still built · column order) · ⑬b history align (no book / no market → GRAY · opt-out) · ⑬c integrate scan (none → GRAY · legacy csv → PENDING_ |

## 2. PowerShell 雜湊鏈(pwsh 7.4.6)

```
Run-VRN2-v0146.ps1 parse errors: 0
boot146.ps1 parse errors: 0
Run-VRN1-VRN2-v0107.ps1 parse errors: 0
boot_pair107.ps1 parse errors: 0
cs101.ps1 parse errors: 1
round.ps1 parse errors: 0
vrn2 one-click v0146: code sha = boot H → True (9f7490806d18)
one-liner decodes to boot → True
package zip sha = \67fde9888e9f466d8f3ccf45f2afd2a2d4873e3d82d66493d5ee65202916bb96 → True
operator v0107: code sha = boot H → True (1e54c76d7b8e)
operator H2 = vrn2 one-click v0146 code sha → True
operator banner says v0107 → True
localround H_OP = operator v0107 code sha → True
localround H_CS = chainship md v0101 code sha → True
chainship md WANT = tool v0101 sha → True
```

## 3. 沙盒整輪(套件 v0146 · 19 份真實樣本 · Linux · 無網路 · 共識引擎走離線 fixture)

| 項目 | 值 |
|---|---|
| 收尾 rc | 1(③ 環境檢查 RED in the Linux sandbox only (accelerator deps not in venv; --no-install); same as v0142–v0145)|
| 非綠步驟 | [('③ 環境檢查與補裝', 'RED'), ('⑥c U/I 操作協定', 'GRAY'), ('⑨ 上船 GitHub', 'GRAY'), ('⑩ 整併封存', 'GRAY'), ('⑫a VRN-1 倉同步(借工具前 · 只 fast-forward)', 'GRAY'), ('⑫ PIVOT 資料庫(借用 VRN-1)', 'GRAY'), ('⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 MarketFetch)', 'GRAY'), ('⑥f 共識合併(FactSet / YFinance → Combined 冊)', 'YELLOW'), ('⑬ 輸出位置 · 增量庫(DuckDB)', 'YELLOW'), ('⑬b 歷史對齊(歷史覆蓋預估 · 加減乘除檢驗 · 刪除區)', 'GRAY'), ('⑬c 舊資料庫整合掃描(CSV / XLSX / Google Sheet · 問使用者)', 'YELLOW')] |
| 耗時 | 176.89 秒 |
| 完成判定 | {'verdict': '完成', 'red': 0, 'yellow': 3, 'manager': 'VRN-2 SystemManager v0255'} |
| 個股四項 | {'n': 14, 'all_green': 14, 'step7_seconds': 134} |
| 冪等閘 | GREEN · {'R1': {'elapsed_s': 3.5, 'files': {'JP-2330 20250718.pdf': 2.0, 'GS-6415 20260517.pdf': 3.0, 'Daiwa-1319 20231011(20261006-122413).pdf': 3.5}, 'lanes': 3, 'parallel': True}, 'R2': {'elapsed_s': 4.0, 'files': {'JP-2330 20250718.pdf': 2.0, 'GS-6415 20260517.pdf': 2.5, 'Daiwa-1319 20231011(20261006-122413).pdf': 4.0}, 'lanes': 3, 'parallel': True}, 'total_s': 7.5} |
| 階段耗時 | [計] 階段耗時(秒)· 擷取迴圈 p1loop 34 · 驗收 + 摘要 57 · 輸出冊 30 · U/I 輸出冊頁 0 · 冪等閘 8 · 調節輪 0 · 其他 1 · 總 130 · 收據 VRN2_Phase_Timing_latest.json |
| 四點原文核對 | {'PASS': 52, 'OCR_PENDING': 4} |
| 獨立驗證 | {'basic': "{'PASS': 193, 'OCR': 2}", 'summary': "{'PASS': 65, 'OCR': 5}", 'financial_rows': 4905, 'financial_verdicts': "{'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452}"} |
| 註冊核對 | [計] 註冊核對 · ⑤ 元件登記 GREEN · ⑥c U/I 操作協定 GRAY · ② 定位 VRN-2 程式夾 GREEN · 處理器 VRN2_UIAction_v0109.py · 全部登記成功 |
| ⑤b SSOT-ID | {'lamp': 'GREEN', 'detail': '核發 0 · 衝突 0 · 待核號 521(SSOT 類 112 · 程式類 418)· 自撞 0 · 登記冊 VRN2_Component_Register_v0101.json · 核發冊 尚無(VCGC 還沒核發)'} |
| ⑥e 市場擷取 | {'lamp': 'GRAY', 'detail': '共用夾 functional modules\\VRN 沒有 VRN2_MarketFetch_v*.py(桌機線工具)· 不抓 · ⑬b 歷史對齊與 Combined 的還原價會缺'} |
| ⑥f 共識合併 | YELLOW · 代號 13 / 13 · gate PASS_WITH_WARNINGS · 引擎 VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0121.py · Combined 14 列 |
| Combined 欄序 | REPORT_DATE · FILENAME · TICKER · YFINANCE_TICKER · BLOOMBERG_TICKER · NAME · BROKER · ANALYST · RATING · TARGET_PRICE · TARGET_PRICE(ADJ) · FACTSET_TARGET_PRICE_MEDIAN · YFINANCE_TARGET_PRICE_MEDIAN · 2026_DILUTED_EPS_FACTSET · 2027_DILUTED_EPS_FACTSET · 2028_DILUTED_EPS_FACTSET · 2026_PER_FACTSET · 2027_PER_FACTSET · 2028_PER_FACTSET · CURRENT_PRICE_REPORT · UPSIDE_PCT(ADJ) · ADJ_CLOSE · ADJ_CLOSE_BEFORE_REPORT · TOPIC & SUMMARY · STATUS |
| Combined 第一列(前 19 欄)| {"REPORT_DATE": "2025-10-01", "FILENAME": "CLST-6669 20251001(20261006-052156).pdf", "TICKER": "6669", "YFINANCE_TICKER": "6669.TW", "BLOOMBERG_TICKER": "6669 TT", "NAME": "", "BROKER": "CLSA", "ANALYST": "Kevin Sw Chen", "RATING": "OUTPERFORM", "TARGET_PRICE": "4200.00", "TARGET_PRICE(ADJ)": "", "FACTSET_TARGET_PRICE_MEDIAN": "120.00", "YFINANCE_TARGET_PRICE_MEDIAN": "118.00", "2026_DILUTED_EPS_FACTSET": "5.00", "2027_DILUTED_EPS_FACTSET": "6.00", "2028_DILUTED_EPS_FACTSET": "7.00", "2026_PER_FACTSET": "20.00", "2027_PER_FACTSET": "16.67", "2028_PER_FACTSET": "14.29"} |
| ⑬ 輸出位置 / 增量庫 | {'lamp': 'YELLOW', 'store_engine': 'pyarrow', 'new_files': 14, 'appended': {'BasicInfo': 14, 'FinancialData': 4905, 'Summary': 14, 'Rejected': 815}} |
| ⑬b 歷史對齊 | {'lamp': 'GRAY', 'detail': '沒有市場資料 VRN2_Market_latest.json(⑥e 沒跑或沒抓到)· 不覆蓋'} |
| ⑬c 舊資料庫整合 | {'lamp': 'YELLOW', 'state': 'PENDING_USER', 'candidates': [{'path': '舊基本資料 - Sheet1.csv', 'kind': 'Google Sheet 匯出 CSV', 'target_book': 'BasicInfo', 'mapping': {'Ticker': 'TICKER', 'Date': 'REPORT_DATE', 'Broker': 'BROKER', 'Target Price': 'TARGET_PRICE', 'Rating': 'RATING'}}]} |
| Workbench | {'lamp': 'GREEN', 'version': 'v0102', 'legacy_linked': True} |
| Workbench(無頭 Chromium)| {"errs": [], "ths": ["Report Date / 報告日期", "File Name / 檔案名稱", "Ticker Symbol / 股票代號", "Yahoo Finance Ticker / Yahoo 財經代號", "Bloomberg Ticker / 彭博代號", "Company Name / 公司名稱", "Broker / 券商", "Analyst / 分析師", "Rating / 評等", "Target Price / 目標價", "Adjusted Target Price / 調整後目標價", "FactSet Target Price Median / FactSet 目標價中位數", "YFinance Target Price Median / Yahoo 財經目標價中位數", "2026 Diluted EPS (FactSet) / 2026 稀釋每股盈餘(FactSet)", "2027 Diluted EPS (FactSet) / 2027 稀釋每股盈餘(FactSet)", "2028 Diluted EPS (FactSet) / 2028 稀釋每股盈餘(FactSet)", "2026 PER (FactSet) / 2026 本益比(FactSet)", "2027 PER (FactSet) / 2027 本益比(FactSet)", "2028 PER (FactSet) / 2028 本益比(FactSet)", "Current Price at Report / 報告發布時股價", "Adjusted Upside Percentage / 調整後潛在上漲空間", "Adjusted Close / 調整後收盤價", "Adjusted Close Before Report / 報告前調整後收盤價", "Topic and Summary / 主題與摘要", "Status / 狀態"], "fths": ["Report Date / 報告日期", "File Name / 檔案名稱", "Ticker Symbol / 股票代號", "Broker / 券商", "Page / 頁碼", "Table / 表格", "Item / 科目", "Period / 期間", "Value / 數值(金額欄 百萬台幣)", "Verify / 驗證", "Row / 列", "Section / 段落"], "ds": ["BasicInfo", "FinancialData", "Summary", "Combined", "Rejected"], "stat": [["19", "", true], ["14", "", true], ["1", "", true], ["14", "", true], ["1", "", true], ["20261029_042237", "12px", true]], "logo": ["logo", 40, 40], "first_head": "輸入去重矩陣 · 目前引擎狀態\n偵測到 1 份舊資料庫(Google Sheet 匯出 CSV)· 要不要進行資料整合?\n整合會讀取舊檔、自適應對齊欄位後建立新的整合 Parquet;原有資料在整合成功前絕不刪除,成功後原檔複製到 TEMP(/tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/sc |

## 4. 使用者情境(pwsh · 一鍵 v0146 從假 GitHub 分支取套件 → 跑 → 再貼 → 竄改)

| 項目 | 值 |
|---|---|
| rc | first rc 1 · again rc 1 · tamper rc 1 · done |
| first | [GREEN] ③ 套件 v0146 就位(SHA-256 67fde9888e9f · 套件內 10 檔逐檔核對相符 · 來源 GitHub claude/optimistic-goodall-yhalc5)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v146/t146oc/Download |
| again | [GREEN] ③ 本機已是 v0146 套件(SHA-256 67fde9888e9f · 套件夾 11 檔與已驗證的 zip 逐檔相符)· /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v146/t146oc/Downloads/VRN2_Closeout_v0146 |
| tamper | [YELLOW] ③ 本機套件夾有 1 個檔與已驗證的 zip 不同或不在(ActivateVRN-2_v0146.py)→ 不用它,從本機這份 zip 重新解壓 → [GREEN] ③ 舊套件夾已改名備份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v146/t146oc/Downloads/VRN |
| closeout | [RED] ⑧b 收尾收據 v0146 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1 |
| market | [GRAY] ⑥e 市場擷取(TWSE / TPEX / Yahoo) · 共用夾 functional modules\VRN 沒有 VRN2_MarketFetch_v*.py(桌機線工具)· 不抓 · ⑬b 歷史對齊與 Combined 的還原價會缺 |
| consensus | [YELLOW] ⑥f 共識合併(FactSet / YFinance → Combined) · 共識 YELLOW:擷取環境缺 yfinance(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)→ 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境 · 本輪共識欄留空 · Combined GRAY:Combined 14 列 |
| history | [GRAY] ⑥e 市場擷取(TWSE / TPEX / Yahoo) · 共用夾 functional modules\VRN 沒有 VRN2_MarketFetch_v*.py(桌機線工具)· 不抓 · ⑬b 歷史對齊與 Combined 的還原價會缺 |
| integrate | [GRAY] ⑬c 舊資料庫整合掃描 · NONE · 掃了 2 個夾沒有新的舊資料庫(csv / xlsx / parquet / json) |
| workbench |  |
| registration | [計] 註冊核對 · ⑤ 元件登記 GREEN · ⑥c U/I 操作協定 GRAY · ② 定位 VRN-2 程式夾 GREEN · 處理器 VRN2_UIAction_v0109.py · 全部登記成功 |

## 5. 沒做到 / 沒驗到(照實)

- Windows desktop run of v0146: not yet (next paste-back)
- the launcher's ④ accelerator step writes a bridge copy VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0121.py (= the uploaded v0120 + the [VIA:ACCEL-BRIDGE] header, same as every unbridged runtime member) into the private runtime at run time; ConsensusJoin then takes the highest number, so ⑥f ran the v0121 bridge copy — the shipped v0120 is byte-identical to the upload (sha b50b3ba6f06c8b14…)
- ⑥e in the container: GRAY (the sandbox VIA tree has no shared VRN2_MarketFetch; on the desktop the shared folder has v0112) and the container has no yfinance / network → ⑥e YELLOW there is the honest expectation until the via_tw_fetch env exists
- ⑥f live mode (cnyes + Yahoo) not exercised: the container run used offline engine fixtures for the 13 tickers (consensus values are synthetic); the engine's own live path is the operator's v0120 as uploaded
- ⑬b history alignment ran GRAY in the sandbox (no market json); its 14 selftest cases cover scale / override / Deleted / checks
- ⑬c apply (vrn2://integrate) was exercised by the handler selftest, not from a browser click
- 3014TT POINT_3 FAIL and the 3 missing annual-data books: still need the paste-back zip
- the 969 s 輸出冊 verification phase is not changed this round (would need the manager's second reader to parallelise)
