# VIA B526 完整串接驗收索引

完整報告：`VIA_VRN_VDF_FULL_INTEGRATION_B526.md`

機器報告：`evidence_b526_full_integration/VIA_VRN_VDF_FULL_INTEGRATION_B526.json`

可重跑腳本：`evidence_b526_full_integration/run_via_vrn_full_integration_b526.py`

判定：VRN 288/288 compile/import GREEN、PDF dual-engine GREEN、VIA/VDF central lists GREEN、VDF DuckDB integrity PASS、ENG073 36/36 PASS；整體因 64 份 Windows 原始 PDF/DOCX 未掛載而為 `PARTIAL_BLOCKED`。

最新重跑：2026-09-16 16:30（Asia/Taipei）；13/14 gates PASS，唯一阻擋仍為原始 Windows 樣本不可讀。最新重跑輸出：`evidence_b526_full_integration/real_acceptance_rerun_latest.txt`。本次同步並修正 SQL 結果的 Markdown 顯示格式。

VRN B526 自動化整合測試：`evidence_b526_vrn_integration/VIA_VRN_B526_AUTOMATED_INTEGRATION_TEST.md`；VRN 軟體 gate GREEN，7 個正主/NLP selftest 全部 RC=0，active tree 288/288 compile/import。
