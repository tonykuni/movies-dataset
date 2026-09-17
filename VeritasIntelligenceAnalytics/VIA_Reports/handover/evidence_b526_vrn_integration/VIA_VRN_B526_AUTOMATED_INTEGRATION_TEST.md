# VRN B526 自動化整合測試報告

**完成時間：** 2026-09-16T08:45:51.489717+00:00
**VRN 軟體整合判定：** **GREEN**
**VIA/VDF 完整串接判定：** **PARTIAL_BLOCKED**

## 測試矩陣

| 模組 | 退出碼 | 結果 |
|---|---:|---|
| vrn_072 | RC=0 | PASS |
| vrn_073 | RC=0 | PASS |
| vrn_074 | RC=0 | PASS |
| vrn_080 | RC=0 | PASS |
| vrn_082 | RC=0 | PASS |
| vrn_086 | RC=0 | PASS |
| nlp_744 | RC=0 | PASS |

| 項目 | 實測結果 |
|---|---|
| VRN active compile | 288/288 |
| VRN active import | 288/288 |
| VRN panorama state | GREEN |
| PDF fitz／pdfplumber | GREEN |
| PDF pages | fitz=2; pdfplumber=2 |
| PDF tables | 1 tables; 12 non-empty cells |
| VIA/VDF full integration | PARTIAL_BLOCKED |

## 結論

VRN B526 的 active module compile/import、正主 selftest、NLP 掛載、PDF 雙引擎 regression 與 VIA/VDF 串接均已由實際命令執行並保存輸出。軟體整合 gate 判定為 **GREEN**。完整鏈路仍受 64 份未掛載 Windows 原始 PDF/DOCX 限制，因此整體內容級驗收維持 **PARTIAL_BLOCKED**，不將 synthetic fixture 結果冒稱為原始報告通過。

機器結果：`VRN_B526_AUTOMATED_INTEGRATION_RESULT.json`
各模組輸出與命令輸出均收容在同一 evidence 目錄。
