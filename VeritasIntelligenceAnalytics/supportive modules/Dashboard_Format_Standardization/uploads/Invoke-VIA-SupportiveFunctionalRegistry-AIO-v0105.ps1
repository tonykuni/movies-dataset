param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [int]$MaxTextBytes = 262144,
    [int]$MaxFiles = 0,
    [switch]$ApplyPlacement,
    [switch]$NoOpen,
    [bool]$KeepPowerShellOpen = $true
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "Continue"

function def_NowStamp {
    return (Get-Date).ToString("yyyyMMdd_HHmmss")
}

function def_WriteBanner {
    param([string]$RunId)
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · UNIFIED MANAGED RESOURCE REGISTRY · AIO v0105" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Base : $BaseDir" -ForegroundColor Gray
    Write-Host "Run  : $RunId" -ForegroundColor Gray
    Write-Host "Mode : Registry-first · No destructive delete · No dynamic import target" -ForegroundColor Yellow
    Write-Host ""
}

function def_EnsureDir {
    param([string]$PathValue)
    if (-not [string]::IsNullOrWhiteSpace($PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force -ErrorAction SilentlyContinue | Out-Null
    }
}

function def_WriteUtf8NoBom {
    param(
        [string]$PathValue,
        [string]$TextValue
    )
    $dir = Split-Path -Parent $PathValue
    def_EnsureDir -PathValue $dir
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($PathValue, $TextValue, $utf8)
}

function def_FindPython {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pythonCmd -and $pythonCmd.Source) {
        try {
            $ver = & $pythonCmd.Source --version 2>&1
            if ($LASTEXITCODE -eq 0 -or ($ver -match "Python")) {
                return [pscustomobject]@{ Exe = $pythonCmd.Source; PrefixArgs = @(); Version = ($ver -join " ") }
            }
        } catch {}
    }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pyCmd -and $pyCmd.Source) {
        try {
            $ver = & $pyCmd.Source -3 --version 2>&1
            if ($LASTEXITCODE -eq 0 -or ($ver -match "Python")) {
                return [pscustomobject]@{ Exe = $pyCmd.Source; PrefixArgs = @("-3"); Version = ($ver -join " ") }
            }
        } catch {}
    }
    return $null
}

function def_WriteFallbackHtml {
    param(
        [string]$RunDir,
        [string]$Message
    )
    def_EnsureDir -PathValue $RunDir
    $fallbackJson = Join-Path $RunDir "VIA_NoStall_FatalFallback.json"
    $fallbackHtml = Join-Path $RunDir "VIA_ModuleGovernance_UI.html"
    $payload = [ordered]@{
        ok = $false
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        base_dir = $BaseDir
        message = $Message
        policy = "No destructive delete. Fallback only."
    }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $fallbackJson -Encoding UTF8
    $safeMsg = [System.Net.WebUtility]::HtmlEncode($Message)
    $safeBase = [System.Net.WebUtility]::HtmlEncode($BaseDir)
    $html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA v0105 Fallback</title>
<style>body{font-family:'Microsoft JhengHei',Arial,sans-serif;background:#f9f9f6;color:#1f2933;padding:24px}.card{background:white;border:1px solid #d9ded8;border-radius:16px;padding:18px;max-width:960px}code{background:#f3f4f0;padding:2px 6px;border-radius:6px}</style></head>
<body><div class="card"><h1>VIA v0105 No-Stall Fallback</h1><p>主流程未能啟動 Python engine，但 PowerShell 沒有卡斷，也沒有刪除或覆蓋任何來源。</p><p><b>Base:</b> <code>$safeBase</code></p><pre>$safeMsg</pre></div></body></html>
"@
    def_WriteUtf8NoBom -PathValue $fallbackHtml -TextValue $html
    return $fallbackHtml
}

function def_CopyLatestOutputs {
    param(
        [string]$RunDir,
        [string]$RegistryRoot
    )
    $html = Join-Path $RunDir "VIA_ModuleGovernance_UI.html"
    $latestHtml = Join-Path $RegistryRoot "VIA_ModuleGovernance_UI_LATEST.html"
    if (Test-Path -LiteralPath $html) {
        Copy-Item -LiteralPath $html -Destination $latestHtml -Force -ErrorAction SilentlyContinue
    }
    $ssot = Join-Path $RunDir "VIA_ManagedResourceRegistry_SSOT.json"
    $latestSsot = Join-Path $RegistryRoot "VIA_ManagedResourceRegistry_SSOT_LATEST.json"
    if (Test-Path -LiteralPath $ssot) {
        Copy-Item -LiteralPath $ssot -Destination $latestSsot -Force -ErrorAction SilentlyContinue
    }
    return $latestHtml
}

function def_InvokeMain {
    $RunId = "RUN_$(def_NowStamp)_VIA_MANAGED_RESOURCE_REGISTRY_v0105"
    def_WriteBanner -RunId $RunId

    if (-not (Test-Path -LiteralPath $BaseDir)) {
        throw "BaseDir not found: $BaseDir"
    }

    $RegistryRoot = Join-Path $BaseDir "_via_registry\managed_resource_registry"
    $RunDir = Join-Path $RegistryRoot $RunId
    def_EnsureDir -PathValue $RunDir

    $EnginePath = Join-Path $RunDir "VIA_ManagedResourceRegistry_Engine_v0105.py"
    def_WriteUtf8NoBom -PathValue $EnginePath -TextValue $script:def_EngineSource

    $AcceleratorPs = @(
        "A01 Python engine offload — PowerShell only orchestrates",
        "A02 Type-neutral JSON line protocol",
        "A03 No-Fatal stage guard",
        "A04 Directory HashSet exclusion",
        "A05 Text read cap for huge logs/html",
        "A06 Suffix HashSet filtering",
        "A07 Static AST audit without target import",
        "A08 Safe JSON parsing",
        "A09 History-aware registry reuse",
        "A10 Registry-first placement plan",
        "A11 No destructive delete / no source overwrite",
        "A12 Dynamic Write-Progress from PROGRESS_JSON",
        "A13 HTML UI optimized for large matrices",
        "A14 CSV + JSON dual output",
        "A15 Fallback HTML if anything unexpected occurs"
    )
    Write-Host "def 15 PS Accelerators ON" -ForegroundColor Green
    foreach ($a in $AcceleratorPs) { Write-Host "  $a" -ForegroundColor DarkGray }
    Write-Host ""

    $python = def_FindPython
    if (-not $python) {
        $fallback = def_WriteFallbackHtml -RunDir $RunDir -Message "Python executable not found. Install Python or make sure python/py is on PATH."
        $latest = def_CopyLatestOutputs -RunDir $RunDir -RegistryRoot $RegistryRoot
        if (-not $NoOpen -and (Test-Path -LiteralPath $latest)) { Start-Process -FilePath $latest | Out-Null }
        Write-Host "[WARN] Python not found. Fallback HTML generated: $fallback" -ForegroundColor Yellow
        return
    }

    Write-Host "[OK] Python: $($python.Version)" -ForegroundColor Green
    Write-Host "[1/6] 啟動 Unified Managed Resource Registry engine..." -ForegroundColor Cyan

    $pyArgs = @()
    if ($python.PrefixArgs) { $pyArgs += @($python.PrefixArgs) }
    $pyArgs += @($EnginePath, "--base-dir", $BaseDir, "--output-dir", $RunDir, "--max-text-bytes", [string]$MaxTextBytes)
    if ($MaxFiles -gt 0) { $pyArgs += @("--max-files", [string]$MaxFiles) }
    if ($ApplyPlacement) { $pyArgs += "--apply-placement" }

    $lastProgress = 0
    try {
        & $python.Exe @pyArgs 2>&1 | ForEach-Object {
            $line = $_.ToString()
            if ($line.StartsWith("PROGRESS_JSON ")) {
                try {
                    $payload = $line.Substring("PROGRESS_JSON ".Length) | ConvertFrom-Json -ErrorAction Stop
                    $pct = [int]$payload.pct
                    $lastProgress = $pct
                    Write-Progress -Activity "VIA v0105 Unified Managed Resource Registry" -Status "$($payload.stage) · $($payload.message)" -PercentComplete $pct
                    Write-Host ("[{0,3}%] {1} · {2}" -f $pct, $payload.stage, $payload.message) -ForegroundColor DarkCyan
                } catch {
                    Write-Host $line -ForegroundColor DarkGray
                }
            } else {
                Write-Host $line -ForegroundColor Gray
            }
        }
        Write-Progress -Activity "VIA v0105 Unified Managed Resource Registry" -Completed
    } catch {
        $msg = "Python engine invocation captured error: $($_.Exception.Message)"
        Write-Host "[WARN] $msg" -ForegroundColor Yellow
        def_WriteFallbackHtml -RunDir $RunDir -Message $msg | Out-Null
    }

    $latestHtml = def_CopyLatestOutputs -RunDir $RunDir -RegistryRoot $RegistryRoot
    $runHtml = Join-Path $RunDir "VIA_ModuleGovernance_UI.html"

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0105 OUTPUTS" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Run HTML    : $runHtml" -ForegroundColor Green
    Write-Host "Latest HTML : $latestHtml" -ForegroundColor Green
    Write-Host "SSOT JSON   : $(Join-Path $RunDir 'VIA_ManagedResourceRegistry_SSOT.json')" -ForegroundColor Green
    Write-Host "CSV Matrix  : $(Join-Path $RunDir 'VIA_ManagedResourceMatrix.csv')" -ForegroundColor Green
    Write-Host "ErrorLedger : $(Join-Path $RunDir 'VIA_NoStall_ErrorLedger.json')" -ForegroundColor Green

    if (-not $NoOpen -and (Test-Path -LiteralPath $latestHtml)) {
        Write-Host "[OPEN] HTML U/I" -ForegroundColor Cyan
        Start-Process -FilePath $latestHtml | Out-Null
    }
}

# def EMBEDDED PYTHON ENGINE
$script:def_EngineSource = @'
from __future__ import annotations

# def PARAMETERS
import argparse
import ast
import csv
import hashlib
import html
import json
import os
import re
import sys
import traceback
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PARAM_VERSION = "v0105"
PARAM_ENGINE_NAME = "VIA Unified Managed Resource Registry"
PARAM_MAX_TEXT_BYTES_DEFAULT = 262_144
PARAM_MAX_HISTORY_FILES = 800
PARAM_MAX_CURRENT_FILES = 0
PARAM_EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "env", "node_modules", "dist", "build", ".cache", ".idea", ".vscode",
    "_envs", "_backup", "_backups", "backup", "backups", "site-packages"
}
PARAM_HISTORY_INCLUDE_DIR_HINTS = {
    "_via_registry", "_runs", "_viam_runs", "_vdf_system", "_vrn_system", "registry", "reports", "logs", "matrix"
}
PARAM_SUPPORTED_SUFFIXES = {
    ".py", ".ps1", ".psm1", ".json", ".jsonl", ".html", ".htm", ".md", ".txt", ".csv", ".yaml", ".yml", ".toml",
    ".docx", ".pdf", ".xlsx", ".parquet", ".duckdb", ".sqlite", ".db", ".png", ".jpg", ".jpeg", ".svg", ".ico"
}
PARAM_TEXT_SUFFIXES = {
    ".py", ".ps1", ".psm1", ".json", ".jsonl", ".html", ".htm", ".md", ".txt", ".csv", ".yaml", ".yml", ".toml", ".css", ".js"
}
PARAM_HASH_SUFFIXES = {".py", ".ps1", ".psm1", ".json", ".html", ".htm", ".md", ".txt", ".csv", ".yaml", ".yml", ".toml"}
PARAM_HISTORY_KEYWORDS = [
    "registry", "ssot", "matrix", "gate", "report", "index", "health", "summary", "seal", "ledger", "panorama", "latest", "run_"
]
PARAM_SUPPORTIVE_RULES = [
    {"manager": "VIA_EnvManager", "category": "environment", "keywords": ["envmanager", "env_manager", "environment", "venv", "route", "pip", "uv", "health"]},
    {"manager": "VIA_RegistryCore", "category": "registry", "keywords": ["registrycore", "registry_core", "registry", "module_index", "catalog", "manifest"]},
    {"manager": "VIA_SSOT_Unified", "category": "ssot", "keywords": ["ssot", "single_source", "unified", "canonical", "synonym", "alias"]},
    {"manager": "VIA_RuntimeBridge", "category": "runtime_bridge", "keywords": ["runtime_bridge", "bridge", "runtime", "bootstrap", "injector"]},
    {"manager": "VeritasAegisNexus", "category": "network", "keywords": ["aegis", "nexus", "http", "fetch", "request", "anti", "proxy", "cloudflare", "network"]},
    {"manager": "VeritasCeleritas", "category": "accelerator", "keywords": ["celeritas", "accelerator", "accel", "xmap", "parallel", "thread", "cache", "turbo"]},
    {"manager": "VIA_HardGate", "category": "governance", "keywords": ["hardgate", "gate", "governance", "policy", "risk", "hydra", "guard"]},
    {"manager": "VIA_UI_Manager", "category": "ui_support", "keywords": ["dashboard", "console", "ui", "html", "pwa", "visual", "theme", "layout"]},
    {"manager": "VIA_ParameterManager", "category": "parameters", "keywords": ["parameter", "param", "config", "setting", "schema", "route_table"]},
    {"manager": "VIA_AuditLedger", "category": "audit_tools", "keywords": ["audit", "ledger", "log", "summary", "report", "matrix", "history"]},
]
PARAM_FUNCTIONAL_RULES = [
    {"manager": "VDF", "category": "VDF", "keywords": ["vdf", "veritasdataforge", "twse", "tpex", "mops", "fetch", "stockdata", "fundamental"]},
    {"manager": "VRN", "category": "VRN", "keywords": ["vrn", "veritasreportnova", "pdf", "ocr", "table", "camelot", "pymupdf", "pdfplumber", "layout"]},
    {"manager": "VAP", "category": "VAP", "keywords": ["vap", "analytics", "portfolio", "performance", "risk", "factor", "backtest"]},
    {"manager": "VETF", "category": "VETF", "keywords": ["vetf", "active_etf", "etf"]},
    {"manager": "VIAS", "category": "VIAS", "keywords": ["vias", "asset", "asset_system"]},
    {"manager": "VPNS", "category": "VPNS", "keywords": ["vpns", "panorama", "nexus"]},
    {"manager": "Trading", "category": "Trading", "keywords": ["trading", "intraday", "signal", "strategy", "backtest", "alpha"]},
    {"manager": "Research", "category": "Research", "keywords": ["research", "macro", "industry", "equity", "report", "insight"]},
]
PARAM_FORBIDDEN_AST_NAMES = {"eval", "exec", "compile", "__import__"}
PARAM_RISK_IMPORTS_HIGH = {"subprocess", "socket", "ctypes", "winreg", "shutil"}
PARAM_RISK_IMPORTS_MED = {"os", "sys", "pathlib", "requests", "httpx", "aiohttp", "urllib", "webbrowser"}
PARAM_LIFECYCLE_METHODS = {"setup", "execute", "teardown", "pause", "resume", "health", "status"}
PARAM_RESOURCE_STATES = ["DISCOVERED", "REGISTERED_STATIC", "CONTRACT_READY", "NEEDS_REVIEW", "ERROR"]

# def DATA STRUCTURES
@dataclass
class ManagedResource:
    resource_id: str
    parent_id: str
    name: str
    path: str
    rel_path: str
    suffix: str
    domain: str
    manager: str
    category: str
    resource_type: str
    level: str
    loader: str
    state: str
    health: str
    risk: str
    size_bytes: int = 0
    mtime: str = ""
    sha12: str = ""
    parse_status: str = ""
    parse_error: str = ""
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    json_key_count: int = 0
    has_manifest: bool = False
    has_setup: bool = False
    has_execute: bool = False
    has_teardown: bool = False
    hot_reload_ready: str = "NO"
    config_scope: str = "GLOBAL_UNKNOWN"
    event_bus_ready: str = "UNKNOWN"
    dependency_count: int = 0
    direct_import_coupling: str = "UNKNOWN"
    placement_status: str = "REGISTER_ONLY"
    placement_target: str = ""
    notes: str = ""

@dataclass
class CodeEntity:
    entity_id: str
    parent_id: str
    name: str
    entity_type: str
    rel_path: str
    line: int
    manager: str
    risk: str
    lifecycle_role: str = ""
    notes: str = ""

@dataclass
class DependencyEdge:
    source_id: str
    source_name: str
    dependency: str
    dep_type: str
    risk: str
    notes: str = ""

@dataclass
class HistoryRecord:
    path: str
    rel_path: str
    name: str
    suffix: str
    history_type: str
    reuse_signal: str
    parse_status: str
    size_bytes: int
    mtime: str
    notes: str = ""

# def BASIC UTILS
def def_now_local() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def def_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def def_emit_progress(stage: str, pct: int, message: str) -> None:
    payload = {"stage": stage, "pct": int(max(0, min(100, pct))), "message": message, "time": def_now_local()}
    print("PROGRESS_JSON " + json.dumps(payload, ensure_ascii=False), flush=True)

def def_safe_rel(path_value: Path, base_dir: Path) -> str:
    try:
        return str(path_value.relative_to(base_dir))
    except Exception:
        return str(path_value)

def def_safe_read_text(path_value: Path, max_bytes: int) -> Tuple[str, str]:
    try:
        with path_value.open("rb") as f:
            data = f.read(max_bytes + 1)
        status = "OK" if len(data) <= max_bytes else "TRUNCATED"
        return data[:max_bytes].decode("utf-8", errors="replace"), status
    except Exception as exc:
        return "", "READ_ERROR: " + str(exc)

def def_safe_sha12(path_value: Path, suffix: str) -> str:
    if suffix.lower() not in PARAM_HASH_SUFFIXES:
        return ""
    try:
        h = hashlib.sha256()
        with path_value.open("rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()[:12]
    except Exception:
        return ""

def def_file_id(path_value: Path, base_dir: Path) -> str:
    rel = def_safe_rel(path_value, base_dir).replace("\\", "/")
    return "RES-" + hashlib.sha1(rel.encode("utf-8", errors="ignore")).hexdigest()[:16].upper()

def def_entity_id(parent_id: str, kind: str, name: str, line: int) -> str:
    raw = f"{parent_id}:{kind}:{name}:{line}"
    return "ENT-" + hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16].upper()

def def_should_exclude_dir(dir_name: str) -> bool:
    lower = dir_name.lower()
    if lower in PARAM_EXCLUDE_DIRS:
        return True
    if lower.endswith(".egg-info"):
        return True
    return False

def def_walk_files(base_dir: Path, include_registry: bool, max_files: int = 0) -> List[Path]:
    rows: List[Path] = []
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not def_should_exclude_dir(d)]
        if not include_registry:
            dirs[:] = [d for d in dirs if d.lower() != "_via_registry"]
        for fn in files:
            p = root_path / fn
            try:
                suffix = p.suffix.lower()
                if suffix not in PARAM_SUPPORTED_SUFFIXES:
                    continue
                rows.append(p)
                if max_files and len(rows) >= max_files:
                    return rows
            except Exception:
                continue
    return rows

def def_score_rules(path_value: Path, rules: List[Dict[str, Any]], base_dir: Path) -> Tuple[int, str, str]:
    text = (path_value.name + " " + def_safe_rel(path_value, base_dir) + " " + str(path_value.parent)).lower().replace("\\", "/")
    best_score = 0
    best_manager = "UNASSIGNED"
    best_category = "_inbox_to_classify"
    for rule in rules:
        score = 0
        for kw in rule.get("keywords", []):
            k = str(kw).lower()
            if k and k in text:
                score += 3 if k in path_value.name.lower() else 1
        if score > best_score:
            best_score = score
            best_manager = str(rule.get("manager", "UNASSIGNED"))
            best_category = str(rule.get("category", "_inbox_to_classify"))
    return best_score, best_manager, best_category

def def_classify_domain(path_value: Path, base_dir: Path) -> Tuple[str, str, str, str]:
    rel = def_safe_rel(path_value, base_dir).lower().replace("\\", "/")
    s_score, s_manager, s_cat = def_score_rules(path_value, PARAM_SUPPORTIVE_RULES, base_dir)
    f_score, f_manager, f_cat = def_score_rules(path_value, PARAM_FUNCTIONAL_RULES, base_dir)
    suffix = path_value.suffix.lower()
    if "supportive module" in rel or "supportive_module" in rel:
        if s_score == 0:
            s_manager, s_cat = "VIA_SupportiveInbox", "_inbox_to_classify"
        return "SUPPORTIVE", s_manager, s_cat, "supportive modules"
    if "functional module" in rel or "functional modules" in rel:
        if f_score == 0:
            f_manager, f_cat = "VIA_FunctionalInbox", "_inbox_to_classify"
        return "FUNCTIONAL", f_manager, f_cat, "functional modules"
    if f_score > s_score and f_score > 0:
        return "FUNCTIONAL", f_manager, f_cat, "functional modules"
    if s_score > 0:
        return "SUPPORTIVE", s_manager, s_cat, "supportive modules"
    if suffix in {".json", ".yaml", ".yml", ".toml"}:
        return "PARAMETER_DATA", "VIA_ParameterManager", "parameters", "supportive modules"
    if suffix in {".html", ".htm"}:
        return "UI", "VIA_UI_Manager", "ui_support", "supportive modules"
    if suffix in {".pdf", ".docx", ".md", ".txt"}:
        return "DOCUMENT", "VIA_DocumentRegistry", "documents", "supportive modules"
    return "UNKNOWN", "VIA_InboxClassifier", "_inbox_to_classify", "supportive modules"

def def_resource_type_and_loader(path_value: Path) -> Tuple[str, str, str]:
    suffix = path_value.suffix.lower()
    name = path_value.name.lower()
    if suffix == ".py":
        return "PY_MODULE", "ReflectionLoader", "MODULE"
    if suffix in {".ps1", ".psm1"}:
        return "PS_SCRIPT", "SubprocessLoader", "MODULE"
    if suffix in {".json", ".jsonl"}:
        return "JSON_DATA", "FileLoader", "DATA"
    if suffix in {".html", ".htm"}:
        return "HTML_UI", "FileLoader", "FILE"
    if suffix in {".yaml", ".yml", ".toml"} or name in {"requirements.txt", "pyproject.toml", "package.json"}:
        return "CONFIG_OR_LIB_MANIFEST", "FileLoader", "LIB"
    if suffix in {".pdf", ".docx", ".xlsx", ".md", ".txt"}:
        return "DOCUMENT", "FileLoader", "FILE"
    if suffix in {".parquet", ".duckdb", ".sqlite", ".db", ".csv"}:
        return "DATASTORE", "FileLoader", "DATA"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".ico"}:
        return "ASSET", "FileLoader", "FILE"
    return "FILE", "FileLoader", "FILE"

def def_guess_config_scope(path_value: Path, text: str) -> str:
    name = path_value.name.lower()
    rel = str(path_value).lower().replace("\\", "/")
    if any(k in name for k in ["ssot", "registry", "schema", "manifest", "system_config", "parameters", "config"]):
        if "plugins" in text[:2000].lower() or "module" in text[:2000].lower():
            return "NAMESPACED_OR_MANIFEST"
        return "SYSTEM_OR_GLOBAL"
    return "GLOBAL_UNKNOWN"

def def_extract_imports_from_ast(tree: ast.AST) -> List[str]:
    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return sorted(set(imports))

def def_analyze_python(path_value: Path, text: str, base_dir: Path) -> Tuple[Dict[str, Any], List[CodeEntity], List[DependencyEdge]]:
    info: Dict[str, Any] = {
        "parse_status": "UNKNOWN", "parse_error": "", "functions": [], "classes": [], "imports": [],
        "has_manifest": False, "has_setup": False, "has_execute": False, "has_teardown": False,
        "risk": "LOW", "direct_import_coupling": "LOW", "event_bus_ready": "UNKNOWN", "forbidden": []
    }
    entities: List[CodeEntity] = []
    edges: List[DependencyEdge] = []
    parent_id = def_file_id(path_value, base_dir)
    try:
        tree = ast.parse(text, filename=str(path_value))
        info["parse_status"] = "AST_OK"
        imports = def_extract_imports_from_ast(tree)
        info["imports"] = imports
        forbidden: List[str] = []
        lifecycle_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info["functions"].append(node.name)
                if node.name in PARAM_LIFECYCLE_METHODS:
                    lifecycle_names.add(node.name)
                role = "LIFECYCLE" if node.name in PARAM_LIFECYCLE_METHODS else "FUNCTION"
                entities.append(CodeEntity(
                    entity_id=def_entity_id(parent_id, "function", node.name, getattr(node, "lineno", 0)),
                    parent_id=parent_id, name=node.name, entity_type="FUNCTION", rel_path=def_safe_rel(path_value, base_dir),
                    line=getattr(node, "lineno", 0), manager="ReflectionLoader", risk="LOW", lifecycle_role=role
                ))
            elif isinstance(node, ast.ClassDef):
                info["classes"].append(node.name)
                entities.append(CodeEntity(
                    entity_id=def_entity_id(parent_id, "class", node.name, getattr(node, "lineno", 0)),
                    parent_id=parent_id, name=node.name, entity_type="CLASS", rel_path=def_safe_rel(path_value, base_dir),
                    line=getattr(node, "lineno", 0), manager="ReflectionLoader", risk="LOW", lifecycle_role="CLASS"
                ))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {"__manifest__", "MANIFEST", "manifest"}:
                        info["has_manifest"] = True
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in PARAM_FORBIDDEN_AST_NAMES:
                    forbidden.append(node.func.id)
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    forbidden.append("open")
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"system", "popen", "remove", "rmtree"}:
                        forbidden.append(node.func.attr)
        info["has_setup"] = "setup" in lifecycle_names
        info["has_execute"] = "execute" in lifecycle_names
        info["has_teardown"] = "teardown" in lifecycle_names
        for imp in imports:
            risk = "HIGH" if imp in PARAM_RISK_IMPORTS_HIGH else ("MEDIUM" if imp in PARAM_RISK_IMPORTS_MED else "LOW")
            edges.append(DependencyEdge(parent_id, path_value.stem, imp, "python_import", risk))
        if any(imp in PARAM_RISK_IMPORTS_HIGH for imp in imports) or forbidden:
            info["risk"] = "HIGH"
        elif any(imp in PARAM_RISK_IMPORTS_MED for imp in imports):
            info["risk"] = "MEDIUM"
        plugin_imports = [imp for imp in imports if imp.lower() in {"plugins", "plugin", "modules"}]
        info["direct_import_coupling"] = "HIGH" if plugin_imports else "LOW"
        if "bus" in text.lower() and ("subscribe" in text.lower() or "publish" in text.lower()):
            info["event_bus_ready"] = "YES_SIGNAL"
        info["forbidden"] = sorted(set(forbidden))
    except Exception as exc:
        info["parse_status"] = "AST_ERROR"
        info["parse_error"] = str(exc)
        info["risk"] = "HIGH"
    return info, entities, edges

def def_analyze_powershell(path_value: Path, text: str, base_dir: Path) -> Tuple[Dict[str, Any], List[CodeEntity]]:
    info = {"parse_status": "TEXT_OK", "functions": [], "risk": "LOW", "has_manifest": False}
    entities: List[CodeEntity] = []
    parent_id = def_file_id(path_value, base_dir)
    try:
        for m in re.finditer(r"(?im)^\s*function\s+([A-Za-z0-9_\-:]+)", text):
            name = m.group(1)
            line = text[:m.start()].count("\n") + 1
            info["functions"].append(name)
            entities.append(CodeEntity(def_entity_id(parent_id, "ps_function", name, line), parent_id, name, "PS_FUNCTION", def_safe_rel(path_value, base_dir), line, "SubprocessLoader", "LOW"))
        risky = ["Invoke-Expression", "iex", "Remove-Item", "Stop-Process", "Set-ExecutionPolicy", "Start-Process"]
        found = [x for x in risky if re.search(re.escape(x), text, flags=re.IGNORECASE)]
        if found:
            info["risk"] = "HIGH" if any(x.lower() in ["invoke-expression", "iex", "remove-item", "stop-process"] for x in found) else "MEDIUM"
            info["risky_tokens"] = found
        if "MANIFEST" in text or "__manifest__" in text:
            info["has_manifest"] = True
    except Exception as exc:
        info["parse_status"] = "TEXT_ERROR: " + str(exc)
        info["risk"] = "HIGH"
    return info, entities

def def_analyze_json(path_value: Path, text: str) -> Dict[str, Any]:
    info = {"parse_status": "UNKNOWN", "json_key_count": 0, "has_manifest": False, "risk": "LOW"}
    try:
        if path_value.suffix.lower() == ".jsonl":
            count = 0
            for line in text.splitlines()[:200]:
                if line.strip():
                    json.loads(line)
                    count += 1
            info["parse_status"] = "JSONL_OK"
            info["json_key_count"] = count
        else:
            payload = json.loads(text) if text.strip() else None
            info["parse_status"] = "JSON_OK"
            if isinstance(payload, dict):
                info["json_key_count"] = len(payload)
                info["has_manifest"] = any(k.lower() in {"manifest", "name", "version", "dependencies", "modules", "plugins"} for k in payload.keys())
            elif isinstance(payload, list):
                info["json_key_count"] = len(payload)
    except Exception as exc:
        info["parse_status"] = "JSON_ERROR"
        info["parse_error"] = str(exc)
        info["risk"] = "MEDIUM"
    return info

def def_make_resource(path_value: Path, base_dir: Path, max_text_bytes: int) -> Tuple[ManagedResource, List[CodeEntity], List[DependencyEdge]]:
    rel = def_safe_rel(path_value, base_dir)
    suffix = path_value.suffix.lower()
    stat = path_value.stat()
    domain, manager, category, target_root = def_classify_domain(path_value, base_dir)
    rtype, loader, level = def_resource_type_and_loader(path_value)
    resource_id = def_file_id(path_value, base_dir)
    parse_status = "BINARY_OR_SKIPPED"
    parse_error = ""
    risk = "LOW"
    health = "GREEN"
    function_count = 0
    class_count = 0
    import_count = 0
    json_key_count = 0
    has_manifest = False
    has_setup = False
    has_execute = False
    has_teardown = False
    direct_import_coupling = "UNKNOWN"
    event_bus_ready = "UNKNOWN"
    config_scope = "GLOBAL_UNKNOWN"
    dependency_edges: List[DependencyEdge] = []
    entities: List[CodeEntity] = []
    notes = ""
    if suffix in PARAM_TEXT_SUFFIXES:
        text, read_status = def_safe_read_text(path_value, max_text_bytes)
        parse_status = read_status
        config_scope = def_guess_config_scope(path_value, text)
        if suffix == ".py":
            py_info, py_entities, py_edges = def_analyze_python(path_value, text, base_dir)
            entities.extend(py_entities)
            dependency_edges.extend(py_edges)
            parse_status = py_info.get("parse_status", parse_status)
            parse_error = py_info.get("parse_error", "")
            function_count = len(py_info.get("functions", []))
            class_count = len(py_info.get("classes", []))
            import_count = len(py_info.get("imports", []))
            has_manifest = bool(py_info.get("has_manifest"))
            has_setup = bool(py_info.get("has_setup"))
            has_execute = bool(py_info.get("has_execute"))
            has_teardown = bool(py_info.get("has_teardown"))
            risk = py_info.get("risk", "LOW")
            direct_import_coupling = py_info.get("direct_import_coupling", "UNKNOWN")
            event_bus_ready = py_info.get("event_bus_ready", "UNKNOWN")
            if py_info.get("forbidden"):
                notes += "AST_RISK=" + ",".join(py_info.get("forbidden", []))
        elif suffix in {".ps1", ".psm1"}:
            ps_info, ps_entities = def_analyze_powershell(path_value, text, base_dir)
            entities.extend(ps_entities)
            parse_status = ps_info.get("parse_status", parse_status)
            function_count = len(ps_info.get("functions", []))
            has_manifest = bool(ps_info.get("has_manifest"))
            risk = ps_info.get("risk", "LOW")
            if ps_info.get("risky_tokens"):
                notes += "PS_RISK=" + ",".join(ps_info.get("risky_tokens", []))
        elif suffix in {".json", ".jsonl"}:
            js_info = def_analyze_json(path_value, text)
            parse_status = js_info.get("parse_status", parse_status)
            parse_error = js_info.get("parse_error", "")
            json_key_count = int(js_info.get("json_key_count", 0))
            has_manifest = bool(js_info.get("has_manifest"))
            risk = js_info.get("risk", "LOW")
        else:
            parse_status = read_status
    if parse_status.endswith("ERROR") or "ERROR" in parse_status:
        health = "RED" if suffix in {".py", ".json"} else "YELLOW"
    elif risk == "HIGH":
        health = "YELLOW"
    hot_reload_ready = "YES" if (rtype == "PY_MODULE" and has_setup and has_execute and has_teardown) else ("PARTIAL" if rtype == "PY_MODULE" and (has_setup or has_execute or has_teardown) else "NO")
    if has_manifest and rtype in {"PY_MODULE", "JSON_DATA", "CONFIG_OR_LIB_MANIFEST"}:
        state = "CONTRACT_READY" if hot_reload_ready in {"YES", "PARTIAL"} or rtype != "PY_MODULE" else "REGISTERED_STATIC"
    elif parse_status.endswith("ERROR") or "ERROR" in parse_status:
        state = "ERROR"
    else:
        state = "REGISTERED_STATIC"
    placement_target = str(Path(target_root) / category / path_value.name)
    placement_status = "ALREADY_CANONICAL" if target_root.lower() in rel.lower().replace("\\", "/") and category.lower() in rel.lower() else "REGISTER_OR_COPY_PLAN"
    res = ManagedResource(
        resource_id=resource_id,
        parent_id="",
        name=path_value.name,
        path=str(path_value),
        rel_path=rel,
        suffix=suffix,
        domain=domain,
        manager=manager,
        category=category,
        resource_type=rtype,
        level=level,
        loader=loader,
        state=state,
        health=health,
        risk=risk,
        size_bytes=stat.st_size,
        mtime=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        sha12=def_safe_sha12(path_value, suffix),
        parse_status=parse_status,
        parse_error=parse_error,
        function_count=function_count,
        class_count=class_count,
        import_count=import_count,
        json_key_count=json_key_count,
        has_manifest=has_manifest,
        has_setup=has_setup,
        has_execute=has_execute,
        has_teardown=has_teardown,
        hot_reload_ready=hot_reload_ready,
        config_scope=config_scope,
        event_bus_ready=event_bus_ready,
        dependency_count=len(dependency_edges),
        direct_import_coupling=direct_import_coupling,
        placement_status=placement_status,
        placement_target=placement_target,
        notes=notes,
    )
    return res, entities, dependency_edges

def def_scan_history(base_dir: Path, max_text_bytes: int) -> List[HistoryRecord]:
    history: List[HistoryRecord] = []
    try:
        files = def_walk_files(base_dir, include_registry=True, max_files=0)
    except Exception:
        return history
    candidates: List[Path] = []
    for p in files:
        rel = def_safe_rel(p, base_dir).lower().replace("\\", "/")
        name = p.name.lower()
        in_hint_dir = any(h in rel for h in PARAM_HISTORY_INCLUDE_DIR_HINTS)
        key_hit = any(k in name or k in rel for k in PARAM_HISTORY_KEYWORDS)
        if in_hint_dir or key_hit:
            candidates.append(p)
            if len(candidates) >= PARAM_MAX_HISTORY_FILES:
                break
    total = max(1, len(candidates))
    for i, p in enumerate(candidates, start=1):
        if i % 25 == 0:
            def_emit_progress("History", min(18, 2 + int(i / total * 16)), f"history {i}/{total}")
        try:
            stat = p.stat()
            suffix = p.suffix.lower()
            text = ""
            parse_status = "INDEXED"
            notes = ""
            if suffix in PARAM_TEXT_SUFFIXES:
                text, read_status = def_safe_read_text(p, min(max_text_bytes, 64_000))
                parse_status = read_status
                if suffix == ".json":
                    try:
                        json.loads(text) if text.strip() else None
                        parse_status = "JSON_OK"
                    except Exception as exc:
                        parse_status = "JSON_ERROR"
                        notes = str(exc)[:180]
                elif suffix in {".html", ".htm"}:
                    parse_status = "HTML_INDEXED"
            lower = (p.name + " " + def_safe_rel(p, base_dir)).lower()
            if "ssot" in lower:
                htype, signal = "SSOT", "HIGH_REUSE"
            elif "registry" in lower or "index" in lower:
                htype, signal = "REGISTRY", "HIGH_REUSE"
            elif "gate" in lower or "seal" in lower:
                htype, signal = "GATE_OR_SEAL", "MEDIUM_REUSE"
            elif "matrix" in lower or "report" in lower or suffix in {".html", ".htm"}:
                htype, signal = "REPORT_OR_MATRIX", "MEDIUM_REUSE"
            elif "ledger" in lower or "log" in lower:
                htype, signal = "LEDGER_OR_LOG", "LOW_REUSE"
            else:
                htype, signal = "HISTORY", "LOW_REUSE"
            history.append(HistoryRecord(str(p), def_safe_rel(p, base_dir), p.name, suffix, htype, signal, parse_status, stat.st_size, datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"), notes))
        except Exception as exc:
            history.append(HistoryRecord(str(p), def_safe_rel(p, base_dir), p.name, p.suffix.lower(), "HISTORY", "ERROR_CAPTURED", "SCAN_ERROR", 0, "", str(exc)[:180]))
    return history

def def_build_topology(resources: List[ManagedResource], edges: List[DependencyEdge]) -> Dict[str, Any]:
    by_name = {Path(r.name).stem.lower(): r.resource_id for r in resources if r.resource_type == "PY_MODULE"}
    graph = defaultdict(set)
    reverse = defaultdict(set)
    internal_edges = []
    for e in edges:
        dep_key = e.dependency.lower()
        if dep_key in by_name:
            target = by_name[dep_key]
            if target == e.source_id:
                continue
            graph[e.source_id].add(target)
            reverse[target].add(e.source_id)
            internal_edges.append({"source_id": e.source_id, "target_id": target, "dependency": e.dependency, "risk": e.risk})
    indeg = {r.resource_id: 0 for r in resources}
    for s, targets in graph.items():
        for t in targets:
            indeg[t] = indeg.get(t, 0) + 1
            indeg.setdefault(s, 0)
    q = deque([k for k, v in indeg.items() if v == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for t in graph.get(n, []):
            indeg[t] -= 1
            if indeg[t] == 0:
                q.append(t)
    cycle_count = len(indeg) - len(order)
    return {"internal_edges": internal_edges, "topological_order_count": len(order), "cycle_count": cycle_count}

def def_apply_placement(resources: List[ManagedResource], base_dir: Path, apply: bool, output_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not apply:
        for r in resources:
            rows.append({"resource_id": r.resource_id, "name": r.name, "status": "REVIEW_ONLY_NO_COPY", "target": r.placement_target})
        return rows
    mirror_root = output_dir / "canonical_mirror"
    for r in resources:
        try:
            src = Path(r.path)
            target = mirror_root / r.placement_target
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target = target.with_name(target.stem + "__" + r.resource_id[-6:] + target.suffix)
            if src.is_file():
                import shutil
                shutil.copy2(src, target)
                rows.append({"resource_id": r.resource_id, "name": r.name, "status": "COPIED_TO_MIRROR", "target": str(target)})
            else:
                rows.append({"resource_id": r.resource_id, "name": r.name, "status": "SOURCE_MISSING", "target": str(target)})
        except Exception as exc:
            rows.append({"resource_id": r.resource_id, "name": r.name, "status": "COPY_ERROR", "target": r.placement_target, "error": str(exc)})
    return rows

def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def def_write_csv(path_value: Path, rows: List[Dict[str, Any]]) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path_value.write_text("", encoding="utf-8-sig")
        return
    keys = sorted({k for row in rows for k in row.keys()})
    with path_value.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

def def_html_table(rows: List[Dict[str, Any]], columns: List[str], max_rows: int = 500) -> str:
    th = "".join(f"<th>{html.escape(c)}</th>" for c in columns)
    trs = []
    for row in rows[:max_rows]:
        tds = []
        for c in columns:
            v = row.get(c, "")
            if isinstance(v, bool):
                v = "YES" if v else "NO"
            elif isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False)
            cls = ""
            if c.lower() in {"health", "risk", "state", "parse_status", "hot_reload_ready"}:
                s = str(v).upper()
                if any(x in s for x in ["GREEN", "OK", "YES", "READY", "LOW"]):
                    cls = " class='ok'"
                elif any(x in s for x in ["YELLOW", "WARN", "PARTIAL", "MEDIUM", "REVIEW"]):
                    cls = " class='warn'"
                elif any(x in s for x in ["RED", "ERROR", "HIGH", "NO"]):
                    cls = " class='bad'"
            tds.append(f"<td{cls}>{html.escape(str(v))}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    more = "" if len(rows) <= max_rows else f"<tr><td colspan='{len(columns)}'>Showing {max_rows} / {len(rows)} rows. Full JSON/CSV exported.</td></tr>"
    return f"<div class='tablewrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}{more}</tbody></table></div>"

def def_write_html(output_path: Path, summary: Dict[str, Any], resources: List[Dict[str, Any]], entities: List[Dict[str, Any]], edges: List[Dict[str, Any]], history: List[Dict[str, Any]], placement: List[Dict[str, Any]], topology: Dict[str, Any], accelerators: List[Dict[str, Any]]) -> None:
    counters = summary.get("counters", {})
    cards = "".join(f"<div class='card'><div class='num'>{html.escape(str(v))}</div><div class='lbl'>{html.escape(str(k))}</div></div>" for k, v in counters.items())
    resource_cols = ["resource_id", "name", "domain", "manager", "category", "resource_type", "level", "loader", "state", "health", "risk", "hot_reload_ready", "parse_status", "function_count", "class_count", "import_count", "placement_status", "rel_path"]
    entity_cols = ["entity_id", "parent_id", "entity_type", "name", "line", "manager", "risk", "lifecycle_role", "rel_path"]
    edge_cols = ["source_name", "dependency", "dep_type", "risk", "notes"]
    history_cols = ["history_type", "reuse_signal", "parse_status", "name", "rel_path", "size_bytes", "mtime", "notes"]
    placement_cols = ["resource_id", "name", "status", "target"]
    acc_cols = ["id", "name", "status", "purpose"]
    lifecycle_rows = []
    for r in resources:
        lifecycle_rows.append({
            "name": r.get("name"), "manager": r.get("manager"), "state": r.get("state"),
            "has_manifest": r.get("has_manifest"), "setup": r.get("has_setup"), "execute": r.get("has_execute"), "teardown": r.get("has_teardown"),
            "hot_reload_ready": r.get("hot_reload_ready"), "event_bus_ready": r.get("event_bus_ready"), "direct_import_coupling": r.get("direct_import_coupling"), "rel_path": r.get("rel_path")
        })
    param_rows = []
    for r in resources:
        if r.get("resource_type") in {"JSON_DATA", "CONFIG_OR_LIB_MANIFEST"} or r.get("category") == "parameters":
            param_rows.append({"name": r.get("name"), "manager": r.get("manager"), "config_scope": r.get("config_scope"), "parse_status": r.get("parse_status"), "json_key_count": r.get("json_key_count"), "has_manifest": r.get("has_manifest"), "health": r.get("health"), "rel_path": r.get("rel_path")})
    html_text = f"""<!doctype html>
<html lang='zh-Hant'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>VIA Unified Managed Resource Registry {html.escape(PARAM_VERSION)}</title>
<style>
:root{{--bg:#f9f9f6;--surface:#fff;--ink:#1f2933;--muted:#6b7c78;--line:#d9ded8;--ok:#166534;--warn:#b7791f;--bad:#b91c1c;--blue:#2563eb;--teal:#0f766e;--seal:#9f1d1d}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#f9f9f6,#edf5f2);color:var(--ink);font-family:'Noto Sans TC','Microsoft JhengHei',Arial,sans-serif;font-size:13px;line-height:1.55}}
.wrap{{max-width:1680px;margin:0 auto;padding:22px}}.hero{{background:rgba(255,255,255,.86);border:1px solid var(--line);border-radius:22px;padding:24px;box-shadow:0 12px 36px rgba(31,41,51,.08);position:relative;overflow:hidden}}
.hero:before{{content:'理';position:absolute;right:28px;top:12px;font-size:74px;font-weight:900;color:rgba(159,29,29,.11)}}h1{{margin:0;font-size:26px;letter-spacing:-.04em}}.sub{{color:var(--muted);margin-top:6px}}.policy{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}}.pill{{border:1px solid var(--line);border-radius:999px;padding:4px 10px;background:#fff;color:var(--muted);font-size:12px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:16px 0}}.card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px;box-shadow:0 4px 18px rgba(31,41,51,.05)}}.num{{font:800 24px ui-monospace,Consolas,monospace}}.lbl{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}}.section{{margin-top:16px;background:rgba(255,255,255,.9);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 6px 22px rgba(31,41,51,.05)}}h2{{font-size:18px;margin:0 0 10px}}.toolbar{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}}input,select{{padding:8px 10px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink)}}button{{padding:8px 12px;border:1px solid var(--line);background:#fff;border-radius:10px;cursor:pointer}}button:hover{{border-color:var(--teal);color:var(--teal)}}.tablewrap{{overflow:auto;max-height:560px;border:1px solid var(--line);border-radius:12px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{border-bottom:1px solid #edf0eb;padding:7px 8px;text-align:left;vertical-align:top;white-space:nowrap}}th{{position:sticky;top:0;background:#f3f7f4;z-index:1;font-size:12px;color:#3d4b45}}td{{font-size:12px}}.ok{{color:var(--ok);font-weight:700}}.warn{{color:var(--warn);font-weight:700}}.bad{{color:var(--bad);font-weight:700}}code{{background:#f3f4f0;border:1px solid var(--line);border-radius:6px;padding:1px 5px}}.foot{{color:var(--muted);margin:18px 0;text-align:center}}.matrix-note{{color:var(--muted);font-size:12px;margin:4px 0 10px}}
</style>
</head>
<body>
<div class='wrap'>
  <div class='hero'>
    <h1>VIA Unified Managed Resource Registry · {html.escape(PARAM_VERSION)}</h1>
    <div class='sub'>JSON / PY / PS / HTML / 文件 / SYSTEM / MODULE / CLASS / FUNCTION / LIBS · 統一受控資源層 · 不卡斷 · 動態進度 · History-aware</div>
    <div class='policy'><span class='pill'>No destructive delete</span><span class='pill'>No exec/eval loading</span><span class='pill'>Static AST audit</span><span class='pill'>Registry-first</span><span class='pill'>Review-only by default</span><span class='pill'>Generated {html.escape(summary.get('generated_at',''))}</span></div>
  </div>
  <div class='grid'>{cards}</div>
  <div class='section'><h2>def Resource Filter</h2><div class='toolbar'><input id='q' placeholder='搜尋檔名 / manager / path / type...' oninput='filterTables()'><select id='domain' onchange='filterTables()'><option value=''>All Domains</option><option>SUPPORTIVE</option><option>FUNCTIONAL</option><option>PARAMETER_DATA</option><option>UI</option><option>DOCUMENT</option><option>UNKNOWN</option></select><button onclick='resetFilter()'>Reset</button></div><div class='matrix-note'>下列表格已輸出完整 JSON / CSV；HTML 預設只顯示前 500 筆。</div></div>
  <div class='section'><h2>def Managed Resource Matrix</h2>{def_html_table(resources, resource_cols)}</div>
  <div class='section'><h2>def Lifecycle / Hot-Reload Readiness Matrix</h2>{def_html_table(lifecycle_rows, ['name','manager','state','has_manifest','setup','execute','teardown','hot_reload_ready','event_bus_ready','direct_import_coupling','rel_path'])}</div>
  <div class='section'><h2>def Parameter Integration Matrix</h2>{def_html_table(param_rows, ['name','manager','config_scope','parse_status','json_key_count','has_manifest','health','rel_path'])}</div>
  <div class='section'><h2>def Code Structure Matrix · CLASS / FUNCTION / PS_FUNCTION</h2>{def_html_table(entities, entity_cols)}</div>
  <div class='section'><h2>def Dependency / Import Risk Matrix</h2><div class='matrix-note'>Internal cycle count: {html.escape(str(topology.get('cycle_count',0)))} · Internal edges: {html.escape(str(len(topology.get('internal_edges',[]))))}</div>{def_html_table(edges, edge_cols)}</div>
  <div class='section'><h2>def Historical Record Reuse Matrix</h2>{def_html_table(history, history_cols)}</div>
  <div class='section'><h2>def Placement Plan / Mirror Copy Result</h2>{def_html_table(placement, placement_cols)}</div>
  <div class='section'><h2>def 15 PowerShell + System Accelerators</h2>{def_html_table(accelerators, acc_cols)}</div>
  <div class='foot'>VIA · Veritas Intelligence Analytics · 判天地之美，析萬物之理</div>
</div>
<script>
function norm(s){{return (s||'').toString().toLowerCase()}}
function filterTables(){{
  const q=norm(document.getElementById('q').value); const d=norm(document.getElementById('domain').value);
  document.querySelectorAll('tbody tr').forEach(tr=>{{
    const txt=norm(tr.innerText); let show=true; if(q && !txt.includes(q)) show=false; if(d && !txt.includes(d)) show=false; tr.style.display=show?'':'none';
  }});
}}
function resetFilter(){{document.getElementById('q').value='';document.getElementById('domain').value='';filterTables();}}
</script>
</body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")

def def_make_accelerators() -> List[Dict[str, Any]]:
    names = [
        ("A01", "Python engine offload", "避免 PowerShell 型別集合炸裂"),
        ("A02", "Type-neutral PSCustomObject/Dict", "所有掃描結果用中立字典輸出"),
        ("A03", "No-Fatal stage guard", "每階段失敗只入 ledger"),
        ("A04", "Directory exclusion HashSet", "快速跳過 _envs/node_modules/venv"),
        ("A05", "Text read cap", "大型 HTML/log 不拖垮掃描"),
        ("A06", "Suffix HashSet", "只掃描可治理格式"),
        ("A07", "Static AST audit", "不 import 目標模組也能分析 class/function/import"),
        ("A08", "JSON safe parse", "壞 JSON 不阻斷主流程"),
        ("A09", "History-aware reuse", "吸收舊 Registry/SSOT/Gate/Matrix"),
        ("A10", "Registry-first placement", "先註冊，再視情況 mirror copy"),
        ("A11", "No destructive delete", "不刪原始檔、不覆蓋來源"),
        ("A12", "Dynamic progress", "PROGRESS_JSON + Write-Progress"),
        ("A13", "HTML StringBuilder equivalent", "一次生成 UI，避免反覆 DOM 拼接"),
        ("A14", "CSV/JSON dual output", "方便 DuckDB/Excel/後續引擎讀取"),
        ("A15", "Fallback HTML", "Fatal 也保底產出可讀報告"),
    ]
    return [{"id": i, "name": n, "status": "ON", "purpose": p} for i, n, p in names]

def def_write_fallback(output_dir: Path, error: str, tb: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"ok": False, "error": error, "traceback": tb, "generated_at": def_now_local()}
    def_write_json(output_dir / "VIA_NoStall_FatalFallback.json", payload)
    fallback_html = f"""<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VIA v0105 Fallback</title><body style='font-family:Microsoft JhengHei,Arial;padding:24px;background:#f9f9f6'><h1>VIA v0105 No-Stall Fallback</h1><p>主流程遇到未預期錯誤，但 PowerShell 不應卡斷；請看 JSON。</p><pre>{html.escape(error)}\n\n{html.escape(tb[:4000])}</pre></body></html>"""
    (output_dir / "VIA_ModuleGovernance_UI.html").write_text(fallback_html, encoding="utf-8")

def def_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-text-bytes", type=int, default=PARAM_MAX_TEXT_BYTES_DEFAULT)
    parser.add_argument("--max-files", type=int, default=PARAM_MAX_CURRENT_FILES)
    parser.add_argument("--apply-placement", action="store_true")
    args = parser.parse_args()
    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        def_emit_progress("Start", 1, "initialize managed resource registry")
        if not base_dir.exists():
            raise FileNotFoundError(f"Base dir not found: {base_dir}")
        accelerators = def_make_accelerators()
        def_emit_progress("History", 3, "scan historical registry / ssot / matrix / gate records")
        history_records = def_scan_history(base_dir, args.max_text_bytes)
        def_emit_progress("Discovery", 20, "scan current project files")
        current_files = def_walk_files(base_dir, include_registry=False, max_files=args.max_files)
        total = max(1, len(current_files))
        resources: List[ManagedResource] = []
        entities: List[CodeEntity] = []
        edges: List[DependencyEdge] = []
        errors: List[Dict[str, Any]] = []
        for i, p in enumerate(current_files, start=1):
            if i == 1 or i % 25 == 0 or i == total:
                pct = 20 + int(i / total * 45)
                def_emit_progress("Classify", pct, f"classify {i}/{total}: {p.name}")
            try:
                res, ents, deps = def_make_resource(p, base_dir, args.max_text_bytes)
                resources.append(res)
                entities.extend(ents)
                edges.extend(deps)
            except Exception as exc:
                errors.append({"path": str(p), "error": str(exc), "traceback": traceback.format_exc()})
        def_emit_progress("Topology", 68, "build dependency topology and lifecycle matrices")
        topology = def_build_topology(resources, edges)
        def_emit_progress("Placement", 75, "build placement plan / optional mirror copy")
        placement = def_apply_placement(resources, base_dir, bool(args.apply_placement), output_dir)
        res_rows = [asdict(r) for r in resources]
        ent_rows = [asdict(e) for e in entities]
        edge_rows = [asdict(e) for e in edges]
        hist_rows = [asdict(h) for h in history_records]
        def_emit_progress("Registry", 84, "write JSON and CSV outputs")
        counters = {
            "Resources": len(res_rows),
            "Supportive": sum(1 for r in res_rows if r.get("domain") == "SUPPORTIVE"),
            "Functional": sum(1 for r in res_rows if r.get("domain") == "FUNCTIONAL"),
            "PY": sum(1 for r in res_rows if r.get("resource_type") == "PY_MODULE"),
            "PS": sum(1 for r in res_rows if r.get("resource_type") == "PS_SCRIPT"),
            "JSON": sum(1 for r in res_rows if r.get("resource_type") == "JSON_DATA"),
            "HTML": sum(1 for r in res_rows if r.get("resource_type") == "HTML_UI"),
            "Classes": len([e for e in ent_rows if e.get("entity_type") == "CLASS"]),
            "Functions": len([e for e in ent_rows if "FUNCTION" in str(e.get("entity_type"))]),
            "History": len(hist_rows),
            "Errors": len(errors),
            "HighRisk": sum(1 for r in res_rows if r.get("risk") == "HIGH"),
        }
        summary = {
            "ok": True,
            "engine": PARAM_ENGINE_NAME,
            "version": PARAM_VERSION,
            "generated_at": def_now_local(),
            "generated_at_utc": def_now_utc(),
            "base_dir": str(base_dir),
            "output_dir": str(output_dir),
            "apply_placement": bool(args.apply_placement),
            "counters": counters,
            "topology": topology,
            "policy": {
                "delete_original": False,
                "overwrite_source": False,
                "dynamic_import_target": False,
                "exec_eval_loading": False,
                "review_only_default": not bool(args.apply_placement),
            }
        }
        def_write_json(output_dir / "VIA_ManagedResourceRegistry_SSOT.json", {"summary": summary, "resources": res_rows, "entities": ent_rows, "dependencies": edge_rows, "history": hist_rows, "placement": placement, "accelerators": accelerators, "errors": errors})
        def_write_json(output_dir / "VIA_ManagedResourceRegistry_Summary.json", summary)
        def_write_json(output_dir / "VIA_NoStall_ErrorLedger.json", errors)
        def_write_json(output_dir / "VIA_15_PS_AcceleratorMatrix.json", accelerators)
        def_write_csv(output_dir / "VIA_ManagedResourceMatrix.csv", res_rows)
        def_write_csv(output_dir / "VIA_CodeStructureMatrix.csv", ent_rows)
        def_write_csv(output_dir / "VIA_DependencyRiskMatrix.csv", edge_rows)
        def_write_csv(output_dir / "VIA_HistoricalReuseMatrix.csv", hist_rows)
        def_emit_progress("HTML", 94, "render optimized HTML UI")
        def_write_html(output_dir / "VIA_ModuleGovernance_UI.html", summary, res_rows, ent_rows, edge_rows, hist_rows, placement, topology, accelerators)
        def_emit_progress("Done", 100, "completed managed resource registry")
        print(json.dumps({"ok": True, "html": str(output_dir / "VIA_ModuleGovernance_UI.html"), "summary": summary}, ensure_ascii=False), flush=True)
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        def_write_fallback(output_dir, str(exc), tb)
        def_emit_progress("Fallback", 100, "fatal captured; fallback HTML written")
        print(json.dumps({"ok": False, "error": str(exc), "html": str(output_dir / "VIA_ModuleGovernance_UI.html")}, ensure_ascii=False), flush=True)
        return 0

if __name__ == "__main__":
    raise SystemExit(def_main())

'@

try {
    def_InvokeMain
} catch {
    Write-Host "" 
    Write-Host "[FATAL-CAPTURED] $($_.Exception.Message)" -ForegroundColor Yellow
    try {
        $RegistryRoot = Join-Path $BaseDir "_via_registry\managed_resource_registry"
        $RunDir = Join-Path $RegistryRoot "RUN_$(def_NowStamp)_VIA_MANAGED_RESOURCE_REGISTRY_v0105_FALLBACK"
        $fallback = def_WriteFallbackHtml -RunDir $RunDir -Message $_.Exception.Message
        $latest = def_CopyLatestOutputs -RunDir $RunDir -RegistryRoot $RegistryRoot
        if (-not $NoOpen -and (Test-Path -LiteralPath $latest)) { Start-Process -FilePath $latest | Out-Null }
        Write-Host "Fallback HTML: $fallback" -ForegroundColor Green
    } catch {
        Write-Host "Fallback generation also failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} finally {
    Write-Host ""
    Write-Host "PowerShell remains open. No destructive action was executed." -ForegroundColor Cyan
    if ($KeepPowerShellOpen) {
        Write-Host "Press Enter to return to prompt." -ForegroundColor DarkGray
        try { Read-Host | Out-Null } catch {}
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
