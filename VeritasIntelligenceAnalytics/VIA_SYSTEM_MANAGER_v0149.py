#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0148→v0149: the one live command key AST found, VIA_ENG003_TALibEngine, is unplugged.

v0148 stays on disk. The technical-analysis path remains VDF_ENG086_QuantGuardOneBridge.
This file does not import talib and does not install it.
"""
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
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VIA_SYSTEM_MANAGER_v0148.py"
RETIRED = "VIA_ENG003_TALibEngine"
REPLACEMENT = "VDF_ENG086_QuantGuardOneBridge"


def _load():
    spec = importlib.util.spec_from_file_location("via_system_manager_v0148_for_v0149", PRIOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ENGINE_CANDIDATE_NAMES.pop(RETIRED, None)
    return module


def selftest() -> int:
    module = _load()
    gone = RETIRED not in module.ENGINE_CANDIDATE_NAMES
    pointed = REPLACEMENT in module.ENGINE_FORMAL_NAMES
    deck = sorted((HERE / "supportive modules" / "registry").glob("CGC_MDL095_DeckServer_v*.py"))[-1]
    text = deck.read_text(encoding="utf-8", errors="replace")
    # The live deck's task keys were already clear; this only checks the file the manager calls.
    tasks = module._mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    task_clean = not any("talib" in key.lower() for key in tasks)
    print(f"  [{'OK' if gone else 'FAIL'}] candidate command unplugged")
    print(f"  [{'OK' if pointed else 'FAIL'}] pointer is {REPLACEMENT}")
    print(f"  [{'OK' if task_clean else 'FAIL'}] deck {deck.name} tasks {len(tasks)}")
    if not (gone and pointed and task_clean):
        return 1
    print("=== prior manager selftest ===")
    return module.selftest()


def main() -> int:
    module = _load()
    if "--selftest" in sys.argv:
        return selftest()
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
