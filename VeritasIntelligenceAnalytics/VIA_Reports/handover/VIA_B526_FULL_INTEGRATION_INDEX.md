# VIA B526 完整串接驗收索引

完整報告：`VIA_VRN_VDF_FULL_INTEGRATION_B526.md`

機器報告：`evidence_b526_full_integration/VIA_VRN_VDF_FULL_INTEGRATION_B526.json`

可重跑腳本：`evidence_b526_full_integration/run_via_vrn_full_integration_b526.py`

基線判定：VRN 288/288 compile/import GREEN、PDF dual-engine GREEN、VDF DuckDB 結構完整、ENG073 36/36 PASS；原始 Windows 樣本未掛載，故不作內容級宣稱。

最新功能級驗收：2026-09-16 17:11（Asia/Taipei）；CGC154 中央站 4/5 GREEN、80.0%。最新機器報告：`VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.json`；HTML 展示：`VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.html`。終極裁決為 `RED`：價格資料最早 2024-01-02，未達要求的 2023-01-01；64 份 Windows 原始樣本仍不可讀；VAP 尚缺 TA_RUN/TPLRUN 真實 run 產物。

VRN B526 自動化整合測試：`evidence_b526_vrn_integration/VIA_VRN_B526_AUTOMATED_INTEGRATION_TEST.md`；VRN 軟體 gate GREEN，7 個正主/NLP selftest 全部 RC=0，active tree 288/288 compile/import。

本批功能補強交接：`VIA_CGC154_FUNCTIONAL_ACCEPTANCE_B526.md`。新增 CGC154 已接入 PowerShell Register、InputConsole、Workflow SSOT、Interface Contract Registry 與 VCGC Component Inventory；VDF ENG087 v0101 已加入 2023 起始日實際覆蓋閘，避免市場清單假綠。
