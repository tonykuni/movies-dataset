# VRN-2 非個股摘要器 v0300 入倉(2026-11-05 · 操作員「新的一個標題四個重點請用新的 SUMMARIZER · NON-STOCK 用附件」)

| 項目 | 內容 |
|---|---|
| 附件 | `VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300_SHA256_1.zip`(原樣入倉 · SHA-256 `d572963ad6eb7c68…`)· 內含 engine .py(38,033 B · SHA-256 `c9cd3003160fa07c…`)· README · OUTPUT_DATAFRAME_CONTRACT · QA_v0300.json(gate PASS · selftest 5/5 · 6 份真報告 PASS)· RESULTS_PREVIEW · REPORT_SUMMARY.html · Invoke-NON-STOCK-SUMMARIZER-v0300.ps1(留在 zip 裡 · 規則:倉裡不放散的 .ps1)|
| 契約 | One Report = One Main Row · **TITLE + POINT_1(What)/ POINT_2(Why)/ POINT_3(Who)/ POINT_4(What next)** · 四張表 REPORT_SUMMARY / TOPIC_DETAIL / COMPANY_DETAIL / EVIDENCE_DETAIL · 本地 · 不下載模型 · 不改來源 |
| **跑不起來的原因** | 引擎第 110–115 行用 `importlib` 載入 **`<ROOT>/internal/NON_STOCK_CORE_v0200.py`**、**`<ROOT>/reuse/vrn2/VRN_M03_PDF_Layout_JSON_v3.py`**、`<ROOT>/reuse/vrn2/VRN_MDL003_TableRestorer.py`、**`<ROOT>/reuse/vrn2/VRN_M07_Summarizer.py`**(ROOT = engine 夾的上一層);附件只有 engine 一支 + 文件。粗體三支**不在附件、不在本倉(movies-dataset)、不在 VRN-1 倉(via-vdf-vrn)**、本機所有 zip 也沒有;只有 `VRN_MDL003_TableRestorer.py`(本倉 `functional modules/VRN/` · 有 `TextRepairEngine.repair_text_blocks`)對得上。附件裡的 SHA txt 指的是另一個完整包 `VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300.zip`(`8d7d2cef…`),那一包應該含 `engine/ internal/ reuse/` 三夾。|
| 引擎要的 API | NON_STOCK_CORE:Claim · SourceBlock · PROFILE_* · def_extract_input / def_extract_claims / def_profile_router / def_guess_block_type / def_normalize_text / def_parse_messenger_blocks / def_apply_note_layers / def_similarity · NUMBER_RE / URL_RE;VRN_M03:analyze_pdf_layout · extract_blocks_pymupdf;VRN_M07:load_libraries(+ extractive_summary_fallback)|
| VRN-2 現況 | v0227 起範圍 = 只擷取個股報告;非個股在 digest 標 `SKIP:非個股報告`(vrn_report_digest 尾版 v0117)· 沒有非個股的四重點 |

## 接法(等完整包到了才做 · 不寫測不了的程式)

1. 完整包原樣入 `functional modules/VRN/nonstock_v0300/`(engine / internal / reuse 三夾照它的相對路徑 · 逐檔 SHA 釘住 · 一字不改;`reuse/vrn2/VRN_MDL003_TableRestorer.py` 與本倉同名檔逐位元對比,不同就照附件的、記在冊)。
2. VRN-2 新薄尾(處理器 / 啟動器新版號):digest 判 `SKIP:非個股報告` 的 PDF 改送 v0300 `run()` → 四張表寫到 `VIA_Reports\vrn2\nonstock\`(REPORT_SUMMARY = 一報告一列 · 一標題四重點)· Workbench 加「非個股」分頁只讀這張表;個股流程一字不動。
3. 自測:v0300 自己的 `--selftest`(5 項)+ `--doctor` + 樣本 PDF 端到端(容器用倉內樣本)→ 桌機一行(取包 · 核 SHA · 跑 · 收據上傳)。
4. VCGC:交接案 `vrn2_nonstock` + 盤點站 + 需求(VRN-REQ 新號)· 編號 · 稽核 0 / 0 / 0。

**下一步要操作員做的:上傳完整包 `VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300.zip`(SHA-256 `8d7d2cef673fdb4c03b4f51cf09283fb2b6435d582ce852405b656237baa8ca1` · 含 internal/ 與 reuse/vrn2/ 三支)。**
