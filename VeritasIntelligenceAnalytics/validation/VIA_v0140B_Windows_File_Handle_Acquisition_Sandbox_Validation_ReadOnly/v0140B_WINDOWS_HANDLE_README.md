# VIA v0140B Windows File Handle Acquisition Sandbox Validation — Read Only

本包是上一階段 `builtin:binary_open` 在 CSV parsing 前發生 `OSError: [Errno 22] Invalid argument` 後的下一個唯讀驗證閘門。它不套用 reader patch；只回答：在不觸發 OneDrive 隱式 hydration、不保存來源內容的前提下，哪一種 Windows handle strategy 能取得有限的來源位元組。

## 核心結論與邊界

- 六引擎以 **PowerShell 7 啟動的六個獨立 Python 程序，嚴格循序執行**；同時內容 open 上限為 1。
- H01 只讀 metadata 與 Windows file attributes。若偵測 `OFFLINE`、`RECALL_ON_OPEN` 或 `RECALL_ON_DATA_ACCESS`，H02–H06 全數跳過，gate 為 hydration-risk HOLD。
- H02–H06 各最多一次 bounded read，單一成功探針最多讀取 65,536 bytes 到記憶體。
- 指標分為 `source_open_attempts`、`source_open_successes`、`source_bytes_read`；失敗的 open 不再被記成內容讀取。
- 來源 hash／write／copy／rename／delete、來源內容 artifact、network、canonical runtime、registry、patch、promotion 全為 0。
- VRN、VDF、VAP 只建立 handle strategy 的靜態適用性矩陣（6 × 3 = 18 rows），不執行任何正式 subsystem runtime。

## 六個獨立引擎

| 順序 | 引擎 | Handle strategy | 來源 open 上限 |
|---:|---|---|---:|
| 1 | H01 | OneDrive / Windows attribute recall preflight | 0 |
| 2 | H02 | Python `pathlib.Path.open("rb")` | 1 |
| 3 | H03 | Python `os.open(..., O_RDONLY | O_BINARY)` | 1 |
| 4 | H04 | Win32 `CreateFileW` exact path | 1 |
| 5 | H05 | Win32 `CreateFileW` extended-length path | 1 |
| 6 | H06 | .NET `FileStream` exact path | 1 |

H04／H05 使用 read access、`FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE`、`OPEN_EXISTING`、`FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN`。H06 使用 `FileMode.Open`、`FileAccess.Read` 與同等 share mask。

## 執行前條件

1. Windows 與 PowerShell 7 (`pwsh`)。
2. 上一階段已存在 accepted predecessor gate：
   `VIA_V0140B_CROSS_SUBSYSTEM_SIX_ENGINE_LOCAL_READER_PATH_REPAIR_PROPOSAL_PASS_READY_NO_SYSTEM_MUTATION`。
3. governed Python 路徑存在，且具備 `pyarrow`，用於 CSV／Parquet 配對證據。
4. 使用者明確提供 approval token：
   `VIA_APPROVE_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_READ_ONLY`。

## 一段 PowerShell 7 直接執行

先將 ZIP 解壓至任意唯讀驗證目錄，再在 PowerShell 7 貼上：

```powershell
$PackageRoot = (Resolve-Path ".\VIA_v0140B_Windows_File_Handle_Acquisition_Sandbox_Validation_ReadOnly").Path
& (Join-Path $PackageRoot "Invoke-VIA-v0140B-Windows-File-Handle-Acquisition-Sandbox-Validation-ReadOnly.ps1") `
  -PackageRoot $PackageRoot `
  -ApprovalToken "VIA_APPROVE_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_READ_ONLY" `
  -SourceCandidatePath (Join-Path $env:USERPROFILE "OneDrive\桌面\tw_stock\Standardized_Prices.csv") `
  -MaximumParallelContentOpens 1 `
  -RunOfflineSelfTest $true `
  -OpenHtml $true
```

若資料根目錄、governed Python 或 predecessor 位置不同，另外傳入 `-MotherRoot`、`-GovernedPythonPath` 或 `-PredecessorRunDir`。launcher 不關閉 PowerShell 視窗。

## Gate 解讀

| Gate | 判定 | 下一步 |
|---|---|---|
| `...PASS_HANDLE_EVIDENCE_READY_NO_SYSTEM_MUTATION` | 至少一種 strategy 成功且讀得 bytes；Hydra 0 | 才可提議下一個 sequential reader-path patch sandbox validation |
| `...HOLD_ALL_HANDLE_STRATEGIES_FAILED_NO_SYSTEM_MUTATION` | H01 安全，但所有可用 strategy 均未讀得 bytes | 人工比較 errno／winerror／runtime 邊界 |
| `...HOLD_IMPLICIT_HYDRATION_RISK_NO_SYSTEM_MUTATION` | H01 偵測 recall/offline risk | 人工檢視 OneDrive placeholder/reparse 狀態；本包不 hydrate 或 pin |
| `...HOLD_FAIL_CLOSED` | 身分、順序、唯一 ownership、zero-effect 或證據完整性失敗 | 只修復 run-local/package 證據後重跑 |

PASS 只代表「已取得安全、有限、非持久化的 handle evidence」，不代表 CSV schema 有效，也不授權套用 patch 或執行 canonical runtime。

## 主要輸出

- `VIA_v0140B_WindowsHandle_Summary.json`
- `VIA_v0140B_WINDOWS_HANDLE_FORMAL_RECORD.json`
- `VIA_v0140B_WindowsHandle_EngineMatrix.csv/.parquet`
- `VIA_v0140B_WindowsHandle_CrossSubsystemMatrix.csv/.parquet`
- `VIA_v0140B_WindowsHandle_Findings.csv`
- `VIA_v0140B_WindowsHandle_SequenceLedger.csv`
- `VIA_v0140B_WindowsHandle_Report.html`
- 每一 lane 的 `TERMINAL_SUMMARY.json`、evidence、findings 與 subsystem matrix

## 離線套件驗證

```powershell
$env:VIA_ALLOW_PARQUET_UNAVAILABLE_FOR_PACKAGE_TEST = "1"
python -m unittest discover -s tests -v
```

此 fallback 只供不具 `pyarrow` 的 package test；正式執行仍要求 governed PyArrow 產生配對 Parquet。
