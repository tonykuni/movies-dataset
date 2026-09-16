# VIA／VRN／VDF／VAP B526 功能級整合驗收交接

**驗收時間：** 2026-09-16 17:11（Asia/Taipei）
**中央驗收器：** `CGC_MDL154_VIAFunctionalAcceptance_v0100.py`
**終極裁決：** `RED`（禁止安裝核可、禁止宣稱全鏈完成）
**驗收原則：** selftest 只證明程式結構；只有實際結果檔、資料庫內容、日期覆蓋、退出碼與證據檔同時核對後，才可判定通過。

## 一、終極結果

| 驗收站 | 實測結果 | 實測數值 | 裁決說明 |
|---|---:|---:|---|
| CGC149 中央治理主控台 | GREEN | 19/19，RC=0 | 元件冊 4928/4928、AST 0、未登錄 0 |
| CGC150 中央治理家族 | GREEN | 12/12，RC=0 | 家族成員、狀態、環境閘與只讀規則通過 |
| CGC153 Workflow Composer | GREEN | 12/12，RC=0 | 已加入 `via_functional_acceptance` 工作流節點 |
| VDF ENG087 市場清單結構驗收 | GREEN | 10/10，RC=0 | 去重、跨族群重複、中央調度與禁用接線通過 |
| VAP ENG006 v0101 | YELLOW | 9/9 結構檢查，RC=2 | VAP DB/UI 已找到；缺少 TA_RUN、TPLRUN 真實執行產物 |
| VRN active tree | GREEN | 288/288 compile、288/288 import | active tree 實測完整 |
| PDF 雙引擎 fixture | GREEN | fitz PASS、pdfplumber PASS、pages_agree=true、1 table | 目前只代表倉內 synthetic fixture |
| 股票 DuckDB | GREEN（結構）／RED（覆蓋） | 1979 股票、208848 價格列、重複鍵 0 | 最早日 2024-01-02，未達 2023-01-01 |
| 主動式 ETF DuckDB | GREEN | 22 universe、1122 holdings、重複鍵 0 | 實體表與欄位在位 |
| Windows 原始樣本 | BLOCKED | 64 份；可讀 0；解析 0 | `C:\測試樣本報告` 未掛載至目前沙盒 |

中央站 GREEN 為 **4/5，80.0%**。因此 CGC154 的整體裁決為 **RED**；這是資料覆蓋與輸入樣本的真實阻擋，不是程式結構失敗。

## 二、已完成的功能補強

本批新增 `CGC_MDL154_VIAFunctionalAcceptance_v0100.py` 作為唯一功能級驗收入口。它只調度既有中央與模組 selftest，並直接核對 VDF 結果 JSON、VRN/PDF 證據、兩本 DuckDB、804 active engine catalog 與 Windows 樣本狀態；每站保留 argv、退出碼、裁決燈、結構分數、尾端輸出與下一步。`PARTIAL`、`BLOCKED`、`YELLOW` 與非零退出碼不會被轉成 GREEN。

VAP 已升版為 `VAP_ENG006_AcceptanceAudit_v0101.py`。它不再把不存在的舊路徑當成唯一資料庫，也不再把「結構庫存在」當作「功能已實跑」；目前實測為 DB/UI 通過、TA/TPL run 產物缺失而明確回傳 RC=2。

VDF `VDF_ENG087_MarketListGovernance_v0101.py` 已加入 `start_required=2023-01-01` 的實際日期閘。它現在會將價格最早日 2024-01-02 判為 RED，避免中央市場清單在未補足 2023 資料時假綠。

CGC154 已接入以下中央正典：

| 正典／入口 | 接線 |
|---|---|
| PowerShell Register | `via-functional-acceptance`、`VIA功能驗收`、`功能級驗收` |
| InputConsole | `central → acceptance → via_functional_acceptance` |
| Workflow SSOT | `via_functional_acceptance`，profile=`test` |
| Interface Contract Registry | CGC154 與 VDF ENG087 v0101 已入冊 |
| Component Inventory | VCGC `registry-sync --apply` 後 4928/4928 |

## 三、資料庫實測摘要

股票資料庫：`functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb`。`tw_listings_industry` 有 1979 列，`tw_daily_prices` 有 208848 列，必要欄位齊全，`(date,ticker)` 重複鍵為 0；但價格日期範圍為 **2024-01-02 至 2026-09-15**，故未滿足中央要求的 2023-01-01 起始日。

主動式 ETF 資料庫：`functional modules/VDF/output_hub/active_tw_etf/active_tw_etf_holdings/ActiveTWETF.duckdb`。`active_tw_etf_universe` 有 22 列，`holdings_daily` 有 1122 列，`(portfolio_date,etf_ticker,holding_ticker)` 重複鍵為 0；目前最新持股日期為 2026-09-15。

## 四、VRN／PDF 實測邊界

VRN active tree 已驗證 288 個 Python 檔案全部 compile/import 通過。倉內 synthetic PDF 已由 fitz 與 pdfplumber 雙引擎核對通過，頁數一致、表格 1 張、表格非空格 12 格。這不等於使用者列出的 60 份 PDF 與 4 份 DOCX 已完成內容級驗收；該批原始檔目前只有 Windows 路徑，沙盒中不存在檔案本體。

使用者樣本狀態檔：`VIA_WINDOWS_SAMPLE_ACCEPTANCE_STATUS_B526.json`。64 份樣本分組為華南 11、凱基 9、兆豐 6、其他 38；目前 readable=0、parsed=0、accepted=0。補齊方式是上傳原始 PDF/DOCX，或提供沙盒可讀取資料夾，然後經 VIA 的 VRN intake → first-page → structured DB → dual-engine verification 重跑。

## 五、下一位接手者最短指令

```powershell
via-functional-acceptance
via-vcgc -SelfTest
via-market-lists status
```

若要補齊 2023 價格資料，先由操作員依網路同意閘執行 ENG054 的官方回補，再重跑：

```powershell
via-market-lists status
via-functional-acceptance
```

若要完成 VAP 實跑驗收，須先產生可追溯的 `TA_RUN_*.parquet/csv` 與 `VIA_Reports/vap_tpl_runs/TPLRUN_*/run.json`，再執行：

```powershell
via-vapaccept -SelfTest
via-functional-acceptance
```

若要完成使用者 PDF/DOCX 內容級驗收，先掛載或上傳原始檔，不能以 synthetic fixture 代替。

## 六、證據位置

- 機器狀態：`VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.json`
- 離線展示：`VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.html`
- VDF 清單狀態：`VIA_Reports/vdf/central_lists/MARKET_LISTS_latest.json`
- VRN/PDF 狀態：`VIA_Reports/handover/evidence_b526_vrn_import/vrn_pdf_validation_b526.json`
- Windows 樣本狀態：`VIA_Reports/handover/VIA_WINDOWS_SAMPLE_ACCEPTANCE_STATUS_B526.json`
- 中央註冊同步：`VIA_Reports/iface_runs/IFACE_20260916_090918.json` 與 VCGC registry-sync 輸出

**接手規則：** 在 `vdf_market_lists_result=GREEN`、`windows_original_samples=GREEN`、`VAP006_AcceptanceAudit=GREEN` 以前，CGC154 必須保持 RED 或 PARTIAL_BLOCKED；不得手動改寫裁決燈。
