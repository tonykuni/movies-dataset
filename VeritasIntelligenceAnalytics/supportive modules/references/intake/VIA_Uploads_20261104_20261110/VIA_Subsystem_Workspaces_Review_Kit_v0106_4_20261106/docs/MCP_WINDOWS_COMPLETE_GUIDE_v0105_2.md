# VIA Governance MCP — Windows 完整手動設定與 stdio 執行指南 v0105.2

> **文件範圍與實際狀態**：這是一份給 Windows 使用者的手動 staging／MCP client 設定指南，不是已在某台 Windows 電腦上執行完成的報告。此工作階段無法連到 Tony-NB（不可用，沒有可切換 workspace），因此本文件不宣稱已在 Tony-NB 安裝、啟動、註冊或驗證。已在目前 Sandbox 以有限 stdio smoke test 驗證的結果，明確標示為 **Sandbox**；Windows 相容性仍是 **NOT_RUN**。
>
> 本文件只會新增候選副本，不替換既有 VIA 檔案，不寫 SSOT，不建立資料庫，不安裝 Manus connector，也不自動登錄 Manus／VCGC。請把所有 `<請替換>` 文字換成你實際知道的路徑；不要猜測客戶端的 GUI 選單或設定檔位置。

## 1. 固定版本、傳輸與安全邊界

本指南與另附smoke helper的版本是v0105.2；原ZIP及MCP adapter維持v0105，serverInfo.version為`0.1.5`。本文件沒有升級或覆寫該adapter。

本次使用的 immutable ZIP 是：

```text
/home/ubuntu/VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip
SHA-256: bf5ac1a16667e2a2f9c8928a2102d6ca191dea07caab5e888f3eb16a596d6be2
```

Windows 上請把同一個 ZIP 與其側檔放在你可讀取的位置，例如 `Downloads`。ZIP 側檔名稱應為：

```text
VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip.sha256
```

這個版本的 server 是一個有限的 **stdio、newline-delimited JSON-RPC 2.0** 程序：

- 沒有 HTTP URL、SSE URL、port 或 localhost endpoint；不要在 client 填 URL。
- 沒有 OAuth、網路、provider call 或遠端註冊。
- 實作的是 MCP `2025-06-18` 的有限子集，不宣稱 full conformance。
- `tools/list` 必須只列出這三個工具，且順序固定：`via_status`、`via_inventory_query`、`via_token_prepare`。
- `via_inventory_query` 只讀 caller 指定 package root 下固定的 `data/governance_inventory_v0105.json`，並要求 caller 提供該檔案的**已知、全小寫 SHA-256** 及 package root；不掃描整個 Windows 磁碟，也不讀任意檔名。
- `via_token_prepare` 只處理 caller 提供的非敏感文字，最多 1 MiB UTF-8；結果是本機 heuristic，不是 provider tokenizer、帳單或 token 節省承諾。
- 候選狀態不是正式上線：`formal_registration=false`、`production_deployment=false`，且不會自動 SSOT／Manus connector registration。

## 2. Windows 先決條件（一般使用者權限）

### 2.1 Python launcher 與版本

只使用 Python 標準庫；**不要以系統管理員身分執行，也不要做廣泛的 `pip install`**。現行 source 使用 Python 3.10 起的語法／型別標註（包括現代 annotation 形式），因此建議使用 **Python >= 3.10**。`py.exe` launcher 必須可以找到同一個 Python 3.x。

在一般 PowerShell 視窗執行：

```powershell
$ErrorActionPreference = 'Stop'
$Py = (Get-Command py.exe -ErrorAction Stop).Source
& $Py -3 --version
if ($LASTEXITCODE -ne 0) { throw "STOP: py -3 failed" }
& $Py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "STOP: Python 3.10 or newer is required" }
"Python launcher: $Py"
```

若 `Get-Command` 找不到 `py.exe`，請依組織允許的 Python 安裝流程安裝含 Python Launcher 的 Python >= 3.10，關閉並重新開啟 PowerShell 後再檢查。不要為了此候選包自行安裝一整套 pip 套件。

### 2.2 既有 VIA root 必須已存在

stager 只接受**已存在的既有 VIA owner root**；它不會替你建立正式 root。請把下列路徑替換成你已確認存在的資料夾，不要把它改成 Windows 磁碟根、`Downloads` 或任意新資料夾：

下例使用您先前指定的Tony-NB路徑，**尚未由本工作階段在實機核實**。請在本機確認owner與位置；程式若找不到它就STOP，不能自動建立或推論該根已驗證。

```powershell
$Root = 'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics'
if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
  throw "STOP: existing VIA root missing; do not create it automatically: $Root"
}
$Root = (Get-Item -LiteralPath $Root -ErrorAction Stop).FullName
"Existing VIA root: $Root"
```

不要刪除或搬移該 root 內的既有 VCGC、VDF、VRN、VQG、VAP、Database、registry 或其他 owner 檔案。候選包的 policy 是 `EXISTING_PLUS_NEW_ATLAS_AND_LOCAL_TOOLS`，不是 replace-existing。

## 3. 下載、驗證與唯一安全 staging

### 3.1 先驗證 ZIP 與側檔

以下命令只讀 ZIP／側檔與既有 root；`$ExpectedFixed` 是本版本外部 SHA，不能用未驗證的值替換：

```powershell
$ErrorActionPreference = 'Stop'
$Py = (Get-Command py.exe -ErrorAction Stop).Source
$Zip = Join-Path $env:USERPROFILE 'Downloads\VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip'
$Sidecar = "$Zip.sha256"
$ExpectedFixed = 'bf5ac1a16667e2a2f9c8928a2102d6ca191dea07caab5e888f3eb16a596d6be2'

if (-not (Test-Path -LiteralPath $Zip -PathType Leaf)) { throw "STOP: ZIP missing: $Zip" }
if (-not (Test-Path -LiteralPath $Sidecar -PathType Leaf)) { throw "STOP: SHA sidecar missing: $Sidecar" }

$ExpectedFromSidecar = ((Get-Content -LiteralPath $Sidecar -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
if ($ExpectedFromSidecar -notmatch '^[0-9a-f]{64}$') { throw 'STOP: sidecar does not contain a SHA-256' }
$Actual = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ExpectedFromSidecar -ne $ExpectedFixed -or $Actual -ne $ExpectedFixed) {
  throw "STOP: ZIP SHA mismatch; expected $ExpectedFixed, sidecar $ExpectedFromSidecar, actual $Actual"
}
"ZIP SHA PASS: $Actual"
```

任何 SHA 不一致都要停下；不要解壓、不要執行、不要以另一個 ZIP 取代、不要修改 immutable ZIP 或腳本來繞過檢查。

### 3.2 以唯一 bootstrap 目錄解出 stager

bootstrap 只是從已驗證 ZIP 取得 stager 的暫存位置；它不是正式 VIA root，也不是候選 target。GUID 使每次 staging 都使用新的目錄：

```powershell
$Bootstrap = Join-Path $env:TEMP ('VIA_v0105_bootstrap_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Bootstrap -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath $Bootstrap -PathType Container)) { throw 'STOP: bootstrap creation failed' }
Expand-Archive -LiteralPath $Zip -DestinationPath $Bootstrap -ErrorAction Stop
$Stager = Join-Path $Bootstrap 'scripts\stage_governance_addon_v0105.py'
if (-not (Test-Path -LiteralPath $Stager -PathType Leaf)) { throw 'STOP: stager missing from verified archive' }
```

### 3.3 執行精確 stager 參數並檢查最後 exit code

stager 的精確參數只有 `--zip`、`--sha256`、`--root`。不要自行加 `--force`、`--replace`、`--register`、`--server`、`--url` 或任何其他 flag：

```powershell
$StageJson = & $Py -3 -B $Stager --zip $Zip --sha256 $ExpectedFixed --root $Root
$StageExit = $LASTEXITCODE
if ($StageExit -ne 0) { throw "STOP: staging process exit code $StageExit" }
if ([string]::IsNullOrWhiteSpace(($StageJson -join ''))) { throw 'STOP: stager returned no JSON' }
$Stage = ($StageJson -join "`n") | ConvertFrom-Json

if ($Stage.status -ne 'PASS_STAGED_CANDIDATE_ONLY') { throw "STOP: unexpected stage status: $($Stage.status)" }
if ([int]$Stage.commands_executed -ne 0) { throw 'STOP: stager reported command execution' }
if ($Stage.existing_engine_modified -ne $false) { throw 'STOP: existing_engine_modified is not false' }
if ($Stage.formal_registration -ne $false) { throw 'STOP: formal_registration is not false' }
if ($Stage.production_deployment -ne $false) { throw 'STOP: production_deployment is not false' }

$Candidate = [string]$Stage.target
if (-not (Test-Path -LiteralPath $Candidate -PathType Container)) { throw 'STOP: candidate target missing' }
$McpScript = Join-Path $Candidate 'scripts\via_governance_mcp_v0105.py'
if (-not (Test-Path -LiteralPath $McpScript -PathType Leaf)) { throw 'STOP: candidate MCP script missing' }

"Candidate: $Candidate"
"MCP entry point: $McpScript"
```

成功後，保留 PowerShell 印出的實際 `$Candidate`。target 應是類似：

```text
<既有 VIA root>\VIA_Review_Candidates\v0105_<UTC timestamp>Z
```

stager 只會在既有 root 下面新增 `VIA_Review_Candidates` 與一個唯一版本目錄，並把已驗證 ZIP 解出成新的候選副本。它不替換既有檔案、不執行任何 engine、不寫 SSOT、不正式 deploy、不登錄 connector。若 stager 命令失敗或最後 exit code 不是 0，請停止，不要手動複製檔案補洞。

## 4. 先取得 caller 已知的 inventory SHA

`via_inventory_query` 的安全邊界是：**caller 必須同時提供已知的 `package_root` 與該 root 之下固定 inventory 的小寫 SHA-256**。它不是「給一個關鍵字就讓 server 自己找檔案」。在完成 staging 後，以實際 `$Candidate` 為 package root：

```powershell
$Inventory = Join-Path $Candidate 'data\governance_inventory_v0105.json'
if (-not (Test-Path -LiteralPath $Inventory -PathType Leaf)) { throw 'STOP: fixed inventory missing' }
$InventorySha = (Get-FileHash -LiteralPath $Inventory -Algorithm SHA256).Hash.ToLowerInvariant()
if ($InventorySha -notmatch '^[0-9a-f]{64}$') { throw 'STOP: inventory SHA is not lowercase hex' }
$KnownV0105InventorySha = '43c74dbe2b35862d06d507ef27c16cd15502686abeb1bb101362a15632a74754'
if ($InventorySha -ne $KnownV0105InventorySha) { throw "STOP: candidate inventory SHA mismatch: $InventorySha" }
"Inventory SHA PASS: $InventorySha"
```

只把這個已由同一個候選副本計算、且與已知版本一致的 `$InventorySha` 放進 query。不要把整個 `C:\`、user profile、任意報告資料夾或未核對的來源路徑當成 `package_root`；server 只讀固定相對路徑 `data/governance_inventory_v0105.json`。

## 5. 精確 stdio 啟動與生命週期

### 5.1 手動 PowerShell 啟動

先重新確認 launcher 的實際位置，再以精確 entry point 啟動：

```powershell
$Py = (Get-Command py.exe -ErrorAction Stop).Source
& $Py -3 -B $McpScript
$McpExit = $LASTEXITCODE
if ($McpExit -ne 0) { throw "STOP: MCP process exit code $McpExit" }
```

這個程序是 stdio server，不是互動式 PowerShell 命令列。啟動後若還沒有 client 寫入 stdin，它**等待輸入是正確行為，不是 hang**；client 寫入一行 JSON-RPC 後才會有對應 response。不要以為沒有 URL 就是失敗，也不要對它使用瀏覽器或 `curl`。沒有輸入而一直等待時，請使用 client 或有限 smoke helper 送入測試訊息並關閉 stdin；不要添加任意 flags。

server 的每一行 stdout 都必須是 UTF-8 JSON-RPC response；不要在同一個 stdout pipe 加 `Write-Host`、banner、debug text 或 wrapper 訊息。診斷文字只能留在 stderr。server 收到 EOF 會正常結束，正常 exit code 為 0。

### 5.2 必須遵守的 initialized lifecycle

MCP client 必須按下列順序送訊息；第二行是 notification，因此不會有 response：

1. `initialize` request：`protocolVersion` 使用 `2025-06-18`，`capabilities` 為 object，`clientInfo.name` 和 `clientInfo.version` 都是字串。
2. `notifications/initialized` notification。
3. `tools/list` request。
4. 依需要呼叫三個 allowlisted tools。
5. client 關閉時送 EOF；一次性 smoke test 必須在有限時間內收到 response 並正常退出。

若跳過第 2 步，`tools/list` 和 `tools/call` 會被拒絕；不要把「server 沒輸出」誤判為工具不存在。

### 5.3 `tools/list` 的精確結果

初始化成功後，`tools/list` 必須只得到以下三個工具，順序也應保持一致：

```text
via_status
via_inventory_query
via_token_prepare
```

三個工具都是 read-only candidate annotations：`readOnlyHint=true`、`destructiveHint=false`、`openWorldHint=false`、`idempotentHint=true`。不要期待 resources、prompts、sampling、HTTP 或 OAuth capability。

### 5.4 `via_status` 應檢查的旗標

先呼叫無參數 `via_status`。至少應看到：

```text
status                       = CANDIDATE_ONLY
registration_status          = CANDIDATE_NOT_REGISTERED
registration_performed      = false
manus_connector_installed   = false
vcgc_host_or_client_registered = false
transport                    = stdio
network_access               = false
provider_calls              = 0
repository_writes           = false
formal_status               = REQUIRES_REAL_ENDPOINT_AND_OWNER_APPROVAL
```

另外，`full_conformance`、`latest_alias_supported`、`http_supported`、`oauth_supported`、`sampling_supported`、`resources_supported`、`prompts_supported` 都應是 false。這些旗標是範圍限制，不是缺少設定；不要以註冊或網路化方式「修正」它們。

### 5.5 一個有限的 inventory query

下列是通用 JSON-RPC request 的內容形狀；實際 client 可能把它包在自己的 message API 中。`package_root` 必須是 `$Candidate`，`inventory_sha` 必須是上一節由 caller 計算的全小寫值；`limit=1` 是有限樣本：

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "via_inventory_query",
    "arguments": {
      "package_root": "C:\\<既有 VIA root>\\VIA_Review_Candidates\\v0105_<UTC timestamp>",
      "inventory_sha": "43c74dbe2b35862d06d507ef27c16cd15502686abeb1bb101362a15632a74754",
      "query": "VIA",
      "offset": 0,
      "limit": 1
    }
  }
}
```

預期結果會標記：`source=data/governance_inventory_v0105.json`、`source_sha256` 等於 caller 提供的 SHA、`evidence_scope=LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE`、`registration_status=CANDIDATE_NOT_REGISTERED`。它只回傳最多一列；不要把完整 inventory 或整個磁碟內容送進 request。

### 5.6 一個安全的 token_prepare sample

只用明確非敏感的測試字串；不要貼入 token、密碼、API key、客戶資料、真實報告或機密路徑：

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "via_token_prepare",
    "arguments": {
      "text": "{\"smoke\":\"v0105\",\"scope\":\"local-candidate\",\"contains_sensitive_data\":false}",
      "allow_lossy": false,
      "max_lines": 20
    }
  }
}
```

結果應顯示 pinned engine source／SHA、`execution_scope=LOCAL_PINNED_ENGINE_ONLY`、`content_persisted=false`、`provider_calls=0`。請比較 **provider calls 是否為 0**；不要把 heuristic measurement 宣稱成 provider tokenizer 或費用節省。

## 6. 通用 client 設定形狀（不猜 GUI）

不同 MCP client 的設定檔名稱、位置、重新載入方式及 GUI 都不同。請依你正在使用的 client 官方文件找到**已知的現有設定檔**；本指南不猜測選單名稱，也不建議任意建立未知設定檔。

### 6.1 先備份並保留既有設定

把下面路徑替換成你已確認的 client 設定檔，並用 GUID 產生不重複的備份名。若不知道設定檔在哪裡，停下並查該 client 文件，不要用全碟搜尋或覆蓋檔案：

```powershell
$ClientConfig = 'C:\<你已確認的 client 設定檔路徑>\config.json'
if (Test-Path -LiteralPath $ClientConfig -PathType Leaf) {
  $Backup = "$ClientConfig.bak.$([guid]::NewGuid().ToString('N'))"
  if (Test-Path -LiteralPath $Backup) { throw "STOP: backup unexpectedly exists: $Backup" }
  Copy-Item -LiteralPath $ClientConfig -Destination $Backup -ErrorAction Stop
  "Config backup: $Backup"
  Get-Content -LiteralPath $ClientConfig -Raw
} else {
  throw 'STOP: existing client config not found; do not guess its location or overwrite a new file'
}
```

只在原有 JSON 中合併新增一個 `mcpServers` entry，保留所有既有 key、server、權限與格式；不要把下面 snippet 整份寫回而抹掉原設定，也不要以 PowerShell `Set-Content` 盲目重建檔案。修改後先用 client 自己的 JSON validation／reload 流程，並保留 backup 以便復原。

### 6.2 generic stdio snippet

以下只表示常見的設定**形狀**，不保證每個 client 的 schema、根鍵或 reload 行為；請以該 client 文件為準。把 `command` 換成前面 `(Get-Command py.exe).Source` 實際印出的完整路徑，把 args 中的 candidate 路徑換成實際 `$McpScript`，並依 JSON 規則把反斜線寫成 `\\`：

```json
{
  "mcpServers": {
    "via-governance-mcp-candidate": {
      "command": "C:\\<Get-Command py.exe 實際回傳的完整路徑>\\py.exe",
      "args": [
        "-3",
        "-B",
        "C:\\<既有 VIA root>\\VIA_Review_Candidates\\v0105_<UTC timestamp>\\scripts\\via_governance_mcp_v0105.py"
      ]
    }
  }
}
```

這裡故意沒有 `url`、`port`、`env`、proxy 或自訂 server flag。client 應直接啟動同一台 Windows 電腦上的 stdio process；它不會因為這個本機 process 運作，就自動讓 Manus Sandbox 看見，也不會自動註冊到 Manus 雲端。若某 client 只能接受 URL／HTTP endpoint，請停下；不要填 `localhost`、不要綁 `0.0.0.0`、不要臨時安裝 proxy。

## 7. 有限 cross-platform smoke helper

本專案另有隔離 helper：

```text
scripts/mcp_stdio_smoke_v0105_2.py
```

它的行為限制如下：

- 只接受 caller 指定的**絕對 package root**，只讀固定且 hash-pinned 的 MCP script、TokenEngine、inventory 三個檔案。
- 以目前同一個 Python 執行 `-B scripts/via_governance_mcp_v0105.py`，`shell=False`，不加 server 任意 flag。
- 寫入 `initialize`、`notifications/initialized`、`tools/list`、`via_status`、一個 `limit=1` 的 inventory query、一個非敏感 token sample，然後送 EOF。
- 有固定 30 秒 process timeout；captures stdout/stderr，不把 child stdout 轉發成 banner。
- 驗證沒有 JSON-RPC error、三個工具 exact match、候選旗標、inventory caller SHA、token engine SHA、`provider_calls=0`、registration flags clear、EOF clean exit。
- `--out` 是 create-once；若檔案已存在，拒絕覆寫。它不做 shell action、不掃描整個 Windows filesystem、不寫 package 內容、不做 connector registration。

這個 v0105.2 helper 是另附的新檔，**不在原不可變v0105 ZIP裡**。請下載本次提供的 `mcp_stdio_smoke_v0105_2.py` 至您選擇的工具／Downloads資料夾，或從同一份專案 checkout 取得它；不要為了加入helper重打包或改原ZIP。`$Candidate` 仍是第3節stager回傳的候選root：

```powershell
$Helper = Join-Path $env:USERPROFILE 'Downloads\mcp_stdio_smoke_v0105_2.py'
$Out = 'C:\<你指定的輸出資料夾>\mcp_stdio_smoke_v0105_2_receipt.json'
& $Py -3 -B $Helper --package-root $Candidate --out $Out
if ($LASTEXITCODE -ne 0) { throw "STOP: smoke helper exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $Out -PathType Leaf)) { throw 'STOP: smoke receipt missing' }
Get-Content -LiteralPath $Out -Raw
```

如果要重跑，必須指定新的不存在的 `--out`；不要刪除舊 receipt 來掩蓋結果。client 的手動 stdio 連線與 smoke helper 是兩條分開的路徑；helper PASS 也不等於正式註冊或 Windows production deployment。

## 8. 本次 Sandbox smoke scope 與 receipt

已在目前 Sandbox 以現行 package root 執行的命令是：

```text
python3 -B /home/ubuntu/viaatlas/scripts/mcp_stdio_smoke_v0105_2.py \
  --package-root /home/ubuntu/viaatlas \
  --out /home/ubuntu/viaatlas/artifacts/mcp_stdio_smoke_v0105_2_receipt.json
```

receipt 應明確包含 `scope=Sandbox`、`windows_compatibility=NOT_RUN`，以及以下 pinned SHA：

```text
MCP script: 901b91eb4add9db2c19f5a62e6ea291caa6a681294148fc6ca7ebc14a349225a
TokenEngine: ca3c38ee00d2d7df5af71bcaea59ab7e7c73a15ec1d1f7b03218127efaf62af5
Inventory: 43c74dbe2b35862d06d507ef27c16cd15502686abeb1bb101362a15632a74754
```

這個 Linux/Sandbox smoke 只證明該有限 stdio session 在該環境完成 initialized lifecycle、工具與固定檔案 hash 驗證；它**不證明 Windows 成功**，也不證明 Manus connector、VCGC、正式 endpoint 或 production deployment。

## 9. 故障排除與停損規則

### `py.exe` 找不到或版本太舊

先重開 PowerShell，再用 `Get-Command py.exe -ErrorAction Stop` 和 `py -3 --version` 檢查。沒有 Python Launcher 或低於 3.10 就停止並走受控安裝流程；不要用廣泛 pip 安裝、不要以管理員權限執行、不要猜一個 `python.exe` 路徑。

### ZIP／sidecar／inventory SHA mismatch

停止 staging。重新取得原 ZIP 與 sidecar，確認實際 SHA 必須等於本文件固定值；不要以另一份下載物、修改後腳本、解壓後手動替換檔案或改 helper 常數來繞過檢查。stager 與 helper 都是 fail-closed。

### 路徑含空格、中文或反斜線出錯

PowerShell 原生執行使用 `& $Py ...`，路徑以變數傳入；檔案檢查使用 `-LiteralPath`。不要在沒有引號的字串中拼接路徑。JSON 設定內的 Windows `\` 必須寫成 `\\`，並且只能貼入實際 `$Candidate`／`$McpScript`，不要照抄 `<UTC timestamp>`。

### stdout 出現 banner、不是 JSON，或 client 顯示 parse error

MCP child stdout 必須只有 newline-delimited JSON-RPC response。不要在同一 pipe 混入 `Write-Host`、啟動 banner、debug print、shell wrapper 輸出或 Python traceback；把診斷放到 stderr。使用絕對 `py.exe` command 加 `-3 -B` 與原始 script，不要加任意 server flags。helper 會把 banner／空行視為失敗。

### 程序停著不動

若尚未送 stdin，stdio server 等待輸入是正確行為，不是 hang；它不是 URL server，也不會自行輸出 heartbeat。真正的有限測試應完成 initialize、送 `notifications/initialized`、送 requests，最後關閉 stdin；helper 在 30 秒後仍未退出就 FAIL。不要用 `--daemon`、`--listen`、`--url`、proxy 或任意 flags 讓它看似有輸出。

### tools 被拒絕或 `initialize is required`

檢查是否先收到 `initialize` response，再送沒有 id 的 `notifications/initialized`，最後才送 `tools/list`／`tools/call`。notification 不應期待 response；不要省略 clientInfo、capabilities 或 protocolVersion。

### client 只接受 URL

這個 candidate 沒有 URL、port、HTTP、SSE、OAuth 或 localhost bridge。不要填假 URL、不要綁 `0.0.0.0`、不要臨時安裝未驗證 proxy；改用支援 command/stdin/stdout 的 client，或停止並另行設計受控 endpoint。

### `via_inventory_query` 失敗

確認 `package_root` 是實際候選 target（不是既有 root 的 parent，也不是全碟路徑），固定檔案確實存在，並重新以 `Get-FileHash` 取得全小寫 SHA。query 必須只使用允許的 filter／offset／limit；`limit` 不可大於 50，smoke 使用 1。不要改用 arbitrary filename。

### Windows 的 `via_token_prepare` 失敗、可能與 UTF-8／SystemRoot 有關

helper 的外層 subprocess 會保留 caller environment，並只記錄有限診斷（Python/platform、`SystemRoot` 是否存在、UTF-8 environment 是否設定），不傾印整個環境。現行 MCP script 內部啟動 TokenEngine 時使用它自己明確的 UTF-8／`LC_ALL` 子程序環境，沒有宣稱 Windows `SystemRoot` 相容性已驗證。Sandbox/Linux smoke 的 PASS **不證明 Windows token subprocess 成功**；若 Windows 的 `via_token_prepare` 失敗，請保留 receipt 與 stderr，標示 Windows compatibility NOT_RUN／未通過，交由 owner 另行修正與審查。不要修改 immutable 舊 script、不要用廣泛環境注入、不要以 provider call 或 token savings 聲稱成功。

### client 設定被覆蓋或無法載入

停止使用該設定檔，先以第 6 節備份復原。永遠保留既有 `mcpServers` entries，只合併一個新 candidate entry；不要把 generic snippet 當成可直接覆蓋整份 config 的檔案，也不要猜測 GUI reload 選單。

## 10. 完成判定

只有在以下全部成立時，才可說「本機候選 stdio smoke 通過」：

- ZIP 外部 SHA 通過，stager exit code 為 0，且 `PASS_STAGED_CANDIDATE_ONLY`／`commands_executed=0`。
- `$Candidate` 是既有 root 下唯一的新候選目錄；既有 owner 檔案沒有被替換。
- client 完成 `initialize` → `notifications/initialized` → `tools/list` 的生命週期。
- 工具 exact 3；`via_status` 顯示 candidate-only、stdio、network false、registration false、provider_calls 0。
- bounded inventory query 使用 caller 已知的小寫 SHA 與正確 package root。
- token sample 只用非敏感文字，`provider_calls=0`、`content_persisted=false`，且 pinned engine SHA 通過。
- stdout 無 banner／非 JSON；EOF 後程序在有限時間內以 0 結束。
- client 設定已先備份、既有 entries 保留，且沒有填 URL 或自動註冊。

這些條件仍然只代表 local candidate evidence；它們不等於 Windows 已在 Tony-NB 執行、不等於正式 Manus connector、不等於 VCGC registration，也不等於 production deployment。
