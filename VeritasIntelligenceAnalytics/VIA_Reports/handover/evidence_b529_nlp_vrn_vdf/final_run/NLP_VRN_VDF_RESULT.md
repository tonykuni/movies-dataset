# VIA NLP → VRN → VDF 實測矩陣報告（YELLOW）

- **Run ID：** `B529-20260916T105325-68faf473`
- **輸入：** 2 件；sidecar 2 件
- **NLP：** 2 件；摘要通過 2 件
- **DuckDB：** `/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/functional modules/VRN/db/vrn_reports.duckdb`

## 第 2 頁｜完整測試矩陣

|序|階段|元件|預期|實際|結果|
|---:|---|---|---|---|---|
|1|輸入樣本|PDF/DOCX/Image intake|>=1 個可支援檔案|2 個|**PASS**|
|2|首頁擷取|VRN ENG072|returncode=0；sidecar 齊全|rc=0; sidecar=2|**PASS**|
|3|NLP 文字與摘要|SUP_MDL744 NLPApplicationHub|Hub VERIFIED；摘要可回溯|processed=2; summary_ok=2|**PASS**|
|4|VRN 結構化入庫|VRN ENG073|returncode=0；DB 可讀|rc=0; DB=GREEN|**PASS**|
|5|資料庫驗證|vrn_reports.duckdb|NLP 表與 pipeline runs 在位|{"vrn_report_basic": 2, "vrn_report_metrics": 0, "vrn_report_analyst": 0, "vrn_nlp_text_summary": 2, "vrn_pipeline_runs": 4}|**PASS**|
|6|VDF 中央狀態|VDF ENG087 / MARKET_LISTS|三清單 GREEN|RED|**BLOCKED**|

## VDF 阻擋原因

- tw_stock_universe：價格資料最早日 2024-01-02 晚於要求起始日 2023-01-01；需補齊 2023 起資料

## 第 3 頁｜逐件依序結果

|序|報告|正規化字數|TextProcessor|摘要|span|摘要點|
|---:|---|---:|---|---|---|---|
|1|synthetic_financial_report|441|VERIFIED|OK|True|Generic Layout Engine Test Annual Research Report 1. / Executive Overview This is the main body paragraph used to establish the body font size. / A second body line confirms paragraph-level classification. / 1.1 Key Observation The document contains a table and one figure for layout testing. / Table 1: Quarterly Data Metric Q1 Q2 Q3 Revenue 100 120 150 Profit 20 25 31 Source: Synthetic data Figure 1: Trend Overview Source: Generated locally|
|2|Veritas_VOFIE_Reconstructed|998|VERIFIED|OK|True|VOFIE_Sample_Input · 全格式讀取、主題重構與模板生成報告 / AI candidates never auto-apply / 來源唯讀; / VOFIE_Sample_Input.md — markdown, 724 bytes, d5e4960d8292a363. / 完整來源內容、重複主題、行號與雜湊仍保留在後續章節與 Component Specs JSON。 / policy=STRUCTURAL_CANDIDATE_ONLY;|

## AI 接手提示

JSON 是機器裁決正本；HTML 是三頁矩陣；DuckDB `vrn_nlp_text_summary` 是文字與證據摘要資料表。VDF 若非 GREEN，必須讀 `vdf_gate.blockers`，不得把整批標成 GREEN。
