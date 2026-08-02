# PMIS-Lite 系統清單：模組 × 引擎 × 函式工具 × 函式庫 × 最佳化狀態

_實際程式碼盤點 · 26 模組 / ~2,488 行 / 22 自我測試全通過 · 全本機處理_

**狀態圖例**：✅ 已測試＋已優化　🟢 已測試　🔵 已實作（環境相依，本機驗證）　🟡 可再強化（已標示方向）

---

## 一、擷取層（Adapters · 多來源，萬用介面）

| 模組 | 引擎/類別 | 主要功能 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `adapters/base` | `SourceAdapter` (Protocol) | 統一 adapter 介面（回傳統一 Record） | — | ✅ |
| `adapters/excel_csv` | `ExcelCsvAdapter` | 讀 Excel/CSV 多表、治亂碼、欄位語意對應、完整性計數 | pandas, openpyxl | ✅ |
| `adapters/msproject` | `MSProjectAdapter` | 讀 MS Project XML 匯出、任務/資源/指派、摘要任務略過 | xml(內建) | 🟢 |
| `adapters/plm` | `PLMExportAdapter` | 讀 PLM 匯出（CSV/Excel）+ 廠牌欄位對應 | pandas | 🟢 |
| `adapters/outlook_desktop` | `OutlookDesktopAdapter` | 讀已登入 Outlook（近 N 月）、附件落地、清理引用尾 | win32com | 🔵 |

🟡 **待強化**：msproject 接 mpxj 直讀 .mpp；outlook 接備援鏈（COM→libpff→IMAP）；新增 Gmail adapter。

---

## 二、文字處理引擎（治亂碼 / 修復 / 編號）

| 模組 | 引擎/函式 | 主要功能 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `encoding` | `detect_file_encoding`, `repair_mojibake` | BOM/chardet/回退偵測、mojibake 保守修復 | chardet | ✅ |
| `textrepair` | `clean_email_text` | 剝引用尾/簽名/免責，主體不刪，記錄刪除 | — | ✅ |
| `numbering` | `content_hash`, `make_uid` | WBS 式穩定身分編號（內容雜湊） | hashlib(內建) | ✅ |
| `schema` | `Record` | 統一 SSOT 資料格式（15 欄） | — | ✅ |

🟡 **待強化**：encoding 改用 charset-normalizer 為首選；textrepair 加多語簽名樣式；繁簡用 OpenCC 對齊。

---

## 三、附件擷取引擎（多型別 → 文字）

| 模組 | 引擎/函式 | 支援型別 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `attachments` | `extract_attachment`, `AttachmentResult` | pdf/docx/xlsx/pptx/txt/csv/md/json/rtf/html/eml/影像 | pdfplumber, docx, openpyxl, pptx, (pytesseract, pdf2image, PIL 選用) | 🟢 |

內含 OCR 救援路徑（掃描 PDF）：目前單引擎，🟡 待接三引擎接力（Tesseract→RapidOCR→PaddleOCR）。

---

## 四、分類與關鍵字引擎（提高歸類率核心）

| 模組 | 引擎/函式 | 主要功能 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `classify` | `classify_all`, `seed_buckets_from_data`, `classify_record` | 三道遞進：關鍵字→討論串傳播→模糊指派；桶自資料長出 | — | ✅ |
| `keywords` | `generate_keyword_candidates`, `apply_approved` | 從資料挖鑑別性關鍵字候選、核可後 append-only 寫回 | — | ✅ |
| `normalize/terms` | `TermStore`, `Candidate`, `mine_candidates` | 同義字/簡寫探勘（括號/共現/近似）、不自動合併 | difflib(內建) | 🟢 |

🟡 **待強化**：classify/keywords 接 CKIP 繁中斷詞取代 bigram，濾掉「成度/載效」碎片；terms 接 rapidfuzz 加速近似。

---

## 五、追蹤與分析引擎

| 模組 | 引擎/函式 | 主要功能 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `actions` | `extract_actions`, `ActionItem` | 追蹤事項抽取（觸發詞+負責人+期限） | — | 🟢 |
| `stakeholders` | `build_registry`, `Stakeholder` | 利害關係人登錄（僅工作事實、客觀參與度） | — | ✅ |
| `panorama` | `build_panorama`, `panorama_markdown` | 數月全景：每產品時間跨度、每週活動、停滯偵測 | — | ✅ |
| `completeness` | `CompletenessReport`, `SourceAudit`, `categorize` | 完整性 gate：結構略過/可救回/錯誤分類、涵蓋率 | — | ✅ |

🟡 **待強化**：actions 去重+「未回覆 N 天升旗」；stakeholders 人工標註參與度欄位。

---

## 六、儲存與產出引擎

| 模組 | 引擎/函式 | 主要功能 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `store` | `ParquetStore` | Parquet 增量、append-only、快照、變更偵測 | pandas, pyarrow | ✅ |
| `report_html` | `build_html` | 門外漢結果頁（完整性/歸類率/全景/候選） | pandas | 🔵 |
| `slides` | `build_deck` | 簡報草稿（分產品頁+風險頁，沿用範本） | pptx, pandas | 🔵 |

🟡 **待強化**：store 升級 DuckDB 查詢層；report_html 加歷史趨勢圖；slides 套使用者範本字體。

---

## 七、平台與韌性引擎（Plug & Play / 備援）

| 模組 | 引擎/函式 | 主要功能 | 函式庫 | 狀態 |
|------|----------|---------|--------|------|
| `autodetect` | `probe`, `build_sources`, `verify_detection`, `detection_markdown` | 環境/來源自動偵測、遞迴掃描、偵測查核 | win32com(選用) | ✅ |
| `resilience` | `run_chain`, `Strategy`, `ChainResult` | 備援鏈：多策略依序嘗試、記錄走到第幾條 | — | ✅ |
| `pipeline` | `run` | 主流程編排（0 偵測→1 擷取→…→7 產出） | pandas | 🟢 |

🟡 **待強化**：把 resilience 接進 msproject/outlook 實際多路徑 fallback。

---

## 八、入口與啟動

| 檔案 | 角色 | 狀態 |
|------|------|------|
| `run_demo.py` | 開發者一鍵跑（顯式 config） | 🟢 |
| `run_auto.py` | 門外漢一鍵跑（自動偵測+開結果頁+不崩潰） | 🔵 |
| `START_Windows.bat` | 雙擊啟動（自動裝套件、免管理員） | 🔵 |
| `config_builder.html` | 點選式設定產生器（手機可用、免打字） | 🔵 |
| `tests/test_stage1.py` | 22 項自我測試 | ✅ |

---

## 九、外部函式庫總清單（目前實際使用）

**已用（核心）**：pandas、openpyxl、pyarrow、chardet、python-pptx、python-docx、pdfplumber、pypdf
**選用（強化）**：pytesseract、pdf2image、Pillow（OCR）、pywin32（Outlook/MSProject COM）
**內建標準庫**：os, re, json, hashlib, datetime, difflib, xml, email, dataclasses, collections, html, webbrowser, platform, traceback

🟡 **規劃導入（見 FMEA 文件 15 選型）**：mpxj、libpff/libratom、extract-msg、RapidOCR/PaddleOCR、CKIP Transformers、jieba、rapidfuzz、charset-normalizer、DuckDB/Polars、OpenCC、google-api-python-client。

---

## 十、整體最佳化狀態總結

| 面向 | 狀態 |
|------|------|
| 測試覆蓋 | 22/22 通過，14 個核心模組有直接測試 ✅ |
| 完整性（不可遺漏） | gate 內建，未解釋遺漏=0 才 PASS，涵蓋率 94.7% ✅ |
| 歸類率 | 三道遞進 + 自動關鍵字生成，55.6%→83.3% 實證 ✅ |
| 韌性（降低失敗率） | 備援鏈機制已內建並測試；多路徑實接為下一步 🟢→🟡 |
| 門外漢可用性 | 一鍵 .bat + 自動偵測 + 結果頁 + 設定產生器 🔵 |
| 合規 | 全本機、自有權限、AUP 提醒、僅記工作事實 ✅ |
| 真實郵件/MSProject 接通 | 程式就緒，需於 Windows 實機驗證 🔵 |
