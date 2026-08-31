from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

"""VIA Central Governance 自適應向下治理與沙盒修補引擎 v1.0.0。"""

# =============================================================================
# def PARAMETERS
# =============================================================================
import argparse
import ast
import builtins
import concurrent.futures
import contextlib
import copy
import datetime as dt
import fnmatch
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set, Tuple


def_PARAM_ENGINE = "VIA_ADAPTIVE_DOWNWARD_GOVERNOR"
def_PARAM_VERSION = "1.0.0"
def_PARAM_ASSET_ID = "AST-PY-ENG-VIA-710-100"
def_PARAM_MAX_ROUNDS = 3

def_PARAM_ROOT_CANDIDATES = [
    Path(r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"),
    Path(r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics"),
    Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"),
    Path("/mnt/data"),
]

def_PARAM_CORE_MODULES = [
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_SSOT_Unified",
    "VIA_EnvManager",
    "VIA_RegistryCore_v1",
    "VeritasAegisNexus",
    "VeritasCeleritas",
]

def_PARAM_EXPECTED_EXPORTS = {
    "VIA_EnvManager": ["def_scan_all_envs", "def_get_base_via_conflicts", "def_plan_install_request"],
    "VIA_RegistryCore_v1": ["def_status_report", "def_resolve_module"],
    "VIA_SSOT_Unified": ["get_ssot", "normalize", "extract", "contains"],
    "VeritasAegisNexus": ["fetch_json", "fetch_text", "safe_request"],
    "VeritasCeleritas": ["cross_init", "xmap", "xbatch_process", "thread_budget"],
}

def_PARAM_SUFFIXES = {
    ".py", ".ps1", ".psm1", ".psd1", ".js", ".mjs", ".cjs", ".ts",
    ".html", ".htm", ".json", ".jsonl", ".yaml", ".yml", ".md", ".txt",
}

def_PARAM_IGNORE_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules", "site-packages", "dist-packages",
    "build", "dist", ".tox", ".nox", ".venv", "venv", "env",
    "_via_adaptive_downward_runs", "_via_registry_output", "_via_envmanager_output",
}

def_PARAM_IGNORE_GLOBS = ["*.pyc", "*.pyo", "*.tmp", "*.temp", "*.lock"]
def_PARAM_MAX_TEXT_BYTES = 12 * 1024 * 1024

def_PARAM_CLASS_PARALLEL = "PARALLEL_FIXABLE"
def_PARAM_CLASS_SEQUENCE = "SEQUENCE_DEPENDENT"
def_PARAM_CLASS_SYNC = "MULTI_SUBSYSTEM_SYNCHRONIZATION"
def_PARAM_CLASS_HYDRA = "HYDRA_REVIEW_ONLY"

def_PARAM_WEIGHT = {"INFO": 0, "LOW": 1, "MEDIUM": 3, "HIGH": 7, "CRITICAL": 12}
def_PARAM_RYG = {"INFO": "GREEN", "LOW": "GREEN", "MEDIUM": "YELLOW", "HIGH": "RED", "CRITICAL": "RED"}

def_PARAM_WINDOWS_PATH = re.compile(r"[A-Za-z]:\\[^\r\n\"']+")
def_PARAM_POSIX_PATH = re.compile(r"(?<![A-Za-z0-9_])/(?:mnt|home|Users|opt|var|tmp)/[^\r\n\"']+")
def_PARAM_ASSET_ID_RE = re.compile(r"AST-(?:PS|PY|JS|HTML|JSON|YAML|META)-(?:MOD|CLS|FNC|CHK|RUN|MAIN|REG|CFG|LIB|PKG|RPT|FIX|ENG|TPL)-[A-Z0-9]+-\d{3}-\d{3}")
def_PARAM_VERSION_RE = re.compile(r"(?i)(?:__version__\s*=\s*[\"']|\bversion\s*[:=]\s*[\"']?)(v?\d+(?:\.\d+){0,3})")
def_PARAM_PREFIX = re.compile(r"^(VIA|VRN|VDF|VAP|VGF|VPNS|VETF|VMFRS|VPN|VPS|VSE|VIS|VDS|VGE)(?:[_\-.]|$)", re.I)

def_PARAM_ACCELERATORS = [
    {"id": "A01", "name": "Short-Path Run Governance", "enabled": True},
    {"id": "A02", "name": "Incremental SHA-256 Scan", "enabled": True},
    {"id": "A03", "name": "AST-NoImport Analysis", "enabled": True},
    {"id": "A04", "name": "Parallel-Safe Read Lanes", "enabled": True},
    {"id": "A05", "name": "Adaptive CPU/RAM Worker Budget", "enabled": True},
    {"id": "A06", "name": "Append-Only Evidence Ledger", "enabled": True},
    {"id": "A07", "name": "Atomic Output Writes", "enabled": True},
    {"id": "A08", "name": "JSON Asset Index", "enabled": True},
    {"id": "A09", "name": "Interface Contract Cache", "enabled": True},
    {"id": "A10", "name": "Dependency Graph Resolver", "enabled": True},
    {"id": "A11", "name": "Hydra SCC Detector", "enabled": True},
    {"id": "A12", "name": "SSOT Difference Validator", "enabled": True},
    {"id": "A13", "name": "Sandbox Mirror Repair", "enabled": True},
    {"id": "A14", "name": "Idempotent Patch State Machine", "enabled": True},
    {"id": "A15", "name": "HTML RYG Matrix Generator", "enabled": True},
]

def_PARAM_GENERATED_ASSET_IDS = {
    "manifest": "AST-JSON-REG-VIA-710-101",
    "ssot_overlay": "AST-JSON-CFG-VIA-710-102",
    "contract_ssot": "AST-JSON-REG-VIA-710-103",
    "path_registry": "AST-PY-REG-VIA-710-104",
    "contract_bridge": "AST-PY-MOD-VIA-710-105",
    "activation_config": "AST-JSON-CFG-VIA-710-106",
    "verification": "AST-JSON-RPT-VIA-710-107",
    "hydra_queue": "AST-JSON-RPT-VIA-710-108",
}


# =============================================================================
# def DATA STRUCTURES
# =============================================================================
@dataclass
class def_Profile:
    cpu_logical: int
    cpu_physical: int
    memory_total_mb: int
    memory_available_mb: int
    memory_percent: float
    disk_free_mb: int
    workers: int
    batch_size: int
    mode: str


@dataclass
class def_Asset:
    path: str
    relative_path: str
    name: str
    stem: str
    suffix: str
    language: str
    subsystem: str
    size_bytes: int
    sha256: str
    modified_utc: str
    parse_status: str = "INDEXED"
    line_count: int = 0
    asset_ids: List[str] = field(default_factory=list)
    version: str = ""
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    contracts: List[Dict[str, Any]] = field(default_factory=list)
    hardcoded_paths: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class def_Issue:
    issue_id: str
    code: str
    severity: str
    ryg: str
    classification: str
    subsystem: str
    path: str
    relative_path: str
    line: int
    title: str
    detail: str
    evidence: str = ""
    auto_fixable: bool = False
    hydra: bool = False
    status: str = "OPEN"
    suggested_action: str = ""


@dataclass
class def_Edge:
    source: str
    target: str
    edge_type: str
    status: str = "RESOLVED"
    detail: str = ""


@dataclass
class def_Action:
    action_id: str
    round_no: int
    order_no: int
    code: str
    classification: str
    source_path: str
    target_path: str
    status: str
    detail: str
    before_sha256: str = ""
    after_sha256: str = ""
    canonical_mutation: bool = False
    hydra_touched: bool = False


@dataclass
class def_Snapshot:
    root: str
    generated_at_utc: str
    assets: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    contracts: Dict[str, Any]
    ssot: Dict[str, Any]
    quantities: Dict[str, Any]
    subsystem_health: Dict[str, Any]
    fix_order: List[Dict[str, Any]]
    summary: Dict[str, Any]


# =============================================================================
# def UTILITIES
# =============================================================================
def def_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def def_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def def_hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def def_hash_file(path_value: Path) -> str:
    digest = hashlib.sha256()
    with path_value.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def def_short(value: str, length: int = 14) -> str:
    return def_hash_text(value)[:length].upper()


def def_read(path_value: Path) -> Tuple[str, str]:
    raw = path_value.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def def_write_text(path_value: Path, text_value: str) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path_value.with_name(path_value.name + ".tmp")
    temp_path.write_text(text_value, encoding="utf-8", newline="\n")
    os.replace(temp_path, path_value)


def def_write_json(path_value: Path, payload: Any) -> None:
    def_write_text(path_value, json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def def_append_jsonl(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    with path_value.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def def_relative(path_value: Path, root_value: Path) -> str:
    try:
        return str(path_value.resolve().relative_to(root_value.resolve())).replace("\\", "/")
    except Exception:
        return path_value.name


def def_within(path_value: Path, parent_value: Path) -> bool:
    try:
        path_value.resolve().relative_to(parent_value.resolve())
        return True
    except Exception:
        return False


def def_pick_root(explicit: str = "") -> Path:
    if explicit:
        path_value = Path(explicit).expanduser()
        if not path_value.exists():
            raise FileNotFoundError(path_value)
        return path_value.resolve()
    for path_value in def_PARAM_ROOT_CANDIDATES:
        if path_value.exists():
            return path_value.resolve()
    return Path.cwd().resolve()


def def_issue(code: str, severity: str, classification: str, subsystem: str,
              path_value: Path, root_value: Path, line: int, title: str, detail: str,
              evidence: str = "", auto_fixable: bool = False, hydra: bool = False,
              suggested_action: str = "") -> def_Issue:
    relative = def_relative(path_value, root_value)
    issue_id = "ISS-" + def_short("|".join([code, relative, str(line), detail]))
    return def_Issue(issue_id, code, severity, def_PARAM_RYG.get(severity, "YELLOW"),
                     classification, subsystem, str(path_value), relative, line, title,
                     detail, evidence[:1600], auto_fixable, hydra, "OPEN", suggested_action)


def def_language(path_value: Path) -> str:
    return {".py": "PYTHON", ".ps1": "POWERSHELL", ".psm1": "POWERSHELL",
            ".psd1": "POWERSHELL", ".js": "JAVASCRIPT", ".mjs": "JAVASCRIPT",
            ".cjs": "JAVASCRIPT", ".ts": "TYPESCRIPT", ".html": "HTML",
            ".htm": "HTML", ".json": "JSON", ".jsonl": "JSONL",
            ".yaml": "YAML", ".yml": "YAML", ".md": "MARKDOWN",
            ".txt": "TEXT"}.get(path_value.suffix.lower(), "OTHER")


def def_subsystem(path_value: Path, source: str = "") -> str:
    match_value = def_PARAM_PREFIX.search(path_value.stem)
    if match_value:
        return match_value.group(1).upper()
    probe = (" ".join(path_value.parts[-5:]) + " " + source[:3000]).upper()
    for prefix in ("VRN", "VDF", "VAP", "VGF", "VPNS", "VETF", "VMFRS", "VIA", "VPN", "VPS", "VSE", "VIS", "VDS", "VGE"):
        if re.search(rf"(?:^|[^A-Z0-9]){prefix}(?:[^A-Z0-9]|$)", probe):
            return prefix
    return "GENERAL"


def def_ignore(path_value: Path, output_root: Optional[Path] = None) -> bool:
    if output_root and def_within(path_value, output_root):
        return True
    if any(part in def_PARAM_IGNORE_DIRS for part in path_value.parts):
        return True
    return any(fnmatch.fnmatch(path_value.name, pattern) for pattern in def_PARAM_IGNORE_GLOBS)


def def_profile(root_value: Path) -> def_Profile:
    logical = max(1, os.cpu_count() or 1)
    physical, total_mb, available_mb, percent = logical, 4096, 2048, 50.0
    try:
        import psutil  # type: ignore
        physical = psutil.cpu_count(logical=False) or logical
        vm = psutil.virtual_memory()
        total_mb, available_mb, percent = int(vm.total / 1048576), int(vm.available / 1048576), float(vm.percent)
    except Exception:
        pass
    try:
        free_mb = int(shutil.disk_usage(root_value).free / 1048576)
    except Exception:
        free_mb = 0
    if percent >= 90:
        mode, workers, batch = "STOP", 1, 8
    elif percent >= 82:
        mode, workers, batch = "SAFE", max(1, min(2, physical)), 16
    elif percent >= 70:
        mode, workers, batch = "BALANCED", max(1, min(4, physical)), 32
    else:
        mode, workers, batch = "MAXSAFE", max(2, min(8, max(1, physical - 1))), 64
    return def_Profile(logical, physical, total_mb, available_mb, round(percent, 2), free_mb, workers, batch, mode)


def def_files(root_value: Path, output_root: Optional[Path] = None) -> List[Path]:
    rows: List[Path] = []
    for current_root, dir_names, file_names in os.walk(root_value):
        current = Path(current_root)
        dir_names[:] = [name for name in dir_names if not def_ignore(current / name, output_root)]
        for name in sorted(file_names):
            path_value = current / name
            if path_value.suffix.lower() in def_PARAM_SUFFIXES and not def_ignore(path_value, output_root):
                rows.append(path_value)
    return sorted(rows, key=lambda row: str(row).lower())

# =============================================================================
# def PYTHON ANALYSIS
# =============================================================================
def def_ast_name(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def def_imports(tree: ast.AST) -> List[Tuple[int, str, bool]]:
    rows: List[Tuple[int, str, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            rows.extend((node.lineno, alias.name, False) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            rows.extend((node.lineno, f"{module}:{alias.name}", alias.name == "*") for alias in node.names)
    return rows


def def_contract(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Dict[str, Any]:
    return {
        "name": node.name,
        "line": node.lineno,
        "args": [arg.arg for arg in list(node.args.posonlyargs) + list(node.args.args)],
        "kwonlyargs": [arg.arg for arg in node.args.kwonlyargs],
        "vararg": node.args.vararg.arg if node.args.vararg else "",
        "kwarg": node.args.kwarg.arg if node.args.kwarg else "",
        "defaults": len(node.args.defaults),
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "decorators": [def_ast_name(row) for row in node.decorator_list],
    }


def def_defined_top(tree: ast.Module) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result[node.name] = node.lineno
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result[alias.asname or alias.name.split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    result[alias.asname or alias.name] = node.lineno
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.lineno
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            result[node.target.id] = node.lineno
    return result


def def_top_loads(node: ast.AST) -> List[Tuple[str, int]]:
    class def_Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.rows: List[Tuple[str, int]] = []

        def visit_FunctionDef(self, value: ast.FunctionDef) -> None:
            for decorator in value.decorator_list:
                self.visit(decorator)
            for default in list(value.args.defaults) + list(value.args.kw_defaults):
                if default is not None:
                    self.visit(default)

        def visit_AsyncFunctionDef(self, value: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(value)  # type: ignore[arg-type]

        def visit_ClassDef(self, value: ast.ClassDef) -> None:
            for base in value.bases:
                self.visit(base)
            for keyword in value.keywords:
                self.visit(keyword.value)
            for decorator in value.decorator_list:
                self.visit(decorator)

        def visit_Name(self, value: ast.Name) -> None:
            if isinstance(value.ctx, ast.Load):
                self.rows.append((value.id, getattr(value, "lineno", 0)))

    visitor = def_Visitor()
    visitor.visit(node)
    return visitor.rows


def def_validate_ssot_rules(tree: ast.Module, path_value: Path, root_value: Path, subsystem: str) -> List[def_Issue]:
    issues: List[def_Issue] = []
    for node in tree.body:
        target_name, value_node = "", None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name, value_node = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name, value_node = node.target.id, node.value
        if target_name != "_RAW_REGEX" or not isinstance(value_node, ast.Call) or not value_node.args:
            continue
        raw_node = value_node.args[0]
        if not isinstance(raw_node, ast.Constant) or not isinstance(raw_node.value, str):
            continue
        try:
            payload = json.loads(raw_node.value)
        except Exception as exc:
            issues.append(def_issue("SSOT_EMBEDDED_JSON_INVALID", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                    subsystem, path_value, root_value, getattr(node, "lineno", 0),
                                    "SSOT 內嵌 JSON 無法解析", str(exc),
                                    suggested_action="先修復 SSOT JSON，再允許下游同步。"))
            continue
        ids: Dict[str, int] = {}
        names: Dict[str, int] = {}
        for index, rule in enumerate(payload if isinstance(payload, list) else []):
            if not isinstance(rule, dict):
                continue
            rule_id = str(rule.get("rule_id", ""))
            rule_name = str(rule.get("rule_name", ""))
            pattern = str(rule.get("pattern", ""))
            line = getattr(node, "lineno", 0)
            if rule_id in ids:
                issues.append(def_issue("SSOT_DUPLICATE_RULE_ID", "HIGH", def_PARAM_CLASS_HYDRA,
                                        subsystem, path_value, root_value, line, "SSOT Rule ID 重複",
                                        f"{rule_id} indexes={ids[rule_id]},{index}", hydra=True,
                                        suggested_action="保留單一 canonical Rule ID；其餘轉 alias/deprecated。"))
            ids[rule_id] = index
            if rule_name in names:
                issues.append(def_issue("SSOT_DUPLICATE_RULE_NAME", "MEDIUM", def_PARAM_CLASS_SYNC,
                                        subsystem, path_value, root_value, line, "SSOT Rule Name 重複",
                                        f"{rule_name} indexes={names[rule_name]},{index}", hydra=True,
                                        suggested_action="名稱重複者建立 alias map。"))
            names[rule_name] = index
            if not pattern:
                continue
            flags = 0
            for flag_name in rule.get("flags", []):
                flags |= getattr(re, str(flag_name), 0)
            try:
                regex_obj = re.compile(pattern, flags)
            except Exception as exc:
                issues.append(def_issue("SSOT_REGEX_COMPILE_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                        subsystem, path_value, root_value, line, "SSOT Regex 無法編譯",
                                        f"{rule_id}/{rule_name}: {exc}",
                                        suggested_action="修 Regex 後重跑 pass/fail cases。"))
                continue
            for example in rule.get("examples_pass", []):
                if regex_obj.search(str(example)) is None:
                    detail = f"{rule_id}/{rule_name}: pass={example!r} 不符合 {pattern!r}"
                    issues.append(def_issue("SSOT_RULE_EXAMPLE_CONTRADICTION", "HIGH", def_PARAM_CLASS_HYDRA,
                                            subsystem, path_value, root_value, line,
                                            "SSOT 通過案例與規則矛盾", detail,
                                            json.dumps(rule, ensure_ascii=False), hydra=True,
                                            suggested_action="由 SSOT owner 決定修規則或案例；不自動改寫。"))
            for example in rule.get("examples_fail", []):
                if regex_obj.search(str(example)) is not None:
                    detail = f"{rule_id}/{rule_name}: fail={example!r} 反而符合 {pattern!r}"
                    issues.append(def_issue("SSOT_RULE_EXAMPLE_CONTRADICTION", "HIGH", def_PARAM_CLASS_HYDRA,
                                            subsystem, path_value, root_value, line,
                                            "SSOT 失敗案例與規則矛盾", detail,
                                            json.dumps(rule, ensure_ascii=False), hydra=True,
                                            suggested_action="由 SSOT owner 決定修規則或案例；不自動改寫。"))
    return issues


def def_analyze_python(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    source, encoding = def_read(path_value)
    subsystem = def_subsystem(path_value, source)
    stat_value = path_value.stat()
    version_match = def_PARAM_VERSION_RE.search(source[:12000])
    asset = def_Asset(str(path_value), def_relative(path_value, root_value), path_value.name,
                      path_value.stem, path_value.suffix.lower(), "PYTHON", subsystem,
                      stat_value.st_size, def_hash_file(path_value),
                      dt.datetime.fromtimestamp(stat_value.st_mtime, dt.timezone.utc).isoformat(),
                      line_count=len(source.splitlines()),
                      asset_ids=def_owned_asset_ids("PYTHON", source),
                      version=version_match.group(1) if version_match else "",
                      metadata={"encoding": encoding})
    issues: List[def_Issue] = []
    try:
        tree = ast.parse(source, filename=str(path_value))
        compile(tree, str(path_value), "exec")
        asset.parse_status = "PASS"
    except Exception as exc:
        asset.parse_status = "FAIL"
        issues.append(def_issue("PY_SYNTAX_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                subsystem, path_value, root_value, getattr(exc, "lineno", 0) or 0,
                                "Python AST/Compile 失敗", str(exc), traceback.format_exc(),
                                suggested_action="語法修復前停止此節點與下游啟用。"))
        return asset, issues

    import_rows = def_imports(tree)
    asset.imports = sorted(set(row[1] for row in import_rows))
    duplicate: Dict[str, List[int]] = defaultdict(list)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            asset.contracts.append(def_contract(node))
            asset.exports.append(node.name)
            duplicate[node.name].append(node.lineno)
        elif isinstance(node, ast.ClassDef):
            asset.exports.append(node.name)
            duplicate[node.name].append(node.lineno)
    asset.exports = sorted(set(asset.exports))

    for line, import_name, star in import_rows:
        base = import_name.split(":", 1)[0].split(".", 1)[0]
        if base.lower() == path_value.stem.lower():
            issues.append(def_issue("PY_SELF_IMPORT", "HIGH", def_PARAM_CLASS_HYDRA,
                                    subsystem, path_value, root_value, line, "模組自我匯入",
                                    f"{path_value.stem} imports {import_name}", hydra=True,
                                    suggested_action="移除自我 import 或以明確本地引用替代。"))
        if star:
            issues.append(def_issue("PY_WILDCARD_IMPORT", "MEDIUM", def_PARAM_CLASS_SEQUENCE,
                                    subsystem, path_value, root_value, line, "Wildcard import 不可追蹤",
                                    import_name, suggested_action="改為明確 export contract。"))

    for name, lines in duplicate.items():
        if len(lines) > 1:
            issues.append(def_issue("PY_DUPLICATE_EXPORT", "HIGH", def_PARAM_CLASS_HYDRA,
                                    subsystem, path_value, root_value, min(lines), "同模組重複定義 export",
                                    f"{name} lines={lines}", hydra=True,
                                    suggested_action="確認 canonical implementation；其餘改 alias/deprecated。"))

    future = def_defined_top(tree)
    known: Set[str] = set(dir(builtins)) | {"__name__", "__file__", "__package__", "__spec__"}
    for statement in tree.body:
        statement_line = getattr(statement, "lineno", 0)
        for name, load_line in def_top_loads(statement):
            if name not in known and future.get(name, 0) > statement_line:
                issues.append(def_issue("PY_TOPLEVEL_USE_BEFORE_DEF", "HIGH", def_PARAM_CLASS_HYDRA,
                                        subsystem, path_value, root_value, load_line,
                                        "Top-level 在定義前使用符號",
                                        f"{name} used={load_line}, defined={future[name]}", hydra=True,
                                        suggested_action="將 bootstrap 延後，或改成函式內 lazy resolution。"))
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            known.add(statement.name)
        elif isinstance(statement, ast.Import):
            known.update(alias.asname or alias.name.split(".")[0] for alias in statement.names)
        elif isinstance(statement, ast.ImportFrom):
            known.update(alias.asname or alias.name for alias in statement.names if alias.name != "*")
        elif isinstance(statement, ast.Assign):
            known.update(target.id for target in statement.targets if isinstance(target, ast.Name))
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            known.add(statement.target.id)

    paths: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            paths.update(def_PARAM_WINDOWS_PATH.findall(node.value))
            paths.update(def_PARAM_POSIX_PATH.findall(node.value))
        if isinstance(node, ast.Call):
            call_name = def_ast_name(node.func)
            if call_name in {"eval", "exec"}:
                issues.append(def_issue("PY_DYNAMIC_EXECUTION", "HIGH", def_PARAM_CLASS_HYDRA,
                                        subsystem, path_value, root_value, getattr(node, "lineno", 0),
                                        "動態執行需人工審核", call_name, hydra=True,
                                        suggested_action="改由 allowlisted Registry dispatch。"))
            if call_name in {"sys.path.insert", "sys.path.append"} and "VIA:CONTROLLED_TEMP_SYS_PATH" not in source:
                issues.append(def_issue("PY_GLOBAL_SYS_PATH_MUTATION", "MEDIUM", def_PARAM_CLASS_SYNC,
                                        subsystem, path_value, root_value, getattr(node, "lineno", 0),
                                        "全域 sys.path 寫入", call_name,
                                        suggested_action="改用受控 context manager 或 spec_from_file_location。"))
            if call_name in {"shutil.rmtree", "os.remove", "os.unlink", "Path.unlink"}:
                issues.append(def_issue("PY_DESTRUCTIVE_CALL", "HIGH", def_PARAM_CLASS_HYDRA,
                                        subsystem, path_value, root_value, getattr(node, "lineno", 0),
                                        "直接破壞性檔案操作", call_name, hydra=True,
                                        suggested_action="只允許 run-local allowlist + approval + backup。"))
    asset.hardcoded_paths = sorted(paths)
    if len(paths) >= 3:
        issues.append(def_issue("MULTIPLE_HARDCODED_ROOTS", "HIGH", def_PARAM_CLASS_HYDRA,
                                subsystem, path_value, root_value, 0, "同模組含多個固定根目錄",
                                f"count={len(paths)}", "\n".join(sorted(paths)[:30]), hydra=True,
                                suggested_action="統一交由 Path Authority/manifest。"))
    elif paths:
        issues.append(def_issue("PY_HARDCODED_ABSOLUTE_PATH", "MEDIUM", def_PARAM_CLASS_SEQUENCE,
                                subsystem, path_value, root_value, 0, "固定絕對路徑降低可移植性",
                                f"count={len(paths)}", "\n".join(sorted(paths)[:20]),
                                suggested_action="改由中央 Path Authority 解析。"))

    if path_value.name == "VIA_Runtime_Bridge_All_in_One.py" and re.search(
            r"^def_PARAM_SUPPORTIVE_ROOT\s*=\s*Path\(r?[\"'][A-Za-z]:\\", source, re.M):
        issues.append(def_issue("RUNTIME_STATIC_SUPPORTIVE_ROOT", "MEDIUM", def_PARAM_CLASS_PARALLEL,
                                subsystem, path_value, root_value, 0, "Runtime Bridge 固定 supportive root",
                                "user-specific absolute path", auto_fixable=True,
                                suggested_action="沙盒副本改為 Path(__file__).resolve().parent。"))
    if path_value.name == "VIA_RegistryCore_v1.py":
        registry_governance_region = source.split("# def DATA STRUCTURES", 1)[0]
        if "/mnt/data/VeritasAegisNexus(4).py" in registry_governance_region or "/mnt/data/VeritasCeleritas(4).py" in registry_governance_region:
            issues.append(def_issue("REGISTRY_STATIC_UPLOADED_PATHS", "HIGH", def_PARAM_CLASS_SEQUENCE,
                                    subsystem, path_value, root_value, 0, "Registry 指向暫存路徑/舊檔名",
                                    "legacy /mnt/data paths", auto_fixable=True,
                                    suggested_action="沙盒副本改用自身目錄 + manifest。"))
        if any(token in registry_governance_region for token in ("VeritasAegisNexus(4)", "VeritasCeleritas(4)", "VIA_5D_CodeEngine(3)")):
            issues.append(def_issue("REGISTRY_LEGACY_MODULE_KEYS", "HIGH", def_PARAM_CLASS_SYNC,
                                    subsystem, path_value, root_value, 0, "Registry key 含 Windows 複製尾碼",
                                    "legacy (n) module keys", auto_fixable=True, hydra=True,
                                    suggested_action="移除尾碼，以 hash+alias 保留版本關係。"))
    if path_value.name == "VIA_EnvManager.py" and re.search(r"^def_PARAM_ENABLE_EXEC\s*=\s*True\s*$", source, re.M):
        issues.append(def_issue("ENV_EXECUTION_DEFAULT_ENABLED", "MEDIUM", def_PARAM_CLASS_PARALLEL,
                                subsystem, path_value, root_value, 0, "EnvManager 預設允許命令執行",
                                "def_PARAM_ENABLE_EXEC=True", auto_fixable=True,
                                suggested_action="中央治理與沙盒預設 False。"))
    if "Path.cwd()" in source and path_value.name in {"VIA_EnvManager.py", "VIA_RegistryCore_v1.py"}:
        issues.append(def_issue("OUTPUT_PATH_CWD_DRIFT", "LOW", def_PARAM_CLASS_PARALLEL,
                                subsystem, path_value, root_value, 0, "輸出根依賴目前工作目錄",
                                "Path.cwd() may drift", auto_fixable=True,
                                suggested_action="改由 __file__ 或 CLI 明確傳入。"))

    issues.extend(def_validate_ssot_rules(tree, path_value, root_value, subsystem))
    return asset, issues

# =============================================================================
# def HTML / JS / JSON / POWERSHELL ANALYSIS
# =============================================================================
class def_HTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: Dict[str, List[int]] = defaultdict(list)
        self.handlers: List[Tuple[int, str, str]] = []
        self.scripts: List[Tuple[int, str, str]] = []
        self.passwords: List[int] = []
        self._in_script = False
        self._script_line = 0
        self._script_type = ""
        self._buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        line, _ = self.getpos()
        if attr_map.get("id"):
            self.ids[attr_map["id"]].append(line)
        for key, value in attr_map.items():
            if key.startswith("on"):
                self.handlers.append((line, key, value))
        if tag.lower() == "script":
            self._in_script, self._script_line, self._script_type, self._buffer = True, line, attr_map.get("type", ""), []
        if tag.lower() == "input" and attr_map.get("type", "").lower() == "password":
            self.passwords.append(line)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            self.scripts.append((self._script_line, self._script_type, "".join(self._buffer)))
            self._in_script, self._buffer = False, []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._buffer.append(data)


def def_node_check(source: str) -> Tuple[bool, str]:
    node_cmd = shutil.which("node")
    if not node_cmd:
        return True, "NODE_NOT_AVAILABLE"
    with tempfile.TemporaryDirectory(prefix="via_js_") as temp_dir:
        path_value = Path(temp_dir) / "script.js"
        path_value.write_text(source, encoding="utf-8")
        try:
            result = subprocess.run([node_cmd, "--check", str(path_value)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=30)
            return result.returncode == 0, (result.stdout + "\n" + result.stderr).strip()
        except Exception as exc:
            return False, str(exc)


def def_owned_asset_ids(language: str, source: str) -> List[str]:
    """Extract identity declarations only; references in reports/ledgers are not owners."""
    candidates: List[str] = []
    if language == "JSON":
        try:
            payload = json.loads(source)
            if isinstance(payload, dict):
                for key in ("asset_id", "assetId", "ASSET_ID"):
                    value = payload.get(key)
                    if isinstance(value, str) and def_PARAM_ASSET_ID_RE.fullmatch(value.strip()):
                        candidates.append(value.strip())
        except Exception:
            pass
    elif language == "HTML":
        pattern = r"<meta[^>]+name=[\"'](?:vaos-asset-id|asset-id)[\"'][^>]+content=[\"'](AST-[^\"']+)[\"']"
        for match_value in re.finditer(pattern, source, re.I):
            value = match_value.group(1).strip()
            if def_PARAM_ASSET_ID_RE.fullmatch(value):
                candidates.append(value)
    elif language == "PYTHON":
        declaration_patterns = [
            r"(?m)^\s*(?:__asset_id__|def_PARAM_ASSET_ID|ASSET_ID)\s*(?::[^=]+)?=\s*[\"'](AST-[A-Z0-9-]+)[\"']",
            r"(?im)^\s*#.*?ASSET_ID\s*[:=]\s*(AST-[A-Z0-9-]+)",
        ]
        for pattern in declaration_patterns:
            candidates.extend(match.group(1) for match in re.finditer(pattern, source))
    elif language == "POWERSHELL":
        pattern = r"(?im)^\s*\$(?:def_PARAM_ASSET_ID|AssetId|ASSET_ID)\s*=\s*[\"'](AST-[A-Z0-9-]+)[\"']"
        candidates.extend(match.group(1) for match in re.finditer(pattern, source))
    else:
        pattern = r"(?im)^.{0,30}ASSET_ID\s*[:=]\s*(AST-[A-Z0-9-]+)"
        candidates.extend(match.group(1) for match in re.finditer(pattern, source[:12000]))
    return sorted({value for value in candidates if def_PARAM_ASSET_ID_RE.fullmatch(value)})


def def_base_asset(path_value: Path, root_value: Path, language: str, source: str, encoding: str) -> def_Asset:
    stat_value = path_value.stat()
    version_match = def_PARAM_VERSION_RE.search(source[:12000])
    return def_Asset(str(path_value), def_relative(path_value, root_value), path_value.name,
                     path_value.stem, path_value.suffix.lower(), language,
                     def_subsystem(path_value, source), stat_value.st_size,
                     def_hash_file(path_value),
                     dt.datetime.fromtimestamp(stat_value.st_mtime, dt.timezone.utc).isoformat(),
                     line_count=len(source.splitlines()),
                     asset_ids=def_owned_asset_ids(language, source),
                     version=version_match.group(1) if version_match else "",
                     metadata={"encoding": encoding})


def def_analyze_html(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    source, encoding = def_read(path_value)
    asset = def_base_asset(path_value, root_value, "HTML", source, encoding)
    issues: List[def_Issue] = []
    parser = def_HTMLParser()
    try:
        parser.feed(source)
        parser.close()
        asset.parse_status = "PASS"
    except Exception as exc:
        asset.parse_status = "WARN"
        issues.append(def_issue("HTML_PARSE_ERROR", "HIGH", def_PARAM_CLASS_SEQUENCE,
                                asset.subsystem, path_value, root_value, 0, "HTML 解析失敗", str(exc),
                                suggested_action="修結構後才允許 UI 注入。"))
    for id_value, lines in parser.ids.items():
        if len(lines) > 1:
            issues.append(def_issue("HTML_DUPLICATE_ID", "HIGH", def_PARAM_CLASS_SYNC,
                                    asset.subsystem, path_value, root_value, min(lines), "HTML ID 重複",
                                    f"id={id_value!r}, lines={lines}", hydra=True,
                                    suggested_action="每個 DOM ID 僅保留一個 owner。"))
    scripts = [script for _, type_value, script in parser.scripts
               if type_value.lower() not in {"application/json", "application/ld+json", "text/template"} and script.strip()]
    if scripts:
        ok_value, detail = def_node_check("\n".join(scripts))
        asset.metadata["javascript_check"] = "PASS" if ok_value else "FAIL"
        if not ok_value:
            issues.append(def_issue("JAVASCRIPT_SYNTAX_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                    asset.subsystem, path_value, root_value, parser.scripts[0][0],
                                    "內嵌 JavaScript 語法錯誤", detail,
                                    suggested_action="修 JS 後重跑 UI user-test。"))
    if parser.handlers:
        issues.append(def_issue("HTML_INLINE_EVENT_CONTRACT", "LOW", def_PARAM_CLASS_SYNC,
                                asset.subsystem, path_value, root_value, parser.handlers[0][0],
                                "Inline event 降低契約可追蹤性", f"count={len(parser.handlers)}",
                                suggested_action="逐步改為 data-action + single dispatcher。"))
    password_signal = bool(re.search(r"(?i)(?:default|password|passcode|密碼)[^\r\n]{0,90}(?:via\d{4}|[A-Za-z0-9@#$%]{6,})", source))
    if parser.passwords and password_signal:
        issues.append(def_issue("HTML_CLIENT_SIDE_SECRET", "HIGH", def_PARAM_CLASS_HYDRA,
                                asset.subsystem, path_value, root_value, parser.passwords[0],
                                "前端可見密碼不是授權邊界", "client-side visual lock",
                                hydra=True, suggested_action="視覺鎖只防誤觸；真授權移到本機後端 ACL/token。"))
    if re.search(r"@import\s+url\([^)]*(?:fonts\.googleapis|http)", source, re.I):
        issues.append(def_issue("HTML_EXTERNAL_FONT_DEPENDENCY", "LOW", def_PARAM_CLASS_PARALLEL,
                                asset.subsystem, path_value, root_value, 0, "HTML 離線依賴外部字型",
                                "external font import", suggested_action="保留 system-font fallback。"))
    return asset, issues


def def_analyze_js(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    source, encoding = def_read(path_value)
    asset = def_base_asset(path_value, root_value, def_language(path_value), source, encoding)
    issues: List[def_Issue] = []
    ok_value, detail = def_node_check(source)
    asset.parse_status = "PASS" if ok_value else "FAIL"
    if not ok_value:
        issues.append(def_issue("JAVASCRIPT_SYNTAX_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                asset.subsystem, path_value, root_value, 0, "JavaScript 語法錯誤", detail,
                                suggested_action="修 syntax 後重建 contract。"))
    for match_value in re.finditer(r"\b(eval|Function)\s*\(", source):
        issues.append(def_issue("JS_DYNAMIC_EXECUTION", "HIGH", def_PARAM_CLASS_HYDRA,
                                asset.subsystem, path_value, root_value,
                                source.count("\n", 0, match_value.start()) + 1,
                                "JavaScript 動態執行", match_value.group(0), hydra=True,
                                suggested_action="改為 allowlisted dispatcher。"))
    return asset, issues


def def_analyze_json(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    source, encoding = def_read(path_value)
    asset = def_base_asset(path_value, root_value, def_language(path_value), source, encoding)
    issues: List[def_Issue] = []
    if path_value.suffix.lower() == ".jsonl":
        failed = []
        for line_no, line in enumerate(source.splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:
                failed.append((line_no, str(exc)))
        asset.parse_status = "FAIL" if failed else "PASS"
        for line_no, detail in failed[:20]:
            issues.append(def_issue("JSONL_PARSE_ERROR", "HIGH", def_PARAM_CLASS_SEQUENCE,
                                    asset.subsystem, path_value, root_value, line_no,
                                    "JSONL 列解析失敗", detail,
                                    suggested_action="修復或移至 quarantine ledger。"))
        return asset, issues

    duplicate_keys: List[str] = []
    def def_hook(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicate_keys.append(key)
            result[key] = value
        return result
    try:
        json.loads(source, object_pairs_hook=def_hook)
        asset.parse_status = "PASS"
    except Exception as exc:
        asset.parse_status = "FAIL"
        issues.append(def_issue("JSON_PARSE_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                asset.subsystem, path_value, root_value, getattr(exc, "lineno", 0) or 0,
                                "JSON 解析失敗", str(exc),
                                suggested_action="修復後才允許 Registry/SSOT 讀取。"))
    if duplicate_keys:
        issues.append(def_issue("JSON_DUPLICATE_KEYS", "HIGH", def_PARAM_CLASS_SYNC,
                                asset.subsystem, path_value, root_value, 0,
                                "JSON 重複 key 造成覆蓋", str(sorted(set(duplicate_keys))[:30]),
                                hydra=True, suggested_action="每個 key 僅保留一個 canonical owner。"))
    return asset, issues


def def_ps_ast(path_value: Path) -> Tuple[bool, str]:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        return True, "POWERSHELL_NOT_AVAILABLE"
    escaped = str(path_value).replace("'", "''")
    command = ("$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('" + escaped +
               "',[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e|%{$_.ToString()};exit 2}else{exit 0}")
    try:
        result = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-Command", command],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        return result.returncode == 0, (result.stdout + "\n" + result.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def def_analyze_ps(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    source, encoding = def_read(path_value)
    asset = def_base_asset(path_value, root_value, "POWERSHELL", source, encoding)
    issues: List[def_Issue] = []
    ok_value, detail = def_ps_ast(path_value)
    asset.parse_status = "PASS" if ok_value else "FAIL"
    if not ok_value:
        issues.append(def_issue("POWERSHELL_AST_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                                asset.subsystem, path_value, root_value, 0, "PowerShell AST 失敗", detail,
                                suggested_action="修 AST 後才允許執行。"))
    patterns = [r"\bRemove-Item\b", r"\brm\s+-rf\b", r"\bInvoke-Expression\b|\biex\b",
                r"Set-ExecutionPolicy\s+[^\r\n]*(?:LocalMachine|CurrentUser)"]
    for pattern in patterns:
        for match_value in re.finditer(pattern, source, re.I):
            line = source.count("\n", 0, match_value.start()) + 1
            issues.append(def_issue("POWERSHELL_HIGH_RISK_COMMAND", "HIGH", def_PARAM_CLASS_HYDRA,
                                    asset.subsystem, path_value, root_value, line,
                                    "PowerShell 高風險命令", match_value.group(0), hydra=True,
                                    suggested_action="僅允許 run-local + explicit approval + hash-state-machine。"))
    return asset, issues


def def_analyze_generic(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    source, encoding = def_read(path_value)
    asset = def_base_asset(path_value, root_value, def_language(path_value), source, encoding)
    asset.parse_status = "INDEXED"
    return asset, []


def def_analyze_one(path_value: Path, root_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
    if path_value.stat().st_size > def_PARAM_MAX_TEXT_BYTES:
        source, encoding = def_read(path_value)
        asset = def_base_asset(path_value, root_value, def_language(path_value), source, encoding)
        asset.parse_status = "SKIPPED_SIZE"
        issue = def_issue("ASSET_SIZE_SCAN_LIMIT", "LOW", def_PARAM_CLASS_PARALLEL,
                          asset.subsystem, path_value, root_value, 0, "資產超過深掃上限",
                          f"size={path_value.stat().st_size}", suggested_action="改用分段分析。")
        return asset, [issue]
    suffix = path_value.suffix.lower()
    if suffix == ".py":
        return def_analyze_python(path_value, root_value)
    if suffix in {".html", ".htm"}:
        return def_analyze_html(path_value, root_value)
    if suffix in {".js", ".mjs", ".cjs", ".ts"}:
        return def_analyze_js(path_value, root_value)
    if suffix in {".json", ".jsonl"}:
        return def_analyze_json(path_value, root_value)
    if suffix in {".ps1", ".psm1", ".psd1"}:
        return def_analyze_ps(path_value, root_value)
    return def_analyze_generic(path_value, root_value)

# =============================================================================
# def DEPENDENCY / CONTRACT / HYDRA
# =============================================================================
def def_module_index(assets: Sequence[def_Asset]) -> Dict[str, def_Asset]:
    result: Dict[str, def_Asset] = {}
    for asset in assets:
        if asset.language == "PYTHON":
            result.setdefault(asset.stem, asset)
    return result


def def_edges(assets: Sequence[def_Asset]) -> List[def_Edge]:
    module_index = def_module_index(assets)
    result: List[def_Edge] = []
    seen: Set[Tuple[str, str]] = set()
    for asset in assets:
        if asset.language != "PYTHON":
            continue
        for import_name in asset.imports:
            target = import_name.split(":", 1)[0].split(".", 1)[0]
            if target in module_index and (asset.stem, target) not in seen:
                seen.add((asset.stem, target))
                result.append(def_Edge(asset.stem, target, "PY_IMPORT", "RESOLVED", import_name))
    return result


def def_scc(nodes: Sequence[str], edges: Sequence[def_Edge]) -> List[List[str]]:
    adjacency: Dict[str, List[str]] = defaultdict(list)
    for edge in edges:
        adjacency[edge.source].append(edge.target)
    counter = [0]
    stack: List[str] = []
    on_stack: Set[str] = set()
    indexes: Dict[str, int] = {}
    low: Dict[str, int] = {}
    result: List[List[str]] = []

    def def_visit(node: str) -> None:
        indexes[node] = low[node] = counter[0]
        counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency.get(node, []):
            if target not in indexes:
                def_visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], indexes[target])
        if low[node] == indexes[node]:
            component: List[str] = []
            while stack:
                target = stack.pop()
                on_stack.remove(target)
                component.append(target)
                if target == node:
                    break
            result.append(sorted(component))

    for node in nodes:
        if node not in indexes:
            def_visit(node)
    return result


def def_graph_issues(assets: Sequence[def_Asset], edges: Sequence[def_Edge], root_value: Path) -> List[def_Issue]:
    issues: List[def_Issue] = []
    module_index = def_module_index(assets)
    for component in def_scc(sorted(module_index), edges):
        if len(component) > 1:
            owner = module_index[component[0]]
            issues.append(def_issue("PY_IMPORT_CYCLE", "HIGH", def_PARAM_CLASS_HYDRA,
                                    owner.subsystem, Path(owner.path), root_value, 0,
                                    "Python 模組形成循環依賴", " -> ".join(component + [component[0]]),
                                    hydra=True, suggested_action="用 Interface Contract/Registry 反轉依賴。"))
    return issues


def def_duplicate_issues(assets: Sequence[def_Asset], root_value: Path) -> List[def_Issue]:
    issues: List[def_Issue] = []
    by_stem: Dict[str, List[def_Asset]] = defaultdict(list)
    by_id: Dict[str, List[def_Asset]] = defaultdict(list)
    for asset in assets:
        by_stem[asset.stem.lower()].append(asset)
        for asset_id in asset.asset_ids:
            by_id[asset_id].append(asset)
    for stem, rows in by_stem.items():
        if len(rows) > 1 and len({row.sha256 for row in rows}) > 1:
            owner = rows[0]
            issues.append(def_issue("DUPLICATE_MODULE_STEM_DIFFERENT_HASH", "HIGH", def_PARAM_CLASS_HYDRA,
                                    owner.subsystem, Path(owner.path), root_value, 0,
                                    "同名模組存在不同內容版本",
                                    f"stem={stem}; files={[row.relative_path for row in rows]}",
                                    "\n".join(f"{row.sha256}  {row.relative_path}" for row in rows),
                                    hydra=True, suggested_action="指定 canonical owner；其餘轉 alias/deprecated。"))
    for asset_id, rows in by_id.items():
        if len(rows) > 1 and len({row.sha256 for row in rows}) > 1:
            owner = rows[0]
            issues.append(def_issue("DUPLICATE_ASSET_ID_DIFFERENT_HASH", "CRITICAL", def_PARAM_CLASS_HYDRA,
                                    owner.subsystem, Path(owner.path), root_value, 0,
                                    "同 Asset ID 指向不同內容",
                                    f"asset_id={asset_id}; files={[row.relative_path for row in rows]}",
                                    "\n".join(f"{row.sha256}  {row.relative_path}" for row in rows),
                                    hydra=True, suggested_action="Fail-closed；建立新版本 ID/hash-chain。"))
    return issues


def def_contracts(assets: Sequence[def_Asset]) -> Dict[str, Any]:
    module_index = def_module_index(assets)
    modules = {
        name: {"path": asset.relative_path, "subsystem": asset.subsystem,
               "exports": asset.exports, "functions": {row["name"]: row for row in asset.contracts},
               "sha256": asset.sha256}
        for name, asset in sorted(module_index.items())
    }
    checks = []
    for module_name, expected in def_PARAM_EXPECTED_EXPORTS.items():
        asset = module_index.get(module_name)
        missing = list(expected) if asset is None else [name for name in expected if name not in asset.exports]
        checks.append({"module": module_name,
                       "status": "MISSING_MODULE" if asset is None else "MISSING_EXPORT" if missing else "PASS",
                       "expected": expected, "missing": missing,
                       "path": asset.relative_path if asset else ""})
    return {"modules": modules, "checks": checks}


def def_contract_issues(contracts: Dict[str, Any], assets: Sequence[def_Asset], root_value: Path) -> List[def_Issue]:
    module_index = def_module_index(assets)
    fallback = next(iter(module_index.values()), None)
    issues: List[def_Issue] = []
    for check in contracts.get("checks", []):
        if check.get("status") == "PASS":
            continue
        asset = module_index.get(check.get("module")) or fallback
        if not asset:
            continue
        severity = "CRITICAL" if check.get("status") == "MISSING_MODULE" else "HIGH"
        issues.append(def_issue("INTERFACE_CONTRACT_GAP", severity, def_PARAM_CLASS_SYNC,
                                asset.subsystem, Path(asset.path), root_value, 0,
                                "核心介面契約缺口", json.dumps(check, ensure_ascii=False),
                                suggested_action="補 export 或建立 compatibility adapter 後再啟用下游。"))
    return issues


def def_fix_order(assets: Sequence[def_Asset], edges: Sequence[def_Edge]) -> List[Dict[str, Any]]:
    nodes = sorted(def_module_index(assets))
    incoming = {node: 0 for node in nodes}
    dependents: Dict[str, List[str]] = defaultdict(list)
    for edge in edges:
        if edge.source != edge.target:
            incoming[edge.source] = incoming.get(edge.source, 0) + 1
            dependents[edge.target].append(edge.source)
    queue_value = deque(sorted(node for node, count in incoming.items() if count == 0))
    ordered: List[str] = []
    while queue_value:
        node = queue_value.popleft()
        ordered.append(node)
        for dependent in sorted(dependents.get(node, [])):
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                queue_value.append(dependent)
    remaining = sorted(set(nodes) - set(ordered))
    return [{"order": index, "module": node,
             "status": "ACYCLIC" if node in ordered else "CYCLE_REVIEW",
             "reason": "dependency-first" if node in ordered else "Hydra/cycle review"}
            for index, node in enumerate(ordered + remaining, 1)]


def def_summary(assets: Sequence[def_Asset], issues: Sequence[def_Issue]) -> Dict[str, Any]:
    severity = Counter(issue.severity for issue in issues)
    parse = Counter(asset.parse_status for asset in assets)
    if severity["CRITICAL"]:
        gate = "RED_FAIL_CLOSED"
    elif severity["HIGH"]:
        gate = "YELLOW_HIGH_RISK_REVIEW"
    elif severity["MEDIUM"]:
        gate = "YELLOW_REPAIRABLE"
    else:
        gate = "GREEN_READY"
    return {"assets_total": len(assets), "parse_status": dict(parse), "issues_total": len(issues),
            "severity": {name: severity[name] for name in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]},
            "hydra_count": sum(issue.hydra for issue in issues),
            "auto_fixable_count": sum(issue.auto_fixable for issue in issues),
            "risk_score": sum(def_PARAM_WEIGHT.get(issue.severity, 1) for issue in issues),
            "gate": gate}


def def_subsystem_health(assets: Sequence[def_Asset], issues: Sequence[def_Issue]) -> Dict[str, Any]:
    asset_count = Counter(asset.subsystem for asset in assets)
    issue_map: Dict[str, List[def_Issue]] = defaultdict(list)
    for issue in issues:
        issue_map[issue.subsystem].append(issue)
    result = {}
    for subsystem in sorted(set(asset_count) | set(issue_map)):
        rows = issue_map[subsystem]
        highest = next((severity for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
                        if any(row.severity == severity for row in rows)), "INFO")
        result[subsystem] = {"assets": asset_count[subsystem], "issues": len(rows),
                             "critical": sum(row.severity == "CRITICAL" for row in rows),
                             "high": sum(row.severity == "HIGH" for row in rows),
                             "hydra": sum(row.hydra for row in rows),
                             "ryg": def_PARAM_RYG[highest]}
    return result


def def_analyze(root_value: Path, output_root: Optional[Path], profile: def_Profile) -> def_Snapshot:
    paths = def_files(root_value, output_root)
    def def_worker(path_value: Path) -> Tuple[def_Asset, List[def_Issue]]:
        try:
            return def_analyze_one(path_value, root_value)
        except Exception as exc:
            source = ""
            with contextlib.suppress(Exception):
                source, _ = def_read(path_value)
            stat_value = path_value.stat()
            asset = def_Asset(str(path_value), def_relative(path_value, root_value), path_value.name,
                              path_value.stem, path_value.suffix.lower(), def_language(path_value),
                              def_subsystem(path_value, source), stat_value.st_size, def_hash_file(path_value),
                              dt.datetime.fromtimestamp(stat_value.st_mtime, dt.timezone.utc).isoformat(),
                              "ANALYZER_ERROR", len(source.splitlines()))
            issue = def_issue("ANALYZER_INTERNAL_ERROR", "CRITICAL", def_PARAM_CLASS_SEQUENCE,
                              asset.subsystem, path_value, root_value, 0, "分析器內部錯誤", str(exc),
                              traceback.format_exc(), suggested_action="隔離資產並修分析器。")
            return asset, [issue]
    if profile.workers <= 1:
        result_rows = [def_worker(path_value) for path_value in paths]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=profile.workers) as executor:
            result_rows = list(executor.map(def_worker, paths))
    assets: List[def_Asset] = []
    issues: List[def_Issue] = []
    for asset, issue_rows in result_rows:
        assets.append(asset)
        issues.extend(issue_rows)
    edges = def_edges(assets)
    issues.extend(def_graph_issues(assets, edges, root_value))
    issues.extend(def_duplicate_issues(assets, root_value))
    contracts = def_contracts(assets)
    issues.extend(def_contract_issues(contracts, assets, root_value))
    dedup = {issue.issue_id: issue for issue in issues}
    issues = sorted(dedup.values(), key=lambda row: (-def_PARAM_WEIGHT[row.severity], row.relative_path, row.line, row.code))
    assets = sorted(assets, key=lambda row: row.relative_path)
    module_index = def_module_index(assets)
    expected, present = set(def_PARAM_CORE_MODULES), set(module_index)
    ssot = {"expected_core_modules": sorted(expected), "present_core_modules": sorted(expected & present),
            "missing_core_modules": sorted(expected - present),
            "registry_legacy_key_issue_count": sum(issue.code == "REGISTRY_LEGACY_MODULE_KEYS" for issue in issues),
            "ssot_rule_contradiction_count": sum(issue.code == "SSOT_RULE_EXAMPLE_CONTRADICTION" for issue in issues)}
    ssot["alignment_status"] = "PASS" if not ssot["missing_core_modules"] and not ssot["registry_legacy_key_issue_count"] and not ssot["ssot_rule_contradiction_count"] else "REVIEW"
    languages = Counter(asset.language for asset in assets)
    quantities = {"asset_count": len(assets), "language_count": dict(languages),
                  "unique_hash_count": len({asset.sha256 for asset in assets}),
                  "duplicate_hash_file_count": len(assets) - len({asset.sha256 for asset in assets}),
                  "core_expected": len(expected), "core_present": len(expected & present),
                  "parse_fail_count": sum(asset.parse_status == "FAIL" for asset in assets),
                  "issue_count": len(issues)}
    return def_Snapshot(str(root_value), def_now(), [asdict(row) for row in assets],
                        [asdict(row) for row in issues], [asdict(row) for row in edges],
                        contracts, ssot, quantities, def_subsystem_health(assets, issues),
                        def_fix_order(assets, edges), def_summary(assets, issues))


# =============================================================================
# def SANDBOX REPAIR
# =============================================================================
def def_copy_sandbox(canonical_root: Path, sandbox_root: Path, output_root: Path) -> List[def_Action]:
    actions: List[def_Action] = []
    sandbox_root.mkdir(parents=True, exist_ok=True)
    for source_path in def_files(canonical_root, output_root):
        relative = Path(def_relative(source_path, canonical_root))
        target = sandbox_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        before = def_hash_file(source_path)
        if target.exists() and def_hash_file(target) == before:
            status = "SKIP_IDENTICAL"
        else:
            shutil.copy2(source_path, target)
            status = "COPIED"
        actions.append(def_Action("ACT-" + def_short("copy|" + str(relative)), 1, len(actions) + 1,
                                  "SANDBOX_MIRROR_COPY", def_PARAM_CLASS_PARALLEL,
                                  str(source_path), str(target), status,
                                  "Canonical read-only mirror", before, def_hash_file(target)))
    return actions


def def_patch(path_value: Path, transform: Any, code: str, round_no: int, order_no: int, detail: str) -> def_Action:
    if not path_value.exists():
        return def_Action("ACT-" + def_short(code + "|missing"), round_no, order_no, code,
                          def_PARAM_CLASS_SEQUENCE, str(path_value), str(path_value), "SKIP_MISSING", detail)
    original, _ = def_read(path_value)
    proposed, changed = transform(original)
    before = def_hash_text(original)
    if changed and proposed != original:
        backup = path_value.with_suffix(path_value.suffix + f".before_{code}.bak")
        if not backup.exists():
            def_write_text(backup, original)
        def_write_text(path_value, proposed)
        status = "APPLIED_SANDBOX_ONLY"
    else:
        status = "SKIP_ALREADY_COMPLIANT"
    return def_Action("ACT-" + def_short(code + "|" + str(path_value)), round_no, order_no, code,
                      def_PARAM_CLASS_SEQUENCE, str(path_value), str(path_value), status, detail,
                      before, def_hash_file(path_value), False, False)


def def_transform_runtime(source: str) -> Tuple[str, bool]:
    result, count1 = re.subn(r"^def_PARAM_SUPPORTIVE_ROOT\s*=\s*Path\([^\n]+\)\s*$",
                             'def_PARAM_SUPPORTIVE_ROOT = Path(__file__).resolve().parent', source, count=1, flags=re.M)
    count = count1
    for name in ["def_PARAM_ENABLE_BOOTSTRAP_SCAN", "def_PARAM_ENABLE_CELERITAS_INIT", "def_PARAM_ENABLE_ENV_GOVERNANCE_CHECK"]:
        result, c = re.subn(rf"^{name}\s*=\s*True\s*$", f"{name} = False", result, count=1, flags=re.M)
        count += c
    return result, count > 0


def def_transform_registry(source: str) -> Tuple[str, bool]:
    result, count = source, 0
    replacements = [
        (r"^def_PARAM_ENABLE_SUBPROCESS_EXECUTION\s*=\s*True\s*$", "def_PARAM_ENABLE_SUBPROCESS_EXECUTION = False"),
        (r"^def_PARAM_BASE_DIR\s*=\s*Path\.cwd\(\)\s*$", "def_PARAM_BASE_DIR = Path(__file__).resolve().parent"),
        (r"^def_PARAM_PATH_VERITAS_AEGIS\s*=.*$", 'def_PARAM_PATH_VERITAS_AEGIS = def_PARAM_BASE_DIR / "VeritasAegisNexus.py"'),
        (r"^def_PARAM_PATH_VERITAS_CELERITAS\s*=.*$", 'def_PARAM_PATH_VERITAS_CELERITAS = def_PARAM_BASE_DIR / "VeritasCeleritas.py"'),
        (r"^def_PARAM_PATH_VIA_5D\s*=.*$", 'def_PARAM_PATH_VIA_5D = def_PARAM_BASE_DIR / "VIA_5D_CodeEngine.py"'),
        (r"^def_PARAM_PATH_ENV_DISPATCH\s*=.*$", 'def_PARAM_PATH_ENV_DISPATCH = def_PARAM_BASE_DIR / "VIA_EnvDispatch.py"'),
        (r"^def_PARAM_PATH_ENV_ROUTER\s*=.*$", 'def_PARAM_PATH_ENV_ROUTER = def_PARAM_BASE_DIR / "VIA_EnvRouter.py"'),
        (r"^def_PARAM_PATH_MANIFEST\s*=.*$", 'def_PARAM_PATH_MANIFEST = def_PARAM_BASE_DIR / "via_manifest.json"'),
    ]
    for pattern, replacement in replacements:
        result, c = re.subn(pattern, replacement, result, count=1, flags=re.M)
        count += c
    marker = "# def DATA STRUCTURES"
    if marker in result:
        head, tail = result.split(marker, 1)
        for old, new in [("VeritasAegisNexus(4)", "VeritasAegisNexus"),
                         ("VeritasCeleritas(4)", "VeritasCeleritas"),
                         ("VIA_5D_CodeEngine(3)", "VIA_5D_CodeEngine")]:
            if old in head:
                head, count = head.replace(old, new), count + 1
        result = head + marker + tail
    return result, count > 0


def def_transform_env(source: str) -> Tuple[str, bool]:
    result, c1 = re.subn(r"^def_PARAM_ENABLE_EXEC\s*=\s*True\s*$", "def_PARAM_ENABLE_EXEC = False", source, count=1, flags=re.M)
    result, c2 = re.subn(r"^def_PARAM_OUTPUT_DIR\s*=\s*Path\.cwd\(\)\s*/\s*[\"']_via_envmanager_output[\"']\s*$",
                         'def_PARAM_OUTPUT_DIR = Path(__file__).resolve().parent / "_via_envmanager_output"', result, count=1, flags=re.M)
    return result, (c1 + c2) > 0


def def_find_asset_path(snapshot: def_Snapshot, stem_value: str, root_value: Path) -> Optional[Path]:
    candidates = [row for row in snapshot.assets if str(row.get("stem", "")).lower() == stem_value.lower()]
    if not candidates:
        return None
    candidates.sort(key=lambda row: (0 if "/" not in str(row.get("relative_path", "")) else 1,
                                     len(str(row.get("relative_path", ""))),
                                     str(row.get("relative_path", "")).lower()))
    return root_value / str(candidates[0].get("relative_path", ""))


def def_generate_manifest(snapshot: def_Snapshot, sandbox_root: Path, round_no: int, order_no: int) -> def_Action:
    target = sandbox_root / "VIA_Adaptive_Governance_Manifest_v0100.json"
    before = def_hash_file(target) if target.exists() else ""
    hierarchy: Dict[str, Dict[str, Any]] = {}
    for row in snapshot.assets:
        subsystem = str(row.get("subsystem", "GENERAL"))
        language = str(row.get("language", "OTHER"))
        bucket = hierarchy.setdefault(subsystem, {"asset_count": 0, "languages": {}, "assets": []})
        bucket["asset_count"] += 1
        bucket["languages"][language] = int(bucket["languages"].get(language, 0)) + 1
        bucket["assets"].append({
            "relative_path": row.get("relative_path"),
            "stem": row.get("stem"),
            "language": language,
            "sha256": row.get("sha256"),
            "parse_status": row.get("parse_status"),
            "exports": row.get("exports", []),
            "imports": row.get("imports", []),
        })
    payload = {
        "schema": "VIA_ADAPTIVE_GOVERNANCE_MANIFEST/1.0",
        "engine": def_PARAM_ENGINE,
        "engine_version": def_PARAM_VERSION,
        "asset_id": def_PARAM_GENERATED_ASSET_IDS["manifest"],
        "generator_asset_id": def_PARAM_ASSET_ID,
        "generated_at_utc": def_now(),
        "round": round_no,
        "root": snapshot.root,
        "policy": {
            "canonical_mutation": False,
            "sandbox_only_repair": True,
            "append_only_evidence": True,
            "hydra_nodes": "REVIEW_ONLY",
            "max_rounds": def_PARAM_MAX_ROUNDS,
        },
        "accelerators": def_PARAM_ACCELERATORS,
        "resource_profile": {},
        "summary": snapshot.summary,
        "quantities": snapshot.quantities,
        "ssot": snapshot.ssot,
        "subsystem_health": snapshot.subsystem_health,
        "fix_order": snapshot.fix_order,
        "dependency_edges": snapshot.dependencies,
        "contract_checks": snapshot.contracts.get("checks", []),
        "hierarchy": hierarchy,
    }
    def_write_json(target, payload)
    return def_Action("ACT-" + def_short("manifest|" + str(target)), round_no, order_no,
                      "GENERATE_ADAPTIVE_MANIFEST", def_PARAM_CLASS_SYNC,
                      snapshot.root, str(target), "GENERATED",
                      "向下治理階層、契約、依賴與健康狀態的單一 manifest",
                      before, def_hash_file(target), False, False)


def def_generate_ssot_overlay(snapshot: def_Snapshot, sandbox_root: Path, round_no: int, order_no: int) -> def_Action:
    target = sandbox_root / "VIA_Adaptive_SSOT_Overlay_v0100.json"
    before = def_hash_file(target) if target.exists() else ""
    module_rows: Dict[str, Dict[str, Any]] = {}
    for row in snapshot.assets:
        stem = str(row.get("stem", ""))
        if stem in def_PARAM_CORE_MODULES:
            module_rows[stem] = {
                "canonical_candidate": row.get("relative_path"),
                "sha256": row.get("sha256"),
                "parse_status": row.get("parse_status"),
                "exports": row.get("exports", []),
            }
    unresolved = [row for row in snapshot.issues if bool(row.get("hydra")) or
                  str(row.get("code", "")).startswith("SSOT_")]
    payload = {
        "schema": "VIA_SSOT_OVERLAY/1.0",
        "asset_id": def_PARAM_GENERATED_ASSET_IDS["ssot_overlay"],
        "generated_at_utc": def_now(),
        "authority": "OVERLAY_ONLY_NO_CANONICAL_MUTATION",
        "base_root": snapshot.root,
        "alignment_status": snapshot.ssot.get("alignment_status"),
        "core_module_owners": module_rows,
        "module_aliases": {
            "VeritasAegisNexus(4)": "VeritasAegisNexus",
            "VeritasCeleritas(4)": "VeritasCeleritas",
            "VIA_5D_CodeEngine(3)": "VIA_5D_CodeEngine",
            "VIA_RuntimeBridge_AllInOne": "VIA_Runtime_Bridge_All_in_One",
        },
        "governance_rules": {
            "path_resolution": "manifest_then_local_root_then_explicit_override",
            "dependency_activation": "dependency_first_fail_closed",
            "interface_resolution": "contract_bridge_only",
            "duplicate_identity": "canonical_owner_or_alias",
            "hydra_repair": "manual_approval_required",
        },
        "unresolved_review_items": [{
            "issue_id": row.get("issue_id"),
            "code": row.get("code"),
            "severity": row.get("severity"),
            "relative_path": row.get("relative_path"),
            "detail": row.get("detail"),
            "suggested_action": row.get("suggested_action"),
        } for row in unresolved],
    }
    def_write_json(target, payload)
    return def_Action("ACT-" + def_short("ssot-overlay|" + str(target)), round_no, order_no,
                      "GENERATE_SSOT_OVERLAY", def_PARAM_CLASS_SYNC,
                      snapshot.root, str(target), "GENERATED",
                      "以 overlay 對齊 canonical owner/alias；不覆寫 VIA_SSOT_Unified",
                      before, def_hash_file(target), False, False)


def def_generate_contract_json(snapshot: def_Snapshot, sandbox_root: Path, round_no: int, order_no: int) -> def_Action:
    target = sandbox_root / "VIA_Interface_Contract_SSOT_v0100.json"
    before = def_hash_file(target) if target.exists() else ""
    modules = snapshot.contracts.get("modules", {})
    consumers: Dict[str, List[str]] = defaultdict(list)
    for edge in snapshot.dependencies:
        if edge.get("status") == "RESOLVED":
            consumers[str(edge.get("target"))].append(str(edge.get("source")))
    payload = {
        "schema": "VIA_INTERFACE_CONTRACT/1.0",
        "asset_id": def_PARAM_GENERATED_ASSET_IDS["contract_ssot"],
        "generated_at_utc": def_now(),
        "policy": "SCHEMA_FIRST_LAZY_IMPORT_FAIL_CLOSED",
        "modules": {},
        "checks": snapshot.contracts.get("checks", []),
    }
    for module_name, module_row in sorted(modules.items()):
        payload["modules"][module_name] = {
            **module_row,
            "consumers": sorted(set(consumers.get(module_name, []))),
            "required_exports": def_PARAM_EXPECTED_EXPORTS.get(module_name, []),
            "activation_gate": "PASS" if all(name in module_row.get("exports", [])
                                                 for name in def_PARAM_EXPECTED_EXPORTS.get(module_name, [])) else "REVIEW",
        }
    def_write_json(target, payload)
    return def_Action("ACT-" + def_short("contract-json|" + str(target)), round_no, order_no,
                      "GENERATE_INTERFACE_CONTRACT_SSOT", def_PARAM_CLASS_SYNC,
                      snapshot.root, str(target), "GENERATED",
                      "函式簽名、export、consumer 與 activation gate 契約",
                      before, def_hash_file(target), False, False)


def def_generate_path_registry(sandbox_root: Path, round_no: int, order_no: int) -> def_Action:
    target = sandbox_root / "VIA_AdaptivePathRegistry_v0100.py"
    before = def_hash_file(target) if target.exists() else ""
    source = (f'# ASSET_ID: {def_PARAM_GENERATED_ASSET_IDS["path_registry"]}\n' + '''from __future__ import annotations

"""VIA 自適應本機路徑註冊器；不修改 sys.path，僅回傳可驗證路徑。"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def_PARAM_ROOT = Path(__file__).resolve().parent
def_PARAM_MANIFEST = def_PARAM_ROOT / "VIA_Adaptive_Governance_Manifest_v0100.json"
def_PARAM_ALIASES = {
    "VeritasAegisNexus(4)": "VeritasAegisNexus",
    "VeritasCeleritas(4)": "VeritasCeleritas",
    "VIA_5D_CodeEngine(3)": "VIA_5D_CodeEngine",
    "VIA_RuntimeBridge_AllInOne": "VIA_Runtime_Bridge_All_in_One",
}


def def_read_manifest() -> Dict:
    try:
        return json.loads(def_PARAM_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def def_normalize_module_name(module_name: str) -> str:
    return def_PARAM_ALIASES.get(module_name, module_name)


def def_candidates(module_name: str, explicit_root: str = "") -> List[Path]:
    normalized = def_normalize_module_name(module_name)
    roots = [Path(explicit_root)] if explicit_root else []
    roots.extend([def_PARAM_ROOT, def_PARAM_ROOT / "supportive modules", def_PARAM_ROOT / "supportive_module"])
    manifest = def_read_manifest()
    for subsystem in manifest.get("hierarchy", {}).values():
        for row in subsystem.get("assets", []):
            if row.get("stem") == normalized and row.get("relative_path"):
                roots.append(def_PARAM_ROOT / Path(row["relative_path"]).parent)
    output: List[Path] = []
    for root in roots:
        path_value = root / f"{normalized}.py"
        if path_value not in output:
            output.append(path_value)
    return output


def def_resolve(module_name: str, explicit_root: str = "") -> Optional[Path]:
    for path_value in def_candidates(module_name, explicit_root):
        if path_value.is_file():
            return path_value.resolve()
    return None


def def_status(module_names: Optional[List[str]] = None) -> Dict:
    names = module_names or [
        "VIA_Panorama_AST_RuntimeInjector", "VIA_Runtime_Bridge_All_in_One",
        "VIA_SSOT_Unified", "VIA_EnvManager", "VIA_RegistryCore_v1",
        "VeritasAegisNexus", "VeritasCeleritas",
    ]
    return {name: str(def_resolve(name) or "") for name in names}
''')
    def_write_text(target, source)
    return def_Action("ACT-" + def_short("path-registry|" + str(target)), round_no, order_no,
                      "GENERATE_ADAPTIVE_PATH_REGISTRY", def_PARAM_CLASS_SEQUENCE,
                      str(sandbox_root), str(target), "GENERATED",
                      "動態根目錄 + alias + manifest 解析，避免固定 C:/mnt 路徑",
                      before, def_hash_file(target), False, False)


def def_generate_contract_bridge(snapshot: def_Snapshot, sandbox_root: Path, round_no: int, order_no: int) -> def_Action:
    target = sandbox_root / "VIA_AdaptiveContractBridge_v0100.py"
    before = def_hash_file(target) if target.exists() else ""
    expected_literal = repr(def_PARAM_EXPECTED_EXPORTS)
    source = f'''# ASSET_ID: {def_PARAM_GENERATED_ASSET_IDS["contract_bridge"]}
from __future__ import annotations

"""VIA 契約優先的 lazy bridge；預設只做 AST 驗證，明確呼叫才載入模組。"""

import ast
import contextlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from VIA_AdaptivePathRegistry_v0100 import def_resolve, def_status as def_path_status


def_PARAM_EXPECTED_EXPORTS = {expected_literal}
def_PARAM_LOADED: Dict[str, Any] = {{}}
def_PARAM_ERRORS: Dict[str, str] = {{}}


# VIA:CONTROLLED_TEMP_SYS_PATH — scoped insertion, always removed in finally.
@contextlib.contextmanager
def def_temporary_sys_path(path_value: Path) -> Iterator[None]:
    root = str(path_value.resolve())
    inserted = root not in sys.path
    if inserted:
        sys.path.insert(0, root)
    try:
        yield
    finally:
        if inserted:
            with contextlib.suppress(ValueError):
                sys.path.remove(root)


def def_ast_exports(path_value: Path) -> List[str]:
    try:
        tree = ast.parse(path_value.read_text(encoding="utf-8", errors="replace"), filename=str(path_value))
        return sorted({{node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}})
    except Exception:
        return []


def def_validate_contracts() -> Dict[str, Any]:
    rows = []
    for module_name, expected in def_PARAM_EXPECTED_EXPORTS.items():
        path_value = def_resolve(module_name)
        exports = def_ast_exports(path_value) if path_value else []
        missing = [name for name in expected if name not in exports]
        rows.append({{
            "module": module_name,
            "path": str(path_value or ""),
            "expected": expected,
            "missing": missing,
            "status": "PASS" if path_value and not missing else "REVIEW",
        }})
    return {{"ok": all(row["status"] == "PASS" for row in rows), "rows": rows}}


def def_lazy_load(module_name: str, explicit_root: str = "") -> Any:
    if module_name in def_PARAM_LOADED:
        return def_PARAM_LOADED[module_name]
    path_value = def_resolve(module_name, explicit_root)
    if path_value is None:
        def_PARAM_ERRORS[module_name] = "MODULE_PATH_NOT_FOUND"
        return None
    runtime_name = f"via_adaptive_{{module_name}}_{{abs(hash(str(path_value)))}}"
    try:
        spec_value = importlib.util.spec_from_file_location(runtime_name, str(path_value))
        if spec_value is None or spec_value.loader is None:
            raise RuntimeError("SPEC_OR_LOADER_MISSING")
        module_obj = importlib.util.module_from_spec(spec_value)
        sys.modules[runtime_name] = module_obj
        with def_temporary_sys_path(path_value.parent):
            spec_value.loader.exec_module(module_obj)
        def_PARAM_LOADED[module_name] = module_obj
        return module_obj
    except Exception as exc:
        def_PARAM_ERRORS[module_name] = f"{{type(exc).__name__}}: {{exc}}\\n{{traceback.format_exc()}}"
        sys.modules.pop(runtime_name, None)
        return None


def def_resolve_callable(module_name: str, callable_name: str) -> Dict[str, Any]:
    expected = def_PARAM_EXPECTED_EXPORTS.get(module_name, [])
    if expected and callable_name not in expected:
        return {{"ok": False, "error": "CALLABLE_NOT_ALLOWLISTED", "module": module_name, "callable": callable_name}}
    module_obj = def_lazy_load(module_name)
    if module_obj is None:
        return {{"ok": False, "error": "MODULE_LOAD_FAILED", "detail": def_PARAM_ERRORS.get(module_name, "")}}
    callable_obj = getattr(module_obj, callable_name, None)
    if not callable(callable_obj):
        return {{"ok": False, "error": "CALLABLE_NOT_FOUND", "module": module_name, "callable": callable_name}}
    return {{"ok": True, "module": module_name, "callable": callable_name, "object": callable_obj}}


def def_call(module_name: str, callable_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    resolved = def_resolve_callable(module_name, callable_name)
    if not resolved.get("ok"):
        return resolved
    try:
        result = resolved["object"](*args, **kwargs)
        return {{"ok": True, "module": module_name, "callable": callable_name, "result": result}}
    except Exception as exc:
        return {{"ok": False, "module": module_name, "callable": callable_name,
                 "error": str(exc), "traceback": traceback.format_exc()}}


def def_status() -> Dict[str, Any]:
    return {{
        "paths": def_path_status(),
        "contracts": def_validate_contracts(),
        "loaded": sorted(def_PARAM_LOADED),
        "errors": dict(def_PARAM_ERRORS),
    }}


def def_run_self_tests() -> Dict[str, Any]:
    contract_result = def_validate_contracts()
    path_result = def_path_status()
    return {{
        "ok": bool(path_result) and isinstance(contract_result.get("rows"), list),
        "contract_gate": contract_result.get("ok"),
        "path_count": sum(bool(value) for value in path_result.values()),
        "contract_rows": contract_result.get("rows", []),
    }}


if __name__ == "__main__":
    print(json.dumps(def_run_self_tests(), ensure_ascii=False, indent=2, default=str))
'''
    def_write_text(target, source)
    return def_Action("ACT-" + def_short("contract-bridge|" + str(target)), round_no, order_no,
                      "GENERATE_ADAPTIVE_CONTRACT_BRIDGE", def_PARAM_CLASS_SEQUENCE,
                      str(sandbox_root), str(target), "GENERATED",
                      "allowlist + AST contract preflight + lazy import + temporary path scope",
                      before, def_hash_file(target), False, False)


def def_generate_activation_config(snapshot: def_Snapshot, sandbox_root: Path, round_no: int, order_no: int) -> def_Action:
    target = sandbox_root / "VIA_Adaptive_Activation_Config_v0100.json"
    before = def_hash_file(target) if target.exists() else ""
    payload = {
        "schema": "VIA_ADAPTIVE_ACTIVATION/1.0",
        "asset_id": def_PARAM_GENERATED_ASSET_IDS["activation_config"],
        "generated_at_utc": def_now(),
        "default_mode": "SANDBOX_REVIEW",
        "canonical_mutation": False,
        "subprocess_execution": False,
        "network_execution": False,
        "auto_install": False,
        "hydra_auto_repair": False,
        "required_gates": {
            "python_compile": "PASS",
            "json_parse": "PASS",
            "contract_validation": "PASS_OR_REVIEW_WITH_ADAPTER",
            "ssot_alignment": snapshot.ssot.get("alignment_status"),
            "critical_issues": 0,
        },
        "activation_order": [row.get("module") for row in snapshot.fix_order],
        "blocked_issue_ids": [row.get("issue_id") for row in snapshot.issues
                              if row.get("hydra") or row.get("severity") == "CRITICAL"],
    }
    def_write_json(target, payload)
    return def_Action("ACT-" + def_short("activation-config|" + str(target)), round_no, order_no,
                      "GENERATE_ACTIVATION_CONFIG", def_PARAM_CLASS_SYNC,
                      snapshot.root, str(target), "GENERATED",
                      "Fail-closed sandbox activation policy",
                      before, def_hash_file(target), False, False)


# =============================================================================
# def REPAIR ROUNDS
# =============================================================================
def def_round1_comprehensive(canonical_snapshot: def_Snapshot, canonical_root: Path,
                             sandbox_root: Path, run_dir: Path, apply_safe_fixes: bool) -> List[def_Action]:
    actions = def_copy_sandbox(canonical_root, sandbox_root, run_dir)
    if not apply_safe_fixes:
        actions.append(def_Action("ACT-" + def_short("round1-preview"), 1, len(actions) + 1,
                                  "ROUND1_PREVIEW_ONLY", def_PARAM_CLASS_PARALLEL,
                                  str(canonical_root), str(sandbox_root), "SKIPPED_BY_POLICY",
                                  "--apply-safe-fixes 未啟用；僅建立等內容沙盒鏡像"))
        return actions
    order = len(actions) + 1
    patch_specs = [
        ("VIA_Runtime_Bridge_All_in_One", def_transform_runtime, "PATCH_RUNTIME_DYNAMIC_ROOT",
         "固定 supportive root 改本檔目錄；重型 bootstrap 預設關閉"),
        ("VIA_RegistryCore_v1", def_transform_registry, "PATCH_REGISTRY_PATH_AND_EXEC_GATE",
         "舊版帶括號名稱轉 alias；路徑本地化；subprocess 預設停用"),
        ("VIA_EnvManager", def_transform_env, "PATCH_ENVMANAGER_EXEC_AND_OUTPUT_GATE",
         "環境執行預設停用；輸出固定至模組旁 run-local 目錄"),
    ]
    for stem, transform, code, detail in patch_specs:
        source_path = def_find_asset_path(canonical_snapshot, stem, canonical_root)
        target_path = sandbox_root / def_relative(source_path, canonical_root) if source_path else sandbox_root / f"{stem}.py"
        actions.append(def_patch(target_path, transform, code, 1, order, detail))
        order += 1
    return actions


def def_round2_sequential(snapshot: def_Snapshot, sandbox_root: Path) -> List[def_Action]:
    actions: List[def_Action] = []
    generators = [
        def_generate_manifest,
        def_generate_ssot_overlay,
        def_generate_contract_json,
    ]
    for generator in generators:
        actions.append(generator(snapshot, sandbox_root, 2, len(actions) + 1))
    actions.append(def_generate_path_registry(sandbox_root, 2, len(actions) + 1))
    actions.append(def_generate_contract_bridge(snapshot, sandbox_root, 2, len(actions) + 1))
    actions.append(def_generate_activation_config(snapshot, sandbox_root, 2, len(actions) + 1))
    return actions


# =============================================================================
# def VALIDATION / SANDBOX ACTIVATION
# =============================================================================
def def_run_command(command: List[str], cwd: Path, timeout: int = 120,
                    extra_env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    environment = dict(os.environ)
    environment.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "VIA_ACCEL_MODE": "safe",
        "VIA_CANONICAL_MUTATION": "0",
        "VIA_SANDBOX_MODE": "1",
    })
    if extra_env:
        environment.update(extra_env)
    try:
        completed = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=timeout,
                                   env=environment)
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "command": command,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "returncode": -2, "command": command,
                "stdout": str(exc.stdout or "")[-12000:], "stderr": "TIMEOUT"}
    except Exception as exc:
        return {"ok": False, "returncode": -1, "command": command,
                "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def def_validate_python_syntax(sandbox_root: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for path_value in sorted(sandbox_root.rglob("*.py"), key=lambda row: str(row).lower()):
        if def_ignore(path_value):
            continue
        try:
            source, _ = def_read(path_value)
            tree = ast.parse(source, filename=str(path_value))
            compile(tree, str(path_value), "exec")
            rows.append({"path": def_relative(path_value, sandbox_root), "status": "PASS", "detail": "AST+compile"})
        except Exception as exc:
            rows.append({"path": def_relative(path_value, sandbox_root), "status": "FAIL", "detail": str(exc)})
    return {"ok": bool(rows) and all(row["status"] == "PASS" for row in rows),
            "total": len(rows), "passed": sum(row["status"] == "PASS" for row in rows),
            "failed": sum(row["status"] == "FAIL" for row in rows), "rows": rows}


def def_validate_json_files(sandbox_root: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for path_value in sorted(sandbox_root.rglob("*.json"), key=lambda row: str(row).lower()):
        if def_ignore(path_value):
            continue
        try:
            json.loads(def_read(path_value)[0])
            rows.append({"path": def_relative(path_value, sandbox_root), "status": "PASS"})
        except Exception as exc:
            rows.append({"path": def_relative(path_value, sandbox_root), "status": "FAIL", "detail": str(exc)})
    return {"ok": all(row["status"] == "PASS" for row in rows), "total": len(rows),
            "passed": sum(row["status"] == "PASS" for row in rows),
            "failed": sum(row["status"] == "FAIL" for row in rows), "rows": rows}


def def_validate_generated_bridge(sandbox_root: Path) -> Dict[str, Any]:
    bridge = sandbox_root / "VIA_AdaptiveContractBridge_v0100.py"
    if not bridge.exists():
        return {"ok": False, "status": "MISSING", "path": str(bridge)}
    return def_run_command([sys.executable, "-B", str(bridge)], sandbox_root, timeout=90,
                           extra_env={"PYTHONPATH": str(sandbox_root)})


def def_extract_json_payload(text_value: str) -> Optional[Dict[str, Any]]:
    positions = [index for index, char in enumerate(text_value) if char == "{"]
    for index in reversed(positions):
        try:
            payload = json.loads(text_value[index:])
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue
    return None


def def_run_core_selftests(sandbox_root: Path, activate_sandbox: bool) -> Dict[str, Any]:
    if not activate_sandbox:
        return {"ok": True, "activated": False, "status": "SKIPPED_BY_POLICY", "rows": []}
    rows: List[Dict[str, Any]] = []
    for file_name, timeout in [
        ("VIA_Runtime_Bridge_All_in_One.py", 120),
        ("VIA_RegistryCore_v1.py", 120),
    ]:
        path_value = sandbox_root / file_name
        if not path_value.exists():
            candidates = list(sandbox_root.rglob(file_name))
            path_value = candidates[0] if candidates else path_value
        if not path_value.exists():
            rows.append({"name": file_name, "ok": False, "status": "MISSING"})
            continue
        result = def_run_command([sys.executable, "-B", str(path_value), "selftest"],
                                 sandbox_root, timeout=timeout,
                                 extra_env={"PYTHONPATH": str(sandbox_root)})
        payload = def_extract_json_payload(str(result.get("stdout", "")))
        semantic_ok = bool(result.get("ok")) and isinstance(payload, dict) and payload.get("ok") is True
        rows.append({"name": file_name, "path": def_relative(path_value, sandbox_root),
                     "ok": semantic_ok, "status": "PASS" if semantic_ok else "FAIL",
                     "semantic_payload": payload, **{key: value for key, value in result.items() if key != "ok"}})

    env_path = sandbox_root / "VIA_EnvManager.py"
    if not env_path.exists():
        candidates = list(sandbox_root.rglob("VIA_EnvManager.py"))
        env_path = candidates[0] if candidates else env_path
    if env_path.exists():
        probe_code = (
            "import importlib.util, json, pathlib, sys\n"
            f"p=pathlib.Path({str(env_path)!r})\n"
            "spec=importlib.util.spec_from_file_location('via_env_sandbox_contract', str(p))\n"
            "m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)\n"
            "out=pathlib.Path(m.def_PARAM_OUTPUT_DIR).resolve()\n"
            "root=p.parent.resolve()\n"
            "payload={'ok': m.def_PARAM_ENABLE_EXEC is False and (out==root or root in out.parents),"
            "'exec_disabled': m.def_PARAM_ENABLE_EXEC is False,'output_run_local': out==root or root in out.parents,"
            "'output_dir': str(out)}\n"
            "print(json.dumps(payload, ensure_ascii=False))\n"
        )
        result = def_run_command([sys.executable, "-B", "-c", probe_code], sandbox_root, timeout=120,
                                 extra_env={"PYTHONPATH": str(sandbox_root)})
        payload = def_extract_json_payload(str(result.get("stdout", "")))
        semantic_ok = bool(result.get("ok")) and isinstance(payload, dict) and payload.get("ok") is True
        rows.append({"name": "VIA_EnvManager.py::sandbox_safety_contract",
                     "path": def_relative(env_path, sandbox_root), "ok": semantic_ok,
                     "status": "PASS" if semantic_ok else "FAIL", "semantic_payload": payload,
                     **{key: value for key, value in result.items() if key != "ok"}})
    else:
        rows.append({"name": "VIA_EnvManager.py::sandbox_safety_contract", "ok": False, "status": "MISSING"})

    gate_ok = bool(rows) and all(bool(row.get("ok")) for row in rows)
    return {"ok": gate_ok, "activated": True,
            "status": "PASS" if gate_ok else "FAIL", "rows": rows}


def def_validate_powershell_capability(sandbox_root: Path) -> Dict[str, Any]:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    ps_files = [path for path in sandbox_root.rglob("*.ps1") if not def_ignore(path)]
    if not ps_files:
        return {"ok": True, "status": "NO_FILES", "rows": []}
    if not pwsh:
        return {"ok": True, "status": "SKIPPED_TOOL_UNAVAILABLE",
                "detail": "PowerShell executable not available in this Linux sandbox",
                "rows": [{"path": def_relative(path, sandbox_root), "status": "STATIC_SCAN_ONLY"}
                         for path in ps_files]}
    rows = []
    for path_value in ps_files:
        ok_value, detail = def_ps_ast(path_value)
        rows.append({"path": def_relative(path_value, sandbox_root),
                     "status": "PASS" if ok_value else "FAIL", "detail": detail})
    return {"ok": all(row["status"] == "PASS" for row in rows), "status": "PASS", "rows": rows}


def def_round3_polish(snapshot: def_Snapshot, sandbox_root: Path, activate_sandbox: bool) -> Tuple[List[def_Action], Dict[str, Any]]:
    tests = {
        "python_syntax": def_validate_python_syntax(sandbox_root),
        "json_parse": def_validate_json_files(sandbox_root),
        "contract_bridge": def_validate_generated_bridge(sandbox_root),
        "powershell_ast": def_validate_powershell_capability(sandbox_root),
    }
    tests["core_selftests"] = def_run_core_selftests(sandbox_root, activate_sandbox)
    tests["ok"] = all(bool(value.get("ok")) for key, value in tests.items()
                      if key not in {"ok"} and isinstance(value, dict))
    target = sandbox_root / "VIA_Sandbox_Verification_v0100.json"
    before = def_hash_file(target) if target.exists() else ""
    def_write_json(target, {"asset_id": def_PARAM_GENERATED_ASSET_IDS["verification"], "generated_at_utc": def_now(), "snapshot_gate": snapshot.summary.get("gate"), **tests})
    action = def_Action("ACT-" + def_short("sandbox-verify|" + str(target)), 3, 1,
                        "SANDBOX_VERIFY_AND_ACTIVATE", def_PARAM_CLASS_SEQUENCE,
                        str(sandbox_root), str(target), "PASS" if tests["ok"] else "FAIL",
                        "AST/compile + JSON + contract bridge + optional core selftests",
                        before, def_hash_file(target), False, False)
    hygiene_target = sandbox_root / "VIA_Hydra_Review_Queue_v0100.json"
    hydra_rows = [row for row in snapshot.issues if row.get("hydra")]
    def_write_json(hygiene_target, {
        "asset_id": def_PARAM_GENERATED_ASSET_IDS["hydra_queue"],
        "generated_at_utc": def_now(),
        "policy": "SUGGESTIONS_ONLY_NO_AUTOMATIC_SOURCE_REWRITE",
        "count": len(hydra_rows),
        "items": hydra_rows,
    })
    action2 = def_Action("ACT-" + def_short("hydra-queue|" + str(hygiene_target)), 3, 2,
                         "GENERATE_HYDRA_REVIEW_QUEUE", def_PARAM_CLASS_HYDRA,
                         str(sandbox_root), str(hygiene_target), "GENERATED_REVIEW_ONLY",
                         f"{len(hydra_rows)} 個 Hydra 節點未自動改寫",
                         "", def_hash_file(hygiene_target), False, False)
    return [action, action2], tests


def def_verify_canonical_integrity(canonical_snapshot: def_Snapshot) -> Dict[str, Any]:
    rows = []
    for asset in canonical_snapshot.assets:
        path_value = Path(str(asset.get("path", "")))
        expected = str(asset.get("sha256", ""))
        if not path_value.exists():
            rows.append({"path": str(path_value), "status": "MISSING", "expected": expected, "actual": ""})
            continue
        actual = def_hash_file(path_value)
        rows.append({"path": str(path_value), "status": "PASS" if actual == expected else "CHANGED",
                     "expected": expected, "actual": actual})
    return {"ok": all(row["status"] == "PASS" for row in rows),
            "total": len(rows), "passed": sum(row["status"] == "PASS" for row in rows),
            "changed": sum(row["status"] == "CHANGED" for row in rows),
            "missing": sum(row["status"] == "MISSING" for row in rows), "rows": rows}


# =============================================================================
# def HTML UI MATRICES
# =============================================================================
def def_cell(value: Any, max_length: int = 1200) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        text_value = json.dumps(value, ensure_ascii=False, default=str)
    elif value is None:
        text_value = ""
    else:
        text_value = str(value)
    if len(text_value) > max_length:
        text_value = text_value[:max_length] + "…"
    return html.escape(text_value)


def def_html_table(rows: Sequence[Dict[str, Any]], columns: Sequence[Tuple[str, str]],
                   empty_message: str = "No rows") -> str:
    if not rows:
        return f'<div class="empty">{html.escape(empty_message)}</div>'
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            class_name = ""
            if key in {"ryg", "status", "severity", "gate"}:
                normalized = str(value).upper()
                if any(token in normalized for token in ["RED", "FAIL", "CRITICAL", "HIGH", "CHANGED", "MISSING"]):
                    class_name = " red"
                elif any(token in normalized for token in ["YELLOW", "WARN", "REVIEW", "MEDIUM", "HOLD"]):
                    class_name = " yellow"
                elif any(token in normalized for token in ["GREEN", "PASS", "OK", "APPLIED", "GENERATED", "COPIED", "SKIP_IDENTICAL"]):
                    class_name = " green"
            cells.append(f'<td class="{class_name.strip()}">{def_cell(value)}</td>')
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def def_issue_code_counts(snapshot: def_Snapshot) -> Dict[str, int]:
    return dict(Counter(str(row.get("code", "UNKNOWN")) for row in snapshot.issues))


def def_round_delta(before: def_Snapshot, after: def_Snapshot) -> Dict[str, Any]:
    return {
        "assets": int(after.summary.get("assets_total", 0)) - int(before.summary.get("assets_total", 0)),
        "issues": int(after.summary.get("issues_total", 0)) - int(before.summary.get("issues_total", 0)),
        "critical": int(after.summary.get("severity", {}).get("CRITICAL", 0)) - int(before.summary.get("severity", {}).get("CRITICAL", 0)),
        "high": int(after.summary.get("severity", {}).get("HIGH", 0)) - int(before.summary.get("severity", {}).get("HIGH", 0)),
        "hydra": int(after.summary.get("hydra_count", 0)) - int(before.summary.get("hydra_count", 0)),
        "risk_score": int(after.summary.get("risk_score", 0)) - int(before.summary.get("risk_score", 0)),
        "before_gate": before.summary.get("gate"),
        "after_gate": after.summary.get("gate"),
    }


def def_action_summary(actions: Sequence[def_Action]) -> Dict[str, Any]:
    statuses = Counter(action.status for action in actions)
    return {
        "total": len(actions),
        "applied": sum(action.status in {"APPLIED_SANDBOX_ONLY", "GENERATED", "PASS", "COPIED"} for action in actions),
        "failed": sum(action.status == "FAIL" for action in actions),
        "canonical_mutations": sum(action.canonical_mutation for action in actions),
        "hydra_touched": sum(action.hydra_touched for action in actions),
        "statuses": dict(statuses),
    }


def def_matrix_section(section_id: str, title: str, subtitle: str, body: str) -> str:
    return (f'<section id="{html.escape(section_id)}" class="matrix">'
            f'<div class="matrix-head"><div><h2>{html.escape(title)}</h2>'
            f'<p>{html.escape(subtitle)}</p></div></div>{body}</section>')


def def_build_matrix_body(before: def_Snapshot, after: def_Snapshot,
                          actions: Sequence[def_Action], tests: Optional[Dict[str, Any]] = None,
                          canonical_integrity: Optional[Dict[str, Any]] = None) -> str:
    issue_rows = [row for row in after.issues if row.get("severity") in {"CRITICAL", "HIGH", "MEDIUM"}]
    optimization_rows = []
    for row in after.issues:
        if row.get("auto_fixable") or row.get("severity") in {"LOW", "MEDIUM"}:
            optimization_rows.append({
                "code": row.get("code"), "severity": row.get("severity"),
                "subsystem": row.get("subsystem"), "relative_path": row.get("relative_path"),
                "detail": row.get("detail"), "suggested_action": row.get("suggested_action"),
            })
    hydra_rows = [row for row in after.issues if row.get("hydra")]
    action_rows = [asdict(row) for row in actions]
    health_rows = [{"subsystem": key, **value} for key, value in sorted(after.subsystem_health.items())]
    quantity_rows = []
    all_keys = sorted(set(before.quantities) | set(after.quantities))
    for key in all_keys:
        before_value, after_value = before.quantities.get(key), after.quantities.get(key)
        quantity_rows.append({"metric": key, "before": before_value, "after": after_value,
                              "status": "PASS" if key not in {"parse_fail_count"} or not after_value else "REVIEW"})
    ssot_rows = []
    for key in sorted(set(before.ssot) | set(after.ssot)):
        before_value, after_value = before.ssot.get(key), after.ssot.get(key)
        status = "PASS" if key == "alignment_status" and after_value == "PASS" else (
            "PASS" if before_value == after_value and key != "alignment_status" else "REVIEW")
        ssot_rows.append({"dimension": key, "before": before_value, "after": after_value, "status": status})
    contract_rows = list(after.contracts.get("checks", []))
    test_rows: List[Dict[str, Any]] = []
    if tests:
        for key, value in tests.items():
            if key == "ok" or not isinstance(value, dict):
                continue
            test_rows.append({"test": key, "status": value.get("status") or ("PASS" if value.get("ok") else "FAIL"),
                              "detail": {name: val for name, val in value.items() if name not in {"rows", "stdout", "stderr"}},
                              "evidence": ((value.get("stdout") or "") + "\n" + (value.get("stderr") or ""))[-1600:]})
    delta = def_round_delta(before, after)
    cards = [
        ("Gate", after.summary.get("gate"), "gate"),
        ("Assets", after.summary.get("assets_total"), "neutral"),
        ("Issues", after.summary.get("issues_total"), "neutral"),
        ("Critical", after.summary.get("severity", {}).get("CRITICAL", 0), "red"),
        ("High", after.summary.get("severity", {}).get("HIGH", 0), "yellow"),
        ("Hydra", after.summary.get("hydra_count", 0), "red"),
        ("Risk Δ", delta.get("risk_score"), "neutral"),
        ("Canonical Writes", sum(action.canonical_mutation for action in actions), "green"),
    ]
    card_html = '<div class="cards">' + "".join(
        f'<div class="card {kind}"><span>{html.escape(label)}</span><strong>{def_cell(value, 120)}</strong></div>'
        for label, value, kind in cards) + '</div>'
    parts = [card_html]
    parts.append(def_matrix_section("errors", "Error Matrix", "當輪重掃後仍存在的中高風險錯誤",
        def_html_table(issue_rows, [
            ("ryg", "RYG"), ("severity", "Severity"), ("code", "Code"),
            ("classification", "Class"), ("subsystem", "System"),
            ("relative_path", "Asset"), ("line", "Line"), ("detail", "Evidence"),
            ("suggested_action", "Governance Action")], "未發現中高風險錯誤")))
    parts.append(def_matrix_section("optimization", "Optimization Matrix", "安全可改善項與建議",
        def_html_table(optimization_rows, [
            ("severity", "Severity"), ("code", "Code"), ("subsystem", "System"),
            ("relative_path", "Asset"), ("detail", "Finding"), ("suggested_action", "Action")],
            "無額外優化項")))
    parts.append(def_matrix_section("hydra", "Hydra Risk Matrix", "重複 owner、循環、自我匯入、啟動順序與動態執行；僅建議不自動改寫",
        def_html_table(hydra_rows, [
            ("severity", "Severity"), ("code", "Code"), ("subsystem", "System"),
            ("relative_path", "Asset"), ("line", "Line"), ("detail", "Hydra Evidence"),
            ("suggested_action", "Review Action")], "Hydra=0")))
    parts.append(def_matrix_section("dependency", "Dependency Matrix", "AST import dependency graph",
        def_html_table(after.dependencies, [
            ("source", "Consumer"), ("target", "Provider"), ("edge_type", "Type"),
            ("status", "Status"), ("detail", "Detail")], "無可解析依賴")))
    parts.append(def_matrix_section("fix-order", "Fix Order Matrix", "依賴優先；cycle/Hydra 節點 fail-closed",
        def_html_table(after.fix_order, [
            ("order", "Order"), ("module", "Module"), ("status", "Status"), ("reason", "Reason")],
            "無模組排序")))
    parts.append(def_matrix_section("actions", "Repair Action Matrix", "所有寫入僅發生於 sandbox",
        def_html_table(action_rows, [
            ("round_no", "Round"), ("order_no", "Order"), ("code", "Action"),
            ("classification", "Class"), ("status", "Status"),
            ("target_path", "Target"), ("detail", "Detail"),
            ("canonical_mutation", "Canonical Write"), ("hydra_touched", "Hydra Touched")],
            "本輪無修補動作")))
    parts.append(def_matrix_section("health", "RYG Health Matrix", "各子系統健康指標",
        def_html_table(health_rows, [
            ("subsystem", "Subsystem"), ("ryg", "RYG"), ("assets", "Assets"),
            ("issues", "Issues"), ("critical", "Critical"), ("high", "High"), ("hydra", "Hydra")],
            "無子系統資料")))
    parts.append(def_matrix_section("quantity", "Quantity Validation", "掃描數量與解析完整性",
        def_html_table(quantity_rows, [
            ("metric", "Metric"), ("before", "Before"), ("after", "After"), ("status", "Status")],
            "無數量資料")))
    parts.append(def_matrix_section("ssot", "SSOT Comparison", "Canonical 與 sandbox overlay 對齊狀態",
        def_html_table(ssot_rows, [
            ("dimension", "Dimension"), ("before", "Before"), ("after", "After"), ("status", "Status")],
            "無 SSOT 資料")))
    parts.append(def_matrix_section("contracts", "Interface Contract Matrix", "Provider exports 與下游要求",
        def_html_table(contract_rows, [
            ("module", "Module"), ("status", "Status"), ("expected", "Expected"),
            ("missing", "Missing"), ("path", "Path")], "無契約檢查")))
    parts.append(def_matrix_section("systems", "Multi-System Comparison", "VIA / VRN / VDF / VAP / others 同步治理",
        def_html_table(health_rows, [
            ("subsystem", "System"), ("ryg", "RYG"), ("assets", "Assets"),
            ("issues", "Issues"), ("critical", "Critical"), ("high", "High"), ("hydra", "Hydra")],
            "無跨系統資料")))
    if test_rows:
        parts.append(def_matrix_section("tests", "Sandbox Test Matrix", "test → debug → consolidate → user-test evidence",
            def_html_table(test_rows, [
                ("test", "Test"), ("status", "Status"), ("detail", "Detail"), ("evidence", "Evidence")],
                "尚未執行測試")))
    if canonical_integrity:
        integrity_summary = [{"metric": key, "value": value, "status": "PASS" if key != "ok" or value else "FAIL"}
                             for key, value in canonical_integrity.items() if key != "rows"]
        parts.append(def_matrix_section("integrity", "Canonical Integrity Matrix", "原始母檔 hash 不變驗證",
            def_html_table(integrity_summary, [("metric", "Metric"), ("value", "Value"), ("status", "Status")],
                           "無完整性資料")))
    return "".join(parts)


def def_render_report(title: str, round_label: str, before: def_Snapshot, after: def_Snapshot,
                      actions: Sequence[def_Action], tests: Optional[Dict[str, Any]] = None,
                      canonical_integrity: Optional[Dict[str, Any]] = None,
                      round_links: Optional[List[Dict[str, str]]] = None) -> str:
    navigation = "".join(
        f'<a href="{html.escape(row.get("href", "#"))}">{html.escape(row.get("label", "Round"))}</a>'
        for row in (round_links or []))
    body = def_build_matrix_body(before, after, actions, tests, canonical_integrity)
    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#f4f7fb;--surface:#ffffff;--surface2:#f8fafc;--line:#d9e1ec;--text:#243147;--muted:#66758c;--blue:#3f6ea8;--green:#2f855a;--green-bg:#e8f5ed;--yellow:#a66a00;--yellow-bg:#fff4d6;--red:#b54848;--red-bg:#fdeaea;--violet:#6b5aa6;--shadow:0 5px 18px rgba(63,78,100,.08)}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,"Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;font-size:12px;line-height:1.5}}
header{{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.96);border-bottom:1px solid var(--line);backdrop-filter:blur(9px)}}
.header-inner{{max-width:1740px;margin:auto;padding:13px 18px;display:flex;align-items:center;gap:14px}}.logo{{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,var(--blue),var(--violet));color:#fff;display:grid;place-items:center;font-weight:800}}
h1{{font-size:18px;margin:0}}.sub{{color:var(--muted);font-size:10px;margin-top:2px}}nav{{margin-left:auto;display:flex;gap:5px;flex-wrap:wrap}}nav a{{color:var(--blue);text-decoration:none;border:1px solid var(--line);border-radius:6px;padding:4px 8px;background:var(--surface2)}}
main{{max-width:1740px;margin:auto;padding:14px 18px 40px}}.hero{{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:14px 16px;box-shadow:var(--shadow);margin-bottom:9px}}.hero h2{{margin:0 0 3px;font-size:15px}}.hero p{{margin:0;color:var(--muted)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:6px;margin-bottom:9px}}.card{{background:var(--surface);border:1px solid var(--line);border-radius:9px;padding:8px 10px;box-shadow:var(--shadow)}}.card span{{display:block;color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.4px}}.card strong{{display:block;margin-top:2px;font:700 13px ui-monospace,SFMono-Regular,Consolas,monospace;overflow:hidden;text-overflow:ellipsis}}.card.red{{border-left:4px solid var(--red)}}.card.yellow{{border-left:4px solid var(--yellow)}}.card.green{{border-left:4px solid var(--green)}}
.matrix{{background:var(--surface);border:1px solid var(--line);border-radius:11px;margin-bottom:8px;overflow:hidden;box-shadow:var(--shadow)}}.matrix-head{{padding:9px 12px;background:var(--surface2);border-bottom:1px solid var(--line)}}.matrix h2{{margin:0;font-size:12px}}.matrix p{{margin:1px 0 0;color:var(--muted);font-size:9px}}.table-wrap{{overflow:auto;max-height:560px}}table{{border-collapse:collapse;width:100%;font-size:10px}}th{{position:sticky;top:0;background:#eef3f9;color:#52627a;text-align:left;padding:6px 7px;border-bottom:1px solid var(--line);white-space:nowrap}}td{{padding:5px 7px;border-bottom:1px solid #edf1f6;vertical-align:top;max-width:420px;word-break:break-word}}tr:hover td{{background:#fafcff}}td.green{{background:var(--green-bg);color:var(--green);font-weight:700}}td.yellow{{background:var(--yellow-bg);color:var(--yellow);font-weight:700}}td.red{{background:var(--red-bg);color:var(--red);font-weight:700}}.empty{{padding:14px;color:var(--muted)}}footer{{color:var(--muted);text-align:center;padding:12px}}
@media(max-width:760px){{.header-inner,.hero{{flex-direction:column}}nav{{margin-left:0}}main{{padding:8px}}}}
</style>
</head>
<body>
<header><div class="header-inner"><div class="logo">VIA</div><div><h1>{html.escape(title)}</h1><div class="sub">Veritas Intelligence Analytics · Observa · Intellege · Praevide</div></div><nav>{navigation}<a href="#errors">Errors</a><a href="#hydra">Hydra</a><a href="#actions">Fixes</a><a href="#tests">Tests</a></nav></div></header>
<main><div class="hero"><div><h2>{html.escape(round_label)}</h2><p>Generated {html.escape(def_now())} · canonical mutation = false · max rounds = {def_PARAM_MAX_ROUNDS}</p></div><div><strong>{def_cell(after.summary.get("gate"), 100)}</strong></div></div>{body}</main>
<footer>{html.escape(def_PARAM_ENGINE)} v{html.escape(def_PARAM_VERSION)} · {html.escape(def_PARAM_ASSET_ID)}</footer>
</body></html>'''


def def_write_round_artifacts(report_dir: Path, round_no: int, before: def_Snapshot,
                              after: def_Snapshot, actions: Sequence[def_Action],
                              tests: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    report_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"Round_{round_no}"
    before_json = report_dir / f"{prefix}_Before.json"
    after_json = report_dir / f"{prefix}_After.json"
    actions_json = report_dir / f"{prefix}_Actions.json"
    html_path = report_dir / f"{prefix}_Matrix.html"
    def_write_json(before_json, asdict(before))
    def_write_json(after_json, asdict(after))
    def_write_json(actions_json, [asdict(row) for row in actions])
    html_value = def_render_report(f"VIA Adaptive Downward Governance · Round {round_no}",
                                   f"Round {round_no} · Panoramic Re-analysis",
                                   before, after, actions, tests)
    def_write_text(html_path, html_value)
    return {"before_json": str(before_json), "after_json": str(after_json),
            "actions_json": str(actions_json), "html": str(html_path)}


# =============================================================================
# def ORCHESTRATION
# =============================================================================
def def_final_gate(final_snapshot: def_Snapshot, tests: Dict[str, Any],
                   integrity: Dict[str, Any], activate_sandbox: bool) -> str:
    if not integrity.get("ok"):
        return "RED_CANONICAL_INTEGRITY_FAILURE"
    if int(final_snapshot.summary.get("severity", {}).get("CRITICAL", 0)) > 0:
        return "RED_CRITICAL_HOLD"
    if tests and not tests.get("ok"):
        return "RED_SANDBOX_TEST_FAILURE"
    if int(final_snapshot.summary.get("hydra_count", 0)) > 0 or int(final_snapshot.summary.get("severity", {}).get("HIGH", 0)) > 0:
        return "YELLOW_SANDBOX_ACTIVE_REVIEW_REQUIRED" if activate_sandbox else "YELLOW_SANDBOX_READY_REVIEW_REQUIRED"
    return "GREEN_SANDBOX_ACTIVE" if activate_sandbox else "GREEN_SANDBOX_READY"


def def_run_governance(base_root: Path, output_root: Path, rounds: int,
                       apply_safe_fixes: bool, activate_sandbox: bool) -> Dict[str, Any]:
    rounds = max(1, min(def_PARAM_MAX_ROUNDS, int(rounds)))
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / f"RUN_{def_stamp()}_VIA_ADAPTIVE_DOWNWARD_v0100"
    report_dir = run_dir / "reports"
    sandbox_root = run_dir / "sandbox"
    ledger_path = run_dir / "VIA_Adaptive_Evidence_Ledger.jsonl"
    report_dir.mkdir(parents=True, exist_ok=True)

    profile = def_profile(base_root)
    preflight = {
        "generated_at_utc": def_now(),
        "base_root": str(base_root),
        "output_root": str(output_root),
        "run_dir": str(run_dir),
        "sandbox_root": str(sandbox_root),
        "profile": asdict(profile),
        "rounds": rounds,
        "apply_safe_fixes": apply_safe_fixes,
        "activate_sandbox": activate_sandbox,
        "accelerators": def_PARAM_ACCELERATORS,
        "policy": "NO_CANONICAL_MUTATION_APPEND_ONLY_SANDBOX",
    }
    def_write_json(run_dir / "VIA_Adaptive_Preflight.json", preflight)
    def_append_jsonl(ledger_path, {"event": "PREFLIGHT", **preflight})

    canonical_snapshot = def_analyze(base_root, output_root, profile)
    def_write_json(run_dir / "Canonical_Baseline.json", asdict(canonical_snapshot))
    def_append_jsonl(ledger_path, {"event": "CANONICAL_BASELINE", "summary": canonical_snapshot.summary,
                                  "ssot": canonical_snapshot.ssot, "quantities": canonical_snapshot.quantities})

    round_records: List[Dict[str, Any]] = []
    all_actions: List[def_Action] = []
    current_snapshot = canonical_snapshot
    tests: Dict[str, Any] = {}

    if rounds >= 1:
        before = canonical_snapshot
        actions = def_round1_comprehensive(canonical_snapshot, base_root, sandbox_root, output_root, apply_safe_fixes)
        all_actions.extend(actions)
        after = def_analyze(sandbox_root, None, def_profile(sandbox_root))
        paths = def_write_round_artifacts(report_dir, 1, before, after, actions)
        record = {"round": 1, "strategy": "COMPREHENSIVE_PARALLEL_SAFE",
                  "before": before.summary, "after": after.summary,
                  "delta": def_round_delta(before, after), "actions": def_action_summary(actions), "paths": paths}
        round_records.append(record)
        def_append_jsonl(ledger_path, {"event": "ROUND_COMPLETE", **record})
        current_snapshot = after

    if rounds >= 2:
        before = current_snapshot
        actions = def_round2_sequential(before, sandbox_root)
        all_actions.extend(actions)
        after = def_analyze(sandbox_root, None, def_profile(sandbox_root))
        paths = def_write_round_artifacts(report_dir, 2, before, after, actions)
        record = {"round": 2, "strategy": "SEQUENTIAL_DEPENDENCY_AND_CONTRACT",
                  "before": before.summary, "after": after.summary,
                  "delta": def_round_delta(before, after), "actions": def_action_summary(actions), "paths": paths}
        round_records.append(record)
        def_append_jsonl(ledger_path, {"event": "ROUND_COMPLETE", **record})
        current_snapshot = after

    if rounds >= 3:
        before = current_snapshot
        actions, tests = def_round3_polish(before, sandbox_root, activate_sandbox)
        all_actions.extend(actions)
        after = def_analyze(sandbox_root, None, def_profile(sandbox_root))
        paths = def_write_round_artifacts(report_dir, 3, before, after, actions, tests)
        record = {"round": 3, "strategy": "FINAL_POLISH_STABILITY_HARDENING",
                  "before": before.summary, "after": after.summary,
                  "delta": def_round_delta(before, after), "actions": def_action_summary(actions),
                  "tests": {key: value for key, value in tests.items() if key != "core_selftests"},
                  "paths": paths}
        round_records.append(record)
        def_append_jsonl(ledger_path, {"event": "ROUND_COMPLETE", **record})
        current_snapshot = after

    integrity = def_verify_canonical_integrity(canonical_snapshot)
    gate = def_final_gate(current_snapshot, tests, integrity, activate_sandbox)
    final_summary = {
        "ok": gate.startswith("GREEN") or gate.startswith("YELLOW"),
        "gate": gate,
        "engine": def_PARAM_ENGINE,
        "version": def_PARAM_VERSION,
        "asset_id": def_PARAM_ASSET_ID,
        "generated_at_utc": def_now(),
        "base_root": str(base_root),
        "run_dir": str(run_dir),
        "sandbox_root": str(sandbox_root),
        "rounds_executed": len(round_records),
        "apply_safe_fixes": apply_safe_fixes,
        "sandbox_activation_requested": activate_sandbox,
        "sandbox_activation_status": tests.get("core_selftests", {}).get("status", "NOT_REQUESTED") if tests else "NOT_RUN",
        "canonical_mutation": False,
        "canonical_integrity": {key: value for key, value in integrity.items() if key != "rows"},
        "baseline": canonical_snapshot.summary,
        "final": current_snapshot.summary,
        "ssot": current_snapshot.ssot,
        "contracts": current_snapshot.contracts.get("checks", []),
        "rounds": round_records,
        "actions": def_action_summary(all_actions),
        "tests_ok": tests.get("ok") if tests else None,
        "remaining_review": {
            "critical": current_snapshot.summary.get("severity", {}).get("CRITICAL", 0),
            "high": current_snapshot.summary.get("severity", {}).get("HIGH", 0),
            "hydra": current_snapshot.summary.get("hydra_count", 0),
        },
    }
    final_json = run_dir / "VIA_Adaptive_Final_Summary.json"
    final_snapshot_json = run_dir / "VIA_Adaptive_Final_Snapshot.json"
    final_html = run_dir / "VIA_Adaptive_Final_Matrix.html"
    actions_json = run_dir / "VIA_Adaptive_All_Actions.json"
    integrity_json = run_dir / "VIA_Canonical_Integrity.json"
    def_write_json(final_json, final_summary)
    def_write_json(final_snapshot_json, asdict(current_snapshot))
    def_write_json(actions_json, [asdict(row) for row in all_actions])
    def_write_json(integrity_json, integrity)
    round_links = [{"label": f"Round {row['round']}",
                    "href": str(Path(row["paths"]["html"]).relative_to(run_dir)).replace("\\", "/")}
                   for row in round_records]
    final_report = def_render_report("VIA Central Governance · Adaptive Downward Final Matrix",
                                     f"Final Gate · {gate}", canonical_snapshot, current_snapshot,
                                     all_actions, tests, integrity, round_links)
    def_write_text(final_html, final_report)
    final_summary.update({
        "final_json": str(final_json),
        "final_snapshot_json": str(final_snapshot_json),
        "final_html": str(final_html),
        "actions_json": str(actions_json),
        "integrity_json": str(integrity_json),
        "ledger_jsonl": str(ledger_path),
    })
    def_write_json(final_json, final_summary)
    def_write_json(output_root / "LATEST_RUN.json", final_summary)
    def_append_jsonl(ledger_path, {"event": "FINAL", "summary": final_summary})
    return final_summary


# =============================================================================
# def SELF TESTS
# =============================================================================
def def_test_self_import_detection() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        target = root / "Demo.py"
        target.write_text("from Demo import *\n", encoding="utf-8")
        _, issues = def_analyze_python(target, root)
        assert any(row.code == "PY_SELF_IMPORT" for row in issues)
        assert any(row.code == "PY_WILDCARD_IMPORT" for row in issues)


def def_test_use_before_def_detection() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        target = root / "Order.py"
        target.write_text("x = later()\ndef later():\n    return 1\n", encoding="utf-8")
        _, issues = def_analyze_python(target, root)
        assert any(row.code == "PY_TOPLEVEL_USE_BEFORE_DEF" for row in issues)


def def_test_runtime_transform_idempotence() -> None:
    source = ('def_PARAM_SUPPORTIVE_ROOT = Path(r"C:\\\\X")\n'
              'def_PARAM_ENABLE_BOOTSTRAP_SCAN = True\n'
              'def_PARAM_ENABLE_CELERITAS_INIT = True\n'
              'def_PARAM_ENABLE_ENV_GOVERNANCE_CHECK = True\n')
    first, changed1 = def_transform_runtime(source)
    second, changed2 = def_transform_runtime(first)
    assert changed1 is True
    assert changed2 is False
    assert first == second


def def_test_html_duplicate_id() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        target = root / "x.html"
        target.write_text('<div id="a"></div><span id="a"></span>', encoding="utf-8")
        _, issues = def_analyze_html(target, root)
        assert any(row.code == "HTML_DUPLICATE_ID" for row in issues)


def def_test_scc_cycle() -> None:
    edges = [def_Edge("A", "B", "IMPORT"), def_Edge("B", "A", "IMPORT")]
    components = def_scc(["A", "B"], edges)
    assert any(set(row) == {"A", "B"} for row in components)


def def_test_generated_bridge_compile() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        snapshot = def_Snapshot(str(root), def_now(), [], [], [], {"modules": {}, "checks": []},
                                {}, {}, {}, [], {"gate": "GREEN_READY"})
        def_generate_path_registry(root, 2, 1)
        def_generate_contract_bridge(snapshot, root, 2, 2)
        validation = def_validate_python_syntax(root)
        assert validation["ok"] is True


def def_run_self_tests() -> Dict[str, Any]:
    tests = [
        def_test_self_import_detection,
        def_test_use_before_def_detection,
        def_test_runtime_transform_idempotence,
        def_test_html_duplicate_id,
        def_test_scc_cycle,
        def_test_generated_bridge_compile,
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


# =============================================================================
# def CLI
# =============================================================================
def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA Central Governance Adaptive Downward Governor")
    parser.add_argument("--base-root", default="", help="VIA canonical root; read-only")
    parser.add_argument("--output-root", default="", help="Append-only run output root")
    parser.add_argument("--rounds", type=int, default=def_PARAM_MAX_ROUNDS)
    parser.add_argument("--apply-safe-fixes", action="store_true", help="Apply only allowlisted fixes to sandbox mirror")
    parser.add_argument("--activate-sandbox", action="store_true", help="Run isolated core self-tests; never activates canonical runtime")
    parser.add_argument("--selftest", action="store_true")
    return parser


def def_main(argv: Optional[List[str]] = None) -> int:
    args = def_build_parser().parse_args(argv)
    if args.selftest:
        payload = def_run_self_tests()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload.get("ok") else 2
    base_root = def_pick_root(args.base_root)
    output_root = Path(args.output_root).expanduser().resolve() if args.output_root else base_root / "_via_adaptive_downward_runs"
    payload = def_run_governance(base_root, output_root, args.rounds,
                                 args.apply_safe_fixes, args.activate_sandbox)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("ok") else 3


def def_run_cli() -> None:
    code = def_main()
    if code != 0:
        print(f"[{def_PARAM_ENGINE}] exit_code={code}", file=sys.stderr)


if __name__ == "__main__":
    def_run_cli()
