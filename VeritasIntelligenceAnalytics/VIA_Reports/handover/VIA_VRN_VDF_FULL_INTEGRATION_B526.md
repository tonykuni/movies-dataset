# VIA／VRN／VDF B526 完整串接驗收報告

**驗收時間：** 2026-09-16T08:30:49.269952+00:00  
**整體判定：** **PARTIAL_BLOCKED**

## 一、判定摘要

VIA 中央清單、VDF 實體 DuckDB、VRN active tree、VRN/PDF regression 與 ENG073 結構化資料庫自測均已串接驗證。整體仍標示 **PARTIAL_BLOCKED**，唯一主要阻擋是使用者列出的 64 份原始 Windows PDF/DOCX 在本沙盒不可讀；因此不能宣稱原始報告內容級驗收完成。

| Gate | 結果 |
|---|---|
| VRN active compile | 288/288 |
| VRN active import | 288/288 |
| VRN state | GREEN |
| PDF dual-engine fixture | GREEN |
| VIA/VDF central market lists | GREEN |
| ENG073 structured DB | 36/36; FAIL=0; RC=0 |
| Original Windows samples | 0/64 readable |

## 二、VDF 資料庫實測

股票資料庫實體檢查結果如下：

| 項目 | 結果 |
|---|---|
| `tw_listings_industry` rows | 1979 |
| `tw_daily_prices` rows | 208848 |
| price range | ['2024-01-02', '2026-09-15', 655, 319] |
| required-field nulls | 0; price=0 |
| duplicate keys | listing=0; price=0 |

主動式 ETF 資料庫實體檢查結果如下：

| 項目 | 結果 |
|---|---|
| registry rows | 30 |
| daily-required count | 22 |
| holdings rows | 1122 |
| holdings range | ['2026-09-15', '2026-09-15', 1, 22, 241] |
| holdings nulls | 0 |
| holdings duplicate keys | 0 |
| fetch failures | 0 |

## 三、VRN 與資料庫串接

VRN active tree 已達 288/288 compile 與 288/288 import。VRN/PDF 驗收使用 fitz 與 pdfplumber 互核 synthetic fixture，兩者均解析 2 頁；pdfplumber 取得 1 張表與 12 個非空儲存格。ENG073 retained zero-network evidence 顯示 36/36 checks OK、FAIL 0、RC=0，包含首頁欄位、金融資料、NLP 掛載、代號／券商／評等正典化、冪等入庫與 first-page contract。

## 四、Windows 原始樣本阻擋

目前 manifest 共 64 份：60 PDF、4 DOCX；華南 11、凱基 9、兆豐 6、其他 38。可讀取檔案為 0/64，因此下列內容尚未驗收：首頁擷取、代號／公司／券商／評等／目標價、報告型別、逐檔 structured DB row、原始檔雙引擎互核。

## 五、證據檔案

機器可讀報告：`/home/ubuntu/work/full_integration_b526/VIA_VRN_VDF_FULL_INTEGRATION_B526.json`  
既有 VRN/PDF 證據：`/home/ubuntu/work/vrn_pdf_validation_b524.json`  
既有 ENG073 36/36 證據：`/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/evidence_b524/vrn073.txt`  
Windows 樣本狀態：`/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/VIA_WINDOWS_SAMPLE_ACCEPTANCE_STATUS_B526.json`

## 接手結論

軟體結構 gate 與現有 VIA/VDF 資料庫 gate 已驗證；下一步不是重跑 288 個 import，而是掛載原始 PDF/DOCX，執行 VRN intake → first-page → ENG073 structured DB → fitz/pdfplumber cross-check，完成 64 份內容級驗收。
