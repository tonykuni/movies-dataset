# GenericLayoutExtractionOS 2.0 測試報告

測試日期：2026-08-28  
Python：3.12.13  
Adapter Schema：`GLE-ADAPTER/2.0`  
Orchestrator Schema：`GLE-ORCHESTRATOR/2.0`  
Core Layout Schema：`GLE-LAYOUT/1.0`

## 自動化測試

```text
test_config_rejects_invalid_ocr_mode                    ... ok
test_end_to_end                                         ... ok
test_image_ocr_lane                                     ... ok
test_auto_route_stops_after_pdfplumber_quality_gate     ... ok
test_every_probe_is_safe                                ... ok
test_fusion_records_multiple_sources                    ... ok
test_image_only_pdf_jumps_to_ocr_lane                   ... ok
test_registry_contains_all_unique_engines_in_resource_order ... ok
test_scanned_image_jumps_to_ocr_lane                    ... ok
test_three_engine_consensus_route                       ... ok

Ran 10 tests
OK
```

## Registry 與環境檢查

| Gate | 結果 |
|---|---|
| 32 個 Adapter 唯一註冊 | PASS |
| 第一 Adapter 為 pdfplumber | PASS |
| Level／Priority 單調排序 | PASS |
| 32 個 Probe 不拋例外 | PASS |
| Python Compileall | PASS |
| pip check | PASS：No broken requirements found |
| 本次環境可用後端 | 7／32 |
| 未安裝後端安全略過 | PASS |

## Auto Mode

| 項目 | 結果 |
|---|---|
| Route | `pdfplumber` |
| Route Count | 1 |
| Status | PASS 1 |
| Stop Reason | Quality Gate 與必要能力通過 |
| Consensus Elements | 83 |
| Core Layout | PASS |

證明 `pdfplumber` 確實在第一順位，達標後不會啟動更耗資源的引擎。

## Consensus Mode

| 項目 | 結果 |
|---|---|
| Route | `pdfplumber → pymupdf → pdfminer_six` |
| Status | PASS 3 |
| Consensus Elements | 100 |
| 多來源 Fingerprint | PASS |
| 相同元素信心加權 | PASS |

## All Mode

| 項目 | 結果 |
|---|---:|
| Route Count | 32 |
| 實際完成 | 7 |
| 安全略過 | 25 |
| FAIL | 0 |
| TIMEOUT | 0 |
| Consensus Elements | 107 |

大型模型未安裝時均回報 `SKIPPED_UNAVAILABLE`，沒有偽造成功結果。

## 掃描影像 OCR Lane

- 影像輸入先由 `pdfplumber` Probe 判定不可用。
- 中間 Structure／Markdown／Vision lane 標記 `SKIPPED_POLICY`。
- 路由直接跳至 Tesseract。
- Tesseract TSV 成功輸出 Text、BBox、Confidence、Reading Order。
- OCR 品質與必要能力通過後停止，不再啟動 Paddle／EasyOCR。

## Core Layout Regression

合成 PDF：2 頁、32 個核心 Layout Elements、Warning 0。

成功辨識：

- `TEXT.H1/H2/H3/BODY`
- `TABLE.CAPTION/CONTENT/HEADER/STUB/DATA/SOURCE`
- `FIGURE.CAPTION/CONTENT/SOURCE`
- `META.PAGE_NUMBER/RUNNING_HEADER`
- `NOISE.END_DISCLAIMER`

輸出驗證：JSON、JSONL、UTF-8-SIG CSV、SQLite、HTML、Annotated PNG、唯一 Element ID、Source Fingerprint 全部通過。

## 已修正問題

1. pdfplumber 無框線 Stream 偵測會把整頁多欄本文誤判為表格：已改為預設關閉。
2. 固定字級倍率會把 16 pt 與 22 pt 同判 H1：已改用文件字級群聚。
3. OCRmyPDF `--clean` 在沒有 unpaper 時失敗：已移除非必要依賴，保留 `--deskew`。
4. PaddleOCR 2.x／3.x API 不同：文字引擎採雙版本分支，PaddlePDF 明確要求 v3。
5. HURIDOCS、PaddleLayout、PaddleDetection API／模型差異：改用可驗證的 Command Adapter，不猜測本機 API。

## 尚未在本環境執行的項目

- Docling、Marker、MinerU、DeepDoctection、LayoutParser、Table Transformer 模型推理：套件／權重未安裝。
- Paddle 全系列：PaddlePaddle／模型未安裝。
- Java PDFBox/Tika、Node pdf.js/pdf-parse、.NET PdfSharp：需要使用者本機 Runtime 或 Runner。
- Windows PowerShell 安裝腳本：已完成靜態結構與 Hash-State-Machine 設計；此 Linux 測試容器沒有 PowerShell 7，需在 Windows 11 實機執行。

以上未執行項目不標示為 PASS；引擎在 Probe 與 Audit 中會呈現實際狀態。
