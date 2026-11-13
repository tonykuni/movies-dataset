# VeritasDeployLedger 3.0 — VIA 商業部署升級開發包

**狀態：開發工具已實作並測試；尚未產生可交付客戶的 Windows 正式安裝包。**

本包延續 VIA_HybridEdgeCloud_AllInOne_v0200.py 的 2.2.0 授權核心，將相容核心修正為 2.2.1，新增 VDL 3.0 部署工廠、VCGC 轉接器及客戶端安裝器原始程式。原 Library 檔、母／子系統及 GitHub 未被改寫。

完整交接與限制見 `VIA_DeployLedger_v0300_Handover.html`。這是管理端開發包，包含原始碼；**不要直接把本 ZIP 當成客戶產品交付。**

## 先在 Tony 的 Windows 電腦執行

解壓縮後雙擊 `Start-VIA-Commercial.cmd`。

預設會使用既有 via_core／via_core_312／via_extract_312 環境，盤點既有 VIA 根、工具與 VRN 收尾紀錄，輸出 discovery.json、console.log、HTML 狀態頁；PowerShell 視窗保持開啟。此步驟不建立成功基線、不編譯、不安裝套件、不更新 GitHub。

若需明確選擇直譯器：

```powershell
.\Start-VIA-Commercial.cmd -PythonPath "C:\Python313\python.exe"
```

已具備經核對的部署契約後，執行三輪檢查：

```powershell
.\Start-VIA-Commercial.cmd -Contract "C:\VIA_ReleaseWork\deploy_contract.json"
```

完整製造流程由一個 job 串接：

```powershell
.\Start-VIA-Commercial.cmd -Job "C:\VIA_ReleaseWork\factory_job.json"
```

`*.example.json` 明確是未完成範本。不得將 placeholder 或 `closure_reviewed=false` 改成綠燈來跳過驗證。依實際入口、動態載入、資料檔、二進位工具、測試輸出與 VCGC 契約完成映射，才可使用；其中已填入最近貼回包觀察到的路徑，但不是新一輪現場確認。

## 實作範圍

- 每個子系統獨立入口與獨立編譯輸出；共同產品號、KEY 與授權閘。
- 來源只讀、複製到隔離暫存後 AST 注入啟動授權，獨立執行須有合法授權狀態與一次性程序綁定 token。
- 環境真實版本、pip check、工具 SHA256、子系統完整收尾、VCGC SSOT／Regex／同義字／登錄／網路／加速器回條；三輪後狀態穩定才形成候選基線。
- 環境修復僅委派明確配置的 VCGC 隔離修復契約。不刪原環境、不自行安裝 pip、不設定網路同意閘。
- Windows Nuitka standalone 編譯；明確動態模組與資源映射；第三方二進位工具／OCR 模型需列入 Assets、雜湊與授權告知。
- 客戶 runtime 以 AST 相依閉包抽取；排除發號、簽發授權、管理私鑰、測試及開發端 CLI。信任公鑰雜湊寫入編譯程式。
- 管理端 SQLite 產品／裝置席次台帳；Ed25519 授權簽章；重複啟用冪等、併發席次保護、撤銷後拒發。
- 客戶 ZIP 解壓前驗簽、檔案集合與雜湊核對、路徑及容量限制；DPAPI 裝置綁定；分版本安裝、快速測試、最後原子切換入口、回復上一版。
- 編譯後的 `VIA_Setup.exe` 預設有原生檔案／KEY 輸入精靈。初次啟用目前為離線請求與簽發往返，尚無已部署的線上授權服務。

## 已知真實狀態

最近已讀取貼回包 `VRN2_PasteBack_20261101_091958.zip`：

- VRN2_RoundAll v0122、ActivateVRN-2 v0166。
- Python：`C:\Python313\python.exe`，紀錄另列 via_core_312 擷取環境。
- 22 個環境檢查項目綠燈，但未提供完整套件版本／檔案雜湊閉包。
- 狀態 OPEN；VRN-2 待修 1 項（市場擷取）、人工 2 項、資料源 2 項。
- 見 `evidence/observed_windows_state.json`。紀錄時間未帶時區，保留原始字串，不自行換算。

因此本次不把「快好了」或「環境全綠」當成可商業出貨的證據。

## 測試

```powershell
& $Python .\tests\test_deployledger.py
& $Python .\legacy\VIA_HybridEdgeCloud_AllInOne_v0200.py selftest --rounds 3 --output-dir .\qa-local
```

交付證據中：新增 48 項部署／授權測試、相容核心 40 項 × 3 輪。Windows 原生編譯、DPAPI、PowerShell 解析／執行及真實 VCGC 接合尚未在此 Linux 工作環境實測。交易安裝測試使用明確標記的合成封包，並 mock 裝置授權與 EXE 功能執行；真實簽章驗證、授權簽發、竄改拒絕及席次競爭有執行。

## 發行門檻

`discover → prepare → build → qualify → seal`。`seal` 只產生 CANDIDATE，不會自動改為客戶核准版。

正式交付前須完成：Windows 當前真實閉包／原生相容調整、VCGC 零衝突及子系統收尾、Windows 編譯與合法／非法啟動驗證、Setup 的 Authenticode 簽署，以及乾淨 Windows 安裝／快速功能測試。若在 qualify 後簽署 Setup，必須重新 seal；若簽署引擎 EXE 本身，必須先更新建置證據並重新產生其模組 manifest 與驗收，不能只重簽 ZIP。

本地編譯、授權與裝置綁定提高原始碼提取和未授權使用的難度，不宣稱客戶有系統管理權限時仍能達成絕對不可逆向。離線授權撤銷無法即時通知未連線設備，已簽發授權會維持至到期；預設 30 天效期，續期／換機的服務流程尚須接到正式授權服務。第三方開源工具本身不等於 VIA 專有原始碼保護範圍。
