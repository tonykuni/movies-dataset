# VIA 離線部署與測試指南

## 1. 離線部署原則

VIA 的兩個正式入口都是單檔 HTML，不需要資料庫、CDN、API、HTTP Server 或遠端 chart runtime。建議先在可連網環境下載 ZIP 與 SHA-256 校驗檔，再把兩個檔案帶入隔離的離線環境。離線環境只需要 Python 3；若要執行自動化 E2E，另外準備 Chromium 與 Python Playwright。`docs/references/streamlit_companion/` 是可選的 Python companion，不是正式 HTML runtime 依賴。

## 2. 安裝與 checksum

```bash
cd /path/to/release
sha256sum -c VIA-Standardized-Template-Updated-2026-09-20.zip.sha256
unzip -q VIA-Standardized-Template-Updated-2026-09-20.zip -d /opt/via
cd /opt/via/via_standardized_template_updated
```

不要在離線主機重新下載套件或執行 `pip install`。如果需要 Playwright，請先在有網路的建置主機準備 wheel 或完整 Python 環境，再以離線媒體帶入。

## 3. 單一入口與直接使用 `file://`

先開啟完整系統入口：

```text
file:///opt/via/via_standardized_template_updated/ui/VIA-Complete-System.html
```

它會提供中央 UI、SYNCHRONIZER 與離線指南的單一啟動面板；正式功能仍由兩個 standalone HTML 分別執行。

以檔案管理器或瀏覽器開啟：

```text
file:///opt/via/via_standardized_template_updated/ui/VIA-UI-Standalone-NoServer.html
file:///opt/via/via_standardized_template_updated/ui/VIA-SYNCHRONIZER-Standalone.html
```

中央 UI 可直接查看投資工作區、圖表模式、時間區間、watchlist、設定抽屜與 add-on slot。SYNCHRONIZER 可套用四個產業 profile，並匯出 JSON、CSV 與 Excel 相容 SpreadsheetML `.xls`。

若已在離線 Python environment 預先準備 optional companion 依賴，可額外啟動本地 Streamlit 工作流與 CSV 分析：

```bash
bash docs/references/streamlit_companion/run_companion.sh
```

此命令只綁定 `127.0.0.1`，不會改變兩個 canonical HTML 的 `file://` 執行方式；未安裝 optional 依賴時，正式 HTML 仍完全可用。

## 4. SYNCHRONIZER 同源測試

在同一個 Chromium profile 中開啟兩個相同的 SYNCHRONIZER `file://` 頁籤。先在第一個頁籤套用產業 profile，再確認第二個頁籤透過 `BroadcastChannel` 收到模組與分析狀態。重新整理後確認 `localStorage` 的 version 2 state 仍存在。測試完成後清除該 file origin 的瀏覽器資料，避免把測試狀態留在工作環境。

某些瀏覽器對 `file://` 的 storage policy 不同。若瀏覽器阻擋 `localStorage` 或跨頁通訊，可使用離線 loopback fallback；它不會連到外部網路：

```bash
cd /opt/via/via_standardized_template_updated
python3 -m http.server 8765 --bind 127.0.0.1
```

接著只使用 `http://127.0.0.1:8765/ui/...`，完成測試後停止該程序。這是本機離線 fallback，不是產品部署依賴。

## 5. 離線自動化測試

先確認 Python、Chromium 與 Playwright 已預先安裝：

```bash
python3 --version
chromium --version
python3 -m pip show playwright
```

直接對 `file://` 中央 UI 執行三裝置測試：

```bash
python3 e2e/run_via_investment_e2e.py \
  --html ui/VIA-UI-Standalone-NoServer.html \
  --out-dir e2e/results-offline
```

驗證標準化目錄與所有 inline JavaScript：

```bash
python3 skills/via-e2e-zip-verifier/scripts/validate_standardized_package.py \
  /opt/via/via_standardized_template_updated \
  --run-e2e \
  --out-dir /tmp/via-offline-verify
```

驗證中央 UI 與 SYNCHRONIZER 跨頁同步：

```bash
python3 e2e/test_via_cross_page_sync.py \
  --ui ui/VIA-UI-Standalone-NoServer.html \
  --synchronizer ui/VIA-SYNCHRONIZER-Standalone.html \
  --out e2e/results-cross-page/report.json
```

同步測試基準為 11/11 PASS，涵蓋 BroadcastChannel、localStorage、storage event、模板、view-only、modules-only 與 manual scope。

驗證 ZIP 而不信任來源目錄：

```bash
python3 skills/via-e2e-zip-verifier/scripts/validate_standardized_zip.py \
  /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip \
  --checksum-file /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip.sha256 \
  --run-extracted-e2e \
  --out-dir /tmp/via-offline-zip-verify
```

## 6. 一鍵完整系統 quality gate

一次執行 canonical validator、三裝置 E2E、跨頁同步與 launcher user-flow test：

```bash
bash ci/run_complete_system.sh   /opt/via/via_standardized_template_updated
```

若要同時驗證 release ZIP：

```bash
bash ci/run_complete_system.sh   /opt/via/via_standardized_template_updated   /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip   /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip.sha256
```

若已在本機啟動 optional Streamlit companion，可加入：

```bash
STREAMLIT_URL=http://127.0.0.1:8501 bash ci/run_complete_system.sh /opt/via/via_standardized_template_updated
```

完整結果會寫入 `/tmp/via-complete-system/`，其中 `system-report.json` 為聚合結果。

## 7. 一鍵離線 smoke test

若要一次完成 canonical directory、三裝置 E2E，以及可選的 ZIP 解壓驗證：

```bash
bash ci/run_offline_smoke.sh \
  /opt/via/via_standardized_template_updated \
  /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip \
  /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip.sha256
```

若只測試已解壓模板，可省略後兩個參數。輸出預設寫入 `/tmp/via-offline-smoke/`，也可用 `OFFLINE_OUT=/path/to/output` 指定輸出位置。

## 8. 離線檢查標準

部署可接受的條件是：兩個 HTML 可直接開啟；standalone contract 沒有外部 resource tag；inline JavaScript 通過 Node syntax check；四個 industry profile 存在；JUnit 為 54 tests、0 failures、0 errors；Desktop、Tablet、Mobile 三個 viewport 都沒有水平 overflow；解壓後 E2E 為 54/54 PASS。

