# VeritasAutoPlot v025 完整系統套件

VAP v025 不是只有 HTML。這個資料夾包含 Workbench、JavaScript 功能引擎、Plotly Renderer 契約、本機 Python Runtime、VDF 來源 Gate、TA‑Lib 技術指標入口、資料 Adapter、圖片檔案儲存、PowerShell 啟動器、SSOT 規格與自動測試。

## 最快啟動

Windows PowerShell 進入本資料夾後執行：

```powershell
.\Invoke-VAP-v025.ps1 -InstallDependencies -RunTests
```

若要在已安裝 Chrome／Edge 的 Windows 上執行真正的 136＋72 瀏覽器 Gate，第一次加上：

```powershell
.\Invoke-VAP-v025.ps1 -InstallBrowserTests -RunTests -NoBrowser
```

`-InstallBrowserTests` 只安裝 Playwright 測試套件，沿用本機 Chrome／Edge，不下載另一份瀏覽器。未安裝瀏覽器執行檔時，Gate 明確記為 `NOT_EXECUTED`。

之後日常啟動只需：

```powershell
.\Invoke-VAP-v025.ps1
```

也可雙擊 `Start-VAP-v025.cmd`。啟動器會依序執行 Runtime 自檢、VDF 驗證、增量 `SYNC CONNECT`，再開啟 `http://127.0.0.1:8765/`。PowerShell 視窗會保持執行；按 `Ctrl+C` 停止。

## 資料入口規則

- 所有正式來源必須先存在於 `config/vdf_connection_manifest.json`，狀態為 `AUTHORIZED`、`readOnly=true`，且 SHA‑256 Fingerprint 正確。
- VAP Runtime 只綁定 `127.0.0.1`，資料路徑必須位於 `allowedRoots`，JSON Endpoint 主機必須位於 `allowedHosts`。
- 股票、ETF、股票指數只允許 VDF 核准的 Adjusted Price 欄位進入可繪圖 Numeric Catalog。原始 `close` 不會作為正式股票價格退路。
- TA‑Lib 不負責下載股價；它只以 VDF 提供的 Adjusted Price 計算 SMA、EMA、RSI、MACD、BBANDS。量能指標使用 Split‑Adjusted Volume，缺值填 `0`，不向前沿用。
- 價格缺值只以前一交易日值 Forward‑Fill；禁止兩日平均或未來資料回填。
- 美股 T 日效果映射至下一個台股交易日，禁止同日時間穿越。

要接入新 VDF 來源，需同步新增：

1. `config/vap_runtime_config.json` 的 Source。
2. VDF 工具產生的 Authorized Connection Record。
3. Connection 的 Canonical JSON SHA‑256 Fingerprint。
4. 股票來源的 `adjustedPriceField` 與 `taLibEvidence.status=PASS`。

## 使用者完整流程

1. PowerShell 啟動並完成 `SYNC CONNECT`。
2. Workbench 顯示 `VDF SYNC` 與 Runtime Catalog。
3. 從 Gallery 或 Catalog 新增圖。
4. 在左側大圖區繪製；右側參數可收合且不清除設定。
5. 以 `1Y／3Y／5Y／All`、Native／Weekly／Monthly／Quarterly／Yearly 與 Level／Change %／Rebase 100／YoY % 調整觀察規格；圖面上方直接顯示最新值、可見區間、來源與 As Of。
6. 可收藏目前 Observation Spec；相同設定以 SHA‑256 冪等去重。
7. 儲存圖像：IndexedDB 保存瀏覽器主檔，Runtime 同步保存 SVG、JSON、Observation Spec、資料證據與 Registry Event。
8. 搜尋、勾選及擷取特定保存圖；載回時恢復原本的觀察規格。
9. 將多圖依共同交易時間軸由上至下堆疊；面板高度為標準高度的 `0.5×–4×`。
10. 由使用者明確匯出 HTML、PNG、PDF 或 JSON；系統不自動下載。

## MacroMicro 互動基準

VAP 參考 MacroMicro 的「先讀圖、再調參數」操作模型，不複製其品牌樣式。大圖、水平圖例、最新值、快速時間區間、頻率與數值模式位於同一閱讀層；資料參數維持右側可收合。VDF、Adjusted Price、TA‑Lib、來源、As Of 與 Proxy 揭露仍由 VAP 自己的治理契約控制。

## 主要檔案

- `ui/VAP_Workbench_v025.html`：完整 Workbench。
- `js/vap-core-engine-v025.js`：資料、時間、堆圖與刷新契約。
- `js/vap-plotly-renderer-v025.js`：Plotly Dashboard Figure Contract。
- `js/vap-runtime-bridge-v025.js`：瀏覽器至本機 Runtime 的安全 Bridge。
- `runtime/vap_data_runtime_v025.py`：VDF Gate、Adapter、Cache、HTTP API 與檔案保存。
- `runtime/vap_vdf_manifest_tool_v025.py`：VDF Handoff Fingerprint 與 Gate 驗證工具。
- `config/vap_runtime_config.json`：Runtime 設定。
- `config/vdf_connection_manifest.json`：VDF 授權與股票 Adj／TA‑Lib 證據。
- `tests/run_all_tests_v025.py`：完整套件測試入口。
- `spec/vap_system_spec_v025.json`：系統 SSOT。

## 測試與 Fail‑Closed

```powershell
.\Invoke-VAP-v025.ps1 -RunTests -NoBrowser
```

Python／HTTP／SQLite／VDF／Adjusted Price／TA‑Lib Evidence／圖片防竄改／JavaScript／HTML 結構測試會自動執行。Workbench 另保留 136 項完整診斷及 72 項使用者情境。若本機沒有瀏覽器執行檔，報告會標記 `NOT_EXECUTED`，不會偽造通過。

## 安全邊界

- SQLite 與 DuckDB 固定 Read‑Only；Runtime 不提供 SQL 寫入 API。
- 不保存資料庫密碼。JSON Endpoint Header 只能從環境變數映射取得。
- 圖片保存採 Append‑Only；相同 ID 不得以不同內容覆寫。
- SVG 會拒絕 Script、事件屬性、ForeignObject、外部 URL 與 Data URL。
- Runtime 只服務套件目錄內的靜態檔，不允許路徑穿越。
