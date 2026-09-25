#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG101 — who is allowed into the next live test.

Taiwan monthly revenue uses the exchange master list already read by
ENG063. This file does not replace that list and it does not fetch.
International probe names start at NVDA and can be added or removed.
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

DEFAULT_INTL = ("NVDA",)


def intl_universe(current: list[str] | None = None, add: list[str] | None = None, remove: list[str] | None = None) -> list[str]:
    chosen = []
    seed = list(DEFAULT_INTL if current is None else current)
    for item in seed + list(add or []):
        code = str(item or "").strip().upper()
        if code and code not in chosen and code not in {str(x).strip().upper() for x in (remove or [])}:
            chosen.append(code)
    return chosen


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    chk("default nvda", intl_universe() == ["NVDA"])
    chk("add", intl_universe(add=["aapl", "NVDA"]) == ["NVDA", "AAPL"])
    chk("remove", intl_universe(add=["AAPL"], remove=["nvda"]) == ["AAPL"])
    chk("taiwan not here", "2330" not in intl_universe())
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG101 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
