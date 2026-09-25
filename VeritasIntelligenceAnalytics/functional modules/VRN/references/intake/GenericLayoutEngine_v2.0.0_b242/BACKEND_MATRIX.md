# GenericLayoutExtractionOS 2.0 · Backend Matrix

## Resource Level 1

| Engine | Runtime | 實作方式 | Capabilities |
|---|---|---|---|
| pdfplumber | Python | Direct API | Text、BBox、Font、Table、Layout |
| PyPDF | Python | Direct API | Text、Metadata |
| Poppler pdftotext | C++ CLI | Subprocess | Text、Physical Layout |
| pdf-parse | Node.js | Node Adapter | Text、Metadata |

## Resource Level 2

| Engine | Runtime | 實作方式 | Capabilities |
|---|---|---|---|
| PyMuPDF | Python／MuPDF | Direct API | Text、BBox、Font、Image、Layout |
| pdfminer.six | Python | Direct API | Character、Font、BBox、Layout |
| Apache PDFBox | Java | JAR／Command Adapter | Text、Metadata |
| pdf.js | Node.js | Node Adapter | Text、Transform、BBox |
| MuPDF mutool | C/C++ CLI | Command Adapter | Text、Layout |
| PyMuPDF4LLM | Python | Direct API | Markdown、RAG、Layout |
| Camelot | Python | Direct API | Table、CSV、BBox |
| Tabula-Py | Python／Java | Direct API | Table、CSV |

## Resource Level 3

| Engine | Runtime | 實作方式 | Capabilities |
|---|---|---|---|
| Docling | Python／Model | Direct API | Markdown、Table、Figure、RAG |
| Unstructured | Python／Model | Direct API | Semantic Elements、RAG |
| Apache Tika | Java | JAR／Command Adapter | Text、Metadata、Multi-format |
| PdfSharp | .NET | Command Adapter | Text、Layout |

## Resource Level 4

| Engine | Runtime | 實作方式 | Capabilities |
|---|---|---|---|
| Marker | Python／Model | CLI Adapter | Markdown、Formula、Table、Figure |
| MinerU | Python／Model | CLI Adapter | Markdown、Formula、Table、Figure |
| LayoutParser | Python／Detectron2 | Direct API | Layout、BBox、Vision |
| DeepDoctection | Python／Model | Direct API | Layout、Table、OCR |
| HURIDOCS VGT | Python／Container | Configurable Runner | Layout、Reading Order |
| Table Transformer | Transformers／Torch | Direct API | Table Detection、BBox |

## Resource Level 5

| Engine | Runtime | 實作方式 | Capabilities |
|---|---|---|---|
| Tesseract | Native CLI | TSV Adapter | OCR、Text、BBox |
| PaddleOCR | PaddlePaddle | v2/v3 Direct API | OCR、CJK、BBox |
| Paddle PP-Structure | PaddlePaddle | Direct API | Layout、Table、Figure |
| PaddleLayout | PaddlePaddle | Versioned Command Adapter | Layout、BBox |
| PaddlePDF | PaddleOCR v3 | Direct PDF Pipeline | PDF、OCR、Layout |
| PaddleDetection | PaddlePaddle | Command Adapter | Object Detection、Layout |
| EasyOCR | Torch | Direct API | Multilingual OCR、BBox |
| OCRmyPDF | Python／CLI | Subprocess | Searchable PDF、Deskew |
| Transkribus Core | Local Runner | Command Adapter | Historical／Handwriting OCR |

## External Boundary

| Engine | 狀態 | 原因 |
|---|---|---|
| Adobe Extract API | Registered、Disabled | 需要外部雲端與憑證，不屬於本機免費執行邊界 |

## Backend Status Contract

| Status | 意義 |
|---|---|
| `PASS` | 已執行並完成 |
| `WARN` | 已執行但有非致命問題 |
| `FAIL` | 引擎執行失敗，路由器繼續下一引擎 |
| `TIMEOUT` | 超過該引擎的時間限制 |
| `SKIPPED_UNAVAILABLE` | 套件、執行檔、模型或 Runner 未安裝 |
| `SKIPPED_POLICY` | 因掃描跳轉、記憶體限制或本機政策略過 |

## 品質 Gate

```text
Character Count
Readable Character Ratio
Replacement Character Ratio
Duplicate Line Ratio
BBox Element Ratio
Required Capabilities
Available Memory For Heavy Backends
```

自動模式只有在品質和必要能力同時達標時才停止；`PASS` 不等於一定被採用。Consensus Fusion 會保留所有來源及 Fingerprint，不靜默覆寫。
