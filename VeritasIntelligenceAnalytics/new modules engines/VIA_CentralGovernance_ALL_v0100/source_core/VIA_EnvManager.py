from __future__ import annotations

"""
VIA_EnvManager.py
VIA 中央環境治理核心：統一管理 venv / libs / alias / route / health / conflicts / rebuild plan。

設計原則：
1. 只增不減：所有掃描、修復建議、快照皆 append-only。
2. 參數集中於頂部。
3. 優先吸收既有紀錄：Alias Map / Library Registry / Route Table / 安裝歷史。
4. 可離線運作；若無 uv / pip 也能以降級模式完成盤點。
5. 與 VIA_SSOT_Unified / VeritasCeleritas / EnvRouter 保持鬆耦合。
6. 預設不直接破壞環境；只做掃描、分類、建議、可選修復命令生成。
7. 任何新增工具都必須先經過 EnvManager 決策，再決定環境位置。
"""

# ══════════════════════════════════════════════════════════════════════════════
# def PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import socket
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional


def_PARAM_SYSTEM_CODE = "SYS_VIA"
def_PARAM_MODULE_ID = "VIS-ENV-MANAGER-000001"
def_PARAM_MODULE_VERSION = "1.1.0"
def_PARAM_OWNER = "VIA_ENV_MANAGER"
def_PARAM_APPEND_ONLY = True

def_PARAM_ENABLE_AUTO_CREATE_DIR = True
def_PARAM_ENABLE_UV = True
def_PARAM_ENABLE_PIP = True
def_PARAM_ENABLE_IMPORT_PROBE = True
def_PARAM_ENABLE_SSOT = True
def_PARAM_ENABLE_ACCELERATOR = True
def_PARAM_ENABLE_HISTORY = True
def_PARAM_ENABLE_EXEC = True

def_PARAM_OUTPUT_DIR = Path.cwd() / "_via_envmanager_output"
def_PARAM_SSOT_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_SSOT.json"
def_PARAM_HISTORY_JSONL = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_History.jsonl"
def_PARAM_HEALTH_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_Health.json"
def_PARAM_HTML_REPORT = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_Report.html"
def_PARAM_COMMAND_PLAN_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_CommandPlan.json"
def_PARAM_INSTALL_REQUEST_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_InstallRequests.jsonl"
def_PARAM_INSTALL_PLAN_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_InstallPlan.json"
def_PARAM_INSTALL_DECISION_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_InstallDecision.json"
def_PARAM_CONFLICT_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_ConflictReport.json"

def_PARAM_STATUS_OK = "OK"
def_PARAM_STATUS_WARN = "WARN"
def_PARAM_STATUS_REBUILD = "REBUILD"
def_PARAM_STATUS_BROKEN = "BROKEN"
def_PARAM_STATUS_UNKNOWN = "UNKNOWN"

def_PARAM_ENV_ROOT_CANDIDATES = [
    Path(r"C:\Users\tonyk\envs"),
    Path(r"C:\VeritasIntelligenceAnalytics\Environments"),
    Path(r"C:\VHB_System\Environments"),
    Path(r"C:\Users\tonyk\OneDrive\Documents\Environments"),
]

def_PARAM_ALIAS_JSON_CANDIDATES = [
    Path(r"C:\VeritasIntelligenceAnalytics\_tier_install_reports\TIERPATCH_V3_20260414_172619\VIA_Env_Alias_Map_v3.json"),
]

def_PARAM_REGISTRY_JSON_CANDIDATES = [
    Path(r"C:\VeritasIntelligenceAnalytics\_tier_install_reports\TIERPATCH_V3_20260414_172619\VIA_Library_Registry_v3.json"),
]

def_PARAM_ROUTE_TABLE_JSON_CANDIDATES = [
    Path(r"C:\VeritasIntelligenceAnalytics\VIA_EnvRoute_Table.json"),
]

def_PARAM_SSOT_MODULE_CANDIDATES = [
    Path("/mnt/data/VIA_SSOT_Unified.py"),
    Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py"),
]

def_PARAM_ACCELERATOR_MODULE_CANDIDATES = [
    Path("/mnt/data/VeritasCeleritas.py"),
    Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"),
]

def_PARAM_SNAPSHOT_LIBS = [
    "pip",
    "setuptools",
    "wheel",
    "packaging",
    "numpy",
    "pandas",
    "pyarrow",
    "requests",
    "aiohttp",
    "duckdb",
    "polars",
    "scipy",
    "torch",
    "tensorflow",
    "paddleocr",
    "pymupdf",
    "pdfplumber",
    "camelot",
    "tabula",
    "weasyprint",
    "openpyxl",
    "xlsxwriter",
    "plotly",
    "orjson",
    "uvicorn",
    "fastapi",
]

def_PARAM_HIGH_RISK_LIBS = [
    "torch",
    "tensorflow",
    "paddleocr",
    "paddlepaddle",
    "opencv-python",
    "opencv-contrib-python",
    "onnxruntime",
    "pyvips",
    "camelot-py",
    "tabula-py",
    "weasyprint",
    "playwright",
    "selenium",
    "jax",
    "xgboost",
    "lightgbm",
    "catboost",
]

def_PARAM_MEDIUM_RISK_LIBS = [
    "pymupdf",
    "pdfplumber",
    "polars",
    "duckdb",
    "pyarrow",
    "plotly",
    "fastapi",
    "uvicorn",
    "aiohttp",
    "httpx",
    "orjson",
    "openpyxl",
    "xlsxwriter",
]

def_PARAM_BASE_BLOCK_RISK_LEVELS = ["MEDIUM", "HIGH"]

def_PARAM_VIA_CORE_WHITELIST = [
    "pip",
    "setuptools",
    "wheel",
    "packaging",
    "requests",
    "httpx",
    "aiohttp",
    "orjson",
    "numpy",
    "pandas",
    "pyarrow",
    "duckdb",
    "polars",
    "openpyxl",
    "xlsxwriter",
    "plotly",
    "fastapi",
    "uvicorn",
    "rich",
    "loguru",
    "pydantic",
]

def_PARAM_ENV_PURPOSE_HINTS = {
    "via_core": ["requests", "httpx", "aiohttp", "orjson", "numpy", "pandas", "pyarrow", "duckdb", "polars", "plotly", "openpyxl", "xlsxwriter", "fastapi", "uvicorn"],
    "via_vdf": ["numpy", "pandas", "pyarrow", "duckdb", "polars", "plotly", "openpyxl", "xlsxwriter"],
    "via_vrn": ["pymupdf", "pdfplumber", "numpy", "pandas", "pyarrow"],
    "paddle_311": ["paddleocr", "paddlepaddle", "opencv-python"],
    "camelot_311": ["camelot-py", "tabula-py", "pdfplumber"],
}

def_PARAM_ENV_NAME_PATTERNS = [
    re.compile(r"^via_", re.IGNORECASE),
    re.compile(r"^base$", re.IGNORECASE),
    re.compile(r"^venv", re.IGNORECASE),
    re.compile(r"^\.venv$", re.IGNORECASE),
    re.compile(r"^paddle", re.IGNORECASE),
    re.compile(r"^camelot", re.IGNORECASE),
]

def_PARAM_BASE_ENV_NAMES = [
    "base",
    "venv_base",
    "py_base",
]

def_PARAM_MANAGED_ENV_PREFIXES = [
    "via_",
    "base",
    "paddle",
    "camelot",
]


# ══════════════════════════════════════════════════════════════════════════════
# def DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class def_EnvAliasRecord:
    alias_name: str
    env_name: str
    env_path: str
    python_exe: str


@dataclass
class def_LibProbeResult:
    package_name: str
    status: str
    version: str = ""
    detail: str = ""
    source: str = "importlib"


@dataclass
class def_EnvHealthRecord:
    env_name: str
    env_path: str
    python_exe: str
    alias_names: List[str] = field(default_factory=list)
    exists: bool = False
    python_exists: bool = False
    pyvenv_cfg_exists: bool = False
    package_count: int = 0
    pip_check_ok: Optional[bool] = None
    uv_check_ok: Optional[bool] = None
    broken_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_core_libs: List[str] = field(default_factory=list)
    high_risk_libs_found: List[str] = field(default_factory=list)
    snapshot_libs: List[Dict[str, Any]] = field(default_factory=list)
    installed_package_names: List[str] = field(default_factory=list)
    status: str = def_PARAM_STATUS_UNKNOWN
    recommended_action: str = ""
    route_targets: List[str] = field(default_factory=list)
    last_scan_utc: str = ""
    is_base_env: bool = False
    is_managed_env: bool = False


@dataclass
class def_EnvConflictRecord:
    env_name: str
    severity: str
    category: str
    detail: str
    related_packages: List[str] = field(default_factory=list)


@dataclass
class def_InstallRequest:
    package_name: str
    requested_version: str = ""
    reason: str = ""
    requested_by: str = def_PARAM_OWNER
    requested_at_utc: str = ""
    preferred_env: str = ""
    allow_base: bool = False
    risk_level: str = "LOW"


@dataclass
class def_InstallDecision:
    package_name: str
    normalized_package_name: str
    risk_level: str
    approved: bool
    blocked_reason: str = ""
    target_env: str = ""
    target_python: str = ""
    strategy: str = ""
    powershell_commands: List[str] = field(default_factory=list)
    python_commands: List[str] = field(default_factory=list)
    executable_commands: List[List[str]] = field(default_factory=list)


@dataclass
class def_EnvManagerState:
    module_id: str
    version: str
    created_at_utc: str
    updated_at_utc: str
    env_root: str
    alias_map: Dict[str, str] = field(default_factory=dict)
    route_table: List[Dict[str, Any]] = field(default_factory=list)
    registry_rows: List[Dict[str, Any]] = field(default_factory=list)
    envs: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# def LOW LEVEL UTILS
# ══════════════════════════════════════════════════════════════════════════════
def def_now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_ensure_output_dir() -> None:
    if def_PARAM_ENABLE_AUTO_CREATE_DIR:
        def_PARAM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def def_read_text_safe(path_value: Path) -> str:
    try:
        return path_value.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path_value.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def def_read_json_safe(path_value: Path, default_value: Any) -> Any:
    try:
        if path_value.is_file():
            return json.loads(def_read_text_safe(path_value))
    except Exception:
        pass
    return copy.deepcopy(default_value)


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def def_append_jsonl(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    with path_value.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(payload, ensure_ascii=False) + "\n")


def def_pick_first_existing_path(path_candidates: List[Path]) -> Optional[Path]:
    for path_value in path_candidates:
        if path_value.exists():
            return path_value
    return None


def def_get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown-host"


def def_is_base_env_name(env_name: str) -> bool:
    normalized = env_name.strip().lower()
    return normalized in {row.lower() for row in def_PARAM_BASE_ENV_NAMES}


def def_is_managed_env_name(env_name: str) -> bool:
    normalized = env_name.strip().lower()
    return any(normalized.startswith(prefix.lower()) for prefix in def_PARAM_MANAGED_ENV_PREFIXES)


def def_hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def def_path_to_python(env_path: Path) -> Path:
    return env_path / "Scripts" / "python.exe"


def def_is_env_dir(path_value: Path) -> bool:
    if not path_value.is_dir():
        return False
    if (path_value / "pyvenv.cfg").exists():
        return True
    if def_path_to_python(path_value).exists():
        return True
    for pattern in def_PARAM_ENV_NAME_PATTERNS:
        if pattern.search(path_value.name):
            return True
    return False


def def_find_env_root() -> Path:
    for candidate in def_PARAM_ENV_ROOT_CANDIDATES:
        if candidate.exists():
            return candidate
    return def_PARAM_ENV_ROOT_CANDIDATES[0]


def def_run_subprocess(command: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "command": command,
        }
    except Exception as exc:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
            "command": command,
        }



# ══════════════════════════════════════════════════════════════════════════════
# def OPTIONAL EXTERNAL BRIDGES
# ══════════════════════════════════════════════════════════════════════════════
def def_load_module_from_candidates(module_name: str, path_candidates: List[Path]) -> Any:
    if not def_PARAM_ENABLE_IMPORT_PROBE:
        return None
    path_value = def_pick_first_existing_path(path_candidates)
    if path_value is None:
        return None
    try:
        spec_value = importlib.util.spec_from_file_location(module_name, str(path_value))
        if spec_value is None or spec_value.loader is None:
            return None
        module_obj = importlib.util.module_from_spec(spec_value)
        spec_value.loader.exec_module(module_obj)
        return module_obj
    except Exception:
        return None


def def_get_ssot_module() -> Any:
    if not def_PARAM_ENABLE_SSOT:
        return None
    return def_load_module_from_candidates("VIA_SSOT_Unified_runtime", def_PARAM_SSOT_MODULE_CANDIDATES)


def def_get_accelerator_module() -> Any:
    if not def_PARAM_ENABLE_ACCELERATOR:
        return None
    return def_load_module_from_candidates("VeritasCeleritas_runtime", def_PARAM_ACCELERATOR_MODULE_CANDIDATES)


def def_try_ssot_normalize_package_name(package_name: str) -> str:
    ssot_module = def_get_ssot_module()
    if ssot_module is None:
        return package_name
    try:
        if hasattr(ssot_module, "normalize"):
            normalized = ssot_module.normalize(package_name)
            return normalized or package_name
        if hasattr(ssot_module, "get_ssot"):
            ssot_obj = ssot_module.get_ssot()
            if hasattr(ssot_obj, "normalize"):
                normalized = ssot_obj.normalize(package_name)
                return normalized or package_name
    except Exception:
        return package_name
    return package_name


def def_try_accelerated_unique(items: List[str]) -> List[str]:
    accelerator = def_get_accelerator_module()
    if accelerator is None:
        return sorted(list(dict.fromkeys(items)))
    try:
        if hasattr(accelerator, "dedupe_preserve_order"):
            return accelerator.dedupe_preserve_order(items)
    except Exception:
        return sorted(list(dict.fromkeys(items)))
    return sorted(list(dict.fromkeys(items)))


# ══════════════════════════════════════════════════════════════════════════════
# def PACKAGE NORMALIZATION / RISK
# ══════════════════════════════════════════════════════════════════════════════
def def_normalize_package_name(package_name: str) -> str:
    normalized = def_try_ssot_normalize_package_name(package_name).strip().lower()
    return normalized.replace("_", "-")


def def_get_package_risk_level(package_name: str) -> str:
    normalized = def_normalize_package_name(package_name)
    if normalized in {def_normalize_package_name(row) for row in def_PARAM_HIGH_RISK_LIBS}:
        return "HIGH"
    if normalized in {def_normalize_package_name(row) for row in def_PARAM_MEDIUM_RISK_LIBS}:
        return "MEDIUM"
    return "LOW"


def def_is_via_core_whitelisted(package_name: str) -> bool:
    normalized = def_normalize_package_name(package_name)
    return normalized in {def_normalize_package_name(row) for row in def_PARAM_VIA_CORE_WHITELIST}


# ══════════════════════════════════════════════════════════════════════════════
# def PREVIOUS RECORD LOADERS
# ══════════════════════════════════════════════════════════════════════════════
def def_load_alias_map() -> Dict[str, str]:
    path_value = def_pick_first_existing_path(def_PARAM_ALIAS_JSON_CANDIDATES)
    if path_value is None:
        return {}
    payload = def_read_json_safe(path_value, {})
    return payload if isinstance(payload, dict) else {}


def def_load_library_registry_rows() -> List[Dict[str, Any]]:
    path_value = def_pick_first_existing_path(def_PARAM_REGISTRY_JSON_CANDIDATES)
    if path_value is None:
        return []
    payload = def_read_json_safe(path_value, [])
    return payload if isinstance(payload, list) else []


def def_load_route_table() -> List[Dict[str, Any]]:
    path_value = def_pick_first_existing_path(def_PARAM_ROUTE_TABLE_JSON_CANDIDATES)
    if path_value is not None:
        payload = def_read_json_safe(path_value, [])
        if isinstance(payload, list):
            return payload
    return [
        {"pattern": "VIA_IntegrationSystem.py", "alias": "via_core", "reason": "core integration entry"},
        {"pattern": "VDF_DataHub_Orchestrator.py", "alias": "via_vdf", "reason": "VDF orchestration"},
        {"pattern": "vrn_mdl_003_table_extraction_engine_v_1.py", "alias": "camelot_311", "reason": "table extraction"},
        {"pattern": "vrn_mdl_004_layout_semantic_engine_v_1.py", "alias": "paddle_311", "reason": "layout semantic"},
        {"pattern": "vrn_mdl_005_ocrtext_fusion_engine_v_1.py", "alias": "paddle_311", "reason": "ocr fusion"},
    ]


def def_build_alias_records(alias_map: Dict[str, str], env_root: Path) -> List[def_EnvAliasRecord]:
    records: List[def_EnvAliasRecord] = []
    for alias_name, env_name in alias_map.items():
        env_path = env_root / env_name
        python_exe = def_path_to_python(env_path)
        records.append(
            def_EnvAliasRecord(
                alias_name=alias_name,
                env_name=env_name,
                env_path=str(env_path),
                python_exe=str(python_exe),
            )
        )
    return records


# ══════════════════════════════════════════════════════════════════════════════
# def ENV DISCOVERY
# ══════════════════════════════════════════════════════════════════════════════
def def_scan_env_directories(env_root: Path) -> List[Path]:
    if not env_root.exists():
        return []
    env_paths: List[Path] = []
    for child in env_root.iterdir():
        if def_is_env_dir(child):
            env_paths.append(child)
    return sorted(env_paths, key=lambda p: p.name.lower())


def def_group_aliases_by_env_name(alias_map: Dict[str, str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for alias_name, env_name in alias_map.items():
        grouped.setdefault(env_name, []).append(alias_name)
    for env_name in grouped:
        grouped[env_name] = sorted(grouped[env_name])
    return grouped


def def_find_route_targets_for_alias(alias_name: str, route_table: List[Dict[str, Any]]) -> List[str]:
    targets: List[str] = []
    for row in route_table:
        row_alias = row.get("alias") or row.get("Alias")
        if row_alias == alias_name:
            pattern_value = row.get("pattern") or row.get("Pattern") or ""
            if pattern_value:
                targets.append(pattern_value)
    return def_try_accelerated_unique(targets)


# ══════════════════════════════════════════════════════════════════════════════
# def LIB PROBES
# ══════════════════════════════════════════════════════════════════════════════
def def_probe_uv_command() -> Optional[str]:
    if not def_PARAM_ENABLE_UV:
        return None
    return shutil.which("uv")


def def_probe_pip_with_python(python_exe: Path, subcommand: List[str], timeout: int = 180) -> Dict[str, Any]:
    if not python_exe.exists():
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "python missing"}
    return def_run_subprocess([str(python_exe), "-m", "pip"] + subcommand, timeout=timeout)


def def_run_uv_pip_check(python_exe: Path) -> Dict[str, Any]:
    uv_cmd = def_probe_uv_command()
    if uv_cmd is None or not python_exe.exists():
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "uv or python missing"}
    return def_run_subprocess([uv_cmd, "pip", "check", "--python", str(python_exe)], timeout=180)


def def_run_pip_check(python_exe: Path) -> Dict[str, Any]:
    return def_probe_pip_with_python(python_exe, ["check"], timeout=180)


def def_run_pip_list_json(python_exe: Path) -> List[Dict[str, Any]]:
    result = def_probe_pip_with_python(python_exe, ["list", "--format", "json"], timeout=240)
    if not result.get("ok"):
        return []
    try:
        payload = json.loads(result.get("stdout", "[]"))
        return payload if isinstance(payload, list) else []
    except Exception:
        return []


def def_probe_single_import(python_exe: Path, package_name: str) -> def_LibProbeResult:
    normalized_name = def_try_ssot_normalize_package_name(package_name)
    code = (
        "import importlib, json\n"
        f"name = {normalized_name!r}\n"
        "try:\n"
        "    mod = importlib.import_module(name)\n"
        "    print(json.dumps({'ok': True, 'version': getattr(mod, '__version__', '')}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok': False, 'error': str(e)}))\n"
    )
    if not python_exe.exists():
        return def_LibProbeResult(package_name=package_name, status="MISSING", detail="python missing")
    result = def_run_subprocess([str(python_exe), "-c", code], timeout=120)
    try:
        payload = json.loads((result.get("stdout") or "").strip() or "{}")
        if payload.get("ok"):
            return def_LibProbeResult(
                package_name=package_name,
                status="OK",
                version=payload.get("version", ""),
                detail="import ok",
                source="python-import",
            )
        return def_LibProbeResult(
            package_name=package_name,
            status="MISSING",
            detail=payload.get("error", result.get("stderr", "")),
            source="python-import",
        )
    except Exception:
        return def_LibProbeResult(
            package_name=package_name,
            status="UNKNOWN",
            detail=result.get("stderr", "parse failed"),
            source="python-import",
        )


def def_snapshot_core_libs(python_exe: Path) -> List[def_LibProbeResult]:
    return [def_probe_single_import(python_exe, package_name) for package_name in def_PARAM_SNAPSHOT_LIBS]


def def_extract_missing_core_libs(snapshot_results: List[def_LibProbeResult]) -> List[str]:
    return [row.package_name for row in snapshot_results if row.status != "OK"]


def def_extract_high_risk_found(installed_packages: List[Dict[str, Any]]) -> List[str]:
    installed_name_map = {def_normalize_package_name(str(row.get("name", ""))): row for row in installed_packages}
    found = []
    for package_name in def_PARAM_HIGH_RISK_LIBS:
        if def_normalize_package_name(package_name) in installed_name_map:
            found.append(package_name)
    return def_try_accelerated_unique(found)


def def_extract_installed_package_names(installed_packages: List[Dict[str, Any]]) -> List[str]:
    names = []
    for row in installed_packages:
        name_value = str(row.get("name", "")).strip()
        if name_value:
            names.append(def_normalize_package_name(name_value))
    return def_try_accelerated_unique(names)


# ══════════════════════════════════════════════════════════════════════════════
# def HEALTH EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
def def_choose_status(
    exists: bool,
    python_exists: bool,
    pip_check_ok: Optional[bool],
    uv_check_ok: Optional[bool],
    missing_core_libs: List[str],
    broken_reasons: List[str],
    warnings: List[str],
) -> str:
    if not exists or not python_exists:
        return def_PARAM_STATUS_BROKEN
    if broken_reasons:
        return def_PARAM_STATUS_REBUILD
    if pip_check_ok is False or uv_check_ok is False:
        return def_PARAM_STATUS_REBUILD
    if missing_core_libs or warnings:
        return def_PARAM_STATUS_WARN
    return def_PARAM_STATUS_OK


def def_build_recommended_action(status_value: str, record: def_EnvHealthRecord) -> str:
    if status_value == def_PARAM_STATUS_BROKEN:
        return "recreate_env_from_alias_or_registry"
    if status_value == def_PARAM_STATUS_REBUILD:
        return "rebuild_env_and_reinstall_locked_dependencies"
    if status_value == def_PARAM_STATUS_WARN:
        return "repair_missing_libs_and_recheck"
    if status_value == def_PARAM_STATUS_OK:
        return "keep_and_register_current_health"
    return "manual_review"


def def_assess_single_env(env_path: Path, alias_names: List[str], route_targets: List[str]) -> def_EnvHealthRecord:
    python_exe = def_path_to_python(env_path)
    pyvenv_cfg = env_path / "pyvenv.cfg"
    exists = env_path.exists()
    python_exists = python_exe.exists()
    pyvenv_cfg_exists = pyvenv_cfg.exists()

    broken_reasons: List[str] = []
    warnings: List[str] = []

    if exists and not python_exists:
        broken_reasons.append("python_exe_missing")
    if exists and not pyvenv_cfg_exists:
        warnings.append("pyvenv_cfg_missing")

    installed_packages = def_run_pip_list_json(python_exe) if python_exists else []
    installed_package_names = def_extract_installed_package_names(installed_packages)
    package_count = len(installed_packages)
    uv_check = def_run_uv_pip_check(python_exe) if python_exists else {"ok": False, "stderr": "python missing"}
    pip_check = def_run_pip_check(python_exe) if python_exists else {"ok": False, "stderr": "python missing"}

    if python_exists and pip_check.get("ok") is False:
        warnings.append("pip_check_failed")
    if python_exists and def_probe_uv_command() and uv_check.get("ok") is False:
        warnings.append("uv_pip_check_failed")

    snapshot_results = def_snapshot_core_libs(python_exe) if python_exists else []
    missing_core_libs = def_extract_missing_core_libs(snapshot_results)
    high_risk_libs_found = def_extract_high_risk_found(installed_packages)

    if len(high_risk_libs_found) >= 3:
        warnings.append("multiple_high_risk_libs_detected")
    if package_count == 0 and python_exists:
        warnings.append("empty_or_unreadable_environment")

    status_value = def_choose_status(
        exists=exists,
        python_exists=python_exists,
        pip_check_ok=pip_check.get("ok") if python_exists else None,
        uv_check_ok=uv_check.get("ok") if python_exists and def_probe_uv_command() else None,
        missing_core_libs=missing_core_libs,
        broken_reasons=broken_reasons,
        warnings=warnings,
    )

    record = def_EnvHealthRecord(
        env_name=env_path.name,
        env_path=str(env_path),
        python_exe=str(python_exe),
        alias_names=alias_names,
        exists=exists,
        python_exists=python_exists,
        pyvenv_cfg_exists=pyvenv_cfg_exists,
        package_count=package_count,
        pip_check_ok=pip_check.get("ok") if python_exists else None,
        uv_check_ok=uv_check.get("ok") if python_exists and def_probe_uv_command() else None,
        broken_reasons=broken_reasons,
        warnings=warnings,
        missing_core_libs=missing_core_libs,
        high_risk_libs_found=high_risk_libs_found,
        snapshot_libs=[asdict(row) for row in snapshot_results],
        installed_package_names=installed_package_names,
        status=status_value,
        route_targets=route_targets,
        last_scan_utc=def_now_utc_iso(),
        is_base_env=def_is_base_env_name(env_path.name),
        is_managed_env=def_is_managed_env_name(env_path.name),
    )
    record.recommended_action = def_build_recommended_action(status_value, record)
    return record


# ══════════════════════════════════════════════════════════════════════════════
# def CONFLICT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
def def_find_base_and_via_conflicts(records: List[def_EnvHealthRecord]) -> List[def_EnvConflictRecord]:
    conflicts: List[def_EnvConflictRecord] = []
    base_records = [row for row in records if row.is_base_env]
    via_records = [row for row in records if row.env_name.lower().startswith("via_")]

    if not base_records:
        conflicts.append(
            def_EnvConflictRecord(
                env_name="base",
                severity="WARN",
                category="BASE_MISSING",
                detail="base 環境未找到，無法完成 base vs via_ 衝突比對",
                related_packages=[],
            )
        )
        return conflicts

    base_record = base_records[0]
    base_package_set = set(base_record.installed_package_names)

    for via_record in via_records:
        overlap_high_risk = []
        for package_name in def_PARAM_HIGH_RISK_LIBS:
            normalized_name = def_normalize_package_name(package_name)
            if normalized_name in base_package_set and normalized_name in set(via_record.installed_package_names):
                overlap_high_risk.append(normalized_name)

        if overlap_high_risk:
            conflicts.append(
                def_EnvConflictRecord(
                    env_name=via_record.env_name,
                    severity="WARN",
                    category="BASE_VIA_HIGH_RISK_OVERLAP",
                    detail="base 與 via_ 環境同時存在高風險套件，需確認是否應隔離",
                    related_packages=sorted(overlap_high_risk),
                )
            )

        if via_record.status in [def_PARAM_STATUS_REBUILD, def_PARAM_STATUS_BROKEN]:
            conflicts.append(
                def_EnvConflictRecord(
                    env_name=via_record.env_name,
                    severity="WARN",
                    category="VIA_ENV_UNHEALTHY",
                    detail="via_ 環境狀態不健康，新增工具不可直接裝入",
                    related_packages=sorted(via_record.high_risk_libs_found),
                )
            )

    return conflicts


# ══════════════════════════════════════════════════════════════════════════════
# def COMMAND PLAN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def def_build_repair_commands(record: def_EnvHealthRecord) -> List[str]:
    commands: List[str] = []
    python_exe = record.python_exe
    if not python_exe:
        return commands

    if record.status == def_PARAM_STATUS_WARN and record.missing_core_libs:
        missing = " ".join(record.missing_core_libs[:12])
        commands.append(f'uv pip install --python "{python_exe}" {missing}')
        commands.append(f'"{python_exe}" -m pip install {missing}')

    if record.status == def_PARAM_STATUS_REBUILD:
        commands.append(f'# REBUILD SUGGESTION for {record.env_name}')
        commands.append(f'Remove-Item -LiteralPath "{record.env_path}" -Recurse -Force')
        commands.append(f'python -m venv "{record.env_path}"')
        commands.append(f'"{python_exe}" -m pip install --upgrade pip setuptools wheel')

    if record.status == def_PARAM_STATUS_BROKEN:
        commands.append(f'# BROKEN ENV: {record.env_name}')
        commands.append(f'python -m venv "{record.env_path}"')

    commands.append(f'"{python_exe}" -m pip check')
    if def_probe_uv_command():
        commands.append(f'uv pip check --python "{python_exe}"')
    return commands


def def_build_gatekeeper_install_commands(target_python: str, package_expr: str) -> Dict[str, Any]:
    uv_cmd = def_probe_uv_command()
    powershell_commands = []
    executable_commands: List[List[str]] = []

    if uv_cmd:
        powershell_commands.append(f'uv pip install --python "{target_python}" {package_expr}')
        powershell_commands.append(f'uv pip check --python "{target_python}"')
        executable_commands.append([uv_cmd, "pip", "install", "--python", target_python, package_expr])
        executable_commands.append([uv_cmd, "pip", "check", "--python", target_python])

    powershell_commands.append(f'& "{target_python}" -m pip install {package_expr}')
    powershell_commands.append(f'& "{target_python}" -m pip check')

    python_commands = [
        f'"{target_python}" -m pip install {package_expr}',
        f'"{target_python}" -m pip check',
    ]
    executable_commands.append([target_python, "-m", "pip", "install", package_expr])
    executable_commands.append([target_python, "-m", "pip", "check"])

    return {
        "powershell_commands": powershell_commands,
        "python_commands": python_commands,
        "executable_commands": executable_commands,
    }


def def_build_gatekeeper_rebuild_commands(record: Dict[str, Any]) -> List[str]:
    env_path = str(record.get("env_path", ""))
    python_exe = str(record.get("python_exe", ""))
    commands = [
        f'Remove-Item -LiteralPath "{env_path}" -Recurse -Force',
        f'python -m venv "{env_path}"',
    ]
    if python_exe:
        commands.append(f'& "{python_exe}" -m pip install --upgrade pip setuptools wheel')
    return commands


def def_build_command_plan(records: List[def_EnvHealthRecord]) -> Dict[str, Any]:
    return {
        "generated_at_utc": def_now_utc_iso(),
        "items": [
            {
                "env_name": record.env_name,
                "status": record.status,
                "recommended_action": record.recommended_action,
                "commands": def_build_repair_commands(record),
            }
            for record in records
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# def STATE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def def_build_envmanager_state() -> def_EnvManagerState:
    env_root = def_find_env_root()
    alias_map = def_load_alias_map()
    registry_rows = def_load_library_registry_rows()
    route_table = def_load_route_table()
    alias_group_map = def_group_aliases_by_env_name(alias_map)

    env_paths = def_scan_env_directories(env_root)
    known_names = {path_value.name for path_value in env_paths}
    for env_name in alias_group_map.keys():
        if env_name not in known_names:
            env_paths.append(env_root / env_name)
    env_paths = sorted(env_paths, key=lambda p: p.name.lower())

    env_records: List[def_EnvHealthRecord] = []
    for env_path in env_paths:
        alias_names = alias_group_map.get(env_path.name, [])
        route_targets: List[str] = []
        for alias_name in alias_names:
            route_targets.extend(def_find_route_targets_for_alias(alias_name, route_table))
        route_targets = def_try_accelerated_unique(route_targets)
        env_records.append(def_assess_single_env(env_path, alias_names, route_targets))

    conflicts = def_find_base_and_via_conflicts(env_records)
    return def_EnvManagerState(
        module_id=def_PARAM_MODULE_ID,
        version=def_PARAM_MODULE_VERSION,
        created_at_utc=def_now_utc_iso(),
        updated_at_utc=def_now_utc_iso(),
        env_root=str(env_root),
        alias_map=alias_map,
        route_table=route_table,
        registry_rows=registry_rows,
        envs=[asdict(row) for row in env_records],
        conflicts=[asdict(row) for row in conflicts],
    )


# ══════════════════════════════════════════════════════════════════════════════
# def SAVE / REPORT
# ══════════════════════════════════════════════════════════════════════════════
def def_save_state(state_obj: def_EnvManagerState) -> None:
    def_write_json(def_PARAM_SSOT_JSON, asdict(state_obj))
    def_write_json(def_PARAM_HEALTH_JSON, {"envs": state_obj.envs, "updated_at_utc": state_obj.updated_at_utc})
    def_write_json(def_PARAM_CONFLICT_JSON, {"conflicts": state_obj.conflicts, "updated_at_utc": state_obj.updated_at_utc})
    if def_PARAM_ENABLE_HISTORY:
        def_append_jsonl(
            def_PARAM_HISTORY_JSONL,
            {
                "event": "ENV_SCAN",
                "module_id": state_obj.module_id,
                "version": state_obj.version,
                "updated_at_utc": state_obj.updated_at_utc,
                "env_count": len(state_obj.envs),
                "conflict_count": len(state_obj.conflicts),
                "host": def_get_hostname(),
                "state_hash": def_hash_text(json.dumps(asdict(state_obj), ensure_ascii=False, sort_keys=True)),
            },
        )


def def_build_summary(state_obj: def_EnvManagerState) -> Dict[str, Any]:
    summary = {
        "total_envs": len(state_obj.envs),
        "ok": 0,
        "warn": 0,
        "rebuild": 0,
        "broken": 0,
        "unknown": 0,
        "conflicts": len(state_obj.conflicts),
        "base_envs": 0,
        "via_envs": 0,
    }
    for row in state_obj.envs:
        status_value = str(row.get("status", def_PARAM_STATUS_UNKNOWN)).lower()
        if status_value in summary:
            summary[status_value] += 1
        else:
            summary["unknown"] += 1
        if row.get("is_base_env") is True:
            summary["base_envs"] += 1
        if str(row.get("env_name", "")).lower().startswith("via_"):
            summary["via_envs"] += 1
    return summary


def def_render_html_report(state_obj: def_EnvManagerState) -> str:
    summary = def_build_summary(state_obj)
    rows_html = []
    for row in state_obj.envs:
        rows_html.append(
            "<tr>"
            f"<td>{row.get('env_name','')}</td>"
            f"<td>{row.get('status','')}</td>"
            f"<td>{', '.join(row.get('alias_names', []))}</td>"
            f"<td>{row.get('package_count', 0)}</td>"
            f"<td>{row.get('pip_check_ok')}</td>"
            f"<td>{row.get('uv_check_ok')}</td>"
            f"<td>{', '.join(row.get('missing_core_libs', []))}</td>"
            f"<td>{', '.join(row.get('high_risk_libs_found', []))}</td>"
            f"<td>{row.get('recommended_action','')}</td>"
            "</tr>"
        )

    conflict_rows_html = []
    for row in state_obj.conflicts:
        conflict_rows_html.append(
            "<tr>"
            f"<td>{row.get('env_name','')}</td>"
            f"<td>{row.get('severity','')}</td>"
            f"<td>{row.get('category','')}</td>"
            f"<td>{row.get('detail','')}</td>"
            f"<td>{', '.join(row.get('related_packages', []))}</td>"
            "</tr>"
        )

    html_value = f"""
<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
<meta charset=\"utf-8\" />
<title>VIA EnvManager Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f8fb; color: #1f2937; }}
.card {{ background: #ffffff; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef2ff; }}
</style>
</head>
<body>
<div class=\"card\">
<h1>VIA_EnvManager</h1>
<p><strong>Version:</strong> {state_obj.version}</p>
<p><strong>Env Root:</strong> {state_obj.env_root}</p>
<p><strong>Total Envs:</strong> {summary['total_envs']}</p>
<p><strong>Base Envs:</strong> {summary['base_envs']} | <strong>via_ Envs:</strong> {summary['via_envs']}</p>
<p><strong>OK:</strong> {summary['ok']} | <strong>WARN:</strong> {summary['warn']} | <strong>REBUILD:</strong> {summary['rebuild']} | <strong>BROKEN:</strong> {summary['broken']}</p>
<p><strong>Conflicts:</strong> {summary['conflicts']}</p>
</div>
<div class=\"card\">
<h2>Environment Health</h2>
<table>
<thead>
<tr>
<th>Env</th>
<th>Status</th>
<th>Aliases</th>
<th>Packages</th>
<th>pip check</th>
<th>uv check</th>
<th>Missing Core Libs</th>
<th>High Risk Libs</th>
<th>Recommended Action</th>
</tr>
</thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>
</div>
<div class=\"card\">
<h2>Base vs via_ Conflicts</h2>
<table>
<thead>
<tr>
<th>Env</th>
<th>Severity</th>
<th>Category</th>
<th>Detail</th>
<th>Related Packages</th>
</tr>
</thead>
<tbody>
{''.join(conflict_rows_html)}
</tbody>
</table>
</div>
</body>
</html>
""".strip()
    def_PARAM_HTML_REPORT.write_text(html_value, encoding="utf-8")
    return html_value


# ══════════════════════════════════════════════════════════════════════════════
# def INSTALL GOVERNANCE
# ══════════════════════════════════════════════════════════════════════════════
def def_choose_target_env_for_package(package_name: str, preferred_env: str = "", allow_base: bool = False) -> Dict[str, Any]:
    normalized_package_name = def_normalize_package_name(package_name)
    risk_level = def_get_package_risk_level(package_name)
    state_obj = def_build_envmanager_state()
    env_rows = state_obj.envs

    if preferred_env:
        preferred = next((row for row in env_rows if str(row.get("env_name", "")).lower() == preferred_env.lower()), None)
        if preferred is not None:
            return {"ok": True, "env_name": preferred.get("env_name"), "reason": "preferred_env", "record": preferred, "risk_level": risk_level}

    if risk_level in def_PARAM_BASE_BLOCK_RISK_LEVELS and not allow_base:
        for env_name, hints in def_PARAM_ENV_PURPOSE_HINTS.items():
            if normalized_package_name in {def_normalize_package_name(row) for row in hints}:
                matched = next((row for row in env_rows if str(row.get("env_name", "")).lower() == env_name.lower()), None)
                if matched is not None and matched.get("status") in [def_PARAM_STATUS_OK, def_PARAM_STATUS_WARN]:
                    return {"ok": True, "env_name": matched.get("env_name"), "reason": "purpose_routed_env", "record": matched, "risk_level": risk_level}

    if risk_level == "HIGH":
        for row in env_rows:
            if str(row.get("env_name", "")).lower().startswith("via_") and row.get("status") in [def_PARAM_STATUS_OK, def_PARAM_STATUS_WARN]:
                return {"ok": True, "env_name": row.get("env_name"), "reason": "high_risk_isolated_to_via_env", "record": row, "risk_level": risk_level}

    if normalized_package_name and def_is_via_core_whitelisted(normalized_package_name):
        for row in env_rows:
            if str(row.get("env_name", "")).lower() == "via_core" and row.get("status") == def_PARAM_STATUS_OK:
                return {"ok": True, "env_name": row.get("env_name"), "reason": "via_core_whitelist", "record": row, "risk_level": risk_level}

    if allow_base and risk_level == "LOW":
        for row in env_rows:
            if row.get("is_base_env") is True and row.get("status") == def_PARAM_STATUS_OK:
                return {"ok": True, "env_name": row.get("env_name"), "reason": "base_allowed_and_low_risk", "record": row, "risk_level": risk_level}

    for row in env_rows:
        if str(row.get("env_name", "")).lower().startswith("via_") and row.get("status") == def_PARAM_STATUS_OK:
            return {"ok": True, "env_name": row.get("env_name"), "reason": "default_healthy_via_env", "record": row, "risk_level": risk_level}

    return {"ok": False, "error": "NO_HEALTHY_MANAGED_ENV_AVAILABLE", "package_name": package_name, "risk_level": risk_level}


def def_plan_install_request(package_name: str, requested_version: str = "", reason: str = "", preferred_env: str = "", allow_base: bool = False) -> Dict[str, Any]:
    risk_level = def_get_package_risk_level(package_name)
    request_obj = def_InstallRequest(
        package_name=package_name,
        requested_version=requested_version,
        reason=reason,
        requested_by=def_PARAM_OWNER,
        requested_at_utc=def_now_utc_iso(),
        preferred_env=preferred_env,
        allow_base=allow_base,
        risk_level=risk_level,
    )
    env_decision = def_choose_target_env_for_package(package_name, preferred_env=preferred_env, allow_base=allow_base)

    blocked_reason = ""
    approved = False
    target_env = ""
    target_python = ""
    strategy = ""
    command_payload: Dict[str, Any] = {"powershell_commands": [], "python_commands": [], "executable_commands": []}

    if env_decision.get("ok"):
        record = env_decision.get("record", {})
        target_env = str(record.get("env_name", ""))
        target_python = str(record.get("python_exe", ""))
        if str(target_env).lower() == "base" and risk_level in def_PARAM_BASE_BLOCK_RISK_LEVELS and not allow_base:
            blocked_reason = "BASE_BLOCKED_FOR_MEDIUM_HIGH_RISK"
        elif str(target_env).lower() == "via_core" and not def_is_via_core_whitelisted(package_name) and risk_level != "LOW":
            blocked_reason = "VIA_CORE_ONLY_WHITELIST_ALLOWED"
        elif not target_python:
            blocked_reason = "TARGET_PYTHON_MISSING"
        elif record.get("status") in [def_PARAM_STATUS_REBUILD, def_PARAM_STATUS_BROKEN]:
            blocked_reason = "TARGET_ENV_UNHEALTHY"
        else:
            approved = True
            package_expr = package_name + (requested_version if requested_version else "")
            command_payload = def_build_gatekeeper_install_commands(target_python, package_expr)
            strategy = str(env_decision.get("reason", ""))
    else:
        blocked_reason = env_decision.get("error", "NO_ENV_DECISION")

    decision_obj = def_InstallDecision(
        package_name=package_name,
        normalized_package_name=def_normalize_package_name(package_name),
        risk_level=risk_level,
        approved=approved,
        blocked_reason=blocked_reason,
        target_env=target_env,
        target_python=target_python,
        strategy=strategy,
        powershell_commands=command_payload["powershell_commands"],
        python_commands=command_payload["python_commands"],
        executable_commands=command_payload["executable_commands"],
    )

    decision_payload = {"request": asdict(request_obj), "env_decision": env_decision, "decision": asdict(decision_obj)}
    def_append_jsonl(def_PARAM_INSTALL_REQUEST_JSON, asdict(request_obj))
    def_write_json(def_PARAM_INSTALL_DECISION_JSON, decision_payload)
    def_write_json(def_PARAM_INSTALL_PLAN_JSON, {"generated_at_utc": def_now_utc_iso(), "items": [decision_payload]})
    return decision_payload


def def_execute_install_request(package_name: str, requested_version: str = "", reason: str = "", preferred_env: str = "", allow_base: bool = False, executor: str = "uv") -> Dict[str, Any]:
    decision = def_plan_install_request(
        package_name=package_name,
        requested_version=requested_version,
        reason=reason,
        preferred_env=preferred_env,
        allow_base=allow_base,
    )
    decision_row = decision.get("decision", {})
    if not decision_row.get("approved"):
        return decision
    if not def_PARAM_ENABLE_EXEC:
        decision["executed"] = False
        decision["execution_error"] = "EXEC_DISABLED"
        return decision

    executable_commands: List[List[str]] = decision_row.get("executable_commands", [])
    result_rows: List[Dict[str, Any]] = []
    if executor == "uv":
        selected_commands = executable_commands
    else:
        selected_commands = [row for row in executable_commands if len(row) >= 3 and row[1:3] == ["-m", "pip"]]
        if len(selected_commands) > 2:
            selected_commands = selected_commands[-2:]

    for command in selected_commands:
        result_rows.append(def_run_subprocess(command, timeout=1800))
        if result_rows[-1].get("ok") is False:
            break

    decision["executed"] = True
    decision["execution_results"] = result_rows
    decision["execution_result"] = result_rows[-1] if result_rows else {"ok": False, "stderr": "NO_COMMAND_EXECUTED"}
    def_write_json(def_PARAM_INSTALL_DECISION_JSON, decision)
    return decision


# ══════════════════════════════════════════════════════════════════════════════
# def HIGH LEVEL API
# ══════════════════════════════════════════════════════════════════════════════
def def_scan_all_envs() -> Dict[str, Any]:
    def_ensure_output_dir()
    state_obj = def_build_envmanager_state()
    state_obj.updated_at_utc = def_now_utc_iso()
    def_save_state(state_obj)
    def_render_html_report(state_obj)
    command_plan = def_build_command_plan([def_EnvHealthRecord(**row) for row in state_obj.envs])
    def_write_json(def_PARAM_COMMAND_PLAN_JSON, command_plan)
    return {
        "ok": True,
        "summary": def_build_summary(state_obj),
        "ssot_json": str(def_PARAM_SSOT_JSON),
        "health_json": str(def_PARAM_HEALTH_JSON),
        "conflict_json": str(def_PARAM_CONFLICT_JSON),
        "html_report": str(def_PARAM_HTML_REPORT),
        "command_plan_json": str(def_PARAM_COMMAND_PLAN_JSON),
        "env_count": len(state_obj.envs),
        "conflict_count": len(state_obj.conflicts),
    }


def def_get_env_by_name(env_name: str) -> Dict[str, Any]:
    state_obj = def_build_envmanager_state()
    for row in state_obj.envs:
        if row.get("env_name", "").lower() == env_name.lower():
            return {"ok": True, "record": row}
    return {"ok": False, "error": "ENV_NOT_FOUND", "env_name": env_name}


def def_get_env_by_alias(alias_name: str) -> Dict[str, Any]:
    state_obj = def_build_envmanager_state()
    target_env_name = state_obj.alias_map.get(alias_name)
    if not target_env_name:
        return {"ok": False, "error": "ALIAS_NOT_FOUND", "alias_name": alias_name}
    return def_get_env_by_name(target_env_name)


def def_get_rebuild_candidates() -> Dict[str, Any]:
    state_obj = def_build_envmanager_state()
    rows = [row for row in state_obj.envs if row.get("status") in [def_PARAM_STATUS_REBUILD, def_PARAM_STATUS_BROKEN]]
    return {"ok": True, "items": rows, "count": len(rows)}


def def_export_command_plan() -> Dict[str, Any]:
    state_obj = def_build_envmanager_state()
    records = [def_EnvHealthRecord(**row) for row in state_obj.envs]
    payload = def_build_command_plan(records)
    def_write_json(def_PARAM_COMMAND_PLAN_JSON, payload)
    return {"ok": True, "path": str(def_PARAM_COMMAND_PLAN_JSON), "items": len(payload.get("items", []))}


def def_get_base_via_conflicts() -> Dict[str, Any]:
    state_obj = def_build_envmanager_state()
    return {"ok": True, "count": len(state_obj.conflicts), "items": state_obj.conflicts, "path": str(def_PARAM_CONFLICT_JSON)}


# ══════════════════════════════════════════════════════════════════════════════
# def SELF TESTS
# ══════════════════════════════════════════════════════════════════════════════
def def_test_is_env_dir() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        env_dir = root / "via_core"
        env_dir.mkdir(parents=True, exist_ok=True)
        (env_dir / "pyvenv.cfg").write_text("home=C:/Python313\n", encoding="utf-8")
        assert def_is_env_dir(env_dir) is True


def def_test_group_aliases_by_env_name() -> None:
    grouped = def_group_aliases_by_env_name({"via_core": "envA", "paddle_311": "envB", "via_vdf": "envA"})
    assert grouped["envA"] == ["via_core", "via_vdf"]
    assert grouped["envB"] == ["paddle_311"]


def def_test_choose_status() -> None:
    assert def_choose_status(True, True, True, True, [], [], []) == def_PARAM_STATUS_OK
    assert def_choose_status(True, False, None, None, [], ["python_exe_missing"], []) == def_PARAM_STATUS_BROKEN


def def_test_build_repair_commands() -> None:
    record = def_EnvHealthRecord(
        env_name="via_test",
        env_path="C:/Users/tonyk/envs/via_test",
        python_exe="C:/Users/tonyk/envs/via_test/Scripts/python.exe",
        status=def_PARAM_STATUS_WARN,
        missing_core_libs=["requests", "duckdb"],
        recommended_action="repair_missing_libs_and_recheck",
    )
    commands = def_build_repair_commands(record)
    assert any("requests" in row for row in commands)
    assert any("pip check" in row for row in commands)


def def_test_choose_target_env_for_package_rejects_when_no_env() -> None:
    original_builder = globals()["def_build_envmanager_state"]
    try:
        def _fake_builder() -> def_EnvManagerState:
            return def_EnvManagerState(
                module_id=def_PARAM_MODULE_ID,
                version=def_PARAM_MODULE_VERSION,
                created_at_utc=def_now_utc_iso(),
                updated_at_utc=def_now_utc_iso(),
                env_root="X",
                alias_map={},
                route_table=[],
                registry_rows=[],
                envs=[],
                conflicts=[],
            )
        globals()["def_build_envmanager_state"] = _fake_builder
        result = def_choose_target_env_for_package("torch")
        assert result["ok"] is False
    finally:
        globals()["def_build_envmanager_state"] = original_builder


def def_test_normalize_package_name() -> None:
    assert def_normalize_package_name("opencv_python") == "opencv-python"


def def_test_package_risk_level() -> None:
    assert def_get_package_risk_level("torch") == "HIGH"
    assert def_get_package_risk_level("duckdb") == "MEDIUM"
    assert def_get_package_risk_level("rich") == "LOW"


def def_test_via_core_whitelist() -> None:
    assert def_is_via_core_whitelisted("requests") is True
    assert def_is_via_core_whitelisted("torch") is False


def def_test_install_command_builder_returns_structured_commands() -> None:
    payload = def_build_gatekeeper_install_commands("C:/envs/via_core/Scripts/python.exe", "duckdb==1.1.3")
    assert payload["powershell_commands"]
    assert payload["python_commands"]
    assert payload["executable_commands"]
    assert payload["executable_commands"][-1][-2:] == ["pip", "check"]


def def_test_execute_install_request_stops_on_first_failure() -> None:
    original_plan = globals()["def_plan_install_request"]
    original_run = globals()["def_run_subprocess"]
    try:
        def _fake_plan(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            return {
                "decision": {
                    "approved": True,
                    "executable_commands": [
                        ["python", "-m", "pip", "install", "x"],
                        ["python", "-m", "pip", "check"],
                    ]
                }
            }
        def _fake_run(command: List[str], timeout: int = 120) -> Dict[str, Any]:
            if command[-1] == "x":
                return {"ok": False, "returncode": 1, "stdout": "", "stderr": "install failed", "command": command}
            return {"ok": True, "returncode": 0, "stdout": "", "stderr": "", "command": command}
        globals()["def_plan_install_request"] = _fake_plan
        globals()["def_run_subprocess"] = _fake_run
        result = def_execute_install_request("x")
        assert result["executed"] is True
        assert len(result["execution_results"]) == 1
        assert result["execution_results"][0]["ok"] is False
    finally:
        globals()["def_plan_install_request"] = original_plan
        globals()["def_run_subprocess"] = original_run


def def_run_self_tests() -> Dict[str, Any]:
    tests = [
        def_test_is_env_dir,
        def_test_group_aliases_by_env_name,
        def_test_choose_status,
        def_test_build_repair_commands,
        def_test_choose_target_env_for_package_rejects_when_no_env,
        def_test_normalize_package_name,
        def_test_package_risk_level,
        def_test_via_core_whitelist,
        def_test_install_command_builder_returns_structured_commands,
        def_test_execute_install_request_stops_on_first_failure,
    ]
    passed: List[str] = []
    failed: List[Dict[str, str]] = []
    for test_func in tests:
        try:
            test_func()
            passed.append(test_func.__name__)
        except Exception as exc:
            failed.append({
                "test": test_func.__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            })
    return {"ok": len(failed) == 0, "passed": passed, "failed": failed, "total": len(tests)}


# ══════════════════════════════════════════════════════════════════════════════
# def CLI
# ══════════════════════════════════════════════════════════════════════════════
def def_print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def def_main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    command = argv[0] if argv else "scan"

    if command in ["scan", "status"]:
        def_print_json(def_scan_all_envs())
        return 0
    if command == "env":
        def_print_json(def_get_env_by_name(argv[1] if len(argv) > 1 else ""))
        return 0
    if command == "alias":
        def_print_json(def_get_env_by_alias(argv[1] if len(argv) > 1 else ""))
        return 0
    if command == "rebuild-candidates":
        def_print_json(def_get_rebuild_candidates())
        return 0
    if command == "conflicts":
        def_print_json(def_get_base_via_conflicts())
        return 0
    if command == "plan-install":
        package_name = argv[1] if len(argv) > 1 else ""
        requested_version = argv[2] if len(argv) > 2 else ""
        preferred_env = argv[3] if len(argv) > 3 else ""
        def_print_json(def_plan_install_request(package_name, requested_version=requested_version, preferred_env=preferred_env))
        return 0
    if command == "execute-install":
        package_name = argv[1] if len(argv) > 1 else ""
        requested_version = argv[2] if len(argv) > 2 else ""
        preferred_env = argv[3] if len(argv) > 3 else ""
        def_print_json(def_execute_install_request(package_name, requested_version=requested_version, preferred_env=preferred_env))
        return 0
    if command == "export-plan":
        def_print_json(def_export_command_plan())
        return 0
    if command == "selftest":
        def_print_json(def_run_self_tests())
        return 0

    def_print_json({
        "ok": False,
        "error": "UNKNOWN_COMMAND",
        "supported": [
            "scan",
            "status",
            "env <env_name>",
            "alias <alias_name>",
            "rebuild-candidates",
            "conflicts",
            "plan-install <package> [version_suffix] [preferred_env]",
            "execute-install <package> [version_suffix] [preferred_env]",
            "export-plan",
            "selftest",
            "Gatekeeper Rules: base blocks MEDIUM/HIGH risk; via_core whitelist only; new tools must pass EnvManager first",
        ],
        "received": command,
    })
    return 1


def def_run_cli() -> None:
    exit_code = def_main()
    if exit_code != 0:
        print(f"[VIA_EnvManager] exit_code={exit_code}", file=sys.stderr)


if __name__ == "__main__":
    def_run_cli()
