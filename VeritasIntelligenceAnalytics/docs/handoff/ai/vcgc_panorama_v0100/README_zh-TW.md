# VCGC 全景啟用檢查套件 v0100

本套件沿用電腦內既有 VCGC、工具鎖冊、加速器與全功能測試管理器。作用是啟用本次執行所需支援 API、核對功能就緒狀態，並對指定兩個目錄做三輪全景稽核。它不是 VIA 全套引擎安裝包，也不會替每一個業務系統開啟正式擷取任務。

**交付狀態：Python 編譯及 13/13 隔離回歸測試通過；Windows PS7 與真實 VIA 引擎尚未在本次環境執行。** 13 項包括失敗阻擋、逾時、來源變動偵測及完整流程的合成引擎測試；不等於 328 個 VIA 測試站已通過。

## 直接啟動

下載 VCGC_Panorama_v0100.zip 至 Downloads，在 PowerShell 貼上：

```powershell
$ViaZip = Join-Path $env:USERPROFILE 'Downloads\VCGC_Panorama_v0100.zip'
$ViaPack = Join-Path $env:LOCALAPPDATA 'VIA\VCGC_Panorama_Pack_v0100'
Expand-Archive -LiteralPath $ViaZip -DestinationPath $ViaPack -Force
pwsh -NoLogo -NoProfile -NoExit -File (Join-Path $ViaPack 'Invoke-VCGC-Panorama-v0100.ps1')
```

預設掃描：

- `C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics`
- `C:\Users\tonyk\OneDrive\Documents\movies-dataset`

作用中 VCGC 優先選第二個目錄內的 `VeritasIntelligenceAnalytics`；兩個根目錄都掃描，但不混用兩套 VCGC、不同步或覆蓋彼此的程式。完整參數放在 PS1 與 PY 頂部。

若需明確指定作用中 VIA 與既有環境：

```powershell
& "$env:LOCALAPPDATA\VIA\VCGC_Panorama_Pack_v0100\Invoke-VCGC-Panorama-v0100.ps1" `
  -ViaRoot 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' `
  -Python '請改為既有 via_core 環境的 Scripts\python.exe 完整路徑'
```

需要 PowerShell 7、Python 3.11+、完整本機 VCGC 版本鏈。自動偵測先使用已啟動的 venv，再找常見 via_core 位置與 PATH；找不到時報錯，不自動改裝 Python。這次不下載缺少的 VIA 來源，也不自動安裝依賴。

## 已核對的工具矩陣

GitHub 唯讀參考點：`tonykuni/movies-dataset`，commit `4647c8c12e931b6d69730cd0077ecfb41caba1b5`。VCGC 主控台尾版為 v0192，功能冊 v0191 有 328 個測試站；完整表見 `VCGC_FUNCTION_STATIONS.csv`。實際執行以本機冊為準，版本差異會保留在報告。

| 類別 | 參考鎖定版本 | 本機操作與證據 |
|---|---|---|
| Token 全景工具 CGC_MDL158 | v0117 | token 預檢；read、slice、JSON slice、pack、chain、digest、ETag 重用 |
| Python Celeritas | v1141 | 經 VIA_SuperAccel_Module.activate(apply_limits=True)；記錄實際回傳與執行緒預算 |
| PowerShell 加速器 | 既有 VIA_PS_Accel_Module / Celeritas.PS7 | 在 PS1 行程載入與 Start；離開 finally 還原；載入與效能提升分開 |
| 網路 Aegis Nexus | v1652 | SHA、入口工具卡、冊上網路轉接自測；不將外站成功當成既有事實 |
| Unified NLP | v0108 | 合成短文 text --file --brief smoke + 冊上自測 |
| Generic Layout Hub | v0110 | 鎖冊存在、SHA、冊上相關測試 |
| Polars Frame | v0100 | 鎖冊存在、SHA、冊上相關測試 |
| Praddle | v0100 | 鎖冊與既有測試；OCR 隔離環境缺少就保留未驗證 |
| PDFPlumber Plus | v0102 | 鎖冊與既有測試 |
| OCR Super | v0102 | 鎖冊與既有測試 |
| 原生 VIA MCP Engine | v0102（尾版，非工具鎖項） | VCGC mcp doctor 與功能冊中的 selftest |
| VCGC MCP Server CGC_MDL279 | v0100（登錄功能） | 冊上 selftest；不新增外部平台設定或長駐服務 |

## 節省 Token 的七項用法

其中 `$V` 為本機 VCGC 主控台尾版，`$E` 為本機鎖冊 token.path，`$N` 為 nlp.path；工具由鎖冊選定，不以檔名最新作為換版理由。

| 工具 | 命令型式 | 用途 |
|---|---|---|
| read | `python $E read <檔案或目錄>` | 先看骨架、定義與問題，JSON 支援深度摘要 |
| slice | `python $E slice <py> <函式名>` | 只讀需要的完整定義；也支援 JSON 路徑 |
| digest | `python $E digest <log>` | 讀取判決摘要，完整 log 保留 |
| pack | `python $E pack <目錄>` | 先取資料夾索引再讀檔 |
| --if-etag | `python $E read <檔案> --if-etag <上一張etag>` | 同內容回傳 304；必須有前次內容可重用 |
| chain | `python $E chain <家族或檔案> --all` | 薄尾版本鏈與覆寫關係 |
| NLP brief | `python $V run <鎖定NLP路徑> text --file <文字檔> --brief` | 長文摘要；不可代替原始證據與驗算 |

套件會呼叫上述介面並保存輸出，ETag 額外確認 304 標記。節省比例沒有預設數字，不保證任何百分比。Manus 提到的 agentmemory、Ponytail、OmniRoute，以及其他候選工具不能單靠頁面標題判定已安裝；本套件不虛報它們已啟用。

## 執行順序與三輪檢查

1. 載入既有 PS 加速器；尋找本機 VCGC。第一個 VCGC 動詞為 `token`；失敗則停止後續啟用與串測，但仍產出唯讀來源診斷。
2. 執行 `handoff check`、`functions`，驗鎖定工具 SHA。CRLF/LF 差異獨立標為 LINE_ENDINGS_ONLY，不改原檔。呼叫 Python 加速 API，取得 CPU 執行緒限制；可用記憶體不足時降低掃描併行數。
3. `test --quick`、`enter --no-pull --card`、`test inventory`。`--card` 僅核對入口與支援工具，沒有啟動正式業務流程。
4. **第一輪：** 遞迴所有保留版本的 .py、.ps1、.psm1、.psd1。Python AST + 記憶體內 compile；PowerShell 原生 Parser.ParseFile。被掃描檔案不會因掃描而執行。記錄雜湊、定義、橋接標記、加速呼叫候選及直接網路呼叫候選。
5. **第二輪：** 循序重查 Python 語法錯誤、同名異內容、缺橋標記與網路轉接候選；執行原生 Token 工具、SSOT panorama，再由 VCGC 執行 `test --full`。完整串測不重用舊綠燈，可能耗時較長。`-ReuseReceipts` 可改用管理器既有的相依指紋重用策略。
6. **第三輪：** 重新列舉來源，檢查新增、刪除及內容變動；收取本次新鮮的 TEST_latest.json、目前功能冊、狀態與交接收據。生成 HTML/JSON/CSV。

範圍說明：保留舊版、封存程式也會掃描，因此舊版問題可造成紅黃燈；不自動把它們當成現役錯誤。預設排除 `.git`、node_modules、venv/site-packages 等相依環境，排除清單逐項列出。使用 `-IncludeDependencies` 可納入依賴來源，`.git` 仍排除。符號連結與 Windows junction 不跟隨，明列未覆蓋，避免循環與跨根掃描。

「存在橋接標記」「AST 找到 API 呼叫候選」「執行 API 回傳」「真實效能提升」是不同證據。掃描不宣稱執行覆蓋率 100%，也不會為補標記而自動修改全部 PS/PY。程式修復與版本號變更需以本次報告的實際問題為依據。

## 輸出

預設：`%LOCALAPPDATA%\VIA\VCGC_Panorama_v0100\<執行時間>`

- `VCGC_PANORAMA.html`：可搜尋的三行 Header 靜態矩陣，完成後自動開啟；無 UI server。
- `SUMMARY.json`、`TOOLS.csv`：總結、工具版本、SHA 與實際執行狀態。
- `SOURCE_INVENTORY.json/csv`：每一個來源檔的檢查結果。
- `REVIEW.json`：需複核項；包含啟發式規則，不能不經確認就批次修改。
- `COMMANDS.json`、`logs/`：實際命令、時間、退出碼、完整日誌，每 15 秒心跳。
- `PS_AST.jsonl`、`PS_BOOTSTRAP.json`：PowerShell 語法及啟用證據。
- `SOURCE_CHANGES.json`、`EXCLUSIONS.json`：來源變化與未覆蓋範圍。
- `VCGC_TEST_RESULT.json`：本次管理器產出的串測收據；沒取得新收據就 UNVERIFIED。
- `LOCAL_FUNCTION_INVENTORY.json`：本機當次功能冊。

狀態碼：0 GREEN＝本次條件均通過；2 YELLOW＝尚有需確認或未驗證；1 RED＝缺檔、解析失敗、阻擋或測試失敗。語法通過不代表財報、資料庫或市場擷取結果已驗收。發現紅黃燈應先查看對應 command log，不要刪除日誌或改寫收據為綠燈。

## 保留既有環境

套件無 git pull、push、merge；沒有刪除舊版、AST 寫入、套件安裝、外部平台設定變更或新的 UI server。既有 VCGC 動詞會照自身設計寫入本機報告、事件與串測帳本。任何現成管理器的拒絕或同意閘都保留，不設置繞過旗標。未執行 `go`，因該完整操作台流程包含其他系統業務與同步動作，超過本次支援工具檢查範圍。

中斷後可重新執行；每次輸出為新目錄。若要沿用合法成功收據，加 `-ReuseReceipts`。逾時只終止本套件啟動的該子行程樹，不終止其他 Python/PowerShell 工作。PS1 finally 還原自身套用的加速設定。

## 驗證與續接

`python -B test_vcgc_panorama_v0100.py` 可重跑交付套件的 13 項隔離測試。`DELIVERY_QA.json` 是本次 Linux 測試收據；Windows PS7 原生解析與實際工具啟動必須在你的電腦上完成。

參考來源包含 GitHub 的 AGENTS.md、CLAUDE.md、工具鎖冊、AI 功能卡、全功能冊與實際 CLI 原始碼。Manus 與 ChatGPT 分享紀錄已讀取；Claude Code 分享連結導向登入頁，未據此推定其程式已合入或已啟動。

本機執行後，交接重點是 SUMMARY.json、COMMANDS.json、VCGC_TEST_RESULT.json 及第一個失敗步驟的 log。保留原始來源與測試證據，再依現役版本、版史與環境問題分批修正。
