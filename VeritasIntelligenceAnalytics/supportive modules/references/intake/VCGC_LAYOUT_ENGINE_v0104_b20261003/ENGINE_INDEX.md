# Layout 功能定位索引

版本 v0104；單一入口 via-vcgc layout；46 能力／15 模組／564 定義／37 有效 API。

先讀本索引與 ENGINE_CATALOG.json 的所需模組，再用既有 via-panorama slice 讀單一函式。完整能力、註冊碼、行號、來源雜湊及驗證範圍皆由同一 SSOT 產生。

| 模組 | 職責 | 定義數 | 原始碼 |
| --- | --- | ---: | --- |
| hub | 唯一公開引擎與修復流程 | 15 | supportive modules/70_VRN_Rules/SUP_MDL743_GenericLayoutHub_v0104.py |
| base | 鎖定的成功擷取與原始證據 | 15 | supportive modules/70_VRN_Rules/SUP_MDL743_GenericLayoutHub_v0101.py |
| common | 共用參數、座標與原值 | 11 | supportive modules/70_VRN_Rules/layout_repair_v0100/SUP_MDL743_LayoutCommon_v0100.py |
| text | 內文結構與接句修復 | 5 | supportive modules/70_VRN_Rules/layout_repair_v0100/SUP_MDL743_LayoutText_v0100.py |
| tables | 表格分區、還原與核對 | 12 | supportive modules/70_VRN_Rules/layout_repair_v0100/SUP_MDL743_LayoutTables_v0101.py |
| figures | 圖區、子圖與條件式 OCR | 8 | supportive modules/70_VRN_Rules/layout_repair_v0100/SUP_MDL743_LayoutFigures_v0100.py |
| manager | 靜態清冊、函式索引與功能呈現 | 10 | supportive modules/registry/CGC_MDL069_SystemManager_v0114.py |
| gle_core | 鎖定的 Layout 核心 | 67 | functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/generic_layout_engine.py |
| gle_adapters | 鎖定的後端介面 | 32 | functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/adapter_sdk.py |
| gle_backends | 鎖定的後端實作 | 104 | functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/all_backend_engines.py |
| gle_router | 鎖定的後端調度 | 32 | functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/multi_engine_orchestrator.py |
| bridge | 鎖定的 GLE 掛載與相容介面 | 22 | supportive modules/70_VRN_Rules/SUP_MDL743_GenericLayoutHub_v0100.py |
| financial_reader | 鎖定的 FINANCIAL DATA 擷取 | 124 | functional modules/VRN/engine/VRN_Integrated_ReportDatabase_Engine.py |
| evidence_reader | 鎖定的座標證據支援 | 103 | functional modules/VRN/engine/VRN_Evidence_Core.py |
| bundle | 原始位元封裝與完整性核對 | 4 | supportive modules/70_VRN_Rules/layout_repair_v0100/SUP_MDL743_LayoutBundle_v0100.py |

| 功能碼 | 能力 | 實作 |
| --- | --- | --- |
| LAYOUT.SOURCE_LOCK | 成功擷取／原始值 SHA-256 鎖定 | base:def_locked_sources, hub:def_repair_document |
| LAYOUT.EXTRACT_REUSE | 沿用舊 GLE 與三後端擷取，不重造擷取器 | base:def_analyze |
| LAYOUT.FULL_PAGE | 首頁任意位置與全頁文字座標保留 | common:def_words, common:def_lines, base:def_native_svg |
| LAYOUT.FONT_EVIDENCE | 字級／字型粗體／描邊／疊印證據 | text:def_font_evidence, hub:def_traces |
| LAYOUT.SEVEN_LEVELS | 主標題、H1/H2/H3、本文、頁底、後方備註七階 | text:def_classify |
| LAYOUT.END_MATTER | 後方小字與其標題子樹隔離且留存 | text:def_classify |
| LAYOUT.RUNNING_MARGIN | 跨頁重複頁首、頁尾、頁碼指紋隔離 | text:def_classify |
| LAYOUT.BODY_TABLE_MASK | 表圖與本文分流，避免表格文字混入段落 | text:def_reading_order |
| LAYOUT.CONTEXT_FIVE | 表圖上下最多五行補抓及同欄防撞 | common:def_context |
| LAYOUT.SOURCE_BIND | 表號／圖號／說明／單位／資料來源綁定 | common:def_context, figures:def_figure_metadata |
| LAYOUT.TABLE_PROJECT | 無框線表格由原生文字座標重建欄列 | tables:def_project_rows, tables:def_recover_tables, tables:def_table_rows |
| LAYOUT.MISSING_ROWS | 表頭以外對齊資料列與合計列補回 | tables:def_recover_tables |
| LAYOUT.TABLE_SPANS | 幾何證明的跨格／多層表頭；無來源空軸清理與HTML表格 | tables:def_spans_and_fragments, hub:def_html_table |
| LAYOUT.CELL_WRAP | 同一来源儲存格斷行縫合，歧義不強併 | tables:def_spans_and_fragments |
| LAYOUT.NUMERIC_GUARD | 零／空白／負括號／百分比與原值分開保留 | common:def_number, tables:def_cell |
| LAYOUT.CHECKSUM | 合計驗算與不一致標記，禁止用吻合冒充完整 | tables:def_checksum |
| LAYOUT.MULTITABLE_SPLIT | 左右獨立財報先分欄、各欄上下分表，避免再黏回 | tables:def_split_tables, tables:def_statement_regions, hub:def_tables_html |
| LAYOUT.SIDE_RELATION | 並排獨立表／折疊表／帳戶表／寬表四態判別 | tables:def_table_relation |
| LAYOUT.VERTICAL_UNROLL | 有表頭、表號、序列證據才縱向展開 | tables:def_adjacent |
| LAYOUT.ACCOUNT_BIND | 資產與負債權益雙區共同綁定 | tables:def_adjacent |
| LAYOUT.WIDE_REJOIN | 主鍵與列座標守門，誤切寬表橫向接回 | tables:def_adjacent |
| LAYOUT.CROSS_PAGE_TABLE | 相鄰頁、欄位、表號及正文障礙共同檢查續表 | tables:def_continue_tables |
| LAYOUT.REPEATED_HEADER | 續表重複表頭去重，保留原始頁面與來源 | tables:def_continue_tables |
| LAYOUT.TABLE_DEDUP | 同座標同來源候選去重，異處同值不得消失 | tables:def_deduplicate |
| LAYOUT.HEADING_FSM | 標題前綴／留白／字級／間距守門與斷句FSM | text:def_can_join, text:def_stitch |
| LAYOUT.WRAPPED_HEADING | 長標題同階緊鄰折行合併 | text:def_stitch |
| LAYOUT.CROSS_PAGE_TEXT | 跨頁接句剝離頁首頁尾且禁止吞入新標題 | text:def_can_join, text:def_stitch |
| LAYOUT.HEADING_TREE | 主文標題樹與段落路徑 | text:def_stitch |
| LAYOUT.MIXED_COLUMNS | 單雙欄閱讀順序、浮動圖表、章節分界 | text:def_reading_order |
| LAYOUT.COMPOUND_FIGURE | 左右與上下複合子圖空白走廊切分 | figures:def_split_canvas, figures:def_compact_assets |
| LAYOUT.DUAL_AXIS_GUARD | 連續X軸／繪圖內容阻止錯切雙Y軸圖 | figures:def_split_canvas |
| LAYOUT.SHARED_LEGEND | 共用圖例獨立擷取並綁回子圖 | figures:def_split_canvas, figures:def_figures |
| LAYOUT.FIGURE_PARENT | 共用母圖號、獨立子圖號與來源歸屬 | figures:def_figure_metadata |
| LAYOUT.FIGURE_OCR | 裁切放大後逐子圖OCR；原生文字優先 | figures:def_figures, figures:def_ocr_status |
| LAYOUT.OCR_ROLES | 圖內標題、左右Y軸、X軸、圖例、數據標籤 | figures:def_ocr_roles |
| LAYOUT.LABEL_PAIR | 位置相近標籤配對候選，未知數列不造值 | figures:def_ocr_roles |
| LAYOUT.DUAL_EVIDENCE | 原頁／圖區影像加原生文字與上下文共同留證 | figures:def_figures, hub:def_export |
| LAYOUT.RAW_REPAIRED | 原始與修復值、source IDs、理由與頁碼沿革 | hub:def_repair_document |
| LAYOUT.CACHE_RESUME | 內容及程式雜湊快取、逐檔原子斷點 | hub:def_run_batch |
| LAYOUT.FILENAME_ORDER | 依輸入檔名向下排列、檔內按實體頁排序 | hub:def_run_batch |
| LAYOUT.EXPORT | HTML、JSON、CSV與內嵌HTML表格Markdown | hub:def_export |
| LAYOUT.FINANCIAL_REUSE | 舊年度財報矩陣與新版修復同時保留 | base:def_analyze, hub:def_export, financial_reader:extract_document_tables, evidence_reader:pdf_column_tables |
| LAYOUT.ENGINE_HEADER | 引擎頂部機器可讀功能描述與唯一SSOT | hub:def_manifest, manager:def_engine_catalog, manager:def_ast_index, manager:def_effective_api |
| LAYOUT.MANAGER_UI | System Manager 與使用者同一完整功能卡 | manager:def_catalog_html, hub:def_catalog_html |
| LAYOUT.REGISTRY | 每項功能與實作def可追溯、缺件紅燈 | manager:def_engine_catalog, bundle:def_verify, bundle:def_copy_runtime, bundle:def_create_zip |
| LAYOUT.OPTIONAL_BACKENDS | 既有模型介面沿用、缺依賴誠實列示、不自動下載 | gle_core:probe_backends, figures:def_ocr_status |
