# VIA Dual Web Scraping Engine Package

版本：2026-08-19 Consolidated Package

## 必要檔案

- `VIA_WebScraping_DualEngine_Governance_Controller.py`：唯一控制入口。
- `VIA_Unified_WebScraping_Playwright_Engine.py`：Python 爬蟲引擎。
- `VIA_WebScraping_Playwright_Engine.js`：JavaScript 爬蟲引擎。
- `VIA_Investment_Report_Type_SSOT.json`：投資報告類型中英文契約。
- `VIA_Investment_Report_Classifier.py`：Python 報告分類器。
- `VIA_Investment_Report_Classifier.js`：JavaScript 報告分類器。
- `VIA_WebScraping_Compliance_SSOT.json`：法遵、風險與 PII 契約。
- `VIA_WebScraping_Compliance.py`：Python 法遵模組。
- `VIA_WebScraping_Compliance.js`：JavaScript 法遵模組。
- `package.json`：Node.js 依賴契約。

所有檔案必須放在同一資料夾。不要單獨移動其中一個 `.js` 或 `.json`。

## Windows 安裝

```powershell
python -m pip install playwright httpx beautifulsoup4 lxml trafilatura `
  readability-lxml extruct html2text pyarrow duckdb
python -m playwright install chromium

npm install
npx playwright install chromium
```

## 完整自測

```powershell
python VIA_WebScraping_Compliance.py
python VIA_Investment_Report_Classifier.py
python VIA_Unified_WebScraping_Playwright_Engine.py --self-test
node VIA_WebScraping_Playwright_Engine.js --self-test
python VIA_WebScraping_DualEngine_Governance_Controller.py --self-test
```

## 診斷模式

診斷模式不會對外抓取：

```powershell
python VIA_WebScraping_DualEngine_Governance_Controller.py `
  --mode diagnose `
  --output-dir VIA_Diagnostics
```

## 實際執行

每次實際爬取都必須提供同意、用途與授權依據：

```powershell
python VIA_WebScraping_DualEngine_Governance_Controller.py `
  "https://example.com/research" `
  --mode dual `
  --consent-token "I_ACCEPT_RESPONSIBLE_SCRAPING" `
  --purpose "擷取公開投資研究報告供個人研究使用" `
  --authorization-basis "公開頁面且依網站條款及 robots.txt 合規存取" `
  --pii-mode full `
  --output-dir VIA_Output
```

## 安全限制

- 不繞過登入、付費牆、CAPTCHA、WAF 或其他存取控制。
- `robots.txt` 或必要法遵狀態無法確認時採 Fail-Closed。
- ToS 自動掃描是風險提示，不是法律意見。
- 中文姓名與地址不以寬鬆 Regex 自動刪除，避免污染投資資料。
- 台灣身分證與信用卡須通過檢查碼後才遮蔽。

