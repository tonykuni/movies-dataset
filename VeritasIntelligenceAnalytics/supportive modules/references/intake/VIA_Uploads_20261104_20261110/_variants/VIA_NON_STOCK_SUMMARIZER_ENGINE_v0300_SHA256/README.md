# VIA NON-STOCK SUMMARIZER ENGINE v0300

## 核心原則
**One Report = One Main Row · One Title + Four Points · Details on Demand**

v0300 不是重新寫 VRN-2。主引擎直接復用：
- `VRN_M03_PDF_Layout_JSON_v3.py`：PDF Layout / font / role / block
- `VRN_MDL003_TableRestorer.py`：9-step Text Repair / noise / dedup
- `VRN_M07_Summarizer.py`：本地 extractive NLP helper（v0300 禁止模型下載）
- `NON_STOCK_CORE_v0200.py`：Story / Claim / Evidence / Guards

## 四張輸出表
1. `REPORT_SUMMARY`：一報告一列，首頁/Pivot 用
2. `TOPIC_DETAIL`：一主題一列
3. `COMPANY_DETAIL`：一公司 × 報告一列
4. `EVIDENCE_DETAIL`：一 Claim / Evidence 一列

## Main row header
`REPORT_ID, REPORT_DATE, FILE_NAME, REPORT_TYPE, SOURCE, ANALYST_AUTHOR, MAIN_STORY, MAIN_INDUSTRY, TITLE, POINT_1, POINT_2, POINT_3, POINT_4, DIRECTION, HORIZON, COMPANY_COUNT, TOPIC_COUNT, EVIDENCE_COUNT, STATUS`

## 一標題四重點
- Point 1 = 核心結論 / What
- Point 2 = 驅動因素 / Why
- Point 3 = 影響對象 / Who
- Point 4 = 展望、風險、下一步 / What next

## Windows
```powershell
.\Invoke-NON-STOCK-SUMMARIZER-v0300.ps1 -InputPath "C:\測試樣本報告" -OpenHtml
```

## Python
```powershell
python .\engine\VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300.py "C:\測試樣本報告" --outdir .\output
```

## 治理
- Local only
- 不改原始來源
- 不下載模型
- VRN-2 模組只讀復用
- 主表簡潔，細節留在 child tables


## v0300 Real Test
- 6 available real samples: PASS
- REPORT_SUMMARY rows: 6
- TOPIC_DETAIL rows: 143
- COMPANY_DETAIL rows: 63
- EVIDENCE_DETAIL rows: 2516
- All tested PDFs used `VRN2_M03_LAYOUT+MDL003_REPAIR`.
