#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. Read a command register through its dot-source chain.

v0257 only adds one command and loads v0256. The gate must see that chain.
Direct start stays refused. v0104 and v0106 are not rewritten.
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VDF_SystemManager_v0106.py"
_body = None


def _follow(path: Path, seen: set) -> str:
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = [text]
    for name in re.findall(r"Register-VIA-Commands-v\d+\.ps1", text):
        parts.append(_follow(path.parent / name, seen))
    return "\n".join(parts)


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location("vdf_manager_v0106_for_v0107", PRIOR)
        prior = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prior)
        body = prior._load()
        plain = body._src
        original = body.scrape_gate_split

        def _src(p):
            text = plain(p)
            path = Path(str(p)) if p else None
            if path is not None and path.name.startswith("Register-VIA-Commands-"):
                return _follow(path, set())
            return text

        def scrape_gate_split(environ=None):
            body._src = _src
            try:
                return original(environ)
            finally:
                body._src = plain

        body.scrape_gate_split = scrape_gate_split
        _body = body
    return _body


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    ok = main() == 2
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
