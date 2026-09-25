# VIA Investment UI Cross-Device E2E

這個測試套件使用 Python Playwright 與系統 Chromium，直接測試 VIA 的單檔 `file://` 中央管理 UI，不需要 HTTP Server、CDN 或外部圖表 runtime。

## 執行

```bash
python3 run_via_investment_e2e.py \
  --html ../VIA-UI-Standalone-NoServer.html \
  --out-dir results
```

可使用 `--devices desktop-1440,tablet-768,mobile-390` 指定裝置矩陣，或使用 `--headed` 開啟可視化瀏覽器。

## 中央 UI／SYNCHRONIZER 跨頁同步

使用 `test_via_cross_page_sync.py` 在同一個 Chromium context 開啟兩個頁面，驗證 `via.sync.state.v2`、`via.sync.v2`、`BroadcastChannel`、瀏覽器 `storage` event、模板資料、view-only scope 與 manual scope：

```bash
python3 test_via_cross_page_sync.py \
  --ui ../ui/VIA-UI-Standalone-NoServer.html \
  --synchronizer ../ui/VIA-SYNCHRONIZER-Standalone.html \
  --out-dir results-cross-page
```

這個測試仍然是本機離線測試；`file://` 在目前 Chromium 環境可共享同一個 storage origin。若目標瀏覽器對 `file://` storage 有不同安全政策，請改用離線 `127.0.0.1` loopback，或依序使用 JSON 匯出／匯入驗證。

## 完整系統 launcher 與一鍵 gate

`test_complete_system.py` 會從 `VIA-Complete-System.html` 依序開啟中央 UI、SYNCHRONIZER 與離線指南，並檢查 launcher 的 mobile 幾何與 browser console：

```bash
python3 test_complete_system.py \
  --launcher ../ui/VIA-Complete-System.html \
  --out results-system/report.json
```

要一次執行 canonical validator、三裝置 E2E、跨頁同步、launcher 與可選 Streamlit companion，使用：

```bash
bash ../ci/run_complete_system.sh "$(cd .. && pwd)"
```

若 Streamlit companion 已啟動，可加上 `STREAMLIT_URL=http://127.0.0.1:8501`；若本機已安裝 Streamlit，也可用 `RUN_STREAMLIT=1` 讓 gate 自動啟動與關閉它。

## 測試範圍

測試涵蓋初始 render、單檔無伺服器契約、水平溢出、投資卡片幾何、折線／面積／柱狀圖、1D／1W／1M／3M 範圍、tooltip／crosshair、市場範圍、全域搜尋、設定抽屜、新增銜接 modal、UI Lab、導覽與流量暫停、add-on 註冊、v2 state snapshot、行動版側欄、accessibility landmarks，以及 browser console/page errors。跨頁測試另外涵蓋投資模板由 SYNCHRONIZER 到中央 UI、視圖由中央 UI 回傳、localStorage envelope、storage event、view-only 與 manual scope。

## 輸出

每次執行會建立 `report.json`、`report.md`、`junit.xml`、每個裝置的 PNG 截圖與 `visual-findings.md`。CI 可直接使用 `junit.xml`；人員檢視使用 Markdown 與 PNG。

## 目前基線

2026-09-20 的完整矩陣包含 3 個裝置、每個裝置 18 項檢查，共 54/54 通過；跨頁同步為 11/11，launcher user-flow 為 7/7。若啟用 optional Streamlit runtime，companion smoke 為 5/5。
