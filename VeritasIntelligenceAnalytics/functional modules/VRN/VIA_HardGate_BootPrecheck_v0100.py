# -*- coding: utf-8 -*-
"""
VIA_HardGate_BootPrecheck.py — 7-Tool BOOT_PRECHECK 統一載入樣板
================================================================
依 VIA_Supportive_HardGate_Seal.json 政策載入 7 個支援工具：
  1. VIA_SSOT_Unified            (全域配置 + 鎖定 regex + 會計同義字)
  2. VeritasCeleritas            (lazy module + parallel map)
  3. VeritasAegisNexus           (network safety + offline_mode)
  4. VIA_RegistryCore_v1         (append-only 模組登記)
  5. VIA_Runtime_Bridge_All_in_One (VRN_SupportBridge — 統一橋接)
  6. VIA_EnvManager              (多 venv 管理)
  7. VIA_Panorama_AST_RuntimeInjector (AST 編號 / 注入)

POLICY (per VIA_Supportive_HardGate_Seal.json):
  - BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH
  - Python 3.12 inject
  - All loads silent on failure (try/except), return capability dict

USAGE
-----
  在每個 VRN_MDLxxx 模組頂部加：

      from VIA_HardGate_BootPrecheck import HARDGATE_BOOT
      _HG_CAPS = HARDGATE_BOOT(ssot_dir=cfg.get("ssot_dir", ""))
      _SSOT = _HG_CAPS["plugins"]["ssot"]
      _CEL  = _HG_CAPS["plugins"]["celeritas"]
      _AEG  = _HG_CAPS["plugins"]["aegis"]
      _REG  = _HG_CAPS["plugins"]["registry"]
      _BRG  = _HG_CAPS["plugins"]["runtime_bridge"]
      _ENV  = _HG_CAPS["plugins"]["env_manager"]
      _AST  = _HG_CAPS["plugins"]["ast_planner"]

OR (zero-import-path mode):
      _HG_CAPS = hardgate_load_inline(ssot_dir)

Both modes return same capability dict.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
__version__ = "1.0.0"

import os
import sys
import json
import time
import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger("HARDGATE")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(
        "[%(asctime)s][%(levelname)s][HARDGATE] %(message)s",
        datefmt="%H:%M:%S"))
    log.addHandler(h)
    log.setLevel(logging.INFO)

# ── 7-tool config per VIA_Supportive_HardGate_Seal.json ───────────────────────
_HARDGATE_TOOLS: Dict[str, Dict[str, Any]] = {
    "ssot": {
        "filename":   "VIA_SSOT_Unified.py",
        "module":     "VIA_SSOT_Unified",
        "expected":   ["SSOT", "TW_STOCK_CODE_4DIGIT"],
        "category":   "config",
    },
    "celeritas": {
        "filename":   "VeritasCeleritas.py",
        "module":     "VeritasCeleritas",
        "expected":   ["_LazyModule", "celeritas_parallel_map"],
        "category":   "perf",
    },
    "aegis": {
        "filename":   "VeritasAegisNexus.py",
        "module":     "VeritasAegisNexus",
        "expected":   ["check_robots", "run_self_test"],
        "category":   "network",
    },
    "registry": {
        "filename":   "VIA_RegistryCore_v1.py",
        "module":     "VIA_RegistryCore_v1",
        "expected":   ["RegistryCore"],
        "category":   "registry",
    },
    "runtime_bridge": {
        "filename":   "VIA_Runtime_Bridge_All_in_One.py",
        "module":     "VIA_Runtime_Bridge_All_in_One",
        "expected":   ["BRIDGE"],
        "category":   "bridge",
    },
    "env_manager": {
        "filename":   "VIA_EnvManager.py",
        "module":     "VIA_EnvManager",
        "expected":   ["EnvManager"],
        "category":   "env",
    },
    "ast_planner": {
        "filename":   "VIA_Panorama_AST_RuntimeInjector.py",
        "module":     "VIA_Panorama_AST_RuntimeInjector",
        "expected":   ["ASTRuntimeInjector"],
        "category":   "ast",
    },
}


def _import_from_path(fpath: str, mod_name: str) -> Any:
    """Import a Python file from absolute path. Returns module or None."""
    try:
        if not os.path.isfile(fpath):
            return None
        spec = importlib.util.spec_from_file_location(mod_name, fpath)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        log.debug("Import fail %s: %s", mod_name, e)
        return None


def _import_from_sys(mod_name: str) -> Any:
    """Try ordinary `importlib.import_module`. Returns module or None."""
    try:
        return importlib.import_module(mod_name)
    except Exception:
        return None


def _check_capability(mod: Any, expected: list) -> bool:
    """Verify expected attributes are on module. Returns True if all present."""
    if mod is None:
        return False
    for attr in expected:
        if not hasattr(mod, attr):
            log.debug("Missing attr %s on %s", attr, mod.__name__)
            return False
    return True


def hardgate_load_inline(ssot_dir: str = "",
                          policy: str = "BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH",
                          py_inject: str = "3.12",
                          quiet: bool = False) -> Dict[str, Any]:
    """
    Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json.

    Args:
        ssot_dir: Directory containing the 7 tool files.
        policy: Boot policy (default: per Seal.json).
        py_inject: Python version target.
        quiet: If True, suppress success log lines.

    Returns:
        Dict with keys:
          "policy":     boot policy string
          "py_inject":  Python version string
          "ssot_dir":   resolved ssot_dir
          "plugins":    Dict[tool_key, module_or_None]
          "ok":         Dict[tool_key, bool]  (all expected attrs present)
          "n_loaded":   int  (how many modules loaded successfully)
          "n_capable":  int  (how many have expected attrs)
          "elapsed_ms": float
          "seal":       "BOOT_PRECHECKED" if all 7 capable else "PARTIAL"

    Behavior:
        - Tries direct file import (ssot_dir/<filename>) first.
        - Falls back to `importlib.import_module(<module>)`.
        - All failures are silent (return None).
        - Never raises.
        - Honors NO_NETWORK / NO_PARALLEL / NO_AUTOPATCH policy:
          * No HTTP calls, no spawn of threads/processes.
          * No file modification.
    """
    t0 = time.perf_counter()
    plugins: Dict[str, Any] = {}
    ok:      Dict[str, bool] = {}
    ssot_dir = ssot_dir or ""

    for key, cfg in _HARDGATE_TOOLS.items():
        mod = None
        # Path 1: direct file import from ssot_dir
        if ssot_dir:
            fpath = str(Path(ssot_dir) / cfg["filename"])
            mod = _import_from_path(fpath, cfg["module"])
        # Path 2: sys.path import
        if mod is None:
            mod = _import_from_sys(cfg["module"])

        plugins[key] = mod
        ok[key] = _check_capability(mod, cfg["expected"])
        if mod is not None and not quiet:
            log.info("✓ %s loaded (%s)  capable=%s", key, cfg["category"], ok[key])
        elif mod is None and not quiet:
            log.debug("✗ %s NOT loaded  (will use stdlib fallback)", key)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    n_loaded   = sum(1 for m in plugins.values() if m is not None)
    n_capable  = sum(1 for v in ok.values() if v)
    seal       = "BOOT_PRECHECKED" if n_capable == 7 else "PARTIAL"

    if not quiet:
        log.info("HardGate %s: %d/7 loaded, %d/7 capable, %.1fms",
                  seal, n_loaded, n_capable, elapsed_ms)

    return {
        "policy":     policy,
        "py_inject":  py_inject,
        "ssot_dir":   ssot_dir,
        "plugins":    plugins,
        "ok":         ok,
        "n_loaded":   n_loaded,
        "n_capable":  n_capable,
        "elapsed_ms": elapsed_ms,
        "seal":       seal,
    }


# ── Convenience aliases ──────────────────────────────────────────────────────
HARDGATE_BOOT = hardgate_load_inline


def hardgate_caps_summary(caps: Dict[str, Any]) -> str:
    """One-line capability string for log summary."""
    okmap = caps.get("ok", {})
    parts = []
    for k in _HARDGATE_TOOLS:
        parts.append(f"{k}={'✓' if okmap.get(k) else '✗'}")
    return f"[{caps.get('seal','?')}] " + " ".join(parts)


def hardgate_get(caps: Dict[str, Any], key: str) -> Any:
    """Safe accessor: returns module or None."""
    return caps.get("plugins", {}).get(key)


__all__ = [
    "__version__",
    "hardgate_load_inline", "HARDGATE_BOOT",
    "hardgate_caps_summary", "hardgate_get",
    "_HARDGATE_TOOLS",
]


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--ssot-dir", default="",
                    help="Directory containing the 7 supportive tool files")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()
    caps = HARDGATE_BOOT(ssot_dir=args.ssot_dir, quiet=args.quiet)
    print(hardgate_caps_summary(caps))
    print(json.dumps({k: v for k, v in caps.items() if k != "plugins"},
                     indent=2, ensure_ascii=False, default=str))
