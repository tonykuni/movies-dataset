# 全整合稽核 · 2026-08-28

## 結論

新附件提出的輕量、中量、重量、Paddle、YAML Loader 與自動 fallback 已全部納入 GenericLayoutExtractionOS 2.1。引擎登錄總數仍為 32；31 個本機／可設定後端可依環境執行，Adobe Extract API 保留為預設停用的外部邊界。

## 附件逐項對照

| 附件要求 | 實際 adapter／元件 | 狀態 | 2.1 處理方式 |
|---|---|---|---|
| pdfplumber 主引擎 | `pdfplumber` | 已整合 | Auto 第一順位，文字／BBox／Font／Table／Layout |
| PyPDF | `pypdf` | 已整合並修正 | 使用真正的 `pypdf.PdfReader` layout extraction，不誤呼叫 pdfminer |
| Poppler pdftotext | `poppler_pdftotext` | 已整合 | `-layout -enc UTF-8` subprocess，含 timeout |
| PyMuPDF | `pymupdf` | 已整合 | Text／BBox／Font／Image／Layout |
| pdfminer.six | `pdfminer_six` | 已整合 | 字元字型與 top-origin BBox |
| Docling | `docling` | 已整合 | 重量級 Markdown／Table／Figure／RAG |
| Marker | `marker` | 已整合 | 可設定 CLI runner，公式／表格／圖形重建 |
| PaddleOCR | `paddleocr` | 已整合並升級 | PaddleOCR 2.x／3.x 雙 API，繁中／英文與 BBox |
| PaddleLayout | `paddle_layout` | 已整合並升級 | 3.x 官方 `LayoutDetection`；2.x／自訂模型用 runner |
| PaddleDetection | `paddle_detection` | 已整合 | 自訂 PaddleDetection runner，輸出統一 adapter contract |
| PaddlePDF | `paddle_pdf_pipeline` | 已整合並升級 | 3.x 官方 `PPStructureV3` PDF、Markdown、公式、讀序 |
| PP-Structure | `paddle_ppstructure` | 已整合並升級 | v2 `PPStructure`／v3 `PPStructureV3` 相容 |
| YAML 固定欄位 | `multi_engine_policy.example.yaml` | 新增 | 32 後端、priority、role、handles、fallback_if 完整配置 |
| 自動 fallback | `execute_route` | 已整合並優化 | 輕到重；掃描件在 pdfplumber 後直接重建 OCR lane |
| ABCD 簡化概念 | `auto` + YAML priority | 已吸收 | 不另複製一套脆弱 dispatcher；同一路由器可配置 A→B→C→D |

## 修復的附件示例風險

1. 原示例的 `run_pypdf()` 實際呼叫 pdfminer；2.1 已使用 `PdfReader`。
2. `Taskflow("layout")` 不是跨 Paddle 版本的穩定 Layout 契約；3.x 改用官方 `LayoutDetection`。
3. 只用「文字非空」判定成功會漏掉表格、Layout detection 與 OCRmyPDF artifacts；2.1 使用 Text／Structure／Artifact 三類 Gate。
4. 原示例在 image-only PDF 會逐引擎空跑；2.1 直接跳到 OCR lane，並保存 route decision。
5. 原示例沒有 timeout、記憶體保護、來源指紋、失敗狀態與可回復機制；2.1 均已補齊。

## 32 後端完整性

`multi_engine_policy.example.yaml` 包含 31 個啟用後端與 1 個停用的 Adobe 外部後端。`list` 與測試會檢查名稱唯一、資源等級／priority 順序；`probe` 只報告真實可用性，不把未安裝模型當作成功。

## 2.1 優化摘要

- `GLE-ADAPTER/2.1`、`GLE-ORCHESTRATOR/2.1`。
- YAML／JSON 雙設定格式，未知欄位 fail closed。
- SHA-256 快取鍵包含輸入、設定、adapter schema 與後端版本；只快取 PASS／WARN。
- Cache hit、原耗時、acceptance basis、route decisions 寫入 audit。
- BBox 同時保留原座標與 0–1 normalized 座標，跨 PDF point／OCR pixel 融合。
- Paddle 3.x 採官方 PP-StructureV3／LayoutDetection；模型預設不允許任意下載。
- 掃描文件不再產生大量 `SKIPPED_POLICY` 噪音。

## 官方 API 依據

- PaddleOCR PP-StructureV3: https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html
- PaddleOCR LayoutDetection: https://www.paddleocr.ai/main/en/version3.x/module_usage/layout_detection.html
- pypdf layout extraction: https://pypdf.readthedocs.io/en/latest/user/extract-text.html
