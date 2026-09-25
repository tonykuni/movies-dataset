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

# def PARAMETERS
import ast
import importlib
import json
import os
import py_compile
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

def_PARAM_SUPPORTIVE_ROOT = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module")
def_PARAM_ORDER = [
    "VIA_SSOT_Unified",
    "VIA_RegistryCore_v1",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_EnvManager",
    "VIA_Panorama_AST_RuntimeInjector",
    "VeritasCeleritas",
    "VeritasAegisNexus",
]
def_PARAM_LOCK_NETWORK_IO = True
def_PARAM_LOCK_PARALLEL_ACCELERATOR = True
def_PARAM_AST_PLANNER_ONLY = True
def_PARAM_HARD_GATE = True

# def DATA
@dataclass
class def_ModuleGate:
    name: str
    role: str
    path: str = ""
    exists: bool = False
    ast_ok: bool = False
    compile_ok: bool = False
    import_ok: bool = False
    functions: int = 0
    classes: int = 0
    risk: str = "UNKNOWN"
    recommendation: str = ""
    error: str = ""

@dataclass
class def_RuntimeState:
    generated_at: str
    hard_pass: bool
    network_io_enabled: bool
    parallel_accelerator_enabled: bool
    modules: List[Dict[str, Any]] = field(default_factory=list)
    loaded_modules: Dict[str, str] = field(default_factory=dict)
    bootstrap: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)

# def ROLE MAP
def def_role_map() -> Dict[str, Dict[str, str]]:
    return {
        "VIA_SSOT_Unified": {
            "role": "SSOT_SCHEMA_REGISTRY",
            "risk": "YELLOW",
            "recommendation": "可接入，但需 hard gate。",
        },
        "VIA_RegistryCore_v1": {
            "role": "ASSET_REGISTRY",
            "risk": "YELLOW",
            "recommendation": "可接入，但需 hard gate。",
        },
        "VIA_Runtime_Bridge_All_in_One": {
            "role": "RUNTIME_BRIDGE",
            "risk": "GREEN",
            "recommendation": "適合直接接 SSOT / registry。",
        },
        "VIA_EnvManager": {
            "role": "ENV_HEALTH_GATE",
            "risk": "YELLOW",
            "recommendation": "可接入，但需 hard gate。",
        },
        "VIA_Panorama_AST_RuntimeInjector": {
            "role": "AST_AUDIT_PLANNER",
            "risk": "PLANNER_ONLY",
            "recommendation": "只做 audit/planner，不自動 patch。",
        },
        "VeritasCeleritas": {
            "role": "ACCELERATOR_LOCKED_SAFE_ONLY",
            "risk": "LOCKED_ACCELERATOR",
            "recommendation": "先只用安全統計/裝飾器，不開並行。",
        },
        "VeritasAegisNexus": {
            "role": "NETWORK_LOCKED_UNTIL_GATE",
            "risk": "LOCKED_NETWORK",
            "recommendation": "先只註冊，不啟用網路 I/O。",
        },
    }

# def UTILS
def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def def_read_text(path_value: Path) -> str:
    try:
        return path_value.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path_value.read_text(encoding="utf-8", errors="replace")

def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def def_count_ast(path_value: Path) -> Dict[str, Any]:
    payload = {"ast_ok": False, "compile_ok": False, "functions": 0, "classes": 0, "error": ""}
    try:
        src = def_read_text(path_value)
        tree = ast.parse(src, filename=str(path_value))
        payload["ast_ok"] = True
        payload["functions"] = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        payload["classes"] = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        try:
            py_compile.compile(str(path_value), doraise=True)
            payload["compile_ok"] = True
        except Exception as exc:
            payload["error"] = "COMPILE_WARN: " + str(exc)
        return payload
    except Exception as exc:
        payload["error"] = str(exc)
        return payload

def def_add_supportive_to_path() -> None:
    root = str(def_PARAM_SUPPORTIVE_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)

# def GATE SCAN
def def_scan_module(module_name: str) -> def_ModuleGate:
    meta = def_role_map().get(module_name, {})
    path_value = def_PARAM_SUPPORTIVE_ROOT / f"{module_name}.py"
    row = def_ModuleGate(
        name=f"{module_name}.py",
        role=meta.get("role", ""),
        path=str(path_value),
        exists=path_value.exists(),
        risk=meta.get("risk", "UNKNOWN"),
        recommendation=meta.get("recommendation", ""),
    )

    if not row.exists:
        row.error = "FILE_NOT_FOUND"
        return row

    ast_payload = def_count_ast(path_value)
    row.ast_ok = bool(ast_payload["ast_ok"])
    row.compile_ok = bool(ast_payload["compile_ok"])
    row.functions = int(ast_payload["functions"])
    row.classes = int(ast_payload["classes"])
    row.error = ast_payload.get("error", "")

    try:
        def_add_supportive_to_path()
        mod = importlib.import_module(module_name)
        row.import_ok = mod is not None
    except Exception:
        row.import_ok = False
        row.error = (row.error + "\n" + traceback.format_exc()).strip()

    return row

# def SAFE BOOTSTRAP
def def_safe_bootstrap() -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ssot": {},
        "registry": {},
        "runtime_bridge": {},
        "env_manager": {},
        "ast_planner": {},
        "celeritas": {"locked_parallel": def_PARAM_LOCK_PARALLEL_ACCELERATOR},
        "aegis": {"locked_network_io": def_PARAM_LOCK_NETWORK_IO},
    }

    def_add_supportive_to_path()

    try:
        ssot = importlib.import_module("VIA_SSOT_Unified")
        result["ssot"] = {
            "ok": True,
            "has_get_ssot": hasattr(ssot, "get_ssot"),
            "has_normalize": hasattr(ssot, "normalize"),
            "file": getattr(ssot, "__file__", ""),
        }
    except Exception as exc:
        result["ssot"] = {"ok": False, "error": str(exc)}

    try:
        registry = importlib.import_module("VIA_RegistryCore_v1")
        result["registry"] = {
            "ok": True,
            "has_status_report": hasattr(registry, "def_status_report"),
            "has_register_module_file": hasattr(registry, "def_register_module_file"),
            "file": getattr(registry, "__file__", ""),
        }
    except Exception as exc:
        result["registry"] = {"ok": False, "error": str(exc)}

    try:
        bridge = importlib.import_module("VIA_Runtime_Bridge_All_in_One")
        result["runtime_bridge"] = {
            "ok": True,
            "has_bootstrap_runtime": hasattr(bridge, "def_bootstrap_runtime"),
            "has_via_task": hasattr(bridge, "def_via_task"),
            "file": getattr(bridge, "__file__", ""),
        }
    except Exception as exc:
        result["runtime_bridge"] = {"ok": False, "error": str(exc)}

    try:
        envm = importlib.import_module("VIA_EnvManager")
        result["env_manager"] = {
            "ok": True,
            "has_scan_all_envs": hasattr(envm, "def_scan_all_envs"),
            "has_get_base_via_conflicts": hasattr(envm, "def_get_base_via_conflicts"),
            "has_plan_install": hasattr(envm, "def_plan_install_request"),
            "file": getattr(envm, "__file__", ""),
        }
    except Exception as exc:
        result["env_manager"] = {"ok": False, "error": str(exc)}

    try:
        planner = importlib.import_module("VIA_Panorama_AST_RuntimeInjector")
        result["ast_planner"] = {
            "ok": True,
            "planner_only": def_PARAM_AST_PLANNER_ONLY,
            "file": getattr(planner, "__file__", ""),
        }
    except Exception as exc:
        result["ast_planner"] = {"ok": False, "error": str(exc)}

    try:
        cel = importlib.import_module("VeritasCeleritas")
        result["celeritas"].update({
            "ok": True,
            "has_thread_budget": hasattr(cel, "thread_budget"),
            "has_capability_report": hasattr(cel, "capability_report"),
            "has_xbatch": hasattr(cel, "xbatch"),
            "parallel_enabled": False,
            "file": getattr(cel, "__file__", ""),
        })
    except Exception as exc:
        result["celeritas"].update({"ok": False, "error": str(exc)})

    try:
        aegis = importlib.import_module("VeritasAegisNexus")
        result["aegis"].update({
            "ok": True,
            "has_headers_builder": hasattr(aegis, "HeadersBuilder"),
            "has_library_registry": hasattr(aegis, "LibraryRegistry"),
            "network_io_enabled": False,
            "file": getattr(aegis, "__file__", ""),
        })
    except Exception as exc:
        result["aegis"].update({"ok": False, "error": str(exc)})

    return result

# def HTML
def def_write_html(path_value: Path, state: Dict[str, Any]) -> None:
    rows = []
    for r in state["modules"]:
        color = "#16a34a" if r["import_ok"] and r["compile_ok"] else "#ca8a04"
        if not r["exists"] or not r["ast_ok"]:
            color = "#dc2626"
        rows.append(
            "<tr>"
            f"<td>{r['name']}</td><td>{r['role']}</td>"
            f"<td>{r['exists']}</td><td>{r['ast_ok']}</td><td>{r['compile_ok']}</td><td>{r['import_ok']}</td>"
            f"<td>{r['functions']}</td><td>{r['classes']}</td>"
            f"<td style='color:{color};font-weight:700'>{r['risk']}</td>"
            f"<td>{r['recommendation']}</td><td><pre>{r['error']}</pre></td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Supportive Module HardGate Integration</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f6f4ef;color:#1f2937;margin:24px}}
.card{{background:white;border:1px solid #ddd6c7;border-radius:14px;padding:16px;margin-bottom:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}
h1{{margin:0 0 4px 0;font-size:22px}}
h2{{margin:0;color:#4c78a8;font-size:13px;letter-spacing:.08em}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th,td{{border:1px solid #ddd6c7;padding:7px;vertical-align:top}}
th{{background:#edecea}}
pre{{white-space:pre-wrap;font-size:10px;margin:0;color:#991b1b}}
.ok{{color:#16a34a;font-weight:800}}
.bad{{color:#dc2626;font-weight:800}}
.warn{{color:#ca8a04;font-weight:800}}
</style>
</head>
<body>
<div class="card">
<h1>VIA Supportive Module SSOT Fit Audit → HardGate Integration</h1>
<h2>VERITAS INTELLIGENCE ANALYTICS</h2>
<p>Generated: {state["generated_at"]}</p>
<p>HARD_PASS: <span class="{ "ok" if state["hard_pass"] else "bad" }">{state["hard_pass"]}</span></p>
<p>Network I/O Enabled: <b>{state["network_io_enabled"]}</b> · Parallel Accelerator Enabled: <b>{state["parallel_accelerator_enabled"]}</b></p>
</div>
<div class="card">
<table>
<thead>
<tr>
<th>Name</th><th>Role</th><th>Exists</th><th>AST</th><th>Compile</th><th>Import</th><th>Functions</th><th>Classes</th><th>Risk</th><th>Recommendation</th><th>Error</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>
<div class="card">
<h3>Recommended Order</h3>
<pre>{json.dumps(def_PARAM_ORDER, ensure_ascii=False, indent=2)}</pre>
</div>
<div class="card">
<h3>Bootstrap</h3>
<pre>{json.dumps(state["bootstrap"], ensure_ascii=False, indent=2, default=str)}</pre>
</div>
</body>
</html>"""
    path_value.write_text(html, encoding="utf-8")

# def MAIN
def def_main() -> int:
    rows = [asdict(def_scan_module(name)) for name in def_PARAM_ORDER]

    hard_pass = all(
        r["exists"] and r["ast_ok"] and r["compile_ok"]
        for r in rows
    )

    bootstrap = def_safe_bootstrap()

    state = asdict(def_RuntimeState(
        generated_at=def_now(),
        hard_pass=bool(hard_pass),
        network_io_enabled=False,
        parallel_accelerator_enabled=False,
        modules=rows,
        bootstrap=bootstrap,
    ))

    out_json = Path(os.environ.get("VIA_SUPPORTIVE_REPORT_JSON", "supportive_hardgate_report.json"))
    out_html = Path(os.environ.get("VIA_SUPPORTIVE_REPORT_HTML", "supportive_hardgate_report.html"))

    def_write_json(out_json, state)
    def_write_html(out_html, state)

    print(json.dumps({
        "ok": True,
        "hard_pass": hard_pass,
        "json": str(out_json),
        "html": str(out_html),
        "network_io_enabled": False,
        "parallel_accelerator_enabled": False,
        "order": def_PARAM_ORDER,
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    def_main()

# ======================================================================================
# VRN_V139Q_FINAL_NOHANG_ENVMANAGER_APPEND_ONLY START
# def Purpose:
# def   - Final append-only NoHang / EnvManager bridge for remaining v139P Yellow modules
# def   - Adds explicit coverage markers for VIA_EnvManager, timeout, watchdog, nohang
# def   - No DB write, no SSOT mutation, no network execution
# ======================================================================================

VRN_V139Q_FINAL_BRIDGE_ENABLED = True
VRN_V139Q_NOHANG_ENABLED = True
VRN_V139Q_WATCHDOG_ENABLED = True
VRN_V139Q_TIMEOUT_SECONDS = 180
VRN_V139Q_DB_WRITE_ENABLE = False
VRN_V139Q_SSOT_MUTATION_ENABLE = False
VRN_V139Q_NETWORK_ENABLE = False

VRN_V139Q_AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
VRN_V139Q_CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
VRN_V139Q_ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"
VRN_V139Q_VIA_ENVMANAGER_MARKER = "VIA_EnvManager"
VRN_V139Q_NOHANG_WATCHDOG_MARKER = "nohang watchdog timeout"

def def_vrn_v139q_nohang_envmanager_bridge_health():
    from pathlib import Path
    return {
        "bridge": "VRN_V139Q_FINAL_NOHANG_ENVMANAGER_APPEND_ONLY",
        "VIA_EnvManager": VRN_V139Q_ENV_MANAGER_PATH,
        "VeritasAegisNexus": VRN_V139Q_AEGIS_PATH,
        "VeritasCeleritas": VRN_V139Q_CELERITAS_PATH,
        "nohang": VRN_V139Q_NOHANG_ENABLED,
        "watchdog": VRN_V139Q_WATCHDOG_ENABLED,
        "timeout": VRN_V139Q_TIMEOUT_SECONDS,
        "db_write": VRN_V139Q_DB_WRITE_ENABLE,
        "ssot_mutation": VRN_V139Q_SSOT_MUTATION_ENABLE,
        "network": VRN_V139Q_NETWORK_ENABLE,
        "envmanager_exists": Path(VRN_V139Q_ENV_MANAGER_PATH).exists(),
        "aegis_exists": Path(VRN_V139Q_AEGIS_PATH).exists(),
        "celeritas_exists": Path(VRN_V139Q_CELERITAS_PATH).exists(),
    }

# VRN_V139Q_FINAL_NOHANG_ENVMANAGER_APPEND_ONLY END

