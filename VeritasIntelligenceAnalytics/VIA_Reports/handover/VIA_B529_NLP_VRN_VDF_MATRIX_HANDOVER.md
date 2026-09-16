# VIA／VRN／VDF B529：NLP 文字修復、證據型摘要與三頁矩陣交接

**驗收批次：** B529
**驗收時間：** 2026-09-16 18:50（Asia/Taipei）
**中央引擎：** `VRN_ENG087_NLPTextSummaryBridge_v0100.py`
**實測 Run：** `B529-20260916T105325-68faf473`

## 一、交付結論

B529 已把 SUP_MDL744 NLP 應用系統統轄橋接入 VRN，並由單一中央入口依序執行 ENG072 首頁擷取、NLP 文字正規化與證據型摘要、ENG073 結構化入庫，以及 VDF ENG087 三清單唯讀狀態檢查。流程會保存 `normalized_text`、source SHA-256、摘要 `source_span`、摘要狀態與每次 pipeline run，不覆寫 ENG073 的 canonical 欄位。

本次以倉內可讀的 PDF/DOCX 夾具實測 **2 件**：ENG072 `2/2`、NLP `2/2`、摘要 `2/2`、ENG073 `rc=0`、DuckDB 表驗證通過。資料庫已具備 `vrn_nlp_text_summary` 與 `vrn_pipeline_runs`；VDF 維持誠實的 `RED`，所以總裁決為 `YELLOW`，不是 NLP 或 VRN 失敗。

## 二、三頁報告與 AI 可讀輸出

每次 `run` 會在 `VIA_Reports/vrn/nlp_pipeline/` 產生最新檔案，並在該次 `B529-*` 目錄保存不可覆寫的實測證據：

| 產物 | 用途 |
|---|---|
| `NLP_VRN_VDF_latest.html` | 自動開啟的完整三頁矩陣：第 1 頁總覽、第 2 頁完整測試矩陣、第 3 頁逐件依序結果 |
| `NLP_VRN_VDF_latest.json` | AI／程式機器裁決正本，含 `vdf_gate.blockers`、引擎 rc、資料庫計數與摘要證據 |
| `NLP_VRN_VDF_latest.md` | 可低額度接手的 Markdown 報告 |
| `B529-*/NLP_VRN_VDF_MATRIX.html` | 該次實測的不可變三頁 HTML |
| `B529-*/NLP_VRN_VDF_RESULT.json` | 該次實測 JSON |
| `B529-*/NLP_VRN_VDF_RESULT.md` | 該次實測 Markdown |

本次最後實測產物：`VIA_Reports/vrn/nlp_pipeline/B529-20260916T105325-68faf473/`。

## 三、實測結果

| 階段 | 實測結果 | 判定 |
|---|---:|---|
| 輸入 PDF/DOCX | 2 件；sidecar 2 件；缺件 0 | PASS |
| VRN ENG072 | `returncode=0`；PDF 雙法擷取 1 件、DOCX ZIP fallback 1 件 | PASS |
| SUP_MDL744 NLP | 尾版 `VIA_NLP_Application_System_v1.8.0`；研報服務 `6/6`；Hub `VERIFIED` | PASS |
| NLP 文字與摘要 | processed `2`；summary `2`；evidence span `True` | PASS |
| VRN ENG073 | `returncode=0`；基本資料入庫 2 件 | PASS |
| `vrn_reports.duckdb` | `vrn_nlp_text_summary=2`、`vrn_pipeline_runs=4`；資料庫可讀 | PASS |
| VDF ENG087 | 股票全集 `RED`；主動 ETF `GREEN`；熱門族群 `GREEN` | BLOCKED |
| 總裁決 | `YELLOW` | 誠實裁決 |

VDF 唯一阻擋原因是：股票價格資料最早日為 `2024-01-02`，晚於規格要求的 `2023-01-01`，需要補齊 2023 起資料。這個缺口不應被 NLP/VRN 報告生成掩蓋。

## 四、中央接線

已納入 VIA InputConsole：`vrn_nlp_vrn_vdf_pipeline`；已納入 Workflow SSOT：`vrn_nlp_vdf_pipeline`。介面同步結果顯示新節點 `OK`；既有 6 個歷史參數漂移仍由 MDL054 報告，未被本批假裝清除。VCGC registry-sync 已完成：活元件 `4983`、本次新元件 `5`、變更 `23`、退役 `0`、AST 錯誤 `0`。Workflow selftest `12/12`；VCGC selftest `19/19`。

## 五、Windows PowerShell 操作入口

進入 VIA 母系統並載入命令冊後，可用以下單一命令；執行完成會自動開啟三頁 HTML：

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. .\Register-VIA-Commands-v0208.ps1
NLP串接 -In 'C:\測試樣本報告' -Force
```

亦可執行完整腳本：

```powershell
& '.\VIA_Reports\handover\VIA_NLP_VRN_VDF_B529.ps1'
```

輸入資料夾不存在時腳本會停止，不會假造結果；VDF 非 GREEN 時仍會開啟報告，但回傳非零碼並在 HTML/JSON/Markdown 顯示阻擋原因。

## 六、下一位 AI 最省額度接手順序

先讀 `VIA_Reports/vrn/nlp_pipeline/NLP_VRN_VDF_latest.json`；只在需要版面時讀 `NLP_VRN_VDF_latest.html`；需要人類閱讀時讀 `NLP_VRN_VDF_latest.md`。若 `verdict=YELLOW`，只需讀 `vdf_gate.blockers`，本批已知唯一阻擋是 2023 價格覆蓋，不必重新掃完整程式樹。若要重跑 Windows 樣本，使用上方三行 PowerShell；若要只查狀態，使用 `NLP串接 -Status`。
