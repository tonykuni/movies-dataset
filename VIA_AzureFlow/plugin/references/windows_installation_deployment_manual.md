# VIA 天青智流 AzureFlow QA Plug-in
## Windows 安裝、部署、操作與原始碼導讀手冊

**文件版本：** 1.1.0
**適用 Plug-in：** `via-azureflow-qa-plugin`  —  **角色：** standalone QA／inspection sub-engine
**撰寫日期：** 2026-09-20（+08:00）

> 本手冊說明如何把 Plug-in 匯出到另一個 Windows 開發環境，如何透過 PowerShell launcher 執行，以及如何檢視與使用 standalone HTML UI。Plug-in 是一次執行型本地工具，不需要安裝成 Windows Service，也不會自動修改來源檔案、SSOT 或 Windows 系統設定。

## 1. 系統定位與可部署內容

Plug-in 把兩個檢查能力整合成一個可插入母系統的子引擎。第一部分是 AzureFlow v8 的唯讀 engine／job／artifact inspection。第二部分是 VIA ZIP／E2E／standardized package verification。兩者由 `via_azureflow_qa.py` 以三個固定 action 統一調度：`inspect`、`verify` 與 `all`。[1] [2]

Plug-in ZIP 展開後具有下列結構：

```text
via-azureflow-qa-plugin/
├─ SKILL.md
├─ plugin_manifest.json
├─ Invoke-VIA-AzureFlowQA.ps1
├─ references/
│  ├─ integration_contract.md
│  └─ windows_installation_deployment_manual.md
├─ scripts/
│  ├─ via_azureflow_qa.py
│  ├─ inspect_azureflow.py
│  ├─ validate_via_zip.py
│  ├─ validate_standardized_package.py
│  └─ validate_standardized_zip.py
└─ templates/
   └─ VIA_AzureFlow_QA_Standalone.html
```

`plugin_manifest.json` 是給母系統讀取的 machine-readable registration。它宣告 plug-in ID、三個 action、Python entrypoint、PowerShell launcher、standalone UI、輸出 artifacts、支援的 ZIP 種類與安全政策。[3]

## 2. Windows 安裝前置條件

### 2.1 必要元件

| 元件 | 用途 | 檢查方式 |
|---|---|---|
| Windows 10／11 | 執行環境 | `winver` |
| PowerShell 7 或 Windows PowerShell 5.1 | 執行 launcher | `$PSVersionTable.PSVersion` |
| Python 3.10 或更新版本 | 執行 orchestrator 與 validators | `python --version` 或 `py -3 --version` |
| Edge／Chrome | 開啟 standalone HTML UI | 直接雙擊 HTML 或瀏覽器 `file://` 開啟 |
| Node.js（可選） | 檢查 standalone HTML 的 inline JavaScript syntax；ZIP validator 若檢查 HTML 也會使用 | `node --version` |

Plug-in 本身使用 Python standard library 與既有 validator 腳本，不要求 pip 套件。若要執行 ZIP 內的 extracted E2E，還需要該 ZIP 自己聲明的測試執行環境；這個動作必須明確加入 `-RunExtractedE2E`，不是預設流程。

### 2.2 建議的資料夾

建議把 Plug-in 放在不含空格的短路徑，便於 PowerShell 與 CI 呼叫：

```text
C:\VIA\plugins\via-azureflow-qa-plugin\
C:\VIA\work\reconstruction\
C:\VIA\delivery\
C:\VIA\QA\
```

來源文件、ZIP 與 Plug-in 可以分開保存。Plug-in 只讀取它們，不會把重建結果寫回來源位置。

## 3. 匯出 ZIP 與完整性確認

### 3.1 取得交付檔

從本次交付取得：

```text
VIA_AzureFlow_QA_Plugin_Standalone.zip
VIA_AzureFlow_QA_Plugin_Standalone.zip.sha256
```

把這兩個檔案放在 Windows 的暫存下載資料夾，例如：

```text
C:\Users\<使用者>\Downloads\
```

### 3.2 用 PowerShell 驗證 SHA-256

在 PowerShell 執行：

```powershell
$zip = 'C:\Users\<使用者>\Downloads\VIA_AzureFlow_QA_Plugin_Standalone.zip'
Get-FileHash -Algorithm SHA256 $zip
```

目前交付包的 SHA-256 以 ZIP 旁的 `VIA_AzureFlow_QA_Plugin_Standalone.zip.sha256` sidecar 為準。手冊不把 ZIP 自身的 hash 硬編碼在 ZIP 內，避免產生自我參照。若 PowerShell 計算出的 hash 與 sidecar 不一致，請停止安裝並重新取得 ZIP；不要對 hash 不一致的檔案執行 launcher 或解壓。

### 3.3 解壓與檔案檢查

```powershell
$zip = 'C:\Users\<使用者>\Downloads\VIA_AzureFlow_QA_Plugin_Standalone.zip'
$install = 'C:\VIA\plugins'
Expand-Archive -LiteralPath $zip -DestinationPath $install -Force
$plugin = Join-Path $install 'via-azureflow-qa-plugin'
Get-ChildItem -LiteralPath $plugin -Recurse -File | Select-Object FullName, Length
```

安裝完成後，至少應存在：

```text
C:\VIA\plugins\via-azureflow-qa-plugin\SKILL.md
C:\VIA\plugins\via-azureflow-qa-plugin\plugin_manifest.json
C:\VIA\plugins\via-azureflow-qa-plugin\Invoke-VIA-AzureFlowQA.ps1
C:\VIA\plugins\via-azureflow-qa-plugin\scripts\via_azureflow_qa.py
C:\VIA\plugins\via-azureflow-qa-plugin\templates\VIA_AzureFlow_QA_Standalone.html
```

## 4. 初次環境檢查

進入 Plug-in 目錄：

```powershell
Set-Location 'C:\VIA\plugins\via-azureflow-qa-plugin'
python --version
py -3 --version
$PSVersionTable.PSVersion
```

如果系統只有 `py` 而沒有 `python`，launcher 會自動嘗試 `py`。如果兩者都不存在，請先安裝 Python 3，並在安裝時選取 **Add Python to PATH**。安裝後重新開啟 PowerShell。

接著做不執行來源程式的語法檢查：

```powershell
python -m py_compile `
  .\scripts\via_azureflow_qa.py `
  .\scripts\inspect_azureflow.py `
  .\scripts\validate_via_zip.py `
  .\scripts\validate_standardized_package.py `
  .\scripts\validate_standardized_zip.py
```

`py_compile` 只解析 Python syntax，不會執行使用者輸入的來源檔案。

## 5. PowerShell launcher 詳細說明

### 5.1 Launcher 的執行流程

`Invoke-VIA-AzureFlowQA.ps1` 的流程如下：

1. 以 `ValidateSet` 限制 action 只能是 `Inspect`、`Verify` 或 `All`。
2. 由 `$MyInvocation.MyCommand.Path` 取得 launcher 所在資料夾，因此不依賴目前工作目錄。
3. 確認 `scripts\via_azureflow_qa.py` 存在。
4. 先尋找 `python`，找不到時再尋找 `py`。
5. 把 PowerShell 參數轉換成 Python CLI 參數。
6. 以 `& $pythonCommand @arguments` 執行 CLI。
7. 將 Python exit code 原樣傳回 PowerShell。

Launcher 的核心入口為：

```powershell
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cli = Join-Path $scriptDir 'scripts\via_azureflow_qa.py'
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
& $pythonCommand @arguments
exit $LASTEXITCODE
```

這個設計使 launcher 可以從任何目前工作目錄被呼叫，同時保留 Python 子程序的成功或失敗狀態。

### 5.2 Launcher 參數

| PowerShell 參數 | 必要性 | 說明 |
|---|---|---|
| `-Action Inspect` | 必要 | 只查 AzureFlow health、catalog、status、jobs、dashboard 與 local run |
| `-Action Verify` | 必要 | 只驗證 ZIP |
| `-Action All` | 必要 | 先 inspect，再 verify，寫統一 summary |
| `-Root <path>` | Inspect／All 必要 | AzureFlow reconstruction workspace 路徑 |
| `-RunsDir <path>` | 可選 | 指定 `app\runs` 以外的 runs 位置 |
| `-Zip <path>` | Verify／All 必要 | 要驗證的 ZIP 路徑 |
| `-ChecksumFile <path>` | 可選 | ZIP 對應的 SHA-256 text file |
| `-Output <path>` | 可選 | 輸出目錄；預設為目前目錄的 `VIA_AzureFlow_QA_Output` |
| `-BaseUrl <url>` | 可選 | AzureFlow API；預設 `http://127.0.0.1:8766` |
| `-PackageKind Auto` | 可選 | 自動選擇 VIA 或 standardized validator |
| `-PackageKind Via` | 可選 | 強制使用 VIA all-in-one validator |
| `-PackageKind Standardized` | 可選 | 強制使用 standardized ZIP validator |
| `-RunExtractedE2E` | 可選開關 | 明確啟用 extracted package E2E runner |
| `-NoArtifactProbe` | 可選開關 | Inspect 時不對 API artifact endpoint 逐項 GET |

`-Action` 是唯一必填語意參數。其他參數依 action 使用；例如 `Inspect` 不需要 `-Zip`，`Verify` 不需要 `-Root`。

### 5.3 PowerShell 執行政策

如果 Windows 阻擋本地 `.ps1`，先使用目前 PowerShell process 的暫時政策，不要修改整台電腦的永久政策：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

接著再執行 launcher。`-Scope Process` 只對目前 PowerShell 視窗有效，關閉視窗後恢復原設定。

## 6. 三個 action 的操作方式

### 6.1 Inspect：只檢查 AzureFlow

```powershell
$plugin = 'C:\VIA\plugins\via-azureflow-qa-plugin'
& "$plugin\Invoke-VIA-AzureFlowQA.ps1" `
  -Action Inspect `
  -Root 'C:\VIA\work\reconstruction' `
  -BaseUrl 'http://127.0.0.1:8766' `
  -Output 'C:\VIA\QA\inspect'
```

Inspect 會呼叫：

```text
GET /api/health
GET /api/catalog
GET /api/status
GET /api/jobs
GET /api/dashboard
```

並從 workspace 讀取：

```text
VIA_SSOT_Engine_Registry_v8.json
app\runs\<job_id>\record.json
app\runs\<job_id>\v8_unified.json
app\runs\<job_id>\v8_ast_modules.json
app\runs\<job_id>\v8_governance.json
```

輸出目錄會包含：

```text
C:\VIA\QA\inspect\
├─ VIA_AzureFlow_Engine_Job_Inspection.md
├─ inspect_summary.json
├─ stdout.txt
└─ stderr.txt
```

如果 API 不可用，inspection script 仍可使用 local run fallback；報告會明確記錄 API error，不會重啟服務。若 workspace path 不存在，結果會標示 `NOT_MOUNTED_IN_SANDBOX` 或對應的 path failure，不會把不存在的 Windows 檔案宣稱為已測試。

### 6.2 Verify：只驗證 ZIP

VIA all-in-one ZIP：

```powershell
& "$plugin\Invoke-VIA-AzureFlowQA.ps1" `
  -Action Verify `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -PackageKind Via `
  -Output 'C:\VIA\QA\verify'
```

Standardized ZIP：

```powershell
& "$plugin\Invoke-VIA-AzureFlowQA.ps1" `
  -Action Verify `
  -Zip 'C:\VIA\delivery\standardized.zip' `
  -ChecksumFile 'C:\VIA\delivery\standardized.zip.sha256' `
  -PackageKind Standardized `
  -Output 'C:\VIA\QA\verify'
```

`Auto` 模式只讀取 ZIP central directory 的 member names，未通過 path safety／CRC 前不解壓。若 ZIP 根目錄恰有一個 `manifest.json`，優先路由到 standardized validator；否則若看到 `ui/VIA-UI-Standalone-NoServer.html`，才路由到 VIA all-in-one validator。這個優先序允許 standardized package 同時包含自己的 central UI 檔案。

Verify 的基本檢查順序是：

1. 計算 ZIP SHA-256，若指定 checksum file 就比對。
2. 檢查 absolute path 與 `..` path traversal。
3. 執行 ZIP CRC integrity test。
4. 在隔離輸出資料夾解壓。
5. 找到 package root。
6. 檢查 required files。
7. 檢查 standalone HTML、inline JavaScript、E2E report、JUnit、industry profile、UI copy synchronization 與 screenshots。
8. 產生 `verification.json` 與 `verify_summary.json`。

若 checksum、path safety、CRC 或 package root 失敗，系統會提前輸出結構化 FAIL；不會繼續解析不存在的報告檔。

### 6.3 All：完整 QA

```powershell
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path $env:USERPROFILE "Downloads\VIA_AzureFlow_QA_$stamp"
& "$plugin\Invoke-VIA-AzureFlowQA.ps1" `
  -Action All `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output $out
```

All 會先產生 `inspect`，再產生 `verify`。兩者都完成後寫入：

```text
$out\VIA_AzureFlow_QA_Run_Summary.json
```

summary 的核心欄位如下：

```json
{
  "schema": "VIA_AZUREFLOW_QA_PLUGIN_RUN/1.0",
  "plugin": "via-azureflow-qa-plugin",
  "action": "all",
  "actions": {
    "inspect": {"status": "PASS", "exit_code": 0},
    "verify": {"status": "PASS", "exit_code": 0}
  },
  "safety": {
    "source_write": false,
    "source_delete": false,
    "code_execution": false,
    "network": false,
    "human_review_required": true
  },
  "status": "PASS"
}
```

只有 `inspect=PASS` 且 `verify=PASS` 時，combined `status` 才會是 `PASS`。若 ZIP 不存在、API 路徑未掛載或 package contract 不完整，summary 會保留具體 failure reason。

## 7. Standalone HTML UI 詳細導讀

### 7.1 開啟 UI

UI 位於：

```text
templates\VIA_AzureFlow_QA_Standalone.html
```

可以直接雙擊，或在 Edge／Chrome 輸入：

```text
file:///C:/VIA/plugins/via-azureflow-qa-plugin/templates/VIA_AzureFlow_QA_Standalone.html
```

UI 不需要 HTTP server、CDN、Node dev server 或遠端資源。它的執行角色是 **控制面板與命令產生器**，不是實際的 Python 執行器。

### 7.2 Layout 與配色

UI 使用 inline CSS。核心變數如下：

```css
:root{
  --paper:#f7faf9;
  --panel:#fff;
  --ink:#24343a;
  --muted:#6f7f83;
  --line:#dce8e5;
  --cyan:#2b9db0;
  --cyan-dark:#197789;
  --cyan-soft:#e7f5f6;
  --teal:#4c9f86;
  --yellow:#e8b04e;
  --red:#c96868;
}
```

整體使用淺色背景、白色 panels、細邊框、圓角與低強度陰影。桌面版使用左右兩欄；螢幕寬度小於 820px 時轉為單欄，三個 action buttons 轉為垂直排列。

主要 layout selector 是：

```css
.layout{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:16px}
```

左欄負責輸入，右欄負責 command preview、status、local log 與輸出提示。這個分工降低操作時的認知負擔，也讓 UI 可以在不改動 Python 的情況下替換。

### 7.3 輸入元件

UI 提供：

- `zipFile`：瀏覽器 file picker。
- `drop`：ZIP drag-and-drop 區域。
- `zipPath`：Windows ZIP 完整路徑。
- `rootPath`：AzureFlow workspace 完整路徑。
- `runsDir`：可選的 runs directory。
- `checksum`：可選 SHA-256 file。
- `baseUrl`：AzureFlow API URL，預設 localhost 8766。
- `outDir`：輸出資料夾。
- `e2e`：是否加入 `-RunExtractedE2E`。

瀏覽器故意只顯示被選檔案的名稱。因為瀏覽器的 file picker 不應將 Windows 完整本機路徑暴露給 JavaScript，使用者仍需在 `zipPath` 貼上真正的 Windows 路徑。這也讓同一個 HTML 能以 `file://` 在不同 Windows 使用者帳戶工作。

### 7.4 三個 action buttons

HTML 中只有三個主要 action buttons：

```html
<button class="action" data-action="inspect">只檢查 AzureFlow</button>
<button class="action secondary" data-action="verify">只驗證 ZIP</button>
<button class="action" data-action="all">完整 QA</button>
```

按鈕事件只呼叫 `run(action)`。它會呼叫 `command(action)`，把欄位值轉成 PowerShell 命令，顯示在 `#command`，並更新 `#status` 與 `#log`。瀏覽器不會呼叫 `fetch`，也不會啟動 Python 或 PowerShell。

命令產生器的核心邏輯是：

```javascript
function command(action){
  sync();
  state.action=action;
  var parts=['.\\Invoke-VIA-AzureFlowQA.ps1',
    '-Action',action.charAt(0).toUpperCase()+action.slice(1),
    '-BaseUrl',quote(state.baseUrl),
    '-Output',quote(state.outDir)];
  if(action!=="verify") parts.push('-Root',quote(state.rootPath));
  if(state.runsDir&&action!=="verify") parts.push('-RunsDir',quote(state.runsDir));
  if(action!=="inspect"&&state.zipPath) parts.push('-Zip',quote(state.zipPath));
  if(state.checksum&&action!=="inspect") parts.push('-ChecksumFile',quote(state.checksum));
  if(state.e2e&&action!=="inspect") parts.push('-RunExtractedE2E');
  return parts.join(" ");
}
```

### 7.5 Drag-and-drop 行為

`dragover` 事件會暫時套用 `.drag` CSS class，`drop` 事件只保存 `File.name` 並更新提示。它不讀取 ZIP 內容，也不把 ZIP 上傳到網路。使用者必須手動補上 Windows 完整路徑，然後複製 PowerShell 命令。

### 7.6 UI 與安全邊界

UI 的 inline script 不含 `<script src>`、`<link href>`、CDN、`fetch`、WebSocket、iframe、image 或 remote resource。它只操作 DOM、輸入值、local status、drag event 與 clipboard API。Clipboard API 只在使用者按下「複製命令」後執行；若瀏覽器阻擋，命令仍可手動選取。

## 8. Python orchestrator 詳細導讀

`via_azureflow_qa.py` 是 Plug-in 的實際執行核心。它的 `PLUGIN_DIR` 由目前腳本位置推導，因此 plug-in 可移植到任何 Windows 路徑，不依賴固定的 `/home/ubuntu` 或母系統工作區。[4]

### 8.1 Inspect route

`inspect_action()` 會建立 `inspect` 輸出資料夾，呼叫同資料夾的 `inspect_azureflow.py`，並將 stdout、stderr 與 Markdown report 分開保存。若 workspace path 不存在，會保留 `NOT_MOUNTED_IN_SANDBOX` 狀態；不會假設該 Windows path 在目前環境可讀。

### 8.2 Verify route

`detect_package_kind()` 只用 Python `zipfile` 讀取 central directory member names。它在 extraction 前判斷：

```python
root_manifests = [
    name for name in names
    if name.count('/') == 1 and name.endswith('/manifest.json')
]
if len(root_manifests) == 1:
    return 'standardized'
if any(name.endswith('/ui/VIA-UI-Standalone-NoServer.html') for name in names):
    return 'via'
return 'via'
```

因此 auto-detection 不會因為尚未通過安全檢查而執行 ZIP 內容。之後 `verify_action()` 才呼叫對應的 validator。不存在的 ZIP 會在 preflight 階段輸出 FAIL，並明確寫出 validator 未啟動。

### 8.3 Combined summary 與 exit code

`all` 將 inspect／verify 結果放進 `actions`，再由 `combined_status()` 決定總狀態：

- 任一 action 為 `FAIL` → `FAIL`。
- 沒有 FAIL，但有 `REVIEW_REQUIRED` 或 `SKIPPED` → `REVIEW_REQUIRED`。
- 所有 action 都 PASS → `PASS`。

CLI 的 exit code 只有在總狀態為 `PASS` 時是 0。這使 PowerShell、CI 或母系統可以直接判斷結果。

## 9. 母系統整合與部署模式

### 9.1 作為獨立工具

直接使用 PowerShell launcher。這是最適合 Windows 開發者的模式，因為可使用原生 Windows path、Downloads、拖曳 UI 與人工 review。

### 9.2 作為母系統 plug-in

母系統讀取 `plugin_manifest.json`，顯示三個 action，並把以下欄位視為單一 handoff：

```text
VIA_AzureFlow_QA_Run_Summary.json
```

母系統可以把 `inspect/` 與 `verify/` 以兩個子面板呈現，不需要複製來源文件。`plugin_manifest.json` 中的 `ssot_promotion=false` 與 `automatic_command_activation=false` 必須保留，因為 QA PASS 不等於批准指令或提升 SSOT 狀態。

### 9.3 CI／開發腳本

CI 可直接呼叫 Python CLI，不需要開啟 HTML：

```powershell
python .\scripts\via_azureflow_qa.py all `
  --base-url 'http://127.0.0.1:8766' `
  --root 'C:\VIA\work\reconstruction' `
  --zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  --checksum-file 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  --out-dir 'C:\VIA\QA\ci-run' `
  --no-artifact-probe
if ($LASTEXITCODE -ne 0) { throw 'VIA AzureFlow QA failed' }
```

`--no-artifact-probe` 適合 API endpoint 較慢或只想先取得 catalog／job summary 的 CI；完整驗證時應移除這個選項。

Plug-in 不會自行建立 Windows Service 或常駐背景程序。若使用者要排程，應由 Windows Task Scheduler 或母系統 CI 明確呼叫 launcher，並把每次輸出放在獨立 timestamped directory；不要讓排程覆寫前一次報告。

### 9.4 完整系統一鍵流程

若要把 manifest、AzureFlow inspection、ZIP verification、combined handoff 與 Task Scheduler readiness 收斂成一次可稽核執行，使用根目錄的 `Invoke-VIAAzureFlowQASystem.ps1`。它會先讀取 `plugin_manifest.json`，確認所有核心 entrypoints 存在，再呼叫既有 `All` QA action，最後產生：

| 輸出 | 用途 |
|---|---|
| `VIA_AzureFlow_QA_System_Report.json` | machine-readable manifest、QA、排程 readiness、activation 與 safety 狀態 |
| `VIA_AzureFlow_QA_System_Report.md` | 人工 review 用的完整矩陣與 handoff 報告 |
| `qa/` | 既有 inspect／verify／combined QA 輸出 |
| `activation_result.json` | 是否要求、阻擋、失敗或完成 Windows Task Scheduler registration |

先執行不註冊任務的完整 system run：

```powershell
$plugin = 'C:\VIA\plugins\via-azureflow-qa-plugin'
& "$plugin\Invoke-VIAAzureFlowQASystem.ps1" `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output 'C:\VIA\QA\system-run' `
  -NoArtifactProbe
if ($LASTEXITCODE -ne 0) { throw 'VIA AzureFlow complete system QA failed' }
Get-Content 'C:\VIA\QA\system-run\VIA_AzureFlow_QA_System_Report.json' | ConvertFrom-Json |
  Select-Object status,version,manifest_summary,qa,scheduling,activation
```

成功但尚未註冊任務時，`activation.status` 應為 `READY_FOR_WINDOWS_ACTIVATION`，而不是 `ACTIVATED`。這是預設安全行為。

完成人工 review 後，才在實際 Windows 主機明確加入 `-ActivateSchedule`：

```powershell
& "$plugin\Invoke-VIAAzureFlowQASystem.ps1" `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output 'C:\VIA\QA\system-run-activated' `
  -TaskName 'VIA-AzureFlow-QA-All' `
  -Schedule Daily `
  -At (Get-Date).Date.AddHours(2) `
  -RunOnlyWhenUserIsLoggedOn `
  -ActivateSchedule
if ($LASTEXITCODE -ne 0) { throw 'VIA AzureFlow Task Scheduler activation failed' }
Get-Content 'C:\VIA\QA\system-run-activated\activation_result.json' | ConvertFrom-Json |
  Select-Object status,registered,task_name,qa_exit_code,safety
```

這個開關只會在 `All` QA PASS 後呼叫 `Register-VIAAzureFlowQATask.ps1`。Python system layer 本身不會註冊任務；Linux／sandbox 執行只能產生 `READY_FOR_WINDOWS_ACTIVATION`，不能宣稱已完成 Windows Task Scheduler activation。

### 9.5 Task Scheduler 完整批次範例

Plug-in 提供三層 Windows 自動化入口：[8] [9] [10]

| 檔案 | 作用 |
|---|---|
| `scripts\Invoke-VIA-AzureFlowQA-Scheduled.ps1` | 每次排程建立 timestamped output、執行原有 launcher、寫入 `task_scheduler.log` 與 `task_result.json` |
| `scripts\Register-VIAAzureFlowQATask.ps1` | 建立、更新或移除 Windows Task Scheduler task |
| `Run-VIAAzureFlowQAScheduled.cmd` | 可直接指定給 Task Scheduler 的完整 CMD wrapper |

最簡單的方式是先編輯 `Run-VIAAzureFlowQAScheduled.cmd` 中的四個路徑：`ROOT`、`ZIP`、`CHECKSUM` 與 `OUTPUT_ROOT`。這個 wrapper 會呼叫 PowerShell scheduled runner，並把 runner 的 exit code 原樣傳回 Task Scheduler。

```bat
@echo off
setlocal EnableExtensions
set "PLUGIN_ROOT=%~dp0"
set "ROOT=C:\VIA\work\reconstruction"
set "ZIP=C:\VIA\delivery\VIA-All-Latest.zip"
set "CHECKSUM=C:\VIA\delivery\VIA-All-Latest.zip.sha256"
set "OUTPUT_ROOT=%USERPROFILE%\Downloads\VIA_AzureFlow_QA_Scheduled"
set "BASE_URL=http://127.0.0.1:8766"

powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass ^
  -File "%PLUGIN_ROOT%scripts\Invoke-VIA-AzureFlowQA-Scheduled.ps1" ^
  -Action All -PluginRoot "%PLUGIN_ROOT%" ^
  -Root "%ROOT%" -Zip "%ZIP%" -ChecksumFile "%CHECKSUM%" ^
  -BaseUrl "%BASE_URL%" -PackageKind Auto ^
  -OutputRoot "%OUTPUT_ROOT%" -NoArtifactProbe

set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
```

也可以用 PowerShell 註冊腳本建立每日任務。以下範例會在每天 02:00，以目前互動使用者身分執行 `All`，並將結果寫入 Downloads 的 timestamped directories：

```powershell
$plugin = 'C:\VIA\plugins\via-azureflow-qa-plugin'
& "$plugin\scripts\Register-VIAAzureFlowQATask.ps1" `
  -TaskName 'VIA-AzureFlow-QA-All' `
  -Action All `
  -PluginRoot $plugin `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -OutputRoot "$env:USERPROFILE\Downloads\VIA_AzureFlow_QA_Scheduled" `
  -Schedule Daily `
  -At (Get-Date).Date.AddHours(2) `
  -RunOnlyWhenUserIsLoggedOn `
  -NoArtifactProbe
```

註冊完成後，先確認 Task Scheduler 中的 task action、trigger、user、Start when available 與 output path。若要手動移除：

```powershell
& "$plugin\scripts\Register-VIAAzureFlowQATask.ps1" `
  -TaskName 'VIA-AzureFlow-QA-All' `
  -PluginRoot $plugin `
  -Unregister
```

此註冊腳本預設使用 `Interactive` logon type，適合需要 OneDrive、使用者磁碟或本地桌面環境的開發機。若要在無人登入時執行，應由 Windows 管理員依組織政策調整 task principal、帳戶權限、credential 與 network share access；不要直接把明文密碼寫進 CMD 或 PowerShell。

### 9.6 Task Scheduler 測試方法

先做不經 Task Scheduler 的 runner smoke test。這會執行相同的 scheduled runner，驗證 timestamped output、summary、task log、task result 與 exit code：

```powershell
$plugin = 'C:\VIA\plugins\via-azureflow-qa-plugin'
& "$plugin\scripts\Test-VIAAzureFlowQATask.ps1" `
  -Action All `
  -PluginRoot $plugin `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -OutputRoot "$env:TEMP\VIA_AzureFlow_QA_TaskTest" `
  -NoArtifactProbe
```

若要測試真正的已註冊 task，先以 `Register-VIAAzureFlowQATask.ps1` 建立 task，再指定相同的 `OutputRoot`：

```powershell
& "$plugin\scripts\Test-VIAAzureFlowQATask.ps1" `
  -TaskName 'VIA-AzureFlow-QA-All' `
  -UseRegisteredTask `
  -PluginRoot $plugin `
  -OutputRoot "$env:USERPROFILE\Downloads\VIA_AzureFlow_QA_Scheduled" `
  -TimeoutSeconds 600
```

測試成功的判定條件是：

```text
task_result.json.status == PASS
task_result.json.exit_code == 0
VIA_AzureFlow_QA_Run_Summary.json 存在且完整
task_scheduler.log 存在
```

若 `All` 中的 `verify` 因 ZIP contract 不完整而 FAIL，Task Scheduler 本身仍是正常啟動；這時 `task_result.json` 必須忠實呈現 FAIL，不能為了讓排程顯示成功而吞掉 exit code。

## 10. Windows 安裝與 Plug-in 視覺化圖表

Plug-in 提供兩種圖表格式。互動 HTML 適合在 Windows 開發環境中用滑鼠檢視；Mermaid／PNG 適合放在文件、稽核報告或版本庫中。[11] [12]

### 10.1 互動 HTML

開啟：

```text
templates\VIA_AzureFlow_Windows_Deployment_Interactive.html
```

可以直接雙擊，或輸入：

```text
file:///C:/VIA/plugins/via-azureflow-qa-plugin/templates/VIA_AzureFlow_Windows_Deployment_Interactive.html
```

互動圖表提供：

1. 「看安裝流程」聚焦 ZIP hash、解壓、launcher 與 Python。
2. 「看三個 QA Actions」聚焦 orchestrator、inspect、verify、all 與 validators。
3. 「看 Task Scheduler」聚焦 scheduled runner、timestamped output、人工 review 與母系統 handoff。
4. 點選任一節點查看用途、命令、輸入、輸出與安全限制。
5. 「下載圖表狀態 JSON」保存目前選取節點與本地檢視狀態；不會上傳任何檔案。

圖表頁面只使用 inline CSS／JavaScript。它不使用 CDN、fetch、WebSocket 或遠端圖片，並明確標示 `source_write=false`、`source_delete=false`、`network_default=false` 與 `human_review_required=true`。

### 10.2 Mermaid 與 PNG

Mermaid source：

```text
references\VIA_AzureFlow_Windows_Deployment_Architecture.mmd
```

靜態 PNG：

```text
references\VIA_AzureFlow_Windows_Deployment_Architecture.png
```

Mermaid 圖表將下列資料流串起來：

```text
Windows host
  → ZIP + SHA-256
  → Expand-Archive
  → PowerShell launcher／Python orchestrator
  → inspect／verify／all
  → VIA 或 standardized validator
  → timestamped output
  → Task Scheduler
  → human review／parent handoff
```

Windows 使用者通常直接開啟 PNG 或互動 HTML 即可。若開發環境使用 VS Code，可用 Mermaid extension 編輯 `.mmd`；不需要把 Mermaid runtime 放入 Plug-in 的執行流程。

## 11. 輸出目錄與解讀

典型的 `all` 輸出：

```text
C:\VIA\QA\run-20260920-0044\
├─ VIA_AzureFlow_QA_Run_Summary.json
├─ inspect\
│  ├─ VIA_AzureFlow_Engine_Job_Inspection.md
│  ├─ inspect_summary.json
│  ├─ stdout.txt
│  └─ stderr.txt
└─ verify\
   ├─ verification.json
   ├─ verify_summary.json
   ├─ stdout.txt
   ├─ stderr.txt
   └─ validator\
      └─ extracted\
```

`verification.json` 是 ZIP validator 的詳細檢查結果。`verify_summary.json` 是 orchestrator 對該 action 的包裝結果。`VIA_AzureFlow_QA_Run_Summary.json` 是父系統最適合讀取的總結檔。

若 output directory 已存在，CLI 會建立或更新其中的 action 子目錄。為避免稽核資料互相覆蓋，正式 CI 或批次流程請使用 timestamped output directory。

## 12. 故障排除

### PowerShell 顯示 script execution 被禁止

使用目前 process 的暫時政策：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

不要在沒有安全審核的情況下修改 `LocalMachine` execution policy。

### 顯示 Python not found

檢查：

```powershell
Get-Command python
Get-Command py
```

安裝 Python 3 後重新開啟 PowerShell。Launcher 不會自動下載或安裝 Python。

### UI 可以開啟但命令執行失敗

UI 的定位是 command preview，不是執行器。請確認：

1. 已把 `zipPath` 填成完整 Windows 路徑。
2. 已把 `rootPath` 填成實際 AzureFlow workspace。
3. PowerShell 的 current directory 是 Plug-in 根目錄，或使用 launcher 的完整路徑。
4. Python 已在 PATH。
5. 檢查 `VIA_AzureFlow_QA_Run_Summary.json`、`stdout.txt` 與 `stderr.txt`。

### Windows path 被標記為未掛載

這個狀態表示目前執行環境看不到該 path。在真正 Windows 主機上，請確認磁碟、OneDrive 或 network share 已掛載，並確認 PowerShell 使用的帳戶具有讀取權限。不要把 sandbox 的 `NOT_MOUNTED_IN_SANDBOX` 解讀成原始 Windows 文件本身不存在。

### AzureFlow API 不可用

`inspect` 仍會產出 API error 與 local fallback 資訊。檢查：

```powershell
Invoke-WebRequest 'http://127.0.0.1:8766/api/health'
```

Plug-in 不會因為 API quiet 或 unavailable 自動重啟服務。請由管理者另行檢查 AzureFlow v8 server。

### ZIP checksum、path safety 或 CRC 失敗

停止使用該 ZIP。重新取得與 checksum 相符的交付包。不要以 `-RunExtractedE2E` 重試不安全或 hash 不一致的 ZIP。

### Standardized package 被判成 VIA package

改用明確參數：

```powershell
-PackageKind Standardized
```

`Auto` 只根據 ZIP member names 判斷。若 package 同時混合多種 layout，應由建置端先拆分成單一契約的 ZIP。

### Node.js 不存在

基本 inspect 與 ZIP path／CRC 驗證不一定需要 Node.js。若 package contract 要求 inline JavaScript syntax check，請安裝 Node.js，或在 CI 環境補上 Node runtime。缺少 Node 時不應把「未執行 syntax check」宣稱為完整通過。

## 13. 安全與功能邊界

本 Plug-in 的 `PASS` 只代表相應檢查契約通過。它不代表：

- 已批准或自動執行 command。
- 已將 v8 SSOT 從 review 狀態提升為 active。
- 已對 Windows 真實樣品完成測試，除非該 path 在當前 Windows 主機確實可讀。
- 已啟用網路 provider、VAKE fetch 或外部 deployment。
- 已把來源修正內容寫回原始文件。

`-RunExtractedE2E` 是明確的額外選項。它只在 checksum、path safety 與 CRC 通過後執行 packaged test runner；此操作仍不等於執行使用者提供的來源程式。

## 14. 版本與完整性資訊

| 檔案 | SHA-256 |
|---|---|
| `Invoke-VIA-AzureFlowQA.ps1` | `98cadc4a61634af896bdf21b941e778ad8edfe85e6e0b2abd342a06e50849d12` |
| `Invoke-VIAAzureFlowQASystem.ps1` | `d1d193b6bdd515ac23b1c85222fc23e610e426aa7a11f3210ec662dd14f9db25` |
| `templates/VIA_AzureFlow_QA_Standalone.html` | `567a3ce2ae5dfc8cdeb441b607ffc9d5047e78e8972018df6ee112d212b45749` |
| `scripts/via_azureflow_qa.py` | `7b86eb8c4aa351520b55298502b496567ab298a334af3190eb95ed6425c9f84a` |
| `scripts/via_azureflow_qa_system.py` | `5494757f0215168a33e4c4b8eb33c0382f17897da89d31957098a0a4b6f89bf7` |
| `plugin_manifest.json` | `6207dc100488e7c8bdbcfd12d8dca7aed0bf7e91f998eb964ba7fa21b7aea49d` |
| `templates/VIA_AzureFlow_Windows_Deployment_Interactive.html` | `016fb0581da5463ef2a16154990f6b81cd0997c1359c1461feba345ab8223c05` |
| `references/VIA_AzureFlow_Windows_Deployment_Architecture.mmd` | `b1f02c06c4fecd834051828008e007fd09057d543eb1e85a12b62d7ce0601989` |
| `scripts/Invoke-VIA-AzureFlowQA-Scheduled.ps1` | `432de818f7b70ba185dc3b77163b351be3be1f5c16aa295d1ffe9f05bc589adb` |
| `Run-VIAAzureFlowQAScheduled.cmd` | `0bb8bd05e78aebb3294c9067cdb43d50495cb44dc06cbc0701e6ab0ca876bc3e` |
| `VIA_AzureFlow_QA_Plugin_Standalone.zip` | Read the external `.sha256` sidecar; the ZIP does not contain its own checksum. |

## References

[1]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/SKILL.md "VIA AzureFlow QA Plug-in skill workflow"
[2]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/integration_contract.md "VIA AzureFlow QA Plug-in integration contract"
[3]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/plugin_manifest.json "VIA AzureFlow QA Plug-in manifest"
[4]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/scripts/via_azureflow_qa.py "VIA AzureFlow QA Plug-in orchestrator source"
[5]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/Invoke-VIA-AzureFlowQA.ps1 "VIA AzureFlow QA Windows PowerShell launcher"
[6]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/templates/VIA_AzureFlow_QA_Standalone.html "VIA AzureFlow QA standalone HTML UI"
[7]: file:///home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Plugin_Standalone.zip "VIA AzureFlow QA Plug-in portable ZIP"
[8]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/scripts/Invoke-VIA-AzureFlowQA-Scheduled.ps1 "VIA AzureFlow QA Windows scheduled runner"
[9]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/scripts/Register-VIAAzureFlowQATask.ps1 "VIA AzureFlow QA Task Scheduler registration script"
[10]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/scripts/Test-VIAAzureFlowQATask.ps1 "VIA AzureFlow QA Task Scheduler test harness"
[11]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/templates/VIA_AzureFlow_Windows_Deployment_Interactive.html "VIA AzureFlow Windows deployment interactive architecture"
[12]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/VIA_AzureFlow_Windows_Deployment_Architecture.mmd "VIA AzureFlow Windows deployment Mermaid source"
[13]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/Invoke-VIAAzureFlowQASystem.ps1 "VIA AzureFlow complete system Windows launcher"
[14]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/scripts/via_azureflow_qa_system.py "VIA AzureFlow manifest-driven complete system CLI"
[15]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/integration_contract.md "VIA AzureFlow complete system and activation contract"
