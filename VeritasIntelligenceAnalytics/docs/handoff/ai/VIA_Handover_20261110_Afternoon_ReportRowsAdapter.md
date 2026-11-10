# 交接 2026-11-10(下午)· VRN2_ReportRows v0101 改為轉接層

操作員:「先前有成過 為何重工」→ 我承認:v0100 沒先查既有引擎就另寫一套。操作員 YES → 改回接既有成功的引擎。

## 事實(查過的)
- 個股四點:VRN-2 主線早有(ENG062 抽句 → BookSource 四點;VerbatimVerifier / IndependentVerifier 逐值驗;v0125–v0176 多輪)。輸出冊 `VIA_Reports/vrn2/output/VRN2_Summary_latest.json`(POINT_1–4)+ `VRN2_BasicInfo_latest.json`(RATING · TARGET_PRICE · CURRENT_PRICE_REPORT)。
- 非個股:操作員自己的非個股摘要器 v0300 / v0310(`nonstock_v0310/engine`)早有 `topic_rows`(一主題一行)· `company_rows`(晨會一家一行)· `report_summary`;11-03 桌機結果上傳過。容器跑不動只因缺 `internal/NON_STOCK_CORE_v0200.py`(SHA 92f53d82…)。
- VRN-1 摘要器 `VIA_Financial_Document_Summarizer_Engine_1.py` 早在 VRN 夾。

## v0101 做法(`functional modules/VRN/VRN2_ReportRows_v0101.py` · v0100 薄尾 · v0100 一字不動)
- 個股:主線冊有這份 → 四點 / 評等 / TP / 收盤直接取主線(檔名去中文後比對,另以代號 + 日期輔比)· source = VRN-2 主線。
- 非個股:v0310 RESULTS.json(當場跑或 `--nonstock-out` 指桌機輸出)→ 產業依 INDUSTRY 一產業一行 · 晨會一家一行 · 其他一主題一行 · source = 非個股摘要器 v0310。
- 都沒有 → v0100 抽取暫代,行上寫原因(主線冊沒有這份 / 缺 NON_STOCK_CORE)。
- 原句驗證照跑,但不替上游背書:v0310 的點若不是原句 → MISMATCH 照實。
- 自測 10/10 + v0100 鏈 11/11;容器 13 份真 PDF:53 行全暫代(主線冊只有另 5 份且四點空 · v0310 缺 NON_STOCK_CORE)· 原句驗證 155/155。

## 登冊(main 上的冊不就地改 → 出新版)
需求冊 v0245(VRN-REQ019 改指回既有引擎 · why_rework)· 工作流冊 VRN v0109(VRN-WKF011 → v0101)· 盤點冊 v0221(+V-vrn2-reportrows-v0101)· 交接案 V-vrn2-reportrows-v0101 rc 0 · 待辦 `VRN-REQ019:nonstock-core`(操作員)。

## 桌機一行
`python "functional modules/VRN/VRN2_ReportRows_v0101.py" run --pdf-dir <報告夾> --vrn2-books <VRN-2 輸出夾> [--nonstock-out <v0310 輸出夾>]`
