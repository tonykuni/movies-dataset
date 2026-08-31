# GenericLayoutExtractionOS 2.1

泛用、本機優先、由輕到重的 PDF／影像擷取與 Layout Analysis 系統。不包含券商、財務、摘要或其他領域語義。

## 核心規則

```text
Level 1  pdfplumber → PyPDF → Poppler → pdf-parse
Level 2  PyMuPDF → pdfminer → PDFBox → pdf.js → MuPDF → 表格引擎
Level 3  Docling → Unstructured → Tika → PdfSharp
Level 4  Marker → MinerU → LayoutParser → DeepDoctection → HURIDOCS → TATR
Level 5  Tesseract → PaddleOCR／PP-Structure／Layout／PDF／Detection → EasyOCR → OCRmyPDF
```

- `pdfplumber` 永遠是 PDF 自動模式的第一引擎。
- 前一引擎通過文字品質、BBox、重複率及必要能力 Gate 後停止。
- 無文字層或影像輸入直接跳到 OCR lane，不浪費資源執行 Markdown／深度 Layout 模型。
- 大型模型啟動前檢查可用記憶體。
- 未安裝或未設定的引擎輸出 `SKIPPED_UNAVAILABLE`，不會假裝執行成功。
- 所有引擎輸出統一 `GLE-ADAPTER/2.1` 契約，再由 Consensus Fusion 仲裁。
- 文字、版面／表格與輸出檔採不同品質 Gate，避免「有框無字」被誤判失敗。
- 同一輸入、後端版本與設定使用 SHA-256 快取；設定或檔案改變時自動失效。

## 快速執行

自動、省資源模式：

```powershell
python multi_engine_orchestrator.py run "C:\path\report.pdf" `
  --output "C:\path\layout_output" `
  --mode auto
```

使用附件同款的固定欄位 YAML（完整 32 後端）：

```powershell
python multi_engine_orchestrator.py run "C:\path\report.pdf" `
  --output "C:\path\layout_output" `
  --config ".\multi_engine_policy.example.yaml"
```

需要強制重跑時加入 `--no-cache`。

三引擎結構共識：

```powershell
python multi_engine_orchestrator.py run "C:\path\report.pdf" `
  --output "C:\path\consensus_output" `
  --mode consensus
```

Paddle 全系列：

```powershell
python multi_engine_orchestrator.py run "C:\path\report.pdf" `
  --output "C:\path\paddle_output" `
  --mode paddle
```

指定引擎：

```powershell
python multi_engine_orchestrator.py run "C:\path\report.pdf" `
  --output "C:\path\selected_output" `
  --adapter pdfplumber `
  --adapter pymupdf `
  --adapter docling
```

列出及檢查全部引擎：

```powershell
python multi_engine_orchestrator.py list
python multi_engine_orchestrator.py probe
```

## 執行模式

| Mode | 用途 |
|---|---|
| `auto` | pdfplumber 第一；品質達標停止，失敗逐層升級 |
| `consensus` | pdfplumber＋PyMuPDF＋pdfminer 三引擎融合 |
| `tables` | pdfplumber＋Camelot＋Tabula＋TATR＋PP-Structure |
| `paddle` | pdfplumber＋PyMuPDF＋Paddle 全系列 |
| `ocr` | Tesseract 起始的完整 OCR fallback |
| `all` | 依資源順序嘗試所有可用引擎，用於驗收而非常態批次 |

## 32 個後端引擎

| Level | Engines |
|---:|---|
| 1 | pdfplumber、PyPDF、Poppler pdftotext、Node pdf-parse |
| 2 | PyMuPDF、pdfminer.six、Apache PDFBox、pdf.js、MuPDF CLI、PyMuPDF4LLM、Camelot、Tabula-Py |
| 3 | Docling、Unstructured、Apache Tika、PdfSharp |
| 4 | Marker、MinerU、LayoutParser、DeepDoctection、HURIDOCS VGT、Table Transformer |
| 5 | Tesseract、PaddleOCR、Paddle PP-Structure、PaddleLayout、PaddlePDF、PaddleDetection、EasyOCR、OCRmyPDF、Transkribus Core |
| External | Adobe Extract API 僅登錄；本機模式刻意禁止執行 |

## Paddle 系列分工

- `paddleocr`：繁中／簡中／英文文字及 BBox
- `paddle_ppstructure`：標題、本文、表格、圖形結構
- `paddle_layout`：依本機 Paddle 版本設定 Layout runner
- `paddle_pdf_pipeline`：PaddleOCR v3 PDF Document Pipeline
- `paddle_detection`：自訂 PaddleDetection 版面／物件模型

由於 PaddleOCR 2.x、3.x API 差異大，`PaddleOCR` 文字引擎內建雙版本相容；PaddleOCR 3.x 的版面與全文路徑直接使用官方 `LayoutDetection`、`PPStructureV3`，2.x 或自訂權重則保留 Command Adapter。`PADDLE_LAYOUT_MODEL` 預設採較省資源的 `PP-DocLayout-S`。

## 輸出

- `multi_engine_run.json`：路由、停止原因、品質、錯誤及稽核
- `backend_audit.csv`：每個後端的狀態、耗時與品質
- `consensus_layout.json`
- `consensus_elements.jsonl`
- `core_layout/layout_document.json`
- `core_layout/layout_elements.csv/jsonl/sqlite`
- `core_layout/layout_report.html`
- 原頁與 Annotated Layout PNG
- 具備 pyarrow 時輸出 Parquet

每個 Consensus Element 保存所有 `source_adapters` 與 `source_fingerprints`，不會靜默覆寫衝突來源。
另輸出 `bbox_normalized`（0–1），讓 PDF point 與 OCR pixel 座標可安全對照。

## 安裝

核心環境：

```powershell
.\Install-GenericLayoutEngine-All.ps1 -Profile Core
```

全部 Python 適配器：

```powershell
.\Install-GenericLayoutEngine-All.ps1 -Profile All
```

安裝腳本採 Requirements Hash State Machine；相同版本會跳過，變更時備份前一份狀態並建立安裝稽核。PowerShell 視窗不會被關閉。

Java、Node.js、.NET、Poppler、MuPDF、Tesseract、OCRmyPDF、PDFBox、Tika、PdfSharp Helper 與模型權重屬系統層依賴，請用 `probe` 查看實際狀態。

## 可設定外部 Runner

下列環境變數接受含 `{input}`、`{output}` 的 Command Template：

```text
GLE_PDFBOX_COMMAND
GLE_PDFJS_COMMAND
GLE_PDFSHARP_COMMAND
GLE_TIKA_COMMAND
GLE_MARKER_COMMAND
GLE_MINERU_COMMAND
GLE_HURIDOCS_COMMAND
GLE_PADDLE_LAYOUT_COMMAND
GLE_PADDLE_DETECTION_COMMAND
GLE_TRANSKRIBUS_COMMAND
```

另支援：`PDFBOX_JAR`、`TIKA_JAR`、`LAYOUTPARSER_MODEL_URI`、`TATR_MODEL`、`PADDLE_OCR_LANG`、`EASYOCR_LANGUAGES`。

## 原始 Layout Engine

若只需單一核心 Layout，不需要多引擎路由：

```powershell
python generic_layout_engine.py analyze "C:\path\report.pdf" `
  --output "C:\path\layout_output" `
  --ocr auto
```

## 測試

```powershell
python -m unittest discover -s tests -v
```

測試涵蓋原生 PDF、掃描影像 OCR、H1/H2/H3、表格、圖形、唯一 ID、32 個後端唯一註冊、所有 Probe 安全性、pdfplumber 第一順位、三引擎融合、OCR 直接跳轉、YAML Stack、快取、能力感知 Gate、Timeout、後端失敗續跑及記憶體 Gate。

完整逐項對照見 `INTEGRATION_AUDIT.md`，驗證結果見 `TEST_REPORT.md`。
