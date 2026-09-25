# GenericLayoutExtractionOS 2.1 測試報告

測試日期：2026-08-28  
Python：3.12.13  
Adapter Schema：`GLE-ADAPTER/2.1`  
Orchestrator Schema：`GLE-ORCHESTRATOR/2.1`  
Consensus Schema：`GLE-CONSENSUS/2.1`  
Core Layout Schema：`GLE-LAYOUT/1.0`

## 結論

程式編譯、18 項單元／故障注入測試、32 後端 list/probe、Auto、Consensus、附件型 YAML、All、掃描 OCR、Cache、Wheel build 與 isolated entrypoint 均通過。未安裝的套件或模型維持 `SKIPPED_UNAVAILABLE`，不列為實跑 PASS。

## 自動化測試

```text
18 tests
18 PASS
0 FAIL
0 ERROR
```

新增驗證包含：

- 附件型 `pdf_extraction_engine` YAML priority 載入。
- Text／Structure／Artifact 三類品質 Gate。
- SHA-256 快取命中與原耗時保存。
- Timeout 轉成 `TIMEOUT`，不終止整條路由。
- All Mode 在後端故障後繼續下一引擎。
- 重量級後端在低記憶體條件下 `SKIPPED_POLICY`。
- normalized BBox 與多來源 Consensus。
- 掃描文件直接重建 OCR lane，不產生中間假執行紀錄。

## Registry、設定與封裝

| Gate | 結果 |
|---|---|
| Adapter 登錄 | PASS：32 |
| Adapter 名稱唯一 | PASS：32／32 |
| 第一 Adapter | PASS：`pdfplumber` |
| Level／Priority 排序 | PASS |
| Probe 安全 | PASS：32／32 |
| 本環境可用後端 | 7／32 |
| 完整 YAML | PASS：31 enabled + 1 disabled cloud boundary |
| Python `py_compile` | PASS |
| `pip check` | PASS：No broken requirements found |
| Wheel build | PASS：`generic_layout_engine-2.1.0-py3-none-any.whl` |
| Wheel CLI entrypoint | PASS：`generic-layout-os list` 回傳 32 |

## 實際 CLI 回歸

| Mode | Route | Backend 狀態 | Canonical Elements | 本次耗時 |
|---|---|---|---:|---:|
| Auto | `pdfplumber` | PASS 1 | 83 | 127 ms |
| Consensus | `pdfplumber → pymupdf → pdfminer_six` | PASS 3 | 100 | 260 ms |
| Attachment YAML | `pdfplumber` 後達 Gate 停止 | PASS 1 | 83 | 116 ms |
| All | 32 個完整路由 | PASS 7、SKIPPED 25、FAIL 0 | 107 | 2106 ms |
| Scan Auto | `pdfplumber → tesseract` | SKIPPED_UNAVAILABLE 1、PASS 1 | 2 | 449 ms |

上述耗時只代表本次 Linux 容器的合成文件，不能當作跨機器 benchmark。

## Cache 回歸

- 第一次執行：`pdfplumber.cache_hit = false`。
- 相同檔案、設定、adapter schema 與後端版本第二次執行：`cache_hit = true`。
- 命中後 adapter 當次耗時為 0 ms；保留 `cache_source_duration_ms` 供稽核。
- Cache key 使用 SHA-256；輸入或設定改變會自然產生新 key。
- 只快取 `PASS`／`WARN`，不固化 `FAIL`、`TIMEOUT` 或不可用狀態。

## Paddle 整合靜態確認

| 路徑 | 2.1 實作 |
|---|---|
| PaddleOCR text | v2 `.ocr()`／v3 `.predict()` 雙分支 |
| PP-Structure | v2 `PPStructure`／v3 `PPStructureV3` |
| PaddleLayout | v3 官方 `LayoutDetection`；較舊或自訂模型使用 command runner |
| PaddlePDF | v3 官方 `PPStructureV3` PDF + Markdown |
| PaddleDetection | 自訂 runner，輸出統一 contract |

本環境未安裝 PaddlePaddle 與模型，因此上述項目只通過 API 分支、Probe、Compile 與契約測試，不標示為模型推理 PASS。

## OCR 語言降級

本環境 Tesseract 僅有 `eng`、`osd`。2.1 會偵測要求的 `chi_tra+chi_sim+eng`，清楚記錄缺少 `chi_tra`／`chi_sim`，並在仍有 `eng` 時安全降級。All Mode 中 Tesseract 與 OCRmyPDF 均實跑 PASS；不再因缺少部分語言包令整條驗收出現 FAIL。

## Core Layout Regression

合成 PDF 與掃描影像回歸均通過，涵蓋：

- `TEXT.H1/H2/H3/BODY`
- `TABLE.CAPTION/CONTENT/HEADER/STUB/DATA/SOURCE`
- `FIGURE.CAPTION/CONTENT/SOURCE`
- `META.PAGE_NUMBER/RUNNING_HEADER`
- `NOISE.END_DISCLAIMER`
- JSON、JSONL、UTF-8-SIG CSV、SQLite、HTML、Annotated PNG、唯一 ID、Source Fingerprint

## 未在本環境實跑的後端

- Docling、Marker、MinerU、DeepDoctection、LayoutParser、Table Transformer：套件／權重未安裝。
- Paddle 全系列：PaddlePaddle／模型未安裝。
- Java PDFBox／Tika、Node pdf.js／pdf-parse、.NET PdfSharp：缺對應 Runtime 或 runner。
- Windows PowerShell 7 AST／實機安裝：此 Linux 容器沒有 `pwsh`；安裝腳本仍保留 requirements hash state machine、備份、稽核與不關閉視窗規則。

上述未執行項目不標示為 PASS；`probe`、`backend_audit.csv` 與 `multi_engine_run.json` 會呈現真實狀態。
