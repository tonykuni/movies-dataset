#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Policy tail. The existing policy sections stay. L50's panoramic ban runs after them."""
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
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0149.py"
BAN = HERE / "CGC_MDL205_TalibBan_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0149_for_v0150")
ban = _load(BAN, "vcgc_talib_ban")
body = prev.body
_policy = body.policy_step


def policy_step() -> int:
    rc = _policy()
    card = ban.check()
    print(f"[政策] L50 全景 · 尾版 {card['tails']} · import {card['imports']} · 提及 {card['mentions']} · 已裝 {card['installed']} · {card['lamp']}")
    return rc or (0 if card["lock_success"] else 2)


body.policy_step = policy_step


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    return prev.main(argv)


def selftest() -> int:
    return ban.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
