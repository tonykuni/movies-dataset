# VIA Governance MCP v0105 — Windows 手動接入

## 目前狀態

2026-11-06 11:33 的裝置刷新結果：Tony-NB `unavailable`、`switchable=false`、`workspaces=[]`。Manus 本工作階段的使用者自有 connector 清單為 0，搜尋 `PC`／`MCP` 均無匹配。故這是候選版的手動接入指引，**不是已在 Tony-NB 安裝、啟動或註冊的結果**。

本 server 是有限 **stdio JSON-RPC** 程序，不是 HTTP/SSE 服務：

- HTTP URL：**沒有**。
- Port：**不監聽**。
- OAuth／網路／provider：無。
- 開發版本：MCP 2025-06-18 子集，不宣稱完整規格符合性。
- 工具：`via_status`、`via_inventory_query`、`via_token_prepare`。
- Token tool 對文字有1MiB限制、預設保留模式；估算為heuristic，不是帳單或provider tokenizer。呼叫者不可提供敏感文字。
- `via_inventory_query` 僅讀固定inventory並要求資料夾及inventory SHA；只提供本機候選證據，不含Manus UI supplemental merge。

由於它僅限stdio，如MCP客戶端只接受URL，這個server不能直接接入。不要改用未驗證的 `localhost` URL，也不要把服務綁到 `0.0.0.0`；網路化需另行設計受控authenticated endpoint，這份候選包沒有HTTP bridge。

## 候選 ZIP

下載：[VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip](/home/ubuntu/VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip)

外部SHA-256：`bf5ac1a16667e2a2f9c8928a2102d6ca191dea07caab5e888f3eb16a596d6be2`。

SHA側檔：[VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip.sha256](/home/ubuntu/VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip.sha256)。

此 ZIP 有44個明確allowlist payload，已完成外部SHA、CRC、manifest/SHA及clean-extract驗證。範圍是治理頁／候選工具和證據，不是五個production engine、VDF資料庫或整套VIA部署。`formal_registration=false`，`production_deployment=false`。

## 在 Tony-NB 手動staging

先把 ZIP 和 `.sha256` 側檔下載到 `Downloads`。使用一般PowerShell，不開管理員權限；這些命令不啟動任何引擎：

```powershell
$ErrorActionPreference = 'Stop'
$Zip = Join-Path $env:USERPROFILE 'Downloads\VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip'
$Sidecar = "$Zip.sha256"
$Expected = ((Get-Content -LiteralPath $Sidecar -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$Actual = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Actual -ne $Expected -or $Expected -ne 'bf5ac1a16667e2a2f9c8928a2102d6ca191dea07caab5e888f3eb16a596d6be2') { throw 'STOP: ZIP SHA mismatch' }

$Root = 'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics'
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'STOP: existing VIA root missing; do not create it automatically' }

# Extract the externally-hash-verified archive into a unique temporary bootstrap directory.
$Bootstrap = Join-Path $env:TEMP ('VIA_v0105_bootstrap_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Bootstrap | Out-Null
Expand-Archive -LiteralPath $Zip -DestinationPath $Bootstrap
$Stager = Join-Path $Bootstrap 'scripts\stage_governance_addon_v0105.py'

# The stager verifies the same external SHA, exact members, CRC, Windows-safe paths,
# manifest/checksums and false deployment flags, then creates a new versioned candidate only.
$StageJson = py -3 -B $Stager --zip $Zip --sha256 $Expected --root $Root
$Stage = $StageJson | ConvertFrom-Json
if ($Stage.status -ne 'PASS_STAGED_CANDIDATE_ONLY' -or $Stage.commands_executed -ne 0) { throw 'STOP: candidate stage did not pass' }
$Candidate = $Stage.target
$McpScript = Join-Path $Candidate 'scripts\via_governance_mcp_v0105.py'
if (-not (Test-Path -LiteralPath $McpScript -PathType Leaf)) { throw 'STOP: candidate MCP script missing' }
"Staged candidate: $Candidate"
"MCP entry point: $McpScript"
```

請保留PowerShell回傳的實際 `Candidate` 路徑；stager使用UTC時間建立唯一目錄。staging只解出**新候選副本**到 `VIA_Review_Candidates`，不替換既有VCGC、VDF、VRN、VQG、VAP或Database檔案，不建正式root，不寫SSOT，也不執行engine。

## MCP客戶端使用stdio

先在PowerShell確認Python launcher位置：

```powershell
(Get-Command py.exe -ErrorAction Stop).Source
```

在您使用的MCP客戶端設定檔中，新增同一個server的stdio設定。把`C:\...\v0105_<timestamp>...`換成上一步實際回傳的候選路徑；若客戶端需要絕對命令路徑，將`command`設成剛查到的 `py.exe` 完整路徑：

```json
{
  "mcpServers": {
    "via-governance-mcp-candidate": {
      "command": "py",
      "args": [
        "-3",
        "-B",
        "C:\\Users\\tonyk\\OneDrive\\Documents\\VeritasIntelligenceAnalytics\\VIA_Review_Candidates\\v0105_<UTC_TIMESTAMP>\\scripts\\via_governance_mcp_v0105.py"
      ]
    }
  }
}
```

客戶端會啟動並用stdin/stdout交換newline-delimited JSON-RPC；不要用瀏覽器或 `curl` 對它呼叫，也不要在MCP客戶端中填URL。若主機只能輸入HTTP endpoint，請停下，不要臨時安裝proxy。

接入後先呼叫 `via_status`，必須看到 `CANDIDATE_ONLY`、`network_access=false`、`registration_performed=false`。如測 `via_inventory_query`，只用stager回報之 `$Candidate` 路徑和候選package固定inventory的SHA；不要把整個Windows磁碟路徑或敏感資料塞入tool。此步驟不連VCGC endpoint、不建立資料庫、不讀取 `C:\測試樣本報告`，也不會把本機MCP自動註冊到Manus雲端。

## 為什麼這不是Manus PC connector

本機 stdio command 是「執行MCP客戶端所在電腦上的程序」。它只能在配置此client的本機上下文內可用；它不會因為Tony-NB本機程序運行而自動被Manus Sandbox看見。本次Manus遠端裝置工具目前回報Tony-NB不可用，沒有可切換workspace，且Manus connector清單為空。因此目前只能由您手動接入合適的本機MCP客戶端；Manus雲端不能直接操作該stdio程序。
