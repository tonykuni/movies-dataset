# =============================================================================
# def VDF · NexusCore Panorama Three-Round Activation Gate
# VERITAS INTELLIGENCE ANALYTICS
# Purpose:
#   1) Confirm VDF functional modules and NexusCore supportive modules exist.
#   2) Build a VDF Nexus activation bridge without modifying original source files.
#   3) Parse VIA_data_manifest.json and fetch yfinance / FRED series locally.
#   4) Export JSON / CSV / Parquet + HTML Matrix report.
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# =============================================================================
# def PARAMS · edit here only
# =============================================================================
$def_PARAM_VDF_BASE = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF"
$def_PARAM_SUPPORT_BASE = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules"

# Manifest candidates: save the uploaded attachment as VIA_data_manifest.json in any of these locations.
$def_PARAM_MANIFEST_EXPLICIT = ""
$def_PARAM_MANIFEST_CANDIDATES = @(
    (Join-Path $def_PARAM_VDF_BASE "VIA_data_manifest.json"),
    (Join-Path $env:USERPROFILE "Downloads\VIA_data_manifest.json"),
    (Join-Path $env:USERPROFILE "Desktop\VIA_data_manifest.json"),
    (Join-Path $env:USERPROFILE "OneDrive\Desktop\VIA_data_manifest.json")
)

$def_PARAM_RUN_ROOT = Join-Path $def_PARAM_VDF_BASE "_vdf_system\macro_manifest_fetch_runs"
$def_PARAM_BRIDGE_ROOT = Join-Path $def_PARAM_VDF_BASE "_vdf_system\bridge"

$def_PARAM_ENABLE_NEXUSCORE_INVOKE = $true
$def_PARAM_ENABLE_POLYGLOT_INVOKE = $true
$def_PARAM_ENABLE_PIP_INSTALL_MISSING = $true
$def_PARAM_ENABLE_NETWORK_FETCH = $true
$def_PARAM_OPEN_HTML_REPORT = $true
$def_PARAM_KEEP_POWERSHELL_OPEN = $true

# Fetch start policy:
#   ALL       = use manifest.config.period_starts.ALL, normally 2005-01-03.
#   DATASTART = use manifest.config.data_start.
#   AUTO      = sector chart starts from sector_chart_start, others data_start.
$def_PARAM_FETCH_START_POLICY = "ALL"

$def_PARAM_PROCESS_TIMEOUT_SEC = 900
$def_PARAM_SUPPORTIVE_TIMEOUT_SEC = 240
$def_PARAM_FETCH_TIMEOUT_SEC = 7200

$def_PARAM_FRED_API_KEY_ENV = "FRED_API_KEY"

$def_PARAM_PYTHON_CANDIDATES = @(
    (Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe"),
    (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe"),
    "python",
    "py"
)

$def_PARAM_REQUIRED_VDF_ITEMS = @(
    "Invoke-VDF.ps1",
    "Invoke-VDF-Fetch.ps1",
    "VDF_MDL000_README.md",
    "VDF_MDL001_TWEquityEngine.py",
    "VDF_MDL001_TWUniverseVerify.py",
    "VDF_MDL002_YFinanceFetchingEngine.py",
    "VDF_MDL003_SentimentMacroEngine.py",
    "VDF_MDL004_TWFullMarketEngine.py",
    "VDF_MDL005_TWStockFilter.py",
    "VDF_MDL006_FinancialModel.py",
    "VDF_MDL007_SSOTResolver.py",
    "VDF_MDL101_OutputManager.py",
    "VDF_MDL102_FormatUpgrader.py",
    "VDF_MDL103_MasterRegistry.py",
    "VDF_MDL104_RegistryLoader.py",
    "VDF_MDL105_CrossValidator.py",
    "VDF_MDL201_GenerateFullRegistry.py",
    "VDF_MDL301_SystemTest.py",
    "VDF_MDL302_FinalActivation.py",
    "VDF_MDL303_RegistryActivation.py",
    "VDF_MDL401_RegistrySchema.json",
    "VDF_MDL402_RegistrySample.json",
    "VDF_MDL403_RegistryFull.json",
    "VDF_MDL501_DataModuleController.html",
    "__pycache__"
)

$def_PARAM_SUPPORTIVE_ITEMS = @(
    "Read_Me_VeritasNexusCore.md",
    "Invoke-VeritasNexusCore.ps1",
    "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
)

$def_PARAM_REQUIRED_PYTHON_PACKAGES = @(
    "pandas",
    "pyarrow",
    "yfinance",
    "requests"
)

# Three-round panorama policy. Max 3 rounds prevents over-fixing / Hydra risk.
$def_PARAM_MAX_ROUNDS = 3
$def_PARAM_ENABLE_SAFE_AUTO_REPAIR = $true
$def_PARAM_ENABLE_ROUND_PROGRESS_HTML = $true
$def_PARAM_ENABLE_FINAL_CONSOLIDATION = $true
$def_PARAM_ENABLE_USER_SMOKE_TEST = $false
$def_PARAM_STOP_BEFORE_FETCH_ON_HIGH_RISK = $false
$def_PARAM_USER_SMOKE_TIMEOUT_SEC = 300
$def_PARAM_OPTIONAL_ITEMS = @("__pycache__")

# Risk gate: only these repair classes can run automatically.
$def_PARAM_AUTO_REPAIR_ALLOWLIST = @(
    "CREATE_RUN_DIR",
    "COPY_MANIFEST_TO_RUN",
    "GENERATE_BRIDGE",
    "GENERATE_FETCH_ADAPTER",
    "GENERATE_REQUIRED_ITEMS_JSON",
    "PACKAGE_INSTALL",
    "WRITE_PROGRESS_REPORT",
    "CONSOLIDATE_OUTPUTS"
)


# =============================================================================
# def GLOBALS
# =============================================================================
$script:def_RUN_ID = "RUN_{0}_VDF_NEXUS_PANORAMA_3ROUND" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$script:def_RUN_DIR = Join-Path $def_PARAM_RUN_ROOT $script:def_RUN_ID
$script:def_LOG_DIR = Join-Path $script:def_RUN_DIR "logs"
$script:def_OUT_DIR = Join-Path $script:def_RUN_DIR "outputs"
$script:def_MATRIX_ROWS = [System.Collections.Generic.List[object]]::new()

# =============================================================================
# def UTILITY
# =============================================================================
function def_EnsureDir {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function def_WriteLine {
    param(
        [Parameter(Mandatory=$true)][string]$Level,
        [Parameter(Mandatory=$true)][string]$Message
    )
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = "Gray"
    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL" -or $Level -eq "FATAL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    Write-Host ("[{0}] [{1}] {2}" -f $ts, $Level, $Message) -ForegroundColor $color
}

function def_AddMatrixRow {
    param(
        [string]$Round,
        [string]$Layer,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$Class,
        [string]$Priority,
        [string]$Metric,
        [string]$Value,
        [string]$Message,
        [string]$Path
    )
    $row = [pscustomobject]@{
        RunId    = $script:def_RUN_ID
        Round    = $Round
        Layer    = $Layer
        Name     = $Name
        Status   = $Status
        Risk     = $Risk
        Class    = $Class
        Priority = $Priority
        Metric   = $Metric
        Value    = $Value
        Message  = $Message
        Path     = $Path
        Time     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    [void]$script:def_MATRIX_ROWS.Add($row)
}

function def_GetHashOrBlank {
    param([string]$Path)
    if ((Test-Path -LiteralPath $Path) -and ((Get-Item -LiteralPath $Path).PSIsContainer -eq $false)) {
        try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
        catch { return "" }
    }
    return ""
}

function def_QuoteArg {
    param([AllowNull()][string]$Arg)
    if ($null -eq $Arg) { return '""' }
    $a = [string]$Arg
    if ($a -eq "") { return '""' }
    if ($a -match '[\s"]') {
        return '"' + ($a -replace '"','\"') + '"'
    }
    return $a
}

function def_InvokeProcess {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [int]$TimeoutSec = 300,
        [string]$WorkDir = ""
    )

    if (-not (Test-Path -LiteralPath $FilePath) -and -not (Get-Command $FilePath -ErrorAction SilentlyContinue)) {
        def_AddMatrixRow "Round1" "PROCESS" $Name "FAIL_FILE_NOT_FOUND" "HIGH" "SEQUENTIAL_FIX" "P0" "exists" "false" "Executable not found." $FilePath
        return [pscustomobject]@{ Ok=$false; ExitCode=-999; StdOut=""; StdErr="Executable not found"; TimedOut=$false }
    }

    $safeName = ($Name -replace '[^\w\.-]+','_')
    $stdoutPath = Join-Path $script:def_LOG_DIR "$safeName.stdout.txt"
    $stderrPath = Join-Path $script:def_LOG_DIR "$safeName.stderr.txt"

    $argLine = ($Arguments | ForEach-Object { def_QuoteArg $_ }) -join " "
    if ([string]::IsNullOrWhiteSpace($WorkDir)) { $WorkDir = $script:def_RUN_DIR }

    def_WriteLine "RUN" ("{0}: {1} {2}" -f $Name, $FilePath, $argLine)

    try {
        $p = Start-Process -FilePath $FilePath `
            -ArgumentList $argLine `
            -WorkingDirectory $WorkDir `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath

        $exited = $p.WaitForExit([Math]::Max(1, $TimeoutSec) * 1000)
        if (-not $exited) {
            try { $p.Kill($true) } catch {}
            def_AddMatrixRow "Round2" "PROCESS" $Name "FAIL_TIMEOUT" "MEDIUM" "SEQUENTIAL_FIX" "P1" "timeout_sec" "$TimeoutSec" "Process timed out and was killed." $FilePath
            return [pscustomobject]@{ Ok=$false; ExitCode=-124; StdOut=(Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue); StdErr=(Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue); TimedOut=$true }
        }

        $out = Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue
        $err = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
        $ok = ($p.ExitCode -eq 0)
        $risk = if ($ok) { "LOW" } else { "MEDIUM" }
        $status = if ($ok) { "OK_EXIT_0" } else { "WARN_EXIT_$($p.ExitCode)" }
        def_AddMatrixRow "Round2" "PROCESS" $Name $status $risk "PARALLEL_SAFE" "P2" "exit_code" "$($p.ExitCode)" "stdout/stderr saved in logs." $FilePath
        return [pscustomobject]@{ Ok=$ok; ExitCode=$p.ExitCode; StdOut=$out; StdErr=$err; TimedOut=$false }
    }
    catch {
        def_AddMatrixRow "Round2" "PROCESS" $Name "FAIL_EXCEPTION" "MEDIUM" "SEQUENTIAL_FIX" "P1" "exception" "$($_.Exception.Message)" "Process invocation failed." $FilePath
        return [pscustomobject]@{ Ok=$false; ExitCode=-998; StdOut=""; StdErr=$_.Exception.Message; TimedOut=$false }
    }
}

function def_ResolvePwsh {
    $current = (Get-Process -Id $PID).Path
    if ($current -and (Test-Path -LiteralPath $current)) { return $current }
    $cmd = Get-Command "pwsh" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd2 = Get-Command "powershell" -ErrorAction SilentlyContinue
    if ($cmd2) { return $cmd2.Source }
    throw "PowerShell executable not found."
}

function def_ResolvePython {
    foreach ($candidate in $def_PARAM_PYTHON_CANDIDATES) {
        try {
            $exe = $candidate
            if (-not (Test-Path -LiteralPath $exe)) {
                $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
                if ($cmd) { $exe = $cmd.Source }
            }
            if ($exe -and (Test-Path -LiteralPath $exe)) {
                $probe = def_InvokeProcess -Name "PythonProbe" -FilePath $exe -Arguments @("-c", "import sys; print(sys.executable); print(sys.version)") -TimeoutSec 20 -WorkDir $script:def_RUN_DIR
                if ($probe.Ok) {
                    def_WriteLine "OK" ("Python resolved: {0}" -f $exe)
                    def_AddMatrixRow "Round1" "ENV" "Python" "OK_RESOLVED" "LOW" "PARALLEL_SAFE" "P0" "python" $exe "Python available." $exe
                    return $exe
                }
            }
        } catch {}
    }
    def_AddMatrixRow "Round1" "ENV" "Python" "FAIL_NOT_FOUND" "HIGH" "SEQUENTIAL_FIX" "P0" "python" "missing" "No usable Python found." ""
    throw "No usable Python found."
}

function def_ResolveManifest {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_MANIFEST_EXPLICIT)) {
        if (Test-Path -LiteralPath $def_PARAM_MANIFEST_EXPLICIT) {
            return (Resolve-Path -LiteralPath $def_PARAM_MANIFEST_EXPLICIT).Path
        }
        throw "Manifest explicit path not found: $def_PARAM_MANIFEST_EXPLICIT"
    }

    $found = @()
    foreach ($p in $def_PARAM_MANIFEST_CANDIDATES) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            $found += (Get-Item -LiteralPath $p)
        }
    }

    if ($found.Count -gt 0) {
        $pick = $found | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        return $pick.FullName
    }

    $msg = "VIA_data_manifest.json not found. Save the uploaded attachment into VDF base or Downloads, then rerun."
    def_AddMatrixRow "Round1" "MANIFEST" "VIA_data_manifest.json" "FAIL_NOT_FOUND" "HIGH" "SEQUENTIAL_FIX" "P0" "manifest" "missing" $msg ($def_PARAM_MANIFEST_CANDIDATES -join "; ")
    throw $msg
}

# =============================================================================
# def PREFLIGHT
# =============================================================================
function def_TestRequiredItems {
    param(
        [string]$BasePath,
        [string[]]$Items,
        [string]$Layer
    )
    foreach ($item in $Items) {
        $path = Join-Path $BasePath $item
        $isOptional = @($def_PARAM_OPTIONAL_ITEMS | Where-Object { $_ -eq $item }).Count -gt 0
        if (Test-Path -LiteralPath $path) {
            $gi = Get-Item -LiteralPath $path
            $kind = if ($gi.PSIsContainer) { "dir" } else { "file" }
            $hash = def_GetHashOrBlank $path
            def_AddMatrixRow "Round1" $Layer $item "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" $kind "true" ("Found. SHA256={0}" -f $hash) $path
        } else {
            if ($isOptional) {
                def_AddMatrixRow "Round1" $Layer $item "WARN_OPTIONAL_MISSING" "LOW" "PARALLEL_SAFE" "P3" "exists" "false" "Optional cache directory missing; no repair required." $path
            } else {
                def_AddMatrixRow "Round1" $Layer $item "FAIL_MISSING" "HIGH" "SEQUENTIAL_FIX" "P0" "exists" "false" "Required item missing." $path
            }
        }
    }
}

function def_ReadManifestSummary {
    param([string]$ManifestPath)
    $raw = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8
    $manifest = $raw | ConvertFrom-Json -Depth 64

    $schema = [string]$manifest.meta.schema
    $title = [string]$manifest.meta.title
    $declTotal = [int]$manifest.meta.total_series
    $declYf = [int]$manifest.meta.yfinance_count
    $declFred = [int]$manifest.meta.fred_count
    $fetcher = [string]$manifest.meta.fetcher
    $start = [string]$manifest.config.data_start
    $norm = [string]$manifest.config.norm_date

    def_AddMatrixRow "Round1" "MANIFEST" "Schema" "OK_PARSED" "LOW" "PARALLEL_SAFE" "P0" "schema" $schema $title $ManifestPath
    def_AddMatrixRow "Round1" "MANIFEST" "Fetcher" "OK_DECLARED" "LOW" "PARALLEL_SAFE" "P0" "fetcher" $fetcher "Declared VDF fetcher." $ManifestPath
    def_AddMatrixRow "Round1" "MANIFEST" "SeriesDeclared" "OK_DECLARED" "LOW" "PARALLEL_SAFE" "P0" "total/yf/fred" ("{0}/{1}/{2}" -f $declTotal,$declYf,$declFred) ("data_start={0}; norm_date={1}" -f $start,$norm) $ManifestPath

    return $manifest
}

function def_CreateNexusBridge {
    param(
        [string]$ManifestPath,
        [string]$PythonExe
    )
    def_EnsureDir $def_PARAM_BRIDGE_ROOT | Out-Null
    $bridgePath = Join-Path $def_PARAM_BRIDGE_ROOT "SSOT_VDF_NexusBridge.json"

    $vdfItems = @()
    foreach ($item in $def_PARAM_REQUIRED_VDF_ITEMS) {
        $p = Join-Path $def_PARAM_VDF_BASE $item
        $vdfItems += [pscustomobject]@{
            name = $item
            path = $p
            exists = (Test-Path -LiteralPath $p)
            sha256 = (def_GetHashOrBlank $p)
        }
    }

    $supportItems = @()
    foreach ($item in $def_PARAM_SUPPORTIVE_ITEMS) {
        $p = Join-Path $def_PARAM_SUPPORT_BASE $item
        $supportItems += [pscustomobject]@{
            name = $item
            path = $p
            exists = (Test-Path -LiteralPath $p)
            sha256 = (def_GetHashOrBlank $p)
        }
    }

    $bridge = [pscustomobject]@{
        schema = "VIA.VDF.NexusActivationBridge"
        version = "v1.0"
        run_id = $script:def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        policy = [pscustomobject]@{
            no_source_overwrite = $true
            no_delete = $true
            no_stop_process = $true
            outputs_only_under_vdf_system = $true
            network_fetch = $def_PARAM_ENABLE_NETWORK_FETCH
            pip_install_missing = $def_PARAM_ENABLE_PIP_INSTALL_MISSING
        }
        paths = [pscustomobject]@{
            vdf_base = $def_PARAM_VDF_BASE
            support_base = $def_PARAM_SUPPORT_BASE
            manifest = $ManifestPath
            run_dir = $script:def_RUN_DIR
            output_dir = $script:def_OUT_DIR
            python = $PythonExe
        }
        vdf_items = $vdfItems
        supportive_items = $supportItems
        activated_adapters = @(
            "VDF_MDL002_YFinanceFetchingEngine.py",
            "VDF_MDL003_SentimentMacroEngine.py",
            "VDF_MDL004_TWFullMarketEngine.py",
            "VDF_MDL006_FinancialModel.py",
            "VDF_MDL007_SSOTResolver.py",
            "VDF_MDL102_FormatUpgrader.py",
            "VDF_MDL103_MasterRegistry.py",
            "VDF_MDL104_RegistryLoader.py",
            "VDF_MDL105_CrossValidator.py",
            "VDF_MDL201_GenerateFullRegistry.py",
            "VDF_MDL301_SystemTest.py",
            "VDF_MDL302_FinalActivation.py",
            "VDF_MDL303_RegistryActivation.py",
            "VDF_MDL101_OutputManager.py"
        )
    }

    $bridge | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $bridgePath -Encoding UTF8
    $runBridge = Join-Path $script:def_RUN_DIR "SSOT_VDF_NexusBridge.json"
    Copy-Item -LiteralPath $bridgePath -Destination $runBridge -Force

    def_AddMatrixRow "Round1" "BRIDGE" "SSOT_VDF_NexusBridge" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "bridge" "ready" "Nexus bridge generated." $bridgePath
    return $bridgePath
}

# =============================================================================
# def SUPPORTIVE MODULES
# =============================================================================
function def_InvokeSupportiveModules {
    $pwsh = def_ResolvePwsh

    $readme = Join-Path $def_PARAM_SUPPORT_BASE "Read_Me_VeritasNexusCore.md"
    if (Test-Path -LiteralPath $readme) {
        $size = (Get-Item -LiteralPath $readme).Length
        def_AddMatrixRow "Round1" "NEXUSCORE" "ReadMe" "OK_AVAILABLE" "LOW" "PARALLEL_SAFE" "P0" "bytes" "$size" "NexusCore ReadMe available for local documentation bridge." $readme
    }

    $nexus = Join-Path $def_PARAM_SUPPORT_BASE "Invoke-VeritasNexusCore.ps1"
    if ($def_PARAM_ENABLE_NEXUSCORE_INVOKE -and (Test-Path -LiteralPath $nexus)) {
        [void](def_InvokeProcess -Name "Invoke-VeritasNexusCore" -FilePath $pwsh -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",$nexus) -TimeoutSec $def_PARAM_SUPPORTIVE_TIMEOUT_SEC -WorkDir $def_PARAM_SUPPORT_BASE)
    } else {
        def_AddMatrixRow "Round2" "NEXUSCORE" "Invoke-VeritasNexusCore" "WARN_SKIPPED" "LOW" "PARALLEL_SAFE" "P3" "enabled" "$def_PARAM_ENABLE_NEXUSCORE_INVOKE" "NexusCore invoke skipped or script missing." $nexus
    }

    $poly = Join-Path $def_PARAM_SUPPORT_BASE "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
    if ($def_PARAM_ENABLE_POLYGLOT_INVOKE -and (Test-Path -LiteralPath $poly)) {
        [void](def_InvokeProcess -Name "Invoke-VIA-PolyglotCheckTestRepair" -FilePath $pwsh -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",$poly) -TimeoutSec $def_PARAM_SUPPORTIVE_TIMEOUT_SEC -WorkDir $def_PARAM_SUPPORT_BASE)
    } else {
        def_AddMatrixRow "Round2" "POLYGLOT" "Invoke-VIA-PolyglotCheckTestRepair" "WARN_SKIPPED" "LOW" "PARALLEL_SAFE" "P3" "enabled" "$def_PARAM_ENABLE_POLYGLOT_INVOKE" "Polyglot invoke skipped or script missing." $poly
    }
}

# =============================================================================
# def PYTHON FETCHER GENERATION
# =============================================================================
function def_WritePythonFetcher {
    param([string]$FetcherPath)

    $py = @'
# -*- coding: utf-8 -*-
"""
VDF Manifest Fetch Adapter
Generated by Invoke-VDF-Nexus-ManifestFetch.ps1

This script:
- audits VDF Python modules by AST without executing them;
- flattens VIA_data_manifest.json;
- fetches yfinance and FRED series;
- exports raw/transformed wide and long datasets;
- keeps manual/vendor series in status table for review.
"""

import argparse
import csv
import datetime as _dt
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

def def_json_dump(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def def_sha256(path: pathlib.Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def def_import_pandas():
    import pandas as pd
    return pd

def def_import_requests():
    import requests
    return requests

def def_module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def def_package_check(outdir: pathlib.Path) -> int:
    packages = ["pandas", "pyarrow", "yfinance", "requests"]
    rows = []
    for pkg in packages:
        rows.append({
            "package": pkg,
            "available": def_module_available(pkg),
        })
    def_json_dump(outdir / "VDF_PythonPackageCheck.json", rows)
    for r in rows:
        print(f"{r['package']}={r['available']}")
    return 0 if all(r["available"] for r in rows) else 2

def def_audit_python_modules(vdf_base: pathlib.Path, required_json: pathlib.Path, outdir: pathlib.Path) -> int:
    import ast

    required_items = json.loads(required_json.read_text(encoding="utf-8"))
    rows = []

    for item in required_items:
        p = vdf_base / item
        row = {
            "item": item,
            "path": str(p),
            "exists": p.exists(),
            "kind": "dir" if p.exists() and p.is_dir() else ("file" if p.exists() else "missing"),
            "sha256": def_sha256(p),
            "syntax_ok": None,
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "error": "",
        }

        if p.exists() and p.is_file() and p.suffix.lower() == ".py":
            try:
                text = p.read_text(encoding="utf-8-sig", errors="replace")
                compile(text, str(p), "exec")
                tree = ast.parse(text)
                funcs = []
                classes = []
                imports = []

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        funcs.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                    elif isinstance(node, ast.Import):
                        for n in node.names:
                            imports.append(n.name)
                    elif isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        imports.append(mod)

                row["syntax_ok"] = True
                row["function_count"] = len(funcs)
                row["class_count"] = len(classes)
                row["import_count"] = len(sorted(set([x for x in imports if x])))
                row["functions"] = funcs[:80]
                row["classes"] = classes[:80]
                row["imports"] = sorted(set([x for x in imports if x]))[:120]
            except Exception as e:
                row["syntax_ok"] = False
                row["error"] = repr(e)

        rows.append(row)

    def_json_dump(outdir / "VDF_ModuleAudit.json", rows)
    csv_path = outdir / "VDF_ModuleAudit.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["item","path","exists","kind","sha256","syntax_ok","function_count","class_count","import_count","error"])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in writer.fieldnames})

    fail = [r for r in rows if (not r.get("exists")) or (r.get("syntax_ok") is False)]
    print(f"MODULE_AUDIT_ROWS={len(rows)}")
    print(f"MODULE_AUDIT_FAIL={len(fail)}")
    return 0 if not fail else 3

def def_load_manifest(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def def_flatten_manifest(manifest: Dict[str, Any]):
    rows: List[Dict[str, Any]] = []

    for group, items in manifest.get("datasets", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            r = dict(item)
            r["source_section"] = "datasets"
            r["group"] = group
            r["panels_joined"] = "|".join([str(x) for x in r.get("panels", [])])
            rows.append(r)

    engine = manifest.get("engine_inputs_風險引擎因子", {})
    for group, items in engine.items():
        if not isinstance(items, list):
            continue
        for item in items:
            r = dict(item)
            r["source_section"] = "engine_inputs_風險引擎因子"
            r["group"] = group
            r["panels_joined"] = "|".join([str(x) for x in r.get("panels", [])])
            rows.append(r)

    return rows

def def_effective_start(manifest: Dict[str, Any], row: Dict[str, Any], policy: str) -> str:
    cfg = manifest.get("config", {})
    policy = (policy or "ALL").upper()

    if policy == "ALL":
        return cfg.get("period_starts", {}).get("ALL", cfg.get("data_start", "2005-01-03"))

    if policy == "DATASTART":
        return cfg.get("data_start", "2024-01-02")

    group = str(row.get("group", ""))
    if "sp500_sectors" in group or row.get("panels_joined") == "②":
        return cfg.get("sector_chart_start", cfg.get("data_start", "2024-01-02"))

    return cfg.get("data_start", "2024-01-02")

def def_start_minus_years(date_str: str, years: int) -> str:
    try:
        d = _dt.datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        return d.replace(year=d.year - int(years)).isoformat()
    except Exception:
        return date_str

def def_fetch_yfinance_series(ticker: str, start: str):
    pd = def_import_pandas()
    import yfinance as yf

    data = yf.download(
        tickers=ticker,
        start=start,
        auto_adjust=False,
        progress=False,
        threads=False,
        group_by="column",
    )

    if data is None or len(data) == 0:
        raise RuntimeError(f"yfinance returned no data for {ticker}")

    if isinstance(data.columns, pd.MultiIndex):
        # Single ticker sometimes still returns MultiIndex. Prefer first matching price field.
        for price_field in ["Adj Close", "Close", "Open"]:
            if price_field in data.columns.get_level_values(0):
                sub = data[price_field]
                if hasattr(sub, "columns"):
                    s = sub.iloc[:, 0]
                else:
                    s = sub
                s.name = ticker
                return s.dropna()
    else:
        for price_field in ["Adj Close", "Close", "Open"]:
            if price_field in data.columns:
                s = data[price_field]
                s.name = ticker
                return s.dropna()

    raise RuntimeError(f"yfinance has no usable price column for {ticker}")

def def_fetch_fred_api(series_id: str, start: str, api_key: str):
    pd = def_import_pandas()
    requests = def_import_requests()
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    payload = r.json()
    obs = payload.get("observations", [])
    rows = []
    for o in obs:
        val = o.get("value")
        if val in (None, ".", ""):
            v = math.nan
        else:
            try:
                v = float(val)
            except Exception:
                v = math.nan
        rows.append((o.get("date"), v))
    if not rows:
        raise RuntimeError(f"FRED API returned no observations for {series_id}")
    s = pd.Series(
        [x[1] for x in rows],
        index=pd.to_datetime([x[0] for x in rows]),
        name=series_id,
        dtype="float64",
    )
    return s.dropna(how="all")

def def_fetch_fred_csv(series_id: str, start: str):
    pd = def_import_pandas()
    requests = def_import_requests()
    from io import StringIO

    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {"id": series_id, "cosd": start}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text))
    if df.empty or len(df.columns) < 2:
        raise RuntimeError(f"FRED CSV returned no usable data for {series_id}")

    date_col = df.columns[0]
    value_col = df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df[value_col] = pd.to_numeric(df[value_col].replace(".", None), errors="coerce")
    s = df.set_index(date_col)[value_col].astype("float64")
    s.name = series_id
    return s.dropna(how="all")

def def_fetch_fred_series(series_id: str, start: str, api_key: str):
    if api_key:
        try:
            return def_fetch_fred_api(series_id, start, api_key)
        except Exception as e:
            print(f"WARN_FRED_API_FALLBACK {series_id}: {e}", file=sys.stderr)
    return def_fetch_fred_csv(series_id, start)

def def_align_wide(df):
    if df is None or len(df) == 0:
        return df
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.dropna(how="all")
    df = df.ffill()
    return df

def def_apply_transforms(raw_wide, inventory_rows: List[Dict[str, Any]], norm_date: str):
    pd = def_import_pandas()
    transformed = pd.DataFrame(index=raw_wide.index)

    inv_by_key = {str(r.get("key")): r for r in inventory_rows if r.get("key") is not None}

    share_keys = ["U_LT5", "U_5_14", "U_15_26", "U_27"]
    share_raw = pd.DataFrame(index=raw_wide.index)
    for k in share_keys:
        if k in raw_wide.columns:
            share_raw[k] = raw_wide[k]
    share_den = share_raw.sum(axis=1).replace(0, math.nan) if len(share_raw.columns) else None

    for key, row in inv_by_key.items():
        if key not in raw_wide.columns:
            continue

        s = raw_wide[key].copy()
        transform = str(row.get("transform", "raw")).lower()
        freq = str(row.get("frequency", "")).lower()

        try:
            if transform == "normalize":
                nd = pd.to_datetime(norm_date)
                base_candidates = s.loc[s.index >= nd].dropna()
                if base_candidates.empty:
                    base_candidates = s.dropna()
                base = float(base_candidates.iloc[0]) if not base_candidates.empty else math.nan
                if not math.isnan(base) and base != 0:
                    s = s / base * 100.0
                else:
                    s = s * math.nan

            elif transform == "yoy":
                if "monthly" in freq:
                    periods = 12
                elif "weekly" in freq:
                    periods = 52
                elif "quarter" in freq:
                    periods = 4
                else:
                    periods = 252
                s = s.pct_change(periods=periods) * 100.0

            elif transform == "diff":
                s = s.diff()

            elif transform == "div1000":
                s = s / 1000.0

            elif transform == "divide10":
                s = s / 10.0

            elif transform == "share":
                if share_den is not None and key in share_raw.columns:
                    s = share_raw[key] / share_den * 100.0
                else:
                    s = s * math.nan

            elif transform in ("raw", "level", "overlay", "scenario"):
                pass

            else:
                pass

        except Exception as e:
            print(f"WARN_TRANSFORM_FAILED {key} {transform}: {e}", file=sys.stderr)

        transformed[key] = s

    transformed = def_align_wide(transformed)
    return transformed

def def_write_frame(df, out_prefix: pathlib.Path) -> Dict[str, str]:
    paths: Dict[str, str] = {}
    if df is None:
        return paths

    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    csv_path = out_prefix.with_suffix(".csv")
    df_out = df.copy()
    df_out.index.name = "date"
    df_out.to_csv(csv_path, encoding="utf-8-sig")
    paths["csv"] = str(csv_path)

    json_path = out_prefix.with_suffix(".json")
    df_json = df_out.reset_index()
    if "date" in df_json.columns:
        df_json["date"] = df_json["date"].astype(str)
    json_path.write_text(df_json.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
    paths["json"] = str(json_path)

    try:
        parquet_path = out_prefix.with_suffix(".parquet")
        df_out.to_parquet(parquet_path)
        paths["parquet"] = str(parquet_path)
    except Exception as e:
        paths["parquet_error"] = repr(e)

    return paths

def def_write_long(df, out_prefix: pathlib.Path) -> Dict[str, str]:
    pd = def_import_pandas()
    if df is None or df.empty:
        return {}
    long_df = df.copy()
    long_df.index.name = "date"
    long_df = long_df.reset_index().melt(id_vars=["date"], var_name="key", value_name="value")
    long_df = long_df.dropna(subset=["value"])
    return def_write_frame(long_df.set_index("date"), out_prefix)

def def_main_fetch(args) -> int:
    pd = def_import_pandas()

    manifest_path = pathlib.Path(args.manifest)
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    manifest = def_load_manifest(manifest_path)
    cfg = manifest.get("config", {})
    norm_date = cfg.get("norm_date", cfg.get("data_start", "2025-01-02"))
    fred_lookback_years = int(cfg.get("fred_lookback_years", 1))
    api_key = os.environ.get(args.fred_api_key_env, "")

    inventory_rows = def_flatten_manifest(manifest)
    inv_df = pd.DataFrame(inventory_rows)
    inv_df.to_csv(outdir / "VDF_ManifestInventory.csv", index=False, encoding="utf-8-sig")
    (outdir / "VDF_ManifestInventory.json").write_text(inv_df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")

    counts = inv_df["source"].value_counts(dropna=False).to_dict() if "source" in inv_df.columns else {}
    def_json_dump(outdir / "VDF_ManifestSourceCounts.json", {
        "declared_meta": manifest.get("meta", {}),
        "actual_flattened_count": len(inventory_rows),
        "actual_source_counts": counts,
    })

    if not args.network:
        status = []
        for row in inventory_rows:
            status.append({
                "key": row.get("key"),
                "source": row.get("source"),
                "id": row.get("id"),
                "status": "SKIP_NETWORK_DISABLED",
                "message": "Network fetch disabled by PowerShell parameter.",
            })
        pd.DataFrame(status).to_csv(outdir / "VDF_MacroFetchStatus.csv", index=False, encoding="utf-8-sig")
        def_json_dump(outdir / "VDF_MacroFetchStatus.json", status)
        return 0

    series_map = {}
    status_rows = []

    for i, row in enumerate(inventory_rows, start=1):
        key = str(row.get("key", "")).strip()
        source = str(row.get("source", "")).strip().lower()
        sid = str(row.get("id", "")).strip()
        start = def_effective_start(manifest, row, args.start_policy)

        if not key:
            continue

        if source == "fred":
            start = def_start_minus_years(start, fred_lookback_years)

        print(f"[{i}/{len(inventory_rows)}] FETCH {key} source={source} id={sid} start={start}", flush=True)

        try:
            if source == "yfinance":
                s = def_fetch_yfinance_series(sid, start)
                s.name = key
                series_map[key] = s
                status_rows.append({"key": key, "source": source, "id": sid, "status": "OK_FETCHED", "rows": int(s.shape[0]), "start": str(s.index.min().date()) if len(s) else "", "end": str(s.index.max().date()) if len(s) else "", "message": ""})

            elif source == "fred":
                s = def_fetch_fred_series(sid, start, api_key)
                s.name = key
                series_map[key] = s
                status_rows.append({"key": key, "source": source, "id": sid, "status": "OK_FETCHED", "rows": int(s.shape[0]), "start": str(s.index.min().date()) if len(s) else "", "end": str(s.index.max().date()) if len(s) else "", "message": ""})

            elif source in ("derived",):
                status_rows.append({"key": key, "source": source, "id": sid, "status": "WARN_DERIVED_PENDING", "rows": 0, "start": "", "end": "", "message": "Derived series requires model scenario layer after base fetch."})

            else:
                status_rows.append({"key": key, "source": source, "id": sid, "status": "WARN_MANUAL_VENDOR_SKIPPED", "rows": 0, "start": "", "end": "", "message": "Manual/vendor/vdf-manual source is preserved in inventory but not auto-fetched."})

        except Exception as e:
            status_rows.append({"key": key, "source": source, "id": sid, "status": "FAIL_FETCH", "rows": 0, "start": "", "end": "", "message": repr(e)})
            print(f"FAIL_FETCH {key}: {e}", file=sys.stderr, flush=True)

    if series_map:
        raw_wide = pd.concat(series_map.values(), axis=1)
        raw_wide = def_align_wide(raw_wide)
    else:
        raw_wide = pd.DataFrame()

    transformed_wide = def_apply_transforms(raw_wide, inventory_rows, norm_date) if not raw_wide.empty else pd.DataFrame()

    raw_paths = def_write_frame(raw_wide, outdir / "VDF_MacroRawWide")
    transformed_paths = def_write_frame(transformed_wide, outdir / "VDF_MacroTransformedWide")
    raw_long_paths = def_write_long(raw_wide, outdir / "VDF_MacroRawLong")
    transformed_long_paths = def_write_long(transformed_wide, outdir / "VDF_MacroTransformedLong")

    status_df = pd.DataFrame(status_rows)
    status_df.to_csv(outdir / "VDF_MacroFetchStatus.csv", index=False, encoding="utf-8-sig")
    def_json_dump(outdir / "VDF_MacroFetchStatus.json", status_rows)

    summary = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "manifest": str(manifest_path),
        "inventory_count": len(inventory_rows),
        "source_counts": counts,
        "fetched_columns": list(raw_wide.columns) if not raw_wide.empty else [],
        "raw_shape": list(raw_wide.shape),
        "transformed_shape": list(transformed_wide.shape),
        "status_counts": status_df["status"].value_counts(dropna=False).to_dict() if not status_df.empty else {},
        "raw_paths": raw_paths,
        "transformed_paths": transformed_paths,
        "raw_long_paths": raw_long_paths,
        "transformed_long_paths": transformed_long_paths,
        "fred_api_key_env": args.fred_api_key_env,
        "fred_api_key_available": bool(api_key),
    }
    def_json_dump(outdir / "VDF_MacroFetchSummary.json", summary)

    fail_count = int((status_df["status"] == "FAIL_FETCH").sum()) if not status_df.empty else 0
    print("FETCH_SUMMARY=" + json.dumps(summary, ensure_ascii=False))
    return 0 if fail_count == 0 else 4

def def_main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["package_check", "audit", "fetch"], required=True)
    ap.add_argument("--manifest", default="")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--vdf-base", default="")
    ap.add_argument("--required-json", default="")
    ap.add_argument("--start-policy", default="ALL")
    ap.add_argument("--fred-api-key-env", default="FRED_API_KEY")
    ap.add_argument("--network", action="store_true", default=True)
    ap.add_argument("--no-network", dest="network", action="store_false")
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.mode == "package_check":
        return def_package_check(outdir)

    if args.mode == "audit":
        return def_audit_python_modules(pathlib.Path(args.vdf_base), pathlib.Path(args.required_json), outdir)

    if args.mode == "fetch":
        return def_main_fetch(args)

    return 1

if __name__ == "__main__":
    try:
        raise SystemExit(def_main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(99)
'@

    Set-Content -LiteralPath $FetcherPath -Value $py -Encoding UTF8
    def_AddMatrixRow "Round1" "PYTHON" "VDF_ManifestFetchAdapter.py" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "file" "ready" "Generated local Python fetch adapter." $FetcherPath
}

function def_EnsurePythonPackages {
    param([string]$PythonExe, [string]$FetcherPath)

    $pkg = def_InvokeProcess -Name "PythonPackageCheck" -FilePath $PythonExe -Arguments @($FetcherPath, "--mode", "package_check", "--outdir", $script:def_OUT_DIR) -TimeoutSec 90 -WorkDir $script:def_RUN_DIR

    if ($pkg.Ok) {
        def_AddMatrixRow "Round1" "PYTHON" "RequiredPackages" "OK_AVAILABLE" "LOW" "PARALLEL_SAFE" "P0" "packages" ($def_PARAM_REQUIRED_PYTHON_PACKAGES -join ",") "All required Python packages available." $PythonExe
        return
    }

    if (-not $def_PARAM_ENABLE_PIP_INSTALL_MISSING) {
        def_AddMatrixRow "Round1" "PYTHON" "RequiredPackages" "WARN_MISSING_NO_INSTALL" "MEDIUM" "SEQUENTIAL_FIX" "P1" "pip_install" "false" "Missing packages; pip install disabled." $PythonExe
        return
    }

    def_WriteLine "WARN" "Some Python packages are missing. Installing into resolved Python environment."
    [void](def_InvokeProcess -Name "PipUpgrade" -FilePath $PythonExe -Arguments @("-m","pip","install","--upgrade","pip") -TimeoutSec $def_PARAM_PROCESS_TIMEOUT_SEC -WorkDir $script:def_RUN_DIR)
    $installArgs = @("-m","pip","install","--upgrade") + $def_PARAM_REQUIRED_PYTHON_PACKAGES
    $pip = def_InvokeProcess -Name "PipInstallRequired" -FilePath $PythonExe -Arguments $installArgs -TimeoutSec $def_PARAM_PROCESS_TIMEOUT_SEC -WorkDir $script:def_RUN_DIR

    if ($pip.Ok) {
        def_AddMatrixRow "Round1" "PYTHON" "RequiredPackages" "OK_INSTALLED" "LOW" "SEQUENTIAL_FIX" "P1" "packages" ($def_PARAM_REQUIRED_PYTHON_PACKAGES -join ",") "Missing packages installed." $PythonExe
    } else {
        def_AddMatrixRow "Round1" "PYTHON" "RequiredPackages" "FAIL_INSTALL" "HIGH" "SEQUENTIAL_FIX" "P0" "packages" ($def_PARAM_REQUIRED_PYTHON_PACKAGES -join ",") "pip install failed; see logs." $PythonExe
    }
}

function def_RunModuleAudit {
    param([string]$PythonExe, [string]$FetcherPath)

    $requiredPath = Join-Path $script:def_RUN_DIR "VDF_RequiredItems.json"
    $def_PARAM_REQUIRED_VDF_ITEMS | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $requiredPath -Encoding UTF8

    $audit = def_InvokeProcess -Name "VDF_ModuleAudit_AST" -FilePath $PythonExe -Arguments @(
        $FetcherPath,
        "--mode", "audit",
        "--outdir", $script:def_OUT_DIR,
        "--vdf-base", $def_PARAM_VDF_BASE,
        "--required-json", $requiredPath
    ) -TimeoutSec $def_PARAM_PROCESS_TIMEOUT_SEC -WorkDir $script:def_RUN_DIR

    if ($audit.Ok) {
        def_AddMatrixRow "Round2" "VDF_AUDIT" "AST_Syntax_ModuleRegistry" "OK_AUDIT_PASS" "LOW" "PARALLEL_SAFE" "P0" "audit" "pass" "AST syntax and module registry generated." (Join-Path $script:def_OUT_DIR "VDF_ModuleAudit.json")
    } else {
        def_AddMatrixRow "Round2" "VDF_AUDIT" "AST_Syntax_ModuleRegistry" "WARN_AUDIT_REVIEW" "MEDIUM" "SEQUENTIAL_FIX" "P1" "exit_code" "$($audit.ExitCode)" "AST audit needs review; see logs/output." (Join-Path $script:def_OUT_DIR "VDF_ModuleAudit.json")
    }
}

function def_RunManifestFetch {
    param(
        [string]$PythonExe,
        [string]$FetcherPath,
        [string]$ManifestPath
    )

    $args = @(
        $FetcherPath,
        "--mode", "fetch",
        "--manifest", $ManifestPath,
        "--outdir", $script:def_OUT_DIR,
        "--vdf-base", $def_PARAM_VDF_BASE,
        "--start-policy", $def_PARAM_FETCH_START_POLICY,
        "--fred-api-key-env", $def_PARAM_FRED_API_KEY_ENV
    )

    if (-not $def_PARAM_ENABLE_NETWORK_FETCH) {
        $args += "--no-network"
    }

    $fetch = def_InvokeProcess -Name "VDF_ManifestFetch" -FilePath $PythonExe -Arguments $args -TimeoutSec $def_PARAM_FETCH_TIMEOUT_SEC -WorkDir $script:def_RUN_DIR

    if ($fetch.Ok) {
        def_AddMatrixRow "Round3" "FETCH" "ManifestDataFetch" "OK_FETCH_COMPLETE" "LOW" "PARALLEL_SAFE" "P0" "network" "$def_PARAM_ENABLE_NETWORK_FETCH" "Manifest data fetch completed." (Join-Path $script:def_OUT_DIR "VDF_MacroFetchSummary.json")
    } else {
        def_AddMatrixRow "Round3" "FETCH" "ManifestDataFetch" "WARN_FETCH_REVIEW" "MEDIUM" "SEQUENTIAL_FIX" "P1" "exit_code" "$($fetch.ExitCode)" "Fetch completed with failures/review; see status table." (Join-Path $script:def_OUT_DIR "VDF_MacroFetchStatus.csv")
    }
}


# =============================================================================
# def PANORAMA THREE-ROUND CONTROL
# =============================================================================
function def_GetMatrixStats {
    $okCount = @($script:def_MATRIX_ROWS | Where-Object { $_.Status -like "OK*" }).Count
    $warnCount = @($script:def_MATRIX_ROWS | Where-Object { $_.Status -like "WARN*" }).Count
    $failCount = @($script:def_MATRIX_ROWS | Where-Object { $_.Status -like "FAIL*" }).Count
    $highCount = @($script:def_MATRIX_ROWS | Where-Object { $_.Risk -eq "HIGH" }).Count
    $mediumCount = @($script:def_MATRIX_ROWS | Where-Object { $_.Risk -eq "MEDIUM" }).Count
    $risk = if ($failCount -gt 0 -or $highCount -gt 0) { "HIGH" } elseif ($warnCount -gt 0 -or $mediumCount -gt 0) { "MEDIUM" } else { "LOW" }
    return [pscustomobject]@{ OK=$okCount; WARN=$warnCount; FAIL=$failCount; HIGH=$highCount; MEDIUM=$mediumCount; Risk=$risk }
}

function def_GetOpenIssues {
    $issues = @($script:def_MATRIX_ROWS | Where-Object { $_.Status -like "FAIL*" -or $_.Status -like "WARN*" })
    return $issues | Sort-Object Priority, Risk, Layer, Name
}

function def_ClassifyRoundFindings {
    param([int]$Round)
    $roundName = "Round$Round"
    $issues = @(def_GetOpenIssues)
    $parallel = @($issues | Where-Object { $_.Class -eq "PARALLEL_SAFE" })
    $sequential = @($issues | Where-Object { $_.Class -ne "PARALLEL_SAFE" })
    $hydra = @($sequential | Where-Object { $_.Risk -eq "HIGH" -or $_.Priority -eq "P0" })

    def_AddMatrixRow $roundName "CLASSIFY" "ParallelSafeFixes" "OK_CLASSIFIED" "LOW" "PARALLEL_SAFE" "P1" "count" "$($parallel.Count)" "Can be handled independently or reviewed without cross-impact." ""
    def_AddMatrixRow $roundName "CLASSIFY" "SequentialFixes" "OK_CLASSIFIED" $(if($sequential.Count -gt 0){"MEDIUM"}else{"LOW"}) "SEQUENTIAL_FIX" "P0" "count" "$($sequential.Count)" "Must be handled in order to avoid Hydra risk." ""
    def_AddMatrixRow $roundName "CLASSIFY" "HydraRiskGate" $(if($hydra.Count -gt 0){"WARN_HYDRA_RISK_OPEN"}else{"OK_HYDRA_CLEAR"}) $(if($hydra.Count -gt 0){"HIGH"}else{"LOW"}) "SEQUENTIAL_FIX" "P0" "count" "$($hydra.Count)" "High-priority sequential issues are isolated before deeper activation." ""
}

function def_AddOptimizationRows {
    param([int]$Round)
    $roundName = "Round$Round"

    $fredKey = [Environment]::GetEnvironmentVariable($def_PARAM_FRED_API_KEY_ENV, "Process")
    if ([string]::IsNullOrWhiteSpace($fredKey)) {
        def_AddMatrixRow $roundName "OPTIMIZE" "FRED_API_KEY" "WARN_ENV_MISSING" "MEDIUM" "SEQUENTIAL_FIX" "P1" "env" $def_PARAM_FRED_API_KEY_ENV "FRED can fallback to public CSV for some series, but API key is recommended for stable fetch." ""
    } else {
        def_AddMatrixRow $roundName "OPTIMIZE" "FRED_API_KEY" "OK_ENV_AVAILABLE" "LOW" "PARALLEL_SAFE" "P1" "env" $def_PARAM_FRED_API_KEY_ENV "FRED API key available in process environment." ""
    }

    $summaryPath = Join-Path $script:def_OUT_DIR "VDF_MacroFetchSummary.json"
    if (Test-Path -LiteralPath $summaryPath) {
        try {
            $summary = Get-Content -LiteralPath $summaryPath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 64
            $rawShape = ($summary.raw_shape -join "x")
            $transShape = ($summary.transformed_shape -join "x")
            def_AddMatrixRow $roundName "VALIDATE" "FetchSummary" "OK_SUMMARY_READ" "LOW" "PARALLEL_SAFE" "P1" "raw/transformed" "$rawShape / $transShape" "Fetch summary parsed." $summaryPath
        } catch {
            def_AddMatrixRow $roundName "VALIDATE" "FetchSummary" "WARN_SUMMARY_PARSE" "MEDIUM" "SEQUENTIAL_FIX" "P1" "exception" "$($_.Exception.Message)" "Summary exists but failed to parse." $summaryPath
        }
    } else {
        def_AddMatrixRow $roundName "VALIDATE" "FetchSummary" "WARN_SUMMARY_NOT_READY" "MEDIUM" "SEQUENTIAL_FIX" "P1" "exists" "false" "Fetch summary not found yet." $summaryPath
    }
}

function def_ValidateCoreOutputs {
    param([int]$Round)
    $roundName = "Round$Round"
    $expected = @(
        "VDF_ManifestInventory.csv",
        "VDF_ModuleAudit.json",
        "VDF_MacroFetchStatus.csv",
        "VDF_MacroFetchSummary.json",
        "VDF_MacroRawWide.csv",
        "VDF_MacroTransformedWide.csv"
    )
    foreach ($name in $expected) {
        $path = Join-Path $script:def_OUT_DIR $name
        if (Test-Path -LiteralPath $path) {
            $len = (Get-Item -LiteralPath $path).Length
            def_AddMatrixRow $roundName "OUTPUT" $name "OK_OUTPUT_FOUND" "LOW" "PARALLEL_SAFE" "P2" "bytes" "$len" "Output artifact exists." $path
        } else {
            def_AddMatrixRow $roundName "OUTPUT" $name "WARN_OUTPUT_MISSING" "MEDIUM" "SEQUENTIAL_FIX" "P1" "exists" "false" "Output artifact missing; review previous step." $path
        }
    }
}

function def_InvokeUserSmokeTest {
    if (-not $def_PARAM_ENABLE_USER_SMOKE_TEST) {
        def_AddMatrixRow "Round3" "USER_TEST" "Invoke-VDF.ps1" "WARN_SKIPPED_BY_POLICY" "LOW" "PARALLEL_SAFE" "P3" "enabled" "false" "Full user smoke test skipped by parameter to avoid unknown side effects." (Join-Path $def_PARAM_VDF_BASE "Invoke-VDF.ps1")
        return
    }
    $pwsh = def_ResolvePwsh
    $entry = Join-Path $def_PARAM_VDF_BASE "Invoke-VDF.ps1"
    if (Test-Path -LiteralPath $entry) {
        [void](def_InvokeProcess -Name "UserSmoke_Invoke_VDF" -FilePath $pwsh -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",$entry) -TimeoutSec $def_PARAM_USER_SMOKE_TIMEOUT_SEC -WorkDir $def_PARAM_VDF_BASE)
    } else {
        def_AddMatrixRow "Round3" "USER_TEST" "Invoke-VDF.ps1" "FAIL_ENTRY_MISSING" "HIGH" "SEQUENTIAL_FIX" "P0" "exists" "false" "VDF entrypoint missing." $entry
    }
}

function def_WriteRoundProgressHtml {
    param([int]$Round)
    if (-not $def_PARAM_ENABLE_ROUND_PROGRESS_HTML) { return }

    $path = Join-Path $script:def_RUN_DIR ("VDF_Panorama_Round{0}_Progress.html" -f $Round)
    $stats = def_GetMatrixStats
    $issues = @(def_GetOpenIssues)
    $parallel = @($issues | Where-Object { $_.Class -eq "PARALLEL_SAFE" })
    $sequential = @($issues | Where-Object { $_.Class -ne "PARALLEL_SAFE" })

    $rowsHtml = foreach ($r in $script:def_MATRIX_ROWS) {
        $cls = "ok"
        if ($r.Status -like "FAIL*") { $cls = "fail" }
        elseif ($r.Status -like "WARN*") { $cls = "warn" }
        "<tr class='$cls'><td>$(def_HtmlEncode $r.Round)</td><td>$(def_HtmlEncode $r.Layer)</td><td>$(def_HtmlEncode $r.Name)</td><td>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.Risk)</td><td>$(def_HtmlEncode $r.Class)</td><td>$(def_HtmlEncode $r.Priority)</td><td>$(def_HtmlEncode $r.Metric)</td><td>$(def_HtmlEncode $r.Value)</td><td>$(def_HtmlEncode $r.Message)</td><td>$(def_HtmlEncode $r.Path)</td></tr>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VDF Panorama Round $Round Progress</title>
<style>
:root{--paper:#f9f9f6;--ink:#26332f;--muted:#6f7b75;--line:#d9ddd4;--ok:#e9f4ee;--warn:#fff7df;--fail:#ffe9e4}
*{box-sizing:border-box} body{margin:0;padding:28px;background:radial-gradient(circle at 12% 8%,rgba(160,190,178,.20),transparent 32%),linear-gradient(115deg,rgba(80,130,120,.08),transparent 45%),var(--paper);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif}
h1{font-size:23px;margin:0}.sub{color:var(--muted);font-size:13px}.seal{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border:2px solid #a64236;color:#a64236;font-weight:800;margin-right:12px}.head{display:flex;align-items:center;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:16px}.kpis{display:grid;grid-template-columns:repeat(6,minmax(110px,1fr));gap:12px;margin:16px 0}.kpi{background:rgba(255,255,255,.66);border:1px solid var(--line);border-radius:16px;padding:13px}.kpi b{display:block;font-size:20px}.kpi span{font-size:12px;color:var(--muted)}
table{width:100%;border-collapse:separate;border-spacing:0;background:rgba(255,255,255,.66);border:1px solid var(--line);border-radius:16px;overflow:hidden}th,td{font-size:12px;text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}th{position:sticky;top:0;background:#eff4ef}tr.ok td{background:var(--ok)}tr.warn td{background:var(--warn)}tr.fail td{background:var(--fail)}
</style>
</head>
<body>
<div class="head"><div class="seal">理</div><div><h1>VDF Nexus Panorama · Round $Round Progress</h1><div class="sub">Run ID: $(def_HtmlEncode $script:def_RUN_ID) · Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</div></div></div>
<div class="kpis">
<div class="kpi"><b>$(def_HtmlEncode $stats.Risk)</b><span>Risk</span></div>
<div class="kpi"><b>$($stats.OK)</b><span>OK</span></div>
<div class="kpi"><b>$($stats.WARN)</b><span>WARN</span></div>
<div class="kpi"><b>$($stats.FAIL)</b><span>FAIL</span></div>
<div class="kpi"><b>$($parallel.Count)</b><span>Parallel Safe</span></div>
<div class="kpi"><b>$($sequential.Count)</b><span>Sequential</span></div>
</div>
<table><thead><tr><th>Round</th><th>Layer</th><th>Name</th><th>Status</th><th>Risk</th><th>Class</th><th>Priority</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th></tr></thead><tbody>
$($rowsHtml -join "`n")
</tbody></table>
</body>
</html>
"@
    Set-Content -LiteralPath $path -Value $html -Encoding UTF8
    def_WriteLine "OK" "Round $Round progress HTML: $path"
}

function def_ConsolidateFinalArtifacts {
    if (-not $def_PARAM_ENABLE_FINAL_CONSOLIDATION) { return }
    $consolidatedDir = Join-Path $script:def_RUN_DIR "consolidated"
    def_EnsureDir $consolidatedDir | Out-Null
    $patterns = @("*.csv","*.json","*.parquet","*.html")
    foreach ($pattern in $patterns) {
        Get-ChildItem -LiteralPath $script:def_OUT_DIR -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $consolidatedDir $_.Name) -Force
        }
    }
    Get-ChildItem -LiteralPath $script:def_RUN_DIR -Filter "*.html" -File -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $consolidatedDir $_.Name) -Force
    }
    def_AddMatrixRow "Round3" "CONSOLIDATE" "FinalArtifacts" "OK_CONSOLIDATED" "LOW" "PARALLEL_SAFE" "P2" "dir" "ready" "Selected outputs copied to consolidated folder." $consolidatedDir
}

# =============================================================================
# def REPORT
# =============================================================================
function def_HtmlEncode {
    param([AllowNull()][object]$Value)
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_WriteReports {
    $csvPath = Join-Path $script:def_RUN_DIR "VDF_NexusPanorama3Round_Matrix.csv"
    $jsonPath = Join-Path $script:def_RUN_DIR "VDF_NexusPanorama3Round_Matrix.json"
    $htmlPath = Join-Path $script:def_RUN_DIR "VDF_NexusPanorama3Round_Report.html"

    $script:def_MATRIX_ROWS | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8BOM
    $script:def_MATRIX_ROWS | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    $stats = def_GetMatrixStats
    $okCount = $stats.OK
    $warnCount = $stats.WARN
    $failCount = $stats.FAIL
    $risk = $stats.Risk
    $status = if ($failCount -gt 0 -or $risk -eq "HIGH") { "VDF_NEXUS_PANORAMA_3ROUND_REVIEW" } elseif ($warnCount -gt 0) { "VDF_NEXUS_PANORAMA_3ROUND_READY_WITH_WARNINGS" } else { "VDF_NEXUS_PANORAMA_3ROUND_READY" }

    $rowsHtml = foreach ($r in $script:def_MATRIX_ROWS) {
        $cls = "ok"
        if ($r.Status -like "FAIL*") { $cls = "fail" }
        elseif ($r.Status -like "WARN*") { $cls = "warn" }
        "<tr class='$cls'><td>$(def_HtmlEncode $r.Round)</td><td>$(def_HtmlEncode $r.Layer)</td><td>$(def_HtmlEncode $r.Name)</td><td>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.Risk)</td><td>$(def_HtmlEncode $r.Class)</td><td>$(def_HtmlEncode $r.Priority)</td><td>$(def_HtmlEncode $r.Metric)</td><td>$(def_HtmlEncode $r.Value)</td><td>$(def_HtmlEncode $r.Message)</td><td>$(def_HtmlEncode $r.Path)</td></tr>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VDF Nexus Panorama Three-Round Report</title>
<style>
:root{
  --paper:#f9f9f6; --ink:#26332f; --muted:#6f7b75; --line:#d9ddd4;
  --ok:#e9f4ee; --warn:#fff7df; --fail:#ffe9e4; --cyan:#d8ebe7;
}
*{box-sizing:border-box}
body{
  margin:0; padding:28px; background:
  radial-gradient(circle at 12% 8%, rgba(160,190,178,.18), transparent 32%),
  radial-gradient(circle at 92% 18%, rgba(190,80,60,.08), transparent 26%),
  linear-gradient(115deg, rgba(80,130,120,.08), transparent 45%),
  var(--paper);
  color:var(--ink);
  font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;
}
.header{border-bottom:1px solid var(--line); padding-bottom:18px; margin-bottom:18px}
.seal{display:inline-flex; align-items:center; justify-content:center; width:46px; height:46px; border:2px solid #a64236; color:#a64236; font-weight:800; margin-right:12px}
h1{font-size:24px; letter-spacing:.02em; margin:0 0 6px}
.sub{color:var(--muted); font-size:13px}
.kpis{display:grid; grid-template-columns:repeat(5,minmax(120px,1fr)); gap:12px; margin:18px 0}
.kpi{background:rgba(255,255,255,.62); border:1px solid var(--line); border-radius:16px; padding:14px}
.kpi b{display:block; font-size:22px}
.kpi span{font-size:12px; color:var(--muted)}
table{width:100%; border-collapse:separate; border-spacing:0; background:rgba(255,255,255,.66); border:1px solid var(--line); border-radius:16px; overflow:hidden}
th,td{font-size:12px; text-align:left; padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:top}
th{position:sticky; top:0; background:#eff4ef; z-index:2}
tr.ok td{background:var(--ok)}
tr.warn td{background:var(--warn)}
tr.fail td{background:var(--fail)}
.path{font-family:Consolas,monospace}
.footer{margin-top:18px; color:var(--muted); font-size:12px}
</style>
</head>
<body>
<div class="header">
  <div style="display:flex;align-items:center">
    <div class="seal">理</div>
    <div>
      <h1>Veritas Intelligence Analytics · VDF Nexus Panorama Three-Round Gate</h1>
      <div class="sub">Run ID: $(def_HtmlEncode $script:def_RUN_ID) · Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</div>
    </div>
  </div>
</div>

<div class="kpis">
  <div class="kpi"><b>$(def_HtmlEncode $status)</b><span>Status</span></div>
  <div class="kpi"><b>$(def_HtmlEncode $risk)</b><span>Risk</span></div>
  <div class="kpi"><b>$okCount</b><span>OK</span></div>
  <div class="kpi"><b>$warnCount</b><span>WARN</span></div>
  <div class="kpi"><b>$failCount</b><span>FAIL</span></div>
</div>

<table>
<thead>
<tr>
<th>Round</th><th>Layer</th><th>Name</th><th>Status</th><th>Risk</th><th>Class</th><th>Priority</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th>
</tr>
</thead>
<tbody>
$($rowsHtml -join "`n")
</tbody>
</table>

<div class="footer">
Outputs: $(def_HtmlEncode $script:def_OUT_DIR)<br>
Matrix CSV: $(def_HtmlEncode $csvPath)<br>
Matrix JSON: $(def_HtmlEncode $jsonPath)
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $htmlPath -Value $html -Encoding UTF8

    def_WriteLine "OK" "Matrix CSV : $csvPath"
    def_WriteLine "OK" "Matrix JSON: $jsonPath"
    def_WriteLine "OK" "HTML Report: $htmlPath"
    def_WriteLine "OK" "Outputs    : $script:def_OUT_DIR"

    if ($def_PARAM_OPEN_HTML_REPORT -and (Test-Path -LiteralPath $htmlPath)) {
        Start-Process $htmlPath
    }

    return [pscustomobject]@{
        Status = $status
        Risk = $risk
        OK = $okCount
        WARN = $warnCount
        FAIL = $failCount
        Html = $htmlPath
        Csv = $csvPath
        Json = $jsonPath
        Outputs = $script:def_OUT_DIR
    }
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VDF · NEXUSCORE PANORAMA THREE-ROUND ACTIVATION GATE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    def_EnsureDir $script:def_RUN_DIR | Out-Null
    def_EnsureDir $script:def_LOG_DIR | Out-Null
    def_EnsureDir $script:def_OUT_DIR | Out-Null
    def_EnsureDir $def_PARAM_BRIDGE_ROOT | Out-Null

    def_WriteLine "RUN" "RunDir: $script:def_RUN_DIR"
    def_WriteLine "RUN" "VDF Base: $def_PARAM_VDF_BASE"
    def_WriteLine "RUN" "Supportive Base: $def_PARAM_SUPPORT_BASE"
    def_WriteLine "RUN" "Policy: max_rounds=$def_PARAM_MAX_ROUNDS; safe_auto_repair=$def_PARAM_ENABLE_SAFE_AUTO_REPAIR; no_source_overwrite=true"

    # -------------------------------------------------------------------------
    # def Round 1 · Discovery / SSOT / Bridge / Adapter
    # -------------------------------------------------------------------------
    def_WriteLine "RUN" "Round 1/3: Discovery, manifest parse, SSOT bridge, adapter generation."
    def_TestRequiredItems -BasePath $def_PARAM_VDF_BASE -Items $def_PARAM_REQUIRED_VDF_ITEMS -Layer "VDF"
    def_TestRequiredItems -BasePath $def_PARAM_SUPPORT_BASE -Items $def_PARAM_SUPPORTIVE_ITEMS -Layer "SUPPORTIVE"

    $manifestPath = def_ResolveManifest
    $manifestCopy = Join-Path $script:def_RUN_DIR "VIA_data_manifest.json"
    Copy-Item -LiteralPath $manifestPath -Destination $manifestCopy -Force
    def_AddMatrixRow "Round1" "REPAIR" "CopyManifestToRun" "OK_REPAIR_APPLIED" "LOW" "PARALLEL_SAFE" "P0" "repair" "COPY_MANIFEST_TO_RUN" "Manifest copied into isolated run directory." $manifestCopy

    [void](def_ReadManifestSummary -ManifestPath $manifestCopy)

    $pythonExe = def_ResolvePython

    $fetcherPath = Join-Path $script:def_RUN_DIR "VDF_ManifestFetchAdapter.py"
    def_WritePythonFetcher -FetcherPath $fetcherPath
    def_AddMatrixRow "Round1" "REPAIR" "GenerateFetchAdapter" "OK_REPAIR_APPLIED" "LOW" "PARALLEL_SAFE" "P0" "repair" "GENERATE_FETCH_ADAPTER" "Adapter generated under run directory only." $fetcherPath

    def_CreateNexusBridge -ManifestPath $manifestCopy -PythonExe $pythonExe | Out-Null
    def_AddMatrixRow "Round1" "REPAIR" "GenerateNexusBridge" "OK_REPAIR_APPLIED" "LOW" "PARALLEL_SAFE" "P0" "repair" "GENERATE_BRIDGE" "Bridge generated under VDF _vdf_system/bridge." (Join-Path $def_PARAM_BRIDGE_ROOT "SSOT_VDF_NexusBridge.json")

    def_ClassifyRoundFindings -Round 1
    def_AddOptimizationRows -Round 1
    def_WriteRoundProgressHtml -Round 1

    $statsAfterRound1 = def_GetMatrixStats
    if ($def_PARAM_STOP_BEFORE_FETCH_ON_HIGH_RISK -and $statsAfterRound1.Risk -eq "HIGH") {
        def_AddMatrixRow "Round1" "GATE" "StopBeforeFetch" "WARN_STOPPED_BY_HIGH_RISK" "HIGH" "SEQUENTIAL_FIX" "P0" "risk" "$($statsAfterRound1.Risk)" "Fetch skipped due to high-risk gate." ""
        $result = def_WriteReports
        return
    }

    # -------------------------------------------------------------------------
    # def Round 2 · Supportive import / package repair / AST audit
    # -------------------------------------------------------------------------
    def_WriteLine "RUN" "Round 2/3: NexusCore import, package repair, AST module audit."
    def_InvokeSupportiveModules
    def_EnsurePythonPackages -PythonExe $pythonExe -FetcherPath $fetcherPath
    def_RunModuleAudit -PythonExe $pythonExe -FetcherPath $fetcherPath

    def_ClassifyRoundFindings -Round 2
    def_AddOptimizationRows -Round 2
    def_WriteRoundProgressHtml -Round 2

    # -------------------------------------------------------------------------
    # def Round 3 · Fetch / validate / consolidate / optional user smoke test
    # -------------------------------------------------------------------------
    def_WriteLine "RUN" "Round 3/3: Manifest fetch, validation, consolidation, user-test gate."
    def_RunManifestFetch -PythonExe $pythonExe -FetcherPath $fetcherPath -ManifestPath $manifestCopy
    def_ValidateCoreOutputs -Round 3
    def_AddOptimizationRows -Round 3
    def_InvokeUserSmokeTest
    def_ConsolidateFinalArtifacts

    def_ClassifyRoundFindings -Round 3
    def_WriteRoundProgressHtml -Round 3

    $result = def_WriteReports

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VDF NEXUS PANORAMA THREE-ROUND COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("Status  : {0}" -f $result.Status)
    Write-Host ("Risk    : {0}" -f $result.Risk)
    Write-Host ("OK      : {0}" -f $result.OK)
    Write-Host ("WARN    : {0}" -f $result.WARN)
    Write-Host ("FAIL    : {0}" -f $result.FAIL)
    Write-Host ("HTML    : {0}" -f $result.Html)
    Write-Host ("Outputs : {0}" -f $result.Outputs)
}

# =============================================================================
# def ENTRY
# =============================================================================
try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    try {
        def_AddMatrixRow "FATAL" "ENTRY" "def_Main" "FAIL_FATAL" "HIGH" "SEQUENTIAL_FIX" "P0" "exception" "$($_.Exception.Message)" "Fatal error caught at entry." ""
        [void](def_WriteReports)
    } catch {}
}
finally {
    if ($def_PARAM_KEEP_POWERSHELL_OPEN) {
        Write-Host ""
        Write-Host "PowerShell session remains open." -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
