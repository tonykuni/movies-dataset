# VIA 標準化模板・更新版

**版本：** `2026-09-20`   
**模式：** local-only、standalone HTML、可自適應、可擴充、可驗證  
**更新日期：** 2026-09-20

本套件將 VIA 中央管理 UI、SYNCHRONIZER、Plotly × Seaborn light Engine Hub、四個產業 profile、E1/E2/E3 TriEngine handoff、CI/CD quality gate、跨裝置 E2E、效能分析、視覺回歸與可重複使用技能整合為單一標準模板。

## 直接使用

1. 優先以 `file://` 開啟 `ui/VIA-Complete-System.html`。
2. 也可以直接開啟 `ui/VIA-UI-Standalone-NoServer.html` 或 `ui/VIA-SYNCHRONIZER-Standalone.html`。
3. 在 SYNCHRONIZER 選擇產業模板，確認模組、圖表、歷史趨勢與 pivot 設定。
4. 需要匯出時使用內建 JSON、CSV 與 Excel 相容 SpreadsheetML `.xls`。

不需要 HTTP Server、CDN、資料庫、API 或遠端 chart runtime。`localStorage` 與 `BroadcastChannel` 僅用於同源分頁的本機狀態同步。完整離線部署、`file://` 測試、Chromium/Playwright E2E 與 loopback fallback 請參考 `docs/OFFLINE-DEPLOYMENT-AND-TESTING.md`。若需要 Python 資料分析或本地工作流探索，可選擇 `docs/references/streamlit_companion/`；它不屬於 canonical HTML runtime。

## Canonical 目錄

| 目錄 | 標準用途 |
|---|---|
| `ui/` | 完整系統 launcher、中央 UI 與 SYNCHRONIZER 正式入口 |
| `profiles/` | 四產業標準模組、圖表與 history schema |
| `engines/` | VIA Spec Extractor 與 TriEngine Hub 執行來源 |
| `ci/` | VSX、模組 validator、TriEngine quality gate 與 CI 範本 |
| `e2e/` | 跨裝置與跨頁同步 Playwright runner、結果與截圖 |
| `skills/` | VIA UCC/TriEngine 與 E2E/ZIP 可重複技能 |
| `docs/` | 狀態 schema、palette、handoff、參考、標準與離線測試文件 |
| `qa/` | CI artifacts、效能分析與視覺回歸資料 |
| `assets/` | 透明無框印章 Logo 與品牌資產 |
| `legacy/reference-templates/` | 舊版或參考 HTML，不作為正式入口 |

`docs/references/streamlit_companion/` 是 optional-local Python companion，提供 CSV 分析與 Mermaid／Graphviz／Agraph 工作流圖表。未安裝 Streamlit 或圖表套件時，兩個 canonical HTML 仍可正常執行。

## 產業 profile

目前標準 registry 共包含 4 個產業，模組數量如下：

| Profile ID | 名稱 | 模組數 |
|---|---|---:|
| `finance-cyber` | 金融資安 | 5 |
| `investment-research` | 投資研究 | 5 |
| `smart-healthcare` | 智慧醫療 | 5 |
| `smart-manufacturing` | 智慧製造 | 5 |

## 驗證與 quality gate

目前基準為桌機 `1440×1000`、平板 `768×1024`、手機 `390×844`。最新跨裝置 E2E 報告為 54/54 PASS，跨頁同步測試為 11/11 PASS，launcher user-flow 可驗證兩個正式入口，且中央 UI 與 SYNCHRONIZER 均維持無外部依賴的 standalone contract。標準化 QA 基準詳見 `qa/STANDARDIZED-VALIDATION.md`。

```bash
python3 e2e/run_via_investment_e2e.py \
  --html ui/VIA-UI-Standalone-NoServer.html \
  --out-dir e2e/results-local

python3 e2e/test_via_cross_page_sync.py \
  --ui ui/VIA-UI-Standalone-NoServer.html \
  --synchronizer ui/VIA-SYNCHRONIZER-Standalone.html \
  --out e2e/results-cross-page/report.json

python3 e2e/test_complete_system.py \
  --launcher ui/VIA-Complete-System.html \
  --out e2e/results-system/report.json

bash ci/run_complete_system.sh \
  "$(pwd)"

python3 skills/via-e2e-zip-verifier/scripts/validate_via_zip.py \
  /path/to/VIA-Standardized-Template-Updated.zip \
  --checksum-file /path/to/VIA-Standardized-Template-Updated.zip.sha256 \
  --run-extracted-e2e \
  --out-dir /tmp/via-standardized-verify
```

如需依 Spec IR 產生產業驗證器，使用 `skills/via-ucc-triengine-workbench/scripts/generate_module_validation.py`。如需整合 E1/E2/E3，先讀取 `docs/references/tri-engine-handoff.md`。

## 擴充規則

新增產業時必須在 `profiles/industry-profile.json` 加入穩定 profile ID、模組 ID、圖表 ID、history schema 與 pivot 欄位，然後同步產生 VSX、validator、browser smoke script、CI artifacts 與 E2E 回歸結果。新增插件只允許透過現有 local add-on slot 掛載，不得把 Server 或 CDN 依賴引入 canonical UI。
