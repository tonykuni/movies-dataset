# VIA／VRN B528：報告資料庫建立與中央驗收交接

**驗收時間：** 2026-09-16T10:31:14.546530+00:00
**批次目的：** 建立 `vrn_reports.duckdb`，以 ENG072 → ENG073 實際串接匯入可讀取樣本，並以指定資料庫 status、只讀 SQL 與 ENG073 自測完成驗證。

## 終極裁決

B527 原本唯一的資料缺口是 `functional modules/VRN/db/vrn_reports.duckdb` 不存在。本批已建立實體 DuckDB，並由 ENG073 v0126 寫入兩筆 `vrn_report_basic`。因此 **VRN 報告資料庫 gate 已提升為 GREEN**。B527 機器狀態檔已同步更新，資料狀態由 YELLOW 改為 GREEN。

這個 GREEN 的範圍是「資料庫存在、入口可讀、結構正確、匯入可重跑且自測通過」。它不是對使用者 Windows 64 份原始報告的內容品質背書，因為那些 `C:\測試樣本報告\...` 路徑在本次 Linux 沙盒仍未掛載。

## 實際輸入與結果

本批使用兩個倉內可讀取的收容樣本，沒有建立空資料庫，也沒有手工插入假資料。

| 輸入 | ENG072 結果 | ENG073 結果 |
| --- | --- | --- |
| `synthetic_financial_report.pdf` | `DUAL_ZONES`，1,133 字，sidecar 成功 | 1 筆 `vrn_report_basic` |
| `Veritas_VOFIE_Reconstructed.docx` | `DOCX_ZIP_FALLBACK`，991 字，sidecar 成功 | 1 筆 `vrn_report_basic` |

ENG072 實際輸出 **2/2 sidecars**，返回碼為 0。ENG073 實際處理 **2/2 檔案**，返回碼為 0。兩筆樣本均為通用測試／重構文件，無法合理推導台股代號、券商、評等或財務指標，因此資料庫中的 `ticker`、`broker` 與 `metrics` 保持空值；這是誠實解析，不是缺陷掩蓋。

## 資料庫結構與只讀核驗

資料庫位置為 `functional modules/VRN/db/vrn_reports.duckdb`。只讀 SQL 核驗確認三張表存在：`vrn_report_basic`、`vrn_report_metrics` 與 `vrn_report_analyst`。

| 表 | 實際列數 | 判定 |
| --- | ---: | --- |
| `vrn_report_basic` | 2 | PASS |
| `vrn_report_metrics` | 0 | PASS；樣本無可誠實結構化的財務指標 |
| `vrn_report_analyst` | 0 | PASS；樣本無分析師欄位 |

ENG073 v0127 新增了 `--status --db <path>` 指定庫狀態入口。指定本批資料庫後，實測輸出為 `vrn_report_basic 2 列`、`vrn_report_metrics 0 列`，返回碼為 0。ENG073 的 36 項零網路自測為 **36/36 PASS**，並以 `py_compile` 驗證新尾版語法。

## 中央治理同步

透過 VCGC `registry-sync --apply` 完成中央收錄。實測結果為 **4,953 active 元件、0 新增、42 變更、0 退役、0 AST 錯誤**。42 項變更是中央掃描在本批尾版與既有狀態間的實際同步結果；沒有任何元件被退役。

B527 的中央驗收數據維持如下：CGC155 **9/9 PASS**、VCGC **19/19 PASS**、Central Governance Family **12/12 PASS**、Workflow Composer **12/12 PASS**。本批新增的 ENG073 資料庫自測為 **36/36 PASS**。

## 可重跑命令

```bash
PY=/home/ubuntu/work/quantguard_venv/bin/python
ROOT=/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics
DB="$ROOT/functional modules/VRN/db/vrn_reports.duckdb"

"$PY" "$ROOT/functional modules/VRN/VRN_ENG072_FirstPageText_v0129.py" run \
  --in "$ROOT/functional modules/VRN/references/intake/PDFRegressionEvidence_v1.0.0_b245/PDFRegressionEvidence_v1.0.0/synthetic_financial_report.pdf" \
  --in "$ROOT/functional modules/VRN/references/intake/Veritas_OmniFormat_Intelligence_Engine_v0140_FINAL_b245/Veritas_OmniFormat_Intelligence_Engine_v0140/examples/output/VOFIE_v0140_SYSTEM_Final/Veritas_VOFIE_Reconstructed.docx"
"$PY" "$ROOT/functional modules/VRN/VRN_ENG073_ReportStructuredDB_v0127.py" run \
  --dir "$ROOT/VIA_Reports/first_page_text" --db "$DB"
"$PY" "$ROOT/functional modules/VRN/VRN_ENG073_ReportStructuredDB_v0127.py" --status --db "$DB"
"$PY" "$ROOT/functional modules/VRN/VRN_ENG073_ReportStructuredDB_v0127.py" --selftest
"$PY" "$ROOT/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0111.py" registry-sync --apply
```

## 視覺化產物

PASS 數據與中央元件冊圖表位於 `VIA_Reports/handover/b528_visuals/B528_PASS_AND_COMPONENTS.png`。離線 HTML 儀表板位於 `VIA_Reports/handover/b528_visuals/B528_ACCEPTANCE_DASHBOARD.html`，機器可讀圖表來源位於 `B528_VISUALIZATION_DATA.json`。

## 尚未完成的內容級驗收

使用者原始清單共 64 份，包含 60 份 PDF 與 4 份 DOCX。其 Windows 路徑尚未掛載到目前執行環境，因此本批沒有假稱已解析這 64 份。要完成華南投顧、凱基投顧與其他券商的內容級驗收，下一步只需把原始檔案掛載到可讀取位置，然後以 ENG072 的 `--in` 重跑；ENG073 與中央資料庫入口已就緒。

## References

[1]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/functional%20modules/VRN/VRN_ENG072_FirstPageText_v0129.py "VRN ENG072 首頁文字擷取引擎"

[2]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/functional%20modules/VRN/VRN_ENG073_ReportStructuredDB_v0127.py "VRN ENG073 報告結構化資料庫引擎"

[3]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/functional%20modules/VRN/db/vrn_reports.duckdb "VRN 報告結構化 DuckDB"

[4]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/b528_visuals/B528_ACCEPTANCE_DASHBOARD.html "B528 驗收離線 HTML 儀表板"
