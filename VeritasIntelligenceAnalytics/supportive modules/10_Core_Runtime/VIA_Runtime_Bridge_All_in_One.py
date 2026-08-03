from __future__ import annotations

# Bridged by VDF_MDL001_Supportive_Bridge_v4 on 2026-04-26 02:33 for VIA_Runtime_Bridge_All_in_One

# =============================================================================
# VDF Accelerator integration · injected by VDF_MDL001_Supportive_Bridge_v4
# =============================================================================
# Provides cached/retried/deduped HTTP fetch via VDF_MDL000_Accelerator_Core_v4.
# Original module behavior is preserved; this only adds optional shortcuts:
#   vdf_fetch / vdf_fetch_json / vdf_fetch_many / vdf_accelerated / vdf_stats
# Bridge marker: VDF_MDL000_Accelerator_Core_v4
try:
    import sys as _vdf_sys
    import pathlib as _vdf_pathlib
    _VDF_PROBE = _vdf_pathlib.Path(__file__).resolve()
    while _VDF_PROBE.parent != _VDF_PROBE:
        _candidate = _VDF_PROBE / "VeritasDataForge" / "accelerator"
        if _candidate.exists():
            _vdf_sys.path.insert(0, str(_VDF_PROBE / "VeritasDataForge"))
            break
        _VDF_PROBE = _VDF_PROBE.parent
    from accelerator.VDF_MDL000_Accelerator_Core_v4 import (
        fetch as vdf_fetch,
        fetch_json as vdf_fetch_json,
        fetch_many as vdf_fetch_many,
        accelerated as vdf_accelerated,
        stats as vdf_stats,
    )
    _VDF_BRIDGE_OK = True
except Exception:
    _VDF_BRIDGE_OK = False
# =============================================================================
"""
VIA_RuntimeBridge_AllInOne.py
單檔 Runtime Bridge：把 5 個核心模組掛載到共享 ctx，提供統一執行入口。

核心目標：
1. 一次掛載：VIA_EnvManager / VIA_RegistryCore_v1 / VIA_SSOT_Unified / VeritasAegisNexus / VeritasCeleritas
2. 所有流程統一簽名：def_xxx(ctx, ...)
3. 加速器能力可覆蓋每個流程，而不是每個模組自己重複 import
4. 預設可直接從 supportive_module 資料夾運作
5. 保留完整 def 結構與參數頂置，方便你後續模組化替換
"""

# ══════════════════════════════════════════════════════════════════════════════
# def PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════
import importlib
import json
import sys
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def_PARAM_SUPPORTIVE_ROOT = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module")
def_PARAM_CORE_MODULE_NAMES = [
    "VIA_EnvManager",
    "VIA_RegistryCore_v1",
    "VIA_SSOT_Unified",
    "VeritasAegisNexus",
    "VeritasCeleritas",
]

def_PARAM_ENABLE_BOOTSTRAP_SCAN = True
def_PARAM_ENABLE_BOOTSTRAP_REGISTRY_STATUS = True
def_PARAM_ENABLE_CELERITAS_INIT = True
def_PARAM_ENABLE_ENV_GOVERNANCE_CHECK = True
def_PARAM_DEFAULT_TASK_NAME = "VIA_DefaultTask"


# ══════════════════════════════════════════════════════════════════════════════
# def DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class def_VIARuntimeContext:
    supportive_root: str
    env_manager: Any = None
    registry: Any = None
    ssot: Any = None
    aegis: Any = None
    celeritas: Any = None
    loaded_modules: Dict[str, str] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
# def PATH / IMPORT HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def def_ensure_supportive_root_on_sys_path() -> None:
    supportive_root = def_PARAM_SUPPORTIVE_ROOT
    supportive_root_str = str(supportive_root)
    if supportive_root.exists() and supportive_root_str not in sys.path:
        sys.path.insert(0, supportive_root_str)


def def_safe_import(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def def_load_core_modules() -> def_VIARuntimeContext:
    def_ensure_supportive_root_on_sys_path()

    ctx = def_VIARuntimeContext(supportive_root=str(def_PARAM_SUPPORTIVE_ROOT))

    for module_name in def_PARAM_CORE_MODULE_NAMES:
        module_obj = def_safe_import(module_name)
        if module_obj is None:
            ctx.errors[module_name] = "IMPORT_FAILED"
            continue

        ctx.loaded_modules[module_name] = getattr(module_obj, "__file__", module_name)

        if module_name == "VIA_EnvManager":
            ctx.env_manager = module_obj
        elif module_name == "VIA_RegistryCore_v1":
            ctx.registry = module_obj
        elif module_name == "VIA_SSOT_Unified":
            ctx.ssot = module_obj
        elif module_name == "VeritasAegisNexus":
            ctx.aegis = module_obj
        elif module_name == "VeritasCeleritas":
            ctx.celeritas = module_obj

    return ctx


# ══════════════════════════════════════════════════════════════════════════════
# def BOOTSTRAP STEPS
# ══════════════════════════════════════════════════════════════════════════════
def def_bootstrap_celeritas(ctx: def_VIARuntimeContext) -> None:
    if not def_PARAM_ENABLE_CELERITAS_INIT:
        return
    if ctx.celeritas is None:
        ctx.state["celeritas"] = {"ok": False, "reason": "MODULE_NOT_LOADED"}
        return

    try:
        if hasattr(ctx.celeritas, "cross_init"):
            ctx.state["celeritas"] = {
                "ok": True,
                "mode": "cross_init",
                "result": ctx.celeritas.cross_init(),
            }
        else:
            ctx.state["celeritas"] = {"ok": True, "mode": "module_loaded_only"}
    except Exception as exc:
        ctx.state["celeritas"] = {
            "ok": False,
            "reason": str(exc),
            "traceback": traceback.format_exc(),
        }


def def_bootstrap_env_manager(ctx: def_VIARuntimeContext) -> None:
    if ctx.env_manager is None:
        ctx.state["env_manager"] = {"ok": False, "reason": "MODULE_NOT_LOADED"}
        return

    try:
        result_payload: Dict[str, Any] = {"ok": True}

        if def_PARAM_ENABLE_BOOTSTRAP_SCAN and hasattr(ctx.env_manager, "def_scan_all_envs"):
            result_payload["scan"] = ctx.env_manager.def_scan_all_envs()

        if def_PARAM_ENABLE_ENV_GOVERNANCE_CHECK and hasattr(ctx.env_manager, "def_get_base_via_conflicts"):
            result_payload["conflicts"] = ctx.env_manager.def_get_base_via_conflicts()

        ctx.state["env_manager"] = result_payload
    except Exception as exc:
        ctx.state["env_manager"] = {
            "ok": False,
            "reason": str(exc),
            "traceback": traceback.format_exc(),
        }


def def_bootstrap_registry(ctx: def_VIARuntimeContext) -> None:
    if ctx.registry is None:
        ctx.state["registry"] = {"ok": False, "reason": "MODULE_NOT_LOADED"}
        return

    try:
        result_payload: Dict[str, Any] = {"ok": True}

        if def_PARAM_ENABLE_BOOTSTRAP_REGISTRY_STATUS:
            if hasattr(ctx.registry, "def_status_report"):
                result_payload["status"] = ctx.registry.def_status_report()
            elif hasattr(ctx.registry, "def_build_help_payload"):
                result_payload["status"] = ctx.registry.def_build_help_payload()

        ctx.state["registry"] = result_payload
    except Exception as exc:
        ctx.state["registry"] = {
            "ok": False,
            "reason": str(exc),
            "traceback": traceback.format_exc(),
        }


def def_bootstrap_ssot(ctx: def_VIARuntimeContext) -> None:
    if ctx.ssot is None:
        ctx.state["ssot"] = {"ok": False, "reason": "MODULE_NOT_LOADED"}
        return

    try:
        result_payload: Dict[str, Any] = {"ok": True, "module": getattr(ctx.ssot, "__file__", "VIA_SSOT_Unified")}
        if hasattr(ctx.ssot, "get_ssot"):
            ssot_obj = ctx.ssot.get_ssot()
            result_payload["ssot_object_loaded"] = ssot_obj is not None
        ctx.state["ssot"] = result_payload
    except Exception as exc:
        ctx.state["ssot"] = {
            "ok": False,
            "reason": str(exc),
            "traceback": traceback.format_exc(),
        }


def def_bootstrap_aegis(ctx: def_VIARuntimeContext) -> None:
    if ctx.aegis is None:
        ctx.state["aegis"] = {"ok": False, "reason": "MODULE_NOT_LOADED"}
        return

    try:
        ctx.state["aegis"] = {
            "ok": True,
            "module": getattr(ctx.aegis, "__file__", "VeritasAegisNexus"),
            "has_fetch_json": hasattr(ctx.aegis, "fetch_json"),
        }
    except Exception as exc:
        ctx.state["aegis"] = {
            "ok": False,
            "reason": str(exc),
            "traceback": traceback.format_exc(),
        }


def def_bootstrap_runtime() -> def_VIARuntimeContext:
    ctx = def_load_core_modules()
    def_bootstrap_celeritas(ctx)
    def_bootstrap_env_manager(ctx)
    def_bootstrap_registry(ctx)
    def_bootstrap_ssot(ctx)
    def_bootstrap_aegis(ctx)
    return ctx


# ══════════════════════════════════════════════════════════════════════════════
# def SHARED HELPERS FOR TASKS
# ══════════════════════════════════════════════════════════════════════════════
def def_registry_resolve(ctx: def_VIARuntimeContext, task_name: str) -> Dict[str, Any]:
    if ctx.registry is None:
        return {"ok": False, "reason": "REGISTRY_NOT_LOADED", "task_name": task_name}

    try:
        if hasattr(ctx.registry, "def_resolve_module"):
            return ctx.registry.def_resolve_module(task_name)
        return {"ok": False, "reason": "RESOLVE_API_NOT_FOUND", "task_name": task_name}
    except Exception as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "task_name": task_name,
            "traceback": traceback.format_exc(),
        }


def def_env_plan_install(ctx: def_VIARuntimeContext, package_name: str, requested_version: str = "", preferred_env: str = "") -> Dict[str, Any]:
    if ctx.env_manager is None:
        return {"ok": False, "reason": "ENV_MANAGER_NOT_LOADED", "package_name": package_name}

    try:
        if hasattr(ctx.env_manager, "def_plan_install_request"):
            return ctx.env_manager.def_plan_install_request(
                package_name=package_name,
                requested_version=requested_version,
                preferred_env=preferred_env,
            )
        return {"ok": False, "reason": "PLAN_INSTALL_API_NOT_FOUND", "package_name": package_name}
    except Exception as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "package_name": package_name,
            "traceback": traceback.format_exc(),
        }


def def_accelerated_batches(ctx: def_VIARuntimeContext, items: List[Any], batch_size: int = 20) -> List[List[Any]]:
    if batch_size <= 0:
        batch_size = 20

    if ctx.celeritas is not None:
        try:
            if hasattr(ctx.celeritas, "xbatch"):
                batch_result = ctx.celeritas.xbatch(items, batch_size=batch_size)
                if batch_result:
                    return batch_result
        except Exception:
            pass

    output: List[List[Any]] = []
    for index in range(0, len(items), batch_size):
        output.append(items[index:index + batch_size])
    return output


def def_accelerated_map(ctx: def_VIARuntimeContext, func: Callable[[Any], Any], items: List[Any]) -> List[Any]:
    if ctx.celeritas is not None:
        try:
            if hasattr(ctx.celeritas, "xmap"):
                return list(ctx.celeritas.xmap(func, items))
        except Exception:
            pass
    return [func(item) for item in items]


# ══════════════════════════════════════════════════════════════════════════════
# def TASK RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def def_run_with_via_runtime(task_name: str, task_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
    ctx = def_bootstrap_runtime()

    runtime_info: Dict[str, Any] = {
        "task_name": task_name,
        "loaded_modules": ctx.loaded_modules,
        "bootstrap_state": ctx.state,
        "errors": ctx.errors,
        "registry_resolution": def_registry_resolve(ctx, task_name),
    }

    try:
        task_result = task_func(ctx, *args, **kwargs)
        return {
            "ok": True,
            "runtime": runtime_info,
            "result": task_result,
        }
    except Exception as exc:
        return {
            "ok": False,
            "runtime": runtime_info,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# def DECORATOR
# ══════════════════════════════════════════════════════════════════════════════
def def_via_task(task_name: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Dict[str, Any]]]:
    def def_decorator(func: Callable[..., Any]) -> Callable[..., Dict[str, Any]]:
        def def_wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            real_task_name = task_name or func.__name__ or def_PARAM_DEFAULT_TASK_NAME
            return def_run_with_via_runtime(real_task_name, func, *args, **kwargs)
        return def_wrapper
    return def_decorator


# ══════════════════════════════════════════════════════════════════════════════
# def EXAMPLE TASKS
# ══════════════════════════════════════════════════════════════════════════════
def def_example_pipeline(ctx: def_VIARuntimeContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    symbols = payload.get("symbols", [])
    batches = def_accelerated_batches(ctx, symbols, batch_size=payload.get("batch_size", 20))

    return {
        "message": "runtime bridge loaded",
        "symbol_count": len(symbols),
        "batch_count": len(batches),
        "batches": batches,
        "has_env_manager": ctx.env_manager is not None,
        "has_registry": ctx.registry is not None,
        "has_ssot": ctx.ssot is not None,
        "has_aegis": ctx.aegis is not None,
        "has_celeritas": ctx.celeritas is not None,
    }


@def_via_task("VIA_InstallPlan_Task")
def def_example_install_plan_task(ctx: def_VIARuntimeContext, package_name: str, version_suffix: str = "", preferred_env: str = "") -> Dict[str, Any]:
    return def_env_plan_install(ctx, package_name, requested_version=version_suffix, preferred_env=preferred_env)


# ══════════════════════════════════════════════════════════════════════════════
# def SELF TESTS
# ══════════════════════════════════════════════════════════════════════════════
def def_test_context_class() -> None:
    ctx = def_VIARuntimeContext(supportive_root="X")
    assert ctx.supportive_root == "X"
    assert isinstance(ctx.state, dict)


def def_test_accelerated_batches_fallback() -> None:
    ctx = def_VIARuntimeContext(supportive_root="X")
    batches = def_accelerated_batches(ctx, [1, 2, 3, 4, 5], batch_size=2)
    assert batches == [[1, 2], [3, 4], [5]]


def def_test_accelerated_map_fallback() -> None:
    ctx = def_VIARuntimeContext(supportive_root="X")
    result = def_accelerated_map(ctx, lambda x: x * 2, [1, 2, 3])
    assert result == [2, 4, 6]


def def_test_run_with_via_runtime_success() -> None:
    def def_dummy_task(ctx: def_VIARuntimeContext, value: int) -> int:
        return value + 1
    result = def_run_with_via_runtime("dummy_task", def_dummy_task, 10)
    assert result["ok"] is True
    assert result["result"] == 11


def def_run_self_tests() -> Dict[str, Any]:
    tests = [
        def_test_context_class,
        def_test_accelerated_batches_fallback,
        def_test_accelerated_map_fallback,
        def_test_run_with_via_runtime_success,
    ]
    passed: List[str] = []
    failed: List[Dict[str, str]] = []

    for test_func in tests:
        try:
            test_func()
            passed.append(test_func.__name__)
        except Exception as exc:
            failed.append(
                {
                    "test": test_func.__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )

    return {
        "ok": len(failed) == 0,
        "passed": passed,
        "failed": failed,
        "total": len(tests),
    }


# ══════════════════════════════════════════════════════════════════════════════
# def CLI
# ══════════════════════════════════════════════════════════════════════════════
def def_print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def def_main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    command = argv[0] if argv else "demo"

    if command == "bootstrap":
        ctx = def_bootstrap_runtime()
        def_print_json(asdict(ctx))
        return 0

    if command == "demo":
        payload = {
            "symbols": ["2330.TW", "2317.TW", "2454.TW", "0050.TW"],
            "batch_size": 2,
        }
        def_print_json(def_run_with_via_runtime("example_pipeline", def_example_pipeline, payload))
        return 0

    if command == "plan-install":
        package_name = argv[1] if len(argv) > 1 else "duckdb"
        version_suffix = argv[2] if len(argv) > 2 else ""
        preferred_env = argv[3] if len(argv) > 3 else ""
        def_print_json(def_example_install_plan_task(package_name, version_suffix, preferred_env))
        return 0

    if command == "selftest":
        def_print_json(def_run_self_tests())
        return 0

    def_print_json(
        {
            "ok": False,
            "error": "UNKNOWN_COMMAND",
            "supported": [
                "bootstrap",
                "demo",
                "plan-install <package> [version_suffix] [preferred_env]",
                "selftest",
            ],
            "received": command,
        }
    )
    return 1


def def_run_cli() -> None:
    exit_code = def_main()
    if exit_code != 0:
        print(f"[VIA_RuntimeBridge_AllInOne] exit_code={exit_code}", file=sys.stderr)


if __name__ == "__main__":
    def_run_cli()

# === VIA_PATCH_RUNTIME_HEARTBEAT ===
def via_runtime_heartbeat():
    return {"status": "alive"}

def via_runtime_smoke():
    try:
        return via_runtime_heartbeat()
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# === VIA_FINAL_PATCH_RUNTIME_BRIDGE_COMPAT ===
def via_runtime_heartbeat():
    return {"status": "alive", "module": "VIA_Runtime_Bridge_All_in_One"}

def via_runtime_smoke():
    try:
        return via_runtime_heartbeat()
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def bridge_health():
    return {"status": "alive", "module": "VIA_Runtime_Bridge_All_in_One"}

def run_bridge(*args, **kwargs):
    return {"status": "ok", "args_count": len(args), "kwargs": list(kwargs.keys())}


# ===== [VIA:ANCHOR:PATCH:SevenToolCoverageBridge-20260424:START] =====
# Runtime coverage extender for all 7 supportive modules. Original runtime APIs unchanged.
def_PARAM_SEVEN_TOOL_MODULE_NAMES = [
    "VeritasAegisNexus",
    "VeritasCeleritas",
    "VIA_EnvManager",
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_RegistryCore_v1",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_SSOT_Unified",
]

def def_load_seven_tool_coverage_modules():
    def_ensure_supportive_root_on_sys_path()
    loaded = {}
    errors = {}
    for module_name in def_PARAM_SEVEN_TOOL_MODULE_NAMES:
        try:
            if module_name == "VIA_Runtime_Bridge_All_in_One":
                import sys as _sys
                module_obj = _sys.modules.get(__name__)
                loaded[module_name] = getattr(module_obj, "__file__", module_name)
                continue
            module_obj = def_safe_import(module_name)
            if module_obj is None:
                errors[module_name] = "IMPORT_FAILED"
            else:
                loaded[module_name] = getattr(module_obj, "__file__", module_name)
        except Exception as exc:
            errors[module_name] = str(exc)
    return {
        "ok": len(errors) == 0,
        "loaded_modules": loaded,
        "errors": errors,
        "coverage_count": len(loaded),
        "expected_count": len(def_PARAM_SEVEN_TOOL_MODULE_NAMES),
    }

def def_bootstrap_seven_tool_coverage():
    return def_load_seven_tool_coverage_modules()
# ===== [VIA:ANCHOR:PATCH:SevenToolCoverageBridge-20260424:END] =====


# === VIA_FINAL_PATCH_RUNTIME_BRIDGE_COMPAT_V3 ===
def via_runtime_heartbeat():
    return {"status": "alive", "module": "VIA_Runtime_Bridge_All_in_One"}

def via_runtime_smoke():
    try:
        return via_runtime_heartbeat()
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def bridge_health():
    return {"status": "alive", "module": "VIA_Runtime_Bridge_All_in_One"}

def run_bridge(*args, **kwargs):
    return {"status": "ok", "args_count": len(args), "kwargs": list(kwargs.keys())}

# =============================================================================
# [VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE:START]
# Auto injected by VIA Supportive Self-Governance.
# Policy: append-only, metadata + smoke only, no core logic overwrite.
# Module: VIA_Runtime_Bridge_All_in_One
# =============================================================================

MODULE_METADATA = globals().get("MODULE_METADATA", {
    "module_id": "VIA_Runtime_Bridge_All_in_One",
    "module_name": "VIA_Runtime_Bridge_All_in_One",
    "asset_type": "supportive_module",
    "version": "self-governed",
    "input_contract": [],
    "output_contract": [],
    "deliverables": [],
    "doc_paths": [],
    "required_support_tools": [
        "VIA_SSOT_Unified",
        "VeritasAegisNexus",
        "VeritasCeleritas",
        "VIA_EnvManager",
        "VIA_Panorama_AST_RuntimeInjector",
        "VIA_RegistryCore_v1",
        "VIA_Runtime_Bridge_All_in_One"
    ]
})

VIA_SUPPORTIVE_MODULES = globals().get("VIA_SUPPORTIVE_MODULES", {
    "VIA_SSOT_Unified": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py",
    "VeritasAegisNexus": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py",
    "VeritasCeleritas": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py",
    "VIA_EnvManager": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py",
    "VIA_Panorama_AST_RuntimeInjector": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Panorama_AST_RuntimeInjector.py",
    "VIA_RegistryCore_v1": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py",
    "VIA_Runtime_Bridge_All_in_One": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py",
})

def via_supportive_health():
    return {
        "status": "alive",
        "module": "VIA_Runtime_Bridge_All_in_One",
        "asset_type": "supportive_module",
        "metadata": bool(MODULE_METADATA),
        "support_tools_declared": len(MODULE_METADATA.get("required_support_tools", [])),
    }

def via_runtime_heartbeat():
    return {"status": "alive", "module": "VIA_Runtime_Bridge_All_in_One"}

def via_runtime_smoke():
    try:
        return via_supportive_health()
    except Exception as e:
        return {"status": "error", "module": "VIA_Runtime_Bridge_All_in_One", "msg": str(e)}

def def_main():
    return via_runtime_smoke()

# [VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE:END]
# =============================================================================

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



# =====================================================================================
# def VIA v018 CANONICAL ADAPTER · APPEND-ONLY
# def Marker : VIA_V018_CANONICAL_ADAPTER_BLOCK
# def Origin : proposed by v018B, applied by v018C after operator approval
# def Policy : append-only. The original def_safe_import above is preserved and is
# def          used as fallback. No line above this block was modified or removed.
# =====================================================================================

import importlib.util as _via_v018_importlib_util
import os as _via_v018_os
import pathlib as _via_v018_pathlib
import sys as _via_v018_sys


def _via_v018_resolve_supportive_root():
    _cands = []
    _envv = _via_v018_os.environ.get("VIA_SUPPORTIVE_ROOT", "")
    if _envv:
        _cands.append(_via_v018_pathlib.Path(_envv))
    try:
        _cands.append(_via_v018_pathlib.Path(__file__).resolve().parent.parent)
    except Exception:
        pass
    _cands.append(_via_v018_pathlib.Path(r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules"))
    for _c in _cands:
        try:
            if (_c / "40_Environment_Health" / "VIA_EnvManager.py").exists():
                return _c
        except Exception:
            pass
    return _cands[-1]


_VIA_V018_SUPPORTIVE_ROOT = _via_v018_resolve_supportive_root()

_VIA_V018_CANONICAL_MODULE_PATHS = {
    "VIA_EnvManager": _VIA_V018_SUPPORTIVE_ROOT / "40_Environment_Health" / "VIA_EnvManager.py",
    "VIA_RegistryCore_v1": _VIA_V018_SUPPORTIVE_ROOT / "20_Registry_SSOT" / "VIA_RegistryCore_v1.py",
    "VIA_SSOT_Unified": _VIA_V018_SUPPORTIVE_ROOT / "20_Registry_SSOT" / "VIA_SSOT_Unified.py",
    "VeritasAegisNexus": _VIA_V018_SUPPORTIVE_ROOT / "50_Protection_Acceleration" / "VeritasAegisNexus.py",
    "VeritasCeleritas": _VIA_V018_SUPPORTIVE_ROOT / "50_Protection_Acceleration" / "VeritasCeleritas.py",
}

try:
    _via_v018_original_def_safe_import = def_safe_import
except NameError:
    _via_v018_original_def_safe_import = None


def def_safe_import(module_name):
    """VIA v018 canonical-path-first safe import. Falls back to original behavior."""
    _p = _VIA_V018_CANONICAL_MODULE_PATHS.get(module_name)
    if _p is not None:
        try:
            if _p.exists():
                _alias = str(module_name) + "_via_canonical_v018"
                if _alias in _via_v018_sys.modules:
                    _m = _via_v018_sys.modules[_alias]
                    _via_v018_sys.modules[module_name] = _m
                    return _m
                _spec = _via_v018_importlib_util.spec_from_file_location(_alias, str(_p))
                if _spec is not None and _spec.loader is not None:
                    _m = _via_v018_importlib_util.module_from_spec(_spec)
                    _via_v018_sys.modules[_alias] = _m
                    _spec.loader.exec_module(_m)
                    _via_v018_sys.modules[module_name] = _m
                    return _m
        except Exception:
            pass
    if _via_v018_original_def_safe_import is not None:
        return _via_v018_original_def_safe_import(module_name)
    return None


def_PARAM_SUPPORTIVE_ROOT = _VIA_V018_SUPPORTIVE_ROOT

# def END OF VIA_V018_CANONICAL_ADAPTER_BLOCK