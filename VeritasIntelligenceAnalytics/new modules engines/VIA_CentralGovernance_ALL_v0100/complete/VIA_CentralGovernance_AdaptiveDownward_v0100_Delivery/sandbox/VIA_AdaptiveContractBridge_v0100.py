# ASSET_ID: AST-PY-MOD-VIA-710-105
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


def_PARAM_EXPECTED_EXPORTS = {'VIA_EnvManager': ['def_scan_all_envs', 'def_get_base_via_conflicts', 'def_plan_install_request'], 'VIA_RegistryCore_v1': ['def_status_report', 'def_resolve_module'], 'VIA_SSOT_Unified': ['get_ssot', 'normalize', 'extract', 'contains'], 'VeritasAegisNexus': ['fetch_json', 'fetch_text', 'safe_request'], 'VeritasCeleritas': ['cross_init', 'xmap', 'xbatch_process', 'thread_budget']}
def_PARAM_LOADED: Dict[str, Any] = {}
def_PARAM_ERRORS: Dict[str, str] = {}


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
        return sorted({node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))})
    except Exception:
        return []


def def_validate_contracts() -> Dict[str, Any]:
    rows = []
    for module_name, expected in def_PARAM_EXPECTED_EXPORTS.items():
        path_value = def_resolve(module_name)
        exports = def_ast_exports(path_value) if path_value else []
        missing = [name for name in expected if name not in exports]
        rows.append({
            "module": module_name,
            "path": str(path_value or ""),
            "expected": expected,
            "missing": missing,
            "status": "PASS" if path_value and not missing else "REVIEW",
        })
    return {"ok": all(row["status"] == "PASS" for row in rows), "rows": rows}


def def_lazy_load(module_name: str, explicit_root: str = "") -> Any:
    if module_name in def_PARAM_LOADED:
        return def_PARAM_LOADED[module_name]
    path_value = def_resolve(module_name, explicit_root)
    if path_value is None:
        def_PARAM_ERRORS[module_name] = "MODULE_PATH_NOT_FOUND"
        return None
    runtime_name = f"via_adaptive_{module_name}_{abs(hash(str(path_value)))}"
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
        def_PARAM_ERRORS[module_name] = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        sys.modules.pop(runtime_name, None)
        return None


def def_resolve_callable(module_name: str, callable_name: str) -> Dict[str, Any]:
    expected = def_PARAM_EXPECTED_EXPORTS.get(module_name, [])
    if expected and callable_name not in expected:
        return {"ok": False, "error": "CALLABLE_NOT_ALLOWLISTED", "module": module_name, "callable": callable_name}
    module_obj = def_lazy_load(module_name)
    if module_obj is None:
        return {"ok": False, "error": "MODULE_LOAD_FAILED", "detail": def_PARAM_ERRORS.get(module_name, "")}
    callable_obj = getattr(module_obj, callable_name, None)
    if not callable(callable_obj):
        return {"ok": False, "error": "CALLABLE_NOT_FOUND", "module": module_name, "callable": callable_name}
    return {"ok": True, "module": module_name, "callable": callable_name, "object": callable_obj}


def def_call(module_name: str, callable_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    resolved = def_resolve_callable(module_name, callable_name)
    if not resolved.get("ok"):
        return resolved
    try:
        result = resolved["object"](*args, **kwargs)
        return {"ok": True, "module": module_name, "callable": callable_name, "result": result}
    except Exception as exc:
        return {"ok": False, "module": module_name, "callable": callable_name,
                 "error": str(exc), "traceback": traceback.format_exc()}


def def_status() -> Dict[str, Any]:
    return {
        "paths": def_path_status(),
        "contracts": def_validate_contracts(),
        "loaded": sorted(def_PARAM_LOADED),
        "errors": dict(def_PARAM_ERRORS),
    }


def def_run_self_tests() -> Dict[str, Any]:
    contract_result = def_validate_contracts()
    path_result = def_path_status()
    return {
        "ok": bool(path_result) and isinstance(contract_result.get("rows"), list),
        "contract_gate": contract_result.get("ok"),
        "path_count": sum(bool(value) for value in path_result.values()),
        "contract_rows": contract_result.get("rows", []),
    }


if __name__ == "__main__":
    print(json.dumps(def_run_self_tests(), ensure_ascii=False, indent=2, default=str))
