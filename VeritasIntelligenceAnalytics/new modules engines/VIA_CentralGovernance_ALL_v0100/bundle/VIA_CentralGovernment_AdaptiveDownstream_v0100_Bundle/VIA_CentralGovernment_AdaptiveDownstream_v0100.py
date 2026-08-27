#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VIA_CentralGovernment_AdaptiveDownstream_v0100.py

VIA Central Government 的「向下遞迴、自適應、沙盒修復」治理擴充層。

治理定位
--------
1. 只讀取 canonical；所有修復只寫入每次執行專屬 sandbox / overlay。
2. 三輪上限：Round 1 平行安全修復、Round 2 相依序治理、Round 3 重驗與收斂。
3. Gate 不跳級：FILE_DISCOVERED → AST_PASS → CONTRACT_PASS → READ_ONLY_DATA_PASS
   → DATA_QUALITY_PASS → SANDBOX_RUNTIME_PASS → INTEGRATION_PASS → USER_TEST_PASS。
4. 高風險 Hydra、刪除、覆蓋、啟用、安裝、網路操作只提出建議，不自動執行。
5. 不 import 被掃描模組；Python 以 ast/compile 靜態驗證，PowerShell 以 parser 可用性決定。
6. 產出 append-only JSON/CSV/HTML、Hash Ledger、契約 sidecar、相依修復順序與 RYG 矩陣。

本檔完全使用 Python 標準函式庫；psutil 如存在只用於資源預算偵測。
"""

from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════════════
# def PARAMETERS — 所有可調參數集中於頂部
# ══════════════════════════════════════════════════════════════════════════════
import argparse
import ast
import builtins
import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import traceback
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple


def_PARAM_SYSTEM_NAME = "VIA Central Government"
def_PARAM_ENGINE_NAME = "VIA_CentralGovernment_AdaptiveDownstream"
def_PARAM_ENGINE_VERSION = "1.0.0"
def_PARAM_MODULE_KEY = "VCG_ADAPTIVE_DOWNSTREAM"
def_PARAM_REGISTRY_ID = "PENDING_CENTRAL_REGISTRY_ASSIGNMENT"
def_PARAM_DEFAULT_ROOT = Path(r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics")
def_PARAM_DEFAULT_OUTPUT_ROOT = Path.home() / "AppData" / "Local" / "VIA" / "CentralGovernanceRuns"
def_PARAM_MAX_ROUNDS = 3
def_PARAM_DEFAULT_MODE = "STAGE"
def_PARAM_ALLOWED_MODES = ("AUDIT", "STAGE")
def_PARAM_MAX_DEPTH = 24
def_PARAM_MAX_FILE_BYTES = 8 * 1024 * 1024
def_PARAM_MAX_WORKERS = 12
def_PARAM_MIN_WORKERS = 2
def_PARAM_SUBPROCESS_TIMEOUT_SECONDS = 90
def_PARAM_FAILURE_CIRCUIT_BREAKER = 3
def_PARAM_DOWNSTREAM_HORIZON_BY_TIER = {"LIGHT": 1, "STANDARD": 3, "DEEP": 5}
def_PARAM_HTML_PREVIEW_ROWS = 1200
def_PARAM_APPEND_ONLY = True
def_PARAM_CANONICAL_MUTATION = False
def_PARAM_AUTO_ACTIVATION = False
def_PARAM_NETWORK_ALLOWED = False
def_PARAM_IMPORT_TARGETS = False
def_PARAM_RUN_RUNTIME_TESTS = False

def_PARAM_SUPPORTED_EXTENSIONS = {
    ".py", ".pyw", ".ps1", ".psm1", ".psd1", ".js", ".mjs", ".cjs",
    ".ts", ".html", ".htm", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".md", ".txt", ".sql", ".ipynb",
}

def_PARAM_CODE_EXTENSIONS = {
    ".py", ".pyw", ".ps1", ".psm1", ".psd1", ".js", ".mjs", ".cjs", ".ts", ".html", ".htm",
}

def_PARAM_EXCLUDED_DIR_NAMES = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", "env", "dist", "build", ".idea", ".vscode",
    "_via_central_governance_runs", "_via_registry_output", "_via_envmanager_output",
    "_via_cache", "site-packages", "Lib", "Scripts",
}

def_PARAM_EXCLUDED_PATH_TOKENS = {
    "\\.git\\", "/.git/", "\\node_modules\\", "/node_modules/",
    "\\site-packages\\", "/site-packages/", "\\__pycache__\\", "/__pycache__/",
}

def_PARAM_GATE_SEQUENCE = [
    "FILE_DISCOVERED",
    "AST_PASS",
    "CONTRACT_PASS",
    "READ_ONLY_DATA_PASS",
    "DATA_QUALITY_PASS",
    "SANDBOX_RUNTIME_PASS",
    "INTEGRATION_PASS",
    "USER_TEST_PASS",
    "ACTIVATED",
    "POST_ACTIVATION_STABLE",
]

def_PARAM_SCANNING_LANES = [
    "L01_STRUCTURE_AST",
    "L02_CONTRACT_SSOT",
    "L03_DEPENDENCY_ROUTING",
    "L04_HYDRA_IDENTITY",
    "L05_SECURITY_GOVERNANCE",
    "L06_QUALITY_OPTIMIZATION",
]

def_PARAM_ACCELERATORS = [
    "A01_SHORT_PATH_RUNTIME",
    "A02_INCREMENTAL_HASH_SCAN",
    "A03_BOUNDED_READONLY_PARALLELISM",
    "A04_AST_CACHE",
    "A05_SEMANTIC_HASH_DEDUP",
    "A06_DEPENDENCY_DAG",
    "A07_CONTRACT_FINGERPRINT",
    "A08_ADAPTIVE_RISK_DEPTH",
    "A09_RESOURCE_PRESSURE_BUDGET",
    "A10_SANDBOX_COPY_ON_WRITE",
    "A11_EXPECTED_HASH_GUARD",
    "A12_APPEND_ONLY_LEDGER",
    "A13_RESUME_CHECKPOINT",
    "A14_HTML_RYG_MATRIX",
    "A15_FAILURE_CIRCUIT_BREAKER",
]

def_PARAM_SUBSYSTEM_RULES = [
    ("VCG", re.compile(r"(?i)(central.?govern|governance|ssot|registry|runtime.?bridge|envmanager|aegis|celeritas|panorama)")),
    ("VRN", re.compile(r"(?i)(^|[/\\_\-.])vrn([/\\_\-.]|$)|reportnova|pdf|ocr|table.?extract|document")),
    ("VDF", re.compile(r"(?i)(^|[/\\_\-.])vdf([/\\_\-.]|$)|dataforge|fetch|dataset|duckdb|parquet|market.?data")),
    ("VAP", re.compile(r"(?i)(^|[/\\_\-.])vap([/\\_\-.]|$)|autoplot|plot|chart|visual")),
    ("VETF", re.compile(r"(?i)(^|[/\\_\-.])vetf([/\\_\-.]|$)|active.?etf|etf.?holding")),
    ("VMFRS", re.compile(r"(?i)(marketflow|risk.?suite|fomo|fund.?flow|group.?rotation)")),
]

def_PARAM_INTERFACE_ALIAS_MODULES = {
    "env_manager": "VIA_EnvManager",
    "registry": "VIA_RegistryCore_v1",
    "ssot": "VIA_SSOT_Unified",
    "aegis": "VeritasAegisNexus",
    "celeritas": "VeritasCeleritas",
}

def_PARAM_ROLE_RULES = [
    ("TEST", re.compile(r"(?i)(^|[/\\_\-.])(test|tests|pytest|pester)([/\\_\-.]|$)")),
    ("ENTRY", re.compile(r"(?i)(main|entry|launcher|invoke|start|run|orchestrator|centralgovernment)")),
    ("CONFIG", re.compile(r"(?i)(config|setting|manifest|registry|ssot|schema|contract)")),
    ("REPORT", re.compile(r"(?i)(report|dashboard|matrix|html)")),
    ("DATA", re.compile(r"(?i)(data|dataset|csv|parquet|duckdb|sqlite)")),
]

def_PARAM_RISK_WEIGHTS = {"INFO": 0, "LOW": 1, "MEDIUM": 3, "HIGH": 7, "CRITICAL": 12}
def_PARAM_RYG_BY_SEVERITY = {"INFO": "G", "LOW": "G", "MEDIUM": "Y", "HIGH": "R", "CRITICAL": "R"}

def_PARAM_SAFE_FIX_IDS = {
    "ENC_UTF8_BOM",
    "FMT_TRAILING_WHITESPACE",
    "FMT_FINAL_NEWLINE",
    "FMT_MIXED_NEWLINES",
}

def_PARAM_HIGH_RISK_PATH_PATTERNS = [
    re.compile(r"(?i)OneDrive"),
    re.compile(r"(?i)^/mnt/data/"),
    re.compile(r"(?i)C:\\Users\\[^\\]+\\Downloads"),
]

def_PARAM_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    re.compile(r"(?i)Authorization\s*[:=].*Bearer\s+[A-Za-z0-9._\-]{12,}"),
]

def_PARAM_PY_DANGEROUS_CALLS = {
    "eval": "CRITICAL",
    "exec": "CRITICAL",
    "os.system": "CRITICAL",
    "subprocess.Popen": "HIGH",
    "subprocess.run": "MEDIUM",
    "subprocess.call": "HIGH",
    "shutil.rmtree": "CRITICAL",
    "Path.unlink": "HIGH",
    "os.remove": "HIGH",
    "os.unlink": "HIGH",
}

def_PARAM_PS_DANGEROUS_PATTERNS = [
    ("PS_INVOKE_EXPRESSION", "CRITICAL", re.compile(r"(?i)\b(Invoke-Expression|iex)\b")),
    ("PS_REMOVE_ITEM", "HIGH", re.compile(r"(?i)\bRemove-Item\b")),
    ("PS_STOP_PROCESS", "CRITICAL", re.compile(r"(?i)\bStop-Process\b")),
    ("PS_EXIT", "HIGH", re.compile(r"(?im)^\s*exit(?:\s+\d+|\s+\$\w+)?\s*$")),
    ("PS_DOWNLOAD_EXEC", "CRITICAL", re.compile(r"(?is)(Invoke-WebRequest|curl|wget).{0,300}(Invoke-Expression|iex|Start-Process)")),
]

def_PARAM_COPY_SUFFIX_RE = re.compile(r"\s*\((\d+)\)(?=\.[^.]+$|$)")
def_PARAM_VERSION_SUFFIX_RE = re.compile(r"(?i)(?:[_\-.]v(?:er(?:sion)?)?)\d+(?:[._-]\d+)*")
def_PARAM_MODULE_ID_PATTERNS = [
    re.compile(r"\b(?:VCG|VIA|VRN|VDF|VAP|VETF|VMFRS)_(?:MDL|ENG|SYS|MOD|FNC|LIB|REG|CFG|RPT|TPL)\d{3,6}(?:_[A-Z0-9_-]+)?\b"),
    re.compile(r"\bVIS-[A-Z0-9-]+-\d{4,8}\b"),
    re.compile(r"\bSYS_[A-Z0-9]+\.MDL\d+(?:\.[A-Z0-9_-]+)?\b"),
]
def_PARAM_ASSET_ID_RE = re.compile(r"\bAST-(?:PS|PY|JS|HTML|JSON|YAML)-[A-Z]+-[A-Z0-9]+-\d{3}-\d{3}\b")
def_PARAM_ANCHOR_RE = re.compile(r"(?:ANCHOR\[VIA:ANCHOR:([A-Z0-9_-]+)\]|\[VIA:ANCHOR:([A-Z0-9_-]+)\])")

def_PARAM_HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr",
}


# ══════════════════════════════════════════════════════════════════════════════
# def DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class def_EngineConfig:
    root: Path
    output_root: Path
    mode: str = def_PARAM_DEFAULT_MODE
    rounds: int = def_PARAM_MAX_ROUNDS
    max_depth: int = def_PARAM_MAX_DEPTH
    max_workers: int = def_PARAM_MAX_WORKERS
    incremental: bool = True
    open_html: bool = False
    include_extensions: Set[str] = field(default_factory=lambda: set(def_PARAM_SUPPORTED_EXTENSIONS))
    baseline_path: Optional[Path] = None
    enable_runtime_tests: bool = def_PARAM_RUN_RUNTIME_TESTS


@dataclass
class def_AssetRecord:
    asset_id: str
    relative_path: str
    absolute_path: str
    extension: str
    language: str
    subsystem: str
    role: str
    depth: int
    size_bytes: int
    modified_ns: int
    content_hash: str
    semantic_hash: str = ""
    encoding: str = "utf-8"
    newline_style: str = "UNKNOWN"
    cached: bool = False
    gate: str = "FILE_DISCOVERED"
    health: str = "G"
    risk_score: int = 0
    issue_count: int = 0
    contract_hash: str = ""
    exports: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    module_ids: List[str] = field(default_factory=list)
    anchors: List[str] = field(default_factory=list)
    analysis_meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class def_IssueRecord:
    issue_id: str
    asset_id: str
    relative_path: str
    subsystem: str
    lane: str
    category: str
    severity: str
    classification: str
    title: str
    detail: str
    line: int = 0
    symbol: str = ""
    auto_fixable: bool = False
    fix_id: str = ""
    status: str = "OPEN"
    inherited_from: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class def_ContractRecord:
    asset_id: str
    relative_path: str
    language: str
    subsystem: str
    module_name: str
    version: str
    owner: str
    entrypoints: List[str]
    exports: List[Dict[str, Any]]
    dependencies: List[str]
    inputs: List[str]
    outputs: List[str]
    side_effects: List[str]
    supports_setup_execute_teardown: bool
    contract_hash: str
    source: str = "STATIC_INFERENCE"


@dataclass
class def_DependencyEdge:
    source_asset_id: str
    target_asset_id: str
    source_path: str
    target_path: str
    dependency_name: str
    edge_type: str
    status: str


@dataclass
class def_PatchRecord:
    patch_id: str
    asset_id: str
    relative_path: str
    round_no: int
    fix_ids: List[str]
    original_hash: str
    proposed_hash: str
    overlay_path: str
    status: str
    validation: str
    note: str = ""


@dataclass
class def_RoundResult:
    round_no: int
    name: str
    started_at_utc: str
    finished_at_utc: str
    assets: int
    issues_open: int
    issues_resolved: int
    patches_written: int
    gate_counts: Dict[str, int]
    health_counts: Dict[str, int]
    classification_counts: Dict[str, int]
    report_json: str
    report_html: str


# ══════════════════════════════════════════════════════════════════════════════
# def GENERAL UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def def_now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_run_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def def_sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def def_sha256_text(value: str) -> str:
    return def_sha256_bytes(value.encode("utf-8"))


def def_sha256_file(path_value: Path) -> str:
    digest = hashlib.sha256()
    with path_value.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def def_read_bytes_safe(path_value: Path) -> bytes:
    try:
        return path_value.read_bytes()
    except Exception:
        return b""


def def_decode_text(payload: bytes) -> Tuple[str, str]:
    if payload.startswith(b"\xef\xbb\xbf"):
        return payload.decode("utf-8-sig", errors="replace"), "utf-8-sig"
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        return payload.decode("utf-16", errors="replace"), "utf-16"
    for encoding in ("utf-8", "cp950", "big5", "latin-1"):
        try:
            return payload.decode(encoding), encoding
        except Exception:
            continue
    return payload.decode("utf-8", errors="replace"), "utf-8-replace"


def def_detect_newline_style(text_value: str) -> str:
    crlf = text_value.count("\r\n")
    bare_lf = text_value.count("\n") - crlf
    bare_cr = text_value.count("\r") - crlf
    styles = sum(int(value > 0) for value in (crlf, bare_lf, bare_cr))
    if styles > 1:
        return "MIXED"
    if crlf > 0:
        return "CRLF"
    if bare_lf > 0:
        return "LF"
    if bare_cr > 0:
        return "CR"
    return "NONE"


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_append_jsonl(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    with path_value.open("a", encoding="utf-8", newline="\n") as file_obj:
        file_obj.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def def_write_csv(path_value: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path_value.write_text("", encoding="utf-8-sig")
        return
    fieldnames: List[str] = []
    seen: Set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path_value.open("w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: def_flatten_csv_value(row.get(key)) for key in fieldnames})


def def_flatten_csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def def_rel_path(path_value: Path, root: Path) -> str:
    try:
        return path_value.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path_value.name


def def_safe_asset_id(relative_path: str) -> str:
    short = def_sha256_text(relative_path.lower())[:10].upper()
    return f"VCG-ASSET-{short}"


def def_normalize_module_key(path_value: str) -> str:
    stem = Path(path_value).stem
    stem = def_PARAM_COPY_SUFFIX_RE.sub("", stem)
    stem = def_PARAM_VERSION_SUFFIX_RE.sub("", stem)
    stem = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_").lower()
    return stem


def def_extract_module_ids(text_value: str) -> List[str]:
    output: Set[str] = set()
    for pattern in def_PARAM_MODULE_ID_PATTERNS:
        output.update(pattern.findall(text_value))
    return sorted(output)


def def_is_relative_to(path_value: Path, parent: Path) -> bool:
    try:
        path_value.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def def_classification_for_issue(severity: str, category: str, auto_fixable: bool) -> str:
    if category in {"HYDRA", "IDENTITY_COLLISION", "SSOT_AUTHORITY_COLLISION"}:
        return "MULTI_SUBSYSTEM_SYNCHRONIZATION"
    if severity in {"CRITICAL", "HIGH"}:
        return "SEQUENCE_DEPENDENT"
    if auto_fixable:
        return "PARALLEL_FIXABLE"
    if category in {"CONTRACT_DRIFT", "DEPENDENCY_MISSING", "DEPENDENCY_CYCLE", "PATH_BINDING"}:
        return "SEQUENCE_DEPENDENT"
    return "PARALLEL_REVIEWABLE"


def def_resolve_resource_budget(requested_workers: int) -> Dict[str, Any]:
    cpu_count = max(1, os.cpu_count() or 4)
    memory_percent = 0.0
    available_mb = 0
    psutil_available = False
    try:
        import psutil  # type: ignore

        psutil_available = True
        memory_percent = float(psutil.virtual_memory().percent)
        available_mb = int(psutil.virtual_memory().available // (1024 * 1024))
    except Exception:
        pass

    workers = min(def_PARAM_MAX_WORKERS, max(def_PARAM_MIN_WORKERS, requested_workers, cpu_count // 2))
    mode = "NORMAL"
    if memory_percent >= 88 or (available_mb and available_mb < 1024):
        workers = 1
        mode = "PRESSURE_STOP_PARALLEL"
    elif memory_percent >= 78 or (available_mb and available_mb < 2048):
        workers = min(workers, 2)
        mode = "PRESSURE_REDUCED"
    else:
        workers = min(workers, max(2, cpu_count - 1))

    return {
        "psutil_available": psutil_available,
        "cpu_count": cpu_count,
        "memory_percent": memory_percent,
        "available_mb": available_mb,
        "workers": max(1, workers),
        "mode": mode,
    }


# ══════════════════════════════════════════════════════════════════════════════
# def DISCOVERY / DOWNSTREAM SCOPE
# ══════════════════════════════════════════════════════════════════════════════
def def_should_exclude_dir(path_value: Path) -> bool:
    name_lower = path_value.name.lower()
    if path_value.name in def_PARAM_EXCLUDED_DIR_NAMES:
        return True
    if name_lower.startswith("run_") or (name_lower.startswith("_via_") and "run" in name_lower) or name_lower.startswith("_vcg_"):
        return True
    normalized = str(path_value).replace("/", "\\")
    return any(token.replace("/", "\\") in normalized for token in def_PARAM_EXCLUDED_PATH_TOKENS)


def def_infer_subsystem(relative_path: str) -> str:
    for subsystem, pattern in def_PARAM_SUBSYSTEM_RULES:
        if pattern.search(relative_path):
            return subsystem
    return "OTHERS"


def def_infer_role(relative_path: str) -> str:
    for role, pattern in def_PARAM_ROLE_RULES:
        if pattern.search(relative_path):
            return role
    return "MODULE"


def def_language_from_extension(extension: str) -> str:
    extension = extension.lower()
    if extension in {".py", ".pyw"}:
        return "PYTHON"
    if extension in {".ps1", ".psm1", ".psd1"}:
        return "POWERSHELL"
    if extension in {".js", ".mjs", ".cjs", ".ts"}:
        return "JAVASCRIPT"
    if extension in {".html", ".htm"}:
        return "HTML"
    if extension in {".json", ".jsonl", ".ipynb"}:
        return "JSON"
    if extension in {".yaml", ".yml"}:
        return "YAML"
    if extension == ".toml":
        return "TOML"
    if extension == ".sql":
        return "SQL"
    return "TEXT"


def def_walk_files(root: Path, max_depth: int, include_extensions: Set[str]) -> Iterator[Path]:
    root = root.resolve()
    stack: List[Tuple[Path, int]] = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            continue
        try:
            children = list(current.iterdir())
        except Exception:
            continue
        for child in sorted(children, key=lambda item: item.name.lower(), reverse=True):
            if child.is_dir():
                if not def_should_exclude_dir(child):
                    stack.append((child, depth + 1))
                continue
            if not child.is_file():
                continue
            if child.suffix.lower() in include_extensions:
                yield child


def def_discover_assets(config: def_EngineConfig) -> List[def_AssetRecord]:
    rows: List[def_AssetRecord] = []
    for path_value in def_walk_files(config.root, config.max_depth, config.include_extensions):
        if def_is_relative_to(path_value, config.output_root):
            continue
        try:
            stat_value = path_value.stat()
        except Exception:
            continue
        relative = def_rel_path(path_value, config.root)
        depth = max(0, len(Path(relative).parts) - 1)
        content_hash = def_sha256_file(path_value)
        rows.append(
            def_AssetRecord(
                asset_id=def_safe_asset_id(relative),
                relative_path=relative,
                absolute_path=str(path_value),
                extension=path_value.suffix.lower(),
                language=def_language_from_extension(path_value.suffix),
                subsystem=def_infer_subsystem(relative),
                role=def_infer_role(relative),
                depth=depth,
                size_bytes=int(stat_value.st_size),
                modified_ns=int(stat_value.st_mtime_ns),
                content_hash=content_hash,
            )
        )
    rows.sort(key=lambda row: (row.subsystem, row.relative_path.lower()))
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# def BASELINE / INCREMENTAL CACHE
# ══════════════════════════════════════════════════════════════════════════════
def def_baseline_matches_root(path_value: Path, root: Path) -> bool:
    try:
        payload = json.loads(path_value.read_text(encoding="utf-8"))
        baseline_root = payload.get("root") or (payload.get("run_summary", {}) or {}).get("root")
        if not baseline_root:
            return False
        return str(Path(str(baseline_root)).resolve()).casefold() == str(root.resolve()).casefold()
    except Exception:
        return False


def def_find_latest_baseline(
    output_root: Path,
    explicit_path: Optional[Path] = None,
    root: Optional[Path] = None,
) -> Optional[Path]:
    if explicit_path and explicit_path.is_file():
        if root is None or def_baseline_matches_root(explicit_path, root):
            return explicit_path
        return None
    if not output_root.exists():
        return None
    candidates = sorted(output_root.glob("RUN_*/baseline.json"), key=lambda path_value: path_value.stat().st_mtime_ns, reverse=True)
    for candidate in candidates:
        if root is None or def_baseline_matches_root(candidate, root):
            return candidate
    return None


def def_load_baseline(path_value: Optional[Path]) -> Dict[str, Any]:
    if path_value is None or not path_value.is_file():
        return {}
    try:
        payload = json.loads(path_value.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def def_baseline_asset_cache(baseline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    cache = baseline.get("asset_cache", {}) if isinstance(baseline, dict) else {}
    return cache if isinstance(cache, dict) else {}


def def_baseline_failure_counts(baseline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = baseline.get("failure_counts", {}) if isinstance(baseline, dict) else {}
    return rows if isinstance(rows, dict) else {}


# ══════════════════════════════════════════════════════════════════════════════
# def PYTHON STATIC ANALYSIS HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def def_ast_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = def_ast_call_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def def_ast_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Dict[str, Any]:
    positional = [arg.arg for arg in list(node.args.posonlyargs) + list(node.args.args)]
    keyword_only = [arg.arg for arg in node.args.kwonlyargs]
    defaults_count = len(node.args.defaults)
    required_count = max(0, len(positional) - defaults_count)
    return {
        "name": node.name,
        "async": isinstance(node, ast.AsyncFunctionDef),
        "positional": positional,
        "keyword_only": keyword_only,
        "vararg": node.args.vararg.arg if node.args.vararg else "",
        "kwarg": node.args.kwarg.arg if node.args.kwarg else "",
        "required_count": required_count,
        "returns": ast.unparse(node.returns) if node.returns is not None and hasattr(ast, "unparse") else "",
        "line": int(getattr(node, "lineno", 0)),
    }


def def_extract_static_string_assignment(tree: ast.Module, name_value: str) -> str:
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: List[ast.expr] = []
            value_node: Optional[ast.expr] = None
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value_node = node.value
            else:
                targets = [node.target]
                value_node = node.value
            if any(isinstance(target, ast.Name) and target.id == name_value for target in targets):
                if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
                    return value_node.value
    return ""


def def_extract_top_level_defined_lines(tree: ast.Module) -> Dict[str, int]:
    output: Dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            output[node.name] = int(node.lineno)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    output[target.id] = int(node.lineno)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    output[alias.asname or alias.name.split(".")[0]] = int(node.lineno)
            else:
                for alias in node.names:
                    output[alias.asname or alias.name] = int(node.lineno)
    return output


def def_top_level_use_before_definition(tree: ast.Module) -> List[Tuple[str, int, int]]:
    defined_lines = def_extract_top_level_defined_lines(tree)
    builtins_set = set(dir(builtins))
    findings: List[Tuple[str, int, int]] = []

    def def_visit_top_statement(statement: ast.stmt) -> None:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)) and node is not statement:
                continue
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                name_value = node.id
                definition_line = defined_lines.get(name_value)
                use_line = int(getattr(node, "lineno", 0))
                if definition_line and definition_line > use_line and name_value not in builtins_set:
                    findings.append((name_value, use_line, definition_line))

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        def_visit_top_statement(statement)
    return sorted(set(findings), key=lambda row: (row[1], row[0]))


def def_validate_json_loads_rule_corpora(tree: ast.Module) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value_node = node.value
        target_name = ""
        if isinstance(node, ast.Assign) and node.targets and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
        if not isinstance(value_node, ast.Call):
            continue
        call_name = def_ast_call_name(value_node.func)
        if call_name != "json.loads" or not value_node.args:
            continue
        first_arg = value_node.args[0]
        if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
            continue
        try:
            payload = json.loads(first_arg.value)
        except Exception as exc:
            findings.append({"kind": "JSON_LITERAL_INVALID", "target": target_name, "detail": str(exc), "line": int(node.lineno)})
            continue
        if not isinstance(payload, list):
            continue
        for row in payload:
            if not isinstance(row, dict) or not isinstance(row.get("pattern"), str):
                continue
            flags_value = 0
            for flag_name in row.get("flags", []):
                flags_value |= int(getattr(re, str(flag_name), 0))
            rule_name = str(row.get("rule_name") or row.get("rule_id") or "UNKNOWN_RULE")
            try:
                regex_obj = re.compile(row["pattern"], flags_value)
            except Exception as exc:
                findings.append({"kind": "REGEX_COMPILE_ERROR", "target": target_name, "rule": rule_name, "detail": str(exc), "line": int(node.lineno)})
                continue
            for example in row.get("examples_pass", []):
                if regex_obj.search(str(example)) is None:
                    findings.append({
                        "kind": "REGEX_PASS_EXAMPLE_MISSED",
                        "target": target_name,
                        "rule": rule_name,
                        "example": example,
                        "pattern": row["pattern"],
                        "line": int(node.lineno),
                    })
            for example in row.get("examples_fail", []):
                if regex_obj.search(str(example)) is not None:
                    findings.append({
                        "kind": "REGEX_FAIL_EXAMPLE_MATCHED",
                        "target": target_name,
                        "rule": rule_name,
                        "example": example,
                        "pattern": row["pattern"],
                        "line": int(node.lineno),
                    })
    return findings


def def_semantic_hash_python(tree: ast.Module) -> str:
    try:
        return def_sha256_text(ast.dump(tree, annotate_fields=True, include_attributes=False))
    except Exception:
        return ""


def def_iter_module_scope_nodes(tree: ast.Module) -> Iterator[ast.AST]:
    """Yield module-scope nodes, descending through control blocks but never function/class bodies."""
    stack: List[ast.AST] = list(reversed(tree.body))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        child_lists: List[List[ast.AST]] = []
        for field_name in ("body", "orelse", "finalbody"):
            value = getattr(node, field_name, None)
            if isinstance(value, list):
                child_lists.append(value)
        handlers = getattr(node, "handlers", None)
        if isinstance(handlers, list):
            for handler in handlers:
                child_lists.append(getattr(handler, "body", []))
        cases = getattr(node, "cases", None)
        if isinstance(cases, list):
            for case in cases:
                child_lists.append(getattr(case, "body", []))
        for child_list in reversed(child_lists):
            for child in reversed(child_list):
                if isinstance(child, ast.AST):
                    stack.append(child)


def def_extract_interface_refs(tree: ast.Module) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "hasattr" and len(node.args) >= 2:
            object_path = def_ast_call_name(node.args[0])
            attr_node = node.args[1]
            if isinstance(attr_node, ast.Constant) and isinstance(attr_node.value, str):
                key = (object_path, attr_node.value, int(getattr(node, "lineno", 0)))
                if key not in seen:
                    seen.add(key)
                    refs.append({"object_path": object_path, "attribute": attr_node.value, "line": key[2], "kind": "HASATTR"})
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            object_path = def_ast_call_name(node.func.value)
            if object_path.startswith("ctx."):
                key = (object_path, node.func.attr, int(getattr(node, "lineno", 0)))
                if key not in seen:
                    seen.add(key)
                    refs.append({"object_path": object_path, "attribute": node.func.attr, "line": key[2], "kind": "CALL"})
    return sorted(refs, key=lambda row: (row["object_path"], row["attribute"], row["line"]))


def def_semantic_hash_text(text_value: str, language: str) -> str:
    if language == "PYTHON":
        try:
            return def_semantic_hash_python(ast.parse(text_value))
        except Exception:
            pass
    normalized_lines = []
    for line_value in text_value.splitlines():
        stripped = line_value.strip()
        if not stripped:
            continue
        if language in {"TEXT", "JSON", "YAML", "TOML", "SQL"}:
            normalized_lines.append(re.sub(r"\s+", " ", stripped))
        else:
            normalized_lines.append(re.sub(r"\s+", " ", stripped))
    return def_sha256_text("\n".join(normalized_lines))


# ══════════════════════════════════════════════════════════════════════════════
# def FILE ANALYZERS — 六通道的單檔基礎輸出
# ══════════════════════════════════════════════════════════════════════════════
def def_issue(
    asset: def_AssetRecord,
    issue_id: str,
    lane: str,
    category: str,
    severity: str,
    title: str,
    detail: str,
    line: int = 0,
    symbol: str = "",
    auto_fixable: bool = False,
    fix_id: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> def_IssueRecord:
    return def_IssueRecord(
        issue_id=issue_id,
        asset_id=asset.asset_id,
        relative_path=asset.relative_path,
        subsystem=asset.subsystem,
        lane=lane,
        category=category,
        severity=severity,
        classification=def_classification_for_issue(severity, category, auto_fixable),
        title=title,
        detail=detail,
        line=line,
        symbol=symbol,
        auto_fixable=auto_fixable,
        fix_id=fix_id,
        evidence=evidence or {},
    )


def def_analyze_format_quality(asset: def_AssetRecord, payload: bytes, text_value: str) -> List[def_IssueRecord]:
    issues: List[def_IssueRecord] = []
    if payload.startswith(b"\xef\xbb\xbf"):
        issues.append(def_issue(asset, "ENC_UTF8_BOM", "L06_QUALITY_OPTIMIZATION", "FORMAT", "LOW", "UTF-8 BOM", "檔案含 UTF-8 BOM；sandbox 可安全移除。", auto_fixable=True, fix_id="ENC_UTF8_BOM"))
    if any(line.rstrip(" \t") != line for line in text_value.splitlines()):
        issues.append(def_issue(asset, "FMT_TRAILING_WHITESPACE", "L06_QUALITY_OPTIMIZATION", "FORMAT", "LOW", "行尾空白", "偵測到行尾空白；sandbox 可安全清理。", auto_fixable=True, fix_id="FMT_TRAILING_WHITESPACE"))
    newline_style = def_detect_newline_style(text_value)
    asset.newline_style = newline_style
    if newline_style == "MIXED":
        issues.append(def_issue(asset, "FMT_MIXED_NEWLINES", "L06_QUALITY_OPTIMIZATION", "FORMAT", "LOW", "換行格式混用", "同一檔案同時出現 CRLF/LF/CR；sandbox 統一為 LF。", auto_fixable=True, fix_id="FMT_MIXED_NEWLINES"))
    if text_value and not text_value.endswith(("\n", "\r")):
        issues.append(def_issue(asset, "FMT_FINAL_NEWLINE", "L06_QUALITY_OPTIMIZATION", "FORMAT", "LOW", "缺少檔尾換行", "sandbox 可補上單一檔尾換行。", auto_fixable=True, fix_id="FMT_FINAL_NEWLINE"))
    if asset.size_bytes > def_PARAM_MAX_FILE_BYTES:
        issues.append(def_issue(asset, "QUALITY_OVERSIZED_FILE", "L06_QUALITY_OPTIMIZATION", "OPTIMIZATION", "MEDIUM", "大型檔案", f"檔案大小 {asset.size_bytes:,} bytes，建議分段索引或延遲載入。"))
    return issues


def def_detect_hardcoded_paths(asset: def_AssetRecord, text_value: str) -> List[def_IssueRecord]:
    issues: List[def_IssueRecord] = []
    raw_candidates = sorted(set(re.findall(r"(?:[A-Za-z]:\\[^\r\n'\"]+|/mnt/data/[^\r\n'\"]+)", text_value)))
    path_candidates = [
        row for row in raw_candidates
        if not any(token in row for token in ("[", "]", "\\r", "\\n", "(?", "*", "+", "{|"))
    ]
    for path_text in path_candidates[:100]:
        if any(pattern.search(path_text) for pattern in def_PARAM_HIGH_RISK_PATH_PATTERNS):
            severity = "HIGH" if "OneDrive" in path_text else "MEDIUM"
            issues.append(def_issue(
                asset,
                "PATH_HARDCODED_EXTERNAL_ROOT",
                "L02_CONTRACT_SSOT",
                "PATH_BINDING",
                severity,
                "硬編碼外部路徑",
                f"偵測到可能違反 Mother Root／可攜性治理的路徑：{path_text[:300]}",
                evidence={"path": path_text},
            ))
    return issues


def def_detect_secrets(asset: def_AssetRecord, text_value: str) -> List[def_IssueRecord]:
    issues: List[def_IssueRecord] = []
    for pattern in def_PARAM_SECRET_PATTERNS:
        match_value = pattern.search(text_value)
        if match_value:
            issues.append(def_issue(asset, "SEC_HARDCODED_SECRET", "L05_SECURITY_GOVERNANCE", "SECURITY", "CRITICAL", "疑似硬編碼密鑰", "偵測到疑似密碼、Token 或 API Key；不顯示原值。", line=text_value[:match_value.start()].count("\n") + 1))
    return issues


def def_analyze_python(asset: def_AssetRecord, text_value: str) -> Tuple[List[def_IssueRecord], def_ContractRecord, Dict[str, Any]]:
    issues: List[def_IssueRecord] = []
    exports: List[Dict[str, Any]] = []
    imports: List[str] = []
    entrypoints: List[str] = []
    inputs: Set[str] = set()
    outputs: Set[str] = set()
    side_effects: Set[str] = set()
    version = ""
    owner = ""
    meta: Dict[str, Any] = {}
    module_name = Path(asset.relative_path).stem

    try:
        tree = ast.parse(text_value, filename=asset.relative_path)
        compile(tree, asset.relative_path, "exec")
        asset.semantic_hash = def_semantic_hash_python(tree)
        asset.gate = "AST_PASS"
    except SyntaxError as exc:
        issues.append(def_issue(asset, "PY_SYNTAX_ERROR", "L01_STRUCTURE_AST", "SYNTAX", "CRITICAL", "Python 語法錯誤", str(exc), line=int(exc.lineno or 0)))
        contract = def_ContractRecord(
            asset_id=asset.asset_id,
            relative_path=asset.relative_path,
            language=asset.language,
            subsystem=asset.subsystem,
            module_name=module_name,
            version="",
            owner="",
            entrypoints=[],
            exports=[],
            dependencies=[],
            inputs=[],
            outputs=[],
            side_effects=[],
            supports_setup_execute_teardown=False,
            contract_hash=def_sha256_text(asset.relative_path + ":SYNTAX_ERROR"),
        )
        return issues, contract, {"syntax_ok": False, "traceback": traceback.format_exc()}
    except Exception as exc:
        issues.append(def_issue(asset, "PY_AST_ANALYSIS_ERROR", "L01_STRUCTURE_AST", "SYNTAX", "CRITICAL", "Python AST 分析失敗", str(exc)))
        contract = def_ContractRecord(asset.asset_id, asset.relative_path, asset.language, asset.subsystem, module_name, "", "", [], [], [], [], [], [], False, def_sha256_text(asset.relative_path + ":AST_ERROR"))
        return issues, contract, {"syntax_ok": False}

    module_docstring = ast.get_docstring(tree) or ""
    interface_refs = def_extract_interface_refs(tree)
    module_ids = def_extract_module_ids(text_value)
    anchors = [left or right for left, right in def_PARAM_ANCHOR_RE.findall(text_value)]
    asset.module_ids = sorted(set(module_ids))
    asset.anchors = sorted(set(anchors))

    if not module_docstring and asset.role in {"ENTRY", "MODULE"}:
        issues.append(def_issue(asset, "CONTRACT_MODULE_DOCSTRING_MISSING", "L02_CONTRACT_SSOT", "CONTRACT", "LOW", "缺少模組契約說明", "未找到 module docstring；已在 Round 2 sidecar 補足靜態契約。"))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signature = def_ast_signature(node)
            if not node.name.startswith("_"):
                exports.append({"kind": "function", **signature})
                inputs.update(signature["positional"])
                inputs.update(signature["keyword_only"])
                if signature["returns"]:
                    outputs.add(signature["returns"])
            if node.name in {"main", "def_main", "run", "def_run", "execute", "def_execute", "setup", "teardown", "cross_init"}:
                entrypoints.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                methods = [child.name for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_")]
                exports.append({"kind": "class", "name": node.name, "methods": methods, "line": int(node.lineno)})
                if any(method in {"execute", "run", "setup", "teardown"} for method in methods):
                    entrypoints.append(node.name)

    for node in def_iter_module_scope_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                if alias.name.split(".")[0].lower() == module_name.lower():
                    issues.append(def_issue(asset, "PY_SELF_IMPORT", "L03_DEPENDENCY_ROUTING", "HYDRA", "HIGH", "模組自我匯入", f"模組範圍 import {alias.name} 可能造成循環初始化或 Hydra。", line=int(node.lineno), symbol=alias.name))
        elif isinstance(node, ast.ImportFrom):
            dependency = node.module or ""
            if dependency:
                imports.append(dependency)
                if dependency.split(".")[0].lower() == module_name.lower():
                    issues.append(def_issue(asset, "PY_SELF_IMPORT", "L03_DEPENDENCY_ROUTING", "HYDRA", "HIGH", "模組自我匯入", f"模組範圍 from {dependency} import ... 可能造成循環初始化或 Hydra。", line=int(node.lineno), symbol=dependency))

    for name_value, use_line, definition_line in def_top_level_use_before_definition(tree):
        issues.append(def_issue(
            asset,
            "PY_TOPLEVEL_USE_BEFORE_DEF",
            "L01_STRUCTURE_AST",
            "INITIALIZATION_ORDER",
            "HIGH",
            "頂層名稱先使用後定義",
            f"{name_value} 於第 {use_line} 行使用，但定義在第 {definition_line} 行；若例外被吞掉，功能會靜默降級。",
            line=use_line,
            symbol=name_value,
            evidence={"definition_line": definition_line},
        ))

    broad_except_pass_count = 0
    top_level_calls: List[Tuple[str, int]] = []
    dangerous_call_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None or (isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    broad_except_pass_count += 1
        if isinstance(node, ast.Call):
            call_name = def_ast_call_name(node.func)
            severity = def_PARAM_PY_DANGEROUS_CALLS.get(call_name)
            if severity:
                dangerous_call_count += 1
                side_effects.add(call_name)
                issues.append(def_issue(asset, f"PY_CALL_{re.sub(r'[^A-Za-z0-9]+', '_', call_name).upper()}", "L05_SECURITY_GOVERNANCE", "SECURITY", severity, "高風險呼叫", f"偵測到 {call_name}；中央治理不得在 Gate 前自動執行。", line=int(getattr(node, "lineno", 0)), symbol=call_name))

    for node in tree.body:
        candidate_nodes: List[ast.AST] = []
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            candidate_nodes.append(node.value)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value_node = node.value
            if isinstance(value_node, ast.Call):
                candidate_nodes.append(value_node)
        for call_node in candidate_nodes:
            call_name = def_ast_call_name(call_node.func) if isinstance(call_node, ast.Call) else ""
            if call_name and call_name not in {"dataclass", "field", "re.compile", "Path", "json.loads", "logging.getLogger"}:
                top_level_calls.append((call_name, int(getattr(call_node, "lineno", 0))))

    if broad_except_pass_count:
        issues.append(def_issue(asset, "PY_BROAD_EXCEPT_PASS", "L06_QUALITY_OPTIMIZATION", "OBSERVABILITY", "MEDIUM", "廣域例外被靜默吞掉", f"偵測到 {broad_except_pass_count} 個 except Exception/BaseException: pass；會降低自適應診斷可信度。", evidence={"count": broad_except_pass_count}))

    for call_name, line_value in top_level_calls[:30]:
        if any(token in call_name.lower() for token in ("init", "bootstrap", "configure", "start", "run", "scan", "register", "install", "execute")):
            issues.append(def_issue(asset, "PY_IMPORT_TIME_SIDE_EFFECT", "L05_SECURITY_GOVERNANCE", "IMPORT_SIDE_EFFECT", "HIGH", "匯入期可能執行副作用", f"頂層呼叫 {call_name} 可能在 import 時執行；應改為顯式 Gate 後入口。", line=line_value, symbol=call_name))

    for finding in def_validate_json_loads_rule_corpora(tree):
        kind = str(finding.get("kind"))
        severity = "HIGH" if kind in {"REGEX_COMPILE_ERROR", "JSON_LITERAL_INVALID"} else "MEDIUM"
        issues.append(def_issue(
            asset,
            f"SSOT_{kind}",
            "L02_CONTRACT_SSOT",
            "SSOT_RULE_VALIDATION",
            severity,
            "SSOT 規則與範例不一致",
            json.dumps(finding, ensure_ascii=False),
            line=int(finding.get("line", 0)),
            symbol=str(finding.get("rule", finding.get("target", ""))),
            evidence=finding,
        ))

    version = def_extract_static_string_assignment(tree, "__version__") or def_extract_static_string_assignment(tree, "def_PARAM_MODULE_VERSION")
    owner = def_extract_static_string_assignment(tree, "__owner__") or def_extract_static_string_assignment(tree, "def_PARAM_OWNER")

    if not asset.module_ids and asset.subsystem == "VCG":
        issues.append(def_issue(asset, "IDENTITY_MODULE_ID_MISSING", "L04_HYDRA_IDENTITY", "IDENTITY", "MEDIUM", "中央治理資產缺少可辨識 ID", "未在原始碼中找到 VCG/VIA/VRN/VDF/VAP 類模組 ID；Round 2 只產生 proposed sidecar，不自行配號。"))

    supports_contract = False
    export_names = {str(row.get("name", "")) for row in exports}
    all_method_names: Set[str] = set()
    for row in exports:
        if row.get("kind") == "class":
            all_method_names.update(row.get("methods", []))
    combined_names = export_names | all_method_names
    supports_contract = {"setup", "execute", "teardown"}.issubset(combined_names)

    contract_payload = {
        "module_name": module_name,
        "version": version,
        "owner": owner,
        "entrypoints": sorted(set(entrypoints)),
        "exports": exports,
        "dependencies": sorted(set(imports)),
        "inputs": sorted(inputs),
        "outputs": sorted(outputs),
        "side_effects": sorted(side_effects),
        "supports_setup_execute_teardown": supports_contract,
    }
    contract_hash = def_sha256_text(json.dumps(contract_payload, ensure_ascii=False, sort_keys=True, default=str))
    contract = def_ContractRecord(
        asset_id=asset.asset_id,
        relative_path=asset.relative_path,
        language=asset.language,
        subsystem=asset.subsystem,
        module_name=module_name,
        version=version,
        owner=owner,
        entrypoints=sorted(set(entrypoints)),
        exports=exports,
        dependencies=sorted(set(imports)),
        inputs=sorted(inputs),
        outputs=sorted(outputs),
        side_effects=sorted(side_effects),
        supports_setup_execute_teardown=supports_contract,
        contract_hash=contract_hash,
    )
    asset.contract_hash = contract_hash
    asset.exports = sorted(export_names)
    asset.imports = sorted(set(imports))
    meta.update({
        "syntax_ok": True,
        "module_docstring": bool(module_docstring),
        "top_level_calls": top_level_calls,
        "broad_except_pass_count": broad_except_pass_count,
        "dangerous_call_count": dangerous_call_count,
        "interface_refs": interface_refs,
        "function_count": sum(1 for row in exports if row.get("kind") == "function"),
        "class_count": sum(1 for row in exports if row.get("kind") == "class"),
    })
    return issues, contract, meta


def def_analyze_json(asset: def_AssetRecord, text_value: str) -> Tuple[List[def_IssueRecord], def_ContractRecord, Dict[str, Any]]:
    issues: List[def_IssueRecord] = []
    parsed: Any = None
    syntax_ok = True
    if asset.extension == ".jsonl":
        rows = []
        for index, line_value in enumerate(text_value.splitlines(), start=1):
            if not line_value.strip():
                continue
            try:
                rows.append(json.loads(line_value))
            except Exception as exc:
                syntax_ok = False
                issues.append(def_issue(asset, "JSONL_PARSE_ERROR", "L01_STRUCTURE_AST", "SYNTAX", "HIGH", "JSONL 解析錯誤", str(exc), line=index))
        parsed = rows
    else:
        try:
            parsed = json.loads(text_value)
        except Exception as exc:
            syntax_ok = False
            issues.append(def_issue(asset, "JSON_PARSE_ERROR", "L01_STRUCTURE_AST", "SYNTAX", "CRITICAL", "JSON 解析錯誤", str(exc)))
    asset.semantic_hash = def_sha256_text(json.dumps(parsed, ensure_ascii=False, sort_keys=True, default=str)) if syntax_ok else def_semantic_hash_text(text_value, asset.language)
    if syntax_ok:
        asset.gate = "READ_ONLY_DATA_PASS"
    top_keys = sorted(parsed.keys()) if isinstance(parsed, dict) else []
    contract_payload = {"module_name": Path(asset.relative_path).stem, "top_keys": top_keys, "kind": type(parsed).__name__ if syntax_ok else "INVALID"}
    contract_hash = def_sha256_text(json.dumps(contract_payload, ensure_ascii=False, sort_keys=True))
    contract = def_ContractRecord(asset.asset_id, asset.relative_path, asset.language, asset.subsystem, Path(asset.relative_path).stem, "", "", [], [{"kind": "json_keys", "name": key} for key in top_keys], [], [], top_keys, [], False, contract_hash)
    asset.contract_hash = contract_hash
    return issues, contract, {"syntax_ok": syntax_ok, "top_keys": top_keys, "row_count": len(parsed) if isinstance(parsed, list) else 1}


def def_analyze_powershell(asset: def_AssetRecord, text_value: str) -> Tuple[List[def_IssueRecord], def_ContractRecord, Dict[str, Any]]:
    issues: List[def_IssueRecord] = []
    functions = sorted(set(re.findall(r"(?im)^\s*function\s+([A-Za-z_][\w-]*)", text_value)))
    imports = sorted(set(re.findall(r"(?im)^\s*(?:Import-Module|\.\s+)\s*['\"]?([^'\"\s]+)", text_value)))
    parameters = sorted(set(re.findall(r"(?im)^\s*\[Parameter[^\]]*\]\s*(?:\[[^\]]+\]\s*)?\$([A-Za-z_]\w*)|^\s*(?:\[[^\]]+\]\s*)?\$([A-Za-z_]\w*)\s*=", text_value)))
    flattened_params = sorted({left or right for left, right in parameters if left or right})
    for issue_id, severity, pattern in def_PARAM_PS_DANGEROUS_PATTERNS:
        match_value = pattern.search(text_value)
        if match_value:
            issues.append(def_issue(asset, issue_id, "L05_SECURITY_GOVERNANCE", "SECURITY", severity, "PowerShell 高風險指令", f"偵測到 {match_value.group(0)[:120]}；不得於自動治理中直接執行。", line=text_value[:match_value.start()].count("\n") + 1))
    if re.search(r"(?im)^\s*Set-ExecutionPolicy\b", text_value):
        issues.append(def_issue(asset, "PS_EXECUTION_POLICY_MUTATION", "L05_SECURITY_GOVERNANCE", "SECURITY", "HIGH", "修改 PowerShell ExecutionPolicy", "應限制為 Process scope 並由人工入口控制。"))
    if not functions and asset.role == "ENTRY":
        issues.append(def_issue(asset, "PS_ENTRY_NO_FUNCTION_BOUNDARY", "L02_CONTRACT_SSOT", "CONTRACT", "MEDIUM", "入口腳本缺少函式邊界", "建議以 def_Main／完整 function 區塊包裝，降低貼上重複執行風險。"))
    asset.semantic_hash = def_semantic_hash_text(text_value, asset.language)
    asset.exports = functions
    asset.imports = imports
    asset.module_ids = def_extract_module_ids(text_value)
    asset.anchors = sorted({left or right for left, right in def_PARAM_ANCHOR_RE.findall(text_value)})
    contract_payload = {"functions": functions, "imports": imports, "parameters": flattened_params}
    contract_hash = def_sha256_text(json.dumps(contract_payload, ensure_ascii=False, sort_keys=True))
    contract = def_ContractRecord(asset.asset_id, asset.relative_path, asset.language, asset.subsystem, Path(asset.relative_path).stem, "", "", [name for name in functions if name.lower() in {"def_main", "main"}], [{"kind": "function", "name": name} for name in functions], imports, flattened_params, [], [row[0] for row in def_PARAM_PS_DANGEROUS_PATTERNS if row[2].search(text_value)], False, contract_hash)
    asset.contract_hash = contract_hash
    asset.gate = "AST_PASS"
    return issues, contract, {"syntax_ok": None, "function_count": len(functions), "parameters": flattened_params}


class def_ActualHtmlIdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        for key, value in attrs:
            if key.lower() == "id" and value:
                self.ids.append(value)


def def_analyze_html(asset: def_AssetRecord, text_value: str) -> Tuple[List[def_IssueRecord], def_ContractRecord, Dict[str, Any]]:
    issues: List[def_IssueRecord] = []
    parser = def_ActualHtmlIdParser()
    try:
        parser.feed(text_value)
        ids = parser.ids
    except Exception:
        ids = re.findall(r"(?i)\bid\s*=\s*['\"]([^'\"]+)['\"]", re.sub(r"(?is)<script.*?</script>", "", text_value))
    duplicate_ids = sorted([key for key, count in Counter(ids).items() if count > 1])
    if duplicate_ids:
        issues.append(def_issue(asset, "HTML_DUPLICATE_IDS", "L04_HYDRA_IDENTITY", "IDENTITY_COLLISION", "HIGH", "HTML ID 重複", f"重複 IDs：{duplicate_ids[:30]}", evidence={"duplicate_ids": duplicate_ids}))
    functions = sorted(set(re.findall(r"(?m)\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", text_value)))
    onclick_calls = sorted(set(re.findall(r"(?i)onclick\s*=\s*['\"]\s*([A-Za-z_$][\w$]*)", text_value)))
    missing_handlers = sorted(set(onclick_calls) - set(functions))
    if missing_handlers:
        issues.append(def_issue(asset, "HTML_MISSING_EVENT_HANDLERS", "L02_CONTRACT_SSOT", "CONTRACT_DRIFT", "HIGH", "HTML 事件函式缺失", f"onclick 參照但未找到定義：{missing_handlers[:40]}", evidence={"missing_handlers": missing_handlers}))
    if re.search(r"(?i)<script[^>]+src=['\"]https?://", text_value) or re.search(r"(?i)@import\s+url\(['\"]?https?://", text_value):
        issues.append(def_issue(asset, "HTML_EXTERNAL_RUNTIME_DEPENDENCY", "L03_DEPENDENCY_ROUTING", "DEPENDENCY", "MEDIUM", "HTML 依賴外部資源", "離線或受限網路環境可能造成 UI 降級；建議本地字體／腳本 fallback。"))
    asset.semantic_hash = def_semantic_hash_text(text_value, asset.language)
    asset.exports = functions
    asset.imports = sorted(set(re.findall(r"(?i)(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", text_value)))
    asset.anchors = sorted({left or right for left, right in def_PARAM_ANCHOR_RE.findall(text_value)})
    contract_payload = {"ids": sorted(set(ids)), "functions": functions, "onclick": onclick_calls}
    contract_hash = def_sha256_text(json.dumps(contract_payload, ensure_ascii=False, sort_keys=True))
    contract = def_ContractRecord(asset.asset_id, asset.relative_path, asset.language, asset.subsystem, Path(asset.relative_path).stem, "", "", functions[:20], [{"kind": "js_function", "name": name} for name in functions], asset.imports, ids, onclick_calls, ["browser_ui"], False, contract_hash)
    asset.contract_hash = contract_hash
    asset.gate = "CONTRACT_PASS" if not missing_handlers else "AST_PASS"
    return issues, contract, {"id_count": len(ids), "duplicate_ids": duplicate_ids, "function_count": len(functions), "missing_handlers": missing_handlers}


def def_analyze_generic(asset: def_AssetRecord, text_value: str) -> Tuple[List[def_IssueRecord], def_ContractRecord, Dict[str, Any]]:
    issues: List[def_IssueRecord] = []
    asset.semantic_hash = def_semantic_hash_text(text_value, asset.language)
    contract_payload = {"module_name": Path(asset.relative_path).stem, "language": asset.language, "line_count": len(text_value.splitlines())}
    contract_hash = def_sha256_text(json.dumps(contract_payload, ensure_ascii=False, sort_keys=True))
    contract = def_ContractRecord(asset.asset_id, asset.relative_path, asset.language, asset.subsystem, Path(asset.relative_path).stem, "", "", [], [], [], [], [], [], False, contract_hash)
    asset.contract_hash = contract_hash
    asset.gate = "READ_ONLY_DATA_PASS"
    return issues, contract, {"line_count": len(text_value.splitlines())}


def def_analyze_single_asset(asset: def_AssetRecord) -> Tuple[def_AssetRecord, List[def_IssueRecord], def_ContractRecord]:
    path_value = Path(asset.absolute_path)
    payload = def_read_bytes_safe(path_value)
    text_value, encoding = def_decode_text(payload)
    asset.encoding = encoding
    issues = def_analyze_format_quality(asset, payload, text_value)
    issues.extend(def_detect_hardcoded_paths(asset, text_value))
    issues.extend(def_detect_secrets(asset, text_value))

    if asset.language == "PYTHON":
        language_issues, contract, meta = def_analyze_python(asset, text_value)
    elif asset.language == "POWERSHELL":
        language_issues, contract, meta = def_analyze_powershell(asset, text_value)
    elif asset.language == "JSON":
        language_issues, contract, meta = def_analyze_json(asset, text_value)
    elif asset.language == "HTML":
        language_issues, contract, meta = def_analyze_html(asset, text_value)
    else:
        language_issues, contract, meta = def_analyze_generic(asset, text_value)
    issues.extend(language_issues)
    asset.analysis_meta = meta
    asset.issue_count = len(issues)
    asset.risk_score = sum(def_PARAM_RISK_WEIGHTS.get(issue.severity, 0) for issue in issues)
    asset.health = "R" if any(issue.severity in {"CRITICAL", "HIGH"} for issue in issues) else ("Y" if issues else "G")
    if asset.gate == "AST_PASS" and not any(issue.category in {"CONTRACT", "CONTRACT_DRIFT", "PATH_BINDING"} and issue.severity in {"HIGH", "CRITICAL"} for issue in issues):
        asset.gate = "CONTRACT_PASS"
    return asset, issues, contract


# ══════════════════════════════════════════════════════════════════════════════
# def GLOBAL DEPENDENCY / HYDRA / CONTRACT DRIFT
# ══════════════════════════════════════════════════════════════════════════════
def def_local_module_index(assets: Sequence[def_AssetRecord]) -> Dict[str, List[def_AssetRecord]]:
    output: Dict[str, List[def_AssetRecord]] = defaultdict(list)
    seen: Dict[str, Set[str]] = defaultdict(set)
    for asset in assets:
        if asset.language != "PYTHON":
            continue
        for key_value in {Path(asset.relative_path).stem.lower(), def_normalize_module_key(asset.relative_path)}:
            if key_value and asset.asset_id not in seen[key_value]:
                output[key_value].append(asset)
                seen[key_value].add(asset.asset_id)
    return output


def def_build_dependency_edges(assets: Sequence[def_AssetRecord]) -> Tuple[List[def_DependencyEdge], List[def_IssueRecord]]:
    index = def_local_module_index(assets)
    by_id = {asset.asset_id: asset for asset in assets}
    edges: List[def_DependencyEdge] = []
    issues: List[def_IssueRecord] = []
    stdlib_names = set(getattr(sys, "stdlib_module_names", set()))

    for asset in assets:
        own_names = {Path(asset.relative_path).stem.lower(), def_normalize_module_key(asset.relative_path)}
        for dependency in asset.imports:
            root_name = dependency.split(".")[0].lower()
            if root_name in own_names:
                continue
            candidates = index.get(root_name, [])
            candidates = [candidate for candidate in candidates if candidate.asset_id != asset.asset_id]
            if len(candidates) == 1:
                target = candidates[0]
                edges.append(def_DependencyEdge(asset.asset_id, target.asset_id, asset.relative_path, target.relative_path, dependency, "LOCAL_IMPORT", "RESOLVED"))
            elif len(candidates) > 1:
                issues.append(def_issue(asset, "DEP_AMBIGUOUS_LOCAL_MODULE", "L03_DEPENDENCY_ROUTING", "HYDRA", "HIGH", "本地模組解析不唯一", f"依賴 {dependency} 對應 {len(candidates)} 個候選：{[row.relative_path for row in candidates[:10]]}", symbol=dependency))
                for target in candidates:
                    edges.append(def_DependencyEdge(asset.asset_id, target.asset_id, asset.relative_path, target.relative_path, dependency, "LOCAL_IMPORT", "AMBIGUOUS"))
            elif root_name and (root_name.startswith(("via", "vrn", "vdf", "vap", "veritas")) and root_name not in stdlib_names):
                issues.append(def_issue(asset, "DEP_MISSING_LOCAL_MODULE", "L03_DEPENDENCY_ROUTING", "DEPENDENCY_MISSING", "HIGH", "本地依賴缺失", f"找不到本地依賴 {dependency}；不得自動改用同名其他版本。", symbol=dependency))
    return edges, issues


def def_dedupe_issues(issues: Sequence[def_IssueRecord]) -> List[def_IssueRecord]:
    """避免增量快取與全域重算產生同一問題的 Hydra 式重複列。"""
    output: List[def_IssueRecord] = []
    seen: Set[Tuple[Any, ...]] = set()
    for issue in issues:
        key = (
            issue.asset_id, issue.issue_id, issue.line, issue.symbol,
            issue.inherited_from, issue.detail, issue.status,
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(issue)
    return output


def def_apply_adaptive_risk_profiles(
    assets: Sequence[def_AssetRecord],
    issues: Sequence[def_IssueRecord],
    edges: Sequence[def_DependencyEdge],
) -> Dict[str, Dict[str, Any]]:
    """A08：依資產角色、風險與相依扇入／扇出調整向下分析深度。"""
    issue_map: Dict[str, List[def_IssueRecord]] = defaultdict(list)
    fan_in: Counter[str] = Counter()
    fan_out: Counter[str] = Counter()
    for issue in issues:
        if issue.status == "OPEN":
            issue_map[issue.asset_id].append(issue)
    for edge in edges:
        if edge.status == "RESOLVED":
            fan_out[edge.source_asset_id] += 1
            fan_in[edge.target_asset_id] += 1

    profiles: Dict[str, Dict[str, Any]] = {}
    for asset in assets:
        open_issues = issue_map.get(asset.asset_id, [])
        score = sum(def_PARAM_RISK_WEIGHTS.get(issue.severity, 0) for issue in open_issues)
        high_count = sum(issue.severity in {"CRITICAL", "HIGH"} for issue in open_issues)
        connectivity = fan_in[asset.asset_id] + fan_out[asset.asset_id]
        central_role = asset.role in {"ENTRY", "CONFIG"} or asset.subsystem == "VCG"
        if high_count > 0 or score >= 14 or connectivity >= 4 or (central_role and connectivity >= 2):
            tier = "DEEP"
        elif score > 0 or connectivity > 0 or central_role:
            tier = "STANDARD"
        else:
            tier = "LIGHT"
        profile = {
            "tier": tier,
            "downstream_horizon": def_PARAM_DOWNSTREAM_HORIZON_BY_TIER[tier],
            "risk_score": score,
            "high_issue_count": high_count,
            "fan_in": fan_in[asset.asset_id],
            "fan_out": fan_out[asset.asset_id],
            "validation_scope": (
                ["syntax", "contract", "dependency", "security", "hydra", "downstream"]
                if tier == "DEEP" else
                ["syntax", "contract", "dependency", "security"]
                if tier == "STANDARD" else
                ["syntax", "format"]
            ),
        }
        asset.analysis_meta = dict(asset.analysis_meta or {})
        asset.analysis_meta["adaptive_profile"] = profile
        profiles[asset.relative_path] = profile
    return profiles


def def_apply_failure_circuit_breaker(
    assets: Sequence[def_AssetRecord],
    issues: List[def_IssueRecord],
    baseline: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """A15：同一資產連續高風險失敗達門檻後停止自修，改為 fail-closed。"""
    previous_rows = def_baseline_failure_counts(baseline)
    issue_map: Dict[str, List[def_IssueRecord]] = defaultdict(list)
    for issue in issues:
        if issue.status == "OPEN":
            issue_map[issue.asset_id].append(issue)

    states: Dict[str, Dict[str, Any]] = {}
    existing = {(issue.asset_id, issue.issue_id) for issue in issues}
    for asset in assets:
        high_issues = [issue for issue in issue_map.get(asset.asset_id, []) if issue.severity in {"CRITICAL", "HIGH"}]
        previous = previous_rows.get(asset.relative_path, {})
        previous_count = int(previous.get("consecutive_high_runs", 0)) if isinstance(previous, dict) else 0
        consecutive = previous_count + 1 if high_issues else 0
        state = "OPEN" if consecutive >= def_PARAM_FAILURE_CIRCUIT_BREAKER else "CLOSED"
        row = {
            "state": state,
            "consecutive_high_runs": consecutive,
            "threshold": def_PARAM_FAILURE_CIRCUIT_BREAKER,
            "high_issue_count": len(high_issues),
            "action": "HUMAN_REVIEW_ONLY" if state == "OPEN" else "SAFE_OVERLAY_ALLOWED",
        }
        asset.analysis_meta = dict(asset.analysis_meta or {})
        asset.analysis_meta["failure_circuit"] = row
        states[asset.relative_path] = row
        if state == "OPEN" and (asset.asset_id, "FAILURE_CIRCUIT_OPEN") not in existing:
            issues.append(def_issue(
                asset,
                "FAILURE_CIRCUIT_OPEN",
                "L05_SECURITY_GOVERNANCE",
                "STABILITY",
                "HIGH",
                "連續失敗斷路器已開啟",
                f"連續 {consecutive} 次執行存在高風險問題；停止自動修復，僅保留人工審核建議。",
                evidence=row,
            ))
    return states


def def_find_dependency_cycles(assets: Sequence[def_AssetRecord], edges: Sequence[def_DependencyEdge]) -> List[List[str]]:
    graph: Dict[str, List[str]] = defaultdict(list)
    for edge in edges:
        if edge.status == "RESOLVED":
            graph[edge.source_asset_id].append(edge.target_asset_id)
    state: Dict[str, int] = {}
    stack: List[str] = []
    cycles: List[List[str]] = []

    def def_dfs(node_id: str) -> None:
        state[node_id] = 1
        stack.append(node_id)
        for neighbor in graph.get(node_id, []):
            if state.get(neighbor, 0) == 0:
                def_dfs(neighbor)
            elif state.get(neighbor) == 1 and neighbor in stack:
                index_value = stack.index(neighbor)
                cycle = stack[index_value:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)
        stack.pop()
        state[node_id] = 2

    for asset in assets:
        if state.get(asset.asset_id, 0) == 0:
            def_dfs(asset.asset_id)
    return cycles


def def_dependency_topological_order(assets: Sequence[def_AssetRecord], edges: Sequence[def_DependencyEdge]) -> List[str]:
    graph: Dict[str, Set[str]] = defaultdict(set)
    indegree: Dict[str, int] = {asset.asset_id: 0 for asset in assets}
    for edge in edges:
        if edge.status != "RESOLVED":
            continue
        if edge.target_asset_id not in graph[edge.source_asset_id]:
            graph[edge.source_asset_id].add(edge.target_asset_id)
            indegree[edge.target_asset_id] = indegree.get(edge.target_asset_id, 0) + 1
    queue = deque(sorted([node_id for node_id, degree in indegree.items() if degree == 0]))
    output: List[str] = []
    while queue:
        node_id = queue.popleft()
        output.append(node_id)
        for neighbor in sorted(graph.get(node_id, set())):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    for node_id in sorted(indegree):
        if node_id not in output:
            output.append(node_id)
    return output


def def_detect_global_hydra(assets: Sequence[def_AssetRecord], contracts: Sequence[def_ContractRecord]) -> List[def_IssueRecord]:
    issues: List[def_IssueRecord] = []
    by_hash: Dict[str, List[def_AssetRecord]] = defaultdict(list)
    by_semantic: Dict[str, List[def_AssetRecord]] = defaultdict(list)
    by_key: Dict[str, List[def_AssetRecord]] = defaultdict(list)
    by_module_id: Dict[str, List[def_AssetRecord]] = defaultdict(list)
    by_contract_key: Dict[str, List[def_ContractRecord]] = defaultdict(list)

    for asset in assets:
        by_hash[asset.content_hash].append(asset)
        if asset.semantic_hash:
            by_semantic[asset.semantic_hash].append(asset)
        by_key[def_normalize_module_key(asset.relative_path)].append(asset)
        for module_id in asset.module_ids:
            by_module_id[module_id].append(asset)
    for contract in contracts:
        if contract.module_name:
            by_contract_key[def_normalize_module_key(contract.module_name)].append(contract)

    def def_emit(group: Sequence[def_AssetRecord], issue_id: str, severity: str, title: str, category: str, detail_prefix: str) -> None:
        paths = sorted(asset.relative_path for asset in group)
        for asset in group:
            issues.append(def_issue(asset, issue_id, "L04_HYDRA_IDENTITY", category, severity, title, f"{detail_prefix}: {paths}", evidence={"paths": paths}))

    for group in by_hash.values():
        if len(group) > 1:
            severity = "HIGH" if any(asset.subsystem == "VCG" or asset.role == "ENTRY" for asset in group) else "MEDIUM"
            def_emit(group, "HYDRA_EXACT_DUPLICATE", severity, "完全相同檔案", "HYDRA", "相同 SHA-256")

    for group in by_semantic.values():
        unique_hashes = {asset.content_hash for asset in group}
        if len(group) > 1 and len(unique_hashes) > 1:
            severity = "HIGH" if any(asset.subsystem == "VCG" for asset in group) else "MEDIUM"
            def_emit(group, "HYDRA_SEMANTIC_DUPLICATE", severity, "語義等價多版本", "HYDRA", "AST/語義 Hash 相同但內容 Hash 不同")

    for key_value, group in by_key.items():
        if key_value and len(group) > 1:
            if any(def_PARAM_COPY_SUFFIX_RE.search(Path(asset.relative_path).name) for asset in group) or len({asset.content_hash for asset in group}) > 1:
                severity = "CRITICAL" if any(asset.subsystem == "VCG" and asset.role == "ENTRY" for asset in group) else "HIGH"
                def_emit(group, "HYDRA_NORMALIZED_NAME_COLLISION", severity, "正規化模組名稱碰撞", "IDENTITY_COLLISION", f"normalized_key={key_value}")

    for module_id, group in by_module_id.items():
        if len(group) > 1:
            def_emit(group, "HYDRA_MODULE_ID_COLLISION", "CRITICAL", "模組 ID 重複", "SSOT_AUTHORITY_COLLISION", f"module_id={module_id}")

    for key_value, group in by_contract_key.items():
        hashes = {contract.contract_hash for contract in group}
        if key_value and len(group) > 1 and len(hashes) > 1:
            asset_by_path = {asset.relative_path: asset for asset in assets}
            asset_group = [asset_by_path[contract.relative_path] for contract in group if contract.relative_path in asset_by_path]
            if asset_group:
                def_emit(asset_group, "HYDRA_CONTRACT_DIVERGENCE", "HIGH", "同名模組契約分歧", "HYDRA", f"contract_key={key_value}")
    return issues


def def_detect_interface_contract_mismatch(assets: Sequence[def_AssetRecord], contracts: Sequence[def_ContractRecord]) -> Tuple[List[def_IssueRecord], List[Dict[str, Any]]]:
    issues: List[def_IssueRecord] = []
    matrix: List[Dict[str, Any]] = []
    contract_by_name = {contract.module_name.lower(): contract for contract in contracts}
    for asset in assets:
        refs = asset.analysis_meta.get("interface_refs", []) if isinstance(asset.analysis_meta, dict) else []
        for ref in refs:
            object_path = str(ref.get("object_path", ""))
            parts = object_path.split(".")
            alias = parts[-1] if parts else ""
            module_name = def_PARAM_INTERFACE_ALIAS_MODULES.get(alias)
            if not module_name:
                continue
            target_contract = contract_by_name.get(module_name.lower())
            attribute = str(ref.get("attribute", ""))
            exported_names: Set[str] = set()
            if target_contract:
                for row in target_contract.exports:
                    if isinstance(row, dict) and row.get("name"):
                        exported_names.add(str(row["name"]))
                    if isinstance(row, dict):
                        exported_names.update(str(value) for value in row.get("methods", []) if value)
            status = "PASS" if target_contract and attribute in exported_names else ("TARGET_MISSING" if target_contract is None else "ATTRIBUTE_MISSING")
            matrix.append({
                "source_asset_id": asset.asset_id,
                "source_path": asset.relative_path,
                "line": int(ref.get("line", 0)),
                "object_path": object_path,
                "target_module": module_name,
                "attribute": attribute,
                "reference_kind": ref.get("kind", ""),
                "status": status,
            })
            if status != "PASS":
                severity = "HIGH" if ref.get("kind") == "CALL" else "MEDIUM"
                issues.append(def_issue(asset, "INTERFACE_CONTRACT_MISMATCH", "L02_CONTRACT_SSOT", "CONTRACT_DRIFT", severity, "跨模組介面契約不相容", f"{object_path}.{attribute} → {module_name}: {status}", line=int(ref.get("line", 0)), symbol=attribute, evidence=matrix[-1]))
    return issues, matrix


def def_detect_contract_drift(assets: Sequence[def_AssetRecord], contracts: Sequence[def_ContractRecord], baseline: Dict[str, Any]) -> List[def_IssueRecord]:
    issues: List[def_IssueRecord] = []
    baseline_contracts = baseline.get("contracts", {}) if isinstance(baseline, dict) else {}
    if not isinstance(baseline_contracts, dict):
        return issues
    asset_by_path = {asset.relative_path: asset for asset in assets}
    for contract in contracts:
        previous = baseline_contracts.get(contract.relative_path)
        if not isinstance(previous, dict):
            continue
        previous_hash = str(previous.get("contract_hash", ""))
        if previous_hash and previous_hash != contract.contract_hash:
            asset = asset_by_path[contract.relative_path]
            previous_exports = {str(row.get("name")) for row in previous.get("exports", []) if isinstance(row, dict)}
            current_exports = {str(row.get("name")) for row in contract.exports if isinstance(row, dict)}
            removed = sorted(previous_exports - current_exports)
            added = sorted(current_exports - previous_exports)
            severity = "HIGH" if removed else "MEDIUM"
            issues.append(def_issue(asset, "CONTRACT_DRIFT", "L02_CONTRACT_SSOT", "CONTRACT_DRIFT", severity, "介面契約漂移", f"契約 Hash 已改變；removed={removed}, added={added}", evidence={"previous_hash": previous_hash, "current_hash": contract.contract_hash, "removed": removed, "added": added}))
    return issues


def def_propagate_downstream_holds(assets: Sequence[def_AssetRecord], edges: Sequence[def_DependencyEdge], issues: List[def_IssueRecord]) -> List[def_IssueRecord]:
    asset_by_id = {asset.asset_id: asset for asset in assets}
    reverse_graph: Dict[str, Set[str]] = defaultdict(set)
    for edge in edges:
        if edge.status == "RESOLVED":
            reverse_graph[edge.target_asset_id].add(edge.source_asset_id)
    high_risk_sources = {issue.asset_id for issue in issues if issue.severity in {"CRITICAL", "HIGH"} and issue.category in {"HYDRA", "IDENTITY_COLLISION", "SSOT_AUTHORITY_COLLISION", "DEPENDENCY_MISSING", "CONTRACT_DRIFT", "SYNTAX"}}
    existing_pairs = {(issue.asset_id, issue.inherited_from) for issue in issues if issue.inherited_from}
    inherited: List[def_IssueRecord] = []
    for source_id in high_risk_sources:
        source_asset = asset_by_id.get(source_id)
        profile = (source_asset.analysis_meta or {}).get("adaptive_profile", {}) if source_asset else {}
        max_horizon = int(profile.get("downstream_horizon", 5))
        queue = deque([(source_id, 0)])
        visited = {source_id}
        while queue:
            node_id, depth = queue.popleft()
            if depth >= max_horizon:
                continue
            for dependent_id in reverse_graph.get(node_id, set()):
                if dependent_id in visited:
                    continue
                visited.add(dependent_id)
                queue.append((dependent_id, depth + 1))
                if (dependent_id, source_id) in existing_pairs:
                    continue
                asset = asset_by_id.get(dependent_id)
                source_asset = asset_by_id.get(source_id)
                if asset and source_asset:
                    inherited.append(def_IssueRecord(
                        issue_id="DOWNSTREAM_INHERITED_HOLD",
                        asset_id=asset.asset_id,
                        relative_path=asset.relative_path,
                        subsystem=asset.subsystem,
                        lane="L03_DEPENDENCY_ROUTING",
                        category="DOWNSTREAM_RISK",
                        severity="MEDIUM",
                        classification="SEQUENCE_DEPENDENT",
                        title="下游繼承 HOLD",
                        detail=f"上游 {source_asset.relative_path} 存在高風險問題，依賴鏈未通過前不可晉級。",
                        inherited_from=source_id,
                        evidence={"upstream_path": source_asset.relative_path, "distance": depth + 1},
                    ))
    return inherited


# ══════════════════════════════════════════════════════════════════════════════
# def SAFE SANDBOX FIXES / ROUND 2 SIDECARS
# ══════════════════════════════════════════════════════════════════════════════
def def_apply_safe_text_fixes(payload: bytes, text_value: str, fix_ids: Sequence[str]) -> bytes:
    output = text_value
    _, source_encoding = def_decode_text(payload)
    if "FMT_MIXED_NEWLINES" in fix_ids:
        output = output.replace("\r\n", "\n").replace("\r", "\n")
    if "FMT_TRAILING_WHITESPACE" in fix_ids:
        output = re.sub(r"[ \t]+(?=\r\n|\n|\r|$)", "", output)
    if "FMT_FINAL_NEWLINE" in fix_ids and output and not output.endswith(("\n", "\r")):
        style = def_detect_newline_style(output)
        output += "\r\n" if style == "CRLF" else ("\r" if style == "CR" else "\n")
    if "ENC_UTF8_BOM" in fix_ids:
        return output.encode("utf-8")
    target_encoding = source_encoding
    if target_encoding in {"utf-8-replace", "utf-8-sig"} and not payload.startswith(b"\xef\xbb\xbf"):
        target_encoding = "utf-8"
    try:
        return output.encode(target_encoding)
    except Exception:
        return output.encode("utf-8")


def def_stage_round1_safe_fixes(
    run_dir: Path,
    assets: Sequence[def_AssetRecord],
    issues: List[def_IssueRecord],
    mode: str,
) -> List[def_PatchRecord]:
    if mode != "STAGE":
        return []
    issues_by_asset: Dict[str, List[def_IssueRecord]] = defaultdict(list)
    for issue in issues:
        if issue.auto_fixable and issue.fix_id in def_PARAM_SAFE_FIX_IDS and issue.status == "OPEN":
            issues_by_asset[issue.asset_id].append(issue)
    asset_by_id = {asset.asset_id: asset for asset in assets}
    patches: List[def_PatchRecord] = []
    overlay_root = run_dir / "overlay" / "round_1"
    for asset_id, asset_issues in issues_by_asset.items():
        asset = asset_by_id[asset_id]
        circuit = (asset.analysis_meta or {}).get("failure_circuit", {})
        if circuit.get("state") == "OPEN":
            for issue in asset_issues:
                issue.evidence = {**(issue.evidence or {}), "auto_fix_blocked": "FAILURE_CIRCUIT_OPEN"}
            continue
        source_path = Path(asset.absolute_path)
        payload = def_read_bytes_safe(source_path)
        text_value, _ = def_decode_text(payload)
        fix_ids = sorted({issue.fix_id for issue in asset_issues})
        proposed = def_apply_safe_text_fixes(payload, text_value, fix_ids)
        original_hash = def_sha256_bytes(payload)
        proposed_hash = def_sha256_bytes(proposed)
        if proposed_hash == original_hash:
            continue
        overlay_path = overlay_root / asset.relative_path
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        overlay_path.write_bytes(proposed)
        validation = def_validate_overlay_file(overlay_path, asset.language)
        patch = def_PatchRecord(
            patch_id=f"PATCH-R1-{def_sha256_text(asset.relative_path + proposed_hash)[:12].upper()}",
            asset_id=asset.asset_id,
            relative_path=asset.relative_path,
            round_no=1,
            fix_ids=fix_ids,
            original_hash=original_hash,
            proposed_hash=proposed_hash,
            overlay_path=str(overlay_path),
            status="STAGED" if validation.startswith("PASS") else "HOLD",
            validation=validation,
            note="Canonical unchanged; copy-on-write sandbox overlay only.",
        )
        patches.append(patch)
        if patch.status == "STAGED":
            for issue in asset_issues:
                issue.status = "RESOLVED_IN_OVERLAY"
    return patches


def def_validate_overlay_file(path_value: Path, language: str) -> str:
    try:
        if language == "PYTHON":
            text_value = path_value.read_text(encoding="utf-8")
            tree = ast.parse(text_value, filename=str(path_value))
            compile(tree, str(path_value), "exec")
            return "PASS_PY_COMPILE"
        if language == "JSON":
            text_value = path_value.read_text(encoding="utf-8")
            if path_value.suffix.lower() == ".jsonl":
                for line_value in text_value.splitlines():
                    if line_value.strip():
                        json.loads(line_value)
            else:
                json.loads(text_value)
            return "PASS_JSON_PARSE"
        return "PASS_TEXT_ROUNDTRIP"
    except Exception as exc:
        return f"FAIL:{exc}"


def def_generate_contract_sidecars(run_dir: Path, contracts: Sequence[def_ContractRecord], issues: Sequence[def_IssueRecord]) -> List[str]:
    sidecar_root = run_dir / "overlay" / "round_2" / "contracts"
    issue_map: Dict[str, List[def_IssueRecord]] = defaultdict(list)
    for issue in issues:
        issue_map[issue.asset_id].append(issue)
    paths: List[str] = []
    for contract in contracts:
        sidecar_path = sidecar_root / f"{contract.relative_path}.governance.json"
        sidecar_payload = {
            "schema": "VIA_CONTRACT_ENVELOPE/1.0",
            "authority": def_PARAM_SYSTEM_NAME,
            "registry_id": def_PARAM_REGISTRY_ID,
            "module_key": def_PARAM_MODULE_KEY,
            "source_asset_id": contract.asset_id,
            "source_relative_path": contract.relative_path,
            "source_contract_hash": contract.contract_hash,
            "import_mode": "REGISTER_ONLY_NO_IMPORT",
            "activation": "PROHIBITED_AUTOMATICALLY",
            "canonical_mutation": False,
            "contract": asdict(contract),
            "universal_interface_envelope": {
                "accepted_input_forms": ["POSITIONAL", "KEYWORD", "DICT_PAYLOAD", "JSON_SERIALIZABLE_CONTEXT"],
                "output_forms": ["DICT", "LIST", "SCALAR", "JSON_SERIALIZABLE_RESULT"],
                "context_fields": ["ssot", "registry", "env_manager", "aegis", "celeritas", "state", "errors"],
                "unknown_field_policy": "PRESERVE_IN_EXTENSIONS",
                "missing_optional_policy": "DEFAULT_OR_DEGRADED",
                "missing_required_policy": "FAIL_CLOSED",
                "schema_evolution": "BACKWARD_COMPATIBLE_ADAPTER_REQUIRED",
            },
            "governance": {
                "highest_severity": def_highest_severity(issue_map.get(contract.asset_id, [])),
                "issue_ids": sorted({issue.issue_id for issue in issue_map.get(contract.asset_id, [])}),
                "hydra_risk": any(issue.category in {"HYDRA", "IDENTITY_COLLISION", "SSOT_AUTHORITY_COLLISION"} for issue in issue_map.get(contract.asset_id, [])),
                "manual_activation_gate": "REQUIRED",
                "test_gate": "STATIC_AND_SANDBOX_REQUIRED",
            },
        }
        def_write_json(sidecar_path, sidecar_payload)
        paths.append(str(sidecar_path))
    return paths


def def_generate_resolution_plans(run_dir: Path, assets: Sequence[def_AssetRecord], edges: Sequence[def_DependencyEdge], issues: Sequence[def_IssueRecord], order: Sequence[str]) -> Dict[str, str]:
    asset_by_id = {asset.asset_id: asset for asset in assets}
    issue_rows = [asdict(issue) for issue in issues if issue.classification in {"SEQUENCE_DEPENDENT", "MULTI_SUBSYSTEM_SYNCHRONIZATION"}]
    fix_order_rows = []
    for index, asset_id in enumerate(order, start=1):
        asset = asset_by_id.get(asset_id)
        if not asset:
            continue
        related = [issue for issue in issues if issue.asset_id == asset_id and issue.status == "OPEN"]
        if not related:
            continue
        fix_order_rows.append({
            "order": index,
            "asset_id": asset.asset_id,
            "relative_path": asset.relative_path,
            "subsystem": asset.subsystem,
            "highest_severity": def_highest_severity(related),
            "issue_ids": sorted({issue.issue_id for issue in related}),
            "automatic_action": "NONE_HIGH_RISK_SUGGESTION_ONLY" if any(issue.severity in {"HIGH", "CRITICAL"} for issue in related) else "SIDE_CAR_ONLY",
        })
    dependency_plan = {
        "generated_at_utc": def_now_utc_iso(),
        "policy": "dependency_ordered / no canonical mutation / no import / no activation",
        "edges": [asdict(edge) for edge in edges],
        "fix_order": fix_order_rows,
    }
    issue_plan = {
        "generated_at_utc": def_now_utc_iso(),
        "policy": "high-risk suggestion only; parallel-safe fixes already staged in sandbox",
        "issues": issue_rows,
    }
    path_binding = {
        "generated_at_utc": def_now_utc_iso(),
        "policy": "parameterize paths through Central Governance context; do not rewrite source automatically",
        "bindings": [
            {
                "asset_id": issue.asset_id,
                "relative_path": issue.relative_path,
                "detected_path": issue.evidence.get("path", ""),
                "recommended_binding": "ctx.paths.resolve(relative_or_registered_asset_id)",
            }
            for issue in issues if issue.category == "PATH_BINDING"
        ],
    }
    dependency_path = run_dir / "overlay" / "round_2" / "dependency_resolution_plan.json"
    issue_path = run_dir / "overlay" / "round_2" / "sequential_fix_plan.json"
    path_binding_path = run_dir / "overlay" / "round_2" / "path_binding_overlay.json"
    def_write_json(dependency_path, dependency_plan)
    def_write_json(issue_path, issue_plan)
    def_write_json(path_binding_path, path_binding)
    return {"dependency_plan": str(dependency_path), "sequential_fix_plan": str(issue_path), "path_binding_overlay": str(path_binding_path)}


# ══════════════════════════════════════════════════════════════════════════════
# def SANDBOX VERIFICATION / GATES
# ══════════════════════════════════════════════════════════════════════════════
def def_detect_powershell_parser() -> str:
    for command_name in ("pwsh", "powershell"):
        resolved = shutil.which(command_name)
        if resolved:
            return resolved
    return ""


def def_verify_assets(assets: Sequence[def_AssetRecord], patches: Sequence[def_PatchRecord]) -> List[Dict[str, Any]]:
    patch_by_path = {patch.relative_path: Path(patch.overlay_path) for patch in patches if patch.status == "STAGED"}
    powershell = def_detect_powershell_parser()
    rows: List[Dict[str, Any]] = []
    for asset in assets:
        path_value = patch_by_path.get(asset.relative_path, Path(asset.absolute_path))
        result = {"asset_id": asset.asset_id, "relative_path": asset.relative_path, "language": asset.language, "path_used": str(path_value), "status": "SKIP", "detail": ""}
        try:
            if asset.language == "PYTHON":
                source = path_value.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source, filename=str(path_value))
                compile(tree, str(path_value), "exec")
                result.update(status="PASS", detail="ast.parse + compile; no import")
            elif asset.language == "JSON":
                source = path_value.read_text(encoding="utf-8", errors="replace")
                if path_value.suffix.lower() == ".jsonl":
                    for line_value in source.splitlines():
                        if line_value.strip():
                            json.loads(line_value)
                else:
                    json.loads(source)
                result.update(status="PASS", detail="JSON parse")
            elif asset.language == "POWERSHELL" and powershell:
                command = [powershell, "-NoProfile", "-NonInteractive", "-Command", f"$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('{str(path_value).replace("'", "''")}',[ref]$t,[ref]$e)|Out-Null;if($e.Count -gt 0){{$e|ForEach-Object{{$_.Message}};throw 'AST_FAIL'}}"]
                completed = subprocess.run(command, capture_output=True, text=True, timeout=def_PARAM_SUBPROCESS_TIMEOUT_SECONDS)
                if completed.returncode == 0:
                    result.update(status="PASS", detail="PowerShell Parser AST")
                else:
                    result.update(status="FAIL", detail=(completed.stderr or completed.stdout)[:1000])
            elif asset.language == "POWERSHELL":
                result.update(status="SKIP", detail="pwsh/powershell unavailable; static regex only")
            elif asset.language == "JAVASCRIPT" and path_value.suffix.lower() in {".js", ".mjs", ".cjs"} and shutil.which("node"):
                completed = subprocess.run([shutil.which("node") or "node", "--check", str(path_value)], capture_output=True, text=True, timeout=def_PARAM_SUBPROCESS_TIMEOUT_SECONDS)
                result.update(status="PASS" if completed.returncode == 0 else "FAIL", detail=(completed.stderr or completed.stdout or "node --check")[:1000])
            else:
                result.update(status="PASS", detail="read-only text roundtrip")
        except Exception as exc:
            result.update(status="FAIL", detail=str(exc))
        rows.append(result)
    return rows


def def_assign_asset_gates(assets: Sequence[def_AssetRecord], issues: Sequence[def_IssueRecord], verification: Sequence[Dict[str, Any]]) -> None:
    issue_map: Dict[str, List[def_IssueRecord]] = defaultdict(list)
    verify_map = {row["asset_id"]: row for row in verification}
    for issue in issues:
        if issue.status == "OPEN":
            issue_map[issue.asset_id].append(issue)
    for asset in assets:
        open_issues = issue_map.get(asset.asset_id, [])
        verification_row = verify_map.get(asset.asset_id, {})
        if any(issue.category == "SYNTAX" and issue.severity in {"CRITICAL", "HIGH"} for issue in open_issues):
            asset.gate = "FILE_DISCOVERED"
        elif any(issue.category in {"CONTRACT", "CONTRACT_DRIFT", "PATH_BINDING"} and issue.severity in {"CRITICAL", "HIGH"} for issue in open_issues):
            asset.gate = "AST_PASS"
        elif any(issue.category in {"HYDRA", "IDENTITY_COLLISION", "SSOT_AUTHORITY_COLLISION", "DEPENDENCY_MISSING", "DEPENDENCY_CYCLE"} and issue.severity in {"CRITICAL", "HIGH"} for issue in open_issues):
            asset.gate = "CONTRACT_PASS"
        elif verification_row.get("status") == "FAIL":
            asset.gate = "DATA_QUALITY_PASS"
        elif verification_row.get("status") == "PASS":
            asset.gate = "SANDBOX_RUNTIME_PASS"
        elif asset.gate in {"FILE_DISCOVERED", "AST_PASS"}:
            asset.gate = "CONTRACT_PASS"
        asset.issue_count = len(open_issues)
        asset.risk_score = sum(def_PARAM_RISK_WEIGHTS.get(issue.severity, 0) for issue in open_issues)
        asset.health = "R" if any(issue.severity in {"CRITICAL", "HIGH"} for issue in open_issues) else ("Y" if open_issues else "G")


# ══════════════════════════════════════════════════════════════════════════════
# def REPORTING / HTML RYG MATRIX
# ══════════════════════════════════════════════════════════════════════════════
def def_highest_severity(issues: Sequence[def_IssueRecord]) -> str:
    order = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return max((issue.severity for issue in issues), key=lambda value: order.get(value, -1), default="INFO")


def def_count_by(rows: Iterable[Any], attribute: str) -> Dict[str, int]:
    output: Dict[str, int] = defaultdict(int)
    for row in rows:
        value = getattr(row, attribute, "UNKNOWN")
        output[str(value)] += 1
    return dict(sorted(output.items()))


def def_build_round_payload(
    round_no: int,
    round_name: str,
    started_at: str,
    assets: Sequence[def_AssetRecord],
    issues: Sequence[def_IssueRecord],
    contracts: Sequence[def_ContractRecord],
    edges: Sequence[def_DependencyEdge],
    patches: Sequence[def_PatchRecord],
    verification: Sequence[Dict[str, Any]],
    resource_budget: Dict[str, Any],
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    open_issues = [issue for issue in issues if issue.status == "OPEN"]
    resolved_issues = [issue for issue in issues if issue.status != "OPEN"]
    return {
        "system": def_PARAM_SYSTEM_NAME,
        "engine": def_PARAM_ENGINE_NAME,
        "version": def_PARAM_ENGINE_VERSION,
        "registry_id": def_PARAM_REGISTRY_ID,
        "round_no": round_no,
        "round_name": round_name,
        "started_at_utc": started_at,
        "finished_at_utc": def_now_utc_iso(),
        "policy": {
            "append_only": True,
            "canonical_mutation": False,
            "target_import": False,
            "network": False,
            "automatic_activation": False,
            "high_risk_auto_repair": False,
            "max_rounds": 3,
        },
        "accelerators": def_PARAM_ACCELERATORS,
        "lanes": def_PARAM_SCANNING_LANES,
        "resource_budget": resource_budget,
        "summary": {
            "assets": len(assets),
            "contracts": len(contracts),
            "dependency_edges": len(edges),
            "issues_open": len(open_issues),
            "issues_resolved_in_overlay": len(resolved_issues),
            "patches": len(patches),
            "gate_counts": def_count_by(assets, "gate"),
            "health_counts": def_count_by(assets, "health"),
            "severity_counts": def_count_by(open_issues, "severity"),
            "classification_counts": def_count_by(open_issues, "classification"),
            "subsystem_counts": def_count_by(assets, "subsystem"),
            "adaptive_deep_assets": sum(1 for asset in assets if (asset.analysis_meta or {}).get("adaptive_profile", {}).get("tier") == "DEEP"),
            "failure_circuit_open": sum(1 for asset in assets if (asset.analysis_meta or {}).get("failure_circuit", {}).get("state") == "OPEN"),
        },
        "assets": [asdict(asset) for asset in assets],
        "issues": [asdict(issue) for issue in issues],
        "contracts": [asdict(contract) for contract in contracts],
        "dependencies": [asdict(edge) for edge in edges],
        "patches": [asdict(patch) for patch in patches],
        "verification": list(verification),
        "extra": extra or {},
    }


def def_html_badge(text_value: str, kind: str) -> str:
    return f'<span class="badge {html.escape(kind)}">{html.escape(text_value)}</span>'


def def_html_table(headers: Sequence[str], rows: Sequence[Sequence[Any]], limit: int = def_PARAM_HTML_PREVIEW_ROWS) -> str:
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    body_rows = []
    for row in list(rows)[:limit]:
        body_rows.append("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>")
    if not body_rows:
        body_rows.append(f'<tr><td colspan="{len(headers)}" class="empty">No rows</td></tr>')
    return f"<div class='table-wrap'><table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>"


def def_render_round_html(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    assets = payload["assets"]
    issues = payload["issues"]
    dependencies = payload["dependencies"]
    patches = payload["patches"]
    verification = payload["verification"]
    open_issues = [row for row in issues if row.get("status") == "OPEN"]
    hydra_rows = [row for row in open_issues if row.get("category") in {"HYDRA", "IDENTITY_COLLISION", "SSOT_AUTHORITY_COLLISION"}]
    optimization_rows = [row for row in open_issues if row.get("category") in {"FORMAT", "OPTIMIZATION", "OBSERVABILITY", "PATH_BINDING"}]
    fix_order = sorted(open_issues, key=lambda row: (-def_PARAM_RISK_WEIGHTS.get(str(row.get("severity")), 0), str(row.get("relative_path"))))
    extra = payload.get("extra", {}) if isinstance(payload.get("extra"), dict) else {}
    interface_rows = extra.get("interface_matrix", []) if isinstance(extra.get("interface_matrix", []), list) else []
    cycle_rows = extra.get("cycles", []) if isinstance(extra.get("cycles", []), list) else []
    subsystem_health: Dict[str, Dict[str, int]] = defaultdict(lambda: {"G": 0, "Y": 0, "R": 0})
    for asset in assets:
        subsystem_health[str(asset.get("subsystem", "OTHERS"))][str(asset.get("health", "Y"))] += 1

    cards = [
        ("Assets", summary["assets"]),
        ("Open Issues", summary["issues_open"]),
        ("Resolved In Overlay", summary["issues_resolved_in_overlay"]),
        ("Patches", summary["patches"]),
        ("Dependency Edges", summary["dependency_edges"]),
        ("Hydra", len(hydra_rows)),
    ]
    card_html = "".join(f"<div class='card'><div class='value'>{value}</div><div class='label'>{html.escape(label)}</div></div>" for label, value in cards)

    error_table = def_html_table(
        ["RYG", "Severity", "Subsystem", "Lane", "Class", "Issue", "File", "Line", "Detail"],
        [[def_PARAM_RYG_BY_SEVERITY.get(row.get("severity", "MEDIUM"), "Y"), row.get("severity"), row.get("subsystem"), row.get("lane"), row.get("classification"), row.get("issue_id"), row.get("relative_path"), row.get("line"), row.get("detail")] for row in open_issues],
    )
    optimization_table = def_html_table(
        ["Severity", "Issue", "File", "Auto Fix", "Status", "Detail"],
        [[row.get("severity"), row.get("issue_id"), row.get("relative_path"), row.get("auto_fixable"), row.get("status"), row.get("detail")] for row in optimization_rows],
    )
    hydra_table = def_html_table(
        ["Severity", "Issue", "Subsystem", "File", "Detail"],
        [[row.get("severity"), row.get("issue_id"), row.get("subsystem"), row.get("relative_path"), row.get("detail")] for row in hydra_rows],
    )
    dependency_table = def_html_table(
        ["Source", "Target", "Dependency", "Type", "Status"],
        [[row.get("source_path"), row.get("target_path"), row.get("dependency_name"), row.get("edge_type"), row.get("status")] for row in dependencies],
    )
    fix_order_table = def_html_table(
        ["Order", "Severity", "Class", "Issue", "File", "Allowed Action"],
        [[index, row.get("severity"), row.get("classification"), row.get("issue_id"), row.get("relative_path"), "SANDBOX_SAFE_FIX" if row.get("auto_fixable") else "SUGGESTION_OR_SIDECAR_ONLY"] for index, row in enumerate(fix_order, start=1)],
    )
    patch_table = def_html_table(
        ["Patch", "File", "Fix IDs", "Status", "Validation", "Overlay"],
        [[row.get("patch_id"), row.get("relative_path"), row.get("fix_ids"), row.get("status"), row.get("validation"), row.get("overlay_path")] for row in patches],
    )
    verify_table = def_html_table(
        ["Status", "Language", "File", "Detail"],
        [[row.get("status"), row.get("language"), row.get("relative_path"), row.get("detail")] for row in verification],
    )
    ssot_table = def_html_table(
        ["File", "Gate", "Contract Hash", "Module IDs", "Anchors", "Exports"],
        [[row.get("relative_path"), row.get("gate"), str(row.get("contract_hash", ""))[:16], row.get("module_ids"), row.get("anchors"), row.get("exports")] for row in assets],
    )
    subsystem_table = def_html_table(
        ["Subsystem", "Green", "Yellow", "Red", "Total"],
        [[name, counts["G"], counts["Y"], counts["R"], sum(counts.values())] for name, counts in sorted(subsystem_health.items())],
    )
    quantity_table = def_html_table(
        ["Metric", "Count"],
        [[key, value] for key, value in summary.items() if isinstance(value, (int, float))] + [["Gate " + key, value] for key, value in summary["gate_counts"].items()] + [["Severity " + key, value] for key, value in summary["severity_counts"].items()],
    )
    adaptive_table = def_html_table(
        ["File", "Tier", "Horizon", "Risk", "High", "Fan In", "Fan Out", "Validation Scope"],
        [[row.get("relative_path"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("tier"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("downstream_horizon"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("risk_score"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("high_issue_count"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("fan_in"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("fan_out"), (row.get("analysis_meta") or {}).get("adaptive_profile", {}).get("validation_scope")] for row in assets],
    )
    circuit_table = def_html_table(
        ["File", "State", "Consecutive High Runs", "Threshold", "High Issues", "Action"],
        [[row.get("relative_path"), (row.get("analysis_meta") or {}).get("failure_circuit", {}).get("state"), (row.get("analysis_meta") or {}).get("failure_circuit", {}).get("consecutive_high_runs"), (row.get("analysis_meta") or {}).get("failure_circuit", {}).get("threshold"), (row.get("analysis_meta") or {}).get("failure_circuit", {}).get("high_issue_count"), (row.get("analysis_meta") or {}).get("failure_circuit", {}).get("action")] for row in assets],
    )
    interface_table = def_html_table(
        ["Caller", "Object", "Target Module", "Attribute", "Kind", "Status"],
        [[row.get("caller_path"), row.get("object_path"), row.get("target_module"), row.get("attribute"), row.get("reference_kind"), row.get("status")] for row in interface_rows],
    )
    cycle_table = def_html_table(
        ["Cycle", "Node Count"],
        [[cycle, len(cycle)] for cycle in cycle_rows],
    )

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(def_PARAM_SYSTEM_NAME)} · Adaptive Downstream Round {payload['round_no']}</title>
<style>
:root{{--bg:#f4f6f8;--surface:#ffffff;--border:#d9dee5;--ink:#24303d;--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--yellow:#c4943a;--red:#c96b5a;--violet:#7a6daa;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:12px/1.5 Inter,"Noto Sans TC",Arial,sans-serif}}
header{{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 22px;position:sticky;top:0;z-index:10}}
h1{{font-size:20px;margin:0 0 4px}} .sub{{color:var(--muted);font-family:ui-monospace,monospace}}
main{{max-width:1800px;margin:auto;padding:14px 18px 40px}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:7px;margin-bottom:10px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:9px;padding:9px 11px}} .value{{font-size:20px;font-weight:800}} .label{{color:var(--muted);font-size:10px;text-transform:uppercase}}
section{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px;margin:8px 0}} h2{{font-size:14px;margin:0 0 8px;color:var(--blue)}}
.table-wrap{{overflow:auto;max-height:520px;border:1px solid var(--border);border-radius:7px}} table{{border-collapse:collapse;width:100%;font-size:10px}} th{{position:sticky;top:0;background:#eef2f6;text-align:left;z-index:1}} th,td{{border-bottom:1px solid var(--border);padding:5px 6px;vertical-align:top;white-space:nowrap}} td:last-child{{white-space:normal;min-width:260px}} tr:hover{{background:#f8fafb}}
.policy{{display:flex;gap:5px;flex-wrap:wrap}} .badge{{border-radius:12px;padding:2px 7px;background:#edf1f5;color:var(--muted);font-size:10px}} .empty{{text-align:center;color:var(--muted)}}
.g{{color:var(--green)}}.y{{color:var(--yellow)}}.r{{color:var(--red)}}
</style>
</head>
<body>
<header><h1>Veritas Intelligence Analytics · VIA Central Government</h1><div class="sub">Adaptive Downstream Governance · Round {payload['round_no']} · {html.escape(payload['round_name'])} · {html.escape(payload['finished_at_utc'])}</div></header>
<main>
<div class="cards">{card_html}</div>
<section><h2>Governance Policy</h2><div class="policy">{''.join(def_html_badge(f'{key}={value}', 'policy') for key,value in payload['policy'].items())}</div></section>
<section><h2>RYG Multi-System Comparison</h2>{subsystem_table}</section>
<section><h2>Error Matrix</h2>{error_table}</section>
<section><h2>Optimization Matrix</h2>{optimization_table}</section>
<section><h2>Hydra Risk Matrix</h2>{hydra_table}</section>
<section><h2>Dependency Matrix</h2>{dependency_table}</section>
<section><h2>Dependency Cycle Matrix</h2>{cycle_table}</section>
<section><h2>Interface Contract Matrix</h2>{interface_table}</section>
<section><h2>Adaptive Risk-Depth Matrix · A08</h2>{adaptive_table}</section>
<section><h2>Failure Circuit-Breaker Matrix · A15</h2>{circuit_table}</section>
<section><h2>Fix Order Matrix</h2>{fix_order_table}</section>
<section><h2>Sandbox Patch Matrix</h2>{patch_table}</section>
<section><h2>Sandbox Verification</h2>{verify_table}</section>
<section><h2>SSOT / Contract Comparison</h2>{ssot_table}</section>
<section><h2>Quantity Validation</h2>{quantity_table}</section>
</main></body></html>"""


def def_save_round_report(run_dir: Path, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    round_dir = run_dir / f"round_{payload['round_no']}"
    json_path = round_dir / f"VIA_CG_Adaptive_Round_{payload['round_no']}.json"
    html_path = round_dir / f"VIA_CG_Adaptive_Round_{payload['round_no']}.html"
    def_write_json(json_path, payload)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(def_render_round_html(payload), encoding="utf-8")
    def_write_csv(round_dir / "assets.csv", payload["assets"])
    def_write_csv(round_dir / "issues.csv", payload["issues"])
    def_write_csv(round_dir / "dependencies.csv", payload["dependencies"])
    def_write_csv(round_dir / "patches.csv", payload["patches"])
    return json_path, html_path


def def_build_round_result(payload: Dict[str, Any], json_path: Path, html_path: Path) -> def_RoundResult:
    summary = payload["summary"]
    return def_RoundResult(
        round_no=int(payload["round_no"]),
        name=str(payload["round_name"]),
        started_at_utc=str(payload["started_at_utc"]),
        finished_at_utc=str(payload["finished_at_utc"]),
        assets=int(summary["assets"]),
        issues_open=int(summary["issues_open"]),
        issues_resolved=int(summary["issues_resolved_in_overlay"]),
        patches_written=int(summary["patches"]),
        gate_counts=dict(summary["gate_counts"]),
        health_counts=dict(summary["health_counts"]),
        classification_counts=dict(summary["classification_counts"]),
        report_json=str(json_path),
        report_html=str(html_path),
    )


# ══════════════════════════════════════════════════════════════════════════════
# def ENGINE ORCHESTRATION — 三輪全景式閉環
# ══════════════════════════════════════════════════════════════════════════════
def def_analyze_assets_parallel(assets: Sequence[def_AssetRecord], resource_budget: Dict[str, Any]) -> Tuple[List[def_AssetRecord], List[def_IssueRecord], List[def_ContractRecord]]:
    analyzed_assets: List[def_AssetRecord] = []
    issues: List[def_IssueRecord] = []
    contracts: List[def_ContractRecord] = []
    workers = int(resource_budget.get("workers", 1))
    with ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="VCG-SCAN") as executor:
        future_map = {executor.submit(def_analyze_single_asset, asset): asset for asset in assets}
        for future in as_completed(future_map):
            asset = future_map[future]
            try:
                analyzed_asset, asset_issues, contract = future.result()
            except Exception as exc:
                analyzed_asset = asset
                asset_issues = [def_issue(asset, "ANALYZER_UNHANDLED_EXCEPTION", "L01_STRUCTURE_AST", "ANALYZER", "CRITICAL", "分析器未處理例外", str(exc), evidence={"traceback": traceback.format_exc()})]
                contract = def_ContractRecord(asset.asset_id, asset.relative_path, asset.language, asset.subsystem, Path(asset.relative_path).stem, "", "", [], [], [], [], [], [], False, def_sha256_text(asset.relative_path + ":UNHANDLED"))
            analyzed_assets.append(analyzed_asset)
            issues.extend(asset_issues)
            contracts.append(contract)
    analyzed_assets.sort(key=lambda row: (row.subsystem, row.relative_path.lower()))
    contracts.sort(key=lambda row: row.relative_path.lower())
    issues.sort(key=lambda row: (-def_PARAM_RISK_WEIGHTS.get(row.severity, 0), row.relative_path.lower(), row.issue_id))
    return analyzed_assets, issues, contracts


def def_apply_incremental_cache(assets: List[def_AssetRecord], baseline: Dict[str, Any]) -> Tuple[List[def_AssetRecord], Dict[str, Dict[str, Any]]]:
    cache = def_baseline_asset_cache(baseline)
    changed: List[def_AssetRecord] = []
    reused: Dict[str, Dict[str, Any]] = {}
    for asset in assets:
        previous = cache.get(asset.relative_path)
        if isinstance(previous, dict) and previous.get("content_hash") == asset.content_hash:
            reused[asset.relative_path] = previous
        else:
            changed.append(asset)
    return changed, reused


def def_restore_cached_analysis(assets: List[def_AssetRecord], changed_results: Sequence[def_AssetRecord], changed_issues: Sequence[def_IssueRecord], changed_contracts: Sequence[def_ContractRecord], reused: Dict[str, Dict[str, Any]]) -> Tuple[List[def_AssetRecord], List[def_IssueRecord], List[def_ContractRecord]]:
    changed_asset_map = {asset.relative_path: asset for asset in changed_results}
    issue_rows: List[def_IssueRecord] = list(changed_issues)
    contract_rows: List[def_ContractRecord] = list(changed_contracts)
    final_assets: List[def_AssetRecord] = []
    for asset in assets:
        if asset.relative_path in changed_asset_map:
            final_assets.append(changed_asset_map[asset.relative_path])
            continue
        previous = reused.get(asset.relative_path, {})
        try:
            cached_asset = def_AssetRecord(**previous["asset"])
            cached_asset.absolute_path = asset.absolute_path
            cached_asset.modified_ns = asset.modified_ns
            cached_asset.cached = True
            final_assets.append(cached_asset)
            for row in previous.get("issues", []):
                restored_row = dict(row)
                if restored_row.get("status") == "RESOLVED_IN_OVERLAY":
                    restored_row["status"] = "OPEN"
                issue_rows.append(def_IssueRecord(**restored_row))
            contract_rows.append(def_ContractRecord(**previous["contract"]))
        except Exception:
            final_assets.append(asset)
    final_assets.sort(key=lambda row: (row.subsystem, row.relative_path.lower()))
    issue_rows.sort(key=lambda row: (-def_PARAM_RISK_WEIGHTS.get(row.severity, 0), row.relative_path.lower(), row.issue_id))
    contract_rows.sort(key=lambda row: row.relative_path.lower())
    return final_assets, issue_rows, contract_rows


def def_build_baseline_payload(assets: Sequence[def_AssetRecord], issues: Sequence[def_IssueRecord], contracts: Sequence[def_ContractRecord], run_summary: Dict[str, Any]) -> Dict[str, Any]:
    issue_map: Dict[str, List[def_IssueRecord]] = defaultdict(list)
    contract_map = {contract.relative_path: contract for contract in contracts}
    for issue in issues:
        issue_map[issue.relative_path].append(issue)
    asset_cache: Dict[str, Any] = {}
    for asset in assets:
        contract = contract_map.get(asset.relative_path)
        if contract is None:
            continue
        asset_cache[asset.relative_path] = {
            "content_hash": asset.content_hash,
            "asset": asdict(asset),
            "issues": [asdict(issue) for issue in issue_map.get(asset.relative_path, [])],
            "contract": asdict(contract),
        }
    return {
        "generated_at_utc": def_now_utc_iso(),
        "engine_version": def_PARAM_ENGINE_VERSION,
        "root": run_summary.get("root", ""),
        "asset_cache": asset_cache,
        "contracts": {contract.relative_path: asdict(contract) for contract in contracts},
        "failure_counts": {
            asset.relative_path: dict((asset.analysis_meta or {}).get("failure_circuit", {}))
            for asset in assets
        },
        "run_summary": run_summary,
    }


def def_execute_three_rounds(config: def_EngineConfig) -> Dict[str, Any]:
    if config.rounds != 3:
        raise ValueError("VIA governance policy requires exactly three rounds; rounds must equal 3.")
    if config.mode not in def_PARAM_ALLOWED_MODES:
        raise ValueError(f"Unsupported mode: {config.mode}")
    if not config.root.exists() or not config.root.is_dir():
        raise FileNotFoundError(f"Root not found or not directory: {config.root}")

    run_dir = config.output_root / f"RUN_{def_run_stamp()}_{def_PARAM_ENGINE_NAME}_v0100"
    run_dir.mkdir(parents=True, exist_ok=False)
    ledger_path = run_dir / "event_ledger.jsonl"
    resource_budget = def_resolve_resource_budget(config.max_workers)
    baseline_path = def_find_latest_baseline(config.output_root, config.baseline_path, config.root)
    baseline = def_load_baseline(baseline_path)
    def_append_jsonl(ledger_path, {"event": "RUN_CREATED", "time": def_now_utc_iso(), "run_dir": str(run_dir), "root": str(config.root), "mode": config.mode, "baseline": str(baseline_path or "")})

    # def ROUND 1 — full discovery + parallel-safe sandbox fixes
    round1_started = def_now_utc_iso()
    discovered_assets = def_discover_assets(config)
    if config.incremental and baseline:
        changed_assets, reused = def_apply_incremental_cache(discovered_assets, baseline)
    else:
        changed_assets, reused = discovered_assets, {}
    def_append_jsonl(ledger_path, {"event": "DISCOVERY_COMPLETE", "time": def_now_utc_iso(), "assets": len(discovered_assets), "changed": len(changed_assets), "reused": len(reused)})
    changed_results, changed_issues, changed_contracts = def_analyze_assets_parallel(changed_assets, resource_budget)
    assets, issues, contracts = def_restore_cached_analysis(discovered_assets, changed_results, changed_issues, changed_contracts, reused)
    edges, dependency_issues = def_build_dependency_edges(assets)
    issues.extend(dependency_issues)
    cycles = def_find_dependency_cycles(assets, edges)
    asset_by_id = {asset.asset_id: asset for asset in assets}
    for cycle in cycles:
        cycle_paths = [asset_by_id[node_id].relative_path for node_id in cycle if node_id in asset_by_id]
        for node_id in set(cycle):
            asset = asset_by_id.get(node_id)
            if asset:
                issues.append(def_issue(asset, "DEPENDENCY_CYCLE", "L03_DEPENDENCY_ROUTING", "DEPENDENCY_CYCLE", "HIGH", "循環相依", f"cycle={cycle_paths}", evidence={"cycle": cycle_paths}))
    issues.extend(def_detect_global_hydra(assets, contracts))
    interface_issues, interface_matrix = def_detect_interface_contract_mismatch(assets, contracts)
    issues.extend(interface_issues)
    issues.extend(def_detect_contract_drift(assets, contracts, baseline))
    issues = def_dedupe_issues(issues)
    adaptive_profiles = def_apply_adaptive_risk_profiles(assets, issues, edges)
    issues.extend(def_propagate_downstream_holds(assets, edges, issues))
    issues = def_dedupe_issues(issues)
    circuit_states = def_apply_failure_circuit_breaker(assets, issues, baseline)
    issues = def_dedupe_issues(issues)
    issues.sort(key=lambda row: (-def_PARAM_RISK_WEIGHTS.get(row.severity, 0), row.relative_path.lower(), row.issue_id))
    patches = def_stage_round1_safe_fixes(run_dir, assets, issues, config.mode)
    verification_r1 = def_verify_assets(assets, patches)
    def_assign_asset_gates(assets, issues, verification_r1)
    round1_payload = def_build_round_payload(1, "Comprehensive Parallel-Safe Fix", round1_started, assets, issues, contracts, edges, patches, verification_r1, resource_budget, {"cycles": cycles, "interface_matrix": interface_matrix, "adaptive_profiles": adaptive_profiles, "failure_circuits": circuit_states, "incremental_reused": len(reused), "incremental_changed": len(changed_assets)})
    round1_json, round1_html = def_save_round_report(run_dir, round1_payload)
    round_results = [def_build_round_result(round1_payload, round1_json, round1_html)]
    def_append_jsonl(ledger_path, {"event": "ROUND_COMPLETE", "round": 1, "time": def_now_utc_iso(), "summary": round1_payload["summary"]})

    # def ROUND 2 — dependency ordered sidecars / suggestions only for high risk
    round2_started = def_now_utc_iso()
    order = def_dependency_topological_order(assets, edges)
    sidecars = def_generate_contract_sidecars(run_dir, contracts, issues)
    plans = def_generate_resolution_plans(run_dir, assets, edges, issues, order)
    verification_r2 = def_verify_assets(assets, patches)
    def_assign_asset_gates(assets, issues, verification_r2)
    round2_payload = def_build_round_payload(2, "Dependency-Ordered Contract And Routing Governance", round2_started, assets, issues, contracts, edges, patches, verification_r2, resource_budget, {"topological_order": order, "contract_sidecars": sidecars, "plans": plans, "cycles": cycles, "interface_matrix": interface_matrix, "adaptive_profiles": adaptive_profiles, "failure_circuits": circuit_states})
    round2_json, round2_html = def_save_round_report(run_dir, round2_payload)
    round_results.append(def_build_round_result(round2_payload, round2_json, round2_html))
    def_append_jsonl(ledger_path, {"event": "ROUND_COMPLETE", "round": 2, "time": def_now_utc_iso(), "summary": round2_payload["summary"]})

    # def ROUND 3 — re-verify, stability hardening, no new source mutation
    round3_started = def_now_utc_iso()
    verification_r3 = def_verify_assets(assets, patches)
    def_assign_asset_gates(assets, issues, verification_r3)
    unresolved_high = [issue for issue in issues if issue.status == "OPEN" and issue.severity in {"CRITICAL", "HIGH"}]
    final_gate = "HOLD_REMEDIATION_REQUIRED" if unresolved_high else "READY_FOR_MANUAL_USER_TEST_REVIEW"
    round3_payload = def_build_round_payload(3, "Final Re-Analysis And Stability Hardening", round3_started, assets, issues, contracts, edges, patches, verification_r3, resource_budget, {"final_gate": final_gate, "unresolved_high_count": len(unresolved_high), "new_fixes_in_round_3": 0, "cycles": cycles, "interface_matrix": interface_matrix, "adaptive_profiles": adaptive_profiles, "failure_circuits": circuit_states})
    round3_json, round3_html = def_save_round_report(run_dir, round3_payload)
    round_results.append(def_build_round_result(round3_payload, round3_json, round3_html))
    def_append_jsonl(ledger_path, {"event": "ROUND_COMPLETE", "round": 3, "time": def_now_utc_iso(), "summary": round3_payload["summary"], "final_gate": final_gate})

    final_summary = {
        "ok": len(unresolved_high) == 0,
        "gate": final_gate,
        "activation": "NOT_ACTIVATED",
        "canonical_mutation": False,
        "network_used": False,
        "target_imported": False,
        "root": str(config.root),
        "mode": config.mode,
        "run_dir": str(run_dir),
        "baseline_used": str(baseline_path or ""),
        "assets": len(assets),
        "issues_open": len([issue for issue in issues if issue.status == "OPEN"]),
        "issues_resolved_in_overlay": len([issue for issue in issues if issue.status != "OPEN"]),
        "unresolved_high": len(unresolved_high),
        "patches": len(patches),
        "rounds": [asdict(result) for result in round_results],
        "final_html": str(round3_html),
        "final_json": str(round3_json),
        "event_ledger": str(ledger_path),
        "contract_sidecars": len(sidecars),
    }
    summary_path = run_dir / "VIA_CG_Adaptive_Summary.json"
    def_write_json(summary_path, final_summary)
    baseline_payload = def_build_baseline_payload(assets, issues, contracts, final_summary)
    def_write_json(run_dir / "baseline.json", baseline_payload)
    def_write_json(run_dir / "hash_ledger.json", {
        "generated_at_utc": def_now_utc_iso(),
        "policy": "original -> overlay / same proposal -> skip / other -> new append-only proposal",
        "assets": [{"relative_path": asset.relative_path, "content_hash": asset.content_hash, "contract_hash": asset.contract_hash} for asset in assets],
        "patches": [asdict(patch) for patch in patches],
    })
    def_append_jsonl(ledger_path, {"event": "RUN_COMPLETE", "time": def_now_utc_iso(), "summary_path": str(summary_path), "gate": final_gate})
    return final_summary


# ══════════════════════════════════════════════════════════════════════════════
# def SELF TESTS
# ══════════════════════════════════════════════════════════════════════════════
def def_test_normalize_module_key() -> None:
    assert def_normalize_module_key("VIA_Core_v0100 (2).py") == "via_core"


def def_test_safe_fix() -> None:
    payload = b"\xef\xbb\xbfprint('x')  \r\n"
    text_value, _ = def_decode_text(payload)
    proposed = def_apply_safe_text_fixes(payload, text_value, ["ENC_UTF8_BOM", "FMT_TRAILING_WHITESPACE", "FMT_MIXED_NEWLINES", "FMT_FINAL_NEWLINE"])
    assert proposed == b"print('x')\n"


def def_test_safe_fix_preserves_encoding_and_crlf() -> None:
    original_text = "測試  \r\n下一行\r\n"
    payload = original_text.encode("cp950")
    text_value, encoding = def_decode_text(payload)
    assert encoding == "cp950"
    proposed = def_apply_safe_text_fixes(payload, text_value, ["FMT_TRAILING_WHITESPACE"])
    assert proposed.decode("cp950") == "測試\r\n下一行\r\n"


def def_test_rule_corpus_validation() -> None:
    source = "import json\nRULES = json.loads(r'''[{\"rule_name\":\"X\",\"pattern\":\"^A$\",\"examples_pass\":[\"B\"],\"examples_fail\":[\"A\"]}]''')\n"
    findings = def_validate_json_loads_rule_corpora(ast.parse(source))
    kinds = {row["kind"] for row in findings}
    assert "REGEX_PASS_EXAMPLE_MISSED" in kinds
    assert "REGEX_FAIL_EXAMPLE_MATCHED" in kinds


def def_test_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "project"
        output = Path(temp_dir) / "runs"
        root.mkdir()
        original = "\ufefffrom __future__ import annotations\n\ndef def_main():  \n    return 0"
        (root / "VIA_Demo_v1.py").write_text(original, encoding="utf-8")
        (root / "VIA_Demo_v1 (1).py").write_text(original, encoding="utf-8")
        config = def_EngineConfig(root=root, output_root=output, mode="STAGE", rounds=3, max_workers=2, incremental=False)
        summary = def_execute_three_rounds(config)
        assert summary["activation"] == "NOT_ACTIVATED"
        assert summary["canonical_mutation"] is False
        assert summary["rounds"] and len(summary["rounds"]) == 3
        assert (root / "VIA_Demo_v1.py").read_text(encoding="utf-8") == original
        assert summary["patches"] >= 1


def def_test_adaptive_risk_profile() -> None:
    a = def_AssetRecord("A", "VIA_A.py", "/tmp/VIA_A.py", ".py", "PYTHON", "VCG", "ENTRY", 1, 1, 0, "h")
    b = def_AssetRecord("B", "VDF_B.py", "/tmp/VDF_B.py", ".py", "PYTHON", "VDF", "MODULE", 1, 1, 0, "h2")
    issue = def_issue(a, "X", "L05_SECURITY_GOVERNANCE", "SECURITY", "HIGH", "x", "x")
    edge = def_DependencyEdge("A", "B", "VIA_A.py", "VDF_B.py", "VDF_B", "LOCAL_IMPORT", "RESOLVED")
    profiles = def_apply_adaptive_risk_profiles([a, b], [issue], [edge])
    assert profiles["VIA_A.py"]["tier"] == "DEEP"
    assert profiles["VIA_A.py"]["downstream_horizon"] == 5


def def_test_failure_circuit_breaker() -> None:
    asset = def_AssetRecord("A", "VIA_A.py", "/tmp/VIA_A.py", ".py", "PYTHON", "VCG", "ENTRY", 1, 1, 0, "h")
    issue = def_issue(asset, "X", "L05_SECURITY_GOVERNANCE", "SECURITY", "HIGH", "x", "x")
    baseline = {"failure_counts": {"VIA_A.py": {"consecutive_high_runs": 2}}}
    states = def_apply_failure_circuit_breaker([asset], [issue], baseline)
    assert states["VIA_A.py"]["state"] == "OPEN"
    assert asset.analysis_meta["failure_circuit"]["action"] == "HUMAN_REVIEW_ONLY"


def def_test_cached_overlay_status_reopens() -> None:
    asset = def_AssetRecord("A", "VIA_A.py", "/tmp/VIA_A.py", ".py", "PYTHON", "VCG", "MODULE", 1, 1, 0, "h")
    contract = def_ContractRecord("A", "VIA_A.py", "PYTHON", "VCG", "VIA_A", "", "", [], [], [], [], [], [], False, "ch")
    issue = def_IssueRecord("FMT_FINAL_NEWLINE", "A", "VIA_A.py", "VCG", "L06_QUALITY_OPTIMIZATION", "FORMAT", "LOW", "PARALLEL_FIXABLE", "x", "x", auto_fixable=True, fix_id="FMT_FINAL_NEWLINE", status="RESOLVED_IN_OVERLAY")
    reused = {"VIA_A.py": {"asset": asdict(asset), "issues": [asdict(issue)], "contract": asdict(contract)}}
    _, rows, _ = def_restore_cached_analysis([asset], [], [], [], reused)
    assert rows[0].status == "OPEN"


def def_run_self_tests() -> Dict[str, Any]:
    tests = [
        def_test_normalize_module_key,
        def_test_safe_fix,
        def_test_safe_fix_preserves_encoding_and_crlf,
        def_test_rule_corpus_validation,
        def_test_adaptive_risk_profile,
        def_test_failure_circuit_breaker,
        def_test_cached_overlay_status_reopens,
        def_test_end_to_end,
    ]
    passed: List[str] = []
    failed: List[Dict[str, Any]] = []
    for test_func in tests:
        try:
            test_func()
            passed.append(test_func.__name__)
        except Exception as exc:
            failed.append({"test": test_func.__name__, "error": str(exc), "traceback": traceback.format_exc()})
    return {"ok": not failed, "total": len(tests), "passed": passed, "failed": failed}


# ══════════════════════════════════════════════════════════════════════════════
# def CLI
# ══════════════════════════════════════════════════════════════════════════════
def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA Central Government adaptive downstream governance engine")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run exactly three governance rounds")
    run_parser.add_argument("--root", required=True)
    run_parser.add_argument("--output-root", required=True)
    run_parser.add_argument("--mode", choices=def_PARAM_ALLOWED_MODES, default=def_PARAM_DEFAULT_MODE)
    run_parser.add_argument("--rounds", type=int, default=3)
    run_parser.add_argument("--max-depth", type=int, default=def_PARAM_MAX_DEPTH)
    run_parser.add_argument("--max-workers", type=int, default=def_PARAM_MAX_WORKERS)
    run_parser.add_argument("--no-incremental", action="store_true")
    run_parser.add_argument("--baseline", default="")
    run_parser.add_argument("--open-html", action="store_true")

    subparsers.add_parser("selftest", help="Run standard-library-only self tests")
    subparsers.add_parser("capabilities", help="Print engine capability contract")
    return parser


def def_capabilities() -> Dict[str, Any]:
    return {
        "system": def_PARAM_SYSTEM_NAME,
        "engine": def_PARAM_ENGINE_NAME,
        "version": def_PARAM_ENGINE_VERSION,
        "registry_id": def_PARAM_REGISTRY_ID,
        "modes": list(def_PARAM_ALLOWED_MODES),
        "rounds": 3,
        "lanes": def_PARAM_SCANNING_LANES,
        "accelerators": def_PARAM_ACCELERATORS,
        "gates": def_PARAM_GATE_SEQUENCE,
        "safe_fix_ids": sorted(def_PARAM_SAFE_FIX_IDS),
        "forbidden": ["canonical mutation", "automatic activation", "target import", "network", "high-risk automatic repair"],
    }


def def_main(argv: Optional[List[str]] = None) -> int:
    parser = def_build_parser()
    args = parser.parse_args(argv)
    command = args.command or "capabilities"
    if command == "selftest":
        result = def_run_self_tests()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    if command == "capabilities":
        print(json.dumps(def_capabilities(), ensure_ascii=False, indent=2))
        return 0
    if command == "run":
        config = def_EngineConfig(
            root=Path(args.root),
            output_root=Path(args.output_root),
            mode=args.mode,
            rounds=args.rounds,
            max_depth=args.max_depth,
            max_workers=args.max_workers,
            incremental=not args.no_incremental,
            open_html=args.open_html,
            baseline_path=Path(args.baseline) if args.baseline else None,
        )
        try:
            summary = def_execute_three_rounds(config)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0 if summary.get("gate") in {"READY_FOR_MANUAL_USER_TEST_REVIEW", "HOLD_REMEDIATION_REQUIRED"} else 1
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2))
            return 2
    parser.print_help()
    return 1


def def_run_cli() -> None:
    code = def_main()
    if code != 0:
        print(f"[{def_PARAM_ENGINE_NAME}] exit_code={code}", file=sys.stderr)


if __name__ == "__main__":
    def_run_cli()
