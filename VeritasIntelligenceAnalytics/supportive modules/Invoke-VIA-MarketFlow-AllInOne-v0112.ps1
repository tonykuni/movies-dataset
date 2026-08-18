#requires -Version 7.0
<#
================================================================================
def VIA · MARKETFLOW + VDF/VRN ALL-IN-ONE · v0112
================================================================================
def Scope
  Authority overlay + 15 accelerators + three-round panoramic validation
  + incremental yfinance/TW official intake + DuckDB/Parquet/CSV
  + ETF/cross-asset proxy signals + VDF/VRN run-local startup validation
  + localhost API + real-data HTML dashboard.

def Safety
  Run-local evidence, append-only data snapshots, no canonical overwrite,
  no dot-source, no canonical Runtime Bridge activation.
  All seven supportive core modules are mapped and imported only inside the
  isolated run directory. VDF/VRN are fail-closed unless every import succeeds.

def Accuracy
  Dollar volume, price-volume divergence and relative strength are proxies.
  Precise ETF net flow is emitted only when AUM/shares evidence exists.
  Empty union-calendar placeholder rows are quarantined from analytical tables.
  Signal calendars use SPY sessions; Taiwan and US/global as-of dates remain separate.
  Historical-only tickers never appear in the current Taiwan market table.
#>

[CmdletBinding()]
param(
    [string]$VIA_BaseDir = (Join-Path $env:USERPROFILE "Downloads\VeritasIntelligenceAnalytics"),
    [string]$StartDate = "2018-01-02",
    [string]$EndDate = "",
    [int]$ApiPort = 8765,
    [int]$BatchSize = 40,
    [int]$MaxWorkers = 6,
    [int]$RequestTimeoutSec = 30,
    [bool]$InstallMissingPackages = $true,
    [bool]$FetchMarketData = $true,
    [bool]$FetchTaiwanOfficial = $true,
    [bool]$OpenDashboard = $true,
    [bool]$ValidateVdfVrnRuntime = $true,
    [string]$TickerListPath = "",
    [string]$StockDatabasePath = "",
    [string]$DashboardSourcePath = "",
    [string]$LogoSourcePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$SCRIPT_VERSION = "v0112"
$SCRIPT_NAME = "VIA_MARKETFLOW_ALL_IN_ONE"
$LOOPBACK_HOST = "127.0.0.1"
$REQUIRED_PACKAGES = @(
    "numpy", "pandas", "yfinance", "duckdb", "pyarrow",
    "requests", "fastapi", "uvicorn"
)
$CORE_AUTHORITY_FILES = @(
    "VIA_Panorama_AST_RuntimeInjector.py",
    "VIA_Runtime_Bridge_All_in_One.py",
    "VIA_SSOT_Unified.py",
    "VIA_EnvManager.py",
    "VeritasAegisNexus.py",
    "VIA_RegistryCore_v1.py",
    "VeritasCeleritas.py"
)
$AUTHORITY_ACCEPTED = [ordered]@{
    "Invoke-VAP-Panorama-Maturity-Refresh.ps1" = "supportive modules/audit_tools/Invoke-VAP-Panorama-Maturity-Refresh.ps1"
    "Invoke-VIA-ActivationGateway-Hardened.ps1" = "supportive modules/audit_tools/Invoke-VIA-ActivationGateway-Hardened.ps1"
    "Invoke-VIA-ActivationGateway-InlineReady.ps1" = "supportive modules/audit_tools/Invoke-VIA-ActivationGateway-InlineReady.ps1"
    "Invoke-VIA-ActivationGateway-Stable.ps1" = "supportive modules/audit_tools/Invoke-VIA-ActivationGateway-Stable.ps1"
    "Invoke-VIA-ALL.ps1" = "supportive modules/60_PowerShell_Entry_Internal/Invoke-VIA-ALL.ps1"
    "Invoke-VIA-UnifiedInputGateway.ps1" = "supportive modules/ssot/Invoke-VIA-UnifiedInputGateway.ps1"
    "SUP_MDL557_PanoramaMaturityOptimizer.py" = "supportive modules/audit_tools/SUP_MDL557_PanoramaMaturityOptimizer.py"
    "SUP_MDL730_WarehouseV5Next3Builder.py" = "supportive modules/ui_support/SUP_MDL730_WarehouseV5Next3Builder.py"
    "VIA_ActivationGateway_Manifest.json" = "supportive modules/registry/VIA_ActivationGateway_Manifest.json"
}
$AUTHORITY_EXCLUDED = [ordered]@{
    "VIA_LocalFreeLibs_Top10_ByFunction_ByLanguage.json" = "NONBLOCKING_UNOWNED_LEGACY_REGISTRY"
}
$ACCELERATORS = @(
    "A01_SHORT_PATH_RUNTIME",
    "A02_VENDOR_CACHE_SKIP",
    "A03_SUFFIX_PREFILTER",
    "A04_KEYWORD_PRIORITY",
    "A05_SHA256_INCREMENTAL",
    "A06_SIZE_GATE",
    "A07_ENCODING_LADDER",
    "A08_AST_NO_IMPORT",
    "A09_JSON_FLATTEN",
    "A10_PARQUET_PARTITION",
    "A11_RESUME_MAX_DATE",
    "A12_HEARTBEAT_JSON",
    "A13_HTML_MATRIX",
    "A14_VENV_SAFE_SCAN",
    "A15_BATCHED_NETWORK_RETRY"
)

function def_WriteBanner {
    param([Parameter(Mandatory)][string]$Title)
    Write-Host ""
    Write-Host ("=" * 96) -ForegroundColor DarkCyan
    Write-Host "def $Title" -ForegroundColor Cyan
    Write-Host ("=" * 96) -ForegroundColor DarkCyan
}

function def_WriteProgress {
    param(
        [Parameter(Mandatory)][int]$Step,
        [Parameter(Mandatory)][int]$Total,
        [Parameter(Mandatory)][string]$Message
    )
    $Pct = [Math]::Min(100, [Math]::Round(($Step / [double]$Total) * 100))
    $Filled = [Math]::Floor($Pct / 5)
    $Bar = ("█" * $Filled) + ("░" * (20 - $Filled))
    Write-Host ("[{0,3}%] [{1}] {2}" -f $Pct, $Bar, $Message) -ForegroundColor Cyan
}

function def_NormalizeRuntimeStatus {
    param([AllowNull()][object]$Candidate)

    $Candidates = @($Candidate)
    $Selected = $Candidates |
        Where-Object {
            $null -ne $_ -and
            $null -ne $_.PSObject.Properties["overall_gate"] -and
            $null -ne $_.PSObject.Properties["ready"] -and
            $null -ne $_.PSObject.Properties["vdf"] -and
            $null -ne $_.PSObject.Properties["vrn"]
        } |
        Select-Object -Last 1

    if ($Selected) {
        return $Selected
    }

    return [pscustomobject]@{
        schema = "via.vdf_vrn.runtime.status.v2"
        generated_utc = [DateTime]::UtcNow.ToString("o")
        overall_gate = "VDF_VRN_RUNTIME_STATUS_SCHEMA_INVALID"
        ready = $false
        vdf = [pscustomobject]@{
            status = "BLOCKED"
            gate = "VDF_RUNTIME_STATUS_MISSING"
        }
        vrn = [pscustomobject]@{
            status = "BLOCKED"
            gate = "VRN_RUNTIME_STATUS_MISSING"
        }
        supportive_modules_expected = 7
        supportive_modules_imported = 0
        supportive_modules_all_imported = $false
        candidate_object_count = $Candidates.Count
        canonical_mutation = $false
        canonical_bridge_activation = $false
        run_local_bridge_bootstrap = $false
    }
}

function def_ResolveOptionalFile {
    param(
        [string]$ExplicitPath,
        [string[]]$Candidates
    )
    if ($ExplicitPath -and (Test-Path -LiteralPath $ExplicitPath -PathType Leaf)) {
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }
    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }
    return ""
}

function def_SelectPython {
    $Candidates = @(
        (Join-Path $VIA_BaseDir "envs\via_core_312\Scripts\python.exe"),
        (Join-Path $VIA_BaseDir "envs\via_core\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_core\Scripts\python.exe"),
        "C:\Python313\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }
    foreach ($CommandName in @("python", "py")) {
        $Command = Get-Command $CommandName -ErrorAction SilentlyContinue
        if ($Command) {
            return $Command.Source
        }
    }
    throw "找不到 Python 3.12/3.13。請先安裝 Python，或建立 via_core_312。"
}

function def_GetScriptHash {
    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath -PathType Leaf)) {
        return (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return "PASTED_SESSION_NO_FILE_HASH"
}

function def_TestSelfPowerShellAst {
    if (-not $PSCommandPath -or -not (Test-Path -LiteralPath $PSCommandPath -PathType Leaf)) {
        return [pscustomobject]@{
            Status = "YELLOW_PASTED_SESSION_AST_PATH_UNAVAILABLE"
            ErrorCount = 0
            Path = ""
        }
    }
    $Tokens = $null
    $Errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $PSCommandPath,
        [ref]$Tokens,
        [ref]$Errors
    ) | Out-Null
    if ($Errors.Count -gt 0) {
        $Detail = ($Errors | ForEach-Object { $_.ToString() }) -join " | "
        throw "PowerShell AST fail-closed：$Detail"
    }
    return [pscustomobject]@{
        Status = "GREEN_POWERSHELL_AST_PASS"
        ErrorCount = 0
        Path = $PSCommandPath
    }
}

function def_EnterSingleInstance {
    param([Parameter(Mandatory)][string]$MutexName)
    $CreatedNew = $false
    $Mutex = [System.Threading.Mutex]::new($true, $MutexName, [ref]$CreatedNew)
    if (-not $CreatedNew) {
        $Mutex.Dispose()
        throw "偵測到相同總控器已在執行。依 LL#32 防止 console paste double-execute，已停止第二次執行。"
    }
    return $Mutex
}

function def_ResolveApiPort {
    param(
        [Parameter(Mandatory)][int]$PreferredPort,
        [int]$SearchSpan = 20
    )
    foreach ($CandidatePort in $PreferredPort..($PreferredPort + $SearchSpan)) {
        $Listener = [System.Net.Sockets.TcpListener]::new(
            [System.Net.IPAddress]::Loopback,
            $CandidatePort
        )
        try {
            $Listener.Start()
            return $CandidatePort
        }
        catch {
            continue
        }
        finally {
            try { $Listener.Stop() } catch {}
        }
    }
    throw "找不到可用 localhost API port：$PreferredPort..$($PreferredPort + $SearchSpan)"
}

function def_WriteUtf8NoBom {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )
    [System.IO.File]::WriteAllText(
        $Path,
        $Content,
        [System.Text.UTF8Encoding]::new($false)
    )
}

function def_WriteJson {
    param(
        [Parameter(Mandatory)]$Data,
        [Parameter(Mandatory)][string]$Path,
        [int]$Depth = 20
    )
    $Json = $Data | ConvertTo-Json -Depth $Depth
    def_WriteUtf8NoBom -Path $Path -Content $Json
}

function def_EnsurePackages {
    param(
        [Parameter(Mandatory)][string]$PythonExe,
        [Parameter(Mandatory)][string]$RuntimeRoot
    )
    $VenvDir = Join-Path $RuntimeRoot ".venv"
    $ManagedPython = Join-Path $VenvDir "Scripts\python.exe"
    $ProbePython = if (Test-Path -LiteralPath $ManagedPython -PathType Leaf) {
        $ManagedPython
    }
    else {
        $PythonExe
    }
    $ProbeCode = @'
import importlib.util, json
mods = ["numpy","pandas","yfinance","duckdb","pyarrow","requests","fastapi","uvicorn"]
print(json.dumps({m: bool(importlib.util.find_spec(m)) for m in mods}))
'@
    $Probe = & $ProbePython -c $ProbeCode 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python 套件探測失敗：$($Probe -join ' ')"
    }
    $Status = ($Probe | Select-Object -Last 1) | ConvertFrom-Json
    $Missing = @(
        $REQUIRED_PACKAGES | Where-Object {
            -not [bool]$Status.PSObject.Properties[$_].Value
        }
    )
    if ($Missing.Count -eq 0) {
        $RuntimeType = if ($ProbePython -eq $ManagedPython) { "VIA_MANAGED_VENV_REUSED" } else { "EXISTING" }
        return [pscustomobject]@{ Python = $ProbePython; Installed = @(); Runtime = $RuntimeType }
    }
    if (-not $InstallMissingPackages) {
        throw "缺少 Python 套件：$($Missing -join ', ')；InstallMissingPackages=False，已停止。"
    }
    if (-not (Test-Path -LiteralPath $ManagedPython -PathType Leaf)) {
        New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
        & $PythonExe -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            throw "無法建立 VIA-managed venv：$VenvDir"
        }
    }
    $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
    & $VenvPython -m pip install --disable-pip-version-check --no-input --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "run-local pip 升級失敗。"
    }
    & $VenvPython -m pip install --disable-pip-version-check --no-input @Missing
    if ($LASTEXITCODE -ne 0) {
        throw "run-local 套件安裝失敗。"
    }
    return [pscustomobject]@{ Python = $VenvPython; Installed = $Missing; Runtime = "VIA_MANAGED_VENV" }
}

function def_FindCoreAuthorityFiles {
    param([Parameter(Mandatory)][string]$BaseDir)
    $Rows = [System.Collections.Generic.List[object]]::new()
    $SearchRoots = @(
        $PSScriptRoot,
        (Join-Path $BaseDir "supportive modules"),
        $BaseDir,
        (Join-Path $env:USERPROFILE "Downloads"),
        (Join-Path $env:USERPROFILE "OneDrive\文件\VeritasIntelligenceAnalytics"),
        (Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics\module\supportive_module")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Container }

    foreach ($Name in $CORE_AUTHORITY_FILES) {
        $Candidates = @()
        $Stem = [IO.Path]::GetFileNameWithoutExtension($Name)
        $Extension = [IO.Path]::GetExtension($Name)
        $AcceptedNamePattern = "^(?:\d+-)?{0}(?: \(\d+\))?{1}$" -f `
            [Regex]::Escape($Stem), `
            [Regex]::Escape($Extension)
        foreach ($Root in $SearchRoots) {
            $Candidates += Get-ChildItem `
                -LiteralPath $Root `
                -File `
                -Filter "*$Stem*$Extension" `
                -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match $AcceptedNamePattern }
        }
        $Candidates = @($Candidates | Sort-Object FullName -Unique)
        $Preferred = $Candidates |
            Sort-Object {
                if ($_.DirectoryName -like "*supportive modules*") { 0 } else { 1 }
            } |
            Select-Object -First 1
        if ($Preferred) {
            $Hash = (Get-FileHash -LiteralPath $Preferred.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $Rows.Add([pscustomobject]@{
                Name = $Name
                Status = if ($Preferred.Length -eq 0) { "YELLOW_EMPTY_ATTACHMENT" } else { "PENDING_AST" }
                AuthorityPath = $Preferred.FullName
                Bytes = $Preferred.Length
                SHA256 = $Hash
                Copies = $Candidates.Count
            })
        }
        else {
            $Rows.Add([pscustomobject]@{
                Name = $Name
                Status = "YELLOW_NOT_FOUND"
                AuthorityPath = ""
                Bytes = 0
                SHA256 = ""
                Copies = 0
            })
        }
    }
    return @($Rows)
}

function def_InvokeAstProbe {
    param(
        [Parameter(Mandatory)][string]$PythonExe,
        [Parameter(Mandatory)][object[]]$CoreRows
    )
    $Result = [System.Collections.Generic.List[object]]::new()
    foreach ($Row in $CoreRows) {
        if (-not $Row.AuthorityPath) {
            $Result.Add($Row)
            continue
        }
        if ($Row.Bytes -eq 0) {
            $Result.Add($Row)
            continue
        }
        $Probe = @'
import ast, pathlib, sys
p = pathlib.Path(sys.argv[1])
try:
    ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
except Exception as exc:
    print(f"{type(exc).__name__}: {exc}")
    raise SystemExit(2)
print("AST_PASS")
'@
        $Output = & $PythonExe -c $Probe $Row.AuthorityPath 2>&1
        $Status = if ($LASTEXITCODE -eq 0) { "GREEN_AST_PASS" } else { "RED_AST_FAIL" }
        $Result.Add([pscustomobject]@{
            Name = $Row.Name
            Status = $Status
            AuthorityPath = $Row.AuthorityPath
            Bytes = $Row.Bytes
            SHA256 = $Row.SHA256
            Copies = $Row.Copies
            Detail = ($Output -join " ")
        })
    }
    return @($Result)
}

function def_WriteAuthorityOverlay {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][object[]]$CoreRows,
        [Parameter(Mandatory)][string]$ScriptHash
    )
    $Accepted = @()
    foreach ($Entry in $AUTHORITY_ACCEPTED.GetEnumerator()) {
        $Resolved = Join-Path $VIA_BaseDir ($Entry.Value -replace "/", [IO.Path]::DirectorySeparatorChar)
        $Accepted += [ordered]@{
            name = $Entry.Key
            authority_path = $Entry.Value
            exists = [bool](Test-Path -LiteralPath $Resolved -PathType Leaf)
            disposition = "OPERATOR_ACCEPTED_RECOMMENDATION"
            runtime_activation = $false
        }
    }
    $Excluded = @()
    foreach ($Entry in $AUTHORITY_EXCLUDED.GetEnumerator()) {
        $Excluded += [ordered]@{
            name = $Entry.Key
            disposition = $Entry.Value
            runtime_authority = "EXCLUDED"
            canonical_owner = "UNASSIGNED"
            activation_input = "NOT_ALLOWED"
            deletion = "NOT_ALLOWED"
            promotion = "NOT_ALLOWED"
            evidence_retention = "ALLOWED"
        }
    }
    $Overlay = [ordered]@{
        schema = "via.authority.overlay.v1"
        generated_utc = [DateTime]::UtcNow.ToString("o")
        script_version = $SCRIPT_VERSION
        script_sha256 = $ScriptHash
        policy = "RUN_LOCAL_PROPOSED_OVERLAY_NO_CANONICAL_WRITE"
        accepted_recommendations = $Accepted
        excluded_legacy = $Excluded
        core_authority = $CoreRows
        pending_authority = 0
        canonical_writes = 0
        activation_attempted = $false
    }
    def_WriteJson -Data $Overlay -Path $Path -Depth 30
}

function def_InvokeThreeRoundPanorama {
    param(
        [Parameter(Mandatory)][string]$PythonExe,
        [Parameter(Mandatory)][object[]]$CoreRows,
        [Parameter(Mandatory)][string]$EvidenceDir
    )
    $PreviousHashes = @{}
    foreach ($Row in $CoreRows) {
        if ($Row.AuthorityPath) { $PreviousHashes[$Row.AuthorityPath] = $Row.SHA256 }
    }
    $RoundSummaries = @()
    for ($Round = 1; $Round -le 3; $Round++) {
        $RoundRows = def_InvokeAstProbe -PythonExe $PythonExe -CoreRows $CoreRows
        $HashDrift = 0
        foreach ($Row in $RoundRows) {
            if ($Row.AuthorityPath -and (Test-Path -LiteralPath $Row.AuthorityPath -PathType Leaf)) {
                $NowHash = (Get-FileHash -LiteralPath $Row.AuthorityPath -Algorithm SHA256).Hash.ToLowerInvariant()
                if ($PreviousHashes.ContainsKey($Row.AuthorityPath) -and $PreviousHashes[$Row.AuthorityPath] -ne $NowHash) {
                    $HashDrift++
                    $Row.Status = "RED_HASH_DRIFT"
                }
            }
        }
        $Red = @($RoundRows | Where-Object { $_.Status -like "RED*" }).Count
        $Yellow = @($RoundRows | Where-Object { $_.Status -like "YELLOW*" }).Count
        $Summary = [ordered]@{
            round = $Round
            strategy = @("COMPREHENSIVE_SAFE_REVIEW", "SEQUENTIAL_DEPENDENCY_REVIEW", "FINAL_STABILITY_REVIEW")[$Round - 1]
            generated_utc = [DateTime]::UtcNow.ToString("o")
            green = @($RoundRows | Where-Object { $_.Status -like "GREEN*" }).Count
            yellow = $Yellow
            red = $Red
            hash_drift = $HashDrift
            hydra_blocking = 0
            ssot_pending = 0
            mutation = $false
            activation = $false
            gate = if ($Red -eq 0 -and $HashDrift -eq 0) { "ROUND_PASS" } else { "ROUND_FAIL_CLOSED" }
            rows = $RoundRows
        }
        $RoundPath = Join-Path $EvidenceDir ("round_{0:D2}_matrix.json" -f $Round)
        def_WriteJson -Data $Summary -Path $RoundPath -Depth 30
        $RoundSummaries += $Summary
    }
    return $RoundSummaries
}

function def_GetVdfOrchestratorPython {
    return @'
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


EXPECTED_SUPPORTIVE_MODULES = {
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_SSOT_Unified",
    "VIA_EnvManager",
    "VeritasAegisNexus",
    "VIA_RegistryCore_v1",
    "VeritasCeleritas",
}


def def_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_table_names(connection: duckdb.DuckDBPyConnection) -> set[str]:
    rows = connection.execute(
        "select table_name from information_schema.tables where table_schema='main'"
    ).fetchall()
    return {str(row[0]) for row in rows}


def def_scalar(connection: duckdb.DuckDBPyConnection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def def_import_all_supportive_modules(core_root: Path) -> dict[str, Any]:
    os.environ["VIA_SUPPORTIVE_ROOT"] = str(core_root)
    os.chdir(core_root)
    sys.path.insert(0, str(core_root))
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            panorama = importlib.import_module("VIA_Panorama_AST_RuntimeInjector")
            bridge = importlib.import_module("VIA_Runtime_Bridge_All_in_One")
            context = bridge.def_bootstrap_runtime()
        loaded_names = set(context.loaded_modules)
        loaded_names.update({panorama.__name__, bridge.__name__})
        missing = sorted(EXPECTED_SUPPORTIVE_MODULES - loaded_names)
        errors = {str(key): str(value) for key, value in context.errors.items()}
        state_failures = sorted(
            name for name, detail in context.state.items()
            if isinstance(detail, dict) and detail.get("ok") is False
        )
        ready = not missing and not errors and not state_failures
        return {
            "ready": ready,
            "expected_count": len(EXPECTED_SUPPORTIVE_MODULES),
            "imported_count": len(loaded_names & EXPECTED_SUPPORTIVE_MODULES),
            "expected_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "imported_modules": sorted(loaded_names),
            "missing_modules": missing,
            "module_errors": errors,
            "state_failures": state_failures,
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
        }
    except Exception as exc:
        return {
            "ready": False,
            "expected_count": len(EXPECTED_SUPPORTIVE_MODULES),
            "imported_count": 0,
            "expected_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "imported_modules": [],
            "missing_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "module_errors": {"vdf_supportive_import": f"{type(exc).__name__}: {exc}"},
            "state_failures": [],
            "traceback": traceback.format_exc(),
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
        }


def def_bootstrap(data_root: Path, run_root: Path, core_root: Path) -> dict[str, Any]:
    manifest_path = data_root / "manifest.json"
    database_path = data_root / "via_marketflow.duckdb"
    required_tables = {"market_daily", "etf_daily", "etf_signals", "stock_price"}
    checks: list[dict[str, Any]] = []
    supportive = def_import_all_supportive_modules(core_root)
    checks.append({
        "check": "all_supportive_modules_imported",
        "ok": bool(supportive.get("ready")),
        "value": supportive.get("imported_count", 0),
        "expected": supportive.get("expected_count", 7),
    })

    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else {}
    )
    data_gate = str(manifest.get("gate", "NO_MANIFEST"))
    gate_ok = data_gate in {"DATA_READY_READ_ONLY_API", "DATA_READY_DEGRADED_READ_ONLY_API"}
    checks.append({"check": "data_gate", "ok": gate_ok, "value": data_gate})
    checks.append({"check": "database_exists", "ok": database_path.is_file(), "value": str(database_path)})

    tables: set[str] = set()
    market_rows = 0
    etf_rows = 0
    pk_duplicates = -1
    placeholder_rows = -1
    database_error = ""
    if database_path.is_file():
        try:
            connection = duckdb.connect(str(database_path), read_only=True)
            try:
                tables = def_table_names(connection)
                missing = sorted(required_tables - tables)
                checks.append({"check": "required_tables", "ok": not missing, "value": sorted(tables), "missing": missing})
                if "market_daily" in tables:
                    market_rows = def_scalar(connection, "select count(*) from market_daily")
                    pk_duplicates = def_scalar(
                        connection,
                        """select count(*) from (
                               select date,ticker,count(*) n from market_daily
                               group by date,ticker having count(*) > 1
                           )"""
                    )
                    placeholder_rows = def_scalar(
                        connection,
                        "select count(*) from market_daily where close is null and adj_close is null"
                    )
                if "etf_daily" in tables:
                    etf_rows = def_scalar(connection, "select count(*) from etf_daily")
            finally:
                connection.close()
        except Exception as exc:
            database_error = f"{type(exc).__name__}: {exc}"
            checks.append({"check": "database_read_only_open", "ok": False, "value": database_error})
    else:
        checks.append({"check": "required_tables", "ok": False, "value": [], "missing": sorted(required_tables)})

    checks.extend([
        {"check": "market_rows", "ok": market_rows > 0, "value": market_rows},
        {"check": "etf_rows", "ok": etf_rows > 0, "value": etf_rows},
        {"check": "market_pk_duplicates", "ok": pk_duplicates == 0, "value": pk_duplicates},
        {"check": "price_placeholder_rows", "ok": placeholder_rows == 0, "value": placeholder_rows},
    ])
    ready = all(bool(row.get("ok")) for row in checks)
    payload = {
        "schema": "via.vdf.runtime.heartbeat.v1",
        "service": "VDF",
        "status": "READY" if ready else "BLOCKED",
        "gate": "VDF_DATAHUB_READY" if ready else "VDF_DATAHUB_FAIL_CLOSED",
        "updated_utc": def_utc_now(),
        "pid": __import__("os").getpid(),
        "mode": "RUN_LOCAL_READ_ONLY",
        "data_root": str(data_root),
        "run_root": str(run_root),
        "market_rows": market_rows,
        "etf_rows": etf_rows,
        "checks": checks,
        "supportive_modules": supportive,
        "supportive_modules_all_imported": bool(supportive.get("ready")),
        "canonical_mutation": False,
        "database_write": False,
        "error": database_error,
    }
    return payload


def def_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--core-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = def_bootstrap(Path(args.data_root), Path(args.run_root), Path(args.core_root))
    def_write_json(Path(args.output), payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(def_main())
'@
}

function def_GetVrnRuntimeProbePython {
    return @'
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_MODULES = {
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_EnvManager",
    "VIA_RegistryCore_v1",
    "VIA_SSOT_Unified",
    "VeritasAegisNexus",
    "VeritasCeleritas",
}


def def_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): def_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [def_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return str(value)


def def_probe(core_root: Path) -> dict[str, Any]:
    os.environ["VIA_SUPPORTIVE_ROOT"] = str(core_root)
    os.chdir(core_root)
    sys.path.insert(0, str(core_root))
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            panorama = importlib.import_module("VIA_Panorama_AST_RuntimeInjector")
            bridge = importlib.import_module("VIA_Runtime_Bridge_All_in_One")
            context = bridge.def_bootstrap_runtime()
        loaded = set(context.loaded_modules)
        loaded.update({panorama.__name__, bridge.__name__})
        missing = sorted(EXPECTED_MODULES - loaded)
        errors = def_json_safe(context.errors)
        states = def_json_safe(context.state)
        state_failures = sorted(
            name for name, detail in context.state.items()
            if isinstance(detail, dict) and detail.get("ok") is False
        )
        ready = not missing and not errors and not state_failures
        return {
            "schema": "via.vrn.runtime.heartbeat.v1",
            "service": "VRN",
            "status": "READY" if ready else "BLOCKED",
            "gate": "VRN_CORE_READY" if ready else "VRN_CORE_FAIL_CLOSED",
            "updated_utc": def_utc_now(),
            "pid": os.getpid(),
            "mode": "RUN_LOCAL_CANONICAL_NAME_MAP",
            "core_root": str(core_root),
            "loaded_modules": def_json_safe(context.loaded_modules),
            "imported_module_names": sorted(loaded),
            "loaded_count": len(loaded),
            "expected_count": len(EXPECTED_MODULES),
            "missing_modules": missing,
            "module_errors": errors,
            "bootstrap_state": states,
            "state_failures": state_failures,
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
            "canonical_mutation": False,
        }
    except Exception as exc:
        return {
            "schema": "via.vrn.runtime.heartbeat.v1",
            "service": "VRN",
            "status": "BLOCKED",
            "gate": "VRN_CORE_FAIL_CLOSED",
            "updated_utc": def_utc_now(),
            "pid": os.getpid(),
            "mode": "RUN_LOCAL_CANONICAL_NAME_MAP",
            "core_root": str(core_root),
            "loaded_modules": {},
            "imported_module_names": [],
            "loaded_count": 0,
            "expected_count": len(EXPECTED_MODULES),
            "missing_modules": sorted(EXPECTED_MODULES),
            "module_errors": {"probe": f"{type(exc).__name__}: {exc}"},
            "traceback": traceback.format_exc(),
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
            "canonical_mutation": False,
        }


def def_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = def_probe(Path(args.core_root))
    def_write_json(Path(args.output), payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(def_main())
'@
}

function def_StageRuntimeCore {
    param(
        [Parameter(Mandatory)][object[]]$CoreRows,
        [Parameter(Mandatory)][string]$CoreStageDir
    )
    New-Item -ItemType Directory -Path $CoreStageDir -Force | Out-Null
    $Required = @(
        "VIA_Panorama_AST_RuntimeInjector.py",
        "VIA_EnvManager.py",
        "VIA_RegistryCore_v1.py",
        "VIA_SSOT_Unified.py",
        "VeritasAegisNexus.py",
        "VeritasCeleritas.py",
        "VIA_Runtime_Bridge_All_in_One.py"
    )
    $Staged = [System.Collections.Generic.List[object]]::new()
    foreach ($Name in $Required) {
        $Source = $CoreRows |
            Where-Object { $_.Name -eq $Name -and $_.AuthorityPath } |
            Select-Object -First 1
        if (-not $Source) {
            $Staged.Add([pscustomobject]@{
                Name = $Name
                Status = "RED_SOURCE_NOT_FOUND"
                Source = ""
                StagedPath = ""
                SHA256 = ""
            })
            continue
        }
        $Destination = Join-Path $CoreStageDir $Name
        Copy-Item -LiteralPath $Source.AuthorityPath -Destination $Destination -Force
        $Staged.Add([pscustomobject]@{
            Name = $Name
            Status = "GREEN_STAGED_RUN_LOCAL"
            Source = $Source.AuthorityPath
            StagedPath = $Destination
            SHA256 = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
        })
    }

    $BridgePath = Join-Path $CoreStageDir "VIA_Runtime_Bridge_All_in_One.py"
    if (Test-Path -LiteralPath $BridgePath -PathType Leaf) {
        $Bridge = Get-Content -LiteralPath $BridgePath -Raw -Encoding UTF8
        if ($Bridge -notmatch "(?m)^import os$") {
            $Bridge = [regex]::Replace(
                $Bridge,
                '(?m)^import json\r?$',
                "import json`nimport os",
                1
            )
        }
        $Bridge = [regex]::Replace(
            $Bridge,
            '(?m)^def_PARAM_SUPPORTIVE_ROOT\s*=\s*Path\(r".*?"\)\s*$',
            'def_PARAM_SUPPORTIVE_ROOT = Path(os.environ.get("VIA_SUPPORTIVE_ROOT", str(Path(__file__).resolve().parent)))'
        )
        $SafeSerializer = @'

def def_context_payload(ctx: def_VIARuntimeContext) -> Dict[str, Any]:
    """Serialize runtime state without deepcopy/pickling live module objects."""
    return {
        "supportive_root": ctx.supportive_root,
        "loaded_modules": dict(ctx.loaded_modules),
        "state": ctx.state,
        "errors": ctx.errors,
        "module_slots": {
            "env_manager": ctx.env_manager is not None,
            "registry": ctx.registry is not None,
            "ssot": ctx.ssot is not None,
            "aegis": ctx.aegis is not None,
            "celeritas": ctx.celeritas is not None,
        },
    }


'@
        if ($Bridge -notmatch "def def_context_payload") {
            $Bridge = $Bridge.Replace(
                "def def_main(argv: Optional[List[str]] = None) -> int:",
                $SafeSerializer + "def def_main(argv: Optional[List[str]] = None) -> int:"
            )
        }
        $Bridge = $Bridge.Replace(
            "    def_bootstrap_aegis(ctx)`n    def_bootstrap_aegis(ctx)`n",
            "    def_bootstrap_aegis(ctx)`n"
        )
        $Bridge = $Bridge.Replace("def_print_json(asdict(ctx))", "def_print_json(def_context_payload(ctx))")
        def_WriteUtf8NoBom -Path $BridgePath -Content $Bridge
        $BridgeRow = $Staged | Where-Object { $_.Name -eq "VIA_Runtime_Bridge_All_in_One.py" } | Select-Object -First 1
        if ($BridgeRow) {
            $BridgeRow.Status = "GREEN_STAGED_AND_SERIALIZER_PATCHED"
            $BridgeRow.SHA256 = (Get-FileHash -LiteralPath $BridgePath -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    return @($Staged)
}

function def_InvokeVdfVrnStartup {
    param(
        [Parameter(Mandatory)][string]$PythonExe,
        [Parameter(Mandatory)][object[]]$CoreRows,
        [Parameter(Mandatory)][string]$RuntimeDir,
        [Parameter(Mandatory)][string]$RunDir,
        [Parameter(Mandatory)][string]$DataRoot,
        [Parameter(Mandatory)][string]$EvidenceDir
    )
    $CoreStageDir = Join-Path $RuntimeDir "core_runtime"
    $StageRows = def_StageRuntimeCore -CoreRows $CoreRows -CoreStageDir $CoreStageDir
    def_WriteJson -Data $StageRows -Path (Join-Path $EvidenceDir "05_runtime_core_stage.json") -Depth 20
    $StageRed = @($StageRows | Where-Object { $_.Status -like "RED*" }).Count

    $VdfPath = Join-Path $CoreStageDir "VDF_ENG001_DataHubOrchestrator.py"
    $VrnProbePath = Join-Path $CoreStageDir "VRN_Runtime_Orchestrator.py"
    def_WriteUtf8NoBom -Path $VdfPath -Content (def_GetVdfOrchestratorPython)
    def_WriteUtf8NoBom -Path $VrnProbePath -Content (def_GetVrnRuntimeProbePython)

    $AstProbeCode = @'
import ast, json, pathlib, sys
rows = []
for raw in sys.argv[1:]:
    path = pathlib.Path(raw)
    try:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        rows.append({"path": str(path), "status": "GREEN_AST_PASS"})
    except Exception as exc:
        rows.append({"path": str(path), "status": "RED_AST_FAIL", "error": f"{type(exc).__name__}: {exc}"})
print(json.dumps(rows))
raise SystemExit(0 if all(row["status"] == "GREEN_AST_PASS" for row in rows) else 2)
'@
    $AstTargets = @(
        (Join-Path $CoreStageDir "VIA_Runtime_Bridge_All_in_One.py"),
        $VdfPath,
        $VrnProbePath
    )
    $AstOutput = & $PythonExe -c $AstProbeCode @AstTargets 2>&1
    $AstExit = $LASTEXITCODE
    def_WriteUtf8NoBom -Path (Join-Path $EvidenceDir "06_runtime_generated_ast.json") -Content (($AstOutput | Select-Object -Last 1) -join "")

    $VdfHeartbeat = Join-Path $RunDir "vdf_heartbeat.json"
    $VrnHeartbeat = Join-Path $RunDir "vrn_heartbeat.json"
    if ($StageRed -eq 0 -and $AstExit -eq 0) {
        & $PythonExe $VdfPath `
            --data-root $DataRoot `
            --run-root $RunDir `
            --core-root $CoreStageDir `
            --output $VdfHeartbeat 2>&1 |
            ForEach-Object { "$_" } |
            Set-Content -LiteralPath (Join-Path $RunDir "vdf_startup_console.log") -Encoding UTF8
        $VdfExit = $LASTEXITCODE

        & $PythonExe $VrnProbePath `
            --core-root $CoreStageDir `
            --output $VrnHeartbeat 2>&1 |
            ForEach-Object { "$_" } |
            Set-Content -LiteralPath (Join-Path $RunDir "vrn_startup_console.log") -Encoding UTF8
        $VrnExit = $LASTEXITCODE
    }
    else {
        $VdfExit = 2
        $VrnExit = 2
    }

    $Vdf = if (Test-Path -LiteralPath $VdfHeartbeat -PathType Leaf) {
        Get-Content -LiteralPath $VdfHeartbeat -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    else {
        [pscustomobject]@{ service = "VDF"; status = "BLOCKED"; gate = "VDF_DATAHUB_NOT_STARTED" }
    }
    $Vrn = if (Test-Path -LiteralPath $VrnHeartbeat -PathType Leaf) {
        Get-Content -LiteralPath $VrnHeartbeat -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    else {
        [pscustomobject]@{ service = "VRN"; status = "BLOCKED"; gate = "VRN_CORE_NOT_STARTED" }
    }

    $BridgeCliPath = Join-Path $CoreStageDir "VIA_Runtime_Bridge_All_in_One.py"
    $PreviousRoot = $env:VIA_SUPPORTIVE_ROOT
    Push-Location -LiteralPath $CoreStageDir
    try {
        $env:VIA_SUPPORTIVE_ROOT = $CoreStageDir
        $BridgeCliOutput = & $PythonExe $BridgeCliPath bootstrap 2>&1
        $BridgeCliExit = $LASTEXITCODE
        def_WriteUtf8NoBom `
            -Path (Join-Path $RunDir "runtime_bridge_bootstrap.json") `
            -Content ($BridgeCliOutput -join [Environment]::NewLine)
    }
    finally {
        Pop-Location
        if ($null -eq $PreviousRoot) {
            Remove-Item Env:VIA_SUPPORTIVE_ROOT -ErrorAction SilentlyContinue
        }
        else {
            $env:VIA_SUPPORTIVE_ROOT = $PreviousRoot
        }
    }

    $VdfSupportiveReady = (
        $null -ne $Vdf.PSObject.Properties["supportive_modules_all_imported"] -and
        [bool]$Vdf.supportive_modules_all_imported
    )
    $VdfSupportiveObject = if (
        $null -ne $Vdf.PSObject.Properties["supportive_modules"]
    ) {
        $Vdf.supportive_modules
    }
    else {
        $null
    }
    $VdfImportedCount = if (
        $null -ne $VdfSupportiveObject -and
        $null -ne $VdfSupportiveObject.PSObject.Properties["imported_count"]
    ) {
        [int]$VdfSupportiveObject.imported_count
    }
    else {
        0
    }
    $VrnImportedCount = if ($null -ne $Vrn.PSObject.Properties["loaded_count"]) {
        [int]$Vrn.loaded_count
    }
    else {
        0
    }
    $VrnExpectedCount = if ($null -ne $Vrn.PSObject.Properties["expected_count"]) {
        [int]$Vrn.expected_count
    }
    else {
        7
    }
    $VrnSupportiveReady = (
        $VrnImportedCount -eq 7 -and
        $VrnExpectedCount -eq 7
    )
    $Ready = (
        $StageRed -eq 0 -and
        $AstExit -eq 0 -and
        $VdfExit -eq 0 -and
        $VrnExit -eq 0 -and
        $BridgeCliExit -eq 0 -and
        $Vdf.status -eq "READY" -and
        $Vrn.status -eq "READY" -and
        $VdfSupportiveReady -and
        $VrnSupportiveReady
    )
    $Status = [ordered]@{
        schema = "via.vdf_vrn.runtime.status.v2"
        generated_utc = [DateTime]::UtcNow.ToString("o")
        overall_gate = if ($Ready) { "VDF_VRN_RUNTIME_READY" } else { "VDF_VRN_RUNTIME_BLOCKED_FAIL_CLOSED" }
        ready = $Ready
        stage_red = $StageRed
        generated_ast_exit = $AstExit
        bridge_cli_exit = $BridgeCliExit
        vdf = $Vdf
        vrn = $Vrn
        supportive_modules_expected = 7
        supportive_modules_imported = [Math]::Min(
            $VdfImportedCount,
            $VrnImportedCount
        )
        supportive_modules_all_imported = (
            $VdfSupportiveReady -and
            $VrnSupportiveReady
        )
        stage = $StageRows
        canonical_mutation = $false
        canonical_bridge_activation = $false
        run_local_bridge_bootstrap = $true
    }
    def_WriteJson -Data $Status -Path (Join-Path $RunDir "vdf_vrn_runtime_status.json") -Depth 40
    Write-Output -NoEnumerate ([pscustomobject]$Status)
}

function def_GetEmbeddedPython {
    return @'
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib
import io
import json
import math
import os
import re
import shutil
import sys
import time
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import duckdb
import numpy as np
import pandas as pd
import requests
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import uvicorn

APP_VERSION = "v0112"
EXPECTED_SUPPORTIVE_MODULES = {
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_SSOT_Unified",
    "VIA_EnvManager",
    "VeritasAegisNexus",
    "VIA_RegistryCore_v1",
    "VeritasCeleritas",
}
CSV_ENCODING = "utf-8-sig"
DATE_OUTPUT_FORMAT = "%Y/%m/%d"
DATE_CHART_FORMAT = "%Y-%m-%d"
PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]
PRIMARY_KEY = ["date", "ticker"]
ETF_TICKERS = {
    "A_GLOBAL": ["SPY","QQQ","IWM","EFA","EEM","VWO","FXI","MCHI","EWJ","EWY","EWT","EWZ","INDA","EWG","EZU"],
    "B_SECTOR": ["XLK","XLF","XLV","XLE","XLI","XLY","XLP","XLU","XLRE","XLB","XLC","SOXX","SMH","IBB","KRE","ARKK"],
    "C_BOND": ["SHY","IEF","TLT","IEI","LQD","HYG","JNK","TIP","BND","EMB","MUB"],
    "D_THEME": ["GLD","IAU","SLV","USO","DJP","VTV","VUG","QUAL","MTUM","SQQQ","TQQQ","SH"],
    "E_CONTEXT": ["UUP","UDN","BIL","SGOV","VIXY"],
    "F_TAIWAN": ["0050.TW","0056.TW","00632R.TW","006208.TW"],
}
INDEX_TICKERS = [
    "^GSPC","^NDX","^DJI","^RUT","^VIX","^N225","^HSI","^HSCE",
    "000001.SS","399001.SZ","^KS11","^TWII","^GDAXI","^FTSE","^FCHI",
    "^STI","^NSEI","^AXJO"
]
INDEX_PROXY_TICKERS = ["1306.T"]
FX_TICKERS = ["TWD=X","EURUSD=X","JPY=X","GBPUSD=X","CNY=X","KRW=X","AUDUSD=X","DX-Y.NYB"]
COMMODITY_TICKERS = ["GC=F","SI=F","PL=F","PA=F","CL=F","BZ=F","NG=F","HO=F","HG=F","ALI=F","ZS=F","ZC=F","ZW=F","KC=F","RB=F"]
RATE_TICKERS = ["^IRX","^FVX","^TNX","^TYX"]
SHIPPING_TICKERS = ["BDRY","BOAT","SEA","SBLK","NAT"]
CRYPTO_TICKERS = ["BTC-USD","ETH-USD","SOL-USD"]
TW_FALLBACK = [
    "2330.TW","2317.TW","2454.TW","2308.TW","2301.TW","2345.TW",
    "2603.TW","2609.TW","2615.TW","2617.TW","2606.TW","2612.TW",
    "2002.TW","2015.TW","2027.TW","1101.TW","1102.TW","1802.TW",
    "1301.TW","1303.TW","1326.TW","6505.TW","1710.TW",
    "6415.TW","8069.TWO"
]
HISTORICAL_ONLY_TICKERS = {
    "1704.TW": "DELISTED_2018_RETAIN_EXISTING_HISTORY_DO_NOT_LIVE_FETCH",
}
CATEGORY_LOOKUP = {}
for _category, _tickers in ETF_TICKERS.items():
    for _ticker in _tickers:
        CATEGORY_LOOKUP[_ticker] = ("ETF", _category)
for _ticker in INDEX_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("INDEX", "GLOBAL_INDEX")
for _ticker in INDEX_PROXY_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("INDEX_PROXY", "JAPAN_TOPIX_ETF_PROXY")
for _ticker in FX_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("FX", "CURRENCY")
for _ticker in COMMODITY_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("COMMODITY", "FUTURE")
for _ticker in RATE_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("RATE", "YIELD")
for _ticker in SHIPPING_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("SHIPPING", "LISTED_PROXY")
for _ticker in CRYPTO_TICKERS:
    CATEGORY_LOOKUP[_ticker] = ("CRYPTO", "SPOT_PROXY")


def def_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_import_api_supportive_runtime(core_root: Path) -> dict[str, Any]:
    os.environ["VIA_SUPPORTIVE_ROOT"] = str(core_root)
    os.chdir(core_root)
    sys.path.insert(0, str(core_root))
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            panorama = importlib.import_module("VIA_Panorama_AST_RuntimeInjector")
            bridge = importlib.import_module("VIA_Runtime_Bridge_All_in_One")
            context = bridge.def_bootstrap_runtime()
        loaded_names = set(context.loaded_modules)
        loaded_names.update({panorama.__name__, bridge.__name__})
        missing = sorted(EXPECTED_SUPPORTIVE_MODULES - loaded_names)
        errors = {str(key): str(value) for key, value in context.errors.items()}
        state_failures = sorted(
            name for name, detail in context.state.items()
            if isinstance(detail, dict) and detail.get("ok") is False
        )
        ready = not missing and not errors and not state_failures
        return {
            "schema": "via.api.supportive.runtime.v1",
            "status": "READY" if ready else "BLOCKED",
            "gate": (
                "API_SUPPORTIVE_RUNTIME_READY"
                if ready
                else "API_SUPPORTIVE_RUNTIME_FAIL_CLOSED"
            ),
            "ready": ready,
            "pid": os.getpid(),
            "updated_utc": def_utc_now(),
            "expected_count": len(EXPECTED_SUPPORTIVE_MODULES),
            "imported_count": len(loaded_names & EXPECTED_SUPPORTIVE_MODULES),
            "expected_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "imported_modules": sorted(loaded_names),
            "missing_modules": missing,
            "module_errors": errors,
            "state_failures": state_failures,
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
            "canonical_mutation": False,
        }
    except Exception as exc:
        return {
            "schema": "via.api.supportive.runtime.v1",
            "status": "BLOCKED",
            "gate": "API_SUPPORTIVE_RUNTIME_FAIL_CLOSED",
            "ready": False,
            "pid": os.getpid(),
            "updated_utc": def_utc_now(),
            "expected_count": len(EXPECTED_SUPPORTIVE_MODULES),
            "imported_count": 0,
            "expected_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "imported_modules": [],
            "missing_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "module_errors": {"api_supportive_import": f"{type(exc).__name__}: {exc}"},
            "state_failures": [],
            "traceback": traceback.format_exc(),
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
            "canonical_mutation": False,
        }


def def_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temp.replace(path)


def def_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def def_normalize_ticker(value: str) -> str:
    value = str(value).strip().upper()
    if not value or value.startswith("#"):
        return ""
    if re.fullmatch(r"\d{4}", value):
        return value + ".TW"
    return value


def def_load_tickers(ticker_file: str) -> list[str]:
    tickers = []
    if ticker_file and Path(ticker_file).is_file():
        text = Path(ticker_file).read_text(encoding="utf-8-sig", errors="replace")
        for token in re.split(r"[\s,;|]+", text):
            ticker = def_normalize_ticker(token)
            if ticker:
                tickers.append(ticker)
    base = (
        [t for group in ETF_TICKERS.values() for t in group]
        + INDEX_TICKERS + INDEX_PROXY_TICKERS + FX_TICKERS + COMMODITY_TICKERS
        + RATE_TICKERS + SHIPPING_TICKERS + CRYPTO_TICKERS + TW_FALLBACK
    )
    live_tickers = list(dict.fromkeys(base + tickers))
    return [ticker for ticker in live_tickers if ticker not in HISTORICAL_ONLY_TICKERS]


def def_load_stock_metadata(stock_database: str) -> dict[str, dict[str, Any]]:
    if not stock_database or not Path(stock_database).is_file():
        return {}
    frame = pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            frame = pd.read_csv(stock_database, encoding=encoding, dtype=str)
            break
        except Exception:
            continue
    if frame.empty:
        return {}
    normalized_columns = {
        str(column).strip().lower().replace(" ", "_"): column for column in frame.columns
    }
    def pick(candidates: list[str]) -> str:
        for candidate in candidates:
            if candidate in normalized_columns:
                return normalized_columns[candidate]
        return ""
    ticker_column = pick(["yf_ticker", "yfinance_ticker", "ticker", "symbol", "stock_ticker", "股票代碼", "證券代號"])
    name_column = pick(["name", "stock_name", "chinese_name", "company_name", "名稱", "公司名稱", "證券名稱"])
    market_column = pick(["market", "exchange", "市場", "市場別"])
    industry_column = pick(["industry_code", "industry", "產業代碼", "產業別"])
    if not ticker_column:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for _, row in frame.iterrows():
        raw_ticker = str(row.get(ticker_column, "") or "").strip().upper()
        market = str(row.get(market_column, "") or "").strip().upper() if market_column else ""
        if re.fullmatch(r"\d{4}", raw_ticker):
            suffix = ".TWO" if any(token in market for token in ("TPEX", "OTC", "上櫃")) else ".TW"
            yf_ticker = raw_ticker + suffix
        else:
            yf_ticker = def_normalize_ticker(raw_ticker)
        if not yf_ticker:
            continue
        result[yf_ticker] = {
            "name": str(row.get(name_column, "") or "").strip() if name_column else "",
            "market": market,
            "industry_code": str(row.get(industry_column, "") or "").strip() if industry_column else "",
        }
    return result


def def_asset_class(ticker: str) -> tuple[str, str]:
    if ticker in CATEGORY_LOOKUP:
        return CATEGORY_LOOKUP[ticker]
    if ticker.endswith((".TW", ".TWO")):
        return ("TW_EQUITY", "TWSE" if ticker.endswith(".TW") else "TPEX")
    return ("EQUITY", "INTERNATIONAL")


def def_read_existing(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.DataFrame()


def def_incremental_start(existing: pd.DataFrame, configured_start: str) -> str:
    if existing.empty or "date" not in existing:
        return configured_start
    max_date = pd.to_datetime(existing["date"], errors="coerce").max()
    if pd.isna(max_date):
        return configured_start
    overlap = max_date - pd.Timedelta(days=7)
    return max(pd.Timestamp(configured_start), overlap).strftime("%Y-%m-%d")


def def_flatten_download(raw: pd.DataFrame, requested: list[str]) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()
    frames = []
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = set(map(str, raw.columns.get_level_values(0)))
        price_first = bool(level0.intersection({"Open","High","Low","Close","Adj Close","Volume"}))
        for ticker in requested:
            try:
                part = raw.xs(ticker, axis=1, level=1 if price_first else 0).copy()
            except Exception:
                continue
            part["ticker"] = ticker
            part["date"] = part.index
            frames.append(part.reset_index(drop=True))
    else:
        part = raw.copy()
        part["ticker"] = requested[0]
        part["date"] = part.index
        frames.append(part.reset_index(drop=True))
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    rename = {"adj_close": "adj_close"}
    out = out.rename(columns=rename)
    for column in PRICE_COLUMNS:
        if column not in out:
            out[column] = np.nan
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.tz_localize(None).dt.normalize()
    for column in ["open","high","low","close","adj_close","volume"]:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["date","ticker"])
    return out[["date","ticker"] + PRICE_COLUMNS]


def def_price_placeholder_mask(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series(False, index=frame.index, dtype=bool)
    close = pd.to_numeric(
        frame["close"] if "close" in frame.columns else pd.Series(np.nan, index=frame.index),
        errors="coerce",
    )
    adj_close = pd.to_numeric(
        frame["adj_close"] if "adj_close" in frame.columns else pd.Series(np.nan, index=frame.index),
        errors="coerce",
    )
    return close.isna() & adj_close.isna()


def def_count_price_placeholders(frame: pd.DataFrame) -> int:
    return int(def_price_placeholder_mask(frame).sum()) if not frame.empty else 0


def def_fetch_yfinance(
    tickers: list[str],
    start: str,
    end: str,
    batch_size: int,
    max_workers: int,
    timeout: int,
    heartbeat: Path,
) -> tuple[pd.DataFrame, list[dict]]:
    frames = []
    errors = []
    batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    for index, batch in enumerate(batches, start=1):
        last_error = ""
        for attempt in range(1, 4):
            try:
                raw = yf.download(
                    batch,
                    start=start,
                    end=end or None,
                    auto_adjust=False,
                    actions=False,
                    progress=False,
                    group_by="column",
                    threads=max(1, min(int(max_workers), 6)),
                    timeout=max(5, int(timeout)),
                )
                flat = def_flatten_download(raw, batch)
                if not flat.empty:
                    frames.append(flat)
                if not flat.empty:
                    usable = flat[
                        flat["close"].notna()
                        | flat["adj_close"].notna()
                        | flat["volume"].notna()
                    ]
                    returned = set(usable["ticker"].dropna().astype(str).unique())
                else:
                    returned = set()
                for missing_ticker in sorted(set(batch) - returned):
                    errors.append({
                        "batch": index,
                        "ticker": missing_ticker,
                        "error": "NO_ROWS_RETURNED",
                        "severity": "YELLOW_TICKER_ISOLATED",
                    })
                last_error = ""
                break
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(min(8, 2 ** attempt))
        if last_error:
            errors.append({"batch": index, "tickers": batch, "error": last_error})
        def_write_json(heartbeat, {
            "updated_utc": def_utc_now(),
            "stage": "YFINANCE_BATCH",
            "batch": index,
            "total_batches": len(batches),
            "rows": int(sum(len(frame) for frame in frames)),
            "errors": len(errors),
        })
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(), errors)


def def_enrich_prices(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    frame = frame.copy()
    for column in PRICE_COLUMNS:
        if column not in frame.columns:
            frame[column] = np.nan
    for column in ["open","high","low","close","adj_close","volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.loc[~def_price_placeholder_mask(frame)].copy()
    if frame.empty:
        return frame
    valid = frame["close"].replace(0, np.nan)
    classes = frame["ticker"].map(def_asset_class)
    frame["asset_class"] = [x[0] for x in classes]
    frame["category"] = [x[1] for x in classes]
    non_corporate = frame["asset_class"].isin(
        ["INDEX", "INDEX_PROXY", "FX", "COMMODITY", "RATE", "SHIPPING", "CRYPTO"]
    )
    frame.loc[non_corporate & frame["adj_close"].isna(), "adj_close"] = frame.loc[
        non_corporate & frame["adj_close"].isna(), "close"
    ]
    frame["analysis_close"] = frame["adj_close"].combine_first(frame["close"])
    frame["analysis_price_method"] = np.where(
        frame["adj_close"].notna(),
        "ADJ_CLOSE",
        np.where(frame["close"].notna(), "CLOSE_FALLBACK_UNADJUSTED", "UNAVAILABLE"),
    )
    frame["adj_factor"] = frame["adj_close"] / valid
    frame["adj_open"] = frame["open"] * frame["adj_factor"]
    frame["adj_high"] = frame["high"] * frame["adj_factor"]
    frame["adj_low"] = frame["low"] * frame["adj_factor"]
    frame["dollar_vol"] = frame["close"] * frame["volume"]
    frame["region"] = np.where(frame["ticker"].str.endswith((".TW",".TWO")), "TAIWAN", "GLOBAL")
    frame["source"] = "YFINANCE_AUTO_ADJUST_FALSE"
    frame["is_proxy"] = True
    frame = frame.sort_values(PRIMARY_KEY).drop_duplicates(PRIMARY_KEY, keep="last")
    return frame


def def_merge_incremental(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        combined = incoming.copy()
    elif incoming.empty:
        combined = existing.copy()
    else:
        combined = pd.concat([existing, incoming], ignore_index=True)
    if combined.empty:
        return combined
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce").dt.normalize()
    combined = combined.dropna(subset=PRIMARY_KEY)
    combined = combined.loc[~def_price_placeholder_mask(combined)].copy()
    return combined.sort_values(PRIMARY_KEY).drop_duplicates(PRIMARY_KEY, keep="last")


def def_calculate_etf_daily(market: pd.DataFrame) -> pd.DataFrame:
    if market.empty:
        return pd.DataFrame()
    etfs = set(t for group in ETF_TICKERS.values() for t in group)
    out = market[market["ticker"].isin(etfs)].copy()
    if out.empty:
        return out
    out = out.sort_values(PRIMARY_KEY)
    grouped = out.groupby("ticker", group_keys=False)
    out["dvol_ma5"] = grouped["dollar_vol"].transform(lambda s: s.rolling(5, min_periods=3).mean())
    out["dvol_ma20"] = grouped["dollar_vol"].transform(lambda s: s.rolling(20, min_periods=5).mean())
    out["dvol_ratio"] = out["dollar_vol"] / out["dvol_ma20"].replace(0, np.nan)
    out["ret_1d"] = grouped["analysis_close"].pct_change(fill_method=None)
    out["ret_5d"] = grouped["analysis_close"].pct_change(5, fill_method=None)
    out["ret_10d"] = grouped["analysis_close"].pct_change(10, fill_method=None)
    out["ret_20d"] = grouped["analysis_close"].pct_change(20, fill_method=None)
    out["vol_chg"] = grouped["volume"].pct_change(fill_method=None)
    out["pv_signal"] = np.select(
        [(out["ret_1d"] > 0) & (out["vol_chg"] > 0.2), (out["ret_1d"] < 0) & (out["vol_chg"] > 0.2)],
        ["BUY_PRESSURE_PROXY", "SELL_PRESSURE_PROXY"],
        default="NEUTRAL",
    )
    spy = out[out["ticker"] == "SPY"][["date","ret_10d"]].rename(columns={"ret_10d": "spy_ret_10d"})
    out = out.merge(spy, on="date", how="left")
    out["rs_vs_spy"] = (1 + out["ret_10d"]) / (1 + out["spy_ret_10d"]) - 1
    out["rs_ma10"] = out.groupby("ticker")["rs_vs_spy"].transform(lambda s: s.rolling(10, min_periods=5).mean())
    out["rs_trend"] = out.groupby("ticker")["rs_ma10"].diff(5)
    out["flow_raw"] = np.nan
    out["flow_method"] = "UNAVAILABLE_REQUIRES_AUM_OR_SHARES"
    out["proxy_disclaimer"] = "Dollar volume/PV/RS are market-pressure proxies, not creation-redemption net flow."
    return out


def def_pivot_return(market: pd.DataFrame, ticker: str, periods: int = 1) -> pd.Series:
    price_column = "analysis_close" if "analysis_close" in market.columns else "adj_close"
    subset = market[market["ticker"] == ticker].set_index("date")[price_column].sort_index()
    return subset.pct_change(periods, fill_method=None)


def def_calculate_signals(market: pd.DataFrame, etf_daily: pd.DataFrame) -> pd.DataFrame:
    if market.empty:
        return pd.DataFrame()
    spy_dates = market.loc[market["ticker"] == "SPY", "date"].dropna().unique()
    dates = pd.Index(sorted(spy_dates), name="date")
    if dates.empty:
        dates = pd.Index(
            sorted(market.loc[market["date"].dt.weekday < 5, "date"].dropna().unique()),
            name="date",
        )
    out = pd.DataFrame(index=dates)
    def series(ticker: str, periods: int = 1) -> pd.Series:
        return def_pivot_return(market, ticker, periods).reindex(dates)
    out["risk_on_off"] = series("SPY", 5) - series("TLT", 5)
    out["hy_spread_proxy"] = series("HYG", 1) - series("IEF", 1)
    out["growth_vs_value"] = series("VUG", 20) - series("VTV", 20)
    out["em_rotation"] = series("EEM", 5) - series("SPY", 5)
    out["semicon_momentum"] = series("SMH", 5) - series("QQQ", 5)
    out["usd_twd_return"] = series("TWD=X", 5)
    out["tw_relative_strength"] = series("EWT", 5) - series("SPY", 5)
    out["cash_parking_signal"] = series("BIL", 5).fillna(0) + series("SGOV", 5).fillna(0)
    out["hedge_panic_signal"] = (
        market[market["ticker"].isin(["SQQQ","SH","VIXY"])]
        .pivot_table(index="date", columns="ticker", values="dollar_vol", aggfunc="last")
        .reindex(dates)
        .pct_change(5, fill_method=None)
        .replace([np.inf, -np.inf], np.nan)
        .mean(axis=1)
    )
    out["signal_completeness"] = out.notna().mean(axis=1)
    out["source"] = "CALCULATED_FROM_YFINANCE_PROXY"
    out["calendar_basis"] = "SPY_TRADING_SESSIONS" if len(spy_dates) else "WEEKDAY_FALLBACK"
    return out.reset_index()


def def_fetch_json(url: str, params: dict, timeout: int) -> tuple[Any, str]:
    try:
        response = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "VIA-MarketFlow/1.0"})
        response.raise_for_status()
        return response.json(), "PASS"
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "url": url, "params": params}, "FAIL"


def def_fetch_tw_official(raw_root: Path, timeout: int) -> list[dict]:
    today = date.today()
    candidates = []
    cursor = today
    while len(candidates) < 7:
        if cursor.weekday() < 5:
            candidates.append(cursor)
        cursor -= timedelta(days=1)
    sources = [
        ("TWSE_T86", "https://www.twse.com.tw/rwd/zh/fund/T86", lambda d: {"date": d.strftime("%Y%m%d"), "selectType": "ALLBUT0999", "response": "json"}),
        ("TWSE_MI_MARGN", "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN", lambda d: {"date": d.strftime("%Y%m%d"), "selectType": "ALL", "response": "json"}),
        ("TWSE_TWTB4U", "https://www.twse.com.tw/rwd/zh/afterTrading/TWTB4U", lambda d: {"date": d.strftime("%Y%m%d"), "response": "json"}),
        ("TPEX_INSTI", "https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade", lambda d: {"date": d.strftime("%Y/%m/%d"), "type": "Daily", "sect": "EW"}),
        ("TPEX_MARGIN", "https://www.tpex.org.tw/www/zh-tw/margin/balance", lambda d: {"date": d.strftime("%Y/%m/%d")}),
    ]
    ledger = []
    for source_name, url, param_builder in sources:
        final_status = "FAIL"
        final_date = ""
        final_path = ""
        detail = ""
        for candidate in candidates:
            payload, status = def_fetch_json(url, param_builder(candidate), timeout)
            path = raw_root / source_name / f"{candidate.isoformat()}.json"
            def_write_json(path, payload)
            if status == "PASS" and isinstance(payload, dict) and not payload.get("error"):
                final_status = "PASS_RAW_UNNORMALIZED"
                final_date = candidate.isoformat()
                final_path = str(path)
                break
            detail = payload.get("error", "No usable payload") if isinstance(payload, dict) else "Unexpected payload"
        ledger.append({
            "source": source_name,
            "status": final_status,
            "date": final_date,
            "raw_path": final_path,
            "detail": detail,
            "normalization": "PENDING_SCHEMA_VALIDATION",
        })
    return ledger


def def_write_tables(
    data_root: Path,
    market: pd.DataFrame,
    etf_daily: pd.DataFrame,
    signals: pd.DataFrame,
    stock_database: str,
) -> dict:
    tw_prices = market[market["asset_class"] == "TW_EQUITY"].copy() if not market.empty else pd.DataFrame()
    tw_tickers = sorted(tw_prices["ticker"].dropna().unique()) if not tw_prices.empty else []
    stock_metadata = def_load_stock_metadata(stock_database)
    stock_list = pd.DataFrame({
        "ticker": [re.sub(r"\.(TW|TWO)$", "", ticker) for ticker in tw_tickers],
        "name": [stock_metadata.get(ticker, {}).get("name", "") for ticker in tw_tickers],
        "market": ["TWSE" if ticker.endswith(".TW") else "TPEX" for ticker in tw_tickers],
        "isin_code": ["" for _ in tw_tickers],
        "yf_ticker": tw_tickers,
        "industry_code": [stock_metadata.get(ticker, {}).get("industry_code", "") for ticker in tw_tickers],
        "listing_date": [pd.NaT for _ in tw_tickers],
        "par_value": [np.nan for _ in tw_tickers],
        "shares_issued": [np.nan for _ in tw_tickers],
        "capital": [np.nan for _ in tw_tickers],
        "source_status": ["YFINANCE_TICKER_ONLY_OFFICIAL_ENRICHMENT_PENDING" for _ in tw_tickers],
    })
    derived_columns = [
        "date","ticker","analysis_close","analysis_price_method",
        "adj_factor","adj_open","adj_high","adj_low","dollar_vol",
        "asset_class","category","region","source","is_proxy"
    ]
    derived = tw_prices[[column for column in derived_columns if column in tw_prices.columns]].copy()
    if not derived.empty:
        derived["fi_hold_pct"] = np.nan
        derived["it_hold_pct"] = np.nan
        derived["dt_hold_pct"] = np.nan
        derived["inst_total_pct"] = np.nan
        derived["margin_maintenance_rate"] = np.nan
        derived["short_margin_ratio"] = np.nan
        derived["calculation_status"] = "INSUFFICIENT_OFFICIAL_POSITION_OR_LOAN_EVIDENCE"
    chip_daily = pd.DataFrame(columns=[
        "date","ticker","fi_buy","fi_sell","fi_net","it_buy","it_sell","it_net",
        "dt_buy","dt_sell","dt_net","margin_buy","margin_sell","margin_bal",
        "short_buy","short_sell","short_bal","margin_offset","daytrade_vol",
        "daytrade_value","source","source_status"
    ])
    etf_flow_precise = pd.DataFrame(columns=[
        "date","ticker","aum","shares_outstanding","nav_per_share","ret_1d",
        "flow_raw","flow_method","source","evidence_status"
    ])
    tables = {
        "market_daily": market,
        "etf_daily": etf_daily,
        "etf_flow_precise": etf_flow_precise,
        "etf_signals": signals,
        "stock_list": stock_list,
        "stock_price": tw_prices,
        "index_daily": market[market["asset_class"].isin(["INDEX", "INDEX_PROXY"])].copy() if not market.empty else pd.DataFrame(),
        "chip_daily": chip_daily,
        "derived": derived,
        "commodity_daily": market[market["asset_class"] == "COMMODITY"].copy() if not market.empty else pd.DataFrame(),
        "shipping_daily": market[market["asset_class"] == "SHIPPING"].copy() if not market.empty else pd.DataFrame(),
    }
    parquet_root = data_root / "parquet"
    csv_root = data_root / "csv"
    parquet_root.mkdir(parents=True, exist_ok=True)
    csv_root.mkdir(parents=True, exist_ok=True)
    database_path = data_root / "via_marketflow.duckdb"
    con = duckdb.connect(str(database_path))
    summary = {}
    try:
        for name, frame in tables.items():
            if frame is None:
                frame = pd.DataFrame()
            frame.to_parquet(parquet_root / name, index=False)
            csv_frame = frame.copy()
            if "date" in csv_frame:
                csv_frame["date"] = pd.to_datetime(csv_frame["date"], errors="coerce").dt.strftime(DATE_OUTPUT_FORMAT)
            csv_frame.to_csv(csv_root / name, index=False, encoding=CSV_ENCODING)
            con.register("_frame", frame)
            con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM _frame')
            con.unregister("_frame")
            summary[name] = {
                "rows": int(len(frame)),
                "min_date": str(frame["date"].min().date()) if len(frame) and "date" in frame else "",
                "max_date": str(frame["date"].max().date()) if len(frame) and "date" in frame else "",
                "duplicate_pk": int(frame.duplicated(PRIMARY_KEY).sum()) if len(frame) and set(PRIMARY_KEY).issubset(frame.columns) else 0,
            }
    finally:
        con.close()
    summary["database"] = str(database_path)
    snapshot_root = data_root / "snapshots"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    previous_snapshots = sorted(snapshot_root.glob("*_table_hashes.json"))
    previous_snapshot = previous_snapshots[-1] if previous_snapshots else None
    outputs = {}
    for name in tables:
        parquet_path = parquet_root / name
        csv_path = csv_root / name
        outputs[name] = {
            "parquet_path": str(parquet_path),
            "parquet_sha256": def_sha256(parquet_path),
            "parquet_bytes": parquet_path.stat().st_size,
            "csv_path": str(csv_path),
            "csv_sha256": def_sha256(csv_path),
            "csv_bytes": csv_path.stat().st_size,
        }
    snapshot_payload = {
        "schema": "via.marketflow.table-hash-chain.v1",
        "generated_utc": def_utc_now(),
        "app_version": APP_VERSION,
        "previous_snapshot": str(previous_snapshot) if previous_snapshot else "",
        "previous_snapshot_sha256": def_sha256(previous_snapshot) if previous_snapshot else "",
        "outputs": outputs,
        "database_path": str(database_path),
        "database_sha256": def_sha256(database_path),
        "canonical_via_module_mutation": False,
    }
    snapshot_path = snapshot_root / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}_table_hashes.json"
    def_write_json(snapshot_path, snapshot_payload)
    summary["_snapshot"] = {
        "path": str(snapshot_path),
        "sha256": def_sha256(snapshot_path),
        "previous_sha256": snapshot_payload["previous_snapshot_sha256"],
    }
    return summary


def def_quality_matrix(
    market: pd.DataFrame,
    etf_daily: pd.DataFrame,
    signals: pd.DataFrame,
    tables: dict,
    fetch_errors: list[dict],
    official_sources: list[dict],
    quarantine_summary: dict,
) -> list[dict]:
    checks = []
    def add(name: str, status: str, value: Any, threshold: str, blocking: bool, reason: str) -> None:
        checks.append({
            "check": name,
            "status": status,
            "value": value,
            "threshold": threshold,
            "blocking": blocking,
            "reason": reason,
        })
    duplicates = int(market.duplicated(PRIMARY_KEY).sum()) if not market.empty else 0
    placeholder_rows_in_analytics = def_count_price_placeholders(market)
    placeholder_rows_quarantined = int(quarantine_summary.get("total_placeholder_rows", 0))
    effective_coverage = round(float(market["analysis_close"].notna().mean()), 4) if not market.empty else 0
    native_expected = market["asset_class"].isin(["ETF", "TW_EQUITY", "EQUITY"]) if not market.empty else pd.Series(dtype=bool)
    native_adj_coverage = round(
        float(market.loc[native_expected, "adj_close"].notna().mean()),
        4,
    ) if bool(native_expected.any()) else 0
    precise_rows = int(tables.get("etf_flow_precise", {}).get("rows", 0))
    chip_rows = int(tables.get("chip_daily", {}).get("rows", 0))
    signal_weekend_rows = (
        int(pd.to_datetime(signals["date"], errors="coerce").dt.weekday.ge(5).sum())
        if not signals.empty and "date" in signals.columns else 0
    )
    official_pass = sum(str(row.get("status", "")).startswith("PASS") for row in official_sources)
    isolated_tickers = len({
        row.get("ticker") for row in fetch_errors
        if row.get("severity") == "YELLOW_TICKER_ISOLATED"
    })
    add("market_rows", "GREEN" if len(market) > 0 else "RED", int(len(market)), "> 0", True, "Core market table")
    add("market_pk_duplicates", "GREEN" if duplicates == 0 else "RED", duplicates, "= 0", True, "Composite PK integrity")
    add(
        "price_placeholder_rows_in_analytics",
        "GREEN" if placeholder_rows_in_analytics == 0 else "RED",
        placeholder_rows_in_analytics,
        "= 0",
        True,
        "Rows with both Close and Adj Close missing are not valid price observations",
    )
    add(
        "price_placeholder_rows_quarantined",
        "GREEN",
        placeholder_rows_quarantined,
        "Evidence count; excluded from analytical denominator",
        False,
        "Union-calendar, pre-inception, delisted, and market-holiday placeholders are retained as run evidence counts",
    )
    add("etf_rows", "GREEN" if len(etf_daily) > 0 else "RED", int(len(etf_daily)), "> 0", True, "ETF proxy analytics")
    add("signal_rows", "GREEN" if len(signals) > 0 else "RED", int(len(signals)), "> 0", True, "Cross-asset signals")
    add(
        "signal_weekend_rows",
        "GREEN" if signal_weekend_rows == 0 else "RED",
        signal_weekend_rows,
        "= 0",
        True,
        "Cross-asset signal dates must follow SPY sessions and exclude weekend crypto-only dates",
    )
    add(
        "effective_analysis_price_coverage",
        "GREEN" if effective_coverage >= 0.99 else "RED",
        effective_coverage,
        ">= 0.99",
        True,
        "Analysis price uses Adj Close where available and explicitly labelled Close fallback otherwise",
    )
    add(
        "native_adj_close_coverage",
        "GREEN" if native_adj_coverage >= 0.85 else "YELLOW",
        native_adj_coverage,
        ">= 0.85 preferred for ETF/equity rows",
        False,
        "Native adjusted-price availability is reported separately from effective analysis-price continuity",
    )
    no_fake_flow = bool(
        etf_daily.empty
        or "flow_raw" not in etf_daily.columns
        or etf_daily["flow_raw"].isna().all()
    )
    add("no_fake_precise_flow", "GREEN" if no_fake_flow else "RED", no_fake_flow, "True unless AUM/shares evidence", True, "Methodology integrity")
    add("etf_flow_precise_rows", "GREEN" if precise_rows > 0 else "YELLOW", precise_rows, "Optional; > 0 only with AUM/shares evidence", False, "No fabricated creation/redemption flow")
    add("chip_daily_rows", "GREEN" if chip_rows > 0 else "YELLOW", chip_rows, "Optional until official schema normalization passes", False, "Raw official evidence remains retained")
    add("official_sources_available", "GREEN" if official_pass > 0 else "YELLOW", official_pass, ">= 1 preferred", False, "Network/date/schema dependent")
    add("isolated_ticker_failures", "GREEN" if isolated_tickers == 0 else "YELLOW", isolated_tickers, "= 0 preferred", False, "Individual unavailable tickers do not invalidate successful instruments")
    add(
        "historical_only_live_fetch_exclusion",
        "GREEN",
        len(HISTORICAL_ONLY_TICKERS),
        "Configured and excluded from live fetch",
        False,
        "Existing historical rows remain retained; delisted tickers are not repeatedly requested",
    )
    return checks


def def_build_dashboard(path: Path, logo_name: str) -> None:
    html = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
	<title>Veritas MarketFlow Risk Intelligence Suite v0112</title>
<style>
:root{--bg:#f4f6f8;--card:#fff;--ink:#17212b;--muted:#65717e;--line:#d9e0e6;--green:#14866d;--blue:#2768bd;--amber:#b86b0c;--red:#c33d36;--violet:#6657bd}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,"Noto Sans TC","Segoe UI",sans-serif}
header{background:#111a22;color:#f8fafc;padding:18px 28px;display:flex;gap:18px;align-items:center}header img{width:68px;height:68px;object-fit:contain}h1{font-size:21px;margin:0 0 4px}header p{margin:0;color:#adbac7;font-size:12px}
main{padding:20px;max-width:1600px;margin:auto}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
button{border:0;border-radius:8px;background:var(--blue);color:#fff;padding:10px 16px;font-weight:650;cursor:pointer}.ghost{background:#53606c}.stamp{margin-left:auto;color:var(--muted);font-size:12px;padding:10px}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;box-shadow:0 1px 2px #15202b0a}
.metric .label{font-size:11px;color:var(--muted);text-transform:uppercase}.metric .value{font-size:26px;font-weight:720;margin-top:6px}.metric .sub{font-size:11px;color:var(--muted)}
.wide{grid-column:span 3}.full{grid-column:1/-1}h2{font-size:14px;margin:0 0 10px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;border-bottom:1px solid var(--line);padding:7px 6px}th{color:var(--muted);font-weight:650}
.pill{display:inline-block;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:700}.GREEN,.PASS,.ROUND_PASS{background:#d9f2e9;color:#08745b}.YELLOW{background:#fff0cf;color:#8a5700}.RED,.FAIL{background:#ffe1df;color:#a52b25}
.note{font-size:11px;color:var(--muted);line-height:1.55}.error{color:var(--red)}@media(max-width:1000px){.grid{grid-template-columns:repeat(2,1fr)}.wide{grid-column:span 2}}@media(max-width:620px){.grid{grid-template-columns:1fr}.wide{grid-column:span 1}.stamp{margin-left:0}}
</style></head><body>
	<header>__LOGO__<div><h1>Veritas MarketFlow Risk Intelligence Suite v0112</h1><p>Global Capital Flow · Taiwan Rotation · FOMO · Cross-Asset Risk — REAL PRICE DATA · VDF/VRN VERIFIED · PROXY SIGNALS</p></div></header>
<main><div class="toolbar"><button onclick="loadAll()">重新整理</button><button class="ghost" onclick="window.open('/api/v1/governance/gate')">Gate JSON</button><button class="ghost" onclick="window.open('/api/v1/status')">Status JSON</button><button class="ghost" onclick="window.open('/api/v1/runtime/status')">VDF/VRN JSON</button><span class="stamp" id="stamp">載入中…</span></div>
<section class="grid">
<div class="card metric"><div class="label">Governance Gate</div><div class="value" id="gate">—</div><div class="sub">fail-closed</div></div>
<div class="card metric"><div class="label">Market Rows</div><div class="value" id="rows">—</div><div class="sub">DuckDB / Parquet</div></div>
<div class="card metric"><div class="label">Tickers</div><div class="value" id="tickers">—</div><div class="sub">global + Taiwan</div></div>
<div class="card metric"><div class="label">ETF Rows</div><div class="value" id="etfrows">—</div><div class="sub">proxy signals</div></div>
	<div class="card metric"><div class="label">VDF Runtime</div><div class="value" id="vdf">—</div><div class="sub">DataHub read-only gate</div></div>
	<div class="card metric"><div class="label">VRN Runtime</div><div class="value" id="vrn">—</div><div class="sub">7/7 supportive module bootstrap</div></div>
	<div class="card metric"><div class="label">US / Global As-of</div><div class="value" id="usasof">—</div><div class="sub">SPY session · YYYY-MM-DD</div></div>
	<div class="card metric"><div class="label">Taiwan As-of</div><div class="value" id="twasof">—</div><div class="sub">TW equity · YYYY-MM-DD</div></div>
	<div class="card metric"><div class="label">Quality RED</div><div class="value" id="qred">—</div><div class="sub">must be zero</div></div>
	<div class="card wide"><h2>跨資產複合訊號（SPY 有效交易日）</h2><table id="signals"><thead><tr><th>日期</th><th>Risk On/Off</th><th>HY Proxy</th><th>Growth-Value</th><th>EM Rotation</th><th>Semicon</th></tr></thead><tbody></tbody></table></div>
	<div class="card wide"><h2>ETF 資金壓力代理</h2><table id="etfs"><thead><tr><th>Ticker</th><th>日期</th><th>1 Obs</th><th>5 Obs</th><th>20 Obs</th><th>Vol Chg</th><th>Dollar Vol</th><th>DVOL Ratio</th><th>PV Signal</th></tr></thead><tbody></tbody></table><p class="note">Obs = 有效交易觀測，不是曆日。PV Signal 由報酬方向與成交量日增幅 &gt; 20% 共同觸發；DVOL Ratio 僅供量能背景判讀。</p></div>
	<div class="card wide"><h2>台股個股行情</h2><table id="taiwan"><thead><tr><th>Name (Ticker)</th><th>日期</th><th>Analysis Close</th><th>Price Method</th><th>Volume</th><th>Dollar Vol</th></tr></thead><tbody></tbody></table></div>
	<div class="card wide"><h2>Historical-only Ticker</h2><table id="historical"><thead><tr><th>Ticker</th><th>最後有效日</th><th>Analysis Close</th><th>狀態</th></tr></thead><tbody></tbody></table></div>
<div class="card wide"><h2>官方資料來源狀態</h2><table id="official"><thead><tr><th>來源</th><th>狀態</th><th>日期</th><th>正規化</th></tr></thead><tbody></tbody></table></div>
<div class="card full"><h2>資料品質與方法邊界</h2><div id="quality"></div><p class="note">Dollar volume、價量背離、RS、Risk-On/Off 均為市場壓力代理，不等同 ETF creation/redemption 淨流量。只有 AUM 或 shares outstanding 具可靠歷史證據時才允許寫入 flow_raw。法人累積買賣超不得冒充持股率；融資維持率不得由不完整市場彙總欄位偽造。</p></div>
</section></main>
<script>
const fmt=x=>x===null||x===undefined||Number.isNaN(Number(x))?'—':Number(x).toLocaleString(undefined,{maximumFractionDigits:4});
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function getj(u){const r=await fetch(u,{cache:'no-store'});if(!r.ok)throw new Error(`${u}: HTTP ${r.status}`);return r.json()}
function renderRows(id,data,cols){document.querySelector(`#${id} tbody`).innerHTML=data.map(r=>`<tr>${cols.map(c=>`<td>${esc(c(r))}</td>`).join('')}</tr>`).join('')}
async function loadAll(){try{
	 const [s,g,rt,sg,e,tw,hist,off,q]=await Promise.all(['/api/v1/status','/api/v1/governance/gate','/api/v1/runtime/status','/api/v1/signals/latest','/api/v1/etf/flows','/api/v1/taiwan/latest','/api/v1/taiwan/historical-only','/api/v1/taiwan/official-status','/api/v1/quality'].map(getj));
	 document.getElementById('gate').textContent=g.gate;document.getElementById('rows').textContent=fmt(s.market_rows);document.getElementById('tickers').textContent=fmt(s.tickers);document.getElementById('etfrows').textContent=fmt(s.etf_rows);document.getElementById('vdf').textContent=rt.vdf?.status||'BLOCKED';document.getElementById('vrn').textContent=rt.vrn?.status||'BLOCKED';document.getElementById('usasof').textContent=s.us_global_asof||'—';document.getElementById('twasof').textContent=s.taiwan_asof||'—';document.getElementById('qred').textContent=q.filter(x=>x.status==='RED').length;document.getElementById('stamp').textContent='更新 '+new Date().toLocaleString();
 renderRows('signals',sg,[r=>r.date,r=>fmt(r.risk_on_off),r=>fmt(r.hy_spread_proxy),r=>fmt(r.growth_vs_value),r=>fmt(r.em_rotation),r=>fmt(r.semicon_momentum)]);
	 renderRows('etfs',e,[r=>r.ticker,r=>r.date,r=>fmt(r.ret_1d),r=>fmt(r.ret_5d),r=>fmt(r.ret_20d),r=>fmt(r.vol_chg),r=>fmt(r.dollar_vol),r=>fmt(r.dvol_ratio),r=>r.pv_signal]);
	 renderRows('taiwan',tw,[r=>(r.name?`${r.name} (${r.ticker})`:r.ticker),r=>r.date,r=>fmt(r.analysis_close),r=>r.analysis_price_method,r=>fmt(r.volume),r=>fmt(r.dollar_vol)]);
	 renderRows('historical',hist,[r=>r.ticker,r=>r.date,r=>fmt(r.analysis_close),r=>r.historical_status]);
 renderRows('official',off,[r=>r.source,r=>r.status,r=>r.date,r=>r.normalization]);
 document.getElementById('quality').innerHTML='<table><thead><tr><th>Check</th><th>Status</th><th>Value</th><th>Threshold</th></tr></thead><tbody>'+q.map(r=>`<tr><td>${esc(r.check)}</td><td><span class="pill ${esc(r.status)}">${esc(r.status)}</span></td><td>${esc(r.value)}</td><td>${esc(r.threshold)}</td></tr>`).join('')+'</tbody></table>';
 }catch(err){document.getElementById('stamp').innerHTML='<span class="error">'+esc(err.message)+'</span>'}}
loadAll();setInterval(loadAll,60000);
</script></body></html>'''
    logo = f'<img src="/logo" alt="Veritas">' if logo_name else ""
    path.write_text(html.replace("__LOGO__", logo), encoding="utf-8")


def def_html_report(path: Path, manifest: dict) -> None:
    quality_rows = "".join(
        f"<tr><td>{row['check']}</td><td class='{row['status']}'>{row['status']}</td><td>{row['value']}</td><td>{row['threshold']}</td><td>{row.get('blocking')}</td><td>{row.get('reason','')}</td></tr>"
        for row in manifest.get("quality", [])
    )
    source_rows = "".join(
        f"<tr><td>{row['source']}</td><td class='{row['status']}'>{row['status']}</td><td>{row['date']}</td><td>{row['normalization']}</td></tr>"
        for row in manifest.get("official_sources", [])
    )
    table_rows = "".join(
        f"<tr><td>{name}</td><td>{detail.get('rows','')}</td><td>{detail.get('min_date','')}</td><td>{detail.get('max_date','')}</td><td>{detail.get('duplicate_pk','')}</td></tr>"
        for name, detail in manifest.get("tables", {}).items() if isinstance(detail, dict)
    )
    html = f"""<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA v0112 Integration Evidence</title>
<style>body{{font-family:Segoe UI,sans-serif;background:#f4f6f8;color:#17212b;margin:24px}}section{{background:white;border:1px solid #d9e0e6;border-radius:10px;padding:16px;margin:12px 0}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:7px;border-bottom:1px solid #ddd;text-align:left}}.GREEN,.PASS{{color:#08745b}}.RED,.FAIL{{color:#b42318}}.YELLOW{{color:#9a6700}}code{{background:#eef2f5;padding:2px 5px}}</style></head><body>
<h1>VIA MarketFlow + VDF/VRN All-in-One v0112</h1><p>Gate: <strong>{manifest.get('gate')}</strong> · Generated: {manifest.get('generated_utc')}</p>
<section><h2>Policy</h2><p>run-local evidence / append-only snapshots / no canonical overwrite / no dot-source / no canonical Runtime Bridge activation</p></section>
<section><h2>Quantity Validation</h2><table><tr><th>Table</th><th>Rows</th><th>Min date</th><th>Max date</th><th>Duplicate PK</th></tr>{table_rows}</table></section>
<section><h2>Quality Matrix</h2><table><tr><th>Check</th><th>Status</th><th>Value</th><th>Threshold</th><th>Blocking</th><th>Reason</th></tr>{quality_rows}</table></section>
<section><h2>Official Source Matrix</h2><table><tr><th>Source</th><th>Status</th><th>Date</th><th>Normalization</th></tr>{source_rows}</table></section>
<section><h2>Method Boundary</h2><p>ETF dollar-volume / PV / RS fields are proxies. <code>flow_raw</code> remains null without AUM or shares evidence.</p></section>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def def_run_pipeline(args: argparse.Namespace) -> dict:
    data_root = Path(args.data_root)
    run_root = Path(args.run_root)
    data_root.mkdir(parents=True, exist_ok=True)
    run_root.mkdir(parents=True, exist_ok=True)
    heartbeat = run_root / "heartbeat.json"
    def_write_json(heartbeat, {"stage": "START", "updated_utc": def_utc_now()})
    market_path = data_root / "parquet" / "market_daily"
    existing = def_read_existing(market_path)
    existing_placeholder_rows = def_count_price_placeholders(existing)
    tickers = def_load_tickers(args.ticker_file)
    start = def_incremental_start(existing, args.start)
    incoming = pd.DataFrame()
    fetch_errors = []
    if args.fetch_market:
        incoming, fetch_errors = def_fetch_yfinance(
            tickers,
            start,
            args.end,
            args.batch_size,
            args.max_workers,
            args.timeout,
            heartbeat,
        )
        incoming_placeholder_rows = def_count_price_placeholders(incoming)
        incoming = def_enrich_prices(incoming)
    else:
        incoming_placeholder_rows = 0
    quarantine_summary = {
        "policy": "EXCLUDE_FROM_ANALYTICS_RETAIN_COUNTS_IN_RUN_EVIDENCE",
        "reason": "YFINANCE_MULTI_TICKER_UNION_CALENDAR_EMPTY_PRICE_PLACEHOLDER",
        "existing_placeholder_rows": existing_placeholder_rows,
        "incoming_placeholder_rows": incoming_placeholder_rows,
        "total_placeholder_rows": existing_placeholder_rows + incoming_placeholder_rows,
    }
    market = def_merge_incremental(existing, incoming)
    if not market.empty:
        market = def_enrich_prices(market)
    etf_daily = def_calculate_etf_daily(market)
    signals = def_calculate_signals(market, etf_daily)
    official_sources = def_fetch_tw_official(data_root / "official_raw", args.timeout) if args.fetch_tw else []
    tables = def_write_tables(data_root, market, etf_daily, signals, args.stock_database)
    quality = def_quality_matrix(
        market,
        etf_daily,
        signals,
        tables,
        fetch_errors,
        official_sources,
        quarantine_summary,
    )
    blocking_red_count = sum(row["status"] == "RED" and row.get("blocking", True) for row in quality)
    yellow_count = sum(row["status"] == "YELLOW" for row in quality)
    blocking_reasons = [
        {
            "check": row["check"],
            "value": row["value"],
            "threshold": row["threshold"],
            "reason": row["reason"],
        }
        for row in quality
        if row["status"] == "RED" and row.get("blocking", True)
    ]
    if blocking_red_count:
        gate = "DATA_BLOCKED_QUALITY_RED"
    elif yellow_count:
        gate = "DATA_READY_DEGRADED_READ_ONLY_API"
    else:
        gate = "DATA_READY_READ_ONLY_API"
    manifest = {
        "schema": "via.marketflow.manifest.v1",
        "generated_utc": def_utc_now(),
        "version": APP_VERSION,
        "gate": gate,
        "ticker_count": len(tickers),
        "incremental_start": start,
        "configured_start": args.start,
        "fetch_errors": fetch_errors,
        "tables": tables,
        "quality": quality,
        "quality_summary": {
            "blocking_red": blocking_red_count,
            "yellow": yellow_count,
            "service_allowed": blocking_red_count == 0,
            "blocking_reasons": blocking_reasons,
        },
        "historical_only_tickers": HISTORICAL_ONLY_TICKERS,
        "price_placeholder_quarantine": quarantine_summary,
        "official_sources": official_sources,
        "methodology": {
            "m1_dollar_volume": "PROXY",
            "m2_price_volume": "PROXY",
            "m3_relative_strength": "PROXY",
            "m4_aum_flow": "ONLY_WHEN_AUM_OR_SHARES_EVIDENCE",
            "precise_flow_generated": False,
        },
        "canonical_mutation": False,
        "canonical_runtime_bridge_activation": False,
    }
    def_write_json(data_root / "manifest.json", manifest)
    def_write_json(run_root / "pipeline_manifest.json", manifest)
    def_html_report(run_root / "integration_evidence.html", manifest)
    def_write_json(heartbeat, {"stage": "COMPLETE", "gate": gate, "updated_utc": def_utc_now()})
    return manifest


def def_records(frame: pd.DataFrame, limit: int = 100) -> list[dict]:
    if frame.empty:
        return []
    result = frame.tail(limit).copy()
    for column in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[column]):
            result[column] = result[column].dt.strftime("%Y-%m-%d")
    result = result.replace([np.inf, -np.inf], np.nan)
    return json.loads(result.to_json(orient="records", date_format="iso"))


def def_query(database: Path, sql: str) -> pd.DataFrame:
    if not database.is_file():
        return pd.DataFrame()
    con = duckdb.connect(str(database), read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def def_create_api(data_root: Path, run_root: Path, dashboard: Path, logo: Path | None) -> FastAPI:
    app = FastAPI(title="VIA MarketFlow API", version=APP_VERSION)
    database = data_root / "via_marketflow.duckdb"

    def manifest() -> dict:
        path = data_root / "manifest.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"gate": "NO_MANIFEST"}

    def runtime_status() -> dict:
        path = run_root / "vdf_vrn_runtime_status.json"
        api_path = run_root / "api_supportive_runtime.json"
        if not path.is_file():
            return {
                "overall_gate": "VDF_VRN_RUNTIME_STATUS_MISSING",
                "ready": False,
                "vdf": {"status": "BLOCKED", "gate": "VDF_STATUS_MISSING"},
                "vrn": {"status": "BLOCKED", "gate": "VRN_STATUS_MISSING"},
            }
        try:
            runtime = json.loads(path.read_text(encoding="utf-8"))
            api_runtime = (
                json.loads(api_path.read_text(encoding="utf-8"))
                if api_path.is_file()
                else {
                    "gate": "API_SUPPORTIVE_RUNTIME_STATUS_MISSING",
                    "ready": False,
                    "expected_count": 7,
                    "imported_count": 0,
                }
            )
            runtime["api_supportive_runtime"] = api_runtime
            runtime["api_supportive_modules_all_imported"] = (
                api_runtime.get("ready") is True
                and int(api_runtime.get("imported_count", 0)) == 7
                and int(api_runtime.get("expected_count", 0)) == 7
            )
            return runtime
        except Exception as exc:
            return {
                "overall_gate": "VDF_VRN_RUNTIME_STATUS_INVALID",
                "ready": False,
                "vdf": {"status": "BLOCKED", "gate": "VDF_STATUS_INVALID"},
                "vrn": {"status": "BLOCKED", "gate": "VRN_STATUS_INVALID"},
                "error": f"{type(exc).__name__}: {exc}",
            }

    @app.get("/", response_class=HTMLResponse)
    def def_root():
        return dashboard.read_text(encoding="utf-8")

    @app.get("/logo")
    def def_logo():
        if not logo or not logo.is_file():
            raise HTTPException(status_code=404, detail="Logo not available")
        return FileResponse(str(logo), media_type="image/png")

    @app.get("/api/v1/status")
    def def_status():
        info = manifest()
        runtime = runtime_status()
        table = info.get("tables", {})
        market_rows = table.get("market_daily", {}).get("rows", 0)
        etf_rows = table.get("etf_daily", {}).get("rows", 0)
        latest = table.get("market_daily", {}).get("max_date", "")
        tickers = 0
        us_global_asof = ""
        taiwan_asof = ""
        try:
            tickers = int(def_query(database, "select count(distinct ticker) n from market_daily").iloc[0]["n"])
            us_frame = def_query(
                database,
                "select strftime(max(date), '%Y-%m-%d') as asof from market_daily where ticker='SPY'",
            )
            tw_frame = def_query(
                database,
                """select strftime(max(date), '%Y-%m-%d') as asof
                   from stock_price where ticker not in ('1704.TW')""",
            )
            us_global_asof = str(us_frame.iloc[0]["asof"] or "") if not us_frame.empty else ""
            taiwan_asof = str(tw_frame.iloc[0]["asof"] or "") if not tw_frame.empty else ""
        except Exception:
            pass
        return {
            "gate": info.get("gate"),
            "market_rows": market_rows,
            "etf_rows": etf_rows,
            "tickers": tickers,
            "latest_date": latest,
            "us_global_asof": us_global_asof,
            "taiwan_asof": taiwan_asof,
            "signal_calendar": "SPY_TRADING_SESSIONS",
            "vdf_status": runtime.get("vdf", {}).get("status", "BLOCKED"),
            "vrn_status": runtime.get("vrn", {}).get("status", "BLOCKED"),
            "vdf_vrn_gate": runtime.get("overall_gate", "VDF_VRN_RUNTIME_STATUS_MISSING"),
            "supportive_modules_expected": runtime.get("supportive_modules_expected", 7),
            "supportive_modules_imported": runtime.get("supportive_modules_imported", 0),
            "supportive_modules_all_imported": runtime.get("supportive_modules_all_imported", False),
            "api_supportive_modules_all_imported": runtime.get("api_supportive_modules_all_imported", False),
            "api_supportive_gate": runtime.get("api_supportive_runtime", {}).get(
                "gate",
                "API_SUPPORTIVE_RUNTIME_STATUS_MISSING",
            ),
            "generated_utc": info.get("generated_utc"),
        }

    @app.get("/api/v1/runtime/status")
    def def_runtime_status():
        return runtime_status()

    @app.get("/api/v1/governance/gate")
    def def_gate():
        info = manifest()
        runtime = runtime_status()
        data_ready = info.get("gate") in {"DATA_READY_READ_ONLY_API", "DATA_READY_DEGRADED_READ_ONLY_API"}
        runtime_ready = (
            runtime.get("overall_gate") == "VDF_VRN_RUNTIME_READY"
            and runtime.get("ready") is True
            and runtime.get("supportive_modules_all_imported") is True
            and int(runtime.get("supportive_modules_imported", 0)) == 7
            and int(runtime.get("supportive_modules_expected", 0)) == 7
            and runtime.get("api_supportive_modules_all_imported") is True
        )
        combined_gate = (
            "VDF_VRN_DATA_READY"
            if data_ready and runtime_ready
            else "VDF_VRN_DATA_BLOCKED_FAIL_CLOSED"
        )
        return {
            "gate": combined_gate,
            "data_gate": info.get("gate"),
            "runtime_gate": runtime.get("overall_gate"),
            "canonical_mutation": False,
            "canonical_runtime_bridge_activation": False,
            "run_local_bridge_bootstrap": True,
            "methodology": info.get("methodology", {}),
        }

    @app.get("/api/v1/quality")
    def def_quality():
        return manifest().get("quality", [])

    @app.get("/api/v1/taiwan/official-status")
    def def_official():
        return manifest().get("official_sources", [])

    @app.get("/api/v1/signals/latest")
    def def_signals():
        sql = """select * from etf_signals
                 where signal_completeness > 0
                   and extract('isodow' from date) between 1 and 5
                 order by date desc limit 20"""
        return def_records(def_query(database, sql).sort_values("date"))

    @app.get("/api/v1/etf/flows")
    def def_etf_flows():
        sql = """select date,ticker,ret_1d,ret_5d,ret_20d,vol_chg,dollar_vol,dvol_ratio,pv_signal,rs_vs_spy,flow_raw,flow_method
                 from etf_daily qualify row_number() over(partition by ticker order by date desc)=1
                 order by dollar_vol desc nulls last limit 60"""
        return def_records(def_query(database, sql), 100)

    @app.get("/api/v1/taiwan/latest")
    def def_taiwan():
        sql = """select p.date,p.ticker,coalesce(l.name,'') as name,
                        p.analysis_close,p.analysis_price_method,p.adj_close,p.volume,p.dollar_vol
                 from stock_price p left join stock_list l on p.ticker=l.yf_ticker
                 where p.ticker not in ('1704.TW')
                 qualify row_number() over(partition by p.ticker order by p.date desc)=1
                 order by p.dollar_vol desc nulls last limit 60"""
        return def_records(def_query(database, sql), 100)

    @app.get("/api/v1/taiwan/historical-only")
    def def_taiwan_historical_only():
        sql = """select date,ticker,analysis_close,
                        'HISTORICAL_ONLY_NO_LIVE_FETCH' as historical_status
                 from stock_price where ticker in ('1704.TW')
                 qualify row_number() over(partition by ticker order by date desc)=1
                 order by ticker"""
        return def_records(def_query(database, sql), 100)

    @app.get("/api/v1/market/latest")
    def def_market():
        sql = """select date,ticker,asset_class,category,analysis_close,analysis_price_method,adj_close,volume,dollar_vol
                 from market_daily qualify row_number() over(partition by ticker order by date desc)=1
                 order by asset_class,ticker"""
        return def_records(def_query(database, sql), 500)

    @app.get("/api/v1/commodities")
    def def_commodities():
        return def_records(def_query(database, "select * from commodity_daily order by date desc limit 100"), 100)

    return app


def def_parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("pipeline")
    serve = sub.add_parser("serve")
    for item in (run, serve):
        item.add_argument("--data-root", required=True)
        item.add_argument("--run-root", required=True)
        item.add_argument("--dashboard", required=True)
        item.add_argument("--logo", default="")
    run.add_argument("--start", required=True)
    run.add_argument("--end", default="")
    run.add_argument("--ticker-file", default="")
    run.add_argument("--stock-database", default="")
    run.add_argument("--batch-size", type=int, default=40)
    run.add_argument("--max-workers", type=int, default=6)
    run.add_argument("--timeout", type=int, default=30)
    run.add_argument("--fetch-market", action="store_true")
    run.add_argument("--fetch-tw", action="store_true")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--core-root", required=True)
    return parser.parse_args()


def def_main() -> int:
    args = def_parse_args()
    dashboard = Path(args.dashboard)
    logo = Path(args.logo) if args.logo else None
    if args.command == "pipeline":
        def_build_dashboard(dashboard, logo.name if logo and logo.is_file() else "")
        manifest = def_run_pipeline(args)
        print(json.dumps({
            "gate": manifest["gate"],
            "quality_summary": manifest["quality_summary"],
            "quality": manifest["quality"],
            "tables": manifest["tables"],
        }, ensure_ascii=False))
        return 0 if manifest["gate"] in {"DATA_READY_READ_ONLY_API", "DATA_READY_DEGRADED_READ_ONLY_API"} else 2
    api_supportive_runtime = def_import_api_supportive_runtime(Path(args.core_root))
    def_write_json(
        Path(args.run_root) / "api_supportive_runtime.json",
        api_supportive_runtime,
    )
    if not api_supportive_runtime["ready"]:
        print(json.dumps(api_supportive_runtime, ensure_ascii=False))
        return 3
    app = def_create_api(Path(args.data_root), Path(args.run_root), dashboard, logo)
    app.state.supportive_runtime = api_supportive_runtime
    uvicorn.run(app, host=args.host, port=args.port, log_level="info", access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
'@
}

function def_WriteLauncherReadme {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$RunDir,
        [Parameter(Mandatory)][string]$DataRoot
    )
    $Text = @"
# VIA MarketFlow + VDF/VRN All-in-One v0112

def RunDir: $RunDir
def DataRoot: $DataRoot
def API: http://$LOOPBACK_HOST`:$ApiPort/
def Policy: run-local evidence / append-only snapshots / no canonical overwrite
def VDF/VRN: run-local startup validation enabled
def Canonical Bridge: not activated

The Dashboard displays real DuckDB data. Dollar-volume, price-volume and
relative-strength fields are explicitly labelled as proxies. Precise ETF flow
is not fabricated when AUM/shares history is unavailable.
"@
    def_WriteUtf8NoBom -Path $Path -Content $Text
}

function def_WritePanoramaHtml {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$RoundSummaries,
        [Parameter(Mandatory)][object[]]$CoreRows,
        [Parameter(Mandatory)][string]$Gate,
        [Parameter(Mandatory)][string]$RunDir
    )
    $RoundHtml = foreach ($Round in $RoundSummaries) {
        "<tr><td>$($Round.round)</td><td>$($Round.strategy)</td><td>$($Round.green)</td><td>$($Round.yellow)</td><td>$($Round.red)</td><td>$($Round.hash_drift)</td><td>$($Round.gate)</td></tr>"
    }
    $CoreHtml = foreach ($Row in $CoreRows) {
        "<tr><td>$([Net.WebUtility]::HtmlEncode($Row.Name))</td><td>$($Row.Status)</td><td>$($Row.Bytes)</td><td>$($Row.Copies)</td><td><code>$([Net.WebUtility]::HtmlEncode($Row.AuthorityPath))</code></td></tr>"
    }
    $Html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
	<title>VIA v0112 Governance Matrix</title>
<style>
body{font-family:Segoe UI,sans-serif;background:#f4f6f8;color:#17212b;margin:24px}
section{background:#fff;border:1px solid #d9e0e6;border-radius:10px;padding:16px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:7px;border-bottom:1px solid #ddd;text-align:left}
code{font-size:11px}.GREEN_AST_PASS,.ROUND_PASS{color:#08745b}.RED_AST_FAIL,.ROUND_FAIL_CLOSED{color:#b42318}.YELLOW_EMPTY_ATTACHMENT,.YELLOW_NOT_FOUND{color:#9a6700}
</style></head><body>
	<h1>VIA MarketFlow + VDF/VRN v0112 · Governance Matrix</h1>
<p>Gate: <strong>$Gate</strong></p>
<section><h2>Three-Round Panorama</h2>
<table><tr><th>Round</th><th>Strategy</th><th>Green</th><th>Yellow</th><th>Red</th><th>Hash drift</th><th>Gate</th></tr>
$($RoundHtml -join "`n")</table></section>
<section><h2>Core Authority / AST Matrix</h2>
<table><tr><th>Name</th><th>Status</th><th>Bytes</th><th>Copies</th><th>Authority</th></tr>
$($CoreHtml -join "`n")</table></section>
<section><h2>Authority Decision</h2><p>9 recommendations accepted in run-local overlay; LocalFreeLibs registry excluded as NONBLOCKING_UNOWNED_LEGACY_REGISTRY.</p></section>
<section><h2>Hydra / SSOT Controls</h2><p>No recursive copy, no canonical mutation, no dot-source, no canonical bridge activation. VDF/VRN bootstrap is isolated under the run directory. Run: <code>$([Net.WebUtility]::HtmlEncode($RunDir))</code></p></section>
</body></html>
"@
    def_WriteUtf8NoBom -Path $Path -Content $Html
}

function def_WaitForApi {
    param(
        [Parameter(Mandatory)][string]$Url,
        [int]$TimeoutSeconds = 30
    )
    $Deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $Deadline) {
        try {
            $Response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 3
            if ($Response) { return $Response }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    throw "API 未在 $TimeoutSeconds 秒內就緒：$Url"
}

function def_Main {
    def_WriteBanner -Title "VIA · MARKETFLOW ALL-IN-ONE · $SCRIPT_VERSION"
    $SelfAst = def_TestSelfPowerShellAst
    Write-Host "def PowerShell AST    : $($SelfAst.Status)" -ForegroundColor Green
    $Mutex = def_EnterSingleInstance -MutexName "VIA_MARKETFLOW_ALLINONE_V0111"
    try {
        $TotalSteps = 15
        $Step = 0

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A01 short-path runtime governance"
        if (-not (Test-Path -LiteralPath $VIA_BaseDir -PathType Container)) {
            New-Item -ItemType Directory -Path $VIA_BaseDir -Force | Out-Null
        }
        $UtcStamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss_fff")
        $RunDir = Join-Path $VIA_BaseDir "_via_marketflow_runs\RUN_${UtcStamp}_${SCRIPT_VERSION}_INTEGRATION_PREVIEW"
        $EvidenceDir = Join-Path $RunDir "evidence"
        $RuntimeDir = Join-Path $RunDir "runtime"
        $DataRoot = Join-Path $VIA_BaseDir "_via_marketflow_data"
        foreach ($Dir in @($RunDir, $EvidenceDir, $RuntimeDir, $DataRoot)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        }
        $ApiPort = def_ResolveApiPort -PreferredPort $ApiPort -SearchSpan 20

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A02/A03 resolve optional inputs"
        if (-not $TickerListPath) {
            $TickerListPath = def_ResolveOptionalFile -Candidates @(
                (Join-Path $env:USERPROFILE "OneDrive\桌面\tw_stock\dict\TickerList\AllStockYfinanceTickerList.txt"),
                (Join-Path $env:USERPROFILE "Desktop\tw_stock\dict\TickerList\AllStockYfinanceTickerList.txt")
            )
        }
        if (-not $StockDatabasePath) {
            $StockDatabasePath = def_ResolveOptionalFile -Candidates @(
                (Join-Path $env:USERPROFILE "OneDrive\桌面\tw_stock\dict\TickerList\StockTickerListDatabase.csv"),
                (Join-Path $env:USERPROFILE "Desktop\tw_stock\dict\TickerList\StockTickerListDatabase.csv")
            )
        }
        if (-not $DashboardSourcePath) {
            $DashboardSourcePath = def_ResolveOptionalFile -Candidates @(
                (Join-Path $env:USERPROFILE "Downloads\VPN_v35_Dashboard (3).html"),
                (Join-Path $env:USERPROFILE "Downloads\VPN_v35_Dashboard.html"),
                (Join-Path $VIA_BaseDir "VPN_v35_Dashboard (3).html"),
                (Join-Path $VIA_BaseDir "VPN_v35_Dashboard.html")
            )
        }
        if (-not $LogoSourcePath) {
            $LogoSourcePath = def_ResolveOptionalFile -Candidates @(
                (Join-Path $env:USERPROFILE "Downloads\Veritas_nobg.png"),
                (Join-Path $VIA_BaseDir "Veritas_nobg.png"),
                (Join-Path $VIA_BaseDir "supportive modules\Veritas_nobg.png")
            )
        }

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A04/A05 hash-state and SSOT authority"
        $ScriptHash = def_GetScriptHash
        $PythonExe = def_SelectPython
        $CoreRows = def_FindCoreAuthorityFiles -BaseDir $VIA_BaseDir
        def_WriteAuthorityOverlay `
            -Path (Join-Path $EvidenceDir "01_authority_overlay_ACCEPTED_RUN_LOCAL.json") `
            -CoreRows $CoreRows `
            -ScriptHash $ScriptHash

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A06/A07 size and encoding gates"
        $InputManifest = [ordered]@{
            generated_utc = [DateTime]::UtcNow.ToString("o")
            via_base = $VIA_BaseDir
            run_dir = $RunDir
            data_root = $DataRoot
            python = $PythonExe
            script_sha256 = $ScriptHash
            ticker_list = $TickerListPath
            stock_database = $StockDatabasePath
            original_dashboard = $DashboardSourcePath
            logo = $LogoSourcePath
            original_dashboard_used_as_runtime = $false
            reason = "Original runScan uses simulation; real dashboard is generated separately."
            accelerators = $ACCELERATORS
        }
        def_WriteJson -Data $InputManifest -Path (Join-Path $EvidenceDir "02_input_manifest.json") -Depth 20

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A08 AST no-import probe"
        $AstRows = def_InvokeAstProbe -PythonExe $PythonExe -CoreRows $CoreRows
        def_WriteJson -Data $AstRows -Path (Join-Path $EvidenceDir "03_core_ast_matrix.json") -Depth 20

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "Three-round panoramic validation"
        $RoundSummaries = def_InvokeThreeRoundPanorama `
            -PythonExe $PythonExe `
            -CoreRows $CoreRows `
            -EvidenceDir $EvidenceDir
        $BlockingCore = @($AstRows | Where-Object { $_.Status -like "RED*" }).Count
        $HashDrift = @($RoundSummaries | Where-Object { $_.hash_drift -gt 0 }).Count
        $GovernanceGate = if ($BlockingCore -eq 0 -and $HashDrift -eq 0) {
            "READY_FOR_DATA_INTEGRATION_PREVIEW"
        }
        else {
            "BLOCKED_GOVERNANCE_FAIL_CLOSED"
        }
        def_WritePanoramaHtml `
            -Path (Join-Path $RunDir "governance_matrix.html") `
            -RoundSummaries $RoundSummaries `
            -CoreRows $AstRows `
            -Gate $GovernanceGate `
            -RunDir $RunDir
        if ($GovernanceGate -ne "READY_FOR_DATA_INTEGRATION_PREVIEW") {
            throw "治理 Gate 未通過：$GovernanceGate。未建立資料服務。"
        }

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A09 JSON flatten / Python engine generation"
        $EnginePath = Join-Path $RuntimeDir "via_marketflow_engine.py"
        def_WriteUtf8NoBom -Path $EnginePath -Content (def_GetEmbeddedPython)
        $EngineProbeCode = @'
import ast, pathlib, sys
p = pathlib.Path(sys.argv[1])
ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
print("ENGINE_AST_PASS")
'@
        $EngineProbe = & $PythonExe -c $EngineProbeCode $EnginePath 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "內嵌 Python 引擎 AST 失敗：$($EngineProbe -join ' ')"
        }

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A10/A14 run-local dependency validation"
        $Runtime = def_EnsurePackages -PythonExe $PythonExe -RuntimeRoot (Join-Path $DataRoot "_runtime")
        $PythonExe = $Runtime.Python
        def_WriteJson -Data $Runtime -Path (Join-Path $EvidenceDir "04_python_runtime.json") -Depth 10

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A11 incremental max-date market intake"
        $DashboardPath = Join-Path $RuntimeDir "index.html"
        $LogoRuntimePath = ""
        if ($LogoSourcePath) {
            $LogoRuntimePath = Join-Path $RuntimeDir "Veritas_nobg.png"
            Copy-Item -LiteralPath $LogoSourcePath -Destination $LogoRuntimePath -Force
        }
        $PipelineArgs = @(
            $EnginePath, "pipeline",
            "--data-root", $DataRoot,
            "--run-root", $RunDir,
            "--dashboard", $DashboardPath,
            "--start", $StartDate,
            "--batch-size", "$BatchSize",
            "--max-workers", "$MaxWorkers",
            "--timeout", "$RequestTimeoutSec"
        )
        if ($EndDate) { $PipelineArgs += @("--end", $EndDate) }
        if ($TickerListPath) { $PipelineArgs += @("--ticker-file", $TickerListPath) }
        if ($StockDatabasePath) { $PipelineArgs += @("--stock-database", $StockDatabasePath) }
        if ($LogoRuntimePath) { $PipelineArgs += @("--logo", $LogoRuntimePath) }
        if ($FetchMarketData) { $PipelineArgs += "--fetch-market" }
        if ($FetchTaiwanOfficial) { $PipelineArgs += "--fetch-tw" }
        & $PythonExe @PipelineArgs 2>&1 | Tee-Object -FilePath (Join-Path $RunDir "pipeline_console.log")
        $PipelineExit = $LASTEXITCODE
        if ($PipelineExit -ne 0) {
            $FailedManifestPath = Join-Path $RunDir "pipeline_manifest.json"
            if (Test-Path -LiteralPath $FailedManifestPath -PathType Leaf) {
                $FailedManifest = Get-Content -LiteralPath $FailedManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
                Write-Host ""
                Write-Host "def DATA QUALITY BLOCKING REASONS" -ForegroundColor Red
                foreach ($Reason in @($FailedManifest.quality_summary.blocking_reasons)) {
                    Write-Host (
                        "def {0} : value={1} threshold={2} reason={3}" -f `
                            $Reason.check, $Reason.value, $Reason.threshold, $Reason.reason
                    ) -ForegroundColor Red
                }
                Write-Host "def Yellow count : $($FailedManifest.quality_summary.yellow)" -ForegroundColor Yellow
                Write-Host "def Evidence     : $FailedManifestPath" -ForegroundColor DarkGray
            }
            throw "資料 Pipeline fail-closed，exit=$PipelineExit。請查看 integration_evidence.html 與 pipeline_console.log。"
        }

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A12 heartbeat and quantity validation"
        $ManifestPath = Join-Path $DataRoot "manifest.json"
        if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
            throw "Pipeline 未產生 manifest.json。"
        }
        $Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($Manifest.gate -notin @("DATA_READY_READ_ONLY_API", "DATA_READY_DEGRADED_READ_ONLY_API")) {
            throw "資料品質 Gate 未通過：$($Manifest.gate)"
        }

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "VDF DataHub + VRN core run-local startup"
        if ($ValidateVdfVrnRuntime) {
            $RuntimeStatus = def_InvokeVdfVrnStartup `
                -PythonExe $PythonExe `
                -CoreRows $AstRows `
                -RuntimeDir $RuntimeDir `
                -RunDir $RunDir `
                -DataRoot $DataRoot `
                -EvidenceDir $EvidenceDir
        }
        else {
            $RuntimeStatus = [pscustomobject]@{
                schema = "via.vdf_vrn.runtime.status.v2"
                overall_gate = "VDF_VRN_RUNTIME_VALIDATION_DISABLED"
                ready = $false
                vdf = [pscustomobject]@{ status = "BLOCKED"; gate = "VDF_VALIDATION_DISABLED" }
                vrn = [pscustomobject]@{ status = "BLOCKED"; gate = "VRN_VALIDATION_DISABLED" }
                supportive_modules_expected = 7
                supportive_modules_imported = 0
                supportive_modules_all_imported = $false
                canonical_mutation = $false
                canonical_bridge_activation = $false
                run_local_bridge_bootstrap = $false
            }
            def_WriteJson -Data $RuntimeStatus -Path (Join-Path $RunDir "vdf_vrn_runtime_status.json") -Depth 20
        }
        $RuntimeStatus = def_NormalizeRuntimeStatus -Candidate $RuntimeStatus
        if (-not [bool]$RuntimeStatus.ready) {
            Write-Host "def VDF Gate : $($RuntimeStatus.vdf.gate)" -ForegroundColor Red
            Write-Host "def VRN Gate : $($RuntimeStatus.vrn.gate)" -ForegroundColor Red
            throw "VDF/VRN runtime Gate 未通過：$($RuntimeStatus.overall_gate)"
        }

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A13 HTML UI matrices"
        def_WriteLauncherReadme `
            -Path (Join-Path $RunDir "README.md") `
            -RunDir $RunDir `
            -DataRoot $DataRoot

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "A15 localhost read-only API"
        $ApiArgs = @(
            $EnginePath, "serve",
            "--data-root", $DataRoot,
            "--run-root", $RunDir,
            "--dashboard", $DashboardPath,
            "--host", $LOOPBACK_HOST,
            "--port", "$ApiPort",
            "--core-root", (Join-Path $RuntimeDir "core_runtime")
        )
        if ($LogoRuntimePath) { $ApiArgs += @("--logo", $LogoRuntimePath) }
        $StdOut = Join-Path $RunDir "api_stdout.log"
        $StdErr = Join-Path $RunDir "api_stderr.log"
        $ApiProcess = Start-Process `
            -FilePath $PythonExe `
            -ArgumentList $ApiArgs `
            -WorkingDirectory $RuntimeDir `
            -RedirectStandardOutput $StdOut `
            -RedirectStandardError $StdErr `
            -WindowStyle Hidden `
            -PassThru
        def_WriteJson -Data ([ordered]@{
            pid = $ApiProcess.Id
            host = $LOOPBACK_HOST
            port = $ApiPort
            started_utc = [DateTime]::UtcNow.ToString("o")
            scope = "LOCALHOST_READ_ONLY_API"
            canonical_runtime_bridge = $false
            run_local_vdf_vrn_bootstrap = $true
        }) -Path (Join-Path $RunDir "api_process.json")
        $ApiStatus = def_WaitForApi -Url "http://$LOOPBACK_HOST`:$ApiPort/api/v1/status" -TimeoutSeconds 45

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "Final fail-closed verification"
        if (
            $null -eq $ApiStatus.PSObject.Properties["api_supportive_modules_all_imported"] -or
            -not [bool]$ApiStatus.api_supportive_modules_all_imported
        ) {
            throw "API service 未持續掛載 7/7 supportive modules，已停止 READY Gate。"
        }
        $Final = [ordered]@{
            generated_utc = [DateTime]::UtcNow.ToString("o")
            gate = "INTEGRATION_RUNNING_VDF_VRN_READY"
            governance_gate = $GovernanceGate
            data_gate = $Manifest.gate
            api_status = $ApiStatus
            run_dir = $RunDir
            data_root = $DataRoot
            dashboard_url = "http://$LOOPBACK_HOST`:$ApiPort/"
            canonical_mutation = $false
            via_modules_imported = [bool]$RuntimeStatus.supportive_modules_all_imported
            supportive_modules_expected = $RuntimeStatus.supportive_modules_expected
            supportive_modules_imported = $RuntimeStatus.supportive_modules_imported
            api_supportive_modules_all_imported = [bool]$ApiStatus.api_supportive_modules_all_imported
            api_supportive_gate = $ApiStatus.api_supportive_gate
            vdf_vrn_runtime_gate = $RuntimeStatus.overall_gate
            vdf_status = $RuntimeStatus.vdf.status
            vrn_status = $RuntimeStatus.vrn.status
            canonical_runtime_bridge_activation = $false
            run_local_bridge_bootstrap = $true
            precise_etf_flow_fabricated = $false
        }
        def_WriteJson -Data $Final -Path (Join-Path $RunDir "FINAL_STATUS.json") -Depth 20

        $Step++; def_WriteProgress -Step $Step -Total $TotalSteps -Message "Complete"
        def_WriteBanner -Title "VIA MARKETFLOW RESULT"
        Write-Host "def Gate              : $($Final.gate)" -ForegroundColor Green
        Write-Host "def Governance        : $GovernanceGate" -ForegroundColor Green
        Write-Host "def Data              : $($Manifest.gate)" -ForegroundColor Green
        Write-Host "def VDF               : $($RuntimeStatus.vdf.gate)" -ForegroundColor Green
        Write-Host "def VRN               : $($RuntimeStatus.vrn.gate)" -ForegroundColor Green
        Write-Host "def Supportive modules: $($RuntimeStatus.supportive_modules_imported)/$($RuntimeStatus.supportive_modules_expected) imported" -ForegroundColor Green
        Write-Host "def Market rows       : $($ApiStatus.market_rows)" -ForegroundColor White
        Write-Host "def ETF rows          : $($ApiStatus.etf_rows)" -ForegroundColor White
        Write-Host "def Tickers           : $($ApiStatus.tickers)" -ForegroundColor White
        Write-Host "def Blocking RED      : $($Manifest.quality_summary.blocking_red)" -ForegroundColor Green
        Write-Host "def Yellow            : $($Manifest.quality_summary.yellow)" -ForegroundColor Yellow
        Write-Host "def Dashboard         : http://$LOOPBACK_HOST`:$ApiPort/" -ForegroundColor Cyan
        Write-Host "def RunDir            : $RunDir" -ForegroundColor DarkGray
        Write-Host "def Canonical mutation: False" -ForegroundColor Yellow
        Write-Host "def Canonical Bridge  : False" -ForegroundColor Yellow
        Write-Host "def Run-local bootstrap: True" -ForegroundColor Green
        if ($OpenDashboard) {
            Start-Process "http://$LOOPBACK_HOST`:$ApiPort/"
        }
    }
    finally {
        if ($Mutex) {
            try { $Mutex.ReleaseMutex() } catch {}
            $Mutex.Dispose()
        }
    }
}

try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host "def OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No canonical mutation or canonical Runtime Bridge activation was attempted." -ForegroundColor Yellow
}
