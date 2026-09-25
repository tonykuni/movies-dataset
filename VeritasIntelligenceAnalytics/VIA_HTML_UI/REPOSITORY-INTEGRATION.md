# VIA_HTML_UI

這個區域收錄已完成整合測試的 VIA 標準化 local-only HTML UI 系統。

## 開始使用

優先開啟單一入口：

```text
ui/VIA-Complete-System.html
```

也可以直接開啟兩個正式功能入口：

```text
ui/VIA-UI-Standalone-NoServer.html
ui/VIA-SYNCHRONIZER-Standalone.html
```

所有正式 HTML 都可以直接以 `file://` 開啟，不需要 Server、CDN、資料庫或外部圖表 runtime。SYNCHRONIZER 與中央 UI 透過同源 `localStorage` 與 `BroadcastChannel` 提供可選的本機跨頁同步。

## 完整測試

在 `VIA_HTML_UI/` 目錄執行：

```bash
bash ci/run_complete_system.sh "$(pwd)"
```

這個 gate 會執行 canonical package contract、Desktop／Tablet／Mobile E2E、跨頁同步、launcher user-flow、ZIP 驗證，以及在提供 Streamlit runtime 時的 companion smoke test。

目前已驗證結果：

- Canonical contract：20/20 PASS
- Cross-page synchronization：11/11 PASS
- Complete-system launcher：7/7 PASS
- Streamlit companion：5/5 PASS
- ZIP verification：23/23 PASS
- Cross-device E2E：54/54 PASS

詳細測試產物位於 `e2e/results-final/`，包含 `complete-system-report.json`、cross-page report、launcher report、Streamlit report、JUnit 與裝置截圖。

## 產業與擴充

標準 registry 位於 `profiles/industry-profile.json`，目前包含智慧製造、金融資安、智慧醫療與投資研究。未來 add-on 可沿用中央 UI 的 `VIA_REGISTER_ADDON` 與 SYNCHRONIZER 的 `VIA_REGISTER_SYNC_ADDON` contract；新增模組後應重新執行 `ci/run_complete_system.sh`。

## 品牌與視覺

UI 採用淺色灰藍／金色／狀態色系、緊湊自適應 layout、透明無框朱紅印章 Logo，以及本機 Plotly-like／Seaborn-inspired chart engine。桌機、平板與手機均已完成視覺與功能回歸。
