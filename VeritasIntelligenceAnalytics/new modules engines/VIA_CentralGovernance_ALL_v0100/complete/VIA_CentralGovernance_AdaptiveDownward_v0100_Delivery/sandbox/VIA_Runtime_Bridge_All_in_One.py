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


def_PARAM_SUPPORTIVE_ROOT = Path(__file__).resolve().parent
def_PARAM_CORE_MODULE_NAMES = [
    "VIA_EnvManager",
    "VIA_RegistryCore_v1",
    "VIA_SSOT_Unified",
    "VeritasAegisNexus",
    "VeritasCeleritas",
]

def_PARAM_ENABLE_BOOTSTRAP_SCAN = False
def_PARAM_ENABLE_BOOTSTRAP_REGISTRY_STATUS = True
def_PARAM_ENABLE_CELERITAS_INIT = False
def_PARAM_ENABLE_ENV_GOVERNANCE_CHECK = False
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
