# VeritasPulse — 封裝與發佈 (HTML / PWA / EXE)

`build_all.py` 產出的 `output/VeritasPulse_App.html` 是**單一自足檔**(資料內嵌、
無外部相依),三種發佈方式都從它出發。彈性設定見 `output/config.json`。

---

## 1. HTML(最簡單 · 零安裝)

直接把 `VeritasPulse_App.html` 給人或自己用 —— 雙擊用瀏覽器開即可。
- 優點:零安裝、跨平台、可放雲端硬碟、可 email。
- 列印 / PDF:App 內「會議紀錄」頁有「列印 / PDF」鈕,或瀏覽器 Ctrl+P 另存 PDF。
- 限制:純檔案模式下 Service Worker / PWA 安裝需要用 `http(s)://` 提供(見下)。

## 2. PWA(可安裝 · 離線 · 像 App)

`build_all.py` 會一併產出 `manifest.webmanifest`、`service-worker.js`、`vpl_icon.svg`。
要啟用安裝與離線,需用 HTTP 伺服器提供(不能用 file://):

```powershell
cd output
py -3.11 -m http.server 8777
# 瀏覽器開 http://localhost:8777/VeritasPulse_App.html
# Chrome/Edge 網址列右側會出現「安裝」圖示 → 裝成桌面/開始選單 App
```

- 優點:可安裝、離線可用(SW 快取)、有 App 圖示、獨立視窗。
- 設定:`config.json` 的 `"pwa": true/false` 控制是否輸出 PWA 檔。
- 部署到內網/雲:把 `output/` 整包放上任何靜態主機即可。

## 3. EXE(Windows 原生視窗 · 雙擊執行)

用 `desktop/` 的 pywebview 包裝 + PyInstaller 打包成單一 `.exe`:

```powershell
python build_all.py            # 先產生 output\VeritasPulse_App.html
cd desktop
pwsh -File .\Build-Exe.ps1     # 產出 dist\VeritasPulse.exe
```

- 優點:雙擊即開、原生視窗、不需瀏覽器、可發給非技術同仁。
- 原理:`vpl_desktop.py` 用 pywebview 開原生視窗載入內嵌的 HTML;
  PyInstaller `--onefile --windowed` 打成單檔 exe,HTML 以 `--add-data` 內嵌。
- 需求:Windows + `py -3.11`;首次會自動裝 pywebview / pyinstaller。
- 注意:`.exe` 必須在 Windows 上打包(跨平台無法產生 Windows 執行檔)。

---

## 彈性設定(所有功能可改)

編輯 `output/config.json` 後重跑 `build_all.py`:
- `modules`:任一模組開關,如 `{"ledger": false}` 關掉記帳。
- `accent`:改主色(預設橄欖綠 `#5e7032`),全 UI 連動。
- `brand` / `brand_sub`:改品牌名。
- `llm_providers`:ChatGPT/Claude/Gemini/Copilot/Notion 開關 + endpoint。
- `default_minutes_mode`:`concise` 或 `comprehensive`。
- `news_sources` / `world_clocks` / `weather_default`:首頁來源與城市。

## 自動布建(無衝突風險驗證後才布建)

```powershell
# 乾跑:只驗證衝突閘門,不安裝
py -3.11 -m vpl.core.env_arrange --deploy --root <supportive_module 路徑>
# 通過驗證後實際經 EnvManager 治理布建
py -3.11 -m vpl.core.env_arrange --deploy --live --root <supportive_module 路徑>
```

閘門檢查:Veritas 可達(可驗證)· 所有相依 APPROVED · env 掃描無衝突 ·
base-VIA 衝突檢查 · numpy 黃金律(<2.0)。**全部通過才布建**,否則 BLOCKED。
報告:`output/vpl_deploy.html`。
