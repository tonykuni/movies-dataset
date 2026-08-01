# Veritas Storage Optimizer 2026 — Desktop GUI Edition

本地端儲存空間清理與最佳化工具:將 Python / Node.js 雙清理引擎封裝為 **單檔式本地桌面 GUI 應用程式**(VIA house style:內嵌 HTTP 後端 + 動畫 HTML 前端 + 內嵌 Self-Test)。

```
VeritasStorageOptimizer/
├── VeritasStorageOptimizer_AllInOne.ps1   # ★ 單一 PowerShell 整併版 (見下節)
├── veritas_gui.py            # 單檔 GUI 主程式:stdlib http.server 後端 + 內嵌動畫前端
├── engine/
│   ├── veritas_cleaner.py    # Python 引擎 (僅標準庫)
│   └── veritas_cleaner.js    # Node.js 引擎 (Node v18+, 零 npm 套件)
├── tests/
│   ├── e2e_apitest.js        # 零相依 e2e:Python GUI 後端完整 API 契約 (42 assertions)
│   ├── e2e_ps_usertest.js    # 零相依 e2e:pwsh AIO 後端 + 三引擎 + 實刪 (59 assertions)
│   └── ps_lint.py            # PS7 靜態分析 (here-string / 括號平衡 / LL 規則)
├── logs/                     # append-only 活動日誌 + 每次執行的稽核日誌 (git 忽略)
└── README.md
```

## ★ 單一 PowerShell 整併版 (All-In-One)

`VeritasStorageOptimizer_AllInOne.ps1` 將**全部功能整併為一個檔案**(PS 7.0+,零外部模組):
原生 PowerShell 清理引擎(2-Pass Hash + 串流 MD5)、HttpListener 後端、內嵌動畫 HTML 前端、
內嵌 Self-Test,並在 `engine/` 腳本存在時自動掛載 Python / Node.js 為可切換子引擎。

```powershell
# GUI 模式:於 127.0.0.1:8868 啟動並開啟瀏覽器
pwsh -File VeritasStorageOptimizer_AllInOne.ps1

# 自訂連接埠 / 不開瀏覽器
pwsh -File VeritasStorageOptimizer_AllInOne.ps1 -Port 9000 -NoBrowser

# 無頭 CLI 模式:Dry-Run(加 -Execute 才實體刪除)
pwsh -File VeritasStorageOptimizer_AllInOne.ps1 -Dir D:\Downloads -MaxMB 500
pwsh -File VeritasStorageOptimizer_AllInOne.ps1 -Dir D:\Downloads -MaxMB 500 -Execute

# 內嵌自我測試 (28 assertions)
pwsh -File VeritasStorageOptimizer_AllInOne.ps1 -SelfTest
```

測試鏈(全部通過):`tests/ps_lint.py` 靜態分析 0 錯誤 → pwsh AST 解析 0 錯誤 →
`-SelfTest` 28/28 → `tests/e2e_ps_usertest.js` 真實後端 59/59(三引擎 Dry-Run、
防護 Guard、實體刪除、巢狀空目錄連鎖清除、Unicode 檔名、symlink 循環/逃逸圍堵、
非法閾值伺服器端拒絕、單元素 JSON 陣列形狀、300 檔案規模化精確重複比對、
404 / shutdown 契約)。

安全強化(第二輪 DEBUG 循環修正):

- **Symlink 圍堵** — 目錄遍歷一律不跟隨 symlink / junction(ReparsePoint),
  杜絕循環懸掛與「逃逸出目標範圍刪除外部檔案」
- **閾值伺服器端驗證** — `maxMB <= 0` 一律拒絕(前端、後端、引擎 CLI 三層);
  並修正 PS 後端 `maxMB: 0` 因 falsy 判斷被靜默改回預設值的缺陷
- **稽核檔名毫秒級時戳** — 同秒內多次執行不再互相覆寫

執行期間單檔即可運作(Python / Node 未安裝時自動停用對應子引擎,原生 PS 引擎永遠可用)。

## 核心架構 (2026 Storage Architecture)

| 設計 | 說明 |
|---|---|
| 二階段重複檔案比對 (2-Pass Hash Filtering) | 僅對「檔案大小相同」的候選群組計算 MD5,避免無謂 I/O |
| 串流分頁雜湊 (Streaming Chunk Hashing) | 固定 64 KB Chunk / Stream 讀取,數 GB 大檔也不會 OOM |
| 預設安全試執行 (Dry-Run Safety Mode) | 預設僅輸出預計刪除清單與可釋放容量;實體刪除需顯式切換模式 + 前端二次確認 |
| 關鍵系統路徑過濾 (System Protection) | 引擎跳過 `.git` `.svn` `.venv` `node_modules` `$RECYCLE.BIN` `System Volume Information`;GUI 後端另拒絕根目錄、家目錄與其上層 |
| 稽核日誌 (Audit Trail) | GUI 活動採 append-only 日誌;每次掃描/清理各產生獨立稽核檔 |

清理策略(兩引擎一致):

1. **暫存檔** — 副檔名 `.tmp .log .cache .bak .old .temp .swp .dmp` 標記刪除
2. **超大檔案** — 超過閾值(預設 200 MB)標記刪除
3. **重複檔案** — 同容量群組經串流 MD5 比對後,保留第一份、標記其餘副本
4. **空資料夾** — 由下而上遞迴清除(Python 引擎)

## GUI 桌面應用程式

### 環境需求

- Python 3.8+(僅標準庫,零外部相依)
- (選用)Node.js v18+ — 有安裝才能切換 Node.js 引擎;GUI 自動偵測並停用未就緒的引擎

### 啟動

```bash
python veritas_gui.py                     # 於 127.0.0.1:8867 啟動並自動開啟瀏覽器
python veritas_gui.py --port 9000         # 自訂連接埠
python veritas_gui.py --no-browser        # 不自動開啟瀏覽器
```

後端僅綁定 loopback (127.0.0.1),不對外開放。

### 操作流程

1. 輸入 **目標資料夾** 與 **大檔閾值 (MB)**
2. 選擇 **清理引擎**(Python / Node.js)
3. 預設 **僅掃描 Dry-Run**:即時顯示標記檔案數、空資料夾數、可釋放容量與完整清單
4. 確認清單無誤後切換 **實體刪除**,按下執行時會跳出不可復原警告的確認視窗
5. 每次執行的稽核日誌路徑顯示於結果面板,並存於 `logs/`

> ⚠️ 實體刪除為永久刪除(不經資源回收筒),請務必先以 Dry-Run 檢視清單。

## 測試

```bash
# 內嵌自我測試 (17 assertions):Token 替換、防護 Guard、輸出解析、沙盒 Dry-Run/Execute 往返
python veritas_gui.py --self-test

# 零相依 e2e 測試 (35 assertions):啟動真實後端,驗證前端頁面、/api/env、
# 雙引擎 Dry-Run、防護 Guard、實體刪除與 404 契約
node tests/e2e_apitest.js
```

## CLI 直接使用

```bash
# Python 引擎 — Dry-Run 安全預覽
python engine/veritas_cleaner.py --dir /path/to/clean --max-mb 200

# Python 引擎 — 實體刪除 + 自訂日誌
python engine/veritas_cleaner.py --dir /path/to/clean --max-mb 500 --log audit.log --execute

# Node.js 引擎 — Dry-Run / 實體刪除
node engine/veritas_cleaner.js --dir /path/to/clean --max-mb 200
node engine/veritas_cleaner.js /path/to/clean --max-mb 500 --execute
```

## 打包為獨立桌面執行檔

以 [PyInstaller](https://pyinstaller.org/) 打包為單一免安裝應用程式(啟動即開瀏覽器視窗):

```bash
pip install pyinstaller

# Windows → dist/VeritasOptimizer.exe / macOS → dist/VeritasOptimizer.app
pyinstaller --onefile --name VeritasOptimizer \
    --add-data "engine:engine" \
    veritas_gui.py
```

(Windows 上 `--add-data` 分隔符改用分號:`--add-data "engine;engine"`)

## 已知限制與後續方向

- 重複檔案採 MD5 指紋;如需抗碰撞可將兩引擎的 `md5` 換成 `sha256`(單行修改)
- Dry-Run 的空資料夾統計為「當前已空」者;實際執行時刪檔後可能出現更多可清除的空資料夾
- 進階路線:以 `send2trash`(Python)/ `trash`(Node.js)改為移入作業系統資源回收筒,提供反悔機制
