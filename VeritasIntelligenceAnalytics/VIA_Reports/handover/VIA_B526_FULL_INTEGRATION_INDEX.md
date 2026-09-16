# VIA B526 完整串接驗收索引

完整報告：`VIA_VRN_VDF_FULL_INTEGRATION_B526.md`

機器報告：`evidence_b526_full_integration/VIA_VRN_VDF_FULL_INTEGRATION_B526.json`

可重跑腳本：`evidence_b526_full_integration/run_via_vrn_full_integration_b526.py`

基線判定：VRN 288/288 compile/import GREEN、PDF dual-engine GREEN、VDF DuckDB 結構完整、ENG073 36/36 PASS；原始 Windows 樣本未掛載，故不作內容級宣稱。

最新功能級驗收：2026-09-16 17:11（Asia/Taipei）；CGC154 中央站 4/5 GREEN、80.0%。最新機器報告：`VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.json`；HTML 展示：`VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.html`。終極裁決為 `RED`：價格資料最早 2024-01-02，未達要求的 2023-01-01；64 份 Windows 原始樣本仍不可讀；VAP 尚缺 TA_RUN/TPLRUN 真實 run 產物。

VRN B526 自動化整合測試：`evidence_b526_vrn_integration/VIA_VRN_B526_AUTOMATED_INTEGRATION_TEST.md`；VRN 軟體 gate GREEN，7 個正主/NLP selftest 全部 RC=0，active tree 288/288 compile/import。

本批功能補強交接：`VIA_CGC154_FUNCTIONAL_ACCEPTANCE_B526.md`。新增 CGC154 已接入 PowerShell Register、InputConsole、Workflow SSOT、Interface Contract Registry 與 VCGC Component Inventory；VDF ENG087 v0101 已加入 2023 起始日實際覆蓋閘，避免市場清單假綠。

## B527 統一 SSOT／自動編碼整合

交接報告：`VIA_B527_SSOT_AUTOCODE_INTEGRATION_HANDOVER.md`
機器狀態：`VIA_B527_SSOT_AUTOCODE_INTEGRATION_STATUS.json`
機器 manifest：`../ssot_autocode/VIA_SSOT_AUTOCODE_latest.json`
HTML 狀態頁：`../ssot_autocode/VIA_SSOT_AUTOCODE_latest.html`

CGC155 自測 9/9、VCGC 19/19、中央治理家族 12/12、Workflow Composer 12/12；介面掃描 0 新編／0 漂移／2780 穩定；中央元件冊 4953 active、0 AST 錯。總裁決為 `YELLOW`，唯一缺口是尚不存在的 `functional modules/VRN/db/vrn_reports.duckdb`，不得用空資料庫偽造 GREEN。

## B528 VRN 報告資料庫驗收

交接報告：`VIA_B528_VRN_DATABASE_ACCEPTANCE_HANDOVER.md`
機器狀態：`VIA_B528_VRN_DATABASE_ACCEPTANCE_STATUS.json`
裁決：**GREEN**（ENG073 36/36 PASS；指定庫 status PASS；只讀 SQL PASS）。使用者 Windows 64 份原始樣本仍待掛載，未被本批假稱已解析。

## B529 NLP→VRN→VDF 三頁矩陣鏈

交接報告：`VIA_B529_NLP_VRN_VDF_MATRIX_HANDOVER.md`
機器狀態：`VIA_B529_NLP_VRN_VDF_MATRIX_STATUS.json`
最新 HTML：`../vrn/nlp_pipeline/NLP_VRN_VDF_latest.html`
最新 JSON：`../vrn/nlp_pipeline/NLP_VRN_VDF_latest.json`
最新 Markdown：`../vrn/nlp_pipeline/NLP_VRN_VDF_latest.md`
Windows PowerShell：`VIA_NLP_VRN_VDF_B529.ps1`

B529 最後 Run `B529-20260916T105325-68faf473` 實測 2 個倉內 PDF/DOCX 夾具：ENG072 2/2、NLP 2/2、證據摘要 2/2、ENG073 rc=0、DuckDB GREEN（`vrn_nlp_text_summary=2`、`vrn_pipeline_runs=4`）；三頁報告會自動開啟並同時輸出 HTML/JSON/Markdown。總裁決 `YELLOW`，VDF 唯一阻擋仍是股票價格資料最早 2024-01-02，未達 2023-01-01。新中央節點 `vrn_nlp_vrn_vdf_pipeline`、工作流 `vrn_nlp_vdf_pipeline` 已登錄；Workflow 12/12、VCGC 19/19。

## B531 25 項 PowerShell 加速器與 Python 單點掛載

交接報告：`VIA_B531_25_ACCELERATOR_CONTROL_HANDOVER.md`
機器狀態：`VIA_B531_25_ACCELERATOR_CONTROL_STATUS.json`
三頁狀態頁：`VIA_B531_25_ACCELERATOR_CONTROL.html`
Windows 一貼式 probe：`VIA_B531_25_ACCELERATOR_CONTROL.ps1`
證據包：`evidence_b531_accelerator_control/`

B531 的 CGC156 離線控制面實測 **GREEN 21/21、`READY_FOR_25`**；SSOT 與 PowerShell roster 均為 ID `01..25`。`sitecustomize.py` 實際將 25-roster 與 CGC156 identity 注入 VIA 啟動的 Python；VDF probe 顯示 `VIA_ACCEL_BOOT=cache:9/88:17env`、`via_net=True`、Celeritas/Aegis lazy mount。QuantGuard selftest 8/8 PASS；新增 `VIA_QuantGuard_TA_Lib_Policy_v0100.json` 與政策法 L50，指定 QuantGuard 為唯一活動技術分析／因子路徑，TA-Lib/talib 不得安裝、import、載入、復活、路由或作活動 benchmark；歷史 L36/L41/L42 標記 SUPERSEDED。canonical active mounts 掃描無禁用接線。SuperAccel 為 88 catalogued／9 available／79 missing-or-stub，誠實保留缺件，不把 25 roster 說成 25 套獨立演算法已安裝。

中央同步 8 站中 7 站 exit 0；`iface_sync=1` 僅代表 6 個既有 InputConsole contract drift，未被盲改或假稱已解。VCGC ACTIVE 4,996/4,996、家族 237/237、AST errors 0。Windows 首次 probe 實際發現 dot-source scope 導致 25 項回退為 20 項，已改為 global canonical state，需 pull 最新修正後重跑；sandbox 仍無 PowerShell parser。Windows `C:\測試樣本報告` 原始 PDF/DOCX 仍未掛載，資料補庫仍停止。
